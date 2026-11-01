from pathlib import Path
import hashlib,json,statistics
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';B=Path('/workspace/g337323L');M=Path('/workspace/g337323memoL');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
f=j(B/'receipt.json');memo=j(M/'receipt.json');perf=j(B/'evidence/performance.json');profile=j(B/'evidence/profile-counts.json')
ck(f['source_sha']==memo['sha']==L and f['base']=='b74f9a2ae7ade1555b9be45283adecc097fb76e3' and f['main']=='adbaebf9c73ea6801d7b4d5214e4b846b132923b','original fixed source and denominators')
stages={'prepare':0,'build':0,'compare':1,'perf':0,'profile':0};ck(set(f['stages'])==set(stages),'only original five stages in formal OUT')
for name,code in stages.items():
 s=f['stages'][name];ck(s['execution_exit']==code and s['ended_utc'] and s['source_before']==s['source_after']=={'head':L,'status':''},'closed sameL exact stage '+name)
ck(f['wrapper_exit']==1 and f['full_acceptance_passed'] is None and f['all_required_stages_completed'] is False and f['all_executed_stage_commands_passed'] is False and f['all_measured_original_targets_met'] is False,'original cumulative and partial-driver verdict preserved')
samples=perf['samples'];wanted={(n,r,v) for n in [16,32,48,64] for r in [1,2,3] for v in ['base','fix','main']}
ck(len(samples)==36 and {(s['n'],s['round'],s['version']) for s in samples}==wanted and all(s['exit']==0 and s['seconds']>0 for s in samples),'36 complete unique original successful measured samples')
ck([(s['n'],s['round'],s['version']) for s in samples]==[(n,r,v) for n in [16,32,48,64] for r in [1,2,3] for v in ['base','fix','main']],'original base-fix-main interleaved order')
calc={}
for n in [16,32,48,64]:
 d={v:statistics.median(s['seconds'] for s in samples if s['n']==n and s['version']==v) for v in ['base','fix','main']};d.update({'fix/main':d['fix']/d['main'],'fix/base':d['fix']/d['base']});calc[str(n)]=d
ck(calc==perf['medians'],'actual original36 recompute exact medians')
q=f['quantitative_targets'];ck(q['N64_fix_main']['actual']==calc['64']['fix/main']==1.4282954375137715 and q['N64_fix_main']['target']=='<=1.3' and q['N64_fix_main']['target_met'] is False,'N64 true original red')
ck(q['small_N_no_regression']['points']=={n:{'fix_base':calc[n]['fix/base'],'target_met':calc[n]['fix/base']<=1} for n in ['16','32','48']} and all(calc[n]['fix/base']<=1 for n in ['16','32','48']),'smallN original denominator unchanged all pass')
for name,p in profile.items():
 path=B/'evidence'/('gprof-'+name+'.stdout');raw=path.read_text();lines=[x.split() for x in raw.split('Call graph')[0].splitlines() if len(x.split())==7 and x.split()[-1]=='geo_eval_source']
 ck(h(path)==p['gprof_stdout_sha256'] and len(lines)==1 and int(lines[0][3])==p['counts']['geo_eval_source'],'original gprof exact sourcecalls '+name)
ratio=profile['fix-64']['counts']['geo_eval_source']/profile['fix-32']['counts']['geo_eval_source'];ck(profile['fix-32']['counts']['geo_eval_source']==82668 and profile['fix-64']['counts']['geo_eval_source']==364369 and ratio==q['geo_eval_source_64_32']['actual']==4.407618425509266 and q['geo_eval_source_64_32']['target_met'] is True and q['geo_eval_source_64_32']['target']=='<=4.5','sourcecalls original integer ratio green')
ck(memo['formal_receipt_sha256']==h(B/'receipt.json') and memo['fixed_formal_criterion']==q['geo_eval_source_64_32'] and memo['source_before']==memo['source_after']=={'head':L,'status':''} and memo['ended_utc'] and memo['passed'] is True and memo['exit']==0 and not memo['errors'],'memo binds exact formal sourcecalls and sameL')
expected={'withdrawn':1,'restored':0,'abc':0};ck([x['phase'] for x in memo['phases']]==list(expected),'three original phases exact order')
for phase in memo['phases']:
 name=phase['phase'];r=j(phase['receipt']);ck(r==phase['result'] and r['execution_complete'] is True and r['exit']==r['criterion_exit']==phase['actual_exit']==expected[name] and not r['errors'] and r['source_before']==r['source_after']=={'head':L,'status':''},'true completed phase not infrastructure2 '+name)
 if name in ['withdrawn','restored']:
  for label,count in r['profile_counts'].items():
   p=M/name/'evidence'/('gprof-'+label+'.stdout');raw=p.read_text();lines=[x for x in raw.split('Call graph')[0].splitlines() if len(x.split())==7 and x.split()[-1]=='geo_eval_source'];ck(h(p)==count['gprof_sha256'] and len(lines)==1 and lines[0]==count['original_line'] and int(lines[0].split()[3])==count['calls'],'memo original sourcecall gprof '+name+'/'+label)
  ratio=r['profile_counts']['fix-64']['calls']/r['profile_counts']['fix-32']['calls'];ck(r['actual']==ratio and r['target']=='<=4.5' and r['target_met']==(ratio<=4.5),'memo quantitative criterion '+name)
  changed=[p for p in r['source_before_variant'] if r['source_before_variant'][p]!=r['source_after_variant'][p]];ck(sorted(changed)==sorted(r['changed_source_paths'])==(['geometry-app/native/reference_sources.inc','geometry-core/references.inc'] if name=='withdrawn' else []),'exact source closure variant '+name)
 else:ck(r['ABC_result']=={'scenes':175,'runs':350,'failures':[],'original_exit':0,'original_audit_tuple_equal':True} and r['variant_sources']==r['variant_sources_after_ABC'],'original isolatedABC complete175/350 and audit tuple0; source stable')
for gate,code in [('geo323-perf',1),('geo323-profile',1),('memo',0)]:
 p=Path('/workspace/train337-L-'+gate+'-original-launch-20261024');r=j(p/'RESULT.json');row=r['command'];d=Path(row['directory']);ck(r['source_sha']==row['source_sha']==row['acceptance_sha']==L and r['gate']==gate and r['actual_exit']==row['actual_process_returncode']==code and row['ended_epoch'] and not row['timeout_expired'],'actual outer distinct exit '+gate)
 ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'outer exact request/result '+gate)
 for stream in ['stdout','stderr']:
  x=d/(stream+'.bin');ck(x.stat().st_size==row[stream+'_bytes'] and h(x)==row[stream+'_sha256'],'outer complete original stream '+gate+'/'+stream)
r={'schema':'geo323-all-terminal-small-metadata-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'source_sha':L,'formal_receipt_sha256':h(B/'receipt.json'),'memo_receipt_sha256':h(M/'receipt.json'),'formal_stage_exits':stages,'outer_exits':{'geo323-perf':1,'geo323-profile':1,'memo':0},'N64_fix_main':calc['64']['fix/main'],'N64_target_met':False,'small_N_fix_base':{n:calc[n]['fix/base'] for n in ['16','32','48']},'source_calls_N32':82668,'source_calls_N64':364369,'source_calls_ratio':q['geo_eval_source_64_32']['actual'],'memo_phase_exits':expected,'memo_withdrawn_ratio':memo['phases'][0]['result']['actual'],'memo_restored_ratio':memo['phases'][1]['result']['actual'],'original_isolated_ABC':memo['phases'][2]['result']['ABC_result'],'limits':['Small original receipts, scalar timing records, gprof text and three original outer captures only. No current checkout/cache, large graph/archive payload, compiler or subject run.','ABC175/350 plus audit tuple is the original successful judge result; full paired graph/stream package independent byte review remains separate.','Original formal OUT has full_acceptance_passed=null and all_required_stages_completed=false because only five of its stages ran there. Separately recorded L gates do not rewrite those original fields.','N64 numerical red and cross-version compare red remain; memo criterion red/green uses original denominator and no infrastructure2 counted.']}
p=O/'GEO323_ALL_TERMINAL_METADATA_PEER.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
