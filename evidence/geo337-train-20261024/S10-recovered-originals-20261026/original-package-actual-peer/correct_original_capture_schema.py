from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent;B=Path('/dev/shm/geometry-axiom-geo337-20261025');H=lambda b:hashlib.sha256(b).hexdigest();count=0
def ck(ok,msg):
 global count
 count+=1
 if not ok:raise AssertionError(msg)
p=O/'REVIEW.initial-request-schema.json';raw=p.read_bytes();ck(H(raw)=='38575a6b37ec5f0be95f6d0ff92042df2da69bfbe5408f3b84068b202663ea58','preserved first full package pass except schema')
j=json.loads(raw);ck(j['exit_code']==1 and j['blocking_findings']==['original full request/env retained']*2 and j['checks']==10082,'only exact two reader schema findings')
for label in ['verify','collection']:
 d=B/('S10-full123-terminal-'+label+'-root-original-20261025');catalog=(d/'subcommands.json').read_bytes();ck(H(catalog)==j['collector_launch_bindings'][str(d/'subcommands.json')],'original catalog unchanged')
 rows=json.loads(catalog);ck(len(rows)==1,'one original capture');r=rows[0];q=json.loads((Path(r['directory'])/'request.json').read_bytes())
 ck({k:(v,r.get(k)) for k,v in q.items() if r.get(k)!=v}=={'actual_process_returncode':(None,0)},'only original pending-exit evolves None to0')
 ck(q['timeout_expired'] is False and r['timeout_expired'] is False,'timeout remains false')
 ck(all(r[k]==v for k,v in q.items() if k not in ('actual_process_returncode','timeout_expired')),'all argv/env/time/start/stdin exact')
j['exit_code']=0;j['blocking_findings']=[];j['checks']=j['checks']-2+count
j['reviewer_schema_correction']={'initial_review':str(p),'initial_review_sha256':H(raw),'initial_exit_code':1,'initial_full_checks':10082,'initial_full_passed_checks':10080,'correction_checks':count,'cause':'原c387 request是啟動時actual_process_returncode=None；result是終態0。初reader不該要求此一演化欄相同。所有其他request/argv/env/stdin/timeout保持精確相等。','full_archive_rehashed_again':False,'subject_raw_modified':False,'corrected_reproducible_script_sha256':H((O/'audit.py').read_bytes())}
j['reviewed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dest=O/'REVIEW.json';dest.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':j['checks'],'correction_checks':count,'review_sha256':H(dest.read_bytes()),'index_sha256':j['index_sha256'],'ledger_sha256':j['ledger_sha256']}))
