"""Prepare a minimal a6 binding delta from the reviewed S10 assembler."""
from pathlib import Path
import ast,difflib,hashlib,json
HERE=Path(__file__).parent
OLD=Path('/tmp/geo337-S10-architecture-assembly-preparation-20261025/assemble_architecture_v2.py')
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=='b51110ff9756326a2b47d2ae4a6aded2a7995d92e2a882ddf9ec4065fae87d17'
original=raw.decode();text=original
def replace(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old))
 text=text.replace(old,new)
replace("SOURCE='82c922a3941525d3a094ac0158bdc7dea57ea360'","SOURCE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'")
replace("ROOT=OWN/'F10-pool'","ROOT=OWN/'a6-architecture-source-20261026'")
replace("GATES=OWN/'S10-preledger-checks-original-20261025'","GATES=OWN/'a6-architecture-gates-original-20261026'")
replace("PREP=OWN/'F10-source-preparation-reserve-anchor'","PREP=OWN/'a6-architecture-source-original-20261026'")
replace('import argparse,collections,contextlib,datetime,fcntl,hashlib,importlib.util,json,os,re,resource,stat,sys','import argparse,collections,contextlib,datetime,fcntl,hashlib,importlib.util,json,os,re,resource,shutil,stat,sys')
for line in original.splitlines():
 if line.startswith(('GATES_PIN=','GATE_PEER=','GATE_PEER_PIN=','SOURCE_PEER=','SOURCE_PEER_PIN=','SOURCE_MANIFEST_PIN=')):
  replace(line,'# '+line.split('=')[0]+' is bound below to actual a6 outputs, never historical S10 execution.')
replace("'決策佇列.md':'fe822051b5413fb79490b333e23f3c9d6b96959c01f937c274d3246772c15e14'","'決策佇列.md':'e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740'")
replace("p.add_argument('--root-execution-lease',action='store_true');a=p.parse_args()","p.add_argument('--root-execution-lease',action='store_true');p.add_argument('--bindings',type=Path,required=True);p.add_argument('--bindings-sha256',required=True);a=p.parse_args()")
replace(" need(a.root_execution_lease,'root must schedule after full123 lease ends')",""" need(a.root_execution_lease,'root must schedule actual a6 assembly after the original three judges complete')
 binding_raw=pinned(a.bindings,a.bindings_sha256);binding=json.loads(binding_raw)
 need(binding['source_sha']==SOURCE and binding['root_execution_lease'] is True,'actual a6 original binding lease')
 need(Path(binding['source_result']['path'])==PREP/'RESULT.json' and Path(binding['gate_result']['path'])==GATES/'RESULT.json','fixed a6 original source/gate paths')
 prepared=json.loads(pinned(PREP/'RESULT.json',binding['source_result']['sha256']))
 need(prepared['source_sha']==SOURCE and prepared['exit_code']==0 and prepared['materialized'] is True,'actual a6 source complete')
 SOURCE_MANIFEST_PIN=prepared['source_manifest_sha256']
 GATES_PIN=binding['gate_result']['sha256']
 GATE_PEER=Path(binding['gate_actual_peer']['path']);GATE_PEER_PIN=binding['gate_actual_peer']['sha256']
 SOURCE_PEER=Path(binding['source_actual_peer']['path']);SOURCE_PEER_PIN=binding['source_actual_peer']['sha256']""")
replace(" need(O.is_absolute()and O==O.resolve()and O.parent==OWN and not O.exists(),'fresh direct OWN output child')"," need(O==OWN/'a6-architecture-four-original-20261026'and O==O.resolve()and not O.exists(),'fresh fixed a6 architecture output')")
replace("  O.mkdir();(O/'new').mkdir();(O/'previous-artifact').mkdir();(O/'original-gates').mkdir();(O/'tmp').mkdir()","""  seen=set();used=0
  for root in [OWN,Path('/dev/shm/geo337-F9-browsers-20261025')]:
   for path in [root,*root.rglob('*')]:
    st=path.lstat();key=(st.st_dev,st.st_ino)
    if key not in seen:seen.add(key);used+=st.st_blocks*512
  need(used+67108864<=2147483648 and shutil.disk_usage(OWN).free>=67108864,'original64MiB and two-OWN2GiB assembly admission')
  O.mkdir();(O/'new').mkdir();(O/'previous-artifact').mkdir();(O/'original-gates').mkdir();(O/'tmp').mkdir()
  (O/'ROOT_BINDINGS.json').write_bytes(binding_raw)
  dump(O/'RESOURCE_ADMISSION.json',{'shared_before':used,'additional_bound':67108864,'shared_ceiling':2147483648})""")
replace("need(gate_peer['exit_code']==source_peer['exit_code']==0,'closed source/gate actual peers')","need(gate_peer['exit_code']==source_peer['exit_code']==0 and not gate_peer['blocking_findings'] and not source_peer['blocking_findings'] and gate_peer['source_sha']==source_peer['source_sha']==SOURCE and gate_peer['gate_result_sha256']==GATES_PIN and source_peer['source_result_sha256']==binding['source_result']['sha256'],'actual a6 source/gate peer identities')")
replace("need([x['exit_code']for x in batch['gates']]==[1,0,0,0,0,0]and not batch['all_gates_passed'],'original stale check preserved separately')","need([x['exit_code']for x in batch['gates']]==[0,0,0] and batch['all_gates_passed'] and batch['exit_code']==0,'all three actual a6 original judges passed; no synthetic ledger row')")
replace("for number,g in enumerate(batch['gates'][1:4]):","for number,g in enumerate(batch['gates']):")
replace("f'{number+5:06d}'","f'{number+4:06d}'")
replace('本次改動的test_geo314_commit_paths.py與決策不在604inputs，帳本仍須另完整重產。','相對前次執行的test_geo314_commit_paths.py與決策不在604inputs；全帳本保留S10實際重產原件，其於a6有效性由獨立--check判定，本架構收據不認證帳本。')
replace('為已授權normal merge逐字合入。','為a6既有檔案的逐byte快照，不以其內容自行擴張授權。')
text=text.replace('S10 original-gate receipt assembly','a6 original-gate receipt assembly')
text=text.replace('closed S10 original gates','closed a6 original gates')
text=text.replace('Root executes only after the full-ledger lease ends.','Root executes only after the actual a6 three-gate batch and its source lease end.')
text=text.replace('沒有重跑三裁判。','本組裝階段沒有再次執行三裁判。')
text=text.replace('original three gate execution.','actual a6 original three gate execution.')
# The execution source labels now describe newly executed a6 gates. S10 stays
# explicitly named only in history/ledger wording, never as a moved gate result.
for old,new in [('Assemble four S10 artifacts','Assemble four a6 artifacts'),('fixed S10 original source only','fixed a6 original source only'),('original S10 executions','original a6 executions'),('current source exact clean S10','current source exact clean a6'),('protected S10 SSOT bytes','protected a6 SSOT bytes'),('clean exactS10','clean exacta6'),('executed at S10','executed at a6'),('labelled at S10','labelled at a6'),('relabeled at S10','relabeled at a6'),('relabelled at S10','relabelled at a6'),('S10 must have zero','a6 must have zero'),('未在S10重跑或移標','未在a6重跑或移標')]:text=text.replace(old,new)
ast.parse(text)
(HERE/'assemble_a6.py').write_text(text)
(HERE/'ASSEMBLER_DIFF.txt').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=str(OLD),tofile='assemble_a6.py')))
(HERE/'S10_ASSEMBLER_SOURCE_BINDING.json').write_text(json.dumps({'path':str(OLD),'sha256':hashlib.sha256(raw).hexdigest(),'new_sha256':hashlib.sha256(text.encode()).hexdigest(),'actual_a6_gates_executed':False,'source_materialized':False,'assembly_executed':False},indent=2)+'\n')
print('Prepared assembler only; no source access or formal execution.')
