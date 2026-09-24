from django.contrib import admin

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


class ExerciseOptionInline(admin.TabularInline):
    model = ExerciseOption
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
