# German–Albanian Learning App

A mobile-friendly application for Albanian-speaking learners studying German.

## Technology

- Python 3.12
- Django
- PostgreSQL for production
- `faster-whisper` for German speech recognition (planned)

## Local development

```powershell
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

The development configuration reads local values from `.env`. Copy
`.env.example` to `.env` and replace the example secret key before starting.

Development email is printed in the server console. Registration requires opening the generated
verification link before the learner can sign in.

For a complete Windows guide covering installation, cloning, content/media imports, bulk
publication, learner registration, and manual testing, see
[`docs/windows_clone_setup.md`](docs/windows_clone_setup.md).

## Lesson tutor

The optional AI tutor explains an exercise only after the learner has attempted it. It is disabled
by default so a local setup cannot accidentally send course data or incur API cost. See
[`docs/lesson_tutor.md`](docs/lesson_tutor.md) for architecture, configuration, safety boundaries,
testing, and the learner flow.

For the current implementation status, installation checklist, manual acceptance test, known
boundaries, and ordered next steps, see
[`docs/session_handout.md`](docs/session_handout.md).
