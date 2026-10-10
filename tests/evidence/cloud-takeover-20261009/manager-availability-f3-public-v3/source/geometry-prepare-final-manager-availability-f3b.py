from pathlib import Path
import hashlib, json

original = Path('<workspace-path>')
target = Path('<workspace-path>')
assert not target.exists()
text = original.read_text()
text = text.replace("EXPECTED='102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c'", "EXPECTED='f3b8285729b42cd22451c98cba1e2ec4514517f3'")
text = text.replace("OUT=Path('<workspace-path>')", "OUT=Path('<workspace-path>')")
text = text.replace("'agent':'/root/ui_tail_contract'", "'agent':'/root'")
text = text.replace('exact102ff', 'exactf3b')
target.write_text(text)
print(json.dumps({'originalSourceSHA256': hashlib.sha256(original.read_bytes()).hexdigest(), 'newSource': str(target), 'newSourceSHA256': hashlib.sha256(target.read_bytes()).hexdigest(), 'purpose': 'Recheck actual preserved original/default locations and incremental candidates read-only; use only existing CLI help, never construct Store or initialize missing ledger.'}))
