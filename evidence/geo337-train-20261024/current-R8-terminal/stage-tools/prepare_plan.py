from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).resolve().parent;OLD=Path('/tmp/geo323-final-r7-stage-tools-20261024');H=lambda b:hashlib.sha256(b).hexdigest()
assert not(D/'PLAN.json').exists(),'prepare once; never rewrite bound request'
rawpins=(OLD/'FINAL_PINS.json').read_bytes();assert H(rawpins)=='d3b42b86b723a75e44fe6ad6f14d1c365b76c980f7a185fa79d2fcb6ee474759';pins=json.loads(rawpins)['files'];changes=[]
for name in ['prepare_source.py','launch_stages.py','bind_final_request.py','start_five.py']:
 raw=(OLD/name).read_bytes();assert H(raw)==pins[name]['sha256'];s=raw.decode()
 if name=='bind_final_request.py':
  a="p.add_argument('--sha',required=True);a=p.parse_args()";b="p.add_argument('--sha',required=True);p.add_argument('--required-ancestor',required=True);a=p.parse_args()";assert s.count(a)==1;s=s.replace(a,b)
  a="if not re.fullmatch('[0-9a-f]{40}',a.sha):raise RuntimeError('full root-selected final R required')";b="if not re.fullmatch('[0-9a-f]{40}',a.sha) or not re.fullmatch('[0-9a-f]{40}',a.required_ancestor):raise RuntimeError('full root-selected final R and actual published new H ancestor required')";assert s.count(a)==1;s=s.replace(a,b)
  a="git('merge-base','--is-ancestor','1449d430d1c4734bb1bc3a9f91f3851c845cc0f3',a.sha)";b="git('merge-base','--is-ancestor',a.required_ancestor,a.sha)";assert s.count(a)==1;s=s.replace(a,b)
  a="request['selected_final_source']=a.sha;request['status']=";b="request['selected_final_source']=a.sha;request['required_product_ancestor']=a.required_ancestor;request['status']=";assert s.count(a)==1;s=s.replace(a,b)
  a="result={'source_sha':a.sha,'source_materialized'";b="result={'source_sha':a.sha,'required_product_ancestor':a.required_ancestor,'source_materialized'";assert s.count(a)==1;s=s.replace(a,b)
 if name=='start_five.py':s=s.replace('R7','R8')
 ast.parse(s);(D/name).write_text(s)
 if s.encode()!=raw:(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='R7/'+name,tofile='R8/'+name)))
 changes.append({'name':name,'before_sha256':H(raw),'after_sha256':H(s.encode()),'bytes':len(s.encode())})
raw=(OLD/'REQUEST.unbound.json').read_bytes();assert H(raw)==pins['REQUEST.unbound.json']['sha256'];r=json.loads(raw)
r.update(status='PARAMETER_PLAN_ONLY; new H ancestor and final R8 source UNBOUND; no materialization or formal execution',selected_final_source='__ROOT_FINAL_R8_SHA__',source_sha=None,required_product_ancestor=None,source_checkout='/tmp/geo323-final-r8-source-20261024',acceptance_out='/tmp/g337323R8',inner_lock='/tmp/g337323R8/stage.lock')
for name in ['REQUEST.unbound.json','REQUEST.template.json']:(D/name).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for name,pin in r['tool_files'].items():
 raw=(Path(r['original_tools'])/name).read_bytes();assert H(raw)==pin['sha256'] and len(raw)==pin['bytes']
assert(D/'prepare_source.py').read_bytes()==(OLD/'prepare_source.py').read_bytes()
assert(D/'launch_stages.py').read_bytes()==(OLD/'launch_stages.py').read_bytes()
assert (D/'start_five.py').read_text().replace('R8','R7')==(OLD/'start_five.py').read_text()
old_r=json.loads((OLD/'REQUEST.unbound.json').read_bytes());delta={k for k in set(old_r)|set(r) if old_r.get(k)!=r.get(k)}
assert delta=={'status','selected_final_source','source_checkout','acceptance_out','inner_lock'}
assert 'required_product_ancestor' not in old_r and r['required_product_ancestor'] is None
assert r['full_round_min_free_bytes']==r['source_resource_min_free_bytes']==(138+128)*1024*1024
assert all(not Path(r[k]).exists()for k in ['source_checkout','acceptance_out'])
plan={'required_product_ancestor':None,'selected_final_source':None,'source_unbound':True,'materialized':False,'formal_run':False,'C_run':False,'old_final_pins_sha256':H(rawpins),'tool_changes':changes,'request_value_changes':sorted(delta),'new_null_request_field':'required_product_ancestor','source_ancestor_policy':'Root must supply the actual newly published H source full SHA; no guessed SHA, previous S144, or substitution of F7 for the new H ancestor. The original Git merge-base ancestry check remains mandatory.','unchanged':['prepare_source.py all bytes','launch_stages.py all bytes','six v5 tool bytes and pinned inventory','175 scenes / 36 samples / 4 profiles','original thresholds / timeout600 / clocks / samples / cumulative exit handling','both nonblocking heavy locks','all new runtime/preparation/source/OUT in TMP','resource admission138MiB+native128MiB'],'static_only':True}
(D/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'prepared':str(D),'required_product_ancestor':None,'final_source':None,'formal_run':False,'static_only':True}))
