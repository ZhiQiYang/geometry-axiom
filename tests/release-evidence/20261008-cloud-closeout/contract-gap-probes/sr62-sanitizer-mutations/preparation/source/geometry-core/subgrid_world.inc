/* I23/I25: upstream line cardinality is locked while any child survives.
 * The transaction baseline includes geometry before a boundary or split edit. */
static bool subgrid_parent_count_valid(const World *before,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b,char *err,size_t cap)
{
    if (!before) return true;
    const ReferenceGrid *old=world_find_grid(before,parent->id);
    if (!old) return true;
    if (old->from_binding!=parent->from_binding) {
        if (err) snprintf(err,cap,"I37: a parent grid cannot change its ordinal/lattice index space");
        return false;
    }
    if (parent->from_binding) return true; /* Visible cardinality is not identity. */
    const PlacementSurface *op=world_find_placement(before,old->placement_id);
    if (!op || old->is_subgrid) return false;
    const SpaceBoundarySurface *ob=world_placement_boundary(before,op);
    for (int a=0;a<2;++a) {
        Coord coords[GRID_MAX_LINES]; size_t n=0,on=0;
        if (old->axis[a].source!=GRID_SRC_NONE && !grid_axis_lines(old,op,ob,a,coords,&on,err,cap)) return false;
        if (parent->axis[a].source!=GRID_SRC_NONE && !grid_axis_lines(parent,p,b,a,coords,&n,err,cap)) return false;
        if (on!=n) {
            if (err) snprintf(err,cap,"I23：父網格 %u 仍有子格，%c 軸線數不可從 %u 改成 %u；請先處理子格與引用",parent->id,a?'v':'u',(unsigned)on,(unsigned)n);
            return false;
        }
    }
    return true;
}

static bool subgrid_world_valid(const World *world,char *err,size_t cap)
{
    for (size_t i=0;i<world->grid_count;++i) {
        const ReferenceGrid *g=&world->grids[i];
        const PlacementSurface *p=world_find_placement(world,g->placement_id);
        if (!p || !grid_is_valid_in(world->grids,world->grid_count,g,p,world_placement_boundary(world,p),err,cap)) return false;
        if (!g->is_subgrid) {
            bool children=false;
            for (size_t j=0;j<world->grid_count;++j) {
                const ReferenceGrid *other=&world->grids[j];
                if (i!=j && !other->is_subgrid && other->placement_id==g->placement_id) {
                    if (err) snprintf(err,cap,"I10：面 %u 只能有一組主網格",g->placement_id);
                    return false;
                }
                if (other->is_subgrid && other->parent_id==g->id) children=true;
            }
            if (children && !subgrid_parent_count_valid(g_subgrid_before,g,p,world_placement_boundary(world,p),err,cap)) return false;
        }
    }
    return true;
}

/* R13: test a whole parent/child family against one candidate face. */
static bool subgrid_family_fits(const World *w,const ReferenceGrid *parent,
    const PlacementSurface *p,const SpaceBoundarySurface *b)
{
    ReferenceGrid grids[WORLD_MAX_GRIDS]; memcpy(grids,w->grids,w->grid_count*sizeof *grids);
    bool children=false;
    for (size_t i=0;i<w->grid_count;++i) {
        if (grids[i].id==parent->id || (grids[i].is_subgrid && grids[i].parent_id==parent->id)) {
            grids[i].placement_id=p->id;
            if (grids[i].is_subgrid) children=true;
        }
    }
    for (size_t i=0;i<w->grid_count;++i) {
        ReferenceGrid *g=&grids[i];
        if (g->id!=parent->id && !(g->is_subgrid && g->parent_id==parent->id)) continue;
        if (!grid_is_valid_in(grids,w->grid_count,g,p,b,NULL,0)) return false;
        if (!g->is_subgrid && children && !subgrid_parent_count_valid(g_subgrid_before,g,p,b,NULL,0)) return false;
    }
    return true;
}
