/* Woodworking edge attachment policy and legacy application categories.
 * Geometry and vertex identities are owned by the independent K region store. */
#ifndef GEOMETRY_WOODWORKING_BOUNDARY_POLICY_H
#define GEOMETRY_WOODWORKING_BOUNDARY_POLICY_H
#ifndef GEO_KERNEL_REGIONS_H
#include "regions.h"
#endif
typedef enum { WOOD_EDGE_FREE=0, WOOD_EDGE_FIXED=1 } WoodEdgeFixity;
typedef enum { WOOD_BOUNDARY_UNSPECIFIED=0, WOOD_BOUNDARY_ROOM_PLAN=1,
    WOOD_BOUNDARY_WALL_ELEVATION=2 } WoodBoundaryKind;
typedef struct {
    uint32_t id;
    WoodBoundaryKind kind;
    WoodEdgeFixity fixity[GEO_REGION_MAX_HOLES+1][GEO_LOOP_MAX_VERTICES];
} WoodBoundaryPolicy;
typedef struct {
    uint32_t id, fill_id;
    GeoCoord height;
    WoodBoundaryPolicy components[8];
} WoodPlacementPolicy;
/* I3 default attachment policy. Only the requested entries are written. */
void wood_boundary_default_fixity(WoodEdgeFixity *,size_t);
#endif
