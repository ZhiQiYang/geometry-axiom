"""Read-only parent reader comparison in a disposable source fixture (no worktree)."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '635dd86ee368579aec444fb3ba16e48bccf4877e'


def main():
    evidence = Path(sys.argv[1]).resolve()
    evidence.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='geo198-parent-reader-') as temp:
        temp = Path(temp)
        archive = temp/'parent.tar'
        with archive.open('wb') as target:
            subprocess.run(['git','archive','--format=tar',BASE],cwd=ROOT,stdout=target,check=True)
        fixture = temp/'source'
        fixture.mkdir()
        with tarfile.open(archive) as source:
            source.extractall(fixture,filter='data')
        identity = {'head':BASE,'tree':subprocess.check_output(['git','rev-parse',BASE+'^{tree}'],cwd=ROOT,text=True).strip(),
                    'source_sha256':hashlib.sha256((fixture/'current_geometry.c').read_bytes()).hexdigest(),
                    'reader_sha256':hashlib.sha256((fixture/'geometry-guide/公理層-閱讀器.html').read_bytes()).hexdigest(),
                    'scope':'parent reader suite only; not a parent aggregate or WSL receipt'}
        (evidence/'identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n')
        argv = [sys.executable,str(fixture/'tests/_unittest_runner.py'),str(fixture/'tests/test_axiom_reader.py'),
                '--json-out',str(evidence/'result.json'),'--log',str(evidence/'reader.log')]
        proc = subprocess.run(argv,cwd=fixture,capture_output=True,text=True,timeout=900)
        (evidence/'runner.log').write_text(proc.stdout+proc.stderr)
        print('Parent reader exit:',proc.returncode)
        return proc.returncode


if __name__=='__main__':
    sys.exit(main())
