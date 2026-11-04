"""Named frontend creation-pin mutants; no native ledger is rewritten.

The judge loads the exact modified production source through its declared
GEOMETRY_CREATION_SOURCE seam. Original repository bytes remain untouched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'geometry-web/space-workspace.js'
TEST = 'tests/test_model_creation_identity_pin.js'

def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError('mutation source anchor is not unique: ' + before[:80])
    return source.replace(before, after, 1)

def rows(source):
    def block(start, end):
        first = source.index(start)
        return source[first:source.index(end, first)]
    owner = block('  function assertCreationOwner(', '  function creationPin(')
    graph = block('      if (data?.live!==true', '      const graph=SourceInspector.index(data)')
    final = block('    const final=creationPin(', '    GeometryProject.validateSpaceModel(record);')
    pin_guard = block('    if (dump?.ok!==true', '    return {scene:dump.text,revision:dump.revision')
    return [
        ('R362_C01_OWNER', 'context object, session', 'R362_CREATE_OWNER_context', owner,
         '  function assertCreationOwner(owner, revision=null) { return; }\n'),
        ('R362_C02_READ_DOWNGRADE', 'identity read failure', 'R362_CREATE_IDENTITY_READ_throw',
         '    const read=await api("identity-read");',
         '    let read;try { read=await api("identity-read"); } catch (_) { return; }'),
        ('R362_C03_GRAPH_PIN', 'live complete graph', 'R362_CREATE_GRAPH_PIN', graph, ''),
        ('R362_C04_FINAL_NATIVE_PIN', 'source changes after graph', 'R362_CREATE_FINAL_NATIVE_PIN', final, ''),
        ('R362_C05_INPUT_AFTER_AWAIT', 'cancelled or edited input', 'R362_CREATE_INPUT_sequence',
         '      if(seq!==state.sequence||revision!==state.revision||state.previewRevision!==revision||state.source!==source)throw new Error("設定或預覽已改變，未建立模型；請重新預覽。");', ''),
        ('R362_C06_ROOTS', 'active creation stores', 'R362_CREATE_ROOTS_REQUIRED',
         '      record.sourceIdentity=IdentityLedger.buildSourceIdentity({...record.input,boundary_id:record.source.boundary_id},graph.nodes);', ''),
        ('R362_C07_DUMP_PIN', 'live complete graph', 'R362_CREATE_DUMP_PIN', pin_guard, ''),
    ]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=False)
    original = SOURCE.read_bytes()
    source = original.decode('utf-8')
    def execute(label, variant, pattern=None):
        with tempfile.TemporaryDirectory(prefix='geometry-creation-pin-') as directory:
            candidate = Path(directory) / 'space-workspace.js'
            candidate.write_text(variant, encoding='utf-8', newline='\n')
            command = ['node', '--test', '--test-reporter=spec']
            if pattern:
                command.append('--test-name-pattern=' + pattern)
            command.append(TEST)
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, 'GEOMETRY_CREATION_SOURCE':str(candidate)}, capture_output=True, timeout=60)
        raw = result.stdout + result.stderr
        (options.output / (label + '.log')).write_bytes(raw)
        return {'exit':result.returncode,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}, raw.decode()
    baseline, _ = execute('baseline', source)
    if baseline['exit'] != 0:
        raise AssertionError('normal production baseline must be green')
    results = []
    for name, pattern, marker, old, new in rows(source):
        before, _ = execute(name + '-baseline', source, pattern)
        mutant, output = execute(name + '-mutant', replace_once(source, old, new), pattern)
        restored, _ = execute(name + '-restored', source, pattern)
        if before['exit'] != 0 or mutant['exit'] != 1 or restored['exit'] != 0 or marker not in output or 'ERR_ASSERTION' not in output or any(error in output for error in ('ReferenceError:', 'TypeError:', 'SyntaxError:')):
            raise AssertionError(name + ' did not produce its named assertion and restored green')
        results.append({'id':name,'marker':marker,'baseline':before,'mutant':mutant,'restored':restored})
    final, _ = execute('final', source)
    assert final['exit'] == 0 and SOURCE.read_bytes() == original
    result = {'scope':'frontend production source; not a native ledger','sourceSha256':hashlib.sha256(original).hexdigest(),'baseline':baseline,'mutants':results,'final':final,'sourceBytesUnchanged':True}
    (options.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'mutants':len(results),'all':'0/1/0','sourceBytesUnchanged':True}))

if __name__ == '__main__':
    main()
