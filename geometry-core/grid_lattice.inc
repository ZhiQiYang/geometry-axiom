/* D29/R32: integer lattice arithmetic. No viewport is a source definition. */
static bool grid_i64_add(int64_t a,int64_t b,int64_t *out)
{
    if ((b>0 && a>INT64_MAX-b)||(b<0 && a<INT64_MIN-b)) return false;
    *out=a+b; return true;
}
static bool grid_i64_mul_positive(int64_t a,int64_t b,int64_t *out)
{
    if (b<=0 || a>INT64_MAX/b || a<INT64_MIN/b) return false;
    *out=a*b; return true;
}
static int64_t grid_floor_div(int64_t a,int64_t b)
{ int64_t q=a/b,r=a%b; return q-(r<0); }
static int64_t grid_ceil_div(int64_t a,int64_t b)
{ int64_t q=a/b,r=a%b; return q+(r>0); }
static bool grid_axis_is_infinite(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT || a->source==GRID_SRC_REPEAT_PANEL; }
static bool grid_system_is_infinite(const GridSystem *s)
{ return grid_axis_is_infinite(&s->axis[0]) || grid_axis_is_infinite(&s->axis[1]); }
static Coord grid_axis_pitch(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT?a->step:a->panel+a->gap; }
static Coord grid_axis_phase(const GridAxisDef *a)
{ return a->source==GRID_SRC_REPEAT?a->start:a->anchor+a->panel+a->gap/2; }

static bool grid_lattice_coord(const ReferenceGrid *g,int axis,int64_t k,Coord *out)
{
    if (!g || !g->from_binding || axis<0 || axis>1 || g->lattice_step[axis]<=0) return false;
    int64_t base=g->lattice_base[axis],origin=g->lattice_index[axis],step=g->lattice_step[axis],value;
    if (k>=origin) {
        uint64_t delta=(uint64_t)k-(uint64_t)origin;
        int64_t room=COORD_LIMIT-base;
        if (room<0 || delta>(uint64_t)(room/step)) return false;
        value=base+(int64_t)delta*step;
    } else {
        uint64_t delta=(uint64_t)origin-(uint64_t)k;
        int64_t room=base+COORD_LIMIT;
        if (room<0 || delta>(uint64_t)(room/step)) return false;
        value=base-(int64_t)delta*step;
    }
    if (!coord_in_range(value)) return false;
    if(out) *out=value; return true;
}

static bool grid_lattice_window(const ReferenceGrid *g,int axis,Coord lo,Coord hi,
    size_t limit,bool sample,GridQueryAxis *out,char *err,size_t cap)
{
    memset(out,0,sizeof *out); out->stride=1;
    if (!g || axis<0 || axis>1 || !limit || limit>GRID_MAX_LINES || lo>hi ||
        !coord_in_range(lo) || !coord_in_range(hi)) goto invalid;
    if (!g->lattice_step[axis]) return true;
    out->defined=true;
    int64_t step=g->lattice_step[axis],base=g->lattice_base[axis],origin=g->lattice_index[axis];
    int64_t first_delta=grid_ceil_div(lo-base,step),last_delta=grid_floor_div(hi-base,step);
    if(first_delta>last_delta) return true;
    if(!grid_i64_add(origin,first_delta,&out->first)||!grid_i64_add(origin,last_delta,&out->last)) {
        if(err) snprintf(err,cap,"R32: INDEX_RANGE exceeds signed int64"); return false;
    }
    out->total=(uint64_t)(last_delta-first_delta)+1;
    if(out->total>limit && !sample) {
        if(err) snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu lines; limit %u",(unsigned long long)out->total,(unsigned)limit);
        return false;
    }
    out->stride=sample?(out->total+limit-1)/limit:1;
    if(!out->stride) out->stride=1;
    int64_t stride=(int64_t)out->stride,k=out->first,r=k%stride;
    if(r<0)r+=stride;
    if(r && !grid_i64_add(k,stride-r,&k)) return true;
    for(;k<=out->last;) {
        GridQueryLine *line=&out->lines[out->count]; line->index=k;
        if(!grid_lattice_coord(g,axis,k,&line->coordinate)) goto invalid;
        if(++out->count>=limit || out->last-k<stride) break;
        k+=stride;
    }
    return true;
invalid:
    if(err) snprintf(err,cap,"R32: invalid lattice query or D1 coordinate"); return false;
}
