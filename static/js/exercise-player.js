const form = document.querySelector("[data-word-order-form]");

if (form) {
    const answer = form.querySelector("[data-word-answer]");
    const input = form.querySelector("[data-word-order-input]");
    const tokens = [...form.querySelectorAll("[data-word-token]")];
    const reset = form.querySelector("[data-word-reset]");
    const selected = [];

    const renderAnswer = () => {
        answer.textContent = selected.map((button) => button.value).join(" ") ||
            "Zgjidhni fjalët sipas radhës.";
        input.value = selected.map((button) => button.value).join(" ");
    };

    tokens.forEach((button) => {
        button.addEventListener("click", () => {
            selected.push(button);
            button.disabled = true;
            renderAnswer();
        });
    });

    reset.addEventListener("click", () => {
        selected.splice(0);
        tokens.forEach((button) => {
            button.disabled = false;
        });
        renderAnswer();
    });
}
