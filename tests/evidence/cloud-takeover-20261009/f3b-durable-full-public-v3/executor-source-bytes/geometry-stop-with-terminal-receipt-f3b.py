from pathlib import Path
import datetime, hashlib, json, subprocess, sys, urllib.request

helper, root, port, output, gate_paths = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4]), sys.argv[5:]
assert not output.exists()
helper_path = Path(helper).resolve()
python = Path('/proc/self/exe').resolve()
gates = [json.loads((Path(p) / 'receipt.json').read_text()) for p in gate_paths]
assert all(g['before']['git']['head'] == 'f3b8285729b42cd22451c98cba1e2ec4514517f3' for g in gates)
assert all(g['before']['git']['status'] == '' for g in gates)
command = [str(python), str(helper_path), root, port, str(output)]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
assert output.is_dir(), run.stderr.decode(errors='replace')
(output / 'stop.stdout.raw.log').write_bytes(run.stdout)
(output / 'stop.stderr.raw.log').write_bytes(run.stderr)
identity = json.loads((output / 'identity.json').read_text())
pids = {identity['server']: 'owned server'}
pids.update({p: 'owned direct native bridge' for p in identity['children']})
for gate in gates:
    for role in ('node', 'browser'):
        record = gate.get('executionIdentity', {}).get(role, {})
        if record.get('pid'):
            pids[record['pid']] = 'actual test ' + role
for gate in gates:
    binding = gate.get('executionIdentity', {}).get('liveBinding') or {}
    for process in binding.get('processes', []):
        if process.get('pid'):
            pids[process['pid']] = process.get('role', 'actual full integration process')
states = []
for pid, role in pids.items():
    proc = Path('/proc') / str(pid)
    try:
        raw = (proc / 'stat').read_bytes()
        (output / ('proc-' + str(pid) + '.stat.raw')).write_bytes(raw)
        states.append({'pid': pid, 'role': role, 'exists': True,
                       'state': raw.decode().split(') ', 1)[1].split()[0],
                       'statSHA256': hashlib.sha256(raw).hexdigest()})
    except FileNotFoundError:
        states.append({'pid': pid, 'role': role, 'exists': False, 'state': 'absent-at-observation'})
try:
    response = urllib.request.urlopen('http://127.0.0.1:' + port + '/runtime', timeout=2)
    port_state = {'accepting': True, 'response': response.read().decode()}
except Exception as exc:
    port_state = {'accepting': False, 'rawError': repr(exc)}
files = [{'path': str(p.relative_to(output)), 'bytes': p.stat().st_size,
          'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(output.rglob('*')) if p.is_file()]
record = {'schema': 'geometry-root-owned-stop-terminal/1', 'startedUtc': started,
          'observedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'command': command, 'exitCode': run.returncode,
          'helperSHA256': hashlib.sha256(helper_path.read_bytes()).hexdigest(),
          'actualPython': str(python), 'actualPythonSHA256': hashlib.sha256(python.read_bytes()).hexdigest(),
          'wrapperSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'receiptSources': gate_paths, 'processObservations': states, 'portObservation': port_state,
          'rawFiles': files, 'productTestExecution': False,
          'note': 'Exact owned helper signal and immediate process observations; zombie is not absent. No historical process state is reconstructed.'}
(output / 'terminal-receipt.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
sys.exit(run.returncode)
