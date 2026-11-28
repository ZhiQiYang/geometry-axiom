"""Independent exact rectangle/R43 oracle for the PF-6 App projection.

Construction uses only the authored 300 mm square, 100 mm panels, 3 mm gaps,
chosen odd timber width, and R45's explicit selection.  It does not import
product code or consume the builder's rectangles to predict the answer.
The separate checker partitions each two-panel seam at footprint vertices,
unions cross-sections, and measures continuous coverage from each panel edge.
"""
from fractions import Fraction


def construct_rectangles(width=27, omit_first_primary=False, side=1):
    low, high = width // 2, width - width // 2
    # I13: first map the seam centre into the host; only then put the odd
    # extra millimetre on +cross. In finish coordinates a negative side swaps
    # the two half-widths for U-running primaries, not for V-running members.
    below, above = (low, high) if side == 1 else (high, low)
    primary_centres = [204] if omit_first_primary else [101, 204]
    rectangles = [(0, 0, width, 300), (300-width, 0, 300, 300),
                  (width, 0, 300-width, width),
                  (width, 300-width, 300-width, 300)]
    rectangles += [(width, c-below, 300-width, c+above) for c in primary_centres]
    stops = [(0, width)] + [(c-below, c+above) for c in primary_centres] + [(300-width, 300)]
    for centre in (101, 204):
        rectangles += [(centre-low, left[1], centre+high, right[0])
                       for left, right in zip(stops, stops[1:])]
    return rectangles


def host_rectangle(rectangle, side):
    u0, v0, u1, v1 = rectangle
    return rectangle if side == 1 else (u0, -v1, u1, -v0)


def continuous_width(intervals, edge, boundary, left):
    merged = []
    for lo, hi in sorted(intervals):
        lo, hi = max(lo, min(edge, boundary)), min(hi, max(edge, boundary))
        if lo >= hi:
            continue
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
        else:
            merged.append((lo, hi))
    for lo, hi in merged:
        if lo <= edge <= hi:
            return edge-lo if left else hi-edge
    return 0


def support_parts(rectangles):
    rows = []
    # The three disjoint longitudinal panel bodies are fixed by D43.
    bodies = [(0, 100), (103, 203), (206, 300)]
    for axis in (0, 1):
        along = 1-axis
        for k in (0, 1):
            edges = (100+103*k, 103+103*k)
            bounds = (0 if k == 0 else 103, 203 if k == 0 else 300)
            for start, stop in bodies:
                cuts = {start, stop}
                for rectangle in rectangles:
                    cuts.update(x for x in (rectangle[along], rectangle[along+2])
                                if start < x < stop)
                ordered = sorted(cuts)
                spans = []
                for lo, hi in zip(ordered, ordered[1:]):
                    midpoint = Fraction(lo+hi, 2)
                    intervals = [(r[axis], r[axis+2]) for r in rectangles
                                 if r[along] < midpoint < r[along+2]]
                    left = continuous_width(intervals, edges[0], bounds[0], True)
                    right = continuous_width(intervals, edges[1], bounds[1], False)
                    if spans and spans[-1][1] == lo and spans[-1][2:] == (left, right):
                        spans[-1] = (spans[-1][0], hi, left, right)
                    else:
                        spans.append((lo, hi, left, right))
                rows += [("uv"[axis], k, start, stop, lo, hi, left, right)
                         for lo, hi, left, right in spans]
    return sorted(rows)


def disclosed_support(state):
    fill = next(row for row in state["panelFills"] if row["definition"]["id"] == 1)
    data = fill["derived"]
    rows = []
    for part in data["support"]:
        seam = data["effectiveSeams"][part["seam"]]
        rows.append((seam["axis"], int(seam["k"]),
                     *map(int, seam["range"]), *map(int, part["range"]),
                     int(part["left"]), int(part["right"])))
    return sorted(rows)
