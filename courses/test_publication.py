import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .importer import import_course_data
from .models import CEFRLevel, Exercise, ExerciseOption, Lesson, Unit
from .publication import publish_units, unpublish_units


class CoursePublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reviewer = get_user_model().objects.create_superuser(
            email="publisher@example.com", password="secure-test-password"
        )

    def create_unit(self, position=1, valid=True):
        level, _ = CEFRLevel.objects.get_or_create(
            code="A1",
            defaults={
                "title_de": "Anfänger",
                "title_sq": "Fillestar",
                "position": 1,
            },
        )
        unit = Unit.objects.create(
            level=level,
            slug=f"unit-{position}",
            title_de=f"Unit {position}",
            title_sq=f"Njësia {position}",
            position=position,
        )
        lesson = Lesson.objects.create(
            unit=unit,
            slug="lesson-1",
            title_de="Lektion 1",
            title_sq="Mësimi 1",
            position=1,
        )
        exercise = Exercise.objects.create(
            lesson=lesson,
            external_id=f"unit-{position}-translation-1",
            exercise_type=Exercise.Type.TRANSLATION_CHOICE,
            instructions_sq="Zgjidh përkthimin.",
            position=1,
        )
        ExerciseOption.objects.create(
            exercise=exercise,
            text_sq="Përshëndetje",
            position=1,
            is_correct=True,
        )
        if valid:
            ExerciseOption.objects.create(
                exercise=exercise,
                text_sq="Mirupafshim",
                position=2,
            )
        return unit, lesson, exercise

    def test_publish_unit_publishes_complete_hierarchy_and_exercises(self):
        unit, lesson, exercise = self.create_unit()

        result = publish_units([unit], self.reviewer)

        self.assertEqual(result, (1, 1))
        unit.refresh_from_db()
        lesson.refresh_from_db()
        exercise.refresh_from_db()
        unit.level.refresh_from_db()
        self.assertTrue(unit.level.is_published)
        self.assertTrue(unit.is_published)
        self.assertTrue(lesson.is_published)
        self.assertEqual(exercise.review_status, Exercise.ReviewStatus.PUBLISHED)
        self.assertEqual(exercise.reviewed_by, self.reviewer)
        self.assertIsNotNone(exercise.reviewed_at)

    def test_unpublish_hides_unit_and_preserves_review_history(self):
        unit, lesson, exercise = self.create_unit()
        publish_units([unit], self.reviewer)

        result = unpublish_units([unit])

        self.assertEqual(result, (1, 1))
        unit.refresh_from_db()
        lesson.refresh_from_db()
        exercise.refresh_from_db()
        unit.level.refresh_from_db()
        self.assertTrue(unit.level.is_published)
        self.assertFalse(unit.is_published)
        self.assertFalse(lesson.is_published)
        self.assertEqual(exercise.review_status, Exercise.ReviewStatus.REVIEWED)
        self.assertEqual(exercise.reviewed_by, self.reviewer)
        self.assertIsNotNone(exercise.reviewed_at)

    def test_invalid_unit_stops_all_selected_units_without_partial_publication(self):
        valid_unit, _, valid_exercise = self.create_unit(position=1)
        invalid_unit, _, invalid_exercise = self.create_unit(position=2, valid=False)

        with self.assertRaisesMessage(ValidationError, "at least two options"):
            publish_units([valid_unit, invalid_unit], self.reviewer)

        valid_unit.refresh_from_db()
        invalid_unit.refresh_from_db()
        valid_exercise.refresh_from_db()
        invalid_exercise.refresh_from_db()
        self.assertFalse(valid_unit.is_published)
        self.assertFalse(invalid_unit.is_published)
        self.assertEqual(valid_exercise.review_status, Exercise.ReviewStatus.DRAFT)
        self.assertEqual(invalid_exercise.review_status, Exercise.ReviewStatus.DRAFT)

    def test_complete_a1_unit_can_be_published_in_one_operation(self):
        content_path = (
            Path(__file__).resolve().parent.parent
            / "course_content"
            / "a1"
            / "unit-01-greetings-introductions.json"
        )
        import_course_data(json.loads(content_path.read_text(encoding="utf-8")))
        unit = Unit.objects.get(slug="pershendetjet-dhe-prezantimi")

        result = publish_units([unit], self.reviewer)

        self.assertEqual(result, (1, 24))
        self.assertEqual(
            Exercise.objects.filter(
                lesson__unit=unit,
                review_status=Exercise.ReviewStatus.PUBLISHED,
            ).count(),
            24,
        )
        self.assertFalse(unit.lessons.filter(is_published=False).exists())
