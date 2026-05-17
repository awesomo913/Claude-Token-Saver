# From: cdp_client.py:259
# Evaluate JavaScript in the page and return the result.

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
