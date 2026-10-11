#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#ifdef _MSC_VER
#include <intrin.h>
#endif

/*
 * 目前整合版：
 *
 * 1. 建立房間座標中的空間邊界面。
 * 2. 從正交多邊形輪廓與孔推導邊，支援空間、RC 柱樑及其投影。
 * 3. 每條邊可取得局部座標、房間座標，以及它所在的側向平面。
 * 4. 在空間邊界面上建立非實體參考線。
 * 5. 以 at-line / at-face 保存角材定位引用；主格、子格與共用基準皆可推導定位。
 * 6. 宣告角材截面 A × B，長度依合法擋面與跨距推導；變更依賴時預覽並重驗。
 * 7. 把角材 A0 面貼到空間邊界面。
 * 8. 從完整角材推導 A0、A1、B0、B1、START、END 六個面。
 *
 * 第一版限制：
 *
 * - 1 個座標單位 = 1 mm。
 * - 空間邊界面是正交多邊形（可含孔）；舊註曾寫「矩形」，已過時。
 * - 表面座標框架只接受正交的單位軸向量。
 * - 角材長度方向只能沿表面的 ±U 或 ±V。
 *
 * 配套：geometry-guide/ 下的導讀頁內嵌本檔快照，
 * 改動本檔後須重跑 make_guide.py + check_panels.py;
 * 條號註解有增減時一併重跑 sync_axiom_reader.py(正典閱讀器
 * 由 公理層.md 與 公理層-白話.md 同步;make_axiom_reader.py 已退役)。
 */

typedef int64_t Coord;

/* 支援的定義座標／尺寸：±100 km，保留整數乘積與最多 32 頂點累加的餘量。
 * ID 仍使用完整 uint32 範圍。衍生世界座標可以較大，不能拿 ID 的解析器讀尺寸。 */
#define COORD_LIMIT INT64_C(100000000)
static bool coord_in_range(Coord value)
{
    return value >= -COORD_LIMIT && value <= COORD_LIMIT;
}

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
/* 公理 D2：承載面框架——原點 + 三個單位整數軸，room = origin + u·U + v·V + w·N。 */

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
/* 公理 I1：承載面 frame 合法——U、V 單位正交且 U×V=N。 */
static bool surface_frame_is_valid(const SurfaceFrame *frame)
{
    if (frame == NULL || !coord_in_range(frame->origin.x) ||
        !coord_in_range(frame->origin.y) || !coord_in_range(frame->origin.z)) {
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
/* A line may gain one interval per hole interval; this conservative
 * bound covers the outline and every allowed hole without truncation. */
#define GUIDE_MAX_SEGMENTS (POLY_MAX_VERTICES * (POLY_MAX_HOLES + 1))

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
        loop->count > POLY_MAX_VERTICES) {
        return false;
    }

    /* 邊的軸平行與非零長檢查。 */
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        if (!coord_in_range(a.u) || !coord_in_range(a.v)) return false;

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
 * 矩形中心是否在環內（射線法，與 poly_contains_point 同一套半開區間）。
 * 中心座標是 (min+max)/2，可能是半整數，所以全部放大 2 倍後比較，保持純整數。
 *
 * 只對「中心不在任何環邊上」的情形給出可靠答案；poly_contains_rect 不需要這個前提：
 * 中心在環邊上時，那條邊必穿入矩形內部（中心嚴格在矩形內部），
 * 另一道檢查（segment2_crosses_rect_interior）本來就會拒絕。
 */
static bool poly_rect_center_inside(
    const PolygonLoop2 *loop,
    Coord min_u, Coord min_v, Coord max_u, Coord max_v
)
{
    Coord cu2 = min_u + max_u;   /* 2 × 中心 u */
    Coord cv2 = min_v + max_v;   /* 2 × 中心 v */
    int crossings = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u == b.u) {   /* 只有直立邊會與水平射線交叉 */
            Coord v_lo2 = 2 * coord_min(a.v, b.v);
            Coord v_hi2 = 2 * coord_max(a.v, b.v);

            if (cv2 >= v_lo2 && cv2 < v_hi2 && cu2 < 2 * a.u) {
                ++crossings;
            }
        }
    }

    return (crossings & 1) != 0;
}

/*
 * 軸平行矩形 ⊆ 環（含邊界）。GEO-257：
 *
 * 不變量：沒有任何環邊穿入矩形開內部（segment2_crosses_rect_interior）時，
 * 矩形開內部不碰環的邊界，而開內部是連通的——所以它要嘛整個在環內，
 * 要嘛整個在環外；任取其中一點（取中心）判內外即可定案。
 * 反之，只要有環邊穿入矩形開內部，邊的兩側一內一外，矩形必跨出環。
 * 所以：矩形 ⊆ 環 ⇔ 無環邊穿入開內部 且 中心在環內。
 *
 * 「四角都在環內」不是充分條件：矩形可以整個落在環外的凹槽裡，
 * 四個角剛好都落在槽壁（環邊或環頂點）上、沒有任何環邊穿過內部
 * （例：槽 x∈[40,60]、y∈[40,100] 內的矩形 [40,60]×[50,70]）。
 * 四角檢查只留作便宜的快退（它是必要條件，不影響結果）；
 * 這樣新判定只會比舊判定多拒絕、不會多接受。
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

    /* 開內部要嘛全在環內、要嘛全在環外；中心在外 → 整個矩形在環外。
     * 與下面的「環邊穿入」檢查互相獨立，順序不影響結果。 */
    if (!poly_rect_center_inside(loop, min_u, min_v, max_u, max_v)) {
        return false;
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
/* 公理 D3：空間邊界面——純局部 2D，不含世界位置。 */

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
/* 公理 D4：承載面——frame + 有效範圍（引用邊界面輪廓，或自帶 rect）。 */

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

/* D4: self-contained rectangles have the same effective outline as a boundary. */
static const SpaceBoundarySurface *placement_effective_boundary(
    const PlacementSurface *p, const SpaceBoundarySurface *b, SpaceBoundarySurface *storage)
{
    if (b) return b;
    memset(storage,0,sizeof *storage);
    placement_outline(p,NULL,&storage->outline);
    return storage;
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
/* 公理 D8：邊是輪廓的第 i 條邊，端點不存、由環即時推出（D9）。 */
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

#include "geometry-core/reference_types.h"
#include "geometry-core/parameter_types.h"
#include "geometry-core/engineering_types.h"
#include "geometry-core/assembly_types.h"
#include "geometry-core/section_profile_types.h"

typedef struct {
    GuideLineId id;
    SurfaceId placement_id;     /* 屬於哪片承載面 */
    GuideDirection direction; /* derived for DATUM */
    GuideSource source;
    uint32_t datum_id;
    bool resolved; /* evaluated cache, never serialized */

    /*
     * GUIDE_ALONG_U：固定 v = offset。
     * GUIDE_ALONG_V：固定 u = offset。
     */
    Coord offset; /* evaluated cache, rebuilt from expression */
    char expression[REF_EXPR_MAX];
} GuideLine;
/* 公理 D6：參考線——承載面 + 方向 + offset；線段不存，用時截出（D9）。 */

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

/* 公理 I7：參考線 offset 必須落在有效範圍的該軸外接區間內。 */

/*
 * 移動既有參考線 = 改位置引用式。
 * 範圍檢查與 create 共用，依賴者重算並經 I8a 確認。
 */
/* 公理 I7：move 與 create 過同一關——構造上產生不出非法 offset（R5）。 */

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
        /* D6/I7: existence and visibility are independent, including rectangles. */
        if (!guide_offset_in_range(surface, NULL, guide->direction, guide->offset)) return 0;
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
    SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
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
            SurfaceSegment2 next[GUIDE_MAX_SEGMENTS];
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
                if (h_lo > s_lo && h_hi < s_hi && next_count < GUIDE_MAX_SEGMENTS) {
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


/* ============================================================
 * 參考網格（ReferenceGrid）：兩軸各一份「線的定義」
 *
 *   axis[0]：u 座標集 → 線沿 V 走；
 *   axis[1]：v 座標集 → 線沿 U 走。
 *
 * 公理 D10 / D10a / I10：
 *   1. 每片承載面最多一座主網格；D19 子網格另依父格矩形派生；
 *   2. 每軸的定義三選一——明寫 / 等差 / 面材，兩軸互相獨立；
 *   3. 推導出的座標序列嚴格遞增、且每條落在承載面該軸的外接區間內；
 *   4. 只存定義（D9）：展開後的座標不進 World，用時由 grid_axis_lines 推出。
 *      「該軸未宣告」（GRID_SRC_NONE）與「該軸推導出零條線」是兩回事。
 * ============================================================ */

#define GRID_MAX_LINES 64
#define GRID_MAX_PHASES 8

typedef enum {
    GRID_SRC_NONE = 0,      /* 該軸未宣告 */
    GRID_SRC_EXPLICIT,      /* 明寫座標 */
    GRID_SRC_SERIES,        /* 等差：start / step / count（GEO-098） */
    GRID_SRC_REPEAT,
    GRID_SRC_REPEAT_PANEL,
    GRID_SRC_PANEL          /* 面材：panel / gap / anchor（GEO-100、D10a） */
} GridSource;

typedef struct {
    int source;             /* GridSource */

    /* GRID_SRC_EXPLICIT */
    Coord coords[GRID_MAX_LINES];
    size_t count;

    /* GRID_SRC_SERIES（GEO-098 起用） */
    Coord start;
    Coord step;
    size_t series_count;

    /* GRID_SRC_PANEL（GEO-100 起用；anchor 在宣告當下具體化，D10a） */
    Coord panel;
    Coord gap;
    Coord anchor;
    bool anchor_explicit;   /* 只影響 dump 是否輸出 from，不影響推導 */
    ParameterRef parameters[6]; /* phase, step, panel, gap, anchor, stagger (D10b) */
    Coord stagger;          /* D10b: odd-band offset; meaningful only when stagger_set */
    bool stagger_set;
} GridAxisDef;

#define WORLD_MAX_GRID_SYSTEMS 16
#define GRID_SYSTEM_NAME_MAX 96
#define GRID_MAX_SUBDIVISION_RULES 32
#define GRID_SUBDIVISION_CAPABILITY "grid-subdivision-rules/1"
typedef struct {
    uint32_t key;
    char name[GRID_SYSTEM_NAME_MAX+1];
    bool all_cells;
    int64_t cell[2];
    unsigned divisions[2];
} GridSubdivisionRule;
typedef struct {
    uint32_t grid_id,system_id,rule_key;
    int64_t cell[2];
    int axis;
    uint32_t inner_index;
} GridRuleLineRef;
typedef struct {
    uint32_t id;
    char name[GRID_SYSTEM_NAME_MAX+1];
    GridAxisDef axis[2];
    int main_along;
    GridSubdivisionRule rules[GRID_MAX_SUBDIVISION_RULES];
    size_t rule_count;
    uint32_t next_rule_key; /* 0=exhausted; whole World undo restores allocator. */
} GridSystem;
#define WORLD_MAX_GRID_BINDINGS 32
typedef struct {
    uint32_t id,boundary_id,system_id,vertex_key;
    int64_t cell[2];
    uint32_t anchor_num[2],anchor_den[2];
} GridBinding;
typedef struct {
    uint32_t boundary_id;
    size_t loop_count,counts[POLY_MAX_HOLES+1];
    uint32_t keys[POLY_MAX_HOLES+1][POLY_MAX_VERTICES];
    uint32_t next_key;
} BoundaryVertexKeys;
typedef struct {
    int64_t index; Coord coordinate;
    size_t segment_count; SurfaceSegment2 segments[GUIDE_MAX_SEGMENTS];
    int64_t segment_band[GUIDE_MAX_SEGMENTS]; /* D10b: other-axis cell, only when segment_has_band */
    bool segment_has_band[GUIDE_MAX_SEGMENTS];
} GridQueryLine;
typedef struct {
    bool defined; int64_t first,last; uint64_t total,stride;
    size_t count; GridQueryLine lines[GRID_MAX_LINES];
} GridQueryAxis;

typedef struct {
    uint32_t id;
    SurfaceId placement_id;
    bool from_system;
    bool from_binding;
    uint32_t binding_id;
    Coord lattice_base[2],lattice_step[2];
    int64_t lattice_index[2];
    bool lattice_cell;
    int64_t lattice_cell_index[2];
    uint32_t system_id;
    Coord system_origin[2];

    GridAxisDef axis[2];
    /* D10: 0 = 未設定, 1 = 沿 u, 2 = 沿 v。 */
    int main_along;
    /* D19: only a parent and cell references are stored; geometry is derived. */
    bool is_subgrid;
    uint32_t parent_id;
    int cell_ref[2][2]; /* -1=min, -2=max, >=0 main-grid line index */
    unsigned divisions[2];
} ReferenceGrid;

#include "geometry-core/grid_lattice.inc"

static bool grid_coord_list_is_valid(const Coord coords[], size_t count)
{
    for (size_t i = 0; i < count; ++i) {
        if (i > 0 && coords[i] <= coords[i - 1]) {
            return false;   /* 必須嚴格遞增 */
        }
    }

    return true;
}

/*
 * 唯一的展開入口（D9：只存定義，線在用時推出）。
 * grid_is_valid、三視圖、at-line grid 放置與日後的子網格全部走它，
 * 不得出現第二份推導邏輯。
 *
 *   axis   0 = u 座標集合（沿 V 走的線），1 = v 座標集合
 *   out    呼叫端提供的堆疊緩衝，容量必須是 GRID_MAX_LINES
 *   err    可為 NULL（重驗只要 true/false）
 *
 * 回傳 true 且 *out_count == 0 是合法結果（面小於一片面材）。
 */
static bool grid_axis_lines(
    const ReferenceGrid *grid,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    int axis,
    Coord out[GRID_MAX_LINES],
    size_t *out_count,
    char *err,
    size_t err_cap
)
{
    if (grid == NULL || grid->is_subgrid || placement == NULL || out == NULL ||
        out_count == NULL || axis < 0 || axis > 1 ||
        grid->placement_id != placement->id) {
        return false;
    }

    if (grid->from_binding) {
        SurfaceRegion2 bounds; GridQueryAxis result;
        if (!placement_local_bounds(placement,boundary,&bounds) ||
            !grid_lattice_window(grid,axis,axis?bounds.min_v:bounds.min_u,
                axis?bounds.max_v:bounds.max_u,GRID_MAX_LINES,false,&result,err,err_cap)) return false;
        *out_count=result.count;
        for (size_t i=0;i<result.count;++i) out[i]=result.lines[i].coordinate;
        return true;
    }
    const GridAxisDef *def = &grid->axis[axis];

    *out_count = 0;

    if (def->source == GRID_SRC_NONE) {
        if (err != NULL) {
            snprintf(err, err_cap, "這一軸沒有宣告格線");
        }
        return false;
    }

    SurfaceRegion2 bounds;

    if (!placement_local_bounds(placement, boundary, &bounds)) {
        return false;
    }

    const Coord lo = axis == 0 ? bounds.min_u : bounds.min_v;
    const Coord hi = axis == 0 ? bounds.max_u : bounds.max_v;
    size_t n = 0;

    if (def->source == GRID_SRC_EXPLICIT) {
        if (def->count > GRID_MAX_LINES) {
            return false;
        }

        for (size_t k = 0; k < def->count; ++k) {
            out[n++] = def->coords[k];
        }
    } else if (def->source == GRID_SRC_SERIES) {
        /* D10：第 k 條 = start + k·step；step > 0 本身就保證嚴格遞增。 */
        if (def->series_count == 0 ||
            def->series_count > GRID_MAX_LINES ||
            def->step <= 0) {
            return false;
        }

        for (size_t k = 0; k < def->series_count; ++k) {
            out[n++] = def->start + (Coord)k * def->step;
        }
    } else if (def->source == GRID_SRC_PANEL) {
        /*
         * D10a：週期 T = panel + gap，第 k 條縫中心線
         *   c_k = a + k·T + panel + gap/2，
         * 產生條件 a+(k+1)·T < hi——整條縫落在範圍內，且其後仍有非空的面材本體。
         * 不滿足就停：末端是裁切片，合法，不因「除不盡」而拒絕。
         */
        const Coord T = def->panel + def->gap;

        if (def->panel <= 0 || def->gap < 0 ||
            def->anchor < lo || def->anchor >= hi) {
            if (err != NULL) {
                snprintf(err, err_cap,
                         "面材參數不合法（面材寬 > 0、縫寬非負、"
                         "起算點須落在承載面範圍內）");
            }
            return false;
        }

        for (size_t k = 0; ; ++k) {
            const Coord gap_hi = def->anchor + (Coord)(k + 1) * T;

            if (gap_hi >= hi) {
                break;
            }

            if (n == GRID_MAX_LINES) {
                if (err != NULL) {
                    snprintf(err, err_cap,
                             "面材排法推導出的格線超過單軸上限");
                }
                return false;
            }

            out[n++] = def->anchor + (Coord)k * T
                     + def->panel + def->gap / 2;
        }
    } else {
        if (err != NULL) {
            snprintf(err, err_cap, "這一軸的格線來源尚未支援");
        }
        return false;
    }

    /* I10：嚴格遞增。 */
    if (!grid_coord_list_is_valid(out, n)) {
        if (err != NULL) {
            snprintf(err, err_cap, "座標必須嚴格遞增");
        }
        return false;
    }

    /* I10：每條都落在該軸外接區間內——與 guide offset 同一條規則。 */
    for (size_t k = 0; k < n; ++k) {
        if (out[k] < lo || out[k] > hi) {
            if (err != NULL) {
                snprintf(err, err_cap, "座標要落在承載面外接範圍內");
            }
            return false;
        }
    }

    *out_count = n;
    return true;
}

static bool grid_is_valid(
    const ReferenceGrid *grid,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary
)
{
    if (grid == NULL || placement == NULL ||
        grid->placement_id != placement->id) {
        return false;
    }

    if (grid->from_binding) return !grid->from_system && !grid->is_subgrid &&
        grid->lattice_step[0]>0 && grid->lattice_step[1]>0;
    /* I10: 主支方向須有對應格線來源；u 座標線沿 v，反之亦然。 */
    if (grid->main_along < 0 || grid->main_along > 2 ||
        (grid->main_along == 1 && grid->axis[1].source == GRID_SRC_NONE) ||
        (grid->main_along == 2 && grid->axis[0].source == GRID_SRC_NONE)) {
        return false;
    }

    /* I10：兩軸皆未宣告 → 拒絕（單軸網格合法）。 */
    if (grid->axis[0].source == GRID_SRC_NONE &&
        grid->axis[1].source == GRID_SRC_NONE) {
        return false;
    }

    Coord lines[GRID_MAX_LINES];
    size_t n;

    for (int a = 0; a < 2; ++a) {
        if (grid->axis[a].source == GRID_SRC_NONE) {
            continue;
        }

        if (!grid_axis_lines(grid, placement, boundary, a,
                             lines, &n, NULL, 0)) {
            return false;
        }
    }

    return true;
}

/* D19 / I25 / R23: canonical single-cell subgrid derivation and finite clips. */
#include "geometry-core/subgrids.inc"

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

/*
 * D15 角材角色與裁切優先級（cut priority）：數字越小越優先——
 * 空間邊界（外輪廓邊、孔邊、柱面）= 0、boundary 邊界材 = 1、
 * primary 主支 = 2、secondary 副支 = 3、custom 由 priority N（N≥1）明寫。
 * custom 的 priority 只參與 I19 的數值比較，不取得任何角色專屬義務。
 */
typedef enum {
    TIMBER_ROLE_BOUNDARY = 0,
    TIMBER_ROLE_PRIMARY,
    TIMBER_ROLE_SECONDARY,
    TIMBER_ROLE_CUSTOM
} TimberRole;

typedef struct {
    TimberId id;

    Coord length;
    Coord size_a;
    Coord size_b;

    /*
     * D15：角色是宣告；「是否真的在邊界上」是推導（R18），
     * 兩者不一致 = 拒絕，不改宣告去遷就幾何。
     * cut_priority 是生效值：非 custom 由角色決定（1/2/3），
     * custom 用宣告的 N。
     */
    TimberRole role;
    Coord cut_priority;

    /*
     * true = auto 角材（timber id A B）：length 不是輸入，
     * 而是每次從位置引用與可延伸區間重建的結果。
     * false 已廢除，建構子拒絕。
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
/* 公理 D7：角材——截面 + 長度模式 + 局部三軸 + 原點；八角不存（D9）。 */

static const char *timber_role_name(TimberRole role)
{
    switch (role) {
        case TIMBER_ROLE_BOUNDARY:  return "boundary";
        case TIMBER_ROLE_PRIMARY:   return "primary";
        case TIMBER_ROLE_SECONDARY: return "secondary";
        case TIMBER_ROLE_CUSTOM:    return "custom";
        default:                    return "?";
    }
}

/* Construct 一支完整角材，但此時尚未放進空間邊界面。 */
static bool timber_construct(
    TimberId id,
    Coord length,
    Coord size_a,
    Coord size_b,
    bool auto_length,
    TimberRole role,
    Coord custom_priority,
    Timber *out_timber
)
{
    if (out_timber == NULL ||
        size_a <= 0 ||
        size_b <= 0 ||
        !auto_length ||
        (auto_length && length != 0) ||
        (role == TIMBER_ROLE_CUSTOM && custom_priority < 1)) {
        return false;
    }

    *out_timber = (Timber){
        .id = id,
        .length = length,
        .size_a = size_a,
        .size_b = size_b,
        .auto_length = auto_length,
        .placed = false,
        .role = role,
        .cut_priority = role == TIMBER_ROLE_CUSTOM
            ? custom_priority
            : (Coord)role + 1,

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
    SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
    size_t n = guide_line_get_local_segments(
        surface, boundary, guide, segs, GUIDE_MAX_SEGMENTS);

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
/* 公理 D5：空間——建構子參數 = 一組邊界面 id，成員不可變。 */

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

/* a * b / den，向零截斷。D1 的 ±1e8 讓 dx*t_num 三次乘超出 int64；
 * 用 128-bit 中間值，避免拾取路徑在合法尺寸下 UB。 */
static Coord mul_div_i64(Coord a, Coord b, Coord den)
{
    if (den == 0) {
        return 0;
    }
#if defined(_MSC_VER)
    __int64 hi;
    __int64 lo = _mul128(a, b, &hi);
    __int64 rem;
    return (Coord)_div128(hi, (unsigned __int64)lo, den, &rem);
#elif defined(__SIZEOF_INT128__)
    return (Coord)((__int128)a * (__int128)b / (__int128)den);
#else
    long double x = (long double)a * (long double)b / (long double)den;
    if (x > (long double)INT64_MAX) return INT64_MAX;
    if (x < (long double)INT64_MIN) return INT64_MIN;
    return (Coord)x;
#endif
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

    Coord cx = a.x + mul_div_i64(dx, t_num, len2);
    Coord cy = a.y + mul_div_i64(dy, t_num, len2);
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
            SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
            size_t seg_count;

            if (guide->placement_id != surface->id) {
                continue;
            }

            seg_count = guide_line_get_local_segments(
                surface, boundary, guide, segs, GUIDE_MAX_SEGMENTS);

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
                Coord coords[GRID_MAX_LINES]; int64_t indices[GRID_MAX_LINES];
                size_t n = 0;
                if (!grid_sample_indices_in(scene->grids, scene->grid_count, grid, surface, boundary, axis,
                                     indices,coords, &n)) {
                    continue;   /* 該軸未宣告或推不出線：不畫（D9） */
                }

                for (size_t li = 0; li < n; ++li) {
                    SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
                    size_t seg_count = grid_line_segments(
                        scene->grids, scene->grid_count, grid, surface, boundary,
                        axis, indices[li], segs, GUIDE_MAX_SEGMENTS);

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
                                     grid->from_binding?"格線%" PRIu32 "（取樣）":"格線%" PRIu32, grid->id);
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
/* 公理 R1：拾取 = 畫家演算法——同一點多個命中時取最後畫的。 */
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
            pick.column = -1;
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
    for (size_t pi=0;pi<scene->placement_count;++pi) {
    for (size_t i = 0; i < scene->guide_count; ++i) {
        if (scene->guides[i].placement_id!=scene->placements[pi].id) continue;
        const GuideLine *guide = &scene->guides[i];
        const PlacementSurface *surface =
            scene_find_placement(scene, guide->placement_id);
        const SpaceBoundarySurface *boundary;
        SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
        size_t seg_count;

        if (surface == NULL) {
            continue;
        }

        boundary = scene_placement_boundary(scene, surface);
        seg_count = guide_line_get_local_segments(
            surface, boundary, guide, segs, GUIDE_MAX_SEGMENTS);

        for (size_t k = 0; k < seg_count; ++k) {
            ViewPoint2 a = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].start.u, segs[k].start.v, 0));
            ViewPoint2 b = view_project(view,
                surface_point_to_room(surface,
                                      segs[k].end.u, segs[k].end.v, 0));
            Coord d2 = view_dist2_to_segment(p, a, b);

            if (d2 <= best2) {
                pick.guide = (int)i;
            }
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
        SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
        size_t seg_count = 0;

        if (surface != NULL) {
            seg_count = guide_line_get_local_segments(
                surface,
                scene_placement_boundary(scene, surface),
                guide, segs, GUIDE_MAX_SEGMENTS);
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

    /* A previous buffered write can fail even when fclose itself succeeds. */
    bool failed = ferror(out) != 0;
    if (fclose(out) != 0) failed = true;
    if (failed) {
        /* Remove an incomplete regular output only; never unlink a device such as /dev/full. */
        struct stat output_stat;
        if (stat(path, &output_stat) == 0) {
#if defined(_WIN32) || defined(_MSC_VER)
            if ((output_stat.st_mode & _S_IFMT) == _S_IFREG) remove(path);
#else
            if (S_ISREG(output_stat.st_mode)) remove(path);
#endif
        }
    }
    return !failed;
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
#define SCENE_MAX_LINE    16384
#define SCENE_MAX_TOKENS  640

/*
 * 一份場景 = 若干空間邊界面（純 2D 輪廓）+ 承載面（3D 嵌入）
 * + 參考線 + 角材 + 空間。
 * 上限都是常數，資料就放在呼叫者給的 World 裡，不做動態配置——
 * World 是 POD，整份 memcpy 就是交易用的快照。
 */
#define WORLD_MAX_BOUNDARIES  16
#define WORLD_MAX_PLACEMENTS  16
#define WORLD_MAX_GUIDES      16
#define WORLD_MAX_GRIDS       16
#define WORLD_MAX_TIMBERS     64
#define WORLD_MAX_SPACES      4
#define WORLD_MAX_RC          32
#define WORLD_MAX_CANVAS_POS  (WORLD_MAX_BOUNDARIES + WORLD_MAX_PLACEMENTS + WORLD_MAX_SPACES + WORLD_MAX_RC * 2 + WORLD_MAX_GRID_SYSTEMS + WORLD_MAX_GRID_BINDINGS + PARAM_CARD_MAX)

/* 一個空間最多八片邊界成員；零成員 = 空容器（公理 D5）。 */
#define SPACE_MAX_MEMBERS 8

/*
 * 角材的放置錨點：哪片承載面、表面上的哪一點、怎麼來的。
 * 重宣告交易要靠它重驗角材，所以放法也要留著。
 *
 * 引用是定義；uv 與 length 僅是 reference_rebuild 產生的衍生快取。
 * 每次交易由引用重新推導；持久化只輸出引用。
 */

typedef enum {
    ANCHOR_AT,          /* at u v：明寫錨點 */
    ANCHOR_AT_GUIDES,   /* at-guides 線1 線2：交點凍結 */
    ANCHOR_AT_GRID,     /* at-line grid 網id 軸 索引：中心線對齊格線 */
    ANCHOR_AT_EDGE,     /* at-face e3 / h1e2 / t7 */
    ANCHOR_AT_LINE,     /* at-line guide id; preserve legacy enum value */
    ANCHOR_AT_RULE      /* source-owned rule line, whole-cell scope */
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

    /* 參照來源：每次重建時用來求位置與跨距。 */
    uint32_t ref_grid;      /* ANCHOR_AT_GRID：網格 id */
    int ref_grid_axis;      /* 0 = u 座標集合，1 = v 座標集合 */
    int64_t ref_grid_index;
    bool ref_grid_has_band; /* D10b: set only for a staggered axis */
    int64_t ref_grid_band;
    GridRuleLineRef ref_rule;
    int ref_hole;           /* ANCHOR_AT_EDGE：-1 外輪廓，否則孔 index */
    int ref_edge;           /* 邊 index */
    bool has_through;
    Coord through;          /* R6(c) span selector */
    uint32_t ref_guide, ref_timber;
    bool ref_is_timber;
    uint64_t order;         /* placement dependency order (I9) */
    bool has_between;
    ReferenceFace between[2];
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
    CANVAS_POS_BEAM,           /* 樑卡：以樑 id 為鍵 */
    CANVAS_POS_GRID_BINDING,
    CANVAS_POS_PARAMETER,
    CANVAS_POS_GRID_SYSTEM,     /* D29: independent reusable grid definition */
    CANVAS_POS_ASSEMBLY_RULE, CANVAS_POS_ASSEMBLY_BINDING
} CanvasPosKind;

typedef struct {
    int kind;                  /* CanvasPosKind */
    uint32_t id;
    Coord x, y;                /* 畫布座標（展示用，非幾何） */
} CanvasPos;
/* 公理 D12：畫布座標——純展示中繼資料，不參與任何幾何推導。 */

typedef struct World {
    SpecValue specs[WORLD_MAX_SPECS];
    size_t spec_count;
    DatumPlane datums[WORLD_MAX_DATUMS];
    size_t datum_count;
    uint64_t next_order;
    SpaceBoundarySurface boundaries[WORLD_MAX_BOUNDARIES];
    size_t boundary_count;
    BoundaryVertexKeys vertex_keys[WORLD_MAX_BOUNDARIES];
    size_t vertex_key_count;
    GridBinding grid_bindings[WORLD_MAX_GRID_BINDINGS];
    size_t grid_binding_count;

    PlacementSurface placements[WORLD_MAX_PLACEMENTS];
    size_t placement_count;

    GuideLine guides[WORLD_MAX_GUIDES];
    size_t guide_count;

    GridSystem grid_systems[WORLD_MAX_GRID_SYSTEMS];
    size_t grid_system_count;
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
    SectionProfileState section_profiles;
    AssemblyState assembly;
    EngineeringState engineering;
    ParameterState parameters;
} World;

static const GridSystem *world_find_grid_system(const World *w,uint32_t id)
{
    for (size_t i=0;i<w->grid_system_count;++i) if (w->grid_systems[i].id==id) return &w->grid_systems[i];
    return NULL;
}

/* 命中物 → 一行描述。網頁橋接與 GDI 狀態列共用；無命中時寫入空字串。 */
static void scene_describe_pick(const Scene *scene, const World *world,
                                const ScenePick *p, char *buf, size_t cap)
{
    buf[0] = '\0';
    if (p == NULL || scene_pick_is_none(p)) {
        return;
    }

    if (p->column >= 0 && p->column < (int)scene->column_count) {
        snprintf(buf, cap, "柱%" PRIu32, scene->columns[p->column].id);
        return;
    }
    if (p->beam >= 0 && p->beam < (int)scene->beam_count) {
        snprintf(buf, cap, "樑%" PRIu32, scene->beams[p->beam].id);
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
static const GridBinding *world_find_grid_binding(const World *w,uint32_t id)
{
    for (size_t i=0;i<w->grid_binding_count;++i) if(w->grid_bindings[i].id==id) return &w->grid_bindings[i];
    return NULL;
}
static const BoundaryVertexKeys *world_find_vertex_keys(const World *,uint32_t);
static bool boundary_vertex_by_key(const World *,uint32_t,uint32_t,SurfacePoint2 *);
static bool boundary_keys_reconcile(World *,const World *,char *,size_t);
static bool boundary_keys_initialize(World *,uint32_t);
static void boundary_geometry_hash(const SpaceBoundarySurface *,char [65]);
static bool grid_bindings_rebuild(World *,char *,size_t);
static bool apply_grid_binding_application(const char *,int,char **,int,World *);
static bool grid_systems_rebuild(World *,char *,size_t);
static bool eng_object_bound(const World *,int,uint32_t);
static uint64_t g_definition_revision;
static char g_engineering_error[256];
static bool sp_rebuild(World *,char *,size_t);
static void sp_capture_diagnostics(World *);
static bool assembly_rebuild(World *,char *,size_t);
static bool assembly_owned(const World *,uint32_t);
static void assembly_owned_prefix(const World *,uint32_t,const char *,FILE *);
static bool assembly_generation_prepare(World *);
static bool assembly_generation_check(const World *);
static bool assembly_generation_integrity(const World *);
static const AsmRuleVersion *assembly_rule(const World *,uint32_t,uint32_t);
static AsmBinding *assembly_binding(World *,uint32_t);
static bool engineering_rebuild(World *,char *,size_t);
static bool parameters_rebuild(World *,char *,size_t);
static const ParameterSet *parameter_find(const World *,uint32_t);
static bool parameter_ref_parse(const char *,ParameterRef *);
static bool parameter_coord(const World *,ParameterRef,Coord *);
static char g_parameter_error[512];
static bool engineering_dump_timber(const World *,const Timber *,FILE *);
static bool world_definitions_equal(const World *a,const World *b)
{
    /* Compare around display-only metadata without two multi-megabyte stack copies. */
    const unsigned char *x=(const unsigned char*)a,*y=(const unsigned char*)b;
    size_t first=(const unsigned char*)&a->canvas_pos-x;
    size_t last=(const unsigned char*)(&a->canvas_pos_count+1)-x;
    return !memcmp(x,y,first) && !memcmp(x+last,y+last,sizeof *a-last);
}

static const World *g_subgrid_before;
static void reference_capture_trial(const World *world);

static bool reference_preview_pending(void);
static uint32_t reference_preview_token(void);
static bool reference_preview_valid(void);
static bool reference_rebuild(World *world);
static bool reference_check_all(const World *w);
static bool reference_snap(World *world, uint32_t pid, GuideDirection dir, uint32_t exclude, Coord at, Coord radius, char *out);
static bool apply_reference_guide(const char *, int, char **, int, World *);
static bool apply_reference_move(const char *, int, char **, int, World *);
static bool apply_reference_place(const char *, int, char **, int, World *);
static bool apply_spec_line(const char *, int, char **, int, World *);
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
static int   g_hist_record_redo_n;
static bool  g_hist_record_evicted;
static World g_hist_evicted;

/* L2 歷史群組:history-begin 時的世界快照;群組內各行不各自記歷史,
 * end 時整組算一步;任一行失敗 → 整組回到 begin 前,不留半套用。 */
static bool  g_hist_grouping;
static bool  g_hist_group_dirty;
static World g_hist_group_base;

/* 變更成功前呼叫：把現況壓入 undo 疊並清掉 redo。 */
static void history_record(const World *w)
{
    g_hist_record_redo_n = g_hist_redo_n;
    g_hist_record_evicted = g_hist_undo_n >= HISTORY_MAX;
    if (g_hist_record_evicted) {
        g_hist_evicted = g_hist_undo[0];
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
    g_hist_grouping = false;
    g_hist_group_dirty = false;
}

/* apply 失敗時呼叫：剛記的快照作廢（世界沒變）。 */
static void history_unrecord(void)
{
    if (g_hist_undo_n > 0) {
        --g_hist_undo_n;
    }
    if (g_hist_record_evicted) {
        memmove(&g_hist_undo[1], &g_hist_undo[0],
                sizeof(World) * g_hist_undo_n);
        g_hist_undo[0] = g_hist_evicted;
        ++g_hist_undo_n;
    }
    g_hist_redo_n = g_hist_record_redo_n;
    g_hist_record_evicted = false;
}

/* canvas-pos 目標物件是否存在——L1 還原時過濾還原後已消失的殘留位。 */
static bool world_canvas_target_exists(const World *w, int kind, uint32_t id)
{
    return
        kind == CANVAS_POS_BOUNDARY  ? world_find_boundary(w, id)  != NULL :
        kind == CANVAS_POS_PLACEMENT ? world_find_placement(w, id) != NULL :
        kind == CANVAS_POS_SPACE     ? world_find_space(w, id)     != NULL :
        kind == CANVAS_POS_COLUMN    ? world_find_column(w, id)    != NULL :
        kind == CANVAS_POS_GRID_BINDING ? world_find_grid_binding(w,id) != NULL :
        kind == CANVAS_POS_ASSEMBLY_RULE ? assembly_rule(w,id,0) != NULL :
        kind == CANVAS_POS_ASSEMBLY_BINDING ? assembly_binding((World*)w,id) != NULL :
        kind == CANVAS_POS_PARAMETER ? parameter_find(w,id) != NULL :
        kind == CANVAS_POS_GRID_SYSTEM ? world_find_grid_system(w,id) != NULL :
                                       world_find_beam(w, id)      != NULL;
}

/* L1:canvas-pos 是展示中繼資料,不進歷史。
 * 還原快照後,還原前仍存在的物件保留使用者當下的擺位;
 * 只存在於快照的物件(刪除後復活)沿用快照位;
 * 還原後已不存在的物件,其殘留位丟棄。 */
static void history_restore_world(World *w, const World *snap)
{
    CanvasPos cur[WORLD_MAX_CANVAS_POS];
    size_t cur_n = w->canvas_pos_count;

    if (cur_n > 0) {
        memcpy(cur, w->canvas_pos, cur_n * sizeof *cur);
    }
    *w = *snap;

    for (size_t i = 0; i < cur_n; ++i) {
        const CanvasPos *cp = &cur[i];
        size_t j;

        if (!world_canvas_target_exists(w, cp->kind, cp->id)) continue;
        for (j = 0; j < w->canvas_pos_count; ++j) {
            if (w->canvas_pos[j].kind == cp->kind &&
                w->canvas_pos[j].id == cp->id) {
                w->canvas_pos[j].x = cp->x;
                w->canvas_pos[j].y = cp->y;
                break;
            }
        }
        if (j == w->canvas_pos_count &&
            w->canvas_pos_count < WORLD_MAX_CANVAS_POS) {
            w->canvas_pos[w->canvas_pos_count++] = *cp;
        }
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
    history_restore_world(w, &g_hist_undo[--g_hist_undo_n]);
    ++g_definition_revision;
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
    history_restore_world(w, &g_hist_redo[--g_hist_redo_n]);
    ++g_definition_revision;
    return true;
}

/* 群組內任一行失敗:回到 begin 前快照並關閉群組,不留半套用。 */
static void history_group_rollback(World *world)
{
    *world = g_hist_group_base;
    g_hist_grouping = false;
    g_hist_group_dirty = false;
}

/* 互動入口共用：undo/redo・歷史群組攔截 + 變更前記快照（失敗自動取消）。
 * 回傳值同 apply_scene_line。 */
static bool apply_interactive_tokens(
    const char *path, int line_no, char *tokens[], int count, World *world)
{
    if (count > 0 && (!strcmp(tokens[0], "preview") || !strcmp(tokens[0], "cancel-preview")))
        return apply_scene_line(path, line_no, tokens, count, world);
    /* L2 群組控制是 session 層指令,不進 .scene 檔格式。 */
    if (count == 1 && strcmp(tokens[0], "history-begin") == 0) {
        if (g_hist_grouping) {
            scene_error(path, line_no, "已有進行中的歷史群組");
            return false;
        }
        g_hist_group_base = *world;
        g_hist_grouping = true;
        g_hist_group_dirty = false;
        return true;
    }
    if (count == 1 && strcmp(tokens[0], "history-end") == 0) {
        if (!g_hist_grouping) {
            scene_error(path, line_no, "沒有進行中的歷史群組");
            return false;
        }
        for (size_t i=0;i<world->timber_count;++i) {
            if (!world->timbers[i].placed) {
                scene_error(path,line_no,"I9: 群組收尾仍有未放置角材（整筆回滾）");
                history_group_rollback(world); return false;
            }
        }
        g_hist_grouping = false;
        /* 整組算一步:把 begin 時的世界推入 undo 疊;沒變更就不記。 */
        if (g_hist_group_dirty) {
            history_record(&g_hist_group_base);
        }
        g_hist_group_dirty = false;
        return true;
    }
    if (count == 1 && strcmp(tokens[0], "history-abort") == 0) {
        /* 冪等:群組可能已因壞行自動回滾,abort 仍回 ok。 */
        if (g_hist_grouping) {
            history_group_rollback(world);
        }
        return true;
    }
    if (count == 1 && strcmp(tokens[0], "undo") == 0) {
        if (g_hist_grouping) {
            scene_error(path, line_no, "歷史群組進行中,不能 undo");
            history_group_rollback(world);
            return false;
        }
        if (history_undo(world)) {
            return true;
        }
        scene_error(path, line_no, "沒有可復原的操作");
        return false;
    }
    if (count == 1 && strcmp(tokens[0], "redo") == 0) {
        if (g_hist_grouping) {
            scene_error(path, line_no, "歷史群組進行中,不能 redo");
            history_group_rollback(world);
            return false;
        }
        if (history_redo(world)) {
            return true;
        }
        scene_error(path, line_no, "沒有可重做的操作");
        return false;
    }
    /* canvas-pos 是展示中繼資料：不記歷史也不清 redo,
     * 否則 renderObjects 的自動排位會把 undo 掉的擺放寫回來。 */
    if (strcmp(tokens[0], "canvas-pos") == 0) {
        bool ok = apply_scene_line(path, line_no, tokens, count, world);
        if (!ok && g_hist_grouping) history_group_rollback(world);
        return ok;
    }

    if (!g_hist_grouping) {
        history_record(world);
    }
    uint32_t preview_before = reference_preview_token();
    if (apply_scene_line(path, line_no, tokens, count, world)) {
        if (g_hist_grouping) g_hist_group_dirty = true;
        return true;
    }
    if (g_hist_grouping) {
        if (!reference_preview_valid() || reference_preview_token() == preview_before) history_group_rollback(world);
        return false;
    }
    /* 失敗也可能已寫入 auto 推導長度；先完整還原，再撤銷歷史。 */
    *world = g_hist_undo[g_hist_undo_n - 1];
    history_unrecord();
    return false;
}

static bool parse_scene_file(const char *path, World *out_world);

/* GEO-163(🔒 2026-09-21 拍板):0 在邊界面的 id 空間是保留值。三個入口共用同一句話,
 * 免得同一條規則在不同指令下講出不一樣的理由。 */
#define RESERVED_BOUNDARY_ID \
    "id 0 是保留值（承載面用它表示「不掛邊界面、自帶矩形」），請改用 1 以上"

/* GEO-164:空間 0 是游離柱樑的標記,宣告與明寫的引用不得占用它。 */
#define RESERVED_SPACE_ID \
    "空間 id 0 是保留值（柱樑用它表示「不屬於空間」），請改用 1 以上；游離柱樑請省略 in"

/*
 * GEO-158：配一個「boundary 與 placement 兩邊都沒被占用、且不是保留值 0」的 id。
 *
 * 原本 canvas_next_id() 與 proj_next_surface_id() 都是裸 max + 1,註解寫「避免碰撞」
 * 但其實不避免,兩個獨立的洞:
 *   1. uint32 上界回繞 → 發出**已經被占用**的 id。投影拆面(apply-proj 的 SPLIT 分支)
 *      在一次交易裡叫兩次,於是追加兩個 id 都是 0 的面;dump 出兩行 `boundary 0`,
 *      再 loadfile 時後者靜默蓋掉前者——**少掉一個面**,而兩次載入都回 ok:true。
 *   2. 0 是 D4 的哨兵值(placement.boundary_id == 0 代表「不掛邊界面、自帶矩形」),
 *      所以 `surface 0` 建不起來、`boundary 0` 永遠掛不上承載面。
 *
 * web_bridge.c 的 newid 已在 GEO-156/157 用同一個判準修好,這裡是核心側的同族缺陷。
 *
 * 終止性:候選 used + 1 個且兩兩相異(used = boundary_count + placement_count,
 * 兩者各有 WORLD_MAX_* 上限),被占用的至多 used 個 → 必定找得到。
 * 回傳 0 = 配號失敗(0 本來就不是合法值,拿它當哨兵不會與正常結果混淆)。
 */
static uint32_t world_next_surface_id(const World *world)
{
    uint32_t id = 0;
    size_t used = world->boundary_count + world->placement_count;

    for (size_t i = 0; i < world->boundary_count; ++i)
        if (world->boundaries[i].id > id) id = world->boundaries[i].id;
    for (size_t i = 0; i < world->placement_count; ++i)
        if (world->placements[i].id > id) id = world->placements[i].id;
    ++id;

    for (size_t attempt = 0; attempt <= used; ++attempt) {
        bool taken = false;

        if (id == 0) id = 1;        /* 任何一輪回繞到保留值都要跳過 */
        for (size_t i = 0; i < world->boundary_count; ++i)
            if (world->boundaries[i].id == id) { taken = true; break; }
        if (!taken) {
            for (size_t i = 0; i < world->placement_count; ++i)
                if (world->placements[i].id == id) { taken = true; break; }
        }
        if (!taken) return id;
        ++id;
    }
    return 0;
}

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
static bool reference_gdi_confirm(HWND window, World *world);
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
    if (!hex || hex[0] != '#' || strlen(hex) != 7) return RGB(0, 0, 0);
    for (int i = 1; i < 7; ++i) {
        char c = hex[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')))
            return RGB(0, 0, 0);
    }
    unsigned v = (unsigned)strtoul(hex + 1, NULL, 16);
    return RGB((v >> 16) & 0xffu, (v >> 8) & 0xffu, v & 0xffu);
}

static POINT gdi_to_pixel(const GdiContext *g, ViewPoint2 p)
{
    POINT out;
    /*
     * GEO-020：正向轉換有同一個缺陷。工單只點名反解，但把已知的同類錯留著沒有道理——
     * 視窗捲動後座標會是負的，往零截斷會讓那一側的線整條偏 1px，且與反解不互為逆運算。
     */
    out.x = (LONG)llround(g->origin_x + (double)(p.x + g->tx) * g->scale);
    out.y = (LONG)llround(g->origin_y + (double)(p.y + g->ty) * g->scale);
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

    /*
     * GEO-030：CreateFontW 會失敗（資源吃緊、字型子系統出問題）。
     * 原本沒判 NULL 就 SelectObject——傳 NULL 進去是錯誤呼叫、回傳 NULL，
     * 接著又拿這個 NULL 去「還原」，等於把 DC 的字型狀態弄壞，之後每一次畫字都受影響。
     * 失敗時就不換字型：用 DC 現有的字型把字畫出來，比弄壞狀態或整段不畫好。
     */
    HGDIOBJ old_font = NULL;

    if (font != NULL) {
        old_font = SelectObject(g->dc, font);
    }

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

    if (old_font != NULL) {
        SelectObject(g->dc, old_font);
    }

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
 * apply_scene_line（含拖曳組出的 move 指令）改它；
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

/* 命中物 → 一行描述；與網頁橋接共用 scene_describe_pick。 */
static void gdi_describe_pick(const GdiApp *app, const ScenePick *p, char *buf, size_t cap)
{
    scene_describe_pick(&app->scene, app->world, p, buf, cap);
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
    } else if (reference_preview_pending() && reference_gdi_confirm(window,app->world)) {
        app_refresh(app,window); gdi_set_status(app,"✓ 已確認套用");
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

        /*
         * GEO-020：用 llround，不要 `(Coord)(x + 0.5)`。
         * 後者對負數是「往零截斷」：-3.4 + 0.5 = -2.9 → -2，應該是 -3。
         * 視圖有 translate，游標落在 tx/ty 左上方時算出來就是負的 mm，
         * 拖曳參考線到那個區域會固定偏 1mm——整份系統是整數 mm 的，1mm 不是誤差是錯值。
         */
        out_mm->x = (Coord)llround(((double)px - ox) / scale - (double)app->layout.tx[v]);
        out_mm->y = (Coord)llround(((double)py - oy) / scale - (double)app->layout.ty[v]);
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

/* Minimized/tiny windows must not send negative control coordinates or dimensions. */
static void gdi_move_control(HWND control, int x, int y, int width, int height, BOOL repaint)
{
    MoveWindow(control, x < 0 ? 0 : x, y < 0 ? 0 : y,
               width < 0 ? 0 : width, height < 0 ? 0 : height, repaint);
}

/* 依目前 client 尺寸重排底部輸入列的控制項。 */
static void gdi_layout_input_bar(HWND window, GdiApp *app)
{
    RECT client;
    GetClientRect(window, &client);

    int w = client.right - client.left;
    int h = client.bottom - client.top;

    /* 頂列左邊是指令回饋（錯誤訊息較長），右邊是 hover 命中物。 */
    gdi_move_control(app->status_label,
               8, h - GDI_INPUT_BAR_H + 4, (w - 16) * 3 / 5, 20, TRUE);
    gdi_move_control(app->hover_label,
               8 + (w - 16) * 3 / 5 + 8, h - GDI_INPUT_BAR_H + 4,
               (w - 16) * 2 / 5 - 8, 20, TRUE);
    gdi_move_control(app->input_edit,
               8, h - 34, w - 176, 26, TRUE);
    gdi_move_control(GetDlgItem(window, IDC_BTN_EXAMPLE),
               w - 162, h - 34, 76, 26, TRUE);
    gdi_move_control(GetDlgItem(window, IDC_BTN_CLEAR),
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

/* 畫布產生新物件用的 id;0 = 配不到(GEO-158)。 */
static uint32_t canvas_next_id(const GdiApp *app)
{
    return world_next_surface_id(app->world);
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
    uint32_t nid = canvas_next_id(app);

    /* GEO-158：配不到就別送。原本回繞時會送出 `surface 0`,解析器拒絕,
     * 使用者只看到一句答非所問的「重宣告後有物件失效」。 */
    if (nid == 0) {
        gdi_set_status(app, "✗ 配不到新的面編號（編號已用盡）");
        return;
    }

    p += snprintf(p, (size_t)(end - p),
                  "surface %u origin %lld %lld %lld u %s v %s outline ",
                  (unsigned)nid,
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

            HWND example_button = CreateWindowW(
                L"BUTTON", L"載入範例",
                WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_BTN_EXAMPLE, cs->hInstance, NULL);

            HWND clear_button = CreateWindowW(
                L"BUTTON", L"清空",
                WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                0, 0, 10, 10,
                window, (HMENU)(INT_PTR)IDC_BTN_CLEAR, cs->hInstance, NULL);

            /*
             * GEO-035：任何一個控制項建不起來就讓 WM_CREATE 失敗。
             * 原本不檢查，於是對 NULL HWND 呼叫 WM_SETFONT 與 SetWindowLongPtrW——
             * 那些呼叫會靜默失敗，接著 gdi_layout_input_bar() 對 NULL 呼叫 MoveWindow，
             * 狀態列也再也更新不了：**視窗看起來開著，其實是壞的**。
             * 回傳 -1 會讓 CreateWindowW 回 NULL，而呼叫端本來就有 `if (window == NULL) return false;`。
             * 帶著半套 UI 繼續跑，比開不起來更難查。
             */
            if (app->status_label == NULL
                || app->hover_label == NULL
                || app->input_edit == NULL
                || example_button == NULL
                || clear_button == NULL) {
                return -1;
            }

            HFONT gui_font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
            SendMessageW(app->status_label, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(app->hover_label, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(app->input_edit, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(example_button, WM_SETFONT, (WPARAM)gui_font, TRUE);
            SendMessageW(clear_button, WM_SETFONT, (WPARAM)gui_font, TRUE);

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
                ofn.lpstrFilter = L"場景檔 (*.scene)\0*.scene\0所有檔案\0*.*\0";
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

                char expr[REF_EXPR_MAX], command[REF_EXPR_MAX+64];
                if (!reference_snap(app->world,gd->placement_id,gd->direction,gd->id,off,80,expr)) {
                    gdi_set_status(app,"R5: 附近沒有合法引用"); return 0;
                }
                snprintf(command,sizeof command,"move %u %s",gd->id,expr);
                interactive_apply_line(app,window,command);

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
    if (iters <= 0) {
        fprintf(stderr, "bench：次數無效。\n");
        return;
    }
    HDC screen = GetDC(NULL);
    if (screen == NULL) {
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
        if (sink_bmp) DeleteObject(sink_bmp);
        if (sink) DeleteDC(sink);
        ReleaseDC(NULL, screen);
        return;
    }

    HGDIOBJ sink_stock = SelectObject(sink, sink_bmp);
    if (!sink_stock || sink_stock == HGDI_ERROR) {
        DeleteObject(sink_bmp); DeleteDC(sink); ReleaseDC(NULL, screen);
        fprintf(stderr, "bench：選取量測位圖失敗。\n");
        return;
    }
    bool completed = false;
    LARGE_INTEGER freq;
    if (!QueryPerformanceFrequency(&freq) || freq.QuadPart <= 0) goto bench_cleanup;

    double cold_setup = 0.0, cold_draw = 0.0, cold_blit = 0.0;
    double warm_setup = 0.0, warm_draw = 0.0, warm_blit = 0.0;

    for (int i = 0; i < iters; ++i) {
        LARGE_INTEGER t0, t1, t2, t3;

        QueryPerformanceCounter(&t0);
        HDC mem = CreateCompatibleDC(screen);
        HBITMAP bmp =
            CreateCompatibleBitmap(screen, client.right, client.bottom);
        if (!mem || !bmp) {
            if (bmp) DeleteObject(bmp);
            if (mem) DeleteDC(mem);
            goto bench_cleanup;
        }
        HGDIOBJ mem_stock = SelectObject(mem, bmp);
        if (!mem_stock || mem_stock == HGDI_ERROR) {
            DeleteObject(bmp); DeleteDC(mem); goto bench_cleanup;
        }
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
    if (!app.mem_dc || !app.mem_bitmap) {
        if (app.mem_bitmap) DeleteObject(app.mem_bitmap);
        if (app.mem_dc) DeleteDC(app.mem_dc);
        app.mem_bitmap = NULL; app.mem_dc = NULL;
        goto bench_cleanup;
    }
    app.mem_w = client.right;
    app.mem_h = client.bottom;
    app.mem_stock = SelectObject(app.mem_dc, app.mem_bitmap);
    if (!app.mem_stock || app.mem_stock == HGDI_ERROR) {
        DeleteObject(app.mem_bitmap); DeleteDC(app.mem_dc);
        app.mem_bitmap = NULL; app.mem_dc = NULL;
        goto bench_cleanup;
    }

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

    completed = true;
bench_cleanup:
    gdi_app_release_objects(&app);
    SelectObject(sink, sink_stock);
    DeleteObject(sink_bmp);
    DeleteDC(sink);
    ReleaseDC(NULL, screen);
    if (!completed) { fprintf(stderr, "bench：配置量測資源失敗，已釋放資源。\n"); return; }

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

static bool g_coord_range_error;
static bool g_parsing_scene_file;
static bool parse_coord(const char *token, Coord *out_value)
{
    Coord value;
    if (!parse_i64(token, &value)) {
        if (errno == ERANGE) g_coord_range_error = true;
        return false;
    }
    if (!coord_in_range(value)) {
        g_coord_range_error = true;
        return false;
    }
    *out_value = value;
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
static char g_revalidate_error[256] = "";

/*
 * snprintf 的截斷以位元組計,可能切在 UTF-8 多位元組字元中間;
 * 這些訊息會進 bridge 的 JSON 與視窗狀態列,尾巴留半個字元就是無效 UTF-8
 * (serve.py 那邊 decode 直接炸)。把結尾不完整的序列整個拿掉:
 * 訊息最多少最後一個字,不會壞掉。中段的壞位元組交給輸出層(js_string)。
 */
static void utf8_trim_tail(char *s)
{
    size_t len = strlen(s);
    size_t i = len;

    while (i > 0 && ((unsigned char)s[i - 1] & 0xC0) == 0x80) {
        --i;                             /* 跳過結尾的續位元組 10xxxxxx */
    }
    if (i == 0) {
        return;                          /* 全是續位元組:不是截斷造成的,留給輸出層 */
    }
    unsigned char lead = (unsigned char)s[i - 1];
    size_t need = lead < 0x80 ? 1
                : (lead & 0xE0) == 0xC0 ? 2
                : (lead & 0xF0) == 0xE0 ? 3
                : (lead & 0xF8) == 0xF0 ? 4 : 1;
    if (len - (i - 1) < need) {
        s[i - 1] = '\0';                 /* 起始位元組後面的續位元組不夠:整個序列拿掉 */
    }
}

/*
 * 從 p 起是不是一個合法的 UTF-8 序列:回長度 1–4,不合法回 0。
 * 不會讀過字串結尾:任一位元組是 NUL 就不是續位元組,提早回 0。
 * 解析層(下面 utf8_is_valid)與 bridge 的 JSON 輸出層(js_string)共用。
 */
static int utf8_seq_len(const unsigned char *p)
{
    unsigned char c = p[0];
    if (c < 0x80) return 1;
    if (c < 0xC2) return 0;                          /* 續位元組打頭,或過長編碼 C0/C1 */
    if (c < 0xE0) return (p[1] & 0xC0) == 0x80 ? 2 : 0;
    if (c < 0xF0) {
        if ((p[1] & 0xC0) != 0x80 || (p[2] & 0xC0) != 0x80) return 0;
        if (c == 0xE0 && p[1] < 0xA0) return 0;      /* 過長編碼 */
        if (c == 0xED && p[1] > 0x9F) return 0;      /* UTF-16 代理對區 */
        return 3;
    }
    if (c < 0xF5) {
        if ((p[1] & 0xC0) != 0x80 || (p[2] & 0xC0) != 0x80 ||
            (p[3] & 0xC0) != 0x80) return 0;
        if (c == 0xF0 && p[1] < 0x90) return 0;      /* 過長編碼 */
        if (c == 0xF4 && p[1] > 0x8F) return 0;      /* 超過 U+10FFFF */
        return 4;
    }
    return 0;
}

/*
 * 場景 DSL 是 UTF-8 文字格式:一行夾了壞位元組就在解析前拒絕,不讓它進世界。
 * 只在輸出層換成 U+FFFD 不夠——畫布看到的名字會跟世界裡的位元組不一樣,
 * 存回去就對不上(R4「重放逐字相同」)。GEO-174,fuzz seed 2 案例 301。
 */
static bool utf8_is_valid(const char *s)
{
    for (const unsigned char *p = (const unsigned char *)s; *p; ) {
        int n = utf8_seq_len(p);
        if (n == 0) return false;
        p += n;
    }
    return true;
}

static void set_revalidate_error(const char *message)
{
    if (message == NULL || message[0] == '\0') {
        snprintf(g_revalidate_error, sizeof g_revalidate_error, "場景重驗失敗");
    } else {
        snprintf(g_revalidate_error, sizeof g_revalidate_error, "%s", message);
        utf8_trim_tail(g_revalidate_error);
    }
}

static void scene_error(const char *path, int line_no, const char *message)
{
    fprintf(stderr, "%s:%d: %s\n", path, line_no, message);
    snprintf(g_scene_last_error, sizeof g_scene_last_error,
             "line %d: %s", line_no, message);
    utf8_trim_tail(g_scene_last_error);
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
/* 公理 I4：Space 建構——零成員 = 空容器直接成立；有成員時各成員邊界面
 * 恰有一個承載面，且槽位一致性全過才成立。非法空間建不出來。 */
/*
 * GEO-041：space_construct 的失敗原因。
 * 原本七種不同的失敗共用一句「這些面組不成一致的空間：…或…或…」，
 * 使用者得自己猜是哪一種、是哪一面出問題。分類不是為了好看——
 * 「面不存在」和「兩片面佔同一方向槽位」的下一步完全不同。
 */
typedef enum {
    SPACE_FAULT_NONE = 0,
    SPACE_FAULT_MEMBER_COUNT,        /* 成員數不在 1..SPACE_MAX_MEMBERS */
    SPACE_FAULT_MISSING_BOUNDARY,    /* 指名的邊界面不存在 */
    SPACE_FAULT_DUPLICATE_BOUNDARY,  /* 同一片邊界面宣告兩次 */
    SPACE_FAULT_NO_CARRIER,          /* 邊界面沒有承載面 → 沒有世界位置（游離面） */
    SPACE_FAULT_AMBIGUOUS_CARRIER,   /* 邊界面被多片承載面引用 → 位置歧義 */
    SPACE_FAULT_SLOT_TAKEN,          /* 兩片面佔同一軸的同一方向槽位 */
    SPACE_FAULT_EXTENT_MISMATCH,     /* 同一軸上的面內區間彼此不一致 */
    SPACE_FAULT_PLANE_MISMATCH,      /* 界面位置與區間端點對不上 */
    SPACE_FAULT_INVERTED             /* 下界 >= 上界（法向朝內會落在這裡） */
} SpaceFault;

typedef struct {
    SpaceFault kind;
    SurfaceId boundary;   /* 相關的邊界面 id；0 = 不適用 */
    int axis;             /* 相關的軸 0/1/2；-1 = 不適用 */
} SpaceFaultInfo;

static bool space_fail(
    SpaceFaultInfo *out,
    SpaceFault kind,
    SurfaceId boundary,
    int axis
)
{
    if (out != NULL) {
        out->kind = kind;
        out->boundary = boundary;
        out->axis = axis;
    }

    return false;
}

/* 把失敗原因寫成一句可以直接給使用者看的話（含出問題的那一面／那一軸）。 */
static void space_fault_describe(
    const SpaceFaultInfo *fault,
    char *buf,
    size_t size
)
{
    const char axis_name = fault->axis == 0 ? 'X'
                         : fault->axis == 1 ? 'Y'
                         : fault->axis == 2 ? 'Z' : '?';

    switch (fault->kind) {
    case SPACE_FAULT_MEMBER_COUNT:
        snprintf(buf, size, "成員數不合法：要 1～%d 片邊界面", SPACE_MAX_MEMBERS);
        break;
    case SPACE_FAULT_MISSING_BOUNDARY:
        snprintf(buf, size, "邊界面 %" PRIu32 " 不存在", fault->boundary);
        break;
    case SPACE_FAULT_DUPLICATE_BOUNDARY:
        snprintf(buf, size, "邊界面 %" PRIu32 " 被宣告兩次", fault->boundary);
        break;
    case SPACE_FAULT_NO_CARRIER:
        snprintf(buf, size,
                 "邊界面 %" PRIu32 " 沒有承載面（游離面沒有世界位置，不能當空間成員）",
                 fault->boundary);
        break;
    case SPACE_FAULT_AMBIGUOUS_CARRIER:
        snprintf(buf, size,
                 "邊界面 %" PRIu32 " 被多片承載面引用，世界位置有歧義",
                 fault->boundary);
        break;
    case SPACE_FAULT_SLOT_TAKEN:
        snprintf(buf, size,
                 "邊界面 %" PRIu32 " 與先前某一片佔住 %c 軸的同一個方向槽位",
                 fault->boundary, axis_name);
        break;
    case SPACE_FAULT_EXTENT_MISMATCH:
        snprintf(buf, size,
                 "邊界面 %" PRIu32 " 在 %c 軸上的面內區間與先前的面不一致",
                 fault->boundary, axis_name);
        break;
    case SPACE_FAULT_PLANE_MISMATCH:
        snprintf(buf, size,
                 "%c 軸的界面位置與面內區間端點對不上", axis_name);
        break;
    case SPACE_FAULT_INVERTED:
        snprintf(buf, size,
                 "%c 軸的下界不小於上界（常見原因：某一片面的法向朝內）", axis_name);
        break;
    default:
        snprintf(buf, size, "未分類的失敗");
        break;
    }
}

static bool space_construct(
    const World *world,
    uint32_t space_id,
    const SurfaceId boundary_ids[],
    size_t count,
    Space *out_space,
    SpaceFaultInfo *out_fault      /* GEO-041：失敗原因；不需要就傳 NULL */
)
{
    typedef struct { Coord v; bool set; } MaybeBound;

    MaybeBound bound[3][2] = { 0 };   /* [軸][0=下界, 1=上界]，由法向面釘住 */
    MaybeBound ext_lo[3] = { 0 };     /* 面內區間在各軸上的下/上界 */
    MaybeBound ext_hi[3] = { 0 };
    bool slot_taken[3][2] = { 0 };    /* [軸][0=負法向, 1=正法向] */

    if (count < 1 || count > SPACE_MAX_MEMBERS || out_space == NULL) {
        return space_fail(out_fault, SPACE_FAULT_MEMBER_COUNT, 0, -1);
    }

    for (size_t i = 0; i < count; ++i) {
        const SpaceBoundarySurface *bd =
            world_find_boundary(world, boundary_ids[i]);

        if (bd == NULL) {
            return space_fail(out_fault, SPACE_FAULT_MISSING_BOUNDARY,
                              boundary_ids[i], -1);
        }

        for (size_t j = 0; j < i; ++j) {
            if (boundary_ids[j] == boundary_ids[i]) {
                return space_fail(out_fault, SPACE_FAULT_DUPLICATE_BOUNDARY,
                                  boundary_ids[i], -1);
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
            return space_fail(
                out_fault,
                carriers == 0 ? SPACE_FAULT_NO_CARRIER
                              : SPACE_FAULT_AMBIGUOUS_CARRIER,
                bd->id, -1);
        }

        int a = axis_index(face->frame.normal);
        Coord n = a == 0 ? face->frame.normal.x
                : a == 1 ? face->frame.normal.y
                         : face->frame.normal.z;
        int slot = n > 0 ? 1 : 0;
        Coord plane = point3_component(face->frame.origin, a);

        if (slot_taken[a][slot]) {
            return space_fail(out_fault, SPACE_FAULT_SLOT_TAKEN, bd->id, a);
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
                return space_fail(out_fault, SPACE_FAULT_EXTENT_MISMATCH,
                                  bd->id, j);
            }

            ext_lo[j].v = lo;  ext_lo[j].set = true;
            ext_hi[j].v = hi;  ext_hi[j].set = true;
        }
    }

    /* 界值與區間端點要吻合；下界必須小於上界（法向朝內在這裡被擋）。 */
    for (int j = 0; j < 3; ++j) {
        if (bound[j][0].set && ext_lo[j].set && bound[j][0].v != ext_lo[j].v) {
            return space_fail(out_fault, SPACE_FAULT_PLANE_MISMATCH, 0, j);
        }
        if (bound[j][1].set && ext_hi[j].set && bound[j][1].v != ext_hi[j].v) {
            return space_fail(out_fault, SPACE_FAULT_PLANE_MISMATCH, 0, j);
        }
        if (bound[j][0].set && bound[j][1].set &&
            bound[j][0].v >= bound[j][1].v) {
            return space_fail(out_fault, SPACE_FAULT_INVERTED, 0, j);
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

/* 已放角材的 A0 footprint（錨點為引用重算後的快取）。 */
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
/* 公理 I11：同面任兩支已放角材的 footprint 正面積不得相交
 *（端點/邊相接 = 零面積 = 合法接觸）。 */
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
 * D18 擋面參照：DSL 指名一個 D11 擋面的寫法。
 *   kind 0 = 邊（hole < 0 是外輪廓 e<i>，否則孔 h<i>e<j>）
 *   kind 1 = 已放角材的側面 t<id>（垂直於本支長度軸的那兩個面，二選一由 R21(d) 決定）
 * 參照只是「指名」，不改變擋面的任何性質，也不新增擋面來源。
 */
typedef struct {
    int kind;
    int hole;
    int edge;
    TimberId timber;
} StopFaceRef;

static bool stop_face_matches_ref(const StopFace *f, const StopFaceRef *r)
{
    if (f == NULL || r == NULL) {
        return false;
    }

    if (r->kind == 1) {
        return f->kind == STOP_TIMBER_SIDE && f->timber_id == r->timber;
    }

    if (r->hole < 0) {
        return f->kind == STOP_OUTLINE_EDGE && f->edge_index == r->edge;
    }

    return f->kind == STOP_HOLE_EDGE &&
           f->hole_index == r->hole && f->edge_index == r->edge;
}

/*
 * R21(a)：被指名的擋面仍須「涵蓋端面全寬」且「非 FREE 邊」——
 * 明寫只買走 R6(d) 的「恰好一個」，不買走物理條件。
 * 過不了的候選在這裡被濾掉，並回報是哪一種不合格。
 */
static size_t stop_ref_candidates(
    const StopFace faces[],
    size_t face_count,
    const StopFaceRef *r,
    Coord cross_lo,
    Coord cross_hi,
    const StopFace *out[],
    size_t out_cap,
    bool *saw_free,
    bool *saw_narrow
)
{
    size_t n = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const StopFace *f = &faces[i];

        if (!stop_face_matches_ref(f, r)) {
            continue;
        }

        if (f->lo > cross_lo || f->hi < cross_hi) {
            *saw_narrow = true;
            continue;
        }

        if (f->fixity == EDGE_FREE) {
            *saw_free = true;
            continue;
        }

        if (n < out_cap) {
            out[n++] = f;
        }
    }

    return n;
}

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
    SpaceBoundarySurface effective;
    boundary=placement_effective_boundary(placement,boundary,&effective);

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

    /* D11 order follows placement, independent of timber declaration order. */
    for (size_t i=1;i<count;++i) {
        if (out[i].kind!=STOP_TIMBER_SIDE) continue;
        uint64_t order=UINT64_MAX;
        for (size_t t=0;t<world->timber_count;++t) if (world->timbers[t].id==out[i].timber_id) order=world->anchors[t].order;
        size_t j=i; StopFace value=out[i];
        while (j && out[j-1].kind==STOP_TIMBER_SIDE) {
            uint64_t previous=UINT64_MAX;
            for (size_t t=0;t<world->timber_count;++t) if (world->timbers[t].id==out[j-1].timber_id) previous=world->anchors[t].order;
            if (previous<=order) break;
            out[j]=out[j-1]; --j;
        }
        out[j]=value;
    }
    for (size_t i=0;i<count;) {
        bool duplicate=false;
        if (out[i].kind==STOP_TIMBER_SIDE) {
            uint64_t order=UINT64_MAX;
            for (size_t t=0;t<world->timber_count;++t) if (world->timbers[t].id==out[i].timber_id) order=world->anchors[t].order;
            for (size_t j=0;j<count && !duplicate;++j) {
                if (i==j || out[i].fixed!=out[j].fixed || out[i].lo>=out[j].hi || out[j].lo>=out[i].hi) continue;
                bool earlier=out[j].kind!=STOP_TIMBER_SIDE;
                if (!earlier) for (size_t t=0;t<world->timber_count;++t)
                    if (world->timbers[t].id==out[j].timber_id && world->anchors[t].order<order) earlier=true;
                if (earlier && out[j].lo<=out[i].lo && out[j].hi>=out[i].hi) duplicate=true;
            }
        }
        if (duplicate) { memmove(out+i,out+i+1,(count-i-1)*sizeof *out); --count; }
        else ++i;
    }
    return count;
}

/*
 * 在座標 at 找「恰好一個涵蓋 [lo,hi] 全寬」的擋面。
 *   回傳命中數；0 = 無擋面（懸空），>1 = 歧義。
 *   命中時 *out_face 指向唯一那面（FREE 邊也算命中，
 *   交由呼叫端拒絕——先找到才能說「頂到自由邊」）。
 */
/* A partial overlap keeps the exposed extension, but the occupied overlap
 * is the earlier edge, not a second support (D11). */
static bool stop_face_shadowed(const StopFace faces[],size_t i,Coord lo,Coord hi)
{
    if (faces[i].kind!=STOP_TIMBER_SIDE) return false;
    for (size_t j=0;j<i;++j)
        if (faces[j].fixed==faces[i].fixed && faces[j].lo<=lo && faces[j].hi>=hi) return true;
    return false;
}

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

        if (f->fixed != at || f->lo > lo || f->hi < hi || stop_face_shadowed(faces,i,lo,hi)) {
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
            f->fixity != EDGE_FREE && !stop_face_shadowed(faces,i,lo,hi)) {
            ++hits;
        }
    }

    return hits;
}

/*
 * R18 角色衍生屬性（純幾何，不看宣告與錨法）：
 *   onBoundary   footprint 某一側面與外輪廓某邊共線且重疊長度 > 0
 *   coversEdge   onBoundary 且長度軸區間 ⊇ 該邊區間
 *   boundaryEdge 該邊索引，無則 -1
 * 只看外輪廓、不看孔邊；不讀 anchor_kind，所以 through / at-guides 貼齊邊
 * 一樣算 onBoundary，at-face 放卻被裁短一樣 coversEdge=false。
 *
 * 多條候選邊時的選法（公理層未指定，此處取確定性規則）：
 * 優先取 coversEdge 成立者，其次取重疊最長者，同長取索引最小者。
 *
 * span_* / cross_* 由呼叫端傳入（與 timber_end_face_check 同一種形式）：
 * 放置當下角材尚未標記 placed，不能靠 timber_a0_footprint_uv 自行推。
 * span_* = 長度軸區間，cross_* = 兩個側面所在的橫向座標。
 *
 * 回傳 false = 推導不出；此時三個輸出為預設值。
 */
static bool timber_role_props(
    const SpaceBoundarySurface *boundary,
    bool along_v,
    Coord span_lo,
    Coord span_hi,
    Coord cross_lo,
    Coord cross_hi,
    bool *out_on_boundary,
    bool *out_covers_edge,
    int *out_boundary_edge
)
{
    int best = -1;
    bool best_covers = false;
    Coord best_overlap = 0;
    size_t i;

    *out_on_boundary = false;
    *out_covers_edge = false;
    *out_boundary_edge = -1;

    if (boundary == NULL) {
        return false;
    }

    for (i = 0; i < boundary->outline.count; ++i) {
        SurfaceSegment2 seg;
        bool edge_along_v, covers;
        Coord edge_fixed, edge_lo, edge_hi, ov;

        if (!loop_get_edge_segment(&boundary->outline, i, &seg)) {
            continue;
        }

        /* 側面沿長度軸走 → 只有與長度軸平行的邊才可能共線。 */
        edge_along_v = seg.start.u == seg.end.u;
        if (edge_along_v != along_v) {
            continue;
        }

        edge_fixed = edge_along_v ? seg.start.u : seg.start.v;
        if (edge_fixed != cross_lo && edge_fixed != cross_hi) {
            continue;
        }

        edge_lo = edge_along_v ? coord_min(seg.start.v, seg.end.v)
                               : coord_min(seg.start.u, seg.end.u);
        edge_hi = edge_along_v ? coord_max(seg.start.v, seg.end.v)
                               : coord_max(seg.start.u, seg.end.u);

        ov = coord_min(span_hi, edge_hi) - coord_max(span_lo, edge_lo);
        if (ov <= 0) {
            continue;   /* 共線但不重疊（或只點接觸）→ 不算 onBoundary */
        }

        covers = span_lo <= edge_lo && span_hi >= edge_hi;
        if (best < 0 || (covers && !best_covers) ||
            (covers == best_covers && ov > best_overlap)) {
            best = (int)i;
            best_covers = covers;
            best_overlap = ov;
        }
    }

    if (best >= 0) {
        *out_on_boundary = true;
        *out_covers_edge = best_covers;
        *out_boundary_edge = best;
    }
    return true;
}

/*
 * 定位邊在角材長度軸上的區間（D16 的固定段/延伸段切分要用它）。
 *
 * D16 寫的是「與它所覆蓋的那條外輪廓 FIXED 邊（boundaryEdge）在長度軸上
 * 重疊的部分」，而 R18 明寫 boundaryEdge 是**純幾何、不看宣告與錨法**，
 * 還特別點名「用 through 放的料貼齊邊一樣 onBoundary」。
 * 所以這裡只能問幾何，不能問 anchor_kind：同一支料用 at-face 放、
 * 或用 at／through 放在同一個位置，footprint 完全相同，固定段就必須相同。
 *
 * dump 往返保存引用與放置順序（R4），角色属性仍由幾何推導、
 * 丟掉放法記錄，但幾何沒變，推導結果因此不變。
 *
 * 只看外輪廓、不看孔邊——孔邊是柱擋面，沒有延伸段語意（I20、I21 同一分界）。
 */
static bool boundary_edge_interval(
    const SpaceBoundarySurface *boundary,
    bool along_v,
    Coord span_lo,
    Coord span_hi,
    Coord cross_lo,
    Coord cross_hi,
    Coord *out_lo,
    Coord *out_hi
)
{
    bool on_boundary = false;
    bool covers_edge = false;
    int edge = -1;
    SurfaceSegment2 seg;

    /*
     * D16 的固定段/延伸段切分預設這支料放得上去(I5)。連 footprint 都不在
     * 有效範圍內的東西,問它的定位邊沒有意義——那種場景該由 I5 用
     * 「放不上去」擋下,不該讓 I22 先攔截並給出誤導的理由
     * (`_mut_notch_straddle.scene`:橫跨凹口的料恰好與凹口底邊共線)。
     */
    if (boundary == NULL ||
        !boundary_contains_rect(
            boundary,
            along_v ? cross_lo : span_lo,
            along_v ? span_lo : cross_lo,
            along_v ? cross_hi : span_hi,
            along_v ? span_hi : cross_hi)) {
        return false;
    }

    if (!timber_role_props(boundary, along_v, span_lo, span_hi,
                           cross_lo, cross_hi,
                           &on_boundary, &covers_edge, &edge) ||
        !on_boundary || edge < 0 ||
        !loop_get_edge_segment(&boundary->outline, (size_t)edge, &seg)) {
        return false;
    }

    *out_lo = along_v
        ? coord_min(seg.start.v, seg.end.v)
        : coord_min(seg.start.u, seg.end.u);
    *out_hi = along_v
        ? coord_max(seg.start.v, seg.end.v)
        : coord_max(seg.start.u, seg.end.u);
    return true;
}

/*
 * I20 邊界材整條覆蓋：`boundary` 的固定段在長度軸上必須 ⊇ 它所覆蓋那條邊的
 * 整個區間，且該邊是外輪廓的 FIXED 邊、與主支軸垂直（D17）。
 *
 * 「與主支軸垂直」由 I21 保證（boundary 的長度軸必 ⊥ 主支軸，而此處的邊與
 * 該長度軸平行），故本函式不重複檢查，只驗覆蓋與 FIXED。
 * 孔邊不算——R18 本就只掃外輪廓。
 *
 * 固定段 = footprint ∩ 邊區間（D16）；固定段 ⊇ 邊區間 等價於
 * footprint 的長度軸區間 ⊇ 邊區間，即 R18 的 coversEdge。
 */
static bool timber_boundary_role_check(
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    const Timber *timber,
    bool along_v,
    Coord span_lo,
    Coord span_hi,
    Coord cross_lo,
    Coord cross_hi,
    char *err,
    size_t err_cap
)
{
    SpaceBoundarySurface effective;
    boundary=placement_effective_boundary(placement,boundary,&effective);

    bool on_boundary = false, covers_edge = false;
    int edge_index = -1;
    SurfaceSegment2 seg;
    Coord edge_lo, edge_hi, cover;

    if (timber == NULL || timber->role != TIMBER_ROLE_BOUNDARY) {
        return true;
    }

    /*
     * footprint 已經跨出有效範圍時讓位給 I5——公理層 I22 明訂
     * 「凸角處延伸即出界，不需另立規則」，該情形的裁決者是 I5 而非本條。
     */
    if (!surface_contains_rect(
            placement, boundary,
            along_v ? cross_lo : span_lo,
            along_v ? span_lo : cross_lo,
            along_v ? cross_hi : span_hi,
            along_v ? span_hi : cross_hi)) {
        return true;
    }
    if (!timber_role_props(boundary, along_v, span_lo, span_hi,
                           cross_lo, cross_hi,
                           &on_boundary, &covers_edge, &edge_index)) {
        return true;
    }

    if (!on_boundary) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 宣告 boundary，"
                     "但沒有任何側面貼在外輪廓邊上",
                     (unsigned)timber->id);
        }
        return false;
    }

    if (!loop_get_edge_segment(&boundary->outline,
                               (size_t)edge_index, &seg)) {
        return true;
    }

    if (boundary->outline.fixity[edge_index] != EDGE_FIXED) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 貼的外輪廓邊 e%d 是自由邊，"
                     "boundary 必須貼 FIXED 邊",
                     (unsigned)timber->id, edge_index);
        }
        return false;
    }

    if (!covers_edge) {
        edge_lo = along_v ? coord_min(seg.start.v, seg.end.v)
                          : coord_min(seg.start.u, seg.end.u);
        edge_hi = along_v ? coord_max(seg.start.v, seg.end.v)
                          : coord_max(seg.start.u, seg.end.u);
        cover = coord_min(span_hi, edge_hi) - coord_max(span_lo, edge_lo);
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 宣告 boundary，"
                     "但只覆蓋外輪廓邊 e%d 的 %lld / %lld mm——"
                     "固定段必須涵蓋整條邊",
                     (unsigned)timber->id, edge_index,
                     (long long)cover, (long long)(edge_hi - edge_lo));
        }
        return false;
    }

    return true;
}

/*
 * 擋面接觸範圍 [lo,hi]（擋面擁有者長度軸上的座標）是否落在
 * owner 的延伸段上——I22：延伸段的側面作擋面時以優先級 2 計。
 * 只有「at-face 外輪廓邊錨的 boundary」才有固定段/延伸段之分;
 * 其餘 owner 一律回傳 false（擋面優先級 = owner.cut_priority）。
 */
static bool stop_in_owner_extension(
    const World *world,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    const Timber *owner,
    Coord lo,
    Coord hi
)
{
    if (owner->role != TIMBER_ROLE_BOUNDARY) {
        return false;
    }

    for (size_t i = 0; i < world->timber_count; ++i) {
        const TimberAnchor *a;
        SurfaceRegion2 f;
        bool owner_along_v;
        Coord edge_lo, edge_hi, fix_lo, fix_hi;
        Coord span_lo, span_hi;

        if (&world->timbers[i] != owner) {
            continue;
        }

        a = &world->anchors[i];
        owner_along_v =
            a->length_direction == SURFACE_DIRECTION_POS_V ||
            a->length_direction == SURFACE_DIRECTION_NEG_V;

        if (!timber_a0_footprint_uv(placement, owner, a, &f)) {
            return false;
        }

        span_lo = owner_along_v ? f.min_v : f.min_u;
        span_hi = owner_along_v ? f.max_v : f.max_u;

        if (!boundary_edge_interval(
                boundary, owner_along_v, span_lo, span_hi,
                owner_along_v ? f.min_u : f.min_v,
                owner_along_v ? f.max_u : f.max_v,
                &edge_lo, &edge_hi)) {
            return false;
        }
        fix_lo = coord_max(span_lo, edge_lo);
        fix_hi = coord_min(span_hi, edge_hi);

        return !(lo >= fix_lo && hi <= fix_hi);
    }

    return false;
}

/*
 * I19/I22 端面檢查：角材兩端面所頂擋面的裁切優先序。
 *
 *   外輪廓邊（RC 牆）：只有 boundary 可頂——端面不提供固定，守的是
 *     「那條邊還沒鋪邊界材」（I19/I20）；其他角色端面頂到 → V_CUT_PRIORITY。
 *   孔邊/柱面：優先級 0,各角色可頂。
 *   角材側面：擋面擁有者優先級須 < 自己；兩支 boundary 可在
 *     轉角互頂（例外一）；擋面落在 owner 延伸段上 → 以 2 計。
 *   自己是 boundary 且該端屬延伸段 → 豁免 I19（可頂任何優先級）。
 *   自己非 boundary 且 at-face 外輪廓錨：跨度不得超出定位邊
 *     （V_EXTENSION）；boundary 超出部分即延伸段。
 *
 * R6 放置與重驗：呼叫端已保證端面有擋面。
 * err 可為 NULL（重驗只取 true/false）。
 */
static bool timber_end_face_check(
    const World *world,
    const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,
    const Timber *self,
    bool along_v,
    Coord span_lo,
    Coord span_hi,
    Coord cross_lo,
    Coord cross_hi,
    char *err,
    size_t err_cap
)
{
    SpaceBoundarySurface effective;
    boundary=placement_effective_boundary(placement,boundary,&effective);

    Coord edge_lo = 0, edge_hi = 0;
    bool has_edge = boundary_edge_interval(
        boundary, along_v, span_lo, span_hi, cross_lo, cross_hi,
        &edge_lo, &edge_hi);
    bool ext_end[2];

    /* I22：非 boundary 的 footprint 不得超出定位邊。 */
    if (has_edge && self->role != TIMBER_ROLE_BOUNDARY &&
        (span_lo < edge_lo || span_hi > edge_hi)) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_EXTENSION：非 boundary 角材（%u）的 "
                     "footprint 超出定位邊範圍", (unsigned)self->id);
        }
        return false;
    }

    ext_end[0] = has_edge && self->role == TIMBER_ROLE_BOUNDARY &&
                 span_lo < edge_lo;
    ext_end[1] = has_edge && self->role == TIMBER_ROLE_BOUNDARY &&
                 span_hi > edge_hi;

    StopFace faces[STOP_FACE_MAX];
    size_t face_count = collect_stop_faces(
        world, placement, boundary, along_v, self,
        faces, STOP_FACE_MAX);

    for (int e = 0; e < 2; ++e) {
        Coord at = e == 0 ? span_lo : span_hi;

        for (size_t i = 0; i < face_count; ++i) {
            const StopFace *f = &faces[i];

            if (f->fixed != at || f->lo > cross_lo || f->hi < cross_hi ||
                f->fixity == EDGE_FREE || ext_end[e] || stop_face_shadowed(faces,i,cross_lo,cross_hi)) {
                continue;
            }

            if (f->kind == STOP_OUTLINE_EDGE) {
                /* I19 的外輪廓邊那一款：端面不提供固定，擋的不是「碰到牆」，
                 * 是「那條邊還沒鋪邊界材」——板靠牆的邊要有骨可釘（I20）。
                 * 孔邊與柱面不在此限（貼邊料角色由宣告決定，I21），
                 * 所以這裡只攔 STOP_OUTLINE_EDGE（見 _test_hole_auto）。 */
                if (self->role != TIMBER_ROLE_BOUNDARY) {
                    if (err != NULL) {
                        snprintf(err, err_cap,
                                 "V_CUT_PRIORITY：角材 %u 端面頂到"
                                 "外輪廓邊（RC）——那條邊還沒鋪邊界材；"
                                 "只有 boundary 可頂 RC",
                                 (unsigned)self->id);
                    }
                    return false;
                }
                continue;
            }

            if (f->kind == STOP_TIMBER_SIDE) {
                const Timber *owner = NULL;
                Coord owner_prio;

                for (size_t k = 0; k < world->timber_count; ++k) {
                    if (world->timbers[k].id == f->timber_id &&
                        world->timbers[k].placed) {
                        owner = &world->timbers[k];
                        break;
                    }
                }
                if (owner == NULL || owner == self) {
                    continue;
                }

                /* 例外一：兩支 boundary 可在轉角互頂。 */
                if (self->role == TIMBER_ROLE_BOUNDARY &&
                    owner->role == TIMBER_ROLE_BOUNDARY) {
                    continue;
                }

                owner_prio = owner->cut_priority;
                if (stop_in_owner_extension(
                        world, placement, boundary,
                        owner, cross_lo, cross_hi)) {
                    /*
                     * I22：延伸段側面作擋面時以優先級 2 計。
                     *
                     * 誰頂得到延伸段的側面(由公理層推導)：
                     *   延伸段沿其所屬 boundary 的長度軸(D16、見
                     *   stop_in_owner_extension)，而 D17 要求 boundary ⊥ 主支軸，
                     *   故延伸段 ⊥ 主支軸。端面頂側面需兩者垂直，
                     *   所以頂得到的料必須「平行於主支軸」。
                     *   - secondary：D17 要求 ⊥ 主支軸 → 與延伸段平行 → 頂不到。
                     *   - primary  ：平行主支軸、頂得到，但 cut_priority 同為 2，
                     *                2 >= 2 落進下面的 V_CUT_PRIORITY(I19)。
                     *   - custom   ：D17 未約束其長度軸、I21 的拒絕條件也只列
                     *                boundary/secondary(D15：custom 不取得任何
                     *                角色專屬的義務或權利)，故可平行主支軸；
                     *                明寫 priority >= 3 時 2 < 3 → 接受。
                     * 即接受路徑存在且唯一：custom priority >= 3。
                     * 正向覆蓋見 _role_priority_ext_custom.scene。
                     *
                     * 公理層 I22 括號原本寫「主支端面不得頂它；副支可以」，
                     * 那句由 D16+D17 推不出來(副支必與延伸段平行、頂不到)。
                     * 2026-09-16 已改成上面推導出的接受路徑：平行主支軸且
                     * 優先級大於 2 的 custom 料。條文與這段註解現在一致。
                     */
                    owner_prio = 2;
                }

                if (owner_prio >= self->cut_priority) {
                    if (err != NULL) {
                        snprintf(err, err_cap,
                                 "V_CUT_PRIORITY：角材 %u（優先級 %d）"
                                 "端面頂到角材 %u（優先級 %d）側面——"
                                 "擋面擁有者優先級必須嚴格小於自己",
                                 (unsigned)self->id, (int)self->cut_priority,
                                 (unsigned)owner->id, (int)owner_prio);
                    }
                    return false;
                }
            }
            /* STOP_HOLE_EDGE：優先級 0,各角色可頂。 */
        }
    }

    return true;
}

/* ============================================================
 * auto 跨距解析：固定中線上，footprint 不穿過任何實體的
 * 連續合法區間全程。
 * ============================================================ */

typedef enum {
    SPAN_OK,
    SPAN_NO_INTERVAL,        /* 中線上沒有任何合法區間 */
    SPAN_AMBIGUOUS,          /* 多個合法區間，沒有選擇器 */
    SPAN_OUTSIDE_CONTACT,    /* 有區間但都不接觸 at-face 引用的邊 */
    SPAN_THROUGH_OUTSIDE,    /* through 座標不在任何合法區間內 */
    SPAN_START_UNSUPPORTED,  /* 起點沒有唯一合法擋面 */
    SPAN_END_UNSUPPORTED,    /* 終點沒有唯一合法擋面 */
    SPAN_START_AMBIGUOUS,    /* 起點擋面歧義 */
    SPAN_END_AMBIGUOUS,      /* 終點擋面歧義 */
    SPAN_FREE_EDGE_END,      /* 擋面是自由邊 */
    SPAN_BETWEEN_BLOCKED,    /* between 指名的兩端之間沒有合法跨距 */
    SPAN_BETWEEN_AMBIGUOUS   /* between 的角材側面有多組合法配對 */
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
 *   has_contact        at-face：候選區間必須與引用邊的範圍重疊
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
    const StopFaceRef *between,
    const SurfaceRegion2 *scope,
    Coord *out_start,
    Coord *out_end,
    char *err,
    size_t err_cap
)
{
    Coord cuts[SPAN_CUT_MAX];
    size_t cut_count = 0;
    Coord scope_lo=scope?(along_v?scope->min_v:scope->min_u):0;
    Coord scope_hi=scope?(along_v?scope->max_v:scope->max_u):0;
    if (scope && (cross_lo<(along_v?scope->min_u:scope->min_v) || cross_hi>(along_v?scope->max_u:scope->max_v))) {
        snprintf(err,err_cap,"I13：角材的完整寬度超出子格範圍");
        return SPAN_NO_INTERVAL;
    }

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

    /* --- at-face 接觸範圍過濾：區間必須與引用邊的範圍重疊 --- */
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

    /* R6/D19: scope selects complete intervals; it never supplies stops. */
    if (scope && !between) {
        size_t kept=0;
        for (size_t i=0;i<interval_count;++i)
            if (intervals[i].start>=scope_lo && intervals[i].end<=scope_hi) intervals[kept++]=intervals[i];
        interval_count=kept;
        if (!kept) {
            snprintf(err,err_cap,"I13/R6：子格 [%lld,%lld] 內沒有兩端獲得支撐的完整跨距",(long long)scope_lo,(long long)scope_hi);
            return SPAN_NO_INTERVAL;
        }
    }

    /*
     * --- R21：between 明寫兩端 ---
     * 它是消解歧義的選擇器，不是放寬條件：兩個被指名的擋面各自仍須
     * 通過 R6(d) 的物理條件，跨距也仍須整段落在某個合法區間內（R6(b)）。
     */
    if (between != NULL) {
        StopFace bfaces[STOP_FACE_MAX];
        size_t bface_count = collect_stop_faces(
            world, placement, boundary, along_v, NULL,
            bfaces, STOP_FACE_MAX);

        const StopFace *ca[WORLD_MAX_TIMBERS * 2];
        const StopFace *cb[WORLD_MAX_TIMBERS * 2];
        bool free_a = false;
        bool free_b = false;
        bool narrow_a = false;
        bool narrow_b = false;
        size_t na = stop_ref_candidates(bfaces, bface_count, &between[0],
                                        cross_lo, cross_hi,
                                        ca, WORLD_MAX_TIMBERS * 2,
                                        &free_a, &narrow_a);
        size_t nb = stop_ref_candidates(bfaces, bface_count, &between[1],
                                        cross_lo, cross_hi,
                                        cb, WORLD_MAX_TIMBERS * 2,
                                        &free_b, &narrow_b);

        if (na == 0 || nb == 0) {
            const bool is_free = (na == 0 && free_a) || (nb == 0 && free_b);
            const bool is_narrow =
                (na == 0 && narrow_a) || (nb == 0 && narrow_b);

            if (is_free) {
                snprintf(err, err_cap,
                         "between 指名的擋面是自由邊（頂到空氣）");
                return SPAN_FREE_EDGE_END;
            }

            snprintf(err, err_cap,
                     is_narrow
                         ? "between 指名的擋面沒有涵蓋角材端面的全寬"
                         : "between 指名的擋面不存在，"
                           "或它不垂直於角材長度軸");
            return SPAN_BETWEEN_BLOCKED;
        }

        SpanInterval hit[WORLD_MAX_TIMBERS * 4];
        size_t hit_count = 0;

        for (size_t x = 0; x < na; ++x) {
            for (size_t y = 0; y < nb; ++y) {
                Coord s = ca[x]->fixed;
                Coord e = cb[y]->fixed;

                if (s == e) {
                    continue;   /* R21(c)：區間必須非空 */
                }

                if (s > e) {
                    const Coord swap = s;

                    s = e;
                    e = swap;
                }

                bool inside = false;

                for (size_t k = 0; k < interval_count; ++k) {
                    if (intervals[k].start <= s && e <= intervals[k].end) {
                        inside = true;
                        break;
                    }
                }

                if (!inside || (scope && (s<scope_lo || e>scope_hi))) {
                    continue;   /* R6: between pairs must be fully inside the child scope. */
                }

                if (hit_count < WORLD_MAX_TIMBERS * 4) {
                    hit[hit_count].start = s;
                    hit[hit_count].end = e;
                    ++hit_count;
                }
            }
        }

        if (hit_count == 0) {
            snprintf(err, err_cap,
                     "between 指名的兩端之間沒有合法跨距"
                     "（被實體擋住，或兩端座標相同）");
            return SPAN_BETWEEN_BLOCKED;
        }

        if (hit_count > 1) {
            size_t n = (size_t)snprintf(err, err_cap,
                                        "between 有多組合法配對：");

            for (size_t k = 0; k < hit_count && n < err_cap; ++k) {
                n += (size_t)snprintf(err + n, err_cap - n, " [%lld,%lld]",
                                      (long long)hit[k].start,
                                      (long long)hit[k].end);
            }

            return SPAN_BETWEEN_AMBIGUOUS;
        }

        *out_start = hit[0].start;
        *out_end = hit[0].end;
        return SPAN_OK;
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

/*
 * D17/I21 主支軸一致:推導承載面的主支軸,驗證角色-方向關係。
 *
 *   primary 全同軸 → 該軸即主支軸;
 *   無 primary 有 boundary → 主支軸 = boundary 長度軸的垂直向;
 *   兩者皆無 → 未定義(第一支 primary/boundary 落地即定義,
 *   此支不做方向檢查);未定義時不得有 secondary(副支必須
 *   在主支之後)。
 *
 * boundary/secondary 的長度軸必須垂直於主支軸(面內只有
 * u/v 兩軸,平行 = 同軸 → 拒絕)。custom 不參與本檢查——
 * 它的 priority 只用於 I19 的數值比較,沒有方向義務。
 *
 * extra/extra_along_v:place 路徑在落料前先驗,那支料尚未進
 * world->anchors,由參數補上;world_revalidate 傳 NULL。
 */
static bool surface_primary_axis_check(
    const World *world,
    SurfaceId placement_id,
    const Timber *extra,
    bool extra_along_v,
    char *err,
    size_t err_size
)
{
    bool has_primary = false, has_boundary = false;
    int primary_axis = -1, boundary_axis = -1;   /* 0 = 沿 u,1 = 沿 v */
    TimberId primary_id = 0;

    /* 第一遍:定軸。primary 優先推導,其次 boundary 的垂直向。 */
    for (size_t i = 0; i <= world->timber_count; ++i) {
        const Timber *t;
        int axis;

        if (i < world->timber_count) {
            const TimberAnchor *a;

            t = &world->timbers[i];
            if (!t->placed) continue;
            a = &world->anchors[i];
            if (a->placement_id != placement_id) continue;
            axis =
                a->length_direction == SURFACE_DIRECTION_POS_V ||
                a->length_direction == SURFACE_DIRECTION_NEG_V ? 1 : 0;
        } else {
            if (extra == NULL) break;
            t = extra;
            axis = extra_along_v ? 1 : 0;
        }

        if (t->role == TIMBER_ROLE_PRIMARY) {
            if (!has_primary) {
                has_primary = true;
                primary_axis = axis;
                primary_id = t->id;
            } else if (axis != primary_axis) {
                if (err != NULL) {
                    snprintf(err, err_size,
                        "V_PRIMARY_AXIS:同面 primary 長度軸不唯一"
                        "（角材 %u 沿 %c,角材 %u 沿 %c）",
                        primary_id, primary_axis ? 'v' : 'u',
                        t->id, axis ? 'v' : 'u');
                }
                return false;
            }
        } else if (t->role == TIMBER_ROLE_BOUNDARY && !has_boundary) {
            has_boundary = true;
            boundary_axis = axis;
        }
    }

    int axis = has_primary ? primary_axis
             : has_boundary ? 1 - boundary_axis
             : -1;

    /* 第二遍:boundary/secondary 不得與主支軸平行;
       主支軸未定義時不得有 secondary。 */
    for (size_t i = 0; i <= world->timber_count; ++i) {
        const Timber *t;
        int t_axis;

        if (i < world->timber_count) {
            const TimberAnchor *a;

            t = &world->timbers[i];
            if (!t->placed) continue;
            a = &world->anchors[i];
            if (a->placement_id != placement_id) continue;
            t_axis =
                a->length_direction == SURFACE_DIRECTION_POS_V ||
                a->length_direction == SURFACE_DIRECTION_NEG_V ? 1 : 0;
        } else {
            if (extra == NULL) break;
            t = extra;
            t_axis = extra_along_v ? 1 : 0;
        }

        if (t->role != TIMBER_ROLE_BOUNDARY &&
            t->role != TIMBER_ROLE_SECONDARY) {
            continue;
        }

        if (axis == -1) {
            if (t->role == TIMBER_ROLE_SECONDARY) {
                if (err != NULL) {
                    snprintf(err, err_size,
                        "V_PRIMARY_AXIS:主支軸未定義,"
                        "secondary（角材 %u）必須在主支之後", t->id);
                }
                return false;
            }
            continue;   /* boundary 落地即定義主支軸 */
        }

        if (t_axis == axis) {
            if (err != NULL) {
                snprintf(err, err_size,
                    "V_PRIMARY_AXIS:角材 %u（%s）長度軸沿 %c,"
                    "與主支軸平行——boundary/secondary 必須垂直於主支軸",
                    t->id, timber_role_name(t->role),
                    axis ? 'v' : 'u');
            }
            return false;
        }
    }

    return true;
}

static bool world_revalidate(World *world);
static const ReferenceGrid *world_find_grid(const World *world, uint32_t id);

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
 * 這一層只讀；呼叫前由 world_revalidate 重建候選世界的衍生資料。
 */
/* 公理 R20：重宣告/刪除連坐——刪除或移動任一角材後，對同面全部角材
 * 重驗 I19–I22 與 R18；任一不過 → 整筆拒絕回滾（I8 同軌）。 */
static bool grid_rules_valid(const GridSystem *,char *,size_t);
static bool grid_rules_world_valid(const World *,char *,size_t);
static bool grid_rule_line(const World *,const GridRuleLineRef *,SurfaceId,Coord *,SurfaceRegion2 *,char *,size_t);
static bool grid_rule_ref_text(const char *,GridRuleLineRef *);
static bool grid_subdivision_used(const World *);
#include "geometry-core/subgrid_world.inc"

static bool world_validate_derived(const World *world)
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

        if (p == NULL || !coord_in_range(g->offset) ||
            (g->direction != GUIDE_ALONG_U && g->direction != GUIDE_ALONG_V)) {
            return false;
        }
    }

    for (size_t i = 0; i < world->grid_count; ++i) {
        const ReferenceGrid *g = &world->grids[i];
        const PlacementSurface *p =
            world_find_placement(world, g->placement_id);

        if (p == NULL ||
            !grid_is_valid_in(world->grids, world->grid_count, g, p, world_placement_boundary(world, p), NULL, 0)) {
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

        /* I23(b)：被 at-line grid 錨定的索引必須仍推導得出——
         * 承載面縮小會讓尾端的線不再產生，那時整筆回滾（I8 同軌）。 */
        if (a->anchor_kind == ANCHOR_AT_GRID) {
            const ReferenceGrid *ag = world_find_grid(world, a->ref_grid);
            const PlacementSurface *ap =
                ag != NULL ? world_find_placement(world, ag->placement_id)
                           : NULL;
            char anchor_error[256] = "";

            if (ag == NULL || ap == NULL ||
                !grid_anchor_line_coord(world->grids, world->grid_count, ag, ap,
                                 world_placement_boundary(world, ap),
                                 a->ref_grid_axis,
                                 a->ref_grid_index,
                                 a->ref_grid_has_band,
                                 a->ref_grid_band,
                                 NULL, anchor_error, sizeof anchor_error)) {
                set_revalidate_error(anchor_error[0] ? anchor_error : "被網格錨定的格線已不存在");
                return false;
            }
        }

        if (a->anchor_kind==ANCHOR_AT_RULE) {
            SurfaceRegion2 cell,f; char error[256]="";
            if(!grid_rule_line(world,&a->ref_rule,p->id,NULL,&cell,error,sizeof error) ||
                !timber_a0_footprint_uv(p,t,a,&f) || f.min_u<cell.min_u || f.max_u>cell.max_u ||
                f.min_v<cell.min_v || f.max_v>cell.max_v) {
                set_revalidate_error(error[0]?error:"I13: rule anchor footprint exceeds parent cell");return false;
            }
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

        {
            SurfaceRegion2 f;
            const SpaceBoundarySurface *b =
                world_placement_boundary(world, p);
            bool along_v =
                a->length_direction == SURFACE_DIRECTION_POS_V ||
                a->length_direction == SURFACE_DIRECTION_NEG_V;

            if (!timber_a0_footprint_uv(p, t, a, &f)) {
                return false;
            }

            /* I13/D19: final-world containment is independent of rebuild order. */
            if (a->anchor_kind==ANCHOR_AT_GRID) {
                const ReferenceGrid *g=world_find_grid(world,a->ref_grid);
                SurfaceRegion2 cell;
                if (g && g->is_subgrid &&
                    (!grid_cell_bounds(world->grids,world->grid_count,g,p,b,&cell,NULL,0) ||
                    f.min_u<cell.min_u || f.max_u>cell.max_u || f.min_v<cell.min_v || f.max_v>cell.max_v)) {
                    set_revalidate_error("I13：角材的完整足跡超出子格範圍"); return false;
                }
                if (g && g->from_binding && a->ref_grid_has_band && g->axis[a->ref_grid_axis].stagger_set) {
                    int axis=a->ref_grid_axis, other=1-axis; int64_t next; Coord lo,hi;
                    Coord flo=axis==0?f.min_v:f.min_u, fhi=axis==0?f.max_v:f.max_u;
                    if (!grid_i64_add(a->ref_grid_band,1,&next) ||
                        !grid_lattice_coord(g,other,a->ref_grid_band,&lo) ||
                        !grid_lattice_coord(g,other,next,&hi) || flo<lo || fhi>hi) {
                        set_revalidate_error("I24：角材沿線範圍超出該格子"); return false;
                    }
                }
            }

            /* R6(d)/R21: the full world must still have unique support,
             * unless between explicitly selects valid stop faces. */
            {
                StopFace faces[STOP_FACE_MAX];
                size_t nf=collect_stop_faces(world,p,b,along_v,t,faces,STOP_FACE_MAX);
                Coord ends[2]={along_v?f.min_v:f.min_u,along_v?f.max_v:f.max_u};
                Coord lo=along_v?f.min_u:f.min_v,hi=along_v?f.max_u:f.max_v;
                for (int k=0;k<2;++k) {
                    size_t hits=count_legal_stops(faces,nf,ends[k],lo,hi);
                    if (hits==0 || (!a->has_between && hits!=1)) {
                        set_revalidate_error("R6(d): 端面需要恰好一個涵蓋全寬的合法擋面"); return false;
                    }
                }
            }

            /* I19/I22：每支料的端面裁切優先序與延伸段規則。 */
            {
                char end_err[256] = "";

                if (!timber_end_face_check(
                        world, p, b, t, along_v,
                        along_v ? f.min_v : f.min_u,
                        along_v ? f.max_v : f.max_u,
                        along_v ? f.min_u : f.min_v,
                        along_v ? f.max_u : f.max_v,
                        end_err, sizeof end_err)) {
                    set_revalidate_error(
                        end_err[0] != '\0' ? end_err : "端面裁切優先序不成立");
                    return false;
                }

                /* I20：邊界材固定段須整條覆蓋所貼的外輪廓邊。 */
                if (!timber_boundary_role_check(
                        p, b, t, along_v,
                        along_v ? f.min_v : f.min_u,
                        along_v ? f.max_v : f.max_u,
                        along_v ? f.min_u : f.min_v,
                        along_v ? f.max_u : f.max_v,
                        end_err, sizeof end_err)) {
                    set_revalidate_error(
                        end_err[0] != '\0' ? end_err : "邊界材固定段未覆蓋定位邊");
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

    /* D17/I21：每片承載面推導主支軸,驗證角色-方向一致。 */
    for (size_t i = 0; i < world->placement_count; ++i) {
        if (!surface_primary_axis_check(
                world, world->placements[i].id, NULL, false,
                NULL, 0)) {
            return false;
        }
    }

    for (size_t i = 0; i < world->space_count; ++i) {
        const Space *s = &world->spaces[i];
        Space probe;

        if (s->boundary_count == 0) {
            continue;   /* 空容器：零成員的部分空間，恆合法 */
        }

        if (!space_construct(
                world, s->id, s->boundaries, s->boundary_count, &probe, NULL)) {
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

/* D2/D7/D9：承載面 frame 改變後，角材的世界姿態與 Space 範圍必須
 * 從定義重建。只在候選世界上操作，全量驗證通過才一起提交；
 * 失敗不會留下部分更新。位置與長度重算，引用與格線索引保持原意。 */
static bool world_revalidate_candidate(World *world,World *candidate)
{
    g_revalidate_error[0] = '\0';
    char grid_error[256]="";
    if (!boundary_keys_reconcile(candidate,g_subgrid_before,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!parameters_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!engineering_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!assembly_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!sp_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!grid_systems_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!grid_bindings_rebuild(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    if (!assembly_generation_prepare(candidate)) {
        set_revalidate_error(g_engineering_error); return false;
    }
    if (!grid_rules_world_valid(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error); reference_capture_trial(candidate); return false;
    }
    reference_capture_trial(candidate);
    if (!subgrid_world_valid(candidate,grid_error,sizeof grid_error)) {
        set_revalidate_error(grid_error[0]?grid_error:"I25: grid dependency invalid");
        return false;
    }

    bool rebuilt=reference_rebuild(candidate);
    char rebuild_error[256]; snprintf(rebuild_error,sizeof rebuild_error,"%s",g_revalidate_error);
    bool all_checks=reference_check_all(candidate);
    if (!rebuilt || !all_checks) {
        if (!rebuilt && rebuild_error[0]) set_revalidate_error(rebuild_error);
        return false;
    }

    for (size_t i = 0; i < candidate->space_count; ++i) {
        const Space *s = &world->spaces[i];
        if (s->boundary_count == 0) {
            candidate->spaces[i] = (Space){0};
            candidate->spaces[i].id = s->id;
        } else if (!space_construct(candidate, s->id, s->boundaries,
                                    s->boundary_count, &candidate->spaces[i],
                                    NULL)) {
            return false;
        }
    }

    if (!world_validate_derived(candidate)) {
        if (g_revalidate_error[0] == '\0') {
            set_revalidate_error("場景重驗失敗");
        }
        return false;
    }
    if (!assembly_generation_check(candidate)) { set_revalidate_error(g_engineering_error); return false; }
    *world = *candidate;
    return true;
}

static bool world_revalidate(World *world)
{
    World *candidate=malloc(sizeof *candidate);
    if(!candidate){set_revalidate_error("I32: candidate World allocation failed");return false;}
    *candidate=*world;
    bool ok=world_revalidate_candidate(world,candidate);
    free(candidate);return ok;
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
    return parse_coord(buf, &out->u) && parse_coord(comma + 1, &out->v);
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
    /* D4:承載面用 boundary_id == 0 表示「不掛邊界面、自帶矩形」,
     * 所以 0 在邊界面的 id 空間是保留值。原本 boundary 0 建得起來,
     * 卻永遠掛不上承載面——一個回 ok:true 的死物件(GEO-163)。 */
    if (id == 0) {
        scene_error(path, line_no, "boundary 的 " RESERVED_BOUNDARY_ID);
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
                char detail[512];
                snprintf(detail,sizeof detail,"重宣告後有物件失效（承載面/參考線/角材/空間沒全過）: boundary %u: %s",
                    id,g_revalidate_error[0]?g_revalidate_error:"I8: dependent objects invalid");
                scene_error(path, line_no, detail);
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
            /* 明明寫了 on boundary 0,卻會被當成「沒寫 on」的預設值(GEO-163)。
             * 原本的訊息是「不掛邊界面的承載面需要 rect」,答非所問。 */
            if (candidate->boundary_id == 0) {
                scene_error(path, line_no,
                    "on boundary 0 不合法:" RESERVED_BOUNDARY_ID
                    "；要自帶矩形請改用 rect");
                return false;
            }
            ++i;
        } else if (strcmp(tokens[i], "origin") == 0) {
            ++i;

            if (i + 2 >= count ||
                !parse_coord(tokens[i], &candidate->frame.origin.x) ||
                !parse_coord(tokens[i + 1], &candidate->frame.origin.y) ||
                !parse_coord(tokens[i + 2], &candidate->frame.origin.z)) {
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
                if (!parse_coord(tokens[i + k], &r[k])) {
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

    World backup = *world;
    world->placements[world->placement_count++] = candidate;
    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no, "新增承載面後有物件失效（已回滾）");
        return false;
    }
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

    /* 合體行會宣告 boundary <id>,所以 0 在這裡是保留值(GEO-163)。
     * 沒有 outline 的 `surface 0` 只宣告承載面,0 對它是合法的——不擋。
     * 原本這裡的失敗訊息是「重宣告後有物件失效」,而它其實是首次宣告。 */
    if (has_outline && id == 0) {
        scene_error(path, line_no, "surface 的 " RESERVED_BOUNDARY_ID);
        return false;
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

        World backup = *world;
        world->placements[world->placement_count++] = candidate;
        if (!world_revalidate(world)) {
            *world = backup;
            scene_error(path, line_no, "新增承載面後有物件失效（已回滾）");
            return false;
        }
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
static bool apply_guide_line(const char *p, int n, char **t, int c, World *w)
{ return apply_reference_guide(p, n, t, c, w); }

/* D7/D15: timber id A B role ...；長度永遠由引用與跨距推導。 */
static bool apply_timber_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    if (world->timber_count == WORLD_MAX_TIMBERS &&
        (count < 2 || !world_find_timber(world, (uint32_t)strtoul(tokens[1], NULL, 10)))) {
        scene_error(path, line_no, "角材的數量超過上限");
        return false;
    }

    /* D7: only A/B dimensions; old explicit lengths are rejected. */
    bool auto_length;
    int role_idx;

    if (count >= 5 && strcmp(tokens[4], "role") == 0) {
        auto_length = true;
        role_idx = 4;
    } else {
        scene_error(path, line_no,
            "D7/I18: timber id A尺寸 B尺寸 role 必填；明寫長度已廢除 "
            "role boundary|primary|secondary|custom [priority N]");
        return false;
    }

    if (count < role_idx + 2) {
        scene_error(path, line_no, "role 後面要接角色名");
        return false;
    }

    TimberRole role;
    Coord custom_priority = 0;
    int tail;

    if (strcmp(tokens[role_idx + 1], "boundary") == 0) {
        role = TIMBER_ROLE_BOUNDARY;
    } else if (strcmp(tokens[role_idx + 1], "primary") == 0) {
        role = TIMBER_ROLE_PRIMARY;
    } else if (strcmp(tokens[role_idx + 1], "secondary") == 0) {
        role = TIMBER_ROLE_SECONDARY;
    } else if (strcmp(tokens[role_idx + 1], "custom") == 0) {
        role = TIMBER_ROLE_CUSTOM;
    } else {
        scene_error(path, line_no,
            "role 只能是 boundary、primary、secondary 或 custom");
        return false;
    }

    if (role == TIMBER_ROLE_CUSTOM) {
        if (count < role_idx + 4 ||
            strcmp(tokens[role_idx + 2], "priority") != 0 ||
            !parse_i64(tokens[role_idx + 3], &custom_priority) ||
            custom_priority < 1) {
            scene_error(path, line_no,
                "custom 角色需要 priority N（N 是 ≥1 的整數）");
            return false;
        }
        tail = role_idx + 4;
    } else {
        if (count > role_idx + 2 &&
            strcmp(tokens[role_idx + 2], "priority") == 0) {
            scene_error(path, line_no, "priority 只能配 custom 角色");
            return false;
        }
        tail = role_idx + 2;
    }

    if (count != tail) {
        scene_error(path, line_no, "timber 行有多餘欄位");
        return false;
    }

    uint32_t id;
    Coord length = 0, size_a, size_b;

    if (auto_length) {
        if (!parse_u32(tokens[1], &id) ||
            !parse_coord(tokens[2], &size_a) ||
            !parse_coord(tokens[3], &size_b)) {
            scene_error(path, line_no,
                "timber auto 需要：id A尺寸 B尺寸（都是整數）");
            return false;
        }
    } else {
        if (!parse_u32(tokens[1], &id) ||
            !parse_coord(tokens[2], &length) ||
            !parse_coord(tokens[3], &size_a) ||
            !parse_coord(tokens[4], &size_b)) {
            scene_error(path, line_no,
                "timber 需要：id 長度 A尺寸 B尺寸（都是整數）");
            return false;
        }
    }

    if (assembly_owned(world,id)) { scene_error(path,line_no,"I42: edit the owning assembly instance"); return false; }
    for (size_t i = 0; i < world->timber_count; ++i) {
        if (world->timbers[i].id == id) {
            Timber updated;
            if (!timber_construct(id, 0, size_a, size_b, true, role, custom_priority, &updated)) return false;
            updated.placed = world->timbers[i].placed;
            return world_replace_object(world, &world->timbers[i], &updated, sizeof updated);
        }
    }

    if (!timber_construct(id, length, size_a, size_b, auto_length,
            role, custom_priority,
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

static ReferenceGrid *world_find_grid_mut(World *world, uint32_t id)
{
    for (size_t i = 0; i < world->grid_count; ++i) {
        if (world->grids[i].id == id) {
            return &world->grids[i];
        }
    }

    return NULL;
}

/*
 * at-face 的邊參照：e3 = 外輪廓邊 index 3；h1e2 = 孔 1 的邊 index 2。
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
 * grid <id> on <承載面id> [main-along u|v|none] u c1 [c2 ...] [v c1 [c2 ...]]
 *
 * 一座網格 = u 座標集合 + v 座標集合（公理 G1–G4）。
 * 同一 id 可寫兩行分別補 u / v 集合（同座標軸只能宣告一次）；
 * 每片承載面最多一座主網格，子網格另走 D19 的完整宣告。
 */
#include "geometry-core/grid_systems.inc"

static bool apply_grid_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    if (count>4 && !strcmp(tokens[4],"from-binding"))
        return apply_grid_binding_application(path,line_no,tokens,count,world);
    if (count>4 && !strcmp(tokens[4],"from-system"))
        return apply_grid_system_application(path,line_no,tokens,count,world);
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
    ReferenceGrid *existing = world_find_grid_mut(world, grid_id);

    if (existing != NULL && (existing->from_system || existing->from_binding)) {
        scene_error(path,line_no,"D29: edit the grid-system source or its application origin; direct axis edits are not allowed");
        return false;
    }
    if (existing != NULL && existing->is_subgrid) {
        scene_error(path,line_no,"D19：不能將既有子網格改成主網格");
        return false;
    }
    if (existing != NULL && existing->placement_id != placement_id) {
        scene_error(path, line_no, "這個 grid id 已經用在別的承載面");
        return false;
    }

    if (existing == NULL) {
        /* 一面一格：不同 id 落在同一承載面 → 拒絕。 */
        for (size_t i = 0; i < world->grid_count; ++i) {
            if (!world->grids[i].is_subgrid && world->grids[i].placement_id == placement_id) {
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

    /* 既有網格可單獨更新主支方向；省略時保留原值。 */
    int i = 4;
    bool has_main_along = false;
    if (i < count && strcmp(tokens[i], "main-along") == 0) {
        if (i + 1 >= count) {
            scene_error(path, line_no, "grid main-along 需要 u、v 或 none");
            return false;
        }
        if (strcmp(tokens[i + 1], "u") == 0) candidate.main_along = 1;
        else if (strcmp(tokens[i + 1], "v") == 0) candidate.main_along = 2;
        else if (strcmp(tokens[i + 1], "none") == 0) candidate.main_along = 0;
        else {
            scene_error(path, line_no, "grid main-along 只接受 u、v 或 none");
            return false;
        }
        has_main_along = true;
        i += 2;
    }
    /* 逐段解析：u|v 開頭，後面跟一串座標直到下一個 u/v 或行尾。 */
    size_t filled = 0;
    bool declared_here[2] = { false, false };

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

        /* 同一行內同軸寫兩次 = 筆誤，擋掉；跨行重宣告既有的軸放行（I10），
         * 由下面的 I23(a) 引用鎖把關「會不會移動已錨定的線」。 */
        if (declared_here[axis]) {
            scene_error(path, line_no,
                axis == 0 ? "grid 的 u 座標集合在同一行只能宣告一次"
                          : "grid 的 v 座標集合在同一行只能宣告一次");
            return false;
        }

        declared_here[axis] = true;

        {
            const GridAxisDef blank = { 0 };

            grid->axis[axis] = blank;   /* 重宣告 = 整軸換掉，不是疊加 */
        }

        /* D10a 面材來源：`u panel <面材寬> gap <縫寬> [from <起算點>]`。 */
        if (strcmp(tokens[i], "panel") == 0) {
            if (i + 3 >= count || strcmp(tokens[i + 2], "gap") != 0) {
                scene_error(path, line_no,
                    "grid panel 需要：panel 面材寬 gap 縫寬 [from 起算點]");
                return false;
            }

            Coord p_panel;
            Coord p_gap;

            if (!parse_coord(tokens[i + 1], &p_panel) ||
                !parse_coord(tokens[i + 3], &p_gap)) {
                scene_error(path, line_no,
                    "grid panel 的面材寬與縫寬都必須是整數");
                return false;
            }

            if (p_panel <= 0) {
                scene_error(path, line_no, "grid panel 的面材寬必須大於 0");
                return false;
            }

            if (p_gap < 0) {
                scene_error(path, line_no, "grid panel 的縫寬不能是負數");
                return false;
            }

            /* D1 全整數、R3 不猜：縫寬為奇數時中心線不是整數 → 拒絕。 */


            int pnext = i + 4;
            bool has_from = false;
            Coord p_from = 0;

            if (pnext < count && strcmp(tokens[pnext], "from") == 0) {
                if (pnext + 1 >= count ||
                    !parse_coord(tokens[pnext + 1], &p_from)) {
                    scene_error(path, line_no,
                        "grid panel 的 from 後面要接一個整數起算點");
                    return false;
                }

                has_from = true;
                pnext += 2;
            }

            /*
             * D10a：起算點在宣告當下具體化並寫進定義。未明寫就取當下的
             * 軸向下界；之後承載面改變不重算 a，因此已存在的索引永不被
             * 重新編號，能變的只有尾端條數。
             */
            if (!has_from) {
                SurfaceRegion2 pbounds;

                if (!placement_local_bounds(
                        placement,
                        world_find_boundary(world, placement->boundary_id),
                        &pbounds)) {
                    scene_error(path, line_no,
                        "grid panel 推不出承載面的外接範圍");
                    return false;
                }

                p_from = axis == 0 ? pbounds.min_u : pbounds.min_v;
            }

            GridAxisDef *pdef = &grid->axis[axis];

            pdef->source = GRID_SRC_PANEL;
            pdef->panel = p_panel;
            pdef->gap = p_gap;
            pdef->anchor = p_from;
            pdef->anchor_explicit = has_from;

            i = pnext;
            ++filled;
            continue;
        }

        /* D10 等差來源：`u series <起點> <間距> <條數>`。
         * 座標一定過 parse_i64、`series` 一定過不了，所以這個分派無歧義。 */
        if (strcmp(tokens[i], "series") == 0) {
            if (i + 3 >= count) {
                scene_error(path, line_no,
                    "grid series 需要：series 起點 間距 條數");
                return false;
            }

            Coord s_start;
            Coord s_step;
            Coord s_count;

            if (!parse_coord(tokens[i + 1], &s_start) ||
                !parse_coord(tokens[i + 2], &s_step) ||
                !parse_i64(tokens[i + 3], &s_count)) {
                scene_error(path, line_no,
                    "grid series 的起點、間距、條數都必須是整數");
                return false;
            }

            if (s_step <= 0) {
                scene_error(path, line_no, "grid series 的間距必須大於 0");
                return false;
            }

            if (s_count <= 0) {
                scene_error(path, line_no, "grid series 的條數必須至少 1");
                return false;
            }

            if (s_count > GRID_MAX_LINES) {
                scene_error(path, line_no,
                    axis == 0 ? "grid u 座標超過上限"
                              : "grid v 座標超過上限");
                return false;
            }

            GridAxisDef *sdef = &grid->axis[axis];

            sdef->source = GRID_SRC_SERIES;
            sdef->start = s_start;
            sdef->step = s_step;
            sdef->series_count = (size_t)s_count;

            i += 4;
            ++filled;
            continue;
        }

        while (i < count &&
               strcmp(tokens[i], "u") != 0 &&
               strcmp(tokens[i], "v") != 0) {
            Coord c;

            if (!parse_coord(tokens[i], &c)) {
                scene_error(path, line_no, "grid 的座標不是有效的整數");
                return false;
            }

            GridAxisDef *def = &grid->axis[axis];

            if (def->count == GRID_MAX_LINES) {
                scene_error(path, line_no,
                    axis == 0 ? "grid u 座標超過上限"
                              : "grid v 座標超過上限");
                return false;
            }

            def->source = GRID_SRC_EXPLICIT;
            def->coords[def->count++] = c;

            ++i;
            ++filled;
        }
    }

    if (filled == 0 && !(existing != NULL && has_main_along)) {
        scene_error(path, line_no, "新網格至少要一個格線來源");
        return false;
    }
    if ((candidate.main_along == 1 && candidate.axis[1].source == GRID_SRC_NONE) ||
        (candidate.main_along == 2 && candidate.axis[0].source == GRID_SRC_NONE)) {
        scene_error(path, line_no, "grid 主支方向沒有對應的格線來源");
        return false;
    }

    /* I8a: preserve the parsed candidate even when parent count locking rejects it. */
    {
        World trial=*world;
        if (existing) trial.grids[existing-world->grids]=candidate;
        else if (trial.grid_count<WORLD_MAX_GRIDS) trial.grids[trial.grid_count++]=candidate;
        reference_capture_trial(&trial);
    }

    {
        const SpaceBoundarySurface *vb =
            world_find_boundary(world, placement->boundary_id);
        Coord probe[GRID_MAX_LINES];
        size_t probe_n;

        for (int a = 0; a < 2; ++a) {
            char gerr[200] = "";

            if (grid->axis[a].source == GRID_SRC_NONE) {
                continue;
            }

            if (!grid_axis_lines(grid, placement, vb, a,
                                 probe, &probe_n, gerr, sizeof gerr)) {
                char msg[320];

                snprintf(msg, sizeof msg,
                    "grid 座標不合法（%c 軸）：%s",
                    a == 0 ? 'u' : 'v',
                    gerr[0] != '\0'
                        ? gerr
                        : "要嚴格遞增、且落在承載面外接範圍內");
                scene_error(path, line_no, msg);
                return false;
            }
        }
    }

    /* I23: also validate read-only grid-preview calls that bypass transactions. */
    for (size_t child=0;child<world->grid_count;++child) {
        if (world->grids[child].is_subgrid && world->grids[child].parent_id==candidate.id) {
            char err[256]="";
            if (!subgrid_parent_count_valid(world,&candidate,placement,world_placement_boundary(world,placement),err,sizeof err)) {
                scene_error(path,line_no,err); return false;
            }
            break;
        }
    }

    /*
     * 回寫走 I8 交易：全量重驗，失敗整筆回滾、World 留在舊狀態。
     * 既有槽位交給 world_replace_object；新增沒有槽位可換，就地做同一套。
     */
    if (existing != NULL) {
        if (!world_replace_object(world, existing, &candidate,
                                  sizeof candidate)) {
            scene_error(path, line_no, g_revalidate_error[0]?g_revalidate_error:"重宣告後有物件失效（已回滾）");
            return false;
        }
    } else {
        World backup = *world;

        world->grids[world->grid_count++] = candidate;

        if (!world_revalidate(world)) {
            *world = backup;
            scene_error(path, line_no, "新增網格後有物件失效（已回滾）");
            return false;
        }
    }

    return true;
}

#include "geometry-core/subgrid_commands.inc"

/* I12/I13/R6: at-line guide/grid 或 at-face e/he/t，保存引用並重算。
 * through 與 between 選擇可證明的合法跨距；既有物件變更走 I8a。 */
static bool apply_place_line(const char *p, int n, char **t, int c, World *w)
{ return apply_reference_place(p, n, t, c, w); }

/* 舊保存標記明確拒絕，避免誤讀成新引用定義。 */
static bool apply_span_auto_line(const char *p, int n, char **t, int c, World *w)
{ (void)t; (void)c; (void)w; scene_error(p,n,"R4: span-auto 已廢除；請使用引用錨法"); return false; }


static bool apply_move_line(const char *p, int n, char **t, int c, World *w)
{ return apply_reference_move(p, n, t, c, w); }

#include "geometry-core/parameters.inc"
#include "geometry-core/references.inc"
#include "geometry-core/engineering.inc"
#include "geometry-core/boundary_vertex_keys.inc"
#include "geometry-core/grid_bindings.inc"
#include "geometry-core/grid_subdivision.inc"
#include "geometry-core/grid_subdivision_query.inc"
#include "geometry-core/engineering_commands.inc"
#include "geometry-core/assembly.inc"
#include "geometry-core/assembly_generation.inc"
#include "geometry-core/section_profiles.inc"


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
/*
 * GEO-043：兩個座標的中點，奇數時取下界（偏低座標側）。
 * 與 D10a 對奇數 gap 的處理同一條紀律——C 的 `/` 對負數是往零截斷，
 * 直接用會讓房間在負座標區的質心偏一格，那不是誤差是錯值。
 */
static Coord coord_midpoint_floor(Coord a, Coord b)
{
    Coord sum = a + b;

    if (sum >= 0) {
        return sum / 2;
    }

    return -(((-sum) + 1) / 2);
}

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
        if (space_id == 0) {
            scene_error(path, line_no, RESERVED_SPACE_ID);
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
    if (!parse_coord(tokens[i + 1], &x) || !parse_coord(tokens[i + 2], &y) ||
        !parse_coord(tokens[i + 4], &w) || !parse_coord(tokens[i + 5], &d)) {
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
        if (!parse_coord(tokens[i + 1], &z0) || !parse_coord(tokens[i + 2], &z1)) {
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
        if (space_id == 0) {
            scene_error(path, line_no, RESERVED_SPACE_ID);
            return false;
        }
        i += 2;
    }
    /* along x|y from a to b at c width w depth d [top z] */
    if (i + 12 > count || strcmp(tokens[i], "along") != 0 ||
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
    if (!parse_coord(tokens[i + 3], &a) || !parse_coord(tokens[i + 5], &b) ||
        !parse_coord(tokens[i + 7], &c) || !parse_coord(tokens[i + 9], &w) ||
        !parse_coord(tokens[i + 11], &d)) {
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
        if (!parse_coord(tokens[i + 1], &top)) {
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
    OBSTACLE_TOP_DROP,
    OBSTACLE_DEGENERATE
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

/* R7: exact orthogonal intersection, not a corner/offset-point proxy.
 * The obstacle contract carries one rectangle. A disconnected/nonrectangular
 * intersection (or zero-area tangency) is reported explicitly, never replaced
 * by a bounding rectangle or silently treated as a missing obstacle. */
#define RECT_CONTACT_ERROR "R7: 投影接觸非單一矩形或僅相切（退化，不猜）"

static void proj_sort_coords(Coord *values, size_t n)
{
    for (size_t i = 1; i < n; ++i) {
        Coord value = values[i];
        size_t j = i;
        while (j > 0 && values[j - 1] > value) {
            values[j] = values[j - 1];
            --j;
        }
        values[j] = value;
    }
}

/* Closed contact suffices for R14 ownership of an R12 uncut strip. It need
 * not be representable as a single cutting rectangle. */
static bool proj_rect_outline_touches(const PolygonLoop2 *loop,
    Coord u0, Coord v0, Coord u1, Coord v1)
{
    if (poly_contains_point(loop, (SurfacePoint2){u0,v0})) return true;
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i], b = loop->v[(i+1)%loop->count];
        if (coord_max(coord_min(a.u,b.u),u0) <= coord_min(coord_max(a.u,b.u),u1) &&
            coord_max(coord_min(a.v,b.v),v0) <= coord_min(coord_max(a.v,b.v),v1))
            return true;
    }
    return false;
}

/* 0 = disjoint; 1 = exact single rectangular contact; -1 = R7 degeneration.
 * Every polygon vertex splits the v-axis into topology-constant open slabs.
 * Pairing sorted vertical-edge crossings gives the entire interior in a slab;
 * clipping those intervals is exact, including half-mm midlines. We accept a
 * rectangle only if every nonempty slab has the same single u interval and the
 * v intervals are consecutive. No area multiplication or geometric sampling. */
static int classify_rect_outline(
    const PolygonLoop2 *loop,
    Coord in_u0, Coord in_v0, Coord in_u1, Coord in_v1,
    ObstacleClass *cls,
    Coord *out_u0, Coord *out_v0, Coord *out_u1, Coord *out_v1
)
{
    if (loop == NULL || loop->count < 4 || loop->count > POLY_MAX_VERTICES ||
            in_u0 >= in_u1 || in_v0 >= in_v1) return 0;
    Coord cuts[POLY_MAX_VERTICES + 2] = { in_v0, in_v1 };
    size_t nc = 2;
    for (size_t i = 0; i < loop->count; ++i)
        if (loop->v[i].v > in_v0 && loop->v[i].v < in_v1)
            cuts[nc++] = loop->v[i].v;
    proj_sort_coords(cuts, nc);

    bool found = false;
    Coord u0 = 0, v0 = 0, u1 = 0, v1 = 0;
    for (size_t slab = 1; slab < nc; ++slab) {
        Coord lo = cuts[slab - 1], hi = cuts[slab];
        if (lo == hi) continue;
        Coord mid2 = lo + hi;
        Coord crossings[POLY_MAX_VERTICES];
        size_t count = 0;
        for (size_t i = 0; i < loop->count; ++i) {
            SurfacePoint2 a = loop->v[i], b = loop->v[(i + 1) % loop->count];
            if (a.u == b.u && mid2 > 2 * coord_min(a.v,b.v) &&
                    mid2 < 2 * coord_max(a.v,b.v)) crossings[count++] = a.u;
        }
        if (count % 2) return -1; /* Valid simple orthogonal loops have paired crossings. */
        proj_sort_coords(crossings, count);
        int intervals = 0;
        Coord left = 0, right = 0;
        for (size_t i = 0; i < count; i += 2) {
            Coord l = coord_max(in_u0, crossings[i]);
            Coord r = coord_min(in_u1, crossings[i + 1]);
            if (l >= r) continue;
            if (++intervals > 1) return -1;
            left = l; right = r;
        }
        if (intervals == 0) continue;
        if (found && (left != u0 || right != u1 || lo != v1)) return -1;
        if (!found) { u0 = left; u1 = right; v0 = lo; found = true; }
        v1 = hi;
    }
    if (!found) {
        /* Distinguish closed boundary tangency from a genuinely absent item. */
        for (size_t i = 0; i < loop->count; ++i) {
            SurfacePoint2 a = loop->v[i], b = loop->v[(i+1)%loop->count];
            if (coord_max(coord_min(a.u,b.u),in_u0) <= coord_min(coord_max(a.u,b.u),in_u1) &&
                coord_max(coord_min(a.v,b.v),in_v0) <= coord_min(coord_max(a.v,b.v),in_v1))
                return -1;
        }
        return 0;
    }

    /* Open slabs omit zero-area components. Every closed edge contact with
     * the original footprint must also lie in the positive-area rectangle. */
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i], b = loop->v[(i+1)%loop->count];
        Coord l = coord_max(coord_min(a.u,b.u),in_u0);
        Coord r = coord_min(coord_max(a.u,b.u),in_u1);
        Coord bottom = coord_max(coord_min(a.v,b.v),in_v0);
        Coord top = coord_min(coord_max(a.v,b.v),in_v1);
        if (l <= r && bottom <= top &&
                (l < u0 || r > u1 || bottom < v0 || top > v1)) return -1;
    }

    int flush = 0;
    bool f[4];
    for (int side = 0; side < 4; ++side) {
        f[side] = side_flush_outline(loop, side, u0, v0, u1, v1);
        if (f[side]) ++flush;
    }
    /* A point-only corner contact is not a hole (R7); do not guess a notch. */
    SurfacePoint2 corners[4] = {{u0,v0},{u1,v0},{u1,v1},{u0,v1}};
    const int adjacent[4][2] = {{0,2},{1,2},{1,3},{0,3}};
    for (int i = 0; i < 4; ++i)
        if (!f[adjacent[i][0]] && !f[adjacent[i][1]] &&
                poly_point_on_edge(loop, corners[i])) return -1;

    if (flush == 0) *cls = OBSTACLE_HOLE;
    else if (flush == 1) *cls = OBSTACLE_NOTCH;
    else if (flush == 2 && !((f[0] && f[1]) || (f[2] && f[3])))
        *cls = OBSTACLE_CORNER;
    else *cls = OBSTACLE_SPLIT;
    *out_u0 = u0; *out_v0 = v0; *out_u1 = u1; *out_v1 = v1;
    return 1;
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
            int contact = classify_rect_outline(&b->outline, u0, v0, u1, v1,
                    &cls, &cu0, &cv0, &cu1, &cv1);
            if (contact == 0) continue;
            if (contact < 0) {
                /* Keep the identity for R15, but never claim a clipped rectangle.
                 * Unselected invalid items must not block a valid explicit item. */
                cls = OBSTACLE_DEGENERATE;
                cu0 = u0; cv0 = v0; cu1 = u1; cv1 = v1;
            }
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

/* ============================================================
 * apply-proj：鬼影轉真幾何（R8 快照式衍生,單一交易）
 *
 *   apply-proj <boundary_id> <item_id>… [cut-strip]
 *
 *   分類沿用 world_face_obstacles 的同一函式（R10）:
 *     hole               → 新增孔環
 *     notch/corner/
 *     top_notch/top_drop → 外環單一覆蓋弧切凹口
 *     split              → 外環切兩片;原 id 給面積最大片(🔒 Q9);
 *                          立面貼牆柱再生新立面（柱露出側面）
 *     strip              → 僅帶 cut-strip 才執行(🔒 Q8):依條帶矩形
 *                          自身接觸再分類套用 + 樑底新平面 + 兩側新立面
 *
 *   拆片/生成面一律是「新邊界面 + 同框承載面」:同一方向槽位只容
 *   一面且跨軸範圍要滿室寬(space_construct),拆片與薄面天生進不了
 *   成員,故空間成員=原面退出,新面皆游離（I17 的另一側）。
 *   新邊 fixity 一律 F(R10);整筆 world_revalidate,失敗回滾。
 * ============================================================ */

/* 邊在貼邊線上與 R 覆蓋跨距的重疊;s0/s1 = 沿 a→e 方向的端點切線座標 */
static bool proj_edge_covered(
    const bool flush[4],
    Coord u0, Coord v0, Coord u1, Coord v1,
    SurfacePoint2 a, SurfacePoint2 e,
    Coord *s0, Coord *s1
)
{
    Coord lo, hi, cov_lo, cov_hi;

    if (a.u == e.u) {
        if (flush[0] && a.u == u0)      { lo = v0; hi = v1; }
        else if (flush[1] && a.u == u1) { lo = v0; hi = v1; }
        else return false;
        cov_lo = coord_max(coord_min(a.v, e.v), lo);
        cov_hi = coord_min(coord_max(a.v, e.v), hi);
        if (cov_lo >= cov_hi) return false;
        if (a.v < e.v) { *s0 = cov_lo; *s1 = cov_hi; }
        else           { *s0 = cov_hi; *s1 = cov_lo; }
        return true;
    }
    if (a.v == e.v) {
        if (flush[2] && a.v == v0)      { lo = u0; hi = u1; }
        else if (flush[3] && a.v == v1) { lo = u0; hi = u1; }
        else return false;
        cov_lo = coord_max(coord_min(a.u, e.u), lo);
        cov_hi = coord_min(coord_max(a.u, e.u), hi);
        if (cov_lo >= cov_hi) return false;
        if (a.u < e.u) { *s0 = cov_lo; *s1 = cov_hi; }
        else           { *s0 = cov_hi; *s1 = cov_lo; }
        return true;
    }
    return false;
}

static SurfacePoint2 proj_pt_on_edge(SurfacePoint2 a, SurfacePoint2 e, Coord t)
{
    if (a.u == e.u) return (SurfacePoint2){ a.u, t };
    return (SurfacePoint2){ t, a.v };
}

/* 單一覆蓋弧切法：貼一線→內線兩點凹口;貼兩鄰線→遠角一點切角。
 * 覆蓋弧若出現兩段以上 = 退化,回 false(整筆回滾)。 */
static bool proj_cut_run(
    PolygonLoop2 *loop,
    const bool flush[4],
    Coord u0, Coord v0, Coord u1, Coord v1
)
{
    int nflush = (flush[0] ? 1 : 0) + (flush[1] ? 1 : 0) +
                 (flush[2] ? 1 : 0) + (flush[3] ? 1 : 0);
    if (nflush < 1 || nflush > 2) return false;
    /* 對邊貼合是 split,不在此處理。 */
    if ((flush[0] && flush[1]) || (flush[2] && flush[3])) return false;

    SurfacePoint2 nv[POLY_MAX_VERTICES];
    EdgeFixity nf[POLY_MAX_VERTICES];
    size_t m = 0, n = loop->count;
    bool in_run = false, emitted = false;
    Coord run_s0 = 0;

    /* 找一條未覆蓋的邊當起點(覆蓋弧跨環尾的迴繞情形)。 */
    size_t start = SIZE_MAX;
    for (size_t i = 0; i < n; ++i) {
        Coord s0, s1;
        if (!proj_edge_covered(flush, u0, v0, u1, v1,
                loop->v[i], loop->v[(i + 1) % n], &s0, &s1)) {
            start = i;
            break;
        }
    }
    if (start == SIZE_MAX) return false;   /* 整環被覆蓋:退化 */

    for (size_t k = 0; k < n; ++k) {
        size_t i = (start + k) % n;
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 e = loop->v[(i + 1) % n];
        Coord s0, s1;
        bool cov = proj_edge_covered(flush, u0, v0, u1, v1, a, e, &s0, &s1);

        if (!cov) {
            if (in_run) {
                /* 弧結束於頂點 a:補 detour + a 當出點 */
                if (!emitted) {
                    if (nflush == 1) {
                        SurfacePoint2 i0, i1;
                        if (flush[0])      { i0=(SurfacePoint2){u1,run_s0}; i1=(SurfacePoint2){u1,a.v}; }
                        else if (flush[1]) { i0=(SurfacePoint2){u0,run_s0}; i1=(SurfacePoint2){u0,a.v}; }
                        else if (flush[2]) { i0=(SurfacePoint2){run_s0,v1}; i1=(SurfacePoint2){a.u,v1}; }
                        else               { i0=(SurfacePoint2){run_s0,v0}; i1=(SurfacePoint2){a.u,v0}; }
                        nv[m]=i0; nf[m]=EDGE_FIXED; ++m;
                        nv[m]=i1; nf[m]=EDGE_FIXED; ++m;
                    } else {
                        SurfacePoint2 far_point;
                        if (flush[0] && flush[2])      far_point=(SurfacePoint2){u1,v1};
                        else if (flush[0] && flush[3]) far_point=(SurfacePoint2){u1,v0};
                        else if (flush[1] && flush[2]) far_point=(SurfacePoint2){u0,v1};
                        else                           far_point=(SurfacePoint2){u0,v0};
                        nv[m]=far_point; nf[m]=EDGE_FIXED; ++m;
                    }
                    emitted = true;
                }
                in_run = false;
            }
            nv[m] = a; nf[m] = loop->fixity[i]; ++m;
            continue;
        }

        /* 覆蓋邊:進點 ent(s0)、出點 ext(s1) */
        SurfacePoint2 ent = proj_pt_on_edge(a, e, s0);
        SurfacePoint2 ext = proj_pt_on_edge(a, e, s1);
        if (!in_run) {
            if (emitted) return false;   /* 第二段覆蓋弧:退化 */
            in_run = true;
            run_s0 = s0;
            nv[m] = a; nf[m] = loop->fixity[i]; ++m;
            if (ent.u != a.u || ent.v != a.v) {
                nv[m] = ent; nf[m] = EDGE_FIXED; ++m;
            }
        }
        if (ext.u != e.u || ext.v != e.v) {
            /* 弧在此邊中段結束:detour + 出點 */
            if (!emitted) {
                if (nflush == 1) {
                    SurfacePoint2 i0, i1;
                    if (flush[0])      { i0=(SurfacePoint2){u1,run_s0}; i1=(SurfacePoint2){u1,s1}; }
                    else if (flush[1]) { i0=(SurfacePoint2){u0,run_s0}; i1=(SurfacePoint2){u0,s1}; }
                    else if (flush[2]) { i0=(SurfacePoint2){run_s0,v1}; i1=(SurfacePoint2){s1,v1}; }
                    else               { i0=(SurfacePoint2){run_s0,v0}; i1=(SurfacePoint2){s1,v0}; }
                    nv[m]=i0; nf[m]=EDGE_FIXED; ++m;
                    nv[m]=i1; nf[m]=EDGE_FIXED; ++m;
                } else {
                    SurfacePoint2 far_point;
                    if (flush[0] && flush[2])      far_point=(SurfacePoint2){u1,v1};
                    else if (flush[0] && flush[3]) far_point=(SurfacePoint2){u1,v0};
                    else if (flush[1] && flush[2]) far_point=(SurfacePoint2){u0,v1};
                    else                           far_point=(SurfacePoint2){u0,v0};
                    nv[m]=far_point; nf[m]=EDGE_FIXED; ++m;
                }
                emitted = true;
            }
            nv[m] = ext; nf[m] = EDGE_FIXED; ++m;
            in_run = false;
        }
        /* ext==e → 弧延續到下一邊,e 落弧內自然丟棄 */
    }

    if (!emitted || m < 4 || m > POLY_MAX_VERTICES) return false;
    memcpy(loop->v, nv, m * sizeof(nv[0]));
    memcpy(loop->fixity, nf, m * sizeof(nf[0]));
    loop->count = m;
    return poly_loop_is_valid(loop);
}

/* 對邊貼合拆分:覆蓋弧把環切成兩段,各段 + R 側邊封口成新環。 */
static bool proj_split_loop(
    const PolygonLoop2 *loop,
    const bool flush[4],
    Coord u0, Coord v0, Coord u1, Coord v1,
    PolygonLoop2 *p1,
    PolygonLoop2 *p2
)
{
    (void)u1;
    PolygonLoop2 *pieces[2] = { p1, p2 };
    size_t pc = 0, n = loop->count;
    bool in_run = false;

    p1->count = p2->count = 0;

    size_t start = SIZE_MAX;
    for (size_t i = 0; i < n; ++i) {
        Coord s0, s1;
        if (!proj_edge_covered(flush, u0, v0, u1, v1,
                loop->v[i], loop->v[(i + 1) % n], &s0, &s1)) {
            start = i;
            break;
        }
    }
    if (start == SIZE_MAX) return false;

    for (size_t k = 0; k < n; ++k) {
        size_t i = (start + k) % n;
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 e = loop->v[(i + 1) % n];
        Coord s0, s1;
        PolygonLoop2 *cur = pieces[pc];
        bool cov = proj_edge_covered(flush, u0, v0, u1, v1, a, e, &s0, &s1);

        if (!cov) {
            if (in_run) {
                /* 弧剛結束於頂點 a:a 是下一片的接觸起點 */
                pc ^= 1; cur = pieces[pc]; in_run = false;
            }
            cur->v[cur->count] = a;
            cur->fixity[cur->count] = loop->fixity[i];
            ++cur->count;
            if (cur->count > POLY_MAX_VERTICES) return false;
            continue;
        }

        SurfacePoint2 ent = proj_pt_on_edge(a, e, s0);
        SurfacePoint2 ext = proj_pt_on_edge(a, e, s1);
        if (!in_run) {
            in_run = true;
            /* a 若在弧外先收進本片;進點是本片邊界的一部分 */
            if (ent.u != a.u || ent.v != a.v) {
                cur->v[cur->count] = a;
                cur->fixity[cur->count] = loop->fixity[i];
                ++cur->count;
            }
            cur->v[cur->count] = ent;
            cur->fixity[cur->count] = EDGE_FIXED;
            ++cur->count;
            if (cur->count > POLY_MAX_VERTICES) return false;
        }
        if (ext.u != e.u || ext.v != e.v) {
            /* 弧中段結束:換片,新片從出點起 */
            pc ^= 1; cur = pieces[pc]; in_run = false;
            cur->v[cur->count] = ext;
            cur->fixity[cur->count] = EDGE_FIXED;
            ++cur->count;
            if (cur->count > POLY_MAX_VERTICES) return false;
        }
    }

    /* 兩片都封口:末頂點→首頂點的邊是 R 側邊,fixity=F */
    if (p1->count >= 4) p1->fixity[p1->count - 1] = EDGE_FIXED;
    if (p2->count >= 4) p2->fixity[p2->count - 1] = EDGE_FIXED;
    return p1->count >= 4 && p2->count >= 4 &&
           poly_loop_is_valid(p1) && poly_loop_is_valid(p2);
}

/* 拆分後孔重分配:依孔頂點落在哪一片,把孔搬到該片的 boundary。
 * 孔跨切線=退化 → 頂點兩片都不含 → 孔丟失 → 後續 revalidate 擋下回滾。 */
static void proj_redistribute_holes(
    SpaceBoundarySurface *keep_b,
    SpaceBoundarySurface *other_b
)
{
    PolygonLoop2 hs[POLY_MAX_HOLES];
    size_t nh = keep_b->hole_count;

    memcpy(hs, keep_b->holes, nh * sizeof(hs[0]));
    keep_b->hole_count = 0;
    for (size_t i = 0; i < nh; ++i) {
        SpaceBoundarySurface *dst =
            poly_contains_point(&keep_b->outline, hs[i].v[0])
            ? keep_b : other_b;
        if (dst->hole_count >= POLY_MAX_HOLES) {
            dst = keep_b;   /* 放不下:塞回原處,revalidate 會擋 */
        }
        dst->holes[dst->hole_count++] = hs[i];
    }
}

/* 環的有向面積(兩倍)。 */
static Coord proj_loop_area2(const PolygonLoop2 *loop)
{
    Coord a2 = 0;
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 b = loop->v[(i + 1) % loop->count];
        a2 += a.u * b.v - b.u * a.v;
    }
    return a2 < 0 ? -a2 : a2;
}

/* 新邊界面 + 同框承載面加入 World(交易內直接寫,id 由呼叫者配)。 */
static bool proj_add_surface(
    World *world,
    uint32_t id,
    const SurfaceFrame *frame,
    const PolygonLoop2 *outline,
    Coord ru0, Coord rv0, Coord ru1, Coord rv1
)
{
    if (world->boundary_count >= WORLD_MAX_BOUNDARIES ||
        world->placement_count >= WORLD_MAX_PLACEMENTS) {
        return false;
    }
    SpaceBoundarySurface *b = &world->boundaries[world->boundary_count];
    memset(b, 0, sizeof(*b));
    b->id = id;
    b->kind = BOUNDARY_UNSPECIFIED;
    b->outline = *outline;
    ++world->boundary_count;

    PlacementSurface *p = &world->placements[world->placement_count];
    memset(p, 0, sizeof(*p));
    p->id = id;
    p->boundary_id = id;
    p->frame = *frame;
    p->rect = (SurfaceRegion2){ ru0, rv0, ru1, rv1 };
    ++world->placement_count;
    return true;
}

/* 從 World 配一組新 boundary/placement id;0 = 配不到(GEO-158)。 */
static uint32_t proj_next_surface_id(const World *world)
{
    return world_next_surface_id(world);
}

/* 把 bid 從所屬空間成員清單移除(拆片面/生成面進不了槽位)。 */
static void proj_space_drop_member(World *world, uint32_t bid)
{
    for (size_t i = 0; i < world->space_count; ++i) {
        Space *s = &world->spaces[i];
        for (size_t m = 0; m < s->boundary_count; ++m) {
            if (s->boundaries[m] == bid) {
                memmove(&s->boundaries[m], &s->boundaries[m + 1],
                    (s->boundary_count - m - 1) * sizeof(s->boundaries[0]));
                --s->boundary_count;
                return;
            }
        }
    }
}

/*
 * 拆面後,掛在原承載面上的參考線/網格/角材要跟著含其錨點的
 * 那片走(與孔重新分配同一條「資料跟材料走」規則):
 *   - 只在保留片合法 → 留原 placement;
 *   - 只在新片合法 → 改掛新 placement;
 *   - 兩片都合法 → 留原片(對使用者資料最少驚訝);
 *   - 兩片都不含(錨點落在被移除的條帶區)→ 回報 false,
 *     由 apply-proj 交易整筆回滾,不靜默丟資料。
 * new_b 必須是剛由 proj_add_surface 追加的那片(取 placement
 * 用陣列尾)。
 */
/* 公理 R13：拆分時承載面輔助資料跟著含錨點的那片走；
 * 兩片都不含 = 失去承載面 → 整筆拒絕回滾，不靜默丟資料。 */
#include "geometry-core/subgrid_rebind.inc"

static bool proj_rebind_aux(
    World *world,
    const PlacementSurface *old_pl,
    const SpaceBoundarySurface *keep_b,
    const SpaceBoundarySurface *new_b,
    SurfaceId new_pl_id
)
{
    const PlacementSurface *new_pl =
        &world->placements[world->placement_count - 1];

    for (size_t i = 0; i < world->grid_count; ++i) {
        ReferenceGrid *g = &world->grids[i];
        if (g->is_subgrid || g->placement_id != old_pl->id) continue;
        bool k = subgrid_family_fits(world,g,old_pl,keep_b);
        bool n = subgrid_family_fits(world,g,new_pl,new_b);
        if (n && !k) {
            uint32_t parent_id=g->id;
            for (size_t j=0;j<world->grid_count;++j) {
                ReferenceGrid *member=&world->grids[j];
                if (member->id==parent_id || (member->is_subgrid && member->parent_id==parent_id)) member->placement_id=new_pl_id;
            }
        } else if (!k && !n) return false;
    }
    World source=*world;
    for (size_t i=0;i<source.guide_count;++i) {
        if (source.guides[i].placement_id!=old_pl->id) continue;
        GuideLine keep,other;
        bool k=reference_fragment_candidate(&source,old_pl->id,old_pl->id,false,i,&keep,NULL,NULL);
        bool n=reference_fragment_candidate(&source,old_pl->id,new_pl_id,false,i,&other,NULL,NULL);
        if (!k && !n) return false;
        world->guides[i]=k?keep:other;
    }
    for (size_t i=0;i<source.timber_count;++i) {
        if (!source.timbers[i].placed || source.anchors[i].placement_id!=old_pl->id) continue;
        Timber keep,other; TimberAnchor ka,na;
        bool k=reference_fragment_candidate(&source,old_pl->id,old_pl->id,true,i,NULL,&keep,&ka);
        bool n=reference_fragment_candidate(&source,old_pl->id,new_pl_id,true,i,NULL,&other,&na);
        if (!k && !n) return false;
        world->timbers[i]=k?keep:other;
        world->anchors[i]=k?ka:na;
    }
    return engineering_follow_fragment(world,old_pl->id);
}

/* 生成面:房間座標矩形 → 自備框(法向朝外)建 boundary+placement。
 *   axis_a/axis_b = 面上兩軸的軸索引(0/1/2);normal 由 u×v 定。 */
/* 公理 R16：top_drop（邊樑整段降低）= 半平面裁切——矩形必跨滿垂直向全幅
 * 且到達輪廓端緣，保留側即新外環；否則拒絕。 */
static bool proj_spawn_face(
    World *world,
    int axis_u, Coord u_lo, Coord u_hi,
    int axis_v, Coord v_lo, Coord v_hi,
    int axis_n, Coord n_plane, int n_sign
)
{
    uint32_t id = proj_next_surface_id(world);
    SurfaceFrame f;

    if (id == 0) return false;      /* GEO-158：配不到就整筆失敗,不追加重複 id */
    memset(&f, 0, sizeof(f));
    f.axis_u.x = axis_u == 0 ? 1 : 0;
    f.axis_u.y = axis_u == 1 ? 1 : 0;
    f.axis_u.z = axis_u == 2 ? 1 : 0;
    f.axis_v.x = axis_v == 0 ? 1 : 0;
    f.axis_v.y = axis_v == 1 ? 1 : 0;
    f.axis_v.z = axis_v == 2 ? 1 : 0;
    f.normal.x = axis_n == 0 ? n_sign : 0;
    f.normal.y = axis_n == 1 ? n_sign : 0;
    f.normal.z = axis_n == 2 ? n_sign : 0;
    f.origin.x = axis_u == 0 ? u_lo : axis_v == 0 ? v_lo : n_plane;
    f.origin.y = axis_u == 1 ? u_lo : axis_v == 1 ? v_lo : n_plane;
    f.origin.z = axis_u == 2 ? u_lo : axis_v == 2 ? v_lo : n_plane;

    PolygonLoop2 o;
    memset(&o, 0, sizeof(o));
    o.count = 4;
    o.v[0] = (SurfacePoint2){ 0, 0 };
    o.v[1] = (SurfacePoint2){ u_hi - u_lo, 0 };
    o.v[2] = (SurfacePoint2){ u_hi - u_lo, v_hi - v_lo };
    o.v[3] = (SurfacePoint2){ 0, v_hi - v_lo };
    for (int i = 0; i < 4; ++i) o.fixity[i] = EDGE_FIXED;

    return proj_add_surface(world, id, &f, &o,
        0, 0, u_hi - u_lo, v_hi - v_lo);
}

/* 半平面裁切:axis 0=u 1=v;keep -1 留 <=cut 側,+1 留 >=cut 側。
 * 供 top_drop「整段降低」:矩形跨滿垂直向全幅時,保留側即新輪廓。
 * 非連通/退化結果由 poly_loop_is_valid 擋下 → 整筆回滾。 */
static bool proj_clip_half(
    PolygonLoop2 *loop,
    int axis,
    Coord cut,
    int keep
)
{
    SurfacePoint2 nv[POLY_MAX_VERTICES];
    EdgeFixity nf[POLY_MAX_VERTICES];
    size_t m = 0, n = loop->count;

    for (size_t i = 0; i < n; ++i) {
        SurfacePoint2 a = loop->v[i];
        SurfacePoint2 e = loop->v[(i + 1) % n];
        Coord ca = axis ? a.v : a.u;
        Coord ce = axis ? e.v : e.u;
        bool ina = keep < 0 ? ca <= cut : ca >= cut;
        bool ine = keep < 0 ? ce <= cut : ce >= cut;

        if (ina) {
            nv[m] = a; nf[m] = loop->fixity[i]; ++m;
        }
        if (ina != ine) {
            /* 正交環的跨線邊必沿被裁軸;交點落在 a/e 上時不補 */
            SurfacePoint2 x = a;
            if (axis) x.v = cut; else x.u = cut;
            if ((x.u != a.u || x.v != a.v) &&
                (x.u != e.u || x.v != e.v)) {
                nv[m] = x; nf[m] = EDGE_FIXED; ++m;
            }
        }
        if (m > POLY_MAX_VERTICES) return false;
    }
    /* 去重相鄰同點(含首尾迴繞) */
    size_t w = 0;
    for (size_t i = 0; i < m; ++i) {
        if (w > 0 && nv[w - 1].u == nv[i].u &&
            nv[w - 1].v == nv[i].v) continue;
        nv[w] = nv[i]; nf[w] = nf[i]; ++w;
    }
    if (w > 1 && nv[0].u == nv[w - 1].u &&
        nv[0].v == nv[w - 1].v) --w;
    if (w < 3) return false;
    memcpy(loop->v, nv, w * sizeof(nv[0]));
    memcpy(loop->fixity, nf, w * sizeof(nf[0]));
    loop->count = w;
    return poly_loop_is_valid(loop);
}

/* 套用單一障礙項到邊界面 b(已取快照 items;world 已在交易中)。
 * out_new_bid:若本次拆分產生新片,回傳新片 boundary id,否則 0。 */
/* 公理 R14：apply-proj 逐項選片——每個指定項以快照矩形對原片與交易內
 * 拆出的同平面新片做接觸分類，套到唯一接觸的那片；橫跨拆分線或不接觸
 * 任何片 = 無法歸屬 → 拒絕。
 * 公理 R17：貼牆柱露出面在柱遠側緣平面——新立面與牆同法向，
 * 但平面座標在柱遠離牆的那條棱線上，不在牆平面上。 */
static bool proj_apply_one(
    World *world,
    SpaceBoundarySurface *b,
    const PlacementSurface *pl,
    const FaceObstacle *it,
    bool cut_strip,
    uint32_t *out_new_bid,
    const char *path,
    int line_no
)
{
    Coord u0 = it->u_lo, v0 = it->v_lo, u1 = it->u_hi, v1 = it->v_hi;
    if (out_new_bid) *out_new_bid = 0;
    if (it->cls == OBSTACLE_DEGENERATE) {
        scene_error(path, line_no, RECT_CONTACT_ERROR);
        return false;
    }

    if (it->cls == OBSTACLE_HOLE) {
        if (b->hole_count >= POLY_MAX_HOLES) {
            scene_error(path, line_no, "孔數超過上限");
            return false;
        }
        PolygonLoop2 *h = &b->holes[b->hole_count];
        memset(h, 0, sizeof(*h));
        h->count = 4;
        h->v[0] = (SurfacePoint2){ u0, v0 };
        h->v[1] = (SurfacePoint2){ u1, v0 };
        h->v[2] = (SurfacePoint2){ u1, v1 };
        h->v[3] = (SurfacePoint2){ u0, v1 };
        for (int i = 0; i < 4; ++i) h->fixity[i] = EDGE_FIXED;
        ++b->hole_count;
        return true;
    }

    /* 貼邊資訊:對外環重算一次(與分類同條件)。 */
    bool flush[4];
    for (int s = 0; s < 4; ++s)
        flush[s] = side_flush_outline(&b->outline, s, u0, v0, u1, v1);

    if (it->cls == OBSTACLE_TOP_DROP) {
        /* 整段降低:矩形必跨滿垂直向全幅 → 半平面裁切保留側。
           未到端緣(非矩形輪廓等)無法判定降側 → 拒絕回滾。 */
        Coord ob0, ob1, ob2, ob3;
        int axis, keep;
        Coord cut;
        poly_bbox(&b->outline, &ob0, &ob1, &ob2, &ob3);
        if (v0 <= ob1 && v1 >= ob3) {
            axis = 0;
            if (u1 >= ob2)      { cut = u0; keep = -1; }
            else if (u0 <= ob0) { cut = u1; keep = +1; }
            else {
                scene_error(path, line_no,
                    "整段降低的矩形未到輪廓端緣");
                return false;
            }
        } else if (u0 <= ob0 && u1 >= ob2) {
            axis = 1;
            if (v1 >= ob3)      { cut = v0; keep = -1; }
            else if (v0 <= ob1) { cut = v1; keep = +1; }
            else {
                scene_error(path, line_no,
                    "整段降低的矩形未到輪廓端緣");
                return false;
            }
        } else {
            scene_error(path, line_no, "整段降低的矩形未跨滿輪廓");
            return false;
        }
        if (!proj_clip_half(&b->outline, axis, cut, keep)) {
            scene_error(path, line_no, "整段降低切法退化");
            return false;
        }
        /* 降後不再滿室高 → 同 R11 退出空間成員變游離面。 */
        proj_space_drop_member(world, b->id);
        return true;
    }

    if (it->cls == OBSTACLE_NOTCH || it->cls == OBSTACLE_CORNER ||
        it->cls == OBSTACLE_TOP_NOTCH) {
        if (!proj_cut_run(&b->outline, flush, u0, v0, u1, v1)) {
            scene_error(path, line_no, "凹口切法退化(覆蓋弧不連續)");
            return false;
        }
        return true;
    }

    if (it->cls == OBSTACLE_STRIP) {
        if (!cut_strip) return true;    /* 🔒 Q8:未勾選=不裁 */
        /* 條帶矩形自身再分類 → 依接觸切天花 */
        ObstacleClass sc;
        Coord cu0, cv0, cu1, cv1;
        int contact = classify_rect_outline(&b->outline, u0, v0, u1, v1,
                &sc, &cu0, &cv0, &cu1, &cv1);
        if (contact <= 0) {
            scene_error(path, line_no, contact < 0 ? RECT_CONTACT_ERROR : "條帶不與輪廓接觸");
            return false;
        }
        bool sf[4];
        for (int s = 0; s < 4; ++s)
            sf[s] = side_flush_outline(&b->outline, s, cu0, cv0, cu1, cv1);
        if (sc == OBSTACLE_HOLE) {
            PolygonLoop2 *h;
            if (b->hole_count >= POLY_MAX_HOLES) return false;
            h = &b->holes[b->hole_count];
            memset(h, 0, sizeof(*h));
            h->count = 4;
            h->v[0] = (SurfacePoint2){ cu0, cv0 };
            h->v[1] = (SurfacePoint2){ cu1, cv0 };
            h->v[2] = (SurfacePoint2){ cu1, cv1 };
            h->v[3] = (SurfacePoint2){ cu0, cv1 };
            for (int i = 0; i < 4; ++i) h->fixity[i] = EDGE_FIXED;
            ++b->hole_count;
        } else if (sc == OBSTACLE_SPLIT) {
            PolygonLoop2 p1, p2;
            if (!proj_split_loop(&b->outline, sf, cu0, cv0, cu1, cv1,
                    &p1, &p2)) {
                scene_error(path, line_no, "條帶拆分退化");
                return false;
            }
            Coord a1 = proj_loop_area2(&p1), a2 = proj_loop_area2(&p2);
            PolygonLoop2 *keep = a1 >= a2 ? &p1 : &p2;
            PolygonLoop2 *other = a1 >= a2 ? &p2 : &p1;
            uint32_t nid = proj_next_surface_id(world);
            Coord r0, r1, r2, r3;
            if (nid == 0) {
                scene_error(path, line_no, "配不到新的面編號（編號已用盡）");
                return false;
            }
            poly_bbox(other, &r0, &r1, &r2, &r3);
            if (!proj_add_surface(world, nid, &pl->frame, other,
                    r0, r1, r2, r3)) {
                scene_error(path, line_no, "面數超過上限");
                return false;
            }
            if (out_new_bid) *out_new_bid = nid;
            b->outline = *keep;
            proj_redistribute_holes(b,
                &world->boundaries[world->boundary_count - 1]);
            if (!proj_rebind_aux(world, pl, b,
                    &world->boundaries[world->boundary_count - 1],
                    nid)) {
                scene_error(path, line_no,
                    g_engineering_error[0]?g_engineering_error:"拆分後參考線/網格/角材失去承載面");
                return false;
            }
            proj_space_drop_member(world, b->id);
        } else {
            if (!proj_cut_run(&b->outline, sf, cu0, cv0, cu1, cv1)) {
                scene_error(path, line_no, "條帶凹口切法退化");
                return false;
            }
        }
        /* 樑底新平面(z_lo)+ 樑兩側新立面 */
        const RcBeam *bm = NULL;
        for (size_t i = 0; i < world->beam_count; ++i)
            if (world->beams[i].id == it->id) bm = &world->beams[i];
        if (bm == NULL) return false;
        if (!proj_spawn_face(world, 1, bm->y_lo, bm->y_hi,
                0, bm->x_lo, bm->x_hi, 2, bm->z_lo, -1)) {
            scene_error(path, line_no, "面數超過上限(樑底)");
            return false;
        }
        if (bm->axis == 0) {
            if (!proj_spawn_face(world, 0, bm->x_lo, bm->x_hi,
                    2, bm->z_lo, bm->z_hi, 1, bm->y_lo, -1) ||
                !proj_spawn_face(world, 2, bm->z_lo, bm->z_hi,
                    0, bm->x_lo, bm->x_hi, 1, bm->y_hi, +1)) {
                scene_error(path, line_no, "面數超過上限(樑側)");
                return false;
            }
        } else {
            /* x_lo 側面 -X:u=+z v=+y(ẑ×ŷ=-x̂);
               x_hi 側面 +X:u=+y v=+z(ŷ×ẑ=+x̂) */
            if (!proj_spawn_face(world, 2, bm->z_lo, bm->z_hi,
                    1, bm->y_lo, bm->y_hi, 0, bm->x_lo, -1) ||
                !proj_spawn_face(world, 1, bm->y_lo, bm->y_hi,
                    2, bm->z_lo, bm->z_hi, 0, bm->x_hi, +1)) {
                scene_error(path, line_no, "面數超過上限(樑側)");
                return false;
            }
        }
        return true;
    }

    /* OBSTACLE_SPLIT */
    {
        PolygonLoop2 p1, p2;
        if (!proj_split_loop(&b->outline, flush, u0, v0, u1, v1,
                &p1, &p2)) {
            scene_error(path, line_no, "拆分退化(覆蓋弧不是兩段)");
            return false;
        }
        Coord a1 = proj_loop_area2(&p1), a2 = proj_loop_area2(&p2);
        PolygonLoop2 *keep = a1 >= a2 ? &p1 : &p2;
        PolygonLoop2 *other = a1 >= a2 ? &p2 : &p1;
        uint32_t nid = proj_next_surface_id(world);
        Coord r0, r1, r2, r3;
        if (nid == 0) {
            scene_error(path, line_no, "配不到新的面編號（編號已用盡）");
            return false;
        }
        poly_bbox(other, &r0, &r1, &r2, &r3);
        if (!proj_add_surface(world, nid, &pl->frame, other,
                r0, r1, r2, r3)) {
            scene_error(path, line_no, "面數超過上限");
            return false;
        }
        if (out_new_bid) *out_new_bid = nid;
        b->outline = *keep;
        proj_redistribute_holes(b,
            &world->boundaries[world->boundary_count - 1]);
        if (!proj_rebind_aux(world, pl, b,
                &world->boundaries[world->boundary_count - 1],
                nid)) {
            scene_error(path, line_no,
                g_engineering_error[0]?g_engineering_error:"拆分後參考線/網格/角材失去承載面");
            return false;
        }
        proj_space_drop_member(world, b->id);

        /* 立面貼牆柱:柱露出側面生成新立面(同牆平面/法向) */
        if (!it->is_beam) {
            const RcColumn *c = NULL;
            for (size_t i = 0; i < world->column_count; ++i)
                if (world->columns[i].id == it->id) c = &world->columns[i];
            if (c == NULL) return false;
            int na = axis_index(pl->frame.normal);
            Coord np = point3_component(pl->frame.origin, na);
            int ns = na == 0 ? (int)pl->frame.normal.x
                   : na == 1 ? (int)pl->frame.normal.y
                             : (int)pl->frame.normal.z;
            /* 露出側面在柱遠側緣(材料側與牆同向,normal 沿用):
               牆 x=0(n=-X)→ x_hi;牆 x=W(n=+X)→ x_lo,y 牆同理。 */
            SurfaceFrame f = pl->frame;
            Coord edge = ns < 0
                ? (na == 0 ? c->x_hi : c->y_hi)
                : (na == 0 ? c->x_lo : c->y_lo);
            if (na == 0)      f.origin.x = edge;
            else if (na == 1) f.origin.y = edge;
            else              f.origin.z = edge;
            (void)np;
            Coord fu0, fv0, fu1, fv1;
            box_project_uv(&f, c->x_lo, c->x_hi, c->y_lo, c->y_hi,
                c->z_lo, c->z_hi, &fu0, &fv0, &fu1, &fv1);
            /* 新面 = 同牆框 + 柱露出 uv 矩形 */
            PolygonLoop2 o;
            memset(&o, 0, sizeof(o));
            o.count = 4;
            o.v[0] = (SurfacePoint2){ fu0, fv0 };
            o.v[1] = (SurfacePoint2){ fu1, fv0 };
            o.v[2] = (SurfacePoint2){ fu1, fv1 };
            o.v[3] = (SurfacePoint2){ fu0, fv1 };
            for (int i = 0; i < 4; ++i) o.fixity[i] = EDGE_FIXED;
            uint32_t sid2 = proj_next_surface_id(world);
            if (sid2 == 0) {
                scene_error(path, line_no, "配不到新的面編號（編號已用盡）");
                return false;
            }
            if (!proj_add_surface(world, sid2, &f, &o,
                    fu0, fv0, fu1, fv1)) {
                scene_error(path, line_no, "面數超過上限(柱側面)");
                return false;
            }
        }
        return true;
    }
}

/* 公理 R12：項目 id 加 c/b 前綴消歧（柱樑共用數值 id 空間）。
 * 公理 R15：列出的每個 id 都必須匹配到項目，否則整筆拒絕回滾——
 *           不靜默忽略、不部分套用。 */
static bool apply_applyproj_line(
    const char *path,
    int line_no,
    char *tokens[],
    int count,
    World *world
)
{
    if (count < 3) {
        scene_error(path, line_no,
            "apply-proj 用法:apply-proj <boundary_id> <item_id>… [cut-strip]");
        return false;
    }
    uint32_t bid;
    if (!parse_u32(tokens[1], &bid)) {
        scene_error(path, line_no, "apply-proj 的面 id 不是有效整數");
        return false;
    }
    SpaceBoundarySurface *b = NULL;
    for (size_t i = 0; i < world->boundary_count; ++i) {
        if (world->boundaries[i].id == bid) {
            b = &world->boundaries[i];
            break;
        }
    }
    if (b == NULL) {
        scene_error(path, line_no, "apply-proj 的邊界面不存在");
        return false;
    }
    const PlacementSurface *pl = NULL;
    for (size_t i = 0; i < world->placement_count; ++i) {
        if (world->placements[i].boundary_id == bid) {
            pl = &world->placements[i];
            break;
        }
    }
    if (pl == NULL) {
        scene_error(path, line_no,
            "未放置的面不能套用投影（R9）");
        return false;
    }

    bool cut_strip = false;
    uint32_t ids[32];
    int types[32];   /* -1=不限,0=柱,1=樑;柱樑 id 空間相同,需型別消歧 */
    size_t nids = 0;
    for (int i = 2; i < count && nids < 32; ++i) {
        if (strcmp(tokens[i], "cut-strip") == 0) { cut_strip = true; continue; }
        int t = -1;
        const char *num = tokens[i];
        if (num[0] == 'c') { t = 0; ++num; }
        else if (num[0] == 'b') { t = 1; ++num; }
        if (!parse_u32(num, &ids[nids])) {
            scene_error(path, line_no, "apply-proj 的項目 id 不是有效整數");
            return false;
        }
        types[nids] = t;
        ++nids;
    }
    if (nids == 0) {
        scene_error(path, line_no, "apply-proj 至少要一個項目 id");
        return false;
    }

    World backup = *world;
    FaceObstacle items[64];
    size_t n = world_face_obstacles(world, b, items, 64);
    if (n == SIZE_MAX) {
        scene_error(path, line_no, "面未放置，推不出障礙物");
        return false;
    }

    /* 面片清單:拆分產生的新片與原片同平面同框,後續項要套到
       含它的那片(一筆交易內多條帶的情境)。 */
    SpaceBoundarySurface *pb[32];
    const PlacementSurface *pp[32];
    size_t np = 1;
    pb[0] = b; pp[0] = pl;

    size_t applied = 0;
    for (size_t k = 0; k < nids; ++k) {
        bool matched = false;
        for (size_t i = 0; i < n; ++i) {
            if (items[i].id != ids[k]) continue;
            if (types[k] >= 0 && items[i].is_beam != types[k]) continue;
            matched = true;
            /* 選片:矩形應只與一片接觸;橫跨拆分線=無法歸屬,拒絕。 */
            SpaceBoundarySurface *tb = NULL;
            const PlacementSurface *tpl = NULL;
            for (size_t j = 0; j < np; ++j) {
                ObstacleClass pc;
                Coord t0, t1, t2, t3;
                int contact;
                if (items[i].cls == OBSTACLE_STRIP && !cut_strip) {
                    /* R12 skips cutting, not R14 ownership or later R15 items. */
                    contact = proj_rect_outline_touches(&pb[j]->outline,
                            items[i].u_lo, items[i].v_lo,
                            items[i].u_hi, items[i].v_hi) ? 1 : 0;
                } else {
                    contact = classify_rect_outline(&pb[j]->outline,
                            items[i].u_lo, items[i].v_lo,
                            items[i].u_hi, items[i].v_hi,
                            &pc, &t0, &t1, &t2, &t3);
                }
                if (contact < 0) {
                    *world = backup;
                    scene_error(path, line_no, RECT_CONTACT_ERROR);
                    return false;
                }
                if (contact == 0) continue;
                if (tb != NULL) {
                    *world = backup;
                    scene_error(path, line_no,
                        "投影項橫跨拆分線，無法歸屬單一面片");
                    return false;
                }
                tb = pb[j]; tpl = pp[j];
            }
            if (tb == NULL) {
                *world = backup;
                scene_error(path, line_no,
                    "投影項不與任何面片接觸");
                return false;
            }
            uint32_t new_bid = 0;
            if (!proj_apply_one(world, tb, tpl, &items[i], cut_strip,
                    &new_bid, path, line_no)) {
                *world = backup;
                return false;
            }
            ++applied;
            if (new_bid != 0 && np < 32) {
                pb[np] = NULL; pp[np] = NULL;
                for (size_t j = 0; j < world->boundary_count; ++j) {
                    if (world->boundaries[j].id == new_bid) {
                        pb[np] = &world->boundaries[j];
                        break;
                    }
                }
                for (size_t j = 0; j < world->placement_count; ++j) {
                    if (world->placements[j].boundary_id == new_bid) {
                        pp[np] = &world->placements[j];
                        break;
                    }
                }
                if (pb[np] != NULL && pp[np] != NULL) ++np;
            }
        }
        if (!matched) {
            *world = backup;
            scene_error(path, line_no,
                "apply-proj 的項目在此面上不存在（整筆拒絕）");
            return false;
        }
    }
    if (applied == 0) {
        *world = backup;
        scene_error(path, line_no, "這些 id 在此面上沒有可套用的投影");
        return false;
    }

    /* b 可能已不在原位(不會——boundary 陣列是定長 POD);
       但 items 指標已用過,此處只需重驗。 */
    if (!world_revalidate(world)) {
        *world = backup;
        scene_error(path, line_no,
            "套用投影後有物件失效（輪廓退化/空間成員衝突）");
        return false;
    }
    return true;
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
    if (!strcmp(kind,"timber") && assembly_owned(world,id)) { scene_error(path,line_no,"I42: delete the owning assembly instance"); return false; }
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
        for(size_t i=0;i<world->grid_binding_count;++i)if(world->grid_bindings[i].boundary_id==id){
            scene_error(path,line_no,"I37: boundary is still referenced by a grid-binding");return false;
        }
        for(size_t i=0;i<world->vertex_key_count;++i)if(world->vertex_keys[i].boundary_id==id){
            memmove(&world->vertex_keys[i],&world->vertex_keys[i+1],(world->vertex_key_count-i-1)*sizeof(BoundaryVertexKeys));
            memset(&world->vertex_keys[--world->vertex_key_count],0,sizeof(BoundaryVertexKeys));break;
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
            SpaceFaultInfo fault = { SPACE_FAULT_NONE, 0, -1 };
            if (w == 0) {
                rebuild.id = sp->id;
            } else if (!space_construct(world, sp->id,
                                        sp->boundaries, w, &rebuild, &fault)) {
                char why[192];
                char message[256];

                space_fault_describe(&fault, why, sizeof why);
                snprintf(message, sizeof message,
                         "剔除成員後空間 %" PRIu32 " 無法重建：%s",
                         sp->id, why);
                *world = backup;
                scene_error(path, line_no, message);
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
    } else if (strcmp(kind, "datum") == 0) {
        size_t di = SIZE_MAX;
        for (size_t i=0;i<world->datum_count;++i) if (world->datums[i].id==id) di=i;
        if (di==SIZE_MAX) { scene_error(path,line_no,"I7a: datum does not exist"); return false; }
        for (size_t i=0;i<world->guide_count;++i)
            if (world->guides[i].source==GUIDE_DATUM && world->guides[i].datum_id==id) {
                scene_error(path,line_no,"I7a: datum is still referenced by a guide"); return false;
            }
        memmove(&world->datums[di],&world->datums[di+1],(world->datum_count-di-1)*sizeof(DatumPlane));
        --world->datum_count;
        memset(&world->datums[world->datum_count],0,sizeof(DatumPlane));
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
    } else if (strcmp(kind, "grid-binding") == 0) {
        size_t bi=0;while(bi<world->grid_binding_count && world->grid_bindings[bi].id!=id)++bi;
        if(bi==world->grid_binding_count){scene_error(path,line_no,"I37: grid-binding does not exist");return false;}
        for(size_t i=0;i<world->grid_count;++i)if(world->grids[i].from_binding && world->grids[i].binding_id==id){
            scene_error(path,line_no,"I37: grid-binding is still referenced by a grid");return false;
        }
        memmove(&world->grid_bindings[bi],&world->grid_bindings[bi+1],(world->grid_binding_count-bi-1)*sizeof(GridBinding));
        memset(&world->grid_bindings[--world->grid_binding_count],0,sizeof(GridBinding));
        world_drop_canvas_pos(world,CANVAS_POS_GRID_BINDING,id);
    } else if (strcmp(kind, "grid-system") == 0) {
        for(size_t i=0;i<world->grid_binding_count;++i)if(world->grid_bindings[i].system_id==id){
            scene_error(path,line_no,"I37: grid-system is still referenced by a grid-binding");return false;
        }
        size_t si=0;
        while (si<world->grid_system_count && world->grid_systems[si].id!=id) ++si;
        if (si==world->grid_system_count) { scene_error(path,line_no,"I37: grid-system does not exist"); return false; }
        for (size_t i=0;i<world->grid_count;++i) if (world->grids[i].from_system && world->grids[i].system_id==id) {
            char error[160]; snprintf(error,sizeof error,"I37: grid-system %u is still referenced by grid %u",id,world->grids[i].id);
            scene_error(path,line_no,error); return false;
        }
        if(g_parsing_scene_file){
            memmove(g_rule_scene_highwater+si,g_rule_scene_highwater+si+1,(world->grid_system_count-si-1)*sizeof *g_rule_scene_highwater);
            g_rule_scene_highwater[world->grid_system_count-1]=false;
        }
        memmove(&world->grid_systems[si],&world->grid_systems[si+1],(world->grid_system_count-si-1)*sizeof(GridSystem));
        memset(&world->grid_systems[--world->grid_system_count],0,sizeof(GridSystem));
        world_drop_canvas_pos(world,CANVAS_POS_GRID_SYSTEM,id);
    } else if (strcmp(kind, "grid") == 0) {
        size_t gi = SIZE_MAX;

        for (size_t i = 0; i < world->grid_count; ++i) {
            if (world->grids[i].id == id) gi = i;
        }
        if (gi == SIZE_MAX) {
            scene_error(path, line_no, "這個網格不存在");
            return false;
        }
        for (size_t i=0;i<world->grid_count;++i) {
            if (world->grids[i].is_subgrid && world->grids[i].parent_id==id) {
                char err[160]; snprintf(err,sizeof err,"I23：網格 %u 仍有子格 %u，不能刪除",id,world->grids[i].id);
                scene_error(path,line_no,err); return false;
            }
        }
        for (size_t i=0;i<world->guide_count;++i) {
            if (grid_guide_references(&world->guides[i],id)) {
                char err[160]; snprintf(err,sizeof err,"I23：網格 %u 仍被參考線 %u 引用，不能刪除",id,world->guides[i].id);
                scene_error(path,line_no,err); return false;
            }
        }
        for (size_t i = 0; i < world->timber_count; ++i) {
            if (world->timbers[i].placed &&
                ((world->anchors[i].anchor_kind == ANCHOR_AT_GRID && world->anchors[i].ref_grid == id) ||
                 (world->anchors[i].anchor_kind == ANCHOR_AT_RULE && world->anchors[i].ref_rule.grid_id == id))) {
                scene_error(path, line_no,
                    "V_GRID_LOCKED：有角材錨在這個網格上，先刪角材（timber）");
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

    engineering_drop_owned(world,kind,id);
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
    if (space_id == 0) {
        scene_error(path, line_no, RESERVED_SPACE_ID);
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
    SpaceFaultInfo fault = { SPACE_FAULT_NONE, 0, -1 };

    if (face_count == 0) {
        /* 空容器：零成員的部分空間，closed=false、界未釘。 */
        candidate = (Space){ 0 };
        candidate.id = space_id;
    } else if (!space_construct(world, space_id, faces, face_count,
                                &candidate, &fault)) {
        /*
         * 建構子本身就驗成員一致（不改 World）。
         * GEO-041：原本七種失敗共用一句話，使用者得自己猜是哪一種、哪一面。
         */
        char why[192];
        char message[256];

        space_fault_describe(&fault, why, sizeof why);
        snprintf(message, sizeof message, "空間 %" PRIu32 " 組不起來：%s",
                 space_id, why);
        scene_error(path, line_no, message);
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
    if(g_parsing_scene_file)memset(g_rule_scene_highwater,0,sizeof g_rule_scene_highwater);
    return true;
}

/* ============================================================
 * world_dump_dsl：把 World 序列化回 DSL 文本（畫布存檔/匯出用）
 *
 *   原則：輸出是「可重放」的規範形——重放後得到同一個 World。
 *   - 保存 spec、引用式與 at-line/at-face；不輸出衍生 uv/長度。
 *   - 角材依放置順序輸出，參考線依其引用拓樸穿插輸出（R4/I9）。
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
    parameters_dump(world,out);
    engineering_dump_versions(world,out);
    for (size_t i = 0; i < world->boundary_count; ++i) {
        const SpaceBoundarySurface *b = &world->boundaries[i];

        fprintf(out, "boundary %u outline ", (unsigned)b->id);
        dump_loop(out, &b->outline);

        if (b->kind != BOUNDARY_UNSPECIFIED) {
            fprintf(out, " kind %s", b->kind == BOUNDARY_ROOM_PLAN
                    ? "room_plan" : "wall_elevation");
        }

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

    for (size_t i = 0; i < world->spec_count; ++i)
        fprintf(out, "spec %s %lld\n", world->specs[i].name, (long long)world->specs[i].value);

    boundary_keys_dump(world,out);
    if(grid_subdivision_used(world)) fputs("requires " GRID_SUBDIVISION_CAPABILITY "\n",out);
    grid_systems_dump(world,out);
    grid_bindings_dump(world,out);
    engineering_dump_applications(world,out);
    for (size_t i = 0; i < world->grid_count; ++i) {
        const ReferenceGrid *g = &world->grids[i];

        if (g->is_subgrid) continue;
        if (g->from_binding) {
            fprintf(out,"grid %u on %u from-binding %u\n",g->id,g->placement_id,g->binding_id); continue;
        }
        if (g->from_system) {
            fprintf(out,"grid %u on %u from-system %u origin %lld %lld\n",g->id,g->placement_id,g->system_id,
                (long long)g->system_origin[0],(long long)g->system_origin[1]);
            continue;
        }
        if (engineering_dump_grid(world,g,out)) continue;

        bool main_along_dumped = false;
        for (int pass = 0; pass < 2; ++pass) {
            /* 重放時先宣告主支方向所需的來源軸。 */
            int a = g->main_along == 1 ? 1 - pass : pass;
            const GridAxisDef *def = &g->axis[a];

            if (def->source == GRID_SRC_NONE) {
                continue;
            }

            fprintf(out, "grid %u on %u", (unsigned)g->id,
                    (unsigned)g->placement_id);
            if (!main_along_dumped && g->main_along != 0) {
                fprintf(out, " main-along %c", g->main_along == 1 ? 'u' : 'v');
                main_along_dumped = true;
            }
            fprintf(out, " %c", a == 0 ? 'u' : 'v');

            /* 只存來源就只 dump 來源（R4：重放逐字相同）。 */
            if (def->source == GRID_SRC_SERIES) {
                fprintf(out, " series %lld %lld %u",
                        (long long)def->start, (long long)def->step,
                        (unsigned)def->series_count);
            } else if (def->source == GRID_SRC_PANEL) {
                /* 起算點已具體化進定義（D10a），一律輸出——
                 * 省略它的話，承載面事後縮小時重放會取到不同的 a。 */
                fprintf(out, " panel %lld gap %lld from %lld",
                        (long long)def->panel, (long long)def->gap,
                        (long long)def->anchor);
            } else {
                for (size_t k = 0; k < def->count; ++k) {
                    fprintf(out, " %lld", (long long)def->coords[k]);
                }
            }

            fputc('\n', out);
        }
    }

    for (size_t i=0;i<world->grid_count;++i) {
        const ReferenceGrid *g=&world->grids[i];
        if (!g->is_subgrid) continue;
        if(g->lattice_cell){
            fprintf(out,"subgrid %u parent %u lattice-cell %lld %lld divisions u %u v %u\n",g->id,g->parent_id,
                (long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1],g->divisions[0],g->divisions[1]);continue;
        }
        char refs[2][2][32];
        for (int a=0;a<2;++a) for (int k=0;k<2;++k) grid_cell_ref_format(g->cell_ref[a][k],refs[a][k],sizeof refs[a][k]);
        fprintf(out,"subgrid %u parent %u cell u %s %s v %s %s divisions u %u v %u\n",
            g->id,g->parent_id,refs[0][0],refs[0][1],refs[1][0],refs[1][1],g->divisions[0],g->divisions[1]);
    }
    if(world->assembly.instance_count)fputs("requires assembly-timber-generation/1\n",out);
    reference_dump(world, out);

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
                    (long long)(b->y_lo + (b->y_hi - b->y_lo) / 2));
        } else {
            fprintf(out, "along y from %lld to %lld at %lld",
                    (long long)b->y_lo, (long long)b->y_hi,
                    (long long)(b->x_lo + (b->x_hi - b->x_lo) / 2));
        }
        fprintf(out, " width %lld depth %lld top %lld\n",
                (long long)(b->axis == 0 ? b->y_hi - b->y_lo
                                         : b->x_hi - b->x_lo),
                (long long)(b->z_hi - b->z_lo),
                (long long)b->z_hi);
    }

    assembly_dump(world,out);
    sp_dump(world,out);
    /* 畫布座標最後寫：它引用的物件要先存在。 */
    for (size_t i = 0; i < world->canvas_pos_count; ++i) {
        const CanvasPos *p = &world->canvas_pos[i];

        fprintf(out, "canvas-pos %s %u %lld %lld\n",
                p->kind == CANVAS_POS_BOUNDARY  ? "boundary"  :
                p->kind == CANVAS_POS_PLACEMENT ? "placement" :
                p->kind == CANVAS_POS_SPACE     ? "space"     :
                p->kind == CANVAS_POS_COLUMN    ? "column"    :
                p->kind == CANVAS_POS_ASSEMBLY_RULE ? "assembly-rule" : p->kind == CANVAS_POS_ASSEMBLY_BINDING ? "assembly-binding" : p->kind == CANVAS_POS_PARAMETER ? "parameter" : p->kind == CANVAS_POS_GRID_BINDING ? "grid-binding" : p->kind == CANVAS_POS_GRID_SYSTEM ? "grid-system" : "beam",
                (unsigned)p->id, (long long)p->x, (long long)p->y);
    }
}

/*
 * canvas-pos：設定物件在無限畫布上的擺放位置。
 * 純展示中繼資料：只要求目標存在，不做幾何驗證；
 * 同 (kind,id) 再宣告 = 移動卡片。
 */
/* 公理 I14：canvas-pos 只要求 (類別,id) 指的物件存在，不觸發幾何重驗。 */
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
    } else if (strcmp(tokens[1], "assembly-rule") == 0) {
        kind = CANVAS_POS_ASSEMBLY_RULE;
    } else if (strcmp(tokens[1], "assembly-binding") == 0) {
        kind = CANVAS_POS_ASSEMBLY_BINDING;
    } else if (strcmp(tokens[1], "parameter") == 0) {
        kind = CANVAS_POS_PARAMETER;
    } else if (strcmp(tokens[1], "grid-system") == 0) {
        kind = CANVAS_POS_GRID_SYSTEM;
    } else if (strcmp(tokens[1], "grid-binding") == 0) {
        kind = CANVAS_POS_GRID_BINDING;
    } else {
        scene_error(path, line_no,
            "canvas-pos 的類別要是 boundary / placement / space / column / beam / grid-system");
        return false;
    }

    uint32_t id;
    Coord x, y;

    if (!parse_u32(tokens[2], &id) ||
        !parse_coord(tokens[3], &x) ||
        !parse_coord(tokens[4], &y)) {
        scene_error(path, line_no, "canvas-pos 的 id / x / y 要是整數");
        return false;
    }

    /* 畫布座標引用的是世界裡的實體，目標必須存在。 */
    bool exists =
        kind == CANVAS_POS_BOUNDARY  ? world_find_boundary(world, id)  != NULL :
        kind == CANVAS_POS_PLACEMENT ? world_find_placement(world, id) != NULL :
        kind == CANVAS_POS_SPACE     ? world_find_space(world, id)     != NULL :
        kind == CANVAS_POS_COLUMN    ? world_find_column(world, id)    != NULL :
        kind == CANVAS_POS_GRID_BINDING ? world_find_grid_binding(world,id) != NULL :
        kind == CANVAS_POS_ASSEMBLY_RULE ? assembly_rule(world,id,0) != NULL :
        kind == CANVAS_POS_ASSEMBLY_BINDING ? assembly_binding(world,id) != NULL :
        kind == CANVAS_POS_PARAMETER ? parameter_find(world,id) != NULL :
        kind == CANVAS_POS_GRID_SYSTEM ? world_find_grid_system(world,id) != NULL :
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
    { "grid-binding", 15, SCENE_MAX_TOKENS, false, "grid-binding id on-boundary id from-system id vertex-key key cell i j anchor nu du nv dv", apply_grid_binding_line },
    { "boundary-vertex-keys", 7, SCENE_MAX_TOKENS, false, "boundary-vertex-keys id outer keys [hole keys] next-key n", apply_boundary_keys_line },
    { "boundary-keyed", 9, SCENE_MAX_TOKENS, false, "boundary-keyed id geometry-hash hash outline key:u,v ...", apply_boundary_keyed_line },
    { "grid-source-rule", 4, 16, false, "grid-source-rule SID create|key K name-hex HEX selector all-cells|cell I J divide U V", apply_grid_source_rule },
    { "grid-source-rule-highwater", 4, 4, false, "grid-source-rule-highwater SID next K|exhausted (file only)", apply_grid_source_rule_highwater },
    { "grid-system", 10, SCENE_MAX_TOKENS, false, "grid-system id name-hex utf8hex main-along u|v|none u definition v definition", apply_grid_system_line },
    { "owned", 5, 20, false, "owned timber|place instance member native-arguments", apply_assembly_owned_line },
    { "section-profile", 3, 3, false, "section-profile profile|member|run base64-json (atomic scene only)", apply_section_profile_line },
    { "assembly", 2, 3, false, "assembly begin|record|data|commit|end", apply_assembly_line },
    { "parameters", 2, 3, false, "parameters begin|card|field|end", apply_parameters_line },
    { "requires", 2, 2, false, "requires engineering-spec/1", apply_requires_line },
    { "engineering", 3, 3, false, "engineering kind base64-json", apply_engineering_line },
    { "subgrid", 12, 16, true, "subgrid id parent id cell u lo hi v lo hi divisions u n v n", apply_subgrid_line },
    { "spec", 3, 3, false, "spec 名稱 整數mm", apply_spec_line },
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
        "datum", 4, SCENE_MAX_TOKENS, false,
        "datum id x|y|z spec-only position expression",
        apply_datum_line
    },
    {
        "guide", 5, SCENE_MAX_TOKENS, true,
        "guide id 承載面id u|v 位置引用式 或 guide id 承載面id datum 基準id",
        apply_guide_line
    },
    {
        "grid", 6, SCENE_MAX_TOKENS, true,
        "grid id on 承載面id "
        "u 座標...｜series 起點 間距 條數｜panel 面材寬 gap 縫寬 [from 起算點] "
        "[v 同上]",
        apply_grid_line
    },
    {
        "timber", 4, 9, false,
        "timber id A尺寸 B尺寸 "
        "role boundary|primary|secondary|custom [priority N]",
        apply_timber_line
    },
    {
        "place", 8, 20, true,
        "place 角材id on 承載面id at-line guide 線id｜grid 網id u|v 索引 "
        "或 at-face e索引｜h孔e邊｜t角材，"
        "可加 through 座標 或 between 擋面 擋面）",
        apply_place_line
    },
    {
        "span-auto", 2, 2, true,
        "span-auto 已廢除，請重新以 at-line/at-face 定義",
        apply_span_auto_line
    },
    {
        "move", 3, SCENE_MAX_TOKENS, true,
        "move 參考線id 新位置引用式",
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
        "apply-proj", 3, 36, false,
        "apply-proj 邊界面id 項目id… [cut-strip]",
        apply_applyproj_line
    },
    {
        "delete", 3, 3, false,
        "delete boundary|placement|guide|grid|grid-system|timber|space|column|beam id",
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

static bool apply_scene_line_unchecked(const char *path, int line_no, char *tokens[], int count, World *world)
{
    g_coord_range_error = false;
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

        bool ok = SCENE_COMMANDS[i].apply(path, line_no, tokens, count, world);
        if (g_coord_range_error) {
            scene_error(path, line_no, "座標或尺寸超出支援範圍（-100000000 至 100000000 mm）");
            return false;
        }
        return ok;
    }

    scene_error(path, line_no,
        "不認得的指令（boundary placement surface space guide timber place "
        "move column beam delete reset canvas-pos）");
    return false;
}

#include "geometry-core/transactions.inc"

/*
 * 一行一筆，由上往下套用。id 要先宣告才能被引用，
 * 所以「place 寫在 timber 前面」這種錯誤自然變成「id 不存在」，不必另外規定。
 */
/* 公理 I9：DSL 順序即依賴順序——向前參照不存在的 id 自然失敗；
 * 收尾時仍有未放置角材 → 整份拒絕。 */
static bool parse_scene_file(const char *path, World *out_world)
{
    /* 二進位模式：換行自己處理，Windows 的文字模式不介入。 */
    FILE *in = fopen(path, "rb");

    if (in == NULL) {
        scene_error(path, 0, "無法開啟場景檔");
        return false;
    }

    g_parsing_scene_file = true;
    memset(g_rule_scene_highwater,0,sizeof g_rule_scene_highwater);
    g_rule_scene_required=false;
    sp_scene_required=false;
    g_rule_scene_encountered=false;
    g_parameter_scene_loading = true;

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

        if (!utf8_is_valid(line)) {
            scene_error(path, line_no,
                        "這一行含無效的 UTF-8 位元組（場景 DSL 是 UTF-8 文字）");
            ok = false;
            break;
        }

        char *text = line;

        /*
         * UTF-8 BOM 只可能出現在第一行。
         * GEO-014：先確認真的有 3 個位元組再比對——空行或 1~2 字的首行，
         * 原本會讀到 text[1]、text[2] 這兩個未初始化的位元組。
         * 不是理論風險：fgets 只保證寫到終止符為止，後面的內容是上一輪留下的。
         */
        if (line_no == 1 && length >= 3 &&
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

        if (out_world->assembly.loading && strcmp(tokens[0],"assembly")) {
            scene_error(path,line_no,"I41: assembly blocks may only contain assembly records"); ok=false; break;
        }
        if (out_world->parameters.loading && strcmp(tokens[0],"parameters")) {
            scene_error(path,line_no,"I39: parameter block may only contain parameter records"); ok=false; break;
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
            /* 也要記進緩衝:bridge 的 loadfile 只拿得到緩衝,
             * 不然它回 error:""——拒絕沒有理由(GEO-174,fuzz 找到)。 */
            snprintf(g_scene_last_error, sizeof g_scene_last_error,
                     "角材 %" PRIu32 " 沒有 place（收尾時仍未放置，I9）",
                     out_world->timbers[i].id);
            ok = false;
        }
    }

    if (ok && !grid_rules_scene_integrity(out_world)) { scene_error(path,line_no,"I25a: source rule capability/highwater closure missing"); ok=false; }
    if (ok && !assembly_generation_integrity(out_world)) { scene_error(path,line_no,g_engineering_error); ok=false; }

    /* 全部擋面就位後才重驗（grid-ref / I19 / I23 都走這裡），失敗整份拒絕。 */
    if (ok && !world_revalidate(out_world)) {
        scene_error(path, line_no,
            g_revalidate_error[0] != '\0'
                ? g_revalidate_error
                : "場景收尾重驗失敗");
        ok = false;
    }

    g_parsing_scene_file = false;
    g_parameter_scene_loading = false;
    return ok;
}

/* ============================================================
 * 主程式
 * ============================================================ */

/*
 * GEO-075 下料清單：把逐支座標整理成施工用的總表——同規格加總數量。
 * 這是**報告段**，不參與任何幾何推導，也不影響公理層的任何判定。
 *
 * 刻意不用「L=」這個字樣：tests/run_tests.py 的 LEN_RE 是 r"L=(\d+)"，
 * 會把輸出裡每一個 L= 都當成一支角材的長度；清單若用它，既有 128 個測試的長度比對會被污染。
 */
typedef struct {
    Coord length;
    Coord size_a;
    Coord size_b;
    TimberRole role;
    size_t count;
    TimberId ids[WORLD_MAX_TIMBERS];
} CutGroup;

static void print_cut_list(const World *world)
{
    CutGroup groups[WORLD_MAX_TIMBERS];
    size_t group_count = 0;
    size_t placed = 0;
    Coord total_length = 0;

    for (size_t i = 0; i < world->timber_count; ++i) {
        const Timber *t = &world->timbers[i];

        /* 未放置的角材沒有推導出來的長度，不入清單（I9 收尾本來就會擋住整份場景）。 */
        if (!t->placed) {
            continue;
        }

        placed++;
        total_length += t->length;

        size_t g = 0;
        for (; g < group_count; ++g) {
            if (groups[g].length == t->length
                && groups[g].size_a == t->size_a
                && groups[g].size_b == t->size_b
                && groups[g].role == t->role) {
                break;
            }
        }

        if (g == group_count) {
            groups[g].length = t->length;
            groups[g].size_a = t->size_a;
            groups[g].size_b = t->size_b;
            groups[g].role = t->role;
            groups[g].count = 0;
            group_count++;
        }

        groups[g].ids[groups[g].count++] = t->id;
    }

    if (group_count == 0) {
        return;
    }

    /*
     * 長料先切：長度遞減，同長度再依斷面 A、斷面 B、角色排。
     * 排序是為了讓同一份場景永遠得到逐字相同的清單——清單要能拿去比對，不能每次順序不一樣。
     */
    for (size_t a = 0; a + 1 < group_count; ++a) {
        for (size_t b = a + 1; b < group_count; ++b) {
            bool swap =
                groups[b].length > groups[a].length
                || (groups[b].length == groups[a].length
                    && (groups[b].size_a < groups[a].size_a
                        || (groups[b].size_a == groups[a].size_a
                            && (groups[b].size_b < groups[a].size_b
                                || (groups[b].size_b == groups[a].size_b
                                    && groups[b].role < groups[a].role)))));

            if (swap) {
                CutGroup tmp = groups[a];
                groups[a] = groups[b];
                groups[b] = tmp;
            }
        }
    }

    printf("\n=== 下料清單 ===\n");

    for (size_t g = 0; g < group_count; ++g) {
        printf(
            "%" PRId64 "x%" PRId64 "x%" PRId64 " %s x%zu（角材 ",
            groups[g].length,
            groups[g].size_a,
            groups[g].size_b,
            timber_role_name(groups[g].role),
            groups[g].count
        );

        for (size_t k = 0; k < groups[g].count; ++k) {
            printf("%s%" PRIu32, k == 0 ? "" : "、", groups[g].ids[k]);
        }

        printf("）\n");
    }

    printf(
        "合計 %zu 支，%zu 種規格，總長 %" PRId64 " mm\n",
        placed,
        group_count,
        total_length
    );
}

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

            const char *value = argv[++i];
            char *end = NULL;
            errno = 0;
            long parsed = strtol(value, &end, 10);
            if (!value[0] || value[0] < '0' || value[0] > '9' || errno == ERANGE ||
                !end || *end || parsed < 1 || parsed > 1000000) {
                fprintf(stderr, "--bench 次數須為 1 至 1000000 的整數。\n");
                return 1;
            }
            bench_iters = (int)parsed;
            open_window = false;
        } else if (strcmp(argv[i], "--help") == 0) {
            printf("用法：%s [--no-window] [--scene 路徑] [--out 路徑] [--bench N] [--help]\n"
                   "  --no-window  不開啟視窗\n"
                   "  --scene 路徑  載入場景檔\n"
                   "  --out 路徑    SVG 輸出路徑\n"
                   "  --bench N     GDI 測試次數，1..1000000（Windows）\n"
                   "  --help        顯示用法，不建立輸出\n", argv[0]);
            return 0;
        } else {
            fprintf(stderr, "不認得的參數：%s；請用 --help 查看用法。\n", argv[i]);
            return 1;
        }
    }

    World world = { 0 };

    if (scene_path != NULL) {
        if (!parse_scene_file(scene_path, &world)) {
            return 1;
        }
    } else {
        if (!reference_default_world(&world)) return 1;
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

        /*
         * GEO-075 房間內部尺寸 + GEO-043 體積與質心。
         * 只印兩側槽位都有面的軸；推不出來的軸不猜、不補預設（R3）。
         */
        Coord span[3] = { 0, 0, 0 };
        Coord mid[3] = { 0, 0, 0 };
        bool span_known[3] = { false, false, false };

        for (int axis = 0; axis < 3; ++axis) {
            Coord lo = 0;
            Coord hi = 0;

            if (!space_axis_bound(&world, space, axis, 0, &lo)
                || !space_axis_bound(&world, space, axis, 1, &hi)) {
                continue;
            }

            span[axis] = hi > lo ? hi - lo : lo - hi;
            mid[axis] = coord_midpoint_floor(lo, hi);
            span_known[axis] = true;

            printf(
                "內部尺寸 %c：%" PRId64 " mm\n",
                axis == 0 ? 'X' : axis == 1 ? 'Y' : 'Z',
                span[axis]
            );
        }

        /* 三軸都釘住才有體積與質心可言；缺一軸就不是一個有界的盒子。 */
        if (span_known[0] && span_known[1] && span_known[2]) {
            /*
             * I33 的紀律：寧可說算不出來，也不印一個回繞過的數字。
             * D1 允許到 ±100km，三軸相乘確實可能超出 int64。
             */
            if (span[1] != 0 && span[2] != 0
                && span[0] > INT64_MAX / span[1] / span[2]) {
                printf("內部體積：超出 int64 可表示範圍，不印（避免回繞成錯值）\n");
            } else {
                Coord volume = span[0] * span[1] * span[2];

                printf(
                    "內部體積：%" PRId64 " mm³（%.3f m³）\n",
                    volume,
                    (double)volume / 1e9
                );
            }

            printf("內部質心：");
            print_point3((Point3){ mid[0], mid[1], mid[2] });
            printf("\n");
        }
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

    print_cut_list(&world);


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
