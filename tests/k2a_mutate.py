"""Run K2a-A mutations in isolated copies; never edit the checkout or native inventory."""
from pathlib import Path
import shutil,subprocess,json,hashlib
import tempfile
root=Path(__file__).resolve().parents[1];out=Path(tempfile.gettempdir())/'k2a-mutations';out.mkdir(exist_ok=True)
cases=[
 ('M02-first-only','feature-attachments.js','drafts:[...drafts].sort','drafts:[...drafts].slice(0,1).sort','collection'),
 ('M07-duplicate-target','feature-attachments.js','if (targets.has(target))','if (false && targets.has(target))','collection'),
 ('M08-truncate-capacity','feature-attachments.js','value.drafts.length > MAX_GRID_DRAFTS','value.drafts.length > 100','collection'),
 ('M09-allow-draft-ref','feature-attachments.js','["grid-system", "grid-binding", "boundary"].includes','["grid-system", "grid-binding", "boundary", "grid-draft"].includes','collection'),
 ('M11-fake-orphan','feature-attachments.js','if (value.orphans.some','if (false && value.orphans.some','collection'),
 ('M11-false-lost','feature-attachments.js','ref.lost !== true','false','collection'),
 ('M11-downgrade','project-store.js','manifest.format !== GRID_DRAFTS_FORMAT','false','collection'),
 ('M12-clear-lost','reference-workspace.js','if(ref.lost && value.inputRefs.some','if(false && ref.lost && value.inputRefs.some','K2a'),
 ('M12-old-api','reference-workspace.js','options.gridWrite!==gridDraftWrite','false','K2a'),
 ('M14-revive-orphan','reference-workspace.js','if(changed){if(localDeletion)','if(objects){c.orphans=[];changed=true;}if(changed){if(localDeletion)','K2a'),
 ('M15-unreviewed-repin','reference-workspace.js','if(next.baseRef.fingerprint!==expectedBaseFingerprint)','if(false && next.baseRef.fingerprint!==expectedBaseFingerprint)','K2a'),
 ('M04-clear-all','reference-workspace.js','c.drafts.filter(d=>d.draftId!==feature.value.draftId)','[]','K2a'),
 ('M06-no-scan','reference-workspace.js','if(changed){if(localDeletion)','if(false && changed){if(localDeletion)','K2a'),
 ('M05-auto-rebase','grid-system-workspace.js','!samePin(actual,ref)','false','owner'),
 ('M15-literal-comparison','grid-system-workspace.js','return number>=min&&number<=BigInt(LIMIT)&&number===BigInt(other);','return value===actual;','owner'),
 ('M14b-same-lost-id','grid-system-workspace.js','if(before.lost && (','if(false && before.lost && (','owner'),
 ('M10-orphan-to-single','feature-attachments.js','drafts.length === 1 && !orphans.length','drafts.length === 1','collection'),
 ('M12-late-editor-flush','grid-system-workspace.js','state === s && dialog.open','dialog.open','owner'),
 ('M14b-cached-lost-pin','grid-system-workspace.js','for(const ref of owned?.inputRefs||[])if(ref.lost && s.inputPins.has(pinKey(ref)))s.inputPins.get(pinKey(ref)).lost=true;\n    const form=','const form=','owner'),
 ('M14b-noop-deletion-history','reference-workspace.js','if(localDeletion)history.push','if(false && localDeletion)history.push','K2a'),
]
judges={'K2a':'test_reference_workspace_races.js','owner':'test_grid_lesson_control_ownership.js','collection':'test_grid_drafts_collection.js'}
targets={'M14b-noop-deletion-history': 'K2a M14b identical native transaction gives deletion flags one reversible local history step', 'M14b-cached-lost-pin': 'K2a M12 a late flush from the retired draft cannot write after another draft owns the editor', 'M12-late-editor-flush': 'K2a M12 a late flush from the retired draft cannot write after another draft owns the editor', 'M10-orphan-to-single': 'M10 writer selects legacy only for one healthy draft, collection for orphans or lost', 'M14b-same-lost-id': 'K2a M14b replacement requires old/new confirmation and rejects a previously lost identity', 'M15-literal-comparison': 'K2a M15 two-way comparison follows integer and signed-cell parsing rather than raw spelling', 'M05-auto-rebase': 'K2a M05 changed input pin blocks preview until an explicitly selected current pin is recorded', 'M06-no-scan': 'K2a M06/M14 deletion receipt marks orphans and lost even when identical ids still exist', 'M04-clear-all': 'K2a M04 native confirmation clears only its leased draft; failed confirmation preserves both', 'M15-unreviewed-repin': 'K2a M15 repin requires the reviewed current fingerprint and keeps raw and lost references intact', 'M14-revive-orphan': 'K2a M06/M14 deletion receipt marks orphans and lost even when identical ids still exist', 'M12-old-api': 'K2a M01/M03/M12 per-draft writes coexist, legacy replacement and late context flush cannot alter them', 'M12-clear-lost': 'K2a M12/M14b lost flags cannot be erased or repinned with the same identity', 'M11-downgrade': 'M11 downgrade and capability stripping fail on real archive bytes', 'M11-false-lost': 'M11 strict schema, orphan membership, lost placement and flag values reject', 'M11-fake-orphan': 'M11 strict schema, orphan membership, lost placement and flag values reject', 'M09-allow-draft-ref': 'M09 drafts are never valid input references', 'M08-truncate-capacity': 'M08 sixteen drafts accepted; seventeenth rejected without truncation', 'M07-duplicate-target': 'M07 non-orphan target uniqueness rejects the entire collection; orphans do not reserve targets', 'M02-first-only': 'M02 two raw drafts survive real ZIP with collection capability and canonical identity order'}

import re
out=Path(tempfile.gettempdir())/'k2aa-mutations-review'
out.mkdir(exist_ok=True)
def execute(command,cwd,log):
 run=subprocess.run(command,cwd=cwd,capture_output=True,text=True,timeout=120)
 log.write_text(run.stdout+run.stderr)
 return run,run.stdout+run.stderr
def green(run,text):
 return run.returncode==0 and '# tests 1' in text and '# pass 1' in text and '# fail 0' in text and '# skipped 0' in text
results=[]
for name,file,before,after,suite in cases:
 directory=out/name;(directory/'geometry-web').mkdir(parents=True,exist_ok=True);(directory/'tests').mkdir(exist_ok=True)
 for p in (root/'geometry-web').glob('*.js'):shutil.copy2(p,directory/'geometry-web'/p.name)
 shutil.copytree(root/'geometry-web/vendor/fflate',directory/'geometry-web/vendor/fflate',dirs_exist_ok=True)
 judge=judges[suite];shutil.copy2(root/'tests'/judge,directory/'tests'/judge)
 shutil.copytree(root/'tests/fixtures',directory/'tests/fixtures',dirs_exist_ok=True)
 target=directory/'geometry-web'/file;original=target.read_bytes();source=original.decode();assert source.count(before)==1
 expected=targets[name];command=['node','--test','--test-reporter=tap','--test-name-pattern=^'+re.escape(expected)+'$','tests/'+judge]
 baseline,raw=execute(command,directory,directory/'baseline.log');assert green(baseline,raw),(name,raw)
 target.write_text(source.replace(before,after))
 build,raw=execute(['node','--check',str(target)],directory,directory/'build.log');assert build.returncode==0,(name,raw)
 red,raw=execute(command,directory,directory/'red.log')
 detected=red.returncode!=0 and '# tests 1' in raw and '# fail 1' in raw and '# skipped 0' in raw and re.search(r'not ok \d+ - '+re.escape(expected),raw) is not None and "code: 'ERR_ASSERTION'" in raw
 target.write_bytes(original)
 restored,restoredraw=execute(command,directory,directory/'restored.log');assert green(restored,restoredraw),(name,restoredraw)
 result={'id':name,'expected_test':expected,'command':command,'detected':detected,'baseline_exit':baseline.returncode,'build_exit':build.returncode,'red_exit':red.returncode,'restored_exit':restored.returncode,'source_sha256':hashlib.sha256(original).hexdigest(),'judge_sha256':hashlib.sha256((root/'tests'/judge).read_bytes()).hexdigest(),'logs':{p:hashlib.sha256((directory/(p+'.log')).read_bytes()).hexdigest() for p in ['baseline','build','red','restored']}}
 results.append(result);print(json.dumps(result),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results),results
