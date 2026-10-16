/* Ordered region membership and directional plane-slot consistency.
 * closed records six occupied normal slots, not a general solid proof. */
#ifndef GEO_KERNEL_ENCLOSURE_H
#define GEO_KERNEL_ENCLOSURE_H
#include "placements.h"

#define GEO_ENCLOSURE_CAPACITY 4
#define GEO_ENCLOSURE_MEMBER_CAPACITY 8

typedef struct {
    uint32_t id;
    uint32_t member_ids[GEO_ENCLOSURE_MEMBER_CAPACITY];
    size_t member_count;
    GeoCoord min[3],max[3];
    bool closed;
} GeoEnclosure;

typedef enum {
    GEO_ENCLOSURE_FAULT_NONE=0,
    GEO_ENCLOSURE_FAULT_MEMBER_COUNT,
    GEO_ENCLOSURE_FAULT_MISSING_REGION,
    GEO_ENCLOSURE_FAULT_DUPLICATE_REGION,
    GEO_ENCLOSURE_FAULT_NO_CARRIER,
    GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER,
    GEO_ENCLOSURE_FAULT_SLOT_TAKEN,
    GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH,
    GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,
    GEO_ENCLOSURE_FAULT_INVERTED
} GeoEnclosureFaultKind;
typedef struct {
    GeoEnclosureFaultKind kind;
    uint32_t member_id;
    int axis;
} GeoEnclosureFault;

typedef struct GeoEnclosureStore GeoEnclosureStore;
GeoEnclosureStore *geo_enclosures_create(void);
GeoEnclosureStore *geo_enclosures_clone(const GeoEnclosureStore *source);
void geo_enclosures_destroy(GeoEnclosureStore *store);
size_t geo_enclosures_count(const GeoEnclosureStore *store);
const GeoEnclosure *geo_enclosures_at(const GeoEnclosureStore *store,size_t index);
const GeoEnclosure *geo_enclosures_find(const GeoEnclosureStore *store,uint32_t id);
/* Borrow the inline array; stage/remove can change records or their order.
 * No returned pointer owns storage or survives destruction of the store. */
const GeoEnclosure *geo_enclosures_values(const GeoEnclosureStore *store);
/* Bounded POD upsert only: preserve supplied derived caches, even when the
 * member list is temporarily empty. Evaluation is a separate ordered step.
 * Replacements keep their index; new IDs append. Unused members and padding
 * are zeroed. Input may alias a stored record. Failure changes no bytes.
 * IDs include zero; membership may overlap between different enclosures. */
bool geo_enclosures_stage(GeoEnclosureStore *store,const GeoEnclosure *value);
/* Preserve remaining order and clear the removed tail; never cascade. */
bool geo_enclosures_remove(GeoEnclosureStore *store,uint32_t id);

/* Regions and frames must already satisfy the public bounded geometry
 * contract. Only explicit REGION_REF placements are carriers, including
 * region ID zero. RECT/REGION_SET inactive region_id bytes are not references.
 * The outer outline bbox supplies extents; holes do not shrink them.
 * Process members in input order, then final axis checks in X/Y/Z order.
 * Failure preserves out. Success preserves fault. Zero members succeed with
 * only id set and every other output byte zero. IDs may alias out storage.
 * Missing output/IDs or too many members report MEMBER_COUNT. */
bool geo_enclosure_evaluate(const GeoRegionStore *regions,const GeoPlacementStore *placements,
    uint32_t id,const uint32_t *member_ids,size_t member_count,
    GeoEnclosure *out,GeoEnclosureFault *fault);
/* Only a matching actual normal slot is a bound. min/max may instead come
 * from in-plane extents and must not substitute for this query. Scan member
 * order then placement order, returning the first matching slot; no unique
 * carrier validation is performed here. axis=0..2, slot=0 lower/1 upper.
 * Failure, including invalid arguments, leaves out unchanged. */
bool geo_enclosure_axis_bound(const GeoPlacementStore *placements,const GeoEnclosure *enclosure,
    int axis,int slot,GeoCoord *out);
#endif
