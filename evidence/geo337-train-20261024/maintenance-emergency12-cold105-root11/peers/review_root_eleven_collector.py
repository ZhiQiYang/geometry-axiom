from pathlib import Path
import ast,hashlib,json
O=Path('/workspace/train337-canvas-peer-resume');P=Path('/workspace/collect_root_eleven_archive_extensions_originals_20261024.py');OLD=Path('/workspace/collect_four_additional_archive_groups_originals_20261024.py');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
s=P.read_text();old=OLD.read_text();ck(h(P)=='6cd5ada3cb64b637aa9f391c6c792a69cc6a644d14c599b784982f11ea068ffe','collector fixed pin')
def fns(s):return {x.name:ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(s)) if isinstance(x,ast.FunctionDef)}
for name in ['digest','readj','dump','add','tree']:ck(fns(s)[name]==fns(old)[name],'exact original helper '+name)
start=' with tarfile.open(archive,\'w:gz\',compresslevel=1) as tar:';end=' result=dict('
ck(s[s.index(start):s.index(end)]==old[old.index(start):old.index(end)],'exact original tar write/roundtrip/all original posthash')
for text in ["assert gross==134045696","assert len(plans)==1 and [g['count'] for g in plans[0]['groups']]==[8]*11","assert len(archive_bodies)==88","assert not archive_bodies.intersection(x['source'] for x in entries.values())","assert total<64*1024*1024","assert r['exit_code']==0","a['actual_process_returncode']==0","r['plan_sha256']==digest(prep/'PLAN.json')","peer['exit_code']==0 and not peer['findings']","existing_archive_groups_extended=11,old_aliases_preserved=77,new_root_aliases=11,total_aliases_in_scope=88"]:ck(text in s,'exact scope/outcome guard '+text)
for text in ['Total previous19 cold archive groups now113paths, not30groups','Only exact11 root immutable archive leaves are write frozen','older packages and their historical nlink7 fields are not rewritten','Original prepare ran direct exec with full Git capture streams']:ck(text in s,'honest limit '+text)
reg=Path('/workspace/ROOT_ELEVEN_EXTENDED_IMMUTABLE_ALIAS_REGISTRY_20261024.json');r=j(reg);plan=j(r['plan']['path']);actual=j(r['actual']['path'])
ck(h(r['plan']['path'])==r['plan']['sha256']=='14d1725cd02e9c0d2eacb720f02f439f5592cf556909f805435b65a27191f6b1' and h(r['actual']['path'])==r['actual']['sha256'],'registry original anchors')
ck(len(r['groups'])==11 and sum(len(x['aliases']) for x in r['groups'])==88 and r['published'] is False,'registry88 in11 existing groups unpublished')
for n,(g,p,a) in enumerate(zip(r['groups'],plan['groups'],actual['groups']),1):
 ck(g['group']==n and g['git_path']==p['members'][0]['git_path'] and [x['path'] for x in g['aliases']]==[x['path'] for x in p['members']],'registry exact group/path projection '+str(n))
 for i,(x,m,fin) in enumerate(zip(g['aliases'],p['members'],a['final_metadata'])):
  ck(x['sha256']==g['aliases'][0]['sha256']==m['sha256'] and x['bytes']==m['size'] and (x['device'],x['inode'],x['nlink'])==(fin['dev'],fin['inode'],fin['nlink']) and x['nlink']==8,'registry originalhash/actualmetadata '+str(n)+'/'+str(i))
ck('Other423cold/2cardref/1GEO339' in ' '.join(r['limits']) and 'supersedes historical nlink7 for only these11groups' in ' '.join(r['limits']),'registry additive historical write limits')
r={'schema':'root-eleven-collector-registry-static-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'collector_sha256':h(P),'registry_sha256':h(reg),'limits':['Static review only; collector not executed by reviewer. Original body/metadata actual3136/0 is separate.','No88archive payload read; exact registry projection from originalplan/actual report only.','11existing groups extended, not11new groups; unrelated root docs may change, exact alias leaves remain write frozen.']};q=O/'ROOT_ELEVEN_COLLECTOR_REGISTRY_STATIC_PEER.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
