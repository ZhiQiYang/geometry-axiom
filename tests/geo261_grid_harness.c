#include "grid.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

static int64_t value(const char *s){return strtoll(s,NULL,10);}
int main(int argc,char **argv)
{
    if(argc<2)return 2;
    if(!strcmp(argv[1],"center")&&argc==6){
        printf("%" PRId64 "\n",geo_period_center(value(argv[2]),value(argv[3]),value(argv[4]),value(argv[5])));return 0;
    }
    if(!strcmp(argv[1],"shift")&&argc==5){
        printf("%" PRId64 "\n",geo_alternating_shift(value(argv[2])!=0,value(argv[3]),value(argv[4])));return 0;
    }
    if(!strcmp(argv[1],"coordinate")&&argc==6){
        GeoLattice g={value(argv[2]),value(argv[3]),value(argv[4])};GeoCoord out=197;
        bool ok=geo_lattice_coord(&g,value(argv[5]),&out);printf("%d %" PRId64 "\n",ok,out);return 0;
    }
    if(!strcmp(argv[1],"window")&&argc==9){
        GeoLattice g={value(argv[2]),value(argv[3]),value(argv[4])};GeoLatticeLine lines[64];
        GeoLatticeWindow out={.lines=lines,.capacity=64};
        GeoGridStatus status=geo_lattice_window(&g,value(argv[5]),value(argv[6]),(size_t)value(argv[7]),value(argv[8])!=0,&out);
        printf("%d %d %" PRId64 " %" PRId64 " %" PRIu64 " %" PRIu64 " %zu",status,out.defined,out.first,out.last,out.total,out.stride,out.count);
        for(size_t i=0;i<out.count;++i)printf(" %" PRId64 " %" PRId64,lines[i].index,lines[i].coordinate);
        puts("");return 0;
    }
    if(!strcmp(argv[1],"finite")&&argc==8){
        GeoFiniteSequence d={.kind=GEO_SEQUENCE_BODY_GAP,.anchor=value(argv[2]),.body=value(argv[3]),.gap=value(argv[4])};
        GeoCoord out[64];size_t n=0;GeoGridStatus status=geo_finite_sequence(&d,value(argv[5]),value(argv[6]),out,(size_t)value(argv[7]),&n);
        printf("%d %zu",status,n);for(size_t i=0;i<n;++i)printf(" %" PRId64,out[i]);puts("");return 0;
    }
    if(!strcmp(argv[1],"subdivide")&&argc==6){
        GeoCoord out[64];size_t n=0;GeoGridStatus status=geo_interval_subdivide(value(argv[2]),value(argv[3]),(unsigned)value(argv[4]),out,(size_t)value(argv[5]),&n);
        printf("%d %zu",status,n);for(size_t i=0;i<n;++i)printf(" %" PRId64,out[i]);puts("");return 0;
    }
    if(!strcmp(argv[1],"area")&&argc==6){
        /* Union of disjoint rectangles [0,0,10,4] and [0,4,4,10]. */
        GeoPoint2 pts[]={{0,0},{10,0},{10,4},{4,4},{4,10},{0,10}};
        GeoLoop2View loop={pts,6};GeoRect2 rect={value(argv[2]),value(argv[3]),value(argv[4]),value(argv[5])};GeoCoord area=197;
        GeoGeometryStatus status=geo_loop_rect_area2(&loop,&rect,&area);printf("%d %" PRId64 "\n",status,area);return 0;
    }
    if(!strcmp(argv[1],"regions")){
        GeoPoint2 a[]={{0,0},{10,0},{10,10},{0,10}},h[]={{2,2},{8,2},{8,8},{2,8}},b[]={{20,0},{30,0},{30,10},{20,10}};
        GeoLoop2View hole={h,4};GeoRegionView regions[]={{{a,4},&hole,1},{{b,4},NULL,0}};GeoRegionSetView domain={regions,2};
        GeoRect2 queries[]={{2,2,8,8},{9,0,21,1},{10,0,20,10},{19,2,21,3},{0,0,1,1}};
        for(size_t i=0;i<5;++i)printf("%d ",geo_region_set_intersects_rect_positive(&domain,&queries[i]));puts("");return 0;
    }
    return 2;
}
