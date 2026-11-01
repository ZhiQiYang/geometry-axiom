from pathlib import Path
import ast, datetime, difflib, hashlib, json
D=Path('/tmp/geo323-r8-collection-preparation-20261025')
O=Path('/tmp/geo323-r8-collector-static-peer-20261025')
P=json.loads((D/'PROVENANCE.json').read_bytes())
H=lambda b:hashlib.sha256(b).hexdigest()
files=['collect.template.py','launch.template.py','freeze_terminal_plan.py']
checks=[]
for name in files:
    raw=(D/name).read_bytes(); assert H(raw)==P['draft_hashes'][name]; ast.parse(raw)
    original=(D/'original-r7-small-tools'/(name+'.txt')).read_bytes()
    assert H(original)==P['original_tool_hashes'][name]
    label={'collect.template.py':'COLLECTOR','launch.template.py':'LAUNCH','freeze_terminal_plan.py':'FREEZE'}[name]
    diff=''.join(difflib.unified_diff(original.decode().splitlines(True),raw.decode().splitlines(True),fromfile='reviewed-R7/'+name,tofile='unexecuted-R8/'+name))
    assert diff==(D/('R7_TO_R8_'+label+'.diff')).read_text(),name
    checks.append(name+': exact draft/original pins, syntax and diff')
assert (D/'prepare_plan.py').read_bytes()==(D/'freeze_terminal_plan.py').read_bytes()
collector=(D/'collect.template.py').read_text();launcher=(D/'launch.template.py').read_text();freeze=(D/'freeze_terminal_plan.py').read_text()
replacements=[('75a1e93811a52b69385cbdaf6a09d773ed9052ad','6df0264f75e84f03adb70746b6ac3db07a9910fc'),('/tmp/g337323R8','/tmp/g337323R7'),('/tmp/geo323-final-r8-stage-tools-20261024','/tmp/geo323-final-r7-stage-tools-20261024'),('/tmp/geo323-final-r8-source-20261024','/tmp/geo323-final-r7-source-20261024'),('/tmp/geo323-r8-full-package-20261025','/tmp/geo323-r7-full-package-20261024'),('R7_TO_R8_COLLECTOR.diff','R6_TO_R7_COLLECTOR.diff'),('adapt_r7.py','adapt_r6.py'),('ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz','ORIGINAL_R7_FIVE_STAGE_RAW.tar.gz')]
restored=collector
for a,b in replacements:restored=restored.replace(a,b)
assert restored==(D/'original-r7-small-tools/collect.template.py.txt').read_text()
restored=launcher.replace('75a1e93811a52b69385cbdaf6a09d773ed9052ad','6df0264f75e84f03adb70746b6ac3db07a9910fc').replace('R8','R7')
assert restored==(D/'original-r7-small-tools/launch.template.py.txt').read_text()
checks+=['Collector and launcher byte-for-byte original after only necessary parameter substitutions.']
for fragment in ['MAX_ARCHIVE=36*1024*1024','MAX_METADATA=4*1024*1024','NATIVE_TMP_RESERVE=128*1024*1024','MIN_FREE=NATIVE_TMP_RESERVE+MAX_ARCHIVE+MAX_METADATA']:
    assert fragment in collector
for fragment in ["len(terminal_api)==1", "z.get('session_id')==62076", "api[0].name=='EXEC_TOOL_INITIAL.json'", "z['exit_code']==outer['exit']", "stdout_stderr_reconstructed':False", "missing intermediate responses are not invented", "('original',RAW)", "('original-orchestration',TOOLS)", "('tools/v5',V5/'tools-v5')", "('terminal-summary-producer',O/'summary-tool')", "'original-R7-collector/'", "'r8-stage-tools-static-peer/'"]:
    assert fragment in freeze,fragment
assert 'tracked-ledger-check-physical-E51e' not in freeze and 'R7_SOURCE_PREPARATION_ACTUAL_PEER' not in freeze
assert 'ABC_result_present' in freeze and "'ABC_result'in r" in freeze
assert "r['full_acceptance_passed'] is None and r['all_required_stages_completed'] is False" in collector
assert "operational_free_space_guard_bytes':168*1024*1024" in freeze
required=[Path('/tmp/geo323-r7-full-collection-20261024')/n for n in ['collect.py','launch.py','README.md','prepare_plan.py','PLAN.json','PROVENANCE.json']]
required += [Path('/tmp/geo323-r8-tools-peer-specials-20261024')/n for n in ['REVIEW.json','review.py']]
assert all(p.is_file() for p in required)
checks+=['Original initial/session62076 and exactly one terminal exit required; missing API sequence not reconstructed.',
    'Current raw orchestration/v5/source/summary scope retained; historical R7 and old ledger distinctions accurate.',
    'Original resource limits, terminal/exit/ABC fields and byte roundtrip remain.',
    'Historical collector and R8 static peer paths exist; only metadata inspected.']
report={'schema':'geo323-r8-collector-template-static-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'findings':[],
    'source_sha':P['source_sha'],'reviewed_files':{n:H((D/n).read_bytes()) for n in files+['prepare_plan.py','PROVENANCE.json']},'checks':checks,
    'initial_review_error':{'actual_tool_command_exit':1,'kind':'reviewer path assumption','detail':'Initial read assumed original-r7-small-tools/collect.template.py; actual retained file has .txt suffix. Producer unchanged; corrected reviewer path only.'},
    'scope':['Collector/launcher/freeze drafts only; summary assigned separately.','Small source and metadata reads only; no product execution, Git operations, raw hashing or archive creation.','Frozen PLAN, actual collector and archive completeness require separate actual review.']}
assert not (O/'REVIEW.json').exists()
(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(O/'REVIEW.md').write_text('R8 collector／launcher／freeze 小稿靜審通過。必要參數還原後，collector及launcher逐byte等於原R7；完整原流、ABC缺席、七ELF保留及36+4+128MiB守門不變。freeze綁原INITIAL/session62076與唯一terminal exit，不補造API序列；current與歷史scope分明。\n\n未執行collector，未審summary，未讀大型raw或Git；PLAN與封包待實績另驗。第一次reviewer讀取誤漏原檔.txt副檔名，已只修正審查路徑，未改producer。\n')
print(json.dumps({'exit_code':0,'review':str(O/'REVIEW.json'),'sha256':H((O/'REVIEW.json').read_bytes())}))
