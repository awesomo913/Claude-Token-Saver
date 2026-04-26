# Documentation Directory

This directory contains comprehensive documentation about Claude Token Saver's testing, analytics, and privacy practices.

## Files in This Directory

### 📋 Analytics & Testing
- **`analytics/`** — Raw metrics and test data (JSON format)
  - `TOKEN_SAVER_DETAILED_ANALYTICS.json` — 200+ metrics across 3 projects
  - `MACHINE_LEARNING_DATASET.json` — Normalized feature vectors for ML training

### 📖 Documentation
- **`ANALYTICS_PRIVACY.md`** — Privacy guarantee and redaction methodology
  - What personal data is collected (✅ none)
  - What data IS included (metrics only)
  - How redaction works (MD5 hashing, aggregation, anonymization)
  - Verification checklist and templates
  - FAQ about data security

- **`ANALYTICS_TEMPLATES.md`** — Code templates and workflows
  - Template 1: Basic analytics generation
  - Template 2: ML-ready dataset preparation
  - Template 3: Privacy verification
  - Template 4: GitHub publishing workflow
  - Template 5: Custom analysis reports
  - Template 6: CI/CD integration
  - Template 7: Pre-publishing checklist

## Privacy Guarantee

✅ **All data in this directory is privacy-safe:**
- No project names (hashed)
- No file paths (redacted)
- No code content
- No credentials or secrets
- No personal information
- Safe to share publicly
- Safe for ML training
- Safe for academic research

## Using the Analytics

### For Developers
Review test results and dimension scores to understand tool capabilities:
```bash
cat ../PRODUCTION_READINESS.md  # Status and blockers
cat ../TESTING_REPORTS.md       # Detailed findings
```

### For Researchers
Use normalized feature vectors for ML training:
```python
import json
with open('analytics/MACHINE_LEARNING_DATASET.json') as f:
    data = json.load(f)  # Ready for model training
```

### For Tool Developers
Follow templates in `ANALYTICS_TEMPLATES.md` to:
- Generate your own analytics
- Verify privacy before publishing
- Publish safely to GitHub
- Set up automated reporting

## Privacy Verification

Before publishing any new analytics:
1. Run privacy verification (see `ANALYTICS_TEMPLATES.md`)
2. Verify no sensitive patterns found
3. Check project IDs are properly hashed
4. Confirm file paths are redacted
5. Review JSON structure

```bash
python verify_privacy.py
```

## Adding New Analytics

When generating new test results:
1. Redact project identifiers (use MD5 hashing)
2. Remove file paths (use generic labels)
3. Exclude code content
4. Aggregate detailed metrics
5. Verify privacy compliance
6. Update `docs/analytics/` directory
7. Commit with descriptive message

See `ANALYTICS_TEMPLATES.md` for code templates.

## Related Documentation

In the main repository:
- **`PRODUCTION_READINESS.md`** — Current tool status and fix roadmap
- **`TESTING_REPORTS.md`** — Detailed test results across 7 dimensions
- **`README.md`** — Project overview and quick links to analytics

## Questions?

- **Privacy**: See `ANALYTICS_PRIVACY.md`
- **Templates**: See `ANALYTICS_TEMPLATES.md`
- **Test Results**: See `../TESTING_REPORTS.md`
- **Status**: See `../PRODUCTION_READINESS.md`
- **Report Issues**: https://github.com/awesomo913/Claude-Token-Saver/issues

---

*All analytics and documentation in this directory are public, privacy-safe, and suitable for sharing.*
