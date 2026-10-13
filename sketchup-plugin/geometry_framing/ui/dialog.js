'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const names = {board:'面材',wall:'沿邊料',pri:'主支',sec:'副支',long:'縱向料',rib:'橫撐'};
  let busy = false;
  let valid = false;
  function setBusy(value) {
    busy = value;
    $('preview').disabled = value;
    $('generate').disabled = value || !valid;
    $('mode').disabled = value;
    $('parameters').style.pointerEvents = value ? 'none' : '';
    $('parameters').inert = value;
  }
  function invalidate() {
    valid = false;
    $('generate').disabled = true;
    $('status').textContent = '參數已變更，請重新檢查選取。';
    $('checks').replaceChildren();
    $('counts').textContent = '';
  }
  function mode(value) {
    $('mode').value = value;
    ['flat', 'profile'].forEach(key => {
      const field = $(key + '-fields');
      field.hidden = key !== value;
      field.disabled = key !== value;
    });
    $('instruction').textContent = value === 'flat'
      ? '選取一個水平正交面，內圈視為獨立柱。起鋪角依所選面的局部平面座標。'
      : '選取垂直平面內相連的正交邊，兩端需貼住既有樓板或牆面。';
    invalidate();
  }
  function values() {
    const fields = $($('mode').value + '-fields');
    const params = {};
    for (const el of fields.querySelectorAll('input,select')) {
      if (el.type === 'checkbox') params[el.name] = el.checked;
      else if (el.name === 'longY') {
        if (el.value !== 'auto') params.longY = el.value === 'true';
      } else if (el.type === 'number') {
        if (el.value !== '') params[el.name] = Number(el.value);
      } else params[el.name] = el.value;
    }
    return {mode:$('mode').value, params};
  }
  function submit(action) {
    if (busy || !$('parameters').reportValidity()) return;
    if (!window.sketchup || typeof window.sketchup[action] !== 'function') {
      $('status').textContent = '請從 SketchUp 的「擴充功能 → 下角材」開啟。';
      return;
    }
    setBusy(true);
    $('status').textContent = action === 'generate' ? '正在產生角材…' : '正在讀取選取並檢查規則…';
    try { window.sketchup[action](JSON.stringify(values())); }
    catch (error) { valid = false; setBusy(false); $('status').textContent = error.message; }
  }
  window.GeometryFramingUI = {
    receive(payload) {
      if (payload.mode && payload.mode !== $('mode').value) mode(payload.mode);
      valid = payload.ok === true && Array.isArray(payload.checks) && payload.checks.length > 0 && payload.checks.every(c => c.ok);
      if (payload.generated) valid = false;
      setBusy(false);
      $('status').textContent = payload.message || (valid ? '規則檢查通過，可以產生角材。' : '請先處理下列檢查結果。');
      $('status').className = payload.ok === false ? 'fail' : '';
      $('selection').textContent = payload.input && payload.input.axis_note || '';
      $('counts').textContent = Object.entries(payload.counts || {}).map(([role,count]) => `${names[role] || role} ${count}`).join(' · ');
      $('checks').replaceChildren();
      for (const check of payload.checks || []) {
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
    }
  };
  $('mode').addEventListener('change', () => mode($('mode').value));
  $('parameters').addEventListener('input', invalidate);
  $('parameters').addEventListener('change', invalidate);
  $('parameters').addEventListener('submit', e => { e.preventDefault(); submit('preview'); });
  $('rotate').addEventListener('click', () => {
    const a = $('profile-fields').querySelector('[name=a]');
    const b = $('profile-fields').querySelector('[name=b]');
    [a.value,b.value] = [b.value,a.value];
    invalidate();
  });
  $('preview').addEventListener('click', () => submit('preview'));
  $('generate').addEventListener('click', () => submit('generate'));
  if (window.sketchup && window.sketchup.ready) window.sketchup.ready();
})();
