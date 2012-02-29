"""
Generic base classes for other nodes.
"""

from __future__ import absolute_import

import os
import codecs
import json
import subprocess as sp
import inspect

from nodetree import node, writable_node, exceptions
import ocrolib
from PIL import Image

from .. import stages, types, utils


class ExternalToolError(StandardError):
    pass

class TextWriterMixin(writable_node.WritableNodeMixin):
    """Write text data."""
    extension = ".txt"

    @classmethod
    def reader(cls, handle):
        """Read a text cache."""
        utf8reader = codecs.getreader("utf_8")(handle)
        return utf8reader.read()

    @classmethod
    def writer(cls, handle, data):
        """Write a text cache."""
        utf8writer = codecs.getwriter("utf_8")(handle)
        utf8writer.write(data)


class JSONWriterMixin(writable_node.WritableNodeMixin):
    """Functions for reading and writing a node's data in JSON format."""
    extension = ".json"

    @classmethod
    def reader(cls, handle):
        """Read a cache from a given dir."""
        return json.load(handle)

    @classmethod
    def writer(cls, handle, data):
        """Write a cache from a given dir."""
        json.dump(data, handle, ensure_ascii=False)


class PngWriterMixin(writable_node.WritableNodeMixin):
    """Object which writes/reads a PNG."""
    extension = ".png"


class BinaryPngWriterMixin(PngWriterMixin):
    """Functions for reading and writing a node's data in binary PNG."""
    @classmethod
    def reader(cls, handle):
        return ocrolib.numpy.asarray(Image.open(handle))

    @classmethod
    def writer(cls, handle, data):
        pil = Image.fromarray(data)
        pil.save(handle, "PNG")


class GrayPngWriterMixin(BinaryPngWriterMixin):
    """Functions for reading and writing a node's data in binary PNG."""
    abstract = True


class RecognizerNode(node.Node):
    """Base class for recognizer nodes."""
    @classmethod
    def get_helper_dir(cls, category):
        """Get the directory containing helper files."""
        dirname = os.path.splitext(inspect.getfile(cls))[0]
        return os.path.abspath(os.path.join(dirname, category))

    @classmethod
    def get_helper_files(cls, category):
        """Get a list of character model files."""
        dirpath = cls.get_helper_dir(category)
        if not os.path.exists(dirpath):
            return []
        return [f for f in os.listdir(dirpath) if not f.startswith(".")]


class LineRecognizerNode(RecognizerNode, TextWriterMixin):
    """Node which takes a binary and a segmentation and
    recognises text one line at a time."""
    stage = stages.RECOGNIZE
    intypes = [ocrolib.numpy.ndarray, dict]
    outtype = types.HocrString
    abstract = True

    def init_converter(self):
        raise NotImplementedError

    def get_transcript(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def prepare(self):
        pass

    def process(self, binary, boxes):
        """Recognize page text.

        input: tuple of binary, input boxes
        return: page data
        """
        self.prepare()
        pageheight, pagewidth = binary.shape
        iulibbin = ocrolib.numpy2narray(binary)
        out = dict(bbox=[0, 0, pagewidth, pageheight], lines=[])
        numlines = len(boxes.get("lines", []))
        for i in range(numlines):
            set_progress(self.logger, self.progress_func, i, numlines)
            coords = boxes.get("lines")[i]
            iulibcoords = (
                    coords[0], pageheight - coords[3], coords[2],
                    pageheight - coords[1])
            lineimage = ocrolib.iulib.bytearray()
            ocrolib.iulib.extract_subimage(lineimage, iulibbin, *iulibcoords)
            out["lines"].append(dict(
                    index=i+1,
                    bbox=[coords[0], coords[1], coords[2], coords[3]],
                    text=self.get_transcript(ocrolib.narray2numpy(lineimage)),
            ))
        set_progress(self.logger, self.progress_func, numlines, numlines)
        self.cleanup()
        return utils.hocr_from_data(out)


class ColumnRecognizerNode(RecognizerNode, TextWriterMixin):
    """Node which takes a binary and a segmentation and
    recognises each column separately."""
    stage = stages.RECOGNIZE
    intypes = [ocrolib.numpy.ndarray, dict]
    outtype = types.HocrString
    abstract = True

    def init_converter(self):
        raise NotImplementedError

    def get_transcript(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def prepare(self):
        pass

    def process(self, binary, boxes):
        """Recognize page text.

        input: tuple of binary, input boxes
        return: page data
        """
        self.prepare()
        pageheight, pagewidth = binary.shape
        iulibbin = ocrolib.numpy2narray(binary)
        out = [] # list of hocr strings
        numcols = len(boxes.get("columns", []))
        for i in range(numcols):
            set_progress(self.logger, self.progress_func, i, numcols)
            coords = boxes.get("columns")[i]
            iulibcoords = (
                    coords[0], pageheight - coords[3], coords[2],
                    pageheight - coords[1])
            colimage = ocrolib.iulib.bytearray()
            ocrolib.iulib.extract_subimage(colimage, iulibbin, *iulibcoords)
            out.append(self.get_transcript(ocrolib.narray2numpy(colimage)))
        set_progress(self.logger, self.progress_func, numcols, numcols)
        self.cleanup()
        return utils.merge_hocr(out)


def set_progress(logger, progress_func, step, end, granularity=5):
    """Call a progress function, if supplied.  Only call
    every 5 steps.  Also set the total todo, i.e. the
    number of lines to process."""
    if progress_func is None:
        return
    if not (step and end):
        return
    if step != end and step % granularity != 0:
        return
    perc = min(100.0, round(float(step) / float(end), 2) * 100)
    progress_func(perc, end)


class CommandLineRecognizerNode(LineRecognizerNode):
    """Generic recogniser based on a command line tool."""
    binary = "unimplemented"
    abstract = True

    def validate(self):
        super(CommandLineRecognizerNode, self).validate()

    def get_command(self, *args, **kwargs):
        """Get the command line for converting a given image."""
        raise NotImplementedError

    @classmethod
    def write_binary(cls, path, data):
        """Write a binary image."""
        ocrolib.iulib.write_image_binary(path.encode(), ocrolib.numpy2narray(data))

    @classmethod
    def write_packed(cls, path, data):
        """Write a packed image."""
        ocrolib.iulib.write_image_packed(path.encode(), ocrolib.pseg2narray(data))

    @utils.check_aborted
    def get_transcript(self, line):
        """Recognise each individual line by writing it as a temporary
        PNG and calling self.binary on the image."""
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            tmp.close()
            self.write_binary(tmp.name, line)
            text = self.process_line(tmp.name)
            os.unlink(tmp.name)
            return text

    @utils.check_aborted
    def process_line(self, imagepath):
        """Run OCR on image, using YET ANOTHER temporary
        file to gather the output, which is then read back in."""
        lines = []
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.close()
            args = self.get_command(outfile=tmp.name, image=imagepath)
            if not os.path.exists(args[0]):
                raise ExternalToolError("Unable to find binary: '%s'" % args[0])
            self.logger.info(args)
            proc = sp.Popen(args, stderr=sp.PIPE)
            err = proc.stderr.read()
            if proc.wait() != 0:
                return "!!! %s CONVERSION ERROR %d: %s !!!" % (
                        os.path.basename(self.binary).upper(),
                        proc.returncode, err)

            # read and delete the temp text file
            # whilst writing to our file
            with open(tmp.name, "r") as txt:
                lines = [line.rstrip() for line in txt.readlines()]
                if lines and lines[-1] == "":
                    lines = lines[:-1]
                os.unlink(txt.name)
        return unicode(" ".join(lines), "utf8")


class ImageGeneratorNode(node.Node):
    """Node which takes no input and returns an image."""
    abstract = True

    def null_data(self):
        """Return an empty numpy image."""
        return ocrolib.numpy.zeros((640,480,3), dtype=ocrolib.numpy.uint8)


class FileNode(node.Node):
    """Node which reads or writes to a file path."""
    abstract = True

    def validate(self):
        super(FileNode, self).validate()
        if self._params.get("path") is None:
            raise exceptions.ValidationError("'path' not set", self)
        path = self._params.get("path", "")
        if isinstance(path, basestring) and not os.path.exists(path):
            raise exceptions.ValidationError("'path': file not found", self)


