from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Exercise, Unit

CHOICE_TYPES = {
    Exercise.Type.PICTURE_CHOICE,
    Exercise.Type.TRANSLATION_CHOICE,
    Exercise.Type.TRUE_FALSE,
    Exercise.Type.DIALOGUE_CHOICE,
    Exercise.Type.MULTIPLE_SELECT,
}


def _exercise_label(exercise):
    return exercise.external_id or f"exercise {exercise.pk}"


def _validate_related_content(exercise):
    errors = []
    label = _exercise_label(exercise)

    if exercise.exercise_type in CHOICE_TYPES:
        options = list(exercise.options.all())
        if len(options) < 2:
            errors.append(f"{label}: choice exercises require at least two options.")
        for option in options:
            try:
                option.full_clean()
            except ValidationError as error:
                errors.extend(f"{label}: {message}" for message in error.messages)

        correct_count = sum(option.is_correct for option in options)
        if exercise.exercise_type == Exercise.Type.TRUE_FALSE and len(options) != 2:
            errors.append(f"{label}: true/false requires exactly two options.")
        if exercise.exercise_type == Exercise.Type.MULTIPLE_SELECT:
            if len(options) < 3:
                errors.append(f"{label}: multiple select requires at least three options.")
            if correct_count < 2:
                errors.append(f"{label}: multiple select requires at least two correct options.")
            if options and correct_count == len(options):
                errors.append(f"{label}: multiple select requires an incorrect option.")
        elif correct_count != 1:
            errors.append(f"{label}: exactly one option must be correct.")

    if exercise.exercise_type == Exercise.Type.FREE_TEXT:
        accepted_answers = list(exercise.accepted_answers.all())
        if not accepted_answers:
            errors.append(f"{label}: free text requires an accepted-answer variant.")
        for answer in accepted_answers:
            try:
                answer.full_clean()
            except ValidationError as error:
                errors.extend(f"{label}: {message}" for message in error.messages)

    if exercise.exercise_type == Exercise.Type.MATCHING:
        pairs = list(exercise.matching_pairs.all())
        if len(pairs) < 2:
            errors.append(f"{label}: matching requires at least two pairs.")
        for pair in pairs:
            try:
                pair.full_clean()
            except ValidationError as error:
                errors.extend(f"{label}: {message}" for message in error.messages)

    return errors


@transaction.atomic
def publish_units(units, reviewer):
    selected_units = list(
        Unit.objects.filter(pk__in=[unit.pk for unit in units])
        .select_related("level")
        .prefetch_related(
            "lessons__exercises__options",
            "lessons__exercises__accepted_answers",
            "lessons__exercises__matching_pairs",
        )
    )
    now = timezone.now()
    errors = []
    exercises = []

    for unit in selected_units:
        lessons = list(unit.lessons.all())
        if not lessons:
            errors.append(f"{unit}: the unit has no lessons.")
            continue
        for lesson in lessons:
            lesson_exercises = list(lesson.exercises.all())
            if not lesson_exercises:
                errors.append(f"{lesson}: the lesson has no exercises.")
            for exercise in lesson_exercises:
                exercise.review_status = Exercise.ReviewStatus.PUBLISHED
                exercise.reviewed_by = reviewer
                exercise.reviewed_at = now
                try:
                    exercise.full_clean()
                except ValidationError as error:
                    errors.extend(
                        f"{_exercise_label(exercise)}: {message}"
                        for message in error.messages
                    )
                errors.extend(_validate_related_content(exercise))
                exercises.append(exercise)

    if errors:
        raise ValidationError(errors)

    Exercise.objects.filter(pk__in=[exercise.pk for exercise in exercises]).update(
        review_status=Exercise.ReviewStatus.PUBLISHED,
        reviewed_by=reviewer,
        reviewed_at=now,
        updated_at=now,
    )
    for unit in selected_units:
        unit.lessons.update(is_published=True)
        unit.is_published = True
        unit.save(update_fields=["is_published"])
        if not unit.level.is_published:
            unit.level.is_published = True
            unit.level.save(update_fields=["is_published"])

    return len(selected_units), len(exercises)


@transaction.atomic
def unpublish_units(units):
    selected_units = list(Unit.objects.filter(pk__in=[unit.pk for unit in units]))
    exercise_count = 0
    for unit in selected_units:
        exercise_count += Exercise.objects.filter(
            lesson__unit=unit,
            review_status=Exercise.ReviewStatus.PUBLISHED,
        ).update(review_status=Exercise.ReviewStatus.REVIEWED)
        unit.lessons.update(is_published=False)
        unit.is_published = False
        unit.save(update_fields=["is_published"])
    return len(selected_units), exercise_count
