/* D19a/R32: finite, read-only source-rule queries. Cell geometry has exactly
 * one evaluator, grid_rule_cell; this module only selects cells and clips its
 * internal lines through the existing guide-line clipper. */
#define GRID_RULE_QUERY_MAX_CELLS 1024
#define GRID_RULE_QUERY_MAX_SEGMENTS 4096
#define GRID_RULE_QUERY_MAX_CELL_LINES (2 * GRID_MAX_LINES)

typedef struct {
    int axis;
    uint32_t inner_index;
    Coord coordinate;
    size_t segment_first,segment_count;
} GridRuleQueryLine;

typedef struct {
    uint32_t system_id,rule_key;
    int64_t cell[2];
    SurfaceRegion2 bounds;
    size_t line_first,line_count;
} GridRuleQueryCell;

typedef struct {
    bool complete,has_placed_ref,segments_counted;
    uint32_t grid_id;
    uint64_t required_cells,required_segments,stride;
    size_t cell_count,line_count,segment_count;
    GridRuleQueryCell *cells;
    GridRuleQueryLine *lines;
    SurfaceSegment2 *segments;
} GridRuleQueryResult;

static void grid_rule_query_free(GridRuleQueryResult *q)
{
    if (!q) return;
    free(q->cells); free(q->lines); free(q->segments);
    q->cells=NULL; q->lines=NULL; q->segments=NULL;
    q->cell_count=q->line_count=q->segment_count=0;
}

static bool grid_rule_query_error(char *err,size_t cap,const char *message)
{
    if (err && cap) snprintf(err,cap,"%s",message);
    return false;
}

static bool grid_rule_query_sub(int64_t a,int64_t b,int64_t *out)
{
    if ((b>0 && a<INT64_MIN+b)||(b<0 && a>INT64_MAX+b)) return false;
    *out=a-b; return true;
}

/* Unsigned distance is needed even when a signed interval crosses zero. */
static bool grid_rule_query_span(int64_t first,int64_t last,uint64_t *count)
{
    if (first>last) { *count=0; return true; }
    uint64_t distance=(uint64_t)last-(uint64_t)first;
    if (distance==UINT64_MAX) return false;
    *count=distance+1; return true;
}

static bool grid_rule_query_index_at(int64_t first,uint64_t offset,int64_t *out)
{
    uint64_t room=(uint64_t)INT64_MAX-(uint64_t)first;
    if (offset>room) return false;
    if (first>=0) { *out=first+(int64_t)offset; return true; }
    uint64_t to_zero=UINT64_C(0)-(uint64_t)first;
    if (offset>=to_zero) *out=(int64_t)(offset-to_zero);
    else {
        uint64_t magnitude=to_zero-offset;
        *out=magnitude==(uint64_t)INT64_MAX+1?INT64_MIN:-(int64_t)magnitude;
    }
    return true;
}

/* A query cell may have no visible segments. Its definition and all internal
 * line identities still exist, so zero segments never invalidate the cell. */
static bool grid_rule_query_visit(const World *w,const char *kind,uint32_t id,
    uint32_t key,const int64_t cell[2],const Coord *rect,bool write,
    GridRuleQueryResult *q,uint64_t *segment_total,char *err,size_t cap)
{
    ReferenceGrid derived={0};
    const GridSystem *source=NULL; const GridSubdivisionRule *rule=NULL;
    const PlacementSurface *placement=NULL; const SpaceBoundarySurface *boundary=NULL;
    SurfaceRegion2 bounds;
    if (!grid_rule_cell(w,kind,id,key,cell,&derived,&source,&rule,&bounds,
                       &placement,&boundary,err,cap)) return false;
    if (!source || !rule || !rule->divisions[0] || !rule->divisions[1] ||
        rule->divisions[0]>GRID_MAX_LINES+1 || rule->divisions[1]>GRID_MAX_LINES+1)
        return grid_rule_query_error(err,cap,"R32: invalid rule query definition");
    /* Binding queries use boundary-local coordinates, like grid_query. This
     * adapter is stack-local and never becomes a placement in World. */
    PlacementSurface local={0};
    if (!placement && boundary) placement=&local;
    GridRuleQueryCell *result=NULL;
    if (write) {
        if (q->cell_count>=GRID_RULE_QUERY_MAX_CELLS)
            return grid_rule_query_error(err,cap,"R32: QUERY_CAPACITY exceeds cell budget");
        result=&q->cells[q->cell_count++];
        result->system_id=source->id; result->rule_key=rule->key;
        memcpy(result->cell,cell,sizeof result->cell); result->bounds=bounds;
        result->line_first=q->line_count;
    }
    for (int axis=0;axis<2;++axis) {
        Coord lo=axis?bounds.min_v:bounds.min_u,hi=axis?bounds.max_v:bounds.max_u;
        Coord step=(hi-lo)/(Coord)rule->divisions[axis];
        Coord clip_lo=axis?bounds.min_u:bounds.min_v;
        Coord clip_hi=axis?bounds.max_u:bounds.max_v;
        if (rect) {
            clip_lo=coord_max(clip_lo,rect[1-axis]);
            clip_hi=coord_min(clip_hi,rect[3-axis]);
        }
        for (uint32_t inner=0;inner+1<rule->divisions[axis];++inner) {
            Coord coordinate=lo+(Coord)(inner+1)*step;
            SurfaceSegment2 clips[POLY_MAX_VERTICES]; size_t count=0;
            if (clip_lo<clip_hi && (!rect || (coordinate>=rect[axis] && coordinate<=rect[axis+2]))) {
                if (placement) {
                    GuideLine guide={0}; guide.placement_id=placement->id;
                    guide.direction=axis?GUIDE_ALONG_U:GUIDE_ALONG_V; guide.offset=coordinate;
                    count=guide_line_get_local_segments(placement,boundary,&guide,clips,POLY_MAX_VERTICES);
                } else {
                    clips[0]=axis?(SurfaceSegment2){ {clip_lo,coordinate},{clip_hi,coordinate} }
                        :(SurfaceSegment2){ {coordinate,clip_lo},{coordinate,clip_hi} };
                    count=1;
                }
            }
            GridRuleQueryLine *line=NULL;
            if (write) {
                if (q->line_count>=GRID_RULE_QUERY_MAX_CELLS*GRID_RULE_QUERY_MAX_CELL_LINES)
                    return grid_rule_query_error(err,cap,"R32: QUERY_CAPACITY exceeds line budget");
                line=&q->lines[q->line_count++];
                line->axis=axis; line->inner_index=inner; line->coordinate=coordinate;
                line->segment_first=q->segment_count;
                ++result->line_count;
            }
            for (size_t i=0;i<count;++i) {
                SurfaceSegment2 segment=clips[i];
                Coord *start=axis?&segment.start.u:&segment.start.v;
                Coord *end=axis?&segment.end.u:&segment.end.v;
                *start=coord_max(*start,clip_lo); *end=coord_min(*end,clip_hi);
                if (*start>=*end) continue;
                if (*segment_total==UINT64_MAX)
                    return grid_rule_query_error(err,cap,"R32: QUERY_OVERFLOW counting clipped segments");
                ++*segment_total;
                if (write) {
                    if (q->segment_count>=GRID_RULE_QUERY_MAX_SEGMENTS)
                        return grid_rule_query_error(err,cap,"R32: QUERY_CAPACITY exceeds segment budget");
                    q->segments[q->segment_count++]=segment; ++line->segment_count;
                }
            }
        }
    }
    return true;
}

static bool grid_rule_query_allocate(GridRuleQueryResult *q,size_t cells,char *err,size_t cap)
{
    if (!cells) return true;
    q->cells=calloc(cells,sizeof *q->cells);
    q->lines=calloc(cells*GRID_RULE_QUERY_MAX_CELL_LINES,sizeof *q->lines);
    if (q->required_segments) q->segments=calloc((size_t)q->required_segments,sizeof *q->segments);
    if (!q->cells || !q->lines || (q->required_segments && !q->segments)) {
        grid_rule_query_free(q);
        return grid_rule_query_error(err,cap,"R32: query memory allocation failed");
    }
    return true;
}

static bool grid_rule_query_cell(const World *w,const char *kind,uint32_t id,
    uint32_t key,const int64_t cell[2],GridRuleQueryResult *out,char *err,size_t cap)
{
    memset(out,0,sizeof *out); out->stride=1; out->required_cells=1;
    out->has_placed_ref=kind && !strcmp(kind,"grid"); out->grid_id=id;
    if (!grid_rule_query_visit(w,kind,id,key,cell,NULL,false,out,&out->required_segments,err,cap)) return false;
    out->segments_counted=true;
    if (out->required_segments>GRID_RULE_QUERY_MAX_SEGMENTS)
        return grid_rule_query_error(err,cap,"R32: QUERY_CAPACITY exceeds segment budget");
    if (!grid_rule_query_allocate(out,1,err,cap)) return false;
    uint64_t written=0;
    if (!grid_rule_query_visit(w,kind,id,key,cell,NULL,true,out,&written,err,cap)) {
        grid_rule_query_free(out); return false;
    }
    out->complete=true; return true;
}

static bool grid_rule_query_enumerate(const World *w,const char *kind,uint32_t id,
    uint32_t key,const Coord rect[4],const int64_t first[2],const uint64_t counts[2],
    bool write,GridRuleQueryResult *q,uint64_t *segments,char *err,size_t cap)
{
    *segments=0;
    for (uint64_t ordinal=0;ordinal<q->required_cells;) {
        int64_t cell[2];
        if (!grid_rule_query_index_at(first[0],ordinal%counts[0],&cell[0]) ||
            !grid_rule_query_index_at(first[1],ordinal/counts[0],&cell[1]))
            return grid_rule_query_error(err,cap,"R32: INDEX_RANGE exceeds signed int64");
        if (!grid_rule_query_visit(w,kind,id,key,cell,rect,write,q,segments,err,cap)) return false;
        if (q->required_cells-1-ordinal<q->stride) break;
        ordinal+=q->stride;
    }
    return true;
}

static bool grid_rule_query_rect(const World *w,const char *kind,uint32_t id,
    uint32_t key,const Coord rect[4],size_t limit,bool sample,
    GridRuleQueryResult *out,char *err,size_t cap)
{
    memset(out,0,sizeof *out); out->stride=1;
    out->has_placed_ref=kind && !strcmp(kind,"grid"); out->grid_id=id;
    if (!rect || !limit || limit>GRID_RULE_QUERY_MAX_CELLS || rect[0]>=rect[2] || rect[1]>=rect[3])
        return grid_rule_query_error(err,cap,"R32: rule query needs a positive rectangle and limit 1..1024");
    for (int a=0;a<4;++a) if (!coord_in_range(rect[a]))
        return grid_rule_query_error(err,cap,"R32: rule query rectangle exceeds D1");
    ReferenceGrid derived={0}; const GridSystem *source=NULL;
    const PlacementSurface *placement=NULL; const SpaceBoundarySurface *boundary=NULL;
    if (!grid_rule_target(w,kind,id,&derived,&source,&placement,&boundary,err,cap)) return false;
    const GridSubdivisionRule *rule=source?grid_rule_find(source,key):NULL;
    if (!rule) return grid_rule_query_error(err,cap,"R32: rule query needs an existing source rule");
    int64_t first[2],last[2]; uint64_t counts[2];
    for (int a=0;a<2;++a) {
        int64_t low_delta,high_delta,step=derived.lattice_step[a];
        if (step<=0 || !grid_rule_query_sub(rect[a],derived.lattice_base[a],&low_delta) ||
            !grid_rule_query_sub(rect[a+2],derived.lattice_base[a],&high_delta))
            return grid_rule_query_error(err,cap,"R32: QUERY_OVERFLOW computing cell range");
        low_delta=grid_floor_div(low_delta,step);
        high_delta=grid_ceil_div(high_delta,step);
        if (!grid_i64_add(high_delta,-1,&high_delta) ||
            !grid_i64_add(derived.lattice_index[a],low_delta,&first[a]) ||
            !grid_i64_add(derived.lattice_index[a],high_delta,&last[a]) || last[a]==INT64_MAX)
            return grid_rule_query_error(err,cap,"R32: INDEX_RANGE cell upper line exceeds signed int64");
        if (!grid_rule_query_span(first[a],last[a],&counts[a]))
            return grid_rule_query_error(err,cap,"R32: QUERY_OVERFLOW counting axis cells");
    }
    if (!rule->all_cells) {
        if (rule->cell[0]<first[0] || rule->cell[0]>last[0] ||
            rule->cell[1]<first[1] || rule->cell[1]>last[1]) {
            out->complete=true; return true;
        }
        memcpy(first,rule->cell,sizeof first); counts[0]=counts[1]=1;
    }
    if (counts[1] && counts[0]>UINT64_MAX/counts[1])
        return grid_rule_query_error(err,cap,"R32: QUERY_OVERFLOW counting rectangle cells");
    out->required_cells=counts[0]*counts[1];
    if (!sample && out->required_cells>limit) {
        if (err && cap) snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu cells; limit %zu",
            (unsigned long long)out->required_cells,limit);
        return false;
    }
    if (!out->required_cells) { out->complete=true; return true; }
    out->stride=sample?(out->required_cells-1)/limit+1:1;
    /* Segment budget applies to whole selected cells. If sampling needs a
     * wider stride, restart its preflight; never truncate a cell or its refs. */
    for (;;) {
        if (!grid_rule_query_enumerate(w,kind,id,key,rect,first,counts,false,out,
                                      &out->required_segments,err,cap)) return false;
        out->segments_counted=true;
        if (out->required_segments<=GRID_RULE_QUERY_MAX_SEGMENTS) break;
        if (!sample) {
            if (err && cap) snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu segments; limit %u",
                (unsigned long long)out->required_segments,(unsigned)GRID_RULE_QUERY_MAX_SEGMENTS);
            return false;
        }
        uint64_t factor=(out->required_segments-1)/GRID_RULE_QUERY_MAX_SEGMENTS+1;
        if (out->stride>UINT64_MAX/factor)
            return grid_rule_query_error(err,cap,"R32: QUERY_OVERFLOW computing sample stride");
        out->stride*=factor;
    }
    size_t selected=(size_t)((out->required_cells-1)/out->stride+1);
    if (!grid_rule_query_allocate(out,selected,err,cap)) return false;
    uint64_t written=0;
    if (!grid_rule_query_enumerate(w,kind,id,key,rect,first,counts,true,out,&written,err,cap)) {
        grid_rule_query_free(out); return false;
    }
    out->complete=out->stride==1; return true;
}
