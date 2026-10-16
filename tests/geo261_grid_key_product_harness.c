/* The actual retained preview consumes K vertex quantities in W grid caches. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)
static bool grid_key_line(const char *line){return feed_line("grid-key-product",1,line,&g_world);}
static bool grid_key_edge(GeoEvalContext *g,size_t a,size_t b,GeoDependencyKind kind)
{for(size_t i=0;i<geo_eval_edge_count(g);++i){GeoSourceEdge e;if(geo_eval_edge_at(g,i,&e)&&e.consumer==a&&e.source==b&&e.kind==kind)return true;}return false;}
int main(int argc,char **argv)
{
    CHECK(argc==2,"grid-key-arguments");memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(argv[1],&g_world),"grid-key-original-scene");history_clear();g_preview.ready=false;
    CHECK(grid_key_line("preview spec graph_probe 17")&&g_preview.ready&&g_preview.valid,"grid-key-valid-preview");
    AppWorldCandidate *owner=g_preview.transaction;CHECK(owner,"grid-key-candidate");
    ReferenceEval *reference=app_candidate_evaluation_state(owner->control);
    GeoEvalContext *graph=geo_candidate_sources(app_candidate_core(owner->control));
    const WoodGridApplication *grid=wood_grid_find(&owner->after.wood.grid_applications,4);
    CHECK(grid&&grid->lattice_base[0]==10&&grid->lattice_base[1]==20&&
        grid->lattice_step[0]==100&&grid->lattice_step[1]==100,"grid-key-returned-quantities-drive-actual-cache");
    CHECK(reference&&reference->world==&owner->after&&reference->sources==graph&&geo_eval_is_sealed(graph),"grid-key-same-candidate");
    GeoPoint2 sentinel={-99,-77};GeoRegionKeySources *saved_keys=reference->region_key_sources;
    reference->region_key_sources=NULL;
    bool missing_keys=reference_grid_vertex(reference,1,1,&sentinel);
    reference->region_key_sources=saved_keys;
    CHECK(!missing_keys&&sentinel.u==-99&&sentinel.v==-77,"grid-key-failed-typed-read-keeps-output");
    size_t coordinate[2]={SIZE_MAX,SIZE_MAX},ledger=SIZE_MAX,binding=SIZE_MAX,definition=SIZE_MAX;
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;CHECK(geo_eval_node_at(graph,i,&node),"grid-key-node-view");
        if(node.source.provider==APP_SOURCE_REGION_KEYS){GeoRegionKeySourceKind kind;uint32_t id,key,axis;
            CHECK(geo_region_key_source_decode(&node.source,&kind,&id,&key,&axis),"grid-key-key-decodes");
            if(id==1&&kind==GEO_REGION_KEY_SOURCE_LEDGER)ledger=i;
            if(id==1&&key==1&&kind==GEO_REGION_KEY_SOURCE_COORDINATE&&axis<2)coordinate[axis]=i;
        }else if(node.source.provider==APP_SOURCE_GRID){WoodGridSourceKind kind;uint32_t id;
            if(wood_grid_source_decode(&node.source,&kind,&id)&&id==3){
                if(kind==WOOD_GRID_SOURCE_BINDING)binding=i;
                if(kind==WOOD_GRID_SOURCE_BINDING_DEFINITION)definition=i;}}
    }
    CHECK(ledger!=SIZE_MAX&&binding!=SIZE_MAX&&definition!=SIZE_MAX,"grid-key-identities-present");
    for(size_t axis=0;axis<2;++axis)CHECK(coordinate[axis]!=SIZE_MAX&&
        grid_key_edge(graph,binding,coordinate[axis],GEO_DEPENDENCY_VALUE_REQUIRED)&&
        grid_key_edge(graph,coordinate[axis],ledger,GEO_DEPENDENCY_DEFINITION_REQUIRED),"grid-key-actual-value-and-ledger-edges");
    CHECK(grid_key_edge(graph,definition,ledger,GEO_DEPENDENCY_DEFINITION_REQUIRED),"grid-key-binding-definition-keeps-ledger");
    uint64_t candidate=geo_candidate_id(app_candidate_core(owner->control));char command[64];snprintf(command,sizeof command,"confirm %u",g_preview.token);
    CHECK(grid_key_line(command)&&g_preview.transaction==owner&&geo_candidate_id(app_candidate_core(owner->control))==candidate,"grid-key-confirms-same-candidate");
    grid=wood_grid_find(&g_world.wood.grid_applications,4);
    CHECK(grid&&grid->lattice_base[0]==10&&grid->lattice_base[1]==20,"grid-key-published-cache");
    CHECK(grid_key_line("undo")&&!geo_named_values_find(&g_world.geo.named_values,"graph_probe"),"grid-key-undo-restores-definition");
    return 0;
}
