/* D30/I37/R32: declarative alignment, evaluated relative to its selected cell. */
static uint32_t grid_gcd(uint32_t a,uint32_t b)
{ while(b){uint32_t r=a%b;a=b;b=r;}return a; }

static bool grid_binding_cache(const World *w,const GridBinding *binding,ReferenceGrid *g,char *err,size_t cap)
{
    const GridSystem *s=world_find_grid_system(w,binding->system_id); SurfacePoint2 v;
    if(!s || !grid_axis_is_infinite(&s->axis[0]) || !grid_axis_is_infinite(&s->axis[1]) ||
        !boundary_vertex_by_key(w,binding->boundary_id,binding->vertex_key,&v)) goto invalid;
    g->from_binding=true;g->binding_id=binding->id;g->main_along=s->main_along;
    for(int a=0;a<2;++a){
        if(binding->cell[a]==INT64_MAX){
            if(err)snprintf(err,cap,"D29/R32: cell upper line index exceeds signed int64");return false;
        }
        uint32_t n=binding->anchor_num[a],d=binding->anchor_den[a];
        Coord pitch=grid_axis_pitch(&s->axis[a]);
        if(!d || n>d || pitch<=0 || ((uint64_t)pitch*n)%d) {
            if(err)snprintf(err,cap,"D1/I37: anchor must have an exact integer-millimetre offset");return false;
        }
        g->axis[a]=s->axis[a];g->lattice_step[a]=pitch;g->lattice_index[a]=binding->cell[a];
        g->lattice_base[a]=(a?v.v:v.u)-(Coord)(((uint64_t)pitch*n)/d);
    }
    return true;
invalid:
    if(err)snprintf(err,cap,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes");return false;
}

static bool grid_binding_translation(const World *w,const GridBinding *binding,Coord out[2])
{
    ReferenceGrid g={0};if(!grid_binding_cache(w,binding,&g,NULL,0))return false;
    const GridSystem *s=world_find_grid_system(w,binding->system_id);
    for(int a=0;a<2;++a){
        int64_t index=binding->cell[a],relative=g.lattice_base[a]-grid_axis_phase(&s->axis[a]);
        uint64_t magnitude=index<0?UINT64_C(0)-(uint64_t)index:(uint64_t)index;
        uint64_t pitch=(uint64_t)g.lattice_step[a],product;
        if(magnitude>UINT64_MAX/pitch)return false;
        product=magnitude*pitch;
        /* An intermediate I*pitch may exceed int64 even when translation fits.
         * Keep a sign and magnitude until after the small local offset. */
        bool negative=index>=0;
        if(negative){
            if(relative>=0){
                if(product<(uint64_t)relative){product=(uint64_t)relative-product;negative=false;}
                else product-=(uint64_t)relative;
            }else{
                uint64_t extra=UINT64_C(0)-(uint64_t)relative;
                if(product>UINT64_MAX-extra)return false;product+=extra;
            }
        }else{
            if(relative<0){
                uint64_t extra=UINT64_C(0)-(uint64_t)relative;
                if(product<extra){product=extra-product;negative=true;}else product-=extra;
            }else{if(product>UINT64_MAX-(uint64_t)relative)return false;product+=(uint64_t)relative;}
        }
        uint64_t negative_limit=(uint64_t)INT64_MAX+1;
        if(product>(negative?negative_limit:(uint64_t)INT64_MAX))return false;
        out[a]=negative?(product==negative_limit?INT64_MIN:-(int64_t)product):(int64_t)product;
    }
    return true;
}

static bool grid_bindings_rebuild(World *w,char *err,size_t cap)
{
    if(w->grid_binding_count>WORLD_MAX_GRID_BINDINGS)goto invalid;
    for(size_t i=0;i<w->grid_binding_count;++i){
        ReferenceGrid derived={0};
        if(!grid_binding_cache(w,&w->grid_bindings[i],&derived,err,cap))return false;
        for(size_t j=0;j<i;++j)if(w->grid_bindings[j].id==w->grid_bindings[i].id)goto invalid;
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
        uint32_t factor=grid_gcd(n,d);binding.anchor_num[a]=n/factor;binding.anchor_den[a]=d/factor;
    }
    size_t slot=0;while(slot<candidate.grid_binding_count && candidate.grid_bindings[slot].id!=binding.id)++slot;
    if(slot==candidate.grid_binding_count){
        if(slot==WORLD_MAX_GRID_BINDINGS){scene_error(path,line_no,"I37: grid-binding capacity is 32");return false;}
        ++candidate.grid_binding_count;
    }
    candidate.grid_bindings[slot]=binding;reference_capture_trial(&candidate);
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
    for(size_t i=0;i<w->grid_binding_count;++i){const GridBinding *b=&w->grid_bindings[i];
        fprintf(out,"grid-binding %u on-boundary %u from-system %u vertex-key %u cell %lld %lld anchor %u %u %u %u\n",
            b->id,b->boundary_id,b->system_id,b->vertex_key,(long long)b->cell[0],(long long)b->cell[1],
            b->anchor_num[0],b->anchor_den[0],b->anchor_num[1],b->anchor_den[1]);
    }
}

/* Read-only finite query. The temporary placement below is only the existing
 * polygon clipper's local-frame adapter; it is never inserted into World. */
static bool grid_query(const World *w,const char *kind,uint32_t id,const Coord rect[4],
    size_t limit,bool sample,GridQueryAxis axes[2],char *err,size_t cap)
{
    if(!limit || limit>GRID_MAX_LINES || rect[0]>rect[2] || rect[1]>rect[3])goto invalid;
    for(int a=0;a<4;++a)if(!coord_in_range(rect[a]))goto invalid;
    ReferenceGrid cache={0};const ReferenceGrid *g=&cache;
    PlacementSurface local={0};const PlacementSurface *p=&local;const SpaceBoundarySurface *boundary=NULL;
    if(!strcmp(kind,"system")){
        const GridSystem *s=world_find_grid_system(w,id);if(!s || !grid_system_is_infinite(s))goto invalid;
        cache.from_binding=true;
        for(int a=0;a<2;++a)if(grid_axis_is_infinite(&s->axis[a])){
            cache.lattice_base[a]=grid_axis_phase(&s->axis[a]);cache.lattice_step[a]=grid_axis_pitch(&s->axis[a]);
        }
    }else if(!strcmp(kind,"binding")){
        const GridBinding *b=world_find_grid_binding(w,id);
        if(!b || !grid_binding_cache(w,b,&cache,err,cap))goto invalid;
        boundary=world_find_boundary(w,b->boundary_id);
    }else if(!strcmp(kind,"grid")){
        g=world_find_grid(w,id);if(!g)goto invalid;
        p=world_find_placement(w,g->placement_id);if(!p)goto invalid;
        boundary=world_placement_boundary(w,p);
    }else goto invalid;
    for(int a=0;a<2;++a){
        GridQueryAxis *q=&axes[a];
        if(g->from_binding){if(!grid_lattice_window(g,a,rect[a],rect[a+2],limit,sample,q,err,cap))return false;}
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
            GridQueryLine *line=&q->lines[i];SurfaceSegment2 clips[POLY_MAX_VERTICES];size_t n;
            Coord lo=rect[1-a],hi=rect[3-a];
            if(!strcmp(kind,"system")){
                clips[0]=(SurfaceSegment2){a?(SurfacePoint2){lo,line->coordinate}:(SurfacePoint2){line->coordinate,lo},
                    a?(SurfacePoint2){hi,line->coordinate}:(SurfacePoint2){line->coordinate,hi}};n=1;
            }else if(g->is_subgrid){
                n=grid_line_segments(w->grids,w->grid_count,g,p,boundary,a,line->index,clips,POLY_MAX_VERTICES);
            }else {
                GuideLine guide={0};guide.placement_id=p->id;guide.direction=a?GUIDE_ALONG_U:GUIDE_ALONG_V;guide.offset=line->coordinate;
                n=guide_line_get_local_segments(p,boundary,&guide,clips,POLY_MAX_VERTICES);
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
