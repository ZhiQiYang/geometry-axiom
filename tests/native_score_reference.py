"""Frozen full-load score oracle from native_shards.py blob
07427c4745217b51578d7c8919042170ba551831 (PR379 d996d7a2).
Keep the original candidate order, tie handling and global objective.
This is a test reference, never imported by the planner.
"""
from itertools import combinations


def _swap_scenarios(parts, loads, costs):
    """One bounded, deterministic swap sweep; retain every measured scenario."""
    def score(values):
        return tuple(sorted((ms for load in values for ms in load), reverse=True))

    current = score(loads)
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            for left in sorted(parts[i]):
                for right in sorted(parts[j]):
                    candidate = [load[:] for load in loads]
                    for r, (a, b) in enumerate(zip(costs[left], costs[right])):
                        candidate[i][r] += b - a
                        candidate[j][r] -= b - a
                    improved = score(candidate)
                    if improved < current:
                        parts[i].remove(left)
                        parts[i].add(right)
                        parts[j].remove(right)
                        parts[j].add(left)
                        loads[:] = candidate
                        current = improved
                        break



def _exchange_scenarios(parts, loads, costs):
    """One deterministic two-for-one exchange among 16 costly suites per part.

    Pair swaps keep the number of suites in each part fixed and can stop at a
    local minimum. This bounded search can change those counts while retaining
    every suite and every scenario. The objective is the same complete vector
    of descending loads used by the original swap sweep.
    """
    def score(values):
        return tuple(sorted((ms for load in values for ms in load), reverse=True))

    candidates = [sorted(part, key=lambda name: (-max(costs[name]), name))[:16]
                  for part in parts]
    current, best = score(loads), None
    for i in range(len(parts)):
        for j in range(len(parts)):
            if i == j:
                continue
            for left, middle in combinations(candidates[i], 2):
                combined = [a + b for a, b in zip(costs[left], costs[middle])]
                for right in candidates[j]:
                    candidate = [load[:] for load in loads]
                    for r, (a, b) in enumerate(zip(combined, costs[right])):
                        candidate[i][r] += b - a
                        candidate[j][r] += a - b
                    improved = score(candidate)
                    if improved < current:
                        current = improved
                        best = i, j, left, middle, right, candidate
    if best is not None:
        i, j, left, middle, right, candidate = best
        parts[i].difference_update((left, middle))
        parts[i].add(right)
        parts[j].remove(right)
        parts[j].update((left, middle))
        loads[:] = candidate
