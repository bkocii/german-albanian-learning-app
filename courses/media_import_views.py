import secrets
import time
from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import MediaImportConfirmForm, MediaImportUploadForm
from .media_importer import MediaImportError, import_media_archive, validate_media_archive


def _cache_key(token):
    return f"media-import-preview:{token}"


def _preview_path(token):
    return Path(settings.MEDIA_IMPORT_PREVIEW_ROOT) / f"{token}.zip"


def _cleanup_expired_previews():
    root = Path(settings.MEDIA_IMPORT_PREVIEW_ROOT)
    if not root.exists():
        return
    cutoff = time.time() - settings.MEDIA_IMPORT_PREVIEW_SECONDS
    for path in root.glob("*.zip"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
        except OSError:
            continue


def _save_preview(upload, token):
    root = Path(settings.MEDIA_IMPORT_PREVIEW_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    path = _preview_path(token)
    with path.open("wb") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)
    return path


@staff_member_required
@require_http_methods(["GET", "POST"])
def media_import(request):
    _cleanup_expired_previews()
    validation = None
    confirm_form = None
    upload_form = MediaImportUploadForm()

    if request.method == "POST" and request.POST.get("action") == "import":
        confirm_form = MediaImportConfirmForm(request.POST)
        if confirm_form.is_valid():
            token = confirm_form.cleaned_data["preview_token"]
            cached = cache.get(_cache_key(token))
            path = _preview_path(token)
            if not cached or cached.get("user_id") != request.user.pk or not path.exists():
                messages.error(request, "The preview expired. Upload and validate the ZIP again.")
                return redirect("admin:courses_mediaasset_import_zip")
            cache.delete(_cache_key(token))
            try:
                summary = import_media_archive(path)
            except MediaImportError as error:
                validation = validate_media_archive(path)
                validation.errors = error.errors
            else:
                messages.success(
                    request,
                    f"Imported {summary['assets']} unapproved media asset(s) successfully.",
                )
                return redirect("admin:courses_mediaasset_changelist")
            finally:
                path.unlink(missing_ok=True)
    elif request.method == "POST":
        upload_form = MediaImportUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            token = secrets.token_urlsafe(24)
            path = _save_preview(upload_form.cleaned_data["media_archive"], token)
            validation = validate_media_archive(path)
            if validation.is_valid:
                cache.set(
                    _cache_key(token),
                    {"user_id": request.user.pk},
                    timeout=settings.MEDIA_IMPORT_PREVIEW_SECONDS,
                )
                confirm_form = MediaImportConfirmForm(initial={"preview_token": token})
            else:
                path.unlink(missing_ok=True)

    context = {
        **admin.site.each_context(request),
        "title": "Import media ZIP",
        "upload_form": upload_form,
        "validation": validation,
        "confirm_form": confirm_form,
        "media_list_url": reverse("admin:courses_mediaasset_changelist"),
    }
    return render(request, "admin/courses/media_import.html", context)
