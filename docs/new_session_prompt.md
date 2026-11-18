# Prompt for the next development session

Copy the prompt below into a new chat after uploading the latest full-project handoff ZIP.

```text
Continue development of the German–Albanian Learning App from the attached full-project handoff ZIP.

Before changing code, read these files in order:
1. README.md
2. docs/session_handout.md
3. docs/project_state.md
4. docs/roadmap.md
5. docs/lesson_tutor.md
6. docs/manual_testing_guide.md
7. docs/architecture.md

Treat this full-project ZIP as authoritative. Earlier packages numbered 025–033 were incremental
changed-files packages and should not be applied again.

Current verified baseline:
- 123 automated tests pass (105 before package 037 plus 18 structured-material regression tests).
- `manage.py makemigrations --check`, `manage.py check`, and Ruff pass.
- Both JavaScript syntax checks pass.
- Speaking and microphone behavior were manually confirmed.
- The deployment-wide tutor ceiling was manually confirmed and is set to 14 requests per UTC day.
- Tutor placement and width are stable on desktop; the panel stacks responsively on narrower screens.
- Correct typed and speaking results remain visible until the learner explicitly continues.
- Incorrect speaking results offer retry and must not offer progression.
- Tutor requests and ratings replace only the tutor panel and preserve speaking feedback.
- Opening “Pyet përsëri” scrolls the new-question controls into view.
- Tutor `**bold**` emphasis renders safely after all provider output is HTML-escaped.
- Latest live review: exchanges 106–114 with GPT-5.4 and the enriched demo improved ambiguity and
  word explanations but still repeated corrections. Package 037 needs its focused live comparison.
- Schema 2 adds structured lesson material, exercise teaching contexts, and teaching-only updates.
  Import requires review/approval; editing JSON resets approval. Legacy schema 1 still works.
- The package includes full, existing-demo upgrade and material-refresh JSON. This user already
  imported the earlier enriched demo, so use the upgrade route in docs/tutor-material-037.md.
- Migration courses.0005 adds JSON/approval fields. Existing grading and attempt history remain intact.
- Only examples/tasks from up to three in-scope replies for the same learner and exercise are used
  as repetition hints. Earlier questions/explanations are not sent; this is not conversation memory.

Important design decisions and reasons:
- Tutor help stays focused on the exercise and related beginner German. It can explain beyond the
  uploaded vocabulary, but it is not unrestricted general chat.
- It becomes available only after a saved attempt so its explanation can use the learner's actual
  answer and the exact exercise context.
- Correct answers do not auto-advance because the learner needs time to read feedback or ask for an
  explanation.
- Speaking transcript/result state must stay on screen during tutor actions; therefore tutor forms
  update the sidebar in place instead of reloading the whole page.
- `heise` may match spoken `heiße` as a Whisper transcription tolerance, but typed `heise` remains a
  spelling error. Typed `heisse` is accepted as a keyboard-friendly equivalent of `heiße`.
- Approved structured material supplies concepts, dialogues, FAQ and up to two model replies for
  the current help kind, superseding older generic note strings in the provider context. Approved
  exercise context supplies objective, situation, answer reasons and likely mistakes. Exact exercise
  answers and accepted variants remain grading authority. New language content needs real review.
- The daily request counter reserves before the provider call and retains failed reservations,
  because the external request may already have incurred cost.
- Python AI Toolkit 1.0.0 remains the provider abstraction. Django continues to own authentication,
  lesson scope, persistence, ratings, and budgets.

Do not reintroduce automatic progression, unrestricted chat, browser-side API keys, unescaped model
HTML, or a continue action after an incorrect speaking result.

First run and report this baseline:
uv sync
uv run python manage.py makemigrations --check
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
node --check static/js/speaking-exercise.js
node --check static/js/tutor-panel.js

First read docs/tutor-material-037.md and follow its current upgrade, approval, authoring contract,
and focused live comparison. Keep AI_TUTOR_MODEL=gpt-5.4 for that comparison. The four original A1
tutor contexts and eight examples still have draft editorial revisions. Their 20 request paths
passed an earlier offline check with a fake provider and stubbed speech. Obtain fluent
German–Albanian sign-off, approve the reviewed examples in Admin, and run the live request matrix in
docs/manual_testing_guide.md across all four lessons. Use the Admin update steps in
docs/lesson_tutor.md if the earlier grounding is already imported. Do not implement multi-turn tutor
chat until private-pilot evidence shows it is needed.

Explain each proposed change and why it is necessary. After implementation, provide focused manual
test steps, update the tracking documents, and prepare a changed-files ZIP.
```

## Why this prompt exists

The code alone does not explain why automatic progression was removed, why speaking uses different
`heise` tolerance from typed grading, or why tutor updates must remain confined to the sidebar. This
prompt carries those product decisions into the next session so a well-intentioned refactor does not
undo manually validated behavior.
