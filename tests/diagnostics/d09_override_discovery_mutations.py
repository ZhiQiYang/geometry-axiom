"""Named D09 discovery withdrawals; isolated source copies, actual Node judge.

Missing/ambiguous anchors, syntax/setup errors and timeouts never count as kills.
No mutation ledger or architecture evidence is edited by this diagnostic.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time

CASES=[
    ("D09_DISCOVERY_DROP_TOP_SUMMARY", "${renderOverrideOverview(p?.id)}", "",
     "^D09 discovery starts before", "D09_DISCOVERY_FIRST_SCREEN_OVERVIEW"),
    ("D09_DISCOVERY_DROP_EXPLICIT_ZERO",
     "Object.entries(application?.overrides||{}).map",
     "Object.entries(application?.overrides||{}).filter(([,source])=>source.kind!=='literal'||source.value!==0).map",
     "^D09 discovery counts explicit zero", "D09_DISCOVERY_ZERO_COUNTS"),
    ("D09_DISCOVERY_INCLUDE_OTHER_FACES",
     "const objects=bindingsForPlacement(placementId).filter",
     "const objects=list(state.snapshot.sources??state.snapshot.bindings).filter",
     "^D09 discovery separates actual object", "D09_DISCOVERY_OBJECT_SCOPE"),
    ("D09_DISCOVERY_REMOVE_EXPLICIT_REVEAL",
     "if(details){details.open=true;const control=face?",
     "if(false&&details){details.open=true;const control=face?",
     "^D09 discovery reveal is", "D09_DISCOVERY_EXPLICIT_REVEAL"),
    ("D09_DISCOVERY_RESTORE_NEAREST",
     "scrollIntoView({block:'center',inline:'nearest'})",
     "scrollIntoView({block:'nearest',inline:'nearest'})",
     "^D09 discovery reveal keeps", "D09_DISCOVERY_REVEAL_STRICT_CLIP"),
]
DRIVER_CASES=[
    ("D09_COLD_DROP_REFERENCE_OWNERSHIP",
     "const gridIds=new Set(references.grids.filter", "const gridIds=new Set(snapshot.grids.filter",
     "^D09 cold driver counts raw native", "D09_COLD_NATIVE_SHAPE"),
    ("D09_COLD_IGNORE_REVISION",
     "assert.equal(first.revision,last.revision,'D09_COLD_NATIVE_REVISION');", "",
     "^D09 cold driver refuses missing", "D09_COLD_MIXED_REVISION_REJECTED"),
    ("D09_COLD_INCLUDE_FOREIGN_TARGETS",
     ":r.target.kind==='timber'&&timberIds.has(r.target.id)", ":timberIds.has(r.target.id)",
     "^D09 cold driver preserves explicit", "D09_COLD_NATIVE_OWNERSHIP"),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def named_failure(output, pattern, assertion):
    failures=re.findall(r'^not ok \d+ - ([^\n]+)\n(  ---\n.*?^  \.\.\.)',output,re.M|re.S)
    if len(failures)!=1:return False
    title,body=failures[0]
    error=re.search(r'^  error: [^\n]*(?:\n    [^\n]*)*',body,re.M)
    return bool(re.search(pattern,title) and error and assertion in error.group(0)
                and "  code: 'ERR_ASSERTION'" in body and "  name: 'AssertionError'" in body)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    product=root/'geometry-web/engineering-workspace.js'
    driver=root/'tests/integration/d09_override_discovery_browser.cjs'
    judge=root/'tests/test_d09_override_discovery.js'
    original=product.read_bytes();driver_original=driver.read_bytes();source=original.decode('utf-8')
    result={'schema':'d09-override-discovery-withdrawals/1','sourceSha256':sha(original),
            'testSha256':sha(judge.read_bytes()),'runnerSha256':sha(Path(__file__).read_bytes()),
            'driverSha256':sha(driver.read_bytes()),'cases':[]}
    def run(label,target,pattern=None,source_env='GEOMETRY_D09_DISCOVERY_SOURCE'):
        command=['node','--test','--test-reporter=tap']
        if pattern:command.append('--test-name-pattern='+pattern)
        command.append(str(judge));start=time.monotonic()
        try:
            p=subprocess.run(command,cwd=root,env={**os.environ,source_env:str(target)},
                             capture_output=True,text=True,timeout=45)
            code,stdout,stderr=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired:
            code,stdout,stderr='timeout','','Node exceeded the unchanged 45 s diagnostic bound\n'
        (out/(label+'.stdout')).write_text(stdout,encoding='utf-8',newline='\n')
        (out/(label+'.stderr')).write_text(stderr,encoding='utf-8',newline='\n')
        return {'exit':code,'seconds':time.monotonic()-start,'command':command,
                'sourceSha256':sha(target.read_bytes())},stdout+stderr
    baseline,log=run('baseline',product)
    result['baseline']=baseline;result['ok']=baseline['exit']==0 and '# pass 12' in log and '# skipped 0' in log
    if result['ok']:
        all_cases=[(product,'GEOMETRY_D09_DISCOVERY_SOURCE',case) for case in CASES]+[(driver,'GEOMETRY_D09_COLD_DRIVER_SOURCE',case) for case in DRIVER_CASES]
        for target,source_env,(name,old,new,pattern,assertion) in all_cases:
            source=target.read_text(encoding='utf-8')
            row={'name':name,'assertion':assertion,'anchorCount':source.count(old)}
            if row['anchorCount']!=1:
                row['status']='invalid-anchor';result['ok']=False;result['cases'].append(row);continue
            with tempfile.TemporaryDirectory(prefix='d09-discovery-') as tmp:
                mutant=Path(tmp)/target.name;mutant.write_text(source.replace(old,new),encoding='utf-8',newline='\n')
                syntax=subprocess.run(['node','--check',str(mutant)],capture_output=True,text=True,timeout=45)
                row['syntaxExit']=syntax.returncode
                if syntax.returncode:
                    row['status']='invalid-syntax';result['ok']=False;result['cases'].append(row);continue
                changed,failure=run(name,mutant,pattern,source_env)
            restored,restored_log=run(name+'-restored',target,source_env=source_env)
            killed=changed['exit']==1 and named_failure(failure,pattern,assertion) and '# fail 1' in failure
            green=restored['exit']==0 and '# pass 12' in restored_log and '# skipped 0' in restored_log
            row.update({'withdrawal':changed,'restored':restored,'exitSequence':[baseline['exit'],changed['exit'],restored['exit']],
                        'status':'killed' if killed and green else 'unverified'})
            result['ok']=result['ok'] and killed and green;result['cases'].append(row)
    result['checkoutUnchanged']=product.read_bytes()==original and driver.read_bytes()==driver_original;result['ok']=result['ok'] and result['checkoutUnchanged']
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
