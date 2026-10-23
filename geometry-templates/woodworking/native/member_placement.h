/* Woodworking placement definitions and rebuilt local-coordinate caches.
 * The member array and this placement array use the same index. */
#ifndef GEOMETRY_WOODWORKING_MEMBER_PLACEMENT_H
#define GEOMETRY_WOODWORKING_MEMBER_PLACEMENT_H
#include "member_reference.h"

typedef enum {
    WOOD_SPAN_EXPLICIT = 0,
    WOOD_SPAN_AUTO = 1
} WoodMemberSpanMode;

/* Keep the declared field order, integer discriminator storage and bounded
 * arrays. This is copied inline with the candidate, including inactive fields.
 * Reference definitions are authoritative; uv and the member's length are
 * rebuilt caches. WoodMemberReference is a selected evaluation view of this
 * record, not a replacement for its persistent placement fields. */
typedef struct {
    uint32_t placement_id;
    GeoPoint2 uv;
    int anchor_kind;        /* WoodMemberAnchorKind */
    int span_mode;          /* WoodMemberSpanMode */
    int length_direction;   /* GeoDirection2 */
    int depth_side;         /* WoodMemberDepth */

    uint32_t ref_grid;
    int ref_grid_axis;      /* 0 = u coordinates, 1 = v coordinates */
    int64_t ref_grid_index;
    bool ref_grid_has_band;
    int64_t ref_grid_band;
    GeoGridRuleLineRef ref_rule;
    int ref_hole;           /* -1 = outline; otherwise hole index */
    int ref_edge;
    bool has_through;
    GeoCoord through;
    uint32_t ref_guide, ref_timber;
    bool ref_is_timber;
    char ref_derived_key[512];
    uint64_t order;
    bool has_between;
    WoodMemberReferenceFace between[2];
} WoodMemberPlacement;

#endif
