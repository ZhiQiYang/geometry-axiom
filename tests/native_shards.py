"""依固定CI耗時配置確定性分片；每個套件恰好出現一次。"""
import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import re

TIMINGS = Path(__file__).with_name('native_shard_timings.json')
ADDED_EVIDENCE = Path(__file__).with_name('native_shard_added_evidence.json')
ADDED_R14_EVIDENCE = Path(__file__).with_name('native_shard_added_evidence_r14.json')
ADDED_RECEIPTS = Path(__file__).with_name('native_shard_added_receipts.json')


def _legacy_added_suite_costs():
    return _added_evidence_costs(ADDED_EVIDENCE)


def added_r14_suite_costs():
    return _added_evidence_costs(ADDED_R14_EVIDENCE)


def added_suite_costs():
    legacy = _legacy_added_suite_costs()
    r14 = added_r14_suite_costs()
    receipts = added_receipt_costs()
    if legacy.keys() & r14.keys():
        raise ValueError('R379_NEW_SUITE_UNIQUE_ACROSS_SOURCES')
    if (legacy.keys() | r14.keys()) & receipts.keys():
        raise ValueError('R396_ADDED_RECEIPT_DUPLICATE_LEGACY_SUITE')
    return {**legacy, **r14, **receipts}


def _added_evidence_costs(path):
    """Keep later observed suites separate from retained immutable 315-suite runs.

    Each upper bound is a conservative planning weight, NOT a historical
    observed timing. The referenced CI job may have failed another suite; the
    named suite itself must have an explicitly passing receipt.
    """
    data = json.loads(path.read_text(encoding='utf-8'))
    if (set(data) != {'schema', 'source_run', 'source_head', 'source_checkout',
                      'note', 'observations'}
            or data['schema'] != 'native-shard-added-suite-evidence/1'
            or not re.fullmatch(r'https://github\.com/ZhiQiYang/geometry-axiom/actions/runs/[0-9]+',
                                data['source_run'])
            or not re.fullmatch(r'[a-f0-9]{40}', data['source_head'])
            or not re.fullmatch(r'[a-f0-9]{40}', data['source_checkout'])
            or type(data['note']) is not str or not data['note']
            or type(data['observations']) is not list or not data['observations']):
        raise ValueError('R379_NEW_SUITE_SOURCE_PROVENANCE')
    bounds = {}
    for row in data['observations']:
        if type(row) is not dict or set(row) != {
                'name', 'source_job', 'discovered', 'passed',
                'seconds_rounded', 'planning_upper_ms'}:
            raise ValueError('R379_NEW_SUITE_ROW_SHAPE')
        name = row['name']
        rounded = row['seconds_rounded']
        upper = row['planning_upper_ms']
        if (type(name) is not str or not name or name in bounds
                or not re.fullmatch(re.escape(data['source_run']) + r'/job/[0-9]+',
                                    row['source_job'])
                or type(row['discovered']) is not int or row['discovered'] < 1
                or type(row['passed']) is not int or row['passed'] != row['discovered']
                or type(rounded) not in (int, float) or not 0 < rounded < 1200
                or type(upper) is not int or not rounded * 1000 < upper < 1200000):
            raise ValueError('R379_NEW_SUITE_PROVEN_OBSERVATION_AND_MARGIN')
        bounds[name] = upper
    return bounds



def added_receipt_costs():
    """Use source-bound, passing child rows without relabeling a failed CI job.

    Keep exit-only rows as exit-only. Their passed=1 is the runner's success
    sentinel, not an independently discovered test. Bounds are planning costs.
    """
    def matches(pattern, value):
        return type(value) is str and re.fullmatch(pattern, value) is not None

    data = json.loads(ADDED_RECEIPTS.read_text(encoding='utf-8'))
    if (type(data) is not dict or set(data) != {'schema', 'runs'}
            or data['schema'] != 'native-shard-added-receipts/1'
            or type(data['runs']) is not list or not data['runs']):
        raise ValueError('R396_ADDED_RECEIPT_SCHEMA')
    bounds, seen_runs = {}, set()
    for source in data['runs']:
        if (type(source) is not dict or set(source) != {
                'source_run', 'source_head', 'source_checkout', 'note', 'shards'}
                or not matches(r'https://github\.com/ZhiQiYang/geometry-axiom/actions/runs/[0-9]+',
                               source['source_run'])
                or source['source_run'] in seen_runs
                or not matches(r'[a-f0-9]{40}', source['source_head'])
                or not matches(r'[a-f0-9]{40}', source['source_checkout'])
                or type(source['note']) is not str or not source['note']
                or type(source['shards']) is not list or not source['shards']):
            raise ValueError('R396_ADDED_RECEIPT_SOURCE')
        seen_runs.add(source['source_run'])
        seen_shards = set()
        for shard in source['shards']:
            if (type(shard) is not dict or set(shard) != {
                    'source_job', 'shard', 'artifact_id', 'artifact_sha256',
                    'receipt_file', 'receipt_sha256', 'observations'}
                    or not matches(re.escape(source['source_run']) + r'/job/[0-9]+',
                                   shard['source_job'])
                    or type(shard['shard']) is not list or len(shard['shard']) != 2
                    or any(type(n) is not int for n in shard['shard'])
                    or not 1 <= shard['shard'][0] <= shard['shard'][1]
                    or tuple(shard['shard']) in seen_shards
                    or type(shard['artifact_id']) is not int or shard['artifact_id'] <= 0
                    or not matches(r'[a-f0-9]{64}', shard['artifact_sha256'])
                    or not matches(r'[a-f0-9]{64}', shard['receipt_sha256'])
                    or shard['receipt_file'] != 'shard-%s.json' % shard['shard'][0]
                    or type(shard['observations']) is not list or not shard['observations']):
                raise ValueError('R396_ADDED_RECEIPT_SHARD')
            seen_shards.add(tuple(shard['shard']))
            for entry in shard['observations']:
                if type(entry) is not dict or set(entry) != {'row', 'planning_upper_ms'}:
                    raise ValueError('R396_ADDED_RECEIPT_ENTRY')
                row, upper = entry['row'], entry['planning_upper_ms']
                if (type(row) is not dict or set(row) != {
                        'name', 'counted', 'total', 'passed', 'failed', 'skipped',
                        'seconds', 'ran', 'process_exit_code', 'allowed_skips',
                        'env_problem', 'crashed', 'expected_problem'}
                        or type(row['name']) is not str or not row['name']
                        or row['name'] in bounds
                        or any(type(row[key]) is not int or row[key] < 0 for key in
                               ('total', 'passed', 'failed', 'skipped', 'allowed_skips'))
                        or any(type(row[key]) is not bool for key in
                               ('counted', 'ran', 'env_problem', 'crashed'))
                        or type(row['process_exit_code']) is not int or row['process_exit_code'] != 0
                        or not row['ran'] or row['failed'] or row['skipped'] or row['allowed_skips']
                        or row['env_problem'] or row['crashed']
                        or type(row['expected_problem']) is not str
                        or type(row['seconds']) not in (int, float)
                        or not math.isfinite(row['seconds']) or not 0 < row['seconds'] < 1200
                        or type(upper) is not int or not row['seconds'] * 1000 < upper < 1200000):
                    raise ValueError('R396_ADDED_RECEIPT_PASS_AND_MARGIN')
                if row['counted']:
                    valid = row['total'] > 0 and row['passed'] == row['total']
                else:
                    valid = row['total'] == 0 and row['passed'] == 1
                if not valid:
                    raise ValueError('R396_ADDED_RECEIPT_COUNT_MODE')
                bounds[row['name']] = upper
    return bounds



def parse_shard(value):
    match = re.fullmatch(r'([1-9][0-9]*)/([1-9][0-9]*)', value)
    if not match or int(match[1]) > int(match[2]):
        raise argparse.ArgumentTypeError('分片必須是1起算的i/n，且1 <= i <= n')
    return int(match[1]), int(match[2])


def timing_weights():
    weights = json.loads(TIMINGS.read_text(encoding='utf-8'))['timings_ms']
    if any(not isinstance(value, int) or value <= 0 for value in weights.values()):
        raise ValueError('CI耗時權重必須是正整數毫秒')
    added = added_suite_costs()
    if weights.keys() & added.keys():
        raise ValueError('R379_NEW_SUITE_MUST_NOT_OVERWRITE_LEGACY_WEIGHT')
    return {**weights, **added}


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
    added = added_suite_costs()
    for measured in profiles:
        if measured.keys() & added.keys():
            raise ValueError('R379_NEW_SUITE_MUST_NOT_REWRITE_HISTORICAL_RECEIPT')
        measured.update(added)
    return profiles


def _swap_scenarios(parts, loads, costs):
    """One bounded, deterministic swap sweep; retain every measured scenario."""
    def score(values):
        return tuple(sorted((ms for load in values for ms in load), reverse=True))

    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            # Unchanged shard loads are a common multiset on both sides.
            # Removing it preserves the descending lexicographic comparison.
            current = score((loads[i], loads[j]))
            for left in sorted(parts[i]):
                for right in sorted(parts[j]):
                    a_load, b_load = loads[i][:], loads[j][:]
                    for r, (a, b) in enumerate(zip(costs[left], costs[right])):
                        a_load[r] += b - a
                        b_load[r] -= b - a
                    improved = score((a_load, b_load))
                    if improved < current:
                        candidate = [load[:] for load in loads]
                        candidate[i], candidate[j] = a_load, b_load
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
            pair_score = score((loads[i], loads[j]))
            for left, middle in combinations(candidates[i], 2):
                combined = [a + b for a, b in zip(costs[left], costs[middle])]
                for right in candidates[j]:
                    a_load, b_load = loads[i][:], loads[j][:]
                    for r, (a, b) in enumerate(zip(combined, costs[right])):
                        a_load[r] += b - a
                        b_load[r] += a - b
                    if score((a_load, b_load)) >= pair_score:
                        continue
                    # Promising trials still compare the complete vector with
                    # the best trial, which may involve different shard pairs.
                    candidate = [load[:] for load in loads]
                    candidate[i], candidate[j] = a_load, b_load
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


def _improve_scenarios(parts, loads, costs):
    # A large suite may need to share a part with a complementary scenario
    # vector. Pair/two-for-one swaps cannot always replace many small suites.
    # Screen the original start and eight fixed co-location starts cheaply;
    # only the best screened start receives the more expensive exchanges.
    order = sorted(costs, key=lambda name: (-max(costs[name]), name))
    candidates = [(parts, loads)]
    candidates.extend(_greedy_scenarios(costs, len(parts), (order[0], partner))
                      for partner in order[1:9])
    best_score, best_parts, best_loads = None, None, None
    for candidate_parts, candidate_loads in candidates:
        for _ in range(2):
            _swap_scenarios(candidate_parts, candidate_loads, costs)
        score = tuple(sorted((ms for load in candidate_loads for ms in load), reverse=True))
        if best_score is None or score < best_score:
            best_score, best_parts, best_loads = score, candidate_parts, candidate_loads
    parts[:], loads[:] = best_parts, best_loads
    # Fixed work: four exchanges among 16 candidates per part, never convergence.
    # No random seed, suite-name or budget special case.
    for _ in range(4):
        _exchange_scenarios(parts, loads, costs)
        _swap_scenarios(parts, loads, costs)


def _greedy_scenarios(costs, count, colocated=()):
    parts = [set() for _ in range(count)]
    loads = [[0] * len(next(iter(costs.values()))) for _ in range(count)]
    for name in colocated:
        parts[0].add(name)
        loads[0] = [a + b for a, b in zip(loads[0], costs[name])]
    for name in sorted(costs, key=lambda n: (-max(costs[n]), n)):
        if name in parts[0]:
            continue
        candidates = [[a + b for a, b in zip(load, costs[name])] for load in loads]
        index = min(range(count), key=lambda i: (max(candidates[i]), sum(candidates[i]), i))
        parts[index].add(name)
        loads[index] = candidates[index]
    return parts, loads


def _scenario_owners(suites, count, profiles):
    costs = {s.name: [p.get(s.name, 1000) for p in profiles] for s in suites}
    parts, loads = _greedy_scenarios(costs, count)
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
    legacy = TIMINGS.read_bytes().replace(b'\r\n', b'\n')
    addition = ADDED_EVIDENCE.read_bytes().replace(b'\r\n', b'\n')
    r14 = ADDED_R14_EVIDENCE.read_bytes().replace(b'\r\n', b'\n')
    receipts = ADDED_RECEIPTS.read_bytes().replace(b'\r\n', b'\n')
    return hashlib.sha256(b'\0'.join((legacy, addition, r14, receipts))).hexdigest()
