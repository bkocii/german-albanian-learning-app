from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import (
    CEFRLevel,
    Exercise,
    ExerciseOption,
    Lesson,
    MediaAsset,
    Unit,
    VocabularyEntry,
)


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
        if sum(bool(form.cleaned_data.get("is_correct")) for form in active_forms) != 1:
            raise ValidationError("Published choice exercises require exactly one correct option.")


class ExerciseOptionInline(admin.TabularInline):
    model = ExerciseOption
    formset = ExerciseOptionInlineFormSet
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
    list_display = ("title", "kind", "creator", "license_name", "acquired_on")
    list_filter = ("kind", "license_name")
    search_fields = ("title", "creator", "attribution_text")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("lesson", "position", "exercise_type", "review_status", "reviewed_by")
    list_filter = ("review_status", "exercise_type", "lesson__unit__level")
    search_fields = ("prompt_de", "prompt_sq", "expected_answer")
    autocomplete_fields = ("image", "audio", "reviewed_by")
    inlines = (ExerciseOptionInline,)


@admin.register(ExerciseOption)
class ExerciseOptionAdmin(admin.ModelAdmin):
    list_display = ("exercise", "position", "text_de", "text_sq", "is_correct")
    list_filter = ("is_correct", "exercise__exercise_type")
