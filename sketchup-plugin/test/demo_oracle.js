// 從使用者確認的原始 demo 執行 JavaScript，建立 Ruby 測試的獨立數值基準。
// 使用：node sketchup-plugin/test/demo_oracle.js <framing-mode-demo.html> [輸出.json]
// 不複製、不重寫 demo 規則；僅停用三個畫面啟動呼叫，DOM 事件登記不執行。
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const path = require('node:path');

const sourcePath = process.argv[2];
if (!sourcePath) throw new Error('請提供原始 framing-mode-demo.html 路徑');
const html = fs.readFileSync(sourcePath, 'utf8').replace(/\r\n/g, '\n');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
if (scripts.length !== 1) throw new Error('預期 demo 只有一份內嵌 script');
const startup = '\ninit3D();\nrefresh();\npfInit();';
if (!scripts[0][1].includes(startup)) throw new Error('demo 啟動位置已改變，請人工核對');
const source = scripts[0][1].replace(startup, '');
const context = vm.createContext({
  document: {getElementById() { return {addEventListener() {}}; }, addEventListener() {}},
});
vm.runInContext(source, context, {filename: sourcePath, timeout: 5000});
const oracle = vm.runInContext(`(() => {
  const pick = (obj, keys) => Object.fromEntries(keys.filter(k => k in obj).map(k => [k, obj[k]]));
  const sourceFaces=FACES.slice(), originalBox=box3;
  rgb=()=>[0,0,0]; draw3D=()=>{};
  v3.gl={bindBuffer(){},bufferData(){}};
  Object.assign(v3.show,{wall:false,slab:false,frame:true,board:true});
  const memberKeys = ['role','ri','ei','eo','par','a','b','off','pos','orient','s0','s1','len','clash','kind'];
  const flat = (face, overrides = {}) => {
    const f = {id:face.id,rings:face.rings,p:{...face.p,...overrides},mode:'flat'};
    build(f);
    const boxes=[];
    box3=(vertices,...args)=>{const before=vertices.length;originalBox(vertices,...args);if(vertices.length>before)boxes.push(args.slice(0,6));};
    f.applied=true;f.step=5;
    FACES.splice(0,FACES.length,f);rebuild3D();FACES.splice(0,FACES.length,...sourceFaces);
    return {id:f.id,rings:f.rings,params:f.p,
      counts:Object.fromEntries(['wall','pri','sec'].map(k => [k,f.g.members.filter(m => m.role===k).length])),
      members:f.g.members.map(m => pick(m,memberKeys)),
      la:f.g.LA,lb:f.g.LB,lines:f.g.lines.map(l => pick(l,['t','kind'])),
      clashes:primaryClashes(f,f.p),options:clashFreeOptions(f),
      checks:check(f).map(([ok,title,detail])=>({ok,title,detail})),
      badEnds:endFaces(f).map(x=>({id:x.m.id,e:x.e,col:x.col})),boxes};
  };
  const flats = sourceFaces.map(f=>flat(f));
  const variants = [
    {name:'kitchen_top_right',...flat(FACES[4],{corner:'tr'})},
    {name:'living_no_column_edges',...flat(FACES[0],{colEdge:false})},
    {name:'custom_parameters',...flat(FACES[2],{longY:false,corner:'br',cap:300,gap:3,tw:33,pw:900,pl:1800,bear:10})},
    ...[true,false].flatMap(longY => Object.keys(CORNERS).map(corner => ({name:'orientation_'+longY+'_'+corner,...flat(FACES[2],{longY,corner})})))
  ];
  const defaults = {t:6,a:27,b:33,L:2400,cap:450,flip:false};
  const profile = (name, points, overrides = {}) => {
    Object.assign(PF,defaults,overrides,{pts:points.map(p=>p.slice()),M:null});
    const model=pfModel(); PF.M=model;
    const boxes=[];
    // 只攔截 pf3D 交給渲染器的矩形盒，生成的位置仍由原始 pf3D 決定。
    box3=(_a,x0,y0,x1,y1,z0,z1)=>boxes.push([x0,y0,x1,y1,z0,z1]);
    rgb=()=>[0,0,0]; v3.show.wall=false; pf3D([]);
    return {name,points:PF.pts,params:pick(PF,Object.keys(defaults)),
      boards:model.boards.map(x=>pick(x,['seg','r'])),longs:model.longs.map(x=>pick(x,['r'])),ribs:model.ribs.map(x=>pick(x,['seg','r'])),
      checks:pfChecks(model).map(([ok,title,detail])=>({ok,title,detail})),boxes};
  };
  return {flats,variants,profiles:[
    profile('cove',PF_PRESETS.cove),profile('drop',PF_PRESETS.drop),
    profile('rotated',PF_PRESETS.cove,{a:33,b:27}),profile('flipped',PF_PRESETS.cove,{flip:true}),
    profile('short_extrusion',PF_PRESETS.cove,{L:449}),profile('exact_spacing',PF_PRESETS.drop,{L:900,cap:300}),
    profile('custom_section',PF_PRESETS.cove,{t:9,a:30,b:40,L:1250,cap:320})
  ],panel3700:panelAxis(3700,915,2,27),beams:BEAMS.map(b=>({id:b.id,rect:beamRect(b),bottom:beamBottom(b),top:ZD.slab}))};
})()`, context, {timeout:5000});
const result = {
  provenance: {source:'tasks/reference/framing-mode-demo.html',sha256:crypto.createHash('sha256').update(html).digest('hex'),normalization:'CRLF → LF',method:'原始 script + 停用畫面啟動；直接呼叫原始規則與 pf3D'},
  ...JSON.parse(JSON.stringify(oracle)),
};
const destination = process.argv[3] || path.join(__dirname,'fixtures','demo_oracle.json');
fs.mkdirSync(path.dirname(destination), {recursive:true});
fs.writeFileSync(destination, JSON.stringify(result,null,2)+'\n');
console.log('demo SHA-256: '+result.provenance.sha256);
console.log('平釘五房間構件總數: '+result.flats.map(f=>f.members.length).join(', '));
console.log('客廳記號: '+result.flats[0].lines.map(l=>l.t).join(', '));
console.log('3700 mm 縫: '+result.panel3700.seams.join(', '));
console.log('廚房右上衝突縫(0 起算): '+result.variants[0].clashes.join(', '));
console.log('廚房可行組合: '+result.variants[0].options.join(' / '));
console.log('間接照明槽: '+[result.profiles[0].boards.length,result.profiles[0].longs.length,result.profiles[0].ribs.length].join('/')+'；檢查 '+result.profiles[0].checks.filter(c=>c.ok).length+'/'+result.profiles[0].checks.length+'；3D '+result.profiles[0].boxes.length+' 盒');
console.log('已寫入 '+destination);
