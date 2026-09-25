from django.urls import path

from . import views

app_name = "speech"

urlpatterns = [
    path("microphone-check/", views.microphone_check, name="microphone-check"),
    path(
        "exercise/<int:exercise_id>/transcribe/",
        views.transcribe_exercise,
        name="transcribe-exercise",
    ),
]
