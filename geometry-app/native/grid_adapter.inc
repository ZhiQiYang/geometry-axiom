/* Host-only role metadata follows the K store's stable insertion order.
 * Definitions and bindings have exactly one owner: World.grid_store. */
static size_t app_grid_system_index(const World *world,uint32_t id)
{
    size_t count=geo_grid_systems_count(&world->grid_store);
    for(size_t i=0;i<count;++i)if(geo_grid_systems_at(&world->grid_store,i)->id==id)return i;
    return count;
}
static size_t app_grid_binding_index(const World *world,uint32_t id)
{
    size_t count=geo_grid_bindings_count(&world->grid_store);
    for(size_t i=0;i<count;++i)if(geo_grid_bindings_at(&world->grid_store,i)->id==id)return i;
    return count;
}
static int app_grid_system_main_along(const World *world,uint32_t id)
{
    size_t at=app_grid_system_index(world,id);
    return at<geo_grid_systems_count(&world->grid_store)?world->grid_main_along[at]:0;
}
static bool app_grid_system_main_valid(const GridSystem *system,int main_along)
{
    return main_along>=0 && main_along<=2 &&
        (main_along!=1 || system->axis[1].source) && (main_along!=2 || system->axis[0].source);
}
static bool app_grid_system_put(World *world,const GridSystem *system,int main_along)
{
    size_t at=app_grid_system_index(world,system->id);
    if(!geo_grid_systems_put(&world->grid_store,system))return false;
    world->grid_main_along[at]=main_along;return true;
}
static bool app_grid_system_redeclare(World *world,const GridSystem *system,int main_along,GeoGridStoreError *error)
{
    size_t at=app_grid_system_index(world,system->id);
    if(!geo_grid_systems_redeclare(&world->grid_store,system,error))return false;
    world->grid_main_along[at]=main_along;return true;
}
static bool app_grid_system_remove(World *world,uint32_t id)
{
    size_t count=geo_grid_systems_count(&world->grid_store),at=app_grid_system_index(world,id);
    if(at==count || !geo_grid_systems_remove(&world->grid_store,id))return false;
    memmove(world->grid_main_along+at,world->grid_main_along+at+1,(count-at-1)*sizeof *world->grid_main_along);
    world->grid_main_along[count-1]=0;return true;
}
