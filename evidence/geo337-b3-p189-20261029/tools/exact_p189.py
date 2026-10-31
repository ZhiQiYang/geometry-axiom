#!/usr/bin/env python3
"""Exact, position-specific P-189 policy; never normalizes arbitrary messages."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

POLICY = {
    '_role_priority_mutant.scene': (8, 1, '——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm'),
    '_s1_p8_l_room_primary_through_reflex_extension.scene': (15, 3, '——定位邊 e3 [3000,4800] mm，低端超出 [27,3000] mm'),
    '_s1_p8b_l_room_primary_through_reflex_extension_hi.scene': (12, 3, '——定位邊 e1 [0,1800] mm，高端超出 [1800,4773] mm'),
}

def compare(name: str, scene: Path, baseline, candidate, scene_hash: str, pinned_scenes: dict):
    """Arguments retain actual stdout/stderr bytes and integer subprocess exits."""
    if type(baseline.returncode) is not int or type(candidate.returncode) is not int:
        return False, 'returncode-type'
    if baseline.returncode != 0 or candidate.returncode != baseline.returncode:
        return False, 'returncode'
    if name not in POLICY:
        return (baseline.stdout == candidate.stdout and baseline.stderr == candidate.stderr,
                'strict-bytes')
    if scene_hash != pinned_scenes.get(name):
        return False, 'scene-input-identity'
    line, member, suffix = POLICY[name]
    old_error = f'V_EXTENSION：非 boundary 角材（{member}）的 footprint 超出定位邊範圍'.encode()
    prefix = b'{"ok":false,"error":"line ' + str(line).encode() + b': ' + old_error
    ending = b'","status":"INVALID","code":"SCENE_INVALID"}\n'
    old_first = prefix + ending
    if not baseline.stdout.startswith(old_first):
        return False, 'baseline-first-response'
    rest = baseline.stdout[len(old_first):]
    if len(rest.splitlines()) != 1 or json.loads(rest).get('ok') is not True:
        return False, 'baseline-dump'
    expected_stdout = prefix + suffix.encode() + ending + rest
    old_stderr = str(scene).encode() + b':' + str(line).encode() + b': ' + old_error + b'\n'
    if baseline.stderr != old_stderr:
        return False, 'baseline-stderr'
    expected_stderr = old_stderr[:-1] + suffix.encode() + b'\n'
    if candidate.stdout != expected_stdout:
        return False, 'exact-position-stdout'
    if candidate.stderr != expected_stderr:
        return False, 'exact-position-stderr'
    return True, 'exact-three-position-policy'
