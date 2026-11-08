# Session handout — lesson-scoped AI tutor

Last updated: 8 November 2026

## Outcome

The application now has an optional AI tutor for Albanian-speaking German learners. It appears only
after the learner has attempted the current exercise. It explains that attempt with the current
lesson's material; it is not a general chatbot and it cannot teach unrelated topics.

The tutor also works after a speaking exercise finishes transcription. In speech comparison,
`heiße`, the keyboard form `heisse`, and Whisper's possible transcript `heise` are treated as the
same spoken word. Typed exercises still reject `heise`, because it is not correct German spelling.

## What was delivered

| Area | Delivered behavior |
| --- | --- |
| Learner access | Tutor controls appear only after a saved typed or speaking attempt. |
| Requests | Explain the mistake, correct answer, grammar, another example, or a short lesson question. |
| Scope | Current lesson, exercise, vocabulary, and the learner's own attempt only. |
| Responses | Validated Albanian explanation, up to two bilingual examples, and an optional concrete task. |
| Grounding | Lesson objective, vocabulary, exercise data, reviewed notes, and approved tutor examples. |
| Safety | Server-side API key, ownership checks, rate limits, length limits, scope refusal, and output validation. |
| Operations | Read-only exchange records include model, request ID, latency, tokens, and estimated cost when available. |
| Content | Four A1 lesson contexts and eight tutor examples are ready for human review. |

The integration uses `python-ai-toolkit[django]==1.0.0`. The toolkit centralizes the structured
OpenAI request, schema parsing, validation, one repair attempt for malformed output, and usage
metadata. Django remains responsible for authentication, permissions, lesson scope, rate limiting,
database records, and what the learner is allowed to see.

## Files and responsibilities

- `docs/lesson_tutor.md` — architecture, data handling, configuration, and testing reference
- `tutor/` — request validation, service, stored exchanges, views, URLs, admin, and tests
- `templates/learning/exercise_player.html` — learner tutor controls and rendered response
- `courses/models.py` — lesson tutor notes and approval-gated tutor examples
- `courses/importer.py` — optional `tutor_context` import and validation
- `course_content/a1/unit-01-tutor-material.json` — supplemental A1 grounding without duplicate exercises
- `.env.example` and `config/settings.py` — disabled-by-default tutor configuration

## Installation and activation

From the project root in PowerShell:

```powershell
uv sync
uv run python manage.py migrate
```

Add the following to the local `.env` file:

```env
TUTOR_ENABLED=True
OPENAI_API_KEY=replace-with-your-real-key
AI_TUTOR_MODEL=gpt-5.4-mini
TUTOR_RATE_ATTEMPTS=10
TUTOR_RATE_WINDOW_SECONDS=300
TUTOR_MAX_QUESTION_LENGTH=500
```

Never commit the real API key. Restart Django after changing `.env`:

```powershell
uv run python manage.py runserver
```

## Import and review the lesson material

The supplemental tutor file updates the four existing A1 Unit 1 lessons without importing duplicate
exercises.

1. Open **Admin → Courses → Exercises → Import course JSON**.
2. Upload `course_content/a1/unit-01-tutor-material.json`.
3. Select **Validate and preview**.
4. Confirm **4 tutor lesson contexts**, **8 tutor examples**, and **0 exercises**.
5. Confirm the import.
6. Open **Admin → Courses → Lesson tutor examples**.
7. Review German, Albanian, and the explanation; approve only material ready for learners.
8. Review each lesson's grammar notes, common mistakes, and guidance in the lesson admin.

Imported examples are intentionally unapproved. Unapproved examples are never sent to the model.

## Acceptance test

Run the automated checks first:

```powershell
uv run python manage.py makemigrations --check
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
```

Expected test count at this handoff: **88 tests**.

Then test manually as a verified learner:

1. Submit an incorrect typed answer and confirm the tutor becomes available only afterward.
2. Request **Pse ishte gabim?** and verify that the explanation refers to this exercise.
3. Test the correct-answer, grammar, and example request types.
4. Ask a short custom question about the lesson; verify a relevant Albanian answer.
5. Ask an unrelated question; verify the fixed lesson-only refusal.
6. Complete a speaking exercise, wait for transcription, and use **Pyet tutorin** from its feedback.
7. Speak `Ich heiße …`; if Whisper returns `heise`, verify speech matching still accepts it.
8. Type `heise` in a typed spelling exercise and verify it remains incorrect.
9. Verify examples show German, Albanian, and a useful explanation instead of generic filler.
10. Verify any follow-up is immediately actionable and does not promise a future conversation.
11. Open **Admin → Tutor exchanges** and inspect stored request and usage metadata.
12. Set `TUTOR_ENABLED=False`, restart, and verify no provider request or exchange is created.

## Current boundaries

- One validated request and response at a time; there is no continuing chat thread.
- No tutor access before an attempt.
- No cross-lesson retrieval, vector database, web search, autonomous tools, or curriculum changes.
- No pronunciation score; speech recognition only compares expected and recognized words.
- AI output can still be imperfect. Reviewed grounding, validation, and staff inspection reduce risk
  but do not replace a private pilot and language review.
- Provider usage can incur cost. Rate limits exist, but a deployment-wide budget ceiling has not yet
  been implemented.

## Next steps, in order

### 1. Finish content review

Have a fluent German–Albanian reviewer check the four lesson contexts and eight examples. Approve
only verified examples. This produces better tutor answers more reliably than prompt changes alone:
the request tells the model how to answer, while reviewed lesson material gives it what to teach.

### 2. Run the four-lesson tutor acceptance pass

Test every request type in every lesson, including at least one incorrect answer, one speaking
attempt, and one out-of-scope question. Record examples of vague, incorrect, or repetitive output.

### 3. Add tutor quality feedback

Add **Helpful** and **Not helpful** controls to each response, store the rating on the exchange, and
provide an admin filter/report. This is the recommended next engineering task because it turns pilot
opinions into evidence and identifies which lesson grounding needs improvement.

### 4. Add budget protection

Define a daily deployment-wide cost/request ceiling in addition to the existing per-learner rate
limit. Display or log a clear reason when the ceiling pauses tutor requests.

### 5. Run a small private pilot

Measure helpfulness, wrong-answer rate, refusal behavior, latency, repeated questions, and cost.
Update lesson material before changing the general prompt whenever the problem is missing or
lesson-specific knowledge.

### 6. Decide whether multi-turn chat is justified

Only after pilot evidence should the interface offer a continuing lesson conversation. If added, it
should remain inside the current lesson, have a short turn limit, preserve attempt context, and use a
clear **End conversation** action. It should not become an unrestricted agent.

## Decision rule for improving responses

| Problem observed | First fix |
| --- | --- |
| Missing lesson fact or weak example | Improve reviewed lesson notes/examples. |
| Wrong tone, excessive length, or unsupported promise | Improve request instructions and response validation. |
| Incorrect German or Albanian in approved material | Correct the material and repeat human review. |
| Repeated model error despite good grounding | Add a targeted validator or deterministic application rule. |
| Learners need a real follow-up exchange | Evaluate limited multi-turn chat after pilot evidence. |

Answer quality comes from both inputs: strong request instructions control format and behavior,
while reviewed exercise material controls factual and pedagogical quality.
