import hashlib,json,pathlib,subprocess
root=pathlib.Path('/workspace/geometry-axiom');out=root/'tests/evidence/pf1-capacity-review-20261012'
manifest=json.loads((out/'manifest.json').read_text());binding=json.loads((out/'source-binding.json').read_text())
for n,v in manifest.items():
 data=(out/n).read_bytes();assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],n
for n,sha in binding['final_sources'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==sha,n
changed=subprocess.check_output(['git','diff','--name-only','26a7c443b9bd10ae036b0956bd99233f594b5395'],cwd=root,text=True).splitlines()
allowed={'geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c','tests/test_panel_fill_finish_surface.py','tests/run_all.expected.json','tests/mutants_results.json','geometry-web/docs/PANEL-FILL-NATIVE-VALIDATION.md'}
assert all(n in allowed or n.startswith('tests/evidence/pf1-capacity-review-20261012/') for n in changed),changed
ledger=json.loads((root/'tests/mutants_results.json').read_text());assert len(ledger)==48
assert {v:sum(r['verdict']==v for r in ledger.values()) for v in ('killed','crashed','equivalent','retired')}=={'killed':40,'crashed':1,'equivalent':4,'retired':3}
assert all(r['execution']['compile_exit_code']==0 and r['execution']['baseline']['exit_code']==0 and r['execution']['baseline']['result']['counts']=={'pass':139,'fail':0,'infrastructure':0} for r in ledger.values() if r['verdict']!='retired')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def gh(*args):return json.loads(subprocess.check_output(['gh',*args],cwd=root))
pr=gh('api','repos/ZhiQiYang/geometry-axiom/pulls/190')
if head!='26a7c443b9bd10ae036b0956bd99233f594b5395':
 assert pr['head']['sha']==head and pr['state']=='open' and pr['draft'] and pr['head']['ref']=='feat/pf1-finish-surface-20261011'
 tree=gh('api',f'repos/ZhiQiYang/geometry-axiom/git/trees/{head}?recursive=1');assert not tree['truncated'];blobs={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
 for p in out.rglob('*'):
  if p.is_file():
   data=p.read_bytes();expected=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blobs[str(p.relative_to(root))]==expected,str(p)
 assert subprocess.check_output(['git','status','--porcelain'],cwd=root)==b''
print(json.dumps({'head':head,'payloads':len(manifest),'manifest_blobs':len(manifest)+1,'source_binding':True,'protected_unchanged':True,'core_ledger':True,'remote_verified':head!='26a7c443b9bd10ae036b0956bd99233f594b5395'}))
