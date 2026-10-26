from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, os, stat

OUT=Path('/tmp/geo337-resume-tmp-preservation-peer-20261026')
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'native-TMP-preservation-20261025'
PREP=Path('/tmp/geo337-native-TMP-combined-preservation-20261025')
PLAN_PIN='38e28b2e0b63ad263d2eb22beb6f80e90190073d68a40ad9cc9b81f6e1ac83be'
PEER=Path('/tmp/geo337-native-TMP-executors-static-peer-20261025/ARCHIVE_REVIEW.json')
PEER_PIN='8f8a6d704e2eb0a7ef0d7ae913296f19437d8434d9794e352e9f22cf9495a3e7'
errors=[];checks=0
def check(ok,label):
    global checks
    checks+=1
    if not ok:errors.append(label)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def identity(p,size,pin,label):
    check(p.is_file() and not p.is_symlink(),'regular '+label)
    b=p.read_bytes()
    check(len(b)==size and H(b)==pin,'bytes/hash '+label)
    return b

plan_raw=(PREP/'PLAN.v2.json').read_bytes();plan=json.loads(plan_raw)
check(H(plan_raw)==PLAN_PIN,'original plan pin')
check((ROOT/'PLAN.json').read_bytes()==plan_raw,'archived original plan')
peer_raw=PEER.read_bytes();peer=json.loads(peer_raw)
check(H(peer_raw)==PEER_PIN and peer['exit_code']==0 and not peer['blocking_findings'],'archive static peer')
raw=(ROOT/'RESULT.json').read_bytes();result=json.loads(raw)
check(result['exit_code']==0 and result['plan_sha256']==PLAN_PIN,'archive terminal plan and exit')
check(result['originals_removed'] is False and result['remote_delivered'] is False and result['formal_executed'] is False,'no false retirement/delivery/test claim')
check(result['all_26_original_payloads_still_present'] and result['all_full_raw_and_gzip_roundtrips'],'original preservation claims')
check(H((ROOT/'EXECUTOR.py').read_bytes())==result['executor_sha256']==peer['executor_sha256'],'original executor pin')
check(H((ROOT/'COMMON.py').read_bytes())==result['common_sha256']==peer['common_sha256'],'original common pin')
check(H((ROOT/'REQUEST.json').read_bytes())==result['request_sha256'],'original bound request')
indices=read(PREP/'auxiliary-readonly-validation/EXACT_INDEX_LEAVES.json')
elfs=read(PREP/'auxiliary-readonly-validation/EXACT_ELF_LEAVES.json')
expected={x['effective_index']:('private-index',x['original_state'],x) for x in indices}
expected.update({x['path']:('ELF-cache',x['original_state'],x) for x in elfs})
check(len(indices)==2 and len(elfs)==24 and len(expected)==26,'exact original 2 index + 24 ELF scope')
check(len(result['archives'])==26 and {x['original_path'] for x in result['archives']}==set(expected),'archive exact payload set')
payloads=[]
for a in result['archives']:
    path=Path(a['original_path']);kind,state,original_row=expected[str(path)]
    check(a['original_state']==state,'original plan state '+str(path))
    b=identity(path,state['bytes'],state['sha256'],str(path))
    st=path.lstat()
    now={'device':st.st_dev,'inode':st.st_ino,'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid,'nlink':st.st_nlink,'bytes':st.st_size,'allocated':st.st_blocks*512,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns}
    check(all(now[k]==state[k] for k in now),'physical identity '+str(path))
    check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==state['git_blob_sha1'],'original Git blob identity '+str(path))
    check((b.startswith(b'DIRC') if kind=='private-index' else b.startswith(b'\x7fELF')),'expected generated artifact magic '+str(path))
    r=identity(ROOT/a['raw_member'],a['raw_bytes'],a['raw_sha256'],'raw '+str(path))
    z=identity(ROOT/a['gzip_member'],a['gzip_bytes'],a['gzip_sha256'],'gzip '+str(path))
    check(b==r==gzip.decompress(z),'complete original/raw/gzip roundtrip '+str(path))
    check(a['complete_roundtrip'] is True,'original roundtrip claim '+str(path))
    if kind=='ELF-cache':
        fp=Path(original_row['fingerprint_receipt']);check(H(fp.read_bytes())==original_row['fingerprint_sha256'],'original ELF fingerprint '+str(path))
        facts=Path(original_row['owner_facts_path']);check(H(facts.read_bytes())==original_row['owner_facts_sha256'],'original task ownership '+str(path))
    payloads.append({'original_path':str(path),'kind':kind,'bytes':len(b),'raw_sha256':H(b),'raw_member':a['raw_member'],
                     'gzip_member':a['gzip_member'],'gzip_bytes':len(z),'gzip_sha256':H(z),'current_original_exact':True,'full_roundtrip':True})
prereqs=read(ROOT/'PREREQUISITE_PATH_MAP.json')
check(len(prereqs)==24,'original prerequisite count')
for x in prereqs:
    archived=identity(ROOT/x['member'],x['bytes'],x['sha256'],'prerequisite archive '+x['member'])
    identity(Path(x['original_path']),x['bytes'],x['sha256'],'prerequisite original '+x['original_path'])
    check(x['original_path'] in plan['bindings'] and plan['bindings'][x['original_path']]==x['sha256'],'prerequisite plan binding '+x['original_path'])

commands_verified=0;raw_streams=0
def verify_commands(rows,scope):
    global commands_verified,raw_streams
    for row in rows:
        d=Path(row['directory']);r=read(d/'result.json');q=read(d/'request.json')
        check(r==row,scope+' original command aggregate '+str(d))
        for k in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','stdin_provided','stdin_sha256','started_epoch']:
            check(q.get(k)==r.get(k),scope+' request/result '+k+' '+str(d))
        for n in ['stdout','stderr']:
            identity(d/(n+'.bin'),r[n+'_bytes'],r[n+'_sha256'],scope+' '+n+' '+str(d));raw_streams+=1
        check(H((d/'stdin.bin').read_bytes())==r['stdin_sha256'],scope+' stdin '+str(d));raw_streams+=1
        check(r['actual_process_returncode']==0 and not r['timeout_expired'],scope+' actual zero terminal '+str(d))
        commands_verified+=1
verify_commands(result['commands'],'archive')
check(read(ROOT/'commands/subcommands.json')==result['commands'],'archive command aggregate equality')
outer=OWN/'native-TMP-preservation-root-original-20261025'
o=read(outer/'RESULT.json')
check(o['actual_exit']==0 and o['retirement_executed'] is False and o['request_sha256']==result['request_sha256'],'outer true zero and no retirement')
verify_commands(read(outer/'subcommands.json'),'outer')
inventory=[]
for base in [ROOT,outer]:
    for p in sorted(base.rglob('*')):
        check(not p.is_symlink(),'no symlink '+str(p))
        if p.is_file():inventory.append({'source_path':str(p),'bytes':p.stat().st_size,'sha256':H(p.read_bytes())})
report={'schema':'native-TMP-preservation-independent-actual-peer/1','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'exit_code':1 if errors else 0,'blocking_findings':errors,'checks':checks,
        'archive_result_sha256':H(raw),'plan_sha256':PLAN_PIN,'archive_static_peer_sha256':PEER_PIN,
        'original_payloads_verified':len(payloads),'raw_payload_bytes':sum(x['bytes'] for x in payloads),'gzip_payload_bytes':sum(x['gzip_bytes'] for x in payloads),
        'all_original_payloads_still_present':not errors,'original_commands_verified':commands_verified,'original_raw_streams_verified':raw_streams,
        'preservation_file_count':len(inventory),'preservation_bytes':sum(x['bytes'] for x in inventory),
        'retirement_executed':False,'actual_freed_bytes':0,'remote_delivery_verified':False,
        'ownership_basis':'Exactly the approved two private Git indices and 24 old generated ELF cache leaves; verified original ownership/fingerprint pins, exact byte/state identity, DIRC/ELF signatures. No arbitrary user source, fixture, personal file or unlisted cache added.',
        'limits':['No unlink, retirement, lease modification, Git mutation, formal test, compiler or network operation performed.',
                  'Both complete raw_member and gzip_member must be remote-verified before the original retirement guard can accept; no gzip-only exception.',
                  'This is complete artifact preservation, not source semantics validation; indices retain original repository path metadata and ELFs retain original compiled bytes.',
                  'No claim that other processes or environments are inactive; retirement requires a fresh root lease/consumer guard.',
                  'Original frozen metadata and any old failures stay intact; no remote delivery or disk recovery claimed.']}
OUT.mkdir(exist_ok=True)
(OUT/'PAYLOADS.json').write_text(json.dumps(payloads,ensure_ascii=False,indent=2)+'\n')
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(report['exit_code'])
