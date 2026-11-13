#include "supports.h"

bool wood_stop_matches_ref(const WoodStopFace *f, const WoodStopRef *r)
{
    if (f == NULL || r == NULL) {
        return false;
    }

    if (r->kind == 1) {
        return f->kind == WOOD_STOP_MEMBER_SIDE && f->timber_id == r->timber;
    }

    if (r->hole < 0) {
        return f->kind == WOOD_STOP_OUTLINE_EDGE && f->edge_index == r->edge;
    }

    return f->kind == WOOD_STOP_HOLE_EDGE &&
           f->hole_index == r->hole && f->edge_index == r->edge;
}

size_t wood_stop_ref_candidates(
    const WoodStopFace faces[],
    size_t face_count,
    const WoodStopRef *r,
    GeoCoord cross_lo,
    GeoCoord cross_hi,
    const WoodStopFace *out[],
    size_t out_cap,
    bool *saw_free,
    bool *saw_narrow
)
{
    size_t n = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const WoodStopFace *f = &faces[i];

        if (!wood_stop_matches_ref(f, r)) {
            continue;
        }

        if (f->lo > cross_lo || f->hi < cross_hi) {
            *saw_narrow = true;
            continue;
        }

        if (f->fixity == WOOD_STOP_FREE) {
            *saw_free = true;
            continue;
        }

        if (n < out_cap) {
            out[n++] = f;
        }
    }

    return n;
}

bool wood_stop_shadowed(const WoodStopFace faces[], size_t i, GeoCoord lo, GeoCoord hi)
{
    if (faces[i].kind != WOOD_STOP_MEMBER_SIDE) return false;
    for (size_t j = 0; j < i; ++j)
        if (faces[j].fixed == faces[i].fixed && faces[j].lo <= lo && faces[j].hi >= hi) return true;
    return false;
}

size_t wood_stop_pick(
    const WoodStopFace faces[],
    size_t face_count,
    GeoCoord at,
    GeoCoord lo,
    GeoCoord hi,
    const WoodStopFace **out_face
)
{
    const WoodStopFace *found = NULL;
    size_t hits = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const WoodStopFace *f = &faces[i];

        if (f->fixed != at || f->lo > lo || f->hi < hi || wood_stop_shadowed(faces, i, lo, hi)) {
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

size_t wood_stop_count_legal(
    const WoodStopFace faces[],
    size_t face_count,
    GeoCoord at,
    GeoCoord lo,
    GeoCoord hi
)
{
    size_t hits = 0;

    for (size_t i = 0; i < face_count; ++i) {
        const WoodStopFace *f = &faces[i];

        if (f->fixed == at && f->lo <= lo && f->hi >= hi &&
            f->fixity != WOOD_STOP_FREE && !wood_stop_shadowed(faces, i, lo, hi)) {
            ++hits;
        }
    }

    return hits;
}

static GeoCoord wood_support_min(GeoCoord a, GeoCoord b) { return a < b ? a : b; }
static GeoCoord wood_support_max(GeoCoord a, GeoCoord b) { return a > b ? a : b; }

bool wood_member_boundary_props(
    const GeoLoop2View *outline,
    bool along_v,
    GeoCoord span_lo,
    GeoCoord span_hi,
    GeoCoord cross_lo,
    GeoCoord cross_hi,
    bool *out_on_boundary,
    bool *out_covers_edge,
    int *out_boundary_edge
)
{
    int best = -1;
    bool best_covers = false;
    GeoCoord best_overlap = 0;
    size_t i;

    *out_on_boundary = false;
    *out_covers_edge = false;
    *out_boundary_edge = -1;

    if (outline == NULL) {
        return false;
    }

    for (i = 0; i < outline->count; ++i) {
        GeoSegment2 seg;
        bool edge_along_v, covers;
        GeoCoord edge_fixed, edge_lo, edge_hi, ov;

        seg.start = outline->v[i];
        seg.end = outline->v[(i + 1) % outline->count];

        edge_along_v = seg.start.u == seg.end.u;
        if (edge_along_v != along_v) {
            continue;
        }

        edge_fixed = edge_along_v ? seg.start.u : seg.start.v;
        if (edge_fixed != cross_lo && edge_fixed != cross_hi) {
            continue;
        }

        edge_lo = edge_along_v ? wood_support_min(seg.start.v, seg.end.v)
                               : wood_support_min(seg.start.u, seg.end.u);
        edge_hi = edge_along_v ? wood_support_max(seg.start.v, seg.end.v)
                               : wood_support_max(seg.start.u, seg.end.u);

        ov = wood_support_min(span_hi, edge_hi) - wood_support_max(span_lo, edge_lo);
        if (ov <= 0) {
            continue;
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
