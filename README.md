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
