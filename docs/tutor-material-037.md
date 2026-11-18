# Structured teaching material and exercise design — package 037

16 November 2026. This package follows the full handoff plus packages 035 and 036.

## What the latest live review established

The nine new exchanges 106–114 used GPT-5.4 and the enriched demo lesson. Reply 110 now distinguished
greeting someone from wishing them a good day on leaving; reply 112 explained the parts of the
greeting. The richer material helped. However, corrections were repeated in grammar answers,
several explanations were unnecessarily long, and rote mental repetition added little value.

The next implementation makes the teaching data explicit and reusable, while keeping the existing
player, grading, speaking, ratings, and request budget. The provider model remains configurable;
keep `AI_TUTOR_MODEL=gpt-5.4` for this live comparison. This package does not edit `.env` or change
the configured daily limit.

## Apply the code

1. Stop Django. If using the standard local SQLite database, make a copy outside the project:

```powershell
Copy-Item .\db.sqlite3 ..\language-cours-before-037.sqlite3
```

2. Extract the changed-files ZIP into the project root, preserving the directory structure.
3. Run:

```powershell
uv run python manage.py migrate
uv run python manage.py makemigrations --check
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
uv run python manage.py runserver
```

Expected: 123 tests. Migration `courses.0005` adds four fields with empty/unapproved defaults; it
does not replace exercises, answers, attempts, or tutor exchanges. There are no new dependencies.

## Choose one import

Use **Admin → Courses → Exercises → Import course JSON** after applying the migration.

| Your database | File under `course_content/tutor-037/` | New exercises | Existing contexts updated |
| --- | --- | ---: | ---: |
| Already contains the three-exercise enriched demo from earlier today | `greetings-upgrade-existing-demo-v2.json` | 7 | 3 |
| Does not contain that demo lesson | `greetings-full-v2.json` | 10 | 0 |
| Already contains all ten package-037 exercises; later material revision | `greetings-material-refresh-v2.json` | 0 | 10 |

For the current user's demonstrated database, use the **upgrade** file. It targets unit slug
`tutor-demo-pershendetje-ne-situata`, lesson slug `pershendetje-dhe-urime-ne-situata`, and the three
existing `demo-a1-rich-greetings-*` external IDs. It preserves their question text, answers,
positions, publication state, primary keys, attempts, and old tutor replies. It adds `Gute Nacht`
to the vocabulary and exercises at positions 4–10. It does not modify the original course lesson
containing exercise 22.

Preview must show one structured lesson material and ten exercise tutor contexts in all three
cases. The full file also shows ten vocabulary rows, ten exercises, sixteen options, and four
accepted answers. The upgrade file shows one vocabulary row, seven exercises, ten options, and
four accepted answers. These are payload counts, not totals already in the database.

Do not import the full and upgrade files into the same lesson. Duplicate exercise IDs/positions are
reported rather than overwritten. The material-refresh file is repeatable after all ten exercises
exist. Each import resets approval for the structured records it supplies.

## Review, approve, and publish

The supplied wording is an original draft for German–Albanian review. Review the language, examples,
and answer variants before using them with learners. Local live comparison can be performed after
the staff reviewer has inspected the material.

1. In **Courses → Lessons**, open the demo lesson and expand **Lesson tutor grounding**. Inspect
   `tutor_material`. Save any edits first. Then use **Approve reviewed structured tutor material**
   on the Lessons list, or approve the unchanged JSON in a separate save.
2. In **Courses → Exercises**, filter to the demo content. Inspect the collapsed **Exercise tutor
   teaching context** on each exercise. Select the ten reviewed rows and run **Approve reviewed
   exercise tutor contexts**. This action does not publish them.
3. In **Courses → Units**, select only the demo unit and run the existing **Publish selected units
   with all lessons and exercises** action after reviewing the questions and their answers.

Imported structured lesson material and exercise contexts are unapproved by default. Approval is
separate from publishing. Editing JSON through normal model saves/Admin resets its approval, even
if the old checkbox was checked; save the revision, review it, then approve again. Bulk approval
validates selected JSON and references before approving any selected record. Empty records are
skipped. Legacy bilingual examples retain their separate existing approval workflow.

## How to structure future content

Start from `greetings-full-v2.json`, change the level/unit/lesson identity and stable exercise IDs,
and retain the field names. Use `schema_version: 2`. Schema 1 files remain supported, but new
structured fields require version 2; version 2 rejects unknown fields rather than ignoring them.

### Shared lesson material: `lesson.tutor_material`

| Field | Purpose | Limit |
| --- | --- | --- |
| `overview_sq` | What the learner should understand and use | 2,000 characters; required for a nonempty material object |
| `topics_sq` | Related topics the material explains | 12 strings, 200 characters each |
| `concepts` | Named explanations with optional bilingual illustrations | 8; each has a unique `key`, `title_sq`, `explanation_sq`, optional `examples` |
| `dialogues` | Real situations with speakers and translated turns | 6; each has `key`, `situation_sq`, 2–6 `turns` |
| `faq` | Real learner questions, ambiguity and useful direct answers | 10; each has `key`, `question_sq`, `answer_sq` |
| `response_examples` | Models of good tutor replies for each help button | 10; `kind`, `explanation_sq`, optional `question_sq`, `german_examples`, `follow_up_sq` |

Concept explanations and FAQ answers allow 1,200 characters. Dialogue turns require `speaker`,
`german`, and `albanian`; German/Albanian text is at most 250 characters each. Bilingual examples
use `german`, `albanian`, and optional `why_it_helps_sq`. Model replies use the same 1,600-character
explanation and at-most-two-example limit as tutor responses. All material together is limited to
24,000 serialized characters. The supplied package has six concepts, three dialogues, seven FAQ
entries, and six model replies; it stays well below that cap.

Keep concepts, dialogues, and FAQ keys unique across their three sections. Use lowercase words
joined by hyphens. Add a simple core explanation and a deeper optional concept for a natural
follow-up question instead of attaching a grammar lecture to every translation.

### Exercise-specific teaching: `exercise.tutor_context`

| Field | Purpose |
| --- | --- |
| `objective_sq` | The particular skill being tested |
| `situation_sq` | Who is speaking, where, when, and with what intention |
| `answer_reason_sq` | Why the recorded correct answer fits this question |
| `grammar_focus_sq` | What a grammar request should explain here |
| `common_mistakes` | Up to eight `{ "answer": "…", "explanation_sq": "…" } records |
| `material_keys` | Up to sixteen relevant concept/dialogue/FAQ keys from this lesson |

The entire exercise context is capped at 6,000 serialized characters. Keys are validated against
the supplied or already-stored lesson material. They indicate teaching priorities in the prompt;
they do not create a vector search or prohibit use of the rest of the approved lesson.

This block explains the question; it never changes grading. Put genuinely accepted written
variants in the existing `accepted_answers` field. Define meaningful wrong options so each
distinguishes a real confusion. Avoid two valid options in a single-choice question.

### Updating teaching material without reimporting questions

At lesson level, `exercise_tutor_updates` can contain objects with only `external_id` and
`tutor_context`. The exercise must already exist in that exact lesson. The update cannot contain
question text, answers, type, position, approval flags, or publication fields. This gives later
teaching revisions an explicit route without replacing grading data or learner history. Omit new
`exercises` and `vocabulary` for a material-only refresh. Existing vocabulary pairs are reused by
the older importer and their notes are not overwritten; edit those rows in Admin if revising them.

## Exercise progression in the supplied pack

| Position | Interaction | Learning purpose |
| --- | --- | --- |
| 1 | Translation choice | Recognize the morning greeting and distinguish evening/farewell |
| 2 | Dialogue choice | Wish someone a good day while leaving |
| 3 | Speaking | Produce the daytime greeting |
| 4 | Missing word | Connect `Tag` to the meaning and pattern |
| 5 | Dialogue choice | Greet a person on entering a shop |
| 6 | Dialogue choice | Return a good-day wish with `Danke, gleichfalls!` |
| 7 | Multiple select | Identify both farewell forms |
| 8 | Free text | Produce a farewell wish, including reviewed variants |
| 9 | Word order | Combine a greeting and polite address |
| 10 | Speaking | Produce the farewell wish orally |

These can be expanded into shorter lessons later. For this pilot they share one coherent body of
teaching material, so we can isolate the effect of the new context. No new audio/media is required.

## What the tutor receives

When approved, structured material supplies concepts, dialogues, FAQ and up to two model replies
matching the current help kind. It supersedes the three older generic lesson-note strings in the
provider context; those strings stay stored for legacy fallback. Approved exercise context adds
the specific goal, situation, reason and likely mistakes. Accepted answers and matching pairs are
now included alongside the exact question and saved learner attempt. Unapproved JSON is excluded.

The prompt permits related beginner German beyond the uploaded word list. It still anchors grading
facts in the exercise, requires bilingual examples, rejects unrelated requests, and keeps learner
ownership, HTML escaping, usage limits and server-side credentials. Explanations should answer the
current question once. Model replies demonstrate a suitable level of detail; they are not guaranteed
answers or conversation history. The recent-three-reply avoidance window is unchanged.

Practice defaults to empty. A useful oral self-check can be included, but the page still has no
tutor-practice answer box, recording or automatic grading. Common unsupported practice instructions
and rote `Thuaje/Thuaji me mendje` tasks are omitted locally without another provider request.
Bilingual dialogue examples preserve line breaks and display German and Albanian on separate lines.

## Live comparison and acceptance

After approval and publication, use positions 1, 2, 6 and 8 to cover different learning goals. Run
the first five cases below initially rather than all buttons on the same simple translation.

| Case | Expected useful behavior |
| --- | --- |
| Wrong `Mirëmbrëma` at position 1 → mistake help | One concise contrast and one cue; no repeated headings and summaries |
| Position 1 → grammar | Explain `guten` and `Morgen` with a useful comparison, not the same correction again |
| Custom `si thuhet diten e mire` | Distinguish greeting versus leaving, or ask a concise clarification |
| Custom `Kur dal nga dyqani, si them ditën e mirë?` | Directly answer `Schönen Tag noch!` without returning to the old mistake |
| Position 2 or 6 → example | A genuinely useful situation/short dialogue, not only another name |
| Custom `Pse ka -en te Guten Morgen?` | Brief optional explanation of the masculine accusative phrase, with translation |
| Position 8 with accepted `Einen schönen Tag noch!` | Recognize that this is an accepted written variant |
| Unrelated weather question | Fixed language-learning refusal |
| Speaking request and rating | Preserve recognized-word feedback and the existing retry/continue rules |

Rate replies and export new exchange IDs using the existing JSON command. `_lesson_context` now
includes structured material and teaching context automatically. The export reconstructs context
from the current database, not an immutable historical request snapshot: retain previous exported
files as the baseline and compare new IDs above 114. Material can increase input tokens, so review
recorded usage and latency as well as quality. Existing quota usage still counts.

## Verification and limits

123 tests pass, including 18 new checks for strict structure/reference validation, fresh/upgrade/
refresh imports, rollback, approval isolation/reset, Admin actions, context selection, and grading
and tutor access for all ten uploaded exercises. Speaking tests stub transcription; they do not
claim to establish recognition quality. Migration, Django, Ruff, and both JavaScript checks pass.
Live provider quality and browser appearance of the new dialogue formatting still need review.

Tests prove the data reaches the prompt correctly and the flow remains intact. They do not prove
that every new German–Albanian explanation is accurate or that the provider always follows the
teaching style. Keep language review and real learner ratings in the acceptance process.

## Content references

The situations and Albanian explanations are authored for this demo. Reference checks used:

- [Goethe-Institut A1: greetings, farewells, forms of address](https://lernen.goethe.de/deutschonline/A1/PDF/DE/deutschonline_Redemittel_und_Grammatik_1-18.pdf)
- [Goethe-Institut greeting/leave-taking word cards](https://www.goethe.de/prj/dlp/dlapi/v1/index.cfm?endpoint=%2Ftlm%2Fdownload&file_ID=319&tlm_ID=169)
- [Leibniz-Institut für Deutsche Sprache: adjective endings and greeting formulas](https://grammis.ids-mannheim.de/progr@mm/6895)
- [OpenAI: prompt engineering and examples](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [OpenAI: evaluating variable model output](https://developers.openai.com/api/docs/guides/evaluation-best-practices)

## Commit after review

```powershell
git add courses tutor/services.py tutor/tests.py templates/learning/_lesson_tutor_panel.html static/css/app.css course_content/tutor-037 README.md docs
git diff --cached
git commit -m "Add structured tutor materials and exercise teaching contexts"
```
