# Project State

Last updated: 8 November 2026

## Current milestone

Milestone 4 — First complete unit and lesson-scoped tutor validation.

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
- Staff-only media ZIP validation, preview, and unapproved import
- Stable media IDs, licensing metadata, archive safety limits, and expiring preview files
- Four original lightweight starter illustrations with an import-ready media ZIP
- Supplemental picture-choice JSON plus German audio recording manifest and scripts
- Optional lesson-scoped AI tutor available only after an exercise attempt
- Structured Albanian tutor explanations for mistakes, correct answers, grammar, examples, and
  short lesson questions
- Server-side OpenAI access through `python-ai-toolkit[django]==1.0.0`; API credentials never reach
  the browser
- Exercise, lesson, vocabulary, learner-attempt, and approved lesson-material grounding with no
  unrestricted general chat
- Tutor support for both typed and speaking exercises after their attempt is saved
- Speech-only equivalence for `heiße`, `heisse`, and the possible Whisper transcript `heise`, while
  typed spelling still rejects `heise`
- Validated German–Albanian tutor examples and concrete follow-up tasks; unsupported promises of a
  continuing conversation are rejected
- Staff-reviewable tutor exchanges with model, duration, token, cost, and request metadata
- Tutor rate limits, question-length limits, lesson-scope enforcement, and a master off switch
- Optional reviewed lesson grammar notes, common mistakes, guidance, and approved tutor examples
- Supplemental A1 Unit 1 tutor grounding import with four lesson contexts and eight review-required
  examples
- Eighty-eight automated project tests
- Complete Windows clone-to-test onboarding guide for a fresh development machine

## Next tasks

1. Human-review the A1 Unit 1 German–Albanian course content and supplemental tutor grounding.
2. Approve only tutor examples that pass German and Albanian language review.
3. Test the tutor across all four lessons and every supported request type, including a speaking
   attempt and an out-of-scope question.
4. Run a small private pilot and inspect tutor exchanges for incorrect, vague, or unhelpful answers.
5. Add simple learner helpful/not-helpful feedback before expanding the tutor into multi-turn chat.

The next engineering task is tutor quality feedback and staff review reporting. Multi-turn lesson
conversation should be considered only after pilot evidence shows that the current one-request flow
is useful and safe.

## Constraints

- Start with one complete A1 unit: Greetings and Introductions.
- Use reviewed, original German–Albanian content.
- Do not run live, unreviewed AI exercise generation.
- Treat one active authenticated browser session as one active device for the MVP.
- Treat `faster-whisper` output as recognition feedback, not pronunciation scoring.
- Keep tutor help limited to the current lesson and require an exercise attempt first.
- Use reviewed lesson material as grounding; imported tutor examples remain unapproved by default.
- Keep the tutor optional and server-side, with no browser access to provider credentials.
