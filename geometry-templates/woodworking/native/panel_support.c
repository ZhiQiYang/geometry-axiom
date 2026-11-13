#include "panel_support.h"
#include <stdlib.h>
#include <string.h>
typedef struct {GeoCoord lo,hi;} PanelInterval;
static GeoCoord support_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord support_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
static int support_coord_compare(const void *a,const void *b){GeoCoord x=*(const GeoCoord*)a,y=*(const GeoCoord*)b;return x<y?-1:x>y?1:0;}
void wood_panel_support_free(WoodPanelSupport *s)
{free(s->seams);free(s->nonseams);free(s->parts);memset(s,0,sizeof *s);}
static GeoCoord pf_component(GeoPoint2 p,int axis) {return axis?p.v:p.u;}
static int pf_interval_compare(const void *a,const void *b)
{const PanelInterval *x=a,*y=b;return x->lo!=y->lo?(x->lo<y->lo?-1:1):x->hi!=y->hi?(x->hi<y->hi?-1:1):0;}
/* Compare a nonnegative integer width to positive num/den without overflow. */
static bool pf_support_enough(GeoCoord d,GeoQuantity x)
{return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);}
/* A cross section of one actual fragment, including every hole. The sample
 * cannot hit a polygon vertex; sorted crossings therefore alternate material. */
static size_t pf_support_section(const WoodPanelFragment *f,int axis,GeoCoord y2,GeoCoord *xs)
{
    size_t n=0;int other=1-axis;
    for(size_t l=0;l<f->count;++l){const WoodPanelLoop *loop=&f->loops[l];
        for(size_t v=0;v<loop->count;++v){GeoPoint2 a=loop->points[v],b=loop->points[(v+1)%loop->count];
            GeoCoord x=pf_component(a,axis),z=pf_component(b,axis),u=pf_component(a,other),q=pf_component(b,other);
            if(x==z&&2*support_min(u,q)<y2&&y2<2*support_max(u,q))xs[n++]=x;
        }
    }
    qsort(xs,n,sizeof *xs,support_coord_compare);return n;
}
static size_t pf_support_union(const WoodPanelFootprint *rects,size_t nr,int axis,GeoCoord y2,PanelInterval *out)
{
    size_t n=0;int other=1-axis;
    for(size_t i=0;i<nr;++i)if(2*rects[i].lo[other]<y2&&y2<2*rects[i].hi[other])out[n++]=(PanelInterval){rects[i].lo[axis],rects[i].hi[axis]};
    qsort(out,n,sizeof *out,pf_interval_compare);size_t used=0;
    for(size_t i=0;i<n;++i){
        if(used&&out[i].lo<=out[used-1].hi)out[used-1].hi=support_max(out[used-1].hi,out[i].hi);
        else out[used++]=out[i];
    }
    return used;
}
static GeoCoord pf_support_width(const PanelInterval *un,size_t n,GeoCoord edge,GeoCoord stop,bool left)
{
    for(size_t i=0;i<n;++i){
        if(left&&un[i].lo<edge&&edge<=un[i].hi)return edge-support_max(stop,un[i].lo);
        if(!left&&un[i].lo<=edge&&edge<un[i].hi)return support_min(stop,un[i].hi)-edge;
    }
    return 0;
}
static bool pf_support_append_seam(WoodPanelEffectiveSeam *out,size_t *count,size_t line,GeoCoord lo,GeoCoord hi,GeoCoord left,GeoCoord right,WoodPanelSupportStatus *status)
{
    if(*count&&out[*count-1].line==line&&out[*count-1].range[1]==lo){out[*count-1].range[1]=hi;return true;}
    if(*count==WOOD_PANEL_SUPPORT_MAX)return (*status=WOOD_PANEL_SUPPORT_SEAM_LIMIT,false);
    out[(*count)++]=(WoodPanelEffectiveSeam){line,{lo,hi},{left,right}};return true;
}
/* The product and isolated P-103 harness call this same evaluator. The product
 * supplies footprints selected from its validated placement/member sources. */
WoodPanelSupportStatus wood_panel_support_evaluate(const WoodPanelLayout *d,const WoodPanelFootprint *rects,size_t nr,size_t footprint_capacity,GeoQuantity threshold,WoodPanelSupport *s)
{
    memset(s,0,sizeof *s);bool ok=false;WoodPanelSupportStatus status=WOOD_PANEL_SUPPORT_OK;
    if(nr>footprint_capacity)return WOOD_PANEL_SUPPORT_FOOTPRINT_LIMIT;
    size_t capacity=d->vertices+2*nr+2;
    GeoCoord *cuts=malloc(capacity*sizeof *cuts),*crossings=malloc((d->vertices+1)*sizeof *crossings);
    PanelInterval *un=malloc((nr+1)*sizeof *un);
    s->seams=calloc(WOOD_PANEL_SUPPORT_MAX,sizeof *s->seams);s->nonseams=calloc(WOOD_PANEL_SUPPORT_MAX,sizeof *s->nonseams);s->parts=calloc(WOOD_PANEL_SUPPORT_MAX,sizeof *s->parts);
    if(!cuts||!crossings||!un||!s->seams||!s->nonseams||!s->parts){status=WOOD_PANEL_SUPPORT_WORKSPACE;goto done;}
    size_t work=0;
    for(size_t line=0;line<d->seam_count;++line){const WoodPanelSeamLine *sl=&d->seams[line];int axis=sl->axis,other=1-axis;size_t nc=0;
        GeoCoord edges[2]={sl->coordinate-d->gap/2,sl->coordinate+(d->gap-d->gap/2)};
        /* Board-fragment vertices are as important as footprint vertices (PF23). */
        for(size_t t=0;t<d->count;++t)for(size_t f=0;f<d->tiles[t].count;++f){const WoodPanelFragment *frag=&d->tiles[t].fragments[f];
            for(size_t l=0;l<frag->count;++l)for(size_t v=0;v<frag->loops[l].count;++v)cuts[nc++]=pf_component(frag->loops[l].points[v],other);}
        for(size_t r=0;r<nr;++r){cuts[nc++]=rects[r].lo[other];cuts[nc++]=rects[r].hi[other];}
        if(sl->staggered){cuts[nc++]=sl->range[0];cuts[nc++]=sl->range[1];}
        qsort(cuts,nc,sizeof *cuts,support_coord_compare);size_t unique=0;
        for(size_t i=0;i<nc;++i)if(!unique||cuts[i]!=cuts[unique-1])cuts[unique++]=cuts[i];
        for(size_t y=1;y<unique;++y){GeoCoord lo=cuts[y-1],hi=cuts[y],y2=lo+hi;
            if(sl->staggered&&(lo<sl->range[0]||hi>sl->range[1]))continue;
            if(++work>WOOD_PANEL_SUPPORT_WORK_MAX){status=WOOD_PANEL_SUPPORT_SLAB_LIMIT;goto done;}
            bool present[2]={false,false};GeoCoord stop[2]={0,0};
            for(size_t t=0;t<d->count;++t){const WoodPanelTile *tile=&d->tiles[t];
                if(y2<=2*tile->body[other]||y2>=2*tile->body[other+2])continue;
                if(tile->body[axis+2]!=edges[0]&&tile->body[axis]!=edges[1])continue;
                for(size_t f=0;f<tile->count;++f){size_t n=pf_support_section(&tile->fragments[f],axis,y2,crossings);
                    for(size_t k=1;k<n;k+=2){GeoCoord a=crossings[k-1],b=crossings[k];
                        if(b==edges[0]&&a<b){present[0]=true;stop[0]=a;}
                        if(a==edges[1]&&a<b){present[1]=true;stop[1]=b;}
                    }
                }
            }
            if(!present[0]||!present[1]){
                if((present[0]||present[1])&&!pf_support_append_seam(s->nonseams,&s->non_count,line,lo,hi,edges[0],edges[1],&status))goto done;
                continue;
            }
            if(!pf_support_append_seam(s->seams,&s->count,line,lo,hi,edges[0],edges[1],&status))goto done;
            size_t seam=s->count-1,n=pf_support_union(rects,nr,axis,y2,un);
            GeoCoord left=pf_support_width(un,n,edges[0],stop[0],true),right=pf_support_width(un,n,edges[1],stop[1],false);
            if(s->part_count){WoodPanelSupportPart *last=&s->parts[s->part_count-1];
                if(last->seam==seam&&last->range[1]==lo&&last->left==left&&last->right==right){last->range[1]=hi;continue;}}
            if(s->part_count==WOOD_PANEL_SUPPORT_MAX){status=WOOD_PANEL_SUPPORT_PART_LIMIT;goto done;}
            s->parts[s->part_count++]=(WoodPanelSupportPart){seam,{lo,hi},left,right,pf_support_enough(left,threshold)&&pf_support_enough(right,threshold)};
        }
    }
    ok=true;
done:free(cuts);free(crossings);free(un);if(!ok)wood_panel_support_free(s);return status;
}
