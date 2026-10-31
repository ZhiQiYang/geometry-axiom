/* This private client includes the unchanged residual harness with its final
 * main renamed by the Python compiler. Product hooks are observation only. */
#include "local-init-original-harness.c"

static bool local_watch,local_fail_calloc;
static size_t local_notes,local_note_bytes,local_callocs,local_probes;
static size_t local_persistent_probes,local_fallback_probes;
static size_t local_zero_calls,local_zero_bytes;
static ReferenceEval *local_last;

static void reference_local_note(size_t bytes)
{if(local_watch){++local_notes;local_note_bytes+=bytes;}}
static void *reference_local_test_calloc(size_t count,size_t bytes)
{
    if(local_watch){++local_callocs;if(local_fail_calloc)return NULL;}
    return calloc(count,bytes);
}
#ifdef REFERENCE_LOCAL_WRAP
/* The linker redirects actual emitted calls, including an implicit aggregate
 * initializer. No memset macro substitutes for compiler-generated work. */
void *__real_memset(void *,int,size_t);
void *__wrap_memset(void *pointer,int value,size_t bytes)
{
    if(local_watch&&value==0&&bytes==sizeof(ReferenceEval)){
        ++local_zero_calls;local_zero_bytes+=bytes;
    }
    return __real_memset(pointer,value,bytes);
}
#endif
static void local_reset(void)
{
    local_watch=false;local_fail_calloc=false;
    local_notes=local_note_bytes=local_callocs=local_probes=0;
    local_persistent_probes=local_fallback_probes=0;
    local_zero_calls=local_zero_bytes=0;local_last=NULL;
}
static bool reference_local_probe(ReferenceEval *ctx,bool persistent)
{
    if(!local_watch)return true;
    ++local_probes;local_last=ctx;
    REQUIRE("reference-local-context-present",ctx!=NULL);
    if(persistent){
        ++local_persistent_probes;
        REQUIRE("reference-local-persistent-owner",g_active_app_candidate&&
            app_candidate_evaluation_state(g_active_app_candidate->control)==ctx&&
            ctx->world==&g_active_app_candidate->after&&ctx->sources&&ctx->sources_borrowed);
        return true;
    }
    ++local_fallback_probes;
    /* Compare semantic fields, never aggregate padding or an indeterminate
     * object representation. The original {0} initializes each field below. */
    REQUIRE("reference-local-fallback-initialized",!ctx->world&&!ctx->sources&&
        !ctx->sources_borrowed&&!ctx->sources_registered&&!ctx->parameter_sources&&
        !ctx->parameter_snapshot&&!ctx->linear_definition_sources&&!ctx->version_sources&&
        !ctx->engineering_sources&&!ctx->section_profile_sources&&!ctx->finish_sources&&
        !ctx->placement_sources&&!ctx->region_key_sources&&!ctx->enclosure_sources&&
        !ctx->definition_sources&&!ctx->grid_sources&&!ctx->contact_sources&&!ctx->assembly_sources&&
        !ctx->use_current_values&&!ctx->source_failure);
    for(size_t i=0;i<GEO_GUIDE_CAPACITY;++i)
        REQUIRE("reference-local-fallback-guide-zero",!ctx->guide_values_valid[i]&&
            ctx->guide_values[i].coordinate==0&&!ctx->guide_values[i].context.has_placement&&
            ctx->guide_values[i].context.placement==0&&ctx->guide_values[i].context.axis==0);
    for(size_t i=0;i<WORLD_MAX_TIMBERS;++i)
        REQUIRE("reference-local-fallback-member-zero",!ctx->wanted[i]&&
            !ctx->member_reads[i].anchor_valid&&!ctx->member_reads[i].definition_valid&&
            !ctx->member_reads[i].pose_valid&&!ctx->member_reads[i].footprint_valid&&
            !ctx->member_reads[i].footprint_ok&&!ctx->member_reads[i].contact_valid&&
            ctx->member_reads[i].id==0&&ctx->member_reads[i].pose_id==0&&
            ctx->member_reads[i].placement==0&&ctx->member_reads[i].contact_id==0);
    return true;
}

typedef struct {uint32_t provider;size_t size;unsigned char *key;} LocalNode;
typedef struct {size_t nodes,edges;LocalNode *node;GeoSourceEdge *edge;} LocalGraph;
static bool local_graph_capture(GeoEvalContext *graph,LocalGraph *copy)
{
    *copy=(LocalGraph){0};copy->nodes=geo_eval_node_count(graph);copy->edges=geo_eval_edge_count(graph);
    copy->node=calloc(copy->nodes?copy->nodes:1,sizeof *copy->node);
    copy->edge=calloc(copy->edges?copy->edges:1,sizeof *copy->edge);
    REQUIRE("reference-local-graph-memory",copy->node&&copy->edge);
    for(size_t i=0;i<copy->nodes;++i){GeoSourceNodeView node;
        REQUIRE("reference-local-node-capture",geo_eval_node_at(graph,i,&node));
        copy->node[i].provider=node.source.provider;copy->node[i].size=node.source.key_size;
        copy->node[i].key=malloc(node.source.key_size?node.source.key_size:1);
        REQUIRE("reference-local-node-key-memory",copy->node[i].key);
        if(node.source.key_size)memcpy(copy->node[i].key,node.source.key,node.source.key_size);
    }
    for(size_t i=0;i<copy->edges;++i)
        REQUIRE("reference-local-edge-capture",geo_eval_edge_at(graph,i,&copy->edge[i]));
    return true;
}
static bool local_graph_matches(GeoEvalContext *graph,const LocalGraph *copy)
{
    REQUIRE("reference-local-ordered-graph-count",geo_eval_node_count(graph)==copy->nodes&&
        geo_eval_edge_count(graph)==copy->edges);
    for(size_t i=0;i<copy->nodes;++i){GeoSourceNodeView node;
        REQUIRE("reference-local-ordered-node",geo_eval_node_at(graph,i,&node)&&
            node.source.provider==copy->node[i].provider&&node.source.key_size==copy->node[i].size&&
            (!node.source.key_size||!memcmp(node.source.key,copy->node[i].key,node.source.key_size)));
    }
    for(size_t i=0;i<copy->edges;++i){GeoSourceEdge edge;
        REQUIRE("reference-local-ordered-edge",geo_eval_edge_at(graph,i,&edge)&&
            edge.consumer==copy->edge[i].consumer&&edge.source==copy->edge[i].source&&
            edge.kind==copy->edge[i].kind);
    }
    return true;
}
static void local_graph_dispose(LocalGraph *copy)
{for(size_t i=0;i<copy->nodes;++i)free(copy->node[i].key);free(copy->node);free(copy->edge);}

static bool local_persistent_case(void *after,GeoEvalContext *graph,void *opaque)
{
    (void)graph;bool ordered=opaque!=NULL;World *world=after;
    REQUIRE("reference-local-new-candidate",g_active_app_candidate&&
        world==&g_active_app_candidate->after&&
        !app_candidate_evaluation_state(g_active_app_candidate->control));
    local_reset();local_watch=true;bool ok=reference_rebuild(world);local_watch=false;
    REQUIRE("reference-local-persistent-first",ok&&local_callocs==1&&local_persistent_probes==1&&local_fallback_probes==0);
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    REQUIRE("reference-local-persistent-state",ctx&&ctx==local_last&&ctx->sources==graph);
    saved=*world;LocalGraph copy={0};
    if(ordered){REQUIRE("reference-local-nonempty-graph",geo_eval_node_count(graph)>0&&geo_eval_edge_count(graph)>0);
        REQUIRE("reference-local-graph-captured",local_graph_capture(graph,&copy));}
    local_reset();local_watch=true;ok=reference_rebuild(world);local_watch=false;
    REQUIRE("reference-local-persistent-reuse",ok&&local_callocs==0&&local_persistent_probes==1&&
        local_fallback_probes==0&&local_last==ctx&&app_candidate_evaluation_state(g_active_app_candidate->control)==ctx);
    REQUIRE("reference-local-world-unchanged",!memcmp(&saved,world,sizeof saved));
    if(ordered){bool same=local_graph_matches(graph,&copy);local_graph_dispose(&copy);REQUIRE("reference-local-graph-unchanged",same);}
    return true;
}
static bool local_fallback_active(void *after,GeoEvalContext *graph,void *opaque)
{
    (void)graph;(void)opaque;
    REQUIRE("reference-local-other-world",g_active_app_candidate&&after!=&live&&
        !app_candidate_evaluation_state(g_active_app_candidate->control));
    saved=live;local_reset();local_watch=true;bool ok=reference_rebuild(&live);local_watch=false;
    REQUIRE("reference-local-active-fallback",ok&&local_fallback_probes==1&&local_persistent_probes==0&&
        local_callocs==0&&local_notes==1&&local_note_bytes==sizeof(ReferenceEval));
    REQUIRE("reference-local-active-fallback-owner-untouched",!app_candidate_evaluation_state(g_active_app_candidate->control));
    REQUIRE("reference-local-active-fallback-world",!memcmp(&saved,&live,sizeof live));return true;
}
static bool local_allocation_failure(void *after,GeoEvalContext *graph,void *opaque)
{
    (void)opaque;World *world=after;saved=*world;
    local_reset();local_fail_calloc=true;local_watch=true;bool ok=reference_rebuild(world);local_watch=false;
    REQUIRE("reference-local-allocation-failure",!ok&&local_callocs==1&&local_probes==0&&
        !app_candidate_evaluation_state(g_active_app_candidate->control));
    REQUIRE("reference-local-failure-world",!memcmp(&saved,world,sizeof saved));
    /* The existing begin-candidate reset occurs before calloc: no claim that
     * failure preserves the earlier graph. Recovery must register afresh. */
    REQUIRE("reference-local-failure-reset",geo_eval_node_count(graph)==0&&geo_eval_edge_count(graph)==0);
    local_reset();local_watch=true;ok=reference_rebuild(world);local_watch=false;
    REQUIRE("reference-local-allocation-recovery",ok&&local_callocs==1&&local_probes==1&&local_persistent_probes==1);
    REQUIRE("reference-local-recovery-world",!memcmp(&saved,world,sizeof saved));return true;
}
static bool local_work(void *after,GeoEvalContext *graph,void *opaque)
{
    (void)graph;(void)opaque;World *world=after;
    REQUIRE("reference-local-empty-work-fixture",world->wood.timber_count==0&&
        geo_guides_count(&world->geo.guide_lines)==0&&geo_datums_count(&world->geo.datum_planes)==0);
    local_reset();local_watch=true;bool first=reference_rebuild(world),second=reference_rebuild(world);local_watch=false;
    REQUIRE("reference-local-work-semantics",first&&second&&local_callocs==1&&local_persistent_probes==2&&local_fallback_probes==0);
#ifdef REFERENCE_LOCAL_WRAP
    printf("reference-local-work scope=linux-link-wrap calls=%zu bytes=%zu note_calls=%zu note_bytes=%zu context_bytes=%zu\n",
        local_zero_calls,local_zero_bytes,local_notes,local_note_bytes,sizeof(ReferenceEval));fflush(stdout);
    REQUIRE("persistent-reference-local-zero-work",local_zero_calls==0&&local_zero_bytes==0);
#else
    printf("reference-local-work scope=portable-branch-note-only actual_memset=UNOBSERVED note_calls=%zu note_bytes=%zu context_bytes=%zu\n",
        local_notes,local_note_bytes,sizeof(ReferenceEval));fflush(stdout);
    REQUIRE("persistent-reference-local-zero-work",local_notes==0&&local_note_bytes==0);
#endif
    REQUIRE("reference-local-persistent-branch-note",local_notes==0&&local_note_bytes==0);return true;
}
static bool local_fallback_case(void)
{
    saved=live;local_reset();local_watch=true;bool ok=reference_rebuild(&live);local_watch=false;
    REQUIRE("reference-local-fallback-rebuild",ok&&local_callocs==0&&local_fallback_probes==1&&
        local_persistent_probes==0&&local_notes==1&&local_note_bytes==sizeof(ReferenceEval));
    REQUIRE("reference-local-fallback-world",!memcmp(&saved,&live,sizeof live));
    AppWorldCandidate *candidate=app_world_candidate_create(&live);REQUIRE("reference-local-fallback-candidate",candidate);
    ok=app_world_candidate_evaluate(candidate,local_fallback_active,NULL)==GEO_CANDIDATE_OK;
    app_world_candidate_destroy(candidate);REQUIRE("reference-local-fallback-with-active-owner",ok);return true;
}
static bool local_wrap_calibration(void)
{
    /* A real empty-world fallback initialization calibrates the same emitted
     * sizeof(ReferenceEval) memset under the same compiler/link options. */
    local_reset();local_watch=true;bool ok=reference_rebuild(&live);local_watch=false;
    REQUIRE("reference-local-wrap-calibration-semantics",ok&&local_notes==1&&local_fallback_probes==1);
#ifdef REFERENCE_LOCAL_WRAP
    printf("reference-local-calibration calls=%zu bytes=%zu context_bytes=%zu\n",local_zero_calls,local_zero_bytes,sizeof(ReferenceEval));
    REQUIRE("reference-local-wrap-calibration",local_zero_calls==1&&local_zero_bytes==sizeof(ReferenceEval));
#endif
    return true;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;const char *name=argv[1];test_case=name;
    bool persistent=!strcmp(name,"persistent"),fallback=!strcmp(name,"fallback"),failure=!strcmp(name,"allocation-failure"),
        ordered=!strcmp(name,"ordered-graph"),work=!strcmp(name,"work");
    if(!persistent&&!fallback&&!failure&&!ordered&&!work)return 2;
    if((persistent||fallback||ordered)&&!setup(&live))return 1;
    if(fallback){bool ok=local_fallback_case();if(ok)printf("PASS %s\n",name);return ok?0:1;}
    if(work&&!local_wrap_calibration())return 1;
    AppWorldCandidate *candidate=app_world_candidate_create(&live);if(!candidate)return 2;
    AppCandidateEvaluate callback=work?local_work:failure?local_allocation_failure:local_persistent_case;
    bool ok=app_world_candidate_evaluate(candidate,callback,ordered?(void*)candidate:NULL)==GEO_CANDIDATE_OK;
    app_world_candidate_destroy(candidate);
    if(ok&&ordered)ok=cache_consumer_scenario("cache-definition")&&cache_consumer_scenario("cache-footprint")&&cache_consumer_scenario("cache-pose-kind");
    if(ok)printf("PASS %s\n",name);return ok?0:1;
}
