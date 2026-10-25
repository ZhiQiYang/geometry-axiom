from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
original=Path('/tmp/geo323-provider-hint-publication-20261024/publish.py').read_text()
changes={
 '/tmp/geo323-provider-hint-private-work-20261024':'/tmp/geo337-reference-local-init-work-20261024',
 '/tmp/geo323-provider-hint-prbody-work-20261024':'/tmp/geo337-reference-local-init-prbody-work-20261025',
 '1449d430d1c4734bb1bc3a9f91f3851c845cc0f3':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7',
 'codex/train337-provider-hint-20261024':'codex/train337-reference-local-init-20261024',
 'evidence/geo323-provider-hint-1449d430':'evidence/geo323-reference-local-init-2c463557',
 'Record provider hint proof and related source validation':'Record reference initialization proofs and focused validation',
 'Document provider hint current validation state':'Document reference initialization validation state',
}
candidate=original
for before,after in changes.items():
 assert candidate.count(before)==1,(before,candidate.count(before))
 candidate=candidate.replace(before,after)
assert not (H/'publish.py').exists()
(H/'publish.py').write_text(candidate)
dump(H/'PUBLICATION_TOOL.json',{'original_sha256':sha(original.encode()),'candidate_sha256':sha(candidate.encode()),'only_parameters_changed':changes})
print((H/'PUBLICATION_TOOL.json').read_text())
