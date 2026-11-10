document.addEventListener("click", (event) => {
    const summary = event.target.closest(".tutor-more > summary");
    if (!summary) return;

    window.setTimeout(() => {
        const morePanel = summary.parentElement;
        if (!morePanel.open) return;
        const controls = morePanel.querySelector(".tutor-request-controls");
        controls?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
});
