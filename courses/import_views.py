import secrets

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import CourseImportConfirmForm, CourseImportUploadForm
from .importer import CourseImportError, import_course_data, validate_course_import

SUMMARY_LABELS = {
    "tutor_lessons": "Tutor lesson contexts",
    "tutor_examples": "Tutor examples",
    "accepted_answers": "Accepted answers",
    "matching_pairs": "Matching pairs",
}


def _cache_key(token):
    return f"course-import-preview:{token}"


@staff_member_required
@require_http_methods(["GET", "POST"])
def course_import(request):
    validation = None
    confirm_form = None
    upload_form = CourseImportUploadForm()

    if request.method == "POST" and request.POST.get("action") == "import":
        confirm_form = CourseImportConfirmForm(request.POST)
        if confirm_form.is_valid():
            token = confirm_form.cleaned_data["preview_token"]
            cached = cache.get(_cache_key(token))
            if not cached or cached.get("user_id") != request.user.pk:
                messages.error(request, "The preview expired. Upload and validate the file again.")
                return redirect("admin:courses_exercise_import_json")
            cache.delete(_cache_key(token))
            try:
                summary = import_course_data(cached["data"])
            except CourseImportError as error:
                validation = validate_course_import(cached["data"])
                validation.errors = error.errors
            else:
                if summary["tutor_examples"] and not summary["exercises"]:
                    success_message = (
                        f"Updated {summary['tutor_lessons']} lesson tutor context(s) and "
                        f"imported {summary['tutor_examples']} unapproved tutor example(s)."
                    )
                else:
                    success_message = (
                        f"Imported {summary['exercises']} draft exercises successfully."
                    )
                messages.success(
                    request,
                    success_message,
                )
                return redirect("admin:courses_exercise_changelist")
    elif request.method == "POST":
        upload_form = CourseImportUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            data = upload_form.cleaned_data["course_data"]
            validation = validate_course_import(data)
            if validation.is_valid:
                token = secrets.token_urlsafe(24)
                cache.set(
                    _cache_key(token),
                    {"user_id": request.user.pk, "data": data},
                    timeout=settings.COURSE_IMPORT_PREVIEW_SECONDS,
                )
                confirm_form = CourseImportConfirmForm(initial={"preview_token": token})

    context = {
        **admin.site.each_context(request),
        "title": "Import course JSON",
        "upload_form": upload_form,
        "validation": validation,
        "summary_rows": (
            [
                (SUMMARY_LABELS.get(label, label.replace("_", " ").title()), count)
                for label, count in validation.summary.items()
            ]
            if validation
            else []
        ),
        "confirm_form": confirm_form,
        "exercise_list_url": reverse("admin:courses_exercise_changelist"),
    }
    return render(request, "admin/courses/course_import.html", context)
