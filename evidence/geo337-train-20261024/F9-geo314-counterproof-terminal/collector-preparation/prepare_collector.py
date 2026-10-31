from pathlib import Path
import ast, hashlib, json, os, stat

P = Path('/workspace/geo314-counterproof-terminal-preparation-20261025')
BASE = Path('/workspace/geo337-remaining-browser-terminal-preparation-20261025/collect_four_browser_terminal_v3.py')
H = lambda b: hashlib.sha256(b).hexdigest()
original = BASE.read_text()
assert H(original.encode()) == '813a770b414c6b57f4ffde568e6242614ed3bf28287a3e487ed9811f1113d741'
head = original[:original.index('def main():')].replace('"""Preserve four named terminated F9 jobs; root-approved SHM execution only."""', '"""Collect closed #314 v2 failure and v3 focused proof; no current NATIVE access."""')
head = head.replace("OWN = Path('/dev/shm/geo337-F9-browsers-20261025')\n", '')
head = head.replace("JOBS = {'documents': ('d', 10), 'grid': ('g', 15), 'space': ('s', 15), 'timber': ('t', 20)}", "PREP = Path('/workspace/geo314-counterproof-terminal-preparation-20261025')\nCONFIG = PREP/'SCOPE.json'\nCONFIG_PIN = 'SCOPE_PIN'")
head = head.replace('4 * 2 * 1024**2  # Four job inventories, retaining the original per-job metadata allowance.', '8 * 1024**2  # Preserve the accepted collector metadata allowance.')

dirs = [
 ('preparation/v2', '/workspace/geo314-F9-counterproof-shm-placement-20261025'),
 ('preparation/v3', '/workspace/geo314-F9-counterproof-all-private-index-preparation-20261025'),
 ('preparation/original-counterproof', '/workspace/geo314-F9-kernel-scope-counterproof-preparation-20261025'),
 ('preparation/index-diagnostic', '/workspace/geo314-real-index-refresh-diagnostic-20261025'),
 ('preparation/kernel-scope', '/tmp/geo314-F9-kernel-scope-rootcause-20261025'),
 ('peers/v2-original-static', '/workspace/geo314-F9-counterproof-v2-final-static-peer-n37dc_7n'),
 ('peers/v2-placement-static', '/workspace/geo314-counterproof-shm-static-peer-20261025'),
 ('peers/v3-static', '/workspace/geo314-all-private-index-v3-static-peer-edr2n3g4'),
 ('peers/v3-actual', '/workspace/geo314-v3-independent-actual-peer-13jjxihs'),
 ('author-v3-summary', '/workspace/geo314-v3-author-actual-summary-20261025'),
]
extras = {
 'tools/capture.py': '/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py',
 'tools/clear_terminal_chrome_caches.py': '/workspace/clear_terminal_chrome_caches.py',
 'tools/reap_children.py': '/workspace/geo261-environment/reap_children.py',
}
rows=[]
for prefix,root in dirs:
 for parent,ds,fs in os.walk(root,followlinks=False):
  for name in sorted(ds+fs):
   p=Path(parent)/name;s=p.lstat()
   if stat.S_ISDIR(s.st_mode):continue
   assert stat.S_ISREG(s.st_mode), str(p)
   rows.append(dict(member=prefix+'/'+p.relative_to(root).as_posix(),path=str(p),bytes=s.st_size,sha256=H(p.read_bytes())))
for member,path in extras.items():
 p=Path(path);rows.append(dict(member=member,path=path,bytes=p.stat().st_size,sha256=H(p.read_bytes())))
attempts={
 'v2':dict(root='/dev/shm/geometry-axiom-geo337-20261025/geo314-counterproof-v2-20261025',request='/dev/shm/geometry-axiom-geo337-20261025/geo314-counterproof-root-request-20261025.json',request_sha256='782d960080e2e8853d8cd6beb305b93da7a38a992f29a2cd4de56cd6833731e6',final='/workspace/geo314-F9-shm-counterproof-EXEC_FINAL-20261025.json',exit_code=1,regular_files=204,regular_bytes=13578903,result_sha256='92917bb2e49003e9ef65353fc94bb20a6225c87037a769632dd4df72ed8d9b04',executor='/workspace/geo314-F9-counterproof-shm-placement-20261025/run_counterproof_v2_shm.py',executor_sha256='bd471131af1f620964ec4f54a386b48b5127473f783c3292e256bfe3ba6f423d'),
 'v3':dict(root='/dev/shm/geometry-axiom-geo337-20261025/geo314-counterproof-v3-20261025',request='/dev/shm/geometry-axiom-geo337-20261025/geo314-counterproof-v3-root-request-20261025.json',request_sha256='f3239211d8d9b60fe536bf4a00c6481cf7a5bdeccaa3422f8de96fdf773ce527',final='/workspace/geo314-F9-all-private-counterproof-EXEC_FINAL-20261025.json',exit_code=0,regular_files=258,regular_bytes=20191163,result_sha256='a9b355c1e4836c684390a160568684ec6c7c075badf2729d92f3b27416dca83a',executor='/workspace/geo314-F9-counterproof-all-private-index-preparation-20261025/run_counterproof_v3.py',executor_sha256='74651aa907fc3f280592ac7a1f63f8d9d912f1adaa31ffc2ffe8c428d6fee568'),
}
for a in attempts.values():a['final_sha256']=H(Path(a['final']).read_bytes())
config=dict(source_sha='4f8a794f4167c3562eb182045102e86e9e37cca9',attempts=attempts,extra_files=rows,selection='All leaves in both closed original run roots, no private Git object/index/stdout/stderr exclusion; fixed preparation and peer leaves.',live_NATIVE_access=False)
(P/'SCOPE.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
head=head.replace('SCOPE_PIN',H((P/'SCOPE.json').read_bytes()))
main='''def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path);ap.add_argument('--request-sha256');ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:
  print(json.dumps(dict(state='PREPARATION_ONLY',source_sha=F,attempts=['v2','v3'],product_rerun=False,live_NATIVE_access=False)));return 0
 need(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'),'nonoptimized execution')
 need(a.request is not None and digest(safe(a.request))==a.request_sha256,'root request exact pin');q=J(a.request);pin=digest(__file__)
 need(q.get('source_sha')==F and q.get('root_execution_lease') is True and q.get('all_attempts_closed_no_more_writes') is True,'closed raw scope lease')
 need(q.get('collector_sha256')==pin,'collector identity');pp=safe(q['independent_peer']['path']);need(digest(pp)==q['independent_peer']['sha256'],'peer pin');peer=J(pp)
 need(type(peer.get('exit_code')) is int and peer['exit_code']==0 and peer.get('collector_sha256')==pin,'accepted exact collector')
 need(digest(safe(CONFIG))==CONFIG_PIN and digest(safe(CAP))==CAP_PIN,'fixed scope and original recorder');config=J(CONFIG)
 safe(SHM);need(digest(SHM/'STORAGE_POLICY.json')==POLICY,'original approved storage policy')
 out=safe(q['out']);need(out==SHM/'geo314-counterproof-terminal-package-20261025' and not out.exists(),'fresh exact own output')
 out.mkdir(mode=0o700);(out/'BOUND_REQUEST.json').write_bytes(a.request.read_bytes());(out/'COLLECTOR.py.txt').write_bytes(Path(__file__).read_bytes());(out/'SCOPE.json').write_bytes(CONFIG.read_bytes())
 result=dict(schema='geo314-v2-v3-complete-terminal-package/1',source_sha=F,collection_exit=None,started_epoch=time.time(),collector_sha256=pin,attempts=[],parts=[],errors=[],subject_rerun=False,live_NATIVE_access=False,formal_F9_native_original_exit=1,delivered=False,product_acceptance_rejudged=False)
 write(out/'RESULT.json',result)
 try:
  roots=[];extras={};expected_counts={}
  need(set(q['terminal_inputs'])==set(config['attempts'])=={'v2','v3'},'both terminal identities')
  for name,c in config['attempts'].items():
   root=safe(c['root']);finalpath=safe(c['final']);reqpath=safe(c['request']);executor=safe(c['executor'])
   need(digest(finalpath)==c['final_sha256']==q['terminal_inputs'][name]['final_sha256'],'host terminal identity')
   need(digest(root/'RESULT.json')==c['result_sha256'] and digest(reqpath)==c['request_sha256'] and digest(executor)==c['executor_sha256'],'original result/request/tool pins')
   final=J(finalpath);host=final['actual_tool_result'];summary=json.loads(host['output']);original=J(root/'RESULT.json');rq=J(reqpath)
   need(final['source_sha']==original['source_sha']==rq['source_sha']==F and final['executor_sha256']==rq['tool_sha256']==c['executor_sha256'] and final['request_sha256']==original['request_sha256']==c['request_sha256'],'original source/tool/request identity chain')
   need(rq['out']==str(root),'original own raw path')
   for value in [host['exit_code'],summary['exit_code'],original['exit_code']]:need(type(value) is int and value==c['exit_code'],'original v2 red/v3 zero preserved')
   need(summary['formal_F9_pass'] is False and original['formal_F9_pass'] is False and summary['counterproof_passed'] is True and original['counterproof_passed'] is True,'focused proof not whole native')
   need(original.get('ended_utc') and summary['restoration_errors']==original['restoration_errors'],'closed original restoration outcome')
   if name=='v2':need(len(original['restoration_errors'])==1 and 'original ROOT index bytes/inode/metadata untouched' in original['restoration_errors'][0] and (root/'INDEX_AFTER_FAILURE.bin').is_file(),'original index failure retained')
   else:need(original['restoration_errors']==[] and original['before']==original['after'] and original['shared_index_unchanged'] is True and (root/'ORIGINAL_INDEX.bin').is_file(),'v3 original restored identity')
   roots.append(('attempts/'+name,root,False));expected_counts['attempts/'+name]=(c['regular_files'],c['regular_bytes'])
   extras['attempts/'+name+'/original-host-final.json']=finalpath;extras['attempts/'+name+'/original-root-request.json']=reqpath
   result['attempts'].append(dict(name=name,source_sha=F,original_exit=c['exit_code'],counterproof_passed=True,formal_F9_pass=False,result_sha256=c['result_sha256'],host_sha256=c['final_sha256'],restoration_errors=original['restoration_errors']))
  for row in config['extra_files']:
   p=safe(row['path']);need(p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'pinned preparation/peer/tool original');need(row['member'] not in extras,'extra member collision');extras[row['member']]=p
  extras['collection-tool/collector.py']=Path(__file__);extras['collection-tool/SCOPE.json']=CONFIG;extras['collection-static-peer/REVIEW.json']=pp
'''
inventory=original[original.index('  rows = []; excluded'):original.index('  groups = []')]
inventory=inventory.replace("  inv = dict(schema='geo337-F9-four-browser-complete-terminal-inventory/1'", "  for prefix,(count,nbytes) in expected_counts.items():\n   selected=[r for r in rows if r['member'].startswith(prefix+'/') and r['member'] not in extras]\n   need(len(selected)==count and all(r['type']=='regular' for r in selected) and sum(r['bytes'] for r in selected)==nbytes,'complete closed raw root inventory: '+prefix)\n  need(not excluded and not specials,'no raw exclusion or nonregular omission')\n  inv = dict(schema='geo314-complete-counterproof-terminal-inventory/1'")
inventory=inventory.replace("selection='All regular bytes and symlink targets of four isolated launch/storage/sampler roots, original preparation/closed guards/tools; no ELF/cache/profile/diagnostic exclusions.', no_seed_source_payload_copied=True, no_git_object_payload_copied=True", "selection=config['selection'], live_NATIVE_access=False, private_git_objects_and_indexes_included=True")
tail=original[original.index('  groups = []'):].replace('ORIGINAL_FOUR_BROWSER_PART','ORIGINAL_GEO314_COUNTERPROOF_PART').replace('actual metadata within four original2MiB allowances','actual metadata within original8MiB allowance')
source=head+main+inventory+tail
ast.parse(source);(P/'collect_counterproof_terminal.py').write_text(source)
terms={k:dict(final_sha256=v['final_sha256']) for k,v in attempts.items()};(P/'TERMINAL_PINS.json').write_text(json.dumps(terms,indent=2)+'\n')
launcher=Path('/workspace/geo337-remaining-browser-terminal-preparation-20261025/launch_four_job_collection_v3.py').read_text()
launcher=launcher.replace('four true terminal pins','two true counterproof terminal pins').replace('all four true terminal pins','both true terminal pins')
launcher=launcher.replace("/workspace/geo337-remaining-browser-terminal-preparation-20261025/collect_four_browser_terminal_v3.py",str(P/'collect_counterproof_terminal.py')).replace('813a770b414c6b57f4ffde568e6242614ed3bf28287a3e487ed9811f1113d741',H(source.encode()))
launcher=launcher.replace("JOBS=('documents','grid','space','timber')", "JOBS=('v2','v3')\nFINALS="+repr({k:v['final'] for k,v in attempts.items()}))
start=launcher.index(' for job in JOBS:');end=launcher.index(" need(physical(ROOT).is_dir()",start)
launcher=launcher[:start]+" for job in JOBS:\n  need(set(terminals[job])=={'final_sha256'},'exact host terminal pin')\n  need(sha(physical(FINALS[job]))==terminals[job]['final_sha256'],'true host terminal exact hash')\n"+launcher[end:]
launcher=launcher.replace('remaining-browser-terminal-collection-original-20261025','geo314-counterproof-terminal-collection-original-20261025').replace('remaining-browser-terminal-package-20261025','geo314-counterproof-terminal-package-20261025').replace('all_four_jobs_closed_no_more_guard_writes','all_attempts_closed_no_more_writes').replace('collect four named closed F9 browser jobs without product rerun','collect closed F9 temporary-patch v2 failure and v3 proof without product rerun or live NATIVE read')
ast.parse(launcher);(P/'launch_collection.py').write_text(launcher)
print(json.dumps(dict(collector_sha256=H(source.encode()),launcher_sha256=H(launcher.encode()),scope_sha256=H((P/'SCOPE.json').read_bytes()),terminal_pins_sha256=H((P/'TERMINAL_PINS.json').read_bytes()),extra_files=len(rows),extra_bytes=sum(r['bytes'] for r in rows))))
