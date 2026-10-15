"""#240 S6 oracle: under D10b, are D30 cells still the regions enclosed by the drawn segments?

Implements the clauses literally with exact integers (main 839063b9):
  D29  c(k) = phase + k*step                                     (REPEAT; REPEAT_PANEL is the same with pitch)
  D10b shift(axis, band) = delta if delta is set and band is odd (lowest bit 1, incl. -1) else 0
       u-line k in band j : u = c_u(k) + shift_u(j),  along v over the UNSTAGGERED [c_v(j), c_v(j+1)]
       v-line k in band i : v = c_v(k) + shift_v(i),  along u over the UNSTAGGERED [c_u(i), c_u(i+1)]
  D30  cell(i,j) = [c_u(i)+shift_u(j), +step_u] x [c_v(j)+shift_v(i), +step_v]

Two properties per configuration, over cells i,j in [-N, N]:
  ENCLOSED   every side of every cell lies on drawn segments of the matching line (D29 "圍成格子", D10b "因此 cell 仍是軸對齊矩形")
  PARTITION  inside a central window every unit square is covered by exactly one cell (no overlap, no hole)

Teeth: two mutants of the configuration space must make the checkers fire even without stagger
(drop one drawn segment -> not ENCLOSED; move one cell by 1 mm -> not PARTITION).

Usage: python s6_stagger_oracle.py            (prints the table, exit 0 iff every expectation holds)
"""
from __future__ import annotations

import itertools
import sys


def shift(delta, band):
    return delta if (delta is not None and band & 1) else 0


class Grid:
    def __init__(self, pu, su, du, pv, sv, dv, drop=None, nudge=None):
        self.pu, self.su, self.du, self.pv, self.sv, self.dv = pu, su, du, pv, sv, dv
        self.drop, self.nudge = drop, nudge  # mutants

    def cu(self, k):
        return self.pu + k * self.su

    def cv(self, k):
        return self.pv + k * self.sv

    def cell(self, i, j):
        u0 = self.cu(i) + shift(self.du, j)
        v0 = self.cv(j) + shift(self.dv, i)
        if self.nudge == (i, j):
            u0 += 1
        return (u0, u0 + self.su, v0, v0 + self.sv)

    def u_segments(self, u):
        """Drawn u-line segments at abscissa u: list of v-intervals."""
        out = []
        for j in range(-N - 2, N + 3):
            s = shift(self.du, j)
            if (u - self.pu - s) % self.su == 0:
                k = (u - self.pu - s) // self.su
                if self.drop == ("u", k, j):
                    continue
                out.append((self.cv(j), self.cv(j + 1)))
        return out

    def v_segments(self, v):
        out = []
        for i in range(-N - 2, N + 3):
            s = shift(self.dv, i)
            if (v - self.pv - s) % self.sv == 0:
                k = (v - self.pv - s) // self.sv
                if self.drop == ("v", k, i):
                    continue
                out.append((self.cu(i), self.cu(i + 1)))
        return out


def covered(interval, pieces):
    lo, hi = interval
    for a, b in sorted(pieces):
        if a > lo:
            return False
        lo = max(lo, b)
        if lo >= hi:
            return True
    return lo >= hi


def enclosed(g):
    bad = []
    for i, j in itertools.product(range(-N, N + 1), repeat=2):
        u0, u1, v0, v1 = g.cell(i, j)
        sides = [covered((v0, v1), g.u_segments(u0)), covered((v0, v1), g.u_segments(u1)),
                 covered((u0, u1), g.v_segments(v0)), covered((u0, u1), g.v_segments(v1))]
        if not all(sides):
            bad.append((i, j))
    return bad


def partition(g):
    """Window W = [cu(-1), cu(2)] x [cv(-1), cv(2)].  Exact areas (mm^2) by coordinate compression:
    overlap = area covered by >= 2 cells, hole = area covered by none."""
    wx0, wx1, wy0, wy1 = g.cu(-1), g.cu(2), g.cv(-1), g.cv(2)
    rects = []
    for i, j in itertools.product(range(-N, N + 1), repeat=2):
        u0, u1, v0, v1 = g.cell(i, j)
        a, b, c, d = max(u0, wx0), min(u1, wx1), max(v0, wy0), min(v1, wy1)
        if a < b and c < d:
            rects.append((a, b, c, d))
    xs = sorted({wx0, wx1} | {r[0] for r in rects} | {r[1] for r in rects})
    ys = sorted({wy0, wy1} | {r[2] for r in rects} | {r[3] for r in rects})
    over = hole = 0
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            n = sum(1 for a, b, c, d in rects if a <= x0 and x1 <= b and c <= y0 and y1 <= d)
            area = (x1 - x0) * (y1 - y0)
            over += area if n > 1 else 0
            hole += area if n == 0 else 0
    return over, hole


N = 4


def run_case(name, g, expect_enclosed, expect_partition):
    bad = enclosed(g)
    over, hole = partition(g)
    ok = (not bad) == expect_enclosed and (over == 0 and hole == 0) == expect_partition
    return ok, f"{'OK ' if ok else 'BAD'} {name:<46} enclosed={not bad!s:<5} open_cells={len(bad):<3} overlap_mm2={over:<5} hole_mm2={hole}"


def main():
    rows, all_ok = [], True
    # Fixed examples (R14's numbers and a board-sized 交丁).
    cases = [
        ("none: step 100/100", Grid(0, 100, None, 0, 100, None), True, True),
        ("u-only δ50 (step 100/100)", Grid(0, 100, 50, 0, 100, None), True, True),
        ("v-only δ400 (D10b example 1830)", Grid(0, 915 + 2, None, 0, 1830, 400), True, True),
        ("both δ50/δ50 (R14 example)", Grid(0, 100, 50, 0, 100, 50), False, False),
        ("both δ-30/δ70", Grid(0, 100, -30, 0, 100, 70), False, False),
        # Teeth: the checkers must fire on broken but stagger-free grids.
        ("MUTANT drop one segment (no stagger)", Grid(0, 100, None, 0, 100, None, drop=("u", 1, 0)), False, True),
        ("MUTANT nudge one cell 1 mm (no stagger)", Grid(0, 100, None, 0, 100, None, nudge=(0, 0)), False, False),
    ]
    for name, g, e1, e2 in cases:
        ok, line = run_case(name, g, e1, e2)
        rows.append(line)
        all_ok &= ok
    # Exhaustive sweep on small pitches: every legal delta (non-zero, not a multiple of the pitch, both signs).
    swept = {"single": [0, 0], "biaxial": [0, 0]}
    for su, sv in [(4, 6), (5, 5), (6, 4), (7, 3)]:
        legal_u = [d for d in range(-2 * su, 2 * su + 1) if d % su]
        legal_v = [d for d in range(-2 * sv, 2 * sv + 1) if d % sv]
        for du in legal_u:
            for g in (Grid(1, su, du, 2, sv, None),):
                ok, line = run_case("", g, True, True)
                swept["single"][0] += 1
                swept["single"][1] += ok
                if not ok:
                    rows.append("single-axis counterexample " + line)
        for dv in legal_v:
            ok, line = run_case("", Grid(1, su, None, 2, sv, dv), True, True)
            swept["single"][0] += 1
            swept["single"][1] += ok
            if not ok:
                rows.append("single-axis counterexample " + line)
        for du in legal_u:
            for dv in legal_v:
                ok, line = run_case("", Grid(1, su, du, 2, sv, dv), False, False)
                swept["biaxial"][0] += 1
                swept["biaxial"][1] += ok
                if not ok:
                    rows.append("biaxial exception " + line)
    rows.append(f"sweep single-axis: {swept['single'][1]}/{swept['single'][0]} enclosed AND partition")
    rows.append(f"sweep biaxial    : {swept['biaxial'][1]}/{swept['biaxial'][0]} NOT enclosed AND NOT partition")
    all_ok &= swept["single"][0] == swept["single"][1] and swept["biaxial"][0] == swept["biaxial"][1]
    print("\n".join(rows))
    print("ALL EXPECTATIONS HOLD" if all_ok else "EXPECTATION FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
