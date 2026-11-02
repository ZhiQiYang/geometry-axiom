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
    weights = timing_weights() if weights is None else weights
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
