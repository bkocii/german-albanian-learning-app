# Project State

Last updated: 24 September 2026

## Current milestone

Milestone 4 — First complete unit.

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
- Learner course catalog showing only published levels, units, and lessons
- Exercise-by-exercise lesson player with immediate answer feedback
- Learner lesson progress, completion time, and immutable exercise attempts
- Dedicated picture selection, translation choice, missing-word, and word-order interactions
- Publishing validation for expected text, picture options, and exactly one correct choice
- German audio approval metadata with approver and timestamp audit data
- Dedicated listening interaction with repeatable browser playback and typed German answers
- Click-triggered, 15-second browser microphone check with local playback and deletion
- Browser-only microphone audio that is never uploaded or stored during the check
- Temporary speaking-audio upload with format and 5 MiB size limits
- German `faster-whisper` transcription using the CPU-friendly base/int8 defaults
- Expected, recognized, matched, and missing-word feedback without pronunciation scoring
- Guaranteed temporary-file deletion and per-user transcription throttling
- Thirty-nine automated project tests

## Next task

Build and publish the reviewed A1 Unit 1: Greetings and Introductions content set.

## Constraints

- Start with one complete A1 unit: Greetings and Introductions.
- Use reviewed, original German–Albanian content.
- Do not run live, unreviewed AI exercise generation.
- Treat one active authenticated browser session as one active device for the MVP.
- Treat `faster-whisper` output as recognition feedback, not pronunciation scoring.
