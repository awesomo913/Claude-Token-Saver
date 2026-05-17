# From: claude_backend/gui.py:1543
# Assemble the final prompt.

    def _assemble(self, mode: str = "smart") -> str:
        """Assemble the final prompt.

        Modes:
            'smart' — uses Prompt Architect logic (role, constraints, quality gate)
            'template' — uses simple template wrapping
            'raw' — just snippets + request, no wrapping
        """
        items = ""
        for it in self._context_queue:
            items += f"### {it['name']} (from {it['source']})\n```\n{it['content'].strip()}\n```\n\n"
        request = self._get_request_text()
        if not items and not request:
            return ""

        if mode == "smart":
            # Get project conventions if available
            conventions = ""
            if self._analysis and self._analysis.conventions.samples_analyzed > 0:
                cv = self._analysis.conventions
                parts = []
                if cv.path_style != "unknown": parts.append(f"Path style: {cv.path_style}")
                if cv.type_hints != "unknown": parts.append(f"Type hints: {cv.type_hints}")
                if cv.logging_style != "unknown": parts.append(f"Logging: {cv.logging_style}")
                if cv.error_handling != "unknown": parts.append(f"Error handling: {cv.error_handling}")
                conventions = "\n".join(f"- {p}" for p in parts)

            return build_smart_prompt(
                request=request or "Work with the code context provided.",
                code_context=items.strip(),
                project_conventions=conventions,
            )
        elif mode == "template":
            t = TEMPLATES.get(self._tmpl.get(), "{items}\n\n{request}")
            return t.format(items=items.strip(), request=request).strip()
        else:  # raw
            parts = []
            if items.strip(): parts.append(items.strip())
            if request: parts.append(request)
            return "\n\n".join(parts)
