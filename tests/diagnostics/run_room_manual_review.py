#!/usr/bin/env python3
"""Run the R22 component/native diagnostic using the normal fresh-binary guard.

This does not launch a browser or change its sandbox. Build with start_local.py.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bridge', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--mutation', choices=['keep-reviewed-after-edit', 'allow-unapplied-row'])
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('r22_local_launcher', ROOT / 'geometry-web/start_local.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
launcher.ensure_stack()
registry = launcher.load_registry(ROOT)
bridge = registry.require_fresh('bridge', args.bridge)
env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(bridge), GEOMETRY_ROOM_REVIEW_OUT=str(args.out.resolve()))
if args.mutation:
    env['GEOMETRY_ROOM_REVIEW_MUTATION'] = args.mutation
else:
    env.pop('GEOMETRY_ROOM_REVIEW_MUTATION', None)
raise SystemExit(subprocess.run(['node', str(ROOT / 'tests/diagnostics/room_manual_review.cjs')],
                               cwd=ROOT, env=env).returncode)
