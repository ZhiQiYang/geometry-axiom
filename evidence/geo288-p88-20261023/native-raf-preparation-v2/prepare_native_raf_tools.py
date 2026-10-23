"""Prepare, never execute, one F-bound original-native-rAF scheduling proof."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

here=Path(__file__).resolve().parent
old=here/'p88-only-query-tools-render-trace'
out=here/'p88-native-raf-tools-v2'
repo=Path('/tmp/g288p88final-3d681636')
F='3d681636902371ecc528b20f51eea33e272581c9'
out.mkdir(exist_ok=False)
(out/'trace-tools').mkdir()
def h(data):return hashlib.sha256(data).hexdigest()
def once(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new,1)
for rel in ['capture.py','only-p88.cjs']:
    shutil.copyfile(old/rel,out/rel)
fixed=(repo/'geometry-web/grid_rule_lines_test.js').read_bytes()
withdrawn=(here/'candidate-local-v5/grid_rule_lines_test.js.original').read_bytes()
assert h(fixed)=='8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52'
assert h(withdrawn)=='c47259607a3299d49e1044f3d4d6e5561c0601e0f2295fb7ec5f2255261f4e8c'
(out/'P88.fixed.js').write_bytes(fixed);(out/'P88.withdrawn.js').write_bytes(withdrawn)
patch=''.join(difflib.unified_diff(fixed.decode().splitlines(True),withdrawn.decode().splitlines(True),fromfile='F/geometry-web/grid_rule_lines_test.js',tofile='withdrawn/geometry-web/grid_rule_lines_test.js'))
(out/'P88.withdrawn.patch').write_text(patch)
manifest={'schema':'geo288-p88-final-native-raf-source-variants/1','repo':str(repo),'sha':F,
          'only_source_change_in_withdrawn':'geometry-web/grid_rule_lines_test.js','executed':False,
          'files':[{'source_relative':'geometry-web/grid_rule_lines_test.js','original_sha256':h(fixed),
                    'candidate':str(out/'P88.fixed.js'),'candidate_sha256':h(fixed),
                    'withdrawn':str(out/'P88.withdrawn.js'),'withdrawn_sha256':h(withdrawn),
                    'patch':str(out/'P88.withdrawn.patch'),'patch_sha256':h(patch.encode())}]}
(out/'SOURCE_VARIANTS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

pre=(old/'trace-tools/preload.cjs').read_text()
anchor="const queryAfterLine=queryAfterLines[0];"
pre=once(pre,anchor,anchor+"""
const querySuccessLines=queryBytes.toString('utf8').split(/\\r?\\n/).map((line,i)=>line.trim()==='paintQuery();'?i+1:null).filter(Boolean);
if(querySuccessLines.length!==1)throw Error('Expected unique original query success paint callsite');
const querySuccessLine=querySuccessLines[0];
const appSource=path.join(repo,'geometry-web','app.js'),appBytes=fs.readFileSync(appSource),appText=appBytes.toString('utf8');
const restoreAnchor='requestAnimationFrame(() => {\\n      if (fe.gridPreviewSeq !== seq || pane.dataset.bid !== String(bid) ||';
if(appText.split(restoreAnchor).length!==2)throw Error('Expected unique F original scroll-restore rAF');
const restoreStart=appText.indexOf(restoreAnchor),restoreRafLine=appText.slice(0,restoreStart).split('\\n').length;
const restoreCallbackStart=restoreStart+'requestAnimationFrame('.length;
const restoreCallbackEnd=appText.indexOf('\\n    });',restoreCallbackStart)+'\\n    }'.length;
if(restoreCallbackEnd<restoreCallbackStart)throw Error('Original restore callback boundary missing');
const restoreCallbackSource=appText.slice(restoreCallbackStart,restoreCallbackEnd);
""")
pre=pre.replace('geo288-p88-readonly-trace-and-controlled-query/1','geo288-p88-original-native-raf-interleaving/1')
pre=pre.replace('P88-original-query-release-after-mode-measure','P88-measure-before-original-native-restore')
pre=once(pre,"  query_source:querySource,query_source_sha256:hash(queryBytes),query_after_callsite_line:queryAfterLine,", "  query_source:querySource,query_source_sha256:hash(queryBytes),query_after_callsite_line:queryAfterLine,query_success_callsite_line:querySuccessLine,\n  app_source:appSource,app_source_sha256:hash(appBytes),restore_raf_line:restoreRafLine,restore_callback_source:restoreCallbackSource,restore_callback_sha256:hash(Buffer.from(restoreCallbackSource)),\n  controlled_api_wrapper_replaces_promise_while_preserving_resolved_object:true,")
pre=once(pre,'function installBrowserTrace(proofMode, queryAfterLine) {','function installBrowserTrace(proofMode, queryAfterLine, restoreRafLine, restoreCallbackSource, querySuccessLine) {')
fragment=(here/'native-raf-browser-fragment.js').read_text()
pre=once(pre,'  // Synchronous observation only: preserve original this, arguments, return\n',fragment+'\n  // Synchronous observation only: preserve original this, arguments, return\n')
pre=once(pre,'    let result;\n    try{result=Reflect.apply(originalRender,this,args);}',"""    let result;
    const previousRender=activeRender;
    activeRender={invocation,matching:!!pendingMeasure&&!!heldQuery?.released&&!!heldQuery?.returned&&heldQuery.arm_token===armedToken&&ReferenceWorkspace.context()===heldQuery.context&&stack.includes('at paintQuery (')&&stack.includes('at query (')&&stack.includes('/grid-rule-lines.js:'+querySuccessLine+':')};
    try{result=Reflect.apply(originalRender,this,args);}""")
pre=once(pre,"    catch(error){observeRender('renderFaceInspector-throw',{invocation,stack});throw error;}\n", "    catch(error){observeRender('renderFaceInspector-throw',{invocation,stack});throw error;}\n    finally{activeRender=previousRender;}\n")
pre=once(pre,"        append('query-response-returned',{command:cmd,result_json:JSON.stringify(result),state:state()});", "        heldQuery.returned=true;\n        append('query-response-returned',{command:cmd,result_json:JSON.stringify(result),state:state()});")
start=pre.index('  async function injectQueryRelease(');end=pre.index('  function publicControl()',start)
pre=pre[:start]+pre[end:]
pre=once(pre,'      return injectQueryRelease(selector,p);','      return undefined;')
pre=once(pre,'    stop() {','    measureWithRestore,\n    stop() {')
pre=once(pre,'      observer.disconnect();',"""      observer.disconnect();
      if(pendingMeasure){errors.push('Native rAF measurement unresolved at cleanup');rejectPending(Error('P88 native rAF cleanup before completion'));}
      if(window.requestAnimationFrame===rafWrapper)window.requestAnimationFrame=originalRaf;
      else errors.push('Native rAF wrapper lost ownership; not forcibly restored');
      if(window.cancelAnimationFrame===cancelRafWrapper)window.cancelAnimationFrame=originalCancelRaf;
      else errors.push('Native cancelAnimationFrame wrapper lost ownership; not forcibly restored');""")
oldwrap="`(async()=>{const p=(${expression});const t=window.__geo288P88PassiveTrace_v1;if(!t)throw Error('P88 trace missing');await t.afterMeasure(${JSON.stringify(selector)},p);return p;})()`"
newwrap="`(async()=>{const t=window.__geo288P88PassiveTrace_v1;if(!t)throw Error('P88 trace missing');return await t.measureWithRestore(${JSON.stringify(selector)},()=>(${expression}),${measurementId});})()`"
pre=once(pre,oldwrap,newwrap)
pre=once(pre,'const measurement = /^','let measurementSerial=0;\nconst measurement = /^')
pre=once(pre,"      nodeEvent('measure-request', {selector});","      const measurementId=++measurementSerial;\n      nodeEvent('measure-request', {selector,measurement_id:measurementId});")
pre=once(pre,"nodeEvent('measure-return', {selector, original_measure:value});","nodeEvent('measure-return', {selector, measurement_id:measurementId, original_measure:value});")
pre=once(pre,'${JSON.stringify(mode)},${JSON.stringify(queryAfterLine)})','${JSON.stringify(mode)},${JSON.stringify(queryAfterLine)},${JSON.stringify(restoreRafLine)},${JSON.stringify(restoreCallbackSource)},${JSON.stringify(querySuccessLine)})')
(out/'trace-tools/preload.cjs').write_text(pre)

loader=(old/'trace-tools/patch-loader.cjs').read_text()
loader=once(loader,"  const fixed=variant!=='withdrawn',body=fixed?fs.readFileSync(row.candidate):raw;","  const fixed=variant!=='withdrawn',body=fixed?raw:fs.readFileSync(row.withdrawn);")
loader=once(loader,'(fixed?row.candidate_sha256:row.original_sha256)','(fixed?row.original_sha256:row.withdrawn_sha256)')
loader=once(loader,'candidate:fixed?row.candidate:null','candidate:fixed?null:row.withdrawn')
(out/'trace-tools/patch-loader.cjs').write_text(loader)

driver=(old/'run_proof.py').read_text().replace("FINAL = '13d02c1db7022145a52ee063286a558e595eb212'",f"FINAL = '{F}'")
driver=once(driver,"len(candidate['files']) == 2", "len(candidate['files']) == 1")
driver=once(driver,"{'geometry-web/cdp_helpers.js', 'geometry-web/grid_rule_lines_test.js'}", "{'geometry-web/grid_rule_lines_test.js'}")
driver=driver.replace('指定兩檔','固定 F 的 P88 單檔')
driver=once(driver,"    candidate_frozen = dict(candidate, files=[])","""    need(candidate['sha']==a.sha and candidate['files'][0]['original_sha256']=='8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52'
         and candidate['files'][0]['withdrawn_sha256']=='c47259607a3299d49e1044f3d4d6e5561c0601e0f2295fb7ec5f2255261f4e8c', 'F 原件／撤回唯一 bytes 不符')
    candidate_frozen = dict(candidate, files=[])""")
driver=once(driver,"candidate_frozen['files'].append(dict(entry, candidate=str(target), patch=str(patch_target)))", """withdrawn_source=Path(entry['withdrawn'])
        withdrawn_target=tools / ('withdrawn-' + withdrawn_source.name)
        need(h(withdrawn_source.read_bytes())==entry['withdrawn_sha256'], '撤回 bytes 變動')
        withdrawn_target.write_bytes(withdrawn_source.read_bytes())
        frozen[str(withdrawn_source.resolve())]={'sha256':h(withdrawn_source.read_bytes()),'snapshot':str(withdrawn_target)}
        candidate_frozen['files'].append(dict(entry, candidate=str(target), withdrawn=str(withdrawn_target), patch=str(patch_target)))""")
driver=driver.replace('19700 + index','19801 + index').replace('9710 + index','9720 + index')
driver=once(driver,"len(memory['files']) == 2","len(memory['files']) == 1")
driver=once(driver,"expected['candidate_sha256' if fixed else 'original_sha256']", "expected['original_sha256' if fixed else 'withdrawn_sha256']")
driver=once(driver,"(expected['candidate'] if fixed else None)","(None if fixed else expected['withdrawn'])")
driver=driver.replace("event['kind'] == 'controlled-query-release'","event['kind'] == 'controlled-native-raf-measurement'")
driver=once(driver,"                    scroll_events =", """                    native=injection['native_callback']
                    need(native['native_dispatch_count']==1 and native['original_measure_evaluations']==1
                         and native['this_is_window'] is True and native['callback_completed'] is True
                         and native['callback_source_matches'] is True and native['cancelled'] is False
                         and native['original_request_animation_frame_native'] is True
                         and native['original_cancel_animation_frame_native'] is True
                         and injection['parsed_json_unchanged'] is True,
                         '原 native callback／原單次量測／parsed JSON 守門不符')
                    scroll_events =""")
driver=once(driver,"                    clicks = [event", """                    native_rows={kind:[e for e in observed['events'] if e['kind']==kind] for kind in ('native-restore-registered','native-restore-entry','native-restore-return')}
                    need(all(len(events)==1 for events in native_rows.values()), '原 native callback 登錄／進出事件不唯一')
                    reg,entry,returned=[native_rows[k][0] for k in ('native-restore-registered','native-restore-entry','native-restore-return')]
                    measured=[e for e in observed['events'] if e['kind']=='measure' and e.get('inside_native_restore_before_original') is True]
                    need(len(measured)==1 and reg['serial']<entry['serial']<measured[0]['serial']<returned['serial']<scroll_events[0]['serial']
                         and all(e['native_id']==native['native_id'] for e in (reg,entry,returned))
                         and returned['original_threw'] is False and measured[0]['original_measure']==injection['original_measure'], '原量測／native callback 時序或原值不符')
                    node_returns=[e for e in observed['node_events'] if e['kind']=='measure-return' and e.get('measurement_id')==injection['measurement_id']]
                    need(len(node_returns)==1 and node_returns[0]['selector']=='#refGuideMode' and node_returns[0]['original_measure']==injection['original_measure'], '原量測 CDP 回傳值或身份不符')
                    pressed=[e for e in observed['node_events'] if e['kind']=='cdp-mouse-request' and e['params']['type']=='mousePressed'
                             and int(e['monotonic_ns'])>int(node_returns[0]['monotonic_ns'])]
                    need(pressed, '原量測 CDP 回覆後缺真 mousePressed')
                    row['first_post_measure_mouse_request']=pressed[0]
                    if variant=='withdrawn':
                        need(pressed[0]['params']['x']==injection['original_measure']['x'] and pressed[0]['params']['y']==injection['original_measure']['y'], '撤回的真 CDP mousePressed 並未使用原舊座標')
                    clicks = [event""")
ast.parse(driver);(out/'run_proof.py').write_text(driver)
for rel in ['run_proof.py','trace-tools/preload.cjs','trace-tools/patch-loader.cjs']:
    (out/(Path(rel).name+'.diff')).write_text(''.join(difflib.unified_diff((old/rel).read_text().splitlines(True),(out/rel).read_text().splitlines(True),fromfile=str(old/rel),tofile=str(out/rel))))
checks=[]
for relative in ['trace-tools/preload.cjs','trace-tools/patch-loader.cjs']:
    command=['env','-u','NODE_OPTIONS','node','--check',str(out/relative)]
    process=subprocess.run(command,capture_output=True)
    checks.append({'command':command,'exit':process.returncode,'stdout':process.stdout.decode(),'stderr':process.stderr.decode()})
    assert process.returncode==0
shutil.copyfile(here/'P88_NATIVE_RAF_PROOF_DESIGN.md',out/'DESIGN.md')
shutil.copyfile(here/'native-raf-browser-fragment.js',out/'native-raf-browser-fragment.js')
shutil.copyfile(Path(__file__),out/'prepare_native_raf_tools.py')
files={str(p.relative_to(out)):h(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}
(out/'PREPARATION.json').write_text(json.dumps({'schema':'geo288-p88-native-raf-proof-preparation/1','sha':F,'executed':False,'scope':'External diagnostic preparation only. No source or formal runner changed; no Chrome/build launched. Prior failed experiment remains preserved.','syntax_checks':checks,'files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'preparation':str(out/'PREPARATION.json'),'sha256':h((out/'PREPARATION.json').read_bytes()),'executed':False}))
