#ifndef GEOMETRY_KERNEL_PARAMETER_SOURCES_H
#define GEOMETRY_KERNEL_PARAMETER_SOURCES_H
#include "parameters.h"
#include "source.h"

/* The composition root assigns the registry identity. Keys are exactly two
 * uint32_t values: card id then field id. The store and resolver must outlive
 * this binding; the binding must outlive every evaluation using its provider. */
typedef struct GeoParameterSources GeoParameterSources;
GeoParameterSources *geo_parameter_sources_register(GeoEvalContext *,GeoParameterStore *,
    GeoProviderToken,const char *name_space,const char *implementation_fingerprint);
void geo_parameter_sources_destroy(GeoParameterSources *);
const GeoParameterStore *geo_parameter_sources_store(const GeoParameterSources *);
const GeoEvalContext *geo_parameter_sources_context(const GeoParameterSources *);
bool geo_parameter_sources_rebuild(GeoParameterSources *,GeoParameterError *);
bool geo_parameter_sources_value(GeoParameterSources *,GeoParameterRef,GeoQuantity *,GeoParameterError *);
#endif
