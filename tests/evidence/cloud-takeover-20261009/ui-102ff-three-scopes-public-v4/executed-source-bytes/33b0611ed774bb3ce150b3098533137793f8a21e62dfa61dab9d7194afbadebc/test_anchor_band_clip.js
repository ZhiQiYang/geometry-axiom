'use strict';
// Execute the shipped anchor renderer and cross-range calculation. Only the
// surrounding DOM/model query ports are fixtures; this is not browser QA.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const file=process.env.GEOMETRY_TEST_APP_FILE||path.join(__dirname,'../geometry-web/app.js');
const app=fs.readFileSync(file,'utf8');
const crossStart=app.indexOf('function fePointInLoop('),crossEnd=app.indexOf('/* 依主支軸規則算',crossStart);
const drawStart=app.indexOf('  if ((fe.tool === "timber" || fe.anchorPreview)'),drawEnd=app.indexOf('  /* RC 障礙物鬼影',drawStart);
assert.ok(crossStart>=0&&crossEnd>crossStart&&drawStart>=0&&drawEnd>drawStart,'shipped anchor paths must be present');
const code=app.slice(crossStart,crossEnd)+'\n'+app.slice(drawStart,drawEnd);
const box=[0,0,600,400],loops=[{verts:[[0,0],[600,0],[600,400],[0,400]]}];
function render({axis='v',value=200,A=20,bounds=null,globalBounds=box,anchor='at-line k1 v0',info=true,visible=true,sid=1,preview=true}={}){
  const calls=[],fe={tool:'select',anchorPreview:preview,timberHoverAnchor:null},oc={bmap:{1:structuredClone(loops)}};
  const line=info?{constAxis:axis,value,...(bounds?{bounds:bounds.slice()}:{})}:null;
  const env={fe,oc,e:{bid:1},gb:globalBounds.slice(),z:1,root:{id:'root'},refRoot:{id:'references'},annotations:{id:'annotations'},
    $:id=>id==='tbAnchor'?{value:anchor}:id==='tbA'?{value:String(A)}:null,
    ReferenceVisibility:{anchorVisible:()=>visible},feSid:()=>sid,feAnchorLineInfo:()=>line,
    feAnchorEdgeInfo:(a,b)=>a[0]===b[0]?{constAxis:'u',value:a[0]}:a[1]===b[1]?{constAxis:'v',value:a[1]}:null,
    el:(tag,attrs,parent)=>{const node={tag,attrs:{...attrs},parent};calls.push(node);return node;}};
  const before=JSON.stringify({fe,oc,gb:env.gb,line});vm.runInNewContext(code,env);
  assert.equal(JSON.stringify({fe,oc,gb:env.gb,line}),before,'preview must not mutate model, navigation or input bounds');
  return {calls,bands:calls.filter(n=>n.tag==='rect'&&n.attrs.class==='fe-anchor-band'),
    labels:calls.filter(n=>n.attrs.class==='fe-dim fe-anchor-band-label'),highlights:calls.filter(n=>n.attrs.class==='fe-anchor-hi')};
}
function empty(input){const result=render(input);assert.equal(result.bands.length,0,JSON.stringify(result.bands[0]?.attrs));
  assert.equal(result.labels.length,0,'an empty material intersection must not carry a band label');assert.equal(result.highlights.length,1,'the reference highlight remains independent');
  assert.equal(result.calls.filter(n=>n.tag==='g').length,0,'do not create empty material/label groups');}
function rectangle(input,expected){const result=render(input);assert.equal(result.bands.length,1);assert.equal(result.labels.length,1);assert.equal(result.highlights.length,1);
  const a=result.bands[0].attrs;assert.deepEqual([a.x,a.y,a.width,a.height],expected);assert.ok(a.width>0&&a.height>0);
  const label=result.labels[0];assert.equal(label.attrs.x,a.x+a.width/2);assert.equal(label.attrs.y,a.y+a.height/2);
  assert.equal(result.bands[0].parent.attrs['clip-path'],'url(#face-material-clip)');assert.equal(label.parent.attrs['clip-path'],'url(#face-material-clip)');
  assert.equal(label.textContent,'橫向定位示意');}
const z=.25833333333333336,pad=80/z,padded=[-pad,-pad,600+pad,800+pad];
test('390px raw v=1200 case produces no negative-height band',()=>{
  assert.ok(Math.abs((800+pad)-(1200-10)-(-80.32258064516145))<1e-10);empty({value:1200,globalBounds:padded});
});
test('390px raw v=1600 case produces no negative-height band',()=>{
  assert.ok(Math.abs((800+pad)-(1600-10)-(-480.32258064516145))<1e-10);empty({value:1600,globalBounds:padded});
});
test('the transposed u-axis cases reject the same empty intersection',()=>{
  for(const value of [1200,1600])empty({axis:'u',value,globalBounds:[-pad,-pad,800+pad,600+pad]});
});
test('both axes reject intervals wholly below or above their bounds',()=>{
  for(const axis of ['u','v'])for(const value of [-100,1000])empty({axis,value});
});
test('exact contact at either bound has zero material area and no band',()=>{
  for(const axis of ['u','v'])for(const value of [-10,(axis==='u'?600:400)+10])empty({axis,value});
});
test('zero extent in the orthogonal clipping direction is also empty',()=>{
  empty({axis:'u',value:50,bounds:[0,30,100,30]});empty({axis:'v',value:50,bounds:[30,0,30,100]});
});
test('normal u and v intersections retain exact geometry and polygon clipping',()=>{
  rectangle({axis:'u'},[190,0,20,400]);rectangle({axis:'v'},[0,190,600,20]);
});
test('lower-bound partial intersections preserve their positive cropped extent',()=>{
  rectangle({axis:'u',value:5},[0,0,15,400]);rectangle({axis:'v',value:5},[0,0,600,15]);
});
test('upper-bound partial intersections preserve their positive cropped extent',()=>{
  rectangle({axis:'u',value:595},[585,0,15,400]);rectangle({axis:'v',value:395},[0,385,600,15]);
});
test('rule-local bounds take precedence over global overrun for both axes',()=>{
  rectangle({axis:'u',value:60,bounds:[40,30,80,70]},[50,30,20,40]);
  rectangle({axis:'v',value:60,bounds:[40,30,80,70]},[40,50,40,20]);
});
test('a rule-local empty intersection is not rescued by a larger global box or anchor label',()=>{
  for(const axis of ['u','v'])for(const anchor of ['at-line k1 u0','at-line k1 v0','at-line r8 v1600'])
    empty({axis,value:200,bounds:[40,30,80,70],globalBounds:padded,anchor});
});
test('missing or unsupported cross-ranges retain the prior no-band behavior',()=>{
  for(const A of [0,-20]){const r=render({A});assert.equal(r.bands.length,0);assert.equal(r.highlights.length,1);}
  assert.equal(render({anchor:'at-face t99'}).bands.length,0);
  for(const options of [{info:false},{visible:false},{sid:0},{preview:false}])assert.equal(render(options).calls.length,0);
});
test('ordinary at-face material-side bands remain unchanged',()=>{
  rectangle({axis:'v',value:0,anchor:'at-face e0'},[0,0,600,20]);
  rectangle({axis:'u',value:0,anchor:'at-face e3'},[0,0,20,400]);
});
test('strictly positive fractional overlap is preserved without arbitrary pixel tolerance',()=>{
  rectangle({axis:'u',value:609.75},[599.75,0,.25,400]);rectangle({axis:'v',value:409.75},[0,399.75,600,.25]);
});
