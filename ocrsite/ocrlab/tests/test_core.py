"""Core tests.  Test general environment."""

import subprocess as sp
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.conf import settings


class CoreTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_isri_tools(self):
        """
        Ensure running 'accuracy' with no args results
        in usage info.  Basically we want to make sure
        that the accuracy binary is available.
        """
        stdout, stderr = self._run_cmd("accuracy")
        self.assertRegexpMatches(stderr, "^Usage")

    def test_cuneiform(self):
        """
        Ensure cuneiform is available.  This is fragile since it depends
        on Cuneiform's annoying output on stdout.
        """
        stdout, stderr = self._run_cmd("cuneiform")
        self.assertRegexpMatches(stdout, "^Cuneiform for Linux")

    def test_tesseract(self):
        """
        Ensure tesseract is available.
        """
        stdout, stderr = self._run_cmd("tesseract")
        self.assertRegexpMatches(stderr, "Usage")

    def test_convert(self):
        """
        Ensure (Image|Graphics)Magick is available.
        """
        stdout, stderr = self._run_cmd("convert")
        self.assertRegexpMatches(stdout, "Usage")

    def test_PIL(self):
        """
        Make sure PIL >= 1.1 is available.
        """
        from PIL import Image
        version = [int(v) for v in Image.VERSION.split(".")]
        self.assertGreaterEqual(version[1], 1)

    def test_numpy(self):
        """
        Make sure numpy >= 1.4 is available.
        """
        from numpy import version
        version = [int(v) for v in version.version.split(".")]
        self.assertGreaterEqual(version[1], 4)

    def test_ocrolib(self):
        """
        Just check importing ocrolib doesn't error.
        """
        import ocrolib

    def _run_cmd(self, *args):
        p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
        return p.communicate()

