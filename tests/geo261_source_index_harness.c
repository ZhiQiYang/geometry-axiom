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
static uint64_t edge_probe_hash_calls;
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
        REQUIRE("node-evaluates",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
        /* 逐筆對線性 oracle：多出節點是重複，少了節點是不同鍵被誤併。 */
        REQUIRE("merged-node",geo_eval_node_count(ctx)>=oracle_node_count);
        REQUIRE("duplicate-node",geo_eval_node_count(ctx)<=oracle_node_count);}
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
    GeoSourceDescriptor d,old;memset(&d,0x5a,sizeof d);memcpy(&old,&d,sizeof old);
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
/* 邊索引的確定性碰撞。邊的雜湊把 consumer、source、kind 依序混入，kind 最後混入，
 * 所以隨機的邊幾乎不會讓「只差 kind」的兩條邊落在同一個探測序列，只靠 edges 案例的
 * 規模抓不到「去重漏比 kind」。下面兩張表寫死在這裡，鍵本身與被測雜湊無關，
 * 但每個鍵在執行時都用被測的 geo_source_edge_hash 複驗（edge-collision-precondition）：
 * 雜湊一改，這個案例會當場失敗，而不是悄悄失去牙齒。
 * 找法（`client edge-search` 會用被測雜湊印出同一份表，另有獨立的 Python 版本交叉比對）：
 *   - 只用前 EDGE_NODES 個 refs 當節點，consumer 與 source 都是真實節點序號且不相等；
 *   - 依 consumer 由小到大、source 由小到大、kind 由 0 到 2 掃描；
 *   - edge_group：前 EDGE_GROUP 個 (hash & 4095)==4095 的三元組。低 12 位全是 1，
 *     所以邊索引從 16 槽起的每一次倍增，這些邊的起始槽都相同（空間內共有 194 個）；
 *   - edge_pairs：前 EDGE_PAIRS 組 consumer、source 相同、kind 不同、(hash & 4095) 相同
 *     且不等於 4095 的邊對（空間內共有 13 組）。 */
enum { EDGE_NODES=512, EDGE_GROUP=32, EDGE_PAIRS=8, EDGE_SLOT_MASK=4095 };
typedef struct { unsigned consumer, source; int kind; } EdgeKey;
typedef struct { unsigned consumer, source; int kind_a, kind_b; } EdgePair;
static const EdgeKey edge_group[EDGE_GROUP]={
    {1,316,2},{2,46,2},{5,497,1},{6,154,0},{6,233,0},{7,400,0},{8,256,1},{13,342,2},
    {13,431,2},{16,507,2},{20,99,2},{24,73,2},{26,397,0},{30,137,1},{30,196,0},{33,345,0},
    {34,165,2},{36,77,1},{38,236,1},{38,323,2},{40,192,1},{40,457,2},{41,399,1},{43,473,2},
    {49,216,2},{50,72,1},{50,252,0},{53,19,0},{53,467,0},{55,441,2},{56,339,1},{59,114,0}};
static const EdgePair edge_pairs[EDGE_PAIRS]={
    {66,374,1,2},{100,482,1,2},{180,159,1,2},{185,79,1,2},
    {211,466,0,1},{256,422,0,1},{282,40,1,2},{292,226,0,1}};
static GeoSourceEdge edge_of(unsigned consumer,unsigned source,int kind)
{return (GeoSourceEdge){consumer,source,(GeoDependencyKind)kind};}
static size_t edge_slot(unsigned consumer,unsigned source,int kind)
{return (size_t)geo_source_edge_hash(edge_of(consumer,source,kind))&EDGE_SLOT_MASK;}
/* consumer 取自真實節點序號；與 edges 案例的差別只在於不經 provider 回呼，直接指定 active。 */
static int add_edge(GeoEvalContext *ctx,unsigned consumer,unsigned source,int kind)
{
    linear_edge(consumer,source,(GeoDependencyKind)kind);
    ctx->active=consumer;
    GeoSourceStatus status=geo_eval_depend(ctx,refs[source],(GeoDependencyKind)kind);
    ctx->active=SIZE_MAX;
    REQUIRE("edge-depend",status==GEO_SOURCE_OK);
    /* 多一條是重複，少一條是不同的邊被誤判為已存在。 */
    REQUIRE("missing-edge",geo_eval_edge_count(ctx)>=oracle_edge_count);
    REQUIRE("duplicate-edge",geo_eval_edge_count(ctx)<=oracle_edge_count);
    return 0;
}
static int edge_collisions(void)
{
    for(size_t i=0;i<EDGE_GROUP;++i){const EdgeKey *k=&edge_group[i];
        REQUIRE("edge-collision-precondition",k->consumer<EDGE_NODES&&k->source<EDGE_NODES&&k->consumer!=k->source&&
            edge_slot(k->consumer,k->source,k->kind)==EDGE_SLOT_MASK);}
    for(size_t i=0;i<EDGE_PAIRS;++i){const EdgePair *p=&edge_pairs[i];
        REQUIRE("edge-collision-precondition",p->consumer<EDGE_NODES&&p->source<EDGE_NODES&&p->consumer!=p->source&&
            p->kind_a!=p->kind_b&&edge_slot(p->consumer,p->source,p->kind_a)==edge_slot(p->consumer,p->source,p->kind_b)&&
            edge_slot(p->consumer,p->source,p->kind_a)!=EDGE_SLOT_MASK);}
    GeoEvalContext *ctx=context();REQUIRE("context",ctx);GeoSourceDescriptor d;
    for(size_t i=0;i<EDGE_NODES;++i){linear_node(refs[i]);
        REQUIRE("edge-nodes",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);}
    REQUIRE("edge-nodes-created",geo_eval_node_count(ctx)==EDGE_NODES&&!geo_eval_edge_count(ctx));
    for(size_t i=0;i<EDGE_GROUP;++i)
        if(add_edge(ctx,edge_group[i].consumer,edge_group[i].source,edge_group[i].kind))return 1;
    for(size_t i=0;i<EDGE_PAIRS;++i){const EdgePair *p=&edge_pairs[i];
        if(add_edge(ctx,p->consumer,p->source,p->kind_a)||add_edge(ctx,p->consumer,p->source,p->kind_b))return 1;}
    REQUIRE("edge-collision-all-added",oracle_edge_count==EDGE_GROUP+2*EDGE_PAIRS&&geo_eval_edge_count(ctx)==oracle_edge_count);
    REQUIRE("edge-index-in-use",ctx->edge_index&&ctx->edge_index_capacity);
    /* 全部再加一遍：先倒序、再正序。已存在的邊不得重複，排序仍是首次插入序。 */
    for(size_t i=EDGE_PAIRS;i-->0;){const EdgePair *p=&edge_pairs[i];
        if(add_edge(ctx,p->consumer,p->source,p->kind_b)||add_edge(ctx,p->consumer,p->source,p->kind_a))return 1;}
    for(size_t i=EDGE_GROUP;i-->0;)
        if(add_edge(ctx,edge_group[i].consumer,edge_group[i].source,edge_group[i].kind))return 1;
    for(size_t i=0;i<EDGE_GROUP;++i)
        if(add_edge(ctx,edge_group[i].consumer,edge_group[i].source,edge_group[i].kind))return 1;
    for(size_t i=0;i<EDGE_PAIRS;++i){const EdgePair *p=&edge_pairs[i];
        if(add_edge(ctx,p->consumer,p->source,p->kind_a)||add_edge(ctx,p->consumer,p->source,p->kind_b))return 1;}
    REQUIRE("edge-collision-order",!graph_equal(ctx));
    geo_eval_destroy(ctx);
    REQUIRE("edge-collision-frees-all",live_allocations==0);return 0;
}
/* 重現上面兩張表：印出可直接貼回的 C 初始化列。 */
static int edge_search(void)
{
    size_t found=0;
    printf("edge_group:\n");
    for(unsigned c=0;c<EDGE_NODES&&found<EDGE_GROUP;++c)for(unsigned s=0;s<EDGE_NODES&&found<EDGE_GROUP;++s){
        if(c==s)continue;
        for(int k=0;k<3&&found<EDGE_GROUP;++k)if(edge_slot(c,s,k)==EDGE_SLOT_MASK){printf("{%u,%u,%d},\n",c,s,k);++found;}}
    printf("edge_pairs:\n");found=0;
    for(unsigned c=0;c<EDGE_NODES&&found<EDGE_PAIRS;++c)for(unsigned s=0;s<EDGE_NODES&&found<EDGE_PAIRS;++s){
        if(c==s)continue;
        for(int a=0;a<3&&found<EDGE_PAIRS;++a)for(int b=a+1;b<3&&found<EDGE_PAIRS;++b)
            if(edge_slot(c,s,a)==edge_slot(c,s,b)&&edge_slot(c,s,a)!=EDGE_SLOT_MASK){
                printf("{%u,%u,%d,%d}, /* slot %zu */\n",c,s,a,b,edge_slot(c,s,a));++found;}}
    return found==EDGE_PAIRS?0:1;
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
static int probe_seed_nodes(GeoEvalContext *ctx)
{
    GeoSourceDescriptor descriptor;
    for(size_t i=0;i<40;++i){linear_node(refs[i]);
        REQUIRE("edge-probe-seed",geo_eval_describe(ctx,refs[i],&descriptor)==GEO_SOURCE_OK);}
    return graph_equal(ctx);
}
static int probe_add_ordered(GeoEvalContext *ctx,size_t consumer,size_t source,GeoDependencyKind kind)
{
    linear_edge(consumer,source,kind);ctx->active=consumer;
    GeoSourceStatus status=geo_eval_depend(ctx,refs[source],kind);ctx->active=SIZE_MAX;
    REQUIRE("edge-probe-depend-status",status==GEO_SOURCE_OK);
    return graph_equal(ctx);
}
static int probe_resize_precondition(GeoEvalContext *ctx)
{
    REQUIRE("edge-probe-resize-boundary",ctx->edge_count==8&&ctx->edge_index_capacity==16);
    GeoSourceEdge edge={0,9,GEO_DEPENDENCY_VALUE_REQUIRED};size_t fresh[32]={0};
    size_t old_slot=(size_t)geo_source_edge_hash(edge)&15;
    while(ctx->edge_index[old_slot])old_slot=(old_slot+1)&15;
    for(size_t i=0;i<8;++i){size_t slot=(size_t)geo_source_edge_hash(ctx->edges[i])&31;
        while(fresh[slot])slot=(slot+1)&31;fresh[slot]=i+1;}
    size_t next_slot=(size_t)geo_source_edge_hash(edge)&31;
    while(fresh[next_slot])next_slot=(next_slot+1)&31;
    REQUIRE("edge-probe-old-empty-slot-is-wrong-after-resize",old_slot==9&&next_slot==25&&!fresh[old_slot]);
    return 0;
}
static int probe_edges(void)
{
    for(int faults=0;faults<2;++faults){
        oracle_node_count=oracle_edge_count=0;
        GeoEvalContext *ctx=context();REQUIRE("edge-probe-context",ctx);
        if(probe_seed_nodes(ctx))return 1;
        unsigned failures_before=index_failures;
        for(size_t i=1;i<=33;++i){
            if(!faults&&i==9&&probe_resize_precondition(ctx))return 1;
            int inject=faults&&(i==1||i==9||i==17);fail_indexes=inject;
            int result=probe_add_ordered(ctx,0,i,GEO_DEPENDENCY_VALUE_REQUIRED);fail_indexes=0;
            if(result)return result;
            if(inject)REQUIRE("edge-probe-index-failure-is-linear",!ctx->edge_index&&!ctx->edge_index_capacity);
            if(!faults&&(i==1||i==9||i==17||i==33)){
                size_t expected=i==1?16:i==9?32:i==17?64:128;
                REQUIRE("edge-probe-doubled-capacity",ctx->edge_index_capacity==expected);}
            /* Check the just-inserted edge before a later rebuild can repair its index. */
            if(i==9&&(probe_add_ordered(ctx,0,9,GEO_DEPENDENCY_VALUE_REQUIRED)||
                       probe_add_ordered(ctx,0,1,GEO_DEPENDENCY_VALUE_REQUIRED)))return 1;
        }
        REQUIRE("edge-probe-fallback-count",index_failures-failures_before==(unsigned)(faults?3:0));
        if(probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_VALUE_REQUIRED)||
           probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)||
           probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_EVALUATE_BEFORE)||
           probe_add_ordered(ctx,0,1,GEO_DEPENDENCY_DEFINITION_REQUIRED))return 1;
        /* Revisit final post-rehash insertions as well as the first 33 edges. */
        if(probe_add_ordered(ctx,0,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)||
           probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_EVALUATE_BEFORE)||
           probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)||
           probe_add_ordered(ctx,1,1,GEO_DEPENDENCY_VALUE_REQUIRED))return 1;
        for(size_t i=33;i>0;--i)if(probe_add_ordered(ctx,0,i,GEO_DEPENDENCY_VALUE_REQUIRED))return 1;
        REQUIRE("edge-probe-exact-37-ordered-edges",ctx->edge_count==37);
        geo_eval_destroy(ctx);REQUIRE("edge-probe-frees-all",live_allocations==0);
    }
    return 0;
}
static int probe_cost(void)
{
    oracle_node_count=oracle_edge_count=0;
    GeoEvalContext *ctx=context();REQUIRE("edge-probe-cost-context",ctx);
    if(probe_seed_nodes(ctx))return 1;
    edge_probe_hash_calls=0;
    for(size_t i=1;i<=12;++i)if(probe_add_ordered(ctx,0,i,GEO_DEPENDENCY_VALUE_REQUIRED))return 1;
    uint64_t observed=edge_probe_hash_calls;
    geo_eval_destroy(ctx);REQUIRE("edge-probe-cost-frees-all",live_allocations==0);
    printf("PROBE_HASH_CALLS=%llu\n",(unsigned long long)observed);
    REQUIRE("edge-probe-cost-instrumentation-live",observed>0);
    REQUIRE("edge-probe-reuses-lookup-hash",observed==21);
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;prepare_refs();int result;
    if(!strcmp(argv[1],"edge-probe"))result=probe_edges();
    else if(!strcmp(argv[1],"edge-probe-cost"))result=probe_cost();
    else if(!strcmp(argv[1],"nodes"))result=nodes_and_seal();
    else if(!strcmp(argv[1],"edges"))result=edges_and_reset();
    else if(!strcmp(argv[1],"edge-collisions"))result=edge_collisions();
    else if(!strcmp(argv[1],"edge-search"))return edge_search();
    else if(!strcmp(argv[1],"allocation"))result=failures();
    else if(!strcmp(argv[1],"growth"))result=growth_failures();
    else if(!strcmp(argv[1],"statuses"))result=statuses();
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
