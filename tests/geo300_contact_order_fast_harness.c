/* Actual W collector versus the original linear placement-order/live-set
 * policy. Serialize public fields individually: struct padding is not output. */
#include "contact_world.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern void geo300_sort_work_reset(void);
extern uint64_t geo300_sort_comparisons(void);
#define REQUIRE(name,condition) do {if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}} while(0)

static GeoCoord minimum(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord maximum(GeoCoord a,GeoCoord b){return a>b?a:b;}
static uint64_t original_order(const WoodContactWorld *world,uint32_t id)
{
    uint64_t order=UINT64_MAX;
    for(size_t i=0;i<world->member_count;++i)
        if(world->members[i].member->id==id)order=world->members[i].order;
    return order;
}
static bool original_earlier(const WoodContactWorld *world,uint32_t id,uint64_t order)
{
    for(size_t i=0;i<world->member_count;++i)
        if(world->members[i].member->id==id&&world->members[i].order<order)return true;
    return false;
}
static size_t original_collect(const WoodContactWorld *world,bool along_v,
    const WoodMember *exclude,WoodStopFace *out,size_t cap)
{
    size_t count=0;
    for(size_t component=0;component<world->region_count;++component){
        const WoodBoundaryRegion *boundary=world->regions[component];if(!boundary)continue;
        const WoodBoundaryLoop *loops[1+GEO_REGION_MAX_HOLES];
        int hole_of[1+GEO_REGION_MAX_HOLES];size_t loop_count=0;
        loops[loop_count]=&boundary->outline;hole_of[loop_count++]=-1;
        for(size_t h=0;h<boundary->hole_count;++h){loops[loop_count]=&boundary->holes[h];hole_of[loop_count++]=(int)h;}
        for(size_t li=0;li<loop_count;++li){const WoodBoundaryLoop *loop=loops[li];
            for(size_t i=0;i<loop->count&&count<cap;++i){GeoPoint2 a=loop->v[i],b=loop->v[(i+1)%loop->count];
                if(along_v&&a.v!=b.v)continue;if(!along_v&&a.u!=b.u)continue;
                out[count++]=(WoodStopFace){hole_of[li]<0?WOOD_STOP_OUTLINE_EDGE:WOOD_STOP_HOLE_EDGE,boundary->id,0,
                    hole_of[li]<0?-1:(int)(component*GEO_REGION_MAX_HOLES)+hole_of[li],
                    hole_of[li]<0?(int)(component*GEO_LOOP_MAX_VERTICES+i):(int)i,loop->fixity[i],
                    along_v?a.v:a.u,along_v?minimum(a.u,b.u):minimum(a.v,b.v),
                    along_v?maximum(a.u,b.u):maximum(a.v,b.v)};
            }
        }
    }
    for(size_t i=0;i<world->member_count&&count+2<=cap;++i){
        const WoodContactMemberFact *fact=&world->members[i];const WoodMember *member=fact->member;
        if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;
        const GeoRect2 *f=&fact->footprint;
        if(along_v){
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_v,f->min_u,f->max_u};
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_v,f->min_u,f->max_u};
        }else{
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_u,f->min_v,f->max_v};
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_u,f->min_v,f->max_v};
        }
    }
    for(size_t i=1;i<count;++i){
        if(out[i].kind!=WOOD_STOP_MEMBER_SIDE)continue;
        uint64_t order=original_order(world,out[i].timber_id);size_t j=i;WoodStopFace value=out[i];
        while(j&&out[j-1].kind==WOOD_STOP_MEMBER_SIDE){
            if(original_order(world,out[j-1].timber_id)<=order)break;
            out[j]=out[j-1];--j;
        }
        out[j]=value;
    }
    /* Intentionally retain the old immediate deletion, without an index or
     * interval union; removed faces cannot witness any later deletion. */
    for(size_t i=0;i<count;){bool covered=false;
        if(out[i].kind==WOOD_STOP_MEMBER_SIDE){uint64_t order=original_order(world,out[i].timber_id);
            for(size_t j=0;j<count&&!covered;++j){
                if(i==j||out[i].fixed!=out[j].fixed||out[i].lo>=out[j].hi||out[j].lo>=out[i].hi)continue;
                bool earlier=out[j].kind!=WOOD_STOP_MEMBER_SIDE||original_earlier(world,out[j].timber_id,order);
                if(earlier&&out[j].lo<=out[i].lo&&out[j].hi>=out[i].hi)covered=true;
            }
        }
        if(covered){memmove(out+i,out+i+1,(count-i-1)*sizeof *out);--count;}else ++i;
    }
    return count;
}

static size_t public_bytes(const WoodStopFace *face,unsigned char *out)
{
    size_t at=0;
#define FIELD(name) do {memcpy(out+at,&face->name,sizeof face->name);at+=sizeof face->name;} while(0)
    FIELD(kind);FIELD(boundary_id);FIELD(timber_id);FIELD(hole_index);
    FIELD(edge_index);FIELD(fixity);FIELD(fixed);FIELD(lo);FIELD(hi);
#undef FIELD
    return at;
}
static void facts_init(WoodMember *members,WoodContactMemberFact *facts,size_t count)
{
    for(size_t i=0;i<count;++i){
        members[i]=(WoodMember){0};members[i].id=(uint32_t)(i+1);
        members[i].role=WOOD_MEMBER_ROLE_PRIMARY;members[i].cut_priority=2;members[i].placed=true;
        facts[i]=(WoodContactMemberFact){&members[i],7,(uint64_t)i+1,false,true,
            {1000+(GeoCoord)i*100,2000+(GeoCoord)i*100,1010+(GeoCoord)i*100,2020+(GeoCoord)i*100}};
    }
}
static void loop_init(WoodBoundaryLoop *loop,GeoCoord u,GeoCoord v,GeoCoord side)
{
    loop->count=4;
    GeoPoint2 points[4]={{u,v},{u+side,v},{u+side,v+side},{u,v+side}};
    memcpy(loop->v,points,sizeof points);
    for(size_t i=0;i<4;++i)loop->fixity[i]=i==1?WOOD_STOP_FREE:WOOD_STOP_FIXED;
}
/* work: zero = no bound, one = no member-sort comparisons, two = fallback used. */
static int verify(const char *label,const char *assertion,const WoodContactWorld *world,
    const WoodMember *exclude,size_t cap,int work)
{
    WoodStopFace actual[WOOD_CONTACT_FACE_CAPACITY],expected[WOOD_CONTACT_FACE_CAPACITY];
    for(int axis=0;axis<2;++axis){
        geo300_sort_work_reset();
        size_t got=wood_contact_collect_stops(world,axis!=0,exclude,cap?actual:NULL,cap);
        uint64_t comparisons=geo300_sort_comparisons();
        size_t want=original_collect(world,axis!=0,exclude,cap?expected:NULL,cap);
        REQUIRE(assertion,got==want);
        for(size_t i=0;i<got;++i){
            unsigned char a[sizeof(WoodStopFace)],b[sizeof(WoodStopFace)];
            size_t an=public_bytes(&actual[i],a),bn=public_bytes(&expected[i],b);
            if(an!=bn||memcmp(a,b,an)){
                fprintf(stderr,"case=%s axis=%d face=%zu actual_id=%u expected_id=%u\n",label,axis,i,
                    (unsigned)actual[i].timber_id,(unsigned)expected[i].timber_id);
                REQUIRE(assertion,false);
            }
        }
        printf("case=%s axis=%d public_faces=%zu field_bytes=equal member_comparisons=%" PRIu64 "\n",
            label,axis,got,comparisons);
        if(work==1)REQUIRE("contact-order-sorted-no-merge",comparisons==0);
        if(work==2)REQUIRE("contact-order-unsorted-retains-merge",comparisons>0);
    }
    return 0;
}

static int sorted_cases(bool equal)
{
    WoodMember members[64];WoodContactMemberFact facts[64];facts_init(members,facts,64);
    for(size_t i=0;i<64;++i)facts[i].order=equal?UINT64_MAX:UINT64_MAX-63+i;
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=64};
    return verify(equal?"equal-uint64":"ascending-uint64","contact-order-sorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1);
}
static int unsorted_cases(void)
{
    WoodMember members[5];WoodContactMemberFact facts[5];facts_init(members,facts,5);
    const uint64_t orders[5]={UINT64_MAX,UINT64_C(9223372036854775808),UINT64_C(4294967296),1,0};
    for(size_t i=0;i<5;++i)facts[i].order=orders[i];
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=5};
    if(verify("reverse-uint64","contact-order-unsorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,2))return 1;
    world.member_count=2;facts[0].order=UINT64_C(4294967296);facts[1].order=1;
    if(verify("low-word-wrap-inversion","contact-order-unsorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,2))return 1;
    facts[0].order=UINT64_C(9223372036854775808);
    if(verify("signed-wrap-inversion","contact-order-unsorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,2))return 1;
    world.member_count=5;
    facts_init(members,facts,5);facts[3].order=3;
    if(verify("equal-adjacent","contact-order-sorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1))return 1;
    facts[4].order=2;
    return verify("last-inversion","contact-order-unsorted-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,2);
}
static int edge_cases(void)
{
    WoodMember members[8];WoodContactMemberFact facts[8];facts_init(members,facts,8);
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=8};
    WoodBoundaryRegion boundary[2]={{0}};
    for(size_t i=0;i<2;++i){boundary[i].id=(uint32_t)i+40;
        loop_init(&boundary[i].outline,(GeoCoord)i*300,(GeoCoord)i*300,100);
        boundary[i].hole_count=1;loop_init(&boundary[i].holes[0],20+(GeoCoord)i*300,20+(GeoCoord)i*300,40);
        world.regions[i]=&boundary[i];
    }
    world.region_count=2;
    if(verify("rc-prefix-holes","contact-order-boundary-prefix-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1))return 1;
    for(size_t cap=0;cap<15;++cap)
        if(verify("capacity-before-sort","contact-order-capacity-byte-oracle",&world,NULL,cap,0))return 1;
    world.region_count=0;members[1].placed=false;facts[2].placement_id=99;facts[3].footprint_valid=false;
    if(verify("filtered-and-excluded","contact-order-filtered-byte-oracle",&world,&members[4],WOOD_CONTACT_FACE_CAPACITY,1))return 1;
    members[7].placed=false;facts[7].order=0;
    if(verify("filtered-zero-conservative-miss","contact-order-filtered-byte-oracle",&world,&members[4],WOOD_CONTACT_FACE_CAPACITY,2))return 1;
    facts_init(members,facts,8);members[0].id=members[6].id;
    if(verify("duplicate-id-last-order","contact-order-duplicate-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,0))return 1;
    facts_init(members,facts,8);world.member_count=5;
    /* Single-witness, exact overlap, enclosed zero/reversed spans and equal
     * order all retain the original policy; the fast path does not decide it. */
    facts[0].footprint=(GeoRect2){0,0,10,5};facts[0].order=1;
    facts[1].footprint=(GeoRect2){0,5,10,10};facts[1].order=1;
    facts[2].footprint=(GeoRect2){0,0,10,10};facts[2].order=2;
    facts[3].footprint=(GeoRect2){0,5,10,5};facts[3].order=3;
    facts[4].footprint=(GeoRect2){0,8,10,3};facts[4].order=4;
    if(verify("single-witness-degenerate","contact-order-degenerate-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1))return 1;
    world.member_count=0;
    return verify("empty","contact-order-empty-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1);
}
static int full_capacity(void)
{
    static WoodMember members[WOOD_CONTACT_MEMBER_CAPACITY];
    static WoodContactMemberFact facts[WOOD_CONTACT_MEMBER_CAPACITY];
    facts_init(members,facts,WOOD_CONTACT_MEMBER_CAPACITY);
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=WOOD_CONTACT_MEMBER_CAPACITY};
    return verify("full-member-capacity","contact-order-capacity-byte-oracle",&world,NULL,WOOD_CONTACT_FACE_CAPACITY,1);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"sorted"))return sorted_cases(false);
    if(!strcmp(argv[1],"ties"))return sorted_cases(true);
    if(!strcmp(argv[1],"unsorted"))return unsorted_cases();
    if(!strcmp(argv[1],"edges"))return edge_cases();
    if(!strcmp(argv[1],"capacity"))return full_capacity();
    return 2;
}
