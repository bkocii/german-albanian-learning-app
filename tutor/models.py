from django.conf import settings
from django.db import models

from courses.models import Exercise
from learning.models import ExerciseAttempt


class TutorExchange(models.Model):
    class Kind(models.TextChoices):
        EXPLAIN_MISTAKE = "explain_mistake", "Explain the mistake"
        EXPLAIN_ANSWER = "explain_answer", "Explain the answer"
        GRAMMAR = "grammar", "Explain the grammar"
        EXAMPLE = "example", "Give another example"
        CUSTOM = "custom", "Custom lesson question"

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_exchanges",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="tutor_exchanges",
    )
    attempt = models.ForeignKey(
        ExerciseAttempt,
        on_delete=models.CASCADE,
        related_name="tutor_exchanges",
    )
    kind = models.CharField(max_length=30, choices=Kind)
    question = models.TextField(blank=True)
    explanation_sq = models.TextField()
    german_examples = models.JSONField(default=list, blank=True)
    follow_up_sq = models.TextField(blank=True)
    within_lesson_scope = models.BooleanField(default=True)
    model_name = models.CharField(max_length=100)
    request_id = models.CharField(max_length=100, blank=True)
    duration_ms = models.FloatField(blank=True, null=True)
    input_tokens = models.PositiveIntegerField(blank=True, null=True)
    output_tokens = models.PositiveIntegerField(blank=True, null=True)
    estimated_cost_usd = models.DecimalField(
        max_digits=12, decimal_places=8, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("learner", "created_at"))]

    def __str__(self):
        return f"{self.learner} — {self.exercise_id} — {self.kind}"
