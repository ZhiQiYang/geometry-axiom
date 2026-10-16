"""Prepare a new immutable receipt runner; retain original red runs untouched."""
from pathlib import Path

here = Path(__file__).resolve().parent
original = (here.parent / 'run-region-edges.py').read_text(encoding='utf-8')
changes = {
    "NEW = 'be9ed3e7886f951918a8e02e678e0284f0d34079'": "NEW = 'a88d3c57917d22aa28e3357b2c22e08c586a9f71'",
    "EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')": "EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')\nRUNNERS = Path(__file__).resolve().parent",
    "source[:8] + '-v1'": "source[:8] + '-v2'",
    "str(EVIDENCE / 'exercise-region-edges.py')": "str(RUNNERS / 'exercise-region-edges.py')",
    "{name: sha(EVIDENCE / name) for name in ('run-region-edges.py', 'exercise-region-edges.py')}": "{name: sha(RUNNERS / name) for name in ('run-region-edges-v2.py', 'exercise-region-edges.py')}",
}
for before, after in changes.items():
    if original.count(before) != 1:
        raise RuntimeError('Expected one fixed preparation marker: ' + before)
    original = original.replace(before, after)
(here / 'run-region-edges-v2.py').write_text(original, encoding='utf-8', newline='\n')
(here / 'exercise-region-edges.py').write_bytes((here.parent / 'exercise-region-edges.py').read_bytes())
