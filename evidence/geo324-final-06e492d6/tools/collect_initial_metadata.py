#!/usr/bin/env python3
"""只收 Git／環境原件；不 checkout、merge、編譯或執行驗收。"""
import datetime
import importlib.util
import json
import os
from pathlib import Path

BASE = Path('/tmp/geo324-owner-20261024')
OUT = BASE / 'initial-metadata'
REPO = Path('/workspace/geometry-axiom')
GROK = '4e176e830b691269cc72d021ce7e1bc0b167d621'
MAIN = 'eda91c8593f0795278f7f16ff8b93d147a4fdaa7'
HANDOFF = 'd193946b8e0fbda024d3b134c4851e9393a43d38'
PRBASE = '7dae5f21c7ca401e660450d437e60ba566218da8'
PATHS = ['geometry-templates/woodworking/geometry_woodworking/model_sources.py',
         'tests/test_geometry_host_sources.py', 'tests/run_all.expected.json']
if OUT.exists():
    raise SystemExit('refuse overwrite')
OUT.mkdir(parents=True)
spec = importlib.util.spec_from_file_location('capture', '/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env.pop('PYTHONOPTIMIZE', None)
rec = module.Recorder(OUT, env, GROK)
commands = [
    ['git', 'status', '--short'],
    ['git', 'rev-parse', 'HEAD', 'refs/remotes/origin/grok/geo261-faces-keyerror-322', 'refs/remotes/origin/main', 'refs/remotes/origin/handoff/codex-takeover-20261021'],
    ['git', 'show', HANDOFF+':handoff/pr-reviews/324.md'],
    ['git', 'show', HANDOFF+':handoff/pr-requests/README.md'],
    ['git', 'log', '--format=%H %P %s', PRBASE+'..'+GROK],
    ['git', 'diff', '--name-status', PRBASE, GROK],
    ['git', 'diff', '--stat', PRBASE, GROK],
    ['git', 'diff', PRBASE, GROK, '--'] + PATHS,
    ['git', 'ls-tree', PRBASE, '--'] + PATHS,
    ['git', 'ls-tree', GROK, '--'] + PATHS,
    ['git', 'ls-tree', MAIN, '--'] + PATHS,
    ['git', 'merge-base', MAIN, GROK],
    ['git', 'diff', '--name-status', PRBASE, MAIN, '--'] + PATHS,
    ['git', 'diff', PRBASE, MAIN, '--', 'tests/run_all.expected.json'],
    ['git', 'show', MAIN+':.github/workflows/integration-tests.yml'],
    ['git', 'show', GROK+':tests/test_geometry_host_sources.py'],
    ['git', 'show', GROK+':geometry-templates/woodworking/geometry_woodworking/model_sources.py'],
    ['git', 'grep', '-n', '-e', 'geometry_woodworking.model_sources', '-e', 'from .model_sources import', MAIN, '--', 'tests', 'geometry-app', 'geometry-templates', 'geometry-core'],
    ['git', 'show', MAIN+':tests/run_all.py'],
    ['git', 'show', MAIN+':tests/mutate.py'],
    ['uname', '-a'],
    ['python3', '--version'],
    ['node', '--version'],
    ['google-chrome', '--version'],
    ['df', '-B1', '/workspace', '/tmp'],
]
errors = []
for command in commands:
    row, stdout, stderr = rec.run(command, cwd=REPO, timeout=60, check=False,
                                 source_sha=GROK, source_variant='read-only-preparation-not-an-acceptance-execution')
    if row['actual_process_returncode'] != 0:
        errors.append({'command': command, 'exit': row['actual_process_returncode']})
result = {'schema': 'geo324.readonly-preparation.v1', 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'sourceHead': GROK, 'mainHead': MAIN, 'handoffHead': HANDOFF, 'prLocalBase': PRBASE,
          'executionKind': 'metadata-only', 'productOrTestExecuted': False, 'gitMutationPerformed': False,
          'commands': len(rec.rows), 'nonzeroCommands': errors,
          'warning': 'metadata success never substitutes for a product gate; no checkout or acceptance run yet'}
module.dump(OUT/'receipt.json', result)
print(json.dumps(result, ensure_ascii=False))
