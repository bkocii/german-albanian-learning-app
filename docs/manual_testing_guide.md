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
