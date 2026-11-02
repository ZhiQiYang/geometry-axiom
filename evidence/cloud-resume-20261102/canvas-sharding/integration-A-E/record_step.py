"""Record local ordinary merge commands and conflicted/dirty source bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE=Path('/tmp/geometry-canvas-shards-20261102')
ROOT=Path(__file__).resolve().parent
label,*command=sys.argv[1:]
if command and command[0]=='--':command=command[1:]
OUT=ROOT/label
OUT.mkdir(exist_ok=False)
def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE)
def snapshot(name):
 head=git('rev-parse','HEAD').decode().strip()
 status=git('status','--porcelain=v1');(OUT/(name+'.status')).write_bytes(status)
 unmerged=git('ls-files','-u');(OUT/(name+'.unmerged')).write_bytes(unmerged)
 dirty=git('diff','--name-only','-z','HEAD').decode().split('\0')
 rows=[]
 for relative in sorted(set(x for x in dirty if x)):
  path=SOURCE/relative
  row={'path':relative,'present':path.is_file()}
  if path.is_file() and not relative.startswith('evidence/'):
   raw=path.read_bytes();target=OUT/name/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
   row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),copy=str(target))
  rows.append(row)
 return {'head':head,'commit':git('show','-s','--format=%H %P %T',head).decode().strip(),
         'status_sha256':hashlib.sha256(status).hexdigest(),'unmerged_stage_bytes_sha256':hashlib.sha256(unmerged).hexdigest(),'dirty':rows}
receipt={'label':label,'command':command,'cwd':str(SOURCE),'before':snapshot('before')}
process=subprocess.run(command,cwd=SOURCE,capture_output=True)
(OUT/'stdout').write_bytes(process.stdout);(OUT/'stderr').write_bytes(process.stderr)
receipt.update(exit_code=process.returncode,stdout_sha256=hashlib.sha256(process.stdout).hexdigest(),stderr_sha256=hashlib.sha256(process.stderr).hexdigest(),after=snapshot('after'))
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(process.stdout.decode(errors='replace'),end='');print(process.stderr.decode(errors='replace'),end='',file=sys.stderr)
print('recorded',OUT/'receipt.json','exit',process.returncode)
raise SystemExit(process.returncode)
