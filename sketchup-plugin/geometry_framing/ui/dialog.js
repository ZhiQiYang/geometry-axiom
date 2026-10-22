'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const svgNS = 'http://www.w3.org/2000/svg';
  const names = {board:'面材',wall:'沿邊料',pri:'主支',sec:'副支',long:'縱向料',rib:'橫撐'};
  const corners = {tl:'左上',tr:'右上',bl:'左下',br:'右下'};
  const previous = {};
  let busy = false;
  let valid = false;
  let phase = 'unreviewed';
  let staleReason = '';
  let selectionLabel = '';

  const currentMode = () => $('mode').value;
  const lastResult = () => previous[currentMode()];
  const number = value => Number.isFinite(Number(value)) ? Number(value).toLocaleString('zh-TW', {maximumFractionDigits: 3}) : '—';
  const pointText = point => Array.isArray(point) ? point.map(number).join(', ') + ' mm' : '';
  const directionText = direction => Array.isArray(direction) ? direction.map(value => String(Number(Number(value).toFixed(3)))).join(', ') : '';
  const vector = value => Array.isArray(value) && value.length >= 2 && value.every(Number.isFinite);

  function setBusy(value) {
    busy = value;
    $('preview').disabled = value;
    $('generate').disabled = value || !valid;
    $('mode').disabled = value;
    $('parameters').inert = value;
    document.querySelector('.results').setAttribute('aria-busy', String(value));
  }

  function status(message, failure = false) {
    $('status').textContent = message;
    $('status').className = failure ? 'fail' : '';
  }

  function unreviewedMessage() {
    return currentMode() === 'profile'
      ? '尚未檢查。按「檢查／選起點」讀取折線，並指定這次的起點。'
      : '尚未檢查。選取幾何後，按「檢查選取」。';
  }

  function invalidate(reason = 'params', message) {
    valid = false;
    if (lastResult()) {
      phase = 'stale';
      if (staleReason !== 'selection' || reason === 'selection') staleReason = reason;
      status(message || (staleReason === 'selection'
        ? '選取或模型已變更。下方保留上一輪對象的結果，請重新檢查。'
        : '參數已變更，結果已過期。上一輪建議保留供修正參考，請重新檢查。'));
    } else {
      phase = 'unreviewed';
      staleReason = '';
      status(message || unreviewedMessage());
    }
    setBusy(false);
    renderResult();
  }

  function mode(value) {
    $('mode').value = value;
    ['flat', 'profile'].forEach(key => {
      const field = $(key + '-fields');
      field.hidden = key !== value;
      field.disabled = key !== value;
    });
    $('instruction').textContent = value === 'flat'
      ? '選取一個水平正交面，再檢查這次的排板與骨架。'
      : '選取垂直平面內相連的正交邊；每次檢查可重新指定起點。';
    $('preview').textContent = value === 'profile' ? '檢查／選起點' : '檢查選取';
    staleReason = '';
    selectionLabel = '';
    invalidate('selection');
  }

  function values() {
    const fields = $(currentMode() + '-fields');
    const params = {};
    for (const el of fields.querySelectorAll('input,select')) {
      if (el.type === 'checkbox') params[el.name] = el.checked;
      else if (el.name === 'longY') {
        if (el.value !== 'auto') params.longY = el.value === 'true';
      } else if (el.type === 'number') {
        if (el.value !== '') params[el.name] = Number(el.value);
      } else params[el.name] = el.value;
    }
    return {mode:currentMode(), params};
  }

  function submit(action) {
    if (busy || (action === 'generate' && !valid) || !$('parameters').reportValidity()) return;
    if (!window.sketchup || typeof window.sketchup[action] !== 'function') {
      status('請從 SketchUp 的「擴充功能 → 下角材」開啟。');
      return;
    }
    setBusy(true);
    status(action === 'generate' ? '正在新增一批角材…' :
      currentMode() === 'profile' ? '請在 SketchUp 指定起點，接著檢查這次的斷面。' : '正在讀取目前選取並檢查規則…');
    try { window.sketchup[action](JSON.stringify(values())); }
    catch (error) { invalidate('selection', error.message); }
  }

  function svgElement(tag, attributes = {}, text) {
    const element = document.createElementNS(svgNS, tag);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function arrow(svg, start, end, kind = 'axis', label = '') {
    const dx = end[0] - start[0], dy = end[1] - start[1], length = Math.hypot(dx, dy);
    if (length < 0.01) return;
    const ux = dx / length, uy = dy / length;
    const points = [
      [end[0] - ux * 5 - uy * 3, end[1] - uy * 5 + ux * 3], end,
      [end[0] - ux * 5 + uy * 3, end[1] - uy * 5 - ux * 3]
    ];
    svg.append(svgElement('line', {x1:start[0],y1:start[1],x2:end[0],y2:end[1],class:kind}));
    svg.append(svgElement('polyline', {points:points.map(point => point.join(',')).join(' '),class:kind}));
    if (label) svg.append(svgElement('text', {x:end[0] + ux * 10, y:end[1] + uy * 10 + 4, 'text-anchor':'middle'}, label));
  }

  function pathData(rings, project) {
    return rings.map(ring => 'M' + ring.map(point => project(point).join(',')).join(' L') + ' Z').join(' ');
  }

  function flatDiagram(svg, input, params) {
    const directions = input.directions_world || {};
    if (!Array.isArray(input.rings) || !input.rings.length || !vector(directions.x) || !vector(directions.y) || !vector(input.origin_world_mm)) return false;
    const rings = input.rings;
    const origin = input.origin_world_mm;
    const world = point => [origin[0] + point[0] * directions.x[0] + point[1] * directions.y[0],
      origin[1] + point[0] * directions.x[1] + point[1] * directions.y[1]];
    const points = rings.flat().map(world);
    const minX = Math.min(...points.map(point => point[0])), maxX = Math.max(...points.map(point => point[0]));
    const minY = Math.min(...points.map(point => point[1])), maxY = Math.max(...points.map(point => point[1]));
    const scale = Math.min(240 / Math.max(1, maxX - minX), 127 / Math.max(1, maxY - minY));
    const left = (360 - (maxX - minX) * scale) / 2, top = 68 + (127 - (maxY - minY) * scale) / 2;
    const projectWorld = point => [left + (point[0] - minX) * scale, top + (maxY - point[1]) * scale];
    const project = point => projectWorld(world(point));
    svg.setAttribute('viewBox', '0 0 360 260');
    svg.append(svgElement('title', {id:'diagram-title'}, `所選面的世界 XY 俯視圖；起鋪角 ${corners[params.corner] || '待檢查'}，箭頭標示局部 X、Y`));
    svg.append(svgElement('text', {x:14,y:23,'data-world-heading':'true'}, '世界 XY 俯視：世界 X 向右、Y 向上'));
    svg.append(svgElement('path', {d:pathData(rings, project),class:'outline'}));
    const map = input.corner_map || {};
    for (const [key, label] of Object.entries(corners)) {
      if (!vector(map[key])) continue;
      const point = projectWorld(map[key]);
      const selected = key === params.corner;
      svg.append(svgElement('circle', {cx:point[0],cy:point[1],r:selected ? 5 : 4,class:selected ? 'active' : 'corner','data-corner':key}));
      svg.append(svgElement('text', {x:Math.max(28,Math.min(332,point[0])),y:point[1] + (point[1] < 131.5 ? -12 : 23),'text-anchor':'middle','data-corner-label':key}, label));
    }
    const axisOrigin = [287,215];
    arrow(svg, axisOrigin, [axisOrigin[0] + directions.x[0] * 29, axisOrigin[1] - directions.x[1] * 29], 'axis', '局部 X');
    arrow(svg, axisOrigin, [axisOrigin[0] + directions.y[0] * 19, axisOrigin[1] - directions.y[1] * 19], 'axis', '局部 Y');
    svg.append(svgElement('text', {x:14,y:241}, `${corners[params.corner] || '—'}起鋪`));
    const lengthAxis = typeof params.longY === 'boolean' ? `板長沿局部 ${params.longY ? 'Y' : 'X'}` : '板長方向待檢查';
    $('diagram-caption').textContent = `${lengthAxis}；箭頭與角名對應本次所選面的局部方向。`;
    return true;
  }

  function profileDiagram(svg, input, params) {
    const points = input.points;
    const directions = input.directions_world || {};
    if (!Array.isArray(points) || points.length < 2 || !vector(directions.u) || !vector(directions.v) || !vector(directions.L)) return false;
    const minU = Math.min(...points.map(point => point[0])), maxU = Math.max(...points.map(point => point[0]));
    const minV = Math.min(...points.map(point => point[1])), maxV = Math.max(...points.map(point => point[1]));
    const scale = Math.min(270 / Math.max(1, maxU - minU), 126 / Math.max(1, maxV - minV));
    const project = point => [42 + (point[0] - minU) * scale, 43 + (point[1] - minV) * scale];
    svg.setAttribute('viewBox', '0 0 360 300');
    svg.append(svgElement('title', {id:'diagram-title'}, `所選完成面斷面；起點 ${pointText(input.start_point_mm)}；u 向右、v 向下；橘色箭頭表示核心計算的結構側，L ${number(params.L)} mm`));
    svg.append(svgElement('text', {x:14,y:23}, '所選完成面斷面'));
    if (Array.isArray(input.profile_ring)) svg.append(svgElement('path', {d:pathData([input.profile_ring], project),class:'guide'}));
    svg.append(svgElement('polyline', {points:points.map(point => project(point).join(',')).join(' '),class:'axis',style:'stroke-width:3'}));
    for (const segment of input.profile_segments || []) {
      if (!vector(segment.p) || !vector(segment.q) || !vector(segment.n)) continue;
      const middle = project([(segment.p[0] + segment.q[0]) / 2, (segment.p[1] + segment.q[1]) / 2]);
      const sign = Boolean(params.flip) === Boolean(input.profile_flip) ? 1 : -1;
      const normal = segment.n.map(value => value * sign);
      arrow(svg, [middle[0] + normal[0] * 3,middle[1] + normal[1] * 3],
        [middle[0] + normal[0] * 19,middle[1] + normal[1] * 19], 'side');
    }
    const start = project(points[0]), end = project(points.at(-1));
    svg.append(svgElement('circle', {cx:start[0],cy:start[1],r:5,class:'active','data-profile-start':'true'}));
    svg.append(svgElement('text', {x:Math.min(317,start[0] + 10),y:Math.max(35,start[1] - 10)}, '起點'));
    svg.append(svgElement('circle', {cx:end[0],cy:end[1],r:4,class:'corner'}));
    svg.append(svgElement('text', {x:Math.max(30,end[0]),y:end[1] + 22,'text-anchor':'middle'}, '終點'));
    arrow(svg, [30,224], [65,224], 'axis', 'u');
    arrow(svg, [30,224], [30,254], 'axis', 'v');
    arrow(svg, [112,220], [139,220], 'side');
    svg.append(svgElement('text', {x:148,y:225}, params.flip ? '結構側（已換邊）' : '結構側'));
    svg.append(svgElement('text', {x:104,y:274}, `L ${number(params.L)} mm`));
    const a = Number(params.a), b = Number(params.b);
    if (a > 0 && b > 0) {
      const timberScale = 37 / Math.max(a,b), width = a * timberScale, height = b * timberScale;
      svg.append(svgElement('rect', {x:278-width/2,y:263-height/2,width,height,class:'timber','data-section-a':a,'data-section-b':b}));
      svg.append(svgElement('text', {x:278,y:235,'text-anchor':'middle'}, `u ${number(a)}`));
      svg.append(svgElement('text', {x:306,y:267}, `v ${number(b)}`));
    }
    $('diagram-caption').textContent = `u → 世界 (${directionText(directions.u)})；v → 世界 (${directionText(directions.v)})\nL → 世界 (${directionText(directions.L)})；角材斷面隨 u／v 尺寸更新。`;
    return true;
  }

  function renderSelection(result) {
    const input = result && result.input || {};
    const label = input.source_name || input.source || '';
    $('selection').hidden = !label;
    $('diagram').hidden = true;
    $('selection-diagram').replaceChildren();
    if (!label) return;
    const oldSelection = phase === 'stale' && staleReason === 'selection';
    let params = result.params || {};
    if (phase === 'stale' && staleReason === 'params') {
      params = {...params, ...values().params};
      if (currentMode() === 'flat') {
        if ($('flat-fields').querySelector('[name=longY]').value === 'auto') delete params.longY;
        if ($('flat-fields').querySelector('[name=ceil]').value === '') params.ceil = input.ceil;
      }
    }
    $('selection-name').textContent = `${oldSelection ? '上一輪對象：' : '檢查對象：'}${label}`;
    const details = [];
    if (input.source_path_label) details.push(input.source_path_label);
    if (oldSelection) details.push(`目前：${selectionLabel || '選取或模型已變更'}；以下不是目前選取的檢查結果。`);
    if (currentMode() === 'flat') {
      const bounds = input.bounds_mm;
      if (Array.isArray(bounds) && bounds.length >= 4) details.push(`${number(bounds[2]-bounds[0])} × ${number(bounds[3]-bounds[1])} mm`);
      if (Number.isFinite(input.ceil)) details.push(`選面標高 ${number(input.ceil)} mm`);
      if (Number.isFinite(params.ceil) && params.ceil !== input.ceil) details.push(`設定完成面 ${number(params.ceil)} mm`);
    } else if (Array.isArray(input.start_point_mm)) {
      details.push(`起點世界座標：(${pointText(input.start_point_mm)})`);
      if (Array.isArray(input.end_point_mm)) details.push(`終點世界座標：(${pointText(input.end_point_mm)})`);
    }
    $('selection-details').textContent = details.join('\n');
    const shown = currentMode() === 'flat'
      ? flatDiagram($('selection-diagram'), input, params)
      : profileDiagram($('selection-diagram'), input, params);
    $('diagram').hidden = !shown;
    if (shown && phase === 'stale') $('diagram-caption').textContent =
      `${oldSelection ? '上一輪選取示意；僅供參考。' : staleReason === 'params' ? '目前參數示意；尚未重新檢查。' : '上一輪示意；這次檢查尚未完成。'}\n${$('diagram-caption').textContent}`;
  }

  function renderResult() {
    const result = lastResult();
    document.querySelector('.results').classList.toggle('is-stale', phase === 'stale');
    $('review-result').hidden = !result;
    $('result-state').textContent = phase === 'stale' ? '結果已過期 · 上一輪數量與建議，僅供參考' :
      phase === 'generated' ? '本次新增批次的檢查結果' : result ? '本次規則檢查' : '';
    $('counts').textContent = Object.entries(result && result.counts || {}).map(([role,count]) => `${names[role] || role} ${count}`).join(' · ');
    $('checks').replaceChildren();
    for (const check of result && result.checks || []) {
      const item = document.createElement('li');
      const title = document.createElement('strong');
      title.className = check.ok ? 'pass' : 'fail';
      title.textContent = `${check.ok ? '✓' : '✕'} ${check.title}`;
      const detail = document.createElement('div');
      detail.className = 'detail';
      detail.textContent = check.detail || '';
      item.append(title, detail);
      $('checks').append(item);
    }
    renderSelection(result);
  }

  window.GeometryFramingUI = {
    receive(payload) {
      const next = payload.status || (payload.generated ? 'generated' : Array.isArray(payload.checks) && payload.checks.length ? 'reviewed' : 'unreviewed');
      if (payload.preserve_result || next === 'stale') {
        // 選取通知可能來自後端上次檢查的模式，不能覆寫使用者剛切換的模式。
        if (next === 'error' && payload.mode && payload.mode !== currentMode()) return;
        selectionLabel = payload.selection_label || selectionLabel;
        invalidate(next === 'error' ? 'check' : 'selection', payload.message);
        if (next === 'error') status(payload.message || payload.error_check && payload.error_check.detail || '檢查未完成，請調整後重試。', true);
        return;
      }
      if (payload.mode && payload.mode !== currentMode()) {
        if (next !== 'unreviewed') return;
        mode(payload.mode);
      }
      valid = next === 'reviewed' && payload.ok === true && Array.isArray(payload.checks) && payload.checks.length > 0 && payload.checks.every(check => check.ok);
      phase = next;
      staleReason = '';
      selectionLabel = '';
      if (Array.isArray(payload.checks) && payload.checks.length) previous[currentMode()] = payload;
      else if (next === 'unreviewed') delete previous[currentMode()];
      setBusy(false);
      status(payload.message || (phase === 'generated' ? '已新增一批角材；舊批次保留。再次新增前，請重新檢查。' :
        valid ? '規則檢查通過，可以新增一批角材。' : next === 'unreviewed' ? unreviewedMessage() : '請先處理下列檢查結果。'),
      next === 'error' || (next === 'reviewed' && !valid));
      renderResult();
    }
  };

  $('mode').addEventListener('change', () => mode(currentMode()));
  $('parameters').addEventListener('input', () => invalidate());
  $('parameters').addEventListener('change', () => invalidate());
  $('parameters').addEventListener('invalid', event => {
    const details = event.target.closest('details');
    if (details) details.open = true;
  }, true);
  $('parameters').addEventListener('submit', event => { event.preventDefault(); submit('preview'); });
  $('rotate').addEventListener('click', () => {
    const a = $('profile-fields').querySelector('[name=a]');
    const b = $('profile-fields').querySelector('[name=b]');
    [a.value,b.value] = [b.value,a.value];
    invalidate();
  });
  $('generate').addEventListener('click', () => submit('generate'));
  if (window.sketchup && window.sketchup.ready) window.sketchup.ready();
})();
