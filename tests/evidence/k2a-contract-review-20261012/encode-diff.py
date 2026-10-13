import hashlib,json,pathlib,shutil
out=pathlib.Path('tests/evidence/k2a-contract-review-20261012');p=out/'contract.diff';data=p.read_bytes()
# Preserve raw Git context-line spaces inside JSON; checking the patch as source text flags those context lines.
(out/'contract.diff.json').write_text(json.dumps({'encoding':'utf-8','sha256':hashlib.sha256(data).hexdigest(),'diff':data.decode('utf-8')},ensure_ascii=False,indent=2)+'\n')
p.unlink()
r=out/'receipt.json';value=json.loads(r.read_text());value['contract_diff_sha256']=hashlib.sha256(data).hexdigest()
value['packaging']='Raw git diff retained losslessly as a JSON string; context-only blank-line spaces no longer trigger source whitespace checks'
r.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
p=out/'README.md';p.write_text(p.read_text().replace('contract.diff 給精確修文','contract.diff.json 的 diff 字串保存未改寫的原 git diff，附原 SHA-256，給精確修文'))
shutil.copyfile(__file__,out/'encode-diff.py')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS')
(out/'SHA256SUMS').write_text(manifest)
