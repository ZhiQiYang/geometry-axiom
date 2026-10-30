/* H: definition-import/1. Composes existing parameter, spec, material and assembly
 * operations. The capability is advertised to executors and is not a scene or
 * project capability. Unlisted identities never enter the imported world.
 * Card numbers follow parameter_import. Rule and binding numbers follow
 * WORLD_NEXT_ID with skip-zero, including ids assigned earlier in this import.
 */
#define DI_SCENE_MAX (16u * 1024u * 1024u)
#define DI_NAME_MAX GEO_NAMED_VALUE_NAME_BYTES

static char g_di_sha[65];
static uint32_t g_di_sha_token;

typedef struct { char code[40], message[180], name[DI_NAME_MAX]; } DiNote;
typedef struct { uint32_t from, to; } DiCard;
typedef struct { uint32_t from_id, from_version, to_id, to_version; size_t index; } DiRule;
typedef struct { uint32_t from_id, to_id, rule_from, rule_version, rule_to, rule_to_version; size_t index; } DiBinding;
typedef struct { char from[DI_NAME_MAX], to[DI_NAME_MAX]; GeoCoord value; int action; } DiSpec; /* 0 create, 1 rename, 2 map */
typedef struct { char id[ENG_ID_MAX]; uint32_t version; int action, kind; size_t index; char fingerprint[65]; } DiMaterial;
typedef struct {
    DiCard cards[GEO_PARAMETER_CARD_MAX]; size_t card_n;
    DiRule rules[ASM_RULE_MAX]; size_t rule_n;
    DiBinding bindings[ASM_BINDING_MAX]; size_t binding_n;
    DiSpec specs[GEO_NAMED_VALUE_CAPACITY]; size_t spec_n;
    DiMaterial materials[ENG_MATERIAL_MAX]; size_t material_n;
    DiNote notes[24]; size_t note_n;
    bool unsupported, policy, schema, invalid;
    char error[200];
} DiPlan;

static void di_note(DiPlan *p, const char *code, const char *name, const char *message)
{
    if (p->note_n >= sizeof p->notes / sizeof p->notes[0]) return;
    DiNote *n = &p->notes[p->note_n++];
    snprintf(n->code, sizeof n->code, "%s", code);
    snprintf(n->name, sizeof n->name, "%s", name ? name : "");
    snprintf(n->message, sizeof n->message, "%s", message);
}
static bool di_stop(DiPlan *p, int kind, const char *message)
{
    snprintf(p->error, sizeof p->error, "%s", message);
    if (kind == 1) p->unsupported = true;
    else if (kind == 2) p->policy = true;
    else if (kind == 3) p->schema = true;
    else p->invalid = true;
    return false;
}
static bool di_hex64(const char *s)
{
    if (!s || strlen(s) != 64) return false;
    for (int i = 0; i < 64; ++i) if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return false;
    return true;
}
static bool di_u32(const GeoJson *j, int t, uint32_t *out, bool positive)
{
    int64_t v; if (!geo_json_integer(j, t, &v) || v < 0 || v > UINT32_MAX || (positive && v == 0)) return false;
    *out = (uint32_t)v; return true;
}
static bool di_join(char *out, size_t cap, const char *dir, const char *name)
{
    size_t n = strlen(dir); bool slash = n && (dir[n - 1] == '/' || dir[n - 1] == '\\');
    int wrote = snprintf(out, cap, slash ? "%s%s" : "%s/%s", dir, name);
    return wrote > 0 && (size_t)wrote < cap;
}
static char *di_read(const char *path, size_t *size, size_t cap, const char **error)
{
    FILE *f = fopen(path, "rb"); if (!f) { *error = "無法讀取匯入檔"; return NULL; }
    if (fseek(f, 0, SEEK_END)) { fclose(f); *error = "無法讀取匯入檔"; return NULL; }
    long n = ftell(f);
    if (n < 0 || (size_t)n > cap || fseek(f, 0, SEEK_SET)) { fclose(f); *error = n > 0 && (size_t)n > cap ? "匯入檔超過容量上限" : "無法讀取匯入檔"; return NULL; }
    char *text = malloc((size_t)n + 1); if (!text) { fclose(f); *error = "無法配置匯入檔"; return NULL; }
    size_t got = fread(text, 1, (size_t)n, f); bool ok = got == (size_t)n && !ferror(f); fclose(f);
    if (!ok) { free(text); *error = "匯入檔讀取不完整"; return NULL; }
    text[got] = 0; if (size) *size = got;
    if (memchr(text, 0, got) || !utf8_is_valid(text)) { free(text); *error = "場景必須是不含 NUL 的完整 UTF-8"; return NULL; }
    return text;
}
static void di_hash_bytes(const char *text, size_t n, char out[65]) { geo_sha256(text, n, out); }
static bool di_id_used(const uint32_t *ids, size_t n, const uint32_t *extra, size_t en, uint32_t id)
{
    for (size_t i = 0; i < n; ++i) if (ids[i] == id) return true;
    for (size_t i = 0; i < en; ++i) if (extra[i] == id) return true;
    return false;
}
/* Same search as WORLD_NEXT_ID, plus ids already assigned in this import. */
static bool di_next_id(const uint32_t *ids, size_t n, const uint32_t *extra, size_t en, bool skip_zero, uint32_t *out)
{
    uint32_t id = 0;
    for (size_t i = 0; i < n; ++i) if (ids[i] > id) id = ids[i];
    for (size_t i = 0; i < en; ++i) if (extra[i] > id) id = extra[i];
    ++id;
    for (size_t attempt = 0; attempt <= n + en; ++attempt) {
        if (skip_zero && id == 0) id = 1;
        if (!di_id_used(ids, n, extra, en, id)) { *out = id; return true; }
        ++id;
    }
    return false;
}
static bool di_keys_only(const GeoJson *j, int token, const char *a, const char *b)
{
    if (token < 0 || j->tokens[token].type != GEO_J_OBJECT) return false;
    for (int p = token + 1; p < j->tokens[token].next; p = j->tokens[p + 1].next) {
        const char *key = j->tokens[p].string;
        if (!key || (strcmp(key, a) && (!b || strcmp(key, b)))) return false;
    }
    return true;
}
static const AsmRuleVersion *di_rule(const World *w, uint32_t id, uint32_t version)
{
    for (size_t i = 0; i < w->wood.assembly.rule_count; ++i) {
        const AsmRuleVersion *r = &w->wood.assembly.rules[i];
        if (r->id == id && r->version == version) return r;
    }
    return NULL;
}
static const AsmBinding *di_binding(const World *w, uint32_t id)
{
    for (size_t i = 0; i < w->wood.assembly.binding_count; ++i) if (w->wood.assembly.bindings[i].id == id) return &w->wood.assembly.bindings[i];
    return NULL;
}
static void di_material_hash(const EngMaterialVersion *m, char out[65])
{
    size_t n = 0; while (n < ENG_RECORD_MAX && m->content[n]) ++n;
    geo_sha256(m->content, n, out);
}
static bool di_add_card(DiPlan *p, const World *src, uint32_t id, int depth);
static bool di_expr(DiPlan *p, const World *src, GeoJson *j, int t, int depth)
{
    if (depth > 32) return di_stop(p, 1, "匯入運算式巢狀超過上限");
    char op[16]; if (!geo_json_string(j, geo_json_member(j, t, "op"), op, sizeof op)) return di_stop(p, 0, "參數運算式無法解析");
    if (!strcmp(op, "literal")) return true;
    if (!strcmp(op, "ref")) {
        uint32_t id; if (!di_u32(j, geo_json_member(j, t, "parameterId"), &id, false)) return di_stop(p, 0, "參數引用無法解析");
        return di_add_card(p, src, id, depth + 1);
    }
    if (strcmp(op, "neg") && strcmp(op, "add") && strcmp(op, "sub") && strcmp(op, "mul") && strcmp(op, "div")) return di_stop(p, 1, "未列舉的運算不得進入匯入範圍");
    if (!di_expr(p, src, j, geo_json_member(j, t, "left"), depth + 1)) return false;
    if (strcmp(op, "neg") && !di_expr(p, src, j, geo_json_member(j, t, "right"), depth + 1)) return false;
    return true;
}
static bool di_add_card(DiPlan *p, const World *src, uint32_t id, int depth)
{
    for (size_t i = 0; i < p->card_n; ++i) if (p->cards[i].from == id) return true;
    const GeoParameterCard *cards = geo_parameters_cards(&src->geo.parameters);
    size_t n = geo_parameters_card_count(&src->geo.parameters), at = n;
    for (size_t i = 0; i < n; ++i) if (cards[i].id == id) { at = i; break; }
    if (at == n) return di_stop(p, 0, "閉包引用了不存在的參數卡");
    if (p->card_n >= GEO_PARAMETER_CARD_MAX) return di_stop(p, 1, "參數卡容量不足");
    p->cards[p->card_n++].from = id;
    const GeoParameterCard *card = &cards[at];
    for (size_t f = 0; f < card->count; ++f) {
        int index = parameter_field_index(src, id, card->fields[f]);
        if (index < 0) return di_stop(p, 0, "參數欄位不存在");
        GeoJson expr = {0}; const char *text = geo_parameters_fields(&src->geo.parameters)[index].expression;
        if (!geo_json_parse(&expr, text) || !di_expr(p, src, &expr, 0, depth)) { geo_json_free(&expr); return p->unsupported || p->invalid || p->schema ? false : di_stop(p, 0, "參數運算式無法解析"); }
        geo_json_free(&expr);
    }
    return !p->unsupported && !p->invalid;
}
static bool di_add_spec(DiPlan *p, const World *src, const char *name)
{
    for (size_t i = 0; i < p->spec_n; ++i) if (!strcmp(p->specs[i].from, name)) return true;
    const GeoNamedValue *v = geo_named_values_find(&src->geo.named_values, name);
    if (!v) return di_stop(p, 0, "閉包引用了不存在的具名規格");
    if (p->spec_n >= GEO_NAMED_VALUE_CAPACITY) return di_stop(p, 1, "具名規格容量不足");
    DiSpec *s = &p->specs[p->spec_n++];
    snprintf(s->from, sizeof s->from, "%s", name); snprintf(s->to, sizeof s->to, "%s", name); s->value = v->value; s->action = 0;
    return true;
}
static bool di_add_material(DiPlan *p, const World *src, const char *id, uint32_t version)
{
    for (size_t i = 0; i < p->material_n; ++i) if (!strcmp(p->materials[i].id, id) && p->materials[i].version == version) return true;
    size_t found = src->wood.engineering.material_count;
    for (size_t i = 0; i < src->wood.engineering.material_count; ++i) {
        const EngMaterialVersion *m = eng_material_at(src, i);
        if (m && !strcmp(m->ref.id, id) && m->ref.version == version) { found = i; break; }
    }
    if (found == src->wood.engineering.material_count) return di_stop(p, 0, "閉包引用了不存在的材料");
    const EngMaterialVersion *m = eng_material_at(src, found);
    if (!m->kind) return di_stop(p, 1, "板材：首版不支援");
    if (p->material_n >= ENG_MATERIAL_MAX) return di_stop(p, 1, "材料容量不足");
    DiMaterial *d = &p->materials[p->material_n++];
    snprintf(d->id, sizeof d->id, "%s", id); d->version = version; d->kind = m->kind; d->index = found; d->action = 1;
    di_material_hash(m, d->fingerprint);
    return true;
}
static bool di_pull_source(DiPlan *p, const World *src, GeoJson *j, int t)
{
    if (t < 0 || geo_json_is_null(j, t)) return true;
    char kind[24]; if (!geo_json_string(j, geo_json_member(j, t, "kind"), kind, sizeof kind)) return di_stop(p, 0, "尺寸來源缺少種類");
    if (!strcmp(kind, "literal")) return true;
    if (!strcmp(kind, "spec")) { char name[DI_NAME_MAX]; if (!geo_json_string(j, geo_json_member(j, t, "name"), name, sizeof name)) return di_stop(p, 0, "具名規格來源無法解析"); return di_add_spec(p, src, name); }
    if (!strcmp(kind, "parameter")) { uint32_t id; if (!di_u32(j, geo_json_member(j, t, "parameterId"), &id, false)) return di_stop(p, 0, "參數來源無法解析"); return di_add_card(p, src, id, 0); }
    if (!strcmp(kind, "material")) {
        char id[ENG_ID_MAX]; uint32_t version;
        if (!geo_json_string(j, geo_json_member(j, t, "id"), id, sizeof id) || !di_u32(j, geo_json_member(j, t, "version"), &version, true)) return di_stop(p, 0, "材料來源無法解析");
        return di_add_material(p, src, id, version);
    }
    if (!strcmp(kind, "application")) return di_stop(p, 1, "工法應用：首版不支援");
    return di_stop(p, 1, "未列舉的身分不得進入匯入範圍");
}
static bool di_add_rule_ref(DiPlan *p, const World *src, uint32_t id, uint32_t version)
{
    for (size_t i = 0; i < p->rule_n; ++i) if (p->rules[i].from_id == id && p->rules[i].from_version == version) return true;
    size_t index = src->wood.assembly.rule_count;
    for (size_t i = 0; i < src->wood.assembly.rule_count; ++i) if (src->wood.assembly.rules[i].id == id && src->wood.assembly.rules[i].version == version) { index = i; break; }
    if (index == src->wood.assembly.rule_count) return di_stop(p, 0, "閉包引用了不存在的規則版本");
    if (p->rule_n >= ASM_RULE_MAX) return di_stop(p, 1, "規則容量不足");
    p->rules[p->rule_n++] = (DiRule){id, version, 0, 0, index};
    return true;
}
static bool di_pull_binding(DiPlan *p, const World *src, const AsmBinding *b)
{
    GeoJson j = {0}; if (!geo_json_parse(&j, b->content)) { geo_json_free(&j); return di_stop(p, 0, "配置內容無法解析"); }
    int rule = geo_json_member(&j, 0, "rule"); uint32_t id, version;
    if (!di_u32(&j, geo_json_member(&j, rule, "id"), &id, true) || !di_u32(&j, geo_json_member(&j, rule, "version"), &version, true) || !di_add_rule_ref(p, src, id, version)) { geo_json_free(&j); return false; }
    int slots = geo_json_member(&j, 0, "slots");
    for (int i = 0; i < geo_json_size(&j, slots) && !p->unsupported && !p->invalid; ++i) {
        int s = geo_json_at(&j, slots, i);
        if (!di_pull_source(p, src, &j, geo_json_member(&j, s, "A")) || !di_pull_source(p, src, &j, geo_json_member(&j, s, "B"))) { geo_json_free(&j); return false; }
    }
    geo_json_free(&j); return !p->unsupported && !p->invalid;
}
static int di_cmp_u32(uint32_t a, uint32_t b) { return a < b ? -1 : a > b ? 1 : 0; }
static void di_sort_plan(DiPlan *p)
{
    for (size_t i = 1; i < p->card_n; ++i) { DiCard k = p->cards[i]; size_t q = i; while (q && p->cards[q - 1].from > k.from) { p->cards[q] = p->cards[q - 1]; --q; } p->cards[q] = k; }
    for (size_t i = 1; i < p->rule_n; ++i) { DiRule k = p->rules[i]; size_t q = i; while (q && (p->rules[q - 1].from_id > k.from_id || (p->rules[q - 1].from_id == k.from_id && p->rules[q - 1].from_version > k.from_version))) { p->rules[q] = p->rules[q - 1]; --q; } p->rules[q] = k; }
    for (size_t i = 1; i < p->binding_n; ++i) { DiBinding k = p->bindings[i]; size_t q = i; while (q && p->bindings[q - 1].from_id > k.from_id) { p->bindings[q] = p->bindings[q - 1]; --q; } p->bindings[q] = k; }
}
static bool di_collect(DiPlan *p, const World *src, GeoJson *req)
{
    int roots = geo_json_member(req, 0, "roots");
    if (roots < 0 || req->tokens[roots].type != GEO_J_OBJECT || !di_keys_only(req, roots, "rules", "bindings")) return di_stop(p, 1, "組構實例：首版不支援");
    int rules = geo_json_member(req, roots, "rules"), bindings = geo_json_member(req, roots, "bindings");
    if (!geo_json_is_array(req, rules) || !geo_json_is_array(req, bindings)) return di_stop(p, 3, "匯入根必須包含規則與配置陣列");
    int rc = geo_json_size(req, rules), bc = geo_json_size(req, bindings);
    if (rc < 0 || bc < 0 || (rc == 0 && bc == 0)) return di_stop(p, 3, "匯入根不得是空的");
    if (rc > ASM_RULE_MAX || bc > ASM_BINDING_MAX) return di_stop(p, 1, "匯入根超過容量");
    for (int i = 0; i < rc; ++i) {
        int t = geo_json_at(req, rules, i); uint32_t id, version;
        if (!geo_json_keys(req, t, "id,version", "") || !di_u32(req, geo_json_member(req, t, "id"), &id, true) || !di_u32(req, geo_json_member(req, t, "version"), &version, true)) return di_stop(p, 3, "規則根需要正整數 id 與 version");
        if (!di_add_rule_ref(p, src, id, version)) return false;
    }
    for (int i = 0; i < bc; ++i) {
        uint32_t id; if (!di_u32(req, geo_json_at(req, bindings, i), &id, true)) return di_stop(p, 3, "配置根必須是正整數");
        for (size_t q = 0; q < p->binding_n; ++q) if (p->bindings[q].from_id == id) return di_stop(p, 3, "配置根重複");
        const AsmBinding *b = di_binding(src, id); if (!b) return di_stop(p, 0, "來源沒有這個配置");
        if (p->binding_n >= ASM_BINDING_MAX) return di_stop(p, 1, "配置容量不足");
        DiBinding *row = &p->bindings[p->binding_n++];
        *row = (DiBinding){id, 0, b->rule_id, b->rule_version, 0, 0, (size_t)(b - src->wood.assembly.bindings)};
        if (!di_pull_binding(p, src, b)) return false;
    }
    di_sort_plan(p);
    return !p->unsupported && !p->invalid && !p->schema;
}
static bool di_name_choice(DiPlan *p, GeoJson *req, const char *name, char *mode, size_t mode_n, char *fresh, size_t fresh_n, bool *present)
{
    int names = geo_json_member(req, 0, "names"); *present = false; mode[0] = fresh[0] = 0;
    if (names < 0 || req->tokens[names].type != GEO_J_OBJECT) return di_stop(p, 3, "names 必須是物件");
    for (int k = names + 1; k < req->tokens[names].next; k = req->tokens[k + 1].next) {
        if (!req->tokens[k].string || strcmp(req->tokens[k].string, name)) continue;
        int v = k + 1; *present = true;
        if (!geo_json_string(req, geo_json_member(req, v, "mode"), mode, mode_n)) return di_stop(p, 3, "改名選擇缺少 mode");
        if (!strcmp(mode, "rename")) {
            if (!geo_json_keys(req, v, "mode,name", "") || !geo_json_string(req, geo_json_member(req, v, "name"), fresh, fresh_n)) return di_stop(p, 3, "重新命名需要 mode 與 name");
        } else if (!strcmp(mode, "map-existing")) {
            if (!geo_json_keys(req, v, "mode", "")) return di_stop(p, 3, "沿用既有名稱只接受 mode");
        } else return di_stop(p, 3, "未知的名稱處理");
    }
    return true;
}
static bool di_classify(DiPlan *p, const World *target, GeoJson *req)
{
    int names = geo_json_member(req, 0, "names");
    if (names < 0 || req->tokens[names].type != GEO_J_OBJECT) return di_stop(p, 3, "names 必須是物件");
    for (int k = names + 1; k < req->tokens[names].next && !p->schema; k = req->tokens[k + 1].next) {
        const char *key = req->tokens[k].string; bool closure = false, collide = false;
        if (!key) return di_stop(p, 3, "names 的鍵必須是字串");
        for (size_t i = 0; i < p->spec_n; ++i) if (!strcmp(p->specs[i].from, key)) { closure = true; collide = geo_named_values_find(&target->geo.named_values, key) != NULL; }
        if (!closure || !collide) { p->policy = true; di_note(p, "IMPORT_RENAME_UNNEEDED", key, "這個名稱不是需要處理的撞名規格"); }
    }
    if (p->schema) return false;
    for (size_t i = 0; i < p->spec_n; ++i) {
        DiSpec *s = &p->specs[i]; bool collide = geo_named_values_find(&target->geo.named_values, s->from) != NULL;
        if (!collide) { s->action = 0; snprintf(s->to, sizeof s->to, "%s", s->from); continue; }
        char mode[20], fresh[DI_NAME_MAX]; bool present = false;
        if (!di_name_choice(p, req, s->from, mode, sizeof mode, fresh, sizeof fresh, &present)) return false;
        if (!present) { p->policy = true; di_note(p, "IMPORT_RENAME_REQUIRED", s->from, "撞名規格必須明示重新命名或沿用既有名稱"); continue; }
        if (!strcmp(mode, "map-existing")) { s->action = 2; snprintf(s->to, sizeof s->to, "%s", s->from); continue; }
        if (!geo_named_value_name_valid(fresh)) { p->policy = true; di_note(p, "IMPORT_RENAME_GRAMMAR", fresh, "新名稱不符合具名規格文法"); continue; }
        bool bad = geo_named_values_find(&target->geo.named_values, fresh) != NULL || !strcmp(fresh, s->from);
        for (size_t q = 0; q < p->spec_n && !bad; ++q) if (!strcmp(p->specs[q].from, fresh) || (q != i && p->specs[q].to[0] && !strcmp(p->specs[q].to, fresh))) bad = true;
        if (bad) { p->policy = true; di_note(p, "IMPORT_RENAME_COLLISION", fresh, "新名稱與既有、閉包或另一個新名稱相撞"); continue; }
        s->action = 1; snprintf(s->to, sizeof s->to, "%s", fresh);
    }
    for (size_t i = 0; i < p->material_n && !p->unsupported; ++i) {
        DiMaterial *d = &p->materials[i];
        const EngMaterialVersion *have = NULL;
        for (size_t q = 0; q < target->wood.engineering.material_count; ++q) {
            const EngMaterialVersion *m = eng_material_at(target, q);
            if (m && !strcmp(m->ref.id, d->id) && m->ref.version == d->version) { have = m; break; }
        }
        if (!have) { d->action = 1; continue; }
        char have_hash[65]; di_material_hash(have, have_hash);
        if (strcmp(have_hash, d->fingerprint)) { p->policy = true; char label[80]; snprintf(label, sizeof label, "%s@%u", d->id, d->version); di_note(p, "IMPORT_FINGERPRINT", label, "同一材料版本的內容指紋不同，整批不匯入"); }
        else d->action = 0;
    }
    if (p->policy || p->schema || p->unsupported) return false;
    uint32_t cursor = 0;
    for (size_t i = 0; i < p->card_n; ++i) { while (parameter_find(target, cursor)) ++cursor; p->cards[i].to = cursor++; }
    uint32_t assigned[ASM_RULE_MAX]; size_t assigned_n = 0; uint32_t existing[ASM_RULE_MAX];
    size_t existing_n = target->wood.assembly.rule_count;
    for (size_t i = 0; i < existing_n; ++i) existing[i] = target->wood.assembly.rules[i].id;
    for (size_t i = 0; i < p->rule_n; ) {
        uint32_t source = p->rules[i].from_id, fresh; size_t end = i;
        while (end < p->rule_n && p->rules[end].from_id == source) ++end;
        if (!di_next_id(existing, existing_n, assigned, assigned_n, true, &fresh)) return di_stop(p, 1, "規則沒有可分配的新號碼");
        assigned[assigned_n++] = fresh;
        for (size_t q = i, version = 1; q < end; ++q, ++version) { p->rules[q].to_id = fresh; p->rules[q].to_version = (uint32_t)version; }
        i = end;
    }
    uint32_t bexist[ASM_BINDING_MAX], bnew[ASM_BINDING_MAX]; size_t bn = target->wood.assembly.binding_count, bnew_n = 0;
    for (size_t i = 0; i < bn; ++i) bexist[i] = target->wood.assembly.bindings[i].id;
    for (size_t i = 0; i < p->binding_n; ++i) {
        uint32_t fresh; if (!di_next_id(bexist, bn, bnew, bnew_n, true, &fresh)) return di_stop(p, 1, "配置沒有可分配的新號碼");
        bnew[bnew_n++] = fresh; p->bindings[i].to_id = fresh;
        for (size_t q = 0; q < p->rule_n; ++q) if (p->rules[q].from_id == p->bindings[i].rule_from && p->rules[q].from_version == p->bindings[i].rule_version) {
            p->bindings[i].rule_to = p->rules[q].to_id; p->bindings[i].rule_to_version = p->rules[q].to_version;
        }
        if (!p->bindings[i].rule_to) return di_stop(p, 0, "配置引用的規則不在閉包內");
    }
    return true;
}
static const char *di_spec_to(const DiPlan *p, const char *name)
{
    for (size_t i = 0; i < p->spec_n; ++i) if (!strcmp(p->specs[i].from, name)) return p->specs[i].to;
    return NULL;
}
static bool di_card_to(const DiPlan *p, uint32_t from, uint32_t *to)
{
    for (size_t i = 0; i < p->card_n; ++i) if (p->cards[i].from == from) { *to = p->cards[i].to; return true; }
    return false;
}
static bool di_replace_string(GeoJson *j, int token, const char *text)
{
    size_t n = strlen(text); char *copy = malloc(n + 1); if (!copy) return false;
    memcpy(copy, text, n + 1); free(j->tokens[token].string); j->tokens[token].string = copy; return true;
}
static bool di_walk(GeoJson *j, int t, const DiPlan *p, int depth)
{
    if (depth > 32 || t < 0) return false;
    int type = j->tokens[t].type;
    if (type != GEO_J_OBJECT && type != GEO_J_ARRAY) return true;
    if (type == GEO_J_ARRAY) {
        for (int i = 0; i < j->tokens[t].size; ++i) if (!di_walk(j, geo_json_at(j, t, i), p, depth + 1)) return false;
        return true;
    }
    int pid = geo_json_member(j, t, "parameterId");
    if (pid >= 0 && j->tokens[pid].type == GEO_J_INTEGER) {
        uint32_t neu; if (!di_card_to(p, (uint32_t)j->tokens[pid].number, &neu)) return false;
        j->tokens[pid].number = neu;
    }
    int kind = geo_json_member(j, t, "kind"); char k[16];
    if (kind >= 0 && geo_json_string(j, kind, k, sizeof k) && !strcmp(k, "spec")) {
        int name = geo_json_member(j, t, "name"); char buf[DI_NAME_MAX];
        if (name < 0 || !geo_json_string(j, name, buf, sizeof buf)) return false;
        const char *to = di_spec_to(p, buf); if (!to || (strcmp(to, buf) && !di_replace_string(j, name, to))) return false;
    }
    for (int q = t + 1; q < j->tokens[t].next; q = j->tokens[q + 1].next) if (!di_walk(j, q + 1, p, depth + 1)) return false;
    return true;
}
static bool di_import_cards(World *w, const World *src, const DiPlan *p)
{
    if (!p->card_n) return true;
    for (size_t i = 0; i < p->card_n; ++i) if (parameter_find(w, p->cards[i].to)) return eng_fail("參數配號與既有卡片衝突");
    FILE *file = tmpfile(); if (!file) return eng_fail("無法配置參數包");
    fputs("{\"schema\":\"geometry-parameters/1\",\"cards\":[", file);
    for (size_t i = 0; i < p->card_n; ++i) {
        const GeoParameterCard *cards = geo_parameters_cards(&src->geo.parameters); const GeoParameterCard *card = NULL;
        for (size_t q = 0; q < geo_parameters_card_count(&src->geo.parameters); ++q) if (cards[q].id == p->cards[i].from) card = &cards[q];
        if (!card) { fclose(file); return eng_fail("參數卡已不在來源"); }
        if (i) fputc(',', file); parameter_json_card(src, card, file, false);
    }
    fputs("]}", file);
    if (fflush(file) || fseek(file, 0, SEEK_END)) { fclose(file); return eng_fail("無法完成參數包"); }
    long n = ftell(file); if (n < 1 || n > GEO_JSON_MAX_INPUT || fseek(file, 0, SEEK_SET)) { fclose(file); return eng_fail("參數包超過 1 MiB"); }
    char *text = malloc((size_t)n + 1); if (!text) { fclose(file); return eng_fail("無法配置參數包"); }
    size_t got = fread(text, 1, (size_t)n, file); fclose(file); if (got != (size_t)n) { free(text); return eng_fail("參數包讀取不完整"); }
    text[got] = 0; GeoJson pack = {0}; bool ok = geo_json_parse_n(&pack, text, got) && parameter_import(w, &pack, 0); geo_json_free(&pack); free(text);
    if (!ok) return false;
    for (size_t i = 0; i < p->card_n; ++i) if (!parameter_find(w, p->cards[i].to)) return eng_fail("參數配號與 parameter_import 不一致");
    return true;
}
static bool di_apply_ops(World *w, const World *src, const DiPlan *p)
{
    if (!di_import_cards(w, src, p)) return false;
    for (size_t i = 0; i < p->spec_n; ++i) {
        const DiSpec *s = &p->specs[i]; if (s->action == 2) continue;
        if (!geo_named_values_put(&w->geo.named_values, s->to, s->value)) return eng_fail("具名規格無法寫入");
    }
    for (size_t i = 0; i < p->material_n; ++i) {
        const DiMaterial *d = &p->materials[i]; if (d->action == 0) continue;
        const EngMaterialVersion *m = eng_material_at(src, d->index); GeoJson body = {0};
        if (!m || !geo_json_parse(&body, m->content) || !eng_publish_material(w, &body, 0, NULL)) { geo_json_free(&body); return false; }
        geo_json_free(&body);
    }
    for (size_t i = 0; i < p->rule_n; ++i) {
        const DiRule *r = &p->rules[i]; GeoJson body = {0};
        if (!geo_json_parse(&body, src->wood.assembly.rules[r->index].content)) { geo_json_free(&body); return eng_fail("規則內容無法解析"); }
        int id = geo_json_member(&body, 0, "id"), version = geo_json_member(&body, 0, "version");
        if (id < 0 || version < 0) { geo_json_free(&body); return eng_fail("規則缺少身分"); }
        body.tokens[id].number = r->to_id; body.tokens[version].number = r->to_version;
        bool ok = asm_publish(w, &body, 0, NULL); geo_json_free(&body); if (!ok) return false;
    }
    for (size_t i = 0; i < p->binding_n; ++i) {
        const DiBinding *b = &p->bindings[i]; GeoJson body = {0};
        if (!geo_json_parse(&body, src->wood.assembly.bindings[b->index].content)) { geo_json_free(&body); return eng_fail("配置內容無法解析"); }
        int id = geo_json_member(&body, 0, "id"), rule = geo_json_member(&body, 0, "rule");
        if (id < 0 || rule < 0) { geo_json_free(&body); return eng_fail("配置缺少身分"); }
        body.tokens[id].number = b->to_id;
        body.tokens[geo_json_member(&body, rule, "id")].number = b->rule_to;
        body.tokens[geo_json_member(&body, rule, "version")].number = b->rule_to_version;
        bool ok = di_walk(&body, 0, p, 0) && asm_put_binding(w, &body, 0); geo_json_free(&body); if (!ok) return false;
    }
    return true;
}
typedef struct { const World *source, *before; const DiPlan *plan; } DiApply;
static bool di_apply_candidate(void *after, GeoEvalContext *sources, void *opaque)
{
    (void)sources; DiApply *call = opaque; World *candidate = after; bool ok = true;
    ParameterCandidateScope scope;
    if (!parameters_begin_candidate(candidate, &scope)) ok = eng_fail(g_parameter_error);
    if (ok) ok = di_apply_ops(candidate, call->source, call->plan);
    if (ok) receipt_scan_candidate(candidate);
    if (scope.ledger) {
        if (ok && !parameter_retirements_valid(candidate)) ok = eng_fail(g_parameter_error);
        parameters_end_candidate(&scope);
    }
    if (ok) ok = assembly_versions_immutable(call->before, candidate);
    if (ok) {
        const World *previous = g_subgrid_before; bool capturing = g_reference_capturing;
        g_reference_capturing = true; g_reference_trial = *candidate; g_subgrid_before = call->before;
        ok = world_revalidate(candidate); g_subgrid_before = previous; g_reference_capturing = capturing;
        if (!ok) { *candidate = g_reference_trial; if (!g_engineering_error[0]) eng_fail(g_revalidate_error[0] ? g_revalidate_error : "I35: candidate geometry is invalid"); }
    }
    return ok;
}
static void di_json_notes(const DiPlan *p)
{
    fputs(",\"conflicts\":[", stdout); bool first = true;
    for (size_t i = 0; i < p->note_n; ++i) if (!strcmp(p->notes[i].code, "IMPORT_FINGERPRINT")) { printf("%s{\"code\":", first ? "" : ","); js_string(p->notes[i].code); fputs(",\"name\":", stdout); js_string(p->notes[i].name); fputs(",\"message\":", stdout); js_string(p->notes[i].message); putchar('}'); first = false; }
    fputs("],\"diagnostics\":[", stdout); first = true;
    for (size_t i = 0; i < p->note_n; ++i) if (strcmp(p->notes[i].code, "IMPORT_FINGERPRINT")) { printf("%s{\"code\":", first ? "" : ","); js_string(p->notes[i].code); fputs(",\"name\":", stdout); js_string(p->notes[i].name); fputs(",\"message\":", stdout); js_string(p->notes[i].message); putchar('}'); first = false; }
    putchar(']');
}
static void di_json_map(const DiPlan *p, const World *after)
{
    fputs("\"map\":{\"rules\":[", stdout);
    for (size_t i = 0; i < p->rule_n; ++i) printf("%s{\"class\":\"world-local\",\"action\":\"create\",\"from\":{\"id\":%u,\"version\":%u},\"to\":{\"id\":%u,\"version\":%u}}", i ? "," : "", p->rules[i].from_id, p->rules[i].from_version, p->rules[i].to_id, p->rules[i].to_version);
    fputs("],\"bindings\":[", stdout);
    for (size_t i = 0; i < p->binding_n; ++i) printf("%s{\"class\":\"world-local\",\"action\":\"create\",\"from\":%u,\"to\":%u}", i ? "," : "", p->bindings[i].from_id, p->bindings[i].to_id);
    fputs("],\"parameters\":[", stdout);
    for (size_t i = 0; i < p->card_n; ++i) printf("%s{\"class\":\"world-local\",\"action\":\"create\",\"from\":%u,\"to\":%u}", i ? "," : "", p->cards[i].from, p->cards[i].to);
    fputs("],\"specs\":[", stdout);
    for (size_t i = 0; i < p->spec_n; ++i) { const char *action = p->specs[i].action == 1 ? "rename" : p->specs[i].action == 2 ? "map-existing" : "create"; printf("%s{\"class\":\"name\",\"action\":", i ? "," : ""); js_string(action); fputs(",\"from\":", stdout); js_string(p->specs[i].from); fputs(",\"to\":", stdout); js_string(p->specs[i].to); putchar('}'); }
    fputs("],\"materials\":[", stdout);
    for (size_t i = 0; i < p->material_n; ++i) { printf("%s{\"class\":\"content-global\",\"action\":", i ? "," : ""); js_string(p->materials[i].action ? "create" : "share"); printf(",\"id\":"); js_string(p->materials[i].id); printf(",\"version\":%u,\"fingerprint\":", p->materials[i].version); js_string(p->materials[i].fingerprint); putchar('}'); }
    fputs("]},\"bindings\":[", stdout);
    if (after) for (size_t i = 0; i < p->binding_n; ++i) {
        const AsmBinding *b = di_binding(after, p->bindings[i].to_id); printf("%s{\"id\":%u,\"slots\":[", i ? "," : "", p->bindings[i].to_id);
        GeoJson body = {0}; bool parsed = b && geo_json_parse(&body, b->content); int slots = parsed ? geo_json_member(&body, 0, "slots") : -1;
        WoodAssemblyContext ctx = app_asm_context(after);
        for (int s = 0; parsed && s < geo_json_size(&body, slots); ++s) {
            int t = geo_json_at(&body, slots, s); uint32_t slot = 0; di_u32(&body, geo_json_member(&body, t, "slotId"), &slot, true);
            printf("%s{\"slotId\":%u", s ? "," : "", slot);
            for (int axis = 0; axis < 2; ++axis) {
                int value = geo_json_member(&body, t, axis ? "B" : "A"); printf(",\"%c\":", axis ? 'B' : 'A');
                Coord effective = 0; char path[192];
                if (value < 0 || geo_json_is_null(&body, value)) fputs("{\"effective\":null,\"path\":null}", stdout);
                else if (wood_assembly_slot_dimension_direct(&ctx, p->bindings[i].to_id, slot, axis, &effective, path, sizeof path)) { printf("{\"effective\":%lld,\"path\":", (long long)effective); js_string(path); putchar('}'); }
                else fputs("{\"effective\":null,\"path\":null}", stdout);
            }
            fputs("}", stdout);
        }
        geo_json_free(&body); fputs("]}", stdout);
    }
    putchar(']');
}
static void di_json_definitions(const World *w)
{
    fputs("{\"rules\":[", stdout);
    for (size_t i = 0; i < w->wood.assembly.rule_count; ++i) { const AsmRuleVersion *r = &w->wood.assembly.rules[i]; printf("%s{\"id\":%u,\"version\":%u,\"name\":", i ? "," : "", r->id, r->version); js_string(r->name); putchar('}'); }
    fputs("],\"bindings\":[", stdout);
    for (size_t i = 0; i < w->wood.assembly.binding_count; ++i) { const AsmBinding *b = &w->wood.assembly.bindings[i]; printf("%s{\"id\":%u,\"name\":", i ? "," : "", b->id); js_string(b->name); printf(",\"rule\":{\"id\":%u,\"version\":%u},\"content\":%s}", b->rule_id, b->rule_version, b->content); }
    fputs("],\"parameters\":[", stdout);
    for (size_t i = 0; i < geo_parameters_card_count(&w->geo.parameters); ++i) { if (i) putchar(','); parameter_json_card(w, &geo_parameters_cards(&w->geo.parameters)[i], stdout, false); }
    fputs("],\"specs\":[", stdout);
    for (size_t i = 0; i < geo_named_values_count(&w->geo.named_values); ++i) { const GeoNamedValue *v = geo_named_values_at(&w->geo.named_values, i); printf("%s{\"name\":", i ? "," : ""); js_string(v->name); printf(",\"value\":%lld}", (long long)v->value); }
    fputs("],\"materials\":[", stdout);
    for (size_t i = 0; i < w->wood.engineering.material_count; ++i) {
        const EngMaterialVersion *m = eng_material_at(w, i); char hash[65]; if (!m) continue; di_material_hash(m, hash);
        printf("%s{\"id\":", i ? "," : ""); js_string(m->ref.id); printf(",\"version\":%u,\"kind\":%s,\"fingerprint\":", m->ref.version, m->kind ? "\"timber\"" : "\"panel\""); js_string(hash); printf(",\"archived\":%s,\"content\":%s}", m->archived ? "true" : "false", m->content);
    }
    fputs("]}", stdout);
}
static bool di_load_isolated(const char *path, AppWorldCandidate **out)
{
    *out = app_world_candidate_create(&g_world); if (!*out) { eng_bridge_error("MEMORY", "無法配置隔離場景"); return false; }
    g_engineering_error[0] = 0; g_scene_last_error[0] = 0;
    if (app_world_candidate_evaluate(*out, app_scene_load_evaluate, (void *)path) != GEO_CANDIDATE_OK) {
        const char *error = scene_last_error();
        bool unsupported = error && (strstr(error, "unsupported") || strstr(error, "UNSUPPORTED"));
        eng_bridge_error(unsupported ? "UNSUPPORTED" : "VALIDATION", error && error[0] ? error : "無法讀取來源場景");
        app_world_candidate_destroy(*out); *out = NULL; return false;
    }
    return true;
}
static void cmd_definition_import_read(const char *path)
{
    if (!path || !path[0]) { eng_bridge_error("SCHEMA", "需要來源場景檔"); return; }
    const char *error = NULL; size_t n = 0; char *text = di_read(path, &n, DI_SCENE_MAX, &error);
    if (!text) { eng_bridge_error(error && strstr(error, "超過") ? "CAPACITY" : "INPUT", error); return; }
    char hash[65]; di_hash_bytes(text, n, hash); free(text);
    AppWorldCandidate *source = NULL; if (!di_load_isolated(path, &source)) return;
    printf("{\"ok\":true,\"scene_sha256\":\"%s\",", hash); json_engineering_capabilities(&source->after); fputs(",\"definitions\":", stdout); di_json_definitions(&source->after); fputs("}\n", stdout);
    app_world_candidate_destroy(source);
}
static void cmd_definition_import_preview(const char *dir)
{
    if (g_history.grouping) { eng_bridge_error("HISTORY_GROUP", "請先結束目前的歷史群組"); return; }
    if (g_preview.ready) { eng_bridge_error("TOKEN", "請先確認或取消目前的預覽"); return; }
    if (!dir || !dir[0]) { eng_bridge_error("SCHEMA", "需要匯入目錄"); return; }
    char request_path[1024], scene_path[1024];
    if (!di_join(request_path, sizeof request_path, dir, "request.json") || !di_join(scene_path, sizeof scene_path, dir, "source.scene")) { eng_bridge_error("INPUT", "匯入路徑過長"); return; }
    const char *error = NULL; size_t request_n = 0, scene_n = 0;
    char *request = di_read(request_path, &request_n, GEO_JSON_MAX_INPUT, &error);
    if (!request) { eng_bridge_error("INPUT", error ? error : "無法讀取匯入請求"); return; }
    char *scene = di_read(scene_path, &scene_n, DI_SCENE_MAX, &error);
    if (!scene) { free(request); eng_bridge_error(error && strstr(error, "超過") ? "CAPACITY" : "INPUT", error); return; }
    char scene_hash[65]; di_hash_bytes(scene, scene_n, scene_hash); free(scene);
    GeoJson req = {0}; DiPlan *plan = calloc(1, sizeof *plan); AppWorldCandidate *source = NULL, *target = NULL; bool staged = false;
    if (!plan) { free(request); eng_bridge_error("MEMORY", "無法配置匯入計畫"); return; }
    if (!geo_json_parse_n(&req, request, request_n)) { eng_bridge_error("JSON", req.error[0] ? req.error : "匯入請求不是 JSON"); goto done; }
    char schema[40], given[80]; int64_t revision = -1;
    if (!geo_json_keys(&req, 0, "schema,expectedRevision,sourceSceneSha256,roots,names", "") || !geo_json_string(&req, geo_json_member(&req, 0, "schema"), schema, sizeof schema) || strcmp(schema, "definition-import/1") || !geo_json_integer(&req, geo_json_member(&req, 0, "expectedRevision"), &revision) || revision < 0 || !geo_json_string(&req, geo_json_member(&req, 0, "sourceSceneSha256"), given, sizeof given) || !di_hex64(given)) {
        eng_bridge_error("SCHEMA", "需要 definition-import/1、expectedRevision、來源摘要、roots 與 names"); goto done;
    }
    if ((uint64_t)revision != g_definition_revision) { eng_bridge_error("STALE", "目標定義已變更，請重新預覽"); goto done; }
    if (strcmp(given, scene_hash)) { eng_bridge_error("INVALID", "來源場景摘要不符"); goto done; }
    g_engineering_error[0] = 0; g_scene_last_error[0] = 0;
    source = app_world_candidate_create(&g_world);
    if (!source || app_world_candidate_evaluate(source, app_scene_load_evaluate, scene_path) != GEO_CANDIDATE_OK) {
        const char *load_error = scene_last_error(); bool unsupported = load_error && (strstr(load_error, "unsupported") || strstr(load_error, "UNSUPPORTED"));
        eng_bridge_error(unsupported ? "UNSUPPORTED" : "VALIDATION", load_error && load_error[0] ? load_error : "無法讀取來源場景"); goto done;
    }
    if (!di_collect(plan, &source->after, &req) || !di_classify(plan, &g_world, &req)) {
        if (plan->unsupported) eng_bridge_error("UNSUPPORTED", plan->error[0] ? plan->error : "首版不支援這個匯入");
        else if (plan->schema) eng_bridge_error("SCHEMA", plan->error[0] ? plan->error : "匯入請求不符合 schema");
        else if (plan->policy) { fputs("{\"ok\":true,\"preview\":{\"valid\":false", stdout); di_json_notes(plan); fputs("}}\n", stdout); }
        else eng_bridge_error("INVALID", plan->error[0] ? plan->error : g_engineering_error);
        goto done;
    }
    target = app_world_candidate_create(&g_world);
    if (!target) { eng_bridge_error("MEMORY", "無法配置匯入候選"); goto done; }
    DiApply call = {&source->after, &target->before, plan};
    g_engineering_error[0] = 0; g_scene_last_error[0] = 0; g_reference_issue_count = 0;
    bool ok = app_world_candidate_evaluate(target, di_apply_candidate, &call) == GEO_CANDIDATE_OK && app_world_candidate_seal(target);
    if (!ok) { eng_bridge_error("INVALID", g_engineering_error[0] ? g_engineering_error : (scene_last_error()[0] ? scene_last_error() : "匯入候選無法封存")); goto done; }
    app_world_candidate_destroy(source); source = NULL;
    char *label = "definition-import"; reference_stage(target, &label, 1, true); staged = true; g_preview.definition_import = true;
    snprintf(g_di_sha, sizeof g_di_sha, "%s", scene_hash); g_di_sha_token = g_preview.token;
    printf("{\"ok\":true,\"preview\":{\"valid\":true,\"token\":%u,\"revision\":%llu,", g_preview.token, (unsigned long long)g_preview.revision);
    di_json_map(plan, &target->after); di_json_notes(plan); fputs("}}\n", stdout);
done:
    geo_json_free(&req); free(request); free(plan);
    if (source) app_world_candidate_destroy(source);
    if (target && !staged) app_world_candidate_destroy(target);
}
static void cmd_definition_import_confirm(const char *arg)
{
    uint32_t token;
    if (!arg || !parse_u32(arg, &token) || !g_preview.ready || !g_preview.definition_import || g_preview.token != token || !g_preview.valid || g_di_sha_token != token) { eng_bridge_error("TOKEN", "需要有效的定義匯入預覽權杖"); return; }
    if (g_history.grouping || g_preview.revision != g_definition_revision || !app_world_candidate_current(g_preview.transaction, &g_world)) { g_preview.ready = false; eng_bridge_error("STALE", "定義匯入預覽已過期"); return; }
    if (!assembly_versions_immutable(&g_world, &g_preview.transaction->after)) { g_preview.ready = false; eng_bridge_error("INVALID", g_engineering_error); return; }
    if (!app_world_candidate_revalidate(g_preview.transaction, &g_world)) { g_preview.ready = false; eng_bridge_error("INVALID", g_revalidate_error); return; }
    bool changed = !world_definitions_equal(&g_world, &g_preview.transaction->after); uint64_t before = g_definition_revision;
    if (changed) history_record(&g_world);
    if (!app_world_candidate_publish(g_preview.transaction, &g_world, true)) { if (changed) history_unrecord(); g_preview.ready = false; eng_bridge_error("STALE", "定義匯入預覽已過期"); return; }
    if (changed) ++g_definition_revision;
    g_preview.ready = false; g_di_sha_token = 0;
    printf("{\"ok\":true,\"history_changed\":%s,\"revision\":%llu,\"before_revision\":%llu,\"transaction_id\":%u}\n", changed ? "true" : "false", (unsigned long long)g_definition_revision, (unsigned long long)before, token);
}
static void cmd_definition_import_cancel(const char *arg)
{
    uint32_t token; if (!arg || !parse_u32(arg, &token)) { eng_bridge_error("TOKEN", "取消需要定義匯入預覽權杖"); return; }
    bool cancelled = g_preview.ready && g_preview.definition_import && g_preview.token == token;
    if (cancelled) { g_preview.ready = false; g_di_sha_token = 0; app_candidate_discard(g_preview.transaction->control); }
    printf("{\"ok\":true,\"cancelled\":%s,\"revision\":%llu}\n", cancelled ? "true" : "false", (unsigned long long)g_definition_revision);
}
