#ifndef GEOMETRY_KERNEL_GEOMETRY_IMPLEMENTATION
#define GEOMETRY_KERNEL_GEOMETRY_IMPLEMENTATION
#include "geometry.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>
static GeoCoord geo_coord_min(GeoCoord,GeoCoord);
static GeoCoord geo_coord_max(GeoCoord,GeoCoord);

bool geo_coord_in_range(GeoCoord value)
{
    return value >= -GEO_COORD_LIMIT && value <= GEO_COORD_LIMIT;
}

GeoCoord geo_vector_dot(GeoVector3 a, GeoVector3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

GeoVector3 geo_vector_cross(GeoVector3 a, GeoVector3 b)
{
    return (GeoVector3){
        .x = a.y * b.z - a.z * b.y,
        .y = a.z * b.x - a.x * b.z,
        .z = a.x * b.y - a.y * b.x
    };
}

GeoVector3 geo_vector_negate(GeoVector3 v)
{
    return (GeoVector3){
        .x = -v.x,
        .y = -v.y,
        .z = -v.z
    };
}

bool geo_vector_equal(GeoVector3 a, GeoVector3 b)
{
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

bool geo_frame_is_valid(const GeoFrame *frame)
{
    if (frame == NULL || !geo_coord_in_range(frame->origin.x) ||
        !geo_coord_in_range(frame->origin.y) || !geo_coord_in_range(frame->origin.z)) {
        return false;
    }

    /* Reject unbounded/non-cardinal axes before any multiplication. */
    const GeoVector3 axes[3]={frame->axis_u,frame->axis_v,frame->normal};
    for(size_t i=0;i<3;++i)
        if(axes[i].x < -1 || axes[i].x > 1 || axes[i].y < -1 || axes[i].y > 1 ||
           axes[i].z < -1 || axes[i].z > 1)return false;

    return geo_vector_dot(frame->axis_u, frame->axis_u) == 1 &&
           geo_vector_dot(frame->axis_v, frame->axis_v) == 1 &&
           geo_vector_dot(frame->axis_u, frame->axis_v) == 0 &&
           geo_vector_equal(
               geo_vector_cross(frame->axis_u, frame->axis_v),
               frame->normal
           );
}

bool geo_loop_is_valid(const GeoLoop2View *loop)
{
    if (loop == NULL || loop->v == NULL || loop->count < 4 ||
        loop->count > GEO_LOOP_MAX_VERTICES) {
        return false;
    }

    /* 邊的軸平行與非零長檢查。 */
    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];

        if (!geo_coord_in_range(a.u) || !geo_coord_in_range(a.v)) return false;

        bool axis_u = a.v == b.v;   /* 沿 U 方向的邊：v 座標不變 */
        bool axis_v = a.u == b.u;

        if ((!axis_u && !axis_v) || (a.u == b.u && a.v == b.v)) {
            return false;
        }
    }

    /* 非相鄰邊不得相交或共線重疊。 */
    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a1 = loop->v[i];
        GeoPoint2 a2 = loop->v[(i + 1) % loop->count];

        for (size_t j = i + 2; j < loop->count; ++j) {
            if (i == 0 && j + 1 == loop->count) {
                continue;   /* 首邊與末邊相鄰，共享頂點合法 */
            }

            GeoPoint2 b1 = loop->v[j];
            GeoPoint2 b2 = loop->v[(j + 1) % loop->count];

            /* 軸平行線段的相交/共線重疊判定。 */
            if (a1.u == a2.u && b1.u == b2.u) {
                /* 兩條直立邊。 */
                if (a1.u != b1.u) {
                    continue;
                }
                if (geo_coord_max(geo_coord_min(a1.v, a2.v), geo_coord_min(b1.v, b2.v)) <=
                    geo_coord_min(geo_coord_max(a1.v, a2.v), geo_coord_max(b1.v, b2.v))) {
                    return false;   /* 共線且區間重疊 */
                }
            } else if (a1.v == a2.v && b1.v == b2.v) {
                /* 兩條水平邊。 */
                if (a1.v != b1.v) {
                    continue;
                }
                if (geo_coord_max(geo_coord_min(a1.u, a2.u), geo_coord_min(b1.u, b2.u)) <=
                    geo_coord_min(geo_coord_max(a1.u, a2.u), geo_coord_max(b1.u, b2.u))) {
                    return false;
                }
            } else {
                /* 一橫一直：交點須嚴格同時落在兩邊內部才算相交；
                 * 端點相碰在非相鄰邊上也不允許（會形成接觸自交）。 */
                GeoPoint2 h1, h2, s1, s2;
                if (a1.v == a2.v) { h1 = a1; h2 = a2; s1 = b1; s2 = b2; }
                else              { h1 = b1; h2 = b2; s1 = a1; s2 = a2; }

                GeoCoord hu_min = geo_coord_min(h1.u, h2.u);
                GeoCoord hu_max = geo_coord_max(h1.u, h2.u);
                GeoCoord sv_min = geo_coord_min(s1.v, s2.v);
                GeoCoord sv_max = geo_coord_max(s1.v, s2.v);

                if (s1.u >= hu_min && s1.u <= hu_max &&
                    h1.v >= sv_min && h1.v <= sv_max) {
                    return false;
                }
            }
        }
    }

    /* 有向面積非零（shoelace）；順/逆時針不限，但必須有面積。 */
    GeoCoord area2 = 0;
    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];
        area2 += a.u * b.v - b.u * a.v;
    }

    return area2 != 0;
}

bool geo_loop_point_on_edge(const GeoLoop2View *loop, GeoPoint2 p)
{
    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u == b.u) {
            if (p.u == a.u &&
                p.v >= geo_coord_min(a.v, b.v) && p.v <= geo_coord_max(a.v, b.v)) {
                return true;
            }
        } else {
            if (p.v == a.v &&
                p.u >= geo_coord_min(a.u, b.u) && p.u <= geo_coord_max(a.u, b.u)) {
                return true;
            }
        }
    }

    return false;
}

bool geo_loop_contains_point(const GeoLoop2View *loop, GeoPoint2 p)
{
    if (loop == NULL) {
        return false;
    }

    if (geo_loop_point_on_edge(loop, p)) {
        return true;
    }

    int crossings = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u != b.u) {
            continue;   /* 水平邊不與水平射線交叉 */
        }

        GeoCoord v_min = geo_coord_min(a.v, b.v);
        GeoCoord v_max = geo_coord_max(a.v, b.v);

        if (p.v >= v_min && p.v < v_max && p.u < a.u) {
            ++crossings;
        }
    }

    return crossings % 2 == 1;
}

bool geo_segment_crosses_rect_interior(
    GeoPoint2 a, GeoPoint2 b,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
)
{
    if (a.u == b.u) {
        /* 直立邊：u 須嚴格在 (min_u,max_u) 內，且 v 區間與 (min_v,max_v) 有正長度交集。 */
        if (a.u <= min_u || a.u >= max_u) {
            return false;
        }
        GeoCoord lo = geo_coord_max(geo_coord_min(a.v, b.v), min_v);
        GeoCoord hi = geo_coord_min(geo_coord_max(a.v, b.v), max_v);
        return lo < hi;
    }

    if (a.v <= min_v || a.v >= max_v) {
        return false;
    }
    GeoCoord lo = geo_coord_max(geo_coord_min(a.u, b.u), min_u);
    GeoCoord hi = geo_coord_min(geo_coord_max(a.u, b.u), max_u);
    return lo < hi;
}

static bool geo_loop_rect_center_inside(
    const GeoLoop2View *loop,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
)
{
    GeoCoord cu2 = min_u + max_u;   /* 2 × 中心 u */
    GeoCoord cv2 = min_v + max_v;   /* 2 × 中心 v */
    int crossings = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];

        if (a.u == b.u) {   /* 只有直立邊會與水平射線交叉 */
            GeoCoord v_lo2 = 2 * geo_coord_min(a.v, b.v);
            GeoCoord v_hi2 = 2 * geo_coord_max(a.v, b.v);

            if (cv2 >= v_lo2 && cv2 < v_hi2 && cu2 < 2 * a.u) {
                ++crossings;
            }
        }
    }

    return (crossings & 1) != 0;
}

bool geo_loop_contains_rect(
    const GeoLoop2View *loop,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
)
{
    if (loop == NULL || min_u >= max_u || min_v >= max_v) {
        return false;
    }

    GeoPoint2 corners[4] = {
        { min_u, min_v }, { max_u, min_v },
        { max_u, max_v }, { min_u, max_v }
    };

    for (size_t i = 0; i < 4; ++i) {
        if (!geo_loop_contains_point(loop, corners[i])) {
            return false;
        }
    }

    /* 開內部要嘛全在環內、要嘛全在環外；中心在外 → 整個矩形在環外。
     * 與下面的「環邊穿入」檢查互相獨立，順序不影響結果。 */
    if (!geo_loop_rect_center_inside(loop, min_u, min_v, max_u, max_v)) {
        return false;
    }

    for (size_t i = 0; i < loop->count; ++i) {
        if (geo_segment_crosses_rect_interior(
                loop->v[i], loop->v[(i + 1) % loop->count],
                min_u, min_v, max_u, max_v)) {
            return false;
        }
    }

    return true;
}

void geo_loop_bbox(
    const GeoLoop2View *loop,
    GeoCoord *out_min_u, GeoCoord *out_min_v,
    GeoCoord *out_max_u, GeoCoord *out_max_v
)
{
    GeoCoord min_u = loop->v[0].u, max_u = loop->v[0].u;
    GeoCoord min_v = loop->v[0].v, max_v = loop->v[0].v;

    for (size_t i = 1; i < loop->count; ++i) {
        min_u = geo_coord_min(min_u, loop->v[i].u);
        max_u = geo_coord_max(max_u, loop->v[i].u);
        min_v = geo_coord_min(min_v, loop->v[i].v);
        max_v = geo_coord_max(max_v, loop->v[i].v);
    }

    *out_min_u = min_u;
    *out_min_v = min_v;
    *out_max_u = max_u;
    *out_max_v = max_v;
}

GeoGeometryStatus geo_loop_clip_line(
    const GeoLoop2View *loop,
    bool along_u,
    GeoCoord offset,
    GeoSegment2 out[],
    size_t out_cap,
    size_t *out_count
)
{
    if(out_count)*out_count=0;
    if(!loop||!loop->v||loop->count>GEO_LOOP_MAX_VERTICES||!out_count||(!out&&out_cap))return GEO_GEOMETRY_INVALID;
    GeoCoord crossings[GEO_LOOP_MAX_VERTICES];
    size_t crossing_count = 0;

    for (size_t i = 0; i < loop->count; ++i) {
        GeoPoint2 a = loop->v[i];
        GeoPoint2 b = loop->v[(i + 1) % loop->count];

        if (along_u) {
            /* 直線 v=offset 只與直立邊（a.u == b.u）相交；
             * 水平邊（a.v == b.v）與它平行，跳過。 */
            if (a.v == b.v) {
                continue;
            }
            GeoCoord v_min = geo_coord_min(a.v, b.v);
            GeoCoord v_max = geo_coord_max(a.v, b.v);
            if (offset >= v_min && offset < v_max) {
                crossings[crossing_count++] = a.u;
            }
        } else {
            /* 直線 u=offset 只與水平邊（a.v == b.v）相交；
             * 直立邊與它平行，跳過。 */
            if (a.u == b.u) {
                continue;
            }
            GeoCoord u_min = geo_coord_min(a.u, b.u);
            GeoCoord u_max = geo_coord_max(a.u, b.u);
            if (offset >= u_min && offset < u_max) {
                crossings[crossing_count++] = a.v;
            }
        }
    }

    /* 插入排序交點；頂點處的相鄰兩邊只會貢獻一個交點（半開區間），
     * 但水平邊端點與直立邊可能給出重複交點——去重。 */
    for (size_t i = 1; i < crossing_count; ++i) {
        GeoCoord key = crossings[i];
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
    if(crossing_count/2>out_cap)return GEO_GEOMETRY_CAPACITY;
    size_t seg_count = 0;
    for (size_t i = 0; i + 1 < crossing_count && seg_count < out_cap; i += 2) {
        GeoCoord lo = crossings[i];
        GeoCoord hi = crossings[i + 1];

        if (along_u) {
            out[seg_count].start = (GeoPoint2){ lo, offset };
            out[seg_count].end   = (GeoPoint2){ hi, offset };
        } else {
            out[seg_count].start = (GeoPoint2){ offset, lo };
            out[seg_count].end   = (GeoPoint2){ offset, hi };
        }
        ++seg_count;
    }

    *out_count=seg_count;return GEO_GEOMETRY_OK;
}

bool geo_region_is_valid(const GeoRegionView *b)
{
    if (b == NULL || b->hole_count > GEO_REGION_MAX_HOLES ||
        (b->hole_count && !b->holes) || !geo_loop_is_valid(&b->outline)) {
        return false;
    }

    /* Pairwise tests below may inspect a later hole. Validate every borrowed
     * loop first so the validation entry point also accepts malformed input
     * safely, without assuming its producer already checked the views. */
    for(size_t h=0;h<b->hole_count;++h)if(!geo_loop_is_valid(&b->holes[h]))return false;

    for (size_t h = 0; h < b->hole_count; ++h) {
        const GeoLoop2View *hole = &b->holes[h];

        if (!geo_loop_is_valid(hole)) {
            return false;
        }

        /* 孔的每個頂點必須在外輪廓內（不含外輪廓邊上），
         * 且孔的每條邊不得穿外輪廓。 */
        for (size_t i = 0; i < hole->count; ++i) {
            GeoPoint2 p = hole->v[i];

            if (geo_loop_point_on_edge(&b->outline, p) ||
                !geo_loop_contains_point(&b->outline, p)) {
                return false;
            }
        }

        for (size_t i = 0; i < hole->count; ++i) {
            GeoPoint2 a = hole->v[i];
            GeoPoint2 c = hole->v[(i + 1) % hole->count];

            for (size_t j = 0; j < b->outline.count; ++j) {
                GeoPoint2 d = b->outline.v[j];
                GeoPoint2 e = b->outline.v[(j + 1) % b->outline.count];

                /* 孔邊與外輪廓邊不得相交（含共線）。 */
                if (a.u == c.u && d.u == e.u) {
                    if (a.u == d.u &&
                        geo_coord_max(geo_coord_min(a.v, c.v), geo_coord_min(d.v, e.v)) <
                        geo_coord_min(geo_coord_max(a.v, c.v), geo_coord_max(d.v, e.v))) {
                        return false;
                    }
                } else if (a.v == c.v && d.v == e.v) {
                    if (a.v == d.v &&
                        geo_coord_max(geo_coord_min(a.u, c.u), geo_coord_min(d.u, e.u)) <
                        geo_coord_min(geo_coord_max(a.u, c.u), geo_coord_max(d.u, e.u))) {
                        return false;
                    }
                } else {
                    GeoPoint2 h1, h2, s1, s2;
                    if (a.v == c.v) { h1 = a; h2 = c; s1 = d; s2 = e; }
                    else            { h1 = d; h2 = e; s1 = a; s2 = c; }

                    if (s1.u > geo_coord_min(h1.u, h2.u) &&
                        s1.u < geo_coord_max(h1.u, h2.u) &&
                        h1.v > geo_coord_min(s1.v, s2.v) &&
                        h1.v < geo_coord_max(s1.v, s2.v)) {
                        return false;
                    }
                }
            }
        }

        /* 孔互不重疊：任一孔頂點落在別孔內，或邊互相穿越，即拒絕。 */
        for (size_t k = h + 1; k < b->hole_count; ++k) {
            const GeoLoop2View *other = &b->holes[k];

            for (size_t i = 0; i < hole->count; ++i) {
                if (geo_loop_contains_point(other, hole->v[i])) {
                    return false;
                }
            }
            for (size_t i = 0; i < other->count; ++i) {
                if (geo_loop_contains_point(hole, other->v[i])) {
                    return false;
                }
            }
        }
    }

    return true;
}

bool geo_region_contains_point(
    const GeoRegionView *b,
    GeoPoint2 p
)
{
    if (b == NULL || !geo_loop_contains_point(&b->outline, p)) {
        return false;
    }

    for (size_t h = 0; h < b->hole_count; ++h) {
        const GeoLoop2View *hole = &b->holes[h];

        if (geo_loop_contains_point(hole, p) &&
            !geo_loop_point_on_edge(hole, p)) {
            return false;
        }
    }

    return true;
}

bool geo_region_contains_rect(
    const GeoRegionView *b,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
)
{
    if (b == NULL ||
        !geo_loop_contains_rect(&b->outline, min_u, min_v, max_u, max_v)) {
        return false;
    }

    for (size_t h = 0; h < b->hole_count; ++h) {
        const GeoLoop2View *hole = &b->holes[h];
        GeoCoord h_min_u, h_min_v, h_max_u, h_max_v;
        geo_loop_bbox(hole, &h_min_u, &h_min_v, &h_max_u, &h_max_v);

        /* 矩形與孔 bbox 無交集 → 快退。 */
        if (h_max_u <= min_u || h_min_u >= max_u ||
            h_max_v <= min_v || h_min_v >= max_v) {
            continue;
        }

        /* 任一孔頂點嚴格在矩形內 → 相交。 */
        for (size_t i = 0; i < hole->count; ++i) {
            GeoPoint2 p = hole->v[i];
            if (p.u > min_u && p.u < max_u &&
                p.v > min_v && p.v < max_v) {
                return false;
            }
        }

        /* 任一孔邊穿過矩形內部 → 相交。 */
        for (size_t i = 0; i < hole->count; ++i) {
            if (geo_segment_crosses_rect_interior(
                    hole->v[i], hole->v[(i + 1) % hole->count],
                    min_u, min_v, max_u, max_v)) {
                return false;
            }
        }

        /* 孔整個罩住矩形（矩形四角都在孔內）。 */
        if (geo_loop_contains_point(hole, (GeoPoint2){ min_u + 1, min_v + 1 }) &&
            !geo_loop_point_on_edge(hole, (GeoPoint2){ min_u + 1, min_v + 1 })) {
            /* min+1 只是代表點：四角嚴格在孔內才算罩住。
             * 用四角逐一判定較穩。 */
            GeoPoint2 corners[4] = {
                { min_u, min_v }, { max_u, min_v },
                { max_u, max_v }, { min_u, max_v }
            };
            size_t inside = 0;
            for (size_t i = 0; i < 4; ++i) {
                if (geo_loop_contains_point(hole, corners[i])) {
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

static GeoCoord geo_coord_min(GeoCoord a, GeoCoord b) { return a < b ? a : b; }

static GeoCoord geo_coord_max(GeoCoord a, GeoCoord b) { return a > b ? a : b; }

GeoPoint3 geo_frame_point(const GeoFrame *frame,GeoCoord u,GeoCoord v,GeoCoord w)
{
    return (GeoPoint3){frame->origin.x+u*frame->axis_u.x+v*frame->axis_v.x+w*frame->normal.x,
        frame->origin.y+u*frame->axis_u.y+v*frame->axis_v.y+w*frame->normal.y,
        frame->origin.z+u*frame->axis_u.z+v*frame->axis_v.z+w*frame->normal.z};
}
GeoVector3 geo_frame_direction(const GeoFrame *frame,GeoDirection2 direction)
{
    switch(direction){
    case GEO_DIRECTION_POS_U:return frame->axis_u;
    case GEO_DIRECTION_NEG_U:return geo_vector_negate(frame->axis_u);
    case GEO_DIRECTION_POS_V:return frame->axis_v;
    case GEO_DIRECTION_NEG_V:return geo_vector_negate(frame->axis_v);
    default:return (GeoVector3){0,0,0};
    }
}
GeoPoint2 geo_frame_project_uv(const GeoFrame *frame,GeoPoint3 point)
{
    GeoVector3 d={point.x-frame->origin.x,point.y-frame->origin.y,point.z-frame->origin.z};
    return (GeoPoint2){geo_vector_dot(d,frame->axis_u),geo_vector_dot(d,frame->axis_v)};
}
GeoRect2 geo_rectangle_footprint(const GeoFrame *frame,GeoPoint2 anchor,
    GeoVector3 along,GeoVector3 across,GeoCoord extent_along,GeoCoord extent_across)
{
    GeoPoint2 far_pt={anchor.u+extent_along*geo_vector_dot(along,frame->axis_u)+extent_across*geo_vector_dot(across,frame->axis_u),
        anchor.v+extent_along*geo_vector_dot(along,frame->axis_v)+extent_across*geo_vector_dot(across,frame->axis_v)};
    return (GeoRect2){geo_coord_min(anchor.u,far_pt.u),geo_coord_min(anchor.v,far_pt.v),geo_coord_max(anchor.u,far_pt.u),geo_coord_max(anchor.v,far_pt.v)};
}
bool geo_rect_overlap_positive(const GeoRect2 *a,const GeoRect2 *b)
{
    return geo_coord_min(a->max_u,b->max_u)>geo_coord_max(a->min_u,b->min_u)&&
        geo_coord_min(a->max_v,b->max_v)>geo_coord_max(a->min_v,b->min_v);
}
bool geo_box_face(const GeoBox3 *box,unsigned axis,unsigned side,GeoQuad3 *out)
{
    static const unsigned char walk[2][4][2]={{{0,0},{0,1},{1,1},{1,0}},{{0,0},{1,0},{1,1},{0,1}}};
    unsigned u,w;
    if(!box||!out||axis>2||side>1)return false;
    u=(axis+1)%3;w=(axis+2)%3;
    for(size_t i=0;i<4;++i){
        GeoCoord local[3]={0,0,0};local[axis]=side?box->extent[axis]:0;
        local[u]=walk[side][i][0]?box->extent[u]:0;local[w]=walk[side][i][1]?box->extent[w]:0;
        out->vertices[i]=geo_frame_point(&box->frame,local[0],local[1],local[2]);
    }
    return true;
}
GeoRect2 geo_aabb_project_uv(const GeoFrame *frame,GeoPoint3 low,GeoPoint3 high)
{
    GeoRect2 result={INT64_MAX,INT64_MAX,INT64_MIN,INT64_MIN};
    for(unsigned i=0;i<8;++i){
        GeoPoint3 corner={(i&1)?high.x:low.x,(i&2)?high.y:low.y,(i&4)?high.z:low.z};
        GeoPoint2 point=geo_frame_project_uv(frame,corner);
        result.min_u=geo_coord_min(result.min_u,point.u);result.max_u=geo_coord_max(result.max_u,point.u);
        result.min_v=geo_coord_min(result.min_v,point.v);result.max_v=geo_coord_max(result.max_v,point.v);
    }
    return result;
}
bool geo_region_set_contains_rect(const GeoRegionSetView *domain,const GeoRect2 *rect)
{
    for(size_t i=0;i<domain->count;++i)
        if(geo_region_contains_rect(&domain->regions[i],rect->min_u,rect->min_v,rect->max_u,rect->max_v))return true;
    return false;
}
GeoGeometryStatus geo_strip_intervals(const GeoRegionSetView *domain,bool along_v,GeoInterval cross,
    const GeoRect2 *obstacles,size_t obstacle_count,GeoIntervalBuffer *out,GeoStripScratch scratch)
{
    size_t count=0,unique=0;bool open=false;GeoCoord *cuts=scratch.cuts;
    if(!domain||(!domain->regions&&domain->count)||!out||(!out->items&&out->capacity)||
       !cuts||(!obstacles&&obstacle_count)||cross.start>=cross.end)return GEO_GEOMETRY_INVALID;
    out->count=0;
    for(size_t c=0;c<domain->count;++c){
        const GeoRegionView *region=&domain->regions[c];
        for(size_t h=0;h<=region->hole_count;++h){
            const GeoLoop2View *loop=h?&region->holes[h-1]:&region->outline;
            if(loop->count>scratch.capacity-count)return GEO_GEOMETRY_CAPACITY;
            for(size_t i=0;i<loop->count;++i)cuts[count++]=along_v?loop->v[i].v:loop->v[i].u;
        }
    }
    for(size_t i=0;i<obstacle_count;++i){
        if(scratch.capacity-count<2)return GEO_GEOMETRY_CAPACITY;
        cuts[count++]=along_v?obstacles[i].min_v:obstacles[i].min_u;
        cuts[count++]=along_v?obstacles[i].max_v:obstacles[i].max_u;
    }
    for(size_t i=1;i<count;++i){GeoCoord key=cuts[i];size_t j=i;while(j>0&&cuts[j-1]>key){cuts[j]=cuts[j-1];--j;}cuts[j]=key;}
    for(size_t i=0;i<count;++i)if(!unique||cuts[i]!=cuts[unique-1])cuts[unique++]=cuts[i];
    for(size_t i=0;i+1<unique;++i){
        GeoCoord lo=cuts[i],hi=cuts[i+1];bool ok;
        GeoRect2 cell=along_v?(GeoRect2){cross.start,lo,cross.end,hi}:(GeoRect2){lo,cross.start,hi,cross.end};
        if(lo>=hi)continue;
        ok=geo_region_set_contains_rect(domain,&cell);
        for(size_t k=0;ok&&k<obstacle_count;++k)if(geo_rect_overlap_positive(&cell,&obstacles[k]))ok=false;
        if(ok&&!open){
            if(out->count>=out->capacity){out->count=0;return GEO_GEOMETRY_CAPACITY;}
            out->items[out->count]=(GeoInterval){lo,hi};open=true;
        }else if(ok)out->items[out->count].end=hi;
        else if(open){++out->count;open=false;}
    }
    if(open)++out->count;
    return GEO_GEOMETRY_OK;
}
GeoGeometryStatus geo_loop_rect_area2(const GeoLoop2View *loop,const GeoRect2 *r,GeoCoord *out)
{
    if(!loop||!loop->v||loop->count>GEO_LOOP_MAX_VERTICES||!r||!out)return GEO_GEOMETRY_INVALID;
    GeoPoint2 a[GEO_LOOP_MAX_VERTICES * 4], z[GEO_LOOP_MAX_VERTICES * 4];
    size_t n=loop->count;
    memcpy(a,loop->v,n*sizeof *a);
    for (int side=0;side<4 && n;++side) {
        int axis=side/2; bool low=(side%2)==0;
        GeoCoord bound=axis==0?(low?r->min_u:r->max_u):(low?r->min_v:r->max_v);
        size_t m=0;
        for (size_t i=0;i<n;++i) {
            GeoPoint2 p=a[i], q=a[(i+1)%n];
            GeoCoord pc=axis==0?p.u:p.v, qc=axis==0?q.u:q.v;
            bool pin=low?pc>=bound:pc<=bound, qin=low?qc>=bound:qc<=bound;
            if (pin != qin) {
                GeoPoint2 hit=p;
                if (axis==0) hit.u=bound; else hit.v=bound;
                if (m>=GEO_LOOP_MAX_VERTICES*4) return GEO_GEOMETRY_CAPACITY;
                z[m++]=hit;
            }
            if (qin) {
                if (m>=GEO_LOOP_MAX_VERTICES*4) return GEO_GEOMETRY_CAPACITY;
                z[m++]=q;
            }
        }
        n=m; memcpy(a,z,n*sizeof *a);
    }
    GeoCoord area=0;
    for (size_t i=0;i<n;++i) area+=a[i].u*a[(i+1)%n].v-a[(i+1)%n].u*a[i].v;
    *out=area<0?-area:area;return GEO_GEOMETRY_OK;
}

bool geo_region_set_intersects_rect_positive(const GeoRegionSetView *domain,const GeoRect2 *rect)
{
    if(!domain||!rect||rect->min_u>=rect->max_u||rect->min_v>=rect->max_v)return false;
    for(size_t c=0;c<domain->count;++c){
        const GeoRegionView *part=&domain->regions[c];GeoCoord area;
        if(geo_loop_rect_area2(&part->outline,rect,&area)!=GEO_GEOMETRY_OK)return false;
        for(size_t h=0;h<part->hole_count;++h){GeoCoord hole;
            if(geo_loop_rect_area2(&part->holes[h],rect,&hole)!=GEO_GEOMETRY_OK)return false;
            area-=hole;
        }
        if(area>0)return true;
    }
    return false;
}
static int geo_complement_coord_compare(const void *a,const void *b)
{GeoCoord x=*(const GeoCoord*)a,y=*(const GeoCoord*)b;return (x>y)-(x<y);}
GeoGeometryStatus geo_loop_rect_complement(const GeoLoop2View *p,const GeoRect2 *r,
    GeoRect2 *out,size_t capacity,size_t *out_count)
{
    if(out_count)*out_count=0;
    if(!p||!p->v||p->count>GEO_LOOP_MAX_VERTICES||!r||!out_count||(!out&&capacity))return GEO_GEOMETRY_INVALID;
    GeoCoord ys[GEO_LOOP_MAX_VERTICES+2];size_t ny=0,n=0;ys[ny++]=r->min_v;ys[ny++]=r->max_v;
    for(size_t i=0;i<p->count;++i)if(p->v[i].v>r->min_v&&p->v[i].v<r->max_v)ys[ny++]=p->v[i].v;
    qsort(ys,ny,sizeof(GeoCoord),geo_complement_coord_compare);
    for(size_t k=1;k<ny;++k){GeoCoord lo=ys[k-1],hi=ys[k];if(lo==hi)continue;GeoCoord y2=lo+hi,xs[GEO_LOOP_MAX_VERTICES];size_t nx=0;
        for(size_t i=0;i<p->count;++i){GeoPoint2 a=p->v[i],b=p->v[(i+1)%p->count];if(a.u==b.u&&2*geo_coord_min(a.v,b.v)<y2&&y2<2*geo_coord_max(a.v,b.v))xs[nx++]=a.u;}
        qsort(xs,nx,sizeof(GeoCoord),geo_complement_coord_compare);GeoCoord cursor=r->min_u;
        for(size_t i=0;i+1<nx;i+=2){GeoCoord a=geo_coord_max(xs[i],r->min_u),b=geo_coord_min(xs[i+1],r->max_u);if(a>=b)continue;
            if(cursor<a){if(n==capacity)return GEO_GEOMETRY_CAPACITY;out[n++]=(GeoRect2){cursor,lo,a,hi};}if(b>cursor)cursor=b;}
        if(cursor<r->max_u){if(n==capacity)return GEO_GEOMETRY_CAPACITY;out[n++]=(GeoRect2){cursor,lo,r->max_u,hi};}
    }
    *out_count=n;return GEO_GEOMETRY_OK;
}

void geo_aabb_project_interval(const GeoCoord lo[3],const GeoCoord hi[3],GeoPoint3 origin,GeoVector3 axis,GeoCoord out[2])
{
    int c=axis.x?0:axis.y?1:2;GeoCoord sign=axis.x?axis.x:axis.y?axis.y:axis.z;
    GeoCoord o=c==0?origin.x:c==1?origin.y:origin.z;
    if(sign>0){out[0]=lo[c]-o;out[1]=hi[c]-o;}else{out[0]=o-hi[c];out[1]=o-lo[c];}
}

GeoCoord geo_loop_rect_intersection_area(const GeoLoop2View *p,const GeoRect2 *rect)
{
    GeoCoord u0=rect->min_u,v0=rect->min_v,u1=rect->max_u,v1=rect->max_v;
    GeoCoord ys[GEO_LOOP_MAX_VERTICES+2],xs[GEO_LOOP_MAX_VERTICES],area=0;size_t ny=0;
    ys[ny++]=v0;ys[ny++]=v1;
    for(size_t i=0;i<p->count;++i)if(p->v[i].v>v0&&p->v[i].v<v1)ys[ny++]=p->v[i].v;
    qsort(ys,ny,sizeof ys[0],geo_complement_coord_compare);
    for(size_t k=1;k<ny;++k){
        GeoCoord lo=ys[k-1],hi=ys[k],mid2=lo+hi;size_t nx=0;if(lo==hi)continue;
        for(size_t i=0;i<p->count;++i){GeoPoint2 a=p->v[i],b=p->v[(i+1)%p->count];
            if(a.u==b.u&&2*geo_coord_min(a.v,b.v)<mid2&&mid2<2*geo_coord_max(a.v,b.v))xs[nx++]=a.u;}
        qsort(xs,nx,sizeof xs[0],geo_complement_coord_compare);
        for(size_t i=0;i+1<nx;i+=2){GeoCoord a=geo_coord_max(xs[i],u0),b=geo_coord_min(xs[i+1],u1);if(a<b)area+=(b-a)*(hi-lo);}
    }
    return area;
}

bool geo_loop_touches_rect(const GeoLoop2View *p,const GeoRect2 *rect)
{
    GeoCoord u0=rect->min_u,v0=rect->min_v,u1=rect->max_u,v1=rect->max_v;
    for(size_t i=0;i<p->count;++i){GeoPoint2 a=p->v[i],b=p->v[(i+1)%p->count];
        if(geo_coord_min(a.u,b.u)<=u1&&u0<=geo_coord_max(a.u,b.u)&&geo_coord_min(a.v,b.v)<=v1&&v0<=geo_coord_max(a.v,b.v))return true;}
    return false;
}

bool geo_collinear_segment_overlap(GeoPoint2 a,GeoPoint2 b,GeoPoint2 c,GeoPoint2 d,GeoCoord *lo,GeoCoord *hi)
{
    bool vertical=a.u==b.u;if(vertical!=(c.u==d.u)||(vertical?a.u!=c.u:a.v!=c.v))return false;
    GeoCoord x=vertical?a.v:a.u,y=vertical?b.v:b.u,z=vertical?c.v:c.u,q=vertical?d.v:d.u;
    *lo=geo_coord_max(geo_coord_min(x,y),geo_coord_min(z,q));*hi=geo_coord_min(geo_coord_max(x,y),geo_coord_max(z,q));return *lo<*hi;
}
#endif
