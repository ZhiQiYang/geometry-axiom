"""Read-only small static review: never import/run candidate or generator."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
DRAFT=Path('/workspace/geo300-capacity512-publication-20261024/host-v5-draft')
REPO=Path('/workspace/geo300-capacity512-work-20261024')
SOURCE='400a6d0ca50f3aca104fb569c77c8ef753c93355'
PIN='d4a745e6f2d101bcd65166617eacc75a3d095d8dc4bee9aa320532438ab25ca1'
checks=[]
def check(name,ok,detail=None):
    checks.append(dict(name=name,ok=bool(ok),detail=detail))
def sha(data):return hashlib.sha256(data).hexdigest()
def git(path):
    result=subprocess.run(['git','-C',str(REPO),'show',SOURCE+':'+path],capture_output=True)
    check('git source '+path,result.returncode==0,result.returncode)
    return result.stdout
def methods(data):
    tree=ast.parse(data)
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='TimberCapacityHost')
    return {node.name:node for node in cls.body if isinstance(node,ast.FunctionDef)}
def textpart(data,node):return ''.join(data.decode().splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def normalize(node):return ast.dump(node,include_attributes=False)

manifest=json.loads((DRAFT/'MANIFEST.json').read_text())
patch=(DRAFT/'HOST_V2.patch').read_bytes()
check('frozen patch pin',sha(patch)==PIN)
check('manifest source',manifest['source_sha']==SOURCE)
check('manifest patch',manifest['patch_sha256']==PIN)
check('exact three leaves',set(manifest['files'])=={'tests/test_geo261_timber_capacity_host.py','tests/geo300_scene_generator.py','tests/run_all.expected.json'})
old={};new={};reconstructed=''
for path,record in manifest['files'].items():
    data=(DRAFT/'candidate'/path).read_bytes();new[path]=data
    check(path+' bytes',len(data)==record['bytes'])
    check(path+' candidate pin',sha(data)==record['after_sha256'])
    if record['before_sha256'] is None:before=b''
    else:
        before=git(path)
        check(path+' source pin',sha(before)==record['before_sha256'])
    old[path]=before
    reconstructed+=''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),data.decode().splitlines(keepends=True),fromfile='a/'+path if before else '/dev/null',tofile='b/'+path))
check('entire patch reconstructs exact candidate',reconstructed.encode()==patch)
generator=Path(manifest['original_generator_path']).read_bytes()
check('generator exact original bytes',generator==new['tests/geo300_scene_generator.py'])
check('generator parse only',isinstance(ast.parse(generator),ast.Module))
hostpath='tests/test_geo261_timber_capacity_host.py'
before=old[hostpath];after=new[hostpath];bm=methods(before);am=methods(after);text=after.decode()
old_tests=[name for name in bm if name.startswith('test_')]
new_tests=[name for name in am if name.startswith('test_')]
check('old method names manifest',old_tests==manifest['methods_before'])
check('new method names manifest',new_tests==manifest['methods_after'])
check('five old methods retained',len(old_tests)==5 and set(old_tests)<=set(new_tests))
check('exact seven actual AST methods',len(new_tests)==7)
for name in ('setUpClass','reject_unchanged','test_actual_host_independent_admission_storage_and_scratch_values','test_each_real_declaration_retains_legacy_64_and_admits_up_to_512','test_real_bridge_guard_withdrawal_uses_safe_missing_id_then_restores','test_real_host_compile_contract_rejects_each_drifted_capacity'):
    check('original AST preserved '+name,normalize(bm[name])==normalize(am[name]))
check('sentinel only helper rename',textpart(before,bm['capacity_first_sentinel']).replace('self.load_full(bridge)','self.populate_full(bridge)')==textpart(after,am['capacity_first_sentinel']))
oldreg=json.loads(old['tests/run_all.expected.json']);newreg=json.loads(new['tests/run_all.expected.json'])
before_count=oldreg['suites']['py:test_geo261_timber_capacity_host']['count']
after_count=newreg['suites']['py:test_geo261_timber_capacity_host']['count']
check('expected precise five to seven',before_count==5 and after_count==7)
newreg['suites']['py:test_geo261_timber_capacity_host']['count']=5
check('all other registry data unchanged',newreg==oldreg)
check('expected only count bytes',old['tests/run_all.expected.json'].replace(b'"py:test_geo261_timber_capacity_host": {\n      "mode": "count",\n      "count": 5,',b'"py:test_geo261_timber_capacity_host": {\n      "mode": "count",\n      "count": 7,')==new['tests/run_all.expected.json'])
withdrawals=json.loads((DRAFT/'EXACT_WITHDRAWALS.json').read_text())
check('three separate withdrawal regions',set(withdrawals)=={'count','population','unplaced_replay'})
for name,row in withdrawals.items():
    check(name+' unique forward region',text.count(row['after'])==1)
    check(name+' withdrawal differs',row['before']!=row['after'])
    withdrawn=text.replace(row['after'],row['before'])
    check(name+' standalone variant parses',isinstance(ast.parse(withdrawn),ast.Module))
    check(name+' exact restoration',withdrawn.replace(row['before'],row['after'])==text)
check('count uses declaration source',all(token in textpart(after,am['assert_count']) for token in ['bridge.command("objects")','response["timbers"]','bridge.command("dump")','line.startswith("timber ")','list(range(1,count+1))','line.startswith("place ")']))
check('I9 refusal explicit twice',text.count('self.assertIn("I9",refused["error"])')==2)
check('unplaced rollback explicit twice',all(x in text for x in ['unplaced-load-must-rollback','unplaced-replay-load-must-rollback']))
check('unplaced replay only skips blank/comments','if not line.strip() or line.lstrip().startswith("#"):continue' in textpart(after,am['test_full_capacity_redeclaration_replay_and_rejected_edit_preserve_history']))
batch=textpart(after,am['placed_batch'])
check('raw protocol binary stdin/stdout','_bridge.run_once(payload.encode("utf-8"),text=False,bridge=self.bridge,timeout=600)' in batch)
check('complete protocol rows counted','self.assertEqual(len(commands),len(rows),label)' in batch)
check('command labels distinct','len({name for name,_ in commands})' in batch)
check('600 seconds original P189 source',"default=600.0" in Path('/tmp/train337-final-p52-p189-prep/p189/scale_compare2.py').read_text())
geometry=textpart(after,am['assert_placed_geometry'])
check('geometry uses DSL not generator rectangle',all(s in geometry for s in ['for line in text.splitlines():','rectangles={}','lhs,rhs=rectangles[int(left[1:])],rectangles[int(right[1:])]']) and 'meta[' not in geometry)
check('exact length direction and axis',all(s in geometry for s in ['self.assertEqual(direction,geometry["dir"])','geometry["axes"][0]','geometry["length"]']))
check('normal and right hand width axis',all(s in geometry for s in ['geometry["axes"][1]','geometry["axes"][2]','[0,0,1]']))
check('corners bounded and nonoverlap',all(s in geometry for s in ['self.assertLess(rect[0],rect[2])','self.assertGreaterEqual(rect[0],0)','self.assertLessEqual(rect[2],width)','self.assertFalse(left[0]<right[2]','for along in (0,1) for across in (0,1)','self.assertEqual(rectangles[identifier],actual']))
check('placed N64 and N512 retained','for count in (64,512):' in text)
check('fresh canonical raw equality','self.assertEqual(first_raw,second_raw,' in text)
check('dump byte and definition equivalence',all(s in text for s in ['rows["dump"]["text"].encode("utf-8"),first["dump"]["text"].encode("utf-8")','rows["dump"]["definition_sha256"],first["dump"]["definition_sha256"]']))
history=textpart(after,am['test_real_placed_512_sequential_replay_and_safe_513_history'])
check('history exact rejection complete dumps',all(s in history for s in ['self.assertEqual(rows["dump"],rows["after-513"])','self.assertEqual(rows["dump"],rows["after-missing"])','self.assertEqual(rows["undone"],rows["after-pending-redo"])']))
check('history validates final geometry','self.assert_placed_geometry(512,text,rows["final-dump"],rows["final-objects"],rows["final-references"])' in history)
check('R18 exact target and newline preservation',all(s in history for s in ['# R18 角材 ','splitlines(keepends=True)','self.assertEqual(1,']))
bridge=git('tests/_bridge.py').decode()
check('binary run_once plumbing preserves raw','if text:\n        kwargs.update(text=True, encoding=\'utf-8\')' in bridge)
check('run_once rejects abnormal termination','if type(p.returncode) is int and p.returncode != 0:' in bridge)
refs=git('geometry-web/reference_bridge.inc').decode()
check('references excludes unplaced actual API','if (!w->wood.timbers[i].placed) continue;' in refs)
check('reference payload no edit revision', 'sourceFingerprint' in refs and 'revision' not in refs)
refdump=git('geometry-core/references.inc').decode()
check('canonical actual R18 annotation', '# R18 角材 %u:' in refdump)
member=git('geometry-templates/woodworking/native/member_reference.c').decode()
check('existing frame actual right handed','GeoVector3 a=geo_vector_cross(b,length);' in member)
result=dict(scope='Small read-only static review only; no subject import, generator execution, C, browser or Git writes',source_sha=SOURCE,patch_sha256=PIN,checks=len(checks),passed=sum(c['ok'] for c in checks),failed=sum(not c['ok'] for c in checks),findings=[c for c in checks if not c['ok']],limitations=['All C, formal 7 methods, three correction withdrawal/restoration executions and placed 512 acceptance remain UNRUN.','Original 600-second P189 ceiling reused only for new batch cases; original old method limits and seven ABI controls preserved.','Initial v3 left-handed width-axis gap and v4 R18 leaf deletion expected-text error were reported and corrected in v5; no earlier static approval supersedes this candidate.','Stack highwater exploration plan is not runtime evidence.'])
(HERE/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
(HERE/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(result['failed']))
