"""
Cuneiform Recogniser
"""

from __future__ import absolute_import

import os
import shutil
import tempfile
import subprocess as sp

from nodetree import node

import numpy
from . import base
from .. import utils, stages, types


class AbbyyRecognizer(base.CommandLineRecognizerNode):
    """
    Recognize an image using Abbyy Finereader.
    """
    binary = "abbyyocr"
    stage = stages.RECOGNIZE
    intypes = [numpy.ndarray]
    parameters = [
        dict(name="single_column", type="bool", value=False),
        dict(name="invert_image", type="bool", value=False),
        dict(name="no_despeckle", type="bool", value=False),
    ]

    def get_command(self, outfile, image):
        """
        Cuneiform command line.  Simplified for now.
        """
        args = [self.binary]
        if self._params.get("invert_image", False):
            args.append("--invertImage")
        if self._params.get("no_despeckle", False):
            args.append("--dontDespecleImage")
        if self._params.get("single_column", False):
            args.append("--singleColumnMode")
        args.extend(["-if", image, "-f", "XML", "-of", outfile])
        return args

    def set_image_dpi(self, image):
        """
        Hack to set 300 PPI on all images.  This should hopefully
        prevent FR from using up thousands of pages of license
        if there's no resolution header available.
        """
        p = sp.Popen(["convert", "-units", "PixelsPerInch",
                "-density", "300", image, image])
        return p.wait()

    def process(self, binary):
        """
        Convert a full page.
        """
        hocr = ""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.close()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as btmp:
                btmp.close()
                self.write_binary(btmp.name, binary)
                self.set_image_dpi(btmp.name)
                args = self.get_command(tmp.name, btmp.name)
                self.logger.debug("Running: '%s'", " ".join(args))
                proc = sp.Popen(args, stderr=sp.PIPE)
                err = proc.stderr.read()
                if proc.wait() != 0:
                    return "!!! %s CONVERSION ERROR %d: %s !!!" % (
                            os.path.basename(self.binary).upper(),
                            proc.returncode, err)
                hocr = utils.hocr_from_abbyy(tmp.name)
            os.unlink(tmp.name)
            os.unlink(btmp.name)
        utils.set_progress(self.logger, self.progress_func, 100, 100)
        return hocr
