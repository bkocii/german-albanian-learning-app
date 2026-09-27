import json
from copy import deepcopy
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .importer import import_course_data, validate_course_import
from .models import CEFRLevel, Exercise, ExerciseAcceptedAnswer, MatchingPair

EXAMPLE_PATH = (
    Path(__file__).resolve().parent.parent
    / "course_content"
    / "examples"
    / "a1-unit-import-example.json"
)


def example_data():
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


class CourseImporterServiceTests(TestCase):
    def test_example_file_validates_without_writing(self):
        result = validate_course_import(example_data())
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.summary["exercises"], 3)
        self.assertEqual(result.summary["accepted_answers"], 2)
        self.assertEqual(result.summary["matching_pairs"], 2)
        self.assertFalse(CEFRLevel.objects.exists())

    def test_import_creates_draft_nested_content(self):
        summary = import_course_data(example_data())
        self.assertEqual(summary["exercises"], 3)
        self.assertEqual(Exercise.objects.count(), 3)
        self.assertFalse(Exercise.objects.exclude(review_status=Exercise.ReviewStatus.DRAFT).exists())
        self.assertEqual(ExerciseAcceptedAnswer.objects.count(), 2)
        self.assertEqual(MatchingPair.objects.count(), 2)

    def test_duplicate_external_id_is_reported_before_import(self):
        data = example_data()
        duplicate = deepcopy(data["units"][0]["lessons"][0]["exercises"][0])
        duplicate["position"] = 4
        data["units"][0]["lessons"][0]["exercises"].append(duplicate)
        result = validate_course_import(data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("duplicate exercise external_id" in error for error in result.errors))


class CourseImporterAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            email="course-admin@example.com", password="secure-test-password"
        )
        cls.learner = get_user_model().objects.create_user(
            email="course-learner@example.com", password="secure-test-password"
        )

    def setUp(self):
        cache.clear()

    def upload(self, data=None):
        payload = json.dumps(data or example_data(), ensure_ascii=False).encode("utf-8")
        upload = SimpleUploadedFile("course.json", payload, content_type="application/json")
        return self.client.post(
            reverse("admin:courses_exercise_import_json"),
            {"action": "preview", "course_file": upload},
        )

    def test_import_page_requires_staff(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("admin:courses_exercise_import_json"))
        self.assertEqual(response.status_code, 302)

    def test_preview_writes_nothing_and_confirm_imports_drafts(self):
        self.client.force_login(self.staff)
        preview = self.upload()
        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, "The file is valid")
        self.assertFalse(Exercise.objects.exists())
        token = preview.context["confirm_form"].initial["preview_token"]

        confirm = self.client.post(
            reverse("admin:courses_exercise_import_json"),
            {"action": "import", "preview_token": token},
            follow=True,
        )
        self.assertContains(confirm, "Imported 3 draft exercises successfully")
        self.assertEqual(Exercise.objects.count(), 3)
        self.assertFalse(Exercise.objects.exclude(review_status=Exercise.ReviewStatus.DRAFT).exists())

    def test_invalid_json_shows_form_error(self):
        self.client.force_login(self.staff)
        upload = SimpleUploadedFile("broken.json", b"{broken", content_type="application/json")
        response = self.client.post(
            reverse("admin:courses_exercise_import_json"),
            {"action": "preview", "course_file": upload},
        )
        self.assertContains(response, "Upload a valid UTF-8 JSON file")
