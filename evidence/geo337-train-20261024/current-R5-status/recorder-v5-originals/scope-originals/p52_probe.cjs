/* 僅在隔離 checkout 執行的 P52 診斷；不寫入或改動產品／正式 harness。 */
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const repo = process.argv[2];
if (!repo || !process.env.P52_OUT) throw Error('需要 repo 與 P52_OUT');
const filename = path.join(repo, 'geometry-web/cdp_test.js');
const source = fs.readFileSync(filename, 'utf8').replace(/\r\n/g,'\n');
function between(start, end, from = 0) {
  const i = source.indexOf(start, from), j = source.indexOf(end, i + start.length);
  if (i < 0 || j < 0) throw Error('診斷擷取錨點不存在：' + start);
  return source.slice(i, j);
}
const bootstrap = between('/* CDP', '  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {');
const viewportHelpers = between('  const waitForFaceViewport = async () => {', '  const clickFacePoint =');
const faceHelpers = between('  const openFace48 = async () => {', '  /* (1) 真滑鼠點外輪廓邊');
const setupHelper = between('  const setupLinesG196 = async (lines)', '  /* helper 自測:');
const support = between('  const F_SUPPORT = [', '  const enterTimber49');
let p52 = between("  console.log('=== P52.", '  /* L 形:');
const restoreStart = p52.indexOf('    /* P52-3 矩陣把世界留在最後一個情境');
if (restoreStart < 0) throw Error('缺少 P52 矩陣收尾');
// 原有 P52 的 32 種 UI 情境先完整執行一次，再重複原 P52-4/5 路徑。
p52 = p52.slice(0, restoreStart) + '\n    for (let trial=0;trial<Number(process.env.P52_REPS||4);trial++) {\n' + p52.slice(restoreStart);
const oldTarget = `    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);
    await sleep(400);
    const g = await eval_(\`(async()=>{ const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3); return t && t.geometry; })()\`);`;
if (p52.split(oldTarget).length !== 2) throw Error('P52-5 擷取必須唯一');
const newTarget = `    const pre=await eval_(\`(()=>{const p=new DOMPoint(2000,1500).matrixTransform($('faceEditorRoot').getScreenCTM());
      const el=document.elementFromPoint(p.x,p.y);window.__p52Requests=[];window.__p52Start=performance.now();
      const raw=apiRequest;window.__p52Raw=raw;apiRequest=async(...args)=>{const row={command:args[0],startMs:performance.now()-window.__p52Start};
        window.__p52Requests.push(row);try{const r=await raw(...args);row.endMs=performance.now()-window.__p52Start;row.ok=r?.ok;return r;}
        catch(e){row.error=String(e);throw e;}};
      return {busy:oc.busy,tool:fe.tool,hit:el?.closest('[data-face-hit]')?.dataset.faceHit,point:{x:p.x,y:p.y},title:document.title,url:location.href};})()\`);
    const started=process.hrtime.bigint();
    await click(pt48(2000,1500).x,pt48(2000,1500).y);
    const dispatchMs=Number(process.hrtime.bigint()-started)/1e6;
    let g=null,polls=0,lastRefs=null;
    while(Number(process.hrtime.bigint()-started)/1e6<10000){
      lastRefs=await eval_(\`(async()=>{const refs=await apiRequest('references');return {ok:refs.ok,error:refs.error,ids:(refs.timbers||[]).map(t=>t.id),g:(refs.timbers||[]).find(t=>t.id===3)?.geometry};})()\`);
      polls++;if(lastRefs?.g){g=lastRefs.g;break;}await delay(25);
    }
    const appearedMs=Number(process.hrtime.bigint()-started)/1e6;
    const diag=await eval_(\`(()=>{apiRequest=window.__p52Raw;return {requests:window.__p52Requests,busy:oc.busy,toasts:[...document.querySelectorAll('.toast')].map(t=>t.textContent),timbers:fe.timbers.map(t=>t.id)};})()\`);
    const sample={trial,pre,dispatchMs,appearedMs,polls,lastRefs,g,diag};samples.push(sample);
    _log('P52_SAMPLE '+JSON.stringify(sample));
    if(g)await waitForUI('!oc.busy && !ReferenceWorkspace.history.group && fe.timbers.some(t=>t.id===3)',15000);
    sample.settledMs=Number(process.hrtime.bigint()-started)/1e6;
    if(trial===0){const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(process.env.P52_OUT,'placement.png'),Buffer.from(shot.result.data,'base64'));}`;
p52 = p52.replace(oldTarget, newTarget);
// 在原本 P52 區塊關閉前補上重複試次的括號；原幾何斷言逐字保留。
p52 = p52.trimEnd().replace(/\n  \}$/, '\n    }\n  }');
const body = `
  const check=bodyCheck(),samples=[];
  await send('Emulation.setDeviceMetricsOverride',{width:5400,height:3800,deviceScaleFactor:1,mobile:false});
  let pt48;
${viewportHelpers}
${faceHelpers}
${setupHelper}
${support}
${p52}
  fs.writeFileSync(path.join(process.env.P52_OUT,'samples.json'),JSON.stringify({schema:'geo261-p52-probe/1',sha:process.env.P52_SHA,passed:passN,failed:failN,exceptions:excN,samples},null,2)+String.fromCharCode(10));
  _log('P52_PROBE_RESULT '+JSON.stringify({passed:passN,failed:failN,exceptions:excN,samples:samples.length}));
  chrome?.kill();process.exit(failN>0||excN>0?1:0);
}
`;
const footer = source.slice(source.indexOf('async function fatal(e) {'));
const generated = bootstrap + body + footer;
fs.mkdirSync(process.env.P52_OUT,{recursive:true});
fs.writeFileSync(path.join(process.env.P52_OUT,'generated-probe.cjs'),generated);
if (process.env.P52_COMPILE_ONLY === '1') {
  new Function(generated);
  console.log('P52 診斷程式語法與擷取錨點通過');
} else {
  const target = new Module(filename, module);
  target.filename = filename;
  target.paths = Module._nodeModulePaths(path.dirname(filename));
  // 令既有 harness 的 require.main 檢查按正式入口執行。
  require.main = target;
  process.mainModule = target;
  target._compile(generated, filename);
}
