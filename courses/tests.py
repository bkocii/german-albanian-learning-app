import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import (
    CEFRLevel,
    Exercise,
    ExerciseAcceptedAnswer,
    ExerciseOption,
    Lesson,
    MatchingPair,
    MediaAsset,
    Unit,
)


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

    def create_asset(self, kind, **overrides):
        values = {
            "title": f"Test {kind}",
            "kind": kind,
            "file": SimpleUploadedFile(f"test.{kind}", b"test"),
            "creator": "Course team",
            "license_name": "Original work",
            "acquired_on": date.today(),
        }
        values.update(overrides)
        return MediaAsset.objects.create(
            **values,
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

    def test_approved_audio_requires_approval_metadata(self):
        asset = MediaAsset(
            title="German greeting",
            kind=MediaAsset.Kind.AUDIO,
            language_code=MediaAsset.Language.GERMAN,
            file=SimpleUploadedFile("hallo.mp3", b"test"),
            creator="Course team",
            license_name="Original work",
            acquired_on=date.today(),
            is_approved=True,
        )
        with self.assertRaisesMessage(ValidationError, "require an approver"):
            asset.full_clean()

    def test_published_listening_requires_approved_german_audio(self):
        reviewer = get_user_model().objects.create_user(
            email="audio-reviewer@example.com", password="secure-test-password"
        )
        audio = self.create_asset(
            MediaAsset.Kind.AUDIO,
            language_code=MediaAsset.Language.GERMAN,
        )
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.LISTENING,
            instructions_sq="Dëgjo dhe shkruaj.",
            expected_answer="Guten Morgen",
            audio=audio,
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=reviewer,
            reviewed_at=timezone.now(),
        )
        with self.assertRaisesMessage(ValidationError, "must be approved"):
            exercise.full_clean()

    def test_published_speaking_requires_expected_answer(self):
        reviewer = get_user_model().objects.create_user(
            email="speech-content-reviewer@example.com", password="secure-test-password"
        )
        exercise = Exercise(
            lesson=self.lesson,
            exercise_type=Exercise.Type.SPEAKING,
            instructions_sq="Thuaj fjalinë.",
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=reviewer,
            reviewed_at=timezone.now(),
        )
        with self.assertRaisesMessage(ValidationError, "requires an expected answer"):
            exercise.full_clean()

    def test_future_exercise_type_can_be_drafted_but_not_published(self):
        exercise = Exercise(
            lesson=self.lesson,
            external_id="greeting-dialogue-1",
            exercise_type=Exercise.Type.DIALOGUE_CHOICE,
            instructions_sq="Zgjidh përgjigjen.",
        )
        exercise.full_clean()

        reviewer = get_user_model().objects.create_user(
            email="future-reviewer@example.com", password="secure-test-password"
        )
        exercise.review_status = Exercise.ReviewStatus.PUBLISHED
        exercise.reviewed_by = reviewer
        exercise.reviewed_at = timezone.now()
        with self.assertRaisesMessage(ValidationError, "must remain a draft"):
            exercise.full_clean()

    def test_external_exercise_id_must_be_unique_inside_lesson(self):
        Exercise.objects.create(
            lesson=self.lesson,
            external_id="hello-choice-1",
            exercise_type=Exercise.Type.TRANSLATION_CHOICE,
            instructions_sq="Zgjidh.",
            position=1,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exercise.objects.create(
                lesson=self.lesson,
                external_id="hello-choice-1",
                exercise_type=Exercise.Type.MISSING_WORD,
                instructions_sq="Plotëso.",
                position=2,
            )

    def test_accepted_answers_and_matching_pairs_are_ordered(self):
        free_text = Exercise.objects.create(
            lesson=self.lesson,
            external_id="free-text-1",
            exercise_type=Exercise.Type.FREE_TEXT,
            instructions_sq="Përkthe.",
            position=1,
        )
        second_answer = ExerciseAcceptedAnswer.objects.create(
            exercise=free_text, text="Guten Tag!", position=2
        )
        first_answer = ExerciseAcceptedAnswer.objects.create(
            exercise=free_text, text="Guten Tag", position=1
        )
        self.assertEqual(list(free_text.accepted_answers.all()), [first_answer, second_answer])

        matching = Exercise.objects.create(
            lesson=self.lesson,
            external_id="matching-1",
            exercise_type=Exercise.Type.MATCHING,
            instructions_sq="Bashko çiftet.",
            position=2,
        )
        pair = MatchingPair.objects.create(
            exercise=matching,
            left_text="Hallo",
            right_text="Përshëndetje",
            position=1,
        )
        self.assertEqual(list(matching.matching_pairs.all()), [pair])
