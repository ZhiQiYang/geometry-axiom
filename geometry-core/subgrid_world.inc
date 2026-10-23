/* I23/I25: upstream line cardinality is locked while any child survives.
 * The transaction baseline includes geometry before a boundary or split edit. */
static bool subgrid_parent_count_valid(const World *before,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);WoodGridContext old;if(before)old=app_grid_context(before);return wood_grid_parent_count_valid(before?&old:NULL,parent,p?&host:NULL,err,cap);}


static bool subgrid_world_valid(const World *world,char *err,size_t cap)
{WoodGridContext c=app_grid_context(world),before;if(g_subgrid_before){before=app_grid_context(g_subgrid_before);c.before=&before;}return wood_grid_world_valid(&c,err,cap);}


/* R13: test a whole parent/child family against one candidate face. */
static bool subgrid_family_fits(const World *w,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b)
{WoodGridHost host;app_grid_host_value(p,b,&host);WoodGridContext c=app_grid_context(w),before;if(g_subgrid_before){before=app_grid_context(g_subgrid_before);c.before=&before;}return wood_grid_family_fits(&c,parent,p?&host:NULL);}
