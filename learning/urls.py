from django.urls import path

from . import views

app_name = "learning"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path(
        "<str:level_code>/<slug:unit_slug>/<slug:lesson_slug>/",
        views.lesson_start,
        name="lesson-start",
    ),
    path("exercise/<int:exercise_id>/", views.exercise_player, name="exercise"),
]
