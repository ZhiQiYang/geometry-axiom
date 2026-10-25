"""Read an exact Git blob and report its byte identity without duplicate payload logs."""
import argparse, hashlib, json, subprocess, sys
parser=argparse.ArgumentParser()
parser.add_argument('--repo',required=True)
parser.add_argument('--spec',required=True)
a=parser.parse_args()
argv=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',a.repo,'cat-file','blob',a.spec]
p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
if p.stderr:sys.stderr.buffer.write(p.stderr)
if p.returncode:
    sys.stdout.buffer.write(p.stdout)
    sys.exit(p.returncode)
raw=p.stdout
print(json.dumps({'command':argv,'actual_exit':p.returncode,'spec':a.spec,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_oid':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'scope':'Complete Git blob read; stdout reports identity. Internal payload pipe is not claimed as a separate original receipt.'}))
