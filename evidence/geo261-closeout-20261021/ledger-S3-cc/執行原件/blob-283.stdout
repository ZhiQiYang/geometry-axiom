/* D19/I25/R23: derived, single-level cells. This module stores no geometry. */
#define GRID_CELL_MIN (-1)
#define GRID_CELL_MAX (-2)

static void grid_cell_ref_format(int ref, char *out, size_t cap)
{
    if (ref == GRID_CELL_MIN) snprintf(out,cap,"min");
    else if (ref == GRID_CELL_MAX) snprintf(out,cap,"max");
    else snprintf(out,cap,"line:%d",ref);
}

/* Clip an orthogonal loop against a rectangle and take twice its area.
 * Integer intersections stay exact. The shoelace sum also handles disconnected
 * pieces joined by a zero-area clip-boundary walk. */




static bool grid_cell_bounds(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,SurfaceRegion2 *out,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);return wood_grid_cell_bounds(grids,count,grid,p?&host:NULL,out,err,cap);}


static bool grid_axis_lines_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,Coord out[GRID_MAX_LINES],size_t *out_count,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);return wood_grid_axis_lines_in(grids,count,grid,p?&host:NULL,axis,out,out_count,err,cap);}


static bool grid_line_coord_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,int64_t index,Coord *out,size_t *total,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);return wood_grid_line_coord_in(grids,count,grid,p?&host:NULL,axis,index,out,total,err,cap);}


/* D10b / I24: band shifts only a staggered lattice line. Index existence stays unstaggered. */
static bool grid_anchor_line_coord(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,int64_t index,
    bool has_band,int64_t band,Coord *out,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);return wood_grid_anchor_line_coord(grids,count,grid,p?&host:NULL,axis,index,has_band,band,out,err,cap);}


/* Display/query sampling preserves the source index. A sampled pair is never a
 * cell definition; lattice-cell evaluation above always uses consecutive k. */
static bool grid_sample_indices_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,
    int64_t indices[GRID_MAX_LINES],Coord coords[GRID_MAX_LINES],size_t *out_count)
{
    if (!out_count) return false;
    *out_count=0;
    if (!grid || !p || grid->placement_id!=p->id || axis<0 || axis>1 || !indices || !coords) return false;
    if (grid->from_binding && !grid->is_subgrid) {
        SurfaceRegion2 bounds; GridQueryAxis result;
        if (!placement_local_bounds(p,b,&bounds) ||
            !grid_lattice_window(grid,axis,axis?bounds.min_v:bounds.min_u,
                axis?bounds.max_v:bounds.max_u,GRID_MAX_LINES,true,&result,NULL,0)) return false;
        for (size_t i=0;i<result.count;++i) {
            indices[i]=result.lines[i].index; coords[i]=result.lines[i].coordinate;
        }
        *out_count=result.count;
        return true;
    }
    if (!grid_axis_lines_in(grids,count,grid,p,b,axis,coords,out_count,NULL,0)) return false;
    for (size_t i=0;i<*out_count;++i) indices[i]=(int64_t)i;
    return true;
}

static bool grid_is_valid_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,char *err,size_t cap)
{WoodGridHost host;app_grid_host_value(p,b,&host);return wood_grid_valid_in(grids,count,grid,p?&host:NULL,err,cap);}


static size_t grid_line_segments(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,int64_t index,SurfaceSegment2 *out,size_t cap)
{
    Coord coord; SurfaceRegion2 cell;
    if (!grid_line_coord_in(grids,count,grid,p,b,axis,index,&coord,NULL,NULL,0)) return 0;
    if (grid->is_subgrid && !grid_cell_bounds(grids,count,grid,p,b,&cell,NULL,0)) return 0;
    GuideLine line={.placement_id=p->id,.direction=axis==0?GUIDE_ALONG_V:GUIDE_ALONG_U,.offset=coord};
    SurfaceSegment2 segments[GUIDE_MAX_SEGMENTS];
    size_t n=guide_line_get_local_segments(p,b,&line,segments,GUIDE_MAX_SEGMENTS), written=0;
    for (size_t i=0;i<n && written<cap;++i) {
        SurfaceSegment2 s=segments[i];
        if (grid->is_subgrid) {
            if (axis==0) { s.start.v=coord_max(s.start.v,cell.min_v); s.end.v=coord_min(s.end.v,cell.max_v); }
            else { s.start.u=coord_max(s.start.u,cell.min_u); s.end.u=coord_min(s.end.u,cell.max_u); }
        }
        if (axis==0?s.start.v<s.end.v:s.start.u<s.end.u) out[written++]=s;
    }
    return written;
}
