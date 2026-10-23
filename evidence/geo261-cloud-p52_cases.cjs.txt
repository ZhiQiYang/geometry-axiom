/* 從真實 harness 擷取同一 P52 流程；量測或對等待修正做具名負對照。 */
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const repo=process.argv[2],filename=path.join(repo,'geometry-web/cdp_test.js');
const source=fs.readFileSync(filename,'utf8').replace(/\r\n/g,'\n');
const mode=process.env.P52_CASE_MODE||'measure',out=process.env.P52_OUT;
if(!out)throw Error('缺少 P52_OUT');
function between(a,b){const i=source.indexOf(a),j=source.indexOf(b,i+a.length);if(i<0||j<0)throw Error('缺少擷取錨點 '+a);return source.slice(i,j);}
const bootstrap=between('/* CDP','  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {');
const helpers=between('  const waitForFaceViewport = async () => {','  const clickFacePoint =')+
 between('  const openFace48 = async () => {','  /* (1) 真滑鼠點外輪廓邊')+
 between('  const setupLinesG196 = async (lines)','  /* helper 自測:')+
 between('  const F_SUPPORT = [','  const enterTimber49');
let p52=between("  console.log('=== P52.",'  /* L 形:');
const restore='    /* P52-3 矩陣把世界留在最後一個情境';
if(mode!=='measure'){
 const a=p52.indexOf('    /* ±n 與負向長度軸'),b=p52.indexOf(restore);
 if(a<0||b<0)throw Error('缺少矩陣範圍');
 p52=p52.slice(0,a)+p52.slice(b);
}
const start=p52.indexOf(restore);
p52=p52.slice(0,start)+`    for(let trial=0;trial<${mode==='measure'?'Number(process.env.P52_REPS||4)':'1'};trial++){\n`+p52.slice(start);
const clickLine='    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);';
const clickAt=p52.indexOf(clickLine),gAt=p52.indexOf('    const g = await eval_',clickAt),footAt=p52.indexOf('    const fxLo',gAt);
if(clickAt<0||gAt<0||footAt<0||p52.indexOf(clickLine,clickAt+1)>=0)throw Error('目標放置必須唯一');
const originalTarget=p52.slice(clickAt,footAt);
if(mode==='measure'){
 const measured=`    const pre=await eval_(\`(()=>{window.__p52Requests=[];window.__p52Start=performance.now();const raw=apiRequest;window.__p52Raw=raw;
 apiRequest=async(...args)=>{const row={command:args[0],startMs:performance.now()-__p52Start};__p52Requests.push(row);try{const r=await raw(...args);row.endMs=performance.now()-__p52Start;row.ok=r?.ok;return r;}catch(e){row.error=String(e);throw e;}};
 const p=new DOMPoint(2000,1500).matrixTransform($('faceEditorRoot').getScreenCTM());return {busy:oc.busy,tool:fe.tool,hit:document.elementFromPoint(p.x,p.y)?.closest('[data-face-hit]')?.dataset.faceHit,title:document.title,url:location.href};})()\`);
    const started=process.hrtime.bigint();
${clickLine}
    const dispatchMs=Number(process.hrtime.bigint()-started)/1e6;
    let g=null,lastRefs=null,polls=0;
    while(Number(process.hrtime.bigint()-started)/1e6<10000){lastRefs=await eval_(\`(async()=>{const r=await apiRequest('references');return {ok:r.ok,ids:(r.timbers||[]).map(t=>t.id),g:(r.timbers||[]).find(t=>t.id===3)?.geometry};})()\`);polls++;if(lastRefs?.g){g=lastRefs.g;break;}await delay(25);}
    const appearedMs=Number(process.hrtime.bigint()-started)/1e6;
    const diag=await eval_(\`(()=>{apiRequest=window.__p52Raw;return {requests:__p52Requests,busy:oc.busy,timbers:fe.timbers.map(t=>t.id)};})()\`);
    const sample={trial,pre,dispatchMs,appearedMs,polls,lastRefs,g,diag};samples.push(sample);
    if(g)await waitForUI('!oc.busy && !ReferenceWorkspace.history.group && fe.timbers.some(t=>t.id===3)',15000);
    sample.settledMs=Number(process.hrtime.bigint()-started)/1e6;
    _log('P52_SAMPLE '+JSON.stringify(sample));
`;
 p52=p52.replace(originalTarget,measured);
}else{
 if(!originalTarget.includes('cdp.makeSettle'))throw Error('等待修正不在候選來源中');
 let target=originalTarget;
 if(mode==='revert-delay')target=clickLine+'\n    await sleep(400);\n'+p52.slice(gAt,footAt);
 const fault=mode==='delay'||mode==='revert-delay'?'delay':mode;
 const hook=`    await eval_(\`(()=>{const raw=apiRequest;window.__p52CaseRaw=raw;window.__p52CaseEvents=[];
 apiRequest=async(command,...rest)=>{const original=command;let injected=null;
 if(command.startsWith('line place 3 on 1 ')&&${JSON.stringify(fault)}==='delay'){injected='place-before-send-900ms';__p52CaseEvents.push({original,injected,ms:performance.now()});await new Promise(r=>setTimeout(r,900));}
 if(command.startsWith('line place 3 on 1 ')&&${JSON.stringify(fault)}==='missing'){__p52CaseEvents.push({original,injected:'omit-place',ms:performance.now()});return {ok:true};}
 if(command.startsWith('line timber 3 27 33 ')&&${JSON.stringify(fault)}==='wrong'){command=command.replace('timber 3 27 33 ','timber 3 28 33 ');injected='A28';}
 const r=await raw(command,...rest);__p52CaseEvents.push({original,command,injected,ok:r?.ok,ms:performance.now()});return r;};return true;})()\`);
`;
 p52=p52.replace(originalTarget,hook+target);
}
p52=p52.trimEnd().replace(/\n  \}$/,'\n    }\n  }');
const body=`
  const check=bodyCheck(),samples=[];let pt48;
  await send('Emulation.setDeviceMetricsOverride',{width:5400,height:3800,deviceScaleFactor:1,mobile:false});
  try {
${helpers}
${p52}
    const events=await eval_('window.__p52CaseEvents||[]');
    const result={mode:${JSON.stringify(mode)},sha:process.env.P52_SHA,passed:passN,failed:failN,exceptions:excN,samples,events};
    fs.writeFileSync(path.join(process.env.P52_OUT,'result.json'),JSON.stringify(result,null,2));
    const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(process.env.P52_OUT,'placement.png'),Buffer.from(shot.result.data,'base64'));
    _log('P52_CASE_RESULT '+JSON.stringify(result));
  }catch(error){
    const events=await eval_('window.__p52CaseEvents||[]');
    fs.writeFileSync(path.join(process.env.P52_OUT,'result.json'),JSON.stringify({mode:${JSON.stringify(mode)},sha:process.env.P52_SHA,passed:passN,failed:failN,exceptions:excN,fatal:error.message,events},null,2));throw error;
  }
  chrome?.kill();process.exit(failN||excN?1:0);
}
`;
const generated=bootstrap+body+source.slice(source.indexOf('async function fatal(e) {'));
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'generated-probe.cjs'),generated);
if(process.env.P52_COMPILE_ONLY==='1'){new Function(generated);console.log('P52 情境語法通過 '+mode);}
else {const target=new Module(filename,module);target.filename=filename;target.paths=Module._nodeModulePaths(path.dirname(filename));process.mainModule=target;require.main=target;target._compile(generated,filename);}
