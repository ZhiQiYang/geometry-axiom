#!/usr/bin/env python3
"""Bounded U476 study scan against an external JavaScript candidate.

The checker never imports candidate code. Synthetic observations prove only
the finite set/count problem; native acquisition and project authority remain
outside this research schema. All child invocations have an explicit timeout.
"""
import argparse
import collections
import contextlib
import copy
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

import check
import fixtures


BATCH_SIZE = 128
CHILD_TIMEOUT_SECONDS = 30


def invoke(candidate, inputs, mode='batch'):
    command = ['node', str(candidate), mode]
    try:
        process = subprocess.run(command, input=json.dumps(inputs), text=True,
                                 encoding='utf-8', capture_output=True,
                                 timeout=CHILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('U476_INFRASTRUCTURE_TIMEOUT:' + repr(command)) from error
    if process.returncode != 0:
        raise RuntimeError('U476_INFRASTRUCTURE_CHILD_EXIT:' + str(process.returncode)
                           + ':' + process.stderr[-4000:])
    try:
        answers = json.loads(process.stdout)
    except (ValueError, TypeError) as error:
        raise RuntimeError('U476_INFRASTRUCTURE_CHILD_JSON') from error
    if not isinstance(answers, list) or len(answers) != len(inputs):
        raise RuntimeError('U476_INFRASTRUCTURE_CHILD_BATCH_LENGTH')
    return answers


@contextlib.contextmanager
def records(path):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8', newline='\n') as stream:
                yield stream


def write_gzip(path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    path.write_bytes(gzip.compress(raw, mtime=0))


def assignments(size, prefix=(), largest=0):
    """All canonical partitions, plus independent excluded/undeclared rows."""
    if len(prefix) == size:
        yield prefix
        return
    for allocation in ('E', 'U', *range(1, largest + 2)):
        next_largest = max(largest, allocation) if type(allocation) is int else largest
        yield from assignments(size, prefix + (allocation,), next_largest)


def arithmetic(sources, lengths, allocation):
    """Third, closed finite-domain expectation; no candidate/checker calls."""
    selected = [(source, group) for source, group in zip(sources, allocation) if group != 'E']
    if not selected:
        return 'EMPTY', 0, 0
    if any(group == 'U' for _, group in selected):
        return 'INCOMPLETE', None, None
    physical_sources = set(source for source, _ in selected)
    declared_groups = set(group for _, group in selected)
    # A bijection must hold between selected physical sources and item groups.
    if any(len({source for source, at in selected if at == group}) != 1
           for group in declared_groups):
        return 'INCOMPLETE', None, None
    if any(len({group for at, group in selected if at == source}) != 1
           for source in physical_sources):
        return 'INCOMPLETE', None, None
    return 'COMPLETE', len(physical_sources), sum(lengths[source] for source in physical_sources)


def generated_cases():
    for size in range(5):
        for sources in itertools.product((0, 1), repeat=size):
            for lengths in itertools.product((1, 2), repeat=2):
                for allocation in assignments(size):
                    yield (size, sources, lengths, allocation,
                           fixtures.make(sources, lengths, allocation))


def reject_wrong_outputs(candidate, destination):
    complete_facts = fixtures.named('same-source-explicit')
    correct = invoke(candidate, [complete_facts])[0]
    check.inspect(complete_facts, correct)
    corruptions = []
    changed = copy.deepcopy(correct)
    changed['items'][0]['L'] += 1
    corruptions.append(('changed-native-length', complete_facts, changed,
                        'U476_CHECK_NATIVE_MEASUREMENT:L'))
    changed = copy.deepcopy(correct)
    changed['items'][0]['members'].pop()
    corruptions.append(('omitted-alias', complete_facts, changed,
                        'U476_CHECK_EXPLICIT_GROUP'))
    changed = copy.deepcopy(correct)
    changed['itemCount'] += 1
    corruptions.append(('invented-count', complete_facts, changed, 'U476_CHECK_COUNT'))
    changed = copy.deepcopy(correct)
    changed['accounting']['physicalItemLengthMm'] += 1
    corruptions.append(('wrong-physical-total', complete_facts, changed,
                        'U476_CHECK_PHYSICAL_LENGTH'))
    corruptions.append(('forged-complete', fixtures.named('same-source-unresolved'),
                        copy.deepcopy(correct), 'U476_CHECK_STATUS:INCOMPLETE'))
    corruptions.append(('undeclared-auto-merge', fixtures.named('same-source-undeclared'),
                        copy.deepcopy(correct), 'U476_CHECK_STATUS:INCOMPLETE'))
    unit_facts = fixtures.make(lengths=(1, 1))
    unit_answer = invoke(candidate, [unit_facts])[0]
    check.inspect(unit_facts, unit_answer)
    changed = copy.deepcopy(unit_answer)
    changed['items'][0]['L'] = True
    corruptions.append(('boolean-length-is-not-one-mm', unit_facts, changed,
                        'U476_CHECK_NATIVE_MEASUREMENT:L'))
    changed = copy.deepcopy(unit_answer)
    changed['itemCount'] = True
    corruptions.append(('boolean-count-is-not-one-item', unit_facts, changed,
                        'U476_CHECK_COUNT_TYPE'))
    results = []
    for name, data, answer, expected in corruptions:
        try:
            check.inspect(data, answer)
        except check.Rejected as error:
            if str(error) != expected:
                raise AssertionError('U476_CHECKER_NEGATIVE_WRONG_REASON:' + name + ':' + str(error))
            results.append({'name': name, 'rejected': expected, 'input': data, 'proposed': answer})
        else:
            raise AssertionError('U476_CHECKER_ACCEPTED_CORRUPTION:' + name)
    write_gzip(destination / 'checker-negative-cases.json.gz', results)
    return len(results)


def run(candidate, destination, with_history=True):
    destination.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    named = [{'name': name, 'input': fixtures.named(name)} for name in fixtures.NAMES]
    answers = invoke(candidate, [case['input'] for case in named])
    for case, answer in zip(named, answers):
        try:
            checked = check.inspect(case['input'], answer)
        except check.Rejected as error:
            raise AssertionError('U476_SCAN_NAMED:' + case['name'] + ':' + str(error)) from error
        case.update(output=answer, checker=checked)
    write_gzip(destination / 'named-cases.json.gz', named)
    rejected_count = reject_wrong_outputs(candidate, destination)

    counts, sizes = collections.Counter(), collections.Counter()
    metamorphic_counts = collections.Counter()
    batch, transforms = [], []
    total = 0

    def flush_transforms():
        if not transforms:
            return
        portion = transforms[:BATCH_SIZE]
        derived = invoke(candidate, [entry['input'] for entry in portion])
        for entry, answer in zip(portion, derived):
            check.inspect(entry['input'], answer)
            original = entry['original']
            if entry['kind'] == 'order':
                assert answer == original, 'U476_SCAN_ORDER_INVARIANCE'
            elif entry['kind'] == 'revoke':
                assert answer['status'] == 'INCOMPLETE', 'U476_SCAN_REVOKE_UNRESOLVED'
                assert answer['rawRows'] == original['rawRows'], 'U476_SCAN_REVOKE_RAW_LIST'
                assert answer['accounting']['rawRepresentedLengthMm'] == original['accounting']['rawRepresentedLengthMm'], 'U476_SCAN_REVOKE_RAW_LENGTH'
            else:
                assert answer['accounting'] == original['accounting'], 'U476_SCAN_REPRESENTATIVE_ACCOUNTING'
                assert answer['itemCount'] == original['itemCount'], 'U476_SCAN_REPRESENTATIVE_COUNT'
            metamorphic_counts[entry['kind']] += 1
        del transforms[:len(portion)]

    def flush(stream):
        nonlocal total
        if not batch:
            return
        derived = invoke(candidate, [entry[4] for entry in batch])
        for (size, sources, lengths, allocation, data), answer in zip(batch, derived):
            check.inspect(data, answer)
            status, count, length = arithmetic(sources, lengths, allocation)
            assert answer['status'] == status, 'U476_SCAN_ANALYTIC_STATUS'
            assert answer['itemCount'] == count, 'U476_SCAN_ANALYTIC_COUNT'
            assert answer['accounting']['physicalItemLengthMm'] == length, 'U476_SCAN_ANALYTIC_LENGTH'
            total += 1
            counts[status] += 1
            sizes[size] += 1
            stream.write(json.dumps({'case': total, 'n': size, 'sources': sources,
                                     'sourceLengthsMm': lengths, 'allocation': allocation,
                                     'status': status, 'itemCount': count,
                                     'accounting': answer['accounting']}, sort_keys=True) + '\n')
            if status != 'COMPLETE':
                continue
            reordered = copy.deepcopy(data)
            for field in ('representations', 'current'):
                reordered[field].reverse()
            for field in ('items', 'excluded'):
                reordered['declarations'][field].reverse()
            for item in reordered['declarations']['items']:
                item['members'].reverse()
            transforms.append({'kind': 'order', 'input': reordered, 'original': answer})
            if any(len(item['members']) > 1 for item in data['declarations']['items']):
                revoked = copy.deepcopy(data)
                revoked['declarations']['items'] = [
                    {'itemKey': index + 1, 'members': [row['ref']], 'representative': row['ref']}
                    for index, row in enumerate(revoked['representations'])
                    if row['ref'] not in revoked['declarations']['excluded']]
                transforms.append({'kind': 'revoke', 'input': revoked, 'original': answer})
                representative = copy.deepcopy(data)
                for item in representative['declarations']['items']:
                    item['representative'] = item['members'][-1]
                transforms.append({'kind': 'representative', 'input': representative, 'original': answer})
            if len(transforms) >= BATCH_SIZE:
                flush_transforms()
        batch.clear()

    with records(destination / 'scan-cases.jsonl.gz') as stream:
        for entry in generated_cases():
            batch.append(entry)
            if len(batch) == BATCH_SIZE:
                flush(stream)
        flush(stream)
    flush_transforms()
    assert total == 11036, 'U476_SCAN_UNIVERSE_SIZE'
    raw = gzip.decompress((destination / 'scan-cases.jsonl.gz').read_bytes())
    summary = {
        'studySchema': 'U476-scan/1', 'researchOnly': True,
        'candidate': str(candidate), 'exhaustiveCases': total,
        'byRepresentationCount': dict(sizes), 'statusCounts': dict(counts),
        'namedCases': len(named), 'maliciousOutputsRejected': rejected_count,
        'metamorphicChecks': dict(metamorphic_counts), 'checkerAcceptedAll': True,
        'batchSize': BATCH_SIZE, 'childTimeoutSeconds': CHILD_TIMEOUT_SECONDS,
        'rawCasesBytes': len(raw), 'rawCasesSha256': hashlib.sha256(raw).hexdigest(),
        'finiteDomain': {'representationCount': [0, 1, 2, 3, 4], 'sourceIds': [0, 1],
                         'sourceLengthsMm': [1, 2],
                         'declarations': 'all canonical partitions, excluded, undeclared'}}
    if with_history:
        import history_scan
        summary['history'] = history_scan.run(candidate, destination / 'history')
    summary['durationSeconds'] = round(time.monotonic() - started, 6)
    (destination / 'scan-summary.json').write_text(
        json.dumps(summary, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, sort_keys=True))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--bounded', action='store_true', required=True)
    args = parser.parse_args()
    try:
        run(args.candidate.resolve(), args.out.resolve())
    except (AssertionError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
