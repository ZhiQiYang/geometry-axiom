#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * 目前整合版：
 *
 * 1. 建立房間座標中的空間邊界面。
 * 2. 從空間邊界面推導四條正交邊。
 * 3. 每條邊可取得局部座標、房間座標，以及它所在的側向平面。
 * 4. 在空間邊界面上建立非實體參考線。
 * 5. 以兩條參考線的交點作為角材放置錨點。
 * 6. Construct 一支 27 × 33 × L 的完整角材。
 * 7. 把角材 A0 面貼到空間邊界面。
 * 8. 從完整角材推導 A0、A1、B0、B1、START、END 六個面。
 *
 * 第一版限制：
 *
 * - 1 個座標單位 = 1 mm。
 * - 空間邊界面是矩形。
 * - 表面座標框架只接受正交的單位軸向量。
 * - 角材長度方向只能沿表面的 ±U 或 ±V。
 *
 * 配套：geometry-guide/ 下的導讀頁內嵌本檔快照，
 * 改動本檔後須重跑 make_guide.py + check_panels.py。
 */

typedef int64_t Coord;

typedef uint32_t SurfaceId;
typedef uint32_t SurfaceEdgeId;
typedef uint32_t GuideLineId;
typedef uint32_t TimberId;

/* ============================================================
 * 基礎幾何型別
 * ============================================================ */

typedef struct {
    Coord x;
    Coord y;
    Coord z;
} Point3;

typedef struct {
    Coord x;
    Coord y;
    Coord z;
} Vector3;

typedef struct {
    Coord u;
    Coord v;
} SurfacePoint2;

typedef struct {
    SurfacePoint2 start;
    SurfacePoint2 end;
} SurfaceSegment2;

typedef struct {
    Point3 start;
    Point3 end;
} Segment3;

typedef struct {
    Point3 vertices[4];
} Quad3;

typedef struct {
    Point3 point;
    Vector3 normal;
} Plane3;

/* ============================================================
 * 向量運算
 * ============================================================ */

static Coord vector_dot(Vector3 a, Vector3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static Vector3 vector_cross(Vector3 a, Vector3 b)
{
    return (Vector3){
        .x = a.y * b.z - a.z * b.y,
        .y = a.z * b.x - a.x * b.z,
        .z = a.x * b.y - a.y * b.x
    };
}

static Vector3 vector_negate(Vector3 v)
{
    return (Vector3){
        .x = -v.x,
        .y = -v.y,
        .z = -v.z
    };
}

static bool vector_equal(Vector3 a, Vector3 b)
{
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

/* ============================================================
 * 承載面的局部座標框架
 * ============================================================ */

/*
 * 承載面（PlacementSurface）的局部座標框架。
 *
 * origin：
 *   表面局部 (u=0,v=0,w=0) 在房間座標中的位置。
 *
 * axis_u、axis_v：
 *   表面內的兩個正交方向。
 *
 * normal：
 *   離開表面的方向。
 *
 * 任意表面座標 (u,v,w) 對應的房間座標：
 *
 *   room = origin + u*axis_u + v*axis_v + w*normal
 */
typedef struct {
    Point3 origin;
    Vector3 axis_u;
    Vector3 axis_v;
    Vector3 normal;
} SurfaceFrame;

/* 自帶矩形範圍（承載面未掛邊界面時的退路）。 */
typedef struct {
    Coord min_u;
    Coord min_v;
    Coord max_u;
    Coord max_v;
} SurfaceRegion2;

/*
 * 第一版要求 U、V、N 都是長度 1 的正交整數軸，
 * 並且 U × V = N。
 *
 * 只需檢查三件事：U、V 長度 1，U ⊥ V，U × V = N。
 * N 的其餘性質由叉積保證，不必再檢查：
 *   N ⊥ U、N ⊥ V：叉積垂直於兩個因子。
 *   |N| = 1：|U × V|² = |U|²|V|² − (U·V)² = 1。
 */
static bool surface_frame_is_valid(const SurfaceFrame *frame)
{
    if (frame == NULL) {
        return false;
    }

    return vector_dot(frame->axis_u, frame->axis_u) == 1 &&
           vector_dot(frame->axis_v, frame->axis_v) == 1 &&
           vector_dot(frame->axis_u, frame->axis_v) == 0 &&
           vector_equal(
               vector_cross(frame->axis_u, frame->axis_v),
               frame->normal
           );
}

/* ============================================================
 * 局部 2D 正交多邊形（空間邊界面的形狀語言）
 *
 * PolygonLoop2 是一條封閉的頂點環：
 *   - 頂點依序相連，最後一點接回第一點。
 *   - 每條邊必須軸平行（u 相等或 v 相等）。
 *   - 邊 i 是 v[i] → v[i+1]（i+1 對 count 取模）。
 *   - fixity[i] 是邊 i 的固定/自由語意，不寫預設全 FIXED。
 * ============================================================ */

#define POLY_MAX_VERTICES 32
#define POLY_MAX_HOLES     8

typedef enum {
    EDGE_FREE = 0,      /* 外側無垂直實體面可釘（挑空/陽角/門洞…） */
    EDGE_FIXED = 1      /* 有：牆、樓板、樑底、柱面、陰角 */
} EdgeFixity;

typedef enum {
    BOUNDARY_UNSPECIFIED,
    BOUNDARY_ROOM_PLAN,        /* 平面圖視角 */
    BOUNDARY_WALL_ELEVATION    /* 立面 */
} BoundaryKind;

typedef struct {
    SurfacePoint2 v[POLY_MAX_VERTICES];
    size_t count;
    EdgeFixity fixity[POLY_MAX_VERTICES];
} PolygonLoop2;

static Coord coord_min(Coord a, Coord b) { return a < b ? a : b; }
static Coord coord_max(Coord a, Coord b) { return a > b ? a : b; }

/*
 * 環的合法性（I2）：
 *   ≥4 頂點、頂點數為偶數（正交多邊形每轉彎兩次才回得起始軸）、
 *   每邊軸平行且非零長、非自交（非相鄰邊不得相交或共線重疊）、
 *   有向面積非零（不自退化）。
 */
static bool poly_loop_is_valid(const PolygonLoop2 *loop)
{
    if (loop == NULL || loop->count < 4 ||
        loop->count > POLY_MAX_VERTICES || loop->count % 2 != 0) {
        return false;
    }

    /* 邊的軸平行與非零長檢查。 */
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        bool axis_u = a.v == b.v;   /* 沿 U 方向的邊：v 座標不變 */
        bool axis_v = a.u == b.u;

        if ((!axis_u && !axis_v) || (a.u == b.u && a.v == b.v)) {
            return false;
        }
    }

    /* 非相鄰邊不得相交或共線重疊。 */
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a1 = loop->v[i];
        SurfacePoint2 a2 = loop->v[(i + 1) % loop->count];

        for (size_t j = i + 2; j < loop->count; ++j) {
            if (i == 0 && j + 1 == loop->count) {
                continue;   /* 首邊與末邊相鄰，共享頂點合法 */
            }

            SurfacePoint2 b1 = loop->v[j];
            SurfacePoint2 b2 = loop->v[(j + 1) % loop->count];

            /* 軸平行線段的相交/共線重疊判定。 */
            if (a1.u == a2.u && b1.u == b2.u) {
                /* 兩條直立邊。 */
                if (a1.u != b1.u) {
                    continue;
                }
                if (coord_max(coord_min(a1.v, a2.v), coord_min(b1.v, b2.v)) <=
                    coord_min(coord_max(a1.v, a2.v), coord_max(b1.v, b2.v))) {
                    return false;   /* 共線且區間重疊 */
                }
            } else if (a1.v == a2.v && b1.v == b2.v) {
                /* 兩條水平邊。 */
                if (a1.v != b1.v) {
                    continue;
                }
                if (coord_max(coord_min(a1.u, a2.u), coord_min(b1.u, b2.u)) <=
                    coord_min(coord_max(a1.u, a2.u), coord_max(b1.u, b2.u))) {
                    return false;
                }
            } else {
                /* 一橫一直：交點須嚴格同時落在兩邊內部才算相交；
                 * 端點相碰在非相鄰邊上也不允許（會形成接觸自交）。 */
                SurfacePoint2 h1, h2, s1, s2;
                if (a1.v == a2.v) { h1 = a1; h2 = a2; s1 = b1; s2 = b2; }
                else              { h1 = b1; h2 = b2; s1 = a1; s2 = a2; }

                Coord hu_min = coord_min(h1.u, h2.u);
                Coord hu_max = coord_max(h1.u, h2.u);
                Coord sv_min = coord_min(s1.v, s2.v);
                Coord sv_max = coord_max(s1.v, s2.v);

                if (s1.u >= hu_min && s1.u <= hu_max &&
                    h1.v >= sv_min && h1.v <= sv_max) {
                    return false;
                }
            }
        }
    }

    /* 有向面積非零（shoelace）；順/逆時針不限，但必須有面積。 */
    Coord area2 = 0;
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];
        area2 += a.u * b.v - b.u * a.v;
    }

    return area2 != 0;
}

/* 點是否落在環的邊上。 */
static bool poly_point_on_edge(const PolygonLoop2 *loop, SurfacePoint2 p)
{
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u == b.u) {
            if (p.u == a.u &&
                p.v >= coord_min(a.v, b.v) && p.v <= coord_max(a.v, b.v)) {
                return true;
            }
        } else {
            if (p.v == a.v &&
                p.u >= coord_min(a.u, b.u) && p.u <= coord_max(a.u, b.u)) {
                return true;
            }
        }
    }

    return false;
}

/*
 * 點是否在環內（含邊界）。
 * 射線法：向右射一條水平線，數與直立邊的交叉次數；
 * 半開區間 [v_min, v_max) 避免頂點被數兩次。
 */
static bool poly_contains_point(const PolygonLoop2 *loop, SurfacePoint2 p)
{
    if (loop == NULL) {
        return false;
    }

    if (poly_point_on_edge(loop, p)) {
        return true;
    }

    int crossings = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u != b.u) {
            continue;   /* 水平邊不與水平射線交叉 */
        }

        Coord v_min = coord_min(a.v, b.v);
        Coord v_max = coord_max(a.v, b.v);

        if (p.v >= v_min && p.v < v_max && p.u < a.u) {
            ++crossings;
        }
    }

    return crossings % 2 == 1;
}

/*
 * 線段與矩形內部是否相交（端點在矩形邊上不算相交）。
 * 矩形 = [min_u,max_u] × [min_v,max_v]。
 */
static bool segment2_crosses_rect_interior(
    SurfacePoint2 a, SurfacePoint2 b,
    Coord min_u, Coord min_v, Coord max_u, Coord max_v
)
{
    if (a.u == b.u) {
        /* 直立邊：u 須嚴格在 (min_u,max_u) 內，且 v 區間與 (min_v,max_v) 有正長度交集。 */
        if (a.u <= min_u || a.u >= max_u) {
            return false;
        }
        Coord lo = coord_max(coord_min(a.v, b.v), min_v);
        Coord hi = coord_min(coord_max(a.v, b.v), max_v);
        return lo < hi;
    }

    if (a.v <= min_v || a.v >= max_v) {
        return false;
    }
    Coord lo = coord_max(coord_min(a.u, b.u), min_u);
    Coord hi = coord_min(coord_max(a.u, b.u), max_u);
    return lo < hi;
}

/*
 * 軸平行矩形 ⊆ 環（含邊界）。
 * 四角都在環內 + 無任何環邊穿過矩形內部 → 矩形全在環內。
 * （若矩形跨出環，必有環邊穿入矩形內部；四角在內只是必要條件。）
 */
static bool poly_contains_rect(
    const PolygonLoop2 *loop,
    Coord min_u, Coord min_v, Coord max_u, Coord max_v
)
{
    if (loop == NULL || min_u >= max_u || min_v >= max_v) {
        return false;
    }

    SurfacePoint2 corners[4] = {
        { min_u, min_v }, { max_u, min_v },
        { max_u, max_v }, { min_u, max_v }
    };

    for (size_t i = 0; i < 4; ++i) {
        if (!poly_contains_point(loop, corners[i])) {
            return false;
        }
    }

    for (size_t i = 0; i < loop->count; ++i) {
        if (segment2_crosses_rect_interior(
                loop->v[i], loop->v[(i + 1) % loop->count],
                min_u, min_v, max_u, max_v)) {
            return false;
        }
    }

    return true;
}

/* 環的軸向外接矩形。 */
static void poly_bbox(
    const PolygonLoop2 *loop,
    Coord *out_min_u, Coord *out_min_v,
    Coord *out_max_u, Coord *out_max_v
)
{
    Coord min_u = loop->v[0].u, max_u = loop->v[0].u;
    Coord min_v = loop->v[0].v, max_v = loop->v[0].v;

    for (size_t i = 1; i < loop->count; ++i) {
        min_u = coord_min(min_u, loop->v[i].u);
        max_u = coord_max(max_u, loop->v[i].u);
        min_v = coord_min(min_v, loop->v[i].v);
        max_v = coord_max(max_v, loop->v[i].v);
    }

    *out_min_u = min_u;
    *out_min_v = min_v;
    *out_max_u = max_u;
    *out_max_v = max_v;
}

/*
 * 一條軸平行直線與環的交集 = 若干線段。
 * line 是「垂直座標 = offset」的無限線；axis_u_line 表示線沿 U 走
 * （固定 v=offset），否則沿 V 走（固定 u=offset）。
 * 演算法：蒐集所有邊與直線的交點座標，排序後依奇偶配對成線段。
 * 半開區間避免頂點重複計數。
 */
static size_t poly_clip_line(
    const PolygonLoop2 *loop,
    bool along_u,
    Coord offset,
    SurfaceSegment2 out[],
    size_t out_cap
)
{
    Coord crossings[POLY_MAX_VERTICES];
    size_t crossing_count = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        if (along_u) {
            /* 直線 v=offset 只與直立邊（a.u == b.u）相交；
             * 水平邊（a.v == b.v）與它平行，跳過。 */
            if (a.v == b.v) {
                continue;
            }
            Coord v_min = coord_min(a.v, b.v);
            Coord v_max = coord_max(a.v, b.v);
            if (offset >= v_min && offset < v_max) {
                crossings[crossing_count++] = a.u;
            }
        } else {
            /* 直線 u=offset 只與水平邊（a.v == b.v）相交；
             * 直立邊與它平行，跳過。 */
            if (a.u == b.u) {
                continue;
            }
            Coord u_min = coord_min(a.u, b.u);
            Coord u_max = coord_max(a.u, b.u);
            if (offset >= u_min && offset < u_max) {
                crossings[crossing_count++] = a.v;
            }
        }
    }

    /* 插入排序交點；頂點處的相鄰兩邊只會貢獻一個交點（半開區間），
     * 但水平邊端點與直立邊可能給出重複交點——去重。 */
    for (size_t i = 1; i < crossing_count; ++i) {
        Coord key = crossings[i];
        size_t j = i;
        while (j > 0 && crossings[j - 1] > key) {
            crossings[j] = crossings[j - 1];
            --j;
        }
        crossings[j] = key;
    }

    size_t unique = 0;
    for (size_t i = 0; i < crossing_count; ++i) {
        if (unique == 0 || crossings[i] != crossings[unique - 1]) {
            crossings[unique++] = crossings[i];
        }
    }
    crossing_count = unique;

    /* 奇偶配對：[0,1]、[2,3]… 各成一條內部線段。 */
    size_t seg_count = 0;
    for (size_t i = 0; i + 1 < crossing_count && seg_count < out_cap; i += 2) {
        Coord lo = crossings[i];
        Coord hi = crossings[i + 1];

        if (along_u) {
            out[seg_count].start = (SurfacePoint2){ lo, offset };
            out[seg_count].end   = (SurfacePoint2){ hi, offset };
        } else {
            out[seg_count].start = (SurfacePoint2){ offset, lo };
            out[seg_count].end   = (SurfacePoint2){ offset, hi };
        }
        ++seg_count;
    }

    return seg_count;
}

/* ============================================================
 * 空間邊界面（SpaceBoundarySurface）：空間的實體邊界，純局部 2D
 *
 * 內容：正交外輪廓 + 零個以上內孔 + 每邊 fixity + 分類。
 * 不知道自己坐在世界哪裡——3D 位置由承載面（PlacementSurface）給。
 * ============================================================ */

typedef struct {
    SurfaceId id;
    BoundaryKind kind;
    PolygonLoop2 outline;
    PolygonLoop2 holes[POLY_MAX_HOLES];
    size_t hole_count;
} SpaceBoundarySurface;

/* 外輪廓合法 + 每個孔合法、嚴格在外輪廓內、孔之間互不重疊。 */
static bool boundary_is_valid(const SpaceBoundarySurface *b)
{
    if (b == NULL || !poly_loop_is_valid(&b->outline)) {
        return false;
    }

    for (size_t h = 0; h < b->hole_count; ++h) {
        const PolygonLoop2 *hole = &b->holes[h];

        if (!poly_loop_is_valid(hole)) {
            return false;
        }

        /* 孔的每個頂點必須在外輪廓內（不含外輪廓邊上），
         * 且孔的每條邊不得穿外輪廓。 */
        for (size_t i = 0; i < hole->count; ++i) {
            SurfacePoint2 p = hole->v[i];

            if (poly_point_on_edge(&b->outline, p) ||
                !poly_contains_point(&b->outline, p)) {
                return false;
            }
        }

        for (size_t i = 0; i < hole->count; ++i) {
            SurfacePoint2 a = hole->v[i];
            SurfacePoint2 c = hole->v[(i + 1) % hole->count];

            for (size_t j = 0; j < b->outline.count; ++j) {
                SurfacePoint2 d = b->outline.v[j];
                SurfacePoint2 e = b->outline.v[(j + 1) % b->outline.count];

                /* 孔邊與外輪廓邊不得相交（含共線）。 */
                if (a.u == c.u && d.u == e.u) {
                    if (a.u == d.u &&
                        coord_max(coord_min(a.v, c.v), coord_min(d.v, e.v)) <
                        coord_min(coord_max(a.v, c.v), coord_max(d.v, e.v))) {
                        return false;
                    }
                } else if (a.v == c.v && d.v == e.v) {
                    if (a.v == d.v &&
                        coord_max(coord_min(a.u, c.u), coord_min(d.u, e.u)) <
                        coord_min(coord_max(a.u, c.u), coord_max(d.u, e.u))) {
                        return false;
                    }
                } else {
                    SurfacePoint2 h1, h2, s1, s2;
                    if (a.v == c.v) { h1 = a; h2 = c; s1 = d; s2 = e; }
                    else            { h1 = d; h2 = e; s1 = a; s2 = c; }

                    if (s1.u > coord_min(h1.u, h2.u) &&
                        s1.u < coord_max(h1.u, h2.u) &&
                        h1.v > coord_min(s1.v, s2.v) &&
                        h1.v < coord_max(s1.v, s2.v)) {
                        return false;
                    }
                }
            }
        }

        /* 孔互不重疊：任一孔頂點落在別孔內，或邊互相穿越，即拒絕。 */
        for (size_t k = h + 1; k < b->hole_count; ++k) {
            const PolygonLoop2 *other = &b->holes[k];

            for (size_t i = 0; i < hole->count; ++i) {
                if (poly_contains_point(other, hole->v[i])) {
                    return false;
                }
            }
            for (size_t i = 0; i < other->count; ++i) {
                if (poly_contains_point(hole, other->v[i])) {
                    return false;
                }
            }
        }
    }

    return true;
}

/* 點是否在邊界面的有效區域：外輪廓內（含邊上）且不在任何孔內（孔邊上算在外）。 */
static bool boundary_contains_point(
    const SpaceBoundarySurface *b,
    SurfacePoint2 p
)
{
    if (b == NULL || !poly_contains_point(&b->outline, p)) {
        return false;
    }

    for (size_t h = 0; h < b->hole_count; ++h) {
        const PolygonLoop2 *hole = &b->holes[h];

        if (poly_contains_point(hole, p) &&
            !poly_point_on_edge(hole, p)) {
            return false;
        }
    }

    return true;
}

/*
 * 軸平行矩形 ⊆ 有效區域：矩形在外輪廓內，且與每個孔的內部不相交。
 * （孔邊上接觸允許：角材可以貼著柱面走。）
 */
static bool boundary_contains_rect(
    const SpaceBoundarySurface *b,
    Coord min_u, Coord min_v, Coord max_u, Coord max_v
)
{
    if (b == NULL ||
        !poly_contains_rect(&b->outline, min_u, min_v, max_u, max_v)) {
        return false;
    }

    for (size_t h = 0; h < b->hole_count; ++h) {
        const PolygonLoop2 *hole = &b->holes[h];
        Coord h_min_u, h_min_v, h_max_u, h_max_v;
        poly_bbox(hole, &h_min_u, &h_min_v, &h_max_u, &h_max_v);

        /* 矩形與孔 bbox 無交集 → 快退。 */
        if (h_max_u <= min_u || h_min_u >= max_u ||
            h_max_v <= min_v || h_min_v >= max_v) {
            continue;
        }

        /* 任一孔頂點嚴格在矩形內 → 相交。 */
        for (size_t i = 0; i < hole->count; ++i) {
            SurfacePoint2 p = hole->v[i];
            if (p.u > min_u && p.u < max_u &&
                p.v > min_v && p.v < max_v) {
                return false;
            }
        }

        /* 任一孔邊穿過矩形內部 → 相交。 */
        for (size_t i = 0; i < hole->count; ++i) {
            if (segment2_crosses_rect_interior(
                    hole->v[i], hole->v[(i + 1) % hole->count],
                    min_u, min_v, max_u, max_v)) {
                return false;
            }
        }

        /* 孔整個罩住矩形（矩形四角都在孔內）。 */
        if (poly_contains_point(hole, (SurfacePoint2){ min_u + 1, min_v + 1 }) &&
            !poly_point_on_edge(hole, (SurfacePoint2){ min_u + 1, min_v + 1 })) {
            /* min+1 只是代表點：四角嚴格在孔內才算罩住。
             * 用四角逐一判定較穩。 */
            SurfacePoint2 corners[4] = {
                { min_u, min_v }, { max_u, min_v },
                { max_u, max_v }, { min_u, max_v }
            };
            size_t inside = 0;
            for (size_t i = 0; i < 4; ++i) {
                if (poly_contains_point(hole, corners[i])) {
                    ++inside;
                }
            }
            if (inside == 4) {
                return false;
            }
        }
    }

    return true;
}

/* ============================================================
 * 承載面（PlacementSurface）：角材釘上去的那面
 *
 *   frame：3D 嵌入（origin + U/V/N）——世界位置只活在這裡。
 *   boundary_id：掛哪片邊界面；0 = 游離，用自帶 rect。
 *   rect：boundary_id == 0 時的矩形有效範圍。
 * ============================================================ */

typedef struct {
    SurfaceId id;
    SurfaceFrame frame;
    SurfaceId boundary_id;
    SurfaceRegion2 rect;
} PlacementSurface;

static bool placement_is_valid(const PlacementSurface *p)
{
    if (p == NULL || !surface_frame_is_valid(&p->frame)) {
        return false;
    }

    if (p->boundary_id == 0) {
        return p->rect.min_u < p->rect.max_u &&
               p->rect.min_v < p->rect.max_v;
    }

    return true;
}

/* 將承載面局部座標轉成房間三維座標。 */
static Point3 surface_point_to_room(
    const PlacementSurface *surface,
    Coord u,
    Coord v,
    Coord w
)
{
    return (Point3){
        .x = surface->frame.origin.x +
             u * surface->frame.axis_u.x +
             v * surface->frame.axis_v.x +
             w * surface->frame.normal.x,

        .y = surface->frame.origin.y +
             u * surface->frame.axis_u.y +
             v * surface->frame.axis_v.y +
             w * surface->frame.normal.y,

        .z = surface->frame.origin.z +
             u * surface->frame.axis_u.z +
             v * surface->frame.axis_v.z +
             w * surface->frame.normal.z
    };
}

/*
 * 承載面的有效輪廓：有掛邊界面就用它的 outline；
 * 沒掛就把自帶 rect 展成一個四頂點環（全部 FIXED）。
 */
static void placement_outline(
    const PlacementSurface *p,
    const SpaceBoundarySurface *boundary,
    PolygonLoop2 *out
)
{
    if (boundary != NULL) {
        *out = boundary->outline;
        return;
    }

    out->count = 4;
    out->v[0] = (SurfacePoint2){ p->rect.min_u, p->rect.min_v };
    out->v[1] = (SurfacePoint2){ p->rect.max_u, p->rect.min_v };
    out->v[2] = (SurfacePoint2){ p->rect.max_u, p->rect.max_v };
    out->v[3] = (SurfacePoint2){ p->rect.min_u, p->rect.max_v };
    for (size_t i = 0; i < 4; ++i) {
        out->fixity[i] = EDGE_FIXED;
    }
}

/* 承載面有效區域的點包含判定。 */
static bool surface_contains_point(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    SurfacePoint2 point
)
{
    if (surface == NULL) {
        return false;
    }

    if (boundary != NULL) {
        return boundary_contains_point(boundary, point);
    }

    return point.u >= surface->rect.min_u &&
           point.u <= surface->rect.max_u &&
           point.v >= surface->rect.min_v &&
           point.v <= surface->rect.max_v;
}

/* 承載面有效區域的矩形包含判定。 */
static bool surface_contains_rect(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    Coord min_u, Coord min_v, Coord max_u, Coord max_v
)
{
    if (boundary != NULL) {
        return boundary_contains_rect(boundary, min_u, min_v, max_u, max_v);
    }

    return surface != NULL &&
           min_u >= surface->rect.min_u && max_u <= surface->rect.max_u &&
           min_v >= surface->rect.min_v && max_v <= surface->rect.max_v;
}

/* 環的外接矩形。 */
static bool polygon_loop_bounds(
    const PolygonLoop2 *loop,
    SurfaceRegion2 *out
)
{
    if (loop == NULL || out == NULL || loop->count == 0) {
        return false;
    }

    Coord min_u = loop->v[0].u, max_u = loop->v[0].u;
    Coord min_v = loop->v[0].v, max_v = loop->v[0].v;

    for (size_t i = 1; i < loop->count; ++i) {
        min_u = coord_min(min_u, loop->v[i].u);
        max_u = coord_max(max_u, loop->v[i].u);
        min_v = coord_min(min_v, loop->v[i].v);
        max_v = coord_max(max_v, loop->v[i].v);
    }

    *out = (SurfaceRegion2){ min_u, min_v, max_u, max_v };
    return true;
}

/* 承載面有效區域的外接矩形（邊界面 = 輪廓 bbox；無邊界面 = 自帶 rect）。 */
static bool placement_local_bounds(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    SurfaceRegion2 *out
)
{
    if (surface == NULL || out == NULL) {
        return false;
    }

    if (boundary != NULL) {
        return polygon_loop_bounds(&boundary->outline, out);
    }

    if (surface->rect.min_u >= surface->rect.max_u ||
        surface->rect.min_v >= surface->rect.max_v) {
        return false;
    }

    *out = surface->rect;
    return true;
}

/* ============================================================
 * 邊界面的邊：由外輪廓環推導，不再是獨立宣告的物件
 *
 * 邊 i = outline.v[i] → outline.v[i+1]，fixity 存在環上。
 * ============================================================ */

/* 邊 i 在 UV 中的線段（環的第 i 條邊）。 */
static bool loop_get_edge_segment(
    const PolygonLoop2 *loop,
    size_t edge_index,
    SurfaceSegment2 *out_segment
)
{
    if (loop == NULL || out_segment == NULL ||
        edge_index >= loop->count) {
        return false;
    }

    out_segment->start = loop->v[edge_index];
    out_segment->end = loop->v[(edge_index + 1) % loop->count];
    return true;
}

/*
 * 環邊的局部外向法線（在 UV 平面內）。
 * 先算環的有向面積定左右手，再取邊方向 × 環內側。
 * 回傳 ±U 或 ±V 的單位方向（dx, dy in UV）。
 */
static bool loop_edge_outward_normal(
    const PolygonLoop2 *loop,
    size_t edge_index,
    SurfacePoint2 *out_normal
)
{
    SurfaceSegment2 seg;

    if (out_normal == NULL ||
        !loop_get_edge_segment(loop, edge_index, &seg)) {
        return false;
    }

    Coord area2 = 0;
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];
        area2 += a.u * b.v - b.u * a.v;
    }

    /* 邊方向。 */
    Coord du = seg.end.u - seg.start.u;
    Coord dv = seg.end.v - seg.start.v;

    /*
     * CCW 環（area2 > 0）：內側在邊的左邊 → 外向 = (dv, -du)。
     * CW  環（area2 < 0）：內側在右邊 → 外向 = (-dv, du)。
     * 邊是單位軸平行，所以 (dv,-du)/(-dv,du) 必有一分量 ±1、另一分量 0。
     */
    if (area2 > 0) {
        out_normal->u = dv > 0 ? 1 : (dv < 0 ? -1 : 0);
        out_normal->v = du > 0 ? -1 : (du < 0 ? 1 : 0);
    } else {
        out_normal->u = dv > 0 ? -1 : (dv < 0 ? 1 : 0);
        out_normal->v = du > 0 ? 1 : (du < 0 ? -1 : 0);
    }

    return true;
}

/* 邊的 UV 線段 → 房間座標三維線段（承載面提供 frame）。 */
static bool surface_get_edge_room_segment(
    const PlacementSurface *surface,
    const SurfaceSegment2 *local,
    Segment3 *out_segment
)
{
    if (surface == NULL || local == NULL || out_segment == NULL) {
        return false;
    }

    out_segment->start = surface_point_to_room(
        surface, local->start.u, local->start.v, 0);
    out_segment->end = surface_point_to_room(
        surface, local->end.u, local->end.v, 0);
    return true;
}

/*
 * 取得與該邊關聯的側向承載平面：
 * 邊上的任一點 + 局部外向法線（經 frame 轉成房間方向）。
 */
static bool surface_get_edge_side_plane(
    const PlacementSurface *surface,
    const SurfaceSegment2 *local,
    SurfacePoint2 uv_outward_normal,
    Plane3 *out_plane
)
{
    if (surface == NULL || local == NULL || out_plane == NULL) {
        return false;
    }

    out_plane->point = surface_point_to_room(
        surface, local->start.u, local->start.v, 0);

    /* UV 法線 (nu, nv) → 房間方向 = nu*axis_u + nv*axis_v。 */
    out_plane->normal = (Vector3){
        .x = uv_outward_normal.u * surface->frame.axis_u.x +
             uv_outward_normal.v * surface->frame.axis_v.x,
        .y = uv_outward_normal.u * surface->frame.axis_u.y +
             uv_outward_normal.v * surface->frame.axis_v.y,
        .z = uv_outward_normal.u * surface->frame.axis_u.z +
             uv_outward_normal.v * surface->frame.axis_v.z
    };

    return true;
}

/* ============================================================
 * 表面參考線：只有定位作用，不是實體
 * ============================================================ */

typedef enum {
    GUIDE_ALONG_U,
    GUIDE_ALONG_V
} GuideDirection;

typedef struct {
    GuideLineId id;
    SurfaceId placement_id;     /* 屬於哪片承載面 */
    GuideDirection direction;

    /*
     * GUIDE_ALONG_U：固定 v = offset。
     * GUIDE_ALONG_V：固定 u = offset。
     */
    Coord offset;
} GuideLine;

/*
 * offset 的合法範圍 = 有效輪廓的軸向外接區間。
 * （外接區間內的線未必真的截到輪廓——L 形凹區會落空；
 *   截線為零段的 offset 在 get_local_segments 自然給出空集合。）
 */
static bool guide_offset_in_range(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    GuideDirection direction,
    Coord offset
)
{
    if (surface == NULL) {
        return false;
    }

    Coord min_u, min_v, max_u, max_v;

    if (boundary != NULL) {
        poly_bbox(&boundary->outline, &min_u, &min_v, &max_u, &max_v);
    } else {
        min_u = surface->rect.min_u;
        min_v = surface->rect.min_v;
        max_u = surface->rect.max_u;
        max_v = surface->rect.max_v;
    }

    if (direction == GUIDE_ALONG_U) {
        return offset >= min_v && offset <= max_v;
    }

    if (direction == GUIDE_ALONG_V) {
        return offset >= min_u && offset <= max_u;
    }

    return false;
}

static bool create_guide_line(
    GuideLineId id,
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    GuideDirection direction,
    Coord offset,
    GuideLine *out_guide
)
{
    if (surface == NULL || out_guide == NULL) {
        return false;
    }

    if (!guide_offset_in_range(surface, boundary, direction, offset)) {
        return false;
    }

    *out_guide = (GuideLine){
        .id = id,
        .placement_id = surface->id,
        .direction = direction,
        .offset = offset
    };

    return true;
}

/*
 * 移動既有參考線 = 改它的 offset 定義。
 * 範圍檢查與 create 共用；已放置的角材不追溯——place 是事件不是約束。
 */
static bool guide_line_move(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    GuideLine *guide,
    Coord offset
)
{
    if (surface == NULL || guide == NULL ||
        guide->placement_id != surface->id ||
        !guide_offset_in_range(surface, boundary, guide->direction, offset)) {
        return false;
    }

    guide->offset = offset;
    return true;
}

/*
 * 參考線在有效區域中的線段（可能多段：外輪廓截出區間、再扣掉孔區間）。
 * 回傳段數；0 段表示這條線完全落在輪廓外（凹區）。
 */
static size_t guide_line_get_local_segments(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    const GuideLine *guide,
    SurfaceSegment2 out[],
    size_t out_cap
)
{
    if (surface == NULL || guide == NULL || out == NULL || out_cap == 0 ||
        guide->placement_id != surface->id) {
        return 0;
    }

    bool along_u = guide->direction == GUIDE_ALONG_U;

    if (boundary == NULL) {
        /* 自帶矩形：整條線一段，不截。 */
        SurfacePoint2 lo, hi;

        if (along_u) {
            lo = (SurfacePoint2){ surface->rect.min_u, guide->offset };
            hi = (SurfacePoint2){ surface->rect.max_u, guide->offset };
        } else {
            lo = (SurfacePoint2){ guide->offset, surface->rect.min_v };
            hi = (SurfacePoint2){ guide->offset, surface->rect.max_v };
        }

        out[0].start = lo;
        out[0].end = hi;
        return 1;
    }

    /* 外輪廓截線。 */
    SurfaceSegment2 segs[POLY_MAX_VERTICES];
    size_t seg_count =
        poly_clip_line(&boundary->outline, along_u, guide->offset,
                       segs, POLY_MAX_VERTICES);

    /* 逐孔扣掉落在孔內的子區間。 */
    for (size_t h = 0; h < boundary->hole_count; ++h) {
        SurfaceSegment2 hole_segs[POLY_MAX_VERTICES];
        size_t hole_count =
            poly_clip_line(&boundary->holes[h], along_u, guide->offset,
                           hole_segs, POLY_MAX_VERTICES);

        for (size_t hs = 0; hs < hole_count; ++hs) {
            /* 孔區間在「沿線軸」上的 [h_lo, h_hi]。 */
            Coord h_lo, h_hi;
            if (along_u) {
                h_lo = hole_segs[hs].start.u;
                h_hi = hole_segs[hs].end.u;
            } else {
                h_lo = hole_segs[hs].start.v;
                h_hi = hole_segs[hs].end.v;
            }

            /* 每條現有線段與孔區間做差集，可能裂成兩段。 */
            SurfaceSegment2 next[POLY_MAX_VERTICES];
            size_t next_count = 0;

            for (size_t s = 0; s < seg_count; ++s) {
                Coord s_lo, s_hi;
                if (along_u) {
                    s_lo = segs[s].start.u;
                    s_hi = segs[s].end.u;
                } else {
                    s_lo = segs[s].start.v;
                    s_hi = segs[s].end.v;
                }

                Coord keep_lo = s_lo;
                Coord keep_hi = s_hi;

                if (h_lo <= s_lo && h_hi >= s_hi) {
                    continue;   /* 整段被孔吃掉 */
                }

                if (h_hi <= s_lo || h_lo >= s_hi) {
                    next[next_count++] = segs[s];   /* 不相交，整段留下 */
                    continue;
                }

                /* 部分重疊：留下不重疊的一或兩段。 */
                if (h_lo > s_lo) {
                    keep_lo = s_lo;
                    keep_hi = h_lo;
                } else {
                    keep_lo = h_hi;
                    keep_hi = s_hi;
                }

                if (along_u) {
                    next[next_count].start = (SurfacePoint2){ keep_lo, guide->offset };
                    next[next_count].end   = (SurfacePoint2){ keep_hi, guide->offset };
                } else {
                    next[next_count].start = (SurfacePoint2){ guide->offset, keep_lo };
                    next[next_count].end   = (SurfacePoint2){ guide->offset, keep_hi };
                }
                ++next_count;

                /* 孔區間把線段剖成兩段的情形：h_lo > s_lo 且 h_hi < s_hi。 */
                if (h_lo > s_lo && h_hi < s_hi && next_count < POLY_MAX_VERTICES) {
                    if (along_u) {
                        next[next_count].start = (SurfacePoint2){ h_hi, guide->offset };
                        next[next_count].end   = (SurfacePoint2){ s_hi, guide->offset };
                    } else {
                        next[next_count].start = (SurfacePoint2){ guide->offset, h_hi };
                        next[next_count].end   = (SurfacePoint2){ guide->offset, s_hi };
                    }
                    ++next_count;
                }
            }

            memcpy(segs, next, next_count * sizeof *segs);
            seg_count = next_count;
        }
    }

    size_t n = seg_count < out_cap ? seg_count : out_cap;
    memcpy(out, segs, n * sizeof *out);
    return n;
}

/*
 * 求同一承載面上一條 U 方向線與一條 V 方向線的交點。
 * 多邊形之後「offset 在外接區間」不再保證交點在有效區域
 * （可能落在凹區或孔裡），所以要另外檢查有效區域。
 */
static bool guide_line_intersection(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    const GuideLine *a,
    const GuideLine *b,
    SurfacePoint2 *out_point
)
{
    if (surface == NULL || a == NULL || b == NULL || out_point == NULL) {
        return false;
    }

    if (a->placement_id != surface->id ||
        b->placement_id != surface->id ||
        a->direction == b->direction) {
        return false;
    }

    const GuideLine *along_u =
        a->direction == GUIDE_ALONG_U ? a : b;

    const GuideLine *along_v =
        a->direction == GUIDE_ALONG_V ? a : b;

    SurfacePoint2 point = {
        .u = along_v->offset,
        .v = along_u->offset
    };

    /* 交點必須真的在有效區域內（輪廓內、孔外）。 */
    if (!surface_contains_point(surface, boundary, point)) {
        return false;
    }

    *out_point = point;
    return true;
}


/* ============================================================
 * 參考網格（ReferenceGrid）：一座標集合 = 一組參考線
 *
 *   u_coords[i]：u 座標 → 線沿 V 走；
 *   v_coords[i]：v 座標 → 線沿 U 走。
 *
 * 公理 G1–G4：
 *   1. 每片承載面最多一座網格；
 *   2. 每個座標集合嚴格遞增、不重複；
 *   3. 座標落在承載面有效範圍的軸向外接區間內；
 *   4. 網格是唯讀參考資料：線段由座標與輪廓推導，不存獨立狀態。
 * ============================================================ */

#define GRID_MAX_LINES 32

typedef struct {
    uint32_t id;
    SurfaceId placement_id;

    Coord u_coords[GRID_MAX_LINES];
    size_t u_count;
    Coord v_coords[GRID_MAX_LINES];
    size_t v_count;
} ReferenceGrid;

static bool grid_coord_list_is_valid(const Coord coords[], size_t count)
{
    for (size_t i = 0; i < count; ++i) {
        if (i > 0 && coords[i] <= coords[i - 1]) {
            return false;   /* 必須嚴格遞增 */
        }
    }

    return true;
}

static bool grid_is_valid(
    const ReferenceGrid *grid,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary
)
{
    if (grid == NULL || placement == NULL ||
        grid->placement_id != placement->id ||
        grid->u_count > GRID_MAX_LINES ||
        grid->v_count > GRID_MAX_LINES ||
        (grid->u_count == 0 && grid->v_count == 0)) {
        return false;
    }

    if (!grid_coord_list_is_valid(grid->u_coords, grid->u_count) ||
        !grid_coord_list_is_valid(grid->v_coords, grid->v_count)) {
        return false;
    }

    /* 座標落在外接區間內——與 guide offset 同一條規則。 */
    SurfaceRegion2 bounds;

    if (!placement_local_bounds(placement, boundary, &bounds)) {
        return false;
    }

    for (size_t i = 0; i < grid->u_count; ++i) {
        if (grid->u_coords[i] < bounds.min_u ||
            grid->u_coords[i] > bounds.max_u) {
            return false;
        }
    }

    for (size_t i = 0; i < grid->v_count; ++i) {
        if (grid->v_coords[i] < bounds.min_v ||
            grid->v_coords[i] > bounds.max_v) {
            return false;
        }
    }

    return true;
}

/* ============================================================
 * 完整角材實體
 * ============================================================ */

/*
 * 角材局部座標：
 *
 *   local X：長度 L
 *   local Y：A 尺寸，例如 27
 *   local Z：B 尺寸，例如 33
 *
 * 六個面：
 *
 *   A0：local Z = 0，尺寸 L × A
 *   A1：local Z = B，尺寸 L × A
 *   B0：local Y = 0，尺寸 L × B
 *   B1：local Y = A，尺寸 L × B
 *   START：local X = 0，尺寸 A × B
 *   END：local X = L，尺寸 A × B
 */
typedef enum {
    TIMBER_FACE_A0,
    TIMBER_FACE_A1,
    TIMBER_FACE_B0,
    TIMBER_FACE_B1,
    TIMBER_FACE_START,
    TIMBER_FACE_END,
    TIMBER_FACE_COUNT
} TimberFaceId;

/*
 * 六個面出自同一條規則：面 = 法向軸 k + 哪一側 s。
 *
 *   k：0 = 長度軸，1 = A 軸，2 = B 軸。
 *   s：0 = 座標 0 側，1 = 滿尺寸側。
 *
 * 面內兩軸是第 (k+1)%3 與 (k+2)%3 軸；(u, w, k) 恆為右手系
 * （u × w = k），所以同一個繞行順序在 s=1 給出 +k 法向、
 * 反向走在 s=0 給出 −k 法向：六個面的法向一律朝外。
 */
static const struct {
    unsigned char axis;
    unsigned char side;
} TIMBER_FACE_SPEC[TIMBER_FACE_COUNT] = {
    [TIMBER_FACE_A0]    = { 2, 0 },
    [TIMBER_FACE_A1]    = { 2, 1 },
    [TIMBER_FACE_B0]    = { 1, 0 },
    [TIMBER_FACE_B1]    = { 1, 1 },
    [TIMBER_FACE_START] = { 0, 0 },
    [TIMBER_FACE_END]   = { 0, 1 }
};

/* 面內四角的繞行順序：沿 u、w 兩軸的 0/1 係數。 */
static const unsigned char TIMBER_FACE_WALK[2][4][2] = {
    { {0,0}, {0,1}, {1,1}, {1,0} },   /* s = 0：反向 */
    { {0,0}, {1,0}, {1,1}, {0,1} }    /* s = 1：正向 */
};

/* 每個面的全名（文字輸出）與短名（圖上標籤）。 */
static const struct {
    const char *full;
    const char *brief;
} TIMBER_FACE_NAMES[TIMBER_FACE_COUNT] = {
    [TIMBER_FACE_A0]    = { "A0（接觸面）",     "A0"    },
    [TIMBER_FACE_A1]    = { "A1（另一個 A 面）", "A1"    },
    [TIMBER_FACE_B0]    = { "B0",              "B0"    },
    [TIMBER_FACE_B1]    = { "B1",              "B1"    },
    [TIMBER_FACE_START] = { "START 端面",       "START" },
    [TIMBER_FACE_END]   = { "END 端面",         "END"   }
};

static bool timber_face_id_is_valid(TimberFaceId face)
{
    return face >= TIMBER_FACE_A0 && face < TIMBER_FACE_COUNT;
}

static const char *timber_face_name(TimberFaceId face)
{
    return timber_face_id_is_valid(face)
        ? TIMBER_FACE_NAMES[face].full
        : "UNKNOWN_FACE";
}

static const char *timber_face_short_name(TimberFaceId face)
{
    return timber_face_id_is_valid(face)
        ? TIMBER_FACE_NAMES[face].brief
        : "?";
}

typedef enum {
    SURFACE_DIRECTION_POS_U,
    SURFACE_DIRECTION_NEG_U,
    SURFACE_DIRECTION_POS_V,
    SURFACE_DIRECTION_NEG_V
} SurfaceDirection;

typedef enum {
    SURFACE_DEPTH_POSITIVE_NORMAL,
    SURFACE_DEPTH_NEGATIVE_NORMAL
} SurfaceDepthSide;

typedef struct {
    TimberId id;

    Coord length;
    Coord size_a;
    Coord size_b;

    /*
     * true = auto 角材（timber id A B）：length 不是輸入，
     * 而是 place 當下由可延伸區間推導後凍結的結果。
     * false = 明寫長度（timber id L A B）。
     */
    bool auto_length;

    bool placed;

    /*
     * 完整角材放入房間後的局部座標框架。
     */
    Point3 origin;
    Vector3 axis_length;
    Vector3 axis_a;
    Vector3 axis_b;
} Timber;

/* Construct 一支完整角材，但此時尚未放進空間邊界面。 */
static bool timber_construct(
    TimberId id,
    Coord length,
    Coord size_a,
    Coord size_b,
    bool auto_length,
    Timber *out_timber
)
{
    if (out_timber == NULL ||
        size_a <= 0 ||
        size_b <= 0 ||
        (!auto_length && length <= 0) ||
        (auto_length && length != 0)) {
        return false;
    }

    *out_timber = (Timber){
        .id = id,
        .length = length,
        .size_a = size_a,
        .size_b = size_b,
        .auto_length = auto_length,
        .placed = false,

        /* 尚未放置前，先使用標準局部框架。 */
        .origin = { 0, 0, 0 },
        .axis_length = { 1, 0, 0 },
        .axis_a = { 0, 1, 0 },
        .axis_b = { 0, 0, 1 }
    };

    return true;
}

static Vector3 surface_direction_vector(
    const PlacementSurface *surface,
    SurfaceDirection direction
)
{
    switch (direction) {
        case SURFACE_DIRECTION_POS_U:
            return surface->frame.axis_u;

        case SURFACE_DIRECTION_NEG_U:
            return vector_negate(surface->frame.axis_u);

        case SURFACE_DIRECTION_POS_V:
            return surface->frame.axis_v;

        case SURFACE_DIRECTION_NEG_V:
            return vector_negate(surface->frame.axis_v);

        default:
            return (Vector3){ 0, 0, 0 };
    }
}

/*
 * 將完整角材的 A0 面貼到承載面。
 *
 * anchor：
 *   角材局部原點 (0,0,0) 在表面上的 UV 位置。
 *
 * length_direction：
 *   角材長度沿表面的哪一個正交方向。
 *
 * depth_side：
 *   角材 B 尺寸朝表面法線哪一側延伸。
 *
 * 前提：surface 已通過 placement_is_valid；
 * boundary 是 surface 掛的邊界面（NULL = 自帶矩形）。
 *
 * 放置規則（公理 I5/I6）：
 *   1. 錨點在有效區域內；
 *   2. 整個 A0 矩形 ⊆ 有效區域（輪廓內、不跨孔）；
 *   3. 長度兩端若正好貼在邊界面的外輪廓邊上，
 *      對應的邊必須是 FIXED（V_FREE_EDGE_END）。
 */
static bool timber_place_a0_on_surface(
    Timber *timber,
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    SurfacePoint2 anchor,
    SurfaceDirection length_direction,
    SurfaceDepthSide depth_side
)
{
    if (timber == NULL ||
        surface == NULL ||
        !surface_contains_point(surface, boundary, anchor)) {
        return false;
    }

    Vector3 axis_length = surface_direction_vector(
        surface,
        length_direction
    );

    if (vector_dot(axis_length, axis_length) != 1) {
        return false;
    }

    Vector3 axis_b =
        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL
            ? surface->frame.normal
            : vector_negate(surface->frame.normal);

    /*
     * 保持右手座標：
     *
     *   axis_length × axis_a = axis_b
     *
     * 因此：
     *
     *   axis_a = axis_b × axis_length
     *
     * 兩個因子都是單位長且互相垂直，axis_a 必為單位長，不必再檢查。
     */
    Vector3 axis_a = vector_cross(axis_b, axis_length);

    SurfacePoint2 far_corner = {
        .u = anchor.u +
             timber->length * vector_dot(axis_length, surface->frame.axis_u) +
             timber->size_a * vector_dot(axis_a, surface->frame.axis_u),

        .v = anchor.v +
             timber->length * vector_dot(axis_length, surface->frame.axis_v) +
             timber->size_a * vector_dot(axis_a, surface->frame.axis_v)
    };

    Coord rect_min_u = coord_min(anchor.u, far_corner.u);
    Coord rect_max_u = coord_max(anchor.u, far_corner.u);
    Coord rect_min_v = coord_min(anchor.v, far_corner.v);
    Coord rect_max_v = coord_max(anchor.v, far_corner.v);

    /* 整個 A0 矩形必須在有效區域內——凹角與孔洞下
     * 「兩角點在內」不再是充分條件。 */
    if (!surface_contains_rect(
            surface, boundary,
            rect_min_u, rect_min_v, rect_max_u, rect_max_v)) {
        return false;
    }

    /*
     * 端面（START/END，長度軸的兩端）若正好貼在外輪廓邊上，
     * 該邊必須是 FIXED：自由邊外側沒有垂直實體面，釘不住。
     * 端面懸在面內部（沒貼任何邊）不檢查——那是懸臂。
     */
    if (boundary != NULL) {
        const PolygonLoop2 *outline = &boundary->outline;
        Coord end_uv[2];
        bool ends_along_v;   /* 端面線段在 UV 中沿 V 走（長度沿 U） */

        if (vector_dot(axis_length, surface->frame.axis_u) != 0) {
            /* 長度沿 U：端面在 u = min/max，線段沿 V。 */
            end_uv[0] = rect_min_u;
            end_uv[1] = rect_max_u;
            ends_along_v = true;
        } else {
            /* 長度沿 V：端面在 v = min/max，線段沿 U。 */
            end_uv[0] = rect_min_v;
            end_uv[1] = rect_max_v;
            ends_along_v = false;
        }

        for (int e = 0; e < 2; ++e) {
            Coord end_at = end_uv[e];

            for (size_t i = 0; i < outline->count; ++i) {
                SurfacePoint2 a = outline->v[i];
                SurfacePoint2 b = outline->v[(i + 1) % outline->count];

                if (ends_along_v) {
                    /* 端面線段在 u=end_at、v ∈ [rect_min_v, rect_max_v]；
                     * 找共線且重疊的直立輪廓邊。 */
                    if (a.u != b.u || a.u != end_at) {
                        continue;
                    }
                    if (coord_max(rect_min_v, coord_min(a.v, b.v)) <
                        coord_min(rect_max_v, coord_max(a.v, b.v)) &&
                        outline->fixity[i] == EDGE_FREE) {
                        return false;
                    }
                } else {
                    if (a.v != b.v || a.v != end_at) {
                        continue;
                    }
                    if (coord_max(rect_min_u, coord_min(a.u, b.u)) <
                        coord_min(rect_max_u, coord_max(a.u, b.u)) &&
                        outline->fixity[i] == EDGE_FREE) {
                        return false;
                    }
                }
            }
        }
    }

    timber->origin = surface_point_to_room(
        surface,
        anchor.u,
        anchor.v,
        0
    );

    timber->axis_length = axis_length;
    timber->axis_a = axis_a;
    timber->axis_b = axis_b;
    timber->placed = true;

    return true;
}

/* 將角材局部座標轉成房間三維座標。 */
static Point3 timber_local_to_room(
    const Timber *timber,
    Coord length_coordinate,
    Coord a_coordinate,
    Coord b_coordinate
)
{
    return (Point3){
        .x = timber->origin.x +
             length_coordinate * timber->axis_length.x +
             a_coordinate * timber->axis_a.x +
             b_coordinate * timber->axis_b.x,

        .y = timber->origin.y +
             length_coordinate * timber->axis_length.y +
             a_coordinate * timber->axis_a.y +
             b_coordinate * timber->axis_b.y,

        .z = timber->origin.z +
             length_coordinate * timber->axis_length.z +
             a_coordinate * timber->axis_a.z +
             b_coordinate * timber->axis_b.z
    };
}

/* 從完整角材推導指定面的四個房間座標頂點。 */
static bool timber_get_face_room(
    const Timber *timber,
    TimberFaceId face,
    Quad3 *out_face
)
{
    if (timber == NULL || out_face == NULL ||
        !timber->placed || !timber_face_id_is_valid(face)) {
        return false;
    }

    const Coord dims[3] = { timber->length, timber->size_a, timber->size_b };
    const int k = TIMBER_FACE_SPEC[face].axis;
    const int s = TIMBER_FACE_SPEC[face].side;
    const int u = (k + 1) % 3;
    const int w = (k + 2) % 3;

    for (size_t i = 0; i < 4; ++i) {
        Coord local[3] = { 0, 0, 0 };
        local[k] = s ? dims[k] : 0;
        local[u] = TIMBER_FACE_WALK[s][i][0] ? dims[u] : 0;
        local[w] = TIMBER_FACE_WALK[s][i][1] ? dims[w] : 0;
        out_face->vertices[i] = timber_local_to_room(
            timber,
            local[0],
            local[1],
            local[2]
        );
    }

    return true;
}

/* ============================================================
 * 輸出函式
 * ============================================================ */

static void print_coord3(Coord x, Coord y, Coord z)
{
    printf(
        "(%" PRId64 ", %" PRId64 ", %" PRId64 ")",
        x,
        y,
        z
    );
}

static void print_point3(Point3 point)
{
    print_coord3(point.x, point.y, point.z);
}

static void print_vector3(Vector3 vector)
{
    print_coord3(vector.x, vector.y, vector.z);
}

static void print_axis_aligned_plane(const Plane3 *plane)
{
    if (plane == NULL) {
        return;
    }

    if (plane->normal.x != 0 &&
        plane->normal.y == 0 &&
        plane->normal.z == 0) {
        printf("x = %" PRId64, plane->point.x);
        return;
    }

    if (plane->normal.x == 0 &&
        plane->normal.y != 0 &&
        plane->normal.z == 0) {
        printf("y = %" PRId64, plane->point.y);
        return;
    }

    if (plane->normal.x == 0 &&
        plane->normal.y == 0 &&
        plane->normal.z != 0) {
        printf("z = %" PRId64, plane->point.z);
        return;
    }

    printf("非軸對齊平面");
}

static void print_surface_edge(
    const PlacementSurface *surface,
    const PolygonLoop2 *outline,
    size_t edge_index
)
{
    SurfaceSegment2 local;
    Segment3 room;
    Plane3 side_plane;
    SurfacePoint2 uv_normal;

    if (surface == NULL || outline == NULL ||
        !loop_get_edge_segment(outline, edge_index, &local) ||
        !loop_edge_outward_normal(outline, edge_index, &uv_normal) ||
        !surface_get_edge_room_segment(surface, &local, &room) ||
        !surface_get_edge_side_plane(surface, &local, uv_normal, &side_plane)) {
        return;
    }

    printf(
        "\n邊 #%zu（%s）：\n",
        edge_index,
        outline->fixity[edge_index] == EDGE_FIXED ? "FIXED" : "FREE"
    );

    printf(
        "  表面局部線段："
        "(%" PRId64 ", %" PRId64 ") -> "
        "(%" PRId64 ", %" PRId64 ")\n",
        local.start.u,
        local.start.v,
        local.end.u,
        local.end.v
    );

    printf("  房間三維線段：");
    print_point3(room.start);
    printf(" -> ");
    print_point3(room.end);
    printf("\n");

    printf("  側向承載平面：");
    print_axis_aligned_plane(&side_plane);
    printf("\n");

    printf("  向外法線：");
    print_vector3(side_plane.normal);
    printf("\n");
}

/* 印邊界面的所有外輪廓邊與孔邊。 */
static void print_boundary_edges(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary
)
{
    for (size_t i = 0; i < boundary->outline.count; ++i) {
        print_surface_edge(surface, &boundary->outline, i);
    }

    for (size_t h = 0; h < boundary->hole_count; ++h) {
        const PolygonLoop2 *hole = &boundary->holes[h];

        printf("\n孔 #%zu：\n", h);

        for (size_t i = 0; i < hole->count; ++i) {
            print_surface_edge(surface, hole, i);
        }
    }
}

static void print_guide_line(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    const GuideLine *guide
)
{
    SurfaceSegment2 segs[POLY_MAX_VERTICES];
    size_t n = guide_line_get_local_segments(
        surface, boundary, guide, segs, POLY_MAX_VERTICES);

    if (n == 0) {
        printf("參考線 %" PRIu32 "：（落在有效區域之外，無線段）\n",
               guide->id);
        return;
    }

    for (size_t i = 0; i < n; ++i) {
        if (n > 1) {
            printf("參考線 %" PRIu32 "（段 %zu）：", guide->id, i);
        } else {
            printf("參考線 %" PRIu32 "：", guide->id);
        }
        printf(
            "(%" PRId64 ", %" PRId64 ") -> "
            "(%" PRId64 ", %" PRId64 ")\n",
            segs[i].start.u,
            segs[i].start.v,
            segs[i].end.u,
            segs[i].end.v
        );
    }
}

static void print_timber_face(
    const Timber *timber,
    TimberFaceId face
)
{
    Quad3 quad;

    if (!timber_get_face_room(timber, face, &quad)) {
        return;
    }

    printf("\n角材 %u 的 %s：\n", timber->id, timber_face_name(face));

    for (size_t i = 0; i < 4; ++i) {
        printf("  vertex[%zu] = ", i);
        print_point3(quad.vertices[i]);
        printf("\n");
    }
}

/* ============================================================
 * 三視圖：幾何走訪與繪圖後端介面
 *
 * 幾何只走訪一次，「畫到哪裡」交給後端決定：
 *   - SVG 後端：純 C，只用 stdio 把幾何印成 SVG 標籤（第一層）。
 *   - GDI 後端：呼叫 Windows 自帶的 user32 / gdi32 開視窗（第二層）。
 * ============================================================ */

/*
 * 視圖 = 兩個互相垂直的單位軸（與 SurfaceFrame 同一個公理）：
 *
 *   right：畫面 +x 對應的房間方向
 *   down ：畫面 +y 對應的房間方向（螢幕與 SVG 的 y 軸都向下）
 *
 * 視線方向（從觀者射進場景）不另外存，由叉積決定：
 *
 *   into = right × down
 *
 * 投影就是內積：畫面座標 = (p·right, p·down)；p·into 越小越靠近觀者。
 * 畫面方向與遠近順序出自同一組軸，所以不可能是鏡像。
 *
 * 版面採第三角法：前視圖在左上，從哪一側看就放在前視圖的哪一側。
 *   側視圖（觀者在 +X）放右邊，與前視圖共用 Z；
 *   仰視圖（觀者在 -Z，從房間往上看天花板）放下面，與前視圖共用 X。
 */
typedef struct {
    const char *title;
    Vector3 right;
    Vector3 down;
} ViewFrame;

enum {
    VIEW_FRONT,
    VIEW_SIDE,
    VIEW_BOTTOM,
    VIEW_COUNT
};

/*
 * 前視：X × (-Z) = +Y，觀者在 -Y。
 * 側視：Y × (-Z) = -X，觀者在 +X。
 * 仰視：X × Y    = +Z，觀者在 -Z。
 */
static const ViewFrame VIEW_FRAMES[VIEW_COUNT] = {
    [VIEW_FRONT]  = { "前視圖（X 向右，Z 向上）", { 1, 0, 0 }, { 0, 0, -1 } },
    [VIEW_SIDE]   = { "側視圖（Y 向右，Z 向上）", { 0, 1, 0 }, { 0, 0, -1 } },
    [VIEW_BOTTOM] = { "仰視圖（X 向右，Y 向下）", { 1, 0, 0 }, { 0, 1,  0 } }
};

typedef struct {
    Coord x;
    Coord y;
} ViewPoint2;

typedef struct {
    Coord min_x;
    Coord min_y;
    Coord max_x;
    Coord max_y;
    bool has_point;
} ViewBounds;

/* ============================================================
 * 空間（Space）：建構子參數 = 一組邊界面 id；成員不可變。
 * 範圍與封閉與否由成員的承載面推導——只讀衍生，不是輸入。
 * ============================================================ */

typedef struct {
    uint32_t id;
    SurfaceId boundaries[8];    /* 成員邊界面 id（建構時傳入） */
    size_t boundary_count;
    Coord room_min[3];          /* 推導：各軸下界（slot 有面才有效） */
    Coord room_max[3];
    bool closed;                /* 六個方向槽位全滿 */
} Space;

/* ---- RC 柱/樑（公理 D13/D14）----
 *
 *   房間座標的軸對齊方塊（AABB），是空間的障礙物、不是成員面。
 *   本層只存資料；對邊界面的投影一律推導（obstacles）＋明確套用，
 *   不自動裁切。
 *
 *   RcBeam.axis：0 = 沿 x，1 = 沿 y（語法保證軸平行，I16）。
 *   z_hi 一律是實值：省略 top/z 時由所屬空間 ±Z 槽推導後凍結存入。
 */
typedef struct {
    uint32_t id;
    uint32_t space_id;          /* 0 = 游離 */
    Coord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;
} RcColumn;

typedef struct {
    uint32_t id;
    uint32_t space_id;          /* 0 = 游離 */
    int axis;                   /* 0 = 沿 x，1 = 沿 y */
    Coord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;
} RcBeam;

/* 一張圖要畫的所有東西；全部只是引用，不複製。 */
typedef struct {
    const PlacementSurface *placements;
    size_t placement_count;
    const SpaceBoundarySurface *boundaries;
    size_t boundary_count;
    const Space *spaces;
    size_t space_count;
    const GuideLine *guides;
    size_t guide_count;
    const ReferenceGrid *grids;
    size_t grid_count;
    const Timber *timbers;
    size_t timber_count;
    const RcColumn *columns;
    size_t column_count;
    const RcBeam *beams;
    size_t beam_count;
} Scene;

static const PlacementSurface *scene_find_placement(
    const Scene *scene,
    SurfaceId id
)
{
    for (size_t i = 0; i < scene->placement_count; ++i) {
        if (scene->placements[i].id == id) {
            return &scene->placements[i];
        }
    }

    return NULL;
}

static const SpaceBoundarySurface *scene_find_boundary(
    const Scene *scene,
    SurfaceId id
)
{
    for (size_t i = 0; i < scene->boundary_count; ++i) {
        if (scene->boundaries[i].id == id) {
            return &scene->boundaries[i];
        }
    }

    return NULL;
}

/* 承載面掛的邊界面（0 = 沒掛）。 */
static const SpaceBoundarySurface *scene_placement_boundary(
    const Scene *scene,
    const PlacementSurface *placement
)
{
    if (placement->boundary_id == 0) {
        return NULL;
    }

    return scene_find_boundary(scene, placement->boundary_id);
}

/* 畫什麼「角色」由幾何層決定；長什麼樣子由各後端決定。 */
typedef enum {
    STYLE_FRAME,
    STYLE_TITLE,
    STYLE_SURFACE,
    STYLE_EDGE,
    STYLE_EDGE_FREE,
    STYLE_HOLE,
    STYLE_LABEL,
    STYLE_GUIDE,
    STYLE_GUIDE_LABEL,
    STYLE_TIMBER_FACE,
    STYLE_TIMBER_FACE_NEAR,
    STYLE_TIMBER_LABEL,
    STYLE_HOVER,
    STYLE_RC_COLUMN,
    STYLE_RC_BEAM,
    STYLE_COUNT
} DrawStyle;

/*
 * 每種角色的外觀規格；一個值只在一處定義，兩個後端都從這裡取。
 *
 *   line / fill：「#rrggbb」。fill 為 NULL 表示此角色沒有填色。
 *   gdi_fill：GDI 沒有半透明，含透明的填色給它一個替代實色；
 *            NULL 表示 GDI 直接用 fill。
 *   svg_fill_opacity：SVG 專用（0~1），GDI 忽略。
 *   text_mm / bold：文字樣式用；text_mm = 0 表示非文字。
 *   線寬與虛線樣式是各後端的渲染機制，不在這張表裡。
 */
typedef struct {
    const char *line;
    const char *fill;
    const char *gdi_fill;
    double svg_fill_opacity;
    int text_mm;
    bool bold;
} StyleSpec;

static const StyleSpec STYLE_SPEC[STYLE_COUNT] = {
    [STYLE_FRAME]            = { "#bbbbbb", "#ffffff", NULL,      1.0,    0, false },
    [STYLE_TITLE]            = { "#222222", NULL,      NULL,      1.0,  150, true  },
    [STYLE_SURFACE]          = { "#3366cc", "#dbe9ff", NULL,      0.6,    0, false },
    [STYLE_EDGE]             = { "#3366cc", NULL,      NULL,      1.0,    0, false },
    [STYLE_EDGE_FREE]        = { "#e08020", NULL,      NULL,      1.0,    0, false },
    [STYLE_HOLE]             = { "#3366cc", "#ffffff", NULL,      1.0,    0, false },
    [STYLE_LABEL]            = { "#333333", NULL,      NULL,      1.0,  110, false },
    [STYLE_GUIDE]            = { "#cc3333", NULL,      NULL,      1.0,    0, false },
    [STYLE_GUIDE_LABEL]      = { "#b03030", NULL,      NULL,      1.0,  110, false },
    [STYLE_TIMBER_FACE]      = { "#a06000", "#ffd27f", "#ffe2aa", 0.5,    0, false },
    [STYLE_TIMBER_FACE_NEAR] = { "#a06000", "#ffd27f", "#f5b94a", 0.85,   0, false },
    [STYLE_TIMBER_LABEL]     = { "#7a4a00", NULL,      NULL,      1.0,  110, true  },
    [STYLE_HOVER]            = { "#e02080", NULL,      NULL,      1.0,    0, false },
    [STYLE_RC_COLUMN]        = { "#5a5a5a", "#c8c8c8", "#c8c8c8", 0.55,   0, false },
    [STYLE_RC_BEAM]          = { "#4a4a4a", "#9e9e9e", "#9e9e9e", 0.55,   0, false }
};

/*
 * 繪圖後端介面。
 * 座標一律是「視圖內的 mm」；begin_view 告訴後端這個視圖要平移多少。
 */
typedef struct {
    void *ctx;
    void (*begin_view)(void *ctx, Coord tx, Coord ty);
    void (*end_view)(void *ctx);
    void (*rect)(void *ctx, ViewPoint2 min, ViewPoint2 max, DrawStyle style);
    void (*polygon)(void *ctx, const ViewPoint2 *pts, size_t count, DrawStyle style);
    void (*line)(void *ctx, ViewPoint2 a, ViewPoint2 b, DrawStyle style);
    /* rotate_degrees 非 0 時，文字以自己的錨點為中心旋轉（沿直立的邊標字用）。 */
    void (*text)(void *ctx, ViewPoint2 at, DrawStyle style, const char *utf8, int rotate_degrees);
} DrawTarget;

/* 點（視為從房間原點出發的位置向量）在某個軸上的分量。 */
static Coord point_along(Point3 p, Vector3 axis)
{
    return p.x * axis.x + p.y * axis.y + p.z * axis.z;
}

static ViewPoint2 view_project(const ViewFrame *view, Point3 p)
{
    return (ViewPoint2){
        .x = point_along(p, view->right),
        .y = point_along(p, view->down)
    };
}

static void view_bounds_add(ViewBounds *b, ViewPoint2 p)
{
    if (!b->has_point) {
        b->min_x = b->max_x = p.x;
        b->min_y = b->max_y = p.y;
        b->has_point = true;
        return;
    }

    if (p.x < b->min_x) b->min_x = p.x;
    if (p.x > b->max_x) b->max_x = p.x;
    if (p.y < b->min_y) b->min_y = p.y;
    if (p.y > b->max_y) b->max_y = p.y;
}

/* 投影後多邊形的兩倍有向面積；為 0 表示這個形在此視圖中只剩一條線。 */
static Coord view_poly_area2(const ViewPoint2 *pts, size_t count)
{
    Coord area2 = 0;

    for (size_t i = 0; i < count; ++i) {
        size_t j = (i + 1) % count;
        area2 += pts[i].x * pts[j].y - pts[j].x * pts[i].y;
    }

    return area2 < 0 ? -area2 : area2;
}

static Coord view_quad_area2(const ViewPoint2 q[4])
{
    return view_poly_area2(q, 4);
}

/* 點在不在凸四邊形內（含邊上）：對四條邊的有向叉積全部同號。 */
static bool view_quad_contains(const ViewPoint2 q[4], ViewPoint2 p)
{
    int sign = 0;

    for (size_t i = 0; i < 4; ++i) {
        size_t j = (i + 1) % 4;
        Coord cross =
            (q[j].x - q[i].x) * (p.y - q[i].y) -
            (q[j].y - q[i].y) * (p.x - q[i].x);
        int s = cross > 0 ? 1 : cross < 0 ? -1 : 0;

        if (s == 0) {
            continue;
        }

        if (sign == 0) {
            sign = s;
        } else if (s != sign) {
            return false;
        }
    }

    return true;
}

/* 點到線段的平方距離（整數）；線段內部的最近點用整數除法，誤差小於 1mm。 */
static Coord view_dist2_to_segment(ViewPoint2 p, ViewPoint2 a, ViewPoint2 b)
{
    Coord dx = b.x - a.x;
    Coord dy = b.y - a.y;
    Coord len2 = dx * dx + dy * dy;
    Coord px = p.x - a.x;
    Coord py = p.y - a.y;

    if (len2 == 0) {
        return px * px + py * py;
    }

    /* t = (p−a)·(b−a) / len2；先比較分子分母，夾出端點側的情形。 */
    Coord t_num = px * dx + py * dy;

    if (t_num <= 0) {
        return px * px + py * py;
    }

    if (t_num >= len2) {
        Coord qx = p.x - b.x;
        Coord qy = p.y - b.y;
        return qx * qx + qy * qy;
    }

    Coord cx = a.x + dx * t_num / len2;
    Coord cy = a.y + dy * t_num / len2;
    Coord ex = p.x - cx;
    Coord ey = p.y - cy;

    return ex * ex + ey * ey;
}

/*
 * 下面三個 emit 函式：target 為 NULL 時只累積邊界、不輸出。
 * 這樣同一段「走訪場景」的程式碼可以先量尺寸、再真正畫。
 */
static void scene_emit_polygon(
    const DrawTarget *target,
    ViewBounds *bounds,
    const ViewPoint2 *pts,
    size_t count,
    DrawStyle style
)
{
    for (size_t i = 0; i < count; ++i) {
        view_bounds_add(bounds, pts[i]);
    }

    if (target != NULL) {
        target->polygon(target->ctx, pts, count, style);
    }
}

static void scene_emit_line(
    const DrawTarget *target,
    ViewBounds *bounds,
    ViewPoint2 a,
    ViewPoint2 b,
    DrawStyle style
)
{
    view_bounds_add(bounds, a);
    view_bounds_add(bounds, b);

    if (target != NULL) {
        target->line(target->ctx, a, b, style);
    }
}

static void scene_emit_text(
    const DrawTarget *target,
    ViewPoint2 at,
    DrawStyle style,
    const char *text,
    int rotate_degrees
)
{
    if (target != NULL) {
        target->text(target->ctx, at, style, text, rotate_degrees);
    }
}

/* 角材面在單一視圖中的投影結果：面 id、四個畫面座標頂點、視線距離總和。 */
typedef struct {
    TimberFaceId id;
    ViewPoint2 q[4];
    Coord distance4;
} ProjectedFace;

/*
 * 把一支角材的六個面投到某個視圖：退化面跳過，
 * 其餘依視線距離遞減排序（遠的先、近的後）。
 * 繪製與滑鼠拾取共用同一份投影；bounds 為 NULL 時不累積邊界。
 */
static size_t timber_project_faces(
    const Timber *timber,
    const ViewFrame *view,
    ViewBounds *bounds,
    ProjectedFace faces[TIMBER_FACE_COUNT]
)
{
    const Vector3 into = vector_cross(view->right, view->down);
    size_t face_count = 0;

    for (int f = TIMBER_FACE_A0; f < TIMBER_FACE_COUNT; ++f) {
        Quad3 quad;

        if (!timber_get_face_room(timber, (TimberFaceId)f, &quad)) {
            continue;
        }

        /* 直接寫進 faces[face_count]：退化面不遞增計數，下一支面自然覆蓋。 */
        ProjectedFace *pf = &faces[face_count];
        pf->distance4 = 0;

        for (size_t i = 0; i < 4; ++i) {
            pf->q[i] = view_project(view, quad.vertices[i]);
            pf->distance4 += point_along(quad.vertices[i], into);

            if (bounds != NULL) {
                view_bounds_add(bounds, pf->q[i]);
            }
        }

        /* 在此視圖中退化成一條線的面不畫；它的輪廓已在其他面的邊上。 */
        if (view_quad_area2(pf->q) == 0) {
            continue;
        }

        pf->id = (TimberFaceId)f;
        ++face_count;
    }

    /* 依距離遞減排序（插入排序）。 */
    for (size_t i = 1; i < face_count; ++i) {
        for (size_t j = i; j > 0 && faces[j - 1].distance4 < faces[j].distance4; --j) {
            ProjectedFace tmp = faces[j];
            faces[j] = faces[j - 1];
            faces[j - 1] = tmp;
        }
    }

    return face_count;
}

/* AABB 投到某視圖：取三軸區間在視圖右/下向量上的投影區間，組成四點。
 * 退化（面積 0）回 false——那個視圖只看得見一條線，不畫也不供 pick。 */
static bool rc_aabb_project(
    const ViewFrame *view,
    Coord x_lo, Coord x_hi, Coord y_lo, Coord y_hi, Coord z_lo, Coord z_hi,
    ViewPoint2 q[4]
)
{
    const Coord lo[3] = { x_lo, y_lo, z_lo };
    const Coord hi[3] = { x_hi, y_hi, z_hi };
    const Coord rv[3] = { view->right.x, view->right.y, view->right.z };
    const Coord dv[3] = { view->down.x,  view->down.y,  view->down.z  };
    Coord r_lo = 0, r_hi = 0, d_lo = 0, d_hi = 0;

    for (int j = 0; j < 3; ++j) {
        r_lo += rv[j] >= 0 ? rv[j] * lo[j] : rv[j] * hi[j];
        r_hi += rv[j] >= 0 ? rv[j] * hi[j] : rv[j] * lo[j];
        d_lo += dv[j] >= 0 ? dv[j] * lo[j] : dv[j] * hi[j];
        d_hi += dv[j] >= 0 ? dv[j] * hi[j] : dv[j] * lo[j];
    }
    if (r_lo == r_hi || d_lo == d_hi) {
        return false;
    }
    q[0] = (ViewPoint2){ r_lo, d_lo };
    q[1] = (ViewPoint2){ r_hi, d_lo };
    q[2] = (ViewPoint2){ r_hi, d_hi };
    q[3] = (ViewPoint2){ r_lo, d_hi };
    return true;
}

/* 在某一個視圖中畫出整個場景：逐片承載面（輪廓＋孔＋邊＋參考線），最後是角材。 */
static void scene_draw_view(
    const DrawTarget *target,
    ViewBounds *bounds,
    const ViewFrame *view,
    const Scene *scene
)
{
    char label[128];

    for (size_t s = 0; s < scene->placement_count; ++s) {
        const PlacementSurface *surface = &scene->placements[s];
        const SpaceBoundarySurface *boundary =
            scene_placement_boundary(scene, surface);

        /* 1. 有效輪廓（邊界面的外輪廓，或自帶矩形） */
        PolygonLoop2 outline;
        placement_outline(surface, boundary, &outline);

        ViewPoint2 outline_pts[POLY_MAX_VERTICES];
        for (size_t i = 0; i < outline.count; ++i) {
            Point3 p = surface_point_to_room(
                surface, outline.v[i].u, outline.v[i].v, 0);
            outline_pts[i] = view_project(view, p);
        }

        /* 輪廓在此視圖中是不是有面積（否則它只是一條線，邊與參考線的文字就不標）。 */
        bool surface_has_area = view_poly_area2(outline_pts, outline.count) != 0;

        scene_emit_polygon(
            target, bounds, outline_pts, outline.count, STYLE_SURFACE);

        /* 2. 孔：填成紙面色再描邊，視覺上就是輪廓裡的洞。 */
        if (boundary != NULL) {
            for (size_t h = 0; h < boundary->hole_count; ++h) {
                const PolygonLoop2 *hole = &boundary->holes[h];
                ViewPoint2 hole_pts[POLY_MAX_VERTICES];

                for (size_t i = 0; i < hole->count; ++i) {
                    Point3 p = surface_point_to_room(
                        surface, hole->v[i].u, hole->v[i].v, 0);
                    hole_pts[i] = view_project(view, p);
                }

                scene_emit_polygon(
                    target, bounds, hole_pts, hole->count, STYLE_HOLE);
            }
        }

        /* 3. 輪廓的邊：線段 + 編號（FIXED 實線、FREE 橘線；
         *    標籤往邊的外向法線方向推出去） */
        for (size_t i = 0; i < outline.count; ++i) {
            SurfaceSegment2 local;
            Segment3 room;
            SurfacePoint2 uv_normal;

            if (!loop_get_edge_segment(&outline, i, &local) ||
                !surface_get_edge_room_segment(surface, &local, &room) ||
                !loop_edge_outward_normal(&outline, i, &uv_normal)) {
                continue;
            }

            ViewPoint2 a = view_project(view, room.start);
            ViewPoint2 b = view_project(view, room.end);

            scene_emit_line(target, bounds, a, b,
                outline.fixity[i] == EDGE_FIXED ? STYLE_EDGE : STYLE_EDGE_FREE);

            if (!surface_has_area) {
                continue;
            }

            /* 邊的 UV 外向法線 → 房間方向 → 視圖方向。 */
            Point3 n_room = surface_point_to_room(
                surface, uv_normal.u, uv_normal.v, 0);
            Point3 o_room = surface_point_to_room(surface, 0, 0, 0);
            ViewPoint2 n = {
                .x = view_project(view, n_room).x - view_project(view, o_room).x,
                .y = view_project(view, n_room).y - view_project(view, o_room).y
            };

            ViewPoint2 at = {
                .x = (a.x + b.x) / 2 + n.x * 120,
                .y = (a.y + b.y) / 2 + n.y * 120
            };

            snprintf(label, sizeof label, "邊%zu%s",
                     i,
                     outline.fixity[i] == EDGE_FIXED ? "" : "（自由）");

            /* 直立的邊把字轉 90 度，免得長字串撞出畫框。 */
            scene_emit_text(target, at, STYLE_LABEL, label, a.x == b.x ? -90 : 0);
        }

        /* 4. 這片面的參考線：虛線，多邊形下可能被截成多段 */
        for (size_t i = 0; i < scene->guide_count; ++i) {
            const GuideLine *guide = &scene->guides[i];
            SurfaceSegment2 segs[POLY_MAX_VERTICES];
            size_t seg_count;

            if (guide->placement_id != surface->id) {
                continue;
            }

            seg_count = guide_line_get_local_segments(
                surface, boundary, guide, segs, POLY_MAX_VERTICES);

            for (size_t k = 0; k < seg_count; ++k) {
                ViewPoint2 a = view_project(view,
                    surface_point_to_room(surface,
                                          segs[k].start.u, segs[k].start.v, 0));
                ViewPoint2 b = view_project(view,
                    surface_point_to_room(surface,
                                          segs[k].end.u, segs[k].end.v, 0));

                scene_emit_line(target, bounds, a, b, STYLE_GUIDE);

                if (surface_has_area && k == 0) {
                    ViewPoint2 at = { .x = a.x + 40, .y = a.y - 40 };
                    snprintf(label, sizeof label, "參考線%" PRIu32, guide->id);
                    scene_emit_text(target, at, STYLE_GUIDE_LABEL, label, 0);
                }
            }
        }

        /* 5. 這片面的參考網格：每個座標一條線，跟參考線同款虛線。
         *    u 座標線沿 V 走（GUIDE_ALONG_V），v 座標線沿 U 走。 */
        for (size_t g = 0; g < scene->grid_count; ++g) {
            const ReferenceGrid *grid = &scene->grids[g];
            bool labeled = false;

            if (grid->placement_id != surface->id) {
                continue;
            }

            for (int axis = 0; axis < 2; ++axis) {
                const Coord *coords =
                    axis == 0 ? grid->u_coords : grid->v_coords;
                size_t n =
                    axis == 0 ? grid->u_count : grid->v_count;
                GuideDirection dir =
                    axis == 0 ? GUIDE_ALONG_V : GUIDE_ALONG_U;

                for (size_t li = 0; li < n; ++li) {
                    GuideLine temp = {
                        0, surface->id, dir, coords[li]
                    };
                    SurfaceSegment2 segs[POLY_MAX_VERTICES];
                    size_t seg_count = guide_line_get_local_segments(
                        surface, boundary, &temp,
                        segs, POLY_MAX_VERTICES);

                    for (size_t k = 0; k < seg_count; ++k) {
                        ViewPoint2 a = view_project(view,
                            surface_point_to_room(surface,
                                segs[k].start.u, segs[k].start.v, 0));
                        ViewPoint2 b = view_project(view,
                            surface_point_to_room(surface,
                                segs[k].end.u, segs[k].end.v, 0));

                        scene_emit_line(target, bounds, a, b, STYLE_GUIDE);

                        if (surface_has_area && !labeled) {
                            ViewPoint2 at = { .x = a.x + 40, .y = a.y + 20 };
                            snprintf(label, sizeof label,
                                     "格線%" PRIu32, grid->id);
                            scene_emit_text(target, at,
                                            STYLE_GUIDE_LABEL, label, 0);
                            labeled = true;
                        }
                    }
                }
            }
        }
    }

    /* 4. 角材：六個面依距離由遠到近畫，最靠近觀者的面標名 */
    for (size_t t = 0; t < scene->timber_count; ++t) {
        const Timber *timber = &scene->timbers[t];
        ProjectedFace faces[TIMBER_FACE_COUNT];
        size_t face_count =
            timber_project_faces(timber, view, bounds, faces);

        for (size_t i = 0; i < face_count; ++i) {
            bool nearest = i + 1 == face_count;

            scene_emit_polygon(target, bounds, faces[i].q, 4,
                               nearest ? STYLE_TIMBER_FACE_NEAR : STYLE_TIMBER_FACE);

            if (nearest) {
                ViewPoint2 at = { 0, 0 };

                for (size_t k = 0; k < 4; ++k) {
                    at.x += faces[i].q[k].x;
                    at.y += faces[i].q[k].y;
                }

                at.x /= 4;
                at.y /= 4;

                snprintf(label, sizeof label, "角材%" PRIu32 " %s",
                         timber->id, timber_face_short_name(faces[i].id));
                scene_emit_text(target, at, STYLE_TIMBER_LABEL, label, 0);
            }
        }
    }

    /* 5. RC 柱/樑：AABB 在各視圖的投影矩形（B-2，直接畫方塊投影） */
    for (size_t c = 0; c < scene->column_count; ++c) {
        const RcColumn *col = &scene->columns[c];
        ViewPoint2 q[4];

        if (!rc_aabb_project(view, col->x_lo, col->x_hi,
                             col->y_lo, col->y_hi,
                             col->z_lo, col->z_hi, q)) {
            continue;
        }
        scene_emit_polygon(target, bounds, q, 4, STYLE_RC_COLUMN);
        if (target != NULL) {
            ViewPoint2 at = {
                (q[0].x + q[2].x) / 2, (q[0].y + q[2].y) / 2
            };
            snprintf(label, sizeof label, "柱%" PRIu32, col->id);
            scene_emit_text(target, at, STYLE_LABEL, label, 0);
        }
    }
    for (size_t b = 0; b < scene->beam_count; ++b) {
        const RcBeam *bm = &scene->beams[b];
        ViewPoint2 q[4];

        if (!rc_aabb_project(view, bm->x_lo, bm->x_hi,
                             bm->y_lo, bm->y_hi,
                             bm->z_lo, bm->z_hi, q)) {
            continue;
        }
        scene_emit_polygon(target, bounds, q, 4, STYLE_RC_BEAM);
        if (target != NULL) {
            ViewPoint2 at = {
                (q[0].x + q[2].x) / 2, (q[0].y + q[2].y) / 2
            };
            snprintf(label, sizeof label, "樑%" PRIu32, bm->id);
            scene_emit_text(target, at, STYLE_LABEL, label, 0);
        }
    }
}

/* ============================================================
 * 三視圖版面：量測、對齊、平移
 * ============================================================ */

typedef struct {
    ViewBounds bounds[VIEW_COUNT];   /* 各視圖含邊距的範圍（視圖內 mm） */
    Coord tx[VIEW_COUNT];            /* 各視圖搬到版面上的平移量 */
    Coord ty[VIEW_COUNT];
    Coord total_w;
    Coord total_h;
} SceneLayout;

/* 把邊界撐到至少 min_extent 見方（置中），再四周加 pad。 */
static void view_bounds_pad(ViewBounds *b, Coord min_extent, Coord pad, Coord title_strip)
{
    Coord w = b->max_x - b->min_x;
    Coord h = b->max_y - b->min_y;

    if (w < min_extent) {
        Coord grow = (min_extent - w) / 2;
        b->min_x -= grow;
        b->max_x = b->min_x + min_extent;
    }

    if (h < min_extent) {
        Coord grow = (min_extent - h) / 2;
        b->min_y -= grow;
        b->max_y = b->min_y + min_extent;
    }

    b->min_x -= pad;
    b->max_x += pad;
    b->min_y -= pad + title_strip;
    b->max_y += pad;
}

/*
 * 第一趟：用 NULL 後端走訪三次，只量各視圖邊界，
 * 再依三視圖規則對齊並算出平移量。
 */
static bool scene_compute_layout(const Scene *scene, SceneLayout *layout)
{
    const Coord MIN_EXTENT = 600;
    const Coord PAD = 250;
    const Coord TITLE_STRIP = 140;
    const Coord GAP = 300;

    if (scene == NULL || layout == NULL) {
        return false;
    }

    /*
     * 沒有承載面（例如只有游離邊界面的世界）：三視圖本來就畫不出
     * 東西，回一個最小空版面，不要整個拒絕。
     */
    if (scene->placement_count == 0 && scene->column_count == 0 &&
        scene->beam_count == 0) {
        for (size_t v = 0; v < VIEW_COUNT; ++v) {
            layout->bounds[v] = (ViewBounds){ 0 };
            view_bounds_pad(&layout->bounds[v], MIN_EXTENT, PAD, TITLE_STRIP);
        }

        Coord w = MIN_EXTENT + PAD * 2;
        Coord h = MIN_EXTENT + PAD * 2 + TITLE_STRIP;

        layout->tx[VIEW_FRONT] = 0;
        layout->ty[VIEW_FRONT] = 0;
        layout->tx[VIEW_SIDE]  = w + GAP;
        layout->ty[VIEW_SIDE]  = 0;
        layout->tx[VIEW_BOTTOM] = 0;
        layout->ty[VIEW_BOTTOM] = h + GAP;
        layout->total_w = w * 2 + GAP;
        layout->total_h = h * 2 + GAP;
        return true;
    }

    for (size_t v = 0; v < VIEW_COUNT; ++v) {
        layout->bounds[v] = (ViewBounds){ 0 };
        /* scene_draw_view 一定會畫表面的四個角，所以邊界必定有點，不必再檢查。 */
        scene_draw_view(NULL, &layout->bounds[v], &VIEW_FRAMES[v], scene);
        view_bounds_pad(&layout->bounds[v], MIN_EXTENT, PAD, TITLE_STRIP);
    }

    /* 前視圖與仰視圖的畫面 x 都是房間 X；前視圖與側視圖的畫面 y 都是 -Z。 */
    ViewBounds *front = &layout->bounds[VIEW_FRONT];
    ViewBounds *side = &layout->bounds[VIEW_SIDE];
    ViewBounds *bottom = &layout->bounds[VIEW_BOTTOM];

    if (bottom->min_x < front->min_x) front->min_x = bottom->min_x; else bottom->min_x = front->min_x;
    if (bottom->max_x > front->max_x) front->max_x = bottom->max_x; else bottom->max_x = front->max_x;
    if (side->min_y < front->min_y) front->min_y = side->min_y; else side->min_y = front->min_y;
    if (side->max_y > front->max_y) front->max_y = side->max_y; else side->max_y = front->max_y;

    Coord front_w = front->max_x - front->min_x;
    Coord front_h = front->max_y - front->min_y;
    Coord side_w = side->max_x - side->min_x;
    Coord bottom_h = bottom->max_y - bottom->min_y;

    /* 各視圖的平移量：把該視圖的 (min_x, min_y) 搬到版面上的位置。 */
    layout->tx[VIEW_FRONT] = -front->min_x;
    layout->ty[VIEW_FRONT] = -front->min_y;

    layout->tx[VIEW_SIDE] = front_w + GAP - side->min_x;
    layout->ty[VIEW_SIDE] = -side->min_y;

    layout->tx[VIEW_BOTTOM] = -bottom->min_x;
    layout->ty[VIEW_BOTTOM] = front_h + GAP - bottom->min_y;

    layout->total_w = front_w + GAP + side_w;
    layout->total_h = front_h + GAP + bottom_h;

    return true;
}

/* 第二趟：依版面把三個視圖真正畫到後端。 */
static void scene_render(const DrawTarget *target, const SceneLayout *layout, const Scene *scene)
{
    for (size_t v = 0; v < VIEW_COUNT; ++v) {
        const ViewBounds *b = &layout->bounds[v];
        ViewBounds scratch = { 0 };

        target->begin_view(target->ctx, layout->tx[v], layout->ty[v]);

        target->rect(target->ctx,
                     (ViewPoint2){ b->min_x, b->min_y },
                     (ViewPoint2){ b->max_x, b->max_y },
                     STYLE_FRAME);

        target->text(target->ctx,
                     (ViewPoint2){ b->min_x + 60, b->min_y + 110 },
                     STYLE_TITLE, VIEW_FRAMES[v].title, 0);

        scene_draw_view(target, &scratch, &VIEW_FRAMES[v], scene);

        target->end_view(target->ctx);
    }
}

/* ============================================================
 * 命中測試與高亮（互動層共用，SVG 路徑不走這裡）
 * ============================================================ */

/* 游標命中的物件；view 記著是哪個視圖，-1 / COUNT 表示沒有。 */
typedef struct {
    int view;
    int guide;              /* scene->guides 的索引 */
    int timber;             /* scene->timbers 的索引 */
    TimberFaceId face;
    int column;             /* scene->columns 的索引 */
    int beam;               /* scene->beams 的索引 */
} ScenePick;

static const ScenePick SCENE_PICK_NONE = {
    -1, -1, -1, TIMBER_FACE_COUNT, -1, -1
};

static bool scene_pick_equal(ScenePick a, ScenePick b)
{
    return a.view == b.view && a.guide == b.guide &&
           a.timber == b.timber && a.face == b.face &&
           a.column == b.column && a.beam == b.beam;
}

static bool scene_pick_is_none(const ScenePick *p)
{
    return p->guide < 0 && p->timber < 0 && p->column < 0 && p->beam < 0;
}

/*
 * 視圖內的 mm 點反解回表面 (u,v)：投影是線性的，
 * 兩個未知數兩條方程式。det = 0 表示表面在此視圖退化成線；
 * 除不盡表示答案不是整數 mm——兩種情形都拒絕，不猜。
 */


/*
 * 容差反解：給畫布輸入用。滑鼠座標不一定落在整數 uv 上，
 * 四捨五入到最近的整數座標；det == 0（該視圖看不到這面）仍失敗。
 */
static bool view_unproject_on_surface_near(
    const ViewFrame *view,
    const PlacementSurface *surface,
    ViewPoint2 p,
    SurfacePoint2 *out_uv
)
{
    Coord a = vector_dot(surface->frame.axis_u, view->right);
    Coord b = vector_dot(surface->frame.axis_v, view->right);
    Coord c = vector_dot(surface->frame.axis_u, view->down);
    Coord d = vector_dot(surface->frame.axis_v, view->down);
    Coord e = p.x - point_along(surface->frame.origin, view->right);
    Coord f = p.y - point_along(surface->frame.origin, view->down);
    Coord det = a * d - b * c;

    if (det == 0) {
        return false;
    }

    double u_num = (double)(e * d - b * f);
    double v_num = (double)(a * f - e * c);

    out_uv->u = (Coord)llround(u_num / (double)det);
    out_uv->v = (Coord)llround(v_num / (double)det);
    return true;
}

/* 嚴格版：near 版反解後代回驗算，要求恰好整除（拖曳等舊路徑用）。 */
static bool view_unproject_on_surface(
    const ViewFrame *view,
    const PlacementSurface *surface,
    ViewPoint2 p,
    SurfacePoint2 *out_uv
)
{
    if (!view_unproject_on_surface_near(view, surface, p, out_uv)) {
        return false;
    }

    Coord a = vector_dot(surface->frame.axis_u, view->right);
    Coord b = vector_dot(surface->frame.axis_v, view->right);
    Coord c = vector_dot(surface->frame.axis_u, view->down);
    Coord d = vector_dot(surface->frame.axis_v, view->down);
    Coord e = p.x - point_along(surface->frame.origin, view->right);
    Coord f = p.y - point_along(surface->frame.origin, view->down);

    return a * out_uv->u + b * out_uv->v == e &&
           c * out_uv->u + d * out_uv->v == f;
}

/* ---- 畫布編輯用的邊界命中判定 ---- */

typedef enum {
    BOUNDARY_HIT_NONE,
    BOUNDARY_HIT_VERTEX,
    BOUNDARY_HIT_EDGE
} BoundaryHitKind;

typedef struct {
    BoundaryHitKind kind;
    int loop;          /* -1 = 外輪廓,0.. = 孔 index */
    int index;         /* 頂點 index 或邊 index（邊 i = v[i]→v[i+1]） */
    Coord dist;        /* 命中點到目標的距離（mm，對角線用 max 範數） */
} BoundaryHit;

/* 點到軸平行線段的距離（Chebyshev，夠命中判定用）。 */
static Coord dist_point_segment_axis(SurfacePoint2 p, SurfacePoint2 a, SurfacePoint2 b)
{
    Coord du, dv;

    if (a.u == b.u) {
        du = p.u - a.u; if (du < 0) du = -du;
        Coord lo = coord_min(a.v, b.v), hi = coord_max(a.v, b.v);
        dv = p.v < lo ? lo - p.v : p.v > hi ? p.v - hi : 0;
    } else {
        dv = p.v - a.v; if (dv < 0) dv = -dv;
        Coord lo = coord_min(a.u, b.u), hi = coord_max(a.u, b.u);
        du = p.u < lo ? lo - p.u : p.u > hi ? p.u - hi : 0;
    }

    return du > dv ? du : dv;
}

/*
 * 在邊界面上找離 uv 最近的頂點或邊（r = 拾取半徑 mm）。
 * 頂點優先於邊；同類取最近者。所有環（外輪廓 + 孔）一起比。
 */
static bool boundary_pick_point(
    const SpaceBoundarySurface *b,
    SurfacePoint2 uv,
    Coord radius,
    BoundaryHit *out
)
{
    BoundaryHit best = { BOUNDARY_HIT_NONE, -1, -1, radius + 1 };

    if (b == NULL) {
        return false;
    }

    for (int li = -1; li < (int)b->hole_count; ++li) {
        const PolygonLoop2 *loop = li < 0 ? &b->outline : &b->holes[li];

        for (size_t i = 0; i < loop->count; ++i) {
            SurfacePoint2 a = loop->v[i];
            Coord dv = llabs(uv.u - a.u) > llabs(uv.v - a.v)
                ? llabs(uv.u - a.u) : llabs(uv.v - a.v);

            if (dv <= radius && dv < best.dist) {
                best = (BoundaryHit){
                    BOUNDARY_HIT_VERTEX, li, (int)i, dv };
            }
        }

        for (size_t i = 0; i < loop->count; ++i) {
            Coord de = dist_point_segment_axis(
                uv, loop->v[i], loop->v[(i + 1) % loop->count]);

            if (de <= radius && best.kind != BOUNDARY_HIT_VERTEX &&
                de < best.dist) {
                best = (BoundaryHit){ BOUNDARY_HIT_EDGE, li, (int)i, de };
            }
        }
    }

    *out = best;
    return best.kind != BOUNDARY_HIT_NONE;
}

/*
 * 在某一個視圖中，找 view_mm 點命中的物件。
 * 面畫在參考線之上，所以先挑面；同處多個命中取最後畫的（最近的）。
 */
static ScenePick scene_pick_at(
    const Scene *scene,
    const ViewFrame *view,
    int view_index,
    ViewPoint2 p,
    Coord pick_radius
)
{
    ScenePick pick = SCENE_PICK_NONE;
    pick.view = view_index;

    /* RC 柱樑（投影矩形內即命中；後寫的蓋前面的，與繪製順序一致） */
    for (size_t c = 0; c < scene->column_count; ++c) {
        const RcColumn *col = &scene->columns[c];
        ViewPoint2 q[4];

        if (rc_aabb_project(view, col->x_lo, col->x_hi,
                            col->y_lo, col->y_hi,
                            col->z_lo, col->z_hi, q) &&
            view_quad_contains(q, p)) {
            pick.column = (int)c;
        }
    }
    for (size_t b = 0; b < scene->beam_count; ++b) {
        const RcBeam *bm = &scene->beams[b];
        ViewPoint2 q[4];

        if (rc_aabb_project(view, bm->x_lo, bm->x_hi,
                            bm->y_lo, bm->y_hi,
                            bm->z_lo, bm->z_hi, q) &&
            view_quad_contains(q, p)) {
            pick.beam = (int)b;
        }
    }
    if (pick.column >= 0 || pick.beam >= 0) {
        return pick;
    }

    for (size_t t = 0; t < scene->timber_count; ++t) {
        ProjectedFace faces[TIMBER_FACE_COUNT];
        size_t n =
            timber_project_faces(&scene->timbers[t], view, NULL, faces);

        for (size_t i = 0; i < n; ++i) {
            if (view_quad_contains(faces[i].q, p)) {
                pick.timber = (int)t;
                pick.face = faces[i].id;
            }
        }
    }

    if (pick.timber >= 0) {
        return pick;
    }

    Coord best2 = pick_radius * pick_radius;

    for (size_t i = 0; i < scene->guide_count; ++i) {
        const GuideLine *guide = &scene->guides[i];
        const PlacementSurface *surface =
            scene_find_placement(scene, guide->placement_id);
        const SpaceBoundarySurface *boundary;
        SurfaceSegment2 segs[POLY_MAX_VERTICES];
        size_t seg_count;

        if (surface == NULL) {
            continue;
        }

        boundary = scene_placement_boundary(scene, surface);
        seg_count = guide_line_get_local_segments(
            surface, boundary, guide, segs, POLY_MAX_VERTICES);

        for (size_t k = 0; k < seg_count; ++k) {
            ViewPoint2 a = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].start.u, segs[k].start.v, 0));
            ViewPoint2 b = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].end.u, segs[k].end.v, 0));
            Coord d2 = view_dist2_to_segment(p, a, b);

            if (d2 <= best2) {
                best2 = d2;
                pick.guide = (int)i;
            }
        }
    }

    return pick;
}

/* 把命中的物件用 STYLE_HOVER 線框再畫一次；只畫在 pick->view 的視圖。 */
static void scene_draw_pick(
    const DrawTarget *target,
    const SceneLayout *layout,
    const Scene *scene,
    const ScenePick *pick
)
{
    if (pick == NULL || pick->view < 0 || pick->view >= VIEW_COUNT) {
        return;
    }

    int v = pick->view;
    const ViewFrame *view = &VIEW_FRAMES[v];

    target->begin_view(target->ctx, layout->tx[v], layout->ty[v]);

    if (pick->column >= 0 && pick->column < (int)scene->column_count) {
        const RcColumn *col = &scene->columns[pick->column];
        ViewPoint2 q[4];

        if (rc_aabb_project(view, col->x_lo, col->x_hi,
                            col->y_lo, col->y_hi,
                            col->z_lo, col->z_hi, q)) {
            target->polygon(target->ctx, q, 4, STYLE_HOVER);
        }
    }
    if (pick->beam >= 0 && pick->beam < (int)scene->beam_count) {
        const RcBeam *bm = &scene->beams[pick->beam];
        ViewPoint2 q[4];

        if (rc_aabb_project(view, bm->x_lo, bm->x_hi,
                            bm->y_lo, bm->y_hi,
                            bm->z_lo, bm->z_hi, q)) {
            target->polygon(target->ctx, q, 4, STYLE_HOVER);
        }
    }
    if (pick->timber >= 0 && pick->timber < (int)scene->timber_count) {
        ProjectedFace faces[TIMBER_FACE_COUNT];
        size_t n = timber_project_faces(
            &scene->timbers[pick->timber], view, NULL, faces);

        for (size_t i = 0; i < n; ++i) {
            if (faces[i].id == pick->face) {
                target->polygon(target->ctx, faces[i].q, 4, STYLE_HOVER);
            }
        }
    }

    if (pick->guide >= 0 && pick->guide < (int)scene->guide_count) {
        const GuideLine *guide = &scene->guides[pick->guide];
        const PlacementSurface *surface =
            scene_find_placement(scene, guide->placement_id);
        SurfaceSegment2 segs[POLY_MAX_VERTICES];
        size_t seg_count = 0;

        if (surface != NULL) {
            seg_count = guide_line_get_local_segments(
                surface,
                scene_placement_boundary(scene, surface),
                guide, segs, POLY_MAX_VERTICES);
        }

        for (size_t k = 0; k < seg_count; ++k) {
            ViewPoint2 a = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].start.u, segs[k].start.v, 0));
            ViewPoint2 b = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].end.u, segs[k].end.v, 0));
            target->line(target->ctx, a, b, STYLE_HOVER);
        }
    }

    target->end_view(target->ctx);
}

/* ============================================================
 * 後端一：SVG 檔（純 C，只用 stdio）
 * ============================================================ */

static const char *svg_style_class(DrawStyle style)
{
    switch (style) {
        case STYLE_FRAME:            return "frame";
        case STYLE_TITLE:            return "title";
        case STYLE_SURFACE:          return "surface";
        case STYLE_EDGE:             return "edge";
        case STYLE_EDGE_FREE:        return "edge edge-free";
        case STYLE_HOLE:             return "hole";
        case STYLE_LABEL:            return "label";
        case STYLE_GUIDE:            return "guide";
        case STYLE_GUIDE_LABEL:      return "label guide-label";
        case STYLE_TIMBER_FACE:      return "timber-face";
        case STYLE_TIMBER_FACE_NEAR: return "timber-face timber-face-near";
        case STYLE_TIMBER_LABEL:     return "label timber-label";
        case STYLE_HOVER:            return "hover";
        default:                     return "";
    }
}

static void svg_begin_view(void *ctx, Coord tx, Coord ty)
{
    fprintf((FILE *)ctx,
            "<g transform=\"translate(%" PRId64 ",%" PRId64 ")\">\n",
            tx, ty);
}

static void svg_end_view(void *ctx)
{
    fprintf((FILE *)ctx, "</g>\n");
}

static void svg_rect(void *ctx, ViewPoint2 min, ViewPoint2 max, DrawStyle style)
{
    fprintf((FILE *)ctx,
            "<rect class=\"%s\" x=\"%" PRId64 "\" y=\"%" PRId64 "\" "
            "width=\"%" PRId64 "\" height=\"%" PRId64 "\"/>\n",
            svg_style_class(style),
            min.x, min.y, max.x - min.x, max.y - min.y);
}

static void svg_polygon(void *ctx, const ViewPoint2 *pts, size_t count, DrawStyle style)
{
    FILE *out = (FILE *)ctx;

    fprintf(out, "<polygon points=\"");

    for (size_t i = 0; i < count; ++i) {
        fprintf(out, "%" PRId64 ",%" PRId64 "%s",
                pts[i].x, pts[i].y, i + 1 < count ? " " : "");
    }

    fprintf(out, "\" class=\"%s\"/>\n", svg_style_class(style));
}

static void svg_line(void *ctx, ViewPoint2 a, ViewPoint2 b, DrawStyle style)
{
    fprintf((FILE *)ctx,
            "<line x1=\"%" PRId64 "\" y1=\"%" PRId64 "\" "
            "x2=\"%" PRId64 "\" y2=\"%" PRId64 "\" class=\"%s\"/>\n",
            a.x, a.y, b.x, b.y, svg_style_class(style));
}

static void svg_text(void *ctx, ViewPoint2 at, DrawStyle style, const char *utf8, int rotate_degrees)
{
    FILE *out = (FILE *)ctx;

    fprintf(out,
            "<text x=\"%" PRId64 "\" y=\"%" PRId64 "\" class=\"%s\"",
            at.x, at.y, svg_style_class(style));

    if (rotate_degrees != 0) {
        fprintf(out,
                " transform=\"rotate(%d %" PRId64 " %" PRId64 ")\"",
                rotate_degrees, at.x, at.y);
    }

    fprintf(out, ">%s</text>\n", utf8);
}

/* 函式集合固定，只有 ctx 每次呼叫才綁。 */
static const DrawTarget SVG_TARGET = {
    .begin_view = svg_begin_view,
    .end_view = svg_end_view,
    .rect = svg_rect,
    .polygon = svg_polygon,
    .line = svg_line,
    .text = svg_text
};

/* 輸出三視圖 SVG 檔。 */
static bool emit_svg_three_views(const char *path, const Scene *scene, const SceneLayout *layout)
{
    if (path == NULL || scene == NULL || layout == NULL) {
        return false;
    }

    /* 二進位模式：換行固定輸出 LF，不讓 Windows 的文字模式改成 CRLF。 */
    FILE *out = fopen(path, "wb");

    if (out == NULL) {
        return false;
    }

    fprintf(out, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
    fprintf(out,
            "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100%%\" "
            "viewBox=\"0 0 %" PRId64 " %" PRId64 "\">\n",
            layout->total_w, layout->total_h);

    fprintf(out,
            "<style>\n"
            "  polygon, line, rect { vector-effect: non-scaling-stroke; }\n"
            "  .frame { fill: %s; stroke: %s; stroke-width: 1px; }\n"
            "  .title { font: bold %dpx sans-serif; fill: %s; }\n"
            "  .label { font: %dpx sans-serif; fill: %s; text-anchor: middle; dominant-baseline: middle; }\n"
            "  .guide-label { text-anchor: start; fill: %s; }\n"
            "  .timber-label { fill: %s; font-weight: bold; }\n"
            "  .guide-label, .timber-label { paint-order: stroke; stroke: #ffffff; stroke-width: 30px; stroke-linejoin: round; }\n"
            "  .surface { fill: %s; fill-opacity: %g; stroke: %s; stroke-width: 1.5px; }\n"
            "  .hole { fill: %s; stroke: %s; stroke-width: 1.5px; }\n"
            "  .edge { stroke: %s; stroke-width: 1.5px; }\n"
            "  .edge-free { stroke: %s; stroke-width: 1.5px; stroke-dasharray: 30 15; }\n"
            "  .guide { stroke: %s; stroke-width: 1px; stroke-dasharray: 60 30; }\n"
            "  .timber-face { fill: %s; fill-opacity: %g; stroke: %s; stroke-width: 1.5px; }\n"
            "  .timber-face-near { fill-opacity: %g; }\n"
            "</style>\n",
            STYLE_SPEC[STYLE_FRAME].fill, STYLE_SPEC[STYLE_FRAME].line,
            STYLE_SPEC[STYLE_TITLE].text_mm, STYLE_SPEC[STYLE_TITLE].line,
            STYLE_SPEC[STYLE_LABEL].text_mm, STYLE_SPEC[STYLE_LABEL].line,
            STYLE_SPEC[STYLE_GUIDE_LABEL].line,
            STYLE_SPEC[STYLE_TIMBER_LABEL].line,
            STYLE_SPEC[STYLE_SURFACE].fill, STYLE_SPEC[STYLE_SURFACE].svg_fill_opacity,
            STYLE_SPEC[STYLE_SURFACE].line,
            STYLE_SPEC[STYLE_HOLE].fill, STYLE_SPEC[STYLE_HOLE].line,
            STYLE_SPEC[STYLE_EDGE].line,
            STYLE_SPEC[STYLE_EDGE_FREE].line,
            STYLE_SPEC[STYLE_GUIDE].line,
            STYLE_SPEC[STYLE_TIMBER_FACE].fill, STYLE_SPEC[STYLE_TIMBER_FACE].svg_fill_opacity,
            STYLE_SPEC[STYLE_TIMBER_FACE].line,
            STYLE_SPEC[STYLE_TIMBER_FACE_NEAR].svg_fill_opacity);

    DrawTarget target = SVG_TARGET;
    target.ctx = out;

    scene_render(&target, layout, scene);

    fprintf(out, "</svg>\n");

    return fclose(out) == 0;
}

/*
 * 由 __FILE__ 推導原始碼所在目錄，拼出該目錄下某檔名的路徑，
 * 不受執行時工作目錄影響。
 */
static bool path_beside_source(char *buffer, size_t size, const char *name)
{
    const char *source = __FILE__;
    const char *backslash = strrchr(source, '\\');
    const char *slash = strrchr(source, '/');
    const char *last = backslash > slash ? backslash : slash;
    size_t dir_len = last != NULL ? (size_t)(last - source + 1) : 0;

    int n = snprintf(buffer, size, "%.*s%s",
                     (int)dir_len, source, name);

    return n > 0 && (size_t)n < size;
}

/*
 * 互動視窗會呼叫下方的「場景文字檔輸入層」。
 * C 要先用後宣告，所以在這裡先給前置宣告；
 * 定義與說明都在下方那一節。
 */
#define SCENE_MAX_LINE    2048
#define SCENE_MAX_TOKENS  160

/*
 * 一份場景 = 若干空間邊界面（純 2D 輪廓）+ 承載面（3D 嵌入）
 * + 參考線 + 角材 + 空間。
 * 上限都是常數，資料就放在呼叫者給的 World 裡，不做動態配置——
 * World 是 POD，整份 memcpy 就是交易用的快照。
 */
#define WORLD_MAX_BOUNDARIES  8
#define WORLD_MAX_PLACEMENTS  8
#define WORLD_MAX_GUIDES      16
#define WORLD_MAX_GRIDS       8
#define WORLD_MAX_TIMBERS     64
#define WORLD_MAX_SPACES      4
#define WORLD_MAX_RC          32
#define WORLD_MAX_CANVAS_POS  (WORLD_MAX_BOUNDARIES + WORLD_MAX_PLACEMENTS + WORLD_MAX_SPACES + WORLD_MAX_RC * 2)

/* 一個空間最多八片邊界成員，至少兩片（子集也合法：只檢查彼此一致）。 */
#define SPACE_MAX_MEMBERS 8

/*
 * 角材的放置錨點：哪片承載面、表面上的哪一點、怎麼來的。
 * 重宣告交易要靠它重驗角材，所以放法也要留著。
 *
 * 凍結語意：uv 與 timbers[i].length 在 place 當下凍結，
 * 之後 grid / guide / 邊界變動只重驗、不重算。
 */

typedef enum {
    ANCHOR_AT,          /* at u v：明寫錨點 */
    ANCHOR_AT_GUIDES,   /* at-guides 線1 線2：交點凍結 */
    ANCHOR_AT_GRID,     /* at-grid 網id 軸 索引：中心線對齊格線 */
    ANCHOR_AT_EDGE      /* at-edge e3 / h1e2：貼邊 */
} AnchorKind;

typedef enum {
    SPAN_EXPLICIT,      /* timber id L A B：長度是輸入 */
    SPAN_AUTO           /* timber id A B：長度是推導結果 */
} SpanMode;

typedef struct {
    SurfaceId placement_id;
    SurfacePoint2 uv;
    int anchor_kind;        /* AnchorKind */
    int span_mode;          /* SpanMode */
    int length_direction;   /* SurfaceDirection */
    int depth_side;         /* SurfaceDepthSide */

    /* 參照來源：place 之後只供追溯與重驗，不再用來重算。 */
    uint32_t ref_grid;      /* ANCHOR_AT_GRID：網格 id */
    int ref_grid_axis;      /* 0 = u 座標集合，1 = v 座標集合 */
    int ref_grid_index;
    int ref_hole;           /* ANCHOR_AT_EDGE：-1 外輪廓，否則孔 index */
    int ref_edge;           /* 邊 index */
    bool has_through;
    Coord through;          /* 區間選擇器（長度軸上的座標） */
} TimberAnchor;

/*
 * 畫布座標：物件在無限畫布上的擺放位置。
 * 純展示中繼資料——不參與任何幾何推導，只跟著 dump/讀檔走。
 */
typedef enum {
    CANVAS_POS_BOUNDARY = 0,   /* 面卡：以邊界面 id 為鍵 */
    CANVAS_POS_PLACEMENT,      /* 自帶矩形面卡：以承載面 id 為鍵 */
    CANVAS_POS_SPACE,          /* 空間卡：以空間 id 為鍵 */
    CANVAS_POS_COLUMN,         /* 柱卡：以柱 id 為鍵 */
    CANVAS_POS_BEAM            /* 樑卡：以樑 id 為鍵 */
} CanvasPosKind;

typedef struct {
    int kind;                  /* CanvasPosKind */
    uint32_t id;
    Coord x, y;                /* 畫布座標（展示用，非幾何） */
} CanvasPos;

typedef struct World {
    SpaceBoundarySurface boundaries[WORLD_MAX_BOUNDARIES];
    size_t boundary_count;

    PlacementSurface placements[WORLD_MAX_PLACEMENTS];
    size_t placement_count;

    GuideLine guides[WORLD_MAX_GUIDES];
    size_t guide_count;

    ReferenceGrid grids[WORLD_MAX_GRIDS];
    size_t grid_count;

    Timber timbers[WORLD_MAX_TIMBERS];

    /* 與 timbers 同索引：放置用的錨點。 */
    TimberAnchor anchors[WORLD_MAX_TIMBERS];
    size_t timber_count;

    Space spaces[WORLD_MAX_SPACES];
    size_t space_count;

    RcColumn columns[WORLD_MAX_RC];
    size_t column_count;

    RcBeam beams[WORLD_MAX_RC];
    size_t beam_count;

    CanvasPos canvas_pos[WORLD_MAX_CANVAS_POS];
    size_t canvas_pos_count;
} World;

static Scene scene_from_world(const World *world);
static const PlacementSurface *world_find_placement(
    const World *world, uint32_t id);
static const SpaceBoundarySurface *world_find_boundary(
    const World *world, uint32_t id);
static const Space *world_find_space(const World *world, uint32_t id);
static const RcColumn *world_find_column(const World *world, uint32_t id);
static const RcBeam *world_find_beam(const World *world, uint32_t id);
static const char *scene_last_error(void);
static int split_tokens(char *line, char *tokens[], int max_tokens);
static bool apply_scene_line(
    const char *path, int line_no, char *tokens[], int count, World *world);

/* ---- 復原/重做：World 是 POD，memcpy 即快照 ----
 * undo/redo 是 session 層指令，不進 .scene 檔格式；
 * 由互動入口（interactive_apply_line / web feed_line）攔截。
 */
static void scene_error(const char *path, int line_no, const char *message);

#define HISTORY_MAX 32
static World g_hist_undo[HISTORY_MAX];
static int   g_hist_undo_n;
static World g_hist_redo[HISTORY_MAX];
static int   g_hist_redo_n;

/* 變更成功前呼叫：把現況壓入 undo 疊並清掉 redo。 */
static void history_record(const World *w)
{
    if (g_hist_undo_n >= HISTORY_MAX) {
        memmove(&g_hist_undo[0], &g_hist_undo[1],
                sizeof(World) * (HISTORY_MAX - 1));
        --g_hist_undo_n;
    }
    g_hist_undo[g_hist_undo_n++] = *w;
    g_hist_redo_n = 0;
}

/* 檔案載入/啟動載入後呼叫：那些不是使用者操作，不該被 undo。 */
static void history_clear(void)
{
    g_hist_undo_n = 0;
    g_hist_redo_n = 0;
}

/* apply 失敗時呼叫：剛記的快照作廢（世界沒變）。 */
static void history_unrecord(void)
{
    if (g_hist_undo_n > 0) {
        --g_hist_undo_n;
    }
}

static bool history_undo(World *w)
{
    if (g_hist_undo_n <= 0) {
        return false;
    }
    if (g_hist_redo_n >= HISTORY_MAX) {
        memmove(&g_hist_redo[0], &g_hist_redo[1],
                sizeof(World) * (HISTORY_MAX - 1));
        --g_hist_redo_n;
    }
    g_hist_redo[g_hist_redo_n++] = *w;
    *w = g_hist_undo[--g_hist_undo_n];
    return true;
}

static bool history_redo(World *w)
{
    if (g_hist_redo_n <= 0) {
        return false;
    }
    if (g_hist_undo_n >= HISTORY_MAX) {
        memmove(&g_hist_undo[0], &g_hist_undo[1],
                sizeof(World) * (HISTORY_MAX - 1));
        --g_hist_undo_n;
    }
    g_hist_undo[g_hist_undo_n++] = *w;
    *w = g_hist_redo[--g_hist_redo_n];
    return true;
}

/* 互動入口共用：undo/redo 攔截 + 變更前記快照（失敗自動取消）。
 * 回傳值同 apply_scene_line。 */
static bool apply_interactive_tokens(
    const char *path, int line_no, char *tokens[], int count, World *world)
{
    if (count == 1 && strcmp(tokens[0], "undo") == 0) {
        if (history_undo(world)) {
            return true;
        }
        scene_error(path, line_no, "沒有可復原的操作");
        return false;
    }
    if (count == 1 && strcmp(tokens[0], "redo") == 0) {
        if (history_redo(world)) {
            return true;
        }
        scene_error(path, line_no, "沒有可重做的操作");
        return false;
    }
    /* canvas-pos 是展示中繼資料：不記歷史也不清 redo,
     * 否則 renderObjects 的自動排位會把 undo 掉的擺放寫回來。 */
    if (strcmp(tokens[0], "canvas-pos") == 0) {
        return apply_scene_line(path, line_no, tokens, count, world);
    }

    history_record(world);
    if (apply_scene_line(path, line_no, tokens, count, world)) {
        return true;
    }
    history_unrecord();
    return false;
}

static bool parse_scene_file(const char *path, World *out_world);

/* ============================================================
 * 後端二：Windows 視窗（只靠作業系統自帶的 user32 / gdi32）
 *
 * 三個觀念：
 *   1. 事件迴圈：GetMessage 一則一則取出作業系統送來的事件。
 *   2. 回呼函式：gdi_window_proc 是交給作業系統、由它來呼叫的函式。
 *   3. 只在 WM_PAINT 裡畫：作業系統說「該重畫了」才畫。
 * ============================================================ */
#ifdef _WIN32

#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commdlg.h>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "comdlg32.lib")

/*
 * GDI 物件快取：筆、刷、字型建立是系統呼叫，比整個幾何計算還貴。
 * DrawStyle 是封閉 enum，直接以它為索引；字型以 (px, weight, rotate)
 * 為鍵。所有權屬於 GdiApp，視窗關閉時統一釋放。
 */
#define GDI_FONT_CACHE_MAX 16

typedef struct {
    HPEN pens[STYLE_COUNT];         /* NULL = 尚未建立 */
    HBRUSH brushes[STYLE_COUNT];
    struct {
        int px;
        int weight;
        int rotate10;
        HFONT font;
    } fonts[GDI_FONT_CACHE_MAX];
    size_t font_count;
} GdiObjectCache;

/* 畫到視窗時的狀態：mm → 像素的比例與偏移。 */
typedef struct {
    HDC dc;
    double scale;       /* 像素 / mm */
    double origin_x;    /* 版面 (0,0) 在視窗裡的像素位置 */
    double origin_y;
    Coord tx;           /* 目前視圖的平移量（mm） */
    Coord ty;
    GdiObjectCache *objects;    /* 筆刷與字型快取，由擁有者注入 */
} GdiContext;

/* 「#rrggbb」轉 COLORREF。 */
static COLORREF gdi_color(const char *hex)
{
    unsigned v = (unsigned)strtoul(hex + 1, NULL, 16);
    return RGB((v >> 16) & 0xffu, (v >> 8) & 0xffu, v & 0xffu);
}

static POINT gdi_to_pixel(const GdiContext *g, ViewPoint2 p)
{
    POINT out;
    out.x = (LONG)(g->origin_x + (double)(p.x + g->tx) * g->scale + 0.5);
    out.y = (LONG)(g->origin_y + (double)(p.y + g->ty) * g->scale + 0.5);
    return out;
}

static void gdi_begin_view(void *ctx, Coord tx, Coord ty)
{
    GdiContext *g = (GdiContext *)ctx;
    g->tx = tx;
    g->ty = ty;
}

static void gdi_end_view(void *ctx)
{
    (void)ctx;
}

/* 原始碼是 UTF-8，Win32 的寬字元 API 要 UTF-16；回傳含結尾的字元數。 */
static int utf8_to_wide(const char *utf8, WCHAR *out, int cap)
{
    return MultiByteToWideChar(CP_UTF8, 0, utf8, -1, out, cap);
}

/*
 * 每種角色對應一組筆與刷。顏色取自 STYLE_SPEC；線寬與虛線是 GDI 的渲染機制。
 * 物件由 cache 持有：第一次用到才建立，之後每幀只是查表。
 * style 超出 enum 範圍時退回當場建立、scope 標記自管，由呼叫端刪除。
 */
static void gdi_select_style(
    GdiObjectCache *cache, DrawStyle style,
    HPEN *pen, HBRUSH *brush, bool *owned
)
{
    const char *fill = NULL;
    COLORREF line_color = RGB(0, 0, 0);
    int pen_px = 1;
    int pen_kind = PS_SOLID;

    if (style >= 0 && style < STYLE_COUNT) {
        const StyleSpec *spec = &STYLE_SPEC[style];
        line_color = gdi_color(spec->line);
        fill = spec->gdi_fill != NULL ? spec->gdi_fill : spec->fill;
    }

    switch (style) {
        case STYLE_SURFACE:
        case STYLE_EDGE:
        case STYLE_TIMBER_FACE:
        case STYLE_TIMBER_FACE_NEAR:
            pen_px = 2;
            break;

        case STYLE_HOVER:
            pen_px = 3;
            break;

        case STYLE_GUIDE:
            pen_kind = PS_DASH;
            break;

        default:
            break;
    }

    if (cache != NULL && style >= 0 && style < STYLE_COUNT) {
        if (cache->pens[style] == NULL) {
            cache->pens[style] = CreatePen(pen_kind, pen_px, line_color);
        }
        *pen = cache->pens[style];

        if (fill != NULL) {
            if (cache->brushes[style] == NULL) {
                cache->brushes[style] = CreateSolidBrush(gdi_color(fill));
            }
            *brush = cache->brushes[style];
        } else {
            *brush = (HBRUSH)GetStockObject(NULL_BRUSH);
        }
        *owned = false;
        return;
    }

    *pen = CreatePen(pen_kind, pen_px, line_color);
    *brush = fill != NULL
        ? CreateSolidBrush(gdi_color(fill))
        : (HBRUSH)GetStockObject(NULL_BRUSH);
    *owned = true;
}

static void gdi_release_style(HPEN pen, HBRUSH brush, bool owned)
{
    if (!owned) {
        return;
    }

    DeleteObject(pen);

    if (brush != (HBRUSH)GetStockObject(NULL_BRUSH)) {
        DeleteObject(brush);
    }
}

/* 釋放快取裡全部 GDI 物件；視窗關閉或量測冷路徑時呼叫。 */
static void gdi_cache_release(GdiObjectCache *cache)
{
    for (int i = 0; i < STYLE_COUNT; ++i) {
        if (cache->pens[i] != NULL) {
            DeleteObject(cache->pens[i]);
            cache->pens[i] = NULL;
        }
        if (cache->brushes[i] != NULL) {
            DeleteObject(cache->brushes[i]);
            cache->brushes[i] = NULL;
        }
    }
    for (size_t i = 0; i < cache->font_count; ++i) {
        DeleteObject(cache->fonts[i].font);
    }
    cache->font_count = 0;
}

/*
 * 畫一個圖形 = 選筆刷進 DC、畫、還原並釋放。
 * 三個 gdi_ 繪圖函式共用這段骨架；線條雖然用不到刷子，
 * 選進 NULL_BRUSH 無害，統一寫法比分支省事。
 */
typedef struct {
    HPEN pen;
    HBRUSH brush;
    HGDIOBJ old_pen;
    HGDIOBJ old_brush;
    bool owned;         /* true = 未進快取（越界 style），用完要刪 */
} GdiStyleScope;

static void gdi_style_begin(GdiContext *g, DrawStyle style, GdiStyleScope *scope)
{
    gdi_select_style(g->objects, style, &scope->pen, &scope->brush, &scope->owned);
    scope->old_pen = SelectObject(g->dc, scope->pen);
    scope->old_brush = SelectObject(g->dc, scope->brush);
}

static void gdi_style_end(GdiContext *g, const GdiStyleScope *scope)
{
    SelectObject(g->dc, scope->old_pen);
    SelectObject(g->dc, scope->old_brush);
    gdi_release_style(scope->pen, scope->brush, scope->owned);
}

static void gdi_rect(void *ctx, ViewPoint2 min, ViewPoint2 max, DrawStyle style)
{
    GdiContext *g = (GdiContext *)ctx;
    GdiStyleScope scope;
    POINT a = gdi_to_pixel(g, min);
    POINT b = gdi_to_pixel(g, max);

    gdi_style_begin(g, style, &scope);
    Rectangle(g->dc, a.x, a.y, b.x, b.y);
    gdi_style_end(g, &scope);
}

static void gdi_polygon(void *ctx, const ViewPoint2 *pts, size_t count, DrawStyle style)
{
    GdiContext *g = (GdiContext *)ctx;
    GdiStyleScope scope;
    POINT pxy[POLY_MAX_VERTICES];

    for (size_t i = 0; i < count; ++i) {
        pxy[i] = gdi_to_pixel(g, pts[i]);
    }

    gdi_style_begin(g, style, &scope);
    Polygon(g->dc, pxy, (int)count);
    gdi_style_end(g, &scope);
}

static void gdi_line(void *ctx, ViewPoint2 a, ViewPoint2 b, DrawStyle style)
{
    GdiContext *g = (GdiContext *)ctx;
    GdiStyleScope scope;
    POINT pa = gdi_to_pixel(g, a);
    POINT pb = gdi_to_pixel(g, b);

    gdi_style_begin(g, style, &scope);
    MoveToEx(g->dc, pa.x, pa.y, NULL);
    LineTo(g->dc, pb.x, pb.y);
    gdi_style_end(g, &scope);
}

/*
 * 文字：原始碼是 UTF-8，GDI 的寬字元 API 要 UTF-16，先轉碼。
 * 字級以 mm 定義（與 SVG 相同），乘上比例變像素，但不小於 10 px。
 */
static void gdi_text(void *ctx, ViewPoint2 at, DrawStyle style, const char *utf8, int rotate_degrees)
{
    GdiContext *g = (GdiContext *)ctx;
    WCHAR wide[256];
    int wide_len = utf8_to_wide(utf8, wide, 256);

    if (wide_len <= 1) {
        return;
    }

    const StyleSpec *spec =
        style >= 0 && style < STYLE_COUNT ? &STYLE_SPEC[style] : NULL;

    double size_mm = spec != NULL && spec->text_mm > 0 ? spec->text_mm : 110;
    COLORREF color = spec != NULL ? gdi_color(spec->line) : RGB(51, 51, 51);
    int weight = spec != NULL && spec->bold ? FW_BOLD : FW_NORMAL;
    UINT align =
        style == STYLE_TITLE || style == STYLE_GUIDE_LABEL
            ? TA_LEFT | TA_BASELINE
            : TA_CENTER | TA_BASELINE;

    int px = (int)(size_mm * g->scale + 0.5);

    if (px < 10) {
        px = 10;
    }

    /* lfEscapement 以 0.1 度為單位、逆時針為正；SVG 的 rotate(-90) 在 y 向下的畫面裡也是逆時針。 */
    int rotate10 = -rotate_degrees * 10;
    HFONT font = NULL;
    bool font_owned = false;

    if (g->objects != NULL) {
        GdiObjectCache *cache = g->objects;

        for (size_t i = 0; i < cache->font_count; ++i) {
            if (cache->fonts[i].px == px &&
                cache->fonts[i].weight == weight &&
                cache->fonts[i].rotate10 == rotate10) {
                font = cache->fonts[i].font;
                break;
            }
        }

        if (font == NULL) {
            font = CreateFontW(
                -px, 0, rotate10, rotate10, weight,
                FALSE, FALSE, FALSE, DEFAULT_CHARSET,
                OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
                DEFAULT_PITCH | FF_DONTCARE, L"Microsoft JhengHei"
            );

            if (font != NULL && cache->font_count < GDI_FONT_CACHE_MAX) {
                cache->fonts[cache->font_count].px = px;
                cache->fonts[cache->font_count].weight = weight;
                cache->fonts[cache->font_count].rotate10 = rotate10;
                cache->fonts[cache->font_count].font = font;
                ++cache->font_count;
            } else {
                font_owned = true;
            }
        }
    } else {
        font = CreateFontW(
            -px, 0, rotate10, rotate10, weight,
            FALSE, FALSE, FALSE, DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_DONTCARE, L"Microsoft JhengHei"
        );
        font_owned = true;
    }

    HGDIOBJ old_font = SelectObject(g->dc, font);
    UINT old_align = SetTextAlign(g->dc, align);
    COLORREF old_color = SetTextColor(g->dc, color);
    int old_mode = SetBkMode(g->dc, TRANSPARENT);

    POINT p = gdi_to_pixel(g, at);

    /* SVG 的 label 是 dominant-baseline: middle，基線要往下移約 0.35 個字高。 */
    if (align & TA_CENTER) {
        if (rotate_degrees == 0) {
            p.y += (LONG)(px * 0.35);
        } else {
            p.x += (LONG)(px * 0.35);
        }
    }

    TextOutW(g->dc, p.x, p.y, wide, wide_len - 1);

    SetBkMode(g->dc, old_mode);
    SetTextColor(g->dc, old_color);
    SetTextAlign(g->dc, old_align);
    SelectObject(g->dc, old_font);

    if (font_owned && font != NULL) {
        DeleteObject(font);
    }
}

/* 視窗底部輸入列的高度（px）：狀態列 + 指令輸入 + 按鈕。 */
#define GDI_INPUT_BAR_H 64

#define IDC_INPUT_EDIT   101
#define IDC_BTN_EXAMPLE  102
#define IDC_BTN_CLEAR    103
#define IDC_STATUS_LABEL 104
#define IDC_HOVER_LABEL  105

/* 功能表項目；載入範例／清空直接重用按鈕的 ID。 */
#define IDM_OPEN_SCENE   201
#define IDM_ZOOM_RESET   202
#define IDM_EXIT         203
#define IDM_UNDO         204
#define IDM_REDO         205

/* 畫布工具與工作面選擇；IDM_WORK_BASE+i = 第 i 個承載面。 */
#define IDM_TOOL_VIEW    210
#define IDM_TOOL_RECT    211
#define IDM_TOOL_POLY    212
#define IDM_TOOL_HOLE    213
#define IDM_TOOL_EDIT    214
#define IDM_EXPORT_SCENE 215
#define IDM_WORK_BASE    300   /* 300.. 承載面；398/399 = 新水平面 z=0/2500 */
#define IDM_WORK_NEW_Z0  398
#define IDM_WORK_NEW_Z1  399

/* 畫布工具：檢視之外的模式全部只產生 DSL 行（見下方畫布層）。 */
typedef enum {
    TOOL_VIEW = 0,
    TOOL_RECT,          /* 拉矩形建面 */
    TOOL_POLY,          /* 逐點畫正交多邊形建面 */
    TOOL_HOLE,          /* 拉矩形挖孔（併進工作面的邊界） */
    TOOL_EDIT           /* 拖頂點／邊編輯工作面的邊界 */
} CanvasTool;

static const char *axis_word(Vector3 axis);
static void world_dump_dsl(const World *world, FILE *out);
static char *fmt_loop(char *p, char *end, const PolygonLoop2 *loop);

/* 輸入列的 Enter 送給主視窗的自訂訊息。 */
#define WM_APP_APPLY_INPUT  (WM_APP + 1)

/*
 * 視窗的全部狀態。world 是場景唯一定義，UI 只能經由
 * domain 動詞（apply_scene_line / guide_line_move）改它；
 * scene 與 layout 由 world 推導，每次變動後重建。
 * hover/selected/drag 是互動態，不是場景內容。
 */
typedef struct {
    World *world;
    Scene scene;
    SceneLayout layout;
    bool has_layout;
    ScenePick hover;
    ScenePick selected;
    int drag_guide;         /* 拖曳中的 guides 索引，-1 = 沒有 */
    int drag_view;
    bool panning;           /* 中鍵平移中 */
    int pan_last_x;
    int pan_last_y;
    double zoom;            /* 滾輪縮放倍率，1.0 = fit-to-window */
    double pan_x;           /* 像素空間的平移（疊在 fit 平移之後） */
    double pan_y;
    HWND input_edit;
    HWND status_label;
    HWND hover_label;
    int input_line_no;

    /* 畫布工具態（TOOL_*）；互動態，不是場景內容。 */
    int canvas_tool;
    uint32_t work_placement;    /* 工作面 placement id；0 = 新水平面 */
    Coord work_plane_z;
    uint32_t edit_boundary;     /* TOOL_EDIT 作用的邊界面 id */
    int draw_view;              /* 進行中繪製所在視圖；-1 = 無 */
    SurfacePoint2 draw_pts[POLY_MAX_VERTICES];
    size_t draw_count;
    bool draw_down;
    SurfacePoint2 draw_start, draw_cur;
    BoundaryHit edit_hit;
    bool edit_down;
    SpaceBoundarySurface edit_work;   /* 編輯中的邊界副本 */
    HMENU surf_menu;

    /* 離屏緩衝與 GDI 物件快取：尺寸不變就整幀重用，不再每幀重建。 */
    HDC mem_dc;
    HBITMAP mem_bitmap;
    HGDIOBJ mem_stock;    /* mem_dc 建來時內含的 1×1 位圖，刪前選回去用 */
    int mem_w;
    int mem_h;
    GdiObjectCache objects;
} GdiApp;

/* 畫布層定義在下方；app_refresh／gdi_paint 要先看到原型。 */
static void gdi_draw_canvas_preview(HDC dc, RECT draw, GdiApp *app);
static void gdi_rebuild_surf_menu(GdiApp *app);
static void gdi_enter_edit(GdiApp *app);

/* 函式集合固定，只有 ctx 每次重畫才綁。 */
static const DrawTarget GDI_TARGET = {
    .begin_view = gdi_begin_view,
    .end_view = gdi_end_view,
    .rect = gdi_rect,
    .polygon = gdi_polygon,
    .line = gdi_line,
    .text = gdi_text
};

/*
 * 畫圖範圍 → mm→px 變換：整個版面等比縮放置中，四周留 16 px。
 * paint 與滑鼠命中測試共用，保證「看到的」與「點到的」是同一份數學。
 */
static void gdi_frame_transform(
    RECT draw, const SceneLayout *layout,
    double *out_scale, double *out_ox, double *out_oy
)
{
    const double MARGIN = 16.0;
    double cw = (double)(draw.right - draw.left);
    double ch = (double)(draw.bottom - draw.top);
    double sx = (cw - 2 * MARGIN) / (double)layout->total_w;
    double sy = (ch - 2 * MARGIN) / (double)layout->total_h;
    double scale = sx < sy ? sx : sy;

    *out_scale = scale;
    *out_ox = (cw - (double)layout->total_w * scale) / 2;
    *out_oy = (ch - (double)layout->total_h * scale) / 2;
}

/*
 * fit 之上再疊使用者視圖態：zoom 是倍率，pan 是像素位移。
 * 繪製與滑鼠命中測試都只走這裡——「看到的=點到的」靠共用守住。
 */
static void gdi_view_transform(
    const GdiApp *app, RECT draw,
    double *out_scale, double *out_ox, double *out_oy
)
{
    double scale, ox, oy;

    gdi_frame_transform(draw, &app->layout, &scale, &ox, &oy);

    *out_scale = scale * app->zoom;
    *out_ox = ox * app->zoom + app->pan_x;
    *out_oy = oy * app->zoom + app->pan_y;
}

static void gdi_paint(HDC dc, RECT client, GdiApp *app)
{
    /* 底部輸入列的背景；控制項蓋不到的部分由這裡鋪底色。 */
    RECT draw = client;
    RECT bar = client;

    draw.bottom -= GDI_INPUT_BAR_H;
    bar.top = draw.bottom;
    FillRect(dc, &bar, GetSysColorBrush(COLOR_BTNFACE));

    if (!app->has_layout) {
        return;
    }

    GdiContext g = {
        .dc = dc, .tx = 0, .ty = 0, .objects = &app->objects
    };

    gdi_view_transform(app, draw, &g.scale, &g.origin_x, &g.origin_y);

    if (g.scale <= 0) {
        return;
    }

    DrawTarget target = GDI_TARGET;
    target.ctx = &g;

    scene_render(&target, &app->layout, &app->scene);

    /* 命中高亮疊在最上層：點選的優先，沒有才用 hover 的。 */
    const ScenePick *show =
        !scene_pick_is_none(&app->selected) ? &app->selected :
        !scene_pick_is_none(&app->hover)    ? &app->hover : NULL;

    if (show != NULL) {
        scene_draw_pick(&target, &app->layout, &app->scene, show);
    }

    /* 畫布工具的進行中預覽（矩形／多邊形／編輯手柄），壓在最上層。 */
    gdi_draw_canvas_preview(dc, draw, app);
}

/* 釋放 GdiApp 持有的全部 GDI 資源：離屏緩衝 + 物件快取。 */
static void gdi_app_release_objects(GdiApp *app)
{
    if (app->mem_dc != NULL) {
        if (app->mem_bitmap != NULL) {
            /* 選中的物件不能刪：先把建來時的 stock 位圖選回去。 */
            SelectObject(app->mem_dc, app->mem_stock);
            DeleteObject(app->mem_bitmap);
            app->mem_bitmap = NULL;
        }
        DeleteDC(app->mem_dc);
        app->mem_dc = NULL;
    }
    app->mem_stock = NULL;
    app->mem_w = 0;
    app->mem_h = 0;
    gdi_cache_release(&app->objects);
}

/* World 變動後：重建 Scene、重算版面、清命中態、重畫。 */
static void app_refresh(GdiApp *app, HWND window)
{
    app->scene = scene_from_world(app->world);
    app->has_layout =
        app->scene.placement_count > 0 &&
        scene_compute_layout(&app->scene, &app->layout);
    app->hover = SCENE_PICK_NONE;
    app->selected = SCENE_PICK_NONE;
    app->drag_guide = -1;
    gdi_rebuild_surf_menu(app);
    /* 工作面被刪掉時回退到第一片；編輯工具的目標也跟著重取。 */
    if (app->work_placement != 0 &&
        world_find_placement(app->world, app->work_placement) == NULL) {
        app->work_placement = app->world->placement_count > 0
            ? app->world->placements[0].id : 0;
    }
    if (app->canvas_tool == TOOL_EDIT) {
        gdi_enter_edit(app);
    }
    InvalidateRect(window, NULL, FALSE);
}

static void gdi_set_status(GdiApp *app, const char *utf8)
{
    WCHAR wide[512];
    utf8_to_wide(utf8, wide, 512);
    SetWindowTextW(app->status_label, wide);
}

/* hover 列：即時顯示游標下的命中物；與指令回饋的 status 列分開。 */
static void gdi_set_hover(GdiApp *app, const char *utf8)
{
    WCHAR wide[256];
    utf8_to_wide(utf8, wide, 256);
    SetWindowTextW(app->hover_label, wide);
}

/* 命中物 → 一行描述；無命中時寫入空字串。 */
static void gdi_describe_pick(const GdiApp *app, const ScenePick *p, char *buf, size_t cap)
{
    buf[0] = '\0';

    if (p == NULL || scene_pick_is_none(p)) {
        return;
    }

    if (p->timber >= 0 && p->timber < (int)app->scene.timber_count) {
        snprintf(buf, cap, "角材%" PRIu32 " %s",
                 app->scene.timbers[p->timber].id,
                 timber_face_name(p->face));
        return;
    }

    if (p->guide >= 0 && p->guide < (int)app->world->guide_count) {
        const GuideLine *gd = &app->world->guides[p->guide];
        snprintf(buf, cap, "參考線%" PRIu32 " 沿%s offset=%" PRId64,
                 gd->id,
                 gd->direction == GUIDE_ALONG_U ? "U" : "V",
                 (int64_t)gd->offset);
    }
}

/* 定義在下方；gdi_load_scene_file 要先看到原型。 */
static void interactive_apply_line(GdiApp *app, HWND window, const char *text);

/*
 * 載入一份場景檔：先 reset，再走 parse_scene_file——
 * 按鈕、功能表與拖曳一樣，UI 只是另一種輸入法。
 */
static void gdi_load_scene_file(GdiApp *app, HWND window, const char *path, const char *name)
{
    /* 快照式載入：失敗世界不動，成功則整步可 undo。 */
    World before = *app->world;
    memset(app->world, 0, sizeof *app->world);

    if (parse_scene_file(path, app->world)) {
        history_record(&before);
        app_refresh(app, window);
        char msg[320];
        snprintf(msg, sizeof msg, "✓ 已載入 %s", name);
        gdi_set_status(app, msg);
    } else {
        *app->world = before;   /* 解析失敗：還原，不留半殘世界 */
        char msg[320];
        snprintf(msg, sizeof msg, "✗ %s", scene_last_error());
        gdi_set_status(app, msg);
    }
}

/* 開檔對話框；OFN_NOCHANGEDIR 避免動到 path_beside_source 依賴的工作目錄。 */
static void gdi_open_scene_dialog(GdiApp *app, HWND window)
{
    WCHAR wpath[512] = L"";
    char path[512 * 4];
    OPENFILENAMEW ofn = { 0 };

    ofn.lStructSize = sizeof ofn;
    ofn.hwndOwner = window;
    ofn.lpstrFile = wpath;
    ofn.nMaxFile = 512;
    ofn.lpstrFilter = L"場景檔 (*.scene)\0*.scene\0所有檔案\0*.*\0";
    ofn.lpstrTitle = L"開啟場景檔";
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR;

    if (!GetOpenFileNameW(&ofn)) {
        return;
    }

    if (WideCharToMultiByte(CP_UTF8, 0, wpath, -1,
                            path, sizeof path, NULL, NULL) <= 1) {
        return;
    }

    gdi_load_scene_file(app, window, path, path);
}

/*
 * 一行輸入 = 一行場景指令，與場景檔走同一條路：
 * 切 token → apply_scene_line → 守門員。接受就刷新畫面，
 * 拒絕就把解析層給的理由顯示在狀態列。
 */

static void interactive_apply_line(GdiApp *app, HWND window, const char *text)
{
    char line[SCENE_MAX_LINE];

    snprintf(line, sizeof line, "%s", text);

    /* # 之後是註解，與場景檔同規則。 */
    char *hash = strchr(line, '#');

    if (hash != NULL) {
        *hash = '\0';
    }

    char *tokens[SCENE_MAX_TOKENS];
    int count = split_tokens(line, tokens, SCENE_MAX_TOKENS);

    if (count <= 0) {
        return;
    }

    ++app->input_line_no;

    if (apply_interactive_tokens("<輸入>", app->input_line_no, tokens, count, app->world)) {
        app_refresh(app, window);
        gdi_set_status(app, "✓ 已套用");
        SetWindowTextW(app->input_edit, L"");
    } else {
        char msg[320];
        snprintf(msg, sizeof msg, "✗ %s", scene_last_error());
        gdi_set_status(app, msg);
    }
}

/* 像素 → 視圖編號 + 視圖內 mm；游標不在任何視圖內時回 false。 */
static bool gdi_screen_to_view(
    HWND window, const GdiApp *app, int px, int py,
    int *out_view, ViewPoint2 *out_mm, Coord *out_pick_radius
)
{
    RECT client;
    GetClientRect(window, &client);
    client.bottom -= GDI_INPUT_BAR_H;

    double scale, ox, oy;
    gdi_view_transform(app, client, &scale, &ox, &oy);

    if (scale <= 0) {
        return false;
    }

    for (int v = 0; v < VIEW_COUNT; ++v) {
        const ViewBounds *b = &app->layout.bounds[v];
        double x0 = ox + (double)(b->min_x + app->layout.tx[v]) * scale;
        double x1 = ox + (double)(b->max_x + app->layout.tx[v]) * scale;
        double y0 = oy + (double)(b->min_y + app->layout.ty[v]) * scale;
        double y1 = oy + (double)(b->max_y + app->layout.ty[v]) * scale;

        if ((double)px < x0 || (double)px > x1 ||
            (double)py < y0 || (double)py > y1) {
            continue;
        }

        out_mm->x = (Coord)(((double)px - ox) / scale - (double)app->layout.tx[v] + 0.5);
        out_mm->y = (Coord)(((double)py - oy) / scale - (double)app->layout.ty[v] + 0.5);
        *out_view = v;
        *out_pick_radius = (Coord)(8.0 / scale + 0.5);
        return true;
    }

    return false;
}

/* 單行 EDIT 不報 Enter；子類化攔下來，轉成給主視窗的自訂訊息。 */
static WNDPROC g_edit_orig_proc = NULL;

static LRESULT CALLBACK gdi_input_proc(
    HWND edit, UINT msg, WPARAM wparam, LPARAM lparam
)
{
    if (msg == WM_KEYDOWN && wparam == VK_RETURN) {
        SendMessageW(GetParent(edit), WM_APP_APPLY_INPUT, 0, 0);
        return 0;
    }

    if (msg == WM_CHAR && wparam == VK_RETURN) {
        return 0;   /* 吃掉 Enter 的嗶聲 */
    }

    /* 滾輪訊息跟隨鍵盤焦點：EDIT 有焦點時轉發給主視窗縮放。 */
    if (msg == WM_MOUSEWHEEL) {
        return SendMessageW(GetParent(edit), msg, wparam, lparam);
    }

    return CallWindowProcW(g_edit_orig_proc, edit, msg, wparam, lparam);
}

/* 依目前 client 尺寸重排底部輸入列的控制項。 */
static void gdi_layout_input_bar(HWND window, GdiApp *app)
{
    RECT client;
    GetClientRect(window, &client);

    int w = client.right - client.left;
    int h = client.bottom - client.top;

    /* 頂列左邊是指令回饋（錯誤訊息較長），右邊是 hover 命中物。 */
    MoveWindow(app->status_label,
               8, h - GDI_INPUT_BAR_H + 4, (w - 16) * 3 / 5, 20, TRUE);
    MoveWindow(app->hover_label,
               8 + (w - 16) * 3 / 5 + 8, h - GDI_INPUT_BAR_H + 4,
               (w - 16) * 2 / 5 - 8, 20, TRUE);
    MoveWindow(app->input_edit,
               8, h - 34, w - 176, 26, TRUE);
    MoveWindow(GetDlgItem(window, IDC_BTN_EXAMPLE),
               w - 162, h - 34, 76, 26, TRUE);
    MoveWindow(GetDlgItem(window, IDC_BTN_CLEAR),
               w - 80, h - 34, 72, 26, TRUE);
}

/* ============================================================
 * 畫布工具（GDI）：在畫布中建立／編輯空間邊界面
 *
 * 與 web 版同一份規則：畫布動作只是「產生 DSL 行」丟進
 * interactive_apply_line——世界狀態仍是唯一事實來源，
 * 公理守門員照舊把關，拒絕就留在原狀。
 * ============================================================ */

/* 工作面的承載面：既有 placement，或堆疊上的臨時水平面（新平面）。 */
static const PlacementSurface *canvas_work_surface(
    const GdiApp *app, PlacementSurface *tmp
)
{
    if (app->work_placement == 0) {
        memset(tmp, 0, sizeof *tmp);
        tmp->frame.origin = (Point3){ 0, 0, app->work_plane_z };
        tmp->frame.axis_u = (Vector3){ 1, 0, 0 };
        tmp->frame.axis_v = (Vector3){ 0, 1, 0 };
        tmp->frame.normal = (Vector3){ 0, 0, 1 };
        return tmp;
    }
    return world_find_placement(app->world, app->work_placement);
}

/* 目前最大 boundary/placement id + 1（畫布產生新物件用）。 */
static uint32_t canvas_next_id(const GdiApp *app)
{
    uint32_t m = 0;
    for (size_t i = 0; i < app->world->boundary_count; ++i)
        if (app->world->boundaries[i].id > m) m = app->world->boundaries[i].id;
    for (size_t i = 0; i < app->world->placement_count; ++i)
        if (app->world->placements[i].id > m) m = app->world->placements[i].id;
    return m + 1;
}



/* 在選定平面上建新 surface（boundary + placement 合體一行）。 */
static void canvas_emit_new_surface(
    GdiApp *app, HWND window,
    const PlacementSurface *plane,
    const SurfacePoint2 *pts, size_t count
)
{
    char line[SCENE_MAX_LINE];
    char *p = line, *end = line + sizeof line;

    p += snprintf(p, (size_t)(end - p),
                  "surface %u origin %lld %lld %lld u %s v %s outline ",
                  (unsigned)canvas_next_id(app),
                  (long long)plane->frame.origin.x,
                  (long long)plane->frame.origin.y,
                  (long long)plane->frame.origin.z,
                  axis_word(plane->frame.axis_u),
                  axis_word(plane->frame.axis_v));
    for (size_t i = 0; i < count; ++i) {
        p += snprintf(p, (size_t)(end - p), "%s%lld,%lld",
                      i ? " " : "", (long long)pts[i].u, (long long)pts[i].v);
    }
    interactive_apply_line(app, window, line);
}

/* 邊界面整體重宣告（編輯拖曳、挖孔都走這條；交易式，失敗回退）。 */
static void canvas_emit_boundary(
    GdiApp *app, HWND window, const SpaceBoundarySurface *b
)
{
    char line[SCENE_MAX_LINE];
    char *p = line, *end = line + sizeof line;

    p += snprintf(p, (size_t)(end - p),
                  "boundary %u outline ", (unsigned)b->id);
    p = fmt_loop(p, end, &b->outline);
    for (size_t h = 0; h < b->hole_count; ++h) {
        p += snprintf(p, (size_t)(end - p), " hole ");
        p = fmt_loop(p, end, &b->holes[h]);
    }
    interactive_apply_line(app, window, line);
}

/* 畫布互動態歸零（工具切換、Esc、場景載入時呼叫）。 */
static void canvas_reset_drawing(GdiApp *app)
{
    app->draw_count = 0;
    app->draw_down = false;
    app->edit_down = false;
    app->draw_view = -1;
}

/* 進入編輯工具：鎖定工作面的邊界面。 */
static void gdi_enter_edit(GdiApp *app)
{
    const PlacementSurface *ws =
        world_find_placement(app->world, app->work_placement);
    const SpaceBoundarySurface *b =
        ws != NULL ? world_find_boundary(app->world, ws->boundary_id) : NULL;
    app->edit_boundary = b != NULL ? b->id : 0;
    app->edit_down = false;
    app->draw_view = -1;
}

/* 頂點拉角：鄰邊保持正交（鄰點共享座標跟著動）——與 web 版同一套。 */
static void canvas_apply_vertex_edit(PolygonLoop2 *loop, size_t i, SurfacePoint2 uv)
{
    size_t n = loop->count;
    SurfacePoint2 *prev = &loop->v[(i + n - 1) % n];
    SurfacePoint2 *next = &loop->v[(i + 1) % n];
    SurfacePoint2 *cur = &loop->v[i];

    if (prev->v == cur->v) prev->v = uv.v; else prev->u = uv.u;
    if (next->u == cur->u) next->u = uv.u; else next->v = uv.v;
    *cur = uv;
}
static void canvas_apply_edge_edit(PolygonLoop2 *loop, size_t i, SurfacePoint2 uv)
{
    SurfacePoint2 *a = &loop->v[i], *b = &loop->v[(i + 1) % loop->count];
    if (a->v == b->v) { a->v = b->v = uv.v; } else { a->u = b->u = uv.u; }
}

/* 預覽：uv 多邊形畫到某視圖（紅虛線 + 頂點手柄）。 */
static void gdi_preview_loop(
    HDC dc, const GdiContext *g, const ViewFrame *view,
    const PlacementSurface *plane, const PolygonLoop2 *loop, bool handles
)
{
    POINT pxy[POLY_MAX_VERTICES];

    for (size_t i = 0; i < loop->count; ++i) {
        ViewPoint2 q = view_project(view,
            surface_point_to_room(plane, loop->v[i].u, loop->v[i].v, 0));
        pxy[i] = gdi_to_pixel(g, q);
    }
    Polygon(dc, pxy, (int)loop->count);
    if (handles) {
        for (size_t i = 0; i < loop->count; ++i) {
            RECT hr = { pxy[i].x - 4, pxy[i].y - 4,
                        pxy[i].x + 4, pxy[i].y + 4 };
            FrameRect(dc, &hr, (HBRUSH)GetStockObject(BLACK_BRUSH));
        }
    }
}

/* 進行中的矩形／多邊形／編輯中邊界，壓在圖層最上。 */
static void gdi_draw_canvas_preview(HDC dc, RECT draw, GdiApp *app)
{
    if (app->canvas_tool == TOOL_VIEW) {
        return;
    }

    PlacementSurface tmp;
    const PlacementSurface *plane = canvas_work_surface(app, &tmp);
    if (plane == NULL) {
        return;
    }

    HPEN pen = CreatePen(PS_DASH, 1, RGB(0xc0, 0x39, 0x2b));
    HGDIOBJ old_pen = SelectObject(dc, pen);
    HGDIOBJ old_brush = SelectObject(dc, GetStockObject(NULL_BRUSH));

    GdiContext g = {
        .dc = dc, .tx = 0, .ty = 0, .objects = &app->objects
    };
    gdi_view_transform(app, draw, &g.scale, &g.origin_x, &g.origin_y);

    if (app->canvas_tool == TOOL_EDIT && app->edit_boundary != 0) {
        /* 手柄在所有看得見這面的視圖都畫（編輯不限起始視圖）。 */
        const SpaceBoundarySurface *b = app->edit_down
            ? &app->edit_work
            : world_find_boundary(app->world, app->edit_boundary);
        for (int v = 0; v < VIEW_COUNT && b != NULL; ++v) {
            SurfacePoint2 probe;
            if (!view_unproject_on_surface_near(&VIEW_FRAMES[v], plane,
                    (ViewPoint2){ 0, 0 }, &probe)) {
                continue;   /* det = 0：此視圖看這面是線 */
            }
            g.tx = app->layout.tx[v];
            g.ty = app->layout.ty[v];
            for (int li = -1; li < (int)b->hole_count; ++li) {
                gdi_preview_loop(dc, &g, &VIEW_FRAMES[v], plane,
                    li < 0 ? &b->outline : &b->holes[li], true);
            }
        }
    } else if (app->draw_view >= 0) {
        int v = app->draw_view;
        g.tx = app->layout.tx[v];
        g.ty = app->layout.ty[v];

        if (app->draw_down) {
            Coord u0 = coord_min(app->draw_start.u, app->draw_cur.u);
            Coord u1 = coord_max(app->draw_start.u, app->draw_cur.u);
            Coord v0 = coord_min(app->draw_start.v, app->draw_cur.v);
            Coord v1 = coord_max(app->draw_start.v, app->draw_cur.v);
            PolygonLoop2 r = { 0 };
            r.v[0] = (SurfacePoint2){ u0, v0 };
            r.v[1] = (SurfacePoint2){ u1, v0 };
            r.v[2] = (SurfacePoint2){ u1, v1 };
            r.v[3] = (SurfacePoint2){ u0, v1 };
            r.count = 4;
            gdi_preview_loop(dc, &g, &VIEW_FRAMES[v], plane, &r, false);
        } else if (app->canvas_tool == TOOL_POLY && app->draw_count > 0) {
            POINT pxy[POLY_MAX_VERTICES];
            size_t n = app->draw_count;
            for (size_t i = 0; i < n; ++i) {
                ViewPoint2 q = view_project(&VIEW_FRAMES[v],
                    surface_point_to_room(plane,
                        app->draw_pts[i].u, app->draw_pts[i].v, 0));
                pxy[i] = gdi_to_pixel(&g, q);
            }
            ViewPoint2 q = view_project(&VIEW_FRAMES[v],
                surface_point_to_room(plane,
                    app->draw_cur.u, app->draw_cur.v, 0));
            pxy[n] = gdi_to_pixel(&g, q);
            Polyline(dc, pxy, (int)n + 1);
        }
    }

    SelectObject(dc, old_brush);
    SelectObject(dc, old_pen);
    DeleteObject(pen);
}

/* ---- 畫布滑鼠流程 ---- */
static void gdi_canvas_down(
    GdiApp *app, HWND window, int v, ViewPoint2 mm, Coord radius
)
{
    PlacementSurface tmp;
    const PlacementSurface *plane = canvas_work_surface(app, &tmp);
    SurfacePoint2 uv;

    if (plane == NULL ||
        !view_unproject_on_surface_near(&VIEW_FRAMES[v], plane, mm, &uv)) {
        gdi_set_status(app, "這個視圖看不到工作面（換視圖或換工作面）");
        return;
    }

    if (app->canvas_tool == TOOL_RECT || app->canvas_tool == TOOL_HOLE) {
        app->draw_down = true;
        app->draw_view = v;
        app->draw_start = app->draw_cur = uv;
        SetCapture(window);
    } else if (app->canvas_tool == TOOL_POLY) {
        /* 軸鎖：新點與上一點水平或垂直對齊（取主軸）。 */
        if (app->draw_count > 0) {
            SurfacePoint2 p = app->draw_pts[app->draw_count - 1];
            Coord du = uv.u - p.u, dv = uv.v - p.v;
            if (du < 0) du = -du;
            if (dv < 0) dv = -dv;
            if (du >= dv) uv.v = p.v; else uv.u = p.u;
        }
        /* 點回起點附近 = 閉合送出。 */
        if (app->draw_count >= 3) {
            SurfacePoint2 p0 = app->draw_pts[0];
            Coord du = uv.u - p0.u, dv = uv.v - p0.v;
            if (du < 0) du = -du;
            if (dv < 0) dv = -dv;
            if (du <= radius && dv <= radius) {
                canvas_emit_new_surface(
                    app, window, plane, app->draw_pts, app->draw_count);
                canvas_reset_drawing(app);
                return;
            }
        }
        if (app->draw_count < POLY_MAX_VERTICES) {
            app->draw_pts[app->draw_count++] = uv;
            app->draw_cur = uv;
            app->draw_view = v;
        }
    } else if (app->canvas_tool == TOOL_EDIT && app->edit_boundary != 0) {
        const SpaceBoundarySurface *b =
            world_find_boundary(app->world, app->edit_boundary);
        BoundaryHit hit;
        if (b == NULL || !boundary_pick_point(b, uv, radius, &hit)) {
            return;
        }
        app->edit_work = *b;
        app->edit_hit = hit;
        app->edit_down = true;
        app->draw_view = v;
        SetCapture(window);
    }
    InvalidateRect(window, NULL, FALSE);
}

static void gdi_canvas_move(GdiApp *app, HWND window, int v, ViewPoint2 mm)
{
    if (app->draw_view >= 0 && v != app->draw_view) {
        return;   /* 進行中的繪製鎖在起始視圖 */
    }

    PlacementSurface tmp;
    const PlacementSurface *plane = canvas_work_surface(app, &tmp);
    SurfacePoint2 uv;

    if (plane == NULL ||
        !view_unproject_on_surface_near(&VIEW_FRAMES[v], plane, mm, &uv)) {
        return;
    }

    if (app->draw_down) {
        app->draw_cur = uv;
    } else if (app->canvas_tool == TOOL_POLY && app->draw_count > 0) {
        SurfacePoint2 lock = uv;
        SurfacePoint2 p = app->draw_pts[app->draw_count - 1];
        Coord du = uv.u - p.u, dv = uv.v - p.v;
        if (du < 0) du = -du;
        if (dv < 0) dv = -dv;
        if (du >= dv) lock.v = p.v; else lock.u = p.u;
        app->draw_cur = lock;
    } else if (app->edit_down) {
        PolygonLoop2 *loop = app->edit_hit.loop < 0
            ? &app->edit_work.outline
            : &app->edit_work.holes[app->edit_hit.loop];
        if (app->edit_hit.kind == BOUNDARY_HIT_VERTEX) {
            canvas_apply_vertex_edit(loop, (size_t)app->edit_hit.index, uv);
        } else {
            canvas_apply_edge_edit(loop, (size_t)app->edit_hit.index, uv);
        }
    } else {
        return;
    }
    InvalidateRect(window, NULL, FALSE);
}

static void gdi_canvas_up(GdiApp *app, HWND window, int v, ViewPoint2 mm)
{
    if (app->draw_down) {
        app->draw_down = false;
        ReleaseCapture();
        if (v == app->draw_view) {
            PlacementSurface tmp;
            const PlacementSurface *plane = canvas_work_surface(app, &tmp);
            SurfacePoint2 uv;
            if (plane != NULL &&
                view_unproject_on_surface_near(
                    &VIEW_FRAMES[v], plane, mm, &uv) &&
                uv.u != app->draw_start.u && uv.v != app->draw_start.v) {
                Coord u0 = coord_min(app->draw_start.u, uv.u);
                Coord u1 = coord_max(app->draw_start.u, uv.u);
                Coord v0 = coord_min(app->draw_start.v, uv.v);
                Coord v1 = coord_max(app->draw_start.v, uv.v);
                SurfacePoint2 pts[4] = {
                    { u0, v0 }, { u1, v0 }, { u1, v1 }, { u0, v1 }
                };
                if (app->canvas_tool == TOOL_RECT) {
                    canvas_emit_new_surface(app, window, plane, pts, 4);
                } else {
                    /* 挖孔：矩形當新孔併進工作面的邊界，整體重宣告。 */
                    const PlacementSurface *ws =
                        world_find_placement(app->world, app->work_placement);
                    const SpaceBoundarySurface *b = ws != NULL
                        ? world_find_boundary(app->world, ws->boundary_id)
                        : NULL;
                    if (b == NULL || b->hole_count >= POLY_MAX_HOLES) {
                        gdi_set_status(app, "✗ 挖孔要有邊界面的工作面（且孔數未滿）");
                    } else {
                        SpaceBoundarySurface nb = *b;
                        PolygonLoop2 *h = &nb.holes[nb.hole_count++];
                        memcpy(h->v, pts, sizeof pts);
                        h->count = 4;
                        for (int i = 0; i < 4; ++i) h->fixity[i] = EDGE_FIXED;
                        canvas_emit_boundary(app, window, &nb);
                    }
                }
            }
        }
        app->draw_view = -1;
        InvalidateRect(window, NULL, FALSE);
    } else if (app->edit_down) {
        app->edit_down = false;
        ReleaseCapture();
        canvas_emit_boundary(app, window, &app->edit_work);
        InvalidateRect(window, NULL, FALSE);
    }
}

/* 工作面子功能表：refresh 時依 world 重建（承載面增減會反映在這裡）。 */
static void gdi_rebuild_surf_menu(GdiApp *app)
{
    if (app->surf_menu == NULL) {
        return;
    }
    while (GetMenuItemCount(app->surf_menu) > 0) {
        DeleteMenu(app->surf_menu, 0, MF_BYPOSITION);
    }
    for (size_t i = 0; i < app->world->placement_count; ++i) {
        const PlacementSurface *p = &app->world->placements[i];
        WCHAR label[96];
        swprintf(label, 96, L"面 %u（z=%lld%hs）",
                 (unsigned)p->id, (long long)p->frame.origin.z,
                 p->boundary_id != 0 ? " 有邊界" : " 無邊界");
        AppendMenuW(app->surf_menu, MF_STRING,
                    (UINT_PTR)(IDM_WORK_BASE + i), label);
    }
    if (app->world->placement_count > 0) {
        AppendMenuW(app->surf_menu, MF_SEPARATOR, 0, NULL);
    }
    AppendMenuW(app->surf_menu, MF_STRING, IDM_WORK_NEW_Z0, L"＋新水平面 z=0");
    AppendMenuW(app->surf_menu, MF_STRING, IDM_WORK_NEW_Z1, L"＋新水平面 z=2500");
}

static LRESULT CALLBACK gdi_window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam)
{
    GdiApp *app = (GdiApp *)GetWindowLongPtrW(window, GWLP_USERDATA);

    switch (message) {
        case WM_CREATE: {
            /* CreateWindow 的最後一個參數會從這裡拿回來，掛在視窗上。 */
            CREATESTRUCTW *cs = (CREATESTRUCTW *)lparam;
            app = (GdiApp *)cs->lpCreateParams;
            SetWindowLongPtrW(window, GWLP_USERDATA, (LONG_PTR)app);

            /* 底部輸入列：狀態列 + hover 列 + 指令輸入 + 範例／清空按鈕。 */
            app->status_label = CreateWindowW(
                L"STATIC", L"", WS_CHILD | WS_VISIBLE | SS_LEFT,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_STATUS_LABEL, cs->hInstance, NULL);

            app->hover_label = CreateWindowW(
                L"STATIC", L"", WS_CHILD | WS_VISIBLE | SS_LEFT,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_HOVER_LABEL, cs->hInstance, NULL);

            app->input_edit = CreateWindowW(
                L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_INPUT_EDIT, cs->hInstance, NULL);

            CreateWindowW(
                L"BUTTON", L"載入範例",
                WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_BTN_EXAMPLE, cs->hInstance, NULL);

            CreateWindowW(
                L"BUTTON", L"清空",
                WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_BTN_CLEAR, cs->hInstance, NULL);

            HFONT gui_font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
            SendMessageW(app->status_label, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(app->hover_label, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(app->input_edit, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(GetDlgItem(window, IDC_BTN_EXAMPLE),
                         WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(GetDlgItem(window, IDC_BTN_CLEAR),
                         WM_SETFONT, (WPARAM)gui_font, TRUE);

            g_edit_orig_proc = (WNDPROC)SetWindowLongPtrW(
                app->input_edit, GWLP_WNDPROC, (LONG_PTR)gdi_input_proc);

            gdi_layout_input_bar(window, app);
            gdi_set_status(app,
                "指令：surface｜edge｜guide｜timber｜place｜move 線id offset｜room｜reset");
            return 0;
        }

        case WM_SIZE:
            if (app != NULL) {
                gdi_layout_input_bar(window, app);
            }
            return 0;

        case WM_ERASEBKGND:
            /* 背景由 WM_PAINT 的離屏緩衝一起畫，這裡不清，避免閃爍。 */
            return 1;

        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC dc = BeginPaint(window, &ps);
            RECT client;
            GetClientRect(window, &client);

            if (app == NULL) {
                /* 視窗還沒綁上 app（WM_CREATE 之前）：鋪白底就好。 */
                FillRect(dc, &client, (HBRUSH)GetStockObject(WHITE_BRUSH));
                EndPaint(window, &ps);
                return 0;
            }

            /*
             * 離屏緩衝：先畫到記憶體位圖，再一次貼到視窗。
             * DC 建一次重用；位圖只在尺寸變了才重建——
             * GDI 物件建立是系統呼叫，比整個幾何繪製還貴。
             */
            if (app->mem_dc == NULL) {
                app->mem_dc = CreateCompatibleDC(dc);
            }
            if (app->mem_dc == NULL) {
                EndPaint(window, &ps);
                return 0;
            }
            if (app->mem_w != client.right || app->mem_h != client.bottom) {
                if (app->mem_bitmap != NULL) {
                    SelectObject(app->mem_dc, app->mem_stock);
                    DeleteObject(app->mem_bitmap);
                }
                app->mem_bitmap =
                    CreateCompatibleBitmap(dc, client.right, client.bottom);
                app->mem_w = client.right;
                app->mem_h = client.bottom;
            }
            if (app->mem_bitmap == NULL) {
                EndPaint(window, &ps);
                return 0;
            }

            HDC mem = app->mem_dc;
            HGDIOBJ old_bitmap = SelectObject(mem, app->mem_bitmap);

            /* 第一次選入時，回傳值是 DC 內建的 stock 位圖，留著拆緩衝用。 */
            if (app->mem_stock == NULL) {
                app->mem_stock = old_bitmap;
            }

            FillRect(mem, &client, (HBRUSH)GetStockObject(WHITE_BRUSH));
            gdi_paint(mem, client, app);
            BitBlt(dc, 0, 0, client.right, client.bottom, mem, 0, 0, SRCCOPY);

            /* 位圖留在 DC 裡沒關係；下次先比對尺寸再決定重用或重建。 */
            SelectObject(mem, old_bitmap);
            EndPaint(window, &ps);
            return 0;
        }

        case WM_APP_APPLY_INPUT: {
            WCHAR wbuf[SCENE_MAX_LINE];
            char utf8[SCENE_MAX_LINE * 4];

            if (app == NULL) {
                return 0;
            }

            GetWindowTextW(app->input_edit, wbuf, SCENE_MAX_LINE);

            if (WideCharToMultiByte(CP_UTF8, 0, wbuf, -1,
                                    utf8, sizeof utf8, NULL, NULL) <= 1) {
                return 0;
            }

            interactive_apply_line(app, window, utf8);
            return 0;
        }

        case WM_COMMAND:
            if (app == NULL) {
                return 0;
            }

            if (LOWORD(wparam) == IDC_BTN_CLEAR) {
                interactive_apply_line(app, window, "reset");
                return 0;
            }

            if (LOWORD(wparam) == IDC_BTN_EXAMPLE) {
                char path[512];

                if (path_beside_source(path, sizeof path, "room_a.scene")) {
                    gdi_load_scene_file(app, window, path, "範例 room_a.scene");
                } else {
                    gdi_set_status(app, "✗ 找不到 room_a.scene");
                }
                return 0;
            }

            if (LOWORD(wparam) == IDM_OPEN_SCENE) {
                gdi_open_scene_dialog(app, window);
                return 0;
            }

            if (LOWORD(wparam) == IDM_ZOOM_RESET) {
                app->zoom = 1.0;
                app->pan_x = 0.0;
                app->pan_y = 0.0;
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            if (LOWORD(wparam) == IDM_UNDO) {
                interactive_apply_line(app, window, "undo");
                return 0;
            }

            if (LOWORD(wparam) == IDM_REDO) {
                interactive_apply_line(app, window, "redo");
                return 0;
            }

            if (LOWORD(wparam) == IDM_EXIT) {
                DestroyWindow(window);
                return 0;
            }

            if (LOWORD(wparam) >= IDM_TOOL_VIEW &&
                LOWORD(wparam) <= IDM_TOOL_EDIT) {
                app->canvas_tool = (int)LOWORD(wparam) - IDM_TOOL_VIEW;
                canvas_reset_drawing(app);
                CheckMenuRadioItem(GetMenu(window), IDM_TOOL_VIEW,
                                   IDM_TOOL_EDIT, LOWORD(wparam),
                                   MF_BYCOMMAND);
                if (app->canvas_tool == TOOL_EDIT) {
                    gdi_enter_edit(app);
                }
                {
                    static const char *hint[] = {
                        "", "在工作面上拉出一個矩形",
                        "逐點點出正交多邊形（點回起點閉合、Esc 取消）",
                        "在工作面邊界內拉一個矩形當孔",
                        "拖頂點拉角、拖邊平移；放開即重宣告"
                    };
                    gdi_set_status(app, hint[app->canvas_tool]);
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            if (LOWORD(wparam) >= IDM_WORK_BASE &&
                LOWORD(wparam) < IDM_WORK_NEW_Z0 &&
                (size_t)(LOWORD(wparam) - IDM_WORK_BASE) <
                    app->world->placement_count) {
                app->work_placement =
                    app->world->placements[LOWORD(wparam) - IDM_WORK_BASE].id;
                canvas_reset_drawing(app);
                if (app->canvas_tool == TOOL_EDIT) gdi_enter_edit(app);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            if (LOWORD(wparam) == IDM_WORK_NEW_Z0 ||
                LOWORD(wparam) == IDM_WORK_NEW_Z1) {
                app->work_placement = 0;
                app->work_plane_z =
                    LOWORD(wparam) == IDM_WORK_NEW_Z0 ? 0 : 2500;
                canvas_reset_drawing(app);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            if (LOWORD(wparam) == IDM_EXPORT_SCENE) {
                WCHAR wpath[512] = L"canvas_export.scene";
                char path[512 * 4];
                OPENFILENAMEW ofn = { 0 };

                ofn.lStructSize = sizeof ofn;
                ofn.hwndOwner = window;
                ofn.lpstrFile = wpath;
                ofn.nMaxFile = 512;
                ofn.lpstrFilter = L"場景檔 (*.scene) *.scene 所有檔案 *.* ";
                ofn.lpstrTitle = L"匯出場景檔";
                ofn.Flags = OFN_OVERWRITEPROMPT | OFN_NOCHANGEDIR;
                ofn.lpstrDefExt = L"scene";

                if (GetSaveFileNameW(&ofn) &&
                    WideCharToMultiByte(CP_UTF8, 0, wpath, -1,
                                        path, sizeof path, NULL, NULL) > 1) {
                    FILE *f = fopen(path, "wb");
                    if (f != NULL) {
                        world_dump_dsl(app->world, f);
                        fclose(f);
                        gdi_set_status(app, "✓ 已匯出 .scene");
                    } else {
                        gdi_set_status(app, "✗ 無法寫入檔案");
                    }
                }
                return 0;
            }
            return 0;

        case WM_MOUSEMOVE: {
            if (app == NULL || !app->has_layout) {
                return 0;
            }

            int px = (short)LOWORD(lparam);
            int py = (short)HIWORD(lparam);

            /* 中鍵平移：pan 直接存像素位移。 */
            if (app->panning) {
                app->pan_x += (double)(px - app->pan_last_x);
                app->pan_y += (double)(py - app->pan_last_y);
                app->pan_last_x = px;
                app->pan_last_y = py;
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            int v;
            ViewPoint2 mm;
            Coord radius;

            if (app->canvas_tool != TOOL_VIEW) {
                if (gdi_screen_to_view(window, app, px, py, &v, &mm, &radius)) {
                    gdi_canvas_move(app, window, v, mm);
                }
                return 0;
            }

            /* 拖曳中：游標反解回「這條線所屬的」表面 (u,v)，clamp 進範圍後改 offset。 */
            if (app->drag_guide >= 0) {
                if (!gdi_screen_to_view(window, app, px, py, &v, &mm, &radius) ||
                    v != app->drag_view) {
                    return 0;
                }

                SurfacePoint2 uv;
                GuideLine *gd = &app->world->guides[app->drag_guide];
                const PlacementSurface *surface =
                    world_find_placement(app->world, gd->placement_id);

                if (surface == NULL ||
                    !view_unproject_on_surface(
                        &VIEW_FRAMES[v], surface, mm, &uv)) {
                    return 0;
                }

                const SpaceBoundarySurface *boundary =
                    gd->placement_id != 0
                        ? world_find_boundary(app->world, surface->boundary_id)
                        : NULL;

                Coord min_u, min_v, max_u, max_v;
                if (boundary != NULL) {
                    poly_bbox(&boundary->outline,
                              &min_u, &min_v, &max_u, &max_v);
                } else {
                    min_u = surface->rect.min_u;
                    min_v = surface->rect.min_v;
                    max_u = surface->rect.max_u;
                    max_v = surface->rect.max_v;
                }

                Coord off = gd->direction == GUIDE_ALONG_U ? uv.v : uv.u;
                Coord lo = gd->direction == GUIDE_ALONG_U ? min_v : min_u;
                Coord hi = gd->direction == GUIDE_ALONG_U ? max_v : max_u;

                /* clamp 後必定過守門員——拖曳在構造上不可能產生非法 offset。 */
                if (off < lo) off = lo;
                if (off > hi) off = hi;

                if (off == gd->offset) {
                    return 0;
                }

                guide_line_move(surface, boundary, gd, off);
                app_refresh(app, window);

                /* refresh 會清掉互動態；拖曳還在進行，補回來讓線保持高亮。 */
                app->drag_guide = (int)(gd - app->world->guides);
                app->drag_view = v;
                app->hover.view = v;
                app->hover.guide = app->drag_guide;

                {
                    char desc[160];
                    gdi_describe_pick(app, &app->hover, desc, sizeof desc);
                    gdi_set_hover(app, desc);
                }
                return 0;
            }

            ScenePick np = SCENE_PICK_NONE;

            if (gdi_screen_to_view(window, app, px, py, &v, &mm, &radius)) {
                np = scene_pick_at(
                    &app->scene, &VIEW_FRAMES[v], v, mm, radius);
            }

            if (!scene_pick_equal(np, app->hover)) {
                char desc[160];
                app->hover = np;
                gdi_describe_pick(app, &np, desc, sizeof desc);
                gdi_set_hover(app, desc);
                InvalidateRect(window, NULL, FALSE);
            }
            return 0;
        }

        case WM_LBUTTONDOWN: {
            if (app == NULL || !app->has_layout) {
                return 0;
            }

            int v;
            ViewPoint2 mm;
            Coord radius;
            int px = (short)LOWORD(lparam);
            int py = (short)HIWORD(lparam);

            if (!gdi_screen_to_view(window, app, px, py, &v, &mm, &radius)) {
                return 0;
            }

            if (app->canvas_tool != TOOL_VIEW) {
                gdi_canvas_down(app, window, v, mm, radius);
                return 0;
            }

            ScenePick p =
                scene_pick_at(&app->scene, &VIEW_FRAMES[v], v, mm, radius);

            if (p.guide >= 0) {
                app->drag_guide = p.guide;
                app->drag_view = v;
                app->hover = p;
                SetCapture(window);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }

            app->selected = p;
            InvalidateRect(window, NULL, FALSE);

            if (p.timber >= 0) {
                char msg[128];
                snprintf(msg, sizeof msg, "角材%" PRIu32 " %s",
                         app->scene.timbers[p.timber].id,
                         timber_face_name(p.face));
                gdi_set_status(app, msg);
            }
            return 0;
        }

        case WM_LBUTTONUP: {
            if (app != NULL && app->canvas_tool != TOOL_VIEW) {
                int v; ViewPoint2 mm; Coord radius;
                if (gdi_screen_to_view(window, app,
                        (short)LOWORD(lparam), (short)HIWORD(lparam),
                        &v, &mm, &radius)) {
                    gdi_canvas_up(app, window, v, mm);
                } else {
                    gdi_canvas_up(app, window, -1, (ViewPoint2){ 0, 0 });
                }
                ReleaseCapture();
                return 0;
            }
            if (app != NULL && app->drag_guide >= 0) {
                app->drag_guide = -1;
                ReleaseCapture();
                InvalidateRect(window, NULL, FALSE);
            }
            return 0;
        }

        case WM_MBUTTONDOWN:
            if (app != NULL && app->has_layout) {
                app->panning = true;
                app->pan_last_x = (short)LOWORD(lparam);
                app->pan_last_y = (short)HIWORD(lparam);
                SetCapture(window);
            }
            return 0;

        case WM_MBUTTONUP:
            if (app != NULL && app->panning) {
                app->panning = false;
                ReleaseCapture();
            }
            return 0;

        case WM_MOUSEWHEEL: {
            if (app == NULL || !app->has_layout) {
                return 0;
            }

            POINT pt = { (short)LOWORD(lparam), (short)HIWORD(lparam) };
            ScreenToClient(window, &pt);

            RECT client;
            GetClientRect(window, &client);

            if (pt.y < 0 || pt.y >= client.bottom - GDI_INPUT_BAR_H) {
                return 0;
            }

            /* 以游標為錨：pan' = pan·f + c·(1−f)，被 clamp 時用實際倍率。 */
            int steps = GET_WHEEL_DELTA_WPARAM(wparam) / 120;
            double f = 1.0;
            int i;
            for (i = 0; i < (steps > 0 ? steps : -steps); ++i) {
                f *= steps > 0 ? 1.15 : 1.0 / 1.15;
            }

            double nz = app->zoom * f;
            if (nz < 0.02) nz = 0.02;
            if (nz > 80.0) nz = 80.0;

            double eff = nz / app->zoom;
            app->pan_x = app->pan_x * eff + (double)pt.x * (1.0 - eff);
            app->pan_y = app->pan_y * eff + (double)pt.y * (1.0 - eff);
            app->zoom = nz;
            InvalidateRect(window, NULL, FALSE);
            return 0;
        }

        case WM_SETCURSOR:
            if (LOWORD(lparam) == HTCLIENT && app != NULL &&
                (app->drag_guide >= 0 || app->hover.guide >= 0)) {
                SetCursor(LoadCursorA(NULL, IDC_SIZEALL));
                return TRUE;
            }
            break;

        case WM_KEYDOWN:
            if (wparam == VK_ESCAPE) {
                /* 兩段式：有互動態先取消，沒有才關視窗。 */
                if (app != NULL &&
                    (app->draw_down || app->edit_down ||
                     app->draw_count > 0)) {
                    canvas_reset_drawing(app);
                    ReleaseCapture();
                    InvalidateRect(window, NULL, FALSE);
                } else if (app != NULL && app->panning) {
                    app->panning = false;
                    ReleaseCapture();
                } else if (app != NULL && app->drag_guide >= 0) {
                    app->drag_guide = -1;
                    ReleaseCapture();
                    InvalidateRect(window, NULL, FALSE);
                } else if (app != NULL &&
                           (!scene_pick_is_none(&app->selected) ||
                            !scene_pick_is_none(&app->hover))) {
                    app->selected = SCENE_PICK_NONE;
                    app->hover = SCENE_PICK_NONE;
                    InvalidateRect(window, NULL, FALSE);
                } else {
                    DestroyWindow(window);
                }
            }
            return 0;

        case WM_DESTROY:
            if (app != NULL) {
                gdi_app_release_objects(app);
            }
            PostQuitMessage(0);
            return 0;

        default:
            return DefWindowProcW(window, message, wparam, lparam);
    }

    return DefWindowProcW(window, message, wparam, lparam);
}

/*
 * 開視窗顯示三視圖，直到使用者關閉視窗或按 Esc 才返回。
 * 視窗持有 world 指標：輸入列與拖曳都經由 domain 動詞改它。
 */
static bool gdi_show_three_views(World *world)
{
    GdiApp app = { 0 };
    app.world = world;
    app.scene = scene_from_world(world);
    app.has_layout =
        app.scene.placement_count > 0 &&
        scene_compute_layout(&app.scene, &app.layout);
    app.hover = SCENE_PICK_NONE;
    app.selected = SCENE_PICK_NONE;
    app.drag_guide = -1;
    app.drag_view = -1;
    app.zoom = 1.0;

    WNDCLASSW wc = { 0 };
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = gdi_window_proc;
    wc.hInstance = GetModuleHandleW(NULL);
    wc.hCursor = LoadCursorA(NULL, IDC_ARROW);
    wc.lpszClassName = L"CurrentGeometryThreeViews";

    if (!RegisterClassW(&wc)) {
        return false;
    }

    /* 功能表：檔案（開啟/範例/清空/結束）與檢視（重設縮放）。 */
    HMENU menu = CreateMenu();
    HMENU file_menu = CreatePopupMenu();
    HMENU view_menu = CreatePopupMenu();
    HMENU canvas_menu = CreatePopupMenu();

    AppendMenuW(file_menu, MF_STRING, IDM_OPEN_SCENE, L"開啟場景檔…\tCtrl+O");
    AppendMenuW(file_menu, MF_STRING, IDC_BTN_EXAMPLE, L"載入範例\tCtrl+E");
    AppendMenuW(file_menu, MF_STRING, IDC_BTN_CLEAR, L"清空");
    AppendMenuW(file_menu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(file_menu, MF_STRING, IDM_EXPORT_SCENE, L"匯出 .scene…");
    AppendMenuW(file_menu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(file_menu, MF_STRING, IDM_EXIT, L"結束");
    AppendMenuW(view_menu, MF_STRING, IDM_ZOOM_RESET, L"重設視圖\tCtrl+0");
    AppendMenuW(canvas_menu, MF_STRING, IDM_TOOL_VIEW, L"檢視／選取");
    AppendMenuW(canvas_menu, MF_STRING, IDM_TOOL_RECT, L"▭ 拉矩形建面");
    AppendMenuW(canvas_menu, MF_STRING, IDM_TOOL_POLY, L"⬠ 畫多邊形建面");
    AppendMenuW(canvas_menu, MF_STRING, IDM_TOOL_HOLE, L"▨ 挖矩形孔");
    AppendMenuW(canvas_menu, MF_STRING, IDM_TOOL_EDIT, L"✥ 編輯邊界");
    AppendMenuW(canvas_menu, MF_SEPARATOR, 0, NULL);
    app.surf_menu = CreatePopupMenu();
    AppendMenuW(canvas_menu, MF_POPUP, (UINT_PTR)app.surf_menu, L"工作面");
    AppendMenuW(menu, MF_POPUP, (UINT_PTR)file_menu, L"檔案(&F)");
    AppendMenuW(menu, MF_POPUP, (UINT_PTR)view_menu, L"檢視(&V)");
    AppendMenuW(menu, MF_POPUP, (UINT_PTR)canvas_menu, L"畫布(&C)");
    gdi_rebuild_surf_menu(&app);

    HWND window = CreateWindowW(
        wc.lpszClassName,
        L"角材幾何 三視圖（輸入指令改場景；拖曳參考線；滾輪縮放；Esc 取消/關閉）",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 1100, 800,
        NULL, menu, wc.hInstance, &app
    );

    if (window == NULL) {
        return false;
    }

    /* Ctrl 快速鍵走加速器表；Esc 留在 WM_KEYDOWN，打字時不攔。 */
    ACCEL accel[] = {
        { FVIRTKEY | FCONTROL, 'O', IDM_OPEN_SCENE },
        { FVIRTKEY | FCONTROL, 'E', IDC_BTN_EXAMPLE },
        { FVIRTKEY | FCONTROL, '0', IDM_ZOOM_RESET },
        { FVIRTKEY | FCONTROL, 'Z', IDM_UNDO },
        { FVIRTKEY | FCONTROL, 'Y', IDM_REDO },
        { FVIRTKEY | FCONTROL | FSHIFT, 'Z', IDM_REDO }
    };
    HACCEL haccel = CreateAcceleratorTableW(accel, 6);

    MSG msg;

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        if (!TranslateAcceleratorW(window, haccel, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    if (haccel != NULL) {
        DestroyAcceleratorTable(haccel);
    }
    DestroyMenu(menu);

    return true;
}

/*
 * --bench N：不開視窗，量測 WM_PAINT 路徑兩種寫法的差異。
 *
 *   cold：每輪重建緩衝 DC/位圖，並清掉物件快取（筆/刷/字型全部重建）
 *         ≈ 快取之前的每幀成本。
 *   warm：緩衝與快取保留，每輪只畫 + BitBlt ≈ 快取之後的每幀成本。
 *
 * BitBlt 的目標是另一塊記憶體位圖，不刷到螢幕。
 */
static void bench_paint(const Scene *scene, const SceneLayout *layout, int iters)
{
    RECT client = { 0, 0, 1100, 800 };
    HDC screen = GetDC(NULL);

    if (screen == NULL || iters <= 0) {
        fprintf(stderr, "bench：拿不到螢幕 DC。\n");
        return;
    }

    GdiApp app = { 0 };
    app.scene = *scene;
    app.layout = *layout;
    app.has_layout = true;
    app.hover = SCENE_PICK_NONE;
    app.selected = SCENE_PICK_NONE;
    app.drag_guide = -1;
    app.drag_view = -1;

    HDC sink = CreateCompatibleDC(screen);
    HBITMAP sink_bmp =
        CreateCompatibleBitmap(screen, client.right, client.bottom);

    if (sink == NULL || sink_bmp == NULL) {
        fprintf(stderr, "bench：建立量測用位圖失敗。\n");
        return;
    }

    SelectObject(sink, sink_bmp);

    LARGE_INTEGER freq;
    QueryPerformanceFrequency(&freq);

    double cold_setup = 0.0, cold_draw = 0.0, cold_blit = 0.0;
    double warm_setup = 0.0, warm_draw = 0.0, warm_blit = 0.0;

    for (int i = 0; i < iters; ++i) {
        LARGE_INTEGER t0, t1, t2, t3;

        QueryPerformanceCounter(&t0);
        HDC mem = CreateCompatibleDC(screen);
        HBITMAP bmp =
            CreateCompatibleBitmap(screen, client.right, client.bottom);
        HGDIOBJ mem_stock = SelectObject(mem, bmp);
        QueryPerformanceCounter(&t1);

        gdi_cache_release(&app.objects);
        gdi_paint(mem, client, &app);
        QueryPerformanceCounter(&t2);

        BitBlt(sink, 0, 0, client.right, client.bottom, mem, 0, 0, SRCCOPY);
        SelectObject(mem, mem_stock);
        DeleteObject(bmp);
        DeleteDC(mem);
        QueryPerformanceCounter(&t3);

        cold_setup += (double)(t1.QuadPart - t0.QuadPart) / freq.QuadPart;
        cold_draw  += (double)(t2.QuadPart - t1.QuadPart) / freq.QuadPart;
        cold_blit  += (double)(t3.QuadPart - t2.QuadPart) / freq.QuadPart;
    }

    app.mem_dc = CreateCompatibleDC(screen);
    app.mem_bitmap =
        CreateCompatibleBitmap(screen, client.right, client.bottom);
    app.mem_w = client.right;
    app.mem_h = client.bottom;
    app.mem_stock = SelectObject(app.mem_dc, app.mem_bitmap);

    for (int i = 0; i < iters; ++i) {
        LARGE_INTEGER t0, t1, t2;

        QueryPerformanceCounter(&t0);
        gdi_paint(app.mem_dc, client, &app);
        QueryPerformanceCounter(&t1);

        BitBlt(sink, 0, 0, client.right, client.bottom,
               app.mem_dc, 0, 0, SRCCOPY);
        QueryPerformanceCounter(&t2);

        warm_draw += (double)(t1.QuadPart - t0.QuadPart) / freq.QuadPart;
        warm_blit += (double)(t2.QuadPart - t1.QuadPart) / freq.QuadPart;
    }

    gdi_app_release_objects(&app);
    DeleteObject(sink_bmp);
    DeleteDC(sink);
    ReleaseDC(NULL, screen);

    printf("\n=== GDI 每幀成本量測（%d 次）===\n", iters);
    printf("cold（每幀重建）：建立 %.1f + 繪製 %.1f + 貼上/拆除 %.1f = %.1f us\n",
           cold_setup / iters * 1e6,
           cold_draw / iters * 1e6,
           cold_blit / iters * 1e6,
           (cold_setup + cold_draw + cold_blit) / iters * 1e6);
    printf("warm（快取重用）：建立 %.1f + 繪製 %.1f + 貼上 %.1f = %.1f us\n",
           warm_setup / iters * 1e6,
           warm_draw / iters * 1e6,
           warm_blit / iters * 1e6,
           (warm_setup + warm_draw + warm_blit) / iters * 1e6);
}

#endif /* _WIN32 */

/* ============================================================
 * 場景文字檔輸入層
 *
 * World 結構與各上限常數在 GDI 互動層之前已定義
 * （互動層要解參考它的欄位，前置宣告不夠）。
 * ============================================================ */

/* 繪圖層只讀指標：World 變動後重建一次 Scene，計數就同步了。 */
static Scene scene_from_world(const World *world)
{
    return (Scene){
        .placements = world->placements,
        .placement_count = world->placement_count,
        .boundaries = world->boundaries,
        .boundary_count = world->boundary_count,
        .spaces = world->spaces,
        .space_count = world->space_count,
        .guides = world->guides,
        .guide_count = world->guide_count,
        .grids = world->grids,
        .grid_count = world->grid_count,
        .timbers = world->timbers,
        .timber_count = world->timber_count,
        .columns = world->columns,
        .column_count = world->column_count,
        .beams = world->beams,
        .beam_count = world->beam_count
    };
}

/* 關鍵字一律查表：多一種寫法只是多一列資料。 */
typedef struct {
    const char *word;
    int value;
} KeywordEntry;

/* 每張表以 NULL 收尾，查表就不必另外傳長度。 */
static const KeywordEntry GUIDE_DIRECTION_WORDS[] = {
    { "u", GUIDE_ALONG_U },
    { "v", GUIDE_ALONG_V },
    { NULL, 0 }
};

static const KeywordEntry LENGTH_DIRECTION_WORDS[] = {
    { "+u", SURFACE_DIRECTION_POS_U },
    { "-u", SURFACE_DIRECTION_NEG_U },
    { "+v", SURFACE_DIRECTION_POS_V },
    { "-v", SURFACE_DIRECTION_NEG_V },
    { NULL, 0 }
};

static const KeywordEntry DEPTH_SIDE_WORDS[] = {
    { "+n", SURFACE_DEPTH_POSITIVE_NORMAL },
    { "-n", SURFACE_DEPTH_NEGATIVE_NORMAL },
    { NULL, 0 }
};

static const KeywordEntry BOUNDARY_KIND_WORDS[] = {
    { "room_plan",       BOUNDARY_ROOM_PLAN },
    { "wall_elevation",  BOUNDARY_WALL_ELEVATION },
    { "unspecified",     BOUNDARY_UNSPECIFIED },
    { NULL, 0 }
};

static const KeywordEntry FIXITY_WORDS[] = {
    { "fixed", EDGE_FIXED },
    { "free",  EDGE_FREE },
    { "F",     EDGE_FIXED },
    { "X",     EDGE_FREE },
    { NULL, 0 }
};

/* 軸只有六種寫法，所以場景檔根本寫不出非單位、非軸向的向量。 */
static const struct {
    const char *word;
    Vector3 axis;
} AXIS_WORDS[] = {
    { "+x", {  1,  0,  0 } },
    { "-x", { -1,  0,  0 } },
    { "+y", {  0,  1,  0 } },
    { "-y", {  0, -1,  0 } },
    { "+z", {  0,  0,  1 } },
    { "-z", {  0,  0, -1 } }
};

static bool lookup_keyword(const char *token, const KeywordEntry *table, int *out_value)
{
    for (size_t i = 0; table[i].word != NULL; ++i) {
        if (strcmp(token, table[i].word) == 0) {
            *out_value = table[i].value;
            return true;
        }
    }

    return false;
}

static bool lookup_axis(const char *token, Vector3 *out_axis)
{
    for (size_t i = 0; i < sizeof(AXIS_WORDS) / sizeof(AXIS_WORDS[0]); ++i) {
        if (strcmp(token, AXIS_WORDS[i].word) == 0) {
            *out_axis = AXIS_WORDS[i].axis;
            return true;
        }
    }

    return false;
}

static bool parse_i64(const char *token, Coord *out_value)
{
    char *end = NULL;

    errno = 0;

    long long value = strtoll(token, &end, 10);

    if (end == token || *end != '\0' || errno == ERANGE) {
        return false;
    }

    *out_value = (Coord)value;
    return true;
}

/* 所有 int64 → uint32 的窄化都走這裡：先檢查範圍再轉型。 */
static bool parse_u32(const char *token, uint32_t *out_value)
{
    Coord value;

    if (!parse_i64(token, &value) || value < 0 || value > (Coord)UINT32_MAX) {
        return false;
    }

    *out_value = (uint32_t)value;
    return true;
}

/* 就地切分：空白改寫成字串結尾，tokens 指進原本那條緩衝。超過上限回 -1。 */
static int split_tokens(char *line, char *tokens[], int max_tokens)
{
    int count = 0;
    char *p = line;

    while (*p != '\0') {
        while (*p == ' ' || *p == '\t') {
            ++p;
        }

        if (*p == '\0') {
            break;
        }

        if (count == max_tokens) {
            return -1;
        }

        tokens[count++] = p;

        while (*p != '\0' && *p != ' ' && *p != '\t') {
            ++p;
        }

        if (*p != '\0') {
            *p++ = '\0';
        }
    }

    return count;
}

/*
 * 錯誤同時去兩個地方：stderr 給命令列使用者，
 * 緩衝區給視窗裡的狀態列（UI 拿不到 stderr）。
 */
static char g_scene_last_error[256] = "";

static void scene_error(const char *path, int line_no, const char *message)
{
    fprintf(stderr, "%s:%d: %s\n", path, line_no, message);
    snprintf(g_scene_last_error, sizeof g_scene_last_error,
             "line %d: %s", line_no, message);
}

static const char *scene_last_error(void)
{
    return g_scene_last_error;
}

static const SpaceBoundarySurface *world_find_boundary(
    const World *world,
    uint32_t id
)
{
    for (size_t i = 0; i < world->boundary_count; ++i) {
        if (world->boundaries[i].id == id) {
            return &world->boundaries[i];
        }
    }

    return NULL;
}

static const PlacementSurface *world_find_placement(
    const World *world,
    uint32_t id
)
{
    for (size_t i = 0; i < world->placement_count; ++i) {
        if (world->placements[i].id == id) {
            return &world->placements[i];
        }
    }

    return NULL;
}

static const Space *world_find_space(const World *world, uint32_t id)
{
    for (size_t i = 0; i < world->space_count; ++i) {
        if (world->spaces[i].id == id) {
            return &world->spaces[i];
        }
    }

    return NULL;
}

static const RcColumn *world_find_column(const World *world, uint32_t id)
{
    for (size_t i = 0; i < world->column_count; ++i) {
        if (world->columns[i].id == id) {
            return &world->columns[i];
        }
    }

    return NULL;
}

static const RcBeam *world_find_beam(const World *world, uint32_t id)
{
    for (size_t i = 0; i < world->beam_count; ++i) {
        if (world->beams[i].id == id) {
            return &world->beams[i];
        }
    }

    return NULL;
}

/* 承載面掛的邊界面；0 或未找到都回 NULL（= 自帶 rect 模式）。 */
static const SpaceBoundarySurface *world_placement_boundary(
    const World *world,
    const PlacementSurface *placement
)
{
    if (placement == NULL || placement->boundary_id == 0) {
        return NULL;
    }

    return world_find_boundary(world, placement->boundary_id);
}

static const GuideLine *world_find_guide(const World *world, uint32_t id)
{
    for (size_t i = 0; i < world->guide_count; ++i) {
        if (world->guides[i].id == id) {
            return &world->guides[i];
        }
    }

    return NULL;
}

static Timber *world_find_timber(World *world, uint32_t id)
{
    for (size_t i = 0; i < world->timber_count; ++i) {
        if (world->timbers[i].id == id) {
            return &world->timbers[i];
        }
    }

    return NULL;
}

/* ============================================================
 * 房間：把已宣告的面綁成一組，並檢查它們彼此一致
 *
 * 每片面的框架受「單位軸向量」限制，所以一片面給出三條約束：
 *   法向軸 a：法向 ±X/±Y/±Z → 佔據房間在 a 軸的下界/上界槽位，
 *             界值 = 面所在的平面座標。
 *   面內兩軸：面的 region 投影回房間座標 → 釘住那兩軸的 [min,max]。
 * 一致 = 沒有兩片面佔同一槽位、同一軸的所有區間約束相同、
 *        且下界小於上界（法向朝內的面會讓 lo > hi，自動被拒）。
 * 六槽全滿且區間一致時，房間就是字面上的封閉盒；
 * 少於六面則是「這幾面彼此一致」的部分宣告。
 * ============================================================ */

/* 單位軸向量的非零分量編號：0=x, 1=y, 2=z。 */
static int axis_index(Vector3 axis)
{
    if (axis.x != 0) return 0;
    if (axis.y != 0) return 1;
    return 2;
}

static Coord point3_component(Point3 p, int axis)
{
    return axis == 0 ? p.x : axis == 1 ? p.y : p.z;
}

/* 承載面的有效輪廓投影到房間座標軸 axis 上的 [min,max] 區間。 */
static void surface_extent_on_axis(
    const PlacementSurface *surface,
    const SpaceBoundarySurface *boundary,
    int axis,
    Coord *out_lo,
    Coord *out_hi
)
{
    const SurfaceFrame *f = &surface->frame;
    Coord o = point3_component(f->origin, axis);
    Coord su = axis == 0 ? f->axis_u.x : axis == 1 ? f->axis_u.y : f->axis_u.z;
    Coord sv = axis == 0 ? f->axis_v.x : axis == 1 ? f->axis_v.y : f->axis_v.z;
    Coord lo, hi;

    Coord min_u, min_v, max_u, max_v;
    if (boundary != NULL) {
        poly_bbox(&boundary->outline, &min_u, &min_v, &max_u, &max_v);
    } else {
        min_u = surface->rect.min_u;
        min_v = surface->rect.min_v;
        max_u = surface->rect.max_u;
        max_v = surface->rect.max_v;
    }

    if (su != 0) {
        lo = su > 0 ? min_u : -max_u;
        hi = su > 0 ? max_u : -min_u;
    } else {
        lo = sv > 0 ? min_v : -max_v;
        hi = sv > 0 ? max_v : -min_v;
    }

    *out_lo = o + lo;
    *out_hi = o + hi;
}

/*
 * Space 建構子：成員 = 一組邊界面 id。
 * 每片邊界面必須恰有一片承載面掛著它（由此取得 3D 位置），
 * 再對承載面跑槽位一致性——與舊 room_bind 同構。
 * 寫進 out_space；失敗不動 out_space。
 */
static bool space_construct(
    const World *world,
    uint32_t space_id,
    const SurfaceId boundary_ids[],
    size_t count,
    Space *out_space
)
{
    typedef struct { Coord v; bool set; } MaybeBound;

    MaybeBound bound[3][2] = { 0 };   /* [軸][0=下界, 1=上界]，由法向面釘住 */
    MaybeBound ext_lo[3] = { 0 };     /* 面內區間在各軸上的下/上界 */
    MaybeBound ext_hi[3] = { 0 };
    bool slot_taken[3][2] = { 0 };    /* [軸][0=負法向, 1=正法向] */

    if (count < 1 || count > SPACE_MAX_MEMBERS || out_space == NULL) {
        return false;
    }

    for (size_t i = 0; i < count; ++i) {
        const SpaceBoundarySurface *bd =
            world_find_boundary(world, boundary_ids[i]);

        if (bd == NULL) {
            return false;
        }

        for (size_t j = 0; j < i; ++j) {
            if (boundary_ids[j] == boundary_ids[i]) {
                return false;   /* 同一片邊界面被宣告兩次 */
            }
        }

        /* 這片邊界面必須恰有一片承載面掛著。 */
        const PlacementSurface *face = NULL;
        size_t carriers = 0;

        for (size_t p = 0; p < world->placement_count; ++p) {
            if (world->placements[p].boundary_id == bd->id) {
                face = &world->placements[p];
                ++carriers;
            }
        }

        if (carriers != 1) {
            return false;   /* 0 = 沒有世界位置；>1 = 位置歧義 */
        }

        int a = axis_index(face->frame.normal);
        Coord n = a == 0 ? face->frame.normal.x
                : a == 1 ? face->frame.normal.y
                         : face->frame.normal.z;
        int slot = n > 0 ? 1 : 0;
        Coord plane = point3_component(face->frame.origin, a);

        if (slot_taken[a][slot]) {
            return false;   /* 兩片面佔同一方向槽位：重複或衝突 */
        }

        slot_taken[a][slot] = true;
        bound[a][slot].v = plane;
        bound[a][slot].set = true;

        for (int j = 0; j < 3; ++j) {
            if (j == a) {
                continue;
            }

            Coord lo, hi;
            surface_extent_on_axis(face, bd, j, &lo, &hi);

            if (ext_lo[j].set &&
                (ext_lo[j].v != lo || ext_hi[j].v != hi)) {
                return false;   /* 同一軸的區間約束不一致 */
            }

            ext_lo[j].v = lo;  ext_lo[j].set = true;
            ext_hi[j].v = hi;  ext_hi[j].set = true;
        }
    }

    /* 界值與區間端點要吻合；下界必須小於上界（法向朝內在這裡被擋）。 */
    for (int j = 0; j < 3; ++j) {
        if (bound[j][0].set && ext_lo[j].set && bound[j][0].v != ext_lo[j].v) {
            return false;
        }
        if (bound[j][1].set && ext_hi[j].set && bound[j][1].v != ext_hi[j].v) {
            return false;
        }
        if (bound[j][0].set && bound[j][1].set &&
            bound[j][0].v >= bound[j][1].v) {
            return false;
        }
    }

    *out_space = (Space){ 0 };
    out_space->id = space_id;
    out_space->boundary_count = count;
    for (size_t i = 0; i < count; ++i) {
        out_space->boundaries[i] = boundary_ids[i];
    }

    for (int j = 0; j < 3; ++j) {
        out_space->room_min[j] = bound[j][0].set ? bound[j][0].v : ext_lo[j].v;
        out_space->room_max[j] = bound[j][1].set ? bound[j][1].v : ext_hi[j].v;
    }

    out_space->closed =
        slot_taken[0][0] && slot_taken[0][1] &&
        slot_taken[1][0] && slot_taken[1][1] &&
        slot_taken[2][0] && slot_taken[2][1];

    return true;
}

/*
 * 重宣告交易（公理 I8）：
 *   把 slot 指到的物件換成 *replacement，然後重驗整個 World——
 *   所有承載面、參考線、已放置角材、空間都還合法才提交，
 *   否則回滾舊物件。
 *
 * 重驗範圍刻意取全體：World 很小，全驗比重驗「依賴者清單」簡單且不可能漏。
 */

/* ============================================================
 * 角材 UV footprint、實體重疊與擋面（公理 O1–O3、S1–S3）
 *
 *   O1：A0 footprint 必須 ⊆ 有效區域（已由放置守門員把關）。
 *   O2：實體不得正面積重疊——邊界面、孔、已放角材都是阻擋來源；
 *       端點相接（零面積接觸）合法，那正是「頂到了」的定義。
 *   O3：auto 跨距 = 固定中線上連續合法區間的全程，
 *       兩端必須各有一個涵蓋全寬的唯一擋面。
 * ============================================================ */

/*
 * 由錨點參數推導 A0 在承載面 UV 上的矩形。
 * 與 timber_place_a0_on_surface 內的算法同式，
 * 獨立抽出讓「未放置的候選」也能先算 footprint。
 */
static bool a0_rect_uv(
    const PlacementSurface *surface,
    SurfacePoint2 anchor,
    int length_direction,
    int depth_side,
    Coord length,
    Coord size_a,
    SurfaceRegion2 *out
)
{
    if (surface == NULL || out == NULL || length <= 0) {
        return false;
    }

    Vector3 axis_length = surface_direction_vector(
        surface,
        (SurfaceDirection)length_direction
    );

    if (vector_dot(axis_length, axis_length) != 1) {
        return false;
    }

    Vector3 axis_b =
        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL
            ? surface->frame.normal
            : vector_negate(surface->frame.normal);

    Vector3 axis_a = vector_cross(axis_b, axis_length);

    SurfacePoint2 far_pt = {
        .u = anchor.u +
             length * vector_dot(axis_length, surface->frame.axis_u) +
             size_a * vector_dot(axis_a, surface->frame.axis_u),
        .v = anchor.v +
             length * vector_dot(axis_length, surface->frame.axis_v) +
             size_a * vector_dot(axis_a, surface->frame.axis_v)
    };

    *out = (SurfaceRegion2){
        coord_min(anchor.u, far_pt.u),
        coord_min(anchor.v, far_pt.v),
        coord_max(anchor.u, far_pt.u),
        coord_max(anchor.v, far_pt.v)
    };
    return true;
}

/* 已放角材的 A0 footprint（錨點是凍結值）。 */
static bool timber_a0_footprint_uv(
    const PlacementSurface *surface,
    const Timber *timber,
    const TimberAnchor *anchor,
    SurfaceRegion2 *out
)
{
    if (timber == NULL || anchor == NULL || !timber->placed) {
        return false;
    }

    return a0_rect_uv(
        surface, anchor->uv,
        anchor->length_direction, anchor->depth_side,
        timber->length, timber->size_a, out
    );
}

/* 正面積重疊：兩軸交集都必須有正長度；端點相接不算。 */
static bool uv_rects_overlap(
    Coord a_min_u, Coord a_min_v, Coord a_max_u, Coord a_max_v,
    Coord b_min_u, Coord b_min_v, Coord b_max_u, Coord b_max_v
)
{
    return coord_min(a_max_u, b_max_u) > coord_max(a_min_u, b_min_u) &&
           coord_min(a_max_v, b_max_v) > coord_max(a_min_v, b_min_v);
}

/* 候選矩形是否與同承載面上任何已放角材正面積重疊。 */
static bool world_footprint_collides(
    const World *world,
    const PlacementSurface *placement,
    const SurfaceRegion2 *rect,
    const Timber *exclude
)
{
    if (world == NULL || placement == NULL || rect == NULL) {
        return true;
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *t = &world->timbers[i];
        const TimberAnchor *a = &world->anchors[i];
        SurfaceRegion2 other;

        if (!t->placed || t == exclude ||
            a->placement_id != placement->id) {
            continue;
        }

        if (!timber_a0_footprint_uv(placement, t, a, &other)) {
            continue;
        }

        if (uv_rects_overlap(
                rect->min_u, rect->min_v, rect->max_u, rect->max_v,
                other.min_u, other.min_v, other.max_u, other.max_v)) {
            return true;
        }
    }

    return false;
}

/* ============================================================
 * 擋面（StopFace）：角材端面可以頂住的垂直實體面
 *
 *   來源只有三種：外輪廓邊、孔邊、已放角材的側面。
 *   fixed = 擋面在角材「長度軸」上的座標；
 *   lo..hi = 擋面在角材「寬度軸」上的涵蓋範圍。
 * ============================================================ */

typedef enum {
    STOP_OUTLINE_EDGE,
    STOP_HOLE_EDGE,
    STOP_TIMBER_SIDE
} StopFaceKind;

typedef struct {
    int kind;               /* StopFaceKind */
    SurfaceId boundary_id;  /* 邊類擋面：所屬邊界面 */
    TimberId timber_id;     /* 角材側面：所屬角材 */
    int hole_index;         /* STOP_HOLE_EDGE：孔 index，否則 -1 */
    int edge_index;         /* 環上邊 index / 角材面序號 */
    int fixity;             /* EdgeFixity；角材側面記 EDGE_FIXED */
    Coord fixed;
    Coord lo;
    Coord hi;
} StopFace;

#define STOP_FACE_MAX \
    (POLY_MAX_VERTICES * (POLY_MAX_HOLES + 1) + WORLD_MAX_TIMBERS * 2)

/*
 * 枚舉所有「垂直於角材長度軸」的擋面。
 *   along_v = true：角材沿 V → 端面是水平線段 → 擋面是水平邊
 *                   （a.v == b.v）與已放角材的 min_v / max_v 側面。
 */
static size_t collect_stop_faces(
    const World *world,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    bool along_v,
    const Timber *exclude,
    StopFace out[],
    size_t out_cap
)
{
    size_t count = 0;

    if (boundary != NULL) {
        const PolygonLoop2 *loops[1 + POLY_MAX_HOLES];
        int hole_of[1 + POLY_MAX_HOLES];
        size_t loop_count = 0;

        loops[loop_count] = &boundary->outline;
        hole_of[loop_count] = -1;
        ++loop_count;

        for (size_t h = 0; h < boundary->hole_count; ++h) {
            loops[loop_count] = &boundary->holes[h];
            hole_of[loop_count] = (int)h;
            ++loop_count;
        }

        for (size_t li = 0; li < loop_count; ++li) {
            const PolygonLoop2 *loop = loops[li];

            for (size_t i = 0; i < loop->count && count < out_cap; ++i) {
                SurfacePoint2 a = loop->v[i];
                SurfacePoint2 b = loop->v[(i + 1) % loop->count];

                /* 只收與長度軸垂直的邊：
                 * along_v 取水平邊（v 恆定），否則取直立邊。 */
                if (along_v && a.v != b.v) {
                    continue;
                }
                if (!along_v && a.u != b.u) {
                    continue;
                }

                out[count++] = (StopFace){
                    hole_of[li] < 0 ? STOP_OUTLINE_EDGE : STOP_HOLE_EDGE,
                    boundary->id,
                    0,
                    hole_of[li],
                    (int)i,
                    loop->fixity[i],
                    along_v ? a.v : a.u,
                    along_v ? coord_min(a.u, b.u) : coord_min(a.v, b.v),
                    along_v ? coord_max(a.u, b.u) : coord_max(a.v, b.v)
                };
            }
        }
    }

    /* 已放角材：footprint 上垂直於長度軸的兩個側面。 */
    for (size_t i = 0; i < world->timber_count && count + 2 <= out_cap; ++i) {
        const Timber *t = &world->timbers[i];
        const TimberAnchor *a = &world->anchors[i];
        SurfaceRegion2 f;

        if (!t->placed || t == exclude ||
            a->placement_id != placement->id) {
            continue;
        }

        if (!timber_a0_footprint_uv(placement, t, a, &f)) {
            continue;
        }

        if (along_v) {
            out[count++] = (StopFace){
                STOP_TIMBER_SIDE, 0, t->id, -1, 0, EDGE_FIXED,
                f.min_v, f.min_u, f.max_u
            };
            out[count++] = (StopFace){
                STOP_TIMBER_SIDE, 0, t->id, -1, 1, EDGE_FIXED,
                f.max_v, f.min_u, f.max_u
            };
        } else {
            out[count++] = (StopFace){
                STOP_TIMBER_SIDE, 0, t->id, -1, 0, EDGE_FIXED,
                f.min_u, f.min_v, f.max_v
            };
            out[count++] = (StopFace){
                STOP_TIMBER_SIDE, 0, t->id, -1, 1, EDGE_FIXED,
                f.max_u, f.min_v, f.max_v
            };
        }
    }

    return count;
}

/*
 * 在座標 at 找「恰好一個涵蓋 [lo,hi] 全寬」的擋面。
 *   回傳命中數；0 = 無擋面（懸空），>1 = 歧義。
 *   命中時 *out_face 指向唯一那面（FREE 邊也算命中，
 *   交由呼叫端拒絕——先找到才能說「頂到自由邊」）。
 */
static size_t pick_stop(
    const StopFace faces[],
    size_t face_count,
    Coord at,
    Coord lo,
    Coord hi,
    const StopFace **out_face
)
{
    const StopFace *found = NULL;
    size_t hits = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const StopFace *f = &faces[i];

        if (f->fixed != at || f->lo > lo || f->hi < hi) {
            continue;
        }

        found = f;
        ++hits;
    }

    if (hits == 1 && out_face != NULL) {
        *out_face = found;
    }

    return hits;
}

/* 數「合法」擋面（FREE 邊不算）：重驗只要求存在，不要求唯一。 */
static size_t count_legal_stops(
    const StopFace faces[],
    size_t face_count,
    Coord at,
    Coord lo,
    Coord hi
)
{
    size_t hits = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const StopFace *f = &faces[i];

        if (f->fixed == at && f->lo <= lo && f->hi >= hi &&
            f->fixity != EDGE_FREE) {
            ++hits;
        }
    }

    return hits;
}

/* ============================================================
 * auto 跨距解析：固定中線上，footprint 不穿過任何實體的
 * 連續合法區間全程。
 * ============================================================ */

typedef enum {
    SPAN_OK,
    SPAN_NO_INTERVAL,        /* 中線上沒有任何合法區間 */
    SPAN_AMBIGUOUS,          /* 多個合法區間，沒有選擇器 */
    SPAN_OUTSIDE_CONTACT,    /* 有區間但都不接觸 at-edge 引用的邊 */
    SPAN_THROUGH_OUTSIDE,    /* through 座標不在任何合法區間內 */
    SPAN_START_UNSUPPORTED,  /* 起點沒有唯一合法擋面 */
    SPAN_END_UNSUPPORTED,    /* 終點沒有唯一合法擋面 */
    SPAN_START_AMBIGUOUS,    /* 起點擋面歧義 */
    SPAN_END_AMBIGUOUS,      /* 終點擋面歧義 */
    SPAN_FREE_EDGE_END       /* 擋面是自由邊 */
} SpanStatus;

#define SPAN_CUT_MAX \
    (POLY_MAX_VERTICES * (POLY_MAX_HOLES + 1) + WORLD_MAX_TIMBERS * 2)

typedef struct {
    Coord start;
    Coord end;
} SpanInterval;

/*
 * 解析 auto 跨距。
 *
 *   along_v            角材長度軸 = V（false = U）
 *   cross_lo/cross_hi  角材在寬度軸上的覆蓋範圍
 *   has_contact        at-edge：候選區間必須與引用邊的範圍重疊
 *   has_through        區間選擇器（長度軸座標）
 *   out_start/out_end  解析結果（長度軸座標）
 *   err/err_cap        失敗時的人話訊息
 */
static SpanStatus resolve_auto_span(
    const World *world,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    bool along_v,
    Coord cross_lo,
    Coord cross_hi,
    bool has_contact,
    Coord contact_lo,
    Coord contact_hi,
    bool has_through,
    Coord through,
    Coord *out_start,
    Coord *out_end,
    char *err,
    size_t err_cap
)
{
    Coord cuts[SPAN_CUT_MAX];
    size_t cut_count = 0;

    /* --- 切點：輪廓與孔的所有頂點在長度軸上的座標 --- */
    if (boundary != NULL) {
        const PolygonLoop2 *loops[1 + POLY_MAX_HOLES];
        size_t loop_count = 0;

        loops[loop_count++] = &boundary->outline;

        for (size_t h = 0; h < boundary->hole_count; ++h) {
            loops[loop_count++] = &boundary->holes[h];
        }

        for (size_t li = 0; li < loop_count; ++li) {
            for (size_t i = 0; i < loops[li]->count &&
                            cut_count < SPAN_CUT_MAX; ++i) {
                cuts[cut_count++] = along_v
                    ? loops[li]->v[i].v
                    : loops[li]->v[i].u;
            }
        }
    } else {
        cuts[cut_count++] = along_v
            ? placement->rect.min_v : placement->rect.min_u;
        cuts[cut_count++] = along_v
            ? placement->rect.max_v : placement->rect.max_u;
    }

    /* --- 切點：同面已放角材 footprint 在長度軸上的兩端 --- */
    for (size_t i = 0; i < world->timber_count &&
                    cut_count + 2 <= SPAN_CUT_MAX; ++i) {
        const Timber *t = &world->timbers[i];
        const TimberAnchor *a = &world->anchors[i];
        SurfaceRegion2 f;

        if (!t->placed || a->placement_id != placement->id) {
            continue;
        }

        if (!timber_a0_footprint_uv(placement, t, a, &f)) {
            continue;
        }

        cuts[cut_count++] = along_v ? f.min_v : f.min_u;
        cuts[cut_count++] = along_v ? f.max_v : f.max_u;
    }

    /* 排序 + 去重。 */
    for (size_t i = 1; i < cut_count; ++i) {
        Coord key = cuts[i];
        size_t j = i;

        while (j > 0 && cuts[j - 1] > key) {
            cuts[j] = cuts[j - 1];
            --j;
        }
        cuts[j] = key;
    }

    size_t unique = 0;
    for (size_t i = 0; i < cut_count; ++i) {
        if (unique == 0 || cuts[i] != cuts[unique - 1]) {
            cuts[unique++] = cuts[i];
        }
    }
    cut_count = unique;

    /* --- 逐 cell 檢查：整個 footprint ⊆ 有效區域且不撞已放角材 --- */
    SpanInterval intervals[SPAN_CUT_MAX / 2 + 1];
    size_t interval_count = 0;
    bool open = false;

    for (size_t i = 0; i + 1 < cut_count; ++i) {
        Coord lo = cuts[i];
        Coord hi = cuts[i + 1];

        if (lo >= hi) {
            continue;
        }

        SurfaceRegion2 cell;

        if (along_v) {
            cell = (SurfaceRegion2){ cross_lo, lo, cross_hi, hi };
        } else {
            cell = (SurfaceRegion2){ lo, cross_lo, hi, cross_hi };
        }

        bool ok =
            surface_contains_rect(
                placement, boundary,
                cell.min_u, cell.min_v, cell.max_u, cell.max_v) &&
            !world_footprint_collides(world, placement, &cell, NULL);

        if (ok && !open) {
            intervals[interval_count].start = lo;
            intervals[interval_count].end = hi;
            open = true;
        } else if (ok) {
            intervals[interval_count].end = hi;
        } else if (open) {
            ++interval_count;
            open = false;
        }
    }
    if (open) {
        ++interval_count;
    }

    if (interval_count == 0) {
        snprintf(err, err_cap, "中線上沒有任何合法跨距");
        return SPAN_NO_INTERVAL;
    }

    /* --- at-edge 接觸範圍過濾：區間必須與引用邊的範圍重疊 --- */
    if (has_contact) {
        SpanInterval touching[SPAN_CUT_MAX / 2 + 1];
        size_t touching_count = 0;

        for (size_t i = 0; i < interval_count; ++i) {
            if (intervals[i].start < contact_hi &&
                intervals[i].end > contact_lo) {
                touching[touching_count++] = intervals[i];
            }
        }

        if (touching_count == 0) {
            snprintf(err, err_cap,
                     "有合法跨距但都不接觸引用的邊");
            return SPAN_OUTSIDE_CONTACT;
        }

        memcpy(intervals, touching, touching_count * sizeof(SpanInterval));
        interval_count = touching_count;
    }

    /* --- 選區間 --- */
    size_t chosen = (size_t)-1;

    if (has_through) {
        for (size_t i = 0; i < interval_count; ++i) {
            if (through >= intervals[i].start &&
                through <= intervals[i].end) {
                chosen = i;
                break;
            }
        }

        if (chosen == (size_t)-1) {
            snprintf(err, err_cap,
                     "through 座標不在任何合法跨距內");
            return SPAN_THROUGH_OUTSIDE;
        }
    } else if (interval_count > 1) {
        size_t n = (size_t)snprintf(err, err_cap, "跨距歧義：");

        for (size_t i = 0; i < interval_count && n < err_cap; ++i) {
            n += (size_t)snprintf(err + n, err_cap - n, " [%lld,%lld]",
                          (long long)intervals[i].start,
                          (long long)intervals[i].end);
        }
        return SPAN_AMBIGUOUS;
    } else {
        chosen = 0;
    }

    Coord span_start = intervals[chosen].start;
    Coord span_end = intervals[chosen].end;

    /* --- 兩端必須各有唯一合法擋面（place 當下不猜） --- */
    StopFace faces[STOP_FACE_MAX];
    size_t face_count = collect_stop_faces(
        world, placement, boundary, along_v, NULL,
        faces, STOP_FACE_MAX);

    const StopFace *stop = NULL;
    size_t hits;

    hits = pick_stop(faces, face_count, span_start,
                     cross_lo, cross_hi, &stop);
    if (hits == 0) {
        snprintf(err, err_cap, "跨距起點沒有擋面（端面懸空）");
        return SPAN_START_UNSUPPORTED;
    }
    if (hits > 1) {
        snprintf(err, err_cap, "跨距起點擋面歧義");
        return SPAN_START_AMBIGUOUS;
    }
    if (stop->fixity == EDGE_FREE) {
        snprintf(err, err_cap, "跨距起點頂到自由邊");
        return SPAN_FREE_EDGE_END;
    }

    hits = pick_stop(faces, face_count, span_end,
                     cross_lo, cross_hi, &stop);
    if (hits == 0) {
        snprintf(err, err_cap, "跨距終點沒有擋面（端面懸空）");
        return SPAN_END_UNSUPPORTED;
    }
    if (hits > 1) {
        snprintf(err, err_cap, "跨距終點擋面歧義");
        return SPAN_END_AMBIGUOUS;
    }
    if (stop->fixity == EDGE_FREE) {
        snprintf(err, err_cap, "跨距終點頂到自由邊");
        return SPAN_FREE_EDGE_END;
    }

    *out_start = span_start;
    *out_end = span_end;
    return SPAN_OK;
}

static bool world_revalidate(const World *world);

static bool world_replace_object(
    World *world,
    void *slot,
    const void *replacement,
    size_t size
)
{
    /* World 是 POD（固定容量陣列），整份 memcpy 就是快照。 */
    World backup = *world;

    memcpy(slot, replacement, size);

    if (!world_revalidate(world)) {
        *world = backup;
        return false;
    }

    return true;
}

/*
 * World 全量重驗：
 *   承載面自身合法、掛的邊界面存在；
 *   參考線 offset 仍在有效範圍；
 *   已放置角材用留存的放法重新驗證（A0 矩形 ⊆ 有效區域、自由邊規則）；
 *   空間成員仍然彼此一致。
 * 重驗只讀、不動 World。
 */
static bool world_revalidate(const World *world)
{
    for (size_t i = 0; i < world->boundary_count; ++i) {
        if (!boundary_is_valid(&world->boundaries[i])) {
            return false;
        }
    }

    for (size_t i = 0; i < world->placement_count; ++i) {
        const PlacementSurface *p = &world->placements[i];

        if (!placement_is_valid(p)) {
            return false;
        }

        if (p->boundary_id != 0 &&
            world_find_boundary(world, p->boundary_id) == NULL) {
            return false;
        }
    }

    for (size_t i = 0; i < world->guide_count; ++i) {
        const GuideLine *g = &world->guides[i];
        const PlacementSurface *p =
            world_find_placement(world, g->placement_id);

        if (p == NULL ||
            !guide_offset_in_range(
                p, world_placement_boundary(world, p),
                g->direction, g->offset)) {
            return false;
        }
    }

    for (size_t i = 0; i < world->grid_count; ++i) {
        const ReferenceGrid *g = &world->grids[i];
        const PlacementSurface *p =
            world_find_placement(world, g->placement_id);

        if (p == NULL ||
            !grid_is_valid(g, p, world_placement_boundary(world, p))) {
            return false;
        }
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *t = &world->timbers[i];

        if (!t->placed) {
            continue;
        }

        const TimberAnchor *a = &world->anchors[i];
        const PlacementSurface *p =
            world_find_placement(world, a->placement_id);

        if (p == NULL) {
            return false;
        }

        Timber probe = *t;
        probe.placed = false;

        if (!timber_place_a0_on_surface(
                &probe, p, world_placement_boundary(world, p),
                a->uv,
                (SurfaceDirection)a->length_direction,
                (SurfaceDepthSide)a->depth_side)) {
            return false;
        }

        /*
         * auto 角材的恆真條件：兩端各至少還有一個合法擋面。
         * place 當下要求唯一（不猜）；事後重驗只要求存在——
         * 唯一性是用來決定當初怎麼放，不是事後不變式。
         */
        if (a->span_mode == SPAN_AUTO) {
            SurfaceRegion2 f;
            const SpaceBoundarySurface *b =
                world_placement_boundary(world, p);
            bool along_v =
                a->length_direction == SURFACE_DIRECTION_POS_V ||
                a->length_direction == SURFACE_DIRECTION_NEG_V;

            if (!timber_a0_footprint_uv(p, t, a, &f)) {
                return false;
            }

            StopFace faces[STOP_FACE_MAX];
            size_t face_count = collect_stop_faces(
                world, p, b, along_v, t, faces, STOP_FACE_MAX);

            if (along_v) {
                if (count_legal_stops(faces, face_count,
                        f.min_v, f.min_u, f.max_u) == 0 ||
                    count_legal_stops(faces, face_count,
                        f.max_v, f.min_u, f.max_u) == 0) {
                    return false;
                }
            } else {
                if (count_legal_stops(faces, face_count,
                        f.min_u, f.min_v, f.max_v) == 0 ||
                    count_legal_stops(faces, face_count,
                        f.max_u, f.min_v, f.max_v) == 0) {
                    return false;
                }
            }
        }
    }

    /* 實體不得正面積重疊：同承載面的已放角材兩兩檢查。 */
    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *ti = &world->timbers[i];
        const TimberAnchor *ai = &world->anchors[i];

        if (!ti->placed) {
            continue;
        }

        for (size_t j = i + 1; j < world->timber_count; ++j) {
            const Timber *tj = &world->timbers[j];
            const TimberAnchor *aj = &world->anchors[j];
            const PlacementSurface *p;
            SurfaceRegion2 fi, fj;

            if (!tj->placed || ai->placement_id != aj->placement_id) {
                continue;
            }

            p = world_find_placement(world, ai->placement_id);

            if (p == NULL ||
                !timber_a0_footprint_uv(p, ti, ai, &fi) ||
                !timber_a0_footprint_uv(p, tj, aj, &fj)) {
                return false;
            }

            if (uv_rects_overlap(
                    fi.min_u, fi.min_v, fi.max_u, fi.max_v,
                    fj.min_u, fj.min_v, fj.max_u, fj.max_v)) {
                return false;
            }
        }
    }

    for (size_t i = 0; i < world->space_count; ++i) {
        const Space *s = &world->spaces[i];
        Space probe;

        if (s->boundary_count == 0) {
            continue;   /* 空容器：零成員的部分空間，恆合法 */
        }

        if (!space_construct(
                world, s->id, s->boundaries, s->boundary_count, &probe)) {
            return false;
        }
    }

    /* RC 柱/樑（I15–I17）：AABB 非空、所屬空間存在、足跡 ⊆ 平面範圍。 */
    for (size_t i = 0; i < world->column_count; ++i) {
        const RcColumn *c = &world->columns[i];

        if (!(c->x_hi > c->x_lo && c->y_hi > c->y_lo && c->z_hi > c->z_lo)) {
            return false;
        }
        if (c->space_id != 0) {
            const Space *s = world_find_space(world, c->space_id);
            if (s == NULL) {
                return false;
            }
            if (c->x_lo < s->room_min[0] || c->x_hi > s->room_max[0] ||
                c->y_lo < s->room_min[1] || c->y_hi > s->room_max[1]) {
                return false;   /* I15 足跡越出空間平面範圍 */
            }
        }
        for (size_t j = i + 1; j < world->column_count; ++j) {
            const RcColumn *o = &world->columns[j];
            if (c->x_lo < o->x_hi && o->x_lo < c->x_hi &&
                c->y_lo < o->y_hi && o->y_lo < c->y_hi) {
                return false;   /* I15 柱-柱正面積相交（邊相接合法） */
            }
        }
    }
    for (size_t i = 0; i < world->beam_count; ++i) {
        const RcBeam *b = &world->beams[i];

        if (!(b->x_hi > b->x_lo && b->y_hi > b->y_lo && b->z_hi > b->z_lo)) {
            return false;
        }
        if (b->space_id != 0) {
            const Space *s = world_find_space(world, b->space_id);
            if (s == NULL) {
                return false;
            }
            if (b->x_lo < s->room_min[0] || b->x_hi > s->room_max[0] ||
                b->y_lo < s->room_min[1] || b->y_hi > s->room_max[1]) {
                return false;   /* I16 足跡越出空間平面範圍 */
            }
        }
    }

    return true;
}

/* ---- 共用小解析工具 ---- */

/* 解析 u,v 形式的頂點 token（允許 (u,v) 帶括號）。 */
static bool parse_uv(const char *token, SurfacePoint2 *out)
{
    char buf[64];
    size_t len = strlen(token);

    if (len == 0 || len >= sizeof buf) {
        return false;
    }

    memcpy(buf, token, len + 1);

    /* 脫掉一對外層括號。 */
    if (buf[0] == '(') {
        if (buf[len - 1] != ')') {
            return false;
        }
        buf[len - 1] = '\0';
        memmove(buf, buf + 1, len - 1);
    }

    char *comma = strchr(buf, ',');

    if (comma == NULL) {
        return false;
    }

    *comma = '\0';
    return parse_i64(buf, &out->u) && parse_i64(comma + 1, &out->v);
}

/* 從 tokens[i] 起讀頂點進 loop，直到遇到非 u,v token；回傳下一個 token 位（-1 = 頂點數超上限）。 */
static int parse_loop_vertices(
    char *tokens[],
    int i,
    int count,
    PolygonLoop2 *loop
)
{
    loop->count = 0;

    while (i < count) {
        SurfacePoint2 p;

        if (!parse_uv(tokens[i], &p)) {
            break;
        }

        if (loop->count == POLY_MAX_VERTICES) {
            return -1;
        }

        loop->v[loop->count++] = p;
        ++i;
    }

    return i;
}

/* 從 tokens[i] 起讀 fixity 清單（fixed/F、free/X），長度要剛好等於 loop 邊數。 */
static int parse_loop_fixity(
    char *tokens[],
    int i,
    int count,
    PolygonLoop2 *loop
)
{
    size_t n = 0;

    while (i < count) {
        int fixity;

        if (!lookup_keyword(tokens[i], FIXITY_WORDS, &fixity)) {
            break;
        }

        if (n == POLY_MAX_VERTICES) {
            return -1;
        }

        loop->fixity[n++] = (EdgeFixity)fixity;
        ++i;
    }

    if (n == 0 || n != loop->count) {
        return -1;
    }

    return i;
}

static void loop_fixity_default_fixed(PolygonLoop2 *loop)
{
    for (size_t k = 0; k < POLY_MAX_VERTICES; ++k) {
        loop->fixity[k] = EDGE_FIXED;
    }
}

/* ---- boundary ----
 *
 *   boundary id outline u,v u,v u,v u,v ...
 *             [kind room_plan|wall_elevation|unspecified]
 *             [fixity F F F F]
 *             [hole u,v u,v ... [fixity F F F F]] ...
 *
 * 外輪廓 / 每個孔都是一個正交多邊形環；fixity 一邊一個，預設全 FIXED（公理 I3）。
 * 同名 id = 交易式重宣告（I8）。
 */

/* 讀 boundary id 之後的所有 token 進 candidate；surface 合體簡寫也走這裡。 */
static bool parse_boundary_body(
    const char *path,
    int line_no,
    char *tokens[],
    int i,
    int count,
    SpaceBoundarySurface *candidate
)
{
    memset(candidate, 0, sizeof *candidate);
    candidate->kind = BOUNDARY_UNSPECIFIED;
    loop_fixity_default_fixed(&candidate->outline);

    bool have_outline = false;

    while (i < count) {
        if (strcmp(tokens[i], "outline") == 0) {
            ++i;

            int next = parse_loop_vertices(
                tokens, i, count, &candidate->outline);

            if (next < 0 || next == i) {
                scene_error(path, line_no,
                    "outline 後面要接至少四個 u,v 頂點");
                return false;
            }

            have_outline = true;
            i = next;
        } else if (strcmp(tokens[i], "fixity") == 0) {
            ++i;

            /* 修飾最後讀到的環：有孔就修孔，否則修外輪廓。 */
            PolygonLoop2 *loop = candidate->hole_count > 0
                ? &candidate->holes[candidate->hole_count - 1]
                : &candidate->outline;

            int next = parse_loop_fixity(tokens, i, count, loop);

            if (next < 0) {
                scene_error(path, line_no,
                    "fixity 的數量要跟邊數一樣（不寫就是全 FIXED）");
                return false;
            }

            i = next;
        } else if (strcmp(tokens[i], "kind") == 0) {
            ++i;

            int kind;

            if (i >= count ||
                !lookup_keyword(tokens[i], BOUNDARY_KIND_WORDS, &kind)) {
                scene_error(path, line_no,
                    "kind 只能寫 room_plan / wall_elevation / unspecified");
                return false;
            }

            candidate->kind = (BoundaryKind)kind;
            ++i;
        } else if (strcmp(tokens[i], "hole") == 0) {
            ++i;

            if (candidate->hole_count == POLY_MAX_HOLES) {
                scene_error(path, line_no, "孔的數量超過上限");
                return false;
            }

            PolygonLoop2 *hole = &candidate->holes[candidate->hole_count];
            loop_fixity_default_fixed(hole);

            int next = parse_loop_vertices(tokens, i, count, hole);

            if (next < 0 || next == i) {
                scene_error(path, line_no,
                    "hole 後面要接至少四個 u,v 頂點");
                return false;
            }

            ++candidate->hole_count;
            i = next;
        } else {
            scene_error(path, line_no,
                "boundary 只認得 outline / fixity / kind / hole");
            return false;
        }
    }

    if (!have_outline) {
        scene_error(path, line_no, "boundary 需要 outline");
        return false;
    }

    if (!boundary_is_valid(candidate)) {
        scene_error(path, line_no,
            "邊界面輪廓不合法：邊要軸平行、不零長、不自交；"
            "孔要在外輪廓內且互不重疊");
        return false;
    }

    return true;
}

static bool apply_boundary_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t id;

    if (!parse_u32(tokens[1], &id)) {
        scene_error(path, line_no, "boundary 的 id 不是有效的整數");
        return false;
    }

    SpaceBoundarySurface candidate;

    if (!parse_boundary_body(path, line_no, tokens, 2, count, &candidate)) {
        return false;
    }

    candidate.id = id;

    for (size_t i = 0; i < world->boundary_count; ++i) {
        if (world->boundaries[i].id == id) {
            if (!world_replace_object(
                    world, &world->boundaries[i],
                    &candidate, sizeof candidate)) {
                scene_error(path, line_no,
                    "重宣告後有物件失效（承載面/參考線/角材/空間沒全過）");
                return false;
            }
            return true;
        }
    }

    if (world->boundary_count == WORLD_MAX_BOUNDARIES) {
        scene_error(path, line_no, "邊界面的數量超過上限");
        return false;
    }

    world->boundaries[world->boundary_count++] = candidate;
    return true;
}

/* ---- placement ----
 *
 *   placement id on boundary 邊id origin x y z u 軸 v 軸
 *   placement id origin x y z u 軸 v 軸 rect min_u min_v max_u max_v
 *
 * 掛邊界面時有效範圍由邊界面輪廓推導；不掛時 rect 必填。
 * 同名 id = 交易式重宣告。
 */
static bool parse_placement_body(
    const char *path,
    int line_no,
    char *tokens[],
    int i,
    int count,
    PlacementSurface *candidate
)
{
    memset(candidate, 0, sizeof *candidate);
    candidate->boundary_id = 0;

    bool have_origin = false;
    bool have_u = false;
    bool have_v = false;
    bool have_rect = false;

    while (i < count) {
        if (strcmp(tokens[i], "on") == 0) {
            ++i;

            if (i >= count || strcmp(tokens[i], "boundary") != 0) {
                scene_error(path, line_no, "on 後面要接 boundary");
                return false;
            }
            ++i;

            if (i >= count || !parse_u32(tokens[i], &candidate->boundary_id)) {
                scene_error(path, line_no,
                    "on boundary 後面要接邊界面 id");
                return false;
            }
            ++i;
        } else if (strcmp(tokens[i], "origin") == 0) {
            ++i;

            if (i + 2 >= count ||
                !parse_i64(tokens[i], &candidate->frame.origin.x) ||
                !parse_i64(tokens[i + 1], &candidate->frame.origin.y) ||
                !parse_i64(tokens[i + 2], &candidate->frame.origin.z)) {
                scene_error(path, line_no,
                    "origin 後面要接三個整數座標");
                return false;
            }
            have_origin = true;
            i += 3;
        } else if (strcmp(tokens[i], "u") == 0) {
            ++i;
            if (i >= count ||
                !lookup_axis(tokens[i], &candidate->frame.axis_u)) {
                scene_error(path, line_no, "u 軸只能寫 +x -x +y -y +z -z");
                return false;
            }
            have_u = true;
            ++i;
        } else if (strcmp(tokens[i], "v") == 0) {
            ++i;
            if (i >= count ||
                !lookup_axis(tokens[i], &candidate->frame.axis_v)) {
                scene_error(path, line_no, "v 軸只能寫 +x -x +y -y +z -z");
                return false;
            }
            have_v = true;
            ++i;
        } else if (strcmp(tokens[i], "rect") == 0) {
            ++i;
            Coord r[4];

            if (i + 3 >= count) {
                scene_error(path, line_no, "rect 後面要接四個整數");
                return false;
            }
            for (int k = 0; k < 4; ++k) {
                if (!parse_i64(tokens[i + k], &r[k])) {
                    scene_error(path, line_no, "rect 後面要接四個整數");
                    return false;
                }
            }
            candidate->rect.min_u = r[0];
            candidate->rect.min_v = r[1];
            candidate->rect.max_u = r[2];
            candidate->rect.max_v = r[3];
            have_rect = true;
            i += 4;
        } else {
            scene_error(path, line_no,
                "placement 只認得 on / origin / u / v / rect");
            return false;
        }
    }

    if (!have_origin || !have_u || !have_v) {
        scene_error(path, line_no,
            "placement 需要 origin、u、v 三個欄位");
        return false;
    }

    /* rect 與否由呼叫端決定：placement 指令要求它，
     * surface 合體簡寫之後才補 boundary_id。 */
    (void)have_rect;

    candidate->frame.normal = vector_cross(
        candidate->frame.axis_u, candidate->frame.axis_v);

    if (!surface_frame_is_valid(&candidate->frame)) {
        scene_error(path, line_no, "u 軸與 v 軸必須互相垂直");
        return false;
    }

    return true;
}

static bool apply_placement_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t id;

    if (!parse_u32(tokens[1], &id)) {
        scene_error(path, line_no, "placement 的 id 不是有效的整數");
        return false;
    }

    PlacementSurface candidate;

    if (!parse_placement_body(path, line_no, tokens, 2, count, &candidate)) {
        return false;
    }

    candidate.id = id;

    if (candidate.boundary_id == 0 &&
        (candidate.rect.min_u >= candidate.rect.max_u ||
         candidate.rect.min_v >= candidate.rect.max_v)) {
        scene_error(path, line_no,
            "不掛邊界面的承載面需要 rect min_u min_v max_u max_v");
        return false;
    }

    if (candidate.boundary_id != 0 &&
        world_find_boundary(world, candidate.boundary_id) == NULL) {
        scene_error(path, line_no, "on boundary 指的邊界面不存在");
        return false;
    }

    for (size_t i = 0; i < world->placement_count; ++i) {
        if (world->placements[i].id == id) {
            if (!world_replace_object(
                    world, &world->placements[i],
                    &candidate, sizeof candidate)) {
                scene_error(path, line_no,
                    "重宣告後有物件失效（參考線/角材/空間沒全過）");
                return false;
            }
            return true;
        }
    }

    if (world->placement_count == WORLD_MAX_PLACEMENTS) {
        scene_error(path, line_no, "承載面的數量超過上限");
        return false;
    }

    world->placements[world->placement_count++] = candidate;
    return true;
}

/* ---- surface 合體簡寫 ----
 *
 *   surface id on boundary 邊id origin x y z u 軸 v 軸
 *   surface id origin x y z u 軸 v 軸 rect min_u min_v max_u max_v
 *   surface id origin x y z u 軸 v 軸 outline u,v u,v ... [fixity ...] [hole ...]
 *
 * 前兩種 = placement 指令的另一個拼法；
 * 第三種一行同時建邊界面 + 掛它的承載面，兩者共用這個 id。
 * 物件層永遠是兩個物件（公理層決策 #6），簡寫只是少打一行。
 */
static bool apply_surface_combined_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t id;

    if (!parse_u32(tokens[1], &id)) {
        scene_error(path, line_no, "surface 的 id 不是有效的整數");
        return false;
    }

    /* 掃一下有沒有 outline：有 = 合體，沒有 = 等同 placement。 */
    bool has_outline = false;

    for (int i = 2; i < count; ++i) {
        if (strcmp(tokens[i], "outline") == 0) {
            has_outline = true;
            break;
        }
    }

    if (!has_outline) {
        /* 等同 placement：借 placement 的解析，把 tokens[0] 當作沒看見。 */
        PlacementSurface candidate;

        if (!parse_placement_body(
                path, line_no, tokens, 2, count, &candidate)) {
            return false;
        }

        candidate.id = id;

        if (candidate.boundary_id == 0 &&
            (candidate.rect.min_u >= candidate.rect.max_u ||
             candidate.rect.min_v >= candidate.rect.max_v)) {
            scene_error(path, line_no,
                "不掛邊界面的承載面需要 rect min_u min_v max_u max_v");
            return false;
        }

        if (candidate.boundary_id != 0 &&
            world_find_boundary(world, candidate.boundary_id) == NULL) {
            scene_error(path, line_no, "on boundary 指的邊界面不存在");
            return false;
        }

        for (size_t i = 0; i < world->placement_count; ++i) {
            if (world->placements[i].id == id) {
                if (!world_replace_object(
                        world, &world->placements[i],
                        &candidate, sizeof candidate)) {
                    scene_error(path, line_no,
                        "重宣告後有物件失效");
                    return false;
                }
                return true;
            }
        }

        if (world->placement_count == WORLD_MAX_PLACEMENTS) {
            scene_error(path, line_no, "承載面的數量超過上限");
            return false;
        }

        world->placements[world->placement_count++] = candidate;
        return true;
    }

    /* 合體：先把 token 拆成「placement 段」與「boundary 段」。
     * outline/fixity/kind/hole 歸 boundary，其餘歸 placement。
     * 做法：走一遍 token，outline 起手的段與 fixity/kind/hole 起手的段收進
     * boundary 段；on/origin/u/v/rect 歸 placement 段。
     */
    char *b_tokens[SCENE_MAX_TOKENS];
    char *p_tokens[SCENE_MAX_TOKENS];
    int b_count = 0;
    int p_count = 0;

    for (int i = 2; i < count; ++i) {
        const char *t = tokens[i];

        if (strcmp(t, "outline") == 0 || strcmp(t, "fixity") == 0 ||
            strcmp(t, "kind") == 0 || strcmp(t, "hole") == 0) {
            /* boundary 段關鍵字：收關鍵字本身，後面頂點/fixity/子句由
             * parse_boundary_body 自己掃，但我們需要知道哪些 token 屬於它。
             * 簡化：boundary 段關鍵字出現後，直到下一個 placement 關鍵字
             * （on/origin/u/v/rect）之前的 token 全部歸 boundary。 */
            b_tokens[b_count++] = tokens[i];
            ++i;

            while (i < count) {
                const char *s = tokens[i];
                if (strcmp(s, "on") == 0 || strcmp(s, "origin") == 0 ||
                    strcmp(s, "u") == 0 || strcmp(s, "v") == 0 ||
                    strcmp(s, "rect") == 0) {
                    --i;
                    break;
                }
                if (strcmp(s, "outline") == 0 || strcmp(s, "fixity") == 0 ||
                    strcmp(s, "kind") == 0 || strcmp(s, "hole") == 0) {
                    --i;
                    break;
                }
                if (b_count == SCENE_MAX_TOKENS) {
                    scene_error(path, line_no, "指令太長");
                    return false;
                }
                b_tokens[b_count++] = tokens[i];
                ++i;
            }
        } else {
            /* placement 段：關鍵字本身 + 它的固定參數數量。 */
            int arity = 0;
            if (strcmp(t, "on") == 0)      arity = 2; /* on boundary id */
            else if (strcmp(t, "origin") == 0) arity = 3;
            else if (strcmp(t, "u") == 0 || strcmp(t, "v") == 0) arity = 1;
            else if (strcmp(t, "rect") == 0) arity = 4;
            else {
                scene_error(path, line_no, "surface 指令裡有不認得的 token");
                return false;
            }

            if (p_count + 1 + arity >= SCENE_MAX_TOKENS ||
                i + arity >= count) {
                scene_error(path, line_no, "surface 指令欄位不完整");
                return false;
            }

            p_tokens[p_count++] = tokens[i];
            for (int k = 0; k < arity; ++k) {
                p_tokens[p_count++] = tokens[++i];
            }
        }
    }

    /* 建 boundary candidate。 */
    SpaceBoundarySurface boundary;

    if (!parse_boundary_body(path, line_no, b_tokens, 0, b_count, &boundary)) {
        return false;
    }
    boundary.id = id;

    /* 建 placement candidate：frame 段 + on boundary id。 */
    PlacementSurface placement;

    if (!parse_placement_body(path, line_no, p_tokens, 0, p_count, &placement)) {
        return false;
    }
    placement.id = id;
    placement.boundary_id = id;

    /* 兩個一起進 World：任一失敗整筆不算。先檢查容量再寫。 */
    bool replace_b = false;
    bool replace_p = false;

    for (size_t i = 0; i < world->boundary_count; ++i) {
        if (world->boundaries[i].id == id) { replace_b = true; break; }
    }
    for (size_t i = 0; i < world->placement_count; ++i) {
        if (world->placements[i].id == id) { replace_p = true; break; }
    }

    if (!replace_b && world->boundary_count == WORLD_MAX_BOUNDARIES) {
        scene_error(path, line_no, "邊界面的數量超過上限");
        return false;
    }
    if (!replace_p && world->placement_count == WORLD_MAX_PLACEMENTS) {
        scene_error(path, line_no, "承載面的數量超過上限");
        return false;
    }

    /* 借用 world_replace_object 的交易語意：分兩步，第二步失敗要還原第一步。 */
    World backup = *world;

    if (replace_b) {
        for (size_t i = 0; i < world->boundary_count; ++i) {
            if (world->boundaries[i].id == id) {
                world->boundaries[i] = boundary;
                break;
            }
        }
    } else {
        world->boundaries[world->boundary_count++] = boundary;
    }

    if (replace_p) {
        for (size_t i = 0; i < world->placement_count; ++i) {
            if (world->placements[i].id == id) {
                world->placements[i] = placement;
                break;
            }
        }
    } else {
        world->placements[world->placement_count++] = placement;
    }

    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no,
            "重宣告後有物件失效（參考線/角材/空間沒全過）");
        return false;
    }

    return true;
}

/* guide <id> <承載面id> <u|v> <offset>：offset 合法範圍由承載面決定。 */
static bool apply_guide_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    (void)count;

    if (world->guide_count == WORLD_MAX_GUIDES) {
        scene_error(path, line_no, "參考線的數量超過上限");
        return false;
    }

    GuideLine guide;
    int direction;

    if (!parse_u32(tokens[1], &guide.id)) {
        scene_error(path, line_no, "guide 的 id 不是有效的整數");
        return false;
    }

    for (size_t i = 0; i < world->guide_count; ++i) {
        if (world->guides[i].id == guide.id) {
            scene_error(path, line_no, "這個 guide id 已經用過了");
            return false;
        }
    }

    if (!parse_u32(tokens[2], &guide.placement_id)) {
        scene_error(path, line_no, "guide 的承載面 id 不是有效的整數");
        return false;
    }

    const PlacementSurface *placement =
        world_find_placement(world, guide.placement_id);

    if (placement == NULL) {
        scene_error(path, line_no, "guide 指的承載面不存在");
        return false;
    }

    if (!lookup_keyword(tokens[3], GUIDE_DIRECTION_WORDS, &direction)) {
        scene_error(path, line_no, "guide 的方向只能寫 u 或 v");
        return false;
    }

    guide.direction = (GuideDirection)direction;

    if (!parse_i64(tokens[4], &guide.offset)) {
        scene_error(path, line_no, "guide 的 offset 不是有效的整數");
        return false;
    }

    const SpaceBoundarySurface *boundary =
        world_find_boundary(world, placement->boundary_id);

    if (!guide_offset_in_range(
            placement, boundary, guide.direction, guide.offset)) {
        scene_error(path, line_no, "guide 的 offset 落在承載面範圍之外");
        return false;
    }

    world->guides[world->guide_count++] = guide;
    return true;
}

/*
 * timber 兩種語法（公理 O3：明寫長度與 auto 是兩種建構語意）：
 *
 *   timber id L A B   明寫長度：只能配 at / at-guides 放置
 *   timber id A B     auto：長度由 place 當下的合法區間推導，
 *                     只能配 at-grid / at-edge 放置
 */
static bool apply_timber_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    if (world->timber_count == WORLD_MAX_TIMBERS) {
        scene_error(path, line_no, "角材的數量超過上限");
        return false;
    }

    uint32_t id;
    Coord length = 0, size_a, size_b;
    bool auto_length;

    if (count == 5) {
        auto_length = false;
        if (!parse_u32(tokens[1], &id) ||
            !parse_i64(tokens[2], &length) ||
            !parse_i64(tokens[3], &size_a) ||
            !parse_i64(tokens[4], &size_b)) {
            scene_error(path, line_no,
                "timber 需要：id 長度 A尺寸 B尺寸（都是整數）");
            return false;
        }
    } else if (count == 4) {
        auto_length = true;
        if (!parse_u32(tokens[1], &id) ||
            !parse_i64(tokens[2], &size_a) ||
            !parse_i64(tokens[3], &size_b)) {
            scene_error(path, line_no,
                "timber auto 需要：id A尺寸 B尺寸（都是整數）");
            return false;
        }
    } else {
        scene_error(path, line_no,
            "timber 需要：id 長度 A尺寸 B尺寸，或 id A尺寸 B尺寸（auto）");
        return false;
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        if (world->timbers[i].id == id) {
            scene_error(path, line_no, "這個 timber id 已經用過了");
            return false;
        }
    }

    if (!timber_construct(id, length, size_a, size_b, auto_length,
            &world->timbers[world->timber_count])) {
        scene_error(path, line_no, "角材的長度與 A/B 尺寸都要大於 0");
        return false;
    }

    ++world->timber_count;
    return true;
}

/* 承載面上的參考網格查找。 */
static const ReferenceGrid *world_find_grid(const World *world, uint32_t id)
{
    for (size_t i = 0; i < world->grid_count; ++i) {
        if (world->grids[i].id == id) {
            return &world->grids[i];
        }
    }

    return NULL;
}

/*
 * at-edge 的邊參照：e3 = 外輪廓邊 index 3；h1e2 = 孔 1 的邊 index 2。
 * 索引一律 0-based，跟 fixity 清單的順位一致。
 */
static bool parse_edge_ref(const char *token, int *out_hole, int *out_edge)
{
    if (token == NULL || out_hole == NULL || out_edge == NULL) {
        return false;
    }

    const char *p = token;

    if (*p == 'e') {
        ++p;
        *out_hole = -1;
    } else if (*p == 'h') {
        ++p;
        Coord hole;

        const char *e_at = strchr(p, 'e');
        if (e_at == NULL || e_at == p) {
            return false;
        }

        char buf[16];
        size_t n = (size_t)(e_at - p);
        if (n >= sizeof buf) {
            return false;
        }
        memcpy(buf, p, n);
        buf[n] = '\0';

        if (!parse_i64(buf, &hole) || hole < 0) {
            return false;
        }

        *out_hole = (int)hole;
        p = e_at + 1;
    } else {
        return false;
    }

    Coord edge;
    if (!parse_i64(p, &edge) || edge < 0) {
        return false;
    }

    *out_edge = (int)edge;
    return true;
}

/*
 * 由 footprint 矩形 + 方向反推 A0 錨角（局部原點角落）。
 * 長度軸分量非零時用它定錨角，否則用 A 軸分量。
 */
static SurfacePoint2 anchor_corner_from_rect(
    const PlacementSurface *surface,
    int length_direction,
    int depth_side,
    const SurfaceRegion2 *rect
)
{
    Vector3 axis_length = surface_direction_vector(
        surface, (SurfaceDirection)length_direction);
    Vector3 axis_b =
        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL
            ? surface->frame.normal
            : vector_negate(surface->frame.normal);
    Vector3 axis_a = vector_cross(axis_b, axis_length);

    Coord lu = vector_dot(axis_length, surface->frame.axis_u);
    Coord lv = vector_dot(axis_length, surface->frame.axis_v);
    Coord au = vector_dot(axis_a, surface->frame.axis_u);
    Coord av = vector_dot(axis_a, surface->frame.axis_v);

    Coord du = lu != 0 ? lu : au;
    Coord dv = lv != 0 ? lv : av;

    return (SurfacePoint2){
        du > 0 ? rect->min_u : rect->max_u,
        dv > 0 ? rect->min_v : rect->max_v
    };
}

/*
 * grid <id> on <承載面id> u c1 [c2 ...] [v c1 [c2 ...]]
 *
 * 一座網格 = u 座標集合 + v 座標集合（公理 G1–G4）。
 * 同一 id 可寫兩行分別補 u / v 集合（同座標軸只能宣告一次）；
 * 每片承載面最多一座網格（與 TS 的 E_GRID_UNIQUE 同規則）。
 */
static bool apply_grid_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t grid_id;

    if (!parse_u32(tokens[1], &grid_id)) {
        scene_error(path, line_no, "grid 的 id 不是有效的整數");
        return false;
    }

    if (count < 4 || strcmp(tokens[2], "on") != 0) {
        scene_error(path, line_no, "grid 需要：id on 承載面id u|v 座標...");
        return false;
    }

    uint32_t placement_id;

    if (!parse_u32(tokens[3], &placement_id)) {
        scene_error(path, line_no, "grid 的承載面 id 不是有效的整數");
        return false;
    }

    const PlacementSurface *placement =
        world_find_placement(world, placement_id);

    if (placement == NULL) {
        scene_error(path, line_no, "grid 指的承載面不存在");
        return false;
    }

    /* 找既有同 id 網格（可補另一軸），或建新的。
     * 一律在副本上改，驗完才回寫——失敗不留半成品（I8）。 */
    ReferenceGrid candidate = { 0 };
    ReferenceGrid *existing = NULL;

    for (size_t i = 0; i < world->grid_count; ++i) {
        if (world->grids[i].id == grid_id) {
            existing = &world->grids[i];
            break;
        }
    }

    if (existing != NULL && existing->placement_id != placement_id) {
        scene_error(path, line_no, "這個 grid id 已經用在別的承載面");
        return false;
    }

    if (existing == NULL) {
        /* 一面一格：不同 id 落在同一承載面 → 拒絕。 */
        for (size_t i = 0; i < world->grid_count; ++i) {
            if (world->grids[i].placement_id == placement_id) {
                scene_error(path, line_no,
                    "這片承載面已經有一座網格（一面一格）");
                return false;
            }
        }

        if (world->grid_count == WORLD_MAX_GRIDS) {
            scene_error(path, line_no, "網格的數量超過上限");
            return false;
        }

        candidate.id = grid_id;
        candidate.placement_id = placement_id;
    } else {
        candidate = *existing;
    }

    ReferenceGrid *grid = &candidate;

    /* 逐段解析：u|v 開頭，後面跟一串座標直到下一個 u/v 或行尾。 */
    int i = 4;
    size_t filled = 0;

    while (i < count) {
        int axis;

        if (strcmp(tokens[i], "u") == 0) {
            axis = 0;
        } else if (strcmp(tokens[i], "v") == 0) {
            axis = 1;
        } else {
            scene_error(path, line_no,
                "grid 的座標段要用 u 或 v 開頭");
            return false;
        }
        ++i;

        if (i >= count) {
            scene_error(path, line_no, "grid 的座標段至少要一個座標");
            return false;
        }

        if (axis == 0 && grid->u_count > 0) {
            scene_error(path, line_no, "grid 的 u 座標集合只能宣告一次");
            return false;
        }
        if (axis == 1 && grid->v_count > 0) {
            scene_error(path, line_no, "grid 的 v 座標集合只能宣告一次");
            return false;
        }

        while (i < count &&
               strcmp(tokens[i], "u") != 0 &&
               strcmp(tokens[i], "v") != 0) {
            Coord c;

            if (!parse_i64(tokens[i], &c)) {
                scene_error(path, line_no, "grid 的座標不是有效的整數");
                return false;
            }

            if (axis == 0) {
                if (grid->u_count == GRID_MAX_LINES) {
                    scene_error(path, line_no, "grid u 座標超過上限");
                    return false;
                }
                grid->u_coords[grid->u_count++] = c;
            } else {
                if (grid->v_count == GRID_MAX_LINES) {
                    scene_error(path, line_no, "grid v 座標超過上限");
                    return false;
                }
                grid->v_coords[grid->v_count++] = c;
            }

            ++i;
            ++filled;
        }
    }

    if (filled == 0) {
        scene_error(path, line_no, "grid 至少要一個座標");
        return false;
    }

    if (!grid_is_valid(
            grid, placement,
            world_find_boundary(world, placement->boundary_id))) {
        scene_error(path, line_no,
            "grid 座標不合法：要嚴格遞增、且落在承載面外接範圍內");
        return false;
    }

    /* 全部驗完才回寫：合併模式覆蓋原格，新網格到這裡才入列。 */
    if (existing != NULL) {
        *existing = candidate;
    } else {
        world->grids[world->grid_count++] = candidate;
    }

    return true;
}

/*
 * place <角材id> on <承載面id> <錨法> [through c] <長度方向> <深度側>
 *
 * 錨法四種，兩兩一組：
 *
 *   明寫長度角材（timber id L A B）：
 *     at u v                      直接給錨點的局部座標（A0 角點）
 *     at-guides <線id> <線id>     兩條參考線交點當錨點（place 當下凍結）
 *
 *   auto 角材（timber id A B）：
 *     at-grid <網id> u|v <索引>   格線座標 = 角材中心線，長度自動推導
 *     at-edge e<i> | h<i>e<j>     貼邊放（輪廓邊或孔邊），長度自動推導
 *
 *   兩種都可在方向前加 through <座標> 指定要用哪一段合法區間。
 *
 * 凍結語意（公理層決策 #5 + O3）：錨點與推導長度在 place 當下
 * 凍結，之後移動參考線／網格不連動，重驗只檢查凍結結果仍合法。
 */
static bool apply_place_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t timber_id;

    if (!parse_u32(tokens[1], &timber_id)) {
        scene_error(path, line_no, "place 的角材 id 不是有效的整數");
        return false;
    }

    Timber *timber = NULL;

    for (size_t i = 0; i < world->timber_count; ++i) {
        if (world->timbers[i].id == timber_id) {
            timber = &world->timbers[i];
            break;
        }
    }

    if (timber == NULL) {
        scene_error(path, line_no, "place 指的角材不存在");
        return false;
    }

    if (timber->placed) {
        scene_error(path, line_no, "這支角材已經放過了");
        return false;
    }

    /* place t on s ... ：on 與承載面 id 固定在 token 2、3。 */
    if (count < 4 || strcmp(tokens[2], "on") != 0) {
        scene_error(path, line_no, "place 需要：角材id on 承載面id ...");
        return false;
    }

    uint32_t placement_id;

    if (!parse_u32(tokens[3], &placement_id)) {
        scene_error(path, line_no, "place 的承載面 id 不是有效的整數");
        return false;
    }

    const PlacementSurface *placement =
        world_find_placement(world, placement_id);

    if (placement == NULL) {
        scene_error(path, line_no, "place 指的承載面不存在");
        return false;
    }

    const SpaceBoundarySurface *boundary =
        world_find_boundary(world, placement->boundary_id);

    int anchor_kind = -1;
    SurfacePoint2 anchor_uv = { 0, 0 };
    bool has_through = false;
    Coord through = 0;
    uint32_t ref_grid = 0;
    int ref_grid_axis = -1;
    int ref_grid_index = -1;
    int ref_hole = -1;
    int ref_edge = -1;
    Coord centerline = 0;
    int i = 0;

    if (count >= 5 && strcmp(tokens[4], "at") == 0) {
        /* place t on s at u v dir side */
        if (count != 9) {
            scene_error(path, line_no,
                "place at 需要：角材id on 承載面id at u v 長度方向 深度側");
            return false;
        }

        if (!parse_i64(tokens[5], &anchor_uv.u) ||
            !parse_i64(tokens[6], &anchor_uv.v)) {
            scene_error(path, line_no, "place at 的 u / v 不是有效的整數");
            return false;
        }

        anchor_kind = ANCHOR_AT;
        i = 7;
    } else if (count >= 5 && strcmp(tokens[4], "at-guides") == 0) {
        /* place t on s at-guides g1 g2 dir side */
        if (count != 9) {
            scene_error(path, line_no,
                "place at-guides 需要：角材id on 承載面id at-guides 線1 線2 長度方向 深度側");
            return false;
        }

        uint32_t guide_a_id, guide_b_id;

        if (!parse_u32(tokens[5], &guide_a_id) ||
            !parse_u32(tokens[6], &guide_b_id)) {
            scene_error(path, line_no, "place at-guides 的線 id 不是有效的整數");
            return false;
        }

        const GuideLine *guide_a = NULL;
        const GuideLine *guide_b = NULL;

        for (size_t g = 0; g < world->guide_count; ++g) {
            if (world->guides[g].id == guide_a_id) guide_a = &world->guides[g];
            if (world->guides[g].id == guide_b_id) guide_b = &world->guides[g];
        }

        if (guide_a == NULL || guide_b == NULL) {
            scene_error(path, line_no, "place at-guides 指的參考線不存在");
            return false;
        }

        if (!guide_line_intersection(
                placement, boundary, guide_a, guide_b, &anchor_uv)) {
            scene_error(path, line_no,
                "這兩條參考線不相交（方向相同、不同面，或交點在有效區域外）");
            return false;
        }

        anchor_kind = ANCHOR_AT_GUIDES;
        i = 7;
    } else if (count >= 5 && strcmp(tokens[4], "at-grid") == 0) {
        /* place t on s at-grid g u|v n [through c] dir side */
        if (count != 10 && count != 12) {
            scene_error(path, line_no,
                "place at-grid 需要：角材id on 承載面id at-grid 網id u|v 索引 [through 座標] 長度方向 深度側");
            return false;
        }

        if (!parse_u32(tokens[5], &ref_grid)) {
            scene_error(path, line_no, "place at-grid 的網格 id 不是有效的整數");
            return false;
        }

        const ReferenceGrid *grid = NULL;

        for (size_t g = 0; g < world->grid_count; ++g) {
            if (world->grids[g].id == ref_grid) {
                grid = &world->grids[g];
                break;
            }
        }

        if (grid == NULL || grid->placement_id != placement_id) {
            scene_error(path, line_no, "place at-grid 指的網格不在這片承載面上");
            return false;
        }

        Coord grid_index;

        if (strcmp(tokens[6], "u") == 0) {
            ref_grid_axis = 0;
        } else if (strcmp(tokens[6], "v") == 0) {
            ref_grid_axis = 1;
        } else {
            scene_error(path, line_no, "place at-grid 的座標軸只能寫 u 或 v");
            return false;
        }

        if (!parse_i64(tokens[7], &grid_index) ||
            grid_index < 0 ||
            (ref_grid_axis == 0 &&
             (size_t)grid_index >= grid->u_count) ||
            (ref_grid_axis == 1 &&
             (size_t)grid_index >= grid->v_count)) {
            scene_error(path, line_no, "place at-grid 的格線索引超出範圍");
            return false;
        }

        ref_grid_index = (int)grid_index;
        centerline = ref_grid_axis == 0
            ? grid->u_coords[grid_index]
            : grid->v_coords[grid_index];

        anchor_kind = ANCHOR_AT_GRID;
        i = 8;
    } else if (count >= 5 && strcmp(tokens[4], "at-edge") == 0) {
        /* place t on s at-edge e3|h1e2 [through c] dir side */
        if (count != 8 && count != 10) {
            scene_error(path, line_no,
                "place at-edge 需要：角材id on 承載面id at-edge e索引|h孔索引e邊索引 [through 座標] 長度方向 深度側");
            return false;
        }

        if (boundary == NULL) {
            scene_error(path, line_no,
                "at-edge 需要承載面掛邊界面（自帶矩形沒有邊）");
            return false;
        }

        if (!parse_edge_ref(tokens[5], &ref_hole, &ref_edge)) {
            scene_error(path, line_no,
                "at-edge 的邊參照寫法是 e3 或 h1e2");
            return false;
        }

        const PolygonLoop2 *loop =
            ref_hole < 0 ? &boundary->outline : NULL;

        if (ref_hole >= 0) {
            if ((size_t)ref_hole >= boundary->hole_count) {
                scene_error(path, line_no, "at-edge 的孔索引超出範圍");
                return false;
            }
            loop = &boundary->holes[ref_hole];
        }

        if ((size_t)ref_edge >= loop->count) {
            scene_error(path, line_no, "at-edge 的邊索引超出範圍");
            return false;
        }

        anchor_kind = ANCHOR_AT_EDGE;
        i = 6;
    } else {
        scene_error(path, line_no,
            "place 的錨法只認得 at、at-guides、at-grid、at-edge");
        return false;
    }

    /* 可選 through <座標>：長度軸上的區間選擇器。 */
    if (anchor_kind == ANCHOR_AT_GRID || anchor_kind == ANCHOR_AT_EDGE) {
        if (i + 2 <= count && strcmp(tokens[i], "through") == 0) {
            if (!parse_i64(tokens[i + 1], &through)) {
                scene_error(path, line_no, "through 的座標不是有效的整數");
                return false;
            }
            has_through = true;
            i += 2;
        }
    }

    int length_direction, depth_side;

    if (!lookup_keyword(tokens[i], LENGTH_DIRECTION_WORDS, &length_direction)) {
        scene_error(path, line_no, "長度方向只能寫 +u -u +v -v");
        return false;
    }

    if (!lookup_keyword(tokens[i + 1], DEPTH_SIDE_WORDS, &depth_side)) {
        scene_error(path, line_no, "深度側只能寫 +n 或 -n");
        return false;
    }

    bool along_v =
        length_direction == SURFACE_DIRECTION_POS_V ||
        length_direction == SURFACE_DIRECTION_NEG_V;

    /* 語法配對（公理 O3）：auto 角材 ↔ 中心線錨法；明寫 ↔ 角點錨法。 */
    bool auto_anchor =
        anchor_kind == ANCHOR_AT_GRID || anchor_kind == ANCHOR_AT_EDGE;

    if (auto_anchor && !timber->auto_length) {
        scene_error(path, line_no,
            "明寫長度角材只能用 at 或 at-guides 放置");
        return false;
    }

    if (!auto_anchor && timber->auto_length) {
        scene_error(path, line_no,
            "auto 角材（timber id A B）只能用 at-grid 或 at-edge 放置");
        return false;
    }

    if (auto_anchor) {
        /*
         * 由錨法決定寬度範圍與接觸範圍，再推導跨距。
         *   at-grid：中線 = 格線座標，寬度 = 中線 ± ⌊w/2⌋ / ⌈w/2⌉
         *           （奇數寬多的 1mm 一律在 +cross 側——公理，不是猜）。
         *   at-edge：footprint 貼齊邊、向面內延伸一個寬度；
         *           邊的長度軸範圍是接觸範圍（區間可超出，必須重疊）。
         */
        Coord cross_lo, cross_hi;
        bool has_contact = false;
        Coord contact_lo = 0, contact_hi = 0;
        Coord w = timber->size_a;

        if (anchor_kind == ANCHOR_AT_GRID) {
            /* 座標軸必須 ⊥ 長度軸：u 座標線沿 V 走 → 配沿 V 的料，
             * v 座標線沿 U 走 → 配沿 U 的料。方向不垂直 → 拒絕。 */
            if ((ref_grid_axis == 0) != along_v) {
                scene_error(path, line_no,
                    "格線座標軸必須與角材長度方向垂直"
                    "（u 座標線配 ±v，v 座標線配 ±u）");
                return false;
            }

            cross_lo = centerline - w / 2;
            cross_hi = cross_lo + w;
        } else {
            /* at-edge：邊必須與長度方向平行，footprint 貼邊向內。 */
            const PolygonLoop2 *loop =
                ref_hole < 0
                    ? &boundary->outline
                    : &boundary->holes[ref_hole];

            SurfaceSegment2 edge_seg;
            SurfacePoint2 outward;

            loop_get_edge_segment(loop, (size_t)ref_edge, &edge_seg);
            loop_edge_outward_normal(loop, (size_t)ref_edge, &outward);

            bool edge_runs_v = edge_seg.start.u == edge_seg.end.u;

            if (edge_runs_v != along_v) {
                scene_error(path, line_no,
                    "at-edge 的邊必須與角材長度方向平行");
                return false;
            }

            /* 材料側：外輪廓取外向法線的反側（-outward）；
             * 孔的外向法線本身已指向材料側（+outward）。 */

            if (along_v) {
                /* 直立邊：fixed u，跨 v；寬度沿 u 向材料側。 */
                Coord c = edge_seg.start.u;
                Coord in = ref_hole < 0 ? -outward.u : outward.u;

                if (in > 0) {
                    cross_lo = c;
                    cross_hi = c + w;
                } else if (in < 0) {
                    cross_lo = c - w;
                    cross_hi = c;
                } else {
                    scene_error(path, line_no, "at-edge 的邊方向異常");
                    return false;
                }

                contact_lo = coord_min(edge_seg.start.v, edge_seg.end.v);
                contact_hi = coord_max(edge_seg.start.v, edge_seg.end.v);
            } else {
                Coord c = edge_seg.start.v;
                Coord in = ref_hole < 0 ? -outward.v : outward.v;

                if (in > 0) {
                    cross_lo = c;
                    cross_hi = c + w;
                } else if (in < 0) {
                    cross_lo = c - w;
                    cross_hi = c;
                } else {
                    scene_error(path, line_no, "at-edge 的邊方向異常");
                    return false;
                }

                contact_lo = coord_min(edge_seg.start.u, edge_seg.end.u);
                contact_hi = coord_max(edge_seg.start.u, edge_seg.end.u);
            }

            has_contact = true;
        }

        char span_err[200] = "";
        Coord span_start, span_end;
        SpanStatus status = resolve_auto_span(
            world, placement, boundary, along_v,
            cross_lo, cross_hi,
            has_contact, contact_lo, contact_hi,
            has_through, through,
            &span_start, &span_end,
            span_err, sizeof span_err);

        if (status != SPAN_OK) {
            char msg[256];
            snprintf(msg, sizeof msg, "auto 跨距推導失敗：%s", span_err);
            scene_error(path, line_no, msg);
            return false;
        }

        /* 跨距 + 寬度範圍 → footprint 矩形 → 錨角 + 長度（凍結）。 */
        SurfaceRegion2 rect =
            along_v
                ? (SurfaceRegion2){ cross_lo, span_start, cross_hi, span_end }
                : (SurfaceRegion2){ span_start, cross_lo, span_end, cross_hi };

        anchor_uv = anchor_corner_from_rect(
            placement, length_direction, depth_side, &rect);
        timber->length = span_end - span_start;
    }

    /* 實體不得正面積重疊（公理 O2）：明寫與 auto 都套用。 */
    SurfaceRegion2 footprint;

    if (!a0_rect_uv(
            placement, anchor_uv, length_direction, depth_side,
            timber->length, timber->size_a, &footprint)) {
        scene_error(path, line_no, "角材參數無法推導 footprint");
        return false;
    }

    if (world_footprint_collides(
            world, placement, &footprint, timber)) {
        scene_error(path, line_no,
            "角材與同承載面上的已放角材正面積重疊");
        return false;
    }

    if (!timber_place_a0_on_surface(
            timber, placement, boundary, anchor_uv,
            (SurfaceDirection)length_direction,
            (SurfaceDepthSide)depth_side)) {
        scene_error(path, line_no,
            "放不上去：錨點在有效範圍外、A0 面跨出邊界或孔，或端面頂到自由邊");
        return false;
    }

    /* 重宣告交易要靠錨點重驗角材，所以放法要留著。 */
    world->anchors[timber - world->timbers] = (TimberAnchor){
        .placement_id = placement_id,
        .uv = anchor_uv,
        .anchor_kind = anchor_kind,
        .span_mode = timber->auto_length ? SPAN_AUTO : SPAN_EXPLICIT,
        .length_direction = length_direction,
        .depth_side = depth_side,
        .ref_grid = ref_grid,
        .ref_grid_axis = ref_grid_axis,
        .ref_grid_index = ref_grid_index,
        .ref_hole = ref_hole,
        .ref_edge = ref_edge,
        .has_through = has_through,
        .through = through
    };

    return true;
}


static bool apply_move_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    (void)count;

    uint32_t guide_id;
    Coord offset;

    if (!parse_u32(tokens[1], &guide_id) ||
        !parse_i64(tokens[2], &offset)) {
        scene_error(path, line_no, "move 需要：參考線id 新offset");
        return false;
    }

    GuideLine *guide = NULL;

    for (size_t i = 0; i < world->guide_count; ++i) {
        if (world->guides[i].id == guide_id) {
            guide = &world->guides[i];
            break;
        }
    }

    if (guide == NULL) {
        scene_error(path, line_no, "move 指的參考線不存在");
        return false;
    }

    const PlacementSurface *placement =
        world_find_placement(world, guide->placement_id);

    if (placement == NULL ||
        !guide_line_move(placement,
            world_find_boundary(world, placement->boundary_id),
            guide, offset)) {
        scene_error(path, line_no, "move 的 offset 落在承載面範圍之外");
        return false;
    }

    return true;
}

/* space <id> boundary <面id> <面id> [面id ...]：建構子吃邊界面清單，
 * 一致性由 space_construct 把關；同名 id = 交易式重宣告。 */
/* ============================================================
 * delete kind id：刪除指令（交易式）
 *
 * 語意（整份 World 快照 → 修改 → world_revalidate，失敗全數回滾）：
 *   boundary ：還被承載面掛著就拒絕（先刪 placement）；否則移除，
 *              並自各空間成員剔除、用剩下的成員重建空間。
 *   placement：還被參考線 / 網格 / 已放角材引用就拒絕；否則移除。
 *              它掛的邊界面留下來變游離面——placement 只是「放進世界」的關係。
 *   guide    ：直接移除（角材錨點在 place 當下就解成 uv，不引用線）。
 *   grid     ：被角材錨點 ref_grid 引用就拒絕；否則移除。
 *   timber   ：角材與其錨點一起移除（沒有東西引用角材）。
 *   space    ：移除（成員是參照不是持有）。
 * 畫布座標是展示中繼資料，跟著刪除標的一起清，不算幾何引用。
 * ============================================================ */
static void world_drop_canvas_pos(World *world, int kind, uint32_t id)
{
    for (size_t i = 0; i < world->canvas_pos_count; ++i) {
        CanvasPos *p = &world->canvas_pos[i];
        if (p->kind == kind && p->id == id) {
            memmove(p, p + 1,
                    (world->canvas_pos_count - i - 1) * sizeof *p);
            --world->canvas_pos_count;
            return;
        }
    }
}

/* ---- RC 柱/樑（公理 D13/D14、I15–I17、R8）----
 *
 *   column id [in S] at x y size w d [z z0 z1]
 *   beam   id [in S] along x|y from a to b at c width w depth d [top z]
 *
 *   兩者都是房間座標 AABB。省略 z/top → 從所屬空間 ±Z 槽推導；
 *   游離或推不出就拒絕，不猜（R11）。同 id 重宣告 = 交易式重綁。
 */

/* 找空間某軸某向槽位面的高程；沒有該槽回 false（推不出）。 */
static bool space_axis_bound(
    const World *world,
    const Space *space,
    int axis,
    int slot,
    Coord *out
)
{
    for (size_t i = 0; i < space->boundary_count; ++i) {
        for (size_t p = 0; p < world->placement_count; ++p) {
            const PlacementSurface *pl = &world->placements[p];

            if (pl->boundary_id != space->boundaries[i]) {
                continue;
            }
            int a = axis_index(pl->frame.normal);
            if (a != axis) {
                continue;
            }
            Coord n = a == 0 ? pl->frame.normal.x
                    : a == 1 ? pl->frame.normal.y
                             : pl->frame.normal.z;
            if ((n > 0 ? 1 : 0) == slot) {
                *out = point3_component(pl->frame.origin, axis);
                return true;
            }
        }
    }
    return false;
}

static bool apply_column_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t id, space_id = 0;
    int i = 2;

    if (!parse_u32(tokens[1], &id)) {
        scene_error(path, line_no, "column 的 id 不是有效的整數");
        return false;
    }
    if (i + 1 < count && strcmp(tokens[i], "in") == 0) {
        if (!parse_u32(tokens[i + 1], &space_id)) {
            scene_error(path, line_no, "in 後面的空間 id 不是有效的整數");
            return false;
        }
        i += 2;
    }
    /* at x y size w d [z z0 z1] */
    if (i + 6 > count || strcmp(tokens[i], "at") != 0 ||
        strcmp(tokens[i + 3], "size") != 0) {
        scene_error(path, line_no,
            "column 用法：column id [in 空間] at x y size w d [z z0 z1]");
        return false;
    }
    Coord x, y, w, d;
    if (!parse_i64(tokens[i + 1], &x) || !parse_i64(tokens[i + 2], &y) ||
        !parse_i64(tokens[i + 4], &w) || !parse_i64(tokens[i + 5], &d)) {
        scene_error(path, line_no, "column 的座標與尺寸要是整數");
        return false;
    }
    i += 6;
    if (w <= 0 || d <= 0) {
        scene_error(path, line_no, "柱的 w/d 要是正整數");
        return false;
    }

    const Space *space = NULL;
    if (space_id != 0) {
        space = world_find_space(world, space_id);
        if (space == NULL) {
            scene_error(path, line_no, "in 指的空間不存在");
            return false;
        }
    }

    Coord z0, z1;
    if (i + 3 == count && strcmp(tokens[i], "z") == 0) {
        if (!parse_i64(tokens[i + 1], &z0) || !parse_i64(tokens[i + 2], &z1)) {
            scene_error(path, line_no, "z 的兩個值要是整數");
            return false;
        }
        if (z1 <= z0) {
            scene_error(path, line_no, "z1 要大於 z0");
            return false;
        }
    } else if (i == count) {
        if (space == NULL) {
            scene_error(path, line_no,
                "游離柱必須明寫 z z0 z1（沒有空間可推導）");
            return false;
        }
        if (!space_axis_bound(world, space, 2, 0, &z0) ||
            !space_axis_bound(world, space, 2, 1, &z1)) {
            scene_error(path, line_no,
                "所屬空間 ±Z 槽沒有面，推不出柱高——請明寫 z z0 z1");
            return false;
        }
    } else {
        scene_error(path, line_no,
            "column 用法：column id [in 空間] at x y size w d [z z0 z1]");
        return false;
    }

    World backup = *world;
    RcColumn col = {
        .id = id, .space_id = space_id,
        .x_lo = x, .x_hi = x + w,
        .y_lo = y, .y_hi = y + d,
        .z_lo = z0, .z_hi = z1
    };

    for (size_t k = 0; k < world->column_count; ++k) {
        if (world->columns[k].id == id) {
            world->columns[k] = col;
            goto revalidate;
        }
    }
    if (world->column_count == WORLD_MAX_RC) {
        scene_error(path, line_no, "柱的數量超過上限");
        return false;
    }
    world->columns[world->column_count++] = col;

revalidate:
    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no,
            "柱宣告後有物件失效（足跡越界/柱-柱重疊/空間不存在）");
        return false;
    }
    return true;
}

static bool apply_beam_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t id, space_id = 0;
    int i = 2;

    if (!parse_u32(tokens[1], &id)) {
        scene_error(path, line_no, "beam 的 id 不是有效的整數");
        return false;
    }
    if (i + 1 < count && strcmp(tokens[i], "in") == 0) {
        if (!parse_u32(tokens[i + 1], &space_id)) {
            scene_error(path, line_no, "in 後面的空間 id 不是有效的整數");
            return false;
        }
        i += 2;
    }
    /* along x|y from a to b at c width w depth d [top z] */
    if (i + 11 > count || strcmp(tokens[i], "along") != 0 ||
        strcmp(tokens[i + 2], "from") != 0 ||
        strcmp(tokens[i + 4], "to") != 0 ||
        strcmp(tokens[i + 6], "at") != 0 ||
        strcmp(tokens[i + 8], "width") != 0 ||
        strcmp(tokens[i + 10], "depth") != 0) {
        scene_error(path, line_no,
            "beam 用法：beam id [in 空間] along x|y from a to b "
            "at c width w depth d [top z]");
        return false;
    }
    int axis;
    if (strcmp(tokens[i + 1], "x") == 0)      axis = 0;
    else if (strcmp(tokens[i + 1], "y") == 0) axis = 1;
    else {
        scene_error(path, line_no, "beam 的走向軸要是 x 或 y");
        return false;
    }
    Coord a, b, c, w, d;
    if (!parse_i64(tokens[i + 3], &a) || !parse_i64(tokens[i + 5], &b) ||
        !parse_i64(tokens[i + 7], &c) || !parse_i64(tokens[i + 9], &w) ||
        !parse_i64(tokens[i + 11], &d)) {
        scene_error(path, line_no, "beam 的座標與尺寸要是整數");
        return false;
    }
    i += 12;
    if (b <= a || w <= 0 || d <= 0) {
        scene_error(path, line_no, "樑跨度要 b>a、寬深要是正整數");
        return false;
    }

    const Space *space = NULL;
    if (space_id != 0) {
        space = world_find_space(world, space_id);
        if (space == NULL) {
            scene_error(path, line_no, "in 指的空間不存在");
            return false;
        }
    }

    Coord top;
    if (i + 2 == count && strcmp(tokens[i], "top") == 0) {
        if (!parse_i64(tokens[i + 1], &top)) {
            scene_error(path, line_no, "top 要是整數");
            return false;
        }
    } else if (i == count) {
        if (space == NULL) {
            scene_error(path, line_no,
                "游離樑必須明寫 top z（沒有空間可推導）");
            return false;
        }
        if (!space_axis_bound(world, space, 2, 1, &top)) {
            scene_error(path, line_no,
                "所屬空間 +Z 槽沒有面，推不出樑頂——請明寫 top z");
            return false;
        }
    } else {
        scene_error(path, line_no,
            "beam 用法：beam id [in 空間] along x|y from a to b "
            "at c width w depth d [top z]");
        return false;
    }
    /* 中心線對齊:c±w/2,奇數多的 1mm 在 +側(I13 慣例) */
    World backup = *world;
    RcBeam bm = { .id = id, .space_id = space_id, .axis = axis };
    if (axis == 0) {
        bm.x_lo = a;          bm.x_hi = b;
        bm.y_lo = c - w / 2;  bm.y_hi = c - w / 2 + w;
    } else {
        bm.y_lo = a;          bm.y_hi = b;
        bm.x_lo = c - w / 2;  bm.x_hi = c - w / 2 + w;
    }
    bm.z_hi = top;
    bm.z_lo = top - d;

    for (size_t k = 0; k < world->beam_count; ++k) {
        if (world->beams[k].id == id) {
            world->beams[k] = bm;
            goto revalidate;
        }
    }
    if (world->beam_count == WORLD_MAX_RC) {
        scene_error(path, line_no, "樑的數量超過上限");
        return false;
    }
    world->beams[world->beam_count++] = bm;

revalidate:
    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no,
            "樑宣告後有物件失效（足跡越界/空間不存在）");
        return false;
    }
    return true;
}

/* ============================================================
 * 面障礙物推導（R7/R8/R9）
 *
 *   obstacles <boundary_id> 把所屬空間的柱/樑投影到已放置面的
 *   uv 空間，依「足跡與輪廓的接觸關係」單一分類：
 *
 *     平面面（法向 ±Z）:
 *       柱   → hole / notch / corner / split
 *       樑   → strip（天花）;地板不受影響
 *     立面（法向水平）:
 *       柱貼牆 → split;樑沿牆 → top_drop;樑搭牆 → top_notch
 *
 *   這只是推導出的鬼影資料，不改邊界面；apply-proj 才落地。
 * ============================================================ */

typedef enum {
    OBSTACLE_HOLE,
    OBSTACLE_NOTCH,
    OBSTACLE_CORNER,
    OBSTACLE_SPLIT,
    OBSTACLE_STRIP,
    OBSTACLE_TOP_NOTCH,
    OBSTACLE_TOP_DROP
} ObstacleClass;

typedef struct {
    uint32_t id;
    int is_beam;
    ObstacleClass cls;
    Coord u_lo, v_lo, u_hi, v_hi;
} FaceObstacle;

/* 房間座標點在面框上的 uv。axis_u/axis_v 是單位軸向量。 */
static SurfacePoint2 frame_project_uv(const SurfaceFrame *f, Point3 p)
{
    Point3 d = { p.x - f->origin.x, p.y - f->origin.y, p.z - f->origin.z };
    int au = axis_index(f->axis_u);
    int av = axis_index(f->axis_v);
    Coord su = f->axis_u.x + f->axis_u.y + f->axis_u.z;
    Coord sv = f->axis_v.x + f->axis_v.y + f->axis_v.z;
    SurfacePoint2 r = {
        point3_component(d, au) * su,
        point3_component(d, av) * sv
    };
    return r;
}

/* AABB 八角投影到面框 uv 的包圍矩形。 */
static void box_project_uv(
    const SurfaceFrame *f,
    Coord x_lo, Coord x_hi, Coord y_lo, Coord y_hi,
    Coord z_lo, Coord z_hi,
    Coord *u_lo, Coord *v_lo, Coord *u_hi, Coord *v_hi
)
{
    Coord ul = INT64_MAX, uh = INT64_MIN, vl = INT64_MAX, vh = INT64_MIN;
    for (int i = 0; i < 8; ++i) {
        Point3 c = {
            (i & 1) ? x_hi : x_lo,
            (i & 2) ? y_hi : y_lo,
            (i & 4) ? z_hi : z_lo
        };
        SurfacePoint2 q = frame_project_uv(f, c);
        ul = coord_min(ul, q.u);
        uh = coord_max(uh, q.u);
        vl = coord_min(vl, q.v);
        vh = coord_max(vh, q.v);
    }
    *u_lo = ul; *u_hi = uh; *v_lo = vl; *v_hi = vh;
}

/* R 的某側是否與輪廓某邊共線正重疊（貼邊）。 */
static bool side_flush_outline(
    const PolygonLoop2 *loop,
    int side,          /* 0 left(u=u0) 1 right 2 bottom(v=v0) 3 top */
    Coord u0, Coord v0, Coord u1, Coord v1
)
{
    Coord c = (side == 0) ? u0 : (side == 1) ? u1 : (side == 2) ? v0 : v1;
    Coord lo = (side < 2) ? v0 : u0;
    Coord hi = (side < 2) ? v1 : u1;

    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 e = loop->v[(i + 1) % loop->count];
        Coord elo, ehi;

        if (side < 2) {
            if (a.u != c || e.u != c) continue;
            elo = coord_min(a.v, e.v);
            ehi = coord_max(a.v, e.v);
        } else {
            if (a.v != c || e.v != c) continue;
            elo = coord_min(a.u, e.u);
            ehi = coord_max(a.u, e.u);
        }
        if (coord_min(hi, ehi) > coord_max(lo, elo)) return true;
    }
    return false;
}

/* 矩形與輪廓的接觸分類：R 會先被輪廓邊界線裁切到內部
 * （直角切法，涵蓋孔/凹口/角/拆分全部案例）,再按貼邊數分類。
 * 回傳是否有正接觸；有時 out_* 為裁切後的 uv 矩形。 */
static bool classify_rect_outline(
    const PolygonLoop2 *loop,
    Coord in_u0, Coord in_v0, Coord in_u1, Coord in_v1,
    ObstacleClass *cls,
    Coord *out_u0, Coord *out_v0, Coord *out_u1, Coord *out_v1
)
{
    Coord u0 = in_u0, v0 = in_v0, u1 = in_u1, v1 = in_v1;
    size_t inside = 0;

    {
        SurfacePoint2 corners[4] = {
            { u0, v0 }, { u1, v0 }, { u1, v1 }, { u0, v1 }
        };
        for (int i = 0; i < 4; ++i) {
            if (poly_contains_point(loop, corners[i])) ++inside;
        }
    }
    if (inside == 0) return false;

    if (inside < 4) {
        /* 矩形跨出輪廓：每條切過 R 內部的輪廓邊把 R 裁向內側。 */
        for (size_t i = 0; i < loop->count; ++i) {
            SurfacePoint2 a = loop->v[i];
            SurfacePoint2 e = loop->v[(i + 1) % loop->count];
            Coord lo, hi, mid;

            if (a.u == e.u) {
                lo = coord_min(a.v, e.v);
                hi = coord_max(a.v, e.v);
                if (coord_min(v1, hi) <= coord_max(v0, lo)) continue;
                if (a.u <= u0 || a.u >= u1) continue;
                mid = (lo + hi) / 2;
                if (poly_contains_point(
                        loop, (SurfacePoint2){ a.u + 1, mid }))
                    u0 = a.u;
                else
                    u1 = a.u;
            } else if (a.v == e.v) {
                lo = coord_min(a.u, e.u);
                hi = coord_max(a.u, e.u);
                if (coord_min(u1, hi) <= coord_max(u0, lo)) continue;
                if (a.v <= v0 || a.v >= v1) continue;
                mid = (lo + hi) / 2;
                if (poly_contains_point(
                        loop, (SurfacePoint2){ mid, a.v + 1 }))
                    v0 = a.v;
                else
                    v1 = a.v;
            }
        }
        if (u0 >= u1 || v0 >= v1) return false;
    }

    {
        int flush = 0;
        bool f[4];
        for (int s = 0; s < 4; ++s) {
            f[s] = side_flush_outline(loop, s, u0, v0, u1, v1);
            if (f[s]) ++flush;
        }
        if (flush == 0) {
            *cls = OBSTACLE_HOLE;
        } else if (flush == 1) {
            *cls = OBSTACLE_NOTCH;
        } else if (flush == 2) {
            bool opposite = (f[0] && f[1]) || (f[2] && f[3]);
            *cls = opposite ? OBSTACLE_SPLIT : OBSTACLE_CORNER;
        } else {
            *cls = OBSTACLE_SPLIT;
        }
    }
    *out_u0 = u0; *out_v0 = v0; *out_u1 = u1; *out_v1 = v1;
    return true;
}

/* 面的所屬空間 id（非成員回 0，對應游離柱樑）。 */
static uint32_t world_space_of_boundary(const World *world, uint32_t bid)
{
    for (size_t i = 0; i < world->space_count; ++i) {
        for (size_t m = 0; m < world->spaces[i].boundary_count; ++m) {
            if (world->spaces[i].boundaries[m] == bid) {
                return world->spaces[i].id;
            }
        }
    }
    return 0;
}

/* 已放置面的障礙物推導。回傳筆數；面未放置回 SIZE_MAX。 */
static size_t world_face_obstacles(
    const World *world,
    const SpaceBoundarySurface *b,
    FaceObstacle *out,
    size_t cap
)
{
    const PlacementSurface *pl = NULL;
    for (size_t p = 0; p < world->placement_count; ++p) {
        if (world->placements[p].boundary_id == b->id) {
            pl = &world->placements[p];
            break;
        }
    }
    if (pl == NULL) return SIZE_MAX;

    const SurfaceFrame *f = &pl->frame;
    int n_axis = axis_index(f->normal);
    Coord plane = point3_component(f->origin, n_axis);
    uint32_t sid = world_space_of_boundary(world, b->id);
    size_t n = 0;
    Coord o_u0, o_v0, o_u1, o_v1;

    poly_bbox(&b->outline, &o_u0, &o_v0, &o_u1, &o_v1);

    for (size_t i = 0; i < world->column_count && n < cap; ++i) {
        const RcColumn *c = &world->columns[i];
        Coord u0, v0, u1, v1;
        if (c->space_id != sid) continue;

        box_project_uv(f, c->x_lo, c->x_hi, c->y_lo, c->y_hi,
            c->z_lo, c->z_hi, &u0, &v0, &u1, &v1);

        if (n_axis == 2) {
            /* 平面面：柱足跡 vs 輪廓接觸 → hole/notch/corner/split */
            ObstacleClass cls;
            Coord cu0, cv0, cu1, cv1;
            if (!classify_rect_outline(&b->outline, u0, v0, u1, v1,
                    &cls, &cu0, &cv0, &cu1, &cv1)) continue;
            out[n++] = (FaceObstacle){
                c->id, 0, cls, cu0, cv0, cu1, cv1
            };
        } else {
            /* 立面：柱的垂直軸區間要含牆平面才算貼牆。
             * uv 矩形已經是柱與牆的交線投影，裁到牆範圍。 */
            Coord nlo, nhi;
            if (n_axis == 0) { nlo = c->x_lo; nhi = c->x_hi; }
            else             { nlo = c->y_lo; nhi = c->y_hi; }
            if (plane < nlo || plane > nhi) continue;
            u0 = coord_max(u0, o_u0); u1 = coord_min(u1, o_u1);
            v0 = coord_max(v0, o_v0); v1 = coord_min(v1, o_v1);
            if (u0 >= u1 || v0 >= v1) continue;
            out[n++] = (FaceObstacle){
                c->id, 0, OBSTACLE_SPLIT, u0, v0, u1, v1
            };
        }
    }

    for (size_t i = 0; i < world->beam_count && n < cap; ++i) {
        const RcBeam *bm = &world->beams[i];
        Coord u0, v0, u1, v1;
        if (bm->space_id != sid) continue;

        box_project_uv(f, bm->x_lo, bm->x_hi, bm->y_lo, bm->y_hi,
            bm->z_lo, bm->z_hi, &u0, &v0, &u1, &v1);

        if (n_axis == 2) {
            /* 只有法向 +Z 的天花受影響；樑要真的碰到那個高程。 */
            if (f->normal.z <= 0) continue;
            if (plane < bm->z_lo || plane > bm->z_hi) continue;
            out[n++] = (FaceObstacle){
                bm->id, 1, OBSTACLE_STRIP, u0, v0, u1, v1
            };
        } else {
            Coord nlo, nhi;
            int h_axis;      /* 牆的水平面內軸（非法向的那個） */
            /* 樑沿法向軸的跨度要含牆平面（搭/貼牆）。 */
            if (n_axis == 0) { nlo = bm->x_lo; nhi = bm->x_hi; }
            else             { nlo = bm->y_lo; nhi = bm->y_hi; }
            if (plane < nlo || plane > nhi) continue;
            h_axis = (n_axis == 0) ? 1 : 0;
            if (bm->axis == (uint8_t)h_axis) {
                /* 貼牆走：頂邊整段降樑深。 */
                u0 = coord_max(u0, o_u0); u1 = coord_min(u1, o_u1);
                v0 = coord_max(v0, o_v0); v1 = coord_min(v1, o_v1);
                if (u0 >= u1 || v0 >= v1) continue;
                out[n++] = (FaceObstacle){
                    bm->id, 1, OBSTACLE_TOP_DROP, u0, v0, u1, v1
                };
            } else if (bm->axis == (uint8_t)n_axis) {
                /* 搭牆：頂邊 w×d 凹口。 */
                u0 = coord_max(u0, o_u0); u1 = coord_min(u1, o_u1);
                v0 = coord_max(v0, o_v0); v1 = coord_min(v1, o_v1);
                if (u0 >= u1 || v0 >= v1) continue;
                out[n++] = (FaceObstacle){
                    bm->id, 1, OBSTACLE_TOP_NOTCH, u0, v0, u1, v1
                };
            }
        }
    }
    return n;
}

static bool apply_delete_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    (void)count;

    uint32_t id;

    if (!parse_u32(tokens[2], &id)) {
        scene_error(path, line_no, "delete 的 id 不是有效的整數");
        return false;
    }

    const char *kind = tokens[1];
    World backup = *world;

    if (strcmp(kind, "boundary") == 0) {
        size_t bi = SIZE_MAX;

        for (size_t i = 0; i < world->boundary_count; ++i) {
            if (world->boundaries[i].id == id) bi = i;
        }
        if (bi == SIZE_MAX) {
            scene_error(path, line_no, "這個邊界面不存在");
            return false;
        }
        for (size_t i = 0; i < world->placement_count; ++i) {
            if (world->placements[i].boundary_id == id) {
                scene_error(path, line_no,
                    "這個邊界面還有承載面掛著，先刪它的承載面（placement）");
                return false;
            }
        }
        memmove(&world->boundaries[bi], &world->boundaries[bi + 1],
                (world->boundary_count - bi - 1) *
                sizeof world->boundaries[0]);
        --world->boundary_count;
        /* 空間成員是參照：剔除後用剩下的成員重建空間。 */
        for (size_t s = 0; s < world->space_count; ++s) {
            Space *sp = &world->spaces[s];
            size_t w = 0;
            for (size_t m = 0; m < sp->boundary_count; ++m) {
                if (sp->boundaries[m] != id) {
                    sp->boundaries[w++] = sp->boundaries[m];
                }
            }
            if (w == sp->boundary_count) continue;
            Space rebuild = { 0 };
            if (w == 0) {
                rebuild.id = sp->id;
            } else if (!space_construct(world, sp->id,
                                        sp->boundaries, w, &rebuild)) {
                *world = backup;
                scene_error(path, line_no, "剔除成員後空間無法重建");
                return false;
            }
            *sp = rebuild;
        }
        world_drop_canvas_pos(world, CANVAS_POS_BOUNDARY, id);
    } else if (strcmp(kind, "placement") == 0) {
        size_t pi = SIZE_MAX;

        for (size_t i = 0; i < world->placement_count; ++i) {
            if (world->placements[i].id == id) pi = i;
        }
        if (pi == SIZE_MAX) {
            scene_error(path, line_no, "這個承載面不存在");
            return false;
        }
        for (size_t i = 0; i < world->guide_count; ++i) {
            if (world->guides[i].placement_id == id) {
                scene_error(path, line_no,
                    "這個承載面還有參考線，先刪參考線（guide）");
                return false;
            }
        }
        for (size_t i = 0; i < world->grid_count; ++i) {
            if (world->grids[i].placement_id == id) {
                scene_error(path, line_no,
                    "這個承載面還有網格，先刪網格（grid）");
                return false;
            }
        }
        for (size_t i = 0; i < world->timber_count; ++i) {
            if (world->timbers[i].placed &&
                world->anchors[i].placement_id == id) {
                scene_error(path, line_no,
                    "這個承載面還有已放置的角材，先刪角材（timber）");
                return false;
            }
        }
        memmove(&world->placements[pi], &world->placements[pi + 1],
                (world->placement_count - pi - 1) *
                sizeof world->placements[0]);
        --world->placement_count;
        world_drop_canvas_pos(world, CANVAS_POS_PLACEMENT, id);
    } else if (strcmp(kind, "guide") == 0) {
        size_t gi = SIZE_MAX;

        for (size_t i = 0; i < world->guide_count; ++i) {
            if (world->guides[i].id == id) gi = i;
        }
        if (gi == SIZE_MAX) {
            scene_error(path, line_no, "這條參考線不存在");
            return false;
        }
        memmove(&world->guides[gi], &world->guides[gi + 1],
                (world->guide_count - gi - 1) * sizeof world->guides[0]);
        --world->guide_count;
    } else if (strcmp(kind, "grid") == 0) {
        size_t gi = SIZE_MAX;

        for (size_t i = 0; i < world->grid_count; ++i) {
            if (world->grids[i].id == id) gi = i;
        }
        if (gi == SIZE_MAX) {
            scene_error(path, line_no, "這個網格不存在");
            return false;
        }
        for (size_t i = 0; i < world->timber_count; ++i) {
            if (world->timbers[i].placed &&
                world->anchors[i].ref_grid == id) {
                scene_error(path, line_no,
                    "有角材錨在這個網格上，先刪角材（timber）");
                return false;
            }
        }
        memmove(&world->grids[gi], &world->grids[gi + 1],
                (world->grid_count - gi - 1) * sizeof world->grids[0]);
        --world->grid_count;
    } else if (strcmp(kind, "timber") == 0) {
        size_t ti = SIZE_MAX;

        for (size_t i = 0; i < world->timber_count; ++i) {
            if (world->timbers[i].id == id) ti = i;
        }
        if (ti == SIZE_MAX) {
            scene_error(path, line_no, "這支角材不存在");
            return false;
        }
        memmove(&world->timbers[ti], &world->timbers[ti + 1],
                (world->timber_count - ti - 1) * sizeof world->timbers[0]);
        memmove(&world->anchors[ti], &world->anchors[ti + 1],
                (world->timber_count - ti - 1) * sizeof world->anchors[0]);
        --world->timber_count;
    } else if (strcmp(kind, "space") == 0) {
        size_t si = SIZE_MAX;

        for (size_t i = 0; i < world->space_count; ++i) {
            if (world->spaces[i].id == id) si = i;
        }
        if (si == SIZE_MAX) {
            scene_error(path, line_no, "這個空間不存在");
            return false;
        }
        memmove(&world->spaces[si], &world->spaces[si + 1],
                (world->space_count - si - 1) * sizeof world->spaces[0]);
        --world->space_count;
        world_drop_canvas_pos(world, CANVAS_POS_SPACE, id);
        /* I17：刪空間 → 柱樑變游離，不跟著刪。 */
        for (size_t i = 0; i < world->column_count; ++i) {
            if (world->columns[i].space_id == id) {
                world->columns[i].space_id = 0;
            }
        }
        for (size_t i = 0; i < world->beam_count; ++i) {
            if (world->beams[i].space_id == id) {
                world->beams[i].space_id = 0;
            }
        }
    } else if (strcmp(kind, "column") == 0) {
        size_t ci = SIZE_MAX;

        for (size_t i = 0; i < world->column_count; ++i) {
            if (world->columns[i].id == id) ci = i;
        }
        if (ci == SIZE_MAX) {
            scene_error(path, line_no, "這根柱不存在");
            return false;
        }
        memmove(&world->columns[ci], &world->columns[ci + 1],
                (world->column_count - ci - 1) * sizeof world->columns[0]);
        --world->column_count;
        world_drop_canvas_pos(world, CANVAS_POS_COLUMN, id);
    } else if (strcmp(kind, "beam") == 0) {
        size_t bi = SIZE_MAX;

        for (size_t i = 0; i < world->beam_count; ++i) {
            if (world->beams[i].id == id) bi = i;
        }
        if (bi == SIZE_MAX) {
            scene_error(path, line_no, "這根樑不存在");
            return false;
        }
        memmove(&world->beams[bi], &world->beams[bi + 1],
                (world->beam_count - bi - 1) * sizeof world->beams[0]);
        --world->beam_count;
        world_drop_canvas_pos(world, CANVAS_POS_BEAM, id);
    } else {
        scene_error(path, line_no,
            "delete 的類別要是 boundary / placement / guide / grid / timber / space / column / beam");
        return false;
    }

    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no, "刪除後 World 失效，已回滾");
        return false;
    }
    return true;
}

static bool apply_space_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    uint32_t space_id;

    if (!parse_u32(tokens[1], &space_id)) {
        scene_error(path, line_no, "space 的 id 不是有效的整數");
        return false;
    }

    int i = 2;

    if (i < count && strcmp(tokens[i], "boundary") == 0) {
        ++i;
    }


    SurfaceId faces[SPACE_MAX_MEMBERS];
    size_t face_count = 0;

    for (; i < count; ++i) {
        if (face_count == SPACE_MAX_MEMBERS) {
            scene_error(path, line_no, "空間的邊界面數量超過上限");
            return false;
        }
        if (!parse_u32(tokens[i], &faces[face_count])) {
            scene_error(path, line_no, "space 的面 id 不是有效的整數");
            return false;
        }
        ++face_count;
    }

    Space candidate;

    if (face_count == 0) {
        /* 空容器：零成員的部分空間，closed=false、界未釘。 */
        candidate = (Space){ 0 };
        candidate.id = space_id;
    } else if (!space_construct(world, space_id, faces, face_count, &candidate)) {
        /* 建構子本身就驗成員一致（不改 World）。 */
        scene_error(path, line_no,
            "這些面組不成一致的空間：面不存在、重複、"
            "沒有唯一承載面、佔同一方向槽位，或區間不一致");
        return false;
    }

    for (size_t s = 0; s < world->space_count; ++s) {
        if (world->spaces[s].id == space_id) {
            if (!world_replace_object(
                    world, &world->spaces[s],
                    &candidate, sizeof candidate)) {
                scene_error(path, line_no, "重宣告空間後 World 失效");
                return false;
            }
            return true;
        }
    }

    if (world->space_count == WORLD_MAX_SPACES) {
        scene_error(path, line_no, "空間的數量超過上限");
        return false;
    }

    world->spaces[world->space_count++] = candidate;
    return true;
}


static bool apply_reset_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    (void)path;
    (void)line_no;
    (void)tokens;

    *world = (World){ 0 };
    return true;
}

/* ============================================================
 * world_dump_dsl：把 World 序列化回 DSL 文本（畫布存檔/匯出用）
 *
 *   原則：輸出是「可重放」的規範形——重放後得到同一個 World。
 *   - at-guides 的錨點在 place 當下已凍結（R2），dump 成等價的 at u v。
 *   - 物件順序依依賴鏈：boundary → placement → guide → grid
 *     → timber → place → space。
 * ============================================================ */

static const char *axis_word(Vector3 axis)
{
    for (size_t i = 0; i < sizeof(AXIS_WORDS) / sizeof(AXIS_WORDS[0]); ++i) {
        if (AXIS_WORDS[i].axis.x == axis.x &&
            AXIS_WORDS[i].axis.y == axis.y &&
            AXIS_WORDS[i].axis.z == axis.z) {
            return AXIS_WORDS[i].word;
        }
    }
    return "+x";   /* 公理保證軸恆為六向之一；走到這是內部錯誤 */
}

static const char *length_dir_word(int dir)
{
    switch (dir) {
        case SURFACE_DIRECTION_POS_U: return "+u";
        case SURFACE_DIRECTION_NEG_U: return "-u";
        case SURFACE_DIRECTION_POS_V: return "+v";
        case SURFACE_DIRECTION_NEG_V: return "-v";
        default:                      return "+u";
    }
}

static const char *depth_side_word(int side)
{
    return side == SURFACE_DEPTH_POSITIVE_NORMAL ? "+n" : "-n";
}

/* 一個環 → 「u,v u,v … [fixity …]」（全 FIXED 時省略 fixity 子句）。
 * GDI 畫布產 DSL 行也用這個（canvas_emit_*）。 */
static char *fmt_loop(char *p, char *end, const PolygonLoop2 *loop)
{
    for (size_t i = 0; i < loop->count; ++i) {
        p += snprintf(p, (size_t)(end - p), "%s%lld,%lld",
                      i ? " " : "",
                      (long long)loop->v[i].u, (long long)loop->v[i].v);
    }
    bool any_free = false;
    for (size_t i = 0; i < loop->count; ++i) {
        if (loop->fixity[i] == EDGE_FREE) { any_free = true; break; }
    }
    if (any_free) {
        p += snprintf(p, (size_t)(end - p), " fixity");
        for (size_t i = 0; i < loop->count; ++i) {
            p += snprintf(p, (size_t)(end - p), " %c",
                          loop->fixity[i] == EDGE_FREE ? 'X' : 'F');
        }
    }
    return p;
}

static void dump_loop(FILE *out, const PolygonLoop2 *loop)
{
    char buf[POLY_MAX_VERTICES * 26 + 8];
    fmt_loop(buf, buf + sizeof buf, loop);
    fputs(buf, out);
}

static void world_dump_dsl(const World *world, FILE *out)
{
    for (size_t i = 0; i < world->boundary_count; ++i) {
        const SpaceBoundarySurface *b = &world->boundaries[i];

        fprintf(out, "boundary %u outline ", (unsigned)b->id);
        dump_loop(out, &b->outline);

        for (size_t h = 0; h < b->hole_count; ++h) {
            fputs(" hole ", out);
            dump_loop(out, &b->holes[h]);
        }
        fputc('\n', out);
    }

    for (size_t i = 0; i < world->placement_count; ++i) {
        const PlacementSurface *p = &world->placements[i];

        fprintf(out, "placement %u ", (unsigned)p->id);
        if (p->boundary_id != 0) {
            fprintf(out, "on boundary %u ", (unsigned)p->boundary_id);
        }
        fprintf(out, "origin %lld %lld %lld u %s v %s",
                (long long)p->frame.origin.x,
                (long long)p->frame.origin.y,
                (long long)p->frame.origin.z,
                axis_word(p->frame.axis_u),
                axis_word(p->frame.axis_v));
        if (p->boundary_id == 0) {
            fprintf(out, " rect %lld %lld %lld %lld",
                    (long long)p->rect.min_u, (long long)p->rect.min_v,
                    (long long)p->rect.max_u, (long long)p->rect.max_v);
        }
        fputc('\n', out);
    }

    for (size_t i = 0; i < world->guide_count; ++i) {
        const GuideLine *g = &world->guides[i];

        fprintf(out, "guide %u %u %s %lld\n",
                (unsigned)g->id, (unsigned)g->placement_id,
                g->direction == GUIDE_ALONG_U ? "u" : "v",
                (long long)g->offset);
    }

    for (size_t i = 0; i < world->grid_count; ++i) {
        const ReferenceGrid *g = &world->grids[i];

        if (g->u_count > 0) {
            fprintf(out, "grid %u on %u u", (unsigned)g->id,
                    (unsigned)g->placement_id);
            for (size_t k = 0; k < g->u_count; ++k) {
                fprintf(out, " %lld", (long long)g->u_coords[k]);
            }
            fputc('\n', out);
        }
        if (g->v_count > 0) {
            fprintf(out, "grid %u on %u v", (unsigned)g->id,
                    (unsigned)g->placement_id);
            for (size_t k = 0; k < g->v_count; ++k) {
                fprintf(out, " %lld", (long long)g->v_coords[k]);
            }
            fputc('\n', out);
        }
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *t = &world->timbers[i];

        /* auto 角材的 length 在 place 當下已凍結；dump 明寫形式，
         * 重放不再重算（參照若被移動過，重算會得到不同的世界）。 */
        fprintf(out, "timber %u %lld %lld %lld\n",
                (unsigned)t->id, (long long)t->length,
                (long long)t->size_a, (long long)t->size_b);
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *t = &world->timbers[i];
        const TimberAnchor *a = &world->anchors[i];

        if (!t->placed) {
            continue;
        }

        /* R2：錨點在 place 當下已凍結。at-grid/at-edge 的參照形式
         * 會在參照（格線座標、邊位置）事後移動時重放出不同位置，
         * 一律 dump 凍結點；through 是 auto 選段器，明寫長度下無意義。 */
        fprintf(out, "place %u on %u at %lld %lld %s %s\n",
                (unsigned)t->id, (unsigned)a->placement_id,
                (long long)a->uv.u, (long long)a->uv.v,
                length_dir_word(a->length_direction),
                depth_side_word(a->depth_side));
    }

    for (size_t i = 0; i < world->space_count; ++i) {
        const Space *s = &world->spaces[i];

        if (s->boundary_count == 0) {
            fprintf(out, "space %u\n", (unsigned)s->id);
            continue;
        }

        fprintf(out, "space %u boundary", (unsigned)s->id);
        for (size_t k = 0; k < s->boundary_count; ++k) {
            fprintf(out, " %u", (unsigned)s->boundaries[k]);
        }
        fputc('\n', out);
    }

    /* RC 柱/樑:z/top 一律明寫（建構時已推導凍結，重放不再推導）。 */
    for (size_t i = 0; i < world->column_count; ++i) {
        const RcColumn *c = &world->columns[i];

        fprintf(out, "column %u ", (unsigned)c->id);
        if (c->space_id != 0) {
            fprintf(out, "in %u ", (unsigned)c->space_id);
        }
        fprintf(out, "at %lld %lld size %lld %lld z %lld %lld\n",
                (long long)c->x_lo, (long long)c->y_lo,
                (long long)(c->x_hi - c->x_lo),
                (long long)(c->y_hi - c->y_lo),
                (long long)c->z_lo, (long long)c->z_hi);
    }
    for (size_t i = 0; i < world->beam_count; ++i) {
        const RcBeam *b = &world->beams[i];

        fprintf(out, "beam %u ", (unsigned)b->id);
        if (b->space_id != 0) {
            fprintf(out, "in %u ", (unsigned)b->space_id);
        }
        if (b->axis == 0) {
            fprintf(out, "along x from %lld to %lld at %lld",
                    (long long)b->x_lo, (long long)b->x_hi,
                    (long long)((b->y_lo + b->y_hi) / 2));
        } else {
            fprintf(out, "along y from %lld to %lld at %lld",
                    (long long)b->y_lo, (long long)b->y_hi,
                    (long long)((b->x_lo + b->x_hi) / 2));
        }
        fprintf(out, " width %lld depth %lld top %lld\n",
                (long long)(b->axis == 0 ? b->y_hi - b->y_lo
                                         : b->x_hi - b->x_lo),
                (long long)(b->z_hi - b->z_lo),
                (long long)b->z_hi);
    }

    /* 畫布座標最後寫：它引用的物件要先存在。 */
    for (size_t i = 0; i < world->canvas_pos_count; ++i) {
        const CanvasPos *p = &world->canvas_pos[i];

        fprintf(out, "canvas-pos %s %u %lld %lld\n",
                p->kind == CANVAS_POS_BOUNDARY  ? "boundary"  :
                p->kind == CANVAS_POS_PLACEMENT ? "placement" :
                p->kind == CANVAS_POS_SPACE     ? "space"     :
                p->kind == CANVAS_POS_COLUMN    ? "column"    : "beam",
                (unsigned)p->id, (long long)p->x, (long long)p->y);
    }
}

/*
 * canvas-pos：設定物件在無限畫布上的擺放位置。
 * 純展示中繼資料：只要求目標存在，不做幾何驗證；
 * 同 (kind,id) 再宣告 = 移動卡片。
 */
static bool apply_canvaspos_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    (void)count;
    int kind;

    if (strcmp(tokens[1], "boundary") == 0) {
        kind = CANVAS_POS_BOUNDARY;
    } else if (strcmp(tokens[1], "placement") == 0) {
        kind = CANVAS_POS_PLACEMENT;
    } else if (strcmp(tokens[1], "space") == 0) {
        kind = CANVAS_POS_SPACE;
    } else if (strcmp(tokens[1], "column") == 0) {
        kind = CANVAS_POS_COLUMN;
    } else if (strcmp(tokens[1], "beam") == 0) {
        kind = CANVAS_POS_BEAM;
    } else {
        scene_error(path, line_no,
            "canvas-pos 的類別要是 boundary / placement / space / column / beam");
        return false;
    }

    uint32_t id;
    Coord x, y;

    if (!parse_u32(tokens[2], &id) ||
        !parse_i64(tokens[3], &x) ||
        !parse_i64(tokens[4], &y)) {
        scene_error(path, line_no, "canvas-pos 的 id / x / y 要是整數");
        return false;
    }

    /* 畫布座標引用的是世界裡的實體，目標必須存在。 */
    bool exists =
        kind == CANVAS_POS_BOUNDARY  ? world_find_boundary(world, id)  != NULL :
        kind == CANVAS_POS_PLACEMENT ? world_find_placement(world, id) != NULL :
        kind == CANVAS_POS_SPACE     ? world_find_space(world, id)     != NULL :
        kind == CANVAS_POS_COLUMN    ? world_find_column(world, id)    != NULL :
                                       world_find_beam(world, id)      != NULL;

    if (!exists) {
        scene_error(path, line_no, "canvas-pos 指的物件不存在");
        return false;
    }

    for (size_t i = 0; i < world->canvas_pos_count; ++i) {
        CanvasPos *p = &world->canvas_pos[i];

        if (p->kind == kind && p->id == id) {
            p->x = x;
            p->y = y;
            return true;
        }
    }

    if (world->canvas_pos_count == WORLD_MAX_CANVAS_POS) {
        scene_error(path, line_no, "畫布座標的數量超過上限");
        return false;
    }

    world->canvas_pos[world->canvas_pos_count++] =
        (CanvasPos){ .kind = kind, .id = id, .x = x, .y = y };
    return true;
}

/*
 * 指令表：欄位數範圍（含指令本身）、要不要先有承載面、用法字串、套用函式。
 * boundary / placement / surface / space / place 是變長指令，欄位數由各自
 * 的解析函式把關，這裡只擋明顯太短。
 */
static const struct {
    const char *word;
    int min_fields;
    int max_fields;
    bool needs_placement;
    const char *usage;
    bool (*apply)(const char *path, int line_no, char *tokens[], int count, World *world);
} SCENE_COMMANDS[] = {
    {
        "boundary", 6, SCENE_MAX_TOKENS, false,
        "boundary id outline u,v u,v u,v u,v ... "
        "[kind room_plan|wall_elevation] [fixity F F ...] "
        "[hole u,v ... [fixity ...]]",
        apply_boundary_line
    },
    {
        "placement", 10, SCENE_MAX_TOKENS, false,
        "placement id [on boundary 邊id] origin x y z u 軸 v 軸 "
        "[rect min_u min_v max_u max_v]",
        apply_placement_line
    },
    {
        "surface", 10, SCENE_MAX_TOKENS, false,
        "surface id origin x y z u 軸 v 軸 (rect ... | outline u,v ...)",
        apply_surface_combined_line
    },
    {
        "space", 2, 4 + SPACE_MAX_MEMBERS, false,
        "space id [boundary 面id 面id ...]（無成員 = 空容器）",
        apply_space_line
    },
    {
        "guide", 5, 5, true,
        "guide id 承載面id 方向（u 或 v） offset",
        apply_guide_line
    },
    {
        "grid", 6, SCENE_MAX_TOKENS, true,
        "grid id on 承載面id u 座標... [v 座標...]",
        apply_grid_line
    },
    {
        "timber", 4, 5, false,
        "timber id 長度 A尺寸 B尺寸（或 id A尺寸 B尺寸 = auto）",
        apply_timber_line
    },
    {
        "place", 8, 12, true,
        "place 角材id on 承載面id at u v 長度方向 深度側"
        "（或 at-guides 線1 線2｜at-grid 網id u|v 索引｜at-edge e索引，可加 through 座標）",
        apply_place_line
    },
    {
        "move", 3, 3, true,
        "move 參考線id 新offset",
        apply_move_line
    },
    {
        "column", 8, 13, false,
        "column id [in 空間id] at x y size w d [z z0 z1]",
        apply_column_line
    },
    {
        "beam", 15, 19, false,
        "beam id [in 空間id] along x|y from a to b at c "
        "width w depth d [top z]",
        apply_beam_line
    },
    {
        "delete", 3, 3, false,
        "delete boundary|placement|guide|grid|timber|space|column|beam id",
        apply_delete_line
    },
    {
        "reset", 1, 1, false,
        "reset",
        apply_reset_line
    },
    {
        "canvas-pos", 5, 5, false,
        "canvas-pos boundary|placement|space|column|beam id x y",
        apply_canvaspos_line
    },
    { NULL, 0, 0, false, NULL, NULL }
};

static bool apply_scene_line(const char *path, int line_no, char *tokens[], int count, World *world)
{
    for (size_t i = 0; SCENE_COMMANDS[i].word != NULL; ++i) {
        if (strcmp(tokens[0], SCENE_COMMANDS[i].word) != 0) {
            continue;
        }

        if (count < SCENE_COMMANDS[i].min_fields ||
            count > SCENE_COMMANDS[i].max_fields) {
            fprintf(stderr, "%s:%d: 欄位數不對，用法：%s\n",
                    path, line_no, SCENE_COMMANDS[i].usage);
            snprintf(g_scene_last_error, sizeof g_scene_last_error,
                     "line %d: 欄位數不對，用法：%s",
                     line_no, SCENE_COMMANDS[i].usage);
            return false;
        }

        if (SCENE_COMMANDS[i].needs_placement && world->placement_count == 0) {
            scene_error(path, line_no, "這個指令前面要先有 placement 或 surface");
            return false;
        }

        return SCENE_COMMANDS[i].apply(path, line_no, tokens, count, world);
    }

    scene_error(path, line_no,
        "不認得的指令（boundary placement surface space guide timber place "
        "move column beam delete reset canvas-pos）");
    return false;
}

/*
 * 一行一筆，由上往下套用。id 要先宣告才能被引用，
 * 所以「place 寫在 timber 前面」這種錯誤自然變成「id 不存在」，不必另外規定。
 */
static bool parse_scene_file(const char *path, World *out_world)
{
    /* 二進位模式：換行自己處理，Windows 的文字模式不介入。 */
    FILE *in = fopen(path, "rb");

    if (in == NULL) {
        fprintf(stderr, "無法開啟場景檔：%s\n", path);
        return false;
    }

    char line[SCENE_MAX_LINE];
    int line_no = 0;
    bool ok = true;

    while (ok && fgets(line, sizeof line, in) != NULL) {
        ++line_no;

        size_t length = strlen(line);

        if (length > 0 && line[length - 1] != '\n' && !feof(in)) {
            scene_error(path, line_no, "這一行太長");
            ok = false;
            break;
        }

        char *text = line;

        /* UTF-8 BOM 只可能出現在第一行。 */
        if (line_no == 1 &&
            (unsigned char)text[0] == 0xEF &&
            (unsigned char)text[1] == 0xBB &&
            (unsigned char)text[2] == 0xBF) {
            text += 3;
        }

        /* 去掉換行；CRLF 的 \r 也一起去掉。 */
        char *newline = strchr(text, '\n');

        if (newline != NULL) {
            *newline = '\0';

            if (newline > text && newline[-1] == '\r') {
                newline[-1] = '\0';
            }
        }

        /* # 之後到行尾都是註解。 */
        char *hash = strchr(text, '#');

        if (hash != NULL) {
            *hash = '\0';
        }

        char *tokens[SCENE_MAX_TOKENS];
        int count = split_tokens(text, tokens, SCENE_MAX_TOKENS);

        if (count < 0) {
            scene_error(path, line_no, "這一行的欄位太多");
            ok = false;
            break;
        }

        if (count == 0) {
            continue;
        }

        ok = apply_scene_line(path, line_no, tokens, count, out_world);
    }

    fclose(in);

    /*
     * 沒放置的角材沒有位置，既印不出也畫不出，一定是場景檔漏了 place。
     * 擋在這裡，後面就能確定 World 裡的角材都已放置。
     */
    for (size_t i = 0; ok && i < out_world->timber_count; ++i) {
        if (!out_world->timbers[i].placed) {
            fprintf(stderr, "%s: 角材 %" PRIu32 " 沒有 place。\n",
                    path, out_world->timbers[i].id);
            ok = false;
        }
    }

    return ok;
}

/* ============================================================
 * 主程式
 * ============================================================ */

int main(int argc, char **argv)
{
    /* --no-window：只印文字與 SVG，不開視窗（自動測試用）。 */
    bool open_window = true;

    /* --scene：幾何改從場景檔讀；沒給就用下面那組硬編的房間 A。 */
    const char *scene_path = NULL;

    /* --out：改 SVG 的輸出路徑；沒給就放在本原始碼旁邊。 */
    const char *out_path = NULL;

    /* --bench N：量測 GDI 每幀成本 N 次（Windows 才有效）。 */
    int bench_iters = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--no-window") == 0) {
            open_window = false;
        } else if (strcmp(argv[i], "--scene") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "--scene 後面要接場景檔路徑。\n");
                return 1;
            }

            scene_path = argv[++i];
        } else if (strcmp(argv[i], "--out") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "--out 後面要接輸出路徑。\n");
                return 1;
            }

            out_path = argv[++i];
        } else if (strcmp(argv[i], "--bench") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "--bench 後面要接次數。\n");
                return 1;
            }

            bench_iters = atoi(argv[++i]);
        }
    }

    World world = { 0 };

    if (scene_path != NULL) {
        if (!parse_scene_file(scene_path, &world)) {
            return 1;
        }
    } else {
        /*
         * 房間 A 的天花：一片邊界面 + 一片掛它的承載面。
         *
         * 房間根座標：
         *   X 向右
         *   Y 向下／向房間深處
         *   Z 向上
         *
         * 天花高度：
         *   z = 2500
         *
         * 表面局部座標：
         *   U = 房間 X
         *   V = 房間 Y
         *   N = 房間 Z
         */
        SpaceBoundarySurface ceiling_boundary = {
            .id = 1,
            .kind = BOUNDARY_ROOM_PLAN,
            .outline = {
                .count = 4,
                .v = {
                    { 0, 0 }, { 4000, 0 }, { 4000, 3000 }, { 0, 3000 }
                },
                .fixity = { EDGE_FIXED, EDGE_FIXED, EDGE_FIXED, EDGE_FIXED }
            },
            .hole_count = 0
        };

        if (!boundary_is_valid(&ceiling_boundary)) {
            fprintf(stderr, "邊界面定義無效。\n");
            return 1;
        }

        world.boundaries[0] = ceiling_boundary;
        world.boundary_count = 1;

        PlacementSurface ceiling = {
            .id = 1,
            .boundary_id = ceiling_boundary.id,
            .frame = {
                .origin = { 0, 0, 2500 },
                .axis_u = { 1, 0, 0 },
                .axis_v = { 0, 1, 0 },
                .normal = { 0, 0, 1 }
            }
        };

        if (!surface_frame_is_valid(&ceiling.frame)) {
            fprintf(stderr, "承載面框架無效。\n");
            return 1;
        }

        world.placements[0] = ceiling;
        world.placement_count = 1;

        /*
         * 建立兩條非實體參考線：
         *
         * guide_u：沿 U，固定 v=300。
         * guide_v：沿 V，固定 u=500。
         */
        if (!create_guide_line(
                1,
                &world.placements[0],
                &world.boundaries[0],
                GUIDE_ALONG_U,
                300,
                &world.guides[0]
            )) {
            fprintf(stderr, "無法建立 U 方向參考線。\n");
            return 1;
        }

        if (!create_guide_line(
                2,
                &world.placements[0],
                &world.boundaries[0],
                GUIDE_ALONG_V,
                500,
                &world.guides[1]
            )) {
            fprintf(stderr, "無法建立 V 方向參考線。\n");
            return 1;
        }

        world.guide_count = 2;

        SurfacePoint2 anchor;

        if (!guide_line_intersection(
                &world.placements[0],
                &world.boundaries[0],
                &world.guides[0],
                &world.guides[1],
                &anchor
            )) {
            fprintf(stderr, "兩條參考線沒有有效交點。\n");
            return 1;
        }

        /*
         * Construct 一支完整角材：
         *
         *   長度 = 1800
         *   A 尺寸 = 27
         *   B 尺寸 = 33
         */
        if (!timber_construct(
                1,
                1800,
                27,
                33,
                false,
                &world.timbers[0]
            )) {
            fprintf(stderr, "無法 Construct 角材。\n");
            return 1;
        }

        /*
         * 將角材 A0 面放到天花承載面：
         *
         *   A0 局部原點放在參考線交點 (500,300)。
         *   長度沿 +U。
         *   B 尺寸沿表面 +N，也就是房間 +Z。
         *
         * 放置後整支角材範圍：
         *
         *   X：500 ～ 2300
         *   Y：300 ～ 327
         *   Z：2500 ～ 2533
         */
        if (!timber_place_a0_on_surface(
                &world.timbers[0],
                &world.placements[0],
                &world.boundaries[0],
                anchor,
                SURFACE_DIRECTION_POS_U,
                SURFACE_DEPTH_POSITIVE_NORMAL
            )) {
            fprintf(stderr, "無法把角材 A0 面放到承載面。\n");
            return 1;
        }

        world.anchors[0] = (TimberAnchor){
            .placement_id = ceiling.id,
            .uv = anchor,
            .anchor_kind = ANCHOR_AT_GUIDES,
            .span_mode = SPAN_EXPLICIT,
            .length_direction = SURFACE_DIRECTION_POS_U,
            .depth_side = SURFACE_DEPTH_POSITIVE_NORMAL,
            .ref_grid_axis = -1,
            .ref_grid_index = -1,
            .ref_hole = -1,
            .ref_edge = -1
        };
        world.timber_count = 1;
    }

    if (world.placement_count == 0 && world.boundary_count == 0 &&
        world.space_count == 0) {
        fprintf(stderr, "場景裡沒有任何物件。\n");
        return 1;
    }

    /* 以下不分來源：兩條路徑都只讀 world。逐片承載面分組印，參考線歸屬各自的面。 */
    for (size_t s = 0; s < world.placement_count; ++s) {
        const PlacementSurface *placement = &world.placements[s];
        const SpaceBoundarySurface *boundary =
            world_find_boundary(&world, placement->boundary_id);

        if (s > 0) {
            printf("\n");
        }

        printf("=== 承載面 ===\n");
        printf("承載面 ID：%" PRIu32 "\n", placement->id);
        printf("承載面原點：");
        print_point3(placement->frame.origin);
        printf("\n");

        SurfaceRegion2 bounds;

        if (placement_local_bounds(placement, boundary, &bounds)) {
            printf("局部範圍：U=[%" PRId64 ",%" PRId64 "]，"
                   "V=[%" PRId64 ",%" PRId64 "]\n",
                   bounds.min_u, bounds.max_u,
                   bounds.min_v, bounds.max_v);
        }

        printf("掛的邊界面：%s\n",
               boundary != NULL ? "有" : "無（自帶矩形）");

        if (boundary != NULL) {
            printf("\n=== 邊界面的邊 ===\n");
            print_boundary_edges(placement, boundary);
        }

        printf("\n=== 參考線 ===\n");

        for (size_t i = 0; i < world.guide_count; ++i) {
            if (world.guides[i].placement_id == placement->id) {
                print_guide_line(placement, boundary, &world.guides[i]);
            }
        }
    }

    for (size_t i = 0; i < world.space_count; ++i) {
        const Space *space = &world.spaces[i];

        printf("\n=== 空間 ===\n");
        printf("空間 ID：%" PRIu32 "\n", space->id);
        printf("成員邊界面：");

        for (size_t f = 0; f < space->boundary_count; ++f) {
            printf("%s%" PRIu32, f == 0 ? "" : " ", space->boundaries[f]);
        }

        printf("\n");
        printf("狀態：%s\n",
               space->closed ? "封閉（六面）" : "部分（彼此一致）");
    }

    for (size_t i = 0; i < world.timber_count; ++i) {
        /* 錨點由兩條參考線交出來時叫「參考線交點」，直接給座標時叫「放置錨點」。 */
        const TimberAnchor *anchor = &world.anchors[i];
        const char *anchor_name =
            anchor->anchor_kind == ANCHOR_AT_GUIDES ? "參考線交點" :
            anchor->anchor_kind == ANCHOR_AT_GRID   ? "格線中心線" :
            anchor->anchor_kind == ANCHOR_AT_EDGE   ? "貼邊" :
                                                      "放置錨點";

        /* 未放置的角材錨點是零值，沒有所屬面——借第一片面推導房間座標。 */
        const PlacementSurface *surface =
            world_find_placement(&world, anchor->placement_id);

        if (surface == NULL) {
            surface = &world.placements[0];
        }

        Point3 anchor_room = surface_point_to_room(
            surface,
            anchor->uv.u,
            anchor->uv.v,
            0
        );

        printf(
            "%s，表面座標："
            "(%" PRId64 ", %" PRId64 ")\n",
            anchor_name,
            anchor->uv.u,
            anchor->uv.v
        );

        printf("%s，房間座標：", anchor_name);
        print_point3(anchor_room);
        printf("\n");
    }

    for (size_t i = 0; i < world.timber_count; ++i) {
        const Timber *timber = &world.timbers[i];

        printf("\n=== 已放置的完整角材 ===\n");
        printf("角材 ID：%" PRIu32 "\n", timber->id);
        printf(
            "尺寸：L=%" PRId64 "，A=%" PRId64 "，B=%" PRId64 " mm\n",
            timber->length,
            timber->size_a,
            timber->size_b
        );

        printf("角材原點：");
        print_point3(timber->origin);
        printf("\n");

        printf("長度軸：");
        print_vector3(timber->axis_length);
        printf("\n");

        printf("A 尺寸軸：");
        print_vector3(timber->axis_a);
        printf("\n");

        printf("B 尺寸軸：");
        print_vector3(timber->axis_b);
        printf("\n");

        printf("\n=== 從完整角材推導六個面 ===\n");

        for (int f = TIMBER_FACE_A0; f < TIMBER_FACE_COUNT; ++f) {
            print_timber_face(timber, (TimberFaceId)f);
        }
    }


    /*
     * 純 C 輸出三視圖 SVG：
     * 只用 stdio 把上面算好的幾何印成 SVG 標籤，
     * 預設放在本原始碼旁邊（current_geometry.svg），--out 可以改。
     */
    Scene scene = scene_from_world(&world);

    SceneLayout layout;

    if (!scene_compute_layout(&scene, &layout)) {
        fprintf(stderr, "無法計算三視圖版面。\n");
        return 1;
    }

    char svg_path[512];

    if (out_path != NULL) {
        int written = snprintf(svg_path, sizeof svg_path, "%s", out_path);

        if (written < 0 || (size_t)written >= sizeof svg_path) {
            fprintf(stderr, "--out 的路徑太長。\n");
            return 1;
        }
    } else if (!path_beside_source(
                   svg_path, sizeof svg_path, "current_geometry.svg")) {
        fprintf(stderr, "無法組出 SVG 的輸出路徑。\n");
        return 1;
    }

    if (!emit_svg_three_views(svg_path, &scene, &layout)) {
        fprintf(stderr, "無法輸出 SVG 三視圖。\n");
        return 1;
    }

    printf("\n=== SVG 三視圖 ===\n");
    printf("已輸出：%s\n", svg_path);

    /*
     * 第二層：只靠作業系統自帶的 user32 / gdi32 開視窗，
     * 畫的內容與 SVG 走同一段幾何走訪，只是後端不同。
     */
#ifdef _WIN32
    if (bench_iters > 0) {
        bench_paint(&scene, &layout, bench_iters);
    }

    if (open_window) {
        printf("\n=== 視窗 ===\n");
        printf("已開啟三視圖視窗，關閉視窗或按 Esc 結束程式。\n");
        fflush(stdout);

        if (!gdi_show_three_views(&world)) {
            fprintf(stderr, "無法開啟視窗。\n");
            return 1;
        }
    }
#else
    (void)open_window;
    (void)bench_iters;
#endif

    return 0;
}
