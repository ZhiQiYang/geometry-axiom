#ifndef GEO_KERNEL_LINEAR_DEFINITION_SOURCES_H
#define GEO_KERNEL_LINEAR_DEFINITION_SOURCES_H
#include "guides.h"
#include "source.h"

#define GEO_LINEAR_DEFINITION_CONTENT_MAX (32+32*GEO_LINEAR_MAX_TERMS+GEO_LINEAR_KEY_BYTES)
typedef enum {GEO_LINEAR_DEFINITION_DATUM=1,GEO_LINEAR_DEFINITION_GUIDE=2} GeoLinearDefinitionKind;
typedef struct {unsigned char bytes[5];} GeoLinearDefinitionKey;
typedef struct GeoLinearDefinitionSources GeoLinearDefinitionSources;
/* Exact portable identity: one kind byte and BE32 authored id. */
GeoSourceRef geo_linear_definition_source_ref(GeoProviderToken,GeoLinearDefinitionKind,uint32_t,GeoLinearDefinitionKey *);
bool geo_linear_definition_source_decode(const GeoSourceRef *,GeoLinearDefinitionKind *,uint32_t *);
/* Canonical authored data only. Expressions retain mode, completeness, term
 * order, unnormalised signed coefficients and complete opaque source keys.
 * Cache values, padding and inactive fields are excluded. Invalid/truncated
 * inputs leave the caller's output unchanged. */
size_t geo_datum_definition_encode(const GeoDatum *,unsigned char [GEO_LINEAR_DEFINITION_CONTENT_MAX]);
bool geo_datum_definition_decode(const void *,size_t,GeoDatum *);
size_t geo_guide_definition_encode(const GeoGuide *,unsigned char [GEO_LINEAR_DEFINITION_CONTENT_MAX]);
bool geo_guide_definition_decode(const void *,size_t,GeoGuide *);
/* Stores and graph belong to the same isolated candidate. Describing and
 * enumerating definitions never evaluates a term, datum position or guide. */
GeoLinearDefinitionSources *geo_linear_definition_sources_register(GeoEvalContext *,const GeoDatumStore *,const GeoGuideStore *,GeoProviderToken);
void geo_linear_definition_sources_destroy(GeoLinearDefinitionSources *);
bool geo_linear_definition_sources_datum(GeoLinearDefinitionSources *,uint32_t,GeoDatum *);
bool geo_linear_definition_sources_guide(GeoLinearDefinitionSources *,uint32_t,GeoGuide *);
bool geo_linear_definition_sources_complete(GeoLinearDefinitionSources *);
#endif
