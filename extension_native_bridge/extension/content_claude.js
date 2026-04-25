/**
 * claude.ai: detect finished assistant output via the same DOM signals the
 * app already encodes in CLAUDE_SELECTORS (data-is-streaming, .font-claude-message).
 * No network interception — finalized UI text only.
 */
(function () {
  "use strict";

  const seen = new Set();

  function textFingerprint(text) {
    const t = (text || "").trim();
    if (!t) return null;
    return t.length + ":" + t.slice(0, 200);
  }

  function findAssistantText(streamingNode) {
    // Prefer canonical assistant typography inside the block
    const el =
      streamingNode.querySelector?.(".font-claude-message") ||
      streamingNode.querySelector?.('[data-testid="chat-message-content"]') ||
      streamingNode;
    return (el && el.innerText) ? el.innerText.trim() : "";
  }

  function emitAssistant(text) {
    const fp = textFingerprint(text);
    if (!fp || seen.has(fp)) return;
    seen.add(fp);
    chrome.runtime.sendMessage({
      type: "assistant_message",
      text,
      url: location.href,
      title: document.title,
      ts: new Date().toISOString()
    });
  }

  function tryCapture(streamingNode) {
    if (streamingNode.getAttribute("data-is-streaming") !== "false") return;
    const t = findAssistantText(streamingNode);
    if (t) emitAssistant(t);
  }

  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === "attributes" && m.attributeName === "data-is-streaming") {
        const el = m.target;
        if (el.getAttribute("data-is-streaming") === "false") {
          tryCapture(el);
        }
      }
    }
  });

  function observeNode(node) {
    if (!node || node.nodeType !== 1) return;
    if (node.hasAttribute("data-is-streaming")) {
      observer.observe(node, { attributes: true, attributeFilter: ["data-is-streaming"] });
      if (node.getAttribute("data-is-streaming") === "false") tryCapture(node);
    }
    node.querySelectorAll?.("[data-is-streaming]").forEach((n) => {
      observer.observe(n, { attributes: true, attributeFilter: ["data-is-streaming"] });
      if (n.getAttribute("data-is-streaming") === "false") tryCapture(n);
    });
  }

  const rootObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const n of m.addedNodes) {
        if (n.nodeType === 1) observeNode(n);
      }
    }
  });
  rootObserver.observe(document.body, { childList: true, subtree: true });
  observeNode(document.body);

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === "insert_text" && msg.text) {
      insertIntoProseMirror(msg.text);
      sendResponse({ ok: true });
    }
    return true;
  });

  function insertIntoProseMirror(text) {
    const el =
      document.querySelector('div.ProseMirror[contenteditable="true"]') ||
      document.querySelector('fieldset div[contenteditable="true"]');
    if (!el) {
      console.warn("[Claude Bridge] no ProseMirror input found");
      return;
    }
    el.focus();
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    const sel = window.getSelection();
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
    if (document.execCommand("insertText", false, (el.textContent && el.textContent.trim() ? "\n" : "") + text)) {
      return;
    }
    const prefix = (el.textContent && el.textContent.trim()) ? el.textContent + "\n" : "";
    el.textContent = prefix + text;
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text }));
  }

  // Wake/reconnect: ping native host on visibility (tab wake from discarding)
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      chrome.runtime.sendMessage({ type: "ping", source: "visibility" });
    }
  });
})();
