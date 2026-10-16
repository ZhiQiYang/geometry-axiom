#ifndef GEO_KERNEL_PLACEMENTS_INTERNAL_H
#define GEO_KERNEL_PLACEMENTS_INTERNAL_H
#include "../placements.h"
/* Inline POD: a whole candidate copy owns every definition and coordinate. */
struct GeoPlacementStore {
    GeoPlacementDefinition items[GEO_PLACEMENT_CAPACITY];
    size_t count;
};
#endif
