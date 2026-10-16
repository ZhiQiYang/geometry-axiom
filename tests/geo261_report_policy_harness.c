#include "cut_list.h"
#include "boundary_policy.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)
static WoodMember member(uint32_t id,GeoCoord length,GeoCoord a,GeoCoord b,WoodMemberRole role,bool placed)
{WoodMember value={0};value.id=id;value.length=length;value.size_a=a;value.size_b=b;value.role=role;value.placed=placed;return value;}
static int grouping(void)
{
    WoodMember values[]={member(9,100,20,30,WOOD_MEMBER_ROLE_PRIMARY,true),member(2,100,20,30,WOOD_MEMBER_ROLE_PRIMARY,true),
        member(3,100,20,30,WOOD_MEMBER_ROLE_SECONDARY,true),member(4,100,30,20,WOOD_MEMBER_ROLE_PRIMARY,true),
        member(5,1000,1,1,WOOD_MEMBER_ROLE_BOUNDARY,false),member(6,50,20,30,WOOD_MEMBER_ROLE_PRIMARY,true),
        member(7,100,20,40,WOOD_MEMBER_ROLE_PRIMARY,true)};
    values[0].cut_priority=99;values[1].cut_priority=1;
    WoodMember before[7];memcpy(before,values,sizeof values);WoodCutList result;
    CHECK(wood_cut_list_collect(values,7,&result),"report-collect");
    CHECK(result.placed==6&&result.total_length==550,"report-placed-only");
    CHECK(result.group_count==5,"report-exact-spec-identity");
    CHECK(result.groups[0].count==2&&result.groups[0].ids[0]==9&&result.groups[0].ids[1]==2,"report-id-order");
    CHECK(result.groups[1].role==WOOD_MEMBER_ROLE_SECONDARY,"report-role-order");
    CHECK(result.groups[2].size_b==40&&result.groups[3].size_a==30,"report-section-order");
    CHECK(result.groups[4].length==50,"report-length-order");
    CHECK(!memcmp(before,values,sizeof values),"report-input-unchanged");return 0;
}
static int ordering(void)
{
    WoodMember values[]={member(1,70,40,20,WOOD_MEMBER_ROLE_PRIMARY,true),member(2,90,40,20,WOOD_MEMBER_ROLE_PRIMARY,true),
        member(3,90,30,40,WOOD_MEMBER_ROLE_SECONDARY,true),member(4,90,30,20,WOOD_MEMBER_ROLE_SECONDARY,true),
        member(5,90,30,20,WOOD_MEMBER_ROLE_BOUNDARY,true)};
    WoodCutList result;CHECK(wood_cut_list_collect(values,5,&result),"report-order-collect");
    CHECK(result.groups[4].length==70,"report-length-order");
    const uint32_t ids[]={5,4,3,2,1};for(size_t i=0;i<5;++i)CHECK(result.groups[i].ids[0]==ids[i],"report-tie-break-order");return 0;
}
static int limits(void)
{
    WoodCutList result;memset(&result,0xa5,sizeof result);
    CHECK(wood_cut_list_collect(NULL,0,&result)&&!result.group_count&&!result.placed&&!result.total_length,"report-empty");
    WoodMember values[WOOD_CUT_LIST_MEMBER_CAPACITY];for(size_t i=0;i<WOOD_CUT_LIST_MEMBER_CAPACITY;++i)values[i]=member((uint32_t)i,100,20,30,WOOD_MEMBER_ROLE_PRIMARY,true);
    CHECK(wood_cut_list_collect(values,WOOD_CUT_LIST_MEMBER_CAPACITY,&result)&&result.group_count==1&&result.placed==64&&result.groups[0].count==64&&result.groups[0].ids[63]==63,"report-capacity");
    WoodCutList before;memcpy(&before,&result,sizeof result);
    CHECK(!wood_cut_list_collect(values,WOOD_CUT_LIST_MEMBER_CAPACITY+1,&result)&&!memcmp(&before,&result,sizeof result),"report-over-capacity-atomic");
    CHECK(!wood_cut_list_collect(NULL,1,&result)&&!memcmp(&before,&result,sizeof result),"report-missing-input-atomic");return 0;
}
static int fixity(void)
{
    WoodEdgeFixity values[GEO_LOOP_MAX_VERTICES];for(size_t i=0;i<GEO_LOOP_MAX_VERTICES;++i)values[i]=WOOD_EDGE_FREE;
    wood_boundary_default_fixity(values,4);
    for(size_t i=0;i<4;++i)CHECK(values[i]==WOOD_EDGE_FIXED,"fixity-default-fixed");
    for(size_t i=4;i<GEO_LOOP_MAX_VERTICES;++i)CHECK(values[i]==WOOD_EDGE_FREE,"fixity-requested-prefix-only");
    wood_boundary_default_fixity(values,GEO_LOOP_MAX_VERTICES);
    for(size_t i=0;i<GEO_LOOP_MAX_VERTICES;++i)CHECK(values[i]==WOOD_EDGE_FIXED,"fixity-full-capacity");
    wood_boundary_default_fixity(NULL,0);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"grouping"))return grouping();if(!strcmp(argv[1],"ordering"))return ordering();
    if(!strcmp(argv[1],"limits"))return limits();if(!strcmp(argv[1],"fixity"))return fixity();return 2;
}
