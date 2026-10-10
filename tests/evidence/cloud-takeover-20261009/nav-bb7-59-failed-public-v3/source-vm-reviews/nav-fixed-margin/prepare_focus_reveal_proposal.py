"""Prepare exact product proposals in scratch; never write the checkout."""
import datetime
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('<workspace-path>')
OUT = Path(__file__).resolve().parent
EXPECTED = '102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c'
CAPTION = Path('<workspace-path>')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

before = {'head': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain')}
assert before == {'head': EXPECTED, 'dirty': ''}, before
app = (ROOT/'geometry-web/app.js').read_text()
anchor = '''document.addEventListener("focusin", e => {
  if (!canvasMenuTrigger) return;
  const pop = $(canvasMenuTrigger.getAttribute("aria-controls"));
  if (e.target !== canvasMenuTrigger && !pop?.contains(e.target)) closeMenus();
});
'''
helper = '''document.addEventListener("focusin", e => {
  const nav = $("faceWorkspaceTools"), tool = e.target;
  if (!nav || !tool?.matches?.(".workspace-tool") || !nav.contains(tool)
      || tool !== document.activeElement || !nav.closest("#objectWorkspace:not([hidden])")
      || nav.closest("[hidden]") || !nav.getClientRects().length
      || getComputedStyle(tool).visibility !== "visible") return;
  const box = nav.getBoundingClientRect(), rect = tool.getBoundingClientRect();
  if (nav.clientWidth <= 0 || rect.width <= 0 || rect.height <= 0) return;
  const left = box.left + nav.clientLeft + 3, right = box.left + nav.clientLeft + nav.clientWidth - 3;
  const delta = rect.left < left ? rect.left - left : rect.right > right ? rect.right - right : 0;
  if (delta) nav.scrollLeft += delta;
});
'''
assert app.count(anchor) == 1
candidate = app.replace(anchor, anchor+helper)
(OUT/'app.focus-reveal.candidate.js').write_text(candidate)
(OUT/'focus-reveal.helper.js').write_text(helper)
patch = ''.join(difflib.unified_diff(app.splitlines(True), candidate.splitlines(True), fromfile='a/geometry-web/app.js', tofile='b/geometry-web/app.js'))
(OUT/'focus-reveal.patch').write_text(patch)

caption = CAPTION.read_text()
assert sha(CAPTION) == '01744e5910989b2454800ae1cef2c07c9b7db29185c28ece5fec6c65d44e496d'
old_line = '/* PREPARED ONLY. Standalone, explicit partial #123 contract probe.\n'
new_line = '/* Standalone, explicit partial #123 caption and toolbar-focus contract probe.\n'
assert caption.startswith(old_line)
caption_candidate = new_line + caption[len(old_line):]
assert caption_candidate.splitlines(True)[1:] == caption.splitlines(True)[1:]
(OUT/'issue123_caption_browser.cjs').write_text(caption_candidate)
caption_patch = ''.join(difflib.unified_diff([], caption_candidate.splitlines(True), fromfile='/dev/null', tofile='b/tests/issue123_caption_browser.cjs'))
(OUT/'retain-caption-regression.patch').write_text(caption_patch)
(OUT/'caption-comment-only.diff').write_text(''.join(difflib.unified_diff(caption.splitlines(True), caption_candidate.splitlines(True), fromfile='original-01744e-caption-source', tofile='proposed-tests/issue123_caption_browser.cjs')))
after = {'head': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain')}
assert after == before
receipt = {
    'schema': 'geometry-nav-focus-reveal-scratch-proposal/1',
    'checkedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'executor': {'executable': sys.executable, 'executableSHA256': sha(sys.executable), 'command': sys.orig_argv, 'script': str(Path(__file__).resolve()), 'scriptSHA256': sha(__file__)},
    'checkout': {'path': str(ROOT), 'before': before, 'after': after},
    'inputs': {'geometry-web/app.js': sha(ROOT/'geometry-web/app.js'), 'geometry-web/app.css': sha(ROOT/'geometry-web/app.css'), 'originalCaption': {'path': str(CAPTION), 'sha256': sha(CAPTION)},
               'diagnosticActual': {'path': '<isolated-test-directory>', 'sha256': sha('<isolated-test-directory>')}},
    'files': {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and p.name != 'proposal-receipt.json'},
    'productOrFormalTestWritten': False, 'browserExecuted': False, 'serviceStarted': False,
    'claims': ['synchronous nearest horizontal reveal of a current focused face workspace tool only', 'only nav.scrollLeft may change', 'caption proposed formal source differs from original01744e solely first comment line'],
    'limits': ['scratch candidate not applied; static/VM is not browser acceptance', 'CSS alone is not established as a reliable fix; actual outer scroll range is zero', 'original01744e failed27/1 retained; seven widths must run on new clean product SHA', 'app.js behavior change requires purposefully complete CDP regression;102ff results must not be borrowed'],
}
(OUT/'proposal-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'head': EXPECTED, 'dirty': '', 'paths': receipt['files'], 'receiptSHA256': sha(OUT/'proposal-receipt.json')}, ensure_ascii=False))
