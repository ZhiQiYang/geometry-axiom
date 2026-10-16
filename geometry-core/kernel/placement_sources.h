#ifndef GEO_KERNEL_PLACEMENT_SOURCES_H
#define GEO_KERNEL_PLACEMENT_SOURCES_H
#include "placements.h"
#include "source.h"

typedef enum { GEO_PLACEMENT_SOURCE_FRAME=1,GEO_PLACEMENT_SOURCE_REGIONS=2 } GeoPlacementSourceKind;
typedef struct { unsigned char bytes[5]; } GeoPlacementSourceKey;
typedef struct { unsigned char bytes[4]; } GeoRegionSourceKey;
typedef struct GeoPlacementSources GeoPlacementSources;
/* An optional same-candidate binding supplies an upstream typed source. Its
 * key must remain readable after the callback returns, until the immediately
 * following synchronous geo_eval_source call has returned. Candidate-owned
 * storage satisfies this contract; callback-local arrays do not. Returning
 * false selects the owned store's explicit value. */
typedef bool (*GeoPlacementSourceBinding)(void *,uint32_t,GeoPlacementSourceKind,GeoSourceRef *);
GeoSourceRef geo_placement_source_ref(GeoProviderToken,GeoPlacementSourceKind,uint32_t,GeoPlacementSourceKey *);
GeoSourceRef geo_region_source_ref(GeoProviderToken,uint32_t,GeoRegionSourceKey *);
bool geo_placement_source_decode(const GeoSourceRef *,GeoPlacementSourceKind *,uint32_t *);
bool geo_region_source_decode(const GeoSourceRef *,uint32_t *);
GeoPlacementSources *geo_placement_sources_register(GeoEvalContext *,const GeoPlacementStore *,const GeoRegionStore *,
    GeoProviderToken,GeoProviderToken,GeoPlacementSourceBinding,void *);
/* Does not access graph or stores: either destruction order is safe. No
 * evaluation or borrowed-view reads may follow destruction of this handle. */
void geo_placement_sources_destroy(GeoPlacementSources *);
#endif
