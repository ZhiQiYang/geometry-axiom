/* PF-H: D4 definitions and R41 reconstruction. All geometry is a disposable POD
 * cache; persistence contains only id, source fill and the typed h source. */
static const DerivedPlacement *dp_find(const World *w,uint32_t id)
{for(uint64_t i=0;i<w->finish_surfaces.host_count;++i)if(w->finish_surfaces.hosts[i].id==id)return &w->finish_surfaces.hosts[i];return NULL;}
static bool dp_parse(GeoJson *j,int t,DerivedPlacement *p)
{
    memset(p,0,sizeof *p);int h=geo_json_member(j,t,"h");
    if(!geo_json_keys(j,t,"id,fillId,h","")||!eng_u32(j,geo_json_member(j,t,"id"),&p->id,false)||
       !eng_u32(j,geo_json_member(j,t,"fillId"),&p->fill_id,true))return fs_error("D4: host requires id, fillId and a typed h source");
    if(geo_json_integer(j,h,&p->h.value))p->h.kind=ENG_LITERAL;
    else if(!eng_source_parse(j,h,&p->h,false))return false;
    if(p->h.kind==ENG_MATERIAL&&p->h.field!=ENG_B)return fs_error("D4: h material source must be timber B");
    if(!geo_json_canonical(j,t,p->definition,sizeof p->definition))return fs_capacity_error("I33 CAPACITY: D4 definition exceeds 1023 bytes");
    return true;
}
static bool dp_operation(World *w,GeoJson *j,int t,bool remove)
{
    DerivedPlacement d;uint32_t id;FinishSurfaceState *s=&w->finish_surfaces;
    if(remove){if(!geo_json_keys(j,t,"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,false))return fs_error("D4: delete-derived-placement needs id");}
    else {if(!geo_json_keys(j,t,"op,value","")||!dp_parse(j,geo_json_member(j,t,"value"),&d))return false;id=d.id;}
    size_t i=0;while(i<s->host_count&&s->hosts[i].id!=id)++i;
    const PlacementSurface *old=world_find_placement(w,id);
    if(remove){
        if(i==s->host_count)return fs_error("D4: derived placement does not exist");
        memmove(&s->hosts[i],&s->hosts[i+1],(s->host_count-i-1)*sizeof d);memset(&s->hosts[--s->host_count],0,sizeof d);
        for(size_t k=0;k<w->placement_count;++k)if(w->placements[k].id==id){memmove(&w->placements[k],&w->placements[k+1],(w->placement_count-k-1)*sizeof *old);memset(&w->placements[--w->placement_count],0,sizeof *old);break;}
        asm_remove_position(w,CANVAS_POS_PLACEMENT,id);
        return true;
    }
    if(old&&!old->derived_fill_id)return fs_error("D4: placement variant cannot change");
    if(i<s->host_count&&s->hosts[i].fill_id!=d.fill_id)return fs_error("D4: source fill is immutable");
    for(size_t k=0;k<s->host_count;++k)if(k!=i&&s->hosts[k].fill_id==d.fill_id)return fs_error("D4: one derived placement per panel fill");
    if(i==s->host_count){
        if(i==FS_MAX||w->placement_count==WORLD_MAX_PLACEMENTS)return fs_capacity_error("I33 CAPACITY: derived placement limit reached");
        ++s->host_count;PlacementSurface *p=&w->placements[w->placement_count++];memset(p,0,sizeof *p);p->id=id;p->derived_fill_id=d.fill_id;
    }
    s->hosts[i]=d;return true;
}
typedef struct {SurfacePoint2 a,b;EdgeFixity fixity;char name[32];} DpSource;
#define DP_SOURCE_MAX ((POLY_MAX_HOLES+1)*POLY_MAX_VERTICES+4*FS_OBSTACLE_MAX)
static size_t dp_sources(const World *w,const PfLayout *d,DpSource *out)
{
    size_t n=0;const SpaceBoundarySurface *f=world_find_boundary(w,d->finish->boundary_id);int side=d->finish->side;
    for(size_t h=0;h<=f->hole_count;++h){const PolygonLoop2 *l=h?&f->holes[h-1]:&f->outline;
        for(size_t e=0;e<l->count;++e){DpSource *s=&out[n++];s->a=l->v[e];s->b=l->v[(e+1)%l->count];s->a.v*=side;s->b.v*=side;s->fixity=l->fixity[e];
            if(h)snprintf(s->name,sizeof s->name,"h%zue%zu",h-1,e);else snprintf(s->name,sizeof s->name,"e%zu",e);}}
    static const char *sides[]={"u-","u+","v-","v+"};
    for(uint32_t i=0;i<d->finish->obstacle_count;++i)if(d->cuts[i]){
        const Coord *r=d->obstacles[i].rect;Coord lo=coord_min(side*r[1],side*r[3]),hi=coord_max(side*r[1],side*r[3]);char ref[16];fs_obstacle_text(&d->finish->obstacles[i],ref);
        SurfacePoint2 a[4]={{r[0],lo},{r[2],lo},{r[0],lo},{r[0],hi}},b[4]={{r[0],hi},{r[2],hi},{r[2],lo},{r[2],hi}};
        for(int k=0;k<4;++k){DpSource *s=&out[n++];s->a=a[k];s->b=b[k];s->fixity=EDGE_FIXED;snprintf(s->name,sizeof s->name,"%s:%s",ref,sides[k]);}}
    return n;
}
static bool dp_overlap(SurfacePoint2 a,SurfacePoint2 b,SurfacePoint2 c,SurfacePoint2 d,Coord *lo,Coord *hi)
{
    bool vertical=a.u==b.u;if(vertical!=(c.u==d.u)||(vertical?a.u!=c.u:a.v!=c.v))return false;
    Coord x=vertical?a.v:a.u,y=vertical?b.v:b.u,z=vertical?c.v:c.u,q=vertical?d.v:d.u;
    *lo=coord_max(coord_min(x,y),coord_min(z,q));*hi=coord_min(coord_max(x,y),coord_max(z,q));return *lo<*hi;
}
static EdgeFixity dp_fixity(const DpSource *s,size_t n,SurfacePoint2 a,SurfacePoint2 b)
{
    /* F provenance precedes obstacle provenance. Clipping splits at every source
     * endpoint, so every retained elementary edge is wholly covered. */
    for(size_t i=0;i<n;++i){Coord lo,hi;if(s[i].name[0]!='e'&&s[i].name[0]!='h')break;
        if(dp_overlap(a,b,s[i].a,s[i].b,&lo,&hi))return s[i].fixity;}
    return EDGE_FIXED;
}
static bool dp_loop(const PfLoop *raw,int side,const DpSource *sources,size_t ns,PolygonLoop2 *out)
{
    size_t n=raw->count;SurfacePoint2 *v=malloc(n*sizeof *v);EdgeFixity *fix=malloc(n*sizeof *fix);
    if(!v||!fix){free(v);free(fix);return fs_capacity_error("I33 CAPACITY: R41 loop workspace unavailable");}
    for(size_t i=0;i<n;++i){v[i]=raw->points[side>0?i:(n-i)%n];v[i].v*=side;}
    for(size_t i=0;i<n;++i)fix[i]=dp_fixity(sources,ns,v[i],v[(i+1)%n]);
    memset(out,0,sizeof *out);bool ok=true;
    for(size_t i=0;i<n;++i){size_t prev=(i+n-1)%n,next=(i+1)%n;
        if(fix[prev]==fix[i]&&((v[prev].u==v[i].u&&v[i].u==v[next].u)||(v[prev].v==v[i].v&&v[i].v==v[next].v)))continue;
        if(out->count==POLY_MAX_VERTICES){ok=fs_capacity_error("I33 CAPACITY: R41 loop exceeds %d maximal edges",POLY_MAX_VERTICES);break;}
        out->v[out->count]=v[i];out->fixity[out->count++]=fix[i];}
    free(v);free(fix);if(!ok)return false;
    PolygonLoop2 original=*out;size_t first=0;
    for(size_t i=1;i<out->count;++i)if(pf_point_order(out->v[i],out->v[first])<0)first=i;
    for(size_t i=0;i<out->count;++i){out->v[i]=original.v[(first+i)%out->count];out->fixity[i]=original.fixity[(first+i)%out->count];}
    return true;
}
static bool dp_values(const World *w,const PlacementSurface *p,PfLayout *d)
{
    const DerivedPlacement *def=dp_find(w,p->id);const PanelFill *fill=def?pf_find(w,def->fill_id):NULL;
    if(!fill)return fs_error("I55/D4: derived placement %u source fill is missing",p->id);
    memset(d,0,sizeof *d);if(!pf_values(w,fill,d))return false;
    for(uint32_t i=0;i<d->finish->obstacle_count;++i)d->cuts[i]=d->obstacles[i].relation==FS_INTERIOR&&d->obstacles[i].q[0]<d->t+p->derived_h&&d->obstacles[i].q[1]>d->t;
    return true;
}
static bool dp_rebuild(World *w)
{
    for(uint64_t i=0;i<w->finish_surfaces.host_count;++i){const DerivedPlacement *def=&w->finish_surfaces.hosts[i];PlacementSurface *p=NULL;
        for(size_t k=0;k<w->placement_count;++k)if(w->placements[k].id==def->id)p=&w->placements[k];
        if(!p||!p->derived_fill_id)return fs_error("D4: derived placement variant or identity missing");
        Coord h;EngTarget target={1,def->id,0,1};if(!eng_resolve(w,&def->h,&target,def->id,0,&h,NULL,0))return false;
        memset(p,0,sizeof *p);p->id=def->id;p->derived_fill_id=def->fill_id;p->derived_h=h;
        PfLayout d;if(!dp_values(w,p,&d))return false;
        p->frame=d.finish->frame;p->frame.axis_v=(d.finish->side>0?p->frame.axis_v:vector_negate(p->frame.axis_v));p->frame.normal=(d.finish->side>0?p->frame.normal:vector_negate(p->frame.normal));
        p->frame.origin.x+=d.t*p->frame.normal.x;p->frame.origin.y+=d.t*p->frame.normal.y;p->frame.origin.z+=d.t*p->frame.normal.z;
        if(!coord_in_range(p->frame.origin.x)||!coord_in_range(p->frame.origin.y)||!coord_in_range(p->frame.origin.z))return fs_capacity_error("D1/I33 CAPACITY: R41 back frame exceeds D1");
        const SpaceBoundarySurface *f=world_find_boundary(w,d.finish->boundary_id);SurfaceRegion2 bounds;polygon_loop_bounds(&f->outline,&bounds);
        d.tiles=calloc(1,sizeof *d.tiles);if(!d.tiles)return fs_capacity_error("I33 CAPACITY: R41 workspace unavailable");d.count=1;d.keep_collinear=true;
        PfTile *tile=d.tiles;tile->body[0]=bounds.min_u;tile->body[1]=bounds.min_v;tile->body[2]=bounds.max_u;tile->body[3]=bounds.max_v;
        bool ok=pf_clip(w,&d,tile);DpSource *sources=calloc(DP_SOURCE_MAX,sizeof *sources);if(!sources)ok=fs_capacity_error("I33 CAPACITY: R41 source workspace unavailable");size_t ns=ok?dp_sources(w,&d,sources):0;
        if(ok&&tile->count>DP_COMPONENT_MAX)ok=fs_capacity_error("I33 CAPACITY: R41 component limit is %d",DP_COMPONENT_MAX);
        for(size_t c=0;c<tile->count&&ok;++c){PfFragment *fragment=&tile->fragments[c];SpaceBoundarySurface *b=&p->components[c];b->id=p->id;
            if(fragment->count>POLY_MAX_HOLES+1){ok=fs_capacity_error("I33 CAPACITY: R41 hole limit is %d",POLY_MAX_HOLES);break;}
            for(size_t l=0;l<fragment->count&&ok;++l){PfLoop *loop=&fragment->loops[l];
                if(l&&!loop->hole){ok=fs_error("R41/R3: component has multiple outer loops");break;}
                ok=dp_loop(loop,d.finish->side,sources,ns,l?&b->holes[b->hole_count++]:&b->outline);}
            if(ok&&!boundary_is_valid(b))ok=fs_error("R41/R3: derived component has non-simple or touching outer/hole boundaries");
            if(ok)++p->component_count;}
        free(sources);pf_free(&d);if(!ok)return false;
        for(size_t c=0;c<p->component_count;++c)for(size_t j=c+1;j<p->component_count;++j)
            if(pf_point_order(p->components[j].outline.v[0],p->components[c].outline.v[0])<0){SpaceBoundarySurface swap=p->components[c];p->components[c]=p->components[j];p->components[j]=swap;}
        /* Reject the whole candidate if a complete persistent key cannot be
         * represented; readers must never silently substitute a truncated key. */
        for(size_t c=0;c<p->component_count;++c){const SpaceBoundarySurface *b=&p->components[c];for(size_t k=0;k<=b->hole_count;++k){const PolygonLoop2 *l=k?&b->holes[k-1]:&b->outline;
            for(size_t e=0;e<l->count;++e){char key[512];if(!dp_edge_key(w,p,c,k?(int)k-1:-1,e,key,sizeof key))return false;}}}
    }
    return true;
}
typedef struct {Coord lo,hi;} DpInterval;
static int dp_interval_order(const void *a,const void *b)
{const DpInterval *x=a,*y=b;return x->lo!=y->lo?(x->lo<y->lo?-1:1):x->hi<y->hi?-1:x->hi>y->hi;}
/* A source's segment/total counts refer to maximal retained intervals across ALL
 * components. Consequently a remote split invalidates old keys as R41 requires. */
static bool dp_edge_key(const World *w,const PlacementSurface *p,size_t component,int hole,size_t edge,char *out,size_t cap)
{
    if(!p||!p->derived_fill_id||component>=p->component_count)return false;
    const SpaceBoundarySurface *b=&p->components[component];if(hole>=(int)b->hole_count)return false;
    const PolygonLoop2 *loop=hole<0?&b->outline:&b->holes[hole];if(edge>=loop->count)return false;
    SurfacePoint2 a=loop->v[edge],z=loop->v[(edge+1)%loop->count];bool forward=a.u==z.u?a.v<z.v:a.u<z.u;
    PfLayout d;if(!dp_values(w,p,&d))return false;DpSource *sources=calloc(DP_SOURCE_MAX,sizeof *sources);
    size_t capacity=DP_COMPONENT_MAX*(POLY_MAX_HOLES+1)*POLY_MAX_VERTICES;
    DpInterval *intervals=malloc(capacity*sizeof *intervals);
    typedef struct {Coord first;size_t source;unsigned segment,total;} Part;
    Part *parts=calloc(DP_SOURCE_MAX,sizeof *parts);if(!sources||!intervals||!parts){free(sources);free(intervals);free(parts);return fs_capacity_error("I33 CAPACITY: R41 key workspace unavailable");}
    size_t ns=dp_sources(w,&d,sources),np=0;
    for(size_t s=0;s<ns;++s){Coord lo,hi;if(!dp_overlap(a,z,sources[s].a,sources[s].b,&lo,&hi))continue;size_t n=0;
        for(size_t c=0;c<p->component_count;++c){const SpaceBoundarySurface *region=&p->components[c];for(size_t h=0;h<=region->hole_count;++h){const PolygonLoop2 *l=h?&region->holes[h-1]:&region->outline;
            for(size_t e=0;e<l->count;++e){Coord x,y;if(dp_overlap(l->v[e],l->v[(e+1)%l->count],sources[s].a,sources[s].b,&x,&y))intervals[n++]=(DpInterval){x,y};}}}
        qsort(intervals,n,sizeof *intervals,dp_interval_order);size_t total=0;
        for(size_t k=0;k<n;++k)if(total&&intervals[k].lo<=intervals[total-1].hi)intervals[total-1].hi=coord_max(intervals[total-1].hi,intervals[k].hi);else intervals[total++]=intervals[k];
        for(size_t k=0;k<total;++k)if(lo<intervals[k].hi&&hi>intervals[k].lo){bool direction=sources[s].a.u==sources[s].b.u?sources[s].a.v<sources[s].b.v:sources[s].a.u<sources[s].b.u;
            parts[np++]=(Part){forward?lo:-hi,s,(unsigned)(direction?k:total-1-k),(unsigned)total};break;}
    }
    for(size_t i=1;i<np;++i){Part x=parts[i];size_t k=i;while(k&&(parts[k-1].first>x.first||(parts[k-1].first==x.first&&parts[k-1].source>x.source))){parts[k]=parts[k-1];--k;}parts[k]=x;}
    size_t used=0;bool ok=np>0&&cap>2;if(ok)out[used++]='[';
    for(size_t i=0;i<np&&ok;++i){int n=snprintf(out+used,cap-used,"%s[\"%s\",%u,%u]",i?",":"",sources[parts[i].source].name,parts[i].segment,parts[i].total);if(n<0||(size_t)n>=cap-used)ok=false;else used+=(size_t)n;}
    if(ok&&used+2<=cap){out[used++]=']';out[used]=0;}else ok=false;
    free(sources);free(intervals);free(parts);return ok||fs_capacity_error("I33 CAPACITY: R41 key exceeds supported size");
}
static bool dp_edge_resolve(const World *w,const PlacementSurface *p,const char *key,int *hole,int *edge)
{
    size_t matches=0;char candidate[512];
    if(!p||!p->derived_fill_id)return false;
    for(size_t c=0;c<p->component_count;++c){const SpaceBoundarySurface *b=&p->components[c];for(size_t h=0;h<=b->hole_count;++h){const PolygonLoop2 *l=h?&b->holes[h-1]:&b->outline;
        for(size_t e=0;e<l->count;++e){if(!dp_edge_key(w,p,c,h?(int)h-1:-1,e,candidate,sizeof candidate))return false;
            if(!strcmp(key,candidate)){++matches;*hole=h?(int)(c*POLY_MAX_HOLES+h-1):-1;*edge=h?(int)e:(int)(c*POLY_MAX_VERTICES+e);}}}}
    return matches==1||fs_error("R41: key %.160s matches %zu derived edges; exactly one is required",key,matches);
}
static void dp_dump(const World *w,FILE *out)
{for(uint64_t i=0;i<w->finish_surfaces.host_count;++i){const DerivedPlacement *p=&w->finish_surfaces.hosts[i];fprintf(out,"derived-placement %u definition-hex ",p->id);for(const unsigned char *c=(const unsigned char*)p->definition;*c;++c)fprintf(out,"%02x",*c);fputc('\n',out);}}
static bool apply_derived_placement_line(const char *path,int line,char **t,int count,World *w)
{
    if(!g_parsing_scene_file||!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){scene_error(path,line,"I56: derived-placement requires an atomic scene with all three capabilities");return false;}
    uint32_t id;char definition[1024];size_t n=strlen(t[3]);
    if(count!=4||strcmp(t[2],"definition-hex")||!parse_u32(t[1],&id)||!n||n%2||n/2>=sizeof definition)goto invalid;
    for(size_t i=0;i<n/2;++i){int a=grid_system_hex_digit(t[3][2*i]),b=grid_system_hex_digit(t[3][2*i+1]);if(a<0||b<0||!(a*16+b))goto invalid;definition[i]=(char)(a*16+b);}definition[n/2]=0;
    GeoJson j;DerivedPlacement p;bool ok=app_json_parse(&j,definition);if(ok)ok=dp_parse(&j,0,&p);geo_json_free(&j);
    if(!ok){scene_error(path,line,g_engineering_error);return false;}
    if(id!=p.id||dp_find(w,id)||world_find_placement(w,id)){scene_error(path,line,"D4/I56: derived placement id mismatch, duplicate or variant collision");return false;}
    for(uint64_t i=0;i<w->finish_surfaces.host_count;++i)if(w->finish_surfaces.hosts[i].fill_id==p.fill_id){scene_error(path,line,"D4: one derived placement per fill");return false;}
    if(w->finish_surfaces.host_count==FS_MAX||w->placement_count==WORLD_MAX_PLACEMENTS){scene_error(path,line,"I33 CAPACITY: derived placement limit reached");return false;}
    w->finish_surfaces.hosts[w->finish_surfaces.host_count++]=p;PlacementSurface *host=&w->placements[w->placement_count++];memset(host,0,sizeof *host);host->id=id;host->derived_fill_id=p.fill_id;
    if(!dp_rebuild(w)){scene_error(path,line,g_engineering_error);return false;}return true;
invalid:scene_error(path,line,"D4: derived-placement id definition-hex HEX");return false;
}
