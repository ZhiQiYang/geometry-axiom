/* Local-only case-bundle reader. No source URL is fetched and no bundle is persisted. */
(function (global) {
  'use strict';

  const LIMITS = Object.freeze({ cases: 1000, assets: 20000, manifestBytes: 4 * 1024 * 1024,
    imageBytes: 20 * 1024 * 1024, imagePixels: 20000000, imageSide: 32768,
    files: 60001, noteLength: 20000, notesBytes: 2 * 1024 * 1024 });
  const BAD_KEYS = new Set(['__proto__', 'prototype', 'constructor']);
  const KIND_NAMES = Object.freeze({ plan: '平面', section: '剖面', photo: '照片', drawing: '圖面', elevation: '立面' });
  const IMAGE_EXT = /\.(?:jpe?g|png|webp)$/i;
  // Notes remain in this page's memory across workspace navigation and remounts.
  // Neither files nor note text are written to browser storage.
  const sessionNotes = new Map(), unexportedNotes = new Set();
  if (typeof global.addEventListener === 'function') global.addEventListener('beforeunload', event => {
    if (!unexportedNotes.size) return;
    event.preventDefault(); event.returnValue = '';
  });
  let active = null;

  function fail(message) { throw new Error(message); }
  function plain(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
  function safeJSON(value) {
    const todo = [[value, 0]];
    let count = 0;
    while (todo.length) {
      const [item, depth] = todo.pop();
      if (++count > 250000 || depth > 32) fail('JSON 結構過大或層數過深。');
      if (!item || typeof item !== 'object') continue;
      for (const key of Object.keys(item)) {
        if (BAD_KEYS.has(key)) fail('JSON 含不安全的欄位名稱。');
        todo.push([item[key], depth + 1]);
      }
    }
    return value;
  }
  function normalizePath(value) {
    if (typeof value !== 'string' || !value || value.length > 2048) fail('檔案路徑必須是有限長度的相對路徑。');
    const path = value.normalize('NFC');
    if (/^[\/\\]|[\\\x00-\x1f\x7f:#?%]/.test(path)) fail('不接受絕對路徑、網址或編碼路徑：' + value);
    const parts = path.split('/');
    if (parts.some(p => !p || p === '.' || p === '..' || BAD_KEYS.has(p.toLowerCase()))) fail('不安全的相對路徑：' + value);
    return path;
  }
  function safeURL(value) {
    if (typeof value !== 'string' || value.length > 8192 || /[\x00-\x20\x7f]/.test(value)) return null;
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  }
  function display(value, fallback = '未提供') {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'string') return value;
    if (Array.isArray(value)) return value.length ? value.map(v => display(v, '')).join('；') : fallback;
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }
  function idText(value, label) {
    if (typeof value !== 'string' || !value.trim() || value.length > 200 || BAD_KEYS.has(value)) fail(label + ' 缺少有效 id。');
    return value;
  }
  function documentRoles(value) {
    // Role metadata can add filter membership, but cannot rename an asset's primary kind.
    return Array.isArray(value) ? [...new Set(value.filter(role => typeof role === 'string' && Object.prototype.hasOwnProperty.call(KIND_NAMES, role)))] : [];
  }
  function matchesRole(asset, role) {
    return !role || asset.kind === role || documentRoles(asset.document_roles).includes(role);
  }
  function roleOptions(assets) {
    // Preserve the existing primary-kind order before appending role-only filters.
    const kinds = new Set(assets.map(asset => asset.kind));
    for (const asset of assets) for (const role of documentRoles(asset.document_roles)) kinds.add(role);
    return [...kinds];
  }
  function validateManifest(input) {
    safeJSON(input);
    if (plain(input) && input.schema_version !== undefined && input.schema_version !== '1.0') fail('不支援此案例索引 schema_version；需要 1.0。');
    const source = Array.isArray(input) ? input : plain(input) ? input.cases : null;
    if (!Array.isArray(source) || !source.length || source.length > LIMITS.cases) fail('案例索引須包含 1–1,000 個案例。');
    const caseIds = new Set(), paths = new Set();
    let total = 0;
    const cases = source.map(raw => {
      if (!plain(raw)) fail('案例資料格式錯誤。');
      const id = idText(raw.id, '案例');
      if (raw.schema_version !== '1.0') fail('案例 ' + id + ' 的 schema_version 必須是 1.0。');
      if (caseIds.has(id)) fail('案例 id 重複：' + id);
      caseIds.add(id);
      if (!Array.isArray(raw.assets) || (total += raw.assets.length) > LIMITS.assets) fail('素材清單無效或超過 20,000 筆。');
      const ids = new Set();
      const assets = raw.assets.map(a => {
        if (!plain(a)) fail('素材資料格式錯誤。');
        const assetId = idText(a.id, '素材');
        if (ids.has(assetId)) fail('同一案例素材 id 重複：' + assetId);
        ids.add(assetId);
        const asset = Object.assign(Object.create(null), a);
        asset.id = assetId;
        asset.path = normalizePath(a.path);
        for (const key of ['view_path', 'thumbnail', 'source_pdf_path']) {
          if (a[key] !== undefined && a[key] !== null && a[key] !== '') asset[key] = normalizePath(a[key]);
          else delete asset[key];
        }
        if (a.page_previews !== undefined) {
          if (!Array.isArray(a.page_previews) || a.page_previews.length > 2000) fail('素材頁面預覽清單無效：' + assetId);
          asset.page_previews = a.page_previews.map(normalizePath);
          if (new Set(asset.page_previews.map(p => p.toLowerCase())).size !== asset.page_previews.length) fail('素材頁面預覽重複：' + assetId);
        }
        // Each physical asset belongs to exactly one record; duplicate aliases within that record are harmless.
        for (const path of new Set([asset.path, asset.view_path, asset.thumbnail, ...(asset.page_previews || [])].filter(Boolean))) {
          const normalized = path.toLowerCase();
          if (paths.has(normalized)) fail('素材路徑重複：' + path);
          paths.add(normalized);
        }
        for (const key of ['source_url', 'figure_url', 'source_page_url', 'license_url', 'license_evidence_url']) {
          if (a[key] && !safeURL(a[key])) fail('素材含不安全的來源網址：' + assetId);
        }
        asset.kind = typeof a.kind === 'string' && a.kind.length <= 100 ? a.kind : 'other';
        if (a.document_roles !== undefined) asset.document_roles = documentRoles(a.document_roles);
        asset.caption = display(a.caption, assetId);
        return asset;
      });
      for (const key of ['source_url', 'license_source_url']) {
        if (raw[key] && !safeURL(raw[key])) fail('案例含不安全的來源網址：' + id);
      }
      const record = Object.assign(Object.create(null), raw, { id, assets, title: display(raw.title, id) });
      record.searchText = [id, record.title, display(raw.tags, ''), display(raw.test_coverage, ''), display(raw.geometry_notes, '')].join(' ').toLocaleLowerCase();
      return record;
    });
    return { cases, assetCount: total };
  }

  function imageDimensions(bytes) {
    const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    const n = b.length;
    if (n > LIMITS.imageBytes) fail('圖片超過 20 MB；請建立較小的 JPG / PNG / WEBP 檢視副本。');
    const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
    const ascii = (start, length) => String.fromCharCode(...b.subarray(start, start + length));
    function dimensions(width, height, mime) {
      if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 || width > LIMITS.imageSide || height > LIMITS.imageSide || width * height > LIMITS.imagePixels) {
        fail('圖片解碼尺寸超過上限（2,000 萬像素或單邊 32,768 px）；請使用安全的檢視副本。');
      }
      return { width, height, mime };
    }
    if (n >= 24 && b[0] === 137 && ascii(1, 3) === 'PNG' && b[4] === 13 && b[5] === 10 && b[6] === 26 && b[7] === 10) {
      if (dv.getUint32(8) !== 13 || ascii(12, 4) !== 'IHDR') fail('PNG 標頭無效。');
      const result = dimensions(dv.getUint32(16), dv.getUint32(20), 'image/png');
      let offset = 8, ended = false;
      while (offset + 12 <= n) {
        const length = dv.getUint32(offset), type = ascii(offset + 4, 4);
        if (offset + 12 + length > n) fail('PNG 區塊不完整。');
        if (['acTL', 'fcTL', 'fdAT'].includes(type)) fail('不支援動畫 PNG；請先匯出靜態圖片。');
        if (type === 'IHDR' && offset !== 8) fail('PNG 有重複尺寸標頭。');
        offset += 12 + length;
        if (type === 'IEND') { ended = true; break; }
      }
      if (!ended) fail('PNG 檔案不完整。');
      return result;
    }
    if (n >= 4 && b[0] === 255 && b[1] === 216) {
      let offset = 2, result = null;
      while (offset < n) {
        if (b[offset++] !== 255) fail('JPEG 標頭無效。');
        while (offset < n && b[offset] === 255) offset++;
        const marker = b[offset++];
        if (marker === 217 || marker === 218) break;
        if (marker === 1 || (marker >= 208 && marker <= 215)) continue;
        if (offset + 2 > n) fail('JPEG 標頭不完整。');
        const length = dv.getUint16(offset);
        if (length < 2 || offset + length > n) fail('JPEG 區塊不完整。');
        if ([192, 193, 194, 195, 197, 198, 199, 201, 202, 203, 205, 206, 207].includes(marker)) {
          if (length < 8 || result) fail('JPEG 尺寸標頭無效。');
          result = dimensions(dv.getUint16(offset + 5), dv.getUint16(offset + 3), 'image/jpeg');
        }
        offset += length;
      }
      if (!result) fail('找不到可驗證的 JPEG 尺寸。');
      return result;
    }
    if (n >= 20 && ascii(0, 4) === 'RIFF' && ascii(8, 4) === 'WEBP') {
      const end = dv.getUint32(4, true) + 8;
      if (end !== n) fail('WEBP 區塊長度無效。');
      let offset = 12, result = null, frame = null;
      const u24 = start => b[start] + b[start + 1] * 256 + b[start + 2] * 65536;
      while (offset + 8 <= end) {
        const type = ascii(offset, 4), length = dv.getUint32(offset + 4, true), start = offset + 8;
        if (start + length > end) fail('WEBP 區塊不完整。');
        if (type === 'ANIM' || type === 'ANMF') fail('不支援動畫 WEBP；請先匯出靜態圖片。');
        if (type === 'VP8X') {
          if (length !== 10 || result || (b[start] & 2)) fail('不支援動畫或無效的 WEBP。');
          result = dimensions(1 + u24(start + 4), 1 + u24(start + 7), 'image/webp');
        }
        if (type === 'VP8 ') {
          if (length < 10 || frame || b[start + 3] !== 157 || b[start + 4] !== 1 || b[start + 5] !== 42) fail('WEBP 影格標頭無效。');
          frame = dimensions(dv.getUint16(start + 6, true) & 16383, dv.getUint16(start + 8, true) & 16383, 'image/webp');
        }
        if (type === 'VP8L') {
          if (length < 5 || frame || b[start] !== 47) fail('WEBP 無損影格標頭無效。');
          const bits = dv.getUint32(start + 1, true);
          frame = dimensions((bits & 16383) + 1, ((bits >>> 14) & 16383) + 1, 'image/webp');
        }
        offset = start + length + (length % 2);
      }
      if (!frame || (result && (result.width !== frame.width || result.height !== frame.height))) fail('WEBP 尺寸資訊不一致。');
      return frame;
    }
    fail('僅支援標頭可驗證的靜態 JPG、PNG 或 WEBP；TIFF / SVG 不在瀏覽器內解碼。');
  }

  function indexFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length || files.length > LIMITS.files) fail('請選擇含 case_index.json 的案例資料夾（最多 60,001 個檔案）。');
    const paths = new Map(), folded = new Set(), manifests = [];
    files.forEach(file => {
      const path = normalizePath(file.webkitRelativePath || file.name);
      if (folded.has(path.toLowerCase())) fail('選取的檔案路徑重複：' + path);
      folded.add(path.toLowerCase());
      paths.set(path, file);
      if (path.split('/').pop() === 'case_index.json') manifests.push(path);
    });
    if (!manifests.length) fail('找不到 case_index.json；請選擇完整案例資料夾。');
    const shallowest = Math.min(...manifests.map(path => path.split('/').length));
    const candidates = manifests.filter(path => path.split('/').length === shallowest);
    if (candidates.length !== 1) fail('同一最上層找到多份 case_index.json；請只選擇一個案例快照資料夾。');
    const manifestPath = candidates[0], manifest = paths.get(manifestPath);
    if (manifest.size > LIMITS.manifestBytes) fail('案例索引超過 4 MB。');
    const root = manifestPath.slice(0, manifestPath.lastIndexOf('/') + 1), relative = new Map();
    for (const [path, file] of paths) if (path.startsWith(root)) relative.set(path.slice(root.length), file);
    return { manifest, files: relative, name: root.replace(/\/$/, '').split('/').pop() || '本機案例' };
  }
  async function fingerprint(text) {
    if (global.crypto && global.crypto.subtle) {
      const hash = await global.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
      return Array.from(new Uint8Array(hash), v => v.toString(16).padStart(2, '0')).join('');
    }
    // Used only to keep session notes separate, never as evidence of file integrity.
    let first = 2166136261, second = 5381;
    for (let i = 0; i < text.length; i++) { first = Math.imul(first ^ text.charCodeAt(i), 16777619); second = Math.imul(second, 33) ^ text.charCodeAt(i); }
    return 'session-' + (first >>> 0).toString(16) + '-' + (second >>> 0).toString(16) + '-' + text.length;
  }
  function serializeNotes(bundle, notes) {
    const records = Array.from(notes, ([caseId, value]) => ({ caseId, text: value.text, updatedAt: value.updatedAt }));
    const text = JSON.stringify({ schema: 'geometry-case-notes/1', bundleId: bundle.key, bundleName: bundle.name,
      exportedAt: new Date().toISOString(), notes: records }, null, 2);
    if (new TextEncoder().encode(text).byteLength > LIMITS.notesBytes) fail('本資料夾的筆記總量超過 2 MB；此變更未儲存，請先縮短筆記。');
    return text;
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function button(text, action, className = '') {
    const b = el('button', 'doc-case-button ' + className, text);
    b.type = 'button'; b.addEventListener('click', action); return b;
  }
  function link(text, url) {
    const safe = safeURL(url);
    if (!safe) return null;
    const a = el('a', 'doc-case-link', text);
    a.href = safe; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.referrerPolicy = 'no-referrer';
    return a;
  }
  function field(list, label, value) {
    list.append(el('dt', '', label), el('dd', '', display(value)));
  }
  function kindLabel(kind) { return KIND_NAMES[kind] || kind; }

  function mount(container, options = {}) {
    if (!container || typeof container.replaceChildren !== 'function') fail('案例閱讀器需要有效的容器。');
    if (active) active.destroy();
    let destroyed = false, importToken = 0, bundle = null, selectedCase = null;
    const notes = sessionNotes, panes = [], downloads = new Set();
    const root = el('section', 'doc-case-root'); root.setAttribute('aria-label', '本機案例閱讀器');
    const header = el('header', 'doc-case-header'), heading = el('div', 'doc-case-heading');
    const folderInput = el('input'); folderInput.type = 'file'; folderInput.multiple = true;
    folderInput.setAttribute('webkitdirectory', ''); folderInput.hidden = true;
    const noteInput = el('input'); noteInput.type = 'file'; noteInput.accept = '.json,application/json'; noteInput.hidden = true;
    heading.append(el('h2', '', '案例資料'), el('p', '', '平面・剖面・照片，同案對照'));
    if (typeof options.onBack === 'function') header.append(button('返回文件', () => options.onBack()));
    header.append(heading, button('開啟案例資料夾', () => folderInput.click(), 'doc-case-primary'));
    const status = el('p', 'doc-case-status', '只讀取你選取的本機檔案，不上傳或自動載入來源網址。');
    status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    const layout = el('div', 'doc-case-layout'), sidebar = el('aside', 'doc-case-sidebar');
    sidebar.setAttribute('aria-label', '案例清單');
    const searchLabel = el('label', 'doc-case-search-label', '搜尋案例');
    const search = el('input', 'doc-case-search'); search.type = 'search'; search.placeholder = '名稱、標籤、幾何特徵';
    searchLabel.append(search);
    const count = el('p', 'doc-case-count', '尚未開啟資料夾'), caseList = el('div', 'doc-case-list');
    sidebar.append(searchLabel, count, caseList);
    const main = el('main', 'doc-case-main');
    main.append(el('div', 'doc-case-empty', '選擇含 case_index.json 的資料夾，即可在這裡對照案例。素材須一併保留原本的相對路徑；缺少的檔案會清楚標示。'));
    layout.append(sidebar, main); root.append(header, status, layout, folderInput, noteInput); container.replaceChildren(root);

    function report(message, error = false) {
      if (destroyed) return;
      status.textContent = message; status.classList.toggle('doc-case-error', error);
      if (typeof options.onStatus === 'function') options.onStatus(message, error);
    }
    function currentNotes() {
      if (!bundle) return new Map();
      if (!notes.has(bundle.key)) notes.set(bundle.key, new Map());
      return notes.get(bundle.key);
    }
    function preferredPath(asset) { return asset.view_path || (asset.page_previews || [])[0] || asset.path; }
    function available(asset) { return bundle.files.has(preferredPath(asset)); }
    function renderList() {
      caseList.replaceChildren();
      if (!bundle) return;
      const query = search.value.trim().toLocaleLowerCase();
      const visible = bundle.cases.filter(c => !query || c.searchText.includes(query));
      count.textContent = visible.length + ' / ' + bundle.cases.length + ' 案例 · ' + bundle.assetCount + ' 筆素材';
      for (const c of visible) {
        const b = button('', () => showCase(c), 'doc-case-list-item');
        b.setAttribute('aria-current', c === selectedCase ? 'true' : 'false');
        b.append(el('span', 'doc-case-eyebrow', c.id), el('strong', '', c.title));
        const usable = c.assets.filter(a => a.counted !== false);
        b.append(el('span', 'doc-case-list-meta', usable.length + ' 筆採用 · ' + c.assets.filter(available).length + ' 筆檔案可用'));
        if (c.tags) b.append(el('span', 'doc-case-tags', display(c.tags, '')));
        caseList.append(b);
      }
      if (!visible.length) caseList.append(el('p', 'doc-case-empty', '沒有符合的案例。'));
    }
    function clearPanes() { while (panes.length) panes.pop().destroy(); }
    function caseEvidence(c) {
      const section = el('details', 'doc-case-evidence');
      section.append(el('summary', '', '案例證據、尺度與使用限制'));
      const list = el('dl', 'doc-case-fields');
      field(list, '圖組配對依據', c.matching_evidence);
      field(list, '尺寸／比例證據', c.dimensions_evidence);
      field(list, '量測可信度', c.measurement_confidence);
      field(list, '樑／構件證據', c.beam_geometry_rating || c.beam_certainty);
      field(list, '淨高', c.ceiling_height_status);
      field(list, '實測／標註證據', c.measurement_evidence);
      field(list, '缺少資料', c.missing_data);
      if (c.limitations) field(list, '其他限制', c.limitations);
      field(list, '授權', c.license); field(list, '著作／攝影', c.copyright_credit);
      if (c.downloaded_at_utc || c.downloaded_at) field(list, '蒐集日期', c.downloaded_at_utc || c.downloaded_at);
      section.append(list);
      const links = el('div', 'doc-case-links');
      for (const [label, url] of [['開啟案例來源 ↗', c.source_url], ['授權來源 ↗', c.license_source_url]]) {
        const a = link(label, url); if (a) links.append(a);
      }
      section.append(links); return section;
    }
    function makePane(c, initial, label) {
      let token = 0, url = null, image = null, dims = null, scale = 1, fitMode = true, isDead = false;
      const pane = el('section', 'doc-case-pane'); pane.setAttribute('aria-label', label + ' 素材檢視');
      const controls = el('div', 'doc-case-pane-controls');
      const title = el('strong', 'doc-case-pane-title', label);
      const kindSelect = el('select', 'doc-case-kind'); kindSelect.setAttribute('aria-label', label + ' 素材種類');
      const all = el('option', '', '所有種類'); all.value = ''; kindSelect.append(all);
      for (const kind of roleOptions(c.assets)) { const option = el('option', '', kindLabel(kind)); option.value = kind; kindSelect.append(option); }
      const assetSelect = el('select', 'doc-case-asset'); assetSelect.setAttribute('aria-label', label + ' 素材');
      controls.append(title, kindSelect, assetSelect);
      const documentTools = el('div', 'doc-case-document-tools'); documentTools.hidden = true;
      const tools = el('div', 'doc-case-zoom-tools'), zoomLabel = el('output', 'doc-case-zoom-label', '—');
      zoomLabel.setAttribute('aria-label', label + ' 縮放比例');
      const fitButton = button('適合', () => { fitMode = true; resize(true); });
      const out = button('−', () => zoom(scale / 1.25)); out.setAttribute('aria-label', label + ' 縮小');
      const into = button('＋', () => zoom(scale * 1.25)); into.setAttribute('aria-label', label + ' 放大');
      const actual = button('100%', () => zoom(1));
      tools.append(fitButton, out, zoomLabel, into, actual);
      const viewport = el('div', 'doc-case-viewport'); viewport.tabIndex = 0;
      viewport.setAttribute('aria-label', label + ' 圖片，可拖曳或捲動平移');
      const stage = el('div', 'doc-case-stage'); viewport.append(stage);
      const caption = el('p', 'doc-case-caption');
      const metadata = el('details', 'doc-case-asset-evidence'); metadata.append(el('summary', '', '這張素材的證據與來源'));
      const fields = el('dl', 'doc-case-fields'); metadata.append(fields);
      pane.append(controls, documentTools, tools, viewport, caption, metadata);
      function release() { if (image) { image.onload = null; image.onerror = null; image.removeAttribute('src'); image = null; } if (url) { URL.revokeObjectURL(url); url = null; } dims = null; }
      function sizes(center = false) {
        if (!dims || !image) return;
        const width = dims.width * scale, height = dims.height * scale;
        stage.style.width = Math.max(viewport.clientWidth, width) + 'px';
        stage.style.height = Math.max(viewport.clientHeight, height) + 'px';
        image.style.width = width + 'px'; image.style.height = height + 'px';
        zoomLabel.textContent = Math.round(scale * 100) + '%';
        fitButton.setAttribute('aria-pressed', String(fitMode));
        if (center) { viewport.scrollLeft = Math.max(0, (width - viewport.clientWidth) / 2); viewport.scrollTop = Math.max(0, (height - viewport.clientHeight) / 2); }
      }
      function resize(center = false) {
        if (!dims || !image) return;
        if (fitMode) scale = Math.max(.01, Math.min(4, (viewport.clientWidth - 24) / dims.width, (viewport.clientHeight - 24) / dims.height));
        sizes(center);
      }
      function zoom(next) {
        if (!dims || !image) return;
        const x = (viewport.scrollLeft + viewport.clientWidth / 2 - Math.max(0, (viewport.clientWidth - dims.width * scale) / 2)) / scale;
        const y = (viewport.scrollTop + viewport.clientHeight / 2 - Math.max(0, (viewport.clientHeight - dims.height * scale) / 2)) / scale;
        fitMode = false; scale = Math.max(.01, Math.min(4, next)); sizes();
        viewport.scrollLeft = x * scale - viewport.clientWidth / 2;
        viewport.scrollTop = y * scale - viewport.clientHeight / 2;
      }
      const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => resize()) : null;
      if (observer) observer.observe(viewport);
      let drag = null;
      viewport.addEventListener('pointerdown', event => {
        if (event.pointerType === 'touch' || event.button !== 0 || !image) return;
        drag = { x: event.clientX, y: event.clientY, left: viewport.scrollLeft, top: viewport.scrollTop };
        viewport.setPointerCapture(event.pointerId); viewport.classList.add('doc-case-dragging'); event.preventDefault();
      });
      viewport.addEventListener('pointermove', event => { if (drag) { viewport.scrollLeft = drag.left + drag.x - event.clientX; viewport.scrollTop = drag.top + drag.y - event.clientY; } });
      const endDrag = () => { drag = null; viewport.classList.remove('doc-case-dragging'); };
      viewport.addEventListener('pointerup', endDrag); viewport.addEventListener('pointercancel', endDrag); viewport.addEventListener('lostpointercapture', endDrag);
      function message(text) { stage.replaceChildren(el('p', 'doc-case-image-message', text)); stage.style.width = ''; stage.style.height = ''; zoomLabel.textContent = '—'; }
      async function choose(asset, selectedPath) {
        const mine = ++token; release(); endDrag();
        for (const b of [fitButton, out, into, actual]) b.disabled = true;
        fields.replaceChildren();
        documentTools.replaceChildren(); documentTools.hidden = true;
        if (!asset) { caption.textContent = '此案例沒有素材'; message('沒有可檢視的素材。'); return; }
        const previews = asset.page_previews || [];
        const path = selectedPath && previews.includes(selectedPath) ? selectedPath : preferredPath(asset), file = bundle.files.get(path);
        if (previews.length) {
          const pages = el('select', 'doc-case-page'); pages.setAttribute('aria-label', label + ' 頁面預覽');
          previews.forEach((preview, i) => {
            const option = el('option', '', '第 ' + (i + 1) + ' 頁預覽' + (!bundle.files.has(preview) ? ' [缺檔]' : ''));
            option.value = preview; pages.append(option);
          });
          if (!previews.includes(path)) { const option = el('option', '', '預設檢視'); option.value = path; pages.prepend(option); }
          pages.value = path; pages.addEventListener('change', () => choose(asset, pages.value));
          documentTools.append(pages);
        }
        for (const [pdfPath, title] of [[asset.path, '開啟素材 PDF'], [asset.source_pdf_path, '開啟完整來源 PDF']]) {
          if (!pdfPath || !/\.pdf$/i.test(pdfPath) || (pdfPath === asset.path && title === '開啟完整來源 PDF')) continue;
          const originalFile = bundle.files.get(pdfPath);
          const open = button(title + (!originalFile ? ' [缺檔]' : ''), async () => {
            try { await options.onOpenFile(originalFile); }
            catch (error) { report('無法開啟 PDF：' + (error.message || '讀取失敗'), true); }
          });
          open.disabled = !originalFile || typeof options.onOpenFile !== 'function';
          open.title = pdfPath + (!originalFile ? '（所選資料夾內缺少此檔案）' : '');
          documentTools.append(open);
        }
        documentTools.hidden = !documentTools.children.length;
        caption.textContent = asset.caption + (asset.counted === false ? ' · 已排除，不納入採用數' : '');
        field(fields, '種類', kindLabel(asset.kind)); field(fields, '尺度', asset.scale_status || asset.dimensions_or_scale_notes);
        field(fields, '樑／構件', asset.beam_status); field(fields, '授權', asset.license || c.license);
        field(fields, '著作／攝影', asset.copyright_credit || asset.credit || asset.credits || c.copyright_credit);
        if (asset.catalog_description) field(fields, '典藏描述', asset.catalog_description);
        if (asset.catalog_caption) field(fields, '典藏標題', asset.catalog_caption);
        if (asset.license_evidence) field(fields, '授權證據', asset.license_evidence);
        field(fields, '原始像素（索引）', Array.isArray(asset.pixels) ? asset.pixels.join(' × ') : asset.pixels);
        field(fields, '素材檔案', asset.path);
        field(fields, '素材轉換', asset.transform || '索引未提供轉換紀錄');
        if (asset.source_pdf_path) field(fields, '完整來源檔案', asset.source_pdf_path);
        if (asset.source_page_number || asset.source_page_1based) field(fields, '來源頁碼', asset.source_page_number || asset.source_page_1based);
        field(fields, '檢視檔案', path);
        field(fields, '檢視轉換', path !== asset.path ? (asset.view_transform || '檢視副本；轉換方式未提供') : '直接檢視素材檔案');
        field(fields, '圖面人工檢視紀錄', asset.visual_audit === true ? '索引標示已檢視；本閱讀器未重新驗證' : '未提供已檢視紀錄');
        for (const [label, source] of [['素材來源 ↗', asset.figure_url || asset.source_page_url], ['來源檔案網址 ↗', asset.source_url], ['素材授權 ↗', asset.license_url], ['授權證據 ↗', asset.license_evidence_url]]) {
          const a = link(label, source); if (a) { const dd = el('dd'); dd.append(a); fields.append(el('dt', '', '外部來源'), dd); }
        }
        if (!file) { message('缺少本機檔案：' + path + '。請重新選取包含此檔案的資料夾；不會從來源網址下載。'); return; }
        if (/\.pdf$/i.test(path)) {
          message(typeof options.onOpenFile === 'function' ? '這是 PDF 文件，請使用上方「開啟素材 PDF」進入文件閱讀器。' : '這是 PDF 文件。請從文件閱讀器匯入此 PDF。');
          return;
        }
        if (/\.(?:dwg|dxf)$/i.test(path)) { message('目前不解析 DWG / DXF。請先由 CAD 軟體匯出 PDF 或靜態圖片，再加入案例索引。'); return; }
        if (!IMAGE_EXT.test(path)) { message('不直接解碼 TIFF 或其他不支援格式。請在索引 view_path 指定 JPG / PNG / WEBP 檢視副本。'); return; }
        if (file.size > LIMITS.imageBytes) { message('檔案超過 20 MB，已在解碼前拒絕。請提供較小的檢視副本。'); return; }
        message('正在檢查圖片標頭與像素上限…');
        try {
          const bytes = await file.arrayBuffer();
          if (isDead || destroyed || token !== mine) return;
          const checked = imageDimensions(bytes);
          // The browser sees only a verified local byte buffer, never a path or remote URL.
          url = URL.createObjectURL(new Blob([bytes], { type: checked.mime }));
          const img = el('img', 'doc-case-image'); image = img;
          img.alt = asset.caption; img.draggable = false; img.decoding = 'async';
          img.onload = () => {
            if (isDead || destroyed || token !== mine) return;
            const width = img.naturalWidth, height = img.naturalHeight;
            if (!width || !height || width * height > LIMITS.imagePixels || Math.max(width, height) > LIMITS.imageSide) { release(); message('瀏覽器解碼結果超過安全上限。'); return; }
            dims = { width, height }; fitMode = true; resize(true);
            field(fields, '檢視像素（標頭已檢查）', checked.width + ' × ' + checked.height);
            for (const b of [fitButton, out, into, actual]) b.disabled = false;
          };
          img.onerror = () => { if (!isDead && token === mine) { release(); message('圖片無法解碼；檔案可能損毀或編碼不受支援。'); } };
          stage.replaceChildren(img); img.src = url;
        } catch (error) { if (!isDead && !destroyed && token === mine) { release(); message(error.message || '圖片讀取失敗。'); } }
      }
      function populate(preferred) {
        assetSelect.replaceChildren();
        const items = c.assets.filter(a => matchesRole(a, kindSelect.value));
        for (const a of items) {
          const option = el('option', '', kindLabel(a.kind) + ' · ' + a.caption + (a.counted === false ? ' [已排除]' : '') + (!available(a) ? ' [缺檔]' : ''));
          option.value = a.id; assetSelect.append(option);
        }
        const next = items.find(a => a.id === preferred) || items[0];
        if (next) assetSelect.value = next.id;
        assetSelect.disabled = !next; choose(next);
      }
      kindSelect.addEventListener('change', () => populate(assetSelect.value));
      assetSelect.addEventListener('change', () => choose(c.assets.find(a => a.id === assetSelect.value)));
      panes.push({ destroy() { isDead = true; token++; release(); if (observer) observer.disconnect(); } });
      // Defer until the pane is in the document, so fit measures a real viewport.
      queueMicrotask(() => { if (!isDead && !destroyed) populate(initial && initial.id); });
      return pane;
    }

    function exportNotes() {
      if (!bundle) return;
      let text;
      try { text = serializeNotes(bundle, currentNotes()); }
      catch (error) { report('無法匯出筆記：' + error.message, true); return; }
      const url = URL.createObjectURL(new Blob([text], { type: 'application/json' })); downloads.add(url);
      const a = el('a'); a.href = url; a.download = 'geometry-case-notes-' + new Date().toISOString().slice(0, 10) + '.json';
      root.append(a); a.click(); a.remove();
      // A download click cannot prove that the file was saved. Retain the unload warning.
      setTimeout(() => { URL.revokeObjectURL(url); downloads.delete(url); }, 1000);
      report('已準備本機筆記 JSON 下載。請確認下載完成；重新整理或關閉網頁後不保留工作階段筆記。');
    }
    function showCase(c) {
      selectedCase = c; clearPanes(); renderList(); main.replaceChildren(); main.scrollTop = 0;
      const top = el('div', 'doc-case-case-heading');
      top.append(el('span', 'doc-case-eyebrow', c.id + ' · ' + display(c.tier, '分類未提供')), el('h3', '', c.title));
      if (c.geometry_notes) top.append(el('p', '', display(c.geometry_notes)));
      const confidence = el('p', 'doc-case-confidence', display(c.measurement_confidence, '尚無量測可信度資料；不要由圖片自行假定精確尺寸。'));
      top.append(confidence); main.append(top);
      const compare = el('div', 'doc-case-compare');
      const usable = c.assets.filter(a => a.counted !== false), pool = usable.length ? usable : c.assets;
      const left = pool.find(a => a.kind === 'plan') || pool[0];
      const right = pool.find(a => a.kind === 'section' && a !== left) || pool.find(a => a.kind === 'photo' && a !== left) || pool.find(a => a !== left) || left;
      compare.append(makePane(c, left, 'A'), makePane(c, right, 'B')); main.append(compare, caseEvidence(c));
      const noteSection = el('section', 'doc-case-notes');
      const noteHeading = el('div', 'doc-case-note-heading'); noteHeading.append(el('h4', '', '建模筆記'));
      noteHeading.append(button('匯入筆記', () => noteInput.click()), button('匯出筆記 JSON', exportNotes));
      const label = el('label', 'doc-case-note-label', '此案例的觀察、假設與待確認事項');
      const textarea = el('textarea', 'doc-case-note-input'); textarea.rows = 5; textarea.maxLength = LIMITS.noteLength;
      textarea.placeholder = '例如：可確認的幾何／尚缺的尺寸／預計用哪些物件與關係建模…';
      textarea.value = currentNotes().get(c.id)?.text || '';
      const hint = el('p', 'doc-case-note-hint', '切換文件／案例會保留筆記；重新整理或關閉網頁後清除。請匯出 JSON 備份，不會修改模型或來源檔。');
      textarea.addEventListener('input', () => {
        const previous = currentNotes(), next = new Map(previous);
        if (textarea.value.length > LIMITS.noteLength) {
          textarea.value = previous.get(c.id)?.text || '';
          report('每個案例筆記最多 20,000 字；此變更未儲存。', true); return;
        }
        if (textarea.value) next.set(c.id, { text: textarea.value, updatedAt: new Date().toISOString() });
        else next.delete(c.id);
        try { serializeNotes(bundle, next); }
        catch (error) { textarea.value = previous.get(c.id)?.text || ''; report(error.message, true); return; }
        notes.set(bundle.key, next);
        unexportedNotes.add(bundle.key);
        hint.textContent = '本次工作階段已保留 · ' + textarea.value.length + ' / ' + LIMITS.noteLength + ' 字。關閉前請匯出 JSON。';
      });
      label.append(textarea); noteSection.append(noteHeading, label, hint); main.append(noteSection);
    }

    async function importFiles(fileList) {
      if (destroyed) return false;
      const mine = ++importToken;
      report('正在檢查本機案例索引…');
      try {
        const indexed = indexFiles(fileList), text = await indexed.manifest.text();
        if (destroyed || mine !== importToken) return false;
        if (new TextEncoder().encode(text).byteLength > LIMITS.manifestBytes) fail('案例索引超過 4 MB。');
        const validated = validateManifest(JSON.parse(text));
        const key = await fingerprint(text);
        if (destroyed || mine !== importToken) return false;
        clearPanes();
        bundle = { ...indexed, ...validated, key }; search.value = '';
        const missing = bundle.cases.reduce((n, c) => n + c.assets.filter(a => !available(a)).length, 0);
        showCase(bundle.cases[0]);
        report('已開啟 ' + bundle.name + '：' + bundle.cases.length + ' 個案例、' + bundle.assetCount + ' 筆素材' + (missing ? '，' + missing + ' 筆缺少本機檢視檔案。' : '。') + ' 索引證據未經本閱讀器重新驗證。');
        return true;
      } catch (error) {
        if (!destroyed && mine === importToken) report('無法開啟案例資料夾：' + (error.message || '索引無效'), true);
        return false;
      }
    }
    async function importNotes(file) {
      if (!file || !bundle) return false;
      const key = bundle.key;
      try {
        if (file.size > LIMITS.notesBytes) fail('筆記 JSON 超過 2 MB。');
        const text = await file.text();
        if (new TextEncoder().encode(text).byteLength > LIMITS.notesBytes) fail('筆記 JSON 超過 2 MB。');
        const parsed = safeJSON(JSON.parse(text));
        if (destroyed || !bundle || bundle.key !== key) return false;
        if (!plain(parsed) || parsed.schema !== 'geometry-case-notes/1' || parsed.bundleId !== key || !Array.isArray(parsed.notes) || parsed.notes.length > LIMITS.cases) fail('筆記格式或案例索引身份不符；請使用此資料夾匯出的筆記。');
        const incoming = new Map(), known = new Set(bundle.cases.map(c => c.id));
        for (const row of parsed.notes) {
          if (!plain(row) || !known.has(row.caseId) || incoming.has(row.caseId) || typeof row.text !== 'string' || row.text.length > LIMITS.noteLength) fail('筆記包含重複、未知案例或過長內容。');
          incoming.set(row.caseId, { text: row.text, updatedAt: typeof row.updatedAt === 'string' ? row.updatedAt.slice(0, 100) : new Date().toISOString() });
        }
        const current = currentNotes();
        for (const [id, value] of incoming) if (current.has(id) && current.get(id).text !== value.text) fail('案例 ' + id + ' 已有不同筆記；為避免覆寫，整份匯入已取消。請先匯出現有筆記。');
        const merged = new Map(current);
        for (const [id, value] of incoming) if (value.text) merged.set(id, value);
        serializeNotes(bundle, merged); notes.set(key, merged);
        if (incoming.size) unexportedNotes.add(key);
        showCase(selectedCase); report('已合併 ' + incoming.size + ' 筆工作階段筆記；仍需匯出 JSON 才能保留。'); return true;
      } catch (error) { report('無法匯入筆記：' + error.message, true); return false; }
    }
    folderInput.addEventListener('change', () => { const files = Array.from(folderInput.files || []); folderInput.value = ''; if (files.length) importFiles(files); });
    noteInput.addEventListener('change', () => { const file = noteInput.files[0]; noteInput.value = ''; if (file) importNotes(file); });
    search.addEventListener('input', renderList);
    const api = {
      importFiles, importNotes,
      destroy() {
        if (destroyed) return;
        destroyed = true; importToken++; clearPanes();
        for (const url of downloads) URL.revokeObjectURL(url);
        downloads.clear(); bundle = null; selectedCase = null; root.remove();
        if (active === api) active = null;
      }
    };
    active = api; return api;
  }
  const api = Object.freeze({ mount, importFiles: files => active ? active.importFiles(files) : Promise.resolve(false),
    destroy: () => { if (active) active.destroy(); },
    helpers: Object.freeze({ normalizePath, safeURL, safeJSON, validateManifest, matchesRole, roleOptions, imageDimensions, indexFiles, serializeNotes, limits: LIMITS }) });
  global.DocumentCases = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
