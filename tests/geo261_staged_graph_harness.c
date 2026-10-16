/* Real H handlers must validate their staged bytes in the retained candidate.
 * The fixture contains a spec -> guide edge and a placed boundary member.
 * This client links the same external K/W/H objects as the real bridge. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)

typedef enum {
    CASE_BOUNDARY_KEYS,CASE_BOUNDARY_KEYED,CASE_GRID_SYSTEM,CASE_GRID_SYSTEM_APPLICATION,
    CASE_GRID_SOURCE_RULE,CASE_GRID_BINDING,CASE_GRID_BINDING_APPLICATION
} StagedCase;
static bool staged_line(const char *value)
{return feed_line("staged-graph-witness",1,value,&g_world);}
static bool staged_confirm(void)
{char command[64];snprintf(command,sizeof command,"confirm %u",g_preview.token);return staged_line(command);}
static bool staged_commit(const char *command)
{
    uint32_t previous=g_preview.token;bool ok=staged_line(command);
    if(g_preview.ready&&g_preview.token!=previous)return g_preview.valid&&staged_confirm();
    return ok;
}
static char *staged_dump(const World *world)
{
    FILE *stream=tmpfile();if(!stream)return NULL;
    world_dump_dsl(world,stream);if(fflush(stream)){fclose(stream);return NULL;}
    long length=ftell(stream);if(length<0||fseek(stream,0,SEEK_SET)){fclose(stream);return NULL;}
    char *text=malloc((size_t)length+1);if(!text){fclose(stream);return NULL;}
    size_t used=fread(text,1,(size_t)length,stream);
    if(ferror(stream)){free(text);fclose(stream);return NULL;}
    text[used]='\0';fclose(stream);return text;
}
static bool staged_binding_command(char *command,size_t capacity)
{
    SpaceBoundarySurface boundary;char hash[65];
    if(!app_boundary_read(&g_world,71,&boundary))return false;
    boundary_geometry_hash(&boundary,hash);if(!hash[0])return false;
    int size=snprintf(command,capacity,
        "grid-binding 1 on-boundary 71 from-system 5 vertex outer 0 geometry-hash %s cell -2 -3 anchor 2 4 2 8",hash);
    return size>0&&(size_t)size<capacity;
}
static bool staged_command(StagedCase which,char *command,size_t capacity)
{
    /* DSL spelling and geometry come from test_geo261_native_grid_product,
     * test_grid_system_contract and test_infinite_grid_contract. */
    const char *text=NULL;
    switch(which){
    case CASE_BOUNDARY_KEYS:text="boundary-vertex-keys 71 outer 1 2 3 4 next-key 5";break;
    case CASE_BOUNDARY_KEYED:{
        if(!staged_commit("boundary-vertex-keys 71 outer 1 2 3 4 next-key 5"))return false;
        SpaceBoundarySurface boundary;char hash[65];
        if(!app_boundary_read(&g_world,71,&boundary))return false;
        boundary_geometry_hash(&boundary,hash);if(!hash[0])return false;
        int size=snprintf(command,capacity,"boundary-keyed 71 geometry-hash %s outline "
            "1:410,500 2:1610,500 3:1610,1300 4:410,1300",hash);
        return size>0&&(size_t)size<capacity;
    }
    case CASE_GRID_SYSTEM:text="grid-system 5 name-hex 677269642073746f7265 main-along none u repeat 17 120 v repeat -21 80";break;
    case CASE_GRID_SYSTEM_APPLICATION:text="grid 10 on 1 from-system 6 origin 0 0";break;
    case CASE_GRID_SOURCE_RULE:text="grid-source-rule 5 create name-hex 72756c65 selector cell -2 -3 divide 3 2";break;
    case CASE_GRID_BINDING:return staged_binding_command(command,capacity);
    case CASE_GRID_BINDING_APPLICATION:{
        char binding[512];if(!staged_binding_command(binding,sizeof binding)||!staged_commit(binding))return false;
        text="grid 10 on 71 from-binding 1";break;
    }
    }
    int size=snprintf(command,capacity,"%s",text);return size>0&&(size_t)size<capacity;
}
static int staged_graph(AppWorldCandidate *owner)
{
    GeoCandidate *core=app_candidate_core(owner->control);GeoEvalContext *sources=geo_candidate_sources(core);
    CHECK(sources&&geo_eval_is_sealed(sources),"retained-graph-is-sealed");
    CHECK(geo_eval_candidate_id(sources)==geo_candidate_id(core),"graph-retains-candidate-identity");
    CHECK(geo_eval_base_revision(sources)==geo_candidate_base_revision(core),"graph-retains-base-revision");
    CHECK(geo_eval_provider_count(sources)>=4&&geo_eval_node_count(sources)>=3,"retained-graph-is-not-empty");
    bool guide_provider=false,member_provider=false,reference_provider=false;
    for(size_t i=0;i<geo_eval_provider_count(sources);++i){
        const GeoSourceProvider *provider=geo_eval_provider_at(sources,i);CHECK(provider,"provider-view");
        if(provider->token<APP_SOURCE_GUIDE||provider->token>APP_SOURCE_PARAMETER)continue;
        ReferenceEval *state=provider->candidate_state;
        CHECK(state&&state==app_candidate_evaluation_state(owner->control),"provider-state-owned-by-retained-candidate");
        CHECK(state->world==&owner->after&&state->sources==sources&&state->sources_borrowed,"provider-uses-actual-after-and-resolver");
        if(provider->token==APP_SOURCE_GUIDE)guide_provider=true;
        if(provider->token==APP_SOURCE_MEMBER_POSE)member_provider=true;
        if(provider->token==APP_SOURCE_REFERENCE)reference_provider=true;
    }
    CHECK(guide_provider&&member_provider&&reference_provider,"actual-guide-member-reference-providers");
    size_t guide=SIZE_MAX,reference=SIZE_MAX;bool member=false,dependency=false;
    for(size_t i=0;i<geo_eval_node_count(sources);++i){
        GeoSourceNodeView node;CHECK(geo_eval_node_at(sources,i,&node),"node-view");
        if((node.source.provider==APP_SOURCE_GUIDE||node.source.provider==APP_SOURCE_MEMBER_POSE)&&node.source.key_size==sizeof(uint32_t)){
            uint32_t id;memcpy(&id,node.source.key,sizeof id);if(id!=1)continue;
            CHECK(node.state==GEO_NODE_VALID&&node.status==GEO_SOURCE_OK&&node.value,"existing-object-was-evaluated");
            if(node.source.provider==APP_SOURCE_GUIDE){
                CHECK(node.value->kind==GEO_SOURCE_AXIS_POSITION&&node.value->as.position.coordinate==500,"guide-value-from-existing-spec");guide=i;
            }else{
                CHECK(node.value->kind==GEO_SOURCE_BOX&&node.value->as.box.extent[0]==1000&&
                    node.value->as.box.extent[1]==40&&node.value->as.box.extent[2]==50,"member-pose-from-existing-boundary");member=true;
            }
        }
        if(node.source.provider==APP_SOURCE_REFERENCE&&node.source.key_size==sizeof(AppReferenceSourceKey)){
            AppReferenceSourceKey key;memcpy(&key,node.source.key,sizeof key);
            if(!strcmp(key.expression,"spec:x")){
                CHECK(node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_QUANTITY&&
                    node.value->as.quantity.num==500&&node.value->as.quantity.den==1,"reference-node-evaluated");reference=i;
            }
        }
    }
    CHECK(guide!=SIZE_MAX&&reference!=SIZE_MAX&&member,"actual-dependency-nodes-retained");
    for(size_t i=0;i<geo_eval_edge_count(sources);++i){
        GeoSourceEdge edge;CHECK(geo_eval_edge_at(sources,i,&edge),"edge-view");
        if(edge.consumer==guide&&edge.source==reference&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED)dependency=true;
    }
    CHECK(dependency,"guide-spec-dependency-edge-retained");return 0;
}
static int staged_effect(StagedCase which,const World *world)
{
    switch(which){
    case CASE_BOUNDARY_KEYS:{
        const BoundaryVertexKeys *keys=world_find_vertex_keys(world,71);
        CHECK(keys&&keys->loop_count==1&&keys->counts[0]==4&&keys->next_key==5&&keys->keys[0][0]==1,"boundary-keys-staged");break;
    }
    case CASE_BOUNDARY_KEYED:{
        SurfacePoint2 point;CHECK(boundary_vertex_by_key(world,71,1,&point)&&point.u==410&&point.v==500,"keyed-vertex-moved");break;
    }
    case CASE_GRID_SYSTEM:{
        const GridSystem *source=world_find_grid_system(world,5);
        CHECK(source&&source->axis[0].start==17&&source->axis[1].start==-21,"grid-system-redeclared");break;
    }
    case CASE_GRID_SYSTEM_APPLICATION:{
        const ReferenceGrid *grid=world_find_grid(world,10);
        CHECK(grid&&grid->from_system&&grid->system_id==6&&grid->placement_id==1,"finite-source-applied");break;
    }
    case CASE_GRID_SOURCE_RULE:{
        const GridSystem *source=world_find_grid_system(world,5);
        CHECK(source&&source->rule_count==1&&source->next_rule_key==2&&source->rules[0].key==1&&
            source->rules[0].divisions[0]==3&&source->rules[0].divisions[1]==2,"source-rule-created-once");break;
    }
    case CASE_GRID_BINDING:{
        const GridBinding *binding=world_find_grid_binding(world,1);
        CHECK(binding&&binding->boundary_id==71&&binding->system_id==5&&binding->cell[0]==-2&&binding->cell[1]==-3&&
            binding->anchor_num[0]==1&&binding->anchor_den[0]==2&&binding->anchor_num[1]==1&&binding->anchor_den[1]==4,"binding-created-and-normalized");break;
    }
    case CASE_GRID_BINDING_APPLICATION:{
        const ReferenceGrid *grid=world_find_grid(world,10);
        CHECK(grid&&grid->from_binding&&grid->binding_id==1&&grid->placement_id==71,"binding-applied");break;
    }
    }
    return 0;
}
static int staged_witness(const char *path,StagedCase which)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(path,&g_world),"existing-scene-fixture-loads");history_clear();g_preview.ready=false;
    char command[1024],preview[1100];CHECK(staged_command(which,command,sizeof command),"case-prerequisites");
    history_clear();World *before=malloc(sizeof *before);CHECK(before,"snapshot-memory");memcpy(before,&g_world,sizeof *before);
    char *before_dump=staged_dump(&g_world);CHECK(before_dump,"before-dump");uint64_t revision=g_definition_revision;
    snprintf(preview,sizeof preview,"preview %s",command);
    CHECK(staged_line(preview)&&g_preview.ready&&g_preview.valid,"ready-valid-preview");
    AppWorldCandidate *owner=g_preview.transaction;CHECK(owner,"preview-owner");GeoCandidate *core=app_candidate_core(owner->control);
    uint64_t id=geo_candidate_id(core);const void *before_buffer=app_candidate_before(owner->control);void *after_buffer=app_candidate_after(owner->control);
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_SEALED&&geo_candidate_evaluation_generation(core)==1,"preview-evaluated-once");
    CHECK(before_buffer==&owner->before&&after_buffer==&owner->after&&geo_candidate_base_revision(core)==revision,"candidate-buffers-and-base");
    CHECK(staged_graph(owner)==0&&staged_effect(which,&owner->after)==0,"preview-graph-and-effect");
    char *unchanged=staged_dump(&g_world),*after_dump=staged_dump(&owner->after);CHECK(unchanged&&after_dump,"preview-dumps");
    CHECK(!strcmp(before_dump,unchanged)&&!memcmp(before,&g_world,sizeof *before)&&g_definition_revision==revision,"preview-keeps-live-dump-and-bytes");
    CHECK(strcmp(before_dump,after_dump)!=0,"preview-has-real-staged-change");free(unchanged);
    CHECK(staged_confirm(),"same-candidate-confirm");
    CHECK(g_preview.transaction==owner&&app_candidate_core(owner->control)==core&&geo_candidate_id(core)==id&&
        app_candidate_before(owner->control)==before_buffer&&app_candidate_after(owner->control)==after_buffer,"confirm-keeps-owner-id-and-buffers");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_evaluation_generation(core)==2,"confirm-fully-revalidates-same-candidate");
    CHECK(staged_graph(owner)==0&&staged_effect(which,&g_world)==0,"published-graph-and-effect");
    CHECK(g_definition_revision==revision+1&&!g_preview.ready,"single-publication-revision");
    char *published=staged_dump(&g_world);CHECK(published&&!strcmp(after_dump,published),"publishes-reviewed-dump");free(published);
    CHECK(!staged_confirm()&&geo_candidate_evaluation_generation(core)==2,"confirm-token-is-single-use");
    CHECK(staged_line("undo"),"one-undo-step");char *restored=staged_dump(&g_world);
    CHECK(restored&&!strcmp(before_dump,restored),"undo-restores-whole-baseline");
    free(restored);free(before_dump);free(after_dump);free(before);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    static const char *const cases[]={"boundary-keys","boundary-keyed","grid-system","grid-system-application",
        "grid-source-rule","grid-binding","grid-binding-application"};
    for(size_t i=0;i<sizeof cases/sizeof cases[0];++i)if(!strcmp(argv[1],cases[i]))return staged_witness(argv[2],(StagedCase)i);
    return 2;
}
