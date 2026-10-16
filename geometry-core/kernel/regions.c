#include "internal/regions.h"
#include <stdlib.h>
#include <string.h>

static const GeoRegionLoop *geo_region_loop(const GeoRegionDefinition *region, size_t loop)
{
    return loop ? &region->holes[loop - 1] : &region->outline;
}

static bool geo_region_definition_valid(const GeoRegionDefinition *region)
{
    if (!region || region->hole_count > GEO_REGION_MAX_HOLES) return false;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];
    for (size_t i = 0; i < region->hole_count; ++i)
        holes[i] = (GeoLoop2View){region->holes[i].v, region->holes[i].count};
    GeoRegionView view = {{region->outline.v, region->outline.count}, holes, region->hole_count};
    return geo_region_is_valid(&view);
}

GeoRegionStore *geo_regions_create(void) { return calloc(1, sizeof(GeoRegionStore)); }
GeoRegionStore *geo_regions_clone(const GeoRegionStore *source)
{
    if (!source) return NULL;
    GeoRegionStore *copy = malloc(sizeof *copy);
    if (copy) memcpy(copy, source, sizeof *copy);
    return copy;
}
void geo_regions_destroy(GeoRegionStore *store) { free(store); }
size_t geo_regions_count(const GeoRegionStore *store) { return store ? store->count : 0; }
const GeoRegionDefinition *geo_regions_at(const GeoRegionStore *store, size_t index)
{
    return store && index < store->count ? &store->regions[index] : NULL;
}
const GeoRegionDefinition *geo_regions_find(const GeoRegionStore *store, uint32_t id)
{
    if (!store) return NULL;
    for (size_t i = 0; i < store->count; ++i)
        if (store->regions[i].id == id) return &store->regions[i];
    return NULL;
}
bool geo_regions_put(GeoRegionStore *store, const GeoRegionDefinition *region)
{
    if (!store || !geo_region_definition_valid(region)) return false;
    size_t at = 0;
    while (at < store->count && store->regions[at].id != region->id) ++at;
    if (at >= GEO_REGION_CAPACITY) return false;
    /* Snapshot active fields before touching the store: region may be a
     * borrowed view of the very slot being replaced. Padding stays zero. */
    GeoRegionDefinition next;
    memset(&next, 0, sizeof next);
    next.id = region->id;
    next.hole_count = region->hole_count;
    next.outline.count = region->outline.count;
    memcpy(next.outline.v, region->outline.v, next.outline.count * sizeof next.outline.v[0]);
    for (size_t i = 0; i < next.hole_count; ++i) {
        next.holes[i].count = region->holes[i].count;
        memcpy(next.holes[i].v, region->holes[i].v, next.holes[i].count * sizeof next.holes[i].v[0]);
    }
    memcpy(&store->regions[at], &next, sizeof next);
    if (at == store->count) ++store->count;
    return true;
}
bool geo_regions_remove(GeoRegionStore *store, uint32_t id)
{
    if (!store) return false;
    size_t at = 0;
    while (at < store->count && store->regions[at].id != id) ++at;
    if (at == store->count) return false;
    memmove(store->regions + at, store->regions + at + 1, (store->count - at - 1) * sizeof *store->regions);
    memset(&store->regions[--store->count], 0, sizeof *store->regions);
    return true;
}

size_t geo_region_keys_count(const GeoRegionStore *store) { return store ? store->key_count : 0; }
const GeoRegionKeys *geo_region_keys_at(const GeoRegionStore *store, size_t index)
{
    return store && index < store->key_count ? &store->keys[index] : NULL;
}
const GeoRegionKeys *geo_region_keys_find(const GeoRegionStore *store, uint32_t id)
{
    if (!store) return NULL;
    for (size_t i = 0; i < store->key_count; ++i)
        if (store->keys[i].boundary_id == id) return &store->keys[i];
    return NULL;
}
bool geo_region_keys_has(const GeoRegionKeys *keys, uint32_t key)
{
    if (!keys || !key) return false;
    for (size_t l = 0; l < keys->loop_count; ++l)
        for (size_t i = 0; i < keys->counts[l]; ++i)
            if (keys->keys[l][i] == key) return true;
    return false;
}
bool geo_region_keys_valid(const GeoRegionDefinition *b, const GeoRegionKeys *keys)
{
    if (!b || !keys || keys->boundary_id != b->id || b->hole_count > GEO_REGION_MAX_HOLES ||
        keys->loop_count != b->hole_count + 1) return false;
    for (size_t l = 0; l < keys->loop_count; ++l) {
        const GeoRegionLoop *loop = geo_region_loop(b, l);
        if (loop->count > GEO_LOOP_MAX_VERTICES || keys->counts[l] != loop->count) return false;
        for (size_t i = 0; i < keys->counts[l]; ++i) {
            uint32_t key = keys->keys[l][i];
            if (!key || (keys->next_key && key >= keys->next_key)) return false;
            for (size_t ol = 0; ol <= l; ++ol) {
                size_t stop = ol == l ? i : keys->counts[ol];
                for (size_t oi = 0; oi < stop; ++oi)
                    if (keys->keys[ol][oi] == key) return false;
            }
        }
    }
    return true;
}
bool geo_region_keys_put(GeoRegionStore *store, const GeoRegionKeys *keys)
{
    if (!store || !keys || !keys->loop_count || keys->loop_count > GEO_REGION_MAX_HOLES + 1) return false;
    /* Validate the same table invariants without requiring this store to own
     * the caller's geometry yet. Geometry-count agreement is explicit below. */
    GeoRegionDefinition shape;
    memset(&shape, 0, sizeof shape);
    shape.id = keys->boundary_id;
    shape.hole_count = keys->loop_count - 1;
    shape.outline.count = keys->counts[0];
    for (size_t l = 1; l < keys->loop_count; ++l) shape.holes[l - 1].count = keys->counts[l];
    if (!geo_region_keys_valid(&shape, keys)) return false;
    size_t at = 0;
    while (at < store->key_count && store->keys[at].boundary_id != keys->boundary_id) ++at;
    if (at >= GEO_REGION_CAPACITY) return false;
    GeoRegionKeys next;
    memset(&next, 0, sizeof next);
    next.boundary_id = keys->boundary_id;
    next.loop_count = keys->loop_count;
    next.next_key = keys->next_key;
    for (size_t l = 0; l < next.loop_count; ++l) {
        next.counts[l] = keys->counts[l];
        memcpy(next.keys[l], keys->keys[l], next.counts[l] * sizeof next.keys[l][0]);
    }
    memcpy(&store->keys[at], &next, sizeof next);
    if (at == store->key_count) ++store->key_count;
    return true;
}
bool geo_region_keys_remove(GeoRegionStore *store, uint32_t id)
{
    if (!store) return false;
    size_t at = 0;
    while (at < store->key_count && store->keys[at].boundary_id != id) ++at;
    if (at == store->key_count) return false;
    memmove(store->keys + at, store->keys + at + 1, (store->key_count - at - 1) * sizeof *store->keys);
    memset(&store->keys[--store->key_count], 0, sizeof *store->keys);
    return true;
}
bool geo_region_keys_initialize(GeoRegionStore *store, const GeoRegionDefinition *b)
{
    if (!store || !b) return false;
    const GeoRegionKeys *existing = geo_region_keys_find(store, b->id);
    if (existing) return geo_region_keys_valid(b, existing);
    if (b->hole_count > GEO_REGION_MAX_HOLES || store->key_count >= GEO_REGION_CAPACITY) return false;
    GeoRegionKeys keys;
    memset(&keys, 0, sizeof keys);
    keys.boundary_id = b->id;
    keys.loop_count = b->hole_count + 1;
    keys.next_key = 1;
    for (size_t l = 0; l < keys.loop_count; ++l) {
        keys.counts[l] = geo_region_loop(b, l)->count;
        if (keys.counts[l] > GEO_LOOP_MAX_VERTICES) return false;
        for (size_t i = 0; i < keys.counts[l]; ++i) keys.keys[l][i] = keys.next_key++;
    }
    if (!geo_region_keys_valid(b, &keys)) return false;
    return geo_region_keys_put(store, &keys);
}
bool geo_region_vertex_by_key(const GeoRegionDefinition *b, const GeoRegionKeys *keys,
    uint32_t key, GeoPoint2 *out)
{
    if (!key || !geo_region_keys_valid(b, keys)) return false;
    for (size_t l = 0; l < keys->loop_count; ++l)
        for (size_t i = 0; i < keys->counts[l]; ++i)
            if (keys->keys[l][i] == key) {
                if (out) *out = geo_region_loop(b, l)->v[i];
                return true;
            }
    return false;
}
bool geo_region_keys_same(const GeoRegionKeys *a, const GeoRegionKeys *b)
{
    if (!a || !b) return false;
    if (a->boundary_id != b->boundary_id || a->loop_count != b->loop_count || a->next_key != b->next_key) return false;
    for (size_t l = 0; l < a->loop_count; ++l) {
        if (a->counts[l] != b->counts[l]) return false;
        for (size_t i = 0; i < a->counts[l]; ++i) if (a->keys[l][i] != b->keys[l][i]) return false;
    }
    return true;
}

GeoRegionKeyStatus geo_region_keys_reconcile(
    const GeoRegionDefinition *b, GeoRegionKeys *keys,
    const GeoRegionDefinition *old_boundary, const GeoRegionKeys *old,
    bool keyed)
{
    if (!b || !keys) return GEO_REGION_KEYS_INVALID;
    if (old && (!geo_region_keys_valid(old_boundary, old) || old->boundary_id != b->id))
        return GEO_REGION_KEYS_PREVIOUS_INVALID;
    if (old && !keyed) {
        /* Always derive from the transaction baseline: repeated validation of
         * one candidate must not allocate another set of keys. */
        GeoRegionKeys remapped;
        memset(&remapped, 0, sizeof remapped);
        remapped.boundary_id = b->id;
        remapped.loop_count = b->hole_count + 1;
        remapped.next_key = old->next_key;
        if (b->hole_count > GEO_REGION_MAX_HOLES) return GEO_REGION_KEYS_TOO_MANY_LOOPS;
        for (size_t l = 0; l < remapped.loop_count; ++l) {
            remapped.counts[l] = geo_region_loop(b, l)->count;
            if (remapped.counts[l] > GEO_LOOP_MAX_VERTICES) return GEO_REGION_KEYS_TOO_MANY_VERTICES;
        }
        for (size_t ol = 0; ol < old->loop_count; ++ol) for (size_t oi = 0; oi < old->counts[ol]; ++oi) {
            GeoPoint2 p = geo_region_loop(old_boundary, ol)->v[oi];
            size_t matches = 0, match_loop = 0, match_index = 0;
            for (size_t l = 0; l < remapped.loop_count; ++l) {
                const GeoRegionLoop *loop = geo_region_loop(b, l);
                for (size_t i = 0; i < loop->count; ++i)
                    if (loop->v[i].u == p.u && loop->v[i].v == p.v) {
                        ++matches; match_loop = l; match_index = i;
                    }
            }
            if (matches != 1 || remapped.keys[match_loop][match_index]) return GEO_REGION_KEYS_IDENTITY_CHANGED;
            remapped.keys[match_loop][match_index] = old->keys[ol][oi];
        }
        for (size_t l = 0; l < remapped.loop_count; ++l) for (size_t i = 0; i < remapped.counts[l]; ++i) {
            if (remapped.keys[l][i]) continue;
            if (!remapped.next_key) return GEO_REGION_KEYS_EXHAUSTED;
            remapped.keys[l][i] = remapped.next_key;
            remapped.next_key = remapped.next_key == UINT32_MAX ? 0 : remapped.next_key + 1;
        }
        memcpy(keys, &remapped, sizeof remapped);
    }
    if (!geo_region_keys_valid(b, keys)) return GEO_REGION_KEYS_INVALID;
    if (old && keyed) {
        for (size_t l = 0; l < keys->loop_count; ++l) for (size_t i = 0; i < keys->counts[l]; ++i) {
            uint32_t key = keys->keys[l][i];
            if (!geo_region_keys_has(old, key) && (!old->next_key || key < old->next_key)) return GEO_REGION_KEYS_RETIRED_KEY;
        }
        if (!old->next_key ? keys->next_key != 0 : (keys->next_key && keys->next_key < old->next_key))
            return GEO_REGION_KEYS_HIGHWATER_BACKWARDS;
    }
    return GEO_REGION_KEYS_OK;
}
