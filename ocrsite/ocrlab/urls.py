"""Ocrlab URLs."""

from django.conf.urls.defaults import *
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from django.utils.functional import lazy
from django.core.urlresolvers import reverse

# Workaround for using reverse with success_url in class based generic views
# because direct usage of it throws an exception.
reverse_lazy = lambda name=None, *args : lazy(reverse, str)(name, args=args)


import views, models, forms

PAGINATE_BY = 10


urlpatterns = patterns('',
    url(r'^$', views.home, name="home"),
    url(r'^progress/(?P<task_id>[a-z0-9-]+)/?$',
            views.progress, name='ocr_progress'),

    url(r'^presets/?$', ListView.as_view(
            model=models.Preset,
            template_name="object_list.html",
            paginate_by=PAGINATE_BY), name="preset_list"),
    url(r'^presets/create/?$', CreateView.as_view(
            model=models.Preset,
            template_name="object_create.html",
            success_url=reverse_lazy("preset_list")
            ), name="preset_create"),
    url(r'^presets/update/(?P<slug>[-\w]+)/?$', UpdateView.as_view(
            model=models.Preset,
            template_name="object_update.html",
            success_url=reverse_lazy("preset_list")
            ), name="preset_update"),
    url(r'^presets/delete/(?P<slug>[-\w]+)/?$', DeleteView.as_view(
            model=models.Preset,
            template_name="object_delete.html",
            success_url=reverse_lazy("preset_list")
            ), name="preset_delete"),
    url(r'^presets/detail/(?P<slug>[-\w]+)/?$', DetailView.as_view(
            model=models.Preset,
            template_name="object_detail.html"
            ), name="preset_detail"),

)


