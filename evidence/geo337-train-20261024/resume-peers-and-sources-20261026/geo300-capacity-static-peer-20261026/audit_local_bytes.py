"""Independent local-capture audit. No Git, API, imports from source, or tests."""
from pathlib import Path
import ast,hashlib,json,difflib
BASE=Path('/tmp/geo300-capacity-static-20261026')
OUT=Path(__file__).parent
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
CAPACITY='9a8584f57be7935604c3bad4c2481945a6ec3d9f'
def H(b):return hashlib.sha256(b).hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def raw(tag):return (BASE/tag/'stdout.bin').read_bytes()
def metadata(tag):return json.loads((BASE/tag/'RESULT.json').read_bytes())
manifest=json.loads((BASE/'MANIFEST.json').read_bytes())
manifest_rows=[]
for row in manifest['files']:
 name=row['path'];path=Path(name)
 need(not path.is_absolute()and '..'not in path.parts,'manifest relative path')
 p=BASE/path;b=p.read_bytes();need(len(b)==row['bytes']and H(b)==row['sha256'],'manifest byte mismatch '+name)
 manifest_rows.append({'path':name,'bytes':len(b),'sha256':H(b)})
captures=[]
for p in sorted(BASE.glob('*/RESULT.json')):
 q=json.loads(p.read_bytes())
 if all(x in q for x in ['command','stdout_bytes','stdout_sha256','stderr_bytes','stderr_sha256']):
  for stream in ['stdout','stderr']:
   b=p.with_name(stream+'.bin').read_bytes();need(len(b)==q[stream+'_bytes']and H(b)==q[stream+'_sha256'],'capture '+str(p)+' '+stream)
  captures.append({'path':str(p.relative_to(BASE)),'exit_code':q['exit_code'],'command':q['command']})
def constant_set(tag,names):
 found={}
 for n in ast.parse(raw(tag)).body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name)and t.id in names:
     need(t.id not in found,'duplicate constant');found[t.id]=ast.literal_eval(n.value)
 need(set(found)==set(names),'all original literal constants');return found
source_constants=constant_set('source-index-tests',{'EDGE_PROBE_REUSE_EDITS','PROVIDER_HINT_EDIT'})
contact_constants=constant_set('wood-contact-tests',{'MONOTONIC_SORT_BLOCK','PLANE_RANGE_EDITS'})
def reverse_many(data,edits,steps):
 for old,new in reversed(edits):
  old=old.encode();new=new.encode();need(new and data.count(new)==1,'one exact new edit occurrence')
  position=data.index(new);changed=data[:position]+old+data[position+len(new):]
  need(changed!=data,'real byte change')
  steps.append({'before_sha256':H(data),'after_sha256':H(changed),'removed_bytes':len(new),'inserted_bytes':len(old),'offset':position})
  data=changed
 return data
def reconstruct(kind,omit=None):
 steps=[]
 if kind=='kernel':
  b=raw('kernel-source')
  if omit!='PROVIDER_HINT_EDIT':b=reverse_many(b,[source_constants['PROVIDER_HINT_EDIT']],steps)
  if omit!='EDGE_PROBE_REUSE_EDITS':b=reverse_many(b,source_constants['EDGE_PROBE_REUSE_EDITS'],steps)
 else:
  b=raw('contact-world')
  if omit!='MONOTONIC_SORT_BLOCK':
   block=contact_constants['MONOTONIC_SORT_BLOCK'].encode();need(b.count(block)==1,'exact monotonic block')
   pos=b.index(block);b=b[:pos]+b[pos+len(block):];steps.append({'removed_monotonic_bytes':len(block),'offset':pos,'after_sha256':H(b)})
  if omit!='PLANE_RANGE_EDITS':b=reverse_many(b,contact_constants['PLANE_RANGE_EDITS'],steps)
 return b,steps
scopes=[('kernel','kernel-source','pr348-source','geometry-core/kernel/source.c',['EDGE_PROBE_REUSE_EDITS','PROVIDER_HINT_EDIT']),('contact','contact-world','pr348-contact','geometry-templates/woodworking/native/contact_world.c',['MONOTONIC_SORT_BLOCK','PLANE_RANGE_EDITS'])]
results=[]
for kind,newtag,oldtag,path,groups in scopes:
 new=raw(newtag);old=raw(oldtag)
 need(metadata(newtag)['command']==['git','show',F+':'+path],'full F command identity')
 command=metadata(oldtag)['command'];need(command[-1]=='repos/ZhiQiYang/geometry-axiom/contents/'+path+'?ref='+CAPACITY and 'Accept: application/vnd.github.raw+json'in command,'full capacity raw API identity')
 need(metadata(newtag)['exit_code']==metadata(oldtag)['exit_code']==0,'actual completed captures')
 restored,steps=reconstruct(kind);need(restored==old,'byte exact reverse full file '+path)
 controls=[]
 for group in groups:
  partial,_=reconstruct(kind,omit=group);need(partial!=old,'every missing group necessary '+group)
  controls.append({'group_not_reversed':group,'equals_capacity':False,'sha256':H(partial)})
 expected_diff=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=CAPACITY+'/'+oldtag,tofile=F+'/'+newtag)).encode()
 need((BASE/(oldtag+'-to-F.diff')).read_bytes()==expected_diff,'complete published textual diff')
 results.append({'path':path,'F':{'sha':F,'bytes':len(new),'sha256':H(new)},'capacity':{'sha':CAPACITY,'bytes':len(old),'sha256':H(old)},'all_reverse_steps':steps,'complete_reverse_is_byte_equal':True,'independent_group_necessity_controls':controls,'formal_runtime':False})
for tag,path in [('source-index-tests','tests/test_geo261_source_index.py'),('wood-contact-tests','tests/test_geo261_wood_contact_world.py')]:
 need(metadata(tag)['exit_code']==0 and metadata(tag)['command']==['git','show',F+':'+path],'test literal constants exact full F identity')
pr=json.loads(raw('pr348'));need(pr['head']['sha']==CAPACITY and pr['number']==348,'captured PR full head')
history={}
for tag,sha in [('edge-reuse-history','9430bae568feb98805072930c92f9a03a1250d4e'),('hint-history','81b6c388f8b73e9aaf885b1d948e5f306b77bafd'),('monotonic-history','aa16e73d6e1f2965e0a911581e2a545aaaf66870'),('plane-range-history','7c4a40a71fe46242c302efaa85f1a4d13df0c19a')]:
 m=metadata(tag);need(m['exit_code']==0 and m['command'][:2]==['git','log']and F in m['command'],'captured history at fullF')
 rows=raw(tag).decode().splitlines();need(len(rows)==1 and rows[0].split()[0]==sha,'one full source-history SHA')
 history[tag]={'sha':sha,'capture_sha256':H(raw(tag)),'claim_limit':'fixed-F git log -S snapshot; not a complete commit diff or whole branch containment proof'}
analysis=json.loads((BASE/'ANALYSIS.json').read_bytes());need(analysis['analyzed_source_sha']==F and analysis['capacity_head']==CAPACITY and analysis['exit_code']==0,'analysis full SHA')
for observed,claimed in zip(results,analysis['missing_existing_optimizations']):
 need(observed['path']==claimed['path']and observed['F']['sha256']==claimed['current_sha256']and observed['capacity']['sha256']==claimed['capacity_sha256']and claimed['exact_reversal_matches_capacity']is True,'analysis source equality matches independent calculation')
terminal=json.loads((BASE/'ANALYSIS_EXEC_FINAL.json').read_bytes());need(terminal['exit_code']==0 and json.loads(terminal['output'])==analysis,'saved analysis terminal output exact JSON')
result={'schema':'geo300-independent-local-byte-audit/1','exit_code':0,'formal_tests_executed':False,'git_or_api_executed':False,'source_or_original_evidence_written':False,'source_sha':F,'capacity_head':CAPACITY,'manifest_sha256':H((BASE/'MANIFEST.json').read_bytes()),'manifest_files_checked':len(manifest_rows),'capture_stream_pairs_checked':len(captures),'reversals':results,'history_captures':history,'source_inputs':{name:{'bytes':(BASE/name).stat().st_size,'sha256':H((BASE/name).read_bytes())}for name in ['REPORT.md','ANALYSIS.json','ANALYSIS_EXEC_FINAL.json']},'limitations':['exact byte equality covers only the two named C files and the four explicitly reversed groups','No C compilation, test runtime, fixture generator runtime, capacity performance, or causal timeout diagnosis','git log -S provides captured full origin SHAs, not unrecorded full commit deltas']}
(OUT/'BYTE_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'exit_code':0,'manifest_files_checked':len(manifest_rows),'capture_stream_pairs_checked':len(captures),'both_files_byte_equal':True}))
