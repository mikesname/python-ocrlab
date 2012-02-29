
from __future__ import absolute_import

from nodetree import node, writable_node, exceptions
from .base import GrayPngWriterMixin
from .. import stages
import numpy


class Rotate90(node.Node, GrayPngWriterMixin):
    """Rotate a Numpy image num*90 degrees counter-clockwise."""
    stage = stages.FILTER_BINARY
    intypes = [numpy.ndarray]
    outtype = numpy.ndarray
    parameters = [{
        "name": "num",
        "value": 1,
    }]
                    
    def validate(self):
        super(Rotate90, self).validate()
        if not self._params.get("num"):
            raise exceptions.ValidationError("'num' is not set", self)
        try:
            num = int(self._params.get("num"))
        except ValueError:
            raise exceptions.ValidationError("'num' must be an integer", self)

    def process(self, image):
        return numpy.rot90(image, int(self._params.get("num", 1)))


class Rotate90Gray(Rotate90):
    """Grayscale version of above."""
    stage = stages.FILTER_GRAY


