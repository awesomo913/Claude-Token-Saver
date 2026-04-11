"""Broadcast mode — send a task to all active sessions and loop endlessly.

When enabled, the user types ONE task description and it gets:
1. Engineered into a proper prompt via Prompt Architect's engine
2. Sent to ALL active sessions (or selected ones)
3. After each session completes, it auto-feeds the next improvement round
4. Loops until the user clicks Stop or hits Ctrl+K

Each session works independently — they all start at the same time and
the Traffic Controller serializes their mouse access. The prompts are
customized per-session using the AI profile name for context.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from gemini_coder.task_manager import CodingTask, TaskStatus
from .auto_save import save_task_output

logger = logging.getLogger(__name__)

# Import prompt engine for prompt engineering
try:
    from prompt_engine import (
        generate_code_prompt,
        BUILD_TARGETS,
        ENHANCEMENTS,
    )
    PROMPT_ENGINE_AVAILABLE = True
except ImportError:
    PROMPT_ENGINE_AVAILABLE = False
    logger.warning("prompt_engine not found — prompts will be sent raw")


def engineer_prompt(
    task: str,
    build_target: str = "PC Desktop App",
    enhancements: Optional[list[str]] = None,
    context: str = "",
) -> str:
    """Use Prompt Architect's engine to build a production-grade prompt.

    Takes a simple task like "Build a calculator" and expands it into
    a full engineered prompt with role, platform context, reasoning,
    constraints, and quality gates.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        return task

    if enhancements is None:
        enhancements = ["More Features + Robustness"]

    return generate_code_prompt(
        task=task,
        build_target=build_target,
        enhancements=enhancements,
        context=context,
        reasoning="Structured CoT (SCoT)",
        output_format="Code Only",
        constraint_presets=["Python Best Practices", "Robustness"],
    )


def engineer_improvement_prompt(
    task: str,
    iteration: int,
    ai_name: str = "",
) -> str:
    """Generate an improvement prompt for subsequent iterations.

    Cycles through different improvement focuses so each round
    makes the code meaningfully better in a different dimension.
    """
    improvement_focuses = [
        {
            "focus": "Add Features",
            "prompt": (
                "You previously wrote code for: {task}\n\n"
                "Now ADD 2-3 useful features a real user would want:\n"
                "- Config options, CLI arguments, settings\n"
                "- Logging, progress indicators\n"
                "- Input validation, helpful error messages\n"
                "- Any missing functionality\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Professional Polish",
            "prompt": (
                "Improve this code to look and feel professional:\n"
                "- Clean structure, consistent naming\n"
                "- Type hints, docstrings\n"
                "- Organized imports, __main__ block\n"
                "- Polished output/UI\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Robustness & Edge Cases",
            "prompt": (
                "Harden this code for real-world use:\n"
                "- Handle edge cases, empty input, missing files\n"
                "- Add retry logic, graceful shutdown\n"
                "- Resource cleanup, error handling\n"
                "- Validate all inputs\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Performance & Optimization",
            "prompt": (
                "Optimize this code:\n"
                "- Fix bottlenecks, use efficient data structures\n"
                "- Add caching where sensible\n"
                "- Minimize I/O and unnecessary computation\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Final Review & Expand",
            "prompt": (
                "Senior developer final review:\n"
                "- Ensure all features work together\n"
                "- Fix any remaining issues\n"
                "- Add usage examples in comments\n"
                "- Think about what ELSE this could do — add one more capability\n\n"
                "Return the FINAL, COMPLETE code."
            ),
        },
    ]

    idx = iteration % len(improvement_focuses)
    focus = improvement_focuses[idx]
    prompt = focus["prompt"].format(task=task)

    if ai_name:
        prompt = f"[You are {ai_name}] {prompt}"

    return prompt


@dataclass
class BroadcastConfig:
    """Configuration for a broadcast run."""
    task: str = ""
    build_target: str = "PC Desktop App"
    enhancements: list[str] = field(default_factory=lambda: ["More Features + Robustness"])
    context: str = ""
    session_ids: list[str] = field(default_factory=list)  # Empty = all active
    endless: bool = True
    max_iterations: int = 999  # Safety cap
    time_limit_minutes: int = 0  # 0 = no limit


class BroadcastController:
    """Broadcasts a task to multiple sessions and loops improvements.

    Usage:
        bc = BroadcastController(session_manager)
        bc.set_callbacks(on_output=..., on_status=...)
        bc.start(BroadcastConfig(task="Build a calculator"))
        # ... runs until bc.stop()
    """

    def __init__(self, session_manager) -> None:
        self._sm = session_manager
        self._running = False
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._iteration_counts: dict[str, int] = {}
        self._results: dict[str, str] = {}  # session_id -> latest actual result

        self._on_output: Optional[Callable] = None
        self._on_status: Optional[Callable] = None
        self._on_iteration: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def set_callbacks(
        self,
        on_output: Optional[Callable] = None,
        on_status: Optional[Callable] = None,
        on_iteration: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
    ) -> None:
        self._on_output = on_output
        self._on_status = on_status
        self._on_iteration = on_iteration
        self._on_complete = on_complete

    def start(self, config: BroadcastConfig) -> None:
        """Start broadcasting to all target sessions."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._iteration_counts.clear()
        self._threads.clear()

        # Determine target sessions
        if config.session_ids:
            sessions = [
                self._sm.get_session(sid)
                for sid in config.session_ids
                if self._sm.get_session(sid)
            ]
        else:
            sessions = self._sm.active_sessions

        if not sessions:
            logger.warning("No active sessions to broadcast to")
            self._running = False
            return

        # Engineer the initial prompt
        engineered = engineer_prompt(
            task=config.task,
            build_target=config.build_target,
            enhancements=config.enhancements,
            context=config.context,
        )

        if self._on_status:
            names = ", ".join(s.ai_profile.name for s in sessions)
            self._on_status(f"Broadcasting to {len(sessions)} sessions: {names}")

        logger.info("Broadcasting to %d sessions: %s",
                     len(sessions),
                     [s.display_name for s in sessions])

        # Model switching is done manually by the user before broadcast.
        # Auto-switching was unreliable (typed model names into chat input).
        # The UI shows a reminder: "Pick a different model on each window first."

        # Launch a thread per session
        for session in sessions:
            if not session.is_configured:
                logger.warning("Skipping unconfigured session: %s", session.display_name)
                continue

            t = threading.Thread(
                target=self._session_loop,
                args=(session, config, engineered),
                daemon=True,
            )
            self._threads.append(t)
            t.start()

    def stop(self) -> None:
        """Stop all broadcast loops."""
        self._stop_event.set()
        self._running = False

        # Stop all session executors
        for session in self._sm.sessions:
            if session.client:
                session.client.cancel()

        logger.info("Broadcast stopped")
        if self._on_complete:
            self._on_complete(dict(self._iteration_counts))

    def _save_result(self, session, task: str, iteration: int,
                     focus: str, result: str, start_time: float) -> None:
        """Save an iteration's actual result to Downloads."""
        try:
            title = f"{task[:40]}_iter{iteration}_{focus.replace(' ', '_')}"
            path = save_task_output(
                title=title,
                output=result,
                ai_name=session.ai_profile.name,
                corner=session.corner,
                elapsed_seconds=time.time() - start_time,
                iterations=iteration,
            )
            if path and self._on_status:
                self._on_status(f"Saved: {path.name}")
        except Exception as e:
            logger.warning("Auto-save failed for %s: %s", session.display_name, e)

    def _session_loop(self, session, config: BroadcastConfig, initial_prompt: str) -> None:
        """Run the endless improvement loop for one session."""
        sid = session.session_id
        ai_name = session.ai_profile.name
        self._iteration_counts[sid] = 0
        start_time = time.time()

        try:
            # Iteration 0: Initial build with engineered prompt
            if self._stop_event.is_set():
                return

            if self._on_output:
                self._on_output(
                    sid, "system",
                    f"[{ai_name}] Starting: {config.task}\n"
                    f"{'='*50}\n"
                )

            result = session.client.generate(
                prompt=initial_prompt,
                system_instruction=(
                    "You are an expert coding assistant. Write clean, complete, "
                    "production-ready code. No placeholders."
                ),
                on_progress=lambda t, s=sid: (
                    self._on_output(s, "code", t) if self._on_output else None
                ),
            )

            # Store actual result and auto-save
            self._results[sid] = result
            if self._on_output:
                self._on_output(sid, "result", result)
            self._save_result(session, config.task, 1, "Initial Build", result, start_time)

            self._iteration_counts[sid] = 1
            if self._on_iteration:
                self._on_iteration(sid, 1, "Initial Build", ai_name)

            # Improvement loop
            iteration = 1
            while not self._stop_event.is_set():
                # Check limits
                if iteration >= config.max_iterations:
                    break
                if config.time_limit_minutes > 0:
                    elapsed_min = (time.time() - start_time) / 60
                    if elapsed_min >= config.time_limit_minutes:
                        break

                improvement = engineer_improvement_prompt(
                    task=config.task,
                    iteration=iteration,
                    ai_name=ai_name,
                )

                focus_names = [
                    "Add Features", "Professional Polish",
                    "Robustness", "Performance", "Final Review & Expand"
                ]
                focus = focus_names[iteration % len(focus_names)]

                if self._on_output:
                    self._on_output(
                        sid, "system",
                        f"\n[{ai_name}] Improvement #{iteration + 1}: {focus}\n"
                        f"{'-'*40}\n"
                    )

                try:
                    result = session.client.generate(
                        prompt=improvement,
                        on_progress=lambda t, s=sid: (
                            self._on_output(s, "code", t)
                            if self._on_output else None
                        ),
                    )
                except Exception as e:
                    logger.warning("[%s] Improvement failed: %s", ai_name, e)
                    if self._on_output:
                        self._on_output(sid, "error", f"Error: {e}\n")
                    time.sleep(5)
                    continue

                # Store actual result and auto-save
                self._results[sid] = result
                if self._on_output:
                    self._on_output(sid, "result", result)
                iteration += 1
                self._save_result(session, config.task, iteration, focus, result, start_time)

                self._iteration_counts[sid] = iteration
                if self._on_iteration:
                    self._on_iteration(sid, iteration, focus, ai_name)

        except InterruptedError:
            logger.info("[%s] Broadcast cancelled", ai_name)
        except Exception as e:
            logger.error("[%s] Broadcast error: %s", ai_name, e)
            if self._on_output:
                self._on_output(sid, "error", f"[{ai_name}] Fatal: {e}\n")
        finally:
            count = self._iteration_counts.get(sid, 0)
            elapsed = time.time() - start_time
            logger.info("[%s] Broadcast loop ended: %d iterations in %.0fs",
                         ai_name, count, elapsed)
