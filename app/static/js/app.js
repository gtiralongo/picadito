document.addEventListener("DOMContentLoaded", function () {
    setupDarkMode();
    setupSignupForm();
    setupWhatsAppLinks();
});

/* Dark mode */
function setupDarkMode() {
    var toggle = document.getElementById("dark-toggle");
    if (!toggle) return;

    var stored = localStorage.getItem("picadito-theme");
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var theme = stored || (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
    toggle.textContent = theme === "dark" ? "☀️" : "🌙";

    toggle.addEventListener("click", function () {
        var current = document.documentElement.getAttribute("data-theme");
        var next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("picadito-theme", next);
        toggle.textContent = next === "dark" ? "☀️" : "🌙";
    });
}

/* Signup */
function setupSignupForm() {
    var form = document.getElementById("signup-form");
    if (!form) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        var eventId = form.getAttribute("data-event-id");
        var formData = new FormData(form);

        fetch("/e/" + eventId + "/participar", {
            method: "POST",
            body: formData,
        })
            .then(function (r) {
                if (!r.ok) return r.json().then(function (d) { throw d; });
                return r.json();
            })
            .then(function (data) {
                form.classList.add("hidden");
                var success = document.getElementById("signup-success");
                var linkInput = document.getElementById("edit-link");
                linkInput.value = data.edit_url;
                success.classList.remove("hidden");
            })
            .catch(function (err) {
                var errorEl = document.getElementById("signup-error");
                errorEl.textContent = err.error || "Error al anotarte";
                errorEl.classList.remove("hidden");
            });
    });
}

/* WhatsApp links */
function setupWhatsAppLinks() {
    var links = document.querySelectorAll("#whatsapp-share");
    links.forEach(function (el) {
        var shareInput = document.querySelector("#share-link");
        if (!shareInput) return;
        el.addEventListener("click", function (e) {
            e.preventDefault();
            var url = shareInput.value;
            var text = encodeURIComponent("Veni a jugar: " + url);
            window.open("https://wa.me/?text=" + text, "_blank");
        });
    });
}

/* Copy helpers */
function copyLink() {
    var input = document.getElementById("edit-link");
    if (!input) return;
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value).catch(function () {});
}

function copyShareLink() {
    var input = document.getElementById("share-link");
    if (!input) return;
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value).catch(function () {});
}
