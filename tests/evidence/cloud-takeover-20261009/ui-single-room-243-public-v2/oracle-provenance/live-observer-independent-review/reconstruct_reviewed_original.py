"""Reconstruct already-read original observer into scratch; require exact SHA."""
from pathlib import Path
import hashlib

out = Path('<workspace-path>')
s = (out / 'reviewed-observer-5c674f63.py').read_text()
s = s.replace('''    parent = int(stat[1])
    try:
        parent_start = (Path('/proc') / str(parent) / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    except OSError:
        parent_start = None
    return {'pid': pid, 'parent': parent, 'parentStartTicks': parent_start,
            'state': stat[0], 'startTicks': stat[19],
''', '''    return {'pid': pid, 'parent': int(stat[1]), 'state': stat[0], 'startTicks': stat[19],
''')
s = s.replace('observed, latest, transient = {}, {}, []', 'observed, transient = {}, []')
s = s.replace('''            for pid in sorted(children(child.pid)):
                try:
''', '''            for pid in sorted(children(child.pid)):
                if pid in observed:
                    continue
                try:
''')
s = s.replace('''                        # Retain exec transitions rather than permanently
                        # treating a first-seen launcher shell as its browser.
                        key = (pid, value['startTicks'], value['exe'], tuple(value['argv']))
                        observed.setdefault(key, value)
                        latest[pid] = value
''', '''                        observed[pid] = value
''')
s = s.replace('saved = latest.get(pid)', 'saved = observed.get(pid)')
start = s.index("    inner_path = output / 'inner-gate' / 'receipt.json'\n", s.index('    after = snapshot()'))
end = s.index('    checks = {\n', start)
s = s[:start] + s[end:]
s = s.replace('''        'actualProbePythonObserved': bool(probe_python),
        'actualPlaywrightDriverNodeObserved': bool(driver_node),
        'actualMainChromeObserved': bool(main_chrome),
''', '''        'actualProbePythonObserved': any('python' in Path(v['exe']).name and
                                        any(str(arg) in v['argv'] for arg in probe[1:] if str(arg).endswith('.py'))
                                        for v in observed.values()),
        'actualPlaywrightDriverNodeObserved': any(Path(v['exe']).name == 'node' and
                                                  any('playwright' in arg for arg in v['argv'])
                                                  for v in observed.values()),
        'actualMainChromeObserved': any('chromium' in Path(v['exe']).name and
                                       '--remote-debugging-pipe' in v['argv'] and
                                       not any(arg.startswith('--type=') for arg in v['argv'])
                                       for v in observed.values()),
''')
s = s.replace("    checks['innerOriginalGateVerified'] =", "    inner_path = output / 'inner-gate' / 'receipt.json'\n    inner = json.loads(inner_path.read_text()) if inner_path.is_file() else {}\n    checks['innerOriginalGateVerified'] =")
s = s.replace('''               'directActualProbeBindings': {'innerGateExecutionPid': probe_pid, 'probePython': probe_python,
                                            'ownedDriverNode': driver_node, 'ownedMainChrome': main_chrome,
                                            'rule': 'Exact inner execution pid and argv for probe Python; direct parent pid plus process startTicks bind Node to that Python and Chrome to that Node, observed live.'},
''', '')
b = s.encode()
h = hashlib.sha256(b).hexdigest()
assert h == '637113a1c44c5966b16b3b2b1103d17962225941ba24e4680d402374c6ef362f', h
p = out / 'reviewed-observer-637113a1.py'
p.write_bytes(b)
print(str(p), h)
