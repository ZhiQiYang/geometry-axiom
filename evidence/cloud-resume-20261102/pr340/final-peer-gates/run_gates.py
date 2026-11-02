"""Fixed-b3a source receipt checks; no product builds or mutation execution."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

SOURCE=Path('/tmp/geometry-pr340-20261102')
OUT=Path(__file__).resolve().parent
HEAD='b3a248607d7eb68d3167abbb926cf491d9b35a26'
OLD_HEAD='1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965'
MAIN='5775a9e9e46bca801a9a70aaeafcdab9f597bc4d'
TOOLS='502a64ff6214dd6060927b7f14643a533536f20d'


def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()


def metadata():
    results=[]
    for label,path in [('main','/branches/main'),('pr340','/pulls/340')]:
        url='https://api.github.com/repos/ZhiQiYang/geometry-axiom'+path
        headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'geometry-fixed-b3a-peer-readonly'}
        if os.environ.get('GH_TOKEN'):headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120) as response:
            raw=response.read();status=response.status
        target=OUT/(label+'-metadata.json');target.write_bytes(raw)
        results.append({'url':url,'file':str(target),'http_status':status,'sha256':digest(raw)})
    observed=json.loads((OUT/'main-metadata.json').read_text())['commit']['sha']
    receipt={'command':'python -B run_gates.py metadata','exit_code':0,'expected_main':MAIN,'observed_main':observed,'main_unchanged':observed==MAIN,'requests':results}
    save(OUT/'metadata-receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


def run():
    assert git('rev-parse','HEAD')==HEAD
    assert git('status','--porcelain=v1')==''
    assert git('show','-s','--format=%P',HEAD).split()==[OLD_HEAD,TOOLS]
    empty=OUT/'empty-mutation-cache';empty.mkdir(exist_ok=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',MUTATE_CACHE=str(empty))
    commands=[
        ('mutation-check',[sys.executable,'-B','tests/mutate.py','--check']),
        ('architecture-cli',[sys.executable,'-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json']),
        ('architecture-unit',[sys.executable,'-B','tests/test_architecture_contract.py']),
        ('architecture-product',[sys.executable,'-B','tests/test_product_architecture.py']),
    ]
    receipt={'schema':'geometry-pr340-fixed-source-lightgates/1','head':HEAD,'previous_head':OLD_HEAD,'previous_results_reused':False,
             'main':MAIN,'tools_source':TOOLS,'source':str(SOURCE),'source_clean_before':True,
             'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':[],
             'env':{'MUTATE_CACHE':str(empty),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},
             'limitations':['Mutation --check reads committed original ledger and source/oracle receipts in an empty cache; no binary-byte or fresh mutation execution claim.','This is new b3a evidence; earlier 1605 results remain attached to 1605.','Formal integration and mutation CI for b3a have not been generated or accepted by this local lightgate run.']}
    for label,command in commands:
        assert git('rev-parse','HEAD')==HEAD
        stdout,stderr=OUT/(label+'.stdout'),OUT/(label+'.stderr')
        with stdout.open('wb') as output,stderr.open('wb') as errors:
            process=subprocess.run(command,cwd=SOURCE,env=env,stdout=output,stderr=errors,timeout=180)
        row={'label':label,'command':command,'cwd':str(SOURCE),'head':HEAD,'exit_code':process.returncode,
             'stdout':stdout.name,'stderr':stderr.name,'stdout_sha256':digest(stdout.read_bytes()),'stderr_sha256':digest(stderr.read_bytes())}
        if label=='architecture-cli' and process.returncode==0:
            scan=json.loads(stdout.read_bytes());row.update(ok=scan.get('ok'),diagnostics=scan.get('diagnostics'),edge_count=len(scan['edges']))
            assert scan['ok'] is True and scan['diagnostics']==[]
        elif label in ['architecture-unit','architecture-product']:
            raw=stderr.read_bytes();match=re.search(rb'Ran (\d+) tests? in ',raw)
            assert match and int(match[1])>0 and not re.search(rb'\bskipped=[1-9]\d*',raw)
            row.update(tests_run=int(match[1]),skips=0)
        receipt['commands'].append(row);save(OUT/'lightgates-receipt.json',receipt)
        print(label,'head',HEAD,'exit',process.returncode,row.get('tests_run',''))
        assert process.returncode==0,(label,stderr.read_text())
    receipt['source_clean_after']=git('status','--porcelain=v1')==''
    receipt['final_head']=git('rev-parse','HEAD')
    assert receipt['source_clean_after'] and receipt['final_head']==HEAD and not list(empty.iterdir())
    receipt['empty_cache_unchanged']=True
    receipt['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt['exit_code']=0
    save(OUT/'lightgates-receipt.json',receipt)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='metadata':metadata()
    else:run()
