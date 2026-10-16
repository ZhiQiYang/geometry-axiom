#include "app_candidate.h"
#ifndef GEOMETRY_KERNEL_CODEC_H
#include "codec.h"
#endif
#include <stdlib.h>
#include <string.h>

struct AppCandidate {
    void *before,*after;
    size_t snapshot_size;
    GeoCandidate *core;
    char before_hash[65],after_hash[65];
    unsigned char *before_bytes,*after_bytes;
    bool sealed;
    void *evaluation_state;
    AppCandidateDisposeState dispose_state;
};
static bool app_candidate_overlap(const void *a,const void *b,size_t size)
{
    uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
    if(size>UINTPTR_MAX-x||size>UINTPTR_MAX-y)return true;
    return x<y+size&&y<x+size;
}
AppCandidate *app_candidate_create(void *before,void *after,const void *live,
    size_t size,uint64_t id,uint64_t revision,const char *stamp)
{
    if(!before||!after||!live||!size||app_candidate_overlap(before,after,size)||
       app_candidate_overlap(before,live,size)||app_candidate_overlap(after,live,size))return NULL;
    AppCandidate *candidate=calloc(1,sizeof *candidate);
    if(!candidate)return NULL;
    candidate->core=geo_candidate_create(id,revision,stamp);
    if(!candidate->core){free(candidate);return NULL;}
    candidate->before=before;candidate->after=after;candidate->snapshot_size=size;
    memcpy(before,live,size);memcpy(after,live,size);
    geo_sha256(before,size,candidate->before_hash);
    candidate->before_bytes=malloc(size);
    if(candidate->before_bytes)memcpy(candidate->before_bytes,before,size);
    return candidate;
}
void app_candidate_set_evaluation_state(AppCandidate *candidate,void *state,AppCandidateDisposeState dispose)
{
    if(!candidate)return;
    if(candidate->evaluation_state&&candidate->evaluation_state!=state&&candidate->dispose_state)
        candidate->dispose_state(candidate->evaluation_state);
    candidate->evaluation_state=state;candidate->dispose_state=dispose;
}
void *app_candidate_evaluation_state(const AppCandidate *candidate)
{return candidate?candidate->evaluation_state:NULL;}
void app_candidate_destroy(AppCandidate *candidate)
{
    if(!candidate)return;
    app_candidate_set_evaluation_state(candidate,NULL,NULL);
    geo_candidate_destroy(candidate->core);free(candidate->before_bytes);free(candidate->after_bytes);free(candidate);
}
GeoCandidateStatus app_candidate_bind_core(AppCandidate *candidate,const char *name,size_t offset,size_t size)
{
    if(!candidate||offset>candidate->snapshot_size||size>candidate->snapshot_size-offset)return GEO_CANDIDATE_INVALID;
    return geo_candidate_bind_state(candidate->core,name,(const unsigned char*)candidate->before+offset,
        (unsigned char*)candidate->after+offset,size);
}
static bool app_candidate_hash_matches(const void *,size_t,const char expected[65],const void *);
typedef struct {AppCandidate *candidate;AppCandidateEvaluate evaluate;void *opaque;} AppCandidateCall;
static bool app_candidate_call(void *opaque,GeoEvalContext *sources)
{
    AppCandidateCall *call=opaque;
    return call->evaluate(call->candidate->after,sources,call->opaque);
}
GeoCandidateStatus app_candidate_evaluate(AppCandidate *candidate,AppCandidateEvaluate evaluate,void *opaque)
{
    if(!candidate||!evaluate)return GEO_CANDIDATE_INVALID;
    if(candidate->sealed)return GEO_CANDIDATE_STATE;
    if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;
    app_candidate_set_evaluation_state(candidate,NULL,NULL);
    AppCandidateCall call={candidate,evaluate,opaque};
    GeoCandidateStatus status=geo_candidate_evaluate(candidate->core,app_candidate_call,&call);
    if(status==GEO_CANDIDATE_OK){
        geo_sha256(candidate->after,candidate->snapshot_size,candidate->after_hash);
        if(!candidate->after_bytes)candidate->after_bytes=malloc(candidate->snapshot_size);
        if(candidate->after_bytes)memcpy(candidate->after_bytes,candidate->after,candidate->snapshot_size);
    }
    return status;
}
static bool app_candidate_hash_matches(const void *bytes,size_t size,const char expected[65],const void *hashed_bytes)
{
    /* The private copy contains exactly the bytes used for expected. This is
     * an exact cache-key comparison, never a weaker digest. Any changed byte
     * takes the original SHA path; allocation failure merely disables caching. */
    if(hashed_bytes&&!memcmp(bytes,hashed_bytes,size))return true;
    char actual[65];geo_sha256(bytes,size,actual);return !strcmp(actual,expected);
}
GeoCandidateStatus app_candidate_seal(AppCandidate *candidate)
{
    if(!candidate)return GEO_CANDIDATE_INVALID;
    if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;
    if(!app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;
    GeoCandidateStatus status=geo_candidate_seal(candidate->core);
    if(status!=GEO_CANDIDATE_OK)return status;
    candidate->sealed=true;return GEO_CANDIDATE_OK;
}
GeoCandidateStatus app_candidate_check(const AppCandidate *candidate,const void *live,uint64_t revision,
    const char *stamp,AppCandidateEqual equal,void *opaque)
{
    if(!candidate||!live||!equal)return GEO_CANDIDATE_INVALID;
    if(!candidate->sealed)return GEO_CANDIDATE_STATE;
    GeoCandidateStatus status=geo_candidate_check(candidate->core,revision,stamp);
    if(status!=GEO_CANDIDATE_OK)return status;
    if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes)||
       !app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;
    return equal(live,candidate->before,opaque)?GEO_CANDIDATE_OK:GEO_CANDIDATE_STATE_CHANGED;
}
GeoCandidateStatus app_candidate_publish(AppCandidate *candidate,void *live,uint64_t revision,
    const char *stamp,AppCandidateEqual equal,AppCandidatePublish publish,void *opaque)
{
    if(!publish)return GEO_CANDIDATE_INVALID;
    GeoCandidateStatus status=app_candidate_check(candidate,live,revision,stamp,equal,opaque);
    if(status!=GEO_CANDIDATE_OK)return status;
    status=geo_candidate_mark_published(candidate->core,revision,stamp);
    if(status!=GEO_CANDIDATE_OK)return status;
    publish(live,candidate->after,opaque);return GEO_CANDIDATE_OK;
}
GeoCandidateStatus app_candidate_reopen(AppCandidate *candidate,const void *live,uint64_t revision,
    const char *stamp,AppCandidateEqual equal,void *opaque)
{
    GeoCandidateStatus status=app_candidate_check(candidate,live,revision,stamp,equal,opaque);
    if(status!=GEO_CANDIDATE_OK)return status;
    app_candidate_set_evaluation_state(candidate,NULL,NULL);
    status=geo_candidate_reopen(candidate->core,revision,stamp);
    if(status==GEO_CANDIDATE_OK)candidate->sealed=false;
    return status;
}
void app_candidate_discard(AppCandidate *candidate)
{
    if(!candidate)return;
    app_candidate_set_evaluation_state(candidate,NULL,NULL);
    geo_candidate_discard(candidate->core);candidate->sealed=false;
}
const void *app_candidate_before(const AppCandidate *candidate){return candidate?candidate->before:NULL;}
void *app_candidate_after(AppCandidate *candidate){return candidate?candidate->after:NULL;}
GeoCandidate *app_candidate_core(const AppCandidate *candidate){return candidate?candidate->core:NULL;}
