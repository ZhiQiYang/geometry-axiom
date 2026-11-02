"""Run unchanged architecture judges and assemble the existing canonical schema.

All output remains outside the checkout until explicitly adopted. No product,
judge, policy, timeout, or native executable is changed or run here.
"""
import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--main',required=True)
args=parser.parse_args()
root=args.root.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
manifest_path='geometry-core/domain-decoupling/product-architecture.json'
derived=[manifest_path,'geometry-core/domain-decoupling/product-architecture-scan.json',
         'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md',
         'geometry-core/domain-decoupling/product-architecture-receipt.json']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*argv):return subprocess.check_output(['git',*argv],cwd=root)
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
head=git('rev-parse','HEAD').decode().strip()
assert git('status','--porcelain')==b''
manifest_raw=(root/manifest_path).read_bytes();manifest=json.loads(manifest_raw)
stages={}
for record in git('ls-files','--stage','-z').split(b'\0'):
    if record:
        meta,path=record.split(b'\t',1);stages[path.decode()]=meta.decode().split()[1]
def snapshot():
    rows=[]
    for entry in sorted(manifest['sources']+manifest['exclusions'],key=lambda e:e['path']):
        path=root/entry['path'];raw=path.read_bytes();stat=path.stat()
        rows.append({'path':entry['path'],'sha256':sha(raw.replace(b'\r\n',b'\n')),
                     'rawSha256':sha(raw),'bytes':len(raw),'indexGitBlob':stages[entry['path']],
                     'mode':stat.st_mode,'mtimeNs':stat.st_mtime_ns})
    return rows
before=snapshot();save(out/'inputs-before.json',before)
commands=[('architecture-cli',[sys.executable,'-B','tests/architecture_contract.py','--root','.', '--manifest',manifest_path]),
          ('architecture-unit',[sys.executable,'-B','tests/test_architecture_contract.py']),
          ('architecture-product',[sys.executable,'-B','tests/test_product_architecture.py'])]
records=[]
for label,command in commands:
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
    stdout=out/(label+'.stdout');stderr=out/(label+'.stderr')
    with stdout.open('wb') as output,stderr.open('wb') as errors:
        process=subprocess.run(command,cwd=root,stdout=output,stderr=errors)
    raw_out=stdout.read_bytes();raw_err=stderr.read_bytes()
    row={'command':command,'cwd':str(root),'acceptance_sha':head,'source_sha':head,'source_variant':label,
         'environment':'local managed cloud Linux; unchanged original CLI; no GitHub run ID',
         'startedUtc':started,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'actual_process_returncode':process.returncode,'exitCode':process.returncode,'timeout_expired':False,
         'elapsedSeconds':time.monotonic()-clock,'stdout_sha256':sha(raw_out),'stderr_sha256':sha(raw_err),
         'stdout_bytes':len(raw_out),'stderr_bytes':len(raw_err),'stdout_file':str(stdout),'stderr_file':str(stderr)}
    if label!='architecture-cli':
        match=re.search(rb'Ran (\d+) tests? in ',raw_err)
        assert match and int(match[1])>0 and raw_err.rstrip().endswith(b'OK') and b'skipped=' not in raw_err
        row.update(testsRun=int(match[1]),skipped=0)
    records.append(row);save(out/'commands.json',records)
    assert process.returncode==0,(label,process.returncode)
after=snapshot();assert before==after;save(out/'inputs-after.json',after)
assert git('rev-parse','HEAD').decode().strip()==head and git('status','--porcelain')==b''
scan_raw=(out/'architecture-cli.stdout').read_bytes();scan=json.loads(scan_raw)
assert scan['ok'] is True and scan['diagnostics']==[]
inputs=[{'path':row['path'],'sha256':row['sha256']} for row in before]
closure=sha(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode())
counts={'executableFiles':len(inputs),'ownedSources':len(manifest['sources']),'exclusions':len(manifest['exclusions']),
        'edges':len(scan['edges']),'diagnostics':0,'layers':dict(Counter(e['layer'] for e in manifest['sources'])),
        'languages':dict(Counter(e['language'] for e in manifest['sources'])),
        'forbiddenIdentifiers':len(manifest['policy']['forbiddenIdentifiers']),
        'forbiddenStrings':len(manifest['policy']['forbiddenStrings'])}
report=(
    '# Product architecture — canvas sharding fixed-source canonical receipt\n\n'
    f'Actual execution source `{head}`; adopted main `{args.main}`; verified tool dependency '
    '`502a64ff6214dd6060927b7f14643a533536f20d`. This is a local managed-cloud Linux execution '
    'of the original three commands, with no GitHub run ID.\n\n'
    f'All three commands exited 0; generic {records[1]["testsRun"]} and product {records[2]["testsRun"]} tests '
    f'completed without skips. {counts["executableFiles"]} inputs, {counts["ownedSources"]} owned sources, '
    f'{counts["exclusions"]} exclusions, {counts["edges"]} edges, 0 diagnostics. '
    f'LF input closure `{closure}`. Source, index, and every input raw/LF identity were unchanged across execution.\n\n'
    'The manifest preserves the adopted K/W/H policy and inherited R06 typed repeat provenance/finite derived-host '
    'reader scope; the canvas harness/receipt tools and current exclusions are pinned to their actual LF bytes. '
    'The four canonical outputs are derived artifacts and are excluded from their own input closure.\n\n'
    'This receipt certifies the static graph and its two unchanged architecture judges only. '
    'Generic mutation execution at fixed S 76d311cf, downloaded official binaries, the pending full census, and browser '
    'execution retain their separate source-bound receipts. It does not relabel them as execution at this head, '
    'or claim a new performance, Windows, dynamic reading-A, or W-lexicon audit.\n'
).encode()
receipt={'schema':'geometry-product-architecture-receipt/1','hashMode':'sha256 after CRLF-to-LF normalization',
         'inputClosureHashSerialization':'SHA-256 of UTF-8 JSON for the path-sorted inputs array, with ensure_ascii=false and separators=(comma,colon); each entry has path then sha256, and no trailing newline.',
         'inputClosureExcludes':derived,'inputClosureExclusionReason':'Non-executable derived artifacts; receipt does not hash itself.',
         'notClaimed':['native execution at this head','generic mutation rerun at this head','browser execution at this head',
                       'new performance comparison','Windows probes','new W lexicon completeness audit'],
         'headBinding':'Original three unchanged judges ran at this exact clean source; all declared input raw/LF/index identities were equal before and after. Canonical artifact assembly follows outside the source tree.',
         'createdUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'basis':'Existing canonical geometry-product-architecture-receipt/1 schema; source-bound original three commands and unchanged adopted policies.',
         'sourceBaseHead':head,'headObservedBefore':head,'headObservedAfter':head,'actualAdoptedMain':args.main,
         'executionEnvironment':'local managed cloud Linux; no GitHub run ID','manifestSha256':sha(manifest_raw.replace(b'\r\n',b'\n')),
         'scannerSha256':sha((root/'tests/architecture_contract.py').read_bytes().replace(b'\r\n',b'\n')),
         'scanSha256':sha(scan_raw),'reportSha256':sha(report),'inputClosureSha256':closure,'counts':counts,
         'scanPassed':True,'actualCliScan':records[0],'validation':records[1:],'inputs':inputs,
         'environment':{'pythonExecutable':sys.executable,'pythonVersion':sys.version,'platform':platform.platform(),
                        'nodeVersion':subprocess.check_output(['node','--version'],cwd=root,text=True).strip()}}
artifacts=out/'canonical';artifacts.mkdir()
(artifacts/'product-architecture.json').write_bytes(manifest_raw)
(artifacts/'product-architecture-scan.json').write_bytes(scan_raw)
(artifacts/'PRODUCT-ARCHITECTURE.md').write_bytes(report)
save(artifacts/'product-architecture-receipt.json',receipt)
save(out/'summary.json',{'executionHead':head,'actualAdoptedMain':args.main,'inputClosureSha256':closure,
                        'counts':counts,'sourceAndInputsUnchanged':True,'commands':records,
                        'artifacts':{p.name:sha(p.read_bytes()) for p in sorted(artifacts.iterdir())}})
print(json.dumps({'source':head,'counts':counts,'closure':closure,'commandExits':[r['exitCode'] for r in records]}))
