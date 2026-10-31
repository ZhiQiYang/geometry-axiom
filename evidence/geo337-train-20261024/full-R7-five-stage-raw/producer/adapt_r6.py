from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).resolve().parent;OLD=Path('/workspace/geo323-r6-full-collection-20261024')
H=lambda b:hashlib.sha256(b).hexdigest()
raw=(OLD/'collect.py').read_bytes();assert H(raw)=='2601305276977f1a3850f7cf9f35497210013ec816ac63df0767841dd9ecc7ce'
s=raw.decode()
for a,b in [('2bbe54f19b2d19e8a816530f0c4edca950629a34','6df0264f75e84f03adb70746b6ac3db07a9910fc'),('/workspace/g337323R6','/tmp/g337323R7'),('/workspace/geo323-final-r6-stage-tools-20261024','/tmp/geo323-final-r7-stage-tools-20261024'),('/workspace/geo323-final-r6-source-20261024','/tmp/geo323-final-r7-source-20261024'),('/tmp/geo323-r6-full-package-20261024','/tmp/geo323-r7-full-package-20261024'),('ede91bc92d702d4d3f386ab2c7622658ef5fc5ffdba1c8e5e53fd6201d510209','__FROZEN_TERMINAL_PLAN_SHA256__'),('TOP_LEVEL_TOOL_TRANSCRIPT_LIMIT.json','TOOL_RESPONSE_SCOPE.json'),('ORIGINAL_R6_FIVE_STAGE_RAW.tar.gz','ORIGINAL_R7_FIVE_STAGE_RAW.tar.gz')]:
 assert a in s,a;s=s.replace(a,b)
a="    need(plan['source_sha']==R,'fixed R plan')"
b=a+"\n    for name,pin in plan['terminal_bindings'].items():\n        original=Path(pin['path']);need(original.stat().st_size==pin['bytes'] and digest(original)==pin['sha256'],'frozen original terminal binding '+name)"
assert s.count(a)==1;s=s.replace(a,b)
changes={
 "need(driver['source_sha']==R and driver['exit']==outer['exit']==1,'original outer Recorder and launcher terminal1 retained')":"need(driver['source_sha']==R and type(outer['exit']) is int and driver['exit']==outer['exit']==plan['expected_terminal']['outer_exit'],'frozen actual outer Recorder and launcher terminal retained')",
 "need(annotation['complete_original_tool_response_saved'] is False and annotation['stdout_stderr_reconstructed'] is False and annotation['source_sha']==R,'missing tool transcript disclosed, never invented')":"need(annotation['stdout_stderr_reconstructed'] is False and annotation['source_sha']==R and annotation['supplied_api_files'],'actual owner-supplied API objects retained without reconstruction or completeness inference')",
 "need(len(driver['commands'])==2 and [x['actual_exit']for x in driver['commands']]==[0,1],'original df and five-stage outer exits')":"need(len(driver['commands'])==2 and [x['actual_exit']for x in driver['commands']]==[0,outer['exit']],'original df and five-stage outer exits')",
 "need([c['actual_process_exit'] for c in outer['commands']]==[0,0,1,1,1],'original cumulative CLI exits')":"need([c['actual_process_exit'] for c in outer['commands']]==plan['expected_terminal']['cumulative_cli_exits'],'frozen original cumulative CLI exits')",
 "need([r['stages'][n]['execution_exit'] for n in STAGES]==[0,0,1,0,0],'original own-stage exits')":"need([r['stages'][n]['execution_exit'] for n in STAGES]==plan['expected_terminal']['own_stage_exits'],'frozen original own-stage exits')",
 "need('ABC_result' not in r,'missing downstream audit stays missing')":"need(('ABC_result' in r)==plan['expected_terminal']['ABC_result_present'],'original downstream audit presence stays unchanged')",
 "need(r['quantitative_targets']['N64_fix_main']['target_met'] is False and r['quantitative_targets']['small_N_no_regression']['points']['16']['target_met'] is False,'both original R6 N64 and N16 targets stay red')":"need(r['quantitative_targets']==plan['expected_terminal']['quantitative_targets'],'all original target values and verdicts retained, never inferred from R6')",
 "for name in ['collect.py','PLAN.json','launch.py','README.md','prepare_plan.py','R5_TO_R6_COLLECTOR.diff','PROVENANCE.json','TOOL_RESPONSE_SCOPE.json','adapt_r5.py']:":"for name in ['collect.py','PLAN.json','launch.py','README.md','freeze_terminal_plan.py','prepare_plan.py','R6_TO_R7_COLLECTOR.diff','PROVENANCE.json','TOOL_RESPONSE_SCOPE.json','adapt_r6.py','COLLECTOR_PINS.json']:",
 "outer_tool_transcript_complete=False":"outer_tool_transcript_sequence_completeness='not independently inferred'",
 "'Original compare1, N64/main>1.3 and N16/base>1 remain red; perf/profile execution0 differs from cumulative CLI1.'":"'Every current original target and exit is copied from frozen terminal receipts; no R6 verdict is imposed and no product acceptance is inferred.'",
 "'No complete top session60337 API tool response was supplied to this collector; original outer-five Recorder retains actual launch exit1 and full streams. The later annotation is explicitly not original tool raw.'":"'Exactly the supplied root-owned API response files are preserved bytewise. Full API sequence completeness is not inferred. Original outer Recorder and stage streams retain their actual exits and full bytes.'"
}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
ast.parse(s);(D/'collect.template.py').write_text(s);(D/'R6_TO_R7_COLLECTOR.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='R6-collector',tofile='R7-terminal-bound-collector')))
raw=(OLD/'launch.py').read_bytes();assert H(raw)=='215b2629aaf2cdb7b57e4c4a0719b30b95f3bf80bc62a5e72717146c2ce972b4';s=raw.decode().replace('2601305276977f1a3850f7cf9f35497210013ec816ac63df0767841dd9ecc7ce','__FROZEN_COLLECTOR_SHA256__').replace('ede91bc92d702d4d3f386ab2c7622658ef5fc5ffdba1c8e5e53fd6201d510209','__FROZEN_TERMINAL_PLAN_SHA256__').replace('2bbe54f19b2d19e8a816530f0c4edca950629a34','6df0264f75e84f03adb70746b6ac3db07a9910fc')
a="""    terminal=Path('/tmp/geo323-shadow-hint-F-observation-20261024/execution/RESULT.json')
    need(digest(terminal)=='5ef9f5d6f00268f1e069fe08180b76807239b23665931397eccba3a27baef5e1','original K shadow terminal pin')
    k=json.loads(terminal.read_bytes())
    need(k['source_sha']=='6df0264f75e84f03adb70746b6ac3db07a9910fc' and k['exit']==0 and k['ended_utc'] and k['source_clean_after'] is True,'K shadow original terminal before heavy collection')"""
b="""    plan=json.loads((ROOT/'PLAN.json').read_bytes())
    pin=plan['terminal_bindings']['outer'];terminal=Path(pin['path'])
    need(digest(terminal)==pin['sha256'] and terminal.stat().st_size==pin['bytes'],'original R7 terminal pin')
    k=json.loads(terminal.read_bytes())
    need(k['source_sha']=='6df0264f75e84f03adb70746b6ac3db07a9910fc' and type(k['exit']) is int and k['exit']==plan['expected_terminal']['outer_exit'],'actual R7 terminal before heavy collection')"""
assert s.count(a)==1;s=s.replace(a,b);ast.parse(s);(D/'launch.template.py').write_text(s);(D/'R6_TO_R7_LAUNCH.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='R6-launch',tofile='R7-terminal-bound-launch')))
(D/'PROVENANCE.json').write_text(json.dumps({'R6_collector':str(OLD/'collect.py'),'R6_collector_sha256':'2601305276977f1a3850f7cf9f35497210013ec816ac63df0767841dd9ecc7ce','R6_package_actual_peer':'/workspace/train337-canvas-peer-resume/R6_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json','R6_package_actual_peer_sha256':'85e835f23d2c595de5abc63b18eea45e1b3c56a9b52dc5e392660bf4450be9b9','R7_source':'6df0264f75e84f03adb70746b6ac3db07a9910fc','no_active_OUT_read':True,'no_subject_executed':True,'scope':'Only tools prepared. Current R7 outcomes and membership must be frozen from true terminal artifacts before collection.'},indent=2)+'\n')
print(json.dumps({'collector_template_sha256':H((D/'collect.template.py').read_bytes()),'launcher_template_sha256':H((D/'launch.template.py').read_bytes()),'active_OUT_read':False}))
