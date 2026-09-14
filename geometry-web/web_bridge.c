/* web_bridge.c — current_geometry.c 的網頁介面橋接器。
 *
 * 幾何層整支用 unity build 含進來（內部函式全是 static，不 include 就碰不到）。
 * 對外協定：stdin 一行一個指令，stdout 一行回一個 JSON 物件。
 *
 *   default                      → 內建房間 A（等價 room_a.scene）
 *   reset                        → 清空世界
 *   line <文字>                  → 套用一行場景指令（surface/edge/guide/timber/place/move/room/reset）
 *   loadfile <路徑>              → reset 後 parse_scene_file（伺服器端路徑）
 *   render                       → {"ok":true,"layout":{...},"ops":[...]}
 *   pick <view> <x> <y> <r>      → 命中描述 + hover 高亮 ops（r = 拾取半徑，視圖內 mm）
 *   drag <guide_idx> <view> <x> <y> → 拖曳參考線：反解 uv、clamp、guide_line_move
 *
 * ops 串流就是 DrawTarget 回呼的逐字序列化：begin/rect/poly/line/text/end。
 * 網頁端是唯一新增東西；C 端一行都沒改。
 */
#define _CRT_SECURE_NO_WARNINGS
#include <fcntl.h>
#include <io.h>

#define main geometry_cli_main
#include "../current_geometry.c"
#undef main

static World g_world;
static int g_input_line_no = 0;

/* ---------------- JSON 輸出小工具 ---------------- */

static void js_string(const char *s)
{
    putchar('"');
    for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        switch (*p) {
        case '"':  fputs("\\\"", stdout); break;
        case '\\': fputs("\\\\", stdout); break;
        case '\n': fputs("\\n", stdout);  break;
        case '\r': fputs("\\r", stdout);  break;
        case '\t': fputs("\\t", stdout);  break;
        default:
            if (*p < 0x20) printf("\\u%04x", *p);
            else           putchar(*p);
        }
    }
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
    snprintf(line, sizeof line, "%s", text);

    char *hash = strchr(line, '#');
    if (hash != NULL) *hash = '\0';

    char *tokens[SCENE_MAX_TOKENS];
    int count = split_tokens(line, tokens, SCENE_MAX_TOKENS);
    if (count <= 0) return true;   /* 空行／純註解：不算錯 */

    /* undo/redo 攔截 + 變更前記快照，都在共享核心裡。 */
    return apply_interactive_tokens(path, line_no, tokens, count, world);
}

/* 內建預設 = room_a.scene 的內容，走同一條解析路。 */
static const char *DEFAULT_SCENE[] = {
    "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
    "guide 1 1 u 300",
    "guide 2 1 v 500",
    "timber 1 1800 27 33",
    "place 1 on 1 at-guides 1 2 +u +n",
};

static bool world_default(World *world)
{
    memset(world, 0, sizeof *world);
    for (size_t i = 0; i < sizeof(DEFAULT_SCENE) / sizeof(DEFAULT_SCENE[0]); ++i) {
        if (!feed_line("<內建>", (int)i + 1, DEFAULT_SCENE[i], world)) return false;
    }
    history_clear();   /* 啟動載入不是使用者操作，不該被 undo */
    return true;
}

/* 命中物 → 一行描述；與 gdi_describe_pick 相同邏輯（那支在 _WIN32 裡碰不到）。 */
static void describe_pick(const Scene *scene, const World *world,
                          const ScenePick *p, char *buf, size_t cap)
{
    buf[0] = '\0';
    if (p == NULL || scene_pick_is_none(p)) return;

    if (p->column >= 0 && p->column < (int)scene->column_count) {
        snprintf(buf, cap, "柱%" PRIu32,
                 scene->columns[p->column].id);
        return;
    }
    if (p->beam >= 0 && p->beam < (int)scene->beam_count) {
        snprintf(buf, cap, "樑%" PRIu32,
                 scene->beams[p->beam].id);
        return;
    }
    if (p->timber >= 0 && p->timber < (int)scene->timber_count) {
        snprintf(buf, cap, "角材%" PRIu32 " %s",
                 scene->timbers[p->timber].id, timber_face_name(p->face));
        return;
    }
    if (p->guide >= 0 && p->guide < (int)world->guide_count) {
        const GuideLine *gd = &world->guides[p->guide];
        snprintf(buf, cap, "參考線%" PRIu32 " 沿%s offset=%" PRId64,
                 gd->id, gd->direction == GUIDE_ALONG_U ? "U" : "V",
                 (int64_t)gd->offset);
    }
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
    describe_pick(&scene, &g_world, &p, desc, sizeof desc);

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

static void cmd_drag(int guide_idx, int v, Coord x, Coord y)
{
    if (guide_idx < 0 || guide_idx >= (int)g_world.guide_count ||
        v < 0 || v >= VIEW_COUNT) {
        fputs("{\"ok\":false}\n", stdout);
        return;
    }

    GuideLine *gd = &g_world.guides[guide_idx];
    const PlacementSurface *surface =
        world_find_placement(&g_world, gd->placement_id);
    const SpaceBoundarySurface *boundary =
        surface ? world_placement_boundary(&g_world, surface) : NULL;
    SurfacePoint2 uv;
    SurfaceRegion2 bounds;

    if (surface == NULL ||
        !placement_local_bounds(surface, boundary, &bounds) ||
        !view_unproject_on_surface(&VIEW_FRAMES[v], surface,
                                   (ViewPoint2){ x, y }, &uv)) {
        fputs("{\"ok\":false}\n", stdout);
        return;
    }

    /* 與 GDI 拖曳同一段：反解 → clamp → move（構造上不可能非法）。 */
    Coord off = gd->direction == GUIDE_ALONG_U ? uv.v : uv.u;
    Coord lo = gd->direction == GUIDE_ALONG_U ? bounds.min_v : bounds.min_u;
    Coord hi = gd->direction == GUIDE_ALONG_U ? bounds.max_v : bounds.max_u;
    if (off < lo) off = lo;
    if (off > hi) off = hi;

    guide_line_move(surface, boundary, gd, off);
    printf("{\"ok\":true,\"offset\":%" PRId64 "}\n", (int64_t)off);
}

static void cmd_line(const char *text)
{
    if (feed_line("<輸入>", ++g_input_line_no, text, &g_world)) {
        fputs("{\"ok\":true}\n", stdout);
    } else {
        fputs("{\"ok\":false,\"error\":", stdout);
        js_string(scene_last_error());
        fputs("}\n", stdout);
    }
}

static void cmd_loadfile(const char *path)
{
    /* 先記快照：失敗時世界不動，成功時載入本身可以 undo。 */
    World before = g_world;
    memset(&g_world, 0, sizeof g_world);
    if (parse_scene_file(path, &g_world)) {
        history_record(&before);
        fputs("{\"ok\":true}\n", stdout);
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

/* newid：各類物件目前最大 id + 1（畫布產生新物件用）。 */
static void cmd_newid(void)
{
    uint32_t mb = 0, mp = 0, mg = 0, mgr = 0, mt = 0, ms = 0;
    uint32_t mc = 0, mbm = 0;

    for (size_t i = 0; i < g_world.boundary_count; ++i)
        if (g_world.boundaries[i].id > mb) mb = g_world.boundaries[i].id;
    for (size_t i = 0; i < g_world.placement_count; ++i)
        if (g_world.placements[i].id > mp) mp = g_world.placements[i].id;
    for (size_t i = 0; i < g_world.guide_count; ++i)
        if (g_world.guides[i].id > mg) mg = g_world.guides[i].id;
    for (size_t i = 0; i < g_world.grid_count; ++i)
        if (g_world.grids[i].id > mgr) mgr = g_world.grids[i].id;
    for (size_t i = 0; i < g_world.timber_count; ++i)
        if (g_world.timbers[i].id > mt) mt = g_world.timbers[i].id;
    for (size_t i = 0; i < g_world.space_count; ++i)
        if (g_world.spaces[i].id > ms) ms = g_world.spaces[i].id;
    for (size_t i = 0; i < g_world.column_count; ++i)
        if (g_world.columns[i].id > mc) mc = g_world.columns[i].id;
    for (size_t i = 0; i < g_world.beam_count; ++i)
        if (g_world.beams[i].id > mbm) mbm = g_world.beams[i].id;

    printf("{\"ok\":true,\"boundary\":%u,\"placement\":%u,\"guide\":%u,"
           "\"grid\":%u,\"timber\":%u,\"space\":%u,"
           "\"column\":%u,\"beam\":%u}\n",
           mb + 1, mp + 1, mg + 1, mgr + 1, mt + 1, ms + 1, mc + 1, mbm + 1);
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

    fputs("{\"ok\":true,\"loops\":[", stdout);
    for (int li = -1; li < (int)b->hole_count; ++li) {
        const PolygonLoop2 *loop = li < 0 ? &b->outline : &b->holes[li];
        if (li >= 0) putchar(',');
        fputs("{\"verts\":[", stdout);
        for (size_t i = 0; i < loop->count; ++i) {
            if (i) putchar(',');
            printf("[%lld,%lld]", (long long)loop->v[i].u,
                   (long long)loop->v[i].v);
        }
        fputs("],\"fixity\":[", stdout);
        for (size_t i = 0; i < loop->count; ++i) {
            if (i) putchar(',');
            putchar(loop->fixity[i] == EDGE_FREE ? '0' : '1');
        }
        fputs("]}", stdout);
    }
    fputs("]}\n", stdout);
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
        printf("{\"kind\":\"boundary\",\"id\":%u,\"placed\":%s,"
               "\"bbox\":[%lld,%lld,%lld,%lld],",
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
        for (const char *p = buf; *p; ++p) {
            switch (*p) {
            case '"':  fputs("\\\"", stdout); break;
            case '\\': fputs("\\\\", stdout); break;
            case '\n': fputs("\\n", stdout);  break;
            case '\r': break;
            default:   putchar(*p);
            }
        }
    }
    fputs("\"}\n", stdout);
    fclose(tmp);
}

int main(void)
{
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stdin), _O_BINARY);

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
        if (n == 0) continue;

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
            fputs("{\"ok\":true}\n", stdout);
        } else if (strcmp(line, "line") == 0 && arg != NULL) {
            cmd_line(arg);
        } else if (strcmp(line, "loadfile") == 0 && arg != NULL) {
            cmd_loadfile(arg);
        } else if (strcmp(line, "pick") == 0 && arg != NULL) {
            int v; long long x, y, r;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &x, &y, &r) == 4) {
                cmd_pick(v, (Coord)x, (Coord)y, (Coord)r);
            } else {
                fputs("{\"ok\":false,\"error\":\"pick 用法：pick v x y r\"}\n", stdout);
            }
        } else if (strcmp(line, "drag") == 0 && arg != NULL) {
            int gi, v; long long x, y;
            if (sscanf(arg, "%d %d %lld %lld", &gi, &v, &x, &y) == 4) {
                cmd_drag(gi, v, (Coord)x, (Coord)y);
            } else {
                fputs("{\"ok\":false,\"error\":\"drag 用法：drag idx v x y\"}\n", stdout);
            }
        } else if (strcmp(line, "uv") == 0 && arg != NULL) {
            int v; long long x, y, sid;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &x, &y, &sid) == 4) {
                cmd_uv(v, (Coord)x, (Coord)y, (uint32_t)sid);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "proj") == 0 && arg != NULL) {
            int v; long long u, vv, sid;
            if (sscanf(arg, "%d %lld %lld %lld", &v, &u, &vv, &sid) == 4) {
                cmd_proj(v, (Coord)u, (Coord)vv, (uint32_t)sid);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "bhit") == 0 && arg != NULL) {
            long long bid, u, v, r;
            if (sscanf(arg, "%lld %lld %lld %lld", &bid, &u, &v, &r) == 4) {
                cmd_bhit((uint32_t)bid, (Coord)u, (Coord)v, (Coord)r);
            } else {
                fputs("{\"ok\":false}\n", stdout);
            }
        } else if (strcmp(line, "boundary") == 0 && arg != NULL) {
            cmd_boundary((uint32_t)strtoul(arg, NULL, 10));
        } else if (strcmp(line, "obstacles") == 0 && arg != NULL) {
            cmd_obstacles((uint32_t)strtoul(arg, NULL, 10));
        } else if (strcmp(line, "newid") == 0) {
            cmd_newid();
        } else if (strcmp(line, "surfaces") == 0) {
            cmd_surfaces();
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
