"""
Nodes to perform random things.
"""

from __future__ import absolute_import

import os
import re
import codecs
import tempfile
import subprocess as sp
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from nodetree import node, writable_node, exceptions

from . import base
from .. import stages, types, utils


class NoOp(node.Node, writable_node.WritableNodeMixin):
    stage = stages.UTILS

    def __init__(self, *args, **kwargs):
        super(NoOp, self).__init__(*args, **kwargs)
        self.intypes = [type(None)]
        self.outtype = type(None)

    def validate(self):
        if self.input(0):
            self.intypes = [self._inputs[0].outtype]
            self.outtype = self._inputs[0].outtype
        super(NoOp, self).validate()


    def set_input(self, num, n):
        """
        Override the base set input to dynamically change our
        in and out types.
        """
        super(NoOp, self).set_input(num, n)
        self.intypes = [self._inputs[num].outtype]
        self.outtype = self._inputs[num].outtype

    def first_active(self):
        return self._inputs[0].first_active()

    def process(self, input):
        return input


class FindReplace(node.Node, base.TextWriterMixin):
    """
    Find an replace stuff in input with output.
    """
    stage = stages.UTILS
    intypes = [types.HocrString]
    outtype = types.HocrString
    parameters = [
        dict(name="find", value=""),
        dict(name="replace", value=""),
    ]

    def __init__(self, *args, **kwargs):
        super(FindReplace, self).__init__(*args, **kwargs)
        self._findre = None
        self._replace = None

    def validate(self):
        super(FindReplace, self).validate()
        try:
            re.compile(self._params.get("find"))
        except Exception, err:
            raise exceptions.ValidationError("find: regular expression error: %s" % err, self)

    def content_data(self, data, tag, attrs):
        """Replace all content data."""
        return self._findre.sub(self._replace, data)

    def process(self, xml):
        """
        Run find/replace on input
        """
        find = self._params.get("find", "")
        replace = self._params.get("replace", "")
        if find.strip() == "" or replace.strip() == "":
            return xml
        self._findre = re.compile(find)
        self._replace = replace
        parser = utils.HTMLContentHandler()
        parser.content_data = self.content_data
        return parser.parse(xml)


class HocrToText(node.Node, base.TextWriterMixin):
    """
    Convert HOCR to text.
    """
    stage = stages.UTILS
    intypes = [unicode]
    outtype = unicode
    parameters = []

    def process(self, input):
        soup = BeautifulSoup(input)
        raw = ''.join(soup.find("div", {"class":"ocr_page"}).findAll(text=True))
        decode = BeautifulStoneSoup(raw, 
                convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        return re.sub("[\n]{3,100}", "\n\n", decode.text)


class TextFileIn(base.FileNode, base.TextWriterMixin):
    """
    Read a text file.  That's it.
    """
    stage = stages.INPUT
    intypes = []
    outtype = unicode
    parameters = [dict(name="path", value="", type="filepath")]

    def process(self):
        with open(self._params.get("path"), "r") as fh:
            return self.reader(fh)


class Switch(node.Node, writable_node.WritableNodeMixin):
    """
    Node which passes through its selected input.
    """
    stage = stages.UTILS
    intypes = [object, object]
    outtype = type(None)
    parameters = [dict(name="input", value=0, type="switch")]

    def __init__(self, *args, **kwargs):
        self.arity = kwargs.get("arity", 2)
        self.intypes = [object for i in range(self.arity)]
        self.outtype = object
        super(Switch, self).__init__(*args, **kwargs)

    def active_input(self):
        """The active child node."""
        input = int(self._params.get("input", 0))
        return self._inputs[input]

    def validate_all(self):
        """Only validate active input."""
        active = self.active_input()
        if active is not None:
            active.validate_all()
        self.validate()

    def early_eval(self):
        """Pass through the selected input."""
        input = int(self._params.get("input", 0))
        return self.eval_input(input)

    def set_input(self, num, n):
        """
        Override the base set input to dynamically change our
        in and out types.
        """
        super(Switch, self).set_input(num, n)
        input = int(self._params.get("input", 0))
        if input == num:
            self.outtype = self._inputs[input].outtype

    def first_active(self):
        if self.arity > 0 and self.ignored:
            return self._inputs[self.passthrough].first_active()
        input = int(self._params.get("input", 0))
        return self._inputs[input].first_active()

    def get_file_name(self):
        input = int(self._params.get("input", 0))
        if self.input(input):
            return "%s%s" % (self.input(input), self.input(input).extension)
        return "%s%s" % (self.input(input), self.extension)

    def writer(self, fh, data):
        """
        Pass through the writer function from the selected node.
        """
        input = int(self._params.get("input", 0))
        if self.input(input):
            return self.input(input).writer(fh, data)
        
    def reader(self, fh):
        """
        Pass through the writer function from the selected node.
        """
        input = int(self._params.get("input", 0))
        if self.input(input):
            return self.input(input).reader(fh)
        

class FileOut(node.Node, writable_node.WritableNodeMixin):
    """
    A node that writes a file to disk.
    """
    stage = stages.OUTPUT
    outtype = type(None)
    parameters = [
            dict(name="path", value="", type="filepath"),
            dict(name="create_dir", value=False, type="bool"),
    ]

    def validate(self):
        """
        Check params are OK.
        """
        if self._params.get("path") is None:
            raise exceptions.ValidationError("'path' not set", self)

    def set_input(self, num, n):
        """
        Override the base set input to dynamically change our
        in and out types.
        """
        super(FileOut, self).set_input(num, n)
        self.outtype = self._inputs[num].outtype

    def null_data(self):
        """
        Return the input.
        """
        next = self.first_active()
        if next is not None:
            return next.eval()

    def get_file_name(self):
        if self.input(0):
            return "%s%s" % (self.input(0), self.input(0).extension)
        return "%s%s" % (self, self.extension)

    def writer(self, fh, data):
        """
        Pass through the writer function from the selected node.
        """
        if self.input(0):
            return self.input(0).writer(fh, data)
        
    def reader(self, fh):
        """
        Pass through the writer function from the selected node.
        """
        if self.input(0):
            return self.input(0).reader(fh)
        
    def process(self, input):
        """
        Write the input to the given path.
        """
        if input is None:
            return
        if not os.environ.get("NODETREE_WRITE_FILEOUT"):
            return input
        path = self._params.get("path")
        if not os.path.exists(os.path.dirname(path)) and self._params.get("create_dir", False):
            os.makedirs(os.path.dirname(path), 0777)
        with open(path, "w") as fh:
            self._inputs[0].writer(fh, input)
        return input


class TextEvaluation(node.Node, base.TextWriterMixin):
    """
    Evaluate two text inputs with ISRI accuracy program.
    """
    stage = stages.UTILS
    intypes = [unicode, unicode]
    outtype = unicode
    parameters = [
        dict(name="method", value="character",
                choices=["character", "word"]),
    ]

    def process(self, intext, gttext):
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as t1:
            with tempfile.NamedTemporaryFile(delete=False, mode="wb") as t2:
                self.writer(t1, gttext)
                self.writer(t2, intext)
        writer = codecs.getwriter("utf8")(sp.PIPE)
        method = self._params.get("method", "character")
        bin = "accuracy" if method == "character" else "wordacc"
        p = sp.Popen([bin, t1.name, t2.name], stdout=writer)
        report = p.communicate()[0]
        os.unlink(t1.name)
        os.unlink(t2.name)
        return unicode(report, "utf8", "replace")


class TextDiff(node.Node, base.TextWriterMixin):
    """
    Do a side-by-side.
    """
    stage = stages.UTILS
    intypes = [unicode, unicode]
    outtype = unicode
    parameters = [dict(name="format", value="normal",
        choices=("normal", "side-by-side", "rcs"))]

    def process(self, intext, gttext):
        format = self._params.get("format", "normal")
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as t1:
            with tempfile.NamedTemporaryFile(delete=False, mode="wb") as t2:
                self.writer(t1, gttext)
                self.writer(t2, intext)
        writer = codecs.getwriter("utf8")(sp.PIPE)
        p = sp.Popen(["diff", "--%s" % format, t1.name, t2.name], stdout=writer)
        report = p.communicate()[0]
        os.unlink(t1.name)
        os.unlink(t2.name)
        return unicode(report, "utf8", "replace")


class AbbyyXmlToHocr(node.Node, base.TextWriterMixin):
    """
    Convert Abbyy XML to HOCR.
    """
    stage = stages.UTILS
    intypes = [unicode]
    outtype = unicode
    parameters = []

    def process(self, intext):
        out = ""
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as t1:
            self.writer(t1, intext)
            t1.close()
            out = utils.hocr_from_abbyy(t1.name)
            os.unlink(t1.name)
        return out

