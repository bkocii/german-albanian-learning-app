from django.contrib import admin

from .models import TutorDailyUsage, TutorExchange


@admin.register(TutorExchange)
class TutorExchangeAdmin(admin.ModelAdmin):
    list_display = (
        "learner",
        "exercise",
        "kind",
        "feedback_rating",
        "within_lesson_scope",
        "model_name",
        "created_at",
    )
    list_filter = (
        "feedback_rating",
        "kind",
        "within_lesson_scope",
        "model_name",
        "created_at",
    )
    search_fields = ("learner__email", "question", "explanation_sq", "request_id")
    readonly_fields = tuple(field.name for field in TutorExchange._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TutorDailyUsage)
class TutorDailyUsageAdmin(admin.ModelAdmin):
    list_display = ("date", "request_count", "updated_at")
    readonly_fields = ("date", "request_count", "updated_at")
    date_hierarchy = "date"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
