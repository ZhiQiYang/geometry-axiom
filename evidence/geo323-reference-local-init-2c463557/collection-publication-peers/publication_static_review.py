from pathlib import Path
import hashlib,json,datetime,ast
H=Path('/tmp/geo337-h-init-evidence-preparation-20261025');OUT=Path(__file__).resolve().parent
checks=[]
def ck(ok,label):checks.append({'passed':bool(ok),'label':label})
def sha(b):return hashlib.sha256(b).hexdigest()
s=(H/'publish.py').read_text();info=json.loads((H/'PUBLICATION_TOOL.json').read_bytes());old=Path('/tmp/geo323-provider-hint-publication-20261024/publish.py').read_text()
ck(sha(s.encode())=='f156da31e3264fb710017a22d33bec5155a29c158b93a072e8b91a161e6d6f80','fixed candidate pin')
ck(sha(old.encode())==info['original_sha256'],'original publisher pin')
x=old
for a,b in info['only_parameters_changed'].items():ck(a in x,'old parameter present '+a);x=x.replace(a,b)
ck(x==s and len(info['only_parameters_changed'])==7,'exact seven substitutions no workflow change')
for token in ("need(not OUT.exists()and not BODYROOT.exists()","free>=64*1024*1024","manifest['source_sha']==S","manifest['prefix']==PREFIX","name.startswith(PREFIX+'/')","sha(Path(item['local']).read_bytes())==item['sha256']","template.count(b'__EVIDENCE_SHA__')==1","sha(template)==manifest['body_sha256']","'owned branch'","'clean before E'","'remote source still S'","'fresh owned body remote branch'","'new exact evidence leaf'","'copied evidence bytes'","'exact stage allowlist'","'ordinary E parent S'","'published evidence exact blob'","'remoteE'","'body only'","'ordinary D parent E'","'exact finalbody'","'remoteD'","'original E checkout remains clean'","'force_push':False","'product_tests_reexecuted':False"):
 ck(token in s,'retained publication guard '+token)
ck("g('push','origin','HEAD:refs/heads/'+BRANCH)" in s and "g('push','origin','HEAD:refs/heads/'+DBRANCH"in s,'normal explicit owned pushes')
ck("'--force'"not in s and "'--force-with-lease'"not in s and "g('reset'"not in s and "g('clean'"not in s,'no rewrite/reset/clean')
ck("codex/train337-reference-local-init-20261024"in s and 'claude/'not in s and 'grok/'not in s,'owned codex branches only')
ck("PREFIX='evidence/geo323-reference-local-init-2c463557'" in s,'unique S evidence prefix')
body=(H/'PR_BODY.template.md').read_text();progress=(H/'PROGRESS.md').read_text()
ck(body.count('__EVIDENCE_SHA__')==1,'one evidence placeholder')
for name,text in [('body',body),('progress',progress)]:
 for token in ('2c4635577a8fcb11e88b346547f7bb1c7b739fb7','14/14','0／1／0' if name=='progress'else '0/1/0','O0','O2','N16','255168','未跑' if name=='body'else '未執行','ELF'):
  ck(token in text,'truthful scoped '+name+' '+token)
 ck(('不是 READY-TO-MERGE'in text)or('尚不是 READY-TO-MERGE'in text),'no readiness claim '+name)
ck('1777 checks'in body and '不是新增產品測試數'in body,'audit count correctly scoped')
ck(Path('/tmp/geo337-reference-local-init-draft-20261024/launch_formal.py').is_file(),'documented original launcher exists')
fail=[x for x in checks if not x['passed']]
r={'reviewer':'/root/h_init_actual_review','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7','checks':len(checks),'failures':fail,'exit':int(bool(fail)),'details':checks,'bindings':{p.name:sha(p.read_bytes())for p in [H/'publish.py',H/'PUBLICATION_TOOL.json',H/'PR_BODY.template.md',H/'PROGRESS.md']},'scope':'publisher code and wording static review; future manifest/publication actual not yet accepted'}
(OUT/'PUBLICATION_STATIC_REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failures':fail,'exit':r['exit'],'sha256':sha((OUT/'PUBLICATION_STATIC_REVIEW.json').read_bytes())},ensure_ascii=False));raise SystemExit(r['exit'])
