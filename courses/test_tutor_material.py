import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from learning.models import ExerciseAttempt
from tutor.models import TutorExchange
from tutor.services import TutorResponse, _lesson_context, ask_lesson_tutor, build_tutor_prompt

from .importer import CourseImportError, import_course_data, validate_course_import
from .models import CEFRLevel, Exercise, Lesson, Unit
from .publication import publish_units

CONTENT = Path(__file__).resolve().parent.parent / "course_content" / "tutor-037"


def package(name="greetings-full-v2.json"):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def lesson_data(data):
    return data["units"][0]["lessons"][0]


def import_legacy_demo():
    data = package()
    data["schema_version"] = 1
    lesson = lesson_data(data)
    lesson.pop("tutor_material")
    lesson["vocabulary"] = lesson["vocabulary"][:9]
    lesson["exercises"] = lesson["exercises"][:3]
    for exercise in lesson["exercises"]:
        exercise.pop("tutor_context")
    import_course_data(data)


class StructuredTutorImportTests(TestCase):
    def test_v2_preview_reports_material_and_does_not_write(self):
        result = validate_course_import(package())
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.summary["tutor_materials"], 1)
        self.assertEqual(result.summary["exercise_tutor_contexts"], 10)
        self.assertEqual(result.summary["exercises"], 10)
        self.assertEqual(result.summary["vocabulary"], 10)
        self.assertEqual(result.summary["options"], 16)
        self.assertFalse(CEFRLevel.objects.exists())

    def test_full_import_validates_models_and_requires_explicit_approval(self):
        import_course_data(package())
        lesson = Lesson.objects.get()
        self.assertEqual(len(lesson.tutor_material["concepts"]), 6)
        self.assertEqual(len(lesson.tutor_material["dialogues"]), 3)
        self.assertFalse(lesson.tutor_material_approved)
        self.assertFalse(lesson.is_published)
        for exercise in lesson.exercises.all():
            exercise.full_clean()
            self.assertTrue(exercise.tutor_context)
            self.assertFalse(exercise.tutor_context_approved)
            self.assertEqual(exercise.review_status, Exercise.ReviewStatus.DRAFT)
        lesson.full_clean()

    def test_upgrade_preserves_questions_and_attempts_and_adds_seven_exercises(self):
        import_legacy_demo()
        exercise = Exercise.objects.get(position=1)
        original = {
            field: getattr(exercise, field)
            for field in (
                "pk",
                "prompt_de",
                "prompt_sq",
                "expected_answer",
                "exercise_type",
                "review_status",
                "position",
            )
        }
        user = get_user_model().objects.create_user(email="upgrade@example.com")
        attempt = ExerciseAttempt.objects.create(
            learner=user,
            exercise=exercise,
            selected_option=exercise.options.get(is_correct=True),
            is_correct=True,
        )
        exchange = TutorExchange.objects.create(
            learner=user,
            exercise=exercise,
            attempt=attempt,
            kind="example",
            explanation_sq="Keep this original reply.",
            model_name="test",
        )
        summary = import_course_data(package("greetings-upgrade-existing-demo-v2.json"))
        self.assertEqual(summary["exercises"], 7)
        self.assertEqual(summary["exercise_tutor_contexts"], 10)
        self.assertEqual(Exercise.objects.count(), 10)
        exercise.refresh_from_db()
        for field, value in original.items():
            self.assertEqual(getattr(exercise, field), value)
        self.assertTrue(exercise.tutor_context)
        self.assertFalse(exercise.tutor_context_approved)
        attempt.refresh_from_db()
        self.assertEqual(attempt.exercise_id, exercise.pk)
        exchange.refresh_from_db()
        self.assertEqual(exchange.explanation_sq, "Keep this original reply.")

    def test_invalid_structured_fields_are_rejected_before_writing(self):
        for change in (
            lambda lesson: lesson["tutor_material"].update(unknown_field="ignored?"),
            lambda lesson: lesson["tutor_material"].update(dialogues="wrong type"),
            lambda lesson: lesson["tutor_material"]["concepts"][0].update(
                explanation_sq="x" * 1201
            ),
            lambda lesson: lesson["tutor_material"]["faq"][0].update(key="daily-greetings"),
            lambda lesson: lesson["tutor_material"]["response_examples"][0].update(kind="unknown"),
            lambda lesson: lesson["exercises"][0]["tutor_context"].update(
                material_keys=["missing-key"]
            ),
            lambda lesson: lesson["exercises"][0].update(tutor_notes="unsupported field"),
            lambda lesson: lesson["exercises"][0].update(tutor_context_approved=True),
        ):
            data = package()
            change(lesson_data(data))
            with self.subTest(data=lesson_data(data)["exercises"][0]["external_id"]):
                result = validate_course_import(data)
                self.assertFalse(result.is_valid)
                with self.assertRaises(CourseImportError):
                    import_course_data(data)
                self.assertFalse(CEFRLevel.objects.exists())

    def test_schema_one_rejects_new_material_instead_of_silently_ignoring_it(self):
        data = package()
        data["schema_version"] = 1
        result = validate_course_import(data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("requires schema_version 2" in error for error in result.errors))

    def test_teaching_updates_cannot_change_grading_or_target_missing_exercises(self):
        import_legacy_demo()
        for field, value in (("prompt_de", "Overwrite"), ("external_id", "not-here")):
            data = package("greetings-upgrade-existing-demo-v2.json")
            lesson_data(data)["exercise_tutor_updates"][0][field] = value
            self.assertFalse(validate_course_import(data).is_valid)
        self.assertEqual(Exercise.objects.count(), 3)

    def test_runtime_import_failure_rolls_back_material_and_exercises(self):
        with patch("courses.importer.Exercise.full_clean", side_effect=ValidationError("Failed")):
            with self.assertRaises(ValidationError):
                import_course_data(package())
        self.assertFalse(Lesson.objects.exists())
        self.assertFalse(Unit.objects.exists())
        self.assertFalse(CEFRLevel.objects.exists())

    def test_changed_material_and_context_reset_approval(self):
        import_course_data(package())
        Lesson.objects.update(tutor_material_approved=True)
        Exercise.objects.update(tutor_context_approved=True)
        lesson = Lesson.objects.get()
        lesson.tutor_material["overview_sq"] += " A reviewed revision is needed."
        lesson.save(update_fields=("tutor_material",))
        lesson.refresh_from_db()
        self.assertFalse(lesson.tutor_material_approved)
        exercise = Exercise.objects.first()
        exercise.tutor_context["objective_sq"] = "New objective."
        exercise.save(update_fields=("tutor_context",))
        exercise.refresh_from_db()
        self.assertFalse(exercise.tutor_context_approved)

    def test_unknown_references_are_also_rejected_when_editing_models(self):
        import_course_data(package())
        exercise = Exercise.objects.first()
        exercise.tutor_context["material_keys"] = ["unknown"]
        with self.assertRaises(ValidationError):
            exercise.full_clean()

    def test_teaching_only_update_is_repeatable_and_resets_review(self):
        import_course_data(package())
        data = package("greetings-upgrade-existing-demo-v2.json")
        lesson = lesson_data(data)
        lesson["exercises"] = []
        lesson["vocabulary"] = []
        Exercise.objects.update(tutor_context_approved=True)
        summary = import_course_data(data)
        self.assertEqual(summary["exercises"], 0)
        self.assertEqual(Exercise.objects.count(), 10)
        self.assertFalse(Exercise.objects.get(position=1).tutor_context_approved)
        self.assertTrue(Exercise.objects.get(position=4).tutor_context_approved)

    def test_refresh_file_updates_all_contexts_without_creating_exercises(self):
        import_course_data(package())
        original_ids = list(Exercise.objects.values_list("pk", flat=True))
        result = import_course_data(package("greetings-material-refresh-v2.json"))
        self.assertEqual(result["exercises"], 0)
        self.assertEqual(result["exercise_tutor_contexts"], 10)
        self.assertEqual(list(Exercise.objects.values_list("pk", flat=True)), original_ids)
        self.assertFalse(Exercise.objects.filter(tutor_context_approved=True).exists())


class StructuredTutorIntegrationTests(TestCase):
    def setUp(self):
        import_course_data(package())
        self.learner = get_user_model().objects.create_user(email="context@example.com")
        self.exercise = Exercise.objects.get(position=1)
        self.attempt = ExerciseAttempt.objects.create(
            learner=self.learner,
            exercise=self.exercise,
            selected_option=self.exercise.options.get(is_correct=False, position=2),
            is_correct=False,
        )

    def approve(self):
        Lesson.objects.update(tutor_material_approved=True)
        Exercise.objects.update(tutor_context_approved=True)
        self.exercise = Exercise.objects.select_related("lesson").get(pk=self.exercise.pk)

    def test_unapproved_content_is_excluded_from_provider_context(self):
        context = _lesson_context(self.exercise, self.attempt)
        self.assertEqual(context["reviewed_tutor_material"]["structured_material"], {})
        self.assertEqual(context["exercise"]["teaching_context"], {})

    def test_approved_material_uses_only_current_kind_examples_and_overrides_legacy_notes(self):
        self.approve()
        self.exercise.lesson.tutor_grammar_notes_sq = "LEGACY_MEMORIZE_ONLY"
        context = _lesson_context(self.exercise, self.attempt, kind="grammar")
        material = context["reviewed_tutor_material"]["structured_material"]
        self.assertEqual(len(material["response_examples"]), 1)
        self.assertEqual(material["response_examples"][0]["kind"], "grammar")
        self.assertEqual(len(material["dialogues"]), 3)
        self.assertEqual(context["reviewed_tutor_material"]["grammar_notes_sq"], "")
        self.assertIn("grammar_focus_sq", context["exercise"]["teaching_context"])
        exported = _lesson_context(self.exercise, self.attempt)
        self.assertEqual(
            len(exported["reviewed_tutor_material"]["structured_material"]["response_examples"]), 6
        )

    def test_accepted_answers_are_available_for_teaching_without_changing_grading(self):
        self.approve()
        exercise = Exercise.objects.get(position=8)
        attempt = ExerciseAttempt.objects.create(
            learner=self.learner,
            exercise=exercise,
            answer_text="Einen schönen Tag noch!",
            is_correct=True,
        )
        context = _lesson_context(exercise, attempt)
        self.assertIn("Einen schönen Tag noch!", context["exercise"]["accepted_answers"])
        self.assertTrue(context["learner_attempt"]["is_correct"])

    def test_service_omits_the_rote_mental_task_seen_in_live_replies(self):
        self.approve()
        reply = TutorResponse(
            explanation_sq="Shpjegim i dobishëm.",
            follow_up_sq="Thuaji me mendje: Morgen = mëngjes, Abend = mbrëmje.",
            within_lesson_scope=True,
        )
        provider = SimpleNamespace(ask=lambda *args, **kwargs: SimpleNamespace(data=reply))
        _, response = ask_lesson_tutor(
            exercise=self.exercise, attempt=self.attempt, kind="grammar", client=provider
        )
        self.assertEqual(response.follow_up_sq, "")
        self.assertEqual(response.explanation_sq, reply.explanation_sq)

    def test_staff_can_approve_material_and_contexts_without_publishing(self):
        staff = get_user_model().objects.create_superuser(email="review@example.com")
        self.client.force_login(staff)
        response = self.client.post(
            reverse("admin:courses_lesson_changelist"),
            {
                "action": "approve_reviewed_material",
                "_selected_action": self.exercise.lesson_id,
            },
            follow=True,
        )
        self.assertContains(response, "Approved 1 reviewed tutor content record(s).")
        response = self.client.post(
            reverse("admin:courses_exercise_changelist"),
            {
                "action": "approve_reviewed_contexts",
                "_selected_action": self.exercise.pk,
            },
            follow=True,
        )
        self.assertContains(response, "Approved 1 reviewed tutor content record(s).")
        self.exercise.refresh_from_db()
        self.assertTrue(self.exercise.tutor_context_approved)
        self.assertEqual(self.exercise.review_status, Exercise.ReviewStatus.DRAFT)
        self.assertFalse(Lesson.objects.get().is_published)

    def test_prompt_contains_current_exercise_goal_and_related_language_permission(self):
        self.approve()
        prompt = build_tutor_prompt(
            exercise=self.exercise,
            attempt=self.attempt,
            kind="custom",
            question="si thuhet diten e mire",
        )
        self.assertIn("Related beginner German", prompt)
        self.assertNotIn("Use only the supplied lesson and exercise context", prompt)
        self.assertIn("Schönen Tag noch!", prompt)
        self.assertIn(self.exercise.tutor_context["objective_sq"], prompt)
        context = json.loads(
            prompt.split("LESSON_CONTEXT_JSON:\n")[1].split("\n\nLEARNER_REQUEST_JSON:", 1)[0]
        )
        self.assertEqual(
            [
                item["kind"]
                for item in context["reviewed_tutor_material"]["structured_material"][
                    "response_examples"
                ]
            ],
            ["custom", "custom"],
        )

    @override_settings(TUTOR_ENABLED=True)
    @patch("speech.views.transcribe_german")
    def test_all_ten_uploaded_exercises_grade_and_keep_tutor_access(self, transcribe):
        self.approve()
        publish_units(Unit.objects.all(), self.learner)
        self.client.force_login(self.learner)
        for exercise in Exercise.objects.order_by("position"):
            with self.subTest(position=exercise.position, kind=exercise.exercise_type):
                url = reverse("learning:exercise", args=(exercise.pk,))
                if exercise.exercise_type == Exercise.Type.SPEAKING:
                    transcribe.return_value = exercise.expected_answer
                    response = self.client.post(
                        reverse("speech:transcribe-exercise", args=(exercise.pk,)),
                        {
                            "audio": SimpleUploadedFile(
                                "recording.webm", b"test-audio", content_type="audio/webm"
                            )
                        },
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.json()["is_match"])
                else:
                    if exercise.options.exists():
                        payload = {
                            "option": list(
                                exercise.options.filter(is_correct=True).values_list(
                                    "pk", flat=True
                                )
                            )
                        }
                    else:
                        payload = {"answer": exercise.expected_answer}
                    response = self.client.post(url, payload)
                    self.assertEqual(response.status_code, 302)
                attempt = exercise.attempts.latest("pk")
                self.assertTrue(attempt.is_correct)
                response = self.client.get(url, {"attempt": attempt.pk})
                self.assertContains(response, 'id="lesson-tutor"')
                self.assertContains(response, 'value="grammar"')
