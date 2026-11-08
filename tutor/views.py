from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from courses.models import Exercise
from learning.models import ExerciseAttempt

from .budget import reserve_daily_request
from .models import TutorExchange
from .services import TutorServiceError, ask_lesson_tutor


def _exercise_url(exercise, attempt, exchange=None):
    url = reverse("learning:exercise", args=(exercise.pk,))
    query = f"attempt={attempt.pk}"
    if exchange:
        query += f"&tutor={exchange.pk}"
    return f"{url}?{query}"


@login_required
@require_POST
def ask(request, exercise_id):
    exercise = get_object_or_404(
        Exercise.objects.select_related("lesson__unit__level")
        .prefetch_related("lesson__vocabulary", "lesson__tutor_examples", "options"),
        pk=exercise_id,
        review_status=Exercise.ReviewStatus.PUBLISHED,
        lesson__is_published=True,
        lesson__unit__is_published=True,
        lesson__unit__level__is_published=True,
    )
    attempt = get_object_or_404(
        ExerciseAttempt,
        pk=request.POST.get("attempt"),
        learner=request.user,
        exercise=exercise,
    )

    if not settings.TUTOR_ENABLED:
        messages.warning(request, "Tutori i mësimit nuk është aktivizuar.")
        return redirect(_exercise_url(exercise, attempt))

    kind = request.POST.get("kind", "")
    valid_kinds = {value for value, _ in TutorExchange.Kind.choices}
    if kind not in valid_kinds:
        messages.warning(request, "Zgjidhni llojin e shpjegimit që dëshironi.")
        return redirect(_exercise_url(exercise, attempt))

    question = request.POST.get("question", "").strip()
    if kind == TutorExchange.Kind.CUSTOM and not question:
        messages.warning(request, "Shkruani pyetjen tuaj për këtë mësim.")
        return redirect(_exercise_url(exercise, attempt))
    if len(question) > settings.TUTOR_MAX_QUESTION_LENGTH:
        messages.warning(request, "Pyetja është shumë e gjatë.")
        return redirect(_exercise_url(exercise, attempt))

    cutoff = timezone.now() - timedelta(seconds=settings.TUTOR_RATE_WINDOW_SECONDS)
    recent_count = TutorExchange.objects.filter(
        learner=request.user, created_at__gte=cutoff
    ).count()
    if recent_count >= settings.TUTOR_RATE_ATTEMPTS:
        messages.warning(
            request,
            "Keni arritur kufirin e përkohshëm të pyetjeve. Provoni përsëri pas pak.",
        )
        return redirect(_exercise_url(exercise, attempt))

    if not reserve_daily_request(settings.TUTOR_DAILY_REQUEST_LIMIT):
        messages.warning(
            request,
            "Tutori ka arritur kufirin ditor. Provoni përsëri nesër.",
        )
        return redirect(_exercise_url(exercise, attempt))

    try:
        result, response = ask_lesson_tutor(
            exercise=exercise,
            attempt=attempt,
            kind=kind,
            question=question,
        )
    except TutorServiceError:
        messages.warning(
            request,
            "Tutori nuk mundi të përgjigjej tani. Provoni përsëri pas pak.",
        )
        return redirect(_exercise_url(exercise, attempt))

    usage = result.token_usage
    exchange = TutorExchange.objects.create(
        learner=request.user,
        exercise=exercise,
        attempt=attempt,
        kind=kind,
        question=question,
        explanation_sq=response.explanation_sq,
        german_examples=[example.model_dump() for example in response.german_examples],
        follow_up_sq=response.follow_up_sq,
        within_lesson_scope=response.within_lesson_scope,
        model_name=result.model,
        request_id=result.request_id,
        duration_ms=result.duration_ms,
        input_tokens=usage.input_tokens if usage else None,
        output_tokens=usage.output_tokens if usage else None,
        estimated_cost_usd=result.estimated_cost_usd,
    )
    return redirect(_exercise_url(exercise, attempt, exchange))


@login_required
@require_POST
def rate(request, exchange_id):
    exchange = get_object_or_404(
        TutorExchange.objects.select_related("exercise", "attempt"),
        pk=exchange_id,
        learner=request.user,
    )
    rating = request.POST.get("rating", "")
    valid_ratings = {value for value, _ in TutorExchange.FeedbackRating.choices}
    if rating not in valid_ratings:
        messages.warning(request, "Zgjidhni një vlerësim të vlefshëm.")
        return redirect(_exercise_url(exchange.exercise, exchange.attempt, exchange))

    exchange.feedback_rating = rating
    exchange.feedback_rated_at = timezone.now()
    exchange.save(update_fields=("feedback_rating", "feedback_rated_at"))
    messages.success(request, "Faleminderit për vlerësimin.")
    return redirect(_exercise_url(exchange.exercise, exchange.attempt, exchange))

