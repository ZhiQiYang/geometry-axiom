"""Control mutants for the GEO-261 re-anchoring of the Q38 gate (experiment only, never committed).

Each control is run by the real gate (same baseline, same judge).  Expected:
  XC36  W legacy RegionDef envelope -> bbox             : survived (branch not on the source-graph path)
  XC39  W legacy member rect read with u/v swapped       : survived (same reason)
  XC40A only K's arrangement choice uses the world grid  : not 'killed' (mesh_objects raises COORDINATE_DOMAIN)
  XC40B only K's mesh_objects domain guard is dropped    : survived (each domain still gets its own grid)
  XC28L1 / XC29L1   only the I49 error (main's single point)          : survived
  XC28L12 / XC29L12 I49 error + profile-definition edge, no 3rd layer  : expected survived if the 3rd layer is needed
  XC28L13 / XC29L13 I49 error + 3rd layer, profile-definition edge kept: expected survived if the edge is needed
  XC03L1 / XC04L1   only the pair predicate (closed interval)       : expected not killed (graph error)
Run from the repository root: python3 q38_controls.py --only XC36 ... (gate options).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
import section_profile_mutation_check as g  # noqa: E402

BY_ID = {c['id']: c for c in g.CASES}
(k_file, k_before, k_after), (m_file, m_before, m_after) = BY_ID['SPM40']['patches']


def layers(case_id, new_id, keep):
    """A control made of the listed patch indexes (0 = main's anchor) of a multi-layer case."""
    source = BY_ID[case_id]
    chosen = [source['patches'][i] for i in keep]
    return g.case(new_id, source['clause'], 'control: %s layers %s' % (case_id, keep), *chosen[0], source['tests'],
                  source['cause'], group=source['group'], error_types=source['error_types'], more=chosen[1:])


g.CASES += [
    g.case('XC36', 'R37', 'control: legacy RegionDef envelope becomes the outline bbox', g.WP,
           'shape, length = RegionDef(run["outline"]), run["length"]',
           'shape, length = RegionDef((lambda o: ((min(p[0] for p in o), min(p[1] for p in o)), '
           '(max(p[0] for p in o), min(p[1] for p in o)), (max(p[0] for p in o), max(p[1] for p in o)), '
           '(min(p[0] for p in o), max(p[1] for p in o))))(run["outline"])), run["length"]',
           [g.M3], ['R37: exact mesh volume of the envelope object'], group='model'),
    g.case('XC39', 'R36/R37', 'control: legacy member rect read with u and v swapped', g.WP,
           'u0, v0, u1, v1 = member["rect"]', 'v0, u0, v1, u1 = member["rect"]',
           [g.MADV], ['R36/R37: bounds of the'], group='model'),
    g.case('XC40A', 'D39', 'control: only the K arrangement choice is the world grid', k_file, k_before, k_after,
           [g.MLOCAL], ['A section-profile object must produce one complete solid'], group='model',
           error_types=[g.MODEL_ERROR]),
    g.case('XC40B', 'D39', 'control: only the K mesh domain guard is dropped', m_file, m_before, m_after,
           [g.MLOCAL], ['A section-profile object must produce one complete solid'], group='model',
           error_types=[g.MODEL_ERROR]),
    layers('SPM28', 'XC28L1', [0]), layers('SPM28', 'XC28L12', [0, 1]), layers('SPM28', 'XC28L13', [0, 2]),
    layers('SPM29', 'XC29L1', [0]), layers('SPM29', 'XC29L12', [0, 1]), layers('SPM29', 'XC29L13', [0, 2]),
    layers('SPM03', 'XC03L1', [0]), layers('SPM04', 'XC04L1', [0]),
]
sys.exit(g.main())
