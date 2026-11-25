"""serve-wt.sh 的 Linux 行程紀錄與清理；連接埠只用來啟動和探測，不是行程身分。"""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time


BOOT_ID = Path('/proc/sys/kernel/random/boot_id')


def start_ticks(proc):
    # /proc/PID/stat 的 comm 可以含空格和右括號；結尾之後才從欄 3 開始。
    return int((proc / 'stat').read_bytes().rsplit(b')', 1)[1].split()[19])


def commands(wt, port):
    return ([sys.executable, '-u', str(wt / 'geometry-web/start_local.py'), '--port', str(port)],
            [sys.executable, '-u', str(wt / 'geometry-web/serve.py'), str(port)])


def stop_owned(record, wt, port, fb):
    pid = record['pid']
    if (type(pid) is not int or pid <= 1 or record['boot'] != BOOT_ID.read_text().strip()
            or record['worktree'] != str(wt) or record['port'] != port or record['feedback'] != str(fb)):
        raise ValueError('行程紀錄與本次測試不符；未送出停止訊號')
    # 先取得核心 handle，再核對身分；即使檢查後 PID 被重用，也不會送給後來的行程。
    fd = os.pidfd_open(pid)
    try:
        proc = Path('/proc') / str(pid)
        allowed = [b'\0'.join(map(os.fsencode, args)) + b'\0' for args in commands(wt, port)]
        if (proc.stat().st_uid != os.getuid() or start_ticks(proc) != record['startTicks']
                or (proc / 'cwd').readlink() != wt or (proc / 'cmdline').read_bytes() not in allowed):
            raise ValueError('PID 的啟動時間、工作樹或完整命令列不符；未送出停止訊號')
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        poller = select.poll()
        poller.register(fd, select.POLLIN)
        if not poller.poll(5000):
            raise RuntimeError('已對本次服務送出停止訊號，5 秒內未退出；不擴大清理')
    finally:
        os.close(fd)
    print(f'已停止本次測試服務 PID {pid}')


def start(wt, port, fb, state):
    # 建置前先拒絕占用；start_local 本身會在 exec 前重查，最後仍以服務 bind 為準。
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', port))
    fb.mkdir(mode=0o700)  # 每次全新，不能覆寫別次的行程紀錄。
    with (fb / 'build.log').open('xb') as log:
        subprocess.run([sys.executable, 'geometry-web/start_local.py', '--build-only'], cwd=wt,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    with (fb / 'server.log').open('xb') as log:
        child = subprocess.Popen(commands(wt, port)[0], cwd=wt, start_new_session=True,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 env={**os.environ, 'GEOMETRY_FEEDBACK_DIR': str(fb)})
    # 尚未 wait/reap，這裡取得的一定是剛啟動的子行程，不會是重用的 PID。
    record = {'pid': child.pid, 'startTicks': start_ticks(Path('/proc') / str(child.pid)),
              'boot': BOOT_ID.read_text().strip(), 'worktree': str(wt), 'port': port, 'feedback': str(fb)}
    try:
        partial = state.with_suffix('.tmp')
        partial.write_text(json.dumps(record))
        partial.rename(state)
        for _ in range(180):
            if child.poll() is not None:
                raise RuntimeError(f'自己的服務 PID {child.pid} 已退出；見 {fb}/server.log')
            probe = subprocess.run([sys.executable, 'geometry-web/runtime_version.py', '--probe', str(port)],
                                   cwd=wt, capture_output=True, text=True)
            if probe.returncode == 0:
                if json.loads(probe.stdout)['pid'] != child.pid or child.poll() is not None:
                    raise RuntimeError('探測到的服務不是本次子行程，拒絕沿用')
                print(probe.stdout, end='')
                return
            time.sleep(1)
        raise RuntimeError('服務探測逾時')
    except BaseException:
        if child.poll() is None:
            stop_owned(record, wt, port, fb)
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stop', action='store_true')
    ap.add_argument('worktree', type=Path)
    ap.add_argument('port', type=int)
    ap.add_argument('feedback', type=Path)
    a = ap.parse_args()
    wt, fb = a.worktree.resolve(strict=True), a.feedback.resolve()
    if not os.getuid() or not 1024 <= a.port <= 65535 or Path(os.environ['TMPDIR']).resolve() not in fb.parents:
        ap.error('須以非 root 使用 1024–65535 埠及 TMPDIR 下的專用回報目錄')
    if not hasattr(signal, 'pidfd_send_signal') or not hasattr(os, 'pidfd_open'):
        ap.error('需要 Linux pidfd 支援；不以裸 PID 代替')
    os.close(os.pidfd_open(os.getpid()))  # 核心不支援時在啟動前報錯。
    state = fb / 'server-pid.json'
    if a.stop:
        try:
            directory = fb.stat()
            if directory.st_uid != os.getuid() or directory.st_mode & 0o077 or state.is_symlink():
                raise ValueError('不是本帳號的私有行程紀錄；未送出停止訊號')
            record = json.loads(state.read_text())
            stop_owned(record, wt, a.port, fb)
        except (FileNotFoundError, ProcessLookupError) as exc:
            raise RuntimeError('找不到本次測試的行程紀錄或 PID；未停止任何行程') from exc
    else:
        start(wt, a.port, fb, state)


if __name__ == '__main__':
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f'診斷服務錯誤：{error}')
