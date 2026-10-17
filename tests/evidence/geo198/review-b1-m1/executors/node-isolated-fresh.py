import json,pathlib,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'));import binaries,run_all
env=run_all.child_env(binaries.inspect_all(),[])
argv=['node','--test','--test-reporter=spec','tests/test_reference_workspace_races.js']
print(json.dumps({'argv':argv,'cwd':str(root),'geometry_environment':{k:v for k,v in env.items() if k.startswith('GEOMETRY_')}},indent=2),flush=True)
p=subprocess.run(argv,cwd=root,env=env)
print('Isolated original file returncode:',p.returncode,flush=True);sys.exit(p.returncode)
