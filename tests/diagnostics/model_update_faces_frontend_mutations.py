"""R362 JS/controller/adapter behavioral mutations, separate from the C ledger.

Run with fresh GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE. This tool mutates
one shipped function at a time, requires its named assertion to fail, restores
the exact original bytes and reruns the same test. Infrastructure errors,
timeouts and skipped tests never count as kills.
"""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = 'geometry-web/model-update.js'
APP = 'geometry-web/model-update-app.js'
SPACE = 'geometry-web/space-workspace.js'
REVIEW = 'tests/test_model_update_faces_review.js'
UI = 'tests/test_model_update_faces_app.js'
MUTANTS = [
    ('R362_J01_FACES_SELECTION', CONTROL,
     "    if (s?.mode === 'faces') {", "    if (false) {",
     REVIEW, '^R362_FACE_SELECTION ', 'R362_FACE_SELECTION'),
    ('R362_J02_FACES_BEGIN', CONTROL,
     "if (!['plan', 'faces'].includes(record.input.mode))", "if (record.input.mode !== 'plan')",
     REVIEW, '^R362_FACE_RECEIPT ', 'R362_FACE_RECEIPT_BEGIN'),
    ('R362_J03_SLOT_BINDING', CONTROL,
     "chosen.uses.length === old.input.uses.length && next.input.uses.length === old.input.uses.length &&\n        next.input.uses.every((use, index) => use.placement_id === chosen.uses[index].placement_id &&\n          use.orientation === old.input.uses[index].orientation && use.purpose === old.input.uses[index].purpose)",
     'true', REVIEW, '^R362_FACE_RECEIPT ', 'R362_FACE_RECEIPT_ORDER'),
    ('R362_J04_PRODUCER_IDENTITY', CONTROL,
     "          Object.hasOwn(next, 'sourceIdentity') ||\n", '',
     REVIEW, '^R362_FACE_RECEIPT ', 'R362_FACE_RECEIPT_PRODUCER_IDENTITY'),
    ('R362_J05_RECEIPT_ALIAS', CONTROL,
     'identityReceipt = observed == null ? null : clone(observed);',
     'identityReceipt = observed == null ? null : observed;',
     REVIEW, '^R362_IDENTITY_RECEIPT ', 'R362_IDENTITY_RECEIPT_ALIAS'),
    ('R362_J06_RECEIPT_PIN', CONTROL,
     'const reviewId = await digest(canonical({generation: op.generation, candidate, ...(identityReceipt ? {identityReceipt} : {})}));',
     'const reviewId = await digest(canonical({generation: op.generation, candidate}));',
     REVIEW, '^R362_IDENTITY_RECEIPT ', 'R362_IDENTITY_RECEIPT_PIN'),
    ('R362_J07_NATIVE_IDENTITY_PIN', APP,
     "if (response.live !== true || response.complete !== true || response.revision !== pin.revision ||\n        response.sourceFingerprint !== pin.fingerprint || response.identityLedger?.schema !== 'identity-ledger/1' ||\n        response.identityLedger.active !== true)",
     'if (false)', UI, '^R362_UI_IDENTITY_PIN ', 'R362_UI_IDENTITY_PIN'),
    ('R362_J08_UNKNOWN_PREFILL', APP,
     'select.value = proved.has(use.placement_id) && current.surfaces.some(surface => surface.id === use.placement_id) ? String(use.placement_id) : \'\';',
     'select.value = current.surfaces.some(surface => surface.id === use.placement_id) ? String(use.placement_id) : \'\';',
     UI, '^R362_UI_UNKNOWN ', 'R362_UI_UNKNOWN_NO_PREFILL'),
    ('R362_J09_DECISION_PIN', APP,
     'if (current.decisionSignature && json(withDecisions(current.judged)) !== current.decisionSignature)',
     'if (false)', UI, '^R362_UI_REPLACED ', 'R362_UI_DECISION_PIN'),
    ('R362_J10_LIBRARY_FACES', SPACE,
     'if(record.input.mode==="faces") {', 'if(false) {',
     UI, '^R362_LIBRARY_FACES ', 'R362_LIBRARY_FACES'),
    ('R362_J11_REQUIRED_RETARGET', APP,
     'return !!(current?.judged && globalThis.IdentityLedger && !IdentityLedger.previewAllowed(withDecisions(current.judged)));',
     'return false;', UI, '^R362_UI_REPLACED ', 'R362_UI_REPLACED_DECISION'),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    originals = {name: (ROOT / name).read_bytes() for name in (CONTROL, APP, SPACE)}
    records = []

    def run(name, files, pattern=None):
        command = ['node', '--test', '--test-reporter=spec']
        if pattern:
            command += ['--test-name-pattern', pattern]
        command += files
        process = subprocess.run(command, cwd=ROOT, env=os.environ, capture_output=True, timeout=300)
        raw = process.stdout + process.stderr
        (out / (name + '.log')).write_bytes(raw)
        return {'command': command, 'exit_code': process.returncode, 'log': name + '.log',
                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}, raw.decode()

    def infrastructure_ok(log):
        return not any(word in log for word in ('BASE_TIMEOUT', 'TimeoutExpired', 'bridge closed',
            'BridgeClosed', 'MODULE_NOT_FOUND', 'SyntaxError', 'ReferenceError')) and bool(re.search(r'ℹ skipped 0\n', log))

    baseline, log = run('baseline', [REVIEW, UI])
    assert baseline['exit_code'] == 0 and 'ℹ tests 11\n' in log and 'ℹ pass 11\n' in log and infrastructure_ok(log), log
    try:
        for name, filename, before, after, suite, pattern, marker in MUTANTS:
            source = originals[filename].decode()
            assert source.count(before) == 1, (name, source.count(before))
            (ROOT / filename).write_bytes(source.replace(before, after).encode())
            mutant, text = run(name, [suite], pattern)
            assert mutant['exit_code'] == 1 and 'AssertionError [ERR_ASSERTION]' in text and marker in text and 'ℹ fail 1\n' in text and infrastructure_ok(text), (name, text)
            (ROOT / filename).write_bytes(originals[filename])
            restored, normal = run(name + '-restored', [suite], pattern)
            assert restored['exit_code'] == 0 and 'ℹ tests 1\n' in normal and 'ℹ pass 1\n' in normal and infrastructure_ok(normal), (name, normal)
            records.append({'id': name, 'path': filename, 'baseline': baseline['exit_code'],
                            'mutant': mutant, 'restored': restored, 'marker': marker})
            print(name, '0/1/0', flush=True)
    finally:
        for filename, original in originals.items():
            (ROOT / filename).write_bytes(original)
    result = {'schema': 'r362-frontend-mutations/1', 'official_native_ledger': False,
              'products': {name: hashlib.sha256(content).hexdigest() for name, content in originals.items()},
              'baseline': baseline, 'mutations': records}
    (out / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('all named frontend mutations killed and restored')


if __name__ == '__main__':
    main()
