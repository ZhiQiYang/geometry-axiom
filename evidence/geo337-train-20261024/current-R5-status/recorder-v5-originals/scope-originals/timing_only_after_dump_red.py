"""Independent original timing/tail only; never overrides the original full P189 red."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent

def h(body):return hashlib.sha256(body).hexdigest()
def main():
    final=sys.argv[1];prior=Path(os.environ['GEO261_P189_FULL_OUT']).resolve()
    root_receipt=json.loads((prior/'receipt.json').read_bytes())
    assert root_receipt['gate']=='p189' and root_receipt['source_sha']==final
    assert root_receipt['passed'] is False and root_receipt['launcher_exit_code']==1
    phase=root_receipt['phases'][0]
    assert phase['name']=='p189' and phase['primary_returncode']==1
    recorded=phase['outer_command'];directory=Path(recorded['directory'])
    stderr=(directory/'stderr.bin').read_bytes()
    assert h(stderr)==recorded['stderr_sha256']
    assert b'AssertionError: dump ' in stderr and '不同：'.encode()in stderr
    assert not (prior/'measurement/samples.tsv').exists() and not (prior/'measurement/loadfile-samples.json').exists(),'no resampling: original full timing must not have started'
    provenance=json.loads((prior/'measurement/provenance.json').read_bytes())
    assert provenance['shas']=={'main':'adbaebf9c73ea6801d7b4d5214e4b846b132923b','base':'3e600772076465fc65a26ac09055028301c0fb0b','fix':final}
    out=Path(os.environ['GEO261_P189_OUT']);work=Path(os.environ['GEO261_P189_WORK'])
    assert not out.exists() and not work.exists()
    out.mkdir(parents=True);work.mkdir(parents=True)
    identities=[]
    for side,wanted in provenance['binaries_sha256'].items():
        source=prior/'work'/side/'bridge';body=source.read_bytes();assert h(body)==wanted
        (work/side).mkdir();destination=work/side/'bridge';shutil.copy2(source,destination)
        assert destination.read_bytes()==body
        identities.append({'side':side,'source_sha':provenance['shas'][side],'from':str(source),'path':str(destination),'bytes':len(body),'sha256':wanted})
    scope={'scope':'timing-only; original full P189 dump assertion remains red','overall_P189_passed':False,'source_sha':final,'original_full_out':str(prior),'original_full_receipt_sha256':h((prior/'receipt.json').read_bytes()),'original_full_exit':1,'binary_identities':identities,'dump_equivalence_executed_in_this_stage':False,'sampling_retried':False,'original_timing_tail_source':'p189_verify.original.py.txt'}
    (out/'TIMING_ONLY_SCOPE.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
    raw=(HERE/'p189_verify.original.py.txt').read_bytes();assert h(raw)=='93a5d5715274bf64dcbe748dd4c724b00be0930264936a8d0ceb0e12a639a878'
    tree=ast.parse(raw.decode());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    starts=[i for i,n in enumerate(function.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='timing'for t in n.targets)]
    assert len(starts)==1
    tail=ast.Module(body=function.body[starts[0]:],type_ignores=[])
    tail_raw=''.join(raw.decode().splitlines(keepends=True)[tail.body[0].lineno-1:tail.body[-1].end_lineno])
    (out/'original-timing-tail.py.txt').write_text(tail_raw)
    scope['original_tail_ast_sha256']=h(ast.dump(tail,include_attributes=False).encode())
    spec=importlib.util.spec_from_file_location('p189_bound_original',HERE/'p189_verify.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.__dict__.update(provenance={**provenance,'scope':'timing-only; original full P189 remains red','overall_P189_passed':False},started=time.time(),dumps=[])
    code=None
    try:
        exec(compile(tail,str(HERE/'p189_verify.original.py.txt'),'exec'),module.__dict__)
        code=0
    except SystemExit as error:
        assert type(error.code)is int and error.code in(0,1)
        code=error.code
    except BaseException as error:
        scope['timing_tail_exception']={'type':type(error).__name__,'repr':repr(error)}
        raise
    finally:
        for item in identities:
            assert h(Path(item['path']).read_bytes())==item['sha256'] and h(Path(item['from']).read_bytes())==item['sha256']
        scope['timing_tail_exit']=code
        (out/'TIMING_ONLY_SCOPE.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
    return code
if __name__=='__main__':raise SystemExit(main())
