/* 真 H/K 物件的整合 deferred-SHA 呼叫端；不替換 digest 或候選判決。
 * Python 只插樁真 SHA、四個 optional caches、constructor 與 provider metadata allocations。
 * 成功才輸出 SHA 收據；任何失敗必須先回報一個具名 ASSERT 並正常 exit 1。 */
#include "app_candidate.h"
#include "codec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(label, expression) do { if(!(expression)) { \
    fprintf(stderr,"ASSERT:%s line=%d expr=%s\n",label,__LINE__,#expression); return 1; \
} } while(0)
enum { K_BEFORE=1,K_AFTER=2,H_BEFORE=4,H_AFTER=8,H_HANDLE=16,K_HANDLE=32,K_TEXT=64,K_METADATA=128,
       SNAPSHOT_SIZE=96,CORE_OFFSET=16,CORE_SIZE=32,MAX_SHA_RECORDS=4096 };
typedef struct {
    const void *input;size_t size;unsigned char bytes[SNAPSHOT_SIZE];char digest[65];
} ShaRecord;
typedef struct Fixture Fixture;
typedef struct { Fixture *fixture;GeoEvalContext *sources; } EvalState;
struct Fixture {
    unsigned char live[SNAPSHOT_SIZE],before[SNAPSHOT_SIZE],after[SNAPSHOT_SIZE];
    unsigned char original[SNAPSHOT_SIZE],latest[SNAPSHOT_SIZE];
    AppCandidate *app;GeoCandidate *core;GeoEvalContext *sources;
    void *saved_before,*saved_after,*k_saved_before,*k_saved_after;
    uint64_t id;unsigned seed,evaluations,publications,equalities,disposals,errors;
    bool fail,change_before,preserve_view,change_core;
};
static const char STAMP[]="deferred-candidate/exact-snapshot/1";
static const uint64_t REVISION=43;
static ShaRecord host_records[MAX_SHA_RECORDS];
static size_t host_count;
static ShaRecord kernel_records[MAX_SHA_RECORDS];
static size_t kernel_count,kernel_mark;
static unsigned fail_allocations,attempts[256];
static void *last_allocation[256];
static void *allocation_history[256][4];
static const void *kernel_before,*kernel_after;

void candidate_cache_test_host_sha(const void *data,size_t size,char out[65])
{
    /* 非法輸入不能用假 digest 補救；crash 明確是 suite failure，絕非負控 killed。 */
    if(!data||size>SNAPSHOT_SIZE||host_count==MAX_SHA_RECORDS)abort();
    ShaRecord *record=&host_records[host_count++];record->input=data;record->size=size;
    memcpy(record->bytes,data,size);
    geo_sha256(data,size,out);memcpy(record->digest,out,65);
}
void candidate_cache_test_kernel_sha(const void *data,size_t size,char out[65])
{
    if(!data||size>SNAPSHOT_SIZE||kernel_count==MAX_SHA_RECORDS)abort();
    ShaRecord *record=&kernel_records[kernel_count++];record->input=data;record->size=size;
    memcpy(record->bytes,data,size);geo_sha256(data,size,out);memcpy(record->digest,out,65);
}
void *candidate_cache_test_alloc(size_t size,unsigned slot)
{
    if(slot!=K_BEFORE&&slot!=K_AFTER&&slot!=H_BEFORE&&slot!=H_AFTER&&slot!=K_TEXT&&slot!=K_METADATA)abort();
    ++attempts[slot];void *result=fail_allocations&slot?NULL:malloc(size);
    /* malloc 的未初始化內容不具契約；固定 poison 讓漏 copy 的突變可重現。 */
    if(result)memset(result,0xa5,size);
    if(attempts[slot]<=4)allocation_history[slot][attempts[slot]-1]=result;
    last_allocation[slot]=result;return result;
}
void *candidate_deferred_test_calloc(size_t count,size_t size,unsigned slot)
{
    if(slot!=H_HANDLE&&slot!=K_HANDLE)abort();
    ++attempts[slot];void *result=fail_allocations&slot?NULL:calloc(count,size);
    last_allocation[slot]=result;return result;
}
static void kernel_reset(Fixture *fixture)
{
    kernel_before=fixture->before+CORE_OFFSET;kernel_after=fixture->after+CORE_OFFSET;
    kernel_mark=kernel_count;
}
static bool k_input(size_t index,const void *pointer,const void *bytes,size_t size)
{
    return index<kernel_count&&kernel_records[index].input==pointer&&
        kernel_records[index].size==size&&!memcmp(kernel_records[index].bytes,bytes,size);
}
static bool k_provider(size_t index)
{
    /* Independent fixture bytes: BE64 count=1, token=91, lengths 21/15.
     * No saved state digest is allowed to masquerade as provider metadata. */
    unsigned char expected[68]={0};expected[7]=1;expected[15]=91;expected[23]=21;expected[52]=15;
    memcpy(expected+24,"deferred-test:neutral",21);memcpy(expected+53,"deferred-test/1",15);
    return index<kernel_count&&kernel_records[index].size==sizeof expected&&
        !memcmp(kernel_records[index].bytes,expected,sizeof expected);
}
static bool kernel_counts(unsigned before,unsigned after,unsigned providers)
{
    unsigned b=0,a=0,p=0;
    for(size_t i=kernel_mark;i<kernel_count;++i){
        if(k_input(i,kernel_before,kernel_before,CORE_SIZE))++b;
        else if(k_input(i,kernel_after,kernel_after,CORE_SIZE))++a;
        else if(k_provider(i))++p;
        else return false;
    }
    return b==before&&a==after&&p==providers;
}
static bool k_pair(size_t mark,const void *saved,const void *actual,const void *original,size_t size)
{
    return saved&&saved!=actual&&kernel_count==mark+2&&
        k_input(mark,saved,original,size)&&k_input(mark+1,actual,actual,size);
}
static bool h_input(size_t index,const void *pointer,const void *bytes)
{
    return index<host_count&&host_records[index].input==pointer&&
        host_records[index].size==SNAPSHOT_SIZE&&!memcmp(host_records[index].bytes,bytes,SNAPSHOT_SIZE);
}
static bool h_pair(size_t mark,const void *saved,const void *actual,const void *original)
{
    return host_count==mark+2&&h_input(mark,saved,original)&&h_input(mark+1,actual,actual);
}
static bool h_fallbacks(size_t mark,Fixture *fixture,unsigned mask)
{
    size_t next=mark;
    if(mask&H_BEFORE){if(!h_input(next++,fixture->before,fixture->before))return false;}
    if(mask&H_AFTER){if(!h_input(next++,fixture->after,fixture->after))return false;}
    return host_count==next;
}
static bool h_only(size_t index)
{return index<CORE_OFFSET||index>=CORE_OFFSET+CORE_SIZE;}
static void dispose_state(void *opaque)
{
    EvalState *state=opaque;Fixture *fixture=state->fixture;
    if(app_candidate_evaluation_state(fixture->app)!=state||
       geo_eval_candidate_id(state->sources)!=fixture->id)++fixture->errors;
    ++fixture->disposals;free(state);
}
static bool describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{(void)opaque;(void)source;memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;return true;}
static bool source_value(void *opaque,GeoEvalContext *sources,const GeoSourceRef *source,GeoSourceValue *out)
{
    (void)source;EvalState *state=opaque;
    if(state->sources!=sources)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_LENGTH};return true;
}
static bool evaluate_bytes(void *after,GeoEvalContext *sources,void *opaque)
{
    Fixture *fixture=opaque;
    if(after!=fixture->after||geo_eval_candidate_id(sources)!=fixture->id||
       geo_eval_base_revision(sources)!=REVISION||geo_eval_provider_count(sources)||
       geo_eval_node_count(sources)||geo_candidate_state(fixture->core)!=GEO_CANDIDATE_EVALUATING)return false;
    ++fixture->evaluations;fixture->sources=sources;
    EvalState *state=calloc(1,sizeof *state);if(!state)return false;
    state->fixture=fixture;state->sources=sources;
    app_candidate_set_evaluation_state(fixture->app,state,dispose_state);
    GeoSourceProvider provider={91,"deferred-test:neutral","deferred-test/1",state,describe,source_value};
    if(!geo_eval_register(sources,&provider))return false;
    unsigned key=1;GeoSourceRef ref={91,&key,sizeof key};GeoSourceValue result;
    if(geo_eval_source(sources,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&result)!=GEO_SOURCE_OK)return false;
    /* H 專用案例只改未綁定 bytes；跨層案例才明確改 K range。 */
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)if(h_only(i)||fixture->change_core)fixture->after[i]=(unsigned char)(fixture->seed+13u*(unsigned)i);
    fixture->after[5]=0;
    if(fixture->change_before){fixture->before[0]^=0x45;fixture->live[0]^=0x45;}
    return !fixture->fail;
}
static bool equal_live(const void *live,const void *before,void *opaque)
{
    Fixture *fixture=opaque;++fixture->equalities;
    if(!fixture->preserve_view)return !memcmp(live,before,SNAPSHOT_SIZE);
    return !memcmp(live,before,SNAPSHOT_SIZE-1);
}
static void publish_bytes(void *live,const void *after,void *opaque)
{
    Fixture *fixture=opaque;unsigned char view=fixture->live[SNAPSHOT_SIZE-1];
    if(live!=fixture->live||after!=fixture->after||geo_candidate_state(fixture->core)!=GEO_CANDIDATE_PUBLISHED||
       geo_candidate_sources(fixture->core)!=fixture->sources||!geo_eval_is_sealed(fixture->sources))++fixture->errors;
    ++fixture->publications;memcpy(live,after,SNAPSHOT_SIZE);
    if(fixture->preserve_view)fixture->live[SNAPSHOT_SIZE-1]=view;
}
static GeoCandidateStatus evaluate(Fixture *fixture)
{
    kernel_reset(fixture);unsigned allocations=attempts[H_AFTER],kernel_allocations=attempts[K_AFTER];
    GeoCandidateStatus status=app_candidate_evaluate(fixture->app,evaluate_bytes,fixture);
    if(attempts[H_AFTER]!=allocations)fixture->saved_after=last_allocation[H_AFTER];
    if(attempts[K_AFTER]!=kernel_allocations)fixture->k_saved_after=last_allocation[K_AFTER];
    if(status==GEO_CANDIDATE_OK)memcpy(fixture->latest,fixture->after,SNAPSHOT_SIZE);
    return status;
}
static GeoCandidateStatus seal(Fixture *fixture)
{kernel_reset(fixture);return app_candidate_seal(fixture->app);}
static GeoCandidateStatus check(Fixture *fixture)
{kernel_reset(fixture);return app_candidate_check(fixture->app,fixture->live,REVISION,STAMP,equal_live,fixture);}
static GeoCandidateStatus publish(Fixture *fixture)
{kernel_reset(fixture);return app_candidate_publish(fixture->app,fixture->live,REVISION,STAMP,equal_live,publish_bytes,fixture);}
static int create_fixture(Fixture *fixture,bool deferred,unsigned mask,uint64_t id)
{
    memset(fixture,0,sizeof *fixture);fixture->id=id;fixture->seed=37;fail_allocations=mask;
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)fixture->live[i]=(unsigned char)(7u+19u*(unsigned)i+(unsigned)id);
    fixture->live[0]=fixture->live[5]=0;memcpy(fixture->original,fixture->live,SNAPSHOT_SIZE);
    kernel_reset(fixture);
    fixture->app=deferred?app_candidate_create_deferred_sha(fixture->before,fixture->after,fixture->live,SNAPSHOT_SIZE,id,REVISION,STAMP):
        app_candidate_create(fixture->before,fixture->after,fixture->live,SNAPSHOT_SIZE,id,REVISION,STAMP);
    REQUIRE("fixture-create",fixture->app!=NULL);fixture->core=app_candidate_core(fixture->app);
    fixture->saved_before=last_allocation[H_BEFORE];
    REQUIRE("fixture-copies-complete-snapshot",!memcmp(fixture->before,fixture->original,SNAPSHOT_SIZE)&&!memcmp(fixture->after,fixture->original,SNAPSHOT_SIZE));
    REQUIRE("fixture-public-buffer-identity",app_candidate_before(fixture->app)==fixture->before&&app_candidate_after(fixture->app)==fixture->after);
    return 0;
}
static int bind_fixture(Fixture *fixture)
{
    kernel_reset(fixture);
    REQUIRE("fixture-bind",app_candidate_bind_core(fixture->app,"opaque-core",CORE_OFFSET,CORE_SIZE)==GEO_CANDIDATE_OK);
    fixture->k_saved_before=last_allocation[K_BEFORE];return 0;
}
static int initialize(Fixture *fixture,bool deferred,unsigned mask,uint64_t id)
{
    if(create_fixture(fixture,deferred,mask,id))return 1;
    return bind_fixture(fixture);
}
static int finish(Fixture *fixture)
{
    app_candidate_destroy(fixture->app);
    REQUIRE("disposal-lifetime-and-once",!fixture->errors&&fixture->disposals==fixture->evaluations);return 0;
}
static int prepare(Fixture *fixture)
{
    REQUIRE("fixture-initialized",initialize(fixture,true,0,701)==0);
    REQUIRE("deferred-valid-evaluation",evaluate(fixture)==GEO_CANDIDATE_OK);
    REQUIRE("deferred-valid-seal",seal(fixture)==GEO_CANDIDATE_OK);return 0;
}
static int normal(bool deferred)
{
    Fixture fixture;size_t mark=host_count;
    REQUIRE("fixture-initialized",initialize(&fixture,deferred,0,701)==0);
    if(deferred)REQUIRE("deferred-create-no-sha",host_count==mark);
    else REQUIRE("eager-create-real-sha",host_count==mark+1&&h_input(mark,fixture.before,fixture.original));
    REQUIRE(deferred?"deferred-bind-skips-state-sha":"eager-bind-real-sha",kernel_counts(deferred?0:1,0,0));
    REQUIRE("create-only-before-cache",attempts[H_BEFORE]==1&&attempts[H_AFTER]==0);
    mark=host_count;REQUIRE("deferred-valid-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE(deferred?"deferred-evaluation-skips-state-sha":"eager-evaluation-kernel-real-sha",kernel_counts(0,deferred?0:1,0));
    if(deferred)REQUIRE("deferred-evaluation-no-sha",host_count==mark);
    else REQUIRE("eager-evaluation-real-sha",host_count==mark+1&&h_input(mark,fixture.after,fixture.latest));
    mark=host_count;REQUIRE("deferred-valid-seal",seal(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("seal-kernel-provider-preserved",kernel_counts(0,0,1));
    for(unsigned i=0;i<3;++i){
        REQUIRE("deferred-unchanged-check",check(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("check-kernel-provider-preserved",kernel_counts(0,0,1));
    }
    REQUIRE("read-only-hits-no-sha",host_count==mark);
    REQUIRE("read-only-no-cache-reallocation",attempts[H_BEFORE]==1&&attempts[H_AFTER]==1);
    REQUIRE("read-only-no-evaluation",fixture.evaluations==1&&geo_candidate_evaluation_generation(fixture.core)==1);
    return finish(&fixture);
}
static int tamper(bool before,bool last_only)
{
    Fixture fixture;REQUIRE("fixture-prepared",prepare(&fixture)==0);
    unsigned char *actual=before?fixture.before:fixture.after;
    const void *saved=before?fixture.saved_before:fixture.saved_after;
    const void *original=before?(void*)fixture.original:(void*)fixture.latest;
    for(size_t i=last_only?SNAPSHOT_SIZE-1:0;i<SNAPSHOT_SIZE;++i)if(h_only(i)){
        for(unsigned repetition=0;repetition<2;++repetition){
            unsigned char change=(unsigned char)(0x51+repetition);actual[i]^=change;if(before)fixture.live[i]^=change;
            size_t mark=host_count;unsigned equalities=fixture.equalities;
            REQUIRE(before?"deferred-before-tamper-rejected":"deferred-after-tamper-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
            REQUIRE("deferred-pending-inputs-complete",h_pair(mark,saved,actual,original));
            REQUIRE("h-only-rejection-keeps-kernel-provider",kernel_counts(0,0,1));
            REQUIRE("h-rejection-before-equality",fixture.equalities==equalities);
            mark=host_count;REQUIRE("tamper-publication-rejected",publish(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
            REQUIRE("tamper-publication-hashes-original-pair",h_pair(mark,saved,actual,original)&&fixture.publications==0);
            REQUIRE("h-only-publication-rejection-keeps-kernel-provider",kernel_counts(0,0,1));
            actual[i]^=change;if(before)fixture.live[i]^=change;mark=host_count;
            REQUIRE("restoration-keeps-seal",check(&fixture)==GEO_CANDIDATE_OK);
            REQUIRE("restoration-no-sha",host_count==mark);
            REQUIRE("restoration-keeps-kernel-provider",kernel_counts(0,0,1));
        }
    }
    REQUIRE("tamper-keeps-state",fixture.evaluations==1&&geo_candidate_evaluation_generation(fixture.core)==1&&
        geo_candidate_state(fixture.core)==GEO_CANDIDATE_SEALED);
    REQUIRE("tamper-keeps-private-copies",!memcmp(fixture.saved_before,fixture.original,SNAPSHOT_SIZE)&&!memcmp(fixture.saved_after,fixture.latest,SNAPSHOT_SIZE));
    return finish(&fixture);
}
static int before_evaluate(void)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)if(h_only(i)){
        fixture.before[i]^=1;fixture.live[i]^=1;size_t mark=host_count;
        REQUIRE("deferred-before-evaluator-rejected",evaluate(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("before-evaluator-original-inputs",h_pair(mark,fixture.saved_before,fixture.before,fixture.original));
        REQUIRE("before-rejection-no-evaluator",fixture.evaluations==0&&geo_candidate_evaluation_generation(fixture.core)==0);
        fixture.before[i]^=1;fixture.live[i]^=1;
    }
    REQUIRE("restored-before-evaluates",evaluate(&fixture)==GEO_CANDIDATE_OK);return finish(&fixture);
}
static int after_seal(void)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);
    REQUIRE("deferred-valid-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)if(h_only(i)){
        fixture.after[i]^=1;size_t mark=host_count;
        REQUIRE("deferred-evaluated-after-rejected",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("after-seal-original-inputs",h_pair(mark,fixture.saved_after,fixture.after,fixture.latest));fixture.after[i]^=1;
    }
    REQUIRE("restored-after-seals",seal(&fixture)==GEO_CANDIDATE_OK);return finish(&fixture);
}
static int callback_before(void)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);fixture.change_before=true;
    REQUIRE("callback-completes-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);size_t mark=host_count;
    REQUIRE("callback-before-change-blocks-seal",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("callback-before-compares-original",h_pair(mark,fixture.saved_before,fixture.before,fixture.original));
    fixture.before[0]^=0x45;fixture.live[0]^=0x45;mark=host_count;
    REQUIRE("callback-before-restored-seals",seal(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("callback-before-restored-no-sha",host_count==mark);return finish(&fixture);
}
static int unevaluated(void)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);size_t mark=host_count;
    REQUIRE("unevaluated-seal-rejected",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("unevaluated-actual-only-no-null-input",host_count==mark+1&&h_input(mark,fixture.after,fixture.after));
    mark=host_count;REQUIRE("unevaluated-check-rejected",check(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("unevaluated-publish-rejected",publish(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("unevaluated-no-side-effects",host_count==mark&&fixture.evaluations==0&&fixture.publications==0&&attempts[H_AFTER]==0);
    return finish(&fixture);
}
static int failed_evaluation(bool prior_success)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);
    if(prior_success)REQUIRE("initial-success",evaluate(&fixture)==GEO_CANDIDATE_OK);
    unsigned allocations=attempts[H_AFTER];fixture.seed+=29;fixture.fail=true;size_t mark=host_count;
    REQUIRE("failed-evaluator-verdict",evaluate(&fixture)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("failed-after-rejected-by-h",seal(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    if(prior_success)REQUIRE("failed-evaluation-keeps-last-success",h_pair(mark,fixture.saved_after,fixture.after,fixture.latest));
    else REQUIRE("failed-first-has-no-pending-seal",host_count==mark+1&&h_input(mark,fixture.after,fixture.after));
    REQUIRE("failed-evaluation-no-cache-allocation",attempts[H_AFTER]==allocations);
    mark=host_count;REQUIRE("failed-check-keeps-state",check(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("failed-publication-keeps-state",publish(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("failed-no-publication-or-check-sha",fixture.publications==0&&host_count==mark);
    fixture.fail=false;fixture.seed+=31;REQUIRE("failed-candidate-can-recover",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("recovered-seal",seal(&fixture)==GEO_CANDIDATE_OK);return finish(&fixture);
}
static int lifecycle(void)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,0,701)==0);
    REQUIRE("lifecycle-initial-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("lifecycle-current-valid-seal",seal(&fixture)==GEO_CANDIDATE_OK);
    for(unsigned round=0;round<3;++round){
        unsigned char previous[SNAPSHOT_SIZE];memcpy(previous,fixture.after,SNAPSHOT_SIZE);
        size_t mark=host_count;unsigned disposals=fixture.disposals;
        kernel_reset(&fixture);
        REQUIRE("lifecycle-reopen",app_candidate_reopen(fixture.app,fixture.live,REVISION,STAMP,equal_live,&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("lifecycle-reopen-keeps-kernel-checks",kernel_counts(0,0,2));
        REQUIRE("lifecycle-reopen-disposes-state-first",fixture.disposals==disposals+1&&!app_candidate_evaluation_state(fixture.app)&&!geo_candidate_sources(fixture.core));
        REQUIRE("lifecycle-keeps-identity",geo_candidate_id(fixture.core)==fixture.id&&geo_candidate_base_revision(fixture.core)==REVISION&&
            geo_candidate_evaluation_generation(fixture.core)==round+1);
        fixture.seed+=17;REQUIRE("lifecycle-next-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("lifecycle-current-valid-seal",seal(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("lifecycle-unchanged-no-sha",host_count==mark);
        memcpy(fixture.after,previous,SNAPSHOT_SIZE);mark=host_count;
        REQUIRE("lifecycle-old-after-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("lifecycle-latest-saved-input",h_pair(mark,fixture.saved_after,fixture.after,fixture.latest));
        memcpy(fixture.after,fixture.latest,SNAPSHOT_SIZE);mark=host_count;
        REQUIRE("lifecycle-restored-check",check(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("lifecycle-restored-no-sha",host_count==mark);
    }
    REQUIRE("lifecycle-reuses-private-buffers",attempts[H_BEFORE]==1&&attempts[H_AFTER]==1);
    return finish(&fixture);
}
static int oom(unsigned mask)
{
    Fixture fixture;size_t created=host_count;REQUIRE("fixture-initialized",initialize(&fixture,true,mask,701)==0);
    REQUIRE("oom-kernel-before-capture",kernel_counts(!!(mask&K_BEFORE),0,0));
    size_t evaluated=host_count;REQUIRE("deferred-oom-valid-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("oom-kernel-evaluation-capture",kernel_counts(!!(mask&K_BEFORE),!!(mask&K_AFTER),0));
    size_t sealed=host_count;REQUIRE("deferred-oom-valid-seal",seal(&fixture)==GEO_CANDIDATE_OK);
    /* 先證明合法 verdict，再查 instrumentation；OOM omission 的首個紅點必須是正常 verdict。 */
    REQUIRE("oom-create-immediate-sha",evaluated==created+!!(mask&H_BEFORE)&&(!(mask&H_BEFORE)||h_input(created,fixture.before,fixture.original)));
    size_t count=evaluated;
    if(mask&H_BEFORE)REQUIRE("oom-evaluate-before-input",h_input(count++,fixture.before,fixture.original));
    if(mask&H_AFTER)REQUIRE("oom-evaluate-after-immediate-input",h_input(count++,fixture.after,fixture.latest));
    REQUIRE("oom-evaluate-exact-sha-count",sealed==count);
    REQUIRE("oom-seal-fallback-inputs",h_fallbacks(sealed,&fixture,mask));
    REQUIRE("oom-kernel-seal-counts",kernel_counts(!!(mask&K_BEFORE),!!(mask&K_AFTER),1));
    size_t mark=host_count;REQUIRE("oom-check-valid",check(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("oom-check-exact-inputs",h_fallbacks(mark,&fixture,mask));
    for(unsigned side=0;side<2;++side){
        unsigned char *actual=side?fixture.after:fixture.before;actual[0]^=0x80;if(!side)fixture.live[0]^=0x80;
        mark=host_count;unsigned equalities=fixture.equalities;
        REQUIRE("deferred-oom-tamper-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
        size_t next=mark;if(side&&(mask&H_BEFORE))REQUIRE("oom-before-first",h_input(next++,fixture.before,fixture.before));
        unsigned flag=side?H_AFTER:H_BEFORE;
        if(mask&flag)REQUIRE("oom-mismatch-actual-only",host_count==next+1&&h_input(next,actual,actual));
        else REQUIRE("oom-other-side-pending-pair",h_pair(next,side?fixture.saved_after:fixture.saved_before,actual,side?fixture.latest:fixture.original));
        REQUIRE("oom-h-rejection-before-equality",fixture.equalities==equalities);
        actual[0]^=0x80;if(!side)fixture.live[0]^=0x80;mark=host_count;
        REQUIRE("oom-restoration-valid",check(&fixture)==GEO_CANDIDATE_OK);
        REQUIRE("oom-restoration-exact-inputs",h_fallbacks(mark,&fixture,mask));
    }
    REQUIRE("oom-read-does-not-retry",attempts[K_BEFORE]==1&&attempts[K_AFTER]==1&&attempts[H_BEFORE]==1&&attempts[H_AFTER]==1);
    return finish(&fixture);
}
static int retry(unsigned mask)
{
    Fixture fixture;REQUIRE("fixture-initialized",initialize(&fixture,true,mask,701)==0);
    REQUIRE("retry-initial-evaluation",evaluate(&fixture)==GEO_CANDIDATE_OK);
    unsigned char previous[SNAPSHOT_SIZE];memcpy(previous,fixture.after,SNAPSHOT_SIZE);
    unsigned before_attempts=attempts[H_BEFORE],after_attempts=attempts[H_AFTER];
    fixture.fail=true;fixture.seed+=11;REQUIRE("retry-failed-evaluation",evaluate(&fixture)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("retry-failure-does-not-allocate",attempts[H_BEFORE]==before_attempts&&attempts[H_AFTER]==after_attempts);
    fixture.fail=false;fail_allocations=0;fixture.seed+=23;size_t mark=host_count;
    REQUIRE("retry-next-success",evaluate(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("retry-success-hashes-only-missing-before",host_count==mark+!!(mask&H_BEFORE)&&(!(mask&H_BEFORE)||h_input(mark,fixture.before,fixture.original)));
    REQUIRE("retry-current-valid-seal",seal(&fixture)==GEO_CANDIDATE_OK);
    memcpy(fixture.after,previous,SNAPSHOT_SIZE);mark=host_count;
    REQUIRE("retry-old-after-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    size_t next=mark;if(mask&H_BEFORE)REQUIRE("retry-missing-before-input",h_input(next++,fixture.before,fixture.original));
    REQUIRE("retry-clears-stale-digest",h_pair(next,fixture.saved_after,fixture.after,fixture.latest));
    memcpy(fixture.after,fixture.latest,SNAPSHOT_SIZE);REQUIRE("retry-restoration-valid",check(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("retry-only-after-allocation",attempts[H_BEFORE]==1&&attempts[H_AFTER]==2&&attempts[K_BEFORE]==1&&attempts[K_AFTER]==1+!!(mask&K_AFTER));
    return finish(&fixture);
}
static int publication(bool presentation)
{
    Fixture fixture;REQUIRE("fixture-prepared",prepare(&fixture)==0);size_t mark=host_count;
    fixture.preserve_view=presentation;if(presentation)fixture.live[SNAPSHOT_SIZE-1]=203;
    REQUIRE("publication-once",publish(&fixture)==GEO_CANDIDATE_OK);
    REQUIRE("publication-keeps-kernel-checks",kernel_counts(0,0,2));
    REQUIRE("publication-complete-root",!memcmp(fixture.live,fixture.latest,presentation?SNAPSHOT_SIZE-1:SNAPSHOT_SIZE));
    REQUIRE("publication-preserves-presentation",!presentation||fixture.live[SNAPSHOT_SIZE-1]==203);
    REQUIRE("publication-no-extra-sha-or-evaluation",host_count==mark&&fixture.evaluations==1&&fixture.publications==1&&fixture.disposals==0);
    REQUIRE("publication-repeat-rejected",publish(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("publication-terminal-evaluation",evaluate(&fixture)==GEO_CANDIDATE_STATE&&fixture.evaluations==1&&fixture.publications==1);
    return finish(&fixture);
}
static int discard_case(void)
{
    Fixture fixture;REQUIRE("fixture-prepared",prepare(&fixture)==0);app_candidate_discard(fixture.app);
    REQUIRE("discard-disposes-once",fixture.disposals==1&&!app_candidate_evaluation_state(fixture.app));
    REQUIRE("discard-terminal-check",check(&fixture)==GEO_CANDIDATE_STATE&&publish(&fixture)==GEO_CANDIDATE_STATE);
    REQUIRE("discard-terminal-evaluate",evaluate(&fixture)==GEO_CANDIDATE_STATE&&fixture.evaluations==1);
    app_candidate_discard(fixture.app);REQUIRE("discard-no-live-write",!memcmp(fixture.live,fixture.original,SNAPSHOT_SIZE));return finish(&fixture);
}
static int invalid(void)
{
    unsigned char live[SNAPSHOT_SIZE+1]={0},before[SNAPSHOT_SIZE+1]={0},after[SNAPSHOT_SIZE+1]={0};
#define CREATE(b,a,l,s,t) app_candidate_create_deferred_sha((b),(a),(l),(s),701,REVISION,(t))
    REQUIRE("invalid-null-before",CREATE(NULL,after,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-null-after",CREATE(before,NULL,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-null-live",CREATE(before,after,NULL,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-zero-size",CREATE(before,after,live,0,STAMP)==NULL);
    REQUIRE("invalid-before-after-overlap",CREATE(before,before+1,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-before-live-overlap",CREATE(live+1,after,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-after-live-overlap",CREATE(before,live+1,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-before-overflow",CREATE((void*)(uintptr_t)(UINTPTR_MAX-3),after,live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-after-overflow",CREATE(before,(void*)(uintptr_t)(UINTPTR_MAX-3),live,SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-live-overflow",CREATE(before,after,(void*)(uintptr_t)(UINTPTR_MAX-3),SNAPSHOT_SIZE,STAMP)==NULL);
    REQUIRE("invalid-empty-stamp",CREATE(before,after,live,SNAPSHOT_SIZE,"")==NULL);
    REQUIRE("invalid-null-stamp",CREATE(before,after,live,SNAPSHOT_SIZE,NULL)==NULL);
#undef CREATE
    REQUIRE("invalid-no-cache-or-sha",host_count==0&&attempts[H_BEFORE]==0&&attempts[H_AFTER]==0);return 0;
}
static int constructor_oom(unsigned mask)
{
    unsigned char live[SNAPSHOT_SIZE],before[SNAPSHOT_SIZE],after[SNAPSHOT_SIZE];
    memset(live,0x3c,sizeof live);memset(before,0xa5,sizeof before);memset(after,0x5a,sizeof after);fail_allocations=mask;
    REQUIRE("constructor-allocation-fails-cleanly",app_candidate_create_deferred_sha(before,after,live,SNAPSHOT_SIZE,701,REVISION,STAMP)==NULL);
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)REQUIRE("constructor-failure-preserves-buffers",live[i]==0x3c&&before[i]==0xa5&&after[i]==0x5a);
    REQUIRE("constructor-failure-before-capture",host_count==0&&attempts[H_BEFORE]==0&&attempts[H_AFTER]==0&&attempts[mask]==1);
    Fixture fixture;REQUIRE("constructor-can-recover",initialize(&fixture,true,0,701)==0);return finish(&fixture);
}
static int isolation(void)
{
    Fixture left,right;REQUIRE("left-initialized",initialize(&left,true,0,701)==0);REQUIRE("right-initialized",initialize(&right,true,0,702)==0);
    REQUIRE("left-evaluated",evaluate(&left)==GEO_CANDIDATE_OK);REQUIRE("left-sealed",seal(&left)==GEO_CANDIDATE_OK);
    right.seed+=47;REQUIRE("right-evaluated",evaluate(&right)==GEO_CANDIDATE_OK);REQUIRE("right-sealed",seal(&right)==GEO_CANDIDATE_OK);
    REQUIRE("candidate-private-storage",left.saved_before!=right.saved_before&&left.saved_after!=right.saved_after&&left.sources!=right.sources);
    unsigned char backup[SNAPSHOT_SIZE];memcpy(backup,left.after,SNAPSHOT_SIZE);
    /* 只搬 H bytes；K bindings 保持各自值，不能遮蔽跨候選 baseline 混用。 */
    for(size_t i=0;i<SNAPSHOT_SIZE;++i)if(h_only(i))left.after[i]=right.after[i];
    size_t mark=host_count;REQUIRE("cross-candidate-after-rejected",check(&left)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("cross-candidate-own-saved-input",h_pair(mark,left.saved_after,left.after,left.latest));
    REQUIRE("other-candidate-unaffected",check(&right)==GEO_CANDIDATE_OK);
    memcpy(left.after,backup,SNAPSHOT_SIZE);REQUIRE("own-candidate-restored",check(&left)==GEO_CANDIDATE_OK);
    REQUIRE("left-finished",finish(&left)==0);return finish(&right);
}
static int guard_priority(void)
{
    Fixture fixture;REQUIRE("fixture-prepared",prepare(&fixture)==0);fixture.after[0]^=1;size_t mark=host_count;
    REQUIRE("revision-before-h",app_candidate_check(fixture.app,fixture.live,REVISION+1,STAMP,equal_live,&fixture)==GEO_CANDIDATE_REVISION_CHANGED);
    REQUIRE("stamp-before-h",app_candidate_check(fixture.app,fixture.live,REVISION,"other",equal_live,&fixture)==GEO_CANDIDATE_PROVIDER_CHANGED);
    GeoSourceProvider *provider=(GeoSourceProvider*)geo_eval_provider_at(fixture.sources,0);REQUIRE("provider-present",provider!=NULL);
    ++provider->token;REQUIRE("provider-before-h",check(&fixture)==GEO_CANDIDATE_PROVIDER_CHANGED);--provider->token;
    REQUIRE("core-guards-no-h-sha",host_count==mark&&fixture.equalities==0&&fixture.publications==0);
    REQUIRE("restored-core-still-checks-h",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("restored-core-pending-inputs",h_pair(mark,fixture.saved_after,fixture.after,fixture.latest));
    fixture.after[0]^=1;fixture.live[0]^=1;mark=host_count;
    REQUIRE("live-change-still-rejected",check(&fixture)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("live-equality-after-h-hits",host_count==mark&&fixture.equalities==1);fixture.live[0]^=1;return finish(&fixture);
}
/* Cost cases are deliberately separate from the mode-independent correctness
 * case. A withdrawal must hit its named cost assertion, not a setup assertion. */
static int create_policy(bool deferred)
{
    Fixture f;size_t mark=host_count;
    if(create_fixture(&f,deferred,0,701))return 1;
    REQUIRE(deferred?"deferred-create-no-sha":"eager-create-real-sha",
        deferred?host_count==mark:host_count==mark+1&&h_input(mark,f.before,f.original));
    REQUIRE("create-has-no-kernel-state-or-provider-sha",kernel_count==0);
    return finish(&f);
}
static int bind_policy(void)
{
    Fixture f;if(initialize(&f,true,0,701))return 1;
    REQUIRE("deferred-bind-skips-state-sha",kernel_counts(0,0,0));return finish(&f);
}
static int bound_tamper(void)
{
    Fixture f;if(prepare(&f))return 1;
    for(unsigned side=0;side<2;++side){
        unsigned char *actual=(side?f.after:f.before)+CORE_OFFSET;
        const void *saved=side?f.k_saved_after:f.k_saved_before;
        const unsigned char *original=(side?f.latest:f.original)+CORE_OFFSET;
        for(size_t i=0;i<CORE_SIZE;++i)for(unsigned repetition=0;repetition<2;++repetition){
            unsigned char change=(unsigned char)(0x51+repetition);actual[i]^=change;
            if(!side)f.live[CORE_OFFSET+i]^=change;
            kernel_reset(&f);size_t mark=kernel_count,hmark=host_count;unsigned equalities=f.equalities;
            REQUIRE(side?"kernel-after-tamper-rejected":"kernel-before-tamper-rejected",
                geo_candidate_check(f.core,REVISION,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
            REQUIRE("kernel-direct-saved-actual-pair",k_pair(mark,saved,actual,original,CORE_SIZE));
            REQUIRE("kernel-direct-never-invokes-host",host_count==hmark&&f.equalities==equalities);
            mark=kernel_count;
            REQUIRE("host-check-rejects-through-kernel-first",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
            REQUIRE("host-check-keeps-kernel-saved-actual-pair",k_pair(mark,saved,actual,original,CORE_SIZE));
            REQUIRE("kernel-rejection-precedes-host-snapshot",host_count==hmark&&f.equalities==equalities);
            mark=kernel_count;
            REQUIRE("kernel-tamper-cannot-publish",publish(&f)==GEO_CANDIDATE_STATE_CHANGED&&f.publications==0);
            REQUIRE("publication-retains-kernel-guard",k_pair(mark,saved,actual,original,CORE_SIZE)&&host_count==hmark);
            actual[i]^=change;if(!side)f.live[CORE_OFFSET+i]^=change;
            REQUIRE("kernel-restoration-keeps-same-seal",check(&f)==GEO_CANDIDATE_OK);
            REQUIRE("kernel-restored-hit-only-provider-sha",kernel_counts(0,0,1)&&host_count==hmark);
        }
    }
    REQUIRE("kernel-tamper-preserves-original-copies",
        !memcmp(f.k_saved_before,f.original+CORE_OFFSET,CORE_SIZE)&&
        !memcmp(f.k_saved_after,f.latest+CORE_OFFSET,CORE_SIZE));
    REQUIRE("kernel-tamper-no-reevaluation",f.evaluations==1&&geo_candidate_evaluation_generation(f.core)==1);
    return finish(&f);
}
static int cross_recovery(unsigned mask)
{
    Fixture f;if(initialize(&f,true,mask,701))return 1;f.change_core=true;
    REQUIRE("cross-initial-evaluation",evaluate(&f)==GEO_CANDIDATE_OK);
    unsigned char old[SNAPSHOT_SIZE];memcpy(old,f.after,sizeof old);
    unsigned h_attempts=attempts[H_AFTER],k_attempts=attempts[K_AFTER];
    f.fail=true;f.seed+=11;
    REQUIRE("cross-failed-evaluation",evaluate(&f)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("cross-failure-does-not-capture-either-layer",attempts[H_AFTER]==h_attempts&&attempts[K_AFTER]==k_attempts&&
        (!f.saved_after||!memcmp(f.saved_after,old,SNAPSHOT_SIZE))&&
        (!f.k_saved_after||!memcmp(f.k_saved_after,old+CORE_OFFSET,CORE_SIZE)));
    REQUIRE("cross-failure-cannot-publish",publish(&f)==GEO_CANDIDATE_STATE&&f.publications==0);
    f.fail=false;fail_allocations=0;f.seed+=23;size_t hmark=host_count;
    REQUIRE("cross-recovery-evaluates",evaluate(&f)==GEO_CANDIDATE_OK);
    REQUIRE("cross-recovery-defers-both-current-captures",host_count==hmark&&kernel_counts(0,0,0));
    REQUIRE("cross-recovery-retries-only-missing-current",attempts[H_BEFORE]==1&&attempts[K_BEFORE]==1&&
        attempts[H_AFTER]==1+!!(mask&H_AFTER)&&attempts[K_AFTER]==1+!!(mask&K_AFTER));
    memcpy(f.after,old,SNAPSHOT_SIZE);hmark=host_count;
    /* H seal checks its snapshot before K. A K rejection must not conceal a
     * stale H digest: require H's actual saved/actual pair and no K call. */
    REQUIRE("cross-old-full-snapshot-cannot-seal",seal(&f)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("cross-recovery-h-current-saved-pair",h_pair(hmark,f.saved_after,f.after,f.latest)&&kernel_counts(0,0,0));
    memcpy(f.after,f.latest,SNAPSHOT_SIZE);
    REQUIRE("cross-current-seals",seal(&f)==GEO_CANDIDATE_OK);
    memcpy(f.after+CORE_OFFSET,old+CORE_OFFSET,CORE_SIZE);kernel_reset(&f);size_t kmark=kernel_count;hmark=host_count;
    REQUIRE("cross-k-old-generation-rejected",geo_candidate_check(f.core,REVISION,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    REQUIRE("cross-recovery-k-current-saved-pair",k_pair(kmark,f.k_saved_after,f.after+CORE_OFFSET,f.latest+CORE_OFFSET,CORE_SIZE)&&host_count==hmark);
    memcpy(f.after+CORE_OFFSET,f.latest+CORE_OFFSET,CORE_SIZE);
    REQUIRE("cross-restoration-valid",check(&f)==GEO_CANDIDATE_OK);
    REQUIRE("cross-restoration-only-provider",kernel_counts(0,0,1)&&host_count==hmark);
    REQUIRE("cross-recovered-complete-publication",publish(&f)==GEO_CANDIDATE_OK&&f.publications==1&&!memcmp(f.live,f.latest,SNAPSHOT_SIZE));
    return finish(&f);
}
static int coexist(void)
{
    Fixture eager,deferred;size_t mark=host_count;
    if(initialize(&eager,false,0,701))return 1;
    REQUIRE("coexist-eager-create-and-bind",host_count==mark+1&&h_input(mark,eager.before,eager.original)&&kernel_counts(1,0,0));
    mark=host_count;if(initialize(&deferred,true,0,702))return 1;
    REQUIRE("coexist-deferred-create-and-bind",host_count==mark&&kernel_counts(0,0,0));
    mark=host_count;REQUIRE("coexist-eager-evaluates",evaluate(&eager)==GEO_CANDIDATE_OK);
    REQUIRE("coexist-eager-captures-both-layers",host_count==mark+1&&h_input(mark,eager.after,eager.latest)&&kernel_counts(0,1,0));
    mark=host_count;REQUIRE("coexist-deferred-evaluates",evaluate(&deferred)==GEO_CANDIDATE_OK);
    REQUIRE("coexist-deferred-captures-neither-digest",host_count==mark&&kernel_counts(0,0,0));
    REQUIRE("coexist-eager-seals",seal(&eager)==GEO_CANDIDATE_OK&&kernel_counts(0,0,1));
    REQUIRE("coexist-deferred-seals",seal(&deferred)==GEO_CANDIDATE_OK&&kernel_counts(0,0,1));
    for(unsigned round=0;round<3;++round){
        REQUIRE("coexist-eager-check",check(&eager)==GEO_CANDIDATE_OK&&kernel_counts(0,0,1));
        REQUIRE("coexist-deferred-check",check(&deferred)==GEO_CANDIDATE_OK&&kernel_counts(0,0,1));
    }
    REQUIRE("coexist-independent-owned-copies",eager.saved_before!=deferred.saved_before&&eager.saved_after!=deferred.saved_after&&
        eager.k_saved_before!=deferred.k_saved_before&&eager.k_saved_after!=deferred.k_saved_after&&host_count==mark);
    if(finish(&eager))return 1;return finish(&deferred);
}
static int split_ranges(void)
{
    Fixture f;if(create_fixture(&f,true,0,701))return 1;f.change_core=true;
    for(unsigned range=0;range<2;++range)
        REQUIRE("split-bind-real-ranges",app_candidate_bind_core(f.app,range?"right":"left",CORE_OFFSET+range*16,16)==GEO_CANDIDATE_OK);
    REQUIRE("split-bind-no-state-sha",kernel_count==0);
    REQUIRE("split-evaluates",evaluate(&f)==GEO_CANDIDATE_OK);
    REQUIRE("split-evaluation-no-state-sha",kernel_count==0);
    REQUIRE("split-seals",seal(&f)==GEO_CANDIDATE_OK);
    for(unsigned side=0;side<2;++side)for(unsigned range=0;range<2;++range)for(size_t byte=0;byte<16;++byte){
        size_t offset=CORE_OFFSET+range*16;unsigned char *actual=(side?f.after:f.before)+offset;
        const unsigned char *original=(side?f.latest:f.original)+offset;
        void *saved=allocation_history[side?K_AFTER:K_BEFORE][range];actual[byte]^=1;
        kernel_reset(&f);size_t mark=kernel_count,hmark=host_count;
        REQUIRE("split-range-tamper-rejected",geo_candidate_check(f.core,REVISION,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
        REQUIRE("split-only-mutated-range-hashed",k_pair(mark,saved,actual,original,16)&&host_count==hmark);
        actual[byte]^=1;REQUIRE("split-restored-host-check",check(&f)==GEO_CANDIDATE_OK);
    }
    REQUIRE("split-full-publication",publish(&f)==GEO_CANDIDATE_OK&&!memcmp(f.live,f.latest,SNAPSHOT_SIZE));return finish(&f);
}
static int metadata_oom(void)
{
    Fixture f;if(initialize(&f,true,0,701))return 1;
    REQUIRE("metadata-evaluates",evaluate(&f)==GEO_CANDIDATE_OK);fail_allocations=K_METADATA;
    REQUIRE("metadata-seal-failure-is-memory",seal(&f)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-seal-failure-keeps-evaluated",geo_candidate_state(f.core)==GEO_CANDIDATE_EVALUATED&&
        !geo_eval_is_sealed(f.sources)&&kernel_counts(0,0,0)&&f.publications==0);
    fail_allocations=0;REQUIRE("metadata-seal-recovers",seal(&f)==GEO_CANDIDATE_OK);fail_allocations=K_METADATA;
    void *state=app_candidate_evaluation_state(f.app);unsigned disposals=f.disposals;
    REQUIRE("metadata-check-failure-is-memory",check(&f)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-publish-failure-is-memory",publish(&f)==GEO_CANDIDATE_MEMORY&&f.publications==0);
    REQUIRE("metadata-reopen-failure-is-memory",app_candidate_reopen(f.app,f.live,REVISION,STAMP,equal_live,&f)==GEO_CANDIDATE_MEMORY);
    REQUIRE("metadata-failure-keeps-owner-and-seal",app_candidate_evaluation_state(f.app)==state&&f.disposals==disposals&&
        geo_candidate_state(f.core)==GEO_CANDIDATE_SEALED&&geo_eval_is_sealed(f.sources));
    fail_allocations=0;REQUIRE("metadata-check-recovers",check(&f)==GEO_CANDIDATE_OK&&kernel_counts(0,0,1));return finish(&f);
}
static int policy_correctness(void)
{
    /* Identical client and expected functional behavior for 00/01/10/11.
     * No expected policy is passed in and no SHA verdict is substituted. */
    Fixture f;if(initialize(&f,true,0,701))return 1;f.change_core=true;
    REQUIRE("policy-evaluates",evaluate(&f)==GEO_CANDIDATE_OK);
    REQUIRE("policy-seals",seal(&f)==GEO_CANDIDATE_OK);
    for(unsigned side=0;side<2;++side){
        unsigned char *actual=side?f.after:f.before;
        for(size_t byte=0;byte<SNAPSHOT_SIZE;++byte){
            actual[byte]^=1;if(!side)f.live[byte]^=1;
            REQUIRE("policy-full-snapshot-tamper-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
            REQUIRE("policy-tamper-never-publishes",publish(&f)==GEO_CANDIDATE_STATE_CHANGED&&f.publications==0);
            if(!h_only(byte))REQUIRE("policy-bound-state-independently-rejected",geo_candidate_check(f.core,REVISION,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
            actual[byte]^=1;if(!side)f.live[byte]^=1;
            REQUIRE("policy-restoration-valid",check(&f)==GEO_CANDIDATE_OK);
        }
    }
    uint64_t id=geo_candidate_id(f.core);unsigned char old[SNAPSHOT_SIZE];memcpy(old,f.after,SNAPSHOT_SIZE);
    REQUIRE("policy-reopens-same-handle",app_candidate_reopen(f.app,f.live,REVISION,STAMP,equal_live,&f)==GEO_CANDIDATE_OK&&
        geo_candidate_id(f.core)==id&&geo_candidate_evaluation_generation(f.core)==1);
    f.fail=true;f.seed+=11;REQUIRE("policy-failed-evaluation",evaluate(&f)==GEO_CANDIDATE_EVALUATION_FAILED);
    REQUIRE("policy-failure-never-publishes",publish(&f)==GEO_CANDIDATE_STATE&&f.publications==0);
    f.fail=false;f.seed+=23;REQUIRE("policy-recovery-evaluates",evaluate(&f)==GEO_CANDIDATE_OK);
    REQUIRE("policy-recovery-seals",seal(&f)==GEO_CANDIDATE_OK);
    memcpy(f.after,old,SNAPSHOT_SIZE);REQUIRE("policy-old-generation-rejected",check(&f)==GEO_CANDIDATE_STATE_CHANGED);
    memcpy(f.after,f.latest,SNAPSHOT_SIZE);
    REQUIRE("policy-complete-root-publication",publish(&f)==GEO_CANDIDATE_OK&&f.publications==1&&
        !memcmp(f.live,f.latest,SNAPSHOT_SIZE)&&geo_candidate_id(f.core)==id&&geo_candidate_evaluation_generation(f.core)==3);
    REQUIRE("policy-no-second-publication",publish(&f)==GEO_CANDIDATE_STATE&&f.publications==1);
    return finish(&f);
}
int main(int argc,char **argv)
{
    if(argc<2||argc>3)return 2;const char *name=argv[1];unsigned mask=0;
    if(argc==3){char *end=NULL;unsigned long value=strtoul(argv[2],&end,10);if(!end||*end||value>255)return 2;mask=(unsigned)value;}
    int result;
    if(!strcmp(name,"normal"))result=normal(true);
    else if(!strcmp(name,"eager"))result=normal(false);
    else if(!strcmp(name,"create"))result=create_policy(true);
    else if(!strcmp(name,"eager-create"))result=create_policy(false);
    else if(!strcmp(name,"bind"))result=bind_policy();
    else if(!strcmp(name,"before-check"))result=tamper(true,false);
    else if(!strcmp(name,"after-check"))result=tamper(false,false);
    else if(!strcmp(name,"last-byte"))result=tamper(false,true);
    else if(!strcmp(name,"before-evaluate"))result=before_evaluate();
    else if(!strcmp(name,"after-seal"))result=after_seal();
    else if(!strcmp(name,"callback-before"))result=callback_before();
    else if(!strcmp(name,"unevaluated"))result=unevaluated();
    else if(!strcmp(name,"failed-first"))result=failed_evaluation(false);
    else if(!strcmp(name,"failed-later"))result=failed_evaluation(true);
    else if(!strcmp(name,"lifecycle"))result=lifecycle();
    else if(!strcmp(name,"oom")&&argc==3&&mask<=15)result=oom(mask);
    else if(!strcmp(name,"retry")&&argc==3&&(mask&H_AFTER)&&mask<=15)result=retry(mask);
    else if(!strcmp(name,"publication"))result=publication(false);
    else if(!strcmp(name,"presentation"))result=publication(true);
    else if(!strcmp(name,"discard"))result=discard_case();
    else if(!strcmp(name,"invalid"))result=invalid();
    else if(!strcmp(name,"constructor-oom")&&argc==3&&(mask==H_HANDLE||mask==K_HANDLE||mask==K_TEXT))result=constructor_oom(mask);
    else if(!strcmp(name,"isolation"))result=isolation();
    else if(!strcmp(name,"guard-priority"))result=guard_priority();
    else if(!strcmp(name,"bound-tamper"))result=bound_tamper();
    else if(!strcmp(name,"cross-recovery")&&argc==3&&(mask==H_AFTER||mask==K_AFTER||mask==(H_AFTER|K_AFTER)))result=cross_recovery(mask);
    else if(!strcmp(name,"coexist"))result=coexist();
    else if(!strcmp(name,"split-ranges"))result=split_ranges();
    else if(!strcmp(name,"metadata-oom"))result=metadata_oom();
    else if(!strcmp(name,"policy-correctness"))result=policy_correctness();
    else return 2;
    if(result)return result;
    for(unsigned layer=0;layer<2;++layer)for(size_t i=0;i<(layer?kernel_count:host_count);++i){
        ShaRecord *record=layer?&kernel_records[i]:&host_records[i];printf("SHA %c %zu ",layer?'K':'H',record->size);
        for(size_t j=0;j<record->size;++j)printf("%02x",record->bytes[j]);
        printf(" %s\n",record->digest);
    }
    printf("PASS %s\n",name);return 0;
}
