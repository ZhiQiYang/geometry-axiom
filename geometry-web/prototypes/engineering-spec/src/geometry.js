// Prototype-only millimetre model. Production validation remains in geometry-core.
import { panelFor } from './catalog.js';
export { panelFor } from './catalog.js';
export const SCENE = Object.freeze({ width: 4000, height: 3000, hole: [2300, 1400, 2800, 1900] });

function coordinates(panel, gap, hi) {
  const step = panel + gap;
  const lines = [];
  for (let k = 0; (k + 1) * step < hi; k += 1) {
    lines.push(panel + Math.floor(gap / 2) + k * step);
  }
  return lines;
}

// A line is represented by two [u, v] points; an opening splits it into real segments.
export function clipLine(axis, coordinate, lo, hi, hole = SCENE.hole) {
  const [u0, v0, u1, v1] = hole;
  const acrossHole = axis === 'u' ? coordinate > u0 && coordinate < u1 : coordinate > v0 && coordinate < v1;
  const holeLo = axis === 'u' ? v0 : u0;
  const holeHi = axis === 'u' ? v1 : u1;
  const ranges = acrossHole && holeLo < hi && holeHi > lo
    ? [[lo, Math.min(hi, holeLo)], [Math.max(lo, holeHi), hi]]
    : [[lo, hi]];
  return ranges.filter(([a, b]) => b > a).map(([a, b]) => axis === 'u'
    ? [[coordinate, a], [coordinate, b]]
    : [[a, coordinate], [b, coordinate]]);
}

export function getLayout(settings, { width = SCENE.width, height = SCENE.height, hasSubgrid = true, catalog } = {}) {
  const result = { width, height, u: [], v: [], mainSegments: [], child: null, errors: [], panel: null };
  const panel = settings && Object.hasOwn(settings, 'panel') ? settings.panel : panelFor(settings?.methodId, catalog);
  if (!Array.isArray(panel) || panel.length < 2 || !panel.slice(0, 2).every(value => Number.isSafeInteger(value) && value > 0) || (panel[2] !== null && panel[2] !== undefined && (!Number.isFinite(panel[2]) || panel[2] <= 0))) result.errors.push({ code: 'PANEL', message: '請引用有效的面材尺寸；厚度可尚未設定。' });
  if (!Number.isSafeInteger(settings?.gap) || settings.gap < 0 || settings.gap > 100000000) {
    result.errors.push({ code: 'GAP', message: '接縫寬度請輸入 0–100,000,000 mm 的整數。' });
  }
  if (!['u', 'v'].includes(settings?.longAxis) || !['u', 'v'].includes(settings?.mainAlong)) {
    result.errors.push({ code: 'AXIS', message: '請選擇有效的排板與主支方向。' });
  }
  if (![width, height].every(value => Number.isSafeInteger(value) && value > 0 && value <= 100000)) {
    result.errors.push({ code: 'SIZE', message: '示範面的尺寸超出支援範圍。' });
  }
  if (result.errors.length) return result;
  if (panel.slice(0, 2).some(value => !Number.isSafeInteger(value + settings.gap))) {
    result.errors.push({ code: 'SIZE', message: '面材與縫寬的總和超出可精確計算的整數範圍。' });
    return result;
  }
  result.panel = [...panel];
  const [short, long] = panel;
  const steps = [settings.longAxis === 'v' ? short : long, settings.longAxis === 'v' ? long : short].map(value => value + settings.gap);
  const counts = [Math.floor((width - 1) / steps[0]), Math.floor((height - 1) / steps[1])];
  if (counts.some(count => count > 64)) {
    result.errors.push({ code: 'LINE_LIMIT', message: `主網格推導線數 u=${counts[0]}、v=${counts[1]}，超過單軸 64 條上限；請調整面材或縫寬。` });
    return result;
  }
  result.u = coordinates(settings.longAxis === 'v' ? short : long, settings.gap, width);
  result.v = coordinates(settings.longAxis === 'v' ? long : short, settings.gap, height);
  for (const axis of ['u', 'v']) {
    result[axis].forEach((coordinate, index) => {
      const role = (axis === 'u' ? 'v' : 'u') === settings.mainAlong ? 2 : 3;
      clipLine(axis, coordinate, 0, axis === 'u' ? height : width).forEach(points => {
        result.mainSegments.push({ axis, index, coordinate, role, points });
      });
    });
  }
  if (!hasSubgrid) return result;
  if (result.u.length < 2 || result.v.length < 1) {
    result.errors.push({ code: 'CELL_MISSING', message: '子網格所引用的父格線已不存在，請先調整子網格。' });
    return result;
  }
  const bounds = { u: [result.u[0], result.u[1]], v: [0, result.v[0]] };
  const span = bounds.u[1] - bounds.u[0];
  result.child = { bounds, divisions: { u: 3, v: 1 }, segments: [], valid: span % 3 === 0, span };
  if (!result.child.valid) {
    result.errors.push({ code: 'SUBGRID_INTEGER', message: `父格寬度 ${span} mm 無法整數三等分。`, span, divisions: 3 });
    return result;
  }
  for (let index = 0; index < 2; index += 1) {
    const coordinate = bounds.u[0] + (index + 1) * span / 3;
    clipLine('u', coordinate, bounds.v[0], bounds.v[1]).forEach(points => {
      result.child.segments.push({ axis: 'u', index, coordinate, role: 3, points });
    });
  }
  return result;
}

export function getLayoutErrors(baseline, draft, options) {
  const before = getLayout(baseline, options);
  const after = getLayout(draft, options);
  if ((options?.hasSubgrid ?? true) && before.panel && after.panel
      && (before.u.length !== after.u.length || before.v.length !== after.v.length)) {
    return ['此主網格仍有子網格，不能變更父格線數量。'];
  }
  return after.errors.map(error => error.message);
}
