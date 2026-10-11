import hashlib,json,pathlib,shutil,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom');raw=pathlib.Path('/tmp/geometry-tests/pr190-capacity')
out=root/'tests/evidence/pf1-capacity-review-20261012';out.mkdir(parents=True,exist_ok=True)
for p in raw.rglob('*'):
 if not p.is_file() or p.suffix not in ('.json','.stdout','.stderr'):continue
 if any(part.startswith('shadow-') for part in p.relative_to(raw).parts):continue
 dest=out/'receipts'/p.relative_to(raw);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in pathlib.Path('/tmp').glob('geometry-190-*.py'):shutil.copyfile(p,out/p.name.removeprefix('geometry-190-'))
sys.path.insert(0,str(root/'tests'));import binaries
ledger=json.loads((root/'tests/mutants_results.json').read_text());active={k for k,v in ledger.items() if v['verdict']!='retired'}
binary_files=[]
for p in pathlib.Path('/tmp/geometry-tests/mutants').rglob('*.fingerprint.json'):
 if p.parent.name not in active|{'_baseline'}:continue
 dest=out/'core-sidecars'/p.relative_to('/tmp/geometry-tests/mutants');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);binary_files.append(str(dest.relative_to(out)))
p=binaries.BY_NAME['bridge'].sidecar
if p.exists():shutil.copyfile(p,out/'native-bridge.fingerprint.json')
paths=['current_geometry.c','geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c','tests/test_panel_fill_finish_surface.py',
 'tests/run_all.expected.json','tests/mutants_results.json','tests/mutate.py','tests/run_tests.py','tests/fixtures/pf1-legacy-dumps.json',
 '公理層.md','geometry-guide/公理層-白話.md','geometry-guide/公理層-閱讀器.html','BACKLOG.md','決策佇列.md','AGENTS.md']
meta={'execution_base':'26a7c443b9bd10ae036b0956bd99233f594b5395','execution_tree':'base plus dirty product/tests; artifact-only final commit does not alter tested source/judge bytes',
 'final_sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths},'ssot_normalized_sha256':hashlib.sha256((root/'公理層.md').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
 'core_sidecars':binary_files,'native_bridge_sha256':hashlib.sha256(binaries.BY_NAME['bridge'].path.read_bytes()).hexdigest()}
(out/'source-binding.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
diff=subprocess.check_output(['git','diff','26a7c443b9bd10ae036b0956bd99233f594b5395','--',*paths[:5]],cwd=root)
(out/'product-test.diff.json').write_text(json.dumps({'encoding':'utf-8','sha256':hashlib.sha256(diff).hexdigest(),'raw':diff.decode('utf-8')},ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'payloads':len(manifest),'bytes':sum(v['bytes'] for v in manifest.values())}))
