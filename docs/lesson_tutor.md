# Lesson-scoped AI tutor

## Purpose

The tutor gives an Albanian-speaking learner help with the exercise they just attempted and related
beginner German. The uploaded vocabulary guides it rather than acting as a closed whitelist.
It is not a general chatbot and it is not an autonomous agent. The application sends one controlled
request and receives one validated explanation.

The initial release supports five requests:

- explain why the learner's answer was wrong
- explain the correct answer
- explain the grammar needed for the exercise
- give another example from the same lesson
- answer a short custom question about the lesson or related beginner German

The tutor becomes available only after an exercise attempt exists. This prevents it from being used
as an answer generator before the learner tries the exercise.

On desktop, the lesson reserves a wider tutor column before the attempt. It initially contains a
disabled explanation, then changes in place to active tutor controls. Correct answers do not advance
automatically: the learner chooses **Vazhdo** or uses the tutor. On narrower screens, the tutor stacks
below the exercise.

Speaking attempts are created asynchronously by the transcription endpoint. After transcription,
the page fetches the attempt-aware tutor panel and replaces the disabled sidebar in place. The
recognized-word feedback remains visible, while **Pyet tutorin** opens the now-active tutor panel.
Tutor questions and ratings update only that sidebar, so they do not erase the speaking result.
An incorrect speaking result offers **Provo përsëri**; only a correct result offers progression.
Once the sidebar activates successfully, the duplicate result-level tutor link is hidden.
When an existing response is long, **Pyet përsëri** remains collapsed; opening it scrolls the
question controls into view inside the tutor panel.

Tutor explanations may use `**text**` for emphasis. The learner page renders that limited syntax as
bold text after escaping the complete response. Other model-supplied HTML remains visible only as
escaped text and cannot become page markup.

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
- approved structured concepts, situations/dialogues, FAQ and up to two model replies matching the
  request kind; approved exercise-specific objective, situation, answer reason and grammar focus
- accepted-answer variants and matching pairs, alongside the exact saved answer and grading outcome
- German examples and practice from at most three recent in-scope exchanges for this learner and
  exercise, including previous attempts, as repetition hints only (at most six 250-character
  German strings and three 300-character tasks)

When available, the request also includes reviewed lesson-level tutor grounding:

- Albanian grammar notes
- common learner mistakes
- tutor guidance and limits
- approved German–Albanian examples

These fields are optional. Lessons without structured material continue to use their legacy notes,
objective, vocabulary and exercise data. Approved structured material supersedes the three generic
legacy lesson-note strings in the provider context, while keeping those strings in the database.
New structured JSON and exercise context are independently excluded until approved. Edits/imports
reset approval. See [package 037](tutor-material-037.md) for the schema, limits, review controls and
teaching-only updates to existing exercise IDs.

The learner's email, password, session, other exercises, other learners, earlier custom questions,
earlier explanations, and complete attempt history are not included. The repetition hints are not
conversation memory and do not let a new question refer back to an earlier explanation.

Course and learner text is serialized into labelled JSON and explicitly treated as data rather than
instructions. The selected request-type instruction is outside these JSON blocks. This reduces
prompt-injection risk from content fields. It cannot provide a perfect
security guarantee, so application permissions and output validation remain mandatory.

## Response validation

The toolkit must return a `TutorResponse` containing:

- `explanation_sq`: a non-empty Albanian explanation, limited to 1,600 characters
- `german_examples`: at most two examples, each with German, Albanian, and an optional explanation
- `follow_up_sq`: optional oral or mental self-practice, or an empty string when it adds no value
- `within_lesson_scope`: whether the request concerns the exercise or related German learning

If the model marks a request as outside scope, the application discards its generated explanation
and displays a fixed Albanian lesson-only refusal. This is safer than displaying an unrestricted
out-of-scope answer.

The response model also rejects follow-ups such as “Nëse do, mund të provojmë…” because the current
page cannot continue a conversation automatically. Practice must be an oral or mental task, for
example: “Thuaj me zë një përshëndetje që përdoret në mëngjes.” It must not disclose its solution
or promise recording, grading, or an answer control. Practice defaults to empty; rote
`Thuaje/Thuaji me mendje` lists are omitted locally. Empty practice is valid and hides the **Provo**
line. Invalid structured output is sent through the toolkit's repair path once.

After validation, local postprocessing removes German examples already present in the three recent
replies, duplicate examples within the new reply, and repeated practice. Comparison ignores case,
punctuation, and whitespace. It also omits tasks containing common Albanian write/select/fill/submit/
click/record wording. This is a conservative text filter, not complete semantic validation: paraphrases
and name-only variations still need live review. Omission preserves the main explanation and does
not add a provider call. Existing stored exchanges are not rewritten.

## Response behavior and live reviews

Package 037 builds on the first comparison below. The later enriched-demo replies 106–114 showed
improved ambiguity and word explanations. Structured model replies now demonstrate concise teaching;
exercise contexts focus each help kind, and related vocabulary/brief grammar expansion is allowed.
The supplied pack has recognition, situational, pattern, written and spoken tasks. Its data flow is
covered by automated tests; new live provider quality and dialogue formatting need review.

The 16 November review covered nine exchanges on one greeting exercise. Package 036 adds the
following request guidance; language quality still requires live review:

| Request | Intended behavior |
| --- | --- |
| Mistake | Contrast the actual wrong answer with the correct answer and explain the confusion. |
| Answer | Explain the meaning and why it fits; acknowledge a correct attempt without inventing an error. |
| Grammar | Explain one relevant pattern or learning the fixed phrase as a whole, rather than only repeating the translation. |
| Example | Demonstrate useful usage with little introduction; avoid repetition and name-only variation where possible. |
| Custom | Answer the new question first; use the original mistake only if relevant and clarify ambiguous wording instead of guessing. |

Approved material remains teaching authority. Recent practice is only an avoidance list. No new
vocabulary should be invented for novelty, and zero examples or no practice is preferable to filler.

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
TUTOR_DAILY_REQUEST_LIMIT=14
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

The committed default is 14 requests per UTC day for the initial private pilot. This is one shared
deployment limit, not a separate allowance for every learner.

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
reservation after provider failure. Regression tests also exercise bounded history isolation,
duplicate/unsupported practice omission, trusted instruction separation, and saving/rendering the
postprocessed result. Fake-provider tests do not establish live response quality.

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
panel. Confirm that the right-hand disabled state becomes active immediately, without moving below
the answer or losing the recognized-word feedback.
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

If an earlier copy was imported, the importer rejects occupied example positions. In a test
database, open each existing lesson and copy the three revised note fields from the matching JSON
lesson. Under **Lesson tutor examples**, update each row at positions 1 and 2 from the corresponding
JSON entry. Save changed examples with **Is approved** unchecked pending review. The notes take
effect when saved, so have the reviewer sign off on the wording before copying them to a live
deployment. Leave the existing exercises and attempt history in place.

Use the [four-lesson request matrix](manual_testing_guide.md#a1-tutor-grounding-and-request-matrix)
to evaluate the live provider answers after sign-off.

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
