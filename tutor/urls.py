from django.urls import path

from . import views

app_name = "tutor"

urlpatterns = [
    path("exercise/<int:exercise_id>/ask/", views.ask, name="ask"),
]
