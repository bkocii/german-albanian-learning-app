const speakingExercise = document.querySelector("[data-speaking-exercise]");

if (speakingExercise) {
    const form = speakingExercise.closest("form");
    const startButton = speakingExercise.querySelector("[data-speaking-start]");
    const stopButton = speakingExercise.querySelector("[data-speaking-stop]");
    const submitButton = speakingExercise.querySelector("[data-speaking-submit]");
    const status = speakingExercise.querySelector("[data-speaking-status]");
    const preview = speakingExercise.querySelector("[data-speaking-preview]");
    const feedback = speakingExercise.querySelector("[data-speaking-feedback]");
    const maxSeconds = Number(speakingExercise.dataset.maxSeconds) || 15;

    let recorder = null;
    let stream = null;
    let stopTimer = null;
    let recording = null;
    let recordingUrl = null;
    let chunks = [];

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
                ? "Të gjitha fjalët u njohën në rendin e pritur."
                : "Provoni përsëri nëse dëshironi ta përmirësoni përputhjen.";
            speakingExercise.querySelector("[data-speaking-next]").href = result.next_url;
            feedback.hidden = false;
            status.textContent = "Transkriptimi përfundoi.";
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
