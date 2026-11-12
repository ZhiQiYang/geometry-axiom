"""Small static evidence/source readback; no remote request, C or writes to owner."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
PUB=Path('/workspace/geo300-capacity512-publication-20261024/host-v5-source-publication')
DRAFT=PUB.parent/'host-v5-draft'
REPO=Path('/workspace/geo300-capacity512-work-20261024')
F='0f695866c0ba12d2c70dfd7d40628d0fda0f905f'
E='391f44da1c3e37e50c7a25a8a855b93c2865062c'
checks=[]
def check(name,value):checks.append({'name':name,'ok':bool(value)})
def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):
    p=subprocess.run(['git','-C',str(REPO),*args],capture_output=True)
    check('read-only git exit '+str(args),p.returncode==0)
    return p.stdout
result=json.loads((PUB/'RESULT.json').read_text());rows=json.loads((PUB/'subcommands.json').read_text());manifest=json.loads((DRAFT/'MANIFEST.json').read_text())
check('actual F and E',result['source_sha']==F and result['head_before']==E)
check('publication flags',all(result[x] is True for x in ('committed','pushed','remote_verified','success')))
check('no formal claims',all(result[x] is False for x in ('formal_acceptance','C_executed','generator_executed')))
check('reviewed manifest same',result['files']==manifest['files'])
check('exact 21 captured children',len(rows)==result['commands']==21)
for i,row in enumerate(rows):
    d=Path(row['directory'])
    check(f'child {i} actual exit0',row['actual_process_returncode']==0 and row['timeout_expired'] is False)
    check(f'child {i} only df/git',row['command'][0] in ('df','git'))
    for stream in ('stdout','stderr'):
        data=(d/(stream+'.bin')).read_bytes()
        check(f'child {i} {stream} original pin',len(data)==row[stream+'_bytes'] and sha(data)==row[stream+'_sha256'])
commands=[r['command'] for r in rows]
push=['git','push','origin','refs/heads/'+result['branch']+':refs/heads/'+result['branch']]
check('one normal push',commands.count(push)==1 and not any('--force' in c for c in commands))
remote=[r for r in rows if r['command'][:3]==['git','ls-remote','--refs']]
check('two remote observations',len(remote)==2)
check('remote parent first',(Path(remote[0]['directory'])/'stdout.bin').read_text().split()==[E,'refs/heads/'+result['branch']])
check('remote F last',(Path(remote[-1]['directory'])/'stdout.bin').read_text().split()==[F,'refs/heads/'+result['branch']])
check('source HEAD F',git('rev-parse','HEAD').decode().strip()==F)
check('single regular parent E',git('show','-s','--format=%P',F).decode().strip()==E)
check('three changed leaves only',git('diff-tree','--no-commit-id','--name-only','-r',F).decode().splitlines()==sorted(manifest['files']))
for path,record in manifest['files'].items():
    data=git('show',F+':'+path)
    check(path+' public exact reviewed candidate',data==(DRAFT/'candidate'/path).read_bytes())
    check(path+' public pin',sha(data)==record['after_sha256'] and len(data)==record['bytes'])
check('source clean now',git('status','--porcelain=v1','--untracked-files=all')==b'')
df=(Path(rows[0]['directory'])/'stdout.bin').read_text()
check('fresh df records original guard met',any(int(line.split()[3])>=25*1024*1024 for line in df.splitlines()[1:] if line.endswith('/workspace')))
report={'scope':'Actual publication metadata and three small public Git leaf bytes only; no source test/generator/C execution or remote retry','source_sha':F,'parent':E,'checks':len(checks),'passed':sum(c['ok'] for c in checks),'failed':sum(not c['ok'] for c in checks),'findings':[c for c in checks if not c['ok']],'notes':['All 21 recorded child exits are actual zero; publisher outer exit is reported by owner, not independently rerun here.','Formal H7 and helper withdrawals, placed512 acceptance, stack, ledger and architecture remain UNRUN at F.','PR body Dfd206 still describes prior source until owner publishes an updated body.']}
(HERE/'PUBLICATION_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
(HERE/'PUBLICATION_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False));print(sha((HERE/'PUBLICATION_REVIEW.json').read_bytes()))
raise SystemExit(bool(report['failed']))
