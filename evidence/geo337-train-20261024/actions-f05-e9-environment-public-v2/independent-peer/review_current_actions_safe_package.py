import collections,hashlib,json,tarfile
from pathlib import Path
B=Path('/workspace/pr338-pr339-current-actions-publication-v2-20261024');R=Path('/workspace/pr338-pr339-current-actions-environment-20261024');O=Path('/workspace/train337-canvas-peer-resume')
checks=0;findings=[]
def ck(v,l):
 global checks
 checks+=1
 if not v:findings.append(l)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');red=j(B/'PUBLIC_REDACTIONS.json');inv=j(B/'MEMBER_INVENTORY.json')['members'];cl=j(R/'CLASSIFICATION.json');binding=j(R/'SOURCE_BINDING.json')
ck(h(p['archive'])==p['archive_sha256']=='40567a58ce19e563245b109736ee1417a28e8d77308ce0027df19dfc6fd361c8','exact public archive pin')
ck(h(B/'PUBLIC_REDACTIONS.json')==p['public_redaction_manifest_sha256']=='29452ec5766d7383fa90ef04abe30fd2833b1ca81175a6b9c8004e5452d8b6e5','exact public redaction pin')
ck(h(R/'CLASSIFICATION.json')==p['classification_sha256']=='6c5bb4c8dbb0420e61296efdaff1b7dc5acf2335a2959da7d4a92b35ac889121','original classification pin')
ck(h(R/'SOURCE_BINDING.json')==p['source_binding_sha256']=='fa86699c1544a7a0c20498e0720e59ae9e5060be5397e9f73f5977b626b39280','original full-tree binding pin')
secrets=[];public={};private_names=set()
for item in red['items']:
 raw=Path(item['private_original']).read_bytes();ck(len(raw)==item['original_bytes'] and sh(raw)==item['original_sha256'],'private original full stream intact')
 data=raw
 for rg in reversed(item['ranges']):
  a,b=rg['start_byte'],rg['end_byte_exclusive'];value=raw[a:b];secrets.append(value)
  ck(rg['field']=='signature' and b>a and sh(value)==rg['redacted_value_sha256'] and raw[a-10:a]==b'signature=','exact credential-value range without disclosure')
  data=data[:a]+b'REDACTED_SIGNED_QUERY_VALUE'+data[b:]
 ck(sh(data)==item['public_sha256'] and len(data)==item['public_bytes'],'public replacement exact and only specified bytes')
 public[item['public_member']]=data;private_names.add(item['public_member'].removesuffix('.redacted'))
ck(len(secrets)==len(red['items'])==2 and all(secrets),'exact two nonempty credential values held only in memory')
secret_matches=0
def scan(data):
 global secret_matches
 secret_matches+=sum(value in data for value in secrets)
iv={x['member']:x for x in inv};ck(len(iv)==len(inv)==363,'exact363 original public entries')
with tarfile.open(p['archive'],'r:gz') as tar:
 ms=tar.getmembers();ck(len(ms)==p['member_count']==365 and len({m.name for m in ms})==365 and {m.name for m in ms}==set(iv)|{'PUBLIC_REDACTIONS.json','MEMBER_INVENTORY.json'},'exact365 unique public member set')
 ck(not private_names&{m.name for m in ms},'unredacted signed stderr names omitted from public archive')
 for m in ms:
  ck(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe regular member '+m.name)
  data=tar.extractfile(m).read();scan(data)
  if m.name not in iv:ck(data==(B/m.name).read_bytes(),'embedded metadata exact '+m.name);continue
  x=iv[m.name];raw=Path(x['source']).read_bytes();ck(len(raw)==x['original_bytes'] and sh(raw)==x['original_sha256'],'retained original hash '+m.name)
  ck(len(data)==x['public_bytes']==m.size and sh(data)==x['public_sha256'],'public member bytes '+m.name)
  ck(data==(public[m.name] if x['redacted'] else raw),'only declared redaction '+m.name)
for f in B.iterdir():
 if f.is_file() and f.suffix!='.gz':scan(f.read_bytes())
ck(secret_matches==0,'no exact secret value anywhere in public uncompressed members or adjacent package metadata')
allrows=[]
for name,expected in [('original-metadata',48),('policy-original-metadata',5),('full-tree-original-metadata',12)]:
 rows=j(R/name/'subcommands.json');ck(len(rows)==expected,'original read command count '+name);allrows+=rows
 for row in rows:
  d=Path(row['directory']);ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'exact original request/result '+str(d))
  ck(row['timeout_expired'] is False and row['ended_epoch']>=row['started_epoch'],'actual original terminal read '+str(d))
  for stream in ('stdout','stderr','stdin'):
   raw=(d/(stream+'.bin')).read_bytes();ck(sh(raw)==row[stream+'_sha256'],'original stream hash '+str(d/stream))
   if stream!='stdin':ck(len(raw)==row[stream+'_bytes'],'original stream length '+str(d/stream))
ck(collections.Counter(x['actual_process_returncode'] for x in allrows)=={0:63,1:2},'65 original read statuses:63zero+twoForbidden1')
bad=[x for x in allrows if x['actual_process_returncode']!=0];ck(len(bad)==2 and all('--log' in x['command'] and b'Forbidden' in (Path(x['directory'])/'stderr.bin').read_bytes() for x in bad),'only signed log download read failures; no nonexistent-log inference')
for run,expected_pr,expected_id,head in zip(cl['runs'],(338,339),(40043471807,40040764499),('f05e7cfd373c9a77a366f7b2ddafd9401f261cf4','e9ee6d088b0cad4e3984aa2842a50acc311c2351')):
 api=j(R/f'PR{expected_pr}_run_api.original');jobs=j(R/f'PR{expected_pr}_jobs_api.original')['jobs']
 ck(run['pr']==expected_pr and run['run_id']==api['id']==expected_id and run['reviewed_head']==api['head_sha']==head,'current exact reviewed run and SHA')
 ck(api['status']=='completed' and api['conclusion']=='failure' and len(jobs)==len(run['jobs'])==7,'all original seven job failure')
 for job in jobs:
  out=next(x for x in run['jobs'] if x['job_id']==job['id']);ann=j(Path(out['annotation_capture'])/'stdout.bin')
  ck(job['runner_id']==out['runner_id']==0 and job['runner_name']==out['runner_name']=='' and job['steps']==out['steps']==[] and job['conclusion']=='failure','original scheduler prevented execution '+str(job['id']))
  ck(len([x for x in ann if x['annotation_level']=='failure'])==1 and out['failure_annotation']==next(x for x in ann if x['annotation_level']=='failure') and 'recent account payments have failed or your spending limit needs to be increased' in ann[0]['message'],'exact original disjunctive billing annotation '+str(job['id']))
 ck(not run['actions_executed_product'] and not run['product_pass_inferred'] and not run['current_ci_blocker_resolved'],'no inferred product pass or B3 resolution')
 ck('does not prove a log archive does not exist' in run['log_retrieval']['classification'],'Forbidden access limitation retained')
for quote in cl['policy_quotes']:
 filename='PROCEDURE_SOURCE_decisions.txt' if quote['source']=='決策佇列.md' else 'PROCEDURE_SOURCE_handoff.txt'
 lines=(R/filename).read_text().splitlines();expected='\n'.join(lines[quote['start_line']-1:quote['end_line']]);ck(expected==quote['verbatim'],'exact existing policy quote '+quote['name'])
ck('does not create a broader same-head equivalence rule' in cl['policy_conclusion'] and 'or mark B3/B2 resolved' in cl['policy_conclusion'],'policy limits preserved')
def tree(raw):
 rows=raw.split(b'\0');ck(rows[-1]==b'','complete NUL tree stream');out={}
 for row in rows[:-1]:
  meta,path=row.split(b'\t',1);ck(path not in out,'unique tracked path');out[path]=tuple(meta.split(b' '))
 return out
for pair,n in zip(binding['pairs'],(260,20)):
 trees=[]
 for item in pair['whole_tree_captures']:
  cmd=item['original_command'];raw=(Path(cmd['directory'])/'stdout.bin').read_bytes();ck(cmd in allrows and cmd['command']==['git','ls-tree','-r','-z','--full-tree',item['sha']] and sh(raw)==item['tree_raw_sha256'],'complete original tree bytes and argv')
  data=tree(raw);ck(len(data)==item['entries'],'tree entry count');trees.append(data)
 a,b=trees;diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k));decoded=[x.decode() for x in diff]
 ck(len(diff)==pair['total_changed_paths']==n and decoded==pair['all_changed_paths'] and all(x.startswith(b'evidence/') for x in diff),'exact evidence-only full-tree change set')
 ck({k:v for k,v in a.items() if not k.startswith(b'evidence/')}=={k:v for k,v in b.items() if not k.startswith(b'evidence/')},'complete non-evidence path/mode/type/object map identical')
 raw=(Path(pair['raw_diff_command']['directory'])/'stdout.bin').read_bytes().split(b'\0');ck(raw[-1]==b'' and len(raw[:-1])==2*n,'complete raw diff pair count')
 ck(sorted(raw[1:-1:2])==diff,'raw diff covers same exact paths')
 ns=(Path(pair['name_status_command']['directory'])/'stdout.bin').read_bytes().split(b'\0');ck(ns[-1]==b'' and sorted(ns[1:-1:2])==diff,'name-status covers same exact paths')
ck(binding['exit_code']==0 and not binding['product_test_or_workflow_modified_by_audit'],'read-only source comparison')
report={'schema':'independent-current-actions-public-safe-package-and-source-binding-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'archive_sha256':p['archive_sha256'],'members':365,'public_original_entries':363,'original_reads':65,'read_exit_counts':{'0':63,'1':2},'redactions':2,'secret_matches_in_public_member_bytes_and_package_metadata':secret_matches,'credential_values_printed':False,'whole_tree_evidence_only_change_counts':{'338':260,'339':20},'limits':['No new API request or subject execution. Existing original complete read outputs and metadata were checked.','Two private signed-query values are retained in original cloud streams; public copies explicitly replace only their exact byte ranges. All other bytes are unchanged.','Collector producer outer streams still need separate check if attached; this report covers archive and adjacent package metadata only.','Annotations prove scheduler prevented all14 jobs due to payment failure OR spending limit; Forbidden is a separate download access failure, not proof logs do not exist.','Complete non-evidence tree equality is a source relationship only. Original runtime SHA remains L/F; no gate result, B3 resolution, merged status, or expanded authorization is inferred.']};out=O/'CURRENT_ACTIONS_SAFE_PACKAGE_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'path':str(out),'sha256':h(out)},ensure_ascii=False));raise SystemExit(report['exit_code'])
