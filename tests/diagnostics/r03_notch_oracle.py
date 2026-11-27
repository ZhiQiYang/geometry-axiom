#!/usr/bin/env python3
"""R03 single-notch witness: unchanged policy-A builder + independent geometry audit.

This is a reference/test tool, never a product generator or native legality waiver.
All intersections below are exact axis-aligned arrangements.  The independent
audit does not call the historical oracle's Region/check/rectangle helpers.
Four board-side *directions* may contain multiple segments after an L/U cut;
artificial rectangle-decomposition edges are not reported as physical edges.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / "geometry-core/framing-template/oracle/framing_oracle.py"
SPEC = importlib.util.spec_from_file_location("r03_policy_a_reference", ORACLE)
REFERENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFERENCE)
PARAMS = dict(P=915, L=1830, gap=2, w=27, M=367, X=8, min_piece=27)
LAYOUT = dict(A="x", a_start="min", b_start="min")
L_ROOM = dict(outer=[[0, 0], [3740, 0], [3740, 2000],
                     [2500, 2000], [2500, 3301], [0, 3301]])
U_ROOM = dict(outer=[[0, 0], [3880, 0], [3880, 1500], [3580, 1500],
                     [3580, 1900], [3880, 1900], [3880, 3600], [0, 3600]])


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def inside(ring, x, y):
    """Ray parity at an open-cell midpoint, independently of Region.section."""
    parity = False
    for p, q in zip(ring, ring[1:] + ring[:1]):
        if p[0] == q[0] and min(p[1], q[1]) < y < max(p[1], q[1]) and p[0] > x:
            parity = not parity
    return parity


def intersect(r, s):
    q = [max(r[0], s[0]), max(r[1], s[1]), min(r[2], s[2]), min(r[3], s[3])]
    return q if q[0] < q[2] and q[1] < q[3] else None


def cells(rect, rectangles=(), ring=()):
    xs = {rect[0], rect[2]}
    ys = {rect[1], rect[3]}
    xs.update(p[0] for p in ring if rect[0] < p[0] < rect[2])
    ys.update(p[1] for p in ring if rect[1] < p[1] < rect[3])
    for other in rectangles:
        xs.update(v for v in (other[0], other[2]) if rect[0] < v < rect[2])
        ys.update(v for v in (other[1], other[3]) if rect[1] < v < rect[3])
    xs, ys = sorted(xs), sorted(ys)
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            yield [x0, y0, x1, y1]


def contains(rect, x, y):
    return rect[0] < x < rect[2] and rect[1] < y < rect[3]


def midpoint(rect):
    return Fraction(rect[0] + rect[2], 2), Fraction(rect[1] + rect[3], 2)


def normalize_room(room):
    if room.get("holes"):
        raise ValueError("R03B_SHAPE_HOLES_UNSUPPORTED")
    points = room.get("outer")
    if not isinstance(points, list) or any(not isinstance(p, (list, tuple)) or len(p) != 2
            or any(type(v) is not int for v in p) for p in points):
        raise ValueError("R03B_SHAPE_INTEGER_POINTS")
    ring = []
    for p in points:
        if not ring or list(p) != ring[-1]:
            ring.append(list(p))
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    while len(ring) >= 4:
        shorter = [p for i, p in enumerate(ring)
                   if not (ring[i - 1][0] == p[0] == ring[(i + 1) % len(ring)][0]
                           or ring[i - 1][1] == p[1] == ring[(i + 1) % len(ring)][1])]
        if len(shorter) == len(ring):
            break
        ring = shorter
    if len(ring) not in (4, 6, 8):
        raise ValueError("R03B_SHAPE_SINGLE_NOTCH_ONLY")
    edges = list(zip(ring, ring[1:] + ring[:1]))
    for p, q in edges:
        if (p[0] == q[0]) == (p[1] == q[1]):
            raise ValueError("R03B_SHAPE_ORTHOGONAL")
    for i, (p, q) in enumerate(edges):
        for j in range(i + 1, len(edges)):
            if j in ((i + 1) % len(edges), (i - 1) % len(edges)):
                continue
            a, b = edges[j]
            if (max(min(p[0], q[0]), min(a[0], b[0])) <= min(max(p[0], q[0]), max(a[0], b[0]))
                    and max(min(p[1], q[1]), min(a[1], b[1])) <= min(max(p[1], q[1]), max(a[1], b[1]))):
                raise ValueError("R03B_SHAPE_SIMPLE_RING")
    box = [min(p[0] for p in ring), min(p[1] for p in ring),
           max(p[0] for p in ring), max(p[1] for p in ring)]
    missing = [r for r in cells(box, ring=ring) if not inside(ring, *midpoint(r))]
    notch = None
    shape = "rectangle"
    if missing:
        notch = [min(r[0] for r in missing), min(r[1] for r in missing),
                 max(r[2] for r in missing), max(r[3] for r in missing)]
        area = sum((r[2] - r[0]) * (r[3] - r[1]) for r in missing)
        if area != (notch[2] - notch[0]) * (notch[3] - notch[1]):
            raise ValueError("R03B_SHAPE_RECTANGULAR_NOTCH")
        touch = [i for i in range(4) if notch[i] == box[i]]
        if len(touch) == 1 and len(ring) == 8:
            shape = "U"
        elif len(touch) == 2 and touch not in ([0, 2], [1, 3]) and len(ring) == 6:
            shape = "L"
        else:
            raise ValueError("R03B_SHAPE_SINGLE_NOTCH_ONLY")
    elif len(ring) != 4:
        raise ValueError("R03B_SHAPE_SIMPLE_RECTANGLE")
    return dict(outer=ring), dict(shape=shape, bbox=box, notch=notch)


def role(timber):
    if timber.get("core_role") == "custom":
        return "custom", timber["priority"]
    if timber["kind"] == "boundary":
        return "boundary", 1
    if timber["kind"] in ("main", "rc_parallel"):
        return "primary", 2
    return "secondary", 3


def timber_rows(result):
    a, b = result["a"], result["b"]
    rows = []
    for t in result["timbers"]:
        r = list(t["rect"])
        along = b if t["kind"] in ("main", "rc_parallel", "doubling") else a
        cross = 1 - along
        center = r[cross] + (r[cross + 2] - r[cross]) // 2
        ends = [[r[along], center], [r[along + 2], center]]
        if along == 1:
            ends = [[v[1], v[0]] for v in ends]
        core_role, priority = role(t)
        rows.append(dict(id=t["id"], kind=t["kind"], role=core_role, priority=priority,
                         rect=r, axis="xy"[along], endpoints=ends,
                         length=r[along + 2] - r[along],
                         **{k: t[k] for k in ("seam", "at", "rc_line", "edge", "ext", "shift") if k in t}))
    return rows


def side_segments(ring, cell):
    """True boundary of cell intersect polygon, grouped into four normal directions."""
    grid = list(cells(cell, ring=ring))
    occupied = [r for r in grid if inside(ring, *midpoint(r))]
    groups = defaultdict(list)
    for r in occupied:
        for axis, sign, at, lo, hi in ((0, -1, r[0], r[1], r[3]), (0, 1, r[2], r[1], r[3]),
                                      (1, -1, r[1], r[0], r[2]), (1, 1, r[3], r[0], r[2])):
            mid = Fraction(lo + hi, 2)
            x, y = ((Fraction(at) + Fraction(sign, 2), mid) if axis == 0
                    else (mid, Fraction(at) + Fraction(sign, 2)))
            if any(contains(s, x, y) for s in occupied):
                continue
            groups[(axis, sign, at)].append((lo, hi))
    out = []
    for (axis, sign, at), intervals in sorted(groups.items()):
        merged = []
        for lo, hi in sorted(intervals):
            if merged and merged[-1][1] == lo:
                merged[-1][1] = hi
            else:
                merged.append([lo, hi])
        out.extend(dict(axis=axis, outward=sign, at=at, interval=iv) for iv in merged)
    return out, occupied


def board_supports(room, result, params):
    ring = room["outer"]
    a, b = result["a"], result["b"]
    box = [min(p[0] for p in ring), min(p[1] for p in ring),
           max(p[0] for p in ring), max(p[1] for p in ring)]
    spans = {}
    for axis, seams in ((a, result["seams_a"]), (b, result["seams_b"])):
        cur = box[axis]
        spans[axis] = []
        for center in sorted(seams):
            spans[axis].append([cur, center - params["gap"] // 2])
            cur = center + params["gap"] - params["gap"] // 2
        spans[axis].append([cur, box[axis + 2]])
    boards, failures = [], []
    timbers = result["timbers"]
    rectangles = [list(t["rect"]) for t in timbers]
    for ix, xp in enumerate(spans[0]):
        for iy, yp in enumerate(spans[1]):
            cell = [xp[0], yp[0], xp[1], yp[1]]
            if cell[0] >= cell[2] or cell[1] >= cell[3]:
                continue
            sides, occupied = side_segments(ring, cell)
            if not occupied:
                continue
            edge_rows = []
            for side in sides:
                axis, sign, at = side["axis"], side["outward"], side["at"]
                lo, hi = side["interval"]
                across = sorted([at, at - sign * params["X"]])
                band = ([across[0], lo, across[1], hi] if axis == 0
                        else [lo, across[0], hi, across[1]])
                contact, gaps = defaultdict(list), []
                for atom in cells(band, rectangles + occupied, ring):
                    x, y = midpoint(atom)
                    if not any(contains(r, x, y) for r in occupied):
                        continue
                    owners = [t["id"] for t in timbers if contains(t["rect"], x, y)]
                    if owners:
                        for owner in owners:
                            contact[owner].append(atom)
                    else:
                        gaps.append(atom)
                # Existing R-nosliver is along-edge bridging, never a transverse
                # bearing-width exemption.  Record both physical flanks explicitly.
                bridged = []
                for gap in gaps:
                    along = 1 - axis
                    length = gap[along + 2] - gap[along]
                    flanks = []
                    for end, direction in ((gap[along], -1), (gap[along + 2], 1)):
                        slab = list(gap)
                        slab[along], slab[along + 2] = sorted([end, end + direction])
                        covered = all(any(contains(t["rect"], *midpoint(atom)) for t in timbers)
                                      for atom in cells(slab, rectangles))
                        flanks.append(covered)
                    if length < params["min_piece"] and all(flanks):
                        bridged.append(dict(rect=gap, length=length, exclusive_limit=params["min_piece"],
                                            reason="R-nosliver-along-edge-two-flanks"))
                    else:
                        failures.append(dict(check="R03B_BOARD_EDGE_UNSUPPORTED", board=[ix, iy],
                                             side=side, gap=gap))
                edge_rows.append(dict(direction="xy"[axis] + ("+" if sign > 0 else "-"),
                                      at=at, interval=[lo, hi], bearing_width=params["X"],
                                      supports=[dict(id=k, bands=v) for k, v in sorted(contact.items())],
                                      short_edge_bridges=bridged))
            boards.append(dict(key=[ix, iy], nominal=cell, clipped_cells=occupied, sides=edge_rows))
    return boards, failures


def independent_check(room, result, params):
    """Physical output checks. It deliberately does not trust oracle verdict/metadata."""
    ring = room["outer"]
    timbers = result["timbers"]
    failures = []
    if len(timbers) > 512:
        failures.append(dict(check="R03B_CAPACITY_512", count=len(timbers)))
    ids = [t["id"] for t in timbers]
    if len(ids) != len(set(ids)):
        failures.append(dict(check="R03B_UNIQUE_TIMBER_IDS"))
    for i, t in enumerate(timbers):
        r = t["rect"]
        if len(r) != 4 or any(type(v) is not int for v in r) or r[0] >= r[2] or r[1] >= r[3]:
            failures.append(dict(check="R03B_VALID_FOOTPRINT", id=t["id"]))
            continue
        if any(not inside(ring, *midpoint(atom)) for atom in cells(r, ring=ring)):
            failures.append(dict(check="R03B_NO_WALL_CROSSING", id=t["id"], rect=r))
        for other in timbers[i + 1:]:
            if intersect(r, other["rect"]):
                failures.append(dict(check="R03B_NO_OVERLAP", ids=[t["id"], other["id"]]))
    a, b = result["a"], result["b"]
    bounds = sorted({p[b] for p in ring} | {v for t in timbers for v in (t["rect"][b], t["rect"][b + 2])})
    for seam in result["seams_a"]:
        for lo, hi in zip(bounds, bounds[1:]):
            p = [None, None]
            p[a], p[b] = Fraction(2 * seam + 1, 2), Fraction(lo + hi, 2)
            if inside(ring, *p) and not any(contains(t["rect"], *p) for t in timbers):
                failures.append(dict(check="R03B_MAIN_LINE_COVERED", seam=seam, interval=[lo, hi]))
    for t in timbers:
        if t["kind"] != "main":
            continue
        r = t["rect"]
        for end in (r[b], r[b + 2]):
            supporters = [s for s in timbers if s["kind"] == "boundary"
                          and end in (s["rect"][b], s["rect"][b + 2])
                          and s["rect"][a] <= r[a] and s["rect"][a + 2] >= r[a + 2]
                          and s.get("edge", [0, -1])[0] <= r[a]
                          and s.get("edge", [0, -1])[1] >= r[a + 2]]
            if not supporters:
                failures.append(dict(check="R03B_MAIN_END_ON_RC_BOUNDARY", id=t["id"], end=end))
    boards, board_failures = board_supports(room, result, params)
    failures.extend(board_failures)
    return failures, boards


def construct(room, layout=None, params=None):
    layout = dict(LAYOUT if layout is None else layout)
    params = dict(PARAMS if params is None else params)
    normalized, shape = normalize_room(room)
    result = REFERENCE.build(normalized, layout, params)
    old_fails = REFERENCE.check(result, params)
    old_verdict, old_problems = REFERENCE.verdict(result, params, old_fails)
    independent, boards = independent_check(normalized, result, params)
    output = dict(schema="r03-single-notch-reference/1", params=params, layout=layout,
                  room=normalized, shape=shape, reference_verdict=old_verdict,
                  reference_failures=old_fails, reference_problems=old_problems,
                  conflicts=result["conflicts"], core_limits=result["core_limits"],
                  seams_a=result["seams_a"], seams_b=result["seams_b"],
                  moved_a=result["moved_a"], moved_b=result["moved_b"],
                  timbers=timber_rows(result), boards=boards,
                  independent_failures=independent)
    return output, result


def l_room(width=3740, height=3301, cut_x=2500, cut_y=2000):
    return dict(outer=[[0, 0], [width, 0], [width, cut_y],
                      [cut_x, cut_y], [cut_x, height], [0, height]])


def u_room(width=3880, height=3600, depth=300, begin=1500, extent=400):
    return dict(outer=[[0, 0], [width, 0], [width, begin], [width - depth, begin],
                      [width - depth, begin + extent], [width, begin + extent],
                      [width, height], [0, height]])


def mutation_triplets(params=None):
    """Data withdrawals check the checker; they are NOT product-source mutations."""
    params = dict(PARAMS if params is None else params)
    room, _ = normalize_room(L_ROOM)
    _, original = construct(room, params=params)
    def verdict(candidate):
        fails, _ = independent_check(room, candidate, params)
        return int(bool(fails)), sorted({f["check"] for f in fails})
    mutations = {}
    m = deepcopy(original)
    m["timbers"] = [t for t in m["timbers"] if t["id"] != 0]
    mutations["R03B_WITHDRAW_WALL_BOARD_SUPPORT"] = (m, "R03B_BOARD_EDGE_UNSUPPORTED")
    m = deepcopy(original)
    m["timbers"] = [t for t in m["timbers"]
                    if not (t["kind"] == "boundary" and t.get("rc_line") == 2000)]
    notch_failures, _ = independent_check(room, m, params)
    assert any(f["check"] == "R03B_BOARD_EDGE_UNSUPPORTED" and f["side"]["at"] == 2000
               for f in notch_failures), "R03B_TRUE_NOTCH_CUT_EDGE_OBSERVED"
    mutations["R03B_WITHDRAW_NOTCH_CUT_EDGE_SUPPORT"] = (m, "R03B_BOARD_EDGE_UNSUPPORTED")
    m = deepcopy(original)
    m["timbers"].append(dict(m["timbers"][0], id=999))
    mutations["R03B_ALLOW_OVERLAPPING_MEMBERS"] = (m, "R03B_NO_OVERLAP")
    m = deepcopy(original)
    m["timbers"][0]["rect"] = [-1, 0, 3740, 27]
    mutations["R03B_ALLOW_MEMBER_THROUGH_WALL"] = (m, "R03B_NO_WALL_CROSSING")
    m = deepcopy(original)
    main = next(t for t in m["timbers"] if t["kind"] == "main")
    lo, hi = main["rect"][1], main["rect"][3]
    mid = (lo + hi) // 2
    top, bottom = list(main["rect"]), list(main["rect"])
    top[3], bottom[1] = mid - 50, mid + 50
    main["rect"] = top
    m["timbers"].append(dict(main, id=999, rect=bottom))
    mutations["R03B_SPLIT_MAIN_INSIDE_ROOM"] = (m, "R03B_MAIN_END_ON_RC_BOUNDARY")
    m = deepcopy(original)
    m["timbers"] += [dict(m["timbers"][0], id=1000 + i) for i in range(513 - len(m["timbers"]))]
    mutations["R03B_ALLOW_513_MEMBERS"] = (m, "R03B_CAPACITY_512")
    rows = []
    for name, (candidate, expected) in mutations.items():
        before, _ = verdict(original)
        withdrawn, failures = verdict(candidate)
        restored, _ = verdict(original)
        assert [before, withdrawn, restored] == [0, 1, 0], (name, before, withdrawn, restored)
        assert expected in failures, (name, expected, failures)
        rows.append(dict(name=name, exits=[before, withdrawn, restored], exact_check=expected,
                         kind="checker-data-withdrawal"))
    # Moving the source origin can produce internally consistent geometry.
    # The independent physical checker deliberately does not infer the origin;
    # unchanged reference C7, which derives expected seams from inputs, catches it.
    shifted = REFERENCE.build(room, LAYOUT, params, {"shift_origin"})
    before = REFERENCE.check(original, params)
    wrong = REFERENCE.check(shifted, params)
    restored = REFERENCE.check(original, params)
    assert not before and not restored, "R03B_SOURCE_ORIGIN_BASELINE_RESTORED"
    assert "C7_SEAMS_NOT_FROM_START" in {f["check"] for f in wrong}, "R03B_SOURCE_ORIGIN_EXACT_KILL"
    rows.append(dict(name="R03B_WITHDRAW_SOURCE_ORIGIN", exits=[0, 1, 0],
                     exact_check="C7_SEAMS_NOT_FROM_START", kind="historical-constructor-test-hook",
                     validator="unchanged-policy-A-reference-C7",
                     independent_physical_check_cannot_prove_origin=True))
    return rows


def rectangle_degeneracy(params=None):
    params = dict(PARAMS if params is None else params)
    outputs = []
    for width, height in ((3740, 3301), (3740, 2000), (2500, 3000)):
        plain = dict(outer=[[0, 0], [width, 0], [width, height], [0, height]])
        for name, degenerate in (("L-zero-width", l_room(width, height, width, height // 2)),
                                 ("L-zero-height", l_room(width, height, width // 2, height)),
                                 ("U-zero-depth", u_room(width, height, 0, height // 3, height // 4)),
                                 ("U-zero-extent", u_room(width, height, width // 4, height // 3, 0))):
            normal, shape = normalize_room(degenerate)
            assert shape["shape"] == "rectangle", "R03B_ZERO_NOTCH_IS_RECTANGLE"
            for layout in REFERENCE.LAYOUTS:
                old = REFERENCE.build(plain, layout, params)
                new = REFERENCE.build(normal, layout, params)
                assert timber_rows(old) == timber_rows(new), "R03B_ZERO_NOTCH_EXACT_V2_MEMBERS"
                assert old["seams_a"] == new["seams_a"] and old["seams_b"] == new["seams_b"], "R03B_ZERO_NOTCH_EXACT_V2_SEAMS"
                outputs.append(dict(case=name, width=width, height=height, layout=layout,
                                    timbers=len(new["timbers"]), verdict=REFERENCE.verdict(new, params)[0]))
    return outputs


def scan(out_dir, params=None):
    params = dict(PARAMS if params is None else params)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, counts = [], Counter()
    max_members = 0
    for family, coordinate, values in (("L-cut-x", "cut_x", range(2490, 2511)),
                                       ("L-cut-y", "cut_y", range(1990, 2011)),
                                       ("U-depth", "depth", range(290, 311)),
                                       ("U-begin", "begin", range(1490, 1511)),
                                       ("U-extent", "extent", range(390, 411))):
        for value in values:
            room = l_room(**{coordinate: value}) if family.startswith("L") else u_room(**{coordinate: value})
            for layout in REFERENCE.LAYOUTS:
                output, _ = construct(room, layout, params)
                counts[output["reference_verdict"]] += 1
                max_members = max(max_members, len(output["timbers"]))
                if output["reference_verdict"] == "buildable" and output["independent_failures"]:
                    counts["independent_failure"] += 1
                rows.append(dict(family=family, varying_mm=value, layout=layout,
                                 members=len(output["timbers"]),
                                 verdict=output["reference_verdict"],
                                 conflicts=output["conflicts"],
                                 independent_failures=output["independent_failures"],
                                 seams_a=output["seams_a"], seams_b=output["seams_b"],
                                 timber_values=[[t["id"], t["kind"], t["role"], t["priority"],
                                                 *t["rect"], t["length"]] for t in output["timbers"]],
                                 geometry_sha256=hashlib.sha256(canonical_json(output["timbers"]).encode()).hexdigest()))
    raw = "".join(canonical_json(row) + "\n" for row in rows).encode()
    (out_dir / "r03b-notch-scan.jsonl").write_bytes(raw)
    summary = dict(schema="r03-single-notch-scan/1", params=params, step_mm=1,
                   parameter_ranges={"L-cut-x": [2490, 2510], "L-cut-y": [1990, 2010],
                                     "U-depth": [290, 310], "U-begin": [1490, 1510], "U-extent": [390, 410]},
                   layouts=8, total=len(rows), counts=dict(counts), max_members=max_members,
                   raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                   limitations="Independent geometry checks do not replace native I8/R43 or Chrome acceptance.")
    (out_dir / "r03b-notch-scan-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    assert not counts["independent_failure"], "R03B_SCAN_INDEPENDENT_VIOLATION"
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON {room, layout?, params?}; L/U or zero-notch rectangle")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--scan", type=Path, help="write exact 1 mm scan JSONL and summary")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--gap", type=int, choices=(2, 3), default=2)
    args = parser.parse_args()
    params = dict(PARAMS, gap=args.gap)
    if args.input:
        request = json.loads(args.input.read_text(encoding="utf-8"))
        output, _ = construct(request["room"], request.get("layout"), request.get("params", params))
        text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    if args.self_test or not args.input and not args.scan:
        for name, room in (("L", L_ROOM), ("U", U_ROOM)):
            output, _ = construct(room, params=params)
            assert output["reference_verdict"] == "buildable", "R03B_REFERENCE_BUILDABLE"
            assert not output["independent_failures"], "R03B_INDEPENDENT_CHECKS"
            print(canonical_json(dict(case=name, members=len(output["timbers"]), boards=len(output["boards"]))))
        print(canonical_json(dict(params=params, rectangle_degeneracy=rectangle_degeneracy(params))))
        print(canonical_json(dict(mutations=mutation_triplets(params))))
    if args.scan:
        print(canonical_json(scan(args.scan, params)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
