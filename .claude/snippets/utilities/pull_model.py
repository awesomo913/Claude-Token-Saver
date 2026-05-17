# From: claude_backend/ollama_manager.py:201
# Download a model in a background thread. Streams progress.

    def pull_model(
        self,
        model_name: str,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Download a model in a background thread. Streams progress."""
        def _run():
            try:
                payload = json.dumps({"name": model_name, "stream": True}).encode()
                req = urllib.request.Request(
                    f"{self.host}/api/pull",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=600) as resp:
                    for line in resp:
                        try:
                            chunk = json.loads(line.decode("utf-8", errors="replace"))
                        except json.JSONDecodeError:
                            continue
                        status = chunk.get("status", "")
                        total = chunk.get("total", 0) or 0
                        completed = chunk.get("completed", 0) or 0
                        pct = (completed / total * 100) if total > 0 else 0
                        if on_progress:
                            on_progress(pct, status)
                if on_done:
                    on_done()
            except Exception as e:
                if on_error:
                    on_error(str(e))

        threading.Thread(target=_run, daemon=True).start()
