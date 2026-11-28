#!/usr/bin/env python3
"""Finite independent history model for U476 research declarations.

This model operates on documents and a monotonic allocator. It imports no
candidate, parser, or history helper. It does not claim a real project owner,
World history transaction, scenario persistence, or native proof lease.
"""
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess


MAX_KEY = 4294967295
ACTIONS = ('add', 'clear', 'undo', 'redo', 'cancel', 'reopen')
BATCH_SIZE = 64


def member(source):
    def pin(text):
        return hashlib.sha256(text.encode()).hexdigest()
    return {'kind': 'live', 'projectScope': 'project-research-A',
            'scenario': 'scenario-selected-A',
            'timber': {'kind': 'timber', 'id': source, 'mark': 'timber-life-' + str(source)},
            'placement': {'kind': 'placement', 'id': 0, 'mark': 'placement-life-0'},
            'definitionPin': {'timber': pin('definition-' + str(source)),
                              'placement': pin('placement-definition')},
            'effectivePin': {'timber': pin('effective-' + str(source)),
                             'placement': pin('placement-effective')}}


def empty_document(next_key=1):
    return {'schema': 'U476-study-document/1', 'projectScope': 'project-research-A',
            'scenario': 'scenario-selected-A', 'nextItemKey': next_key,
            'items': [], 'excluded': []}


def one_item_document():
    result = empty_document(2)
    result['items'] = [{'itemKey': 1, 'members': [member(0)],
                        'representative': ['live', None, 'timber', 0, 'placement', 0]}]
    return result


def build_case(name, labels, initial=None):
    document = copy.deepcopy(initial if initial is not None else empty_document())
    opened = copy.deepcopy(document)
    allocator = document['nextItemKey']
    past, future, operations, expected = [], [], [], []
    revision = 0

    def view():
        return {'document': copy.deepcopy(document), 'revision': revision,
                'undoDepth': len(past), 'redoDepth': len(future),
                'dirty': document != opened, 'needsVerification': True}

    first = view()
    for label in labels:
        prior = copy.deepcopy(document)
        changed, allocated, succeeded, action_result = False, [], True, None
        if label in ('add', 'cancel', 'clear', 'noop', 'duplicate-key', 'retired-key'):
            draft = copy.deepcopy(document)
            if label in ('add', 'cancel'):
                occupied = {m['timber']['id'] for item in draft['items'] for m in item['members']}
                source = next(value for value in range(5) if value not in occupied)
                draft['items'].append({'itemKey': None, 'members': [member(source)],
                                       'representative': ['live', None, 'timber', source, 'placement', 0]})
            elif label == 'clear':
                draft['items'] = []
            elif label == 'duplicate-key':
                assert draft['items'], 'U476_HISTORY_FIXTURE_DUPLICATE_PRECONDITION'
                draft['items'].append(copy.deepcopy(draft['items'][0]))
            elif label == 'retired-key':
                assert not draft['items'] and allocator > 1, 'U476_HISTORY_FIXTURE_RETIRED_PRECONDITION'
                draft['items'] = copy.deepcopy(one_item_document()['items'])
            if label == 'cancel':
                operations.append({'op': 'cancel', 'document': draft})
                action_result = False
            else:
                operations.append({'op': 'commit', 'document': draft})
                if label in ('duplicate-key', 'retired-key') or (label == 'add' and allocator == 0):
                    succeeded = False
                else:
                    committed = copy.deepcopy(draft)
                    if label == 'add':
                        allocated = [allocator]
                        committed['items'][-1]['itemKey'] = allocator
                        allocator = 0 if allocator == MAX_KEY else allocator + 1
                    committed['nextItemKey'] = allocator
                    committed['items'].sort(key=lambda item: item['itemKey'])
                    changed = committed != prior
                    if changed:
                        past.append(prior)
                        future.clear()
                        document = committed
                        revision += 1
                    action_result = {'changed': changed, 'allocatedKeys': allocated}
        elif label in ('undo', 'redo'):
            operations.append({'op': label})
            source_stack, destination_stack = (past, future) if label == 'undo' else (future, past)
            action_result = bool(source_stack)
            if source_stack:
                destination_stack.append(copy.deepcopy(document))
                document = source_stack.pop()
                document['nextItemKey'] = allocator
                revision += 1
        elif label == 'reopen':
            operations.append({'op': 'reopen'})
            past.clear()
            future.clear()
            revision = 0
            opened = copy.deepcopy(document)
            action_result = True
        else:
            raise AssertionError('U476_HISTORY_UNKNOWN_LABEL:' + label)
        expected.append({'op': operations[-1]['op'], 'ok': succeeded,
                         'result': action_result, 'view': view()})
    return {'name': name, 'labels': list(labels),
            'input': {'document': first['document'], 'operations': operations},
            'expected': {'initial': first, 'steps': expected, 'final': view()}}


def inspect(case, actual):
    want = case['expected']
    assert actual['initial'] == want['initial'], 'U476_HISTORY_INITIAL:' + case['name']
    assert len(actual['steps']) == len(want['steps']), 'U476_HISTORY_STEP_COUNT:' + case['name']
    for index, (received, expected) in enumerate(zip(actual['steps'], want['steps'])):
        suffix = case['name'] + ':' + str(index)
        assert received['op'] == expected['op'], 'U476_HISTORY_OPERATION:' + suffix
        assert received['ok'] is expected['ok'], 'U476_HISTORY_ACCEPTANCE:' + suffix
        assert received['view'] == expected['view'], 'U476_HISTORY_STATE:' + suffix
        if not expected['ok']:
            assert type(received.get('error')) is str and received['error'], 'U476_HISTORY_ERROR_REQUIRED:' + suffix
        elif expected['op'] == 'commit':
            for field in ('changed', 'allocatedKeys'):
                assert received['result'][field] == expected['result'][field], 'U476_HISTORY_COMMIT:' + field + ':' + suffix
        else:
            assert received['result'] is expected['result'], 'U476_HISTORY_RESULT:' + suffix
    assert actual['final'] == want['final'], 'U476_HISTORY_FINAL:' + case['name']


def run(candidate, destination):
    destination.mkdir(parents=True, exist_ok=True)
    cases = [build_case('enumerated-' + '-'.join(labels), labels)
             for size in range(4) for labels in itertools.product(ACTIONS, repeat=size)]
    assert len(cases) == 259, 'U476_HISTORY_UNIVERSE_SIZE'
    named = [
        build_case('issued-key-not-reused-after-undo', ('add', 'undo', 'add')),
        build_case('issued-key-not-reused-after-delete', ('add', 'clear', 'add')),
        build_case('highwater-survives-reopen', ('add', 'undo', 'reopen', 'add')),
        build_case('empty-noop-and-cancel', ('noop', 'cancel', 'noop')),
        build_case('undo-to-open-bytes-dirty-clears', ('clear', 'undo'), one_item_document()),
        build_case('duplicate-key-atomic-rejection', ('duplicate-key', 'undo'), one_item_document()),
        build_case('retired-key-cannot-be-reintroduced', ('clear', 'retired-key'), one_item_document()),
        build_case('exhaustion-survives-undo-and-reopen', ('add', 'undo', 'reopen', 'add'), empty_document(MAX_KEY)),
        build_case('exhausted-allocator-allows-noop', ('noop', 'cancel'), empty_document(0)),
    ]
    cases += named
    records = []
    for offset in range(0, len(cases), BATCH_SIZE):
        batch = cases[offset:offset + BATCH_SIZE]
        command = ['node', str(candidate), 'history-batch']
        try:
            process = subprocess.run(command, input=json.dumps([case['input'] for case in batch]),
                                     text=True, encoding='utf-8', capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('U476_HISTORY_INFRASTRUCTURE_TIMEOUT') from error
        if process.returncode != 0:
            raise RuntimeError('U476_HISTORY_INFRASTRUCTURE_EXIT:' + str(process.returncode)
                               + ':' + process.stderr[-2000:])
        try:
            answers = json.loads(process.stdout)
        except ValueError as error:
            raise RuntimeError('U476_HISTORY_INFRASTRUCTURE_JSON') from error
        if not isinstance(answers, list) or len(answers) != len(batch):
            raise RuntimeError('U476_HISTORY_INFRASTRUCTURE_BATCH_LENGTH')
        for case, answer in zip(batch, answers):
            inspect(case, answer)
            records.append({'name': case['name'], 'labels': case['labels'],
                            'input': case['input'], 'actual': answer})
    raw = (json.dumps(records, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    (destination / 'history-cases.json.gz').write_bytes(gzip.compress(raw, mtime=0))
    summary = {'researchOnly': True, 'exhaustiveSequences': 259, 'namedSequences': len(named),
               'totalSequences': len(cases), 'maxEnumeratedSteps': 3,
               'actions': list(ACTIONS), 'batchSize': BATCH_SIZE, 'childTimeoutSeconds': 30,
               'checkedOperations': sum(len(case['labels']) for case in cases),
               'rawBytes': len(raw), 'rawSha256': hashlib.sha256(raw).hexdigest(),
               'allMatchedIndependentModel': True}
    (destination / 'history-summary.json').write_text(
        json.dumps(summary, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return summary
