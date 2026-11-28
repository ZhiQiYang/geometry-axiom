"""Generate D09's independent architecture fragment; delegate real census/golden imports.

This never fabricates a count, elapsed time, artifact or byte pin. Registration
is for this exact test-only module, not a directory exemption or hash refresh.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
import architecture_contract as architecture

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['register','import-canvas'])
    parser.add_argument('--artifact-id')
    parser.add_argument('--artifact',type=Path)
    args=parser.parse_args()
    if args.action=='import-canvas':
        if not args.artifact_id or not args.artifact:parser.error('original official artifact ZIP and artifact ID are required')
        return subprocess.run(['node','geometry-web/canvas_registry.js','import-cost','--id','P4549',
                               '--artifact-id',args.artifact_id,'--artifact',str(args.artifact.resolve())],cwd=ROOT).returncode
    module='geometry-web/canvas_sections/P4549.js'
    raw=(ROOT/module).read_bytes()
    if b'\r' in raw:raise ValueError('D09 module must be pure LF')
    manifest_path=ROOT/'geometry-core/domain-decoupling/product-architecture.json'
    manifest=architecture.load_manifest(manifest_path)
    entry={'path':module,'hashMode':'lf','sha256':hashlib.sha256(raw).hexdigest(),
           'reason':'D09 P4549 strict independent canvas module: real App preview/cancel/confirm and 390/1400 override-discovery paint checks; dispatched only by canvas_registry.js, never a product runtime dependency.'}
    matches=[item for item in manifest['exclusions'] if item['path']==module]
    if matches and matches!=[entry]:raise ValueError('Existing source review differs: inspect module before generating a new reviewed pin')
    if not matches:manifest['exclusions'].append(entry)
    planned=architecture.fragment_manifest_files(manifest)
    name='product-architecture.d/exclusions/'+module+'.json'
    target=manifest_path.parent/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(planned[name])
    print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'bytes':len(planned[name]),
                      'sha256':hashlib.sha256(planned[name]).hexdigest(),'moduleSha256':entry['sha256'],
                      'acceptance':False}))
    return 0

if __name__=='__main__':raise SystemExit(main())
