#ifndef GEO_KERNEL_CANDIDATE_H
#define GEO_KERNEL_CANDIDATE_H
#include "source.h"

typedef struct GeoCandidate GeoCandidate;
typedef enum {
    GEO_CANDIDATE_OPEN=0, GEO_CANDIDATE_EVALUATING, GEO_CANDIDATE_EVALUATED,
    GEO_CANDIDATE_SEALED, GEO_CANDIDATE_PUBLISHED, GEO_CANDIDATE_REJECTED,
    GEO_CANDIDATE_DISCARDED
} GeoCandidateState;
typedef enum {
    GEO_CANDIDATE_OK=0, GEO_CANDIDATE_INVALID, GEO_CANDIDATE_STATE,
    GEO_CANDIDATE_MEMORY, GEO_CANDIDATE_DUPLICATE, GEO_CANDIDATE_OVERLAP,
    GEO_CANDIDATE_REVISION_CHANGED, GEO_CANDIDATE_PROVIDER_CHANGED,
    GEO_CANDIDATE_STATE_CHANGED, GEO_CANDIDATE_EVALUATION_FAILED
} GeoCandidateStatus;
typedef bool (*GeoCandidateEvaluate)(void *,GeoEvalContext *);

/* The exact, nonempty provider stamp is copied. The candidate owns its source
 * context, not the caller's buffers. It never copies data into a live root. */
GeoCandidate *geo_candidate_create(uint64_t candidate_id,uint64_t base_revision,
                                  const char *provider_stamp);
void geo_candidate_destroy(GeoCandidate *);
/* Bind actual POD stores before the first evaluation. Names are opaque,
 * nonempty and copied. All before/current ranges must be nonempty, distinct
 * and disjoint from all other bindings. They must remain alive until destroy.
 * Initialize padding deterministically; pointed-to data is not covered by a
 * POD hash and must be bound separately. Before bytes stay immutable. */
GeoCandidateStatus geo_candidate_bind_state(GeoCandidate *,const char *name,
                                           const void *before,void *current,size_t size);
/* OPEN, EVALUATED and REJECTED may be evaluated with a fresh resolver carrying
 * the same candidate id and revision. The opaque argument may be an assembly
 * wrapper; it and every provider must use this candidate's current buffers,
 * never a live root or a different candidate. The callback must finish all
 * mutations before returning. Neither candidate nor context may be destroyed
 * from a callback. This API is single-threaded. */
GeoCandidateStatus geo_candidate_evaluate(GeoCandidate *,GeoCandidateEvaluate,void *);
/* Seal only a successful, unchanged evaluation. Provider metadata is captured
 * from the actual resolver. Sealing freezes source registration/evaluation. */
GeoCandidateStatus geo_candidate_seal(GeoCandidate *);
GeoCandidateStatus geo_candidate_check(const GeoCandidate *,uint64_t live_revision,
                                      const char *provider_stamp);
/* Rechecks the seal, then marks authorization for the caller's one complete
 * root publication. No buffers, history or identifiers are copied/advanced. */
GeoCandidateStatus geo_candidate_mark_published(GeoCandidate *,uint64_t live_revision,
                                               const char *provider_stamp);
/* Reopen a checked SEALED candidate for revalidation; id, revision, stamp and
 * bindings stay fixed. Old resolver views expire. Bindings cannot be added. */
GeoCandidateStatus geo_candidate_reopen(GeoCandidate *,uint64_t live_revision,
                                       const char *provider_stamp);
/* Terminal cancellation, allowed before publication and outside evaluation. */
GeoCandidateStatus geo_candidate_discard(GeoCandidate *);
/* Borrowed context, valid only until reevaluation, reopen, discard or destroy.
 * Do not destroy it. After seal use only the resolver's read-only operations. */
GeoEvalContext *geo_candidate_sources(const GeoCandidate *);
GeoCandidateState geo_candidate_state(const GeoCandidate *);
uint64_t geo_candidate_id(const GeoCandidate *);
uint64_t geo_candidate_base_revision(const GeoCandidate *);
#endif
