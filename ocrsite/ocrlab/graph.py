"""
Utility class for displaying node scripts.
"""

import os
import re
import sys
import pydot
import json
import tempfile

class DotError(StandardError):
    """Dot problems."""


# http://www.graphviz.org/doc/info/lang.html
RAW_NAME_RE = r"(^[A-Za-z_][a-zA-Z0-9_]*$)|(^-?([.[0-9]+|[0-9]+(.[0-9]*)?)$)"


def conditional_quote(name):
    if re.match(RAW_NAME_RE, name) is None:
        return "\"%s\"" % name
    return name

def get_node_positions(nodedict, aspect=None):
    """
    Build the pydot graph.
    """
    g = pydot.Dot(margin="0.1", ranksep="0.7", nodesep="1.5")
    if aspect is not None:
        g.set_aspect(round(aspect))
    for name, node in nodedict.iteritems():
        n = pydot.Node(name, width="0.5", fixedsize="0.5")
        g.add_node(n)

    for name, node in nodedict.iteritems():
        for i in node["inputs"]:
            try:
                src = g.get_node(conditional_quote(i))
                if isinstance(src, list):
                    src = src[0]
                dst = g.get_node(conditional_quote(name))
                if isinstance(dst, list):
                    dst = dst[0]
                g.add_edge(pydot.Edge(src, dst))
            except IndexError:
                print "Input %s not found" % i
    
    # dot doesn't seem to work on < 4 nodes... prevent it from
    # by just throwing an error
    if len(nodedict) < 4:
        raise DotError("Dot breaks with less than 4 nodes.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dot") as t:
        t.close()
        g.write_dot(t.name)
    g = pydot.graph_from_dot_file(t.name)
    print "Wrote dot file %s" % t.name

    out = {}
    for name, node in nodedict.iteritems():
        gn = g.get_node(conditional_quote(name))
        if isinstance(gn, list):
            gn = gn[0]
        out[name] = [int(float(d)) \
                for d in gn.get_pos().replace('"', "").split(",")]
    return out
   
if __name__ == "__main__":
    nodes = {}
    with open(sys.argv[1], "r") as f:
        nodes = json.load(f)
    print get_node_positions(nodes)

