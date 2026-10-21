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

GeoParameterStore *geo_document_parameters(GeoDocument *document)
{return document?&document->parameters:NULL;}
const GeoParameterStore *geo_document_parameters_view(const GeoDocument *document)
{return document?&document->parameters:NULL;}
GeoNamedValues *geo_document_named_values(GeoDocument *document)
{return document?&document->named_values:NULL;}
const GeoNamedValues *geo_document_named_values_view(const GeoDocument *document)
{return document?&document->named_values:NULL;}
GeoDatumStore *geo_document_datums(GeoDocument *document)
{return document?&document->datum_planes:NULL;}
const GeoDatumStore *geo_document_datums_view(const GeoDocument *document)
{return document?&document->datum_planes:NULL;}
GeoGuideStore *geo_document_guides(GeoDocument *document)
{return document?&document->guide_lines:NULL;}
const GeoGuideStore *geo_document_guides_view(const GeoDocument *document)
{return document?&document->guide_lines:NULL;}
GeoRegionStore *geo_document_regions(GeoDocument *document)
{return document?&document->region_data:NULL;}
const GeoRegionStore *geo_document_regions_view(const GeoDocument *document)
{return document?&document->region_data:NULL;}
GeoPlacementStore *geo_document_placements(GeoDocument *document)
{return document?&document->placement_data:NULL;}
const GeoPlacementStore *geo_document_placements_view(const GeoDocument *document)
{return document?&document->placement_data:NULL;}
GeoGridStore *geo_document_grids(GeoDocument *document)
{return document?&document->grid_store:NULL;}
const GeoGridStore *geo_document_grids_view(const GeoDocument *document)
{return document?&document->grid_store:NULL;}
GeoVersionStore *geo_document_versions(GeoDocument *document)
{return document?&document->version_store:NULL;}
const GeoVersionStore *geo_document_versions_view(const GeoDocument *document)
{return document?&document->version_store:NULL;}
GeoEnclosureStore *geo_document_enclosures(GeoDocument *document)
{return document?&document->enclosures:NULL;}
const GeoEnclosureStore *geo_document_enclosures_view(const GeoDocument *document)
{return document?&document->enclosures:NULL;}
