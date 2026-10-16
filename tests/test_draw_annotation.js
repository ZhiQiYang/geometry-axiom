/* Executes the real replay function. This DOM double is a unit test, not a
   browser render or a native draw-operation producer. */
'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const script=fs.readFileSync(process.env.GEOMETRY_TEST_DRAW_APP||require.resolve('../geometry-web/app.js'),'utf8');
const start=script.indexOf('function replay(ops, root) {');
const finish=script.indexOf('/* ---- 重繪 ---- */',start);
assert.ok(start>=0&&finish>start,'actual application replay function must exist');
const replaySource=script.slice(start,finish);
class Element {
  constructor(name){this.name=name;this.attributes={};this.dataset={};this.childNodes=[];this.ownText='';}
  setAttribute(key,value){this.attributes[key]=String(value);if(key.startsWith('data-'))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(value);}
  getAttribute(key){return this.attributes[key]??null;}
  appendChild(child){this.childNodes.push(child);return child;}
  set textContent(value){this.ownText=String(value);this.childNodes=[];}
  get textContent(){return this.ownText+this.childNodes.map(c=>c.textContent).join('');}
}
function render(ops){
  const root=new Element('svg'),context={STYLE:{0:{line:'#234',text:11,mid:true},1:{line:'#123',text:15,bold:true},2:{line:'#456',w:2,fill:'#789',fop:.5,dash:'2 3'}},
    el(name,attributes,parent){const e=new Element(name);for(const [k,v] of Object.entries(attributes))e.setAttribute(k,v);if(parent)parent.appendChild(e);return e;}};
  vm.runInNewContext(replaySource,context);context.replay(ops,root);return root;
}
const texts=root=>root.childNodes.flatMap(child=>child.name==='text'?[child]:texts(child));
const annotation=(entityId=42,faceId='A0',shortLabel='角材42')=>({kind:'member-face',entityId,faceId,shortLabel});
const label=(t='角材42 A0',extra={})=>({op:'text',s:0,x:17,y:23,t,...extra});

test('native typed member metadata preserves the existing short label, full tooltip and pick identity',()=>{
  const [text]=texts(render([label(undefined,{annotation:annotation()})]));
  assert.equal(text.ownText,'角材42');assert.equal(text.dataset.timberId,'42');assert.equal(text.dataset.timberFace,'A0');
  assert.equal(text.attributes['data-label-full'],'角材42 A0');assert.equal(text.attributes['aria-label'],'角材42 A0');
  assert.equal(text.childNodes[0].name,'title');assert.equal(text.childNodes[0].textContent,'角材42 A0');
});
test('member identity survives translated labels, every face and the uint32 endpoint',()=>{
  for(const face of ['A0','A1','B0','B1','START','END']){
    const full='Beam alpha / '+face,[text]=texts(render([label(full,{annotation:annotation(0xffffffff,face,'構件甲')})]));
    assert.equal(text.ownText,'構件甲');assert.equal(text.dataset.timberId,'4294967295');assert.equal(text.dataset.timberFace,face);
    assert.equal(text.childNodes[0].textContent,full);
  }
});
test('a misleading Chinese label cannot override structural identity or the short display label',()=>{
  const [text]=texts(render([label('角材999 END',{annotation:annotation(7,'B1','custom caption')})]));
  assert.equal(text.ownText,'custom caption');assert.equal(text.dataset.timberId,'7');assert.equal(text.dataset.timberFace,'B1');
  assert.equal(text.attributes['aria-label'],'角材999 END');
});
test('plain labels stay plain even when their spelling resembles a member face',()=>{
  for(const full of ['角材42 A0','角材 9 END','ordinary label']){
    const [text]=texts(render([label(full)]));assert.equal(text.ownText,full);
    assert.equal(text.dataset.timberId,undefined);assert.equal(text.dataset.timberFace,undefined);assert.equal(text.childNodes.length,0);
  }
});
test('malformed annotations cannot manufacture selectable members',()=>{
  const cases=[null,{},[],{...annotation(),kind:'other'},{...annotation(),faceId:'SIDE'},
    ...[0,-1,1.5,0x100000000,'42',NaN].map(entityId=>({...annotation(),entityId})),
    {...annotation(),shortLabel:null},{...annotation(),shortLabel:42}];
  for(const value of cases){const [text]=texts(render([label('角材42 A0',{annotation:value})]));
    assert.equal(text.ownText,'角材42 A0');assert.equal(text.dataset.timberId,undefined);assert.equal(text.childNodes.length,0);}
});
test('replay keeps transforms, style, annotation order and operation input unchanged',()=>{
  const ops=[{op:'begin',tx:100,ty:200,viewIndex:2},label('member',{s:1,rot:90,annotation:annotation()}),
    {op:'rect',s:2,x0:1,y0:2,x1:11,y1:22},{op:'line',s:2,x0:0,y0:0,x1:3,y1:4},
    {op:'poly',s:2,p:['0,0','1,0','0,1']},{op:'end'},label('root label')];
  const before=structuredClone(ops),root=render(ops),geometry=root.childNodes[0],layers=root.childNodes.slice(1),[text]=texts(root);
  assert.deepEqual(ops,before);assert.deepEqual(geometry.childNodes.map(n=>n.name),['rect','line','polygon']);
  assert.deepEqual(geometry.childNodes[0].attributes,{x:'1',y:'2',width:'10',height:'20',fill:'#789','fill-opacity':'0.5',stroke:'#456','stroke-width':'2','vector-effect':'non-scaling-stroke'});
  assert.equal(layers[0].attributes.transform,'translate(100,200)');assert.equal(layers[0].dataset.viewIndex,'2');
  assert.equal(layers[1].childNodes[0].ownText,'root label');assert.equal(text.attributes.transform,'rotate(90 17 23)');
  assert.equal(text.attributes['data-fs0'],'15');assert.equal(text.attributes['font-weight'],'bold');
});
test('annotation strings are text, including angle brackets and quotes',()=>{
  const short='<script>caption</script>',full='"quoted" <member>';
  const [text]=texts(render([label(full,{annotation:annotation(5,'START',short)})]));
  assert.equal(text.ownText,short);assert.equal(text.childNodes.length,1);assert.equal(text.childNodes[0].name,'title');
  assert.equal(text.childNodes[0].ownText,full);assert.equal(text.attributes['dominant-baseline'],'middle');
});
