const speakingExercise = document.querySelector("[data-speaking-exercise]");

if (speakingExercise) {
    const form = speakingExercise.closest("form");
    const startButton = speakingExercise.querySelector("[data-speaking-start]");
    const stopButton = speakingExercise.querySelector("[data-speaking-stop]");
    const submitButton = speakingExercise.querySelector("[data-speaking-submit]");
    const status = speakingExercise.querySelector("[data-speaking-status]");
    const preview = speakingExercise.querySelector("[data-speaking-preview]");
    const feedback = speakingExercise.querySelector("[data-speaking-feedback]");
    const nextLink = speakingExercise.querySelector("[data-speaking-next]");
    const tutorLink = speakingExercise.querySelector("[data-speaking-tutor]");
    const maxSeconds = Number(speakingExercise.dataset.maxSeconds) || 15;

    let recorder = null;
    let stream = null;
    let stopTimer = null;
    let recording = null;
    let recordingUrl = null;
    let chunks = [];
    let tutorFallbackUrl = "";

    const focusTutor = () => {
        const tutorPanel = document.querySelector("[data-tutor-panel]");
        if (!tutorPanel) return;
        tutorPanel.open = true;
        tutorPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const activateTutor = async (tutorUrl) => {
        const currentColumn = document.querySelector(".tutor-column");
        if (!currentColumn) return false;
        try {
            const response = await fetch(tutorUrl, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) return false;
            const page = new DOMParser().parseFromString(await response.text(), "text/html");
            const activeColumn = page.querySelector(".tutor-column");
            if (!activeColumn) return false;
            currentColumn.replaceWith(activeColumn);
            window.history.replaceState({}, "", tutorUrl);
            return true;
        } catch (_error) {
            return false;
        }
    };

    document.addEventListener("submit", async (event) => {
        const tutorForm = event.target.closest(".tutor-column form");
        if (!tutorForm) return;
        event.preventDefault();
        const column = tutorForm.closest(".tutor-column");
        const submitter = event.submitter;
        if (submitter) submitter.disabled = true;
        try {
            const formData = new FormData(tutorForm);
            if (submitter?.name) formData.set(submitter.name, submitter.value);
            const response = await fetch(tutorForm.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error("Kërkesa e tutorit dështoi.");
            const page = new DOMParser().parseFromString(await response.text(), "text/html");
            const updatedColumn = page.querySelector(".tutor-column");
            if (!updatedColumn) throw new Error("Përgjigjja e tutorit nuk mund të shfaqet.");
            column.replaceWith(updatedColumn);
            const responseUrl = response.url.split("#", 1)[0];
            window.history.replaceState({}, "", `${responseUrl}#lesson-tutor`);
            focusTutor();
        } catch (error) {
            status.textContent = error.message;
            if (submitter) submitter.disabled = false;
        }
    });

    tutorLink.addEventListener("click", (event) => {
        event.preventDefault();
        if (document.querySelector("[data-tutor-panel]")) {
            focusTutor();
        } else if (tutorFallbackUrl) {
            window.location.assign(tutorFallbackUrl);
        }
    });

    const releaseStream = () => {
        if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
        }
    };

    const clearRecording = () => {
        if (recordingUrl) {
            URL.revokeObjectURL(recordingUrl);
            recordingUrl = null;
        }
        recording = null;
        preview.hidden = true;
        preview.removeAttribute("src");
        submitButton.disabled = true;
        feedback.hidden = true;
    };

    const stopRecording = () => {
        if (recorder?.state === "recording") {
            recorder.stop();
        }
    };

    startButton.addEventListener("click", async () => {
        if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
            status.textContent = "Ky shfletues nuk e mbështet regjistrimin e mikrofonit.";
            return;
        }
        clearRecording();
        status.textContent = "Po kërkohet leja për mikrofonin…";
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true },
                video: false,
            });
            recorder = new MediaRecorder(stream);
            chunks = [];
            recorder.addEventListener("dataavailable", (event) => {
                if (event.data.size) chunks.push(event.data);
            });
            recorder.addEventListener("stop", () => {
                clearTimeout(stopTimer);
                releaseStream();
                startButton.disabled = false;
                stopButton.disabled = true;
                recording = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                recordingUrl = URL.createObjectURL(recording);
                preview.src = recordingUrl;
                preview.hidden = false;
                submitButton.disabled = false;
                status.textContent = "Regjistrimi është gati. Dëgjojeni ose dërgojeni për kontroll.";
            });
            recorder.start();
            startButton.disabled = true;
            stopButton.disabled = false;
            status.textContent = `Po regjistrohet — maksimumi ${maxSeconds} sekonda.`;
            stopTimer = window.setTimeout(stopRecording, maxSeconds * 1000);
        } catch (error) {
            releaseStream();
            startButton.disabled = false;
            stopButton.disabled = true;
            status.textContent =
                error.name === "NotAllowedError"
                    ? "Leja për mikrofonin nuk u dha."
                    : "Mikrofoni nuk mund të hapej. Provoni përsëri.";
        }
    });

    stopButton.addEventListener("click", stopRecording);

    submitButton.addEventListener("click", async () => {
        if (!recording) return;
        submitButton.disabled = true;
        startButton.disabled = true;
        status.textContent = "Po transkriptohet regjistrimi…";
        const body = new FormData();
        const extension = recording.type.includes("ogg") ? "ogg" :
            recording.type.includes("mp4") ? "m4a" : "webm";
        body.append("audio", recording, `recording.${extension}`);
        try {
            const response = await fetch(speakingExercise.dataset.endpoint, {
                method: "POST",
                headers: { "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value },
                body,
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Transkriptimi dështoi.");
            speakingExercise.querySelector("[data-speaking-transcript]").textContent = result.transcript;
            speakingExercise.querySelector("[data-speaking-matched]").textContent =
                result.matched_words.join(", ") || "—";
            speakingExercise.querySelector("[data-speaking-missing]").textContent =
                result.missing_words.join(", ") || "—";
            speakingExercise.querySelector("[data-speaking-unexpected]").textContent =
                result.unexpected_words.join(", ") || "—";
            speakingExercise.querySelector("[data-speaking-result]").textContent = result.is_match
                ? "Saktë! Të gjitha fjalët u njohën në rendin e pritur."
                : "Jo e saktë. Provoni përsëri nëse dëshironi ta përmirësoni përputhjen.";
            nextLink.href = result.is_match ? result.next_url : result.retry_url;
            nextLink.textContent = result.is_match ? "Vazhdo" : "Provo përsëri";
            tutorFallbackUrl = result.tutor_url;
            tutorLink.href = "#lesson-tutor";
            tutorLink.hidden = false;
            feedback.hidden = false;
            const tutorActivated = await activateTutor(result.tutor_url);
            tutorLink.hidden = tutorActivated;
            status.textContent = "Transkriptimi përfundoi. Mund të vazhdoni ose të pyesni tutorin.";
            if (result.is_match) {
                feedback.classList.add("success-burst");
            }
        } catch (error) {
            status.textContent = error.message;
            submitButton.disabled = false;
        } finally {
            startButton.disabled = false;
        }
    });

    window.addEventListener("beforeunload", () => {
        clearTimeout(stopTimer);
        releaseStream();
        if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    });
}
