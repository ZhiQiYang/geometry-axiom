/* Keep the original independent linear graph oracle and allocation controls.
 * This client adds public-API witnesses for the generic hint-bucket change. */
static unsigned long long provider_hint_find_calls;
#define main provider_hint_original_main
#include "geo261_source_index_harness.c"
#undef main

static GeoEvalContext *provider_context(void)
{
    GeoSourceProvider providers[]={
        {2,"hint.two","test/1",NULL,describe,evaluate},
        {UINT32_C(0x80000002),"hint.high","test/1",NULL,describe,evaluate},
        {UINT32_MAX,"hint.max","test/1",NULL,describe,evaluate},
        {0,"hint.zero","test/1",NULL,describe,evaluate},
        {19,"hint.nineteen","test/1",NULL,describe,evaluate}};
    GeoEvalContext *ctx=geo_eval_create(31,19);
    if(ctx&&!geo_eval_register_many(ctx,providers,5)){geo_eval_destroy(ctx);return NULL;}
    return ctx;
}
static int provider_semantics(void)
{
    /* Deliberately unaligned keys; the middle byte differs, both ends match. */
    union { uint64_t aligned; unsigned char bytes[8]; } a_store={0},b_store={0};
    unsigned char *a=a_store.bytes,*b=b_store.bytes;a[2]=1;b[2]=2;
    REQUIRE("provider-hint-unaligned-keys",(uintptr_t)(a+1)%sizeof(uint64_t)!=0&&(uintptr_t)(b+1)%sizeof(uint64_t)!=0);
    GeoSourceRef input[]={
        {2,a+1,4},{UINT32_C(0x80000002),a+1,4},{UINT32_MAX,a+1,4},{0,a+1,4},
        {2,b+1,4},{2,NULL,0},{2,b+1,0},{19,a+1,4}};
    const char *labels[]={"provider-hint-first-node","provider-hint-full-width-provider",
        "provider-hint-full-width-provider","provider-hint-full-width-provider",
        "provider-hint-middle-byte-identity","provider-hint-zero-key",
        "provider-hint-zero-key","provider-hint-other-provider"};
    fail_indexes=1;GeoEvalContext *ctx=provider_context();REQUIRE("provider-hint-context",ctx);
    for(size_t i=0;i<sizeof input/sizeof *input;++i){GeoSourceValue value;linear_node(input[i]);
        REQUIRE("provider-hint-evaluate",geo_eval_source(ctx,input[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        REQUIRE(labels[i],geo_eval_node_count(ctx)==oracle_node_count);
        REQUIRE("provider-hint-ordered-public-graph",!graph_equal(ctx));
        REQUIRE("provider-hint-value",value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==7);
    }
    for(size_t i=sizeof input/sizeof *input;i-->0;){GeoSourceValue value;
        REQUIRE("provider-hint-repeat",geo_eval_source(ctx,input[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        REQUIRE("provider-hint-repeat-graph",!graph_equal(ctx));
    }
    REQUIRE("provider-hint-real-index-fallback",index_failures>0&&ctx->node_index_capacity==0);
    GeoSourceValue value,old;memset(&value,0x5a,sizeof value);memcpy(&old,&value,sizeof old);
    REQUIRE("provider-hint-malformed-key",geo_eval_source(ctx,(GeoSourceRef){2,NULL,1},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&!memcmp(&old,&value,sizeof value));
    REQUIRE("provider-hint-invalid-kind",geo_eval_depend(ctx,input[0],(GeoDependencyKind)99)==GEO_SOURCE_INVALID);
    REQUIRE("provider-hint-status-graph",!graph_equal(ctx));
    REQUIRE("provider-hint-seal",geo_eval_seal(ctx));
    REQUIRE("provider-hint-sealed-reset",!geo_eval_reset(ctx));
    REQUIRE("provider-hint-sealed-missing",geo_eval_source(ctx,(GeoSourceRef){999,NULL,0},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    geo_eval_destroy(ctx);REQUIRE("provider-hint-free",live_allocations==0);
    /* A new context may reuse addresses, but neither old ordinals nor hints. */
    oracle_node_count=oracle_edge_count=0;ctx=provider_context();REQUIRE("provider-hint-recreate",ctx);
    linear_node(input[0]);REQUIRE("provider-hint-recreated-node",geo_eval_depend(ctx,input[0],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK&&!graph_equal(ctx));
    REQUIRE("provider-hint-reset",geo_eval_reset(ctx)&&geo_eval_node_count(ctx)==0&&geo_eval_provider_count(ctx)==0);
    for(size_t i=0;i<256;++i)REQUIRE("provider-hint-clear",ctx->node_hint[i]==0);
    geo_eval_destroy(ctx);REQUIRE("provider-hint-reset-free",live_allocations==0);
    puts("PASS provider-hint-semantics");return 0;
}
static int provider_work(void)
{
    unsigned char a[4]={0,1,0,0},b[5]={16,2,0,0,0};
    GeoSourceRef pair[2]={{2,a,sizeof a},{19,b,sizeof b}};
    GeoEvalContext *ctx=provider_context();REQUIRE("provider-hint-work-context",ctx);
    for(size_t i=0;i<2;++i){linear_node(pair[i]);REQUIRE("provider-hint-warmup",geo_eval_depend(ctx,pair[i],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK);}
    provider_hint_find_calls=0;
    for(size_t repeat=0;repeat<8;++repeat)for(size_t i=0;i<2;++i)
        REQUIRE("provider-hint-work-status",geo_eval_depend(ctx,pair[i],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK);
    REQUIRE("provider-hint-work-public-graph",!graph_equal(ctx));
    unsigned long long calls=provider_hint_find_calls;geo_eval_destroy(ctx);
    REQUIRE("provider-hint-work-free",live_allocations==0);
    printf("PROVIDER_HINT_FIND_CALLS=%llu\n",calls);
    REQUIRE("provider-hint-cross-family-cache",calls==0);
    puts("PASS provider-hint-work");return 0;
}
int main(int argc,char **argv)
{
    if(argc==2&&!strcmp(argv[1],"provider-hint-semantics"))return provider_semantics();
    if(argc==2&&!strcmp(argv[1],"provider-hint-work"))return provider_work();
    return 2;
}
