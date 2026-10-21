/* Owned plane-local line definitions and their explicitly evaluated caches.
 * Host text, provider namespaces, dependency policy and visible clipping are
 * outside this store. Returned guide pointers borrow the store's lifetime. */
#ifndef GEO_KERNEL_GUIDES_H
#define GEO_KERNEL_GUIDES_H
#include "datums.h"

#define GEO_GUIDE_CAPACITY 16
typedef enum { GEO_GUIDE_ALONG_U = 0, GEO_GUIDE_ALONG_V = 1 } GeoGuideDirection;
typedef enum { GEO_GUIDE_LOCAL = 0, GEO_GUIDE_DATUM = 1 } GeoGuideSource;
typedef struct {
    uint32_t id, placement_id;
    GeoGuideDirection direction; /* Definition for LOCAL, cache for DATUM. */
    GeoGuideSource source;
    uint32_t datum_id;
    bool resolved;
    GeoCoord offset;
    GeoLinearExpression expression; /* LOCAL only; owns every source key. */
} GeoGuide;

typedef struct GeoGuideStore GeoGuideStore;
typedef enum {
    GEO_GUIDE_OK = 0, GEO_GUIDE_INVALID, GEO_GUIDE_MISSING_FRAME,
    GEO_GUIDE_MISSING_DATUM, GEO_GUIDE_LINEAR_FAILED, GEO_GUIDE_DATUM_FAILED
} GeoGuideStatus;
typedef struct {
    GeoGuideStatus status;
    GeoLinearResult linear;
    GeoDatumIntersectionStatus intersection;
} GeoGuideResult;

GeoGuideStore *geo_guides_create(void);
GeoGuideStore *geo_guides_clone(const GeoGuideStore *store);
void geo_guides_destroy(GeoGuideStore *store);
size_t geo_guides_count(const GeoGuideStore *store);
const GeoGuide *geo_guides_at(const GeoGuideStore *store, size_t index);
const GeoGuide *geo_guides_values(const GeoGuideStore *store);
const GeoGuide *geo_guides_find(const GeoGuideStore *store, uint32_t id);
/* Copies explicit caches as well as definitions, allowing a definition edit
 * to retain the prior cache until evaluation. Fresh definitions supply zero
 * caches. Incomplete LOCAL prefixes remain evaluable for source diagnostics;
 * unused datum/expression fields and inactive storage are zeroed. */
bool geo_guides_put(GeoGuideStore *store, const GeoGuide *guide);
bool geo_guides_remove(GeoGuideStore *store, uint32_t id);
/* Clear resolved only; neither definitions nor attempted caches are cleared. */
void geo_guides_reset_resolved(GeoGuideStore *store);
/* LOCAL checks only frame presence, then evaluates the typed expression.
 * DATUM requires the matching datum and delegates geometric validation.
 * LOCAL failures leave the prior offset unchanged. DATUM RANGE writes the
 * attempted direction/offset. All failures leave resolved unchanged; only
 * success sets it true. Call reset_resolved separately when recomputing. */
GeoGuideResult geo_guides_evaluate(GeoGuideStore *store, size_t index,
    const GeoFrame *frame, const GeoDatum *datum, GeoLinearResolver resolve, void *state);
/* Same result/cache contract, using returned authored data for this identity.
 * Source kind must match the stored definition; change kind through put first.
 * Authored fields in the store are retained; DATUM direction is a cache. */
GeoGuideResult geo_guides_evaluate_definition(GeoGuideStore *store, size_t index,
    const GeoGuide *definition, const GeoFrame *frame, const GeoDatum *datum,
    GeoLinearResolver resolve, void *state);
#endif
