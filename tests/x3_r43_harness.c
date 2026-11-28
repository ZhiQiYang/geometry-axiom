/* Independent cell-occupancy oracle for neutral section/edge geometry. */
#include "geometry.h"
#include <stdio.h>

#define CHECK(name,condition) do {if(!(condition)){fprintf(stderr,"ASSERT:" name "\n");return 1;}} while(0)

static const GeoAxisBox2 catalog[]={
    {{-3,-2},{0,2}},{{0,-2},{3,2}},{{-2,-3},{2,-1}},{{-1,-1},{1,3}},
    {{-3,0},{-2,3}},{{1,0},{3,1}},{{-3,-3},{3,3}},{{2,-3},{3,-2}}
};

int main(void)
{
    GeoAxisBox2 touching[]={{{90,0},{105,300}},{{105,0},{120,300}}};
    GeoInterval intervals[8];
    size_t n=geo_rect_section_union(touching,2,0,300,intervals);
    CHECK("X3_R43_UNION_TOUCHING",n==1&&intervals[0].start==90&&intervals[0].end==120);
    CHECK("X3_R43_EDGE_COVERAGE",geo_interval_edge_coverage(intervals,n,100,0,true)==10);
    CHECK("X3_R43_EDGE_COVERAGE",geo_interval_edge_coverage(intervals,n,100,1000,false)==20);
    unsigned long sections=0,queries=0;
    for(unsigned mask=0;mask<256;++mask)for(int reversed=0;reversed<2;++reversed){
        GeoAxisBox2 rects[8];size_t count=0;
        for(unsigned k=0;k<8;++k){unsigned i=reversed?7-k:k;if(mask&(1u<<i))rects[count++]=catalog[i];}
        for(int axis=0;axis<2;++axis)for(int y2=-7;y2<=7;++y2){
            /* Mark unit cells by midpoint containment. Run lengths provide an
             * independent oracle: no sorting/merging of input intervals. */
            bool cells[8]={false};int other=1-axis;
            for(int x=-4;x<4;++x)for(size_t i=0;i<count;++i)
                if(2*rects[i].lo[axis]<2*x+1&&2*x+1<2*rects[i].hi[axis]&&
                   2*rects[i].lo[other]<y2&&y2<2*rects[i].hi[other])cells[x+4]=true;
            GeoInterval expected[8];size_t expected_count=0;
            for(int x=-4;x<4;){
                if(!cells[x+4]){++x;continue;}
                int start=x;while(x<4&&cells[x+4])++x;
                expected[expected_count++]=(GeoInterval){start,x};
            }
            n=geo_rect_section_union(rects,count,axis,y2,intervals);++sections;
            CHECK("X3_R43_CELL_UNION",n==expected_count);
            for(size_t i=0;i<n;++i)
                CHECK("X3_R43_CELL_UNION",intervals[i].start==expected[i].start&&intervals[i].end==expected[i].end);
            /* Walking adjacent occupied cells cannot jump an uncovered gap.
             * Stops bound the walk independently of the returned intervals. */
            for(int edge=-4;edge<=4;++edge){
                for(int stop=-4;stop<=edge;++stop){
                    GeoCoord width=0;for(int x=edge-1;x>=stop&&cells[x+4];--x)++width;
                    ++queries;CHECK("X3_R43_EDGE_COVERAGE",geo_interval_edge_coverage(intervals,n,edge,stop,true)==width);
                }
                for(int stop=edge;stop<=4;++stop){
                    GeoCoord width=0;for(int x=edge;x<stop&&cells[x+4];++x)++width;
                    ++queries;CHECK("X3_R43_EDGE_COVERAGE",geo_interval_edge_coverage(intervals,n,edge,stop,false)==width);
                }
            }
        }
    }
    printf("X3_R43_ORACLE sections=%lu edge_queries=%lu touching_cases=1\n",sections,queries);
    return 0;
}
