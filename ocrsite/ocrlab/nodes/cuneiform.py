"""
Cuneiform Recogniser
"""

from __future__ import absolute_import

import os
import codecs
import shutil
import tempfile
import subprocess as sp

import numpy

from nodetree import node

from . import base
from .. import stages, types, utils


class CuneiformRecognizer(base.CommandLineRecognizerNode):
    """
    Recognize an image using Cuneiform.
    """
    binary = "cuneiform"
    stage = stages.RECOGNIZE
    intypes = [numpy.ndarray]
    parameters = [
            dict(name="single_column", type="bool", value=False)
    ]

    def get_command(self, outfile, image):
        """
        Cuneiform command line.  Simplified for now.
        """
        args = [self.binary, "-f", "hocr", "-o", outfile]
        if self._params.get("single_column", False):
            args.extend(["--singlecolumn"])
        return args + [image]

    def process(self, binary):
        """
        Convert a full page.
        """
        hocr = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
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
                    return u"!!! %s CONVERSION ERROR %d: %s !!!" % (
                            os.path.basename(self.binary).upper(),
                            proc.returncode, err)
                with codecs.open(tmp.name, "r", "utf8") as tread:
                    hocr = tread.read()
            os.unlink(tmp.name)
            os.unlink(btmp.name)
        utils.set_progress(self.logger, self.progress_func, 100, 100)
        return hocr


