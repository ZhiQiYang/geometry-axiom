#!/usr/bin/env python3
"""保留原稀疏缺依賴失敗，只補 feedback_store 物化後重跑 metadata。"""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

base=Path('/tmp/geo324-owner-20261024')
original=base/'prepare_metadata_package.py'
bound=base/'prepare_metadata_package_v2.py'
if bound.exists(): raise SystemExit('refuse overwrite')
raw=original.read_text()
edits=[("OUT=BASE/'authority-and-plan'","OUT=BASE/'authority-and-plan-resume1'"),
       ("+'/geometry-web/feedback_cli.py\\n'","+'/geometry-web/feedback_cli.py\\n/geometry-web/feedback_store.py\\n'")]
adapted=raw
for before,after in edits:
    if adapted.count(before)!=1: raise SystemExit('binding anchor not unique')
    adapted=adapted.replace(before,after,1)
bound.write_text(adapted)
(base/'METADATA_PREPARATION_CORRECTION.diff').write_text(''.join(difflib.unified_diff(raw.splitlines(True),adapted.splitlines(True),fromfile=original.name,tofile=bound.name)))
(base/'METADATA_PREPARATION_CORRECTION.json').write_text(json.dumps({
  'originalAttempt':str(base/'authority-and-plan/receipt.json'),'originalExit':1,
  'reason':'thin checkout omitted feedback_store.py dependency for read-only startup inbox list',
  'change':'only metadata output directory and one additional existing feedback_store sparse path; no product/source edits',
  'originalToolSHA256':hashlib.sha256(original.read_bytes()).hexdigest(),
  'boundToolSHA256':hashlib.sha256(bound.read_bytes()).hexdigest(),
  'productTestExecuted':False},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(subprocess.run([sys.executable,'-B',str(bound)],cwd=base).returncode)
