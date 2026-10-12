import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-tests/pr194-review');out.mkdir(parents=True,exist_ok=True)
label=sys.argv[1];argv=sys.argv[2:];names=['tests/test_lan_review.py','tests/run_all.py','tests/_unittest_runner.py','geometry-web/serve.py','geometry-web/lan_guard.py','geometry-web/lan_tls.py','tests/evidence/lan_review_mutants.json']
before={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names};head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();started=time.time()
with (out/(label+'.stdout')).open('wb') as a,(out/(label+'.stderr')).open('wb') as b:p=subprocess.run(argv,cwd=root,stdout=a,stderr=b)
after={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
r={'argv':argv,'cwd':str(root),'head_at_start':head,'returncode':p.returncode,'origin':'subprocess.run','seconds':time.time()-started,'sources_before':before,'sources_after':after,'sources_unchanged':before==after}
(out/(label+'.receipt.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(p.returncode)
