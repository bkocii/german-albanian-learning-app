from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in)
def record_active_session(sender, request, user, **kwargs):
    if request.session.session_key is None:
        request.session.save()
    user.active_session_key = request.session.session_key
    user.save(update_fields=["active_session_key"])


@receiver(user_logged_out)
def clear_active_session(sender, request, user, **kwargs):
    if user is None:
        return
    if user.active_session_key == request.session.session_key:
        user.active_session_key = ""
        user.save(update_fields=["active_session_key"])
