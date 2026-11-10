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
- 99 automated tests pass.
- `manage.py makemigrations --check`, `manage.py check`, and Ruff pass.
- Speaking and microphone behavior were manually confirmed.
- The deployment-wide tutor ceiling was manually confirmed and is set to 14 requests per UTC day.
- Tutor placement and width are stable on desktop; the panel stacks responsively on narrower screens.
- Correct typed and speaking results remain visible until the learner explicitly continues.
- Incorrect speaking results offer retry and must not offer progression.
- Tutor requests and ratings replace only the tutor panel and preserve speaking feedback.
- Opening “Pyet përsëri” scrolls the new-question controls into view.
- Tutor `**bold**` emphasis renders safely after all provider output is HTML-escaped.

Important design decisions and reasons:
- The tutor is lesson-scoped, not a general chatbot, to reduce hallucination, cost, and unrelated use.
- It becomes available only after a saved attempt so its explanation can use the learner's actual
  answer and the exact exercise context.
- Correct answers do not auto-advance because the learner needs time to read feedback or ask for an
  explanation.
- Speaking transcript/result state must stay on screen during tutor actions; therefore tutor forms
  update the sidebar in place instead of reloading the whole page.
- `heise` may match spoken `heiße` as a Whisper transcription tolerance, but typed `heise` remains a
  spelling error. Typed `heisse` is accepted as a keyboard-friendly equivalent of `heiße`.
- Reviewed lesson notes and approved examples determine what the tutor teaches; prompts determine
  response style and validation. Weak factual examples should first be fixed in grounding material.
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

Then review the documented next tasks. The recommended next step is human review of the four A1
tutor contexts and eight examples, followed by a five-request-type test matrix across all four
lessons. Do not implement multi-turn tutor chat until private-pilot evidence shows it is needed.

Explain each proposed change and why it is necessary. After implementation, provide focused manual
test steps, update the tracking documents, and prepare a changed-files ZIP.
```

## Why this prompt exists

The code alone does not explain why automatic progression was removed, why speaking uses different
`heise` tolerance from typed grading, or why tutor updates must remain confined to the sidebar. This
prompt carries those product decisions into the next session so a well-intentioned refactor does not
undo manually validated behavior.
