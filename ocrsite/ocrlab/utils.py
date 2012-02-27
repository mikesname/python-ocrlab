"""
Useful functions and classes for nodes to use.
"""

import os
import re
import tempfile
import subprocess as sp
from lxml import etree
from HTMLParser import HTMLParser
from . import cache, exceptions


class HTMLContentHandler(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._data = []
        self._ctag = None
        self._cattrs = None

    def data(self):
        return "".join(self._data)

    def content_data(self, data, tag, attrs):
        """ABC method.  Does nothing by default."""
        return data

    def parsefile(self, filename):
        with open(filename, "r") as f:
            for line in f.readlines():
                self.feed(line)
        return self.data()

    def parse(self, string):
        self._data = []
        self.feed(string)
        return self.data()

    def handle_decl(self, decl):
        self._data.append("<!%s>" % decl)

    def handle_comment(self, comment):
        self._data.append("<!-- %s -->" % comment)

    def handle_starttag(self, tag, attrs):
        """Simple add the tag to the data stack."""
        self._ctag = tag
        self._cattrs = attrs
        self._data.append(
                "<%s %s>" % (tag, " ".join(["%s='%s'" % a for a in attrs])))

    def handle_data(self, data):
        self._data.append(self.content_data(
                data, self._ctag, self._cattrs))

    def handle_endtag(self, tag):
        self._data.append("</%s>" % tag)


class HocrToTextHelper(HTMLParser):
    """
    Get text from a HOCR document.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self._text = []
        self._gotline = False

    def parsefile(self, filename):
        self._text = []
        with open(filename, "r") as f:
            for line in f.readlines():
                self.feed(line)
        return "\n".join(self._text)

    def parse(self, string):
        self._text = []
        self.feed(string)
        return "\n".join(self._text)

    def handle_starttag(self, tag, attrs):
        for name, val in attrs:
            if name == "class" and val.find("ocr_line") != -1:
                self._gotline = True
        if tag.lower() == "br":
            self._text.append("\n")
        elif tag.lower() == "p":
            self._text.append("\n\n")

    def handle_data(self, data):
        if self._gotline:
            self._text.append(data)

    def handle_endtag(self, tag):
        self._gotline = False


def merge_hocr(hocrlist):
    """Merge several HOCR files (i.e. representing
    individual columns) into one page file."""
    raise NotImplementedError


def hocr_from_data(pagedata):
    """
    Return an HOCR document (as a string).
    """
    from django.template import Template, Context
    with open(os.path.join(os.path.dirname(__file__), 
            "templates", "hocr_template.html"), "r") as tmpl:
        t = Template(tmpl.read())
        return unicode(t.render(Context(pagedata)))


def hocr_from_abbyy(abbyyxml):
    """
    Apply some XSL to transform Abbyy XML to HOCR.
    """
    with open(os.path.join(os.path.dirname(__file__), "abbyy2hocr.xsl"), "r") as tmpl:
        with open(abbyyxml, "r") as abbyy:
            xsl = etree.parse(tmpl)
            xml = etree.parse(abbyy)
            transform = etree.XSLT(xsl)
            return unicode(transform(xml))


def get_cacher(settings):
    cache_path = settings.NODETREE_PERSISTANT_CACHER.split('.')
    # Allow for Python 2.5 relative paths
    if len(cache_path) > 1:
        cache_module_name = '.'.join(cache_path[:-1])
    else:
        cache_module_name = '.'
    cache_module = __import__(cache_module_name, {}, {}, cache_path[-1])
    cacher = getattr(cache_module, cache_path[-1])
    return cacher


def get_dzi_cacher(settings):
    try:
        cachebase = get_cacher(settings)
        cacher = cache.DziFileCacher
        cacher.__bases__ = (cachebase,)
    except ImportError:
        raise exceptions.ImproperlyConfigured(
                "Error importing base cache module '%s'" % settings.NODETREE_PERSISTANT_CACHER)
    return cacher


def get_binary(binname):
    """
    Try and find where Tesseract is installed.
    """
    bin = sp.Popen(["which", binname],
            stdout=sp.PIPE).communicate()[0].strip()
    if bin and os.path.exists(bin):
        return bin

    for path in ["/usr/local/bin", "/usr/bin"]:
        binpath = os.path.join(path, binname)
        if os.path.exists(binpath):
            return binpath
    # fallback...
    return binname


def set_progress(logger, progress_func, step, end, granularity=5):
    """
    Call a progress function, if supplied.  Only call
    every 5 steps.  Also set the total todo, i.e. the
    number of lines to process.
    """
    if progress_func is None:
        return
    if not (step and end):
        return
    if step != end and step % granularity != 0:
        return
    perc = min(100.0, round(float(step) / float(end), 2) * 100)
    progress_func(perc, end)


def check_aborted(method):
    def wrapper(*args, **kwargs):
        instance = args[0]
        if instance.abort_func is not None:
            if instance.abort_func():
                instance.logger.warning("Aborted")
                raise AbortedAction(method.func_name)
        return method(*args, **kwargs)
    return wrapper


def convert_to_temp_image(imagepath, suffix="tif"):
    """
    Convert PNG to TIFF with GraphicsMagick.  This seems
    more reliable than PIL, which seems to have problems
    with Group4 TIFF encoders.
    """
    with tempfile.NamedTemporaryFile(suffix=".%s" % suffix) as tmp:
        tmp.close()
        retcode = sp.call(["convert", imagepath, tmp.name])
        if not retcode == 0:
            raise ExternalToolError(
                "convert failed to create TIFF file with errno %d" % retcode)
        return tmp.name

