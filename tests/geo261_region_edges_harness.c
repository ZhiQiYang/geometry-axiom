/* I2/I5 regression client. Only public K types and geometry operations. */
#include "geometry.h"
#include <stdio.h>
#include <string.h>

#define CHECK(c) do { if (!(c)) { fprintf(stderr, "line %d: %s\n", __LINE__, #c); return 1; } } while (0)
#define LOOP(a) ((GeoLoop2View){a, sizeof(a) / sizeof((a)[0])})

static int crossing_holes(void)
{
    const GeoPoint2 outer[]={{0,0},{100,0},{100,100},{0,100}};
    const GeoPoint2 horizontal[]={{10,40},{90,40},{90,60},{10,60}};
    const GeoPoint2 vertical[]={{40,10},{60,10},{60,90},{40,90}};
    GeoLoop2View holes[]={LOOP(horizontal),LOOP(vertical)};
    GeoRegionView region={LOOP(outer),holes,2};
    /* No vertex lies in the opposite hole: an edge test is essential. */
    for (size_t h=0;h<2;++h) for (size_t i=0;i<4;++i)
        CHECK(!geo_loop_contains_point(&holes[1-h],holes[h].v[i]));
    CHECK(!geo_region_is_valid(&region));
    GeoPoint2 reversed[4];
    for (size_t i=0;i<4;++i) reversed[i]=vertical[3-i];
    holes[1]=LOOP(reversed);
    CHECK(!geo_region_is_valid(&region));
    GeoLoop2View swap=holes[0];holes[0]=holes[1];holes[1]=swap;
    CHECK(!geo_region_is_valid(&region));
    return 0;
}

static int contact_controls(void)
{
    const GeoPoint2 outer[]={{0,0},{100,0},{100,100},{0,100}};
    const GeoPoint2 first[]={{10,10},{30,10},{30,30},{10,30}};
    const GeoPoint2 disjoint[]={{31,10},{50,10},{50,30},{31,30}};
    const GeoPoint2 point_touch[]={{30,30},{50,30},{50,50},{30,50}};
    const GeoPoint2 edge_touch[]={{30,10},{50,10},{50,30},{30,30}};
    const GeoPoint2 nested[]={{15,15},{20,15},{20,20},{15,20}};
    GeoLoop2View holes[]={LOOP(first),LOOP(disjoint)};
    GeoRegionView region={LOOP(outer),holes,2};
    CHECK(geo_region_is_valid(&region));
    holes[1]=LOOP(point_touch);CHECK(!geo_region_is_valid(&region));
    holes[1]=LOOP(edge_touch);CHECK(!geo_region_is_valid(&region));
    holes[1]=LOOP(nested);CHECK(!geo_region_is_valid(&region));
    holes[1]=LOOP(first);CHECK(!geo_region_is_valid(&region));
    region.hole_count=1;
    /* Hole-ring contact by a rectangle remains legal; interior overlap does not. */
    CHECK(geo_region_contains_rect(&region,0,0,10,100));
    CHECK(geo_region_contains_rect(&region,0,0,10,10));
    CHECK(!geo_region_contains_rect(&region,9,9,11,11));
    return 0;
}

static int unit_rectangles(void)
{
    const GeoCoord origins[]={0,-10,GEO_COORD_LIMIT-10,-GEO_COORD_LIMIT};
    for (size_t k=0;k<sizeof(origins)/sizeof(origins[0]);++k) {
        GeoCoord o=origins[k];
        GeoPoint2 outer[]={{o,o},{o+10,o},{o+10,o+10},{o,o+10}};
        for (GeoCoord width=1;width<=3;++width) for (GeoCoord height=1;height<=3;++height) {
            GeoPoint2 points[]={{o+2,o+2},{o+2+width,o+2},{o+2+width,o+2+height},{o+2,o+2+height}};
            GeoLoop2View hole=LOOP(points);
            GeoRegionView region={LOOP(outer),&hole,1};
            GeoRegionSetView set={&region,1};
            GeoRect2 same={o+2,o+2,o+2+width,o+2+height};
            CHECK(geo_region_is_valid(&region));
            CHECK(!geo_region_contains_rect(&region,same.min_u,same.min_v,same.max_u,same.max_v));
            CHECK(!geo_region_set_contains_rect(&set,&same));
            CHECK(!geo_region_contains_rect(&region,o+2,o+2,o+3,o+3));
            CHECK(geo_region_contains_rect(&region,o+1,o+2,o+2,o+2+height));
            CHECK(geo_region_contains_rect(&region,o+2,o+1,o+2+width,o+2));
            CHECK(geo_region_contains_rect(&region,o+2+width,o+2,o+3+width,o+2+height));
            CHECK(geo_region_contains_rect(&region,o+2,o+2+height,o+2+width,o+3+height));
            CHECK(geo_region_contains_point(&region,(GeoPoint2){o+2,o+2}));
        }
    }
    return 0;
}

static int unit_strips(void)
{
    const GeoPoint2 outer[]={{0,0},{10,0},{10,10},{0,10}};
    const GeoPoint2 points[]={{2,2},{3,2},{3,3},{2,3}};
    GeoLoop2View hole=LOOP(points);
    GeoRegionView region={LOOP(outer),&hole,1};
    GeoRegionSetView set={&region,1};
    GeoInterval intervals[2];GeoCoord cuts[8];
    GeoIntervalBuffer out={intervals,2,0};
    for (unsigned axis=0;axis<2;++axis) {
        CHECK(geo_strip_intervals(&set,axis!=0,(GeoInterval){2,3},NULL,0,&out,(GeoStripScratch){cuts,8})==GEO_GEOMETRY_OK);
        CHECK(out.count==2);
        CHECK(intervals[0].start==0&&intervals[0].end==2);
        CHECK(intervals[1].start==3&&intervals[1].end==10);
        /* A width band that merely touches the hole is still complete. */
        CHECK(geo_strip_intervals(&set,axis!=0,(GeoInterval){1,2},NULL,0,&out,(GeoStripScratch){cuts,8})==GEO_GEOMETRY_OK);
        CHECK(out.count==1&&intervals[0].start==0&&intervals[0].end==10);
        out.capacity=1;
        CHECK(geo_strip_intervals(&set,axis!=0,(GeoInterval){2,3},NULL,0,&out,(GeoStripScratch){cuts,8})==GEO_GEOMETRY_CAPACITY);
        CHECK(out.count==0);out.capacity=2;
    }
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 70;
    if(!strcmp(argv[1],"crossing-holes"))return crossing_holes();
    if(!strcmp(argv[1],"contact-controls"))return contact_controls();
    if(!strcmp(argv[1],"unit-rectangles"))return unit_rectangles();
    if(!strcmp(argv[1],"unit-strips"))return unit_strips();
    return 71;
}
