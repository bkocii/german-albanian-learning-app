from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


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
