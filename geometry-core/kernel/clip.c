#include "clip.h"
#include <stdlib.h>
#include <string.h>
static GeoCoord clip_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord clip_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
static int clip_coord_compare(const void *a,const void *b){GeoCoord x=*(const GeoCoord*)a,y=*(const GeoCoord*)b;return x<y?-1:x>y?1:0;}
void geo_clip_result_free(GeoClipResult *r)
{for(size_t f=0;f<r->count;++f){for(size_t l=0;l<r->fragments[f].count;++l)free(r->fragments[f].loops[l].points);free(r->fragments[f].loops);}free(r->fragments);memset(r,0,sizeof *r);}
static bool clip_inside_loop(const GeoLoop2View *p,GeoCoord u2,GeoCoord v2)
{ bool inside=false;for(size_t i=0;i<p->count;++i){GeoPoint2 a=p->v[i],b=p->v[(i+1)%p->count];if(a.u==b.u&&2*a.u>u2&&2*clip_min(a.v,b.v)<v2&&v2<2*clip_max(a.v,b.v))inside=!inside;}return inside; }
static bool clip_inside(const GeoRegionView *b,const GeoRect2 *cuts,size_t cut_count,GeoCoord u2,GeoCoord v2)
{ if(!clip_inside_loop(&b->outline,u2,v2))return false;for(size_t h=0;h<b->hole_count;++h)if(clip_inside_loop(&b->holes[h],u2,v2))return false;
  for(size_t i=0;i<cut_count;++i){const GeoRect2 *r=&cuts[i];if(2*r->min_u<u2&&u2<2*r->max_u&&2*r->min_v<v2&&v2<2*r->max_v)return false;}return true; }
static bool clip_cut_coord(GeoCoord *xs,size_t *n,GeoCoord v,GeoCoord lo,GeoCoord hi,GeoClipStatus *status)
{ if(v<=lo||v>=hi)return true;for(size_t i=0;i<*n;++i)if(xs[i]==v)return true;if(*n==GEO_CLIP_AXIS_MAX)return (*status=GEO_CLIP_AXIS_LIMIT,false);xs[(*n)++]=v;return true; }
typedef struct { int x0,y0,x1,y1,dir;bool used; } GeoClipEdge;
int geo_clip_point_order(GeoPoint2 a,GeoPoint2 b)
{return a.u!=b.u?(a.u<b.u?-1:1):a.v!=b.v?(a.v<b.v?-1:1):0;}
static int clip_loop_order(const void *a,const void *b)
{const GeoClipLoop *x=a,*y=b;if(x->hole!=y->hole)return x->hole?1:-1;return geo_clip_point_order(x->points[0],y->points[0]);}
static int clip_component_order(const void *a,const void *b)
{return geo_clip_point_order(((const GeoClipComponent*)a)->loops[0].points[0],((const GeoClipComponent*)b)->loops[0].points[0]);}
GeoClipStatus geo_region_clip_rect_minus_rects(const GeoRegionView *b,
    const GeoRect2 *body,const GeoRect2 *cuts,size_t cut_count,bool keep_collinear,
    size_t vertex_limit,size_t *vertex_count,GeoClipResult *t)
{
    GeoCoord xs[GEO_CLIP_AXIS_MAX]={body->min_u,body->max_u},ys[GEO_CLIP_AXIS_MAX]={body->min_v,body->max_v};size_t nx=2,ny=2;bool ok=true;GeoClipStatus status=GEO_CLIP_OK;
    for(size_t h=0;h<=b->hole_count&&ok;++h){const GeoLoop2View *l=h?&b->holes[h-1]:&b->outline;for(size_t i=0;i<l->count&&ok;++i)ok=clip_cut_coord(xs,&nx,l->v[i].u,xs[0],xs[1],&status)&&clip_cut_coord(ys,&ny,l->v[i].v,ys[0],ys[1],&status);}
    for(size_t i=0;i<cut_count&&ok;++i){GeoCoord r[4]={cuts[i].min_u,cuts[i].min_v,cuts[i].max_u,cuts[i].max_v};for(int k=0;k<4&&ok;++k)ok=k%2?clip_cut_coord(ys,&ny,r[k],ys[0],ys[1],&status):clip_cut_coord(xs,&nx,r[k],xs[0],xs[1],&status);}
    if(!ok)return status;qsort(xs,nx,sizeof *xs,clip_coord_compare);qsort(ys,ny,sizeof *ys,clip_coord_compare);
    size_t width=nx-1,height=ny-1,n=width*height;int *labels=calloc(n,sizeof *labels),*queue=malloc(n*sizeof *queue);GeoClipEdge *edges=malloc(GEO_CLIP_EDGE_MAX*sizeof *edges);
    if(!labels||!queue||!edges){free(labels);free(queue);free(edges);return GEO_CLIP_WORKSPACE;}
    for(size_t y=0;y<height;++y)for(size_t x=0;x<width;++x)labels[y*width+x]=clip_inside(b,cuts,cut_count,xs[x]+xs[x+1],ys[y]+ys[y+1])?-1:0;
    int component=0;
    for(size_t seed=0;seed<n&&ok;++seed)if(labels[seed]==-1){
        ++component;size_t head=0,tail=1;queue[0]=(int)seed;labels[seed]=component;GeoCoord component_area=0;
        while(head<tail){int cell=queue[head++],x=cell%(int)width,y=cell/(int)width;component_area+=(xs[x+1]-xs[x])*(ys[y+1]-ys[y]);int neighbors[4]={x?cell-1:-1,x+1<(int)width?cell+1:-1,y?cell-(int)width:-1,y+1<(int)height?cell+(int)width:-1};
            for(int k=0;k<4;++k)if(neighbors[k]>=0&&labels[neighbors[k]]==-1){labels[neighbors[k]]=component;queue[tail++]=neighbors[k];}}
        GeoClipComponent *grown=realloc(t->fragments,(t->count+1)*sizeof *grown);if(!grown){ok=(status=GEO_CLIP_COMPONENT_WORKSPACE,false);break;}t->fragments=grown;GeoClipComponent *f=&grown[t->count++];memset(f,0,sizeof *f);f->area=component_area;t->area+=component_area;
        size_t ne=0;
        for(size_t q=0;q<tail&&ok;++q){int cell=queue[q],x=cell%(int)width,y=cell/(int)width;
            bool boundary[4]={!y||labels[cell-width]!=component,x+1==(int)width||labels[cell+1]!=component,y+1==(int)height||labels[cell+width]!=component,!x||labels[cell-1]!=component};
            int dx[4]={1,0,-1,0},dy[4]={0,1,0,-1},sx[4]={x,x+1,x+1,x},sy[4]={y,y,y+1,y+1};
            for(int k=0;k<4&&ok;++k)if(boundary[k]){if(ne==GEO_CLIP_EDGE_MAX){ok=(status=GEO_CLIP_EDGE_LIMIT,false);break;}edges[ne++]=(GeoClipEdge){sx[k],sy[k],sx[k]+dx[k],sy[k]+dy[k],k,false};}}
        for(size_t start=0;start<ne&&ok;++start)if(!edges[start].used){
            GeoPoint2 *points=malloc(ne*sizeof *points);if(!points){ok=(status=GEO_CLIP_LOOP_WORKSPACE,false);break;}
            size_t at=start,np=0;int firstx=edges[start].x0,firsty=edges[start].y0;
            while(ok){GeoClipEdge *e=&edges[at];if(e->used||np==ne){ok=(status=GEO_CLIP_TRAVERSAL,false);break;}e->used=true;points[np++]=(GeoPoint2){xs[e->x0],ys[e->y0]};if(e->x1==firstx&&e->y1==firsty)break;
                /* At a repeated vertex take the right branch first: this splits touching hole rings
                 * into simple clockwise loops, instead of one figure-eight. Components are already
                 * split by positive-length cell adjacency, so point-touching material is never joined. */
                int rank=-1;size_t next=ne;for(size_t k=0;k<ne;++k)if(!edges[k].used&&edges[k].x0==e->x1&&edges[k].y0==e->y1){int turn=(edges[k].dir-e->dir+4)%4,r=turn==3?3:turn==0?2:turn==1?1:0;if(r>rank){rank=r;next=k;}}
                if(next==ne){ok=(status=GEO_CLIP_OPEN_CONTOUR,false);break;}at=next;}
            if(!ok){free(points);break;}
            /* Remove collinear subdivision vertices, then rotate to the lexicographically smallest point. */
            GeoPoint2 *corners=malloc(np*sizeof *corners);if(!corners){free(points);ok=(status=GEO_CLIP_CORNERS_WORKSPACE,false);break;}
            size_t count=0;for(size_t k=0;k<np;++k){GeoPoint2 a=points[(k+np-1)%np],v=points[k],z=points[(k+1)%np];if(keep_collinear||!((a.u==v.u&&v.u==z.u)||(a.v==v.v&&v.v==z.v)))corners[count++]=v;}free(points);points=corners;
            size_t min=0;for(size_t k=1;k<count;++k)if(geo_clip_point_order(points[k],points[min])<0)min=k;
            GeoPoint2 *ordered=malloc(count*sizeof *ordered);if(!ordered){free(points);ok=(status=GEO_CLIP_ORDERED_WORKSPACE,false);break;}for(size_t k=0;k<count;++k)ordered[k]=points[(min+k)%count];free(points);
            if(*vertex_count+count>vertex_limit){free(ordered);ok=(status=GEO_CLIP_VERTEX_LIMIT,false);break;}*vertex_count+=count;
            GeoClipLoop *loops=realloc(f->loops,(f->count+1)*sizeof *loops);if(!loops){free(ordered);ok=(status=GEO_CLIP_COLLECTION_WORKSPACE,false);break;}f->loops=loops;
            bool hole=ordered[1].v>ordered[0].v;loops[f->count++]=(GeoClipLoop){ordered,count,hole};
        }
        if(ok){qsort(f->loops,f->count,sizeof *f->loops,clip_loop_order);if(!f->count||f->loops[0].hole)ok=(status=GEO_CLIP_NO_OUTER,false);}
    }
    free(labels);free(queue);free(edges);if(ok&&t->count)qsort(t->fragments,t->count,sizeof *t->fragments,clip_component_order);return status;
}
