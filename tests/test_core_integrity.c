/* Build: gcc -std=c11 -O2 tests/test_core_integrity.c -lm -o test_core_integrity */
#include <string.h>
#define main geometry_program_main
#include "../current_geometry.c"
#undef main

static World test_world, saved_world;
static int checks, failures;
#define CHECK(expr) do { ++checks; if (!(expr)) { \
    ++failures; fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expr); \
} } while (0)

static bool command(const char *text)
{
    char line[SCENE_MAX_LINE], *tokens[SCENE_MAX_TOKENS];
    snprintf(line, sizeof line, "%s", text);
    int count = split_tokens(line, tokens, SCENE_MAX_TOKENS);
    return apply_interactive_tokens("integrity", 1, tokens, count, &test_world);
}

static void room(void)
{
    test_world = (World){0};
    history_clear();
    CHECK(command("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000"));
}

static void test_frame_updates(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    CHECK(!command("move 1 1/2*edge:e1:u"));
    CHECK(g_preview.ready && g_preview.valid);
    CHECK(test_world.guides[0].offset == 500);
    char text[64]; snprintf(text,sizeof text,"confirm %u",g_preview.token);
    CHECK(command(text));
    CHECK(test_world.guides[0].offset == 2000);
    CHECK(!command("placement 1 on boundary 1 origin 0 0 3000 u +x v +y"));
    CHECK(g_preview.valid); snprintf(text,sizeof text,"confirm %u",g_preview.token);
    CHECK(command(text)); CHECK(test_world.timbers[2].origin.z == 3000);
    CHECK(command("undo")); CHECK(test_world.timbers[2].origin.z == 2500);
    CHECK(command("redo")); CHECK(test_world.timbers[2].origin.z == 3000);
    saved_world=test_world;
    CHECK(!command("boundary 1 outline 0,0 20,0 20,3000 0,3000"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(!g_preview.valid);
}

static void test_space_extents(void)
{
    room();
    CHECK(command("space 1 boundary 1"));
    CHECK(command("boundary 1 outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(test_world.spaces[0].room_max[0] == 2000);
    saved_world = test_world;
    CHECK(!command("column 1 in 1 at 2500 100 size 100 100 z 0 2000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(!command("beam 1 in 1 along x from 2500 to 2800 at 500 width 100 depth 100 top 2000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("boundary 1 outline 0,0 4000,0 4000,3000 0,3000"));
    CHECK(test_world.spaces[0].room_max[0] == 4000);
    CHECK(command("column 1 in 1 at 2500 100 size 100 100 z 0 2000"));
    CHECK(command("beam 1 in 1 along x from 2500 to 2800 at 500 width 100 depth 100 top 2000"));
    saved_world = test_world;
    CHECK(!command("surface 1 origin 0 0 2500 u +x v +y outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete column 1"));
    saved_world = test_world;
    CHECK(!command("boundary 1 outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete beam 1"));
    CHECK(command("placement 1 on boundary 1 origin 100 200 2500 u +x v +y"));
    CHECK(test_world.spaces[0].room_min[0] == 100 && test_world.spaces[0].room_min[1] == 200);
    CHECK(test_world.spaces[0].room_max[0] == 4100 && test_world.spaces[0].room_max[1] == 3200);
}

static void test_new_placement_transaction(void)
{
    room();
    CHECK(command("space 1 boundary 1"));
    saved_world = test_world;
    CHECK(!command("placement 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(!command("surface 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete space 1"));
    CHECK(command("placement 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(test_world.placement_count == 2); /* Multiple placements remain legal without Space. */
}

static void test_grid_ref_rejects(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    CHECK(command("grid 1 on 1 u 2000 v 1000"));
    CHECK(command("timber 4 27 33 role primary")); saved_world=test_world;
    CHECK(!command("place 4 on 1 at-line grid 1 v 0 +v +n"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(command("place 4 on 1 at-line grid 1 u 0 +v +n"));
    CHECK(test_world.anchors[3].anchor_kind==ANCHOR_AT_GRID);
    CHECK(!command("grid 1 on 1 u 2500")); CHECK(g_preview.valid);
    CHECK(test_world.timbers[3].length==2946);
}

static void test_place_through_short(void)
{
    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 1 20 20 role boundary"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("place 1 on 1 at-face e0 +u +n"));
    CHECK(command("place 2 on 1 at-face e2 -u +n"));
    CHECK(command("timber 3 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 3 on 1 at-line grid 1 u 0 through 1000"));
    CHECK(strstr(scene_last_error(), "缺少長度方向與深度側") != NULL);
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
}

static void test_place_revalidates_existing_i19(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    saved_world=test_world;
    CHECK(!command("delete timber 1"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(g_preview.ready && !g_preview.valid);
    CHECK(g_preview.issue_count>0);
}

static void test_view_dist2_no_overflow(void)
{
    /* 3 km 線段、中點偏移 10mm：三次乘在 int64 會溢位，必須用 128-bit。 */
    Coord d = view_dist2_to_segment(
        (ViewPoint2){1500000, 10},
        (ViewPoint2){0, 0},
        (ViewPoint2){3000000, 0});
    CHECK(d == 100);
    d = view_dist2_to_segment(
        (ViewPoint2){1500000, 0},
        (ViewPoint2){0, 0},
        (ViewPoint2){3000000, 0});
    CHECK(d == 0);
}

static void test_partial_collinear_stop_is_not_duplicated(void)
{
    StopFace faces[]={
        {STOP_OUTLINE_EDGE,1,0,-1,0,EDGE_FIXED,1000,0,100},
        {STOP_TIMBER_SIDE,0,7,-1,0,EDGE_FIXED,1000,50,150}
    };
    const StopFace *stop=NULL;
    CHECK(pick_stop(faces,2,1000,60,80,&stop)==1);
    CHECK(stop && stop->kind==STOP_OUTLINE_EDGE);
    CHECK(count_legal_stops(faces,2,1000,60,80)==1);
    CHECK(pick_stop(faces,2,1000,110,140,&stop)==1);
    CHECK(stop && stop->kind==STOP_TIMBER_SIDE);
    CHECK(pick_stop(faces,2,1000,40,120,&stop)==0);
}

static void test_collinear_vertex_rect_corner(void)
{
    /* I2 permits adjacent collinear edges; I5 includes their shared vertex. */
    PolygonLoop2 loop = {.count=6,
        .v={{0,0},{100,0},{100,50},{100,100},{0,100},{0,50}}};
    for (size_t i=0; i<loop.count; ++i) loop.fixity[i]=EDGE_FIXED;
    SpaceBoundarySurface boundary = {.id=1, .outline=loop};
    PlacementSurface placement = {0};
    CHECK(poly_loop_is_valid(&loop));
    CHECK(boundary_is_valid(&boundary));
    CHECK(poly_point_on_edge(&loop, (SurfacePoint2){100,50}));
    CHECK(poly_contains_point(&loop, (SurfacePoint2){100,50}));
    CHECK(poly_contains_rect(&loop,80,20,100,50));
    CHECK(boundary_contains_rect(&boundary,80,20,100,50));
    CHECK(surface_contains_rect(&placement,&boundary,80,20,100,50));
    CHECK(!poly_contains_rect(&loop,80,20,101,50));
}

static void test_notch_rect_with_corners_on_ring_is_outside(void)
{
    /* GEO-257:凹槽 x∈[40,60]、y∈[40,100] 在環外。「四角都在環內 + 無環邊穿入內部」
     * 不足以證明矩形在環內:槽裡的矩形四角可以全落在槽壁上。 */
    PolygonLoop2 loop = {.count=8,
        .v={{0,0},{100,0},{100,100},{60,100},{60,40},{40,40},{40,100},{0,100}}};
    PolygonLoop2 reversed = {.count=8};
    for (size_t i=0; i<loop.count; ++i) {
        loop.fixity[i]=EDGE_FIXED;
        reversed.v[i]=loop.v[loop.count-1-i];
        reversed.fixity[i]=EDGE_FIXED;
    }
    SpaceBoundarySurface boundary = {.id=1, .outline=loop};
    PlacementSurface placement = {0};
    CHECK(poly_loop_is_valid(&loop));
    CHECK(poly_loop_is_valid(&reversed));
    CHECK(boundary_is_valid(&boundary));

    /* 反例:BACKLOG GEO-257 的 R=[40,60]x[50,70],四角都在槽壁(環邊)上、整個在槽裡。 */
    CHECK(!poly_contains_rect(&loop,40,50,60,70));
    CHECK(!boundary_contains_rect(&boundary,40,50,60,70));
    CHECK(!surface_contains_rect(&placement,&boundary,40,50,60,70));
    CHECK(!poly_contains_rect(&reversed,40,50,60,70));
    /* 同一個槽裡的其他貼壁矩形:貼槽底(角在環頂點上)、整個槽、槽的上半。 */
    CHECK(!poly_contains_rect(&loop,40,40,60,60));
    CHECK(!poly_contains_rect(&loop,40,40,60,100));
    CHECK(!poly_contains_rect(&loop,40,60,60,100));
    CHECK(!poly_contains_rect(&reversed,40,40,60,100));
    /* 中心是半整數(寬 20、高 21)時仍要判外:座標放大 2 倍後比較,不得被整數除法吃掉。 */
    CHECK(!poly_contains_rect(&loop,40,50,60,71));

    /* 對照組:碰槽壁/槽底、但真的在環內的矩形必須維持接受。 */
    CHECK(poly_contains_rect(&loop,0,50,40,70));      /* 左臂,右緣整條貼槽壁 */
    CHECK(poly_contains_rect(&loop,60,50,100,70));    /* 右臂,左緣整條貼槽壁 */
    CHECK(poly_contains_rect(&loop,40,0,60,40));      /* 槽底正下方,上緣整條貼槽底 */
    CHECK(poly_contains_rect(&loop,0,0,100,40));      /* 槽底以下整條,上緣有一段貼槽底 */
    CHECK(poly_contains_rect(&loop,20,0,40,100));     /* 貼槽壁的長條,四角在環邊/環頂點上 */
    CHECK(poly_contains_rect(&reversed,0,50,40,70));
    CHECK(poly_contains_rect(&reversed,40,0,60,40));
    CHECK(poly_contains_rect(&loop,0,50,39,51));      /* 奇數邊長、半整數中心,完全在內 */
    CHECK(boundary_contains_rect(&boundary,0,50,40,70));
    CHECK(surface_contains_rect(&placement,&boundary,40,0,60,40));

    /* 一般跨出仍然拒絕(有環邊穿入內部)。 */
    CHECK(!poly_contains_rect(&loop,30,50,70,70));    /* 橫跨整個槽 */
    CHECK(!poly_contains_rect(&loop,20,50,50,70));    /* 一半在槽裡 */
    CHECK(!poly_contains_rect(&loop,40,30,60,50));    /* 跨槽底 */
    CHECK(!poly_contains_rect(&loop,-1,0,10,10));     /* 跨出外輪廓 */
}

/* GEO-257:poly_contains_rect 對「格子取樣」真值的窮舉核對。
 * 4x4 格子的每一種格子集合(65536 種)當作一個多邊形候選:只收單一連通、無洞、無對角捏點的(正交簡單多邊形),
 * 每個多邊形用 8 種寫法(順/逆時針 x 合併共線頂點與否 x 每個整數點都切開與否)交給 poly_contains_rect,
 * 對每個頂點在格線上的矩形(座標放大 3 倍,所以奇數邊長會出現半整數中心)逐一與真值比:
 * 矩形 ⊆ 多邊形 ⇔ 矩形涵蓋的每個單位格都在集合內。 */
#define ORACLE_N 4
#define ORACLE_SCALE 3

typedef struct { int x0, y0, x1, y1; bool used; } OracleEdge;

static bool oracle_cell(unsigned set, int i, int j)
{
    return i >= 0 && j >= 0 && i < ORACLE_N && j < ORACLE_N && ((set >> (j * ORACLE_N + i)) & 1u);
}

static bool oracle_loop(unsigned set, PolygonLoop2 *loop, bool merge_collinear, bool split_all, bool reverse)
{
    OracleEdge edges[4 * ORACLE_N * ORACLE_N];
    int ne = 0;
    for (int i = 0; i < ORACLE_N; ++i)
        for (int j = 0; j < ORACLE_N; ++j) {
            if (!oracle_cell(set, i, j)) continue;
            if (!oracle_cell(set, i, j - 1)) edges[ne++] = (OracleEdge){ i, j, i + 1, j, false };
            if (!oracle_cell(set, i + 1, j)) edges[ne++] = (OracleEdge){ i + 1, j, i + 1, j + 1, false };
            if (!oracle_cell(set, i, j + 1)) edges[ne++] = (OracleEdge){ i + 1, j + 1, i, j + 1, false };
            if (!oracle_cell(set, i - 1, j)) edges[ne++] = (OracleEdge){ i, j + 1, i, j, false };
        }
    if (ne == 0) return false;
    for (int a = 0; a < ne; ++a)            /* 對角捏點:同一頂點有兩條出邊 */
        for (int b = a + 1; b < ne; ++b)
            if (edges[a].x0 == edges[b].x0 && edges[a].y0 == edges[b].y0) return false;
    int px[4 * ORACLE_N * ORACLE_N], py[4 * ORACLE_N * ORACLE_N], np = 0, cur = 0, used = 1;
    edges[0].used = true;
    px[np] = edges[0].x0; py[np] = edges[0].y0; ++np;
    for (;;) {
        int nx = edges[cur].x1, ny = edges[cur].y1, found = -1;
        if (nx == edges[0].x0 && ny == edges[0].y0) break;
        for (int k = 0; k < ne; ++k)
            if (!edges[k].used && edges[k].x0 == nx && edges[k].y0 == ny) { found = k; break; }
        if (found < 0) return false;
        edges[found].used = true; ++used;
        px[np] = nx; py[np] = ny; ++np;
        cur = found;
    }
    if (used != ne) return false;           /* 不只一圈:有洞或不連通 */
    int mx[4 * ORACLE_N * ORACLE_N], my[4 * ORACLE_N * ORACLE_N], nm = 0;
    for (int k = 0; k < np; ++k) {          /* 合併共線頂點(可選) */
        int pk = (k + np - 1) % np, nk = (k + 1) % np;
        bool collinear = (px[pk] == px[k] && px[k] == px[nk]) || (py[pk] == py[k] && py[k] == py[nk]);
        if (merge_collinear && collinear) continue;
        mx[nm] = px[k]; my[nm] = py[k]; ++nm;
    }
    int sx[8 * ORACLE_N * ORACLE_N], sy[8 * ORACLE_N * ORACLE_N], ns = 0;
    for (int k = 0; k < nm; ++k) {          /* 每個整數點都切開(可選):產生共線頂點 */
        int x1 = mx[(k + 1) % nm], y1 = my[(k + 1) % nm];
        sx[ns] = mx[k]; sy[ns] = my[k]; ++ns;
        if (split_all) {
            int len = abs(x1 - mx[k]) + abs(y1 - my[k]);
            int dx = (x1 > mx[k]) - (x1 < mx[k]), dy = (y1 > my[k]) - (y1 < my[k]);
            for (int t = 1; t < len && ns < 8 * ORACLE_N * ORACLE_N; ++t) { sx[ns] = mx[k] + dx * t; sy[ns] = my[k] + dy * t; ++ns; }
        }
    }
    if (ns < 4 || ns > POLY_MAX_VERTICES) return false;
    loop->count = (size_t)ns;
    for (int k = 0; k < ns; ++k) {
        int at = reverse ? ns - 1 - k : k;
        loop->v[k] = (SurfacePoint2){ (Coord)sx[at] * ORACLE_SCALE, (Coord)sy[at] * ORACLE_SCALE };
        loop->fixity[k] = EDGE_FIXED;
    }
    return true;
}

static void test_poly_contains_rect_matches_cell_oracle(void)
{
    long polygons[8] = {0}, wrong[8] = {0};
    long contact_cases[8] = {0}, wrong_contact[8] = {0};
    long wrong_closed_contact[8] = {0};
    for (unsigned set = 1; set < (1u << (ORACLE_N * ORACLE_N)); ++set) {
        for (int variant = 0; variant < 8; ++variant) {
            PolygonLoop2 loop = {0};
            if (!oracle_loop(set, &loop, (variant & 1) != 0, (variant & 2) != 0, (variant & 4) != 0)) continue;
            if (!poly_loop_is_valid(&loop)) { ++wrong[variant]; continue; }   /* 產生器自己的假設:輸出必為合法環 */
            ++polygons[variant];
            for (int u0 = 0; u0 < ORACLE_N; ++u0) for (int u1 = u0 + 1; u1 <= ORACLE_N; ++u1)
            for (int v0 = 0; v0 < ORACLE_N; ++v0) for (int v1 = v0 + 1; v1 <= ORACLE_N; ++v1) {
                bool truth = true;
                for (int i = u0; i < u1 && truth; ++i)
                    for (int j = v0; j < v1; ++j)
                        if (!oracle_cell(set, i, j)) { truth = false; break; }
                if (poly_contains_rect(&loop, u0 * ORACLE_SCALE, v0 * ORACLE_SCALE, u1 * ORACLE_SCALE, v1 * ORACLE_SCALE) != truth)
                    ++wrong[variant];
                /* Independent occupied-cell intersection oracle. Shrink by one mm
                 * so rectangle corners cannot lie on polygon vertices/edges. */
                int xmin=ORACLE_N, ymin=ORACLE_N, xmax=-1, ymax=-1, occupied=0;
                for (int i=u0; i<u1; ++i) for (int j=v0; j<v1; ++j)
                    if (oracle_cell(set,i,j)) {
                        if (i<xmin) xmin=i; if (i>xmax) xmax=i;
                        if (j<ymin) ymin=j; if (j>ymax) ymax=j;
                        ++occupied;
                    }
                Coord l=u0*ORACLE_SCALE+1, r=u1*ORACLE_SCALE-1;
                Coord bottom=v0*ORACLE_SCALE+1, top=v1*ORACLE_SCALE-1;
                Coord a,b,c,d; ObstacleClass cls;
                int contact=classify_rect_outline(&loop,l,bottom,r,top,&cls,&a,&b,&c,&d);
                bool rectangle=occupied && occupied==(xmax-xmin+1)*(ymax-ymin+1);
                ++contact_cases[variant];
                if ((!occupied && contact!=0) || (occupied && !rectangle && contact>=0) ||
                    (rectangle && (contact<=0 || a!=coord_max(l,xmin*ORACLE_SCALE) ||
                     b!=coord_max(bottom,ymin*ORACLE_SCALE) || c!=coord_min(r,(xmax+1)*ORACLE_SCALE) ||
                     d!=coord_min(top,(ymax+1)*ORACLE_SCALE)))) ++wrong_contact[variant];
                /* Independent closed union of occupied cells, including cells
                 * outside the query that meet it only at an edge or vertex. */
                l=u0*ORACLE_SCALE; r=u1*ORACLE_SCALE;
                bottom=v0*ORACLE_SCALE; top=v1*ORACLE_SCALE;
                int closed=classify_rect_outline(&loop,l,bottom,r,top,&cls,&a,&b,&c,&d);
                bool touches=false, extra=false;
                for (int i=0; i<ORACLE_N; ++i) for (int j=0; j<ORACLE_N; ++j) {
                    if (!oracle_cell(set,i,j)) continue;
                    Coord x0=coord_max(l,i*ORACLE_SCALE), x1=coord_min(r,(i+1)*ORACLE_SCALE);
                    Coord y0=coord_max(bottom,j*ORACLE_SCALE), y1=coord_min(top,(j+1)*ORACLE_SCALE);
                    if (x0>x1 || y0>y1) continue;
                    touches=true;
                    if (closed>0 && (x0<a || x1>c || y0<b || y1>d)) extra=true;
                }
                if ((touches && closed==0) || (closed>0 && extra) ||
                    (!touches && closed!=0)) ++wrong_closed_contact[variant];
            }
        }
    }
    for (int variant = 0; variant < 8; ++variant) {
        CHECK(polygons[variant] > 1000);   /* 真的測到了足夠多的多邊形(不是產生器默默什麼都沒產生) */
        CHECK(wrong[variant] == 0);
        CHECK(contact_cases[variant] > 100000);
        CHECK(wrong_contact[variant] == 0);
        CHECK(wrong_closed_contact[variant] == 0);
    }
}

/* #198: assertions name the two independently specified counterexamples. */
static void test_rect_outline_counterexamples(void)
{
    PolygonLoop2 notch = { .count = 8, .v = {
        {0,0},{100,0},{100,100},{60,100},{60,40},{40,40},{40,100},{0,100}
    }};
    PolygonLoop2 ridge = { .count = 8, .v = {
        {0,0},{100,0},{100,50},{60,50},{60,90},{40,90},{40,50},{0,50}
    }};
    ObstacleClass cls;
    Coord u0, v0, u1, v1;
    int counterexample_A = classify_rect_outline(&notch, 30,50,70,80,
        &cls, &u0,&v0,&u1,&v1);
    CHECK(counterexample_A < 0); /* Two disconnected contacts cannot be one hole/rectangle. */
    int counterexample_B = classify_rect_outline(&ridge, 20,70,80,80,
        &cls, &u0,&v0,&u1,&v1);
    CHECK(counterexample_B > 0);
    CHECK(cls == OBSTACLE_SPLIT);
    CHECK(u0 == 40 && v0 == 70 && u1 == 60 && v1 == 80);
    CHECK(classify_rect_outline(&notch, 10,10,20,20,
        &cls, &u0,&v0,&u1,&v1) > 0);
    CHECK(cls == OBSTACLE_HOLE);
    CHECK(u0 == 10 && v0 == 10 && u1 == 20 && v1 == 20);
    CHECK(classify_rect_outline(&notch, 110,110,120,120,
        &cls, &u0,&v0,&u1,&v1) == 0);
    CHECK(classify_rect_outline(&notch, -10,10,20,20,
        &cls, &u0,&v0,&u1,&v1) > 0);
    CHECK(cls == OBSTACLE_NOTCH);
    CHECK(u0 == 0 && v0 == 10 && u1 == 20 && v1 == 20);
    /* Reverse winding, negative coordinates, one-mm slabs and collinear vertices. */
    for (int reverse = 0; reverse < 2; ++reverse) {
        PolygonLoop2 small = { .count = 9, .v = {
            {-2,-2},{0,-2},{2,-2},{2,0},{1,0},{1,1},{0,1},{0,0},{-2,0}
        }};
        if (reverse) for (size_t i=0; i<small.count/2; ++i) {
            SurfacePoint2 t=small.v[i]; small.v[i]=small.v[small.count-1-i];
            small.v[small.count-1-i]=t;
        }
        /* The old wide footprint also touches the base at v=0 outside the
         * ridge rectangle: it is another rectangle-plus-line case, not a
         * valid positive control. Keep it as a rejection and add a true one. */
        CHECK(classify_rect_outline(&small, -1,0,2,1,
            &cls, &u0,&v0,&u1,&v1) < 0);
        CHECK(classify_rect_outline(&small, 0,0,1,1,
            &cls, &u0,&v0,&u1,&v1) > 0);
        CHECK(cls == OBSTACLE_SPLIT);
        CHECK(u0 == 0 && v0 == 0 && u1 == 1 && v1 == 1);
    }
    CHECK(classify_rect_outline(&notch, 100,100,110,110,
        &cls, &u0,&v0,&u1,&v1) < 0); /* R7: isolated point tangency. */
    int rectangle_plus_isolated_line = classify_rect_outline(&notch, 30,50,60,80,
        &cls, &u0,&v0,&u1,&v1);
    CHECK(rectangle_plus_isolated_line < 0);
    PolygonLoop2 stepped = { .count = 10, .v = {
        {0,0},{100,0},{100,100},{60,100},{60,80},
        {80,80},{80,40},{40,40},{40,100},{0,100}
    }};
    int rectangle_plus_isolated_point = classify_rect_outline(&stepped, 30,50,60,80,
        &cls, &u0,&v0,&u1,&v1);
    CHECK(rectangle_plus_isolated_point < 0);
}

/* Integer orthogonal fixtures partition into whole 1 mm cells. Odd doubled
 * centres enumerate their complete open interiors without engine predicates. */
static bool split_oracle_cell(const PolygonLoop2 *loop, Coord u, Coord v)
{
    bool inside = false;
    for (size_t i=0; i<loop->count; ++i) {
        SurfacePoint2 a=loop->v[i], b=loop->v[(i+1)%loop->count];
        if (a.u==b.u && 2*coord_min(a.v,b.v)<2*v+1 &&
            2*v+1<2*coord_max(a.v,b.v) && 2*a.u>2*u+1) inside=!inside;
    }
    return inside;
}

static bool split_oracle_difference(const PolygonLoop2 *before,
    const PolygonLoop2 *p1, const PolygonLoop2 *p2,
    Coord u0, Coord v0, Coord u1, Coord v1, int *area)
{
    Coord l,b,r,t; poly_bbox(before,&l,&b,&r,&t);
    bool exact=true; *area=0;
    for (Coord u=l-1; u<=r; ++u) for (Coord v=b-1; v<=t; ++v) {
        bool wanted=split_oracle_cell(before,u,v) && !(u>=u0 && u<u1 && v>=v0 && v<v1);
        int actual=split_oracle_cell(p1,u,v)+split_oracle_cell(p2,u,v);
        if (wanted) ++*area;
        if (actual!=(int)wanted) exact=false; /* Also rejects overlap and extra cells. */
    }
    return exact;
}

static void test_projection_corner_contact_is_local(void)
{
    const PolygonLoop2 original={.count=12,.v={{0,10},{10,10},{10,0},{20,0},{20,10},{30,10},
        {30,20},{20,20},{20,40},{10,40},{10,20},{0,20}}};
    for (int variant=0; variant<16; ++variant) {
        PolygonLoop2 loop=original;
        Coord offset=(variant&8)?-50:0;
        size_t shift=(variant&4)?original.count-1:0;
        for (size_t i=0;i<loop.count;++i) {
            size_t at=(variant&1)?(shift+loop.count-i)%loop.count:(shift+i)%loop.count;
            SurfacePoint2 p=original.v[at];
            loop.v[i]=(variant&2)?(SurfacePoint2){p.v+offset,p.u+offset}:
                                    (SurfacePoint2){p.u+offset,p.v+offset};
            loop.fixity[i]=EDGE_FIXED;
        }
        CHECK(poly_loop_is_valid(&loop));
        Coord a,b,c,d; ObstacleClass cls;
        int corner_only_despite_remote_side_contact=classify_rect_outline(&loop,
            10+offset,10+offset,(variant&2)?30+offset:20+offset,
            (variant&2)?20+offset:30+offset,&cls,&a,&b,&c,&d);
        CHECK(corner_only_despite_remote_side_contact<0); /* R7: the corner itself has no positive edge. */
        Coord l=(variant&2)?20+offset:10+offset, bottom=(variant&2)?10+offset:20+offset;
        Coord r=(variant&2)?30+offset:20+offset, top=(variant&2)?20+offset:30+offset;
        CHECK(classify_rect_outline(&loop,l,bottom,r,top,&cls,&a,&b,&c,&d)>0);
        CHECK(cls==OBSTACLE_SPLIT); /* Same remote edges, but now positive contact begins at all corners. */
        bool flush[4]; for(int side=0;side<4;++side)flush[side]=side_flush_outline(&loop,side,a,b,c,d);
        PolygonLoop2 p1={0},p2={0};
        CHECK(proj_split_loop(&loop,flush,a,b,c,d,&p1,&p2));
        int area=0;
        CHECK(split_oracle_difference(&loop,&p1,&p2,a,b,c,d,&area));
        CHECK(area==500);
        CHECK(proj_loop_area2(&p1)+proj_loop_area2(&p2)==1000);
    }
}

static void test_projection_three_residual_components(void)
{
    const PolygonLoop2 fixtures[2] = {
        {.count=14,.v={{0,10},{10,10},{10,0},{20,0},{20,10},{30,10},{30,0},
                      {40,0},{40,20},{20,20},{20,30},{10,30},{10,20},{0,20}}},
        {.count=12,.v={{0,10},{10,10},{10,0},{20,0},{20,10},{30,10},
                      {30,20},{20,20},{20,30},{10,30},{10,20},{0,20}}}
    };
    for (int which=0; which<2; ++which) for (int variant=0; variant<8; ++variant) {
        PolygonLoop2 loop=fixtures[which], p1={0}, p2={0};
        size_t shift=(variant&4)?loop.count-1:0;
        for (size_t i=0; i<loop.count; ++i) {
            size_t at=(variant&1)?(shift+loop.count-i)%loop.count:(shift+i)%loop.count;
            SurfacePoint2 a=fixtures[which].v[at];
            loop.v[i]=(variant&2)?(SurfacePoint2){a.v-50,a.u-50}:(SurfacePoint2){a.u-50,a.v-50};
            loop.fixity[i]=EDGE_FIXED;
        }
        CHECK(poly_loop_is_valid(&loop));
        Coord u0=(variant&2)?-40:-60, v0=(variant&2)?-60:-40;
        Coord u1=(variant&2)?-30:0, v1=(variant&2)?0:-30;
        Coord a,b,c,d; ObstacleClass cls;
        CHECK(classify_rect_outline(&loop,u0,v0,u1,v1,&cls,&a,&b,&c,&d)==1);
        CHECK(cls==OBSTACLE_SPLIT);
        bool flush[4]; for (int s=0;s<4;++s) flush[s]=side_flush_outline(&loop,s,a,b,c,d);
        bool split=proj_split_loop(&loop,flush,a,b,c,d,&p1,&p2);
        bool three_residual_components_rejected=(which==0)?!split:split;
        CHECK(three_residual_components_rejected);
        int area=0;
        bool exact=split_oracle_difference(&loop,&p1,&p2,a,b,c,d,&area);
        CHECK(area==(which==0?300:200));
        bool saved_union_is_exact=!split||exact;
        CHECK(saved_union_is_exact);
        CHECK(!split||proj_loop_area2(&p1)+proj_loop_area2(&p2)==2*area);
        SurfacePoint2 removed={-35,-35};
        CHECK(!split||(!poly_contains_point(&p1,removed)&&!poly_contains_point(&p2,removed)));
    }
}

int main(void)
{
    test_projection_corner_contact_is_local();
    test_projection_three_residual_components();
    test_rect_outline_counterexamples();
    test_collinear_vertex_rect_corner();
    test_notch_rect_with_corners_on_ring_is_outside();
    test_poly_contains_rect_matches_cell_oracle();
    test_partial_collinear_stop_is_not_duplicated();
    test_frame_updates();
    test_space_extents();
    test_new_placement_transaction();
    test_grid_ref_rejects();
    test_place_through_short();
    test_place_revalidates_existing_i19();
    test_view_dist2_no_overflow();
    printf("%d/%d integrity checks passed (World=%zu bytes)\n", checks-failures, checks, sizeof(World));
    return failures ? 1 : 0;
}
