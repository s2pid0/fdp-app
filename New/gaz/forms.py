from django import forms
from .models import *
from django.forms.widgets import ClearableFileInput, CheckboxInput


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class UploadFileForm(forms.Form):
    file_field1 = forms.FileField(widget=ClearableFileInput(attrs={"class": "ff1", "onchange": "pressed_ff1()"}))
    file_field2 = forms.FileField(widget=ClearableFileInput(attrs={"class": "ff2", "onchange": "pressed_ff2()"}))


class EditResultForm(forms.Form):
    variance_reason = forms.ChoiceField(label='', choices=Result.WHY, widget=forms.Select(attrs={"class": "efc1"}))
    actions = forms.ChoiceField(label='', choices=Result.ACTIONS, widget=forms.Select(attrs={"class": "efc2"}))
    postscriptum = forms.CharField(label='', widget=forms.Textarea(attrs={"class": "efc3"}))