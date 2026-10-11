from pathlib import Path
import shutil,subprocess,json,re,hashlib
root=Path(__file__).resolve().parents[1];out=Path('/tmp/k2aa-lifecycle-mutants');out.mkdir(exist_ok=True)
cases=[
 ('M2-collection-projection','feature-attachments.js','if(value.schema===GRID_DRAFTS_SCHEMA)return validateGridDrafts','if(false && value.schema===GRID_DRAFTS_SCHEMA)return validateGridDrafts','test_grid_drafts_lifecycle_capacity.js','M2 healthy singleton collection never subtracts lifecycle capacity'),
 ('M1-pure-removal','reference-workspace.js','if(ref.lost&&!value.inputRefs.some','if(false && ref.lost&&!value.inputRefs.some','test_reference_workspace_races.js','K2a M12/M14b lost flags cannot be erased or repinned with the same identity'),
 ('M2-individual-reserve','feature-attachments.js','MAX_BYTES,gridLostReserve(value),','MAX_BYTES,0,','test_grid_drafts_lifecycle_capacity.js','M2 individual draft reserves every automatic lost flag before admission'),
 ('M2-collection-reserve','feature-attachments.js','MAX_GRID_DRAFTS_BYTES,gridCollectionReserve(value),','MAX_GRID_DRAFTS_BYTES,0,','test_grid_drafts_lifecycle_capacity.js','M2 collection value reserves all lost flags and orphan identifiers'),
 ('M2-record-reserve','feature-attachments.js','MAX_GRID_DRAFTS_BYTES,gridCollectionReserve(record.value),','MAX_GRID_DRAFTS_BYTES,0,','test_grid_drafts_lifecycle_capacity.js','M2 collection record reserves automatic marking within its own byte limit'),
 ('M2-manifest-reserve','project-store.js','if(records?.some(record=>record.kind===Features.GRID_KIND)){','if(false && records?.some(record=>record.kind===Features.GRID_KIND)){','test_grid_drafts_lifecycle_capacity.js','M2 complete manifest reserves grid promotion before native deletion or import'),
]
results=[]
for name,file,before,after,judge,test in cases:
 d=out/name;(d/'geometry-web').mkdir(parents=True,exist_ok=True);(d/'tests').mkdir(exist_ok=True)
 for p in (root/'geometry-web').glob('*.js'):shutil.copy2(p,d/'geometry-web'/p.name)
 shutil.copytree(root/'geometry-web/vendor/fflate',d/'geometry-web/vendor/fflate',dirs_exist_ok=True)
 shutil.copytree(root/'tests/fixtures',d/'tests/fixtures',dirs_exist_ok=True);shutil.copy2(root/'tests'/judge,d/'tests'/judge)
 p=d/'geometry-web'/file;source=p.read_bytes();assert source.decode().count(before)==1
 command=['node','--test','--test-reporter=tap','--test-name-pattern=^'+re.escape(test)+'$','tests/'+judge]
 def run(cmd,label):
  r=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=120);text=r.stdout+r.stderr;(d/(label+'.log')).write_text(text);return r.returncode,text
 code,text=run(command,'baseline');assert code==0 and '# pass 1' in text and '# skipped 0' in text,(name,text)
 p.write_text(source.decode().replace(before,after));code,text=run(['node','--check',str(p)],'build');assert code==0
 code,text=run(command,'red');assert code!=0 and '# fail 1' in text and '# skipped 0' in text and "code: 'ERR_ASSERTION'" in text and re.search('not ok [0-9]+ - '+re.escape(test),text),(name,text)
 p.write_bytes(source);code,text=run(command,'restored');assert code==0 and '# pass 1' in text and '# skipped 0' in text
 results.append({'id':name,'expected_test':test,'command':command,'detected':True,'source_sha256':hashlib.sha256(source).hexdigest(),'judge_sha256':hashlib.sha256((root/'tests'/judge).read_bytes()).hexdigest(),'logs':{label:hashlib.sha256((d/(label+'.log')).read_bytes()).hexdigest() for label in ['baseline','build','red','restored']}});print(name,flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
