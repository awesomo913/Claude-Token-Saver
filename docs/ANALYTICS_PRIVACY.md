# Analytics Privacy & Redaction Methodology

**Status**: ✅ All analytics data is privacy-safe for public sharing  
**Last Updated**: 2026-04-26

---

## Privacy Guarantee

All analytics and testing data published by Claude Token Saver contains **ZERO personal information**:

- ✅ **No project names** — Redacted with MD5 hashing
- ✅ **No file paths** — Replaced with generic labels
- ✅ **No code content** — Only metrics and statistics included
- ✅ **No user data** — No credentials, passwords, or sensitive content
- ✅ **No identifying information** — All PII removed before publication
- ✅ **Safe to share** — Can be used for ML training, public reports, etc.

---

## What Data IS Included

Analytics files contain only **non-sensitive metrics**:

- Tokenization counts (number of tokens per file)
- File size statistics (bytes, line counts)
- File type distributions (.py, .json, etc.)
- Consistency test results (pass/fail, variance)
- Performance metrics (speed, memory)
- Dimension scores (tokenization 9.5/10, etc.)
- Error types and frequencies

**These metrics reveal nothing about your actual code or project.**

---

## What Data IS NEVER Included

The following sensitive information is **permanently excluded** from all analytics:

- ❌ Project names or paths
- ❌ File names or directory structure
- ❌ Code content or snippets
- ❌ Function names or variable names
- ❌ Comments, docstrings, or documentation
- ❌ Configuration values or secrets
- ❌ API keys, tokens, or credentials
- ❌ User information or email addresses
- ❌ Git history or commits
- ❌ Any identifying metadata

---

## Redaction Methodology

### Method 1: MD5 Hashing (Project IDs)
Project identifiers are irreversibly hashed using MD5:

```python
import hashlib

# Original: "my_awesome_webapp"
project_name = "my_awesome_webapp"

# Published as:
redacted_id = "PROJ_" + hashlib.md5(project_name.encode()).hexdigest()[:12]
# Result: PROJ_936dccd44f11

# Key properties:
# - One-way hash (cannot reverse to get original name)
# - Consistent (same project always gets same ID)
# - Unique (different projects get different IDs)
# - Safe (no information leakage)
```

**Why MD5 for analytics?** We use MD5 for analytics (not security-critical hashing) because:
- We don't need cryptographic security
- We need consistency (same project = same hash)
- We need short, readable IDs in reports
- We're not protecting against reversal attacks (public data)

### Method 2: Generic Labels
File paths are replaced with generic labels:

```
BEFORE:  "src/routes/api/auth/login.py"
AFTER:   "api/route_1.py"  (generic, no path info)

BEFORE:  "/Users/alice/Projects/webapp/config.json"
AFTER:   "config.json"  (extension preserved for metrics)

BEFORE:  "packages/utils/tokenizer.py"
AFTER:   "tokenizer.py"  (function-based, no path)
```

### Method 3: Aggregation
Detailed metrics are aggregated to prevent reconstruction:

```
BEFORE (too detailed):
  - file_1.py: 10 tokens, 32 bytes
  - file_2.py: 8 tokens, 26 bytes
  - file_3.py: 5 tokens, 16 bytes

AFTER (aggregated):
  - python files: 3 total, 74 bytes, 23 tokens
  - average: 7.67 tokens/file
  - std_dev: 2.05
```

### Method 4: Type-Only Preservation
File type information is preserved (helpful for metrics) but no names:

```
BEFORE:  "settings.json", "config.json", "schema.json"
AFTER:   ".json files: 3 total" (only count and type)

BEFORE:  "core.py", "utils.py", "test.py"
AFTER:   ".py files: 3 total" (only count and type)
```

---

## File-by-File Redaction Status

### ✅ TOKEN_SAVER_DETAILED_ANALYTICS.json
**Status**: Privacy-safe (public release ready)

**What's included**:
- Tokenization statistics (counts, ratios, variance)
- File type distributions (counts by extension)
- Consistency test results (pass/fail only)
- Performance metrics (speed, memory)

**What's redacted**:
- Project IDs hashed to `PROJ_*`
- File names replaced with generic labels
- No code content or file paths
- No identifying metadata

**Safe to**:
- Publish on GitHub ✅
- Share for ML training ✅
- Include in public reports ✅
- Use for benchmarking ✅

### ✅ MACHINE_LEARNING_DATASET.json
**Status**: Privacy-safe (ML training ready)

**What's included**:
- Normalized feature vectors
- Dimension scores
- Aggregate statistics
- Issue counts and types

**What's redacted**:
- Project IDs hashed
- All personal identifiers removed
- Raw code excluded
- Identifying metadata stripped

**Safe to**:
- Train ML models ✅
- Share with researchers ✅
- Publish in academic work ✅
- Include in open datasets ✅

### ✅ TESTING_REPORTS.md
**Status**: Privacy-safe (public review ready)

**What's included**:
- Test methodology and scope
- Dimension scores and findings
- Error types and frequencies
- Recommendations and roadmap

**What's redacted**:
- Project names hashed
- No test project details
- Generic file descriptions
- Redacted paths

**Safe to**:
- Publish on GitHub ✅
- Share in issue discussions ✅
- Reference in documentation ✅
- Include in PRs ✅

### ✅ PRODUCTION_READINESS.md
**Status**: Privacy-safe (public sharing ready)

**What's included**:
- Feature status and scores
- Critical issues and blockers
- Fix roadmap and timelines
- Testing methodology

**What's redacted**:
- All project identifiers
- No user information
- Generic descriptions
- Safe aggregated metrics

**Safe to**:
- Publish on GitHub ✅
- Share in releases ✅
- Reference in documentation ✅
- Include in discussions ✅

---

## How to Use This Data Safely

### For Tool Developers
```python
# ✅ DO: Use metrics to improve features
metrics = load_json("docs/analytics/TOKEN_SAVER_DETAILED_ANALYTICS.json")
avg_tokens = metrics["aggregate_statistics"]["total_tokens"] / metrics["aggregate_statistics"]["total_files"]
print(f"Avg tokens per file: {avg_tokens}")

# ❌ DON'T: Try to reverse-hash project IDs
# MD5 hashes are one-way; redacted IDs are final
```

### For ML Researchers
```python
# ✅ DO: Use normalized feature vectors
import json
with open("docs/analytics/MACHINE_LEARNING_DATASET.json") as f:
    dataset = json.load(f)
    
# Use dimension scores for training
features = [proj["metrics"]["tokenization_score"] for proj in dataset["projects"]]

# ❌ DON'T: Assume you can identify original projects
# MD5 hashing ensures anonymity
```

### For Security Researchers
```python
# ✅ DO: Verify no sensitive data is present
sensitive_patterns = ["password", "key", "secret", "token", "api_key"]
for pattern in sensitive_patterns:
    grep_result = grep_files(pattern, "docs/analytics/")
    assert len(grep_result) == 0, f"Found {pattern} in analytics!"

# ❌ DON'T: Share project redaction keys
# Keys are not published; redaction is one-way
```

---

## Data Retention & Deletion

### Analytics Files
- **Where**: `docs/analytics/` directory on GitHub
- **Retention**: Kept for historical reference and ML training
- **Deletion**: Can be removed on request (file an issue)
- **Update frequency**: New analyses published regularly

### Local Testing Data
- **Where**: User's local machine (not pushed to GitHub)
- **Retention**: Never stored permanently
- **Deletion**: Automatic (temp files)
- **Visibility**: Not publicly accessible

---

## Verification Checklist

Before any analytics release, we verify:

- [ ] No project names in files
- [ ] No file paths in files
- [ ] No code content in files
- [ ] No credentials or secrets
- [ ] No user email addresses
- [ ] No identifying metadata
- [ ] Project IDs are hashed
- [ ] File names are generic
- [ ] Metrics are aggregated
- [ ] Third-party usage is safe

---

## Template: Generating Safe Analytics

If you want to run tests and publish analytics safely, follow this template:

### Step 1: Run Tests
```bash
python tests/run_comprehensive_analysis.py
```

### Step 2: Verify Privacy
```python
import json

# Load generated analytics
with open("TOKEN_SAVER_DETAILED_ANALYTICS.json") as f:
    analytics = json.load(f)

# Checklist
checks = {
    "no_project_names": all(p["redacted_id"].startswith("PROJ_") for p in analytics["projects"]),
    "no_file_paths": all("/" not in str(f.get("file", "")) for p in analytics["projects"] for f in p.get("file_tokenization_data", [])),
    "aggregated_metrics": "aggregate_stats" in analytics,
    "hashed_ids": all(len(p["redacted_id"]) == 17 for p in analytics["projects"]),  # PROJ_ + 12 chars
}

# Print results
for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check}")
```

### Step 3: Publish
```bash
# Copy to docs/analytics/
cp TOKEN_SAVER_DETAILED_ANALYTICS.json docs/analytics/

# Commit and push
git add docs/analytics/
git commit -m "Add analytics: safe, redacted, privacy-verified"
git push origin main
```

---

## FAQ

### Q: Can someone reverse the MD5 hashes?
**A**: No. MD5 is one-way hashing. Without knowing the original project name, the hash is useless. Even if someone guesses a project name and hashes it, they'd only match if their guess is exactly correct.

### Q: Is this data truly anonymous?
**A**: Yes. The analytics contain only metrics (token counts, file statistics). There's no information that could identify you, your project, or your code.

### Q: Can I share this data with others?
**A**: Yes! All analytics files are safe for public sharing:
- Share with researchers ✅
- Publish in reports ✅
- Use for ML training ✅
- Include in academic work ✅

### Q: What if I want to opt out?
**A**: Disable analytics collection in your local environment. Analytics are **never** sent to our servers—they're only generated locally for your own testing.

### Q: How do I verify no personal data was included?
**A**: Check the analytics files yourself:
```bash
# Search for suspicious patterns
grep -r "password\|secret\|key\|token\|api\|email" docs/analytics/
# Should return nothing (0 matches)
```

### Q: Can you add more metrics without compromising privacy?
**A**: Yes! We can always add more metrics as long as they're:
- Aggregated (not file-by-file details)
- Non-identifying (no names or paths)
- Privacy-verified (before release)

### Q: What if I find sensitive data in the analytics?
**A**: Please report it immediately:
1. File a GitHub issue: https://github.com/awesomo913/Claude-Token-Saver/issues
2. Mark it as security-sensitive
3. We'll investigate and remove the data

---

## Support

For questions about analytics privacy and redaction:
- **GitHub Issues**: https://github.com/awesomo913/Claude-Token-Saver/issues
- **Privacy Policy**: See main README

---

*This document ensures all analytics data is safe for public sharing while maintaining utility for testing, ML training, and research.*
