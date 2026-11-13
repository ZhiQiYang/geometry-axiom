/* Neutral scalar value types. Field kinds are not arithmetic units: a count
 * and a ratio both evaluate to scalars but retain their own field definitions. */
#ifndef GEOMETRY_KERNEL_TYPES_H
#define GEOMETRY_KERNEL_TYPES_H
#include <stdint.h>
typedef enum { GEO_UNIT_SCALAR=0, GEO_UNIT_LENGTH=1 } GeoQuantityUnit;
typedef struct { int64_t num, den; GeoQuantityUnit unit; } GeoQuantity;
#endif
