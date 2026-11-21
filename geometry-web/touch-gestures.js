/* R11 first slice: arbitrate trusted touch pointers before legacy canvas down.
   The adapter owns target identity, cancellation and existing tool operations.
   This controller never dispatches synthetic mouse/pointer events or commands. */
(function () {
  'use strict';
  const HOLD_MS = 500, RING_MS = 150, MOVE_PX = 8;
  let adapter = null, gesture = null, compatibilityPoint = null;
  const consumed = new Set(), expectedRelease = new Set();
  const stop = event => { event.preventDefault(); event.stopImmediatePropagation(); };
  const point = event => ({x:event.clientX,y:event.clientY});
  const remember = event => {
    const id = event.pointerId; compatibilityPoint = point(event);
    consumed.add(id);
    if (consumed.size > 64) consumed.delete(consumed.values().next().value);
  };
  function clearHold(g) {
    clearTimeout(g.ringTimer); clearTimeout(g.holdTimer);
    cancelAnimationFrame(g.ringFrame); g.ring?.remove(); g.ring = null;
  }
  function release(g) {
    for (const id of g.ids) if (adapter.surface.hasPointerCapture(id)) {
      // lostpointercapture may be delivered after releasePointerCapture returns.
      expectedRelease.add(id); adapter.surface.releasePointerCapture(id);
    }
  }
  function finish(g) {
    clearHold(g);
    if (gesture === g) gesture = null;
    release(g); adapter.clearPresentation();
  }
  function cancel() {
    const g = gesture; if (!g || g.phase === 'cancelled') return;
    const wasMenu = g.phase === 'menu';
    g.phase = 'cancelled'; clearHold(g);
    adapter.cancelSingle(g.pin);
    if (wasMenu) adapter.closeMenu();
    release(g); adapter.clearPresentation();
  }
  function sync() {
    const g = gesture;
    // Opening a menu may legitimately select its DOWN target. Its shell now
    // owns the action stamp; no pending tool operation remains in this phase.
    if (g && !['menu','cancelled'].includes(g.phase) && !adapter.current(g.pin)) cancel();
  }
  function ring(g) {
    if (gesture !== g || g.phase !== 'pending') return;
    if (!adapter.current(g.pin)) { cancel(); return; }
    const elapsed = performance.now() - g.started;
    if (elapsed < RING_MS) { g.ringTimer = setTimeout(() => ring(g), RING_MS - elapsed); return; }
    if (!g.ring) {
      g.ring = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      g.ring.classList.add('r11-press-ring'); g.ring.setAttribute('viewBox','0 0 56 56');
      g.ring.setAttribute('aria-hidden','true');
      g.ring.style.left = g.down.clientX + 'px'; g.ring.style.top = g.down.clientY + 'px';
      document.body.append(g.ring);
    }
    const progress = Math.min(1, elapsed / HOLD_MS);
    g.ring.dataset.progress = String(progress);
    g.ring.style.setProperty('--r11-press-progress', String(progress));
    g.ring.innerHTML = CursorV2.pressRing(28,28,progress);
    g.ringFrame = requestAnimationFrame(() => ring(g));
  }
  function hold(g) {
    if (gesture !== g || g.phase !== 'pending') return;
    const remaining = HOLD_MS - (performance.now() - g.started);
    if (remaining > 0) { g.holdTimer = setTimeout(() => hold(g), remaining); return; }
    if (!adapter.current(g.pin)) { cancel(); return; }
    clearHold(g); g.phase = 'menu';
    if (!adapter.openMenu(g.pin)) g.phase = 'cancelled';
  }
  function pair(g) {
    const a = g.points.get(g.pair[0]), b = g.points.get(g.pair[1]);
    if (!a || !b) return null;
    const p = adapter.localPoint((a.x+b.x)/2,(a.y+b.y)/2);
    return {x:p.x,y:p.y,distance:Math.hypot(b.x-a.x,b.y-a.y)};
  }
  function beginTwo(g) {
    clearHold(g);
    const wasMenu = g.phase === 'menu';
    g.phase = 'multi'; adapter.cancelSingle(g.pin); adapter.closeMenu();
    // A menu owns a new selection generation. Starting another tool from its
    // still-held finger would borrow that generation, so drain this sequence.
    if (wasMenu || !adapter.current(g.pin)) { g.phase = 'cancelled'; return; }
    g.pair = [...g.points.keys()].slice(0,2);
    g.camera = adapter.getCamera(); g.origin = pair(g);
    if (!g.origin || g.origin.distance === 0) g.phase = 'cancelled';
  }
  function down(event) {
    if (!adapter) return;
    if (event.pointerType !== 'touch') {
      // A real mouse/stylus keeps its immediate legacy path. Retire only the
      // pending touch operation before that input establishes a new selection.
      cancel(); return;
    }
    // Pointer IDs are reusable. A new touch on the menu/native controls must
    // not inherit the preceding canvas sequence's suppressed compatibility click.
    if (!gesture?.points.has(event.pointerId)) {
      consumed.delete(event.pointerId); expectedRelease.delete(event.pointerId);
      compatibilityPoint = null;
    }
    if (gesture) {
      const g = gesture; stop(event); remember(event);
      g.points.set(event.pointerId,point(event)); g.ids.add(event.pointerId);
      if (!adapter.contains(event)) { cancel(); return; }
      if (g.phase !== 'cancelled') adapter.surface.setPointerCapture(event.pointerId);
      if (g.points.size === 2 && !['multi','cancelled','draining'].includes(g.phase)) beginTwo(g);
      return;
    }
    if (event.isPrimary === false || !adapter.eligible(event)) return;
    adapter.closeMenu();
    const pin = adapter.captureDown(event); if (!pin) return;
    stop(event); remember(event);
    const g = gesture = {pin,down:event,started:performance.now(),phase:'pending',
      points:new Map([[event.pointerId,point(event)]]),ids:new Set([event.pointerId])};
    adapter.surface.setPointerCapture(event.pointerId);
    adapter.clearPresentation();
    if (pin.menu) {
      g.ringTimer = setTimeout(() => ring(g), RING_MS);
      g.holdTimer = setTimeout(() => hold(g), HOLD_MS);
    }
  }
  function move(event) {
    const g = gesture;
    if (!g || event.pointerType !== 'touch' || !g.points.has(event.pointerId)) return;
    stop(event); g.points.set(event.pointerId,point(event)); sync();
    if (g.phase === 'pending' && Math.hypot(event.clientX-g.down.clientX,event.clientY-g.down.clientY) > MOVE_PX) {
      clearHold(g); g.phase = 'single';
      if (adapter.beginSingle(g.pin,g.down,true) === false) { cancel(); return; }
    }
    if (g.phase === 'single') adapter.moveSingle(g.pin,event);
    else if (g.phase === 'multi') {
      const p = pair(g); if (!p) { g.phase = 'draining'; return; }
      const {zoom,x,y} = g.camera, z = Math.max(.02,Math.min(8,zoom*p.distance/g.origin.distance));
      adapter.setCamera({zoom:z,x:p.x-(g.origin.x-x)*z/zoom,y:p.y-(g.origin.y-y)*z/zoom});
    }
  }
  function up(event) {
    const g = gesture;
    if (!g || event.pointerType !== 'touch' || !g.points.has(event.pointerId)) return;
    stop(event); compatibilityPoint = point(event); sync();
    const phase = g.phase;
    g.points.delete(event.pointerId);
    if (phase === 'multi' && g.pair.includes(event.pointerId)) g.phase = 'draining';
    if (g.points.size) return;
    // Retire before the original single path changes selection/history or
    // navigates. Late ownership checks must not cancel its confirmed action.
    finish(g);
    try {
      if (phase === 'pending') {
        if (adapter.beginSingle(g.pin,g.down,false) !== false)
          Promise.resolve(adapter.endSingle(g.pin,event)).catch(adapter.onError);
      } else if (phase === 'single') Promise.resolve(adapter.endSingle(g.pin,event)).catch(adapter.onError);
    } catch (error) { adapter.onError(error); }
  }
  function pointerCancel(event) {
    const g = gesture;
    if (!g || event.pointerType !== 'touch' || !g.points.has(event.pointerId)) return;
    stop(event); cancel(); g.points.delete(event.pointerId);
    if (!g.points.size) finish(g);
  }
  function compatibility(event) {
    const owned = consumed.has(event.pointerId) ||
      (event.sourceCapabilities?.firesTouchEvents && (adapter?.contains(event) ||
        compatibilityPoint && event.clientX === compatibilityPoint.x && event.clientY === compatibilityPoint.y));
    if (owned && (event.pointerType === 'touch' || event.sourceCapabilities?.firesTouchEvents)) stop(event);
  }
  // Registered before app.js: its document-capture double click and later
  // window shortcuts cannot start a tool before touch arbitration completes.
  window.addEventListener('pointerdown',down,{capture:true,passive:false});
  window.addEventListener('pointermove',move,{capture:true,passive:false});
  window.addEventListener('pointerup',up,{capture:true,passive:false});
  window.addEventListener('pointercancel',pointerCancel,{capture:true,passive:false});
  window.addEventListener('lostpointercapture',event => {
    if (expectedRelease.delete(event.pointerId)) return;
    if (gesture?.points.has(event.pointerId)) cancel();
  },true);
  for (const type of ['mousedown','mouseup','click','dblclick','contextmenu'])
    window.addEventListener(type,compatibility,{capture:true,passive:false});
  window.addEventListener('keydown',event => {
    if (event.key !== 'Escape' || event.isComposing || !gesture || gesture.phase === 'cancelled') return;
    stop(event); cancel();
  },true);
  const interrupt = () => { const g = gesture; if (g) { cancel(); finish(g); } };
  window.addEventListener('blur',interrupt);
  window.addEventListener('resize',cancel);
  for (const type of ['wheel','scroll']) window.addEventListener(type,cancel,{capture:true,passive:true});
  document.addEventListener('visibilitychange',() => { if (document.hidden) interrupt(); });
  for (const type of ['geometry-definition-changed','project-info-changed','project-local-history'])
    window.addEventListener(type,sync);
  window.CanvasTouchGestures = {
    attach(value) {
      if (adapter) throw new Error('物件畫布觸控只能註冊一次');
      adapter = value;
      new MutationObserver(sync).observe(document.body,{subtree:true,attributes:true,attributeFilter:['hidden','class']});
    },
    cancel, sync
  };
})();
