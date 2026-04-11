from typing import Optional

from gemini_coder.session_manager import SessionManager
from gemini_coder.ai_profiles import PRESET_PROFILES
from gemini_coder.task_manager import CodingTask
from gemini_coder.expander import ExpansionEngine
from gemini_coder.platform_utils import get_config_dir


class GUIBridge:
    """Bridge between the GUI and the backend.

    This keeps the GUI decoupled from the backend implementation while
    still providing a convenient API for common actions.
    """

    def __init__(self, session_manager: SessionManager, history=None, expander=None) -> None:
        self.session_manager = session_manager
        self._history = history
        self._expander = expander

    def create_session(self, profile_name: str, corner: str) -> Optional[str]:
        """Create a new session for the given profile at the specified corner."""
        profile = PRESET_PROFILES.get(profile_name)
        if not profile:
            return None
        sess = self.session_manager.create_session(profile, corner)
        return sess.session_id

    def start_session(self, session_id: str) -> bool:
        """Start executing tasks for a given session."""
        return self.session_manager.start_session(session_id)

    def stop_session(self, session_id: str) -> None:
        """Stop a given session's executor."""
        self.session_manager.stop_session(session_id)

    def remove_session(self, session_id: str) -> bool:
        """Remove a session completely."""
        return self.session_manager.remove_session(session_id)

    def add_task_to_session(self, session_id: str, description: str, title: str | None = None) -> Optional[str]:
        """Add a coding task to a session's queue."""
        sess = self.session_manager.get_session(session_id)
        if not sess:
            return None
        task = CodingTask(title=title or description[:50], description=description, session_id=session_id)
        if sess.task_queue:
            sess.task_queue.add(task)
        return task.task_id

    def expand_task_for_session(self, session_id: str, task_text: str) -> Optional[str]:
        """Expand a simple task to a production-ready prompt and enqueue."""
        sess = self.session_manager.get_session(session_id)
        if not sess:
            return None
        client = sess.client
        if client is None:
            return None
        expander = self._expander
        if expander is None:
            expander = ExpansionEngine(client, depth_limit=4)
            self._expander = expander
        expanded = expander.expand_task(task_text)
        task = CodingTask(title=task_text[:50], description=expanded, session_id=session_id)
        if sess.task_queue:
            sess.task_queue.add(task)
        return task.task_id

    def get_available_corners(self) -> list[str]:
        """Return list of corners that are not currently occupied."""
        return self.session_manager.get_available_corners()

    def get_all_sessions(self) -> list[str]:
        """Return a human-friendly list of all sessions."""
        return [s.display_name for s in self.session_manager.sessions]
