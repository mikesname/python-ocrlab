"""Field that handles JSON data."""

import json
from django.db import models

from south.modelsinspector import add_introspection_rules

__all__ = ["JSONTextField",]


class JSONTextField(models.TextField):
    def to_python(self, value):
        return value

    def validate(self, value, *args, **kwargs):
        super(models.TextField, self).validate(value, *args, **kwargs)
        try:
            json.loads(value)
        except ValueError:
            raise models.exceptions.ValidationError("Data must be valid JSON")


# get South to play nice with ImageWithThumbsField
add_introspection_rules(
    [
        (
            (JSONTextField, ),
            [],
            {
                "name":         ["name",         {"default": None}],
            },
        ),
    ],
    ["^ocrlab\.models\.jsonfield\.JSONTextField",]
)





