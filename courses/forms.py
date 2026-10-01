import json

from django import forms
from django.conf import settings


class CourseImportUploadForm(forms.Form):
    course_file = forms.FileField(label="Course JSON file")

    def clean_course_file(self):
        upload = self.cleaned_data["course_file"]
        if upload.size > settings.COURSE_IMPORT_MAX_BYTES:
            raise forms.ValidationError("The JSON file is larger than the allowed import limit.")
        try:
            data = json.loads(upload.read().decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise forms.ValidationError("Upload a valid UTF-8 JSON file.") from error
        self.cleaned_data["course_data"] = data
        return upload


class CourseImportConfirmForm(forms.Form):
    preview_token = forms.CharField(widget=forms.HiddenInput)


class MediaImportUploadForm(forms.Form):
    media_archive = forms.FileField(label="Media ZIP archive")

    def clean_media_archive(self):
        upload = self.cleaned_data["media_archive"]
        if upload.size > settings.MEDIA_IMPORT_MAX_ARCHIVE_BYTES:
            raise forms.ValidationError("The ZIP archive is larger than the allowed import limit.")
        if not upload.name.lower().endswith(".zip"):
            raise forms.ValidationError("Upload a .zip media archive.")
        return upload


class MediaImportConfirmForm(forms.Form):
    preview_token = forms.CharField(widget=forms.HiddenInput)
