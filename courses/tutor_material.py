"""Bounded, strict JSON structures shared by models and the course importer."""

import json
import re

from django.core.exceptions import ValidationError

KINDS = ("explain_mistake", "explain_answer", "grammar", "example", "custom")


def text(limit, *, choices=None, key=False):
    return {"type": "text", "limit": limit, "choices": choices, "key": key}


def items(spec, limit, minimum=0):
    return {"type": "list", "item": spec, "limit": limit, "minimum": minimum}


def record(fields, required=()):
    return {"type": "object", "fields": fields, "required": required}


BILINGUAL = record(
    {"german": text(250), "albanian": text(250), "why_it_helps_sq": text(300)},
    ("german", "albanian"),
)
MATERIAL_SCHEMA = record(
    {
        "overview_sq": text(2000),
        "topics_sq": items(text(200), 12),
        "concepts": items(
            record(
                {
                    "key": text(80, key=True),
                    "title_sq": text(200),
                    "explanation_sq": text(1200),
                    "examples": items(BILINGUAL, 3),
                },
                ("key", "title_sq", "explanation_sq"),
            ),
            8,
        ),
        "dialogues": items(
            record(
                {
                    "key": text(80, key=True),
                    "situation_sq": text(500),
                    "turns": items(
                        record(
                            {
                                "speaker": text(80),
                                "german": text(250),
                                "albanian": text(250),
                            },
                            ("speaker", "german", "albanian"),
                        ),
                        6,
                        minimum=2,
                    ),
                },
                ("key", "situation_sq", "turns"),
            ),
            6,
        ),
        "faq": items(
            record(
                {
                    "key": text(80, key=True),
                    "question_sq": text(500),
                    "answer_sq": text(1200),
                },
                ("key", "question_sq", "answer_sq"),
            ),
            10,
        ),
        "response_examples": items(
            record(
                {
                    "kind": text(30, choices=KINDS),
                    "question_sq": text(500),
                    "explanation_sq": text(1600),
                    "german_examples": items(BILINGUAL, 2),
                    "follow_up_sq": text(300),
                },
                ("kind", "explanation_sq"),
            ),
            10,
        ),
    },
    ("overview_sq",),
)
EXERCISE_SCHEMA = record(
    {
        "objective_sq": text(500),
        "situation_sq": text(500),
        "answer_reason_sq": text(1000),
        "grammar_focus_sq": text(1000),
        "common_mistakes": items(
            record(
                {
                    "answer": text(500),
                    "explanation_sq": text(1000),
                },
                ("answer", "explanation_sq"),
            ),
            8,
        ),
        "material_keys": items(text(80, key=True), 16),
    }
)


def _check(value, spec, path, errors):
    if spec["type"] == "text":
        if not isinstance(value, str):
            errors.append(f"{path}: must be a string.")
        elif len(value) > spec["limit"]:
            errors.append(f"{path}: exceeds {spec['limit']} characters.")
        elif spec.get("choices") and value not in spec["choices"]:
            errors.append(f"{path}: must be one of {', '.join(spec['choices'])}.")
        elif spec.get("key") and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            errors.append(f"{path}: use a lowercase key with letters, numbers, and hyphens.")
    elif spec["type"] == "list":
        if not isinstance(value, list):
            errors.append(f"{path}: must be a list.")
            return
        if not spec["minimum"] <= len(value) <= spec["limit"]:
            errors.append(f"{path}: requires {spec['minimum']} to {spec['limit']} items.")
        for index, item in enumerate(value):
            _check(item, spec["item"], f"{path}[{index + 1}]", errors)
    else:
        if not isinstance(value, dict):
            errors.append(f"{path}: must be an object.")
            return
        for name in value.keys() - spec["fields"].keys():
            errors.append(f"{path}.{name}: unknown field.")
        for name in spec["required"]:
            if name not in value or value[name] in ("", None):
                errors.append(f"{path}.{name}: is required.")
        for name in value.keys() & spec["fields"].keys():
            _check(value[name], spec["fields"][name], f"{path}.{name}", errors)


def material_keys(material):
    return {
        item["key"]
        for section in ("concepts", "dialogues", "faq")
        for item in material.get(section, [])
        if isinstance(item, dict) and "key" in item
    }


def _validate(value, schema, limit, label):
    errors = []
    _check(value, schema if value != {} else record({}), label, errors)
    if not errors and len(json.dumps(value, ensure_ascii=False)) > limit:
        errors.append(f"{label}: exceeds the total limit of {limit} characters.")
    if errors:
        raise ValidationError(errors)


def validate_lesson_tutor_material(value):
    _validate(value, MATERIAL_SCHEMA, 24000, "tutor_material")
    keys = [
        item["key"]
        for section in ("concepts", "dialogues", "faq")
        for item in value.get(section, [])
    ]
    if len(keys) != len(set(keys)):
        raise ValidationError("tutor_material: keys must be unique across all sections.")


def validate_exercise_tutor_context(value):
    _validate(value, EXERCISE_SCHEMA, 6000, "tutor_context")


def validate_material_references(context, material):
    missing = set(context.get("material_keys", [])) - material_keys(material)
    if missing:
        raise ValidationError(
            f"tutor_context.material_keys: unknown keys: {', '.join(sorted(missing))}."
        )


def reset_changed_approval(instance, field, approval, kwargs):
    """Editing approved JSON requires another explicit review, also in Admin."""
    update_fields = kwargs.get("update_fields")
    if not instance.pk or (update_fields is not None and field not in update_fields):
        return
    previous = type(instance).objects.filter(pk=instance.pk).values_list(field, flat=True).first()
    if previous != getattr(instance, field):
        setattr(instance, approval, False)
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {approval}
