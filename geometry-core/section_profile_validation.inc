/* Exact integer area partition: horizontal bands at every polygon vertex.
 * Rectangles cover the positive-area complement R\F, without sampling floats. */
static int sp_coord_compare(const void *a,const void *b)
{Coord x=*(const Coord*)a,y=*(const Coord*)b;return (x>y)-(x<y);}
static size_t sp_outside_regions(const PolygonLoop2 *p,const SurfaceRegion2 *r,SurfaceRegion2 out[SP_OUTSIDE_MAX])
{
    Coord ys[POLY_MAX_VERTICES+2];size_t ny=0,n=0;ys[ny++]=r->min_v;ys[ny++]=r->max_v;
    for(size_t i=0;i<p->count;++i)if(p->v[i].v>r->min_v&&p->v[i].v<r->max_v)ys[ny++]=p->v[i].v;
    qsort(ys,ny,sizeof(Coord),sp_coord_compare);
    for(size_t k=1;k<ny;++k){Coord lo=ys[k-1],hi=ys[k];if(lo==hi)continue;Coord y2=lo+hi,xs[POLY_MAX_VERTICES];size_t nx=0;
        for(size_t i=0;i<p->count;++i){SurfacePoint2 a=p->v[i],b=p->v[(i+1)%p->count];if(a.u==b.u&&2*coord_min(a.v,b.v)<y2&&y2<2*coord_max(a.v,b.v))xs[nx++]=a.u;}
        qsort(xs,nx,sizeof(Coord),sp_coord_compare);Coord cursor=r->min_u;
        for(size_t i=0;i+1<nx;i+=2){Coord a=coord_max(xs[i],r->min_u),b=coord_min(xs[i+1],r->max_u);if(a>=b)continue;
            if(cursor<a)out[n++]=(SurfaceRegion2){cursor,lo,a,hi};if(b>cursor)cursor=b;}
        if(cursor<r->max_u)out[n++]=(SurfaceRegion2){cursor,lo,r->max_u,hi};
    }
    return n;
}
static bool sp_intersection(const ProfileMember *a,const ProfileMember *b,SurfaceRegion2 *r)
{
    if(!a->resolved||!b->resolved||a->profile_id!=b->profile_id)return false;
    *r=(SurfaceRegion2){coord_max(a->rect.min_u,b->rect.min_u),coord_max(a->rect.min_v,b->rect.min_v),coord_min(a->rect.max_u,b->rect.max_u),coord_min(a->rect.max_v,b->rect.max_v)};
    return r->min_u<r->max_u&&r->min_v<r->max_v;
}
static void sp_first_error(char *first,size_t cap,const char *message)
{if(!first[0])snprintf(first,cap,"%s",message);}
/* An unrelated upstream parameter failure must not leave an old cached value
 * looking resolved. Evaluate this dimension's own dependency closure. */
static bool sp_resolve_dimension(World *w,const EngDimensionSource *source,const EngTarget *target,Coord *out)
{
    if(source->kind==ENG_PARAMETER){
        int at=parameter_field_index(w,source->parameter.parameter_id,source->parameter.field_id);
        if(at<0)return sp_error("I38 MISSING: parameter %u field %u",source->parameter.parameter_id,source->parameter.field_id);
        ParameterEval *eval=calloc(1,sizeof *eval);if(!eval)return sp_error("I32 CAPACITY: parameter evaluation memory");
        eval->w=w;bool ok=parameter_eval_field(eval,at);free(eval);
        if(!ok)return sp_error("%s",g_parameter_error);
    }
    return eng_resolve(w,source,target,UINT32_MAX,0,out,NULL,0);
}
static bool sp_rebuild(World *w,char *error,size_t capacity)
{
    SectionProfileState *s=&w->section_profiles;char first[256]={0};SurfaceRegion2 outside[SP_OUTSIDE_MAX];
    for(size_t i=0;i<s->member_count;++i){ProfileMember *m=&s->members[i];SectionProfile *p=sp_profile(w,m->profile_id);
        m->resolved=false;m->outside=false;m->range_error=false;m->missing_profile=!p;memset(m->source_error,0,sizeof m->source_error);
        if(!p){sp_error("I49: member %u references missing profile %u",m->id,m->profile_id);sp_first_error(first,sizeof first,g_engineering_error);}
        bool dimensions=true;
        if(m->panel){m->a=m->width;m->b=sp_panel_spec.thickness;}
        else for(int f=0;f<2;++f){EngTarget target={1,0,0,f};
            if(!sp_resolve_dimension(w,f?&m->b_source:&m->a_source,&target,f?&m->b:&m->a)){
                snprintf(m->source_error[f],sizeof m->source_error[f],"%s",g_engineering_error);sp_first_error(first,sizeof first,g_engineering_error);dimensions=false;}}
        if(!dimensions)continue;
        Coord width=m->rotated?m->b:m->a,height=m->rotated?m->a:m->b;
        m->rect=(SurfaceRegion2){m->u0,m->v0,m->u0+width,m->v0+height};m->resolved=true;
        m->range_error=!coord_in_range(m->rect.max_u)||!coord_in_range(m->rect.max_v);
        if(m->range_error){sp_error("I46/D1: member %u rectangle endpoint exceeds coordinate range",m->id);sp_first_error(first,sizeof first,g_engineering_error);}
        /* I44: exact area test. poly_contains_rect (corners on/in + no edge through the interior) also accepts a rectangle that exactly fills a notch. */ if(p&&sp_outside_regions(&p->outline,&m->rect,outside)){
            m->outside=true;sp_error("V_PROFILE_OUTSIDE I44: member %u profile %u rectangle is not contained",m->id,p->id);sp_first_error(first,sizeof first,g_engineering_error);}
    }
    for(size_t i=0;i<s->member_count;++i)for(size_t j=0;j<i;++j){SurfaceRegion2 overlap;if(sp_intersection(&s->members[i],&s->members[j],&overlap)){
        sp_error("V_PROFILE_OVERLAP I45: members %u,%u intersection [%lld,%lld]x[%lld,%lld]",s->members[j].id,s->members[i].id,(long long)overlap.min_u,(long long)overlap.max_u,(long long)overlap.min_v,(long long)overlap.max_v);sp_first_error(first,sizeof first,g_engineering_error);}}
    for(size_t i=0;i<s->run_count;++i){ProfileRun *r=&s->runs[i];SectionProfile *p=sp_profile(w,r->profile_id);EngTarget target={1,0,0,0};
        r->resolved=false;r->range_error=false;r->missing_profile=!p;r->length_error[0]=0;
        if(!p){sp_error("I49: run %u references missing profile %u",r->id,r->profile_id);sp_first_error(first,sizeof first,g_engineering_error);}
        r->length_resolved=sp_resolve_dimension(w,&r->length_source,&target,&r->length);
        if(!r->length_resolved){snprintf(r->length_error,sizeof r->length_error,"I47: %.180s",g_engineering_error);sp_first_error(first,sizeof first,r->length_error);}
        if(!sp_resolve_placement(w,r))sp_first_error(first,sizeof first,r->placement_error);
        if(p&&r->length_resolved&&r->placement_resolved)for(size_t v=0;v<p->outline.count;++v)for(int end=0;end<2;++end){
            Point3 point=sp_point(r,p->outline.v[v].u,p->outline.v[v].v,end?r->length:0);
            if(!coord_in_range(point.x)||!coord_in_range(point.y)||!coord_in_range(point.z)){r->range_error=true;sp_error("I47/I48/D1: run %u generated vertex [%lld,%lld,%lld] exceeds range",r->id,(long long)point.x,(long long)point.y,(long long)point.z);sp_first_error(first,sizeof first,g_engineering_error);}}
        r->resolved=p&&r->length_resolved&&r->placement_resolved&&!r->range_error;
    }
    if(first[0]){snprintf(g_engineering_error,sizeof g_engineering_error,"%s",first);snprintf(error,capacity,"%s",first);return false;}
    return true;
}
static void sp_capture_diagnostics(World *w)
{
    if(!sp_used(w))return;
    char saved[sizeof g_engineering_error],error[256];
    memcpy(saved,g_engineering_error,sizeof saved);
    sp_rebuild(w,error,sizeof error);
    memcpy(g_engineering_error,saved,sizeof saved);
}
