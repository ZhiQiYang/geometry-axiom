import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { getLayout, SCENE } from './geometry';
import { createPanGesture, keyboardPan } from './canvasGestures';

const FALLBACK_COLORS = { background: '#f8fafc', grid: '#e4eaf3', border: '#11998b', face: 'rgba(20, 150, 132, .095)', baseline: '#929dad', draft: '#4654f5', child: '#b38944', text: '#44536f', dimension: '#aeb9cb', highlight: '#c68b2d', 'highlight-fill': 'rgba(217, 159, 56, .055)', 'badge-background': '#ffffff', 'badge-border': '#9da5ff' };
const visible = (value, primary, alias) => value?.[primary] !== false && (!alias || value?.[alias] !== false);

function canvasColors(canvas) {
  const styles = window.getComputedStyle(canvas);
  return Object.fromEntries(Object.entries(FALLBACK_COLORS).map(([name, fallback]) => [name, styles.getPropertyValue(`--canvas-${name}`).trim() || fallback]));
}

function drawSegment(ctx, points, toScreen) {
  const a = toScreen(points[0]);
  const b = toScreen(points[1]);
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
}

function label(ctx, text, x, y, color, size = 12) {
  ctx.fillStyle = color;
  ctx.font = `${size}px "Noto Sans TC", "Microsoft JhengHei", sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, x, y);
}

export function GeometryCanvas({ baseline, draft, visibility = {}, zoom = 1, showPreview = true, showExisting = true, showBackground = true, gridSize = 50, faceName = '客廳天花', highlight = false, hasSubgrid = true, onPoint, panMode = false, onZoom, resetKey = 0 }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(null);
  const transform = useRef(null);
  const helpId = useId();
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setDragging] = useState(false);
  const gesture = useMemo(() => createPanGesture({ onPan: setPan, onDraggingChange: setDragging }), []);
  const before = useMemo(() => getLayout(baseline, { hasSubgrid }), [baseline, hasSubgrid]);
  const after = useMemo(() => getLayout(draft, { hasSubgrid }), [draft, hasSubgrid]);

  useEffect(() => {
    const node = frameRef.current;
    if (!node) return undefined;
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setSize({ width, height });
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  // Returning to fit view restores the original centre after a pan.
  useEffect(() => { if (zoom === 1) setPan({ x: 0, y: 0 }); }, [zoom, resetKey]);

  // Changes to the view must not leave a gesture tied to an old origin.
  useEffect(() => { gesture.cancel(); }, [gesture, panMode, zoom, resetKey, faceName]);
  useEffect(() => {
    const cancel = () => { gesture.cancel(); };
    const visibilityChanged = () => { if (document.hidden) gesture.cancel(); };
    window.addEventListener('blur', cancel);
    document.addEventListener('visibilitychange', visibilityChanged);
    return () => {
      window.removeEventListener('blur', cancel);
      document.removeEventListener('visibilitychange', visibilityChanged);
      gesture.cancel();
    };
  }, [gesture]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !size.width || !size.height) return;
    const ctx = canvas.getContext('2d');
    const colors = canvasColors(canvas);
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(size.width * dpr);
    canvas.height = Math.round(size.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const { width, height } = size;
    ctx.fillStyle = colors.background; ctx.fillRect(0, 0, width, height);
    const padding = { left: width < 500 ? 62 : 70, right: 28, top: height < 600 ? 84 : 107, bottom: height < 600 ? 110 : 170 };
    const fit = Math.max(.015, Math.min((width - padding.left - padding.right) / SCENE.width, (height - padding.top - padding.bottom) / SCENE.height));
    const scale = fit * zoom;
    const ox = padding.left + (width - padding.left - padding.right - SCENE.width * scale) / 2 + pan.x;
    const oy = padding.top + (height - padding.top - padding.bottom - SCENE.height * scale) / 2 + pan.y;
    const point = ([u, v]) => [ox + u * scale, oy + v * scale];
    transform.current = { ox, oy, scale };

    // Viewport graph paper is a drawing aid; dimensions below remain millimetres.
    const baseStep = (Number.isFinite(gridSize) && gridSize > 0 ? gridSize : 50) * scale;
    const step = baseStep * Math.max(1, Math.ceil(24 / baseStep));
    ctx.setLineDash([]);
    if (showBackground) {
      ctx.strokeStyle = colors.grid; ctx.lineWidth = .7;
      ctx.beginPath();
      for (let x = ((ox % step) + step) % step; x <= width; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, height); }
      for (let y = ((oy % step) + step) % step; y <= height; y += step) { ctx.moveTo(0, y); ctx.lineTo(width, y); }
      ctx.stroke();
    }

    const outer = visible(visibility, 'surface', 'outer');
    const hole = visible(visibility, 'hole');
    const main = visible(visibility, 'main', 'grid');
    const child = visible(visibility, 'subgrid', 'child') && hasSubgrid;
    const x1 = ox + SCENE.width * scale;
    const y1 = oy + SCENE.height * scale;
    const [hu0, hv0, hu1, hv1] = SCENE.hole;
    const [hx0, hy0] = point([hu0, hv0]);
    const [hx1, hy1] = point([hu1, hv1]);

    if (outer) {
      ctx.beginPath();
      ctx.rect(ox, oy, x1 - ox, y1 - oy);
      ctx.rect(hx0, hy0, hx1 - hx0, hy1 - hy0);
      ctx.fillStyle = colors.face; ctx.fill('evenodd');
      ctx.strokeStyle = colors.border; ctx.lineWidth = 1.35;
      ctx.strokeRect(ox, oy, x1 - ox, y1 - oy);
    }

    if (main) {
      if (showExisting) {
        ctx.strokeStyle = colors.baseline; ctx.lineWidth = 1; ctx.setLineDash([3, 4]);
        before.mainSegments.forEach(segment => drawSegment(ctx, segment.points, point));
      }
      if (showPreview) {
        ctx.strokeStyle = colors.draft; ctx.lineWidth = 1.65; ctx.setLineDash([7, 5]);
        after.mainSegments.forEach(segment => drawSegment(ctx, segment.points, point));
      }
    }
    if (child && ((showExisting && before.child) || (showPreview && after.child))) {
      if (showExisting && before.child) {
        ctx.strokeStyle = colors.child; ctx.lineWidth = highlight ? 2 : 1.2; ctx.setLineDash([2, 4]);
        before.child.segments.forEach(segment => drawSegment(ctx, segment.points, point));
      }
      const box = (showPreview ? after.child : before.child)?.bounds ?? before.child?.bounds;
      if (highlight || (showPreview && after.child && !after.child.valid)) {
        const [bx, by] = point([box.u[0], box.v[0]]);
        const [ex, ey] = point([box.u[1], box.v[1]]);
        ctx.strokeStyle = colors.highlight; ctx.lineWidth = 1.2; ctx.setLineDash([5, 4]);
        ctx.strokeRect(bx, by, ex - bx, ey - by);
        ctx.save();
        ctx.beginPath(); ctx.rect(ox, oy, x1 - ox, y1 - oy); ctx.rect(hx0, hy0, hx1 - hx0, hy1 - hy0); ctx.clip('evenodd');
        ctx.fillStyle = colors['highlight-fill']; ctx.fillRect(bx, by, ex - bx, ey - by);
        ctx.restore();
      }
      if (showPreview && after.child?.valid) {
        ctx.strokeStyle = colors.child; ctx.lineWidth = 1.2; ctx.setLineDash([2, 4]);
        after.child.segments.forEach(segment => drawSegment(ctx, segment.points, point));
      }
    }
    ctx.setLineDash([]);
    if (hole) {
      ctx.strokeStyle = colors.border; ctx.lineWidth = 1.35;
      ctx.strokeRect(hx0, hy0, hx1 - hx0, hy1 - hy0);
    }

    const handle = (x, y) => {
      ctx.beginPath(); ctx.arc(x, y, 4.4, 0, Math.PI * 2);
      ctx.fillStyle = colors.background; ctx.fill();
      ctx.strokeStyle = colors.border; ctx.lineWidth = 1.4; ctx.stroke();
    };
    if (outer) [[ox, oy], [x1, oy], [ox, y1], [x1, y1]].forEach(([x, y]) => handle(x, y));
    if (hole) [[hx0, hy0], [hx1, hy0], [hx0, hy1], [hx1, hy1]].forEach(([x, y]) => handle(x, y));

    if (outer) {
      ctx.strokeStyle = colors.dimension; ctx.lineWidth = 1;
      const top = oy - 23; const left = ox - 24;
      ctx.beginPath();
      ctx.moveTo(ox, top - 7); ctx.lineTo(ox, top + 8); ctx.moveTo(x1, top - 7); ctx.lineTo(x1, top + 8);
      ctx.moveTo(ox, top); ctx.lineTo(x1, top);
      ctx.moveTo(ox + 5, top - 4); ctx.lineTo(ox, top); ctx.lineTo(ox + 5, top + 4);
      ctx.moveTo(x1 - 5, top - 4); ctx.lineTo(x1, top); ctx.lineTo(x1 - 5, top + 4);
      ctx.moveTo(left - 7, oy); ctx.lineTo(left + 8, oy); ctx.moveTo(left - 7, y1); ctx.lineTo(left + 8, y1);
      ctx.moveTo(left, oy); ctx.lineTo(left, y1);
      ctx.moveTo(left - 4, oy + 5); ctx.lineTo(left, oy); ctx.lineTo(left + 4, oy + 5);
      ctx.moveTo(left - 4, y1 - 5); ctx.lineTo(left, y1); ctx.lineTo(left + 4, y1 - 5);
      ctx.stroke();
      label(ctx, '4000', (ox + x1) / 2, top - 12, colors.text);
      label(ctx, '3000', left - 16, (oy + y1) / 2, colors.text);
    }
    if (showPreview && main && after.u.length) {
      const bx = Math.min(width - 70, Math.max(68, point([after.u[0], 0])[0]));
      const by = oy + Math.min(70, (y1 - oy) * .18);
      ctx.fillStyle = colors['badge-background']; ctx.strokeStyle = colors['badge-border']; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.roundRect(bx - 39, by - 12, 78, 25, 7); ctx.fill(); ctx.stroke();
      label(ctx, `縫寬 ${draft.gap} mm`, bx, by + 1, colors.draft, 11);
    }
  }, [before, after, size, zoom, pan, visibility, showPreview, showExisting, showBackground, gridSize, highlight, hasSubgrid, draft.gap]);

  function handleMove(event) {
    if (gesture.isActive() && !gesture.owns(event.pointerId)) return;
    const t = transform.current;
    const rect = event.currentTarget.getBoundingClientRect();
    gesture.move(event);
    if (t) onPoint?.({ x: Math.round((event.clientX - rect.left - t.ox) / t.scale), y: Math.round((event.clientY - rect.top - t.oy) / t.scale) });
  }
  function handleKeyDown(event) {
    if (event.key === 'Escape') { gesture.cancel(); return; }
    if (!keyboardPan(event, pan)) return;
    event.preventDefault();
    gesture.cancel();
    setPan(previous => keyboardPan(event, previous));
  }

  return <div ref={frameRef} className="geometry-canvas" style={{ width: '100%', height: '100%', minHeight: 260, position: 'relative' }}>
    <canvas ref={canvasRef} tabIndex={0} role="group" aria-roledescription="互動畫布" aria-describedby={helpId}
      aria-label={`${faceName}網格示範，4000 × 3000 毫米；含一個 500 × 500 毫米開口。灰色為現有格線、藍色為預覽、琥珀色為子網格。`}
      data-pan-x={pan.x} data-pan-y={pan.y} data-dragging={isDragging} data-zoom={zoom}
      style={{ display: 'block', width: '100%', height: '100%', touchAction: panMode ? 'none' : 'pan-y', cursor: panMode ? (isDragging ? 'grabbing' : 'grab') : 'crosshair' }}
      onPointerMove={handleMove} onPointerDown={event => {
        if (!panMode) return;
        if (gesture.start(event, pan)) {
          event.preventDefault();
          event.currentTarget.focus({ preventScroll: true });
        }
      }} onPointerUp={gesture.end} onPointerCancel={gesture.end} onLostPointerCapture={gesture.end}
      onBlur={() => gesture.cancel()} onKeyDown={handleKeyDown}
      onWheel={event => {
        if (event.ctrlKey || !onZoom) return;
        onZoom(Math.max(.5, Math.min(2.5, zoom * (event.deltaY < 0 ? 1.08 : .92))));
      }} />
    <p id={helpId} className="canvas-keyboard-help"><span className="canvas-keyboard-hint">方向鍵微移 · Shift 加快 · Home 回到中央</span><span className="canvas-touch-hint">{panMode ? '平移已開啟：單指拖動畫布' : '開啟「平移」即可拖動畫布'}</span></p>
    <span className="sr-only">現有主網格 u 軸 {before.u.length} 條、v 軸 {before.v.length} 條。{hasSubgrid ? '包含一個局部子網格，u 軸三等分。' : '本面沒有子網格。'}{showPreview && after.errors.map(error => error.message).join(' ')}</span>
  </div>;
}
