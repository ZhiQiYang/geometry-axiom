/* web_bridge.c — current_geometry.c 的網頁介面橋接器。
 *
 * 幾何層整支用 unity build 含進來（內部函式全是 static，不 include 就碰不到）。
 * 對外協定：stdin 一行一個指令，stdout 一行回一個 JSON 物件。
 *
 *   default                      → 內建預設世界（reference_default_world）
 *   reset                        → 清空世界
 *   line <文字>                  → 套用一行場景指令（與 SCENE_COMMANDS 同一條路）
 *   loadfile <路徑>              → parse_scene_file（失敗還原世界；成功記入 undo）
 *   render                       → {"ok":true,"layout":{...},"ops":[...]}
 *   pick <view> <x> <y> <r>      → 命中描述 + hover 高亮 ops（r = 拾取半徑，視圖內 mm）
 *   drag <guide_idx> <view> <x> <y> → 拖曳參考線：反解 uv、reference_snap、組 move 走 feed_line
 *   grid-preview grid|subgrid ... → 在 World 副本上驗證並推導格線，不寫入場景或 undo
 *
 * ops 串流就是 DrawTarget 回呼的逐字序列化：begin/rect/poly/line/text/end。
 * 幾何本體在 current_geometry.c；本檔只做 stdin/JSON 橋。
 */
#define _CRT_SECURE_NO_WARNINGS
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

#define main geometry_cli_main
#include "../current_geometry.c"
#undef main

static World g_world;
static int g_input_line_no = 0;
static void json_engineering_sources(const World *);
static void json_engineering_capabilities(const World *);
static bool eng_definition_hash(const World *,char[65]);

/* ---------------- JSON 輸出小工具 ---------------- */

/*
 * JSON 字串輸出。這裡是 bridge 對外的最後一道:輸入若夾帶無效 UTF-8
 * (fuzz 會、複製貼上也會),或訊息被位元組截斷切到半個字,原樣吐出去
 * 整條 JSON 串流就壞了(serve.py 的 decode 直接炸)。無效序列逐位元組換成
 * U+FFFD——標出來、不吞掉;合法序列原樣通過(GEO-174)。
 */
static void js_string_body(const char *s)
{
    for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        switch (*p) {
        case '"':  fputs("\\\"", stdout); break;
        case '\\': fputs("\\\\", stdout); break;
        case '\n': fputs("\\n", stdout);  break;
        case '\r': fputs("\\r", stdout);  break;
        case '\t': fputs("\\t", stdout);  break;
        default:
            if (*p < 0x20) {
                printf("\\u%04x", *p);
            } else if (*p < 0x80) {
                putchar(*p);
            } else {
                int n = utf8_seq_len(p);
                if (n == 0) {
                    fputs("\\ufffd", stdout);       /* 無效序列:一個位元組換一個替代字元 */
                } else {
                    fwrite(p, 1, (size_t)n, stdout);
                    p += n - 1;                    /* for 的 ++p 補最後一步 */
                }
            }
        }
    }
}

static void js_string(const char *s)
{
    putchar('"');
    js_string_body(s);
    putchar('"');
}

/* ---------------- JSON 版 DrawTarget ---------------- */

typedef struct {
    int count;
} JsonOps;

static void jop_sep(JsonOps *j)
{
    if (j->count++ > 0) putchar(',');
}

static void jt_begin_view(void *ctx, Coord tx, Coord ty)
{
    JsonOps *j = ctx;
    jop_sep(j);
    printf("{\"op\":\"begin\",\"tx\":%" PRId64 ",\"ty\":%" PRId64 "}",
           (int64_t)tx, (int64_t)ty);
}

static void jt_end_view(void *ctx)
{
    JsonOps *j = ctx;
    jop_sep(j);
    fputs("{\"op\":\"end\"}", stdout);
}

static void jt_rect(void *ctx, ViewPoint2 mn, ViewPoint2 mx, DrawStyle s)
{
    JsonOps *j = ctx;
    jop_sep(j);
    printf("{\"op\":\"rect\",\"x0\":%" PRId64 ",\"y0\":%" PRId64
           ",\"x1\":%" PRId64 ",\"y1\":%" PRId64 ",\"s\":%d}",
           (int64_t)mn.x, (int64_t)mn.y, (int64_t)mx.x, (int64_t)mx.y, (int)s);
}

static void jt_polygon(void *ctx, const ViewPoint2 *q, size_t count, DrawStyle s)
{
    JsonOps *j = ctx;
    jop_sep(j);
    fputs("{\"op\":\"poly\",\"p\":[", stdout);
    for (size_t i = 0; i < count; ++i) {
        printf("%s%" PRId64 ",%" PRId64, i ? "," : "",
               (int64_t)q[i].x, (int64_t)q[i].y);
    }
    printf("],\"s\":%d}", (int)s);
}

static void jt_line(void *ctx, ViewPoint2 a, ViewPoint2 b, DrawStyle s)
{
    JsonOps *j = ctx;
    jop_sep(j);
    printf("{\"op\":\"line\",\"x0\":%" PRId64 ",\"y0\":%" PRId64
           ",\"x1\":%" PRId64 ",\"y1\":%" PRId64 ",\"s\":%d}",
           (int64_t)a.x, (int64_t)a.y, (int64_t)b.x, (int64_t)b.y, (int)s);
}

static void jt_text(void *ctx, ViewPoint2 at, DrawStyle s, const char *utf8, int rot)
{
    JsonOps *j = ctx;
    jop_sep(j);
    printf("{\"op\":\"text\",\"x\":%" PRId64 ",\"y\":%" PRId64
           ",\"s\":%d,\"rot\":%d,\"t\":",
           (int64_t)at.x, (int64_t)at.y, (int)s, rot);
    js_string(utf8);
    putchar('}');
}

static const DrawTarget JSON_TARGET = {
    NULL, jt_begin_view, jt_end_view, jt_rect, jt_polygon, jt_line, jt_text
};

/* ---------------- 世界操作 ---------------- */

/* 一行文字 → split_tokens → apply_scene_line。與 GDI 的 interactive_apply_line 同路。 */
static bool feed_line(const char *path, int line_no, const char *text, World *world)
{
    char line[SCENE_MAX_LINE];
    if (strlen(text) > sizeof line - 2) {
        scene_error(path, line_no, "指令超過 DSL 單行上限");
        if (g_hist_grouping) history_group_rollback(world);
        return false;
    }
    if (!utf8_is_valid(text)) {           /* 與 parse_scene_file 同一道閘門(GEO-174) */
        scene_error(path, line_no,
                    "這一行含無效的 UTF-8 位元組（場景 DSL 是 UTF-8 文字）");
        if (g_hist_grouping) history_group_rollback(world);
        return false;
    }
    snprintf(line, sizeof line, "%s", text);

    char *hash = strchr(line, '#');
    if (hash != NULL) *hash = '\0';

    char *tokens[SCENE_MAX_TOKENS];
    int count = split_tokens(line, tokens, SCENE_MAX_TOKENS);
    if (count < 0) {
        scene_error(path, line_no, "這一行的欄位太多");
        if (g_hist_grouping) history_group_rollback(world);
        return false;
    }
    if (count == 0) return true;   /* 空行／純註解：不算錯 */

    /* undo/redo 攔截 + 變更前記快照，都在共享核心裡。 */
    return apply_interactive_tokens(path, line_no, tokens, count, world);
}

/* 內建預設 = room_a.scene 的內容，走同一條解析路。 */
static bool world_default(World *world)
{
    bool ok=reference_default_world(world);
    if (ok) ++g_definition_revision;
    history_clear(); g_preview.ready=false;
    return ok;
}

/* ---------------- 指令處理 ---------------- */

static void cmd_render(void)
{
    Scene scene = scene_from_world(&g_world);
    SceneLayout layout;

    /* 空世界/純游離面世界：scene_compute_layout 會回最小空版面。 */
    if (!scene_compute_layout(&scene, &layout)) {
        fputs("{\"ok\":false,\"error\":\"場景沒有可畫的表面\"}\n", stdout);
        return;
    }

    printf("{\"ok\":true,\"layout\":{\"w\":%" PRId64 ",\"h\":%" PRId64 ",\"views\":[",
           (int64_t)layout.total_w, (int64_t)layout.total_h);
    for (int v = 0; v < VIEW_COUNT; ++v) {
        const ViewBounds *b = &layout.bounds[v];
        printf("%s{\"tx\":%" PRId64 ",\"ty\":%" PRId64
               ",\"bounds\":[%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 "]}",
               v ? "," : "",
               (int64_t)layout.tx[v], (int64_t)layout.ty[v],
               (int64_t)b->min_x, (int64_t)b->min_y,
               (int64_t)b->max_x, (int64_t)b->max_y);
    }
    fputs("]},\"ops\":[", stdout);

    JsonOps j = { 0 };
    DrawTarget t = JSON_TARGET;
    t.ctx = &j;
    scene_render(&t, &layout, &scene);

    fputs("]}\n", stdout);
}

static void cmd_pick(int v, Coord x, Coord y, Coord r)
{
    Scene scene = scene_from_world(&g_world);
    SceneLayout layout;
    bool has_layout =
        scene.placement_count > 0 && scene_compute_layout(&scene, &layout);

    ScenePick p = SCENE_PICK_NONE;
    if (has_layout && v >= 0 && v < VIEW_COUNT) {
        p = scene_pick_at(&scene, &VIEW_FRAMES[v], v, (ViewPoint2){ x, y }, r);
        p.view = v;
    }

    char desc[160];
    scene_describe_pick(&scene, &g_world, &p, desc, sizeof desc);

    printf("{\"ok\":true,\"none\":%s,\"desc\":",
           scene_pick_is_none(&p) ? "true" : "false");
    js_string(desc);
    printf(",\"guide\":%d,\"timber\":%d,\"face\":%d,"
           "\"column\":%d,\"beam\":%d,\"hover\":[",
           p.guide, p.timber, (int)p.face, p.column, p.beam);

    if (has_layout && !scene_pick_is_none(&p)) {
        JsonOps j = { 0 };
        DrawTarget t = JSON_TARGET;
        t.ctx = &j;
        scene_draw_pick(&t, &layout, &scene, &p);
    }
    fputs("]}\n", stdout);
}

#include "grid_system_bridge.inc"
#include "grid_binding_bridge.inc"
#include "reference_bridge.inc"

static void cmd_drag(int guide_idx, int v, Coord x, Coord y)
{
    if (guide_idx<0 || guide_idx>=(int)g_world.guide_count || v<0 || v>=VIEW_COUNT) {
        fputs("{\"ok\":false}\n",stdout); return;
    }
    GuideLine *g=&g_world.guides[guide_idx];
    if (g->source==GUIDE_DATUM) {
        fputs("{\"ok\":false,\"error\":\"R5: 這是共用基準參考線，請編輯共同基準或具名規格\"}\n",stdout); return;
    }
    const PlacementSurface *p=world_find_placement(&g_world,g->placement_id); SurfacePoint2 uv;
    if (!p || !view_unproject_on_surface(&VIEW_FRAMES[v],p,(ViewPoint2){x,y},&uv)) {
        fputs("{\"ok\":false}\n",stdout); return;
    }
    Coord at=g->direction==GUIDE_ALONG_U?uv.v:uv.u;
    char expr[REF_EXPR_MAX],command[REF_EXPR_MAX+64];
    if (!reference_snap(&g_world,g->placement_id,g->direction,g->id,at,80,expr)) {
        fputs("{\"ok\":false,\"error\":\"R5: 附近沒有合法引用\"}\n",stdout); return;
    }
    snprintf(command,sizeof command,"move %u %s",g->id,expr);
    uint32_t token=g_preview.token;
    bool ok=feed_line("drag",++g_input_line_no,command,&g_world);
    cmd_reference_result(ok,token);
}

static void cmd_line(const char *text)
{
    uint32_t token=g_preview.token;
    bool ok=feed_line("input",++g_input_line_no,text,&g_world);
    cmd_reference_result(ok,token);
}

static void cmd_loadfile(const char *path)
{
    /*
     * GEO-160：歷史群組進行中不得換掉整個世界。
     *
     * g_hist_grouping / g_hist_group_base 是行程層全域,不在 World 裡,所以
     * 下面那個 World 快照救不到它們。原本 loadfile 直接跨過去:群組還開著,
     * 而 base 停在**載入前**的世界,之後 history-end 會把那個舊世界推進 undo 疊——
     * 使用者按一次 undo,loadfile 與其後所有編輯一起消失。成功路徑也會踩到。
     *
     * 這裡跟 undo / redo 用同一條規則(見 current_geometry.c 的
     * 「歷史群組進行中,不能 undo」),三者都是整個世界被換掉的操作。
     * 只拒絕、不自動中止群組:不靜默丟掉做到一半的編輯;history-abort 是冪等的,
     * 恢復路徑一直都在。
     */
    if (g_hist_grouping) {
        fputs("{\"ok\":false,\"error\":"
              "\"歷史群組進行中,不能載入檔案（請先 history-end 或 history-abort）\"}\n",
              stdout);
        return;
    }

    /* 先記快照：失敗時世界不動，成功時載入本身可以 undo。 */
    World before = g_world;
    memset(&g_world, 0, sizeof g_world);
    if (parse_scene_file(path, &g_world)) {
        history_record(&before);
        ++g_definition_revision;
        char hash[65]; bool hashed=eng_definition_hash(&g_world,hash);
        printf("{\"ok\":true,\"revision\":%llu,",(unsigned long long)g_definition_revision);
        json_engineering_capabilities(&g_world);
        if(hashed)printf(",\"definition_sha256\":\"%s\"",hash);
        fputs("}\n",stdout);
    } else {
        g_world = before;
        fputs("{\"ok\":false,\"error\":", stdout);
        js_string(scene_last_error());
        fputs("}\n", stdout);
    }
}

/* ---- 畫布指令 ---- */

/* uv <view> <x> <y> <surface_id>：視圖 mm → 該承載面 uv（容差反解）。 */
static void cmd_uv(int v, Coord x, Coord y, uint32_t sid)
{
    const PlacementSurface *surface = world_find_placement(&g_world, sid);
    SurfacePoint2 uv;

    if (v < 0 || v >= VIEW_COUNT || surface == NULL ||
        !view_unproject_on_surface_near(
            &VIEW_FRAMES[v], surface, (ViewPoint2){ x, y }, &uv)) {
        fputs("{\"ok\":false}\n", stdout);
        return;
    }
    printf("{\"ok\":true,\"u\":%lld,\"v\":%lld}\n",
           (long long)uv.u, (long long)uv.v);
}

/* proj <view> <u> <v> <surface_id>：承載面 uv → 視圖 mm（編輯手柄用）。 */
static void cmd_proj(int v, Coord u, Coord vv, uint32_t sid)
{
    const PlacementSurface *surface = world_find_placement(&g_world, sid);

    if (v < 0 || v >= VIEW_COUNT || surface == NULL) {
        fputs("{\"ok\":false}\n", stdout);
        return;
    }
    Point3 p = surface_point_to_room(surface, u, vv, 0);
    ViewPoint2 q = view_project(&VIEW_FRAMES[v], p);
    printf("{\"ok\":true,\"x\":%lld,\"y\":%lld}\n",
           (long long)q.x, (long long)q.y);
}

/*
 * GEO-156：從最大 id + 1 起,找第一個沒被占用的 id。
 *
 * 單純的 max + 1 在 uint32 上界會回繞成 0。對 guide / grid 這種 id 0 合法的物件,
 * newid 就發出了一個**已經被占用**的 id;畫布拿去宣告是交易式重宣告,
 * 既有物件直接被覆寫。實測:場景同時有 `guide 0` 與 `guide 4294967295` 時,
 * newid 回 "guide":0。對 surface / timber / column(id 0 不合法)症狀則變成
 * 「新物件建不出來」。原本只有 datum 擋了這件事,其餘八種是裸 + 1。
 *
 * 候選 max+1, max+2, …, max+count+1 共 count + 1 個且兩兩相異(count < 2^32),
 * 而被占用的只有 count 個,所以迴圈必定找得到空位。
 *
 * GEO-159:skip_zero 給 boundary 用。boundary 0 建得起來,但
 * `placement N on boundary 0` 永遠被拒——D4 拿 boundary_id == 0 表示
 * 「不掛邊界面、自帶矩形」。畫布的 objEmitFace() 直接用這個欄位,
 * 回繞發出 0 的話使用者會拿到成功訊息和一個**永遠掛不上承載面的死面**。
 * 其餘八類的 id 0 實測可用,所以不一律跳過,避免無謂的行為變更。
 */
#define WORLD_NEXT_ID(out, array, count, skip_zero)                         \
    do {                                                                    \
        size_t n_ = (size_t)(count);                                        \
        uint32_t id_ = 0;                                                   \
        for (size_t i_ = 0; i_ < n_; ++i_)                                  \
            if ((array)[i_].id > id_) id_ = (array)[i_].id;                 \
        ++id_;                                                              \
        for (size_t attempt_ = 0; attempt_ <= n_; ++attempt_) {             \
            bool used_ = false;                                             \
            if ((skip_zero) && id_ == 0) id_ = 1;                           \
            for (size_t i_ = 0; i_ < n_; ++i_)                              \
                if ((array)[i_].id == id_) { used_ = true; break; }         \
            if (!used_) break;                                              \
            ++id_;                                                          \
        }                                                                   \
        (out) = id_;                                                        \
    } while (0)

/*
 * GEO-157：`surface N` 是「boundary N + placement N」合體一行,
 * 所以它要的 id 必須在**兩個** id 空間裡都是空的。
 *
 * 畫布原本自己用 Math.max(newid.boundary, newid.placement) 湊:那只在「沒有回繞」時
 * 才成立(兩者都大於各自類別的所有既有 id)。GEO-156 之後回繞會給出**小號碼**,
 * 湊出來的號碼可能正好是另一類已存在的物件——而 `surface` 對既有 id 是交易式重宣告,
 * 會**靜默覆寫**(實測:boundary 1 的輪廓被換掉,回應仍是 ok:true)。
 * 這個不變式屬於有資料的那一側,不該讓 JS 猜。
 *
 * 六面盒還要 6 個彼此相異的這種 id,所以 newid 接一個可選的數量。
 */
#define NEWID_MAX_SURFACES 16

static bool surface_id_taken(uint32_t id, const uint32_t *reserved, size_t reserved_count)
{
    for (size_t i = 0; i < g_world.boundary_count; ++i)
        if (g_world.boundaries[i].id == id) return true;
    for (size_t i = 0; i < g_world.placement_count; ++i)
        if (g_world.placements[i].id == id) return true;
    for (size_t i = 0; i < reserved_count; ++i)
        if (reserved[i] == id) return true;
    return false;
}

/* 取 n 個非零、boundary 與 placement 兩邊都沒占用、且彼此相異的 id。 */
static bool next_surface_ids(uint32_t *out, size_t n)
{
    uint32_t id = 0;

    for (size_t i = 0; i < g_world.boundary_count; ++i)
        if (g_world.boundaries[i].id > id) id = g_world.boundaries[i].id;
    for (size_t i = 0; i < g_world.placement_count; ++i)
        if (g_world.placements[i].id > id) id = g_world.placements[i].id;
    ++id;

    for (size_t k = 0; k < n; ++k) {
        size_t used = g_world.boundary_count + g_world.placement_count + k;
        bool found = false;

        /* 非零候選 used + 1 個且兩兩相異,被占用的至多 used 個 → 必定找得到。 */
        for (size_t attempt = 0; attempt <= used; ++attempt) {
            /* D4:boundary_id=0 表示自帶矩形;surface 必須引用同 id 的邊界面。
               每次查找都跳過 0,包含第一個候選及同批後續候選的回繞。 */
            if (id == 0) id = 1;
            if (!surface_id_taken(id, out, k)) { found = true; break; }
            ++id;
        }
        if (!found) return false;
        out[k] = id;
        ++id;
    }
    return true;
}

/* newid [n]：各類物件一個尚未被占用的 id，外加 n 個 surface 用的 id（預設 1）。 */
static void cmd_newid(size_t surface_count)
{
    uint32_t mb, mp, mg, mgr, mgs, mgb, mt, ms, mc, mbm, md, mparam, mar, mab;
    uint32_t surfaces[NEWID_MAX_SURFACES];

    if (surface_count < 1 || surface_count > NEWID_MAX_SURFACES) {
        fputs("{\"ok\":false,\"error\":\"newid 的數量必須是 1 到 16\"}\n", stdout);
        return;
    }
    if (!next_surface_ids(surfaces, surface_count)) {
        fputs("{\"ok\":false,\"error\":\"找不到足夠的空號\"}\n", stdout);
        return;
    }

    /* boundary 的 0 是 D4 的保留值;space 的 0 表示游離柱樑。其餘類別仍允許 0。 */
    WORLD_NEXT_ID(mb,  g_world.boundaries, g_world.boundary_count, true);
    WORLD_NEXT_ID(mp,  g_world.placements, g_world.placement_count, false);
    WORLD_NEXT_ID(mg,  g_world.guides,     g_world.guide_count,     false);
    WORLD_NEXT_ID(mgr, g_world.grids,      g_world.grid_count,      false);
    WORLD_NEXT_ID(mgs, g_world.grid_systems, g_world.grid_system_count, false);
    WORLD_NEXT_ID(mgb, g_world.grid_bindings, g_world.grid_binding_count, false);
    WORLD_NEXT_ID(mt,  g_world.timbers,    g_world.timber_count,    false);
    WORLD_NEXT_ID(ms,  g_world.spaces,     g_world.space_count,     true);
    WORLD_NEXT_ID(mc,  g_world.columns,    g_world.column_count,    false);
    WORLD_NEXT_ID(mbm, g_world.beams,      g_world.beam_count,      false);
    WORLD_NEXT_ID(md,  g_world.datums,     g_world.datum_count,     false);
    WORLD_NEXT_ID(mparam, g_world.parameters.cards, g_world.parameters.card_count, false);

    /* 0 means exhausted for these positive-ID namespaces only. */
    mar=g_world.assembly.rule_high_water==UINT32_MAX?0:g_world.assembly.rule_high_water+1;
    mab=g_world.assembly.binding_high_water==UINT32_MAX?0:g_world.assembly.binding_high_water+1;
    /* 既有的純量欄位一個都沒動:舊的呼叫端(以及 canvas_test.js)照常可用。 */
    printf("{\"ok\":true,\"boundary\":%u,\"placement\":%u,\"guide\":%u,"
           "\"grid\":%u,\"gridSystem\":%u,\"gridBinding\":%u,\"timber\":%u,\"space\":%u,"
           "\"column\":%u,\"beam\":%u,\"datum\":%u,\"parameter\":%u,\"assemblyRule\":%u,\"assemblyBinding\":%u,\"surfaces\":[",
           mb, mp, mg, mgr, mgs, mgb, mt, ms, mc, mbm, md, mparam, mar, mab);
    for (size_t i = 0; i < surface_count; ++i) {
        if (i) putchar(',');
        printf("%u", surfaces[i]);
    }
    fputs("],\"grids\":[",stdout);
    uint32_t candidate_grid=0;
    for(size_t i=0;i<surface_count;++i){
        while(world_find_grid(&g_world,candidate_grid)) ++candidate_grid;
        printf("%s%u",i?",":"",candidate_grid++);
    }
    fputs("]}\n", stdout);
}

/* surfaces：列出承載面（畫布的「工作面」選擇器）。 */
static void cmd_surfaces(void)
{
    fputs("{\"ok\":true,\"surfaces\":[", stdout);
    for (size_t i = 0; i < g_world.placement_count; ++i) {
        const PlacementSurface *p = &g_world.placements[i];
        if (i) putchar(',');
        printf("{\"id\":%u,\"boundary\":%u,"
               "\"origin\":[%lld,%lld,%lld],"
               "\"u\":[%lld,%lld,%lld],\"v\":[%lld,%lld,%lld]}",
               (unsigned)p->id, (unsigned)p->boundary_id,
               (long long)p->frame.origin.x, (long long)p->frame.origin.y,
               (long long)p->frame.origin.z,
               (long long)p->frame.axis_u.x, (long long)p->frame.axis_u.y,
               (long long)p->frame.axis_u.z,
               (long long)p->frame.axis_v.x, (long long)p->frame.axis_v.y,
               (long long)p->frame.axis_v.z);
    }
    fputs("]}\n", stdout);
}

/* boundary <id>：回傳環頂點與 fixity（編輯手柄資料）。 */
static void cmd_boundary(uint32_t id)
{
    const SpaceBoundarySurface *b = world_find_boundary(&g_world, id);

    if (b == NULL) {
        fputs("{\"ok\":false,\"error\":\"邊界面不存在\"}\n", stdout);
        return;
    }

    json_boundary_definition(&g_world,b,true); putchar('\n');
}

/* bhit <boundary_id> <u> <v> <r>：邊界頂點/邊命中（編輯拖曳用）。 */
static void cmd_bhit(uint32_t id, Coord u, Coord v, Coord r)
{
    const SpaceBoundarySurface *b = world_find_boundary(&g_world, id);
    BoundaryHit hit;

    if (!boundary_pick_point(b, (SurfacePoint2){ u, v }, r, &hit)) {
        fputs("{\"ok\":false}\n", stdout);
        return;
    }
    printf("{\"ok\":true,\"kind\":\"%s\",\"loop\":%d,\"index\":%d}\n",
           hit.kind == BOUNDARY_HIT_VERTEX ? "vertex" : "edge",
           hit.loop, hit.index);
}

static const char *obstacle_cls_name(ObstacleClass cls)
{
    switch (cls) {
    case OBSTACLE_HOLE:      return "hole";
    case OBSTACLE_NOTCH:     return "notch";
    case OBSTACLE_CORNER:    return "corner";
    case OBSTACLE_SPLIT:     return "split";
    case OBSTACLE_STRIP:     return "strip";
    case OBSTACLE_TOP_NOTCH: return "top_notch";
    case OBSTACLE_TOP_DROP:  return "top_drop";
    }
    return "?";
}

/* obstacles <boundary_id>：面上柱樑的 uv 鬼影 + 接觸分類（R7/R9）。 */
static void cmd_obstacles(uint32_t id)
{
    const SpaceBoundarySurface *b = world_find_boundary(&g_world, id);
    FaceObstacle items[64];

    if (b == NULL) {
        fputs("{\"ok\":false,\"error\":\"邊界面不存在\"}\n", stdout);
        return;
    }
    size_t n = world_face_obstacles(&g_world, b, items, 64);
    if (n == SIZE_MAX) {
        fputs("{\"ok\":false,\"error\":\"面尚未放置，無法推導障礙物\"}\n",
              stdout);
        return;
    }

    int n_axis = 2;
    for (size_t p = 0; p < g_world.placement_count; ++p) {
        if (g_world.placements[p].boundary_id == b->id) {
            n_axis = axis_index(g_world.placements[p].frame.normal);
            break;
        }
    }

    printf("{\"ok\":true,\"face\":%u,\"kind\":\"%s\",\"items\":[",
           (unsigned)b->id, n_axis == 2 ? "plan" : "elevation");
    for (size_t i = 0; i < n; ++i) {
        const FaceObstacle *it = &items[i];
        if (i) putchar(',');
        printf("{\"id\":%u,\"type\":\"%s\",\"cls\":\"%s\","
               "\"rect\":[%lld,%lld,%lld,%lld]}",
               (unsigned)it->id,
               it->is_beam ? "beam" : "column",
               obstacle_cls_name(it->cls),
               (long long)it->u_lo, (long long)it->v_lo,
               (long long)it->u_hi, (long long)it->v_hi);
    }
    fputs("]}\n", stdout);
}

/* 查某物件的畫布座標；沒設過回 NULL。 */
static const CanvasPos *find_cpos(int kind, uint32_t id)
{
    for (size_t i = 0; i < g_world.canvas_pos_count; ++i) {
        const CanvasPos *p = &g_world.canvas_pos[i];
        if (p->kind == kind && p->id == id) {
            return p;
        }
    }
    return NULL;
}

static void cpos_json(int kind, uint32_t id)
{
    const CanvasPos *p = find_cpos(kind, id);
    if (p == NULL) {
        fputs("\"cx\":0,\"cy\":0,\"hasPos\":false", stdout);
    } else {
        printf("\"cx\":%lld,\"cy\":%lld,\"hasPos\":true",
               (long long)p->x, (long long)p->y);
    }
}

/* objects：列出畫布層所有物件（面卡 + 空間卡）與畫布座標。 */
#include "parameter_bridge.inc"
static void cmd_objects(void)
{
    fputs("{\"ok\":true,\"faces\":[", stdout);

    bool first = true;

    for (size_t i = 0; i < g_world.boundary_count; ++i) {
        const SpaceBoundarySurface *b = &g_world.boundaries[i];
        Coord lo_u = 0, lo_v = 0, hi_u = 0, hi_v = 0;

        if (b->outline.count > 0) {
            lo_u = hi_u = b->outline.v[0].u;
            lo_v = hi_v = b->outline.v[0].v;
            for (size_t k = 1; k < b->outline.count; ++k) {
                if (b->outline.v[k].u < lo_u) lo_u = b->outline.v[k].u;
                if (b->outline.v[k].u > hi_u) hi_u = b->outline.v[k].u;
                if (b->outline.v[k].v < lo_v) lo_v = b->outline.v[k].v;
                if (b->outline.v[k].v > hi_v) hi_v = b->outline.v[k].v;
            }
        }

        bool placed = false;
        for (size_t p = 0; p < g_world.placement_count; ++p) {
            if (g_world.placements[p].boundary_id == b->id) {
                placed = true;
                break;
            }
        }

        if (!first) putchar(',');
        first = false;
        printf("{\"kind\":\"boundary\",\"boundaryKind\":\"%s\",\"id\":%u,\"placed\":%s,"
               "\"bbox\":[%lld,%lld,%lld,%lld],",
               b->kind==BOUNDARY_ROOM_PLAN?"room_plan":b->kind==BOUNDARY_WALL_ELEVATION?"wall_elevation":"unspecified",
               (unsigned)b->id, placed ? "true" : "false",
               (long long)lo_u, (long long)lo_v,
               (long long)hi_u, (long long)hi_v);
        cpos_json(CANVAS_POS_BOUNDARY, b->id);
        putchar('}');
    }

    /* 自帶矩形（無邊界面）的承載面也是一張面卡。 */
    for (size_t i = 0; i < g_world.placement_count; ++i) {
        const PlacementSurface *p = &g_world.placements[i];

        if (p->boundary_id != 0) {
            continue;
        }

        if (!first) putchar(',');
        first = false;
        printf("{\"kind\":\"placement\",\"id\":%u,\"placed\":true,"
               "\"bbox\":[%lld,%lld,%lld,%lld],",
               (unsigned)p->id,
               (long long)p->rect.min_u, (long long)p->rect.min_v,
               (long long)p->rect.max_u, (long long)p->rect.max_v);
        cpos_json(CANVAS_POS_PLACEMENT, p->id);
        putchar('}');
    }

    fputs("],\"spaces\":[", stdout);

    for (size_t i = 0; i < g_world.space_count; ++i) {
        const Space *s = &g_world.spaces[i];

        if (i) putchar(',');
        printf("{\"id\":%u,\"members\":[", (unsigned)s->id);
        for (size_t k = 0; k < s->boundary_count; ++k) {
            if (k) putchar(',');
            printf("%u", (unsigned)s->boundaries[k]);
        }
        printf("],\"closed\":%s,", s->closed ? "true" : "false");
        cpos_json(CANVAS_POS_SPACE, s->id);
        putchar('}');
    }

    fputs("],\"columns\":[", stdout);

    for (size_t i = 0; i < g_world.column_count; ++i) {
        const RcColumn *c = &g_world.columns[i];

        if (i) putchar(',');
        printf("{\"kind\":\"column\",\"id\":%u,\"space\":%u,"
               "\"box\":[%lld,%lld,%lld,%lld,%lld,%lld],",
               (unsigned)c->id, (unsigned)c->space_id,
               (long long)c->x_lo, (long long)c->y_lo, (long long)c->z_lo,
               (long long)c->x_hi, (long long)c->y_hi, (long long)c->z_hi);
        cpos_json(CANVAS_POS_COLUMN, c->id);
        putchar('}');
    }

    fputs("],\"beams\":[", stdout);

    for (size_t i = 0; i < g_world.beam_count; ++i) {
        const RcBeam *b = &g_world.beams[i];

        if (i) putchar(',');
        printf("{\"kind\":\"beam\",\"id\":%u,\"space\":%u,\"axis\":\"%c\","
               "\"box\":[%lld,%lld,%lld,%lld,%lld,%lld],",
               (unsigned)b->id, (unsigned)b->space_id,
               b->axis == 0 ? 'x' : 'y',
               (long long)b->x_lo, (long long)b->y_lo, (long long)b->z_lo,
               (long long)b->x_hi, (long long)b->y_hi, (long long)b->z_hi);
        cpos_json(CANVAS_POS_BEAM, b->id);
        putchar('}');
    }

    fputs("],\"gridSystems\":[",stdout);
    for (size_t i=0;i<g_world.grid_system_count;++i) {
        if (i) putchar(',');
        json_grid_system(&g_world,&g_world.grid_systems[i]);
    }

    fputs("],\"parameters\":[",stdout);
    for(size_t i=0;i<g_world.parameters.card_count;++i){
        if(i)putchar(',');const ParameterSet *c=&g_world.parameters.cards[i];
        fputs("{\"kind\":\"parameter\",\"card\":",stdout);parameter_json_card(&g_world,c,stdout,true);
        printf(",\"id\":%u,\"name\":",c->id);js_string(c->name);putchar(',');cpos_json(CANVAS_POS_PARAMETER,c->id);putchar('}');
    }
    fputs("],\"assemblyRules\":[",stdout);bool first_rule=true;
    for(size_t i=0;i<g_world.assembly.rule_count;++i){const AsmRuleVersion *r=&g_world.assembly.rules[i];if(assembly_rule(&g_world,r->id,0)!=r)continue;
        printf("%s{\"kind\":\"assembly-rule\",\"id\":%u,\"version\":%u,\"name\":",first_rule?"":",",r->id,r->version);first_rule=false;js_string(r->name);putchar(',');cpos_json(CANVAS_POS_ASSEMBLY_RULE,r->id);putchar('}');}
    fputs("],\"assemblyBindings\":[",stdout);
    for(size_t i=0;i<g_world.assembly.binding_count;++i){const AsmBinding *b=&g_world.assembly.bindings[i];printf("%s{\"kind\":\"assembly-binding\",\"id\":%u,\"ruleId\":%u,\"version\":%u,\"complete\":%s,\"name\":",i?",":"",b->id,b->rule_id,b->rule_version,b->complete?"true":"false");js_string(b->name);putchar(',');cpos_json(CANVAS_POS_ASSEMBLY_BINDING,b->id);putchar('}');}
    fputs("],\"parameterUses\":",stdout);json_parameter_uses(&g_world);
    fputs(",\"gridBindings\":[",stdout);
    for (size_t i=0;i<g_world.grid_binding_count;++i) {
        if (i) putchar(',');
        json_grid_binding(&g_world,&g_world.grid_bindings[i],false);
    }

    /*
     * R18 角色衍生屬性：onBoundary / coversEdge / boundaryEdge 明確成欄位，
     * 不藏在標籤字串裡（公理層 R18 尾句）。角色與裁切優先級（D15）一併出。
     */
    fputs("],\"timbers\":[", stdout);

    first = true;
    for (size_t i = 0; i < g_world.timber_count; ++i) {
        const Timber *t = &g_world.timbers[i];
        const TimberAnchor *a = &g_world.anchors[i];
        const PlacementSurface *p;
        const SpaceBoundarySurface *b;
        SurfaceRegion2 f;
        bool along_v, on_boundary = false, covers_edge = false;
        int boundary_edge = -1;

        if (!t->placed) {
            continue;
        }
        p = world_find_placement(&g_world, a->placement_id);
        if (p == NULL || !timber_a0_footprint_uv(p, t, a, &f)) {
            continue;
        }
        SpaceBoundarySurface effective;
        b=placement_effective_boundary(p,world_placement_boundary(&g_world,p),&effective);

        along_v = a->length_direction == SURFACE_DIRECTION_POS_V ||
                  a->length_direction == SURFACE_DIRECTION_NEG_V;
        timber_role_props(
            b, along_v,
            along_v ? f.min_v : f.min_u,
            along_v ? f.max_v : f.max_u,
            along_v ? f.min_u : f.min_v,
            along_v ? f.max_u : f.max_v,
            &on_boundary, &covers_edge, &boundary_edge);

        if (!first) {
            putchar(',');
        }
        first = false;
        printf("{\"id\":%u,\"surface\":%u,\"role\":\"%s\","
               "\"priority\":%d,\"onBoundary\":%s,\"coversEdge\":%s,"
               "\"boundaryEdge\":%d}",
               (unsigned)t->id, (unsigned)a->placement_id,
               timber_role_name(t->role), (int)t->cut_priority,
               on_boundary ? "true" : "false",
               covers_edge ? "true" : "false",
               boundary_edge);
    }

    fputs("]}\n", stdout);
}

/* dump：World → 可重放 DSL 文本（存檔/匯出）。 */
static void cmd_dump(void)
{
    FILE *tmp = tmpfile();

    if (tmp == NULL) {
        fputs("{\"ok\":false,\"error\":\"暫存檔失敗\"}\n", stdout);
        return;
    }
    world_dump_dsl(&g_world, tmp);
    fflush(tmp);
    rewind(tmp);

    fputs("{\"ok\":true,\"text\":", stdout);
    char buf[2048];
    /* JSON 字串逐段輸出，先寫開頭引號。 */
    putchar('"');
    while (fgets(buf, sizeof buf, tmp) != NULL) {
        /* 去掉 CR(文字模式的痕跡),其餘交給 js_string_body:
         * 跟 error / command 欄同一道 UTF-8 檢查,防線不留單點(GEO-174)。 */
        char *w = buf;
        for (const char *r = buf; *r; ++r) {
            if (*r != '\r') *w++ = *r;
        }
        *w = '\0';
        js_string_body(buf);
    }
    fputs("\",",stdout);json_engineering_capabilities(&g_world);
    printf(",\"revision\":%llu",(unsigned long long)g_definition_revision);
    char hash[65];if(eng_definition_hash(&g_world,hash))printf(",\"definition_sha256\":\"%s\"",hash);
    fputs("}\n", stdout);
    fclose(tmp);
}

#include "engineering_bridge.inc"
#include "assembly_bridge.inc"

/* 視圖點已包含 frame 原點與構件尺寸；不能套用局部定義的單項上限。 */
static bool view_coord_in_range(Coord value)
{
    return value >= -4 * COORD_LIMIT && value <= 4 * COORD_LIMIT;
}

int main(void)
{
#ifdef _WIN32
    /* 只有 Windows 需要關掉 CRLF 轉換;POSIX 的 stdio 本來就是位元組流。 */
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stdin), _O_BINARY);
#endif

    world_default(&g_world);

    char line[4096];
    while (fgets(line, sizeof line, stdin) != NULL) {
        size_t n = strlen(line);
        /* 超長行：fgets 讀滿緩衝卻沒吃到換行 → 整行丟棄，
         * 殘段吞到換行/EOF,恰好回一行錯誤 JSON(不拆成兩次指令)。 */
        if (n == sizeof line - 1 && line[n - 1] != '\n') {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) { }
            fputs("{\"ok\":false,\"error\":\"指令超過單行上限\"}\n", stdout);
            fflush(stdout);
            continue;
        }
        while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r')) line[--n] = '\0';
        if (n == 0 || strspn(line, " \t") == n) {
            fputs("{\"ok\":false,\"error\":\"橋接指令不得為空\"}\n", stdout);
            fflush(stdout);
            continue;
        }

        char *arg = strchr(line, ' ');
        if (arg != NULL) *arg++ = '\0';

        if (strcmp(line, "render") == 0) {
            cmd_render();
        } else if (strcmp(line, "default") == 0) {
            fputs(world_default(&g_world)
                      ? "{\"ok\":true}\n"
                      : "{\"ok\":false,\"error\":\"內建場景失敗\"}\n",
                  stdout);
        } else if (strcmp(line, "reset") == 0) {
            memset(&g_world, 0, sizeof g_world);
            g_world.allocation_namespace=++g_world_namespace_counter;
            history_clear();
            ++g_definition_revision;
            fputs("{\"ok\":true}\n", stdout);
        } else if (strcmp(line, "line") == 0 && arg != NULL) {
            cmd_line(arg);
        } else if (strcmp(line,"assembly-read")==0 && !arg) {
            cmd_assembly_read();
        } else if (strcmp(line,"assembly-newid")==0 && arg) {
            cmd_assembly_newid(arg);
        } else if (strcmp(line,"assembly-preview")==0 && arg) {
            cmd_assembly_preview(arg);
        } else if (strcmp(line,"assembly-confirm")==0) {
            cmd_assembly_confirm(arg);
        } else if (strcmp(line,"assembly-cancel")==0) {
            cmd_assembly_cancel(arg);
        } else if (strcmp(line,"engineering-read")==0 && !arg) {
            cmd_engineering_read();
        } else if (strcmp(line,"engineering-preview")==0 && arg) {
            cmd_engineering_preview(arg);
        } else if (strcmp(line,"engineering-confirm")==0) {
            cmd_engineering_confirm(arg);
        } else if (strcmp(line,"engineering-cancel")==0) {
            cmd_engineering_cancel(arg);
        } else if (strcmp(line,"engineering-validate")==0 && arg) {
            cmd_engineering_validate(arg);
        } else if (strcmp(line, "grid-preview") == 0 && arg != NULL) {
            cmd_grid_preview(arg);
        } else if (strcmp(line, "grid-query") == 0) {
            cmd_grid_query(arg);
        } else if (strcmp(line, "grid-trial-query") == 0) {
            cmd_grid_trial_query(arg);
        } else if (strcmp(line, "loadfile") == 0 && arg != NULL) {
            cmd_loadfile(arg);
        } else if (strcmp(line, "pick") == 0 && arg != NULL) {
            int v; long long x, y, r;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &x, &y, &r) == 4 &&
                view_coord_in_range(x) && view_coord_in_range(y) && coord_in_range(r) && r >= 0) {
                cmd_pick(v, (Coord)x, (Coord)y, (Coord)r);
            } else {
                fputs("{\"ok\":false,\"error\":\"pick 用法：pick v x y r\"}\n", stdout);
            }
        } else if (strcmp(line, "drag") == 0 && arg != NULL) {
            int gi, v; long long x, y;
            if (sscanf(arg, "%d %d %lld %lld", &gi, &v, &x, &y) == 4 &&
                view_coord_in_range(x) && view_coord_in_range(y)) {
                cmd_drag(gi, v, (Coord)x, (Coord)y);
            } else {
                fputs("{\"ok\":false,\"error\":\"drag 用法：drag idx v x y\"}\n", stdout);
            }
        } else if (strcmp(line, "uv") == 0 && arg != NULL) {
            int v; long long x, y, sid;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &x, &y, &sid) == 4 &&
                view_coord_in_range(x) && view_coord_in_range(y)) {
                cmd_uv(v, (Coord)x, (Coord)y, (uint32_t)sid);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "proj") == 0 && arg != NULL) {
            int v; long long u, vv, sid;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &u, &vv, &sid) == 4 &&
                coord_in_range(u) && coord_in_range(vv)) {
                cmd_proj(v, (Coord)u, (Coord)vv, (uint32_t)sid);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "bhit") == 0 && arg != NULL) {
            long long bid, u, v, r;
            if (sscanf(arg, "%lld %lld %lld %lld", &bid, &u, &v, &r) == 4 &&
                coord_in_range(u) && coord_in_range(v) && coord_in_range(r) && r >= 0) {
                cmd_bhit((uint32_t)bid, (Coord)u, (Coord)v, (Coord)r);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "boundary") == 0 && arg != NULL) {
            cmd_boundary((uint32_t)strtoul(arg, NULL, 10));
        } else if (strcmp(line, "obstacles") == 0 && arg != NULL) {
            cmd_obstacles((uint32_t)strtoul(arg, NULL, 10));
        } else if (strcmp(line, "newid") == 0) {
            /* 沒帶參數 = 1 個（舊行為）。解析不乾淨一律交給 cmd_newid 擋掉。 */
            unsigned long count = 1;
            if (arg != NULL) {
                char *end = NULL;
                count = strtoul(arg, &end, 10);
                if (end == arg || *end != '\0') count = 0;
            }
            cmd_newid((size_t)count);
        } else if (strcmp(line, "surfaces") == 0) {
            cmd_surfaces();
        } else if (strcmp(line, "references") == 0) {
            cmd_references();
        } else if (strcmp(line, "snap") == 0 && arg != NULL) {
            cmd_snap_reference(arg);
        } else if (strcmp(line, "objects") == 0) {
            cmd_objects();
        } else if (strcmp(line, "dump") == 0) {
            cmd_dump();
        } else {
            fputs("{\"ok\":false,\"error\":\"不認得的橋接指令\"}\n", stdout);
        }
        fflush(stdout);
    }
    return 0;
}
