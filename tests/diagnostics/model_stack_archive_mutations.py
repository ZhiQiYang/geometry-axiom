"""Named stack archive mutants; assertion failures alone count as kills."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STORE = 'geometry-web/project-store.js'
TEST = 'tests/test_model_stack_archive.cjs'
MUTANTS = (
    ('R362_STACK_MODEL_ROOT_VALIDATION',
     'modelIdentity().validateSourceIdentity(record.sourceIdentity, {...i, boundary_id: s.boundary_id});',
     'void 0;', 'R362_STACK_MODEL_ROOT_VALIDATION'),
    ('R362_STACK_ROOM_READER',
     'Features.ROOM_DISPLAY_CAPABILITY, Features.ROOM_CANDIDATE_CAPABILITY, EVIDENCE_CAPABILITY, EVIDENCE_V2_CAPABILITY, SCENARIO_CAPABILITY, CASE_CAPABILITY];',
     'Features.ROOM_DISPLAY_CAPABILITY, EVIDENCE_CAPABILITY, EVIDENCE_V2_CAPABILITY, SCENARIO_CAPABILITY, CASE_CAPABILITY];',
     'R362_STACK_PARENT_READER_CAPABILITY:room-candidate-drafts/1'),
    ('R362_STACK_EVIDENCE_V2_READER',
     'Features.ROOM_DISPLAY_CAPABILITY, Features.ROOM_CANDIDATE_CAPABILITY, EVIDENCE_CAPABILITY, EVIDENCE_V2_CAPABILITY, SCENARIO_CAPABILITY, CASE_CAPABILITY];',
     'Features.ROOM_DISPLAY_CAPABILITY, Features.ROOM_CANDIDATE_CAPABILITY, EVIDENCE_CAPABILITY, SCENARIO_CAPABILITY, CASE_CAPABILITY];',
     'R362_STACK_PARENT_READER_CAPABILITY:geometry-evidence-links/2'),
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run(root, output, name, phase, assertion):
    process = subprocess.run(['node','--test','--test-reporter=spec',TEST],cwd=root,
                             capture_output=True,timeout=45)
    log = process.stdout + process.stderr
    (output / (name+'-'+phase+'.log')).write_bytes(log)
    text = log.decode(errors='replace')
    counts = {key:int(re.search(r'(?m)^ℹ '+key+r' (\d+)$',text).group(1))
              for key in ('tests','pass','fail','cancelled','skipped','todo')}
    assert counts['tests']==1 and counts['cancelled']==counts['skipped']==counts['todo']==0, text
    if phase == 'mutant':
        assert process.returncode==1 and counts['fail']==1 and counts['pass']==0, text
        assert 'AssertionError [ERR_ASSERTION]' in text and assertion in text, text
        assert "code: 'ERR_ASSERTION'" in text, text
    else:
        assert process.returncode==0 and counts['pass']==1 and counts['fail']==0, text
    return {'exit':process.returncode,'counts':counts,'logSha256':digest(log)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    output=args.out.resolve()
    output.mkdir(parents=True,exist_ok=False)
    original=(ROOT/STORE).read_text()
    result=[]
    with tempfile.TemporaryDirectory(prefix='model-stack-archive-mutants-') as temporary:
        work=Path(temporary)
        (work/'geometry-web').mkdir()
        (work/'tests').mkdir()
        for file in (ROOT/'geometry-web').glob('*.js'):
            shutil.copyfile(file,work/'geometry-web'/file.name)
        for relative in ('geometry-app/application.js','geometry-templates/woodworking/frontend.js',
                         'geometry-templates/woodworking/cutting.js','geometry-core/interval-allocation.js'):
            destination=work/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,destination)
        vendor=Path('geometry-web/vendor/fflate/umd/index.js')
        (work/vendor).parent.mkdir(parents=True)
        shutil.copyfile(ROOT/vendor,work/vendor)
        shutil.copyfile(ROOT/TEST,work/TEST)
        for name,before,after,assertion in MUTANTS:
            assert original.count(before)==1,(name,'mutation anchor is not unique')
            (work/STORE).write_text(original)
            baseline=run(work,output,name,'baseline',assertion)
            (work/STORE).write_text(original.replace(before,after))
            mutated_sha=digest((work/STORE).read_bytes())
            mutant=run(work,output,name,'mutant',assertion)
            (work/STORE).write_text(original)
            restored=run(work,output,name,'restored',assertion)
            result.append({'id':name,'before':before,'after':after,'assertion':assertion,
                           'mutatedSourceSha256':mutated_sha,'baseline':baseline,'mutant':mutant,'restored':restored})
            print(name,baseline['exit'],mutant['exit'],restored['exit'],flush=True)
    receipt={'schema':'model-stack-archive-mutations/1','source':STORE,'sourceSha256':digest((ROOT/STORE).read_bytes()),
             'test':TEST,'testSha256':digest((ROOT/TEST).read_bytes()),'definitionSha256':digest(Path(__file__).read_bytes()),
             'results':result}
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
