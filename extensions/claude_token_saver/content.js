/**
 * Claude Token Saver — Improve & Copy button injected into claude.ai.
 *
 * Anatomy of a click:
 *   1. Find the contenteditable input the user types into.
 *   2. Read the typed text via .innerText (DOM access — no clipboard).
 *   3. Render a small project-picker dropdown anchored to the button.
 *   4. POST {prompt, project_path} to http://127.0.0.1:7321/improve.
 *   5. Token Saver GUI opens automatically with prompt + improved version.
 *   6. User clicks the GUI's blue "Copy Prompt" button, pastes into Claude.
 *
 * The button injection uses a MutationObserver because Anthropic's SPA
 * tears down and recreates DOM nodes when navigating between conversations.
 * Re-attach whenever the input element appears.
 */

const SERVER_BASE = "http://127.0.0.1:7321";
const BUTTON_ID = "cts-improve-button";
const PICKER_ID = "cts-project-picker";
const TOAST_ID = "cts-toast";

// ── Safe DOM helpers (no innerHTML usage) ──────────────────────────

function makeEl(tag, opts) {
  const el = document.createElement(tag);
  if (!opts) return el;
  if (opts.id) el.id = opts.id;
  if (opts.cls) el.className = opts.cls;
  if (opts.text != null) el.textContent = opts.text;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) el.setAttribute(k, v);
  }
  if (opts.style) {
    for (const [k, v] of Object.entries(opts.style)) el.style[k] = v;
  }
  return el;
}

function findInput() {
  // Anthropic uses contenteditable divs with role="textbox".
  // Try multiple selectors for resilience to UI changes.
  return (
    document.querySelector('div[contenteditable="true"][role="textbox"]') ||
    document.querySelector('div[contenteditable="true"]') ||
    document.querySelector("textarea")
  );
}

function getInputText(el) {
  if (!el) return "";
  if (el.tagName === "TEXTAREA") return el.value || "";
  return (el.innerText || el.textContent || "").trim();
}

// ── Button construction ────────────────────────────────────────────

function buildButton() {
  const btn = makeEl("button", {
    id: BUTTON_ID,
    attrs: {
      type: "button",
      title: "Improve prompt with Token Saver Smart Mode",
      "aria-label": "Improve prompt",
    },
  });
  btn.appendChild(makeEl("span", { cls: "cts-icon", text: "✨" }));
  btn.appendChild(makeEl("span", { cls: "cts-label", text: "Improve" }));
  btn.addEventListener("click", onImproveClick);
  return btn;
}

function setButtonState(btn, mode) {
  // Replace children safely — no innerHTML.
  while (btn.firstChild) btn.removeChild(btn.firstChild);
  if (mode === "working") {
    btn.appendChild(makeEl("span", { cls: "cts-icon", text: "⏳" }));
    btn.appendChild(makeEl("span", { cls: "cts-label", text: "Working..." }));
  } else {
    btn.appendChild(makeEl("span", { cls: "cts-icon", text: "✨" }));
    btn.appendChild(makeEl("span", { cls: "cts-label", text: "Improve" }));
  }
}

function ensureButton() {
  if (document.getElementById(BUTTON_ID)) return;
  const input = findInput();
  if (!input) return;

  // Inject as child of the input's parent so it floats nearby.
  const parent = input.closest("form") || input.parentElement;
  if (!parent) return;
  if (!parent.style.position) parent.style.position = "relative";
  parent.appendChild(buildButton());
}

// Re-anchor on DOM mutations. Anthropic's SPA replaces nodes between
// conversations, removing our button. The observer puts it back.
const observer = new MutationObserver(() => {
  // Use rAF to coalesce rapid-fire mutations during page transitions.
  requestAnimationFrame(ensureButton);
});

function startObserver() {
  observer.observe(document.body, { childList: true, subtree: true });
  // Also check now in case input is already present.
  ensureButton();
}

// ── Server interaction ────────────────────────────────────────────

async function fetchProjects() {
  try {
    const r = await fetch(`${SERVER_BASE}/projects`, { method: "GET" });
    if (!r.ok) return [];
    const data = await r.json();
    return Array.isArray(data.projects) ? data.projects : [];
  } catch (e) {
    console.warn("[Token Saver] /projects fetch failed:", e);
    return [];
  }
}

async function postImprove(prompt, projectPath) {
  try {
    const r = await fetch(`${SERVER_BASE}/improve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        project_path: projectPath || "",
      }),
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`Server ${r.status}: ${text}`);
    }
    return await r.json();
  } catch (e) {
    console.error("[Token Saver] /improve failed:", e);
    return { error: e.message || String(e) };
  }
}

// ── Project picker popup ──────────────────────────────────────────

function closePicker() {
  const el = document.getElementById(PICKER_ID);
  if (el) el.remove();
  document.removeEventListener("click", outsideClickHandler, true);
}

function outsideClickHandler(e) {
  const picker = document.getElementById(PICKER_ID);
  if (!picker) return;
  if (!picker.contains(e.target) && e.target.id !== BUTTON_ID) {
    closePicker();
  }
}

async function openPicker(anchor, prompt) {
  closePicker();

  const projects = await fetchProjects();
  const picker = makeEl("div", { id: PICKER_ID });

  picker.appendChild(
    makeEl("div", {
      cls: "cts-picker-header",
      text: projects.length
        ? "Pick project for context:"
        : "No projects bootstrapped yet — typo fix only",
    }),
  );

  const list = makeEl("div", { cls: "cts-picker-list" });
  picker.appendChild(list);

  for (const proj of projects) {
    const row = makeEl("button", {
      cls: "cts-picker-row",
      attrs: { type: "button" },
    });
    row.appendChild(
      makeEl("div", { cls: "cts-picker-title", text: proj.name || proj.slug }),
    );
    row.appendChild(
      makeEl("div", {
        cls: "cts-picker-subtitle",
        text: proj.path || "(path unrecoverable — re-prep to fix)",
      }),
    );
    if (!proj.path) row.disabled = true;
    row.addEventListener("click", () => {
      closePicker();
      sendImprove(prompt, proj.path);
    });
    list.appendChild(row);
  }

  const none = makeEl("button", {
    cls: "cts-picker-row cts-picker-none",
    text: "None — just clean typos",
    attrs: { type: "button" },
  });
  none.addEventListener("click", () => {
    closePicker();
    sendImprove(prompt, "");
  });
  picker.appendChild(none);

  const cancel = makeEl("button", {
    cls: "cts-picker-cancel",
    text: "Cancel",
    attrs: { type: "button" },
  });
  cancel.addEventListener("click", closePicker);
  picker.appendChild(cancel);

  // Anchor near the button (fixed-position, above it).
  const rect = anchor.getBoundingClientRect();
  picker.style.position = "fixed";
  picker.style.right = `${window.innerWidth - rect.right}px`;
  picker.style.bottom = `${window.innerHeight - rect.top + 8}px`;

  document.body.appendChild(picker);

  // Close on outside click (registered after current bubble completes).
  setTimeout(() => {
    document.addEventListener("click", outsideClickHandler, true);
  }, 0);
}

// ── Core flow ─────────────────────────────────────────────────────

async function sendImprove(prompt, projectPath) {
  const btn = document.getElementById(BUTTON_ID);
  if (btn) {
    btn.disabled = true;
    setButtonState(btn, "working");
  }

  const result = await postImprove(prompt, projectPath);

  if (btn) {
    btn.disabled = false;
    setButtonState(btn, "idle");
  }

  if (result.error) {
    showToast(`Error: ${result.error}`, true);
    return;
  }

  const tokens = `${result.original_tokens}→${result.improved_tokens} tokens`;
  showToast(
    `Token Saver opened (${tokens}). Click Copy Prompt in the GUI.`,
    false,
  );
}

function showToast(message, isError) {
  const existing = document.getElementById(TOAST_ID);
  if (existing) existing.remove();

  const toast = makeEl("div", {
    id: TOAST_ID,
    cls: isError ? "cts-toast cts-toast-error" : "cts-toast",
    text: message,
  });
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("cts-toast-fade");
  }, 3500);
  setTimeout(() => {
    toast.remove();
  }, 4200);
}

async function onImproveClick(e) {
  e.preventDefault();
  e.stopPropagation();

  const input = findInput();
  const text = getInputText(input);

  if (!text.trim()) {
    showToast("Type a prompt first, then click Improve.", true);
    return;
  }

  // Verify server reachable; show clear error if Token Saver tray isn't up.
  try {
    const h = await fetch(`${SERVER_BASE}/health`, { method: "GET" });
    if (!h.ok) throw new Error(`status ${h.status}`);
  } catch (err) {
    showToast(
      "Token Saver server not reachable on 127.0.0.1:7321. Is the tray running?",
      true,
    );
    return;
  }

  const btn = document.getElementById(BUTTON_ID);
  await openPicker(btn, text);
}

// ── Boot ──────────────────────────────────────────────────────────

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startObserver);
} else {
  startObserver();
}
