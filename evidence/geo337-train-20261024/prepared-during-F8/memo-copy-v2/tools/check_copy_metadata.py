from pathlib import Path
import argparse,hashlib,json,os,types
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['fixed','hardlink'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir()
source=Path(__file__).parent/'copy_r8_elf.py';raw=source.read_text()
old="    with src.open('rb') as origin, dst.open('xb') as target:\n        shutil.copyfileobj(origin,target,1024*1024)\n"
if a.mode=='hardlink':
 assert raw.count(old)==1
 raw=raw.replace(old,"    os.link(src,dst)\n",1)
m=types.ModuleType('metadata_only_copy_variant');exec(compile(raw,str(source)+'::'+a.mode,'exec'),m.__dict__)
src=a.out/'synthetic-original';dst=a.out/'synthetic-copy';body=b'\x7fELF synthetic bytes only, never executable or product payload\n'*8;src.write_bytes(body);os.chmod(src,0o700);st=src.lstat();want={'bytes':len(body),'mode':st.st_mode,'sha256':hashlib.sha256(body).hexdigest()}
print(json.dumps({'metadata_only':True,'formal_executed':False,'mode':a.mode,'synthetic_bytes':len(body),'original_inode':st.st_ino}),flush=True)
r=m._copy_exact(src,dst,want);assert src.read_bytes()==dst.read_bytes()==body
print(json.dumps({'metadata_only':True,'formal_executed':False,'mode':a.mode,'result':r}),flush=True)
