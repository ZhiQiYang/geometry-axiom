#!/usr/bin/env python3
"""U476 independent finite-study checker, revised from U476 recovery v2.

Only stdlib and supplied study observations are used. This is not a native
receipt authority, attachment parser, or production cutting-plan/2 validator.
There is no import/call of the candidate or shared grouping/eligibility helper.
"""
import json
import sys


class Rejected(AssertionError):
    pass


def _same_json(left, right):
    """Python bool/int equality must not accept a forged JSON scalar type."""
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(_same_json(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    return left == right


def _root_evidence(fact):
    """Independent shape/pair checks; do not infer a node kind from its key."""
    native = fact.get('native', {})
    nodes = native.get('rootNodes')
    if type(nodes) is not dict or set(nodes) != {'timber', 'placement'}:
        return False
    for role in ('timber', 'placement'):
        root, node = fact.get(role), nodes.get(role)
        if type(root) is not dict or type(node) is not dict:
            return False
        value = root.get('id')
        if type(value) is not int or not 0 <= value <= 4294967295:
            return False
        if root.get('kind') != role or node.get('kind') != role:
            return False
        if type(node.get('id')) is not int or node['id'] != value:
            return False
        if node.get('key') != role + ':' + str(value):
            return False
    return (nodes['timber'].get('placed') is True
            and type(nodes['timber'].get('surface')) is int
            and nodes['timber']['surface'] == fact['placement']['id'])


def _pin_evidence(value):
    if type(value) is str:
        return bool(value)
    return (type(value) is dict
            and set(value) == {'timber', 'placement'}
            and all(type(value[root]) is str and bool(value[root])
                    for root in ('timber', 'placement')))


def inspect(data, answer):
    def require(condition, name):
        if not condition:
            raise Rejected(name)
    require(data.get('studySchema') == 'U476-facts/1', 'U476_CHECK_INPUT_SCHEMA')
    require(answer.get('studySchema') == 'U476-result/1' and answer.get('researchOnly') is True, 'U476_CHECK_RESEARCH_BOUNDARY')
    facts, declarations, excluded = data['representations'], data['declarations']['items'], data['declarations']['excluded']
    problems = set()
    def problem(severity, code, ref=''):
        problems.add((severity, code, ref))
    if len({r['ref'] for r in facts}) != len(facts):
        problem('INVALID', 'DUPLICATE_INPUT_FACT')
    current_keys = [(r['timber']['kind'], r['timber']['id'], r['placement']['kind'], r['placement']['id']) for r in data['current']]
    if len(set(current_keys)) != len(current_keys):
        problem('INVALID', 'DUPLICATE_INPUT_FACT')
    if len(declarations) > 64 or len(facts) > 128 or len(data['context']['modelPins']) > 8:
        problem('INVALID', 'CAPACITY')
    if data['endContext'] != data['context']:
        problem('INCOMPLETE', 'READ_CONTEXT_CHANGED')
    keys = [d['itemKey'] for d in declarations]
    if len(set(keys)) != len(keys) or any(type(k) is not int or k < 1 or k > 4294967295 for k in keys):
        problem('INVALID', 'ITEM_KEY')
    membership = [(ref, d['itemKey']) for d in declarations for ref in d['members']] + [(ref, 'excluded') for ref in excluded]
    refs = [r['ref'] for r in facts]
    for ref, _ in membership:
        if ref not in refs or sum(other == ref for other, _ in membership) != 1:
            problem('INVALID', 'REPRESENTATION_PARTITION', ref)
    for d in declarations:
        if not d['members'] or d['representative'] not in d['members']:
            problem('INVALID', 'REPRESENTATIVE')
    for fact in facts:
        ref = fact['ref']
        if ref in excluded:
            continue
        if not any(member == ref for member, _ in membership):
            problem('INCOMPLETE', 'ITEM_DECLARATION_REQUIRED', ref)
        if any(fact[k] != data['context'][k] for k in ('projectScope', 'scenario')):
            problem('UNSUPPORTED', 'CONTEXT_OUTSIDE_SCOPE', ref)
        if fact['kind'] not in ['live', 'model'] or fact['category'] != 'ordinary-d7':
            problem('UNSUPPORTED', 'REPRESENTATION_KIND', ref)
        if fact['timber']['kind'] != 'timber' or fact['placement']['kind'] != 'placement' or any(type(fact[k]['id']) is not int or fact[k]['id'] < 0 or fact[k]['id'] > 4294967295 for k in ('timber', 'placement')):
            problem('INVALID', 'TYPED_ROOT', ref)
        if any(fact[k]['mark'] is None for k in ('timber', 'placement')):
            problem('INCOMPLETE', 'SOURCE_IDENTITY_UNKNOWN', ref)
        if not _root_evidence(fact):
            problem('INCOMPLETE', 'SOURCE_TYPED_ROOT_UNPROVEN', ref)
        if fact['native']['complete'] is not True:
            problem('INCOMPLETE', 'NATIVE_READ_INCOMPLETE', ref)
        if any(not _pin_evidence(fact['native'][axis]) for axis in ('definitionPin', 'effectivePin')):
            problem('INCOMPLETE', 'SOURCE_PIN_MISSING', ref)
        if any(k not in fact['native']['content'] or fact['native']['content'][k] is None for k in ('material', 'direction', 'surface', 'placement', 'supports', 'typedSources')):
            problem('INCOMPLETE', 'SOURCE_DETAIL_MISSING', ref)
        supports = fact['native']['content'].get('supports')
        proved = False
        if type(supports) is list and len(supports) == 2:
            proved = all(type(s) is dict and s.get('kind') in ['timber', 'placement', 'boundary', 'beam', 'column'] and type(s.get('id')) is int and 0 <= s['id'] <= 4294967295 and bool(s.get('faceSelector')) for s in supports)
        if type(supports) is dict:
            proved = all(type(supports.get(side)) is dict and supports[side].get('status') == 'exact' and type(supports[side].get('relation')) is dict and type(supports[side]['relation'].get('source')) is dict and supports[side]['relation']['source'].get('kind') in ['timber', 'placement', 'boundary', 'beam', 'column'] and type(supports[side]['relation']['source'].get('id')) is int and 0 <= supports[side]['relation']['source']['id'] <= 4294967295 for side in ['start', 'finish'])
        if not proved:
            problem('INCOMPLETE', 'SOURCE_SUPPORT_UNPROVEN', ref)
        model = fact['model']
        if fact['kind'] == 'model':
            if model is None or (model['sourceKind'], model['inputOutcome'], model['resultOutcome']) != ('ordinary-plan', 'COMPLETE', 'COMPLETE'):
                problem('UNSUPPORTED', 'MODEL_DUAL_VALIDATION', ref)
            elif fact['timber']['id'] not in model['inputTimbers']:
                problem('INVALID', 'MODEL_INPUT_ROOT', ref)
            if model is not None and data['context']['modelPins'].get(model['recordId']) != {'owner': model['owner'], 'recordSha256': model['recordSha256'], 'readPin': fact['native']['readPin']}:
                problem('INCOMPLETE', 'MODEL_RECORD_CHANGED', ref)
        if fact['kind'] == 'live' and fact['native']['readPin'] != data['context']['liveReadPin']:
            problem('INCOMPLETE', 'MIXED_LIVE_READ', ref)
        candidates = [r for r in data['current'] if r['timber']['kind'] == fact['timber']['kind'] and r['timber']['id'] == fact['timber']['id'] and r['placement']['kind'] == fact['placement']['kind'] and r['placement']['id'] == fact['placement']['id']]
        if not candidates:
            problem('INCOMPLETE', 'SOURCE_ABSENT', ref)
        else:
            now = candidates[-1]
            if now['native']['complete'] is not True or any(not _pin_evidence(now['native'][axis]) for axis in ('definitionPin', 'effectivePin')) or not _root_evidence(now) or now['native']['readPin'] != data['context']['liveReadPin']:
                problem('INCOMPLETE', 'CURRENT_SOURCE_INCOMPLETE', ref)
            if any(fact[k] != now[k] for k in ('projectScope', 'scenario', 'timber', 'placement')):
                problem('INCOMPLETE', 'SOURCE_REPLACED', ref)
            if any(fact['native'][k] != now['native'][k] for k in ('definitionPin', 'effectivePin', 'content')):
                problem('INCOMPLETE', 'SOURCE_CONTENT_CHANGED', ref)
    for d in declarations:
        members = [next((r for r in facts if r['ref'] == ref), None) for ref in d['members']]
        members = [r for r in members if r is not None]
        for r in members[1:]:
            if any(r[k] != members[0][k] for k in ('projectScope', 'scenario', 'timber', 'placement')):
                problem('INCOMPLETE', 'MANUAL_GROUP_SOURCE_MISMATCH', r['ref'])
    for i, a in enumerate(facts):
        if a['ref'] in excluded:
            continue
        left = next((key for ref, key in membership if ref == a['ref']), 'pending:' + a['ref'])
        for b in facts[i + 1:]:
            if b['ref'] in excluded:
                continue
            right = next((key for ref, key in membership if ref == b['ref']), 'pending:' + b['ref'])
            if left != right and all(a[k] == b[k] for k in ('projectScope', 'scenario', 'timber', 'placement')):
                problem('INCOMPLETE', 'DUPLICATE_SOURCE_NEEDS_REVIEW')
    status = 'EMPTY' if all(r['ref'] in excluded for r in facts) else 'COMPLETE'
    for severity in ('INCOMPLETE', 'UNSUPPORTED', 'INVALID'):
        if any(p[0] == severity for p in problems):
            status = severity
    require(answer['status'] == status, 'U476_CHECK_STATUS:' + status)
    require({(d['severity'], d['code'], d['ref']) for d in answer['diagnostics']} == problems, 'U476_CHECK_DIAGNOSTICS')
    require(_same_json(answer['rawRows'], sorted(facts, key=lambda r: r['ref'])), 'U476_CHECK_RAW_REPRESENTATIONS')
    require(answer['excluded'] == sorted(excluded), 'U476_CHECK_EXPLICIT_EXCLUSIONS')
    book = answer['accounting']
    require(all(type(book[key]) in (int, float) for key in ('rawRepresentedLengthMm', 'excludedLengthMm', 'includedRepresentedLengthMm')), 'U476_CHECK_ACCOUNTING_TYPE')
    raw = sum(r['native']['content']['L'] for r in facts)
    omitted = sum(r['native']['content']['L'] for r in facts if r['ref'] in excluded)
    require(book['rawRepresentedLengthMm'] == raw, 'U476_CHECK_RAW_LENGTH')
    require(book['excludedLengthMm'] == omitted, 'U476_CHECK_EXCLUDED_LENGTH')
    require(book['includedRepresentedLengthMm'] == raw - omitted, 'U476_CHECK_INCLUDED_LENGTH')
    if status not in ('COMPLETE', 'EMPTY'):
        require(answer['items'] == [] and answer['itemCount'] is None and book['physicalItemLengthMm'] is None and book['removedAliasLengthMm'] is None, 'U476_CHECK_NO_PARTIAL_TAKEOFF')
        return {'accepted': True, 'status': status}
    if status == 'EMPTY':
        require(answer['items'] == [] and type(answer['itemCount']) in (int, float) and answer['itemCount'] == 0 and type(book['physicalItemLengthMm']) in (int, float) and book['physicalItemLengthMm'] == 0 and type(book['removedAliasLengthMm']) in (int, float) and book['removedAliasLengthMm'] == 0, 'U476_CHECK_EMPTY')
        return {'accepted': True, 'status': status}
    require(_same_json([r['itemKey'] for r in answer['items']], sorted(keys)), 'U476_CHECK_ITEM_PARTITION')
    require(type(answer['itemCount']) in (int, float), 'U476_CHECK_COUNT_TYPE')
    require(answer['itemCount'] == len(declarations), 'U476_CHECK_COUNT')
    require(all(type(book[key]) in (int, float) for key in ('physicalItemLengthMm', 'removedAliasLengthMm')), 'U476_CHECK_ACCOUNTING_TYPE')
    used, physical, removed = [], 0, 0
    for row in answer['items']:
        declaration = next(d for d in declarations if d['itemKey'] == row['itemKey'])
        require(row['members'] == sorted(declaration['members']), 'U476_CHECK_EXPLICIT_GROUP')
        require(row['representative'] == declaration['representative'], 'U476_CHECK_REPRESENTATIVE')
        source = next(f for f in facts if f['ref'] == row['representative'])
        identity = [source['projectScope'], source['scenario'], source['timber']['kind'], source['timber']['id'], source['timber']['mark'], source['placement']['kind'], source['placement']['id'], source['placement']['mark']]
        require(_same_json(row['sourceIdentity'], identity), 'U476_CHECK_SOURCE_IDENTITY')
        for field in ('A', 'B', 'L', 'material'):
            require(_same_json(row[field], source['native']['content'][field]), 'U476_CHECK_NATIVE_MEASUREMENT:' + field)
        require([t['ref'] for t in row['provenance']] == row['members'], 'U476_CHECK_TRACE_COVERAGE')
        for t in row['provenance']:
            fact = next(f for f in facts if f['ref'] == t['ref'])
            for field in ('ref', 'kind', 'projectScope', 'scenario', 'timber', 'placement'):
                require(_same_json(t[field], fact[field]), 'U476_CHECK_TRACE:' + field)
            for field in ('readPin', 'definitionPin', 'effectivePin', 'content'):
                require(_same_json(t[field], fact['native'][field]), 'U476_CHECK_TRACE:' + field)
            model = fact['model']
            require(t['modelRecordId'] == (None if model is None else model['recordId']), 'U476_CHECK_TRACE:modelRecordId')
            require(t['modelRecordSha256'] == (None if model is None else model['recordSha256']), 'U476_CHECK_TRACE:modelRecordSha256')
        used.extend(row['members'])
        physical += source['native']['content']['L']
        removed += sum(next(f for f in facts if f['ref'] == ref)['native']['content']['L'] for ref in row['members'] if ref != row['representative'])
    require(sorted(used) == sorted(r['ref'] for r in facts if r['ref'] not in excluded), 'U476_CHECK_EXACT_PARTITION')
    require(book['physicalItemLengthMm'] == physical, 'U476_CHECK_PHYSICAL_LENGTH')
    require(book['removedAliasLengthMm'] == removed, 'U476_CHECK_REMOVED_ALIAS_LENGTH')
    require(raw == omitted + physical + removed, 'U476_CHECK_ACCOUNTING')
    return {'accepted': True, 'status': status}


if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            envelope = json.load(sys.stdin)
            result = inspect(envelope['input'], envelope['output'])
        elif len(sys.argv) == 3:
            with open(sys.argv[1], encoding='utf-8') as f:
                data = json.load(f)
            with open(sys.argv[2], encoding='utf-8') as f:
                result = inspect(data, json.load(f))
        else:
            raise ValueError('usage: check.py [facts.json proposed-result.json]')
    except Rejected as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print('U476_CHECKER_INPUT_OR_RUNTIME_ERROR:' + type(error).__name__ + ':' + str(error),
              file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
