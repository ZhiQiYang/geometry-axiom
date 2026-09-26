/* GEO-198: portable reference data. Geometry remains the bridge's .scene. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryProject = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const FORMAT = "geometry-canvas/1", MAX_SOURCE = 128 * 1024 * 1024;
  const MAX_PACKAGE = 256 * 1024 * 1024, MAX_EXPANDED = 512 * 1024 * 1024;
  const TYPES = new Set(["application/pdf", "image/png", "image/jpeg", "image/webp", "image/gif"]);
  const hashRE = /^[a-f0-9]{64}$/;
  const copy = x => JSON.parse(JSON.stringify(x));
  const fail = message => { throw new Error(message); };
  const finite = (n, lo, hi) => typeof n === "number" && Number.isFinite(n) && n >= lo && n <= hi;
  const str = (v, max = 1000) => typeof v === "string" && v.length <= max;
  const id = v => typeof v === "string" && /^[\w-]{1,100}$/.test(v);
  const pt = p => Array.isArray(p) && p.length === 2 && p.every(n => finite(n, 0, 1e7));
  async function sha(bytes) {
    return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", bytes)), b => b.toString(16).padStart(2, "0")).join("");
  }
  function validate(m) {
    if (!m || m.format !== FORMAT) fail("專案版本不支援，請使用相容版本開啟。");
    if (!id(m.projectId) || !str(m.name, 200) || !hashRE.test(m.sceneHash)) fail("專案資訊不完整。");
    if (!Array.isArray(m.sources) || m.sources.length > 256 || !Array.isArray(m.faces) || m.faces.length > 10000) fail("專案資料數量不合法。");
    const sources = new Map(), refs = new Set(), faces = new Set();
    for (const s of m.sources) {
      if (!s || !hashRE.test(s.id) || s.id !== s.hash || sources.has(s.id) || !str(s.name, 500) || !TYPES.has(s.type) ||
          !Number.isSafeInteger(s.size) || s.size < 1 || s.size > MAX_SOURCE || s.path !== "sources/" + s.id) fail("來源檔案清單不合法。");
      sources.set(s.id, s);
    }
    for (const f of m.faces) {
      if (!f || !Number.isInteger(f.bid) || f.bid < 1 || f.bid > 4294967295 || faces.has(f.bid) ||
          !Array.isArray(f.pages) || !f.pages.length || f.pages.length > 500) fail("面的來源關聯不合法。");
      faces.add(f.bid);
      for (const p of f.pages) {
        if (!p || !id(p.id) || refs.has(p.id) || !sources.has(p.sourceId) || !Number.isInteger(p.page) || p.page < 1 || p.page > 100000 ||
            !finite(p.imgW, 1, 1e7) || !finite(p.imgH, 1, 1e7) || !finite(p.mmPerPx, 1e-9, 1e8) ||
            !finite(p.x, -1e8, 1e8) || !finite(p.y, -1e8, 1e8) || ![0,90,180,270].includes(p.rot) ||
            !finite(p.opacity, 0, 1) || typeof p.locked !== "boolean" || typeof p.reviewRequired !== "boolean") fail("圖頁對位資料不合法。");
        refs.add(p.id);
        const c = p.crop;
        if (!Array.isArray(c) || c.length !== 4 || !c.every(Number.isFinite) || c[0] < 0 || c[1] < 0 || c[2] <= 0 || c[3] <= 0 ||
            c[0] + c[2] > p.imgW + 0.001 || c[1] + c[3] > p.imgH + 0.001) fail("圖頁取景範圍不合法。");
        if (sources.get(p.sourceId).type !== "application/pdf" && p.page !== 1) fail("圖片只能使用第 1 頁。");
        if (p.calibration !== null) {
          const q = p.calibration;
          if (!q || !Array.isArray(q.points) || q.points.length !== 2 || !q.points.every(pt) ||
              q.points.some(v => v[0] > p.imgW || v[1] > p.imgH) || !Number.isSafeInteger(q.distanceMm) || !finite(q.distanceMm, 1, 1e8) ||
              !finite(q.inputValue, 1e-9, 1e8) || !["mm", "cm"].includes(q.inputUnit)) fail("校準紀錄不合法。");
          const d = Math.hypot(q.points[0][0] - q.points[1][0], q.points[0][1] - q.points[1][1]);
          if (!(d > 0) || Math.abs(q.distanceMm / d - p.mmPerPx) > 1e-8 * p.mmPerPx ||
              Math.abs(q.inputValue * (q.inputUnit === "cm" ? 10 : 1) - q.distanceMm) > 1e-7) fail("校準紀錄與比例不一致。");
        }
        if (!Array.isArray(p.records) || p.records.length > 1000) fail("來源紀錄不合法。");
        const recordIds = new Set();
        for (const r of p.records) {
          if (!r || !id(r.id) || recordIds.has(r.id) || !str(r.label, 300) || !str(r.location, 1000) || !str(r.datum, 300) ||
              !["mm", "cm"].includes(r.unit) || !(r.value === null || finite(r.value, -1e8, 1e8))) fail("來源紀錄欄位不合法。");
          recordIds.add(r.id);
        }
      }
      if (!f.pages.some(p => p.id === f.activePageId)) fail("目前顯示的圖頁不存在。");
    }
    return m;
  }
  function reference(p) {
    const keys = ["id","sourceId","page","imgW","imgH","crop","mmPerPx","x","y","rot","opacity","locked","calibration","reviewRequired","records"];
    return Object.fromEntries(keys.map(k => [k, copy(p[k])]));
  }
  async function pack(scene, manifest, sources, zip) {
    const sceneBytes = new TextEncoder().encode(scene);
    const m = { ...copy(manifest), format: FORMAT, sceneHash: await sha(sceneBytes) };
    validate(m);
    const entries = { "world.scene": sceneBytes, "manifest.json": new TextEncoder().encode(JSON.stringify(m)) };
    for (const s of m.sources) {
      const bytes = sources.get(s.id);
      if (!(bytes instanceof Uint8Array) || bytes.length !== s.size || await sha(bytes) !== s.hash) fail("來源檔案已遺失或變更：" + s.name);
      entries[s.path] = bytes;
    }
    const total = Object.values(entries).reduce((n,b) => n + b.length, 0);
    if (total > MAX_EXPANDED) fail("專案過大，請拆成較小的專案。");
    const bytes = await new Promise((resolve, reject) => zip.zip(entries, { level: 0 }, (e,d) => e ? reject(e) : resolve(d)));
    if (bytes.length > MAX_PACKAGE) fail("專案超過 256 MB，請減少來源檔案。");
    return bytes;
  }
  async function unpack(bytes, zip) {
    if (!(bytes instanceof Uint8Array) || bytes.length > MAX_PACKAGE) fail("專案檔案超過 256 MB。");
    let total = 0, count = 0;
    // A bounded streaming decoder prevents trusting forged ZIP size headers.
    const entries = Object.create(null);
    await new Promise((resolve, reject) => {
      let pending = 0, ended = false, failed = false;
      const die = e => { failed = true; reject(e); };
      const done = () => { if (ended && pending === 0 && !failed) resolve(); };
      const unzip = new zip.Unzip(file => {
        if (failed) return;
        if (++count > 2048 || Object.hasOwn(entries, file.name) ||
            !/^(manifest\.json|world\.scene|sources\/[a-f0-9]{64})$/.test(file.name)) return die(new Error("專案內含重複或不支援的檔案。"));
        entries[file.name] = null; pending++;
        let size = 0; const chunks = [];
        const limit = file.name === "manifest.json" ? 8 * 1024 * 1024 : file.name === "world.scene" ? 16 * 1024 * 1024 : MAX_SOURCE;
        file.ondata = (err, data, final) => {
          if (failed) { file.terminate?.(); return; }
          if (err) return die(err);
          size += data.length; total += data.length;
          if (size > limit || total > MAX_EXPANDED) { file.terminate?.(); return die(new Error("專案解壓縮後超過大小上限。")); }
          chunks.push(data);
          if (final) { const result = new Uint8Array(size); let pos = 0; for (const c of chunks) { result.set(c, pos); pos += c.length; }
            entries[file.name] = result; pending--; done(); }
        };
        file.start();
      });
      unzip.register(zip.UnzipInflate);
      try {
        // Feed bounded chunks so a forged uncompressed size cannot force a giant single allocation.
        for (let at = 0; at < bytes.length && !failed; at += 65536)
          unzip.push(bytes.subarray(at, at + 65536), at + 65536 >= bytes.length);
        if (!bytes.length) unzip.push(bytes, true);
        ended = true; done();
      } catch (e) { die(e); }
    });
    if (!entries["manifest.json"] || !entries["world.scene"]) fail("專案缺少清單或場景。");
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const m = validate(JSON.parse(decoder.decode(entries["manifest.json"])));
    if (await sha(entries["world.scene"]) !== m.sceneHash) fail("場景完整性檢查失敗。");
    const sources = new Map();
    for (const s of m.sources) {
      const data = entries[s.path];
      if (!data || data.length !== s.size || await sha(data) !== s.hash) fail("來源檔案完整性檢查失敗：" + s.name);
      sources.set(s.id, data);
    }
    if (Object.keys(entries).length !== m.sources.length + 2) fail("專案含有未列入清單的檔案。");
    return { manifest: m, scene: decoder.decode(entries["world.scene"]), sources };
  }
  // Only metadata contexts and boundary incarnation ids, never geometry snapshots.
  class ContextHistory {
    constructor(makeContext, limit = 32) {
      this.makeContext = makeContext; this.limit = limit; this.undo = []; this.redo = []; this.group = null;
      this.frame = { context: makeContext(), ids: new Map() };
    }
    snapshot() { return { context: this.frame.context, ids: new Map(this.frame.ids) }; }
    push(frame) { this.undo.push(frame); if (this.undo.length > this.limit) this.undo.shift(); this.redo = []; }
    sync(ids) {
      const live = new Set(ids);
      for (const bid of this.frame.ids.keys()) if (!live.has(bid)) this.frame.ids.delete(bid);
      for (const bid of live) if (!this.frame.ids.has(bid)) this.frame.ids.set(bid, globalThis.crypto.randomUUID());
    }
    replace(context, ids) {
      this.push(this.snapshot()); this.group = null;
      this.frame = { context, ids: new Map(ids || []) };
    }
    observe(command, result) {
      if (command === "objects" && result.ok && Array.isArray(result.faces)) { this.sync(result.faces.filter(f => f.kind === "boundary").map(f => f.id)); return; }
      if (!/^(line |drag |reset$|default$|loadfile )/.test(command)) return;
      const op = command.startsWith("line ") ? command.slice(5).trim().split(/\s+/)[0] : command.split(/\s+/)[0];
      if (!result.ok) {
        // A preview rejection preserves the core's open group; other failures roll it back.
        if (this.group && !result.preview && op !== "history-begin" && op !== "loadfile") {
          this.frame = this.group.base; this.group = null;
        }
        return;
      }
      if (op === "canvas-pos" || op === "preview" || op === "cancel-preview") return;
      if (op === "history-begin") { this.group = { base: this.snapshot(), dirty: false }; return; }
      if (op === "history-abort") { if (this.group) this.frame = this.group.base; this.group = null; return; }
      if (op === "history-end") { if (this.group?.dirty) this.push(this.group.base); this.group = null; return; }
      if (op === "undo" || op === "redo") {
        const from = op === "undo" ? this.undo : this.redo, to = op === "undo" ? this.redo : this.undo;
        if (from.length) { to.push(this.snapshot()); if (to.length > this.limit) to.shift(); this.frame = from.pop(); }
        else { this.frame = { context: this.makeContext(), ids: new Map() }; } // history predating this browser session
        this.group = null; return;
      }
      if (command === "reset" || command === "default") { this.undo = []; this.redo = []; this.group = null; }
      else if (this.group) this.group.dirty = true;
      else this.push(this.snapshot());
      if (op === "reset" || op === "default" || op === "loadfile") this.frame = { context: this.makeContext(), ids: new Map() };
      // A batch may recreate a deleted id before the next objects refresh.
      // Retire the old incarnation at the successful delete, not at render time.
      const deletion = command.match(/^line\s+delete\s+boundary\s+(\d+)(?:\s|$)/);
      if (deletion) this.frame.ids.delete(+deletion[1]);
      const birth = command.match(/^line\s+(?:boundary|surface)\s+(\d+)\s/);
      if (birth && !this.frame.ids.has(+birth[1])) this.frame.ids.set(+birth[1], globalThis.crypto.randomUUID());
    }
  }
  return { FORMAT, MAX_SOURCE, MAX_PACKAGE, TYPES, sha, validate, reference, pack, unpack, ContextHistory };
});
