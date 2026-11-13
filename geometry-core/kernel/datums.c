#include "internal/datums.h"
#include <stdlib.h>
#include <string.h>

GeoDatumStore *geo_datums_create(void){return calloc(1,sizeof(GeoDatumStore));}
GeoDatumStore *geo_datums_clone(const GeoDatumStore *source)
{if(!source)return NULL;GeoDatumStore *copy=malloc(sizeof *copy);if(copy)*copy=*source;return copy;}
void geo_datums_destroy(GeoDatumStore *store){free(store);}
size_t geo_datums_count(const GeoDatumStore *store){return store?store->count:0;}
const GeoDatum *geo_datums_at(const GeoDatumStore *store,size_t at)
{return store&&at<store->count?&store->values[at]:NULL;}
const GeoDatum *geo_datums_values(const GeoDatumStore *store)
{return store?store->values:NULL;}
const GeoDatum *geo_datums_find(const GeoDatumStore *store,uint32_t id)
{if(!store)return NULL;for(size_t i=0;i<store->count;++i)if(store->values[i].id==id)return &store->values[i];return NULL;}
bool geo_datums_put(GeoDatumStore *store,uint32_t id,int axis,const GeoLinearExpression *expression)
{
    if(!store||!expression||axis<0||axis>2||expression->count>GEO_LINEAR_MAX_TERMS||expression->key_bytes>GEO_LINEAR_KEY_BYTES)return false;
    size_t at=0;while(at<store->count&&store->values[at].id!=id)++at;
    if(at>=GEO_DATUM_CAPACITY)return false;
    /* Canonical field-wise copying owns keys and leaves no borrowed memory or
     * unspecified padding in a value-copy candidate snapshot. */
    GeoDatum next;memset(&next,0,sizeof next);next.id=id;next.axis=axis;
    geo_linear_begin(&next.expression,expression->mode);
    for(size_t i=0;i<expression->count;++i){
        const GeoLinearTerm *term=&expression->terms[i];
        if(term->key_offset>=expression->key_bytes||!memchr(expression->keys+term->key_offset,0,expression->key_bytes-term->key_offset))return false;
        GeoLinearSource source={term->provider,term->id,term->field,expression->keys+term->key_offset};
        if(!geo_linear_append(&next.expression,term->numerator,term->denominator,source))return false;
    }
    geo_linear_finish(&next.expression,expression->complete);
    store->values[at]=next;if(at==store->count)++store->count;return true;
}
bool geo_datums_remove(GeoDatumStore *store,uint32_t id)
{
    if(!store)return false;size_t at=0;while(at<store->count&&store->values[at].id!=id)++at;
    if(at==store->count)return false;
    memmove(store->values+at,store->values+at+1,(store->count-at-1)*sizeof *store->values);
    memset(&store->values[--store->count],0,sizeof *store->values);return true;
}
GeoLinearResult geo_datums_evaluate(GeoDatumStore *store,size_t at,GeoLinearResolver resolve,void *state)
{return geo_datums_evaluate_definition(store,at,geo_datums_at(store,at),resolve,state);}
GeoLinearResult geo_datums_evaluate_definition(GeoDatumStore *store,size_t at,const GeoDatum *definition,GeoLinearResolver resolve,void *state)
{
    GeoLinearResult result={GEO_LINEAR_INVALID,GEO_EXACT_OK,0,{0,1,GEO_UNIT_LENGTH}};
    if(!store||at>=store->count||!definition)return result;
    GeoDatum *datum=&store->values[at];
    if(definition->id!=datum->id||definition->axis<0||definition->axis>2)return result;
    result=geo_linear_evaluate(&definition->expression,resolve,state);
    if(result.status==GEO_LINEAR_OK||result.status==GEO_LINEAR_RANGE)datum->position=result.value.num;
    return result;
}
static GeoCoord geo_datum_component(GeoVector3 vector,int axis)
{return axis==0?vector.x:axis==1?vector.y:vector.z;}
GeoDatumIntersectionStatus geo_datum_intersection(const GeoDatum *datum,const GeoFrame *frame,GeoDatumIntersection *out)
{
    if(!datum||!frame||!out||datum->axis<0||datum->axis>2||!geo_frame_is_valid(frame)||!geo_coord_in_range(datum->position))return GEO_DATUM_INTERSECTION_INVALID;
    GeoCoord origin=datum->axis==0?frame->origin.x:datum->axis==1?frame->origin.y:frame->origin.z;
    GeoCoord u=geo_datum_component(frame->axis_u,datum->axis),v=geo_datum_component(frame->axis_v,datum->axis);
    if(!u&&!v)return origin==datum->position?GEO_DATUM_INTERSECTION_COINCIDENT:GEO_DATUM_INTERSECTION_PARALLEL;
    GeoDatumIntersection result={u?0:1,(u?u:v)*(datum->position-origin)};
    *out=result;
    if(!geo_coord_in_range(result.coordinate))return GEO_DATUM_INTERSECTION_RANGE;
    return GEO_DATUM_INTERSECTION_OK;
}
