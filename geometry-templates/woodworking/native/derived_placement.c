/* D4/R41 woodworking policy. H supplies/stages value records; all clipping,
 * overlap and boundary validity calculations use public K geometry. */
#include "derived_placement.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GeoCoord wood_dp_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord wood_dp_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
const DerivedPlacement *wood_dp_find(const WoodDerivedContext *w,uint32_t id)
{for(uint64_t i=0;i<w->finish.state->host_count;++i)if(w->finish.state->hosts[i].id==id)return &w->finish.state->hosts[i];return NULL;}
bool wood_dp_parse(const WoodDerivedContext *w,GeoJson *j,int t,DerivedPlacement *p)
{
    memset(p,0,sizeof *p);int h=geo_json_member(j,t,"h");
    if(!geo_json_keys(j,t,"id,fillId,h","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&p->id,false)||
       !wood_eng_u32(j,geo_json_member(j,t,"fillId"),&p->fill_id,true))return wood_fs_error(&w->finish,"D4: host requires id, fillId and a typed h source");
    if(geo_json_integer(j,h,&p->h.value))p->h.kind=ENG_LITERAL;
    else if(!wood_eng_source_parse((WoodEngineeringContext *)&w->finish.engineering,j,h,&p->h,false))return false;
    if(p->h.kind==ENG_MATERIAL&&p->h.field!=ENG_B)return wood_fs_error(&w->finish,"D4: h material source must be timber B");
    if(!geo_json_canonical(j,t,p->definition,sizeof p->definition))return wood_fs_capacity_error(&w->finish,"I33 CAPACITY: D4 definition exceeds 1023 bytes");
    return true;
}
bool wood_dp_operation(WoodDerivedContext *w,GeoJson *j,int t,bool remove)
{
    DerivedPlacement d;uint32_t id;FinishSurfaceState *s=w->finish.state;
    if(remove){if(!geo_json_keys(j,t,"op,id","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,false))return wood_fs_error(&w->finish,"D4: delete-derived-placement needs id");}
    else {if(!geo_json_keys(j,t,"op,value","")||!wood_dp_parse(w,j,geo_json_member(j,t,"value"),&d))return false;id=d.id;}
    size_t i=0;while(i<s->host_count&&s->hosts[i].id!=id)++i;
    WoodDerivedValue prior;const WoodDerivedValue *old=w->placement_read(w->finish.user,id,&prior)?&prior:NULL;
    if(remove){
        if(i==s->host_count)return wood_fs_error(&w->finish,"D4: derived placement does not exist");
        memmove(&s->hosts[i],&s->hosts[i+1],(s->host_count-i-1)*sizeof d);memset(&s->hosts[--s->host_count],0,sizeof d);
        (void)w->placement_remove(w->finish.user,id);
        w->remove_canvas_position(w->finish.user,id);
        return true;
    }
    if(old&&!old->derived_fill_id)return wood_fs_error(&w->finish,"D4: placement variant cannot change");
    if(i<s->host_count&&s->hosts[i].fill_id!=d.fill_id)return wood_fs_error(&w->finish,"D4: source fill is immutable");
    for(size_t k=0;k<s->host_count;++k)if(k!=i&&s->hosts[k].fill_id==d.fill_id)return wood_fs_error(&w->finish,"D4: one derived placement per panel fill");
    if(i==s->host_count){
        if(i==FS_MAX||w->placement_count(w->finish.user)==w->placement_capacity)return wood_fs_capacity_error(&w->finish,"I33 CAPACITY: derived placement limit reached");
        ++s->host_count;WoodDerivedValue value={0};value.id=id;value.derived_fill_id=d.fill_id;if(!w->placement_write(w->finish.user,&value))return false;
    }
    s->hosts[i]=d;return true;
}
typedef struct {GeoPoint2 a,b;WoodEdgeFixity fixity;char name[32];} WoodDpSource;
#define WOOD_DP_SOURCE_MAX ((GEO_REGION_MAX_HOLES+1)*GEO_LOOP_MAX_VERTICES+4*FS_OBSTACLE_MAX)
static size_t wood_dp_sources(const WoodDerivedContext *w,const WoodFinishLayout *d,WoodDpSource *out)
{
    size_t n=0;WoodBoundaryRegion source;w->finish.boundary(w->finish.user,d->finish->boundary_id,&source);const WoodBoundaryRegion *f=&source;int side=d->finish->side;
    for(size_t h=0;h<=f->hole_count;++h){const WoodBoundaryLoop *l=h?&f->holes[h-1]:&f->outline;
        for(size_t e=0;e<l->count;++e){WoodDpSource *s=&out[n++];s->a=l->v[e];s->b=l->v[(e+1)%l->count];s->a.v*=side;s->b.v*=side;s->fixity=l->fixity[e];
            if(h)snprintf(s->name,sizeof s->name,"h%zue%zu",h-1,e);else snprintf(s->name,sizeof s->name,"e%zu",e);}}
    static const char *sides[]={"u-","u+","v-","v+"};
    for(uint32_t i=0;i<d->finish->obstacle_count;++i)if(d->cuts[i]){
        const GeoCoord *r=d->obstacles[i].rect;GeoCoord lo=wood_dp_min(side*r[1],side*r[3]),hi=wood_dp_max(side*r[1],side*r[3]);char ref[16];wood_fs_obstacle_text(&d->finish->obstacles[i],ref);
        GeoPoint2 a[4]={{r[0],lo},{r[2],lo},{r[0],lo},{r[0],hi}},b[4]={{r[0],hi},{r[2],hi},{r[2],lo},{r[2],hi}};
        for(int k=0;k<4;++k){WoodDpSource *s=&out[n++];s->a=a[k];s->b=b[k];s->fixity=WOOD_EDGE_FIXED;snprintf(s->name,sizeof s->name,"%s:%s",ref,sides[k]);}}
    return n;
}
static WoodEdgeFixity wood_dp_fixity(const WoodDpSource *s,size_t n,GeoPoint2 a,GeoPoint2 b)
{
    /* F provenance precedes obstacle provenance. Clipping splits at every source
     * endpoint, so every retained elementary edge is wholly covered. */
    for(size_t i=0;i<n;++i){GeoCoord lo,hi;if(s[i].name[0]!='e'&&s[i].name[0]!='h')break;
        if(geo_collinear_segment_overlap(a,b,s[i].a,s[i].b,&lo,&hi))return s[i].fixity;}
    return WOOD_EDGE_FIXED;
}
static bool wood_dp_loop(const WoodDerivedContext *w,const WoodPanelLoop *raw,int side,const WoodDpSource *sources,size_t ns,WoodBoundaryLoop *out)
{
    size_t n=raw->count;GeoPoint2 *v=malloc(n*sizeof *v);WoodEdgeFixity *fix=malloc(n*sizeof *fix);
    if(!v||!fix){free(v);free(fix);return wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 loop workspace unavailable");}
    for(size_t i=0;i<n;++i){v[i]=raw->points[side>0?i:(n-i)%n];v[i].v*=side;}
    for(size_t i=0;i<n;++i)fix[i]=wood_dp_fixity(sources,ns,v[i],v[(i+1)%n]);
    memset(out,0,sizeof *out);bool ok=true;
    for(size_t i=0;i<n;++i){size_t prev=(i+n-1)%n,next=(i+1)%n;
        if(fix[prev]==fix[i]&&((v[prev].u==v[i].u&&v[i].u==v[next].u)||(v[prev].v==v[i].v&&v[i].v==v[next].v)))continue;
        if(out->count==GEO_LOOP_MAX_VERTICES){ok=wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 loop exceeds %d maximal edges",GEO_LOOP_MAX_VERTICES);break;}
        out->v[out->count]=v[i];out->fixity[out->count++]=fix[i];}
    free(v);free(fix);if(!ok)return false;
    WoodBoundaryLoop original=*out;size_t first=0;
    for(size_t i=1;i<out->count;++i)if(wood_pf_point_order(out->v[i],out->v[first])<0)first=i;
    for(size_t i=0;i<out->count;++i){out->v[i]=original.v[(first+i)%out->count];out->fixity[i]=original.fixity[(first+i)%out->count];}
    return true;
}
static bool wood_dp_values(const WoodDerivedContext *w,const WoodDerivedValue *p,WoodFinishLayout *d)
{
    const DerivedPlacement *def=wood_dp_find(w,p->id);const PanelFill *fill=def?wood_pf_find(&w->finish,def->fill_id):NULL;
    if(!fill)return wood_fs_error(&w->finish,"I55/D4: derived placement %u source fill is missing",p->id);
    memset(d,0,sizeof *d);if(!wood_pf_values(&w->finish,fill,d))return false;
    for(uint32_t i=0;i<d->finish->obstacle_count;++i)d->cuts[i]=d->obstacles[i].relation==FS_INTERIOR&&d->obstacles[i].q[0]<d->t+p->derived_h&&d->obstacles[i].q[1]>d->t;
    return true;
}
bool wood_dp_rebuild(WoodDerivedContext *w)
{
    for(uint64_t i=0;i<w->finish.state->host_count;++i){const DerivedPlacement *def=&w->finish.state->hosts[i];WoodDerivedValue value;
        WoodDerivedValue *p=w->placement_read(w->finish.user,def->id,&value)?&value:NULL;
        if(!p||!p->derived_fill_id)return wood_fs_error(&w->finish,"D4: derived placement variant or identity missing");
        GeoCoord h;EngTarget target={1,def->id,0,1};if(!wood_eng_resolve(&w->finish.engineering,&def->h,&target,def->id,0,&h,NULL,0))return false;
        memset(p,0,sizeof *p);p->id=def->id;p->derived_fill_id=def->fill_id;p->derived_h=h;
        WoodFinishLayout d;if(!wood_dp_values(w,p,&d))return false;
        p->frame=d.finish->frame;p->frame.axis_v=(d.finish->side>0?p->frame.axis_v:geo_vector_negate(p->frame.axis_v));p->frame.normal=(d.finish->side>0?p->frame.normal:geo_vector_negate(p->frame.normal));
        p->frame.origin.x+=d.t*p->frame.normal.x;p->frame.origin.y+=d.t*p->frame.normal.y;p->frame.origin.z+=d.t*p->frame.normal.z;
        if(!geo_coord_in_range(p->frame.origin.x)||!geo_coord_in_range(p->frame.origin.y)||!geo_coord_in_range(p->frame.origin.z))return wood_fs_capacity_error(&w->finish,"D1/I33 CAPACITY: R41 back frame exceeds D1");
        WoodBoundaryRegion source;w->finish.boundary(w->finish.user,d.finish->boundary_id,&source);const WoodBoundaryRegion *f=&source;GeoRect2 bounds;GeoLoop2View outline={f->outline.v,f->outline.count};geo_loop_bbox(&outline,&bounds.min_u,&bounds.min_v,&bounds.max_u,&bounds.max_v);
        d.layout.tiles=calloc(1,sizeof *d.layout.tiles);if(!d.layout.tiles)return wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 workspace unavailable");d.layout.count=1;d.keep_collinear=true;
        WoodPanelTile *tile=d.layout.tiles;tile->body[0]=bounds.min_u;tile->body[1]=bounds.min_v;tile->body[2]=bounds.max_u;tile->body[3]=bounds.max_v;
        bool ok=wood_pf_clip(&w->finish,&d,tile);WoodDpSource *sources=calloc(WOOD_DP_SOURCE_MAX,sizeof *sources);if(!sources)ok=wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 source workspace unavailable");size_t ns=ok?wood_dp_sources(w,&d,sources):0;
        if(ok&&tile->count>WOOD_DERIVED_COMPONENT_MAX)ok=wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 component limit is %d",WOOD_DERIVED_COMPONENT_MAX);
        for(size_t c=0;c<tile->count&&ok;++c){WoodPanelFragment *fragment=&tile->fragments[c];WoodBoundaryRegion *b=&p->components[c];b->id=p->id;
            if(fragment->count>GEO_REGION_MAX_HOLES+1){ok=wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 hole limit is %d",GEO_REGION_MAX_HOLES);break;}
            for(size_t l=0;l<fragment->count&&ok;++l){WoodPanelLoop *loop=&fragment->loops[l];
                if(l&&!loop->hole){ok=wood_fs_error(&w->finish,"R41/R3: component has multiple outer loops");break;}
                ok=wood_dp_loop(w,loop,d.finish->side,sources,ns,l?&b->holes[b->hole_count++]:&b->outline);}
            if(ok){GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView region=wood_pf_region_view(b,holes);
                if(!geo_region_is_valid(&region))ok=wood_fs_error(&w->finish,"R41/R3: derived component has non-simple or touching outer/hole boundaries");}
            if(ok)++p->component_count;}
        free(sources);wood_pf_free(&d);if(!ok)return false;
        for(size_t c=0;c<p->component_count;++c)for(size_t j=c+1;j<p->component_count;++j)
            if(wood_pf_point_order(p->components[j].outline.v[0],p->components[c].outline.v[0])<0){WoodBoundaryRegion swap=p->components[c];p->components[c]=p->components[j];p->components[j]=swap;}
        /* Reject the whole candidate if a complete persistent key cannot be
         * represented; readers must never silently substitute a truncated key. */
        for(size_t c=0;c<p->component_count;++c){const WoodBoundaryRegion *b=&p->components[c];for(size_t k=0;k<=b->hole_count;++k){const WoodBoundaryLoop *l=k?&b->holes[k-1]:&b->outline;
            for(size_t e=0;e<l->count;++e){char key[512];if(!wood_dp_edge_key(w,p,c,k?(int)k-1:-1,e,key,sizeof key))return false;}}}
        if(!w->placement_write(w->finish.user,p))return false;
    }
    return true;
}
typedef struct {GeoCoord lo,hi;} WoodDpInterval;
static int wood_dp_interval_order(const void *a,const void *b)
{const WoodDpInterval *x=a,*y=b;return x->lo!=y->lo?(x->lo<y->lo?-1:1):x->hi<y->hi?-1:x->hi>y->hi;}
/* A source's segment/total counts refer to maximal retained intervals across ALL
 * components. Consequently a remote split invalidates old keys as R41 requires. */
bool wood_dp_edge_key(const WoodDerivedContext *w,const WoodDerivedValue *p,size_t component,int hole,size_t edge,char *out,size_t cap)
{
    if(!p||!p->derived_fill_id||component>=p->component_count)return false;
    const WoodBoundaryRegion *b=&p->components[component];if(hole>=(int)b->hole_count)return false;
    const WoodBoundaryLoop *loop=hole<0?&b->outline:&b->holes[hole];if(edge>=loop->count)return false;
    GeoPoint2 a=loop->v[edge],z=loop->v[(edge+1)%loop->count];bool forward=a.u==z.u?a.v<z.v:a.u<z.u;
    WoodFinishLayout d;if(!wood_dp_values(w,p,&d))return false;WoodDpSource *sources=calloc(WOOD_DP_SOURCE_MAX,sizeof *sources);
    size_t capacity=WOOD_DERIVED_COMPONENT_MAX*(GEO_REGION_MAX_HOLES+1)*GEO_LOOP_MAX_VERTICES;
    WoodDpInterval *intervals=malloc(capacity*sizeof *intervals);
    typedef struct {GeoCoord first;size_t source;unsigned segment,total;} Part;
    Part *parts=calloc(WOOD_DP_SOURCE_MAX,sizeof *parts);if(!sources||!intervals||!parts){free(sources);free(intervals);free(parts);return wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 key workspace unavailable");}
    size_t ns=wood_dp_sources(w,&d,sources),np=0;
    for(size_t s=0;s<ns;++s){GeoCoord lo,hi;if(!geo_collinear_segment_overlap(a,z,sources[s].a,sources[s].b,&lo,&hi))continue;size_t n=0;
        for(size_t c=0;c<p->component_count;++c){const WoodBoundaryRegion *region=&p->components[c];for(size_t h=0;h<=region->hole_count;++h){const WoodBoundaryLoop *l=h?&region->holes[h-1]:&region->outline;
            for(size_t e=0;e<l->count;++e){GeoCoord x,y;if(geo_collinear_segment_overlap(l->v[e],l->v[(e+1)%l->count],sources[s].a,sources[s].b,&x,&y))intervals[n++]=(WoodDpInterval){x,y};}}}
        qsort(intervals,n,sizeof *intervals,wood_dp_interval_order);size_t total=0;
        for(size_t k=0;k<n;++k)if(total&&intervals[k].lo<=intervals[total-1].hi)intervals[total-1].hi=wood_dp_max(intervals[total-1].hi,intervals[k].hi);else intervals[total++]=intervals[k];
        for(size_t k=0;k<total;++k)if(lo<intervals[k].hi&&hi>intervals[k].lo){bool direction=sources[s].a.u==sources[s].b.u?sources[s].a.v<sources[s].b.v:sources[s].a.u<sources[s].b.u;
            parts[np++]=(Part){forward?lo:-hi,s,(unsigned)(direction?k:total-1-k),(unsigned)total};break;}
    }
    for(size_t i=1;i<np;++i){Part x=parts[i];size_t k=i;while(k&&(parts[k-1].first>x.first||(parts[k-1].first==x.first&&parts[k-1].source>x.source))){parts[k]=parts[k-1];--k;}parts[k]=x;}
    size_t used=0;bool ok=np>0&&cap>2;if(ok)out[used++]='[';
    for(size_t i=0;i<np&&ok;++i){int n=snprintf(out+used,cap-used,"%s[\"%s\",%u,%u]",i?",":"",sources[parts[i].source].name,parts[i].segment,parts[i].total);if(n<0||(size_t)n>=cap-used)ok=false;else used+=(size_t)n;}
    if(ok&&used+2<=cap){out[used++]=']';out[used]=0;}else ok=false;
    free(sources);free(intervals);free(parts);return ok||wood_fs_capacity_error(&w->finish,"I33 CAPACITY: R41 key exceeds supported size");
}
bool wood_dp_edge_resolve(const WoodDerivedContext *w,const WoodDerivedValue *p,const char *key,int *hole,int *edge)
{
    size_t matches=0;char candidate[512];
    if(!p||!p->derived_fill_id)return false;
    for(size_t c=0;c<p->component_count;++c){const WoodBoundaryRegion *b=&p->components[c];for(size_t h=0;h<=b->hole_count;++h){const WoodBoundaryLoop *l=h?&b->holes[h-1]:&b->outline;
        for(size_t e=0;e<l->count;++e){if(!wood_dp_edge_key(w,p,c,h?(int)h-1:-1,e,candidate,sizeof candidate))return false;
            if(!strcmp(key,candidate)){++matches;*hole=h?(int)(c*GEO_REGION_MAX_HOLES+h-1):-1;*edge=h?(int)e:(int)(c*GEO_LOOP_MAX_VERTICES+e);}}}}
    return matches==1||wood_fs_error(&w->finish,"R41: key %.160s matches %zu derived edges; exactly one is required",key,matches);
}
bool wood_dp_load(WoodDerivedContext *w,uint32_t id,const DerivedPlacement *p,const char **message)
{
    WoodDerivedValue prior;*message=NULL;
    if(id!=p->id||wood_dp_find(w,id)||w->placement_read(w->finish.user,id,&prior)){*message="D4/I56: derived placement id mismatch, duplicate or variant collision";return false;}
    for(uint64_t i=0;i<w->finish.state->host_count;++i)if(w->finish.state->hosts[i].fill_id==p->fill_id){*message="D4: one derived placement per fill";return false;}
    if(w->finish.state->host_count==FS_MAX||w->placement_count(w->finish.user)==w->placement_capacity){*message="I33 CAPACITY: derived placement limit reached";return false;}
    w->finish.state->hosts[w->finish.state->host_count++]=*p;WoodDerivedValue host={0};host.id=id;host.derived_fill_id=p->fill_id;if(!w->placement_write(w->finish.user,&host))return false;
    if(!wood_dp_rebuild(w)){*message=w->finish.error;return false;}return true;
}
