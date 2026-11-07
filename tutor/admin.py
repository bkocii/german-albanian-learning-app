from django.contrib import admin

from .models import TutorExchange


@admin.register(TutorExchange)
class TutorExchangeAdmin(admin.ModelAdmin):
    list_display = (
        "learner",
        "exercise",
        "kind",
        "within_lesson_scope",
        "model_name",
        "created_at",
    )
    list_filter = ("kind", "within_lesson_scope", "model_name", "created_at")
    search_fields = ("learner__email", "question", "explanation_sq", "request_id")
    readonly_fields = tuple(field.name for field in TutorExchange._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
