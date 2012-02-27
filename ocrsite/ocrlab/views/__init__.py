"""Ocrlab views."""

import os
import json
import tempfile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from nodetree import script

from .presets import *

from ocrlab import forms, models, nodes as ocrlab_nodes, stages


def save_to_temp(f):
    ext = os.path.splitext(f.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        for chunk in f.chunks():
            temp.write(chunk)
        temp.close()
    return temp.name


def set_script_input(scriptjson, filepath):
    """Modify the given script for a specific file."""
    tree = script.Script(json.loads(scriptjson))
    # get the input node and replace it with out path
    input = tree.get_nodes_by_attr("stage", stages.INPUT)[0]
    input.set_param("path", filepath)
    return json.dumps(tree.serialize(), indent=2)


def home(request):
    """Simple home view."""
    template = "home.html"
    form = forms.SimpleOcrForm()
    context = dict(form=form)
    if request.method == "POST":
        form = forms.SimpleOcrForm(request.POST, request.FILES)
        if form.is_valid():
            preset = form.cleaned_data["preset"]
            name = request.FILES["file"].name
            temppath = save_to_temp(request.FILES["file"])
            try:
                scriptjson = set_script_input(preset.data, temppath)
                s = script.Script(json.loads(scriptjson))
                term = s.get_terminals()[0]

                response = HttpResponse()
                response.write(term.eval())
                return response
            finally:
                os.unlink(temppath)

        context.update(form=form)        
    return render(request, template, context)
