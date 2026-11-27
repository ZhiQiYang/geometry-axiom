#!/usr/bin/env python3
"""R16 v3 named withdrawals in disposable copies; not browser/CI evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PYTEST = 'tests/test_r16_grid_form_contract.py'
NODETEST = 'tests/test_r16_grid_form_runtime.js'
CASES = [
    ('R16GF_RESTORE_LOW_CONTRAST', 'geometry-web/grid-inspector.css',
     'font-size:13px;line-height:1.3;color:var(--form-label-color)}',
     'font-size:13px;line-height:1.3;color:#69788d}', 'R16GF_LABEL_ROOT_TOKEN', PYTEST),
    ('R16GF_REINTRODUCE_SCOPE_ALIAS', 'geometry-web/grid-system-workspace.css',
     '.ig-workspace { --muted: #526579;', '.ig-workspace { --muted: var(--grid-form-label-color);',
     'R16GF_EXISTING_SCOPE_ONLY', PYTEST),
    ('R16GF_REMOVE_COMPACT_FOCUS', 'geometry-web/grid-inspector.css',
     '.gi-inspector input:focus-visible,.gi-inspector select:focus-visible,.gi-inspector button:focus-visible{outline:2px solid var(--accent);',
     '.gi-inspector input:focus-visible,.gi-inspector select:focus-visible,.gi-inspector button:focus-visible{outline:none;',
     'R16GF_FOCUS', PYTEST),
    ('R16GF_REMOVE_FULL_FOCUS', 'geometry-web/grid-system-workspace.css',
     '.ig-settings input:focus-visible, .ig-settings select:focus-visible, .ig-settings button:focus-visible, .ig-footer-actions button:focus-visible { outline: 2px solid var(--accent);',
     '.ig-settings input:focus-visible, .ig-settings select:focus-visible, .ig-settings button:focus-visible, .ig-footer-actions button:focus-visible { outline: none;',
     'R16GF_FOCUS', PYTEST),
    ('R16GF_REMOVE_COMPOUND_FOCUS', 'geometry-web/grid-system-workspace.css',
     '.ig-pf-box:has(input:focus-visible) { outline: 2px solid var(--accent);',
     '.ig-pf-box:has(input:focus-visible) { outline: none;', 'R16GF_FOCUS', PYTEST),
    ('R16GF_DROP_FOOTER_INSET', 'geometry-web/workspace-height-dialogs.css',
     'inset: auto var(--r16-grid-scrollbar, 0px) 0 auto;', 'inset: auto 0 0 auto;',
     'R16GF_FOOTER_GUTTER', PYTEST),
    ('R16GF_IGNORE_REAL_SCROLLBAR', 'geometry-web/grid-system-workspace.js',
     'const gutter=Math.max(0,layout.offsetWidth-layout.clientWidth);', 'const gutter=0;',
     'R16GF_FOOTER_GUTTER', NODETEST),
    ('R16GF_RESTORE_BODY_MUTED_LOOKUP', 'geometry-web/grid-inspector.css',
     'color:var(--form-label-color)}', 'color:var(--muted)}',
     'R16GF_LABEL_ROOT_TOKEN', PYTEST),
    ('R16GF_MOVE_ALIAS_TO_BODY', 'geometry-web/app.css',
     '  --form-label-color: var(--muted);',
     '}\nbody { --form-label-color: var(--muted); }\n:root {',
     'R16GF_ROOT_ALIAS_DECLARATION', PYTEST),
]

def named_failure(output, marker, judge):
    if judge==PYTEST:
        # Read the actual assertion exception, never its echoed source line.
        return any(marker in block for block in re.findall(
            r'^AssertionError:.*?(?=^={10,}|^-{10,}\nRan |\Z)',output,re.M|re.S))
    for _,body in re.findall(r'^not ok \d+ - ([^\n]+)\n(  ---\n.*?^  \.\.\.)',output,re.M|re.S):
        error=re.search(r'^  error: [^\n]*(?:\n    [^\n]*)*',body,re.M)
        if error and marker in error.group(0) and "  code: 'ERR_ASSERTION'" in body:return True
    return False


def copy_sources(stage):
    # Copy the real runtime plus its local dependencies. No test doubles for
    # the measured helper or draft-history implementation are substituted.
    shutil.copytree(ROOT / 'geometry-web', stage / 'geometry-web',
                    ignore=shutil.ignore_patterns('docs', 'evidence', 'node_modules', '*.png', '*.pdf', '*.map'))
    shutil.copytree(ROOT / 'geometry-app', stage / 'geometry-app')
    shutil.copytree(ROOT / 'geometry-templates', stage / 'geometry-templates')
    (stage / 'geometry-core').mkdir()
    for source in (ROOT / 'geometry-core').glob('*.js'):
        shutil.copyfile(source, stage / 'geometry-core' / source.name)
    for file in [PYTEST, NODETEST, 'tests/fixtures/reference_workspace_vm.cjs']:
        target = stage / file
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / file, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('proof output must be outside the product checkout')
    output.mkdir(parents=True, exist_ok=True)
    report = {'schema':'r16-grid-form-local-withdrawals/2', 'chromium_executed':False, 'acceptance':False, 'cases':[]}
    for name, file, old, new, marker, judge in CASES:
        original = (ROOT / file).read_bytes()
        assert original.count(old.encode()) == 1, name + ': one reviewed anchor required'
        mutant = original.replace(old.encode(), new.encode(), 1)
        command = [sys.executable, '-B', judge] if judge == PYTEST else ['node', '--test', '--test-reporter=tap', judge]
        row = {'id':name, 'file':file, 'assertion':marker, 'command':command,
               'before_sha256':hashlib.sha256(original).hexdigest(),
               'mutant_sha256':hashlib.sha256(mutant).hexdigest(), 'phases':[]}
        with tempfile.TemporaryDirectory(prefix=name+'-') as directory:
            stage = Path(directory)
            copy_sources(stage)
            for phase, data, expected in [('baseline', original, 0), ('withdrawal', mutant, 1), ('restored', original, 0)]:
                (stage / file).write_bytes(data)
                if file.endswith('.js'):
                    syntax = subprocess.run(['node','--check',file], cwd=stage, capture_output=True, timeout=30)
                    assert syntax.returncode == 0, name + ': syntax errors are invalid, not killed'
                run = subprocess.run(command, cwd=stage, capture_output=True, text=True, timeout=30)
                raw = '$ '+' '.join(command)+'\n'+run.stdout+run.stderr+'\nexit='+str(run.returncode)+'\n'
                log = name+'.'+phase+'.log'
                (output / log).write_text(raw, encoding='utf-8', newline='\n')
                named = phase != 'withdrawal' or (named_failure(raw,marker,judge) and
                    not any(word in raw for word in ['SyntaxError','ReferenceError','TypeError','ERROR:']))
                assert run.returncode == expected and named, name+' '+phase+' see '+str(output / log)
                row['phases'].append({'phase':phase,'exit':run.returncode,'log':log,
                    'log_sha256':hashlib.sha256(raw.encode()).hexdigest()})
            assert (stage / file).read_bytes() == original
        report['cases'].append(row)
        print(name+' 0/1/0 '+marker)
    (output / 'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
