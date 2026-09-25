import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from courses.models import Exercise
from learning.models import ExerciseAttempt, LessonProgress

from .services import (
    SpeechUploadError,
    compare_recognized_words,
    temporary_audio_file,
    transcribe_german,
)

logger = logging.getLogger(__name__)


def _transcription_rate_limited(user_id):
    key = f"speech-transcription-rate:{user_id}"
    window = settings.SPEECH_TRANSCRIPTION_RATE_WINDOW_SECONDS
    if cache.add(key, 1, timeout=window):
        return False
    return cache.incr(key) > settings.SPEECH_TRANSCRIPTION_RATE_ATTEMPTS


@login_required
def microphone_check(request):
    return render(
        request,
        "speech/microphone_check.html",
        {"max_recording_seconds": settings.SPEECH_MAX_RECORDING_SECONDS},
    )


@login_required
@require_POST
def transcribe_exercise(request, exercise_id):
    if _transcription_rate_limited(request.user.pk):
        return JsonResponse(
            {"error": "Shumë tentativa. Prisni pak para se të provoni përsëri."},
            status=429,
        )
    exercise = get_object_or_404(
        Exercise.objects.select_related("lesson__unit__level"),
        pk=exercise_id,
        exercise_type=Exercise.Type.SPEAKING,
        review_status=Exercise.ReviewStatus.PUBLISHED,
        lesson__is_published=True,
        lesson__unit__is_published=True,
        lesson__unit__level__is_published=True,
    )
    upload = request.FILES.get("audio")
    if not upload:
        return JsonResponse({"error": "Mungon regjistrimi i zërit."}, status=400)

    try:
        with temporary_audio_file(upload) as audio_path:
            transcript = transcribe_german(audio_path)
    except SpeechUploadError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception:
        logger.exception("German speech transcription failed")
        return JsonResponse(
            {"error": "Transkriptimi nuk është i disponueshëm tani. Provoni përsëri."},
            status=503,
        )

    if not transcript:
        return JsonResponse(
            {"error": "Nuk u njoh asnjë fjalë. Flisni më afër mikrofonit dhe provoni përsëri."},
            status=422,
        )

    comparison = compare_recognized_words(exercise.expected_answer, transcript)
    attempt = ExerciseAttempt.objects.create(
        learner=request.user,
        exercise=exercise,
        answer_text=transcript,
        is_correct=comparison["is_match"],
    )

    published_exercises = list(
        exercise.lesson.exercises.filter(review_status=Exercise.ReviewStatus.PUBLISHED)
    )
    published_ids = [item.pk for item in published_exercises]
    attempted_count = (
        ExerciseAttempt.objects.filter(learner=request.user, exercise_id__in=published_ids)
        .values("exercise_id")
        .distinct()
        .count()
    )
    progress, _ = LessonProgress.objects.get_or_create(
        learner=request.user, lesson=exercise.lesson
    )
    progress.save(update_fields=["last_activity_at"])
    if attempted_count == len(published_ids):
        progress.completed_at = timezone.now()
        progress.save(update_fields=["completed_at", "last_activity_at"])

    index = published_ids.index(exercise.pk)
    if index + 1 < len(published_exercises):
        next_url = reverse("learning:exercise", args=(published_exercises[index + 1].pk,))
    else:
        next_url = reverse("learning:catalog")

    return JsonResponse(
        {
            "attempt_id": attempt.pk,
            "transcript": transcript,
            "expected": exercise.expected_answer,
            "next_url": next_url,
            **comparison,
        }
    )
