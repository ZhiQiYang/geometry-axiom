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


def merge_intervals(intervals):
    merged = []
    for lo, hi in sorted(intervals):
        if lo >= hi:
            continue
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def room_line_intervals(ring, axis, at):
    """Intervals along 1-axis at a fixed axis coordinate; only input ring is read."""
    along = 1 - axis
    cuts = sorted({p[along] for p in ring})
    spans = []
    for lo, hi in zip(cuts, cuts[1:]):
        point = [at, at]
        point[along] = Fraction(lo + hi, 2)
        if inside(ring, *point):
            spans.append([lo, hi])
    return merge_intervals(spans)


def room_band_intervals(ring, axis, lo, hi):
    """Full-width footprint containment, including every wall-coordinate cut."""
    cuts = sorted({lo, hi} | {p[axis] for p in ring if lo < p[axis] < hi})
    spans = [[min(p[1 - axis] for p in ring), max(p[1 - axis] for p in ring)]]
    for lower, upper in zip(cuts, cuts[1:]):
        section = room_line_intervals(ring, axis, Fraction(lower + upper, 2))
        spans = merge_intervals([[max(x0, y0), min(x1, y1)]
                                 for x0, x1 in spans for y0, y1 in section
                                 if max(x0, y0) < min(x1, y1)])
    return spans


def rc_walls(ring, width):
    """Reconstruct true fixed RC bands from physical ring edges, never timber metadata."""
    walls = []
    for first, second in zip(ring, ring[1:] + ring[:1]):
        normal = 0 if first[0] == second[0] else 1
        along, at = 1 - normal, first[normal]
        span = sorted([first[along], second[along]])
        probe = [Fraction(at) + Fraction(1, 2), Fraction(at) + Fraction(1, 2)]
        probe[along] = Fraction(sum(span), 2)
        inward = 1 if inside(ring, *probe) else -1
        band = sorted([at, at + inward * width])
        rect = [None] * 4
        rect[normal], rect[normal + 2] = band
        rect[along], rect[along + 2] = span
        walls.append(dict(normal=normal, at=at, span=span, inward=inward, rect=rect))
    return walls


def input_seams(room, layout, params):
    """Independent G6/G7 and short-face retreat, plus the input-derived P182 set.

    P182 preference among feasible constructions remains the historical C7's
    separate policy check.  This checker derives the finite candidate set from
    RC geometry and never accepts a constructor-invented center or origin.
    """
    ring = room["outer"]
    a = 0 if layout["A"] == "x" else 1
    box = [min(p[0] for p in ring), min(p[1] for p in ring),
           max(p[0] for p in ring), max(p[1] for p in ring)]
    walls = rc_walls(ring, params["w"])

    def local_depth(axis, distance, start):
        low, high = box[axis], box[axis + 2]
        coordinate = (low + distance - Fraction(1, 2) if start == "min"
                      else high - distance + Fraction(1, 2))
        depths = []
        along = 1 - axis
        cuts = sorted({p[along] for p in ring})
        for lower, upper in zip(cuts, cuts[1:]):
            mid = Fraction(lower + upper, 2)
            for begin, end in room_line_intervals(ring, along, mid):
                if begin < coordinate < end:
                    depths.append(end - low if start == "min" else high - begin)
        return min(depths, default=high - low)

    def settle(axis, distance, previous, start):
        while True:
            depth = local_depth(axis, distance, start)
            inward = (2 * depth - 3 * params["w"]) // 2
            if distance * 2 <= 2 * depth - 3 * params["w"] or (
                    previous is not None and inward <= previous):
                return distance
            distance = inward

    seams = {}
    for axis, panel, start in ((a, params["P"], layout["a_start"]),
                                (1 - a, params["L"], layout["b_start"])):
        span, period = box[axis + 2] - box[axis], panel + params["gap"]
        half_gap = params["gap"] // 2 if start == "min" else (params["gap"] + 1) // 2
        distances = [panel + half_gap + index * period for index in range((span - 1) // period)]
        if distances:
            distances[-1] = settle(axis, distances[-1], distances[-2] if len(distances) > 1 else None, start)
        seams[axis] = [box[axis] + d if start == "min" else box[axis + 2] - d for d in distances]

    # Parallel short RC faces: convex endpoints lose one perpendicular width;
    # a remaining < min_piece face cannot carry a seam bearing strip.
    b, start = 1 - a, layout["b_start"]
    short_faces = []
    for wall in walls:
        if wall["normal"] != a:
            continue
        lower, upper = wall["span"]
        remaining, reflex = [lower, upper], []
        for endpoint, direction, index in ((lower, 1, 0), (upper, -1, 1)):
            cross_low, cross_high = sorted([wall["at"], wall["at"] + wall["inward"] * params["w"]])
            convex = any(other["normal"] == b and other["at"] == endpoint
                         and other["inward"] == direction
                         and other["span"][0] <= cross_low and cross_high <= other["span"][1]
                         for other in walls)
            if convex:
                remaining[index] += direction * params["w"]
            else:
                reflex.append(endpoint)
        if 0 < remaining[1] - remaining[0] < params["min_piece"]:
            short_faces.append((remaining, reflex))
    while seams[b]:
        last = seams[b][-1]
        bearing = [[last - params["gap"] // 2 - params["X"], last - params["gap"] // 2],
                   [last + (params["gap"] + 1) // 2, last + (params["gap"] + 1) // 2 + params["X"]]]
        hits = [(span, reflex) for span, reflex in short_faces
                if any(max(lo, span[0]) < min(hi, span[1]) for lo, hi in bearing)]
        if not hits:
            break
        span, reflex = hits[0]
        ends = [end for end in reflex if (end <= span[0] if start == "min" else end >= span[1])]
        if not ends:
            break
        end = max(ends) if start == "min" else min(ends)
        distance = (2 * (end - box[b] if start == "min" else box[b + 2] - end) - 3 * params["w"]) // 2
        old_distance = last - box[b] if start == "min" else box[b + 2] - last
        previous = None if len(seams[b]) < 2 else (seams[b][-2] - box[b] if start == "min" else box[b + 2] - seams[b][-2])
        if distance >= old_distance or (previous is not None and distance <= previous):
            break
        distance = settle(b, distance, previous, start)
        seams[b][-1] = box[b] + distance if start == "min" else box[b + 2] - distance

    candidates = []
    if seams[a]:
        start = layout["a_start"]
        initial = seams[a][-1] - box[a] if start == "min" else box[a + 2] - seams[a][-1]
        previous = None if len(seams[a]) < 2 else (seams[a][-2] - box[a] if start == "min" else box[a + 2] - seams[a][-2])
        pending, seen = [initial], {initial}
        half = (params["w"] + 1) // 2
        while pending:
            distance = pending.pop()
            center = box[a] + distance if start == "min" else box[a + 2] - distance
            for wall in walls:
                if wall["normal"] != a or max(wall["rect"][a], center - half) >= min(wall["rect"][a + 2], center + half):
                    continue
                wall_distance = wall["at"] - box[a] if start == "min" else box[a + 2] - wall["at"]
                inward = (2 * wall_distance - 3 * params["w"]) // 2
                if inward < initial and (previous is None or inward > previous) and inward not in seen:
                    seen.add(inward)
                    pending.append(inward)
        candidates = [seams[a][:-1] + [box[a] + distance if start == "min" else box[a + 2] - distance]
                      for distance in sorted(seen, reverse=True)]
    return dict(a=a, b=b, bbox=box, seams_a=seams[a], seams_b=seams[b],
                seam_candidates_a=candidates or [[]], walls=walls)


def material_components(rectangles):
    """Interior-connected components; corner contact is never an adjacency."""
    remaining, components = set(range(len(rectangles))), []
    while remaining:
        todo = [remaining.pop()]
        indices = []
        while todo:
            index = todo.pop()
            indices.append(index)
            rect = rectangles[index]
            neighbours = [other for other in remaining
                          if any((rect[axis + 2] == rectangles[other][axis]
                                  or rectangles[other][axis + 2] == rect[axis])
                                 and max(rect[1 - axis], rectangles[other][1 - axis])
                                 < min(rect[3 - axis], rectangles[other][3 - axis])
                                 for axis in (0, 1))]
            remaining.difference_update(neighbours)
            todo.extend(neighbours)
        components.append(sorted([rectangles[index] for index in indices]))
    return sorted(components, key=lambda component: min((rect[0], rect[1]) for rect in component))


def side_segments(ring, cell):
    """True boundary of cell intersect polygon, grouped into four normal directions."""
    grid = list(cells(cell, ring=ring))
    occupied = [r for r in grid if inside(ring, *midpoint(r))]
    return component_sides(occupied), occupied


def component_sides(occupied):
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
    return out


def component_rings(sides):
    """Trace material-left physical edges; no rectangle-decomposition edges."""
    edges = set()
    for side in sides:
        axis, sign, at = side["axis"], side["outward"], side["at"]
        lo, hi = side["interval"]
        first, last = ((at, lo), (at, hi)) if axis == 0 else ((lo, at), (hi, at))
        if (axis == 0 and sign < 0) or (axis == 1 and sign > 0):
            first, last = last, first
        edges.add((first, last))
    rings = []
    while edges:
        first, last = min(edges)
        edges.remove((first, last))
        ring = [first]
        while last != first:
            ring.append(last)
            following = sorted(edge for edge in edges if edge[0] == last)
            assert len(following) == 1, "R03B_R42_SIMPLE_COMPONENT_BOUNDARY"
            begin, last = following[0]
            edges.remove((begin, last))
        index = ring.index(min(ring))
        rings.append([list(point) for point in ring[index:] + ring[:index]])
    return sorted(rings, key=lambda ring: tuple(ring[0]))


def bearing_profile(side, occupied, timbers):
    """Actual continuous width from a physical board edge, separately from X."""
    axis, inward = side["axis"], -side["outward"]
    along, at = 1 - axis, side["at"]
    lo, hi = side["interval"]
    rectangles = occupied + [t["rect"] for t in timbers]
    stops = sorted({lo, hi} | {value for rect in rectangles for value in (rect[along], rect[along + 2]) if lo < value < hi})
    profile = []
    for begin, end in zip(stops, stops[1:]):
        pos = Fraction(begin + end, 2)
        relevant = [r for r in rectangles if r[along] < pos < r[along + 2]]
        depths = sorted({0} | {inward * (value - at) for rect in relevant for value in (rect[axis], rect[axis + 2])
                               if inward * (value - at) > 0})
        width, material_width, continuous, owners = 0, 0, True, set()
        for near, far in zip(depths, depths[1:]):
            point = [pos, pos]
            point[axis] = at + inward * Fraction(near + far, 2)
            covered = [t["id"] for t in timbers if contains(t["rect"], *point)]
            if not any(contains(r, *point) for r in occupied):
                break
            material_width = far
            continuous = continuous and bool(covered)
            if continuous:
                width = far
                owners.update(covered)
        row = dict(interval=[begin, end], continuous_width=width, material_width=material_width, supports=sorted(owners))
        if profile and profile[-1]["continuous_width"] == width and profile[-1]["material_width"] == material_width and profile[-1]["supports"] == row["supports"]:
            profile[-1]["interval"][1] = end
        else:
            profile.append(row)
    return profile


def board_component_supports(ring, cell, occupied, timbers, params, key, component_id):
    rectangles = [list(t["rect"]) for t in timbers]
    sides = component_sides(occupied)
    edge_rows, failures = [], []
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
        # R-nosliver bridges only the along-edge gap between two material
        # flanks of this component.  It never changes transverse X.
        bridged = []
        for gap in gaps:
            along = 1 - axis
            length = gap[along + 2] - gap[along]
            flanks = []
            for end, direction in ((gap[along], -1), (gap[along + 2], 1)):
                slab = list(gap)
                slab[along], slab[along + 2] = sorted([end, end + direction])
                covered = all(any(contains(t["rect"], *midpoint(atom)) for t in timbers)
                              and any(contains(r, *midpoint(atom)) for r in occupied)
                              for atom in cells(slab, rectangles + occupied))
                flanks.append(covered)
            if length < params["min_piece"] and all(flanks):
                bridged.append(dict(rect=gap, length=length, exclusive_limit=params["min_piece"],
                                    reason="R-nosliver-along-edge-two-flanks"))
            else:
                failures.append(dict(check="R03B_BOARD_EDGE_UNSUPPORTED", board=key,
                                     componentId=component_id, side=side, gap=gap))
        profile = bearing_profile(side, occupied, timbers)
        for segment in profile:
            if segment["material_width"] < params["X"]:
                failures.append(dict(check="R03B_BOARD_EDGE_BEARING_TOO_NARROW", board=key,
                                     componentId=component_id, side=side, segment=segment,
                                     required_width=params["X"]))
        edge_rows.append(dict(direction="xy"[axis] + ("+" if sign > 0 else "-"),
                              at=at, interval=[lo, hi], bearing_width=params["X"],
                              bearing_segments=profile,
                              supports=[dict(id=k, bands=v) for k, v in sorted(contact.items())],
                              short_edge_bridges=bridged))
    return dict(key=key, componentId=component_id, nominal=cell, clipped_cells=occupied,
                rings=component_rings(sides), sides=edge_rows), failures


def board_supports(room, result, params, layout=None, derived=None):
    ring = room["outer"]
    layout = dict(LAYOUT if layout is None else layout)
    derived = input_seams(room, layout, params) if derived is None else derived
    a, b = derived["a"], derived["b"]
    box = [min(p[0] for p in ring), min(p[1] for p in ring),
           max(p[0] for p in ring), max(p[1] for p in ring)]
    spans = {}
    for axis, seams in ((a, derived["seams_a"]), (b, derived["seams_b"])):
        cur = box[axis]
        spans[axis] = []
        for center in sorted(seams):
            spans[axis].append([cur, center - params["gap"] // 2])
            cur = center + params["gap"] - params["gap"] // 2
        spans[axis].append([cur, box[axis + 2]])
    boards, failures = [], []
    timbers = result["timbers"]
    for ix, xp in enumerate(spans[0]):
        for iy, yp in enumerate(spans[1]):
            cell = [xp[0], yp[0], xp[1], yp[1]]
            if cell[0] >= cell[2] or cell[1] >= cell[3]:
                continue
            _, occupied = side_segments(ring, cell)
            if not occupied:
                continue
            components = material_components(occupied)
            for component_id, component in enumerate(components):
                board, board_failures = board_component_supports(ring, cell, component, timbers, params,
                                                                 [ix, iy], component_id)
                boards.append(board)
                failures.extend(board_failures)
    return boards, failures


def verified_rc_contacts(timbers, walls, a, width):
    contacts, failures = [], []
    for timber in timbers:
        kind, rect = timber["kind"], timber["rect"]
        if kind not in ("boundary", "rc_parallel"):
            continue
        normal = 1 - a if kind == "boundary" else a
        fixed = []
        for wall in walls:
            if wall["normal"] != normal or rect[normal] != wall["rect"][normal] or rect[normal + 2] != wall["rect"][normal + 2]:
                continue
            footprint = intersect(rect, wall["rect"])
            if footprint:
                fixed.append(dict(id=timber["id"], kind=kind, rect=footprint,
                                  normal=normal, wall_at=wall["at"], inward=wall["inward"]))
        if kind == "boundary" and not fixed:
            failures.append(dict(check="R03B_BOUNDARY_HAS_TRUE_RC_FIXED_SEGMENT", id=timber["id"], rect=rect))
        contacts.extend(fixed)
    return contacts, failures


def main_spans_from_ring(ring, walls, a, cross, width):
    """Every full-width connected room span must terminate at true RC fixed faces."""
    b, spans = 1 - a, []
    for low, high in room_band_intervals(ring, a, *cross):
        ends = []
        for at, direction in ((low, 1), (high, -1)):
            matches = [wall for wall in walls if wall["normal"] == b and wall["at"] == at
                       and wall["inward"] == direction
                       and wall["span"][0] <= cross[0] and cross[1] <= wall["span"][1]]
            ends.append(matches)
        if all(ends) and low + width < high - width:
            spans.append(dict(interval=[low + width, high - width], rc_ends=[low, high]))
    return spans


def independent_main_checks(room, timbers, params, derived):
    ring, a, b = room["outer"], derived["a"], derived["b"]
    width, walls = params["w"], derived["walls"]
    contacts, failures = verified_rc_contacts(timbers, walls, a, width)
    genuine_boundary = {contact["id"] for contact in contacts if contact["kind"] == "boundary"}
    valid_main = set()
    for timber in timbers:
        if timber["kind"] != "main":
            continue
        rect = timber["rect"]
        cross = [rect[a], rect[a + 2]]
        expected = main_spans_from_ring(ring, walls, a, cross, width)
        valid_span = next((span for span in expected if span["interval"] == [rect[b], rect[b + 2]]), None)
        if valid_span is None:
            failures.append(dict(check="R03B_MAIN_CONTINUOUS_TRUE_RC_SPAN", id=timber["id"],
                                 got=[rect[b], rect[b + 2]], expected=expected))
        supported_ends = []
        for end, direction in ((rect[b], -1), (rect[b + 2], 1)):
            supporters = [contact for contact in contacts if contact["kind"] == "boundary"
                          and contact["rect"][a] <= cross[0] and cross[1] <= contact["rect"][a + 2]
                          and contact["rect"][b + 2 if direction < 0 else b] == end
                          and contact["inward"] == -direction]
            supported_ends.append(supporters)
            if not supporters:
                failures.append(dict(check="R03B_MAIN_END_ON_RC_BOUNDARY", id=timber["id"], end=end))
        if valid_span is not None and all(supported_ends) and cross[1] - cross[0] == width:
            valid_main.add(timber["id"])
        elif cross[1] - cross[0] != width:
            failures.append(dict(check="R03B_MAIN_EXACT_WIDTH", id=timber["id"], got=cross[1] - cross[0], expected=width))

    # Source-derived seam obligations are evaluated even if all main rows or
    # their seam declarations have been deleted/retyped.  Only real fixed RC
    # bands or an uncut main (possibly via touching parallel doubling) qualify.
    for seam in derived["seams_a"]:
        required = room_line_intervals(ring, a, Fraction(2 * seam + 1, 2))
        cuts = sorted({value for span in required for value in span}
                      | {value for t in timbers for value in (t["rect"][b], t["rect"][b + 2])}
                      | {value for contact in contacts for value in (contact["rect"][b], contact["rect"][b + 2])})
        missing = []
        for lo, hi in zip(cuts, cuts[1:]):
            along = Fraction(lo + hi, 2)
            if not any(start < along < end for start, end in required):
                continue
            point = [along, along]
            point[a] = Fraction(2 * seam + 1, 2)
            if any(contains(contact["rect"], *point) for contact in contacts):
                continue
            parallel = [t for t in timbers if t["rect"][b] < along < t["rect"][b + 2]
                        and (t["id"] in genuine_boundary or
                             (t["rect"][a + 2] - t["rect"][a] == width
                              and (t["id"] in valid_main or t["kind"] in ("doubling", "rc_parallel"))))]
            groups = merge_intervals([[t["rect"][a], t["rect"][a + 2]] for t in parallel])
            supported = any(lower <= seam < upper
                            and any(t["id"] in valid_main and lower <= t["rect"][a]
                                    and t["rect"][a + 2] <= upper for t in parallel)
                            for lower, upper in groups)
            if not supported:
                missing.append([lo, hi])
        for lo, hi in merge_intervals(missing):
            # Retain the historical strict along-seam short-gap exception only
            # when both flanks themselves have true RC/main load paths.
            flanked = all(any(begin < probe < end for begin, end in required)
                          and not any(begin < probe < end for begin, end in missing)
                          for probe in (Fraction(2 * lo - 1, 2), Fraction(2 * hi + 1, 2)))
            if hi - lo < params["min_piece"] and flanked:
                continue
            failures.append(dict(check="R03B_REQUIRED_MAIN_RC_SPAN", seam=seam, interval=[lo, hi]))
    return failures


def independent_check(room, result, params, layout=None):
    """Physical output checks. It deliberately does not trust oracle verdict/metadata."""
    layout = dict(LAYOUT if layout is None else layout)
    ring = room["outer"]
    timbers = result["timbers"]
    failures = []
    derived = input_seams(room, layout, params)
    if (result.get("a"), result.get("b")) != (derived["a"], derived["b"]):
        failures.append(dict(check="R03B_AXES_FROM_INPUT", expected=[derived["a"], derived["b"]],
                             got=[result.get("a"), result.get("b")]))
    matched = next((candidate for candidate in derived["seam_candidates_a"]
                    if sorted(candidate) == sorted(result.get("seams_a", []))), None)
    seams_match = matched is not None and sorted(derived["seams_b"]) == sorted(result.get("seams_b", []))
    if not seams_match:
        failures.append(dict(check="R03B_SEAMS_FROM_INPUT", expected_a=derived["seams_a"],
                             allowed_a=derived["seam_candidates_a"], expected_b=derived["seams_b"],
                             got_a=result.get("seams_a"), got_b=result.get("seams_b")))
    if matched is not None:
        derived["seams_a"] = matched
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
    failures.extend(independent_main_checks(room, timbers, params, derived))
    boards, board_failures = board_supports(room, result, params, layout, derived)
    failures.extend(board_failures)
    return failures, boards


def construct(room, layout=None, params=None):
    layout = dict(LAYOUT if layout is None else layout)
    params = dict(PARAMS if params is None else params)
    normalized, shape = normalize_room(room)
    result = REFERENCE.build(normalized, layout, params)
    old_fails = REFERENCE.check(result, params)
    old_verdict, old_problems = REFERENCE.verdict(result, params, old_fails)
    independent, boards = independent_check(normalized, result, params, layout)
    derived = input_seams(normalized, layout, params)
    output = dict(schema="r03-single-notch-reference/2", params=params, layout=layout,
                  room=normalized, shape=shape, reference_verdict=old_verdict,
                  reference_failures=old_fails, reference_problems=old_problems,
                  conflicts=result["conflicts"], core_limits=result["core_limits"],
                  seams_a=result["seams_a"], seams_b=result["seams_b"],
                  moved_a=result["moved_a"], moved_b=result["moved_b"],
                  timbers=timber_rows(result), boards=boards,
                  independent_failures=independent,
                  independent_input_geometry={k: v for k, v in derived.items() if k != "walls"},
                  policy_preference_check="historical-C7; independent checker certifies input-derived candidates and physical spans")
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
    # Keep the original historical constructor hook as a separate old result.
    # v2 additionally detects its input-origin error without invoking C7.
    shifted = REFERENCE.build(room, LAYOUT, params, {"shift_origin"})
    before = REFERENCE.check(original, params)
    wrong = REFERENCE.check(shifted, params)
    restored = REFERENCE.check(original, params)
    assert not before and not restored, "R03B_SOURCE_ORIGIN_BASELINE_RESTORED"
    assert "C7_SEAMS_NOT_FROM_START" in {f["check"] for f in wrong}, "R03B_SOURCE_ORIGIN_EXACT_KILL"
    rows.append(dict(name="R03B_WITHDRAW_SOURCE_ORIGIN", exits=[0, 1, 0],
                     exact_check="C7_SEAMS_NOT_FROM_START", kind="historical-constructor-test-hook",
                     validator="unchanged-policy-A-reference-C7"))
    before, _ = verdict(original)
    withdrawn, failures = verdict(shifted)
    restored, _ = verdict(original)
    assert [before, withdrawn, restored] == [0, 1, 0], "R03B_INDEPENDENT_ORIGIN_TRIPLET"
    assert "R03B_SEAMS_FROM_INPUT" in failures, "R03B_INDEPENDENT_ORIGIN_EXACT_KILL"
    rows.append(dict(name="R03B_SHIFTED_SOURCE_ORIGIN_DATA", exits=[before, withdrawn, restored],
                     exact_check="R03B_SEAMS_FROM_INPUT", kind="checker-data-withdrawal"))
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
    counts = Counter()
    max_members = total = raw_bytes = 0
    digest = hashlib.sha256()
    # Each fully checked case is serialized once in the historical order.
    # Keep only that case alive: complete board witnesses can be large.
    with (out_dir / "r03b-notch-scan.jsonl").open("wb") as stream:
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
                    row = dict(family=family, varying_mm=value, layout=layout,
                               members=len(output["timbers"]),
                               verdict=output["reference_verdict"],
                               conflicts=output["conflicts"],
                               independent_failures=output["independent_failures"],
                               independent_input_geometry=output["independent_input_geometry"],
                               seams_a=output["seams_a"], seams_b=output["seams_b"],
                               boards=output["boards"],
                               timber_values=[[t["id"], t["kind"], t["role"], t["priority"],
                                               *t["rect"], t["length"]] for t in output["timbers"]],
                               geometry_sha256=hashlib.sha256(canonical_json(output["timbers"]).encode()).hexdigest())
                    raw = (canonical_json(row) + "\n").encode()
                    stream.write(raw)
                    digest.update(raw)
                    total += 1
                    raw_bytes += len(raw)
    summary = dict(schema="r03-single-notch-scan/2", params=params, step_mm=1,
                   parameter_ranges={"L-cut-x": [2490, 2510], "L-cut-y": [1990, 2010],
                                     "U-depth": [290, 310], "U-begin": [1490, 1510], "U-extent": [390, 410]},
                   layouts=8, total=total, counts=dict(counts), max_members=max_members,
                   raw_bytes=raw_bytes, raw_sha256=digest.hexdigest(),
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
