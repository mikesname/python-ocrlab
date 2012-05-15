"""
Run a script that takes a file input/output.
"""

import os
import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.utils import simplejson as json

from ocrlab import models, stages, nodes
from nodetree import script, registry

class Command(BaseCommand):
    args = "<scriptfile1> <infile> <outfile>"
    help = "Run a script on a given file, saving the output."
    option_list = BaseCommand.option_list + (
            # TODO: Add options...
        )

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("Usage: %s" % self.help)
        scriptfile, infile, outfile = args

        try:
            with open(scriptfile, "r") as f:
                nodes = json.load(f)
        except Exception:
            raise CommandError("Invalid script file: %s" % scriptfile)
        if nodes is None:
            raise CommandError("No nodes found in script: %s" % scriptfile)

        s = script.Script(nodes)
        input = s.get_nodes_by_attr("stage", stages.INPUT)[0]
        input.set_param("path", infile)

        term = s.get_terminals()[0]
        sys.stderr.write("Rendering to %s\n" % outfile)
        os.environ["NODETREE_WRITE_FILEOUT"] = "1"
        out = s.add_node("util.FileOut", "Output",
                params=[("path", os.path.abspath(outfile))])
        out.set_input(0, term)
        out.eval()


