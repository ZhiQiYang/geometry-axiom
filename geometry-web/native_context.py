"""One native process, receipt namespace and load transaction per editor context."""
import os
import queue
import subprocess
import threading
import uuid


class NativeContext:
    def __init__(self, command):
        self.bridge = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.bridge_lock = threading.RLock()
        self.bridge_responses = queue.Queue()
        self.bridge_failure = None
        self.upload_temps = []
        self.prepared_upload = None
        self.upload_outcomes = {}
        self.upload_lock = threading.Lock()
        self.session = uuid.uuid4().hex
        self.api_receipts = {}
        self.editor_creations = {}
        self.editor_sequence = 0
        self.receipt_lock = threading.Lock()
        self.closed = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        while True:
            try:
                response = self.bridge.stdout.readline()
            except OSError:
                response = b""
            self.bridge_responses.put(response)
            if not response:
                return

    def close(self):
        # Same ordering as a load transaction: no command or late confirm can
        # enter a retired context, and closing B never acquires A's locks.
        with self.upload_lock, self.bridge_lock:
            if self.closed:
                return
            self.closed = True
            self.bridge_failure = "方案編輯已結束，請重新開啟方案。"
            self.bridge.terminate()
            try:
                self.bridge.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.bridge.kill()
                self.bridge.wait(timeout=2)
            paths = self.upload_temps[:]
            if self.prepared_upload:
                paths.append(self.prepared_upload[1])
            for path in paths:
                try:
                    os.unlink(path)
                except OSError:
                    pass
            self.upload_temps.clear()
            self.prepared_upload = None
