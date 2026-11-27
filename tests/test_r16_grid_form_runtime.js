'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const {fixture} = require('./fixtures/reference_workspace_vm.cjs');
const P = require('../geometry-web/project-store.js');

test('R16GF_FOOTER_LANE measures real scrollbar widths without changing the lane left edge', () => {
  const source = fs.readFileSync(path.join(__dirname, '../geometry-web/grid-system-workspace.js'), 'utf8');
  const match = source.match(/  function syncFooterLane\(\) \{([\s\S]*?)\n  \}/);
  assert.ok(match, 'R16GF_FOOTER_LANE: shipped measurement helper is required');
  for (const [outer, inner, lane, height] of [[390,390,180,260],[680,665,180,286],[680,673,180,270],[1400,1400,360,80]]) {
    const properties = new Map();
    const layout = {offsetWidth:outer,clientWidth:inner};
    const footer = {getBoundingClientRect:()=>({height})};
    const dialog = {querySelector:selector=>selector === '.ig-layout' ? layout : footer,
      style:{setProperty:(key,value)=>properties.set(key,value)}};
    vm.runInNewContext(match[0]+'\nsyncFooterLane();', {dialog,Math});
    const gutter = Number.parseFloat(properties.get('--r16-grid-scrollbar'));
    assert.equal(gutter, outer-inner, 'R16GF_FOOTER_GUTTER: exact measured scrollbar width');
    assert.equal(properties.get('--r123h-grid-footer-height'), height+'px', 'R16GF_FOOTER_HEIGHT: real wrapped height');
    assert.equal(outer-gutter-(lane-gutter), outer-lane, 'R16GF_FOOTER_LEFT: canvas reservation unchanged');
    assert.equal(outer-gutter, inner, 'R16GF_FOOTER_RIGHT: inside the actual scrollport');
  }
});

test('R16GF_DRAFT_HISTORY: edit and explicit discard are two local steps with no World write', async () => {
  const {w,calls,env} = await fixture();
  const token = w.getProjectState().contextToken;
  const draft = {schema:P.Features.GRID_SCHEMA,draftId:'r16-source',kind:'source',intent:'create',
    baseRef:null,inputRefs:[],rawForm:Object.fromEntries(P.Features.sourceFields.map(key=>[key,'']))};
  draft.rawForm.igName='GridForm';
  w.setGridDraft(draft.draftId,draft,token);
  const original=JSON.stringify(w.readGridDrafts()), before=w.history.undo.length, frame=w.history.frame;
  const geometry=JSON.stringify([env.oc.faces,env.oc.bmap]);
  const edited=structuredClone(draft);edited.rawForm.igName='GridForm-draft';
  w.setGridDraft(draft.draftId,edited,token);
  const changed=JSON.stringify(w.readGridDrafts());
  w.setGridDraft(draft.draftId,null,token);
  assert.equal(w.history.undo.length,before+2,'R16GF_DRAFT_HISTORY: edit plus discard each records one local step');
  assert.equal(w.history.frame,frame,'R16GF_DRAFT_FRAME: no native history frame change');
  assert.equal(JSON.stringify([env.oc.faces,env.oc.bmap]),geometry,'R16GF_WORLD_UNCHANGED');
  assert.equal(calls.length,0,'R16GF_NATIVE_ZERO_CALLS');
  assert.equal(w.tryLocalHistory('line undo').ok,true);
  assert.equal(JSON.stringify(w.readGridDrafts()),changed,'R16GF_UNDO_DISCARD');
  assert.equal(w.tryLocalHistory('line undo').ok,true);
  assert.equal(JSON.stringify(w.readGridDrafts()),original,'R16GF_UNDO_EDIT');
  assert.equal(w.tryLocalHistory('line redo').ok,true);
  assert.equal(w.tryLocalHistory('line redo').ok,true);
  assert.equal(w.readGridDrafts().drafts.length,0,'R16GF_REDO_DISCARD');
  assert.equal(JSON.stringify([...w.history.frame.ids]),JSON.stringify([...frame.ids]),'R16GF_LOCAL_REDO_NATIVE_IDS');
  assert.equal(JSON.stringify([env.oc.faces,env.oc.bmap]),geometry,'R16GF_LOCAL_REDO_WORLD_UNCHANGED');
  assert.equal(calls.length,0);
});
