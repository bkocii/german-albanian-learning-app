# Course import format

Course content should be prepared as UTF-8 JSON. JSON is used instead of CSV because lessons
contain nested vocabulary, answer options, accepted answers, matching pairs, and media references.

## Safety rules

- `schema_version` must currently be `1`.
- Every imported exercise requires a stable `external_id` using lowercase letters, numbers, and
  hyphens. It is unique inside its lesson and makes duplicate detection reliable.
- Import creates exercises as **drafts**, even if the input asks for another status.
- A reviewer must inspect and publish imported content afterward.
- Image and audio binaries are uploaded separately as media assets. JSON refers to their
  `external_id`; it does not contain base64 files.
- Re-importing an existing `external_id` will be reported during preview rather than silently
  overwriting reviewed content.

## Structure

```json
{
  "schema_version": 1,
  "level": {
    "code": "A1",
    "title_de": "Anfänger",
    "title_sq": "Fillestar",
    "position": 1
  },
  "units": [
    {
      "slug": "pershendetjet-dhe-prezantimi",
      "title_de": "Begrüßung und Vorstellung",
      "title_sq": "Përshëndetjet dhe prezantimi",
      "position": 1,
      "lessons": [
        {
          "slug": "pershendetjet-baze",
          "title_de": "Grundbegrüßungen",
          "title_sq": "Përshëndetjet bazë",
          "objective_sq": "Përdor përshëndetjet bazë.",
          "position": 1,
          "vocabulary": [],
          "exercises": []
        }
      ]
    }
  ]
}
```

## Exercise fields

Required fields are `external_id`, `type`, `position`, and `instructions_sq`.

Supported types:

- `picture_choice`
- `translation_choice`
- `missing_word`
- `word_order`
- `listening`
- `speaking`
- `true_false`
- `dialogue_choice`
- `free_text`
- `matching`
- `multiple_select`

Use `options` for choice exercises, `accepted_answers` for free-text variants, and
`matching_pairs` for matching exercises. `image_ref` and `audio_ref` contain an existing media
asset's `external_id`.

A `multiple_select` exercise requires at least three options, at least two marked
`"is_correct": true`, and at least one marked false.

See `course_content/examples/a1-unit-import-example.json` for a ready-to-copy example. Staff users
can open **Admin → Courses → Exercises → Import course JSON**, validate the file, inspect counts and
warnings, and then confirm one transactional draft import.

The first full course-content candidate is
`course_content/a1/unit-01-greetings-introductions.json`. It intentionally imports as drafts and
must receive human German–Albanian review before publication.

After importing the base unit and the starter media ZIP, import
`course_content/a1/unit-01-picture-exercises.json` to add two picture exercises. After recording,
importing, and approving the three German audio assets, import
`course_content/a1/unit-01-listening-exercises.json` to add three listening exercises.
