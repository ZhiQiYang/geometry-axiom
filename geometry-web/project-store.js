/* GEO-198: portable reference data. Geometry remains the bridge's .scene. */
(function (root, factory) {
  const api = factory(typeof module === "object" && module.exports ? require("./feature-attachments.js") : root.GeometryFeatureAttachments);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryProject = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (Features) {
  "use strict";
  const FORMAT = "geometry-canvas/1", MODEL_FORMAT = "geometry-canvas/2", PROJECTION_FORMAT = "geometry-canvas/3", TIMBER_FORMAT = "geometry-canvas/4", ENGINEERING_FORMAT = "geometry-canvas/5", MAX_SOURCE = 128 * 1024 * 1024;
  const ASSEMBLY_FORMAT = "geometry-canvas/7", ASSEMBLY_CAPABILITY = "assembly-rule-authoring/1", ASSEMBLY_DRAFT_SCHEMA = "assembly-drafts/1";
  const OUTLINE_FORMAT = "geometry-canvas/9";
  const FEATURE_FORMAT = "geometry-canvas/10";
  const GENERATION_FORMAT="geometry-canvas/8", GENERATION_CAPABILITY="assembly-timber-generation/1";
  const PARAMETER_FORMAT = "geometry-canvas/6", PARAMETER_CAPABILITY = "parameters/1";
  const ENGINEERING_CAPABILITY = "engineering-spec/1", DRAFT_SCHEMA = "engineering-drafts/1", MAX_ENGINEERING_DRAFTS = 256;
  const MAX_MANIFEST = 8 * 1024 * 1024, MAX_MODELS = 64;
  const MAX_PACKAGE = 256 * 1024 * 1024, MAX_EXPANDED = 512 * 1024 * 1024;
  const TYPES = new Set(["application/pdf", "image/png", "image/jpeg", "image/webp", "image/gif"]);
  const hashRE = /^[a-f0-9]{64}$/;
  const copy = x => JSON.parse(JSON.stringify(x));
  const fail = message => { throw new Error(message); };
  const finite = (n, lo, hi) => typeof n === "number" && Number.isFinite(n) && n >= lo && n <= hi;
  const str = (v, max = 1000) => typeof v === "string" && v.length <= max;
  const id = v => typeof v === "string" && /^[\w-]{1,100}$/.test(v);
  const pt = p => Array.isArray(p) && p.length === 2 && p.every(n => finite(n, 0, 1e7));
  const object = v => !!v && typeof v === "object" && !Array.isArray(v);
  const uint = v => Number.isSafeInteger(v) && v >= 0 && v <= 4294967295;
  function keys(value, required, optional = []) {
    return object(value) && required.every(k => Object.hasOwn(value, k)) &&
      Object.keys(value).every(k => required.includes(k) || optional.includes(k));
  }
  function validateFaceProjection(projection) {
    if (!keys(projection, ["kind", "view", "region", "wallSide"]) || projection.kind !== "space-boundary-plan" ||
        !["top", "bottom"].includes(projection.view) || projection.region !== "interior" || projection.wallSide !== "outside")
      fail("面的平面投影定義不合法。");
    return projection;
  }
  const positiveId = v => uint(v) && v > 0;
  function validateFaceProjectionList(records) {
    if (!Array.isArray(records) || records.length > 10000) fail("平面投影定義清單不合法。");
    const pairs = new Set();
    for (const record of records) {
      if (!keys(record, ["bid", "placement_id", "projection"]) || !positiveId(record.bid) || !uint(record.placement_id)) fail("面的平面投影關聯不合法。");
      validateFaceProjection(record.projection);
      const key = record.bid + ":" + record.placement_id;
      if (pairs.has(key)) fail("面的平面投影關聯重複。");
      pairs.add(key);
    }
  }
  const horizontalAxes = (u, v) => /^[+-][xy]$/.test(u) && /^[+-][xy]$/.test(v) && u[1] !== v[1];
  // Read only the declaration references needed by metadata. The bridge remains
  // responsible for validating geometry and commits the scene transactionally.
  function sceneProjectionRefs(scene) {
    const boundaries = new Set(), placements = new Map();
    for (const raw of scene.replace(/\r\n/g, "\n").split("\n")) {
      const line = raw.trim();
      if (/^(reset|default)$/.test(line)) { boundaries.clear(); placements.clear(); continue; }
      const deletion = line.match(/^delete\s+(boundary|placement)\s+(\d+)(?:\s|$)/);
      if (deletion) { (deletion[1] === "boundary" ? boundaries : placements).delete(+deletion[2]); continue; }
      const boundary = line.match(/^(?:boundary|surface)\s+(\d+)\s/);
      if (boundary) boundaries.add(+boundary[1]);
      const declaration = line.match(/^(placement|surface)\s+(\d+)\s/);
      if (!declaration) continue;
      const id = +declaration[2], ref = declaration[1] === "surface" ? id : +(line.match(/\bon\s+boundary\s+(\d+)\b/)?.[1] || 0);
      const axes = line.match(/\bu\s+([+-][xyz])\s+v\s+([+-][xyz])(?:\s|$)/);
      placements.set(id, { bid: ref, horizontal: !!axes && horizontalAxes(axes[1], axes[2]) });
    }
    return { boundaries, placements };
  }
  function validateFaceProjectionRefs(records, scene) {
    const refs = sceneProjectionRefs(scene);
    for (const record of records) {
      const placement = refs.placements.get(record.placement_id);
      if (!refs.boundaries.has(record.bid) || placement?.bid !== record.bid) fail("平面投影關聯的面或放置不存在於場景。");
      if (!placement.horizontal) fail("平面投影必須關聯水平放置面。");
    }
  }
  function validateProjectObjectRefs(manifest, objects) {
    if (!objects || !Array.isArray(objects.boundaries) || !Array.isArray(objects.placements) ||
        !objects.boundaries.every(positiveId) || !objects.placements.every(p =>
          keys(p,["id","bid","horizontal"]) && uint(p.id) && uint(p.bid) && typeof p.horizontal === "boolean"))
      fail("服務未提供完整的原生候選物件清單，未變更目前專案。");
    const boundaries = new Set(objects.boundaries), placements = new Map(objects.placements.map(p => [p.id,p]));
    for (const face of manifest.faces) if (!boundaries.has(face.bid)) fail("來源關聯的面不存在於原生候選場景。");
    for (const record of manifest.reconstructionReviews || []) if (!boundaries.has(record.bid)) fail("輪廓核對收據的面不存在於原生候選場景。");
    for (const record of manifest.faceProjections || []) {
      const placement = placements.get(record.placement_id);
      if (!boundaries.has(record.bid) || placement?.bid !== record.bid) fail("平面投影關聯的面或放置不存在於原生候選場景。");
      if (!placement.horizontal) fail("平面投影必須關聯水平放置面。");
    }
  }
  function sceneCapabilities(scene) {
    const result = new Set();
    for (const raw of scene.replace(/\r\n/g, "\n").split("\n")) {
      const line = raw.split("#", 1)[0].trim();
      if (/^engineering(?:\s|$)/.test(line) || /(?:^|\s)eng:/.test(line)) result.add(ENGINEERING_CAPABILITY);
      if (/^parameters(?:\s|$)/.test(line) || /(?:^|[^\w])param:\d+:\d+/.test(line)) result.add(PARAMETER_CAPABILITY);
      if (/^owned(?:\s|$)/.test(line)) result.add(GENERATION_CAPABILITY);
      if (/^assembly(?:\s|$)/.test(line)) result.add(ASSEMBLY_CAPABILITY);
      const requires = line.match(/^requires\s+(.+)$/);
      if (requires) {
        if (![ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, ASSEMBLY_CAPABILITY, GENERATION_CAPABILITY].includes(requires[1])) fail("場景需要尚未支援的工程能力。");
        result.add(requires[1]);
      }
    }
    return [...result].sort();
  }
  function modelRequiresEngineering(model) {
    return sceneCapabilities(model.input?.base_scene || "").length || Object.values(model.result || {}).some(pkg =>
      pkg?.manifest?.capabilities?.includes(ENGINEERING_CAPABILITY) ||
      (typeof pkg?.definitions?.base_scene === "string" && sceneCapabilities(pkg.definitions.base_scene).length));
  }
  function projectFormat(manifest, scene = "") {
    if (Object.hasOwn(manifest, "featureAttachments") && Features.validate(manifest.featureAttachments).records.length) return FEATURE_FORMAT;
    if (manifest.reconstructionReviews?.length) return OUTLINE_FORMAT;
    if (projectCapabilities(manifest, scene).includes(GENERATION_CAPABILITY)) return GENERATION_FORMAT;
    if (projectCapabilities(manifest, scene).includes(ASSEMBLY_CAPABILITY)) return ASSEMBLY_FORMAT;
    if (projectCapabilities(manifest, scene).includes(PARAMETER_CAPABILITY)) return PARAMETER_FORMAT;
    if (manifest.requiredCapabilities?.length || manifest.engineeringDrafts?.records?.length ||
        sceneCapabilities(scene).length || manifest.models?.some(modelRequiresEngineering)) return ENGINEERING_FORMAT;
    if (manifest.models?.some(model => Object.hasOwn(model.input || {}, "timbers") || model.result?.schema === "geometry-space-preview/2")) return TIMBER_FORMAT;
    return manifest.faceProjections?.length || manifest.models?.some(model => Object.hasOwn(model.source, "projection"))
      ? PROJECTION_FORMAT : manifest.models?.length ? MODEL_FORMAT : FORMAT;
  }
  function validateEngineeringDraft(record) {
    jsonData(record);
    if (!keys(record, ["id", "kind", "base_ref", "data", "updated_at"]) || !id(record.id) ||
        !["material", "method", "application"].includes(record.kind) || !object(record.data) ||
        !str(record.updated_at, 100) || !Number.isFinite(Date.parse(record.updated_at))) fail("工程規格草稿不合法。");
    const ref = record.base_ref;
    if (ref !== null && (!keys(ref, ["id", "version", "fingerprint"]) || !id(ref.id) || ref.id.length > 64 ||
        !positiveId(ref.version) || !hashRE.test(ref.fingerprint))) fail("工程規格草稿的原始版本不合法。");
    if (new TextEncoder().encode(JSON.stringify(record)).length > 256 * 1024) fail("單份工程規格草稿超過 256 KB。");
    return record;
  }
  function validateEngineeringDrafts(drafts) {
    if (!keys(drafts, ["schema", "records"]) || drafts.schema !== DRAFT_SCHEMA ||
        !Array.isArray(drafts.records) || drafts.records.length > MAX_ENGINEERING_DRAFTS) fail("工程規格草稿版本或清單不合法。");
    const ids = new Set();
    for (const record of drafts.records) {
      validateEngineeringDraft(record);
      if (ids.has(record.id)) fail("工程規格草稿 ID 重複。");
      ids.add(record.id);
    }
    return drafts;
  }
  function validateAssemblyDraft(record) {
    jsonData(record);
    if (!keys(record, ["id", "kind", "base_ref", "data", "updated_at"], ["binding_intent"]) || !id(record.id) ||
        !["rule", "binding", "instance"].includes(record.kind) || !object(record.data) ||
        !str(record.updated_at, 100) || !Number.isFinite(Date.parse(record.updated_at))) fail("組構草稿不合法。");
    const ref = record.base_ref;
    if (ref !== null && (!keys(ref, record.kind==="instance"?["id","fingerprint"]:["id", "version", "fingerprint"]) || !positiveId(ref.id) ||
        (record.kind!=="instance"&&!positiveId(ref.version)) || !hashRE.test(ref.fingerprint))) fail("組構草稿的固定版本不合法。");
    if (Object.hasOwn(record, 'binding_intent')) {
      const intent=record.binding_intent;
      if(record.kind!=='binding'||!object(intent)||
        !(intent.mode==='create'&&keys(intent,['mode'])||intent.mode==='update'&&keys(intent,['mode','source'])))fail('組構配置草稿的操作意圖不合法。');
      if(intent.mode==='update'){
        validateAssemblyDraft({...record,data:intent.source,binding_intent:{mode:'create'}});
        if(intent.source.id!==record.data.id)fail('組構配置草稿的原始身分不一致。');
      }
    }
    if (new TextEncoder().encode(JSON.stringify(record)).length > 256 * 1024) fail("單份組構草稿超過 256 KB。");
    const d=record.data, list=(a,n,check)=>Array.isArray(a)&&a.length<=n&&a.every(check);
    const source=v=>v===null || object(v)&&(
      v.kind==='literal'&&keys(v,['kind','value'])&&(typeof v.value==='string'||Number.isSafeInteger(v.value)) ||
      v.kind==='spec'&&keys(v,['kind','name'])&&str(v.name,100) ||
      v.kind==='parameter'&&keys(v,['kind','parameterId','fieldId'])&&uint(v.parameterId)&&uint(v.fieldId) ||
      v.kind==='material'&&keys(v,['kind','id','version','field'])&&id(v.id)&&positiveId(v.version)&&['A','B'].includes(v.field));
    if(record.kind==='rule'){
      const joint=j=>keys(j,j.kind==='end-to-side'?['id','kind','scope','terminatedMember','targetMember','end','side','dir']:['id','kind','scope','continuousMember','splitMembers','side','dir'])&&positiveId(j.id)&&str(j.scope,256)&&['+u','-u','+v','-v'].includes(j.side)&&['u','v'].includes(j.dir)&&
        (j.kind==='end-to-side'?positiveId(j.terminatedMember)&&positiveId(j.targetMember)&&['start','finish'].includes(j.end):j.kind==='ortho-split'&&positiveId(j.continuousMember)&&Array.isArray(j.splitMembers)&&j.splitMembers.length===2&&j.splitMembers.every(positiveId));
      if(!keys(d,['id','version','name','slots','members','joints'])||!positiveId(d.id)||!positiveId(d.version)||!str(d.name,256)||
        !list(d.slots,8,v=>keys(v,['id','name'])&&positiveId(v.id)&&str(v.name,256))||
        !list(d.members,12,v=>keys(v,['id','slotId'])&&positiveId(v.id)&&positiveId(v.slotId))||!list(d.joints,16,joint))fail('組構規則草稿結構不合法。');
    }else if(record.kind==='instance'){
      const endpoint=v=>object(v)&&((v.kind==='timber'&&keys(v,['kind','id'])&&uint(v.id))||(v.kind==='member'&&keys(v,['kind','memberId'])&&positiveId(v.memberId)));
      if(!keys(d,['id','name','bindingId','rule','surfaceId','members'])||!positiveId(d.id)||!str(d.name,256)||!positiveId(d.bindingId)||!uint(d.surfaceId)||!keys(d.rule,['id','version','fingerprint'])||!positiveId(d.rule.id)||!positiveId(d.rule.version)||!hashRE.test(d.rule.fingerprint)||!list(d.members,3,v=>keys(v,['memberId','role','guideId','dir','depthSide','ends'])&&positiveId(v.memberId)&&['primary','secondary'].includes(v.role)&&uint(v.guideId)&&['+u','+v'].includes(v.dir)&&v.depthSide==='+n'&&keys(v.ends,['start','finish'])&&endpoint(v.ends.start)&&endpoint(v.ends.finish)))fail('組構實例草稿結構不合法。');
    }else if(!keys(d,['id','name','rule','slots'])||!positiveId(d.id)||!str(d.name,256)||!keys(d.rule,['id','version'])||!positiveId(d.rule.id)||!positiveId(d.rule.version)||
      !list(d.slots,8,v=>keys(v,['slotId','A','B','contactFace','orientation'])&&positiveId(v.slotId)&&source(v.A)&&source(v.B)&&[null,'A','B'].includes(v.contactFace)&&[null,'A','B'].includes(v.orientation)))fail('組構配置草稿結構不合法。');
    return record;
  }
  function validateAssemblyDrafts(drafts) {
    if (!keys(drafts, ["schema", "records"]) || drafts.schema !== ASSEMBLY_DRAFT_SCHEMA ||
        !Array.isArray(drafts.records) || drafts.records.length > 256) fail("組構草稿版本或清單不合法。");
    const ids = new Set();
    for (const record of drafts.records) {
      validateAssemblyDraft(record);
      if (ids.has(record.id)) fail("組構草稿 ID 重複。");
      ids.add(record.id);
    }
    return drafts;
  }
  function validateProjectCapabilities(capabilities) {
    if (!Array.isArray(capabilities) || capabilities.length > 4 || new Set(capabilities).size !== capabilities.length ||
        capabilities.some(capability => ![ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, ASSEMBLY_CAPABILITY, GENERATION_CAPABILITY].includes(capability))) fail("專案需要尚未支援的工程能力。");
    return capabilities;
  }
  function assertProjectCapabilities(manifest, available) {
    const required = manifest.requiredCapabilities || [];
    validateManifestCapabilities(required);
    if (!Array.isArray(available) || required.some(capability => !available.includes(capability)))
      fail("目前服務不支援此專案所需的工程規格能力，未變更目前專案。");
  }
  // Editor capabilities are checked by this reader, never advertised as native
  // scene or model-producer capabilities.
  function validateManifestCapabilities(capabilities) {
    if (!Array.isArray(capabilities) || capabilities.length > 5 || new Set(capabilities).size !== capabilities.length ||
        capabilities.some(capability => ![ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, ASSEMBLY_CAPABILITY, GENERATION_CAPABILITY, Features.GRID_SCHEMA].includes(capability)))
      fail("專案需要尚未支援的能力。");
    return capabilities;
  }
  function readerCapabilities(nativeCapabilities) {
    validateProjectCapabilities(nativeCapabilities);
    return [...nativeCapabilities, Features.GRID_SCHEMA];
  }
  function projectCapabilities(manifest, scene) {
    const required = new Set([...(manifest.requiredCapabilities || []), ...sceneCapabilities(scene)]);
    if (Object.hasOwn(manifest, "featureAttachments")) for (const capability of Features.capabilities(manifest.featureAttachments)) required.add(capability);
    if (manifest.assemblyDrafts?.records?.length) required.add(ASSEMBLY_CAPABILITY);
    if (manifest.assemblyDrafts?.records?.some(r=>r.kind==="instance")) required.add(GENERATION_CAPABILITY);
    for (const model of manifest.models || []) {
      for (const c of sceneCapabilities(model.input?.base_scene || "")) required.add(c);
      for (const pkg of Object.values(model.result || {})) {
        for (const c of pkg?.manifest?.capabilities || []) if ([ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, ASSEMBLY_CAPABILITY, GENERATION_CAPABILITY].includes(c)) required.add(c);
        for (const c of sceneCapabilities(pkg?.definitions?.base_scene || "")) required.add(c);
      }
    }
    return [...required].sort();
  }
  function validateEngineeringScene(manifest, scene) {
    const needed = projectCapabilities({...manifest, requiredCapabilities: []}, scene);
    if (manifest.format === FEATURE_FORMAT && !manifest.featureAttachments?.records.length) fail("第 10 版專案缺少功能附件。");
    if (manifest.requiredCapabilities?.includes(Features.GRID_SCHEMA) && !needed.includes(Features.GRID_SCHEMA)) fail("網格草稿能力缺少對應附件。");
    if(manifest.format===GENERATION_FORMAT&&!manifest.requiredCapabilities?.includes(GENERATION_CAPABILITY))fail("第 8 版專案缺少組構生成能力。");
    if (needed.some(c => !manifest.requiredCapabilities?.includes(c)) ||
        (needed.includes(Features.GRID_SCHEMA) && manifest.format !== FEATURE_FORMAT) ||
        (needed.includes(PARAMETER_CAPABILITY) && ![PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(manifest.format)) ||
        (needed.includes(ASSEMBLY_CAPABILITY) && ![ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(manifest.format)) ||
        (needed.includes(GENERATION_CAPABILITY) && ![GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(manifest.format)) ||
        (needed.length && ![ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(manifest.format)))
      fail("含參數的專案必須使用第 6 版，含工程來源須使用第 5 版以上，並保留所需能力。");
  }
  // Bound and reject non-JSON values before cloning: JSON.stringify otherwise hides NaN.
  function jsonData(value) {
    let count = 0;
    function visit(v, depth) {
      if (++count > 600000 || depth > 64) fail("空間模型資料過大或巢狀過深。");
      if (v === null || typeof v === "boolean") return;
      if (typeof v === "number" && Number.isFinite(v)) return;
      if (typeof v === "string" && v.length <= MAX_MANIFEST) return;
      if (Array.isArray(v)) { for (const item of v) visit(item, depth + 1); return; }
      if (object(v) && [Object.prototype, null].includes(Object.getPrototypeOf(v))) {
        for (const [k, item] of Object.entries(v)) {
          if (["__proto__", "constructor", "prototype"].includes(k) || k.length > 200) fail("空間模型欄位不合法。");
          visit(item, depth + 1);
        }
        return;
      }
      fail("空間模型必須是完整且有限的 JSON 資料。");
    }
    visit(value, 0);
    if (new TextEncoder().encode(JSON.stringify(value)).length > MAX_MANIFEST) fail("空間模型資料超過 8 MB。");
  }
  function validateModelPackage(p) {
    if (!keys(p, ["manifest", "definitions", "request", "derived", "diagnostics"], ["presentation"])) fail("空間模型套件欄位不合法。");
    const m = p.manifest;
    if (!keys(m, ["schema", "profile", "axiom_revision", "axiom_sha256", "generator", "capabilities", "units", "coordinate_system", "source_sha256", "geometry_sha256"]) ||
        m.schema !== "geometry-model-package/1" || m.profile !== "orthogonal-model/1" || m.units !== "mm" ||
        !str(m.axiom_revision, 100) || !hashRE.test(m.axiom_sha256) || !hashRE.test(m.source_sha256) || !hashRE.test(m.geometry_sha256) ||
        !keys(m.generator, ["name", "version"]) || !str(m.generator.name, 200) || !m.generator.name.trim() || !str(m.generator.version, 100) || !m.generator.version.trim() ||
        !keys(m.coordinate_system, ["handedness", "up"]) || m.coordinate_system.handedness !== "right" || m.coordinate_system.up !== "+Z" ||
        !Array.isArray(m.capabilities) || m.capabilities.length > 42 || !m.capabilities.every(c => str(c, 100))) fail("空間模型版本或座標資訊不合法。");
    if (!keys(p.definitions, ["base_scene", "extensions"]) || !str(p.definitions.base_scene, MAX_MANIFEST) ||
        !Array.isArray(p.definitions.extensions) || p.definitions.extensions.length > 512 || !p.definitions.extensions.every(object)) fail("空間模型定義不合法。");
    if (sceneCapabilities(p.definitions.base_scene).some(c => !m.capabilities.includes(c)))
      fail("空間模型缺少工程來源能力宣告。");
    const req = p.request;
    if (!keys(req, ["roots", "role", "target"], ["allow_partial"]) || !Array.isArray(req.roots) || !req.roots.length || req.roots.length > 512 ||
        !req.roots.every(r => keys(r, ["kind", "id"]) && str(r.kind, 100) && uint(r.id)) ||
        !["geometry", "enclosure", "clearance"].includes(req.role) || !["surface-set", "solid-set"].includes(req.target) ||
        (Object.hasOwn(req, "allow_partial") && typeof req.allow_partial !== "boolean")) fail("空間模型請求不合法。");
    if (!keys(p.derived, ["status", "objects"]) || !["COMPLETE", "EMPTY", "INCOMPLETE"].includes(p.derived.status) ||
        !Array.isArray(p.derived.objects) || p.derived.objects.length > 10000 || !Array.isArray(p.diagnostics) || p.diagnostics.length > 10000) fail("空間模型結果不合法。");
    for (const mesh of p.derived.objects) {
      if (!keys(mesh, ["root", "member_path", "role", "status", "representation", "closure", "component", "vertices_mm", "triangles", "face_sources", "boundary_shells", "volume_mm3"]) ||
          !keys(mesh.root, ["kind", "id"]) || !str(mesh.root.kind, 100) || !uint(mesh.root.id) ||
          !Array.isArray(mesh.member_path) || !mesh.member_path.every(uint) || !["geometry", "enclosure", "clearance"].includes(mesh.role) ||
          !["COMPLETE", "EMPTY"].includes(mesh.status) || mesh.representation !== "mesh" || !["open", "closed", "empty"].includes(mesh.closure) ||
          !(mesh.component === null || uint(mesh.component)) || !Array.isArray(mesh.vertices_mm) || mesh.vertices_mm.length > 200000 ||
          !mesh.vertices_mm.every(v => Array.isArray(v) && v.length === 3 && v.every(n => finite(n, -1e8, 1e8))) ||
          !Array.isArray(mesh.triangles) || mesh.triangles.length > 200000 ||
          !mesh.triangles.every(t => Array.isArray(t) && t.length === 3 && t.every(n => uint(n) && n < mesh.vertices_mm.length)) ||
          !Array.isArray(mesh.face_sources) || mesh.face_sources.length !== mesh.triangles.length || !mesh.face_sources.every(Array.isArray) ||
          !Array.isArray(mesh.boundary_shells) || !(mesh.volume_mm3 === null || (str(mesh.volume_mm3, 100) && /^\d+$/.test(mesh.volume_mm3)))) fail("空間模型網格不合法。");
    }
    return p;
  }
  function validateTimberModel(record) {
    const {input, source, result} = record, pkg = result.timbers, refs = input.timbers;
    if (input.mode !== "plan" || !Array.isArray(refs) || !refs.length || refs.length > 512 ||
        !refs.every(ref => keys(ref, ["kind", "id"]) && ref.kind === "timber" && uint(ref.id)) ||
        new Set(refs.map(ref => ref.id)).size !== refs.length) fail("納入角材必須是非空、無重複的明確角材引用。");
    if (source.placement_id !== input.placement_id || !positiveId(source.boundary_id) || source.scene_hash !== result.source_sha256 ||
        result.summary.source_placement !== input.placement_id) fail("角材模型與來源放置面不一致。");
    validateModelPackage(pkg);
    const ids = new Set(refs.map(ref => ref.id)), request = pkg.request;
    if (request.role !== "geometry" || request.target !== "solid-set" || request.allow_partial !== false ||
        request.roots.length !== ids.size || request.roots.some(ref => ref.kind !== "timber" || !ids.has(ref.id)) ||
        new Set(request.roots.map(ref => ref.id)).size !== ids.size || pkg.definitions.extensions.length || pkg.derived.status !== "COMPLETE")
      fail("角材套件必須完整輸出所選角材的材料實體。");
    // These are original-scene timber roots, not generated walls or shell members.
    validateFaceProjectionRefs([{bid:source.boundary_id,placement_id:input.placement_id}], input.base_scene);
    validateFaceProjectionRefs([{bid:source.boundary_id,placement_id:input.placement_id}], pkg.definitions.base_scene);
    const present = new Set();
    let volume = 0n;
    for (const mesh of pkg.derived.objects) {
      if (mesh.root.kind !== "timber" || !ids.has(mesh.root.id) || present.has(mesh.root.id) || mesh.member_path.length ||
          mesh.role !== "geometry" || mesh.status !== "COMPLETE" || mesh.closure !== "closed" || !mesh.triangles.length ||
          mesh.volume_mm3 === null || BigInt(mesh.volume_mm3) <= 0n) fail("角材套件缺少完整實體，或含有未選取的角材。");
      present.add(mesh.root.id); volume += BigInt(mesh.volume_mm3);
      for (const face of mesh.face_sources) {
        if (!face.length || face.some(ref => !keys(ref, ["origin", "feature", "placement_id", "boundary_id", "loop_index", "edge_index", "operation_path", "role", "normal_sign"]) ||
            !keys(ref.origin, ["kind", "id"]) || ref.origin.kind !== "timber" || ref.origin.id !== mesh.root.id ||
            ref.placement_id !== input.placement_id || ref.boundary_id !== source.boundary_id || !str(ref.feature, 100) || !ref.feature ||
            ref.loop_index !== -1 || ref.edge_index !== -1 || !Array.isArray(ref.operation_path) || ref.operation_path.length ||
            ref.role !== "boundary" || ![1, -1].includes(ref.normal_sign))) fail("角材網格來源與所選角材或放置面不一致。");
      }
    }
    if (present.size !== ids.size || result.summary.timber_count !== ids.size || result.summary.timber_volume_mm3 !== volume.toString())
      fail("角材支數或材料體積與模型不一致。");
  }
  function validateSpaceModel(record) {
    jsonData(record);
    if (!keys(record, ["id", "name", "created_at", "source", "input", "result"]) || !id(record.id) || !str(record.name, 200) || !record.name.trim() ||
        !str(record.created_at, 100) || !Number.isFinite(Date.parse(record.created_at))) fail("空間模型紀錄不合法。");
    const s = record.source, i = record.input, r = record.result;
    if (!keys(s, ["kind", "placement_id", "boundary_id", "scene_hash"], ["projection"]) || !["scene", "example"].includes(s.kind) ||
        ![s.placement_id, s.boundary_id].every(v => v === null || uint(v)) || !hashRE.test(s.scene_hash)) fail("空間模型來源不合法。");
    const withTimbers = Object.hasOwn(i || {}, "timbers");
    if (!keys(i, ["mode", "base_scene", "obstacles"], ["placement_id", "settings", "uses", "timbers"]) || !["plan", "faces"].includes(i.mode) ||
        !str(i.base_scene, MAX_MANIFEST) || !Array.isArray(i.obstacles) || i.obstacles.length > 512 ||
        !i.obstacles.every(o => keys(o, ["kind", "id"]) && ["column", "beam"].includes(o.kind) && uint(o.id))) fail("空間模型輸入不合法。");
    const use = u => keys(u, ["placement_id", "orientation", "purpose"]) && uint(u.placement_id) && [1, -1].includes(u.orientation) && ["boundary", "calculation-cap"].includes(u.purpose);
    if (i.mode === "plan") {
      const settings = i.settings;
      if (!keys(i, ["mode", "base_scene", "obstacles", "placement_id", "settings"], ["timbers"]) || !uint(i.placement_id) ||
          !keys(settings, ["bottom", "height", "edges", "floor", "ceiling", "holes", "wall_thickness"]) ||
          !Number.isSafeInteger(settings.bottom) || !finite(settings.bottom, -1e8, 1e8) || !Number.isSafeInteger(settings.height) || !finite(settings.height, 1, 1e8) ||
          !Array.isArray(settings.edges) || !settings.edges.length || settings.edges.length > 512 || !settings.edges.every(uint) || new Set(settings.edges).size !== settings.edges.length ||
          !["none", "boundary", "calculation-cap"].includes(settings.floor) || !["none", "boundary", "calculation-cap"].includes(settings.ceiling) ||
          !["none", "through"].includes(settings.holes) || !(settings.wall_thickness === null || (Number.isSafeInteger(settings.wall_thickness) && finite(settings.wall_thickness, 1, 1e8)))) fail("平面建立空間的設定不合法。");
    } else if (!keys(i, ["mode", "base_scene", "obstacles", "uses"]) || !Array.isArray(i.uses) || !i.uses.length || i.uses.length > 512 || !i.uses.every(use)) fail("組合邊界面的設定不合法。");
    if (Object.hasOwn(s, "projection")) {
      validateFaceProjection(s.projection);
      if (i.mode !== "plan" || !positiveId(s.boundary_id) || s.placement_id !== i.placement_id) fail("空間模型的平面投影來源不一致。");
      validateFaceProjectionRefs([{bid:s.boundary_id,placement_id:s.placement_id}], i.base_scene);
    }
    if (!keys(r, ["schema", "space", "volume", "clearance", "walls", "summary", "source_sha256", ...(withTimbers ? ["timbers"] : [])], ["ok", "diagnostics"]) ||
        r.schema !== (withTimbers ? "geometry-space-preview/2" : "geometry-space-preview/1") ||
        !object(r.summary) || !hashRE.test(r.source_sha256) || (Object.hasOwn(r, "ok") && r.ok !== true) ||
        (Object.hasOwn(r, "diagnostics") && !Array.isArray(r.diagnostics))) fail("空間預覽紀錄不合法。");
    validateModelPackage(r.space);
    for (const key of ["volume", "clearance", "walls"]) if (r[key] !== null) validateModelPackage(r[key]);
    const summary = r.summary;
    if (!keys(summary, ["source_placement", "source_z", "bottom", "top", "generated_faces", "missing", "face_count", "closed", "volume_mm3", "clearance_mm3", "wall_volume_mm3", "wall_diagnostics", ...(withTimbers ? ["timber_count", "timber_volume_mm3"] : [])]) ||
        !(summary.source_placement === null || uint(summary.source_placement)) ||
        ![summary.source_z, summary.bottom, summary.top].every(v => v === null || (Number.isSafeInteger(v) && finite(v, -1e8, 1e8))) ||
        !Array.isArray(summary.generated_faces) || summary.generated_faces.length > 512 ||
        !summary.generated_faces.every(f => keys(f, ["placement_id", "label", "orientation", "purpose"]) && str(f.label, 300) && use({placement_id:f.placement_id, orientation:f.orientation, purpose:f.purpose})) ||
        !Array.isArray(summary.missing) || summary.missing.length > 512 || !summary.missing.every(v => str(v, 1000)) || !uint(summary.face_count) ||
        typeof summary.closed !== "boolean" || summary.closed !== (r.volume !== null) || !Array.isArray(summary.wall_diagnostics)) fail("空間摘要不合法。");
    for (const [key, field] of [["volume", "volume_mm3"], ["clearance", "clearance_mm3"], ["walls", "wall_volume_mm3"]]) {
      const pkg = r[key], values = pkg?.derived.objects.map(o => o.volume_mm3);
      const volume = values?.every(v => v !== null) ? values.reduce((n, v) => n + BigInt(v), 0n).toString() : null;
      if (summary[field] !== volume) fail("空間摘要與已保存的模型不一致。");
    }
    for (const key of ["volume", "clearance"]) if (r[key] && r[key].manifest.source_sha256 !== r.space.manifest.source_sha256) fail("空間與體積模型的來源不一致。");
    if (withTimbers) validateTimberModel(record);
    return record;
  }
  async function sha(bytes) {
    return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", bytes)), b => b.toString(16).padStart(2, "0")).join("");
  }
  function validate(m) {
    if (!m || ![FORMAT, MODEL_FORMAT, PROJECTION_FORMAT, TIMBER_FORMAT, ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format)) fail("專案版本不支援，請使用相容版本開啟。");
    if (Object.hasOwn(m, "featureAttachments") && m.format !== FEATURE_FORMAT) fail("功能附件須使用第 10 版格式。");
    if ([ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format)) {
      if (!keys(m, ["format", "projectId", "name", "sceneHash", "sources", "faces", "models", "faceProjections", "requiredCapabilities"], ["reconstructionReviews", "engineeringDrafts", ...([ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format) ? ["assemblyDrafts"] : []), ...(m.format === FEATURE_FORMAT ? ["featureAttachments"] : [])]))
        fail("第 5 版工程專案的欄位不完整或含未知定義。");
      validateManifestCapabilities(m.requiredCapabilities);
      if (Object.hasOwn(m, "featureAttachments")) Features.validate(m.featureAttachments);
      if (Object.hasOwn(m, "assemblyDrafts")) validateAssemblyDrafts(m.assemblyDrafts);
      if (Object.hasOwn(m, "engineeringDrafts")) validateEngineeringDrafts(m.engineeringDrafts);
    } else if (Object.hasOwn(m, "assemblyDrafts") || Object.hasOwn(m, "requiredCapabilities") || Object.hasOwn(m, "engineeringDrafts"))
      fail("工程能力與草稿必須使用第 5 版格式。");
    if (m.format === FORMAT && Object.hasOwn(m, "models") && (!Array.isArray(m.models) || m.models.length)) fail("含空間模型的專案必須使用第 2 版格式。");
    if (m.format === MODEL_FORMAT && (!Array.isArray(m.models) || m.models.length > MAX_MODELS)) fail("空間模型清單不合法。");
    if ([PROJECTION_FORMAT, TIMBER_FORMAT, ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format) && (!Array.isArray(m.models) || m.models.length > MAX_MODELS || !Array.isArray(m.faceProjections))) fail("平面投影專案清單不合法。");
    if (Object.hasOwn(m, "faceProjections")) validateFaceProjectionList(m.faceProjections);
    if (![PROJECTION_FORMAT, TIMBER_FORMAT, ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format) && (m.faceProjections?.length || m.models?.some(model => Object.hasOwn(model.source || {}, "projection")))) fail("含平面投影定義的專案必須使用第 3 版格式。");
    if (![TIMBER_FORMAT, ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format) && m.models?.some(model => Object.hasOwn(model.input || {}, "timbers") || model.result?.schema === "geometry-space-preview/2")) fail("含角材模型的專案必須使用第 4 版格式。");
    if (Object.hasOwn(m, "reconstructionReviews")) {
      if (![OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format)) fail("輪廓核對收據須使用第 9 版格式。");
      validateReconstructionReviews(m.reconstructionReviews, m.faces);
    }
    validateEngineeringScene(m, "");
    const modelIds = new Set();
    for (const model of m.models || []) {
      validateSpaceModel(model);
      if (modelIds.has(model.id)) fail("空間模型 ID 重複。");
      modelIds.add(model.id);
    }
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
  function reviewBasis(p) {
    return JSON.stringify([p.sourceId,p.id,p.page,p.imgW,p.imgH,p.crop,p.mmPerPx,p.x,p.y,p.rot,p.calibration]);
  }
  function outlineFingerprint(loops) {
    return JSON.stringify((loops || []).map(l=>[l.verts,l.fixity]));
  }
  function validateReconstructionReviews(records, faces) {
    if (!Array.isArray(records) || records.length > 10000) fail("輪廓核對收據清單不合法。");
    const seen=new Set();
    for (const r of records) {
      if (!keys(r,["bid","pageId","basis","geometry","method","warnings","confirmedAt"]) || !positiveId(r.bid) || !id(r.pageId) ||
          !str(r.basis,4000) || !str(r.geometry,100000) || !["manual","pdf-vector","image-lines"].includes(r.method) ||
          !Array.isArray(r.warnings) || r.warnings.length>100 || !r.warnings.every(w=>str(w,1000)) || !str(r.confirmedAt,40) || !Number.isFinite(Date.parse(r.confirmedAt))) fail("輪廓核對收據欄位不合法。");
      const key=r.bid+":"+r.pageId, p=faces?.find(f=>f.bid===r.bid)?.pages.find(p=>p.id===r.pageId);
      if (!p || seen.has(key)) fail("輪廓核對收據引用不存在或重複的來源頁。");
      seen.add(key);
      let basis,loops;try {basis=JSON.parse(r.basis);loops=JSON.parse(r.geometry);}catch {fail("輪廓核對指紋不合法。");}
      if (!Array.isArray(basis) || basis.length!==11 || basis[0]!==p.sourceId || basis[1]!==p.id || basis[2]!==p.page ||
          !finite(basis[3],1,1e7) || !finite(basis[4],1,1e7) || !finite(basis[6],1e-9,1e8) || !finite(basis[7],-1e8,1e8) || !finite(basis[8],-1e8,1e8) || ![0,90,180,270].includes(basis[9])) fail("輪廓核對收據的來源／幾何不合法。");
      const crop=basis[5],q=basis[10];
      if (!Array.isArray(crop) || crop.length!==4 || !crop.every(Number.isFinite) || crop[0]<0 || crop[1]<0 || crop[2]<=0 || crop[3]<=0 || crop[0]+crop[2]>basis[3]+.001 || crop[1]+crop[3]>basis[4]+.001 ||
          !keys(q,["points","distanceMm","inputValue","inputUnit"]) || !Array.isArray(q.points) || q.points.length!==2 || !q.points.every(pt) || q.points.some(v=>v[0]>basis[3]||v[1]>basis[4]) ||
          !Number.isSafeInteger(q.distanceMm) || !finite(q.distanceMm,1,1e8) || !finite(q.inputValue,1e-9,1e8) || !["mm","cm"].includes(q.inputUnit)) fail("輪廓核對收據的校準不合法。");
      const distance=Math.hypot(q.points[0][0]-q.points[1][0],q.points[0][1]-q.points[1][1]);
      if (!(distance>0) || Math.abs(q.distanceMm/distance-basis[6])>1e-8*basis[6] || Math.abs(q.inputValue*(q.inputUnit==="cm"?10:1)-q.distanceMm)>1e-7) fail("輪廓核對收據的校準與比例不一致。");
      if (!Array.isArray(loops) || !loops.length || loops.length>256 || loops.some(l=>!Array.isArray(l)||l.length!==2 || !Array.isArray(l[0]) || l[0].length<4 || l[0].length>1024 ||
            !Array.isArray(l[1]) || l[0].length!==l[1].length || !l[1].every(v=>v===0||v===1) || l[0].some(p=>!Array.isArray(p)||p.length!==2||!p.every(v=>Number.isSafeInteger(v)&&Math.abs(v)<=1e8)))) fail("輪廓核對收據的幾何不合法。");
      if (loops.some(l=>l[0].some((p,i)=>((p[0]===l[0][(i+1)%l[0].length][0])===(p[1]===l[0][(i+1)%l[0].length][1]))))) fail("輪廓核對收據的幾何必須正交。");
      if (JSON.stringify(basis)!==r.basis || JSON.stringify(loops)!==r.geometry) fail("輪廓核對指紋必須使用標準編碼。");
    }
  }
  function reference(p) {
    const keys = ["id","sourceId","page","imgW","imgH","crop","mmPerPx","x","y","rot","opacity","locked","calibration","reviewRequired","records"];
    return Object.fromEntries(keys.map(k => [k, copy(p[k])]));
  }
  async function pack(scene, manifest, sources, zip) {
    const sceneBytes = new TextEncoder().encode(scene);
    for (const model of manifest.models || []) validateSpaceModel(model);
    if (Object.hasOwn(manifest, "faceProjections")) validateFaceProjectionList(manifest.faceProjections);
    if (Object.hasOwn(manifest, "requiredCapabilities")) validateManifestCapabilities(manifest.requiredCapabilities);
    if (Object.hasOwn(manifest, "assemblyDrafts")) validateAssemblyDrafts(manifest.assemblyDrafts);
    if (Object.hasOwn(manifest, "engineeringDrafts")) validateEngineeringDrafts(manifest.engineeringDrafts);
    if (Object.hasOwn(manifest, "featureAttachments")) Features.validate(manifest.featureAttachments);
    const m = { ...copy(manifest), format: projectFormat(manifest, scene), sceneHash: await sha(sceneBytes) };
    if ([ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format)) {
      m.requiredCapabilities = projectCapabilities(manifest, scene);
      if (!m.assemblyDrafts?.records.length) delete m.assemblyDrafts;
      if (!m.engineeringDrafts?.records.length) delete m.engineeringDrafts;
    } else { delete m.requiredCapabilities; delete m.engineeringDrafts; delete m.assemblyDrafts; }
    if (!m.featureAttachments?.records.length) delete m.featureAttachments;
    if (m.format === FORMAT) delete m.models;
    if ([PROJECTION_FORMAT, TIMBER_FORMAT, ENGINEERING_FORMAT, PARAMETER_FORMAT, ASSEMBLY_FORMAT, GENERATION_FORMAT, OUTLINE_FORMAT, FEATURE_FORMAT].includes(m.format)) { m.models ||= []; m.faceProjections ||= []; }
    else delete m.faceProjections;
    validate(m);
    validateEngineeringScene(m, scene);
    const manifestBytes = new TextEncoder().encode(JSON.stringify(m));
    if (manifestBytes.length > MAX_MANIFEST) fail("專案清單超過 8 MB，請拆成較小的專案。");
    const entries = { "world.scene": sceneBytes, "manifest.json": manifestBytes };
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
        const limit = file.name === "manifest.json" ? MAX_MANIFEST : file.name === "world.scene" ? 16 * 1024 * 1024 : MAX_SOURCE;
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
    if (!m.models) m.models = [];
    if (!m.faceProjections) m.faceProjections = [];
    const scene = decoder.decode(entries["world.scene"]);
    validateEngineeringScene(m, scene);
    // Top-level scene references are resolved from the native import candidate,
    // after all reset/delete/redeclaration commands, before its atomic commit.
    return { manifest: m, scene, sources };
  }
  // Core entries mirror bridge transactions; local entries change saved metadata.
  // Sources stay shared (PDF runtime objects cannot be cloned), saved values are snapshots.
  class ContextHistory {
    constructor(makeContext, limit = 32) {
      this.makeContext = makeContext; this.limit = limit; this.undo = []; this.redo = []; this.group = null;
      this.blockCoreRedo = false;
      this.frame = { context: makeContext(), ids: new Map() };
    }
    snapshot() {
      return { context: this.frame.context, ids: new Map(this.frame.ids),
        reconstructionReviews: new Map([...(this.frame.context.reconstructionReviews || new Map())].map(([k,v])=>[k,copy(v)])),
        assemblyDrafts: copy(this.frame.context.assemblyDrafts || []),
        featureAttachments: copy(this.frame.context.featureAttachments || []),
        ...(Array.isArray(this.frame.context.models) ? { models: copy(this.frame.context.models) } : {}),
        ...(this.frame.context.faceProjections instanceof Map ? { faceProjections: new Map([...this.frame.context.faceProjections].map(([key, value]) => [key, copy(value)])) } : {}) };
    }
    restore(frame) {
      this.frame = { context: frame.context, ids: new Map(frame.ids) };
      this.frame.context.reconstructionReviews = new Map([...(frame.reconstructionReviews || new Map())].map(([k,v])=>[k,copy(v)]));
      this.frame.context.assemblyDrafts = copy(frame.assemblyDrafts || []);
      this.frame.context.featureAttachments = copy(frame.featureAttachments || []);
      if (frame.models) this.frame.context.models = copy(frame.models);
      if (frame.faceProjections) this.frame.context.faceProjections = new Map([...frame.faceProjections].map(([key, value]) => [key, copy(value)]));
    }
    push(frame, kind = "core", action = null) {
      this.undo.push({ ...frame, kind, action }); if (this.undo.length > this.limit) this.undo.shift(); this.redo = [];
      // A new core transaction discards its redo branch. A local branch cannot do that,
      // so the browser must refuse any leftover bridge redo beyond its own timeline.
      this.blockCoreRedo = kind === "local";
    }
    changeModels(models) {
      if (this.group) fail("請先完成目前的操作再變更空間模型。");
      this.push(this.snapshot(), "local");
      this.frame.context.models = copy(models);
    }
    changeFaceProjections(projections) {
      if (this.group) fail("請先完成目前的操作再變更平面投影定義。");
      this.push(this.snapshot(), "local");
      this.frame.context.faceProjections = new Map([...projections].map(([key, value]) => [key, copy(value)]));
    }
    pruneFaceProjections(keep) {
      const previous = this.frame.context.faceProjections;
      if (!(previous instanceof Map)) return;
      const next = new Map(), bids = new Map([...this.frame.ids].map(([bid,key]) => [key,bid]));
      for (const [key, records] of previous) {
        const filtered = records.filter(record => bids.has(key) && keep(bids.get(key), record.placement_id));
        if (filtered.length) next.set(key, filtered);
      }
      if (JSON.stringify([...next]) !== JSON.stringify([...previous])) {
        this.frame.context.faceProjections = next;
        this.frame.context.faceProjectionsDirty = true;
      }
    }
    step(op) {
      const from = op === "undo" ? this.undo : this.redo, to = op === "undo" ? this.redo : this.undo;
      const previous = from.pop();
      if (!previous) return false;
      to.push({ ...this.snapshot(), kind: previous.kind || "core", action: previous.action || null }); if (to.length > this.limit) to.shift();
      this.restore(previous); this.group = null; return true;
    }
    actionLabel(op) {
      if (op !== "undo" && op !== "redo") return null;
      return (op === "undo" ? this.undo : this.redo).at(-1)?.action || null;
    }
    tryLocal(command) {
      const match = command.split("#", 1)[0].match(/^line\s+(undo|redo)\s*$/);
      if (!match) return null;
      if (this.group) return { ok: false, local: true, error: "請先完成目前的操作再復原或重做。" };
      const op = match[1], stack = op === "undo" ? this.undo : this.redo;
      if (stack.at(-1)?.kind === "local") { this.step(op); return { ok: true, local: true }; }
      if (op === "redo" && !stack.length && this.blockCoreRedo)
        return { ok: false, local: true, error: "沒有可重做的操作。" };
      return null;
    }
    sync(ids) {
      const live = new Set(ids);
      for (const bid of this.frame.ids.keys()) if (!live.has(bid)) this.frame.ids.delete(bid);
      for (const bid of live) if (!this.frame.ids.has(bid)) this.frame.ids.set(bid, globalThis.crypto.randomUUID());
      this.pruneFaceProjections(() => true);
    }
    replace(context, ids, action = null) {
      this.push(this.snapshot(), "core", action); this.group = null;
      this.frame = { context, ids: new Map(ids || []) };
    }
    observe(command, result) {
      // The bridge accepts blank/comment lines without a native history step.
      // Treating one as a mutation would also unblock an abandoned core redo.
      if (command.startsWith("line ")) {
        command = "line " + command.slice(5).split("#", 1)[0].trim();
        if (command === "line ") return;
      }
      if (command === "objects" && result.ok && Array.isArray(result.faces)) { this.sync(result.faces.filter(f => f.kind === "boundary").map(f => f.id)); return; }
      if (command === "surfaces" && result.ok && Array.isArray(result.surfaces)) {
        this.pruneFaceProjections((bid, pid) => result.surfaces.some(s => s.id === pid && s.boundary === bid && s.u?.[2] === 0 && s.v?.[2] === 0));
        return;
      }
      if (!/^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm )/.test(command)) return;
      const op = command.startsWith("line ") ? command.slice(5).trim().split(/\s+/)[0] : command.split(/\s+/)[0];
      if (!result.ok) {
        // A preview rejection preserves the core's open group; other failures roll it back.
        if (this.group && !result.preview && op !== "history-begin" && op !== "loadfile") {
          this.restore(this.group.base); this.group = null;
        }
        return;
      }
      if (["engineering-confirm", "assembly-confirm"].includes(op) && result.history_changed === false) return;
      if (op === "canvas-pos" || op === "preview" || op === "cancel-preview") return;
      if (op === "history-begin") { this.group = { base: this.snapshot(), dirty: false }; return; }
      if (op === "history-abort") { if (this.group) this.restore(this.group.base); this.group = null; return; }
      if (op === "history-end") { if (this.group?.dirty) this.push(this.group.base); this.group = null; return; }
      if (op === "undo" || op === "redo") {
        const before = this.snapshot();
        if (!this.step(op)) {
          // Earlier core history has no trustworthy reference associations. Independent
          // models and unpublished drafts remain saved values; a core-only step
          // cannot silently delete them.
          const assemblyDrafts = copy(this.frame.context.assemblyDrafts || []);
          const featureAttachments = copy(this.frame.context.featureAttachments || []);
          const models = this.frame.context.models, engineeringDrafts = this.frame.context.engineeringDrafts;
          this.frame = { context: this.makeContext(), ids: new Map() };
          this.frame.context.assemblyDrafts = assemblyDrafts;
          this.frame.context.featureAttachments = featureAttachments;
          if (models) this.frame.context.models = copy(models);
          if (engineeringDrafts) this.frame.context.engineeringDrafts = copy(engineeringDrafts);
          const to = op === "undo" ? this.redo : this.undo;
          to.push({ ...before, kind: "core" }); if (to.length > this.limit) to.shift();
        }
        this.group = null; return;
      }
      if (command === "reset" || command === "default") { this.undo = []; this.redo = []; this.group = null; this.blockCoreRedo = false; }
      else if (this.group) this.group.dirty = true;
      else this.push(this.snapshot());
      if (op === "reset" || op === "default" || op === "loadfile") this.frame = { context: this.makeContext(), ids: new Map() };
      // A batch may recreate a deleted id before the next objects refresh.
      // Retire the old incarnation at the successful delete, not at render time.
      const deletion = command.match(/^line\s+delete\s+boundary\s+(\d+)(?:\s|$)/);
      if (deletion) this.frame.ids.delete(+deletion[1]);
      const birth = command.match(/^line\s+(?:boundary|surface)\s+(\d+)\s/);
      if (birth && !this.frame.ids.has(+birth[1])) this.frame.ids.set(+birth[1], globalThis.crypto.randomUUID());
      const removedPlacement = command.match(/^line\s+delete\s+placement\s+(\d+)(?:\s|$)/);
      const changedPlacement = command.match(/^line\s+(?:placement|surface)\s+(\d+)\s/);
      const placed = changedPlacement && sceneProjectionRefs(command.slice(5)).placements.get(+changedPlacement[1]);
      this.pruneFaceProjections((bid,pid) => !((removedPlacement && pid === +removedPlacement[1]) ||
        (changedPlacement && pid === +changedPlacement[1] && (placed?.bid !== bid || !placed.horizontal))));
    }
  }
  return { Features, FEATURE_FORMAT, readerCapabilities, validateManifestCapabilities, OUTLINE_FORMAT, reviewBasis, outlineFingerprint, validateReconstructionReviews, GENERATION_FORMAT, GENERATION_CAPABILITY, ASSEMBLY_FORMAT, ASSEMBLY_CAPABILITY, ASSEMBLY_DRAFT_SCHEMA, validateAssemblyDraft, validateAssemblyDrafts, PARAMETER_FORMAT, PARAMETER_CAPABILITY, FORMAT, MODEL_FORMAT, PROJECTION_FORMAT, TIMBER_FORMAT, ENGINEERING_FORMAT, ENGINEERING_CAPABILITY, DRAFT_SCHEMA, MAX_ENGINEERING_DRAFTS,
    MAX_SOURCE, MAX_PACKAGE, MAX_MODELS, TYPES, sha, validate, validateSpaceModel, validateModelPackage,
    validateEngineeringDraft, validateEngineeringDrafts, validateProjectCapabilities, assertProjectCapabilities, sceneCapabilities,
    validateFaceProjection, validateFaceProjectionRefs, validateProjectObjectRefs, projectFormat, reference, pack, unpack, ContextHistory };
});
