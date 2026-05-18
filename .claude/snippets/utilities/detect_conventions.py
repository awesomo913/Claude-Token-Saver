# From: claude_backend/analyzers/pattern_detector.py:15
# Analyze Python files to detect coding conventions.

def detect_conventions(entries: list[FileEntry]) -> ConventionReport:
    """Analyze Python files to detect coding conventions."""
    py_files = [e for e in entries if e.ext == ".py"]
    samples = py_files[:MAX_SAMPLES]

    if not samples:
        return ConventionReport(samples_analyzed=0)

    counts = {
        "pathlib": 0, "os_path": 0,
        "type_hints": 0, "no_type_hints": 0,
        "f_string": 0, "format_method": 0, "percent_format": 0,
        "specific_except": 0, "bare_except": 0, "broad_except": 0,
        "logging_module": 0, "print_calls": 0,
        "absolute_import": 0, "relative_import": 0,
    }

    for entry in samples:
        try:
            tree = ast.parse(entry.content)
        except SyntaxError:
            continue
        _analyze_tree(tree, entry.content, counts)

    report = ConventionReport(samples_analyzed=len(samples))
    report.path_style = _classify(counts["pathlib"], counts["os_path"], "pathlib", "os.path")
    report.type_hints = _classify_presence(counts["type_hints"], counts["no_type_hints"], "heavy", "light", "none")
    report.string_format = _classify_multi(
        ("f-string", counts["f_string"]),
        ("format", counts["format_method"]),
        ("percent", counts["percent_format"]),
    )
    report.error_handling = _classify_multi(
        ("specific", counts["specific_except"]),
        ("bare", counts["bare_except"]),
        ("broad", counts["broad_except"]),
    )
    report.logging_style = _classify(counts["logging_module"], counts["print_calls"], "logging", "print")
    report.import_style = _classify(counts["absolute_import"], counts["relative_import"], "absolute", "relative")
    report.details = counts

    return report
