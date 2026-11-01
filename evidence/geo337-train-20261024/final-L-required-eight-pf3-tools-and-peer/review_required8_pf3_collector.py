import ast,difflib,hashlib,json
from pathlib import Path
B=Path('/workspace/train337-final-required8-pf3-collection');O=Path('/workspace/train337-canvas-peer-resume');checks=0;findings=[]
def ck(v,l):
 global checks
 checks+=1
 if not v:findings.append(l)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((B/'PREPARATION.json').read_text());old=Path(p['original']);new=Path(p['collector']);before=old.read_text();src=new.read_text();ast.parse(src)
ck(h(old)==p['original_sha256']=='b2a148d1851ce50f96b48c0b5110e464be2bed395a8bc4030aeaff78061e44b2','exact original section7 collector')
ck(h(new)==p['collector_sha256']=='ce93f88fa5bd8f409977adf7731dcbd418f286afe64838ec3e2d5cad80acfeb4','exact new collector')
ck(h(B/'COLLECTOR_DIFF.patch')==p['patch_sha256']=='f1c6a031832cd37c8b97111ab286d0af2daa4aaaccb0467b94697f405ffbd105','exact full adaptation diff')
ck((B/'COLLECTOR_DIFF.patch').read_text()==''.join(difflib.unified_diff(before.splitlines(True),src.splitlines(True),fromfile=str(old),tofile=str(new))),'full diff matches original/new bytes')
prefix_old=before.split("summary={'schema':",1)[0].replace('section7 evidence','required-eight/PF3 evidence').replace("choices=['cardref','axiom']","choices=['required-eight','pf3']")
ck(src.split("summary={'schema':",1)[0]==prefix_old,'all original terminal/source guards/exclusion/full-directory capture unchanged')
suffix=before.split("for name,value in [('EXCLUDED_ELF_PAYLOADS.json',excluded),('SUMMARY.json',summary)]:",1)[1].replace('ORIGINAL_SECTION7_LOGS_REPORTS_AND_ELF_HASHES','ORIGINAL_NONPERF_LOGS_REPORTS_AND_ELF_HASHES')
ck(src.split("for name,value in [('EXCLUDED_ELF_PAYLOADS.json',excluded),('SUMMARY.json',summary)]:",1)[1]==suffix,'all original unique archive/actual-byte roundtrip unchanged')
ck("stage['source_sha']==L" in src and "stage['stages'][a.gate]['ended_utc']" in src and "stage['stages'][a.gate]['execution_exit']==0 and stage['wrapper_exit']==0" in src,'nested stage and wrapper actual terminal0 required')
ck("hfile(stage_receipt)==r['gates'][0]['original_stage_receipt_sha256']" in src,'original inner stage hash bound by outer receipt')
ck("glob('*/commands/commands.json')" in src and "json.loads((q/'result.json').read_text())==row" in src and "row[kind+'_sha256']" in src,'actual nested v4 schema and all exposed stdout/stderr hashes')
ck("'all_executed_stage_commands_passed','full_acceptance_passed'" in src,'retain original all-stage/full-acceptance flags without promotion')
ck("need(set(names)==set(expected) and len(names)==8" in src and "need(len(found)==1" in src and "count==passed==e['count'] and failed==skipped==0" in src and "==676" in src,'exact eight argv and unique original rows/counts676')
ck('can retain previous unselected logs' in src and 'not676 unittest methods' in src,'historical copied global logs and heterogeneous units explicit')
ck("dict(run=20,failures=0,errors=0,skipped=0)" in src and "len(mutants)==19 and len({x['id'] for x in mutants})==19" in src and "dict(run=1,failures=1,errors=0,skipped=0)" in src,'original PF3 baseline20/distinct19one-method assertion red/restored20 counts')
ck('unlink(' not in src and 'rmtree(' not in src and 'subprocess' not in src,'no subject invocation or deletion')
ck("'before-source.json'" in src and "b==e and b['head']==L and b['status']==''" in src,'closed original source snapshot only; no active ROOT access')
report={'schema':'final-L-required-eight-PF3-terminal-collector-static-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'collector_sha256':h(new),'original_sha256':h(old),'limits':['Static collector review only. No actual required-eight/PF3 acceptance or archive is inferred.','Collector explicitly requires nested terminal0 and full expected success counts. A red/incomplete run would be rejected; original directories remain untouched and must be separately preserved if that occurs.','Nested original v4 receipt and commands/commands.json are retained; actual peer must independently inspect raw exact assertions, not rely solely on summary.','Copied global suite log directory may contain historical unselected outputs; only exact eight original CLI selection and its current stdout count as this run.']};out=O/'REQUIRED8_PF3_COLLECTOR_STATIC_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'path':str(out),'sha256':h(out)},ensure_ascii=False));raise SystemExit(report['exit_code'])
