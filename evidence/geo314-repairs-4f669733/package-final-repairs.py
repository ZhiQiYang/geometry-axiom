import hashlib,json,pathlib,tarfile,shutil
base=pathlib.Path('/workspace/geo314-work');out=pathlib.Path('/tmp/g261-next314/evidence/geo314-repairs-4f669733')
groups={'assembly-repair.tar.gz':['assembly-repair-001','run_assembly_repair.py','assembly-repair-001.stdout.raw','assembly-repair-001.stderr.raw'],'environment-repair.tar.gz':['environment-repair-001','run_graph_environment_retry.py','main-fixture-prereqs-001','materialize_native_fixture_prereqs.py'],'architecture-diagnostic.tar.gz':['architecture-diagnostic-001','run_architecture_diagnostic.py']}
p=out/'PUBLICATION.json';d=json.loads(p.read_text())
for name,paths in groups.items():
 with tarfile.open(out/name,'w:gz',compresslevel=1) as archive:
  for rel in paths:
   q=base/rel;assert q.exists();archive.add(q,arcname=rel,recursive=True)
 q=out/name;row={'path':name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()};d['files']=[r for r in d['files'] if r['path']!=name]+[row];print(row)
d['scopes']={'candidate_reader':'P3=4f669733282613a6f1e4a627c448374716496daa, actualE=c0a2007898f544e658efa72b9b51528a03f7ce51','environment_node_graph':'detachedP2=291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6','architecture':'P3 same manifest/source, actualE=9f634cd061eecb595e42d8362e88697cb6c6378e','assembly_wrapper':'original judges0/0/0; outer1 retained, separate exact2187-source classification0; not an overall formal pass'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(__file__,out/'package-final-repairs.py')
