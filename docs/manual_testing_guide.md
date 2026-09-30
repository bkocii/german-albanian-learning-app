# Manual Testing Guide

## Foundation and custom user model

Run from the project root in PowerShell:

```powershell
uv sync
uv run python manage.py makemigrations --check
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py test
```

Create an administrator using an email address:

```powershell
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Then open `http://127.0.0.1:8000/admin/`, sign in with the email address, and
confirm that Users can be added and edited without a username field.

Expected result:

- All commands complete without errors.
- `createsuperuser` asks for an email address, not a username.
- The administration user list displays email, name, staff status, and active status.

## Learner registration and verification

Start the server:

```powershell
uv run python manage.py runserver
```

1. Open `http://127.0.0.1:8000/` and select **Fillo tani**.
2. Register with a test email and password.
3. Confirm that the account cannot sign in before verification.
4. Copy the `/accounts/verify/...` link printed in the server console and open it.
5. Sign in and confirm that the dashboard opens.

## Password reset

1. Sign out and select **Keni harruar fjalëkalimin?**.
2. Submit the verified account's email.
3. Copy the reset link printed in the server console.
4. Set a new password and sign in with it.

## One active session

1. Sign in using one normal browser window.
2. Sign in to the same account from a different browser or private window.
3. Refresh the dashboard in the first browser.

Expected result: the first browser returns to login and explains that the account was opened
on another device; the second browser remains signed in.

## Account throttling

Repeated account-form submissions from one address are temporarily blocked after the configured
limit. Development defaults are 10 submissions in 300 seconds. Restarting the local server clears
the in-memory development counter.

## Course content administration

After applying migrations, sign in at `http://127.0.0.1:8000/admin/` and confirm that the
**Courses** section contains CEFR levels, units, lessons, vocabulary entries, media assets,
exercises, and exercise options.

Create content in this order:

1. Create level A1.
2. Create Unit 1, then add its lessons.
3. Add vocabulary entries and licensed media records.
4. Create exercises as drafts and add answer options where required.
5. Change an exercise to reviewed or published only after selecting a reviewer and review time.

Expected result: duplicate positions inside the same parent are rejected, media fields accept only
the appropriate image/audio asset type, and reviewed content retains its reviewer audit data.

## Lesson player and progress

Create a small published example in the administration site:

1. Publish level **A1**, Unit 1, and Lesson 1.
2. Add a translation-choice exercise with status **Published**, a reviewer, and review time.
3. Add two options: `Përshëndetje` marked correct and `Mirupafshim` marked incorrect.
4. Sign in as a learner, open **Paneli**, select **Hap kurset**, and start the lesson.
5. Submit the incorrect answer, retry, and then submit the correct answer.
6. Return to the catalog and confirm the lesson shows **Përfunduar**.
7. In the administration site, inspect **Lesson progress** and **Exercise attempts**.

Expected result: only published content appears, both attempts remain recorded, feedback appears
after each answer, and the final exercise completes the lesson. Draft exercises return 404 if their
address is entered directly.

## Four core exercise interactions

Add the following exercises to the published test lesson. Positions must be unique.

### Picture selection — position 2

First create two **Media assets** with kind **Image**. Upload one greeting image and one unrelated
image. For each asset, enter creator, license name, acquisition date, and Albanian alternative text.

Create an exercise with type **Picture selection**, instruction `Zgjidh figurën që tregon një
përshëndetje.` and position 2. Add two image options and mark exactly one correct. Set reviewer,
review time, and status **Published**.

### Missing word — position 3

Create an exercise with type **Missing word**:

- Instruction: `Plotëso fjalën që mungon.`
- German prompt: `Guten ____!`
- Expected answer: `Morgen`
- Position: 3
- Review status: **Published**, with reviewer and review time

No answer options are required.

### Word ordering — position 4

Create an exercise with type **Word ordering**:

- Instruction: `Vendosi fjalët në rendin e saktë.`
- Expected answer: `Ich heiße Arta`
- Position: 4
- Review status: **Published**, with reviewer and review time

No answer options are required.

Open the lesson as a learner and verify:

1. Picture selection displays image cards and grades the chosen image.
2. Translation choice displays text options and rejects an option from another exercise.
3. Missing word accepts `morgen` with different capitalization and surrounding spaces.
4. Word ordering displays shuffled word buttons, supports **Fillo përsëri**, and reconstructs the
   selected sentence.
5. The lesson becomes **Përfunduar** only after every published exercise has an attempt.

Publishing checks: a picture option without an image, a published text exercise without its
expected answer, or a published choice exercise without exactly one correct option must be rejected.

## Approved audio and listening exercise

For local testing, record yourself saying `Guten Morgen` using Windows Sound Recorder. Production
course audio should later be reviewed for clear native or near-native German pronunciation.

Create **Courses → Media assets → Add**:

- Title: `Guten Morgen audio`
- Kind: **Audio**
- Language code: **German**
- File: the recorded audio file
- Creator: your name or `Course team`
- License name: `Original work`
- Acquired on: today's date
- Is approved: checked
- Approved by: your administrator account
- Approved at: **Today / Now**

Create a new exercise using the next available position:

- Exercise type: **Listening**
- Instructions sq: `Dëgjo dhe shkruaj atë që dëgjon.`
- Expected answer: `Guten Morgen`
- Audio: **Guten Morgen audio**
- Review status: **Published**
- Reviewed by: your administrator account
- Reviewed at: **Today / Now**

As a learner, open the lesson and confirm that the audio controls appear, playback can be repeated,
and `guten morgen` is accepted as correct. The attempt must appear under **Exercise attempts**.

Validation checks:

1. An approved asset without **Approved by** or **Approved at** is rejected.
2. A listening exercise cannot be published with an unapproved audio asset.
3. A listening exercise cannot be published with Albanian or language-neutral audio.
4. A published listening exercise requires both an audio asset and expected answer.

## Browser microphone check

Sign in as a learner and open **Paneli → Testo mikrofonin**. Use Chrome or Edge at
`http://127.0.0.1:8000/`; browsers permit microphone access on localhost during development.

1. Confirm the browser does not request microphone permission when the page first opens.
2. Select **Fillo regjistrimin** and allow microphone access when prompted.
3. Speak for a few seconds and select **Ndalo**.
4. Play the recording under **Dëgjo regjistrimin** and confirm your voice is audible.
5. Select **Fshi regjistrimin** and confirm the playback control disappears.
6. Record again and leave or refresh the page; confirm the old recording is no longer available.
7. Start another recording without selecting **Ndalo**; confirm it stops automatically after 15
   seconds.

Permission-denial test: block microphone access in the browser and try again. The page should show
an Albanian explanation and remain usable. No recording from this check is uploaded to Django or
written to disk.

## Speaking transcription with faster-whisper

Run `uv sync` after installing this change. The first real transcription downloads the configured
`base` Whisper model and can take several minutes; later requests reuse the local model cache.

Create a published exercise using the next available lesson position:

- Exercise type: **Speaking**
- Instructions sq: `Thuaje fjalinë në gjermanisht.`
- German prompt: `Guten Morgen`
- Expected answer: `Guten Morgen`
- Review status: **Published**
- Reviewed by: your administrator account
- Reviewed at: **Today / Now**

No options or course audio are required. As a learner:

1. Open the speaking exercise and select **Fillo regjistrimin**.
2. Say `Guten Morgen`, stop, and play the local preview.
3. Select **Dërgo për kontroll** and wait for the first model download/transcription.
4. Confirm the result shows the recognized text, matched words, and any missing words.
5. Confirm the page says this is recognition feedback rather than a pronunciation score.
6. Open **Admin → Learning → Exercise attempts** and confirm the recognized text was recorded.
7. Record a different phrase and confirm missing/unexpected word feedback is shown.

Safety checks:

- Files larger than 5 MiB or outside WebM, Ogg, WAV, and MP4 audio are rejected.
- Empty transcription asks the learner to retry and creates no attempt.
- Temporary audio is deleted after both successful and failed transcription.
- More than 10 transcription requests in 5 minutes from one learner returns a temporary limit.

## Answer feedback and automatic progression

Use a lesson containing at least two published exercises.

1. Submit an incorrect answer and confirm the message says **Jo e saktë.**
2. Confirm the correct answer is not immediately visible.
3. Open **Shiko përgjigjen e saktë** and confirm the correct text or image appears.
4. Close the section, select **Provo përsëri**, and submit the correct answer.
5. Confirm **Saktë!** appears with a short animation.
6. Do not click anything; confirm the next exercise opens automatically after about 1.4 seconds.
7. On the final exercise, confirm a correct answer automatically returns to the course catalog.
8. Confirm **Vazhdo tani** or **Përfundo tani** still works if selected before the automatic move.
9. Repeat with a speaking exercise: exact recognized text should automatically advance, while a
   non-matching transcription should remain on the feedback screen.

With the operating-system reduced-motion setting enabled, the animation should be disabled while
automatic progression continues to work.

## Extensible exercise and import-data foundation

Apply migration `courses.0003`. In **Admin → Courses → Exercises**, confirm the type selector now
includes True or false, Dialogue response, Free-text translation, Matching pairs, and Multiple
select.

1. Create a new dialogue-response exercise as a draft and give it external ID
   `a1-u1-dialogue-001`. Confirm it saves.
2. Keep it as a draft until you add at least two options with exactly one marked correct. Dialogue
   and true/false exercises can now be published; the other three new types remain draft-only.
3. Create a free-text draft and add two accepted answers, for example `Guten Tag` and `Guten Tag!`.
4. Create a matching draft and add `Hallo — Përshëndetje` and `Danke — Faleminderit` pairs.
5. Try to reuse the same exercise external ID inside the same lesson. Confirm it is rejected.
6. Open `course_content/examples/a1-unit-import-example.json` and confirm it is valid JSON and uses
   nested vocabulary, options, accepted answers, and matching pairs.

This step adds the shared data foundation. Free text, matching, and multiple select must remain
drafts until their learner interfaces are delivered.

## True/false and dialogue-response interactions

Test the two types separately in an existing published lesson. Use unique positions.

### True/false

1. In **Admin → Courses → Exercises**, create an exercise with type **True or false**.
2. Enter instruction `Zgjidh e vërtetë ose e gabuar.` and German prompt
   `Hallo do të thotë Përshëndetje.`
3. Add exactly two options: `Richtig / E vërtetë` marked correct and `Falsch / E gabuar`
   unmarked.
4. Set a reviewer, review time, and status **Published**, then save.
5. As a learner, open the lesson and confirm two large option cards appear.
6. Select **Falsch** and submit. Confirm **Jo e saktë.** appears and the correct answer remains
   collapsed until **Shiko përgjigjen e saktë** is opened.
7. Select **Provo përsëri**, choose **Richtig**, and submit. Confirm **Saktë!** appears and the
   player advances automatically.
8. In **Admin → Learning → Exercise attempts**, confirm both attempts and their selected options
   were recorded.

### Dialogue response

1. Create another exercise with type **Dialogue response**.
2. Enter instruction `Zgjidh përgjigjen e duhur.` and German prompt
   `Guten Morgen! Wie heißen Sie?`
3. Add `Ich heiße Arta.` marked correct and `Gute Nacht.` unmarked.
4. Set a reviewer, review time, and status **Published**, then save.
5. As a learner, confirm the German prompt appears as a dialogue bubble and both responses appear
   as selectable response cards.
6. Submit `Gute Nacht.` and confirm the collapsed correct-answer reveal contains
   `Ich heiße Arta.`
7. Retry with `Ich heiße Arta.` and confirm automatic progression.
8. Confirm the incorrect and correct attempts are both retained in the administration site.

Validation checks: publishing either type with fewer than two active options or with zero/multiple
correct options must be rejected. A draft may still be saved while options are being prepared.

## Free-text and matching interactions

Test each type separately in an existing published lesson, using unique positions.

### Free text with accepted variants

1. In **Admin → Courses → Exercises**, create an exercise with type
   **Free-text translation**.
2. Enter instruction `Përkthe në gjermanisht.`, Albanian prompt `Mirëdita`, and expected answer
   `Guten Tag`.
3. Under **Accepted answers**, add position 1 with `Guten Tag!`.
4. Set a reviewer, review time, and status **Published**, then save.
5. As a learner, enter `  guten tag!  ` with lowercase letters and surrounding spaces.
6. Confirm it is accepted, **Saktë!** appears, and automatic progression occurs.
7. Retry or create another attempt with `Guten Abend`. Confirm **Jo e saktë.** appears and
   **Shiko përgjigjen e saktë** remains collapsed until selected.
8. Open the reveal and confirm it shows the primary answer `Guten Tag`.
9. In **Admin → Learning → Exercise attempts**, confirm the exact submitted text was retained.

Validation check: a reviewed or published free-text exercise requires an expected answer and at
least one accepted-answer row. A draft may be saved while these are being prepared.

### Matching pairs

1. Create an exercise with type **Matching pairs** and instruction
   `Bashko fjalët me përkthimet.`
2. Add these matching pairs with unique positions:
   - Position 1: `Hallo` — `Përshëndetje`
   - Position 2: `Danke` — `Faleminderit`
3. Set a reviewer, review time, and status **Published**, then save.
4. As a learner, confirm each German word has a translation dropdown and that both Albanian
   answers are available for every row.
5. Leave one dropdown unselected and submit. The browser should prevent submission. If submitted
   without browser validation, the page must show **Plotësoni të gjitha çiftet.** and create no
   attempt.
6. Deliberately swap the two answers. Confirm **Jo e saktë.** appears.
7. Open **Shiko përgjigjen e saktë** and confirm both correct pairs appear only after opening it.
8. Retry with both correct pairs and confirm automatic progression.
9. In Exercise attempts, confirm the stored answer lists both submitted pair mappings.

Validation check: a reviewed or published matching exercise requires at least two matching-pair
rows. On a narrow browser window, confirm each word and dropdown stack vertically without
horizontal scrolling.

## Multiple-select interaction

Create a new exercise in an existing published lesson:

- Type: **Multiple select**
- Instruction: `Zgjidh të gjitha përshëndetjet.`
- Unique position
- Reviewer and review time
- Status: **Published**

Add these options:

1. `Hallo` — correct
2. `Guten Tag` — correct
3. `Auf Wiedersehen` — incorrect

Test as a learner:

1. Confirm all three options appear as checkboxes and the instruction says to select every correct
   answer.
2. Submit without selecting anything. Confirm **Zgjidhni të paktën një përgjigje.** appears and no
   attempt is created.
3. Select only `Hallo`. Confirm **Jo e saktë.** appears because the correct set is incomplete.
4. Open **Shiko përgjigjen e saktë** and confirm both `Hallo` and `Guten Tag` are shown while
   `Auf Wiedersehen` is omitted.
5. Retry and select all three options. Confirm the result is still incorrect because one selected
   option is wrong.
6. Retry and select exactly `Hallo` and `Guten Tag`. Confirm **Saktë!** and automatic progression.
7. In **Admin → Learning → Exercise attempts**, confirm the selected option text is retained in
   each attempt.

Publication validation tests:

- Two options only: rejected because at least three are required.
- Three options with only one correct: rejected because at least two correct options are required.
- Three options all marked correct: rejected because at least one incorrect option is required.
- The same invalid structures in imported JSON must fail during preview and write nothing.

A draft can be saved while its options are still being prepared.

## JSON course import preview and draft import

Make a copy of `course_content/examples/a1-unit-import-example.json`. If A1 already contains a unit
at position 1, change the copied unit's slug to `import-test`, its titles to `Import test`, and its
position to an unused value such as 99. This avoids deliberately colliding with existing content.

1. Sign in as a staff administrator and open **Courses → Exercises**.
2. Select **Import course JSON** in the upper-right object tools.
3. Upload the copied JSON and select **Validate and preview**.
4. Confirm the preview reports 1 unit, 1 lesson, 1 vocabulary entry, 3 exercises, 2 options, 2
   accepted answers, and 2 matching pairs.
5. Before confirming, open Exercises in another tab and verify no imported external IDs exist.
6. Return to the preview and select **Import as drafts** once.
7. Confirm the success message says 3 draft exercises were imported.
8. Open the imported unit, lesson, vocabulary, exercises, options, accepted answers, and matching
   pairs. Confirm every exercise status is **Draft** and the hierarchy is unpublished.
9. Upload the same file again. Preview must report existing exercise external IDs or occupied
   positions and must not create duplicates.

Validation tests:

- Remove a required `external_id`: preview shows its exact JSON path and writes nothing.
- Change `schema_version` to 2: preview rejects it.
- Give two exercises the same position: preview reports the duplicate.
- Add `"image_ref": "missing-image"`: preview reports the missing media asset.
- Upload malformed JSON: the form reports that valid UTF-8 JSON is required.
- Sign in as a non-staff learner and enter the importer address directly: access is denied.
- Leave a valid preview unused for more than 15 minutes: confirmation requires a new preview.

The file limit defaults to 1 MiB. Media binaries are not embedded in JSON; upload them separately
and reference their external IDs.

## A1 Unit 1 content review and import

Use `course_content/a1/unit-01-greetings-introductions.json`. It contains:

- 1 unit and 4 lessons
- 20 vocabulary entries
- 24 exercises
- 29 choice options
- 5 accepted free-text variants
- 12 matching pairs

The unit intentionally has no picture or listening exercises yet because approved image and audio
assets must be added separately. It includes speaking exercises that use the existing
`faster-whisper` workflow.

### 1. Check for earlier test-import collisions

The earlier example JSON used the same A1 unit, first lesson, and one external exercise ID. In
**Admin → Courses → Units**, look for `Përshëndetjet dhe prezantimi`.

- If it is only disposable content imported while testing the importer, delete that unit before
  continuing. Django shows every related object that will be deleted; read that list before
  confirming.
- If it contains manual content you want to keep, do not delete it. Upload the full file only for
  validation, inspect the collision errors, and decide how the existing content should be merged
  before importing.
- Do not change production external IDs merely to bypass a collision; they are intended to remain
  stable.

### 2. Preview and import

1. Open **Admin → Courses → Exercises → Import course JSON**.
2. Upload `course_content/a1/unit-01-greetings-introductions.json`.
3. Select **Validate and preview**.
4. Confirm the preview reports exactly the counts listed above and no errors.
5. Confirm no records were created merely by previewing.
6. Select **Import as drafts** once.
7. Confirm all four lessons and all 24 exercises exist, remain **Draft**, and the level, unit, and
   lessons remain unpublished.

### 3. Human language review

Review one lesson at a time with a fluent German–Albanian reviewer. For every vocabulary entry and
exercise, check spelling, umlauts, punctuation, formal/informal address, natural Albanian wording,
and whether every marked answer is unambiguous. Record corrections directly in Admin while content
is still draft.

Pay particular attention to:

- `du` versus formal `Sie`
- `Wie geht es dir?` versus `Wie geht es Ihnen?`
- `Tschüss` versus formal `Auf Wiedersehen`
- accepted punctuation variants in free-text exercises
- speaking expected answers, which should be short and unambiguous for transcription

### 4. Test before publication

For each lesson, temporarily publish only that lesson's reviewed exercises, then publish its parent
lesson, unit, and A1 level. Sign in as a learner and complete every exercise, deliberately testing
at least one incorrect answer before the correct answer. Confirm attempt history, collapsed answer
reveals, automatic progression, lesson completion, mobile layout, and speaking feedback.

If a problem is found, return the affected exercise to **Draft**, correct it, repeat review, and
test it again. Do not publish the complete unit until all four lessons pass this review.
