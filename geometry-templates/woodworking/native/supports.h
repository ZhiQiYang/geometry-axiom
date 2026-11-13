/* Woodworking support selection extracted from the existing product.
 * The consumer collects the faces in their original order and owns World,
 * source resolution, placement and diagnostics. K carries geometry only. */
#ifndef GEOMETRY_WOODWORKING_SUPPORTS_H
#define GEOMETRY_WOODWORKING_SUPPORTS_H
#ifndef GEOMETRY_KERNEL_GEOMETRY_H
#include "geometry.h"
#endif

typedef enum {
    WOOD_STOP_OUTLINE_EDGE,
    WOOD_STOP_HOLE_EDGE,
    WOOD_STOP_MEMBER_SIDE
} WoodStopFaceKind;

/* Existing EdgeFixity values. Selection treats exactly zero as FREE; it
 * does not add a new admission check for other consumer-supplied integers. */
enum { WOOD_STOP_FREE = 0, WOOD_STOP_FIXED = 1 };

typedef struct {
    int kind;
    uint32_t boundary_id;
    uint32_t timber_id;
    int hole_index;
    int edge_index;
    int fixity;
    GeoCoord fixed;
    GeoCoord lo;
    GeoCoord hi;
} WoodStopFace;

typedef struct {
    int kind;
    int hole;
    int edge;
    uint32_t timber;
} WoodStopRef;

bool wood_stop_matches_ref(const WoodStopFace *f, const WoodStopRef *r);

/* Preserves input order, caps the returned count at out_cap and only sets
 * diagnostic flags (never resets them). Width rejection precedes FREE.
 * The output array and flags are caller-owned, as in the original helper. */
size_t wood_stop_ref_candidates(
    const WoodStopFace faces[], size_t face_count, const WoodStopRef *r,
    GeoCoord cross_lo, GeoCoord cross_hi,
    const WoodStopFace *out[], size_t out_cap,
    bool *saw_free, bool *saw_narrow
);

/* Only member faces can be shadowed; only an earlier face at the same
 * fixed coordinate covering the requested interval shadows one. */
bool wood_stop_shadowed(const WoodStopFace faces[], size_t i, GeoCoord lo, GeoCoord hi);

/* FREE faces count here so the consumer can identify the original refusal.
 * Writes out_face only for exactly one hit; zero/ambiguous leave it intact. */
size_t wood_stop_pick(
    const WoodStopFace faces[], size_t face_count,
    GeoCoord at, GeoCoord lo, GeoCoord hi, const WoodStopFace **out_face
);
size_t wood_stop_count_legal(
    const WoodStopFace faces[], size_t face_count,
    GeoCoord at, GeoCoord lo, GeoCoord hi
);

/* Original R18 boundary-role derivation over the supplied outer loop only.
 * Null outline resets all outputs and returns false. A non-null borrowed
 * view must have accessible vertices for its count, as other K views do.
 * Covers-edge wins, then longest positive overlap, then earliest index. */
bool wood_member_boundary_props(
    const GeoLoop2View *outline, bool along_v,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord cross_lo, GeoCoord cross_hi,
    bool *out_on_boundary, bool *out_covers_edge, int *out_boundary_edge
);
#endif
