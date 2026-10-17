"""#240 S6 oracle: under D10b, are D30 cells still the regions enclosed by the grid-line segments?

Implements the clauses literally with exact integers.  Clause text as of main 02baea2c (公理層.md there is byte-identical
to c144c013; the K/M/W/H layering keeps these formulas in the W blocks):
  D29  c(k) = phase + k*step   (公理層.md L622; REPEAT_PANEL is the same with pitch, L623-624)
  D10b shift(axis, band) = delta if delta is set and band is odd (lowest bit 1, incl. -1) else 0      (L654)
       u-line k in band j : u = c_u(k) + shift_u(j),  along v over the UNSTAGGERED [c_v(j), c_v(j+1)]   (L656)
       v-line k in band i : v = c_v(k) + shift_v(i),  along u over the UNSTAGGERED [c_u(i), c_u(i+1)]
  D30  cell(i,j) = [c_u(i)+shift_u(j), +step_u] x [c_v(j)+shift_v(i), +step_v]                         (L671-672)

Three properties per configuration, over cells i,j in [-N, N]:
  ENCLOSED    every side of every cell lies on segments of the matching line (D29 "圍成格子", D10b "因此 cell 仍是軸對齊矩形")
  PARTITION   inside a central window every unit square is covered by exactly one cell (no overlap, no hole)
  BAND_EDGES  every u-line segment in band j runs exactly over the UNSTAGGERED c_v(j)..c_v(j+1), and symmetrically for
              v-lines (D10b L656 "band 的切開用另一軸未加相位差的格線", R22 W "即使該軸自己也有相位差").  This is recomputed
              here from c(k) alone, independent of u_segments / v_segments.  Without it a mutant that cuts the bands
              with the other axis's STAGGERED lines survived (review 2026-10-17, mutant M4b): with both axes staggered
              ENCLOSED and PARTITION stay false either way, so only the band cut itself can tell the two apart.
Plus one pinned count used by the proposal's plain-language R22 text: in the δ50/δ50 example (#240 R14 numbers) 25 of the
81 cells are still enclosed, so "兩軸都錯開時格子不被圍住" must not be stated for every cell.

Teeth: mutants of the configuration space must make the checkers fire even without stagger
(drop one drawn segment -> not ENCLOSED and not BAND_EDGES; move one cell by 1 mm -> not PARTITION).

Usage: python s6_stagger_oracle.py            (prints the table, exit 0 iff every expectation holds)
       python s6_stagger_oracle.py --selftest (runs the source mutants listed at the bottom; each must be killed)
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


def band_edges(g):
    """D10b: the segment of u-line k in band j spans the other axis's UNSTAGGERED c_v(j)..c_v(j+1), even when the v axis
    is staggered itself; same for v-lines.  The expected interval is recomputed from phase/step only."""
    bad = []
    for band in range(-N, N + 1):
        for k in range(-N, N + 1):
            want_u = (g.pv + band * g.sv, g.pv + (band + 1) * g.sv)
            if want_u not in g.u_segments(g.cu(k) + shift(g.du, band)):
                bad.append(("u", k, band))
            want_v = (g.pu + band * g.su, g.pu + (band + 1) * g.su)
            if want_v not in g.v_segments(g.cv(k) + shift(g.dv, band)):
                bad.append(("v", k, band))
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


def run_case(name, g, expect_enclosed, expect_partition, expect_band_edges=True):
    bad = enclosed(g)
    over, hole = partition(g)
    cut = band_edges(g)
    ok = ((not bad) == expect_enclosed and (over == 0 and hole == 0) == expect_partition
          and (not cut) == expect_band_edges)
    return ok, (f"{'OK ' if ok else 'BAD'} {name:<46} enclosed={not bad!s:<5} open_cells={len(bad):<3} "
                f"overlap_mm2={over:<5} hole_mm2={hole:<5} band_edges={not cut}")


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
        ("MUTANT drop one segment (no stagger)", Grid(0, 100, None, 0, 100, None, drop=("u", 1, 0)), False, True, False),
        ("MUTANT nudge one cell 1 mm (no stagger)", Grid(0, 100, None, 0, 100, None, nudge=(0, 0)), False, False),
    ]
    for name, g, *expect in cases:
        ok, line = run_case(name, g, *expect)
        rows.append(line)
        all_ok &= ok
    # Pinned count behind the plain-language R22 wording: two staggered axes leave SOME cells enclosed, not none.
    g = Grid(0, 100, 50, 0, 100, 50)
    total = (2 * N + 1) ** 2
    still = total - len(enclosed(g))
    ok = (still, total) == (25, 81)
    rows.append(f"{'OK ' if ok else 'BAD'} R14 example δ50/δ50: {still}/{total} cells still enclosed (expected 25/81)")
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
    rows.append(f"sweep single-axis: {swept['single'][1]}/{swept['single'][0]} enclosed AND partition AND band_edges")
    rows.append(f"sweep biaxial    : {swept['biaxial'][1]}/{swept['biaxial'][0]} NOT enclosed AND NOT partition, band_edges")
    all_ok &= swept["single"][0] == swept["single"][1] and swept["biaxial"][0] == swept["biaxial"][1]
    print("\n".join(rows))
    print("ALL EXPECTATIONS HOLD" if all_ok else "EXPECTATION FAILED")
    return 0 if all_ok else 1


# Source mutants of this file (the reviewer's set of 2026-10-17 plus the v-axis twin of M4b).  Each must make the
# oracle exit non-zero, except M4, which is equivalent: shift(delta, 0) is 0 for every delta, so it changes nothing.
MUTANTS = [
    ("M1 shift ignores parity", "return delta if (delta is not None and band & 1) else 0", "return delta if (delta is not None) else 0", True),
    ("M2 cell ignores the v shift", "v0 = self.cv(j) + shift(self.dv, i)", "v0 = self.cv(j)", True),
    ("M3 covered() always true", "def covered(interval, pieces):\n", "def covered(interval, pieces):\n    return True\n", True),
    ("M4 u bands cut at shift(dv, 0) [equivalent]", "out.append((self.cv(j), self.cv(j + 1)))",
     "out.append((self.cv(j) + shift(self.dv, 0), self.cv(j + 1) + shift(self.dv, 0)))", False),
    ("M4b u bands cut at the STAGGERED v lines", "out.append((self.cv(j), self.cv(j + 1)))",
     "out.append((self.cv(j) + shift(self.dv, 1), self.cv(j + 1) + shift(self.dv, 1)))", True),
    ("M4c v bands cut at the STAGGERED u lines", "out.append((self.cu(i), self.cu(i + 1)))",
     "out.append((self.cu(i) + shift(self.du, 1), self.cu(i + 1) + shift(self.du, 1)))", True),
    ("M5 partition window empty", "wx0, wx1, wy0, wy1 = g.cu(-1), g.cu(2), g.cv(-1), g.cv(2)",
     "wx0, wx1, wy0, wy1 = g.cu(0), g.cu(0), g.cv(0), g.cv(0)", True),
    ("M6 sweep admits pitch multiples", "legal_u = [d for d in range(-2 * su, 2 * su + 1) if d % su]",
     "legal_u = [d for d in range(-2 * su, 2 * su + 1) if d]", True),
    ("M7 only cells -1..1", "\nN = 4\n", "\nN = 1\n", True),
]


def selftest():
    import subprocess
    import tempfile
    from pathlib import Path
    src = Path(__file__).read_text(encoding="utf-8")
    cut = src.index("# Source mutants of this file")
    body, tail = src[:cut], src[cut:]          # mutate the oracle proper, never the anchors listed below
    good = True
    with tempfile.TemporaryDirectory() as tmp:
        for name, old, new, must_kill in MUTANTS:
            assert body.count(old) == 1, f"mutation anchor for {name!r} must occur exactly once"
            path = Path(tmp) / "mutant.py"
            path.write_text(body.replace(old, new) + tail, encoding="utf-8")
            killed = subprocess.run([sys.executable, "-I", str(path)], capture_output=True).returncode != 0
            good &= killed == must_kill
            verdict = "KILLED" if killed else "SURVIVED"
            print(f"{'OK ' if killed == must_kill else 'BAD'} {name:<46} {verdict}"
                  + ("" if must_kill else " (expected: equivalent mutant)"))
    print("selftest: " + ("every non-equivalent mutant is killed" if good else "A MUTANT SURVIVED"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(selftest() if sys.argv[1:] == ["--selftest"] else main())
