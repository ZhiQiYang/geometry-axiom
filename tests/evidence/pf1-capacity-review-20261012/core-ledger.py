import concurrent.futures,json,os,pathlib,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-tests/pr190-capacity')
sys.path.insert(0,str(root/'tests'));import mutate
ids=[m['id'] for m in mutate.MUTANTS]
def job(label,selected):
 path=out/(label+'-ledger.json');env=os.environ.copy();env['MUTATE_RESULTS']=str(path)
 with (out/(label+'.stdout')).open('wb') as a,(out/(label+'.stderr')).open('wb') as b:
  p=subprocess.run([sys.executable,str(root/'tests/mutate.py'),*selected],cwd=root,env=env,stdout=a,stderr=b)
 (out/(label+'-receipt.json')).write_text(json.dumps({'ids':selected,'returncode':p.returncode,'origin':'subprocess.run'},indent=2)+'\n')
 assert p.returncode==0,(label,p.returncode)
 records=mutate.load_records(path);return {k:records[k] for k in selected}
records=job('core-warm',['M01'])
others=[i for i in ids if i!='M01']
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for r in pool.map(lambda pair:job(*pair),[(f'core-{i}',others[i::5]) for i in range(5)]):records.update(r)
assert set(records)==set(ids)
mutate.save_records(root/'tests/mutants_results.json',records)
print(json.dumps({'records':len(records),'verdicts':{v:sum(r['verdict']==v for r in records.values()) for v in set(r['verdict'] for r in records.values())}}))
