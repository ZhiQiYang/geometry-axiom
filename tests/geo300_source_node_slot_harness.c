/* Reuse the complete existing source-index fixture without changing it. */
#include <stddef.h>
static size_t node_hash_calls,node_probe_steps;
#define main original_source_index_main
#include "geo261_source_index_harness.c"
#undef main

static int node_slot_work(void)
{
    GeoEvalContext *ctx=context();GeoSourceDescriptor d;REQUIRE("node-slot-context",ctx);
    for(size_t i=0;i<7;++i){
        size_t old_count=ctx->node_count,expected_probes=0;
        if(ctx->node_index_capacity){
            size_t slot=(size_t)geo_source_node_hash(refs[i])&(ctx->node_index_capacity-1);
            expected_probes=1;
            while(ctx->node_index[slot]){++expected_probes;slot=(slot+1)&(ctx->node_index_capacity-1);}
        }
        node_hash_calls=node_probe_steps=0;linear_node(refs[i]);
        REQUIRE("node-slot-describe",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
        REQUIRE("node-slot-new-ordinal",ctx->node_count==old_count+1);
        if(i){
            REQUIRE("node-slot-no-resize",ctx->node_index_capacity==16);
            REQUIRE("node-miss-one-hash",node_hash_calls==1);
            REQUIRE("node-miss-one-probe-sequence",node_probe_steps==expected_probes);
        }
    }
    REQUIRE("node-slot-ordered-insertions",!graph_equal(ctx));
    REQUIRE("node-slot-original-describe-count",descriptions==7&&!evaluations);
    /* Force the full index path; the optional small hint must not hide a
     * wrong inserted ordinal. This changes only test-owned private hints. */
    for(size_t i=7;i-->0;){
        memset(ctx->node_hint,0,sizeof ctx->node_hint);
        REQUIRE("node-slot-original-key-found",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
        REQUIRE("node-miss-committed-slot-points-to-new-ordinal",ctx->node_count==7);
        GeoSourceValue v;
        REQUIRE("node-slot-value",geo_eval_source(ctx,refs[i],GEO_DEPENDENCY_VALUE_REQUIRED,&v)==GEO_SOURCE_OK&&
            v.kind==GEO_SOURCE_QUANTITY&&v.as.quantity.num==7&&v.as.quantity.den==1&&v.as.quantity.unit==GEO_UNIT_SCALAR);
        GeoSourceNodeView view;REQUIRE("node-slot-node-view",geo_eval_node_at(ctx,i,&view));
        REQUIRE("node-slot-status",view.described&&view.state==GEO_NODE_VALID&&view.status==GEO_SOURCE_OK&&view.value);
    }
    REQUIRE("node-slot-no-extra-provider-calls",descriptions==7&&evaluations==7);
    REQUIRE("node-slot-ordered-final",!graph_equal(ctx));
    REQUIRE("node-slot-seal",geo_eval_seal(ctx));
    for(size_t i=0;i<7;++i)REQUIRE("node-slot-sealed-lookup",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-sealed-no-provider-calls",descriptions==7&&evaluations==7);
    geo_eval_destroy(ctx);REQUIRE("node-slot-no-leak",live_allocations==0);return 0;
}
static int node_slot_growth(void)
{
    GeoEvalContext *ctx=context();GeoSourceDescriptor d;REQUIRE("node-slot-growth-context",ctx);
    for(size_t i=0;i<8;++i){linear_node(refs[i]);REQUIRE("node-slot-growth-fill",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);}
    REQUIRE("node-slot-growth-precondition",ctx->node_index_capacity==16);
    node_hash_calls=0;linear_node(refs[8]);
    REQUIRE("node-slot-growth-insert",geo_eval_describe(ctx,refs[8],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-growth-rebuilds-full-index",ctx->node_index_capacity==32&&node_hash_calls==10);
    for(size_t i=9;i-->0;){memset(ctx->node_hint,0,sizeof ctx->node_hint);
        REQUIRE("node-slot-growth-old-lookup",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);
        REQUIRE("node-slot-growth-no-loss",ctx->node_count==9);}
    REQUIRE("node-slot-growth-order",!graph_equal(ctx));
    geo_eval_destroy(ctx);REQUIRE("node-slot-growth-no-leak",live_allocations==0);return 0;
}
static int node_slot_failure(void)
{
    GeoEvalContext *ctx=context();GeoSourceDescriptor d;REQUIRE("node-slot-failure-context",ctx);
    linear_node(refs[0]);REQUIRE("node-slot-failure-warm",geo_eval_describe(ctx,refs[0],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-failure-index-ready",ctx->node_index&&ctx->node_index_capacity==16);
    uint32_t saved[16];memcpy(saved,ctx->node_index,sizeof saved);size_t live=live_allocations;
    for(size_t offset=1;offset<=2;++offset){
        fail_nth=attempts+offset;
        REQUIRE("node-slot-required-allocation-fails",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_MEMORY);
        REQUIRE("node-slot-failed-append-keeps-index",ctx->node_count==1&&live_allocations==live&&!memcmp(saved,ctx->node_index,sizeof saved));
        REQUIRE("node-slot-failed-append-no-callback",descriptions==1&&!evaluations);
        fail_nth=0;
    }
    linear_node(refs[1]);node_hash_calls=0;
    REQUIRE("node-slot-retry",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-retry-one-hash",node_hash_calls==1);
    REQUIRE("node-slot-retry-order",!graph_equal(ctx));
    REQUIRE("node-slot-reset",geo_eval_reset(ctx));oracle_node_count=oracle_edge_count=0;
    GeoSourceProvider provider={17,"node.slot.rebuilt","test/1",NULL,describe,evaluate};
    REQUIRE("node-slot-reregister",geo_eval_register(ctx,&provider));fail_indexes=1;
    for(size_t i=0;i<3;++i){linear_node(refs[i]);REQUIRE("node-slot-optional-failure-success",geo_eval_describe(ctx,refs[i],&d)==GEO_SOURCE_OK);}
    REQUIRE("node-slot-optional-linear",!ctx->node_index&&!ctx->node_index_capacity);
    REQUIRE("node-slot-optional-order",!graph_equal(ctx));fail_indexes=0;
    linear_node(refs[3]);REQUIRE("node-slot-rebuild-after-optional-failure",geo_eval_describe(ctx,refs[3],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-optional-restored",ctx->node_index&&ctx->node_index_capacity==16);
    REQUIRE("node-slot-rebuilt-order",!graph_equal(ctx));
    geo_eval_destroy(ctx);REQUIRE("node-slot-failure-no-leak",live_allocations==0);return 0;
}
static int node_slot_packed(void)
{
    GeoEvalContext *ctx=context();GeoSourceDescriptor d;REQUIRE("node-slot-packed-context",ctx);
    packed_index_limit=1;linear_node(refs[0]);
    REQUIRE("node-slot-packed-last",geo_eval_describe(ctx,refs[0],&d)==GEO_SOURCE_OK&&ctx->node_index);
    linear_node(refs[1]);REQUIRE("node-slot-packed-append",geo_eval_describe(ctx,refs[1],&d)==GEO_SOURCE_OK);
    REQUIRE("node-slot-ordinal-guard-before-fast-slot",ctx->node_count==2&&!ctx->node_index&&!ctx->node_index_capacity);
    REQUIRE("node-slot-packed-order",!graph_equal(ctx));geo_eval_destroy(ctx);
    REQUIRE("node-slot-packed-no-leak",live_allocations==0);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"node-slot-work")||!strcmp(argv[1],"node-slot-growth")||
       !strcmp(argv[1],"node-slot-failure")||!strcmp(argv[1],"node-slot-packed")){
        if(prepare_refs())return 1;
        int result=!strcmp(argv[1],"node-slot-work")?node_slot_work():
            !strcmp(argv[1],"node-slot-growth")?node_slot_growth():
            !strcmp(argv[1],"node-slot-failure")?node_slot_failure():node_slot_packed();
        if(!result)printf("PASS %s\n",argv[1]);return result;
    }
    return original_source_index_main(argc,argv);
}
