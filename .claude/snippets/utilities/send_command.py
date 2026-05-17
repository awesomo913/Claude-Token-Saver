# From: cdp_client.py:222
# Send a CDP command and wait for the result.

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
