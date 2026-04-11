"""Chrome DevTools Protocol (CDP) client for browser automation.

Replaces pyautogui blind-clicking with direct DOM manipulation.
Connects to Chrome/Edge via their remote debugging port and:
- Finds DOM elements by CSS selector (no guessing pixel coordinates)
- Types into input fields directly (no clipboard hijacking)
- Clicks buttons by selector (no blind coordinate math)
- Reads response text from specific elements (no Ctrl+A full page capture)
- Detects AI completion by polling DOM changes (no hardcoded waits)

Requirements:
- Chrome/Edge launched with --remote-debugging-port=9222
- websocket-client package (already in requirements.txt)

Each browser window has its own CDP target (tab). We find the right tab
by matching the URL pattern from the AIProfile.
"""

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    import urllib.request
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_CDP_PORT = 9222
CDP_TIMEOUT = 10  # seconds for individual CDP commands
COMPLETION_POLL_INTERVAL = 1.5  # seconds between completion checks
MAX_COMPLETION_WAIT = 300  # max seconds to wait for AI response

# Per-corner CDP ports for isolated Chrome instances
CDP_CORNER_PORTS = {
    "top-left": 9222,
    "top-right": 9223,
    "bottom-left": 9224,
    "bottom-right": 9225,
}


def get_cdp_port_for_corner(corner: str) -> int:
    """Get the CDP port assigned to a screen corner."""
    return CDP_CORNER_PORTS.get(corner, DEFAULT_CDP_PORT)


@dataclass
class CDPSelectors:
    """CSS selectors for interacting with a specific AI chat site.

    Each AI site has different DOM structure. This captures the selectors
    needed to automate that specific site.
    """
    # Input area — where to type the prompt
    input_selector: str = "textarea"
    # Send button (if Enter doesn't work)
    send_button_selector: str = ""
    # Use Enter key to send (most sites)
    send_with_enter: bool = True
    # Response containers — the AI's messages
    response_selector: str = ".message"
    # The last/latest response specifically
    last_response_selector: str = ".message:last-child"
    # Loading/generating indicator (present while AI is typing)
    loading_selector: str = ""
    # Stop button (present while generating, disappears when done)
    stop_button_selector: str = ""
    # Selector for response text content within a response container
    response_text_selector: str = ""
    # Whether input is a contenteditable div (vs textarea)
    input_is_contenteditable: bool = False
    # Additional JS to run after page load (e.g., dismiss popups)
    init_script: str = ""


# ── Per-site selector presets ─────────────────────────────────────

GEMINI_SELECTORS = CDPSelectors(
    input_selector='.ql-editor[contenteditable="true"], div.input-area-container [contenteditable="true"], .text-input-field_textarea textarea',
    input_is_contenteditable=True,
    send_with_enter=True,
    send_button_selector='button[aria-label="Send message"], button.send-button, button[mattooltip="Send"]',
    response_selector='.response-container .markdown, .model-response-text .markdown, message-content .markdown',
    last_response_selector='.response-container:last-of-type .markdown, .conversation-container > :last-child .markdown',
    loading_selector='.loading-indicator, .response-container mat-spinner, [aria-label="Loading"]',
    stop_button_selector='button[aria-label="Stop response"], button.stop-button',
)

CHATGPT_SELECTORS = CDPSelectors(
    input_selector='#prompt-textarea, div[contenteditable="true"][id="prompt-textarea"]',
    input_is_contenteditable=True,
    send_with_enter=True,
    # send button may not appear until text is typed — Enter is primary send method
    send_button_selector='button[data-testid="send-button"], button[data-testid="composer-send-button"], button[aria-label="Send prompt"], button[aria-label="Send message"]',
    response_selector='div[data-message-author-role="assistant"] .markdown, div[data-message-author-role="assistant"]',
    last_response_selector='div[data-message-author-role="assistant"]:last-of-type .markdown, div[data-message-author-role="assistant"]:last-of-type',
    # .result-streaming class on the response div is the most reliable completion signal
    loading_selector='.result-streaming, button[data-testid="stop-button"]',
    stop_button_selector='button[data-testid="stop-button"], button[aria-label="Stop generating"]',
)

CLAUDE_SELECTORS = CDPSelectors(
    input_selector='div.ProseMirror[contenteditable="true"], div[contenteditable="true"].ProseMirror, fieldset div[contenteditable="true"]',
    input_is_contenteditable=True,
    send_with_enter=True,
    send_button_selector='button[aria-label="Send Message"], button[aria-label="Send message"]',
    response_selector='div[data-is-streaming] .font-claude-message, .font-claude-message, [data-testid="chat-message-content"]',
    last_response_selector='[data-is-streaming]:last-of-type .font-claude-message, .font-claude-message:last-of-type',
    # data-is-streaming="true" flips to "false" when done — most reliable signal
    loading_selector='div[data-is-streaming="true"]',
    stop_button_selector='button[aria-label="Stop Response"], button[aria-label="Stop response"]',
)

OPENROUTER_SELECTORS = CDPSelectors(
    input_selector='textarea[placeholder*="message"], textarea[placeholder*="Message"], textarea',
    input_is_contenteditable=False,
    send_with_enter=False,
    send_button_selector='button[aria-label="Send message"], button[type="submit"], button[aria-label="Send"]',
    response_selector='.prose, .markdown-body, [class*="message"] .prose',
    last_response_selector='.prose:last-of-type',
    loading_selector='[class*="animate-pulse"], [class*="animate-spin"]',
    stop_button_selector='button[aria-label="Stop"], button[aria-label="Stop generating"]',
)

OLLAMA_WEBUI_SELECTORS = CDPSelectors(
    input_selector='textarea#chat-textarea, textarea[placeholder*="message"], #chat-textarea',
    input_is_contenteditable=False,
    send_with_enter=True,
    send_button_selector='button#send-message-button, button[type="submit"]',
    response_selector='.chat-assistant .prose, [data-role="assistant"] .prose, .assistant-message',
    last_response_selector='.chat-assistant:last-of-type .prose, [data-role="assistant"]:last-of-type .prose',
    loading_selector='[class*="generating"], .chat-assistant .animate-pulse',
    stop_button_selector='button#stop-response-button, button[aria-label="Stop"]',
)

COPILOT_SELECTORS = CDPSelectors(
    input_selector='textarea[placeholder*="message"], #searchbox textarea, textarea',
    input_is_contenteditable=False,
    send_with_enter=True,
    send_button_selector='button[aria-label="Submit"], button[type="submit"]',
    response_selector='.ac-container .ac-textBlock, [class*="response"] p',
    last_response_selector='.ac-container:last-of-type .ac-textBlock',
    loading_selector='[class*="typing"], [class*="loading"]',
    stop_button_selector='button[aria-label="Stop responding"]',
)

# Map profile names to selector presets
SELECTOR_PRESETS: dict[str, CDPSelectors] = {
    "Gemini": GEMINI_SELECTORS,
    "ChatGPT": CHATGPT_SELECTORS,
    "Claude": CLAUDE_SELECTORS,
    "OpenRouter": OPENROUTER_SELECTORS,
    "Ollama Web UI": OLLAMA_WEBUI_SELECTORS,
    "Copilot": COPILOT_SELECTORS,
}


def get_selectors_for_profile(profile_name: str) -> CDPSelectors:
    """Get CDP selectors for a given AI profile name."""
    return SELECTOR_PRESETS.get(profile_name, CDPSelectors())


# ── CDP Connection ────────────────────────────────────────────────

class CDPConnection:
    """WebSocket connection to a single Chrome/Edge tab via CDP.

    Handles:
    - Connecting to the debugging WebSocket
    - Sending commands and receiving results
    - Evaluating JavaScript in the page context
    - Finding elements and interacting with them
    """

    def __init__(self, ws_url: str, timeout: float = CDP_TIMEOUT) -> None:
        self._ws_url = ws_url
        self._timeout = timeout
        self._ws: Optional[websocket.WebSocket] = None
        self._msg_id = 0
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Open WebSocket connection to the CDP target."""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=self._timeout,
                suppress_origin=True,
            )
            logger.info("CDP connected: %s", self._ws_url[:80])
            return True
        except Exception as e:
            logger.error("CDP connection failed: %s", e)
            return False

    def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._ws.connected

    def send_command(self, method: str, params: Optional[dict] = None) -> dict:
        """Send a CDP command and wait for the result."""
        if not self.is_connected:
            raise RuntimeError("CDP not connected")

        with self._lock:
            self._msg_id += 1
            msg_id = self._msg_id

            message = {"id": msg_id, "method": method}
            if params:
                message["params"] = params

            self._ws.send(json.dumps(message))

            # Read responses until we get our result
            deadline = time.time() + self._timeout
            while time.time() < deadline:
                try:
                    self._ws.settimeout(max(0.1, deadline - time.time()))
                    raw = self._ws.recv()
                    response = json.loads(raw)

                    if response.get("id") == msg_id:
                        if "error" in response:
                            error = response["error"]
                            raise RuntimeError(
                                f"CDP error {error.get('code')}: {error.get('message')}"
                            )
                        return response.get("result", {})

                    # Not our response — it's an event, ignore it
                except websocket.WebSocketTimeoutException:
                    continue

            raise TimeoutError(f"CDP command timed out: {method}")

    def evaluate_js(self, expression: str, await_promise: bool = False) -> Any:
        """Evaluate JavaScript in the page and return the result.

        This is the workhorse — most interactions go through JS evaluation.
        """
        params = {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        }
        result = self.send_command("Runtime.evaluate", params)

        if "exceptionDetails" in result:
            exc = result["exceptionDetails"]
            text = exc.get("text", "")
            desc = exc.get("exception", {}).get("description", "")
            raise RuntimeError(f"JS error: {text} {desc}")

        value = result.get("result", {}).get("value")
        return value

    def find_element(self, selector: str) -> bool:
        """Check if a DOM element matching the selector exists."""
        js = f"!!document.querySelector({json.dumps(selector)})"
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False

    def get_element_text(self, selector: str) -> str:
        """Get the text content of an element."""
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            return el ? el.innerText || el.textContent || '' : '';
        }})()
        """
        try:
            result = self.evaluate_js(js)
            return str(result) if result else ""
        except Exception:
            return ""

    def get_all_elements_text(self, selector: str) -> list[str]:
        """Get text content of ALL elements matching a selector."""
        js = f"""
        (() => {{
            const els = document.querySelectorAll({json.dumps(selector)});
            return Array.from(els).map(el => el.innerText || el.textContent || '');
        }})()
        """
        try:
            result = self.evaluate_js(js)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    def click_element(self, selector: str) -> bool:
        """Click a DOM element by selector."""
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.scrollIntoView({{block: 'center'}});
            el.focus();
            el.click();
            return true;
        }})()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False

    def set_input_value(self, selector: str, text: str, is_contenteditable: bool = False) -> bool:
        """Set the value of an input element.

        Handles both <textarea> and contenteditable <div> elements.
        For contenteditable (ProseMirror, Quill), uses CDP Input.insertText
        which is more reliable than execCommand and properly triggers
        framework state updates.
        """
        escaped_text = json.dumps(text)

        if is_contenteditable:
            # Step 1: Focus the element and clear it
            focus_js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                // Select all existing content and delete it
                const sel = window.getSelection();
                sel.selectAllChildren(el);
                return true;
            }})()
            """
            try:
                focused = self.evaluate_js(focus_js)
                if not focused:
                    return False
            except Exception:
                return False

            # Step 2: Delete existing content via CDP keyboard
            try:
                self.send_command("Input.dispatchKeyEvent", {
                    "type": "keyDown", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
                })
                self.send_command("Input.dispatchKeyEvent", {
                    "type": "keyUp", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
                })
            except Exception:
                pass  # May fail if empty, that's OK

            import time as _time
            _time.sleep(0.1)

            # Step 3: Insert text via CDP (works with ProseMirror, Quill, etc.)
            try:
                self.send_command("Input.insertText", {"text": text})
                logger.debug("Inserted %d chars via CDP Input.insertText", len(text))
                return True
            except Exception as e:
                logger.warning("CDP Input.insertText failed: %s, trying execCommand", e)

            # Fallback: execCommand
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                el.innerHTML = '';
                document.execCommand('insertText', false, {escaped_text});
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }})()
            """
            try:
                return bool(self.evaluate_js(js))
            except Exception as e:
                logger.error("Both CDP and execCommand failed: %s", e)
                return False
        else:
            # Standard textarea/input
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                // Use native setter to bypass React's synthetic events
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value'
                )?.set || Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                )?.set;
                if (nativeSetter) {{
                    nativeSetter.call(el, {escaped_text});
                }} else {{
                    el.value = {escaped_text};
                }}
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }})()
            """
            try:
                return bool(self.evaluate_js(js))
            except Exception as e:
                logger.error("Failed to set textarea value: %s", e)
                return False

    def press_enter(self) -> bool:
        """Simulate pressing Enter on the focused element."""
        js = """
        (() => {
            const el = document.activeElement;
            if (!el) return false;
            const events = ['keydown', 'keypress', 'keyup'];
            for (const type of events) {
                el.dispatchEvent(new KeyboardEvent(type, {
                    key: 'Enter', code: 'Enter', keyCode: 13,
                    which: 13, bubbles: true, cancelable: true,
                }));
            }
            return true;
        })()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False

    def dispatch_enter_on(self, selector: str) -> bool:
        """Dispatch Enter key event on a specific element.

        Uses CDP Input.dispatchKeyEvent for maximum compatibility
        (works with ProseMirror, Quill, React, etc.)
        """
        # First focus the element
        focus_js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.focus();
            return true;
        }})()
        """
        try:
            focused = self.evaluate_js(focus_js)
            if not focused:
                return False
        except Exception:
            return False

        # Then dispatch Enter via CDP protocol (more reliable than JS events)
        try:
            self.send_command("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            })
            self.send_command("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            })
            return True
        except Exception as e:
            logger.warning("CDP Enter key failed: %s, trying JS fallback", e)

        # Fallback: JS-level events
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.focus();
            for (const type of ['keydown', 'keypress', 'keyup']) {{
                el.dispatchEvent(new KeyboardEvent(type, {{
                    key: 'Enter', code: 'Enter', keyCode: 13,
                    which: 13, bubbles: true, cancelable: true,
                }}));
            }}
            return true;
        }})()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False

    def get_page_url(self) -> str:
        """Get the current page URL."""
        try:
            return str(self.evaluate_js("window.location.href") or "")
        except Exception:
            return ""

    def get_page_title(self) -> str:
        """Get the current page title."""
        try:
            return str(self.evaluate_js("document.title") or "")
        except Exception:
            return ""

    def scroll_to_bottom(self) -> None:
        """Scroll the page to the bottom (useful for chat views)."""
        self.evaluate_js("window.scrollTo(0, document.body.scrollHeight)")

    def count_elements(self, selector: str) -> int:
        """Count how many elements match a selector."""
        js = f"document.querySelectorAll({json.dumps(selector)}).length"
        try:
            return int(self.evaluate_js(js) or 0)
        except Exception:
            return 0


# ── CDP Tab Discovery ─────────────────────────────────────────────

@dataclass
class CDPTarget:
    """A Chrome/Edge tab available for CDP connection."""
    target_id: str
    title: str
    url: str
    ws_url: str
    tab_type: str = "page"


def discover_cdp_targets(port: int = DEFAULT_CDP_PORT, host: str = "127.0.0.1") -> list[CDPTarget]:
    """Query Chrome's /json endpoint to find all debuggable tabs."""
    if not URLLIB_AVAILABLE:
        return []

    try:
        url = f"http://{host}:{port}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())

        targets = []
        for item in data:
            if item.get("type") != "page":
                continue
            ws_url = item.get("webSocketDebuggerUrl", "")
            if not ws_url:
                continue
            targets.append(CDPTarget(
                target_id=item.get("id", ""),
                title=item.get("title", ""),
                url=item.get("url", ""),
                ws_url=ws_url,
                tab_type=item.get("type", "page"),
            ))

        logger.debug("Found %d CDP targets on port %d", len(targets), port)
        return targets

    except Exception as e:
        logger.debug("CDP discovery failed on port %d: %s", port, e)
        return []


def find_target_by_url(url_pattern: str, port: int = DEFAULT_CDP_PORT) -> Optional[CDPTarget]:
    """Find a CDP target whose URL contains the given pattern."""
    targets = discover_cdp_targets(port)
    pattern_lower = url_pattern.lower()
    for target in targets:
        if pattern_lower in target.url.lower():
            return target
    return None


def find_target_by_title(title_pattern: str, port: int = DEFAULT_CDP_PORT) -> Optional[CDPTarget]:
    """Find a CDP target whose title contains the given pattern."""
    targets = discover_cdp_targets(port)
    pattern_lower = title_pattern.lower()
    for target in targets:
        if pattern_lower in target.title.lower():
            return target
    return None


def is_cdp_available(port: int = DEFAULT_CDP_PORT) -> bool:
    """Check if Chrome is running with remote debugging enabled."""
    try:
        targets = discover_cdp_targets(port)
        return len(targets) > 0
    except Exception:
        return False


# ── High-level AI Chat Automation ─────────────────────────────────

class CDPChatAutomation:
    """High-level chat automation using CDP.

    Combines CDPConnection + CDPSelectors to provide simple methods:
    - send_prompt(text) -> sends text to the chat input and submits
    - wait_for_response() -> waits until the AI finishes generating
    - read_last_response() -> returns the AI's latest response text
    - send_and_read(text) -> full cycle: send, wait, read
    """

    def __init__(
        self,
        connection: CDPConnection,
        selectors: CDPSelectors,
        profile_name: str = "Unknown",
    ) -> None:
        self._conn = connection
        self._sel = selectors
        self._profile_name = profile_name
        self._response_count_before: int = 0

    @property
    def connection(self) -> CDPConnection:
        return self._conn

    @property
    def is_connected(self) -> bool:
        return self._conn.is_connected

    def send_prompt(self, text: str) -> bool:
        """Type a prompt into the chat input and send it.

        Returns True if the prompt was sent successfully.
        """
        if not self._conn.is_connected:
            logger.error("CDP not connected for %s", self._profile_name)
            return False

        # Record current response count for completion detection
        self._response_count_before = self._count_responses()

        # Find and focus the input element
        # Try each selector in the comma-separated list
        input_found = False
        for selector in self._sel.input_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                if self._conn.set_input_value(
                    selector, text,
                    is_contenteditable=self._sel.input_is_contenteditable,
                ):
                    input_found = True
                    logger.debug("Input found with selector: %s", selector)
                    break

        if not input_found:
            logger.error("Could not find chat input for %s", self._profile_name)
            return False

        # Small delay for UI to register the input
        time.sleep(0.3)

        # Send the message
        if self._sel.send_with_enter:
            # Dispatch Enter on the input
            for selector in self._sel.input_selector.split(","):
                selector = selector.strip()
                if self._conn.find_element(selector):
                    self._conn.dispatch_enter_on(selector)
                    break
        else:
            # Click the send button
            sent = False
            for selector in self._sel.send_button_selector.split(","):
                selector = selector.strip()
                if self._conn.click_element(selector):
                    sent = True
                    break
            if not sent:
                # Fallback: try Enter anyway
                logger.warning("Send button not found, trying Enter key")
                self._conn.press_enter()

        logger.info("Prompt sent to %s (%d chars)", self._profile_name, len(text))
        return True

    def wait_for_response(
        self,
        timeout: float = MAX_COMPLETION_WAIT,
        poll_interval: float = COMPLETION_POLL_INTERVAL,
        on_progress: Optional[Any] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> bool:
        """Wait for the AI to finish generating its response.

        Uses multiple detection strategies:
        1. New response element appears (count increases)
        2. Loading/stop indicators appear then disappear
        3. Response text stops changing (stabilizes)

        Returns True if response detected, False on timeout.
        """
        start = time.time()
        last_text = ""
        stable_count = 0
        STABLE_THRESHOLD = 3  # Text unchanged for 3 polls = done
        new_response_detected = False
        initial_text = self._get_latest_response_text()

        # Initial delay to let generation start
        time.sleep(1.5)

        while time.time() - start < timeout:
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Cancelled during wait")

            elapsed = time.time() - start

            # Check indicators
            has_loading = self._check_loading()
            has_stop = self._check_stop_button()

            # Check response count
            current_count = self._count_responses()
            if current_count > self._response_count_before:
                new_response_detected = True

            # Get latest response text
            current_text = self._get_latest_response_text()

            # Ignore temporary empty reads (DOM re-rendering)
            if not current_text and last_text:
                current_text = last_text  # Keep previous value

            # Only count as stable if a NEW response appeared and text changed
            if new_response_detected and current_text != initial_text:
                if current_text and current_text == last_text and len(current_text) > 5:
                    stable_count += 1
                elif current_text and current_text != last_text:
                    stable_count = 0  # Still changing
                # Don't reset stable_count for empty reads
            else:
                stable_count = 0
            last_text = current_text

            # Report progress
            if on_progress:
                remaining = int(timeout - elapsed)
                status = "generating" if (has_loading or has_stop) else "checking"
                on_progress(
                    f"{self._profile_name}: {status}... "
                    f"{remaining}s remaining | {len(current_text)} chars"
                )

            # Decision: Are we done?
            if new_response_detected and current_text != initial_text:
                # New response appeared and text is different from before
                if not has_loading and not has_stop and stable_count >= STABLE_THRESHOLD:
                    logger.info(
                        "%s finished generating (%.1fs, %d chars)",
                        self._profile_name, elapsed, len(current_text)
                    )
                    return True
            elif elapsed > 20 and not new_response_detected:
                # 20s and no new response element — maybe the site uses
                # a different structure. Check if text changed at all.
                if current_text and current_text != initial_text and stable_count >= STABLE_THRESHOLD:
                    logger.info("%s: text changed and stabilized after %.1fs", self._profile_name, elapsed)
                    return True

            time.sleep(poll_interval)

        logger.warning("%s: response wait timed out after %.0fs", self._profile_name, timeout)
        return False

    def read_last_response(self) -> str:
        """Read the text of the AI's most recent response.

        Always gets ALL response elements and takes the LAST one.
        CSS :last-of-type selectors are unreliable for nested chat structures.
        """
        if not self._conn.is_connected:
            return ""

        # Primary: Get all responses via response_selector, take last
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                texts = self._conn.get_all_elements_text(selector)
                if texts:
                    meaningful = [t for t in texts if len(t.strip()) > 5]
                    if meaningful:
                        return meaningful[-1].strip()

        # Fallback: try common selectors
        fallback_selectors = [
            ".markdown", ".prose", "[class*='response'] .markdown",
            "[class*='message']", "[class*='answer']",
            "article", ".content",
        ]
        for selector in fallback_selectors:
            texts = self._conn.get_all_elements_text(selector)
            meaningful = [t for t in texts if len(t.strip()) > 10]
            if meaningful:
                return meaningful[-1].strip()

        logger.warning("Could not find response text for %s", self._profile_name)
        return ""

    def send_and_read(
        self,
        prompt: str,
        timeout: float = MAX_COMPLETION_WAIT,
        on_progress: Optional[Any] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> str:
        """Full cycle: send prompt, wait for response, read it."""
        if not self.send_prompt(prompt):
            raise RuntimeError(f"Failed to send prompt to {self._profile_name}")

        if not self.wait_for_response(
            timeout=timeout,
            on_progress=on_progress,
            cancel_event=cancel_event,
        ):
            logger.warning("%s: wait timed out, reading whatever is available", self._profile_name)

        # Small delay for final rendering
        time.sleep(1.0)
        return self.read_last_response()

    def _check_loading(self) -> bool:
        """Check if any loading indicator is present."""
        if not self._sel.loading_selector:
            return False
        for selector in self._sel.loading_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                return True
        return False

    def _check_stop_button(self) -> bool:
        """Check if a stop/cancel generation button is present."""
        if not self._sel.stop_button_selector:
            return False
        for selector in self._sel.stop_button_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                return True
        return False

    def _get_latest_response_text(self) -> str:
        """Get the text of the LAST (newest) response for change detection.

        Always uses get_all_elements_text and takes [-1] to ensure
        we're reading the newest response, not an older one.
        """
        # Strategy: get ALL response elements and take the last one
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                texts = self._conn.get_all_elements_text(selector)
                if texts:
                    # Filter meaningful and return the last
                    meaningful = [t for t in texts if len(t.strip()) > 5]
                    if meaningful:
                        return meaningful[-1]
        # Fallback to last_response_selector
        if self._sel.last_response_selector:
            for selector in self._sel.last_response_selector.split(","):
                selector = selector.strip()
                text = self._conn.get_element_text(selector)
                if text and len(text.strip()) > 5:
                    return text
        return ""

    def _count_responses(self) -> int:
        """Count the number of response elements on the page."""
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                count = self._conn.count_elements(selector)
                if count > 0:
                    return count
        return 0


# ── Browser Launch Helpers ────────────────────────────────────────

def get_chrome_debug_args(port: int = DEFAULT_CDP_PORT) -> list[str]:
    """Return Chrome command-line args needed for CDP debugging."""
    return [
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
    ]


def launch_chrome_with_cdp(
    url: str = "",
    port: int = DEFAULT_CDP_PORT,
    browser_exe: str = "",
    extra_args: Optional[list[str]] = None,
    corner: str = "",
) -> bool:
    """Launch Chrome/Edge with remote debugging enabled.

    Uses a dedicated Autocoder Chrome profile (~/.autocoder/chrome_profile).
    The user logs in once to each AI site and it's remembered across sessions.
    Chrome's real profile can't be used with --remote-debugging-port.
    """
    import subprocess
    import os
    from pathlib import Path

    if not browser_exe:
        from .window_manager import _find_browser_exe
        browser_exe = _find_browser_exe("chrome") or _find_browser_exe("edge") or ""

    if not browser_exe:
        logger.error("No browser found")
        return False

    # If a corner is specified, use its dedicated port
    if corner and corner in CDP_CORNER_PORTS:
        port = CDP_CORNER_PORTS[corner]

    args = [browser_exe] + get_chrome_debug_args(port)

    # Always use a dedicated Autocoder profile.
    # Chrome won't honor --remote-debugging-port with the real profile
    # because of its singleton process model. The user logs in once
    # to each AI site in this profile and it's remembered.
    profile_dir = str(Path.home() / ".autocoder" / "chrome_profile")
    args.append(f"--user-data-dir={profile_dir}")

    if extra_args:
        args.extend(extra_args)

    if url:
        args.append(url)

    try:
        subprocess.Popen(
            args,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        logger.info("Launched browser with CDP on port %d: %s", port, url)
        # Wait for browser to start
        time.sleep(4)
        return is_cdp_available(port)
    except Exception as e:
        logger.error("Failed to launch browser with CDP: %s", e)
        return False


def is_chrome_running() -> bool:
    """Check if Chrome is currently running."""
    import subprocess
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
            capture_output=True, text=True, timeout=5,
        )
        return 'chrome.exe' in result.stdout
    except Exception:
        return False


def kill_chrome() -> bool:
    """Kill all Chrome processes (needed to relaunch with CDP)."""
    import subprocess
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                       capture_output=True, timeout=10)
        time.sleep(2)
        return not is_chrome_running()
    except Exception:
        return False


# ── Convenience: connect to a specific AI site ────────────────────

def connect_to_ai_site(
    profile_name: str,
    url_pattern: str = "",
    title_pattern: str = "",
    port: int = DEFAULT_CDP_PORT,
) -> Optional[CDPChatAutomation]:
    """Find a browser tab matching the AI site and return a chat automation object.

    Tries the specified port first, then scans all corner ports.

    Args:
        profile_name: Name of the AI profile (e.g., "Gemini", "ChatGPT")
        url_pattern: URL substring to match (e.g., "gemini.google.com")
        title_pattern: Window title substring to match
        port: CDP debugging port (tries this first, then others)

    Returns:
        CDPChatAutomation ready to use, or None if not found.
    """
    # Build list of ports to try: specified port first, then all corner ports
    ports_to_try = [port]
    for p in CDP_CORNER_PORTS.values():
        if p not in ports_to_try:
            ports_to_try.append(p)

    for try_port in ports_to_try:
        target = None
        if url_pattern:
            target = find_target_by_url(url_pattern, try_port)
        if not target and title_pattern:
            target = find_target_by_title(title_pattern, try_port)

        if target:
            conn = CDPConnection(target.ws_url)
            if conn.connect():
                selectors = get_selectors_for_profile(profile_name)
                logger.info("CDP connected to %s on port %d", profile_name, try_port)
                return CDPChatAutomation(conn, selectors, profile_name)

    logger.warning("No CDP target found for %s (url=%s, title=%s) on any port",
                    profile_name, url_pattern, title_pattern)
    return None
