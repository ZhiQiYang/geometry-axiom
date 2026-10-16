/* Actual H composition: role checks and rejected-candidate cache writes. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(x) do{if(!(x)){fprintf(stderr,"ASSERT:%s:%d\n",__func__,__LINE__);return 1;}}while(0)

static GridSystem host_system(void)
{
    GridSystem system={0};system.id=5;strcpy(system.name,"host");system.next_rule_key=1;
    system.axis[0].source=system.axis[1].source=GRID_SRC_REPEAT;
    system.axis[0].start=7;system.axis[0].step=120;
    system.axis[1].start=-11;system.axis[1].step=80;return system;
}
static int first_error(void)
{
    World *world=calloc(1,sizeof *world);CHECK(world);GridSystem system=host_system();char error[512];
    system.rule_count=1;system.rules[0].key=1;system.next_rule_key=2;
    strcpy(system.rules[0].name,"rule");system.rules[0].divisions[0]=system.rules[0].divisions[1]=1;
    CHECK(app_grid_system_put(world,&system,3));
    CHECK(world_find_grid_system(world,5)==geo_grid_systems_at(&world->grid_store,0));
    CHECK(!grid_systems_rebuild(world,error,sizeof error));
    CHECK(!strcmp(error,"I37: grid-system 5 has an invalid definition"));
    CHECK(app_grid_system_put(world,&system,0));
    CHECK(!grid_systems_rebuild(world,error,sizeof error));
    CHECK(!strcmp(error,"I25a: DIVISION_RANGE source 5 rule 1"));
    system.axis[0].stagger_set=true;
    CHECK(app_grid_system_put(world,&system,3));
    CHECK(!grid_systems_rebuild(world,error,sizeof error));
    CHECK(strstr(error,"相位差為 0")!=NULL);
    system=host_system();system.axis[0].source=GRID_SRC_SERIES;system.axis[0].series_count=2;
    system.axis[0].parameters[0]=(ParameterRef){true,100,200};system.axis[1].source=GRID_SRC_NONE;
    strcpy(g_parameter_error,"retained earlier diagnostic");CHECK(app_grid_system_put(world,&system,0));
    CHECK(!grid_systems_rebuild(world,error,sizeof error));
    CHECK(!strcmp(error,"grid-system 5 u: retained earlier diagnostic"));
    free(world);return 0;
}
static int rejected_cache(void)
{
    World *world=calloc(1,sizeof *world);CHECK(world);GridSystem system=host_system();
    CHECK(app_grid_system_put(world,&system,2));
    SpaceBoundarySurface boundary_value={0},*boundary=&boundary_value;boundary->id=71;boundary->outline.count=4;
    boundary->outline.v[0]=(SurfacePoint2){400,500};boundary->outline.v[1]=(SurfacePoint2){1600,500};
    boundary->outline.v[2]=(SurfacePoint2){1600,1300};boundary->outline.v[3]=(SurfacePoint2){400,1300};
    CHECK(app_boundary_stage(world,boundary));
    CHECK(boundary_keys_initialize(world,71));
    GridBinding binding={0};binding.id=9;binding.boundary_id=71;binding.system_id=5;
    binding.vertex_key=world_find_vertex_keys(world,71)->keys[0][0];
    binding.cell[0]=-2;binding.cell[1]=-3;binding.anchor_num[0]=binding.anchor_num[1]=1;
    binding.anchor_den[0]=2;binding.anchor_den[1]=3;CHECK(geo_grid_bindings_put(&world->grid_store,&binding));
    ReferenceGrid grid={0};grid.id=10;grid.axis[0].start=999;grid.axis[1].start=888;
    grid.lattice_base[0]=111;grid.lattice_base[1]=222;grid.lattice_step[1]=333;grid.lattice_index[1]=444;
    char error[256];CHECK(!grid_binding_cache(world,world_find_grid_binding(world,9),&grid,error,sizeof error));
    CHECK(!strcmp(error,"D1/I37: anchor must have an exact integer-millimetre offset"));
    CHECK(grid.from_binding && grid.binding_id==9 && grid.main_along==2);
    CHECK(grid.axis[0].start==7 && grid.lattice_base[0]==340 && grid.lattice_step[0]==120 && grid.lattice_index[0]==-2);
    CHECK(grid.axis[1].start==888 && grid.lattice_base[1]==222 && grid.lattice_step[1]==333 && grid.lattice_index[1]==444);
    binding.vertex_key=UINT32_MAX;CHECK(geo_grid_bindings_put(&world->grid_store,&binding));ReferenceGrid before=grid;
    CHECK(!grid_binding_cache(world,world_find_grid_binding(world,9),&grid,error,sizeof error));
    CHECK(!strcmp(error,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes"));
    CHECK(!memcmp(&before,&grid,sizeof grid));free(world);return 0;
}
int main(void)
{ int result=first_error();return result?result:rejected_cache(); }
