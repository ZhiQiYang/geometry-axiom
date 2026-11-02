from pathlib import Path
import ast,copy,hashlib,json,subprocess,sys,unittest
D=Path(__file__).parent;ROOT=Path('/workspace/geometry-axiom');TOOL=D/'refresh_architecture_zero_delta.py'
src=TOOL.read_text();tree=ast.parse(src);names={'ADDED','HISTORICAL_PIN','CURRENT_PIN','PROBE_PIN','EXPECTED_CHANGED_INPUT'}
body=[]
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in {'H','LF','validate_manifests'}:body.append(n)
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets):body.append(n)
ns={'json':json,'hashlib':hashlib,'copy':copy};exec(compile(ast.Module(body=body,type_ignores=[]),str(TOOL),'exec'),ns)
def readgit(sha):
 path='geometry-core/domain-decoupling/product-architecture.json';argv=['git','-C',str(ROOT),'show',sha+':'+path]
 p=subprocess.run(argv,capture_output=True);(D/(sha[:8]+'.manifest.json')).write_bytes(p.stdout);(D/(sha[:8]+'.stderr.bin')).write_bytes(p.stderr)
 (D/(sha[:8]+'.command.json')).write_text(json.dumps({'argv':argv,'exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'source_sha':sha},indent=2)+'\n');assert p.returncode==0;return p.stdout
current=readgit('a22df116c7e9f6b7d074451f1c8052d59e7e4f3e');historical=readgit('ca7838e0f4950452b9befcf40899d606db9b81fa')
if len(sys.argv)>1:
 assert sys.argv[1] in {'fixed','withdrawn','restored'}
 if sys.argv[1]=='withdrawn':
  # Exact old tool's single delta assertion; same current/previous 937 bytes.
  manifest=json.loads(current);previous_manifest=json.loads(current);ADDED=ns['ADDED']
  assert set(manifest['policy']['forbiddenIdentifiers'])-set(previous_manifest['policy']['forbiddenIdentifiers'])==ADDED
 else:ns['validate_manifests'](current,current,historical)
 print('synthetic unchanged-manifest contract passed');sys.exit(0)
class Contracts(unittest.TestCase):
 def test_unchanged_actual_937_accepted(self):self.assertEqual(len(ns['validate_manifests'](current,current,historical)['policy']['forbiddenIdentifiers']),928)
 def test_old928_is_not_previous937(self):
  with self.assertRaises(AssertionError):ns['validate_manifests'](current,historical,historical)
 def test_historical937_rejected(self):
  with self.assertRaises(AssertionError):ns['validate_manifests'](current,current,current)
 def test_previous_byte_change_rejected(self):
  with self.assertRaises(AssertionError):ns['validate_manifests'](current,current+b'\n',historical)
 def test_current_policy_change_rejected(self):
  m=json.loads(current);m['policy']['forbiddenIdentifiers'].append('wood_unreviewed');raw=json.dumps(m).encode()
  with self.assertRaises(AssertionError):ns['validate_manifests'](raw,raw,historical)
 def test_trust_change_rejected(self):
  m=json.loads(current);m['sources'][0]['layer']='K' if m['sources'][0]['layer']!='K' else 'W';raw=json.dumps(m).encode()
  with self.assertRaises(AssertionError):ns['validate_manifests'](raw,raw,historical)
 def test_historical_tamper_rejected(self):
  with self.assertRaises(AssertionError):ns['validate_manifests'](current,current,historical+b'\n')
 def test_nine_exact_and_prior_guard_preserved(self):self.assertEqual(len(ns['ADDED']),9);self.assertIn("assert prior['sourceBaseHead']==a.prior_source",src)
 def test_only_w_input_changed_guard(self):self.assertEqual(ns['EXPECTED_CHANGED_INPUT'],'geometry-templates/woodworking/native/contact_world.c');self.assertEqual(src.count("assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT]"),2)
 def test_full_inventory_original_gates_not_removed(self):
  for x in ["len(declared)==len(set(declared))==604","assert sorted(tree)==declared","snapshot()==before","zip(results[1:],[205,18])","len(scan['edges'])==798"]:self.assertIn(x,src)
 def test_fresh_out_and_fresh_proofs(self):
  for x in ["not O.exists()","source_sha=F","withdrawn.write_bytes(historical_raw)","'newIdentifiers':0","'guardIdentifiersRetested':9","createdUtc=datetime.datetime.now"]:self.assertIn(x,src)
 def test_no_prior_judgments_inherited(self):
  x=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='receipt' for t in n.targets))
  self.assertIsInstance(x.value,ast.DictComp);keys=ast.literal_eval(x.value.generators[0].iter)
  self.assertEqual(keys,['schema','hashMode','inputClosureHashSerialization','inputClosureExcludes','inputClosureExclusionReason','notClaimed'])
 def test_original_tool_unmodified(self):self.assertEqual(hashlib.sha256(Path('/workspace/refresh_geo337_final_architecture_20261024.py').read_bytes()).hexdigest(),'61aa806e619baa5f0b141d2a5026fe8146691e12406b112cb4b7f765e9db37b0')
 def test_original_probe_pin(self):self.assertEqual(hashlib.sha256(Path('/workspace/geo337-U-architecture-policy-proof-20261024/probe.py').read_bytes()).hexdigest(),ns['PROBE_PIN'])
 def test_no_c_or_product_judge_from_test(self):self.assertEqual([n.name for n in body if isinstance(n,ast.FunctionDef)],['H','LF','validate_manifests'])
unittest.main(verbosity=2)
