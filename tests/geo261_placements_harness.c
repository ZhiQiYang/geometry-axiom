/* Public API geometry witnesses plus private POD-byte checks for snapshot and
 * zero-tail guarantees. This client links only the real K placement/region/
 * geometry objects; it has no host or woodworking definitions. */
#include "placements.h"
#include "internal/placements.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(name,condition) do{if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}}while(0)
static GeoFrame frame(void)
{return (GeoFrame){{10,-20,30},{0,1,0},{0,0,1},{1,0,0}};}
static GeoPlacementDefinition rectangle(uint32_t id)
{GeoPlacementDefinition p;memset(&p,0,sizeof p);p.id=id;p.frame=frame();p.domain=GEO_PLACEMENT_RECT;p.rect=(GeoRect2){-10,-5,30,20};return p;}
static void loop_box(GeoRegionLoop *loop,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{memset(loop,0,sizeof *loop);loop->count=4;loop->v[0]=(GeoPoint2){a,b};loop->v[1]=(GeoPoint2){c,b};loop->v[2]=(GeoPoint2){c,d};loop->v[3]=(GeoPoint2){a,d};}
static GeoRegionDefinition region(uint32_t id,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{GeoRegionDefinition r;memset(&r,0,sizeof r);r.id=id;loop_box(&r.outline,a,b,c,d);return r;}
static GeoPlacementDefinition components(uint32_t id)
{GeoPlacementDefinition p=rectangle(id);p.domain=GEO_PLACEMENT_REGION_SET;p.rect=(GeoRect2){0};p.component_count=2;
 p.components[0]=region(700,-20,-10,-10,0);p.components[1]=region(900,10,20,40,50);return p;}
static bool zero_bytes(const void *data,size_t count)
{const unsigned char *bytes=data;for(size_t i=0;i<count;++i)if(bytes[i])return false;return true;}
static bool same_rect(GeoRect2 a,GeoRect2 b)
{return a.min_u==b.min_u&&a.min_v==b.min_v&&a.max_u==b.max_u&&a.max_v==b.max_v;}

static int storage(void)
{
    GeoPlacementStore *store=geo_placements_create();CHECK("store-create",store&&geo_placements_count(store)==0&&zero_bytes(store,sizeof *store));
    GeoPlacementDefinition expected=rectangle(UINT32_MAX),noisy;memset(&noisy,0xa5,sizeof noisy);noisy.id=expected.id;noisy.frame=expected.frame;noisy.domain=expected.domain;noisy.rect=expected.rect;
    CHECK("store-put-noisy",geo_placements_put(store,&noisy,NULL));const GeoPlacementDefinition *saved=geo_placements_find(store,UINT32_MAX);
    CHECK("store-zero-inactive",saved&&!memcmp(saved,&expected,sizeof expected));
    noisy.rect.min_u=-999;CHECK("store-owns-rectangle",saved->rect.min_u==-10);
    CHECK("store-self-alias",geo_placements_stage(store,saved)&&!memcmp(geo_placements_at(store,0),&expected,sizeof expected));
    GeoPlacementDefinition set=components(3);set.components[0].hole_count=1;loop_box(&set.components[0].holes[0],-18,-8,-12,-2);
    CHECK("store-put-set",geo_placements_put(store,&set,NULL));GeoPlacementDefinition active=set;
    set.components[0].outline.v[0].u=-200;set.components[0].holes[0].v[0].u=-300;
    saved=geo_placements_find(store,3);CHECK("store-owns-all-points",saved->components[0].outline.v[0].u==-20&&saved->components[0].holes[0].v[0].u==-18);
    CHECK("store-set-self-alias",geo_placements_stage(store,saved)&&!memcmp(geo_placements_find(store,3),&active,sizeof active));
    GeoPlacementStore *clone=geo_placements_clone(store),*inline_copy=malloc(sizeof *inline_copy);CHECK("store-clone",clone&&inline_copy&&clone!=store);
    *inline_copy=*store;CHECK("store-inline-pod",!memcmp(inline_copy,store,sizeof *store));
    active.components[1].outline.v[0].u=11;CHECK("store-candidate-stage",geo_placements_stage(clone,&active));
    CHECK("store-independent-copy",geo_placements_find(store,3)->components[1].outline.v[0].u==10&&geo_placements_find(inline_copy,3)->components[1].outline.v[0].u==10);
    CHECK("store-remove",geo_placements_remove(store,UINT32_MAX)&&geo_placements_at(store,0)->id==3&&geo_placements_count(store)==1);
    CHECK("store-zero-removed-tail",zero_bytes(&store->items[1],sizeof store->items[1]));
    CHECK("store-missing-query",!geo_placements_at(store,1)&&!geo_placements_find(store,UINT32_MAX)&&!geo_placements_remove(store,123));
    free(inline_copy);geo_placements_destroy(clone);geo_placements_destroy(store);
    CHECK("store-null-api",geo_placements_count(NULL)==0&&!geo_placements_at(NULL,0)&&!geo_placements_find(NULL,0)&&!geo_placements_clone(NULL));geo_placements_destroy(NULL);return 0;
}
static int capacity(void)
{
    GeoPlacementStore *store=geo_placements_create();CHECK("capacity-create",store);
    for(uint32_t i=0;i<GEO_PLACEMENT_CAPACITY;++i){GeoPlacementDefinition p=rectangle(i);CHECK("capacity-full-sixteen",geo_placements_put(store,&p,NULL));}
    CHECK("capacity-count",geo_placements_count(store)==16);GeoPlacementStore *before=geo_placements_clone(store);CHECK("capacity-snapshot",before);
    GeoPlacementDefinition p=rectangle(UINT32_MAX);CHECK("capacity-reject-seventeenth",!geo_placements_put(store,&p,NULL)&&!memcmp(store,before,sizeof *store));
    p.id=7;p.rect.max_u=99;CHECK("capacity-replace-at-full",geo_placements_put(store,&p,NULL)&&geo_placements_count(store)==16&&geo_placements_at(store,7)->rect.max_u==99);
    CHECK("capacity-delete-order",geo_placements_remove(store,7)&&geo_placements_at(store,7)->id==8&&geo_placements_at(store,14)->id==15);
    p.id=UINT32_MAX;CHECK("capacity-reuse-slot",geo_placements_put(store,&p,NULL)&&geo_placements_at(store,15)->id==UINT32_MAX);
    geo_placements_destroy(before);geo_placements_destroy(store);return 0;
}
static int validation(void)
{
    GeoPlacementStore *store=geo_placements_create();GeoRegionStore *regions=geo_regions_create();CHECK("validation-create",store&&regions);
    GeoPlacementDefinition good=rectangle(1);CHECK("validation-good",geo_placements_put(store,&good,regions));GeoPlacementStore *before=geo_placements_clone(store);CHECK("validation-snapshot",before);
    GeoPlacementDefinition p=good;p.frame.normal=(GeoVector3){-1,0,0};CHECK("validation-handed-frame",!geo_placements_put(store,&p,regions)&&!memcmp(store,before,sizeof *store));
    p=good;p.frame.origin.z=GEO_COORD_LIMIT+1;CHECK("validation-frame-range",!geo_placements_put(store,&p,regions));
    p=good;p.rect.max_u=GEO_COORD_LIMIT+1;CHECK("validation-rect-range",!geo_placements_put(store,&p,regions));
    p=good;p.rect.max_u=p.rect.min_u;CHECK("validation-positive-rect",!geo_placements_put(store,&p,regions));
    p=good;p.domain=(GeoPlacementDomain)99;CHECK("validation-domain-tag",!geo_placements_put(store,&p,regions));
    p=good;p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=0;CHECK("validation-missing-reference",!geo_placements_put(store,&p,regions));
    GeoRegionDefinition r=region(0,-10,-10,10,10);CHECK("validation-region-zero-id",geo_regions_put(regions,&r)&&geo_placements_put(store,&p,regions));
    p=components(2);p.components[1].outline.v[1].v+=1;CHECK("validation-every-component",!geo_placements_put(store,&p,regions));
    p=components(2);p.components[1].hole_count=1;loop_box(&p.components[1].holes[0],10,20,12,22);CHECK("validation-hole-touch",!geo_placements_put(store,&p,regions));
    p=components(2);p.component_count=0;CHECK("validation-empty-set",geo_placements_put(store,&p,regions)&&geo_placements_find(store,2)->component_count==0);
    p=components(2);p.component_count=GEO_PLACEMENT_COMPONENT_CAPACITY;for(size_t c=2;c<p.component_count;++c)p.components[c]=p.components[0];
    CHECK("validation-eight-components",geo_placements_put(store,&p,regions));
    p.component_count=GEO_PLACEMENT_COMPONENT_CAPACITY+1;CHECK("validation-component-limit",!geo_placements_put(store,&p,regions));
    geo_placements_destroy(before);geo_placements_destroy(store);geo_regions_destroy(regions);return 0;
}
static int staging(void)
{
    GeoPlacementStore *store=geo_placements_create();CHECK("stage-create",store);GeoPlacementDefinition p=rectangle(1);p.frame.axis_u=(GeoVector3){0};p.rect.max_u=p.rect.min_u;
    CHECK("stage-before-geometry-validation",geo_placements_stage(store,&p)&&!geo_placement_is_valid(geo_placements_find(store,1),NULL));
    p=rectangle(2);p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=UINT32_MAX;CHECK("stage-before-reference-validation",geo_placements_stage(store,&p)&&!geo_placement_is_valid(geo_placements_find(store,2),NULL));
    p=components(3);p.components[0].outline.count=0;CHECK("stage-before-loop-validation",geo_placements_stage(store,&p)&&!geo_placement_is_valid(geo_placements_find(store,3),NULL));
    GeoPlacementStore *before=geo_placements_clone(store);CHECK("stage-snapshot",before);
    p.component_count=GEO_PLACEMENT_COMPONENT_CAPACITY+1;CHECK("stage-component-bound",!geo_placements_stage(store,&p)&&!memcmp(store,before,sizeof *store));
    p=components(3);p.components[1].hole_count=GEO_REGION_MAX_HOLES+1;CHECK("stage-hole-bound",!geo_placements_stage(store,&p));
    p=components(3);p.components[1].outline.count=GEO_LOOP_MAX_VERTICES+1;CHECK("stage-outline-bound",!geo_placements_stage(store,&p));
    p=components(3);p.components[1].hole_count=1;p.components[1].holes[0].count=GEO_LOOP_MAX_VERTICES+1;CHECK("stage-hole-vertex-bound",!geo_placements_stage(store,&p));
    CHECK("stage-all-failures-atomic",!memcmp(store,before,sizeof *store));
    p=rectangle(4);p.domain=(GeoPlacementDomain)-1;CHECK("stage-domain-bound",!geo_placements_stage(store,&p));
    p=rectangle(4);p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=5;p.component_count=(size_t)-1;
    CHECK("stage-ignores-inactive-counts",geo_placements_stage(store,&p)&&geo_placements_find(store,4)->component_count==0);
    geo_placements_destroy(before);geo_placements_destroy(store);return 0;
}
static int rectangles(void)
{
    GeoPlacementDefinition p=rectangle(1);CHECK("rect-contact-point",geo_placement_contains_point(&p,NULL,(GeoPoint2){30,20})&&geo_placement_contains_point(&p,NULL,(GeoPoint2){-10,-5}));
    CHECK("rect-outside-point",!geo_placement_contains_point(&p,NULL,(GeoPoint2){31,20})&&!geo_placement_contains_point(&p,NULL,(GeoPoint2){0,-6}));
    GeoRect2 r={-10,-5,30,20};CHECK("rect-full-containment",geo_placement_contains_rect(&p,NULL,&r));r.min_u=-11;CHECK("rect-outside-rectangle",!geo_placement_contains_rect(&p,NULL,&r));
    r=(GeoRect2){0,0,0,0};CHECK("rect-original-degenerate-query",geo_placement_contains_rect(&p,NULL,&r));r=(GeoRect2){5,5,-5,-5};CHECK("rect-original-inverted-query",geo_placement_contains_rect(&p,NULL,&r));
    size_t index=91;r=(GeoRect2){0,0,10,10};CHECK("rect-component-zero",geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==0);
    index=91;r.max_u=100;CHECK("rect-failed-index-unchanged",!geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==91);
    GeoRect2 out={1,2,3,4};CHECK("rect-local-bounds",geo_placement_local_bounds(&p,NULL,&out)&&same_rect(out,p.rect));p.rect.max_u=p.rect.min_u;out=(GeoRect2){1,2,3,4};
    CHECK("rect-invalid-bounds-unchanged",!geo_placement_local_bounds(&p,NULL,&out)&&same_rect(out,(GeoRect2){1,2,3,4}));return 0;
}
static int references(void)
{
    GeoRegionStore *regions=geo_regions_create();CHECK("reference-create",regions);GeoRegionDefinition r=region(29,0,0,20,20);r.hole_count=1;loop_box(&r.holes[0],5,5,15,15);CHECK("reference-region",geo_regions_put(regions,&r));
    GeoPlacementDefinition p=rectangle(1);p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=29;
    CHECK("reference-hole-interior",!geo_placement_contains_point(&p,regions,(GeoPoint2){10,10}));
    CHECK("reference-hole-contact",geo_placement_contains_point(&p,regions,(GeoPoint2){5,10})&&geo_placement_contains_point(&p,regions,(GeoPoint2){0,0}));
    GeoRect2 q={0,0,5,20};CHECK("reference-rect-contact",geo_placement_contains_rect(&p,regions,&q));q.max_u=6;CHECK("reference-hole-crossing",!geo_placement_contains_rect(&p,regions,&q));
    q=(GeoRect2){2,2,2,2};CHECK("reference-positive-query-required",!geo_placement_contains_rect(&p,regions,&q));
    GeoRect2 bounds;CHECK("reference-bounds",geo_placement_local_bounds(&p,regions,&bounds)&&same_rect(bounds,(GeoRect2){0,0,20,20}));
    r.hole_count=0;CHECK("reference-update",geo_regions_put(regions,&r)&&geo_placement_contains_point(&p,regions,(GeoPoint2){10,10}));
    CHECK("reference-remove",geo_regions_remove(regions,29));bounds=(GeoRect2){1,2,3,4};CHECK("reference-missing-query",!geo_placement_contains_point(&p,regions,(GeoPoint2){0,0})&&!geo_placement_local_bounds(&p,regions,&bounds)&&same_rect(bounds,(GeoRect2){1,2,3,4}));
    geo_regions_destroy(regions);return 0;
}
static int sets(void)
{
    GeoPlacementDefinition p=components(1);CHECK("set-second-point",geo_placement_contains_point(&p,NULL,(GeoPoint2){25,35}));CHECK("set-gap-point",!geo_placement_contains_point(&p,NULL,(GeoPoint2){0,5}));
    GeoRect2 r={20,30,30,40};size_t index=99;CHECK("set-second-rectangle",geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==1);
    r=(GeoRect2){-15,-5,20,30};index=99;CHECK("set-no-bbox-substitution",!geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==99);
    GeoRect2 out;CHECK("set-all-component-bounds",geo_placement_local_bounds(&p,NULL,&out)&&same_rect(out,(GeoRect2){-20,-10,40,50}));
    p.components[1]=p.components[0];r=(GeoRect2){-18,-8,-12,-2};index=99;CHECK("set-first-complete-component",geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==0);
    p.components[0]=region(7,0,0,10,10);p.components[1]=region(8,10,0,20,10);r=(GeoRect2){5,2,15,8};CHECK("set-no-spanning-union",!geo_placement_contains_rect(&p,NULL,&r));
    p.component_count=0;out=(GeoRect2){1,2,3,4};index=99;
    CHECK("set-empty-queries",!geo_placement_contains_point(&p,NULL,(GeoPoint2){0,0})&&!geo_placement_component_for_rect(&p,NULL,&r,&index)&&index==99&&!geo_placement_local_bounds(&p,NULL,&out)&&same_rect(out,(GeoRect2){1,2,3,4}));return 0;
}
static int views(void)
{
    GeoPlacementDefinition a=rectangle(1),b=rectangle(2);b.rect=(GeoRect2){100,200,300,400};GeoPlacementViewScratch sa,sb;GeoRegionSetView va,vb;
    CHECK("view-rectangle",geo_placement_domain_view(&a,NULL,&sa,&va)&&va.count==1&&va.regions[0].outline.count==4&&va.regions[0].hole_count==0);
    CHECK("view-caller-scratch",va.regions==sa.regions&&va.regions[0].outline.v==sa.rectangle&&geo_placement_domain_view(&b,NULL,&sb,&vb)&&sa.rectangle[0].u==-10&&sb.rectangle[0].u==100);
    a=components(1);a.components[1].hole_count=1;loop_box(&a.components[1].holes[0],15,25,20,30);
    CHECK("view-all-components",geo_placement_domain_view(&a,NULL,&sa,&va)&&va.count==2&&va.regions[1].hole_count==1&&va.regions[1].outline.v==a.components[1].outline.v&&va.regions[1].holes==sa.holes[1]);
    CHECK("view-borrows-coordinate-owner",va.regions[1].holes[0].v==a.components[1].holes[0].v);a.component_count=0;CHECK("view-empty-valid",geo_placement_domain_view(&a,NULL,&sa,&va)&&va.count==0);
    a.domain=GEO_PLACEMENT_REGION_REF;a.region_id=999;CHECK("view-missing-clears-output",!geo_placement_domain_view(&a,NULL,&sa,&va)&&va.count==0&&!va.regions);
    CHECK("view-null",!geo_placement_domain_view(NULL,NULL,&sa,&va)&&!geo_placement_domain_view(&b,NULL,NULL,&va)&&!geo_placement_domain_view(&b,NULL,&sb,NULL));return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"storage"))return storage();if(!strcmp(argv[1],"capacity"))return capacity();if(!strcmp(argv[1],"validation"))return validation();if(!strcmp(argv[1],"stage"))return staging();if(!strcmp(argv[1],"rectangle"))return rectangles();if(!strcmp(argv[1],"reference"))return references();if(!strcmp(argv[1],"components"))return sets();if(!strcmp(argv[1],"views"))return views();return 2;}
