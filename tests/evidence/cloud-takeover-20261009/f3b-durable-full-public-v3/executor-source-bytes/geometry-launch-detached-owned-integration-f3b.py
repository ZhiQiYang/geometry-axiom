from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys

mode, stem = sys.argv[1:]
assert mode in ('cdp', 'space')
assert Path(stem).name == stem
root = Path('<workspace-path>')
head = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == head
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True) == ''
controller = Path('<workspace-path>')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(controller) == '5a33421c7b84919c212ebf3c444bed22a950177462cd87c073e4d99fdda0e5ae'
out = Path('<workspace-path>') / (stem + '-detached-launch')
assert not out.exists()
out.mkdir()
python = Path('/proc/self/exe').resolve()
command = [str(python), str(controller), mode, stem]
with (out / 'controller.stdout.raw.log').open('xb') as stdout, (out / 'controller.stderr.raw.log').open('xb') as stderr:
    child = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True, close_fds=True)
pid = child.pid
proc = Path('/proc') / str(pid)
raw = (proc / 'stat').read_bytes()
(out / 'launched-controller.stat.raw').write_bytes(raw)
record = {'schema': 'geometry-detached-owned-integration-launch/1',
          'startedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'fullSHA': head, 'dirty': '', 'mode': mode, 'controllerCommand': command,
          'actualControllerPID': pid, 'actualControllerPGID': os.getpgid(pid), 'actualControllerSID': os.getsid(pid),
          'controllerSourceSHA256': sha(controller), 'launcherCommand': sys.argv,
          'actualLauncherPID': os.getpid(), 'actualPython': str(python), 'actualPythonSHA256': sha(python),
          'launcherSourceSHA256': sha(__file__), 'launchExitCode': 0,
          'purpose': 'Persist owned controller outside ephemeral tool process group so original identity/census/exit receipts can seal; unchanged canonical tests, golden, source and scope.',
          'productGateExitCodeAtLaunch': None, 'productCompletionAtLaunch': 'pending',
          'rawFiles': [{'path': str(p.relative_to(out)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(out.iterdir()) if p.is_file()]}
assert record['actualControllerPGID'] == pid and record['actualControllerSID'] == pid
(out / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'detachedOwnedControllerPID': pid, 'fullSHA': head, 'mode': mode, 'launchReceipt': str(out / 'launch.json')}))
