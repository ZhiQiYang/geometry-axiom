/* 真實 K 實作；配置代理沿用既有 harness 的測試端注入方式。
 * 私有欄位只用於強制碰撞、配置失敗與釋放檢查，行為以公開 API 斷言。 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static size_t live_allocations,fail_nth,attempts,exact_limit;
static unsigned index_failures,realloc_failures;
static int fail_indexes,fail_reallocs;
static int allocation_fails(void){return ++attempts==fail_nth;}
static void *test_malloc(size_t n)
{if(allocation_fails())return NULL;void *p=malloc(n);if(p)++live_allocations;return p;}
static void *test_calloc(size_t n,size_t s)
{
    if(allocation_fails())return NULL;
    if(fail_indexes&&n>=16&&s==sizeof(size_t)){++index_failures;return NULL;}
    void *p=calloc(n,s);if(p)++live_allocations;return p;
}
static void *test_realloc(void *p,size_t n)
{
    if(allocation_fails())return NULL;
    if(fail_reallocs||(exact_limit&&n>exact_limit)){++realloc_failures;return NULL;}
    int fresh=p==NULL;void *q=realloc(p,n);if(q&&fresh)++live_allocations;return q;
}
static void test_free(void *p){if(p)--live_allocations;free(p);}
#define malloc test_malloc
#define calloc test_calloc
#define realloc test_realloc
#define free test_free
#include "source.c"
#undef malloc
#undef calloc
#undef realloc
#undef free

#define REQUIRE(label,expression) do {if(!(expression)){ \
    fprintf(stderr,"ASSERT:%s line=%d expr=%s\n",label,__LINE__,#expression);return 1;}} while(0)
enum { MANY=1536, COLLISIONS=32, MAX_REFS=MANY+16, MAX_EDGES=8192 };
static unsigned char keys[MAX_REFS][12];
static GeoSourceRef refs[MAX_REFS],oracle_nodes[MAX_REFS];
static GeoSourceEdge oracle_edges[MAX_EDGES];
static size_t oracle_node_count,oracle_edge_count;
static unsigned descriptions,evaluations;
static int callback_mode,callback_failure;
static GeoSourceStatus nested_status;

/* 舊實作的逐筆線性去重規則，與被測索引及雜湊函式無關。 */
static size_t linear_node(GeoSourceRef ref)
{
    for(size_t i=0;i<oracle_node_count;++i){GeoSourceRef old=oracle_nodes[i];
        if(old.provider==ref.provider&&old.key_size==ref.key_size&&
           (!ref.key_size||!memcmp(old.key,ref.key,ref.key_size)))return i;}
    oracle_nodes[oracle_node_count]=ref;return oracle_node_count++;
}
static void linear_edge(size_t consumer,size_t source,GeoDependencyKind kind)
{
    for(size_t i=0;i<oracle_edge_count;++i){GeoSourceEdge e=oracle_edges[i];
        if(e.consumer==consumer&&e.source==source&&e.kind==kind)return;}
    oracle_edges[oracle_edge_count++]=(GeoSourceEdge){consumer,source,kind};
}
static bool describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)state;(void)ref;++descriptions;
    *out=(GeoSourceDescriptor){0};out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_SCALAR;
    if(callback_mode==2)return false;
    if(callback_mode==3)out->context.axis=9;
    return true;
}
static bool evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)state;++evaluations;
    if(callback_mode==1){
        size_t consumer=linear_node(*ref);
        for(size_t i=0;i<96;++i){size_t source=linear_node(refs[i]);
            for(int kind=0;kind<3;++kind){
                linear_edge(consumer,source,(GeoDependencyKind)kind);
                for(int repeat=0;repeat<3;++repeat)
                    if(geo_eval_depend(ctx,refs[i],(GeoDependencyKind)kind)!=GEO_SOURCE_OK)callback_failure=1;
            }
        }
    }else if(callback_mode==4){
        GeoSourceValue value;nested_status=geo_eval_source(ctx,*ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    }else if(callback_mode==5)return false;
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}
static GeoEvalContext *context(void)
{
    GeoEvalContext *ctx=geo_eval_create(31,19);
    GeoSourceProvider providers[]={
        {17,"index.first","test/1",NULL,describe,evaluate},
        {29,"index.second","test/1",NULL,describe,evaluate}};
    if(ctx&&!geo_eval_register_many(ctx,providers,2)){geo_eval_destroy(ctx);return NULL;}
    return ctx;
}
static int graph_equal(GeoEvalContext *ctx)
{
    REQUIRE("duplicate-node",geo_eval_node_count(ctx)==oracle_node_count);
    REQUIRE("duplicate-edge",geo_eval_edge_count(ctx)==oracle_edge_count);
    for(size_t i=0;i<oracle_node_count;++i){GeoSourceNodeView view;GeoSourceRef old=oracle_nodes[i];
        REQUIRE("node-order-readable",geo_eval_node_at(ctx,i,&view));
        REQUIRE("node-order-exact",view.source.provider==old.provider&&view.source.key_size==old.key_size&&
            (!old.key_size||!memcmp(view.source.key,old.key,old.key_size)));
        REQUIRE("zero-size-key-normalized",old.key_size||view.source.key==NULL);
    }
    for(size_t i=0;i<oracle_edge_count;++i){GeoSourceEdge edge,old=oracle_edges[i];
        REQUIRE("edge-order-readable",geo_eval_edge_at(ctx,i,&edge));
        REQUIRE("edge-order-exact",edge.consumer==old.consumer&&edge.source==old.source&&edge.kind==old.kind);
    }
    return 0;
}
static int prepare_refs(void)
{
    /* 前 32 個 key 在最終的 4096 槽表落在同一槽，跨多次擴表。 */
    size_t found=0;
    for(uint32_t value=0;found<COLLISIONS;++value){
        unsigned char key[12]={0};memcpy(key,&value,sizeof value);
        GeoSourceRef ref={17,key,sizeof key};
        if((geo_source_node_hash(ref)&4095)==4095){
            memcpy(keys[found],key,sizeof key);refs[found]=(GeoSourceRef){17,keys[found],sizeof key};++found;
        }
    }
    for(size_t i=COLLISIONS;i<MANY;++i){
        memcpy(keys[i],&i,sizeof i);keys[i][11]=0xa5;
        refs[i]=(GeoSourceRef){17,keys[i],sizeof keys[i]};
    }
    refs[MANY]=(GeoSourceRef){29,keys[0],sizeof keys[0]};
    refs[MANY+1]=(GeoSourceRef){17,keys[0],1};
    refs[MANY+2]=(GeoSourceRef){17,keys[0],sizeof keys[0]-1};
    refs[MANY+3]=(GeoSourceRef){17,NULL,0};
    refs[MANY+4]=(GeoSourceRef){17,keys[1],0};
    refs[MANY+5]=(GeoSourceRef){29,keys[1],0};
    return 0;
}
static int nodes_and_seal(void)
{
    GeoEvalContext *ctx=context();REQUIRE("context",ctx);
    GeoSourceValue value;
    for(size_t i=0;i<MANY+6;++i){linear_node(refs[i]);
        REQUIRE("node-evaluates",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);}
    for(size_t i=MANY+6;i-->0;){
        REQUIRE("node-duplicate-lookup",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        REQUIRE("duplicate-node",geo_eval_node_count(ctx)==oracle_node_count);
    }
    REQUIRE("linear-node-order",!graph_equal(ctx));
    REQUIRE("memoized-callback-count",evaluations==oracle_node_count&&descriptions==oracle_node_count);
    /* 另建一個未描述節點，sealed 不得補描述。 */
    refs[MANY+6]=(GeoSourceRef){29,keys[100],7};linear_node(refs[MANY+6]);
    REQUIRE("undescribed-node",geo_eval_depend(ctx,refs[MANY+6],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK);
    REQUIRE("seal",geo_eval_seal(ctx));
    unsigned calls=evaluations+descriptions;
    for(size_t i=0;i<MANY+6;++i){GeoSourceDescriptor d;
        REQUIRE("sealed-node",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_EVALUATE_BEFORE,&value)==GEO_SOURCE_OK);
        REQUIRE("sealed-describe",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);}
    GeoSourceDescriptor d;memset(&d,0x5a,sizeof d);GeoSourceDescriptor old=d;
    REQUIRE("sealed-unknown-description",geo_eval_describe(ctx,refs[MANY+6],&d)==GEO_SOURCE_INVALID&&!memcmp(&old,&d,sizeof d));
    REQUIRE("sealed-unevaluated",geo_eval_source(ctx,refs[MANY+6],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    GeoSourceRef unknown={999,NULL,0};
    REQUIRE("sealed-unknown",geo_eval_source(ctx,unknown,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    REQUIRE("sealed-reset-refused",!geo_eval_reset(ctx));
    REQUIRE("sealed-no-callbacks",evaluations+descriptions==calls);
    REQUIRE("sealed-order-unchanged",!graph_equal(ctx));geo_eval_destroy(ctx);
    REQUIRE("destroy-frees-all",live_allocations==0);return 0;
}
static int edges_and_reset(void)
{
    GeoEvalContext *ctx=context();REQUIRE("context",ctx);callback_mode=1;
    for(size_t i=100;i<104;++i){GeoSourceValue value;linear_node(refs[i]);
        REQUIRE("consumer-evaluates",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        REQUIRE("callback-dependencies",!callback_failure);
        REQUIRE("duplicate-edge",geo_eval_edge_count(ctx)==oracle_edge_count);}
    REQUIRE("all-three-edge-fields",oracle_edge_count==4*96*3);
    REQUIRE("linear-graph-order",!graph_equal(ctx));
    REQUIRE("reset",geo_eval_reset(ctx));
    REQUIRE("reset-counts",!geo_eval_node_count(ctx)&&!geo_eval_edge_count(ctx)&&!geo_eval_provider_count(ctx));
    REQUIRE("reset-frees-indexes",!ctx->node_index&&!ctx->edge_index&&!ctx->node_index_capacity&&!ctx->edge_index_capacity&&
        !ctx->node_capacity&&!ctx->edge_capacity&&live_allocations==1);
    GeoSourceProvider p={17,"rebuilt","test/2",NULL,describe,evaluate};
    REQUIRE("reregister",geo_eval_register(ctx,&p));oracle_node_count=oracle_edge_count=0;
    for(size_t i=103;i>=100;--i){GeoSourceValue value;linear_node(refs[i]);
        REQUIRE("rebuild",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);}
    REQUIRE("rebuilt-order",!graph_equal(ctx));geo_eval_destroy(ctx);
    REQUIRE("reset-destroy-frees-all",live_allocations==0);return 0;
}
static int failures(void)
{
    /* 每個必要配置點逐一失敗，恢復後須無重複且原節點維持原狀。 */
    for(size_t nth=1;nth<=5;++nth){
        GeoEvalContext *ctx=context();REQUIRE("context",ctx);GeoSourceDescriptor d;
        REQUIRE("existing-node",geo_eval_describe(ctx,refs[0],&d)==GEO_SOURCE_OK);
        size_t live=live_allocations;GeoSourceNodeView before,after;geo_eval_node_at(ctx,0,&before);
        attempts=0;fail_nth=nth;
        GeoSourceStatus status=geo_eval_describe(ctx,refs[1],&d);fail_nth=0;
        REQUIRE("necessary-allocation-memory",status==(nth<=2?GEO_SOURCE_MEMORY:GEO_SOURCE_OK));
        if(status==GEO_SOURCE_MEMORY)REQUIRE("failure-no-leak-or-node",live_allocations==live&&geo_eval_node_count(ctx)==1);
        REQUIRE("allocation-failure-keeps-node",geo_eval_node_at(ctx,0,&after)&&after.source.key==before.source.key&&
            after.state==before.state&&after.status==before.status&&after.described==before.described);
        REQUIRE("retry-node",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_OK&&geo_eval_node_count(ctx)==2);
        geo_eval_destroy(ctx);REQUIRE("failure-destroy-frees-all",live_allocations==0);
    }
    /* 從第一個索引配置即失敗，以及已有索引的擴表失敗；兩者都退回線性。 */
    for(int existing=0;existing<2;++existing){
        GeoEvalContext *ctx=context();REQUIRE("context",ctx);GeoSourceDescriptor d;
        oracle_node_count=oracle_edge_count=0;
        if(existing){
            linear_node(refs[0]);linear_edge(0,0,GEO_DEPENDENCY_VALUE_REQUIRED);
            REQUIRE("initial-index",geo_eval_describe(ctx,refs[0],&d)==GEO_SOURCE_OK&&ctx->node_index);
            ctx->active=0;
            REQUIRE("initial-edge-index",geo_eval_depend(ctx,refs[0],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK&&ctx->edge_index);
            ctx->active=SIZE_MAX;
        }
        fail_indexes=1;
        for(size_t i=0;i<100;++i){linear_node(refs[i]);REQUIRE("index-fallback-node",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);}
        callback_mode=1;
        for(size_t i=100;i<104;++i){GeoSourceValue v;linear_node(refs[i]);
            REQUIRE("index-fallback-edge",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&v)==GEO_SOURCE_OK);}
        REQUIRE("index-allocation-was-rejected",index_failures>0&&!ctx->node_index&&!ctx->edge_index);
        REQUIRE("fallback-order",!graph_equal(ctx));
        for(size_t i=0;i<100;++i)REQUIRE("fallback-duplicate-node",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
        REQUIRE("fallback-no-duplicates",!graph_equal(ctx));
        fail_indexes=0;callback_mode=0;
        if(existing){
            linear_node(refs[104]);REQUIRE("index-rebuild",geo_eval_describe(ctx,refs[104],&d)==GEO_SOURCE_OK&&ctx->node_index);
            REQUIRE("recovered-order",!graph_equal(ctx));
        }
        REQUIRE("fallback-seal",geo_eval_seal(ctx));
        for(size_t i=0;i<100;++i)REQUIRE("fallback-sealed-describe",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
        GeoSourceValue value;
        REQUIRE("fallback-sealed-source",geo_eval_source(ctx,refs[100],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        geo_eval_destroy(ctx);REQUIRE("fallback-frees-all",live_allocations==0);
    }
    return 0;
}
static int growth_failures(void)
{
    GeoEvalContext *ctx=context();REQUIRE("context",ctx);GeoSourceDescriptor d;
    exact_limit=sizeof *ctx->nodes;
    REQUIRE("node-exact-size-retry",geo_eval_describe(ctx,refs[0],&d)==GEO_SOURCE_OK&&ctx->node_capacity==1&&realloc_failures);
    exact_limit=0;fail_reallocs=1;size_t live=live_allocations;
    REQUIRE("node-growth-memory",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_MEMORY);
    REQUIRE("node-growth-no-change",ctx->node_count==1&&ctx->node_capacity==1&&live_allocations==live);
    fail_reallocs=0;
    REQUIRE("node-growth-retry",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_OK);
    /* 在 active consumer 中觀察 edge MEMORY；既有 node 不需新配置。 */
    ctx->active=0;exact_limit=sizeof *ctx->edges;
    REQUIRE("edge-exact-size-retry",geo_eval_depend(ctx,refs[1],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK&&ctx->edge_capacity==1);
    exact_limit=0;fail_reallocs=1;live=live_allocations;
    REQUIRE("edge-growth-memory",geo_eval_depend(ctx,refs[1],GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_MEMORY);
    REQUIRE("edge-growth-no-change",ctx->edge_count==1&&ctx->edge_capacity==1&&live_allocations==live);
    REQUIRE("edge-duplicate-no-allocation",geo_eval_depend(ctx,refs[1],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK&&ctx->edge_count==1);
    fail_reallocs=0;
    REQUIRE("edge-growth-retry",geo_eval_depend(ctx,refs[1],GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK&&ctx->edge_count==2);
    ctx->active=SIZE_MAX;geo_eval_destroy(ctx);REQUIRE("growth-frees-all",live_allocations==0);return 0;
}
static int statuses(void)
{
    GeoEvalContext *ctx=context();REQUIRE("context",ctx);GeoSourceValue value,old;
    memset(&value,0x5a,sizeof value);memcpy(&old,&value,sizeof old);
    GeoSourceRef absent={999,NULL,0},bad={17,NULL,3};
    REQUIRE("missing-provider",geo_eval_source(ctx,absent,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_MISSING);
    REQUIRE("invalid-key",geo_eval_source(ctx,bad,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    REQUIRE("invalid-kind-still-adds-node",geo_eval_source(ctx,refs[0],(GeoDependencyKind)99,&value)==GEO_SOURCE_INVALID&&ctx->node_count==1);
    for(int mode=2;mode<=5;++mode){callback_mode=mode;
        GeoSourceStatus expected=mode==2?GEO_SOURCE_MISSING:mode==3?GEO_SOURCE_INVALID:mode==4?GEO_SOURCE_OK:GEO_SOURCE_FAILED;
        REQUIRE("provider-status",geo_eval_source(ctx,refs[mode],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==expected);
        if(mode<4)REQUIRE("failure-keeps-output",!memcmp(&old,&value,sizeof old));}
    REQUIRE("cycle-preserved",nested_status==GEO_SOURCE_CYCLE);
    REQUIRE("failed-status-memoized",geo_eval_source(ctx,refs[5],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED);
    geo_eval_destroy(ctx);REQUIRE("status-frees-all",live_allocations==0);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;prepare_refs();int result;
    if(!strcmp(argv[1],"nodes"))result=nodes_and_seal();
    else if(!strcmp(argv[1],"edges"))result=edges_and_reset();
    else if(!strcmp(argv[1],"allocation"))result=failures();
    else if(!strcmp(argv[1],"growth"))result=growth_failures();
    else if(!strcmp(argv[1],"statuses"))result=statuses();
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
