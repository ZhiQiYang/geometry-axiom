// Keep ownership of a drag until its pointer ends or the view interrupts it.
export function createPanGesture({ onPan, onDraggingChange }) {
  let active = null;

  function cancel(pointerId) {
    if (!active || (pointerId !== undefined && pointerId !== active.pointerId)) return false;
    const previous = active;
    active = null;
    // Capture can already be gone after pointercancel, lostpointercapture or unmount.
    try {
      if (previous.target.hasPointerCapture(previous.pointerId)) previous.target.releasePointerCapture(previous.pointerId);
    } catch { /* The pointer or target was removed by the browser. */ }
    onDraggingChange(false);
    return true;
  }

  return {
    start(event, pan) {
      if (active || event.button !== 0 || event.isPrimary === false) return false;
      const target = event.currentTarget;
      try { target.setPointerCapture(event.pointerId); } catch { return false; }
      active = { pointerId: event.pointerId, target, startX: event.clientX, startY: event.clientY, x: pan.x, y: pan.y };
      onDraggingChange(true);
      return true;
    },
    move(event) {
      if (!active || event.pointerId !== active.pointerId) return false;
      // Recover when a mouse release happened while the window was inactive.
      if (event.pointerType === 'mouse' && event.buttons === 0) return cancel(event.pointerId);
      onPan({ x: active.x + event.clientX - active.startX, y: active.y + event.clientY - active.startY });
      return true;
    },
    end(event) { return cancel(event.pointerId); },
    cancel,
    owns(pointerId) { return active?.pointerId === pointerId; },
    isActive() { return active !== null; },
  };
}

export function keyboardPan(event, pan) {
  if (event.altKey || event.ctrlKey || event.metaKey || event.isComposing) return null;
  const step = event.shiftKey ? 50 : 10;
  switch (event.key) {
    case 'ArrowLeft': return { x: pan.x - step, y: pan.y };
    case 'ArrowRight': return { x: pan.x + step, y: pan.y };
    case 'ArrowUp': return { x: pan.x, y: pan.y - step };
    case 'ArrowDown': return { x: pan.x, y: pan.y + step };
    case 'Home': return { x: 0, y: 0 };
    default: return null;
  }
}
