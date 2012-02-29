"""Ocrlab views."""

import os
import json
import tempfile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from celery import result
from .presets import *

from ocrlab import forms, models, tasks



def save_to_temp(f):
    ext = os.path.splitext(f.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        for chunk in f.chunks():
            temp.write(chunk)
        temp.close()
    return temp.name


def home(request):
    """Simple home view."""
    template = "home.html"
    form = forms.SimpleOcrForm()
    context = dict(form=form)
    if request.method == "POST":
        form = forms.SimpleOcrForm(request.POST, request.FILES)
        if form.is_valid():
            preset = form.cleaned_data["preset"]
            if form.cleaned_data["async"]:
                # run task asyncronously redirecting to the progress page.
                # save the file handle so it can be accessed from the 
                # (possibly remote) worker.
                temppath = save_to_temp(form.cleaned_data["file"])
                async = tasks.OcrTask.delay(preset.id, temppath)
                return redirect("ocr_progress", task_id=async.task_id)
            res = tasks.OcrTask.run_preset(preset, form.cleaned_data["file"])
            response = HttpResponse()
            response.write(res)
            return response

        context.update(form=form)        
    return render(request, template, context)


def progress(request, task_id):
    """Show progress for a running import."""
    template = "progress.html" if not request.is_ajax() \
            else "_progress.html"
    async = result.AsyncResult(task_id)
    context = dict(async=async)
    progress = 0
    if async.status == "PROGRESS":
        info = async.info
        progress = round(float(info["current"]) / float(info["total"]) * 100)
    elif async.successful():
        progress = 100
    context.update(progress=progress)
    return render(request, template, context)



