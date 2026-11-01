#!/usr/bin/env python3
"""GEO-323 Linux驗收：固定乾淨SHA、原裁判、原始收據，無Git寫入。"""
import argparse
import contextlib
import difflib
import fcntl
import gzip
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import resource
import runpy
import shutil
import sys
import tarfile
import traceback

import geo323_record as capture

HERE = Path(__file__).resolve().parent
SCOPES = ('current_geometry.c', 'geometry-core', 'geometry-app', 'geometry-templates', 'geometry-web')
EXCLUDES = ('geometry-core/domain-decoupling', 'geometry-web/docs', 'geometry-web/prototypes',
            'geometry-web/vendor', 'geometry-web/node_modules')
SYMBOLS = ('geo_eval_source', 'geo_eval_depend', 'wd_read', 'contact_order',
           'wood_contact_collect_stops', 'app_reference_member_footprint')
REQUIRED = ('py:test_geo261_source_index', 'py:test_geo261_candidate_cache',
            'py:test_geo261_graph_product', 'py:test_geo261_assembly_graph_product',
            'py:test_bridge_integrity', 'c:integrity', 'core:run_tests',
            'py:test_geo261_load_residual')
STAGES = ('prepare', 'build', 'compare', 'perf', 'profile', 'required-eight', 'pf3', 'native')


class Tee:
    def __init__(self, original, file):
        self.original, self.file = original, file
    def write(self, text):
        self.file.write(text)
        self.file.flush()
        return self.original.write(text)
    def flush(self):
        self.file.flush()
        self.original.flush()


def load_module():
    spec = importlib.util.spec_from_file_location('geo323_verify_linux', HERE / 'verify_linux.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_environment(args):
    env = os.environ.copy()
    removed = []
    for key in list(env):
        if key.startswith('GEOMETRY_') or key in ('PYTHONOPTIMIZE', 'PYTHONPATH', 'PYTHONSTARTUP', 'NODE_OPTIONS'):
            removed.append(key)
            del env[key]
    env.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', TMPDIR=str(args.out / 'tmp'),
               PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
               GITHUB_SHA=args.sha, GITHUB_WORKSPACE=str(args.repo),
               GEO323_BASE_SHA=args.base, GEO323_MAIN_SHA=args.main)
    return env, removed


class Session:
    def __init__(self, args, recorder):
        self.a, self.r = args, recorder
        self.path = args.out / 'receipt.json'
        self.work, self.evidence = args.out / 'work', args.out / 'evidence'
        self.work.mkdir(exist_ok=True)
        self.evidence.mkdir(exist_ok=True)
        self.record = json.loads(self.path.read_text()) if self.path.exists() else {
            'schema': 'geo323-linux-acceptance/1', 'source_sha': args.sha,
            'source_repo': str(args.repo), 'base': args.base, 'main': args.main,
            'started_utc': capture.utc(), 'stages': {}, 'errors': [],
            'quantitative_targets': {}, 'status': '執行中',
            'ABC_method': {'A': 'base/fix loadfile+dump完整stdout逐bytes及stderr',
                           'B': '每次seal完整ordered node/edge/descriptor/value序列',
                           'C': '每scene/process五guard總呼叫數；不是每seal五計數'},
            'original_judges_modified': False,
            'policy': '沒有挑綠重跑；每個stage僅執行一次，任何原紅保留；未完成一律null。',
        }
        if self.record['source_sha'] != args.sha or self.record['source_repo'] != str(args.repo):
            raise RuntimeError('既有收據的repo/SHA不符，請使用新的out')
        if self.record['base'] != args.base or self.record['main'] != args.main:
            raise RuntimeError('既有收據的base/main SHA不符，請使用新的out')
        tools = {p.relative_to(HERE).as_posix(): capture.sha(p.read_bytes())
                 for p in sorted(HERE.rglob('*')) if p.is_file()
                 and '__pycache__' not in p.parts
                 and p.name not in ('TOOLKIT_MANIFEST.json', 'SHA256SUMS')}
        if self.record.get('tool_hashes', tools) != tools:
            raise RuntimeError('同out的工具bytes已改變，拒絕混用不同driver')
        self.record['tool_hashes'] = tools
        if not (args.out / 'tools-frozen').exists():
            shutil.copytree(HERE, args.out / 'tools-frozen', ignore=shutil.ignore_patterns('__pycache__'))
        self.v = load_module()

    def git(self, *args):
        p = self.r.run(['git', '-C', str(self.a.repo), *args], cwd=self.a.repo)
        if p.returncode:
            raise RuntimeError('唯讀Git命令失敗；原退出與streams見commands')
        return p.stdout

    def state(self):
        return {'head': self.git('rev-parse', 'HEAD').decode().strip(),
                'status': self.git('status', '--porcelain=v1', '--untracked-files=all').decode()}

    def save(self):
        self.record['updated_utc'] = capture.utc()
        capture.dump(self.path, self.record)

    def prepare(self):
        for sha in (self.a.base, self.a.main):
            if self.git('rev-parse', sha + '^{commit}').decode().strip() != sha:
                raise RuntimeError('固定比較SHA不存在或解析不符')
        versions = []
        for command in ([sys.executable, '--version'], ['gcc', '--version'], ['gprof', '--version'],
                        ['git', '--version'], ['node', '--version']):
            result = self.r.run(command, cwd=self.a.repo, timeout=30)
            versions.append({'command': command, 'exit': result.returncode,
                             'stdout': result.stdout.decode(errors='replace'),
                             'stderr': result.stderr.decode(errors='replace')})
            if result.returncode:
                raise RuntimeError('必要環境版本命令失敗')
        root_names = self.git('ls-tree', '-z', '--name-only', self.a.base).decode().split('\0')
        names = sorted(name for name in root_names if name.endswith('.scene'))
        actual = sorted(path.name for path in self.a.repo.glob('*.scene'))
        extra_name = '_i11_two_surfaces_same_uv_accept.scene'
        extra_origin = '6366304eb787b2a50282e4132f45e51eb7d21290'
        extra_sha256 = '4a1c2e411aa070ef89333eff235036f27d6c2f42806eefc6d0351c68cade89cb'
        if len(names) != 171 or extra_name in names or actual != sorted(names + [extra_name]):
            raise RuntimeError('原171固定scene加唯一具名I11新增scene不符；拒絕缺漏或未知extras')
        extra_raw = (self.a.repo / extra_name).read_bytes()
        if capture.sha(extra_raw) != extra_sha256 or extra_raw != self.git('show', extra_origin + ':' + extra_name):
            raise RuntimeError('唯一新增I11 scene的固定來源／bytes不符')
        self.record['additional_root_scene'] = {'name': extra_name, 'origin': extra_origin,
            'sha256': extra_sha256, 'bytes': len(extra_raw),
            'scope': '不納入原175；另補比較／原run_tests.py具名accept+lengths正例，未跑不得當綠'}
        inventory = []
        for name in names:
            expected = self.git('show', self.a.base + ':' + name)
            current = (self.a.repo / name).read_bytes()
            if expected != current:
                raise RuntimeError('根目錄scene與固定base原bytes不符：' + name)
            inventory.append({'name': name, 'bytes': len(current), 'sha256': capture.sha(current)})
        for label, sha in (('base', self.a.base), ('main', self.a.main)):
            target = self.work / ('source-' + label)
            target.mkdir()
            available = set(self.git('ls-tree', '-z', '--name-only', sha).decode().split('\0'))
            paths = [p for p in SCOPES if p in available]
            if not {'current_geometry.c', 'geometry-web'} <= set(paths):
                raise RuntimeError('原C建置範圍缺失')
            command = ['git', '-C', str(self.a.repo), 'archive', '--format=tar', sha, '--',
                       *paths, *(':(exclude)' + p for p in EXCLUDES)]
            result = self.r.run(command, cwd=self.a.repo, read_output=False)
            if result.returncode:
                raise RuntimeError('Git archive失敗')
            archive = Path(self.r.rows[-1]['directory']) / 'stdout.bin'
            with tarfile.open(archive) as handle:
                handle.extractall(target, filter='data')
            source_files = []
            for path in sorted(target.rglob('*')):
                if path.is_file():
                    source_files.append({'path': path.relative_to(target).as_posix(),
                                         'bytes': path.stat().st_size, 'sha256': capture.sha(path.read_bytes())})
            capture.dump(self.evidence / ('archive-source-' + label + '.json'),
                         {'sha': sha, 'archive_raw': str(archive), 'paths': paths,
                          'exclude': EXCLUDES, 'files': source_files})
        scenes = self.evidence / 'scenes'
        scenes.mkdir()
        for n in (16, 32, 48, 64):
            result = self.r.run([sys.executable, '-B', str(HERE / 'mini_gen.py'), str(n)], cwd=self.a.repo)
            if result.returncode:
                raise RuntimeError('原mini_gen失敗')
            (scenes / f's{n}.scene').write_bytes(result.stdout)
            inventory.append({'name': f's{n}.scene', 'generated_n': n,
                              'bytes': len(result.stdout), 'sha256': capture.sha(result.stdout)})
        capture.dump(self.evidence / 'scene-inventory.json', {'root_count': 171, 'generated_count': 4,
                                                            'total': 175, 'scenes': inventory})
        self.record['versions'] = versions
        self.record['source_archives'] = {'base': str(self.work / 'source-base'),
                                          'main': str(self.work / 'source-main'),
                                          'fix': str(self.a.repo),
                                          'scopes': SCOPES, 'exclude': EXCLUDES}
        self.record['scene_count'] = 175

    def require(self, stage):
        if self.record['stages'].get(stage, {}).get('execution_exit') != 0:
            raise RuntimeError('前置stage尚未成功：' + stage)

    def build(self):
        self.require('prepare')
        roots = {'base': self.work / 'source-base', 'fix': self.a.repo, 'main': self.work / 'source-main'}
        builds = []
        self.record['builds'] = builds
        for label in ('base', 'fix', 'main', 'base-trace', 'fix-trace'):
            source = roots[label.split('-')[0]]
            row = {'label': label, 'source': str(source), 'execution_exit': None}
            builds.append(row)
            try:
                exe = self.v.build(source, self.work / label, trace=label.endswith('-trace'))
                row.update(execution_exit=0, binary_sha256=capture.sha(exe.read_bytes()))
            except BaseException:
                row.update(execution_exit=1, error=traceback.format_exc())
                traceback.print_exc()
            self.save()
            if row['execution_exit'] == 0 and label.endswith('-trace'):
                for relative in ('current_geometry.c', 'geometry-app/native/world_candidate.inc',
                                 'geometry-core/references.inc', 'geometry-core/kernel/source.c',
                                 'geometry-web/web_bridge.c'):
                    before = (source / relative).read_text()
                    after = (self.work / label / 'source' / relative).read_text()
                    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                  fromfile=relative, tofile=label + '/' + relative))
                    destination = self.evidence / 'instrumentation' / label / (relative + '.diff')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(diff)
        if any(row['execution_exit'] != 0 for row in builds):
            raise RuntimeError('至少一個原建置失敗，其他獨立建置仍已收齊')

    def require_binaries(self, labels):
        built = {row['label'] for row in self.record.get('builds', []) if row['execution_exit'] == 0}
        if not set(labels) <= built:
            raise RuntimeError('必要原建置未成功：' + repr(sorted(set(labels) - built)))

    def compare(self):
        self.require_binaries(('base', 'fix', 'base-trace', 'fix-trace'))
        self.v.compare(self.a.repo, self.work, self.evidence)
        value = json.loads((self.evidence / 'equivalence.json').read_text())
        if value['scenes'] != 175 or len(value['runs']) != 350:
            raise RuntimeError('原ABC輸出數量不符175/350')
        self.record['ABC_result'] = {'scenes': value['scenes'], 'runs': len(value['runs']),
                                     'failures': value['failures'], 'original_exit': 0}
        pairs = {}
        for row in value['runs']:
            name, version = row['scene'], row['version']
            stdout = (self.evidence / 'stdout' / version / (name + '.stdout')).read_bytes()
            stderr = (self.evidence / 'stdout' / version / (name + '.stderr')).read_bytes()
            graph = gzip.decompress((self.evidence / 'graphs' / version / (name + '.bin.gz')).read_bytes())
            if len(stdout) != row['stdout_bytes'] or capture.sha(stdout) != row['stdout_sha256']:
                raise RuntimeError('原ABC stdout raw/hash不符：' + name)
            if len(graph) != row['graph_bytes'] or capture.sha(graph) != row['graph_sha256']:
                raise RuntimeError('原ABC graph raw/hash不符：' + name)
            pairs.setdefault(name, {})[version] = (stdout, stderr, graph, row['guards'])
        if len(pairs) != 175 or any(v['base'] != v['fix'] for v in pairs.values()):
            raise RuntimeError('原audit四元組stdout/stderr/graph/guards成對不符')
        self.record['ABC_result']['original_audit_tuple_equal'] = True

    def perf(self):
        self.require_binaries(('base', 'fix', 'main'))
        self.v.perf(self.a.repo, self.work, self.evidence)
        value = json.loads((self.evidence / 'performance.json').read_text())
        if len(value['samples']) != 36:
            raise RuntimeError('原性能樣本不完整36筆')
        med = value['medians']
        self.record['quantitative_targets']['N64_fix_main'] = {
            'actual': med['64']['fix/main'], 'target': '<=1.3',
            'target_met': med['64']['fix/main'] <= 1.3,
            'method': '原36樣本，N16/32/48/64，每輪base→fix→main，共3輪；中位數'}
        self.record['quantitative_targets']['small_N_no_regression'] = {
            'reference': '原固定base的變更前載入時間；不得變慢',
            'points': {n: {'fix_base': med[n]['fix/base'], 'target_met': med[n]['fix/base'] <= 1}
                       for n in ('16', '32', '48')}}

    def profile(self):
        self.require('prepare')
        for label, root in (('base', self.work / 'source-base'), ('fix', self.a.repo)):
            self.v.build(root, self.work / (label + '-pg'), profile=True)
        (self.evidence / 'checks').mkdir(exist_ok=True)
        os.environ.update(GEO323_ROOT=str(self.a.repo), GEO323_WORK=str(self.work),
                          GEO323_EVIDENCE=str(self.evidence))
        self.r.env.update(GEO323_ROOT=str(self.a.repo), GEO323_WORK=str(self.work),
                          GEO323_EVIDENCE=str(self.evidence))
        runpy.run_path(str(HERE / 'profile_linux.py'), run_name='__main__')
        profiles = {}
        for version in ('base', 'fix'):
            for n in (32, 64):
                path = self.evidence / f'gprof-{version}-{n}.stdout'
                flat = path.read_text().split('Call graph')[0]
                counts, matched = {}, []
                for line in flat.splitlines():
                    parts = line.split()
                    if len(parts) == 7 and parts[-1] in SYMBOLS:
                        counts[parts[-1]] = int(parts[3])
                        matched.append(line)
                missing = [f for f in SYMBOLS if f not in counts]
                for symbol in SYMBOLS:
                    counts.setdefault(symbol, 0)
                profiles[f'{version}-{n}'] = {'counts': counts, 'original_flat_matched_lines': matched,
                                               'symbols_without_flat_call_record': missing,
                                               'gprof_stdout_sha256': capture.sha(path.read_bytes())}
        capture.dump(self.evidence / 'profile-counts.json', profiles)
        lower = profiles['fix-32']['counts']['geo_eval_source']
        upper = profiles['fix-64']['counts']['geo_eval_source']
        ratio = upper / lower if lower else None
        self.record['quantitative_targets']['geo_eval_source_64_32'] = {
            'N32_calls': lower, 'N64_calls': upper, 'actual': ratio, 'target': '<=4.5',
            'target_met': ratio <= 4.5 if ratio is not None else None,
            'method': '原-O1 -fno-inline -pg；base/fix各N32/N64一次；無main profile；原profile無timeout'}

    def suite(self, kind):
        command = [sys.executable, '-B', 'tests/run_all.py', '--build']
        if kind == 'required-eight':
            for name in REQUIRED:
                command += ['--only', name]
        if kind == 'pf3':
            command = [sys.executable, '-B', 'tests/pf3_mutation_check.py',
                       '--out', str(self.evidence / 'pf3'), '--jobs', '1']
        suite_env = None
        if kind in ('native', 'required-eight'):
            execution_dir = self.evidence / (kind + '-executions')
            execution_dir.mkdir(exist_ok=True)
            log_paths = {
                'GEO261_HOST_FACTS_EXECUTION_LOG': str(execution_dir / 'host-facts.jsonl'),
                'GEO261_CONTACT_SOURCES_EXECUTION_LOG': str(execution_dir / 'contact-sources.jsonl'),
                'GEO261_LOAD_RESIDUAL_EXECUTION_LOG': str(execution_dir / 'load-residual.jsonl'),
            }
            suite_env = dict(self.r.env)
            suite_env.update(log_paths)
            self.record.setdefault('suite_execution_log_paths', {})[kind] = log_paths
            self.save()
        result = self.r.run(command, cwd=self.a.repo, env=suite_env)
        if kind in ('native', 'required-eight'):
            logs = Path('/tmp/geometry-tests/run_all-logs')
            if logs.exists():
                shutil.copytree(logs, self.evidence / (kind + '-suite-logs'))
        if result.returncode:
            raise RuntimeError(f'{kind}原命令退出{result.returncode}；不豁免、不改斷言')

    def stage(self, name):
        if name in self.record['stages']:
            raise RuntimeError('拒絕覆寫／重抽既有stage；需要重試請另用新out：' + name)
        row = {'started_utc': capture.utc(), 'execution_exit': None,
               'source_before': self.state(), 'source_after': None, 'errors': []}
        self.record['stages'][name] = row
        self.save()
        try:
            if row['source_before'] != {'head': self.a.sha, 'status': ''}:
                raise RuntimeError('受驗來源不是指定的乾淨SHA')
            function = getattr(self, name) if name in STAGES[:5] else lambda: self.suite(name)
            function()
            row['execution_exit'] = 0
        except BaseException:
            row['execution_exit'] = 1
            row['errors'].append(traceback.format_exc())
            traceback.print_exc()
        finally:
            row['source_after'] = self.state()
            if row['source_after'] != {'head': self.a.sha, 'status': ''}:
                row['execution_exit'] = 1
                row['errors'].append('執行後來源SHA或乾淨狀態不符；未自行重設來源。')
            row['ended_utc'] = capture.utc()
            self.save()


def inner(args):
    if sys.flags.optimize:
        raise RuntimeError('Python optimize會停用原assert，拒絕執行')
    if args.out == args.repo or args.out.is_relative_to(args.repo):
        raise RuntimeError('out必須在受驗repo之外')
    (args.out / 'tmp').mkdir(parents=True, exist_ok=True)
    env, removed = clean_environment(args)
    os.environ.clear()
    os.environ.update(env)
    args.heavy_lock.parent.mkdir(parents=True, exist_ok=True)
    with args.heavy_lock.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = resource.getrlimit(resource.RLIMIT_STACK)
        if before[1] != resource.RLIM_INFINITY and before[1] < 16777216:
            raise RuntimeError('環境hard stack低於16MiB；不降低hard或放寬測試')
        resource.setrlimit(resource.RLIMIT_STACK, (16777216, before[1]))
        invocation = args.out / 'invocations' / args.invocation
        invocation.mkdir(parents=True, exist_ok=True)
        recorder = capture.Recorder(invocation / 'commands', args.repo, args.sha, env)
        capture.ACTIVE = recorder
        with (invocation / 'driver.stdout').open('w') as stdout, (invocation / 'driver.stderr').open('w') as stderr, \
                contextlib.redirect_stdout(Tee(sys.stdout, stdout)), contextlib.redirect_stderr(Tee(sys.stderr, stderr)):
            session = Session(args, recorder)
            session.record['environment'] = capture.safe_env(env)
            session.record['cleared_environment_names'] = removed
            session.record['platform'] = platform.platform()
            session.record['python_optimize'] = sys.flags.optimize
            session.record['stack_before'] = before
            session.record['stack_during'] = resource.getrlimit(resource.RLIMIT_STACK)
            for name in STAGES if args.stage == 'all' else (args.stage,):
                session.stage(name)
            targets = session.record['quantitative_targets']
            values = [v['target_met'] for v in targets.values() if 'target_met' in v]
            values += [v['target_met'] for v in targets.get('small_N_no_regression', {}).get('points', {}).values()]
            session.record['all_executed_stage_commands_passed'] = all(
                v['execution_exit'] == 0 for v in session.record['stages'].values())
            session.record['all_measured_original_targets_met'] = all(values) if values else None
            session.record['all_required_stages_completed'] = all(
                name in session.record['stages'] for name in STAGES)
            code = int(not session.record['all_executed_stage_commands_passed'] or any(v is False or v is None for v in values))
            session.record['wrapper_exit'] = code
            session.record['full_acceptance_passed'] = (code == 0) if session.record['all_required_stages_completed'] else None
            session.record['status'] = '完成；原命令與量化目標分欄，未執行項不代表通過'
            session.save()
            return code


def main():
    parser = argparse.ArgumentParser(description='固定乾淨SHA的GEO-323 Linux驗收；現在準備工具不等於已跑驗收')
    parser.add_argument('--repo', required=True, type=lambda p: Path(p).resolve())
    parser.add_argument('--sha', required=True)
    parser.add_argument('--base', required=True, help='最後同步的整合基底完整SHA，不接受移動分支')
    parser.add_argument('--main', required=True, help='正式main比較組完整SHA，不接受移動分支')
    parser.add_argument('--out', required=True, type=lambda p: Path(p).resolve())
    parser.add_argument('--heavy-lock', required=True, type=lambda p: Path(p).resolve())
    parser.add_argument('--stage', choices=(*STAGES, 'all'), default='all')
    parser.add_argument('--inside-reaper', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--invocation', help=argparse.SUPPRESS)
    args = parser.parse_args()
    for name in ('sha', 'base', 'main'):
        if not re.fullmatch('[0-9a-f]{40}', getattr(args, name)):
            parser.error('--'+name+'必須是完整40位SHA；不接受移動分支')
    if args.out == args.repo or args.out.is_relative_to(args.repo):
        parser.error('--out必須在受驗repo之外')
    if args.heavy_lock == args.repo or args.heavy_lock.is_relative_to(args.repo):
        parser.error('--heavy-lock必須在受驗repo之外')
    if args.inside_reaper:
        return inner(args)
    args.out.mkdir(parents=True, exist_ok=True)
    invocation = capture.utc().replace(':', '').replace('+', '')
    control = args.out / 'control' / invocation
    env = os.environ.copy()
    env['GEO261_REAPER_LOG'] = str(control / 'reaper.jsonl')
    env['GEO323_BASE_SHA'] = args.base
    env['GEO323_MAIN_SHA'] = args.main
    recorder = capture.Recorder(control / 'outer-command', args.repo, args.sha, env)
    argv = [sys.executable, '-B', str(HERE / 'reap_children.py'), sys.executable, '-B', str(Path(__file__).resolve()),
            '--repo', str(args.repo), '--sha', args.sha, '--base', args.base,
            '--main', args.main, '--out', str(args.out),
            '--heavy-lock', str(args.heavy_lock), '--stage', args.stage,
            '--inside-reaper', '--invocation', invocation]
    result = recorder.run(argv, cwd=args.repo, read_output=False)
    capture.dump(control / 'receipt.json', {'sha': args.sha, 'stage': args.stage,
                 'outer_actual_exit': result.returncode, 'command': recorder.rows[0],
                 'reaper_log': env['GEO261_REAPER_LOG'], 'finished_utc': capture.utc()})
    print(f'驗收外層結束：原退出碼{result.returncode}；完整輸出見{control}', flush=True)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
