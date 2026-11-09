"""Registry-only audit of the mechanical key union; restores unresolved bytes."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import runpy

ROOT=Path(__file__).resolve().parents[2]

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    path=ROOT/'tests/run_all.py'
    original=path.read_bytes()
    pattern=re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> origin/main\n',re.M|re.S)
    resolved,count=pattern.subn(lambda m:m[1]+m[2],original.decode())
    assert count==1,'run from the specified #355 unresolved mechanical merge state'
    try:
        path.write_text(resolved)
        (out/'run_all-validation.py').write_text(resolved)
        problems=runpy.run_path(str(path))['check_registry']()
        report={'temporary_resolution':'suite/key union; main model/native groups preserved',
                'before_sha256':hashlib.sha256(original).hexdigest(),
                'validation_sha256':hashlib.sha256(resolved.encode()).hexdigest(),'problems':problems}
        print(json.dumps(report,ensure_ascii=False))
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        assert problems==[]
    finally:
        path.write_bytes(original)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
