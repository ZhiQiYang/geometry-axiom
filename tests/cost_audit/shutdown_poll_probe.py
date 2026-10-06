#!/usr/bin/env python3
"""Bounded synthetic BaseServer shutdown probe; no listening port or product service."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import socket
import socketserver
import statistics
import sys
import threading
import time
from unittest.mock import patch


def measure(interval):
    entered = threading.Event()
    selected = socketserver._ServerSelector

    class ObservedSelector(selected):
        def select(self, timeout=None):
            entered.set()
            return super().select(timeout)

    class IdleServer(socketserver.BaseServer):
        def __init__(self):
            super().__init__('synthetic-socketpair', None)
            self.reader, self.writer = socket.socketpair()

        def fileno(self):
            return self.reader.fileno()

    server = IdleServer()
    kwargs = {} if interval is None else dict(poll_interval=interval)
    thread = threading.Thread(target=server.serve_forever, kwargs=kwargs, daemon=True)
    elapsed = []
    errors = []

    def stop():
        start = time.perf_counter()
        try:
            server.shutdown()
            elapsed.append(time.perf_counter() - start)
        except BaseException as error:
            errors.append(error)

    shutdown_thread = threading.Thread(target=stop, daemon=True)
    try:
        with patch.object(socketserver, '_ServerSelector', ObservedSelector):
            thread.start()
            if not entered.wait(2):
                raise RuntimeError('synthetic selector did not start')
            shutdown_thread.start()
            shutdown_thread.join(timeout=2)
            if shutdown_thread.is_alive():
                raise RuntimeError('synthetic shutdown exceeded its bound')
            if errors:
                raise RuntimeError('synthetic shutdown failed') from errors[0]
            thread.join(timeout=2)
            if thread.is_alive():
                raise RuntimeError('synthetic server did not stop')
    finally:
        if thread.is_alive():
            # Wake the idle selector without another unbounded shutdown call.
            server.writer.setblocking(False)
            try:
                server.writer.send(b'wake')
            except OSError:
                pass
            thread.join(timeout=2)
        if shutdown_thread.is_alive():
            shutdown_thread.join(timeout=2)
        server.reader.close()
        server.writer.close()
    return dict(configuration='stdlib-default' if interval is None else interval,
                shutdown_wait_seconds=elapsed[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('refusing to overwrite evidence')
    samples = [measure(interval) for _ in range(3) for interval in (None, .01)]
    medians = {label: statistics.median(row['shutdown_wait_seconds'] for row in samples
                                       if row['configuration'] == label)
               for label in ('stdlib-default', .01)}
    source = inspect.getsource(socketserver.BaseServer.serve_forever) + inspect.getsource(socketserver.BaseServer.shutdown)
    result = dict(schema='geometry-test-shutdown-mechanism/1', python=sys.version,
                  stdlib_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  listening_ports=0, product_services=0, samples=samples,
                  median_shutdown_wait_seconds=medians, actual_test_serve_saved_seconds=None,
                  limits=['Synthetic idle socketpair only; no HTTP requests or product test suite.',
                          'Demonstrates polling mechanism, not twelve real server shutdown costs.',
                          'The .01 configuration changes polling frequency, not any product/request/join timeout.'])
    with args.out.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
