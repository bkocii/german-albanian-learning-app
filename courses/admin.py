from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.urls import path

from .import_views import course_import
from .media_import_views import media_import
from .models import (
    CEFRLevel,
    Exercise,
    ExerciseAcceptedAnswer,
    ExerciseOption,
    Lesson,
    MatchingPair,
    MediaAsset,
    Unit,
    VocabularyEntry,
)
from .publication import publish_units, unpublish_units


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class VocabularyInline(admin.TabularInline):
    model = VocabularyEntry
    extra = 0


class ExerciseOptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors) or self.instance.review_status == Exercise.ReviewStatus.DRAFT:
            return
        choice_types = {
            Exercise.Type.PICTURE_CHOICE,
            Exercise.Type.TRANSLATION_CHOICE,
            Exercise.Type.TRUE_FALSE,
            Exercise.Type.DIALOGUE_CHOICE,
            Exercise.Type.MULTIPLE_SELECT,
        }
        if self.instance.exercise_type not in choice_types:
            return
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(active_forms) < 2:
            raise ValidationError("Published choice exercises require at least two options.")
        correct_count = sum(bool(form.cleaned_data.get("is_correct")) for form in active_forms)
        if self.instance.exercise_type == Exercise.Type.MULTIPLE_SELECT:
            if len(active_forms) < 3:
                raise ValidationError(
                    "Reviewed multiple-select exercises require at least three options."
                )
            if correct_count < 2:
                raise ValidationError(
                    "Reviewed multiple-select exercises require at least two correct options."
                )
            if correct_count == len(active_forms):
                raise ValidationError(
                    "Reviewed multiple-select exercises require at least one incorrect option."
                )
        elif correct_count != 1:
            raise ValidationError("Published choice exercises require exactly one correct option.")


class ExerciseOptionInline(admin.TabularInline):
    model = ExerciseOption
    formset = ExerciseOptionInlineFormSet
    extra = 0


class ExerciseAcceptedAnswerInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors) or self.instance.review_status == Exercise.ReviewStatus.DRAFT:
            return
        if self.instance.exercise_type != Exercise.Type.FREE_TEXT:
            return
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if not active_forms:
            raise ValidationError(
                "Reviewed free-text exercises require at least one accepted answer."
            )


class ExerciseAcceptedAnswerInline(admin.TabularInline):
    model = ExerciseAcceptedAnswer
    formset = ExerciseAcceptedAnswerInlineFormSet
    extra = 0


class MatchingPairInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors) or self.instance.review_status == Exercise.ReviewStatus.DRAFT:
            return
        if self.instance.exercise_type != Exercise.Type.MATCHING:
            return
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(active_forms) < 2:
            raise ValidationError(
                "Reviewed matching exercises require at least two matching pairs."
            )


class MatchingPairInline(admin.TabularInline):
    model = MatchingPair
    formset = MatchingPairInlineFormSet
    extra = 0


@admin.register(CEFRLevel)
class CEFRLevelAdmin(admin.ModelAdmin):
    list_display = ("code", "title_sq", "position", "is_published")
    list_editable = ("position", "is_published")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title_sq", "level", "position", "is_published")
    list_filter = ("level", "is_published")
    prepopulated_fields = {"slug": ("title_de",)}
    inlines = (LessonInline,)
    actions = ("publish_complete_units", "unpublish_complete_units")

    @admin.action(description="Publish selected units with all lessons and exercises")
    def publish_complete_units(self, request, queryset):
        try:
            unit_count, exercise_count = publish_units(queryset, request.user)
        except ValidationError as error:
            self.message_user(
                request,
                "Publication stopped. " + " ".join(error.messages),
                level=messages.ERROR,
            )
            return
        self.message_user(
            request,
            f"Published {unit_count} unit(s) and {exercise_count} exercise(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Unpublish selected units and keep exercises reviewed")
    def unpublish_complete_units(self, request, queryset):
        unit_count, exercise_count = unpublish_units(queryset)
        self.message_user(
            request,
            f"Unpublished {unit_count} unit(s); {exercise_count} exercise(s) remain reviewed.",
            level=messages.SUCCESS,
        )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title_sq", "unit", "position", "is_published")
    list_filter = ("unit__level", "unit", "is_published")
    prepopulated_fields = {"slug": ("title_de",)}
    inlines = (VocabularyInline,)


@admin.register(VocabularyEntry)
class VocabularyEntryAdmin(admin.ModelAdmin):
    list_display = ("german", "albanian", "lesson", "position")
    list_filter = ("lesson__unit__level", "lesson__unit", "lesson")
    search_fields = ("german", "albanian")


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    change_list_template = "admin/courses/mediaasset/change_list.html"
    list_display = (
        "external_id",
        "title",
        "kind",
        "language_code",
        "creator",
        "license_name",
        "is_approved",
        "approved_by",
    )
    list_filter = ("kind", "language_code", "is_approved", "license_name")
    search_fields = ("external_id", "title", "creator", "attribution_text")
    autocomplete_fields = ("approved_by",)

    def get_urls(self):
        custom_urls = [
            path(
                "import-zip/",
                self.admin_site.admin_view(media_import),
                name="courses_mediaasset_import_zip",
            )
        ]
        return custom_urls + super().get_urls()


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    change_list_template = "admin/courses/exercise/change_list.html"
    list_display = (
        "external_id",
        "lesson",
        "position",
        "exercise_type",
        "review_status",
        "reviewed_by",
    )
    list_filter = ("review_status", "exercise_type", "lesson__unit__level")
    search_fields = ("external_id", "prompt_de", "prompt_sq", "expected_answer")
    autocomplete_fields = ("image", "audio", "reviewed_by")
    inlines = (ExerciseOptionInline, ExerciseAcceptedAnswerInline, MatchingPairInline)

    def get_urls(self):
        custom_urls = [
            path(
                "import-json/",
                self.admin_site.admin_view(course_import),
                name="courses_exercise_import_json",
            )
        ]
        return custom_urls + super().get_urls()


@admin.register(ExerciseOption)
class ExerciseOptionAdmin(admin.ModelAdmin):
    list_display = ("exercise", "position", "text_de", "text_sq", "is_correct")
    list_filter = ("is_correct", "exercise__exercise_type")


@admin.register(ExerciseAcceptedAnswer)
class ExerciseAcceptedAnswerAdmin(admin.ModelAdmin):
    list_display = ("exercise", "position", "text")
    search_fields = ("text", "exercise__external_id")


@admin.register(MatchingPair)
class MatchingPairAdmin(admin.ModelAdmin):
    list_display = ("exercise", "position", "left_text", "right_text")
    search_fields = ("left_text", "right_text", "exercise__external_id")
