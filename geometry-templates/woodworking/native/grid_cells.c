/* D10/D19/I23-I25/R23 woodworking application and child-cell policy.
 * H supplies one candidate's value facts; all geometry and arithmetic use K. */
#include "grid_application.h"
#include <stdio.h>
#include <string.h>

static bool wood_grid_cells_bounds(const WoodGridHost *host,GeoRect2 *out)
{if(!host||!host->bounds_valid)return false;*out=host->bounds;return true;}
bool wood_grid_lattice_coord(const WoodGridApplication *g,int axis,int64_t k,GeoCoord *out)
{
    if(!g||!g->from_binding||axis<0||axis>1)return false;
    GeoLattice lattice={g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};
    return geo_lattice_coord(&lattice,k,out);
}
bool wood_grid_lattice_coord_band(const WoodGridApplication *g,int axis,int64_t k,int64_t band,GeoCoord *out)
{
    GeoCoord base,shift;int64_t value;
    if(!wood_grid_lattice_coord(g,axis,k,&base))return false;
    shift=geo_alternating_shift(g->axis[axis].stagger_set,g->axis[axis].stagger,band);
    if(!shift){if(out)*out=base;return true;}
    if(!geo_i64_add(base,shift,&value)||!geo_coord_in_range(value))return false;
    if(out)*out=value;return true;
}
/* Main application validation requests exact finite output, never samples. */
static bool wood_grid_lattice_lines(const WoodGridApplication *g,int axis,GeoCoord lo,GeoCoord hi,
    GeoCoord out[WOOD_GRID_MAX_LINES],size_t *count,char *err,size_t cap)
{
    GeoLattice lattice={g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};
    GeoLatticeLine lines[WOOD_GRID_MAX_LINES];GeoLatticeWindow result={.lines=lines,.capacity=WOOD_GRID_MAX_LINES};
    GeoGridStatus status=geo_lattice_window(&lattice,lo,hi,WOOD_GRID_MAX_LINES,false,&result);
    if(status==GEO_GRID_OK){*count=result.count;for(size_t i=0;i<result.count;++i)out[i]=lines[i].coordinate;return true;}
    if(status==GEO_GRID_INDEX_RANGE){if(err)snprintf(err,cap,"R32: INDEX_RANGE exceeds signed int64");return false;}
    if(status==GEO_GRID_CAPACITY){if(err)snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu lines; limit %u",(unsigned long long)result.total,(unsigned)WOOD_GRID_MAX_LINES);return false;}
    if(err)snprintf(err,cap,"R32: invalid lattice query or D1 coordinate");return false;
}
static bool wood_grid_cell_has_area(const WoodGridHost *host,const GeoRect2 *rect)
{
    for(size_t c=0;c<host->component_count;++c){
        const WoodBoundaryRegion *part=&host->components[c];GeoLoop2View holes[GEO_REGION_MAX_HOLES];
        GeoRegionView region={.outline={part->outline.v,part->outline.count},.holes=holes,.hole_count=part->hole_count};
        for(size_t h=0;h<region.hole_count;++h)holes[h]=(GeoLoop2View){part->holes[h].v,part->holes[h].count};
        GeoRegionSetView domain={&region,1};
        if(geo_region_set_intersects_rect_positive(&domain,rect))return true;
    }
    return false;
}
bool wood_grid_axis_lines(
    const WoodGridApplication *grid,
    const WoodGridHost *placement,
    int axis,
    GeoCoord out[WOOD_GRID_MAX_LINES],
    size_t *out_count,
    char *err,
    size_t err_cap
)
{
    if (grid == NULL || grid->is_subgrid || placement == NULL || out == NULL ||
        out_count == NULL || axis < 0 || axis > 1 ||
        grid->placement_id != placement->id) {
        return false;
    }

    if (grid->from_binding) {
        GeoRect2 bounds;
        if (!wood_grid_cells_bounds(placement,&bounds) ||
            !wood_grid_lattice_lines(grid,axis,axis?bounds.min_v:bounds.min_u,
                axis?bounds.max_v:bounds.max_u,out,out_count,err,err_cap)) return false;
        return true;
    }
    const GeoGridAxisDef *def = &grid->axis[axis];

    *out_count = 0;

    if (def->source == GEO_GRID_SOURCE_NONE) {
        if (err != NULL) {
            snprintf(err, err_cap, "這一軸沒有宣告格線");
        }
        return false;
    }

    GeoRect2 bounds;

    if (!wood_grid_cells_bounds(placement,&bounds)) {
        return false;
    }

    const GeoCoord lo = axis == 0 ? bounds.min_u : bounds.min_v;
    const GeoCoord hi = axis == 0 ? bounds.max_u : bounds.max_v;
    GeoFiniteSequence sequence={.kind=GEO_SEQUENCE_NONE,.coordinates=def->coords,.count=def->count,
        .start=def->start,.step=def->step,.body=def->body,.gap=def->gap,.anchor=def->anchor};
    switch(def->source){
    case GEO_GRID_SOURCE_EXPLICIT:sequence.kind=GEO_SEQUENCE_EXPLICIT;break;
    case GEO_GRID_SOURCE_SERIES:sequence.kind=GEO_SEQUENCE_SERIES;sequence.count=def->series_count;break;
    case GEO_GRID_SOURCE_BODY_GAP:sequence.kind=GEO_SEQUENCE_BODY_GAP;break;
    default:if(err)snprintf(err,err_cap,"這一軸的格線來源尚未支援");return false;
    }
    GeoGridStatus status=geo_finite_sequence(&sequence,lo,hi,out,WOOD_GRID_MAX_LINES,out_count);
    if(status==GEO_GRID_OK)return true;
    if(err){const char *message=NULL;
        if(status==GEO_GRID_BODY_GAP_INVALID)message="面材參數不合法（面材寬 > 0、縫寬非負、起算點須落在承載面範圍內）";
        else if(status==GEO_GRID_CAPACITY)message="面材排法推導出的格線超過單軸上限";
        else if(status==GEO_GRID_ORDER)message="座標必須嚴格遞增";
        else if(status==GEO_GRID_BOUNDS)message="座標要落在承載面外接範圍內";
        if(message)snprintf(err,err_cap,"%s",message);
    }
    return false;
}

bool wood_grid_valid(
    const WoodGridApplication *grid,
    const WoodGridHost *placement
)
{
    if (grid == NULL || placement == NULL ||
        grid->placement_id != placement->id) {
        return false;
    }

    if (grid->from_binding) return !grid->from_system && !grid->is_subgrid &&
        grid->lattice_step[0]>0 && grid->lattice_step[1]>0;
    /* I10: 主支方向須有對應格線來源；u 座標線沿 v，反之亦然。 */
    if (grid->main_along < 0 || grid->main_along > 2 ||
        (grid->main_along == 1 && grid->axis[1].source == GEO_GRID_SOURCE_NONE) ||
        (grid->main_along == 2 && grid->axis[0].source == GEO_GRID_SOURCE_NONE)) {
        return false;
    }

    /* I10：兩軸皆未宣告 → 拒絕（單軸網格合法）。 */
    if (grid->axis[0].source == GEO_GRID_SOURCE_NONE &&
        grid->axis[1].source == GEO_GRID_SOURCE_NONE) {
        return false;
    }

    GeoCoord lines[WOOD_GRID_MAX_LINES];
    size_t n;

    for (int a = 0; a < 2; ++a) {
        if (grid->axis[a].source == GEO_GRID_SOURCE_NONE) {
            continue;
        }

        if (!wood_grid_axis_lines(grid, placement, a,
                             lines, &n, NULL, 0)) {
            return false;
        }
    }

    return true;
}

bool wood_grid_cell_bounds(const WoodGridApplication *grids,size_t count,const WoodGridApplication *grid,
    const WoodGridHost *p,GeoRect2 *out,char *err,size_t cap)
{
    const WoodGridApplication *parent=NULL;
    if (!grid || !grid->is_subgrid || !p || grid->placement_id!=p->id) goto invalid;
    for (size_t i=0;i<count;++i) if (grids[i].id==grid->parent_id) parent=&grids[i];
    if (!parent || parent->is_subgrid || parent->placement_id!=p->id) goto invalid;
    if (grid->lattice_cell!=parent->from_binding) {
        if (err) snprintf(err,cap,"D19/I37: subgrid cell index space must match its parent grid");
        return false;
    }
    GeoRect2 bounds;
    if (!wood_grid_cells_bounds(p,&bounds)) goto invalid;
    GeoCoord ends[2][2];
    for (int axis=0;axis<2;++axis) {
        if (grid->lattice_cell) {
            int64_t k=grid->lattice_cell_index[axis];
            if (k==INT64_MAX || !wood_grid_lattice_coord(parent,axis,k,&ends[axis][0]) ||
                !wood_grid_lattice_coord(parent,axis,k+1,&ends[axis][1]) || ends[axis][0]>=ends[axis][1]) {
                if (err) snprintf(err,cap,"D19/I37: subgrid %u lattice cell endpoint is outside the signed-index or D1 coordinate range",grid->id);
                return false;
            }
            continue;
        }
        GeoCoord lines[WOOD_GRID_MAX_LINES], stops[WOOD_GRID_MAX_LINES+2];
        int refs[WOOD_GRID_MAX_LINES+2]; size_t n=0,m=0;
        GeoCoord lo=axis==0?bounds.min_u:bounds.min_v, hi=axis==0?bounds.max_u:bounds.max_v;
        if (parent->axis[axis].source!=GEO_GRID_SOURCE_NONE &&
            !wood_grid_axis_lines(parent,p,axis,lines,&n,err,cap)) return false;
        stops[m]=lo; refs[m++]=WOOD_GRID_CELL_MIN;
        for (size_t i=0;i<n;++i) if (lines[i]>lo && lines[i]<hi) {
            stops[m]=lines[i]; refs[m++]=(int)i;
        }
        stops[m]=hi; refs[m++]=WOOD_GRID_CELL_MAX;
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
    *out=(GeoRect2){ends[0][0],ends[1][0],ends[0][1],ends[1][1]};
    if (!wood_grid_cell_has_area(p,out)) {
        if (err) snprintf(err,cap,"I25：子格 %u 的父格 %u 所選矩形與有效面沒有正面積交集",grid->id,grid->parent_id);
        return false;
    }
    return true;
invalid:
    if (err) snprintf(err,cap,"I25：子格 %u 需要同一面上存在的主網格作為父格",grid?grid->id:0);
    return false;
}

bool wood_grid_axis_lines_in(const WoodGridApplication *grids,size_t count,const WoodGridApplication *grid,
    const WoodGridHost *p,int axis,GeoCoord out[WOOD_GRID_MAX_LINES],size_t *out_count,char *err,size_t cap)
{
    if (!grid || axis<0 || axis>1 || !out || !out_count) return false;
    if (!grid->is_subgrid) return wood_grid_axis_lines(grid,p,axis,out,out_count,err,cap);
    *out_count=0;
    GeoRect2 cell;
    if (!wood_grid_cell_bounds(grids,count,grid,p,&cell,err,cap)) return false;
    GeoCoord lo=axis==0?cell.min_u:cell.min_v, hi=axis==0?cell.max_u:cell.max_v;
    unsigned n=grid->divisions[axis];
    if (geo_interval_subdivide(lo,hi,n,out,WOOD_GRID_MAX_LINES,out_count)!=GEO_GRID_OK) {
        if (err) snprintf(err,cap,"I25：子格 %u（父格 %u）%c 軸跨度 %lld mm 無法精確分成 %u 等分；等分數須為 1…65",grid->id,grid->parent_id,axis?'v':'u',(long long)(hi-lo),n);
        return false;
    }
    return true;
}

bool wood_grid_line_coord_in(const WoodGridApplication *grids,size_t count,const WoodGridApplication *grid,
    const WoodGridHost *p,int axis,int64_t index,GeoCoord *out,size_t *total,char *err,size_t cap)
{
    GeoCoord coords[WOOD_GRID_MAX_LINES]; size_t n=0;
    if (total) *total=0;
    if (grid && grid->from_binding && !grid->is_subgrid) {
        if (!p || p->id!=grid->placement_id || !wood_grid_lattice_coord(grid,axis,index,out)) {
            if (err) snprintf(err,cap,"D10/I37: lattice grid %u index %lld cannot be evaluated in D1",grid->id,(long long)index);
            return false;
        }
        return true;
    }
    if (!wood_grid_axis_lines_in(grids,count,grid,p,axis,coords,&n,err,cap)) return false;
    if (total) *total=n;
    if (index<0 || (uint64_t)index>=n) {
        if (err) snprintf(err,cap,"I23: 網格 %u %c 軸索引 %lld 超出範圍（本軸共 %u 條）",grid->id,axis?'v':'u',(long long)index,(unsigned)n);
        return false;
    }
    if (out) *out=coords[index];
    return true;
}

/* D10b / I24: band shifts only a staggered lattice line. Index existence stays unstaggered. */
bool wood_grid_anchor_line_coord(const WoodGridApplication *grids,size_t count,const WoodGridApplication *grid,
    const WoodGridHost *p,int axis,int64_t index,
    bool has_band,int64_t band,GeoCoord *out,char *err,size_t cap)
{
    bool staggered;
    if(!grid || axis<0 || axis>1) return false;
    if(grid->is_subgrid || !grid->from_binding){
        if(has_band){ if(err) snprintf(err,cap,"I24: 沒有相位差的格線不能寫 band"); return false; }
        return wood_grid_line_coord_in(grids,count,grid,p,axis,index,out,NULL,err,cap);
    }
    staggered=grid->axis[axis].stagger_set;
    if(staggered!=has_band){
        if(err) snprintf(err,cap,staggered?"I24: 有相位差的格線必須寫 band，不默認第 0 格":"I24: 沒有相位差的格線不能寫 band");
        return false;
    }
    if(!wood_grid_line_coord_in(grids,count,grid,p,axis,index,out,NULL,err,cap)) return false;
    if(!staggered) return true;
    if(!wood_grid_lattice_coord_band(grid,axis,index,band,out)){
        if(err) snprintf(err,cap,"D10b/D1: 錯開後的格線座標超出可表達範圍");
        return false;
    }
    return true;
}

bool wood_grid_valid_in(const WoodGridApplication *grids,size_t count,const WoodGridApplication *grid,
    const WoodGridHost *p,char *err,size_t cap)
{
    if (!grid->is_subgrid) {
        if (wood_grid_valid(grid,p)) return true;
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
        const WoodGridApplication *other=&grids[i];
        if (other->id!=grid->id && other->is_subgrid && other->parent_id==grid->parent_id &&
            other->lattice_cell==grid->lattice_cell &&
            (grid->lattice_cell ? !memcmp(other->lattice_cell_index,grid->lattice_cell_index,sizeof grid->lattice_cell_index) :
                !memcmp(other->cell_ref,grid->cell_ref,sizeof grid->cell_ref))) {
            if (err) snprintf(err,cap,"I25：父格 %u 的這個格子已有子格 %u",grid->parent_id,other->id);
            return false;
        }
    }
    for (int a=0;a<2;++a) {
        GeoCoord coords[WOOD_GRID_MAX_LINES]; size_t n;
        if (!wood_grid_axis_lines_in(grids,count,grid,p,a,coords,&n,err,cap)) return false;
    }
    return true;
}

/* I23/I25: upstream line cardinality is locked while any child survives.
 * The transaction baseline includes geometry before a boundary or split edit. */
bool wood_grid_parent_count_valid(const WoodGridContext *before,const WoodGridApplication *parent,
    const WoodGridHost *p,char *err,size_t cap)
{
    if (!before) return true;
    const WoodGridApplication *old=wood_grid_find(before->state,parent->id);
    if (!old) return true;
    if (old->from_binding!=parent->from_binding) {
        if (err) snprintf(err,cap,"I37: a parent grid cannot change its ordinal/lattice index space");
        return false;
    }
    if (parent->from_binding) return true; /* Visible cardinality is not identity. */
    WoodGridHost old_host;const WoodGridHost *op=before->host(before->user,old->placement_id,&old_host)?&old_host:NULL;
    if (!op || old->is_subgrid) return false;
    for (int a=0;a<2;++a) {
        GeoCoord coords[WOOD_GRID_MAX_LINES]; size_t n=0,on=0;
        if (old->axis[a].source!=GEO_GRID_SOURCE_NONE && !wood_grid_axis_lines(old,op,a,coords,&on,err,cap)) return false;
        if (parent->axis[a].source!=GEO_GRID_SOURCE_NONE && !wood_grid_axis_lines(parent,p,a,coords,&n,err,cap)) return false;
        if (on!=n) {
            if (err) snprintf(err,cap,"I23：父網格 %u 仍有子格，%c 軸線數不可從 %u 改成 %u；請先處理子格與引用",parent->id,a?'v':'u',(unsigned)on,(unsigned)n);
            return false;
        }
    }
    return true;
}

bool wood_grid_world_valid(const WoodGridContext *world,char *err,size_t cap)
{
    for (size_t i=0;i<world->state->count;++i) {
        const WoodGridApplication *g=&world->state->items[i];
        WoodGridHost host;const WoodGridHost *p=world->host(world->user,g->placement_id,&host)?&host:NULL;
        if (!p || !wood_grid_valid_in(world->state->items,world->state->count,g,p,err,cap)) return false;
        if (!g->is_subgrid) {
            bool children=false;
            for (size_t j=0;j<world->state->count;++j) {
                const WoodGridApplication *other=&world->state->items[j];
                if (i!=j && !other->is_subgrid && other->placement_id==g->placement_id) {
                    if (err) snprintf(err,cap,"I10：面 %u 只能有一組主網格",g->placement_id);
                    return false;
                }
                if (other->is_subgrid && other->parent_id==g->id) children=true;
            }
            if (children && !wood_grid_parent_count_valid(world->before,g,p,err,cap)) return false;
        }
    }
    return true;
}

/* R13: test a whole parent/child family against one candidate face. */
bool wood_grid_family_fits(const WoodGridContext *w,const WoodGridApplication *parent,
    const WoodGridHost *p)
{
    WoodGridApplication grids[WOOD_GRID_MAX]; memcpy(grids,w->state->items,w->state->count*sizeof *grids);
    bool children=false;
    for (size_t i=0;i<w->state->count;++i) {
        if (grids[i].id==parent->id || (grids[i].is_subgrid && grids[i].parent_id==parent->id)) {
            grids[i].placement_id=p->id;
            if (grids[i].is_subgrid) children=true;
        }
    }
    for (size_t i=0;i<w->state->count;++i) {
        WoodGridApplication *g=&grids[i];
        if (g->id!=parent->id && !(g->is_subgrid && g->parent_id==parent->id)) continue;
        if (!wood_grid_valid_in(grids,w->state->count,g,p,NULL,0)) return false;
        if (!g->is_subgrid && children && !wood_grid_parent_count_valid(w->before,g,p,NULL,0)) return false;
    }
    return true;
}
