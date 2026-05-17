# From: claude_backend/ollama_manager.py:239
# Delete a locally installed model.

    def delete_model(self, model_name: str) -> bool:
        """Delete a locally installed model."""
        try:
            payload = json.dumps({"name": model_name}).encode()
            req = urllib.request.Request(
                f"{self.host}/api/delete",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="DELETE",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug("Failed to delete %s: %s", model_name, e)
            return False
