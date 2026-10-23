'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const application = require('../geometry-app/application.js');
const provider = application.woodworking;
const root = path.join(__dirname, '..');
const read = relative => fs.readFileSync(path.join(root, relative), 'utf8');
const plain = value => JSON.parse(JSON.stringify(value));

function browserComposition(loadTemplate = true) {
  const context = vm.createContext({});
  if (loadTemplate) vm.runInContext(read('geometry-templates/woodworking/frontend.js'), context);
  vm.runInContext(read('geometry-app/application.js'), context);
  return context;
}

test('the host fixes the same immutable woodworking provider in browser and Node', () => {
  const browser = browserComposition();
  assert.equal(browser.GeometryApplication.woodworking.id, provider.id);
  assert.deepEqual(plain(browser.GeometryApplication.woodworking.panel), plain(provider.panel));
  function frozen(value) {
    if (value && ['object', 'function'].includes(typeof value)) {
      assert.ok(Object.isFrozen(value), 'every template object and recipe is immutable');
      Object.values(value).forEach(frozen);
    }
  }
  frozen(application);
  assert.throws(() => { provider.section.A = 44; }, TypeError);
  assert.throws(() => { application.woodworking = {}; }, TypeError);
  assert.throws(() => vm.runInContext('"use strict"; GeometryApplication = {};', browser), /read only|readonly|Cannot assign/i);
});

test('missing fixed template refuses composition before any editor is started', () => {
  assert.throws(() => browserComposition(false), /缺少固定木工模板/);
});

test('new material recipes preserve panel suggestions and deliberately blank timber dimensions', () => {
  assert.deepEqual(provider.materialDraft('panel'), {mode:'new',base:null,name:'矽酸鈣板',type:'panel',
    width:'915',length:'1830',thickness:'6',A:'',B:'',brand:'',model:'',source:'',note:''});
  assert.deepEqual(provider.materialDraft('timber'), {mode:'new',base:null,name:'',type:'timber',
    width:'',length:'',thickness:'',A:'',B:'',brand:'',model:'',source:'',note:''});
});

test('editing a new draft never changes the fixed recipe or the next new draft', () => {
  const first=provider.materialDraft('panel');first.width='800';first.name='User choice';
  const second=provider.materialDraft('panel');
  assert.equal(second.width,'915');assert.equal(second.name,'矽酸鈣板');
  assert.equal(provider.panel.width,915);
  const member=provider.sectionMember('timber');member.A.value=80;
  assert.deepEqual(provider.sectionMember('timber'), {A:{kind:'literal',value:27},B:{kind:'literal',value:33},orientation:'A-u'});
});

test('section recipes retain orientation and source kinds instead of flattening them', () => {
  assert.deepEqual(provider.sectionMember('panel'), {panelSpec:'calcium-silicate-6',width:100,orientation:'thickness-v'});
  assert.deepEqual(provider.sectionMember('timber'), {A:{kind:'literal',value:27},B:{kind:'literal',value:33},orientation:'A-u'});
});

function newMaterialHarness(template = provider, allow = true) {
  const line=read('geometry-web/engineering-workspace.js').split(/\r?\n/).find(line=>line.startsWith('  function newMaterial('));
  assert.ok(line, 'actual material creation entry is present');
  const calls=[],state={material:{type:'panel',width:'saved value'},section:'apply'};
  const context=vm.createContext({state,GeometryApplication:{woodworking:template},
    allowReplaceDraft:()=>allow,changed:()=>calls.push('changed'),render:()=>calls.push('render'),
    $:()=>({focus:()=>calls.push('focus')})});
  vm.runInContext(line,context);
  return {state,calls,create:type=>context.newMaterial(type)};
}

test('the actual material creation entry gets its suggestions from the injected provider', () => {
  const seen=[];
  const h=newMaterialHarness({materialDraft(type){seen.push(type);return {type,width:'sentinel',name:'injected'};}});
  h.create('panel');assert.deepEqual(seen,['panel']);
  assert.equal(h.state.material.width,'sentinel');assert.equal(h.state.section,'materials');
  assert.deepEqual(h.calls,['changed','render','focus']);
});

test('declining draft replacement keeps saved input and never calls a creation recipe', () => {
  const h=newMaterialHarness({materialDraft(){assert.fail('declined draft must not request defaults');}},false);
  h.create('panel');assert.deepEqual(h.state.material,{type:'panel',width:'saved value'});
  assert.equal(h.state.section,'apply');assert.deepEqual(h.calls,[]);
});

test('the actual section new-member entry uses typed template sources', () => {
  const source=read('geometry-web/section-profile-workspace.js');
  const line=source.split(/\r?\n/).find(line=>line.startsWith('  function newItem('));
  assert.ok(line,'actual new-member entry is present');
  const state={profileId:5},seen=[];
  const context=vm.createContext({state,ReferenceWorkspace:{assertEditable(){}},guardSwitch(){},invalidate(){},
    idFor:()=>9,render(){},report(){},GeometryApplication:{woodworking:{sectionMember(kind){seen.push(kind);
      return {A:{kind:'literal',value:41},B:{kind:'literal',value:43},orientation:'A-u'};}}}});
  vm.runInContext(line,context);context.newItem('member');
  assert.deepEqual(seen,['timber']);
  assert.deepEqual(plain(state.draft),{id:9,profileId:5,kind:'timber',A:{kind:'literal',value:41},
    B:{kind:'literal',value:43},orientation:'A-u',u0:0,v0:0});
  assert.equal(state.dirty,true);
});

test('woodworking primary direction derives only from actual primary and boundary members', () => {
  const cases = [
    [[], {axis:null,conflict:false,src:'none'}],
    [[{role:'secondary',dir:'+u'},{role:'custom',dir:'+v'}], {axis:null,conflict:false,src:'none'}],
    [[{role:'primary',dir:'-v'},{role:'primary',dir:'+v'}], {axis:'v',conflict:false,src:'primary'}],
    [[{role:'boundary',dir:'+u'}], {axis:'v',conflict:false,src:'boundary'}],
    [[{role:'primary',dir:'+u'},{role:'boundary',dir:'-v'}], {axis:'u',conflict:false,src:'primary'}],
    [[{role:'primary',dir:'+u'},{role:'boundary',dir:'+u'}], {axis:'u',conflict:true,src:'primary'}],
    [[{role:'primary',dir:'+u'},{role:'primary',dir:'+v'}], {axis:null,conflict:true,src:'primary'}],
    [[{role:'boundary',dir:'+u'},{role:'boundary',dir:'+v'}], {axis:null,conflict:true,src:'none'}],
  ];
  for (const [members, expected] of cases) {
    const saved=plain(members);
    assert.deepEqual(provider.primaryAxisInfo(members), expected, JSON.stringify(members));
    assert.deepEqual(members,saved,'derivation must never mutate saved members');
  }
});

test('click-role policy distinguishes outer edges, reference lines and conflicting evidence', () => {
  for (const axis of [null,'u','v']) for (const kind of ['edge','line']) for (const direction of ['u','v']) {
    const expected=!axis?(kind==='edge'?'boundary':'primary'):
      direction===axis?'primary':kind==='edge'?'boundary':'secondary';
    assert.equal(provider.roleForClick({axis,conflict:false},kind,direction),expected);
    assert.equal(provider.roleForClick({axis,conflict:true},kind,direction),null);
  }
});

test('role controls preserve the custom-role exception and retain uncertain evidence', () => {
  for (const axis of ['u','v']) for (const direction of ['+u','-u','+v','-v']) {
    const options=provider.roleOptions({axis,conflict:false},direction);
    const disabled=options.filter(o=>o.disabled).map(o=>o.value);
    assert.deepEqual(disabled,direction.slice(-1)===axis?['boundary','secondary']:['primary']);
    assert.equal(options.find(o=>o.value==='custom').disabled,false);
  }
  for (const info of [{axis:null,conflict:false},{axis:'u',conflict:true}]) {
    assert.deepEqual(provider.roleOptions(info,'+u').map(o=>[o.value,o.label,o.disabled]),
      [['primary','主支',false],['boundary','邊框材',false],['secondary','副支',false],['custom','自訂角色',false]]);
  }
});

test('subgrid warnings preserve missing, conflicting and parallel actual-support evidence', () => {
  assert.equal(provider.subgridRoleWarning({axis:'u',conflict:false},'+v','secondary'),'');
  assert.equal(provider.subgridRoleWarning({axis:'u',conflict:false},'-u','secondary'),
    '此線平行於實際主支 u 方向，不能用副支 3；請明確改選合法角色。');
  assert.equal(provider.subgridRoleWarning({axis:null,conflict:false},'+v','secondary'),
    '尚未建立實際主支方向；請先放主支或邊界材，或明確改選其他合法角色。');
  assert.equal(provider.subgridRoleWarning({axis:null,conflict:true},'+v','secondary'),
    '面上主支方向有衝突，請先檢查既有角材。');
  assert.equal(provider.subgridRoleWarning({axis:null,conflict:true},'+v','custom'),'');
});

function hostFunction(name, next) {
  const source=read('geometry-web/app.js'),start=source.indexOf('function '+name+'(');
  assert.notEqual(start,-1,'actual host function exists: '+name);
  const end=source.indexOf(next,start+1);assert.ok(end>start,'actual host function end: '+name);
  return source.slice(start,end);
}

test('actual host placement controls consume injected policies without interpreting labels', () => {
  const members=[{role:'primary',dir:'+u'}],seen=[],info={axis:'u',conflict:false};
  const context=vm.createContext({fe:{timbers:members},GeometryApplication:{woodworking:{
    primaryAxisInfo(value){assert.equal(value,members);seen.push('axis');return info;},
    roleForClick(value,kind,dir){assert.equal(value,info);seen.push([kind,dir]);return 'custom';},
    subgridRoleWarning(value,dir,role){assert.equal(value,info);seen.push([dir,role]);return 'injected warning';},
    roleOptions(value,dir){assert.equal(value,info);seen.push(dir);return [{value:'custom',label:'主支線',disabled:true}];},
  }}});
  vm.runInContext(hostFunction('fePrimaryAxisInfo','function feTimberPrimaryAxis'),context);
  vm.runInContext(hostFunction('feTimberRoleForClick','/* 表單與直接點線'),context);
  vm.runInContext(hostFunction('feSubgridRoleWarning','const TB_ROLE_OPTS'),context);
  vm.runInContext(hostFunction('feTimberRoleOptionsHTML','/* 方向改變時重算 #tbRole'),context);
  assert.equal(context.feTimberRoleForClick(8,'edge','v'),'custom');
  assert.equal(context.feSubgridRoleWarning(8,'+u','secondary'),'injected warning');
  assert.equal(context.feTimberRoleOptionsHTML(8,'-u','custom'),
    '<option value="custom" disabled selected>主支線</option>');
  assert.deepEqual(seen,['axis',['edge','v'],'axis',['+u','secondary'],'axis','-u']);
});

test('actual material shortcut markup retains original values and accepts provider data', () => {
  const source=read('geometry-web/engineering-workspace.js');
  const start=source.indexOf('`<div class="ew-button-row">${GeometryApplication.woodworking.materialPresets');
  assert.ok(start>=0,'actual material shortcuts consume the template');
  const end=source.indexOf('</div><p class="ew-note">',start);
  assert.ok(end>start);
  const expression=source.slice(start,end)+'</div>`';
  const render=woodworking=>vm.runInNewContext(expression,{GeometryApplication:{woodworking}});
  assert.equal(render(provider),'<div class="ew-button-row"><button type="button" data-ew-preset="915,1830">915 × 1830</button><button type="button" data-ew-preset="910,1820">910 × 1820</button><button type="button" data-ew-thickness="6">厚 6</button><button type="button" data-ew-thickness="9">厚 9</button></div>');
  assert.equal(render({materialPresets:[{width:804,length:1608}],thicknessPresets:[12]}),
    '<div class="ew-button-row"><button type="button" data-ew-preset="804,1608">804 × 1608</button><button type="button" data-ew-thickness="12">厚 12</button></div>');
});

test('actual section kind switch requests its recipe while preserving identity and position', () => {
  const source=read('geometry-web/section-profile-workspace.js');
  const line=source.split(/\r?\n/).find(line=>line.includes("on('spMemberKind','change'"));
  assert.ok(line,'actual member-kind event binding');
  const callbacks={},seen=[],state={kind:'member'},d={id:8,profileId:2};
  const context=vm.createContext({state,d,bindSource(){},on:(id,event,fn)=>{callbacks[id]=fn;},
    $:()=>({value:'panel'}),number:id=>id==='spU'?17:23,changed(){},editor(){},
    GeometryApplication:{woodworking:{sectionMember(kind){seen.push(kind);return {panelSpec:'injected',width:86,orientation:'thickness-u'};}}}});
  vm.runInContext(line,context);callbacks.spMemberKind();
  assert.deepEqual(seen,['panel']);
  assert.deepEqual(plain(state.draft),{id:8,profileId:2,kind:'panel',u0:17,v0:23,
    panelSpec:'injected',width:86,orientation:'thickness-u'});
});

test('assembly creation preserves typed roles, directions and endpoint sources without sharing mutable defaults', () => {
  const rule={members:[{id:17},{id:23},{id:41}],joints:[
    {kind:'end-to-side',terminatedMember:23,targetMember:17,end:'start'},
    {kind:'end-to-side',terminatedMember:23,targetMember:41,end:'finish'}]};
  const before=plain(rule),members=provider.assemblyInstanceMembers(rule);
  assert.deepEqual(members,[
    {memberId:17,role:'primary',guideId:0,dir:'+v',depthSide:'+n',ends:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}},
    {memberId:23,role:'secondary',guideId:0,dir:'+u',depthSide:'+n',ends:{start:{kind:'member',memberId:17},finish:{kind:'member',memberId:41}}},
    {memberId:41,role:'primary',guideId:0,dir:'+v',depthSide:'+n',ends:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}},
  ]);
  members[0].ends.start.id=300;members[1].ends.finish.memberId=17;
  const next=provider.assemblyInstanceMembers(rule);
  assert.equal(next[0].ends.start.id,0);assert.equal(next[1].ends.finish.memberId,41);assert.deepEqual(rule,before);
});

test('assembly retargeting retains identities and the original secondary role constraints', () => {
  const members=[{memberId:17,role:'primary'},{memberId:23,role:'secondary'},{memberId:41,role:'primary'}];
  const rule={members:[{id:17},{id:23},{id:41}],joints:[
    {kind:'end-to-side',terminatedMember:23,targetMember:41,end:'start'},
    {kind:'end-to-side',terminatedMember:23,targetMember:17,end:'finish'}]};
  assert.equal(provider.canRetargetAssemblyInstance(members,rule),true);
  for(const change of [r=>r.members.pop(),r=>r.members[0].id=99,r=>r.joints.pop(),r=>r.joints[0].kind='ortho-split',r=>r.joints[0].terminatedMember=17]){
    const changed=plain(rule);change(changed);assert.equal(provider.canRetargetAssemblyInstance(members,changed),false);
  }
  assert.deepEqual(provider.assemblyInstanceEnd(rule,'start'),{kind:'member',memberId:41});
  assert.deepEqual(provider.assemblyInstanceEnd(rule,'finish'),{kind:'member',memberId:17});
  assert.throws(()=>provider.assemblyInstanceEnd({...rule,joints:rule.joints.slice(1)},'start'),/新版缺少副支端接來源/);
});
