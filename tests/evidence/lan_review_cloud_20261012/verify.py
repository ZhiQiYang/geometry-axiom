import hashlib,json,pathlib,subprocess
root=pathlib.Path('/workspace/geometry-axiom');out=root/'tests/evidence/lan_review_cloud_20261012';sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((out/'manifest.json').read_text());binding=json.loads((out/'source-binding.json').read_text())
for n,v in manifest.items():
 raw=(out/n).read_bytes();assert len(raw)==v['bytes'] and sha(raw)==v['sha256'],n
for n,v in binding['sources'].items():
 raw=(root/n).read_bytes();assert sha(raw)==v,n
 if n not in ('tests/test_lan_review.py','tests/run_all.py'):assert raw==subprocess.check_output(['git','show','5d7b044:'+n],cwd=root),n
diffnames=subprocess.check_output(['git','diff','--name-only','5d7b044'],cwd=root,text=True).splitlines()
assert all(n in ('tests/test_lan_review.py','tests/run_all.py') or n.startswith('tests/evidence/lan_review_cloud_20261012/') for n in diffnames)
closure=json.loads((out/'receipts/M23-source-closure.json').read_text());assert len(closure)==436
for n,v in closure.items():assert sha((root/n).read_bytes())==v,n
def receipt(label):return json.loads((out/f'receipts/{label}.receipt.json').read_text())
assert receipt('full-baseline')['returncode']==0 and receipt('restored-socket')['returncode']==0
assert receipt('after-socket-mutant')['returncode']==1
assert receipt('partial-old-policy-venv')['returncode']==3 and receipt('partial-restored-policy-venv')['returncode']==0
for label,fail,errors in [('before-socket-closure',0,3),('after-socket-mutant',3,0),('restored-socket',0,0)]:
 p=out/f'receipts/{label}.stdout.raw.json';stdout=json.loads(p.read_text())['raw'];result=json.loads(stdout.splitlines()[-1]);assert result['tests']==3 and result['failures']==fail and result['errors']==errors and result['skips']==0
 if fail:assert all(e['type']=='AssertionError' and 'refused late body was not drained after the response' in e['message'] for e in result['events'])
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if head!='5d7b044beb43f34e01bb56bf3cde70484aee377d':
 pr=json.loads(subprocess.check_output(['gh','api','repos/ZhiQiYang/geometry-axiom/pulls/194'],cwd=root));assert pr['head']['sha']==head and pr['draft'] and pr['state']=='open'
 tree=json.loads(subprocess.check_output(['gh','api',f'repos/ZhiQiYang/geometry-axiom/git/trees/{head}?recursive=1'],cwd=root));assert not tree['truncated'];blobs={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
 for p in out.rglob('*'):
  if p.is_file():
   raw=p.read_bytes();assert blobs[str(p.relative_to(root))]==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),str(p)
 assert subprocess.check_output(['git','status','--porcelain'],cwd=root)==b''
print(json.dumps({'head':head,'payloads':len(manifest),'blobs':len(manifest)+1,'runtime_closure':len(closure),'protected_unchanged':True,'remote_verified':head!='5d7b044beb43f34e01bb56bf3cde70484aee377d'}))
