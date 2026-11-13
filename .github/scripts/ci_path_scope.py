#!/usr/bin/env python3
"""決定 integration-tests.yml 的 browser 系列 job 要不要跑（native 永遠跑）。

依據：決策佇列.md「9. M 提速做法：合併列車＋文件／測試類 PR 只跑相關 job 🔒」
（2026-10-13 使用者拍板）的協調操作化原文：

  - 文件類只跑 native，但 `公理層.md`、白話與正典閱讀器除外，改到它們就要跑 7 項。
  - 測試類跑 native，改到瀏覽器測試時加跑對應 job。
  - 其他一律 7 項並走列車。

這裡只做「最保守」的落實：只有在一個 PR 的每一個變更路徑都能確定是
「純文件」或「與瀏覽器 job 無關的測試檔」時，才略過 browser 系列；
其餘（含任何判不準、取不到差異、push 到 main）一律全跑。
原文沒有定義「瀏覽器測試對應哪個 job」，所以改到瀏覽器測試時不猜對應，
直接全跑（等使用者決定對照後再細分）。

分類（第一個符合的規則決定）：
  axiom      公理層.md、geometry-guide/公理層-白話.md、geometry-guide/公理層-閱讀器.html → 全跑
  served-doc geometry-web/runtime_version.py::static_catalog 會由 App 直接提供的文件 → 全跑
  browser-test-support
             tests/helpers/、tests/fixtures/、檔名含 browser 的 tests/ 檔，以及瀏覽器 job
             會執行的程式（geometry-web/、canvas_evidence.py、package.json、
             tests/test_canvas_shards.js）直接或間接參照到的 tests/ 路徑 → 全跑
             （副檔名不論，含 .md；所以 tests/ 規則排在 doc 之前）
  test       其餘 tests/ 底下的檔案（含 .md）→ 只跑 native
  doc        其餘 *.md → 只跑 native
  other      其他一切（含 workflow 與本檔）→ 全跑

用法（在 actions/checkout 取出的 PR 合併提交上，fetch-depth 至少 2）：
  python3 .github/scripts/ci_path_scope.py --event pull_request --pr-head <sha> [--github-output FILE]
  python3 .github/scripts/ci_path_scope.py --selftest
差異取「合併提交的第一親代 → 合併提交」，也就是這個 PR 實際要併進 base 的變更；
合併提交的第二親代必須等於 --pr-head，否則視為取不到差異而全跑。
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AXIOM_FULL = {'公理層.md', 'geometry-guide/公理層-白話.md', 'geometry-guide/公理層-閱讀器.html'}
NATIVE_ONLY = {'doc', 'test'}
# 瀏覽器 job 直接執行或載入的程式（npm run build → start_local.py → tests/binaries.py；
# browser-canvas-complete 另跑 tests/test_canvas_shards.js）。由此出發追 tests/ 的參照閉包。
SEED_GLOBS = ('package.json', '.github/scripts/canvas_evidence.py', 'geometry-web/**/*.js',
              'geometry-web/**/*.cjs', 'geometry-web/**/*.mjs', 'geometry-web/**/*.py')
SEED_TESTS = ('tests/test_canvas_shards.js',)
TESTS_REF = re.compile(r"(?<![\w-])(?:\.\./)*tests/[\w./-]*[\w-]")
RELATIVE_REF = re.compile(r"""['"](\.{1,2}/[\w./-]+)['"]""")
PY_IMPORT = re.compile(r"^\s*(?:from|import)\s+(?:tests\.)?(\w+)", re.M)


def served_documents(root=ROOT):
    spec = importlib.util.spec_from_file_location('ci_scope_runtime_version',
                                                  root / 'geometry-web/runtime_version.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {path.resolve().relative_to(root.resolve()).as_posix()
            for path in module.static_catalog(root).values()}


def browser_test_closure(root=ROOT):
    """tests/ 底下被瀏覽器 job 程式（直接或間接）參照到的路徑；目錄參照以 '/' 結尾。"""
    root = root.resolve()
    seeds = [p for pattern in SEED_GLOBS for p in sorted(root.glob(pattern))
             if p.is_file() and 'node_modules' not in p.parts]
    if len(seeds) < 10:
        raise RuntimeError('browser-job sources missing from checkout: %d files' % len(seeds))
    found, pending = set(), []

    def add(rel):
        rel = rel.rstrip('/')
        if not rel.startswith('tests/') or rel in found or rel + '/' in found:
            return
        target = root / rel
        if target.is_dir():
            found.add(rel + '/')
        else:
            found.add(rel)
            if target.is_file():
                pending.append(target)

    def scan(path):
        text = path.read_text(encoding='utf-8', errors='replace')
        in_tests = path.resolve().is_relative_to(root / 'tests')
        if path.suffix == '.py' and in_tests:
            # tests/ 內的 Python 只追真正的 import；文件字串裡提到的檔名不算載入。
            for name in PY_IMPORT.findall(text):
                if (path.parent / (name + '.py')).is_file():
                    add((path.parent / (name + '.py')).relative_to(root).as_posix())
            return
        for match in TESTS_REF.findall(text):
            add(re.sub(r'^(?:\.\./)+', '', match))
        if not in_tests:
            return
        for match in RELATIVE_REF.findall(text):
            target = (path.parent / match).resolve()
            for candidate in (target, target.with_name(target.name + '.js'),
                              target.with_name(target.name + '.json')):
                if candidate.exists() and candidate.is_relative_to(root):
                    add(candidate.relative_to(root).as_posix())

    for path in seeds:
        scan(path)
    for name in SEED_TESTS:
        add(name)
    while pending:
        scan(pending.pop())
    return found


def classify_path(path, served, closure):
    if path in AXIOM_FULL:
        return 'axiom'
    if path in served:
        return 'served-doc'
    # tests/ 先於 *.md：tests/helpers/、tests/fixtures/ 與瀏覽器閉包內的 .md 也要全跑（#391 審查 F1）。
    if path.startswith('tests/'):
        name = path.rsplit('/', 1)[-1]
        if (path in closure or any(d.endswith('/') and path.startswith(d) for d in closure)
                or path.startswith(('tests/helpers/', 'tests/fixtures/')) or 'browser' in name):
            return 'browser-test-support'
        return 'test'
    if path.lower().endswith('.md'):
        return 'doc'
    return 'other'


def decide(event, paths, served, closure):
    """回傳 (browser 是否要跑, 每列 (路徑, 分類))。任何不確定都回 True。"""
    if event != 'pull_request':
        return True, [('(event ' + event + ')', 'other')]
    if not paths:
        return True, [('(沒有取得任何變更路徑)', 'other')]
    rows = [(path, classify_path(path, served, closure)) for path in paths]
    return any(category not in NATIVE_ONLY for _, category in rows), rows


def _rev(spec):
    return subprocess.run(['git', 'rev-parse', '--verify', '--quiet', spec + '^{commit}'], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def changed_paths(pr_head):
    base, merge, second = _rev('HEAD^1'), _rev('HEAD'), _rev('HEAD^2')
    for sha in (base, merge, second, pr_head):
        if not re.fullmatch(r'[0-9a-f]{40}', sha or ''):
            raise ValueError('取不到 PR 合併提交的親代（需要 fetch-depth 2）：' + repr(sha))
    if second != pr_head:
        raise ValueError(f'合併提交第二親代 {second} 不是 PR head {pr_head}')
    out = subprocess.run(['git', 'diff', '--name-only', '--no-renames', '-z', base, merge],
                         cwd=ROOT, check=True, capture_output=True).stdout
    return sorted({p.decode('utf-8') for p in out.split(b'\0') if p})


def selftest():
    served = served_documents()
    closure = browser_test_closure()
    cases = [
        (['BACKLOG.md'], False), (['AGENTS.md', 'tests/MUTATION-EVIDENCE.md'], False),
        (['公理層.md'], True), (['geometry-guide/公理層-白話.md'], True),
        (['geometry-guide/公理層-閱讀器.html'], True),
        (['geometry-guide/PRODUCT-VISION.md'], True), (['geometry-web/docs/DOCUMENTS.md'], True),
        (['tests/test_core_integrity.c'], False), (['tests/run_all.expected.json'], False),
        (['tests/mutate.py', 'tests/run_all.py'], False),
        (['tests/binaries.py'], True), (['tests/helpers/canvas_shards.js'], True),
        (['tests/reference_pdf_fixture.js'], True), (['tests/fixtures/new.scene'], True),
        (['tests/fixtures/x.md'], True), (['tests/helpers/README.md'], True),
        (['BACKLOG.md', 'tests/fixtures/x.md'], True),
        (['tests/test_canvas_shards.js'], True), (['tests/room_outline_pan_browser.js'], True),
        (['geometry-web/cdp_test.js'], True), (['geometry-web/space_model_test.js'], True),
        (['current_geometry.c'], True), (['.github/workflows/integration-tests.yml'], True),
        (['.github/scripts/ci_path_scope.py'], True),
        (['BACKLOG.md', 'current_geometry.c'], True), (['BACKLOG.md', 'tests/run_tests.py'], False),
        ([], True),
    ]
    failures = 0
    for paths, expected in cases:
        actual, rows = decide('pull_request', paths, served, closure)
        if actual != expected:
            failures += 1
            print('SELFTEST FAIL', paths, 'expected', expected, 'got', actual, rows)
    if decide('push', ['BACKLOG.md'], served, closure)[0] is not True:
        failures += 1
        print('SELFTEST FAIL push must run everything')
    print(f'selftest: {len(cases) + 1 - failures}/{len(cases) + 1} passed')
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--event', default='')
    parser.add_argument('--pr-head', default='')
    parser.add_argument('--github-output')
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    try:
        paths = changed_paths(args.pr_head) if args.event == 'pull_request' else []
        browser, rows = decide(args.event, paths, served_documents(), browser_test_closure())
    except Exception as error:  # 取不到差異或掃描失敗：保守全跑
        browser, rows = True, [('(分類失敗：' + type(error).__name__ + ': ' + str(error) + ')', 'other')]
    lines = ['| 路徑 | 分類 |', '| --- | --- |'] + [f'| `{p}` | {c} |' for p, c in rows]
    lines.append('')
    lines.append('browser 系列：' + ('全跑' if browser else '略過（本 PR 只有文件／非瀏覽器測試變更，native 照跑）'))
    report = '\n'.join(lines)
    print(report)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write(report + '\n')
    if args.github_output:
        with open(args.github_output, 'a', encoding='utf-8') as handle:
            handle.write('browser=' + ('true' if browser else 'false') + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
