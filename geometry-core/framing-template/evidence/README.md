# Framing proposal: native evidence

Source baseline main e95437877ed15e819fdd3dba3ce5a9d43b84eeda, with empty claim a1ab4d2365b75d2b5091c0b87fbdab8e6147ea7d. Only the new proposal/evidence directory is changed; product/test/core/judge/expected/protected tracked files match baseline. Proposal text was edited during the run; it is not an executed input of the original native tests. No product source changes occurred.

- Original run_all.py --build: 86 suites; counted total2681, pass2680/fail0/skip1 (named allowed Windows GDI), Node659/659. Parent exit0, 599.322s including setup; table timed suites567.7s. Full nonbrowser aggregate, not browser gates or WSL.
- native-all.log/json: original stdout table plus parent exit/duration. native-all-raw.tar.gz:195 raw runner files; native-all-members.json gives every member's bytes/SHA. Binary archive is raw evidence, no base64 transport. inventory.json binds artifacts.
- Original core fixture runner:139/139, fail0/infrastructure0, parent exit0,3.567s. native.json's proposal_sha256 identifies the earlier proposal text at this fixture run, not the final document. Environment/inventory identify final text.
- Initial aggregate lacked --build and thus required binaries were missing. It was explicitly stopped (outer exit143); native-all-incomplete-setup.log is retained and does not count as passed. Only own wrapper/child were stopped. Correct aggregate used freshly built isolated binaries and a separate mutation-cache directory.
- arithmetic.json/log and arithmetic.py.txt check nine fixed numerical expressions in the document. They do not execute a template, perform engine acceptance, or kill mutants. Template acceptance/mutation tables remain unrun designs.
- Linux, gcc/Python versions in environment.json; stack16384KiB; original binaries.py builds in /tmp/framing-proposal-binaries. No WSL, browser, seven-job train or template implementation is claimed.

No SSOT/plain/canonical reader/locked lines/backlog/decision queue edits; tests/runner/expected/mutant ledger unchanged. Existing core freshness checks are not newly executed mutation coverage. GEO-219: no new entrance.
