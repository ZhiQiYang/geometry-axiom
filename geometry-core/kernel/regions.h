/* Owned, ordered region geometry and region-local vertex identities.
 * Regions carry no host kind, edge policy, placement or binding metadata.
 * Unused storage is zeroed; all returned definition/key pointers are borrowed. */
#ifndef GEO_KERNEL_REGIONS_H
#define GEO_KERNEL_REGIONS_H
#include "geometry.h"

#define GEO_REGION_CAPACITY 16
typedef struct {
    GeoPoint2 v[GEO_LOOP_MAX_VERTICES];
    size_t count;
} GeoRegionLoop;
typedef struct {
    uint32_t id;
    GeoRegionLoop outline;
    GeoRegionLoop holes[GEO_REGION_MAX_HOLES];
    size_t hole_count;
} GeoRegionDefinition;

/* Field order retains the product's existing vertex-table representation.
 * next_key == 0 means the uint32 allocation space has been exhausted. */
typedef struct {
    uint32_t boundary_id;
    size_t loop_count, counts[GEO_REGION_MAX_HOLES + 1];
    uint32_t keys[GEO_REGION_MAX_HOLES + 1][GEO_LOOP_MAX_VERTICES];
    uint32_t next_key;
} GeoRegionKeys;

typedef struct GeoRegionStore GeoRegionStore;
GeoRegionStore *geo_regions_create(void);
GeoRegionStore *geo_regions_clone(const GeoRegionStore *source);
void geo_regions_destroy(GeoRegionStore *store);
size_t geo_regions_count(const GeoRegionStore *store);
const GeoRegionDefinition *geo_regions_at(const GeoRegionStore *store, size_t index);
const GeoRegionDefinition *geo_regions_find(const GeoRegionStore *store, uint32_t id);
bool geo_regions_put(GeoRegionStore *store, const GeoRegionDefinition *region);
/* Geometry and identity storage are independent. Removal does not cascade;
 * consumers apply their dependency checks and explicitly remove identities. */
bool geo_regions_remove(GeoRegionStore *store, uint32_t id);

size_t geo_region_keys_count(const GeoRegionStore *store);
const GeoRegionKeys *geo_region_keys_at(const GeoRegionStore *store, size_t index);
const GeoRegionKeys *geo_region_keys_find(const GeoRegionStore *store, uint32_t id);
/* Structural key-table validity only. Geometry matching and retained-key
 * policy are checked against explicit definitions by the functions below. */
bool geo_region_keys_put(GeoRegionStore *store, const GeoRegionKeys *keys);
bool geo_region_keys_remove(GeoRegionStore *store, uint32_t id);
bool geo_region_keys_initialize(GeoRegionStore *store, const GeoRegionDefinition *region);
bool geo_region_keys_valid(const GeoRegionDefinition *region, const GeoRegionKeys *keys);
/* has/same require bounded table counts, as supplied by this store. */
bool geo_region_keys_has(const GeoRegionKeys *keys, uint32_t key);
bool geo_region_keys_same(const GeoRegionKeys *a, const GeoRegionKeys *b);
bool geo_region_vertex_by_key(const GeoRegionDefinition *region, const GeoRegionKeys *keys,
    uint32_t key, GeoPoint2 *out);

typedef enum {
    GEO_REGION_KEYS_OK = 0,
    GEO_REGION_KEYS_INVALID,
    GEO_REGION_KEYS_PREVIOUS_INVALID,
    GEO_REGION_KEYS_TOO_MANY_LOOPS,
    GEO_REGION_KEYS_TOO_MANY_VERTICES,
    GEO_REGION_KEYS_IDENTITY_CHANGED,
    GEO_REGION_KEYS_EXHAUSTED,
    GEO_REGION_KEYS_RETIRED_KEY,
    GEO_REGION_KEYS_HIGHWATER_BACKWARDS
} GeoRegionKeyStatus;

/* Reconcile one table against the transaction baseline, never a previous
 * reconciliation result. Ordinary changes match every old vertex at exactly
 * one current coordinate; keyed changes retain explicit identity assignment.
 * Geometry validity, deletion/dependency policy and hash guards are separate.
 * The caller owns keys and publishes it through put only when appropriate. */
GeoRegionKeyStatus geo_region_keys_reconcile(
    const GeoRegionDefinition *current, GeoRegionKeys *keys,
    const GeoRegionDefinition *before, const GeoRegionKeys *old_keys,
    bool keyed_update);
#endif
