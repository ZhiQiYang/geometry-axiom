#ifndef GEO_KERNEL_DATUMS_H
#define GEO_KERNEL_DATUMS_H
#include "linear.h"
#define GEO_DATUM_CAPACITY 64
typedef struct {
    uint32_t id;
    int axis;
    GeoLinearExpression expression;
    GeoCoord position;
} GeoDatum;
typedef struct GeoDatumStore GeoDatumStore;
typedef enum {
    GEO_DATUM_INTERSECTION_OK=0,GEO_DATUM_INTERSECTION_INVALID,
    GEO_DATUM_INTERSECTION_COINCIDENT,GEO_DATUM_INTERSECTION_PARALLEL,
    GEO_DATUM_INTERSECTION_RANGE
} GeoDatumIntersectionStatus;
typedef struct {int coordinate_axis;GeoCoord coordinate;} GeoDatumIntersection;
GeoDatumStore *geo_datums_create(void);
GeoDatumStore *geo_datums_clone(const GeoDatumStore *);
void geo_datums_destroy(GeoDatumStore *);
size_t geo_datums_count(const GeoDatumStore *);
const GeoDatum *geo_datums_at(const GeoDatumStore *,size_t);
const GeoDatum *geo_datums_values(const GeoDatumStore *);
const GeoDatum *geo_datums_find(const GeoDatumStore *,uint32_t);
/* Store typed definitions, including an incomplete input candidate. Its
 * evaluation fails only after valid-prefix source diagnostics are collected. */
bool geo_datums_put(GeoDatumStore *,uint32_t id,int axis,const GeoLinearExpression *);
bool geo_datums_remove(GeoDatumStore *,uint32_t id);
GeoLinearResult geo_datums_evaluate(GeoDatumStore *,size_t,GeoLinearResolver,void *);
/* Evaluate returned authored data for the same stable identity. Only the
 * existing position cache is updated, with the same OK/RANGE rule. */
GeoLinearResult geo_datums_evaluate_definition(GeoDatumStore *,size_t,const GeoDatum *,GeoLinearResolver,void *);
/* RANGE still supplies the unique (out-of-domain) intersection for rejected
 * candidate diagnostics. Other failures leave out unchanged. */
GeoDatumIntersectionStatus geo_datum_intersection(const GeoDatum *,const GeoFrame *,GeoDatumIntersection *);
#endif
