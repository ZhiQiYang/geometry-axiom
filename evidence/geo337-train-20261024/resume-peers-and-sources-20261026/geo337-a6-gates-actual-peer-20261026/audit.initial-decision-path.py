from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re

OUT=Path('/tmp/geo337-a6-gates-actual-peer-20261026')
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'a6-architecture-gates-original-20261026'
OUTER=OWN/'a6-gates-root-original-20261026'
SOURCE=OWN/'a6-architecture-source-20261026'
SHA='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
INPUT_PIN='57ff6c1b4f172fde46df05f5ecb1632af53ad62a809f0571a08f3f929a290956'
checks=0;errors=[]
def check(ok,label):
    global checks
    checks+=1
    if not ok:errors.append(label)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
raw=(ROOT/'RESULT.json').read_bytes();result=json.loads(raw);outer=read(OUTER/'RESULT.json')
check(result['source_sha']==SHA and outer['source_sha']==SHA,'actual a6 source binding')
check(result['exit_code']==result['wrapper_exit']==outer['exit_code']==0,'true inner/wrapper/outer zero exits')
check(outer['stack_soft_bytes']==16777216,'original16MiB stack')
check(not result['full_native_executed'] and not result['full123_executed'] and not result['historical_gates_relabelled'],'no other gates or historical relabelling')
check(result['before']==result['after'] and result['before']['head']==SHA and result['before']['status']=='','exact clean before/after source state')
inputs_before=(ROOT/'SOURCE_INPUTS.before.json').read_bytes();inputs_after=(ROOT/'SOURCE_INPUTS.after.json').read_bytes()
check(inputs_before==inputs_after and H(inputs_before)==INPUT_PIN,'complete604 source snapshot bytes unchanged')
check(result['source_inputs_before_sha256']==result['source_inputs_after_sha256']==INPUT_PIN,'source snapshot recorded pins')
inputs=json.loads(inputs_before);check(len(inputs)==604 and len({x['path'] for x in inputs})==604,'604 unique source inputs')
request=read(ROOT/'ROOT_REQUEST.json');check(request['source_sha']==SHA and request['root_execution_lease'] is True,'original root request actuala6')
for name in ['source_result','source_actual_peer']:
    bound=request[name];data=Path(bound['path']).read_bytes();d=json.loads(data)
    check(H(data)==bound['sha256'] and d['source_sha']==SHA and d['exit_code']==0,'original bound '+name)
source_result=read(Path(request['source_result']['path']))
source_manifest_path=Path(request['source_result']['path']).parent/'SOURCE_MANIFEST.json'
source_manifest_raw=source_manifest_path.read_bytes();source_manifest=json.loads(source_manifest_raw)
check(H(source_manifest_raw)==source_result['source_manifest_sha256'],'actual source materialization manifest pin')
check(set(source_manifest['architecture_paths'])=={x['path'] for x in inputs},'exact604 source manifest closure')
for x in inputs:
    check(x['git_blob']==source_manifest['files'][x['path']]['oid'],'original a6 blob '+x['path'])
decision=next(x for x in inputs if x['path']=='決策佇列.md')
check(decision['raw_sha256']=='e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740','a6 decision input is not historicalS10')

commands=[];catalog=[];rawbytes=0
for base in [ROOT,OUTER]:
    rows=read(base/'subcommands.json')
    for r in rows:
        directory=Path(r['directory']);check(directory.is_relative_to(base),'command directory scope '+str(directory))
        q=read(directory/'request.json');actual=read(directory/'result.json')
        check(actual==r,'original command aggregate '+str(directory))
        for k in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','stdin_provided','stdin_sha256','started_epoch']:
            check(q.get(k)==r.get(k),'original request/result '+k+' '+str(directory))
        check(type(r['actual_process_returncode']) is int and r['actual_process_returncode']==0 and r['timeout_expired'] is False,'actual command0 no timeout '+str(directory))
        for stream in ['stdin','stdout','stderr']:
            p=directory/(stream+'.bin');b=p.read_bytes();rawbytes+=len(b)
            check(H(b)==r[stream+'_sha256'],'full original hash '+str(p))
            if stream!='stdin':check(len(b)==r[stream+'_bytes'],'full original byte length '+str(p))
            catalog.append([str(p),len(b),H(b)])
        commands.append(r)
check(len(commands)==10,'nine inner plus one outer command')
check(len({x['directory'] for x in commands})==10,'unique original commands')
inner=read(ROOT/'subcommands.json')
check([x['command'][3:] for x in inner[:3]]==[['-c','maintenance.auto=false','rev-parse','HEAD'],['-c','maintenance.auto=false','status','--porcelain=v1','--untracked-files=all'],['-c','maintenance.auto=false','ls-files','--stage','-z']],'before identity argv')
check([x['command'] for x in inner[:3]]==[x['command'] for x in inner[6:9]],'before/after identical identity commands')
for before,after in zip(inner[:3],inner[6:9]):
    check((Path(before['directory'])/'stdout.bin').read_bytes()==(Path(after['directory'])/'stdout.bin').read_bytes(),'before/after full original identity bytes')
check((Path(inner[0]['directory'])/'stdout.bin').read_text().strip()==SHA,'original git HEAD stdouta6')
check((Path(inner[1]['directory'])/'stdout.bin').read_bytes()==b'','original git status empty')
check(H((Path(inner[2]['directory'])/'stdout.bin').read_bytes())==result['before']['index'],'index field is exact ls-files stage output hash')
expected=[('architecture-contract',['tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],None),('architecture-unit',['tests/test_architecture_contract.py'],205),('product-architecture-unit',['tests/test_product_architecture.py'],18)]
gates=[]
check(len(result['gates'])==3,'exactly three original judges')
for record,(name,args,count),original in zip(result['gates'],expected,inner[3:6]):
    row=record['command'];directory=Path(row['directory'])
    check(record['gate']==name and record['exit_code']==0 and row==original,'gate actual row '+name)
    check(Path(row['command'][0]).name=='python3' and row['command'][1:]==['-B',*args],'exact original judge argv '+name)
    check(row['cwd']==str(SOURCE) and row['source_sha']==row['acceptance_sha']==SHA,'actual a6 judge identity '+name)
    check(row['environment']['PYTHONOPTIMIZE'] is None and row['environment']['PYTHONDONTWRITEBYTECODE']=='1','judge environment '+name)
    stdout=(directory/'stdout.bin').read_bytes();stderr=(directory/'stderr.bin').read_bytes()
    if count is None:
        scan=json.loads(stdout);check(scan['ok'] is True and scan['diagnostics']==[] and stderr==b'','contract original scan clean')
    else:
        text=stderr.decode();check(stdout==b'' and re.search(r'Ran '+str(count)+r' tests in [0-9.]+s\n\nOK\n\Z',text) is not None,'original test count and clean OK '+name)
        check(not re.search(r'(?im)\bskipped\b|\bexpected failure\b|\bunexpected success\b',text),'zero skips/special outcomes '+name)
        if count==205:check(len(re.findall(r'(?m)^test_.* \.\.\. ok$',text))==205,'all205 verbose outcomes are ok')
        if count==18:check(text.splitlines()[0]=='.'*18,'all18 product test dots')
    gates.append({'name':name,'exit_code':0,'test_count':count,'skips':0,'command':row['command'],'stdout_bytes':len(stdout),'stdout_sha256':H(stdout),'stderr_bytes':len(stderr),'stderr_sha256':H(stderr),'started_utc':datetime.fromtimestamp(row['started_epoch'],timezone.utc).isoformat(),'ended_utc':datetime.fromtimestamp(row['ended_epoch'],timezone.utc).isoformat(),'elapsed_seconds':row['ended_epoch']-row['started_epoch']})
report={'schema':'a6-original-three-architecture-gates-actual-peer/1','source_sha':SHA,'gate_result_sha256':H(raw),'exit_code':1 if errors else 0,'blocking_findings':errors,'checks':checks,'reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'outer_result_sha256':H((OUTER/'RESULT.json').read_bytes()),'gates':gates,'generic_test_count':205,'product_test_count':18,'skip_count':0,
 'input_count':604,'source_inputs_sha256':INPUT_PIN,'source_before_after_equal':result['before']==result['after'],'original_command_count':len(commands),'original_raw_stream_count':len(catalog),'original_raw_stream_bytes':rawbytes,'original_raw_catalog_sha256':H(json.dumps(catalog,separators=(',',':')).encode()),
 'original_physical_index_preservation_basis':'Original pinned gate driver checks original physical index bytes/device/inode/size/mtime before returning0. RESULT index field is the captured git ls-files --stage output hash, not a separately archived pair of physical-index hashes.',
 'S10_results_relabelled':False,'formal_judges_rerun_by_peer':False,'full_native_or_full123_run':False,
 'limits':['This accepts the three original architecture judges executed at a6 only; it does not adopt four artifacts or prove any later final SHA.','All captured original argv/environment/stdin/stdout/stderr were verified without rerunning judges.','The peer compares original source snapshots and materialization metadata; it does not scan the live source tree or grant a writer/cleanup lease.']}
OUT.mkdir(exist_ok=True);p=OUT/'REVIEW.json'
if p.exists():raise RuntimeError('refuse overwrite existing review')
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(report['exit_code'])
