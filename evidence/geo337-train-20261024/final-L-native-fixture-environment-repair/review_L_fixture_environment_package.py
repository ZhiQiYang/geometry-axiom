"""Read-only narrow archive roundtrip; never reads live ROOT or runs a judge."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

ROOT=Path('/workspace/train337-native-L-fixture-environment-publication')
OUT=Path('/tmp/L-native-fixture-environment-package-peer')
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
PIN='5fff9be5bee11b90485ceb50668354fa353f108c93d79049aca8d1983328141f'
checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ck(name,ok):checks.append({'name':name,'passed':bool(ok)})
def main():
 OUT.mkdir(exist_ok=False)
 raw=(ROOT/'INDEX.json').read_bytes();d=json.loads(raw)
 ck('fixed_index_pin',h(raw)==PIN)
 ck('fixed_L_and_environment_only',d['L']==L and d['kind']=='Original environment diagnosis and actual source materialization, not native test pass')
 archive=ROOT/d['archive'];payload=archive.read_bytes()
 ck('archive_original_bytes_hash',len(payload)==d['archiveBytes'] and h(payload)==d['archiveSHA256'])
 expected={r['member']:r for r in d['members']};ck('index_unique107',len(expected)==len(d['members'])==107)
 captured={};seen=set()
 with tarfile.open(archive,'r:gz')as t:
  members=t.getmembers();ck('archive_exact107_members',len(members)==107)
  for m in members:
   safe=m.isfile() and not m.name.startswith('/') and '..'not in PurePosixPath(m.name).parts and m.name not in seen and m.name in expected
   ck('safe_member:'+m.name,safe);seen.add(m.name)
   if not safe:continue
   b=t.extractfile(m).read();r=expected[m.name]
   ck('member_index_bytes:'+m.name,len(b)==m.size==r['bytes'] and h(b)==r['sha256'])
   original=Path(r['sourcePath']).read_bytes()
   ck('member_original_bytes:'+m.name,b==original)
   if m.name in ('diagnosis/DIAGNOSIS.json','materialization/RESULT.json','outer/RESULT.json','actual-peer/ACTUAL_PEER.json'):captured[m.name]=json.loads(b)
 ck('exact_member_set',seen==set(expected))
 diagnosis=captured['diagnosis/DIAGNOSIS.json'];material=captured['materialization/RESULT.json'];outer=captured['outer/RESULT.json'];peer=captured['actual-peer/ACTUAL_PEER.json']
 ck('prior_native_four_ENOENT_not_passed',diagnosis['sourceSHA']==L and diagnosis['originalNode']['failed']==4 and diagnosis['originalNode']['passed']==733 and diagnosis['originalNode']['skipped']==0 and 'exit1 retained' in diagnosis['classification'])
 ck('materialization_only_no_subject',material['sourceSHA']==L and material['subjectExecutions']==0 and material['environmentMaterializationOnly'] is True and material['originalFourENOENTNotRelabeledPassed'] is True)
 ck('head_complete_tree_unchanged_flags_documented',material['headAndCompleteIndexTreeUnchanged'] is True and material['rawIndexStatAndSparseFlagsExpectedToChange'] is True)
 ck('exact_three_fixtures_397952',len(material['files'])==3 and sum(r['bytes']for r in material['files'])==397952)
 ck('materialization_outer0_not_timeout',outer['actual_process_returncode']==0 and outer['timeout_expired'] is False and outer['source_sha']==L)
 ck('original104peer_scope',peer['checks']==104 and peer['exitCode']==0 and not peer['findings'] and 'complete original native rerun still required' in peer['originalNativeR1'])
 findings=[r for r in checks if not r['passed']]
 result={'schema':'independent-L-native-fixture-environment-package-peer/1','L':L,'readScope':'107 completed archive members and their exact original sourcePath bytes; no live ROOT/product C/index/cache or test execution','checks':len(checks),'exitCode':int(bool(findings)),'findings':findings,'archiveSHA256':h(payload),'indexSHA256':h(raw),'memberCount':len(seen),'completeNativePassClaimed':False,'limits':['Narrow archive roundtrip and original completed metadata only; prior104 actual/tool15 checks not re-executed.','Original native r1 exit1 and four ENOENT retained; exact fixture materialization is environment repair only. Full original230 native rerun remains required.'],'details':checks}
 (OUT/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items()if k!='details'},ensure_ascii=False))
 return result['exitCode']
if __name__=='__main__':sys.exit(main())
