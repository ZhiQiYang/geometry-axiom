"""Exact-source N1 withdrawals: each real Node process loads pinned variant bytes.

The checkout is never mutated. A temporary .js file supplies one module's bytes
through the Node loader; all imports resolve at the original source location.
Both green processes and the failed process use the identical selected test.
Only completed AssertionError details count, never a stack/source marker.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[2]
D='geometry-web/reconstruction-data.js';W='geometry-templates/woodworking/reconstruction-rc.js'
A='geometry-web/reconstruction-rc-adapter.js';S='geometry-web/project-store.js';U='geometry-web/reconstruction-workspace.js'
C='geometry-web/canvas_sections/P4314.js'
FAULTS=[
 ('N1_RC_DATUM_LABEL_WRONG_AXIS',D,"`位置採用或推導須明選世界 ${expected.slice(-1).toUpperCase()}；觀察確認及說明文字不建立座標轉換。`","'位置採用或推導須明選世界 Z；觀察確認及說明文字不建立座標轉換。'",'data','R13_N1_D02 rc-column','R13_N1_DATUM_AXIS_EXACT'),
 ('N1_IMPLICIT_DIMENSION',D,"raw:'',unit:null,basis:{kind:positionField(key)?'unknown':'distance'","raw:'0',unit:null,basis:{kind:positionField(key)?'unknown':'distance'",'data','R13_N1_D01 rc-column','R13_N1_NO_DIMENSION_DEFAULT'),
 ('N1_SPACE_ZERO_ALLOWED',D,'record.spaceId<1','record.spaceId<0','data','R13_N1_D01 rc-column','R13_N1_CLOSED_SCHEMA'),
 ('N1_AXIS_CONFIRMATION_RETAINED',D,"for(const key of ['start','end','center'])affected.add(key);","/* withdrawn: retain position confirmations */",'data','R13_N1_D07','R13_N1_AXIS_INVALIDATES'),
 ('N1_SPACE_REVISION_OMITTED',D,'record.spaceId=action.spaceId;inputChanged=true;','record.spaceId=action.spaceId;','data','R13_N1_D06 rc-column','R13_N1_D5_REVISION'),
 ('N1_RC_CONFIRMATION_IGNORED',D,"if(!field.confirmation)fail('R13_RC_CONFIRMATION','RC 研究幾何須逐欄有效確認；不猜補缺值。');","if(!field.confirmation)field.confirmation={value:directValue(field,key)};",'geometry','R13_N1_G03','R13_N1_G_CONFIRMATION_GATE'),
 ('N1_COLUMN_AS_CENTER',W,'rect=[v.x,v.y,v.x+v.width,v.y+v.depth]','rect=[v.x-Math.floor(v.width/2),v.y,v.x+Math.ceil(v.width/2),v.y+v.depth]','geometry','R13_N1_G02','R13_N1_COLUMN_NEGATIVE_ORIGIN'),
 ('N1_ODD_WIDTH_NEGATIVE',W,'const lo=v.center-Math.floor(v.width/2),hi=v.center+Math.ceil(v.width/2);','const lo=v.center-Math.ceil(v.width/2),hi=v.center+Math.floor(v.width/2);','geometry','R13_N1_G02','R13_N1_BEAM_ODD_X'),
 ('N1_G_DROP_DUPLICATE_GUARD',A,"need(!ids.has(record.id),'R13_G_DUPLICATE');","/* withdrawn duplicate guard */",'geometry','R13_N1_G03','R13_N1_G_DUPLICATE'),
 ('N1_G_SKIP_CAPACITY',A,"records.length<=64","records.length<=256",'geometry','R13_N1_G03','R13_N1_G_64_LIMIT'),
 ('N1_G_DROP_ENDPOINT_RANGE',W,'rect.forEach(value=>K.integer(value));','/* withdrawn endpoint range */','geometry','R13_N1_G04','R13_N1_G_D1_ENDPOINT_LENGTH'),
 ('N1_RC_READER_CAPABILITY_REMOVED',S,'SCENARIO_CAPABILITY, CASE_CAPABILITY, RECONSTRUCTION_CAPABILITY, RC_DATA_CAPABILITY];\n  }','SCENARIO_CAPABILITY, CASE_CAPABILITY, RECONSTRUCTION_CAPABILITY];\n  }','store','R13_N1_H01','R13_N1_READER_RC_CAPABILITY'),
 ('N1_COLUMN_LABEL_CENTER',U,"['x','X','X 起點']","['x','X','X 中心']",'ui','R13_N1_U02','R13_N1_COLUMN_X_ORIGIN_LABEL'),
 ('N1_UI_RC_ADOPT_VISIBLE',U,"q('rdAdopt').hidden=record.kind!=='room-height';","q('rdAdopt').hidden=false;",'ui','R13_N1_U01','R13_N1_RC_ADOPT_HIDDEN'),
 ('N1_UI_AXIS_RENDER_REPLACED',U,'binding.signature=JSON.stringify(next);state().draft=null;','binding.signature=JSON.stringify(next);state().draft=null;if(action.axis!==undefined)render();','ui','R13_N1_U04','R13_N1_AXIS_DOM_NOT_REPLACED'),
 ('N1_UI_RAW_SINGLE_LINE',U,'<textarea id="rd${stem}Raw" rows="1" inputmode="decimal" autocomplete="off" aria-describedby="rd${stem}State" placeholder="尚未填寫"></textarea>','<input id="rd${stem}Raw" type="text" inputmode="decimal" autocomplete="off" aria-describedby="rd${stem}State" placeholder="尚未填寫">','ui','R13_N1_U07 rc-column','R13_N1_RAW_MULTILINE_CONTROL'),
 ('N1_UI_PROJECTED_RAW_LOST',U,'if(projection&&projection.display===control.value)return projection.original;','if(projection&&projection.display===control.value)return control.value;','ui','R13_N1_U07 rc-column','R13_N1_PROJECTED_RAW_EXACT'),
 ('N1_UI_FOREIGN_DRAFT_DISCARDED',U,'states.get(binding.context).draft={id:action.id,action,base:binding.snapshot};','void action;','ui','R13_N1_U08 notification','R13_N1_FOREIGN_DRAFT_RETAINED'),
 ('N1_CANVAS_HISTORY_IDLE_REMOVED',C,"${first}.fields.top.confirmation===null&&connection.phase==='ready'&&!oc.busy&&ReferenceWorkspace.getEvidenceState().blocked===false","${first}.fields.top.confirmation===null&&connection.phase==='ready'&&ReferenceWorkspace.getEvidenceState().blocked===false",'ui','R13_N1_U09','R13_N1_CANVAS_HISTORY_IDLE'),
 ('N1_CANVAS_SELECT_FOCUS_REACQUIRE_REMOVED',C,"await ctl(selector);await key('Escape','Escape',27);","if(n===0){await ctl(selector);await key('Escape','Escape',27);}",'ui','R13_N1_U10','R13_N1_NATIVE_SELECT_REACQUIRE'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def run(command,env,out):
 r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=60)
 out.with_suffix('.stdout').write_bytes(r.stdout);out.with_suffix('.stderr').write_bytes(r.stderr)
 parsed=[json.loads(x) for x in r.stdout.decode().splitlines() if x.startswith('{')]
 row=dict(command=command,exit=r.returncode,events=parsed,stdout=dict(bytes=len(r.stdout),sha256=sha(r.stdout)),stderr=dict(bytes=len(r.stderr),sha256=sha(r.stderr)))
 out.with_suffix('.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');return row
def completed(r,passed):
 summaries=[x['data'] for x in r['events'] if x['type']=='summary']
 if not summaries:return False
 last=summaries[-1];counts=last.get('counts',{})
 expected={'tests':1,'passed':int(passed),'failed':int(not passed),'cancelled':0,'skipped':0,'todo':0}
 return last.get('success') is passed and all(counts.get(k)==v for k,v in expected.items())
def green(r):
 return r['exit']==0 and completed(r,True) and sum(x['type']=='pass' for x in r['events'])==1 and not any(x['type']=='failure' for x in r['events'])
def named_kill(before,fault,restored,marker):
 if not green(before) or not green(restored) or fault['exit']!=1 or not completed(fault,False):return False
 failures=[x for x in fault['events'] if x['type']=='failure']
 if len(failures)!=1 or any(x['type']=='pass' for x in fault['events']):return False
 name=next(x['name'] for x in before['events'] if x['type']=='pass')
 if failures[0]['name']!=name or next(x['name'] for x in restored['events'] if x['type']=='pass')!=name:return False
 error=failures[0]['error']
 if error.get('name')!='AssertionError' or error.get('code')!='ERR_ASSERTION':return False
 message=error.get('message')
 if not isinstance(message,str) or not message:return False
 first=message.splitlines()[0]
 # Node's assert.throws/doesNotThrow/doesNotReject add these fixed prefixes.
 # Only the assertion message's first line counts, never a diff or stack.
 for prefix in ['Missing expected exception: ','Got unwanted exception: ','Got unwanted rejection: ']:
  if first.startswith(prefix):first=first[len(prefix):];break
 return first==marker or first.startswith(marker+' ')
def self_test():
 def row(kind,exit,message='R13_NAMED_ASSERTION',name='one exact case'):
  event={'type':kind,'name':name}
  if kind=='failure':event['error']={'name':'AssertionError','code':'ERR_ASSERTION','message':message}
  counts={'tests':1,'passed':int(kind=='pass'),'failed':int(kind=='failure'),'cancelled':0,'skipped':0,'todo':0}
  return {'exit':exit,'events':[event,{'type':'summary','data':{'success':kind=='pass','counts':counts}}]}
 b=row('pass',0);f=row('failure',1);r=row('pass',0);marker='R13_NAMED_ASSERTION'
 assert named_kill(b,f,r,marker),'N1_PREDICATE_ACCEPTS_REAL_PRIMARY_ASSERTION'
 assert not named_kill(b,row('failure',1,'UNRELATED_ASSERTION\n+ actual - expected\n+ R13_NAMED_ASSERTION'),r,marker),'N1_PREDICATE_REJECTS_MARKER_IN_DIFF'
 assert named_kill(b,row('failure',1,marker+' column-x'),r,marker),'N1_PREDICATE_ACCEPTS_NAMED_SUFFIX'
 for prefix in ['Missing expected exception: ','Got unwanted exception: ','Got unwanted rejection: ']:
  assert named_kill(b,row('failure',1,prefix+marker+'\nActual message: "detail"'),r,marker),'N1_PREDICATE_ACCEPTS_NODE_ASSERT_WRAPPER'
 assert not named_kill(b,row('failure',1,marker+'_UNRELATED'),r,marker),'N1_PREDICATE_REJECTS_MARKER_SUBSTRING'
 assert not named_kill(b,row('failure',1,marker,name='different case'),r,marker),'N1_PREDICATE_REJECTS_OTHER_CASE'
 assert not named_kill(b,f,row('pass',0,name='different restore'),marker),'N1_PREDICATE_REJECTS_OTHER_RESTORE'
 assert not named_kill(row('failure',1),f,r,marker),'N1_PREDICATE_REJECTS_RED_BASELINE'
 wrong=row('failure',1);wrong['events'][0]['error']['name']='TypeError'
 assert not named_kill(b,wrong,r,marker),'N1_PREDICATE_REJECTS_NON_ASSERTION'
 wrong=row('failure',1);wrong['events'][0]['error']['code']='ERR_MODULE_NOT_FOUND'
 assert not named_kill(b,wrong,r,marker),'N1_PREDICATE_REJECTS_IMPORT_ERROR'
 wrong=row('failure',1);wrong['events'].insert(0,wrong['events'][0])
 assert not named_kill(b,wrong,r,marker),'N1_PREDICATE_REJECTS_EXTRA_FAILURE'
 wrong=row('pass',0);wrong['events'][-1]['data']['counts']['skipped']=1
 assert not named_kill(wrong,f,r,marker),'N1_PREDICATE_REJECTS_SKIPPED_BASELINE'
 print(json.dumps({'self_test':'passed','cases':14}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--only',choices=[f[0] for f in FAULTS]);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.self_test:self_test();return
 if a.out is None:p.error('--out is required without --self-test')
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);assert not list(out.iterdir()),'output must be empty'
 results=[]
 with tempfile.TemporaryDirectory(prefix='r13-n1-withdrawal-') as td:
  td=Path(td);hook=td/'hook.cjs'
  hook.write_text("const fs=require('node:fs'),Module=require('node:module'),path=require('node:path');const read=fs.readFileSync,bytes=read(process.env.N1_VARIANT);fs.readFileSync=(f,o)=>typeof f==='string'&&path.resolve(f)===process.env.N1_TARGET?(typeof o==='string'||o?.encoding?bytes.toString(typeof o==='string'?o:o.encoding):Buffer.from(bytes)):read(f,o);const load=Module._extensions['.js'];Module._extensions['.js']=(m,f)=>f===process.env.N1_TARGET?m._compile(bytes.toString('utf8'),f):load(m,f);\n")
  for name,target,before,after,suite,pattern,marker in FAULTS:
   if a.only and name!=a.only:continue
   dest=out/name;dest.mkdir();original=(ROOT/target).read_bytes();assert original.count(before.encode())==1,(name,'anchor')
   mutated=original.replace(before.encode(),after.encode(),1);variant=td/'variant.js'
   command=['node','--require',str(hook),'--test','--test-reporter='+str(ROOT/'tests/diagnostics/r13_n1_reporter.cjs'),'--test-name-pattern=^'+pattern,'tests/test_r13_rc_'+suite+'.js']
   env=os.environ.copy();env.update(N1_TARGET=str(ROOT/target),N1_VARIANT=str(variant))
   variant.write_bytes(original);b=run(command,env,dest/'before');assert green(b),(name,'baseline',b['events'])
   variant.write_bytes(mutated);f=run(command,env,dest/'fault');(dest/'variant.js').write_bytes(mutated)
   failures=[x for x in f['events'] if x['type']=='failure']
   variant.write_bytes(original);r=run(command,env,dest/'restored');assert green(r) and variant.read_bytes()==original and (ROOT/target).read_bytes()==original,(name,'restore')
   killed=named_kill(b,f,r,marker)
   assert killed,(name,'not named kill',failures)
   results.append(dict(name=name,target=target,before_sha256=sha(original),fault_sha256=sha(mutated),test=pattern,assertion=marker,exits=[b['exit'],f['exit'],r['exit']]))
   print(name,'0/1/0',flush=True)
 base_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 (out/'summary.json').write_text(json.dumps(dict(schema='r13-n1-source-withdrawals/1',base_sha=base_sha,mutations=results),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
