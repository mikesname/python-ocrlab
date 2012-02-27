#!/usr/bin/python

import os
import glob
import sys
import json
sys.path.append(os.path.abspath(".."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'ocrsite.settings'

from ocrlab import nodes as nodetree_nodes

from nodetree import script, registry


def run(nodelist, outpath):
    s = script.Script(nodelist)
    term = s.get_terminals()[0]
    print "Rendering to %s" % outpath
    os.environ["NODETREE_WRITE_FILEOUT"] = "1"
    out = s.add_node("util.FileOut", "Output",
            params=[("path", os.path.abspath(outpath))])
    out.set_input(0, term)
    out.eval()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <script> <output>" % sys.argv[0]
        sys.exit(1)

    nodes = None
    with open(sys.argv[1], "r") as f:
        nodes = json.load(f)

    if nodes is None:
        print "No nodes found in script"
        sys.exit(1)

    run(nodes, sys.argv[2])
