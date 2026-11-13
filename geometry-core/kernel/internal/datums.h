#ifndef GEO_KERNEL_DATUMS_INTERNAL_H
#define GEO_KERNEL_DATUMS_INTERNAL_H
#include "../datums.h"
struct GeoDatumStore {GeoDatum values[GEO_DATUM_CAPACITY];size_t count;};
#endif
