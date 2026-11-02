from pathlib import Path
import hashlib, importlib.util, json, os, shutil

L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
tool = Path('/workspace/train337-native-r2-terminal-collection/collect_terminal_native.py')
assert hashlib.sha256(tool.read_bytes()).hexdigest() == 'a320b22c40a17ad4191e02fd397bf3cd3094889cfdb6df0cadfae41da42ad002'
peer = Path('/workspace/train337-canvas-peer-resume/NATIVE_R2_COLLECTOR_STATIC_PEER.json')
assert hashlib.sha256(peer.read_bytes()).hexdigest() == '395a7efbae7b02577fe54ddc624f3563005f096d978dd1fea2d89e1ded89bbe5'
review = json.loads(peer.read_text())
assert review['exit_code'] == 0 and review['findings'] == []
cap_path = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cap_path.read_bytes()).hexdigest() == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('cap', cap_path)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)
out = Path('/workspace/train337-native-r2-terminal-collection-producer')
out.mkdir()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONOPTIMIZE', None)
rec = cap.Recorder(out, env, L)
argv = ['python3', '-B', str(tool)]
cap.dump(out / 'REQUEST.json', dict(sourceSHA=L, argv=argv,
    collectorSHA256=hashlib.sha256(tool.read_bytes()).hexdigest(),
    rootAuthorizedAfterTrueNativeTerminal=True,
    rootAndGlobalCacheRemainLeasedUntilCollectionAndPeerComplete=True,
    freeBefore={name: shutil.disk_usage(name).free for name in ['/workspace', '/tmp']},
    collectorOnly=True, subjectRerun=False))
row, stdout, stderr = rec.run(argv, cwd='/workspace', timeout=None, check=False,
    source_sha=L, source_variant='original-native-r2-terminal-receipt-collection')
cap.dump(out / 'RESULT.json', dict(sourceSHA=L, actual_exit=row['actual_process_returncode'],
    command=row, collectorOnly=True, subjectRerun=False))
print(json.dumps({'actual_exit': row['actual_process_returncode'], 'sourceSHA': L, 'producer': str(out)}))
raise SystemExit(row['actual_process_returncode'])
