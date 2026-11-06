"""Write passive R8 collection drafts from reviewed R7 tools; never inspect active raw OUT."""
from pathlib import Path
import ast,difflib,hashlib,json
O=Path(__file__).resolve().parent
P=Path('/tmp/geo323-r7-full-collection-20261024')
S='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
OLD='6df0264f75e84f03adb70746b6ac3db07a9910fc'
def H(b):return hashlib.sha256(b).hexdigest()
def write(name,data):
 p=O/name;assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(data if isinstance(data,bytes)else data.encode())
def replace(s,a,b,count=None):
 assert a in s,a
 if count is not None:assert s.count(a)==count,(a,s.count(a),count)
 return s.replace(a,b)
def params(s):
 for a,b in [('/tmp/g337323R7','/tmp/g337323R8'),('/tmp/geo323-final-r7-stage-tools-20261024','/tmp/geo323-final-r8-stage-tools-20261024'),('/tmp/geo323-final-r7-source-20261024','/tmp/geo323-final-r8-source-20261024'),('/tmp/geo323-r7-full-package-20261024','/tmp/geo323-r8-full-package-20261025'),('/tmp/geo323-r7-terminal-summary-20261024','/tmp/geo323-r8-terminal-summary-20261025'),(OLD,S)]:s=s.replace(a,b)
 return s
originals={n:(P/n).read_bytes()for n in ['summarize_terminal.py','collect.template.py','launch.template.py','freeze_terminal_plan.py']}
summary=params(originals['summarize_terminal.py'].decode())
summary=summary.replace('g337323R7 and stage-tools','g337323R8 and stage-tools').replace('architecture execution Me321 with adopted outputs at F7 is separately recorded.','architecture execution and adopted outputs are separately recorded; this summary does not relabel those executions.').replace('remain unrun at F7 in this driver','remain unrun at F8 in this driver')
collect=params(originals['collect.template.py'].decode())
collect=replace(collect,'R6_TO_R7_COLLECTOR.diff','R7_TO_R8_COLLECTOR.diff',1)
collect=replace(collect,'adapt_r6.py','adapt_r7.py',1)
collect=replace(collect,'ORIGINAL_R7_FIVE_STAGE_RAW.tar.gz','ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz',1)
launch=params(originals['launch.template.py'].decode()).replace('original R7 terminal pin','original R8 terminal pin').replace('actual R7 terminal before heavy collection','actual R8 terminal before heavy collection')
freeze=params(originals['freeze_terminal_plan.py'].decode())
freeze=replace(freeze,'Freeze original R7 terminal membership','Freeze original R8 terminal membership',1)
freeze=replace(freeze,"R6=Path('/workspace/geo323-r6-full-collection-20261024')","PREVIOUS=Path('/tmp/geo323-r7-full-collection-20261024')",1)
freeze=replace(freeze,"'aab84118de09b9bb394fb6a11eeb51bef3babecd9937b1c9c633caf4a046e211'",repr(H(collect.encode())),1)
freeze=replace(freeze,"'930f203eaaf6c7d428d7516491d883e613f75675673df522d96b36af9ff13bab'",repr(H(launch.encode())),1)
before="""api=[TOOLS/f'EXEC_TOOL_POLL_{i:02d}.json' for i in range(1,4)]
api_records=[]
for p in api:
 raw=p.read_bytes();z=json.loads(raw);assert isinstance(z,dict)
 api_records.append({'path':str(p),'bytes':len(raw),'sha256':H(raw),'scope':'Unmodified owner-supplied original API tool response'})
for p in api[:2]:assert json.loads(p.read_bytes())['session_id']==73841
last=json.loads(api[-1].read_bytes());assert last['exit_code']==outer['exit'] and last['chunk_id']=='87c3e8'
scope={'source_sha':S,'tool_session_id':73841,'stdout_stderr_reconstructed':False,'supplied_api_files':api_records,'sequence_completeness':'No claim of complete API response sequence. These three exact poll responses were supplied by the execution owner; initial launch response is not supplied here.','actual_original_streams':'outer-five Recorder and launch-five retain actual full subprocess streams and exits; these are separate from API object completeness.'}
"""
after="""api=sorted(TOOLS.glob('EXEC_TOOL_*.json'),key=lambda p:(p.name!='EXEC_TOOL_INITIAL.json',p.name))
assert api and api[0].name=='EXEC_TOOL_INITIAL.json','original owner launch object is mandatory'
api_records=[];terminal_api=[]
for p in api:
 raw=p.read_bytes();z=json.loads(raw);assert isinstance(z,dict)
 if 'exit_code' in z:
  assert type(z['exit_code']) is int and z['exit_code']==outer['exit']
  terminal_api.append(p.name)
 else:assert z.get('session_id')==62076,'all supplied running API objects must bind the original R8 session'
 api_records.append({'path':str(p),'bytes':len(raw),'sha256':H(raw),'scope':'Unmodified owner-supplied original API tool response'})
assert json.loads(api[0].read_bytes()).get('session_id')==62076
assert len(terminal_api)==1,'one original owner terminal API response required; missing is not reconstructed'
scope={'source_sha':S,'tool_session_id':62076,'stdout_stderr_reconstructed':False,'supplied_api_files':api_records,'terminal_api_file':terminal_api[0],'sequence_completeness':'No claim of complete API response sequence. All currently supplied original launch/poll/terminal objects are retained exactly; missing intermediate responses are not invented.','actual_original_streams':'outer-five Recorder and launch-five retain actual full subprocess streams and exits; these are separate from API object completeness.'}
"""
freeze=replace(freeze,before,after,1)
freeze=replace(freeze,"('terminal-summary-producer',Path('/tmp/geo323-r7-summary-tool-preparation-20261024')),('tracked-ledger-check-physical-E51e',Path('/tmp/geo337-6df-at-51e-ledger-freshness-20261024')),('tracked-ledger-check-preparation',Path('/tmp/geo337-R7-ledger-check-preparation-20261024'))","('terminal-summary-producer',O/'summary-tool')",1)
freeze=replace(freeze,"add('original-R6-collector/'+name,R6/name)","add('original-R7-collector/'+name,PREVIOUS/name)",1)
start=freeze.index("PEERS=Path('/workspace/train337-canvas-peer-resume')")
end=freeze.index("for name in ['FINAL_PINS.json'",start)
freeze=freeze[:start]+"PEERS=Path('/tmp/geo323-r8-tools-peer-specials-20261024')\nfor name in ['REVIEW.json','review.py']:add('r8-stage-tools-static-peer/'+name,PEERS/name)\n"+freeze[end:]
freeze=freeze.replace('true R7 terminal','true R8 terminal').replace('Current R7 original terminal pinned','Current R8 original terminal pinned')
tools={'summarize_terminal.py':summary,'collect.template.py':collect,'launch.template.py':launch,'freeze_terminal_plan.py':freeze,'prepare_plan.py':freeze}
for name,body in tools.items():
 ast.parse(body);write(name,body)
write('summary-tool/summarize_terminal.py',summary)
for name,data in originals.items():write('original-r7-small-tools/'+name+'.txt',data)
for name,new in [('summarize_terminal.py',summary),('collect.template.py',collect),('launch.template.py',launch),('freeze_terminal_plan.py',freeze)]:
 label={'summarize_terminal.py':'SUMMARY','collect.template.py':'COLLECTOR','launch.template.py':'LAUNCH','freeze_terminal_plan.py':'FREEZE'}[name]
 write('R7_TO_R8_'+label+'.diff',''.join(difflib.unified_diff(originals[name].decode().splitlines(True),new.splitlines(True),fromfile='reviewed-R7/'+name,tofile='unexecuted-R8/'+name)))
provenance={'source_sha':S,'required_H_ancestor':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7','executed':False,'formal_subject_reexecuted':False,'active_raw_out_read':False,'original_tool_hashes':{n:H(v)for n,v in originals.items()},'draft_hashes':{n:H(v.encode())for n,v in tools.items()},'changes':['F8/source/output paths and round labels','actual R8 API session62076 with original initial+available polls+exactly one terminal required, no API reconstruction or invented intermediate responses','R7 historical collector provenance retained as historical R7','old F7/E51 ledger and old R7 peer attachments omitted from current R8 package; current R8 ledger is UNRUN and no R8 source peer is claimed','known R8 tool static peer included'], 'unexecuted_outputs':['R8 summary','frozen membership PLAN','bound collector and launcher','archive','publication'],'limitations':['No new test mirror added; original terminal guards and resource limits retained.','Seven ELF bodies remain at original paths and are hash-only in archive, unchanged original policy.','Original 175 scenes/350 comparisons/36 samples/4 profiles and own-stage versus cumulative CLI outcomes stay original.','ABC_result presence and original acceptance fields copied without filling missing verdicts.']}
write('PROVENANCE.json',json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
write('summary-tool/PINS.json',json.dumps({'source_sha':S,'summary_tool_sha256':H(summary.encode()),'executed':False},indent=2)+'\n')
print(json.dumps({'drafts_written':list(tools),'source_sha':S,'executed':False,'raw_out_read':False,'draft_hashes':provenance['draft_hashes']},indent=2))
