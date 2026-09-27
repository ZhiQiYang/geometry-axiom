import test from 'node:test';
import assert from 'node:assert/strict';
import { createPanGesture, keyboardPan } from '../src/canvasGestures.js';

function fixture() {
  const capture = new Set();
  const pans = [];
  const dragging = [];
  const target = {
    setPointerCapture(id) { capture.add(id); },
    hasPointerCapture(id) { return capture.has(id); },
    releasePointerCapture(id) { capture.delete(id); },
  };
  const gesture = createPanGesture({ onPan: pan => pans.push(pan), onDraggingChange: value => dragging.push(value) });
  const pointer = (id, x, y, extra = {}) => ({ pointerId: id, clientX: x, clientY: y, currentTarget: target, button: 0, buttons: 1, pointerType: 'touch', isPrimary: true, ...extra });
  return { gesture, capture, pans, dragging, target, pointer };
}

test('a second finger cannot take over, move or release the first drag', () => {
  const f = fixture();
  assert.equal(f.gesture.start(f.pointer(1, 10, 20), { x: 30, y: -5 }), true);
  assert.equal(f.gesture.start(f.pointer(2, 200, 300), { x: 30, y: -5 }), false);
  assert.equal(f.gesture.move(f.pointer(2, 250, 350)), false);
  assert.equal(f.gesture.end(f.pointer(2, 250, 350)), false);
  f.gesture.move(f.pointer(1, 25, 50));
  assert.deepEqual(f.pans, [{ x: 45, y: 25 }]);
  assert.deepEqual([...f.capture], [1]);
  f.gesture.end(f.pointer(1, 25, 50));
  assert.deepEqual(f.dragging, [true, false]);
  assert.equal(f.capture.size, 0);
});

test('cancel, lost capture and interruption release ownership and allow the next drag', () => {
  for (const interruption of ['pointercancel', 'lostpointercapture', 'blur-or-mode-change']) {
    const f = fixture();
    f.gesture.start(f.pointer(1, 10, 20), { x: 0, y: 0 });
    if (interruption === 'lostpointercapture') f.capture.clear();
    if (interruption === 'blur-or-mode-change') f.gesture.cancel();
    else f.gesture.end(f.pointer(1, 10, 20));
    assert.equal(f.gesture.isActive(), false, interruption);
    assert.equal(f.capture.size, 0, interruption);
    assert.equal(f.gesture.move(f.pointer(1, 999, 999)), false, interruption);
    assert.equal(f.gesture.start(f.pointer(3, 100, 100), { x: 15, y: 25 }), true, interruption);
    f.gesture.move(f.pointer(3, 110, 105));
    assert.deepEqual(f.pans, [{ x: 25, y: 30 }], interruption);
  }
});

test('released mouse and unavailable capture never leave a stuck drag', () => {
  const f = fixture();
  f.gesture.start(f.pointer(1, 10, 20, { pointerType: 'mouse' }), { x: 0, y: 0 });
  f.gesture.move(f.pointer(1, 40, 50, { pointerType: 'mouse', buttons: 0 }));
  assert.equal(f.gesture.isActive(), false);
  assert.deepEqual(f.pans, []);
  f.target.setPointerCapture = () => { throw new Error('pointer is no longer active'); };
  assert.equal(f.gesture.start(f.pointer(2, 0, 0), { x: 0, y: 0 }), false);
  assert.equal(f.gesture.isActive(), false);
});

test('right clicks and nonprimary contacts do not start panning', () => {
  const f = fixture();
  assert.equal(f.gesture.start(f.pointer(1, 0, 0, { button: 2 }), { x: 0, y: 0 }), false);
  assert.equal(f.gesture.start(f.pointer(2, 0, 0, { isPrimary: false }), { x: 0, y: 0 }), false);
  assert.deepEqual(f.dragging, []);
});

test('keyboard gives fine and coarse movement without intercepting browser shortcuts', () => {
  const pan = { x: 35, y: -25 };
  assert.deepEqual(keyboardPan({ key: 'ArrowLeft' }, pan), { x: 25, y: -25 });
  assert.deepEqual(keyboardPan({ key: 'ArrowDown', shiftKey: true }, pan), { x: 35, y: 25 });
  assert.deepEqual(keyboardPan({ key: 'Home' }, pan), { x: 0, y: 0 });
  for (const modifier of ['altKey', 'ctrlKey', 'metaKey', 'isComposing']) assert.equal(keyboardPan({ key: 'ArrowRight', [modifier]: true }, pan), null);
  assert.equal(keyboardPan({ key: 'Tab' }, pan), null);
  assert.deepEqual(pan, { x: 35, y: -25 });
});
