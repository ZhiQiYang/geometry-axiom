"""Q38j-c isolated update JS mutations; terminal designated assertions alone kill.

Each case executes baseline, variant and restored in fresh Node processes.
An isolated preload substitutes only one product source file; the worktree is
never mutated. Syntax errors, exceptions, skips, crashes and timeouts are invalid.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
UPDATE = 'geometry-web/model-update.js'
UI = 'geometry-web/model-update-app.js'
UPDATE_JUDGE = 'tests/test_space_profile_update.js'
UI_JUDGE = 'tests/test_space_profile_update_ui.js'
CASES = [
    ('Q38JC01-remove-sixth-package', UPDATE,
     "const PACKAGES = ['space', 'volume', 'clearance', 'walls', 'timbers', 'profile_runs'];",
     "const PACKAGES = ['space', 'volume', 'clearance', 'walls', 'timbers'];",
     UPDATE_JUDGE, 'Q38JC controller adds the profile package', 'Q38JC_DIFF_PACKAGE'),
    ('Q38JC02-drop-selected-profile-receipt-guard', UPDATE,
     '        same(next.input.profile_runs || [], chosen.profile_runs) &&\n', '',
     UPDATE_JUDGE, 'Q38JC controller rejects a coherent producer', 'Q38JC_SELECTION_MATCH'),
    ('Q38JC03-preselect-profile-candidates', UI,
     'type="checkbox" data-mu-profile-run="${run.id}"',
     'type="checkbox" data-mu-profile-run="${run.id}" checked',
     UI_JUDGE, 'Q38JC UI all world runs', 'Q38JC_UI_EXPLICIT'),
    ('Q38JC04-drop-explicit-empty-profile-selection', UI,
     'timbers,profile_runs,projection:', 'timbers,projection:',
     UI_JUDGE, 'Q38JC UI explicit empty selection', 'Q38JC_UI_EMPTY_REMOVAL'),
    ('Q38JC05-remove-native-profile-precommit-recheck', UI,
     "    if (profileSource(profilesBefore).revision !== current.profileRevision || profileSource(profilesAfter).revision !== current.profileRevision || current.profileRevision !== pin.revision)\n"
     "      throw Error('斷面拉伸件來源已變更，請關閉後重新明選來源。');",
     '    /* mutant: omit native profile revision recheck */',
     UI_JUDGE, 'Q38JC UI preview and confirmation reread', 'Q38JC_UI_PINNED_REVISION'),
    ('Q38JC06-remove-embedded-profile-boundary-normalization', UPDATE,
     'const boundaryId = chosen.boundary_id === 0 && next.source.boundary_id === null && (old.input.profile_runs?.length || next.input.profile_runs?.length || old.source.boundary_id === null) ? null : chosen.boundary_id;',
     'const boundaryId = chosen.boundary_id;',
     UPDATE_JUDGE, 'Q38JC native embedded profile uses canonical null boundary', 'Q38JC_EMBEDDED_CANONICAL_BOUNDARY'),
    # Old profile inputs and their canonical null source both preserve removal.
    # Remove that entire old-record support; deleting only the old-input term
    # would be an equivalent mutant for validated profile records.
    ('Q38JC07-remove-old-record-boundary-support', UPDATE,
     '(old.input.profile_runs?.length || next.input.profile_runs?.length || old.source.boundary_id === null)',
     '(next.input.profile_runs?.length)',
     UPDATE_JUDGE, 'Q38JC native embedded profile uses canonical null boundary', 'Q38JC_EMBEDDED_REMOVE_BOUNDARY'),
    ('Q38JC08-remove-canonical-null-continuation', UPDATE,
     ' || old.source.boundary_id === null', '',
     UPDATE_JUDGE, 'Q38JC native embedded profile uses canonical null boundary', 'Q38JC_EMBEDDED_CONTINUATION'),
    ('Q38JC09-remove-profile-producer-capability', UI,
     'if(data.record.input.profile_runs||data.selection.profile_runs?.length)await requireProfileSpaceCapability(current,signal);', '',
     UI_JUDGE, 'Q38JC UI /3 capability is required', 'Q38JC_UI_CAPABILITY'),
    ('Q38JC10-claim-run-continuity', UI,
     "summary.token === 'proved' ? '已追蹤根延續已證明；拉伸件延續未知'", "summary.token === 'proved' ? '物件延續已證明'",
     UI_JUDGE, 'Q38JC UI selecting the first run', 'Q38JC_UI_IMMEDIATE_PROOF_SCOPE'),
    ('Q38JC11-hide-empty-selected-run', UI,
     "if (!members.length) return `已納入 ${result.summary.profile_run_count} 條拉伸件，零構件；參考包絡不計材料量。未檢查碰撞、貼合或包含。`;",
     "if (!members.length) return '未納入';",
     UI_JUDGE, 'Q38JC UI per-member review', 'Q38JC_UI_ZERO_MEMBER_SELECTED'),
]
HOOK = r"""'use strict';
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const read=fs.readFileSync,extension=Module._extensions['.js'];
const target=path.resolve(process.env.Q38J_MUTANT_TARGET),variant=read(process.env.Q38J_MUTANT_SOURCE);
fs.readFileSync=function(file,options){
  if(typeof file==='string'&&path.resolve(file)===target){
    const encoding=typeof options==='string'?options:options?.encoding;
    return encoding?variant.toString(encoding):Buffer.from(variant);
  }
  return read.apply(this,arguments);
};
Module._extensions['.js']=function(module,filename){
  if(path.resolve(filename)===target)return module._compile(variant.toString('utf8'),filename);
  return extension(module,filename);
};
"""
REPORTER = r"""const serial=e=>e&&({name:e.name,code:e.code,message:e.message,cause:serial(e.cause)});
module.exports=async function*(events){for await(const e of events)if(['test:pass','test:fail','test:summary'].includes(e.type)){
 const d=e.data;yield JSON.stringify({type:e.type,name:d.name,skip:d.skip,details:d.details&&{...d.details,error:serial(d.details.error)},counts:d.counts})+'\n';
}};
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    cases = [c for c in CASES if not args.case or c[0] in args.case]
    if not cases or args.case and set(args.case) - {c[0] for c in CASES}:
        parser.error('Unknown/empty case selection')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    hook = out / 'substitute.cjs'; hook.write_text(HOOK)
    reporter = out / 'reporter.cjs'; reporter.write_text(REPORTER)
    # Freeze a conservative superset of require/VM/fixture dependencies. The
    # source guards must notice changes in transitive validators, not merely
    # the directly mutated module. No execution claim comes from these hashes.
    closure = {str(p.relative_to(ROOT)) for directory in ('geometry-web', 'geometry-app', 'geometry-templates', 'geometry-core')
               for p in (ROOT / directory).rglob('*.js') if 'node_modules' not in p.parts}
    closure |= {str(p.relative_to(ROOT)) for p in (ROOT / 'tests').glob('*.js')}
    closure |= {str(p.relative_to(ROOT)) for p in (ROOT / 'tests/fixtures').rglob('*') if p.is_file()}
    closure |= {str(p.relative_to(ROOT)) for p in (ROOT / 'geometry-core/modeling').rglob('*.py')}
    closure |= {str(p.relative_to(ROOT)) for directory in ('geometry-app/geometry_app', 'geometry-core/geometry_kernel', 'geometry-core/rule_cases')
                for p in (ROOT / directory).rglob('*.py')}
    closure |= {str(p.relative_to(ROOT)) for p in (ROOT / 'geometry-web').glob('*.py')}
    paths = sorted(closure | {c[1] for c in CASES} | {c[4] for c in CASES} |
                   {'tests/q38j_update_workspace_mutations.py', 'tests/q38j_profile_fixture.py', 'tests/test_space_profile_runs.py',
                    'tests/test_section_profile_modeling.py', 'tests/test_space_profile_update.py', 'tests/test_model_update.py',
                    'geometry-web/model_update.py', 'geometry-web/space_modeling.py', 'geometry-web/start_local.py', 'tests/binaries.py'})
    original = {p: (ROOT / p).read_bytes() for p in paths}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    common = {'head': head, 'sources_sha256': {p: sha(v) for p, v in original.items()},
              'node': subprocess.check_output(['node', '--version'], text=True).strip(),
              'hook_sha256': sha(HOOK.encode()), 'reporter_sha256': sha(REPORTER.encode())}
    common['native'] = {name: {'path': os.environ[name], 'sha256': sha(Path(os.environ[name]).read_bytes()),
                              'fingerprint_sha256': sha(Path(os.environ[name] + '.fingerprint.json').read_bytes())}
                        for name in ('GEOMETRY_MODEL_BASE', 'GEOMETRY_TEST_BRIDGE') if name in os.environ}
    write(out / 'inputs.json', common)
    rows = []
    for ident, target, before, after, judge, test, marker in cases:
        directory = out / ident; directory.mkdir()
        raw = original[target]; old = before.encode(); new = after.encode()
        if raw.count(old) != 1:
            raise RuntimeError(ident + ': anchor must occur exactly once')
        variant = directory / Path(target).name; variant.write_bytes(raw.replace(old, new))
        syntax_command = ['node', '--check', str(variant)]
        syntax_started = time.monotonic()
        syntax = subprocess.run(syntax_command, cwd=ROOT, capture_output=True)
        (directory / 'syntax.stdout').write_bytes(syntax.stdout); (directory / 'syntax.stderr').write_bytes(syntax.stderr)
        syntax_receipt = {'head': head, 'command': syntax_command, 'cwd': str(ROOT),
                          'exit': syntax.returncode, 'elapsed_seconds': round(time.monotonic() - syntax_started, 6),
                          'checked_files': 1, 'stdout_sha256': sha(syntax.stdout), 'stderr_sha256': sha(syntax.stderr)}
        write(directory / 'syntax.execution.json', syntax_receipt)
        if syntax.returncode:
            raise RuntimeError(ident + ': syntax failure cannot kill')
        phases = {}
        for phase in ('baseline', 'mutant', 'restored'):
            command = ['node']
            env = dict(os.environ)
            if phase == 'mutant':
                command += ['--require', str(hook)]
                env.update(Q38J_MUTANT_TARGET=str(ROOT / target), Q38J_MUTANT_SOURCE=str(variant))
            command += ['--test', '--test-reporter=' + str(reporter), '--test-name-pattern=^' + test, judge]
            started = time.monotonic(); timeout = False
            with (directory / (phase + '.stdout')).open('wb') as stdout, (directory / (phase + '.stderr')).open('wb') as stderr:
                try:
                    code = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=120).returncode
                except subprocess.TimeoutExpired:
                    code = None; timeout = True
            output = (directory / (phase + '.stdout')).read_bytes()
            try:
                events = [json.loads(line) for line in output.decode().splitlines()]
            except (UnicodeError, ValueError):
                events = []
            summaries = [e['counts'] for e in events if e.get('type') == 'test:summary']
            counts = summaries[-1] if summaries else None
            failures = [e for e in events if e.get('type') == 'test:fail']
            receipt = {'head': head, 'command': command, 'cwd': str(ROOT), 'exit': code,
                       'elapsed_seconds': round(time.monotonic() - started, 3), 'timeout': timeout,
                       'counts': counts, 'failures': failures, 'stdout_sha256': sha(output),
                       'stderr_sha256': sha((directory / (phase + '.stderr')).read_bytes())}
            write(directory / (phase + '.execution.json'), receipt); phases[phase] = receipt
        def green(name):
            r = phases[name]; c = r['counts']
            return r['exit'] == 0 and not r['timeout'] and c and c['tests'] == c['passed'] == 1 and all(c.get(k) == 0 for k in ('failed', 'cancelled', 'skipped', 'todo'))
        red = phases['mutant']; c = red['counts']
        def designated(failure):
            error = failure.get('details', {}).get('error')
            while error and error.get('cause'):
                error = error['cause']
            return failure.get('name', '').startswith(test) and error and error.get('code') == 'ERR_ASSERTION' and error.get('name') == 'AssertionError' and marker in error.get('message', '')
        killed = (green('baseline') and green('restored') and red['exit'] == 1 and not red['timeout'] and c and
                  c['tests'] == c['failed'] == 1 and all(c.get(k) == 0 for k in ('passed', 'cancelled', 'skipped', 'todo')) and
                  len(red['failures']) == 1 and designated(red['failures'][0]))
        unchanged = all((ROOT / p).read_bytes() == value for p, value in original.items())
        row = {'id': ident, 'target': target, 'judge': judge, 'test': test, 'marker': marker,
               'source_sha256': sha(raw), 'variant_sha256': sha(variant.read_bytes()), 'judge_sha256': sha(original[judge]),
               'verdict': 'killed' if killed and unchanged else 'invalid', 'source_unchanged': unchanged, 'syntax': syntax_receipt, 'phases': phases}
        rows.append(row); write(directory / 'result.json', row)
        write(out / 'results.json', {**common, 'cases': rows, 'killed': sum(r['verdict'] == 'killed' for r in rows), 'total': len(cases)})
        print(ident + ': ' + row['verdict'], flush=True)
    return 0 if all(r['verdict'] == 'killed' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
