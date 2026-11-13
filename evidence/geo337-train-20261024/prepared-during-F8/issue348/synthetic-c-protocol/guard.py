"""Protocol-only guard CLI; validates captured stub boundaries, never a product."""
import argparse, json
from pathlib import Path
from sidecar_snapshot import inspect_events

p = argparse.ArgumentParser()
p.add_argument('--run', type=Path, required=True)
p.add_argument('--completed', action='store_true')
a = p.parse_args()
r = inspect_events((a.run/'events.jsonl').read_bytes(), (a.run/'status.bin').read_bytes(),
                   (a.run/'stdin.bin').read_bytes(), completed=a.completed)
out = {'schema':'geo348-protocol-only-real-c-guard/1', 'valid':r['valid'],
       'errors':r['errors'], 'events':len(r['events']),
       'root_cause':None, 'product_gate_verdict':None, 'sidecar':r}
print(json.dumps(out, ensure_ascii=False))
raise SystemExit(0 if r['valid'] else 1)
