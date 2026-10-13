import pathlib, shutil
root=pathlib.Path('/workspace/scratch/860de1a99063/geometry-axiom')
bad=pathlib.Path('/tmp/geometry217-opt-bad-fixed')
shutil.copytree(root,bad,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','__pycache__'))
inc=bad/'geometry-core/subgrid_rebind.inc'
inc.write_bytes(pathlib.Path('/tmp/geometry211-fixed-subgrid_rebind.inc').read_bytes())
p=bad/'current_geometry.c'
s=p.read_bytes().replace(b'int k=reference_fragment_candidate',b'bool k=reference_fragment_candidate').replace(b'int n=reference_fragment_candidate',b'bool n=reference_fragment_candidate').replace(b'if (k<0 || n<0 || (!k && !n)) return false;',b'if (!k && !n) return false;')
p.write_bytes(s)
old=pathlib.Path('/tmp/geometry217-opt-bad-before')
shutil.copytree(bad,old,dirs_exist_ok=True)
for name in ('fragment_oom.py','reference_fragment_stack.py','fragment_gate_timeout.py'):
 p=old/'tests/diagnostics'/name
 s=p.read_text().replace("if not __debug__:\n    raise RuntimeError('Verification requires assertions; Python optimization mode is not supported')\n",'')
 p.write_text(s)
p=old/'tests/diagnostics/run_fragment_heap_gate.py'
s=p.read_text().replace("    child_env = dict(os.environ)\n    child_env.pop('PYTHONOPTIMIZE', None)\n",'').replace(', env=child_env','')
p.write_text(s)
