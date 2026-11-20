"""Q38j-b isolated JS mutations; terminal designated assertions alone kill.

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
VIEW = 'geometry-web/model-viewer.js'
SOURCE = 'geometry-web/source-inspector.js'
VIEW_JUDGE = 'tests/test_space_profile_view.js'
REPLAY = 'geometry-web/reference-workspace.js'
REPLAY_JUDGE = 'tests/test_space_profile_replay.js'
REPLAY_KEYS = 'const materialKeys = ["timbers", "profile_runs"].filter(key => Object.hasOwn(model.input, key));'
PROFILE_DRAW = "if(visibility.timbers!==false)for(const object of result.profile_runs?.derived?.objects||[])if(object.role==='geometry')objects.push({...object,color:'#ab865f',opacity:1,label:'斷面拉伸件'});"
CASES = [
    ('Q38JB01-remove-profile-display', VIEW, PROFILE_DRAW, '', VIEW_JUDGE, 'Q38JB_PROFILE_DISPLAY:', 'Q38JB_PROFILE_DISPLAY'),
    ('Q38JB02-remove-profile-content-roots', SOURCE, ',...(input.profile_runs||[]).map(r=>key(r.kind,r.id))', '',
     VIEW_JUDGE, 'Q38JB_RUN_CHANGED:', 'Q38JB_RUN_CHANGED'),
    ('Q38JB03-display-reference-envelope', VIEW,
     "if(object.role==='geometry')objects.push({...object,color:'#ab865f',opacity:1,label:'斷面拉伸件'});",
     "objects.push({...object,color:'#ab865f',opacity:1,label:'斷面拉伸件'});",
     VIEW_JUDGE, 'Q38JB_ENVELOPE_NOT_DRAWN:', 'Q38JB_ENVELOPE_NOT_DRAWN'),
    ('Q38JB04-remove-independent-profile-verification', REPLAY, REPLAY_KEYS,
     'const materialKeys = ["timbers"].filter(key => Object.hasOwn(model.input, key));', REPLAY_JUDGE,
     'Q09 /3 profile native verification failure preserves nonempty current project', 'Q38JB_REPLAY_PROFILE_REFUSED'),
    ('Q38JB05-skip-schema3-timber-verification', REPLAY, REPLAY_KEYS,
     'const materialKeys = ["timbers", "profile_runs"].filter(key => Object.hasOwn(model.input, key) && (key !== "timbers" || model.result.schema === "geometry-space-preview/2"));',
     REPLAY_JUDGE, 'Q09 /3 timber native verification failure preserves nonempty current project', 'Q38JB_REPLAY_TIMBER_REFUSED'),
    ('Q38JB_UI_WORLD', 'geometry-web/space-workspace.js', 'if(run.coordinateSpace!=="world"){unavailable++;continue;}', 'if(run.coordinateSpace!=="world"||id===4){unavailable++;continue;}', 'tests/test_space_profile_ui.js', 'Q38JB-UI01 all world runs, including zero, are candidates without inferred relation', 'Q38JB-UI01 world candidates include 0 and unrelated 4'),
    ('Q38JB_UI_PRESELECT', 'geometry-web/space-workspace.js', '<input type="checkbox" data-sm-profile-run="${esc(run.id)}">', '<input type="checkbox" data-sm-profile-run="${esc(run.id)}" checked>', 'tests/test_space_profile_ui.js', 'Q38JB-UI01 all world runs, including zero, are candidates without inferred relation', 'Q38JB-UI01 no profile preselection'),
    ('Q38JB_UI_DROP_ROOTS', 'geometry-web/space-workspace.js', 'input.profile_runs=selectedRuns.sort((a,b)=>a-b).map(id=>({kind:"profile-run",id}));', '/* mutant: omit selected profile roots */', 'tests/test_space_profile_ui.js', 'Q38JB-UI02 explicit profile roots only, omitted when none, faces cannot silently discard', 'Q38JB-UI02 exact sorted explicit roots'),
    ('Q38JB_UI_CAPABILITY', 'geometry-web/space-workspace.js', 'if(!supportsProfileRuns)throw new Error(', 'if(false&&!supportsProfileRuns)throw new Error(', 'tests/test_space_profile_ui.js', 'Q38JB-UI03 section profile capability alone never submits profile preview', 'Q38JB-UI03 /3 capability required before POST'),
    ('Q38JB_UI_SOURCE_REVISION', 'geometry-web/space-workspace.js', '||dump.revision!==profileRevision||checkedDump.revision!==profileRevision||profileReadRevision(profileAfter)!==profileRevision)', ')', 'tests/test_space_profile_ui.js', 'Q38JB-UI05 source read revision race refuses candidates even if dump is identical', 'Q38JB-UI05 changed revision cannot populate candidates'),
    ('Q38JB_UI_REFERENCE_ROW', 'geometry-web/space-workspace.js', 'const members=result.profile_runs?.derived?.objects?.filter(object=>object.role==="geometry")||[];', 'const members=result.profile_runs?.derived?.objects||[];', 'tests/test_space_profile_ui.js', 'Q38JB-UI09 preview preserves exact selected package and warns of unchecked overlap', 'Q38JB-UI09 reference envelope is not a member row'),
    ('Q38JB_UI_PRECOMMIT', 'geometry-web/space-workspace.js', 'if(state.input.profile_runs&&state.source.kind==="scene"&&!await checkProfileSource(state.source,seq))return;', '/* mutant: omit precommit source check */', 'tests/test_space_profile_ui.js', 'Q38JB-UI12 precommit revision check prevents model write', 'Q38JB-UI12 changed revision cannot write model'),
    ('Q38JB_UI_INVALIDATE', 'geometry-web/space-workspace.js', 'state.controller?.abort();state.sequence++;state.previewRevision=-1;state.phase="stale";$("smConfirmFaces").checked=false;', '/* mutant: omit immediate invalidation */', 'tests/test_space_profile_ui.js', 'Q38JB-UI16 source change invalidates now and preserves saved-model views', 'Q38JB-UI16 history change invalidates immediately'),
    ('R430_ACTIVATION_DUMP_REVISION', 'geometry-web/space-workspace.js', ' || dump.revision !== line.revision)', ')',
     'tests/test_space_library_actions.js', 'anything beyond the single activation step leaves the source stale', 'dump revision mismatched: token kept'),
    ('R430_ACTIVATION_PROFILE_REVISION', 'geometry-web/space-workspace.js', 'profiles.revision !== line.revision || ', '',
     'tests/test_space_library_actions.js', 'anything beyond the single activation step leaves the source stale', 'profile revision mismatched: token kept'),
    ('R430_ACTIVATION_HISTORY_REPIN', 'geometry-web/space-workspace.js', 'if (recorded) source.history_token = next;', '/* mutant: leave the activation token stale */',
     'tests/test_space_library_actions.js', 'activation keeps a current scene source usable for the next step', 'R430_ACTIVATION_HISTORY_REPINNED'),
    ('R430_TIMBER_DISCLOSURE_WITHDRAWAL', 'geometry-web/space_model_test.js', "await click('#smTimberSettings > summary');", "await click('#smTimberCandidateDetails > summary');",
     'tests/test_space_test_floor.js', 'R430 timber driver uses the shipped candidate disclosure without changing its census', 'R430_TIMBER_LIVE_DISCLOSURE'),
    ('R430_UI_CREATE_HASH', 'geometry-web/space-workspace.js', 'if(record.input.profile_runs)await GeometryProject.validateSpaceModelHashes(record);', '/* mutant: do not verify a new model source receipt */',
     'tests/test_space_profile_ui.js', 'R430-UI20 new model verifies raw source and receipt before writing history', 'R430_CREATE_SOURCE_HASH_GUARD'),
    ('R430_UI_EDIT_HASH', 'geometry-web/space-workspace.js', '          await GeometryProject.validateSpaceModelHashes(record);', '          /* mutant: do not verify an edited model source receipt */',
     'tests/test_space_profile_ui.js', 'R430-UI21 height edit verifies raw source and receipt before replacing the saved model', 'R430_EDIT_SOURCE_HASH_GUARD'),
    ('R430_UI_CREATE_HASH_OWNER', 'geometry-web/space-workspace.js', '      assertCreationOwner(owner,pin?.revision??null);', '      /* mutant: omit create owner check after hashing */',
     'tests/test_space_profile_ui.js', 'R430-UI22 new model rechecks every owner after the asynchronous source hash', 'R430_CREATE_HASH_AWAIT_OWNER: context'),
    ('R430_UI_EDIT_HASH_OWNER', 'geometry-web/space-workspace.js', '          assertCreationOwner(owner,owner.evidence.nativeRevision);', '          /* mutant: omit edit owner check after hashing */',
     'tests/test_space_profile_ui.js', 'R430-UI23 height edit rechecks owners and original record after the asynchronous source hash', 'R430_EDIT_HASH_AWAIT_OWNER: history'),
    ('R430_UI_CREATE_HASH_PREVIEW', 'geometry-web/space-workspace.js', '      if(seq!==state.sequence||revision!==state.revision||state.previewRevision!==revision||state.source!==source)throw new Error("設定或預覽已改變，未建立模型；請重新預覽。");', '      /* mutant: omit new-model preview recheck */',
     'tests/test_space_profile_ui.js', 'R430-UI22 new model rechecks every owner after the asynchronous source hash', 'R430_CREATE_HASH_AWAIT_OWNER: settings'),
    ('R430_UI_EDIT_HASH_PREVIEW', 'geometry-web/space-workspace.js', '          if(seq!==state.sequence||revision!==state.revision||state.previewRevision!==revision||state.source!==source||state.editing!==editing)\n            throw new Error("設定、預覽或原模型已改變，未更新模型；請重新預覽。");', '          /* mutant: omit edited-model preview recheck */',
     'tests/test_space_profile_ui.js', 'R430-UI23 height edit rechecks owners and original record after the asynchronous source hash', 'R430_EDIT_HASH_AWAIT_OWNER: settings'),
    ('R430_UI_EDIT_HASH_RECORD', 'geometry-web/space-workspace.js', '          assertEditableRecord();', '          /* mutant: omit original saved record recheck */',
     'tests/test_space_profile_ui.js', 'R430-UI23 height edit rechecks owners and original record after the asynchronous source hash', 'R430_EDIT_HASH_AWAIT_OWNER: saved record'),
    ('Q38JB_STORE_IMPLEMENTATION', 'geometry-web/project-store.js', 'withProfileRuns = Object.hasOwn(i || {}, "profile_runs");', 'withProfileRuns = false;', 'tests/test_space_profile_store.js', 'Q38JB native profile and timber packages roundtrip in the dedicated format', 'Q38JB_IMPLEMENTATION'),
    ('Q38JB_STORE_SELECTION', 'geometry-web/project-store.js', 'if (withProfileRuns) validateProfileRunModel(record);', '/* mutant: omit profile validator */', 'tests/test_space_profile_store.js', 'Q38JB selected profile roots are nonempty typed unique uint32 and plan only', 'Q38JB_SELECTION'),
    ('Q38JB_STORE_TIMBERS', 'geometry-web/project-store.js', 'if (withTimbers) validateTimberModel(record);', 'if (withTimbers && !withProfileRuns) validateTimberModel(record);', 'tests/test_space_profile_store.js', 'Q38JB wrapper schemas and all optional package presence are exact', 'Q38JB_SCHEMA3_TIMBER_GUARD'),
    ('Q38JB_STORE_ENVELOPE', 'geometry-web/project-store.js', 'if ([...envelopes.values()].some(count => count !== 1) ||', 'if (false ||', 'tests/test_space_profile_store.js', 'Q38JB every selected run has exactly one zero-material reference envelope', 'Q38JB_ENVELOPE'),
    ('Q38JB_STORE_MATERIAL', 'geometry-web/project-store.js', 'result.summary.profile_material_volume_mm3 !== volume.toString() ||', '', 'tests/test_space_profile_store.js', 'Q38JB profile summary is exact decimal material with unchecked overlap', 'Q38JB_SUMMARY'),
    ('Q38JB_STORE_HASHES', 'geometry-web/project-store.js', 'async function validateProfileRunHashes(manifest) {', 'async function validateProfileRunHashes(manifest) { return;', 'tests/test_space_profile_store.js', 'Q38JB source and package hashes are verified during pack and unpack', 'Q38JB_HASH_PACK'),
    ('Q38JB_STORE_SOURCE', 'geometry-web/project-store.js', 'pkg.definitions.base_scene !== snapshot.canonical_scene || ', '', 'tests/test_space_profile_store.js', 'Q38JB profile request roots source and mandatory capability are exact', 'Q38JB_SAME_SOURCE'),
    ('R430_STORE_LITERAL_SOURCE_WITHDRAWAL', 'geometry-web/project-store.js',
     'pkg.definitions.base_scene !== snapshot.canonical_scene || ', 'pkg.definitions.base_scene !== input.base_scene || ',
     'tests/test_space_profile_store.js', 'R430 raw editor snapshot is accepted only with its native canonical source', 'R430_RAW_SOURCE_ACCEPTED'),
    ('R430_STORE_RAW_HASH', 'geometry-web/project-store.js',
     'await sha(new TextEncoder().encode(record.input.base_scene)) !== snapshot.input_sha256 ||', 'false ||',
     'tests/test_space_profile_store.js', 'R430 source receipt hashes are checked before a model can be committed', 'R430_RAW_HASH_BOUND'),
    ('R430_STORE_CANONICAL_HASH', 'geometry-web/project-store.js',
     'await sha(new TextEncoder().encode(snapshot.canonical_scene)) !== record.source.scene_hash ||', 'false ||',
     'tests/test_space_profile_store.js', 'R430 source receipt hashes are checked before a model can be committed', 'R430_CANONICAL_HASH_BOUND'),
    ('R430_UPDATE_RAW_BINDING', 'geometry-web/model-update.js',
     'next.input.base_scene !== source.scene ||', 'false ||',
     'tests/test_space_profile_update.js', 'R430 controller binds the complete profile candidate to the selected raw source', 'R430_UPDATE_RAW_BINDING'),
    ('R430_UPDATE_RECEIPT_BINDING', 'geometry-web/model-update.js',
     'next.result.source_snapshot.input_sha256 !== candidate.current_scene_sha256 ||', 'false ||',
     'tests/test_space_profile_update.js', 'R430 controller binds the complete profile candidate to the selected raw source', 'R430_UPDATE_RECEIPT_BINDING'),
    ('R430_UPDATE_CANONICAL_BINDING', 'geometry-web/model-update.js',
     'await digest(next.result.source_snapshot.canonical_scene) !== next.result.source_sha256', 'false',
     'tests/test_space_profile_update.js', 'R430 controller binds the complete profile candidate to the selected raw source', 'R430_UPDATE_CANONICAL_BINDING'),
    ('Q38JB_STORE_EMBEDDED', 'geometry-web/project-store.js', '(source.boundary_id === null ? !placed.embedded :', '(false ? !placed.embedded :',
     'tests/test_space_profile_store.js', 'Q38JB native zero identities empty profiles and sorted multiple roots remain valid', 'Q38JB_EMBEDDED_SOURCE'),
    ('Q38JB_STORE_FALSE_EMBEDDED', 'geometry-web/project-store.js', '(source.boundary_id === null ? !placed.embedded :', '(source.boundary_id === null ? false :',
     'tests/test_space_profile_store.js', 'Q38JB profile-only records retain the exact positive boundary source', 'Q38JB_SOURCE_BOUNDARY'),
    ('Q38JB_UI_RENDER_SOURCE_PROFILE_CANDIDATES', 'geometry-web/space-workspace.js',
     'renderTimberCandidates(source);renderProfileCandidates(source);', 'renderTimberCandidates(source);',
     'tests/test_space_profile_ui.js', 'Q38JB-UI19 admitted source renders its selectable profile controls through the shipped source renderer',
     'Q38JB-UI19 admitted source exposes all world profile controls'),
    ('Q38JB_K3_KEEP_COVERED_PROOF', SOURCE,
     'return scoped(ledger.continuitySummary({roots:ledger.judgeRoots(record.sourceIdentity,graph||null)}));',
     "return scoped({token:'unknown',text:'物件延續性未知',listed:[]});",
     VIEW_JUDGE, 'Q38JB_K3_SCOPE:', 'Q38JB_K3_COVERED_PROOF'),
    ('Q38JB_K3_LIMIT_PROOF_SCOPE', SOURCE,
     "value.token==='proved'?'已追蹤根延續已證明；拉伸件延續未知'", "value.token==='proved'?'物件延續已證明'",
     VIEW_JUDGE, 'Q38JB_K3_SCOPE:', 'Q38JB_K3_PROOF_SCOPE'),
    ('Q38JB_K3_UNTRACKED_ROOTS', SOURCE,
     "return (record?.input?.profile_runs||[]).map(ref=>({kind:'profile-run',id:ref.id}));", 'return [];',
     VIEW_JUDGE, 'Q38JB_K3_ROOTS:', 'Q38JB_K3_UNTRACKED'),
    ('R430_REPLAY_SOURCE_SNAPSHOT_REPLY', REPLAY,
     'if (Object.hasOwn(rebuilt, "source_snapshot") !== Object.hasOwn(original, "source_snapshot") ||\n        !sameModelData(rebuilt.source_snapshot, original.source_snapshot))',
     'if (false)', REPLAY_JUDGE,
     'Q08 profile replay binds the exact raw and canonical source receipt before committing',
     'R430_REPLAY_SOURCE_SNAPSHOT_REPLY: different raw geometry'),
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
    paths = sorted(closure | {c[1] for c in CASES} | {c[4] for c in CASES} |
                   {'tests/q38j_workspace_mutations.py', 'tests/q38j_profile_fixture.py', 'tests/test_space_profile_runs.py',
                    'tests/test_section_profile_modeling.py', 'geometry-web/space_modeling.py', 'geometry-web/start_local.py', 'tests/binaries.py'})
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
        syntax = subprocess.run(['node', '--check', str(variant)], capture_output=True)
        (directory / 'syntax.stdout').write_bytes(syntax.stdout); (directory / 'syntax.stderr').write_bytes(syntax.stderr)
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
               'verdict': 'killed' if killed and unchanged else 'invalid', 'source_unchanged': unchanged, 'phases': phases}
        rows.append(row); write(directory / 'result.json', row)
        write(out / 'results.json', {**common, 'cases': rows, 'killed': sum(r['verdict'] == 'killed' for r in rows), 'total': len(cases)})
        print(ident + ': ' + row['verdict'], flush=True)
    return 0 if all(r['verdict'] == 'killed' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
