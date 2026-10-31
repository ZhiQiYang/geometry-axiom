"""Produce the deliberately inactive candidate request; no source reads or writes."""
from pathlib import Path
import json,hashlib
here=Path(__file__).parent
old=Path('/tmp/geo337-S10-three-leaf-adoption-preparation-20261025/REQUEST.UNBOUND.json')
q=json.loads(old.read_bytes())
q.update(schema='candidate-S10-A-three-leaf-byte-adoption/1',architecture_source_sha='a6f4013364e21bcb7239b5dcc25caac0f6d61f77',candidate_branch='codex/train337-recovered-evidence-20261026',expected_parent='9a57aea2128a7bc3985064932c24e2229fd8fcb8',expected_publisher_head='3e4f2560aa11ed2a626db98ba5ed6f129e791052',expected_publisher_index_sha256=None,root_candidate_ref_exclusive=False,out='/dev/shm/geometry-axiom-geo337-20261025/candidate-three-leaf-adoption-original-20261026',s10_to_architecture_decision={'old':{'mode':'100644','oid':None,'bytes':None,'sha256':None},'new':{'mode':'100644','oid':None,'bytes':None,'sha256':None}})
p=here/'REQUEST.UNBOUND.json';assert not p.exists();p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'execution_leases':False}))
