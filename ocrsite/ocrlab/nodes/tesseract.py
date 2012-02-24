"""
Tesseract Recogniser
"""

from __future__ import absolute_import

import os
import shutil
import codecs
import tempfile
import subprocess as sp

from nodetree import node, exceptions, utils as nodeutils

from . import base
from .. import stages, utils, exceptions

from ocradmin.ocrmodels.models import OcrModel

from ocrolib import numpy


class TesseractRecognizer(base.CommandLineRecognizerNode):
    """
    Recognize an image using Tesseract.
    """
    stage = stages.RECOGNIZE
    binary = "tesseract"

    @nodeutils.ClassProperty
    @classmethod
    def parameters(cls):
        return [
            dict(
                name="language_model",
                value="Tesseract Default Lang",
                choices=[m.name for m in \
                        OcrModel.objects.filter(app="tesseract", type="lang")],
            )
        ]

    def validate(self):
        """
        Check we're in a good state.
        """
        super(TesseractRecognizer, self).validate()
        if self._params.get("language_model", "").strip() == "":
            raise exceptions.ValidationError("no language model given: %s" % self._params, self)

    def prepare(self):
        """
        Extract the lmodel to a temporary directory.  This is
        cleaned up in the destructor.
        """
        if not hasattr(self, "_tessdata") is None:
            modpath = utils.lookup_model_file(self._params["language_model"])
            self.unpack_tessdata(modpath)
        self._tesseract = utils.get_binary("tesseract")
        self.logger.debug("Using Tesseract: %s" % self._tesseract)

    @utils.check_aborted
    def get_transcript(self, line):
        """
        Recognise each individual line by writing it as a temporary
        PNG, converting it to Tiff, and calling Tesseract on the
        image.  Unfortunately I can't get the current stable
        Tesseract 2.04 to support anything except TIFFs.
        """
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            tmp.close()
            self.write_binary(tmp.name, line)
            tiff = utils.convert_to_temp_image(tmp.name, "tif")
            text = self.process_line(tiff)
            os.unlink(tmp.name)
            os.unlink(tiff)
            return text

    def unpack_tessdata(self, lmodelpath):
        """
        Unpack the tar-gzipped Tesseract language files into
        a temporary directory and set TESSDATA_PREFIX environ
        var to point at it.
        """
        # might as well make this even less efficient!
        self.logger.debug("Unpacking tessdata: %s" % lmodelpath)
        import tarfile
        self._tessdata = tempfile.mkdtemp() + "/"
        datapath = os.path.join(self._tessdata, "tessdata")
        os.mkdir(datapath)
        # let this throw an exception if it fails.
        tgz = tarfile.open(lmodelpath, "r:*")
        self._lang = os.path.splitext(tgz.getnames()[0])[0]
        tgz.extractall(path=datapath)
        tgz.close()

        # set environ var where tesseract picks up the tessdata dir
        # this DOESN'T include the "tessdata" part
        os.environ["TESSDATA_PREFIX"] = self._tessdata

    @utils.check_aborted
    def process_line(self, imagepath):
        """
        Run Tesseract on the TIFF image, using YET ANOTHER temporary
        file to gather the output, which is then read back in.  If
        you think this seems horribly inefficient you'd be right, but
        Tesseract's external interface is quite inflexible.
        TODO: Fix hardcoded path to Tesseract.
        """
        if not hasattr(self, "_tessdata"):
            self.init_converter()

        lines = []
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.close()
            # args with page-seg mode: 5=line
            tessargs = [self._tesseract, imagepath, tmp.name, "-psm", "7"]
            if self._lang is not None:
                tessargs.extend(["-l", self._lang])
            proc = sp.Popen(tessargs, stderr=sp.PIPE)
            err = proc.stderr.read()
            if proc.wait() != 0:
                return "!!! TESSERACT CONVERSION ERROR %d: %s !!!" % (proc.returncode, err)
            # read and delete Tesseract's temp text file
            # whilst writing to our file
            with open(tmp.name + ".txt", "r") as txt:
                lines = [line.rstrip() for line in txt.readlines()]
                if lines and lines[-1] == "":
                    lines = lines[:-1]
                os.unlink(txt.name)
        return " ".join(lines)

    def cleanup(self):
        """
        Cleanup temporarily-extracted lmodel directory.
        """
        if hasattr(self, "_tessdata") and os.path.exists(self._tessdata):
            try:
                self.logger.debug(
                    "Cleaning up temp tessdata folder: %s" % self._tessdata)
                shutil.rmtree(self._tessdata)
            except OSError, (errno, strerr):
                self.logger.error(
                    "RmTree raised error: %s, %s" % (errno, strerr))


class TesseractPageSeg(TesseractRecognizer):
    """
    Recognize an image using Tesseract, including segmentation.
    """
    intypes = [numpy.ndarray]

    def __init__(self, *args, **kwargs):
        super(TesseractPageSeg, self).__init__(*args, **kwargs)
        self._configtmp = None

    def get_command(self, outfile, image):
        """Simple tesseract command line"""
        args = [self.binary, image, os.path.splitext(outfile)[0]]
        if self._lang is not None:
            args.extend(["-l", self._lang])
        args.append(self._configtmp)
        return args

    def prepare(self):
        super(TesseractPageSeg, self).prepare()
        # write a temp config file specifying the output format
        configtmp = tempfile.NamedTemporaryFile(delete=False)
        configtmp.write("tessedit_create_hocr\t\t1")
        configtmp.close()
        self._configtmp = configtmp.name

    def cleanup(self):
        super(TesseractPageSeg, self).prepare()
        os.unlink(self._configtmp)

    def process(self, binary):
        """
        Convert a full page.
        """

        self.prepare()

        hocr = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            tmp.close()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as btmp:
                btmp.close()
                self.write_binary(btmp.name, binary)
                args = self.get_command(tmp.name, btmp.name)
                self.logger.debug("Running: '%s'", " ".join(args))
                proc = sp.Popen(args, stderr=sp.PIPE)
                err = proc.stderr.read()
                if proc.wait() != 0:
                    print err
                    return u"!!! %s TESSERACT ERROR %d: %s !!!" % (
                            os.path.basename(self.binary).upper(),
                            proc.returncode, err)
                with codecs.open(tmp.name, "r", "utf8") as tread:
                    hocr = tread.read()
            os.unlink(tmp.name)
            os.unlink(btmp.name)
        utils.set_progress(self.logger, self.progress_func, 100, 100)
        self.cleanup()
        return hocr


