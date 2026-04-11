"""Session manager — coordinates up to 4 AI browser sessions.

Each session has its own AI profile, browser window, task queue, and executor.
Sessions share the Mouse Traffic Controller for serialized mouse access.
"""

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from gemini_coder.platform_utils import get_config_dir
from gemini_coder.task_manager import TaskQueue, TaskExecutor

from .ai_profiles import AIProfile, GEMINI_PROFILE
from .universal_client import UniversalBrowserClient

logger = logging.getLogger(__name__)

CORNERS = ["top-left", "top-right", "bottom-left", "bottom-right"]
MAX_SESSIONS = 4


@dataclass
class Session:
    """One AI browser session — a window, a client, and a task queue."""
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    ai_profile: AIProfile = field(default_factory=lambda: GEMINI_PROFILE)
    corner: str = "bottom-right"
    hwnd: Optional[int] = None
    client: Optional[UniversalBrowserClient] = None
    task_queue: Optional[TaskQueue] = None
    executor: Optional[TaskExecutor] = None
    is_active: bool = False
    is_configured: bool = False

    @property
    def display_name(self) -> str:
        return f"{self.ai_profile.name} ({self.corner})"

    @property
    def is_running(self) -> bool:
        return self.executor is not None and self.executor.is_running


class SessionManager:
    """Manages up to 4 simultaneous AI browser sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._corner_map: dict[str, str] = {}  # corner -> session_id

    @property
    def sessions(self) -> list[Session]:
        return list(self._sessions.values())

    @property
    def active_sessions(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.is_active]

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_session_by_corner(self, corner: str) -> Optional[Session]:
        sid = self._corner_map.get(corner)
        return self._sessions.get(sid) if sid else None

    def get_available_corners(self) -> list[str]:
        return [c for c in CORNERS if c not in self._corner_map]

    def get_occupied_corners(self) -> list[str]:
        return list(self._corner_map.keys())

    def create_session(
        self,
        ai_profile: AIProfile,
        corner: str,
    ) -> Session:
        """Create a new session in the given corner."""
        if len(self._sessions) >= MAX_SESSIONS:
            raise RuntimeError(f"Maximum {MAX_SESSIONS} sessions reached")

        if corner in self._corner_map:
            raise RuntimeError(f"Corner {corner} already occupied")

        if corner not in CORNERS:
            raise RuntimeError(f"Invalid corner: {corner}. Use: {CORNERS}")

        # Create client
        client = UniversalBrowserClient(
            ai_profile=ai_profile,
            corner=corner,
            use_traffic_control=True,
        )

        # Create task queue with corner-specific persistence
        queue_path = get_config_dir() / f"task_queue_{corner.replace('-', '_')}.json"
        task_queue = TaskQueue(save_path=queue_path)

        # Create executor
        executor = TaskExecutor(client, task_queue)

        session = Session(
            ai_profile=ai_profile,
            corner=corner,
            client=client,
            task_queue=task_queue,
            executor=executor,
            is_active=True,
        )

        self._sessions[session.session_id] = session
        self._corner_map[corner] = session.session_id

        logger.info("Created session %s: %s at %s",
                     session.session_id, ai_profile.name, corner)
        return session

    def configure_session(self, session_id: str) -> bool:
        """Find/launch the browser window for a session."""
        session = self._sessions.get(session_id)
        if not session or not session.client:
            return False

        ok = session.client.configure()
        if ok:
            session.hwnd = session.client.hwnd
            session.is_configured = True
            logger.info("Session %s configured: hwnd=%s", session_id, session.hwnd)
        return ok

    def start_session(self, session_id: str) -> bool:
        """Start executing the task queue for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if not session.is_configured:
            if not self.configure_session(session_id):
                return False

        if session.executor and not session.executor.is_running:
            session.executor.start()
            logger.info("Session %s started: %s", session_id, session.display_name)
            return True
        return False

    def stop_session(self, session_id: str) -> None:
        """Stop a session's task executor."""
        session = self._sessions.get(session_id)
        if session and session.executor:
            session.executor.stop()
            logger.info("Session %s stopped", session_id)

    def remove_session(self, session_id: str) -> bool:
        """Remove a session completely."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.executor and session.executor.is_running:
            session.executor.stop()

        if session.client:
            session.client.cancel()
            session.client.release_hwnd()

        self._corner_map.pop(session.corner, None)
        del self._sessions[session_id]

        logger.info("Removed session %s: %s", session_id, session.display_name)
        return True

    def stop_all(self) -> None:
        """Emergency stop all sessions."""
        for session in self._sessions.values():
            if session.executor and session.executor.is_running:
                session.executor.stop()
            if session.client:
                session.client.cancel()
        logger.info("All sessions stopped")

    def capture_window_for_session(self, session_id: str, hwnd: int) -> bool:
        """Assign a specific window handle to a session (from capture mode)."""
        session = self._sessions.get(session_id)
        if not session or not session.client:
            return False

        ok = session.client.configure_with_hwnd(hwnd)
        if ok:
            session.hwnd = hwnd
            session.is_configured = True
            logger.info("Captured hwnd=%d for session %s", hwnd, session_id)
        return ok

    def set_session_callbacks(
        self,
        session_id: str,
        on_output: Optional[Callable] = None,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_tick: Optional[Callable] = None,
        on_status: Optional[Callable] = None,
    ) -> None:
        """Wire UI callbacks to a session's executor."""
        session = self._sessions.get(session_id)
        if session and session.executor:
            session.executor.set_callbacks(
                on_output=on_output,
                on_task_start=on_task_start,
                on_task_complete=on_task_complete,
                on_tick=on_tick,
                on_status=on_status,
            )
