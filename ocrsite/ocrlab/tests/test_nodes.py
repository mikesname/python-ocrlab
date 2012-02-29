"""
    Test the scripts.
"""
import os
import glob
from django.test import TestCase
from django.utils import simplejson as json
from django.conf import settings

from nodetree import script, node, exceptions
import numpy

from ocrlab import nodes

VALID_SCRIPTDIR = "ocrlab/scripts/valid"
INVALID_SCRIPTDIR = "ocrlab/scripts/invalid"


class ScriptsTest(TestCase):
    def setUp(self):
        """
            Setup OCR tests.  These run directly, not via views.
        """
        self.validscripts = {}
        self.invalidscripts = {}
        for fname in os.listdir(VALID_SCRIPTDIR):
            if fname.endswith("json"):
                with open(os.path.join(VALID_SCRIPTDIR, fname), "r") as f:
                    self.validscripts[fname] = json.load(f)
        for fname in os.listdir(INVALID_SCRIPTDIR):
            if fname.endswith("json"):
                with open(os.path.join(INVALID_SCRIPTDIR, fname), "r") as f:
                    self.invalidscripts[fname] = json.load(f)
        
    def tearDown(self):
        """
            Cleanup a test.
        """
        pass

    def test_valid_scripts(self):
        """
        Test the supposedly valid script don't raise errors.
        """
        for name, nodes in self.validscripts.iteritems():
            if name.startswith("invalid"):
                continue
            s = script.Script(nodes)
            terms = s.get_terminals()
            self.assertTrue(len(terms) > 0, msg="No terminal nodes found.")

            # check we get an expected type from evaling the nodes
            for n in terms:
                out = n.eval()
                self.assertIn(type(out), (unicode, dict, list, numpy.ndarray),
                        msg="Unexpected output type for node %s: %s" % (
                            n.name, type(out)))

    def test_invalid_scripts(self):
        """
        Test supposedly invalid script DO raise errors.
        """
        for name, nodes in self.invalidscripts.iteritems():
            if not name.startswith("invalid"):
                continue
            s = script.Script(nodes)
            terms = s.get_terminals()
            self.assertTrue(len(terms) > 0, msg="No terminal nodes found.")
            # check we get an expected type from evaling the nodes
            for n in terms:
                self.assertRaises(exceptions.ValidationError, n.eval)



        


