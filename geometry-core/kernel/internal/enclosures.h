#ifndef GEO_KERNEL_ENCLOSURES_INTERNAL_H
#define GEO_KERNEL_ENCLOSURES_INTERNAL_H
#include "../enclosure.h"
/* Inline owned POD; borrowed values refer to this array. */
struct GeoEnclosureStore {
    GeoEnclosure values[GEO_ENCLOSURE_CAPACITY];
    size_t count;
};
#endif
