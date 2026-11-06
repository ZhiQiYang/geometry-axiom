from pathlib import Path
import argparse,subprocess,json,importlib.util,hashlib
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--base',required=True);p.add_argument('--tip',required=True);p.add_argument('--mode',choices=['fixed','withdrawn'],required=True);a=p.parse_args()
helper=Path('/tmp/geo337-F9-nonperf-original-tools-v2-20261025/binding_guards.py');spec=importlib.util.spec_from_file_location('original_pure_metadata_binding_guard',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ancestor=subprocess.run(['git','merge-base','--is-ancestor',a.base,a.tip],cwd=a.repo,capture_output=True)
argv=['git','diff']+(['--no-renames']if a.mode=='fixed'else[])+['--name-only','-z',a.base,a.tip]
p=subprocess.run(argv,cwd=a.repo,capture_output=True);assert ancestor.returncode==p.returncode==0
paths=[v.decode()for v in p.stdout.split(b'\0')if v]
accepted=True;reason=None
try:m.validate_delta(a.tip,ancestor.returncode,paths)
except RuntimeError as e:accepted=False;reason=str(e)
print(json.dumps({'metadata_only':True,'formal_executed':False,'fixture_base':a.base,'fixture_tip':a.tip,'mode':a.mode,'argv':argv,'git_exit':p.returncode,'original_git_stdout_hex':p.stdout.hex(),'original_git_stderr_hex':p.stderr.hex(),'paths':paths,'closure_accepted':accepted,'rejection_reason':reason,'guard_helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest()},ensure_ascii=False),flush=True)
assert not accepted,'fixture-product-rename-must-be-rejected: original product leaf deletion was hidden by rename-only destination'
