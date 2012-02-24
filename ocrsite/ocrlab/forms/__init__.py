"""Ocrlab forms."""

from django import forms

from ocrlab.models import Preset

class SimpleOcrForm(forms.Form):
    file = forms.FileField()
    preset = forms.ModelChoiceField(queryset=Preset.objects.all())

class PresetForm(forms.ModelForm):
    class Meta:
        model = Preset
