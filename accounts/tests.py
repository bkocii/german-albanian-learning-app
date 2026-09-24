from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(
    MAILERS={
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
)
class UserModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_project_uses_custom_user_model(self):
        self.assertIsNot(self.user_model, DjangoUser)
        self.assertEqual(self.user_model._meta.label, "accounts.User")

    def test_create_user_normalizes_email_and_hashes_password(self):
        user = self.user_model.objects.create_user(
            email="Learner@EXAMPLE.COM",
            password="safe-test-password",
        )

        self.assertEqual(user.email, "learner@example.com")
        self.assertTrue(user.check_password("safe-test-password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_is_required(self):
        with self.assertRaisesMessage(ValueError, "email address must be provided"):
            self.user_model.objects.create_user(email="", password="password")

    def test_create_superuser_sets_required_permissions(self):
        user = self.user_model.objects.create_superuser(
            email="admin@example.com",
            password="safe-test-password",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


@override_settings(
    MAILERS={
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
)
class AccountWorkflowTests(TestCase):
    password = "Strong-test-password-728!"

    def setUp(self):
        cache.clear()
        self.user_model = get_user_model()

    def register_user(self, email="learner@example.com"):
        return self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Arta",
                "last_name": "Krasniqi",
                "email": email,
                "password1": self.password,
                "password2": self.password,
            },
        )

    def test_registration_creates_inactive_user_and_sends_verification(self):
        response = self.register_user("Learner@Example.com")

        self.assertRedirects(response, reverse("accounts:verification-sent"))
        user = self.user_model.objects.get(email="learner@example.com")
        self.assertFalse(user.is_active)
        self.assertIsNone(user.email_verified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/verify/", mail.outbox[0].body)

    def test_verification_link_activates_account(self):
        self.register_user()
        verification_url = next(
            line for line in mail.outbox[0].body.splitlines() if "/accounts/verify/" in line
        )

        response = self.client.get(urlparse(verification_url).path)

        user = self.user_model.objects.get(email="learner@example.com")
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.email_verified_at)

    def test_unverified_user_cannot_log_in(self):
        self.user_model.objects.create_user(
            email="learner@example.com",
            password=self.password,
            is_active=False,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "learner@example.com", "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_sends_email_for_active_user(self):
        self.user_model.objects.create_user(
            email="learner@example.com",
            password=self.password,
            is_active=True,
        )

        response = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "learner@example.com"},
        )

        self.assertRedirects(response, reverse("accounts:password-reset-done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_new_login_replaces_previous_active_session(self):
        user = self.user_model.objects.create_user(
            email="learner@example.com",
            password=self.password,
            is_active=True,
        )
        first_client = Client()
        second_client = Client()

        self.assertTrue(first_client.login(email=user.email, password=self.password))
        first_session_key = first_client.session.session_key
        self.assertTrue(second_client.login(email=user.email, password=self.password))
        second_session_key = second_client.session.session_key

        user.refresh_from_db()
        self.assertNotEqual(first_session_key, second_session_key)
        self.assertEqual(user.active_session_key, second_session_key)

        first_response = first_client.get(reverse("accounts:dashboard"), follow=True)
        second_response = second_client.get(reverse("accounts:dashboard"))

        self.assertRedirects(first_response, reverse("accounts:login"))
        self.assertContains(first_response, "pajisje tjetër")
        self.assertEqual(second_response.status_code, 200)

    def test_logout_clears_active_session(self):
        user = self.user_model.objects.create_user(
            email="learner@example.com",
            password=self.password,
            is_active=True,
        )
        self.client.login(email=user.email, password=self.password)

        response = self.client.post(reverse("accounts:logout"))

        user.refresh_from_db()
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(user.active_session_key, "")

    @override_settings(AUTH_RATE_LIMIT_ATTEMPTS=1, AUTH_RATE_LIMIT_WINDOW_SECONDS=60)
    def test_repeated_failed_login_is_rate_limited(self):
        login_url = reverse("accounts:login")
        credentials = {"username": "unknown@example.com", "password": "incorrect"}

        first_response = self.client.post(login_url, credentials)
        second_response = self.client.post(login_url, credentials)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 429)
        self.assertContains(second_response, "Shumë përpjekje", status_code=429)
