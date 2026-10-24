#!/usr/bin/env python3
"""只補 current UNRUN metadata 的 v2 路徑，保 frozen v1/v2 及原peer。"""
import hashlib
import json
from pathlib import Path

base=Path('/tmp/geo324-owner-20261024')
out=base/'current-preparation-binding'
if out.exists():raise SystemExit('refuse overwrite')
out.mkdir()
state=json.loads((base/'preparation-v2/CURRENT_STATE_PREPARED.json').read_text())
edits=[]
for row in state['rows']:
    if row['gate'].startswith('predicate-'):
        before=row['originalCommand']
        row['originalCommand']=before.replace('run_face_predicate_proofs.py:', 'run_face_predicate_proofs_v2.py:', 1)
        if before==row['originalCommand']:raise SystemExit('binding anchor absent')
        edits.append({'gate':row['gate'],'before':before,'after':row['originalCommand']})
if len(edits)!=3:raise SystemExit('expected exactly original three predicate plan rows')
state['bindingRole']='current prepared metadata only; no execution result; old frozen inventories retained'
state['predicateDriverSHA256']='4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d'
(out/'CURRENT_STATE_PREPARED.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
(out/'BINDING.json').write_text(json.dumps({'sourceCandidate':state['productSourceSHA'],'formalFinalSHA':None,
  'changes':edits,'productTestsExecuted':False,
  'reason':'independent peer requested exact v2 executable filename in current plan rows; no subject or assertion change',
  'priorFrozenManifestSHA256':'d38dd52fe3f343ac90dae883c2efbf195409bdf7c42c25e03cb5b06dbbc4ffb6',
  'currentStateSHA256':hashlib.sha256((out/'CURRENT_STATE_PREPARED.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'metadataOnly':True,'exitCode':0,'bindingSHA256':hashlib.sha256((out/'BINDING.json').read_bytes()).hexdigest()}))
