# Lesson-scoped AI tutor

## Purpose

The tutor gives an Albanian-speaking learner additional help with the exercise they just attempted.
It is not a general chatbot and it is not an autonomous agent. The application sends one controlled
request and receives one validated explanation.

The initial release supports five requests:

- explain why the learner's answer was wrong
- explain the correct answer
- explain the grammar needed for the exercise
- give another example from the same lesson
- answer a short custom question about the current lesson

The tutor becomes available only after an exercise attempt exists. This prevents it from being used
as an answer generator before the learner tries the exercise.

Speaking attempts are created asynchronously by the transcription endpoint. After transcription,
the speaking feedback now displays **Pyet tutorin**. That link reloads the current exercise with the
new attempt ID, which gives the tutor the same verified attempt context used by typed exercises.

## Request flow

```text
Learner submits tutor form
        ↓
Django authenticates the learner
        ↓
Django verifies published exercise and owned attempt
        ↓
Django validates question type, length, and rate limit
        ↓
Django atomically reserves one deployment-wide daily request
        ↓
TutorService builds limited lesson JSON
        ↓
Python AI Toolkit sends a structured OpenAI request
        ↓
Pydantic validates the response
        ↓
Django stores the exchange and usage metadata
        ↓
Validated Albanian explanation is displayed
```

The browser never receives the OpenAI API key and never contacts OpenAI directly.

## Information sent to the provider

Only information needed for the current explanation is included:

- CEFR level
- current lesson titles and learning objective
- vocabulary entries belonging to the current lesson
- current exercise type, instructions, prompts, expected answer, and options
- the learner's answer and whether it was correct
- the selected explanation request or custom question

When available, the request also includes reviewed lesson-level tutor grounding:

- Albanian grammar notes
- common learner mistakes
- tutor guidance and limits
- approved German–Albanian examples

These fields are optional. Lessons without them continue to use their objective, vocabulary,
vocabulary examples, and exercise data.

The learner's email, password, session, other lessons, other learners, and complete attempt history
are not included.

Course and learner text is serialized into labelled JSON and explicitly treated as data rather than
instructions. This reduces prompt-injection risk from content fields. It cannot provide a perfect
security guarantee, so application permissions and output validation remain mandatory.

## Response validation

The toolkit must return a `TutorResponse` containing:

- `explanation_sq`: a non-empty Albanian explanation, limited to 1,600 characters
- `german_examples`: at most two examples, each with German, Albanian, and an optional explanation
- `follow_up_sq`: an optional concrete practice task that can be done immediately
- `within_lesson_scope`: whether the question belongs to this lesson

If the model marks a request as outside scope, the application discards its generated explanation
and displays a fixed Albanian lesson-only refusal. This is safer than displaying an unrestricted
out-of-scope answer.

The response model also rejects follow-ups such as “Nëse do, mund të provojmë…” because the current
page cannot continue a conversation automatically. A follow-up must instead be an actionable task,
for example: “Plotëso: Ich ___ Arta.” Invalid structured output is sent through the toolkit's repair
path once.

The toolkit adds the response schema to the prompt, parses returned JSON, validates it with Pydantic,
and may make one repair request if the first result is malformed. A repair request is another paid
provider request, which is why usage metadata is retained.

## Stored data

Each successful exchange stores:

- learner, exercise, and attempt references
- request type and custom question
- validated explanation, examples, and follow-up
- scope decision
- model and toolkit request ID
- duration, token counts, and estimated cost when available
- optional helpful/not-helpful learner rating and the time it was last submitted
- creation time

The application also stores one aggregate daily-usage row containing the UTC date, reserved request
count, and latest update time. It contains no learner content.

Tutor exchanges are read-only in Django Admin. They can be inspected for quality, cost, abuse, and
course-improvement opportunities. Staff can filter exchanges by learner rating without editing the
learner's response. Prompt and response bodies are not written to the toolkit's log
file; toolkit file logging is disabled for this application integration.

## Installation

The application pins the stable toolkit release:

```powershell
uv sync
```

This installs `python-ai-toolkit[django]==1.0.0`, which in turn uses the official OpenAI Python SDK.
The lockfile should be committed. Upgrade the toolkit or OpenAI SDK only through a reviewed dependency
change followed by the complete test suite.

Apply the new database migration:

```powershell
uv run python manage.py migrate
```

## Configuration

The tutor is disabled by default. Add these values to the local `.env` file:

```env
TUTOR_ENABLED=True
OPENAI_API_KEY=replace-with-your-real-key
AI_TUTOR_MODEL=gpt-5.4-mini
TUTOR_RATE_ATTEMPTS=10
TUTOR_RATE_WINDOW_SECONDS=300
TUTOR_MAX_QUESTION_LENGTH=500
TUTOR_DAILY_REQUEST_LIMIT=100
```

Do not commit the real API key. `.env.example` contains only empty or safe example values.

Configuration meanings:

| Setting | Meaning |
| --- | --- |
| `TUTOR_ENABLED` | Master switch. When false, no provider request is made. |
| `OPENAI_API_KEY` | Server-side provider credential. |
| `AI_TUTOR_MODEL` | OpenAI model selected for tutor explanations. |
| `TUTOR_RATE_ATTEMPTS` | Successful exchanges allowed per learner during one window. |
| `TUTOR_RATE_WINDOW_SECONDS` | Length of the rolling rate-limit window. |
| `TUTOR_MAX_QUESTION_LENGTH` | Maximum custom-question length accepted by Django. |
| `TUTOR_DAILY_REQUEST_LIMIT` | Maximum application-level tutor requests reserved across all learners per UTC day. |

The daily counter is reserved atomically before the provider call. A provider failure keeps its
reservation because it may already have consumed billable tokens. Structured-output repair may also
make an additional provider call inside one application-level request, so this ceiling is a reliable
request safeguard rather than an exact dollar limit. Set it from measured pilot usage and cost.

Restart Django after changing `.env`:

```powershell
uv run python manage.py runserver
```

## Automated verification

Run:

```powershell
uv run python manage.py makemigrations --check
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
```

Tutor tests use a deterministic fake client. They require no API key, make no network request, and do
not incur provider cost. They verify configuration gating, attempt ownership, structured output,
out-of-scope replacement, stored usage metadata, learner and daily rate limiting, and conservative
reservation after provider failure.

## Manual test

1. Set the `.env` values and run migrations.
2. Start Django and sign in as a verified learner.
3. Open a published exercise and submit an incorrect answer.
4. Expand **Pyet tutorin për një shpjegim**.
5. Select **Pse ishte gabim?**.
6. Confirm that the response is in Albanian and refers to the current exercise.
7. Ask an unrelated custom question.
8. Confirm that the tutor refuses and redirects the learner back to the lesson.
9. Open Django Admin → Tutor exchanges.
10. Confirm that the request type, response, model, request ID, duration, tokens, and estimated cost
    are visible when the provider supplies them.
11. Select **Po, i dobishëm** and confirm the page thanks the learner and keeps that choice selected.
12. Change it to **Jo, jo i dobishëm** and confirm the latest choice is retained.
13. In Django Admin, filter Tutor exchanges by helpful and not helpful ratings.
14. Set `TUTOR_DAILY_REQUEST_LIMIT=1`, restart Django, and make one tutor request.
15. Make another tutor request and confirm it is blocked before contacting the provider.
16. Open **Admin → Tutor daily usage** and confirm today's UTC counter is 1.

For a speaking exercise, finish transcription first and click **Pyet tutorin** in the speech-feedback
panel. The application opens the same exercise with its saved speaking attempt and tutor controls.
Speech comparison treats `heiße`, `heisse`, and Whisper's possible `heise` transcript as the same
spoken word. Typed exercises still require the correct `heiße` or keyboard alternative `heisse` so
the application does not teach `heise` as correct German spelling.

To prove the off switch works, set `TUTOR_ENABLED=False`, restart Django, and repeat the flow. The page
must say the tutor is not active and no new `TutorExchange` record should be created.

## Import reviewed lesson grounding

The A1 starter content includes a supplemental file:

```text
course_content/a1/unit-01-tutor-material.json
```

It is separate from the original 24-exercise JSON so an existing database can receive improved tutor
material without duplicating exercises.

1. Open **Admin → Courses → Exercises → Import course JSON**.
2. Upload `course_content/a1/unit-01-tutor-material.json`.
3. Select **Validate and preview**.
4. Confirm the preview reports four tutor lessons, eight tutor examples, and zero exercises.
5. Confirm the import.

The importer reuses the existing A1 level, unit, and four lessons. It updates only the three tutor
note fields and creates eight tutor examples. Imported examples are deliberately unapproved.

Review them at **Admin → Courses → Lesson tutor examples**. Check the German, Albanian translation,
and explanation, then enable **Is approved** only for examples that are ready for learners. The tutor
request excludes every unapproved example.

The three lesson fields can also be reviewed from **Admin → Courses → Lessons** under the collapsed
**Lesson tutor grounding** section:

- Tutor grammar notes
- Tutor common mistakes
- Tutor guidance

Future course JSON may use the same optional structure:

```json
{
  "tutor_context": {
    "grammar_notes_sq": "...",
    "common_mistakes_sq": "...",
    "guidance_sq": "...",
    "examples": [
      {
        "position": 1,
        "german": "Ich heiße Besa.",
        "albanian": "Unë quhem Besa.",
        "explanation_sq": "Tregon formën ‘heiße’ pas ‘ich’."
      }
    ]
  }
}
```

## Current boundaries and future work

This first version intentionally does not provide:

- unrestricted general chat
- tutor access before an exercise attempt
- autonomous tools or multi-agent orchestration
- cross-lesson retrieval or a vector database
- automatic curriculum changes
- pronunciation scoring
- background or streaming responses

Possible later improvements should be driven by real learner usage. Good candidates are aggregated
rating reports, approximate-cost alerts, and conversation follow-ups within the same lesson.
