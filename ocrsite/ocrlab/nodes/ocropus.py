"""Ocropus OCR processing nodes."""

import os
import sys
import json

from nodetree import node, writable_node, exceptions
from nodetree import utils as nodeutils

import ocrolib

from . import base
from .. import stages, utils

class UnknownOcropusNodeType(Exception):
    pass

class NoSuchNodeException(Exception):
    pass

class OcropusNodeError(exceptions.NodeError):
    pass


def makesafe(val):
    """The Ocropus libs don't like unicode, so ensure we
    use standard strings."""
    if isinstance(val, unicode):
        return val.encode()
    return val


class GrayFileIn(base.ImageGeneratorNode,
            base.FileNode, base.GrayPngWriterMixin):
    """
    A node that takes a file and returns a numpy object.
    """
    stage = stages.INPUT
    intypes = []
    outtype = ocrolib.numpy.ndarray
    parameters = [dict(name="path", value="", type="filepath")]

    def process(self):
        # TODO: Ensure we can also read a filehandle
        if not os.path.exists(self._params.get("path", "")):
            return self.null_data()
        return ocrolib.read_image_gray(makesafe(self._params.get("path")))
        

class Crop(node.Node, base.BinaryPngWriterMixin):
    """
    Crop a PNG input.
    """
    stage = stages.FILTER_BINARY
    intypes = [ocrolib.numpy.ndarray]
    outtype = ocrolib.numpy.ndarray
    parameters = [
        dict(name="x0", value=-1),
        dict(name="y0", value=-1),
        dict(name="x1", value=-1),
        dict(name="y1", value=-1),
    ]

    def process(self, input):
        """
        Crop an image, using IULIB.  If any of
        the parameters are -1 or less, use the
        outer dimensions.
        """
        x0, y0 = 0, 0
        y1, x1 = input.shape
        try:
            x0 = int(self._params.get("x0", -1))
            if x0 < 0: x0 = 0
        except TypeError: pass
        try:
            y0 = int(self._params.get("y0", -1))
            if y0 < 0: y0 = 0
        except TypeError: pass
        try:
            x1 = int(self._params.get("x1", -1))
            if x1 < 0: x1 = input.shape[1]
        except TypeError: pass
        try:
            y1 = int(self._params.get("y1", -1))
            if y1 < 0: y1 = input.shape[0]
        except TypeError: pass
        # flip the coord system from HOCR to internal
        iy0 = input.shape[1] - y1
        iy1 = input.shape[1] - y0i
        iulibbin = ocrolib.numpy2narray(input)
        out = ocrolib.iulib.bytearray()
        ocrolib.iulib.extract_subimage(out, iulibbin, x0, iy0, x1, iy1)
        return ocrolib.narray2numpy(out)


class OcropusBase(node.Node):
    """
    Wrapper around Ocropus component interface.
    """
    abstract = True
    _comp = None

    def __init__(self, **kwargs):
        """
        Initialise with the ocropus component.
        """
        super(OcropusBase, self).__init__(**kwargs)

    def _set_p(self, p, v):
        """
        Set a component param.
        """
        self._comp.pset(makesafe(p), makesafe(v))

    def __getstate__(self):
        """
        Used when pickled.  Here we simply ignore the
        internal component, which itself contains an
        unpickleable C++ type.
        """
        return super(OcropusBase, self).__dict__

    def validate(self):
        """
        Check state of the inputs.
        """
        self.logger.debug("%s: validating...", self)
        super(OcropusBase, self).validate()
        for i in range(len(self._inputs)):
            if self._inputs[i] is None:
                raise exceptions.ValidationError("missing input '%d'" % i, self)

    @nodeutils.ClassProperty
    @classmethod
    def parameters(cls):
        """
        Get parameters from an Ocropus Node.
        """
        def makesafe(v):
            if v is None:
                return 0
            return v
        p = []
        for i in range(cls._comp.plength()):
            n = cls._comp.pname(i)
            p.append(dict(
                name=n,
                value=makesafe(cls._comp.pget(n)),
            ))
        return p


class OcropusBinarizeBase(OcropusBase, base.BinaryPngWriterMixin):
    """
    Binarize an image with an Ocropus component.
    """
    abstract = True
    stage = stages.BINARIZE
    intypes = [ocrolib.numpy.ndarray]
    outtype = ocrolib.numpy.ndarray

    def process(self, input):
        """
        Perform binarization on an image.
        
        input: a grayscale image.
        return: a binary image.
        """
        # NB. The Ocropus binarize function
        # returns a tuple: (binary, gray)
        # we ignore the latter.
        try:
            out = self._comp.binarize(input, type="B")[0]
        except (IndexError, TypeError, ValueError), err:
            raise OcropusNodeError(err.message, self)
        return out


class OcropusSegmentPageBase(OcropusBase, base.JSONWriterMixin):
    """
    Segment an image using Ocropus.
    """
    abstract = True
    stage = stages.PAGE_SEGMENT
    intypes = [ocrolib.numpy.ndarray]
    outtype = dict

    def null_data(self):
        """
        Return an empty list when ignored.
        """
        return dict(columns=[], lines=[], paragraphs=[])

    def process(self, input):
        """
        Segment a binary image.

        input: a binary image.
        return: a dictionary of box types:
            lines
            paragraphs
            columns
            images
        """
        out = dict(bbox=[0, 0, input.shape[1], input.shape[0]],
                columns=[], lines=[], paragraphs=[])
        try:
            page_seg = self._comp.segment(input)
        except (IndexError, TypeError, ValueError), err:
            raise OcropusNodeError(err.message, self)
        regions = ocrolib.RegionExtractor()
        exfuncs = dict(lines=regions.setPageLines,
                paragraphs=regions.setPageParagraphs)
        # NB: These coordinates are relative to the TOP of the page
        # for some reason
        for box, func in exfuncs.iteritems():
            func(page_seg)
            for i in range(1, regions.length()):
                out[box].append((
                    regions.x0(i), regions.y0(i), regions.x1(i), regions.y1(i)))
        return out


class OcropusGrayscaleFilterBase(OcropusBase, base.GrayPngWriterMixin):
    """
    Filter a binary image.
    """
    abstract = True
    stage = stages.FILTER_GRAY
    intypes = [ocrolib.numpy.ndarray]
    outtype = ocrolib.numpy.ndarray

    def process(self, input):
        try:
            out = self._comp.cleanup_gray(input, type="B")
        except (IndexError, TypeError, ValueError), err:
            raise OcropusNodeError(err.message, self)
        return out



class OcropusBinaryFilterBase(OcropusBase, base.BinaryPngWriterMixin):
    """
    Filter a binary image.
    """
    abstract = True
    stage = stages.FILTER_BINARY
    intypes = [ocrolib.numpy.ndarray]
    outtype = ocrolib.numpy.ndarray

    def process(self, input):
        try:
            out = self._comp.cleanup(input, type="B")
        except (IndexError, TypeError, ValueError), err:
            raise OcropusNodeError(err.message, self)
        return out


class OcropusRecognizer(base.LineRecognizerNode):
    """Ocropus Native text recogniser."""

    @nodeutils.ClassProperty
    @classmethod
    def parameters(cls):
        chars = cls.get_helper_files("char")
        if not chars:
            raise OcropusNodeError("No character models available", None)
        langs = cls.get_helper_files("lang")
        if not langs:
            raise OcropusNodeError("No language models available", None)
        return [
            dict(name="character_model", value=chars[0], choices=chars), 
            dict(name="language_model",  value=langs[0], choices=langs)
        ]

    def validate(self):
        """Check we're in a good state."""
        super(OcropusRecognizer, self).validate()
        if self._params.get("character_model", "").strip() == "":
            raise exceptions.ValidationError("no character model given.", self)
        if self._params.get("language_model", "").strip() == "":
            raise exceptions.ValidationError("no language model given: %s" % self._params, self)

    def init_converter(self):
        """
        Load the line-recogniser and the lmodel FST objects.
        """
        try:
            self._linerec = ocrolib.RecognizeLine()
            cmodpath = os.path.join(self.get_helper_dir("char"), 
                    self._params["character_model"])
            self.logger.debug("Loading char mod file: %s" % cmodpath)
            self._linerec.load_native(cmodpath.encode())
            self._lmodel = ocrolib.OcroFST()
            lmodpath = os.path.join(self.get_helper_dir("lang"), 
                    self._params["language_model"])
            self.logger.debug("Loading lang mod file: %s" % lmodpath)
            self._lmodel.load(lmodpath.encode())
        except (StandardError, RuntimeError):
            raise

    @utils.check_aborted
    def get_transcript(self, line):
        """
        Run line-recognition on an ocrolib.iulib.bytearray images of a
        single line.
        """
        if not hasattr(self, "_lmodel"):
            self.init_converter()
        fst = self._linerec.recognizeLine(line)
        # NOTE: This returns the cost - not currently used
        out, _ = ocrolib.beam_search_simple(fst, self._lmodel, 1000)
        return out

class Manager(object):
    """
    Interface to ocropus.
    """
    _use_types = (
        "IBinarize",
        "ISegmentPage",
        "ICleanupGray",
        "ICleanupBinary",
    )
    _ignored = (
        "StandardPreprocessing",
    )

    @classmethod
    def get_components(cls, oftypes=None, withnames=None, exclude=None):
        """
        Get a datastructure contraining all Ocropus components
        (possibly of a given type) and their default parameters.
        """
        return cls._get_native_components(oftypes, withnames, exclude=exclude)
    
    
    @classmethod
    def get_node(cls, name, **kwargs):
        """
        Get a node by the given name.
        """
        klass = cls.get_node_class(name)
        return klass(**kwargs)

    @classmethod
    def get_node_class(cls, name, comps=None):
        """
        Get a node class for the given name.
        """
        # if we get a qualified name like
        # Ocropus::Recognizer, remove the
        # path, since we ASSume that we're
        # looking in the right module
        if name.find("::") != -1:
            name = name.split("::")[-1]

        # FIXME: This clearly sucks
        comp = None
        if comps is not None:
            for c in comps:
                if name == c.__class__.__name__:
                    comp = c
                    break
        else:
            comp = getattr(ocrolib, name)()
        if node is None:
            raise NoSuchNodeException(name)

        base = OcropusBase
        if comp.interface() == "IBinarize":
            base = OcropusBinarizeBase
        elif comp.interface() == "ISegmentPage":
            base = OcropusSegmentPageBase
        elif comp.interface() == "ICleanupGray":
            base = OcropusGrayscaleFilterBase
        elif comp.interface() == "ICleanupBinary":
            base = OcropusBinaryFilterBase
        else:
            raise UnknownOcropusNodeType("%s: '%s'" % (name, comp.interface()))
        # this is a bit weird
        # create a new class with the name '<OcropusComponentName>Node'
        # and the component as the inner _comp attribute
        return type("%s" % comp.__class__.__name__, (base,), dict(
            _comp=comp,
            __module__=__name__
        ))

    @classmethod
    def get_nodes(cls, *oftypes, **kwargs):
        """
        Get nodes of the given type.
        """
        rawcomps = cls.get_components(oftypes=cls._use_types, exclude=cls._ignored)
        return [cls.get_node_class(comp.__class__.__name__, comps=rawcomps) \
                for comp in rawcomps]



    @classmethod
    def _get_native_components(cls, oftypes=None, withnames=None, exclude=None):
        """
        Get a datastructure contraining all Ocropus native components
        (possibly of a given type) and their default parameters.
        """
        out = []
        clist = ocrolib.ComponentList()
        for i in range(clist.length()):
            ckind = clist.kind(i)
            if oftypes and not \
                    ckind.lower() in [c.lower() for c in oftypes]:
                continue
            cname = clist.name(i)
            if withnames and not \
                    cname.lower() in [n.lower() for n in withnames]:
                continue
            if exclude and cname.lower() in [n.lower() for n in exclude]:
                continue
            compdict = dict(name=cname, type=ckind, parameters=[])
            # TODO: Fix this heavy-handed exception handling which is
            # liable to mask genuine errors - it's needed because of
            # various inconsistencies in the Python/native component
            # wrappers.
            try:
                comp = getattr(ocrolib, cname)()
            except (AttributeError, AssertionError, IndexError):
                continue
            out.append(comp)
        return out


# dynamically generate new nodes classes
Manager.get_nodes()



