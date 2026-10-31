"""R11 named native withdrawals: compile, green -> tagged red -> restore/green.

Run with Python and a C11 gcc/clang-compatible CC. Builds and receipts stay under
--output (default: a fresh system temp directory), never the user's bridge.
Compilation failures, crashes, unrelated assertions and skips are not kills.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = 'geometry-web/timber_edit_bridge.inc'


def case(name):
    return 'TimberEditNative.test_' + name


MUTATIONS = [
    ('R11-N01-typed-source-read', BRIDGE,
     'if(binding){dimension->sourced=true;', 'if(false&&binding){dimension->sourced=true;',
     case('C02_recipe_preserves_parameter_fields_versions_and_override'), 'typed-source-read'),
    ('R11-N02-recipe-override', BRIDGE,
     'call->recipe=recipe->definition;return true;',
     'call->recipe=recipe->definition;call->recipe.dimensions[0].has_override=false;return true;',
     case('C02_recipe_preserves_parameter_fields_versions_and_override'), 'recipe-source-preserved'),
    ('R11-N03-intermediate-evaluation', BRIDGE,
     'ok=timber_edit_apply_patch(candidate,&call->patches[i]);',
     'ok=timber_edit_apply_patch(candidate,&call->patches[i])&&world_revalidate(candidate);',
     case('C04_all_fields_precede_validation_and_one_undo_restores_all'), 'all-fields-before-evaluation'),
    ('R11-N04-final-validation', BRIDGE,
     'if(ok)ok=world_revalidate(candidate);', 'if(ok)ok=true;',
     case('C04_invalid_third_target_rejects_the_entire_candidate'), 'invalid-final-is-atomic'),
    ('R11-N05-owner-eligibility', BRIDGE,
     'if(assembly_owned(w,id))return "I42:', 'if(false&&assembly_owned(w,id))return "I42:',
     case('C05_native_owned_and_mixed_selection_are_blocked_whole'), 'native-owner-guard'),
    ('R11-N06-recipe-revision', BRIDGE,
     '!recipe||recipe->revision!=g_definition_revision||recipe->boundary!=call->pending.boundary',
     '!recipe||recipe->boundary!=call->pending.boundary',
     case('C06_revision_and_recipe_expire_even_after_identical_dump_undo_redo'), 'recipe-revision-bound'),
    ('R11-N07-token-family', 'geometry-web/engineering_bridge.inc',
     'g_preview.engineering_batch && !g_preview.timber_batch &&', 'g_preview.engineering_batch &&',
     case('C06_token_families_cancel_and_duplicate_confirm_are_isolated'), 'token-family-confirm'),
    ('R11-N08-noop', BRIDGE,
     'bool no_op=valid&&world_definitions_equal(&transaction->before,&transaction->after);',
     'bool no_op=false;', case('C03_empty_and_identical_fields_are_noop_without_history'), 'noop-without-token'),
    ('R11-N09-private-id', BRIDGE, 'if(private_id)fputs(', 'if(false&&private_id)fputs(',
     case('C01_id_zero_read_private_preview_and_single_publish'), 'private-preview-id'),
    ('R11-N10-in-place-order', BRIDGE,
     'if(patch->direction_set)w->wood.anchors[index].length_direction=patch->direction;',
     'w->wood.anchors[index].order=++w->app.next_order;if(patch->direction_set)w->wood.anchors[index].length_direction=patch->direction;',
     case('C04_all_fields_precede_validation_and_one_undo_restores_all'), 'in-place-order'),
    ('R11-N11-strict-fields', BRIDGE,
     'if(!geo_json_keys(j,fields,"","A,B,role,priority,direction"))', 'if(!geo_json_is_object(j,fields))',
     case('C12_strict_schema_duplicate_target_controls_and_full_uint64'), 'strict-fields'),
    ('R11-N12-uint64', BRIDGE,
     'value>(UINT64_MAX-(uint64_t)(*p-\'0\'))/10', 'value>(INT64_MAX-(uint64_t)(*p-\'0\'))/10',
     case('C12_strict_schema_duplicate_target_controls_and_full_uint64'), 'full-uint64-revision'),
    ('R11-N13-same-face', BRIDGE,
     'if(!surface||surface->boundary_id!=call->pending.boundary)', 'if(!surface)',
     case('C12_same_project_face_recipe_and_capacity_are_native_guards'), 'same-face-guard'),
    ('R11-N14-source-identity', BRIDGE,
     'bool no_op=valid&&world_definitions_equal(&transaction->before,&transaction->after);',
     'bool no_op=valid&&!memcmp(transaction->before.wood.timbers,transaction->after.wood.timbers,sizeof transaction->before.wood.timbers);',
     case('C02_equal_effective_different_source_is_a_real_edit'), 'source-identity-is-definition'),
    ('R11-N15-explicit-direct', BRIDGE,
     'if(eng_same_target(&w->wood.engineering.bindings[i].target,&target)){',
     'if(false&&eng_same_target(&w->wood.engineering.bindings[i].target,&target)){',
     case('C02_explicit_direct_removes_only_the_selected_source_binding'), 'explicit-direct-unbind'),
    ('R11-N16-private-diagnostic', BRIDGE,
     'if(!pending->creating){js_string(message);return;}', 'if(true){js_string(message);return;}',
     case('C01_private_handle_covers_dependencies_geometry_and_diagnostics'), 'private-diagnostic-handle'),
    ('R11-N17-uint32-wrap', BRIDGE,
     'WORLD_NEXT_ID(call->pending.created_id,g_world.wood.timbers,g_world.wood.timber_count,false);',
     'call->pending.created_id=0;for(size_t i=0;i<g_world.wood.timber_count;++i)if(g_world.wood.timbers[i].id>call->pending.created_id)call->pending.created_id=g_world.wood.timbers[i].id;++call->pending.created_id;',
     case('C01_uint32_wrap_skips_every_live_id_before_single_publish'), 'private-id-wrap-safe'),
    ('R11-N18-priority-dimension-confusion', BRIDGE,
     'if(token>=0&&!timber_edit_priority(j,token,&patch->priority))',
     'if(token>=0&&!eng_coord(j,token,&patch->priority,true))',
     case('C10_priority_is_positive_integer_not_a_dimension'), 'priority-is-not-dimension'),
    ('R11-N19-saved-override', 'geometry-core/engineering.inc',
     'if(b->has_override){if(!eng_source_json(&b->override_value,override,sizeof override))',
     'if(false&&b->has_override){if(!eng_source_json(&b->override_value,override,sizeof override))',
     case('C02_recipe_preserves_parameter_fields_versions_and_override'), 'saved-source-roundtrip'),
    ('R11-N20-priority-precision', BRIDGE,
     'printf("\\\"%lld\\\"",(long long)priority);',
     'printf("\\\"%.0f\\\"",(double)priority);',
     case('C10_full_int64_priority_text_and_recipe_are_exact'), 'exact-priority-text'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, log, env=None, timeout=180):
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        record = {'command': command, 'cwd': str(cwd), 'returncode': result.returncode,
                  'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        record = {'command': command, 'cwd': str(cwd), 'returncode': None, 'error': str(error)}
    log.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--only', action='append', choices=[item[0] for item in MUTATIONS])
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix='geometry-r11-mutations-'))
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = output/'source'
    if source.exists():
        raise SystemExit('Use a new output directory; existing mutation evidence is never overwritten')
    shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.exe', 'feedback'))
    compiler = shlex.split(os.environ.get('CC', 'gcc'))
    baseline = output/('baseline.exe' if os.name == 'nt' else 'baseline')
    build_command = compiler + ['-std=c11', '-O0', 'geometry-web/web_bridge.c', '-lm', '-o', str(baseline)]
    built = run(build_command, source, output/'baseline-build.json')
    if built['returncode'] != 0:
        raise SystemExit('Baseline compilation blocked; see baseline-build.json')
    dependencies = subprocess.run(compiler + ['-std=c11', '-MM', 'geometry-web/web_bridge.c'], cwd=source,
                                  capture_output=True, text=True, check=True).stdout
    names = sorted({str(Path(part).as_posix()) for part in shlex.split(dependencies.replace('\\\n', ' ').split(':', 1)[1])})
    closure = {name: sha(source/name) for name in names}
    (output/'closure.json').write_text(json.dumps(closure, indent=2), encoding='utf-8')
    oracle = output/'baseline-oracles.json'
    env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(baseline), GEOMETRY_TIMBER_ORACLES=str(oracle))
    env.pop('GEOMETRY_TIMBER_RECEIPTS', None)
    baseline_run = run([sys.executable, 'tests/test_timber_edit.py'], source, output/'baseline-tests.json', env)
    if baseline_run['returncode'] != 0:
        raise SystemExit('Baseline tests failed; no mutations counted')
    baseline_oracles = json.loads(oracle.read_text())
    if baseline_oracles['skipped'] or baseline_oracles['errors']:
        raise SystemExit('Baseline contained skips/errors; no mutations counted')
    selected = [item for item in MUTATIONS if not args.only or item[0] in args.only]
    results = []
    summary = {'schema': 'r11-native-mutations/1', 'baseline_binary_sha256': sha(baseline),
               'closure_sha256': hashlib.sha256(json.dumps(closure, sort_keys=True).encode()).hexdigest(),
               'test_sha256': sha(source/'tests/test_timber_edit.py'), 'results': results}
    for name, filename, old, new, test, tag in selected:
        directory = output/name
        directory.mkdir()
        path = source/filename
        original = path.read_bytes()
        text = original.decode('utf-8')
        if text.count(old) != 1 or tag not in baseline_oracles['reached']:
            raise SystemExit(f'{name}: unique source anchor or reached baseline oracle missing')
        path.write_bytes(text.replace(old, new, 1).encode('utf-8'))
        binary = directory/('mutant.exe' if os.name == 'nt' else 'mutant')
        record = {'name': name, 'test': test, 'oracle': tag, 'file': filename,
                  'before_sha256': hashlib.sha256(original).hexdigest(), 'mutant_source_sha256': sha(path),
                  'replacement': {'old': old, 'new': new}}
        try:
            command = compiler + ['-std=c11', '-O0', 'geometry-web/web_bridge.c', '-lm', '-o', str(binary)]
            compiled = run(command, source, directory/'build.json')
            if compiled['returncode'] != 0:
                record['status'] = 'blocked-compile'
            else:
                record['binary_sha256'] = sha(binary)
                mutant_oracle = directory/'oracles.json'
                mutant_env = dict(env, GEOMETRY_TEST_BRIDGE=str(binary), GEOMETRY_TIMBER_ORACLES=str(mutant_oracle))
                red = run([sys.executable, 'tests/test_timber_edit.py', test], source, directory/'red.json', mutant_env)
                observed = json.loads(mutant_oracle.read_text()) if mutant_oracle.is_file() else {}
                evidence = red.get('stderr', '')
                killed = (red['returncode'] == 1 and observed.get('tests') == 1 and
                          observed.get('failures') == 1 and observed.get('errors') == 0 and
                          observed.get('skipped') == 0 and ('KILLER['+tag+']') in evidence)
                record['status'] = 'killed' if killed else 'survived-or-unrelated'
        finally:
            path.write_bytes(original)
            record['restored_source_sha256'] = sha(path)
        # Rebuild the restored source, so the green cannot accidentally run the mutant.
        restored = directory/('restored.exe' if os.name == 'nt' else 'restored')
        restored_build = run(compiler + ['-std=c11', '-O0', 'geometry-web/web_bridge.c', '-lm', '-o', str(restored)],
                             source, directory/'restored-build.json')
        if restored_build['returncode'] == 0:
            record['restored_binary_sha256'] = sha(restored)
            restore_env = dict(env, GEOMETRY_TEST_BRIDGE=str(restored), GEOMETRY_TIMBER_ORACLES=str(directory/'restored-oracles.json'))
            green = run([sys.executable, 'tests/test_timber_edit.py', test], source, directory/'restored-green.json', restore_env)
            record['restored_green'] = green['returncode'] == 0
        else:
            record['restored_green'] = False
        if not record['restored_green']:
            record['status'] = 'blocked-restore'
        results.append(record)
        (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(name, record['status'], 'restore=' + str(record['restored_green']), flush=True)
    print('Receipts:', output/'summary.json')
    return 0 if all(item['status'] == 'killed' and item['restored_green'] for item in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
