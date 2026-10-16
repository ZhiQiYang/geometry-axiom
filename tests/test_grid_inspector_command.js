'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {serialize}=require('./fixtures/grid_inspector_command.cjs');
const repeat=(stagger,refs)=>({source:'repeat',phase:0,step:600,...(stagger===undefined?{}:{stagger}),...(refs?{parameterRefs:refs}:{})});
const panel=(stagger,refs)=>({source:'repeat-panel',panel:400,gap:5,anchor:-100,...(stagger===undefined?{}:{stagger}),...(refs?{parameterRefs:refs}:{})});
const ref=(fieldId)=>({parameterId:901,fieldId});
const cases=[
  ['u repeat positive',repeat(400),repeat(),'u repeat 0 600 stagger 400 v repeat 0 600'],
  ['v repeat negative',repeat(),repeat(-400),'u repeat 0 600 v repeat 0 600 stagger -400'],
  ['both mixed direct',repeat(-400),panel(200),'u repeat 0 600 stagger -400 v repeat-panel 400 gap 5 from -100 stagger 200'],
  ['u panel parameter',panel(400,{stagger:ref(1)}),repeat(),'u repeat-panel 400 gap 5 from -100 stagger param:901:1 v repeat 0 600'],
  ['v panel parameter negative',repeat(),panel(-400,{stagger:ref(2)}),'u repeat 0 600 v repeat-panel 400 gap 5 from -100 stagger param:901:2'],
  ['both parameter axes',panel(400,{stagger:ref(1),panel:ref(3),gap:ref(4),anchor:ref(5)}),repeat(-400,{stagger:ref(2),phase:ref(6),step:ref(7)}),'u repeat-panel param:901:3 gap param:901:4 from param:901:5 stagger param:901:1 v repeat param:901:6 param:901:7 stagger param:901:2'],
  ['absent remains absent',repeat(),panel(),'u repeat 0 600 v repeat-panel 400 gap 5 from -100'],
  ['single-axis source remains single-axis',repeat(),{source:'none'},'u repeat 0 600 v none'],
];
for(const [label,uDefinition,vDefinition,axes] of cases)test('rename retains complete sources: '+label,async()=>{
  const object={id:7,name:'Before',mainAlong:'v',uDefinition,vDefinition},before=structuredClone(object);
  assert.equal(await serialize(object,'改名'),`grid-system 7 name-hex e694b9e5908d main-along v ${axes}`);
  assert.deepEqual(object,before,'serialization cannot mutate the selected object');
});
test('editing a direct pitch still preserves unedited stagger references',async()=>{
  assert.equal(await serialize({id:0,mainAlong:null,uDefinition:repeat(400,{stagger:ref(1)}),vDefinition:repeat(-400)},'A',{giUStep:'900'}),
    'grid-system 0 name-hex 41 main-along none u repeat 0 900 stagger param:901:1 v repeat 0 600 stagger -400');
});
