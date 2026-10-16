#include "parameter_sources.h"
#include <stdlib.h>
#include <string.h>

struct GeoParameterSources {
    GeoEvalContext *sources;
    GeoParameterStore *store;
    GeoParameterEvaluation *evaluation;
    GeoProviderToken token;
};
static bool geo_parameter_source_ref(const GeoParameterSources *state,const GeoSourceRef *source,GeoParameterRef *ref)
{
    if(source->provider!=state->token||source->key_size!=2*sizeof(uint32_t)||!source->key)return false;
    uint32_t ids[2];memcpy(ids,source->key,sizeof ids);
    *ref=(GeoParameterRef){true,ids[0],ids[1]};return true;
}
static GeoParameterStatus geo_parameter_source_status(GeoSourceStatus status)
{
    switch(status){
    case GEO_SOURCE_OK:return GEO_PARAMETER_OK;
    case GEO_SOURCE_CYCLE:return GEO_PARAMETER_CYCLE;
    case GEO_SOURCE_MISSING:return GEO_PARAMETER_MISSING_FIELD;
    case GEO_SOURCE_MEMORY:return GEO_PARAMETER_MEMORY;
    default:return GEO_PARAMETER_INVALID_DEFINITION;
    }
}
static GeoParameterStatus geo_parameter_source_resolve(void *opaque,GeoParameterRef ref,GeoQuantity *out)
{
    GeoParameterSources *state=opaque;uint32_t ids[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(state->sources,(GeoSourceRef){state->token,ids,sizeof ids},
        GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    if(status==GEO_SOURCE_OK)*out=value.as.quantity;
    return geo_parameter_source_status(status);
}
static bool geo_parameter_source_describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    GeoParameterSources *state=opaque;GeoParameterRef ref;
    if(!geo_parameter_source_ref(state,source,&ref))return false;
    int index=geo_parameters_field_index(state->store,ref.parameter_id,ref.field_id);
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->context.axis=-1;
    out->unit=index>=0&&geo_parameters_fields(state->store)[index].type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;
    return true;
}
static bool geo_parameter_source_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *source,GeoSourceValue *out)
{
    GeoParameterSources *state=opaque;GeoParameterRef ref;
    if(ctx!=state->sources||!geo_parameter_source_ref(state,source,&ref))return false;
    out->kind=GEO_SOURCE_QUANTITY;
    return geo_parameter_evaluation_field(state->evaluation,ref,&out->as.quantity);
}
GeoParameterSources *geo_parameter_sources_register(GeoEvalContext *ctx,GeoParameterStore *store,
    GeoProviderToken token,const char *name_space,const char *fingerprint)
{
    if(!ctx||!store)return NULL;
    GeoParameterSources *state=calloc(1,sizeof *state);if(!state)return NULL;
    state->sources=ctx;state->store=store;state->token=token;
    state->evaluation=geo_parameter_evaluation_create(store,geo_parameter_source_resolve,state);
    GeoSourceProvider provider={token,name_space,fingerprint,state,geo_parameter_source_describe,geo_parameter_source_evaluate};
    if(!state->evaluation||!geo_eval_register(ctx,&provider)){geo_parameter_sources_destroy(state);return NULL;}
    return state;
}
void geo_parameter_sources_destroy(GeoParameterSources *state)
{if(state){geo_parameter_evaluation_destroy(state->evaluation);free(state);}}
const GeoParameterStore *geo_parameter_sources_store(const GeoParameterSources *state)
{return state?state->store:NULL;}
const GeoEvalContext *geo_parameter_sources_context(const GeoParameterSources *state)
{return state?state->sources:NULL;}
bool geo_parameter_sources_value(GeoParameterSources *state,GeoParameterRef ref,GeoQuantity *out,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!state||!out){if(error)error->status=GEO_PARAMETER_INVALID_DEFINITION;return false;}
    GeoParameterStatus status=geo_parameter_source_resolve(state,ref,out);
    if(status==GEO_PARAMETER_OK)return true;
    if(error){*error=*geo_parameter_evaluation_error(state->evaluation);
        if(error->status==GEO_PARAMETER_OK){error->status=status;error->source=ref;}}
    return false;
}
bool geo_parameter_sources_rebuild(GeoParameterSources *state,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!state){if(error)error->status=GEO_PARAMETER_INVALID_DEFINITION;return false;}
    const GeoParameterField *fields=geo_parameters_fields(state->store);
    for(size_t i=0;i<geo_parameters_field_count(state->store);++i){GeoQuantity value;
        if(!geo_parameter_sources_value(state,(GeoParameterRef){true,fields[i].parameter_id,fields[i].id},&value,error))return false;}
    return true;
}
