"""Remove general D64 version gates and require named compatibility failures.

Each mutation runs the real Python verifier and native model adapter. Errors,
skips, unexpected exits and missing named assertions never count as killed.
Every restored control runs the complete compatibility suite in a fresh process.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'geometry-core/modeling/__init__.py'
TEST = ROOT / 'tests/test_engineering_model_compatibility.py'
SCENE = 'GRID_CARD_CAPABILITY in scene_required_capabilities(definitions["base_scene"])'
MANIFEST = 'isinstance(manifest["capabilities"], list) and GRID_CARD_CAPABILITY in manifest["capabilities"]'
CONDITION = 'if (' + SCENE + ' or\n                    ' + MANIFEST + '):'
BASE = 'tests.test_engineering_model_compatibility'
CLASS = BASE + '.EngineeringModelCompatibility.'
MUTATIONS = (
    ('V01-remove-gate', CONDITION, 'if False:',
     'test_pre_card_axioms_reject_manifest_card_capability', 'CARD_AXIOM_MANIFEST'),
    ('V02-ignore-manifest', CONDITION, 'if (' + SCENE + '):',
     'test_pre_card_axioms_reject_manifest_card_capability', 'CARD_AXIOM_MANIFEST'),
    ('V03-ignore-source', CONDITION, 'if (' + MANIFEST + '):',
     'test_pre_card_axioms_reject_scene_card_capability_before_rebuild', 'CARD_AXIOM_SOURCE'),
    ('V04-exempt-latest-pre-adoption', CONDITION,
     'if supplied_version not in PRE_CARD_REFERENCE_AXIOM_VERSIONS and (' + SCENE + ' or\n                    ' + MANIFEST + '):',
     'test_pre_card_axioms_reject_card_syntax_with_stripped_declarations', 'CARD_AXIOM_SYNTAX'),
    # GEO-261 retired b3c79615, which already contains D64/I74/R60; treating that
    # adoption pair as pre-adoption must turn the era test red.
    ('V05-card-adoption-treated-as-pre', 'CARD_REFERENCE_AXIOM_VERSIONS = PRE_DECOUPLING_AXIOM_VERSIONS',
     'CARD_REFERENCE_AXIOM_VERSIONS = frozenset()',
     'test_card_claims_split_exactly_at_the_d64_adoption_before_rebuild', 'CARD_AXIOM_ERA'),
)
SUITE_TESTS = 39


def run(directory, selected):
    directory.mkdir(parents=True)
    command = [sys.executable, '-m', 'unittest', selected]
    start = time.monotonic()
    p = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
    (directory / 'stdout.log').write_bytes(p.stdout)
    (directory / 'stderr.log').write_bytes(p.stderr)
    output = p.stderr.decode()
    counts = re.search(r'Ran (\d+) tests? in', output)
    failures = re.search(r'failures=(\d+)', output)
    errors = re.search(r'errors=(\d+)', output)
    skips = re.search(r'skipped=(\d+)', output)
    record = dict(command=command, exit_code=p.returncode,
                  seconds=time.monotonic() - start,
                  tests=int(counts[1]) if counts else None,
                  failures=int(failures[1]) if failures else 0,
                  errors=int(errors[1]) if errors else 0,
                  skips=int(skips[1]) if skips else 0,
                  stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),
                  stderr_sha256=hashlib.sha256(p.stderr).hexdigest())
    (directory / 'receipt.json').write_text(json.dumps(record, indent=2) + '\n')
    return record, output


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    original = TARGET.read_bytes()
    text = original.decode()
    assert text.count(CONDITION) == 1
    baseline, _ = run(out / 'baseline', BASE)
    assert baseline['exit_code'] == 0 and baseline['tests'] == SUITE_TESTS
    assert baseline['failures'] == baseline['errors'] == baseline['skips'] == 0
    report = dict(source_head=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        source_sha256=hashlib.sha256(original).hexdigest(),
        test_sha256=hashlib.sha256(TEST.read_bytes()).hexdigest(),
        baseline=baseline, mutants=[])
    try:
        for identifier, old, new, test, label in MUTATIONS:
            changed = text.replace(old, new, 1).encode()
            TARGET.write_bytes(changed)
            directory = out / identifier
            try:
                red, output = run(directory / 'red', CLASS + test)
            finally:
                TARGET.write_bytes(original)
            restored, _ = run(directory / 'restored', BASE)
            killed = (red['exit_code'] == 1 and red['tests'] == 1 and
                      red['failures'] > 0 and red['errors'] == red['skips'] == 0 and
                      label in output and ('FAIL: ' + test) in output and
                      restored['exit_code'] == 0 and restored['tests'] == SUITE_TESTS and
                      restored['errors'] == restored['skips'] == 0)
            row = dict(id=identifier, old=old, new=new, named_test=test,
                       mutant_sha256=hashlib.sha256(changed).hexdigest(),
                       red=red, restored=restored, verdict='killed' if killed else 'NOT_KILLED')
            report['mutants'].append(row)
            (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(identifier, row['verdict'], flush=True)
            if not killed:
                return 1
    finally:
        TARGET.write_bytes(original)
        assert TARGET.read_bytes() == original
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(main(parser.parse_args().output))
