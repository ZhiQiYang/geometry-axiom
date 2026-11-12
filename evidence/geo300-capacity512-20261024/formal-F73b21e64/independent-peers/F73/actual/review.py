from pathlib import Path
import hashlib,json,re
O=Path(__file__).resolve().parent
F='73b21e64dce72f0d16ca29e18559c51815b9724d';leaf='tests/test_geo261_timber_capacity_host.py'
A=Path('/workspace/geo348-F73b21e64-formal');B=Path('/workspace/geo348-F73b21e64-sentinel-resume');checks=[]
def ck(x,m):checks.append({'check':m,'passed':bool(x)})
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text())
a=load(A/'RESULT.json');b=load(B/'RESULT.json')
ck(sha((A/'RESULT.json').read_bytes())=='23119c194be860059362672980d984c805838f5227c83788c3d2522b7fbc29c0','original first batch exact receipt')
ck(sha((B/'RESULT.json').read_bytes())=='f61c80f1335c1c05e82d094c54f978717fe51fe1c6801f2dab52429acf8dd5c2','resume exact receipt')
ck(a['exit_code']==1 and not a['accepted'],'original environment-limited outer red retained')
ck(b['exit_code']==0 and b['accepted'],'environment-only last-three resume accepted')
ck(b['prior_partial_sha256']==sha((A/'RESULT.json').read_bytes())and not b['prior_ten_phases_rerun'],'resume binds first original receipt and no rerun first ten')
for r in [a,b]:
 ck(r['source_sha']==F and r['source_clean_after']and not r['errors'],'same F and source clean terminal')
 ck(not r['full_H7_executed']and not r['unfixed_512_methods_rerun']and not r['full_native']and not r['ledger_regenerated']and not r['performance'],'no full H7/native/ledger/performance claims')
ck(len(a['phases'])==13 and len(b['phases'])==3,'original planned 13/resumed3')
for p in a['phases'][10:]:ck(p['state']=='UNRUN_ENVIRONMENT'and p.get('actual_exit')is None and not p['passed'],'original environment-unrun preserved '+p['label'])
phases=a['phases'][:10]+b['phases'];ck(len(phases)==13,'exact completed logical phase count')
fixed=Path('/workspace/geo348-sentinel-fix-draft-20261024/candidate.py').read_bytes();ck(sha(fixed)=='abe3ab96bfbda4fd4a535558c0b95294c0bcdccabec7ba129ea2b13cdac8b740','accepted F73 host fixed bytes')
wr=Path('/workspace/geo300-capacity512-publication-20261024/host-v5-draft/EXACT_WITHDRAWALS.json').read_bytes();ck(sha(wr)=='48bf7a7cacc8f3de143a1903210b14ad43aa17d8bf69edcda71e6e94419613cc','three old exact withdrawal snippets pinned');w=json.loads(wr)
variants={}
for name,row in w.items():
 before=row['before'].encode();after=row['after'].encode();ck(fixed.count(after)==1,'withdrawal applied only exact original fixed helper '+name);variants[name]=sha(fixed.replace(after,before,1))
needle=b'SAFE_INCOMPLETE_DECLARATION="timber 513 27 33"'
if needle not in fixed:
 needle=b'SAFE_INCOMPLETE_DECLARATION = "timber 513 27 33"'
# Read actual constant spelling; no substring-wide test changes.
lines=[x for x in fixed.splitlines(keepends=True)if b'="timber 513 27 33"'in x or b'= "timber 513 27 33"'in x]
ck(len(lines)==1,'exact one fixed sentinel constant')
sentinel=lines[0];variants['sentinel_fix']=sha(fixed.replace(sentinel,sentinel.replace(b'"timber 513 27 33"',b'"timber"'),1))
markers={'count':'AssertionError: Lists differ:', 'population':'角材 1 沒有 place（收尾時仍未放置，I9）','unplaced_replay':'self.assertTrue(restored.command("loadfile "+str(replay))["ok"])','sentinel_fix':'host-capacity-first-incomplete-declaration'}
base_source=phases[0]['entry']['source_files_before'];details=[]
for p in phases:
 label=p['label'];entry=p['entry'];obs=p['observation'];negative=p['negative'];expected=1 if negative else 0;q=Path(p['command_directory']);cr=load(q/'result.json');stdout=(q/'stdout.bin').read_bytes();stderr=(q/'stderr.bin').read_bytes();count=p['original_expected_methods']
 ck(p['state']=='COMPLETED'and p['actual_exit']==expected and p['passed'],'actual phase return '+label)
 ck(cr['actual_process_returncode']==expected and not cr['timeout_expired']and cr['source_sha']==F,'raw original capture exit/source/no timeout '+label)
 ck(sha(stdout)==cr['stdout_sha256']and sha(stderr)==cr['stderr_sha256']and len(stdout)==cr['stdout_bytes']and len(stderr)==cr['stderr_bytes'],'raw exact stdout/stderr '+label)
 ck(cr['command']==p['argv']and p['original_argv'][2:] == p['argv'][p['argv'].index('--')+1:],'original selected unittest command '+label)
 ck(entry['original_completed']and entry['original_exit']==expected and entry['original_exception']=={'type':'SystemExit','repr':f'SystemExit({expected})'},'normal original unittest SystemExit '+label)
 ck(p['observation_complete']and obs['observer_complete']and not obs['incomplete_sessions']and not obs['observation_errors']and entry['observer_complete'],'complete observer metadata '+label)
 ck(entry['source_sha']==F and entry['postflight_head']['exit']==0 and bytes.fromhex(entry['postflight_head']['stdout_hex']).decode()==F+'\n' and entry['postflight_head']['stderr_hex']=='' and entry['source_files_before']==entry['source_files_after'],'exact stable phase source '+label)
 expected_source=dict(base_source);expected_source[leaf]=variants[negative]if negative else sha(fixed)
 ck(entry['source_files_before']==expected_source,'only exact permitted test-helper variant '+label)
 ck(p['source_exact_after']and entry['postflight_status']['exit']==0 and bytes.fromhex(entry['postflight_status']['stdout_hex']).decode()==(' M '+leaf+'\n'if negative else '') and entry['postflight_status']['stderr_hex']=='','source dirt only declared variant '+label)
 text=stderr.decode();ck(re.search(r'Ran '+str(count)+r' tests? in ',text)is not None and 'skipped='not in text,'original method count/no skip '+label)
 if negative:
  ck('FAILED (failures=1)'in text and 'AssertionError:'in text and markers[negative]in text and 'ERROR:'not in text,'specific normal assertion cause '+label)
 else:ck(text.rstrip().endswith('OK')and 'FAILED'not in text,'normal positive formal result '+label)
 details.append({'label':label,'actual_exit':expected,'methods':count,'stdout_bytes':len(stdout),'stderr_bytes':len(stderr),'cause':markers.get(negative),'source_host_sha256':entry['source_files_before'][leaf]})
for start in [1,4,7,10]:ck([p['actual_exit']for p in phases[start:start+3]]==[0,1,0],'normal adjacent original trio '+phases[start]['label'])
for root,exitcode in [(A,1),(B,0)]:
 top=root.with_name(root.name+'-launch');receipt=load(top/'receipt.json');completion=load(top/'EXEC_COMPLETION.json')
 ck(completion['exit_code']==exitcode,'real tool process exit '+root.name)
 ck(receipt['source']==F,'top launcher source '+root.name)
 scalars={k:v for k,v in receipt.items()if not isinstance(v,(list,dict))}
 (O/(root.name+'-outer-scalars.json')).write_text(json.dumps(scalars,ensure_ascii=False,indent=2)+'\n')
failed=[c for c in checks if not c['passed']]
(O/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
report={'exit':int(bool(failed)),'checks':len(checks),'passed':len(checks)-len(failed),'findings':failed,'source':F,'phases':details,'reviewer_correction':'Preserved initial helper/report mistakes: UNRUN_ENVIRONMENT omits actual_exit, and observer postflight values are exit/stdout_hex/stderr_hex records, not strings. Reader corrected to actual schema; subject and receipts unchanged.', 'scope':'Small actual terminal/command streams/source-version hashes and exact assertion causes review. No C rerun, Git writes, complete compiler/pipe/session-payload archive walk or large hashing during exclusive R5. Full underlying capture/compiled inputs package integrity remains separate pending review. Original first outer exit1 remains environment incomplete, resumed last3 outer0. Does not validate either deferred true placed512 method, full H7, native, ledger, architecture or performance.'}
(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['exit','checks','passed','findings']},ensure_ascii=False));raise SystemExit(report['exit'])
