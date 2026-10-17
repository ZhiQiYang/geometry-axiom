"""P-153: auto-registered native tests and two isolated frontend mutants."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
FILES = ['geometry-web/grid-inspector.js','geometry-web/grid-system-workspace.js',
         'tests/test_grid_inspector_stagger.cjs']


def main():
    originals = {p: (ROOT / p).read_bytes() for p in FILES}
    stagger = b"const stagger=d.parameterRefs?.stagger||d.stagger!=null?` stagger ${token('stagger')}`:'';"
    assert originals[FILES[0]].count(stagger) == 1
    source = originals[FILES[1]]
    start = source.index(b'  function sourceDraft(s) {')
    end = source.index(b'  function anchor(', start)
    body = source[start:end]
    assert body.count(b'    return result;') == 1
    restore_old = b"    for(const a of axes){const old=s.source?.[a+'Definition'];if(old?.stagger!=null&&!Object.hasOwn(result[a+'Definition'],'stagger'))result[a+'Definition'].stagger=old.stagger;}\n    return result;"
    mutant_draft = source[:start] + body.replace(b'    return result;', restore_old) + source[end:]
    phases = [('fixed',{}),('mutant-stagger',{FILES[0]:originals[FILES[0]].replace(stagger,b"const stagger='';")}),
              ('mutant-sourceDraft',{FILES[1]:mutant_draft}),('restored',{})]
    receipt = {}
    with tempfile.TemporaryDirectory(prefix='geo263-p153-') as folder:
        copy = Path(folder)
        for phase, changes in phases:
            for p, data in originals.items():
                target = copy / p
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(changes.get(p,data))
            env = dict(os.environ,GEOMETRY_263_TRANSCRIPT=str(OUT / (phase+'.jsonl')))
            started = time.monotonic()
            result = subprocess.run(['node','--test','--test-reporter=spec',str(copy / FILES[2])],
                                    env=env,capture_output=True,timeout=60)
            (OUT / (phase+'.stdout')).write_bytes(result.stdout)
            (OUT / (phase+'.stderr')).write_bytes(result.stderr)
            receipt[phase] = {'actual_exit':result.returncode,'seconds':time.monotonic()-started,
                              'test_sha256':hashlib.sha256(originals[FILES[2]]).hexdigest(),
                              'source_sha256':{p:hashlib.sha256(changes.get(p,b)).hexdigest() for p,b in originals.items()}}
            print(phase,'exit',result.returncode)
    (OUT / 'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for phase in ('fixed','restored'):
        text=(OUT / (phase+'.stdout')).read_text()
        assert receipt[phase]['actual_exit']==0 and 'tests 13' in text and 'pass 13' in text and 'fail 0' in text
    for phase,needle in [('mutant-stagger','GEO263_STAGGER_LOST:'),
                         ('mutant-sourceDraft','GEO263_SOURCE_DRAFT_MUST_NOT_RESTORE_REMOVED_STAGGER')]:
        text=(OUT / (phase+'.stdout')).read_text()
        assert receipt[phase]['actual_exit']==1 and needle in text and 'skipped 0' in text
    assert all((ROOT/p).read_bytes()==b for p,b in originals.items())
    print('PASS: 13 registered tests; both mutants caught; original sources unchanged')


if __name__=='__main__':
    main()
