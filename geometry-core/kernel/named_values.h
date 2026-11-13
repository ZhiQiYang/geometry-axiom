#ifndef GEO_KERNEL_NAMED_VALUES_H
#define GEO_KERNEL_NAMED_VALUES_H
#include "geometry.h"
#include <stddef.h>
#include <stdbool.h>
#define GEO_NAMED_VALUE_CAPACITY 64
#define GEO_NAMED_VALUE_NAME_BYTES 96
typedef struct { char name[GEO_NAMED_VALUE_NAME_BYTES]; GeoCoord value; } GeoNamedValue;
typedef struct GeoNamedValues GeoNamedValues;
GeoNamedValues *geo_named_values_create(void);
GeoNamedValues *geo_named_values_clone(const GeoNamedValues *);
void geo_named_values_destroy(GeoNamedValues *);
size_t geo_named_values_count(const GeoNamedValues *);
const GeoNamedValue *geo_named_values_at(const GeoNamedValues *,size_t);
const GeoNamedValue *geo_named_values_find(const GeoNamedValues *,const char *);
bool geo_named_value_name_valid(const char *);
bool geo_named_values_put(GeoNamedValues *,const char *,GeoCoord);
bool geo_named_values_remove(GeoNamedValues *,const char *);
#endif
