/* Candidate-local ordered contact queries. Geometry and already-placed member
 * facts are read through the same source graph by the facts callback; the W
 * collection evaluator alone runs the existing contact order/dedup policy. */
#ifndef GEOMETRY_WOODWORKING_CONTACT_SOURCES_H
#define GEOMETRY_WOODWORKING_CONTACT_SOURCES_H
#include "contact_world.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif

typedef struct {
    uint32_t placement_id;
    bool along_v;
    const WoodMember *exclude; /* Original candidate address, never an ID copy. */
} WoodContactSourceRequest;
typedef struct {
    WoodBoundaryRegion regions[WOOD_CONTACT_COMPONENT_CAPACITY];
    size_t region_count;
    WoodContactMemberFact members[WOOD_CONTACT_MEMBER_CAPACITY];
    size_t member_count;
} WoodContactSourceFacts;
/* The evaluator owns and zero-initializes facts for this call. Fill its inline
 * regions/member facts using actual values from graph. Member pointers borrow
 * the original candidate; do not force BOX evaluation for unplaced members.
 * The callback and user remain bound to this candidate until handle teardown. */
typedef bool (*WoodContactSourceFactsCallback)(void *,GeoEvalContext *,
    const WoodContactSourceRequest *,WoodContactSourceFacts *);

typedef enum { WOOD_CONTACT_SOURCE_COLLECTION=1,WOOD_CONTACT_SOURCE_FEATURE=2 } WoodContactSourceKind;
typedef struct { unsigned char bytes[17]; } WoodContactSourceKey;
typedef struct WoodContactSources WoodContactSources;

GeoSourceRef wood_contact_source_ref(GeoProviderToken,WoodContactSourceKind,uint64_t query_id,
    uint64_t feature_index,WoodContactSourceKey *);
bool wood_contact_source_decode(const GeoSourceRef *,WoodContactSourceKind *,uint64_t *,uint64_t *);
/* Register before the graph's first request. H assigns token 16; the namespace
 * is always wood.contact. Creating a handle reads no candidate facts. */
WoodContactSources *wood_contact_sources_create(GeoEvalContext *,GeoProviderToken,
    WoodContactSourceFactsCallback,void *);
/* Each call owns a copied request and a new query identity, even when arguments
 * repeat. Capacity is passed to the old collector BEFORE its sort/dedup pass.
 * cap==0 still evaluates the collection and keeps its dependencies. Empty is
 * success with count==0; failure leaves both the output array and count intact.
 * A nonzero cap requires out. Graph and original member pointers stay alive
 * for evaluation. The graph must not be reset while this handle is in use. */
bool wood_contact_sources_collect(WoodContactSources *,const WoodContactSourceRequest *,
    WoodStopFace *out,size_t cap,size_t *count);
/* Both graph/handle destruction orders are safe. After handle destruction the
 * graph may only be destroyed; its provider and borrowed values are expired. */
void wood_contact_sources_destroy(WoodContactSources *);
#endif
