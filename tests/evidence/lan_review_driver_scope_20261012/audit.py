import hashlib,json,pathlib,subprocess
root=pathlib.Path('/workspace/geometry-axiom');folder=root/'tests/evidence/lan_review_cloud_20261012';sha=lambda b:hashlib.sha256(b).hexdigest()
old=json.loads(subprocess.check_output(['git','show','ee8dd5c:tests/evidence/lan_review_cloud_20261012/manifest.json'],cwd=root));current=json.loads((folder/'manifest.json').read_text())
assert set(old)==set(current) and len(old)==75
changed=[n for n in old if old[n]!=current[n]];assert changed==['README.md'],changed
for n,v in current.items():
 data=(folder/n).read_bytes();assert len(data)==v['bytes'] and sha(data)==v['sha256'],n
 if n!='README.md':assert v==old[n]
receipt=json.loads((folder/'receipts/partial-old-policy.receipt.json').read_text());suite=json.loads((folder/'receipts/partial-old-policy/py_test_lan_review.json').read_text())
assert receipt['returncode']==0 and {k:suite[k] for k in ('total','passed','failed','skipped')}=={'total':21,'passed':21,'failed':0,'skipped':0}
binding=json.loads((folder/'source-binding.json').read_text())
for n,h in binding['sources'].items():assert sha((root/n).read_bytes())==h and (root/n).read_bytes()==subprocess.check_output(['git','show','ee8dd5c:'+n],cwd=root),n
text=(folder/'README.md').read_text();assert '已交付的只是該子程序 stdout／stderr、receipt 與 suite logs' in text and '當時外層 driver 的原 stdout／stderr、實際退出碼及原文未附' in text
print(json.dumps({'baseline':'ee8dd5cd9db07409e5c9c0dce4a509d803018840','manifest_payloads':75,'unchanged_payloads':74,'updated_payload':'README.md','child_exit':receipt['returncode'],'child_suite':{k:suite[k] for k in ('total','passed','failed','skipped')},'outer_driver_original_delivered':False,'later_venv_not_substituted':True,'product_and_judge_sources_unchanged':len(binding['sources'])},ensure_ascii=False,indent=2))
