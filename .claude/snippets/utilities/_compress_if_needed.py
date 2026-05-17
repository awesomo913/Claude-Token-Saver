# From: claude_backend/gui.py:1253
# If queued code exceeds MAX_PROMPT_TOKENS, compress large blocks to signatures.

    def _compress_if_needed(self) -> None:
        """If queued code exceeds MAX_PROMPT_TOKENS, compress large blocks to signatures."""
        total = sum(count_tokens(q["content"]) for q in self._context_queue)
        if total <= self.MAX_PROMPT_TOKENS:
            return

        # Sort queue items by size (biggest first) and compress the biggest
        sized = sorted(enumerate(self._context_queue), key=lambda x: -len(x[1]["content"]))
        for idx, item in sized:
            if total <= self.MAX_PROMPT_TOKENS:
                break
            content = item["content"]
            old_tokens = count_tokens(content)
            if old_tokens < 100:
                continue  # already small

            # Compress: keep first 5 lines + "# ... (N more lines)" + last 3 lines
            lines = content.splitlines()
            if len(lines) > 15:
                compressed = "\n".join(lines[:5])
                compressed += f"\n# ... ({len(lines) - 8} more lines, use Read tool to see full file)\n"
                compressed += "\n".join(lines[-3:])
                self._context_queue[idx]["content"] = compressed
                total -= old_tokens - count_tokens(compressed)
