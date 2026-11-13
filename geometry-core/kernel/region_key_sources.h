/* Candidate-local vertex identities and coordinates. Ledger definitions own
 * no geometry; coordinate values consume the registered typed region source. */
#ifndef GEO_KERNEL_REGION_KEY_SOURCES_H
#define GEO_KERNEL_REGION_KEY_SOURCES_H
#include "regions.h"
#include "source.h"

typedef enum {
    GEO_REGION_KEY_SOURCE_LEDGER=1,
    GEO_REGION_KEY_SOURCE_COORDINATE=2
} GeoRegionKeySourceKind;
typedef struct {unsigned char bytes[16];} GeoRegionKeySourceKey;
typedef struct GeoRegionKeySources GeoRegionKeySources;

/* Four BE32 fields: kind, region id, vertex key, axis. Ledger keys use zero
 * vertex/axis fields. Region id zero is valid; coordinate axes are 0=u, 1=v.
 * Key zero may be described but cannot resolve a vertex. Failed decoding
 * changes none of its output arguments. */
GeoSourceRef geo_region_key_source_ref(GeoProviderToken,GeoRegionKeySourceKind,
    uint32_t region_id,uint32_t vertex_key,uint32_t axis,GeoRegionKeySourceKey *);
bool geo_region_key_source_decode(const GeoSourceRef *,GeoRegionKeySourceKind *,
    uint32_t *region_id,uint32_t *vertex_key,uint32_t *axis);

#define GEO_REGION_KEY_LEDGER_CONTENT_MAX (12+4*(GEO_REGION_MAX_HOLES+1)*(GEO_LOOP_MAX_VERTICES+1))
/* Canonical geometry.region-key-ledger/1 content: BE32 region id, next_key,
 * loop_count, then each loop's count and ordered active keys as BE32. Empty
 * unused storage and C padding are excluded. next_key=0 retains exhaustion.
 * Structural table validity is checked independently of any region geometry.
 * Encode returns zero on failure. On failure neither function changes its output. */
size_t geo_region_key_ledger_encode(const GeoRegionKeys *,void *,size_t);
bool geo_region_key_ledger_decode(const void *,size_t,GeoRegionKeys *);

/* Register before evaluation begins. Stores and upstream values belong to
 * this same candidate; registration and description perform no evaluation.
 * A graph reset removes registrations: destroy this handle and register a
 * fresh one for the next evaluation generation. */
GeoRegionKeySources *geo_region_key_sources_register(GeoEvalContext *,
    const GeoRegionStore *,GeoProviderToken key_token,GeoProviderToken region_token);
/* Enumerates every stored ledger, including one with no geometry consumer.
 * It neither requests coordinates nor validates ledger/geometry agreement. */
bool geo_region_key_sources_definitions(GeoRegionKeySources *);
/* Both coordinates must succeed before the caller's point changes. NULL out
 * checks existence/validity, like geo_region_vertex_by_key. */
bool geo_region_key_sources_vertex(GeoRegionKeySources *,uint32_t region_id,
    uint32_t vertex_key,GeoPoint2 *out);
/* No graph/store access. Either graph/handle destruction order is safe; no
 * further graph evaluation is allowed once its provider has been destroyed. */
void geo_region_key_sources_destroy(GeoRegionKeySources *);
#endif
