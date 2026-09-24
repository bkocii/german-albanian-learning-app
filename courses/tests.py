import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import CEFRLevel, Exercise, ExerciseOption, Lesson, MediaAsset, Unit


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class CourseModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.level = CEFRLevel.objects.create(
            code="A1", title_de="Anfänger", title_sq="Fillestar", position=1
        )
        cls.unit = Unit.objects.create(
            level=cls.level,
            slug="begrussung",
            title_de="Begrüßung",
            title_sq="Përshëndetjet",
            position=1,
        )
        cls.lesson = Lesson.objects.create(
            unit=cls.unit,
            slug="hallo",
            title_de="Hallo!",
            title_sq="Përshëndetje!",
            position=1,
        )

    def create_asset(self, kind):
        return MediaAsset.objects.create(
            title=f"Test {kind}",
            kind=kind,
            file=SimpleUploadedFile(f"test.{kind}", b"test"),
            creator="Course team",
            license_name="Original work",
            acquired_on=date.today(),
        )

    def test_course_structure_orders_content(self):
        second = Lesson.objects.create(
            unit=self.unit,
            slug="name",
            title_de="Name",
            title_sq="Emri",
            position=2,
        )
        self.assertEqual(list(self.unit.lessons.all()), [self.lesson, second])

    def test_lesson_position_must_be_unique_within_unit(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lesson.objects.create(
                unit=self.unit,
                slug="duplicate",
                title_de="Noch einmal",
                title_sq="Përsëri",
                position=1,
            )

    def test_exercise_rejects_wrong_asset_kind(self):
        audio = self.create_asset(MediaAsset.Kind.AUDIO)
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.PICTURE_CHOICE,
            instructions_sq="Zgjidh figurën.",
            image=audio,
        )
        with self.assertRaisesMessage(ValidationError, "must be an image"):
            exercise.full_clean()

    def test_reviewed_exercise_requires_reviewer_and_time(self):
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.MISSING_WORD,
            instructions_sq="Plotëso fjalën.",
            review_status=Exercise.ReviewStatus.REVIEWED,
        )
        with self.assertRaisesMessage(ValidationError, "need a reviewer and time"):
            exercise.full_clean()

    def test_reviewed_exercise_accepts_complete_review_metadata(self):
        reviewer = get_user_model().objects.create_user(
            email="reviewer@example.com", password="secure-test-password"
        )
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.MISSING_WORD,
            instructions_sq="Plotëso fjalën.",
            expected_answer="Hallo",
            review_status=Exercise.ReviewStatus.REVIEWED,
            reviewed_by=reviewer,
            reviewed_at=timezone.now(),
        )
        exercise.full_clean()
        exercise.save()
        self.assertEqual(exercise.reviewed_by, reviewer)

    def test_option_requires_text_or_image(self):
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type=Exercise.Type.TRANSLATION_CHOICE,
            instructions_sq="Zgjidh përkthimin.",
        )
        option = ExerciseOption(exercise=exercise, position=1)
        with self.assertRaises(ValidationError):
            option.full_clean()

    def test_published_word_order_requires_expected_answer(self):
        reviewer = get_user_model().objects.create_user(
            email="word-reviewer@example.com", password="secure-test-password"
        )
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.WORD_ORDER,
            instructions_sq="Vendosi fjalët në radhë.",
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=reviewer,
            reviewed_at=timezone.now(),
        )
        with self.assertRaisesMessage(ValidationError, "requires an expected answer"):
            exercise.full_clean()

    def test_picture_option_requires_image(self):
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type=Exercise.Type.PICTURE_CHOICE,
            instructions_sq="Zgjidh figurën.",
        )
        option = ExerciseOption(exercise=exercise, text_de="Hallo", position=1)
        with self.assertRaisesMessage(ValidationError, "require an image"):
            option.full_clean()
