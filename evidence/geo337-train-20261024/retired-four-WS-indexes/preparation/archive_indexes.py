"""Archive four sealed retired OWN Git index caches. Never removes any index."""
from pathlib import Path
import argparse, datetime, gzip, hashlib, importlib.util, json, os, stat, sys
HERE = Path(__file__).parent
PLAN = HERE / 'PLAN.json'
PLAN_PIN = '24b2f5df655362bd2c2c6a9ea4c98e3d4bcabc384e80d8c46684e1ec7b2f872f'
OWN = Path('/dev/shm/geometry-axiom-geo337-20261025')
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
GUARD = Path('/workspace/clear_terminal_chrome_caches.py')
GUARD_PIN = 'c51b4da96fc8ce88043484d3072a870fd725a18b00e6288e12144c399069e847'
ROLES = ['R5', 'R6', 'readingL', 'readerF9']
ROOTS = ['/workspace/geo323-final-r5-source-20261024', '/workspace/geo323-final-r6-source-20261024', '/workspace/train337-L-reading-a-source', '/workspace/geo337-F9-readers-actual-urce1nqh/source']

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def h(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())

def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def metadata(path):
    s = path.lstat()
    return dict(dev=s.st_dev, inode=s.st_ino, nlink=s.st_nlink, mode=s.st_mode,
                uid=s.st_uid, gid=s.st_gid, bytes=s.st_size, allocated=s.st_blocks*512,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns, atime_ns=s.st_atime_ns)

def original_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
    with os.fdopen(fd, 'rb') as stream:
        return stream.read()

def load_module(name, path, pin):
    need(h(path.read_bytes()) == pin, 'pinned original helper changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--request', type=Path, required=True)
    ap.add_argument('--request-sha256', required=True)
    ap.add_argument('--execute-archive', action='store_true')
    a = ap.parse_args()
    need(sys.flags.optimize == 0, 'PYTHONOPTIMIZE forbidden')
    raw = a.request.read_bytes()
    need(h(raw) == a.request_sha256, 'request pin')
    q = json.loads(raw)
    need(h(PLAN.read_bytes()) == q['plan_sha256'] == PLAN_PIN, 'exact four-index inventory pin')
    plan = json.loads(PLAN.read_bytes())
    need([s['root'] for s in plan['subjects']] == ROOTS and [s['role'] for s in plan['subjects']] == ROLES, 'exact four approved roots only')
    if not a.execute_archive:
        print(json.dumps({'executed': False, 'index_removed': False, 'plan_sha256': PLAN_PIN}))
        return 0
    for key in ('root_four_sources_no_reuse_lease', 'root_no_active_consumers_lease', 'root_shared_shm_capacity_admitted'):
        need(q[key] is True, 'root lease missing: ' + key)
    peerpath = Path(q['independent_peer']['path'])
    peerraw = peerpath.read_bytes()
    need(h(peerraw) == q['independent_peer']['sha256'], 'independent peer pin')
    peer = json.loads(peerraw)
    need(peer['exit_code'] == 0 and not peer['blocking_findings'] and peer['executor_sha256'] == h(Path(__file__).read_bytes()), 'independent peer did not accept exact executor')
    out = Path(q['out'])
    need(out.is_absolute() and out.resolve() == out and out.parent == OWN and out.name.startswith('retired-four-WS-indexes-20261025') and not out.exists(), 'fresh exact OWN SHM index archive child')
    need(OWN.is_dir() and not OWN.is_symlink(), 'existing approved OWN root')
    cap = load_module('index_archive_capture', CAP, CAP_PIN)
    guard = load_module('index_archive_original_consumer', GUARD, GUARD_PIN)
    out.mkdir()
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONOPTIMIZE', None)
    rec = cap.Recorder(out / 'commands', env, '4f8a794f4167c3562eb182045102e86e9e37cca9')
    result = {'schema':'geo337-four-retired-WS-index-archive/1', 'exit_code':1,
              'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'plan_sha256':PLAN_PIN, 'request_sha256':a.request_sha256,
              'executor_sha256':h(Path(__file__).read_bytes()), 'formal_executed':False,
              'index_removed':False, 'no_source_refs_objects_fixtures_or_dirty_writes':True,
              'archives':[], 'snapshots':[], 'commands':rec.rows,
              'remote_delivered':False, 'removal_authorized_by_this_tool':False}
    try:
        dump(out / 'REQUEST.json', q)
        dump(out / 'PLAN.json', plan)
        def consumers(label):
            d = out / ('consumer-' + label)
            d.mkdir()
            guard.OUT = d
            guard.consumer_check(ROOTS)
        def snapshot(s, label):
            root = Path(s['root']); gitdir = root / '.git'; index = gitdir / 'index'
            guard.ancestors(index)
            need(gitdir.is_dir() and not gitdir.is_symlink() and gitdir.resolve() == gitdir, 'independent physical Git directory')
            need([gitdir.stat().st_dev,gitdir.stat().st_ino] == s['gitdir_device_inode'], 'Git directory identity drift')
            m = metadata(index)
            need(stat.S_ISREG(m['mode']) and m['nlink'] == 1 and all(m[k] == s['index_metadata'][k] for k in m if k != 'atime_ns'), 'index identity drift')
            need(not list(gitdir.glob('*.lock')) and not list((gitdir / 'refs').rglob('*.lock')), 'active Git lock')
            vals = {}
            for key, args in [('head',['rev-parse','HEAD']),('staged',['diff','--cached','--no-ext-diff','--raw','-z']),('status',['status','--porcelain=v1','-z','--untracked-files=all']),('refs',['for-each-ref','--format=%(refname) %(objectname)'])]:
                row, so, se = rec.run(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false',*args], cwd=root, timeout=None, check=True, source_sha=s['head'], source_variant='Retired index archive only: ' + label)
                need(not se, 'unexpected Git stderr')
                vals[key] = so
            need(vals['head'].decode().strip() == s['head'] and not vals['staged'], 'HEAD or staged modifications changed')
            need(vals['status'].hex() == s['git_status_hex'] and h(vals['refs']) == s['git_refs_sha256'], 'worktree dirty state or refs changed')
            for path, wanted in s['other_git_metadata'].items():
                p = Path(path); guard.ancestors(p)
                need(p.is_file() and p.stat().st_size == wanted['bytes'] and h(original_bytes(p)) == wanted['sha256'], 'protected Git metadata changed')
            terminal = Path(s['terminal']['path'])
            need(terminal.stat().st_size == s['terminal']['bytes'] and h(terminal.read_bytes()) == s['terminal']['sha256'], 'terminal provenance changed')
            body = original_bytes(index)
            need(h(body) == s['index_sha256'] and len(body) == m['bytes'] and body[:4] == b'DIRC', 'original complete index bytes drift')
            after = metadata(index)
            need(all(after[k] == m[k] for k in m if k != 'atime_ns'), 'index changed while inspecting')
            xattrs = {n:os.getxattr(index,n,follow_symlinks=False).hex() for n in os.listxattr(index,follow_symlinks=False)}
            entry = {'role':s['role'], 'phase':label, 'index_metadata':after, 'index_sha256':h(body), 'xattrs_hex':xattrs, 'status_sha256':h(vals['status']), 'refs_sha256':h(vals['refs']), 'staged_empty':True}
            result['snapshots'].append(entry)
            return body, entry
        consumers('before')
        before = {s['role']:snapshot(s, 'before')[1] for s in plan['subjects']}
        need(len({tuple(s['gitdir_device_inode']) for s in plan['subjects']}) == 4, 'four independent Git directory inodes')
        for s in plan['subjects']:
            consumers('before-' + s['role'])
            body, snap = snapshot(s, 'prearchive')
            destination = out / (s['role'] + '.index.gz')
            with destination.open('xb') as stream:
                os.chmod(destination, 0o600)
                with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as gz:
                    gz.write(body)
                stream.flush(); os.fsync(stream.fileno())
            with gzip.open(destination, 'rb') as stream:
                restored = stream.read()
            need(restored == body and h(restored) == s['index_sha256'], 'gzip full-byte roundtrip failed')
            result['archives'].append({'role':s['role'], 'original_index':s['index'], 'head':s['head'], 'archive':destination.name, 'archive_bytes':destination.stat().st_size, 'archive_sha256':h(destination.read_bytes()), 'original_bytes':len(body), 'original_sha256':s['index_sha256'], 'original_metadata':snap['index_metadata'], 'xattrs_hex':snap['xattrs_hex'], 'complete_roundtrip':True})
            syncdir(out)
        consumers('after')
        for s in plan['subjects']:
            _, after = snapshot(s, 'after')
            need(after['index_sha256'] == before[s['role']]['index_sha256'] and after['xattrs_hex'] == before[s['role']]['xattrs_hex'], 'final index preservation')
        result.update(exit_code=0, all_four_original_indexes_still_present=True,
                      archived_raw_index_bytes=sum(r['original_bytes'] for r in result['archives']),
                      hypothetical_later_WS_release_bytes=plan['index_allocated_total'])
    except BaseException as exc:
        result['error'] = repr(exc)
        raise
    finally:
        result['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        dump(out / 'RESULT.json', result)
        syncdir(out); syncdir(out.parent)
    print(json.dumps({'exit_code':0, 'out':str(out), 'index_removed':False, 'remote_delivered':False}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
