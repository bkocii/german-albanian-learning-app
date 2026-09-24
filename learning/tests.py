from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import CEFRLevel, Exercise, ExerciseOption, Lesson, Unit

from .models import ExerciseAttempt, LessonProgress


class LessonPlayerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learner = get_user_model().objects.create_user(
            email="learner@example.com", password="secure-test-password"
        )
        cls.reviewer = get_user_model().objects.create_user(
            email="reviewer@example.com", password="secure-test-password"
        )
        cls.level = CEFRLevel.objects.create(
            code="A1",
            title_de="Anfänger",
            title_sq="Fillestar",
            position=1,
            is_published=True,
        )
        cls.unit = Unit.objects.create(
            level=cls.level,
            slug="begrussung",
            title_de="Begrüßung",
            title_sq="Përshëndetjet",
            position=1,
            is_published=True,
        )
        cls.lesson = Lesson.objects.create(
            unit=cls.unit,
            slug="hallo",
            title_de="Hallo!",
            title_sq="Përshëndetje!",
            position=1,
            is_published=True,
        )
        cls.exercise = Exercise.objects.create(
            lesson=cls.lesson,
            exercise_type=Exercise.Type.TRANSLATION_CHOICE,
            instructions_sq="Zgjidh përkthimin.",
            prompt_de="Hallo",
            position=1,
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=cls.reviewer,
            reviewed_at=timezone.now(),
        )
        cls.correct_option = ExerciseOption.objects.create(
            exercise=cls.exercise,
            text_sq="Përshëndetje",
            position=1,
            is_correct=True,
        )
        cls.wrong_option = ExerciseOption.objects.create(
            exercise=cls.exercise,
            text_sq="Mirupafshim",
            position=2,
        )

    def setUp(self):
        self.client.force_login(self.learner)

    def test_catalog_lists_only_published_course_content(self):
        hidden = CEFRLevel.objects.create(
            code="A2",
            title_de="Grundlegende Kenntnisse",
            title_sq="Njohuri themelore",
            position=2,
        )
        response = self.client.get(reverse("learning:catalog"))
        self.assertContains(response, self.level.title_sq)
        self.assertNotContains(response, hidden.title_sq)

    def test_starting_lesson_creates_progress_and_opens_first_exercise(self):
        response = self.client.get(
            reverse(
                "learning:lesson-start",
                args=(self.level.code, self.unit.slug, self.lesson.slug),
            )
        )
        self.assertRedirects(
            response, reverse("learning:exercise", args=(self.exercise.pk,))
        )
        self.assertTrue(
            LessonProgress.objects.filter(learner=self.learner, lesson=self.lesson).exists()
        )

    def test_correct_answer_is_recorded_and_finishes_lesson(self):
        response = self.client.post(
            reverse("learning:exercise", args=(self.exercise.pk,)),
            {"option": self.correct_option.pk},
        )
        attempt = ExerciseAttempt.objects.get(learner=self.learner)
        self.assertTrue(attempt.is_correct)
        self.assertRedirects(
            response,
            f"{reverse('learning:exercise', args=(self.exercise.pk,))}?attempt={attempt.pk}",
        )
        progress = LessonProgress.objects.get(learner=self.learner, lesson=self.lesson)
        self.assertIsNotNone(progress.completed_at)

    def test_option_from_another_exercise_is_rejected(self):
        other_exercise = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type=Exercise.Type.TRANSLATION_CHOICE,
            instructions_sq="Zgjidh.",
            position=2,
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=self.reviewer,
            reviewed_at=timezone.now(),
        )
        other_option = ExerciseOption.objects.create(
            exercise=other_exercise,
            text_sq="Tjetër",
            position=1,
            is_correct=True,
        )
        response = self.client.post(
            reverse("learning:exercise", args=(self.exercise.pk,)),
            {"option": other_option.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ExerciseAttempt.objects.exists())

    def test_draft_exercise_is_not_available_to_learner(self):
        draft = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type=Exercise.Type.MISSING_WORD,
            instructions_sq="Plotëso.",
            expected_answer="Hallo",
            position=2,
        )
        response = self.client.get(reverse("learning:exercise", args=(draft.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_catalog_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("learning:catalog"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/learn/")
