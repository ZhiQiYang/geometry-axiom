/* Independent sequence witnesses for the actual private member-sort function.
 * The Python driver supplies the unchanged product translation unit plus one
 * counted contact_order entry; it does not reimplement the sort. */
#include "contact-monotonic-subject.c"
#include <inttypes.h>
#include <stdlib.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static bool same_face(const WoodStopFace *a,const WoodStopFace *b)
{return a->kind==b->kind&&a->boundary_id==b->boundary_id&&a->timber_id==b->timber_id&&a->hole_index==b->hole_index&&a->edge_index==b->edge_index&&a->fixity==b->fixity&&a->fixed==b->fixed&&a->lo==b->lo&&a->hi==b->hi;}
static int run_case(const char *name)
{
    WoodMember members[64];WoodContactMemberFact facts[64];
    WoodStopFace out[131],original[131];ContactOrderIndex orders;ContactFaceIndex index;
    size_t member_count=8,face_count=8,first=0,expected[128];uint64_t values[64];
    bool work=!strcmp(name,"work");const char *marker="monotonic-ordered-full-fields";
    for(size_t i=0;i<64;++i)values[i]=(uint64_t)(10*(i+1));
    for(size_t i=0;i<128;++i)expected[i]=i;
    if(!strcmp(name,"sorted")){}
    else if(!strcmp(name,"reverse")){for(size_t i=0;i<8;++i){values[i]=(uint64_t)(80-i*10);expected[i]=7-i;}}
    else if(!strcmp(name,"ties")){
        const uint64_t v[8]={30,10,20,10,30,20,10,20};const size_t e[8]={1,3,6,2,5,7,0,4};
        memcpy(values,v,sizeof v);memcpy(expected,e,sizeof e);
    }else if(!strcmp(name,"all-ties")){for(size_t i=0;i<8;++i)values[i]=7;}
    else if(!strcmp(name,"prefix")){
        first=2;member_count=face_count=4;const uint64_t v[4]={40,10,30,20};const size_t e[4]={1,3,2,0};
        memcpy(values,v,sizeof v);memcpy(expected,e,sizeof e);
    }else if(!strcmp(name,"no-member")){first=2;member_count=face_count=0;}
    else if(!strcmp(name,"one-member")){first=2;member_count=face_count=1;}
    else if(!strcmp(name,"last-inversion")){
        values[7]=5;expected[0]=7;for(size_t i=1;i<8;++i)expected[i]=i-1;
        marker="monotonic-last-inversion-full-fields";
    }else if(!strcmp(name,"middle-inversion")){
        member_count=face_count=5;const uint64_t v[5]={10,30,20,40,50};const size_t e[5]={0,2,1,3,4};
        memcpy(values,v,sizeof v);memcpy(expected,e,sizeof e);marker="monotonic-middle-inversion-full-fields";
    }else if(!strcmp(name,"full-uint64")){
        member_count=face_count=4;values[0]=UINT64_MAX;values[1]=UINT64_C(9223372036854775808);values[2]=UINT64_C(4294967296);values[3]=1;
        for(size_t i=0;i<4;++i)expected[i]=3-i;marker="monotonic-full-uint64-fields";
    }else if(work){first=2;member_count=64;face_count=128;}
    else return 2;
    memset(members,0,sizeof members);memset(facts,0,sizeof facts);memset(out,0,sizeof out);
    for(size_t i=0;i<member_count;++i){
        members[i].id=(uint32_t)(i+1);members[i].placed=true;members[i].role=WOOD_MEMBER_ROLE_PRIMARY;
        facts[i]=(WoodContactMemberFact){&members[i],7,values[i],false,true,{0,0,100,27}};
    }
    if(first){
        out[0]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,71,0,-1,11,WOOD_STOP_FREE,444,1,9};
        out[1]=(WoodStopFace){WOOD_STOP_HOLE_EDGE,72,0,3,12,WOOD_STOP_FIXED,-444,2,8};
    }
    for(size_t i=0;i<face_count;++i){
        size_t id=work?i/2:i;
        out[first+i]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,(uint32_t)(1000+i),(uint32_t)(id+1),-1,(int)i,
            i%2?WOOD_STOP_FREE:WOOD_STOP_FIXED,(GeoCoord)(10000+i*100),(GeoCoord)(200+i),(GeoCoord)(227+i)};
    }
    size_t count=first+face_count;memcpy(original,out,sizeof out);memset(&index,0xa5,sizeof index);
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=member_count};
    contact_order_index(&world,&orders);geo_test_sort_order_calls=0;
    contact_member_index_sort(&world,&orders,out,count,first,&index);
    size_t calls=geo_test_sort_order_calls; /* Count only the member-sort interval. */
    for(size_t i=0;i<first;++i)CHECK("monotonic-prefix-fields",same_face(out+i,original+i));
    for(size_t i=0;i<face_count;++i)CHECK(marker,same_face(out+first+i,original+first+expected[i]));
    for(size_t i=count;i<131;++i)CHECK("monotonic-uncollected-tail",same_face(out+i,original+i));
    for(size_t i=first;i<count;++i)CHECK("monotonic-index-identity-retained",index.sorted[i]==i);
    if(face_count<2)CHECK("monotonic-empty-single-no-order-read",calls==0);
    /* The consumer must overwrite all metadata even after the sort returns. */
    contact_face_index_build(&index,out,count);
    for(size_t i=0;i<count;++i){
        CHECK("monotonic-plane-index-completely-rebuilt",index.sorted[i]<count&&index.rank[index.sorted[i]]==i&&index.maximum[i]==0);
        if(i){const WoodStopFace *a=out+index.sorted[i-1],*b=out+index.sorted[i];
            CHECK("monotonic-plane-index-order",a->fixed<b->fixed||(a->fixed==b->fixed&&a->lo<=b->lo));}
    }
    printf("CASE %s faces=%zu first=%zu order_calls=%zu\n",name,face_count,first,calls);
    if(work)CHECK("monotonic-linear-order-lookups",calls==face_count);
    return 0;
}
int main(int argc,char **argv){return argc==2?run_case(argv[1]):2;}
