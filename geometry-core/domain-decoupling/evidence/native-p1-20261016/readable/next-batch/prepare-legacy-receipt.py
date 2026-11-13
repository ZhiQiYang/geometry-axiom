"""Generalize only the old external runner's frozen source/output parameters."""
from pathlib import Path

here = Path(__file__).resolve().parent
original = (here.parent / 'exercise-parameters-legacy.py').read_text(encoding='utf-8')
before = "SOURCE = '4aabd21cf82d495f5ab4902bedc9330ca5ed4e3b'\nEVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')\nROOT = Path('/var/tmp/geo261-baseline-a898ad6e/.git/geo261-candidates/native-parameters-4aabd21c')\nOUT = EVIDENCE / 'parameters-legacy-4aabd21c-v1'"
after = "RECIPE_PATH = Path(sys.argv[1]).resolve()\nRECIPE = json.loads(RECIPE_PATH.read_text(encoding='utf-8'))\nSOURCE = RECIPE['source']\nEVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')\nRUNNERS = Path(__file__).resolve().parent\nROOT = Path('/var/tmp/geo261-baseline-a898ad6e/.git/geo261-candidates') / RECIPE['native_label']\nOUT = EVIDENCE / RECIPE['label']"
changes = {
    before: after,
    "(EVIDENCE / 'native-parameters-4aabd21c-v1/source-before.json')": "(EVIDENCE / RECIPE['native_label'] / 'source-before.json')",
    "{name: sha(EVIDENCE / name) for name in ('run-parameters-legacy.py', 'parameters-legacy-namespace.sh', 'exercise-parameters-legacy.py')}": "{name: sha(RUNNERS / name) for name in ('run-legacy-receipt.py', 'legacy-receipt-namespace.sh', 'exercise-legacy-receipt.py')} | {'recipe': sha(RECIPE_PATH)}",
}
for before, after in changes.items():
    if original.count(before) != 1:
        raise RuntimeError('Expected one legacy preparation marker: ' + before)
    original = original.replace(before, after)
(here / 'exercise-legacy-receipt.py').write_text(original, encoding='utf-8', newline='\n')
