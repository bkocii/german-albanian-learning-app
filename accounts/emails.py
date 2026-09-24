from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token


def send_verification_email(request, user) -> None:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify-email", kwargs={"uidb64": uid, "token": token})
    )
    context = {"user": user, "verification_url": verification_url}
    send_mail(
        subject="Verifiko emailin tënd",
        message=render_to_string("accounts/emails/verify_email.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        using="default",
    )


def find_unverified_user(email):
    return (
        get_user_model()
        .objects.filter(email__iexact=email, is_active=False, email_verified_at__isnull=True)
        .first()
    )
