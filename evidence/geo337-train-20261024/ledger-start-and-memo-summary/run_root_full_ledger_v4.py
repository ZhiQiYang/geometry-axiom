"""Root-only execution driver; prepared/reviewed by child, never launched by it."""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import sys
import xml.etree.ElementTree as ET

F='4f4a24d76e816274bfae06868b4dbf31f0860299'
OLD='f64d638f15c48d2b9723b7ae9d230fb5dacb82d9'
ROOT=Path('/tmp/train337-323-f64d638f-source')
OLD_SEED=Path('/workspace/geo314-train-f64d638f-m121/mutation-cache/_bridge-work')/OLD/'repo'
PARENT_OBJECTS=Path('/workspace/geo314-train-f64d638f-m121/source/.git/objects')
JOB=Path('/tmp/train337-ledger-4f4a24d7-r2')
CACHE=Path('/workspace/train337-ledger-cache-4f4a24d7')
SEED=CACHE/'_bridge-work'/F/'repo'
RESULTS=JOB/'mutants_results.json'
OBS=JOB/'observer'
TEMP=Path('/tmp/train337-ledger-4f4a24d7-r2-tmp')
TOOLS=Path(__file__).resolve().parent
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
REAPER=Path('/workspace/geo261-environment/reap_children.py')
RAW_INDEX=Path('/tmp/geo314-train-f64d638f-launch/ACTUAL_RAW_INDEX.json')
PINS={'retain_mutation_streams.py':'67af8f6768232aa8439a0815a490a8b1076560afd0e40656f6de7edaa009e895',
      'verify_observed_core_raw.py':'12aa2060d03078b96d81ee6b4d28facdb4d3727fb6ff7d0b4c41271f550ac46b'}

def sha(body):return hashlib.sha256(body).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def need(ok,why):
    if not ok:raise RuntimeError(why)
def main():
    need(not JOB.exists() and not CACHE.exists() and not TEMP.exists(),'fresh JOB/CACHE/TMPDIR required')
    JOB.mkdir();TEMP.mkdir()
    record={'schema':'root-original-full-ledger-123/1','sourceSHA':F,
            'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'argv':sys.argv,'root':str(ROOT),'old_seed':str(OLD_SEED),'new_seed':str(SEED),
            'seed_moved':False,'whole_ledger_writer':'root only','outer_capture_timeout':None,
            'original_child_timeouts_changed':False,'product_test_source_changed':False,
            'passed':False,'phases':[],'exit_code':1,'generated_outputs':[]}
    env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))}
    for key in ('PYTHONOPTIMIZE','NODE_OPTIONS','PYTHONPATH','PYTHONSTARTUP'):env.pop(key,None)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',TMPDIR=str(TEMP),
               GITHUB_SHA=F,GITHUB_WORKSPACE=str(ROOT))
    record['environment']={k:env.get(k) for k in ('PATH','LANG','LC_ALL','TMPDIR','CC','CFLAGS','CPPFLAGS','LDFLAGS','PYTHONOPTIMIZE','NODE_OPTIONS','PYTHONPATH','PYTHONSTARTUP','GITHUB_SHA','GITHUB_WORKSPACE')}
    spec=importlib.util.spec_from_file_location('root_ledger_c387',CAPTURE)
    cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
    recorder=cap.Recorder(JOB,env,F)
    lock=None;lock_acquired=False
    raw_manifest=json.loads(RAW_INDEX.read_text())
    need(sha(RAW_INDEX.read_bytes())=='d9d7a39b2b4f007d8968102209a2e4708e3ed3b3b0609fc54f3b659b4ed2ecd1','original raw-index pin')
    source_heads={str(ROOT):OLD,str(OLD_SEED):OLD,str(SEED):OLD}
    def run(argv,cwd=ROOT,check=True,phase=None,transition=False):
        actual_source=source_heads[str(cwd)]
        variant=('checkout-transition-from-'+actual_source+'-to-'+F if transition
                 else 'source-context-before-transition' if actual_source==OLD else 'committed-final-source')
        row,out,err=recorder.run(argv,cwd=cwd,check=check,timeout=None,
                               source_sha=actual_source,source_variant=variant)
        if transition and row['actual_process_returncode']==0:source_heads[str(cwd)]=F
        if phase:record['phases'].append({'phase':phase,'command':row})
        return out
    def raw_guard(label):
        checks=[];errors=[]
        for item in raw_manifest['files']:
            p=Path(item['path'])
            try:
                body=p.read_bytes();match=len(body)==item['bytes'] and sha(body)==item['sha256']
                checks.append({'path':str(p),'bytes':len(body),'sha256':sha(body),'matches_original':match})
                if not match:errors.append('original raw changed '+str(p))
            except Exception as error:
                checks.append({'path':str(p),'error':repr(error)});errors.append(str(p)+' '+repr(error))
        dump(JOB/(label+'-original-raw.json'),{'checks':checks,'errors':errors})
        need(not errors,'original raw guard failed '+label)
    def consumers(paths,label):
        matches=[];errors=[];wanted=[str(p) for p in paths]
        for item in Path('/proc').iterdir():
            if not item.name.isdigit() or int(item.name)==os.getpid():continue
            try:
                text=(item/'status').read_text()
                if any(l.startswith('State:') and '\tZ' in l for l in text.splitlines()):continue
            except OSError:pass
            cwd=cmd=None
            try:cwd=os.readlink(item/'cwd')
            except OSError as error:errors.append({'pid':item.name,'part':'cwd','error':repr(error)})
            try:cmd=(item/'cmdline').read_bytes().replace(b'\0',b' ').decode('utf-8','replace')
            except OSError as error:errors.append({'pid':item.name,'part':'cmdline','error':repr(error)})
            if ((cwd and any(cwd==p or cwd.startswith(p+'/') for p in wanted)) or
                (cmd and any(p in cmd for p in wanted))):
                matches.append({'pid':int(item.name),'cwd':cwd,'cmdline':cmd})
        result={'paths':wanted,'matches':matches,'unreadable_parts':errors,
                'scope':'cwd and cmdline checked independently; unrelated inaccessible OS processes are recorded, not claimed inspected.'}
        dump(JOB/(label+'-consumers.json'),result)
        need(not matches,'live source/seed consumer exists')
    def preserve_generated_svg(label):
        # The only allowed generated output: original main's default SVG in ROOT.
        # It is retained, not deleted or exempted from the subsequent clean guard.
        source=ROOT/'current_geometry.svg'
        if not source.exists() and not source.is_symlink():
            record['generated_outputs'].append({'phase':label,'source':str(source),'present':False})
            return
        before=source.lstat()
        need(stat.S_ISREG(before.st_mode) and not source.is_symlink(),'generated SVG must be a regular nonsymlink')
        tracked_row,_,_=recorder.run(['git','ls-files','--error-unmatch','--','current_geometry.svg'],cwd=ROOT,check=False,timeout=None,source_sha=source_heads[str(ROOT)],source_variant='generated-output-tracking-check')
        need(tracked_row['actual_process_returncode']==1,'default SVG must be untracked, never move tracked source')
        ignore_row,_,_=recorder.run(['git','check-ignore','-v','--','current_geometry.svg'],cwd=ROOT,check=False,timeout=None,source_sha=source_heads[str(ROOT)],source_variant='generated-output-ignore-check')
        need(ignore_row['actual_process_returncode']==0,'default SVG must be ignored by original Git policy')
        need(run(['git','ls-files','--others','--ignored','--exclude-standard','-z','--','current_geometry.svg'])==b'current_geometry.svg\0','only exact ignored default SVG is eligible')
        body=source.read_bytes();parsed=ET.fromstring(body)
        need(parsed.tag in ('svg','{http://www.w3.org/2000/svg}svg'),'expected original SVG XML root')
        signature=lambda st:(st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
        need(signature(source.lstat())==signature(before),'SVG changed during inspection')
        main_raw=(ROOT/'current_geometry.c').read_bytes()
        main_lines=main_raw.decode('utf-8').splitlines()
        tests_lines=(ROOT/'tests/run_tests.py').read_text().splitlines()
        need('預設放在本原始碼旁邊（current_geometry.svg），--out 可以改。' in main_lines[10458] and
             'svg_path, sizeof svg_path, "current_geometry.svg"' in main_lines[10479], 'original main default-output provenance changed')
        need('[exe, "--scene", str(scene), "--no-window"]' in tests_lines[288], 'original run_tests argv provenance changed')
        folder=JOB/'generated-outputs';folder.mkdir(exist_ok=True)
        destination=folder/(label+'-current_geometry.svg')
        need(not destination.exists() and source.stat().st_dev==folder.stat().st_dev,'fresh same-filesystem generated-output destination')
        need(signature(source.lstat())==signature(before),'SVG changed before preservation move')
        os.rename(source,destination)
        retained=destination.read_bytes()
        need(retained==body and not source.exists(),'generated SVG preservation was not byte exact')
        item={'phase':label,'source':str(source),'retained':str(destination),'source_context_sha':source_heads[str(ROOT)],
              'bytes':len(body),'sha256':sha(body),'xml_root':parsed.tag,'move':'same-filesystem rename; no deletion',
              'original_main_raw_sha256':sha(main_raw),'main_lines_10456_10485':'\n'.join(main_lines[10455:10485]),
              'run_tests_lines_288_292':'\n'.join(tests_lines[287:292]),
              'provenance_limit':'Existing pre-ledger SVG matches original CLI default output; no claim which historical command created it.'}
        record['generated_outputs'].append(item)
        dump(folder/(label+'-receipt.json'),item)
    def identity(path,head,label):
        need(path.resolve()==path and stat.S_ISDIR(path.lstat().st_mode) and (path/'.git').is_dir(),'independent regular checkout '+str(path))
        actual=run(['git','rev-parse','HEAD'],path).decode().strip();need(actual==head,label+' HEAD')
        tree=run(['git','rev-parse','HEAD^{tree}'],path).decode().strip()
        need(not run(['git','status','--porcelain=v1','--untracked-files=all'],path),label+' status not clean')
        need(not run(['git','ls-files','--others','--exclude-standard','-z'],path),label+' untracked files')
        need(not run(['git','ls-files','--others','--ignored','--exclude-standard','-z'],path),label+' ignored files')
        run(['git','diff','--cached','--exit-code'],path)
        stages=run(['git','ls-files','--stage','-z'],path)
        refs=run(['git','for-each-ref','--format=%(refname) %(objectname)'],path)
        result={'path':str(path),'head':actual,'tree':tree,'stage_sha256':sha(stages),'refs_sha256':sha(refs)}
        dump(JOB/(label+'-identity.json'),result)
        return result
    code=1
    try:
        lock=open('/tmp/g261r3/heavy.lock','a+b')
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            record['busy']=True;code=75;return code
        lock_acquired=True
        soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
        need(hard==resource.RLIM_INFINITY or hard>=16777216,'16MiB stack unavailable')
        resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard))
        record['stack_before']=[soft,hard];record['stack_after']=list(resource.getrlimit(resource.RLIMIT_STACK))
        record['tools_sha256']={str(CAPTURE):sha(CAPTURE.read_bytes()),str(REAPER):sha(REAPER.read_bytes()),str(Path(__file__)):sha(Path(__file__).read_bytes())}
        need(record['tools_sha256'][str(CAPTURE)]=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original capture changed')
        need(record['tools_sha256'][str(REAPER)]=='7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760','original reaper changed')
        for name,pin in PINS.items():need(sha((TOOLS/name).read_bytes())==pin,'observer/verifier tool pin '+name)
        dump(JOB/'request.json',record)
        raw_guard('before')
        consumers([ROOT,OLD_SEED,SEED],'before')
        preserve_generated_svg('before-F64')
        root_before=identity(ROOT,OLD,'root-before');seed_before=identity(OLD_SEED,OLD,'seed-before')
        alt=OLD_SEED/'.git/objects/info/alternates';alt_bytes=alt.read_bytes()
        need(alt_bytes==(str(PARENT_OBJECTS)+'\n').encode() and PARENT_OBJECTS.is_dir(),'seed parent alternates must remain in place')
        patterns=(OLD_SEED/'.git/info/sparse-checkout').read_bytes()
        need(patterns==b'/*\n!/evidence/\n!/tests/evidence/\n!/tests/release-evidence/\n','original exact seed sparse patterns')
        run(['git','cat-file','-e',F+'^{commit}'],ROOT)
        run(['git','cat-file','-e',F+'^{commit}'],OLD_SEED)
        need(ROOT.stat().st_dev==Path('/tmp').stat().st_dev,'unexpected ROOT mount')
        SEED.parent.mkdir(parents=True)
        need(OLD_SEED.stat().st_dev==SEED.parent.stat().st_dev and not SEED.exists(),'same filesystem fresh seed target')
        consumers([ROOT,OLD_SEED,SEED],'immediate-before-move')
        os.rename(OLD_SEED,SEED);record['seed_moved']=True
        run(['git','-c','core.autocrlf=false','checkout','--detach',F],ROOT,transition=True)
        run(['git','-c','core.autocrlf=false','checkout','--detach',F],SEED,transition=True)
        root_ready=identity(ROOT,F,'root-ready');seed_ready=identity(SEED,F,'seed-ready')
        need(root_ready['refs_sha256']==root_before['refs_sha256'] and seed_ready['refs_sha256']==seed_before['refs_sha256'],'refs changed across detached source transition')
        need((SEED/'.git/objects/info/alternates').read_bytes()==alt_bytes and PARENT_OBJECTS.is_dir(),'parent objects/alternates changed')
        need((SEED/'.git/info/sparse-checkout').read_bytes()==patterns,'seed sparse patterns changed')
        need(not (CACHE/'_bridge-baseline'/F).exists(),'fresh original baseline required')
        run([sys.executable,'-B','tests/mutate.py','--check'],check=False,phase='original-committed-ledger-check')
        env.update(MUTATE_RESULTS=str(RESULTS),MUTATE_CACHE=str(CACHE),GEO261_REAPER_LOG=str(JOB/'full-ledger-reaper.jsonl'))
        record['full_environment_explicit']={k:env[k] for k in ('MUTATE_RESULTS','MUTATE_CACHE','GEO261_REAPER_LOG','GITHUB_SHA','GITHUB_WORKSPACE','TMPDIR')}
        need(not RESULTS.exists() and not OBS.exists(),'fresh external ledger/observer required')
        argv=[sys.executable,'-B',str(REAPER),sys.executable,'-B',str(TOOLS/'retain_mutation_streams.py'),'--root',str(ROOT),'--sha',F,'--out',str(OBS),'--']
        record['full_outer_argv']=argv;dump(JOB/'full-launch-request.json',record)
        run(argv,check=False,phase='original-full-ledger-through-passive-observer')
        preserve_generated_svg('after-F4f-full-cli')
        run([sys.executable,'-B',str(TOOLS/'verify_observed_core_raw.py'),'--ledger',str(RESULTS),'--observations',str(OBS),'--out',str(JOB/'CORE_RAW_MAPPING.json')],check=False,phase='original-core-stream-map')
        run([sys.executable,'-B','tests/mutate.py','--check'],check=False,phase='original-external-new-ledger-check')
        record['original_cli_exit']=json.loads((OBS/'receipt.json').read_text())['original_exit']
        inventory=[]
        ledger=json.loads(RESULTS.read_text())
        bridge_errors=[]
        for mid,row in ledger.items():
            execution=row.get('execution',{})
            if execution.get('schema')!='geometry-bridge-mutation-execution/1':continue
            phases=[]
            for key in ('baseline_build','baseline','mutant_build','mutant','restored_build','restored'):
                if key in execution:phases.append((key,execution[key]))
                else:bridge_errors.append(mid+' missing '+key)
            phases.extend(('mutant_attempt-'+str(i+1),trial) for i,trial in enumerate(execution.get('mutant_attempts',[])))
            for phase,receipt in phases:
                parent=CACHE/'_bridge-baseline'/F if phase in ('baseline_build','baseline') else CACHE/mid
                for stream in ('stdout','stderr'):
                    try:
                        name=receipt[stream+'_file'];need(Path(name).name==name,'original stream filename must be basename')
                        path=parent/name;body=path.read_bytes();need(sha(body)==receipt[stream+'_sha256'],'bridge raw mismatch '+str(path))
                        inventory.append({'id':mid,'phase':phase,'stream':stream,'path':str(path),'bytes':len(body),'sha256':sha(body)})
                    except Exception as error:bridge_errors.append(mid+' '+phase+' '+stream+' '+repr(error))
        dump(JOB/'BRIDGE_RAW_INVENTORY.json',{'files':inventory,'errors':bridge_errors})
        record['ledger_sha256']=sha(RESULTS.read_bytes());record['ledger_count']=len(ledger)
        record['verdicts']={v:sum(row.get('verdict')==v for row in ledger.values()) for v in sorted({row.get('verdict')for row in ledger.values()})}
        record['raw_bridge_rows']=len(inventory)
        raw_guard('after')
        root_after=identity(ROOT,F,'root-after');seed_after=identity(SEED,F,'seed-after')
        need(root_after==root_ready and seed_after==seed_ready,'source/index/refs changed during formal ledger')
        need((SEED/'.git/objects/info/alternates').read_bytes()==alt_bytes and PARENT_OBJECTS.is_dir(),'parent Git objects/alternates changed after formal ledger')
        need(record['original_cli_exit']==0,'original full CLI was not0')
        need(not bridge_errors and inventory,'bridge raw inventory incomplete')
        formal=[p['command']['actual_process_returncode'] for p in record['phases'] if p['phase']!='original-committed-ledger-check']
        need(formal==[0,0,0],'formal original full/stream-map/new-check phase nonzero')
        record['passed']=True;code=0
    except BaseException as error:
        record['error']={'type':type(error).__name__,'repr':repr(error)}
        code=130 if isinstance(error,KeyboardInterrupt) else 1
    finally:
        record['exit_code']=code;record['endedUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['commands']=recorder.rows
        try:raw_guard('final-original-raw')
        except BaseException as error:
            record['raw_final_error']=repr(error);record['passed']=False
            if code==0:code=1;record['exit_code']=1
        if lock_acquired:
            try:preserve_generated_svg('final-leftover')
            except BaseException as error:
                record['generated_output_final_error']=repr(error);record['passed']=False
                if code==0:code=1;record['exit_code']=1
        # Preserve available checkout facts even when a red phase prevented the normal
        # after identity guard; never reset/clean/rollback or hide a failed transition.
        if code!=0 and not record.get('busy'):
            failures=[]
            for label,path in [('root',ROOT),('old-seed',OLD_SEED),('new-seed',SEED)]:
                if not path.exists():continue
                for command in (['git','rev-parse','HEAD'],['git','rev-parse','HEAD^{tree}'],
                                ['git','status','--porcelain=v1','--untracked-files=all'],
                                ['git','ls-files','--stage','-z'],['git','for-each-ref','--format=%(refname) %(objectname)']):
                    try:run(command,path,check=False)
                    except BaseException as error:failures.append({'path':str(path),'command':command,'error':repr(error)})
            record['failure_checkout_snapshot_errors']=failures
        dump(JOB/'receipt.json',record)
        if lock is not None:lock.close()
        print(json.dumps({k:record.get(k) for k in ('sourceSHA','passed','exit_code','original_cli_exit','seed_moved','error','endedUtc')},ensure_ascii=False),flush=True)
    return code

if __name__=='__main__':raise SystemExit(main())
