from pathlib import Path
import ast,difflib,json,hashlib
D=Path(__file__).parent;OLD=Path('/workspace/geo323-final-r5-stage-tools-20261024')
pins={'prepare_source.py':'a598fed13faae894a3a003a32afd58b42e8289f6455315b0aae03fed9bcd6b82','launch_stages.py':'480e07e9002f9a84f2779d93073a545755e78dba02d645232a41483aec762345','bind_final_request.py':'76b14b4147d539bbcc0d4c8ea3f4db2f4a04830ea280c42c309e0923ad022bff','start_five.py':'1d2106bc0c565faf1b23d25a7d05c42930b2462e823253af831ef478da4b3c8f'}
def h(b):return hashlib.sha256(b).hexdigest()
rows=[]
for n,pin in pins.items():
 raw=(OLD/n).read_bytes();assert h(raw)==pin;s=raw.decode()
 if n=='bind_final_request.py':
  before="'aa16e73d6e1f2965e0a911581e2a545aaaf66870'";assert s.count(before)==1;s=s.replace(before,"'df66452e7a514032453bea93b8b18ab74d7b1457'")
 if n=='start_five.py':
  s=s.replace('import json,sys,traceback','import argparse,json,re,sys,traceback')
  old="HERE=Path(__file__).resolve().parent;S='a22df116c7e9f6b7d074451f1c8052d59e7e4f3e'";assert s.count(old)==1;s=s.replace(old,'HERE=Path(__file__).resolve().parent')
  old="def main():\n out=HERE/'outer-five'";assert s.count(old)==1;s=s.replace(old,"def main():\n p=argparse.ArgumentParser();p.add_argument('--sha',required=True);a=p.parse_args();S=a.sha;need(re.fullmatch('[0-9a-f]{40}',S),'full root-selected new R6 source required')\n out=HERE/'outer-five'")
 ast.parse(s);(D/n).write_text(s)
 if s.encode()!=raw:(D/(n+'.diff')).write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='R5/'+n,tofile='R6/'+n)))
 rows.append({'file':n,'original_sha256':pin,'new_sha256':h(s.encode()),'bytes':len(s.encode())})
b=(OLD/'REQUEST.unbound.json').read_bytes();assert h(b)=='7035eccc199423e4045d05c897701d5e148b1d0238aac5b213401d051c748639';request=json.loads(b)
request.update(status='PARAMETER_PLAN_ONLY; new root-selected R6 source unset; no source or formal execution',source_sha=None,selected_final_source='__ROOT_FINAL_R6_SHA__',source_checkout='/workspace/geo323-final-r6-source-20261024',acceptance_out='/workspace/g337323R6',inner_lock='/workspace/g337323R6/stage.lock')
for n,p in request['tool_files'].items():
 raw=(Path(request['original_tools'])/n).read_bytes();assert len(raw)==p['bytes'] and h(raw)==p['sha256']
for n in ['REQUEST.unbound.json','REQUEST.template.json']:(D/n).write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
(D/'PLAN.json').write_text(json.dumps({'source_materialized':False,'C_run':False,'formal_run':False,'final_source':'UNSET until root adopts fresh architecture four files','required_ancestor':'df66452e7a514032453bea93b8b18ab74d7b1457','tool_delta':rows,'unchanged':['accepted v5 runtime six files including original PIPE and deferred perf flush','original base/main/source closure and full 175-scenes/36-samples/4-profile-points','original thresholds and clock boundaries and child timeouts','both global exclusive locks; fresh private inner lock','continue after compare/perf red and preserve cumulative CLI versus original stage execution exits','R5 source/outputs are never rewritten'],'prior_R5_preserved':'/workspace/g337323R5'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prepared':str(D),'source_materialized':False,'C_run':False,'formal_run':False}))
