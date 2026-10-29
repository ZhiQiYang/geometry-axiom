/* Supplement the unchanged full linear node/edge oracle and allocation hooks. */
#include <stddef.h>
static int scope_undo_fail;
static unsigned scope_undo_failures;
#define main original_source_index_main
#include "geo261_source_index_harness.c"
#undef main

enum { S_FANOUT=1,S_NESTED,S_RETRY,S_REQUIRED,S_CONTROL,S_HEAP_REALLOC,S_INVALID_CHILD,S_DEEP_512 };
static int scope_mode,scope_manual_ancestor,scope_callback_error;
static size_t scope_fanout,scope_kinds;
static unsigned scope_root_evaluations,scope_descriptions,scope_evaluations;
static GeoSourceStatus scope_required_status,scope_cycle_status;
static GeoEvalContext *scope_callback_context;
static bool scope_heap_eight,scope_heap_prefix_preserved,scope_invalid_output_unchanged;
static GeoSourceStatus scope_invalid_child_status;
static unsigned scope_deep_depth,scope_deep_max,scope_deep_unwinds;
static int scope_deep_restored;
/* The requested 512-world scale is a test depth, not a product limit. */
enum { SCOPE_TEST_DEPTH=512,SCOPE_DEEP_FIRST=100 };

static int scope_is_ref(const GeoSourceRef *ref,size_t i)
{return ref->provider==refs[i].provider&&ref->key_size==refs[i].key_size&&
    (!ref->key_size||!memcmp(ref->key,refs[i].key,ref->key_size));}
static GeoSourceStatus scope_depend(GeoEvalContext *ctx,size_t consumer,size_t source,int kind)
{
    size_t ci=linear_node(refs[consumer]),si=linear_node(refs[source]);
    GeoSourceStatus status=geo_eval_depend(ctx,refs[source],(GeoDependencyKind)kind);
    if(status==GEO_SOURCE_OK)linear_edge(ci,si,(GeoDependencyKind)kind);
    return status;
}
static bool scope_describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)state;++scope_descriptions;
    *out=(GeoSourceDescriptor){0};out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_SCALAR;
    out->retry_failure=scope_mode==S_RETRY;
    /* describe runs while the parent is still active, before child evaluate. */
    if(scope_mode==S_CONTROL&&scope_is_ref(ref,101)&&
       scope_depend(scope_callback_context,100,2,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
    return true;
}
static bool scope_heap_realloc_evaluate(GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(scope_is_ref(ref,100)){
        if(scope_depend(ctx,100,0,0)!=GEO_SOURCE_OK||scope_depend(ctx,100,1,1)!=GEO_SOURCE_OK)return false;
        size_t parent=linear_node(refs[100]),child=linear_node(refs[101]);GeoSourceValue value;
        linear_edge(parent,child,GEO_DEPENDENCY_VALUE_REQUIRED);
        if(geo_eval_source(ctx,refs[101],GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
        if(scope_depend(ctx,100,0,0)!=GEO_SOURCE_OK||scope_depend(ctx,100,1,1)!=GEO_SOURCE_OK||
           scope_depend(ctx,100,0,2)!=GEO_SOURCE_OK)return false;
    }else{
        for(size_t i=0;i<12;++i)for(int kind=0;kind<3;++kind)for(int repeat=0;repeat<2;++repeat){
            bool fail_here=i==8&&kind==0&&repeat==0;
            GeoSourceEdgeScope *scope=ctx->edge_scope;GeoSourceEdgeUndo *saved=scope->undo;
            if(fail_here){
                scope_heap_eight=scope->count==8&&scope->capacity==8&&scope->undo!=scope->inline_undo;
                scope_undo_fail=1;
            }
            GeoSourceStatus status=scope_depend(ctx,101,i,kind);
            if(fail_here){
                scope_undo_fail=0;
                scope_heap_prefix_preserved=scope->undo==saved&&scope->count==8&&scope->capacity==8&&!scope->complete;
            }
            if(status!=GEO_SOURCE_OK)return false;
        }
    }
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}
static bool scope_invalid_child_evaluate(GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(scope_is_ref(ref,100)){
        if(scope_depend(ctx,100,0,0)!=GEO_SOURCE_OK)return false;
        size_t parent=linear_node(refs[100]),child=linear_node(refs[101]);GeoSourceValue value,saved;
        memset(&value,0x5a,sizeof value);memcpy(&saved,&value,sizeof saved);
        linear_edge(parent,child,GEO_DEPENDENCY_VALUE_REQUIRED);
        scope_invalid_child_status=geo_eval_source(ctx,refs[101],GEO_DEPENDENCY_VALUE_REQUIRED,&value);
        scope_invalid_output_unchanged=!memcmp(&value,&saved,sizeof value);
        if(scope_invalid_child_status!=GEO_SOURCE_INVALID||!scope_invalid_output_unchanged)return false;
        if(scope_depend(ctx,100,0,0)!=GEO_SOURCE_OK||scope_depend(ctx,100,0,1)!=GEO_SOURCE_OK)return false;
    }else{
        if(scope_depend(ctx,101,0,0)!=GEO_SOURCE_OK||scope_depend(ctx,101,1,2)!=GEO_SOURCE_OK)return false;
        *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;
        out->as.quantity=(GeoQuantity){7,0,GEO_UNIT_SCALAR};return true;
    }
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}
static bool scope_deep_evaluate(GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    size_t owner=SCOPE_DEEP_FIRST;
    while(owner<SCOPE_DEEP_FIRST+SCOPE_TEST_DEPTH&&!scope_is_ref(ref,owner))++owner;
    if(owner==SCOPE_DEEP_FIRST+SCOPE_TEST_DEPTH)return false;
    ++scope_deep_depth;if(scope_deep_depth>scope_deep_max)scope_deep_max=scope_deep_depth;
    if(scope_depend(ctx,owner,0,0)!=GEO_SOURCE_OK){--scope_deep_depth;return false;}
    if(owner+1<SCOPE_DEEP_FIRST+SCOPE_TEST_DEPTH){
        size_t parent=linear_node(refs[owner]),child=linear_node(refs[owner+1]);GeoSourceValue value;
        linear_edge(parent,child,GEO_DEPENDENCY_VALUE_REQUIRED);
        if(geo_eval_source(ctx,refs[owner+1],GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK){--scope_deep_depth;return false;}
    }
    size_t before=geo_eval_edge_count(ctx);
    if(scope_depend(ctx,owner,0,0)!=GEO_SOURCE_OK){--scope_deep_depth;return false;}
    if(geo_eval_edge_count(ctx)!=before)scope_deep_restored=0;
    if(scope_depend(ctx,owner,0,1)!=GEO_SOURCE_OK){--scope_deep_depth;return false;}
    ++scope_deep_unwinds;--scope_deep_depth;
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}

static bool scope_evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)state;++scope_evaluations;
    if(scope_mode==S_HEAP_REALLOC)return scope_heap_realloc_evaluate(ctx,ref,out);
    if(scope_mode==S_INVALID_CHILD)return scope_invalid_child_evaluate(ctx,ref,out);
    if(scope_mode==S_DEEP_512)return scope_deep_evaluate(ctx,ref,out);
    size_t owner=scope_is_ref(ref,100)?100:scope_is_ref(ref,101)?101:102;
    if(scope_mode==S_FANOUT){
        for(size_t i=0;i<scope_fanout;++i)for(size_t k=0;k<scope_kinds;++k)for(int repeat=0;repeat<3;++repeat)
            if(scope_depend(ctx,owner,i,(int)k)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
    }else if(scope_mode==S_NESTED||scope_mode==S_CONTROL){
        if(owner==100){
            if(scope_depend(ctx,100,0,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            size_t parent=linear_node(refs[100]),child=linear_node(refs[101]);GeoSourceValue value;
            linear_edge(parent,child,GEO_DEPENDENCY_VALUE_REQUIRED);
            if(geo_eval_source(ctx,refs[101],GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            for(int kind=0;kind<2;++kind)
                if(scope_depend(ctx,100,0,kind)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            if(scope_depend(ctx,100,1,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            if(scope_mode==S_CONTROL){
                if(scope_depend(ctx,100,2,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
                linear_edge(parent,parent,GEO_DEPENDENCY_VALUE_REQUIRED);
                scope_cycle_status=geo_eval_source(ctx,refs[100],GEO_DEPENDENCY_VALUE_REQUIRED,&value);
            }
        }else{
            if(scope_depend(ctx,101,0,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK||
               scope_depend(ctx,101,1,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            if(scope_manual_ancestor){
                size_t saved=ctx->active;ctx->active=linear_node(refs[100]);
                GeoSourceStatus status=scope_depend(ctx,100,0,GEO_DEPENDENCY_DEFINITION_REQUIRED);ctx->active=saved;
                if(status!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
            }
        }
    }else if(scope_mode==S_RETRY){
        ++scope_root_evaluations;
        if(scope_depend(ctx,100,0,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
        if(scope_root_evaluations==1)return false;
        if(scope_depend(ctx,100,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
    }else if(scope_mode==S_REQUIRED){
        /* All source nodes are already declared. Only the required edge
         * array realloc/retry is made to fail, not any optional scope slot. */
        fail_reallocs=1;scope_required_status=geo_eval_depend(ctx,refs[0],GEO_DEPENDENCY_VALUE_REQUIRED);fail_reallocs=0;
        if(scope_depend(ctx,100,0,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK||
           scope_depend(ctx,100,0,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK){scope_callback_error=1;return false;}
    }
    *out=(GeoSourceValue){0};out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){7,1,GEO_UNIT_SCALAR};return true;
}
static GeoEvalContext *scope_context(void)
{
    oracle_node_count=oracle_edge_count=0;scope_callback_error=0;scope_root_evaluations=0;
    scope_descriptions=scope_evaluations=0;edge_hash_calls=edge_find_calls=edge_probe_steps=0;
    GeoEvalContext *ctx=geo_eval_create(41,23);scope_callback_context=ctx;
    GeoSourceProvider provider={17,"edge.scope","test/1",NULL,scope_describe,scope_evaluate};
    if(ctx&&!geo_eval_register(ctx,&provider)){geo_eval_destroy(ctx);return NULL;}return ctx;
}
static int scope_marks_clear(GeoEvalContext *ctx)
{
    REQUIRE("scope-context-unwound",!ctx->edge_scope&&ctx->active==SIZE_MAX);
    for(size_t i=0;i<ctx->node_count;++i)
        REQUIRE("scope-node-marks-unwound",!ctx->nodes[i]->edge_scope&&!ctx->nodes[i]->edge_scope_kinds);
    return 0;
}
static GeoSourceStatus scope_top(GeoEvalContext *ctx,size_t ref,GeoSourceValue *out)
{linear_node(refs[ref]);return geo_eval_source(ctx,refs[ref],GEO_DEPENDENCY_VALUE_REQUIRED,out);}
static int scope_work(void)
{
    scope_mode=S_FANOUT;
    for(int large=0;large<2;++large){
        scope_fanout=large?96:1;scope_kinds=large?3:1;
        GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-work-context",ctx);
        REQUIRE("scope-work-evaluate",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
        REQUIRE("scope-fresh-no-edge-hash",edge_hash_calls==0);
        REQUIRE("scope-fresh-no-full-edge-search",edge_find_calls==0);
        REQUIRE("scope-fanout-all-kinds-once",geo_eval_edge_count(ctx)==scope_fanout*scope_kinds);
        REQUIRE("scope-fanout-value",value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==7&&value.as.quantity.den==1);
        REQUIRE("scope-fanout-provider-count",scope_descriptions==1&&scope_evaluations==1);
        REQUIRE("scope-fanout-original-ordered-graph",!graph_equal(ctx));if(scope_marks_clear(ctx))return 1;
        geo_eval_destroy(ctx);REQUIRE("scope-work-no-leak",!live_allocations);
    }
    return 0;
}
static int scope_nested(void)
{
    scope_mode=S_NESTED;
    for(int manual=0;manual<2;++manual){
        scope_manual_ancestor=manual;GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-nested-context",ctx);
        REQUIRE("scope-nested-evaluate",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
        REQUIRE("scope-parent-restored-no-duplicate",geo_eval_edge_count(ctx)==oracle_edge_count);
        REQUIRE("scope-nested-original-ordered-graph",!graph_equal(ctx));
        REQUIRE("scope-nested-provider-count",scope_evaluations==2&&scope_descriptions==2);
        if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-nested-no-leak",!live_allocations);
    }
    scope_manual_ancestor=0;return 0;
}
static int scope_retry(void)
{
    scope_mode=S_RETRY;GeoEvalContext *ctx=scope_context();GeoSourceValue value,old;REQUIRE("scope-retry-context",ctx);
    memset(&value,0x5a,sizeof value);memcpy(&old,&value,sizeof old);
    REQUIRE("scope-retry-first-fails",scope_top(ctx,100,&value)==GEO_SOURCE_FAILED&&!scope_callback_error);
    REQUIRE("scope-retry-failure-keeps-output",!memcmp(&value,&old,sizeof value));
    REQUIRE("scope-retry-first-edge-retained",geo_eval_edge_count(ctx)==1);
    if(scope_marks_clear(ctx))return 1;
    REQUIRE("scope-retry-second-succeeds",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-retry-retains-old-edges-once",geo_eval_edge_count(ctx)==oracle_edge_count&&oracle_edge_count==2);
    REQUIRE("scope-retry-original-ordered-graph",!graph_equal(ctx));
    REQUIRE("scope-retry-describe-once",scope_descriptions==1&&scope_evaluations==2);
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-retry-no-leak",!live_allocations);return 0;
}
static int scope_optional_failure(void)
{
    scope_mode=S_FANOUT;scope_fanout=12;scope_kinds=3;
    GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-optional-context",ctx);
    scope_undo_failures=0;index_failures=0;scope_undo_fail=1;fail_indexes=1;
    GeoSourceStatus status=scope_top(ctx,100,&value);scope_undo_fail=0;fail_indexes=0;
    REQUIRE("scope-optional-success",status==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-optional-undo-role-was-exercised",scope_undo_failures>0);
    REQUIRE("scope-optional-index-failure-was-exercised",index_failures>0);
    REQUIRE("scope-optional-linear-fallback",!ctx->edge_index&&!ctx->edge_index_capacity);
    REQUIRE("scope-optional-original-ordered-graph",!graph_equal(ctx));
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-optional-no-leak",!live_allocations);return 0;
}
static int scope_required_failure(void)
{
    scope_mode=S_REQUIRED;GeoEvalContext *ctx=scope_context();GeoSourceDescriptor d;GeoSourceValue value;REQUIRE("scope-required-context",ctx);
    for(size_t i=0;i<2;++i){size_t id=i?100:0;linear_node(refs[id]);REQUIRE("scope-required-predeclared",geo_eval_describe(ctx,refs[id],&d)==GEO_SOURCE_OK);}
    unsigned rejected=realloc_failures;
    REQUIRE("scope-required-callback-completes",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-required-failed-with-memory",scope_required_status==GEO_SOURCE_MEMORY&&realloc_failures>rejected);
    REQUIRE("scope-required-retry-keeps-edge",geo_eval_edge_count(ctx)==1&&oracle_edge_count==1);
    REQUIRE("scope-required-original-ordered-graph",!graph_equal(ctx));
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-required-no-leak",!live_allocations);return 0;
}
static int scope_dirty_fallback(void)
{
    scope_mode=S_FANOUT;scope_fanout=2;scope_kinds=1;
    for(int fail=0;fail<2;++fail){
        GeoEvalContext *ctx=scope_context();GeoSourceDescriptor d;GeoSourceValue value;REQUIRE("scope-dirty-context",ctx);
        for(size_t i=0;i<4;++i){const size_t ids[4]={100,0,1,101};size_t id=ids[i];linear_node(refs[id]);
            REQUIRE("scope-dirty-predeclare",geo_eval_describe(ctx,refs[id],&d)==GEO_SOURCE_OK);}
        ctx->active=linear_node(refs[100]);
        REQUIRE("scope-dirty-initial-general-edge",scope_depend(ctx,100,0,0)==GEO_SOURCE_OK);ctx->active=SIZE_MAX;
        REQUIRE("scope-dirty-old-table-exists",ctx->edge_index&&ctx->edge_index_capacity);
        REQUIRE("scope-dirty-first-fresh",scope_top(ctx,101,&value)==GEO_SOURCE_OK&&!scope_callback_error);
        REQUIRE("scope-dirty-second-fresh",scope_top(ctx,102,&value)==GEO_SOURCE_OK&&!scope_callback_error);
        REQUIRE("scope-dirty-prefix-pending",ctx->edge_index_dirty);
        fail_indexes=fail;ctx->active=linear_node(refs[101]);
        GeoSourceStatus status=scope_depend(ctx,101,1,0);ctx->active=SIZE_MAX;fail_indexes=0;
        REQUIRE("scope-dirty-general-lookup",status==GEO_SOURCE_OK);
        REQUIRE("scope-dirty-fallback-preserves-edges",geo_eval_edge_count(ctx)==oracle_edge_count);
        REQUIRE("scope-dirty-closed",!ctx->edge_index_dirty);
        REQUIRE("scope-dirty-complete-or-linear",fail?(!ctx->edge_index&&!ctx->edge_index_capacity):(ctx->edge_index&&ctx->edge_index_capacity));
        REQUIRE("scope-dirty-original-ordered-graph",!graph_equal(ctx));
        if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-dirty-no-leak",!live_allocations);
    }
    return 0;
}
static int scope_control(void)
{
    scope_mode=S_CONTROL;GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-control-context",ctx);
    REQUIRE("scope-control-evaluate",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-cycle-status",scope_cycle_status==GEO_SOURCE_CYCLE);
    REQUIRE("scope-describe-effects-and-cycle-order",!graph_equal(ctx));if(scope_marks_clear(ctx))return 1;
    unsigned calls=scope_descriptions+scope_evaluations;
    REQUIRE("scope-seal",geo_eval_seal(ctx));
    REQUIRE("scope-sealed-read",geo_eval_source(ctx,refs[100],GEO_DEPENDENCY_EVALUATE_BEFORE,&value)==GEO_SOURCE_OK);
    REQUIRE("scope-sealed-no-provider-calls",scope_descriptions+scope_evaluations==calls);
    REQUIRE("scope-sealed-depend-refused",geo_eval_depend(ctx,refs[0],GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_INVALID);
    REQUIRE("scope-sealed-reset-refused",!geo_eval_reset(ctx));geo_eval_destroy(ctx);REQUIRE("scope-control-no-leak",!live_allocations);
    scope_mode=S_FANOUT;scope_fanout=7;scope_kinds=2;ctx=scope_context();REQUIRE("scope-reset-context",ctx);
    REQUIRE("scope-reset-warm",scope_top(ctx,100,&value)==GEO_SOURCE_OK);
    REQUIRE("scope-reset-succeeds",geo_eval_reset(ctx));
    REQUIRE("scope-reset-frees-state",!ctx->edge_scope&&!ctx->edge_index_dirty&&!ctx->node_count&&!ctx->edge_count&&!ctx->provider_count&&live_allocations==1);
    oracle_node_count=oracle_edge_count=0;GeoSourceProvider provider={17,"edge.scope.reset","test/2",NULL,scope_describe,scope_evaluate};
    REQUIRE("scope-reset-reregister",geo_eval_register(ctx,&provider));
    REQUIRE("scope-reset-new-graph",scope_top(ctx,100,&value)==GEO_SOURCE_OK);
    REQUIRE("scope-reset-original-order",!graph_equal(ctx));if(scope_marks_clear(ctx))return 1;
    geo_eval_destroy(ctx);REQUIRE("scope-reset-no-leak",!live_allocations);return 0;
}
static int scope_heap_realloc_failure(void)
{
    scope_mode=S_HEAP_REALLOC;scope_undo_fail=0;scope_undo_failures=0;
    scope_heap_eight=scope_heap_prefix_preserved=false;
    GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-heap-realloc-context",ctx);
    REQUIRE("scope-heap-realloc-evaluates",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-heap-realloc-fallback-keeps-edges-once",geo_eval_edge_count(ctx)==oracle_edge_count&&oracle_edge_count==40);
    REQUIRE("scope-heap-realloc-really-after-eight-heap-records",scope_heap_eight&&scope_undo_failures==1);
    REQUIRE("scope-heap-realloc-failed-growth-keeps-undo-prefix",scope_heap_prefix_preserved);
    REQUIRE("scope-heap-realloc-original-ordered-graph",!graph_equal(ctx));
    REQUIRE("scope-heap-realloc-provider-count",scope_descriptions==2&&scope_evaluations==2);
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-heap-realloc-no-leak",!live_allocations);return 0;
}
static int scope_invalid_child(void)
{
    scope_mode=S_INVALID_CHILD;scope_invalid_output_unchanged=false;scope_invalid_child_status=GEO_SOURCE_OK;
    GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-invalid-child-context",ctx);
    REQUIRE("scope-invalid-child-parent-succeeds",scope_top(ctx,100,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-invalid-child-exact-status-and-output",scope_invalid_child_status==GEO_SOURCE_INVALID&&scope_invalid_output_unchanged);
    REQUIRE("scope-invalid-child-parent-marks-restored",geo_eval_edge_count(ctx)==oracle_edge_count&&oracle_edge_count==5);
    REQUIRE("scope-invalid-child-parent-value",value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==7&&value.as.quantity.den==1);
    GeoSourceNodeView child;size_t index=linear_node(refs[101]);
    REQUIRE("scope-invalid-child-stored-failed-status",geo_eval_node_at(ctx,index,&child)&&child.state==GEO_NODE_FAILED&&child.status==GEO_SOURCE_INVALID&&!child.value);
    REQUIRE("scope-invalid-child-original-ordered-graph",!graph_equal(ctx));
    REQUIRE("scope-invalid-child-provider-count",scope_descriptions==2&&scope_evaluations==2);
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-invalid-child-no-leak",!live_allocations);return 0;
}
static int scope_deep_512(void)
{
    scope_mode=S_DEEP_512;scope_deep_depth=scope_deep_max=scope_deep_unwinds=0;scope_deep_restored=1;
    GeoEvalContext *ctx=scope_context();GeoSourceValue value;REQUIRE("scope-deep-context",ctx);
    REQUIRE("scope-deep-evaluates",scope_top(ctx,SCOPE_DEEP_FIRST,&value)==GEO_SOURCE_OK&&!scope_callback_error);
    REQUIRE("scope-deep-exact-depth-and-unwind",scope_deep_max==SCOPE_TEST_DEPTH&&!scope_deep_depth&&scope_deep_unwinds==SCOPE_TEST_DEPTH);
    REQUIRE("scope-deep-every-parent-restored",scope_deep_restored&&geo_eval_edge_count(ctx)==oracle_edge_count&&oracle_edge_count==3*SCOPE_TEST_DEPTH-1);
    REQUIRE("scope-deep-exact-node-count",geo_eval_node_count(ctx)==SCOPE_TEST_DEPTH+1);
    REQUIRE("scope-deep-provider-calls",scope_descriptions==SCOPE_TEST_DEPTH&&scope_evaluations==SCOPE_TEST_DEPTH);
    REQUIRE("scope-deep-original-ordered-graph",!graph_equal(ctx));
    for(size_t i=SCOPE_DEEP_FIRST;i<SCOPE_DEEP_FIRST+SCOPE_TEST_DEPTH;++i){GeoSourceNodeView node;
        REQUIRE("scope-deep-values-survive-growth",geo_eval_node_at(ctx,linear_node(refs[i]),&node)&&node.state==GEO_NODE_VALID&&node.status==GEO_SOURCE_OK&&node.value&&
            node.value->kind==GEO_SOURCE_QUANTITY&&node.value->as.quantity.num==7&&node.value->as.quantity.den==1);}
    if(scope_marks_clear(ctx))return 1;geo_eval_destroy(ctx);REQUIRE("scope-deep-no-leak",!live_allocations);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    int (*run)(void)=!strcmp(argv[1],"scope-work")?scope_work:!strcmp(argv[1],"scope-nested")?scope_nested:
        !strcmp(argv[1],"scope-retry")?scope_retry:!strcmp(argv[1],"scope-optional")?scope_optional_failure:
        !strcmp(argv[1],"scope-required")?scope_required_failure:!strcmp(argv[1],"scope-dirty")?scope_dirty_fallback:
        !strcmp(argv[1],"scope-control")?scope_control:!strcmp(argv[1],"scope-heap-realloc")?scope_heap_realloc_failure:
        !strcmp(argv[1],"scope-invalid-child")?scope_invalid_child:!strcmp(argv[1],"scope-deep-512")?scope_deep_512:NULL;
    if(!run)return original_source_index_main(argc,argv);
    if(prepare_refs())return 1;int result=run();if(!result)printf("PASS %s\n",argv[1]);return result;
}
