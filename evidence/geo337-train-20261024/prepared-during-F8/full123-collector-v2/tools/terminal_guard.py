"""Terminal metadata only. Never run the original CLI or modify source/ledger."""
from pathlib import Path
import collections,contextlib,fcntl,hashlib,json,os,stat
HERE=Path(__file__).resolve().parent
F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
JOB=Path('/tmp/geo337-full123-F8-job-20261025')
OUTER=Path('/tmp/geo337-full123-F8-launch-20261025')
CACHE=Path('/workspace/geo337-full123-F8-cache-20261025')
ROOT=Path('/tmp/train337-323-f64d638f-source')
TMP=Path('/tmp/geo337-full123-F8-tmp-20261025')
LOCKS=('/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock')
def need(ok,message):
    if not ok:raise RuntimeError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'duplicate JSON key: '+k);d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs)
def read_regular(path):
    p=Path(path);s=p.lstat();need(stat.S_ISREG(s.st_mode) and not p.is_symlink(),'regular original file required: '+str(p))
    return p.read_bytes()
def verify_preparation(expected):
    raw=read_regular(HERE/'PREPARATION.json');need(digest(raw)==expected,'preparation SHA mismatch');p=strict_json(raw)
    for item in p['files']+p['original_tools']:
        q=Path(item['path']);q=q if q.is_absolute() else HERE/q
        b=read_regular(q);need(len(b)==item['bytes'] and digest(b)==item['sha256'],'frozen tool changed: '+str(q))
    return p
@contextlib.contextmanager
def terminal_lease():
    held=[]
    try:
        for name in LOCKS:
            p=Path(name);need(p.is_file() and not p.is_symlink(),'existing original lock required');f=p.open('r+b');held.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        consumers=[]
        for d in Path('/proc').iterdir():
            if not d.name.isdigit() or int(d.name)==os.getpid():continue
            try:
                raw=(d/'cmdline').read_bytes();argv=[x.decode(errors='replace') for x in raw.split(b'\0') if x]
                # Exact argument paths, not substring hits in parent shell source text.
                hit=any(x==str(p) or x.startswith(str(p)+'/') for x in argv for p in (JOB,OUTER,CACHE,ROOT,TMP))
                try:cwd=(d/'cwd').resolve()
                except (FileNotFoundError,ProcessLookupError):cwd=None
                hit=hit or (cwd is not None and any(cwd==p or cwd.is_relative_to(p) for p in (JOB,OUTER,CACHE,ROOT,TMP)))
                if hit:consumers.append({'pid':int(d.name),'argv':argv,'cwd':str(cwd) if cwd else None})
            except (FileNotFoundError,ProcessLookupError):continue
        need(not consumers,'original ROOT/job/cache consumer still active: '+json.dumps(consumers,ensure_ascii=False))
        yield
    finally:
        for f in reversed(held):f.close()
def classify(job,outer,observer,mapping,bridge,ledger):
    """Independent terminal facts, not a replacement mutation verdict judge."""
    conditions={}
    def fact(k,v):conditions[k]=bool(v)
    phases=job.get('phases',[])
    names=[x.get('phase') for x in phases]
    exits=[x.get('command',{}).get('actual_process_returncode') for x in phases]
    fact('exact_four_original_phases',names==['original-tracked-ledger-check','original-full123-passive-observer','original-core-stream-map','original-new-ledger-check'])
    fact('original_full_map_newcheck_zero',len(exits)==4 and all(type(x) is int for x in exits) and exits[1:]==[0,0,0])
    fact('tracked_check_is_recorded',len(exits)==4 and type(exits[0]) is int)
    fact('outer_and_root_zero',outer.get('actual_exit')==0 and job.get('exit_code')==0 and job.get('passed') is True)
    fact('CLI_zero',job.get('original_cli_exit')==0 and observer.get('original_exit')==0 and observer.get('original_completed') is True)
    fact('observer_complete',observer.get('observer_complete') is True and observer.get('source_tool_bytes_unchanged') is True and observer.get('observation_errors')==[] and observer.get('source_sha')==F8)
    fact('source_fixed',job.get('sourceSHA')==F8 and outer.get('source_sha')==F8)
    fact('mapper_passed',mapping.get('passed') is True and mapping.get('failures')==[] and bool(mapping.get('mappings')))
    fact('bridge_inventory_complete',bridge.get('errors')==[] and bool(bridge.get('files')))
    rows=list(ledger.values()) if isinstance(ledger,dict) else []
    heads=[r.get('execution',{}).get('head') for r in rows if isinstance(r,dict) and isinstance(r.get('execution'),dict)]
    retired=[k for k,r in ledger.items() if isinstance(r,dict) and r.get('verdict')=='retired'] if isinstance(ledger,dict) else []
    fact('exact_123_rows',len(rows)==123 and job.get('ledger_count')==123)
    fact('exact_120_natural_F8_heads',len(heads)==120 and set(heads)=={F8} and job.get('execution_head_counts')=={F8:120})
    fact('exact_3_retired',len(retired)==3)
    before=job.get('source_before');fact('source_before_after_final_equal',bool(before) and job.get('source_after')==before and job.get('source_final')==before)
    return {'source_sha':F8,'formal_accepted':all(conditions.values()),'adoption_eligible_before_peer':all(conditions.values()),'conditions':conditions,'failed_conditions':[k for k,v in conditions.items() if not v],'phase_exits':dict(zip(names,exits)),'original_cli_exit':job.get('original_cli_exit'),'root_exit':job.get('exit_code'),'outer_exit':outer.get('actual_exit'),'record_count':len(rows),'execution_head_counts':dict(collections.Counter(heads)),'retired_ids':retired,'verdicts':dict(collections.Counter(r.get('verdict') for r in rows if isinstance(r,dict))),'tracked_check_is_not_relabelled':True}
def parse_optional_terminal(raw,label):
    try:
        value=strict_json(raw);need(isinstance(value,dict),'terminal child JSON must be an object')
        return value,[]
    except (ValueError,TypeError,UnicodeDecodeError,RuntimeError) as exc:
        return {},[{'child':label,'type':type(exc).__name__,'error':str(exc),'raw_bytes_retained':True}]

def bound_terminal(request,request_sha256):
    raw=read_regular(request);need(digest(raw)==request_sha256,'bound request pin mismatch');r=strict_json(raw)
    need(r.get('binding_status')=='BOUND_AFTER_REAL_TERMINAL' and r.get('source_sha')==F8,'unbound or wrong-source request rejected')
    expected={'job_receipt':str(JOB/'receipt.json'),'outer_result':str(OUTER/'RESULT.json')}
    bindings={};objects={}
    for name,item in r['terminal_bindings'].items():
        p=Path(item['path']);need(p.is_absolute() and (p.is_relative_to(Path('/tmp')) or p.is_relative_to(Path('/workspace'))),'private original terminal path required')
        if name in expected:need(str(p)==expected[name],'wrong original terminal binding '+name)
        b=read_regular(p);need(digest(b)==item['sha256'],'terminal original changed '+name);bindings[name]={'path':str(p),'sha256':digest(b),'bytes':len(b)};objects[name]=strict_json(b)
    need(set(bindings)=={'job_receipt','outer_result','original_tool_final'},'all three actual terminal objects required')
    final=objects['original_tool_final'];need(type(final.get('exit_code')) is int and not final.get('session_id'),'original exec terminal response must have actual exit_code and no running session')
    job=objects['job_receipt'];outer=objects['outer_result'];need(job.get('sourceSHA')==outer.get('source_sha')==F8 and isinstance(job.get('endedUtc'),str),'matching ended original source receipts required')
    need(type(outer.get('actual_exit')) is int and outer['actual_exit']==job.get('exit_code')==final['exit_code'],'original outer/root/tool terminal exits disagree')
    cmd=outer.get('command',{});need(cmd.get('actual_process_returncode')==outer['actual_exit'] and cmd.get('source_sha')==F8 and isinstance(cmd.get('ended_epoch'),(int,float)),'outer original command lacks true terminal')
    need(job.get('root')==str(ROOT) and job.get('cache')==str(CACHE),'original root/cache changed')
    observer={};mapping={};bridge={};ledger={};missing=[];terminal_files={};parse_errors=[]
    for name,p in [('observer',JOB/'observer/receipt.json'),('mapping',JOB/'CORE_RAW_MAPPING.json'),('bridge',JOB/'BRIDGE_RAW_INVENTORY.json'),('ledger',JOB/'mutants_results.json')]:
        if p.exists():
            b=read_regular(p);terminal_files[name]={'path':str(p),'sha256':digest(b),'bytes':len(b)};value,child_errors=parse_optional_terminal(b,name);parse_errors.extend(child_errors)
        else:missing.append(str(p));value={}
        if name=='observer':observer=value
        elif name=='mapping':mapping=value
        elif name=='bridge':bridge=value
        else:ledger=value
    facts=classify(job,outer,observer,mapping,bridge,ledger)
    facts['conditions']['optional_terminal_JSON_valid']=not parse_errors
    facts['optional_terminal_parse_errors']=parse_errors
    if 'ledger' in terminal_files:
        actual=terminal_files['ledger']['sha256'];facts['conditions']['ledger_hash_matches_original_receipt']=job.get('ledger_sha256')==actual;facts['conditions']['mapper_ledger_hash_matches']=mapping.get('ledger_sha256')==actual
    else:facts['conditions']['ledger_present']=False
    facts['failed_conditions']=[k for k,v in facts['conditions'].items() if not v];facts['formal_accepted']=not facts['failed_conditions'];facts['adoption_eligible_before_peer']=facts['formal_accepted']
    facts.update(terminal_capture_ready=True,terminal_bindings=bindings,terminal_files=terminal_files,missing_terminal_files=missing,request_sha256=digest(raw),adoption_requires_independent_actual_and_package_peers=True)
    return facts
