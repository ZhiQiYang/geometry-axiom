/* Isolated K-only client. Test-local proxies call the real codec/allocator;
 * no host object, product root, synthetic digest or candidate internals. */
#include "candidate.h"
#include "codec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(label,expr) do{if(!(expr)){fprintf(stderr,"ASSERT:%s line=%d expr=%s\n",label,__LINE__,#expr);return 1;}}while(0)
enum { BEFORE=1,CURRENT=2,TEXT=4,HANDLE=8,BINDINGS=16,METADATA=32,SOURCES=64,
       N=96,MAX_EVENTS=32,MAX_BYTES=128 };
typedef struct {const void *pointer;size_t size;unsigned char bytes[MAX_BYTES];char digest[65];} Event;
typedef struct {
    GeoCandidate *candidate;
    unsigned char before[N],current[N];
    uint64_t id,revision;
    unsigned seed,evaluations;
    bool fail,reentrant,provider;
} Fixture;
static const char STAMP[]="K-deferred/exact-stamp";
static Event events[MAX_EVENTS];
static unsigned event_count,failures,attempts[128],fail_on_attempt[128];

static bool allocation_fails(unsigned slot)
{
    if(slot>=128||!slot||(slot&(slot-1)))abort();
    ++attempts[slot];
    return (failures&slot)||(fail_on_attempt[slot]&&attempts[slot]==fail_on_attempt[slot]);
}
void *candidate_cache_test_alloc(size_t size,unsigned slot)
{return allocation_fails(slot)?NULL:malloc(size);}
void *candidate_deferred_test_calloc(size_t count,size_t size)
{return allocation_fails(HANDLE)?NULL:calloc(count,size);}
void *candidate_deferred_test_realloc(void *old,size_t size)
{return allocation_fails(BINDINGS)?NULL:realloc(old,size);}
GeoEvalContext *candidate_deferred_test_sources(uint64_t id,uint64_t revision)
{return allocation_fails(SOURCES)?NULL:geo_eval_create(id,revision);}
void candidate_cache_test_kernel_sha(const void *bytes,size_t size,char out[65])
{
    if(!bytes||size>MAX_BYTES||event_count==MAX_EVENTS)abort();
    geo_sha256(bytes,size,out);
    Event *event=&events[event_count++];event->pointer=bytes;event->size=size;
    memcpy(event->bytes,bytes,size);memcpy(event->digest,out,65);
}
static void reset_events(void){event_count=0;memset(events,0,sizeof events);}
static void reset_all(unsigned mask)
{failures=mask;memset(attempts,0,sizeof attempts);memset(fail_on_attempt,0,sizeof fail_on_attempt);reset_events();}
static void fill(unsigned char *out,unsigned seed)
{
    for(size_t i=0;i<N;++i)out[i]=(unsigned char)(seed+13u*(unsigned)i);
    out[0]=0;out[5]=0;out[N-1]=0;
}
static bool event_is(unsigned at,const void *pointer,const void *bytes,size_t size)
{
    if(at>=event_count||events[at].size!=size||memcmp(events[at].bytes,bytes,size))return false;
    if(pointer&&events[at].pointer!=pointer)return false;
    char expected[65];geo_sha256(bytes,size,expected);
    return !strcmp(events[at].digest,expected);
}
static bool pair_at(unsigned at,const void *actual,const void *saved,size_t size)
{
    return event_is(at,NULL,saved,size)&&events[at].pointer!=actual&&
        event_is(at+1,actual,actual,size);
}
static bool empty_metadata(unsigned at)
{static const unsigned char zero[8]={0};return event_is(at,NULL,zero,sizeof zero);}
static bool one_provider_metadata(unsigned at,unsigned token,const char *name,const char *fingerprint)
{
    /* Independent fixed fixture encoding: count=1, token, lengths 15 and 20. */
    unsigned char expected[67]={0};expected[7]=1;expected[15]=(unsigned char)token;
    expected[23]=15;expected[46]=20;memcpy(expected+24,name,15);memcpy(expected+47,fingerprint,20);
    return event_is(at,NULL,expected,sizeof expected);
}
static bool describe(void *state,const GeoSourceRef *key,GeoSourceDescriptor *out)
{(void)state;(void)key;(void)out;return false;}
static bool provider_evaluate(void *state,GeoEvalContext *context,const GeoSourceRef *key,GeoSourceValue *out)
{(void)state;(void)context;(void)key;(void)out;return false;}
static bool evaluate(void *opaque,GeoEvalContext *context)
{
    Fixture *f=opaque;
    if(geo_candidate_state(f->candidate)!=GEO_CANDIDATE_EVALUATING||
       geo_candidate_sources(f->candidate)!=context||geo_eval_candidate_id(context)!=f->id||
       geo_eval_base_revision(context)!=f->revision||geo_eval_node_count(context)||geo_eval_provider_count(context))return false;
    if(f->reentrant){
        if(geo_candidate_bind_state(f->candidate,"late",f->before,f->current,N)!=GEO_CANDIDATE_STATE||
           geo_candidate_evaluate(f->candidate,evaluate,f)!=GEO_CANDIDATE_STATE||
           geo_candidate_seal(f->candidate)!=GEO_CANDIDATE_STATE||
           geo_candidate_check(f->candidate,f->revision,STAMP)!=GEO_CANDIDATE_STATE||
           geo_candidate_reopen(f->candidate,f->revision,STAMP)!=GEO_CANDIDATE_STATE||
           geo_candidate_mark_published(f->candidate,f->revision,STAMP)!=GEO_CANDIDATE_STATE||
           geo_candidate_discard(f->candidate)!=GEO_CANDIDATE_STATE)return false;
    }
    ++f->evaluations;fill(f->current,f->seed);
    if(f->provider){
        GeoSourceProvider provider={19,"opaque.provider","implementation/exact",f,describe,provider_evaluate};
        if(!geo_eval_register(context,&provider))return false;
    }
    return !f->fail;
}
static int initialize(Fixture *f,unsigned mask,bool bind)
{
    reset_all(mask);memset(f,0,sizeof *f);f->id=91;f->revision=23;f->seed=37;
    fill(f->before,7);memcpy(f->current,f->before,N);
    f->candidate=geo_candidate_create_deferred_sha(f->id,f->revision,STAMP);
    REQUIRE("deferred-constructor",f->candidate);
    if(bind)REQUIRE("deferred-bind",geo_candidate_bind_state(f->candidate,"opaque-bytes",f->before,f->current,N)==GEO_CANDIDATE_OK);
    return 0;
}
static GeoCandidateStatus check(Fixture *f)
{return geo_candidate_check(f->candidate,f->revision,STAMP);}
static int seal_initial(Fixture *f)
{
    REQUIRE("successful-evaluation",geo_candidate_evaluate(f->candidate,evaluate,f)==GEO_CANDIDATE_OK);
    REQUIRE("successful-seal",geo_candidate_seal(f->candidate)==GEO_CANDIDATE_OK);
    reset_events();return 0;
}
static int constructors(void)
{
    reset_all(0);
    REQUIRE("null-stamp-rejected",!geo_candidate_create_deferred_sha(0,0,NULL));
    REQUIRE("empty-stamp-rejected",!geo_candidate_create_deferred_sha(0,0,""));
    const uint64_t values[2]={0,UINT64_MAX};
    for(unsigned a=0;a<2;++a)for(unsigned b=0;b<2;++b){
        Fixture f={0};f.id=values[a];f.revision=values[b];f.reentrant=true;
        f.candidate=geo_candidate_create_deferred_sha(f.id,f.revision,STAMP);
        REQUIRE("identity-extremes-accepted",f.candidate&&geo_candidate_id(f.candidate)==f.id&&geo_candidate_base_revision(f.candidate)==f.revision);
        REQUIRE("new-candidate-open",geo_candidate_state(f.candidate)==GEO_CANDIDATE_OPEN&&!geo_candidate_sources(f.candidate));
        reset_events();REQUIRE("unevaluated-seal-state",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&event_count==0);
        REQUIRE("zero-binding-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
        REQUIRE("zero-binding-generation",f.evaluations==1&&geo_candidate_evaluation_generation(f.candidate)==1);
        reset_events();REQUIRE("zero-binding-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
        REQUIRE("zero-binding-publishes",geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_OK);
        REQUIRE("published-terminal",geo_candidate_state(f.candidate)==GEO_CANDIDATE_PUBLISHED&&
            geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE&&
            geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&check(&f)==GEO_CANDIDATE_STATE&&
            geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE&&
            geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE&&
            geo_candidate_discard(f.candidate)==GEO_CANDIDATE_STATE);
        geo_candidate_destroy(f.candidate);
    }
    REQUIRE("null-candidate-status",geo_candidate_bind_state(NULL,"x",values,(void*)values,sizeof values)==GEO_CANDIDATE_INVALID&&
        geo_candidate_evaluate(NULL,evaluate,NULL)==GEO_CANDIDATE_INVALID&&geo_candidate_seal(NULL)==GEO_CANDIDATE_INVALID&&
        geo_candidate_check(NULL,0,STAMP)==GEO_CANDIDATE_INVALID&&geo_candidate_reopen(NULL,0,STAMP)==GEO_CANDIDATE_INVALID&&
        geo_candidate_mark_published(NULL,0,STAMP)==GEO_CANDIDATE_INVALID&&geo_candidate_discard(NULL)==GEO_CANDIDATE_INVALID);
    REQUIRE("null-candidate-accessors",!geo_candidate_sources(NULL)&&geo_candidate_state(NULL)==GEO_CANDIDATE_DISCARDED&&
        geo_candidate_id(NULL)==0&&geo_candidate_base_revision(NULL)==0&&geo_candidate_evaluation_generation(NULL)==0);
    geo_candidate_destroy(NULL);return 0;
}
static int hit(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);
    REQUIRE("deferred-bind-skips-state-sha",event_count==0&&attempts[BEFORE]==1&&attempts[CURRENT]==0);
    unsigned char before[N];memcpy(before,f.before,N);
    REQUIRE("successful-evaluation",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    REQUIRE("deferred-evaluation-skips-state-sha",event_count==0&&attempts[CURRENT]==1);
    REQUIRE("successful-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
    REQUIRE("seal-retains-real-provider-sha",event_count==1&&empty_metadata(0));
    for(unsigned i=0;i<5;++i){
        reset_events();REQUIRE("unchanged-check",check(&f)==GEO_CANDIDATE_OK);
        REQUIRE("checks-only-provider-sha",event_count==1&&empty_metadata(0));
    }
    REQUIRE("checks-preserve-evaluation",f.evaluations==1&&geo_candidate_evaluation_generation(f.candidate)==1);
    REQUIRE("checks-do-not-reallocate",attempts[BEFORE]==1&&attempts[CURRENT]==1);
    REQUIRE("before-remains-immutable",!memcmp(before,f.before,N));
    geo_candidate_destroy(f.candidate);return 0;
}
static int coexist(void)
{
    Fixture deferred,eager={0};REQUIRE("fixture",initialize(&deferred,0,true)==0);
    eager.id=92;eager.revision=24;eager.seed=83;fill(eager.before,11);memcpy(eager.current,eager.before,N);
    eager.candidate=geo_candidate_create(eager.id,eager.revision,STAMP);
    REQUIRE("default-constructor-retained",eager.candidate);
    reset_events();REQUIRE("default-bind",geo_candidate_bind_state(eager.candidate,"opaque-bytes",eager.before,eager.current,N)==GEO_CANDIDATE_OK);
    REQUIRE("default-bind-still-eager",event_count==1&&event_is(0,eager.before,eager.before,N));
    reset_events();REQUIRE("interleaved-deferred-evaluation",geo_candidate_evaluate(deferred.candidate,evaluate,&deferred)==GEO_CANDIDATE_OK&&event_count==0);
    reset_events();REQUIRE("interleaved-default-evaluation",geo_candidate_evaluate(eager.candidate,evaluate,&eager)==GEO_CANDIDATE_OK);
    REQUIRE("default-evaluation-still-eager",event_count==1&&event_is(0,eager.current,eager.current,N));
    reset_events();REQUIRE("deferred-seal",geo_candidate_seal(deferred.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    reset_events();REQUIRE("default-seal",geo_candidate_seal(eager.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    unsigned char saved[N];memcpy(saved,deferred.current,N);deferred.current[5]^=1;reset_events();
    REQUIRE("deferred-isolation-rejects-own-tamper",check(&deferred)==GEO_CANDIDATE_STATE_CHANGED&&event_count==2&&pair_at(0,deferred.current,saved,N));
    reset_events();REQUIRE("default-unaffected-by-other-candidate",check(&eager)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    deferred.current[5]^=1;eager.current[5]^=1;reset_events();
    REQUIRE("default-tamper-still-one-real-sha",check(&eager)==GEO_CANDIDATE_STATE_CHANGED&&event_count==1&&event_is(0,eager.current,eager.current,N));
    reset_events();REQUIRE("deferred-unaffected-by-other-candidate",check(&deferred)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    eager.current[5]^=1;reset_events();REQUIRE("default-restoration",check(&eager)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    REQUIRE("coexist-allocation-counts",attempts[BEFORE]==2&&attempts[CURRENT]==2);
    geo_candidate_destroy(eager.candidate);geo_candidate_destroy(deferred.candidate);return 0;
}
static int tamper(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);REQUIRE("initial-seal",seal_initial(&f)==0);
    unsigned char saved[2][N];memcpy(saved[0],f.before,N);memcpy(saved[1],f.current,N);
    for(unsigned side=0;side<2;++side)for(size_t i=0;i<N;++i){
        unsigned char *actual=side?f.current:f.before;actual[i]^=0x5a;reset_events();
        REQUIRE(side?"deferred-current-tamper-rejected":"deferred-before-tamper-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("pending-miss-saved-then-actual",event_count==2&&pair_at(0,actual,saved[side],N));
        REQUIRE("failed-check-preserves-seal",geo_candidate_state(f.candidate)==GEO_CANDIDATE_SEALED&&
            geo_candidate_evaluation_generation(f.candidate)==1&&f.evaluations==1);
        actual[i]^=0x5a;reset_events();REQUIRE("restoration-valid",check(&f)==GEO_CANDIDATE_OK);
        REQUIRE("restoration-only-provider-sha",event_count==1&&empty_metadata(0));
    }
    REQUIRE("tamper-never-reallocates",attempts[BEFORE]==1&&attempts[CURRENT]==1);
    geo_candidate_destroy(f.candidate);return 0;
}
static int unsealed(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);
    unsigned char original[N],evaluated[N];memcpy(original,f.before,N);
    f.before[N-1]^=1;reset_events();
    REQUIRE("before-tamper-blocks-evaluator",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("before-tamper-pair",event_count==2&&pair_at(0,f.before,original,N));
    REQUIRE("blocked-before-no-generation",!f.evaluations&&!geo_candidate_evaluation_generation(f.candidate)&&
        geo_candidate_state(f.candidate)==GEO_CANDIDATE_REJECTED);
    f.before[N-1]^=1;reset_events();REQUIRE("before-restored-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK&&event_count==0);
    memcpy(evaluated,f.current,N);f.current[0]^=1;reset_events();
    REQUIRE("current-tamper-blocks-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("pre-seal-current-pair",event_count==2&&pair_at(0,f.current,evaluated,N));
    f.current[0]^=1;reset_events();REQUIRE("current-restored-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    geo_candidate_destroy(f.candidate);return 0;
}
static int lifecycle(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);f.reentrant=true;
    unsigned char previous[N],latest[N];memcpy(previous,f.current,N);
    for(unsigned round=0;round<4;++round){
        f.seed+=31;reset_events();REQUIRE("lifecycle-evaluate",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
        REQUIRE("lifecycle-deferred-capture",event_count==0&&f.evaluations==round+1&&geo_candidate_evaluation_generation(f.candidate)==round+1);
        memcpy(latest,f.current,N);memcpy(f.current,previous,N);reset_events();
        REQUIRE("prior-round-cannot-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("prior-round-uses-latest-saved",event_count==2&&pair_at(0,f.current,latest,N));
        memcpy(f.current,latest,N);reset_events();REQUIRE("latest-round-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
        REQUIRE("latest-round-cache-hit",event_count==1&&empty_metadata(0));
        reset_events();REQUIRE("reopen-validates-old-seal",geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_OK);
        REQUIRE("reopen-only-provider-sha",event_count==1&&empty_metadata(0));
        REQUIRE("reopen-keeps-identity",geo_candidate_state(f.candidate)==GEO_CANDIDATE_OPEN&&!geo_candidate_sources(f.candidate)&&
            geo_candidate_id(f.candidate)==f.id&&geo_candidate_base_revision(f.candidate)==f.revision&&geo_candidate_evaluation_generation(f.candidate)==round+1);
        REQUIRE("reopen-cannot-add-bindings",geo_candidate_bind_state(f.candidate,"late",f.before,f.current,N)==GEO_CANDIDATE_STATE);
        REQUIRE("reopen-requires-new-evaluation",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE);
        memcpy(previous,latest,N);
    }
    REQUIRE("lifecycle-reuses-one-copy",attempts[BEFORE]==1&&attempts[CURRENT]==1);
    geo_candidate_destroy(f.candidate);return 0;
}
static int failed(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);f.fail=true;
    REQUIRE("first-failed-evaluation",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("failed-first-has-no-current-seal",attempts[CURRENT]==0&&event_count==0&&geo_candidate_evaluation_generation(f.candidate)==1);
    REQUIRE("failed-first-cannot-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&check(&f)==GEO_CANDIDATE_STATE);
    f.fail=false;f.seed+=11;REQUIRE("failure-can-recover",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    GeoEvalContext *previous=geo_candidate_sources(f.candidate);failures=SOURCES;reset_events();
    REQUIRE("resolver-oom-is-memory",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_MEMORY);
    REQUIRE("resolver-oom-retains-old-context",geo_candidate_sources(f.candidate)==previous&&geo_candidate_state(f.candidate)==GEO_CANDIDATE_REJECTED&&
        f.evaluations==2&&geo_candidate_evaluation_generation(f.candidate)==2&&event_count==0);
    failures=0;f.fail=true;f.seed+=11;REQUIRE("failure-after-success",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("failure-never-rolls-back-generation",f.evaluations==3&&geo_candidate_evaluation_generation(f.candidate)==3);
    REQUIRE("failed-current-cannot-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&check(&f)==GEO_CANDIDATE_STATE);
    f.fail=false;f.seed+=11;reset_events();REQUIRE("latest-success-after-failure",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK&&event_count==0);
    REQUIRE("recovered-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&f.evaluations==4&&geo_candidate_evaluation_generation(f.candidate)==4);
    REQUIRE("discard-valid",geo_candidate_discard(f.candidate)==GEO_CANDIDATE_OK&&!geo_candidate_sources(f.candidate));
    reset_events();REQUIRE("discard-terminal",geo_candidate_state(f.candidate)==GEO_CANDIDATE_DISCARDED&&
        geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE&&geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE&&
        check(&f)==GEO_CANDIDATE_STATE&&geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE&&
        geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE&&geo_candidate_discard(f.candidate)==GEO_CANDIDATE_STATE&&event_count==0);
    geo_candidate_destroy(f.candidate);return 0;
}
static int state_edges(void)
{
    const GeoCandidateState states[]={GEO_CANDIDATE_OPEN,GEO_CANDIDATE_EVALUATED,GEO_CANDIDATE_REJECTED,GEO_CANDIDATE_SEALED};
    for(unsigned i=0;i<4;++i){
        Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);
        if(i){
            f.fail=i==2;
            REQUIRE("state-fixture-evaluation",geo_candidate_evaluate(f.candidate,evaluate,&f)==(f.fail?GEO_CANDIDATE_EVALUATION_FAILED:GEO_CANDIDATE_OK));
            if(i==3)REQUIRE("state-fixture-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
        }
        REQUIRE("state-fixture-exact",geo_candidate_state(f.candidate)==states[i]);
        uint64_t generation=geo_candidate_evaluation_generation(f.candidate);GeoEvalContext *sources=geo_candidate_sources(f.candidate);reset_events();
        REQUIRE("null-callback-invalid-not-state",geo_candidate_evaluate(f.candidate,NULL,&f)==GEO_CANDIDATE_INVALID);
        REQUIRE("null-stamp-invalid-not-state",geo_candidate_check(f.candidate,f.revision,NULL)==GEO_CANDIDATE_INVALID&&
            geo_candidate_reopen(f.candidate,f.revision,NULL)==GEO_CANDIDATE_INVALID&&geo_candidate_mark_published(f.candidate,f.revision,NULL)==GEO_CANDIDATE_INVALID);
        REQUIRE("invalid-arguments-preserve-handle",geo_candidate_state(f.candidate)==states[i]&&geo_candidate_sources(f.candidate)==sources&&
            geo_candidate_evaluation_generation(f.candidate)==generation&&event_count==0);
        if(i!=3)REQUIRE("unsealed-cannot-check-or-publish",check(&f)==GEO_CANDIDATE_STATE&&geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE&&
            geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_STATE);
        if(i==0||i==2||i==3)REQUIRE("invalid-state-cannot-seal",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE);
        if(i==3)REQUIRE("sealed-cannot-evaluate",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE);
        REQUIRE("state-guards-no-sha",event_count==0);
        REQUIRE("all-nonterminal-states-discard",geo_candidate_discard(f.candidate)==GEO_CANDIDATE_OK&&
            geo_candidate_state(f.candidate)==GEO_CANDIDATE_DISCARDED&&!geo_candidate_sources(f.candidate)&&
            geo_candidate_evaluation_generation(f.candidate)==generation&&event_count==0);
        REQUIRE("discard-cannot-rebind",geo_candidate_bind_state(f.candidate,"late",f.before,f.current,N)==GEO_CANDIDATE_STATE);
        geo_candidate_destroy(f.candidate);
    }
    return 0;
}
static int generation_limit(void)
{
    /* The isolated test object advances the existing increment to UINT64_MAX.
     * The production overflow guard and every public operation stay intact. */
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);
    REQUIRE("last-generation-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK&&
        f.evaluations==1&&geo_candidate_evaluation_generation(f.candidate)==UINT64_MAX);
    GeoEvalContext *sources=geo_candidate_sources(f.candidate);reset_events();
    REQUIRE("generation-limit-blocks-callback",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE&&f.evaluations==1);
    REQUIRE("generation-limit-preserves-evaluated",geo_candidate_state(f.candidate)==GEO_CANDIDATE_EVALUATED&&geo_candidate_sources(f.candidate)==sources&&
        geo_candidate_evaluation_generation(f.candidate)==UINT64_MAX&&event_count==0);
    REQUIRE("last-generation-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    REQUIRE("last-generation-reopens",geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_OK);
    reset_events();REQUIRE("reopen-does-not-reset-limit",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_STATE&&
        geo_candidate_state(f.candidate)==GEO_CANDIDATE_OPEN&&!geo_candidate_sources(f.candidate)&&
        f.evaluations==1&&geo_candidate_evaluation_generation(f.candidate)==UINT64_MAX&&event_count==0);
    geo_candidate_destroy(f.candidate);return 0;
}
static int oom(unsigned mask)
{
    Fixture f;REQUIRE("fixture",initialize(&f,mask,true)==0);
    unsigned before_missing=!!(mask&BEFORE),current_missing=!!(mask&CURRENT);
    REQUIRE("before-oom-captured",event_count==before_missing&&(!before_missing||event_is(0,f.before,f.before,N)));
    reset_events();REQUIRE("oom-still-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    REQUIRE("current-oom-captured",event_count==before_missing+current_missing&&
        (!before_missing||event_is(0,f.before,f.before,N))&&(!current_missing||event_is(before_missing,f.current,f.current,N)));
    reset_events();REQUIRE("oom-still-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
    REQUIRE("oom-seal-sha-order",event_count==before_missing+current_missing+1&&
        (!before_missing||event_is(0,f.before,f.before,N))&&(!current_missing||event_is(before_missing,f.current,f.current,N))&&empty_metadata(before_missing+current_missing));
    unsigned char saved[2][N];memcpy(saved[0],f.before,N);memcpy(saved[1],f.current,N);
    for(unsigned side=0;side<2;++side){
        unsigned char *actual=side?f.current:f.before;unsigned missing=side?current_missing:before_missing;
        actual[5]^=0x80;reset_events();REQUIRE("oom-tamper-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
        unsigned offset=side?before_missing:0;
        REQUIRE("oom-tamper-real-inputs",event_count==offset+(missing?1u:2u)&&
            (!offset||event_is(0,f.before,f.before,N))&&
            (missing?event_is(offset,actual,actual,N):pair_at(offset,actual,saved[side],N)));
        actual[5]^=0x80;reset_events();REQUIRE("oom-restored-valid",check(&f)==GEO_CANDIDATE_OK);
        REQUIRE("oom-restored-sha-count",event_count==before_missing+current_missing+1&&empty_metadata(before_missing+current_missing));
    }
    REQUIRE("guards-never-retry-cache-allocation",attempts[BEFORE]==1&&attempts[CURRENT]==1);
    geo_candidate_destroy(f.candidate);return 0;
}
static int recovery(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,CURRENT,true)==0);
    reset_events();REQUIRE("oom-round-A-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    REQUIRE("current-oom-captured",event_count==1&&event_is(0,f.current,f.current,N));
    unsigned char old[N],latest[N];memcpy(old,f.current,N);failures=0;f.seed+=51;reset_events();
    REQUIRE("round-B-retries-allocation",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    REQUIRE("recovered-current-is-pending",event_count==0&&attempts[BEFORE]==1&&attempts[CURRENT]==2);
    memcpy(latest,f.current,N);memcpy(f.current,old,N);reset_events();
    REQUIRE("old-oom-digest-cannot-authorize",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("recovery-uses-B-not-old-A",event_count==2&&pair_at(0,f.current,latest,N));
    memcpy(f.current,latest,N);reset_events();REQUIRE("recovered-current-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    geo_candidate_destroy(f.candidate);return 0;
}
static int mixed(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,BEFORE,false)==0);
    REQUIRE("left-binding",geo_candidate_bind_state(f.candidate,"left",f.before,f.current,N/2)==GEO_CANDIDATE_OK);
    failures=0;REQUIRE("right-binding",geo_candidate_bind_state(f.candidate,"right",f.before+N/2,f.current+N/2,N/2)==GEO_CANDIDATE_OK);
    REQUIRE("only-left-before-eager",event_count==1&&event_is(0,f.before,f.before,N/2));
    fail_on_attempt[CURRENT]=2;reset_events();REQUIRE("mixed-evaluates",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    REQUIRE("mixed-evaluate-exact-ranges",event_count==2&&event_is(0,f.before,f.before,N/2)&&event_is(1,f.current+N/2,f.current+N/2,N/2));
    reset_events();REQUIRE("mixed-seals",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
    REQUIRE("mixed-seal-exact-ranges",event_count==3&&event_is(0,f.before,f.before,N/2)&&event_is(1,f.current+N/2,f.current+N/2,N/2)&&empty_metadata(2));
    unsigned char saved[N];memcpy(saved,f.current,N);f.current[N/2-1]^=1;reset_events();
    REQUIRE("mixed-left-current-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("mixed-left-private-range",event_count==3&&event_is(0,f.before,f.before,N/2)&&pair_at(1,f.current,saved,N/2));
    f.current[N/2-1]^=1;f.current[N-1]^=1;reset_events();REQUIRE("mixed-right-current-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("mixed-right-eager-range",event_count==2&&event_is(0,f.before,f.before,N/2)&&event_is(1,f.current+N/2,f.current+N/2,N/2));
    f.current[N-1]^=1;reset_events();REQUIRE("mixed-restored",check(&f)==GEO_CANDIDATE_OK&&event_count==3&&empty_metadata(2));
    REQUIRE("mixed-no-check-reallocation",attempts[BEFORE]==2&&attempts[CURRENT]==2);
    geo_candidate_destroy(f.candidate);return 0;
}
static int resources(void)
{
    reset_all(TEXT);REQUIRE("stamp-oom-rejected",!geo_candidate_create_deferred_sha(0,0,STAMP));
    reset_all(HANDLE);REQUIRE("handle-oom-rejected",!geo_candidate_create_deferred_sha(0,0,STAMP));
    Fixture f;REQUIRE("fixture",initialize(&f,0,false)==0);
    failures=TEXT;REQUIRE("binding-name-oom-memory",geo_candidate_bind_state(f.candidate,"range",f.before,f.current,N)==GEO_CANDIDATE_MEMORY);
    failures=BINDINGS;REQUIRE("binding-array-oom-memory",geo_candidate_bind_state(f.candidate,"range",f.before,f.current,N)==GEO_CANDIDATE_MEMORY);
    failures=0;REQUIRE("binding-failures-remain-atomic",geo_candidate_bind_state(f.candidate,"range",f.before,f.current,N)==GEO_CANDIDATE_OK);
    failures=SOURCES;REQUIRE("first-resolver-oom",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_MEMORY&&
        !geo_candidate_sources(f.candidate)&&!f.evaluations&&!geo_candidate_evaluation_generation(f.candidate));
    failures=0;REQUIRE("resolver-recovery",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK);
    failures=METADATA;reset_events();REQUIRE("metadata-seal-oom-memory",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-failure-not-sealed",geo_candidate_state(f.candidate)==GEO_CANDIDATE_EVALUATED&&!geo_eval_is_sealed(geo_candidate_sources(f.candidate))&&event_count==0);
    failures=0;REQUIRE("metadata-seal-recovery",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK);
    failures=METADATA;reset_events();REQUIRE("metadata-check-oom-memory",check(&f)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-publish-oom-memory",geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-reopen-oom-memory",geo_candidate_reopen(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-oom-preserves-seal",geo_candidate_state(f.candidate)==GEO_CANDIDATE_SEALED&&event_count==0);
    failures=0;reset_events();REQUIRE("metadata-check-recovery",check(&f)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    geo_candidate_destroy(f.candidate);return 0;
}
static int priority(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);REQUIRE("initial-seal",seal_initial(&f)==0);
    f.before[1]^=1;failures=METADATA;reset_events();
    REQUIRE("revision-precedes-stamp-and-bytes",geo_candidate_check(f.candidate,f.revision+1,"wrong")==GEO_CANDIDATE_REVISION_CHANGED&&event_count==0);
    REQUIRE("stamp-precedes-bytes",geo_candidate_check(f.candidate,f.revision,"wrong")==GEO_CANDIDATE_PROVIDER_CHANGED&&event_count==0);
    REQUIRE("bytes-precede-metadata-oom",check(&f)==GEO_CANDIDATE_STATE_CHANGED&&event_count==2);
    f.before[1]^=1;reset_events();REQUIRE("metadata-error-not-hidden",check(&f)==GEO_CANDIDATE_MEMORY&&event_count==0);
    failures=0;reset_events();REQUIRE("priority-restored",check(&f)==GEO_CANDIDATE_OK&&event_count==1&&empty_metadata(0));
    geo_candidate_destroy(f.candidate);return 0;
}
static int provider(void)
{
    Fixture f;REQUIRE("fixture",initialize(&f,0,true)==0);f.provider=true;
    REQUIRE("provider-evaluates-without-state-sha",geo_candidate_evaluate(f.candidate,evaluate,&f)==GEO_CANDIDATE_OK&&event_count==0);
    REQUIRE("provider-seals-real-metadata",geo_candidate_seal(f.candidate)==GEO_CANDIDATE_OK&&event_count==1&&
        one_provider_metadata(0,19,"opaque.provider","implementation/exact"));
    GeoSourceProvider *p=(GeoSourceProvider*)geo_eval_provider_at(geo_candidate_sources(f.candidate),0);
    REQUIRE("actual-provider-present",p&&p->token==19&&!strcmp(p->name_space,"opaque.provider")&&!strcmp(p->implementation_fingerprint,"implementation/exact"));
    p->token=20;reset_events();REQUIRE("provider-token-tamper-rejected",check(&f)==GEO_CANDIDATE_PROVIDER_CHANGED&&event_count==1&&
        one_provider_metadata(0,20,"opaque.provider","implementation/exact"));
    p->token=19;char *name=(char*)p->name_space,*fingerprint=(char*)p->implementation_fingerprint;
    name[0]^=1;reset_events();REQUIRE("provider-name-tamper-rejected",check(&f)==GEO_CANDIDATE_PROVIDER_CHANGED&&event_count==1&&
        one_provider_metadata(0,19,name,fingerprint));name[0]^=1;
    fingerprint[strlen(fingerprint)-1]^=1;reset_events();REQUIRE("provider-fingerprint-tamper-rejected",geo_candidate_mark_published(f.candidate,f.revision,STAMP)==GEO_CANDIDATE_PROVIDER_CHANGED&&
        event_count==1&&one_provider_metadata(0,19,name,fingerprint));
    fingerprint[strlen(fingerprint)-1]^=1;reset_events();REQUIRE("provider-restored-valid",check(&f)==GEO_CANDIDATE_OK&&event_count==1&&
        one_provider_metadata(0,19,"opaque.provider","implementation/exact"));
    geo_candidate_destroy(f.candidate);return 0;
}
int main(int argc,char **argv)
{
    if(argc<2)return 2;
    const char *name=argv[1];int result;
    if(!strcmp(name,"constructors"))result=constructors();
    else if(!strcmp(name,"hit"))result=hit();
    else if(!strcmp(name,"coexist"))result=coexist();
    else if(!strcmp(name,"tamper"))result=tamper();
    else if(!strcmp(name,"unsealed"))result=unsealed();
    else if(!strcmp(name,"lifecycle"))result=lifecycle();
    else if(!strcmp(name,"failed"))result=failed();
    else if(!strcmp(name,"state-edges"))result=state_edges();
    else if(!strcmp(name,"generation-limit"))result=generation_limit();
    else if(!strcmp(name,"oom")&&argc==3){
        char *end=NULL;unsigned long mask=strtoul(argv[2],&end,10);
        if(!end||*end||mask<1||mask>3)return 2;result=oom((unsigned)mask);
    }else if(!strcmp(name,"recovery"))result=recovery();
    else if(!strcmp(name,"mixed"))result=mixed();
    else if(!strcmp(name,"resources"))result=resources();
    else if(!strcmp(name,"priority"))result=priority();
    else if(!strcmp(name,"provider"))result=provider();
    else return 2;
    if(!result)printf("PASS %s\n",name);return result;
}
