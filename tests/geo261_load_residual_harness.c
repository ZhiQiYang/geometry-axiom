/* 真實 H 候選與私有驗證入口；快取儲存刻意重用，以驗證失效規則。 */
#define main geometry_program_main
#include "../current_geometry.c"
#undef main

#define REQUIRE(label,expr) do { if(!(expr)){fprintf(stderr,"ASSERT:%s line=%d expr=%s\n",label,__LINE__,#expr);return false;} } while(0)
static World live,saved;
static const char *test_case;
static bool line(World *world,const char *text)
{
    char buf[SCENE_MAX_LINE],*tokens[SCENE_MAX_TOKENS];snprintf(buf,sizeof buf,"%s",text);
    int n=split_tokens(buf,tokens,SCENE_MAX_TOKENS);
    return apply_scene_line_unchecked("residual",1,tokens,n,world);
}
static bool parameter(World *world,int value)
{
    GeoParameterCard card={0};card.id=1;card.next_field_id=2;card.count=1;card.fields[0]=1;strcpy(card.name,"offset");
    GeoParameterField field={0};field.parameter_id=1;field.id=1;strcpy(field.name,"offset");
    snprintf(field.expression,sizeof field.expression,"{\"op\":\"literal\",\"num\":\"%d\",\"den\":\"1\",\"unit\":\"mm\"}",value);
    GeoParameterError error;
    REQUIRE("parameter-staged",geo_parameters_put(&world->geo.parameters,&card,&field,&error));
    return world_revalidate(world);
}
static bool setup(World *world)
{
    REQUIRE("surface",line(world,"surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000"));
    REQUIRE("boundary-1",line(world,"timber 1 27 33 role boundary")&&line(world,"place 1 on 1 at-face e0 +u +n"));
    REQUIRE("boundary-2",line(world,"timber 2 27 33 role boundary")&&line(world,"place 2 on 1 at-face e2 +u +n"));
    REQUIRE("parameter",parameter(world,500));
    REQUIRE("guide",line(world,"guide 1 1 v param:1:1"));
    REQUIRE("placed-member",line(world,"timber 3 27 33 role primary")&&line(world,"place 3 on 1 at-line guide 1 +v +n"));
    return true;
}
static bool same_rect(GeoRect2 a,GeoRect2 b)
{return a.min_u==b.min_u&&a.max_u==b.max_u&&a.min_v==b.min_v&&a.max_v==b.max_v;}
static bool memo_scenario(World *world)
{
    AppFootprintMemo memo={0};GeoRect2 first,next,actual;
    app_footprint_memo_begin(&memo,world);
    REQUIRE("initial-footprint",app_footprint_memo_read(&memo,2,1,&first));
    REQUIRE("repeat-footprint",app_footprint_memo_read(&memo,2,1,&next)&&same_rect(first,next));
    REQUIRE("placement-key",!app_footprint_memo_read(&memo,2,999,&next));
    REQUIRE("failed-read-does-not-replace-success",app_footprint_memo_read(&memo,2,1,&next)&&same_rect(first,next));
    if(!strcmp(test_case,"parameter")){
        REQUIRE("same-candidate-parameter-edit",parameter(world,700));
        app_footprint_memo_begin(&memo,world);
        REQUIRE("stale-footprint-after-parameter",app_footprint_memo_read(&memo,2,1,&next)&&
            app_reference_member_footprint(world,2,1,&actual)&&same_rect(next,actual)&&!same_rect(first,next));
    }else{
        REQUIRE("move-source",line(world,"spec moved 900"));
        REQUIRE("same-candidate-move",line(world,"move 1 spec:moved"));
        app_footprint_memo_begin(&memo,world);
        REQUIRE("stale-footprint-after-move",app_footprint_memo_read(&memo,2,1,&next)&&
            app_reference_member_footprint(world,2,1,&actual)&&same_rect(next,actual)&&!same_rect(first,next));
    }
    saved=*world;
    REQUIRE("reject-edit",!line(world,"boundary 1 outline 0,0 20,0 20,3000 0,3000"));
    REQUIRE("rejection-rolls-back",!memcmp(&saved,world,sizeof saved));
    REQUIRE("revalidate-after-rollback",world_revalidate(world));
    app_footprint_memo_begin(&memo,world);
    REQUIRE("stale-footprint-after-rollback",app_footprint_memo_read(&memo,2,1,&actual)&&same_rect(next,actual));
    REQUIRE("same-candidate-delete",line(world,"delete timber 3"));
    app_footprint_memo_begin(&memo,world);
    REQUIRE("stale-footprint-after-delete",!app_footprint_memo_read(&memo,2,1,&actual));
    REQUIRE("out-of-range-refusal",!app_footprint_memo_read(&memo,WORLD_MAX_TIMBERS,1,&actual));
    return true;
}
typedef struct {ReferenceEval *evaluation;} Probe;
static bool probe_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;(void)ref;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_QUANTITY,.unit=GEO_UNIT_SCALAR,.context={false,0,-1}};return true;}
static bool probe_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)ref;Probe *probe=user;WoodContactSourceFacts facts;WoodContactSourceRequest request={1,false,NULL};
    if(!reference_contact_facts(probe->evaluation,graph,&request,&facts))return false;
    *out=(GeoSourceValue){.kind=GEO_SOURCE_QUANTITY,.as.quantity={1,1,GEO_UNIT_SCALAR}};return true;
}
static size_t find_node(GeoEvalContext *graph,GeoSourceRef ref)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;geo_eval_node_at(graph,i,&n);
        if(n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&(!ref.key_size||!memcmp(n.source.key,ref.key,ref.key_size)))return i;}
    return SIZE_MAX;
}
static bool has_edge(GeoEvalContext *graph,GeoSourceRef consumer,GeoSourceRef source,GeoDependencyKind kind)
{
    size_t a=find_node(graph,consumer),b=find_node(graph,source);
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge e;geo_eval_edge_at(graph,i,&e);if(e.consumer==a&&e.source==b&&e.kind==kind)return true;}
    return false;
}
static bool consumer_scenario(World *world)
{
    ReferenceEval ctx={0};ctx.world=world;ctx.sources=geo_eval_create(999,0);ctx.sources_borrowed=true;
    REQUIRE("graph-created",ctx.sources!=NULL);
    ReferenceEval *previous=g_reference_active;g_reference_active=&ctx;
    AppWorldCandidate *owner=g_active_app_candidate;g_active_app_candidate=NULL;
    for(size_t i=0;i<world->wood.timber_count;++i)ctx.wanted[i]=world->wood.timbers[i].placed;
    Probe probe={&ctx};GeoSourceProvider p={90,"test.consumer","1",&probe,probe_describe,probe_evaluate};
    REQUIRE("sources-registered",reference_sources_ensure(&ctx));
    REQUIRE("probe-registered",geo_eval_register(ctx.sources,&p));
    for(size_t i=0;i<world->wood.timber_count;++i)world->wood.timbers[i].placed=false;
    for(size_t i=0;i<world->wood.timber_count;++i)REQUIRE("rebuild-for-consumers",reference_eval_timber(&ctx,i));
    uint32_t a=1,b=2,id=3;GeoSourceRef first={90,&a,sizeof a},second={90,&b,sizeof b};GeoSourceValue value;
    REQUIRE("first-consumer",geo_eval_source(ctx.sources,first,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    REQUIRE("second-consumer",geo_eval_source(ctx.sources,second,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    WoodDefinitionKey key;
    REQUIRE("cross-consumer-placement-edge-missing",has_edge(ctx.sources,second,
        wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED));
    REQUIRE("cross-consumer-footprint-edge-missing",has_edge(ctx.sources,second,
        (GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED));
    size_t nodes=geo_eval_node_count(ctx.sources),edges=geo_eval_edge_count(ctx.sources);
    REQUIRE("seal",geo_eval_seal(ctx.sources));
    REQUIRE("sealed-lookup",geo_eval_source(ctx.sources,second,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        geo_eval_node_count(ctx.sources)==nodes&&geo_eval_edge_count(ctx.sources)==edges);
    GeoEvalContext *owned=ctx.sources;
    reference_sources_dispose(&ctx);geo_eval_destroy(owned);g_reference_active=previous;g_active_app_candidate=owner;return true;
}
static bool scenario(void *after,GeoEvalContext *graph,void *opaque)
{
    (void)graph;(void)opaque;World *world=after;
    REQUIRE("same-candidate-identity",g_active_app_candidate&&world==&g_active_app_candidate->after);
    REQUIRE("setup",setup(world));
    return !strcmp(test_case,"consumers")?consumer_scenario(world):memo_scenario(world);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;test_case=argv[1];
    AppWorldCandidate *candidate=app_world_candidate_create(&live);if(!candidate)return 2;
    bool ok=app_world_candidate_evaluate(candidate,scenario,NULL)==GEO_CANDIDATE_OK;
    if(ok&&strcmp(test_case,"consumers"))ok=app_world_candidate_seal(candidate)&&app_world_candidate_publish(candidate,&live,false);
    app_world_candidate_destroy(candidate);if(!ok)return 1;
    printf("PASS %s\n",test_case);return 0;
}
