from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render


def rate_limit(scope):
    """Limit repeated POST submissions by route and client address."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method == "POST":
                address = request.META.get("REMOTE_ADDR", "unknown")
                cache_key = f"auth-rate-limit:{scope}:{address}"
                attempts = cache.get(cache_key, 0)
                if attempts >= settings.AUTH_RATE_LIMIT_ATTEMPTS:
                    return render(request, "accounts/rate_limited.html", status=429)
                if not cache.add(
                    cache_key,
                    1,
                    timeout=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
                ):
                    cache.incr(cache_key)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
