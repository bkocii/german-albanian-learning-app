import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from courses.models import CEFRLevel, Exercise, ExerciseOption, Lesson, Unit

from .models import ExerciseAttempt, LessonProgress


def _published_exercises(lesson):
    return list(
        lesson.exercises.filter(review_status=Exercise.ReviewStatus.PUBLISHED)
        .prefetch_related("options")
        .select_related("image", "audio")
    )


def _normalize_answer(value):
    return " ".join(value.casefold().split())


def _word_tokens(exercise, learner):
    tokens = exercise.expected_answer.split()
    original = tokens.copy()
    random.Random(f"{learner.pk}:{exercise.pk}").shuffle(tokens)
    if len(tokens) > 1 and tokens == original:
        tokens = tokens[1:] + tokens[:1]
    return tokens


@login_required
def catalog(request):
    completed = LessonProgress.objects.filter(
        learner=request.user,
        lesson=OuterRef("pk"),
        completed_at__isnull=False,
    )
    lessons = Lesson.objects.filter(is_published=True).annotate(
        learner_completed=Exists(completed)
    )
    units = Unit.objects.filter(is_published=True).prefetch_related(
        Prefetch("lessons", queryset=lessons)
    )
    levels = CEFRLevel.objects.filter(is_published=True).prefetch_related(
        Prefetch("units", queryset=units)
    )
    return render(request, "learning/catalog.html", {"levels": levels})


@login_required
def lesson_start(request, level_code, unit_slug, lesson_slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("unit__level"),
        unit__level__code=level_code,
        unit__slug=unit_slug,
        slug=lesson_slug,
        unit__level__is_published=True,
        unit__is_published=True,
        is_published=True,
    )
    exercises = _published_exercises(lesson)
    if not exercises:
        messages.info(request, "Ky mësim ende nuk ka ushtrime të publikuara.")
        return redirect("learning:catalog")
    LessonProgress.objects.get_or_create(learner=request.user, lesson=lesson)
    return redirect("learning:exercise", exercise_id=exercises[0].pk)


@login_required
def exercise_player(request, exercise_id):
    exercise = get_object_or_404(
        Exercise.objects.select_related("lesson__unit__level", "image", "audio").prefetch_related(
            "options"
        ),
        pk=exercise_id,
        review_status=Exercise.ReviewStatus.PUBLISHED,
        lesson__is_published=True,
        lesson__unit__is_published=True,
        lesson__unit__level__is_published=True,
    )
    lesson = exercise.lesson
    progress, _ = LessonProgress.objects.get_or_create(learner=request.user, lesson=lesson)
    exercises = _published_exercises(lesson)
    exercise_ids = [item.pk for item in exercises]
    try:
        index = exercise_ids.index(exercise.pk)
    except ValueError as error:
        raise Http404 from error

    if request.method == "POST":
        option = None
        answer_text = request.POST.get("answer", "").strip()
        option_id = request.POST.get("option")
        choice_types = {
            Exercise.Type.PICTURE_CHOICE,
            Exercise.Type.TRANSLATION_CHOICE,
        }
        if exercise.exercise_type in choice_types and option_id:
            option = get_object_or_404(ExerciseOption, pk=option_id, exercise=exercise)
            is_correct = option.is_correct
        elif exercise.exercise_type not in choice_types and answer_text:
            is_correct = _normalize_answer(answer_text) == _normalize_answer(
                exercise.expected_answer
            )
        else:
            messages.warning(request, "Zgjidhni ose shkruani një përgjigje.")
            return redirect("learning:exercise", exercise_id=exercise.pk)

        attempt = ExerciseAttempt.objects.create(
            learner=request.user,
            exercise=exercise,
            selected_option=option,
            answer_text=answer_text,
            is_correct=is_correct,
        )
        progress.save(update_fields=["last_activity_at"])
        attempted_exercise_count = (
            ExerciseAttempt.objects.filter(
                learner=request.user,
                exercise_id__in=exercise_ids,
            )
            .values("exercise_id")
            .distinct()
            .count()
        )
        if attempted_exercise_count == len(exercises):
            progress.completed_at = timezone.now()
            progress.save(update_fields=["completed_at", "last_activity_at"])
        result_url = reverse("learning:exercise", kwargs={"exercise_id": exercise.pk})
        return redirect(f"{result_url}?attempt={attempt.pk}")

    attempt = None
    attempt_id = request.GET.get("attempt")
    if attempt_id:
        attempt = ExerciseAttempt.objects.filter(
            pk=attempt_id, learner=request.user, exercise=exercise
        ).first()

    next_exercise = exercises[index + 1] if index + 1 < len(exercises) else None
    context = {
        "exercise": exercise,
        "attempt": attempt,
        "next_exercise": next_exercise,
        "progress": progress,
        "step_number": index + 1,
        "step_total": len(exercises),
        "word_tokens": (
            _word_tokens(exercise, request.user)
            if exercise.exercise_type == Exercise.Type.WORD_ORDER
            else []
        ),
    }
    return render(request, "learning/exercise_player.html", context)
