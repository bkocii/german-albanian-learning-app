from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class OrderedModel(models.Model):
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        abstract = True


class CEFRLevel(models.Model):
    class Code(models.TextChoices):
        A1 = "A1", "A1"
        A2 = "A2", "A2"
        B1 = "B1", "B1"
        B2 = "B2", "B2"

    code = models.CharField(max_length=2, choices=Code, unique=True)
    title_de = models.CharField(max_length=100)
    title_sq = models.CharField(max_length=100)
    description_sq = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=1, unique=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("position",)

    def __str__(self):
        return f"{self.code} — {self.title_sq}"


class Unit(OrderedModel):
    level = models.ForeignKey(CEFRLevel, on_delete=models.PROTECT, related_name="units")
    slug = models.SlugField(max_length=100)
    title_de = models.CharField(max_length=150)
    title_sq = models.CharField(max_length=150)
    summary_sq = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("level__position", "position")
        constraints = [
            models.UniqueConstraint(fields=("level", "slug"), name="unique_unit_slug_per_level"),
            models.UniqueConstraint(
                fields=("level", "position"), name="unique_unit_position_per_level"
            ),
        ]

    def __str__(self):
        return f"{self.level.code}.{self.position} — {self.title_sq}"


class Lesson(OrderedModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    slug = models.SlugField(max_length=100)
    title_de = models.CharField(max_length=150)
    title_sq = models.CharField(max_length=150)
    objective_sq = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("unit__level__position", "unit__position", "position")
        constraints = [
            models.UniqueConstraint(fields=("unit", "slug"), name="unique_lesson_slug_per_unit"),
            models.UniqueConstraint(
                fields=("unit", "position"), name="unique_lesson_position_per_unit"
            ),
        ]

    def __str__(self):
        return f"{self.unit}.{self.position} — {self.title_sq}"


class VocabularyEntry(OrderedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="vocabulary")
    german = models.CharField(max_length=200)
    albanian = models.CharField(max_length=200)
    part_of_speech = models.CharField(max_length=50, blank=True)
    example_de = models.TextField(blank=True)
    example_sq = models.TextField(blank=True)
    notes_sq = models.TextField(blank=True)

    class Meta:
        ordering = ("lesson", "position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "german", "albanian"), name="unique_vocabulary_pair_per_lesson"
            )
        ]

    def __str__(self):
        return f"{self.german} — {self.albanian}"


class MediaAsset(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"

    title = models.CharField(max_length=150)
    kind = models.CharField(max_length=10, choices=Kind)
    file = models.FileField(upload_to="course-assets/%Y/%m/")
    alt_text_sq = models.CharField(max_length=250, blank=True)
    creator = models.CharField(max_length=150)
    source_url = models.URLField(blank=True)
    license_name = models.CharField(max_length=100)
    license_url = models.URLField(blank=True)
    attribution_text = models.TextField(blank=True)
    acquired_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class Exercise(OrderedModel):
    class Type(models.TextChoices):
        PICTURE_CHOICE = "picture_choice", "Picture selection"
        TRANSLATION_CHOICE = "translation_choice", "Translation choice"
        MISSING_WORD = "missing_word", "Missing word"
        WORD_ORDER = "word_order", "Word ordering"
        LISTENING = "listening", "Listening"
        SPEAKING = "speaking", "Speaking"

    class ReviewStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEWED = "reviewed", "Reviewed"
        PUBLISHED = "published", "Published"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercises")
    exercise_type = models.CharField(max_length=30, choices=Type)
    instructions_sq = models.CharField(max_length=250)
    prompt_de = models.TextField(blank=True)
    prompt_sq = models.TextField(blank=True)
    expected_answer = models.TextField(blank=True)
    image = models.ForeignKey(
        MediaAsset,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="image_exercises",
    )
    audio = models.ForeignKey(
        MediaAsset,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="audio_exercises",
    )
    review_status = models.CharField(
        max_length=10, choices=ReviewStatus, default=ReviewStatus.DRAFT
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="reviewed_exercises",
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("lesson", "position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "position"), name="unique_exercise_position_per_lesson"
            ),
            models.CheckConstraint(
                condition=(
                    Q(review_status="draft", reviewed_by__isnull=True, reviewed_at__isnull=True)
                    | Q(
                        review_status__in=("reviewed", "published"),
                        reviewed_by__isnull=False,
                        reviewed_at__isnull=False,
                    )
                ),
                name="exercise_review_state_is_complete",
            ),
        ]

    def clean(self):
        errors = {}
        if self.image and self.image.kind != MediaAsset.Kind.IMAGE:
            errors["image"] = "The selected asset must be an image."
        if self.audio and self.audio.kind != MediaAsset.Kind.AUDIO:
            errors["audio"] = "The selected asset must be audio."
        if self.review_status == self.ReviewStatus.DRAFT:
            if self.reviewed_by_id or self.reviewed_at:
                errors["review_status"] = "A draft cannot contain review details."
        elif not self.reviewed_by_id or not self.reviewed_at:
            errors["review_status"] = "Reviewed and published exercises need a reviewer and time."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.lesson} / {self.position}: {self.get_exercise_type_display()}"


class ExerciseOption(OrderedModel):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="options")
    text_de = models.CharField(max_length=250, blank=True)
    text_sq = models.CharField(max_length=250, blank=True)
    image = models.ForeignKey(
        MediaAsset,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="exercise_options",
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ("exercise", "position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("exercise", "position"), name="unique_option_position_per_exercise"
            ),
            models.CheckConstraint(
                condition=Q(text_de__gt="") | Q(text_sq__gt="") | Q(image__isnull=False),
                name="exercise_option_has_content",
            ),
        ]

    def clean(self):
        if self.image and self.image.kind != MediaAsset.Kind.IMAGE:
            raise ValidationError({"image": "The selected asset must be an image."})

    def __str__(self):
        return self.text_de or self.text_sq or f"Image option {self.position}"
