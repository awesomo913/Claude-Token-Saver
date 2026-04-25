/**
 * Connects the extension to the Native Messaging host (local Python) when possible.
 * Messages: extension <-> { type, ... } <-> claude_native_host.py
 */
const NATIVE = "com.claudetools.bridge";
let port = null;
const nativeQueue = [];

function flushQueue() {
  if (!port) return;
  while (nativeQueue.length) {
    const payload = nativeQueue.shift();
    try {
      port.postMessage(payload);
    } catch (e) {
      console.error("[Claude Bridge] postMessage failed:", e);
      nativeQueue.unshift(payload);
      break;
    }
  }
}

function connect() {
  if (port) {
    return;
  }
  try {
    port = chrome.runtime.connectNative(NATIVE);
  } catch (e) {
    console.error("[Claude Bridge] connectNative failed:", e);
    return;
  }
  port.onMessage.addListener((msg) => {
    if (msg && msg.type === "insert_text" && msg.text) {
      forwardInsertToClaudeTab(msg.text);
    }
  });
  port.onDisconnect.addListener(() => {
    const err = chrome.runtime.lastError;
    if (err) {
      console.warn("[Claude Bridge] native port disconnected:", err.message);
    }
    port = null;
  });
  flushQueue();
}

function ensurePort() {
  if (!port) {
    connect();
  }
  return port;
}

function postToNative(payload) {
  if (port) {
    try {
      port.postMessage(payload);
    } catch (e) {
      console.warn("[Claude Bridge] post failed, queueing:", e);
      nativeQueue.push(payload);
    }
  } else {
    nativeQueue.push(payload);
    connect();
    if (!port) {
      console.warn("[Claude Bridge] no native port; is the host installed/restarted?");
    }
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "assistant_message" || message?.type === "ping" || message?.type === "log") {
    postToNative(message);
    sendResponse({ ok: true });
    return true;
  }
  if (message?.type === "request_native_port") {
    connect();
    sendResponse({ ok: !!port });
    return true;
  }
  return false;
});

chrome.action.onClicked.addListener(() => {
  postToNative({ type: "ping", source: "extension_badge" });
});

chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();

async function forwardInsertToClaudeTab(text) {
  const claude = { url: ["https://claude.ai/*", "https://*.claude.ai/*"] };
  let tabs = await chrome.tabs.query({ ...claude, active: true, lastFocusedWindow: true });
  if (!tabs.length) {
    tabs = await chrome.tabs.query(claude);
  }
  if (!tabs.length) {
    console.warn("[Claude Bridge] no claude.ai tab for insert");
    return;
  }
  const tab = tabs[0];
  if (!tab.id) return;
  try {
    await chrome.tabs.sendMessage(tab.id, { type: "insert_text", text });
  } catch (e) {
    console.error("[Claude Bridge] sendMessage to tab failed:", e);
  }
}
