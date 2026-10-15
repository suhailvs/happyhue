const cfg = document.getElementById("loginConfig").dataset;
const alertBox = document.getElementById("loginAlert");

function showError(message) {
  alertBox.textContent = message;
  alertBox.hidden = false;
}

function csrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

async function onCredential(response) {
  alertBox.hidden = true;
  try {
    const res = await fetch(cfg.loginUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify({ credential: response.credential, next: cfg.next }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.ok) {
      window.location.assign(data.redirect || "/");
    } else {
      showError(data.message || "Could not sign you in. Please try again.");
    }
  } catch (err) {
    showError("Network problem. Please try again.");
  }
}

function init() {
  if (!cfg.clientId) {
    showError("Google sign-in is not configured.");
    return;
  }
  google.accounts.id.initialize({
    client_id: cfg.clientId,
    callback: onCredential,
    auto_select: false,
  });
  google.accounts.id.renderButton(document.getElementById("googleBtn"), {
    theme: "outline",
    size: "large",
    shape: "pill",
    text: "continue_with",
    width: 320,
  });
}

// The Google script loads async, so wait for it.
let tries = 0;
const timer = setInterval(() => {
  if (window.google && google.accounts && google.accounts.id) {
    clearInterval(timer);
    init();
  } else if (++tries > 100) {
    clearInterval(timer);
    showError("Could not load Google sign-in. Check your connection and refresh.");
  }
}, 100);