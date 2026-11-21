/* R45 suggestion policy over immutable same-candidate facts. This header has
 * no World, history, publication, parser, or global-state dependency. Geometry
 * predicates are public K operations; H supplies complete derived facts and
 * evaluates every returned declaration through the ordinary D7/R6 evaluator. */
#ifndef GEOMETRY_WOODWORKING_R45_BUILDER_H
#define GEOMETRY_WOODWORKING_R45_BUILDER_H
#include "derived_placement.h"
#include "panel_support.h"
#include "member_placement.h"
#include "../../../geometry-core/kernel/codec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WOOD_R45_CANDIDATE_MAX 2048
#define WOOD_R45_KEY_BYTES 65
#define WOOD_R45_EDGE_PART_MAX 64 /* More parts than a 511-byte R41 key can encode. */
enum { WOOD_R45_BOUNDARY,WOOD_R45_EDGE_PRIMARY,WOOD_R45_SEAM_PRIMARY,
       WOOD_R45_SEAM_SECONDARY,WOOD_R45_FREE_EDGE,WOOD_R45_COVERED_EDGE,WOOD_R45_HOLE_EDGE };
typedef struct {
    char key[WOOD_R45_KEY_BYTES],edge_key[512];
    uint32_t edge_order[6*WOOD_R45_EDGE_PART_MAX];
    size_t edge_order_count;
    int kind,role,axis,line_axis;
    int64_t k,band;
    bool has_band,selectable,selected,valid;
    GeoCoord coordinate,range[2],through;
    uint32_t id;
    int duplicate_of;
    GeoCoord rect[4],length;
    char error[512];
} WoodR45Candidate;
typedef struct {
    WoodR45Candidate *items;
    size_t count,capacity;
} WoodR45Plan;
typedef struct {
    size_t component,edge;
    int hole; /* -1 is the outer loop; nonnegative indexes a hole loop. */
    char key[512];
    bool boundary_covered,on_boundary;
} WoodR45EdgeFact;

static void wood_r45_plan_free(WoodR45Plan *plan)
{if(plan){free(plan->items);memset(plan,0,sizeof *plan);}}
static bool wood_r45_error(char *error,size_t capacity,const char *message)
{if(error&&capacity)snprintf(error,capacity,"%s",message);return false;}
static GeoCoord wood_r45_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord wood_r45_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
static bool wood_r45_unsigned(const char **text,uint32_t *value)
{
    const unsigned char *p=(const unsigned char*)*text;uint32_t result=0;
    if(*p<'0'||*p>'9')return false;
    while(*p>='0'&&*p<='9'){uint32_t digit=*p++-'0';
        if(result>(UINT32_MAX-digit)/10)return false;result=result*10+digit;}
    *value=result;*text=(const char*)p;return true;
}
/* R41's source order is numeric and typed: outer e, hole h/e, column c,
 * beam b; obstacle sides u-,u+,v-,v+. Canonical JSON bytes are identity,
 * not ordering (e2 precedes e10; every column precedes every beam). */
static bool wood_r45_source_order(const char *name,uint32_t out[4])
{
    const char *p=name;char kind=*p++;memset(out,0,4*sizeof *out);
    if(kind=='e'){out[0]=0;return wood_r45_unsigned(&p,&out[1])&&!*p;}
    if(kind=='h'){out[0]=1;return wood_r45_unsigned(&p,&out[1])&&*p++=='e'&&wood_r45_unsigned(&p,&out[2])&&!*p;}
    if(kind!='c'&&kind!='b')return false;
    out[0]=kind=='c'?2:3;
    if(!wood_r45_unsigned(&p,&out[1])||*p++!=':')return false;
    if(!strcmp(p,"u-"))out[3]=0;else if(!strcmp(p,"u+"))out[3]=1;
    else if(!strcmp(p,"v-"))out[3]=2;else if(!strcmp(p,"v+"))out[3]=3;else return false;
    return true;
}
static bool wood_r45_edge_order(WoodR45Candidate *item,char *error,size_t cap)
{
    item->edge_order_count=0;if(!item->edge_key[0])return true;
    GeoJson j;bool ok=geo_json_parse(&j,item->edge_key)&&geo_json_is_array(&j,0);
    int count=ok?geo_json_size(&j,0):0;
    if(count<=0||count>WOOD_R45_EDGE_PART_MAX)ok=false;
    for(int k=0;k<count&&ok;++k){int part=geo_json_at(&j,0,k);char name[32];int64_t segment,total;
        uint32_t *values=&item->edge_order[item->edge_order_count];
        ok=geo_json_is_array(&j,part)&&geo_json_size(&j,part)==3&&
            geo_json_string(&j,geo_json_at(&j,part,0),name,sizeof name)&&wood_r45_source_order(name,values)&&
            geo_json_integer(&j,geo_json_at(&j,part,1),&segment)&&segment>=0&&segment<=UINT32_MAX&&
            geo_json_integer(&j,geo_json_at(&j,part,2),&total)&&total>segment&&total<=UINT32_MAX;
        if(ok){values[4]=(uint32_t)segment;values[5]=(uint32_t)total;item->edge_order_count+=6;}
    }
    geo_json_free(&j);return ok||wood_r45_error(error,cap,"R41: invalid complete derived edge key");
}
static bool wood_r45_key(uint32_t fill,WoodR45Candidate *item)
{
    char text[768];int n;
    if(item->edge_key[0])n=snprintf(text,sizeof text,"r45/1;fill=%u;kind=%d;edge=%s",fill,item->kind,item->edge_key);
    else n=snprintf(text,sizeof text,"r45/1;fill=%u;kind=%d;axis=%d;k=%lld;has-band=%d;band=%lld;range=%lld,%lld",
        fill,item->kind,item->line_axis,(long long)item->k,item->has_band?1:0,
        (long long)item->band,(long long)item->range[0],(long long)item->range[1]);
    if(n<0||(size_t)n>=sizeof text)return false;
    geo_sha256(text,(size_t)n,item->key);return true;
}
static bool wood_r45_append(WoodR45Plan *plan,uint32_t fill,const WoodR45Candidate *value,char *error,size_t cap)
{
    WoodR45Candidate item=*value;item.duplicate_of=-1;
    if(!wood_r45_edge_order(&item,error,cap))return false;
    if(!wood_r45_key(fill,&item))return wood_r45_error(error,cap,"I33 CAPACITY: R45 source key exceeds supported size");
    for(size_t i=0;i<plan->count;++i)if(!strcmp(plan->items[i].key,item.key))return true;
    if(plan->count==WOOD_R45_CANDIDATE_MAX)return wood_r45_error(error,cap,"I33 CAPACITY: R45 candidate limit is 2048; no truncated suggestion is returned");
    if(plan->count==plan->capacity){size_t n=plan->capacity?plan->capacity*2:32;if(n>WOOD_R45_CANDIDATE_MAX)n=WOOD_R45_CANDIDATE_MAX;
        WoodR45Candidate *next=realloc(plan->items,n*sizeof *next);if(!next)return wood_r45_error(error,cap,"I33 CAPACITY: R45 candidate workspace unavailable");
        plan->items=next;plan->capacity=n;}
    plan->items[plan->count++]=item;return true;
}
static int wood_r45_order(const void *left,const void *right)
{
    const WoodR45Candidate *a=left,*b=right;
    if(a->kind!=b->kind)return a->kind<b->kind?-1:1;
    if(a->edge_key[0]||b->edge_key[0]){
        size_t count=a->edge_order_count<b->edge_order_count?a->edge_order_count:b->edge_order_count;
        for(size_t k=0;k<count;++k)if(a->edge_order[k]!=b->edge_order[k])return a->edge_order[k]<b->edge_order[k]?-1:1;
        return a->edge_order_count<b->edge_order_count?-1:a->edge_order_count>b->edge_order_count;
    }
    if(a->line_axis!=b->line_axis)return a->line_axis<b->line_axis?-1:1;
    if(a->k!=b->k)return a->k<b->k?-1:1;
    if(a->has_band!=b->has_band)return a->has_band?1:-1;
    if(a->band!=b->band)return a->band<b->band?-1:1;
    if(a->range[0]!=b->range[0])return a->range[0]<b->range[0]?-1:1;
    return a->range[1]<b->range[1]?-1:a->range[1]>b->range[1];
}
static int wood_r45_coord_order(const void *left,const void *right)
{GeoCoord a=*(const GeoCoord*)left,b=*(const GeoCoord*)right;return a<b?-1:a>b;}
static size_t wood_r45_unique_coordinates(GeoCoord *values,size_t count)
{
    qsort(values,count,sizeof *values,wood_r45_coord_order);size_t used=0;
    for(size_t k=0;k<count;++k)if(!used||values[k]!=values[used-1])values[used++]=values[k];
    return used;
}
static GeoCoord wood_r45_coordinate_rank(const GeoCoord *values,size_t count,GeoCoord value)
{for(size_t k=0;k<count;++k)if(values[k]==value)return (GeoCoord)(2*k);return -1;}
/* Exact line/closed-region intersection through public K point predicates.
 * A common strictly increasing mapping on each coordinate axis maps all
 * vertex/source coordinates to even ranks. The cell midpoint maps to the odd
 * rank between its endpoints. Orthogonal containment and boundary contacts
 * depend only on order/equality, so this preserves them, including 1 mm cells.
 * The bounded temporary ranks also honour K's D1 predicate precondition at
 * both signed D1 endpoints; no coordinate doubling can overflow or exceed it.
 * Source ranges and the authored floor midpoint remain in the original units. */
static bool wood_r45_line_component(const WoodBoundaryRegion *region,const WoodR45Candidate *source,
    WoodR45Plan *plan,uint32_t fill,char *error,size_t cap)
{
    enum { CUT_MAX=(GEO_REGION_MAX_HOLES+1)*GEO_LOOP_MAX_VERTICES+2 };
    GeoCoord coordinates[2][CUT_MAX],cuts[CUT_MAX];size_t counts[2]={0},count=0;
    if(!region||!source||region->hole_count>GEO_REGION_MAX_HOLES||
       (source->axis!=0&&source->axis!=1)||!geo_coord_in_range(source->coordinate)||
       !geo_coord_in_range(source->range[0])||!geo_coord_in_range(source->range[1])||
       source->range[0]>=source->range[1])
        return wood_r45_error(error,cap,"D1/R45: invalid line intersection facts");
    GeoLoop2View source_holes[GEO_REGION_MAX_HOLES];
    GeoRegionView source_view=wood_pf_region_view(region,source_holes);
    if(!geo_region_is_valid(&source_view))return wood_r45_error(error,cap,"D1/R41: invalid derived component");
    WoodBoundaryRegion *scaled=malloc(sizeof *scaled);
    if(!scaled)return wood_r45_error(error,cap,"I33 CAPACITY: R45 line workspace unavailable");
    *scaled=*region;cuts[count++]=source->range[0];cuts[count++]=source->range[1];
    coordinates[source->axis][counts[source->axis]++]=source->range[0];
    coordinates[source->axis][counts[source->axis]++]=source->range[1];
    coordinates[1-source->axis][counts[1-source->axis]++]=source->coordinate;
    for(size_t h=0;h<=region->hole_count;++h){
        const WoodBoundaryLoop *loop=h?&region->holes[h-1]:&region->outline;
        for(size_t k=0;k<loop->count;++k){GeoCoord at=source->axis?loop->v[k].v:loop->v[k].u;
            if(at>source->range[0]&&at<source->range[1])cuts[count++]=at;
            coordinates[0][counts[0]++]=loop->v[k].u;coordinates[1][counts[1]++]=loop->v[k].v;
        }
    }
    size_t unique=wood_r45_unique_coordinates(cuts,count);
    for(int axis=0;axis<2;++axis)counts[axis]=wood_r45_unique_coordinates(coordinates[axis],counts[axis]);
    for(size_t h=0;h<=region->hole_count;++h){
        const WoodBoundaryLoop *loop=h?&region->holes[h-1]:&region->outline;
        WoodBoundaryLoop *copy=h?&scaled->holes[h-1]:&scaled->outline;
        for(size_t k=0;k<loop->count;++k){
            copy->v[k].u=wood_r45_coordinate_rank(coordinates[0],counts[0],loop->v[k].u);
            copy->v[k].v=wood_r45_coordinate_rank(coordinates[1],counts[1],loop->v[k].v);
        }
    }
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView view=wood_pf_region_view(scaled,holes);
    bool opened=false,ok=true;GeoCoord low=0,high=0;
    for(size_t k=0;k+1<unique&&ok;++k){GeoCoord a=cuts[k],b=cuts[k+1];
        GeoCoord along=(wood_r45_coordinate_rank(coordinates[source->axis],counts[source->axis],a)+
            wood_r45_coordinate_rank(coordinates[source->axis],counts[source->axis],b))/2;
        GeoCoord across=wood_r45_coordinate_rank(coordinates[1-source->axis],counts[1-source->axis],source->coordinate);
        GeoPoint2 midpoint=source->axis?(GeoPoint2){across,along}:(GeoPoint2){along,across};
        bool included=geo_region_contains_point(&view,midpoint);
        if(included){if(!opened)low=a;high=b;opened=true;}
        if(opened&&(!included||k+2==unique)){
            WoodR45Candidate item=*source;item.range[0]=low;item.range[1]=high;item.through=low+(high-low)/2;
            ok=wood_r45_append(plan,fill,&item,error,cap);opened=false;
        }
    }
    free(scaled);return ok;
}
static bool wood_r45_enumerate(uint32_t fill,int primary_axis,int side,
    const WoodDerivedValue *host,const WoodR45EdgeFact *edges,size_t edge_count,
    const WoodPanelLayout *layout,const WoodPanelSupport *support,
    WoodR45Plan *plan,char *error,size_t cap)
{
    if(!host||!layout||!support||(edge_count&&!edges)||host->component_count>GEO_PLACEMENT_COMPONENT_CAPACITY||
       (primary_axis!=0&&primary_axis!=1)||(side!=1&&side!=-1))
        return wood_r45_error(error,cap,"D45/R45: incomplete same-candidate facts");
    for(size_t k=0;k<edge_count;++k){const WoodR45EdgeFact *fact=&edges[k];
        if(fact->component>=host->component_count)return wood_r45_error(error,cap,"R41: outer edge component is missing");
        const WoodBoundaryRegion *component=&host->components[fact->component];
        if(fact->hole < -1||(fact->hole>=0&&(size_t)fact->hole>=component->hole_count))
            return wood_r45_error(error,cap,"R41: source edge loop is missing");
        const WoodBoundaryLoop *loop=fact->hole<0?&component->outline:&component->holes[fact->hole];
        if(fact->edge>=loop->count)return wood_r45_error(error,cap,"R41: outer edge is missing");
        GeoPoint2 a=loop->v[fact->edge],b=loop->v[(fact->edge+1)%loop->count];
        if(!geo_coord_in_range(a.u)||!geo_coord_in_range(a.v)||!geo_coord_in_range(b.u)||!geo_coord_in_range(b.v))
            return wood_r45_error(error,cap,"D1/R41: outer edge coordinate is out of range");
        WoodR45Candidate item={0};item.axis=a.u==b.u;item.line_axis=1-item.axis;
        item.coordinate=item.axis?a.u:a.v;item.range[0]=wood_r45_min(item.axis?a.v:a.u,item.axis?b.v:b.u);
        item.range[1]=wood_r45_max(item.axis?a.v:a.u,item.axis?b.v:b.u);item.through=item.range[0]+(item.range[1]-item.range[0])/2;
        item.role=item.axis==primary_axis?WOOD_MEMBER_ROLE_PRIMARY:WOOD_MEMBER_ROLE_BOUNDARY;
        item.kind=item.role==WOOD_MEMBER_ROLE_BOUNDARY?WOOD_R45_BOUNDARY:WOOD_R45_EDGE_PRIMARY;
        item.selectable=true;snprintf(item.edge_key,sizeof item.edge_key,"%s",fact->key);
        if(fact->hole>=0){item.kind=WOOD_R45_HOLE_EDGE;item.selectable=false;snprintf(item.error,sizeof item.error,"R45(3): hole loop has no edge member");}
        else if(loop->fixity[fact->edge]==WOOD_EDGE_FREE){item.kind=WOOD_R45_FREE_EDGE;item.selectable=false;snprintf(item.error,sizeof item.error,"R45(3): FREE edge has no edge member");}
        else if(item.role==WOOD_MEMBER_ROLE_BOUNDARY?fact->boundary_covered:fact->on_boundary){item.kind=WOOD_R45_COVERED_EDGE;item.selectable=false;snprintf(item.error,sizeof item.error,"R45(3): existing member covers this outer edge");}
        if(!wood_r45_append(plan,fill,&item,error,cap))return false;
    }
    for(size_t k=0;k<support->count;++k){const WoodPanelEffectiveSeam *seam=&support->seams[k];
        if(seam->line>=layout->seam_count)return wood_r45_error(error,cap,"R43: effective seam line is missing");
        const WoodPanelSeamLine *line=&layout->seams[seam->line];WoodR45Candidate item={0};
        if((line->axis!=0&&line->axis!=1)||!geo_coord_in_range(line->coordinate)||
           !geo_coord_in_range(seam->range[0])||!geo_coord_in_range(seam->range[1]))
            return wood_r45_error(error,cap,"D1/R43: effective seam coordinate is out of range");
        item.line_axis=line->axis;item.axis=1-line->axis;item.k=line->k;item.band=line->band;item.has_band=line->staggered;
        item.role=item.axis==primary_axis?WOOD_MEMBER_ROLE_PRIMARY:WOOD_MEMBER_ROLE_SECONDARY;
        item.kind=item.role==WOOD_MEMBER_ROLE_PRIMARY?WOOD_R45_SEAM_PRIMARY:WOOD_R45_SEAM_SECONDARY;item.selectable=true;
        item.coordinate=line->axis?side*line->coordinate:line->coordinate;
        int sign=item.axis?side:1;item.range[0]=wood_r45_min(sign*seam->range[0],sign*seam->range[1]);item.range[1]=wood_r45_max(sign*seam->range[0],sign*seam->range[1]);
        for(size_t c=0;c<host->component_count;++c)if(!wood_r45_line_component(&host->components[c],&item,plan,fill,error,cap))return false;
    }
    qsort(plan->items,plan->count,sizeof *plan->items,wood_r45_order);return true;
}
static bool wood_r45_same_line(const WoodR45Candidate *a,const WoodR45Candidate *b)
{return a->kind>=WOOD_R45_SEAM_PRIMARY&&a->kind<=WOOD_R45_SEAM_SECONDARY&&a->kind==b->kind&&
    a->line_axis==b->line_axis&&a->k==b->k&&a->has_band==b->has_band&&(!a->has_band||a->band==b->band);}
static bool wood_r45_same_span(const WoodR45Candidate *a,const WoodR45Candidate *b)
{return wood_r45_same_line(a,b)&&a->rect[a->axis]==b->rect[b->axis]&&a->rect[a->axis+2]==b->rect[b->axis+2];}
#endif
