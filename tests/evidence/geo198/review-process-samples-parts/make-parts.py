import base64,gzip,hashlib,json,pathlib,shutil,subprocess,sys,time
root=pathlib.Path.cwd();source=root/'tests/evidence/geo198/review-local-corner/aggregate/process-samples.json'
out=root/'tests/evidence/geo198/review-process-samples-parts';assert not out.exists();out.mkdir()
original=source.read_bytes();source_hash=hashlib.sha256(original).hexdigest()
assert source_hash=='4ed88f6448a80cadbdc3a97c9204468d7b3a42ecf488e0a8b5da8f19d6676726'
assert subprocess.check_output(['git','status','--porcelain'])==b''
compressed=gzip.compress(original,compresslevel=9,mtime=0);encoded=base64.b64encode(compressed);parts=[]
for i,start in enumerate(range(0,len(encoded),8192),1):
    block=encoded[start:start+8192];data=b'\n'.join(block[j:j+76] for j in range(0,len(block),76))+b'\n'
    name=f'process-samples.gzip.base64.part-{i:02d}.txt';(out/name).write_bytes(data)
    parts.append({'file':name,'bytes':len(data),'base64_characters':len(block),'sha256':hashlib.sha256(data).hexdigest()})
value=json.loads(original)
metadata={'schema':'lossless-process-samples-parts/1','source_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    'source_path':source.relative_to(root).as_posix(),'original_sha256':source_hash,'original_bytes':len(original),
    'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'compressed_bytes':len(compressed),'gzip_mtime':0,
    'sample_count':len(value['samples']),'runner_pid':value['runner_pid'],'scope':value['scope'],'parts':parts}
(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
shutil.copyfile('/tmp/geometry-202-process-verify.py',out/'verify.py');shutil.copyfile(__file__,out/'make-parts.py')
argv=[sys.executable,str(out/'verify.py')];start=time.monotonic();run=subprocess.run(argv,capture_output=True,text=True)
assert run.returncode==0,run.stderr
(out/'verification-run.json').write_text(json.dumps({'argv':argv,'returncode':run.returncode,'seconds':time.monotonic()-start,
    'stdout':run.stdout,'stderr':run.stderr,'verify_sha256':hashlib.sha256((out/'verify.py').read_bytes()).hexdigest(),
    'source_bytes_unchanged':source.read_bytes()==original},indent=2)+'\n')
shutil.copyfile('/tmp/geometry-202-process-README.md',out/'README.md')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.iterdir()) if p.is_file())
(out/'SHA256SUMS').write_text(manifest)
print(json.dumps({'parts':len(parts),'payloads':len(manifest.splitlines()),'encoded_bytes':sum(p['bytes'] for p in parts),'verify_exit':run.returncode}))
