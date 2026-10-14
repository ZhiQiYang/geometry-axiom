import pathlib, resource, subprocess, time, json
root=pathlib.Path('/workspace/scratch/860de1a99063/geometry-axiom')
out=pathlib.Path('/tmp/geometry211-bridge-evidence');out.mkdir(exist_ok=True)
rows=[]
for limit in (8192,16384):
 for scene in ('_ax_r13_anchor_follows.scene','_ax_r10_hole_follows_piece.scene','_ax_r17_wall_column_face.scene'):
  def bounds():resource.setrlimit(resource.RLIMIT_STACK,(limit*1024,resource.RLIM_INFINITY))
  commands='loadfile '+str(root/scene)+'\ndump\n'
  t=time.monotonic();p=subprocess.run(['/tmp/geometry211-bridge'],input=commands.encode(),cwd=root,capture_output=True,preexec_fn=bounds,timeout=30)
  name=str(limit)+'-'+scene
  (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
  rows.append(dict(stack_kib=limit,scene=scene,commands=commands,exit=p.returncode,seconds=time.monotonic()-t,stdout_bytes=len(p.stdout),stderr_bytes=len(p.stderr)))
(out/'receipt.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
