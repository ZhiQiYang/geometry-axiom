/* Actual H callbacks must consume returned authored definitions. Mutants in
 * the W serializer change only graph values, leaving this World unchanged. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
int main(int argc,char **argv)
{
    if(argc!=2)return 2;World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);
    CHECK("definition-product-memory",world&&before);
    SpaceBoundarySurface boundary={.id=1,.outline={.v={{0,0},{1000,0},{1000,800},{0,800}},.count=4}};
    for(int i=0;i<4;++i)boundary.outline.fixity[i]=EDGE_FIXED;
    CHECK("definition-product-region",app_boundary_stage(world,&boundary));
    PlacementSurface placement={.id=1,.boundary_id=1,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}}};
    CHECK("definition-product-placement",app_placement_stage(world,&placement));
    world->wood.timber_count=1;
    world->wood.timbers[0]=(WoodMember){.id=11,.size_a=40,.size_b=50,.role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1,.auto_length=true};
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=1,.anchor_kind=WOOD_ANCHOR_AT_EDGE,.span_mode=WOOD_SPAN_AUTO,
        .length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL,.ref_hole=-1,.ref_edge=0,.order=7};
    world->wood.column_count=1;world->wood.columns[0]=(WoodColumn){29,0,100,130,100,140,0,300};
    memcpy(before,world,sizeof *world);ReferenceEval ctx={0};ctx.world=world;ctx.wanted[0]=true;
    CHECK("definition-product-source-factory",reference_sources_ensure(&ctx));
    if(!strcmp(argv[1],"role")||!strcmp(argv[1],"anchor")){
        AppMemberReferenceContext member_context={0};member_context.evaluation=&ctx;member_context.world=world;
        WoodMemberReferenceFact fact;CHECK("definition-product-member-read",app_member_reference_at(&member_context,0,&fact));
        if(!strcmp(argv[1],"role"))CHECK("definition-product-role-is-returned-value",fact.member.role==WOOD_MEMBER_ROLE_BOUNDARY&&fact.member.cut_priority==1&&fact.member.auto_length);
        else CHECK("definition-product-anchor-is-returned-value",fact.anchor.order==7&&fact.anchor.placement_id==1&&fact.anchor.ref_hole==-1&&fact.anchor.ref_edge==0);
    }else if(!strcmp(argv[1],"fixity")){
        WoodBoundaryRegion actual;CHECK("definition-product-boundary-read",reference_fs_boundary(&ctx,1,&actual));
        CHECK("definition-product-fixity-is-returned-value",actual.outline.count==4&&actual.outline.fixity[0]==EDGE_FIXED&&actual.outline.fixity[3]==EDGE_FIXED);
    }else if(!strcmp(argv[1],"rc")){
        FinishObstacleRef ref={FS_OBSTACLE_COLUMN,29};GeoCoord lo[3],hi[3];CHECK("definition-product-obstacle-read",reference_fs_obstacle(&ctx,&ref,lo,hi));
        CHECK("definition-product-RC-is-returned-value",lo[0]==100&&lo[1]==100&&lo[2]==0&&hi[0]==130&&hi[1]==140&&hi[2]==300);
    }else if(!strcmp(argv[1],"unplaced")){
        /* I9 rejects an unplaced member at scene EOF. Its authored identity is
         * still available inside an unfinished candidate without a pose root. */
        CHECK("definition-product-unplaced-is-staged",!world->wood.timbers[0].placed);
        CHECK("definition-product-unplaced-definitions",wood_definition_sources_complete(ctx.definition_sources));
        bool member=false,anchor=false,dimensions=false;
        for(size_t i=0;i<geo_eval_node_count(ctx.sources);++i){GeoSourceNodeView node;WoodDefinitionKind kind;uint32_t id;
            if(geo_eval_node_at(ctx.sources,i,&node)&&node.source.provider==APP_SOURCE_WOOD_DEFINITION&&
                wood_definition_source_decode(&node.source,&kind,&id)&&id==11){
                if(kind==WOOD_DEFINITION_MEMBER)member=node.state==GEO_NODE_VALID;
                if(kind==WOOD_DEFINITION_PLACEMENT)anchor=node.state==GEO_NODE_VALID;
                if(kind==WOOD_DEFINITION_MEMBER_A||kind==WOOD_DEFINITION_MEMBER_B)dimensions=true;
            }
        }
        CHECK("definition-product-unplaced-has-definitions-without-dimensions",member&&anchor&&!dimensions);
    }else return 2;
    CHECK("definition-product-world-is-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
