# Tutor response improvements — package 036

Date: 16 November 2026

## Why this change

Nine live tutor replies on the same `Guten Morgen` exercise were reviewed, covering correct and
incorrect attempts and all five help types. Basic translations were correct, but different buttons
gave similar explanations, examples were repeated, seven follow-ups asked for the same `Guten Tag`
translation, and one custom question was pulled back to the saved mistake. Practice also requested
typing or selection without a tutor-practice answer control.

## Resulting behavior

- Each request type has its own explicit teaching goal. Mistake help uses the actual error;
  answer help explains meaning; grammar help teaches a relevant pattern; examples focus on usage.
- Custom help is instructed to answer the current question first and clarify ambiguous intent.
- Practice is optional, oral or mental, and must not require recording or automatic checking.
- Only German examples and practice from the same learner's three most recent in-scope replies on
  this exercise are supplied as repetition hints, including replies to earlier attempts. At most
  six German strings and three task strings are included. Earlier questions and explanations are
  not sent, so this does not enable multi-turn conversation.
- Before storing a reply, a local filter omits repeated examples/tasks and common unsupported
  write/select/fill/submit/click/record wording. It does not request a replacement from the provider.
  Duplicate comparison ignores case, punctuation, and whitespace. Paraphrases and name-only
  variations are still a live-review concern.

The existing model, toolkit, schema fields, database, quota, ratings, and player UI are compatible.
This package adds no migration, dependency, course import, or environment setting. Old exchange
records stay available for comparison; new requests use the revised behavior.

## Apply on Windows

1. Stop the development server with `Ctrl+C`.
2. Extract the changed-files ZIP into the existing project root (the folder with `manage.py`),
   retaining its `tutor/` and `docs/` paths and replacing the included files.
3. Run from that folder in PowerShell:

```powershell
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
uv run python manage.py runserver
```

Expected automated result: 105 tests. No new migration is required.

## Verification performed

- Full suite: 105 tests pass (99 baseline plus six regression tests).
- Migration check: no changes detected. Django system check and Ruff pass.
- Both tutor-panel and speaking-exercise JavaScript syntax checks pass.
- Offline replay of the nine uploaded replies through a fake provider preserved their explanations,
  omitted all nine unsupported follow-ups, and omitted two repeated examples. It made no provider
  network requests and did not use or modify the learner's live database.

The replay checks deterministic postprocessing; it does not test how the live model responds to
the revised prompt. Natural language quality and instruction-following still require live retesting.

## Retest and start ratings

Use the [targeted package-036 comparison](manual_testing_guide.md#package-036-compare-the-first-greeting-exercise-again).
Repeat the greeting exercise first, then speaking and a grammar-focused exercise. Rate the new
responses and export that day's exchanges using the same JSON export command. Keep the old records
for comparison. Existing requests still count toward the 14-request UTC daily ceiling, so split the
comparison across days if necessary; this update does not reset usage.

For ambiguous custom questions, judge whether the tutor answers the intended question or seeks
clarification rather than guessing. Clarification is a single response, not a new conversation mode;
write the next custom question in full if asking again.

## Commit after manual confirmation

```powershell
git add tutor/services.py tutor/tests.py README.md docs
git commit -m "Improve tutor response guidance and practice variety"
```

Review `git diff --cached` before committing if there are unrelated local documentation changes.
