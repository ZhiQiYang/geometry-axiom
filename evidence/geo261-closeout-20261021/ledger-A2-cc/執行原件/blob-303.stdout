/* Woodworking value records used by template recipes and the H legacy codec.
 * Placed boundary/placement geometry is persisted in independent K stores;
 * these records are explicit caller-owned values, not a second world store. */
#ifndef GEOMETRY_WOODWORKING_DOMAIN_VALUES_H
#define GEOMETRY_WOODWORKING_DOMAIN_VALUES_H
#include "boundary_policy.h"
typedef struct {
    GeoPoint2 v[GEO_LOOP_MAX_VERTICES];
    size_t count;
    WoodEdgeFixity fixity[GEO_LOOP_MAX_VERTICES];
} WoodBoundaryLoop;
typedef struct {
    uint32_t id;
    WoodBoundaryKind kind;
    WoodBoundaryLoop outline;
    WoodBoundaryLoop holes[GEO_REGION_MAX_HOLES];
    size_t hole_count;
} WoodBoundaryRegion;
#endif
