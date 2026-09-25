const microphoneCheck = document.querySelector("[data-microphone-check]");

if (microphoneCheck) {
    const startButton = microphoneCheck.querySelector("[data-record-start]");
    const stopButton = microphoneCheck.querySelector("[data-record-stop]");
    const deleteButton = microphoneCheck.querySelector("[data-record-delete]");
    const status = microphoneCheck.querySelector("[data-microphone-status]");
    const preview = microphoneCheck.querySelector("[data-recording-preview]");
    const audio = microphoneCheck.querySelector("[data-recording-audio]");
    const maxSeconds = Number(microphoneCheck.dataset.maxSeconds) || 15;

    let recorder = null;
    let stream = null;
    let stopTimer = null;
    let audioUrl = null;
    let chunks = [];

    const releaseStream = () => {
        if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
        }
    };

    const clearRecording = () => {
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
            audioUrl = null;
        }
        audio.removeAttribute("src");
        audio.load();
        preview.hidden = true;
        deleteButton.hidden = true;
        status.textContent = "Regjistrimi u fshi. Gati për testim.";
    };

    const stopRecording = () => {
        if (recorder && recorder.state === "recording") {
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
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            });

            recorder.addEventListener("stop", () => {
                clearTimeout(stopTimer);
                releaseStream();
                startButton.disabled = false;
                stopButton.disabled = true;

                const recording = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                audioUrl = URL.createObjectURL(recording);
                audio.src = audioUrl;
                preview.hidden = false;
                deleteButton.hidden = false;
                status.textContent = "Regjistrimi përfundoi. Mund ta dëgjoni më poshtë.";
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
                    ? "Leja për mikrofonin nuk u dha. Lejojeni në shfletues dhe provoni përsëri."
                    : "Mikrofoni nuk mund të hapej. Kontrolloni pajisjen dhe provoni përsëri.";
        }
    });

    stopButton.addEventListener("click", stopRecording);
    deleteButton.addEventListener("click", clearRecording);

    window.addEventListener("beforeunload", () => {
        clearTimeout(stopTimer);
        stopRecording();
        releaseStream();
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
        }
    });
}
