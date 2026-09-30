import random

from django.conf import settings
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
        .prefetch_related("options", "accepted_answers", "matching_pairs")
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


def _matching_rows(exercise, learner):
    pairs = list(exercise.matching_pairs.all())
    right_answers = [pair.right_text for pair in pairs]
    random.Random(f"matching:{learner.pk}:{exercise.pk}").shuffle(right_answers)
    if len(right_answers) > 1 and right_answers == [pair.right_text for pair in pairs]:
        right_answers = right_answers[1:] + right_answers[:1]
    return [{"pair": pair, "right_answers": right_answers} for pair in pairs]


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
        Exercise.objects.select_related(
            "lesson__unit__level", "image", "audio"
        ).prefetch_related("options", "accepted_answers", "matching_pairs"),
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
        if exercise.exercise_type == Exercise.Type.SPEAKING:
            messages.warning(request, "Përdorni butonin e mikrofonit për këtë ushtrim.")
            return redirect("learning:exercise", exercise_id=exercise.pk)
        option = None
        answer_text = request.POST.get("answer", "").strip()
        option_id = request.POST.get("option")
        choice_types = {
            Exercise.Type.PICTURE_CHOICE,
            Exercise.Type.TRANSLATION_CHOICE,
            Exercise.Type.TRUE_FALSE,
            Exercise.Type.DIALOGUE_CHOICE,
        }
        if exercise.exercise_type == Exercise.Type.MATCHING:
            pairs = list(exercise.matching_pairs.all())
            submitted = [request.POST.get(f"match_{pair.pk}", "") for pair in pairs]
            if not pairs or any(not value for value in submitted):
                messages.warning(request, "Plotësoni të gjitha çiftet.")
                return redirect("learning:exercise", exercise_id=exercise.pk)
            is_correct = all(
                selected == pair.right_text for pair, selected in zip(pairs, submitted)
            )
            answer_text = " | ".join(
                f"{pair.left_text} — {selected}"
                for pair, selected in zip(pairs, submitted)
            )
        elif exercise.exercise_type in choice_types and option_id:
            option = get_object_or_404(ExerciseOption, pk=option_id, exercise=exercise)
            is_correct = option.is_correct
        elif exercise.exercise_type == Exercise.Type.FREE_TEXT and answer_text:
            accepted_answers = {
                _normalize_answer(exercise.expected_answer),
                *(
                    _normalize_answer(answer.text)
                    for answer in exercise.accepted_answers.all()
                ),
            }
            is_correct = _normalize_answer(answer_text) in accepted_answers
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
    correct_option = None
    attempt_id = request.GET.get("attempt")
    if attempt_id:
        attempt = ExerciseAttempt.objects.filter(
            pk=attempt_id, learner=request.user, exercise=exercise
        ).first()
        if attempt and not attempt.is_correct:
            correct_option = exercise.options.filter(is_correct=True).first()

    next_exercise = exercises[index + 1] if index + 1 < len(exercises) else None
    context = {
        "exercise": exercise,
        "attempt": attempt,
        "correct_option": correct_option,
        "next_exercise": next_exercise,
        "progress": progress,
        "step_number": index + 1,
        "step_total": len(exercises),
        "word_tokens": (
            _word_tokens(exercise, request.user)
            if exercise.exercise_type == Exercise.Type.WORD_ORDER
            else []
        ),
        "matching_rows": (
            _matching_rows(exercise, request.user)
            if exercise.exercise_type == Exercise.Type.MATCHING
            else []
        ),
        "speech_max_recording_seconds": settings.SPEECH_MAX_RECORDING_SECONDS,
    }
    return render(request, "learning/exercise_player.html", context)
