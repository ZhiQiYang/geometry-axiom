/* Orthographic viewer for the actual geometry-model-package/1 mesh.
 * Presentation only: never reconstructs or substitutes source geometry.
 * Browser: GeometryModelViewer.create(canvas).setObjects(package.derived.objects).
 */
(function (global, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (global) global.GeometryModelViewer = api;
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';

  const VIEWS = {
    iso: { yaw: -Math.PI / 4, pitch: Math.atan(1 / Math.sqrt(2)) },
    top: { yaw: 0, pitch: Math.PI / 2 },
    bottom: { yaw: 0, pitch: -Math.PI / 2 },
    front: { yaw: 0, pitch: 0 }
  };
  const PALETTE = ['#78cbb6', '#eab976', '#81abe5', '#cf9ace', '#a9c879'];
  const clamp = (value, lo, hi) => Math.min(hi, Math.max(lo, value));
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const sub = (a, b) => a.map((value, i) => value - b[i]);
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

  // Screen Y points down; world +Z always points up except in an exact plan view.
  // Positive depth is nearer the observer, so paint in ascending depth order.
  function project(point, yaw, pitch) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    return [
      point[0] * cy + point[1] * sy,
      point[0] * sy * sp - point[1] * cy * sp - point[2] * cp,
      point[0] * sy * cp - point[1] * cy * cp + point[2] * sp
    ];
  }

  // A plan view looks along world -Z (top) or +Z (bottom). Local u/v are
  // mapped through the saved placement frame before choosing a screen axis.
  function projectPlanPoint(point, frame, view) {
    if (!['top', 'bottom'].includes(view)) throw new TypeError('平面檢視方向必須是 top 或 bottom。');
    if (!Array.isArray(point) || point.length !== 2 || !point.every(Number.isSafeInteger) ||
        !frame || !['origin', 'u', 'v'].every(key => Array.isArray(frame[key]) && frame[key].length === 3 && frame[key].every(Number.isSafeInteger))) {
      throw new TypeError('平面預覽需要完整承載面框架與局部整數座標。');
    }
    const world = frame.origin.map((value, axis) => value + point[0] * frame.u[axis] + point[1] * frame.v[axis]);
    return project(world, VIEWS[view].yaw, VIEWS[view].pitch);
  }

  // Assemble display layers from verified packages without changing any saved
  // mesh. The roof switch belongs only to the space shell, never to materials.
  function spacePreviewObjects(result, visibility = {}) {
    const objects=[],top=result.summary?.top;
    if(visibility.space!==false)for(const object of result.space?.derived?.objects||[]) {
      const mesh={...object,color:'#55879a',opacity:0.26,label:'空間邊界'};
      if(!visibility.roof&&typeof top==='number')mesh.triangles=object.triangles.filter(triangle=>!triangle.every(i=>object.vertices_mm[i][2]===top));
      if(mesh.triangles.length)objects.push(mesh);
    }
    if(visibility.walls!==false)for(const object of result.walls?.derived?.objects||[])objects.push({...object,color:'#ced9db',opacity:0.96,label:'材料牆'});
    if(visibility.timbers!==false)for(const object of result.timbers?.derived?.objects||[])objects.push({...object,color:'#bd843d',opacity:1,label:'角材結構'});
    return objects;
  }

  function rgb(value, fallback) {
    const match = /^#([a-f\d]{3}|[a-f\d]{6})$/i.exec(typeof value === 'string' ? value : '');
    if (!match) return rgb(fallback, '#78cbb6');
    const hex = match[1].length === 3 ? match[1].split('').map(x => x + x).join('') : match[1];
    return [0, 2, 4].map(start => parseInt(hex.slice(start, start + 2), 16));
  }

  function prepareObjects(input) {
    if (!Array.isArray(input)) throw new TypeError('3D 檢視器需要網格物件陣列。');
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    const objects = [];
    let triangleCount = 0;
    input.forEach((object, index) => {
      if (!object || !Array.isArray(object.vertices_mm) || !Array.isArray(object.triangles)) {
        throw new TypeError('3D 網格缺少 vertices_mm 或 triangles。');
      }
      const vertices = object.vertices_mm.map(vertex => {
        if (!Array.isArray(vertex) || vertex.length !== 3 || !vertex.every(Number.isSafeInteger)) {
          throw new TypeError('3D 頂點必須是三個安全整數 mm。');
        }
        return vertex.slice();
      });
      const edgeMap = new Map();
      const triangles = object.triangles.map(indices => {
        if (!Array.isArray(indices) || indices.length !== 3 || !indices.every(i => Number.isInteger(i) && i >= 0 && i < vertices.length)) {
          throw new TypeError('3D 三角形引用了不存在的頂點。');
        }
        const points = indices.map(i => vertices[i]);
        const normal = cross(sub(points[1], points[0]), sub(points[2], points[0]));
        const length = Math.hypot(...normal);
        if (!length) throw new TypeError('3D 網格含退化三角形。');
        const triangle = { indices: indices.slice(), normal: normal.map(v => v / length), edges: [] };
        points.forEach(point => point.forEach((v, axis) => {
          min[axis] = Math.min(min[axis], v);
          max[axis] = Math.max(max[axis], v);
        }));
        for (let side = 0; side < 3; side++) {
          const a = indices[side], b = indices[(side + 1) % 3];
          const key = a < b ? `${a}:${b}` : `${b}:${a}`;
          if (!edgeMap.has(key)) edgeMap.set(key, []);
          edgeMap.get(key).push(triangle);
          triangle.edges.push(key);
        }
        return triangle;
      });
      if (!triangles.length) return;
      // Keep real boundary/crease edges, omit coplanar triangulation diagonals.
      const featureEdges = new Set();
      edgeMap.forEach((uses, key) => {
        if (uses.length !== 2 || dot(uses[0].normal, uses[1].normal) < 0.999999) featureEdges.add(key);
      });
      objects.push({
        vertices, triangles, featureEdges,
        color: rgb(object.color, PALETTE[index % PALETTE.length]),
        opacity: Number.isFinite(object.opacity) ? clamp(object.opacity, 0, 1) : object.role === 'enclosure' ? 0.28 : 0.9,
        label: typeof object.label === 'string' ? object.label : object.root ? `${object.root.kind} #${object.root.id}` : `物件 ${index + 1}`
      });
      triangleCount += triangles.length;
    });
    return { objects, triangleCount, bounds: objects.length ? { min, max } : null };
  }

  function create(canvas, options) {
    options = options || {};
    if (!canvas || typeof canvas.getContext !== 'function') throw new TypeError('3D 檢視器需要 canvas。');
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('此瀏覽器無法建立 3D 預覽畫布。');
    const background = options.background || '#111b26';
    const backgroundRGB = rgb(background, '#111b26');
    const lightTheme = options.theme === 'light' || options.theme !== 'dark' && dot(backgroundRGB, [0.2126, 0.7152, 0.0722]) > 150;
    const ink = lightTheme ? {
      text: '#33485a', muted: '#5d6e7b', scale: '#526678', axes: ['#ac443d', '#3e7629', '#3566a8']
    } : {
      text: '#e1e8ef', muted: '#a9b8c8', scale: '#c7d0db', axes: ['#ef9a92', '#9fce85', '#96baff']
    };
    const win = canvas.ownerDocument && canvas.ownerDocument.defaultView || (typeof window !== 'undefined' ? window : null);
    let prepared = prepareObjects([]), width = 1, height = 1, dpr = 1;
    let yaw = VIEWS.iso.yaw, pitch = VIEWS.iso.pitch, view = 'iso';
    let scale = 1, zoom = 1, frame = null, destroyed = false;
    let panX = 0, panY = 0;
    let emptyText = options.emptyText || '建立預覽後，這裡會顯示 3D 模型';
    const pointers = new Map();
    const listeners = [];
    const oldTouchAction = canvas.style.touchAction, oldCursor = canvas.style.cursor;
    const oldTabIndex = canvas.getAttribute('tabindex'), oldLabel = canvas.getAttribute('aria-label');
    canvas.style.touchAction = 'none';
    canvas.style.cursor = 'grab';
    if (oldTabIndex === null) canvas.tabIndex = 0;
    if (!oldLabel) canvas.setAttribute('aria-label', '3D 模型預覽。拖曳或方向鍵旋轉，Shift 拖曳平移，滾輪或加減鍵縮放，F 鍵置中。');

    function center() {
      return prepared.bounds ? prepared.bounds.min.map((v, i) => (v + prepared.bounds.max[i]) / 2) : [0, 0, 0];
    }

    function projectedData() {
      const origin = center();
      let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
      const items = prepared.objects.map(object => {
        const points = object.vertices.map(vertex => project(sub(vertex, origin), yaw, pitch));
        object.triangles.forEach(triangle => triangle.indices.forEach(i => {
          const p = points[i];
          xmin = Math.min(xmin, p[0]); xmax = Math.max(xmax, p[0]);
          ymin = Math.min(ymin, p[1]); ymax = Math.max(ymax, p[1]);
        }));
        return { object, points };
      });
      return { items, xmin, xmax, ymin, ymax };
    }

    function fitScale() {
      if (!prepared.objects.length) { scale = 1; return; }
      const p = projectedData();
      // Short desktop/mobile panes still need a useful model. Fixed HUD padding
      // previously consumed 118 px of a 130 px canvas and reduced it to a speck.
      const usableWidth = Math.max(1, width - Math.min(60, width * 0.1));
      const usableHeight = Math.max(1, height - Math.min(84, height * 0.18));
      scale = Math.min(usableWidth / Math.max(1, p.xmax - p.xmin), usableHeight / Math.max(1, p.ymax - p.ymin));
    }

    function notify() {
      if (typeof options.onChange === 'function') options.onChange(getState());
    }

    function schedule() {
      if (destroyed || frame !== null) return;
      if (win && win.requestAnimationFrame) frame = win.requestAnimationFrame(() => { frame = null; draw(); });
      else draw();
    }

    function resize(redraw = true) {
      if (destroyed) return;
      const rect = canvas.getBoundingClientRect();
      // A hidden dialog/tab has no usable viewport. Keep the last camera until
      // it is shown, and remeasure at drawing time as well as via the observer.
      if (rect.width <= 0 || rect.height <= 0) return;
      const nextWidth = Math.max(1, rect.width), nextHeight = Math.max(1, rect.height);
      const nextDpr = Math.max(1, win && win.devicePixelRatio || 1);
      if (nextWidth === width && nextHeight === height && dpr === nextDpr) return;
      width = nextWidth; height = nextHeight; dpr = nextDpr;
      canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
      fitScale(); if (redraw !== false) schedule();
    }

    function path(points) {
      ctx.beginPath(); ctx.moveTo(points[0][0], points[0][1]);
      ctx.lineTo(points[1][0], points[1][1]); ctx.lineTo(points[2][0], points[2][1]); ctx.closePath();
    }

    function axes() {
      const x = 49, y = height - 45, length = 28;
      ctx.save(); ctx.font = '600 11px system-ui, sans-serif'; ctx.lineWidth = 1.8;
      const axes = [
        { vector: [1, 0, 0], color: ink.axes[0], label: '+X' },
        { vector: [0, 1, 0], color: ink.axes[1], label: '+Y' },
        { vector: [0, 0, 1], color: ink.axes[2], label: '+Z' }
      ].map(axis => ({ ...axis, p: project(axis.vector, yaw, pitch) })).sort((a, b) => a.p[2] - b.p[2]);
      axes.forEach(axis => {
        const dx = axis.p[0] * length, dy = axis.p[1] * length;
        ctx.strokeStyle = axis.color; ctx.fillStyle = axis.color;
        if (Math.hypot(dx, dy) < 1) {
          ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.stroke();
          ctx.fillText(axis.label + (axis.p[2] > 0 ? ' ⊙' : ' ⊗'), x - 13, y + 20);
        } else {
          ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + dx, y + dy); ctx.stroke();
          ctx.beginPath(); ctx.arc(x + dx, y + dy, 2.5, 0, Math.PI * 2); ctx.fill();
          ctx.fillText(axis.label, x + dx + (dx < -4 ? -21 : 5), y + dy + (dy > 4 ? 11 : -4));
        }
      });
      ctx.restore();
    }

    function scaleBar() {
      if (!prepared.objects.length || width < 220) return;
      const pixelsPerMM = scale * zoom;
      const targetMM = Math.min(100, width / 4) / pixelsPerMM;
      const power = Math.pow(10, Math.floor(Math.log10(targetMM)));
      const distance = [5, 2, 1].map(n => n * power).find(n => n <= targetMM) || power / 2;
      const pixels = distance * pixelsPerMM, right = width - 19, bottom = height - 22;
      ctx.save(); ctx.strokeStyle = ink.scale; ctx.fillStyle = ink.scale; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(right - pixels, bottom - 4); ctx.lineTo(right - pixels, bottom);
      ctx.lineTo(right, bottom); ctx.lineTo(right, bottom - 4); ctx.stroke();
      ctx.font = '11px system-ui, sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(`${Number(distance.toPrecision(5)).toLocaleString()} mm`, right, bottom - 9);
      ctx.restore();
    }

    function legend() {
      const labels = Array.from(new Map(prepared.objects.map(object => [object.label, object])).values());
      ctx.save(); ctx.font = '12px system-ui, sans-serif'; ctx.textBaseline = 'middle';
      let x = 16, row = 0;
      labels.slice(0, 4).forEach(object => {
        const label = object.label.length > 22 ? object.label.slice(0, 21) + '…' : object.label;
        const itemWidth = ctx.measureText(label).width + 26;
        if (x > 16 && x + itemWidth > width - 16) { x = 16; row++; }
        if (row > 1) return;
        const y = 19 + row * 21;
        ctx.fillStyle = `rgb(${object.color.join(',')})`; ctx.fillRect(x, y - 4, 8, 8);
        ctx.fillStyle = ink.text; ctx.fillText(label, x + 14, y); x += itemWidth;
      });
      ctx.restore();
    }

    function draw() {
      if (destroyed) return;
      resize(false);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = background; ctx.fillRect(0, 0, width, height);
      if (!prepared.objects.length) {
        ctx.fillStyle = ink.muted; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.font = '14px system-ui, sans-serif';
        ctx.fillText(emptyText, width / 2, height / 2, Math.max(1, width - 36));
        ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; axes(); return;
      }
      const projected = projectedData(), faces = [];
      const xoff = (projected.xmin + projected.xmax) / 2;
      const yoff = (projected.ymin + projected.ymax) / 2;
      const screen = p => [(p[0] - xoff) * scale * zoom + width / 2 + panX, (p[1] - yoff) * scale * zoom + height / 2 - 4 + panY];
      projected.items.forEach(({ object, points }) => {
        object.triangles.forEach(triangle => {
          const trianglePoints = triangle.indices.map(index => points[index]);
          faces.push({ object, triangle, points: trianglePoints.map(screen), depth: trianglePoints.reduce((sum, p) => sum + p[2], 0) / 3 });
        });
      });
      faces.sort((a, b) => a.depth - b.depth);
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      faces.forEach(face => {
        const { object, triangle, points } = face;
        // Fixed world light makes orientation and the true creases legible.
        const light = 0.68 + 0.32 * Math.abs(dot(triangle.normal, [-0.35, -0.25, 0.9027735]));
        ctx.fillStyle = `rgb(${object.color.map(v => Math.round(v * light)).join(',')})`;
        ctx.globalAlpha = object.opacity;
        path(points); ctx.fill();
        ctx.strokeStyle = '#182b38'; ctx.globalAlpha = Math.min(0.95, object.opacity + 0.26); ctx.lineWidth = 1;
        triangle.edges.forEach((edge, side) => {
          if (!object.featureEdges.has(edge)) return;
          const a = points[side], b = points[(side + 1) % 3];
          ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke();
        });
      });
      ctx.globalAlpha = 1; legend(); axes(); scaleBar();
    }

    function listen(type, callback, settings) {
      canvas.addEventListener(type, callback, settings); listeners.push([type, callback, settings]);
    }

    function pinchDistance() {
      const pair = Array.from(pointers.values());
      return pair.length >= 2 ? Math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y) : 0;
    }

    listen('pointerdown', event => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      event.preventDefault();
      canvas.focus({ preventScroll: true });
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      canvas.setPointerCapture(event.pointerId); canvas.style.cursor = 'grabbing';
    });
    listen('pointermove', event => {
      const previous = pointers.get(event.pointerId);
      if (!previous) return;
      const previousDistance = pinchDistance();
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pointers.size >= 2) {
        const nextDistance = pinchDistance();
        if (previousDistance > 2 && nextDistance > 2) zoom = clamp(zoom * nextDistance / previousDistance, 0.1, 12);
      } else if (event.shiftKey) {
        panX += event.clientX - previous.x;
        panY += event.clientY - previous.y;
      } else {
        yaw -= (event.clientX - previous.x) * 0.007;
        pitch = clamp(pitch + (event.clientY - previous.y) * 0.007, -Math.PI / 2, Math.PI / 2);
        view = 'custom';
      }
      schedule(); notify();
    });
    function release(event) {
      pointers.delete(event.pointerId);
      if (canvas.hasPointerCapture && canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      canvas.style.cursor = pointers.size ? 'grabbing' : 'grab';
    }
    listen('pointerup', release); listen('pointercancel', release); listen('lostpointercapture', release);
    listen('wheel', event => {
      event.preventDefault();
      const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? height : 1);
      zoom = clamp(zoom * Math.exp(-delta * 0.0015), 0.1, 12); schedule(); notify();
    }, { passive: false });
    listen('keydown', event => {
      const key = event.key;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (key === 'ArrowLeft') yaw += 0.12;
      else if (key === 'ArrowRight') yaw -= 0.12;
      else if (key === 'ArrowUp') pitch = clamp(pitch + 0.12, -Math.PI / 2, Math.PI / 2);
      else if (key === 'ArrowDown') pitch = clamp(pitch - 0.12, -Math.PI / 2, Math.PI / 2);
      else if (key === '+' || key === '=') zoom = clamp(zoom * 1.15, 0.1, 12);
      else if (key === '-' || key === '_') zoom = clamp(zoom / 1.15, 0.1, 12);
      else if (key.toLowerCase() === 'f' || key === 'Home') { event.preventDefault(); fit(); return; }
      else return;
      if (key.startsWith('Arrow')) view = 'custom';
      event.preventDefault(); schedule(); notify();
    });

    const ResizeObserverClass = win && win.ResizeObserver;
    const observer = ResizeObserverClass ? new ResizeObserverClass(resize) : null;
    if (observer) observer.observe(canvas);
    if (win) win.addEventListener('resize', resize);

    function setObjects(objects) {
      if (destroyed) return;
      // Clear first: malformed or empty new output must never leave an old model.
      prepared = prepareObjects([]); zoom = 1; panX = 0; panY = 0;
      try { prepared = prepareObjects(objects); }
      catch (error) { emptyText = '網格資料無法顯示，請查看建模診斷'; schedule(); notify(); throw error; }
      emptyText = options.emptyText || '建立預覽後，這裡會顯示 3D 模型';
      resize(); fitScale(); schedule(); notify();
      return getState();
    }

    function fit() {
      if (destroyed) return;
      resize(); zoom = 1; panX = 0; panY = 0; fitScale(); schedule(); notify();
    }

    function setView(name) {
      if (!Object.prototype.hasOwnProperty.call(VIEWS, name)) throw new TypeError('檢視方向必須是 iso、top、bottom 或 front。');
      if (destroyed) return;
      yaw = VIEWS[name].yaw; pitch = VIEWS[name].pitch; view = name; fit();
    }

    function getState() {
      return {
        objectCount: prepared.objects.length, triangleCount: prepared.triangleCount,
        bounds: prepared.bounds ? { min: prepared.bounds.min.slice(), max: prepared.bounds.max.slice() } : null,
        labels: prepared.objects.map(object => object.label), view, yaw, pitch, zoom, pan: { x: panX, y: panY },
        width, height, destroyed
      };
    }

    function destroy() {
      if (destroyed) return;
      destroyed = true;
      if (frame !== null && win) win.cancelAnimationFrame(frame);
      if (observer) observer.disconnect();
      if (win) win.removeEventListener('resize', resize);
      listeners.forEach(([type, callback, settings]) => canvas.removeEventListener(type, callback, settings));
      pointers.forEach((_, id) => {
        if (canvas.hasPointerCapture && canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
      });
      pointers.clear(); prepared = prepareObjects([]);
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.style.touchAction = oldTouchAction; canvas.style.cursor = oldCursor;
      if (oldTabIndex === null) canvas.removeAttribute('tabindex'); else canvas.setAttribute('tabindex', oldTabIndex);
      if (oldLabel === null) canvas.removeAttribute('aria-label'); else canvas.setAttribute('aria-label', oldLabel);
    }

    resize(); schedule();
    return { setObjects, fit, setView, destroy, getState };
  }

  return { create, project, projectPlanPoint, spacePreviewObjects, prepareObjects, views: VIEWS };
});
