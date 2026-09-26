const correctFeedback = document.querySelector("[data-auto-next]");

if (correctFeedback) {
    window.setTimeout(() => {
        window.location.assign(correctFeedback.dataset.autoNext);
    }, 1400);
}
