import hashlib,json,pathlib,subprocess
root=pathlib.Path('/workspace/geometry-axiom');out=root/'tests/evidence/pf1-diagnostic-scope-20261012';sha=lambda x:hashlib.sha256(x).hexdigest()
paths=['current_geometry.c','geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c','geometry-web/panel_fill_bridge.inc','tests/test_panel_fill_finish_surface.py','tests/run_all.expected.json','tests/run_all.py','tests/mutants_results.json','公理層.md','geometry-guide/公理層-白話.md','geometry-guide/公理層-閱讀器.html','BACKLOG.md','決策佇列.md']
for p in paths:assert (root/p).read_bytes()==subprocess.check_output(['git','show','687e2c2:'+p],cwd=root)
(out/'source-binding.json').write_text(json.dumps({'tested_head':'687e2c2305b8d380ba1b179b47d723275dc0454c','product_and_judge_unchanged':True,'sources':{p:sha((root/p).read_bytes()) for p in paths}},ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'payloads':len(manifest),'git_blobs':len(manifest)+1}))
