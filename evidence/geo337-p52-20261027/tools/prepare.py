from pathlib import Path
import hashlib,json,os,shutil,socket,subprocess,sys
TOOLS=Path(__file__).parent
ROOT=Path('/workspace/geo337-p52-sources-20261027')
SOURCE=Path('/workspace/geometry-axiom')
SHAS={'fix':'cbf0fb621888596aa14ad5f2349b503e23b1b72d','main':'adbaebf9c73ea6801d7b4d5214e4b846b132923b'}
assert not ROOT.exists();ROOT.mkdir()
rows=[]
def run(argv,cwd=SOURCE):
 p=subprocess.run(argv,cwd=cwd,capture_output=True)
 rows.append({'argv':list(map(str,argv)),'cwd':str(cwd),'exit':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
 (TOOLS/'PREPARATION_COMMANDS.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert p.returncode==0,rows[-1]
 return p.stdout
for label,sha in SHAS.items():
 dest=ROOT/label
 run(['git','clone','--shared','--no-checkout',str(SOURCE),str(dest)])
 run(['git','config','core.autocrlf','false'],dest)
 run(['git','config','core.sparseCheckout','true'],dest)
 run(['git','config','core.sparseCheckoutCone','false'],dest)
 (dest/'.git/info/sparse-checkout').write_text('/*\n!/evidence/\n!/tests/evidence/\n!/tests/release-evidence/\n')
 run(['git','-c','advice.detachedHead=false','checkout','--detach',sha],dest)
 assert run(['git','rev-parse','HEAD'],dest).decode().strip()==sha
 assert run(['git','status','--porcelain','--untracked-files=all'],dest)==b''
for name,dest,wanted in [('capture.py',Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py'),'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'),('reap_children.py',Path('/workspace/geo261-environment/reap_children.py'),'7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760')]:
 data=(TOOLS/name).read_bytes();assert hashlib.sha256(data).hexdigest()==wanted
 assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
chrome=Path('/workspace/geo261-environment/bin/google-chrome');assert not chrome.exists();chrome.parent.mkdir(parents=True,exist_ok=True);chrome.symlink_to('/usr/bin/chromium')
for port in list(range(18960,18969))+list(range(9400,9409)):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
assert Path('/tmp/geo337-native-owner.lock').is_file()
sys.dont_write_bytecode=True;sys.path.insert(0,str(TOOLS/'special/p52'))
from runtime_inventory import complete_runtime_inventory
inventories={}
for label,sha in SHAS.items():
 repo=ROOT/label
 inventory=complete_runtime_inventory(repo,sha,lambda *args:run(['git',*args],repo))
 (TOOLS/(label+'-runtime-preflight.json')).write_text(json.dumps(inventory,indent=2)+'\n')
 inventories[label]={'sha':sha,'source_files':inventory['actual_count'],'source_version':inventory['source_version']}
result={'source_checkouts':inventories,'sparse_exclusions':['evidence','tests/evidence','tests/release-evidence'],'sparse_policy':'Only outside-runtime evidence omitted; the original complete_runtime_inventory independently verified the full tracked RuntimeSnapshot input set.','objects':'Independent git directories, read-only alternate object access to existing source repository; product files are separate checkout files.','chrome_alias':{'path':str(chrome),'target':str(chrome.resolve()),'version':run([str(chrome),'--version']).decode().strip()},'ports_available':list(range(18960,18969))+list(range(9400,9409)),'free_before_launch':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']}}
(TOOLS/'PREPARATION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
