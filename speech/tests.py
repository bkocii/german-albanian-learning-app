from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from courses.models import CEFRLevel, Exercise, Lesson, Unit
from learning.models import ExerciseAttempt

from .services import compare_recognized_words


class MicrophoneCheckTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="speaker@example.com", password="secure-test-password"
        )

    def test_microphone_check_requires_login(self):
        url = reverse("speech:microphone-check")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    @override_settings(SPEECH_MAX_RECORDING_SECONDS=12)
    def test_microphone_check_exposes_limit_and_privacy_message(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("speech:microphone-check"))
        self.assertContains(response, 'data-max-seconds="12"')
        self.assertContains(response, "nuk dërgohet në server")
        self.assertContains(response, "Fillo regjistrimin")

    def test_dashboard_links_to_microphone_check(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, reverse("speech:microphone-check"))


class SpeakingTranscriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learner = get_user_model().objects.create_user(
            email="speech-learner@example.com", password="secure-test-password"
        )
        cls.reviewer = get_user_model().objects.create_user(
            email="speech-reviewer@example.com", password="secure-test-password"
        )
        level = CEFRLevel.objects.create(
            code="A1",
            title_de="Anfänger",
            title_sq="Fillestar",
            position=1,
            is_published=True,
        )
        unit = Unit.objects.create(
            level=level,
            slug="sprechen",
            title_de="Sprechen",
            title_sq="Të folurit",
            position=1,
            is_published=True,
        )
        lesson = Lesson.objects.create(
            unit=unit,
            slug="hallo-sagen",
            title_de="Hallo sagen",
            title_sq="Thuaj përshëndetje",
            position=1,
            is_published=True,
        )
        cls.exercise = Exercise.objects.create(
            lesson=lesson,
            exercise_type=Exercise.Type.SPEAKING,
            instructions_sq="Thuaj fjalinë.",
            expected_answer="Guten Morgen",
            position=1,
            review_status=Exercise.ReviewStatus.PUBLISHED,
            reviewed_by=cls.reviewer,
            reviewed_at=timezone.now(),
        )

    def setUp(self):
        cache.clear()
        self.client.force_login(self.learner)

    @patch("speech.views.transcribe_german")
    def test_audio_is_transcribed_attempt_recorded_and_temporary_file_deleted(self, transcribe):
        temporary_paths = []

        def fake_transcription(path):
            temporary_paths.append(Path(path))
            self.assertTrue(Path(path).exists())
            return "Guten Morgen"

        transcribe.side_effect = fake_transcription
        upload = SimpleUploadedFile("recording.webm", b"audio-data", content_type="audio/webm")
        response = self.client.post(
            reverse("speech:transcribe-exercise", args=(self.exercise.pk,)),
            {"audio": upload},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_match"])
        self.assertTrue(ExerciseAttempt.objects.get().is_correct)
        self.assertTrue(temporary_paths)
        self.assertFalse(temporary_paths[0].exists())

    @override_settings(SPEECH_MAX_UPLOAD_BYTES=3)
    @patch("speech.views.transcribe_german")
    def test_oversized_audio_is_rejected_before_transcription(self, transcribe):
        upload = SimpleUploadedFile("recording.webm", b"large", content_type="audio/webm")
        response = self.client.post(
            reverse("speech:transcribe-exercise", args=(self.exercise.pk,)),
            {"audio": upload},
        )
        self.assertEqual(response.status_code, 400)
        transcribe.assert_not_called()

    @patch("speech.views.transcribe_german")
    def test_unsupported_file_type_is_rejected(self, transcribe):
        upload = SimpleUploadedFile("recording.txt", b"audio", content_type="text/plain")
        response = self.client.post(
            reverse("speech:transcribe-exercise", args=(self.exercise.pk,)),
            {"audio": upload},
        )
        self.assertEqual(response.status_code, 400)
        transcribe.assert_not_called()

    def test_word_feedback_reports_matches_and_missing_words(self):
        result = compare_recognized_words("Guten Morgen Anna", "Guten Anna")
        self.assertEqual(result["matched_words"], ["guten", "anna"])
        self.assertEqual(result["missing_words"], ["morgen"])
        self.assertFalse(result["is_match"])

    @override_settings(SPEECH_TRANSCRIPTION_RATE_ATTEMPTS=1)
    @patch("speech.views.transcribe_german", return_value="Guten Morgen")
    def test_repeated_transcription_is_rate_limited_per_user(self, transcribe):
        url = reverse("speech:transcribe-exercise", args=(self.exercise.pk,))
        first = SimpleUploadedFile("first.webm", b"audio", content_type="audio/webm")
        second = SimpleUploadedFile("second.webm", b"audio", content_type="audio/webm")
        self.assertEqual(self.client.post(url, {"audio": first}).status_code, 200)
        self.assertEqual(self.client.post(url, {"audio": second}).status_code, 429)
        self.assertEqual(transcribe.call_count, 1)
