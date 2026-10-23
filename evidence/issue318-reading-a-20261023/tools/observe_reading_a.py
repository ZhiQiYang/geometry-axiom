"""Small observation only; run after root releases a non-canvas slot."""
import argparse,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
root=args.root.resolve();oracle=root/'geometry-core/framing-template/oracle';sys.path.insert(0,str(oracle))
import framing_oracle as fo
spec=json.loads((oracle/'rooms.json').read_text());p=spec['params']
rooms={
 'FZ120':{'outer':[[0,0],[4100,0],[4100,3672],[1450,3672],[1450,3720],[1000,3720],[1000,3675],[0,3675]]},
 'FZ107':{'outer':[[0,0],[4100,0],[4100,3711],[3650,3711],[3650,3700],[0,3700]]},
 'STEP20':{'outer':[[0,0],[4100,0],[4100,3680],[2600,3680],[2600,3700],[0,3700]]},
}
# Read a literal room from selftest without executing any selftest body.
import ast
tree=ast.parse((oracle/'selftest.py').read_text())
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('FZ107','FZ114') for t in node.targets):
  rooms[node.targets[0].id]=ast.literal_eval(node.value)
layouts={fo.layout_name(x):x for x in fo.LAYOUTS}
started=time.monotonic();rows=[]
for name,layout in [('FZ120','左上起鋪,板長沿Y'),('FZ120','左下起鋪,板長沿Y'),('FZ107','左上起鋪,板長沿Y'),('FZ114','右上起鋪,板長沿Y'),('FZ114','左上起鋪,板長沿X'),('STEP20','左上起鋪,板長沿Y')]:
 for policy in (('current','withdrawn') if name=='FZ120' else ('current',)):
  old_build,old_check=fo._reading_a_build_end,fo.reading_a_end_admission
  if policy=='withdrawn':
   fo._reading_a_build_end=lambda *a:fo.READING_A_ORDINARY;fo.reading_a_end_admission=lambda *a:fo.READING_A_ORDINARY
  try:
   r=fo.build(rooms[name],layouts[layout],p);v,problems=fo.verdict(r,p)
   rows.append({'room':name,'layout':layout,'policy':policy,'verdict':v,'problems':problems,'conflicts':r['conflicts'],'core_limits':r['core_limits'],'seams_a':r['seams_a'],'seams_b':r['seams_b'],'p182':r.get('p182'),'timbers':r['timbers']})
  finally:fo._reading_a_build_end,fo.reading_a_end_admission=old_build,old_check
result={'scope':'Observation; not golden generation or formal acceptance','command':sys.argv,'sha':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'dirty':subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True),'source_hashes':{name:hashlib.sha256((oracle/name).read_bytes()).hexdigest() for name in ('framing_oracle.py','selftest.py','make_golden.py')},'elapsed_seconds':time.monotonic()-started,'rows':rows}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'elapsed_seconds':result['elapsed_seconds'],'rows':[{k:r[k] for k in ('room','layout','policy','verdict','core_limits','seams_a','seams_b')} for r in rows]},ensure_ascii=False,indent=2))
