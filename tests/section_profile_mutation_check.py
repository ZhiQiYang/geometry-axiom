"""Q38 section-profile fault injection: every guard must have a named killer test that turns red.

Relation to proposal AC16: this gate shows that each guard has at least one named killer test that fails with a
message naming the broken clause.  It is NOT a one-to-one mapping to proposal AC16, which expects specific ACs
(AC04-AC06, AC12, ... ) to turn red.  The per-case list that --explore measured, and where it differs from AC16
(AC23 is turned red by no case; AC04-AC06 and AC24 turn red through analogous scenarios), is in
tests/release-evidence/20261010-q38-i44/ac16-per-case-red-tests.md.

Run on Linux/WSL (GCC), never edits the checkout:

    python3 tests/binaries.py build            # the model group needs a fresh model-base adapter
    python3 tests/section_profile_mutation_check.py             # all cases, enforced
    python3 tests/section_profile_mutation_check.py --list      # show the cases
    python3 tests/section_profile_mutation_check.py --explore   # report only, run the whole test class for each case
    python3 tests/section_profile_mutation_check.py --only SPM03 --only SPM04 --group native
    python3 tests/section_profile_mutation_check.py --receipt out.json --logs logs/

Two groups of single-point faults are injected into a disposable copy of the sources:

  native  C sources (geometry-core/section_profile*.inc, geometry-web/section_profile_bridge.inc): the bridge is
          compiled from the copy and tests/test_section_profile_native.py runs against the mutated bridge;
  model   the Python producer (geometry-core/modeling/section_profile.py, engine.py): tests/
          test_section_profile_modeling.py runs inside the mutated copy against the unmutated native adapter.

The baseline of each group must pass with zero skips first.  A mutant counts as KILLED only when ALL hold:

  * at least one test the case names (``tests``) fails with an AssertionError, or errors with a message that contains
    the case's ``cause`` (compiler errors, crashes without that message, timeouts and skips are not detection);
  * the log contains every ``cause`` string, so the failure message itself names the clause that was broken
    ("expected rejection 'V_PANEL_WIDTH' but the candidate was accepted", "R38: V must be -up", ...);
  * for native cases only, the recompiled mutant binary differs from the baseline binary; model cases mutate
    Python source and use the same fresh, unmutated native adapter (there is no mutant-adapter hash comparison).

Historical f0c4c71 results: 39 cases detected by AssertionError (FAIL), two model cases SPM38/SPM40
by cause-labelled ModelError (ERROR), plus one equivalent native case. Do not relabel the ERROR logs as FAIL.

A case marked ``equivalent`` is compiled and run like the others but must NOT be killed; the reason has to be given.
Exit 0 only if every case behaves as declared, 1 if a mutant survived / was mislabelled, 2 if a baseline failed,
the environment is missing, or --only / --group select no case (an unknown --only id included: it is rejected before
anything runs, because a run that selects nothing builds no baseline and would report success).
Not part of tests/run_all.py (it compiles one bridge per case), like tests/assembly_mutation_check.py;
only the selection guard is covered there, by tests/test_section_profile_mutation_check.py.
Anything that survives is a hole in the tests: add the assertion, never delete the case.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NATIVE_MODULE = 'tests.test_section_profile_native'
NATIVE_CLASS = 'SectionProfileNative'
MODEL_MODULE = 'tests.test_section_profile_modeling'
MODEL_CLASS = 'SectionProfileModeling'
# scenario_verify only accepts a registry binary that carries a source/build receipt; a disposable mutant cannot,
# and that test is about the source graph, not about any guard injected here.
EXCLUDED = {'test_source_index_typed_closure_and_display_identity'}

V = 'geometry-core/section_profile_validation.inc'
P = 'geometry-core/section_profiles.inc'
PL = 'geometry-core/section_profile_placement.inc'
CV = 'geometry-core/section_profile_conversion.inc'
BR = 'geometry-web/section_profile_bridge.inc'
MS = 'geometry-core/modeling/section_profile.py'
ME = 'geometry-core/modeling/engine.py'

# Native test methods that carry the teeth.
CONCAVE = 'test_concave_not_four_corners_and_winding'
GEOM = 'test_profile_geometry_and_coordinate_rejections'
TOUCH = 'test_touch_edges_points_and_cross_kind_overlap'
PANEL = 'test_panel_strict_width_fixed_spec_and_long_run'
AC09 = 'test_ac09_advanced_axes_and_vertex_range'
AC01 = 'test_ac01_03_08_independent_rectangles_volumes_and_scope'
SHRINK = 'test_shrink_reject_and_expand_loses_right_contact'
NAMED = 'test_named_sources_rebuild_and_explicit_dependency_transaction'
PARAM = 'test_parameter_zero_ids_types_and_fixed_material_sources_roundtrip'
DUMP = 'test_exact_dump_load_zero_ids_empty_profile_and_fail_closed'
CARD = 'test_all_cardinal_frames_and_four_host_directions_are_exact'
LIVE = 'test_live_host_follow_detach_conversion_and_atomic_delete'
HOLES = 'test_simple_holes_closed_boundary_vertical_direction_and_invalid_up'
CONV = 'test_conversion_reports_all_unsatisfied_conditions_and_zero_writes'
SHRINKHOST = 'test_live_host_shrink_lists_each_run_and_pending_reads_preserve_token'
# Model-producer test methods.
M3 = 'test_three_timber_members_and_actual_concave_reference_envelope'
MLONG = 'test_long_panel_is_one_exact_solid_in_both_orientations'
MLOCAL = 'test_local_runs_do_not_cut_other_local_or_world_mesh_grids'
MADV = 'test_advanced_native_frame_controls_world_axes_and_bounds'


def case(identifier, clause, desc, file, before, after, tests, cause, equivalent=None, group='native'):
    """before must occur exactly once in file; tests: any one of them must catch it; cause: strings the log must show."""
    return {'group': group, 'id': identifier, 'clause': clause, 'desc': desc, 'file': file, 'before': before,
            'after': after, 'tests': list(tests), 'cause': list(cause), 'equivalent': equivalent}


ACCEPT = 'expected the candidate to be accepted'
CASES = [
    case('SPM01', 'I44', 'drop the member-in-profile containment check', V,
         'if(p&&sp_outside_regions(&p->outline,&m->rect,outside)){', 'if(0&&p&&sp_outside_regions(&p->outline,&m->rect,outside)){',
         [CONCAVE, GEOM], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    case('SPM02', 'I45', 'drop the member-overlap check', V,
         'if(sp_intersection(&s->members[i],&s->members[j],&overlap)){',
         'if(0&&sp_intersection(&s->members[i],&s->members[j],&overlap)){',
         [TOUCH, NAMED], ["expected rejection 'V_PROFILE_OVERLAP'"]),
    case('SPM03', 'R36', 'u overlap uses <= : edge-sharing members become overlapping', V,
         'return r->min_u<r->max_u&&r->min_v<r->max_v;', 'return r->min_u<=r->max_u&&r->min_v<r->max_v;',
         [TOUCH], [ACCEPT, 'V_PROFILE_OVERLAP']),
    case('SPM04', 'R36', 'v overlap uses <= : members touching along v become overlapping', V,
         'return r->min_u<r->max_u&&r->min_v<r->max_v;', 'return r->min_u<r->max_u&&r->min_v<=r->max_v;',
         [TOUCH], [ACCEPT, 'V_PROFILE_OVERLAP']),
    case('SPM05', 'I46/D40', 'panel width w < 915 becomes w <= 915', P,
         'm.width>=sp_panel_spec.width_max', 'm.width>sp_panel_spec.width_max',
         [PANEL], ["expected rejection 'V_PANEL_WIDTH'"]),
    case('SPM06', 'I46', 'panel width lower bound 1 becomes 0', P,
         'm.width<1||', 'm.width<0||',
         [PANEL], ["expected rejection 'V_PANEL_WIDTH'"]),
    case('SPM07', 'D40', 'panel spec identity is no longer checked', P,
         'strcmp(spec,SP_PANEL_SPEC)', '0&&strcmp(spec,SP_PANEL_SPEC)',
         [GEOM], ["expected rejection 'panel requires calcium-silicate-6'"]),
    case('SPM08', 'D40', 'spec thickness 6 becomes 7', P, '6,915,1830}', '7,915,1830}',
         [PANEL], ['D40/R36: calcium-silicate-6 is 6 mm thick']),
    case('SPM09', 'D40', 'spec w_max 915 becomes 914', P, '6,915,1830}', '6,914,1830}',
         [PANEL], [ACCEPT, 'V_PANEL_WIDTH']),
    case('SPM10', 'I43', 'drop the outline validity check', P,
         'if(!poly_loop_is_valid(&p.outline))return sp_error("I43: profile',
         'if(0&&!poly_loop_is_valid(&p.outline))return sp_error("I43: profile',
         [GEOM], ["expected rejection 'I43'"]),
    case('SPM11', 'D37', 'run length accepts a D26 material source', P,
         '(length&&out->kind==ENG_MATERIAL)', '(0&&length&&out->kind==ENG_MATERIAL)',
         [PARAM], ["expected rejection 'unsupported dimension source'"]),
    case('SPM12', 'D36', 'material A/B field identity is no longer enforced', P,
         'out->field!=(field?ENG_B:ENG_A)', '0&&out->field!=(field?ENG_B:ENG_A)',
         [PARAM], ["rejected, but not for 'D36'"]),
    case('SPM13', 'I51', 'scene records no longer need the section-profile/1 declaration', P,
         'if(!sp_scene_required){scene_error(', 'if(0&&!sp_scene_required){scene_error(',
         [DUMP], ['I51: a scene with a missing requires section-profile/1 marker must be rejected']),
    case('SPM14', 'I46', 'timber orientation is not validated', P,
         '(strcmp(orientation,"A-u")&&strcmp(orientation,"A-v"))', '0',
         [GEOM], ["expected rejection 'timber orientation must be A-u or A-v'"]),
    case('SPM15', 'I46', 'panel orientation is not validated', P,
         'if(strcmp(orientation,"thickness-v")&&strcmp(orientation,"thickness-u"))return', 'if(0)return',
         [GEOM], ["expected rejection 'panel orientation must be thickness-v or thickness-u'"]),
    case('SPM16', 'R38', 'V = +up instead of -up', PL,
         'r->frame.axis_v=sp_scaled(r->up,-1);', 'r->frame.axis_v=sp_scaled(r->up,1);',
         [CARD], ['R38: V must be -up']),
    case('SPM17', 'R38', 'negative directions (-u,-v) lose their sign', PL,
         '(r->dir%2)?-1:1', '1',
         [CARD], ['R38: N must equal the run direction d']),
    case('SPM18', 'R38', 'dir +u/-u and +v/-v pick the wrong host axis', PL,
         'r->dir<2?host.axis_u:host.axis_v', 'r->dir<2?host.axis_v:host.axis_u',
         [CARD], ['R38: N must equal the run direction d']),
    case('SPM19', 'I48', 'p,q may lie outside the host range', PL,
         'bool inside=boundary_contains_point(&region,(SurfacePoint2){r->p,r->q});', 'bool inside=true;',
         [HOLES], ["expected rejection 'outside closed host range'"]),
    case('SPM20', 'I48', 'up need not be perpendicular to the run direction', PL,
         'bool perpendicular=vector_dot(r->up,r->frame.normal)==0;', 'bool perpendicular=true;',
         [HOLES], ["expected rejection 'perpendicular'"]),
    case('SPM21', 'I48/D1', 'simple-placement origin is not range-checked', PL,
         'bool origin=coord_in_range(r->frame.origin.x)&&coord_in_range(r->frame.origin.y)&&coord_in_range(r->frame.origin.z);',
         'bool origin=true;',
         [HOLES], ["rejected, but not for 'origin exceeds D1'"]),
    case('SPM22', 'R38', 'origin x component swaps p and q', PL,
         'host.origin.x+r->p*host.axis_u.x+r->q*host.axis_v.x', 'host.origin.x+r->q*host.axis_u.x+r->p*host.axis_v.x',
         [LIVE], ['R38/R40: O = o_H + p*U_H + q*V_H must follow the live host']),
    case('SPM23', 'D38', 'advanced->simple conversion ignores the host plane', CV,
         'plane=vector_dot(delta,host.normal)==0', 'plane=true',
         [CONV], ["rejected, but not for 'origin not in host plane'"]),
    case('SPM24', 'D38', 'advanced->simple conversion accepts any V as up', CV,
         'bool legal_up=vector_dot(up,r.frame.normal)==0&&vector_dot(up,up)==1;', 'bool legal_up=true;',
         [CONV, CARD], [],
         equivalent='an advanced frame is accepted only by surface_frame_is_valid (unit cardinal axes, V perpendicular to N), '
                    'so up=-V is always a legal up: the "V has a legal up" condition of D38 can never fail here'),
    case('SPM25', 'D38', 'advanced->simple conversion takes the last host direction regardless of N', CV,
         'if(vector_equal(axes[i],r.frame.normal))dir=i;', 'dir=i;',
         [CARD], ['D38: advanced->simple must recover dir/p/q/up']),
    case('SPM26', 'I49', 'PROFILE_CONTACT_LOST is never reported', BR,
         'if(!p||!m->resolved||!next||!n->resolved)return false;', 'return false;',
         [SHRINK], ['PROFILE_CONTACT_LOST']),
    case('SPM27', 'I44', 'outside-region split drops the right-hand remainder', V,
         'if(cursor<r->max_u)out[n++]', 'if(0&&cursor<r->max_u)out[n++]',
         [CONCAVE], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    case('SPM28', 'I49', 'a member may reference a deleted profile', V,
         'if(!p){sp_error("I49: member %u references missing profile %u"', 'if(0&&!p){sp_error("I49: member %u references missing profile %u"',
         [NAMED], ["expected rejection 'I49'"]),
    case('SPM29', 'I49', 'a run may reference a deleted profile', V,
         'if(!p){sp_error("I49: run %u references missing profile %u"', 'if(0&&!p){sp_error("I49: run %u references missing profile %u"',
         [NAMED], ["expected rejection 'I49'"]),
    case('SPM30', 'I47/D1', 'generated run vertices are not range-checked', V,
         'if(!coord_in_range(point.x)||!coord_in_range(point.y)||!coord_in_range(point.z)){r->range_error=true;',
         'if(0&&(!coord_in_range(point.x)||!coord_in_range(point.y)||!coord_in_range(point.z))){r->range_error=true;',
         [AC09], ["expected rejection 'I47/I48/D1'"]),
    case('SPM31', 'R36', 'A-v / thickness-u swap width and height the wrong way round', V,
         'Coord width=m->rotated?m->b:m->a,height=m->rotated?m->a:m->b;', 'Coord width=m->rotated?m->a:m->b,height=m->rotated?m->b:m->a;',
         [AC01, AC09], [ACCEPT, 'V_PROFILE_']),
    case('SPM32', 'D36', 'panel orientation thickness-u is read as thickness-v', P,
         'm.rotated=!strcmp(orientation,"thickness-u");', 'm.rotated=!strcmp(orientation,"thickness-v");',
         [PANEL], [ACCEPT, 'V_PROFILE_OUTSIDE']),
    case('SPM33', 'D40/R37', 'the 1830 mm sheet length is misused as an upper bound for the run length', V,
         'r->length_resolved=sp_resolve_dimension(w,&r->length_source,&target,&r->length);',
         'r->length_resolved=sp_resolve_dimension(w,&r->length_source,&target,&r->length)&&r->length<=sp_panel_spec.sheet_length;',
         [PANEL], [ACCEPT, 'RUN_LENGTH_INVALID']),
    case('SPM34', 'I51', 'scene load accepts a duplicate profile id', P,
         'if(!strcmp(tokens[1],"profile")&&!sp_profile(w,id))ok=', 'if(!strcmp(tokens[1],"profile"))ok=',
         [DUMP], ['I51: a scene with a duplicate profile id record must be rejected']),
    case('SPM35', 'I49', 'section-profile records may be injected line by line outside an atomic load', P,
         'if(!g_parsing_scene_file){scene_error(', 'if(0&&!g_parsing_scene_file){scene_error(',
         [DUMP], ['I49: section-profile records must not be injected line by line']),
    # Discard one positive-area outside region, independent of the shared poly_contains_rect implementation.
    # The former substitution stopped being a fault after GEO-257 fixed that shared predicate.
    case('SPM41', 'I44', 'a single positive-area outside region is incorrectly treated as contained', V,
         'return n;', 'return n>1?n:0;',
         [CONCAVE], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    case('SPM42', 'I47/D1', 'only the start vertex of a run is range-checked, not the far end', V,
         'Point3 point=sp_point(r,p->outline.v[v].u,p->outline.v[v].v,end?r->length:0);',
         'Point3 point=sp_point(r,p->outline.v[v].u,p->outline.v[v].v,0);',
         [AC09], ["expected rejection 'I47/I48/D1'"]),
    # ---- model group: the Python producer (R37 / R39 / D39) against the unmutated native adapter ----
    case('SPM36', 'R37', 'the reference envelope becomes the bounding rectangle of the outline (L shape lost)', MS,
         'placement = dict(frame, outline=deepcopy(run["outline"]))',
         'placement = dict(frame, outline=(lambda o: [[min(p[0] for p in o), min(p[1] for p in o)], '
         '[max(p[0] for p in o), min(p[1] for p in o)], [max(p[0] for p in o), max(p[1] for p in o)], '
         '[min(p[0] for p in o), max(p[1] for p in o)]])(run["outline"]))',
         [M3], ['R37: exact mesh volume of the envelope object'], group='model'),
    case('SPM37', 'R39', 'the reference envelope is counted as material volume', MS,
         'details["material_volume_mm3"] = "0" if reference else obj["volume_mm3"]',
         'details["material_volume_mm3"] = obj["volume_mm3"]',
         [M3], ['R37/R39: the envelope is a reference object and carries no material volume'], group='model'),
    case('SPM38', 'R37/D40', 'a panel is cut at the 1830 mm sheet length', MS,
         'geometry = geo.extrusion_geometry(placement, 0, run["length"], source)',
         'geometry = geo.extrusion_geometry(placement, 0, min(run["length"], 1830) if member["kind"] == "panel" else run["length"], source)',
         [MLONG], ['Native dimensions and derived exact member volume disagree'], group='model'),
    case('SPM39', 'R36/R37', 'member rectangles are read with u and v swapped', MS,
         'u0, v0, u1, v1 = member["rect"]', 'v0, u0, v1, u1 = member["rect"]',
         [MADV], ['R36/R37: bounds of the'], group='model'),
    case('SPM40', 'D39', 'an unplaced (local) run is cut by the world grid', ME,
         'profile_grid = (grid if run["coordinate_space"] == "world" else',
         'profile_grid = (grid if True else',
         [MLOCAL], ['A section-profile object must produce one complete solid'], group='model'),
]


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts):
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def posix_only():
    if os.name != 'posix':
        raise SystemExit('Use GCC on Linux/WSL; no security settings are changed.')
    import resource
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.RLIM_INFINITY))


def copy_sources(destination: Path, python=False):
    """Disposable copy: C sources (for the bridge) and, for the model group, the Python tree and the axiom text."""
    for parent in (ROOT, ROOT / 'geometry-core', ROOT / 'geometry-web'):
        paths = parent.iterdir() if parent == ROOT else parent.rglob('*')
        for path in paths:
            if path.is_file() and path.suffix in ('.c', '.h', '.inc') and 'vendor' not in path.parts:
                target = destination / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    if python:
        for pattern in ('tests/*.py', 'geometry-core/*.py', 'geometry-core/modeling/*.py', 'geometry-web/*.py'):
            for path in ROOT.glob(pattern):
                target = destination / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        shutil.copyfile(ROOT / '公理層.md', destination / '公理層.md')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_bridge(source: Path, exe: Path):
    result = subprocess.run(['cc', '-std=c11', '-O2', str(source / 'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)],
                            capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError('compile failed: ' + (result.stderr or result.stdout)[-1500:])


NATIVE_CHILD = ('import sys, unittest\n'
                'from unittest.mock import patch\n'
                'import importlib\n'
                'module = importlib.import_module(%r)\n'
                'exe = sys.argv.pop(1)\n'
                'with patch.object(module, "find_bridge", return_value=exe):\n'
                '    unittest.main(module=None, argv=["x", "-v", *sys.argv[1:]])\n') % NATIVE_MODULE
PLAIN_CHILD = 'import sys, unittest\nunittest.main(module=None, argv=["x", "-v", *sys.argv[1:]])\n'
ALL = {}
LOG_DIR = None


def test_names(module_name, class_name, excluded, root):
    import importlib
    import unittest
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True
    try:
        module = importlib.import_module(module_name)
        return [name for name in unittest.TestLoader().getTestCaseNames(getattr(module, class_name)) if name not in excluded]
    finally:
        sys.path.remove(str(root))
        for key in [k for k in sys.modules if k == 'tests' or k.startswith('tests.')]:
            del sys.modules[key]


def run_native(exe: Path, tests, timeout=900):
    names = ['%s.%s.%s' % (NATIVE_MODULE, NATIVE_CLASS, name) for name in (tests or ALL['native'])]
    run = subprocess.run([sys.executable, '-c', NATIVE_CHILD, str(exe), *names], cwd=ROOT,
                         env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=timeout)
    return run.returncode, run.stdout + run.stderr


def run_model(tree: Path, model_base: str, tests, timeout=900):
    names = ['%s.%s.%s' % (MODEL_MODULE, MODEL_CLASS, name) for name in (tests or ALL['model'])]
    env = dict(os.environ, GEOMETRY_MODEL_BASE=model_base, PYTHONDONTWRITEBYTECODE='1')
    run = subprocess.run([sys.executable, '-c', PLAIN_CHILD, *names], cwd=tree, env=env,
                         capture_output=True, text=True, timeout=timeout)
    return run.returncode, run.stdout + run.stderr


FAILED = re.compile(r'^(FAIL|ERROR): (\w+) \(', re.M)


def failures(log):
    return sorted({(kind, name) for kind, name in FAILED.findall(log)})


def first_failure(log):
    match = re.search(r'^(?:AssertionError|\w+Error): (.*)$', log, re.M)
    return match.group(1)[:300] if match else None


def mutate_file(tree: Path, case):
    target = tree / case['file']
    original = target.read_bytes()
    before = case['before'].encode('utf-8')
    assert original.count(before) == 1, (case['id'], 'mutation anchor changed or not unique')
    target.write_bytes(original.replace(before, case['after'].encode('utf-8')))


def prepare_native(case, base_source: Path, work: Path):
    """Build one mutant bridge; returns (exe, error)."""
    source = work / case['id']
    shutil.copytree(base_source, source)
    exe = work / ('bridge-' + case['id'])
    try:
        mutate_file(source, case)
        compile_bridge(source, exe)
    except Exception as error:  # noqa: BLE001 - reported as an invalid mutant
        return exe, str(error)
    finally:
        shutil.rmtree(source, ignore_errors=True)
    return exe, None


def verdict(case, code, log):
    found = failures(log)
    record = {'exit': code, 'failed': ['%s %s' % item for item in found]}
    if LOG_DIR:
        (LOG_DIR / (case['id'] + '.log')).write_text(log, encoding='utf-8')
    if code != 0:
        record['first_failure'] = first_failure(log)
    expected = set(case['tests'])
    caused = all(text in log for text in case['cause'])
    assertions = {name for kind, name in found if kind == 'FAIL'}
    # An ERROR whose message names the cause (e.g. the producer's own ModelError) is detection; a bare error is not.
    detected = assertions | ({name for kind, name in found if kind == 'ERROR'} if case['cause'] and caused else set())
    if 'skipped=' in log:
        record.update(verdict='blocked', note='skips are not detection')
    elif code == 0:
        record['verdict'] = 'equivalent' if case['equivalent'] else 'survived'
    elif not detected:
        record.update(verdict='crashed', note='only unexplained errors, no assertion failure')
    elif not (expected & detected):
        record.update(verdict='wrong-killer', note='failed %s, expected one of %s' % (sorted(detected), sorted(expected)))
    elif not caused:
        record.update(verdict='unlabelled', note='failure log lacks %s' % case['cause'])
    else:
        record['verdict'] = 'killed'
    if case['equivalent'] and record['verdict'] != 'equivalent':
        record['verdict'] = 'not-equivalent'
    return record


def judge_native(case, exe, error, baseline_hash, explore):
    record = {'id': case['id'], 'group': 'native', 'clause': case['clause'], 'desc': case['desc']}
    if error:
        record.update(verdict='invalid', note=error[-400:])
        return record
    record['binary_sha256'] = sha256(exe)
    if record['binary_sha256'] == baseline_hash:
        record.update(verdict='invalid', note='mutant binary equals baseline')
        return record
    try:
        code, log = run_native(exe, None if explore else case['tests'])
    except subprocess.TimeoutExpired:
        record.update(verdict='blocked', note='timeout')
        return record
    record.update(verdict(case, code, log))
    return record


def judge_model(case, model_tree: Path, model_base: str, work: Path, explore):
    record = {'id': case['id'], 'group': 'model', 'clause': case['clause'], 'desc': case['desc']}
    tree = work / case['id']
    shutil.copytree(model_tree, tree)
    try:
        mutate_file(tree, case)
        code, log = run_model(tree, model_base, None if explore else case['tests'])
    except subprocess.TimeoutExpired:
        record.update(verdict='blocked', note='timeout')
        return record
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    record.update(verdict(case, code, log))
    return record


def model_base_path():
    sys.path.insert(0, str(ROOT))
    from tests import binaries
    info = binaries.inspect_one(binaries.BY_NAME['model-base'], path=os.environ.get('GEOMETRY_MODEL_BASE'))
    if info.state != 'fresh':
        raise SystemExit('environment (exit 2): the model group needs a fresh model-base adapter '
                         '(python3 tests/binaries.py build, or set GEOMETRY_MODEL_BASE): ' + info.reason)
    return str(info.path)


def select_cases(only, groups):
    """The cases --only / --group pick.  An unknown id or an empty selection is a ValueError: with no case there is no
    baseline run and all([]) is True, so a mistyped id used to exit 0 without testing anything."""
    known = [c['id'] for c in CASES]
    unknown = sorted(set(only) - set(known))
    if unknown:
        raise ValueError('unknown --only case id(s): %s; valid ids: %s'
                         % (', '.join(repr(item) for item in unknown), ', '.join(known)))
    cases = [c for c in CASES if c['group'] in groups and (not only or c['id'] in only)]
    if not cases:
        where = ', '.join('%s is in group %s' % (c['id'], c['group']) for c in CASES if c['id'] in only)
        raise ValueError('no case selected: --only %s with --group %s matches nothing (%s)'
                         % (' '.join(only) or '(none)', ' '.join(groups), where or 'no case in these groups'))
    return cases


def main(argv=None):
    global LOG_DIR
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--explore', action='store_true', help='run the whole test class for each case, do not enforce expectations')
    parser.add_argument('--only', action='append', default=[])
    parser.add_argument('--group', choices=['native', 'model'], action='append', default=[])
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--receipt')
    parser.add_argument('--logs', help='directory that receives the full test log of every case')
    args = parser.parse_args(argv)
    ids = [c['id'] for c in CASES]
    assert len(ids) == len(set(ids)), 'duplicate case ids'
    for item in CASES:
        assert item['tests'] and (item['cause'] or item['equivalent']), (item['id'], 'a case needs killer tests and a cause')
    groups = args.group or ['native', 'model']
    try:
        cases = select_cases(args.only, groups)
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        for item in CASES:
            print(item['id'], item['group'], item['clause'], item['desc'])
        return 0
    if args.logs:
        LOG_DIR = Path(args.logs)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    posix_only()
    ALL['native'] = test_names(NATIVE_MODULE, NATIVE_CLASS, EXCLUDED, ROOT)
    ALL['model'] = test_names(MODEL_MODULE, MODEL_CLASS, set(), ROOT)
    records = []
    problems = []
    with tempfile.TemporaryDirectory(prefix='section-profile-mutations-') as directory:
        work = Path(directory)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs))
        native_cases = [c for c in cases if c['group'] == 'native']
        model_cases = [c for c in cases if c['group'] == 'model']
        if native_cases:
            base_source = work / 'base-source'
            copy_sources(base_source)
            digest = tree_digest(base_source)
            baseline = work / 'bridge-baseline'
            compile_bridge(base_source, baseline)
            baseline_hash = sha256(baseline)
            code, log = run_native(baseline, None)
            print('native baseline: exit', code, flush=True)
            if code != 0 or 'skipped=' in log:
                print(log[-3000:])
                problems.append('native baseline must pass with zero skips before any mutant is judged')
            else:
                built = list(pool.map(lambda c: (c,) + prepare_native(c, base_source, work), native_cases))
                records += list(pool.map(lambda item: judge_native(item[0], item[1], item[2], baseline_hash, args.explore), built))
                if tree_digest(base_source) != digest:
                    problems.append('the shared base copy changed while mutants were judged')
        if model_cases:
            model_base = model_base_path()
            model_tree = work / 'model-tree'
            copy_sources(model_tree, python=True)
            digest = tree_digest(model_tree)
            code, log = run_model(model_tree, model_base, None)
            print('model baseline: exit', code, flush=True)
            if code != 0 or 'skipped=' in log:
                print(log[-3000:])
                problems.append('model baseline must pass with zero skips before any mutant is judged')
            else:
                records += list(pool.map(lambda c: judge_model(c, model_tree, model_base, work, args.explore), model_cases))
                if tree_digest(model_tree) != digest:
                    problems.append('the shared model copy changed while mutants were judged')
        pool.shutdown()
    summary = {}
    for record in records:
        summary[record['verdict']] = summary.get(record['verdict'], 0) + 1
        print(json.dumps(record, ensure_ascii=False), flush=True)
    result = {'schema': 'section-profile-mutations/1', 'summary': summary, 'results': records}
    if args.receipt:
        Path(args.receipt).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'summary': summary}, ensure_ascii=False))
    for problem in problems:
        print('PROBLEM:', problem)
    if problems:
        return 2
    if args.explore:
        return 0
    return 0 if all(r['verdict'] in ('killed', 'equivalent') for r in records) else 1


if __name__ == '__main__':
    sys.exit(main())
