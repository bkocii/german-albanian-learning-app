# Roadmap

## M1 — Foundation

- [x] Initialize Django project and applications
- [x] Configure environment-based settings
- [x] Create custom email-based user model
- [x] Add learner registration, email verification, and password reset
- [x] Enforce one simultaneous active device/session
- [x] Add basic account-endpoint throttling

## M2 — Course and learning engine

- [x] Model levels, units, lessons, vocabulary, and licensed assets
- [x] Model reviewed exercises and answer options
- [x] Implement the lesson player and progress tracking
- [x] Implement picture choice, translation choice, missing word, and word ordering

## M3 — Audio and speech

- [x] Add approved German lesson audio
- [x] Add listening exercises
- [x] Record browser microphone input safely
- [x] Add `faster-whisper` transcription and expected-word feedback

## M4 — First complete unit

- [x] Refine incorrect-answer reveal and explicit correct-answer progression
- [x] Define extensible exercise models and versioned JSON course format
- [x] Add staff-only JSON validation preview and draft import
- [x] Add true/false and dialogue-response learner interactions
- [x] Add free-text accepted-answer and matching-pair interactions
- [x] Add multiple-select learner interaction
- [ ] Publish A1 Unit 1: Greetings and Introductions
  - [x] Prepare the complete versioned JSON draft
  - [x] Add safe bulk image/audio ZIP import
  - [x] Add lightweight starter images and supplemental picture exercises
  - [ ] Record, review, and add the starter German listening audio
  - [ ] Complete human language review, import, learner testing, and publication
- [ ] Add unit review and completion test
- [ ] Complete mobile usability and accessibility review

## M4.5 — Lesson-scoped AI tutor

- [x] Add optional tutor help after an exercise attempt
- [x] Limit requests to the current lesson, exercise, and learner attempt
- [x] Use structured, validated Albanian responses rather than unrestricted chat output
- [x] Integrate OpenAI server-side through the pinned Python AI Toolkit release
- [x] Add rate limiting, configuration gating, usage metadata, and exchange review
- [x] Make the tutor available after speaking transcription
- [x] Handle likely `heise` transcription without teaching it as correct spelling
- [x] Require bilingual examples and reject unsupported conversation promises
- [x] Add reviewed lesson notes and approval-gated tutor examples
- [x] Prepare four A1 tutor contexts and eight examples
- [x] Refine the draft grounding and prepare a 20-case request matrix using the A1 exercises
- [x] Add learner helpful/not-helpful feedback and Admin filtering
- [x] Add an atomic deployment-wide daily tutor request ceiling
- [x] Reserve a stable, wider tutor column before and after attempts
- [x] Activate the tutor column immediately after speaking transcription
- [x] Preserve speaking results while requesting or rating tutor explanations
- [x] Route incorrect speaking results back to retry instead of the next exercise
- [x] Keep correct-answer results visible until the learner chooses to continue
- [x] Title responses with the request type or learner's custom question
- [x] Manually confirm tutor placement and transitions for typed and speaking exercises
- [x] Manually confirm the 14-request ceiling, microphone flow, retry/continue behavior, preserved
  speaking feedback, ask-again scrolling, and safe bold rendering
- [x] Review nine live greeting exchanges and separate the five request instructions
- [x] Make practice optional and omit common unsupported interactions and repeated extras locally
- [x] Add bounded repetition hints from the same learner's last three in-scope exercise exchanges
- [x] Review the enriched-demo live replies 106–114 and identify remaining length/repetition issues
- [x] Add strict structured material, exercise teaching contexts and approval controls
- [x] Provide full, existing-demo upgrade, and material-refresh imports with a ten-exercise progression
- [x] Allow related beginner language beyond the uploaded vocabulary and demonstrate response quality
- [ ] Review language, approve package-037 material and contexts, then rate the focused live comparison
- [ ] Obtain fluent German–Albanian sign-off and approve the reviewed A1 tutor examples
- [ ] Run the live provider and browser [request matrix](manual_testing_guide.md#a1-tutor-grounding-and-request-matrix)
- [ ] Decide on multi-turn lesson chat only after private-pilot evidence

## M5 — Private pilot

- [ ] Invite a small learner group
- [ ] Review completion, errors, difficult exercises, and tutor exchanges
- [ ] Measure tutor ratings, scope refusals, latency, and approximate cost
- [ ] Improve lesson grounding where low ratings reveal weak explanations
- [ ] Decide whether to expand A1 or revise the lesson engine
