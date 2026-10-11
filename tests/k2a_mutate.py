"""Run K2a-A mutations in isolated copies; never edit the checkout or native inventory."""
from pathlib import Path
import shutil,subprocess,json,hashlib
import tempfile
root=Path(__file__).resolve().parents[1];out=Path(tempfile.gettempdir())/'k2a-mutations';out.mkdir(exist_ok=True)
cases=[
 ('M02-first-only','feature-attachments.js','drafts:[...drafts].sort','drafts:[...drafts].slice(0,1).sort','K2a'),
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
for suite,judge in judges.items():
 command=['node','--test']+([] if suite=='collection' else ['--test-name-pattern=K2a'])+['tests/'+judge]
 run=subprocess.run(command,cwd=root,capture_output=True,text=True);(out/('baseline-'+suite+'.log')).write_text(run.stdout+run.stderr)
 assert run.returncode==0,run.stdout+run.stderr
results=[]
for name,file,before,after,suite in cases:
 path=out/name;(path/'geometry-web').mkdir(parents=True,exist_ok=True);(path/'tests').mkdir(exist_ok=True)
 for p in (root/'geometry-web').glob('*.js'):shutil.copy2(p,path/'geometry-web'/p.name)
 shutil.copytree(root/'geometry-web/vendor/fflate',path/'geometry-web/vendor/fflate',dirs_exist_ok=True)
 for f in ['test_grid_drafts_collection.js','test_reference_workspace_races.js','test_grid_lesson_control_ownership.js']:shutil.copy2(root/'tests'/f,path/'tests'/f)
 shutil.copytree(root/'tests/fixtures',path/'tests/fixtures',dirs_exist_ok=True)
 target=path/'geometry-web'/file;s=target.read_text();assert s.count(before)==1,(name,s.count(before));target.write_text(s.replace(before,after))
 command=['node','--test']
 if suite=='K2a':command+=['--test-name-pattern=K2a','tests/test_reference_workspace_races.js']
 elif suite=='owner':command+=['--test-name-pattern=K2a','tests/test_grid_lesson_control_ownership.js']
 else:command+=['tests/test_grid_drafts_collection.js']
 run=subprocess.run(command,cwd=path,capture_output=True,text=True);(path/'result.log').write_text(run.stdout+run.stderr)
 killed=run.returncode!=0 and 'AssertionError' in run.stdout+run.stderr
 results.append({'id':name,'exit':run.returncode,'detected':killed,
  'source_sha256':hashlib.sha256((root/'geometry-web'/file).read_bytes()).hexdigest(),
  'judge_sha256':hashlib.sha256((root/'tests'/judges[suite]).read_bytes()).hexdigest()});print(results[-1],flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results),results

