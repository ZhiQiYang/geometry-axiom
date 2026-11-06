"""R06/main archive merge: named source withdrawals, real Node assertion kills.

Run from the merged repository:
  python tests/diagnostics/r363_project_store_merge_mutations.py --out /tmp/r363-store-mutations

The production checkout is never modified. Each mutant has its own temporary
project-store.js and read-only symlinked dependencies. Syntax errors, timeouts,
missing anchors and unrelated failures do not count as a kill.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


SCENE = 'const SCENE_CAPABILITIES = [ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, ASSEMBLY_CAPABILITY, GENERATION_CAPABILITY, SUBDIVISION_CAPABILITY, SECTION_CAPABILITY, PANEL_FILL_CAPABILITY, CARD_CAPABILITY, BAY_REPEAT_CAPABILITY, IDENTITY_CAPABILITY];'
RETURN = 'return [...supported, Features.GRID_SCHEMA, Features.GRID_RULE_SCHEMA, Features.GRID_CARD_CAPABILITY, ...shared, Features.ROOM_CAPABILITY, Features.ROOM_HISTORY_CAPABILITY, Features.ROOM_DISPLAY_CAPABILITY, Features.ROOM_CANDIDATE_CAPABILITY, EVIDENCE_CAPABILITY, EVIDENCE_V2_CAPABILITY, SCENARIO_CAPABILITY, CASE_CAPABILITY];'
CASES = [
    ('R363_PS01_DROP_IDENTITY', SCENE, SCENE.replace(', IDENTITY_CAPABILITY', ''), 'R363_PS_CAPABILITY_UNION', 'R363_PS_TEN_CAPABILITIES'),
    ('R363_PS02_OLD_NINE_LIMIT', 'capabilities.length > SCENE_CAPABILITIES.length', 'capabilities.length > 9', 'R363_PS_CAPABILITY_UNION', 'R363_PS_TEN_CAPABILITIES'),
    ('R363_PS03_DROP_BAY', SCENE, SCENE.replace(', BAY_REPEAT_CAPABILITY', ''), 'R363_PS_CAPABILITY_UNION', 'R363_PS_TEN_CAPABILITIES'),
    ('R363_PS04_DROP_EVIDENCE_V2', RETURN, RETURN.replace(', EVIDENCE_V2_CAPABILITY', ''), 'R363_PS_READER_OVERLOAD', 'R363_PS_LEGACY_geometry-evidence-links/2'),
    ('R363_PS05_SKIP_NATIVE_PROFILE', "nativeProfiles.includes('panel-fill-native/1')&&", 'true&&', 'R363_PS_PANEL_PROFILE', 'R363_PS_PROFILE_CREDENTIAL'),
    ('R363_PS06_FORCE_ROOM_ON_19', 'hasRoomCandidate && manifest.format !== ROOM_CANDIDATE_FORMAT', 'hasRoomCandidate !== (manifest.format === ROOM_CANDIDATE_FORMAT)', 'R363_PS_SHARED_19 round trips', 'R363_PS_OWNER_COMBINATION'),
    ('R363_PS07_DROP_REPEAT_FORMAT', 'if((repeat || manifest.requiredCapabilities?.includes(BAY_REPEAT_CAPABILITY)) &&', 'if(false &&', 'R363_PS_SHARED_19 keeps', 'R363_PS_REPEAT_DEFINITION'),
    ('R363_PS08_IDENTITY_FORCES_ENGINEERING', 'engineeringSceneCapabilities(scene).length || manifest.models?.some(modelRequiresEngineering)', 'sceneCapabilities(scene).length || manifest.models?.some(modelRequiresEngineering)', 'R363_PS_IDENTITY_LEGACY', 'R363_PS_IDENTITY_LEGACY'),
    ('R363_PS09_DROP_DEIDENTIFICATION', 'if (modelIdentity().deidentifiedBase(normalizedBase) !== normalizedBase)', 'if (false)', 'R363_PS_MODEL_UNION', 'R363_PS_MODEL_DEIDENTIFIED'),
    ('R363_PS10_DROP_MODEL_BAY_REJECTION', 'if (m.capabilities.includes(BAY_REPEAT_CAPABILITY) || sceneCapabilities(p.definitions.base_scene).includes(BAY_REPEAT_CAPABILITY))', 'if (false)', 'R363_PS_MODEL_UNION', 'R363_PS_MODEL_REPEAT_PACKAGE'),
    ('R363_PS11_WIDEN_PRIMARY_LIMIT', '!list(d.primaries,12,p=>', '!list(d.primaries,13,p=>', 'R363_PS_DRAFT_LIMIT', 'R363_PS_DRAFT_OVER_primaries'),
    ('R363_PS12_DROP_GENERIC_NOOP', 'if (result.history_changed === false) {', 'if (false) {', 'R363_PS_NOOP', 'R363_PS_NO_PHANTOM_HISTORY'),
    ('R363_PS13_ALLOW_MARKER_ONLY_HOST', '       hasRepeatDefinitions(manifest,scene)&&\n', '       true&&\n', 'R363_PS_PANEL_PROFILE', 'R363_PS_REAL_REPEAT'),
    ('R363_PS14_OLD_NATIVE_42_LIMIT', 'available.length>43', 'available.length>42', 'R363_PS_NATIVE_LIMIT', 'R363_PS_NATIVE_43'),
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    production = root / 'geometry-web/project-store.js'
    source_bytes = production.read_bytes()
    source = source_bytes.decode('utf-8')
    test = root / 'tests/test_r363_project_store_merge.js'
    result = {'productionSha256': digest(source_bytes), 'testSha256': digest(test.read_bytes()), 'cases': []}

    def run(label: str, target: Path, pattern: str | None = None):
        command = ['node', '--test', '--test-reporter=tap']
        if pattern:
            command.append('--test-name-pattern=' + pattern)
        command.append(str(test))
        environment = {**os.environ, 'R363_PROJECT_STORE_ROOT': str(target)}
        try:
            process = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=45)
            stdout, stderr, code = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code = str(error.stdout or ''), str(error.stderr or ''), 'timeout'
        (out / (label + '.stdout')).write_text(stdout)
        (out / (label + '.stderr')).write_text(stderr)
        return code, stdout, stderr

    baseline, stdout, stderr = run('baseline', root)
    result['baselineExit'] = baseline
    if baseline != 0 or '# tests 10' not in stdout or '# pass 10' not in stdout or '# skipped 0' not in stdout:
        result['status'] = 'baseline-not-green'
    else:
        for name, old, new, pattern, assertion in CASES:
            if source.count(old) != 1:
                result['cases'].append({'id': name, 'status': 'missing-or-ambiguous-anchor', 'count': source.count(old)})
                continue
            mutant = source.replace(old, new)
            with tempfile.TemporaryDirectory(prefix='r363-store-') as temporary:
                temporary = Path(temporary)
                web = temporary / 'geometry-web'
                web.mkdir()
                for entry in (root / 'geometry-web').iterdir():
                    if entry.name != 'project-store.js':
                        (web / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
                target = web / 'project-store.js'
                target.write_text(mutant)
                syntax = subprocess.run(['node', '--check', str(target)], capture_output=True, text=True, timeout=45)
                if syntax.returncode != 0:
                    result['cases'].append({'id': name, 'status': 'syntax-error', 'stderr': syntax.stderr})
                    continue
                code, stdout, stderr = run(name, temporary, pattern)
                killed = code == 1 and 'ERR_ASSERTION' in stdout and assertion in stdout and pattern in stdout
                result['cases'].append({'id': name, 'status': 'killed/exact-assertion' if killed else 'not-killed',
                                        'exit': code, 'assertion': assertion, 'mutantSha256': digest(mutant.encode())})
        restored, stdout, stderr = run('restored', root)
        result['restoredExit'] = restored
        unchanged = production.read_bytes() == source_bytes
        result['checkoutUnchanged'] = unchanged
        result['status'] = 'passed' if (restored == 0 and '# pass 10' in stdout and '# skipped 0' in stdout and unchanged
            and len(result['cases']) == len(CASES) and all(row['status'] == 'killed/exact-assertion' for row in result['cases'])) else 'failed'
    (out / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
