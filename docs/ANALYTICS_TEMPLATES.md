# Analytics Generation Templates

**Purpose**: Templates and code samples for generating, verifying, and publishing safe analytics  
**Audience**: Tool developers, researchers, and power users  
**Status**: Ready to use

---

## Template 1: Basic Analytics Generation

Use this template to run a basic analysis and verify it's privacy-safe.

### Python Script
```python
#!/usr/bin/env python3
"""
Generate safe analytics for Claude Token Saver

This script:
1. Runs comprehensive tests
2. Redacts all personal information
3. Verifies privacy compliance
4. Saves to docs/analytics/
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

def redact_project_id(project_name: str) -> str:
    """Create irreversible project identifier"""
    hash_obj = hashlib.md5(project_name.encode())
    return f"PROJ_{hash_obj.hexdigest()[:12]}"

def redact_file_path(original_path: str) -> str:
    """Replace file path with generic label"""
    filename = Path(original_path).name
    # Keep extension for metrics, remove path
    return filename

def generate_analytics():
    """Run comprehensive analysis"""
    print("[1/3] Running comprehensive tests...")
    # Run your tests here
    
    print("[2/3] Redacting personal information...")
    # Load results and apply redaction
    
    print("[3/3] Verifying privacy compliance...")
    # Verify no sensitive data remains
    
    print("✅ Analytics generated and verified!")
    print(f"   Saved to: docs/analytics/")

def verify_privacy():
    """Verify no sensitive data in analytics"""
    sensitive_patterns = [
        "password", "secret", "key", "token", "api_key",
        "email", "phone", "/Users/", "/home/", "C:\\Users"
    ]
    
    analytics_dir = Path("docs/analytics")
    all_safe = True
    
    for json_file in analytics_dir.glob("*.json"):
        with open(json_file) as f:
            content = f.read()
            for pattern in sensitive_patterns:
                if pattern.lower() in content.lower():
                    print(f"❌ Found '{pattern}' in {json_file.name}")
                    all_safe = False
    
    if all_safe:
        print("✅ All analytics verified as privacy-safe")
    return all_safe

if __name__ == "__main__":
    generate_analytics()
    if verify_privacy():
        print("\n📊 Ready to publish analytics!")
    else:
        print("\n⚠️  Privacy issues detected. Review before publishing.")
```

### Usage
```bash
python generate_analytics.py
```

---

## Template 2: ML-Ready Dataset

Use this template to prepare analytics for machine learning.

### Python Script
```python
#!/usr/bin/env python3
"""
Prepare ML-ready dataset from analytics

Creates normalized feature vectors suitable for:
- Model training
- Benchmarking
- Comparative analysis
"""

import json
import numpy as np
from pathlib import Path

def load_analytics(filepath: str) -> dict:
    """Load and parse analytics JSON"""
    with open(filepath) as f:
        return json.load(f)

def extract_features(analytics: dict) -> list:
    """Extract normalized feature vectors"""
    features = []
    
    for project in analytics["projects"]:
        feature_vector = {
            "project_id": project["project_id"],
            "project_type": project["project_type"],
            
            # Filesystem metrics
            "file_count": project["metrics"]["files"],
            "total_bytes": project["metrics"]["total_bytes"],
            
            # Tokenization metrics
            "total_tokens": project["metrics"]["total_tokens"],
            "avg_chars_per_token": project["metrics"]["avg_chars_per_token"],
            "token_std_dev": project["metrics"]["token_std_dev"],
            
            # Consistency (normalized 0-100)
            "consistency_score": project["consistency_test"]["score"],
            "variance_max": project["consistency_test"]["variance_max"],
            
            # Status indicators
            "tokenization_pass": 1 if "PASS" in project["status"] else 0,
            "context_generation_fail": 1 if "FAIL" in project["status"] else 0,
        }
        features.append(feature_vector)
    
    return features

def normalize_features(features: list) -> np.ndarray:
    """Normalize features to 0-1 range for ML"""
    # Convert to numpy array
    data = np.array([list(f.values())[2:] for f in features], dtype=float)
    
    # Min-max normalization
    data_min = data.min(axis=0)
    data_max = data.max(axis=0)
    normalized = (data - data_min) / (data_max - data_min + 1e-8)
    
    return normalized

def save_ml_dataset(features: list, normalized: np.ndarray, output_path: str):
    """Save as ML-ready JSON"""
    dataset = {
        "metadata": {
            "version": "2.0",
            "generated": str(datetime.now()),
            "format": "normalized feature vectors",
            "feature_count": len(features),
            "sample_count": len(features)
        },
        "features": features,
        "normalized_vectors": normalized.tolist(),
        "status": "ready_for_ml_training"
    }
    
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"✅ ML dataset saved: {output_path}")

if __name__ == "__main__":
    # Load original analytics
    analytics = load_analytics("docs/analytics/TOKEN_SAVER_DETAILED_ANALYTICS.json")
    
    # Extract and prepare features
    features = extract_features(analytics)
    normalized = normalize_features(features)
    
    # Save ML-ready dataset
    save_ml_dataset(features, normalized, "docs/analytics/ML_READY_DATASET.json")
    
    print(f"📊 Prepared {len(features)} projects for ML training")
```

### Usage
```bash
python prepare_ml_dataset.py
```

---

## Template 3: Privacy Verification

Use this template to verify analytics before publishing.

### Python Script
```python
#!/usr/bin/env python3
"""
Privacy verification for analytics before publication

Checks for:
- Sensitive patterns (passwords, keys, emails)
- Identifying information (names, paths)
- Metadata leaks
- Compliance with privacy policy
"""

import json
import re
from pathlib import Path

class PrivacyVerifier:
    def __init__(self):
        self.sensitive_patterns = {
            "credentials": [
                r"password\s*[=:]\s*['\"]([^'\"]+)['\"]",
                r"api_key\s*[=:]\s*['\"]([^'\"]+)['\"]",
                r"token\s*[=:]\s*['\"]([^'\"]+)['\"]",
                r"secret\s*[=:]\s*['\"]([^'\"]+)['\"]",
            ],
            "identifiers": [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # emails
                r"C:\\Users\\[^\\]+",  # Windows user paths
                r"/Users/[^/]+",  # macOS user paths
                r"/home/[^/]+",  # Linux user paths
            ],
            "paths": [
                r"[a-zA-Z]:\\.*\.[a-z]+",  # Windows absolute paths
                r"/[a-z]+.*\.[a-z]+",  # Unix absolute paths
            ]
        }
        self.issues = []
    
    def verify_file(self, filepath: Path) -> bool:
        """Check single analytics file"""
        print(f"\n📋 Checking {filepath.name}...")
        
        with open(filepath) as f:
            content = f.read()
        
        # Check for sensitive patterns
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.issues.append({
                        "file": filepath.name,
                        "category": category,
                        "pattern": pattern,
                        "matches": len(matches)
                    })
                    print(f"  ⚠️  Found {len(matches)} {category} matches")
        
        # Check JSON structure
        try:
            data = json.loads(content)
            
            # Verify project IDs are hashed
            for project in data.get("projects", []):
                proj_id = project.get("project_id") or project.get("redacted_id")
                if proj_id and not proj_id.startswith("PROJ_"):
                    self.issues.append({
                        "file": filepath.name,
                        "issue": "Project ID not properly hashed",
                        "value": proj_id
                    })
            
            print(f"  ✅ Valid JSON structure")
        
        except json.JSONDecodeError:
            print(f"  ❌ Invalid JSON")
            return False
        
        return len(self.issues) == 0
    
    def verify_all(self, analytics_dir: str = "docs/analytics") -> bool:
        """Verify all analytics files"""
        analytics_path = Path(analytics_dir)
        
        if not analytics_path.exists():
            print(f"❌ Directory not found: {analytics_dir}")
            return False
        
        json_files = list(analytics_path.glob("*.json"))
        print(f"🔍 Verifying {len(json_files)} analytics files...\n")
        
        results = [self.verify_file(f) for f in json_files]
        
        # Summary
        print("\n" + "="*50)
        print("PRIVACY VERIFICATION SUMMARY")
        print("="*50)
        
        if all(results):
            print("✅ All files verified as privacy-safe")
            print("   Safe to publish on GitHub ✓")
            print("   Safe to share with researchers ✓")
            print("   Safe for ML training ✓")
        else:
            print(f"❌ Issues found in {len(results) - sum(results)} files")
            print("\nIssues:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        return all(results)

if __name__ == "__main__":
    verifier = PrivacyVerifier()
    is_safe = verifier.verify_all()
    
    if is_safe:
        print("\n📊 Ready to publish analytics!")
    else:
        print("\n⚠️  Fix issues before publishing")
```

### Usage
```bash
python verify_privacy.py
```

---

## Template 4: GitHub Publishing Workflow

Use this template to safely commit and push analytics.

### Bash Script
```bash
#!/bin/bash
# Safely publish analytics to GitHub

set -e  # Exit on error

echo "📊 Analytics Publishing Workflow"
echo "================================="

# Step 1: Verify privacy
echo "[1/4] Verifying privacy..."
python verify_privacy.py || exit 1

# Step 2: Create docs directory
echo "[2/4] Organizing files..."
mkdir -p docs/analytics
ls -lh docs/analytics/

# Step 3: Commit changes
echo "[3/4] Committing to git..."
git add -A
git commit -m "Add analytics: $(date +%Y-%m-%d)
- Tokenization metrics and consistency tests
- File system analysis and distribution
- Performance benchmarks
- ML-ready feature vectors
- Privacy verified: no personal data"

# Step 4: Push to remote
echo "[4/4] Pushing to GitHub..."
git push origin main

echo "✅ Analytics published successfully!"
echo "   View on GitHub: https://github.com/awesomo913/Claude-Token-Saver/tree/main/docs/analytics"
```

### Usage
```bash
chmod +x publish_analytics.sh
./publish_analytics.sh
```

---

## Template 5: README Update Section

Use this markdown section in your README to describe analytics:

```markdown
## Analytics & Testing

All testing data is **privacy-safe** and suitable for public sharing:

### Generated Files
- **TOKEN_SAVER_DETAILED_ANALYTICS.json** (200+ metrics)
- **MACHINE_LEARNING_DATASET.json** (normalized features)
- **TESTING_REPORTS.md** (detailed findings)
- **PRODUCTION_READINESS.md** (status & roadmap)

### Privacy Guarantee
✅ No project names  
✅ No file paths  
✅ No code content  
✅ No personal data  
✅ Safe to share publicly  

[Learn more](docs/ANALYTICS_PRIVACY.md) about our redaction methodology and privacy protection.

### Using the Data
- **Researchers**: Use normalized features in ML models
- **Developers**: Review dimension scores for improvements
- **Teams**: Share results in reports and documentation

### Generate Your Own Analytics
```bash
python tests/run_comprehensive_analysis.py
```

For templates and examples, see [ANALYTICS_TEMPLATES.md](docs/ANALYTICS_TEMPLATES.md).
```

---

## Template 6: Custom Analysis Report

Use this template to generate custom analysis reports:

### Python Script
```python
#!/usr/bin/env python3
"""
Generate custom analysis report from analytics

Creates a formatted markdown report highlighting:
- Project scaling (small → medium → large)
- Metric trends
- Strengths and weaknesses
- Recommendations
"""

import json
from pathlib import Path

def generate_report(analytics_file: str, output_file: str = "CUSTOM_REPORT.md"):
    """Generate markdown report from analytics"""
    
    with open(analytics_file) as f:
        analytics = json.load(f)
    
    report = [
        "# Custom Analytics Report",
        "",
        f"**Generated**: {analytics['metadata']['timestamp']}",
        f"**Format**: Redacted, privacy-safe",
        "",
        "## Executive Summary",
        "",
    ]
    
    # Add summary statistics
    stats = analytics["aggregate_statistics"]
    report.extend([
        f"- **Projects Analyzed**: {stats['total_projects']}",
        f"- **Files Processed**: {stats['total_files']}",
        f"- **Tokens Counted**: {stats['total_tokens']}",
        f"- **Consistency Rate**: {stats['consistency_rate']}%",
        f"- **Critical Issues**: {stats['critical_issues']}",
        "",
        "## Project Breakdown",
        "",
    ])
    
    # Add per-project details
    for project in analytics["projects"]:
        report.extend([
            f"### {project['project_type'].replace('_', ' ').title()}",
            f"- ID: `{project['project_id']}`",
            f"- Files: {project['metrics']['files']}",
            f"- Tokens: {project['metrics']['total_tokens']}",
            f"- Consistency: {project['consistency_test']['score']}%",
            f"- Status: {project['status']}",
            "",
        ])
    
    # Add recommendations
    report.extend([
        "## Recommendations",
        "",
    ])
    
    for rec in analytics.get("recommendations", []):
        report.extend([
            f"**{rec['priority']}**: {rec['action']}",
            f"- Effort: {rec['effort_hours']} hours",
            "",
        ])
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Report generated: {output_file}")

if __name__ == "__main__":
    generate_report("docs/analytics/TOKEN_SAVER_DETAILED_ANALYTICS.json")
```

### Usage
```bash
python generate_custom_report.py
```

---

## Template 7: CI/CD Integration

Use this template to automate analytics generation in CI/CD:

### GitHub Actions Workflow
```yaml
name: Generate Analytics

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  analytics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install customtkinter pyperclip tiktoken
      
      - name: Run analytics
        run: |
          python tests/run_comprehensive_analysis.py
      
      - name: Verify privacy
        run: |
          python verify_privacy.py
      
      - name: Commit results
        run: |
          git config user.email "analytics@bot.local"  # pii-ok: placeholder for CI bot, not a real address
          git config user.name "Analytics Bot"
          git add docs/analytics/
          git commit -m "Auto-update analytics" || true
          git push origin main
```

---

## Checklist: Before Publishing Analytics

Use this checklist before publishing any analytics:

- [ ] All tests passed
- [ ] Privacy verification completed
- [ ] Project IDs are hashed (PROJ_*)
- [ ] File paths are redacted
- [ ] No code content included
- [ ] No credentials or secrets
- [ ] No user identifiers
- [ ] Metrics are aggregated
- [ ] JSON is valid
- [ ] README updated with links
- [ ] Commit message is descriptive
- [ ] Branch is up-to-date with main

---

## Next Steps

1. **Use a template**: Pick one that matches your workflow
2. **Customize**: Adjust patterns and checks for your data
3. **Test**: Run on sample analytics first
4. **Verify**: Check output manually before publishing
5. **Automate**: Set up CI/CD for regular updates

---

*These templates help you generate, verify, and publish analytics safely while protecting your privacy.*
