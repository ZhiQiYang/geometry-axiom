/* Real H adapters over the same owned K stores linked into the bridge. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"ASSERT:%s:%d:%s\n",__func__,__LINE__,#x); return 1; } } while (0)

static SpaceBoundarySurface boundary_value(uint32_t id,BoundaryKind kind,Coord left,Coord right)
{
    SpaceBoundarySurface result={0};result.id=id;result.kind=kind;result.outline.count=4;
    result.outline.v[0]=(SurfacePoint2){left,0};result.outline.v[1]=(SurfacePoint2){right,0};
    result.outline.v[2]=(SurfacePoint2){right,100};result.outline.v[3]=(SurfacePoint2){left,100};
    for(size_t i=0;i<4;++i)result.outline.fixity[i]=(i&1)?EDGE_FIXED:EDGE_FREE;
    return result;
}
static SurfaceFrame domain_frame(Coord x)
{ return (SurfaceFrame){{x,13,2500},{1,0,0},{0,1,0},{0,0,1}}; }

static int boundary_ownership(void)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK(world&&before);
    SpaceBoundarySurface first=boundary_value(11,BOUNDARY_ROOM_PLAN,0,100);
    first.hole_count=1;first.holes[0].count=4;
    first.holes[0].v[0]=(SurfacePoint2){20,20};first.holes[0].v[1]=(SurfacePoint2){20,40};
    first.holes[0].v[2]=(SurfacePoint2){40,40};first.holes[0].v[3]=(SurfacePoint2){40,20};
    first.holes[0].fixity[2]=EDGE_FIXED;
    SpaceBoundarySurface second=boundary_value(22,BOUNDARY_WALL_ELEVATION,500,800);
    for(size_t i=0;i<4;++i)second.outline.fixity[i]=(i&1)?EDGE_FREE:EDGE_FIXED;
    CHECK(app_boundary_stage(world,&first)&&app_boundary_stage(world,&second));
    CHECK(world_boundary_count(world)==2&&geo_regions_count(&world->geo.region_data)==2);
    const GeoRegionDefinition *stored=geo_regions_find(&world->geo.region_data,11);
    CHECK(stored&&stored->outline.v[0].u==0&&stored->outline.v[1].u==100&&stored->holes[0].v[2].u==40);
    SpaceBoundarySurface a,b;CHECK(app_boundary_read(world,11,&a)&&app_boundary_read(world,22,&b));
    CHECK(a.kind==BOUNDARY_ROOM_PLAN&&b.kind==BOUNDARY_WALL_ELEVATION);
    CHECK(a.outline.fixity[0]==EDGE_FREE&&b.outline.fixity[0]==EDGE_FIXED);
    CHECK(a.holes[0].fixity[2]==EDGE_FIXED&&a.holes[0].fixity[1]==EDGE_FREE);
    CHECK(boundary_contains_point(&a,(SurfacePoint2){10,10}));
    CHECK(!boundary_contains_point(&a,(SurfacePoint2){30,30}));
    a.kind=BOUNDARY_WALL_ELEVATION;a.outline.v[1].u=a.outline.v[2].u=120;
    a.outline.fixity[0]=EDGE_FIXED;a.holes[0].fixity[2]=EDGE_FREE;
    CHECK(app_boundary_read(world,11,&b));
    CHECK(b.kind==BOUNDARY_ROOM_PLAN&&b.outline.v[1].u==100&&b.outline.fixity[0]==EDGE_FREE);
    CHECK(geo_regions_find(&world->geo.region_data,11)->outline.v[1].u==100);
    CHECK(app_boundary_stage(world,&a));
    CHECK(geo_regions_find(&world->geo.region_data,11)->outline.v[1].u==120);
    CHECK(app_boundary_read(world,11,&b)&&b.kind==BOUNDARY_WALL_ELEVATION&&b.outline.fixity[0]==EDGE_FIXED);
    CHECK(b.holes[0].fixity[2]==EDGE_FREE);
    memcpy(before,world,sizeof *world);a.outline.count=POLY_MAX_VERTICES+1;
    CHECK(!app_boundary_stage(world,&a)&&!memcmp(before,world,sizeof *world));
    CHECK(app_boundary_remove(world,11));
    CHECK(world_boundary_count(world)==1&&geo_regions_at(&world->geo.region_data,0)->id==22);
    CHECK(world->wood.boundary_policy[0].id==22&&world->wood.boundary_policy[0].kind==BOUNDARY_WALL_ELEVATION);
    CHECK(app_boundary_at(world,0,&b)&&b.outline.v[0].u==500&&b.outline.fixity[0]==EDGE_FIXED);
    WoodBoundaryPolicy empty={0};CHECK(!memcmp(&world->wood.boundary_policy[1],&empty,sizeof empty));
    CHECK(!app_boundary_remove(world,11));free(before);free(world);return 0;
}

static int placement_ownership(void)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK(world&&before);
    SpaceBoundarySurface boundary=boundary_value(22,BOUNDARY_ROOM_PLAN,0,100);
    CHECK(app_boundary_stage(world,&boundary));
    PlacementSurface rectangle={0};rectangle.id=101;rectangle.frame=domain_frame(7);rectangle.rect=(SurfaceRegion2){0,0,100,100};
    PlacementSurface reference={0};reference.id=102;reference.frame=domain_frame(17);reference.boundary_id=22;
    PlacementSurface components={0};components.id=103;components.frame=domain_frame(27);
    components.derived_fill_id=47;components.derived_h=-12;components.component_count=2;
    components.components[0]=boundary_value(301,BOUNDARY_ROOM_PLAN,0,100);
    components.components[1]=boundary_value(302,BOUNDARY_WALL_ELEVATION,200,300);
    components.components[1].outline.fixity[0]=EDGE_FIXED;
    CHECK(app_placement_stage(world,&rectangle)&&app_placement_stage(world,&reference)&&app_placement_stage(world,&components));
    CHECK(world_placement_count(world)==3&&geo_placements_count(&world->geo.placement_data)==3);
    const GeoPlacementDefinition *stored=geo_placements_find(&world->geo.placement_data,101);
    CHECK(stored&&stored->domain==GEO_PLACEMENT_RECT&&stored->frame.origin.x==7&&stored->rect.max_u==100);
    stored=geo_placements_find(&world->geo.placement_data,102);
    CHECK(stored&&stored->domain==GEO_PLACEMENT_REGION_REF&&stored->region_id==22);
    stored=geo_placements_find(&world->geo.placement_data,103);
    CHECK(stored&&stored->domain==GEO_PLACEMENT_REGION_SET&&stored->component_count==2&&stored->components[1].outline.v[0].u==200);
    PlacementSurface edit,read;CHECK(app_placement_read(world,103,&edit));
    CHECK(edit.derived_fill_id==47&&edit.derived_h==-12&&edit.components[1].kind==BOUNDARY_WALL_ELEVATION);
    CHECK(surface_contains_point(&edit,NULL,(SurfacePoint2){250,50}));
    CHECK(!surface_contains_point(&edit,NULL,(SurfacePoint2){150,50}));
    CHECK(!surface_contains_rect(&edit,NULL,50,10,250,20));
    edit.frame.origin.x=99;edit.derived_h=30;edit.components[1].outline.v[1].u=edit.components[1].outline.v[2].u=350;
    edit.components[1].outline.fixity[0]=EDGE_FREE;
    CHECK(app_placement_read(world,103,&read)&&read.frame.origin.x==27&&read.derived_h==-12);
    CHECK(read.components[1].outline.v[1].u==300&&read.components[1].outline.fixity[0]==EDGE_FIXED);
    CHECK(geo_placements_find(&world->geo.placement_data,103)->components[1].outline.v[1].u==300);
    CHECK(app_placement_stage(world,&edit));
    CHECK(geo_placements_find(&world->geo.placement_data,103)->frame.origin.x==99);
    CHECK(geo_placements_find(&world->geo.placement_data,103)->components[1].outline.v[1].u==350);
    CHECK(app_placement_read(world,103,&read)&&read.derived_h==30&&read.components[1].outline.fixity[0]==EDGE_FREE);
    memcpy(before,world,sizeof *world);edit.component_count=DP_COMPONENT_MAX+1;
    CHECK(!app_placement_stage(world,&edit)&&!memcmp(before,world,sizeof *world));
    CHECK(app_placement_remove(world,101));
    CHECK(world_placement_count(world)==2&&geo_placements_at(&world->geo.placement_data,0)->id==102);
    CHECK(world->wood.placement_policy[0].id==102&&world->wood.placement_policy[1].id==103);
    CHECK(app_placement_at(world,1,&read)&&read.derived_fill_id==47&&read.derived_h==30);
    CHECK(read.components[1].kind==BOUNDARY_WALL_ELEVATION&&read.components[1].outline.fixity[0]==EDGE_FREE);
    WoodPlacementPolicy empty={0};CHECK(!memcmp(&world->wood.placement_policy[2],&empty,sizeof empty));
    CHECK(!app_placement_remove(world,101));free(before);free(world);return 0;
}

static int snapshot_ownership(void)
{
    World *world=calloc(1,sizeof *world),*candidate=malloc(sizeof *candidate);CHECK(world&&candidate);
    SpaceBoundarySurface boundary=boundary_value(11,BOUNDARY_ROOM_PLAN,0,100);
    PlacementSurface placement={0};placement.id=21;placement.boundary_id=11;placement.frame=domain_frame(7);
    CHECK(app_boundary_stage(world,&boundary)&&app_placement_stage(world,&placement));
    memcpy(candidate,world,sizeof *candidate);
    SpaceBoundarySurface edit,original;CHECK(app_boundary_read(candidate,11,&edit));
    edit.outline.v[1].u=edit.outline.v[2].u=60;edit.kind=BOUNDARY_WALL_ELEVATION;
    CHECK(app_boundary_stage(candidate,&edit));
    CHECK(app_placement_remove(candidate,21));
    CHECK(app_boundary_read(world,11,&original)&&original.kind==BOUNDARY_ROOM_PLAN);
    CHECK(boundary_contains_point(&original,(SurfacePoint2){80,50}));
    CHECK(app_boundary_read(candidate,11,&edit)&&!boundary_contains_point(&edit,(SurfacePoint2){80,50}));
    CHECK(world_placement_count(world)==1&&world_placement_count(candidate)==0);
    free(candidate);free(world);return 0;
}

static bool domain_command(World *world,const char *text)
{
    char line[SCENE_MAX_LINE],*tokens[SCENE_MAX_TOKENS];snprintf(line,sizeof line,"%s",text);
    int count=split_tokens(line,tokens,SCENE_MAX_TOKENS);
    return apply_interactive_tokens("domain-product",1,tokens,count,world);
}
static int rejected_candidate(void)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK(world&&before);
    CHECK(reference_default_world(world));history_clear();memcpy(before,world,sizeof *world);
    CHECK(!domain_command(world,"boundary 1 outline 0,0 20,0 20,3000 0,3000"));
    CHECK(!memcmp(before,world,sizeof *world)&&!g_preview.valid);
    CHECK(world_boundary_count(world)==world_boundary_count(before));
    CHECK(world_placement_count(world)==world_placement_count(before));
    free(before);free(world);return 0;
}

static int inactive_rectangle(void)
{
    World *world=calloc(1,sizeof *world);CHECK(world);history_clear();
    CHECK(domain_command(world,"boundary 11 outline 0,0 100,0 100,100 0,100"));
    CHECK(domain_command(world,"boundary 22 outline 200,0 300,0 300,100 200,100"));
    CHECK(domain_command(world,"placement 101 on boundary 11 origin 0 0 0 u +x v +y rect -5 -6 7 8"));
    CHECK(domain_command(world,"placement 102 on boundary 22 origin 0 0 0 u +x v +y rect 10 20 30 40"));
    PlacementSurface first,second;CHECK(app_placement_read(world,101,&first)&&app_placement_read(world,102,&second));
    CHECK(first.rect.min_u==-5&&first.rect.min_v==-6&&first.rect.max_u==7&&first.rect.max_v==8);
    CHECK(second.rect.min_u==10&&second.rect.min_v==20&&second.rect.max_u==30&&second.rect.max_v==40);
    GeoRect2 zero={0};
    CHECK(!memcmp(&geo_placements_find(&world->geo.placement_data,101)->rect,&zero,sizeof zero));
    CHECK(!memcmp(&geo_placements_find(&world->geo.placement_data,102)->rect,&zero,sizeof zero));
    /* The rectangle is retained wire metadata, not the referenced domain. */
    SpaceBoundarySurface boundary;CHECK(app_boundary_read(world,22,&boundary));
    CHECK(surface_contains_point(&second,&boundary,(SurfacePoint2){250,50}));
    CHECK(!surface_contains_point(&second,&boundary,(SurfacePoint2){20,30}));
    CHECK(app_placement_remove(world,101)&&world_placement_count(world)==1);
    CHECK(app_placement_at(world,0,&second)&&second.id==102&&second.rect.min_u==10&&second.rect.max_v==40);
    CHECK(world->app.placement_metadata[0].unused_rect.min_v==20);
    AppPlacementMetadata empty={0};CHECK(!memcmp(&world->app.placement_metadata[1],&empty,sizeof empty));
    FILE *dump=tmpfile();CHECK(dump);world_dump_dsl(world,dump);CHECK(!fflush(dump)&&!fseek(dump,0,SEEK_SET));
    char text[4096];size_t length=fread(text,1,sizeof text-1,dump);text[length]=0;
    CHECK(!ferror(dump)&&feof(dump));fclose(dump);
    CHECK(strstr(text,"placement 102 on boundary 22 origin 0 0 0 u +x v +y\n"));
    CHECK(!strstr(text," rect "));free(world);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"boundaries"))return boundary_ownership();
    if(!strcmp(argv[1],"placements"))return placement_ownership();
    if(!strcmp(argv[1],"snapshot"))return snapshot_ownership();
    if(!strcmp(argv[1],"rollback"))return rejected_candidate();
    if(!strcmp(argv[1],"inactive-rect"))return inactive_rectangle();
    return 2;
}
