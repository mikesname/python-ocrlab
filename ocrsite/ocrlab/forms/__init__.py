"""Ocrlab forms."""

from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from ocrlab.models import Preset

# Add to your settings file
CONTENT_TYPES = ['image', 'video']
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = "20971520"


class SimpleOcrForm(forms.Form):
    file = forms.FileField()
    async = forms.BooleanField(required=False)
    preset = forms.ModelChoiceField(queryset=Preset.objects.all())

    def clean_file(self):    
        content = self.cleaned_data['file']
        content_type = content.content_type.split('/')[0]
        if content_type in CONTENT_TYPES:
            if content._size > MAX_UPLOAD_SIZE:
                raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (
                        filesizeformat(MAX_UPLOAD_SIZE), 
                            filesizeformat(content._size)))
        else:
            raise forms.ValidationError(_('File type is not supported'))
        return content


class PresetForm(forms.ModelForm):
    class Meta:
        model = Preset
