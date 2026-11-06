"""R362 runtime negative controls against the production identity adapter."""
from pathlib import Path
import hashlib, json, os, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'geometry-web/identity-ledger.js'
MUTATIONS=[
 ('R362_CURRENT_MARK',"if (observed(reviewed[i]) !== observed(live[i]))", "if (false)"),
 ('R362_CONFLICT',"|| entries.some(([key, value])", "|| false && entries.some(([key, value])"),
 ('R362_INACTIVE',"if (!active || !rootValid(root)", "if (!rootValid(root)"),
 ('R362_CURRENT_RECEIPT',"const currentIncarnation = validMark(node?.incarnation)", "const currentIncarnation = false && validMark(node?.incarnation)"),
 ('R362_TYPED_CONFIRM',"if (['role','kind','fieldId'].some", "if (false && ['role','kind','fieldId'].some"),
 ('R362_MARK_LIMIT',"BigInt(value.slice(33)) <= 18446744073709551615n", "true"),
]

def run(module):
    return subprocess.run(['node','--test','tests/test_model_identity_review.js'],cwd=ROOT,
        env={**os.environ,'MODEL_IDENTITY_REVIEW_MODULE':str(module)},capture_output=True,text=True)

def main():
    source=SOURCE.read_text(encoding='utf-8'); baseline=run(SOURCE)
    assert baseline.returncode==0, baseline.stdout+baseline.stderr
    results=[]
    with tempfile.TemporaryDirectory(prefix='r362-identity-') as temporary:
        for name,before,after in MUTATIONS:
            assert source.count(before)==1,(name,'anchor must be unique')
            path=Path(temporary)/(name+'.cjs');path.write_text(source.replace(before,after),encoding='utf-8',newline='\n')
            result=run(path); output=result.stdout+result.stderr
            assert result.returncode!=0 and name in output and 'AssertionError' in output,(name,output)
            restored=run(SOURCE);assert restored.returncode==0,restored.stdout+restored.stderr
            results.append({'name':name,'base':0,'mutant':result.returncode,'restored':0,
                'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'mutantSha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    print(json.dumps({'mutations':results},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
