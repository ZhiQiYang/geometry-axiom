#ifndef GEO_KERNEL_DOCUMENT_INTERNAL_H
#define GEO_KERNEL_DOCUMENT_INTERNAL_H
#include "../document.h"
#include "parameter_store.h"
#include "named_values.h"
#include "datums.h"
#include "guides.h"
#include "regions.h"
#include "placements.h"
#include "grid_store.h"
#include "versions.h"
#include "enclosures.h"
/* The host may embed this private layout for whole-candidate value copies.
 * Templates receive public handles, never this storage definition. */
struct GeoDocument {
    GeoNamedValues named_values;
    GeoDatumStore datum_planes;
    GeoRegionStore region_data;
    GeoGridStore grid_store;
    GeoPlacementStore placement_data;
    GeoGuideStore guide_lines;
    GeoVersionStore version_store;
    GeoParameterStore parameters;
    GeoEnclosureStore enclosures;
};
#endif
