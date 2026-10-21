#include "candidate.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>

typedef struct {
    char *name;
    const void *before;
    void *current;
    size_t size;
    char before_hash[65],current_hash[65];
    unsigned char *before_bytes,*current_bytes;
} GeoCandidateBinding;
struct GeoCandidate {
    uint64_t candidate_id,base_revision,evaluation_generation;
    char *provider_stamp;
    GeoCandidateState state;
    GeoCandidateBinding *bindings;
    size_t binding_count;
    bool bindings_closed;
    bool deferred_state_sha;
    GeoEvalContext *sources;
    char providers_hash[65];
};

static char *geo_candidate_copy_text(const char *text)
{
    if(!text||!*text)return NULL;
    size_t length=strlen(text);
    if(length==SIZE_MAX)return NULL;
    char *copy=malloc(length+1);
    if(copy)memcpy(copy,text,length+1);
    return copy;
}
GeoCandidate *geo_candidate_create(uint64_t candidate_id,uint64_t base_revision,
                                  const char *provider_stamp)
{
    char *stamp=geo_candidate_copy_text(provider_stamp);
    if(!stamp)return NULL;
    GeoCandidate *candidate=calloc(1,sizeof *candidate);
    if(!candidate){free(stamp);return NULL;}
    candidate->candidate_id=candidate_id;candidate->base_revision=base_revision;
    candidate->provider_stamp=stamp;candidate->state=GEO_CANDIDATE_OPEN;
    return candidate;
}
GeoCandidate *geo_candidate_create_deferred_sha(uint64_t candidate_id,uint64_t base_revision,
                                               const char *provider_stamp)
{
    GeoCandidate *candidate=geo_candidate_create(candidate_id,base_revision,provider_stamp);
    if(candidate)candidate->deferred_state_sha=true;
    return candidate;
}
void geo_candidate_destroy(GeoCandidate *candidate)
{
    if(!candidate)return;
    geo_eval_destroy(candidate->sources);
    for(size_t i=0;i<candidate->binding_count;++i){free(candidate->bindings[i].name);free(candidate->bindings[i].before_bytes);free(candidate->bindings[i].current_bytes);}
    free(candidate->bindings);free(candidate->provider_stamp);free(candidate);
}
static bool geo_candidate_range(const void *pointer,size_t size,uintptr_t *start,uintptr_t *end)
{
    if(!pointer||!size)return false;
    *start=(uintptr_t)pointer;
    if(size>UINTPTR_MAX-*start)return false;
    *end=*start+(uintptr_t)size;
    return true;
}
static bool geo_candidate_ranges_overlap(uintptr_t a,uintptr_t ae,uintptr_t b,uintptr_t be)
{return a<be&&b<ae;}
GeoCandidateStatus geo_candidate_bind_state(GeoCandidate *candidate,const char *name,
                                           const void *before,void *current,size_t size)
{
    if(!candidate||!name||!*name)return GEO_CANDIDATE_INVALID;
    if(candidate->state!=GEO_CANDIDATE_OPEN||candidate->bindings_closed)return GEO_CANDIDATE_STATE;
    uintptr_t b,be,c,ce;
    if(!geo_candidate_range(before,size,&b,&be)||!geo_candidate_range(current,size,&c,&ce))return GEO_CANDIDATE_INVALID;
    if(geo_candidate_ranges_overlap(b,be,c,ce))return GEO_CANDIDATE_OVERLAP;
    for(size_t i=0;i<candidate->binding_count;++i){
        const GeoCandidateBinding *binding=&candidate->bindings[i];
        if(!strcmp(name,binding->name))return GEO_CANDIDATE_DUPLICATE;
        uintptr_t ob=(uintptr_t)binding->before,oc=(uintptr_t)binding->current;
        uintptr_t obe=ob+(uintptr_t)binding->size,oce=oc+(uintptr_t)binding->size;
        if(geo_candidate_ranges_overlap(b,be,ob,obe)||geo_candidate_ranges_overlap(b,be,oc,oce)||
           geo_candidate_ranges_overlap(c,ce,ob,obe)||geo_candidate_ranges_overlap(c,ce,oc,oce))return GEO_CANDIDATE_OVERLAP;
    }
    if(candidate->binding_count>=SIZE_MAX/sizeof *candidate->bindings)return GEO_CANDIDATE_MEMORY;
    char *copy=geo_candidate_copy_text(name);
    if(!copy)return GEO_CANDIDATE_MEMORY;
    GeoCandidateBinding *bindings=realloc(candidate->bindings,(candidate->binding_count+1)*sizeof *bindings);
    if(!bindings){free(copy);return GEO_CANDIDATE_MEMORY;}
    candidate->bindings=bindings;
    GeoCandidateBinding *binding=&bindings[candidate->binding_count++];
    memset(binding,0,sizeof *binding);binding->name=copy;
    binding->before=before;binding->current=current;binding->size=size;
    binding->before_bytes=malloc(size);
    if(binding->before_bytes)memcpy(binding->before_bytes,before,size);
    if(!candidate->deferred_state_sha||!binding->before_bytes)
        geo_sha256(before,size,binding->before_hash);
    else binding->before_hash[0]='\0';
    return GEO_CANDIDATE_OK;
}
static bool geo_candidate_digest_matches(const void *bytes,size_t size,const char expected[65],const void *hashed_bytes)
{
    if(hashed_bytes&&!memcmp(bytes,hashed_bytes,size))return true;
    char hash[65],saved_expected[65];
    if(hashed_bytes&&!expected[0]){
        geo_sha256(hashed_bytes,size,saved_expected);expected=saved_expected;
    }
    geo_sha256(bytes,size,hash);
    return !strcmp(hash,expected);
}
static GeoCandidateStatus geo_candidate_check_state(const GeoCandidate *candidate,bool include_current)
{
    for(size_t i=0;i<candidate->binding_count;++i){
        const GeoCandidateBinding *binding=&candidate->bindings[i];
        if(!geo_candidate_digest_matches(binding->before,binding->size,binding->before_hash,binding->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;
        if(include_current){
            if(!geo_candidate_digest_matches(binding->current,binding->size,binding->current_hash,binding->current_bytes))return GEO_CANDIDATE_STATE_CHANGED;
        }
    }
    return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_evaluate(GeoCandidate *candidate,GeoCandidateEvaluate evaluate,void *state)
{
    if(!candidate||!evaluate)return GEO_CANDIDATE_INVALID;
    if(candidate->state!=GEO_CANDIDATE_OPEN&&candidate->state!=GEO_CANDIDATE_EVALUATED&&
       candidate->state!=GEO_CANDIDATE_REJECTED)return GEO_CANDIDATE_STATE;
    if(candidate->evaluation_generation==UINT64_MAX)return GEO_CANDIDATE_STATE;
    candidate->bindings_closed=true;
    GeoCandidateStatus status=geo_candidate_check_state(candidate,false);
    if(status!=GEO_CANDIDATE_OK){candidate->state=GEO_CANDIDATE_REJECTED;return status;}
    GeoEvalContext *sources=geo_eval_create(candidate->candidate_id,candidate->base_revision);
    if(!sources){candidate->state=GEO_CANDIDATE_REJECTED;return GEO_CANDIDATE_MEMORY;}
    geo_eval_destroy(candidate->sources);candidate->sources=sources;
    candidate->state=GEO_CANDIDATE_EVALUATING;
    ++candidate->evaluation_generation;
    bool ok=evaluate(state,sources);
    candidate->state=ok?GEO_CANDIDATE_EVALUATED:GEO_CANDIDATE_REJECTED;
    if(!ok)return GEO_CANDIDATE_EVALUATION_FAILED;
    for(size_t i=0;i<candidate->binding_count;++i){
        GeoCandidateBinding *binding=&candidate->bindings[i];
        if(!binding->current_bytes)binding->current_bytes=malloc(binding->size);
        if(binding->current_bytes)memcpy(binding->current_bytes,binding->current,binding->size);
        if(!candidate->deferred_state_sha||!binding->current_bytes)
            geo_sha256(binding->current,binding->size,binding->current_hash);
        else binding->current_hash[0]='\0';
    }
    return GEO_CANDIDATE_OK;
}
static bool geo_candidate_add_size(size_t *total,size_t amount)
{
    if(amount>SIZE_MAX-*total)return false;
    *total+=amount;return true;
}
static void geo_candidate_encode_u64(unsigned char **cursor,uint64_t value)
{
    for(unsigned i=0;i<8;++i)(*cursor)[i]=(unsigned char)(value>>(56-8*i));
    *cursor+=8;
}
static void geo_candidate_encode_text(unsigned char **cursor,const char *text)
{
    size_t length=strlen(text);geo_candidate_encode_u64(cursor,(uint64_t)length);
    memcpy(*cursor,text,length);*cursor+=length;
}
/* Canonical registration-order metadata: BE64 count, then BE64 token and two
 * BE64 byte lengths followed by exact namespace/fingerprint bytes. Delimiters,
 * truncation and native struct padding cannot conflate two registries. */
static GeoCandidateStatus geo_candidate_provider_hash(const GeoEvalContext *sources,char out[65])
{
    if(!sources)return GEO_CANDIDATE_INVALID;
    size_t count=geo_eval_provider_count(sources),size=8;
    if(count>UINT64_MAX)return GEO_CANDIDATE_MEMORY;
    for(size_t i=0;i<count;++i){
        const GeoSourceProvider *provider=geo_eval_provider_at(sources,i);
        if(!provider||!provider->name_space||!provider->implementation_fingerprint)return GEO_CANDIDATE_PROVIDER_CHANGED;
        size_t name_size=strlen(provider->name_space),fingerprint_size=strlen(provider->implementation_fingerprint);
        if(name_size>UINT64_MAX||fingerprint_size>UINT64_MAX||!geo_candidate_add_size(&size,24)||
           !geo_candidate_add_size(&size,name_size)||!geo_candidate_add_size(&size,fingerprint_size))return GEO_CANDIDATE_MEMORY;
    }
    unsigned char *bytes=malloc(size);
    if(!bytes)return GEO_CANDIDATE_MEMORY;
    unsigned char *cursor=bytes;geo_candidate_encode_u64(&cursor,(uint64_t)count);
    for(size_t i=0;i<count;++i){
        const GeoSourceProvider *provider=geo_eval_provider_at(sources,i);
        geo_candidate_encode_u64(&cursor,(uint64_t)provider->token);
        geo_candidate_encode_text(&cursor,provider->name_space);
        geo_candidate_encode_text(&cursor,provider->implementation_fingerprint);
    }
    geo_sha256(bytes,size,out);free(bytes);return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_seal(GeoCandidate *candidate)
{
    if(!candidate)return GEO_CANDIDATE_INVALID;
    if(candidate->state!=GEO_CANDIDATE_EVALUATED)return GEO_CANDIDATE_STATE;
    GeoCandidateStatus status=geo_candidate_check_state(candidate,true);
    if(status!=GEO_CANDIDATE_OK)return status;
    char hash[65];status=geo_candidate_provider_hash(candidate->sources,hash);
    if(status!=GEO_CANDIDATE_OK)return status;
    if(!geo_eval_seal(candidate->sources))return GEO_CANDIDATE_STATE;
    memcpy(candidate->providers_hash,hash,sizeof hash);candidate->state=GEO_CANDIDATE_SEALED;
    return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_check(const GeoCandidate *candidate,uint64_t live_revision,const char *provider_stamp)
{
    if(!candidate||!provider_stamp)return GEO_CANDIDATE_INVALID;
    if(candidate->state!=GEO_CANDIDATE_SEALED)return GEO_CANDIDATE_STATE;
    if(live_revision!=candidate->base_revision)return GEO_CANDIDATE_REVISION_CHANGED;
    if(strcmp(provider_stamp,candidate->provider_stamp))return GEO_CANDIDATE_PROVIDER_CHANGED;
    GeoCandidateStatus status=geo_candidate_check_state(candidate,true);
    if(status!=GEO_CANDIDATE_OK)return status;
    if(!geo_eval_is_sealed(candidate->sources))return GEO_CANDIDATE_STATE;
    char hash[65];status=geo_candidate_provider_hash(candidate->sources,hash);
    if(status!=GEO_CANDIDATE_OK)return status;
    if(strcmp(hash,candidate->providers_hash))return GEO_CANDIDATE_PROVIDER_CHANGED;
    return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_mark_published(GeoCandidate *candidate,uint64_t live_revision,const char *provider_stamp)
{
    GeoCandidateStatus status=geo_candidate_check(candidate,live_revision,provider_stamp);
    if(status!=GEO_CANDIDATE_OK)return status;
    candidate->state=GEO_CANDIDATE_PUBLISHED;return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_reopen(GeoCandidate *candidate,uint64_t live_revision,const char *provider_stamp)
{
    GeoCandidateStatus status=geo_candidate_check(candidate,live_revision,provider_stamp);
    if(status!=GEO_CANDIDATE_OK)return status;
    geo_eval_destroy(candidate->sources);candidate->sources=NULL;
    candidate->providers_hash[0]='\0';candidate->state=GEO_CANDIDATE_OPEN;
    return GEO_CANDIDATE_OK;
}
GeoCandidateStatus geo_candidate_discard(GeoCandidate *candidate)
{
    if(!candidate)return GEO_CANDIDATE_INVALID;
    if(candidate->state==GEO_CANDIDATE_EVALUATING||candidate->state==GEO_CANDIDATE_PUBLISHED||
       candidate->state==GEO_CANDIDATE_DISCARDED)return GEO_CANDIDATE_STATE;
    geo_eval_destroy(candidate->sources);candidate->sources=NULL;
    candidate->state=GEO_CANDIDATE_DISCARDED;return GEO_CANDIDATE_OK;
}
GeoEvalContext *geo_candidate_sources(const GeoCandidate *candidate){return candidate?candidate->sources:NULL;}
GeoCandidateState geo_candidate_state(const GeoCandidate *candidate){return candidate?candidate->state:GEO_CANDIDATE_DISCARDED;}
uint64_t geo_candidate_id(const GeoCandidate *candidate){return candidate?candidate->candidate_id:0;}
uint64_t geo_candidate_base_revision(const GeoCandidate *candidate){return candidate?candidate->base_revision:0;}
uint64_t geo_candidate_evaluation_generation(const GeoCandidate *candidate){return candidate?candidate->evaluation_generation:0;}
