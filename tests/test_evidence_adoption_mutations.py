"""R365 adoption mutation table and isolated executable oracle.

Normal unittest checks live source needles and named behavior assertions.
--run DIR executes JS mutants; --native additionally builds two C mutants with
the local POSIX cc -O0 toolchain. All products live outside the source checkout.
No old ledger is relabeled as a new run.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
APP='geometry-web/evidence-links-app.js'
PARAM='geometry-web/parameters.js'
OWNER='geometry-web/reference-workspace.js'
TRANSPORT='geometry-web/app.js'
NATIVE='geometry-web/source-inspector-bridge.inc'
TESTS=['tests/test_evidence_adoption_app.cjs','tests/test_evidence_parameter_adoption.cjs','tests/test_evidence_adoption_transport.cjs']
CASES=[
 ('R365_ADOPTION_KEEPS_OTHER_OWNERS',OWNER,"      // The lease owns this evidence record. A late readonly objects response\n      // may already have marked another owner's grid sources lost/orphaned.\n      // Keep those current records; the adopted record was validated before\n      // the native request, including the reserved automatic marking capacity.\n      const current=context().featureAttachments.filter(record=>record.kind!==E.KIND);\n      const adopted=adoption.proposal.find(record=>record.kind===E.KIND);\n      context().featureAttachments=structuredClone([...current,adopted]);",'      context().featureAttachments=structuredClone(adoption.proposal);','R365_ADOPTION_PRESERVES_OTHER_OWNER_MARKING'),
 ('R365_PREPARE_BEFORE_PARAMETER_CONFIRM',PARAM,'if(s.evidenceAdoption){','if(false){','R365_PREPARE_BEFORE_CONFIRM'),
 ('R365_ADOPTION_OBSERVE',OWNER,'if(result.ok&&adoption&&assemblyConfirmationCurrent(adoption)){','if(false){','R365_ADOPTION_ACTUALLY_SAVED'),
 ('R365_ONE_CORE_METADATA_STEP',OWNER,'if(result.history_changed===false)history.push(history.snapshot(),"local","採用證據值");','if(true)history.push(history.snapshot(),"local","採用證據值");','R365_ONE_HISTORY_STEP'),
 ('R365_EXACT_CANDIDATE_RECEIPT',OWNER,'if(adoption&&result.ok&&assemblyConfirmationCurrent(adoption)&&','if(false&&adoption&&result.ok&&assemblyConfirmationCurrent(adoption)&&','R365_MATCHED_NATIVE_RECEIPT_REQUIRED'),
 ('R365_PARAMETER_OWNER_AFTER_PREPARE',PARAM,'if(!ownsPresentation()||s.preview!==p)throw new Error(\'採用期間參數或畫面已變更，未送出確認。\');','if(false)throw new Error(\'採用期間參數或畫面已變更，未送出確認。\');','R365_RETIRED_PREFILL_NO_CONFIRM'),
 ('R365_PREPARE_EXACT_RATIONAL',APP,'    E.previewAdoption(link,candidate);','    /* removed candidate rational gate */','R365_CANDIDATE_RATIONAL_AND_IDENTITY'),
 ('R365_EXACT_RECOVERY_LEASE',TRANSPORT,'try{confirmation=ReferenceWorkspace.beginEvidenceConfirmation(evidenceToken);}catch(error){return {ok:false,error:error.message};}\n    if(confirmation)pendingAssemblyConfirmations.set(requestId,confirmation);','try{confirmation=ReferenceWorkspace.beginEvidenceConfirmation(evidenceToken);}catch(error){return {ok:false,error:error.message};}','R365_EXACT_RECOVERY_RELEASES_OWNER'),
 ('R365_CANCEL_ADOPTION_HANDLE',PARAM,'      ReferenceWorkspace.cancelEvidenceConfirmation?.(previous.token);','      /* removed metadata cancellation */','R365_DISCARD_RETIRES_METADATA'),
 ('R365_NATIVE_FIELD_TYPE',APP,"type:live.parameterField?.type,formula:live.parameterField?.expression?.op!=='literal'","type:'dimension',formula:false",'R365_NATIVE_FIELD_ADOPTION_GATE'),
 ('R365_TYPED_REVERSE_FILTER',APP,'const links=E.linksFor(view.links,target),parameter=', 'const links=view.links,parameter=','R365_TYPED_REVERSE_LIST_0'),
 ('R365_ACTIVATION_REVISION_GATE',APP,"if(!current(initial))throw Error('讀取身分帳期間專案已變更，未啟用。');",'/* removed revision guard */','R365_REVISION_CHANGE_BEFORE_ACTIVATION'),
 ('R365_ACTIVATION_SELF_EVENT',APP,"if(name==='geometry-definition-changed'&&activatingLedger){parameterHost=null;objectHosts=[];return;}",'/* removed self-event ownership */','R365_ACTIVATION_EVENT_KEEPS_OPERATION'),
 ('R365_PARALLEL_READ_ONLY', 'geometry-web/evidence-links.js','const seq=sequence,s=stamp(),v=bundle();const links=[];','const seq=++sequence,s=stamp(),v=bundle();const links=[];','R365_PARALLEL_READ_VIEWS'),
]
NATIVE_CASES=[
 ('R365_NATIVE_CANDIDATE_AFTER_PINS',NATIVE,'SiIndex *s=si_build(candidate);','SiIndex *s=si_build(&g_world);','R365_CANDIDATE_PINS_ARE_AFTER','test_candidate_read_is_readonly_and_pins_equal_the_exact_confirmed_candidate'),
 ('R365_NATIVE_EXACT_TOKEN',NATIVE,'g_preview.token!=token||!g_preview.valid||!g_preview.transaction','!g_preview.valid||!g_preview.transaction','R365_CANDIDATE_TOKEN_REQUIRED','test_wrong_token_does_not_consume_the_valid_candidate'),
]


def digest(value):return hashlib.sha256(value).hexdigest()
def check():
    problems=[]
    oracle='\n'.join((ROOT/p).read_text(encoding='utf-8') for p in TESTS+['tests/test_evidence_adoption_native.py'])
    for name,path,before,after,marker,*_ in CASES+NATIVE_CASES:
        source=(ROOT/path).read_text(encoding='utf-8')
        if source.count(before)!=1:problems.append(f'{name}: source anchor count {source.count(before)} != 1')
        if marker not in oracle:problems.append(f'{name}: missing named behavior oracle {marker}')
    return problems


class EvidenceAdoptionMutationRegistry(unittest.TestCase):
    def test_live_sources_and_named_adoption_oracles(self):
        self.assertEqual(check(),[],'R365_ADOPTION_MUTATION_REGISTRY')


def run_mutations(destination,native=False):
    assert check()==[],check()
    out=Path(destination).resolve();out.mkdir(parents=True,exist_ok=True)
    receipts=[]
    with tempfile.TemporaryDirectory(prefix='r365-adoption-mutants-') as directory:
        work=Path(directory)/'source'
        shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('.git','__pycache__','feedback'))
        def run(command,label):
            result=subprocess.run(command,cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
            (out/(label+'.log')).write_text(result.stdout,encoding='utf-8',newline='\n');return result
        command=['node','--test',*TESTS]
        assert run(command,'baseline-js').returncode==0,'R365 mutation baseline must pass'
        for name,path,before,after,marker in CASES:
            file=work/path;original=file.read_bytes();mutated=original.replace(before.encode(),after.encode(),1)
            try:
                file.write_bytes(mutated);result=run(command,name)
                failure=result.stdout.split('failing tests:',1)[-1]
                assert result.returncode!=0 and marker in failure and 'AssertionError' in failure,(name,result.stdout)
            finally:file.write_bytes(original)
            restored=run(command,name+'-restored');assert restored.returncode==0,(name,restored.stdout)
            receipts.append({'name':name,'source':path,'sourceSha256':digest(original),'mutatedSha256':digest(mutated),
                             'oracle':marker,'baseline':0,'mutated':result.returncode,'restored':0,'runtime':'Node shipped adapters'})
        if native:
            cc=shutil.which(os.environ.get('CC','cc'))
            if not cc or os.name=='nt':raise RuntimeError('--native requires a POSIX cc toolchain; no native result was claimed')
            binary=Path(directory)/'bridge'
            compile_command=[cc,'-std=c11','-O0','-g0','-w','geometry-web/web_bridge.c','-lm','-o',str(binary)]
            def compile_binary(label):
                result=run(compile_command,label)
                assert result.returncode==0,(label,result.stdout)
            # The oracle's assertions are unchanged. Only binary lookup is
            # injected for an isolated deliberately mutated bridge, as allowed
            # by _bridge.BridgeSession's instrumented-product path contract.
            script="from tests import _bridge; import unittest,sys; _bridge.find_bridge=lambda:sys.argv[1]; from tests.test_evidence_adoption_native import EvidenceAdoptionNative; r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([EvidenceAdoptionNative(sys.argv[2])]));sys.exit(0 if r.wasSuccessful() and r.testsRun==1 else 1)"
            for name,path,before,after,marker,case in NATIVE_CASES:
                file=work/path;original=file.read_bytes();mutated=original.replace(before.encode(),after.encode(),1)
                test_command=[sys.executable,'-c',script,str(binary),case]
                compile_binary(name+'-baseline-build');assert run(test_command,name+'-baseline').returncode==0
                try:
                    file.write_bytes(mutated);compile_binary(name+'-mutant-build');result=run(test_command,name)
                    assert result.returncode!=0 and 'AssertionError' in result.stdout and marker in result.stdout,(name,result.stdout)
                finally:file.write_bytes(original)
                compile_binary(name+'-restored-build');assert run(test_command,name+'-restored').returncode==0
                receipts.append({'name':name,'source':path,'sourceSha256':digest(original),'mutatedSha256':digest(mutated),
                                 'oracle':marker,'baseline':0,'mutated':result.returncode,'restored':0,'runtime':'POSIX cc -std=c11 -O0 real bridge'})
    record={'nativeRequested':native,'receipts':receipts,'oracleSha256':{p:digest((ROOT/p).read_bytes()) for p in TESTS+['tests/test_evidence_adoption_native.py']}}
    (out/'receipts.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'mutations':len(receipts),'killed':len(receipts),'baseline':0,'restored':0,'nativeRequested':native}))


if __name__=='__main__':
    if len(sys.argv)>=3 and sys.argv[1]=='--run':run_mutations(sys.argv[2],'--native' in sys.argv[3:])
    else:unittest.main()
