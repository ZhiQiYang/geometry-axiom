"""Prepare one evidence package, without Git, network, deletion, or product tests.

The only omitted capture files are the exact 24 fresh API stdout gzip containers.
Their complete *raw stdout* already exists at pinned E9 paths and is indexed here.
The local gzip originals are neither removed nor claimed present in this archive.
"""
import argparse
import datetime
import gzip
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import tarfile
from pathlib import Path, PurePosixPath

OWN = Path('/dev/shm/geometry-axiom-geo337-20261025')
OTHER = Path('/dev/shm/geo337-F9-browsers-20261025')
F = 'cbf0fb621888596aa14ad5f2349b503e23b1b72d'
E9 = '9a57aea2128a7bc3985064932c24e2229fd8fcb8'
PARENT = 'dea5d12a88c0a2ed93141014524dce5d104f8b1f'
REMOTE = OWN / 'retirement-remote-fresh-175947-20261026'
REMOTE_RESULT = 'cb81d42bf76485e2fe1413cda4b7d78b6740bbc7230a26b4cc4a5b63fab3366b'
REMOTE_PEER = Path('/tmp/geo-resume1758-retirement-peer-20261026/REMOTE_FRESH_ACTUAL_REVIEW.json')
REMOTE_PEER_PIN = '53c6275d0ed80a1710d988853adc30d3395f561b980ce98c7e4b52e7bbaea836'
PUBLISHER = Path('/tmp/geo337-recovery-evidence-append-preparation-20261026/publish_append.py')
PUBLISHER_PIN = '988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720'
CEILING = 2 * 1024**3
PREFIX = 'evidence/geo337-train-20261024/resume-175947-20261026/'
PROGRESS = 'evidence/geo337-train-20261024/resume-20261026/PROGRESS.md'
MANDATORY = {
    OWN / 'retirement-preflight-175947-20261026',
    REMOTE,
    OWN / 'approved-retirement-root-175947-20261026',
    OWN / 'native-TMP-retirement-20261025',
    OWN / 'reader-F-175947-20261026',
    Path('/tmp/geo-resume1758-root-20261026'),
}

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def snapshot(path):
    s = path.lstat()
    need(stat.S_ISREG(s.st_mode) and not path.is_symlink(), 'regular input required: ' + str(path))
    return {'device': s.st_dev, 'inode': s.st_ino, 'mode': s.st_mode, 'bytes': s.st_size,
            'mtime_ns': s.st_mtime_ns, 'ctime_ns': s.st_ctime_ns, 'nlink': s.st_nlink}

def read_stable(path):
    before = snapshot(path)
    raw = path.read_bytes()
    need(snapshot(path) == before and len(raw) == before['bytes'], 'input changed while reading: ' + str(path))
    return raw, before

def allowed_root(path):
    return ((path.parent == Path('/tmp') and path.name.startswith('geo-resume1758-')) or
            (path.parent == OWN and (path in MANDATORY or path.name.startswith('axiom-F-175947-'))))

def allocated():
    seen, total = set(), 0
    for root in (OWN, OTHER):
        need(root.is_dir() and not root.is_symlink(), 'original OWN root missing')
        for path in root.rglob('*'):
            s = path.lstat()
            key = (s.st_dev, s.st_ino)
            if key not in seen:
                seen.add(key)
                total += s.st_blocks * 512
    return total

def external_stdout_bindings():
    remote_path = REMOTE / 'RESULT.json'
    raw, remote_state = read_stable(remote_path)
    need(sha(raw) == REMOTE_RESULT, 'fixed new remote RESULT changed')
    r = json.loads(raw)
    need(r['exit_code'] == 0 and r['ended_utc'] and r['evidence_sha'] == E9, 'fresh remote is not terminal')
    need(r['verified_manifest_count'] == 4 and r['verified_raw_payload_count'] == 26 and len(r['remote_checks']) == 30, 'remote fixed scope')
    need(r['unique_remote_download_count'] == 24 and len(r['commands']) == 25, 'fresh unique command count')
    peer_raw, peer_state = read_stable(REMOTE_PEER)
    need(sha(peer_raw) == REMOTE_PEER_PIN, 'fresh remote actual peer changed')
    peer = json.loads(peer_raw)
    need(peer['exit_code'] == 0 and not peer['blocking_findings'] and peer['subject_result_sha256'] == REMOTE_RESULT, 'fresh remote actual peer rejected')
    commands = {Path(x['directory']): x for x in r['commands']}
    groups = {}
    for item in r['remote_checks']:
        d = Path(item['remote_stdout_directory'])
        need(d.parent == REMOTE and d.name.isdecimal() and d.name != '000', 'only exact API capture directories may be external')
        groups.setdefault(d, []).append(item)
    need(len(groups) == 24 and set(groups) == {REMOTE / ('%03d' % n) for n in range(1, 25)}, 'exact unique capture set')
    external = {}
    for directory, items in sorted(groups.items()):
        command = commands[directory]
        need(command['exit_code'] == 0 and not command['timeout_expired'], 'remote command not successful')
        path = directory / 'stdout.bin.gz'
        packed, state = read_stable(path)
        need(sha(packed) == command['stdout_gzip_sha256'] and len(packed) == command['stdout_gzip_bytes'], 'fresh gzip identity')
        body = gzip.decompress(packed)
        need(len(body) == command['stdout_bytes'] and sha(body) == command['stdout_sha256'], 'fresh complete stdout identity')
        oid = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        need(command['argv'] == ['gh', 'api', '--hostname', 'github.com', '-H', 'Accept: application/vnd.github.raw+json', 'repos/ZhiQiYang/geometry-axiom/git/blobs/' + oid], 'unexpected externalized command')
        aliases = []
        for item in items:
            need(item['E9_tree_verified'] is True and item['local_original_byte_equal'] is True and item['gzip_roundtrip'] is True, 'remote path proof incomplete')
            need(item['expected_bytes'] == item['stdout_bytes'] == len(body) and item['expected_sha256'] == item['stdout_sha256'] == sha(body), 'remote alias bytes')
            need(item['expected_oid'] == item['actual_git_oid'] == oid and item['stdout_gzip_sha256'] == sha(packed), 'remote alias OID/gzip')
            gp = item['git_path']
            need(gp.startswith('evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/') and '..' not in PurePosixPath(gp).parts, 'E9 output path outside fixed archive')
            aliases.append({'git_path': gp, 'kind': item['kind'], 'original_path': item['original_path'],
                            'url': 'https://github.com/ZhiQiYang/geometry-axiom/blob/' + E9 + '/' + gp})
        external[path] = {'representation': 'external_complete_raw_stdout', 'evidence_commit': E9,
                          'blob_oid': oid, 'raw_bytes': len(body), 'raw_sha256': sha(body),
                          'fresh_capture_directory': str(directory), 'raw_aliases': aliases,
                          'local_omitted_gzip_bytes': len(packed), 'local_omitted_gzip_sha256': sha(packed),
                          'source_state': state, 'local_gzip_retained': True,
                          'gzip_container_not_claimed_in_new_archive': True,
                          'exact_gzip_recompression_not_claimed': True}
    need(len(external) == 24 and sum(x['local_omitted_gzip_bytes'] for x in external.values()) == 10225981, 'exact externalized container total')
    need(REMOTE / '000/stdout.bin.gz' not in external, 'new ls-tree output must stay internal')
    pins = {remote_path: {'state': remote_state, 'sha256': sha(raw)},
            REMOTE_PEER: {'state': peer_state, 'sha256': sha(peer_raw)}}
    return external, pins

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path)
    p.add_argument('--config-sha256')
    p.add_argument('--out', type=Path)
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    need(not sys.flags.optimize, 'optimized Python forbidden')
    if not a.execute:
        print('PLAN ONLY: no capture reads, package writes, Git, network, deletion or product tests. Root must freeze the config after reader termination.')
        return 0
    need(a.config and a.config_sha256 and a.out, 'explicit frozen configuration and fresh output required')
    executor_path = Path(__file__).absolute()
    executor_raw, executor_state = read_stable(executor_path)
    config_raw, config_state = read_stable(a.config)
    need(sha(config_raw) == a.config_sha256, 'configuration pin')
    cfg = json.loads(config_raw)
    need(cfg.get('template_only_not_executable') is False, 'root must freeze a completed non-template configuration')
    need(cfg['product_sha'] == F and cfg['expected_evidence_parent'] == PARENT and cfg['external_raw_commit'] == E9, 'fixed source/evidence anchors')
    need(a.out.parent == OWN and a.out.name == 'continuation-package-175947-20261026' and not a.out.exists(), 'fresh exact package output')
    need(sha(PUBLISHER.read_bytes()) == PUBLISHER_PIN, 'original publisher unchanged')
    roots = cfg['roots']
    need(len(roots) == len({x['alias'] for x in roots}) == len({x['path'] for x in roots}), 'unique source roots/aliases')
    root_paths = {Path(x['path']) for x in roots}
    need(MANDATORY <= root_paths and a.out not in root_paths, 'mandatory closed receipts missing')
    for entry in roots:
        root, alias = Path(entry['path']), entry['alias']
        need(allowed_root(root) and root.is_dir() and root.resolve() == root and not root.is_symlink(), 'root outside new-scope allowlist')
        need(alias and '/' not in alias and '\\' not in alias and alias not in ('.','..'), 'safe root alias')
    need(len(cfg['terminal_results']) == len({x['path'] for x in cfg['terminal_results']}), 'unique terminal result bindings')
    terminal_pins, terminal_values = {}, {}
    for item in cfg['terminal_results']:
        path = Path(item['path'])
        need(any(path.is_relative_to(r) for r in root_paths), 'terminal result not within included roots')
        raw, state = read_stable(path)
        need(sha(raw) == item['sha256'], 'terminal result pin')
        value = json.loads(raw)
        terminal_pins[path] = {'state': state, 'sha256': sha(raw)}
        terminal_values[path] = value
        need(value['exit_code'] == item['exit_code'] and value['exit_code'] in (0,1,2), 'real terminal exit required')
        if item.get('end_key'):
            need(value.get(item['end_key']), 'terminal end timestamp missing')
    required_results = {
        OWN / 'retirement-preflight-175947-20261026/RESULT.json': (1, 'ended_utc'),
        REMOTE / 'RESULT.json': (0, 'ended_utc'),
        OWN / 'approved-retirement-root-175947-20261026/RESULT.json': (0, None),
        OWN / 'native-TMP-retirement-20261025/RESULT.json': (0, 'ended_utc'),
    }
    for path, (exit_code, end_key) in required_results.items():
        records = [x for x in cfg['terminal_results'] if Path(x['path']) == path]
        need(len(records) == 1 and records[0]['exit_code'] == exit_code and records[0].get('end_key') == end_key,
             'required original terminal result missing or relabelled')
    # Any later optional formal stage needs the same real-termination binding.
    for root in root_paths - MANDATORY:
        if root.parent != OWN:
            continue
        path = root / 'RESULT.json'
        records = [x for x in cfg['terminal_results'] if Path(x['path']) == path]
        need(len(records) == 1 and records[0].get('end_key') == 'ended_utc', 'optional formal stage missing ended pin')
        need(terminal_values[path].get('ended_utc') and terminal_values[path].get('source_sha') == F,
             'optional formal stage active or wrong source')
    # This is an explicit ban on packaging the currently active reader.
    reader_result = OWN / 'reader-F-175947-20261026/RESULT.json'
    reader_rows = [x for x in cfg['terminal_results'] if Path(x['path']) == reader_result]
    need(len(reader_rows) == 1 and reader_rows[0].get('end_key') == 'ended_utc', 'reader must have a pinned real ended result')
    reader = terminal_values[reader_result]
    need(reader.get('ended_utc') and reader.get('source_sha') == F, 'reader still active or wrong source')
    progress_path = Path(cfg['progress_path'])
    need(progress_path.parent == Path('/tmp/geo-resume1758-root-20261026'), 'root owns the new PROGRESS source')
    progress_raw, progress_state = read_stable(progress_path)
    need(sha(progress_raw) == cfg['progress_sha256'], 'PROGRESS pin')
    external, remote_pins = external_stdout_bindings()
    pins = dict(terminal_pins)
    for path, identity in remote_pins.items():
        need(path not in pins or pins[path] == identity, 'terminal changed before remote binding')
        pins[path] = identity
    inputs, dirs, original_lists = {}, set(), {}
    for entry in roots:
        root, alias = Path(entry['path']), entry['alias']
        paths = sorted(root.rglob('*'))
        original_lists[root] = [str(x.relative_to(root)) for x in paths]
        dirs.add(alias)
        for path in paths:
            need(not path.is_symlink(), 'symlink in receipt source')
            member = alias + '/' + path.relative_to(root).as_posix()
            s = path.lstat()
            if stat.S_ISDIR(s.st_mode):
                dirs.add(member)
            else:
                need(stat.S_ISREG(s.st_mode) and member not in inputs, 'unsupported or duplicate input')
                body, state = read_stable(path)
                inputs[member] = {'path': path, 'body': body, 'state': state, 'sha256': sha(body)}
    actual_excluded = {v['path'] for v in inputs.values() if v['path'] in external}
    need(actual_excluded == set(external), 'every external capture must appear in the complete input tree')
    by_path = {v['path']: v for v in inputs.values()}
    for path, identity in pins.items():
        need(path in by_path and by_path[path]['sha256'] == identity['sha256'] and
             by_path[path]['state'] == identity['state'], 'archive input differs from pinned terminal/peer: ' + str(path))
    for path, binding in external.items():
        need(by_path[path]['state'] == binding['source_state'] and
             by_path[path]['sha256'] == binding['local_omitted_gzip_sha256'],
             'external gzip changed after binding')
    rows = []
    tar_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=tar_buffer, mode='wb', filename='', mtime=0, compresslevel=9) as gz:
        with tarfile.open(fileobj=gz, mode='w|', format=tarfile.PAX_FORMAT) as tar:
            for directory in sorted(dirs):
                ti = tarfile.TarInfo(directory)
                ti.type = tarfile.DIRTYPE
                ti.mode = 0o755
                tar.addfile(ti)
            for member, item in sorted(inputs.items()):
                path = item['path']
                row = {'member': member, 'source_path': str(path), 'source_state': item['state'],
                       'bytes': len(item['body']), 'sha256': item['sha256']}
                if path in external:
                    row.update(external[path])
                else:
                    row['representation'] = 'included_full_file'
                    ti = tarfile.TarInfo(member)
                    ti.size = len(item['body'])
                    ti.mode = 0o644
                    tar.addfile(ti, io.BytesIO(item['body']))
                rows.append(row)
    archive = tar_buffer.getvalue()
    included = {x['member']: x for x in rows if x['representation'] == 'included_full_file'}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        need(set(tar.getnames()) == set(included) | dirs, 'archive exact membership')
        for ti in tar:
            if ti.isdir():
                continue
            need(ti.isfile() and ti.name in included, 'archive entry type')
            body = tar.extractfile(ti).read()
            need(len(body) == included[ti.name]['bytes'] and sha(body) == included[ti.name]['sha256'], 'archive full member roundtrip')
    index = {'schema':'resumed-closed-evidence-with-explicit-E9-stdout-references/1',
             'product_sha':F,'previous_evidence_head':PARENT,'external_full_raw_commit':E9,
             'source_execution_binding':'Per-file original receipts; archive creation is not a product-test execution',
             'normalized_tar_metadata':{'uid':0,'gid':0,'mtime':0,'file_mode':'0644','directory_mode':'0755'},
             'included_files':len(included),'external_stdout_container_files':len(external),
             'included_directories':sorted(dirs),'files':rows,
             'archive':{'bytes':len(archive),'sha256':sha(archive)},
             'all_local_originals_retained':True,'archive_does_not_contain_external_gzip_containers':True}
    index_raw = encoded(index)
    readme = ('# 本輪完整原件與明確外部輸出索引\n\n'
              '此包保留本輪新指令、時間、退出碼、環境、錯誤、結果與所有獨有輸出。'
              '只有 INDEX.json 明列的 24 份 fresh API stdout gzip 容器不重包；其完整 raw stdout '
              '逐 byte 相同於固定 E9 的完整 manifest／raw payload，逐筆列 commit/path/Git OID/bytes/SHA256 與 30 個路徑別名。\n\n'
              '本次唯一 git ls-tree stdout、全部 stderr 與新 reader／清理輸出均在 archive。'
              '不宣稱 archive 包含外部 gzip 容器，也不保證重新壓縮的 gzip bytes 相同；所有本地原件仍保留。'
              '原 maps 預檢 exit 1 不改寫，清理結果與產品驗收分開。\n').encode()
    outputs = {'ORIGINALS.tar.gz':archive, 'INDEX.json':index_raw, 'README.md':readme,
               'PREPARER.py':executor_raw, 'CONFIG.json':config_raw}
    manifest = {'schema':'resumed-closed-evidence-publication/1','product_sha':F,
                'previous_evidence_head':PARENT,'files':[]}
    for name, body in outputs.items():
        manifest['files'].append({'source_path':str(a.out/name),'destination':PREFIX+name,'bytes':len(body),'sha256':sha(body)})
    manifest['files'].append({'source_path':str(progress_path),'destination':PROGRESS,'bytes':len(progress_raw),'sha256':sha(progress_raw)})
    manifest_raw = encoded(manifest)
    output_upper = sum(((len(x)+4095)//4096)*4096 for x in list(outputs.values())+[manifest_raw]) + 128*1024
    payload = sum(x['bytes'] for x in manifest['files'])
    publish_bound = payload*3 + len(manifest['files'])*65536 + len(manifest_raw)*8 + 64*1024**2
    used = allocated()
    required_total = used + output_upper + publish_bound
    need(required_total <= CEILING,
         'unchanged original publisher bound does not fit; no output created; used=' + str(used) +
         ' preparation_upper=' + str(output_upper) + ' publisher_bound=' + str(publish_bound) +
         ' deficit_bytes=' + str(max(0, required_total - CEILING)))
    need(shutil.disk_usage(OWN).free > output_upper + publish_bound, 'actual output mount capacity')
    for root, names in original_lists.items():
        need([str(x.relative_to(root)) for x in sorted(root.rglob('*'))] == names, 'source directory changed')
    for item in inputs.values():
        need(snapshot(item['path']) == item['state'] and sha(item['path'].read_bytes()) == item['sha256'], 'source changed after archive assembly')
    need(snapshot(a.config) == config_state and sha(a.config.read_bytes()) == sha(config_raw), 'configuration changed')
    need(snapshot(progress_path) == progress_state and sha(progress_path.read_bytes()) == sha(progress_raw), 'PROGRESS changed')
    need(snapshot(executor_path) == executor_state and sha(executor_path.read_bytes()) == sha(executor_raw), 'preparer source changed')
    a.out.mkdir()
    for name, body in outputs.items():
        with (a.out/name).open('xb') as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
    with (a.out/'PUBLICATION_MANIFEST.json').open('xb') as stream:
        stream.write(manifest_raw)
        stream.flush()
        os.fsync(stream.fileno())
    used_after = allocated()
    result = {'exit_code':0 if used_after + 64*1024 + publish_bound <= CEILING else 1,
              'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'config_sha256':sha(config_raw),'archive_sha256':sha(archive),'archive_bytes':len(archive),
              'index_sha256':sha(index_raw),'publication_manifest_sha256':sha(manifest_raw),
              'included_files':len(included),'external_complete_raw_stdout_files':24,
              'capacity':{'used_before':used,'prepared_output_upper':output_upper,
                          'used_after_payloads':used_after,'final_result_reserved_bytes':64*1024,
                          'original_publisher_additional_bound':publish_bound,'original_ceiling':CEILING},
              'product_tests_executed':False,'Git_or_network_executed':False,'originals_deleted':False,
              'publication_executed':False,'root_must_run_original_publisher_separately':True}
    with (a.out/'RESULT.json').open('xb') as stream:
        stream.write(encoded(result))
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(a.out, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps(result,ensure_ascii=False))
    return result['exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
