#include "panel_layout.h"
#ifndef GEOMETRY_KERNEL_GRID_H
#include "grid.h"
#endif
#include <stdlib.h>
#include <string.h>
static GeoCoord panel_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord panel_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
void wood_panel_layout_free(WoodPanelLayout *d)
{if(d->tiles)for(size_t i=0;i<d->count;++i){WoodPanelTile *t=&d->tiles[i];GeoClipResult r={t->fragments,t->count,t->area};geo_clip_result_free(&r);}free(d->tiles);free(d->seams);memset(d,0,sizeof *d);}
WoodPanelStatus wood_panel_layout_build(const WoodPanelLayoutInput *p,WoodPanelLayout *d,GeoClipStatus *clip_status)
{
    memset(d,0,sizeof *d);*clip_status=GEO_CLIP_OK;d->size[0]=p->size[0];d->size[1]=p->size[1];d->gap=p->gap;d->stagger=p->stagger;
    const GeoRegionView *b=&p->region;GeoCoord lo[2]={b->outline.v[0].u,b->outline.v[0].v},hi[2]={lo[0],lo[1]};
    for(size_t i=1;i<b->outline.count;++i){lo[0]=panel_min(lo[0],b->outline.v[i].u);hi[0]=panel_max(hi[0],b->outline.v[i].u);lo[1]=panel_min(lo[1],b->outline.v[i].v);hi[1]=panel_max(hi[1],b->outline.v[i].v);}
    d->tiles=calloc(WOOD_PANEL_TILE_MAX,sizeof *d->tiles);if(!d->tiles)return WOOD_PANEL_WORKSPACE;
    int row=p->stagger_axis==0?1:0,along=1-row;GeoCoord pitch[2]={geo_period_pitch(d->size[0],d->gap),geo_period_pitch(d->size[1],d->gap)};
    int64_t first=geo_floor_div(lo[row]-p->origin[row]-d->size[row],pitch[row])+1,last=geo_ceil_div(hi[row]-p->origin[row],pitch[row])-1;size_t enumerated=0;
    /* The alternating lattice has at most two row phases.  If neither
     * present phase intersects the along-axis bbox, no row has a body.
     * Raw seam lines still follow their original independent enumeration. */
    bool body_axis_intersects=false;
    if(first<=last)for(int phase=0;phase<2;++phase){
        int64_t sample=first;if(phase){if(first==last)break;++sample;}
        GeoCoord shifted=p->origin[along]+geo_alternating_shift(p->stagger_axis>=0,d->stagger,sample);
        int64_t a=geo_floor_div(lo[along]-shifted-d->size[along],pitch[along])+1,z=geo_ceil_div(hi[along]-shifted,pitch[along])-1;
        if(a<=z){body_axis_intersects=true;break;}
    }
    for(int64_t r=first;body_axis_intersects&&r<=last;++r){GeoCoord shifted=p->origin[along]+geo_alternating_shift(p->stagger_axis>=0,d->stagger,r);
        int64_t a=geo_floor_div(lo[along]-shifted-d->size[along],pitch[along])+1,z=geo_ceil_div(hi[along]-shifted,pitch[along])-1;
        if(z>=a&&(uint64_t)(z-a+1)>WOOD_PANEL_TILE_MAX-enumerated){wood_panel_layout_free(d);return WOOD_PANEL_ENUM_LIMIT;}
        for(int64_t k=a;k<=z;++k){++enumerated;WoodPanelTile *t=&d->tiles[d->count];t->i=row==0?r:k;t->j=row==1?r:k;
            t->body[row]=geo_period_body(p->origin[row],d->size[row],d->gap,r);t->body[along]=geo_period_body(shifted,d->size[along],d->gap,k);t->body[row+2]=t->body[row]+d->size[row];t->body[along+2]=t->body[along]+d->size[along];
            /* Non-visible sheet corners can be beyond D1; only returned geometry is checked below. */
            ++d->count;GeoRect2 body={t->body[0],t->body[1],t->body[2],t->body[3]};GeoClipResult clipped={0};
            *clip_status=geo_region_clip_rect_minus_rects(&p->region,&body,p->cuts,p->cut_count,false,WOOD_PANEL_VERTEX_MAX,&d->vertices,&clipped);
            t->fragments=clipped.fragments;t->count=clipped.count;t->area=clipped.area;
            if(*clip_status!=GEO_CLIP_OK){wood_panel_layout_free(d);return WOOD_PANEL_CLIP;}
            if(!t->count){free(t->fragments);memset(t,0,sizeof *t);--d->count;continue;}
            d->fragments+=t->count;if(t->area==d->size[0]*d->size[1])++d->whole;
            for(int v=0;v<4;++v)if(!geo_coord_in_range(t->body[v])){wood_panel_layout_free(d);return WOOD_PANEL_CORNER_RANGE;}
            for(size_t f=0;f<t->count;++f)for(size_t l=0;l<t->fragments[f].count;++l)for(size_t v=0;v<t->fragments[f].loops[l].count;++v){GeoPoint2 point=t->fragments[f].loops[l].points[v];const GeoFrame *frame=&p->frame;
                GeoCoord u=point.u,z=point.v;GeoPoint3 world={frame->origin.x+u*frame->axis_u.x+z*frame->axis_v.x,frame->origin.y+u*frame->axis_u.y+z*frame->axis_v.y,frame->origin.z+u*frame->axis_u.z+z*frame->axis_v.z};
                if(!geo_coord_in_range(u)||!geo_coord_in_range(z)||!geo_coord_in_range(world.x)||!geo_coord_in_range(world.y)||!geo_coord_in_range(world.z)){wood_panel_layout_free(d);return WOOD_PANEL_VERTEX_RANGE;}}
        }
    }
    d->seams=calloc(4*WOOD_PANEL_TILE_MAX,sizeof *d->seams);if(!d->seams){wood_panel_layout_free(d);return WOOD_PANEL_SEAM_WORKSPACE;}
    for(int axis=0;axis<2;++axis){int other=1-axis;GeoCoord step=pitch[axis],phase=geo_period_center(p->origin[axis],d->size[axis],d->gap,0);
        /* D43: band r is [c_other(r-1),c_other(r)], including the half gaps.
         * Enumerate positive-length bbox intersections; body bounds omit those halves. */
        int64_t r0=0,r1=0;if(p->stagger_axis==axis){GeoCoord center=geo_period_center(p->origin[other],d->size[other],d->gap,0);r0=geo_floor_div(lo[other]-center,pitch[other])+1;r1=geo_ceil_div(hi[other]-center,pitch[other]);}
        for(int64_t r=r0;r<=r1;++r){GeoCoord shift=p->stagger_axis==axis?geo_alternating_shift(true,d->stagger,r):0;
            int64_t k0=geo_ceil_div(lo[axis]-phase-shift,step),k1=geo_floor_div(hi[axis]-phase-shift,step);
            for(int64_t k=k0;k<=k1;++k){if(d->seam_count==4*WOOD_PANEL_TILE_MAX){wood_panel_layout_free(d);return WOOD_PANEL_SEAM_LIMIT;}
                WoodPanelSeamLine *s=&d->seams[d->seam_count++];s->axis=axis;s->k=k;s->band=r;s->staggered=p->stagger_axis==axis;s->coordinate=geo_period_center(p->origin[axis]+shift,d->size[axis],d->gap,k);
                if(s->staggered){s->range[0]=geo_period_center(p->origin[other],d->size[other],d->gap,r-1);s->range[1]=geo_period_center(p->origin[other],d->size[other],d->gap,r);
                    if(!geo_coord_in_range(s->range[0])||!geo_coord_in_range(s->range[1])){wood_panel_layout_free(d);return WOOD_PANEL_BAND_RANGE;}}
            }
        }
    }
    return WOOD_PANEL_OK;
}
