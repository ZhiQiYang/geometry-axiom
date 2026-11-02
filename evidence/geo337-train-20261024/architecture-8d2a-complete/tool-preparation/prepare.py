from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).parent
P=Path('/workspace/refresh_geo337_final_architecture_20261024.py')
b=P.read_bytes();assert hashlib.sha256(b).hexdigest()=='61aa806e619baa5f0b141d2a5026fe8146691e12406b112cb4b7f765e9db37b0'
s=b.decode();(D/'original.py.txt').write_bytes(b)
def replace(old,new):
 global s
 assert s.count(old)==1,(old[:100],s.count(old));s=s.replace(old,new)
replace('The only permitted manifest policy delta is the nine measured Reading A guards.','The permitted current manifest delta is zero; nine guards use a pinned historical manifest.')
replace("p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();R=a.root.resolve();O=a.out.resolve();F=a.sha", "p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior-source',required=True);p.add_argument('--guard-baseline-source',default='ca7838e0f4950452b9befcf40899d606db9b81fa');a=p.parse_args();R=a.root.resolve();O=a.out.resolve();F=a.sha\nassert re.fullmatch('[0-9a-f]{40}',a.prior_source) and re.fullmatch('[0-9a-f]{40}',a.guard_baseline_source)")
replace("def LF(b):return b.replace(b'\\r\\n',b'\\n')", """def LF(b):return b.replace(b'\\r\\n',b'\\n')
HISTORICAL_PIN='80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525'
CURRENT_PIN='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
PROBE_PIN='350fc09a16660d33144fe7b7a8198032e8251e37a67a61179ec96eba39e1e739'
EXPECTED_CHANGED_INPUT='geometry-templates/woodworking/native/contact_world.c'
def validate_manifests(current_raw,previous_raw,historical_raw):
 assert current_raw==previous_raw and H(LF(current_raw))==CURRENT_PIN
 assert H(historical_raw)==HISTORICAL_PIN
 current,previous,historical=map(json.loads,[current_raw,previous_raw,historical_raw])
 assert current==previous
 assert len(current['policy']['forbiddenIdentifiers'])==937 and len(current['policy']['forbiddenStrings'])==55
 assert len(historical['policy']['forbiddenIdentifiers'])==928 and len(historical['policy']['forbiddenStrings'])==55
 assert set(current['policy']['forbiddenIdentifiers'])-set(historical['policy']['forbiddenIdentifiers'])==ADDED
 assert set(historical['policy']['forbiddenIdentifiers'])<=set(current['policy']['forbiddenIdentifiers'])
 check=copy.deepcopy(current);check['policy']['forbiddenIdentifiers']=historical['policy']['forbiddenIdentifiers'];assert check==historical
 return historical""")
replace("old_commit=git('log'", "assert prior['sourceBaseHead']==a.prior_source\nold_commit=git('log'")
old="""assert set(manifest['policy']['forbiddenIdentifiers'])-set(previous_manifest['policy']['forbiddenIdentifiers'])==ADDED
check=copy.deepcopy(manifest);check['policy']['forbiddenIdentifiers']=previous_manifest['policy']['forbiddenIdentifiers'];assert check==previous_manifest
assert set(previous_manifest['policy']['forbiddenIdentifiers'])<=set(manifest['policy']['forbiddenIdentifiers']) and len(manifest['policy']['forbiddenIdentifiers'])==937 and len(manifest['policy']['forbiddenStrings'])==55"""
new="""assert git('rev-parse',a.guard_baseline_source+'^{commit}').decode().strip()==a.guard_baseline_source
git('merge-base','--is-ancestor',a.guard_baseline_source,F)
historical_row,historical_raw,_=run(['git','show',a.guard_baseline_source+':'+ART+'/'+NAMES[0]],variant='Read pinned historical 928-identifier manifest; not the previous 937-identifier artifact')
historical_manifest=validate_manifests(old_four[NAMES[0]],previous_manifest_raw,historical_raw)
(O/'historical-928-manifest.json').write_bytes(historical_raw)
historical_binding={'sourceGitSHA':a.guard_baseline_source,'manifestRawSha256':HISTORICAL_PIN,'manifestLfSha256':H(LF(historical_raw)),'identifiers':928,'strings':55,'readCommand':historical_row,'usedAsPreviousManifest':False}
cap.dump(O/'historical-guard-baseline.json',historical_binding)"""
replace(old,new)
replace("before=snapshot();inputs=[{'path':x['path'],'sha256':x['lfSha256']} for x in before];closure=", "before=snapshot();inputs=[{'path':x['path'],'sha256':x['lfSha256']} for x in before];old_inputs={x['path']:x['sha256'] for x in prior['inputs']};assert set(old_inputs)==set(declared);changed=[x for x in inputs if old_inputs[x['path']]!=x['sha256']];assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT];closure=")
replace("assert words<=set(manifest['policy']['forbiddenIdentifiers']);assert words-set(previous_manifest['policy']['forbiddenIdentifiers'])==ADDED", "assert words<=set(manifest['policy']['forbiddenIdentifiers']);assert not words-set(previous_manifest['policy']['forbiddenIdentifiers']);assert words-set(historical_manifest['policy']['forbiddenIdentifiers'])==ADDED")
replace("cap.dump(O/'policy-guard-inventory.json',{'addedIdentifiers':[{'identifier':n,'origins':origins[n]} for n in sorted(ADDED)],'removedIdentifiers':[],'oldCount':928,'newCount':937,'stringCount':55,'allOtherManifestFieldsEqual':True})", "cap.dump(O/'policy-guard-inventory.json',{'addedIdentifiers':[],'removedIdentifiers':[],'oldCount':937,'newCount':937,'stringCount':55,'allOtherManifestFieldsEqual':True,'historicalGuardIdentifiers':[{'identifier':n,'origins':origins[n]} for n in sorted(ADDED)],'historicalGuardBaseline':historical_binding})")
replace("# Same-source, normal assertion proof of the exact nine strengthened guards.\nprobe=Path('/workspace/geo337-U-architecture-policy-proof-20261024/probe.py').read_text();(O/'tools'/'policy_probe.py').write_text(probe);withdrawn=O/'withdrawn-manifest.json';withdrawn.write_bytes(previous_manifest_raw);proof=[]", "# Fresh same-source assertions against the historical 928 baseline, not previous artifact.\nprobe_raw=Path('/workspace/geo337-U-architecture-policy-proof-20261024/probe.py').read_bytes();assert H(probe_raw)==PROBE_PIN;probe=probe_raw.decode();(O/'tools'/'policy_probe.py').write_bytes(probe_raw);withdrawn=O/'withdrawn-manifest.json';withdrawn.write_bytes(historical_raw);proof=[]")
replace("variant='same-source exact W guard '+phase", "variant='same-source W guard '+phase+'; withdrawn baseline Git '+a.guard_baseline_source+' raw sha256 '+HISTORICAL_PIN")
replace("proof.append({'identifier':name,'phase':phase,'exit':expected,'directory':row['directory']})", "proof.append({'identifier':name,'phase':phase,'exit':expected,'directory':row['directory'],'executionSourceSHA':F,'manifestSourceGitSHA':a.guard_baseline_source if phase=='withdrawn' else F,'manifestRawSha256':HISTORICAL_PIN if phase=='withdrawn' else H(old_four[NAMES[0]])})")
replace("old_inputs={x['path']:x['sha256'] for x in prior['inputs']};assert set(old_inputs)==set(declared);changed=[x for x in inputs if old_inputs[x['path']]!=x['sha256']]\ncounts=", "assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT]\ncounts=")
replace("原完整 W lexer 盤點補9個已存在的 Reading A identifiers：forbiddenIdentifiers 928→937，forbiddenStrings維持55；舊guard全留，其餘manifest分類、路徑、exclusion、trust及政策全部相同。九組原scanner guard assertion在同一來源各0／1／0，兩個neutral probe通過；沒有用舊來源結果移標。", "本輪 manifest 與前份產物逐 bytes 相同：forbiddenIdentifiers 937→937、forbiddenStrings 55；分類、路徑、exclusion、trust及所有政策不變。完整604輸入相較前份收據僅 `{EXPECTED_CHANGED_INPUT}` 的來源雜湊改變。原完整 W lexer 盤點仍覆蓋全部 W identifiers。九組既有 guard 在本次來源重新實跑0／1／0；撤回用歷史928版 Git `{a.guard_baseline_source}`、原SHA256 `{HISTORICAL_PIN}`，明確不同於上一份937版 manifest。兩個neutral probe亦重新通過，沒有移標歷史判決。")
replace("basis='Original Linux receipt schema, full Git/blob inventory and original judges; nine additive W guards only.'", "basis='Original Linux receipt schema and original judges; unchanged 937-identifier manifest, full 604-source inventory, and fresh assertions against pinned historical 928 baseline.'")
replace("'allPolicyFieldsEqualToPrevious':False,'onlyPolicyDelta':{'addedIdentifiers':sorted(ADDED)", "'allPolicyFieldsEqualToPrevious':True,'onlyPolicyDelta':{'addedIdentifiers':[]")
replace("'note':'No inherited proof relabeled. Nine controls execute at this source; original policy is withdrawn outside source.'", "'historicalGuardBaseline':historical_binding,'note':'No inherited proof relabeled. Current/previous manifests are byte-identical (937). Nine controls execute freshly at this source against the separately pinned historical 928 manifest outside source.'")
replace("'newIdentifiers':9,'fixedWithdrawnRestored'", "'newIdentifiers':0,'guardIdentifiersRetested':9,'historicalBaselineSource':a.guard_baseline_source,'historicalBaselineRawSha256':HISTORICAL_PIN,'fixedWithdrawnRestored'")
replace("'newGuardProofExits':[0,1,0],'newGuardCases':9", "'newGuardProofExits':[0,1,0],'newGuardCases':0,'existingGuardCasesRetested':9,'historicalGuardBaseline':historical_binding,'manifestDelta':'unchanged-937-to-937'")
ast.parse(s)
(D/'refresh_architecture_zero_delta.py').write_text(s)
(D/'MINIMAL_TOOL_DIFF.patch').write_text(''.join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile=str(P),tofile='refresh_architecture_zero_delta.py')))
print(json.dumps({'tool_sha256':hashlib.sha256(s.encode()).hexdigest(),'tool_bytes':len(s.encode())}))
