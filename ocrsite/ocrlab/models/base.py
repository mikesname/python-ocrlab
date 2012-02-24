"""Base class for Ocrlab models.  This shouldn't do anything fancy."""

import datetime
from django.db import models

import autoslug


class BaseModel(models.Model):
    slug = None # overrided by subclasses

    class Meta:
        app_label = "ocrlab"
        abstract = True

    @property
    def options(self):
        return self._meta

    @models.permalink
    def get_absolute_url(self):
        return ('%s_detail' % self.options.verbose_name, [self.slug])

    @models.permalink
    def get_update_url(self):
        """url to update an object detail"""
        return ("%s_update" % self.options.verbose_name, [self.slug])

    @models.permalink
    def get_delete_url(self):
        """url to update an object detail"""
        return ("%s_delete" % self.options.verbose_name, [self.slug])

    @classmethod
    @models.permalink
    def get_list_url(cls):
        """URL to view the object list"""
        return ("%s_list" % cls._meta.verbose_name, [])

    @classmethod
    @models.permalink
    def get_create_url(cls):
        """URL to create a new object"""
        return ("%s_create" % cls._meta.verbose_name, [])


class DateTimeModel(models.Model):
    """Object that has auto-update date/time attributes."""
    created_on = models.DateField(editable=False)
    updated_on = models.DateField(editable=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = datetime.datetime.now()
        else:
            self.updated_on = datetime.datetime.now()
        super(DateTimeModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class NameSlugModel(models.Model):
    """Object that has a name field from which a slug
    is automatically generated."""
    name = models.CharField(max_length=100, unique=True)
    slug = autoslug.AutoSlugField(populate_from="name", unique=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        """String representation."""
        return self.name


