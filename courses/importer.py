from dataclasses import dataclass, field

from django.db import transaction

from .models import (
    CEFRLevel,
    Exercise,
    ExerciseAcceptedAnswer,
    ExerciseOption,
    Lesson,
    MatchingPair,
    MediaAsset,
    Unit,
    VocabularyEntry,
)


@dataclass
class ImportValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(
        default_factory=lambda: {
            "units": 0,
            "lessons": 0,
            "vocabulary": 0,
            "exercises": 0,
            "options": 0,
            "accepted_answers": 0,
            "matching_pairs": 0,
        }
    )

    @property
    def is_valid(self):
        return not self.errors


class CourseImportError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Course import validation failed.")


def _required_text(item, field_name, path, result):
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        result.errors.append(f"{path}.{field_name}: a non-empty string is required.")
        return ""
    return value.strip()


def _positive_position(item, path, result):
    value = item.get("position")
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        result.errors.append(f"{path}.position: a positive integer is required.")
        return None
    return value


def _list_field(item, field_name, path, result):
    value = item.get(field_name, [])
    if not isinstance(value, list):
        result.errors.append(f"{path}.{field_name}: must be a list.")
        return []
    return value


def _check_unique(values, label, path, result):
    filtered = [value for value in values if value is not None]
    if len(filtered) != len(set(filtered)):
        result.errors.append(f"{path}: duplicate {label} values are not allowed.")


def validate_course_import(data):
    result = ImportValidationResult()
    if not isinstance(data, dict):
        result.errors.append("The JSON root must be an object.")
        return result
    if data.get("schema_version") != 1:
        result.errors.append("schema_version must be 1.")

    level_data = data.get("level")
    if not isinstance(level_data, dict):
        result.errors.append("level: an object is required.")
        return result
    code = _required_text(level_data, "code", "level", result)
    _required_text(level_data, "title_de", "level", result)
    _required_text(level_data, "title_sq", "level", result)
    level_position = _positive_position(level_data, "level", result)
    if code and code not in CEFRLevel.Code.values:
        result.errors.append("level.code: must be A1, A2, B1, or B2.")

    existing_level = CEFRLevel.objects.filter(code=code).first() if code else None
    if not existing_level and level_position:
        if CEFRLevel.objects.filter(position=level_position).exists():
            result.errors.append(f"level.position: position {level_position} is already in use.")
    elif existing_level:
        result.warnings.append(f"Level {code} already exists and will be reused without changes.")

    units = _list_field(data, "units", "root", result)
    _check_unique(
        [unit.get("slug") for unit in units if isinstance(unit, dict)],
        "unit slug",
        "units",
        result,
    )
    _check_unique(
        [unit.get("position") for unit in units if isinstance(unit, dict)],
        "unit position",
        "units",
        result,
    )

    for unit_index, unit_data in enumerate(units, start=1):
        unit_path = f"units[{unit_index}]"
        if not isinstance(unit_data, dict):
            result.errors.append(f"{unit_path}: must be an object.")
            continue
        result.summary["units"] += 1
        unit_slug = _required_text(unit_data, "slug", unit_path, result)
        _required_text(unit_data, "title_de", unit_path, result)
        _required_text(unit_data, "title_sq", unit_path, result)
        unit_position = _positive_position(unit_data, unit_path, result)
        existing_unit = None
        if existing_level and unit_slug:
            existing_unit = Unit.objects.filter(level=existing_level, slug=unit_slug).first()
            if existing_unit:
                result.warnings.append(f"{unit_path}: existing unit will be reused.")
            elif unit_position and Unit.objects.filter(
                level=existing_level, position=unit_position
            ).exists():
                result.errors.append(
                    f"{unit_path}.position: position {unit_position} is already in use."
                )

        lessons = _list_field(unit_data, "lessons", unit_path, result)
        _check_unique(
            [lesson.get("slug") for lesson in lessons if isinstance(lesson, dict)],
            "lesson slug",
            f"{unit_path}.lessons",
            result,
        )
        _check_unique(
            [lesson.get("position") for lesson in lessons if isinstance(lesson, dict)],
            "lesson position",
            f"{unit_path}.lessons",
            result,
        )
        for lesson_index, lesson_data in enumerate(lessons, start=1):
            lesson_path = f"{unit_path}.lessons[{lesson_index}]"
            if not isinstance(lesson_data, dict):
                result.errors.append(f"{lesson_path}: must be an object.")
                continue
            result.summary["lessons"] += 1
            lesson_slug = _required_text(lesson_data, "slug", lesson_path, result)
            _required_text(lesson_data, "title_de", lesson_path, result)
            _required_text(lesson_data, "title_sq", lesson_path, result)
            lesson_position = _positive_position(lesson_data, lesson_path, result)
            existing_lesson = None
            if existing_unit and lesson_slug:
                existing_lesson = Lesson.objects.filter(
                    unit=existing_unit, slug=lesson_slug
                ).first()
                if existing_lesson:
                    result.warnings.append(f"{lesson_path}: existing lesson will be reused.")
                elif lesson_position and Lesson.objects.filter(
                    unit=existing_unit, position=lesson_position
                ).exists():
                    result.errors.append(
                        f"{lesson_path}.position: position {lesson_position} is already in use."
                    )

            vocabulary = _list_field(lesson_data, "vocabulary", lesson_path, result)
            result.summary["vocabulary"] += len(vocabulary)
            for vocab_index, item in enumerate(vocabulary, start=1):
                vocab_path = f"{lesson_path}.vocabulary[{vocab_index}]"
                if not isinstance(item, dict):
                    result.errors.append(f"{vocab_path}: must be an object.")
                    continue
                _positive_position(item, vocab_path, result)
                _required_text(item, "german", vocab_path, result)
                _required_text(item, "albanian", vocab_path, result)

            exercises = _list_field(lesson_data, "exercises", lesson_path, result)
            _check_unique(
                [item.get("external_id") for item in exercises if isinstance(item, dict)],
                "exercise external_id",
                f"{lesson_path}.exercises",
                result,
            )
            _check_unique(
                [item.get("position") for item in exercises if isinstance(item, dict)],
                "exercise position",
                f"{lesson_path}.exercises",
                result,
            )
            for exercise_index, item in enumerate(exercises, start=1):
                exercise_path = f"{lesson_path}.exercises[{exercise_index}]"
                if not isinstance(item, dict):
                    result.errors.append(f"{exercise_path}: must be an object.")
                    continue
                result.summary["exercises"] += 1
                external_id = _required_text(item, "external_id", exercise_path, result)
                exercise_type = _required_text(item, "type", exercise_path, result)
                exercise_position = _positive_position(item, exercise_path, result)
                _required_text(item, "instructions_sq", exercise_path, result)
                if exercise_type and exercise_type not in Exercise.Type.values:
                    result.errors.append(f"{exercise_path}.type: unsupported exercise type.")
                if existing_lesson and external_id:
                    if Exercise.objects.filter(
                        lesson=existing_lesson, external_id=external_id
                    ).exists():
                        result.errors.append(
                            f"{exercise_path}.external_id: already exists in this lesson."
                        )
                    if exercise_position and Exercise.objects.filter(
                        lesson=existing_lesson, position=exercise_position
                    ).exists():
                        result.errors.append(
                            f"{exercise_path}.position: position is already in use."
                        )

                options = _list_field(item, "options", exercise_path, result)
                accepted = _list_field(item, "accepted_answers", exercise_path, result)
                pairs = _list_field(item, "matching_pairs", exercise_path, result)
                result.summary["options"] += len(options)
                result.summary["accepted_answers"] += len(accepted)
                result.summary["matching_pairs"] += len(pairs)
                _validate_exercise_parts(
                    item,
                    exercise_type,
                    options,
                    accepted,
                    pairs,
                    exercise_path,
                    result,
                )
    return result


def _validate_exercise_parts(item, exercise_type, options, accepted, pairs, path, result):
    text_types = {
        Exercise.Type.MISSING_WORD,
        Exercise.Type.WORD_ORDER,
        Exercise.Type.LISTENING,
        Exercise.Type.SPEAKING,
        Exercise.Type.FREE_TEXT,
    }
    if exercise_type in text_types and not str(item.get("expected_answer", "")).strip():
        result.errors.append(f"{path}.expected_answer: required for this exercise type.")

    single_choice = {
        Exercise.Type.PICTURE_CHOICE,
        Exercise.Type.TRANSLATION_CHOICE,
        Exercise.Type.TRUE_FALSE,
        Exercise.Type.DIALOGUE_CHOICE,
    }
    if exercise_type in single_choice and len(options) < 2:
        result.errors.append(f"{path}.options: at least two options are required.")
    if exercise_type == Exercise.Type.TRUE_FALSE and len(options) != 2:
        result.errors.append(f"{path}.options: true/false requires exactly two options.")
    correct_count = 0
    option_positions = []
    for index, option in enumerate(options, start=1):
        option_path = f"{path}.options[{index}]"
        if not isinstance(option, dict):
            result.errors.append(f"{option_path}: must be an object.")
            continue
        option_positions.append(_positive_position(option, option_path, result))
        if option.get("is_correct") is True:
            correct_count += 1
        if not any(
            str(option.get(field, "")).strip() for field in ("text_de", "text_sq", "image_ref")
        ):
            result.errors.append(f"{option_path}: text or image_ref is required.")
        if exercise_type == Exercise.Type.PICTURE_CHOICE and not option.get("image_ref"):
            result.errors.append(f"{option_path}.image_ref: required for picture selection.")
        _validate_media_ref(option.get("image_ref"), MediaAsset.Kind.IMAGE, option_path, result)
    _check_unique(option_positions, "option position", f"{path}.options", result)
    if exercise_type in single_choice and correct_count != 1:
        result.errors.append(f"{path}.options: exactly one option must be correct.")
    if exercise_type == Exercise.Type.MULTIPLE_SELECT and correct_count < 2:
        result.errors.append(f"{path}.options: multiple select requires two correct options.")
    if exercise_type == Exercise.Type.FREE_TEXT and not accepted:
        result.errors.append(f"{path}.accepted_answers: at least one answer is required.")
    if exercise_type == Exercise.Type.MATCHING and len(pairs) < 2:
        result.errors.append(f"{path}.matching_pairs: at least two pairs are required.")

    answer_positions = []
    answer_texts = []
    for index, answer in enumerate(accepted, start=1):
        answer_path = f"{path}.accepted_answers[{index}]"
        if not isinstance(answer, dict):
            result.errors.append(f"{answer_path}: must be an object.")
            continue
        answer_positions.append(_positive_position(answer, answer_path, result))
        answer_texts.append(_required_text(answer, "text", answer_path, result))
    _check_unique(answer_positions, "accepted-answer position", f"{path}.accepted_answers", result)
    _check_unique(answer_texts, "accepted answer", f"{path}.accepted_answers", result)

    pair_positions = []
    pair_values = []
    for index, pair in enumerate(pairs, start=1):
        pair_path = f"{path}.matching_pairs[{index}]"
        if not isinstance(pair, dict):
            result.errors.append(f"{pair_path}: must be an object.")
            continue
        pair_positions.append(_positive_position(pair, pair_path, result))
        left = _required_text(pair, "left_text", pair_path, result)
        right = _required_text(pair, "right_text", pair_path, result)
        pair_values.append((left, right))
    _check_unique(pair_positions, "matching-pair position", f"{path}.matching_pairs", result)
    _check_unique(pair_values, "matching pair", f"{path}.matching_pairs", result)

    _validate_media_ref(item.get("image_ref"), MediaAsset.Kind.IMAGE, path, result)
    _validate_media_ref(item.get("audio_ref"), MediaAsset.Kind.AUDIO, path, result)
    if exercise_type == Exercise.Type.LISTENING:
        audio_ref = item.get("audio_ref")
        if not audio_ref:
            result.errors.append(f"{path}.audio_ref: required for listening exercises.")
        else:
            audio = MediaAsset.objects.filter(external_id=audio_ref).first()
            if audio and (
                not audio.is_approved or audio.language_code != MediaAsset.Language.GERMAN
            ):
                result.errors.append(
                    f"{path}.audio_ref: listening audio must be approved and German."
                )


def _validate_media_ref(reference, expected_kind, path, result):
    if not reference:
        return
    asset = MediaAsset.objects.filter(external_id=reference).first()
    if not asset:
        result.errors.append(f"{path}: media reference '{reference}' does not exist.")
    elif asset.kind != expected_kind:
        result.errors.append(f"{path}: media reference '{reference}' has the wrong type.")


@transaction.atomic
def import_course_data(data):
    validation = validate_course_import(data)
    if not validation.is_valid:
        raise CourseImportError(validation.errors)

    level_data = data["level"]
    level, _ = CEFRLevel.objects.get_or_create(
        code=level_data["code"],
        defaults={
            "title_de": level_data["title_de"],
            "title_sq": level_data["title_sq"],
            "description_sq": level_data.get("description_sq", ""),
            "position": level_data["position"],
        },
    )
    for unit_data in data.get("units", []):
        unit, _ = Unit.objects.get_or_create(
            level=level,
            slug=unit_data["slug"],
            defaults={
                "title_de": unit_data["title_de"],
                "title_sq": unit_data["title_sq"],
                "summary_sq": unit_data.get("summary_sq", ""),
                "position": unit_data["position"],
            },
        )
        for lesson_data in unit_data.get("lessons", []):
            lesson, _ = Lesson.objects.get_or_create(
                unit=unit,
                slug=lesson_data["slug"],
                defaults={
                    "title_de": lesson_data["title_de"],
                    "title_sq": lesson_data["title_sq"],
                    "objective_sq": lesson_data.get("objective_sq", ""),
                    "position": lesson_data["position"],
                },
            )
            for item in lesson_data.get("vocabulary", []):
                VocabularyEntry.objects.get_or_create(
                    lesson=lesson,
                    german=item["german"],
                    albanian=item["albanian"],
                    defaults={
                        "position": item["position"],
                        "part_of_speech": item.get("part_of_speech", ""),
                        "example_de": item.get("example_de", ""),
                        "example_sq": item.get("example_sq", ""),
                        "notes_sq": item.get("notes_sq", ""),
                    },
                )
            for item in lesson_data.get("exercises", []):
                exercise = Exercise(
                    lesson=lesson,
                    external_id=item["external_id"],
                    exercise_type=item["type"],
                    instructions_sq=item["instructions_sq"],
                    prompt_de=item.get("prompt_de", ""),
                    prompt_sq=item.get("prompt_sq", ""),
                    expected_answer=item.get("expected_answer", ""),
                    image=_asset(item.get("image_ref")),
                    audio=_asset(item.get("audio_ref")),
                    position=item["position"],
                    review_status=Exercise.ReviewStatus.DRAFT,
                )
                exercise.full_clean()
                exercise.save()
                for option in item.get("options", []):
                    ExerciseOption.objects.create(
                        exercise=exercise,
                        position=option["position"],
                        text_de=option.get("text_de", ""),
                        text_sq=option.get("text_sq", ""),
                        image=_asset(option.get("image_ref")),
                        is_correct=option.get("is_correct", False),
                    )
                for answer in item.get("accepted_answers", []):
                    ExerciseAcceptedAnswer.objects.create(
                        exercise=exercise, position=answer["position"], text=answer["text"]
                    )
                for pair in item.get("matching_pairs", []):
                    MatchingPair.objects.create(
                        exercise=exercise,
                        position=pair["position"],
                        left_text=pair["left_text"],
                        right_text=pair["right_text"],
                    )
    return validation.summary


def _asset(external_id):
    if not external_id:
        return None
    return MediaAsset.objects.get(external_id=external_id)
