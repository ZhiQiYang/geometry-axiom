import hashlib,json,pathlib,sys
out=pathlib.Path('/workspace/geometry-axiom/tests/evidence/pf1-capacity-review-20261012')
if len(sys.argv)==3 and sys.argv[1]=='--decode':
 destination=pathlib.Path(sys.argv[2])
 for p in out.rglob('*.raw.json'):
  j=json.loads(p.read_text());data=j['raw'].encode('utf-8');assert len(data)==j['bytes'] and hashlib.sha256(data).hexdigest()==j['sha256']
  target=destination/p.relative_to(out).with_name(j['original_filename']);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 print(json.dumps({'decoded_to':str(destination)}));sys.exit(0)
changed=[]
for p in list(out.rglob('*')):
 if not p.is_file() or p.suffix not in ('.stdout','.stderr'):continue
 data=p.read_bytes()
 if not any(line.endswith((b' ',b'\t',b'\r')) for line in data.split(b'\n')):continue
 j={'original_filename':p.name,'encoding':'utf-8','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'raw':data.decode('utf-8')}
 target=p.with_name(p.name+'.raw.json');target.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');assert json.loads(target.read_text())['raw'].encode('utf-8')==data
 p.unlink();changed.append(str(target.relative_to(out)))
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'encoded_files':changed,'payloads':len(manifest)}))
