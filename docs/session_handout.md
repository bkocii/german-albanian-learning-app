# Session handout — lesson-scoped AI tutor

Last updated: 8 November 2026

## Current outcome

The application has an optional AI tutor for Albanian-speaking German learners. It becomes available
only after a saved exercise attempt and receives only the current lesson, exercise, and learner
attempt. It is not a general chatbot.

The tutor works after typed and speaking attempts. Speech comparison treats `heiße`, `heisse`, and
Whisper's possible `heise` transcript as equivalent spoken words. Typed spelling still rejects
`heise`.

Each displayed response now asks **A ishte i dobishëm ky shpjegim?** The learner can choose
**Po, i dobishëm** or **Jo, jo i dobishëm**, and can change the choice later. The rating is stored on
the exchange with a timestamp. Submitting it does not contact OpenAI or add provider cost.

## Delivered behavior

| Area | Current behavior |
| --- | --- |
| Access | Tutor appears only after the learner's own saved attempt. |
| Requests | Mistake, answer, grammar, example, or short lesson question. |
| Response | Validated Albanian explanation, bilingual examples, and optional concrete practice. |
| Grounding | Exercise data, lesson vocabulary, reviewed notes, and approved examples. |
| Feedback | Helpful/not-helpful choice, timestamp, ownership check, and changeable rating. |
| Budget safety | Atomic deployment-wide request ceiling that resets each UTC day. |
| Staff review | Read-only exchanges with rating filter, model, latency, tokens, and estimated cost. |
| Safety | Server-side API key, lesson scope, rate limits, length limits, and output validation. |

The integration uses `python-ai-toolkit[django]==1.0.0` for structured OpenAI requests, parsing,
validation, repair, and usage metadata. Django owns authentication, permissions, lesson scope,
ratings, and stored exchanges.

## Installation after applying the changed files

Run from the project root in PowerShell:

```powershell
uv sync
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
```

Expected automated result: **95 tests**.

The tutor configuration remains:

```env
TUTOR_ENABLED=True
OPENAI_API_KEY=replace-with-your-real-key
AI_TUTOR_MODEL=gpt-5.4-mini
TUTOR_RATE_ATTEMPTS=10
TUTOR_RATE_WINDOW_SECONDS=300
TUTOR_MAX_QUESTION_LENGTH=500
TUTOR_DAILY_REQUEST_LIMIT=100
```

Never commit the real API key.

## Tutor-material review

Import `course_content/a1/unit-01-tutor-material.json` from **Admin → Courses → Exercises → Import
course JSON**. Preview must report four tutor lesson contexts, eight tutor examples, and zero
exercises. Imported examples are unapproved and are excluded from AI requests until a reviewer
approves them in **Admin → Courses → Lesson tutor examples**.

## Manual acceptance test

1. Submit an incorrect typed answer and request **Pse ishte gabim?**.
2. Confirm the answer refers to the current exercise and uses Albanian.
3. Confirm examples contain German, Albanian, and a useful explanation.
4. Confirm any **Provo:** instruction can be performed immediately.
5. Select **Po, i dobishëm** and confirm the thank-you message and selected button.
6. Refresh the page and confirm the saved choice remains selected.
7. Change it to **Jo, jo i dobishëm** and confirm the choice changes.
8. Sign in as another learner and confirm they cannot access or rate the first learner's exchange.
9. Complete a speaking exercise and confirm tutor access after transcription.
10. If Whisper returns `heise` for spoken `heiße`, confirm speech matching accepts it.
11. Type `heise` in a spelling exercise and confirm it remains incorrect.
12. Ask an unrelated question and confirm the fixed lesson-only refusal.
13. In **Admin → Tutor exchanges**, filter by helpful and not helpful.
14. Confirm the exchange detail remains read-only and shows the rating timestamp.
15. Disable `TUTOR_ENABLED`, restart Django, and confirm no new AI exchange is created.
16. Temporarily set `TUTOR_DAILY_REQUEST_LIMIT=1` and restart Django.
17. Make one tutor request, then confirm the second request is blocked with the daily-limit message.
18. In **Admin → Tutor daily usage**, confirm today's UTC request count is 1.

The daily count is reserved before contacting the provider. Failed provider requests keep their
reservation because they may already have incurred cost. The counter contains no learner content.

## How to improve weak responses

| Observed problem | First improvement |
| --- | --- |
| Missing fact or weak example | Improve reviewed lesson notes or approved examples. |
| Wrong tone, length, or unsupported promise | Improve prompt instructions and response validation. |
| Incorrect reviewed German or Albanian | Correct the course material and repeat human review. |
| Repeated model error with good grounding | Add a targeted validator or deterministic rule. |
| Many not-helpful ratings in one lesson | Review that lesson's exchanges before changing the global prompt. |

Good answers require both: prompt instructions control response behavior, while reviewed lesson
material controls what the tutor teaches.

## Next steps, in order

1. Complete German–Albanian review of the four lesson contexts and eight examples.
2. Test all five request types and feedback controls across all four lessons.
3. Run a small private pilot and review not-helpful exchanges by lesson and request type.
4. Compare daily request count, recorded token usage, approximate cost, and latency.
5. Set the production daily limit from measured pilot usage rather than guessing.
6. Improve reviewed grounding where ratings identify a recurring weakness.
7. Consider limited multi-turn lesson chat only if pilot evidence shows learners need it.

Multi-turn chat should remain lesson-scoped, short, attempt-aware, and explicitly terminable. It
should not become an unrestricted autonomous agent.
