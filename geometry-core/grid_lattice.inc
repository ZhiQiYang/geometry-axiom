/* D29/R32: integer lattice arithmetic. No viewport is a source definition. */
static bool grid_i64_add(int64_t a,int64_t b,int64_t *out)
{ return geo_i64_add(a,b,out); }
static int64_t grid_floor_div(int64_t a,int64_t b)
{ return geo_floor_div(a,b); }
static int64_t grid_ceil_div(int64_t a,int64_t b)
{ return geo_ceil_div(a,b); }
static bool grid_axis_is_infinite(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT || a->source==GRID_SRC_REPEAT_PANEL; }
static bool grid_system_is_infinite(const GridSystem *s)
{ return grid_axis_is_infinite(&s->axis[0]) || grid_axis_is_infinite(&s->axis[1]); }
static Coord grid_axis_pitch(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT?a->step:panel_layout_pitch(a->panel,a->gap); }
static Coord grid_axis_phase(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT?a->start:panel_layout_center(a->anchor,a->panel,a->gap,0); }

static bool grid_lattice_coord(const ReferenceGrid *g,int axis,int64_t k,Coord *out)
{
    if(!g||!g->from_binding||axis<0||axis>1)return false;
    GeoLattice lattice={g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};
    return geo_lattice_coord(&lattice,k,out);
}

static bool grid_lattice_window(const ReferenceGrid *g,int axis,Coord lo,Coord hi,
    size_t limit,bool sample,GridQueryAxis *out,char *err,size_t cap)
{
    memset(out,0,sizeof *out);out->stride=1;
    if(!g||axis<0||axis>1||limit>GRID_MAX_LINES)goto invalid;
    GeoLattice lattice={g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};
    GeoLatticeLine lines[GRID_MAX_LINES];GeoLatticeWindow result={.lines=lines,.capacity=GRID_MAX_LINES};
    GeoGridStatus status=geo_lattice_window(&lattice,lo,hi,limit,sample,&result);
    out->defined=result.defined;out->first=result.first;out->last=result.last;
    out->total=result.total;out->stride=result.stride;out->count=result.count;
    for(size_t i=0;i<result.count;++i){out->lines[i].index=lines[i].index;out->lines[i].coordinate=lines[i].coordinate;}
    if(status==GEO_GRID_OK)return true;
    if(status==GEO_GRID_INDEX_RANGE){if(err)snprintf(err,cap,"R32: INDEX_RANGE exceeds signed int64");return false;}
    if(status==GEO_GRID_CAPACITY){if(err)snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu lines; limit %u",(unsigned long long)out->total,(unsigned)limit);return false;}
invalid:
    if(err)snprintf(err,cap,"R32: invalid lattice query or D1 coordinate");return false;
}

/* D10b: the lowest bit selects the odd band, including negative odds. Shift 0 keeps the unstaggered coordinate. */
static Coord grid_axis_stagger_shift(const GridAxisDef *a,int64_t band)
{ return a?panel_layout_shift(a->stagger_set,a->stagger,band):0; }

static bool grid_lattice_coord_band(const ReferenceGrid *g,int axis,int64_t k,int64_t band,Coord *out)
{
    Coord base,shift; int64_t value;
    if(!grid_lattice_coord(g,axis,k,&base)) return false;
    shift=grid_axis_stagger_shift(&g->axis[axis],band);
    if(!shift){ if(out) *out=base; return true; }
    if(!grid_i64_add(base,shift,&value) || !coord_in_range(value)) return false;
    if(out) *out=value; return true;
}
