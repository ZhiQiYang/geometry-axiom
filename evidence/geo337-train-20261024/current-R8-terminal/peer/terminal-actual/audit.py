from pathlib import Path
import hashlib,json,statistics,re
O=Path('/tmp/geo337-r8-terminal-actual-peer-20261025');O.mkdir(exist_ok=True);B=Path('/tmp/g337323R8');T=Path('/tmp/geo323-final-r8-stage-tools-20261024');R='75a1e93811a52b69385cbdaf6a09d773ed9052ad';E='815cd2e348e47e1666371aff5060820ff29a913a';checks=0;findings=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
def streams(row,d,exitkey='actual_process_returncode'):
 ck(j(d/'result.json')==row,'atomic result matches ledger '+str(d))
 for stream in ['stdin','stdout','stderr']:
  path=d/(stream+'.bin')
  if stream=='stdin' and not path.exists():
   ck(row.get('stdin_provided') is False and row['stdin_sha256']==sha(b''),'original inherited stdin explicitly not captured '+str(d));continue
  raw=path.read_bytes();ck(sha(raw)==row[stream+'_sha256'],'full small stream hash '+str(d)+'/'+stream)
  if stream!='stdin' and stream+'_bytes' in row:ck(len(raw)==row[stream+'_bytes'],'full small stream bytes '+str(d)+'/'+stream)
 return (d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes()
q=Path('/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json');s=j(q);ck(h(q)=='23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd','fixed R8 small projection')
original={}
for key,pin in s['original_file_bindings'].items():
 p=Path(pin['path']);ck(p.stat().st_size==pin['bytes'] and h(p)==pin['sha256'],'original binding '+key);original[key]=j(p)
r=original['receipt'];perf=original['performance'];eq=original['equivalence'];prof=original['profile_counts'];launch=original['launcher'];outer=original['outer']
ck(s['original_receipt']==r and s['original_performance_samples_and_medians']==perf and s['original_profile_counts']==prof,'whole receipt/performance/profile projected without edits')
ck(s['equivalence']=={'scenes':eq['scenes'],'failures':eq['failures'],'full_runs_file':s['original_file_bindings']['equivalence']},'equivalence exact projection linked to whole original')
ck(r['source_sha']==launch['source_sha']==outer['source_sha']==s['source_sha']==R,'one execution sourceR')
stages=['prepare','build','compare','perf','profile'];ck(list(r['stages'])==stages and [r['stages'][k]['execution_exit'] for k in stages]==[0,0,1,0,0],'true stage execution0/0/1/0/0')
ck([x['actual_process_exit'] for x in launch['commands']]==[0,0,1,1,1] and launch['exit']==outer['exit']==s['original_outer_exit']==1,'cumulative CLI and outer original1 preserved')
ck(r['all_required_stages_completed'] is False and r['full_acceptance_passed'] is None and 'ABC_result' not in r,'not full acceptance; ABC result absent')
for row in launch['commands']:
 stage=row['stage'];d=T/'launch-five'/stage;ck(j(d/'result.json')==row and row['original_stage']==r['stages'][stage],'original launcher per-stage terminal '+stage)
 for stream in ['stdout','stderr']:ck(h(d/stream)==row[stream+'_sha256'],'original whole CLI stream '+stage+'/'+stream)
 ck(row['source_sha']==R and row['command'][row['command'].index('--sha')+1]==R and row['command'][-2:]==['--stage',stage],'original one source and CLI stage '+stage)
 ck(r['stages'][stage]['source_before']==r['stages'][stage]['source_after']=={'head':R,'status':''},'clean original before/after source '+stage)
for i,row in enumerate(outer['commands'],1):
 d=T/'outer-five'/'commands'/f'{i:03d}';ck(j(d/'result.json')==row,'outer atomic original row '+str(i))
 for stream in ['stdout','stderr']:ck(h(d/stream)==row[stream+'_sha256'],'outer full stream '+str(i)+'/'+stream)
ck([x['actual_exit'] for x in outer['commands']]==[0,1],'outer df0 and original five-stage CLI1')
inv=sorted(B.glob('invocations/*/commands/commands.json'));ck(len(inv)==5,'exact five invocation ledgers')
allrows=[j(p) for p in inv];pr=allrows[3];samples=pr[2:-2];ck(len(pr)==40 and len(samples)==len(perf['samples'])==36,'36 original actual measurement commands')
expected_order=[(n,round,ver) for n in [16,32,48,64] for round in [1,2,3] for ver in ['base','fix','main']]
ck([(x['n'],x['round'],x['version']) for x in perf['samples']]==expected_order,'exact original interleaving and sample count')
for sample,row in zip(perf['samples'],samples):
 d=Path(row['directory']);stdout,stderr=streams(row,d)
 ck(row['command']==[str(B/'work'/sample['version']/'bridge')] and (d/'stdin.bin').read_text()==sample['command'],'actual executable and stdin correspond sample')
 ck(row['acceptance_sha']==R and row['actual_process_returncode']==sample['exit']==0 and row['recording_complete'] and not row['timeout_expired'] and row['evidence_flush_deferred'],'original PIPE deferred complete sample0')
 ck(sha(stdout)==sample['stdout_sha256'] and not stderr and sample['seconds']>0,'sample actual output, exit and positive original timer')
for n in [16,32,48,64]:
 m=perf['medians'][str(n)]
 for ver in ['base','fix','main']:ck(statistics.median(x['seconds'] for x in perf['samples'] if x['n']==n and x['version']==ver)==m[ver],'median recompute '+str(n)+'/'+ver)
 ck(m['fix']/m['main']==m['fix/main'] and m['fix']/m['base']==m['fix/base'],'exact ratios '+str(n))
quant=r['quantitative_targets'];ck(quant['N64_fix_main']['actual']==perf['medians']['64']['fix/main']==1.2846970752586067 and quant['N64_fix_main']['target']=='<=1.3' and quant['N64_fix_main']['target_met'] is True,'original N64 quantitative target now green')
for n,want,met in [('16',0.9834192453688345,True),('32',0.9007932884873169,True),('48',0.7392862448969592,True)]:ck(quant['small_N_no_regression']['points'][n]['fix_base']==perf['medians'][n]['fix/base']==want and quant['small_N_no_regression']['points'][n]['target_met'] is met and (want<=1)==met,'original smallN/base target truth '+n)
gprofrows=[x for x in allrows[4] if x['command'][0]=='gprof'];ck(len(gprofrows)==4,'four original gprof calls')
for row in gprofrows:
 name=Path(row['cwd']).name;stdout,stderr=streams(row,Path(row['directory']));p=prof[name]
 ck(row['actual_process_returncode']==0 and row['timeout_seconds'] is None and row['acceptance_sha']==R and h(Path(row['directory'])/'stdout.bin')==p['gprof_stdout_sha256'],'original gprof output/exit '+name)
 text=stdout.decode();ck(all(line in text for line in p['original_flat_matched_lines']),'full original flat lines retained '+name)
 for line in p['original_flat_matched_lines']:
  bits=line.split();ck(int(bits[3])==p['counts'][bits[-1]],'actual flat source calls '+name+'/'+bits[-1])
ratio=prof['fix-64']['counts']['geo_eval_source']/prof['fix-32']['counts']['geo_eval_source'];ck(ratio==quant['geo_eval_source_64_32']['actual']==4.407618425509266 and quant['geo_eval_source_64_32']['target']=='<=4.5' and quant['geo_eval_source_64_32']['target_met'],'source call ratio original green')
ck(eq['scenes']==175 and len(eq['runs'])==350 and all(x['exit']==x['trace_exit']==0 for x in eq['runs']),'original175 scenes350 base/fix run and trace exits0')
failed=[['_role_priority_mutant.scene','stdout'],['_s1_p8_l_room_primary_through_reflex_extension.scene','stdout'],['_s1_p8b_l_room_primary_through_reflex_extension_hi.scene','stdout']];ck(eq['failures']==failed,'same three exact stdout failures')
ck('assert not failures,failures' in r['stages']['compare']['errors'][0] and 'AssertionError:' in r['stages']['compare']['errors'][0],'normal original compare assertion exact cause')
CI=Path('/tmp/geo337-F8-E815-current-required-ci-20261025');ci=j(CI/'SUMMARY.json');cir=j(CI/'subcommands.json');ck(len(cir)==18,'18 original read-only CI commands')
ciout=[]
for row in cir:
 stdout,stderr=streams(row,Path(row['directory']));ck(row['actual_process_returncode']==0 and not stderr and not row['timeout_expired'],'original CI API0');ciout.append(json.loads(stdout))
ck(ci['product_source']==R and ci['evidence_head']==E and [(x['run_id'],x['head_sha']) for x in ci['runs']]==[(40170221039,R),(40170692505,E)],'current CI two exact SHA runs')
for idx,run in enumerate(ci['runs']):
 offset=idx*9;rawrun=next(x for x in ciout[offset]['workflow_runs'] if x['id']==run['run_id']);ck(rawrun['head_sha']==run['head_sha'] and rawrun['status']=='completed' and rawrun['conclusion']=='failure','original current run failure')
 jobs=ciout[offset+1]['jobs'];ck(len(jobs)==len(run['jobs'])==7 and run['required_jobs_green'] is False,'each current run seven notgreen jobs')
 for raw,small,annotations in zip(jobs,run['jobs'],ciout[offset+2:offset+9]):
  ck(raw['id']==small['id'] and raw['name']==small['name'] and raw['conclusion']==small['conclusion']=='failure' and raw['runner_id']==small['runner_id']==0 and not raw['runner_name'] and raw['steps']==[] and small['steps_count']==0,'original job not started '+str(raw['id']))
  ck([{'message':x['message'],'level':x['annotation_level']} for x in annotations]==small['annotations'],'exact original annotations '+str(raw['id']))
  ck(any(x['annotation_level']=='failure' and 'recent account payments have failed or your spending limit needs to be increased' in x['message'] for x in annotations),'explicit account-or-spending cause; no product failure inferred')
L=Path('/tmp/geo337-F8-ledger-freshness-20261025');lr=j(L/'RESULT.json');lrows=j(L/'subcommands.json');lout=[]
for row in lrows:
 stdout,stderr=streams(row,Path(row['directory']));lout.append(stdout.decode());ck(not stderr and not row['timeout_expired'],'ledger capture complete no stderr')
ck(len(lrows)==6 and [x['actual_process_returncode'] for x in lrows]==[0,0,0,1,0,0],'original ledger check1 and five source metadata0')
ck(lout[0].strip()==lout[4].strip()=='75a1e93811a52b69385cbdaf6a09d773ed9052ad' and lout[1]==lout[2]==lout[5]=='','physical F8 clean unchanged beforeafter and exact non-evidence productF')
ck(lrows[3]['command']==lr['command']==['python3','tests/mutate.py','--check'] and lr['exit']==1 and lr['product_source']==R and lr['execution_head']=='75a1e93811a52b69385cbdaf6a09d773ed9052ad' and not lr['ledger_regenerated'],'true freshness1 not regeneration')
ck('變異表 123 筆,紀錄 123 筆' in lout[3] and '無效 invalid 0 / 過期 stale 120 / 受阻 blocked 0 / 退役 retired 3' in lout[3] and len(re.findall(r'^  STALE M',lout[3],re.M))==120,'123 inventory120stale3retired noinvalid')
poll=T/'EXEC_TOOL_POLL_03.json'; pollj=j(poll); ck(pollj['exit_code']==1 and pollj['chunk_id']=='2aff4e' and json.loads(pollj['output'])=={'source_sha':R,'exit':1,'original_commands':2},'true final API process observation original exit1');

# Recompute pair differences from the actual complete compare streams and ordered graph artifacts.
import gzip
compare_rows=allrows[2]
ck(len(compare_rows)==704,'350 real +350 instrumented compare commands and four source guards')
actual_failures=[];pairs={}
for i,item in enumerate(eq['runs']):
 normal,trace=compare_rows[2+i*2:4+i*2]
 rawout,rawerr=streams(normal,Path(normal['directory']));trout,trerr=streams(trace,Path(trace['directory']))
 ck(normal['actual_process_returncode']==trace['actual_process_returncode']==item['exit']==item['trace_exit']==0,'true ordinary/trace process exits '+str(i))
 ck(normal['acceptance_sha']==trace['acceptance_sha']==R and normal['timeout_seconds']==trace['timeout_seconds']==600,'fixedSHA and original600s compare timeout '+str(i))
 ck(normal['command']==[str(B/'work'/item['version']/'bridge')] and trace['command']==[str(B/'work'/(item['version']+'-trace')/'bridge')],'exact ordinary/trace executable '+str(i))
 ck((Path(normal['directory'])/'stdin.bin').read_text()==(Path(trace['directory'])/'stdin.bin').read_text()==item['command'],'exact original loadfile dump command '+str(i))
 ck(rawout==trout and rawerr==trerr and len(rawout)==item['stdout_bytes'] and sha(rawout)==item['stdout_sha256'] and len(rawerr)==item['stderr_bytes'],'instrumented stdout/stderr equivalence '+str(i))
 for stream,raw in [('stdout',rawout),('stderr',rawerr)]:ck((B/'evidence'/'stdout'/item['version']/(item['scene']+'.'+stream)).read_bytes()==raw,'original copied full stream '+str(i)+stream)
 graph=gzip.decompress((B/'evidence'/'graphs'/item['version']/(item['scene']+'.bin.gz')).read_bytes())
 ck(len(graph)==item['graph_bytes'] and sha(graph)==item['graph_sha256'],'complete ordered graph bytes '+str(i))
 ck(normal['recording_complete'] and trace['recording_complete'] and not normal['timeout_expired'] and not trace['timeout_expired'],'complete compare recorder '+str(i))
 pairs.setdefault(item['scene'],{})[item['version']]=(rawout,graph,list(item['guards'].values()))
for scene,pair in pairs.items():
 ck(set(pair)=={'base','fix'},'exact pair '+scene)
 for i,label in enumerate(['stdout','source graph (possible cross-consumer dependency loss)','guard traffic']):
  if pair['base'][i]!=pair['fix'][i]:actual_failures.append([scene,label])
ck(actual_failures==eq['failures'],'independent350 raw/stdout/graph pairs reproduce exactly same three original mismatches')
ck(r['all_measured_original_targets_met'] is True and r['all_executed_stage_commands_passed'] is False and r['wrapper_exit']==1,'all performance targets green does not rewrite exact/outer1')
for name,pin in r['tool_hashes'].items():ck(h(B/'tools-frozen'/name)==pin,'original frozen judge tool '+name)
for name in ['EXEC_TOOL_INITIAL.json','EXEC_TOOL_POLL_01.json','EXEC_TOOL_POLL_02.json']:
 api=j(T/name);ck(api.get('session_id')==62076 and api.get('exit_code') is None,'real ongoing API observation '+name)

result={'schema':'R8-terminal-projection-current-CI-ledger-actual-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'summary_sha256':h(q),'source_sha':R,'evidence_head_at_checks':E,'original_file_bindings':s['original_file_bindings'],'CI_summary_sha256':h(CI/'SUMMARY.json'),'original_API_poll_sha256':h(poll),'ledger_result_sha256':h(L/'RESULT.json'),'stage_execution_exits':[0,0,1,0,0],'cumulative_CLI_exits':[0,0,1,1,1],'outer_exit':1,'sample_count':36,'N64_fix_main':perf['medians']['64']['fix/main'],'small_N_fix_base':{n:perf['medians'][n]['fix/base'] for n in ['16','32','48']},'source_call_ratio':ratio,'compare_failures':failed,'CI_runs':[40170221039,40170692505],'CI_read_commands':18,'ledger_execution_head':lr['execution_head'],'ledger_check_exit':1,'ledger_stale':120,'ledger_retired':3,'limits':['Inspected terminal projection, all36 timing sample raw, four gprof flat outputs, all350 ordinary and350 trace commands/streams,350 decompressed graph artifacts, fiveCLI/twoouter plus currentCI/check original streams. Guard counts verified as original equivalence report and pair equality; per-scene original guard file payload was not independently retained in recorder stream rows. Full package roundtrip, all build/preparation raw and later audit remain separate.','No C, perf sampling, network, source changes or threshold changes. Per-sample original perf timer preserved; recorder wall seconds not substituted.','Original source_role heuristic labels retained; acceptance SHA, stage source guards and actual executable paths bind attribution.','Current CI failed before runner/steps owing explicit account payment OR spending limit; no waiver or product pass inferred.','Ledger check red is freshness120stale/3retired, not invalid mutants or a regenerated ledger. All remaining currentR full gates stay UNRUN.']}
p=O/'REVIEW.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':checks,'exit_code':result['exit_code'],'findings':findings}));raise SystemExit(result['exit_code'])
