from pathlib import Path
import ast,collections,hashlib,json,datetime
H=Path('/tmp/geo337-h-init-evidence-preparation-20261025');OUT=Path(__file__).resolve().parent
checks=[]
def ck(ok,label):checks.append({'passed':bool(ok),'label':label})
def sha(b):return hashlib.sha256(b).hexdigest()
s=(H/'collect.py').read_text();plan=json.loads((H/'PACKAGE_PLAN.json').read_bytes());old=Path('/tmp/geo323-provider-hint-publication-20261024/collect.py').read_text();prep=json.loads((H/'PREPARATION.json').read_bytes())
ck(sha(s.encode())=='164b736aa3edb334f7c1cf556e257ce13d8d8cf342bd494fb9af5338e4670cf0','reviewed collector pin')
ck(sha((H/'PACKAGE_PLAN.json').read_bytes())=='5123d82a4b372e167398309db262e9fa43f43ddce82cc22660a96998b2677b92','frozen plan pin')
ck(sha(old.encode())==prep['original_collector'],'original collector pin')
expected=old.replace('ORIGINAL_PROVIDER_HINT_EVIDENCE.tar.gz','ORIGINAL_REFERENCE_LOCAL_INIT_EVIDENCE.tar.gz').replace("tarfile.open(archive,'w:gz',compresslevel=6)","tarfile.open(archive,'w:gz',compresslevel=6,dereference=True)").replace("need(len(b)==item['bytes'],'frozen metadata size changed');rows.append({**item,'sha256':sha(b)})","need(len(b)==item['bytes'],'frozen metadata size changed');need(sha(b)==item['sha256'],'frozen original hash changed');rows.append({**item,'sha256':sha(b)})")
ck(s==expected,'exact three documented changes from original')
ck(plan['source_sha']=='2c4635577a8fcb11e88b346547f7bb1c7b739fb7','public product source pinned')
ck(len(plan['files'])==plan['count']==2546,'2546 frozen leaves')
ck(sum(x['bytes']for x in plan['files'])==plan['bytes']==29033543,'complete frozen byte count')
ck(len({x['archive']for x in plan['files']})==2546,'unique archive names')
ck(all(not x['archive'].startswith('/') and '..'not in Path(x['archive']).parts for x in plan['files']),'safe archive names')
ck(all(Path(x['local']).is_file() and not Path(x['local']).is_symlink() for x in plan['files']),'original regular paths')
ck(all(len(Path(x['local']).read_bytes())==x['bytes'] and sha(Path(x['local']).read_bytes())==x['sha256']for x in plan['files']),'all frozen originals currently hash exact')
scopes={'formal':'/tmp/geo337-reference-local-init-formal-20261024','formal-outer':'/tmp/geo337-reference-local-init-formal-launch-20261024','source-and-tools':'/tmp/geo337-reference-local-init-draft-20261024','product-static-peer':'/tmp/geo337-reference-local-init-product-peer-evidence-20261024','harness-static-peer':'/tmp/geo337-reference-local-init-harness-peer-specials-20261024','driver-static-peer':'/tmp/geo337-reference-local-init-tool-peer-specials-20261024','root-cause-originals':'/tmp/geo323-N16-fixed-cost-static-peer-20261024'}
for prefix,root in scopes.items():
 root=Path(root);expected={prefix+'/'+str(p.relative_to(root)) for p in root.rglob('*')if p.is_file()};actual={x['archive']for x in plan['files']if x['archive'].startswith(prefix+'/')};ck(actual==expected,'exhaustive frozen scope '+prefix)
for token in ("need(not OUT.exists()","shutil.disk_usage(H).free>=100*1024*1024","fcntl.LOCK_EX|fcntl.LOCK_NB","OUT.mkdir()","need(sha(b)==item['sha256']","dereference=True","recursive=False","need(m.isfile()","roundtrip bytes/hash","original bytes unchanged through collect","originals_deleted':False","product_tests_reexecuted':False","dump(OUT/'RAW_INDEX.json'","dump(OUT/'SUMMARY.json'","fcntl.LOCK_UN"):
 ck(token in s,'guard retained '+token)
ck('subprocess'not in s and 'os.system'not in s,'no test/git/subprocess execution')
ck(all(not isinstance(n,ast.Call)or not (isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','rmdir','rmtree','rename','replace'))for n in ast.walk(ast.parse(s))),'no source deletion/rename')
ck(s.index('fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)')<s.index('OUT.mkdir()'),'lock before output mutation')
ck(s.index('frozen original hash changed')<s.index('with tarfile.open'),'frozen source hash before packaging')
ck(s.index('roundtrip bytes/hash')<s.index("dump(OUT/'RAW_INDEX.json'")<s.index('r.update(exit=0'),'full roundtrip precedes success')
fail=[x for x in checks if not x['passed']]
r={'reviewer':'/root/h_init_actual_review','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':plan['source_sha'],'collector_sha256':sha(s.encode()),'plan_sha256':sha((H/'PACKAGE_PLAN.json').read_bytes()),'checks':len(checks),'failures':fail,'exit':int(bool(fail)),'details':checks,'scope':'static and frozen original bytes only; archive not yet executed/reviewed','limitations':['固定 plan 的所有現有路徑均核 hash；後續 actual tar 仍需再驗。','此工具沒有任何產品重跑，不產生新的效能判決。']}
(OUT/'STATIC_REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failures':fail,'exit':r['exit'],'sha256':sha((OUT/'STATIC_REVIEW.json').read_bytes())},ensure_ascii=False));raise SystemExit(r['exit'])
