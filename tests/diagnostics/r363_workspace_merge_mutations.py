"""Named 0/1/0 checks for the R363 workspace merge; no browser claim.

Run after applying the regression and product patches:
  python tests/diagnostics/r363_workspace_merge_mutations.py --root . --output /tmp/r363-workspace-evidence

Only normal ERR_ASSERTION failures in the designated test count as kills.
Timeouts, cancelled tests, missing anchors and transport crashes never count.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    source_path=root/'geometry-web/reference-workspace.js'
    fixture_path=root/'tests/fixtures/reference_workspace_vm.cjs'
    test='tests/test_r363_workspace_merge.js'
    source=source_path.read_text(encoding='utf-8')
    fixture=fixture_path.read_text(encoding='utf-8')
    originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source_path,fixture_path,root/test,
        root/'geometry-web/project-store.js',root/'tests/fixtures/native_available_capabilities.json']}

    def run(name,pattern=None,override=None,fixture_override=None):
        env=os.environ.copy()
        env.pop('GEOMETRY_TEST_REFERENCE_WORKSPACE',None)
        env.pop('GEOMETRY_R363_VM_FIXTURE',None)
        if override:env['GEOMETRY_TEST_REFERENCE_WORKSPACE']=str(override)
        if fixture_override:env['GEOMETRY_R363_VM_FIXTURE']=str(fixture_override)
        command=['node','--test','--test-reporter=tap']
        if pattern:command+=['--test-name-pattern='+pattern]
        command+=[test]
        result=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,text=True,timeout=30)
        log=output/(name+'.tap')
        log.write_text(result.stdout,encoding='utf-8',newline='\n')
        return result.returncode,result.stdout,log

    def green(name,pattern=None):
        code,text,log=run(name,pattern)
        assert code==0 and re.search(r'^# fail 0$',text,re.M) and re.search(r'^# cancelled 0$',text,re.M),(name,text)
        assert re.search(r'^# tests '+str(1 if pattern else 7)+r'$',text,re.M) and re.search(r'^# skipped 0$',text,re.M),(name,text)
        return {'exit':code,'log':log.name,'sha256':hashlib.sha256(log.read_bytes()).hexdigest()}

    baseline=green('baseline')
    cases=[
        ('W01_DROP_SCENE_REQUIREMENTS','R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION',
         "const requiredCapabilities=[...new Set([...(manifest.requiredCapabilities||[]),...P.sceneCapabilities(text)])];",
         "const requiredCapabilities=[...(manifest.requiredCapabilities||[])];",False),
        ('W02_DROP_R06_READER_PROFILE_ARGS','R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION',
         "P.readerCapabilities(candidate.capabilities,candidate.native_capabilities,manifest,candidate.final_scene,hostRecordProfile,{cutting:true})",
         "P.readerCapabilities(candidate.capabilities,{cutting:true})",False),
        ('W03_DROP_PROFILE_REVISION_GATE','R363_W04_PROFILE_REVISION_IS_EXACT',
         "      if(hostRecordProfile&&(!Number.isSafeInteger(hostRecordProfile.revision)||hostRecordProfile.revision<0||\n"
         "         preparedNativeRevision!==null&&hostRecordProfile.revision!==preparedNativeRevision||\n"
         "         nativeRevision!==null&&nativeRevision>hostRecordProfile.revision))\n"
         "        throw new Error('原生來源在讀取衍生承載面能力期間已變更，請重新開啟專案。');\n",
         '',False),
        ('W04_DROP_PRECONFIRM_LOAD_GUARD','R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER',
         'const assertPreparedCurrent=()=>{assertLoadContext(nextLoad);assertCurrent();};',
         'const assertPreparedCurrent=()=>{assertCurrent();};',False),
        ('W05_DROP_CANONICAL_REQUIREMENTS_CHECK','R363_W06_NATIVE_CANONICAL_SCENE_AND_REQUIREMENTS_AGREE',
         '        if(!sameModelData([...candidate.required_capabilities].sort(),P.sceneCapabilities(finalScene)))\n'
         '          throw new Error("工程場景能力與保存來源不一致，未變更目前專案。");\n',
         '',False),
        ('W06_DROP_DEIDENTIFIED_FIXTURE_API','R363_W01_SHARED_FIXTURE_MAIN_CONTRACT',
         "assert.ok(command==='dump'||command==='dump-deidentified','Unexpected API command: '+command);",
         "assert.ok(command==='dump','Unexpected API command: '+command);",True),
        ('W07_ALLOW_STRING_NATIVE_PROFILE','R363_W03_PROFILE_CREDENTIALS_FAIL_CLOSED',
         "Array.isArray(candidate.native_capabilities)&&candidate.native_capabilities.includes('panel-fill-native/1')",
         "candidate.native_capabilities?.includes('panel-fill-native/1')",False),
        ('W08_DROP_PREPARED_REVISION_MATCH','R363_W04_PROFILE_REVISION_IS_EXACT',
         '         preparedNativeRevision!==null&&hostRecordProfile.revision!==preparedNativeRevision||\n',
         '',False),
        ('W09_DROP_CURRENT_NATIVE_REVISION_MATCH','R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER',
         '         nativeRevision!==null&&nativeRevision>hostRecordProfile.revision))',
         '         false))',False),
    ]
    receipts=[]
    with tempfile.TemporaryDirectory(prefix='r363-workspace-mutants-') as directory:
        temporary=Path(directory)
        for name,pattern,old,new,is_fixture in cases:
            before=green(name+'-before',pattern)
            original=fixture if is_fixture else source
            assert original.count(old)==1,(name,'anchor count',original.count(old))
            mutant=temporary/(name+('.cjs' if is_fixture else '.js'))
            mutated=original.replace(old,new)
            if is_fixture:
                # Relocate only imports in this disposable fixture copy; the
                # checked-in shared fixture and product source are untouched.
                for relative in ['../../geometry-web/project-store.js','../../geometry-web/vendor/fflate/umd/index.js',
                                 '../../geometry-web/reference-workspace.js']:
                    assert mutated.count("'"+relative+"'")==1,('fixture import',relative)
                    target=(fixture_path.parent/relative).resolve()
                    mutated=mutated.replace("'"+relative+"'",json.dumps(str(target)))
            mutant.write_text(mutated,encoding='utf-8',newline='\n')
            code,text,log=run(name+'-mutant',pattern,
                              override=None if is_fixture else mutant,
                              fixture_override=mutant if is_fixture else None)
            assert code==1 and "code: 'ERR_ASSERTION'" in text and pattern in text,(name,code,text)
            assert re.search(r'^# fail 1$',text,re.M) and re.search(r'^# cancelled 0$',text,re.M),(name,text)
            assert re.search(r'^# tests 1$',text,re.M) and re.search(r'^# skipped 0$',text,re.M),(name,text)
            assert 'testTimeoutFailure' not in text and 'ERR_MODULE_NOT_FOUND' not in text,(name,text)
            restored=green(name+'-restored',pattern)
            receipts.append({'name':name,'assertion':pattern,'exits':[before['exit'],code,restored['exit']],
                             'normal_assertion':True,'mutant_log':log.name,
                             'mutant_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
                             'restored_log':restored['log']})
    restored=green('restored-full')
    assert all(hashlib.sha256(path.read_bytes()).hexdigest()==digest for path,digest in originals.items())
    report={'test_count':7,'baseline':baseline,'cases':receipts,'restored':restored,
            'mutants_killed':len(receipts),'product_source_unchanged':True,
            'inputs':{str(path.relative_to(root)):digest for path,digest in originals.items()}}
    (output/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tests':7,'mutants':len(receipts),'all_exits':[r['exits'] for r in receipts],
                      'baseline':baseline['exit'],'restored':restored['exit']},ensure_ascii=False))


if __name__=='__main__':
    main()
