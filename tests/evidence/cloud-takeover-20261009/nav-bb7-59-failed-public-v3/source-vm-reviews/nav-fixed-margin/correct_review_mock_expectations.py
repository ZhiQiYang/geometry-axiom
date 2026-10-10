from pathlib import Path
import hashlib
import json
p = Path(__file__).resolve().parent
original = p/'review_focus_reveal.cjs'
source = original.read_text()
replacements = [
    ("helper.match(/(?:\\+=|(?<![=!<>])=(?!=))/g).length===8", "(helper.match(/\\+=/g)||[]).length===1&&helper.includes('if (delta) nav.scrollLeft += delta;')"),
    ("r.scroll===44&&r.rect.height===44", "r.scroll===46&&r.rect.height===44"),
    ("r.scroll===5.40625,r", "r.scroll===4.40625,r"),
    ("'static-vm-review.log'", "'static-vm-review-mock-corrected.log'"),
    ("'static-vm-review.json'", "'static-vm-review-mock-corrected.json'"),
]
for a, b in replacements:
    assert a in source, a
    source = source.replace(a, b)
dest = p/'review_focus_reveal_mock_corrected.cjs'
dest.write_text(source)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
(p/'mock-expectation-correction-note.json').write_text(json.dumps({
    'originalReviewScriptSHA256': sha(original),
    'originalFailedProofSHA256': sha(p/'static-vm-review.json'),
    'originalFailedLogSHA256': sha(p/'static-vm-review.log'),
    'correctedReviewScriptSHA256': sha(dest),
    'reason': 'Three synthetic reviewer expectations were wrong: counting const assignments as product writes, mobile right244 gives delta46, border4 left405.59375 gives delta-15.59375. Exact product helper, candidate, proposed patch, actual diagnostic and caption source remain unchanged.',
    'productAcceptance': False,
}, indent=2)+'\n')
