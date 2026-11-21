'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '../..');

// R396: these checks execute the precise source expressions, not fabricated
// copies of the implementation. They are an independent unit-level gate;
// they do not replace the canonical two-shard browser receipt.
test('R396_FRESH_CHILD_NEVER_INHERITS_CAPTURE_SHARD', () => {
  const source = fs.readFileSync(path.join(ROOT,'geometry-web/timber_reuse_test.js'),'utf8');
  const begin = source.indexOf('const env={...process.env};for(');
  assert.ok(begin >= 0, 'R396_FRESH_CHILD_ENV_ANCHOR');
  const end = source.indexOf('delete env[name];', begin);
  assert.ok(end > begin, 'R396_FRESH_CHILD_DELETE_ANCHOR');
  const expression = source.slice(begin, end + 'delete env[name];'.length);
  const sanitize = new Function('parent',
    'const process={env:parent};' + expression + '\nreturn env;');
  const child = sanitize({GEOMETRY_CDP_CAPTURE_P1161:'1', GEOMETRY_CDP_SHARD:'2/2',
    GEOMETRY_TEST_URL:'http://127.0.0.1:18839/',GEOMETRY_FEEDBACK_DIR:'/tmp/example',
    GEOMETRY_WORKSPACE_CONTEXT_MENU_ONLY:'1',GEOMETRY_WORKSPACE_CONTEXT_MENU_CASES:'W12'});
  assert.equal(Object.hasOwn(child,'GEOMETRY_CDP_CAPTURE_P1161'),false,
    'R396_FRESH_CHILD_CAPTURE_FLAG_LEAK: child loses shard but must also lose capture');
  assert.equal(Object.hasOwn(child,'GEOMETRY_CDP_SHARD'),false);
  assert.equal(Object.hasOwn(child,'GEOMETRY_WORKSPACE_CONTEXT_MENU_ONLY'),false);
  assert.equal(Object.hasOwn(child,'GEOMETRY_WORKSPACE_CONTEXT_MENU_CASES'),false);
  assert.equal(child.GEOMETRY_TEST_URL,'http://127.0.0.1:18839/');
});

test('R396_KEYBOARD_ENTRY_HANDLED_BEFORE_SYNCHRONOUS_HIDE', () => {
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/view-context-menu.js'),'utf8');
  const anchor=source.indexOf('if (event.button === 2) keyboardEntry = null;');
  assert.ok(anchor >= 0,'R396_KEYBOARD_HANDLER_ANCHOR');
  const end=source.indexOf("      attempt(svg,event.target,!event.clientX",anchor);
  assert.ok(end > anchor,'R396_KEYBOARD_POINTER_FALLBACK_ANCHOR');
  const handler=source.slice(anchor,end);
  const exercise=new Function('event','alreadyHandled',`let keyboardEntry={handled:alreadyHandled,target:'canvas'};
    let calls=0;function attempt(){calls++;keyboardEntry=null;}
    const svg='canvas';function handle(){${handler}}
    handle();return {calls,keyboardEntry};`);
  let result;
  assert.doesNotThrow(()=>{result=exercise({button:-1},false);},
    'R396_KEYBOARD_REENTRANT_HIDE: openEntry synchronously clears keyboardEntry');
  assert.equal(result.calls,1,'R396_KEYBOARD_SINGLE_MENU_ENTRY');
  assert.equal(result.keyboardEntry,null);
  assert.equal(exercise({button:-1},true).calls,0, 'R396_KEYBOARD_NO_DUPLICATE_WHEN_ALREADY_HANDLED');
});
