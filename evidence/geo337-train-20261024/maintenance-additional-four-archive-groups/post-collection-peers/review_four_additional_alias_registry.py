#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,stat
P=Path('/workspace/FOUR_ADDITIONAL_IMMUTABLE_ALIAS_REGISTRY_20261024.json');O=Path('/workspace/train337-canvas-peer-resume');C=[]
def need(v,s):C.append({'check':s,'passed':bool(v)})
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(P.read_text());need(h(P)=='c942313062fb0888367030e1f730f89281e56a12399fc4a7d209ed3113474b4a','exact new registry pin')
for key in ['source_plan','actual_report','independent_actual_peer']:
 p=Path(r[key]['path']);need(h(p)==r[key]['sha256'],'exact reference '+key)
plan=json.loads(Path(r['source_plan']['path']).read_text())
need(r['owner_roots']==[o['root'] for o in plan['owners']] and len(r['owner_roots'])==7,'only original seven owners')
need(len(r['groups'])==4,'four additional groups only')
allpaths=[]
for i,(g,old) in enumerate(zip(r['groups'],plan['groups']),1):
 need(g['group']==i and g['label']==old['relative_label'] and g['sha256_from_original_fresh_executor']==old['sha256'],'original group label/hash '+str(i))
 need(len(g['aliases'])==len(old['members'])==7,'exact seven aliases '+str(i))
 for x,src in zip(g['aliases'],old['members']):
  need(all(x[k]==src[k] for k in ['path','owner_root','owner_head','git_path','git_blob']) and x['bytes']==src['size'],'exact projected alias identity '+x['path'])
  p=Path(x['path']);s=p.lstat();need(stat.S_ISREG(s.st_mode) and not p.is_symlink() and (s.st_dev,s.st_ino,s.st_nlink,s.st_size)==(x['current_dev'],x['current_inode'],x['current_nlink'],x['bytes']) and x['current_nlink']==7,'fresh retained alias metadata '+x['path']);allpaths.append(x['path'])
need(len(set(allpaths))==28,'no duplicate or missing named alias')
rules='\n'.join(r['rules']);prior='\n'.join(r['earlier_reservations_not_superseded'])
need('before all applicable aliases are safely de-linked' in rules,'all aliases require delinking before rewrite/reuse')
need('writable test checkout' in rules and 'checkout/reset/clean' in rules,'retired seven owners not writable checkout candidates')
need('Read-only inspection is allowed' in rules and 'separate root decision' in rules,'read-only allowed and ordinary source retirement separate')
need('pending105 source retirement remains unexecuted' in rules,'105 cleanup not falsely executed')
need(all(s in prior for s in ['423','2 cardref','1 GEO339','3 previous large']),'previous 423/2/1/3 leases retained')
need('Metadata registry generation does not repeat body hashing or assert product acceptance' in rules,'metadata only; no acceptance relabel')
findings=[c['check'] for c in C if not c['passed']];result={'scope':'Exact additional alias registry projection and current lstat only','checks':len(C),'exit_code':int(bool(findings)),'findings':findings,'registry_sha256':h(P),'aliases':28,'groups':4,'archive_bodies_read':False,'check_details':C}
p=O/'FOUR_ADDITIONAL_ALIAS_REGISTRY_STATIC_PEER.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':len(C),'exit_code':result['exit_code'],'findings':findings},ensure_ascii=False));raise SystemExit(result['exit_code'])
