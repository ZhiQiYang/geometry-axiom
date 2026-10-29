/* Actual K typed placement keys and original ordered identity/edge oracle. */
#include <stddef.h>
static size_t node_hash_calls,node_probe_steps,node_find_calls;
#define main original_source_index_main
#include "geo261_source_index_harness.c"
#undef main
#include "placement_sources.h"

enum { HINT_KEYS=8,HINT_ROUNDS=4,HINT_TOKEN=17,HINT_CONSUMER=29 };
static GeoPlacementSourceKey hint_keys[HINT_KEYS];
static GeoSourceRef hint_refs[HINT_KEYS];
static uint32_t hint_ids[HINT_KEYS];
static size_t hint_count;
static unsigned hint_descriptions,hint_evaluations;
static const unsigned char hint_root_key=7;
static GeoSourceRef hint_root_ref(void)
{return (GeoSourceRef){HINT_CONSUMER,&hint_root_key,1};}
static GeoFrame hint_frame(uint32_t id)
{return (GeoFrame){{(GeoCoord)id,-20,30},{1,0,0},{0,1,0},{0,0,1}};}
static bool hint_same_frame(GeoFrame a,GeoFrame b)
{return a.origin.x==b.origin.x&&a.origin.y==b.origin.y&&a.origin.z==b.origin.z&&
    geo_vector_equal(a.axis_u,b.axis_u)&&geo_vector_equal(a.axis_v,b.axis_v)&&geo_vector_equal(a.normal,b.normal);}
static bool hint_describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)state;++hint_descriptions;*out=(GeoSourceDescriptor){0};out->context.axis=-1;
    if(ref->provider==HINT_CONSUMER){
        if(ref->key_size!=1||!ref->key||*(const unsigned char *)ref->key!=hint_root_key)return false;
        out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_SCALAR;return true;
    }
    GeoPlacementSourceKind kind;uint32_t id;
    if(!geo_placement_source_decode(ref,&kind,&id)||kind!=GEO_PLACEMENT_SOURCE_FRAME)return false;
    out->kind=GEO_SOURCE_FRAME;out->unit=GEO_UNIT_LENGTH;out->context.has_placement=true;out->context.placement=id;return true;
}
static bool hint_evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)state;++hint_evaluations;
    if(ref->provider==HINT_CONSUMER){
        size_t consumer=linear_node(*ref);
        for(size_t i=0;i<hint_count;++i)for(int kind=0;kind<3;++kind){
            size_t source=linear_node(hint_refs[i]);linear_edge(consumer,source,(GeoDependencyKind)kind);
            if(geo_eval_depend(ctx,hint_refs[i],(GeoDependencyKind)kind)!=GEO_SOURCE_OK)return false;
        }
        *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
    }
    GeoPlacementSourceKind kind;uint32_t id;
    if(!geo_placement_source_decode(ref,&kind,&id)||kind!=GEO_PLACEMENT_SOURCE_FRAME)return false;
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_FRAME;out->as.frame=hint_frame(id);return true;
}
static GeoEvalContext *hint_context(const uint32_t *ids,size_t count)
{
    hint_count=count;hint_descriptions=hint_evaluations=0;oracle_node_count=oracle_edge_count=0;
    for(size_t i=0;i<count;++i){hint_ids[i]=ids[i];
        hint_refs[i]=geo_placement_source_ref(HINT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,ids[i],&hint_keys[i]);}
    GeoEvalContext *ctx=geo_eval_create(348,1);
    GeoSourceProvider p[2]={{HINT_TOKEN,"test.node-hint.typed-frame","test/1",NULL,hint_describe,hint_evaluate},
        {HINT_CONSUMER,"test.node-hint.consumer","test/1",NULL,hint_describe,hint_evaluate}};
    if(ctx&&!geo_eval_register_many(ctx,p,2)){geo_eval_destroy(ctx);return NULL;}return ctx;
}
static int hint_read(GeoEvalContext *ctx,size_t i)
{
    GeoSourceValue value;linear_node(hint_refs[i]);
    GeoSourceStatus status=geo_eval_source(ctx,hint_refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    REQUIRE("node-hint-typed-source-status",status==GEO_SOURCE_OK);
    REQUIRE("node-hint-collision-retains-full-identity",geo_eval_node_count(ctx)==oracle_node_count);
    REQUIRE("node-hint-typed-frame-value",value.kind==GEO_SOURCE_FRAME&&hint_same_frame(value.as.frame,hint_frame(hint_ids[i])));
    return 0;
}
static int hint_finish(GeoEvalContext *ctx)
{
    REQUIRE("node-hint-typed-provider-count",hint_descriptions==hint_count&&hint_evaluations==hint_count);
    REQUIRE("node-hint-typed-node-order",!graph_equal(ctx));
    GeoSourceValue value;GeoSourceRef root=hint_root_ref();linear_node(root);
    REQUIRE("node-hint-real-consumer",geo_eval_source(ctx,root,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==7);
    REQUIRE("node-hint-all-dependency-kinds-preserved",geo_eval_edge_count(ctx)==hint_count*3);
    REQUIRE("node-hint-full-ordered-graph",!graph_equal(ctx));
    REQUIRE("node-hint-no-extra-provider-calls",hint_descriptions==hint_count+1&&hint_evaluations==hint_count+1);
    REQUIRE("node-hint-seal",geo_eval_seal(ctx));
    for(size_t i=0;i<hint_count;++i)if(hint_read(ctx,i))return 1;
    REQUIRE("node-hint-sealed-no-new-callbacks",hint_descriptions==hint_count+1&&hint_evaluations==hint_count+1);
    REQUIRE("node-hint-sealed-depend-refused",geo_eval_depend(ctx,hint_refs[0],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_INVALID);
    REQUIRE("node-hint-sealed-reset-refused",!geo_eval_reset(ctx));
    geo_eval_destroy(ctx);REQUIRE("node-hint-no-leak",!live_allocations);return 0;
}
static size_t old_hint_slot(GeoSourceRef source)
{
    size_t slot=(size_t)source.provider^source.key_size;
    if(source.key_size){const unsigned char *key=source.key;slot^=(size_t)key[0]^key[source.key_size-1];}
    return slot&255;
}
static int typed_work(const char *mode)
{
    const uint32_t ids[HINT_KEYS]={256,512,768,1024,1280,1536,1792,2048};
    GeoEvalContext *ctx=hint_context(ids,HINT_KEYS);REQUIRE("node-hint-context",ctx);
    for(size_t i=0;i<HINT_KEYS;++i){
        GeoPlacementSourceKind kind;uint32_t id;
        REQUIRE("node-hint-real-placement-key",geo_placement_source_decode(&hint_refs[i],&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_FRAME&&id==ids[i]);
        REQUIRE("node-hint-fixed-same-end-byte-case",old_hint_slot(hint_refs[i])==old_hint_slot(hint_refs[0])&&
            hint_keys[i].bytes[0]==hint_keys[0].bytes[0]&&hint_keys[i].bytes[4]==hint_keys[0].bytes[4]);
        for(size_t j=0;j<i;++j)REQUIRE("node-hint-fixed-full-hash-slots-distinct",
            (geo_source_node_hash(hint_refs[i])&255)!=(geo_source_node_hash(hint_refs[j])&255));
        if(hint_read(ctx,i))return 1;
    }
    node_hash_calls=node_probe_steps=node_find_calls=0;
    for(size_t round=0;round<HINT_ROUNDS;++round)for(size_t i=0;i<HINT_KEYS;++i){
        if(!strcmp(mode,"typed-probe"))memset(ctx->node_hint,0,sizeof ctx->node_hint);
        if(hint_read(ctx,i))return 1;
    }
    size_t hashes=node_hash_calls,probes=node_probe_steps,finds=node_find_calls;
    if(hint_finish(ctx))return 1;
    if(!strcmp(mode,"typed-observe")){
        printf("{\"requests\":%u,\"hashes\":%zu,\"finds\":%zu,\"probes\":%zu}\n",(unsigned)(HINT_KEYS*HINT_ROUNDS),hashes,finds,probes);
    }else if(!strcmp(mode,"typed-probe")){
        REQUIRE("node-hint-miss-hash-reused-once",hashes==HINT_KEYS*HINT_ROUNDS);
        REQUIRE("node-hint-forced-miss-runs-real-finder",finds==HINT_KEYS*HINT_ROUNDS&&probes>=finds);
    }else{
        REQUIRE("node-hint-middle-bytes-avoid-full-lookup",finds==0&&probes==0);
        REQUIRE("node-hint-hit-computes-one-hash",hashes==HINT_KEYS*HINT_ROUNDS);
    }
    return 0;
}
static int typed_collision(void)
{
    const uint32_t ids[2]={223,256};GeoEvalContext *ctx=hint_context(ids,2);REQUIRE("node-hint-collision-context",ctx);
    REQUIRE("node-hint-real-collision",(geo_source_node_hash(hint_refs[0])&255)==(geo_source_node_hash(hint_refs[1])&255));
    for(size_t n=0;n<8;++n)for(size_t i=0;i<2;++i)if(hint_read(ctx,i))return 1;
    GeoSourceValue value,saved;memset(&value,0x5a,sizeof value);memcpy(&saved,&value,sizeof saved);
    size_t nodes=geo_eval_node_count(ctx);unsigned calls=hint_descriptions+hint_evaluations;
    node_hash_calls=0;GeoSourceRef invalid={HINT_TOKEN,NULL,5};
    REQUIRE("node-hint-invalid-before-hash",geo_eval_source(ctx,invalid,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&
        !node_hash_calls&&nodes==geo_eval_node_count(ctx)&&calls==hint_descriptions+hint_evaluations&&!memcmp(&value,&saved,sizeof value));
    return hint_finish(ctx);
}
static int typed_fallback(void)
{
    const uint32_t ids[2]={256,512};GeoEvalContext *ctx=hint_context(ids,2);REQUIRE("node-hint-fallback-context",ctx);
    fail_indexes=1;index_failures=0;
    for(size_t n=0;n<4;++n)for(size_t i=0;i<2;++i){memset(ctx->node_hint,0,sizeof ctx->node_hint);if(hint_read(ctx,i))return 1;}
    REQUIRE("node-hint-optional-index-real-linear",index_failures&&!ctx->node_index&&!ctx->node_index_capacity);
    fail_indexes=0;
    REQUIRE("node-hint-reset",geo_eval_reset(ctx));
    REQUIRE("node-hint-reset-erases-hints",!ctx->node_count&&!ctx->provider_count&&live_allocations==1);
    for(size_t i=0;i<256;++i)REQUIRE("node-hint-reset-clears-every-slot",!ctx->node_hint[i]);
    geo_eval_destroy(ctx);REQUIRE("node-hint-fallback-no-leak",!live_allocations);
    ctx=hint_context(ids,2);REQUIRE("node-hint-new-context",ctx);
    for(size_t i=0;i<2;++i)if(hint_read(ctx,i))return 1;
    return hint_finish(ctx);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;int result;
    if(!strcmp(argv[1],"typed-hint")||!strcmp(argv[1],"typed-probe")||!strcmp(argv[1],"typed-observe"))result=typed_work(argv[1]);
    else if(!strcmp(argv[1],"typed-collision"))result=typed_collision();
    else if(!strcmp(argv[1],"typed-fallback"))result=typed_fallback();
    else return original_source_index_main(argc,argv);
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
