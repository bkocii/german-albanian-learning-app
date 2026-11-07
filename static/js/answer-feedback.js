const correctFeedback = document.querySelector("[data-auto-next]");

if (correctFeedback) {
    const autoNextTimer = window.setTimeout(() => {
        window.location.assign(correctFeedback.dataset.autoNext);
    }, 1400);

    const tutorPanel = document.querySelector("[data-tutor-panel]");
    if (tutorPanel) {
        tutorPanel.addEventListener("toggle", () => {
            if (tutorPanel.open) {
                window.clearTimeout(autoNextTimer);
            }
        });
    }
}
