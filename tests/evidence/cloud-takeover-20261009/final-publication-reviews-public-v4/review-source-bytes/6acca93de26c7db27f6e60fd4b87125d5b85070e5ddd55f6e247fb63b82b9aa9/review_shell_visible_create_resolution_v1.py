"""Resolve one reviewer's API-spelling assumption against immutable source."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

BASE = Path('<workspace-path>')
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
checks = []
bindings = {}


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    bindings[str(path)] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    return raw


def check(condition, name):
    checks.append({'name': name, 'passed': bool(condition)})


prior_raw = read(BASE / 'shell-packet-v1-supplement/report.json')
prior = json.loads(prior_raw)
check(hashlib.sha256(prior_raw).hexdigest() == 'a4a79770d1e1d3e25c351c7ba651bc921576ead917907426fa8fde8dd060f294', 'unaltered prior587/1 actualexit1 exact report')
check(prior['reviewDecisionExitCode'] == 1 and prior['metadataChecksPassed'] == 587 and prior['findings'] == ['original unchanged helper declares both normal visible Create routes'], 'only source API-spelling assumption remains')
source_raw = read('<workspace-path>')
source = source_raw.decode()
check(hashlib.sha256(source_raw).hexdigest() == 'ca3ecb98d6091283bb242f4528ae0a47b153888626f7fe1d85479de649e74471', 'original source remains original hash ca3')
exact_loop = "for(const selector of ['#btnCreateObject','#mobileCreateObject'])if(await page.locator(selector).isVisible())candidates.push(selector);"
check(source.count(exact_loop) == 1, 'original helper declares both routes using exact normal locator visibility loop')
check("check('unique visible original Create entry',candidates.length===1,candidates);" in source and 'await normalClick(candidates[0]);await normalClick(entry);' in source, 'exact one original visible control and unchanged normal click')
check("document.querySelectorAll('#btnCreateObject,#mobileCreateObject')" not in source, 'prior diagnostic expected API spelling was wrong, not package or product source')
manifest_path = Path('<workspace-path>')
manifest_raw = read(manifest_path)
check(hashlib.sha256(manifest_raw).hexdigest() == prior['manifestSHA256'] == '4ec51be9a583d025d2a1cc06e78f3a260a2241dc295a1985efa14f4aa9d12867', 'same final-ready packet unchanged')
for path, binding in prior['sourceAndRawBindings'].items():
    raw = read(path)
    check(len(raw) == binding['bytes'] and hashlib.sha256(raw).hexdigest() == binding['sha256'], 'prior verified source/projection/result/build identity unchanged ' + path)
failed = [item['name'] for item in checks if not item['passed']]
exit_code = 0 if not failed else 1
actual_exe = Path('/proc/self/exe').resolve()
report = {'schema': 'geometry-independent-shell-visible-create-resolution/1', 'actor': '/root/publication_final_review', 'startedUtc': started, 'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'manifestSHA256': prior['manifestSHA256'], 'command': [sys.executable, '-B', str(Path(__file__)), str(OUT)], 'sourceSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'actualPython': str(actual_exe), 'actualPythonSHA256': hashlib.sha256(actual_exe.read_bytes()).hexdigest(), 'actualReviewerPID': os.getpid(), 'priorActualExitCode': 1, 'priorReportSHA256': hashlib.sha256(prior_raw).hexdigest(), 'priorFindingsPreserved': prior['findings'], 'resolution': 'Original helper iterates both existing Create selectors with locator.isVisible; it never used the querySelectorAll API spelling mistakenly required by the supplemental reviewer. Original exact40 positive results/order and all public/source/executable/native/build bindings remain unaltered.', 'metadataChecksPassed': sum(item['passed'] for item in checks), 'metadataChecksFailed': len(failed), 'findings': failed, 'checks': checks, 'reviewDecisionExitCode': exit_code, 'finalPacketAccepted': exit_code == 0, 'countsAreProductAssertions': False, 'bindings': bindings, 'original14075of3AndSupplement587of1Preserved': True, 'productBrowserNativeServiceRepoGitHubActions': False}
path = OUT / 'report.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(path), 'reportSHA256': hashlib.sha256(path.read_bytes()).hexdigest(), 'manifestSHA256': prior['manifestSHA256'], 'metadataChecksPassed': report['metadataChecksPassed'], 'metadataChecksFailed': len(failed), 'actualDecisionExitCode': exit_code, 'finalPacketAccepted': exit_code == 0}, ensure_ascii=False))
sys.exit(exit_code)
