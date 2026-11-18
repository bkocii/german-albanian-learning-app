# Project State

Last updated: 16 November 2026

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
- Animated correct feedback with an explicit continue action so tutor help remains available
- Extensible exercise schema with all currently defined learner engines enabled
- Stable external IDs for safe media and exercise import references
- Accepted-answer and matching-pair data models
- Versioned nested JSON format and an A1 import example
- Staff-only JSON upload with size and UTF-8 validation
- No-write validation preview with counts, warnings, and duplicate/media checks
- Single-use confirmation token and transactional draft import
- Dedicated true/false and dialogue-response learner interactions
- Choice grading, retry feedback, collapsed answer reveal, and deliberate progression for both types
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
- Speaking feedback remains visible until the learner continues or asks the tutor
- Staff-only media ZIP validation, preview, and unapproved import
- Stable media IDs, licensing metadata, archive safety limits, and expiring preview files
- Four original lightweight starter illustrations with an import-ready media ZIP
- Supplemental picture-choice JSON plus German audio recording manifest and scripts
- Optional lesson-scoped AI tutor available only after an exercise attempt
- Structured Albanian explanations for mistakes, correct answers, grammar, examples, and lesson questions
- Server-side OpenAI access through `python-ai-toolkit[django]==1.0.0`
- Tutor support for typed and speaking exercises after their attempt is saved
- Speech-only equivalence for `heiße`, `heisse`, and possible Whisper transcript `heise`
- Validated bilingual examples and immediately actionable follow-up tasks
- Reviewed lesson notes and approval-gated tutor examples in the course importer
- Staff-reviewable tutor exchanges with model, duration, token, cost, and request metadata
- Learner helpful/not-helpful ratings with ownership checks, timestamps, and Admin filtering
- Per-learner rate limits plus an atomic deployment-wide daily request ceiling
- Stable, wider desktop tutor column with responsive stacking on narrower screens
- Immediate speaking-tutor activation after transcription without losing transcript feedback
- In-place speaking tutor requests and ratings that preserve recognized-word results
- Delegated tutor form handling that remains active after sidebar replacement
- Reliable hidden-state styling for fallback controls and automatic ask-again scrolling
- Incorrect speaking results offer retry instead of progression to the next exercise
- Request-specific tutor response titles and collapsed ask-again controls below explanations
- Question-length limits, lesson-scope enforcement, and a master off switch
- One hundred and twenty-three automated project tests
- Safe rendering of tutor `**bold**` emphasis without allowing model-supplied HTML
- Manual confirmation of the daily limit, microphone flow, stable tutor placement, speaking-result
  preservation, retry/continue rules, ask-again scrolling, and safe bold rendering
- Request-specific tutor guidance for correction, meaning, grammar, examples, and custom questions
- Optional oral/mental practice with omission of common unsupported write/select/submit requests
- Repetition hints from up to three in-scope exchanges for the same learner and exercise
- Local omission of repeated German examples and practice without additional provider calls
- Custom-question guidance to answer directly and clarify ambiguous wording before guessing
- Strict schema-2 structured lesson material with concepts, dialogues, FAQ and model tutor replies
- Exercise-specific teaching contexts and explicit teaching-only updates that preserve grading/history
- Separate structured-content approval, reset on JSON edits/import and staff bulk approval actions
- Ten-exercise greetings pack with full, existing-demo upgrade, and repeatable material-refresh JSON
- Related beginner-language scope beyond a closed word list and concise request-specific teaching
- Bilingual dialogue line breaks and separate German/Albanian display

## Next tasks

The latest nine GPT-5.4 replies (106–114) used the enriched demo: ambiguity handling and word-level
explanations improved, while repetition and unnecessary length remained. Package 037 adds reusable
structured material, exercise teaching contexts, response examples and broader related-language
guidance. It passes 123 tests, including 18 new tests for import, approvals, data preservation and
all ten exercise flows. The new live teaching quality and dialogue appearance remain to be reviewed.
Use [the package-037 upgrade guide](tutor-material-037.md) for this user's existing demo lesson.

The four A1 Unit 1 tutor contexts and eight examples received a draft editorial pass on
10 November 2026. The revisions cover greetings by time of day, written spelling and speech
recognition, polite forms, and farewells. The
[request matrix](manual_testing_guide.md#a1-tutor-grounding-and-request-matrix) covers all five
request types for each lesson. All 20 request paths passed an offline Django check with a fake
provider and a stubbed speech transcript. Live answer quality, browser interaction, and human
approval across the full matrix are pending.

On 16 November, nine live exchanges for the same greeting exercise were reviewed, covering correct
and incorrect attempts and all five request types. Translations were basically correct, but the
responses repeated the same examples and practice, blurred request types, and overused the saved
mistake in a custom question. Package 036 adjusts prompts and optional-practice handling. Its six
new regression tests cover history isolation, repetition, unsupported practice, prompt/data
separation, and saved/rendered output. Later comparisons used mini and full GPT-5.4, followed by the
enriched demo in exchanges 106–114. Automated checks do not establish German–Albanian teaching
quality; use the package-037 focused comparison and learner ratings for the next review.

1. Obtain fluent German–Albanian sign-off on the A1 Unit 1 course content and revised tutor grounding.
2. Approve only tutor examples that pass review.
3. Apply package 037, import the existing-demo upgrade, review/approve its material and contexts,
   and run the focused comparison on several exercise types. Export new exchanges and rate them.
   Continue the live
   provider matrix and feedback checks, recording weak responses for grounding or prompt changes.
4. Run a small private pilot and use helpful/not-helpful ratings to improve weak lesson grounding.
5. Begin the private pilot with the validated conservative ceiling of 14 requests per UTC day, then
   review daily usage, latency, and approximate cost before changing it.

Multi-turn lesson conversation should be considered only after pilot evidence shows that the current
one-request flow is useful and safe.

## Constraints

- Start with one complete A1 unit: Greetings and Introductions.
- Use reviewed, original German–Albanian content.
- Do not run live, unreviewed AI exercise generation.
- Treat one active authenticated browser session as one active device for the MVP.
- Treat `faster-whisper` output as recognition feedback, not pronunciation scoring.
- Anchor tutor help in the current lesson/exercise, allow related beginner German, and require an
  exercise attempt first.
- Use reviewed lesson material as grounding; imported tutor examples remain unapproved by default.
- Keep the tutor optional and server-side, with no browser access to provider credentials.
