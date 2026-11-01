"""Publish frozen probe evidence and an ordinary child body commit only."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
H=Path(__file__).resolve().parent
R=Path('/workspace/geo323-edge-probe-work-20261024')
O=H/'evidence-publication'
S='a543eef67b81f8d8800f32d5dc4a5641840d2943'
BR='codex/train337-edge-probe-20261024';BODYBR=BR+'-prbody'
PREFIX='evidence/geo323-edge-probe-a543eef6/'
P=H/'evidence-package'
PEER=Path('/workspace/geo323-edge-probe-independent-peer-20261024/PACKAGE_REVIEW.json')
FILES={PREFIX+n:P/n for n in ('ORIGINALS.tar.gz','RAW_INDEX.json','SUMMARY.json')}
FILES.update({PREFIX+n:H/n for n in ('PROGRESS.md','QUESTIONS.md','NEXT.md','PR_REQUEST.json')})
FILES[PREFIX+'PACKAGE_REVIEW.json']=PEER
FILES[PREFIX+'publish_probe_evidence_and_body.py']=Path(__file__).resolve()
report={'source_sha':S,'branch':BR,'evidence_pushed':False,'body_pushed':False,'commands':[],'exit':None}
def sha(data):return hashlib.sha256(data).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def git(*args,data=None):
    env=os.environ.copy()
    for name in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_NAMESPACE'):env.pop(name,None)
    command=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args]
    result=subprocess.run(command,cwd=R,env=env,input=data,capture_output=True)
    d=O/'commands'/f'{len(report["commands"])+1:03d}';d.mkdir(parents=True)
    (d/'stdout').write_bytes(result.stdout);(d/'stderr').write_bytes(result.stderr)
    if data is not None:(d/'stdin').write_bytes(data)
    row={'command':command,'cwd':str(R),'actual_exit':result.returncode,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr),'stdin_sha256':None if data is None else sha(data)}
    (d/'result.json').write_text(json.dumps(row,indent=2)+'\n');report['commands'].append(row)
    need(result.returncode==0,'Git failure; preserve raw '+str(d))
    return result.stdout
def main():
    O.mkdir(exist_ok=False)
    try:
        fs=os.statvfs('/workspace');report['free_bytes_before']=fs.f_bavail*fs.f_frsize
        need(report['free_bytes_before']>=20*1024*1024,'evidence/index resource budget')
        need(git('rev-parse','HEAD').decode().strip()==S,'owned fixed source')
        need(git('symbolic-ref','--short','HEAD').decode().strip()==BR,'owned branch')
        need(git('status','--porcelain=v1','--untracked-files=all')==b'','clean source before evidence')
        need(git('ls-remote','--heads','origin','refs/heads/'+BR).decode().split()==[S,'refs/heads/'+BR],'public source exact')
        need(git('for-each-ref','--format=%(refname)','refs/heads/'+BODYBR)==b'','new body branch absent locally')
        need(git('ls-remote','--heads','origin','refs/heads/'+BODYBR)==b'','new body branch absent remotely')
        summary=json.loads((P/'SUMMARY.json').read_text())
        need(summary['source_sha']==S and summary['exit']==0 and summary['roundtrip_all_bytes_equal'],'fixed source package summary')
        need(sha((P/'ORIGINALS.tar.gz').read_bytes())==summary['archive_sha256']=='b1b47ef8d89b264cc08924e48e99672872386ef2292e23ffe9b2be0e93dc62fa','reviewed archive exact')
        need(sha((P/'RAW_INDEX.json').read_bytes())==summary['raw_index_sha256']=='24b051068097fee5901cb800f08c0320e94f5e939752f0e7f2b8571a2d261914','reviewed raw index exact')
        peer=json.loads(PEER.read_text())
        need(peer['exit']==0 and peer.get('findings',[])==[],'independent package review passed')
        frozen={row['local']:row for row in json.loads((P/'RAW_INDEX.json').read_text())['files']}
        for name in ('PROGRESS.md','QUESTIONS.md','NEXT.md','PR_REQUEST.json','PR_BODY.template.md'):
            path=H/name;need(sha(path.read_bytes())==frozen[str(path)]['sha256'],'reviewed frozen document changed '+name)
        report['files']={name:{'local':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}for name,path in FILES.items()}
        need(sum(x['bytes'] for x in report['files'].values())<4*1024*1024,'reviewed small evidence budget')
        for name,path in FILES.items():
            destination=R/name;need(not destination.exists(),'new evidence path must be absent')
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(path.read_bytes())
        git('add','--sparse','-f','--',*FILES)
        need(set(git('diff','--cached','--name-only').decode().splitlines())==set(FILES),'exact evidence-only staged allowlist')
        git('diff','--cached','--check')
        git('commit','-m','Record edge probe acceptance and preserve the initial harness failure')
        E=git('rev-parse','HEAD').decode().strip();report['evidence_sha']=E
        need(git('show','-s','--format=%P',E).decode().strip()==S,'ordinary evidence parent')
        need(set(git('diff','--name-only',S,E).decode().splitlines())==set(FILES),'evidence only closure')
        git('push','origin','HEAD:refs/heads/'+BR)
        need(git('ls-remote','--heads','origin','refs/heads/'+BR).decode().split()==[E,'refs/heads/'+BR],'public evidence exact')
        report['evidence_pushed']=True
        template=(H/'PR_BODY.template.md').read_bytes();need(template.count(b'__EVIDENCE_HEAD__')==1,'one evidence placeholder')
        body=template.replace(b'__EVIDENCE_HEAD__',E.encode());(O/'PR_BODY.md').write_bytes(body)
        index_path=Path(git('rev-parse','--git-path','index').decode().strip())
        if not index_path.is_absolute():index_path=R/index_path
        index_before=sha(index_path.read_bytes())
        rows=git('ls-tree','-z',E).rstrip(b'\0').split(b'\0');entries={}
        for row in rows:
            mode,name=row.split(b'\t',1);entries[name]=mode
        body_oid=git('hash-object','-w','--stdin',data=body).strip()
        entries[b'PR_BODY.md']=b'100644 blob '+body_oid
        tree=git('mktree','-z',data=b''.join(mode+b'\t'+name+b'\0' for name,mode in sorted(entries.items()))).decode().strip()
        D=git('commit-tree',tree,'-p',E,data=b'Document the current edge probe source and acceptance scope\n').decode().strip();report['body_sha']=D
        need(git('show','-s','--format=%P',D).decode().strip()==E,'ordinary body parent')
        need(git('diff','--name-only',E,D)==b'PR_BODY.md\n','body-only commit')
        git('update-ref','refs/heads/'+BODYBR,D,'0'*40)
        git('push','origin','refs/heads/'+BODYBR+':refs/heads/'+BODYBR)
        need(git('ls-remote','--heads','origin','refs/heads/'+BODYBR).decode().split()==[D,'refs/heads/'+BODYBR],'public body exact')
        need(git('show',D+':PR_BODY.md')==body,'public body bytes exact')
        report['body_pushed']=True;report['body_sha256']=sha(body)
        need(sha(index_path.read_bytes())==index_before,'body leaves source index unchanged')
        need(git('rev-parse','HEAD').decode().strip()==E and git('status','--porcelain=v1','--untracked-files=all')==b'','final evidence head clean')
        report['exit']=0
    except BaseException as exc:
        report['error']=repr(exc);report['exit']=1
    finally:
        (O/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report.get(k) for k in ('evidence_sha','evidence_pushed','body_sha','body_pushed','exit','error')}))
    return report['exit']
if __name__=='__main__':sys.exit(main())
