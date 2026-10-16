/* Fixed woodworking/1 presentation and creation recipes. No project defaults are
   applied while opening a saved document. The host selects this provider once. */
(function (root, factory) {
  'use strict';
  const provider = factory();
  if (typeof module === 'object' && module.exports) module.exports = provider;
  else Object.defineProperty(root, 'GeometryWoodworking', {value: provider});
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const freeze = value => {
    if (value && (typeof value === 'object' || typeof value === 'function')) {
      Object.values(value).forEach(freeze);
      Object.freeze(value);
    }
    return value;
  };
  const panel = freeze({id: 'calcium-silicate-6', name: '矽酸鈣板', thickness: 6,
    width: 915, length: 1830});
  const section = freeze({A: 27, B: 33});
  const engineeringRoles = freeze([['boundary', '邊界材'], ['primary', '主支'], ['secondary', '副支']]);
  const placementRoles = freeze([['primary', '主支'], ['boundary', '邊框材'],
    ['secondary', '副支'], ['custom', '自訂角色']]);
  const labels = freeze({
    materials: {panel: '面材', timber: '角材'},
    roles: {primary: '主支', secondary: '副支', boundary: '邊界材', custom: '自訂'},
    gridLines: {main: '主支線', sub: '副支線'},
    fixedPanel: '矽酸鈣板固定規格：厚 6 mm，斷面寬度小於 915 mm，板長 1830 mm；此規格僅供查看。',
  });

  function materialDraft(type = 'panel') {
    if (type !== 'panel' && type !== 'timber') throw Error('未知材料種類。');
    return {mode: 'new', base: null, name: type === 'panel' ? panel.name : '', type,
      width: type === 'panel' ? String(panel.width) : '',
      length: type === 'panel' ? String(panel.length) : '',
      thickness: type === 'panel' ? String(panel.thickness) : '',
      A: '', B: '', brand: '', model: '', source: '', note: ''};
  }

  function sectionMember(kind) {
    if (kind === 'panel') return {panelSpec: panel.id, width: 100, orientation: 'thickness-v'};
    if (kind === 'timber') return {A: {kind: 'literal', value: section.A},
      B: {kind: 'literal', value: section.B}, orientation: 'A-u'};
    throw Error('未知斷面構件種類。');
  }

  function primaryAxisInfo(timbers = []) {
    const primaries = timbers.filter(t => t.role === "primary");
    const boundaries = timbers.filter(t => t.role === "boundary");
    const axisOf = t => t.dir && t.dir.slice(-1);
    let axis = null, conflict = false, src = "none";
    if (primaries.length) {
      const axes = new Set(primaries.map(axisOf));
      if (axes.size > 1) { conflict = true; }
      else axis = [...axes][0];
      src = "primary";
    }
    if (boundaries.length) {
      /* boundary 的長度軸 ⊥ 主支軸 → 主支軸 = boundary 軸的垂直向。
         所有 boundary 同方向(D17 保證);不一致 = 矛盾。 */
      const bAxes = new Set(boundaries.map(axisOf));
      const bAxis = bAxes.size === 1 ? [...bAxes][0] : null;
      if (bAxis == null) { conflict = true; }
      else {
        const derived = bAxis === "u" ? "v" : "u";
        if (axis == null) { axis = derived; src = "boundary"; }
        else if (axis !== derived) conflict = true;
      }
    }
    return { axis, conflict, src };
  }
  function roleForClick(info, kind, dirAxis) {
    if (info.conflict) return null;
    const axis = info.axis;
    if (!axis) return kind === "edge" ? "boundary" : "primary";
    if (dirAxis === axis) return "primary";
    return kind === "edge" ? "boundary" : "secondary";
  }
  function subgridRoleWarning(info, direction, role) {
    if (role !== "secondary") return "";
    if (info.conflict) return "面上主支方向有衝突，請先檢查既有角材。";
    if (!info.axis) return "尚未建立實際主支方向；請先放主支或邊界材，或明確改選其他合法角色。";
    if (direction?.slice(-1) === info.axis) return `此線平行於實際主支 ${info.axis} 方向，不能用副支 3；請明確改選合法角色。`;
    return "";
  }
  function roleOptions(info, dirValue) {
    const axis = info.conflict ? null : info.axis;
    const dirAxis = (dirValue || "+u").slice(-1);
    const parallel = axis && dirAxis === axis;
    const perpendicular = axis && dirAxis !== axis;
    return placementRoles.map(([v, t]) => {
      let disabled = false, suffix = "";
      if (parallel && (v === "boundary" || v === "secondary")) { disabled = true; suffix = "（需垂直於主支軸）"; }
      else if (perpendicular && v === "primary") { disabled = true; suffix = "（沿主支軸才能是主支）"; }
      return {value: v, label: t + suffix, disabled};
    });
  }

  return freeze({id: 'woodworking/1', panel, section, labels, materialDraft, sectionMember,
    engineeringRoles, placementRoles, primaryAxisInfo, roleForClick, subgridRoleWarning, roleOptions,
    materialPresets: [{width: panel.width, length: panel.length}, {width: 910, length: 1820}],
    thicknessPresets: [panel.thickness, 9],
    trialFaces: [{value: section.A, thickness: section.B}, {value: section.B, thickness: section.A}],
  });
});
