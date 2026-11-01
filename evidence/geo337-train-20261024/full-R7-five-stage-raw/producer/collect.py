"""Seal terminal R originals once; no subject, Git, deletion, or ROOT mutation."""
from pathlib import Path
import datetime,hashlib,json,os,stat,tarfile,traceback

HERE=Path(__file__).resolve().parent
R='6df0264f75e84f03adb70746b6ac3db07a9910fc'
RAW=Path('/tmp/g337323R7')
TOOLS=Path('/tmp/geo323-final-r7-stage-tools-20261024')
V5=Path('/workspace/geo323-recorder-fidelity-v5-draft-20261024/tools-v5')
SOURCE=Path('/tmp/geo323-final-r7-source-20261024')
OUT=Path('/tmp/geo323-r7-full-package-20261024')
STAGES=['prepare','build','compare','perf','profile']
MAX_ARCHIVE=36*1024*1024
MAX_METADATA=4*1024*1024
NATIVE_TMP_RESERVE=128*1024*1024
MIN_FREE=NATIVE_TMP_RESERVE+MAX_ARCHIVE+MAX_METADATA
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def need(value,message):
    if not value:raise RuntimeError(message)
def row(name,path):
    st=path.lstat();need(stat.S_ISREG(st.st_mode),'regular original required '+str(path))
    return {'name':name,'source_path':str(path),'bytes':st.st_size,'sha256':digest(path),'mode':st.st_mode,'mtime_ns':st.st_mtime_ns}
class BoundedArchive:
    def __init__(self,stream):self.stream=stream
    def write(self,data):
        need(self.stream.tell()+len(data)<=MAX_ARCHIVE,'single archive resource budget exceeded; preserve partial file, no automatic retry')
        return self.stream.write(data)
    def flush(self):return self.stream.flush()
    def tell(self):return self.stream.tell()
def collect():
    need(digest(HERE/'PLAN.json')=='27c968a7bd35fb7e63048e77c7a2093f977193966abf1e85dc30adb8a332402c','frozen membership plan')
    plan=json.loads((HERE/'PLAN.json').read_bytes())
    need(plan['source_sha']==R,'fixed R plan')
    for name,pin in plan['terminal_bindings'].items():
        original=Path(pin['path']);need(original.stat().st_size==pin['bytes'] and digest(original)==pin['sha256'],'frozen original terminal binding '+name)
    free=os.statvfs(OUT.parent).f_bavail*os.statvfs(OUT.parent).f_frsize
    need(free>=MIN_FREE,'TMP resource guard: reserve128MiB plus archive36MiB and metadata4MiB')
    need(not OUT.exists(),'single fresh package; never overwrite original or retry automatically')
    r=json.loads((RAW/'receipt.json').read_bytes())
    outer=json.loads((TOOLS/'launch-five/RESULT.json').read_bytes())
    driver=json.loads((TOOLS/'outer-five/RESULT.json').read_bytes())
    annotation=json.loads((HERE/'TOOL_RESPONSE_SCOPE.json').read_bytes())
    request=json.loads((TOOLS/'REQUEST.json').read_bytes())
    prep=json.loads((TOOLS/'preparation/RESULT.json').read_bytes())
    need(r['source_sha']==outer['source_sha']==request['source_sha']==prep['source_sha']==R,'original source bindings')
    need(outer['stages']==STAGES and len(outer['commands'])==5,'five original stage commands')
    need(driver['source_sha']==R and type(outer['exit']) is int and driver['exit']==outer['exit']==plan['expected_terminal']['outer_exit'],'frozen actual outer Recorder and launcher terminal retained')
    need(annotation['stdout_stderr_reconstructed'] is False and annotation['source_sha']==R and annotation['supplied_api_files'],'actual owner-supplied API objects retained without reconstruction or completeness inference')
    need(len(driver['commands'])==2 and [x['actual_exit']for x in driver['commands']]==[0,outer['exit']],'original df and five-stage outer exits')
    for i,c in enumerate(driver['commands'],1):
        directory=TOOLS/'outer-five/commands'/f'{i:03d}'
        need(c==json.loads((directory/'result.json').read_bytes()),'original outer atomic row')
        for stream in ['stdout','stderr']:need(digest(directory/stream)==c[stream+'_sha256'],'complete actual outer '+stream)
    need(driver['commands'][1]['command'][2:]==[str(TOOLS/'launch_stages.py'),'--sha',R,'--stage','five'],'actual original outer launch argv')
    for phase,c in zip(STAGES,outer['commands']):
        original=r['stages'][phase]
        need(original['ended_utc'] and original['source_before']==original['source_after']=={'head':R,'status':''},'closed historical R source '+phase)
        need(c==json.loads((TOOLS/'launch-five'/phase/'result.json').read_bytes()),'original outer row '+phase)
        need(c['stage']==phase and c['original_stage']==original,'outer/stage record identity '+phase)
        for stream in ['stdout','stderr']:
            need(digest(TOOLS/'launch-five'/phase/stream)==c[stream+'_sha256'],'outer full stream '+phase+'/'+stream)
    need([c['actual_process_exit'] for c in outer['commands']]==plan['expected_terminal']['cumulative_cli_exits'],'frozen original cumulative CLI exits')
    need([r['stages'][n]['execution_exit'] for n in STAGES]==plan['expected_terminal']['own_stage_exits'],'frozen original own-stage exits')
    need(r['full_acceptance_passed'] is None and r['all_required_stages_completed'] is False,'unrun stages not passed')
    need(('ABC_result' in r)==plan['expected_terminal']['ABC_result_present'],'original downstream audit presence stays unchanged')
    need(r['quantitative_targets']==plan['expected_terminal']['quantitative_targets'],'all original target values and verdicts retained, never inferred from R6')
    for name,pin in r['tool_hashes'].items():need(digest(V5/name)==pin,'frozen v5 tool '+name)
    need(prep['exit']==0 and len(prep['entries'])==447,'original thin source preparation')
    for entry in prep['entries']:
        p=SOURCE/entry['path'];need(p.stat().st_size==entry['bytes'] and digest(p)==entry['sha256'],'fixed private R source '+entry['path'])
    # Verify each v5 atomic row and raw stdin/stdout/stderr before sealing.
    commands=[]
    for file in sorted(RAW.rglob('commands.json')):
        records=json.loads(file.read_bytes());need(isinstance(records,list),'v5 original row list')
        for c in records:
            directory=Path(c['directory']);need(directory.is_relative_to(RAW),'original capture stays in R OUT')
            need(c==json.loads((directory/'result.json').read_bytes()),'v5 original result identity')
            need(type(c['actual_process_returncode']) is int,'actual process is terminal')
            for stream in ['stdout','stderr']:
                p=directory/(stream+'.bin');need(p.stat().st_size==c[stream+'_bytes'] and digest(p)==c[stream+'_sha256'],'complete atomic '+stream)
            p=directory/'stdin.bin'
            if p.exists():need(digest(p)==c['stdin_sha256'],'original stdin hash')
            else:need(c['stdin_provided'] is False and c['stdin_sha256']==sha_bytes(b''),'absent original stdin explicit')
            need((directory/'request.json').is_file(),'original request retained')
            commands.append({'index':str(file),'directory':str(directory),'exit':c['actual_process_returncode'],'timeout':c['timeout_expired'],'source_sha':c['source_sha'],'acceptance_sha':c['acceptance_sha']})
    # Membership was enumerated before the collector ran; no recursive self-copy.
    rows=[];excluded=[]
    for item in plan['original_files']:
        path=Path(item['path']);need(path.stat().st_size==item['bytes'],'planned original size '+str(path))
        z=row(item['name'],path)
        with path.open('rb') as f:is_elf=f.read(4)==b'\x7fELF'
        need(is_elf==(item['kind']=='ELF-hash-only'),'original payload kind '+str(path))
        if is_elf:
            z['reason']='Only ELF body excluded; original path retained unchanged.';excluded.append(z)
        else:rows.append(z)
    need(len(excluded)==7,'exact seven original ELF paths')
    for name in ['collect.py','PLAN.json','launch.py','README.md','freeze_terminal_plan.py','prepare_plan.py','R6_TO_R7_COLLECTOR.diff','PROVENANCE.json','TOOL_RESPONSE_SCOPE.json','adapt_r6.py','COLLECTOR_PINS.json']:
        rows.append(row('collection-tools/'+name,HERE/name))
    OUT.mkdir()
    summary={k:r[k] for k in ['source_sha','base','main','stages','errors','quantitative_targets','wrapper_exit','all_executed_stage_commands_passed','all_measured_original_targets_met','all_required_stages_completed','full_acceptance_passed']}
    summary.update(outer_tool_transcript_sequence_completeness='not independently inferred',outer_tool_transcript_annotation=annotation,outer_original_recorder=driver,formal_stage_scope=STAGES,outer_exit=outer['exit'],original_cli_exits=[c['actual_process_exit'] for c in outer['commands']],original_capture_rows=commands,source_preparation_entries=447,excluded_elf_count=7,free_bytes_before=free,free_space_filesystem=str(OUT.parent),native_tmp_reserve_bytes=NATIVE_TMP_RESERVE,resource_min_free_bytes=MIN_FREE,archive_limit_bytes=MAX_ARCHIVE,no_existing_file_deleted=True,no_subject_executed=True,published=False,limitations=['Package success verifies evidence byte preservation, never product acceptance.','Every current original target and exit is copied from frozen terminal receipts; no R6 verdict is imposed and no product acceptance is inferred.','Only five of the original eight stages ran here; full_acceptance_passed remains null.','Original source-role heuristic may label orchestration base from argv; no original field is rewritten.','ELF payloads remain at all original paths with exact hashes, not included or deleted.','Original emitted data only; missing audit fields or hidden outputs are not invented.','Exactly the supplied root-owned API response files are preserved bytewise. Full API sequence completeness is not inferred. Original outer Recorder and stage streams retain their actual exits and full bytes.'])
    save(OUT/'SUMMARY.json',summary);save(OUT/'EXCLUDED_ELF_PAYLOADS.json',excluded)
    for name in ['SUMMARY.json','EXCLUDED_ELF_PAYLOADS.json']:rows.append(row('collection/'+name,OUT/name))
    need(len({z['name'] for z in rows})==len(rows),'unique archive members')
    inventory={'source_sha':R,'members':rows,'regular_file_count':len(rows),'logical_original_bytes':sum(z['bytes'] for z in rows),'excluded_elf_manifest':'collection/EXCLUDED_ELF_PAYLOADS.json'}
    save(OUT/'RAW_INVENTORY.json',inventory)
    metadata_bytes=sum(f.stat().st_size for f in OUT.iterdir())
    need(metadata_bytes+65536<=MAX_METADATA,'metadata resource budget (64KiB reserved for final PACKAGE.json)')
    archive=OUT/'ORIGINAL_R7_FIVE_STAGE_RAW.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=BoundedArchive(raw),mode='w:gz',compresslevel=6,dereference=True) as tar:
            for z in rows:tar.add(z['source_path'],arcname=z['name'],recursive=False)
            tar.add(OUT/'RAW_INVENTORY.json',arcname='RAW_INVENTORY.json',recursive=False)
    expected={z['name']:z for z in rows};seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            need(member.isfile() and member.name not in seen,'unique regular archive member');seen.add(member.name)
            h=hashlib.sha256();count=0
            with tar.extractfile(member) as f:
                for part in iter(lambda:f.read(1024*1024),b''):count+=len(part);h.update(part)
            if member.name=='RAW_INVENTORY.json':need(count==(OUT/'RAW_INVENTORY.json').stat().st_size and h.hexdigest()==digest(OUT/'RAW_INVENTORY.json'),'raw index roundtrip')
            else:
                z=expected[member.name];need(count==z['bytes'] and h.hexdigest()==z['sha256']==digest(Path(z['source_path'])),'original full byte roundtrip '+member.name)
    need(seen==set(expected)|{'RAW_INVENTORY.json'},'complete selected originals coverage')
    for z in excluded:need(digest(Path(z['source_path']))==z['sha256'],'excluded ELF remains unchanged')
    result={'source_sha':R,'archive':{'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest(archive),'members':len(seen)},'inventory':{'path':str(OUT/'RAW_INVENTORY.json'),'sha256':digest(OUT/'RAW_INVENTORY.json')},'all_original_selected_bytes_roundtrip':True,'elf_payloads_included':False,'original_ELF_retained':True,'subject_executions':0,'published':False,'exit':0}
    need(os.statvfs(OUT.parent).f_bavail*os.statvfs(OUT.parent).f_frsize>=NATIVE_TMP_RESERVE,'native TMP reserve remains after archive')
    save(OUT/'PACKAGE.json',result);return result
if __name__=='__main__':
    try:result=collect()
    except BaseException:result={'exit':1,'error':traceback.format_exc(),'subject_executions':0,'originals_deleted':False}
    save(HERE/'COLLECTOR_RESULT.json',result);print(json.dumps(result,ensure_ascii=False));raise SystemExit(result['exit'])
