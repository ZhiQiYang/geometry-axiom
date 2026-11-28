"""Independent PF-5 diagnostic checker: no imports from the constructor/runtime.

Coverage is checked by raw world-space cuboid membership at exact critical-cell
midpoints, not the constructor's planar slab/subtraction algorithm. Components
are independently flood-filled. Junction volume uses a 3-D cell integral, not
the constructor's sum of pairwise box-intersection volumes. Only Python's
standard library is shared; there is no shared geometry or parsing helper.
"""
import argparse
import itertools
import json
import sys


def _integer(value):
    return type(value) is int and abs(value) <= 100_000_000


def _same(first, second):
    # bool/float must not compare equal to an integer geometry value.
    return json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected.split()):
        raise ValueError("closed schema fields: " + expected)


def _winding(loop, x2, y2):
    winding = 0
    for i, a in enumerate(loop):
        b = loop[(i+1) % len(loop)]
        cross = (b[0]-a[0])*(y2-2*a[1]) - (b[1]-a[1])*(x2-2*a[0])
        if 2*a[1] <= y2 < 2*b[1] and cross > 0:
            winding += 1
        elif 2*b[1] <= y2 < 2*a[1] and cross < 0:
            winding -= 1
    return winding != 0


def _boundary(loop, x2, y2):
    for i, a in enumerate(loop):
        b = loop[(i+1) % len(loop)]
        if min(a[0], b[0])*2 <= x2 <= max(a[0], b[0])*2 and min(a[1], b[1])*2 <= y2 <= max(a[1], b[1])*2:
            return True
    return False


def _in_face(f, u2, v2):
    region = f["region"]
    return _winding(region["outer"], u2, v2) and not any(_winding(h, u2, v2) for h in region["holes"])


def _local_limits(f, obj, axis, sign=1):
    vector = f["frame"][axis]
    k = next(i for i in range(3) if vector[i])
    values = [(value-f["frame"]["origin"][k])*vector[k]*sign for value in (obj["min"][k], obj["max"][k])]
    return min(values), max(values)


def _alive(f, u2, v2, a, b, selected):
    if not _in_face(f, u2, v2):
        return False
    # Split only the physical normal dimension. Every open interval has a
    # constant cuboid-membership predicate; face/edge/point contact has no cell.
    cuts = {a, b}
    for obj in selected:
        cuts.update(q for q in _local_limits(f, obj, "n", f["side"]) if a < q < b)
    cuts = sorted(cuts)
    frame = f["frame"]
    for q0, q1 in zip(cuts, cuts[1:]):
        q2 = q0+q1
        world2 = [2*frame["origin"][k] + u2*frame["u"][k] + v2*frame["v"][k]
                  + q2*f["side"]*frame["n"][k] for k in range(3)]
        if any(all(2*obj["min"][k] < world2[k] < 2*obj["max"][k] for k in range(3)) for obj in selected):
            return False
    return True


def _loops_ok(outer, holes, errors, label, oriented=False):
    if type(outer) is not list or type(holes) is not list:
        raise ValueError("explicit ring/holes lists")
    loops = [outer]+holes
    for index, loop in enumerate(loops):
        if type(loop) is not list or len(loop) < 4 or any(type(p) is not list or len(p) != 2 or not all(_integer(v) for v in p) for p in loop):
            errors.append(label+": invalid ring vertices")
            return
        edges = [(a, loop[(i+1) % len(loop)]) for i, a in enumerate(loop)]
        if any((a[0] == b[0]) == (a[1] == b[1]) for a, b in edges):
            errors.append(label+": invalid orthogonal edge")
            return
        for i, (a, b) in enumerate(edges):
            for j, (c, d) in enumerate(edges[i+1:], i+1):
                x0, x1 = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
                y0, y1 = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
                if x0 <= x1 and y0 <= y1:
                    adjacent = j == i+1 or (i == 0 and j == len(edges)-1)
                    if not adjacent or x0 != x1 or y0 != y1:
                        errors.append(label+": self-touching ring")
        signed_area2 = sum(a[0]*b[1]-b[0]*a[1] for a, b in edges)
        if signed_area2 == 0:
            errors.append(label+": zero ring area")
        if oriented and (signed_area2 <= 0 if index == 0 else signed_area2 >= 0):
            errors.append(label+": outer/hole winding orientation")
    for i, first in enumerate(loops):
        for second in loops[i+1:]:
            for index, a in enumerate(first):
                b = first[(index+1) % len(first)]
                for j, c in enumerate(second):
                    d = second[(j+1) % len(second)]
                    if all(max(min(a[k], b[k]), min(c[k], d[k])) <= min(max(a[k], b[k]), max(c[k], d[k])) for k in range(2)):
                        errors.append(label+": rings touch/intersect")
                        return
    for i, hole in enumerate(holes):
        if not _winding(outer, 2*hole[0][0], 2*hole[0][1]):
            errors.append(label+": hole outside outer")
        if any(_winding(other, 2*hole[0][0], 2*hole[0][1]) for j, other in enumerate(holes) if j != i):
            errors.append(label+": nested holes")


def _source(data):
    """Validate the raw diagnostic input independently; no constructor calls."""
    _keys(data, "schema room obstacles finishes")
    if data["schema"] != "pf5-geometry-input/1":
        raise ValueError("input schema")
    _keys(data["room"], "min max")
    if type(data["obstacles"]) is not list or type(data["finishes"]) is not list:
        raise ValueError("explicit collections")
    objects = {}
    for obj in data["obstacles"]:
        _keys(obj, "ref min max")
        ref = obj["ref"]
        if type(ref) is not str or len(ref) < 2 or ref[0] not in "bc" or not ref[1:].isdigit():
            raise ValueError("typed obstacle reference")
        identity = int(ref[1:])
        if str(identity) != ref[1:] or not 0 <= identity <= 4_294_967_295 or ref in objects:
            raise ValueError("typed uint32 obstacle identity")
        objects[ref] = obj
    for box in [data["room"]] + list(objects.values()):
        if any(type(box[key]) is not list or len(box[key]) != 3 or not all(_integer(x) for x in box[key]) for key in ("min", "max")):
            raise ValueError("integer-mm AABB")
        if any(not 0 < box["max"][k]-box["min"][k] <= 100_000_000 for k in range(3)):
            raise ValueError("positive bounded AABB extent")
    identities = set()
    for f in data["finishes"]:
        _keys(f, "id label frame side region obstacles thickness section")
        if type(f["id"]) is not int or not 1 <= f["id"] <= 4_294_967_295 or f["id"] in identities or type(f["label"]) is not str:
            raise ValueError("positive uint32 finish identity/label")
        identities.add(f["id"])
        frame = f["frame"]
        _keys(frame, "origin u v n")
        if type(frame["origin"]) is not list or len(frame["origin"]) != 3 or not all(_integer(x) for x in frame["origin"]):
            raise ValueError("D1 origin")
        axes = [frame[key] for key in ("u", "v", "n")]
        if any(type(axis) is not list or len(axis) != 3 or not all(type(x) is int and x in (-1, 0, 1) for x in axis) or sum(abs(x) for x in axis) != 1 for axis in axes):
            raise ValueError("signed unit axes")
        u, v, n = axes
        if u[0]*(v[1]*n[2]-v[2]*n[1])-u[1]*(v[0]*n[2]-v[2]*n[0])+u[2]*(v[0]*n[1]-v[1]*n[0]) != 1:
            raise ValueError("D2 right-handed frame")
        if type(f["side"]) is not int or f["side"] not in (-1, 1) or not _integer(f["thickness"]) or f["thickness"] <= 0:
            raise ValueError("explicit structural side/thickness")
        if type(f["section"]) is not list or len(f["section"]) != 2 or not all(_integer(x) and x > 0 for x in f["section"]):
            raise ValueError("explicit positive A/B section")
        _keys(f["region"], "outer holes")
        if type(f["region"]["outer"]) is not list or type(f["region"]["holes"]) is not list:
            raise ValueError("explicit polygon/holes")
        errors = []
        _loops_ok(f["region"]["outer"], f["region"]["holes"], errors, "source")
        if errors:
            raise ValueError("; ".join(errors))
        if type(f["obstacles"]) is not list or any(type(ref) is not str or ref not in objects for ref in f["obstacles"]) or len(set(f["obstacles"])) != len(f["obstacles"]):
            raise ValueError("explicit unique selected obstacle references")
        for ref in f["obstacles"]:
            for key, sign in (("u", 1), ("v", 1), ("n", f["side"])):
                if not all(_integer(x) for x in _local_limits(f, objects[ref], key, sign)):
                    raise ValueError("D1 selected obstacle local projection")
        for ring in [f["region"]["outer"]]+f["region"]["holes"]:
            for p in ring:
                for q in (0, f["thickness"], f["thickness"]+f["section"][1]):
                    if not all(_integer(frame["origin"][k]+p[0]*u[k]+p[1]*v[k]+q*f["side"]*n[k]) for k in range(3)):
                        raise ValueError("D1 derived world coordinate")


def _check_region(f, region, interval, selected, errors, label, host=False):
    _keys(region, "area components")
    components = region["components"]
    if type(components) is not list:
        raise ValueError("explicit component list")
    rectangles = []
    for index, component in enumerate(components):
        _keys(component, "rectangles outer holes")
        _loops_ok(component["outer"], component["holes"], errors, label, oriented=True)
        if type(component["rectangles"]) is not list or not component["rectangles"]:
            errors.append(label+": empty component")
        for rect in component["rectangles"]:
            if type(rect) is not list or len(rect) != 4 or not all(_integer(x) for x in rect) or rect[0] >= rect[2] or rect[1] >= rect[3]:
                errors.append(label+": invalid cell rectangle")
                return
            rectangles.append((index, rect))
    sign = f["side"] if host else 1
    xs = {p[0] for ring in [f["region"]["outer"]]+f["region"]["holes"] for p in ring}
    ys = {sign*p[1] for ring in [f["region"]["outer"]]+f["region"]["holes"] for p in ring}
    for obj in selected:
        xs.update(_local_limits(f, obj, "u"))
        ys.update(sign*v for v in _local_limits(f, obj, "v"))
    for _, rect in rectangles:
        xs.update((rect[0], rect[2]))
        ys.update((rect[1], rect[3]))
    for component in components:
        for ring in [component["outer"]]+component["holes"]:
            xs.update(p[0] for p in ring)
            ys.update(p[1] for p in ring)
    xs, ys = sorted(xs), sorted(ys)
    occupied, expected_area = {}, 0
    for i, (x0, x1) in enumerate(zip(xs, xs[1:])):
        for j, (y0, y1) in enumerate(zip(ys, ys[1:])):
            u2, v2 = x0+x1, y0+y1
            expected = _alive(f, u2, sign*v2, interval[0], interval[1], selected)
            owners = [index for index, r in rectangles if 2*r[0] < u2 < 2*r[2] and 2*r[1] < v2 < 2*r[3]]
            if len(owners) != int(expected):
                errors.append(label+": world-volume coverage mismatch at " + str((u2, v2)))
            for index, component in enumerate(components):
                polygon = _winding(component["outer"], u2, v2) and not any(_winding(h, u2, v2) for h in component["holes"])
                if polygon != (index in owners):
                    errors.append(label+": ring/cell coverage mismatch")
            if expected:
                expected_area += (x1-x0)*(y1-y0)
                occupied[i, j] = owners[0] if len(owners) == 1 else -1
    if type(region["area"]) is not int or region["area"] != expected_area:
        errors.append(label+": area mismatch")
    # Flood the expected world predicate, not the submitted rectangles. One
    # component may touch another at a point; only edge neighbours connect.
    visited, used_owners = set(), set()
    for seed in occupied:
        if seed in visited:
            continue
        pending, owners = [seed], set()
        visited.add(seed)
        while pending:
            cell = pending.pop()
            owners.add(occupied[cell])
            for neighbour in ((cell[0]-1, cell[1]), (cell[0]+1, cell[1]), (cell[0], cell[1]-1), (cell[0], cell[1]+1)):
                if neighbour in occupied and neighbour not in visited:
                    visited.add(neighbour)
                    pending.append(neighbour)
        if len(owners) != 1 or -1 in owners or owners & used_owners:
            errors.append(label+": interior component partition mismatch")
        used_owners.update(owners)
    if used_owners != set(range(len(components))):
        errors.append(label+": component inventory mismatch")


def _footprint_relation(f, rectangle):
    rings = [f["region"]["outer"]]+f["region"]["holes"]
    xs = sorted({p[0] for r in rings for p in r} | {rectangle[0], rectangle[2]})
    ys = sorted({p[1] for r in rings for p in r} | {rectangle[1], rectangle[3]})
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            if 2*rectangle[0] < x0+x1 < 2*rectangle[2] and 2*rectangle[1] < y0+y1 < 2*rectangle[3] and _in_face(f, x0+x1, y0+y1):
                return "overlap"
    # For zero-area contacts, use endpoints and split-edge midpoints. The
    # critical-grid strata include corners and all boundary intersections.
    xpoints = [2*x for x in xs] + [a+b for a, b in zip(xs, xs[1:])]
    ypoints = [2*y for y in ys] + [a+b for a, b in zip(ys, ys[1:])]
    for x2, y2 in itertools.product(xpoints, ypoints):
        if 2*rectangle[0] <= x2 <= 2*rectangle[2] and 2*rectangle[1] <= y2 <= 2*rectangle[3]:
            if any(_boundary(r, x2, y2) for r in rings):
                return "touch"
    return "separate"


def _diagnostics(f, selected):
    result = []
    for obj in selected:
        u, v, q = _local_limits(f, obj, "u"), _local_limits(f, obj, "v"), _local_limits(f, obj, "n", f["side"])
        rect = [u[0], v[0], u[1], v[1]]
        relation = _footprint_relation(f, rect)
        record = {"ref": obj["ref"], "projectedRect": rect, "normalInterval": list(q), "footprintRelation": relation}
        t, h = f["thickness"], f["section"][1]
        for name, low, high in (("panel", 0, t), ("timber", t, t+h)):
            positive = max(low, q[0]) < min(high, q[1])
            closed = max(low, q[0]) <= min(high, q[1])
            record[name] = "cut" if relation == "overlap" and positive else "touch" if relation != "separate" and closed else "clear"
        result.append(record)
    return result


def _boxes(f, region, a, b):
    frame = f["frame"]
    result = []
    for component in region["components"]:
        for x0, y0, x1, y1 in component["rectangles"]:
            low, high = [], []
            for k in range(3):
                if frame["u"][k]:
                    values = [frame["origin"][k]+frame["u"][k]*x for x in (x0, x1)]
                elif frame["v"][k]:
                    values = [frame["origin"][k]+frame["v"][k]*y for y in (y0, y1)]
                else:
                    values = [frame["origin"][k]+f["side"]*frame["n"][k]*q for q in (a, b)]
                low.append(min(values))
                high.append(max(values))
            result.append((low, high))
    return result


def _covered(point2, boxes):
    return any(all(2*lo[k] <= point2[k] <= 2*hi[k] for k in range(3)) for lo, hi in boxes)


def _voxel_intersection(first, second):
    if not first or not second:
        return -1, 0
    cuts = [sorted({box[side][k] for box in first+second for side in (0, 1)}) for k in range(3)]
    volume = 0
    intervals = [[(a+b, b-a) for a, b in zip(axis, axis[1:])] for axis in cuts]
    for cell in itertools.product(*intervals):
        point2 = [c[0] for c in cell]
        if _covered(point2, first) and _covered(point2, second):
            volume += cell[0][1]*cell[1][1]*cell[2][1]
    if volume:
        return 3, volume
    # Lower-dimensional strata are checked separately so touching never
    # acquires a fictitious 1 mm thickness or a positive volume.
    for dimension in (2, 1, 0):
        for varying in itertools.combinations(range(3), dimension):
            strata = [intervals[k] if k in varying else [(2*p, 0) for p in cuts[k]] for k in range(3)]
            for cell in itertools.product(*strata):
                point2 = [c[0] for c in cell]
                if _covered(point2, first) and _covered(point2, second):
                    return dimension, 0
    return -1, 0


def _line_inventory(f, region):
    lines = {}
    frame = f["frame"]
    for component in region["components"]:
        for loop in [component["outer"]]+component["holes"]:
            for i, p in enumerate(loop):
                q = loop[(i+1) % len(loop)]
                a = [frame["origin"][k]+p[0]*frame["u"][k]+p[1]*frame["v"][k] for k in range(3)]
                b = [frame["origin"][k]+q[0]*frame["u"][k]+q[1]*frame["v"][k] for k in range(3)]
                axis = next(k for k in range(3) if a[k] != b[k])
                key = (axis, tuple(a[k] for k in range(3) if k != axis))
                lines.setdefault(key, []).append((min(a[axis], b[axis]), max(a[axis], b[axis])))
    return lines


def _check_shared_edges(f, a, g, b, shared, errors):
    if type(shared) is not list:
        raise ValueError("explicit shared-edge list")
    first, second = _line_inventory(f, a), _line_inventory(g, b)
    actual = {}
    for item in shared:
        _keys(item, "start end length")
        p, q = item["start"], item["end"]
        if type(p) is not list or type(q) is not list or len(p) != 3 or len(q) != 3 or not all(_integer(x) for x in p+q) or sum(p[k] != q[k] for k in range(3)) != 1:
            errors.append("junction: invalid shared edge")
            continue
        axis = next(k for k in range(3) if p[k] != q[k])
        if type(item["length"]) is not int or item["length"] != abs(p[axis]-q[axis]):
            errors.append("junction: shared edge length")
        key = (axis, tuple(p[k] for k in range(3) if k != axis))
        actual.setdefault(key, []).append((min(p[axis], q[axis]), max(p[axis], q[axis])))
    for key in first.keys() | second.keys() | actual.keys():
        a_ranges, b_ranges, found = first.get(key, []), second.get(key, []), actual.get(key, [])
        cuts = sorted({p for interval in a_ranges+b_ranges+found for p in interval})
        for low, high in zip(cuts, cuts[1:]):
            point2 = low+high
            expected = any(2*x < point2 < 2*y for x, y in a_ranges) and any(2*x < point2 < 2*y for x, y in b_ranges)
            count = sum(2*x < point2 < 2*y for x, y in found)
            if count != int(expected):
                errors.append("junction: shared edge coverage mismatch")


def _check_junctions(inputs, outputs, junctions, errors):
    if type(junctions) is not list:
        raise ValueError("explicit junction list")
    for item in junctions:
        _keys(item, "finishes sharedEdges visibleContactDimension minimumL1Gap layers joinPolicy")
        pair = item["finishes"]
        if type(pair) is not list or len(pair) != 2 or any(type(x) is not int or not 1 <= x <= 4_294_967_295 for x in pair):
            raise ValueError("two positive uint32 finish identities")
        if type(item["layers"]) is not dict:
            raise ValueError("explicit junction layer map")
    expected_pairs = {(a, b) for a in inputs for b in inputs if a < b}
    pairs = [tuple(j["finishes"]) for j in junctions]
    if set(pairs) != expected_pairs or len(pairs) != len(expected_pairs):
        errors.append("junction: pair inventory mismatch")
    for item in junctions:
        _keys(item, "finishes sharedEdges visibleContactDimension minimumL1Gap layers joinPolicy")
        aid, bid = item["finishes"]
        f, g, a, b = inputs[aid], inputs[bid], outputs[aid], outputs[bid]
        if item["joinPolicy"] != "unselected":
            errors.append("junction: invented trim/support policy")
        first, second = _boxes(f, a["panel"], 0, 0), _boxes(g, b["panel"], 0, 0)
        dimension, _ = _voxel_intersection(first, second)
        if type(item["visibleContactDimension"]) is not int or item["visibleContactDimension"] != dimension:
            errors.append("junction: visible contact dimension")
        distances = []
        for lo, hi in first:
            for other_lo, other_hi in second:
                distance = 0
                for k in range(3):
                    if hi[k] < other_lo[k]:
                        distance += other_lo[k]-hi[k]
                    elif other_hi[k] < lo[k]:
                        distance += lo[k]-other_hi[k]
                distances.append(distance)
        gap = min(distances) if distances else None
        if not _same(item["minimumL1Gap"], gap):
            errors.append("junction: minimum L1 gap")
        _check_shared_edges(f, a["panel"], g, b["panel"], item["sharedEdges"], errors)
        if set(item["layers"]) != {left+"-"+right for left, right in itertools.product(("panel", "timber"), repeat=2)}:
            errors.append("junction: layer pair inventory")
        for left, right in itertools.product(("panel", "timber"), repeat=2):
            ft, gt = f["thickness"], g["thickness"]
            first = _boxes(f, a[left], 0, ft) if left == "panel" else _boxes(f, a[left], ft, ft+f["section"][1])
            second = _boxes(g, b[right], 0, gt) if right == "panel" else _boxes(g, b[right], gt, gt+g["section"][1])
            dimension, volume = _voxel_intersection(first, second)
            expected = {"volume": volume, "contactDimension": dimension, "relation": "overlap" if volume else "touch" if dimension >= 0 else "separate"}
            if not _same(item["layers"][left+"-"+right], expected):
                errors.append("junction: world voxel intersection mismatch for "+left+"-"+right)


def check(data, result):
    """Return a list of contract violations. An empty list means this subset passes."""
    errors = []
    try:
        _source(data)
        _keys(result, "schema scope edgeIdentity room finishes junctions")
        if type(result["finishes"]) is not list or type(result["junctions"]) is not list:
            raise ValueError("explicit output finish/junction lists")
        if data["schema"] != "pf5-geometry-input/1" or result["schema"] != "pf5-geometry-output/1":
            errors.append("schema mismatch")
        if result["scope"] != "diagnostic-envelope-only" or result["edgeIdentity"] != "not-modeled":
            errors.append("unsupported completeness claim")
        if not _same(result["room"], data["room"]):
            errors.append("room context changed")
        objects = {o["ref"]: o for o in data["obstacles"]}
        inputs = {f["id"]: f for f in data["finishes"]}
        outputs = {f["id"]: f for f in result["finishes"]}
        if len(objects) != len(data["obstacles"]) or len(inputs) != len(data["finishes"]):
            errors.append("duplicate input identity")
        if set(inputs) != set(outputs) or len(outputs) != len(result["finishes"]):
            errors.append("selected finish inventory mismatch")
        for identity, f in inputs.items():
            r, frame = outputs[identity], f["frame"]
            _keys(r, "id label frame side thickness section obstacles panel timber host")
            _keys(r["host"], "frame h region")
            t, h, side = f["thickness"], f["section"][1], f["side"]
            selected = [objects[ref] for ref in f["obstacles"]]
            for key in ("id", "label", "frame", "side", "thickness", "section"):
                if not _same(r[key], f[key]):
                    errors.append("source metadata mismatch: "+key)
            if not _same(r["obstacles"], _diagnostics(f, selected)):
                errors.append("selected obstacle diagnostic mismatch")
            expected_frame = {"origin": [frame["origin"][k]+t*side*frame["n"][k] for k in range(3)],
                              "u": frame["u"], "v": [side*x for x in frame["v"]], "n": [side*x for x in frame["n"]]}
            if not _same(r["host"]["frame"], expected_frame) or not _same(r["host"]["h"], h):
                errors.append("board-back frame/height mismatch")
            _check_region(f, r["panel"], (0, t), selected, errors, "panel")
            _check_region(f, r["timber"], (t, t+h), selected, errors, "timber")
            _check_region(f, r["host"]["region"], (t, t+h), selected, errors, "host", host=True)
        _check_junctions(inputs, outputs, result["junctions"], errors)
    except (KeyError, TypeError, IndexError, ValueError, StopIteration) as error:
        errors.append("malformed input/output: "+str(error))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("candidate")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as stream:
            source = json.load(stream)
        with open(args.candidate, encoding="utf-8") as stream:
            candidate = json.load(stream)
        errors = check(source, candidate)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return int(bool(errors))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
