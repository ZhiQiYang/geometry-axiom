from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, tarfile

OUT = Path('/tmp/geo337-resume-terminal-audit-20261026')
ROOT = Path('/dev/shm/geometry-axiom-geo337-20261025')
SHA = '82c922a3941525d3a094ac0158bdc7dea57ea360'
errors = []
def check(value, description):
    if not value:
        errors.append(description)
def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()
def read(p):
    return json.loads(p.read_bytes())
def stamp(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()

hostroot = Path('/tmp/geo337-S10-full123-host-results-20261025')
host = read(hostroot/'FINAL.json')
check(host['exit_code'] == 0, 'host final exit')
check(json.loads(host['output'])['sourceSHA'] == SHA, 'host source SHA')
receipt_path = ROOT/'F10-ledger-job/receipt.json'
receipt = read(receipt_path)
check(receipt['sourceSHA'] == SHA, 'receipt source SHA')
check(receipt['exit_code'] == receipt['original_cli_exit'] == 0, 'receipt exits')
check(receipt['source_before'] == receipt['source_after'] == receipt['source_final'], 'original source preservation')
check(receipt['verdicts'] == {'killed':114,'equivalent':5,'crashed':1,'retired':3}, 'verdict counts')
phases=[]
for p in receipt['phases']:
    c=p['command']
    phases.append({'phase':p['phase'],'exit':c['actual_process_returncode'],
                   'started_utc':stamp(c['started_epoch']), 'ended_utc':stamp(c['ended_epoch']),
                   'elapsed_seconds':c['ended_epoch']-c['started_epoch'], 'timeout_expired':c['timeout_expired']})
check([p['exit'] for p in phases] == [1,0,0,0], 'exact original phase exits')

package=ROOT/'S10-ledger-complete-package'
index=read(package/'INDEX.json')
archive=package/index['archive']
archive_sha=digest(archive)
check(archive_sha == index['archive_sha256'] == '1ffc61c1c0d8713653d599e34f2f3882b0535817097ffc44bc05a4b4a3b2a97e', 'archive SHA')
check(archive.stat().st_size == index['archive_bytes'] == 9025694, 'archive byte count')
expected={x['path']:x for x in index['members']}
check(len(expected) == len(index['members']) == 1284, 'index member count and unique paths')
seen=set(); total=0; original_bytes=0
with tarfile.open(archive,'r:gz') as t:
    for m in t:
        check(m.isfile(), 'non-file tar member '+m.name)
        check(m.name not in seen, 'duplicate tar member '+m.name)
        seen.add(m.name)
        if m.name not in expected:
            check(False, 'unexpected tar member '+m.name)
            continue
        e=expected[m.name]; b=t.extractfile(m).read(); total+=len(b)
        check(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'], 'tar bytes '+m.name)
        original=Path(e['source'])
        check(original.is_file(), 'original missing '+str(original))
        if original.is_file():
            original_bytes+=original.stat().st_size
            check(original.stat().st_size==e['bytes'] and digest(original)==e['sha256'], 'original changed '+str(original))
check(seen==set(expected), 'tar exact inventory')
check(total==index['logical_bytes']==52999273, 'logical byte count')

peers={}
for dirname,pin in [('geo337-S10-full123-actual-peer-20261025','1a766fb7d0130ecd378d62afd73e94378728669fe873fc11f4c5fe6d877df8cb'),('geo337-S10-full123-package-actual-peer-20261025','be903744e898c18c0a0e00c25d20652c47277c1bef5a9cdaeb7fd5bc25579f90')]:
    p=Path('/tmp')/dirname/'REVIEW.json';d=read(p);h=digest(p)
    check(h==pin and d['exit_code']==0,'existing independent peer '+dirname)
    peers[dirname]={'sha256':h,'exit_code':d['exit_code'],'checks':d['checks']}

ap=ROOT/'S10-architecture-four-assembly-20261025'
a=read(ap/'RESULT.json')
check(a['sourceSHA']==SHA and a['exit_code']==0,'architecture assembly identity/exit')
check(a['originalGateExits']==[0,0,0], 'architecture original gate exits')
outputs={}
for n,v in a['outputs'].items():
    p=ap/'new'/n;h=digest(p)
    check(p.stat().st_size==v['bytes'] and h==v['rawSha256'],'architecture output '+n)
    outputs[n]={'bytes':p.stat().st_size,'sha256':h}
pres=ROOT/'native-TMP-preservation-20261025/RESULT.json';pr=read(pres)
check(pr['exit_code']==0 and pr['originals_removed'] is False,'TMP preservation terminal')
check(pr['remote_delivered'] is False, 'TMP preservation delivery is still false')

report={'schema':'resume-S10-terminal-original-readonly-audit/1','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'source_sha':SHA,'exit_code':1 if errors else 0,'errors':errors,
        'host_final_sha256':digest(hostroot/'FINAL.json'),'host_final_exit':host['exit_code'],
        'receipt_sha256':digest(receipt_path),'started_utc':receipt['startedUtc'],'ended_utc':receipt['endedUtc'],
        'elapsed_seconds':(datetime.fromisoformat(receipt['endedUtc'])-datetime.fromisoformat(receipt['startedUtc'])).total_seconds(),
        'phase_exits':phases,'verdicts':receipt['verdicts'],'ledger_sha256':receipt['ledger_sha256'],
        'execution_head_counts':receipt['execution_head_counts'],
        'package':{'index_sha256':digest(package/'INDEX.json'),'archive_sha256':archive_sha,'archive_bytes':archive.stat().st_size,'verified_members':len(seen),'logical_bytes':total,'original_files_current_bytes':original_bytes},
        'existing_peers':peers,
        'architecture':{'result_sha256':digest(ap/'RESULT.json'),'exit_code':a['exit_code'],'original_gate_exits':a['originalGateExits'],'judges_rerun':a['originalJudgesRerun'],'outputs':outputs},
        'TMP_preservation':{'result_sha256':digest(pres),'exit_code':pr['exit_code'],'started_utc':pr['started_utc'],'ended_utc':pr['ended_utc'],'originals_removed':pr['originals_removed'],'remote_delivered':pr['remote_delivered']},
        'limits':['本次只讀原件，不重跑產品、mutator 或編譯。','原 tracked check 1、M20 crashed、三個 retired 原判保留。','帳本採用、新 final SHA、遠端交付及其後 native/browser/oracle 不在本次唯讀證明內。','架構核對為現存四個產物 byte identity 及原 RESULT，不替代完整架構語意對抗審查。','TMP-preservation 僅核終態 metadata，不宣告所有 26 payload 可刪除或已交付。']}
OUT.mkdir(exist_ok=True)
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(report['exit_code'])
