# Architecture

## Applications

- `accounts`: learner identity, authentication, verification, and session policy
- `courses`: CEFR levels, units, lessons, vocabulary, exercises, and assets
- `learning`: learner attempts, answers, scores, review, and progress
- `speech`: temporary audio handling, transcription, and recognition feedback

## Technical direction

- Python 3.12 and Django
- SQLite for initial local development; PostgreSQL for production
- Responsive Django templates with lightweight JavaScript
- `faster-whisper` for local German transcription
- Temporary learner recordings deleted after processing

## Account lifecycle

- Registration creates an inactive user and sends a one-use verification link.
- Verification activates the account and records the verification time.
- Django's password-reset tokens provide the recovery workflow.
- A successful login stores the current session key on the user.
- A later login replaces that key; an older browser is signed out on its next request.
- Account POST endpoints use cache-backed, per-address short-window throttling.
- Development email is written to the console; production must configure a real mailer.

## Dependency rules

- Course definitions do not depend on learner progress.
- Learning records reference the configured custom user model and published course content.
- The learner catalog and player exclude unpublished course records and draft exercises.
- Exercise attempts are append-only learner answers; administrators can inspect but not edit them.
- A lesson is completed only after the learner has attempted every published exercise.
- Picture and translation exercises accept only an option belonging to that exercise.
- Missing-word answers use whitespace- and case-normalized comparison.
- Word-order exercises shuffle server-provided tokens and grade the reconstructed sentence.
- Speech processing returns feedback to the learning flow without storing raw audio by default.
- Provider-specific speech code must stay behind a small service interface.
- Production throttling must use a shared cache when more than one application process runs.
