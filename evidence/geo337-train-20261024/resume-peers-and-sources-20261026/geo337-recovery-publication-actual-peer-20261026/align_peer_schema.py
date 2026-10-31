"""Add the original retirement reader's required findings alias; do not rerun audit."""
from pathlib import Path
import hashlib,json
root=Path(__file__).parent;p=root/'REVIEW.json';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='3816fd61b34b2c63213675b2ddc03e0ef90f8d76e62201c8bcf7accba758cffd'
assert not (root/'REVIEW.initial.json').exists()
data=json.loads(raw);assert data['exit_code']==0 and data['findings']==[]
(root/'REVIEW.initial.json').write_bytes(raw)
data['blocking_findings']=data['findings']
data['schema_alignment']='blocking_findings aliases the actual completed audit findings; no verdict, counter, raw receipt, or original stream changed'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'exit_code':0,'audit_rerun':False,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'field_mapping':{'blocking_findings':'findings'}}))
