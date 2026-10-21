/* Owned plane domains: an explicit frame plus a rectangle, exact region
 * reference, or ordered region set. Source/template policy is not stored. */
#ifndef GEO_KERNEL_PLACEMENTS_H
#define GEO_KERNEL_PLACEMENTS_H
#include "regions.h"

#define GEO_PLACEMENT_CAPACITY 16
#define GEO_PLACEMENT_COMPONENT_CAPACITY 8
typedef enum {
    GEO_PLACEMENT_RECT=0, GEO_PLACEMENT_REGION_REF, GEO_PLACEMENT_REGION_SET
} GeoPlacementDomain;
typedef struct {
    uint32_t id;
    GeoFrame frame;
    GeoPlacementDomain domain;
    uint32_t region_id;
    GeoRect2 rect;
    GeoRegionDefinition components[GEO_PLACEMENT_COMPONENT_CAPACITY];
    size_t component_count;
} GeoPlacementDefinition;

typedef struct GeoPlacementStore GeoPlacementStore;
GeoPlacementStore *geo_placements_create(void);
GeoPlacementStore *geo_placements_clone(const GeoPlacementStore *source);
void geo_placements_destroy(GeoPlacementStore *store);
size_t geo_placements_count(const GeoPlacementStore *store);
const GeoPlacementDefinition *geo_placements_at(const GeoPlacementStore *store,size_t index);
const GeoPlacementDefinition *geo_placements_find(const GeoPlacementStore *store,uint32_t id);
/* Stage checks only the domain tag and bounds of active counts, then copies
 * active fields and zeros all inactive bytes. It deliberately permits an
 * unresolved reference or invalid geometry so a consumer can preserve its
 * existing candidate-validation order. No failed write changes the store. */
bool geo_placements_stage(GeoPlacementStore *store,const GeoPlacementDefinition *definition);
/* Full geometry validation: bounded right-handed frame, bounded positive
 * rectangle, existing valid referenced region, or individually valid ordered
 * components. An empty REGION_SET is valid; components are not merged. */
bool geo_placement_is_valid(const GeoPlacementDefinition *definition,const GeoRegionStore *regions);
bool geo_placements_put(GeoPlacementStore *store,const GeoPlacementDefinition *definition,const GeoRegionStore *regions);
bool geo_placements_remove(GeoPlacementStore *store,uint32_t id);

/* Views own no geometry. The scratch belongs to the caller and remains alive
 * while its result is used; non-rectangle vertices borrow definition/regions.
 * No view or scratch pointers are retained in the inline POD store. */
typedef struct {
    GeoPoint2 rectangle[4];
    GeoLoop2View holes[GEO_PLACEMENT_COMPONENT_CAPACITY][GEO_REGION_MAX_HOLES];
    GeoRegionView regions[GEO_PLACEMENT_COMPONENT_CAPACITY];
} GeoPlacementViewScratch;
bool geo_placement_domain_view(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,
    GeoPlacementViewScratch *scratch,GeoRegionSetView *out);

/* Queries consume geometry already validated by put or by the consumer's
 * candidate validator. Boundary contact is included and hole interiors are
 * excluded. Rectangles must fit one complete component: a union bbox is never
 * substituted. Failure leaves index/bounds unchanged. RECT keeps its original
 * endpoint-only rectangle comparison, including degenerate query rectangles. */
bool geo_placement_contains_point(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,GeoPoint2 point);
bool geo_placement_contains_rect(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,const GeoRect2 *rect);
bool geo_placement_component_for_rect(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,const GeoRect2 *rect,size_t *index);
bool geo_placement_local_bounds(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,GeoRect2 *out);
#endif
