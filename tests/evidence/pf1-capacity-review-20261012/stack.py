import json,pathlib,resource,subprocess,sys
out=pathlib.Path('/tmp/geometry-tests/pr190-capacity')
before=resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,before[1]))
after=resource.getrlimit(resource.RLIMIT_STACK)
p=subprocess.run(sys.argv[2:])
(out/(sys.argv[1]+'.stack.json')).write_text(json.dumps({'original_stack_bytes':before,'test_stack_bytes':after,'argv':sys.argv[2:],'returncode':p.returncode,'origin':'subprocess.run','judge_changed':False},indent=2)+'\n')
sys.exit(p.returncode)
