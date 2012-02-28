"""Ocrlab views."""

import os
import json
import tempfile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from nodetree import script

from .presets import *

from ocrlab import forms, models, nodes as ocrlab_nodes, stages


def set_script_input(tree, handle):
    """Modify the given script for a specific file."""
    # get the input node and replace it with out path
    input = tree.get_nodes_by_attr("stage", stages.INPUT)[0]
    input.set_param("path", handle)
    return tree


def home(request):
    """Simple home view."""
    template = "home.html"
    form = forms.SimpleOcrForm()
    context = dict(form=form)
    if request.method == "POST":
        form = forms.SimpleOcrForm(request.POST, request.FILES)
        if form.is_valid():
            preset = form.cleaned_data["preset"]
            s = script.Script(json.loads(preset.data))
            s = set_script_input(s, form.cleaned_data["file"])
            term = s.get_terminals()[0]
            response = HttpResponse()
            response.write(term.eval())
            return response

        context.update(form=form)        
    return render(request, template, context)
