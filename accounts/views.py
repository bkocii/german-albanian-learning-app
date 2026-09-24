from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .emails import find_unverified_user, send_verification_email
from .forms import RegistrationForm, ResendVerificationForm
from .throttling import rate_limit
from .tokens import email_verification_token

User = get_user_model()


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "home.html")


@rate_limit("register")
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        send_verification_email(request, user)
        request.session["verification_email"] = user.email
        return redirect("accounts:verification-sent")

    return render(request, "accounts/register.html", {"form": form})


def verification_sent(request):
    return render(
        request,
        "accounts/verification_sent.html",
        {"verification_email": request.session.get("verification_email")},
    )


def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and user.is_email_verified:
        messages.info(request, "Emaili është verifikuar tashmë. Mund të hyni.")
        return redirect("accounts:login")

    if user and email_verification_token.check_token(user, token):
        user.is_active = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["is_active", "email_verified_at"])
        messages.success(request, "Emaili u verifikua. Tani mund të hyni në llogari.")
        return redirect("accounts:login")

    return render(request, "accounts/verification_invalid.html", status=400)


@rate_limit("resend-verification")
def resend_verification(request):
    form = ResendVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = find_unverified_user(form.cleaned_data["email"])
        if user:
            send_verification_email(request, user)
        request.session["verification_email"] = form.cleaned_data["email"]
        messages.success(
            request,
            "Nëse llogaria pret verifikim, ju dërguam një lidhje të re.",
        )
        return redirect("accounts:verification-sent")

    return render(request, "accounts/resend_verification.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "accounts/dashboard.html")


@method_decorator(rate_limit("login"), name="dispatch")
class AccountLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        address = self.request.META.get("REMOTE_ADDR", "unknown")
        cache.delete(f"auth-rate-limit:login:{address}")
        return super().form_valid(form)


@method_decorator(rate_limit("password-reset"), name="dispatch")
class AccountPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.txt"
    subject_template_name = "registration/password_reset_subject.txt"
