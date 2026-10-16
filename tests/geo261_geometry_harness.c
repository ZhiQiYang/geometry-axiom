/* Public geometry client. No application structs, legacy scene or policy. */
#include "geometry.h"
#include <stdio.h>
#include <string.h>
#include <limits.h>
#define CHECK(condition) do {if(!(condition)){fprintf(stderr,"line %d: %s\n",__LINE__,#condition);return 1;}} while(0)
static const GeoPoint2 square[]={{0,0},{100,0},{100,100},{0,100}};
static const GeoPoint2 notch[]={{0,0},{100,0},{100,100},{60,100},{60,40},{40,40},{40,100},{0,100}};
static const GeoPoint2 hole_points[]={{40,40},{60,40},{60,60},{40,60}};
static GeoLoop2View loop(const GeoPoint2 *points,size_t count)
{return (GeoLoop2View){points,count};}

static int frames(void)
{
    GeoVector3 axes[]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    unsigned count=0;
    for(unsigned u=0;u<6;++u)for(unsigned v=0;v<6;++v){
        if(geo_vector_dot(axes[u],axes[v]))continue;
        GeoFrame frame={{13,-17,23},axes[u],axes[v],geo_vector_cross(axes[u],axes[v])};
        CHECK(geo_frame_is_valid(&frame));
        GeoPoint3 point=geo_frame_point(&frame,-31,47,0);
        GeoPoint2 projected=geo_frame_project_uv(&frame,point);
        CHECK(projected.u==-31&&projected.v==47);++count;
        frame.normal=geo_vector_negate(frame.normal);CHECK(!geo_frame_is_valid(&frame));
    }
    CHECK(count==24);
    GeoFrame invalid={{0,0,0},{INT64_MAX,0,0},{0,1,0},{0,0,1}};
    CHECK(!geo_frame_is_valid(&invalid));
    invalid=(GeoFrame){{GEO_COORD_LIMIT+1,0,0},{1,0,0},{0,1,0},{0,0,1}};
    CHECK(!geo_frame_is_valid(&invalid));
    return 0;
}
static int loops(void)
{
    GeoLoop2View view=loop(notch,8);
    CHECK(geo_loop_is_valid(&view));
    CHECK(geo_loop_contains_point(&view,(GeoPoint2){40,70}));
    CHECK(!geo_loop_contains_point(&view,(GeoPoint2){50,70}));
    CHECK(geo_loop_contains_rect(&view,0,0,100,40));
    CHECK(geo_loop_contains_rect(&view,0,0,40,100));
    CHECK(!geo_loop_contains_rect(&view,20,20,80,80));
    /* Four corners on the ring do not make the open notch part of its region. */
    CHECK(!geo_loop_contains_rect(&view,40,50,60,70));
    GeoPoint2 collinear[]={{0,0},{50,0},{100,0},{100,100},{0,100}};
    view=loop(collinear,5);CHECK(geo_loop_is_valid(&view));CHECK(view.count==5);
    GeoPoint2 crossing[]={{0,0},{80,0},{80,80},{20,80},{20,-20},{60,-20},{60,60},{0,60}};
    view=loop(crossing,8);CHECK(!geo_loop_is_valid(&view));
    view=loop(NULL,4);CHECK(!geo_loop_is_valid(&view));
    return 0;
}
static int regions(void)
{
    GeoLoop2View hole=loop(hole_points,4);
    GeoRegionView region={loop(square,4),&hole,1};
    CHECK(geo_region_is_valid(&region));
    CHECK(geo_region_contains_point(&region,(GeoPoint2){40,50}));
    CHECK(!geo_region_contains_point(&region,(GeoPoint2){50,50}));
    CHECK(geo_region_contains_rect(&region,0,0,40,100));
    CHECK(!geo_region_contains_rect(&region,30,30,70,70));
    CHECK(!geo_region_contains_rect(&region,40,40,60,60));
    GeoPoint2 touching[]={{0,40},{20,40},{20,60},{0,60}};
    hole=loop(touching,4);CHECK(!geo_region_is_valid(&region));
    hole=loop(NULL,4);CHECK(!geo_region_is_valid(&region));
    return 0;
}
static int clipping(void)
{
    GeoLoop2View view=loop(notch,8);GeoSegment2 segments[2];size_t count=99;
    CHECK(geo_loop_clip_line(&view,true,70,segments,2,&count)==GEO_GEOMETRY_OK);
    CHECK(count==2&&segments[0].start.u==0&&segments[0].end.u==40&&segments[1].start.u==60&&segments[1].end.u==100);
    count=99;segments[0].start.u=-5;
    CHECK(geo_loop_clip_line(&view,true,70,segments,1,&count)==GEO_GEOMETRY_CAPACITY);
    CHECK(!count&&segments[0].start.u==-5);
    CHECK(geo_loop_clip_line(&view,true,10,segments,2,&count)==GEO_GEOMETRY_OK);
    CHECK(count==1&&segments[0].start.u==0&&segments[0].end.u==100);
    return 0;
}
static int boxes(void)
{
    GeoBox3 box={{{10,20,30},{0,1,0},{0,0,1},{1,0,0}},{100,20,30}};
    GeoVector3 axes[]={box.frame.axis_u,box.frame.axis_v,box.frame.normal};
    for(unsigned axis=0;axis<3;++axis)for(unsigned side=0;side<2;++side){
        GeoQuad3 face;CHECK(geo_box_face(&box,axis,side,&face));
        GeoVector3 a={face.vertices[1].x-face.vertices[0].x,face.vertices[1].y-face.vertices[0].y,face.vertices[1].z-face.vertices[0].z};
        GeoVector3 b={face.vertices[2].x-face.vertices[1].x,face.vertices[2].y-face.vertices[1].y,face.vertices[2].z-face.vertices[1].z};
        GeoCoord orientation=geo_vector_dot(geo_vector_cross(a,b),axes[axis]);
        CHECK(side?orientation>0:orientation<0);
    }
    GeoRect2 projected=geo_aabb_project_uv(&box.frame,(GeoPoint3){10,20,30},(GeoPoint3){40,120,50});
    CHECK(projected.min_u==0&&projected.max_u==100&&projected.min_v==0&&projected.max_v==20);
    GeoRect2 rect=geo_rectangle_footprint(&box.frame,(GeoPoint2){50,50},geo_vector_negate(box.frame.axis_u),geo_vector_negate(box.frame.axis_v),30,10);
    CHECK(rect.min_u==20&&rect.max_u==50&&rect.min_v==40&&rect.max_v==50);
    GeoRect2 touching={50,40,60,50},overlap={49,40,60,50};
    CHECK(!geo_rect_overlap_positive(&rect,&touching));CHECK(geo_rect_overlap_positive(&rect,&overlap));
    return 0;
}
static int strips(void)
{
    GeoLoop2View hole=loop(hole_points,4);
    GeoPoint2 distant[]={{200,0},{300,0},{300,100},{200,100}};
    GeoRegionView regions[]={{loop(square,4),&hole,1},{loop(distant,4),NULL,0}};
    GeoRegionSetView domain={regions,2};GeoRect2 obstacles[]={{10,45,30,55}};
    GeoInterval intervals[8];GeoCoord cuts[32];GeoIntervalBuffer result={intervals,8,0};
    CHECK(geo_strip_intervals(&domain,false,(GeoInterval){45,55},obstacles,1,&result,(GeoStripScratch){cuts,32})==GEO_GEOMETRY_OK);
    CHECK(result.count==4);
    CHECK(intervals[0].start==0&&intervals[0].end==10&&intervals[1].start==30&&intervals[1].end==40);
    CHECK(intervals[2].start==60&&intervals[2].end==100&&intervals[3].start==200&&intervals[3].end==300);
    CHECK(geo_strip_intervals(&domain,false,(GeoInterval){0,40},NULL,0,&result,(GeoStripScratch){cuts,32})==GEO_GEOMETRY_OK);
    CHECK(result.count==2&&intervals[0].start==0&&intervals[0].end==100);
    CHECK(geo_strip_intervals(&domain,false,(GeoInterval){45,55},NULL,0,&result,(GeoStripScratch){cuts,1})==GEO_GEOMETRY_CAPACITY);
    CHECK(!result.count);
    result.capacity=1;
    CHECK(geo_strip_intervals(&domain,false,(GeoInterval){45,55},NULL,0,&result,(GeoStripScratch){cuts,32})==GEO_GEOMETRY_CAPACITY);
    CHECK(!result.count);
    domain.count=0;
    CHECK(geo_strip_intervals(&domain,false,(GeoInterval){45,55},NULL,0,&result,(GeoStripScratch){cuts,32})==GEO_GEOMETRY_OK);
    CHECK(!result.count);
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 70;
    if(!strcmp(argv[1],"frames"))return frames();
    if(!strcmp(argv[1],"loops"))return loops();
    if(!strcmp(argv[1],"regions"))return regions();
    if(!strcmp(argv[1],"clipping"))return clipping();
    if(!strcmp(argv[1],"boxes"))return boxes();
    if(!strcmp(argv[1],"strips"))return strips();
    return 71;
}
