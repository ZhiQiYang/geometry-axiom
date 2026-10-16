/* An owned collection of neutral definitions. The document contains only
 * inline K stores; no provider, template, host metadata or borrowed pointer
 * is retained. Candidate evaluation contexts are separate, short-lived data. */
#ifndef GEO_KERNEL_DOCUMENT_H
#define GEO_KERNEL_DOCUMENT_H
#include "parameters.h"
#include "named_values.h"
#include "datums.h"
#include "guides.h"
#include "regions.h"
#include "placements.h"
#include "grid_store.h"
#include "versions.h"
#include "enclosure.h"

typedef struct GeoDocument GeoDocument;
GeoDocument *geo_document_create(void);
GeoDocument *geo_document_clone(const GeoDocument *);
void geo_document_destroy(GeoDocument *);
void geo_document_clear(GeoDocument *);

/* These borrowed store handles remain valid until their owning document is
 * destroyed. Mutations use each store's public API and its usual checks. */
GeoParameterStore *geo_document_parameters(GeoDocument *);
GeoNamedValues *geo_document_named_values(GeoDocument *);
GeoDatumStore *geo_document_datums(GeoDocument *);
GeoGuideStore *geo_document_guides(GeoDocument *);
GeoRegionStore *geo_document_regions(GeoDocument *);
GeoPlacementStore *geo_document_placements(GeoDocument *);
GeoGridStore *geo_document_grids(GeoDocument *);
GeoVersionStore *geo_document_versions(GeoDocument *);
GeoEnclosureStore *geo_document_enclosures(GeoDocument *);

const GeoParameterStore *geo_document_parameters_view(const GeoDocument *);
const GeoNamedValues *geo_document_named_values_view(const GeoDocument *);
const GeoDatumStore *geo_document_datums_view(const GeoDocument *);
const GeoGuideStore *geo_document_guides_view(const GeoDocument *);
const GeoRegionStore *geo_document_regions_view(const GeoDocument *);
const GeoPlacementStore *geo_document_placements_view(const GeoDocument *);
const GeoGridStore *geo_document_grids_view(const GeoDocument *);
const GeoVersionStore *geo_document_versions_view(const GeoDocument *);
const GeoEnclosureStore *geo_document_enclosures_view(const GeoDocument *);
#endif
