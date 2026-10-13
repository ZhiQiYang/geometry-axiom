import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom')
out=pathlib.Path('/tmp/geometry-tests/pr190-capacity');out.mkdir(parents=True,exist_ok=True)
label=sys.argv[1];argv=sys.argv[2:]
start=time.time()
with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
    p=subprocess.run(argv,cwd=root,stdout=stdout,stderr=stderr)
receipt={'argv':argv,'cwd':str(root),'returncode':p.returncode,'duration_seconds':time.time()-start,'origin':'subprocess.run',
 'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('current_geometry.c','geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c','tests/test_panel_fill_finish_surface.py')}}
(out/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
sys.exit(p.returncode)
