# From: claude_backend/tray.py:142
# Run prep on current working directory. Notify on completion.

def _run_prep(icon: "pystray.Icon") -> None:
    """Run prep on current working directory. Notify on completion."""
    cwd = Path.cwd()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "claude_backend", "prep", str(cwd), "--quiet"],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode == 0:
            icon.notify("Prep complete", f"Refreshed context for {cwd.name}")
        else:
            icon.notify("Prep failed", "Check logs for details")
    except subprocess.TimeoutExpired:
        icon.notify("Prep timed out", "Aborted after 2 minutes")
    except OSError as e:
        icon.notify("Prep error", str(e))
