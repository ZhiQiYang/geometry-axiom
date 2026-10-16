#ifndef GEO_KERNEL_REGIONS_INTERNAL_H
#define GEO_KERNEL_REGIONS_INTERNAL_H
#include "../regions.h"
/* Inline POD storage keeps candidate snapshots independent, including when
 * the host embeds a store in its own transaction object. */
struct GeoRegionStore {
    GeoRegionDefinition regions[GEO_REGION_CAPACITY];
    size_t count;
    GeoRegionKeys keys[GEO_REGION_CAPACITY];
    size_t key_count;
};
#endif
