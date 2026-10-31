from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).parent;OLD=Path('/workspace/geo323-final-r6-stage-tools-20261024');H=lambda b:hashlib.sha256(b).hexdigest()
assert not (D/'PLAN.json').exists(), 'prepare only once; never rewrite a bound request'
prior_pins_raw=(OLD/'FINAL_PINS.json').read_bytes();assert H(prior_pins_raw)=='7234344b39724aa2970723ff402b040678ac00ffa8fed24859a6262cdd46a18c'
prior_pins=json.loads(prior_pins_raw)['files']
rows=[]
for n in ['prepare_source.py','launch_stages.py','bind_final_request.py','start_five.py']:
 raw=(OLD/n).read_bytes();assert H(raw)==prior_pins[n]['sha256'];s=raw.decode()
 if n=='prepare_source.py':
  a="fs=os.statvfs('/workspace');report['free_bytes_before']=fs.f_bavail*fs.f_frsize";b="fs=os.statvfs(target.parent);report['free_bytes_before']=fs.f_bavail*fs.f_frsize;report['resource_filesystem']=str(target.parent)";assert s.count(a)==1;s=s.replace(a,b)
 if n=='bind_final_request.py':
  a='df66452e7a514032453bea93b8b18ab74d7b1457';assert s.count(a)==1;s=s.replace(a,'1449d430d1c4734bb1bc3a9f91f3851c845cc0f3')
 if n=='start_five.py':
  s=s.replace('import argparse,json,re,sys,traceback','import argparse,json,os,re,sys,traceback').replace('new R6 source required','new R7 source required')
  a="  need(request['source_sha']==S,'one fixed public R');rec.run(['df','-B1','/workspace','/tmp'],root)"
  b="""  need(request['source_sha']==S,'one fixed public R');rec.run(['df','-B1','/workspace','/tmp'],root)
  resource_root=Path(request['resource_filesystem']);need(resource_root==Path('/tmp'),'new R7 raw storage filesystem is TMP')
  for destination in [root,Path(request['acceptance_out']),HERE]:
   need(destination.is_relative_to(resource_root),'all new R7 source/output/tools must be private TMP paths')
   need(destination.parent.stat().st_dev==resource_root.stat().st_dev,'same actual storage device required')
  fs=os.statvfs(resource_root);free=fs.f_bavail*fs.f_frsize
  result['storage_admission']={'filesystem':str(resource_root),'free_before':free,'required':request['full_round_min_free_bytes'],'estimated_round_bytes':request['estimated_round_bytes'],'native_reserve_bytes':request['native_reserve_bytes'],'scope':'storage admission only; no timing or product threshold changed'}
  need(free>=request['full_round_min_free_bytes'],'R7 fresh round138MiB plus native128MiB TMP headroom')"""
  assert s.count(a)==1;s=s.replace(a,b)
 ast.parse(s);(D/n).write_text(s)
 if raw!=s.encode():(D/(n+'.diff')).write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='R6/'+n,tofile='R7/'+n)))
 rows.append({'name':n,'old_sha256':H(raw),'new_sha256':H(s.encode()),'bytes':len(s.encode())})
r=json.loads((OLD/'REQUEST.unbound.json').read_text())
r.update(status='PARAMETER_PLAN_ONLY; new root-selected R7 source unset; no materialization or formal execution',source_sha=None,selected_final_source='__ROOT_FINAL_R7_SHA__',source_checkout='/tmp/geo323-final-r7-source-20261024',acceptance_out='/tmp/g337323R7',inner_lock='/tmp/g337323R7/stage.lock',resource_filesystem='/tmp',estimated_round_bytes=138*1024*1024,native_reserve_bytes=128*1024*1024,full_round_min_free_bytes=(138+128)*1024*1024,source_resource_min_free_bytes=(138+128)*1024*1024)
r['source_budget_scope']='Storage admission only: conservative 138MiB round plus 128MiB native TMP reserve; not a product performance threshold'
for n,pin in r['tool_files'].items():
 b=(Path(r['original_tools'])/n).read_bytes();assert H(b)==pin['sha256'] and len(b)==pin['bytes']
for n in ['REQUEST.unbound.json','REQUEST.template.json']:(D/n).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
plan={'source_unbound':True,'source_materialized':False,'C_run':False,'formal_run':False,'required_ancestor':'1449d430d1c4734bb1bc3a9f91f3851c845cc0f3','new_raw_filesystem':'/tmp','tool_changes':rows,'unchanged':['original launch_stages.py all bytes','accepted v5 six runtime tools and original source/sample/scene/profile/golden/threshold/600-second semantics','both nonblocking global locks plus new private inner stage lock','collect all five stages despite red; separate cumulative CLI and own execution exit','R5/R6 original red records remain untouched'],'resource_only_change':{'before_materialization_and_before_formal':r['full_round_min_free_bytes'],'round_estimate_bytes':r['estimated_round_bytes'],'native_reserve_bytes':r['native_reserve_bytes'],'unit_note':'Use MiB conservatively for root 138MB round request; this is disk admission, never a numerical product threshold'}}
(D/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'prepared':str(D),'formal_run':False,'tmp_min_free_bytes':r['full_round_min_free_bytes']}))
