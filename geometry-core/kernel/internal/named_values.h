#ifndef GEO_KERNEL_NAMED_VALUES_INTERNAL_H
#define GEO_KERNEL_NAMED_VALUES_INTERNAL_H
#include "../named_values.h"
struct GeoNamedValues {
    GeoNamedValue values[GEO_NAMED_VALUE_CAPACITY];
    size_t count;
};
#endif
