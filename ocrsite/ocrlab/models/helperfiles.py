"""Object representing a helper file for an OCR app."""

import datetime
from django.db import models
from taggit.managers import TaggableManager
import autoslug

from .base import BaseModel, DateTimeModel, NameSlugModel

__all__ = ["HelperFileApp", "HelperFileType", "HelperFile"]


class HelperFileApp(BaseModel, NameSlugModel):
    """App which has helper files."""
    class Meta:
        verbose_name = "helperfileapp"
    description = models.TextField(blank=True)


class HelperFileType(BaseModel, NameSlugModel):
    """Type of file helper."""
    class Meta:
        verbose_name = "helperfiletype"
    description = models.TextField(blank=True)


class HelperFile(BaseModel, NameSlugModel, DateTimeModel):
    """File which can be referenced by an OCR node."""
    class Meta:
        verbose_name = "helperfile"
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="models")
    type = models.ForeignKey(HelperFileType)
    app = models.ForeignKey(HelperFileApp)
    tags = TaggableManager()

