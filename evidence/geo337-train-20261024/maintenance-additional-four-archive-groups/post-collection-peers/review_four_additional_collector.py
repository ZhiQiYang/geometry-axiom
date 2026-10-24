#!/usr/bin/env python3
from pathlib import Path
import ast,hashlib,json
O=Path('/workspace/train337-canvas-peer-resume');P=Path('/workspace/collect_four_additional_archive_groups_originals_20261024.py');OLD=Path('/workspace/collect_four_archive_groups_originals_combined_20261024.py');C=[]
def need(v,s):C.append({'check':s,'passed':bool(v)})
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=P.read_text();old=OLD.read_text();a=ast.parse(t);b=ast.parse(old)
need(h(P)=='dcb9f8adf69e3485c56858a366aa2167d7a2b3df91d0bc97ae9d5ac03464427b','exact frozen new collector pin')
def main(z):return next(n for n in z.body if isinstance(n,ast.FunctionDef) and n.name=='main')
def fn(z,name):return next(n for n in main(z).body if isinstance(n,ast.FunctionDef) and n.name==name)
for name in ['add','tree']:need(ast.dump(fn(a,name))==ast.dump(fn(b,name)),name+' exact previous AST; no new traversal/file policy')
suffix=t[t.index(" with tarfile.open(archive,'w:gz'"):t.index(' result=dict(')]
oldsuffix=old[old.index(" with tarfile.open(archive,'w:gz'"):old.index(' result=dict(')]
need(suffix==oldsuffix,'exact original tar creation/full inventory roundtrip/after-hash byte block')
need("OUT.mkdir();entries={}" in t and "OUT=Path('/workspace/four-additional-archive-groups-originals-20261024')" in t,'fresh dedicated OUT only')
need("assert len(plans)==1 and [g['count'] for g in plans[0]['groups']]==[7,7,7,7]" in t and 'assert len(archive_bodies)==28' in t and 'assert gross==300097536' in t,'exact new 4x7 scope and allocation total')
need("r['exit_code']==0" in t and "a['actual_process_returncode']==0" in t and "r['all_original_payload_paths_retained']" in t and "r['all_original_receipt_bytes_preserved']" in t,'true terminal originals required')
need("r['plan_sha256']==digest(prep/'PLAN.json')" in t and "not a['timeout_expired']" in t,'actual plan binding and no outer timeout')
need("tree(prep,'preparation/'+label);tree(actual,'actual/'+label);tree(outer,'launch/'+label)" in t,'entire original prep/actual/outer small streams retained')
need("tree('/workspace/four-additional-terminal-archives-preparation-20261024','initial-prefix-preparation-failure')" in t,'first prefix rejection entire originals retained')
need('prepare_four_additional_terminal_archive_groups_20261024.py' in t and 'prepare_four_additional_terminal_archive_groups_v2_20261024.py' in t,'both original producer versions retained')
for n in ['FOUR_ADDITIONAL_ARCHIVE_GROUPS_STATIC_PEER.json','review_four_additional_archive_groups.py','FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_METADATA_PEER.json','review_four_additional_archive_groups_actual.py']:
 need(n in t,'independent peer/helper included '+n)
for n in ['FOUR_ADDITIONAL_ARCHIVE_GROUPS_STATIC_PEER.json','FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_METADATA_PEER.json']:
 p=O/n;r=json.loads(p.read_text());need(r['exit_code']==0 and not r['findings'],'actual existing peer accepts '+n)
need("peer['exit_code']==0 and not peer['findings']" in t,'collector enforces actual independent peer acceptance')
need("assert not archive_bodies.intersection(x['source'] for x in entries.values())" in t,'28 original archive payload paths explicitly excluded')
need("assert s.st_size<4*1024*1024" in t and "('.tar.gz','.zip','.exe','.pyc')" in t,'original per-file size/type policy unchanged')
need('original-tools/previous-three-groups-executor.py' in t and 'previous-four-groups-collector.py' in t,'adaptation references included')
need("readj(t['path'])==t['original_rows']" in t and "digest(x['path'])==x['sha256']" in t,'original historical red terminal fields and anchor bytes preserved')
need('all_original_payload_paths_retained' in t and 'Original54 terminal rows including failures remain unchanged' in t,'storage success never relabels historical product failure')
need('no independent outer producer transcript' in t and 'nothing is backfilled' in t,'producer direct-exec limitation honest')
need('previous large archive groups and4 additional groups' in t and 'Every applicable alias must be de-linked' in t,'separate immutable leases retained')
need('Gross300097536 source block saving is not net df recovery' in t,'allocation versus df effect separated')
need('Independent post-package peer is adjacent to avoid self-reference' in t,'actual package peer remains pending')
findings=[c['check'] for c in C if not c['passed']]
r={'scope':'Static small-original collector review; no collection, compression or archive-body read executed','checks':len(C),'exit_code':int(bool(findings)),'findings':findings,'collector_sha256':h(P),'previous_collector_sha256':h(OLD),'conditions':['Run only in root-authorized gap after #345 exclusive slot.','Actual package inventory/roundtrip still requires independent terminal review.'],'check_details':C}
p=O/'FOUR_ADDITIONAL_COLLECTOR_STATIC_PEER.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':len(C),'exit_code':r['exit_code'],'findings':findings},ensure_ascii=False));raise SystemExit(r['exit_code'])
