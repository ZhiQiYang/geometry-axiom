#!/usr/bin/env python3
"""R03 R: bounded rectangular FT02 / R-butt reference, not product code.

Input is the resolved second-slice ``bounds / parameters / layout`` plus the
explicit ``seam_retreat`` policy, ``r_butt`` switch and exact rational threshold.
There is no arbitrary wall gap or end-joint interpretation of these policies.

``build`` constructs one candidate. ``check`` independently evaluates its actual
seams, stable D43 panel identities, member geometry, fixed jig, collisions,
end stops and exact R43 coverage. A candidate is not an approval: check may
report physical failures (and native World validation remains authoritative).
The checker does not call build, its construction helpers, or the old oracle.
Only scalar input validation and finite limits are shared.

The command line writes JSON: --scan is a finite 1 mm sweep; --mutations runs
named wrong-output children with a timeout and checks their exact failure
marker. --legacy compares a small declared domain with PR #307/#327's oracle.
No native build, fixture update, network request, or product state is performed.
"""

from __future__ import annotations

import argparse
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


D1 = 100_000_000
MAX_LINES = 64
MAX_MEMBERS = 512
MAX_PANELS = (MAX_LINES + 1) ** 2
KINDS = ("boundary", "main", "rc_parallel", "secondary:mark", "secondary:seam")
PARAMETERS = ("panelWidth", "panelLength", "gap", "timberWidth", "timberDepth", "maxSecondarySpacing")


def _facts(case):
    """Schema/scalar checks only; deliberately contains no layout construction."""
    if not isinstance(case, dict) or set(case) - {"bounds", "parameters", "layout", "seam_retreat", "r_butt", "threshold", "name"}:
        raise ValueError("SCHEMA: expected a resolved R03 rectangular case")
    if not {"bounds", "parameters", "layout", "seam_retreat", "r_butt", "threshold"} <= set(case):
        raise ValueError("SCHEMA: all physical inputs and policy choices must be explicit")
    bounds, p, layout, x = case["bounds"], case["parameters"], case["layout"], case["threshold"]
    integer = lambda value: type(value) is int
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 4 or not all(integer(v) for v in bounds):
        raise ValueError("SCHEMA: bounds must contain four integer millimetre coordinates")
    if not isinstance(p, dict) or set(p) != set(PARAMETERS) or not all(integer(v) for v in p.values()):
        raise ValueError("SCHEMA: parameters must use the six second-slice integer fields")
    if any(p[k] <= 0 for k in PARAMETERS if k != "gap") or p["gap"] < 0:
        raise ValueError("SCHEMA: dimensions must be positive; gap may be zero")
    if any(abs(v) > D1 for v in bounds) or any(v > D1 for v in p.values()):
        raise ValueError("UNSUPPORTED_SCOPE: outside D1")
    if not isinstance(layout, dict) or set(layout) != {"corner", "lengthAlong"} or layout["corner"] not in ("min-min", "max-min", "min-max", "max-max") or layout["lengthAlong"] not in ("u", "v"):
        raise ValueError("SCHEMA: explicit second-slice corner and lengthAlong required")
    if case["seam_retreat"] not in ("none", "ft02") or type(case["r_butt"]) is not bool:
        raise ValueError("SCHEMA: seam_retreat must be none/ft02; r_butt must be boolean")
    if not isinstance(x, dict) or set(x) != {"num", "den"} or not all(integer(v) and v > 0 for v in x.values()):
        raise ValueError("SCHEMA: threshold is an explicit positive rational, never rounded")
    if max(x.values()) > 2 ** 63 - 1:
        raise ValueError("UNSUPPORTED_SCOPE: threshold exceeds the native rational scalar domain")
    w = p["timberWidth"]
    if bounds[2] - bounds[0] <= 2 * w or bounds[3] - bounds[1] <= 2 * w:
        raise ValueError("UNSUPPORTED_SCOPE: rectangle has no four-wall-member interior")
    return bounds, p, layout, x


def case_from_stage2(request, bounds, threshold, *, seam_retreat, r_butt):
    """Resolve no references/defaults: callers supply the already-read X value."""
    case = {"bounds": list(bounds), "parameters": copy.deepcopy(request["parameters"]),
            "layout": copy.deepcopy(request["layout"]), "threshold": dict(threshold),
            "seam_retreat": seam_retreat, "r_butt": r_butt}
    _facts(case)
    return case


def build(case):
    """Construct all members and every clipped D43 panel; do not self-approve."""
    bounds, p, layout, threshold = _facts(case)
    b = 0 if layout["lengthAlong"] == "u" else 1
    a = 1 - b
    sizes = [p["panelWidth"], p["panelWidth"]]
    sizes[b] = p["panelLength"]
    start = layout["corner"].split("-")
    g, w, M = p["gap"], p["timberWidth"], p["maxSecondarySpacing"]
    gl, gu, lh, hh = g // 2, g - g // 2, w // 2, w - w // 2
    origins, seam_rows, seams, by_key = [], [], {}, [{}, {}]
    for axis in (0, 1):
        lo, hi, size = bounds[axis], bounds[axis + 2], sizes[axis]
        origin = hi - size if start[axis] == "max" else lo
        origins.append(origin)
        distances = []
        n = 1
        while n * (size + g) < hi - lo:
            if len(distances) == MAX_LINES:
                raise ValueError("CAPACITY: more than 64 effective seams on one axis")
            distances.append((n - 1) * (size + g) + size + (gu if start[axis] == "max" else gl))
            n += 1
        adjusted = list(distances)
        if distances and 2 * distances[-1] > 2 * (hi - lo) - 3 * w:
            if case["seam_retreat"] == "none":
                raise ValueError("POLICY_RULE_CONFLICT: this case needs FT02; stage two refuses it")
            adjusted[-1] = (2 * (hi - lo) - 3 * w) // 2
            if adjusted[-1] <= (adjusted[-2] if len(adjusted) > 1 else 0):
                raise ValueError("POLICY_RULE_CONFLICT: FT02 would cross the preceding seam or starting wall")
        rows = []
        for index, (raw, distance) in enumerate(zip(distances, adjusted)):
            k = -index - 1 if start[axis] == "max" else index
            center = hi - distance if start[axis] == "max" else lo + distance
            baseline = origin + k * (size + g) + size + gl
            row = {"axis": "uv"[axis], "k": k, "baseline": baseline,
                   "center": center, "retreat": raw - distance}
            rows.append(row)
            by_key[axis][k] = center
        rows.sort(key=lambda row: row["center"])
        seam_rows.extend(rows)
        seams["uv"[axis]] = [row["center"] for row in rows]

    def body(axis, key):
        size, origin = sizes[axis], origins[axis]
        left = by_key[axis].get(key - 1, origin + (key - 1) * (size + g) + size + gl) + gu
        right = by_key[axis].get(key, origin + key * (size + g) + size + gl) - gl
        return max(bounds[axis], left), min(bounds[axis + 2], right)

    body_axes = []
    for axis in (0, 1):
        keys = list(by_key[axis])
        low, high = (min(keys), 0) if start[axis] == "max" and keys else (0, max(keys) + 1 if keys else 0)
        body_axes.append([(k, body(axis, k)) for k in range(low, high + 1)])
    panels = []
    for i, (u0, u1) in body_axes[0]:
        for j, (v0, v1) in body_axes[1]:
            if u0 < u1 and v0 < v1:
                panels.append({"i": i, "j": j, "rect": [u0, v0, u1, v1]})
    if len(panels) > MAX_PANELS:
        raise ValueError("CAPACITY: complete panel set exceeds the declared finite domain")

    mark_rows = []
    ends = [bounds[b], *seams["uv"[b]], bounds[b + 2]]
    for i in range(len(ends) - 1):
        lo, hi = ends[i:i + 2]
        left_seam, right_seam = i > 0, i + 1 < len(ends) - 1
        forward = start[b] == "min" if left_seam == right_seam else left_seam
        anchor, end, sign = (lo, hi, 1) if forward else (hi, lo, -1)
        L = hi - lo
        n = max(1, (L + M - 1) // M)
        if n > MAX_LINES + 1:
            raise ValueError("CAPACITY: a jig span exceeds 64 marks")
        for index in range(1, n):
            distance = index * M
            if index == n - 1:
                c = anchor + sign * distance
                end_seam = right_seam if forward else left_seam
                low, high = (end - lh, end + hh) if end_seam else ((end - w, end) if forward else (end, end + w))
                if c + hh > low and c - lh < high:
                    distance = (n - 2) * M + (M + L - M * (n - 1) + 1) // 2
            c = anchor + sign * distance
            mark_rows.append({"center": c, "anchor": anchor, "delta": c - anchor})
    mark_rows.sort(key=lambda row: row["center"])
    if len(mark_rows) > MAX_LINES:
        raise ValueError("CAPACITY: complete jig exceeds 64 marks")

    members = []

    def put(kind, length_axis, A0, B0, A1, B1, center, key=None, shift=0):
        rect = [A0, B0, A1, B1] if a == 0 else [B0, A0, B1, A1]
        members.append({"kind": kind, "axis": "uv"[length_axis], "center": center,
                        "rect": rect, "length": rect[length_axis + 2] - rect[length_axis],
                        "seam_key": key, "shift": shift})
        if len(members) > MAX_MEMBERS:
            raise ValueError("CAPACITY: complete member set exceeds 512; no truncation")

    A0, A1, B0, B1 = bounds[a], bounds[a + 2], bounds[b], bounds[b + 2]
    put("boundary", a, A0, B0, A1, B0 + w, B0)
    put("boundary", a, A0, B1 - w, A1, B1, B1)
    rails = [(A0, A0 + w)]
    for row in (row for row in seam_rows if row["axis"] == "uv"[a]):
        c = row["center"]
        shift = 0
        left_gap, right_gap = c - lh - (A0 + w), A1 - w - (c + hh)
        # No collision rescue/columns/holes in this rectangle subset. A possible
        # wall overlap is still emitted and independently rejected by check.
        if case["r_butt"] and min(left_gap, right_gap) >= 0 and left_gap != 0 and right_gap != 0:
            choices = []
            if left_gap > 0 and (hh - gu - left_gap) * threshold["den"] >= threshold["num"]:
                choices.append((left_gap, -1))
            if right_gap > 0 and (lh - gl - right_gap) * threshold["den"] >= threshold["num"]:
                choices.append((right_gap, 1))
            if choices:
                distance, direction = min(choices)
                shift = distance * direction
        low, high = c + shift - lh, c + shift + hh
        put("main", b, low, B0 + w, high, B1 - w, c + shift, row["k"], shift)
        rails.append((low, high))
    put("rc_parallel", b, A0, B0 + w, A0 + w, B1 - w, A0)
    put("rc_parallel", b, A1 - w, B0 + w, A1, B1 - w, A1)
    rails.append((A1 - w, A1))
    for first, second in zip(rails, rails[1:]):
        left, right = first[1], second[0]
        if right - left < w:
            continue
        for row in mark_rows:
            c = row["center"]
            put("secondary:mark", a, left, c - lh, right, c + hh, c)
        for row in (row for row in seam_rows if row["axis"] == "uv"[b]):
            c = row["center"]
            put("secondary:seam", a, left, c - lh, right, c + hh, c, row["k"])
    members.sort(key=lambda row: (KINDS.index(row["kind"]), row["rect"]))
    return {"schema": "r03-retreat-oracle/1", "origin": origins, "seams": seams,
            "seam_rows": seam_rows, "marks": [row["center"] for row in mark_rows],
            "mark_rows": mark_rows, "members": members, "panels": panels}


def check(case, result):
    """Independent predicates; no builder, builder helpers, or historical oracle.

    Closed-form signed lattice keys are derived directly from D43. Member
    obligations are checked against actual rows and geometric spans; R43 uses
    unions of actual timber sections, never construction status or cached flags.
    """
    bounds, p, layout, x = _facts(case)
    errors = []

    def fail(code, detail):
        message = code + ": " + detail
        if message not in errors:
            errors.append(message)

    if not isinstance(result, dict) or result.get("schema") != "r03-retreat-oracle/1":
        return ["OUTPUT_SCHEMA: expected complete r03-retreat-oracle/1 output"]
    required = ("origin", "seams", "seam_rows", "marks", "mark_rows", "members", "panels")
    if any(key not in result for key in required):
        return ["OUTPUT_SCHEMA: missing complete output collection"]
    if any(not isinstance(result[key], list) for key in ("origin", "seam_rows", "marks", "mark_rows", "members", "panels")) or not isinstance(result["seams"], dict):
        return ["OUTPUT_SCHEMA: collections have incorrect types"]
    if (len(result["origin"]) != 2 or any(type(value) is not int for value in result["origin"])
            or set(result["seams"]) != {"u", "v"}
            or any(not isinstance(values, list) or len(values) > MAX_LINES or any(type(value) is not int for value in values) for values in result["seams"].values())
            or any(type(value) is not int for value in result["marks"])
            or any(not isinstance(row, dict) or set(row) != {"center", "anchor", "delta"} or any(type(value) is not int for value in row.values()) for row in result["mark_rows"])):
        return ["OUTPUT_SCHEMA: coordinates and source offsets require exact integers"]
    if len(result["members"]) > MAX_MEMBERS or len(result["panels"]) > MAX_PANELS or len(result["seam_rows"]) > 2 * MAX_LINES or len(result["marks"]) > MAX_LINES:
        return ["CAPACITY: complete result exceeds a declared finite limit"]
    B = "uv".index(layout["lengthAlong"])
    A = 1 - B
    W, G, step = p["timberWidth"], p["gap"], p["maxSecondarySpacing"]
    floor_gap, ceil_gap = G // 2, (G + 1) // 2
    lower, upper = W // 2, (W + 1) // 2
    dimensions = [p["panelWidth"] if axis != B else p["panelLength"] for axis in (0, 1)]
    reverse = [value == "max" for value in layout["corner"].split("-")]
    origin = [bounds[q + 2] - dimensions[q] if reverse[q] else bounds[q] for q in (0, 1)]
    if result["origin"] != origin:
        fail("ORIGIN", "second-slice full-panel origin changed")
    if any(abs(value) > D1 for value in origin):
        fail("D1_DERIVED", "formal panel origin exceeds the reloadable D1 domain")
    # Calculate finite signed keys analytically instead of the builder's inward
    # iterative walk. The last key is the only FT02 override on a rectangle.
    expected_centers, expected_rows, body_intervals = [{}, {}], [], []
    for q in (0, 1):
        size = dimensions[q]
        extent = bounds[q + 2] - bounds[q]
        count = (extent - 1) // (size + G)
        if count > MAX_LINES:
            fail("CAPACITY", "case requires too many seams")
            return errors
        keys = list(range(-count, 0)) if reverse[q] else list(range(count))
        far_key = -count if reverse[q] else count - 1
        for key in keys:
            baseline = origin[q] + key * (size + G) + size + floor_gap
            coordinate = baseline
            inward = bounds[q + 2] - baseline if reverse[q] else baseline - bounds[q]
            allowance = (2 * extent - 3 * W) // 2
            retreat = 0
            if key == far_key and inward > allowance:
                if case["seam_retreat"] == "none":
                    fail("FT02_REQUIRED", "stage-two domain excludes this narrow opposite-wall strip")
                else:
                    coordinate = bounds[q + 2] - allowance if reverse[q] else bounds[q] + allowance
                    retreat = inward - allowance
            expected_centers[q][key] = coordinate
            expected_rows.append({"axis": "uv"[q], "k": key, "baseline": baseline, "center": coordinate, "retreat": retreat})
        interval_rows = []
        panel_keys = range(-count, 1) if reverse[q] else range(count + 1)
        for key in panel_keys:
            c0 = expected_centers[q].get(key - 1, origin[q] + (key - 1) * (size + G) + size + floor_gap)
            c1 = expected_centers[q].get(key, origin[q] + key * (size + G) + size + floor_gap)
            if c1 - c0 <= G:
                fail("D43_ORDER", "effective centers leave no positive panel body")
            lo, hi = max(bounds[q], c0 + ceil_gap), min(bounds[q + 2], c1 - floor_gap)
            if lo < hi:
                interval_rows.append((key, lo, hi))
                if hi - lo > size:
                    fail("I52_PANEL_MAX", "clipped physical panel exceeds original board dimension")
        body_intervals.append(interval_rows)
    expected_rows.sort(key=lambda row: (row["axis"], row["center"]))
    got_seams = result["seam_rows"]
    if any(not isinstance(row, dict) or set(row) != {"axis", "k", "baseline", "center", "retreat"} or row.get("axis") not in ("u", "v") or any(type(row.get(k)) is not int for k in ("k", "baseline", "center", "retreat")) for row in got_seams):
        fail("SEAM_KEY", "malformed stable seam identity or coordinate")
    elif got_seams != expected_rows:
        fail("SEAM_KEY", "finite centers/identities/retreats differ from the direct D43/FT02 equations")
    wanted_seams = {"uv"[q]: sorted(expected_centers[q].values()) for q in (0, 1)}
    if result["seams"] != wanted_seams:
        fail("SEAM_LINES", "preview seam lines do not equal effective center rows")
    # Check actual panel identities and bodies without relying on output count
    # or bounding boxes alone. This catches a stale periodic fill after retreat.
    panels_by_key = {}
    for row in result["panels"]:
        if not isinstance(row, dict) or set(row) != {"i", "j", "rect"} or type(row.get("i")) is not int or type(row.get("j")) is not int or not isinstance(row.get("rect"), list) or len(row["rect"]) != 4 or any(type(n) is not int for n in row["rect"]):
            fail("PANEL_ID", "malformed panel row")
            continue
        key = (row["i"], row["j"])
        if key in panels_by_key:
            fail("PANEL_ID", "duplicate signed panel identity")
        panels_by_key[key] = row["rect"]
    expected_panel_keys = {(i, j) for i, _, _ in body_intervals[0] for j, _, _ in body_intervals[1]}
    if set(panels_by_key) != expected_panel_keys:
        fail("PANEL_SET", "missing, extra, or renumbered physical panel")
    for i, u0, u1 in body_intervals[0]:
        for j, v0, v1 in body_intervals[1]:
            if panels_by_key.get((i, j)) != [u0, v0, u1, v1]:
                fail("PANEL_RECT", "panel body does not follow its original signed center keys")

    # Independently calculate jig anchors by classifying the endpoint pair.
    # Only the terminal step may be merged/split, and its half rounds upwards.
    expected_marks = []
    cuts = [bounds[B]] + wanted_seams["uv"[B]] + [bounds[B + 2]]
    for left, right in zip(cuts, cuts[1:]):
        left_is_seam, right_is_seam = left != bounds[B], right != bounds[B + 2]
        from_left = (not reverse[B]) if left_is_seam == right_is_seam else left_is_seam
        anchor, target = (left, right) if from_left else (right, left)
        direction = 1 if from_left else -1
        span = right - left
        regular = (span - 1) // step
        if regular > MAX_LINES:
            fail("CAPACITY", "case requires too many jig marks")
            return errors
        for number in range(1, regular + 1):
            offset = number * step
            if number == regular:
                center = anchor + direction * offset
                target_is_seam = right_is_seam if from_left else left_is_seam
                stop = (target - lower, target + upper) if target_is_seam else ((target - W, target) if from_left else (target, target + W))
                overlap_length = min(center + upper, stop[1]) - max(center - lower, stop[0])
                if overlap_length > 0:
                    last_pair = span - (regular - 1) * step
                    offset = (regular - 1) * step + (last_pair + 1) // 2
            center = anchor + direction * offset
            expected_marks.append({"center": center, "anchor": anchor, "delta": direction * offset})
    expected_marks.sort(key=lambda row: row["center"])
    if result["mark_rows"] != expected_marks or result["marks"] != [row["center"] for row in expected_marks]:
        fail("JIG_MARKS", "fixed upper-modulus/terminal split or source anchor differs")

    # Validate every actual member first; later obligations use this checked
    # geometry, not the builder's rail list or assumed construction success.
    members = []
    signatures = set()
    for row in result["members"]:
        fields = {"kind", "axis", "center", "rect", "length", "seam_key", "shift"}
        if not isinstance(row, dict) or set(row) != fields or row.get("kind") not in KINDS or row.get("axis") not in ("u", "v") or not isinstance(row.get("rect"), list) or len(row["rect"]) != 4 or any(type(n) is not int for n in row["rect"]) or any(type(row.get(k)) is not int for k in ("center", "length", "shift")) or (row.get("seam_key") is not None and type(row["seam_key"]) is not int):
            fail("MEMBER_SCHEMA", "malformed material member")
            continue
        rect = row["rect"]
        axis = "uv".index(row["axis"])
        cross = 1 - axis
        signature = (row["kind"], tuple(rect))
        if signature in signatures:
            fail("MEMBER_DUPLICATE", "same material piece appears twice")
        signatures.add(signature)
        if any(rect[q] >= rect[q + 2] or rect[q] < bounds[q] or rect[q + 2] > bounds[q + 2] for q in (0, 1)):
            fail("MEMBER_BOUNDS", "nonpositive member or member outside the room")
        if rect[cross + 2] - rect[cross] != W or row["length"] != rect[axis + 2] - rect[axis]:
            fail("MEMBER_DIMENSION", "width/length does not describe the actual footprint")
        if row["length"] > D1:
            fail("D1_DERIVED", "automatic material length exceeds D1")
        if row["length"] < W:
            fail("SHORT_PIECE", "locked 27 mm-or-current-width minimum violated")
        if row["kind"] in ("main", "secondary:mark", "secondary:seam") and (rect[cross], rect[cross + 2]) != (row["center"] - lower, row["center"] + upper):
            fail("MEMBER_CENTER", "center does not define its asymmetric integer width")
        members.append(row)
    if members != sorted(members, key=lambda row: (KINDS.index(row["kind"]), row["rect"])):
        fail("MEMBER_ORDER", "member serialization differs from stage two")
    groups = {kind: [row for row in members if row["kind"] == kind] for kind in KINDS}

    def ab(rect):
        return (rect[A], rect[B], rect[A + 2], rect[B + 2])

    # Four RC members are material facts, not optional cached support labels.
    boundary_expected = {(bounds[A], bounds[B], bounds[A + 2], bounds[B] + W),
                         (bounds[A], bounds[B + 2] - W, bounds[A + 2], bounds[B + 2])}
    parallel_expected = {(bounds[A], bounds[B] + W, bounds[A] + W, bounds[B + 2] - W),
                         (bounds[A + 2] - W, bounds[B] + W, bounds[A + 2], bounds[B + 2] - W)}
    if {ab(row["rect"]) for row in groups["boundary"]} != boundary_expected or len(groups["boundary"]) != 2 or any(row["axis"] != "uv"[A] or row["center"] != (bounds[B] if row["rect"][B] == bounds[B] else bounds[B + 2]) or row["shift"] or row["seam_key"] is not None for row in groups["boundary"]):
        fail("RC_BOUNDARY", "complete along-wall boundary pair required")
    if {ab(row["rect"]) for row in groups["rc_parallel"]} != parallel_expected or len(groups["rc_parallel"]) != 2 or any(row["axis"] != "uv"[B] or row["center"] != (bounds[A] if row["rect"][A] == bounds[A] else bounds[A + 2]) or row["shift"] or row["seam_key"] is not None for row in groups["rc_parallel"]):
        fail("RC_PARALLEL", "complete parallel wall pair required")
    if len(groups["main"]) != len(expected_centers[A]) or {row["seam_key"] for row in groups["main"]} != set(expected_centers[A]):
        fail("MAIN_SET", "exactly one continuous main member per original seam key required")
    for row in groups["main"]:
        key = row["seam_key"]
        if key not in expected_centers[A]:
            continue
        seam = expected_centers[A][key]
        negative = seam - lower - bounds[A] - W
        positive = bounds[A + 2] - W - seam - upper
        choices = []
        # Independent target-center test: measure both board-side bearings at
        # each wall-touching center, rather than the builder's shift allowance.
        if case["r_butt"] and negative > 0 and positive > 0:
            for target, distance, sign in ((bounds[A] + W + lower, negative, -1), (bounds[A + 2] - W - upper, positive, 1)):
                left_bearing = seam - floor_gap - (target - lower)
                right_bearing = target + upper - seam - ceil_gap
                if min(left_bearing, right_bearing) * x["den"] >= x["num"]:
                    choices.append((distance, sign, target))
        target = min(choices)[2] if choices else seam
        if row["center"] != target or row["shift"] != target - seam:
            fail("BUTT_POLICY", "main failed nearest feasible wall touch / exact bearing / tie rule")
        if row["axis"] != "uv"[B] or ab(row["rect"])[1::2] != (bounds[B] + W, bounds[B + 2] - W):
            fail("MAIN_CONTINUITY", "main must run continuously between the two boundary members")
        # An already-touching parallel member may extend the continuous
        # support union. R43 is checked below against actual union sections;
        # do not impose a stricter per-single-timber bearing requirement here.

    # The actual ordered main/wall rails induce every physically open span.
    # Check completeness of each mark/seam member in each span, not a second
    # invocation of the construction procedure.
    rails = sorted([(row["rect"][A], row["rect"][A + 2]) for row in groups["main"] + groups["rc_parallel"]])
    open_spans = [(left[1], right[0]) for left, right in zip(rails, rails[1:]) if right[0] - left[1] >= W]
    for kind, points in (("secondary:mark", [(row["center"], None) for row in expected_marks]),
                         ("secondary:seam", [(center, key) for key, center in expected_centers[B].items()])):
        obligations = {(lo, hi, center, key) for lo, hi in open_spans for center, key in points}
        actual = set()
        for row in groups[kind]:
            actual.add((row["rect"][A], row["rect"][A + 2], row["center"], row["seam_key"]))
            if row["axis"] != "uv"[A] or row["shift"]:
                fail("SECONDARY_AXIS", "rectangular jig/seam member changed axis or position")
        if actual != obligations or len(groups[kind]) != len(obligations):
            fail("SECONDARY_SET", "missing/extra/changed member in a complete eligible span")
    for index, row in enumerate(members):
        r = row["rect"]
        for other in members[index + 1:]:
            s = other["rect"]
            if min(r[2], s[2]) > max(r[0], s[0]) and min(r[3], s[3]) > max(r[1], s[1]):
                fail("COLLISION", "two positive-volume timber footprints overlap")
        if row["kind"] == "boundary":
            continue
        axis, cross = "uv".index(row["axis"]), 1 - "uv".index(row["axis"])
        for end in (0, 1):
            value = r[axis + 2 * end]
            supports = [s["rect"] for s in members if s is not row and s["rect"][axis + (0 if end else 2)] == value and s["rect"][cross] <= r[cross] and s["rect"][cross + 2] >= r[cross + 2]]
            if not supports:
                fail("END_FIXATION", "a nonboundary member end lacks a full-width timber stop")

    # R43: exact union sections at every material panel edge. The historical
    # oracle's short-gap bridge exception is intentionally NOT used: an empty
    # 1 mm interval remains empty and cannot stand in for native support.
    for q in (0, 1):
        other = 1 - q
        physical_bodies = {index: (low, high) for index, low, high in body_intervals[q]}
        for key, seam in expected_centers[q].items():
            left_panel, right_panel = physical_bodies.get(key), physical_bodies.get(key + 1)
            if left_panel is None or right_panel is None:
                continue  # not an effective two-panel seam inside the finish
            for _, panel_lo, panel_hi in body_intervals[other]:
                breaks = {panel_lo, panel_hi}
                for row in members:
                    for value in (row["rect"][other], row["rect"][other + 2]):
                        if panel_lo < value < panel_hi:
                            breaks.add(value)
                points = sorted(breaks)
                for start, finish in zip(points, points[1:]):
                    intervals = sorted((row["rect"][q], row["rect"][q + 2]) for row in members if row["rect"][other] <= start and row["rect"][other + 2] >= finish)
                    union = []
                    for left, right in intervals:
                        if union and left <= union[-1][1]:
                            union[-1][1] = max(union[-1][1], right)
                        else:
                            union.append([left, right])
                    left_edge, right_edge = seam - floor_gap, seam + ceil_gap
                    # The contact union is restricted to this seam's two
                    # actual panels. Continuous wood across another seam is
                    # not additional bearing inside a narrower middle panel.
                    left_width = max((left_edge - max(lo, left_panel[0]) for lo, hi in union if lo < left_edge <= hi), default=0)
                    right_width = max((min(hi, right_panel[1]) - right_edge for lo, hi in union if lo <= right_edge < hi), default=0)
                    if min(left_width, right_width) * x["den"] < x["num"]:
                        fail("R43_SUPPORT", f"{'uv'[q]} k={key} [{start},{finish}] has {left_width}/{right_width} mm, X={x['num']}/{x['den']}")
    # At each actual member span, no consecutive boundary/seam/jig center may
    # exceed the declared upper modulus. Use physical actual transverse rows.
    for lo, hi in open_spans:
        positions = {bounds[B], bounds[B + 2]}
        positions.update(row["center"] for row in members if row["kind"].startswith("secondary:") and row["rect"][A] == lo and row["rect"][A + 2] == hi)
        ordered = sorted(positions)
        if any(right - left > step for left, right in zip(ordered, ordered[1:])):
            fail("MAX_SPACING", "actual support center spacing exceeds the upper modulus")
    return errors


def make_case(A=3709, B=2000, *, corner="min-min", along="v", gap=2,
              seam_retreat="ft02", r_butt=True, origin=(0, 0), threshold=(8, 1)):
    """Explicit standard test vector only; not a product default resolver."""
    sizes = (A, B) if along == "v" else (B, A)
    return {"bounds": [origin[0], origin[1], origin[0] + sizes[0], origin[1] + sizes[1]],
            "parameters": {"panelWidth": 915, "panelLength": 1830, "gap": gap,
                           "timberWidth": 27, "timberDepth": 33, "maxSecondarySpacing": 367},
            "layout": {"corner": corner, "lengthAlong": along},
            "seam_retreat": seam_retreat, "r_butt": r_butt,
            "threshold": {"num": threshold[0], "den": threshold[1]}}


def cases():
    """Small named review vectors, including known historical/native mismatch."""
    return {
        "first_seam_ft02": make_case(940),
        "last_seam_ft02": make_case(3700),
        "right_butt_1mm": make_case(3709, seam_retreat="none"),
        "left_butt_2mm": make_case(3709, corner="max-min", seam_retreat="none"),
        "no_action_stage2": make_case(3740, 3301, seam_retreat="none", r_butt=False),
        "legacy_short_gap_is_not_native_support": make_case(3720),
        "reverse_odd_gap": make_case(3709, corner="max-max", along="u", gap=3),
        "translated": make_case(3709, origin=(-123, 456), seam_retreat="none"),
    }


def scan():
    """Finite one-variable-at-a-time 1 mm physical boundary windows.

    A: [910,970] first seam/FT02, [3650,3740] last seam/FT02/butt.
    B: [1820,1880] first board-end seam/FT02. Four corners, both axes,
    gaps 0..3. No cubic dimensions cross-product and no native subprocess.
    Additional no-retreat/no-butt zero-action and exact-rational vectors are
    included. Every checker rejection is counted and sampled, never skipped.
    """
    counts = {"constructed": 0, "accepted": 0, "physical_rejected": 0, "construction_rejected": 0}
    codes, samples, unexpected = {}, [], []
    count = 0

    def assess(name, case):
        nonlocal count
        count += 1
        try:
            output = build(case)
        except ValueError as exc:
            counts["construction_rejected"] += 1
            issues = [str(exc)]
        else:
            counts["constructed"] += 1
            issues = check(case, output)
            counts["physical_rejected" if issues else "accepted"] += 1
        issue_codes = {issue.split(":", 1)[0] for issue in issues}
        for code in sorted(issue_codes):
            codes[code] = codes.get(code, 0) + 1
        physical_codes = {"I52_PANEL_MAX", "D43_ORDER", "D1_DERIVED", "COLLISION", "R43_SUPPORT", "END_FIXATION", "MAX_SPACING", "MEMBER_BOUNDS", "SHORT_PIECE"}
        if issue_codes - physical_codes:
            unexpected.append({"case": name, "codes": sorted(issue_codes - physical_codes)})
        if issues and len(samples) < 16:
            samples.append({"case": name, "input": case, "issues": issues[:3]})
        return issues

    for corner in ("min-min", "max-min", "min-max", "max-max"):
        for along in ("u", "v"):
            for gap in range(4):
                for size in list(range(910, 971)) + list(range(3650, 3741)):
                    assess(f"A={size}/{corner}/{along}/g={gap}", make_case(size, corner=corner, along=along, gap=gap))
                for size in range(1820, 1881):
                    assess(f"B={size}/{corner}/{along}/g={gap}", make_case(3740, size, corner=corner, along=along, gap=gap))
            assess(f"zero-action/{corner}/{along}", make_case(3740, 3301, corner=corner, along=along, seam_retreat="none", r_butt=False))
    for size in range(3708, 3717):
        for num, den in ((8, 1), (11, 1), (45, 4), (12, 1)):
            for butt in (False, True):
                assess(f"bearing/A={size}/X={num}/{den}/butt={butt}", make_case(size, seam_retreat="none", r_butt=butt, threshold=(num, den)))
    # D43/I52 counterexample is a real rejection, not an exception to panel size.
    small = make_case(82, 2000, gap=0)
    small["parameters"]["panelWidth"] = 40
    panel_limit_issues = assess("I52-retreat-would-overgrow-last-board", small)
    if not any(issue.startswith("I52_PANEL_MAX:") for issue in panel_limit_issues):
        unexpected.append({"case": "I52-retreat-would-overgrow-last-board", "codes": ["EXPECTED_I52_REJECTION_MISSING"]})
    narrow = make_case(112, 200, gap=0, threshold=(30, 1))
    narrow["parameters"].update(panelWidth=42, timberWidth=28)
    narrow_issues = assess("R43-continuous-wood-cannot-exceed-middle-panel", narrow)
    if not any(issue.startswith("R43_SUPPORT:") for issue in narrow_issues):
        unexpected.append({"case": "R43-continuous-wood-cannot-exceed-middle-panel", "codes": ["EXPECTED_PANEL_BEARING_REJECTION_MISSING"]})
    derived_limits = []
    outside_origin = make_case(100, 100, corner="max-min", origin=(-D1, 0), seam_retreat="none")
    oversized_length = make_case(2 * D1, 100, origin=(-D1, 0), gap=0, seam_retreat="none")
    oversized_length["parameters"]["panelWidth"] = D1
    for name, case in (("D1-derived-panel-origin", outside_origin), ("D1-automatic-timber-length", oversized_length)):
        issues = assess(name, case)
        derived_limits.append({"case": name, "input": case, "issues": issues})
        if not any(issue.startswith("D1_DERIVED:") for issue in issues):
            unexpected.append({"case": name, "codes": ["EXPECTED_D1_DERIVED_REJECTION_MISSING"]})
    return {"schema": "r03-retreat-scan/1", "ok": not unexpected, "step_mm": 1, "cases": count,
            "counts": counts, "checker_codes": codes, "rejected_samples": samples,
            "unexpected_disagreements": unexpected, "panel_limit_counterexample": {"input": small, "issues": panel_limit_issues},
            "narrow_panel_bearing_counterexample": {"input": narrow, "issues": narrow_issues},
            "derived_limit_counterexamples": derived_limits,
            "note": "Physical rejections are retained; historical oracle pass is not native World approval."}


MUTATIONS = {
    "missing_main": "MAIN_SET", "skip_butt": "BUTT_POLICY",
    "over_bearing": "R43_SUPPORT", "missing_panel": "PANEL_SET",
    "panel_identity": "PANEL_SET", "stale_retreat_panel": "PANEL_RECT",
    "renumber_seam": "SEAM_KEY", "wrong_split_rounding": "JIG_MARKS",
    "floating_end": "END_FIXATION", "duplicate_member": "MEMBER_DUPLICATE",
    "boolean_origin": "OUTPUT_SCHEMA",
}


def mutation_child(name):
    case = make_case(3740, 3301, seam_retreat="none", r_butt=False) if name == "wrong_split_rounding" else make_case(3700 if name == "stale_retreat_panel" else 3709)
    output = build(case)
    baseline = check(case, output)
    if baseline:
        print(json.dumps({"marker": "R03_MUTATION_HARNESS_ERROR", "name": name, "issues": baseline}))
        return 2
    main = next(row for row in reversed(output["members"]) if row["kind"] == "main")
    if name == "missing_main":
        output["members"].remove(main)
    elif name == "skip_butt":
        shift = main["shift"]
        main["rect"][0] -= shift
        main["rect"][2] -= shift
        main["center"] -= shift
        main["shift"] = 0
    elif name == "over_bearing":
        main["rect"][0] += 20
        main["rect"][2] += 20
        main["center"] += 20
        main["shift"] += 20
    elif name == "missing_panel":
        output["panels"].pop()
    elif name == "panel_identity":
        output["panels"][-1]["i"] += 100
    elif name == "stale_retreat_panel":
        for row in output["panels"]:
            if row["i"] == 3:
                row["rect"][2] += 8
            elif row["i"] == 4:
                row["rect"][0] += 8
    elif name == "renumber_seam":
        output["seam_rows"][-1]["k"] += 1
    elif name == "wrong_split_rounding":
        row = next(row for row in output["mark_rows"] if row["center"] == 3117)
        row["center"] -= 1
        row["delta"] -= 1
        output["marks"][output["marks"].index(3117)] -= 1
        for member in output["members"]:
            if member["kind"] == "secondary:mark" and member["center"] == 3117:
                member["center"] -= 1
                member["rect"][1] -= 1
                member["rect"][3] -= 1
    elif name == "floating_end":
        member = next(row for row in output["members"] if row["kind"] == "secondary:mark")
        member["rect"][0] += 1
        member["length"] -= 1
    elif name == "duplicate_member":
        output["members"].append(copy.deepcopy(main))
    elif name == "boolean_origin":
        output["origin"][0] = False
    else:
        raise ValueError("unknown mutation")
    problems = check(case, output)
    wanted = MUTATIONS[name]
    killed = any(problem.startswith(wanted + ":") for problem in problems)
    print(json.dumps({"marker": "R03_MUTATION_KILLED" if killed else "R03_MUTATION_SURVIVED", "name": name, "expected": wanted, "issues": problems}))
    return 1 if killed else 0


def mutations():
    rows = []
    for name, expected in MUTATIONS.items():
        command = [sys.executable, "-B", str(Path(__file__).resolve()), "--mutation", name]
        try:
            child = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            rows.append({"name": name, "status": "HARNESS_TIMEOUT", "timeout_seconds": 10})
            continue
        try:
            message = json.loads(child.stdout)
        except (ValueError, TypeError):
            message = {}
        accepted = (child.returncode == 1 and not child.stderr and message.get("marker") == "R03_MUTATION_KILLED" and message.get("name") == name and message.get("expected") == expected and any(str(issue).startswith(expected + ":") for issue in message.get("issues", [])))
        rows.append({"name": name, "status": "killed" if accepted else "HARNESS_FAILURE", "returncode": child.returncode, "expected": expected, "output": message or child.stdout, "stderr": child.stderr})
    return {"schema": "r03-retreat-mutations/1", "ok": all(row["status"] == "killed" for row in rows), "timeout_seconds_per_child": 10, "rows": rows}


def legacy_comparison():
    """Historical builder is a third witness only, never this checker's helper."""
    source = Path(__file__).resolve().parents[2] / "geometry-core/framing-template/oracle/framing_oracle.py"
    spec = importlib.util.spec_from_file_location("r03_historical_oracle", source)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    rows = []
    for name, case in cases().items():
        result = build(case)
        box, p, layout, x = _facts(case)
        starts = layout["corner"].split("-")
        a = 0 if layout["lengthAlong"] == "v" else 1
        room = {"outer": [[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]}
        old_layout = {"A": "xy"[a], "a_start": starts[a], "b_start": starts[1 - a]}
        params = {"P": p["panelWidth"], "L": p["panelLength"], "gap": p["gap"], "w": p["timberWidth"], "M": p["maxSecondarySpacing"], "X": Fraction(x["num"], x["den"]), "min_piece": p["timberWidth"]}
        flags = set()
        if case["seam_retreat"] == "none":
            flags.update(("no_sliver", "no_seam_retreat"))
        if not case["r_butt"]:
            flags.add("no_r_butt")
        previous = old.build(room, old_layout, params, mut=frozenset(flags))
        expected = sorted((row["kind"] + (":" + row["role"] if row["kind"] == "secondary" else ""), tuple(row["rect"])) for row in previous["timbers"])
        actual = sorted((row["kind"], tuple(row["rect"])) for row in result["members"])
        rows.append({"case": name, "members_equal": actual == expected,
                     "seams_equal": result["seams"]["uv"[a]] == sorted(previous["seams_a"]) and result["seams"]["uv"[1 - a]] == sorted(previous["seams_b"]),
                     "new_checker": check(case, result), "historical_checker": old.check(previous, params),
                     "historical_conflicts": previous["conflicts"], "historical_core_limits": previous["core_limits"]})
    return {"schema": "r03-retreat-legacy-comparison/1", "ok": all(row["members_equal"] and row["seams_equal"] for row in rows), "rows": rows,
            "limitation": "Historical check can accept unsupported short intervals; exact new R43 failures are shown, not suppressed."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--mutations", action="store_true")
    parser.add_argument("--mutation", choices=tuple(MUTATIONS))
    parser.add_argument("--legacy", action="store_true")
    args = parser.parse_args(argv)
    if args.mutation:
        return mutation_child(args.mutation)
    if args.scan:
        report = scan()
    elif args.mutations:
        report = mutations()
    elif args.legacy:
        report = legacy_comparison()
    else:
        report = {name: {"candidate": build(case), "checker": check(case, build(case))} for name, case in cases().items()}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
