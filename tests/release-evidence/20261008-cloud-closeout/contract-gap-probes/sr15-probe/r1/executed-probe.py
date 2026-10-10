#!/usr/bin/env python3
"""SR15 native parameter/binding-anchor probe. Prepared, not executed by author.

Exactly one test is loaded. No build, browser, HTTP reset, or production edits.
The runner must provide an already-fresh bridge and a clean exact repository head.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path('/workspace/geometry-axiom')
sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_grid_subdivision_oracle import NativeSubdivisionOracle
from tests.test_parameters_core import card, field

ARGS = None
REPORT = {'schema': 'sr15-parameter-anchor-native-probe/1', 'checks': [], 'snapshots': {}}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError({'command': ['git', *args], 'stdout': result.stdout,
                            'stderr': result.stderr, 'exit': result.returncode})
    return result.stdout.strip()

def write(name, value):
    (ARGS.out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

class SR15(NativeSubdivisionOracle):
    @classmethod
    def setUpClass(cls):
        # Explicit registry inspection only: never invoke a fallback build.
        info = _bridge.binaries.inspect_one(_bridge.binaries.BY_NAME['bridge'], path=ARGS.bridge)
        if info.state != 'fresh':
            raise RuntimeError('Provided bridge is not fresh: ' + str(info.reason))
        cls.bridge = str(info.path)
        REPORT['bridge'] = {'path': cls.bridge, 'sha256': sha(cls.bridge),
                            'state': info.state, 'reason': info.reason}

    def setUp(self):
        self.session = _bridge.BridgeSession(self.bridge)
        self.directory = ARGS.out / 'requests'
        self.directory.mkdir()
        REPORT['bridge']['pid'] = self.session.process.pid
        REPORT['bridge']['liveExeSHA256'] = sha('/proc/%s/exe' % self.session.process.pid)
        self.assertEqual(REPORT['bridge']['sha256'], REPORT['bridge']['liveExeSHA256'])
        self.wire = (ARGS.out / 'wire.jsonl').open('w', encoding='utf-8')
        self.addCleanup(self.close_owned)
        self.request_number = 0
        self.commit('reset')

    def close_owned(self):
        p = self.session.process
        p.stdin.close()
        killed = False
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            killed = True
            p.kill()
            p.wait(timeout=10)
        (ARGS.out / 'bridge.stderr').write_text(self.session.stderr_text())
        REPORT['bridgeCleanup'] = {'exitCode': p.returncode, 'forcedOwnedProcessStop': killed}
        p.stdout.close()
        self.session.stderr.close()
        self.wire.close()
        self.assertFalse(killed, 'bridge did not exit after stdin closed')
        self.assertEqual(0, p.returncode, 'native bridge exited abnormally')

    def command(self, command):
        self.session.process.stdin.write(command + '\n')
        self.session.process.stdin.flush()
        raw = self.session.process.stdout.readline()
        self.wire.write(json.dumps({'command': command, 'stdoutLine': raw}, ensure_ascii=False) + '\n')
        self.wire.flush()
        if not raw:
            raise AssertionError('bridge closed: ' + self.session.stderr_text())
        return json.loads(raw)

    def mark(self, name, detail=None):
        REPORT['checks'].append({'name': name, 'ok': True, 'detail': detail})
        print('PASS ' + name, flush=True)

    def capture(self, label):
        dump = self.command('dump')
        objects = self.command('objects')
        refs = self.command('references')
        engineering = self.command('engineering-read')
        self.assertTrue(all(r.get('ok') for r in [dump, objects, refs, engineering]))
        self.assertEqual(dump['revision'], engineering['revision'])
        result = {'world': {'dump': dump['text'], 'objects': objects, 'references': refs,
                            'engineeringState': engineering['state']},
                  'revision': dump['revision'], 'definitionSHA256': dump['definition_sha256']}
        REPORT['snapshots'][label] = result
        return result

    def unchanged(self, before, label):
        after = self.capture(label)
        self.assertEqual(before, after, label + ': World, refs, revision, definition hash')
        self.mark(label + ': entire live state and revision unchanged')

    def parameter_preview(self, pitch):
        self.request_number += 1
        request = {'schema': 'engineering-transaction/1',
                   'expectedRevision': self.command('engineering-read')['revision'],
                   'operations': [card(1, 'SR15 pitch', [field(1, str(pitch), name='U pitch')])]}
        path = self.directory / ('parameter-%02d.json' % self.request_number)
        path.write_text(json.dumps(request, ensure_ascii=False) + '\n')
        result = self.command('engineering-preview ' + str(path))
        self.assertTrue(result['ok'], result)
        self.assertIn('preview', result)
        return result['preview']

    def anchor_line(self, numerator=1, denominator=3):
        binding = next(b for b in self.command('objects')['gridBindings'] if b['id'] == 1)
        return ('grid-binding 1 on-boundary 2 from-system 0 vertex-key %s cell -2 1 anchor %s %s 1 2'
                % (binding['vertexKey'], numerator, denominator))

    def phase(self, label, pitch, b_anchor):
        # Literal R32/D30 oracle. Never derive expected coordinates from native results.
        values = {
            (600, 'half'): ([100, 200, 700, 600], [300, 500], [-200, 0, 400, 400], [0, 200], [300, 200]),
            (900, 'half'): ([100, 200, 1000, 600], [400, 700], [-350, 0, 550, 400], [-50, 250], [400, 250]),
            (900, 'third'): ([100, 200, 1000, 600], [400, 700], [-200, 0, 700, 400], [100, 400], [400, 400]),
        }
        a_bounds, a_u, b_bounds, b_u, guide_offsets = values[pitch, b_anchor]
        world = self.capture(label)
        owner = next(row for row in world['world']['objects']['gridSystems'] if row['id'] == 0)
        self.assertEqual(pitch, owner['uDefinition']['step'])
        self.assertEqual({'kind':'parameter', 'parameterId':1, 'fieldId':1},
                         owner['uDefinition']['parameterRefs']['step'])
        self.assertEqual(400, owner['vDefinition']['step'])
        self.assertEqual([{'ruleKey':1, 'name':'oracle rule', 'selector':{'kind':'all-cells'}, 'divisions':[3,2]}], owner['rules'])
        self.assertEqual(2, owner['nextRuleKey'])
        self.assertEqual([0, 1], sorted(owner['bindings']))
        self.assertEqual([{'grid':10,'surface':1}, {'grid':20,'surface':2}], owner['applications'])
        self.assertIn('u repeat 0 param:1:1 v repeat 0 400', world['world']['dump'])
        for binding, bounds, u in [(0,a_bounds,a_u),(1,b_bounds,b_u)]:
            result = self.query('binding', binding, cell=('-2','1'))
            self.assertTrue(result['ok'], result)
            self.assertEqual(bounds, result['bounds'])
            self.assertEqual(u, [l['coordinate'] for l in result['lines'] if l['axis']=='u'])
            self.assertEqual([400 if binding==0 else 200],
                             [l['coordinate'] for l in result['lines'] if l['axis']=='v'])
        refs = world['world']['references']
        for gid, offset, grid, cell, inner in [(9,guide_offsets[0],10,('-2','1'),0),
                                               (29,guide_offsets[1],20,('-2','1'),1)]:
            guide = next(g for g in refs['guides'] if g['id']==gid)
            self.assertEqual(offset, guide['off'])
            self.assertIn('guide %s %s v gridrule:%s:0:1:-2:1:u:%s' %
                          (gid, 1 if gid==9 else 2, grid, inner), world['world']['dump'])
        # V remains 400. Direct secondary lines therefore remain at y400/y600;
        # their full, stable rule identity and parent-cell validity must survive.
        for tid, grid, j, y, length, bounds in [
                (3,10,'1',400,540,a_bounds),
                (23,20,'2',600,240,[b_bounds[0],400,b_bounds[2],800])]:
            timber = next(t for t in refs['timbers'] if t['id']==tid)
            self.assertEqual(y, timber['geometry']['centerline'])
            self.assertEqual(length, timber['geometry']['length'])
            anchor = 'at-line rule %s 0 1 -2 %s v 0' % (grid,j)
            self.assertTrue(timber['definition']['anchor'].startswith(anchor))
            q = self.query('grid', grid, cell=('-2',j))
            self.assertTrue(q['ok'], q)
            self.assertEqual(bounds, q['bounds'])
            line = next(l for l in q['lines'] if l['axis']=='v' and l['innerIndex']==0)
            self.assertEqual(y, line['coordinate'])
            self.assertEqual({'kind':'grid-rule-line','appliedGridId':grid,'systemId':0,
                              'ruleKey':1,'cellI':'-2','cellJ':j,'axis':'v','innerIndex':0}, line['ref'])
        self.unchanged(world, label+'-after-readonly-queries')
        self.mark(label+': exact two-binding coordinates, two guides and two direct refs',
                  {'pitch':pitch,'bAnchor':b_anchor,'guideOffsets':guide_offsets})
        return world

    def history_pair(self, before, after, label):
        self.commit('undo')
        undone = self.capture(label+'-undo')
        self.assertEqual(before['world'], undone['world'])
        self.assertEqual(before['definitionSHA256'], undone['definitionSHA256'])
        self.assertGreater(undone['revision'], after['revision'])
        self.commit('redo')
        redone = self.capture(label+'-redo')
        self.assertEqual(after['world'], redone['world'])
        self.assertEqual(after['definitionSHA256'], redone['definitionSHA256'])
        self.assertGreater(redone['revision'], undone['revision'])
        self.mark(label+': Undo/Redo restore complete World while revision advances')
        return redone

    def test_sr15(self):
        setup = self.parameter_preview(600)
        self.assertTrue(setup['valid'], setup)
        self.assertTrue(self.command('engineering-confirm '+str(setup['token']))['ok'])
        self.commit(self.source(u='repeat 0 param:1:1'))
        self.commit(self.rule())
        for surface, binding, grid, first, anchor, stops, cell_j in [
                (1,0,10,1,(0,1,0,1),(120,680),'1'),
                (2,1,20,21,(1,2,1,2),(120,380),'2')]:
            self.boundary(surface)
            self.binding(binding, boundary=surface, anchor=anchor)
            self.apply_grid(grid, surface=surface, binding=binding)
            self.real_supports(surface=surface, first=first, positions=stops)
            self.commit('timber %s 20 20 role secondary' % (first+2))
            self.commit('place %s on %s at-line rule %s 0 1 -2 %s v 0 between t%s t%s +u +n' %
                        (first+2,surface,grid,cell_j,first,first+1))
        self.commit('guide 9 1 v gridrule:10:0:1:-2:1:u:0')
        self.commit('guide 29 2 v gridrule:20:0:1:-2:1:u:1')
        before = self.phase('parameter600',600,'half')
        pv = self.parameter_preview(900)
        self.assertTrue(pv['valid'], pv)
        self.unchanged(before,'parameter900-preview-live')
        guides = {g['id']:g for g in pv['after']['geometry']['guides']}
        self.assertEqual([400,0,0], guides[9]['worldPoint'])
        self.assertEqual([250,0,0], guides[29]['worldPoint'])
        self.assertEqual({10,20}, {g['id'] for g in pv['after']['geometry']['grids']})
        self.assertTrue(self.command('engineering-cancel '+str(pv['token']))['ok'])
        self.unchanged(before,'parameter900-cancel')
        pv = self.parameter_preview(900)
        self.assertTrue(pv['valid'],pv)
        self.assertTrue(self.command('engineering-confirm '+str(pv['token']))['ok'])
        after = self.phase('parameter900',900,'half')
        self.assertGreater(after['revision'], before['revision'])
        self.assertNotEqual(after['definitionSHA256'], before['definitionSHA256'])
        stable = self.history_pair(before,after,'parameter-update')
        # 902 remains integral at B's one-half anchor (451), so the refusal
        # reaches the intended U3 non-divisibility instead of an earlier I37
        # fractional-anchor guard that 901 would trigger.
        bad = self.parameter_preview(902)
        self.assertFalse(bad['valid'],bad)
        self.assertIn('DIVISION_NOT_EXACT',json.dumps(bad,ensure_ascii=False))
        self.assertFalse(self.command('engineering-confirm '+str(bad['token']))['ok'])
        self.unchanged(stable,'nondivisible-parameter-refused')
        before_anchor = self.capture('before-anchor-edit')
        anchor = self.anchor_line()
        pv = self.preview(anchor)
        self.assertEqual({1}, {r['id'] for r in pv['gridBindings']})
        self.unchanged(before_anchor,'anchor-preview-live')
        self.commit('cancel-preview')
        self.unchanged(before_anchor,'anchor-cancel')
        pv = self.preview(anchor)
        self.commit('confirm '+str(pv['token']))
        after_anchor = self.phase('anchor-third',900,'third')
        self.assertGreater(after_anchor['revision'],before_anchor['revision'])
        self.assertNotEqual(after_anchor['definitionSHA256'],before_anchor['definitionSHA256'])
        # Only B's u fraction changes; source, A binding and both formal tuple
        # identities remain exactly the same, while B translations recompute.
        old_objects,new_objects = before_anchor['world']['objects'],after_anchor['world']['objects']
        self.assertEqual(old_objects['gridSystems'],new_objects['gridSystems'])
        self.assertEqual(next(b for b in old_objects['gridBindings'] if b['id']==0),
                         next(b for b in new_objects['gridBindings'] if b['id']==0))
        old_b=next(b for b in old_objects['gridBindings'] if b['id']==1)
        new_b=next(b for b in new_objects['gridBindings'] if b['id']==1)
        self.assertEqual([{'num':1,'den':2},{'num':1,'den':2}],old_b['anchor'])
        self.assertEqual([{'num':1,'den':3},{'num':1,'den':2}],new_b['anchor'])
        allowed={'anchor','translation','translationExact'}
        self.assertEqual({k:v for k,v in old_b.items() if k not in allowed},
                         {k:v for k,v in new_b.items() if k not in allowed})
        for group, identifiers in [('guides',[1,2,9]),('timbers',[1,2,3,81,82]),('grids',[10])]:
            select=lambda snap:[x for x in snap['world']['references'][group] if x['id'] in identifiers]
            self.assertEqual(select(before_anchor),select(after_anchor),'unrelated A '+group)
        stable=self.history_pair(before_anchor,after_anchor,'binding-anchor-update')
        # An out-of-domain fraction has a parser/contract refusal, never a valid
        # candidate. Pin the existing I37 family and preserve complete state.
        rejected=self.line(self.anchor_line(4,3))
        self.assertFalse(rejected.get('ok') and rejected.get('preview',{}).get('valid',True),rejected)
        self.assertIn('I37',json.dumps(rejected,ensure_ascii=False))
        if 'preview' in rejected:
            self.assertFalse(self.line('confirm '+str(rejected['preview']['token']))['ok'])
        self.unchanged(stable,'invalid-anchor-refused')

def main():
    global ARGS
    ap=argparse.ArgumentParser()
    ap.add_argument('--head',required=True)
    ap.add_argument('--bridge',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ARGS=ap.parse_args()
    ARGS.out.mkdir(parents=True,exist_ok=False)
    REPORT['startedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    REPORT['head']=git('rev-parse','HEAD')
    REPORT['dirtyBefore']=git('status','--porcelain')
    REPORT['sourceSHA256']={str(p):sha(p) for p in [Path(__file__),
        ROOT/'tests/test_grid_subdivision_oracle.py',ROOT/'tests/test_parameters_core.py',
        ROOT/'tests/_bridge.py',ROOT/'公理層.md']}
    if REPORT['head']!=ARGS.head or REPORT['dirtyBefore']:
        write('result.json',REPORT)
        raise RuntimeError('An exact clean head is required')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([SR15('test_sr15')]))
    REPORT['headAfter']=git('rev-parse','HEAD')
    REPORT['dirtyAfter']=git('status','--porcelain')
    REPORT['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    REPORT['testsRun']=result.testsRun
    REPORT['failures']=result.failures
    REPORT['errors']=result.errors
    REPORT['successful']=result.wasSuccessful() and REPORT['headAfter']==ARGS.head and not REPORT['dirtyAfter']
    # Unittest entries hold objects; preserve names and complete traceback text.
    for key in ['failures','errors']:
        REPORT[key]=[{'test':str(test),'traceback':text} for test,text in REPORT[key]]
    write('result.json',REPORT)
    print(json.dumps({'successful':REPORT['successful'],'out':str(ARGS.out),'testsRun':result.testsRun}))
    return 0 if REPORT['successful'] else 1

if __name__=='__main__':
    raise SystemExit(main())
