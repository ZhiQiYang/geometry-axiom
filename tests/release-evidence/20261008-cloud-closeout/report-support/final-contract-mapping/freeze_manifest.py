#!/usr/bin/env python3
"""Hash only the frozen mapping package; do not execute probes/tests."""
import hashlib, json, re
from pathlib import Path
root=Path(__file__).resolve().parent
public=Path('/workspace/closure-evidence/public-candidate')
future=public/'report-support/final-contract-mapping'
files=[root/'README.md',root/'subdivision_mapping.py',root/'freeze_manifest.py']
for directory in ['assembly','room54','subdivision']:
    files.extend(p for p in (root/directory).rglob('*') if p.is_file())
missing=[]
for p in files:
    if p.suffix!='.md': continue
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        target=target.split('#',1)[0]
        if not target or '://' in target or target.startswith('#'): continue
        relative=p.relative_to(root)
        resolved=(future/relative).parent/target
        resolved=resolved.resolve()
        try: relative_inside=resolved.relative_to(future)
        except ValueError: exists=resolved.exists()
        else: exists=(root/relative_inside).exists()
        if not exists: missing.append({'file':str(relative),'link':target,'expected':str(resolved)})
manifest={'schema':'geometry-frozen-contract-mapping-files/1','scope':'source/evidence mapping only; later sr15/sr18/browser probes deliberately excluded','portableDestination':'public-candidate/report-support/final-contract-mapping','files':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)],'markdownLinkCheck':{'missing':missing,'result':'pass' if not missing else 'fail'}}
(root/'frozen-mapping-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(files),'bytes':sum(p.stat().st_size for p in files),'missingLinks':missing},ensure_ascii=False))
raise SystemExit(bool(missing))
