#ifndef GEO_KERNEL_LINEAR_H
#define GEO_KERNEL_LINEAR_H
#include "exact.h"
#include "geometry.h"
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define GEO_LINEAR_MAX_TERMS 64
#define GEO_LINEAR_KEY_BYTES 1536
typedef enum { GEO_LINEAR_FLOOR_FINAL=0, GEO_LINEAR_EXACT_INTEGER_FINAL=1 } GeoLinearMode;
/* Provider numbers are assigned by the host. The kernel never parses keys. */
typedef struct {
    uint32_t provider, id, field;
    const char *key;
} GeoLinearSource;
typedef struct {
    int64_t numerator, denominator;
    uint32_t provider, id, field;
    size_t key_offset;
} GeoLinearTerm;
typedef struct {
    GeoLinearMode mode;
    GeoLinearTerm terms[GEO_LINEAR_MAX_TERMS];
    size_t count, key_bytes;
    char keys[GEO_LINEAR_KEY_BYTES];
    /* A host decoder can retain an invalid suffix after its valid prefix. */
    bool complete;
} GeoLinearExpression;
typedef bool (*GeoLinearResolver)(void *,const GeoLinearSource *,GeoQuantity *);
typedef enum {
    GEO_LINEAR_OK=0, GEO_LINEAR_INVALID, GEO_LINEAR_SOURCE_FAILED,
    GEO_LINEAR_ARITHMETIC, GEO_LINEAR_NOT_INTEGER, GEO_LINEAR_RANGE
} GeoLinearStatus;
typedef struct {
    GeoLinearStatus status;
    GeoExactStatus exact_status;
    size_t term;
    GeoQuantity value;
} GeoLinearResult;

void geo_linear_begin(GeoLinearExpression *,GeoLinearMode);
bool geo_linear_append(GeoLinearExpression *,int64_t numerator,int64_t denominator,
                       GeoLinearSource);
void geo_linear_finish(GeoLinearExpression *,bool complete);
GeoLinearResult geo_linear_evaluate(const GeoLinearExpression *,GeoLinearResolver,void *);
#endif
