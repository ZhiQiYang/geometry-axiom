/* D30/I37/R32: declarative alignment, evaluated relative to its selected cell. */
static bool app_grid_vertex(void *state,uint32_t boundary,uint32_t key,GeoPoint2 *out)
{ return boundary_vertex_by_key((const World *)state,boundary,key,out); }

static bool grid_binding_cache(const World *w,const GridBinding *binding,ReferenceGrid *g,char *err,size_t cap)
{
    GeoGridBindingCache cache={0};GeoGridStoreError detail;
    for(int axis=0;axis<2;++axis){
        cache.axis[axis]=g->axis[axis];
        cache.lattice[axis]=(GeoLattice){g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};
    }
    bool ok=geo_grid_binding_evaluate(&w->grid_store,app_grid_binding_index(w,binding->id),app_grid_vertex,(void *)w,&cache,&detail);
    if(detail.status!=GEO_GRID_STORE_BINDING_SOURCE && detail.status!=GEO_GRID_STORE_BINDING_MISSING && detail.status!=GEO_GRID_STORE_INVALID){
        g->from_binding=true;g->binding_id=binding->id;g->main_along=app_grid_system_main_along(w,binding->system_id);
        for(int axis=0;axis<2;++axis){
            g->axis[axis]=cache.axis[axis];g->lattice_base[axis]=cache.lattice[axis].base;
            g->lattice_step[axis]=cache.lattice[axis].pitch;g->lattice_index[axis]=cache.lattice[axis].index;
        }
    }
    if(ok)return true;
    if(err)switch(detail.status){
    case GEO_GRID_STORE_BINDING_CELL_RANGE:snprintf(err,cap,"D29/R32: cell upper line index exceeds signed int64");break;
    case GEO_GRID_STORE_BINDING_ANCHOR:snprintf(err,cap,"D1/I37: anchor must have an exact integer-millimetre offset");break;
    case GEO_GRID_STORE_BINDING_SHIFT_RANGE:snprintf(err,cap,"D10b/D30: 錯開後的錨點超出可表達範圍");break;
    default:snprintf(err,cap,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes");break;
    }
    return false;
}

static bool grid_binding_translation(const World *w,const GridBinding *binding,Coord out[2])
{ return geo_grid_binding_translation(&w->grid_store,app_grid_binding_index(w,binding->id),app_grid_vertex,(void *)w,out,NULL); }

static bool grid_bindings_rebuild(World *w,char *err,size_t cap)
{
    if(geo_grid_bindings_count(&w->grid_store)>WORLD_MAX_GRID_BINDINGS)goto invalid;
    for(size_t i=0;i<geo_grid_bindings_count(&w->grid_store);++i){
        ReferenceGrid derived={0};
        if(!grid_binding_cache(w,geo_grid_bindings_at(&w->grid_store,i),&derived,err,cap))return false;
        for(size_t j=0;j<i;++j)if((*geo_grid_bindings_at(&w->grid_store,j)).id==(*geo_grid_bindings_at(&w->grid_store,i)).id)goto invalid;
    }
    for(size_t i=0;i<w->grid_count;++i){
        ReferenceGrid *g=&w->grids[i];if(!g->from_binding)continue;
        const GridBinding *binding=world_find_grid_binding(w,g->binding_id);
        const PlacementSurface *p=world_find_placement(w,g->placement_id);
        if(!binding || !p || !p->boundary_id || p->boundary_id!=binding->boundary_id ||
            g->is_subgrid || g->from_system || eng_object_bound(w,0,g->id))goto invalid;
        if(!grid_binding_cache(w,binding,g,err,cap))return false;
    }
    return true;
invalid:
    if(err)snprintf(err,cap,"D30/I37: invalid grid-binding identity, capacity or application");return false;
}

static bool apply_grid_binding_line(const char *path,int line_no,char **t,int count,World *w)
{
    GridBinding binding={0};int at=6;World candidate=*w;
    if(count<16 || !parse_u32(t[1],&binding.id) || strcmp(t[2],"on-boundary") ||
        !parse_u32(t[3],&binding.boundary_id) || strcmp(t[4],"from-system") || !parse_u32(t[5],&binding.system_id))goto invalid;
    if(!strcmp(t[at],"vertex-key")){
        if(!parse_u32(t[at+1],&binding.vertex_key) || !binding.vertex_key)goto invalid;at+=2;
    }else if(!strcmp(t[at],"vertex")){
        uint32_t loop=0,index=0;
        ++at;
        if(at>=count)goto invalid;
        if(!strcmp(t[at],"outer"))++at;
        else if(!strcmp(t[at],"hole")){
            if(at+1>=count || !parse_u32(t[at+1],&loop) || loop>=POLY_MAX_HOLES)goto invalid;
            ++loop;at+=2;
        }else goto invalid;
        if(at+2>=count || !parse_u32(t[at],&index) || strcmp(t[at+1],"geometry-hash"))goto invalid;
        const SpaceBoundarySurface *b=world_find_boundary(&candidate,binding.boundary_id);
        if(!b || !boundary_geometry_hash_matches(b,t[at+2])){
            scene_error(path,line_no,"D30: STALE_GEOMETRY; select a vertex on the current boundary");return false;
        }
        if(!boundary_keys_initialize(&candidate,binding.boundary_id))goto invalid;
        const BoundaryVertexKeys *keys=world_find_vertex_keys(&candidate,binding.boundary_id);
        if(loop>=keys->loop_count || index>=keys->counts[loop])goto invalid;
        binding.vertex_key=keys->keys[loop][index];at+=3;
    }else goto invalid;
    if(at+8!=count || strcmp(t[at],"cell") || !parse_i64(t[at+1],&binding.cell[0]) ||
        !parse_i64(t[at+2],&binding.cell[1]) || strcmp(t[at+3],"anchor"))goto invalid;
    for(int a=0;a<2;++a){
        uint32_t n,d;
        if(!parse_u32(t[at+4+a*2],&n)||!parse_u32(t[at+5+a*2],&d)||!d||n>d)goto invalid;
        binding.anchor_num[a]=n;binding.anchor_den[a]=d;
    }
    if(!geo_grid_binding_normalize(&binding))goto invalid;
    if(!geo_grid_bindings_put(&candidate.grid_store,&binding)){scene_error(path,line_no,"I37: grid-binding capacity is 32");return false;}
    reference_capture_trial(&candidate);
    if(!world_revalidate(&candidate)){scene_error(path,line_no,g_revalidate_error);return false;}
    *w=candidate;return true;
invalid:
    scene_error(path,line_no,"D30/I37: invalid grid-binding vertex, signed cell or rational anchor declaration");return false;
}

static bool apply_grid_binding_application(const char *path,int line_no,char **t,int count,World *w)
{
    ReferenceGrid g={0};
    if(count!=6 || !parse_u32(t[1],&g.id) || strcmp(t[2],"on") || !parse_u32(t[3],&g.placement_id) ||
        strcmp(t[4],"from-binding") || !parse_u32(t[5],&g.binding_id))goto invalid;
    if(eng_object_bound(w,0,g.id))goto invalid;
    g.from_binding=true;size_t slot=w->grid_count;
    for(size_t i=0;i<w->grid_count;++i){
        const ReferenceGrid *old=&w->grids[i];
        if(old->id==g.id){if(!old->from_binding || old->is_subgrid || old->placement_id!=g.placement_id)goto invalid;slot=i;}
        else if(!old->is_subgrid && old->placement_id==g.placement_id)goto invalid;
    }
    if(slot==WORLD_MAX_GRIDS)goto invalid;
    World candidate=*w;candidate.grids[slot]=g;if(slot==candidate.grid_count)++candidate.grid_count;
    const World *baseline=g_subgrid_before;if(!baseline)g_subgrid_before=w;
    reference_capture_trial(&candidate);bool ok=world_revalidate(&candidate);g_subgrid_before=baseline;
    if(!ok){scene_error(path,line_no,g_revalidate_error);return false;}
    *w=candidate;return true;
invalid:
    scene_error(path,line_no,"D30/I37: from-binding requires an available lattice grid identity and the binding's boundary placement");return false;
}

static void grid_bindings_dump(const World *w,FILE *out)
{
    for(size_t i=0;i<geo_grid_bindings_count(&w->grid_store);++i){const GridBinding *b=geo_grid_bindings_at(&w->grid_store,i);
        fprintf(out,"grid-binding %u on-boundary %u from-system %u vertex-key %u cell %lld %lld anchor %u %u %u %u\n",
            b->id,b->boundary_id,b->system_id,b->vertex_key,(long long)b->cell[0],(long long)b->cell[1],
            b->anchor_num[0],b->anchor_den[0],b->anchor_num[1],b->anchor_den[1]);
    }
}

/* D10b / R22: one segment per other-axis cell. Unstaggered lines do not enter here. */
static bool grid_query_stagger_segments(const ReferenceGrid *g,const PlacementSurface *p,
    const SpaceBoundarySurface *boundary,const char *kind,int axis,GridQueryLine *line,
    const Coord rect[4],bool sample,GridQueryAxis *q,char *err,size_t cap)
{
    int other=1-axis;
    int64_t step=g->lattice_step[other],base=g->lattice_base[other],origin=g->lattice_index[other];
    if(step<=0){if(err)snprintf(err,cap,"I24: 相位差需要另一軸");return false;}
    Coord blo=rect[other],bhi=rect[other+2],orig_lo=rect[axis],orig_hi=rect[axis+2];
    int64_t first_delta=grid_floor_div(blo-base,step),last_delta=grid_floor_div(bhi-base,step);
    if(first_delta>last_delta) return true;
    int64_t first,last;
    if(!grid_i64_add(origin,first_delta,&first)||!grid_i64_add(origin,last_delta,&last)){
        if(err)snprintf(err,cap,"R32: INDEX_RANGE exceeds signed int64");return false;
    }
    uint64_t bands=(uint64_t)(last_delta-first_delta)+1,stride=1;
    if(bands>(uint64_t)POLY_MAX_VERTICES && !sample){
        if(err)snprintf(err,cap,"R32: QUERY_CAPACITY requires %llu segments; limit %u",(unsigned long long)bands,(unsigned)POLY_MAX_VERTICES);
        return false;
    }
    if(sample && bands>(uint64_t)POLY_MAX_VERTICES) stride=(bands+(uint64_t)POLY_MAX_VERTICES-1)/(uint64_t)POLY_MAX_VERTICES;
    if(stride>q->stride) q->stride=stride;
    for(uint64_t n=0;n<bands;n+=stride){
        int64_t band,next; Coord band_lo,band_hi,coord;
        if(!grid_i64_add(first,(int64_t)n,&band)) break;
        if(!grid_lattice_coord(g,other,band,&band_lo)||!grid_i64_add(band,1,&next)||!grid_lattice_coord(g,other,next,&band_hi)||
            !grid_lattice_coord_band(g,axis,line->index,band,&coord)){
            if(!sample){if(err)snprintf(err,cap,"D10b/D1: 錯開後的格線座標超出可表達範圍");return false;}
            continue;
        }
        if(coord<orig_lo || coord>orig_hi) continue;
        Coord alo=band_lo>blo?band_lo:blo,ahi=band_hi<bhi?band_hi:bhi;
        if(alo>=ahi) continue;
        if(!strcmp(kind,"system")){
            if(line->segment_count>=POLY_MAX_VERTICES){
                if(!sample){if(err)snprintf(err,cap,"R32: QUERY_CAPACITY");return false;}
                return true;
            }
            SurfaceSegment2 seg=axis?(SurfaceSegment2){(SurfacePoint2){alo,coord},(SurfacePoint2){ahi,coord}}
                :(SurfaceSegment2){(SurfacePoint2){coord,alo},(SurfacePoint2){coord,ahi}};
            line->segments[line->segment_count]=seg;
            line->segment_band[line->segment_count]=band;
            line->segment_has_band[line->segment_count]=true;
            ++line->segment_count;
            continue;
        }
        GuideLine guide={0}; guide.placement_id=p->id; guide.direction=axis?GUIDE_ALONG_U:GUIDE_ALONG_V; guide.offset=coord;
        SurfaceSegment2 clips[GUIDE_MAX_SEGMENTS];
        size_t cn=guide_line_get_local_segments(p,boundary,&guide,clips,GUIDE_MAX_SEGMENTS);
        for(size_t j=0;j<cn;++j){
            SurfaceSegment2 seg=clips[j];
            Coord *start=axis?&seg.start.u:&seg.start.v,*end=axis?&seg.end.u:&seg.end.v;
            if(*start<alo)*start=alo; if(*end>ahi)*end=ahi;
            if(*start>=*end) continue;
            if(line->segment_count>=POLY_MAX_VERTICES){
                if(!sample){if(err)snprintf(err,cap,"R32: QUERY_CAPACITY");return false;}
                return true;
            }
            line->segments[line->segment_count]=seg;
            line->segment_band[line->segment_count]=band;
            line->segment_has_band[line->segment_count]=true;
            ++line->segment_count;
        }
    }
    return true;
}

/* Read-only finite query. The temporary placement below is only the existing
 * polygon clipper's local-frame adapter; it is never inserted into World. */
static bool grid_query(const World *w,const char *kind,uint32_t id,const Coord rect[4],
    size_t limit,bool sample,GridQueryAxis axes[2],char *err,size_t cap)
{
    if(!limit || limit>GRID_MAX_LINES || rect[0]>rect[2] || rect[1]>rect[3])goto invalid;
    for(int a=0;a<4;++a)if(!coord_in_range(rect[a]))goto invalid;
    ReferenceGrid cache={0};const ReferenceGrid *g=&cache;
    PlacementSurface local={0};SpaceBoundarySurface boundary_storage;
    const PlacementSurface *p=&local;const SpaceBoundarySurface *boundary=NULL;
    if(!strcmp(kind,"system")){
        const GridSystem *s=world_find_grid_system(w,id);if(!s || !grid_system_is_infinite(s))goto invalid;
        cache.from_binding=true;
        for(int a=0;a<2;++a)if(grid_axis_is_infinite(&s->axis[a])){
            cache.axis[a]=s->axis[a];cache.lattice_index[a]=0;
            cache.lattice_base[a]=grid_axis_phase(&s->axis[a]);cache.lattice_step[a]=grid_axis_pitch(&s->axis[a]);
        }
    }else if(!strcmp(kind,"binding")){
        const GridBinding *b=world_find_grid_binding(w,id);
        if(!b || !grid_binding_cache(w,b,&cache,err,cap))goto invalid;
        boundary=app_boundary_read(w,b->boundary_id,&boundary_storage);
    }else if(!strcmp(kind,"grid")){
        g=world_find_grid(w,id);if(!g)goto invalid;
        p=app_placement_read(w,g->placement_id,&local);if(!p)goto invalid;
        boundary=app_placement_boundary(w,p,&boundary_storage);
    }else goto invalid;
    for(int a=0;a<2;++a){
        GridQueryAxis *q=&axes[a];
        if(g->from_binding){
            Coord lo=rect[a],hi=rect[a+2];
            if(g->axis[a].stagger_set){
                Coord mag=g->axis[a].stagger>=0?g->axis[a].stagger:(g->axis[a].stagger==INT64_MIN?COORD_LIMIT:-g->axis[a].stagger);
                int64_t elo,ehi;
                if(!grid_i64_add(lo,-(int64_t)mag,&elo)) elo=-COORD_LIMIT;
                if(!grid_i64_add(hi,mag,&ehi)) ehi=COORD_LIMIT;
                if(elo<-COORD_LIMIT) elo=-COORD_LIMIT; if(ehi>COORD_LIMIT) ehi=COORD_LIMIT;
                lo=(Coord)elo; hi=(Coord)ehi;
            }
            if(!grid_lattice_window(g,a,lo,hi,limit,sample,q,err,cap))return false;
        }
        else {
            memset(q,0,sizeof *q);q->stride=1;
            if(g->axis[a].source==GRID_SRC_NONE && !g->is_subgrid)continue;
            q->defined=true;Coord coords[GRID_MAX_LINES];size_t n=0;
            if(!grid_axis_lines_in(w->grids,w->grid_count,g,p,boundary,a,coords,&n,err,cap))return false;
            for(size_t i=0;i<n;++i)if(coords[i]>=rect[a] && coords[i]<=rect[a+2]){
                if(!q->total)q->first=(int64_t)i;q->last=(int64_t)i;++q->total;
            }
            if(q->total>limit && !sample){if(err)snprintf(err,cap,"R32: QUERY_CAPACITY");return false;}
            q->stride=sample?(q->total+limit-1)/limit:1;if(!q->stride)q->stride=1;
            for(size_t i=0;i<n;++i)if(coords[i]>=rect[a] && coords[i]<=rect[a+2] && i%q->stride==0){
                GridQueryLine *line=&q->lines[q->count++];line->index=(int64_t)i;line->coordinate=coords[i];
            }
        }
        for(size_t i=0;i<q->count;++i){
            GridQueryLine *line=&q->lines[i];SurfaceSegment2 clips[GUIDE_MAX_SEGMENTS];size_t n;
            Coord lo=rect[1-a],hi=rect[3-a];
            if(g->from_binding && g->axis[a].stagger_set){
                if(!grid_query_stagger_segments(g,p,boundary,kind,a,line,rect,sample,q,err,cap)) return false;
                continue;
            }
            if(!strcmp(kind,"system")){
                clips[0]=(SurfaceSegment2){a?(SurfacePoint2){lo,line->coordinate}:(SurfacePoint2){line->coordinate,lo},
                    a?(SurfacePoint2){hi,line->coordinate}:(SurfacePoint2){line->coordinate,hi}};n=1;
            }else if(g->is_subgrid){
                n=grid_line_segments(w->grids,w->grid_count,g,p,boundary,a,line->index,clips,GUIDE_MAX_SEGMENTS);
            }else {
                GuideLine guide={0};guide.placement_id=p->id;guide.direction=a?GUIDE_ALONG_U:GUIDE_ALONG_V;guide.offset=line->coordinate;
                n=guide_line_get_local_segments(p,boundary,&guide,clips,GUIDE_MAX_SEGMENTS);
            }
            for(size_t j=0;j<n;++j){
                SurfaceSegment2 seg=clips[j];Coord *start=a?&seg.start.u:&seg.start.v,*end=a?&seg.end.u:&seg.end.v;
                if(*start<lo)*start=lo;if(*end>hi)*end=hi;
                if(*start<*end)line->segments[line->segment_count++]=seg;
            }
        }
    }
    return true;
invalid:
    if(err)snprintf(err,cap,"R32: invalid query source, rectangle or limit (1..64)");return false;
}
