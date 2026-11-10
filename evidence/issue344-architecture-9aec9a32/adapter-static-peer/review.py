from pathlib import Path
import ast,hashlib,json,difflib,datetime,subprocess
P=Path('/workspace/geo344-architecture-adapter-preparation-20261025');O=Path(__file__).parent;OLD=Path('/tmp/geo344-exclusion-digest-preparation-20261025');C=[]
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def ck(n,b):C.append({'name':n,'ok':bool(b)})
prep=J(P/'PREPARATION.json');dry=J(P/'DRY_PLAN_RESULT.json');pins=J(P/'PINS.json');src=(P/'refresh_architecture_cdp_exclusion.py').read_text();tree=ast.parse(src)
ck('pinnedsubject',h((P/'PINS.json').read_bytes())=='200c249e2107d87eb69fd7b773ac94fe1e2e3731c6b033e1dccf68c2acb202c2' and h(src.encode())=='71cb2e314a3d3e7c3419bbe436f2c308a702d6b3be5f9668594fe729248de2de')
for r in pins['files']:
 b=(P/r['path']).read_bytes();ck('pin:'+r['path'],len(b)==r['bytes'] and h(b)==r['sha256'])
ck('old_driver_original',h((P/'original_driver.py.txt').read_bytes())=='5b76f54d810a736e1008450eb2822f8c0d5a427cbd3e7d3138a578909203a7fb' and (P/'original_driver.py.txt').read_bytes()==(OLD/'original-refresh_architecture_k_source_delta.py').read_bytes())
ck('unrun_boundary',all(prep[k] is False for k in ['formal_judges_executed','single_hash_EXCLUSION_DIGEST_proof_executed','historical_nine_policy_guards_executed','strict_node9_rerun','C_or_Chrome_executed','checkout_or_branch_written_by_preparer','large_checkout_materialized','outputs_report_receipt_generated']))
cmds=J(P/'dry-plan-original-capture/subcommands.json');ck('dry_original_three_exits',[r['actual_process_returncode'] for r in cmds]==[0,1,0] and dry['actual_exits']==[0,1,0])
for i,r in enumerate(cmds):
 ck('dry'+str(i)+':terminal',not r['timeout_expired'] and r['ended_epoch']>=r['started_epoch'])
 for n in ['stdout','stderr']:
  b=(Path(r['directory'])/(n+'.bin')).read_bytes();ck('dry'+str(i)+':'+n,len(b)==r[n+'_bytes'] and h(b)==r[n+'_sha256'])
 ck('dry'+str(i)+':stdin',h((Path(r['directory'])/'stdin.bin').read_bytes())==r['stdin_sha256']);ck('dry'+str(i)+':result',J(Path(r['directory'])/'result.json')==r)
first=(Path(cmds[0]['directory'])/'stdout.bin').read_bytes();last=(Path(cmds[2]['directory'])/'stdout.bin').read_bytes();err=(Path(cmds[1]['directory'])/'stderr.bin').read_text();ck('dry_true_plan_not_formal',first==last==(P/'DRY_PLAN.json').read_bytes() and json.loads(first)['execution']=='UNRUN' and 'RuntimeError: Python optimization forbidden' in err and '-O' in cmds[1]['command'])
# Pure static pin/byte derivation; no adapter entry, judge, mutation or fixture creation.
constants={}
for node in tree.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
  try:constants[node.targets[0].id]=ast.literal_eval(node.value)
  except (ValueError,TypeError):pass
old=(OLD/'original-product-architecture.json').read_bytes();fixed=(OLD/'product-architecture.fixed.json').read_bytes();ck('single_hash_fixed_exact',old.count(constants['OLD_DIGEST'].encode())==1 and old.replace(constants['OLD_DIGEST'].encode(),constants['NEW_DIGEST'].encode())==fixed and h(old)==constants['PREVIOUS_PIN'] and h(fixed)==constants['CURRENT_PIN'])
# Read the already-known historical Git blob without mutation or copying its payload.
argv=['git','-C','/workspace/geometry-axiom','show','ca7838e0f4950452b9befcf40899d606db9b81fa:geometry-core/domain-decoupling/product-architecture.json'];q=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);history=q.stdout;derived=history.replace(constants['OLD_DIGEST'].encode(),constants['NEW_DIGEST'].encode());ck('historical_original_exact',q.returncode==0 and h(history)==constants['HISTORICAL_PIN'] and history.count(constants['OLD_DIGEST'].encode())==1);ck('derived_control_exact',h(derived)==constants['DERIVED_HISTORY_PIN'])
cur=json.loads(fixed);pr=json.loads(old);hi=json.loads(history);de=json.loads(derived);ck('policies_937_928_55',len(cur['policy']['forbiddenIdentifiers'])==937 and len(hi['policy']['forbiddenIdentifiers'])==928 and len(cur['policy']['forbiddenStrings'])==len(hi['policy']['forbiddenStrings'])==55 and cur['policy']==pr['policy'])
ck('nine_exact_guard_identifiers',set(cur['policy']['forbiddenIdentifiers'])-set(hi['policy']['forbiddenIdentifiers'])==constants['ADDED'] and len(constants['ADDED'])==9)
c=json.loads(fixed);c['policy']['forbiddenIdentifiers']=de['policy']['forbiddenIdentifiers'];ck('derived_only_nine_policy_difference',c==de)
texts=["if not a.execute:","raise SystemExit(0)","assert not sys.flags.optimize and a.root_scheduled_architecture_run","assert resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216","git('merge-base','--is-ancestor',ANCESTOR,F)","git('diff','--name-only',ANCESTOR,F,'--','.',':(exclude)evidence/**')","assert sorted(tree)==declared","assert sorted(prior_tree)==declared","assert [n for n in declared if tree[n]!=prior_tree[n]]==EXPECTED_CHANGED_INPUTS","assert closure==EXPECTED_CLOSURE","assert snapshot()==before","assert all((R/ART/n).read_bytes()==old_four[n] for n in NAMES)","assert Path(__file__).read_bytes()==driver_before and H(CAP.read_bytes())==CAP_PIN","manifestSourceGitSHA':None if phase=='withdrawn' else F","'controlIsDerived':True","assert digest_outputs[0]==digest_outputs[2]"]
for t in texts:ck('guard:'+t,t in src)
ck('dry_exit_before_capture_and_mkdir',src.index('if not a.execute:')<src.index("CAP=Path(")<src.index('O.mkdir()'))
ck('formal_three_argv_original',"for argv in [['python3','-B',JUDGES[0],'--root','.','--manifest',ART+'/'+NAMES[0]],['python3','-B',JUDGES[1]],['python3','-B',JUDGES[2]]]" in src)
ck('formal_counts_no_skip_relaxation',"zip(results[1:],[205,18])" in src and "text.rstrip().endswith('OK')" in src and "len(scan['edges'])==798" in src and "len(scan['sources'])==334" in src and "len(scan['trustedSourcesNotParsed'])==6" in src)
ck('single_digest_exact0_1_0',"expected=1 if phase=='withdrawn' else 0" in src and "row['timeout_expired'] is False and not err" in src and "assert parsed=={'ok':False,'sources':[],'trustedSourcesNotParsed':[],'edges':[],'diagnostics':[expected_digest_diagnostic]}" in src and "else:assert out==results[0][1]" in src)
ck('W_and_neutral_not_dropped',"for name in sorted(ADDED):" in src and "'geo261_architecture_neutral_probe','neutral'" in src and "manifestIsDerived':phase=='withdrawn'" in src)
ck('outputs_after_all_proofs_and_unchanged',src.index("new=O/'new';")>src.index("for path in [withdrawn,R/ART/NAMES[0]]") and src.index("new=O/'new';")>src.index('assert snapshot()==before'))
# Existing tiny Git fixture: pathspec filtering retains original deleted leaf; no new fixture or writes.
fixture=J('/tmp/geo337-F9-no-rename-metadata-proof-20261025/RESULT.json');gitrows=[];outs=[]
for flags in [[],['--no-renames']]:
 a=['git','-C',fixture['fixture_only'],'diff',*flags,'--name-only',fixture['fixture_base'],fixture['fixture_tip'],'--','.',':(exclude)evidence/**'];z=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE);gitrows.append({'argv':a,'exit_code':z.returncode,'stdout':z.stdout.decode(),'stderr':z.stderr.decode()});outs.append(z.stdout);ck('pathspec_git'+str(len(gitrows)),z.returncode==0 and b'geometry-core/kernel/source.c\n' in z.stdout)
ck('pathspec_does_not_hide_known_rename',outs[0]==outs[1])
fail=[c for c in C if not c['ok']]
r={'schema':'geo344-exact-architecture-adapter-static-peer/1','exit_code':int(bool(fail)),'checks':len(C),'failed_checks':fail,'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject_pins_sha256':h((P/'PINS.json').read_bytes()),'adapter_sha256':h(src.encode()),'source_ancestor':'a5ec136baf3909453867b3eed50f1b93b229ca59','source_S344':'UNBOUND','formal_executed':False,'digest_proof_executed':False,'policy_guards_executed':False,'accepted_scope':'STATIC_ADAPTER_PREPARATION_ONLY','recorded_metadata_entry_exits':[0,1,0],'launch_conditions':['root先固定同a5後裔且僅單manifest hash+evidence變更的可解析S344；本審不表示分支已建立/推送。','提供全部604inputs／三原judge／SSOT的乾淨同源checkout與fresh外部out，root另做磁碟/CPU排程及原c387外層完整收件。','原stack16MiB、原三judge205/18零skip、單hash精確0/1/0與九W/neutral均真跑後才收四檔成功；任一紅不能放寬期待。','本稿不能直接用於先合新列車而多產品差的來源；若來源closure不同需另審新精確適配。'],'limits':['原metadata default/-O/default0/1/0只驗入口，不是產品撤回自證。','未執adapter、C、Chrome、architecture judge、Node strict9或新fixture；唯讀原Git歷史blob及既有tinyfixture metadata。','第98行有Git pathspec排除；既有rename fixture實讀證明此例仍列原刪除葉，不能套用無pathspec版舊漏洞，未要求無效修補。','原歷史928raw與cdp同步衍生本分開，未將衍生控制冒成歷史Git blob。'],'historical_git_read':{'argv':argv,'exit_code':q.returncode,'stdout_bytes':len(q.stdout),'stdout_sha256':h(q.stdout),'stderr':q.stderr.decode(),'payload_storage':'immutable Git object retained; no duplicate payload written'},'readonly_existing_fixture_checks':gitrows,'checks_detail':C}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');(O/'REVIEW.md').write_text(f'# #344 架構 adapter 靜態獨審\n\n{len(C)}項／{len(fail)}錯，exit={int(bool(fail))}。只接受待排程工具：exact a5後裔、單cdp hash、604/602與兩變動、937/55、原三judge205/18、單hash0/1/0、九W／neutral與四檔來源綁定均保。\n\n正式架構／產品反證均未跑；metadata0/1/0不移標。需root提供同源完整checkout／新S344／fresh空間與完整外層收件，才可安排正式執行。舊歷史928與衍生control身份分列。\n\n以既有tiny Git fixture唯讀比對，source diff含pathspec時仍列原刪除葉，無需套用先前無pathspec版的修補。沒有新repo、source或branch寫入。\n')
print(json.dumps({'exit_code':r['exit_code'],'checks':len(C),'failures':fail,'review_sha256':h((O/'REVIEW.json').read_bytes())},ensure_ascii=False));raise SystemExit(bool(fail))
