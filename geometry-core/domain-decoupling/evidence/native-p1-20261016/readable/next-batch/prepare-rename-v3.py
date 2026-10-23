#!/usr/bin/env python3
"""Prepare only an external fixed-source receipt; never alter the test judge."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root.parent / 'run-rename-native-v2.py').read_text(encoding='utf-8')
changes = {
    '0e7c38bb8bf719f0084d24ce73ef65f016d6ddde': '73aca666e779527bd096e7f09a9bc12cdc38d051',
    'grid-rename-native-v2': 'grid-rename-native-v3',
    'grid-rename-0e7c38bb': 'grid-rename-73aca666',
    'b51bc18cac87e8c07e0b2557b5941157f2868118a66ee64e64ec328a716b0be0': '752685eb5b95191c5958bbfaec765484926fcc34a985c28346d0b9a4213769c7',
}
for old, new in changes.items():
    if source.count(old) != 1:
        raise RuntimeError('Unexpected original receipt shape: ' + old)
    source = source.replace(old, new)
ast.parse(source)
target = root / 'run-rename-native-v3.py'
if target.exists():
    raise RuntimeError('Do not overwrite a prepared receipt runner')
target.write_text(source, encoding='utf-8', newline='\n')
print(target)
