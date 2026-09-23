# German–Albanian Learning App

A mobile-friendly application for Albanian-speaking learners studying German.

## Technology

- Python 3.12
- Django
- PostgreSQL for production
- faster-whisper for German speech recognition

## Local development

```powershell
uv sync
uv run python manage.py migrate
uv run python manage.py runserver

