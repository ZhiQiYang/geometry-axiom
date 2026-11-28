"""PF-5 diagnostic envelope constructor, independent of the application runtime.

This is a deliberately separate JSON format, not a native command/scene API.
It implements the geometry subset of D41/I53/R41, not source edge identities,
panel layout, timber placement, support, capacity limits, or transaction rules.
All numeric dimensions and every finish/obstacle membership are explicit.
The timber result is an available layer envelope: section A is retained
metadata, and h is section B. Pair volumes are not collision/support/strength
verdicts for actual placed D7 members; cross-finish support is not inferred.
"""
import argparse
import copy
import itertools
import json
import re
import sys


LIMIT = 100_000_000


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError("PF5_CLOSED_SCHEMA: expected fields " + names)


def _integer(value, label, positive=False):
    if type(value) is not int or abs(value) > LIMIT or (positive and value <= 0):
        raise ValueError("PF5_INTEGER_MM: " + label)
    return value


def _identity(value, positive=False):
    if type(value) is not int or not (int(positive) <= value <= 4_294_967_295):
        raise ValueError("PF5_UINT32_IDENTITY")
    return value


def _vector(value, count, label):
    if not isinstance(value, list) or len(value) != count:
        raise ValueError("PF5_EXPLICIT_VECTOR: " + label)
    return [_integer(x, label) for x in value]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _area(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1])) // 2


def _segments(ring):
    return list(zip(ring, ring[1:]+ring[:1]))


def _segment_intersection(a, b, c, d):
    lo = [max(min(a[k], b[k]), min(c[k], d[k])) for k in range(2)]
    hi = [min(max(a[k], b[k]), max(c[k], d[k])) for k in range(2)]
    return (lo, hi) if all(lo[k] <= hi[k] for k in range(2)) else None


def _inside(ring, x2, y2):
    # Open interior, using doubled coordinates to keep slab midpoints exact.
    count = 0
    for a, b in _segments(ring):
        if a[0] == b[0] and min(a[1], b[1])*2 < y2 < max(a[1], b[1])*2:
            if 2*a[0] == x2:
                return False
            count += 2*a[0] > x2
        elif a[1] == b[1] and 2*a[1] == y2 and min(a[0], b[0])*2 <= x2 <= max(a[0], b[0])*2:
            return False
        # Ray crossing at a vertex uses one half-open endpoint.
    count = sum(a[0] == b[0] and min(a[1], b[1])*2 <= y2 < max(a[1], b[1])*2
                and 2*a[0] > x2 for a, b in _segments(ring))
    return bool(count % 2)


def _validate_ring(ring):
    if not isinstance(ring, list) or len(ring) < 4:
        raise ValueError("PF5_SIMPLE_ORTHOGONAL_RING")
    for point in ring:
        _vector(point, 2, "ring point")
    edges = _segments(ring)
    for a, b in edges:
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise ValueError("PF5_SIMPLE_ORTHOGONAL_RING: nonorthogonal or zero edge")
    for i, (a, b) in enumerate(edges):
        for j in range(i+1, len(edges)):
            c, d = edges[j]
            intersection = _segment_intersection(a, b, c, d)
            if intersection is None:
                continue
            adjacent = j == i+1 or (i == 0 and j == len(edges)-1)
            if not adjacent or intersection[0] != intersection[1]:
                raise ValueError("PF5_SIMPLE_ORTHOGONAL_RING: self intersection")
    if not _area(ring):
        raise ValueError("PF5_SIMPLE_ORTHOGONAL_RING: zero area")


def _validate_region(region):
    _fields(region, "outer holes")
    outer, holes = region["outer"], region["holes"]
    _validate_ring(outer)
    if not isinstance(holes, list):
        raise ValueError("PF5_EXPLICIT_HOLES")
    for hole in holes:
        _validate_ring(hole)
    rings = [outer] + holes
    for i, first in enumerate(rings):
        for second in rings[i+1:]:
            if any(_segment_intersection(a, b, c, d) is not None
                   for a, b in _segments(first) for c, d in _segments(second)):
                raise ValueError("PF5_REGION_TOPOLOGY: rings touch or intersect")
    for i, hole in enumerate(holes):
        if not _inside(outer, 2*hole[0][0], 2*hole[0][1]):
            raise ValueError("PF5_REGION_TOPOLOGY: hole outside outer")
        for other in holes[i+1:]:
            if _inside(hole, 2*other[0][0], 2*other[0][1]) or _inside(other, 2*hole[0][0], 2*hole[0][1]):
                raise ValueError("PF5_REGION_TOPOLOGY: nested holes")


def _bounds(box):
    low, high = _vector(box["min"], 3, "AABB min"), _vector(box["max"], 3, "AABB max")
    for a, b in zip(low, high):
        _integer(b-a, "AABB extent", positive=True)
    return low, high


def _validate(data):
    _fields(data, "schema room obstacles finishes")
    if data["schema"] != "pf5-geometry-input/1":
        raise ValueError("PF5_INPUT_SCHEMA")
    _fields(data["room"], "min max")
    _bounds(data["room"])
    if not isinstance(data["obstacles"], list) or not isinstance(data["finishes"], list):
        raise ValueError("PF5_EXPLICIT_COLLECTIONS")
    objects = {}
    for obj in data["obstacles"]:
        _fields(obj, "ref min max")
        ref = obj["ref"]
        if not isinstance(ref, str) or not re.fullmatch(r"[bc](0|[1-9][0-9]*)", ref) or ref in objects:
            raise ValueError("PF5_UNIQUE_TYPED_OBSTACLE")
        _identity(int(ref[1:]))
        _bounds(obj)
        objects[ref] = obj
    seen = set()
    for f in data["finishes"]:
        _fields(f, "id label frame side region obstacles thickness section")
        identity = _identity(f["id"], positive=True)
        if identity in seen or not isinstance(f["label"], str):
            raise ValueError("PF5_UNIQUE_FINISH_ID")
        seen.add(identity)
        frame = f["frame"]
        _fields(frame, "origin u v n")
        _vector(frame["origin"], 3, "origin")
        for axis in ("u", "v", "n"):
            vector = _vector(frame[axis], 3, axis)
            if sum(abs(x) for x in vector) != 1:
                raise ValueError("PF5_SIGNED_AXIS_FRAME")
        if _cross(frame["u"], frame["v"]) != frame["n"]:
            raise ValueError("PF5_RIGHT_HANDED_FRAME")
        if type(f["side"]) is not int or f["side"] not in (-1, 1):
            raise ValueError("PF5_EXPLICIT_STRUCTURAL_SIDE")
        _integer(f["thickness"], "panel thickness", positive=True)
        _vector(f["section"], 2, "timber section A/B")
        for x in f["section"]:
            _integer(x, "timber section A/B", positive=True)
        _validate_region(f["region"])
        refs = f["obstacles"]
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs):
            raise ValueError("PF5_EXPLICIT_OBSTACLE_MEMBERSHIP")
        if any(ref not in objects for ref in refs):
            raise ValueError("PF5_DANGLING_OBSTACLE")
        for ring in [f["region"]["outer"]] + f["region"]["holes"]:
            for uv in ring:
                for q in (0, f["thickness"], f["thickness"]+f["section"][1]):
                    for coordinate in _world(f, uv[0], uv[1], q):
                        _integer(coordinate, "derived world coordinate")
    return objects


def _scan_intervals(ring, x2):
    intersections = sorted(a[1] for a, b in _segments(ring)
                           if a[1] == b[1] and min(a[0], b[0])*2 < x2 < max(a[0], b[0])*2)
    return list(zip(intersections[::2], intersections[1::2]))


def _difference(intervals, hole):
    result = []
    for lo, hi in intervals:
        if hole[1] <= lo or hole[0] >= hi:
            result.append((lo, hi))
        else:
            if lo < hole[0]:
                result.append((lo, hole[0]))
            if hole[1] < hi:
                result.append((hole[1], hi))
    return result


def _slabs(region):
    rings = [region["outer"]] + region["holes"]
    xs = sorted({p[0] for ring in rings for p in ring})
    rectangles = []
    for lo, hi in zip(xs, xs[1:]):
        intervals = _scan_intervals(region["outer"], lo+hi)
        for hole in region["holes"]:
            for cut in _scan_intervals(hole, lo+hi):
                intervals = _difference(intervals, cut)
        rectangles.extend((lo, bottom, hi, top) for bottom, top in intervals)
    return rectangles


def _subtract(rect, cut):
    x0, y0, x1, y1 = rect
    a, b, c, d = max(x0, cut[0]), max(y0, cut[1]), min(x1, cut[2]), min(y1, cut[3])
    if a >= c or b >= d:
        return [rect]
    result = []
    if x0 < a:
        result.append((x0, y0, a, y1))
    if c < x1:
        result.append((c, y0, x1, y1))
    if y0 < b:
        result.append((a, y0, c, b))
    if d < y1:
        result.append((a, d, c, y1))
    return result


def _positive_overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def _touch(a, b):
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])


def _connected(a, b):
    return ((a[2] == b[0] or b[2] == a[0]) and max(a[1], b[1]) < min(a[3], b[3])
            or (a[3] == b[1] or b[3] == a[1]) and max(a[0], b[0]) < min(a[2], b[2]))


def _canonical(ring):
    result = [p for i, p in enumerate(ring)
              if not (ring[i-1][0] == p[0] == ring[(i+1) % len(ring)][0]
                      or ring[i-1][1] == p[1] == ring[(i+1) % len(ring)][1])]
    first = min(range(len(result)), key=lambda i: result[i])
    return [list(p) for p in result[first:]+result[:first]]


def _outline(rectangles):
    xs = sorted({r[k] for r in rectangles for k in (0, 2)})
    ys = sorted({r[k] for r in rectangles for k in (1, 3)})
    edges = set()
    for x0, y0, x1, y1 in rectangles:
        ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for a, b in zip(ring, ring[1:]+ring[:1]):
            axis = 0 if a[1] == b[1] else 1
            cuts = xs if axis == 0 else ys
            points = [(k, a[1]) if axis == 0 else (a[0], k)
                      for k in cuts if min(a[axis], b[axis]) <= k <= max(a[axis], b[axis])]
            if a[axis] > b[axis]:
                points.reverse()
            for p, q in zip(points, points[1:]):
                if (q, p) in edges:
                    edges.remove((q, p))
                else:
                    edges.add((p, q))
    successor = {}
    for a, b in edges:
        if a in successor:
            raise ValueError("PF5_DERIVED_TOPOLOGY: touching hole/outer cannot be represented")
        successor[a] = b
    rings = []
    while successor:
        first = min(successor)
        ring = [first]
        current = successor.pop(first)
        while current != first:
            ring.append(current)
            if current not in successor:
                raise ValueError("PF5_DERIVED_TOPOLOGY: open or branched boundary")
            current = successor.pop(current)
        rings.append(_canonical(ring))
    outers = [r for r in rings if _area(r) > 0]
    if len(outers) != 1:
        raise ValueError("PF5_DERIVED_TOPOLOGY: component has no unique outer")
    return outers[0], sorted((r for r in rings if _area(r) < 0), key=lambda r: r[0])


def _region(rectangles):
    rectangles = sorted(rectangles)
    components = []
    remaining = set(range(len(rectangles)))
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        group, todo = [seed], [seed]
        while todo:
            current = todo.pop()
            neighbours = [i for i in sorted(remaining) if _connected(rectangles[current], rectangles[i])]
            remaining.difference_update(neighbours)
            group.extend(neighbours)
            todo.extend(neighbours)
        cells = [rectangles[i] for i in sorted(group)]
        outer, holes = _outline(cells)
        components.append({"rectangles": [list(r) for r in cells], "outer": outer, "holes": holes})
    return {"area": sum((r[2]-r[0])*(r[3]-r[1]) for r in rectangles), "components": components}


def _world(f, u, v, q):
    frame, side = f["frame"], f["side"]
    return [frame["origin"][i] + u*frame["u"][i] + v*frame["v"][i] + q*side*frame["n"][i] for i in range(3)]


def _projection(f, obj):
    frame = f["frame"]
    corners = itertools.product(*zip(obj["min"], obj["max"]))
    axes = [frame["u"], frame["v"], [f["side"]*x for x in frame["n"]]]
    points = [[sum((point[k]-frame["origin"][k])*axis[k] for k in range(3)) for axis in axes] for point in corners]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    for value in lo+hi:
        _integer(value, "selected obstacle local projection")
    return [lo[0], lo[1], hi[0], hi[1]], [lo[2], hi[2]]


def _depth_hit(interval, layer):
    return max(interval[0], layer[0]) < min(interval[1], layer[1])


def _layer_relation(footprint, interval, layer):
    if footprint == "overlap" and _depth_hit(interval, layer):
        return "cut"
    if footprint != "separate" and max(interval[0], layer[0]) <= min(interval[1], layer[1]):
        return "touch"
    return "clear"


def _finish(f, objects):
    base = _slabs(f["region"])
    t, h = f["thickness"], f["section"][1]
    intervals = {"panel": (0, t), "timber": (t, t+h)}
    layers = {name: list(base) for name in intervals}
    diagnostics = []
    selected = f["obstacles"]
    for ref in selected:
        rectangle, depth = _projection(f, objects[ref])
        footprint = "overlap" if any(_positive_overlap(r, rectangle) for r in base) else "touch" if any(_touch(r, rectangle) for r in base) else "separate"
        diagnostic = {"ref": ref, "projectedRect": rectangle, "normalInterval": depth, "footprintRelation": footprint}
        for name, interval in intervals.items():
            diagnostic[name] = _layer_relation(footprint, depth, interval)
            if diagnostic[name] == "cut":
                layers[name] = [piece for r in layers[name] for piece in _subtract(r, rectangle)]
        diagnostics.append(diagnostic)
    frame, side = f["frame"], f["side"]
    host_frame = {"origin": _world(f, 0, 0, t), "u": list(frame["u"]),
                  "v": [side*x for x in frame["v"]], "n": [side*x for x in frame["n"]]}
    host_rectangles = [(r[0], min(side*r[1], side*r[3]), r[2], max(side*r[1], side*r[3])) for r in layers["timber"]]
    return {"id": f["id"], "label": f["label"], "frame": copy.deepcopy(frame), "side": side,
            "thickness": t, "section": list(f["section"]), "obstacles": diagnostics,
            "panel": _region(layers["panel"]), "timber": _region(layers["timber"]),
            "host": {"frame": host_frame, "h": h, "region": _region(host_rectangles)}}


def _rectangles(region):
    return [r for component in region["components"] for r in component["rectangles"]]


def _boxes(f, region, interval):
    result = []
    for rect in _rectangles(region):
        points = [_world(f, u, v, q) for u, v, q in itertools.product((rect[0], rect[2]), (rect[1], rect[3]), interval)]
        result.append(([min(p[k] for p in points) for k in range(3)], [max(p[k] for p in points) for k in range(3)]))
    return result


def _intersections(first, second):
    dimension, volume = -1, 0
    for a, b in first:
        for c, d in second:
            extents = [min(b[k], d[k])-max(a[k], c[k]) for k in range(3)]
            if min(extents) >= 0:
                dimension = max(dimension, sum(x > 0 for x in extents))
                volume += extents[0]*extents[1]*extents[2]
    return dimension, volume


def _world_edges(f, region):
    return [(tuple(_world(f, a[0], a[1], 0)), tuple(_world(f, b[0], b[1], 0)))
            for component in region["components"] for ring in [component["outer"]]+component["holes"]
            for a, b in _segments(ring)]


def _shared_edges(f, a, g, b):
    lines = {}
    for start, end in _world_edges(f, a):
        axis = next(i for i in range(3) if start[i] != end[i])
        for other_start, other_end in _world_edges(g, b):
            if not all(start[k] == end[k] == other_start[k] == other_end[k] for k in range(3) if k != axis):
                continue
            low = max(min(start[axis], end[axis]), min(other_start[axis], other_end[axis]))
            high = min(max(start[axis], end[axis]), max(other_start[axis], other_end[axis]))
            if low < high:
                key = (axis, tuple(start[k] if k != axis else 0 for k in range(3)))
                lines.setdefault(key, []).append((low, high))
    result = []
    for (axis, fixed), intervals in sorted(lines.items()):
        merged = []
        for low, high in sorted(intervals):
            if merged and low <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], high)
            else:
                merged.append([low, high])
        for low, high in merged:
            start, end = list(fixed), list(fixed)
            start[axis], end[axis] = low, high
            result.append({"start": start, "end": end, "length": high-low})
    return result


def _junction(f, a, g, b):
    visible_a, visible_b = _boxes(f, a["panel"], (0, 0)), _boxes(g, b["panel"], (0, 0))
    dimension, _ = _intersections(visible_a, visible_b)
    gap = min((sum(max(0, c[k]-z[k], x[k]-d[k]) for k in range(3))
               for x, z in visible_a for c, d in visible_b), default=None)
    layers = {}
    for left, right in itertools.product(("panel", "timber"), repeat=2):
        lt, rt = f["thickness"], g["thickness"]
        first = _boxes(f, a[left], (0, lt) if left == "panel" else (lt, lt+f["section"][1]))
        second = _boxes(g, b[right], (0, rt) if right == "panel" else (rt, rt+g["section"][1]))
        contact_dimension, volume = _intersections(first, second)
        layers[left+"-"+right] = {"volume": volume, "contactDimension": contact_dimension,
                                 "relation": "overlap" if volume else "touch" if contact_dimension >= 0 else "separate"}
    return {"finishes": [f["id"], g["id"]], "sharedEdges": _shared_edges(f, a["panel"], g, b["panel"]),
            "visibleContactDimension": dimension, "minimumL1Gap": gap, "layers": layers, "joinPolicy": "unselected"}


def solve(data):
    """Return geometry diagnostics or reject invalid/unrepresentable input whole."""
    try:
        objects = _validate(data)
        inputs = sorted(data["finishes"], key=lambda f: f["id"])
        outputs = [_finish(f, objects) for f in inputs]
        junctions = [_junction(inputs[i], outputs[i], inputs[j], outputs[j])
                     for i in range(len(inputs)) for j in range(i+1, len(inputs))]
        return {"schema": "pf5-geometry-output/1", "scope": "diagnostic-envelope-only",
                "edgeIdentity": "not-modeled", "room": copy.deepcopy(data["room"]), "finishes": outputs, "junctions": junctions}
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("PF5_EXPLICIT_INPUT_REQUIRED: " + str(error)) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="explicit pf5-geometry-input/1 JSON file, or - for stdin")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") if args.input != "-" else sys.stdin as stream:
            result = solve(json.load(stream))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
