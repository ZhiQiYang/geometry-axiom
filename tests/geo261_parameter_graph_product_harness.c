/* Include the actual bridge and inspect the candidate used by its real DSL.
 * No synthetic provider or reconstructed expected graph is used here. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)

static bool parameter_graph_line(const char *line)
{return feed_line("parameter-graph-witness",1,line,&g_world);}
static bool parameter_graph_confirm(void)
{char line[64];snprintf(line,sizeof line,"confirm %u",g_preview.token);return parameter_graph_line(line);}
static char *parameter_graph_dump(const World *world)
{
    FILE *stream=tmpfile();if(!stream)return NULL;world_dump_dsl(world,stream);
    if(fflush(stream)){fclose(stream);return NULL;}long length=ftell(stream);
    if(length<0||fseek(stream,0,SEEK_SET)){fclose(stream);return NULL;}
    char *text=malloc((size_t)length+1);if(!text){fclose(stream);return NULL;}
    size_t used=fread(text,1,(size_t)length,stream);if(ferror(stream)){free(text);fclose(stream);return NULL;}
    text[used]='\0';fclose(stream);return text;
}
static bool parameter_graph_quantity(GeoQuantity q,int64_t num,int64_t den)
{return q.num==num&&q.den==den&&q.unit==GEO_UNIT_LENGTH;}
static int parameter_graph_values(const World *world,Coord guide_position)
{
    int first=parameter_field_index(world,1,1),second=parameter_field_index(world,2,1);
    CHECK(first>=0&&second>=0,"product-parameter-fields-present");
    const ParameterField *fields=geo_parameters_fields(&world->geo.parameters);
    CHECK(parameter_graph_quantity(fields[first].value,7,1)&&parameter_graph_quantity(fields[second].value,7,3),"product-parameter-values-exact");
    const GuideLine *guide=geo_guides_find(&world->geo.guide_lines,1),*parameter=geo_guides_find(&world->geo.guide_lines,2);
    CHECK(guide&&guide->resolved&&guide->offset==guide_position&&parameter&&parameter->resolved&&parameter->offset==7,"product-guides-use-spec-and-parameter");
    return 0;
}
static int parameter_graph_retained(AppWorldCandidate *owner)
{
    GeoCandidate *candidate=app_candidate_core(owner->control);GeoEvalContext *sources=geo_candidate_sources(candidate);
    ReferenceEval *host=app_candidate_evaluation_state(owner->control);
    CHECK(sources&&geo_eval_is_sealed(sources)&&host&&host->world==&owner->after&&
        host->sources==sources&&host->sources_borrowed,"product-retains-exact-candidate-context");
    CHECK(geo_eval_candidate_id(sources)==geo_candidate_id(candidate)&&geo_eval_base_revision(sources)==geo_candidate_base_revision(candidate),"product-graph-candidate-identity");
    bool provider_found=false;
    for(size_t i=0;i<geo_eval_provider_count(sources);++i){const GeoSourceProvider *provider=geo_eval_provider_at(sources,i);
        CHECK(provider,"product-provider-view");if(provider->token!=APP_SOURCE_PARAMETER)continue;
        GeoParameterSources *parameters=provider->candidate_state;
        CHECK(parameters==host->parameter_sources&&!strcmp(provider->name_space,"core.parameter.field"),"product-parameter-provider-binding");
        CHECK(geo_parameter_sources_store(parameters)==&owner->after.geo.parameters&&geo_parameter_sources_context(parameters)==sources,"product-parameter-provider-exact-store-and-context");
        provider_found=true;
    }
    CHECK(provider_found,"product-parameter-provider-retained");
    size_t first=SIZE_MAX,second=SIZE_MAX,guide=SIZE_MAX;
    for(size_t i=0;i<geo_eval_node_count(sources);++i){GeoSourceNodeView node;CHECK(geo_eval_node_at(sources,i,&node),"product-node-view");
        if(node.source.provider==APP_SOURCE_PARAMETER&&node.source.key_size==2*sizeof(uint32_t)){
            uint32_t ids[2];memcpy(ids,node.source.key,sizeof ids);if(ids[1]!=1||(ids[0]!=1&&ids[0]!=2))continue;
            CHECK(node.state==GEO_NODE_VALID&&node.status==GEO_SOURCE_OK&&node.value&&node.value->kind==GEO_SOURCE_QUANTITY&&
                node.descriptor.unit==GEO_UNIT_LENGTH&&parameter_graph_quantity(node.value->as.quantity,7,ids[0]==1?1:3),"product-graph-values-exact");
            if(ids[0]==1)first=i;else second=i;
        }
        if(node.source.provider==APP_SOURCE_GUIDE&&node.source.key_size==sizeof(uint32_t)){
            uint32_t id;memcpy(&id,node.source.key,sizeof id);if(id==2)guide=i;
        }
    }
    CHECK(first!=SIZE_MAX&&second!=SIZE_MAX&&guide!=SIZE_MAX,"product-parameter-and-guide-nodes-present");
    bool dependency=false,consumer=false;
    for(size_t i=0;i<geo_eval_edge_count(sources);++i){GeoSourceEdge edge;CHECK(geo_eval_edge_at(sources,i,&edge),"product-edge-view");
        if(edge.kind!=GEO_DEPENDENCY_VALUE_REQUIRED)continue;
        if(edge.consumer==first&&edge.source==second)dependency=true;
        if(edge.consumer==guide&&edge.source==first)consumer=true;
    }
    /* Values above remain correct when parameters.c bypasses its resolver.
     * The same K mutation must fail this actual candidate edge assertion. */
    CHECK(dependency,"parameter-ast-dependency-edge");
    CHECK(consumer,"product-guide-consumes-real-parameter-node");return 0;
}
static int parameter_graph_preview(void)
{
    World *before=malloc(sizeof *before);CHECK(before,"product-before-memory");memcpy(before,&g_world,sizeof *before);
    char *before_dump=parameter_graph_dump(&g_world);CHECK(before_dump,"product-before-dump");uint64_t revision=g_definition_revision;
    CHECK(parameter_graph_values(&g_world,500)==0,"product-baseline-values");
    CHECK(parameter_graph_line("preview spec x 600")&&g_preview.ready&&g_preview.valid,"product-ready-valid-preview");
    AppWorldCandidate *owner=g_preview.transaction;CHECK(owner,"product-preview-owner");GeoCandidate *core=app_candidate_core(owner->control);
    uint64_t candidate_id=geo_candidate_id(core);const void *before_buffer=app_candidate_before(owner->control);void *after_buffer=app_candidate_after(owner->control);
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_SEALED&&geo_candidate_evaluation_generation(core)==1&&
        before_buffer==&owner->before&&after_buffer==&owner->after&&geo_candidate_base_revision(core)==revision,"product-preview-evaluated-once");
    CHECK(parameter_graph_values(&owner->after,600)==0,"product-preview-values");
    CHECK(parameter_graph_retained(owner)==0,"product-preview-retains-parameter-graph");
    char *live_dump=parameter_graph_dump(&g_world),*after_dump=parameter_graph_dump(&owner->after);CHECK(live_dump&&after_dump,"product-preview-dumps");
    CHECK(!memcmp(before,&g_world,sizeof *before)&&!strcmp(before_dump,live_dump)&&g_definition_revision==revision,"product-preview-keeps-live-bytes-and-dump");
    CHECK(strcmp(before_dump,after_dump)!=0,"product-preview-has-real-change");free(live_dump);
    CHECK(parameter_graph_confirm(),"product-confirm-same-candidate");
    CHECK(g_preview.transaction==owner&&app_candidate_core(owner->control)==core&&geo_candidate_id(core)==candidate_id&&
        app_candidate_before(owner->control)==before_buffer&&app_candidate_after(owner->control)==after_buffer,"product-confirm-retains-owner-identity-and-buffers");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_evaluation_generation(core)==2,"product-confirm-generation-two");
    CHECK(parameter_graph_values(&g_world,600)==0&&parameter_graph_retained(owner)==0,"product-published-values-and-graph");
    CHECK(g_definition_revision==revision+1&&!g_preview.ready,"product-one-publication-revision");
    char *published=parameter_graph_dump(&g_world);CHECK(published&&!strcmp(published,after_dump),"product-publishes-reviewed-dump");free(published);
    CHECK(!parameter_graph_confirm()&&geo_candidate_evaluation_generation(core)==2,"product-token-single-use");
    CHECK(parameter_graph_line("undo"),"product-one-undo-step");char *restored=parameter_graph_dump(&g_world);
    CHECK(restored&&!strcmp(restored,before_dump)&&parameter_graph_values(&g_world,500)==0,"product-one-undo-restores-whole-definition");
    free(restored);free(before_dump);free(after_dump);free(before);return 0;
}
static int parameter_graph_read_only(void)
{
    /* Deliberately stale live caches make a write through the observational
     * path detectable even though the valid definitions still evaluate to 7. */
    int first=parameter_field_index(&g_world,1,1),second=parameter_field_index(&g_world,2,1);
    CHECK(first>=0&&second>=0,"readonly-fields");
    g_world.geo.parameters.fields[first].value=(GeoQuantity){-123,1,GEO_UNIT_LENGTH};
    g_world.geo.parameters.fields[second].value=(GeoQuantity){-456,1,GEO_UNIT_LENGTH};
    World *before=malloc(sizeof *before);CHECK(before,"readonly-snapshot-memory");memcpy(before,&g_world,sizeof *before);
    ReferenceEval ctx={0};ctx.world=&g_world;ctx.use_current_values=true;
    CHECK(reference_sources_ensure(&ctx)&&ctx.parameter_snapshot&&ctx.parameter_snapshot!=&g_world.geo.parameters,"readonly-clones-parameter-store");
    CHECK(geo_parameter_sources_store(ctx.parameter_sources)==ctx.parameter_snapshot&&
        geo_parameter_sources_context(ctx.parameter_sources)==ctx.sources,"readonly-provider-uses-clone-and-own-resolver");
    GeoQuantity value;CHECK(reference_parameter_quantity(&ctx,(ParameterRef){true,1,1},&value)&&parameter_graph_quantity(value,7,1),"readonly-computes-exact-value-from-definitions");
    CHECK(!memcmp(before,&g_world,sizeof *before),"readonly-recompute-keeps-live-bytes");
    CHECK(geo_eval_node_count(ctx.sources)==2&&geo_eval_edge_count(ctx.sources)==1&&geo_eval_seal(ctx.sources),"readonly-retains-and-seals-native-parameter-edge");
    size_t nodes=geo_eval_node_count(ctx.sources),edges=geo_eval_edge_count(ctx.sources);
    CHECK(reference_parameter_quantity(&ctx,(ParameterRef){true,1,1},&value)&&parameter_graph_quantity(value,7,1)&&
        nodes==geo_eval_node_count(ctx.sources)&&edges==geo_eval_edge_count(ctx.sources)&&!memcmp(before,&g_world,sizeof *before),"readonly-sealed-read-is-observational");
    reference_sources_dispose(&ctx);CHECK(!memcmp(before,&g_world,sizeof *before),"readonly-disposal-keeps-live-bytes");free(before);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(argv[2],&g_world),"existing-parameter-scene-dsl-loads");history_clear();g_preview.ready=false;
    if(!strcmp(argv[1],"preview"))return parameter_graph_preview();
    if(!strcmp(argv[1],"read-only"))return parameter_graph_read_only();
    return 2;
}
