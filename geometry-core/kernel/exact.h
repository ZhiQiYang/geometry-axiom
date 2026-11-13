#ifndef GEOMETRY_KERNEL_EXACT_H
#define GEOMETRY_KERNEL_EXACT_H
#include "types.h"
typedef enum {
    GEO_EXACT_OK=0,
    GEO_EXACT_INTEGER_MAGNITUDE,
    GEO_EXACT_MULTIPLICATION_OVERFLOW,
    GEO_EXACT_SUM_OVERFLOW,
    GEO_EXACT_UNIT_MISMATCH,
    GEO_EXACT_PRODUCT_UNIT,
    GEO_EXACT_DIVISION_ZERO,
    GEO_EXACT_INVERSE_UNIT,
    GEO_EXACT_UNKNOWN_OPERATION,
    GEO_EXACT_DENOMINATOR,
    GEO_EXACT_INVALID_UNIT
} GeoExactStatus;
typedef enum { GEO_EXACT_ADD, GEO_EXACT_SUBTRACT, GEO_EXACT_MULTIPLY, GEO_EXACT_DIVIDE } GeoExactOperation;
/* Values use a signed magnitude no larger than INT64_MAX and a strictly
 * positive denominator. Arithmetic is exact or fails; no output is changed
 * on failure. The returned status has no host wording or clause identifiers. */
GeoExactStatus geo_integer_multiply(int64_t a,int64_t b,int64_t *out);
GeoExactStatus geo_integer_add(int64_t a,int64_t b,int64_t *out);
GeoExactStatus geo_quantity_normalize(GeoQuantity value,GeoQuantity *out);
GeoExactStatus geo_quantity_binary(GeoExactOperation operation,GeoQuantity a,GeoQuantity b,GeoQuantity *out);
#endif
