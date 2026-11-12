/* The unchanged source-index fixture supplies allocator fault injection and an
 * independent ordered graph oracle. Only this private TU includes source.c. */
#include <stddef.h>
static size_t node_hash_calls,node_probe_steps,node_find_calls;
#define main original_source_index_main
#include "geo261_source_index_harness.c"
#undef main

static int hinted(GeoEvalContext *ctx,GeoSourceRef ref,GeoDependencyKind kind,size_t *hint)
{
    size_t expected=linear_node(ref);
    if(ctx->active!=SIZE_MAX)linear_edge(ctx->active,expected,kind);
    REQUIRE("depend-hint-status",geo_eval_depend_hint(ctx,ref,kind,hint)==GEO_SOURCE_OK);
    REQUIRE("depend-hint-full-identity",geo_eval_node_count(ctx)==oracle_node_count&&(!hint||*hint==expected+1));
    REQUIRE("depend-hint-current-consumer-edge",geo_eval_edge_count(ctx)==oracle_edge_count);
    REQUIRE("depend-hint-exact-order",!graph_equal(ctx));return 0;
}
static int identity(void)
{
    GeoEvalContext *ctx=context();REQUIRE("identity-context",ctx);size_t hint=0;
    if(hinted(ctx,refs[0],GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    if(hinted(ctx,refs[1],GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    GeoSourceRef provider={29,keys[1],sizeof keys[1]},shorter={17,keys[1],1};
    if(hinted(ctx,provider,GEO_DEPENDENCY_VALUE_REQUIRED,&hint)||
       hinted(ctx,shorter,GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    unsigned char alias[12];memcpy(alias,keys[0],sizeof alias);GeoSourceRef copy={17,alias,sizeof alias};
    if(hinted(ctx,copy,GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    alias[0]=1; /* Same address, now the exact bytes of refs[1]. */
    if(hinted(ctx,copy,GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    GeoSourceRef empty={17,NULL,0},empty_alias={17,alias,0};
    if(hinted(ctx,empty,GEO_DEPENDENCY_VALUE_REQUIRED,&hint)||
       hinted(ctx,empty_alias,GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    hint=SIZE_MAX;if(hinted(ctx,refs[0],GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    hint=ctx->node_count+1;if(hinted(ctx,refs[1],GEO_DEPENDENCY_VALUE_REQUIRED,&hint))return 1;
    REQUIRE("identity-depend-does-not-evaluate",!descriptions&&!evaluations);
    geo_eval_destroy(ctx);REQUIRE("identity-no-leak",!live_allocations);return 0;
}
static int reset_context(void)
{
    GeoEvalContext *a=context(),*b=context();REQUIRE("reset-contexts",a&&b);size_t hint=0;
    REQUIRE("reset-first",geo_eval_depend_hint(a,refs[0],0,&hint)==GEO_SOURCE_OK&&hint==1);
    REQUIRE("reset-other-order",geo_eval_depend(b,refs[1],0)==GEO_SOURCE_OK);
    oracle_node_count=oracle_edge_count=0;linear_node(refs[1]);
    if(hinted(b,refs[0],0,&hint))return 1;
    REQUIRE("reset-different-context-ordinal",hint==2);
    REQUIRE("reset-allowed",geo_eval_reset(b));oracle_node_count=oracle_edge_count=0;
    GeoSourceProvider p={17,"hint.reset","test/1",NULL,describe,evaluate};
    REQUIRE("reset-register",geo_eval_register(b,&p));
    if(hinted(b,refs[2],0,&hint))return 1;
    REQUIRE("reset-out-of-range-replaced",hint==1);
    if(hinted(b,refs[0],0,&hint))return 1;
    REQUIRE("reset-same-ordinal-new-identity",hint==2);
    hint=1;oracle_node_count=oracle_edge_count=0;linear_node(refs[0]);
    if(hinted(a,refs[0],0,&hint))return 1;
    REQUIRE("reset-no-provider-evaluation",!descriptions&&!evaluations);
    REQUIRE("reset-provider-again",geo_eval_reset(b));oracle_node_count=oracle_edge_count=0;
    GeoSourceProvider ps[]={
        {17,"hint.reset.first","test/2",NULL,describe,evaluate},
        {29,"hint.reset.second","test/2",NULL,describe,evaluate}};
    REQUIRE("reset-both-providers",geo_eval_register_many(b,ps,2));
    GeoSourceRef other={29,keys[0],sizeof keys[0]},shorter={17,keys[0],1};hint=1;
    if(hinted(b,other,0,&hint)||hinted(b,refs[0],0,&hint)||hinted(b,shorter,0,&hint))return 1;
    REQUIRE("reset-provider-and-size-separate",hint==3);
    geo_eval_destroy(a);geo_eval_destroy(b);REQUIRE("reset-no-leak",!live_allocations);return 0;
}
static int status_order(void)
{
    GeoEvalContext *ctx=context();REQUIRE("status-context",ctx);size_t hint=SIZE_MAX;
    GeoSourceRef bad={17,NULL,3},absent={999,NULL,0};
    REQUIRE("status-null-context",geo_eval_depend_hint(NULL,refs[0],0,&hint)==GEO_SOURCE_INVALID&&hint==SIZE_MAX);
    REQUIRE("status-invalid-key-before-hint",geo_eval_depend_hint(ctx,bad,0,&hint)==GEO_SOURCE_INVALID&&hint==SIZE_MAX&&!ctx->started);
    REQUIRE("status-missing-before-invalid-kind",geo_eval_depend_hint(ctx,absent,(GeoDependencyKind)99,&hint)==GEO_SOURCE_MISSING&&hint==SIZE_MAX&&!ctx->node_count);
    fail_nth=attempts+1;
    REQUIRE("status-memory-before-invalid-kind",geo_eval_depend_hint(ctx,refs[0],(GeoDependencyKind)99,&hint)==GEO_SOURCE_MEMORY&&hint==SIZE_MAX&&!ctx->node_count);fail_nth=0;
    REQUIRE("status-invalid-kind-still-inserts-node",geo_eval_depend_hint(ctx,refs[0],(GeoDependencyKind)99,&hint)==GEO_SOURCE_INVALID&&ctx->node_count==1&&hint==SIZE_MAX);
    oracle_node_count=oracle_edge_count=0;linear_node(refs[0]);
    if(hinted(ctx,refs[0],0,&hint))return 1;
    REQUIRE("status-invalid-kind-with-hit",geo_eval_depend_hint(ctx,refs[0],(GeoDependencyKind)-1,&hint)==GEO_SOURCE_INVALID&&hint==1&&!ctx->edge_count);
    GeoSourceNodeView view;REQUIRE("status-depend-leaves-new",geo_eval_node_at(ctx,0,&view)&&view.state==GEO_NODE_NEW&&!view.described&&!view.value);
    callback_mode=5;GeoSourceValue value;
    REQUIRE("status-provider-failure",geo_eval_source(ctx,refs[0],0,&value)==GEO_SOURCE_FAILED);
    unsigned calls=descriptions+evaluations;
    REQUIRE("status-depend-failed-node-is-identity",geo_eval_depend_hint(ctx,refs[0],0,&hint)==GEO_SOURCE_OK);
    REQUIRE("status-no-failure-reevaluation",descriptions+evaluations==calls);
    REQUIRE("status-seal",geo_eval_seal(ctx));size_t allocations=attempts;
    REQUIRE("depend-hint-sealed-guard",geo_eval_depend_hint(ctx,refs[0],0,&hint)==GEO_SOURCE_INVALID&&hint==1);
    REQUIRE("status-sealed-null-hint",geo_eval_depend_hint(ctx,refs[0],0,NULL)==geo_eval_depend(ctx,refs[0],0));
    REQUIRE("status-sealed-no-mutation",!graph_equal(ctx)&&attempts==allocations&&descriptions+evaluations==calls);
    geo_eval_destroy(ctx);REQUIRE("status-no-leak",!live_allocations);return 0;
}
static int null_hint(void)
{
    GeoEvalContext *a=context(),*b=context();REQUIRE("null-contexts",a&&b);
    GeoSourceRef absent={999,NULL,0},bad={17,NULL,9};
    GeoSourceRef list[]={refs[0],refs[1],refs[0],absent,bad,refs[2]};
    for(size_t i=0;i<sizeof list/sizeof *list;++i){GeoDependencyKind kind=i==5?(GeoDependencyKind)99:GEO_DEPENDENCY_DEFINITION_REQUIRED;
        GeoSourceStatus first=geo_eval_depend(a,list[i],kind),second=geo_eval_depend_hint(b,list[i],kind,NULL);
        REQUIRE("null-original-status",first==second);
        REQUIRE("null-original-counts",geo_eval_node_count(a)==geo_eval_node_count(b)&&geo_eval_edge_count(a)==geo_eval_edge_count(b));
    }
    for(size_t i=0;i<geo_eval_node_count(a);++i){GeoSourceNodeView x,y;
        REQUIRE("null-original-order-readable",geo_eval_node_at(a,i,&x)&&geo_eval_node_at(b,i,&y));
        REQUIRE("null-original-order",geo_source_ref_equal(x.source,y.source)&&x.state==y.state&&x.status==y.status&&x.described==y.described);
    }
    a->active=b->active=2;
    for(int k=0;k<3;++k){
        REQUIRE("null-original-edge-status",geo_eval_depend(a,refs[0],(GeoDependencyKind)k)==geo_eval_depend_hint(b,refs[0],(GeoDependencyKind)k,NULL));
        GeoSourceEdge x,y;REQUIRE("null-original-edge-read",geo_eval_edge_at(a,(size_t)k,&x)&&geo_eval_edge_at(b,(size_t)k,&y));
        REQUIRE("null-original-edge-order",x.consumer==y.consumer&&x.source==y.source&&x.kind==y.kind);
    }
    a->active=b->active=SIZE_MAX;geo_eval_destroy(a);geo_eval_destroy(b);
    REQUIRE("null-no-leak",!live_allocations);return 0;
}
static size_t shared_hint;
static int real_callback_failure;
static GeoSourceStatus self_source_status;
static bool hinted_evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)state;++evaluations;size_t consumer=linear_node(*ref);
    for(int kind=0;kind<3;++kind)for(int repeat=0;repeat<2;++repeat)
        if(hinted(ctx,refs[0],(GeoDependencyKind)kind,&shared_hint))real_callback_failure=1;
    if(geo_source_ref_equal(*ref,refs[4])){
        GeoSourceValue v;size_t child=linear_node(refs[5]);linear_edge(consumer,child,GEO_DEPENDENCY_VALUE_REQUIRED);
        if(geo_eval_source(ctx,refs[5],GEO_DEPENDENCY_VALUE_REQUIRED,&v)!=GEO_SOURCE_OK)real_callback_failure=1;
        /* Back at the older consumer after a nested scope. */
        for(int kind=2;kind>=0;--kind)
            if(hinted(ctx,refs[0],(GeoDependencyKind)kind,&shared_hint))real_callback_failure=1;
    }
    size_t self_hint=consumer+1;
    if(hinted(ctx,*ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&self_hint))real_callback_failure=1;
    GeoSourceValue v;linear_edge(consumer,consumer,GEO_DEPENDENCY_VALUE_REQUIRED);
    self_source_status=geo_eval_source(ctx,*ref,GEO_DEPENDENCY_VALUE_REQUIRED,&v);
    if(self_source_status!=GEO_SOURCE_CYCLE)real_callback_failure=1;
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}
static int edge_scopes(void)
{
    GeoEvalContext *ctx=geo_eval_create(31,19);REQUIRE("scope-context",ctx);
    GeoSourceProvider p={17,"hint.real-callback","test/1",NULL,describe,hinted_evaluate};
    REQUIRE("scope-register",geo_eval_register(ctx,&p));GeoSourceValue value;
    for(size_t i=4;i<=6;i+=2){linear_node(refs[i]);
        REQUIRE("scope-source-evaluates",geo_eval_source(ctx,refs[i],0,&value)==GEO_SOURCE_OK);
        REQUIRE("scope-real-callbacks",!real_callback_failure&&self_source_status==GEO_SOURCE_CYCLE);
        REQUIRE("scope-original-value",value.as.quantity.num==7&&value.as.quantity.den==1);
    }
    REQUIRE("scope-provider-count",descriptions==3&&evaluations==3);
    REQUIRE("scope-three-consumers-five-edges-plus-nested",oracle_edge_count==16);
    REQUIRE("scope-complete-ordered-graph",!graph_equal(ctx));
    geo_eval_destroy(ctx);REQUIRE("scope-no-leak",!live_allocations);return 0;
}
static int edge_wiring(void)
{
    GeoEvalContext *ctx=context();REQUIRE("edge-wiring-context",ctx);size_t hint=0;
    if(hinted(ctx,refs[0],0,&hint))return 1;
    if(hinted(ctx,refs[1],0,NULL))return 1;
    ctx->active=1;
    for(int kind=0;kind<3;++kind)if(hinted(ctx,refs[0],(GeoDependencyKind)kind,&hint))return 1;
    ctx->active=0;
    if(hinted(ctx,refs[0],0,&hint))return 1;
    ctx->active=1;
    for(int kind=2;kind>=0;--kind)if(hinted(ctx,refs[0],(GeoDependencyKind)kind,&hint))return 1;
    REQUIRE("edge-wiring-four-exact-edges",oracle_edge_count==4);
    ctx->active=SIZE_MAX;geo_eval_destroy(ctx);REQUIRE("edge-wiring-no-leak",!live_allocations);return 0;
}
static int hit_work(void)
{
    GeoEvalContext *ctx=context();REQUIRE("work-context",ctx);enum{N=512};size_t hints[N]={0};
    for(size_t i=0;i<N;++i)if(hinted(ctx,refs[i],0,&hints[i]))return 1;
    size_t allocations=attempts;node_hash_calls=node_find_calls=node_probe_steps=0;
    for(size_t repeat=0;repeat<4;++repeat)for(size_t i=0;i<N;++i){
        REQUIRE("work-valid-hint",geo_eval_depend_hint(ctx,refs[i],(GeoDependencyKind)(repeat%3),&hints[i])==GEO_SOURCE_OK);
        REQUIRE("work-keeps-ordinal",hints[i]==i+1);
    }
    REQUIRE("depend-hint-hit-avoids-hash-and-lookup",!node_hash_calls&&!node_find_calls&&!node_probe_steps);
    REQUIRE("work-no-allocation-or-evaluation",attempts==allocations&&!descriptions&&!evaluations);
    REQUIRE("work-original-ordered-graph",!graph_equal(ctx));
    geo_eval_destroy(ctx);REQUIRE("work-no-leak",!live_allocations);return 0;
}
static int allocation_failure(void)
{
    GeoEvalContext *ctx=context();REQUIRE("alloc-context",ctx);size_t hint=0;
    if(hinted(ctx,refs[0],0,&hint))return 1;
    size_t live=live_allocations;hint=SIZE_MAX;
    for(size_t offset=1;offset<=2;++offset){fail_nth=attempts+offset;
        REQUIRE("alloc-required-node-key-fail",geo_eval_depend_hint(ctx,refs[1],0,&hint)==GEO_SOURCE_MEMORY);
        REQUIRE("alloc-failure-retains-hint-and-graph",hint==SIZE_MAX&&ctx->node_count==1&&live_allocations==live&&!graph_equal(ctx));fail_nth=0;
    }
    if(hinted(ctx,refs[1],0,&hint))return 1;
    geo_eval_destroy(ctx);REQUIRE("alloc-first-no-leak",!live_allocations);
    oracle_node_count=oracle_edge_count=0;ctx=context();REQUIRE("alloc-array-context",ctx);exact_limit=sizeof *ctx->nodes;
    hint=0;if(hinted(ctx,refs[0],0,&hint))return 1;
    REQUIRE("alloc-exact-growth-precondition",ctx->node_capacity==1);fail_reallocs=1;hint=SIZE_MAX;live=live_allocations;
    REQUIRE("alloc-required-array-fail",geo_eval_depend_hint(ctx,refs[1],0,&hint)==GEO_SOURCE_MEMORY);
    REQUIRE("alloc-array-keeps-state",hint==SIZE_MAX&&ctx->node_count==1&&live_allocations==live&&!graph_equal(ctx));
    exact_limit=0;fail_reallocs=0;
    if(hinted(ctx,refs[1],0,&hint)||hinted(ctx,refs[2],0,NULL))return 1;
    REQUIRE("alloc-node-room-before-edge-fault",ctx->node_count==3&&ctx->node_capacity>=4);
    /* Test-owned active injection isolates the necessary edge-array failure.
     * No edge metadata/hint may be published merely because the node exists. */
    ctx->active=1;hint=0;fail_reallocs=1;
    REQUIRE("alloc-required-edge-fail",geo_eval_depend_hint(ctx,refs[0],0,&hint)==GEO_SOURCE_MEMORY);
    REQUIRE("alloc-edge-failure-retains-hint",hint==0&&!ctx->edge_count);
    fail_reallocs=0;exact_limit=sizeof *ctx->edges;
    if(hinted(ctx,refs[0],0,&hint))return 1;
    REQUIRE("alloc-one-edge-capacity",ctx->edge_capacity==1);fail_reallocs=1;
    size_t fresh_hint=SIZE_MAX;linear_node(refs[3]);
    REQUIRE("alloc-node-may-commit-before-edge-failure",geo_eval_depend_hint(ctx,refs[3],0,&fresh_hint)==GEO_SOURCE_MEMORY);
    REQUIRE("alloc-edge-failure-does-not-publish-new-hint",fresh_hint==SIZE_MAX&&ctx->node_count==4&&ctx->edge_count==1&&!graph_equal(ctx));
    REQUIRE("alloc-hit-new-kind-still-may-fail",geo_eval_depend_hint(ctx,refs[0],GEO_DEPENDENCY_DEFINITION_REQUIRED,&hint)==GEO_SOURCE_MEMORY);
    REQUIRE("alloc-hit-failure-keeps-graph",hint==1&&ctx->edge_count==1&&!graph_equal(ctx));
    fail_reallocs=0;exact_limit=0;
    if(hinted(ctx,refs[0],GEO_DEPENDENCY_DEFINITION_REQUIRED,&hint))return 1;
    ctx->active=SIZE_MAX;geo_eval_destroy(ctx);REQUIRE("alloc-no-leak",!live_allocations);return 0;
}
static int optional_fallback(void)
{
    GeoEvalContext *ctx=context();REQUIRE("fallback-context",ctx);fail_indexes=1;size_t hints[20]={0};
    for(size_t i=0;i<20;++i)if(hinted(ctx,refs[i],0,&hints[i]))return 1;
    REQUIRE("fallback-linear-precondition",index_failures&&!ctx->node_index);
    ctx->active=19;
    for(size_t i=0;i<10;++i)for(int k=0;k<3;++k)
        if(hinted(ctx,refs[i],(GeoDependencyKind)k,&hints[i]))return 1;
    REQUIRE("fallback-edge-index-optional",!ctx->edge_index);
    ctx->active=SIZE_MAX;fail_indexes=0;size_t hint=0;
    if(hinted(ctx,refs[20],0,&hint))return 1;
    REQUIRE("fallback-index-rebuilt",ctx->node_index&&ctx->node_index_capacity);
    for(size_t i=0;i<20;++i)if(hinted(ctx,refs[i],0,&hints[i]))return 1;
    REQUIRE("fallback-no-evaluation",!descriptions&&!evaluations);
    REQUIRE("fallback-reset",geo_eval_reset(ctx));
    REQUIRE("fallback-reset-releases-all",live_allocations==1&&!ctx->node_count&&!ctx->edge_count&&!ctx->node_index&&!ctx->edge_index);
    geo_eval_destroy(ctx);REQUIRE("fallback-no-leak",!live_allocations);return 0;
}

static bool context_value(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)ctx;(void)ref;++evaluations;
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=(GeoQuantity){*(const int *)state,1,GEO_UNIT_SCALAR};return true;
}
static int context_values(void)
{
    GeoEvalContext *a=geo_eval_create(1,1),*b=geo_eval_create(2,1);REQUIRE("values-contexts",a&&b);
    int av=7,bv=23;GeoSourceProvider p={17,"hint.value","test/1",&av,describe,context_value};
    REQUIRE("values-register-a",geo_eval_register(a,&p));p.candidate_state=&bv;
    REQUIRE("values-register-b",geo_eval_register(b,&p));GeoSourceValue value;size_t hint=0;
    REQUIRE("values-first-evaluation",geo_eval_source(a,refs[0],0,&value)==GEO_SOURCE_OK&&value.as.quantity.num==7);
    REQUIRE("values-first-hint",geo_eval_depend_hint(a,refs[0],0,&hint)==GEO_SOURCE_OK&&hint==1);
    REQUIRE("values-same-ordinal-other-context",geo_eval_depend_hint(b,refs[0],0,&hint)==GEO_SOURCE_OK&&hint==1);
    GeoSourceNodeView view;REQUIRE("values-other-context-still-new",geo_eval_node_at(b,0,&view)&&view.state==GEO_NODE_NEW&&!view.value&&!view.described);
    REQUIRE("values-second-own-evaluation",geo_eval_source(b,refs[0],0,&value)==GEO_SOURCE_OK&&value.as.quantity.num==23);
    REQUIRE("values-both-providers-executed",descriptions==2&&evaluations==2);
    geo_eval_destroy(a);geo_eval_destroy(b);REQUIRE("values-no-leak",!live_allocations);return 0;
}
static int full_collision(void)
{
    unsigned char collision[2][16];uint64_t first[2]={0,1},second[2],state[2];
    uint64_t seed=geo_source_hash_size(geo_source_hash_size(UINT64_C(14695981039346656037),17),16);
    for(size_t i=0;i<2;++i){state[i]=(seed^first[i])*UINT64_C(11400714785074694791);state[i]^=state[i]>>32;}
    second[0]=0;second[1]=state[0]^state[1];
    for(size_t i=0;i<2;++i){memcpy(collision[i],&first[i],8);memcpy(collision[i]+8,&second[i],8);}
    GeoSourceRef a={17,collision[0],16},b={17,collision[1],16};
    REQUIRE("collision-precondition",memcmp(a.key,b.key,16)&&geo_source_node_hash(a)==geo_source_node_hash(b));
    GeoEvalContext *ctx=context();REQUIRE("collision-context",ctx);size_t hint=0;
    if(hinted(ctx,a,0,&hint)||hinted(ctx,b,0,&hint)||hinted(ctx,a,0,&hint))return 1;
    REQUIRE("collision-keeps-two-identities",ctx->node_count==2&&hint==1);
    geo_eval_destroy(ctx);REQUIRE("collision-no-leak",!live_allocations);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    for(size_t i=0;i<MAX_REFS;++i){keys[i][0]=(unsigned char)i;keys[i][1]=(unsigned char)(i>>8);keys[i][11]=0xa5;refs[i]=(GeoSourceRef){17,keys[i],sizeof keys[i]};}
    int result;
    if(!strcmp(argv[1],"identity"))result=identity();
    else if(!strcmp(argv[1],"reset-context"))result=reset_context();
    else if(!strcmp(argv[1],"status-order"))result=status_order();
    else if(!strcmp(argv[1],"null-hint"))result=null_hint();
    else if(!strcmp(argv[1],"edge-scopes"))result=edge_scopes();
    else if(!strcmp(argv[1],"edge-wiring"))result=edge_wiring();
    else if(!strcmp(argv[1],"hit-work"))result=hit_work();
    else if(!strcmp(argv[1],"allocation-failure"))result=allocation_failure();
    else if(!strcmp(argv[1],"optional-fallback"))result=optional_fallback();
    else if(!strcmp(argv[1],"context-values"))result=context_values();
    else if(!strcmp(argv[1],"full-collision"))result=full_collision();
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
