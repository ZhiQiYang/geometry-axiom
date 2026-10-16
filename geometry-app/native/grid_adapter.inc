/* H source codec wrappers; W owns source-id-keyed role settings. */
static size_t app_grid_system_index(const World *world,uint32_t id)
{
    size_t count=geo_grid_systems_count(&world->geo.grid_store);
    for(size_t i=0;i<count;++i)if(geo_grid_systems_at(&world->geo.grid_store,i)->id==id)return i;
    return count;
}
static size_t app_grid_binding_index(const World *world,uint32_t id)
{
    size_t count=geo_grid_bindings_count(&world->geo.grid_store);
    for(size_t i=0;i<count;++i)if(geo_grid_bindings_at(&world->geo.grid_store,i)->id==id)return i;
    return count;
}
static int app_grid_system_main_along(const World *world,uint32_t id)
{return wood_grid_source_main_along(&world->wood.grid_applications,id);}

static bool app_grid_system_main_valid(const GridSystem *system,int main_along)
{return wood_grid_source_main_valid(system,main_along);}

static bool app_grid_system_put(World *world,const GridSystem *system,int main_along)
{WoodGridContext c={0};c.state=&world->wood.grid_applications;c.sources=&world->geo.grid_store;return wood_grid_source_put(&c,system,main_along);}

static bool app_grid_system_redeclare(World *world,const GridSystem *system,int main_along,GeoGridStoreError *error)
{WoodGridContext c={0};c.state=&world->wood.grid_applications;c.sources=&world->geo.grid_store;return wood_grid_source_redeclare(&c,system,main_along,error);}

static bool app_grid_system_remove(World *world,uint32_t id)
{WoodGridContext c={0};c.state=&world->wood.grid_applications;c.sources=&world->geo.grid_store;return wood_grid_source_remove(&c,id);}
