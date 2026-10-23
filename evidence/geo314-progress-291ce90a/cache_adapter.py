#!/usr/bin/env python3
"""Diagnostic environment path adapter. Only binaries.OUT_DIR is configured."""
import argparse,datetime,hashlib,importlib.util,json,pathlib,sys
p=argparse.ArgumentParser();p.add_argument('--source-root',required=True,type=pathlib.Path);p.add_argument('--out-dir',required=True,type=pathlib.Path);p.add_argument('--receipt',required=True,type=pathlib.Path);a=p.parse_args()
root=a.source_root.resolve();target=a.out_dir.resolve();tool=root/'tests/binaries.py'
spec=importlib.util.spec_from_file_location('geo314_official_binaries',tool);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
b=m.BY_NAME['bridge'];before={'OUT_DIR':str(m.OUT_DIR),'binary_path':str(b.path),'command':b.command_string(),'fingerprint':m.compute_fingerprint(b)[0],'posix_flags':list(b.posix_flags),'smoke':b.smoke}
m.OUT_DIR=target
after={'OUT_DIR':str(m.OUT_DIR),'binary_path':str(b.path),'command':b.command_string(),'fingerprint':m.compute_fingerprint(b)[0],'posix_flags':list(b.posix_flags),'smoke':b.smoke}
assert all(before[k]==after[k] for k in ['command','fingerprint','posix_flags','smoke'])
row={'schema':'geo314-private-binaries-outdir-adapter/1','scope':'Only output paths change. Original compiler flags, smoke, fingerprint and judges remain unchanged.','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':sys.argv,'adapter_sha256':sha(pathlib.Path(__file__)),'official_tool':str(tool),'official_tool_sha256':sha(tool),'before':before,'after':after,'official_call':['main',['build','bridge']]}
code=m.main(['build','bridge']);row['exit_code']=code
info=m.inspect_one(b,path=b.path);row['official_explicit_inspection']={'state':info.state,'reason':info.reason,'path':str(info.path),'fingerprint':info.fingerprint}
if b.path.exists():row['binary_sha256']=sha(b.path)
if b.sidecar.exists():row['sidecar_sha256']=sha(b.sidecar);row['official_sidecar']=json.loads(b.sidecar.read_text())
row['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();row['official_tool_after_sha256']=sha(tool)
a.receipt.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
if row['official_tool_after_sha256']!=row['official_tool_sha256'] or info.state!='fresh':sys.exit(code or 1)
sys.exit(code)
