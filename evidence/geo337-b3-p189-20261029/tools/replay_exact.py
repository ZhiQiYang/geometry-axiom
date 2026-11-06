#!/usr/bin/env python3
"""Replay preserved real output once; negative variants alter copies only."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from exact_p189 import POLICY, compare

parser=argparse.ArgumentParser()
parser.add_argument('--receipts',type=Path,required=True)
parser.add_argument('--scene',required=True)
parser.add_argument('--mutation',default='none',choices=['none','wrong_text','wrong_position','fourth_difference','other_dump_byte','returncode','stderr_wrong_text','stderr_wrong_position','scene_input_changed','fourth_unlisted_scene'])
args=parser.parse_args()
inventory=json.loads((args.receipts/'scene-inventory.json').read_bytes())
pinned={r['name']:r['sha256'] for r in inventory['scenes']}
found={}; scene_path=None
for folder in sorted((args.receipts/'subcommands').iterdir()):
    stdin=folder/'stdin.bin'
    if not stdin.exists(): continue
    raw=stdin.read_bytes()
    if not raw.startswith(b'loadfile ') or not raw.endswith(b'\ndump\n'): continue
    path=Path(raw[9:-6].decode())
    if path.name!=args.scene: continue
    result=json.loads((folder/'result.json').read_bytes())
    side=Path(result['command'][-1]).parent.name
    if side not in ('main','fix'):continue
    assert not result['timeout_expired']
    streams={}
    for stream in ('stdout','stderr'):
        body=(folder/(stream+'.bin')).read_bytes()
        assert len(body)==result[stream]['bytes'] and hashlib.sha256(body).hexdigest()==result[stream]['sha256']
        streams[stream]=body
    found[side]=SimpleNamespace(**streams,returncode=result['actual_process_returncode'])
    scene_path=path
assert set(found)=={'main','fix'}
a,b=found['main'],found['fix']; name=args.scene; input_hash=pinned[name]
mutation=args.mutation
if mutation!='none':
    suffix=POLICY[name][2].encode()
    if mutation=='wrong_text': b.stdout=b.stdout.replace(suffix,suffix+b'!',1)
    elif mutation=='wrong_position': b.stdout=b.stdout.replace(suffix,b'',1)+suffix
    elif mutation=='fourth_difference': b.stdout+=b'\n'
    elif mutation=='other_dump_byte': b.stdout=b.stdout.replace(b'"revision":',b'"revisioN":',1)
    elif mutation=='returncode': b.returncode=1
    elif mutation=='stderr_wrong_text': b.stderr=b.stderr.replace(suffix,suffix+b'!',1)
    elif mutation=='stderr_wrong_position': b.stderr=suffix+b.stderr.replace(suffix,b'',1)
    elif mutation=='scene_input_changed': input_hash='0'*64
    elif mutation=='fourth_unlisted_scene': name='fourth-unlisted.scene'
passed,reason=compare(name,scene_path,a,b,input_hash,pinned)
print(json.dumps({'scene':args.scene,'mutation':mutation,'passed':passed,'assertion':reason,
                  'baseline_stdout_sha256':hashlib.sha256(a.stdout).hexdigest(),
                  'candidate_stdout_sha256':hashlib.sha256(b.stdout).hexdigest(),
                  'candidate_returncode':b.returncode},ensure_ascii=False))
raise SystemExit(0 if passed else 1)
