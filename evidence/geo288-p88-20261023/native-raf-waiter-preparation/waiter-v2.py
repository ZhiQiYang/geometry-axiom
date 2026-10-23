"""Wait for the three formal canvas processes, then run one frozen diagnostic."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
F = '3d681636902371ecc528b20f51eea33e272581c9'
REPO = Path('/tmp/g288p88final-3d681636')
SEQUENCE = HERE / 'final-3d681636/sequence-receipt.json'
FINAL_LAUNCH = HERE / 'final-3d681636-launch.exit.json'
TOOLS = HERE / 'p88-native-raf-tools-v2'
PREP = 'a6f6dc0e5f02b1090b01216de008be2864a48aa26f5ee09d48f086196b7e127b'
OUTER = Path('/workspace/geo261-environment/execute_f_extra.py')
OUTER_HASH = '68256d90e597fe52807637e3603b7392dd09e9a5342909adc54d21fa4cba2928'
FORMAL_DRIVER = HERE / 'run_final_canvas_three.py'
FORMAL_HASH = '98025b205e42280ba00bff6ae5299ff8c169ac77a9a68ab404c3a6808d37a05e'
OUT = Path('/tmp/g288p88r')
PREFIX = HERE / 'native-raf-controlled-v2-launch'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def h(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def write(suffix, data):
    PREFIX.with_suffix(suffix).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    need(not sys.flags.optimize and os.environ.get('PYTHONOPTIMIZE') in (None, '', '0'), 'No optimized guards')
    for suffix in ('.wait.json', '.request.json', '.stdout', '.stderr', '.exit.json'):
        need(not PREFIX.with_suffix(suffix).exists(), 'Launcher output must be fresh: ' + suffix)
    command = ['env', '-u', 'NODE_OPTIONS', '-u', 'PYTHONOPTIMIZE', 'python3', '-B', str(OUTER),
        '--label', 'p88-native-raf-controlled-v2', '--sha', F, '--repo', str(REPO),
        '--outer-root', str(HERE / 'outers'), '--', 'python3', '-B', str(TOOLS / 'run_proof.py'),
        '--repo', str(REPO), '--sha', F, '--out', str(OUT), '--heavy-lock', '/tmp/g261r3/heavy.lock',
        '--mode', 'controlled', '--job', 'grid', '--candidate', str(TOOLS / 'SOURCE_VARIANTS.json')]
    metadata = {'sha': F, 'command': command, 'cwd': str(REPO), 'waiter_sha256': h(Path(__file__)),
        'started_waiting_utc': utc(), 'preparation_sha256': PREP,
        'environment_input': {k: os.environ.get(k) for k in ('PATH', 'LANG', 'LC_ALL', 'NODE_OPTIONS', 'PYTHONOPTIMIZE', 'PYTHONDONTWRITEBYTECODE')},
        'environment_removals': ['NODE_OPTIONS', 'PYTHONOPTIMIZE'],
        'authorization': 'Root granted one fixed/withdrawn/restored diagnostic after all three formal canvas terminal processes, regardless of red or green; no automatic retry.',
        'scope': 'Controlled native-rAF diagnostic only: original grid bootstrap and full P88; two other grid modules explicitly omitted. This is not a formal canvas/grid gate.',
        'heavy_process_started': False}
    write('.wait.json', metadata)
    print('Waiting for all three formal canvas terminal processes; no heavy process started.', flush=True)
    code = 2
    child_actual_exit = None
    try:
        while True:
            try:
                sequence = json.loads(SEQUENCE.read_text())
                launch = json.loads(FINAL_LAUNCH.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(10)
                continue
            if type(sequence.get('driver_exit_code')) is int and type(launch.get('actual_process_returncode')) is int:
                break
            time.sleep(10)
        need(sequence['sha'] == F and launch['sha'] == F and Path(sequence['source']).resolve() == REPO, 'Formal sequence source identity differs')
        need(sequence['driver_exit_code'] == launch['actual_process_returncode'], 'Formal terminal process and driver exits differ')
        need(sequence['all_three_completed'] is True and len(sequence['runs']) == 3
            and {r['index'] for r in sequence['runs']} == {1, 2, 3}
            and all(r['process_completed'] is True for r in sequence['runs']), 'All three formal processes must terminate')
        before, after = sequence['source_before'], sequence['source_after']
        need(before is not None and after is not None and before['head'] == F and after['head'] == F
            and before['status'] == '' and after['status'] == '' and before['index'] == after['index'], 'Final source-after identity is not clean and explicit')
        for row in sequence['runs']:
            need(row['sha'] == F and h(Path(row['receipt'])) == row['receipt_sha256'], 'Formal original receipt hash differs')
        for stream in ('stdout', 'stderr'):
            need(h(HERE / ('final-3d681636-launch.' + stream)) == launch[stream + '_sha256'], 'Formal launcher stream hash differs')
        need(h(FORMAL_DRIVER) == FORMAL_HASH and h(OUTER) == OUTER_HASH, 'Frozen formal/outer driver differs')
        need(h(TOOLS / 'PREPARATION.json') == PREP, 'Peer-reviewed diagnostic preparation differs')
        preparation = json.loads((TOOLS / 'PREPARATION.json').read_text())
        need(preparation['sha'] == F, 'Diagnostic preparation SHA differs')
        for relative, expected in preparation['files'].items():
            need(h(TOOLS / relative) == expected, 'Frozen diagnostic file differs: ' + relative)
        need(not OUT.exists(), 'Diagnostic output must be fresh')
        metadata.update(formal_sequence_sha256=h(SEQUENCE), formal_launch_exit_sha256=h(FINAL_LAUNCH),
            formal_driver_exit=sequence['driver_exit_code'], formal_runs=sequence['runs'],
            formal_source_before=before, formal_source_after=after,
            preparation_files=preparation['files'], started_utc=utc())
        write('.request.json', metadata)
        print('All three formal canvas processes ended; starting the one frozen native-rAF diagnostic.', flush=True)
        with PREFIX.with_suffix('.stdout').open('xb') as stdout, PREFIX.with_suffix('.stderr').open('xb') as stderr:
            process = subprocess.Popen(command, cwd=REPO, stdout=stdout, stderr=stderr)
            metadata.update(heavy_process_started=True, pid=process.pid)
            write('.request.json', metadata)
            child_actual_exit = process.wait()
            metadata['actual_process_returncode'] = child_actual_exit
            code = child_actual_exit
        metadata.update(actual_process_returncode=child_actual_exit,
            stdout_sha256=h(PREFIX.with_suffix('.stdout')), stderr_sha256=h(PREFIX.with_suffix('.stderr')))
    except BaseException:
        code = 2
        metadata.update(launcher_error=traceback.format_exc(), actual_process_returncode=child_actual_exit)
    metadata.update(ended_utc=utc(), launcher_exit_code=code)
    write('.exit.json', metadata)
    print(json.dumps({'launcher_exit_code': code, 'actual_process_returncode': metadata.get('actual_process_returncode'),
        'heavy_process_started': metadata['heavy_process_started'], 'receipt': str(PREFIX.with_suffix('.exit.json'))}), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
