"""
Nodes for interoperating with Fedora Commons.
"""

import os
import ocrolib
from nodetree import node, exceptions
from cStringIO import StringIO

from . import base, util as utilnodes
from .. import stages, utils

from eulfedora.server import Repository
from eulfedora.models import DigitalObject, FileDatastream
from eulfedora.util import RequestFailed
from PIL import Image


class FedoraIOMixin(object):
    """Common Mixin for objects that require access to a
    Fedora Repository."""
    parameters = [
            dict(name="url", value="http://localhost:8080/fedora/"),
            dict(name="username", value="fedoraAdmin"),
            dict(name="password", value="fedora"),
            dict(name="pid", value=""),
            dict(name="dsid", value=""),
    ]

    def validate(self):
        super(FedoraIOMixin, self).validate()
        missing = []
        for pname in [p["name"] for p in self.parameters]:
            if not self._params.get(pname, "").strip():
                missing.append(pname)
        if missing:
            raise exceptions.ValidationError(
                    "Missing parameter(s): %s" % ", ".join(missing), self)



def get_fedora_proxy_class(dsid):
    fcm = "info:fedora/genrepo:File-1.0"
    return type("FedoraProxyObject", (DigitalObject,), dict(
        FILE_CONTENT_MODEL=fcm,
        CONTENT_MODELS=[fcm],
        DATASTREAM=FileDatastream(dsid, "Binary datastream", defaults={
            "versionable": True,
        })
    ))


class FedoraImageIn(FedoraIOMixin, base.ImageGeneratorNode,
            base.GrayPngWriterMixin):
    stage = stages.INPUT
    intypes = []
    outtype = ocrolib.numpy.ndarray

    def process(self):
        repo = Repository(self._params.get("url"), self._params.get("username"),
                self._params.get("password"))
        # Fixme... this is not the correct way of downloading a datastream!
        try:
            iodata = StringIO(repo.api.getDatastreamDissemination(
                    self._params.get("pid"), self._params.get("dsid"))[0])
            pil = Image.open(iodata)
        except IOError:
            raise exceptions.NodeError(
                    "Error reading datastream contents as an image.", self)
        except RequestFailed:
            raise exceptions.NodeError(
                    "Error communicating with Fedora Repository: 404", self)
        return ocrolib.numpy.asarray(pil)


class FedoraImageOut(FedoraIOMixin, utilnodes.FileOut):
    """
    Update/Input an image datastream to a Fedora Object
    """
    stage = stages.OUTPUT
    outtype = type(None)

    parameters = FedoraIOMixin.parameters + [
        dict(name="format", value="png", choices=[
            "png", "jpeg", "tif", "gif"
        ]),
    ]

    def validate(self):
        missing = []
        for pname in [p["name"] for p in self.parameters]:
            if not self._params.get(pname, "").strip():
                missing.append(pname)
        if missing:
            raise exceptions.ValidationError(
                    "Missing parameter(s): %s" % ", ".join(missing), self)

    def process(self, input):
        """
        Write the input to the given path.
        """
        if input is None:
            return
        #if not os.environ.get("NODETREE_WRITE_FILEOUT"):
        #    return input

        repo = Repository(self._params.get("url"), self._params.get("username"),
                self._params.get("password"))
        try:
            buf = StringIO()
            Image.fromarray(input).save(buf, self._params.get("format").upper())
        except IOError:
            raise exceptions.NodeError(
                    "Error obtaining image buffer in format: %s" % 
                        self._params.get("format").upper(), self)

        pclass = get_fedora_proxy_class(self._params.get("dsid"))
        obj = repo.get_object(self._params.get("pid"), type=pclass)
        obj.DATASTREAM.content = buf
        obj.DATASTREAM.label = "Test Ingest Datastream 1"
        obj.DATASTREAM.mimetype = "image/%s" % self._params.get("format")
        obj.save()
        return input


