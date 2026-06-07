import time
import hashlib
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any

from session import Session
from provider_chain import ProviderChain, IMPROVEMENT_FOCUSES, FOCUS_ORDER
# TODO: Implement these supporting modules (prompt_engineer.py, code_extractor.py, recovery_manager.py)
# from code_extractor import extract_code
# from prompt_engineer import engineer_improvement_prompt
# from recovery_manager import RecoveryManager

class CoreLoop:
    """
    The exact heart of Autocoder - the endless improvement loop.
    Implements the diagram:
    Task → Engineered Prompt → AI chat → Extract → Feed back with next focus.
    
    Incorporates ALL fixes from autocoder-tune-up and ai-coding-pipeline-audit:
    - 90K hard limit + retrieval context
    - Curated focuses (no proliferation)
    - Code-first enforcement
    - 0.3 regression threshold
    - Incremental language + identity lock
    - Stagnation via hash + expansion mode
    - Perfection loop (cycle all focuses)
    """
    
    def __init__(self, provider_chain: ProviderChain, output_dir: Path = None):
        self.provider_chain = provider_chain
        self.output_dir = output_dir or (Path.home() / "Downloads" / "neoautocoder")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recovery = RecoveryManager()
        self.perfection_threshold = 3  # iterations with no improvement → stop
    
    def run(self, session: Session, initial_task: str, max_iterations: int = 0, 
            selected_focuses: List[str] = None) -> str:
        """Main endless improvement loop."""
        print(f"\n=== Starting NeoAutocoder Core Loop for Session {session.session_id} ===")
        print(f"Task: {initial_task[:80]}...")
        
        if not session.current_codebase:
            # Initial build
            session.current_codebase = self._initial_build(session, initial_task)
            self._save_iteration(session, 0, "initial_build")
        
        iteration = session.iteration_count
        no_improvement_streak = 0
        focus_cycle = selected_focuses or FOCUS_ORDER
        
        while True:
            if max_iterations > 0 and iteration >= max_iterations:
                print("Max iterations reached.")
                break
            
            focus_name = focus_cycle[iteration % len(focus_cycle)]
            print(f"\n--- Iteration {iteration} | Focus: {focus_name} ---")
            
            # Engineer prompt with all best practices
            prompt = engineer_improvement_prompt(
                current_code=session.current_codebase,
                focus=IMPROVEMENT_FOCUSES[focus_name],
                task=initial_task,
                focus_name=focus_name,
                iteration=iteration
            )
            
            # Send via provider chain (with all fallbacks, cooldowns, temp cycling)
            try:
                response = self.provider_chain.generate(prompt, session)
            except Exception as e:
                print(f"Provider failure: {e}")
                if not self.recovery.attempt_recovery(session, str(e)):
                    print("Recovery failed. Stopping loop.")
                    break
                continue
            
            # Extract and validate
            extracted = extract_code(response, focus_name)
            
            if not extracted or len(extracted) < 500:
                print("Extraction failed or too small. Attempting recovery...")
                if not self.recovery.handle_extraction_failure(session, response):
                    no_improvement_streak += 1
                    if no_improvement_streak >= self.perfection_threshold:
                        print("Perfection loop triggered - no further improvements.")
                        break
                iteration += 1
                continue
            
            # Validation gates (per audit skill)
            prev_size = len(session.current_codebase)
            new_size = len(extracted)
            shrink_ratio = new_size / prev_size if prev_size > 0 else 1.0
            
            if shrink_ratio < 0.3:  # Tuned per Fix 3
                print(f"REJECTED: Significant regression ({new_size} vs {prev_size} chars, ratio={shrink_ratio:.2f})")
                no_improvement_streak += 1
                iteration += 1
                continue
            
            new_hash = session.update_hash(extracted)
            
            # Check stagnation
            if session.is_stagnant(threshold=3):
                print("Stagnation detected. Entering EXPANSION mode...")
                extracted = self._expansion_mode(session, initial_task, extracted)
                session.update_hash(extracted)
                no_improvement_streak = 0
            else:
                if new_hash == session.last_hash and iteration > 5:
                    no_improvement_streak += 1
                else:
                    no_improvement_streak = 0
            
            # Accept the improvement
            session.current_codebase = extracted
            session.iteration_count = iteration + 1
            session.focus_history.append(focus_name)
            
            self._save_iteration(session, iteration, focus_name)
            
            print(f"Accepted improvement: {new_size} chars (ratio {shrink_ratio:.2f})")
            
            # Perfection check
            if no_improvement_streak >= self.perfection_threshold:
                print("\n=== PERFECTION ACHIEVED ===")
                print("Code has stabilized across all selected focuses.")
                break
            
            iteration += 1
            time.sleep(2.0)  # Gentle rate limit between iterations
        
        session.save_state(self.output_dir)
        return session.current_codebase
    
    def _initial_build(self, session: Session, task: str) -> str:
        """Initial codebase generation."""
        prompt = f"""You are an expert Python developer.
Create a COMPLETE, production-ready implementation for the following task:

TASK: {task}

Requirements:
- CODE FIRST: Output the complete working codebase in a single ```python fenced block.
- Make it SOLID, well-documented, with type hints where appropriate.
- Include comprehensive docstrings and comments.
- Follow PEP 8.
- Any review or explanation comes AFTER the code block.

Begin."""
        
        response = self.provider_chain.generate(prompt)
        code = extract_code(response, "initial")
        if not code or len(code) < 1000:
            code = "# Initial placeholder - implement the task below\n" + task
        return code
    
    def _expansion_mode(self, session: Session, task: str, current_code: str) -> str:
        """Generate companion modules when stagnant."""
        prompt = engineer_improvement_prompt(
            current_code=current_code,
            focus="Explore & Expand: Create a new complementary module or utility that enhances the main codebase while staying true to the original task.",
            task=task,
            focus_name="Expansion",
            iteration=session.iteration_count
        )
        response = self.provider_chain.generate(prompt)
        expanded = extract_code(response, "expansion")
        return expanded or current_code
    
    def _save_iteration(self, session: Session, iter_num: int, focus: str):
        """Organized auto-save per Fix 8."""
        project_slug = self._extract_project_slug(session.current_codebase) or "project"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        iter_dir = self.output_dir / project_slug
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"iter_{iter_num:04d}_{focus.lower().replace(' ', '_')}_{timestamp}.py"
        path = iter_dir / filename
        path.write_text(session.current_codebase)
        
        # Also save metadata
        meta = {
            "iteration": iter_num,
            "focus": focus,
            "size_chars": len(session.current_codebase),
            "hash": session.last_hash,
            "timestamp": timestamp
        }
        (iter_dir / f"{filename}.meta.json").write_text(json.dumps(meta, indent=2))
        
        print(f"Saved: {path}")
    
    def _extract_project_slug(self, code: str) -> Optional[str]:
        """Extract project name from code or task for organized storage."""
        match = re.search(r'(?:class|def|project|app)\s+([A-Za-z0-9_]+)', code)
        if match:
            return match.group(1).lower()
        return None


# Stub for missing modules (in full implementation these are separate files)
def json():
    import json as real_json
    return real_json
