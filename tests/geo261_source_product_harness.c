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
    world->placement_count=1;world->placements[0]=(PlacementSurface){.id=1,
        .frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,1000,1000}};
    world->timber_count=2;world->guide_count=2;
    for(size_t i=0;i<2;++i){
        CHECK(timber_construct((uint32_t)i+1,0,40,50,true,TIMBER_ROLE_PRIMARY,0,&world->timbers[i]));
        world->anchors[i]=(TimberAnchor){.placement_id=1,.anchor_kind=ANCHOR_AT_LINE,.ref_guide=(uint32_t)i+1,.order=i+1};
        world->guides[i]=(GuideLine){.id=(uint32_t)i+1,.placement_id=1,.direction=GUIDE_ALONG_V};
        strcpy(world->guides[i].expression,"timber:2:u:lo");
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
    world->guides[0].offset=37;world->guides[0].resolved=false;
    CHECK(reference_eval_guide(&ctx,0)&&world->guides[0].offset==37&&!world->guides[0].resolved);
    reference_sources_dispose(&ctx);free(world);return 0;
}
