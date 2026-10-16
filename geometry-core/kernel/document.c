#include "internal/document.h"
#include <stdlib.h>
#include <string.h>

GeoDocument *geo_document_create(void)
{return calloc(1,sizeof(GeoDocument));}
GeoDocument *geo_document_clone(const GeoDocument *source)
{
    if(!source)return NULL;
    GeoDocument *copy=malloc(sizeof *copy);
    if(copy)memcpy(copy,source,sizeof *copy);
    return copy;
}
void geo_document_destroy(GeoDocument *document)
{free(document);}
void geo_document_clear(GeoDocument *document)
{if(document)memset(document,0,sizeof *document);}

#define GEO_DOCUMENT_STORE(type,name,field) \
    type *geo_document_##name(GeoDocument *document) \
    {return document?&document->field:NULL;} \
    const type *geo_document_##name##_view(const GeoDocument *document) \
    {return document?&document->field:NULL;}
GEO_DOCUMENT_STORE(GeoParameterStore,parameters,parameters)
GEO_DOCUMENT_STORE(GeoNamedValues,named_values,named_values)
GEO_DOCUMENT_STORE(GeoDatumStore,datums,datum_planes)
GEO_DOCUMENT_STORE(GeoGuideStore,guides,guide_lines)
GEO_DOCUMENT_STORE(GeoRegionStore,regions,region_data)
GEO_DOCUMENT_STORE(GeoPlacementStore,placements,placement_data)
GEO_DOCUMENT_STORE(GeoGridStore,grids,grid_store)
GEO_DOCUMENT_STORE(GeoVersionStore,versions,version_store)
GEO_DOCUMENT_STORE(GeoEnclosureStore,enclosures,enclosures)
#undef GEO_DOCUMENT_STORE
