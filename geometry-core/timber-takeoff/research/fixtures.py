"""U476 finite study observations, derived from U476 test ideas.

The flags here describe synthetic observations. They are never native proof.
The real-native adapter must independently validate its input artifacts.
"""
import copy
import hashlib
import json
import sys


def pin(label):
    return hashlib.sha256(label.encode('utf-8')).hexdigest()


def native_root(source, length):
    return {'projectScope': 'project-research-A', 'scenario': 'scenario-selected-A',
            'timber': {'kind': 'timber', 'id': source, 'mark': 'timber-life-' + str(source)},
            'placement': {'kind': 'placement', 'id': 0, 'mark': 'placement-life-0'},
            'native': {'readPin': pin('live-read-7'), 'complete': True,
                       'definitionPin': {'timber': pin('definition-source-' + str(source)),
                                         'placement': pin('definition-placement-0')},
                       'effectivePin': {'timber': pin('effective-source-' + str(source) + '-length-' + str(length)),
                                        'placement': pin('effective-placement-0')},
                       'content': {'A': 27, 'B': 33, 'L': length,
                                   'material': {'kind': 'material', 'id': 0, 'version': 1, 'fingerprint': pin('material-0-v1')},
                                   'direction': [1, 0, 0], 'surface': {'kind': 'placement', 'id': 0},
                                   'placement': {'kind': 'placement', 'id': 0, 'offset': 0},
                                   'supports': [{'kind': 'boundary', 'id': 1, 'faceSelector': 'left'}, {'kind': 'boundary', 'id': 1, 'faceSelector': 'right'}],
                                   'typedSources': {'A': {'kind': 'spec', 'id': 0, 'field': 'A', 'content': {'value': 27}},
                                                    'B': {'kind': 'spec', 'id': 0, 'field': 'B', 'content': {'value': 33}},
                                                    'ends': [{'kind': 'boundary', 'id': 1, 'faceSelector': 'left', 'content': {'offset': 0}},
                                                             {'kind': 'boundary', 'id': 1, 'faceSelector': 'right', 'content': {'offset': length}}]}}}}


def make(sources=(0, 0), lengths=(1000, 1000), allocation=(1, 1)):
    roots = [native_root(source, lengths[source]) for source in range(len(lengths))]
    for root in roots:
        root['native']['rootNodes'] = {
            'timber': {'key': 'timber:' + str(root['timber']['id']),
                       'kind': 'timber', 'id': root['timber']['id'],
                       'placed': True, 'surface': root['placement']['id']},
            'placement': {'key': 'placement:' + str(root['placement']['id']),
                          'kind': 'placement', 'id': root['placement']['id']}}
    context = {'projectScope': 'project-research-A', 'scenario': 'scenario-selected-A', 'projectRevision': 7,
               'liveReadPin': pin('live-read-7'), 'attachmentPin': pin('explicit-study-declaration'),
               'settingsPin': pin('no-cutting-settings-used'), 'modelPins': {}}
    representations = []
    for index, source in enumerate(sources):
        row = copy.deepcopy(roots[source])
        row['ref'] = ('live:' if index == 0 else 'model-' + str(index) + ':') + str(source)
        row['category'], row['kind'], row['model'] = 'ordinary-d7', ('live' if index == 0 else 'model'), None
        if index:
            row['native']['readPin'] = pin('candidate-read-' + str(index))
            row['model'] = {'recordId': 'record-' + str(index), 'owner': 'owner-in-selected-scenario',
                            'recordSha256': pin('exact-model-record-' + str(index)), 'sourceKind': 'ordinary-plan',
                            'inputTimbers': [source], 'inputOutcome': 'COMPLETE', 'resultOutcome': 'COMPLETE'}
            context['modelPins'][row['model']['recordId']] = {'owner': row['model']['owner'], 'recordSha256': row['model']['recordSha256'], 'readPin': row['native']['readPin']}
        representations.append(row)
    groups, excluded = {}, []
    for row, assigned in zip(representations, allocation):
        if assigned == 'E':
            excluded.append(row['ref'])
        elif assigned != 'U':
            groups.setdefault(assigned, []).append(row['ref'])
    items = [{'itemKey': key, 'members': members, 'representative': members[0]} for key, members in groups.items()]
    return {'studySchema': 'U476-facts/1', 'context': context, 'endContext': copy.deepcopy(context), 'current': roots,
            'representations': representations, 'declarations': {'items': items, 'excluded': excluded}}


def named(name):
    straightforward = {
        'same-source-explicit': {}, 'same-source-unresolved': {'allocation': (1, 2)},
        'same-source-undeclared': {'allocation': ('U', 'U')},
        'same-size-distinct': {'sources': (0, 1), 'allocation': (1, 2)},
        'same-size-illegal-merge': {'sources': (0, 1)},
        'multi-model-aliases': {'sources': (0, 0, 0), 'allocation': (1, 1, 1)},
        'explicit-exclusion': {'allocation': (1, 'E')}, 'all-excluded': {'allocation': ('E', 'E')},
    }
    if name in straightforward:
        return make(**straightforward[name])
    data = make()
    second = data['representations'][1]
    if name == 'definition-changed-same-values':
        second['native']['definitionPin']['timber'] = pin('old-definition-same-measurements')
    elif name == 'effective-changed-same-values':
        second['native']['effectivePin']['timber'] = pin('old-effective-same-measurements')
    elif name == 'typed-source-changed-same-values':
        second['native']['content']['typedSources']['A']['id'] = 9
    elif name == 'support-changed-same-ends':
        second['native']['content']['supports'][0]['id'] = 9
    elif name == 'old-model-missing-marks':
        second['timber']['mark'] = None
    elif name == 'same-id-rebuilt':
        second['timber']['mark'] = 'prior-incarnation'
        data['declarations']['items'] = [{'itemKey': 1, 'members': [second['ref']], 'representative': second['ref']}]
        data['declarations']['excluded'] = [data['representations'][0]['ref']]
    elif name == 'missing-current-source':
        data['current'] = []
    elif name == 'native-read-incomplete':
        second['native']['complete'] = False
    elif name == 'source-pin-missing':
        second['native']['definitionPin'] = None
    elif name == 'source-support-missing':
        second['native']['content']['supports'] = None
    elif name == 'source-support-unknown-equal':
        for row in data['representations'] + data['current']:
            row['native']['content']['supports'] = {'start': {'status': 'unknown', 'relation': None}, 'finish': {'status': 'unknown', 'relation': None}}
    elif name == 'source-support-empty-equal':
        for row in data['representations'] + data['current']:
            row['native']['content']['supports'] = []
    elif name == 'source-detail-missing':
        second['native']['content']['typedSources'] = None
    elif name == 'current-read-incomplete':
        data['current'][0]['native']['complete'] = False
    elif name == 'model-input-invalid':
        second['model']['inputOutcome'] = 'INVALID'
    elif name == 'model-result-invalid':
        second['model']['resultOutcome'] = 'INVALID'
    elif name == 'model-not-selected-input':
        second['model']['inputTimbers'] = [1]
    elif name == 'model-record-replaced':
        second['model']['recordSha256'] = pin('record-was-replaced')
    elif name in ('assembly-owned', 'd36', 'ungenerated-binding', 'arbitrary-mesh'):
        second['category'] = {'assembly-owned': 'assembly-owned', 'd36': 'd36', 'ungenerated-binding': 'binding', 'arbitrary-mesh': 'mesh'}[name]
    elif name == 'faces-plus-timbers':
        second['model']['sourceKind'] = 'faces+timbers'
    elif name == 'cross-project':
        second['projectScope'] = 'other-project'
    elif name == 'cross-scenario':
        second['scenario'] = 'other-scenario'
    elif name == 'context-changed':
        data['endContext']['projectRevision'] += 1
    elif name == 'excluded-context-stale':
        data = named('explicit-exclusion')
        data['endContext']['modelPins']['record-1']['recordSha256'] = pin('excluded-record-replaced')
    elif name == 'included-and-excluded':
        data['declarations']['excluded'] = [second['ref']]
    elif name == 'member-duplicated':
        data['declarations']['items'][0]['members'].append(second['ref'])
    elif name == 'member-unknown':
        data['declarations']['items'][0]['members'].append('no-such-representation')
    elif name == 'representative-fake':
        data['declarations']['items'][0]['representative'] = 'no-such-representation'
    elif name == 'item-key-zero':
        data['declarations']['items'][0]['itemKey'] = 0
    elif name == 'item-key-duplicate':
        data = named('same-size-distinct')
        data['declarations']['items'][1]['itemKey'] = 1
    elif name == 'manual-checkbox-bad-proof':
        second['native']['content']['L'] += 1
        data['declarations']['items'][0]['manualConfirmed'] = True
    elif name == 'native-root-nodes-missing':
        second['native'].pop('rootNodes')
    elif name == 'native-timber-kind-wrong':
        second['native']['rootNodes']['timber']['kind'] = 'placement'
    elif name == 'native-timber-id-wrong':
        second['native']['rootNodes']['timber']['id'] = 9
    elif name == 'native-placement-kind-wrong':
        second['native']['rootNodes']['placement']['kind'] = 'timber'
    elif name == 'native-placement-id-wrong':
        second['native']['rootNodes']['placement']['id'] = 9
    elif name == 'native-root-key-wrong':
        second['native']['rootNodes']['timber']['key'] = 'timber:9'
    elif name == 'native-unplaced':
        second['native']['rootNodes']['timber']['placed'] = False
    elif name == 'native-surface-wrong':
        second['native']['rootNodes']['timber']['surface'] = 9
    elif name == 'current-timber-kind-wrong':
        data['current'][0]['native']['rootNodes']['timber']['kind'] = 'placement'
    elif name == 'current-placement-id-wrong':
        data['current'][0]['native']['rootNodes']['placement']['id'] = 9
    elif name == 'current-root-nodes-missing':
        data['current'][0]['native'].pop('rootNodes')
    elif name == 'empty-definition-pin-map':
        second['native']['definitionPin'] = {}
    elif name == 'missing-placement-pin':
        second['native']['definitionPin'] = {'timber': pin('present-only-one-root')}
    elif name == 'native-complete-not-boolean':
        second['native']['complete'] = 1
    elif name == 'item-key-max':
        data['declarations']['items'][0]['itemKey'] = 4294967295
    elif name == 'item-key-boolean':
        data['declarations']['items'][0]['itemKey'] = True
    elif name == 'caller-verified-cannot-override':
        second['native']['content']['L'] += 1
        second['verified'] = True
        second['native']['verified'] = True
        data['declarations']['items'][0]['verified'] = True
    elif name == 'source-support-empty-source-equal':
        for row in data['representations'] + data['current']:
            row['native']['content']['supports'] = {
                'start': {'status': 'exact', 'relation': {'source': {}}},
                'finish': {'status': 'exact', 'relation': {'source': {}}}}
    elif name == 'current-read-pin-mixed-model-only':
        data['declarations']['items'] = [{'itemKey': 1, 'members': [second['ref']],
                                         'representative': second['ref']}]
        data['declarations']['excluded'] = [data['representations'][0]['ref']]
        data['current'][0]['native']['readPin'] = pin('another-native-read')
    else:
        raise KeyError(name)
    return data


NAMES = ['same-source-explicit', 'same-source-unresolved', 'same-source-undeclared', 'same-size-distinct',
         'same-size-illegal-merge', 'multi-model-aliases', 'explicit-exclusion', 'all-excluded',
         'definition-changed-same-values', 'effective-changed-same-values', 'typed-source-changed-same-values',
         'support-changed-same-ends', 'old-model-missing-marks', 'same-id-rebuilt', 'missing-current-source',
         'native-read-incomplete', 'source-pin-missing', 'source-support-missing', 'source-support-unknown-equal',
         'source-support-empty-equal', 'source-detail-missing', 'current-read-incomplete', 'model-input-invalid',
         'model-result-invalid', 'model-not-selected-input', 'model-record-replaced', 'assembly-owned', 'faces-plus-timbers',
         'd36', 'ungenerated-binding', 'arbitrary-mesh', 'cross-project', 'cross-scenario', 'context-changed',
         'excluded-context-stale', 'included-and-excluded', 'member-duplicated', 'member-unknown', 'representative-fake',
         'item-key-zero', 'item-key-duplicate', 'manual-checkbox-bad-proof']


NAMES += ['native-root-nodes-missing', 'native-timber-kind-wrong', 'native-timber-id-wrong',
          'native-placement-kind-wrong', 'native-placement-id-wrong', 'native-root-key-wrong',
          'native-unplaced', 'native-surface-wrong', 'current-timber-kind-wrong',
          'current-placement-id-wrong', 'current-root-nodes-missing', 'empty-definition-pin-map',
          'missing-placement-pin', 'native-complete-not-boolean', 'item-key-max',
          'item-key-boolean', 'caller-verified-cannot-override',
          'source-support-empty-source-equal', 'current-read-pin-mixed-model-only']


if __name__ == '__main__':
    json.dump({'cases': [{'name': name, 'input': named(name)} for name in NAMES]},
              sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write('\n')
