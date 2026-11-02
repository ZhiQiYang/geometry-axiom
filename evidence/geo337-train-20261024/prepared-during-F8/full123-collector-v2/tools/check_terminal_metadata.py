"""Synthetic classification self-test only; never opens actual live outputs."""
import argparse,copy,json
from terminal_guard import F8,classify,parse_optional_terminal
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['fixed','withdrawn','restored'],required=True);a=p.parse_args()
names=['original-tracked-ledger-check','original-full123-passive-observer','original-core-stream-map','original-new-ledger-check']
source={'root':{'head':F8,'status':''},'seed':{'head':F8,'status':''}}
job={'sourceSHA':F8,'phases':[{'phase':name,'command':{'actual_process_returncode':exit}} for name,exit in zip(names,[1,0,0,0])],'exit_code':0,'passed':True,'original_cli_exit':0,'ledger_count':123,'execution_head_counts':{F8:120},'source_before':source,'source_after':source,'source_final':source}
outer={'actual_exit':0,'source_sha':F8};observer={'original_exit':0,'original_completed':True,'observer_complete':True,'source_tool_bytes_unchanged':True,'observation_errors':[],'source_sha':F8};mapping={'passed':True,'failures':[],'mappings':[{'synthetic_only':True}]};bridge={'errors':[],'files':[{'synthetic_only':True}]}
ledger={'SYNTHETIC%03d'%i:{'execution':{'head':F8},'verdict':'killed'} for i in range(120)};ledger.update({'RETIRED%d'%i:{'verdict':'retired'} for i in range(3)})
if a.phase=='withdrawn':ledger['SYNTHETIC000']['execution']['head']='0'*40
result=classify(job,outer,observer,mapping,bridge,ledger)
print(json.dumps({'synthetic_metadata_only':True,'formal_executed':False,'phase':a.phase,'classified_formal_accepted':result['formal_accepted'],'failed_conditions':result['failed_conditions']},ensure_ascii=False),flush=True)
assert result['formal_accepted'],'synthetic-natural-execution-head-must-remain-F8'
# Further pure negative vectors, without I/O or changing the original assertion.
for label,target,key,value in [('CLI',observer,'original_exit',1),('map',mapping,'passed',False),('bridge',bridge,'errors',['synthetic-error']),('root',job,'exit_code',1),('count',job,'ledger_count',122)]:
 old=copy.deepcopy(target[key]);target[key]=value;bad=classify(job,outer,observer,mapping,bridge,ledger);target[key]=old
 assert not bad['formal_accepted'],label+' rejection missing'
print(json.dumps({'synthetic_metadata_only':True,'negative_vectors':5,'passed':True,'formal_executed':False}))

# Corrupted optional child raw remains collectible, never acceptable as formal green.
for label,raw in [("truncated",b"{"),("duplicate",b'{"x":1,"x":2}'),("array",b"[]"),("null",b"null"),("invalid_utf8",b"\xff")]:
 value,errors=parse_optional_terminal(raw,label)
 assert value=={} and errors and errors[0]["raw_bytes_retained"] is True,label+" malformed optional JSON must preserve bytes and deny formal acceptance"
print(json.dumps({"synthetic_metadata_only":True,"malformed_optional_vectors":5,"raw_preservation":True,"formal_executed":False}))
