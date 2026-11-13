/* The bridge's retained preview must carry the actual enclosure calculation. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)

static bool enclosure_product_line(const char *line)
{return feed_line("enclosure-product",1,line,&g_world);}
static bool enclosure_product_bounds(const World *world,Coord top)
{
    const GeoEnclosure *s=geo_enclosures_find(&world->geo.enclosures,5);
    return s&&s->member_count==1&&s->member_ids[0]==7&&!s->closed&&
        s->min[0]==10&&s->min[1]==20&&s->min[2]==0&&
        s->max[0]==110&&s->max[1]==220&&s->max[2]==top;
}
static int enclosure_product_graph(AppWorldCandidate *owner)
{
    ReferenceEval *reference=app_candidate_evaluation_state(owner->control);
    GeoEvalContext *graph=geo_candidate_sources(app_candidate_core(owner->control));
    CHECK(reference&&reference->world==&owner->after&&reference->sources==graph&&
        reference->enclosure_sources&&geo_eval_is_sealed(graph),"space-same-candidate-provider");
    size_t result=SIZE_MAX,definition=SIZE_MAX,frame=SIZE_MAX,region=SIZE_MAX;
    for(size_t i=0;i<geo_eval_node_count(graph);++i){
        GeoSourceNodeView node;CHECK(geo_eval_node_at(graph,i,&node),"space-node-view");
        if(node.source.provider==APP_SOURCE_ENCLOSURE){
            GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
            CHECK(geo_enclosure_source_decode(&node.source,&kind,&id,&axis,&slot),"space-key-decodes");
            if(id!=5)continue;
            if(kind==GEO_ENCLOSURE_SOURCE_DEFINITION)definition=i;
            if(kind==GEO_ENCLOSURE_SOURCE_RESULT){
                CHECK(node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
                    !strcmp(node.value->as.definition.schema,"geo.enclosure.result/1"),"space-result-typed-value");
                result=i;
            }
        }else if(node.source.provider==APP_SOURCE_PLACEMENT){
            GeoPlacementSourceKind kind;uint32_t id;
            if(geo_placement_source_decode(&node.source,&kind,&id)&&id==9&&kind==GEO_PLACEMENT_SOURCE_FRAME)frame=i;
        }else if(node.source.provider==APP_SOURCE_REGION){
            uint32_t id;if(geo_region_source_decode(&node.source,&id)&&id==7)region=i;
        }
    }
    CHECK(result!=SIZE_MAX&&definition!=SIZE_MAX&&frame!=SIZE_MAX&&region!=SIZE_MAX,
        "space-rebuild-consumes-enclosure-source");
    bool member_edge=false,frame_edge=false,region_edge=false;
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){
        GeoSourceEdge edge;CHECK(geo_eval_edge_at(graph,i,&edge),"space-edge-view");
        if(edge.consumer!=result)continue;
        if(edge.source==definition&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED)member_edge=true;
        if(edge.source==frame&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED)frame_edge=true;
        if(edge.source==region&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED)region_edge=true;
    }
    CHECK(member_edge&&frame_edge&&region_edge,"space-result-real-input-edges");return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(argv[1],&g_world),"space-existing-dsl-load");
    history_clear();g_preview.ready=false;
    CHECK(enclosure_product_bounds(&g_world,330),"space-baseline-bounds");
    World *before=malloc(sizeof *before);CHECK(before,"space-snapshot-memory");memcpy(before,&g_world,sizeof *before);
    uint64_t revision=g_definition_revision;
    CHECK(enclosure_product_line("preview placement 9 on boundary 7 origin 10 20 340 u +x v +y")&&
        g_preview.ready&&g_preview.valid&&g_preview.transaction,"space-preview-valid");
    AppWorldCandidate *owner=g_preview.transaction;
    CHECK(enclosure_product_bounds(&owner->after,340),"space-result-applied");
    CHECK(!memcmp(before,&g_world,sizeof *before)&&g_definition_revision==revision,"space-preview-keeps-live");
    CHECK(enclosure_product_graph(owner)==0,"space-preview-graph");
    char confirm[64];snprintf(confirm,sizeof confirm,"confirm %u",g_preview.token);
    CHECK(enclosure_product_line(confirm)&&g_preview.transaction==owner&&
        enclosure_product_bounds(&g_world,340)&&g_definition_revision==revision+1,"space-confirm-same-candidate");
    CHECK(enclosure_product_graph(owner)==0,"space-published-graph");
    CHECK(enclosure_product_line("undo")&&enclosure_product_bounds(&g_world,330),"space-undo-restores-bounds");
    const GeoPlacementDefinition *placement=geo_placements_find(&g_world.geo.placement_data,9);
    CHECK(placement&&placement->frame.origin.z==330,"space-undo-restores-placement");
    free(before);return 0;
}
