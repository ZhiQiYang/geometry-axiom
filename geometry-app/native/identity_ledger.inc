/* Identity ledger (D59–D62, I70–I72, R56–R58). Layer H: coverage skips
 * assembly-owned timbers via assembly_owned(). Epoch and the serial counter
 * are process state, not World fields, so undo restores marks without
 * rewinding the counter. Derived placements (derived_fill_id != 0) are left
 * out of coverage: world_dump_dsl already skips them and world_revalidate
 * recreates them after identity lines. D59 names every placement; that
 * exclusion is an open question, not a settled exception. */
static uint8_t g_identity_epoch[16];
static bool g_identity_epoch_set;
static bool g_identity_serial_exhausted;
static uint64_t g_identity_next_serial = 1;
static uint64_t g_identity_pending_count;
static bool g_identity_include_marks = true;
static bool g_identity_requires_seen;
static bool g_identity_explicit_preview;
static bool g_identity_explicit_overflow;
static AppIdentityKey g_identity_explicit[APP_IDENTITY_MARK_CAPACITY];
static size_t g_identity_explicit_count;

static void identity_explicit_reset(void)
{
    g_identity_explicit_count = 0;
    g_identity_explicit_overflow = false;
}
static void identity_note_key(uint8_t kind, uint32_t id, uint32_t field_id)
{
    if (g_parsing_scene_file) return;
    for (size_t i = 0; i < g_identity_explicit_count; ++i) {
        const AppIdentityKey *k = &g_identity_explicit[i];
        if (k->kind == kind && k->id == id && k->field_id == field_id) return;
    }
    if (g_identity_explicit_count == APP_IDENTITY_MARK_CAPACITY) {
        g_identity_explicit_overflow = true;
        return;
    }
    g_identity_explicit[g_identity_explicit_count++] = (AppIdentityKey){kind, id, field_id};
}
static void identity_explicit_capture(AppIdentityKey *dst, size_t cap, size_t *count, bool *overflow)
{
    size_t n = g_identity_explicit_count;
    if (n > cap) n = cap;
    if (n) memcpy(dst, g_identity_explicit, n * sizeof *dst);
    *count = g_identity_explicit_count;
    *overflow = g_identity_explicit_overflow || g_identity_explicit_count > cap;
    identity_explicit_reset();
}
static void identity_drop_serials(void) { g_identity_pending_count = 0; }
static void identity_commit_serials(void)
{
    if (!g_identity_pending_count) return;
    uint64_t sum = g_identity_next_serial + g_identity_pending_count;
    bool wrapped = sum < g_identity_next_serial;
    g_identity_next_serial = wrapped ? 0 : sum;
    if (wrapped) g_identity_serial_exhausted = true;
    g_identity_pending_count = 0;
}
static bool identity_accept_requires(const char *path, int line_no, World *w)
{
    if (!g_parsing_scene_file) {
        scene_error(path, line_no, "I71: identity-ledger/1 只能由場景檔宣告；啟用請用 identity-ledger activate");
        return false;
    }
    g_identity_requires_seen = true;
    w->app.identity_active = true;
    return true;
}
static const char *identity_kind_name(uint8_t kind)
{
    switch (kind) {
    case APP_IDENTITY_BOUNDARY: return "boundary";
    case APP_IDENTITY_PLACEMENT: return "placement";
    case APP_IDENTITY_COLUMN: return "column";
    case APP_IDENTITY_BEAM: return "beam";
    case APP_IDENTITY_TIMBER: return "timber";
    case APP_IDENTITY_PARAMETER: return "parameter";
    case APP_IDENTITY_FIELD: return "parameter-field";
    default: return NULL;
    }
}
static int identity_hex(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}
static bool identity_parse_serial(const char *text, uint64_t *out)
{
    if (!text || text[0] < '1' || text[0] > '9') return false;
    uint64_t value = 0;
    for (const char *p = text; *p; ++p) {
        if (*p < '0' || *p > '9') return false;
        uint64_t digit = (uint64_t)(*p - '0');
        if (value > (UINT64_MAX - digit) / 10) return false;
        value = value * 10 + digit;
    }
    *out = value;
    return true;
}
static bool identity_parse_mark(const char *text, uint8_t epoch[16], uint64_t *serial)
{
    if (!text) return false;
    for (int i = 0; i < 32; ++i) if (identity_hex(text[i]) < 0) return false;
    if (text[32] != ':') return false;
    for (int i = 0; i < 16; ++i) epoch[i] = (uint8_t)((identity_hex(text[i * 2]) << 4) | identity_hex(text[i * 2 + 1]));
    return identity_parse_serial(text + 33, serial);
}
static bool identity_format_mark(const AppIdentityMark *mark, char *out, size_t cap)
{
    if (cap < 54) return false;
    for (int i = 0; i < 16; ++i) sprintf(out + i * 2, "%02x", mark->epoch[i]);
    sprintf(out + 32, ":%llu", (unsigned long long)mark->serial);
    return mark->serial >= 1;
}
static int identity_key_cmp(uint8_t ak, uint32_t aid, uint32_t af, uint8_t bk, uint32_t bid, uint32_t bf)
{
    if (ak != bk) return ak < bk ? -1 : 1;
    if (aid != bid) return aid < bid ? -1 : 1;
    if (af != bf) return af < bf ? -1 : 1;
    return 0;
}
static void identity_fail(const char *message)
{
    snprintf(g_scene_last_error, sizeof g_scene_last_error, "%s", message);
}
static bool identity_push_key(AppIdentityKey *keys, size_t *count, uint8_t kind, uint32_t id, uint32_t field)
{
    if (*count == APP_IDENTITY_MARK_CAPACITY) return false;
    keys[(*count)++] = (AppIdentityKey){kind, id, field};
    return true;
}
static bool identity_collect(const World *w, AppIdentityKey *keys, size_t *count)
{
    *count = 0;
    for (size_t i = 0; i < world_boundary_count(w); ++i)
        if (!identity_push_key(keys, count, APP_IDENTITY_BOUNDARY, world_boundary_at(w, i)->id, 0)) return false;
    for (size_t i = 0; i < world_placement_count(w); ++i) {
        const PlacementSurface *p = world_placement_at(w, i);
        if (p->derived_fill_id) continue;
        if (!identity_push_key(keys, count, APP_IDENTITY_PLACEMENT, p->id, 0)) return false;
    }
    for (size_t i = 0; i < w->wood.column_count; ++i)
        if (!identity_push_key(keys, count, APP_IDENTITY_COLUMN, w->wood.columns[i].id, 0)) return false;
    for (size_t i = 0; i < w->wood.beam_count; ++i)
        if (!identity_push_key(keys, count, APP_IDENTITY_BEAM, w->wood.beams[i].id, 0)) return false;
    for (size_t i = 0; i < w->wood.timber_count; ++i) {
        if (assembly_owned(w, w->wood.timbers[i].id)) continue;
        if (!identity_push_key(keys, count, APP_IDENTITY_TIMBER, w->wood.timbers[i].id, 0)) return false;
    }
    const GeoParameterCard *cards = geo_parameters_cards(&w->geo.parameters);
    for (size_t i = 0; i < geo_parameters_card_count(&w->geo.parameters); ++i) {
        const GeoParameterCard *card = &cards[i];
        if (!identity_push_key(keys, count, APP_IDENTITY_PARAMETER, card->id, 0)) return false;
        for (size_t k = 0; k < card->count; ++k)
            if (!identity_push_key(keys, count, APP_IDENTITY_FIELD, card->id, card->fields[k])) return false;
    }
    for (size_t i = 1; i < *count; ++i) {
        AppIdentityKey key = keys[i];
        size_t j = i;
        while (j > 0 && identity_key_cmp(keys[j - 1].kind, keys[j - 1].id, keys[j - 1].field_id, key.kind, key.id, key.field_id) > 0) {
            keys[j] = keys[j - 1];
            --j;
        }
        keys[j] = key;
    }
    return true;
}
static void identity_name_key(char *out, size_t cap, uint8_t kind, uint32_t id, uint32_t field)
{
    const char *name = identity_kind_name(kind);
    if (kind == APP_IDENTITY_FIELD) snprintf(out, cap, "parameter-field %u %u", id, field);
    else snprintf(out, cap, "%s %u", name ? name : "unknown", id);
}
static bool identity_table_ok(const AppIdentityKey *keys, size_t key_count, const AppIdentityMark *marks, size_t mark_count, char *err, size_t cap)
{
    size_t i = 0, j = 0;
    while (i < key_count || j < mark_count) {
        int cmp;
        if (i == key_count) cmp = 1;
        else if (j == mark_count) cmp = -1;
        else cmp = identity_key_cmp(keys[i].kind, keys[i].id, keys[i].field_id, marks[j].kind, marks[j].id, marks[j].field_id);
        char label[80];
        if (cmp < 0) {
            identity_name_key(label, sizeof label, keys[i].kind, keys[i].id, keys[i].field_id);
            snprintf(err, cap, "I70: 缺少 %s 的記號", label);
            return false;
        }
        if (cmp > 0) {
            identity_name_key(label, sizeof label, marks[j].kind, marks[j].id, marks[j].field_id);
            snprintf(err, cap, "I70: 多餘的 %s 記號", label);
            return false;
        }
        if (!identity_kind_name(marks[j].kind) || marks[j].serial < 1 || (marks[j].kind == APP_IDENTITY_FIELD ? false : marks[j].field_id != 0)) {
            snprintf(err, cap, "I70: 記號格式不符");
            return false;
        }
        for (size_t earlier = 0; earlier < j; ++earlier) {
            if (!memcmp(marks[earlier].epoch, marks[j].epoch, 16) && marks[earlier].serial == marks[j].serial) {
                snprintf(err, cap, "I70: 記號重複");
                return false;
            }
        }
        ++i;
        ++j;
    }
    return true;
}
static bool identity_check_world(const World *w, char *err, size_t cap)
{
    AppIdentityKey keys[APP_IDENTITY_MARK_CAPACITY];
    size_t count = 0;
    if (!identity_collect(w, keys, &count)) {
        snprintf(err, cap, "I33: 身分鍵超過 1024");
        return false;
    }
    return identity_table_ok(keys, count, w->app.identity_marks, w->app.identity_mark_count, err, cap);
}
static bool identity_dump_ok(const World *w, char *err, size_t cap)
{
    if (!w->app.identity_active) return true;
    return identity_check_world(w, err, cap);
}
static bool identity_explicit_has(const AppIdentityKey *keys, size_t count, const AppIdentityKey *key)
{
    for (size_t i = 0; i < count; ++i)
        if (keys[i].kind == key->kind && keys[i].id == key->id && keys[i].field_id == key->field_id) return true;
    return false;
}
static const AppIdentityMark *identity_find_mark(const World *w, const AppIdentityKey *key)
{
    for (uint32_t i = 0; i < w->app.identity_mark_count; ++i) {
        const AppIdentityMark *mark = &w->app.identity_marks[i];
        if (mark->kind == key->kind && mark->id == key->id && mark->field_id == key->field_id) return mark;
    }
    return NULL;
}
static bool identity_prepare(const World *before, World *after, const AppIdentityKey *explicit_keys, size_t explicit_count, bool explicit_overflow)
{
    if (g_parsing_scene_file) return true;
    if (explicit_overflow) {
        identity_fail("I33: 明示刪除超過身分帳容量");
        identity_drop_serials();
        return false;
    }
    bool before_on = before->app.identity_active;
    bool after_on = after->app.identity_active;
    if (!before_on && !after_on) {
        after->app.identity_active = false;
        after->app.identity_mark_count = 0;
        memset(after->app.identity_marks, 0, sizeof after->app.identity_marks);
        identity_drop_serials();
        return true;
    }
    AppIdentityKey after_keys[APP_IDENTITY_MARK_CAPACITY];
    size_t after_count = 0;
    if (!identity_collect(after, after_keys, &after_count)) {
        identity_fail("I33: 身分鍵超過 1024");
        identity_drop_serials();
        return false;
    }
    uint64_t need = 0;
    for (size_t i = 0; i < after_count; ++i) {
        bool fresh = !before_on || identity_explicit_has(explicit_keys, explicit_count, &after_keys[i]) || !identity_find_mark(before, &after_keys[i]);
        if (fresh) ++need;
    }
    if (need) {
        if (!g_identity_epoch_set) {
            identity_fail("未設定配號區段");
            identity_drop_serials();
            return false;
        }
        if (g_identity_serial_exhausted || g_identity_next_serial == 0 || need > UINT64_MAX - g_identity_next_serial + 1) {
            identity_fail("I33: 身分序號已達上限");
            identity_drop_serials();
            return false;
        }
    }
    AppIdentityMark *built = calloc(APP_IDENTITY_MARK_CAPACITY, sizeof *built);
    if (!built) {
        identity_fail("I33: 身分帳記憶體不足");
        identity_drop_serials();
        return false;
    }
    uint64_t serial = g_identity_next_serial;
    for (size_t i = 0; i < after_count; ++i) {
        const AppIdentityMark *old = before_on ? identity_find_mark(before, &after_keys[i]) : NULL;
        bool explicit_delete = identity_explicit_has(explicit_keys, explicit_count, &after_keys[i]);
        if (before_on && !explicit_delete && old) {
            built[i] = *old;
        } else {
            /* 不得沿用舊記號 */
            memset(&built[i], 0, sizeof built[i]);
            built[i].kind = after_keys[i].kind;
            memcpy(built[i].epoch, g_identity_epoch, 16);
            built[i].id = after_keys[i].id;
            built[i].field_id = after_keys[i].field_id;
            built[i].serial = serial++;
        }
    }
    char problem[192];
    bool ok = identity_table_ok(after_keys, after_count, built, after_count, problem, sizeof problem);
    if (!ok) identity_fail(problem);
    else {
        memset(after->app.identity_marks, 0, sizeof after->app.identity_marks);
        if (after_count) memcpy(after->app.identity_marks, built, after_count * sizeof *built);
        after->app.identity_mark_count = (uint32_t)after_count;
        after->app.identity_active = true;
        g_identity_pending_count = need;
    }
    free(built);
    if (!ok) identity_drop_serials();
    return ok;
}
static bool identity_prepare_scratch(const World *before, World *after)
{
    AppIdentityKey keys[APP_IDENTITY_MARK_CAPACITY];
    size_t count = 0;
    bool overflow = false;
    identity_explicit_capture(keys, APP_IDENTITY_MARK_CAPACITY, &count, &overflow);
    return identity_prepare(before, after, keys, count, overflow);
}
static bool identity_set_epoch(const char *hex, char *err, size_t cap)
{
    if (!hex) {
        snprintf(err, cap, "配號區段須是 32 位小寫十六進位");
        return false;
    }
    uint8_t epoch[16];
    uint64_t ignored = 0;
    char text[64];
    if (strlen(hex) != 32) {
        snprintf(err, cap, "配號區段須是 32 位小寫十六進位");
        return false;
    }
    memcpy(text, hex, 32);
    memcpy(text + 32, ":1", 3);
    if (!identity_parse_mark(text, epoch, &ignored)) {
        snprintf(err, cap, "配號區段須是 32 位小寫十六進位");
        return false;
    }
    for (uint32_t i = 0; i < g_world.app.identity_mark_count; ++i) {
        if (!memcmp(g_world.app.identity_marks[i].epoch, epoch, 16)) {
            snprintf(err, cap, "配號區段已出現在目前記號");
            return false;
        }
    }
    memcpy(g_identity_epoch, epoch, 16);
    g_identity_epoch_set = true;
    return true;
}
static void identity_sort_marks(World *w)
{
    for (uint32_t i = 1; i < w->app.identity_mark_count; ++i) {
        AppIdentityMark mark = w->app.identity_marks[i];
        uint32_t j = i;
        while (j > 0 && identity_key_cmp(w->app.identity_marks[j - 1].kind, w->app.identity_marks[j - 1].id, w->app.identity_marks[j - 1].field_id, mark.kind, mark.id, mark.field_id) > 0) {
            w->app.identity_marks[j] = w->app.identity_marks[j - 1];
            --j;
        }
        w->app.identity_marks[j] = mark;
    }
}
static bool identity_finish_load(const char *path, int line_no, World *w)
{
    if (!g_identity_requires_seen) {
        if (w->app.identity_active || w->app.identity_mark_count) {
            scene_error(path, line_no, "I72: 有記號但沒有 requires identity-ledger/1");
            return false;
        }
        return true;
    }
    w->app.identity_active = true;
    identity_sort_marks(w);
    char problem[192];
    if (!identity_check_world(w, problem, sizeof problem)) {
        scene_error(path, line_no, problem);
        return false;
    }
    return true;
}
static void identity_dump_requires(const World *w, FILE *out)
{
    if (!g_identity_include_marks || !w->app.identity_active) return;
    fputs("requires identity-ledger/1\n", out);
}
static void identity_dump_lines(const World *w, FILE *out)
{
    if (!g_identity_include_marks || !w->app.identity_active) return;
    for (uint32_t i = 0; i < w->app.identity_mark_count; ++i) {
        const AppIdentityMark *mark = &w->app.identity_marks[i];
        char text[64];
        if (!identity_format_mark(mark, text, sizeof text)) continue;
        if (mark->kind == APP_IDENTITY_FIELD) fprintf(out, "identity parameter-field %u %u %s\n", mark->id, mark->field_id, text);
        else fprintf(out, "identity %s %u %s\n", identity_kind_name(mark->kind), mark->id, text);
    }
}
static bool apply_identity_ledger_line(const char *path, int line_no, char *tokens[], int count, World *world)
{
    (void)count;
    if (strcmp(tokens[1], "activate") != 0) {
        scene_error(path, line_no, "I71: identity-ledger 只接受 activate");
        return false;
    }
    if (g_parsing_scene_file) {
        scene_error(path, line_no, "I71: 場景檔不得使用 identity-ledger activate");
        return false;
    }
    if (g_history.grouping || g_identity_explicit_preview) {
        scene_error(path, line_no, "啟用必須是單獨一筆提交");
        return false;
    }
    if (world->app.identity_active) {
        scene_error(path, line_no, "身分帳已啟用");
        return false;
    }
    if (!g_identity_epoch_set) {
        scene_error(path, line_no, "未設定配號區段");
        return false;
    }
    world->app.identity_active = true;
    return true;
}
static bool apply_identity_line(const char *path, int line_no, char *tokens[], int count, World *world)
{
    if (!g_parsing_scene_file) {
        scene_error(path, line_no, "I71: 互動輸入不得宣告 identity");
        return false;
    }
    if (!g_identity_requires_seen) {
        scene_error(path, line_no, "I72: 記號行缺少 requires identity-ledger/1");
        return false;
    }
    bool field = strcmp(tokens[1], "parameter-field") == 0;
    if (field ? count != 5 : count != 4) {
        scene_error(path, line_no, "I70: 記號格式不符");
        return false;
    }
    uint8_t kind = 0;
    if (field) kind = APP_IDENTITY_FIELD;
    else if (!strcmp(tokens[1], "boundary")) kind = APP_IDENTITY_BOUNDARY;
    else if (!strcmp(tokens[1], "placement")) kind = APP_IDENTITY_PLACEMENT;
    else if (!strcmp(tokens[1], "column")) kind = APP_IDENTITY_COLUMN;
    else if (!strcmp(tokens[1], "beam")) kind = APP_IDENTITY_BEAM;
    else if (!strcmp(tokens[1], "timber")) kind = APP_IDENTITY_TIMBER;
    else if (!strcmp(tokens[1], "parameter")) kind = APP_IDENTITY_PARAMETER;
    else {
        scene_error(path, line_no, "I70: 記號格式不符");
        return false;
    }
    uint32_t id = 0, field_id = 0;
    const char *mark_text = tokens[field ? 4 : 3];
    if (!parse_u32(tokens[2], &id) || !id || (field && !parse_u32(tokens[3], &field_id))) {
        scene_error(path, line_no, "I70: 記號格式不符");
        return false;
    }
    uint8_t epoch[16];
    uint64_t serial = 0;
    if (!identity_parse_mark(mark_text, epoch, &serial)) {
        scene_error(path, line_no, "I70: 記號格式不符");
        return false;
    }
    if (world->app.identity_mark_count == APP_IDENTITY_MARK_CAPACITY) {
        scene_error(path, line_no, "I33: 身分鍵超過 1024");
        return false;
    }
    for (uint32_t i = 0; i < world->app.identity_mark_count; ++i) {
        const AppIdentityMark *old = &world->app.identity_marks[i];
        if (old->kind == kind && old->id == id && old->field_id == field_id) {
            scene_error(path, line_no, "I70: 記號重複");
            return false;
        }
    }
    AppIdentityMark *mark = &world->app.identity_marks[world->app.identity_mark_count++];
    memset(mark, 0, sizeof *mark);
    mark->kind = kind;
    memcpy(mark->epoch, epoch, 16);
    mark->id = id;
    mark->field_id = field_id;
    mark->serial = serial;
    return true;
}
