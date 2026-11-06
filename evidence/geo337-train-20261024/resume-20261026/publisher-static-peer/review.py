from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, types, difflib

OUT=Path('/tmp/geo337-recovery-publisher-peer-20261026')
P=Path('/tmp/geo337-recover-evidence-publisher-20261026.py')
NEW=P.read_text()
INITIAL=(OUT/'SUBJECT.initial.py').read_text()
ORIGINAL=Path('/workspace/geo337-F10-shm-publication-preparation-20261025/publish_evidence_shm_v2.py').read_text()
errors=[]
checks=[]
def check(ok,label):
    checks.append(label)
    if not ok:errors.append(label)
def env_slice(src):
    tree=ast.parse(src)
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    nodes=[];active=False
    for n in main.body:
        if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='env' for x in n.targets):active=True
        if active:
            if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in ['spec','rec'] for x in n.targets):break
            nodes.append(n)
    return ast.Module(body=nodes,type_ignores=[])
fake={'GIT_DIR':'/foreign/repo.git','GIT_COMMON_DIR':'/foreign/common','GIT_WORK_TREE':'/foreign/work',
      'GIT_INDEX_FILE':'/foreign/index','GIT_OBJECT_DIRECTORY':'/foreign/objects','GIT_ALTERNATE_OBJECT_DIRECTORIES':'/foreign/alternate',
      'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':'/foreign/hooks',
      'GH_TOKEN':'synthetic-not-a-real-secret','HTTPS_PROXY':'http://example.invalid:8080','SSL_CERT_FILE':'/existing/managed/ca.pem'}
cases=[]
for name,src in [('fixed',NEW),('withdrawn',INITIAL),('restored',NEW)]:
    ns={'os':types.SimpleNamespace(environ=fake)}
    exec(compile(env_slice(src),'<isolated-memory-environment-block>','exec'),ns)
    env=ns['env'];retained=sorted(k for k in env if k.startswith('GIT_'))
    valid=(retained==['GIT_OPTIONAL_LOCKS'] and env['GIT_OPTIONAL_LOCKS']=='0' and
           all(env.get(k)==fake[k] for k in ['GH_TOKEN','HTTPS_PROXY','SSL_CERT_FILE']))
    cases.append({'case':name,'exit_code':0 if valid else 1,'retained_git_keys':retained,
                  'managed_non_git_values_preserved':all(env.get(k)==fake[k] for k in ['GH_TOKEN','HTTPS_PROXY','SSL_CERT_FILE'])})
check([x['exit_code'] for x in cases]==[0,1,0],'environment withdrawal/restoration 0/1/0')
lines=list(difflib.unified_diff(INITIAL.splitlines(),NEW.splitlines(),lineterm=''))
changed=[x for x in lines if x.startswith(('+','-')) and not x.startswith(('+++','---'))]
check(len(changed)==2 and all('env=' in x for x in changed),'only subject change since initial review is env sanitation')
tree=ast.parse(NEW)
assignments={}
for n in tree.body:
    if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant):
        for target in n.targets:
            if isinstance(target,ast.Name):assignments[target.id]=n.value.value
check(assignments['BRANCH']=='codex/train337-recovered-evidence-20261026','fixed new recovery branch')
check(assignments['BASE']=='a6f4013364e21bcb7239b5dcc25caac0f6d61f77','fixed parent')
check(assignments['HEAD']=='3e4f2560aa11ed2a626db98ba5ed6f129e791052','fixed existing private writer HEAD')
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='git']
verbs=[n.args[0].value for n in calls if n.args and isinstance(n.args[0],ast.Constant)]
check(not set(verbs)&{'checkout','switch','merge','reset','rebase','clean'},'no worktree/HEAD transition command')
check(verbs.count('update-ref')==1,'exactly one new branch ref mutation')
check("git('update-ref','refs/heads/'+BRANCH,commit,'0'*40)" in NEW,'new branch requires missing old ref')
check("git('push','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)" in NEW,'normal single recovery branch push without force')
check("len(g)==1 and old is None" in NEW,'all existing evidence leaf overwrites rejected')
check("need(set(changed)==set(entries)" in NEW and "':(exclude)evidence'" in NEW,'exact added scope and no product delta guard')
check("used+budget<=2*1024**3" in NEW and "64*1024*1024" in NEW,'original shared 2GiB and 64MiB reserve retained')
check("shutil.disk_usage(OWN).free>budget" in NEW,'actual work mount capacity checked')
check(NEW.count("need(snapshot()==before,")==2,'existing HEAD/index/branch/status checked before and after push')
check("len(payload)==item['bytes'] and h(payload)==item['sha256']" in NEW and "hashlib.sha1(b'blob '" in NEW,'full remote bytes SHA256 and Git OID checked')
check("if not a.execute:" in NEW and NEW.index('if not a.execute:')<NEW.index('a.out.mkdir()'),'nonexecute default before writes')
docfacts={}
for name in ['PROGRESS','QUESTIONS']:
    path=Path('/tmp/geo337-recovery-'+name+'-20261026.md');text=path.read_text()
    docfacts[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    if name=='PROGRESS':
        for phrase in ['未標 READY-TO-MERGE','最終驗收 F | 尚未固定','尚未採入產品路徑','本批四檔只代表 S10','未將執行 SHA 改成 S10/a6','仍屬歷史','沒有取得新的原始批准紀錄']:
            check(phrase in text,'PROGRESS explicit limitation '+phrase)
    else:
        check('不改 P-189 比較器' in text and '不改列車或其 prbody' in text,'QUESTIONS conservative scope retained')
report={'schema':'recovery-evidence-publisher-static-peer/2','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'subject_sha256':hashlib.sha256(NEW.encode()).hexdigest(),'exit_code':1 if errors else 0,
        'blocking_findings':errors,'checks':len(checks),'passed_checks':len(checks)-len(errors),
        'environment_counterproof':cases,'initial_review_preserved':'REVIEW.initial.json',
        'subject_delta':lines,'progress_questions':docfacts,
        'non_competing_write_scope':'Only the new recovery ref may be created; existing HEAD/index/train ref stays unchanged.',
        'limits':['Static review plus pure in-memory environment counterproof; no real Git mutation, network, formal test or large fixture.',
                  'Root must bind and check final manifest, actual remaining capacity, and execution/remote verification outcomes.',
                  'PROGRESS external API/environment/branch ancestry claims rely on root actual intake; this peer confirms they are not presented as final-product green.',
                  'This review does not authorize simultaneous writers or infer Claude has stopped.']}
(OUT/'SUBJECT.final.py').write_text(NEW)
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(report['exit_code'])
