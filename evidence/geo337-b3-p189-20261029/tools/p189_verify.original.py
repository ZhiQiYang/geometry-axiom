#!/usr/bin/env python3
"""經鎖執行，沿 fix_verify.sh/scale_compare2.py 的三方方法，額外嚴格核對原始證據。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import shutil
import subprocess
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ['GEO261_P189_OUT'])
WORK = Path(os.environ['GEO261_P189_WORK'])
REPO = os.environ['GEO261_FINAL_REPO']
TOOLS = HERE
GEN = HERE / 'gen_scene.py'
SHAS = {'main': 'adbaebf9c73ea6801d7b4d5214e4b846b132923b',
        'base': '3e600772076465fc65a26ac09055028301c0fb0b',
        'fix': sys.argv[1]}
ENV = dict(os.environ, PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
           LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')


RUN_CAPTURE_INDEX = 0


def run(argv, *, cwd=None, data=None, timeout=1200):
    # 只補原始證據，不更動原 subprocess.run 參數、return 或非零 raise。
    global RUN_CAPTURE_INDEX
    RUN_CAPTURE_INDEX += 1
    capture = OUT / 'subcommands' / f'{RUN_CAPTURE_INDEX:06d}'
    capture.mkdir(parents=True, exist_ok=False)
    started = time.time()
    clock = time.monotonic()
    metadata = {'command': list(argv), 'cwd': str(Path(cwd).resolve()) if cwd is not None else os.getcwd(),
                'started_epoch_utc': started, 'timeout_seconds': timeout,
                'actual_process_returncode': None, 'timeout_expired': False,
                'environment': {key: ENV[key] for key in ('PATH', 'LANG', 'LC_ALL', 'PYTHONIOENCODING',
                                                         'PYTHONDONTWRITEBYTECODE') if key in ENV},
                'stdin': None, 'stdout_file': 'stdout.bin', 'stderr_file': 'stderr.bin'}
    if data is not None:
        (capture / 'stdin.bin').write_bytes(data)
        metadata['stdin'] = {'file': 'stdin.bin', 'bytes': len(data), 'sha256': digest(data)}
    (capture / 'request.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')

    def finish(stdout, stderr, **fields):
        stdout = stdout if stdout is not None else b''
        stderr = stderr if stderr is not None else b''
        (capture / 'stdout.bin').write_bytes(stdout)
        (capture / 'stderr.bin').write_bytes(stderr)
        metadata.update(fields, ended_epoch_utc=time.time(), seconds=time.monotonic() - clock,
                        stdout={'bytes': len(stdout), 'sha256': digest(stdout)},
                        stderr={'bytes': len(stderr), 'sha256': digest(stderr)})
        (capture / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')

    try:
        p = subprocess.run(argv, cwd=cwd, env=ENV, input=data, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        # subprocess.run 自行 kill/wait；例外沒有提供真實 rc，不能捏造 killed/124。
        finish(error.stdout, error.stderr, timeout_expired=True, exception_type=type(error).__name__,
               exception_message=str(error))
        raise
    except OSError as error:
        finish(None, None, exception_type=type(error).__name__, exception_message=str(error))
        raise
    finish(p.stdout, p.stderr, actual_process_returncode=p.returncode)
    if p.returncode:
        raise RuntimeError(f'指令失敗 {p.returncode}: {argv}\n{p.stderr[-1000:]!r}')
    return p


def git(*args):
    return run(['git', '-c', 'safe.directory=*', '-C', REPO, *args]).stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if OUT.exists() or WORK.exists():
        raise RuntimeError('拒絕覆蓋既有收據或工作目錄')
    OUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    started = time.time()
    provenance = {'shas': SHAS, 'compiler': run(['gcc', '--version']).stdout.decode().splitlines()[0],
                  'generator_sha256': digest(GEN.read_bytes()),
                  'verification_script_sha256': digest(Path(__file__).read_bytes()),
                  'timing_script_sha256': digest((TOOLS / 'scale_compare2.py').read_bytes()),
                  'binaries_sha256': {},
                  'method': 'gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm; stack=16384; N=16,32,48,64; 3 rounds; order main/base/fix then reverse'}
    (OUT / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    for label, sha in SHAS.items():
        assert git('rev-parse', sha).decode().strip() == sha
        target = WORK / label
        target.mkdir()
        if label in ('main','base'):
            provider_path=TOOLS/'REFERENCE_BASELINES.json'
            assert digest(provider_path.read_bytes()) == '68181e2b017ca04a9fc854100fdb849b2a722b127338b320082b9ed0c5e63ad0'
            provider=json.loads(provider_path.read_bytes())
            reference=provider['references'][label]
            assert reference['source_sha']==sha
            preserved=OUT/'reference-provenance'/label
            preserved.mkdir(parents=True)
            for role in ('original_provenance','original_receipt'):
                item=provider[role];body=Path(item['path']).read_bytes()
                assert digest(body)==item['sha256']
                (preserved/(role+'.json')).write_bytes(body)
            prior=json.loads(Path(provider['original_provenance']['path']).read_bytes())
            assert prior['shas'][label]==sha and prior['binaries_sha256'][label]==reference['binary_sha256']
            for item in reference['original_metadata']:
                path=Path(item['path']);body=path.read_bytes()
                assert len(body)==item['bytes'] and digest(body)==item['sha256']
                (preserved/(path.parent.name+'-'+path.name)).write_bytes(body)
            commands=[Path(reference['original_metadata'][0]['path']).parent.parent/f'{n:06d}' for n in reference['command_numbers']]
            for index,folder in enumerate(commands):
                receipt=json.loads((folder/'result.json').read_bytes())
                assert receipt['actual_process_returncode']==0 and receipt['timeout_expired'] is False
                for stream in ('stdout','stderr'):
                    body=(folder/(stream+'.bin')).read_bytes()
                    assert len(body)==receipt[stream]['bytes'] and digest(body)==receipt[stream]['sha256']
                    # Keep complete baseline streams in a lossless compressed representation.
                    import gzip
                    compressed=gzip.compress(body,mtime=0)
                    destination=preserved/(folder.name+'-'+stream+'.bin.gz')
                    destination.write_bytes(compressed)
                    assert gzip.decompress(compressed)==body
                    provenance.setdefault('reference_raw_files',[]).append({'original_source':str(folder/(stream+'.bin')),'source_sha':sha,'raw_bytes':len(body),'raw_sha256':digest(body),'representation':'lossless gzip, decompression equals original bytes','stored_file':str(destination),'stored_bytes':len(compressed),'stored_sha256':digest(compressed)})
                if index==0:
                    assert receipt['command'][-2:]==['rev-parse',sha]
                    assert (folder/'stdout.bin').read_bytes().decode().strip()==sha
                elif index==1:
                    assert 'archive' in receipt['command'] and sha in receipt['command']
                else:
                    assert receipt['command']==['gcc','-std=c11','-O2','geometry-web/web_bridge.c','-o','bridge','-lm']
            source=Path(reference['binary_path']);before=source.stat();body=source.read_bytes()
            assert len(body)==reference['binary_bytes'] and digest(body)==reference['binary_sha256']
            shutil.copy2(source,target/'bridge')
            assert (target/'bridge').read_bytes()==body
            after=source.stat()
            assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
            provenance['binaries_sha256'][label]=digest(body)
            provenance.setdefault('reference_build_roles',{})[label]={'role':'reused exact original baseline ELF; no new compile claimed','provider_sha256':digest(provider_path.read_bytes()),'source_sha':sha,'original_compiler':prior['compiler'],'binary_sha256':digest(body)}
            (OUT/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
            print(f'{label} {sha} 沿用已核原基準 ELF（未重新編譯）',flush=True)
            continue
        root_names = set(git('ls-tree', '-z', '--name-only', sha).decode().split('\0'))
        paths = [p for p in ('current_geometry.c', 'geometry-core', 'geometry-app', 'geometry-templates', 'geometry-web') if p in root_names]
        assert {'current_geometry.c', 'geometry-web'} <= set(paths)
        args = ['archive', '--format=tar', sha, '--', *paths,
                ':(exclude)geometry-core/domain-decoupling', ':(exclude)geometry-web/docs', ':(exclude)geometry-web/prototypes',
                ':(exclude)geometry-web/vendor', ':(exclude)geometry-web/node_modules']
        archive = git(*args)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(target, filter='data')
        cmd = ['gcc', '-std=c11', '-O2', 'geometry-web/web_bridge.c', '-o', 'bridge', '-lm']
        p = run(cmd, cwd=target)
        (OUT / f'build-{label}.log').write_bytes(p.stdout + p.stderr)
        provenance['binaries_sha256'][label] = digest((target / 'bridge').read_bytes())
        (OUT / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
        print(f'{label} {sha} 建置完成', flush=True)
    scenes = []
    for n in (16, 32, 48, 64):
        data = run(['python3', str(GEN), str(n), '--family', 'single']).stdout
        scenes.append((f's{n}.scene', data))
    for name in git('ls-tree', '-z', '--name-only', SHAS['base']).decode().split('\0'):
        if name.endswith('.scene'):
            scenes.append(('repo-' + name, git('show', SHAS['base'] + ':' + name)))
    dumps = []
    for name, data in scenes:
        scene = WORK / name
        scene.write_bytes(data)
        raw = {}
        for label in ('base', 'fix'):
            p = run(['bash', '-c', 'ulimit -s 16384; exec "$1"', 'x', str(WORK / label / 'bridge')],
                    cwd=WORK, data=f'loadfile {scene}\ndump\n'.encode(), timeout=900)
            (OUT / f'{name}-{label}.stdout').write_bytes(p.stdout)
            (OUT / f'{name}-{label}.stderr').write_bytes(p.stderr)
            lines = p.stdout.splitlines()
            assert len(lines) == 2, (name, label, lines[:2])
            responses = [json.loads(line) for line in lines]
            assert all(isinstance(r, dict) for r in responses), (name, label)
            assert isinstance(responses[0].get('ok'), bool) and responses[1].get('ok') is True, (name, label, responses)
            # repo-root 包含刻意拒絕的回歸場景；沿原腳本比較完整 load 回覆及 dump，
            # 分開記錄拒絕，不冒充成功載入。四個生成效能場景必須確實載入成功。
            if not name.startswith('repo-'):
                assert responses[0]['ok'] is True, (name, label, responses[0])
            raw[label] = p.stdout
        assert raw['base'] == raw['fix'], f'dump 不同：{name}'
        dumps.append({'scene': name, 'scene_sha256': digest(data), 'bytes': len(raw['base']), 'stdout_sha256': digest(raw['base']),
                      'load_ok': responses[0]['ok'], 'load_response': responses[0], 'dump_ok': True, 'identical': True})
        print(f'{name} loadfile+dump 逐位元組相同', flush=True)
    (OUT / 'dump-equivalence.json').write_text(json.dumps(dumps, ensure_ascii=False, indent=2) + '\n')
    timing = ['python3', str(TOOLS / 'scale_compare2.py'), str(WORK), str(OUT),
              *[f'{label}={WORK / label}' for label in SHAS], '--ns', '16,32,48,64', '--reps', '3', '--gen', str(GEN)]
    p = run(timing, timeout=1800)
    (OUT / 'timing.log').write_bytes(p.stdout + p.stderr)
    print(p.stdout.decode(), flush=True)
    with (OUT / 'samples.tsv').open() as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    assert len(rows) == 36, len(rows)
    assert all(r['status'] == 'ok' and r['ok'] == 'True' for r in rows), rows
    raw_samples = json.loads((OUT / 'loadfile-samples.json').read_text())
    assert len(raw_samples) == 36, len(raw_samples)
    wanted_samples = {(n, r, side) for n in (16, 32, 48, 64) for r in (0, 1, 2) for side in SHAS}
    actual_samples = {(sample['n'], sample['round'], sample['side']) for sample in raw_samples}
    assert actual_samples == wanted_samples and len(actual_samples) == len(raw_samples)
    for sample in raw_samples:
        assert type(sample['actual_process_returncode']) is int and sample['actual_process_returncode'] == 0
        assert sample['timeout_expired'] is False and sample['load_ok'] is True
        assert sample['command'][-1] == str(WORK / sample['side'] / 'bridge')
        for evidence in sample['files'].values():
            payload = (OUT / evidence['path']).read_bytes()
            assert len(payload) == evidence['bytes'] and digest(payload) == evidence['sha256']
        stdout = (OUT / sample['files']['stdout.bin']['path']).read_bytes()
        response = json.loads(stdout.splitlines()[0])
        assert isinstance(response, dict) and response.get('ok') is True
    ratios = []
    for n in (16, 32, 48, 64):
        medians = {}
        for label in SHAS:
            selected = [r for r in rows if r['n'] == str(n) and r['side'] == label]
            assert {r['round'] for r in selected} == {'0', '1', '2'} and len(selected) == 3
            medians[label] = statistics.median(float(r['seconds']) for r in selected)
        ratio = medians['fix'] / medians['main']
        ratios.append({'n': n, 'medians': medians, 'fix_main': ratio, 'pass': ratio <= 2})
    receipt = {'schema': 'geo261-p189-final/1', **provenance, 'dump_count': len(dumps), 'samples': len(rows),
               'ratios': ratios, 'pass': all(r['pass'] for r in ratios), 'seconds': time.time() - started}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    if not receipt['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
