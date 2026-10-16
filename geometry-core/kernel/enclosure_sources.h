/* Same-candidate enclosure definitions, evaluated geometry and actual plane
 * slots. Membership identity never forces geometry or an enclosure result. */
#ifndef GEO_KERNEL_ENCLOSURE_SOURCES_H
#define GEO_KERNEL_ENCLOSURE_SOURCES_H
#include "enclosure.h"
#include "placement_sources.h"

typedef enum {
    GEO_ENCLOSURE_SOURCE_DEFINITION=1,
    GEO_ENCLOSURE_SOURCE_RESULT=2,
    GEO_ENCLOSURE_SOURCE_AXIS_BOUND=3
} GeoEnclosureSourceKind;
typedef struct {unsigned char bytes[7];} GeoEnclosureSourceKey;
typedef struct GeoEnclosureSources GeoEnclosureSources;

/* Key: kind, four-byte big-endian id, axis+1, slot+1. DEFINITION/RESULT
 * require axis=slot=-1. AXIS_BOUND requires axis=0..2 and slot=0..1.
 * Invalid arguments produce an invalid empty key; decode changes no output
 * on failure. Provider-token membership is checked by the provider itself. */
GeoSourceRef geo_enclosure_source_ref(GeoProviderToken,GeoEnclosureSourceKind,uint32_t,
    int axis,int slot,GeoEnclosureSourceKey *);
bool geo_enclosure_source_decode(const GeoSourceRef *,GeoEnclosureSourceKind *,uint32_t *,int *,int *);

GeoEnclosureSources *geo_enclosure_sources_register(GeoEvalContext *,const GeoEnclosureStore *,
    const GeoRegionStore *,const GeoPlacementStore *,GeoProviderToken enclosure_token,
    GeoProviderToken placement_token,GeoProviderToken region_token);
/* The caller owns an immutable candidate snapshot and its graph. The handle
 * owns canonical bytes and evaluated results; either destruction order is
 * safe, but no evaluation or borrowed view may follow handle destruction.
 * geo_eval_reset drops registrations: destroy this handle and register a new
 * one before further requests, even when the candidate identity is reused. */
void geo_enclosure_sources_destroy(GeoEnclosureSources *);
size_t geo_enclosure_sources_count(const GeoEnclosureSources *);
/* Enumerates raw member definitions. min/max/closed here are input caches,
 * not source values; use value() for evaluated geometry. */
const GeoEnclosure *geo_enclosure_sources_at(const GeoEnclosureSources *,size_t);

/* These helpers request the corresponding source in the same graph. Failure
 * leaves out unchanged. value() supplies a fault only for an actual enclosure
 * geometry failure; upstream/type/allocation failures and success preserve it.
 * axis_bound() keeps member/placement scan order and does not require RESULT. */
bool geo_enclosure_sources_value(GeoEnclosureSources *,uint32_t,GeoEnclosure *out,GeoEnclosureFault *);
bool geo_enclosure_sources_axis_bound(GeoEnclosureSources *,uint32_t,int axis,int slot,GeoCoord *out);

/* DEFINITION has schema geo.enclosure.members/1: u32 id, u32 member count,
 * then ordered u32 ids. RESULT has schema geo.enclosure.result/1: the same
 * prefix, three signed i64 minimums, three signed i64 maximums, then closed
 * as one byte. All integers are big endian; signed values use two's complement.
 * No cache, inactive member or struct-padding bytes enter a definition. */
#endif
