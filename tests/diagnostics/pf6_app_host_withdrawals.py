"""PF6 host/HTTP named withdrawals in isolated literal-CJS source closures.

These are executable local diagnostics, never official ME or Chrome evidence.
Every mutant keeps the test bytes and must fail its named functional assertion.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HOST = 'tests/test_panel_fill_builder_host.js'
APP = 'geometry-web/app.js'
WORKSPACE = 'geometry-web/reference-workspace.js'
STORE = 'geometry-web/project-store.js'
TRANSPORT = 'geometry-web/panel_fill_builder_transport.py'
ROWS = [
    ('PF6_APP_HOST_ACCEPT_ZERO_TOKEN', WORKSPACE, 'PF6_APP_HOST_POSITIVE_TOKEN',
     'function timberTokenKey(token){return featureTokenKey(token);}',
     "function timberTokenKey(token){return token===0||token==='0'?'0':featureTokenKey(token);}"),
    ('PF6_APP_HOST_FORGET_NULL_TOKEN_OWNER', WORKSPACE, 'PF6_APP_HOST_NULL_TOKEN_STILL_OWNS_THE_SHARED_LEASE',
     'if(timberPreview)throw new Error("角材候選尚未結束，請先確認或取消。");',
     'if(timberPreview?.token)throw new Error("角材候選尚未結束，請先確認或取消。");'),
    ('PF6_APP_HOST_CROSS_OWNER', WORKSPACE, 'PF6_APP_CROSS_OWNER_CONFIRM',
     'timberPreview.kind!==kind', 'false'),
    ('PF6_APP_HOST_OMIT_WRITE_GATE', APP, 'PF6_APP_HOST_WRITE_GATE',
     '|boundary-pair-confirm |framing-template-confirm |pf6-confirm )/.test(cmd)) {',
     '|boundary-pair-confirm |framing-template-confirm )/.test(cmd)) {'),
    ('PF6_APP_HOST_OMIT_RECEIPT_IDS', APP, 'PF6_APP_HOST_RECEIPT_IDS',
     '|framing-template-cancel |pf6-confirm |pf6-cancel )/.test(cmd) ? crypto.randomUUID() : null;',
     '|framing-template-cancel )/.test(cmd) ? crypto.randomUUID() : null;'),
    ('PF6_APP_HOST_OMIT_CONFIRMATION_CLASS', APP, 'PF6_APP_HOST_CONFIRMATION_LEASE',
     '|boundary-pair-confirm|framing-template-confirm|pf6-confirm) /.test(cmd)) {',
     '|boundary-pair-confirm|framing-template-confirm) /.test(cmd)) {'),
    ('PF6_APP_HOST_WRONG_CONFIRMATION_LEASE', APP, 'PF6_APP_HOST_CONFIRMATION_LEASE',
     'try { confirmation = /^(boundary-pair|framing-template|pf6)-confirm /.test(cmd) ?',
     'try { confirmation = /^(boundary-pair|framing-template)-confirm /.test(cmd) ?'),
    ('PF6_APP_HOST_OMIT_NATIVE_PENDING', WORKSPACE, 'PF6_APP_HOST_NATIVE_OPERATION',
     "  function beginNativeOperation(command) {\n    if (!/^(boundary-pair|framing-template|pf6)-confirm /.test(command))",
     "  function beginNativeOperation(command) {\n    if (!/^(boundary-pair|framing-template)-confirm /.test(command))"),
    ('PF6_APP_HOST_OMIT_OBSERVER', APP, 'PF6_APP_HOST_OBSERVER',
     'if (current) ReferenceWorkspace.observe(cmd, res);',
     "if (current && !cmd.startsWith('pf6-')) ReferenceWorkspace.observe(cmd, res);"),
    ('PF6_APP_HOST_OMIT_DEFINITION_EVENT', APP, 'PF6_APP_HOST_DEFINITION_EVENT',
     '|boundary-pair-confirm |framing-template-confirm |pf6-confirm )/.test(cmd) &&',
     '|boundary-pair-confirm |framing-template-confirm )/.test(cmd) &&'),
    ('PF6_APP_HOST_OMIT_RECOVERY_CLASS', APP, 'PF6_APP_HOST_RECOVERY_CLASSIFICATION',
     'if (/^pf6-(suggest|select|confirm|cancel) /.test(cmd)) {', 'if (false) {'),
    ('PF6_APP_HOST_OMIT_RECOVERY_EVENT', APP, 'PF6_APP_HOST_RECOVERY_EVENT',
     "if (current && cmd.startsWith('pf6-confirm ') && result.ok && result.history_changed !== false)",
     "if (false && current && cmd.startsWith('pf6-confirm ') && result.ok && result.history_changed !== false)"),
    ('PF6_APP_HOST_OMIT_DIRTY_CLASS', WORKSPACE, 'PF6_APP_HOST_DIRTY',
     'if (result.ok && /^(boundary-pair|framing-template|pf6)-confirm /.test(cmd) && result.history_changed !== false) dirty();',
     'if (result.ok && /^(boundary-pair|framing-template)-confirm /.test(cmd) && result.history_changed !== false) dirty();'),
    ('PF6_APP_HOST_OMIT_BROADCAST_CLASS', WORKSPACE, 'PF6_APP_HOST_BROADCAST',
     'if(result.ok && !result.preview && /^(boundary-pair|framing-template|pf6)-confirm /.test(cmd) && result.history_changed !== false)notifySceneChange();',
     'if(result.ok && !result.preview && /^(boundary-pair|framing-template)-confirm /.test(cmd) && result.history_changed !== false)notifySceneChange();'),
    ('PF6_APP_HOST_UINT64_OBSERVER_NUMBER_ROUNDTRIP', WORKSPACE, 'PF6_APP_EXACT_NATIVE_REVISION',
     'nativeDefinitionRevision = text;', 'nativeDefinitionRevision = String(Number(text));'),
    ('PF6_APP_HOST_OMIT_HISTORY', STORE, 'PF6_APP_ONE_HISTORY_IDMAP',
     '/^(boundary-pair|framing-template|pf6)-confirm /', '/^(boundary-pair|framing-template)-confirm /'),
    ('PF6_APP_HOST_RECEIPT_WRONG_SESSION', APP, 'PF6_APP_RECEIPT_ORIGIN_SESSION',
     'JSON.stringify({ receipt: requestId, session: originSession })',
     'JSON.stringify({ receipt: requestId, session: connection.session })'),
    ('PF6_APP_HOST_ACCEPT_HEADERLESS_TERMINAL', APP, 'PF6_APP_TERMINAL_DIRECT_SESSION',
     "    if (/^pf6-(confirm|cancel) /.test(cmd) && r.headers.get('X-Geometry-Session') !== originSession)\n      throw new Error('角材確認／取消的回覆缺少原服務工作階段；僅能核對原請求回執。');\n", ''),
    ('PF6_APP_HOST_DROP_BOOTSTRAP_OBSERVATION', APP, 'PF6_APP_BOOTSTRAP_READ_OBSERVED',
     'const bootstrapRead = !originSession &&', 'const bootstrapRead = false &&'),
    ('PF6_APP_HOST_UNSENT_AS_UNKNOWN', APP, 'PF6_APP_NOT_SENT_IS_NOT_UNKNOWN',
     'return { ok: false, transport: true, sent: false, error: connection.error',
     'return { ok: false, transport: true, error: connection.error'),
    ('PF6_APP_HTTP_REJECT_PARAMETER_ZERO', TRANSPORT, 'PF6_HTTP_PARAMETER_ZERO_IS_VALID',
     "_u32(value['parameterId']) and _u32(value['fieldId'])",
     "_u32(value['parameterId'], positive=True) and _u32(value['fieldId'], positive=True)"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def cjs_closure():
    pending = [HOST, APP, WORKSPACE]
    found = set()
    while pending:
        relative = pending.pop()
        if relative in found:
            continue
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise AssertionError('PF6_WITHDRAW_SOURCE: ' + relative)
        found.add(relative)
        if source.suffix not in {'.js', '.cjs'}:
            continue
        for specifier in re.findall(r"\brequire(?:\.resolve)?\(\s*['\"]([^'\"]+)['\"]\s*\)", source.read_text('utf-8')):
            if not specifier.startswith('.'):
                continue
            target = (source.parent / specifier).resolve()
            choices = [target] if target.suffix else [target, target.with_suffix('.js'), target / 'index.js']
            picked = next((v for v in choices if v.is_file()), None)
            if picked is None or ROOT not in picked.parents:
                raise AssertionError('PF6_WITHDRAW_CJS_CLOSURE: ' + specifier)
            pending.append(picked.relative_to(ROOT).as_posix())
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--out must be a new directory outside the repository')
    output.mkdir(parents=True)
    closure = cjs_closure()
    originals = {relative: (ROOT / relative).read_bytes() for relative in closure | {TRANSPORT}}
    records = []
    with tempfile.TemporaryDirectory(prefix='pf6-host-withdraw-') as temporary:
        work = Path(temporary)
        for relative, raw in originals.items():
            path = work / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for name, relative, assertion, before, after in ROWS:
            original = originals[relative]
            if original.count(before.encode()) != 1:
                raise AssertionError(name + ': product anchor must occur exactly once')
            mutant = original.replace(before.encode(), after.encode(), 1)
            if relative == TRANSPORT:
                program = ("import importlib.util,sys,unittest;"
                           "p=sys.argv[1];s=importlib.util.spec_from_file_location('panel_fill_builder_transport',p);"
                           "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);"
                           "sys.argv=[sys.argv[0],'tests.test_panel_fill_builder_transport.PF6HTTPProtocol.test_parameter_zero_ids_reach_native_without_changing_the_source'];unittest.main(module=None)")
                command = [sys.executable, '-B', '-c', program, str(work / TRANSPORT)]
                cwd = ROOT
            else:
                command = ['node', '--test', '--test-name-pattern=' + assertion, HOST]
                cwd = work
            rows = []
            for phase, raw in [('baseline', original), ('withdrawn', mutant), ('restored', original)]:
                (work / relative).write_bytes(raw)
                env = dict(os.environ)
                env.pop('GEOMETRY_TEST_APP', None); env.pop('GEOMETRY_TEST_REFERENCE_WORKSPACE', None)
                run = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=60)
                logs = {}
                for suffix, data in [('stdout', run.stdout), ('stderr', run.stderr)]:
                    path = output / (name + '-' + phase + '.' + suffix)
                    path.write_bytes(data)
                    logs[suffix] = {'file': path.name, 'bytes': len(data), 'sha256': sha(data)}
                rows.append({'phase': phase, 'exit': run.returncode, **logs})
                if phase == 'withdrawn':
                    failure = (run.stdout + run.stderr).decode('utf-8', 'replace')
            codes = [row['exit'] for row in rows]
            if codes != [0, 1, 0] or assertion not in failure or not any(v in failure for v in ['ERR_ASSERTION', 'AssertionError']):
                raise AssertionError(name + ': expected named functional 0/1/0; got ' + repr(codes))
            records.append({'name': name, 'source': relative, 'assertion': assertion, 'command': command,
                            'source_sha256': sha(original), 'withdrawn_sha256': sha(mutant),
                            'exit_codes': codes, 'runs': rows})
    for relative, raw in originals.items():
        if (ROOT / relative).read_bytes() != raw:
            raise AssertionError('PF6_WITHDRAW_INPUT_CHANGED: ' + relative)
    inputs = {**originals, 'tests/test_panel_fill_builder_transport.py': (ROOT / 'tests/test_panel_fill_builder_transport.py').read_bytes(),
              'tests/test_serve.py': (ROOT / 'tests/test_serve.py').read_bytes(),
              'geometry-web/serve.py': (ROOT / 'geometry-web/serve.py').read_bytes()}
    report = {'schema': 'pf6-app-host-withdrawals/1', 'official_mutation_evidence': False,
              'inputs': [{'path': path, 'bytes': len(raw), 'sha256': sha(raw)} for path, raw in sorted(inputs.items())],
              'records': records}
    (output / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'records': [{'name': row['name'], 'exit_codes': row['exit_codes']} for row in records]}, indent=2))


if __name__ == '__main__':
    main()
