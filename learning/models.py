from django.conf import settings
from django.db import models
from django.db.models import Q

from courses.models import Exercise, ExerciseOption, Lesson


class LessonProgress(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="learner_progress")
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-last_activity_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("learner", "lesson"), name="unique_lesson_progress_per_learner"
            )
        ]

    @property
    def is_completed(self):
        return self.completed_at is not None

    def __str__(self):
        return f"{self.learner} — {self.lesson}"


class ExerciseAttempt(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercise_attempts"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    selected_option = models.ForeignKey(
        ExerciseOption,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="attempts",
    )
    answer_text = models.TextField(blank=True)
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(selected_option__isnull=False) | Q(answer_text__gt=""),
                name="exercise_attempt_has_answer",
            )
        ]

    def __str__(self):
        return f"{self.learner} — {self.exercise} — {self.is_correct}"
