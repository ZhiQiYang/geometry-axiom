"""Copy small original terminal facts; never rerun or reinterpret acceptance."""
from pathlib import Path
import hashlib,json,statistics
ROOT=Path('/tmp/g337323R7');TOOLS=Path('/tmp/geo323-final-r7-stage-tools-20261024');OUT=Path('/tmp/geo323-r7-terminal-summary-20261024');S='6df0264f75e84f03adb70746b6ac3db07a9910fc'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def need(v,m):
 if not v:raise RuntimeError(m)
need(not OUT.exists(),'fresh terminal-summary output');receipt=read(ROOT/'receipt.json');perf=read(ROOT/'evidence/performance.json');eq=read(ROOT/'evidence/equivalence.json');profile=read(ROOT/'evidence/profile-counts.json');launcher=read(TOOLS/'launch-five/RESULT.json');outer=read(TOOLS/'outer-five/RESULT.json')
need(receipt['source_sha']==launcher['source_sha']==outer['source_sha']==S,'one actual R')
need(type(launcher['exit']) is int and launcher['exit']==outer['exit'] and len(outer['commands'])==2 and all(type(c['actual_exit']) is int for c in outer['commands']),'actual closed launcher/outer terminal preserved')
need(len(perf['samples'])==36 and eq['scenes']==175,'complete original samples/scenes')
need(list(receipt['stages'])==['prepare','build','compare','perf','profile'],'all five stages present')
need(all(type(v['execution_exit']) is int and v['ended_utc'] for v in receipt['stages'].values()),'all original own-stage exits terminal; no R6 verdict imposed')
need([r['stage'] for r in launcher['commands']]==list(receipt['stages']) and all(type(r['actual_process_exit']) is int for r in launcher['commands']),'original five cumulative CLI exits copied without R6 assumption')
need(all(v['source_before']==v['source_after']=={'head':S,'status':''}for v in receipt['stages'].values()),'all clean actual source states')
for n in [16,32,48,64]:
 for version in ['base','fix','main']:
  samples=[r for r in perf['samples']if r['n']==n and r['version']==version]
  need(len(samples)==3 and all(r['exit']==0 for r in samples),'three original successful samples')
  need(statistics.median(r['seconds']for r in samples)==perf['medians'][str(n)][version],'original median recomputation')
originals={}
for name,path in [('receipt',ROOT/'receipt.json'),('performance',ROOT/'evidence/performance.json'),('equivalence',ROOT/'evidence/equivalence.json'),('profile_counts',ROOT/'evidence/profile-counts.json'),('launcher',TOOLS/'launch-five/RESULT.json'),('outer',TOOLS/'outer-five/RESULT.json')]:originals[name]={'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}
summary={'source_sha':S,'base':receipt['base'],'main':receipt['main'],'record_type':'Small original-terminal projection; full original command records remain at listed paths','original_file_bindings':originals,'original_receipt':receipt,'original_performance_samples_and_medians':perf,'original_profile_counts':profile,'equivalence':{'scenes':eq['scenes'],'failures':eq['failures'],'full_runs_file':originals['equivalence']},'original_launcher_terminal':{'exit':launcher['exit'],'stages':[{'stage':r['stage'],'actual_process_exit':r['actual_process_exit']}for r in launcher['commands']]},'original_outer_exit':outer['exit'],'normal_locks_released_by_launcher_finally':True,'original_status_not_reinterpreted':{'errors':receipt['errors'],'quantitative_targets':receipt['quantitative_targets'],'own_stage_exits':[receipt['stages'][k]['execution_exit'] for k in receipt['stages']],'cumulative_cli_exits':[r['actual_process_exit'] for r in launcher['commands']],'equivalence_failures':eq['failures']},'limits':['This small projection is not the full archive; original command stdin/stdout/stderr/environment/graphs and compiler artifacts remain in g337323R7 and stage-tools.','v5 PIPE/defer-flush contract is newly fixed; the previous U v4 run remains historical and is not rewritten or resampled.','gprof -O1/-pg function self times are diagnostic, not evidence of O2 wall improvement.','No completed-project or READY-TO-MERGE claim; final native/browser/ledger and other gates remain separately tracked; architecture execution Me321 with adopted outputs at F7 is separately recorded.', 'Original run.py has eight stages; this receipt contains the first five only. required-eight/pf3/native remain unrun at F7 in this driver. Original audit presence and all acceptance fields are retained from receipt without inferring any missing verdict.']}
OUT.mkdir(exist_ok=False);(OUT/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'summary':str(OUT/'SUMMARY.json'),'bytes':(OUT/'SUMMARY.json').stat().st_size,'sha256':sha((OUT/'SUMMARY.json').read_bytes()),'assessment_exit':0}))
