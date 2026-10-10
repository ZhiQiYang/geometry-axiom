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
static Coord grid_loop_rect_area2(const PolygonLoop2 *loop, const SurfaceRegion2 *r)
{
    SurfacePoint2 a[POLY_MAX_VERTICES * 4], z[POLY_MAX_VERTICES * 4];
    size_t n=loop->count;
    memcpy(a,loop->v,n*sizeof *a);
    for (int side=0;side<4 && n;++side) {
        int axis=side/2; bool low=(side%2)==0;
        Coord bound=axis==0?(low?r->min_u:r->max_u):(low?r->min_v:r->max_v);
        size_t m=0;
        for (size_t i=0;i<n;++i) {
            SurfacePoint2 p=a[i], q=a[(i+1)%n];
            Coord pc=axis==0?p.u:p.v, qc=axis==0?q.u:q.v;
            bool pin=low?pc>=bound:pc<=bound, qin=low?qc>=bound:qc<=bound;
            if (pin != qin) {
                SurfacePoint2 hit=p;
                if (axis==0) hit.u=bound; else hit.v=bound;
                if (m>=POLY_MAX_VERTICES*4) return 0;
                z[m++]=hit;
            }
            if (qin) {
                if (m>=POLY_MAX_VERTICES*4) return 0;
                z[m++]=q;
            }
        }
        n=m; memcpy(a,z,n*sizeof *a);
    }
    Coord area=0;
    for (size_t i=0;i<n;++i) area+=a[i].u*a[(i+1)%n].v-a[(i+1)%n].u*a[i].v;
    return area<0?-area:area;
}

static bool grid_cell_has_area(const PlacementSurface *p,const SpaceBoundarySurface *b,const SurfaceRegion2 *r)
{
    PolygonLoop2 outline; placement_outline(p,b,&outline);
    Coord area=grid_loop_rect_area2(&outline,r);
    if (b) for (size_t i=0;i<b->hole_count;++i) area-=grid_loop_rect_area2(&b->holes[i],r);
    return area>0;
}

static bool grid_cell_bounds(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,SurfaceRegion2 *out,char *err,size_t cap)
{
    const ReferenceGrid *parent=NULL;
    if (!grid || !grid->is_subgrid || !p || grid->placement_id!=p->id) goto invalid;
    for (size_t i=0;i<count;++i) if (grids[i].id==grid->parent_id) parent=&grids[i];
    if (!parent || parent->is_subgrid || parent->placement_id!=p->id) goto invalid;
    if (grid->lattice_cell!=parent->from_binding) {
        if (err) snprintf(err,cap,"D19/I37: subgrid cell index space must match its parent grid");
        return false;
    }
    SurfaceRegion2 bounds;
    if (!placement_local_bounds(p,b,&bounds)) goto invalid;
    Coord ends[2][2];
    for (int axis=0;axis<2;++axis) {
        if (grid->lattice_cell) {
            int64_t k=grid->lattice_cell_index[axis];
            if (k==INT64_MAX || !grid_lattice_coord(parent,axis,k,&ends[axis][0]) ||
                !grid_lattice_coord(parent,axis,k+1,&ends[axis][1]) || ends[axis][0]>=ends[axis][1]) {
                if (err) snprintf(err,cap,"D19/I37: subgrid %u lattice cell endpoint is outside the signed-index or D1 coordinate range",grid->id);
                return false;
            }
            continue;
        }
        Coord lines[GRID_MAX_LINES], stops[GRID_MAX_LINES+2];
        int refs[GRID_MAX_LINES+2]; size_t n=0,m=0;
        Coord lo=axis==0?bounds.min_u:bounds.min_v, hi=axis==0?bounds.max_u:bounds.max_v;
        if (parent->axis[axis].source!=GRID_SRC_NONE &&
            !grid_axis_lines(parent,p,b,axis,lines,&n,err,cap)) return false;
        stops[m]=lo; refs[m++]=GRID_CELL_MIN;
        for (size_t i=0;i<n;++i) if (lines[i]>lo && lines[i]<hi) {
            stops[m]=lines[i]; refs[m++]=(int)i;
        }
        stops[m]=hi; refs[m++]=GRID_CELL_MAX;
        bool found=false;
        for (size_t i=0;i+1<m;++i) {
            if (refs[i]==grid->cell_ref[axis][0] && refs[i+1]==grid->cell_ref[axis][1] && stops[i]<stops[i+1]) {
                ends[axis][0]=stops[i]; ends[axis][1]=stops[i+1]; found=true; break;
            }
        }
        if (!found) {
            if (err) snprintf(err,cap,"I25：子格 %u 的父格 %u %c 軸兩界須存在、採標準參照且彼此相鄰",grid->id,grid->parent_id,axis?'v':'u');
            return false;
        }
    }
    *out=(SurfaceRegion2){ends[0][0],ends[1][0],ends[0][1],ends[1][1]};
    if (!grid_cell_has_area(p,b,out)) {
        if (err) snprintf(err,cap,"I25：子格 %u 的父格 %u 所選矩形與有效面沒有正面積交集",grid->id,grid->parent_id);
        return false;
    }
    return true;
invalid:
    if (err) snprintf(err,cap,"I25：子格 %u 需要同一面上存在的主網格作為父格",grid?grid->id:0);
    return false;
}

static bool grid_axis_lines_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,Coord out[GRID_MAX_LINES],size_t *out_count,char *err,size_t cap)
{
    if (!grid || axis<0 || axis>1 || !out || !out_count) return false;
    if (!grid->is_subgrid) return grid_axis_lines(grid,p,b,axis,out,out_count,err,cap);
    *out_count=0;
    SurfaceRegion2 cell;
    if (!grid_cell_bounds(grids,count,grid,p,b,&cell,err,cap)) return false;
    Coord lo=axis==0?cell.min_u:cell.min_v, hi=axis==0?cell.max_u:cell.max_v;
    unsigned n=grid->divisions[axis];
    if (n<1 || n>GRID_MAX_LINES+1 || (hi-lo)%n) {
        if (err) snprintf(err,cap,"I25：子格 %u（父格 %u）%c 軸跨度 %lld mm 無法精確分成 %u 等分；等分數須為 1…65",grid->id,grid->parent_id,axis?'v':'u',(long long)(hi-lo),n);
        return false;
    }
    Coord step=(hi-lo)/n;
    for (unsigned k=1;k<n;++k) out[(*out_count)++]=lo+k*step;
    return true;
}

static bool grid_line_coord_in(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,int64_t index,Coord *out,size_t *total,char *err,size_t cap)
{
    Coord coords[GRID_MAX_LINES]; size_t n=0;
    if (total) *total=0;
    if (grid && grid->from_binding && !grid->is_subgrid) {
        if (!p || p->id!=grid->placement_id || !grid_lattice_coord(grid,axis,index,out)) {
            if (err) snprintf(err,cap,"D10/I37: lattice grid %u index %lld cannot be evaluated in D1",grid->id,(long long)index);
            return false;
        }
        return true;
    }
    if (!grid_axis_lines_in(grids,count,grid,p,b,axis,coords,&n,err,cap)) return false;
    if (total) *total=n;
    if (index<0 || (uint64_t)index>=n) {
        if (err) snprintf(err,cap,"I23: 網格 %u %c 軸索引 %lld 超出範圍（本軸共 %u 條）",grid->id,axis?'v':'u',(long long)index,(unsigned)n);
        return false;
    }
    if (out) *out=coords[index];
    return true;
}

/* D10b / I24: band shifts only a staggered lattice line. Index existence stays unstaggered. */
static bool grid_anchor_line_coord(const ReferenceGrid *grids,size_t count,const ReferenceGrid *grid,
    const PlacementSurface *p,const SpaceBoundarySurface *b,int axis,int64_t index,
    bool has_band,int64_t band,Coord *out,char *err,size_t cap)
{
    bool staggered;
    if(!grid || axis<0 || axis>1) return false;
    if(grid->is_subgrid || !grid->from_binding){
        if(has_band){ if(err) snprintf(err,cap,"I24: 沒有相位差的格線不能寫 band"); return false; }
        return grid_line_coord_in(grids,count,grid,p,b,axis,index,out,NULL,err,cap);
    }
    staggered=grid->axis[axis].stagger_set;
    if(staggered!=has_band){
        if(err) snprintf(err,cap,staggered?"I24: 有相位差的格線必須寫 band，不默認第 0 格":"I24: 沒有相位差的格線不能寫 band");
        return false;
    }
    if(!grid_line_coord_in(grids,count,grid,p,b,axis,index,out,NULL,err,cap)) return false;
    if(!staggered) return true;
    if(!grid_lattice_coord_band(grid,axis,index,band,out)){
        if(err) snprintf(err,cap,"D10b/D1: 錯開後的格線座標超出可表達範圍");
        return false;
    }
    return true;
}

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
{
    if (!grid->is_subgrid) {
        if (grid_is_valid(grid,p,b)) return true;
        if (err) snprintf(err,cap,"I10：主網格 %u 的來源或主支方向不合法",grid->id);
        return false;
    }
    if (grid->main_along || (grid->divisions[0]==1 && grid->divisions[1]==1)) {
        if (err) snprintf(err,cap,"I25：子格 %u 至少一軸須大於 1 等分；子格不設定主支方向",grid->id);
        return false;
    }
    for (size_t i=0;i<count;++i) if (grids[i].id==grid->parent_id && !grids[i].is_subgrid &&
        (grids[i].axis[0].stagger_set || grids[i].axis[1].stagger_set)) {
        if (err) snprintf(err,cap,"I24：有相位差的主格 %u 不能建立子網格",grid->parent_id);
        return false;
    }
    for (size_t i=0;i<count;++i) {
        const ReferenceGrid *other=&grids[i];
        if (other->id!=grid->id && other->is_subgrid && other->parent_id==grid->parent_id &&
            other->lattice_cell==grid->lattice_cell &&
            (grid->lattice_cell ? !memcmp(other->lattice_cell_index,grid->lattice_cell_index,sizeof grid->lattice_cell_index) :
                !memcmp(other->cell_ref,grid->cell_ref,sizeof grid->cell_ref))) {
            if (err) snprintf(err,cap,"I25：父格 %u 的這個格子已有子格 %u",grid->parent_id,other->id);
            return false;
        }
    }
    for (int a=0;a<2;++a) {
        Coord coords[GRID_MAX_LINES]; size_t n;
        if (!grid_axis_lines_in(grids,count,grid,p,b,a,coords,&n,err,cap)) return false;
    }
    return true;
}

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
