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

    return apply_scene_line(path, line_no, tokens, count, world);
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
    return true;
}

/* 命中物 → 一行描述；與 gdi_describe_pick 相同邏輯（那支在 _WIN32 裡碰不到）。 */
static void describe_pick(const Scene *scene, const World *world,
                          const ScenePick *p, char *buf, size_t cap)
{
    buf[0] = '\0';
    if (p == NULL || scene_pick_is_none(p)) return;

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

    if (scene.placement_count == 0 || !scene_compute_layout(&scene, &layout)) {
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
    printf(",\"guide\":%d,\"timber\":%d,\"face\":%d,\"hover\":[",
           p.guide, p.timber, (int)p.face);

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
    memset(&g_world, 0, sizeof g_world);   /* 同 gdi_load_scene_file：先 reset */
    if (parse_scene_file(path, &g_world)) {
        fputs("{\"ok\":true}\n", stdout);
    } else {
        fputs("{\"ok\":false,\"error\":", stdout);
        js_string(scene_last_error());
        fputs("}\n", stdout);
    }
}

int main(void)
{
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stdin), _O_BINARY);

    world_default(&g_world);

    char line[4096];
    while (fgets(line, sizeof line, stdin) != NULL) {
        size_t n = strlen(line);
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
        } else {
            fputs("{\"ok\":false,\"error\":\"不認得的橋接指令\"}\n", stdout);
        }
        fflush(stdout);
    }
    return 0;
}
