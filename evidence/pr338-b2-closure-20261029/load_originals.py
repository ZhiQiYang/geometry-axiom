import hashlib,io,json,pathlib,subprocess,tarfile
root=pathlib.Path('/tmp/pr338-b2-closure');repo='/tmp/r02-ui1';M='0ae1728c2309e1d670369289a6b8da059fa63a50';base='evidence/geo337-train-20261024/'
paths=['full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz']+[f'F9-geo323-ABC-comparison-public/archives/PUBLIC_COMPARISON_PART{i}.tar.gz' for i in range(1,6)]
records=[]
for rel in paths:
    path=base+rel;dst=root/pathlib.Path(path).name
    if not dst.exists():dst.write_bytes(subprocess.check_output(['git','-C',repo,'show',M+':'+path]))
    with tarfile.open(dst,'r:gz') as t:
        members=[{'name':m.name,'bytes':m.size,'kind':'file' if m.isfile() else 'other'} for m in t.getmembers()]
    (root/(dst.name+'.members.json')).write_text(json.dumps(members,indent=2)+'\n')
    row={'commit':M,'path':path,'local':str(dst),'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'members':len(members)};records.append(row)
(root/'archive-bindings.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
