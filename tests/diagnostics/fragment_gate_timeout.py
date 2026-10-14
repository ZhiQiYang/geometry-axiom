"""Exercise the gate's actual run function with real child stdout/stderr and timeout."""
import ast, json, os, pathlib, resource, subprocess, sys, tempfile, time
if not __debug__:
    raise RuntimeError('Verification requires assertions; Python optimization mode is not supported')
source = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).with_name('run_fragment_heap_gate.py')
tree = ast.parse(source.read_text())
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('bounded','run')]
assert len(functions) == 2
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp)
    rows = []
    namespace = dict(resource=resource,subprocess=subprocess,time=time,json=json,os=os,root=out,out=out,rows=rows)
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),namespace)
    command = [sys.executable,'-c',"import sys,time;print('partial stdout',flush=True);print('partial stderr',file=sys.stderr,flush=True);time.sleep(30)"]
    try:
        namespace['run']('timeout',command,timeout=0.5)
    except RuntimeError as error:
        assert 'exited 2' in str(error)
    else:
        raise AssertionError('real timeout must fail the infrastructure gate')
    stdout, stderr = (out/'timeout.stdout').read_bytes(), (out/'timeout.stderr').read_bytes()
    print(json.dumps({'raw_stdout':stdout.decode(),'raw_stderr':stderr.decode(),'rows':rows},indent=2))
    assert stdout == b'partial stdout\n'
    assert stderr == b'partial stderr\n'
    assert rows[0]['exit'] == 2 and rows[0]['timed_out'] is True
    assert rows[0]['error'] and 'timed out' in rows[0]['error']
    assert json.loads((out/'commands.json').read_text()) == rows
    print(json.dumps(rows,indent=2))
    print('PASS: real timeout preserves both raw partial streams and reports infrastructure exit 2')
