#ifndef GEO_KERNEL_GRID_STORE_INTERNAL_H
#define GEO_KERNEL_GRID_STORE_INTERNAL_H
#include "../grid_store.h"
struct GeoGridStore {
    GeoGridSystem systems[GEO_GRID_SYSTEM_CAPACITY];
    size_t system_count;
    GeoGridBinding bindings[GEO_GRID_BINDING_CAPACITY];
    size_t binding_count;
};
#endif
