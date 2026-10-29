const {test}=require('node:test'),assert=require('node:assert/strict');
const Plan=require('../geometry-web/cutting-plan.js');

// 執行實際 open/renderPlan；這是輕量 DOM 契約測試，不冒充真瀏覽器收據。
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.value='';this._text='';this.ids={};}
 append(...items){this.children.push(...items);}
 replaceChildren(...items){this.children=items;this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join('');}
 set innerHTML(value){this.children=[];for(const match of value.matchAll(/id="([^"]+)"/g)){const node=new Element('div');this.ids[match[1]]=node;this.children.push(node);}if(this.ids.cuttingUnit)this.ids.cuttingUnit.value='mm';if(this.ids.cuttingOrder)this.ids.cuttingOrder.value='id';}
 querySelector(selector){return this.ids[selector.slice(1)];}
 setAttribute(){} addEventListener(){} showModal(){} remove(){} close(){}
}
const refs=lengths=>({ok:true,sourceFingerprint:'a'.repeat(64),engineeringSources:[],timbers:lengths.map((L,i)=>({id:i+1,role:'primary',geometry:{surface:1,A:27,B:33,length:L,dir:'+v',side:'+n',origin:[0,0,0],axes:[[0,1,0],[1,0,0],[0,0,1]]}}))});
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'試用料',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
async function view(lengths,s,check){
 const r=refs(lengths),state={contextToken:'R354-04',revision:17,dirty:false},context={dirty:false},history={undo:[],redo:[]};
 const before=JSON.stringify({r,s,state,context,history}),prior=global.document;
 global.document={body:new Element('body'),createElement:tag=>new Element(tag),createTextNode:text=>String(text)};
 delete require.cache[require.resolve('../geometry-web/cutting-workspace.js')];
 const Workspace=require('../geometry-web/cutting-workspace.js');
 try{
  const session=Workspace.open({workspace:{getProjectState:()=>state,context:()=>context,readFeatureAttachment:()=>s,setFeatureAttachment:()=>assert.fail('唯讀操作不得保存設定'),history},references:async()=>r,scope:{surface:1,ids:null}});
  const dialog=document.body.children[0],control=id=>dialog.querySelector('#'+id);
  await control('cuttingCalculate').onclick();assert.match(control('cuttingStatus').textContent,/^COMPLETE/);
  const planBefore=JSON.stringify(session.plan);assert.equal(Plan.verify(session.plan),true);
  await check({control,text:()=>control('cuttingPlan').textContent,plan:session.plan});
  assert.equal(JSON.stringify(session.plan),planBefore,'顯示單位與排序不得改寫方案');
  assert.equal(JSON.stringify({r,s,state,context,history}),before,'求值與顯示不得改 World、設定、dirty、revision 或 history');
 }finally{global.document=prior;delete require.cache[require.resolve('../geometry-web/cutting-workspace.js')];}
}
test('R354-04 T1 畫面彙總耗損及兩類剩料；mm/cm 與排序只改顯示',async()=>view([2560,2560,890,890,890,876],settings(),async({control,text})=>{
 assert.match(text(),/件間及末刀耗損：18 mm/);assert.match(text(),/實際端修整耗損：15 mm/);
 assert.match(text(),/可留用剩料：1 段，實長 1859 mm，可用 1854 mm/);
 assert.match(text(),/廢料：2 段，實長 350 mm，可用 340 mm/);
 const mm=text();control('cuttingOrder').value='length';control('cuttingOrder').onchange();
 assert.match(text(),/件間及末刀耗損：18 mm/);assert.match(text(),/廢料：2 段，實長 350 mm，可用 340 mm/);
 control('cuttingUnit').value='cm';control('cuttingUnit').onchange();
 assert.match(text(),/件間及末刀耗損：1\.8 cm/);assert.match(text(),/實際端修整耗損：1\.5 cm/);
 assert.match(text(),/可留用剩料：1 段，實長 185\.9 cm，可用 185\.4 cm/);
 assert.match(text(),/廢料：2 段，實長 35 cm，可用 34 cm/);
 control('cuttingUnit').value='mm';control('cuttingOrder').value='id';control('cuttingUnit').onchange();assert.equal(text(),mm);
}));
test('R354-04 已用與未用宣告餘料分開，未執行尾修整不重計',async()=>{
 const s=settings();s.remnants=[{key:1,stockType:1,length:1000,headTrim:9,tailTrim:5},{key:2,stockType:1,length:600,headTrim:7,tailTrim:5}];s.nextRemnantKey=3;
 await view([500],s,async({text})=>{
  assert.match(text(),/新料需購入 0 支/);assert.match(text(),/已用宣告餘料：R2/);assert.match(text(),/未使用宣告餘料：R1/);
  assert.match(text(),/件間及末刀耗損：3 mm/);assert.match(text(),/實際端修整耗損：7 mm/);
  assert.match(text(),/可留用剩料：0 段，實長 0 mm，可用 0 mm/);assert.match(text(),/廢料：1 段，實長 90 mm，可用 85 mm/);
 });
});
test('R354-04 恰到修整線：兩端修整互斥於鋸縫且無剩料',async()=>view([3626],settings(),async({text})=>{
 assert.match(text(),/件間及末刀耗損：0 mm/);assert.match(text(),/實際端修整耗損：10 mm/);
 assert.match(text(),/可留用剩料：0 段，實長 0 mm，可用 0 mm/);assert.match(text(),/廢料：0 段，實長 0 mm，可用 0 mm/);
 assert.match(text(),/已用宣告餘料：無/);assert.match(text(),/未使用宣告餘料：無/);
}));
