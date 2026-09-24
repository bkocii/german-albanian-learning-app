from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class SingleActiveSessionMiddleware:
    """Keep only the most recently authenticated session active for each user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and user.active_session_key
            and user.active_session_key != request.session.session_key
        ):
            logout(request)
            messages.warning(
                request,
                "Kjo llogari është hapur në një pajisje tjetër. Hyni përsëri për ta përdorur këtu.",
            )
            return redirect("accounts:login")

        return self.get_response(request)
