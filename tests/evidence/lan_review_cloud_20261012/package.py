import hashlib,json,pathlib,shutil,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom');out=root/'tests/evidence/lan_review_cloud_20261012';raw=pathlib.Path('/tmp/geometry-tests/pr194-review')
sha=lambda b:hashlib.sha256(b).hexdigest()
if len(sys.argv)==3 and sys.argv[1]=='--decode':
 destination=pathlib.Path(sys.argv[2])
 for p in out.rglob('*.raw.json'):
  j=json.loads(p.read_text());data=j['raw'].encode();assert len(data)==j['bytes'] and sha(data)==j['sha256']
  target=destination/p.relative_to(out).with_name(j['original_filename']);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 print(json.dumps({'decoded_to':str(destination)}));sys.exit(0)
for p in raw.rglob('*'):
 if not p.is_file() or p.suffix not in ('.json','.stdout','.stderr','.log') or 'M23-source' in p.relative_to(raw).parts:continue
 target=out/'receipts'/p.relative_to(raw);target.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix in ('.stdout','.stderr','.log'):
  data=p.read_bytes();j={'original_filename':p.name,'bytes':len(data),'sha256':sha(data),'encoding':'utf-8','raw':data.decode('utf-8')}
  target=target.with_name(target.name+'.raw.json');target.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');assert json.loads(target.read_text())['raw'].encode()==data
 else:shutil.copyfile(p,target)
for p in pathlib.Path('/tmp').glob('geometry-194-*.py'):
 if p.name=='geometry-194-publish.py':continue
 shutil.copyfile(p,out/p.name.removeprefix('geometry-194-'))
names=['tests/test_lan_review.py','tests/run_all.py','tests/_unittest_runner.py','tests/test_serve_lan.py','tests/test_serve.py','tests/run_all.expected.json','tests/evidence/lan_review_proof.py','tests/evidence/lan_review_mutants.json','geometry-web/serve.py','geometry-web/lan_guard.py','geometry-web/lan_tls.py','geometry-web/runtime_version.py','geometry-web/native_context.py','current_geometry.c','tests/mutants_results.json','公理層.md','geometry-guide/公理層-白話.md','geometry-guide/公理層-閱讀器.html','BACKLOG.md','決策佇列.md','AGENTS.md']
meta={'execution_base':'5d7b044beb43f34e01bb56bf3cde70484aee377d','execution_tree':'base plus dirty test/allowlist bytes; not a final SHA execution claim','sources':{n:sha((root/n).read_bytes()) for n in names},'ssot_normalized_sha256':sha((root/'公理層.md').read_bytes().replace(b'\r\n',b'\n'))}
(out/'source-binding.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
diff=subprocess.check_output(['git','diff','5d7b044','--','tests/test_lan_review.py','tests/run_all.py'],cwd=root)
(out/'product-test.diff.json').write_text(json.dumps({'encoding':'utf-8','sha256':sha(diff),'raw':diff.decode()},ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'payloads':len(manifest),'bytes':sum(v['bytes'] for v in manifest.values())}))
