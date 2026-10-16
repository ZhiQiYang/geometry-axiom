/* The real bridge translation unit, H candidate adapters and final W pass.
 * No substitute domain selector or boundary-role verdict lives in this test. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)

static SpaceBoundarySurface component(uint32_t id,Coord left,Coord right)
{
    SpaceBoundarySurface b={0};b.id=id;b.kind=BOUNDARY_ROOM_PLAN;b.outline.count=4;
    b.outline.v[0]=(SurfacePoint2){left,0};b.outline.v[1]=(SurfacePoint2){right,0};
    b.outline.v[2]=(SurfacePoint2){right,100};b.outline.v[3]=(SurfacePoint2){left,100};
    for(size_t i=0;i<4;++i)b.outline.fixity[i]=EDGE_FIXED;return b;
}
static int selected_component(void)
{
    World *world=calloc(1,sizeof *world),*candidate=calloc(1,sizeof *candidate);
    CHECK(world&&candidate,"validation-product-world-allocation");
    PlacementSurface p={0};p.id=103;p.derived_fill_id=47;p.derived_h=5;p.component_count=2;
    p.frame=(SurfaceFrame){{7,13,2500},{1,0,0},{0,1,0},{0,0,1}};
    p.components[0]=component(301,0,100);p.components[1]=component(302,200,300);
    CHECK(app_placement_stage(world,&p),"validation-product-derived-stage");
    CHECK(wood_member_construct(17,0,10,5,true,WOOD_MEMBER_ROLE_BOUNDARY,0,&world->wood.timbers[0]),
        "validation-product-member-construction");
    world->wood.timbers[0].length=100;
    world->wood.anchors[0]=(TimberAnchor){.placement_id=103,.uv={200,0},.anchor_kind=ANCHOR_AT,
        .span_mode=SPAN_AUTO,.length_direction=SURFACE_DIRECTION_POS_U,.depth_side=SURFACE_DEPTH_POSITIVE_NORMAL};
    CHECK(timber_place_a0_on_surface(&world->wood.timbers[0],&p,&p.components[1],(SurfacePoint2){200,0},
        SURFACE_DIRECTION_POS_U,SURFACE_DEPTH_POSITIVE_NORMAL),
        "validation-product-second-component-pose");
    world->wood.timber_count=1;WoodMember original;memcpy(&original,&world->wood.timbers[0],sizeof original);char error[256]="preserved";
    WoodWorldValidationContext validation=app_world_validation_context(world);
    /* Removing H's footprint-based selection makes this placed boundary
     * member get checked against component 1 and changes the final verdict. */
    CHECK(wood_world_validate_members(&validation,error,sizeof error)&&!strcmp(error,"preserved"),
        "validation-product-selected-component-verdict");
    CHECK(!memcmp(&original,&world->wood.timbers[0],sizeof original),"validation-product-probe-keeps-member");
    GeoRect2 rect={200,0,300,10};AppValidationDomain domain;
    CHECK(app_validation_domain(world,103,&rect,&domain)&&domain.b==&domain.p->components[1]&&domain.b->id==302,
        "validation-product-selected-boundary-identity");
    WoodGridHost copied;
    CHECK(app_validation_host(world,103,&rect,&copied)&&copied.component_count==2&&copied.bounds.min_u==0&&
        copied.bounds.max_u==300&&copied.components[1].outline.v[1].u==300,"validation-product-copied-domain");
    memcpy(candidate,world,sizeof *world);p.components[1].outline.fixity[0]=EDGE_FREE;
    CHECK(app_placement_stage(candidate,&p),"validation-product-candidate-stage");
    validation=app_world_validation_context(candidate);
    CHECK(!wood_world_validate_members(&validation,error,sizeof error)&&strstr(error,"V_BOUNDARY_ROLE")&&strstr(error,"e0 是自由邊"),
        "validation-product-selected-fixity-refusal");
    CHECK(copied.components[1].outline.fixity[0]==EDGE_FIXED&&copied.components[1].outline.v[1].u==300,
        "validation-product-host-value-lifetime");
    validation=app_world_validation_context(world);strcpy(error,"still-original");
    CHECK(wood_world_validate_members(&validation,error,sizeof error)&&!strcmp(error,"still-original")&&
        !memcmp(&original,&world->wood.timbers[0],sizeof original),"validation-product-candidate-isolation");
    free(candidate);free(world);return 0;
}
int main(int argc,char **argv)
{if(argc==2&&!strcmp(argv[1],"selected-component"))return selected_component();return 2;}
