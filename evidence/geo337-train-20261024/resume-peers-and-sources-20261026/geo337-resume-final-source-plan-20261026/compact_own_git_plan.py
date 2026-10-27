"""Losslessly compact only this agent's newly generated, rebuildable Git plan."""
from pathlib import Path
import gzip,hashlib,json
root=Path(__file__).parent
p=root/'ARCHITECTURE_SELECTED_GIT.json'
raw=p.read_bytes();assert len(raw)==113741 and hashlib.sha256(raw).hexdigest()=='ffc551fb77d32b37a4c7079c8d68008eb94a8736b8858a8d1bc39d2a343c6a60'
out=root/'ARCHITECTURE_SELECTED_GIT.json.gz';assert not out.exists();out.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(out.read_bytes())==raw
compact=json.loads(raw);compact['files']=[[x['path'],x['mode'],x['oid'],x['bytes']]for x in compact['files']];compact['record_fields']=['path','mode','oid','bytes']
# Raw metadata is preserved byte-exact in gzip; replacing only this new derived plan.
p.write_text(json.dumps(compact,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps({'original_raw_retained':str(out),'original_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'gzip_bytes':out.stat().st_size,'compact_bytes':p.stat().st_size}))
