from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def microphone_check(request):
    return render(
        request,
        "speech/microphone_check.html",
        {"max_recording_seconds": settings.SPEECH_MAX_RECORDING_SECONDS},
    )
