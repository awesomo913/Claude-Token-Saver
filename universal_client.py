"""Universal browser-based AI client.

Same generate() interface as GeminiClient — TaskExecutor and ExpansionEngine
work unchanged. Drives ANY AI web chat via an AIProfile.

Two automation backends:
1. CDP (Chrome DevTools Protocol) — preferred, reliable DOM targeting
2. pyautogui fallback — blind clicking (legacy, unreliable)

CDP connects to Chrome/Edge running with --remote-debugging-port=9222.
It finds the right tab by URL pattern, then interacts via DOM selectors.
"""

import logging
import threading
import time
from typing import Callable, Optional

from gemini_coder.gemini_client import Conversation
from gemini_coder.safe_exec import safe_call

from .ai_profiles import AIProfile, GEMINI_PROFILE
from .browser_actions import (
    PYAUTOGUI_AVAILABLE,
    send_prompt_and_get_response,
    send_prompt_phase,
    read_response_phase,
    wait_for_generation_done,
    focus_window,
    POST_GENERATE_WAIT,
)
from .window_manager import (
    find_windows_by_title,
    launch_to_url,
    position_existing_window,
)

# CDP imports
from .cdp_client import (
    CDPConnection,
    CDPChatAutomation,
    CDPSelectors,
    discover_cdp_targets,
    find_target_by_url,
    find_target_by_title,
    is_cdp_available,
    get_selectors_for_profile,
    connect_to_ai_site,
    launch_chrome_with_cdp,
    DEFAULT_CDP_PORT,
)

logger = logging.getLogger(__name__)

try:
    from mousetraffic.client import TrafficClient
    TRAFFIC_AVAILABLE = True
except ImportError:
    TRAFFIC_AVAILABLE = False

# URL patterns for matching AI sites to CDP tabs
AI_URL_PATTERNS = {
    "Gemini": "gemini.google.com",
    "ChatGPT": "chatgpt.com",
    "Claude": "claude.ai",
    "OpenRouter": "openrouter.ai",
    "Copilot": "copilot.microsoft.com",
}


class UniversalBrowserClient:
    """Controls ANY AI web chat through browser automation.

    Drop-in replacement for GeminiClient. TaskExecutor calls generate()
    and gets back a response string — doesn't care which AI produced it.

    Prefers CDP (DOM-based) over pyautogui (pixel-based) when available.
    """

    MAX_RETRIES = 3
    BASE_DELAY = 2.0

    def __init__(
        self,
        ai_profile: AIProfile = GEMINI_PROFILE,
        corner: str = "bottom-right",
        use_traffic_control: bool = True,
        traffic_timeout: float = 600.0,
        cdp_port: int = DEFAULT_CDP_PORT,
    ) -> None:
        self._profile = ai_profile
        self._corner = corner
        self._use_traffic = use_traffic_control and TRAFFIC_AVAILABLE
        self._traffic_timeout = traffic_timeout
        self._cdp_port = cdp_port
        self._hwnd: Optional[int] = None
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._configured = False

        # CDP automation (preferred)
        self._cdp: Optional[CDPChatAutomation] = None
        self._cdp_available = False

    @property
    def profile(self) -> AIProfile:
        return self._profile

    @profile.setter
    def profile(self, value: AIProfile) -> None:
        self._profile = value
        self._configured = False
        self._hwnd = None
        # Disconnect CDP when profile changes
        if self._cdp and self._cdp.connection:
            self._cdp.connection.disconnect()
        self._cdp = None
        self._cdp_available = False

    @property
    def corner(self) -> str:
        return self._corner

    @property
    def is_configured(self) -> bool:
        return self._configured and (self._cdp_available or self._hwnd is not None)

    @property
    def hwnd(self) -> Optional[int]:
        return self._hwnd

    @property
    def using_cdp(self) -> bool:
        """Whether this client is using CDP (vs pyautogui fallback)."""
        return self._cdp_available and self._cdp is not None

    # Track which hwnds are already claimed by other sessions
    _claimed_hwnds: set = set()
    _claimed_lock = threading.Lock()

    @classmethod
    def _claim_hwnd(cls, hwnd: int) -> bool:
        """Thread-safe hwnd claiming."""
        with cls._claimed_lock:
            if hwnd in cls._claimed_hwnds:
                return False
            cls._claimed_hwnds.add(hwnd)
            return True

    @classmethod
    def _release_hwnd(cls, hwnd: int) -> None:
        """Thread-safe hwnd release."""
        with cls._claimed_lock:
            cls._claimed_hwnds.discard(hwnd)

    def configure(self, api_key: str = "") -> bool:
        """Find or launch the AI's window. api_key param ignored (compat).

        Tries CDP first (connect to existing Chrome debug port),
        then falls back to pyautogui window finding.
        """
        # ── Try CDP first ─────────────────────────────────────────
        if self._try_configure_cdp():
            logger.info("Configured %s via CDP (reliable DOM mode)", self._profile.name)
            self._configured = True
            return True

        # ── Fallback to pyautogui ─────────────────────────────────
        if not PYAUTOGUI_AVAILABLE:
            logger.error("Neither CDP nor pyautogui available")
            return False

        # Don't permanently disable traffic — it may start later
        if self._use_traffic and not TrafficClient.is_server_running():
            logger.warning("Traffic Controller not running yet (will re-check at generate time)")

        # Try to find an existing window matching the profile
        if self._profile.title_pattern:
            handles = find_windows_by_title(self._profile.title_pattern)
            with self._claimed_lock:
                available = [h for h in handles if h not in self._claimed_hwnds]
            if available:
                self._hwnd = available[0]
                with self._claimed_lock:
                    self._claimed_hwnds.add(self._hwnd)
                position_existing_window(self._hwnd, self._corner)
                self._configured = True
                logger.info("Found %s window: hwnd=%d (pyautogui fallback)",
                            self._profile.name, self._hwnd)
                return True

        # No existing window — try to launch
        if self._profile.url:
            hwnd = launch_to_url(
                url=self._profile.url,
                corner=self._corner,
                browser=self._profile.browser,
                title_pattern=self._profile.title_pattern,
            )
            if hwnd:
                self._hwnd = hwnd
                with self._claimed_lock:
                    self._claimed_hwnds.add(hwnd)
                self._configured = True
                logger.info("Launched %s window: hwnd=%d (pyautogui fallback)",
                            self._profile.name, hwnd)
                return True

        logger.error("Could not find or launch %s window", self._profile.name)
        return False

    def _try_configure_cdp(self) -> bool:
        """Try to connect to the AI site via CDP."""
        url_pattern = self._profile.url_pattern or AI_URL_PATTERNS.get(self._profile.name, "")
        title_pattern = self._profile.title_pattern

        if not url_pattern and not title_pattern:
            return False

        cdp = connect_to_ai_site(
            profile_name=self._profile.name,
            url_pattern=url_pattern,
            title_pattern=title_pattern,
            port=self._cdp_port,
        )

        if cdp and cdp.is_connected:
            self._cdp = cdp
            self._cdp_available = True
            logger.info("CDP connected to %s: %s", self._profile.name, cdp.connection.get_page_url())
            return True

        return False

    def configure_with_hwnd(self, hwnd: int) -> bool:
        """Directly assign a window handle (from capture mode).

        Also tries to find a matching CDP target for this window.
        """
        import ctypes
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False

        # Reject if another session already claimed this hwnd
        with self._claimed_lock:
            if hwnd in self._claimed_hwnds and hwnd != self._hwnd:
                logger.warning("hwnd=%d already claimed by another session", hwnd)
                return False

        # Release old hwnd if any
        if self._hwnd:
            self._release_hwnd(self._hwnd)

        self._hwnd = hwnd
        with self._claimed_lock:
            self._claimed_hwnds.add(hwnd)
        position_existing_window(hwnd, self._corner)
        self._configured = True

        # Try CDP connection for this window
        self._try_configure_cdp()

        logger.info("Captured window hwnd=%d for %s at %s (cdp=%s)",
                     hwnd, self._profile.name, self._corner, self._cdp_available)
        return True

    def release_hwnd(self) -> None:
        """Release the claimed hwnd when session is removed."""
        if self._hwnd:
            self._release_hwnd(self._hwnd)
            self._hwnd = None
        if self._cdp:
            self._cdp.connection.disconnect()
            self._cdp = None
            self._cdp_available = False
        self._configured = False

    def update_settings(
        self,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        """Ignored — browser AI uses whatever model is loaded in the UI."""
        pass

    def cancel(self) -> None:
        self._cancel_event.set()

    def generate(
        self,
        prompt: str,
        conversation: Optional[Conversation] = None,
        system_instruction: str = "",
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Generate a response by typing into the AI web chat.

        Uses CDP if available, falls back to pyautogui.
        """
        self._cancel_event.clear()

        if not self.is_configured:
            raise RuntimeError(
                f"{self._profile.name} not configured. "
                "Click 'Launch' in the session panel."
            )

        with self._lock:
            # Try CDP first
            if self._cdp_available and self._cdp and self._cdp.is_connected:
                return self._generate_cdp(prompt, conversation, on_progress)

            # Try to reconnect CDP (connection may have dropped)
            if self._try_configure_cdp():
                return self._generate_cdp(prompt, conversation, on_progress)

            # Fallback to pyautogui
            return self._generate_pyautogui(prompt, conversation, on_progress)

    def _generate_cdp(
        self,
        prompt: str,
        conversation: Optional[Conversation],
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Generate using CDP — direct DOM manipulation. No mouse needed."""
        for attempt in range(self.MAX_RETRIES):
            if self._cancel_event.is_set():
                raise InterruptedError("Generation cancelled")

            try:
                if on_progress:
                    on_progress(f"{self._profile.name}: Sending via CDP...")

                result = self._cdp.send_and_read(
                    prompt=prompt,
                    timeout=300,
                    on_progress=on_progress,
                    cancel_event=self._cancel_event,
                )

                if not result or len(result.strip()) < 5:
                    raise RuntimeError("Empty response from CDP")

                if conversation:
                    conversation.add_user_message(prompt)
                    conversation.add_model_message(result)

                logger.info("CDP response from %s: %d chars", self._profile.name, len(result))
                return result

            except InterruptedError:
                raise
            except Exception as e:
                logger.warning(
                    "%s CDP generation failed (attempt %d/%d): %s",
                    self._profile.name, attempt + 1, self.MAX_RETRIES, e
                )
                if attempt < self.MAX_RETRIES - 1:
                    # Try reconnecting CDP
                    self._cdp.connection.disconnect()
                    time.sleep(self.BASE_DELAY * (2 ** attempt))
                    if not self._try_configure_cdp():
                        logger.warning("CDP reconnect failed, will fall back to pyautogui")
                        self._cdp_available = False
                        return self._generate_pyautogui(prompt, conversation, on_progress)
                else:
                    raise RuntimeError(
                        f"{self._profile.name} CDP failed after {self.MAX_RETRIES} attempts: {e}"
                    ) from e

        return ""

    def _generate_pyautogui(
        self,
        prompt: str,
        conversation: Optional[Conversation],
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Generate using pyautogui — legacy blind mouse/keyboard automation."""
        for attempt in range(self.MAX_RETRIES):
            if self._cancel_event.is_set():
                raise InterruptedError("Generation cancelled")

            try:
                # Re-check traffic availability at generate time
                use_traffic = (self._use_traffic and TRAFFIC_AVAILABLE
                               and TrafficClient.is_server_running())
                if use_traffic:
                    traffic_name = f"ai-coder-{self._corner}"

                    # PHASE 1: Acquire lock, send prompt, release lock (~5 seconds)
                    traffic = TrafficClient(traffic_name, timeout=self._traffic_timeout)
                    traffic.acquire()
                    try:
                        traffic.mark_move()
                        send_prompt_phase(self._hwnd, prompt, self._profile)
                    finally:
                        traffic.release()

                    # PHASE 2: Wait (NO lock, all sessions wait in parallel)
                    if on_progress:
                        on_progress(f"{self._profile.name}: Waiting for response (pyautogui)...")
                    wait_for_generation_done(
                        self._hwnd, prompt_length=len(prompt),
                        profile=self._profile, timeout=300,
                        on_progress=on_progress, cancel_event=self._cancel_event,
                    )
                    time.sleep(POST_GENERATE_WAIT)

                    # PHASE 3: Acquire lock, read response, release lock (~5 seconds)
                    traffic2 = TrafficClient(traffic_name, timeout=self._traffic_timeout)
                    traffic2.acquire()
                    try:
                        traffic2.mark_move()
                        result = read_response_phase(self._hwnd, self._profile)
                    finally:
                        traffic2.release()
                else:
                    result = self._do_generate_pyautogui(prompt, on_progress)

                if conversation:
                    conversation.add_user_message(prompt)
                    conversation.add_model_message(result)

                return result

            except InterruptedError:
                raise
            except Exception as e:
                logger.warning(
                    "%s pyautogui generation failed (attempt %d/%d): %s",
                    self._profile.name, attempt + 1, self.MAX_RETRIES, e
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"{self._profile.name} failed after {self.MAX_RETRIES} attempts: {e}"
                    ) from e

        return ""

    def _do_generate_pyautogui(
        self,
        prompt: str,
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Browser automation with defensive timeout (pyautogui)."""
        result = safe_call(
            send_prompt_and_get_response,
            args=(self._hwnd, prompt),
            kwargs={
                "profile": self._profile,
                "timeout": 300,
                "on_progress": on_progress,
                "cancel_event": self._cancel_event,
            },
            timeout_ms=330_000,
        )

        if result.timed_out:
            raise RuntimeError(
                f"{self._profile.name} automation timed out. "
                "Force-killed to protect the main loop."
            )
        if result.error:
            raise RuntimeError(f"{self._profile.name} error: {result.error}")

        return result.stdout

    def test_connection(self) -> tuple[bool, str]:
        """Test that the AI window is accessible."""
        # Test CDP first
        if self._cdp_available and self._cdp and self._cdp.is_connected:
            try:
                title = self._cdp.connection.get_page_title()
                url = self._cdp.connection.get_page_url()
                return True, f"{self._profile.name} ready via CDP ({title[:30]})"
            except Exception:
                pass

        # Test pyautogui
        if not PYAUTOGUI_AVAILABLE:
            return False, "Neither CDP nor pyautogui available"

        if self._hwnd is None:
            configured = self.configure()
            if not configured:
                return False, f"Could not find or launch {self._profile.name}"

        if focus_window(self._hwnd):
            mode = "CDP" if self._cdp_available else "pyautogui"
            traffic_status = ""
            if self._use_traffic:
                if TrafficClient.is_server_running():
                    traffic_status = " | Traffic: Connected"
                else:
                    traffic_status = " | Traffic: Not running"
            return True, f"{self._profile.name} ready [{mode}] (hwnd={self._hwnd}){traffic_status}"

        return False, f"Could not focus {self._profile.name} window"

    def list_available_models(self) -> list[str]:
        return [f"{self._profile.name} (uses whatever model is loaded in browser)"]


# Backward compatibility alias
class BrowserGeminiClient(UniversalBrowserClient):
    """Legacy alias — creates a UniversalBrowserClient with Gemini preset."""
    def __init__(self, **kwargs):
        profile = kwargs.pop("ai_profile", GEMINI_PROFILE)
        super().__init__(ai_profile=profile, **kwargs)
