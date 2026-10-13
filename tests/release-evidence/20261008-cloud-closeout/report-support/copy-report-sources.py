#!/usr/bin/env python3
"""Copy a fixed, non-secret review/identity subset. No repository writes."""
import hashlib
import json
from pathlib import Path
import shutil

source_root = Path('/workspace/closure-evidence')
target_root = Path(__file__).resolve().parent
sources = {
    'latest-remote-summary.md': 'inventory/remote-refresh-environment-return/summary.md',
    'latest-remote-final-followup.json': 'inventory/remote-refresh-environment-return/final-followup.json',
    'full-cdp-r2-independent-review.json': 'ci-source-audit/full-cdp-r2-review/review.json',
    'native-source-impact-458-to-5174.json': 'ci-source-audit/full-cdp-r2-review/source-impact/review.json',
    'resume-independent-review.md': 'inventory/resume-independent-review.md',
    'resume-independent-review.json': 'inventory/resume-independent-review.json',
    'pr173-ce74-source-evidence-review.json': 'inventory/pr173-ce74-source-evidence-review.json',
    'pr173-ce74-replay-review.json': 'inventory/pr173-ce74-replay-review/review.json',
    'pr173-ce74-ci-summary.json': 'inventory/pr173-ce74-ci/summary.json',
    'environment-return-live-service.json': 'bootstrap/environment-return-live-service.json',
    'environment-return-browser-run.json': 'bootstrap/environment-return-browser-run.json',
    'environment-return-browser-run.stdout': 'bootstrap/environment-return-browser-run.stdout',
    'environment-return-browser-run.stderr': 'bootstrap/environment-return-browser-run.stderr',
    'environment-return-completed-gates.json': 'bootstrap/environment-return-completed-gates.json',
    'verify-product-push.json': 'integration/verify-product-push.json',
    'verify-product-push.stdout': 'integration/verify-product-push.stdout',
    'verify-product-push.stderr': 'integration/verify-product-push.stderr',
}
manifest = []
for name, source in sources.items():
    original = source_root / source
    target = target_root / name
    shutil.copyfile(original, target)
    manifest.append({'path': name, 'source': str(original), 'bytes': target.stat().st_size,
                     'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
(target_root / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'copied': len(manifest)}, ensure_ascii=False))
