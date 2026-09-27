import { resolveMethod, methodLabel, panelFor } from './catalog.js';

const roles = [['boundary', '邊界 1'], ['primary', '主支 2'], ['secondary', '副支 3']];
const materialLabel = material => material
  ? `${material.name} · v${material.version}｜${material.type === 'panel' ? `${material.width} × ${material.length} mm · 厚 ${material.thickness == null ? '未設定' : `${material.thickness} mm`}` : `${material.a} × ${material.b} mm`}`
  : '未設定';

/** Compare references as well as values: an identical-size new version still matters. */
export function getPreviewChanges(catalog, before, after) {
  const describe = config => {
    const method = resolveMethod(catalog, config.methodId);
    const panel = catalog.materials[method.panelKey];
    return [
      ['method', '工程做法', config.methodId, methodLabel(catalog, config.methodId)],
      ['panel', '面材規格', [method.panelKey, ...panelFor(config.methodId, catalog)], materialLabel(panel)],
      ...roles.map(([role, label]) => [role, label, method.roles[role]?.key ?? null, materialLabel(method.roles[role])]),
      ['gap', '縫寬／來源', [Number(config.gap), Boolean(config.gapOverride)], `${config.gap} mm · ${config.gapOverride ? '本面覆寫' : '沿用工程做法'}`],
      ['axes', '面材長邊／主支', [config.longAxis, config.mainAlong], `長邊沿 ${config.longAxis}／主支沿 ${config.mainAlong}`],
    ];
  };
  const previous = describe(before);
  const rows = describe(after).map(([id, label, value, text], index) => {
    const oldValue = previous[index][2];
    const oldText = previous[index][3];
    const changed = JSON.stringify(oldValue) !== JSON.stringify(value);
    // Separate materials may have the same display name/version/dimensions.
    // Show the reference only in this ambiguous case so the change stays legible.
    const ambiguous = changed && oldText === text;
    const reference = input => Array.isArray(input) ? input[0] : input;
    return { id, label, changed,
      before: ambiguous ? `${oldText}（引用 ${reference(oldValue)}）` : oldText,
      after: ambiguous ? `${text}（引用 ${reference(value)}）` : text };
  });
  return { firstApplication: !before.applied, changed: rows.filter(row => row.changed), unchanged: rows.filter(row => !row.changed) };
}
