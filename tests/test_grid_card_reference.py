"""CR acceptance against actual native candidates; coordinates are independent constants.

CR24 is the UI slice and is not registered as a fake native pass or skip here.
CR18 tests the currently supported no-ledger context; marked identity-ledger/1
acceptance remains with its implementation owner (no native ledger is advertised).
"""
from copy import deepcopy
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'geometry-core'))
from tests import test_engineering_core as eng_harness
from tests.test_parameters_core import card, field
from tests.test_grid_system_contract import rejection_reason
from modeling import build_package, verify_package, ModelError


def source(parameter=10, u=3, v=8):
    return {'parameterId': parameter, 'uFieldId': u, 'vFieldId': v}


def grid(identifier=4, ref=True, u='repeat -5 card', v='repeat 7 card'):
    value = {'id': identifier, 'name': 'G', 'mainAlong': 'none', 'u': u, 'v': v}
    if ref:
        value['cardReference'] = source() if ref is True else ref
    return {'op': 'put-grid-system', 'value': value}


def parameter(a='12', b='30', identifier=10, extras=(), order=False, name='P'):
    fields = [field(3, a, name='a'), field(8, b, name='b')]
    return card(identifier, name, (fields[::-1] if order else fields) + list(extras))


def swap(identifier=4):
    return {'op': 'swap-grid-card-reference', 'id': identifier}


def unbind(mode='direct', identifier=4):
    return {'op': 'unbind-grid-card-reference', 'id': identifier, 'mode': mode}


class GridCardReference(unittest.TestCase):
    setUpClass = classmethod(eng_harness.EngineeringCore.setUpClass.__func__)
    setUp = eng_harness.EngineeringCore.setUp
    command = eng_harness.EngineeringCore.command
    read = eng_harness.EngineeringCore.read
    request = eng_harness.EngineeringCore.request
    apply = eng_harness.EngineeringCore.apply
    apply_line = eng_harness.EngineeringCore.apply_line

    def seed(self, **kwargs):
        self.apply([parameter(**kwargs), grid()])

    def dump(self):
        return self.command('dump')['text']

    def systems(self):
        return {s['id']: s for s in self.command('objects')['gridSystems']}

    def state(self):
        return self.dump(), self.read(), self.command('objects')

    def reject(self, ops, reason, label):
        before = self.state()
        result = self.request(ops)
        self.assertTrue(result['ok'], (label, result))
        self.assertFalse(result['preview']['valid'], (label, result))
        self.assertIn(reason, json.dumps(result, ensure_ascii=False), (label, result))
        self.assertFalse(self.command(f"engineering-confirm {result['preview']['token']}")['ok'], label)
        self.assertEqual(before, self.state(), label + ': World/metadata/revision unchanged')
        return result

    def lines(self, axis):
        result = self.command('grid-query system 4 rect -100 -100 100 100 mode exact limit 64')
        self.assertTrue(result['ok'], result)
        values = {int(row['index']): row['coordinate'] for row in result['axes'][axis]['lines']}
        return [values[k] for k in (-1, 0, 1)]

    def lengths(self):
        s = self.systems()[4]
        return tuple(next(s[a + 'Definition'][key] for key in ('effectiveStep', 'effectivePanel', 'step', 'panel')
                          if key in s[a + 'Definition']) for a in ('u', 'v'))

    def assert_source(self, expected=source(), label='CARD_UNIT'):
        s = self.systems()[4]
        self.assertEqual(expected, s.get('cardReference'), label)
        for axis in ('u', 'v'):
            d = s[axis + 'Definition']; slot = 'step' if d['source'] == 'repeat' else 'panel'
            self.assertEqual('card', d.get(slot + 'Source'), label)
            self.assertNotIn(slot, d.get('parameterRefs', {}), label)
            self.assertNotIn(slot, d, label + ': no independent direct value in the definition')
        definition = next(l for l in self.dump().splitlines() if l.startswith('grid-system 4 '))
        self.assertIn(f"card-reference {expected['parameterId']} {expected['uFieldId']} {expected['vFieldId']}", definition, label)
        self.assertEqual(2, definition.split().count('card'), label)

    def test_CR01_CARD_UNIT(self):
        self.seed(); self.assert_source()
        self.assertEqual([-17, -5, 7], self.lines('u'), 'CARD_UNIT')
        self.assertEqual([-23, 7, 37], self.lines('v'), 'CARD_UNIT')
        uses = [u for u in self.command('objects')['parameterUses'] if u['kind'] == 'grid-card-reference']
        self.assertEqual(1, len(uses), 'CARD_UNIT usage is one relationship')
        self.assertEqual([3, 8], [p['fieldId'] for p in uses[0]['paths']])

    def test_CR02_MIXED_MODE(self):
        self.seed(extras=[field(9, '3')])
        self.apply([grid(u='repeat-panel card gap param:10:9 from -5')])
        self.assertEqual([-7, 8, 23], self.lines('u'), 'MIXED_MODE')
        self.assertEqual([-23, 7, 37], self.lines('v'))
        self.assert_source()

    def test_CR03_SWAP_MAPPING_ONLY(self):
        self.seed(); self.apply([grid(u='repeat-panel card gap 3 from -5'), swap()])
        self.assertEqual([-7, 26, 59], self.lines('u'), 'SWAP_MAPPING_ONLY')
        self.assertEqual([-5, 7, 19], self.lines('v'))
        self.assert_source(source(u=8, v=3))
        self.assertEqual((3, -5), tuple(self.systems()[4]['uDefinition'][x] for x in ('gap', 'anchor')))

    def test_CR04_EQUAL_VALUE_IDENTITY(self):
        self.seed(b='12')
        graph = lambda: self.command('source-inspect')
        node = lambda g: next(n for n in g['nodes'] if n['key'] == 'grid-system:4')
        old_graph = graph(); old_node = node(old_graph)
        self.assertTrue(old_graph['complete'], 'EQUAL_VALUE_IDENTITY complete native source index')
        edges = {(e['to'], e['field']) for e in old_graph['edges'] if e['from'] == 'grid-system:4'}
        self.assertTrue({('parameter:10', 'card-reference'), ('parameter-field:10:f3', 'u.step'), ('parameter-field:10:f8', 'v.step')} <= edges, 'EQUAL_VALUE_IDENTITY source unit and paths')
        before = self.dump(); preview, _ = self.apply([swap()])
        self.assertNotEqual(before, self.dump(), 'EQUAL_VALUE_IDENTITY')
        self.assertEqual(source(u=8, v=3), preview['preview']['after']['geometry']['gridSystems'][0]['cardReference'])
        swapped = node(graph())
        self.assertNotEqual(old_node['definitionFingerprint'], swapped['definitionFingerprint'], 'EQUAL_VALUE_IDENTITY mapping is a definition')
        self.assertEqual(old_node['valueFingerprint'], swapped['valueFingerprint'])
        self.apply([parameter(a='18', b='12')]); self.assertEqual((12, 18), self.lengths())
        changed = node(graph())
        self.assertEqual(swapped['definitionFingerprint'], changed['definitionFingerprint'], 'EQUAL_VALUE_IDENTITY values are not definitions')
        self.assertNotEqual(swapped['valueFingerprint'], changed['valueFingerprint'])

    def test_CR05_STABLE_FIELD_IDS(self):
        self.seed(); p = self.request([swap()])['preview']
        self.apply_line('canvas-pos parameter 10 3 4')
        self.assertTrue(self.command(f"engineering-confirm {p['token']}")['ok'])
        p = self.request([swap()])['preview']
        self.apply([parameter(order=True, name='renamed')])
        self.assertFalse(self.command(f"engineering-confirm {p['token']}")['ok'], 'STABLE_FIELD_IDS stale rename')
        self.assert_source(source(u=8, v=3)); self.assertEqual((30, 12), self.lengths())

    def test_CR06_EXTRA_FIELD_DEPENDENCY(self):
        self.seed(); self.apply([parameter(extras=[field(9, '7')])]); self.assert_source()
        self.apply([parameter()]); self.assert_source()
        self.apply([parameter(extras=[field(11, '7')], a='=@10:11')])
        self.reject([parameter(a='=@10:11')], 'MISSING', 'EXTRA_FIELD_DEPENDENCY')

    def test_CR07_CARD_SHAPE_DISTINCT_FIELDS_SAME_CARD(self):
        self.apply([card(10, 'P', [field(3, '12')])])
        self.reject([grid()], 'field 8', 'CARD_SHAPE')
        self.apply([parameter()])
        self.reject([grid(ref=source(u=3, v=3))], 'DISTINCT_FIELDS', 'DISTINCT_FIELDS')
        bad = source(); bad['vParameterId'] = 11
        self.reject([grid(ref=bad)], 'SAME_CARD', 'SAME_CARD')

    def test_CR08_MAPPED_SOURCE_PROTECTION(self):
        self.seed()
        self.reject([card(10, 'P', [field(3, '12')])], 'grid-system 4', 'MAPPED_SOURCE_PROTECTION')
        for kind in ('count', 'ratio'):
            self.reject([card(10, 'P', [field(3, '12'), field(8, '30', kind)])], 'not a dimension', 'MAPPED_SOURCE_PROTECTION')
        self.reject([{'op': 'delete-parameter', 'id': 10}, parameter(identifier=11)], 'grid-system 4', 'MAPPED_SOURCE_PROTECTION')

    def test_CR09_EXACT_TARGET_LENGTH(self):
        self.seed()
        for b, why in [('0', 'POSITIVE'), ('-1', 'POSITIVE'), ('1/2', 'integer mm'), ('100000001', 'D1 range')]:
            self.reject([parameter(b=b)], why, 'EXACT_TARGET_LENGTH ' + b)
        for b in ('1', '100000000'):
            self.apply([parameter(b=b)]); self.assertEqual(int(b), self.lengths()[1])

    def test_CR10_FIELD_GRAPH_AND_PRECISION(self):
        self.seed(); self.apply([parameter(b='=3 mm/2*2')]); self.assertEqual((12, 3), self.lengths())
        exact = parameter(); b = exact['value']['fields'][1]; del b['input']
        b['expression'] = {'op': 'mul', 'left': {'op': 'literal', 'num': '3', 'den': '2', 'unit': 'mm'},
                           'right': {'op': 'literal', 'num': '2', 'den': '1', 'unit': '1'}}
        self.apply([exact]); self.assertEqual((12, 3), self.lengths(), 'FIELD_GRAPH_AND_PRECISION exact fractional AST')
        self.reject([parameter(b='=3/2*2')], 'UNIT', 'FIELD_GRAPH_AND_PRECISION unit')
        self.reject([parameter(b='=9223372036854775807 mm*2')], 'PRECISION', 'FIELD_GRAPH_AND_PRECISION precision')
        self.reject([parameter(b='=@10:8')], 'CYCLE', 'FIELD_GRAPH_AND_PRECISION cycle')
        self.apply([parameter(b='=@11:3'), parameter(identifier=11, b='=@10:3')])
        self.assertEqual((12, 12), self.lengths(), 'FIELD_GRAPH_AND_PRECISION cross-card acyclic')

    def test_CR11_SOURCE_EXCLUSIVITY_COMPLETE_MAPPING_MODE_SCOPE(self):
        self.seed()
        for token in ('12', 'param:10:3'):
            self.reject([grid(u='repeat -5 ' + token)], 'SOURCE_EXCLUSIVITY', 'SOURCE_EXCLUSIVITY')
        bad = source(); del bad['vFieldId']
        self.reject([grid(ref=bad)], 'COMPLETE_MAPPING', 'COMPLETE_MAPPING')
        self.reject([grid(v='none')], 'MODE_SCOPE', 'MODE_SCOPE')
        self.reject([grid(u='series 0 12 3')], 'MODE_SCOPE', 'MODE_SCOPE legacy identity')

    def test_CR12_ATOMIC_REBIND(self):
        self.seed(); self.apply([parameter(identifier=11, a='20', b='40'), {'op': 'set-grid-card-reference', 'id': 4, 'value': source(11)}])
        self.assertEqual((20, 40), self.lengths(), 'ATOMIC_REBIND')
        self.assert_source(source(11))
        self.apply([card(12, 'Qbad', [field(3, '25'), field(8, '45', 'count')])])
        self.reject([{'op': 'set-grid-card-reference', 'id': 4, 'value': source(12)}], 'not a dimension', 'ATOMIC_REBIND')

    def test_CR13_EXPLICIT_UNBIND_ORDERED_CAPTURE(self):
        self.seed(extras=[field(9, '3')]); self.apply([grid(u='repeat-panel card gap param:10:9 from -5'), unbind('parameter')])
        self.assertNotIn('cardReference', self.systems()[4]); self.apply([parameter(a='18', extras=[field(9, '3')])])
        self.assertEqual((18, 30), self.lengths(), 'EXPLICIT_UNBIND follows parameter')
        self.apply([{'op': 'set-grid-card-reference', 'id': 4, 'value': source()}, parameter(a='12', extras=[field(9, '3')])])
        p, _ = self.apply([parameter(a='18', extras=[field(9, '3')]), unbind()])
        self.assertEqual([18, 30], p['preview']['cardCaptures'][0]['values'], 'EXPLICIT_UNBIND capture preview')
        self.assertEqual('ordered-candidate-step', p['preview']['cardCaptures'][0]['timing'])
        self.assertEqual((18, 30), self.lengths(), 'EXPLICIT_UNBIND capture current step')
        self.assertIn('gap param:10:9', self.dump(), 'EXPLICIT_UNBIND preserves other source')
        self.apply([parameter(a='12', extras=[field(9, '3')]), {'op': 'set-grid-card-reference', 'id': 4, 'value': source()}])
        p, _ = self.apply([unbind(), parameter(a='18', extras=[field(9, '3')])])
        self.assertEqual([12, 30], p['preview']['cardCaptures'][0]['values'], 'EXPLICIT_UNBIND earlier capture preview')
        self.assertEqual((12, 30), self.lengths(), 'EXPLICIT_UNBIND must not capture future value')

    def test_CR14_MODE_TRANSITION(self):
        self.seed(); self.apply([grid(v='repeat-panel card gap 3 from 7')]); self.assertEqual((12, 30), self.lengths())
        self.reject([grid(v='repeat-panel card')], 'MODE_TRANSITION', 'MODE_TRANSITION missing new fields')
        self.reject([grid(v='none')], 'MODE_SCOPE', 'MODE_TRANSITION half reference')
        self.apply([unbind(), grid(ref=False, u='repeat -5 12', v='none')])
        self.assertNotIn('cardReference', self.systems()[4])

    def binding_fixture(self):
        for identifier in (2, 3):
            self.apply_line(f'boundary {identifier} outline 100,200 1300,200 1300,1000 100,1000')
            self.apply_line(f'boundary-vertex-keys {identifier} outer 1 2 3 4 next-key 5')
            self.apply_line(f'grid-binding {identifier} on-boundary {identifier} from-system 4 vertex-key 1 cell -2 1 anchor 1 2 1 2')

    def test_CR15_ALL_BINDINGS_RECOMPUTE(self):
        self.seed(); self.binding_fixture()
        bindings = lambda: self.command('objects')['gridBindings']
        before = deepcopy(bindings()); self.apply([parameter(a='20')]); after = bindings()
        self.assertEqual([[123, 148]] * 2, [b['translation'] for b in before], 'ALL_BINDINGS_RECOMPUTE exact old value')
        self.assertEqual([[135, 148]] * 2, [b['translation'] for b in after], 'ALL_BINDINGS_RECOMPUTE exact new value')
        for a, b in zip(before, after):
            self.assertEqual(a['cell'], b['cell'], 'ALL_BINDINGS_RECOMPUTE cell')
            self.assertEqual(a['vertexKey'], b['vertexKey'])
            self.assertEqual(a['anchor'], b['anchor'])
        self.assertNotEqual(before, after, 'ALL_BINDINGS_RECOMPUTE effective geometry')
        self.apply_line('grid-binding 2 on-boundary 2 from-system 4 vertex-key 1 cell -2 1 anchor 0 1 1 2')
        self.reject([parameter(a='13')], 'integer', 'ALL_BINDINGS_RECOMPUTE half millimetre')

    def test_CR16_INDEX_AND_DOWNSTREAM(self):
        self.seed(); self.apply([grid(u='repeat -5 card stagger 6')]); self.binding_fixture()
        self.apply([parameter(a='18')]); self.assertEqual((-2, 1), tuple(map(int, self.command('objects')['gridBindings'][0]['cell'])))
        self.reject([parameter(a='6')], '整數倍', 'INDEX_AND_DOWNSTREAM stagger')
        # D19a rules retain keys when the parent's actual length changes.
        self.apply([grid()]); self.apply_line('grid-source-rule 4 create name-hex 52 selector all-cells divide 2 2')
        before = self.systems()[4]['rules']; self.apply([parameter(a='20')]); self.assertEqual(before, self.systems()[4]['rules'])

    def test_CR17_CANDIDATE_LIFECYCLE(self):
        self.seed()
        self.apply_line('boundary-vertex-keys 1 outer 1 2 3 4 next-key 5')
        self.apply_line('grid-binding 2 on-boundary 1 from-system 4 vertex-key 1 cell 0 0 anchor 0 1 0 1')
        before = self.dump(); p = self.request([swap()])['preview']
        self.assertEqual(before, self.dump()); self.command(f"engineering-cancel {p['token']}")
        self.assertFalse(self.command(f"engineering-confirm {p['token']}")['ok']); self.assertEqual(before, self.dump())
        p = self.request([swap()])['preview']; self.apply([parameter(a='18')])
        self.assertFalse(self.command(f"engineering-confirm {p['token']}")['ok'], 'CANDIDATE_LIFECYCLE stale')
        p = self.request([swap()])['preview']; self.apply_line('spec stale_marker 3')
        stale = self.command(f"engineering-confirm {p['token']}")
        self.assertEqual('STALE', stale.get('code'), 'CANDIDATE_LIFECYCLE unrelated definition expiry')
        before = self.dump(); self.apply([swap()]); after = self.dump()
        self.apply_line('undo'); self.assertEqual(before, self.dump(), 'CANDIDATE_LIFECYCLE one undo')
        self.apply_line('redo'); self.assertEqual(after, self.dump(), 'CANDIDATE_LIFECYCLE full redo')
        scene = self.directory / 'confirm.scene'; scene.write_text(self.dump(), encoding='utf-8')
        probe = self.directory / 'confirm-probe'
        bridge_source = ROOT / 'geometry-web/web_bridge.c'
        instrumented = bridge_source.read_text().replace('int main(void)', 'int geometry_bridge_main(void)')
        instrumented = re.sub(r'#include "([^"]+)"', lambda m: '#include "' + str((bridge_source.parent / m[1]).resolve()) + '"', instrumented)
        included = self.directory / 'bridge-main-renamed.inc'; included.write_text(instrumented, encoding='utf-8')
        compile_result = subprocess.run(['cc', '-std=c11', '-O0', '-DCR_BRIDGE_SOURCE="' + str(included) + '"', str(ROOT / 'geometry-core/card-reference/confirmation_probe.c'), '-lm', '-o', str(probe)], capture_output=True, text=True, timeout=60)
        self.assertEqual(0, compile_result.returncode, compile_result.stderr)
        result = subprocess.run([str(probe), str(scene), str(self.directory / 'confirm.json')], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, 'CANDIDATE_LIFECYCLE injection: ' + result.stdout + result.stderr)

    def test_CR18_INCARNATION_NOT_CONTENT_NO_LEDGER_CONTEXT(self):
        self.seed(); before = self.dump()
        self.apply([unbind(), {'op': 'delete-parameter', 'id': 10}, parameter(name='rebuilt'), {'op': 'set-grid-card-reference', 'id': 4, 'value': source()}])
        self.assert_source(); self.assertNotIn('requires identity-ledger/1', self.dump(), 'INCARNATION_NOT_CONTENT no invented marks')
        self.apply_line('undo'); self.assertEqual(before, self.dump())
        self.apply_line('redo'); self.assert_source()

    def test_CR19_CARD_SAVE_ROUNDTRIP(self):
        self.seed(); self.apply([grid(identifier=5)]); before = self.dump()
        path = self.directory / 'card.scene'; path.write_text(before, encoding='utf-8')
        self.command('reset'); self.assertTrue(self.command('loadfile ' + str(path))['ok'])
        self.assertEqual(before, self.dump(), 'CARD_SAVE_ROUNDTRIP full definitions')
        self.assert_source(); self.assertIn(5, self.systems(), 'CARD_SAVE_ROUNDTRIP unused grid')
        # Exercise the real ZIP writer/reader, then a fresh native context.
        result = subprocess.run(['node', str(ROOT / 'geometry-core/card-reference/archive_roundtrip.cjs'), str(path)],
                                capture_output=True, text=True, cwd=ROOT, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.command('reset'); self.assertTrue(self.command('loadfile ' + str(path) + '.reopened')['ok'])
        self.assertEqual(before, self.dump(), 'CARD_SAVE_ROUNDTRIP gcanvas and fresh native context')

    def test_CR20_NO_SILENT_DOWNGRADE(self):
        self.seed(); before = self.state(); text = self.dump()
        bad = [text.replace('requires grid-card-reference/1\n', ''), text.replace('grid-card-reference/1', 'grid-card-reference/2'),
               text.replace('card-reference 10 3 8', 'card-reference 10 3 99'), text.replace('card-reference 10 3 8', 'card-reference 11 3 8'),
               text.replace('repeat -5 card', 'repeat -5 mystery')]
        for n, scene in enumerate(bad):
            path = self.directory / f'bad{n}.scene'; path.write_text(scene, encoding='utf-8')
            self.assertFalse(self.command('loadfile ' + str(path))['ok'], 'NO_SILENT_DOWNGRADE')
            self.assertEqual(before, self.state(), 'NO_SILENT_DOWNGRADE current context retained')
        self.command('reset'); empty = self.state()
        for n in range(len(bad)):
            self.assertFalse(self.command('loadfile ' + str(self.directory / f'bad{n}.scene'))['ok'])
            self.assertEqual(empty, self.state(), 'NO_SILENT_DOWNGRADE empty context retained')

    def test_CR21_LEGACY_UNCHANGED(self):
        self.apply([parameter(), grid(ref=False, u='repeat -5 param:10:3', v='repeat 7 param:10:8')])
        self.assertNotIn('cardReference', self.systems()[4]); self.assertNotIn('grid-card-reference', self.dump())
        self.apply([grid(ref=False, u='repeat -5 18', v='repeat 7 param:10:8')]); self.assertEqual((18, 30), self.lengths())
        self.apply_line('grid-system 5 name-hex 4c main-along none u series 1 2 3 v explicit 4 8')
        self.assertEqual('legacy-finite', self.systems()[5]['mode'])

    def import_fixture(self):
        self.seed(); self.apply([card(i, f'constant{i}', [field(1, '1')]) for i in range(10)])
        c = deepcopy(next(c for c in self.read()['state']['parameters'] if c['id'] == 10))
        for f in c['fields']: f.pop('value', None)
        return {'op': 'import-parameters', 'value': {'schema': 'geometry-parameters/1', 'cards': [c]}}

    def test_CR22_IMPORT_REUSED_KEY_GUARD_IMPORT_ISOLATION(self):
        imported = self.import_fixture()
        self.apply([imported])
        self.assertEqual(11, self.read()['state']['parameters'][-1]['id'], 'IMPORT_ISOLATION same name receives independent id')
        self.reject([{'op': 'delete-parameter', 'id': 10}, imported], 'grid-system 4', 'IMPORT_REUSED_KEY_GUARD')
        self.apply([unbind(), {'op': 'delete-parameter', 'id': 10}, imported])
        c = self.read()['state']['parameters'][-1]
        self.assertEqual(10, c['id'], 'IMPORT_ISOLATION first unused id')
        self.assertEqual([3, 8], [f['id'] for f in c['fields']])
        self.assertNotIn('cardReference', self.systems()[4])

    def test_CR25_EXPLICIT_REVERSED_MAPPING(self):
        self.apply([parameter(), grid(ref=source(u=8, v=3))]); self.assert_source(source(u=8, v=3))
        self.assertEqual([-35, -5, 25], self.lines('u'), 'EXPLICIT_REVERSED_MAPPING')
        self.assertEqual([-5, 7, 19], self.lines('v'))
        self.apply([parameter(a='18')]); self.assertEqual([-11, 7, 25], self.lines('v'))

    def test_CR26_SAME_KEY_REFERENCE_GUARD(self):
        self.seed(); self.reject([{'op': 'delete-parameter', 'id': 10}, parameter()], 'grid-system 4', 'SAME_KEY_REFERENCE_GUARD')

    def test_CR27_EXPLICIT_POST_DELETE_REBIND(self):
        self.seed(); self.apply([{'op': 'delete-parameter', 'id': 10}, parameter(), grid()])
        self.apply([grid(identifier=5)])
        self.reject([{'op': 'delete-parameter', 'id': 10}, parameter(), grid()], 'grid-system 5', 'EXPLICIT_POST_DELETE_REBIND all owners')
        preview, _ = self.apply([{'op': 'delete-parameter', 'id': 10}, parameter(), grid(), grid(identifier=5)])
        self.assertEqual({4, 5}, {r['owner']['id'] for r in preview['preview']['redeclaredReferences']}, 'EXPLICIT_POST_DELETE_REBIND preview')

    def test_CR28_ORDERED_REFERENCE_PROTECTION(self):
        self.seed()
        self.reject([grid(), {'op': 'delete-parameter', 'id': 10}, parameter()], 'grid-system 4', 'ORDERED_REFERENCE_PROTECTION before delete')
        self.reject([{'op': 'delete-parameter', 'id': 10}, parameter(), grid(), {'op': 'delete-parameter', 'id': 10}, parameter()], 'grid-system 4', 'ORDERED_REFERENCE_PROTECTION last delete')
        self.apply([unbind(), {'op': 'delete-parameter', 'id': 10}, parameter()])

    def test_CR29_D25_CARD_CLOSURE(self):
        self.apply([parameter(b='=@11:8'), parameter(identifier=11), grid()])
        # Both providers are explicitly present; the fixture is a real placed timber.
        self.apply_line('boundary-vertex-keys 1 outer 1 2 3 4 next-key 5')
        self.apply_line('grid-binding 2 on-boundary 1 from-system 4 vertex-key 1 cell 0 0 anchor 0 1 0 1')
        self.apply_line('grid 10 on 1 from-binding 2')
        for line in ['timber 90 20 33 role boundary', 'place 90 on 1 at-face e0 +u +n',
                     'timber 91 20 33 role boundary', 'place 91 on 1 at-face e2 +u +n',
                     'timber 1 5 5 role primary', 'place 1 on 1 at-line grid 10 u 1 +v +n']:
            self.apply_line(line)
        definitions = {'base_scene': self.dump(), 'extensions': []}
        req = {'roots': [{'kind': 'timber', 'id': 1}], 'role': 'geometry', 'target': 'solid-set', 'allow_partial': False}
        try:
            pkg = build_package(definitions, req)
            rebuilt = verify_package(pkg)
        except ModelError as error:
            self.fail('D25_CARD_CLOSURE failed to retain/rebuild card sources: ' + str(error))
        self.assertEqual(pkg['derived'], rebuilt['derived'], 'D25_CARD_CLOSURE recompute')
        text = pkg['definitions']['base_scene']
        self.assertIn('card-reference 10 3 8 u repeat -5 card v repeat 7 card', text, 'D25_CARD_CLOSURE keep mapping/source')
        self.assertIn('grid-card-reference/1', pkg['manifest']['capabilities'], 'D25_CARD_CLOSURE capability')
        self.assertIn('parameters/1', pkg['manifest']['capabilities'])
        records = [(line.split()[1], json.loads(base64.b64decode(line.split()[2])))
                   for line in text.splitlines() if line.startswith(('parameters card ', 'parameters field '))]
        self.assertEqual({10, 11}, {r['id'] for kind, r in records if kind == 'card'}, 'D25_CARD_CLOSURE provider cards')
        b = next(r for kind, r in records if kind == 'field' and r['parameterId'] == 10 and r['id'] == 8)
        self.assertEqual({'op': 'ref', 'parameterId': 11, 'fieldId': 8}, b['expression'], 'D25_CARD_CLOSURE transitive source')
        without_q = []
        for line in text.splitlines():
            if line.startswith(('parameters card ', 'parameters field ')):
                r = json.loads(base64.b64decode(line.split()[2]))
                if (r.get('parameterId') if 'parameterId' in r else r['id']) == 11: continue
            without_q.append(line)
        for bad_text in ('\n'.join(without_q) + '\n', text.replace('card-reference 10 3 8', 'card-reference 10 3')):
            broken = deepcopy(pkg); broken['definitions']['base_scene'] = bad_text
            with self.assertRaises(ModelError, msg='D25_CARD_CLOSURE missing provider or mapping'): verify_package(broken)
        for removal in ['requires grid-card-reference/1\n', 'requires parameters/1\n']:
            broken = deepcopy(pkg); broken['definitions']['base_scene'] = text.replace(removal, '')
            with self.assertRaises(ModelError, msg='D25_CARD_CLOSURE stripped source capability'): verify_package(broken)
        broken = deepcopy(pkg); broken['manifest']['capabilities'].remove('grid-card-reference/1')
        with self.assertRaises(ModelError, msg='D25_CARD_CLOSURE stripped manifest capability'): verify_package(broken)

    def test_CR30_SWAP_REVALIDATES_STAGGER(self):
        self.seed(); self.apply([grid(u='repeat -5 card stagger 30')])
        self.reject([swap()], '整數倍', 'SWAP_REVALIDATES_STAGGER')
        self.apply([grid(u='repeat -5 card stagger 6'), swap()]); self.assertEqual((30, 12), self.lengths())

    def test_CR31_CONTROLLED_TOKEN_REJECT(self):
        self.seed()
        for token in ('12', 'param:10:3'):
            before = self.state(); r = self.command('line grid-system 4 name-hex 47 main-along none u repeat -5 ' + token + ' v repeat 7 30')
            self.assertFalse(r.get('ok') and r.get('preview', {}).get('valid', True), 'CONTROLLED_TOKEN_REJECT')
            self.assertIn('CONTROLLED_TOKEN_REJECT', rejection_reason(r)); self.assertEqual(before, self.state())
        self.apply([unbind('parameter')]); self.apply_line('grid-system 4 name-hex 47 main-along none u repeat -5 param:10:3 v repeat 7 param:10:8')

    def test_CR32_FIELD_KEY_RECREATION_GUARD(self):
        self.seed(); omit = card(10, 'P', [field(3, '12')])
        self.reject([omit, parameter()], 'grid-system 4', 'FIELD_KEY_RECREATION_GUARD')
        self.apply([omit, parameter(), grid()])
        self.reject([omit, parameter(), grid(), omit, parameter()], 'grid-system 4', 'FIELD_KEY_RECREATION_GUARD last deletion')

    def test_CR33_PARAMETER_PACKAGE_BOUNDARY(self):
        self.seed()
        package = lambda ops: {'op': 'parameter-package', 'operations': ops}
        self.reject([package([parameter(a='18'), unbind()])], 'PARAMETER_PACKAGE_BOUNDARY', 'PARAMETER_PACKAGE_BOUNDARY')
        self.apply([package([parameter(a='18')]), unbind()]); self.assertEqual((18, 30), self.lengths())
        self.apply([parameter(), {'op': 'set-grid-card-reference', 'id': 4, 'value': source()}])
        self.apply([unbind(), package([parameter(a='18')])]); self.assertEqual((12, 30), self.lengths())


if __name__ == '__main__':
    unittest.main()
