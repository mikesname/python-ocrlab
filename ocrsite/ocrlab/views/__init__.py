
from .presets import *

from django.shortcuts import render, redirect

from ocrlab import forms

def home(request):
    """Simple home view."""
    template = "home.html"
    form = forms.SimpleOcrForm
    context = dict(form=form)
    return render(request, template, context)
