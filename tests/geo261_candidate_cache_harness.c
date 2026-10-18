/* Test-local callers of the real K/H candidate implementation. Only SHA call
 * names and the four optional cache allocations are instrumented by Python. */
#include "candidate.h"
#include "app_candidate.h"
#include "codec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(label, expression) do { if(!(expression)) { \
    fprintf(stderr,"ASSERT:%s line=%d expr=%s\n",label,__LINE__,#expression); \
    return 1; } } while(0)

enum { K_BEFORE=1, K_AFTER=2, H_BEFORE=4, H_AFTER=8, SNAPSHOT_SIZE=96,
       CORE_OFFSET=16, CORE_SIZE=32 };
typedef struct {
    const void *before,*after;
    size_t size;
    unsigned before_calls,after_calls,other_calls;
    char before_hash[65],after_hash[65];
} Trace;
typedef struct {
    bool host;
    unsigned char live[SNAPSHOT_SIZE],before[SNAPSHOT_SIZE],after[SNAPSHOT_SIZE];
    GeoCandidate *core;
    AppCandidate *app;
    unsigned seed,evaluations;
} Fixture;

static Trace kernel_trace,host_trace;
static unsigned fail_allocations,allocation_attempts[16];
static const char STAMP[]="candidate-cache-test/exact-sha256";
static const uint64_t REVISION=23,CANDIDATE_ID=901;

static void traced_sha(Trace *trace,const void *data,size_t length,char out[65])
{
    /* This calls the real codec, never a test digest or an expected-value stub. */
    geo_sha256(data,length,out);
    if(data==trace->before&&length==trace->size){
        ++trace->before_calls;memcpy(trace->before_hash,out,65);
    }else if(data==trace->after&&length==trace->size){
        ++trace->after_calls;memcpy(trace->after_hash,out,65);
    }else ++trace->other_calls;
}
void candidate_cache_test_kernel_sha(const void *data,size_t length,char out[65])
{traced_sha(&kernel_trace,data,length,out);}
void candidate_cache_test_host_sha(const void *data,size_t length,char out[65])
{traced_sha(&host_trace,data,length,out);}
void *candidate_cache_test_alloc(size_t size,unsigned slot)
{
    if(slot!=K_BEFORE&&slot!=K_AFTER&&slot!=H_BEFORE&&slot!=H_AFTER)abort();
    ++allocation_attempts[slot];
    return fail_allocations&slot?NULL:malloc(size);
}
static void reset_counts(void)
{
    kernel_trace.before_calls=kernel_trace.after_calls=kernel_trace.other_calls=0;
    host_trace.before_calls=host_trace.after_calls=host_trace.other_calls=0;
}
static bool counts(unsigned kb,unsigned ka,unsigned ko,unsigned hb,unsigned ha,unsigned ho)
{
    return kernel_trace.before_calls==kb&&kernel_trace.after_calls==ka&&kernel_trace.other_calls==ko&&
        host_trace.before_calls==hb&&host_trace.after_calls==ha&&host_trace.other_calls==ho;
}
static bool same_digest(const void *bytes,size_t size,const char actual[65])
{
    char expected[65];geo_sha256(bytes,size,expected);return !strcmp(expected,actual);
}
static bool evaluate_bytes(Fixture *fixture,GeoEvalContext *sources)
{
    if(geo_eval_candidate_id(sources)!=CANDIDATE_ID||geo_eval_base_revision(sources)!=REVISION||
       geo_eval_provider_count(sources)||geo_eval_node_count(sources))return false;
    ++fixture->evaluations;
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)
        fixture->after[i]=(unsigned char)(fixture->seed+13u*(unsigned)i);
    /* Embedded zero bytes exercise complete byte ranges, not string keys. */
    fixture->after[5]=0;fixture->after[CORE_OFFSET+5]=0;
    return true;
}
static bool evaluate_kernel(void *opaque,GeoEvalContext *sources)
{return evaluate_bytes(opaque,sources);}
static bool evaluate_host(void *after,GeoEvalContext *sources,void *opaque)
{
    Fixture *fixture=opaque;
    return after==fixture->after&&evaluate_bytes(fixture,sources);
}
static bool equal_live(const void *live,const void *before,void *opaque)
{(void)opaque;return !memcmp(live,before,SNAPSHOT_SIZE);}
static int initialize(Fixture *fixture,bool host,unsigned failures)
{
    memset(fixture,0,sizeof *fixture);fixture->host=host;fixture->seed=37;
    memset(&kernel_trace,0,sizeof kernel_trace);memset(&host_trace,0,sizeof host_trace);
    memset(allocation_attempts,0,sizeof allocation_attempts);fail_allocations=failures;
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)fixture->live[i]=(unsigned char)(7u+19u*(unsigned)i);
    fixture->live[0]=0;fixture->live[CORE_OFFSET+5]=0;
    memcpy(fixture->before,fixture->live,SNAPSHOT_SIZE);memcpy(fixture->after,fixture->live,SNAPSHOT_SIZE);
    kernel_trace.before=fixture->before+(host?CORE_OFFSET:0);
    kernel_trace.after=fixture->after+(host?CORE_OFFSET:0);
    kernel_trace.size=host?CORE_SIZE:SNAPSHOT_SIZE;
    if(host){
        host_trace.before=fixture->before;host_trace.after=fixture->after;host_trace.size=SNAPSHOT_SIZE;
        fixture->app=app_candidate_create(fixture->before,fixture->after,fixture->live,SNAPSHOT_SIZE,
            CANDIDATE_ID,REVISION,STAMP);
        REQUIRE("host-create-survives-cache-allocation-failure",fixture->app);
        fixture->core=app_candidate_core(fixture->app);
        REQUIRE("host-bind-survives-cache-allocation-failure",
            app_candidate_bind_core(fixture->app,"opaque-core",CORE_OFFSET,CORE_SIZE)==GEO_CANDIDATE_OK);
    }else{
        fixture->core=geo_candidate_create(CANDIDATE_ID,REVISION,STAMP);
        REQUIRE("kernel-create",fixture->core);
        REQUIRE("kernel-bind-survives-cache-allocation-failure",
            geo_candidate_bind_state(fixture->core,"opaque-bytes",fixture->before,fixture->after,SNAPSHOT_SIZE)==GEO_CANDIDATE_OK);
    }
    REQUIRE("initial-before-sha-exact-count",counts(1,0,0,host?1:0,0,0));
    REQUIRE("initial-kernel-sha-is-real",same_digest(kernel_trace.before,kernel_trace.size,kernel_trace.before_hash));
    REQUIRE("initial-host-sha-is-real",!host||same_digest(host_trace.before,host_trace.size,host_trace.before_hash));
    REQUIRE("only-before-cache-allocations-at-create",allocation_attempts[K_BEFORE]==1&&
        allocation_attempts[K_AFTER]==0&&allocation_attempts[H_BEFORE]==(host?1u:0u)&&allocation_attempts[H_AFTER]==0);
    return 0;
}
static void destroy(Fixture *fixture)
{if(fixture->host)app_candidate_destroy(fixture->app);else geo_candidate_destroy(fixture->core);}
static GeoCandidateStatus evaluate(Fixture *fixture)
{
    return fixture->host?app_candidate_evaluate(fixture->app,evaluate_host,fixture):
        geo_candidate_evaluate(fixture->core,evaluate_kernel,fixture);
}
static GeoCandidateStatus seal(Fixture *fixture)
{return fixture->host?app_candidate_seal(fixture->app):geo_candidate_seal(fixture->core);}
static GeoCandidateStatus check(Fixture *fixture)
{
    return fixture->host?app_candidate_check(fixture->app,fixture->live,REVISION,STAMP,equal_live,NULL):
        geo_candidate_check(fixture->core,REVISION,STAMP);
}
static GeoCandidateStatus reopen(Fixture *fixture)
{
    return fixture->host?app_candidate_reopen(fixture->app,fixture->live,REVISION,STAMP,equal_live,NULL):
        geo_candidate_reopen(fixture->core,REVISION,STAMP);
}
static bool evaluate_counts(bool host,unsigned failures)
{
    return counts(!!(failures&K_BEFORE),1,0,host&&!!(failures&H_BEFORE),host?1:0,0);
}
static bool checked_counts(bool host,unsigned failures,unsigned provider_checks)
{
    return counts(!!(failures&K_BEFORE),!!(failures&K_AFTER),provider_checks,
        host&&!!(failures&H_BEFORE),host&&!!(failures&H_AFTER),0);
}
static int evaluate_and_seal(Fixture *fixture,unsigned failures)
{
    reset_counts();REQUIRE("evaluation-success",evaluate(fixture)==GEO_CANDIDATE_OK);
    REQUIRE("evaluation-reuses-only-unchanged-before",evaluate_counts(fixture->host,failures));
    REQUIRE("evaluated-kernel-sha-is-real",same_digest(kernel_trace.after,kernel_trace.size,kernel_trace.after_hash));
    REQUIRE("evaluated-host-sha-is-real",!fixture->host||same_digest(host_trace.after,host_trace.size,host_trace.after_hash));
    reset_counts();REQUIRE("seal-success",seal(fixture)==GEO_CANDIDATE_OK);
    REQUIRE("seal-cache-or-complete-sha-fallback",checked_counts(fixture->host,failures,1));
    return 0;
}
static int unchanged(bool host)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,0)==0);
    REQUIRE("fixture-sealed",evaluate_and_seal(&fixture,0)==0);
    char before_hash[65],after_hash[65];
    memcpy(before_hash,kernel_trace.before_hash,65);memcpy(after_hash,kernel_trace.after_hash,65);
    for(unsigned i=0;i<5;++i){
        reset_counts();REQUIRE("unchanged-seal-valid",check(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("unchanged-state-does-not-call-sha",counts(0,0,1,0,0,0));
        REQUIRE("unchanged-keeps-original-sha",!strcmp(before_hash,kernel_trace.before_hash)&&!strcmp(after_hash,kernel_trace.after_hash));
    }
    REQUIRE("cache-copies-allocated-only-once",allocation_attempts[K_BEFORE]==1&&allocation_attempts[K_AFTER]==1&&
        allocation_attempts[H_BEFORE]==(host?1u:0u)&&allocation_attempts[H_AFTER]==(host?1u:0u));
    REQUIRE("read-checks-never-reevaluate",fixture.evaluations==1&&geo_candidate_evaluation_generation(fixture.core)==1);
    destroy(&fixture);return 0;
}
static int tampering(bool host)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,0)==0);
    REQUIRE("fixture-sealed",evaluate_and_seal(&fixture,0)==0);
    for(unsigned side=0;side<2;++side){
        unsigned char *bytes=side?fixture.after:fixture.before;
        /* H check also compares live with before. A before-only change would be
         * caught by that equality, so live moves with it: H's before key/SHA is
         * then the only guard deciding the verdict for that byte. */
        unsigned char *mirror=host&&!side?fixture.live:NULL;
        for(size_t i=0;i<SNAPSHOT_SIZE;++i){
            bytes[i]^=0x5a;if(mirror)mirror[i]^=0x5a;reset_counts();
            REQUIRE(host?"host-tamper-rejected":"kernel-tamper-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
            bool bound=!host||(i>=CORE_OFFSET&&i<CORE_OFFSET+CORE_SIZE);
            REQUIRE("every-changed-byte-takes-real-sha",counts(bound&&!side,bound&&side,host&&!bound,
                host&&!bound&&!side,host&&!bound&&side,0));
            bytes[i]^=0x5a;if(mirror)mirror[i]^=0x5a;reset_counts();
            REQUIRE("restoration-preserves-original-seal",check(&fixture)==GEO_CANDIDATE_OK);
            REQUIRE("restoration-reuses-original-byte-key",counts(0,0,1,0,0,0));
            REQUIRE("tamper-checks-never-reseal-or-reevaluate",geo_candidate_state(fixture.core)==GEO_CANDIDATE_SEALED&&
                fixture.evaluations==1&&geo_candidate_evaluation_generation(fixture.core)==1);
        }
    }
    destroy(&fixture);return 0;
}
static int unsealed_tampering(bool host)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,0)==0);
    fixture.before[0]^=1;reset_counts();
    REQUIRE("changed-before-blocks-evaluator",evaluate(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("before-evaluation-mismatch-takes-real-sha",counts(!host,0,0,host,0,0));
    REQUIRE("bad-before-never-calls-evaluator",fixture.evaluations==0&&geo_candidate_evaluation_generation(fixture.core)==0);
    fixture.before[0]^=1;reset_counts();
    REQUIRE("restored-before-can-evaluate",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("restored-before-reuses-original-key",evaluate_counts(host,0));
    fixture.after[SNAPSHOT_SIZE-1]^=1;reset_counts();
    REQUIRE("changed-evaluated-after-blocks-seal",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("before-seal-mismatch-takes-real-sha",counts(0,!host,0,0,host,0));
    fixture.after[SNAPSHOT_SIZE-1]^=1;reset_counts();
    REQUIRE("restored-evaluation-can-seal",seal(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("restored-evaluation-reuses-original-key",counts(0,0,1,0,0,0));
    destroy(&fixture);return 0;
}
static int lifecycle(bool host)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,0)==0);
    REQUIRE("initial-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    unsigned char previous[SNAPSHOT_SIZE],latest[SNAPSHOT_SIZE];
    for(unsigned round=0;round<4;++round){
        memcpy(previous,fixture.after,SNAPSHOT_SIZE);
        fixture.seed+=29;reset_counts();
        REQUIRE("repeated-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("each-evaluation-hashes-new-current-once",evaluate_counts(host,0));
        REQUIRE("generation-advances-only-with-evaluation",geo_candidate_evaluation_generation(fixture.core)==round+2&&fixture.evaluations==round+2);
        REQUIRE("new-kernel-hash-matches-latest-bytes",same_digest(kernel_trace.after,kernel_trace.size,kernel_trace.after_hash));
        REQUIRE("new-host-hash-matches-latest-bytes",!host||same_digest(host_trace.after,host_trace.size,host_trace.after_hash));
        memcpy(latest,fixture.after,SNAPSHOT_SIZE);memcpy(fixture.after,previous,SNAPSHOT_SIZE);reset_counts();
        REQUIRE("old-evaluation-cannot-use-new-seal",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("old-evaluation-takes-real-sha",counts(0,!host,0,0,host,0));
        memcpy(fixture.after,latest,SNAPSHOT_SIZE);reset_counts();
        REQUIRE("latest-evaluation-seals",seal(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("latest-evaluation-key-was-refreshed",counts(0,0,1,0,0,0));
        reset_counts();REQUIRE("reopen-rechecks-latest-seal",reopen(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("reopen-reuses-state-caches",counts(0,0,host?2:1,0,0,0));
        REQUIRE("reopen-preserves-identity-and-generation",geo_candidate_state(fixture.core)==GEO_CANDIDATE_OPEN&&
            geo_candidate_id(fixture.core)==CANDIDATE_ID&&geo_candidate_base_revision(fixture.core)==REVISION&&
            geo_candidate_evaluation_generation(fixture.core)==round+2);
    }
    REQUIRE("repeated-evaluation-reuses-allocated-cache",allocation_attempts[K_BEFORE]==1&&allocation_attempts[K_AFTER]==1&&
        allocation_attempts[H_BEFORE]==(host?1u:0u)&&allocation_attempts[H_AFTER]==(host?1u:0u));
    destroy(&fixture);return 0;
}
static int allocation_fallback(bool host,unsigned failures)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,failures)==0);
    REQUIRE("allocation-failures-do-not-change-evaluation-verdict",evaluate_and_seal(&fixture,failures)==0);
    reset_counts();REQUIRE("allocation-failures-do-not-change-check-verdict",check(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("missing-cache-hashes-every-protected-range",checked_counts(host,failures,1));
    /* Host byte zero is deliberately outside the bound K slice: H must guard
     * it independently. Kernel mode binds all bytes, including this byte. */
    for(unsigned side=0;side<2;++side){
        unsigned char *bytes=side?fixture.after:fixture.before;
        unsigned char *mirror=host&&!side?fixture.live:NULL; /* same live/before rule as tampering() */
        bytes[0]^=0x80;if(mirror)mirror[0]^=0x80;reset_counts();
        REQUIRE(host?"host-tamper-rejected":"kernel-tamper-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        if(host){
            REQUIRE("host-fallback-still-computes-real-sha",counts(!!(failures&K_BEFORE),!!(failures&K_AFTER),1,
                side?!!(failures&H_BEFORE):1,side?1:0,0));
        }else{
            REQUIRE("kernel-fallback-still-computes-real-sha",counts(side?!!(failures&K_BEFORE):1,side?1:0,0,0,0,0));
        }
        bytes[0]^=0x80;if(mirror)mirror[0]^=0x80;reset_counts();
        REQUIRE("fallback-restoration-keeps-original-seal",check(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("fallback-restoration-hashes-only-missing-caches",checked_counts(host,failures,1));
    }
    REQUIRE("read-checks-do-not-reallocate-cache",allocation_attempts[K_BEFORE]==1&&allocation_attempts[K_AFTER]==1&&
        allocation_attempts[H_BEFORE]==(host?1u:0u)&&allocation_attempts[H_AFTER]==(host?1u:0u));
    REQUIRE("fallback-never-changes-before-or-live",!memcmp(fixture.before,fixture.live,SNAPSHOT_SIZE));
    destroy(&fixture);return 0;
}
static int allocation_retry(bool host)
{
    unsigned failures=K_BEFORE|K_AFTER|(host?(H_BEFORE|H_AFTER):0);
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,host,failures)==0);
    reset_counts();REQUIRE("evaluation-survives-no-caches",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("no-cache-evaluation-hashes-before-and-after",evaluate_counts(host,failures));
    fail_allocations=0;fixture.seed+=51;reset_counts();
    REQUIRE("later-evaluation-retries-current-cache",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("retry-still-hashes-before-and-new-after",evaluate_counts(host,failures));
    REQUIRE("only-current-caches-retry-allocation",allocation_attempts[K_BEFORE]==1&&allocation_attempts[K_AFTER]==2&&
        allocation_attempts[H_BEFORE]==(host?1u:0u)&&allocation_attempts[H_AFTER]==(host?2u:0u));
    unsigned missing=K_BEFORE|(host?H_BEFORE:0);
    reset_counts();REQUIRE("retry-seals",seal(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("retry-caches-current-but-not-missing-before",checked_counts(host,missing,1));
    reset_counts();REQUIRE("retry-checks",check(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("retry-check-sha-counts",checked_counts(host,missing,1));
    fixture.after[0]^=1;reset_counts();
    REQUIRE("recovered-cache-remains-byte-keyed",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    if(host)REQUIRE("recovered-host-cache-mismatch-hashes",counts(1,0,1,1,1,0));
    else REQUIRE("recovered-kernel-cache-mismatch-hashes",counts(1,1,0,0,0,0));
    fixture.after[0]^=1;reset_counts();
    REQUIRE("recovered-cache-restoration-valid",check(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("recovered-cache-restoration-counts",checked_counts(host,missing,1));
    destroy(&fixture);return 0;
}
int main(int argc,char **argv)
{
    if(argc<2)return 2;
    const char *name=argv[1];bool host=!strncmp(name,"host-",5);
    const char *action=host?name+5:!strncmp(name,"kernel-",7)?name+7:NULL;
    if(!action)return 2;
    int result;
    if(!strcmp(action,"unchanged"))result=unchanged(host);
    else if(!strcmp(action,"tampering"))result=tampering(host);
    else if(!strcmp(action,"unsealed"))result=unsealed_tampering(host);
    else if(!strcmp(action,"lifecycle"))result=lifecycle(host);
    else if(!strcmp(action,"fallback")&&argc==3){
        char *end=NULL;unsigned long failures=strtoul(argv[2],&end,10);
        if(!end||*end||!failures||failures>15||(!host&&failures>3))return 2;
        result=allocation_fallback(host,(unsigned)failures);
    }else if(!strcmp(action,"retry"))result=allocation_retry(host);
    else return 2;
    if(!result)printf("PASS %s\n",name);
    return result;
}
