# Project State

Last updated: 24 September 2026

## Current milestone

Milestone 2 — Course and learning engine.

## Implemented

- Initial Django project and four application modules
- Environment-based settings
- Custom email-authenticated user model
- Custom user administration
- Learner registration with email verification before login
- Login, logout, and built-in password-reset workflow
- One simultaneous active browser session per account
- Short-window throttling for account submission endpoints
- Eleven automated account tests
- Ordered CEFR level, unit, lesson, and vocabulary models
- Licensed image/audio asset records with source and attribution metadata
- Six exercise types with review state, reviewer audit data, and answer options
- Django administration screens for managing course content
- Six automated course-model tests (17 project tests total)

## Next task

Build the lesson player and learner progress model around published course content.

## Constraints

- Start with one complete A1 unit: Greetings and Introductions.
- Use reviewed, original German–Albanian content.
- Do not run live, unreviewed AI exercise generation.
- Treat one active authenticated browser session as one active device for the MVP.
- Treat `faster-whisper` output as recognition feedback, not pronunciation scoring.
