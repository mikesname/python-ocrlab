"""Model to store script data."""

import datetime
from django.db import models

from taggit.managers import TaggableManager
import jsonfield

from nodetree import script

from .base import BaseModel, DateTimeModel, NameSlugModel


class Preset(BaseModel, NameSlugModel, DateTimeModel):
    description = models.TextField(blank=True)
    data = jsonfield.JSONTextField()
    profile = models.ForeignKey("Profile", related_name="presets",
            null=True, blank=True)
    tags = TaggableManager()


TEST_PROFILE = {
    "must_exist" : [
        {
            "attr": "stage",
            "value": "recognize",
            "unique": False,
        },
        {
            "attr": "stage",
            "value": "input",
            "unique": True,
        },
    ],
}


class Profile(BaseModel, NameSlugModel, DateTimeModel):
    """Preset profile.  This defines a class of
    presets to which the information in the preset
    must conform."""
    description = models.TextField(blank=True)
    data = jsonfield.JSONTextField()
    tags = TaggableManager()

    def validate_preset(self, data):
        this = json.loads(self.data)
        tree = script.Script(data)
        errors = []
        for name, preds in this.iteritems():
            for pred in preds:
                perrors = self.validate_predicate(name, pred, tree)
                if perrors:
                    errors.extend(perrors)
        return errors

    def validate_predicate(self, name, pred, tree):
        errors = []
        if name == "must_exist":
            attr = pred.get("attr")
            value = pred.get("value")
            unique = pred.get("unique")
            nodes = tree.get_nodes_by_attr(attr, value)
            if not nodes:
                errors.append("A node with attr '%s'='%s' must exist" % (attr, value))
            elif len(nodes) > 1:
                errors.append("Node with attr '%s'='%s' must be unique" % (attr, value))
        return errors

