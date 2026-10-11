"""Actual disposable K1 JS source mutations. Never edit the working checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['test_cutting_plan.js', 'test_cutting_project_store.js', 'test_cutting_session.js', 'test_cutting_owner.js']
# Each case must fail with an assertion or an explicit conservation/identity
# validator diagnosis, never an import, syntax or environment error.
CASES = [
 ('between-kerf','cutting-plan.js','s.pieces.at(-1).end+settings.kerf','s.pieces.at(-1).end','T1'),
 ('original-end','cutting-plan.js',"kind:s.tailTrim?'trim':'none'","kind:'trim'",'T2'),
 ('short-last-kerf','cutting-plan.js','Math.min(settings.kerf,s.length-y)','settings.kerf','T2'),
 ('omit-last-cut','cutting-plan.js',"{kind:'separate',consumed:Math.min(settings.kerf,s.length-y),cuts:1}","{kind:'separate',consumed:0,cuts:0}",'T2'),
 ('leftover-threshold','cutting-plan.js','usable>=settings.minRemnant','length>=settings.minRemnant','T4'),
 ('negative-usable','cutting-plan.js','Math.max(0,length-s.tailTrim)','length-s.tailTrim','T4'),
 ('remnant-order','cutting-plan.js','(a.length-a.headTrim-a.tailTrim)-(b.length-b.headTrim-b.tailTrim)','(b.length-b.headTrim-b.tailTrim)-(a.length-a.headTrim-a.tailTrim)','T5'),
 ('dimension-dedupe','cutting-plan.js','rows.set(row.id,row)','rows.set(row.L,row)','T6'),
 ('world-kind','cutting-plan.js',"request.world?.kind!=='live'",'false','T7'),
 ('scope-capacity','cutting-plan.js','request.scopes.length>64','false','T7'),
 ('demand-capacity','cutting-plan.js','rows.size>4096','false','T7'),
 ('stale-selection','cutting-plan.js','placements.get(id)?.geometry?.surface!==scope.surface','false','T7'),
 ('empty-scope','cutting-plan.js','if(!snapshot.rows.length)diagnose','if(false)diagnose','T7'),
 ('unordered-section','cutting-settings.js',"[...s].sort((a,b)=>a-b).join('x')","s.join('x')",'T8'),
 ('material-fingerprint','cutting-settings.js','[m.id,m.version,m.fingerprint]','[m.id,m.version]','T26'),
 ('null-terminal','cutting-plan.js',"diagnose('INCOMPLETE','MATERIAL_UNRESOLVED'","diagnose('INCOMPLETE','MATERIAL_MIXED'",'T10'),
 ('missing-terminal','cutting-plan.js',"diagnose('UNSUPPORTED','NATIVE_CAPABILITY'","diagnose('INCOMPLETE','MATERIAL_UNRESOLVED'",'T10'),
 ('mixed-terminal','cutting-plan.js',"diagnose('INCOMPLETE','MATERIAL_MIXED'","diagnose('INCOMPLETE','NO_STOCK'",'T10'),
 ('allowance','cutting-plan.js','row.L+(settings.allowance??0)','row.L','T4'),
 ('tie-break','cutting-plan.js','b.C-a.C||a.timberId-b.timberId','b.C-a.C||b.timberId-a.timberId','T1'),
 ('canonical-stocks','cutting-settings.js','n.stockTypes.sort((a,b)=>a.key-b.key);','', 'R1.1 R5'),
 ('canonical-remnants','cutting-settings.js','n.remnants.sort((a,b)=>a.key-b.key);','', 'R1.1 R5'),
 ('missing-setting','cutting-plan.js',"filter(k=>settings[k]===null)","filter(k=>false)",'T19'),
 ('overlength-remnants','cutting-plan.js','...settings.remnants.filter(r=>r.stockType===stock.key).map(r=>r.length-r.headTrim-r.tailTrim)','0','T23'),
 ('exhaustion-code','cutting-plan.js',"diagnose('INCOMPLETE','REMNANT_EXHAUSTED'","diagnose('INVALID','OVER_LENGTH'",'T23'),
 ('exhaustion-all-groups','cutting-plan.js','if(failed)continue;','if(failed)break;','R1.1'),
 ('conservation','cutting-plan.js','function verify(plan,expectedIds=null){','function verify(plan,expectedIds=null){return true;','conservation detects'),
 ('typed-error','timber-schedule.js',"failure('NOT_EVALUATED'","failure('REFERENCES_UNVERIFIED'",'typed derive'),
 ('legacy-csv','timber-schedule.js',"JSON.stringify(r.sources,(key,value)=>key==='terminal'?undefined:value)",'JSON.stringify(r.sources)','F4a'),
 ('owned-terminal','timber-schedule.js',"Object.hasOwn(effective[field],'terminal')",'false','F4a'),
 ('integer-range','cutting-settings.js','&&n<=100000000','','T12 strict'),
 ('stock-lock','cutting-settings.js','if(n&&old.remnants.some','if(false&&old.remnants.some','T12b'),
 ('key-reuse','cutting-settings.js','row.key<old[counter]','false','key allocation'),
 ('stock-capacity','cutting-settings.js','v.stockTypes.length>32','false','T18 settings'),
 ('undo-highwater','project-store.js','cutting=Features.Cutting.preserveHighwater(cutting,highwater)','cutting=cutting||Features.Cutting.empty()','P-047'),
 ('new-capability','project-store.js','...(cutting?[CUTTING_CAPABILITY]:[])','...[]','T17 archive'),
 ('old-format','project-store.js','manifest.format!==CUTTING_FORMAT','false','T17b'),
 ('export-state','cutting-workspace.js','function guard(before){','function guard(before){return;','T16'),
 ('export-world','cutting-workspace.js','latest.sourceFingerprint!==candidate.worldFingerprint','false','T16 world'),
 ('export-reentry','cutting-workspace.js','if(exporting)return false;','if(false)return false;','T16 late'),
 ('context-clear','cutting-workspace.js','identity=context;scopes=[];','identity=context;','session scopes'),
 ('stock-diagnostic','cutting-workspace.js','if(Array.isArray(d.detail?.section))','if(false)', 'T8b diagnostics'),
 ('owner-stock-lock','reference-workspace.js','if(kind===P.Features.Cutting.KIND)P.Features.Cutting.transition(previous,value);','', 'actual owner rejects'),
 ('owner-history-kind','reference-workspace.js','kind === P.Features.Cutting.KIND ? "裁切設定" :','', 'actual owner P-047'),
]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='geometry-k1-js-') as directory:
  work=Path(directory);(work/'geometry-web').mkdir();(work/'tests').mkdir()
  for path in (ROOT/'geometry-web').glob('*.js'):shutil.copy2(path,work/'geometry-web'/path.name)
  target=work/'geometry-web/vendor/fflate/umd';target.mkdir(parents=True);shutil.copy2(ROOT/'geometry-web/vendor/fflate/umd/index.js',target/'index.js')
  for name in FILES:shutil.copy2(ROOT/'tests'/name,work/'tests'/name)
  def run(pattern=None):
   command=['node','--test','--test-reporter=tap']
   if pattern:command+=['--test-name-pattern',pattern]
   return subprocess.run(command+[str(work/'tests'/f) for f in FILES],capture_output=True,text=True,encoding='utf-8',timeout=60)
  baseline=run();(args.out.parent/'frontend-baseline.log').write_text(baseline.stdout+baseline.stderr,encoding='utf-8')
  if baseline.returncode:print('baseline failed');return 2
  rows=[]
  for name,file,old,new,pattern in CASES:
   path=work/'geometry-web'/file;original=path.read_text(encoding='utf-8');assert original.count(old)>=1,(name,'missing mutation anchor')
   path.write_text(original.replace(old,new,1),encoding='utf-8')
   try:result=run(pattern)
   finally:path.write_text(original,encoding='utf-8')
   log=result.stdout+result.stderr;(args.out.parent/(name+'.log')).write_text(log,encoding='utf-8')
   cause='assertion' if 'AssertionError' in log else 'invariant' if 'CONSERVATION' in log or 'DEMAND_IDENTITY' in log else None
   killed=result.returncode==1 and cause is not None and 'SyntaxError' not in log and 'MODULE_NOT_FOUND' not in log
   rows.append({'id':name,'status':'killed' if killed else 'not-killed','detectedBy':cause,'testPattern':pattern,'exitCode':result.returncode,'sourceHash':hashlib.sha256(original.encode()).hexdigest(),'mutationHash':hashlib.sha256((old+'\0'+new).encode()).hexdigest()})
   print(name+': '+rows[-1]['status'],flush=True)
  report={'schema':'k1-frontend-mutations/1','tests':{f:hashlib.sha256((ROOT/'tests'/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for f in FILES},'baseline':'passed','results':rows}
  args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  return 0 if all(r['status']=='killed' for r in rows) else 1

if __name__=='__main__':raise SystemExit(main())
