"""Reproduce #355's main-side-only semantic regression from unresolved merge.

Run before P, after T. All seven owned files must still contain the ordinary
merge markers. This runner temporarily chooses only main in those conflicts,
leaves every automatic merge intact, records real tests, then restores every
original unresolved byte. It never stages, commits, rebases or pushes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OURS='b5a61bbc0cb33a1f188112cc5c7982bffbec93ff'
MAIN='343a8abe83029dd883e5e5b1b8e3112411fefe81'
BASE='405f8c5e1a637a16cbe47470faf5ae1fa02b8676'
FILES=['geometry-core/card-reference/run_archive_mutations.py','geometry-web/app.js',
       'geometry-web/cdp_test.js','geometry-web/parameters.js','geometry-web/project-store.js',
       'geometry-web/reference-workspace.js','tests/test_scenario_project_store.js']
COMMAND=['node','--test','tests/diagnostics/r355_merge_contracts.cjs','tests/diagnostics/r355_merge_routes.cjs']
PATTERN=re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> origin/main\n',re.M|re.S)

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def main(out):
    assert git('rev-parse','HEAD')==OURS
    assert git('rev-parse','MERGE_HEAD')==MAIN
    assert git('merge-base',OURS,MAIN)==BASE
    originals={name:(ROOT/name).read_bytes() for name in FILES}
    selected={}
    for name,source in originals.items():
        text,count=PATTERN.subn(lambda m:m[2],source.decode())
        assert count>0,(name,'not the specified unresolved ordinary merge state')
        selected[name]=(text,count)
    out.mkdir(parents=True,exist_ok=False)
    report={'ours':OURS,'main':MAIN,'merge_base':BASE,'command':COMMAND,'before':{},'syntax':[]}
    try:
        for name,(text,count) in selected.items():
            report['before'][name]={'sha256':hashlib.sha256(originals[name]).hexdigest(),'conflicts':count}
            (ROOT/name).write_text(text)
        for name in FILES:
            if name.endswith('.js'):
                result=subprocess.run(['node','--check',name],cwd=ROOT,capture_output=True)
                report['syntax'].append({'file':name,'exit':result.returncode})
                assert result.returncode==0,result.stderr.decode()
        result=subprocess.run(COMMAND,cwd=ROOT,capture_output=True,timeout=30)
        (out/'stdout.log').write_bytes(result.stdout)
        (out/'stderr.log').write_bytes(result.stderr)
        text=(result.stdout+result.stderr).decode()
        report['exit']=result.returncode
        for label in ['tests','pass','fail','skipped','cancelled']:
            match=re.search(r'^(?:#|ℹ) '+label+r' (\d+)$',text,re.M)
            report[label]=int(match[1]) if match else None
        report['failed_names']=[line for line in text.splitlines() if line.startswith(('✖ ','not ok '))]
        assert report['exit']==1 and report['tests']==15 and report['pass']==2 and report['fail']==13
        assert report['skipped']==0 and report['cancelled']==0
        assert 'SyntaxError:' not in text and 'ReferenceError:' not in text
    finally:
        for name,data in originals.items():(ROOT/name).write_bytes(data)
        report['unresolved_restored']=all((ROOT/name).read_bytes()==data for name,data in originals.items())
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['exit','tests','pass','fail','skipped','cancelled','unresolved_restored']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
