from pathlib import Path
import argparse,json
import memo_variant as m
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['fixed','whole-file-H'],required=True);a=p.parse_args();D=Path(__file__).parent/'metadata';rows=[]
for path in m.PINS:
 name=path.replace('/','__');fixed=(D/('F8-'+name)).read_bytes();withdrawn=m.withdraw_memo(path,fixed)if a.mode=='fixed'else(D/('H-'+name)).read_bytes()
 if path=='geometry-core/references.inc':
  print(json.dumps({'mode':a.mode,'path':path,'local_init_retained':withdrawn.count(m.LOCAL_INIT)==1,'metadata_only':True}),flush=True)
  assert withdrawn.count(m.LOCAL_INIT)==1,'ASSERT:memo-counterfactual-retains-H-local-init'
 restored=m.restore_memo(path,withdrawn);assert restored==fixed,'ASSERT:memo-restoration-is-exact-F8'
 rows.append({'path':path,'fixed':m.digest(fixed),'withdrawn':m.digest(withdrawn),'restored':m.digest(restored)})
print(json.dumps({'metadata_only':True,'formal_executed':False,'rows':rows,'exit':0}),flush=True)
