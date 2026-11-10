# German–Albanian Learning App

A mobile-friendly Django application for Albanian-speaking learners studying German. The current
MVP contains a reviewed A1 course flow, typed/listening/speaking exercises, local German speech
recognition, bulk course and media import, and an optional lesson-scoped AI tutor.

## Current capabilities

- Email registration, verification, password reset, and one active browser session per learner
- Published course catalog, lesson progress, immutable attempts, and explicit learner progression
- Picture, choice, missing-word, word-order, listening, speaking, true/false, dialogue, free-text,
  matching, and multiple-select interactions
- German transcription with `faster-whisper`; recordings are temporary and deleted after processing
- Versioned JSON course import and validation plus safe ZIP media import
- Lesson-scoped Albanian tutor explanations after a saved typed or speaking attempt
- Tutor grounding from the current exercise, lesson vocabulary, reviewed notes, and approved examples
- Tutor ratings, usage metadata, per-learner throttling, and a deployment-wide daily ceiling

## Technology

- Python 3.12 and Django 6
- SQLite for local development; PostgreSQL/`psycopg` for production
- `uv` for dependency and virtual-environment management
- `faster-whisper` using CPU `int8` defaults for local German transcription
- `python-ai-toolkit[django]==1.0.0` for structured OpenAI tutor requests
- Responsive server-rendered templates with lightweight JavaScript

## Local setup

From the project root in PowerShell:

```powershell
Copy-Item .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py test
uv run python manage.py runserver
```

Replace `DJANGO_SECRET_KEY` in `.env` with a private development value. Do not commit `.env`, API
keys, the local database, virtual environments, or learner recordings.

Open `http://127.0.0.1:8000/`. Development email is printed in the server console. Registration
requires opening the generated verification link before the learner can sign in.

The first speech transcription can take longer because the selected Whisper model may need to be
downloaded and loaded. The default `base`/CPU/`int8` configuration is intended for the current 8 GB
development laptop.

## Optional lesson tutor

The tutor is disabled by default. It becomes available only after the learner has submitted the
current exercise; it is not a general chatbot. Provider credentials stay on the server, and only
lesson/exercise/attempt context is sent. To enable it locally, set these values in `.env`:

```env
TUTOR_ENABLED=True
OPENAI_API_KEY=replace-with-your-real-key
AI_TUTOR_MODEL=gpt-5.4-mini
TUTOR_RATE_ATTEMPTS=10
TUTOR_RATE_WINDOW_SECONDS=300
TUTOR_MAX_QUESTION_LENGTH=500
TUTOR_DAILY_REQUEST_LIMIT=14
```

Correct answers do not automatically leave the result screen: the learner can continue or ask the
tutor. Incorrect speaking attempts offer retry instead of progression. Tutor requests and ratings
replace only the tutor panel, preserving speech transcription feedback. AI text is escaped before a
narrow `**bold**` formatter is applied, so provider-supplied HTML cannot render.

See [`docs/lesson_tutor.md`](docs/lesson_tutor.md) for the request flow, scope, validation, data
handling, and detailed testing instructions.

## Content administration

- Course JSON format: [`docs/course_import_format.md`](docs/course_import_format.md)
- Media ZIP format: [`docs/media_import_format.md`](docs/media_import_format.md)
- Manual testing: [`docs/manual_testing_guide.md`](docs/manual_testing_guide.md)

Imported course exercises remain drafts until reviewed. Imported tutor examples are unapproved and
are excluded from AI grounding until a staff reviewer explicitly approves them.

## Verification

```powershell
uv run python manage.py makemigrations --check
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
```

The current expected result is **99 automated tests**.

## Project handoff

- Current implementation and constraints: [`docs/project_state.md`](docs/project_state.md)
- Completed milestones and future work: [`docs/roadmap.md`](docs/roadmap.md)
- Tutor-focused continuation guide: [`docs/session_handout.md`](docs/session_handout.md)
- Ready-to-copy next-chat prompt: [`docs/new_session_prompt.md`](docs/new_session_prompt.md)
- Architecture and dependency rules: [`docs/architecture.md`](docs/architecture.md)

The next development session should start with `docs/session_handout.md`, then confirm the current
state with the verification commands above before making changes.
