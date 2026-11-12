"""依固定CI耗時配置確定性分片；每個套件恰好出現一次。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

TIMINGS = Path(__file__).with_name('native_shard_timings.json')


def parse_shard(value):
    match = re.fullmatch(r'([1-9][0-9]*)/([1-9][0-9]*)', value)
    if not match or int(match[1]) > int(match[2]):
        raise argparse.ArgumentTypeError('分片必須是1起算的i/n，且1 <= i <= n')
    return int(match[1]), int(match[2])


def timing_weights():
    weights = json.loads(TIMINGS.read_text(encoding='utf-8'))['timings_ms']
    if any(not isinstance(value, int) or value <= 0 for value in weights.values()):
        raise ValueError('CI耗時權重必須是正整數毫秒')
    return weights


def measured_profiles():
    """Keep complete CI observations separate; do not average away runner skew."""
    runs = json.loads(TIMINGS.read_text(encoding='utf-8'))['measured_runs']
    if len(runs) < 2:
        raise ValueError('分片規劃至少需要兩輪完整量測')
    profiles = []
    for run in runs:
        measured = {}
        for shard in run['shards']:
            values = shard['timings_ms']
            if measured.keys() & values.keys():
                raise ValueError('同輪分片量測包含重複套件')
            if any(not isinstance(name, str) or not name or type(ms) is not int or ms <= 0
                   for name, ms in values.items()):
                raise ValueError('分片量測必須是具名套件的正整數毫秒')
            measured.update(values)
        if (not measured or len(measured) != run['suite_count']
                or (profiles and measured.keys() != profiles[0].keys())):
            raise ValueError('各輪完整量測的套件集合／數量不相等')
        profiles.append(measured)
    return profiles


def _improve_scenarios(parts, loads, costs):
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


def _scenario_owners(suites, count, profiles):
    costs = {s.name: [p.get(s.name, 1000) for p in profiles] for s in suites}
    parts = [set() for _ in range(count)]
    loads = [[0] * len(profiles) for _ in range(count)]
    for name in sorted(costs, key=lambda n: (-max(costs[n]), n)):
        candidates = [[a + b for a, b in zip(load, costs[name])] for load in loads]
        index = min(range(count), key=lambda i: (max(candidates[i]), sum(candidates[i]), i))
        parts[index].add(name)
        loads[index] = candidates[index]
    _improve_scenarios(parts, loads, costs)
    return {name: i for i, part in enumerate(parts) for name in part}


def validate_partition(suites, partitions):
    wanted = Counter(s.name for s in suites)
    actual = Counter(s.name for part in partitions for s in part)
    if any(count != 1 for count in wanted.values()):
        raise ValueError('完整套件清單本身有重複名稱')
    if wanted != actual:
        missing, extra = wanted - actual, actual - wanted
        raise ValueError('分片聯集不相等或重疊：missing=%s extra=%s' % (dict(missing), dict(extra)))


def partition_suites(suites, count, weights=None):
    suites = list(suites)
    if count < 1 or count > len(suites):
        raise ValueError('分片數必須介於1與完整套件數之間')
    if weights is None:
        owners = _scenario_owners(suites, count, measured_profiles())
    else:
        # Explicit weights retain the original scalar LPT API and its history.
        costs = {s.name: weights.get(s.name, 1000) for s in suites}
        loads, owners = [0] * count, {}
        for suite in sorted(suites, key=lambda s: (-costs[s.name], s.name)):
            index = min(range(count), key=lambda i: (loads[i], i))
            owners[suite.name] = index
            loads[index] += costs[suite.name]
    # 片內保留原完整runner的順序；不依機器速度、hash randomization或cache狀態。
    parts = [[s for s in suites if owners[s.name] == i] for i in range(count)]
    validate_partition(suites, parts)
    return parts


def profile_digest():
    return hashlib.sha256(TIMINGS.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
