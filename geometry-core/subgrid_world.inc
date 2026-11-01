/* I23/I25: upstream line cardinality is locked while any child survives.
 * The transaction baseline includes geometry before a boundary or split edit. */
static bool subgrid_parent_count_valid(const World *before,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);WoodGridContext old;if(before)old=app_grid_context(before);return wood_grid_parent_count_valid(before?&old:NULL,parent,p?&host:NULL,err,cap);}


static bool subgrid_world_valid(const World *world,char *err,size_t cap)
{WoodGridContext c=app_grid_context(world),before;if(g_subgrid_before){before=app_grid_context(g_subgrid_before);c.before=&before;}return wood_grid_world_valid(&c,err,cap);}

/* H classifies replacement/replay; W owns the one-axis submission policy.
 * The retained candidate supplies the same sealed ordered facts at confirm. */
static bool grid_stagger_submission_valid(const World *world,char *err,size_t cap)
{
    if(g_parsing_scene_file||!g_subgrid_before)return true;
    const AppWorldCandidate *candidate=g_active_app_candidate;
    const WoodGridStaggerFact *facts=NULL;size_t count=0;
    if(candidate&&world==&candidate->after){facts=candidate->stagger_facts;count=candidate->operation.stagger_count;}
    return wood_grid_stagger_commit_valid(&world->geo.grid_store,&g_subgrid_before->geo.grid_store,
        facts,count,err,cap);
}


/* R13: test a whole parent/child family against one candidate face. */
static bool subgrid_family_fits(const World *w,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b)
{WoodGridHost host;app_grid_host_value(p,b,&host);WoodGridContext c=app_grid_context(w),before;if(g_subgrid_before){before=app_grid_context(g_subgrid_before);c.before=&before;}return wood_grid_family_fits(&c,parent,p?&host:NULL);}
