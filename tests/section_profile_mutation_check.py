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

  native  W section-profile policy, K exact complement and H protocol/bridge adapters: the bridge is
          compiled from the copy and tests/test_section_profile_native.py runs against the mutated bridge;
  model   the producer of the R37/R39/D39 solids: tests/test_section_profile_modeling.py runs inside the
          mutated copy.  GEO-261 left geometry-core/modeling/section_profile.py and engine.py as 3- and 17-line
          facades; the producer is now W geometry_woodworking/section_profile.py (member/envelope requests,
          R39 metadata), K geometry_kernel (one exact arrangement per coordinate domain) and the W native
          region sources the model-base adapter evaluates.  A Python case runs against the unmutated fresh
          adapter.  A case that patches native code (SPM36, SPM39) rebuilds model-base from its own mutated copy
          through tests/binaries.py, so the adapter is fresh for exactly that copy.

A case is one fault.  Where GEO-261 enforces the same rule in more than one layer, the case patches every
layer (``more``), as M11 of geometry-core/card-reference/mutations.py does, so the injected fault is main's
fault and not only a different error code.  Every anchor must occur exactly once.  The main -> GEO-261 anchor
table is in geometry-core/SECTION-PROFILE-NATIVE-CONTRACT.md.

The baseline of each group must pass with zero skips first.  A mutant counts as KILLED only when ALL hold:

  * a method the case names (``tests``) has one terminal AssertionError or explicitly allowed error type;
  * that same exception's complete str(exception) contains every ``cause`` string, naming the broken clause
    ("expected rejection 'V_PANEL_WIDTH' but the candidate was accepted", "R38: V must be -up", ...).
    Printed stdout, traceback source, other methods and separate subtest exceptions cannot supply causes.
    Missing/duplicate/malformed exception records or exit/count inconsistencies block detection;
  * for native cases, and for model cases that patch native code, the recompiled mutant binary (bridge or
    model-base adapter) differs from its baseline binary; a Python-only model case uses the same fresh,
    unmutated adapter as the model baseline (there is no adapter hash comparison for it).

Historical f0c4c71 results: 39 cases detected by AssertionError (FAIL), two model cases SPM38/SPM40
by cause-labelled ModelError (ERROR), plus one equivalent native case. Do not relabel the ERROR logs as FAIL.

A case marked ``equivalent`` is compiled and run like the others but must NOT be killed; the reason has to be given.
Exit 0 only if every case behaves as declared, 1 if a mutant survived / was mislabelled, 2 if a baseline failed,
the environment is missing, or --only / --group select no case (an unknown --only id included: it is rejected before
anything runs, because a run that selects nothing builds no baseline and would report success), or an anchor of a
selected case does not occur exactly once (checked before anything is copied or compiled).
Not part of tests/run_all.py (it compiles one bridge per case), like tests/assembly_mutation_check.py;
the selection and exception-evidence guards are covered by tests/test_section_profile_mutation_check.py.
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

V = P = PL = CV = 'geometry-templates/woodworking/native/section_profile.c'
H = 'geometry-core/section_profiles.inc'
K = 'geometry-core/kernel/geometry.c'
BR = 'geometry-web/section_profile_bridge.inc'
# Model producer after GEO-261 (main 4b975a3d: geometry-core/modeling/section_profile.py and engine.py).
WP = 'geometry-templates/woodworking/geometry_woodworking/section_profile.py'
WS = 'geometry-templates/woodworking/native/section_profile_sources.c'
KE = 'geometry-core/geometry_kernel/evaluate.py'
KG = 'geometry-core/geometry_kernel/geometry.py'
NATIVE_SUFFIXES = ('.c', '.h', '.inc')
MODEL_DIRECTORIES = ('geometry-core/geometry_kernel', 'geometry-app/geometry_app',
                  'geometry-templates/woodworking/geometry_woodworking', 'tests/fixtures')
# The collector records type(exc).__module__ + '.' + __qualname__, i.e. where the class is defined, never the
# alias it was imported through.  GEO-261 defines ModelError in H (geometry_app.model_common); modeling.common
# re-exports that same class object as a compatibility facade, so a ModelError raised via either import path is
# reported under this one name.
MODEL_ERROR = 'geometry_app.model_common.ModelError'

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


def case(identifier, clause, desc, file, before, after, tests, cause, equivalent=None, group='native', error_types=(),
         more=()):
    """Every (file, before) occurs once; one named method's terminal exception must contain every cause string.

    ``more`` holds further (file, before, after) patches of the same fault, one per additional layer."""
    patches = [[file, before, after], *[list(item) for item in more]]
    return {'group': group, 'id': identifier, 'clause': clause, 'desc': desc, 'file': file, 'before': before,
            'after': after, 'patches': patches, 'tests': list(tests), 'cause': list(cause), 'equivalent': equivalent,
            'error_types': list(error_types)}


def patches_native(case):
    return any(Path(file).suffix in NATIVE_SUFFIXES for file, _, _ in case['patches'])


ACCEPT = 'expected the candidate to be accepted'
CASES = [
    case('SPM01', 'I44', 'drop the member-in-profile containment check', V,
         'if(p&&wood_sp_outside_regions(&p->outline,&m->rect,outside)){', 'if(0&&p&&wood_sp_outside_regions(&p->outline,&m->rect,outside)){',
         [CONCAVE, GEOM], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    case('SPM02', 'I45', 'drop the member-overlap check', V,
         'if(wood_sp_intersection(&s->members[i],&s->members[j],&overlap)){',
         'if(0&&wood_sp_intersection(&s->members[i],&s->members[j],&overlap)){',
         [TOUCH, NAMED], ["expected rejection 'V_PROFILE_OVERLAP'"]),
    case('SPM03', 'R36', 'u overlap uses <= : edge-sharing members become overlapping', V,
         'return r->min_u<r->max_u&&r->min_v<r->max_v;', 'return r->min_u<=r->max_u&&r->min_v<r->max_v;',
         [TOUCH], [ACCEPT, 'V_PROFILE_OVERLAP']),
    case('SPM04', 'R36', 'v overlap uses <= : members touching along v become overlapping', V,
         'return r->min_u<r->max_u&&r->min_v<r->max_v;', 'return r->min_u<r->max_u&&r->min_v<=r->max_v;',
         [TOUCH], [ACCEPT, 'V_PROFILE_OVERLAP']),
    case('SPM05', 'I46/D40', 'panel width w < 915 becomes w <= 915', P,
         'm.width>=wood_sp_panel_spec.width_max', 'm.width>wood_sp_panel_spec.width_max',
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
         'if(!wood_sp_loop_valid(&p.outline))return wood_sp_error(w,"I43: profile',
         'if(0&&!wood_sp_loop_valid(&p.outline))return wood_sp_error(w,"I43: profile',
         [GEOM], ["expected rejection 'I43'"]),
    case('SPM11', 'D37', 'run length accepts a D26 material source', P,
         '(length&&out->kind==ENG_MATERIAL)', '(0&&length&&out->kind==ENG_MATERIAL)',
         [PARAM], ["expected rejection 'unsupported dimension source'"]),
    case('SPM12', 'D36', 'material A/B field identity is no longer enforced', P,
         'out->field!=(field?ENG_B:ENG_A)', '0&&out->field!=(field?ENG_B:ENG_A)',
         [PARAM], ["rejected, but not for 'D36'"]),
    case('SPM13', 'I51', 'scene records no longer need the section-profile/1 declaration', H,
         'if(!sp_scene_required){scene_error(', 'if(0&&!sp_scene_required){scene_error(',
         [DUMP], ['I51: a scene with a missing requires section-profile/1 marker must be rejected']),
    case('SPM14', 'I46', 'timber orientation is not validated', P,
         '(strcmp(orientation,"A-u")&&strcmp(orientation,"A-v"))', '0',
         [GEOM], ["expected rejection 'timber orientation must be A-u or A-v'"]),
    case('SPM15', 'I46', 'panel orientation is not validated', P,
         'if(strcmp(orientation,"thickness-v")&&strcmp(orientation,"thickness-u"))return', 'if(0)return',
         [GEOM], ["expected rejection 'panel orientation must be thickness-v or thickness-u'"]),
    case('SPM16', 'R38', 'V = +up instead of -up', PL,
         'r->frame.axis_v=wood_sp_scaled(r->up,-1);', 'r->frame.axis_v=wood_sp_scaled(r->up,1);',
         [CARD], ['R38: V must be -up']),
    case('SPM17', 'R38', 'negative directions (-u,-v) lose their sign', PL,
         '(r->dir%2)?-1:1', '1',
         [CARD], ['R38: N must equal the run direction d']),
    case('SPM18', 'R38', 'dir +u/-u and +v/-v pick the wrong host axis', PL,
         'r->dir<2?host.axis_u:host.axis_v', 'r->dir<2?host.axis_v:host.axis_u',
         [CARD], ['R38: N must equal the run direction d']),
    case('SPM19', 'I48', 'p,q may lie outside the host range', PL,
         'bool inside=wood_sp_region_point(&region,(GeoPoint2){r->p,r->q});', 'bool inside=true;',
         [HOLES], ["expected rejection 'outside closed host range'"]),
    case('SPM20', 'I48', 'up need not be perpendicular to the run direction', PL,
         'bool perpendicular=geo_vector_dot(r->up,r->frame.normal)==0;', 'bool perpendicular=true;',
         [HOLES], ["expected rejection 'perpendicular'"]),
    case('SPM21', 'I48/D1', 'simple-placement origin is not range-checked', PL,
         'bool origin=geo_coord_in_range(r->frame.origin.x)&&geo_coord_in_range(r->frame.origin.y)&&geo_coord_in_range(r->frame.origin.z);',
         'bool origin=true;',
         [HOLES], ["rejected, but not for 'origin exceeds D1'"]),
    case('SPM22', 'R38', 'origin x component swaps p and q', PL,
         'r->frame.origin=geo_frame_point(&host,r->p,r->q,0);', 'r->frame.origin=geo_frame_point(&host,r->p,r->q,0);r->frame.origin.x=host.origin.x+r->q*host.axis_u.x+r->p*host.axis_v.x;',
         [LIVE], ['R38/R40: O = o_H + p*U_H + q*V_H must follow the live host']),
    case('SPM23', 'D38', 'advanced->simple conversion ignores the host plane', CV,
         'plane=geo_vector_dot(delta,host->normal)==0', 'plane=true',
         [CONV], ["rejected, but not for 'origin not in host plane'"]),
    case('SPM24', 'D38', 'advanced->simple conversion accepts any V as up', CV,
         'bool legal_up=geo_vector_dot(up,r->frame.normal)==0&&geo_vector_dot(up,up)==1;', 'bool legal_up=true;',
         [CONV, CARD], [],
         equivalent='an advanced frame is accepted only by surface_frame_is_valid (unit cardinal axes, V perpendicular to N), '
                    'so up=-V is always a legal up: the "V has a legal up" condition of D38 can never fail here'),
    case('SPM25', 'D38', 'advanced->simple conversion takes the last host direction regardless of N', CV,
         'if(geo_vector_equal(axes[i],r->frame.normal))dir=i;', 'dir=i;',
         [CARD], ['D38: advanced->simple must recover dir/p/q/up']),
    case('SPM26', 'I49', 'PROFILE_CONTACT_LOST is never reported', BR,
         'if(!p||!m->resolved||!next||!n->resolved)return false;', 'return false;',
         [SHRINK], ['PROFILE_CONTACT_LOST']),
    case('SPM27', 'I44', 'outside-region split drops the right-hand remainder', K,
         'if(cursor<r->max_u){if(n==capacity)', 'if(0&&cursor<r->max_u){if(n==capacity)',
         [CONCAVE], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    # SPM28/SPM29: GEO-261 rejects a dangling profile reference in three layers -- the I49 error of the W evaluator,
    # the source graph's definition-required edge to the (deleted) profile definition, and the W region source /
    # run root that refuses the unresolved object.  Removing only the I49 error is equivalent (measured: the
    # candidate stays rejected and the PROFILE_MISSING diagnostic still names I49), so each case removes all
    # three for its object kind, as M11 of the card mutants does.
    case('SPM28', 'I49', 'a member may reference a deleted profile', V,
         'if(!exists){wood_sp_error(w,"I49: member %u references missing profile %u"', 'if(0&&!exists){wood_sp_error(w,"I49: member %u references missing profile %u"',
         [NAMED], ["expected rejection 'I49'"],
         more=[(V, 'if(w->evaluation&&w->evaluation->profile_definition)profile_ok=w->evaluation->profile_definition(w->evaluation->user,w,m->profile_id,&p);',
                'if(exists&&w->evaluation&&w->evaluation->profile_definition)profile_ok=w->evaluation->profile_definition(w->evaluation->user,w,m->profile_id,&p);'),
               (WS, 'if(!m->resolved||m->missing_profile||m->outside||m->range_error)return false;',
                'if(!m->resolved||m->outside||m->range_error)return false;')]),
    case('SPM29', 'I49', 'a run may reference a deleted profile', V,
         'if(!exists){wood_sp_error(w,"I49: run %u references missing profile %u"', 'if(0&&!exists){wood_sp_error(w,"I49: run %u references missing profile %u"',
         [NAMED], ["expected rejection 'I49'"],
         more=[(V, 'if(w->evaluation&&w->evaluation->profile_definition)profile_ok=w->evaluation->profile_definition(w->evaluation->user,w,r->profile_id,&p);',
                'if(exists&&w->evaluation&&w->evaluation->profile_definition)profile_ok=w->evaluation->profile_definition(w->evaluation->user,w,r->profile_id,&p);'),
               (WS, 'if(status!=GEO_SOURCE_OK&&!s->run_errors[i][0])wood_sp_source_graph_error(s,first,capacity);',
                'if(status!=GEO_SOURCE_OK&&!s->run_errors[i][0]&&!w->state->runs[i].missing_profile)wood_sp_source_graph_error(s,first,capacity);')]),
    case('SPM30', 'I47/D1', 'generated run vertices are not range-checked', V,
         'if(!geo_coord_in_range(point.x)||!geo_coord_in_range(point.y)||!geo_coord_in_range(point.z)){r->range_error=true;',
         'if(0&&(!geo_coord_in_range(point.x)||!geo_coord_in_range(point.y)||!geo_coord_in_range(point.z))){r->range_error=true;',
         [AC09], ["expected rejection 'I47/I48/D1'"]),
    case('SPM31', 'R36', 'A-v / thickness-u swap width and height the wrong way round', V,
         'GeoCoord width=m->rotated?m->b:m->a,height=m->rotated?m->a:m->b;', 'GeoCoord width=m->rotated?m->a:m->b,height=m->rotated?m->b:m->a;',
         [AC01, AC09], [ACCEPT, 'V_PROFILE_']),
    case('SPM32', 'D36', 'panel orientation thickness-u is read as thickness-v', P,
         'm.rotated=!strcmp(orientation,"thickness-u");', 'm.rotated=!strcmp(orientation,"thickness-v");',
         [PANEL], [ACCEPT, 'V_PROFILE_OUTSIDE']),
    case('SPM33', 'D40/R37', 'the 1830 mm sheet length is misused as an upper bound for the run length', V,
         '?w->evaluation->run_length(w->evaluation->user,w,i,&r->length):wood_sp_run_length_direct(w,i,&r->length);',
         '?w->evaluation->run_length(w->evaluation->user,w,i,&r->length)&&r->length<=wood_sp_panel_spec.sheet_length'
         ':wood_sp_run_length_direct(w,i,&r->length)&&r->length<=wood_sp_panel_spec.sheet_length;',
         [PANEL], [ACCEPT, 'RUN_LENGTH_INVALID']),
    case('SPM34', 'I51', 'scene load accepts a duplicate profile id', H,
         'if(!strcmp(tokens[1],"profile")&&!sp_profile(w,id))ok=', 'if(!strcmp(tokens[1],"profile"))ok=',
         [DUMP], ['I51: a scene with a duplicate profile id record must be rejected']),
    case('SPM35', 'I49', 'section-profile records may be injected line by line outside an atomic load', H,
         'if(!g_parsing_scene_file){scene_error(', 'if(0&&!g_parsing_scene_file){scene_error(',
         [DUMP], ['I49: section-profile records must not be injected line by line']),
    # Discard one positive-area outside region, independent of the shared poly_contains_rect implementation.
    # The former substitution stopped being a fault after GEO-257 fixed that shared predicate.
    case('SPM41', 'I44', 'a single positive-area outside region is incorrectly treated as contained', V,
         'GEO_GEOMETRY_OK?count:0;', 'GEO_GEOMETRY_OK?(count>1?count:0):0;',
         [CONCAVE], ["expected rejection 'V_PROFILE_OUTSIDE'"]),
    case('SPM42', 'I47/D1', 'only the start vertex of a run is range-checked, not the far end', V,
         'GeoPoint3 point=wood_sp_point(r,p->outline.v[v].u,p->outline.v[v].v,end?r->length:0);',
         'GeoPoint3 point=wood_sp_point(r,p->outline.v[v].u,p->outline.v[v].v,0);',
         [AC09], ["expected rejection 'I47/I48/D1'"]),
    # ---- model group: the producer of the R37 / R39 / D39 solids (see the module docstring) ----
    # SPM36/SPM39: in the source-graph path the W native region sources produce the envelope and member regions
    # (W section_profile.py only binds the typed roots); its legacy RegionDef branch is not on that path.
    case('SPM36', 'R37', 'the reference envelope becomes the bounding rectangle of the outline (L shape lost)', WS,
         's->run_regions[i]=(GeoRegionView){{p->outline.v,p->outline.count},NULL,0};',
         'GeoPoint2 *box=malloc(4*sizeof *box);if(!box)return false;'
         'GeoCoord u0=p->outline.v[0].u,v0=p->outline.v[0].v,u1=u0,v1=v0;'
         'for(size_t k=1;k<p->outline.count;++k){if(p->outline.v[k].u<u0)u0=p->outline.v[k].u;if(p->outline.v[k].u>u1)u1=p->outline.v[k].u;'
         'if(p->outline.v[k].v<v0)v0=p->outline.v[k].v;if(p->outline.v[k].v>v1)v1=p->outline.v[k].v;}'
         'box[0]=(GeoPoint2){u0,v0};box[1]=(GeoPoint2){u1,v0};box[2]=(GeoPoint2){u1,v1};box[3]=(GeoPoint2){u0,v1};'
         's->run_regions[i]=(GeoRegionView){{box,4},NULL,0};',
         [M3], ['R37: exact mesh volume of the envelope object'], group='model'),
    case('SPM37', 'R39', 'the reference envelope is counted as material volume', WP,
         'details["material_volume_mm3"] = "0" if reference else mesh["volume_mm3"]',
         'details["material_volume_mm3"] = mesh["volume_mm3"]',
         [M3], ['R37/R39: the envelope is a reference object and carries no material volume'], group='model'),
    case('SPM38', 'R37/D40', 'a panel is cut at the 1830 mm sheet length', WP,
         'source = ProvenanceTemplate((*identity, None, None), identity, ("members", str(member["id"])))',
         'length = min(run["length"], 1830) if member["kind"] == "panel" else length; '
         'source = ProvenanceTemplate((*identity, None, None), identity, ("members", str(member["id"])))',
         [MLONG], ['Native dimensions and derived exact member volume disagree'], group='model',
         error_types=[MODEL_ERROR]),
    case('SPM39', 'R36/R37', 'member rectangles are read with u and v swapped', WS,
         'GeoPoint2 *p=s->member_points[i];p[0]=(GeoPoint2){m->rect.min_u,m->rect.min_v};p[1]=(GeoPoint2){m->rect.max_u,m->rect.min_v};'
         'p[2]=(GeoPoint2){m->rect.max_u,m->rect.max_v};p[3]=(GeoPoint2){m->rect.min_u,m->rect.max_v};',
         'GeoPoint2 *p=s->member_points[i];p[0]=(GeoPoint2){m->rect.min_v,m->rect.min_u};p[1]=(GeoPoint2){m->rect.max_v,m->rect.min_u};'
         'p[2]=(GeoPoint2){m->rect.max_v,m->rect.max_u};p[3]=(GeoPoint2){m->rect.min_v,m->rect.max_u};',
         [MADV], ['R36/R37: bounds of the'], group='model'),
    # SPM40: K meshes each geometry in the arrangement of its own coordinate domain, and mesh_objects refuses an
    # arrangement of another domain.  Patching only the first layer turns the fault into COORDINATE_DOMAIN
    # (a different error); main's fault is that the local run is meshed in the world arrangement.
    case('SPM40', 'D39', 'an unplaced (local) run is cut by the world grid', KE,
         'mesh_records = geo.mesh_objects(geometry, grids[geometry.domain], volume_known=volume_known, max_cells=limits.max_cells)',
         'mesh_records = geo.mesh_objects(geometry, grids.get(CoordinateDomain()) or geo.build_grid([], max_cells=limits.max_cells), '
         'volume_known=volume_known, max_cells=limits.max_cells)',
         [MLOCAL], ['A section-profile object must produce one complete solid'], group='model',
         error_types=[MODEL_ERROR],
         more=[(KG, 'if not isinstance(grid, _Arrangement) or grid.domain != geometry.domain:',
                'if not isinstance(grid, _Arrangement):')]),
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
    for parent in (ROOT, ROOT / 'geometry-core', ROOT / 'geometry-web', ROOT / 'geometry-app', ROOT / 'geometry-templates'):
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
        # GEO-261 K/H/W packages the modeling facade imports (geometry_app first), data files included, and the
        # saved packages the model tests reopen (tests/fixtures/q38-legacy-space-model.json).
        for package in MODEL_DIRECTORIES:
            for path in (ROOT / package).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    target = destination / path.relative_to(ROOT)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
        shutil.copyfile(ROOT / '公理層.md', destination / '公理層.md')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_bridge(source: Path, exe: Path):
    argv = ['cc', '-std=c11', '-O2', str(source / 'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)]
    result = subprocess.run(argv,
                            capture_output=True, text=True, timeout=600)
    if LOG_DIR:
        receipt = dict(argv=argv, exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
                       source_tree_sha256=tree_digest(source), binary_sha256=sha256(exe) if exe.exists() else None)
        (LOG_DIR / (exe.name+'.compile.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError('compile failed: ' + (result.stderr or result.stdout)[-1500:])


EXCEPTION_RUNNER = ROOT / 'tests' / 'section_profile_mutation_runner.py'
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


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_evidence(path, names):
    raw = None
    try:
        raw = path.read_text(encoding='utf-8')
        value = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(value, dict) or value.get('requested') != names:
            raise ValueError('receipt requested methods differ from the actual child command')
        return value
    except (OSError, ValueError) as error:
        return {'invalid_receipt': str(error), 'raw_receipt': raw}


def run_child(names, cwd, env, bridge=None, timeout=900):
    with tempfile.TemporaryDirectory(prefix='section-profile-exceptions-') as directory:
        path = Path(directory) / 'exceptions.json'
        argv = [sys.executable, str(EXCEPTION_RUNNER), '--receipt', str(path)]
        if bridge is not None:
            argv += ['--bridge', str(bridge)]
        run = subprocess.run([*argv, *names], cwd=cwd, env=env,
                             capture_output=True, text=True, timeout=timeout)
        return run.returncode, run.stdout + run.stderr, read_evidence(path, names)


def run_native(exe: Path, tests, timeout=900):
    names = ['%s.%s.%s' % (NATIVE_MODULE, NATIVE_CLASS, name) for name in (tests or ALL['native'])]
    return run_child(names, ROOT, dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), bridge=exe, timeout=timeout)


def run_model(tree: Path, model_base: str, tests, timeout=900):
    names = ['%s.%s.%s' % (MODEL_MODULE, MODEL_CLASS, name) for name in (tests or ALL['model'])]
    return run_child(names, tree, dict(os.environ, GEOMETRY_MODEL_BASE=model_base, PYTHONDONTWRITEBYTECODE='1'),
                     timeout=timeout)


def evidence_problem(code, evidence):
    """Validate child completeness and real unittest counts before interpreting any cause."""
    fields = {'schema', 'requested', 'executed', 'passed', 'tests_run', 'failures', 'errors',
              'skipped', 'expected_failures', 'unexpected_successes', 'events'}
    if not isinstance(evidence, dict) or set(evidence) != fields:
        return 'missing or malformed exception receipt'
    if evidence['schema'] != 'section-profile-exceptions/1':
        return 'unknown exception receipt schema'
    for key in ('requested', 'executed', 'passed'):
        values = evidence[key]
        if not isinstance(values, list) or not all(isinstance(x, str) and x for x in values) or len(set(values)) != len(values):
            return 'missing, duplicate or malformed test identities'
    if not evidence['requested'] or evidence['requested'] != evidence['executed']:
        return 'requested and executed methods differ'
    counts = ('tests_run', 'failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes')
    if any(type(evidence[k]) is not int or evidence[k] < 0 for k in counts):
        return 'malformed unittest counts'
    if evidence['tests_run'] != len(evidence['executed']):
        return 'executed method count differs'
    if any(evidence[k] for k in ('skipped', 'expected_failures', 'unexpected_successes')):
        return 'skips, expected failures and unexpected successes are not detection'
    events = evidence['events']
    if not isinstance(events, list):
        return 'malformed exception records'
    identities = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {'test_id', 'subtest_id', 'kind', 'exception_type', 'message'}:
            return 'malformed exception record'
        if not isinstance(event['test_id'], str) or event['test_id'] not in evidence['executed']:
            return 'exception belongs to an unexecuted method'
        subtest = event['subtest_id']
        if subtest is not None and (not isinstance(subtest, str) or not subtest.startswith(event['test_id']+' ')):
            return 'subtest does not belong to its method'
        identity = (event['test_id'], subtest)
        if identity in identities:
            return 'duplicate terminal exception record'
        identities.add(identity)
        if event['kind'] not in ('failure', 'error') or not isinstance(event['message'], str):
            return 'malformed exception kind or message'
        if not isinstance(event['exception_type'], str) or not re.fullmatch(r'[\w]+(?:\.[\w]+)+', event['exception_type']):
            return 'malformed exception type'
    if any(evidence[k] != sum(e['kind']==kind for e in events) for k,kind in (('failures','failure'),('errors','error'))):
        return 'terminal exceptions and unittest counts differ'
    failed_ids = {e['test_id'] for e in events}
    if set(evidence['passed']) != set(evidence['executed']) - failed_ids:
        return 'passed and failed method identities differ'
    if code != (1 if events else 0):
        return 'actual child exit and unittest counts differ'
    return None


def save_log(identifier, log, evidence):
    if LOG_DIR:
        (LOG_DIR / (identifier + '.log')).write_text(log, encoding='utf-8')
        (LOG_DIR / (identifier + '.exceptions.json')).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')


def mutate_file(tree: Path, case):
    for file, before, after in case['patches']:
        target = tree / file
        original = target.read_bytes()
        before = before.encode('utf-8')
        assert original.count(before) == 1, (case['id'], file, 'mutation anchor changed or not unique')
        target.write_bytes(original.replace(before, after.encode('utf-8')))


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


def verdict(case, code, log, evidence=None):
    save_log(case['id'], log, evidence)
    record = {'exit': code, 'exception_evidence': evidence, 'failed': []}
    problem = evidence_problem(code, evidence)
    if problem:
        record.update(verdict='blocked', note=problem)
    else:
        events = evidence['events']
        record['failed'] = ['%s %s' % ('FAIL' if e['kind']=='failure' else 'ERROR', e['test_id']) for e in events]
        if events:
            record['first_failure'] = events[0]['message'][:300]  # Display only; full strings below drive the verdict.
        module, cls = (NATIVE_MODULE, NATIVE_CLASS) if case['group']=='native' else (MODEL_MODULE, MODEL_CLASS)
        expected = {module+'.'+cls+'.'+name for name in case['tests']}
        detected = [e for e in events if (e['kind']=='failure' and e['exception_type']=='builtins.AssertionError') or
                    (e['kind']=='error' and e['exception_type'] in case['error_types'])]
        named = [e for e in detected if e['test_id'] in expected]
        caused = any(all(text in e['message'] for text in case['cause']) for e in named)
        if code == 0:
            record['verdict'] = 'equivalent' if case['equivalent'] else 'survived'
        elif not detected:
            record.update(verdict='crashed', note='no AssertionError or case-declared error type')
        elif not named:
            record.update(verdict='wrong-killer', note='no terminal exception from a named method')
        elif not caused:
            record.update(verdict='unlabelled', note='no single named terminal exception contains all causes')
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
        code, log, evidence = run_native(exe, None if explore else case['tests'])
    except subprocess.TimeoutExpired:
        record.update(verdict='blocked', note='timeout')
        return record
    record.update(verdict(case, code, log, evidence))
    return record


ADAPTER_BUILD = ('import sys\nfrom pathlib import Path\nfrom tests import binaries\n'
                 'binaries.OUT_DIR = Path(sys.argv[1])\nraise SystemExit(binaries.main(["build", "model-base"]))\n')


def build_model_adapter(tree: Path, directory: Path, name: str):
    """model-base built by the copy's own tests/binaries.py, so its sidecar describes exactly that copy."""
    argv = [sys.executable, '-c', ADAPTER_BUILD, str(directory)]
    result = subprocess.run(argv, cwd=tree, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                            capture_output=True, text=True, timeout=900)
    exe = directory / 'model-base'
    if LOG_DIR:
        receipt = dict(argv=argv[:2] + ['<ADAPTER_BUILD>'] + argv[3:], cwd=str(tree), exit=result.returncode,
                       stdout=result.stdout, stderr=result.stderr, source_tree_sha256=tree_digest(tree),
                       binary_sha256=sha256(exe) if exe.exists() else None)
        (LOG_DIR / (name + '.model-base.compile.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if result.returncode != 0 or not exe.is_file():
        raise RuntimeError('model-base build failed: ' + (result.stderr or result.stdout)[-1500:])
    return exe


def judge_model(case, model_tree: Path, model_base: str, baseline_adapter_hash: str, work: Path, explore):
    record = {'id': case['id'], 'group': 'model', 'clause': case['clause'], 'desc': case['desc']}
    tree = work / case['id']
    shutil.copytree(model_tree, tree)
    try:
        try:
            mutate_file(tree, case)
            adapter = model_base
            if patches_native(case):
                adapter = build_model_adapter(tree, work / ('model-base-' + case['id']), case['id'])
        except Exception as error:  # noqa: BLE001 - reported as an invalid mutant
            record.update(verdict='invalid', note=str(error)[-400:])
            return record
        if patches_native(case):
            record['adapter_sha256'] = sha256(Path(adapter))
            if record['adapter_sha256'] == baseline_adapter_hash:
                record.update(verdict='invalid', note='mutant adapter equals baseline adapter')
                return record
        code, log, evidence = run_model(tree, str(adapter), None if explore else case['tests'])
    except subprocess.TimeoutExpired:
        record.update(verdict='blocked', note='timeout')
        return record
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    record.update(verdict(case, code, log, evidence))
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


def anchor_problems(cases, root=ROOT):
    """Every patch anchor of the selected cases must occur exactly once in the checkout, checked before any copy,
    compile or test run (a drifted anchor otherwise surfaces only as an 'invalid' record at the end)."""
    problems = []
    for item in cases:
        for file, before, _ in item['patches']:
            path = root / file
            count = path.read_bytes().count(before.encode('utf-8')) if path.is_file() else None
            if count != 1:
                problems.append('%s: anchor in %s occurs %s' % (item['id'], file, 'nowhere (no file)' if count is None
                                                                 else '%d times' % count))
    return problems


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
    drifted = anchor_problems(cases)
    if drifted:
        for problem in drifted:
            print('PROBLEM:', problem)
        return 2
    if args.logs:
        LOG_DIR = Path(args.logs)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    posix_only()
    ALL['native'] = test_names(NATIVE_MODULE, NATIVE_CLASS, EXCLUDED, ROOT)
    ALL['model'] = test_names(MODEL_MODULE, MODEL_CLASS, set(), ROOT)
    records = []
    baselines = {}
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
            code, log, evidence = run_native(baseline, None)
            baselines['native'] = dict(exit=code, source_tree_sha256=digest, binary_sha256=baseline_hash,
                                       exception_evidence=evidence)
            save_log('native-baseline', log, evidence)
            print('native baseline: exit', code, flush=True)
            if code != 0 or evidence_problem(code, evidence) is not None:
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
            code, log, evidence = run_model(model_tree, model_base, None)
            adapter_hash = sha256(Path(model_base))
            baselines['model'] = dict(exit=code, source_tree_sha256=digest, adapter_sha256=adapter_hash,
                                      exception_evidence=evidence)
            save_log('model-baseline', log, evidence)
            print('model baseline: exit', code, flush=True)
            if code != 0 or evidence_problem(code, evidence) is not None:
                print(log[-3000:])
                problems.append('model baseline must pass with zero skips before any mutant is judged')
            else:
                records += list(pool.map(lambda c: judge_model(c, model_tree, model_base, adapter_hash, work, args.explore),
                                         model_cases))
                if tree_digest(model_tree) != digest:
                    problems.append('the shared model copy changed while mutants were judged')
        pool.shutdown()
    summary = {}
    for record in records:
        summary[record['verdict']] = summary.get(record['verdict'], 0) + 1
        print(json.dumps(record, ensure_ascii=False), flush=True)
    result = {'schema': 'section-profile-mutations/2', 'baselines': baselines, 'summary': summary, 'results': records}
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
