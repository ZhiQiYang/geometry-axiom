/* 真實 H 候選與私有驗證入口；快取儲存刻意重用，以驗證失效規則。 */
/* 與 NativeBuild 的產品 CLI 一樣，unity 測試使用主控台入口。 */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stdbool.h>
/* Private negative controls use this only to target the second real consumer;
 * the unchanged production body never reads this test flag. */
static bool residual_second_consumer;
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
static bool collection_facts(void *user,GeoEvalContext *graph,const WoodContactSourceRequest *request,WoodContactSourceFacts *out)
{
    (void)user;(void)graph;(void)request;memset(out,0,sizeof *out);out->region_count=1;
    WoodBoundaryRegion *region=&out->regions[0];region->outline.count=4;
    region->outline.v[0]=(GeoPoint2){0,0};region->outline.v[1]=(GeoPoint2){1000,0};
    region->outline.v[2]=(GeoPoint2){1000,1000};region->outline.v[3]=(GeoPoint2){0,1000};
    for(unsigned i=0;i<4;++i)region->outline.fixity[i]=WOOD_EDGE_FIXED;
    return true;
}
static bool collection_reset_scenario(void)
{
    GeoEvalContext *graph=geo_eval_create(1000,0);REQUIRE("collection-graph",graph);
    WoodContactSources *sources=wood_contact_sources_create(graph,80,collection_facts,NULL);
    REQUIRE("collection-provider",sources);WoodContactSourceRequest request={1,false,NULL};WoodStopFace faces[32];size_t count;
    REQUIRE("initial-collection",wood_contact_sources_collect(sources,&request,faces,32,&count)&&count>1);
    GeoSourceProvider provider=*geo_eval_provider_at(graph,0);char name[80],fingerprint[80];
    snprintf(name,sizeof name,"%s",provider.name_space);snprintf(fingerprint,sizeof fingerprint,"%s",provider.implementation_fingerprint);
    provider.name_space=name;provider.implementation_fingerprint=fingerprint;
    REQUIRE("collection-reset",geo_eval_reset(graph)&&geo_eval_register(graph,&provider));
    WoodContactSourceKey key;GeoSourceValue value;
    REQUIRE("feature-after-reset",geo_eval_source(graph,wood_contact_source_ref(80,WOOD_CONTACT_SOURCE_FEATURE,1,0,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    REQUIRE("hint-must-match-key",geo_eval_source(graph,wood_contact_source_ref(80,WOOD_CONTACT_SOURCE_FEATURE,1,1,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    GeoSourceRef collection=wood_contact_source_ref(80,WOOD_CONTACT_SOURCE_COLLECTION,1,0,&key);GeoSourceNodeView node;
    REQUIRE("reset-collection-must-be-evaluated",geo_eval_node_at(graph,find_node(graph,collection),&node)&&node.state==GEO_NODE_VALID&&node.value);
    REQUIRE("reset-insertion-order",geo_eval_node_count(graph)==3&&node.source.key_size==17&&find_node(graph,collection)==1);
    REQUIRE("reset-feature-edge",geo_eval_edge_count(graph)==2);
    REQUIRE("second-reset",geo_eval_reset(graph)&&geo_eval_register(graph,&provider));
    GeoSourceDescriptor descriptor;
    REQUIRE("describe-before-feature",geo_eval_describe(graph,collection,&descriptor)==GEO_SOURCE_OK);
    REQUIRE("described-node-still-needs-evaluation",geo_eval_node_at(graph,0,&node)&&node.state==GEO_NODE_NEW&&!node.value);
    REQUIRE("feature-after-description",geo_eval_source(graph,wood_contact_source_ref(80,WOOD_CONTACT_SOURCE_FEATURE,1,0,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    REQUIRE("described-collection-evaluated",geo_eval_node_at(graph,0,&node)&&node.state==GEO_NODE_VALID&&node.value);
    REQUIRE("described-insertion-order",geo_eval_node_count(graph)==2&&geo_eval_edge_count(graph)==1);
    REQUIRE("reset-seal",geo_eval_seal(graph));wood_contact_sources_destroy(sources);geo_eval_destroy(graph);return true;
}
typedef struct {ReferenceEval *ctx;unsigned mode;} CacheConsumer;
static bool cache_consumer_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    CacheConsumer *probe=user;ReferenceEval *ctx=probe->ctx;uint32_t consumer;
    if(ref->key_size!=sizeof consumer)return false;memcpy(&consumer,ref->key,sizeof consumer);
    residual_second_consumer=consumer==2;
    for(unsigned repeat=0;repeat<2;++repeat){
        if(probe->mode==1){WoodMemberDefinition definition;
            if(!reference_member_definition_read(ctx,0,41,&definition)||definition.id!=41||definition.dimension[0]!=10)return false;
        }else if(probe->mode==2){WoodMemberPlacement anchor;
            if(!reference_member_anchor_read(ctx,0,41,&anchor)||anchor.placement_id!=7||anchor.order!=1)return false;
        }else if(probe->mode==3){WoodContactSourceFacts facts;WoodContactSourceRequest request={7,false,NULL};
            if(graph!=ctx->sources||!reference_contact_facts(ctx,graph,&request,&facts)||facts.member_count!=1||
                !facts.members[0].footprint_valid||!same_rect(facts.members[0].footprint,(GeoRect2){10,20,110,30}))return false;
        }else if(!reference_eval_timber_relation(ctx,0,consumer==1?GEO_DEPENDENCY_DEFINITION_REQUIRED:GEO_DEPENDENCY_EVALUATE_BEFORE))return false;
    }
    residual_second_consumer=false;
    *out=(GeoSourceValue){.kind=GEO_SOURCE_QUANTITY,.as.quantity={1,1,GEO_UNIT_SCALAR}};return true;
}
static bool ordered_cache_edges(GeoEvalContext *graph,size_t prefix_count,const GeoSourceEdge *prefix,
    const GeoSourceRef *consumers,const GeoSourceRef *sources,const GeoDependencyKind *kinds,size_t source_count)
{
    if(geo_eval_edge_count(graph)!=prefix_count+2*source_count)return false;
    for(size_t i=0;i<prefix_count;++i){GeoSourceEdge actual;
        if(!geo_eval_edge_at(graph,i,&actual)||actual.consumer!=prefix[i].consumer||actual.source!=prefix[i].source||actual.kind!=prefix[i].kind)return false;
    }
    for(size_t c=0;c<2;++c)for(size_t s=0;s<source_count;++s){GeoSourceEdge actual;
        GeoDependencyKind kind=kinds[c*source_count+s];
        if(!geo_eval_edge_at(graph,prefix_count+c*source_count+s,&actual)||actual.consumer!=find_node(graph,consumers[c])||
            actual.source!=find_node(graph,sources[s])||actual.kind!=kind)return false;
    }
    return true;
}
static bool cache_consumer_scenario(const char *name)
{
    World *world=calloc(1,sizeof *world),*before=calloc(1,sizeof *before);ReferenceEval *ctx=calloc(1,sizeof *ctx);
    REQUIRE("cache-consumer-allocation",world&&before&&ctx);
    PlacementSurface host={.id=7,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,1000,1000}};
    REQUIRE("cache-consumer-host",app_placement_stage(world,&host));
    world->wood.timber_count=1;
    world->wood.timbers[0]=(WoodMember){.id=41,.length=100,.size_a=10,.size_b=5,.placed=true,.auto_length=true,
        .role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1,.origin={10,20,0},.axis_length={1,0,0},.axis_a={0,1,0},.axis_b={0,0,1}};
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=7,.uv={10,20},.order=1,.anchor_kind=WOOD_ANCHOR_AT,
        .length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL};
    ctx->world=world;ctx->wanted[0]=true;
    ReferenceEval *previous=g_reference_active;AppWorldCandidate *owner=g_active_app_candidate;
    g_reference_active=ctx;g_active_app_candidate=NULL;
    REQUIRE("cache-consumer-register-real-providers",reference_sources_ensure(ctx));
    unsigned mode=!strcmp(name,"cache-definition")?1:!strcmp(name,"cache-anchor")?2:!strcmp(name,"cache-footprint")?3:4;
    CacheConsumer probe={ctx,mode};GeoSourceProvider provider={90,"test.cache-consumer","1",&probe,probe_describe,cache_consumer_evaluate};
    REQUIRE("cache-consumer-register",geo_eval_register(ctx->sources,&provider));
    /* Prime the registered real pose provider's documented snapshot path.
     * Every later read uses the returned canonical BOX and normal H memo. */
    ctx->use_current_values=true;
    REQUIRE("cache-consumer-prime-real-pose",reference_eval_timber_relation(ctx,0,GEO_DEPENDENCY_VALUE_REQUIRED));
    ctx->use_current_values=false;
    WoodMemberDefinition definition;WoodMemberPlacement anchor;WoodContactSourceFacts facts;WoodContactSourceRequest request={7,false,NULL};
    REQUIRE("cache-consumer-prime-real-definition",reference_member_definition_read(ctx,0,41,&definition));
    REQUIRE("cache-consumer-prime-real-anchor",reference_member_anchor_read(ctx,0,41,&anchor));
    REQUIRE("cache-consumer-prime-real-footprint",reference_contact_facts(ctx,ctx->sources,&request,&facts)&&facts.member_count==1&&
        facts.members[0].footprint_valid&&same_rect(facts.members[0].footprint,(GeoRect2){10,20,110,30}));
    REQUIRE("cache-consumer-natural-memos",ctx->member_reads[0].definition_valid&&ctx->member_reads[0].anchor_valid&&
        ctx->member_reads[0].pose_valid&&ctx->member_reads[0].footprint_valid);
    size_t prefix_count=geo_eval_edge_count(ctx->sources),prefix_nodes=geo_eval_node_count(ctx->sources);
    GeoSourceEdge *prefix=calloc(prefix_count?prefix_count:1,sizeof *prefix);REQUIRE("cache-consumer-prefix",prefix);
    for(size_t i=0;i<prefix_count;++i)REQUIRE("cache-consumer-prefix-read",geo_eval_edge_at(ctx->sources,i,&prefix[i]));
    memcpy(before,world,sizeof *before);
    uint32_t first=1,second=2,id=41;GeoSourceRef consumers[2]={{90,&first,sizeof first},{90,&second,sizeof second}};GeoSourceValue value;
    REQUIRE("cache-consumer-first",geo_eval_source(ctx->sources,consumers[0],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    REQUIRE("cache-consumer-second",geo_eval_source(ctx->sources,consumers[1],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    GeoSourceRef sources[5];GeoDependencyKind kinds[10];size_t count=1;WoodDefinitionKey wood;GeoPlacementSourceKey frame,region,placement;
    if(mode==1)sources[0]=wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_MEMBER,id,&wood);
    else if(mode==2)sources[0]=wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&wood);
    else if(mode==3){count=5;
        sources[0]=geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_FRAME,7,&frame);
        sources[1]=geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,7,&region);
        sources[2]=geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_DEFINITION,7,&placement);
        sources[3]=wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&wood);
        sources[4]=(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id};
    }else sources[0]=(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id};
    for(size_t c=0;c<2;++c)for(size_t i=0;i<count;++i)
        kinds[c*count+i]=mode==3?(i==2||i==3?GEO_DEPENDENCY_DEFINITION_REQUIRED:GEO_DEPENDENCY_VALUE_REQUIRED):
            mode==4?(c==0?GEO_DEPENDENCY_DEFINITION_REQUIRED:GEO_DEPENDENCY_EVALUATE_BEFORE):GEO_DEPENDENCY_DEFINITION_REQUIRED;
    const char *marker=mode==1?"definition-cache-second-consumer-edge-and-order":mode==2?"anchor-cache-second-consumer-edge-and-order":
        mode==3?"footprint-cache-second-consumer-edge-and-order":!strcmp(name,"cache-pose-kind")?
        "pose-cache-preserves-requested-dependency-kind":"pose-cache-second-consumer-edge-and-order";
    REQUIRE(marker,ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count));
    REQUIRE("cache-consumer-source-node-order",geo_eval_node_count(ctx->sources)==prefix_nodes+2&&
        find_node(ctx->sources,consumers[0])==prefix_nodes&&find_node(ctx->sources,consumers[1])==prefix_nodes+1);
    size_t nodes=geo_eval_node_count(ctx->sources),edges=geo_eval_edge_count(ctx->sources);
    REQUIRE("cache-consumer-repeated-reads",geo_eval_source(ctx->sources,consumers[1],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        geo_eval_node_count(ctx->sources)==nodes&&geo_eval_edge_count(ctx->sources)==edges&&
        ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count));
    REQUIRE("cache-consumer-world-unchanged",!memcmp(before,world,sizeof *before));
    REQUIRE("cache-consumer-seal",geo_eval_seal(ctx->sources));
    REQUIRE("cache-consumer-sealed-read",geo_eval_source(ctx->sources,consumers[1],GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        geo_eval_node_count(ctx->sources)==nodes&&geo_eval_edge_count(ctx->sources)==edges);
    free(prefix);reference_sources_dispose(ctx);g_reference_active=previous;g_active_app_candidate=owner;
    free(ctx);free(before);free(world);return true;
}
#include "geo261_member_reads_cases.inc"
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
    if(!strncmp(test_case,"member-",7)){
        bool ok=!strcmp(test_case,"member-anchor-id")?member_reads_anchor_id_case():
            !strcmp(test_case,"member-anchor-miss")?member_reads_anchor_miss_case():
            !strcmp(test_case,"member-placement-key")?member_reads_placement_key_case():false;
        if(ok)printf("PASS %s\n",test_case);return ok?0:1;
    }
    if(!strncmp(test_case,"cache-",6)){
        bool ok=cache_consumer_scenario(test_case);if(ok)printf("PASS %s\n",test_case);return ok?0:1;
    }
    if(!strcmp(test_case,"collection-reset")){
        bool ok=collection_reset_scenario();if(ok)printf("PASS %s\n",test_case);return ok?0:1;
    }
    AppWorldCandidate *candidate=app_world_candidate_create(&live);if(!candidate)return 2;
    bool ok=app_world_candidate_evaluate(candidate,scenario,NULL)==GEO_CANDIDATE_OK;
    if(ok&&strcmp(test_case,"consumers"))ok=app_world_candidate_seal(candidate)&&app_world_candidate_publish(candidate,&live,false);
    app_world_candidate_destroy(candidate);if(!ok)return 1;
    printf("PASS %s\n",test_case);return 0;
}
