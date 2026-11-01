from pathlib import Path
import json,statistics
from review_performance_package_common import Review,L
v=Review('p52','68af29e8b306afab056156f4b883a000c605e942de9f2c72486abdd7d917a641','v3');r=v.root;f=r/'formal'
producer=v.j(v.B.parent/'p52-v3-collection-launch/RESULT.json');v.capture(producer);v.ck(producer['actual_process_returncode']==0,'collector actual zero')
for label in ['p52-collection-launch','p52-v2-collection-launch']:
 q=v.j(v.B.parent/label/'RESULT.json');v.ck(q['actual_process_returncode']==1,'historical collector failure retained '+label)
v.ck(v.r['launcher_exit_code']==0 and v.r['passed'] is True,'original P52 passed')
formal=v.j(f/'execution-receipt.json');protocol=v.j(f/'receipt.json');verifier=v.j(r/'verifier/receipt.json')
v.ck(formal['sha']==protocol['sha']==verifier['sha']==L,'all exact L originals')
v.ck(formal['actual_driver_exit_code']==verifier['actual_driver_exit_code']==verifier['original_verifier_process_exit']==0 and formal['passed'] and verifier['passed'] and formal['original_body_completed'] and not formal['errors'] and not verifier['errors'],'formal original and verifier true zero')
v.ck(verifier['original_assertions_unchanged'] and verifier['original_verified_result']=={'sha':L,'command_exit_codes_match':True,'no_timeout_or_crash_counted':True,'drivers_match':True,'nodes':9,'pass':True},'original nine-command verifier pass')
v.ck('DERIVED' in verifier['projection_truthfulness'] and '不是原 launch stdout' in verifier['projection_truthfulness'],'derived projections explicitly labelled')
records=protocol['records'];samples={'main':[],'fix':[]};main='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
v.ck([x['label'] for x in records]==['0-main','1-fix','2-fix','3-main'],'exact main/fix/fix/main blocks')
for x in records:
 side='main' if x['sha']==main else 'fix';rr=x['result'];v.ck(x['sha']=={'main':main,'fix':L}[side] and x['mode']=='measure' and x['exit']==0 and rr['failed']==0 and rr['exceptions']==0,'measurement zero '+x['label'])
 v.ck(len(rr['samples'])==8 and [z['trial'] for z in rr['samples']]==list(range(8)),'eight actual trials '+x['label'])
 for z in rr['samples']:v.ck(isinstance(z['appearedMs'],(int,float)) and z['appearedMs']>=0 and z['lastRefs']['ok'] is True,'actual appearance sample '+x['label'])
 samples[side].extend(z['appearedMs'] for z in rr['samples'])
 local=f/x['label'];expected=local/('samples.json' if side=='main' else 'result.json');v.ck(v.j(expected)==rr,'original full result binds record '+x['label'])
timing=protocol['timing'];med={k:statistics.median(z) for k,z in samples.items()}
v.ck(timing['medians_ms']==med and timing['count']=={'main':16,'fix':16} and timing['ratio']==med['fix']/med['main'] and med['fix']<=med['main'] and timing['no_regression'] is True,'exact recomputed original fix<=main, no slack')
controls=protocol['controls'];v.ck([x['mode'] for x in controls]==['normal','delay','revert-delay','wrong','missing'],'five original controls')
title='P52-5 真實放置的 cross 足跡(核心) = 預示帶範圍 1987..2014';proofs=[]
for x in controls:
 mode=x['mode'];rr=x['result'];log=Path(x['log']).read_text();v.ck(v.j(f/x['label']/'result.json')==rr,'original control result '+mode)
 if mode in ['normal','delay']:good=x['exit']==0 and rr['passed']==5 and rr['failed']==0 and rr['exceptions']==0 and not rr.get('fatal')
 elif mode in ['revert-delay','wrong']:
  good=x['exit']==1 and rr['passed']==4 and rr['failed']==1 and rr['exceptions']==0 and not rr.get('fatal') and sum(line.startswith(title+' ✗') for line in log.splitlines())==1
  good=good and any(z.get('injected')==('place-before-send-900ms' if mode=='revert-delay' else 'A28') for z in rr['events'])
 else:good=x['exit']==1 and rr.get('fatal','').startswith('P52-5 ') and '上限 5000ms' in rr.get('fatal','') and any(z.get('injected')=='omit-place' for z in rr['events'])
 v.ck(good and x['expected_behavior_proved'] is True,'actual named original control failure '+mode);proofs.append({'mode':mode,'exit':x['exit'],'expected_behavior_proved':bool(good)})
nodes=formal['node_commands'];v.ck(len(nodes)==9 and [x['actual_process_returncode'] for x in nodes]==[0]*6+[1]*3 and all(x['timeout_expired'] is False for x in nodes),'nine actual OS Node exits no timeout')
for row in nodes:v.capture(row,f)
guards={x['label']:x for x in formal['guards']}
for side,sha in [('fix',L),('main',main)]:
 a=guards[side+'-before'];b=guards[side+'-after'];v.ck(a['head']==b['head']==sha and a['status']==b['status']=='' and a['diff_sha256']==b['diff_sha256']==v.sh(b'') and a['tree_index_sha256']==b['tree_index_sha256'],'original source guard '+side)
 ia=a['runtime_inputs'];ib=b['runtime_inputs'];v.ck(v.h(ia['path'])==ia['sha256']==v.h(ib['path'])==ib['sha256'] and ia['source_version']==ib['source_version'] and ia['source_set_complete'] and ib['source_set_complete'] and ia['expected_count']==ia['actual_count']==ib['expected_count']==ib['actual_count'],'historical input closure '+side)
annotations=v.j(v.B/'ORIGINAL_P52_CAPTURE_ANNOTATIONS.json');v.ck(len(annotations)==65==v.s['original_p52_post_capture_annotation_rows'],'65 exact appended annotations retained')
for a in annotations:
 v.ck(a['record_file']==str(f/'subcommands.json') and v.h(a['result_file'])==a['result_sha256'] and a['shared_original_OS_fields_exact'] is True and set(a['original_appended_annotations'])<={'effective_environment','legacy_probe_log'},'annotation binds original result '+a['result_file'])
extra={'product_passed':True,'formal_exit':0,'original_verifier_exit':0,'timing_medians_ms':med,'fix_main_ratio':med['fix']/med['main'],'samples_per_side':16,'controls':proofs,'actual_node_exits':[x['actual_process_returncode'] for x in nodes],'historical_collection_failures':[1,1],'post_capture_annotation_rows':65,'projection_note':'Verifier legacy projections are derived from original c387 rows/streams and labelled derived; original complete streams independently archived. Exact Chrome IPC symlinks/sockets are lstat/readlink metadata only, never dereferenced.'}
raise SystemExit(v.finish(extra))
