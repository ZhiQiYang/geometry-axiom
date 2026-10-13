#!/usr/bin/env python3
"""Copy and bind sources; inspect retained archives. Does not compile or run tests."""
import argparse
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--resume-preparation', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    home = Path(__file__).resolve().parent
    target = home / 'source'
    if target.exists() and not args.resume_preparation:
        raise RuntimeError('immutable prepared source already exists; use a new preparation directory')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True)
    if status:
        raise RuntimeError('preparation requires clean source')
    paths = set()

    def local_closure(path):
        relative = path.resolve().relative_to(repo)
        if str(relative) in paths:
            return
        paths.add(str(relative))
        for include in re.findall(rb'^\s*#\s*include\s+"([^"]+)"', path.read_bytes(), re.M):
            child = (path.parent / include.decode()).resolve()
            if not child.is_file():
                raise RuntimeError('missing local include: ' + str(child))
            local_closure(child)

    local_closure(repo / 'geometry-web/web_bridge.c')
    c_paths = sorted(paths)
    paths.update(['tests/__init__.py', 'tests/_bridge.py', 'tests/binaries.py',
                  'tests/test_grid_subdivision_oracle.py', 'tests/test_grid_system_contract.py',
                  'tests/fixtures/grid_subdivision_vectors.json'])
    paths.update(str(p.relative_to(repo)) for p in (repo / 'geometry-core/modeling').glob('*.py'))
    target.mkdir(exist_ok=args.resume_preparation)
    rows = []
    for relative in sorted(paths):
        data = (repo / relative).read_bytes()
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if dest.read_bytes() != data:
                raise RuntimeError('prepared copy differs: ' + relative)
        else:
            dest.write_bytes(data)
        rows.append({'path': relative, 'bytes': len(data), 'sha256': digest(data),
                     'nativeIncludeClosure': relative in c_paths})
    oracle = (target / 'tests/test_grid_subdivision_oracle.py').read_text()
    def line(text, method):
        matches = [i for i, row in enumerate(oracle.splitlines(), 1) if row.strip() == text]
        if len(matches) > 1:
            node = next(n for n in ast.walk(ast.parse(oracle)) if isinstance(n, ast.FunctionDef) and n.name == method)
            matches = [i for i in matches if node.lineno <= i <= node.end_lineno]
        if len(matches) != 1:
            raise RuntimeError(('assertion must be unique', text, matches))
        return matches[0]
    prefix = 'tests.test_grid_subdivision_oracle.NativeSubdivisionOracle.'
    specs = [
        ('M62-1', 'exact divisibility guard bypass', 'geometry-core/grid_subdivision.inc',
         'if(grid_axis_pitch(&s->axis[a])%r->divisions[a])',
         'if(0 && grid_axis_pitch(&s->axis[a])%r->divisions[a])',
         'test_invalid_divisions_source_and_cell_guards_refuse_without_partial_state',
         'self.assertFalse(result.get("ok") and result.get("preview", {}).get("valid", True), (command, result))',
         '600/7 accepted instead of DIVISION_NOT_EXACT; original subTest divisions=(7, 2)'),
        ('M62-2', 'omit saved rule records while retaining highwater', 'geometry-core/grid_subdivision.inc',
         'for(size_t i=0;i<s->rule_count;++i){const GridSubdivisionRule *r=&s->rules[i];\n        fprintf(out,"grid-source-rule',
         'for(size_t i=0;i<0;++i){const GridSubdivisionRule *r=&s->rules[i];\n        fprintf(out,"grid-source-rule',
         'test_native_save_requires_capability_and_load_failures_preserve_live_world',
         'self.assertIn("grid-source-rule 0 key 1", before[0])',
         'saved native dump lacks source rule identity; fails before a falsely successful roundtrip'),
        ('M62-3', 'omit systemId at typed rule dereference', 'geometry-core/grid_subdivision.inc',
         'if(s->id!=ref->system_id || !p || p->id!=pid)',
         'if(!p || p->id!=pid)',
         'test_same_rule_key_in_another_source_cannot_rebind_an_existing_reference',
         'self.assertFalse(result.get("ok") and result.get("preview", {}).get("valid", True), (command, result))',
         'same ruleKey in source 1 accepts rebinding a source 0 formal guide'),
        ('M62-4', 'bypass face/hole clipping while retaining parent-cell segment', 'geometry-core/grid_subdivision_query.inc',
         'if (placement) {\n                    GuideLine guide={0};',
         'if (false && placement) {\n                    GuideLine guide={0};',
         'test_hole_clipping_preserves_line_identity_and_all_visible_segments',
         'self.assertEqual(normalized(segments), normalized(by_line[identity]["segments"]))',
         'literal expected hole-split endpoint multiset differs from an unclipped cell line'),
        ('M62-5', 'bypass lexical capability encounter guard for default highwater', 'geometry-core/grid_subdivision.inc',
         'if(g_rule_scene_encountered && !g_rule_scene_required)return false;',
         'if(false && g_rule_scene_encountered && !g_rule_scene_required)return false;',
         'test_new_allocator_input_syntax_requires_capability_even_when_final_state_is_default',
         'self.assertFalse(rejected["ok"], rejected)',
         'new highwater syntax without requires marker replaces live World despite default resulting allocator'),
    ]
    mutations = []
    patches = home / 'patches'
    patches.mkdir(exist_ok=args.resume_preparation)
    for identifier, desc, relative, old, new, method, assertion, why in specs:
        before = (target / relative).read_bytes()
        if before.count(old.encode()) != 1:
            raise RuntimeError(('mutation anchor must occur once', identifier))
        after = before.replace(old.encode(), new.encode(), 1)
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                    fromfile='a/' + relative, tofile='b/' + relative))
        (patches / (identifier + '.diff')).write_text(patch)
        mutations.append({'id': identifier, 'description': desc, 'path': relative,
            'old': old, 'new': new, 'beforeSha256': digest(before), 'afterSha256': digest(after),
            'diffSha256': digest(patch.encode()), 'test': prefix + method,
            'expectedAssertionLine': line(assertion, method), 'expectedSemanticFailure': why})
    counts = {}
    for relative in ['tests/test_grid_subdivision_oracle.py', 'tests/test_grid_system_contract.py']:
        tree = ast.parse((target / relative).read_text())
        counts[relative] = sum(isinstance(n, ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(tree))
    if list(counts.values()) != [41, 13]:
        raise RuntimeError(('original test inventory changed', counts))
    plan = {'schema': 'geometry-sgr62-isolated-plan/1', 'preparedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'repo': str(repo), 'head': head, 'gitStatusShort': status, 'sourceFiles': rows,
        'testCounts': counts, 'mutations': mutations,
        'compileFlags': ['-std=c11', '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-pie', '-no-pie'],
        'executionStatus': 'NOT_EXECUTED', 'nativeBuildsPlanned': 6,
        'baselineScope': '41 unchanged subdivision tests plus 13 unchanged grid-system contract tests; not historical 152',
        'restoreScope': 'after each mutant, restore private active binary to pristine bytes and rerun its same original method; unchanged pristine source avoids repeating full 54'}
    write_json(home / 'plan.json', plan)
    wanted = '00766856e9148ff432cf7826e4b9958f29c48d30f1cd9b7aad3a38b54bf0c430'
    archives = []
    for archive in sorted((repo / 'tests/release-evidence').rglob('*.tar.gz')):
        record = {'path': str(archive.relative_to(repo)), 'sha256': digest(archive.read_bytes()),
                  'membersHashed': 0, 'matchingKnownSanitizerRaw': [], 'sanitizerNamedMembers': []}
        with tarfile.open(archive) as stream:
            for member in stream:
                if not member.isfile():
                    continue
                data = stream.extractfile(member).read()
                sha = digest(data)
                record['membersHashed'] += 1
                if sha == wanted:
                    record['matchingKnownSanitizerRaw'].append({'path': member.name, 'sha256': sha})
                if any(term in member.name.lower() for term in ['saniti', 'asan', 'ubsan']):
                    record['sanitizerNamedMembers'].append({'path': member.name, 'sha256': sha, 'bytes': len(data)})
        archives.append(record)
    old_mutants = json.loads((repo / 'tests/mutants_results.json').read_text())
    old_summary = [{'id': key, 'description': row.get('desc'), 'verdict': row.get('verdict'),
                    'head': row.get('execution', {}).get('head'), 'testCommand': row.get('execution', {}).get('test_command')}
                   for key, row in old_mutants.items()]
    write_json(home / 'prior-evidence-audit.json', {'knownSanitizerRawSha256': wanted,
        'tmpRawExists': Path('/tmp/subdivision-repeat-only-sanitizers-valid.log').exists(),
        'archives': archives, 'trackedMutationCount': len(old_mutants),
        'trackedMutationFileSha256': digest((repo / 'tests/mutants_results.json').read_bytes()),
        'trackedMutationSummary': old_summary,
        'boundary': 'ordinary scene mutations do not certify the five SGR62 faults; absent raw remains unknown'})
    print(json.dumps({'head': head, 'filesCopied': len(rows), 'testCounts': counts, 'mutationsPrepared': len(mutations),
          'sanitizerHashMatches': sum(len(a['matchingKnownSanitizerRaw']) for a in archives), 'nativeOrTestsExecuted': False}))


if __name__ == '__main__':
    main()
