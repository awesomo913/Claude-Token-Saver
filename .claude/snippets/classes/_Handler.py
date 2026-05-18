# From: claude_backend/http_server.py:496
# Minimal request router.

class _Handler(BaseHTTPRequestHandler):
    """Minimal request router."""

    # Silence default per-request stderr logging.
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        logger.debug("%s - %s", self.client_address[0], format % args)

    def _send_json(self, code: int, payload: dict, origin: str = "") -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if origin and _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _handle_options(self) -> None:
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        if origin and _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle_options()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        origin = self.headers.get("Origin", "")
        if path == "/health":
            self._send_json(200, {"ok": True, "version": VERSION}, origin)
        elif path == "/projects":
            try:
                projects = list_recent_projects(limit=RECENT_PROJECTS_LIMIT)
                self._send_json(200, {"projects": projects}, origin)
            except Exception as e:
                logger.exception("/projects failed")
                self._send_json(500, {"error": str(e)}, origin)
        else:
            self._send_json(404, {"error": "not found"}, origin)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        origin = self.headers.get("Origin", "")

        if not _origin_allowed(origin):
            self._send_json(403, {"error": "origin not allowed"}, "")
            return

        if path != "/improve":
            self._send_json(404, {"error": "not found"}, origin)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            data = json.loads(raw) if raw else {}
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {"error": f"bad JSON: {e}"}, origin)
            return

        prompt = str(data.get("prompt", ""))
        project_path = str(data.get("project_path", ""))
        intent_hint = str(data.get("intent_hint", ""))

        if not prompt.strip():
            self._send_json(400, {"error": "prompt is empty"}, origin)
            return

        try:
            result = run_improve_pipeline(prompt, project_path, intent_hint)
        except Exception as e:
            logger.exception("/improve pipeline failed")
            self._send_json(500, {"error": str(e)}, origin)
            return

        # Write pending file for GUI; spawn GUI if needed.
        write_pending({
            "kind": "improve_request",
            "ts": datetime.now().isoformat(timespec="seconds"),
            "original_prompt": prompt,
            "project_path": project_path,
            **result,
        })
        # Belt-and-braces grant: even if the overlay process didn't
        # call AllowSetForegroundWindow first (e.g. Chrome extension
        # path), the tray process gets a chance here to permit the
        # GUI to raise. Cheap no-op when the call has no effect.
        _allow_foreground_steal()
        gui_ok = ensure_gui_running()

        result["builder_opened"] = gui_ok
        self._send_json(200, result, origin)
