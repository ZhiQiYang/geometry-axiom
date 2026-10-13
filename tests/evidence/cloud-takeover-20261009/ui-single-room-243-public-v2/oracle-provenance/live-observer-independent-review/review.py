"""Pure AST/fixture review only; launches no observer, browser, gate or service."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

source = Path('<workspace-path>')
out = Path('<workspace-path>')
out.mkdir(exist_ok=True)
raw = source.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == '637113a1c44c5966b16b3b2b1103d17962225941ba24e4680d402374c6ef362f', digest
(out / 'reviewed-observer-637113a1.py').write_bytes(raw)
tree = ast.parse(raw)
checks_node = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'checks' for t in n.targets)
                   and isinstance(n.value, ast.Dict))
checks = {k.value: v for k, v in zip(checks_node.keys, checks_node.values)}
probe = ['/python', '/scratch/original_probe.py', '--url', 'http://127.0.0.1:19180/']
observed = {101: {'pid': 101, 'parent': 100, 'exe': '/python3.12',
                 'argv': ['/python', '/scratch/run_gate.py', '--expected-cases', '4', '--', *probe]}}
def predicate(name):
    return eval(compile(ast.Expression(checks[name]), '<observer-predicate-only>', 'eval'),
                {'Path': Path, 'observed': observed, 'probe': probe})
false_python = predicate('actualProbePythonObserved')
assert false_python is True
assert not any(v['argv'][1] == probe[1] for v in observed.values())
observed[102] = {'pid': 102, 'parent': 101, 'exe': '/node', 'argv': ['node', '/other/playwright/cli.js']}
observed[103] = {'pid': 103, 'parent': 102, 'exe': '/chromium',
                 'argv': ['chromium', '--remote-debugging-pipe']}
loose_chain = {name: predicate(name) for name in ['actualProbePythonObserved',
               'actualPlaywrightDriverNodeObserved', 'actualMainChromeObserved']}
assert all(loose_chain.values())
report = {
    'actor': '/root/race_review/hole_order_oracle_review',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Read-only observer source review plus pure synthetic AST predicates; no observer, original gate, browser, service or product test executed.',
    'reviewedSource': {'originalPath': '<workspace-path>',
                       'path': str(source), 'sha256': digest,
                       'sealedCopyProvenance': 'Original bytes were read with sha256sum and sed before the parent revised the mutable observer. After revision, the sealed original was reconstructed in scratch by exact known delta and required to equal that original SHA. No modified-source receipt is rebound to the original SHA.'},
    'verdict': 'needs-revision',
    'findings': [
        {'priority': 'high', 'lines': [165, 168],
         'problem': 'actualProbePythonObserved accepts the inner run_gate.py process itself because its argv forwards the complete probe.py command. Wrapper descendants include the gate root PID. Thus a green predicate does not prove the actual probe interpreter was observed.',
         'proof': {'observedOnlyInnerGate': list(observed.values())[:1],
                   'actualProbePythonPredicate': false_python,
                   'actualProbeScriptAtExecutedPositionObserved': False},
         'next': 'Identify the gate direct child running the original probe command, bind executable script position or exact original argv, and connect that same actual Python PID/startTicks to driver Node and main Chrome ancestry.'},
        {'priority': 'high', 'lines': [168, 175],
         'problem': 'Python, Playwright Node and main Chrome checks are independent any(...) predicates over the entire gate subtree. They never verify that driver Node descends from the accepted probe Python or that main Chrome descends from that driver.',
         'proof': {'allThreeCurrentPredicates': loose_chain,
                   'fixtureHasNoActualProbeInterpreter': True},
         'next': 'Require a recorded immutable parent chain from one identified probe interpreter to its driver Node to its main Chrome, with matching process start ticks, rather than three unrelated names.'},
        {'priority': 'medium', 'lines': [131, 134],
         'problem': 'Observed processes are keyed only by PID and permanently skipped after the first sample. A fork may be sampled before exec, or the Chromium shell launcher may be sampled before exec to its actual browser binary. The final actual executable may therefore never be captured. Reused PID startTicks are also not a new record.',
         'next': 'Re-observe until each required role is captured; retain records keyed by PID/startTicks/executable identity or update when argv/exe changes. Keep earlier samples instead of silently overwriting.'},
        {'priority': 'medium', 'lines': [27, 37, 80, 99],
         'problem': 'live() combines one stat read, a resolved executable path stat, possibly cached SHA, later cmdline and cwd without checking that the PID/startTicks and exe stayed unchanged. SHA cache key excludes executable inode/device/ctime and uses filesystem target stat rather than the /proc executable handle. Concurrent exec/replacement can create an inconsistent identity record.',
         'next': 'Open /proc/PID/exe while live, hash or inode-bind the opened handle, and compare startTicks/exe identity before and after argv/cwd capture. Include device/inode and change time in any executable-byte cache key; retry transient exec samples.'},
        {'priority': 'medium', 'lines': [116, 143, 155, 158],
         'problem': 'Before/after snapshot assertions, disappearing service descendants, timeout capture errors other than ProcessLookupError and child.wait TimeoutExpired can terminate the wrapper before it writes receipt.json. A completed original gate can therefore lose the added identity receipt, and timeout may leave owned client processes alive.',
         'next': 'Write a failure/unknown receipt in finally with preserved original gate/log identities. Catch and record transient process/read and cleanup errors; use bounded TERM/KILL cleanup only for verified owned PID/startTick identities, then explicitly verify leftovers. Never backfill live identities after the process ended.'},
        {'priority': 'low', 'lines': [162, 164],
         'problem': 'nativePidBytesStable compares pid/exe/SHA but omits startTicks already captured. PID reuse could masquerade as the same native process.',
         'next': 'Compare native PID plus startTicks, executable identity and SHA, including the service PID/startTicks when binding ancestry.'}
    ],
    'acceptedProperties': [
        'Existing run_gate.py and original probe command are invoked without source/assertion edits.',
        'Output is a fresh directory outside the repository, and wrapper uses separate owned child session.',
        'Configured executable identities are labelled separately from observed live process records.',
        'Before/after source full SHA and dirty, runtime root/freshness and original gate census checks are present.',
        'The observer attempts /proc executable reads during execution; no explicit retrospective process lookup after completion exists.',
        'Inner original gate success/census remains separately indexed and is necessary for overall success.'
    ],
    'notVerified': ['Actual runtime behavior of this wrapper.', 'Actual Python, Node or Chrome identities from a real run.', 'New product acceptance or any browser result.'],
    'revisionBoundary': 'Observer-only changes are sufficient; original run_gate.py and probe executors/oracles should remain byte-identical.'
}
path = out / 'observer-review-637113a1.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': report['verdict'], 'report': str(path),
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'pureFixturePredicates': loose_chain}, ensure_ascii=False))
