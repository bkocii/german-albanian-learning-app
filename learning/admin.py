from django.contrib import admin

from .models import ExerciseAttempt, LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("learner", "lesson", "started_at", "last_activity_at", "completed_at")
    list_filter = ("lesson__unit__level", "completed_at")
    search_fields = ("learner__email", "lesson__title_de", "lesson__title_sq")
    readonly_fields = ("started_at", "last_activity_at")


@admin.register(ExerciseAttempt)
class ExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ("learner", "exercise", "is_correct", "created_at")
    list_filter = ("is_correct", "exercise__exercise_type", "exercise__lesson__unit__level")
    search_fields = ("learner__email", "answer_text")
    readonly_fields = (
        "learner",
        "exercise",
        "selected_option",
        "answer_text",
        "is_correct",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
