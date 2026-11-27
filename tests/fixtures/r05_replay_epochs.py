"""只重播 L467 命令紀錄中的 host epoch 輸入；不替換 bridge 或 producer 的輸出。"""
import re
import runpy
import secrets
import sys
from pathlib import Path
from unittest.mock import patch


def replay(command_log, script, *args):
    epochs = iter(re.findall(r'^identity-epoch ([0-9a-f]{32})$',
                            Path(command_log).read_text(encoding='utf-8'), re.MULTILINE))

    def recorded_epoch(nbytes):
        if nbytes != 16:
            raise ValueError('非預期的 host epoch 長度')
        return next(epochs)

    with patch.object(secrets, 'token_hex', recorded_epoch), patch.object(sys, 'argv', [script, *args]):
        runpy.run_path(script, run_name='__main__')
    if next(epochs, None) is not None:
        raise ValueError('有未使用的 host epoch 紀錄')


if __name__ == '__main__':
    replay(*sys.argv[1:])
