# Project State

Last updated: 27 September 2026

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
- Optional collapsed correct-answer reveal after mistakes
- Animated correct feedback with automatic movement to the next exercise
- Extensible exercise schema with all currently defined learner engines enabled
- Stable external IDs for safe media and exercise import references
- Accepted-answer and matching-pair data models
- Versioned nested JSON format and an A1 import example
- Staff-only JSON upload with size and UTF-8 validation
- No-write validation preview with counts, warnings, and duplicate/media checks
- Single-use confirmation token and transactional draft import
- Dedicated true/false and dialogue-response learner interactions
- Choice grading, retry feedback, collapsed answer reveal, and automatic progression for both types
- Free-text grading against a primary answer and reviewed accepted variants
- Mobile-friendly matching interaction with shuffled answers and complete-pair validation
- Collapsed matching solution reveal after an incorrect attempt
- Multiple-select grading that requires the exact complete set of correct options
- Multiple-select publication/import validation requiring meaningful correct and incorrect choices
- Complete A1 Unit 1 draft with four lessons, 20 vocabulary entries, and 24 exercises
- Automated validation of the production content file and its expected nested counts
- Atomic Unit admin actions to publish or unpublish an entire unit hierarchy
- Publication validation that prevents partial publication and records the acting administrator
- Typed answers accept standard German `ß` and keyboard-friendly `ss` as equivalent
- Correct speaking feedback remains visible for six seconds before automatic progression
- Sixty-eight automated project tests

## Next task

Human-review the A1 Unit 1 German–Albanian content, import it as drafts, test every lesson, and
publish it only after corrections are complete.

## Constraints

- Start with one complete A1 unit: Greetings and Introductions.
- Use reviewed, original German–Albanian content.
- Do not run live, unreviewed AI exercise generation.
- Treat one active authenticated browser session as one active device for the MVP.
- Treat `faster-whisper` output as recognition feedback, not pronunciation scoring.
