/* PF-1: D41 finish surfaces (panel-fill/1), I52 / I55 / I56 / R4 and the first half of R41.
 *
 * Only definitions live in World: id, name, D3 boundary reference, D2 frame, structure side s and the
 * explicit obstacle set.  F (outline minus holes), each obstacle's projection R_k, its q interval along
 * n = s*N and the plane relation int(R_k) n int(F) are derived on every read and preview and are never
 * serialized (I56, R4).  The two-layer judgement of I53 needs a panel fill (t) and a derived placement (h),
 * which PF-1 does not have; callers report it as pending instead of guessing. */
static bool fs_error(const char *format,...)
{
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    utf8_trim_tail(g_engineering_error);return false;
}
static bool fs_used(const World *w) { return w->finish_surfaces.count!=0; }
static int fs_index(const World *w,uint32_t id)
{
    for(uint64_t i=0;i<w->finish_surfaces.count;++i)if(w->finish_surfaces.items[i].id==id)return (int)i;
    return -1;
}
static const FinishSurface *fs_find(const World *w,uint32_t id)
{ int at=fs_index(w,id);return at<0?NULL:&w->finish_surfaces.items[at]; }
static void fs_obstacle_text(const FinishObstacleRef *r,char out[16])
{ snprintf(out,16,"%c%u",r->kind==FS_OBSTACLE_BEAM?'b':'c',(unsigned)r->id); }
/* Typed reference c<id> / b<id>; canonical decimal only (no sign, no leading zero). */
static bool fs_obstacle_parse(const char *s,FinishObstacleRef *out)
{
    uint32_t id;
    if((s[0]!='c'&&s[0]!='b')||!s[1]||(s[1]=='0'&&s[2]))return false;
    for(const char *p=s+1;*p;++p)if(*p<'0'||*p>'9')return false;
    if(!parse_u32(s+1,&id))return false;
    out->kind=s[0]=='b'?FS_OBSTACLE_BEAM:FS_OBSTACLE_COLUMN;out->id=id;return true;
}
/* R41 source order: columns by id < beams by id. */
static int fs_obstacle_compare(const void *a,const void *b)
{
    const FinishObstacleRef *x=a,*y=b;
    if(x->kind!=y->kind)return x->kind<y->kind?-1:1;
    return (x->id>y->id)-(x->id<y->id);
}
static bool fs_obstacles_normalize(FinishSurface *f)
{
    qsort(f->obstacles,f->obstacle_count,sizeof f->obstacles[0],fs_obstacle_compare);
    for(uint32_t i=1;i<f->obstacle_count;++i)if(!fs_obstacle_compare(&f->obstacles[i-1],&f->obstacles[i])){
        char text[16];fs_obstacle_text(&f->obstacles[i],text);
        return fs_error("D41: finish surface %u lists obstacle %s more than once",(unsigned)f->id,text);
    }
    return true;
}
static bool fs_obstacle_box(const World *w,const FinishObstacleRef *r,Coord lo[3],Coord hi[3])
{
    if(r->kind==FS_OBSTACLE_COLUMN){
        const RcColumn *c=world_find_column(w,r->id);if(!c)return false;
        lo[0]=c->x_lo;lo[1]=c->y_lo;lo[2]=c->z_lo;hi[0]=c->x_hi;hi[1]=c->y_hi;hi[2]=c->z_hi;return true;
    }
    const RcBeam *b=world_find_beam(w,r->id);if(!b)return false;
    lo[0]=b->x_lo;lo[1]=b->y_lo;lo[2]=b->z_lo;hi[0]=b->x_hi;hi[1]=b->y_hi;hi[2]=b->z_hi;return true;
}
/* Interval of (P - O) . axis over the AABB; axis is a unit integer world axis (I1). */
static void fs_project_interval(const Coord lo[3],const Coord hi[3],Point3 origin,Vector3 axis,Coord out[2])
{
    int c=axis.x?0:axis.y?1:2;Coord sign=axis.x?axis.x:axis.y?axis.y:axis.z;
    Coord o=c==0?origin.x:c==1?origin.y:origin.z;
    if(sign>0){out[0]=lo[c]-o;out[1]=hi[c]-o;}else{out[0]=o-hi[c];out[1]=o-lo[c];}
}
/* Exact area of rect [u0,u1]x[v0,v1] inside one simple orthogonal loop: horizontal bands at every vertex v,
 * even-odd crossings of vertical edges at the band middle (doubled to stay integral). */
static Coord fs_loop_rect_area(const PolygonLoop2 *p,Coord u0,Coord v0,Coord u1,Coord v1)
{
    Coord ys[POLY_MAX_VERTICES+2],xs[POLY_MAX_VERTICES],area=0;size_t ny=0;
    ys[ny++]=v0;ys[ny++]=v1;
    for(size_t i=0;i<p->count;++i)if(p->v[i].v>v0&&p->v[i].v<v1)ys[ny++]=p->v[i].v;
    qsort(ys,ny,sizeof ys[0],sp_coord_compare);
    for(size_t k=1;k<ny;++k){
        Coord lo=ys[k-1],hi=ys[k],mid2=lo+hi;size_t nx=0;if(lo==hi)continue;
        for(size_t i=0;i<p->count;++i){SurfacePoint2 a=p->v[i],b=p->v[(i+1)%p->count];
            if(a.u==b.u&&2*coord_min(a.v,b.v)<mid2&&mid2<2*coord_max(a.v,b.v))xs[nx++]=a.u;}
        qsort(xs,nx,sizeof xs[0],sp_coord_compare);
        for(size_t i=0;i+1<nx;i+=2){Coord a=coord_max(xs[i],u0),b=coord_min(xs[i+1],u1);if(a<b)area+=(b-a)*(hi-lo);}
    }
    return area;
}
/* Closed contact between any loop edge and the closed rectangle (edges are axis-parallel). */
static bool fs_loop_touches_rect(const PolygonLoop2 *p,Coord u0,Coord v0,Coord u1,Coord v1)
{
    for(size_t i=0;i<p->count;++i){SurfacePoint2 a=p->v[i],b=p->v[(i+1)%p->count];
        if(coord_min(a.u,b.u)<=u1&&u0<=coord_max(a.u,b.u)&&coord_min(a.v,b.v)<=v1&&v0<=coord_max(a.v,b.v))return true;}
    return false;
}
enum { FS_SEPARATE = 0, FS_TOUCH = 1, FS_INTERIOR = 2 };
static const char *fs_relation_name(int relation)
{ return relation==FS_INTERIOR?"interior":relation==FS_TOUCH?"touch":"separate"; }
/* R41/I53: interior iff int(R_k) n int(F) is non-empty, i.e. positive area (F is a regular orthogonal region).
 * Otherwise any common point lies on F's boundary, so contact is an edge test. */
static int fs_relation(const SpaceBoundarySurface *b,const Coord r[4])
{
    Coord area=fs_loop_rect_area(&b->outline,r[0],r[1],r[2],r[3]);
    for(size_t h=0;h<b->hole_count;++h)area-=fs_loop_rect_area(&b->holes[h],r[0],r[1],r[2],r[3]);
    if(area>0)return FS_INTERIOR;
    if(fs_loop_touches_rect(&b->outline,r[0],r[1],r[2],r[3]))return FS_TOUCH;
    for(size_t h=0;h<b->hole_count;++h)if(fs_loop_touches_rect(&b->holes[h],r[0],r[1],r[2],r[3]))return FS_TOUCH;
    return FS_SEPARATE;
}
typedef struct { Coord rect[4],q[2]; int relation; } FsObstacleView;
static bool fs_obstacle_view(const World *w,const FinishSurface *f,const FinishObstacleRef *r,FsObstacleView *out)
{
    Coord lo[3],hi[3],u[2],v[2],n[2];char text[16];fs_obstacle_text(r,text);
    if(!fs_obstacle_box(w,r,lo,hi))return fs_error("I52/I55: finish surface %u obstacle %s does not exist",(unsigned)f->id,text);
    fs_project_interval(lo,hi,f->frame.origin,f->frame.axis_u,u);
    fs_project_interval(lo,hi,f->frame.origin,f->frame.axis_v,v);
    fs_project_interval(lo,hi,f->frame.origin,f->frame.normal,n);
    out->rect[0]=u[0];out->rect[1]=v[0];out->rect[2]=u[1];out->rect[3]=v[1];
    out->q[0]=f->side>0?n[0]:-n[1];out->q[1]=f->side>0?n[1]:-n[0];
    for(int i=0;i<4;++i)if(!coord_in_range(out->rect[i]))
        return fs_error("I52/D1 CAPACITY: obstacle %s of finish surface %u has local coordinates outside D1 (I33)",text,(unsigned)f->id);
    for(int i=0;i<2;++i)if(!coord_in_range(out->q[i]))
        return fs_error("I52/D1 CAPACITY: obstacle %s of finish surface %u has local coordinates outside D1 (I33)",text,(unsigned)f->id);
    const SpaceBoundarySurface *b=world_find_boundary(w,f->boundary_id);
    if(!b)return fs_error("I52: finish surface %u references missing boundary %u",(unsigned)f->id,(unsigned)f->boundary_id);
    out->relation=fs_relation(b,out->rect);return true;
}
/* I52 first sentence + D41: references exist and are typed, frame obeys D1/D2 (I1), s is a sign. */
static bool fs_check(const World *w,const FinishSurface *f)
{
    size_t n=0;while(n<sizeof f->name&&f->name[n])++n;
    if(!f->id)return fs_error("D41: finish surface id must be a positive integer");
    if(n>FS_NAME_MAX||!grid_system_name_valid((const unsigned char*)f->name,n))
        return fs_error("D41: finish surface %u name must be 1..%d bytes of printable UTF-8",(unsigned)f->id,FS_NAME_MAX);
    if(!world_find_boundary(w,f->boundary_id))
        return fs_error("I52: finish surface %u references missing boundary %u",(unsigned)f->id,(unsigned)f->boundary_id);
    if(!surface_frame_is_valid(&f->frame))
        return fs_error("I52/I1: finish surface %u frame needs an origin in D1 and unit integer axes with U x V = N",(unsigned)f->id);
    if(f->side!=1&&f->side!=-1)return fs_error("D41: finish surface %u structureSide must be 1 or -1",(unsigned)f->id);
    if(f->obstacle_count>FS_OBSTACLE_MAX)return fs_error("I33 CAPACITY: finish surface %u obstacle set is limited to %d",(unsigned)f->id,FS_OBSTACLE_MAX);
    for(uint32_t i=0;i<f->obstacle_count;++i){FsObstacleView view;
        if(i&&fs_obstacle_compare(&f->obstacles[i-1],&f->obstacles[i])>=0)
            return fs_error("D41: finish surface %u obstacle set must be unique and in R41 order",(unsigned)f->id);
        if(!fs_obstacle_view(w,f,&f->obstacles[i],&view))return false;
    }
    return true;
}
/* I55: every candidate World is re-checked as a whole; a committed World never holds a missing reference. */
static bool fs_rebuild(World *w,char *error,size_t capacity)
{
    const FinishSurfaceState *s=&w->finish_surfaces;
    if(s->count>FS_MAX){snprintf(error,capacity,"I33 CAPACITY: finish surface limit is %d",FS_MAX);return false;}
    for(uint64_t i=0;i<s->count;++i){
        for(uint64_t k=0;k<i;++k)if(s->items[k].id==s->items[i].id){snprintf(error,capacity,"D41: duplicate finish surface id %u",(unsigned)s->items[i].id);return false;}
        if(!fs_check(w,&s->items[i])){snprintf(error,capacity,"%s",g_engineering_error);utf8_trim_tail(error);return false;}
    }
    return true;
}
/* I55 delete guard for the DSL `delete` line: name the first finish surface that still references the source. */
static uint32_t fs_reference_owner(const World *w,const char *kind,uint32_t id)
{
    bool boundary=!strcmp(kind,"boundary"),column=!strcmp(kind,"column"),beam=!strcmp(kind,"beam");
    if(!boundary&&!column&&!beam)return 0;
    for(uint64_t i=0;i<w->finish_surfaces.count;++i){const FinishSurface *f=&w->finish_surfaces.items[i];
        if(boundary&&f->boundary_id==id)return f->id;
        for(uint32_t k=0;k<f->obstacle_count;++k)
            if(f->obstacles[k].id==id&&f->obstacles[k].kind==(column?FS_OBSTACLE_COLUMN:FS_OBSTACLE_BEAM)&&!boundary)return f->id;
    }
    return 0;
}
/* ---- transaction operations (panel-fill-transaction/1) ---- */
static bool fs_from_json(EngJson *j,int t,FinishSurface *f)
{
    int frame=eng_json_member(j,t,"frame"),origin,obstacles=eng_json_member(j,t,"obstacles");int64_t side,xyz[3];
    char name[FS_NAME_MAX*4+8];
    memset(f,0,sizeof *f);
    if(!eng_json_keys(j,t,"id,name,boundaryId,frame,structureSide,obstacles","")||!eng_u32(j,eng_json_member(j,t,"id"),&f->id,true)||
       !eng_u32(j,eng_json_member(j,t,"boundaryId"),&f->boundary_id,true))
        return fs_error("D41: finish surface needs positive id and boundaryId, name, frame {origin,U,V,N}, structureSide and obstacles");
    if(!eng_json_string(j,eng_json_member(j,t,"name"),name,sizeof name)||strlen(name)>FS_NAME_MAX)
        return fs_error("D41: finish surface %u name must be 1..%d bytes of printable UTF-8",(unsigned)f->id,FS_NAME_MAX);
    memcpy(f->name,name,strlen(name)+1);
    if(!eng_json_is_object(j,frame)||!eng_json_keys(j,frame,"origin,U,V,N",""))
        return fs_error("I52/D2: finish surface %u frame needs origin, U, V and N",(unsigned)f->id);
    origin=eng_json_member(j,frame,"origin");
    if(!eng_json_is_array(j,origin)||eng_json_size(j,origin)!=3)return fs_error("I52/D1: finish surface %u origin must be three integer mm",(unsigned)f->id);
    for(int i=0;i<3;++i)if(!eng_json_integer(j,eng_json_at(j,origin,i),&xyz[i]))return fs_error("I52/D1: finish surface %u origin must be three integer mm",(unsigned)f->id);
    f->frame.origin=(Point3){xyz[0],xyz[1],xyz[2]};
    if(!sp_axis(j,eng_json_member(j,frame,"U"),&f->frame.axis_u)||!sp_axis(j,eng_json_member(j,frame,"V"),&f->frame.axis_v)||
       !sp_axis(j,eng_json_member(j,frame,"N"),&f->frame.normal))
        return fs_error("I52/D2: finish surface %u axes must each be one of +X -X +Y -Y +Z -Z",(unsigned)f->id);
    if(!eng_json_integer(j,eng_json_member(j,t,"structureSide"),&side)||(side!=1&&side!=-1))
        return fs_error("D41: finish surface %u structureSide must be 1 or -1",(unsigned)f->id);
    f->side=(int32_t)side;
    if(!eng_json_is_array(j,obstacles))return fs_error("D41: finish surface %u obstacles must be an array of c<id> / b<id>",(unsigned)f->id);
    int count=eng_json_size(j,obstacles);
    if(count>FS_OBSTACLE_MAX)return fs_error("I33 CAPACITY: finish surface %u obstacle set is limited to %d",(unsigned)f->id,FS_OBSTACLE_MAX);
    for(int i=0;i<count;++i){char text[16];
        if(!eng_json_string(j,eng_json_at(j,obstacles,i),text,sizeof text)||!fs_obstacle_parse(text,&f->obstacles[i]))
            return fs_error("D41: finish surface %u obstacles must be typed references c<id> or b<id>",(unsigned)f->id);}
    f->obstacle_count=(uint32_t)count;
    return fs_obstacles_normalize(f);
}
static bool fs_put(World *w,EngJson *j,int t)
{
    FinishSurface f;FinishSurfaceState *s=&w->finish_surfaces;
    if(!fs_from_json(j,t,&f)||!fs_check(w,&f))return false;
    int at=fs_index(w,f.id);
    if(at<0){if(s->count>=FS_MAX)return fs_error("I33 CAPACITY: finish surface limit is %d",FS_MAX);at=(int)s->count++;}
    memcpy(&s->items[at],&f,sizeof f);return true;
}
static bool fs_delete(World *w,uint32_t id)
{
    FinishSurfaceState *s=&w->finish_surfaces;int at=fs_index(w,id);
    if(at<0)return fs_error("D41: deleted finish surface %u does not exist",(unsigned)id);
    memmove(&s->items[at],&s->items[at+1],(size_t)(s->count-(uint64_t)at-1)*sizeof s->items[0]);
    --s->count;memset(&s->items[s->count],0,sizeof s->items[0]);return true;
}
static bool fs_operation(World *w,EngJson *j,int t)
{
    char op[40];uint32_t id;
    if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return fs_error("I55: panel-fill operation needs op");
    if(!strcmp(op,"put-finish-surface")){
        if(!eng_json_keys(j,t,"op,value",""))return fs_error("I55: put-finish-surface takes op and value");
        return fs_put(w,j,eng_json_member(j,t,"value"));
    }
    if(!strcmp(op,"delete-finish-surface")){
        if(!eng_json_keys(j,t,"op,id","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,true))return fs_error("I55: delete-finish-surface needs a positive id");
        return fs_delete(w,id);
    }
    /* PF-1 scope (I8a/I55): the panel-fill preview discloses finish surfaces only, so a panel-fill transaction must
     * not carry any other definition change (parameters, materials, sources) that confirm would commit unseen. */
    return fs_error("PF-1 scope (I8a/I55): panel-fill transactions accept only put-finish-surface and delete-finish-surface; "
                    "send %s through its own previewed transaction",op);
}
/* ---- scene records (I56 / R4) ---- */
static const char *fs_axis_word(Vector3 axis)
{
    for(size_t i=0;i<sizeof AXIS_WORDS/sizeof AXIS_WORDS[0];++i)
        if(AXIS_WORDS[i].axis.x==axis.x&&AXIS_WORDS[i].axis.y==axis.y&&AXIS_WORDS[i].axis.z==axis.z)return AXIS_WORDS[i].word;
    return "?";
}
static bool fs_scene_integrity(void)
{ return !fs_scene_required||(fs_scene_engineering&&fs_scene_parameters); }
static void fs_dump(const World *w,FILE *out)
{
    if(!fs_used(w))return;
    if(!engineering_used(w))fputs("requires engineering-spec/1\n",out);
    if(!w->parameters.card_count)fputs("requires parameters/1\n",out);
    fputs("requires " FS_CAPABILITY "\n",out);
    for(uint64_t i=0;i<w->finish_surfaces.count;++i){const FinishSurface *f=&w->finish_surfaces.items[i];
        fprintf(out,"finish-surface %u on boundary %u origin %lld %lld %lld u %s v %s n %s side %s",(unsigned)f->id,(unsigned)f->boundary_id,
            (long long)f->frame.origin.x,(long long)f->frame.origin.y,(long long)f->frame.origin.z,
            fs_axis_word(f->frame.axis_u),fs_axis_word(f->frame.axis_v),fs_axis_word(f->frame.normal),f->side>0?"+n":"-n");
        if(f->obstacle_count){fputs(" obstacles",out);for(uint32_t k=0;k<f->obstacle_count;++k){char text[16];fs_obstacle_text(&f->obstacles[k],text);fprintf(out," %s",text);}}
        fputs(" name-hex ",out);for(size_t k=0;f->name[k];++k)fprintf(out,"%02x",(unsigned char)f->name[k]);
        fputc('\n',out);
    }
}
static bool apply_finish_surface_line(const char *path,int line_no,char **t,int count,World *w)
{
    FinishSurface f;int at;memset(&f,0,sizeof f);
    if(!g_parsing_scene_file){scene_error(path,line_no,"D41/I55: finish-surface records load only with an atomic scene; edit through panel-fill-preview/confirm");return false;}
    if(!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){
        scene_error(path,line_no,"I56: finish-surface needs requires panel-fill/1, engineering-spec/1 and parameters/1 declared first");return false;}
    if(count<19||!parse_u32(t[1],&f.id)||strcmp(t[2],"on")||strcmp(t[3],"boundary")||!parse_u32(t[4],&f.boundary_id)||strcmp(t[5],"origin")||
       !parse_coord(t[6],&f.frame.origin.x)||!parse_coord(t[7],&f.frame.origin.y)||!parse_coord(t[8],&f.frame.origin.z)||
       strcmp(t[9],"u")||!lookup_axis(t[10],&f.frame.axis_u)||strcmp(t[11],"v")||!lookup_axis(t[12],&f.frame.axis_v)||
       strcmp(t[13],"n")||!lookup_axis(t[14],&f.frame.normal)||strcmp(t[15],"side")||(strcmp(t[16],"+n")&&strcmp(t[16],"-n")))goto invalid;
    f.side=t[16][0]=='+'?1:-1;at=17;
    if(at<count&&!strcmp(t[at],"obstacles")){
        for(++at;at<count&&strcmp(t[at],"name-hex");++at){
            if(f.obstacle_count==FS_OBSTACLE_MAX||!fs_obstacle_parse(t[at],&f.obstacles[f.obstacle_count]))goto invalid;
            ++f.obstacle_count;}
        if(!f.obstacle_count)goto invalid;
    }
    if(at+2!=count||strcmp(t[at],"name-hex")||!grid_system_read_name(t[at+1],f.name))goto invalid;
    if(fs_find(w,f.id)){scene_error(path,line_no,"I56: duplicate finish-surface record");return false;}
    if(!fs_obstacles_normalize(&f)||!fs_check(w,&f)){scene_error(path,line_no,g_engineering_error);return false;}
    if(w->finish_surfaces.count>=FS_MAX){scene_error(path,line_no,"I33 CAPACITY: finish surface limit reached");return false;}
    memcpy(&w->finish_surfaces.items[w->finish_surfaces.count++],&f,sizeof f);return true;
invalid:
    scene_error(path,line_no,"D41: finish-surface id on boundary B origin x y z u A v A n A side +n|-n [obstacles c<id>|b<id> ...] name-hex HEX");
    return false;
}
