/* H coordinates complete application snapshots. K receives only the explicitly
 * bound core stores and the evaluator; template/host bytes stay opaque here. */
#ifndef GEO_APP_CANDIDATE_H
#define GEO_APP_CANDIDATE_H
#ifndef GEO_KERNEL_CANDIDATE_H
#include "candidate.h"
#endif

typedef struct AppCandidate AppCandidate;
typedef bool (*AppCandidateEvaluate)(void *after,GeoEvalContext *,void *opaque);
typedef bool (*AppCandidateEqual)(const void *live,const void *before,void *opaque);
typedef void (*AppCandidatePublish)(void *live,const void *after,void *opaque);
typedef void (*AppCandidateDisposeState)(void *);

/* The caller owns two non-overlapping full-snapshot buffers for this handle's
 * entire lifetime. Both are initialized from live. A persistent preview keeps
 * these same buffers and this same handle until publish/discard. */
AppCandidate *app_candidate_create(void *before,void *after,const void *live,
    size_t snapshot_size,uint64_t candidate_id,uint64_t base_revision,const char *provider_stamp);
void app_candidate_destroy(AppCandidate *);
GeoCandidateStatus app_candidate_bind_core(AppCandidate *,const char *name,size_t offset,size_t size);
GeoCandidateStatus app_candidate_evaluate(AppCandidate *,AppCandidateEvaluate,void *opaque);
GeoCandidateStatus app_candidate_seal(AppCandidate *);
GeoCandidateStatus app_candidate_check(const AppCandidate *,const void *live,uint64_t revision,
    const char *provider_stamp,AppCandidateEqual,void *opaque);
/* A confirmation checks the previous seal, then revalidates this same snapshot
 * through a fresh resolver with the same candidate identity and bindings. */
GeoCandidateStatus app_candidate_reopen(AppCandidate *,const void *live,uint64_t revision,
    const char *provider_stamp,AppCandidateEqual,void *opaque);
/* publish cannot fail: all checks finish before its one complete-root replace.
 * The host callback may preserve presentation data according to its old policy. */
GeoCandidateStatus app_candidate_publish(AppCandidate *,void *live,uint64_t revision,
    const char *provider_stamp,AppCandidateEqual,AppCandidatePublish,void *opaque);
void app_candidate_discard(AppCandidate *);
const void *app_candidate_before(const AppCandidate *);
void *app_candidate_after(AppCandidate *);
GeoCandidate *app_candidate_core(const AppCandidate *);
/* Provider callback state belongs to this candidate, never to the live root.
 * It is disposed before re-evaluation or destruction, before the resolver dies. */
void app_candidate_set_evaluation_state(AppCandidate *,void *,AppCandidateDisposeState);
void *app_candidate_evaluation_state(const AppCandidate *);

#endif
