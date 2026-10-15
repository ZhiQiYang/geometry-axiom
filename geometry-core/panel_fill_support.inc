/* PF-3: consume the PF-2 layout, never reconstruct its lattice or clipping.
 * All sampling is in doubled integer coordinates, strictly inside open slabs.
 * Only definitions persist. Results and workspaces are heap owned and bounded. */
#define PF_SUPPORT_MAX 32768
#define PF_SUPPORT_WORK_MAX 1048576
typedef struct { Coord lo[2],hi[2]; } PfFootprint;
typedef struct { size_t line;Coord range[2],edges[2]; } PfEffectiveSeam;
typedef struct { size_t seam;Coord range[2],left,right;bool supported; } PfSupportPart;
typedef struct { Coord lo,hi; } PfInterval;
typedef struct {
    PfEffectiveSeam *seams,*nonseams;size_t count,non_count;
    PfSupportPart *parts;size_t part_count;
} PfSupport;
static void pf_support_free(PfSupport *s)
{free(s->seams);free(s->nonseams);free(s->parts);memset(s,0,sizeof *s);}
static Coord pf_component(SurfacePoint2 p,int axis) {return axis?p.v:p.u;}
static int pf_interval_compare(const void *a,const void *b)
{const PfInterval *x=a,*y=b;return x->lo!=y->lo?(x->lo<y->lo?-1:1):x->hi!=y->hi?(x->hi<y->hi?-1:1):0;}
/* Compare a nonnegative integer width to positive num/den without overflow. */
static bool pf_support_enough(Coord d,ParamValue x)
{return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);}
static bool pf_support_footprints(const World *w,const PanelFill *p,PfFootprint *rects,size_t *count)
{
    *count=0;const PlacementSurface *host=NULL;
    for(size_t i=0;i<w->finish_surfaces.host_count;++i)if(w->finish_surfaces.hosts[i].fill_id==p->id)
        host=world_find_placement(w,w->finish_surfaces.hosts[i].id);
    if(!host)return true;
    const FinishSurface *finish=fs_find(w,p->finish_id);
    for(size_t i=0;i<w->timber_count;++i){
        if(!w->timbers[i].placed||w->anchors[i].placement_id!=host->id)continue;
        SurfaceRegion2 f;
        if(!timber_a0_footprint_uv(host,&w->timbers[i],&w->anchors[i],&f))return fs_error("R43: timber %u footprint unavailable",w->timbers[i].id);
        PfFootprint *r=&rects[(*count)++];r->lo[0]=f.min_u;r->hi[0]=f.max_u;
        r->lo[1]=coord_min(finish->side*f.min_v,finish->side*f.max_v);
        r->hi[1]=coord_max(finish->side*f.min_v,finish->side*f.max_v);
    }
    return true;
}
/* A cross section of one actual fragment, including every hole. The sample
 * cannot hit a polygon vertex; sorted crossings therefore alternate material. */
static size_t pf_support_section(const PfFragment *f,int axis,Coord y2,Coord *xs)
{
    size_t n=0;int other=1-axis;
    for(size_t l=0;l<f->count;++l){const PfLoop *loop=&f->loops[l];
        for(size_t v=0;v<loop->count;++v){SurfacePoint2 a=loop->points[v],b=loop->points[(v+1)%loop->count];
            Coord x=pf_component(a,axis),z=pf_component(b,axis),u=pf_component(a,other),q=pf_component(b,other);
            if(x==z&&2*coord_min(u,q)<y2&&y2<2*coord_max(u,q))xs[n++]=x;
        }
    }
    qsort(xs,n,sizeof *xs,sp_coord_compare);return n;
}
static size_t pf_support_union(const PfFootprint *rects,size_t nr,int axis,Coord y2,PfInterval *out)
{
    size_t n=0;int other=1-axis;
    for(size_t i=0;i<nr;++i)if(2*rects[i].lo[other]<y2&&y2<2*rects[i].hi[other])out[n++]=(PfInterval){rects[i].lo[axis],rects[i].hi[axis]};
    qsort(out,n,sizeof *out,pf_interval_compare);size_t used=0;
    for(size_t i=0;i<n;++i){
        if(used&&out[i].lo<=out[used-1].hi)out[used-1].hi=coord_max(out[used-1].hi,out[i].hi);
        else out[used++]=out[i];
    }
    return used;
}
static Coord pf_support_width(const PfInterval *un,size_t n,Coord edge,Coord stop,bool left)
{
    for(size_t i=0;i<n;++i){
        if(left&&un[i].lo<edge&&edge<=un[i].hi)return edge-coord_max(stop,un[i].lo);
        if(!left&&un[i].lo<=edge&&edge<un[i].hi)return coord_min(stop,un[i].hi)-edge;
    }
    return 0;
}
static bool pf_support_append_seam(PfEffectiveSeam *out,size_t *count,size_t line,Coord lo,Coord hi,Coord left,Coord right)
{
    if(*count&&out[*count-1].line==line&&out[*count-1].range[1]==lo){out[*count-1].range[1]=hi;return true;}
    if(*count==PF_SUPPORT_MAX)return fs_capacity_error("I33 CAPACITY: PF-3 effective/non-seam limit is %d",PF_SUPPORT_MAX);
    out[(*count)++]=(PfEffectiveSeam){line,{lo,hi},{left,right}};return true;
}
/* Pure evaluator shared with the algorithm-only P-103 harness. Production
 * callers can supply footprints only through the validated World above. */
static bool pf_support_evaluate(const PfLayout *d,const PfFootprint *rects,size_t nr,ParamValue threshold,PfSupport *s)
{
    memset(s,0,sizeof *s);bool ok=false;
    if(nr>WORLD_MAX_TIMBERS)return fs_capacity_error("I33 CAPACITY: PF-3 footprint limit is %d",WORLD_MAX_TIMBERS);
    size_t capacity=d->vertices+2*nr+2;
    Coord *cuts=malloc(capacity*sizeof *cuts),*crossings=malloc((d->vertices+1)*sizeof *crossings);
    PfInterval *un=malloc((nr+1)*sizeof *un);
    s->seams=calloc(PF_SUPPORT_MAX,sizeof *s->seams);s->nonseams=calloc(PF_SUPPORT_MAX,sizeof *s->nonseams);s->parts=calloc(PF_SUPPORT_MAX,sizeof *s->parts);
    if(!cuts||!crossings||!un||!s->seams||!s->nonseams||!s->parts){fs_capacity_error("I33 CAPACITY: PF-3 workspace unavailable");goto done;}
    size_t work=0;
    for(size_t line=0;line<d->seam_count;++line){const PfSeamLine *sl=&d->seams[line];int axis=sl->axis,other=1-axis;size_t nc=0;
        Coord edges[2]={sl->coordinate-d->gap/2,sl->coordinate+(d->gap-d->gap/2)};
        /* Board-fragment vertices are as important as footprint vertices (PF23). */
        for(size_t t=0;t<d->count;++t)for(size_t f=0;f<d->tiles[t].count;++f){const PfFragment *frag=&d->tiles[t].fragments[f];
            for(size_t l=0;l<frag->count;++l)for(size_t v=0;v<frag->loops[l].count;++v)cuts[nc++]=pf_component(frag->loops[l].points[v],other);}
        for(size_t r=0;r<nr;++r){cuts[nc++]=rects[r].lo[other];cuts[nc++]=rects[r].hi[other];}
        if(sl->staggered){cuts[nc++]=sl->range[0];cuts[nc++]=sl->range[1];}
        qsort(cuts,nc,sizeof *cuts,sp_coord_compare);size_t unique=0;
        for(size_t i=0;i<nc;++i)if(!unique||cuts[i]!=cuts[unique-1])cuts[unique++]=cuts[i];
        for(size_t y=1;y<unique;++y){Coord lo=cuts[y-1],hi=cuts[y],y2=lo+hi;
            if(sl->staggered&&(lo<sl->range[0]||hi>sl->range[1]))continue;
            if(++work>PF_SUPPORT_WORK_MAX){fs_capacity_error("I33 CAPACITY: PF-3 open-slab evaluation limit is %d",PF_SUPPORT_WORK_MAX);goto done;}
            bool present[2]={false,false};Coord stop[2]={0,0};
            for(size_t t=0;t<d->count;++t){const PfTile *tile=&d->tiles[t];
                if(y2<=2*tile->body[other]||y2>=2*tile->body[other+2])continue;
                if(tile->body[axis+2]!=edges[0]&&tile->body[axis]!=edges[1])continue;
                for(size_t f=0;f<tile->count;++f){size_t n=pf_support_section(&tile->fragments[f],axis,y2,crossings);
                    for(size_t k=1;k<n;k+=2){Coord a=crossings[k-1],b=crossings[k];
                        if(b==edges[0]&&a<b){present[0]=true;stop[0]=a;}
                        if(a==edges[1]&&a<b){present[1]=true;stop[1]=b;}
                    }
                }
            }
            if(!present[0]||!present[1]){
                if((present[0]||present[1])&&!pf_support_append_seam(s->nonseams,&s->non_count,line,lo,hi,edges[0],edges[1]))goto done;
                continue;
            }
            if(!pf_support_append_seam(s->seams,&s->count,line,lo,hi,edges[0],edges[1]))goto done;
            size_t seam=s->count-1,n=pf_support_union(rects,nr,axis,y2,un);
            Coord left=pf_support_width(un,n,edges[0],stop[0],true),right=pf_support_width(un,n,edges[1],stop[1],false);
            if(s->part_count){PfSupportPart *last=&s->parts[s->part_count-1];
                if(last->seam==seam&&last->range[1]==lo&&last->left==left&&last->right==right){last->range[1]=hi;continue;}}
            if(s->part_count==PF_SUPPORT_MAX){fs_capacity_error("I33 CAPACITY: PF-3 support subsegment limit is %d",PF_SUPPORT_MAX);goto done;}
            s->parts[s->part_count++]=(PfSupportPart){seam,{lo,hi},left,right,pf_support_enough(left,threshold)&&pf_support_enough(right,threshold)};
        }
    }
    ok=true;
done:free(cuts);free(crossings);free(un);if(!ok)pf_support_free(s);return ok;
}
static bool pf_support_build(const World *w,const PanelFill *p,const PfLayout *d,PfSupport *s)
{
    memset(s,0,sizeof *s);PfFootprint *rects=malloc(WORLD_MAX_TIMBERS*sizeof *rects);ParamValue threshold;size_t count;
    if(!rects)return fs_capacity_error("I33 CAPACITY: PF-3 footprints unavailable");
    bool ok=parameter_value(w,p->threshold,&threshold)&&pf_support_footprints(w,p,rects,&count)&&pf_support_evaluate(d,rects,count,threshold,s);
    free(rects);return ok;
}
/* Called after D7 reconstruction, before committing any candidate. A capacity
 * failure must reject the transaction, rather than truncate a later read. */
static bool pf_support_rebuild(const World *w)
{
    for(size_t i=0;i<w->finish_surfaces.fill_count;++i){PfLayout d;PfSupport s={0};const PanelFill *p=&w->finish_surfaces.fills[i];
        bool ok=pf_build(w,p,&d)&&pf_support_build(w,p,&d,&s);pf_support_free(&s);pf_free(&d);if(!ok)return false;}
    return true;
}
