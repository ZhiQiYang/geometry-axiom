import collections,hashlib,json,pathlib,re,shutil,subprocess
scratch=pathlib.Path('/tmp/geometry-198-timeouts');root=pathlib.Path('/workspace/geometry-axiom')
rows=[]
for mode in ('whole-node','isolated'):
    folder=scratch/mode
    events=[json.loads(line) for p in folder.glob('*.jsonl') for line in p.read_text().splitlines()]
    names=sorted({e['name'] for e in events if e.get('label')=='test callback'})
    for name in names:
        steps=[e for e in events if e.get('name')==name and e.get('event')=='step']
        labels=collections.defaultdict(list)
        for e in steps:labels[e['label']].append(e['ms'])
        rows.append({'mode':mode,'case':name,'steps':{k:{'count':len(v),'total_ms':sum(v),'maximum_ms':max(v)} for k,v in sorted(labels.items())},'caution':'Nested step totals overlap; Python CPU is excluded from Node cpuUsage.'})
    samples=json.loads((folder/'samples.json').read_text())
    def stat(sample):return {key:int(value) for key,value in (line.split() for line in sample['cpu_stat'].splitlines())}
    first,last=stat(samples[0]),stat(samples[-1]);receipt=json.loads((folder/'run.json').read_text())
    receipt['cgroup_cpu_delta']={k:last[k]-first[k] for k in first};receipt['maximum_observed_node_processes']=max(len(s['nodes']) for s in samples)
    receipt['caution']='Cgroup statistics include all environment tasks; observations do not enforce exclusivity or establish cause of historical timeouts.'
    (folder/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
    before=json.loads((folder/'checkout-before.json').read_text());after=json.loads((folder/'checkout-after.json').read_text())
    assert before['head']==after['head']=='7002a7b8fd186fff9f3d32c24e97df1b9a2bd78e'
    assert before['tracked_diff']==after['tracked_diff']==[]
(scratch/'case-timings.json').write_text(json.dumps(rows,indent=2)+'\n')
controls=['tests/test_reference_workspace_races.js','geometry-web/reference-workspace.js','geometry-web/project-store.js','geometry-core/rule_cases/catalog.py']
source={}
for name in controls:
    data=(root/name).read_bytes().replace(b'\r\n',b'\n');base=subprocess.check_output(['git','show',f'635dd86ee368579aec444fb3ba16e48bccf4877e:{name}'],cwd=root).replace(b'\r\n',b'\n')
    source[name]={'sha256_lf':hashlib.sha256(data).hexdigest(),'equal_exact_base_lf':data==base}
    assert data==base
(scratch/'source-controls.json').write_text(json.dumps(source,indent=2)+'\n')
print(json.dumps(rows,indent=2))
