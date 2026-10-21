#ifndef GEO_KERNEL_PLACEMENT_SOURCES_H
#define GEO_KERNEL_PLACEMENT_SOURCES_H
#include "placements.h"
#include "source.h"

typedef enum {
    GEO_PLACEMENT_SOURCE_FRAME=1,GEO_PLACEMENT_SOURCE_REGIONS=2,
    GEO_PLACEMENT_SOURCE_DEFINITION=3
} GeoPlacementSourceKind;
#define GEO_PLACEMENT_DEFINITION_SCHEMA "geometry.placement-definition/1"
#define GEO_PLACEMENT_DEFINITION_MAX_BYTES (105u+GEO_PLACEMENT_COMPONENT_CAPACITY* \
    (12u+16u*GEO_LOOP_MAX_VERTICES+GEO_REGION_MAX_HOLES*(4u+16u*GEO_LOOP_MAX_VERTICES)))
typedef struct { unsigned char bytes[5]; } GeoPlacementSourceKey;
typedef struct { unsigned char bytes[4]; } GeoRegionSourceKey;
typedef struct GeoPlacementSources GeoPlacementSources;
/* An optional same-candidate binding supplies an upstream typed source. Its
 * key must remain readable after the callback returns, until the immediately
 * following synchronous geo_eval_source call has returned. Candidate-owned
 * storage satisfies this contract; callback-local arrays do not. Returning
 * false selects the owned store's definition, or (for FRAME/REGIONS) geometry
 * read from the actual DEFINITION source. Bound geometry retains priority. */
typedef bool (*GeoPlacementSourceBinding)(void *,uint32_t,GeoPlacementSourceKind,GeoSourceRef *);
GeoSourceRef geo_placement_source_ref(GeoProviderToken,GeoPlacementSourceKind,uint32_t,GeoPlacementSourceKey *);
GeoSourceRef geo_region_source_ref(GeoProviderToken,uint32_t,GeoRegionSourceKey *);
bool geo_placement_source_decode(const GeoSourceRef *,GeoPlacementSourceKind *,uint32_t *);
bool geo_region_source_decode(const GeoSourceRef *,uint32_t *);
/* Canonical wire: BE32 id; twelve signed BE64 frame coordinates in origin,
 * axis_u, axis_v, normal order (x,y,z each); one-byte domain; then RECT's
 * four signed BE64 endpoints (min_u,min_v,max_u,max_v), REGION_REF's BE32
 * region_id, or REGION_SET's BE32 component count and ordered components.
 * Each component is BE32 id, an outline loop, BE32 hole count, then ordered
 * hole loops. A loop is BE32 vertex count followed by signed BE64 u,v pairs.
 * Only tags/count bounds are checked: staged invalid geometry remains data.
 * Inactive fields are omitted on encode and zeroed on decode. Failed writes
 * leave the caller's entire output unchanged; encode returns zero on failure. */
size_t geo_placement_definition_encode(const GeoPlacementDefinition *,void *,size_t);
bool geo_placement_definition_decode(const void *,size_t,GeoPlacementDefinition *);
GeoPlacementSources *geo_placement_sources_register(GeoEvalContext *,const GeoPlacementStore *,const GeoRegionStore *,
    GeoProviderToken,GeoProviderToken,GeoPlacementSourceBinding,void *);
/* Reads and decodes the actual DEFINITION_REQUIRED source value, including a
 * binding's replacement. Checks schema and requested id, never asks for FRAME
 * or REGIONS, and leaves out unchanged on failure. The returned POD owns all
 * decoded fields; provider wire bytes remain owned by the same candidate. */
bool geo_placement_sources_definition(GeoPlacementSources *,uint32_t,GeoPlacementDefinition *);
/* Does not access graph or stores: either destruction order is safe. No
 * evaluation or borrowed-view reads may follow destruction of this handle. */
void geo_placement_sources_destroy(GeoPlacementSources *);
#endif
