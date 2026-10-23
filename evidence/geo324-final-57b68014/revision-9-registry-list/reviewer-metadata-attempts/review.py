from pathlib import Path
import ast,hashlib,importlib.util,json,os
B=Path('/tmp/geo260-peer-followups');spec=importlib.util.spec_from_file_location('cap','/workspace/geo288-main-merge-20261023/bound-3d681636/p73/capture.py');cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify_streams(rows,checks):
 for i,row in enumerate(rows):
  d=Path(row['directory']);request=json.loads((d/'request.json').read_text());result=json.loads((d/'result.json').read_text())
  checks.append((f'row {i+1} original result',result==row))
  for name in ('stdin','stdout','stderr'):
   b=(d/(name+'.bin')).read_bytes();checks.append((f'row {i+1} {name} original SHA',sha(b)==row[name+'_sha256']))
   if name!='stdin':checks.append((f'row {i+1} {name} bytes',len(b)==row[name+'_bytes']))
  checks.append((f'row {i+1} request argv source',request['command']==row['command'] and request['source_sha']==row['source_sha']))
  checks.append((f'row {i+1} true zero no timeout',row['actual_process_returncode']==0 and not row['timeout_expired']))
def finish(out,checks,scope):
 findings=[n for n,ok in checks if not ok];r={'checks':len(checks),'findings':findings,'scope':scope,'rows':[{'check':n,'pass':bool(ok)} for n,ok in checks]};(out/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(out, len(checks),len(findings),sha((out/'REVIEW.json').read_bytes()));assert not findings
# List-only original actual peer.
out=B/'registry-list-1f0ebd3e';out.mkdir();checks=[];r=cap.Recorder(out,os.environ.copy(),'1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599')
def git(*args,repo='/workspace/geometry-axiom/.git'):
 row,b,e=r.run(['git','--git-dir='+repo,*args],cwd='/tmp',timeout=120);return b
src=Path('/tmp/geo324-owner-20261024/registry-list-1f0ebd3e');rows=json.loads((src/'subcommands.json').read_text());receipt=json.loads((src/'receipt.json').read_text());req=json.loads((src/'REQUEST.json').read_text());inputs=json.loads((src/'INPUTS.json').read_text());M=req['sourceSHA']
verify_streams(rows,checks);checks.extend([('12 original rows',len(rows)==12),('original --list only argv',rows[8]['command']==req['actualCommand'] and rows[8]['command'][1:]==['-B','tests/run_all.py','--list']),('receipt scope true original0',receipt['originalExit']==0 and receipt['exitCode']==0 and not receipt['errors'] and receipt['testMethodsExecuted'] is False and receipt['buildOrBrowser'] is False),('initial S57 fixed',Path(rows[0]['directory'],'stdout.bin').read_text().strip()==req['reusedCheckoutBefore']),('initial clean',not Path(rows[1]['directory'],'stdout.bin').read_bytes()),('final M fixed clean',Path(rows[9]['directory'],'stdout.bin').read_text().strip()==M and not Path(rows[10]['directory'],'stdout.bin').read_bytes()),('stage listing unchanged',Path(rows[7]['directory'],'stdout.bin').read_bytes()==Path(rows[11]['directory'],'stdout.bin').read_bytes()),('frozen driver hash',sha(Path('/tmp/geo324-owner-20261024/run_registry_list_1f0ebd3e.py').read_bytes())==req['driverSHA256'])])
raw=Path(rows[6]['directory'],'stdout.bin').read_bytes();pos=0;blob_by_path={}
for item in inputs:
 end=raw.index(b'\n',pos);head=raw[pos:end].split();size=int(head[2]);body=raw[end+1:end+1+size];pos=end+size+2
 obj=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest();checks.append(('raw fixed blob '+item['path'],head[1]==b'blob' and len(body)==item['bytes']==size and sha(body)==item['sha256'] and obj==head[0].decode()==item['gitBlob']));blob_by_path[item['path']]=body
checks.append(('Git batch complete',pos==len(raw)))
tree=git('ls-tree','-z',M,'--',*[x['path'] for x in inputs]);entries={}
for row in tree.split(b'\0'):
 if row:
  h,p=row.split(b'\t',1);entries[p.decode()]=h.split()[2].decode()
checks.append(('all347 independent Git tree paths',len(entries)==len(inputs)==347))
for item in inputs:checks.append(('independent M identity '+item['path'],entries.get(item['path'])==item['gitBlob']))
text=Path(rows[8]['directory'],'stdout.bin').read_text();checks.append(('browser explicitly not covered', '本命令未驗' in text and text.count('本 aggregate 未驗')>=20));checks.append(('original public runner listing source',blob_by_path['tests/run_all.py']==Path(rows[3]['directory'],'stdout.bin').read_bytes()))
finish(out,checks,'Only original --list registry/discovery at M. No methods, build, browser, expected comparison or fresh actual test executed. Stage equality means printed ls-files stage listing, not raw index bytes.')
# noWood ordinary merge and body narrow peer.
out=B/'nowood-merge-4d3a17c3';out.mkdir();checks=[];r=cap.Recorder(out,os.environ.copy(),'bfbab207a92a809fca50fefcefb3fa4b2af05ea9')
repo='/workspace/kernel-no-wood-prep/metadata.git'
def g(*args):return git(*args,repo=repo)
merge=json.loads(Path('/tmp/nowood-ordinary-merge-9a05ae78/receipt.json').read_text());bodypub=json.loads(Path('/tmp/geo261-nowood-prbody-4d3a17c3-20261023/receipt.json').read_text());verify_streams(merge['commands'],checks);verify_streams(bodypub['commands'],checks)
S=merge['merged_source_sha'];P=merge['own_parent'];I=merge['incoming'];tested=merge['original_execution_sha'];D=bodypub['body_ref']
checks.append(('two exact ordinary parents',g('show','-s','--format=%P',S).decode().strip().split()==[P,I]))
names=g('diff','--name-only',I,S).decode().splitlines();product=[x for x in names if not x.startswith('evidence/')];checks.append(('two exact non-evidence leaves',product==['tests/run_all.expected.json','tests/test_rectangular_template.py']))
for item in merge['unchanged_original_11_inputs']:
 old=g('show',tested+':'+item['path']);new=g('show',S+':'+item['path']);checks.append(('unchanged tested input '+item['path'],old==new and len(new)==item['bytes'] and sha(new)==item['sha256']))
old=json.loads(g('show',I+':tests/run_all.expected.json'));new=json.loads(g('show',S+':tests/run_all.expected.json'));key='py:test_rectangular_template';checks.append(('expected only11to13',old[key]==11 and new[key]==13 and {k:v for k,v in old.items() if k!=key}=={k:v for k,v in new.items() if k!=key}))
leaf=g('show',S+':tests/test_rectangular_template.py');tree=ast.parse(leaf);methods=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')];checks.append(('13 original AST methods leaf e948',len(methods)==13 and sha(leaf)=='e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e'))
body=Path('/tmp/NO_WOOD_PR_BODY_4d3a17c3.md').read_bytes();checks.append(('body pinned Git and hash',body==g('show',D+':PR_BODY.md') and sha(body)=='db9f5c35a832eb7f01b5cd661cd3f2932290901ef78ffd3b46e769561e645c11'))
txt=body.decode();checks.append(('execution bfb not relabeled new S',tested in txt and S in txt and '未改標新 head' in txt and '本分支尚未採入列車 closure' in txt));checks.append(('unchanged limits full project not inferred','原 native 記錄共 121 筆' in txt and '未另存 raw compiler pipes' in txt and 'literal include' in txt))
for data,target in [(merge,S),(bodypub,D)]:
 push=[x for x in data['commands'] if 'push' in x['command']];remotes=[x for x in data['commands'] if 'ls-remote' in x['command']];checks.append(('original normal push recorded '+target,bool(push) and push[-1]['actual_process_returncode']==0 and not any(x in push[-1]['command'] for x in ['--force','-f','--force-with-lease'])));checks.append(('original remote exact '+target,Path(remotes[-1]['directory'],'stdout.bin').read_text().split()[0]==target))
checks.append(('no tests false publication metadata',merge['tests_rerun'] is False and merge['ledger_regenerated'] is False and bodypub['tests_or_ledger_executed'] is False))
finish(out,checks,'Only immutable ordinary merge union, 11 exact tested inputs, expected11to13 and body scope, plus original publication streams. No rerun/ELF/public package revalidation; formal actual remains original bfb.')
