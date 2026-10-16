/* Inspect the actual H/W callbacks and K graph on an invalid candidate. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(void)
{
    World *world=calloc(1,sizeof *world);CHECK(world);
    PlacementSurface placement={.id=1,
        .frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,1000,1000}};
    CHECK(app_placement_stage(world,&placement));
    world->wood.timber_count=2;
    for(size_t i=0;i<2;++i){
        CHECK(timber_construct((uint32_t)i+1,0,40,50,true,TIMBER_ROLE_PRIMARY,0,&world->wood.timbers[i]));
        world->wood.anchors[i]=(TimberAnchor){.placement_id=1,.anchor_kind=ANCHOR_AT_LINE,.ref_guide=(uint32_t)i+1,.order=i+1};
        GuideLine guide={.id=(uint32_t)i+1,.placement_id=1,.direction=GUIDE_ALONG_V};
        CHECK(app_guide_put(world,&guide,"timber:2:u:lo"));
    }
    ReferenceEval ctx={0};ctx.world=world;ctx.wanted[0]=ctx.wanted[1]=true;
    g_reference_capturing=true;g_reference_issue_count=0;g_revalidate_error[0]=0;
    CHECK(!reference_eval_timber(&ctx,0));
    const uint32_t ids[]={1,2,0,2,0,1};
    const char *clauses[]={"I9/I7","I9/I7","D6a/I7/I9","I9/I13","D6a/I7/I9","I9/I13"};
    CHECK(g_reference_issue_count==6);
    for(size_t i=0;i<6;++i)CHECK(g_reference_issues[i].timber==ids[i]&&!strcmp(g_reference_issues[i].clause,clauses[i]));
    CHECK(geo_eval_node_count(ctx.sources)==6&&geo_eval_edge_count(ctx.sources)==7);
    size_t soft=0;for(size_t i=0;i<geo_eval_edge_count(ctx.sources);++i){GeoSourceEdge edge;
        CHECK(geo_eval_edge_at(ctx.sources,i,&edge));if(edge.kind==GEO_DEPENDENCY_EVALUATE_BEFORE)++soft;}
    CHECK(soft==1);reference_sources_dispose(&ctx);
    /* The current-cache path was historically observational even if the caller
     * supplies an unresolved cache while testing a disposable candidate. */
    ctx=(ReferenceEval){0};ctx.world=world;ctx.use_current_values=true;
    GuideLine guide=*geo_guides_at(&world->geo.guide_lines,0);guide.offset=37;guide.resolved=false;
    CHECK(geo_guides_put(&world->geo.guide_lines,&guide));
    CHECK(reference_eval_guide(&ctx,0)&&geo_guides_at(&world->geo.guide_lines,0)->offset==37&&!geo_guides_at(&world->geo.guide_lines,0)->resolved);
    reference_sources_dispose(&ctx);free(world);return 0;
}
