/* GEO-300 capacity witnesses. Constants below are independent of W macros. */
#include "document.h"
#include "cut_list.h"
#include "contact_world.h"
#include "member_reference.h"
#include "member_declaration.h"
#include "world_validation.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)

static int values(void)
{
    CHECK(WOOD_MEMBER_CAPACITY==512,"capacity-value-512");
    CHECK(WOOD_CONTACT_MEMBER_CAPACITY==512,"capacity-contact-512");
    CHECK(WOOD_CUT_LIST_MEMBER_CAPACITY==512,"capacity-report-512");
    CHECK(WOOD_MEMBER_SPAN_MEMBER_CAPACITY==512,"capacity-span-members-512");
    CHECK(sizeof(((WoodDocument *)0)->timbers)/sizeof(WoodMember)==512,"capacity-storage-timbers");
    CHECK(sizeof(((WoodDocument *)0)->anchors)/sizeof(WoodMemberPlacement)==512,"capacity-storage-anchors");
    CHECK(WOOD_CONTACT_FACE_CAPACITY==3328,"capacity-face-3328");
    CHECK(WOOD_MEMBER_SPAN_CUT_CAPACITY==3328,"capacity-span-3328");
    CHECK(WOOD_CONTACT_COMPONENT_CAPACITY==8&&WOOD_DOCUMENT_BOUNDARY_CAPACITY==16&&
        WOOD_DOCUMENT_PLACEMENT_CAPACITY==16&&WOOD_OBSTACLE_CAPACITY==32,"capacity-other-resources-unchanged");
    return 0;
}

#ifndef CAPACITY_VALUES_ONLY
static WoodMember member(uint32_t id,GeoCoord length)
{
    WoodMember result={0};result.id=id;result.length=length;result.size_a=20;result.size_b=30;
    result.role=WOOD_MEMBER_ROLE_PRIMARY;result.placed=true;return result;
}
static int report_boundary(void)
{
    CHECK(!values(),"capacity-report-prerequisite");
    WoodMember members[513];uint32_t ids[513];
    for(size_t i=0;i<513;++i){ids[i]=(uint32_t)(1000+(i*73)%513);members[i]=member(ids[i],100);}
    WoodCutList result;
    CHECK(wood_cut_list_collect(members,512,&result),"capacity-report-512-admitted");
    CHECK(result.placed==512&&result.group_count==1&&result.groups[0].count==512&&
        result.groups[0].first==0&&result.total_length==51200,"capacity-report-512-values");
    for(size_t i=0;i<512;++i)CHECK(result.ids[i]==ids[i],"capacity-report-full-declaration-order");
    WoodCutList before;memcpy(&before,&result,sizeof before);
    CHECK(!wood_cut_list_collect(members,513,&result)&&!memcmp(&before,&result,sizeof result),"capacity-report-513-atomic");
    for(size_t i=0;i<512;++i)members[i].length=(GeoCoord)(i+1);
    CHECK(wood_cut_list_collect(members,512,&result)&&result.group_count==512&&result.total_length==131328,"capacity-report-512-distinct");
    WoodCutList copy=result;memset(members,0,sizeof members);memset(&result,0,sizeof result);
    for(size_t i=0;i<512;++i)CHECK(copy.groups[i].first==i&&copy.groups[i].count==1&&
        copy.groups[i].length==(GeoCoord)(512-i)&&copy.ids[i]==ids[511-i],"capacity-report-value-copy-full-slices");
    return 0;
}
static int contact_boundary(void)
{
    CHECK(!values(),"capacity-contact-prerequisite");
    WoodMember members[513];WoodContactMemberFact facts[513];WoodStopFace out[3329];
    for(size_t i=0;i<513;++i){members[i]=member((uint32_t)(1000+i),100);
        facts[i]=(WoodContactMemberFact){.member=&members[i],.placement_id=7,
            .order=UINT64_MAX-i/2,.along_v=false,.footprint_valid=true,
            .footprint={(GeoCoord)(i*10),20,(GeoCoord)(i*10+2),30}};}
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=512};
    memset(out,0x5a,sizeof out);WoodStopFace sentinel=out[1024];
    size_t count=wood_contact_collect_stops(&world,false,NULL,out,3328);
    CHECK(count==1024&&!memcmp(&out[1024],&sentinel,sizeof sentinel),"capacity-contact-512-full-pairs");
    for(size_t i=0;i<512;++i){size_t original=510-2*(i/2)+(i%2);
        CHECK(out[2*i].kind==WOOD_STOP_MEMBER_SIDE&&out[2*i+1].kind==WOOD_STOP_MEMBER_SIDE&&
            out[2*i].timber_id==1000+original&&out[2*i+1].timber_id==1000+original&&
            out[2*i].edge_index==0&&out[2*i+1].edge_index==1&&
            out[2*i].fixed==(GeoCoord)(original*10)&&out[2*i+1].fixed==(GeoCoord)(original*10+2)&&
            out[2*i].lo==20&&out[2*i].hi==30&&out[2*i+1].lo==20&&out[2*i+1].hi==30,
            "capacity-contact-512-stable-uint64-order-and-values");}
    memset(out,0x5a,sizeof out);sentinel=out[1022];
    CHECK(wood_contact_collect_stops(&world,false,NULL,out,1023)==1022&&
        !memcmp(&out[1022],&sentinel,sizeof sentinel),"capacity-contact-partial-buffer-pair-atomic");
    /* Public borrowed facts above capacity retain the original safe fallback.
     * This is not the fixed-storage world validation API below. */
    for(size_t i=0;i<513;++i)facts[i].order=UINT64_MAX-i;
    world.member_count=513;memset(out,0x5a,sizeof out);sentinel=out[1026];
    CHECK(wood_contact_collect_stops(&world,false,NULL,out,3328)==1026&&
        !memcmp(&out[1026],&sentinel,sizeof sentinel),"capacity-contact-513-public-fallback");
    for(size_t i=0;i<513;++i)CHECK(out[2*i].timber_id==1512-i&&out[2*i+1].timber_id==1512-i,
        "capacity-contact-513-fallback-order");
    return 0;
}
typedef struct {WoodMember members[513];unsigned visits[513];size_t calls;bool stop_first,bad_order;} ValidationFixture;
static bool member_at(void *user,size_t i,WoodWorldMemberFact *out)
{
    ValidationFixture *fixture=user;
    if(i>=513)return false;
    if(i!=fixture->calls%512)fixture->bad_order=true;
    ++fixture->calls;++fixture->visits[i];
    if(fixture->stop_first)return false;
    *out=(WoodWorldMemberFact){.member=&fixture->members[i],.placement_id=7,.length_direction=GEO_DIRECTION_POS_U};return true;
}
static int validation_boundary(void)
{
    CHECK(!values(),"capacity-validation-prerequisite");
    ValidationFixture fixture={0};WoodGridState grids={0};WoodWorldValidationContext context={0};
    for(size_t i=0;i<513;++i)fixture.members[i].id=(uint32_t)(i+1);
    WoodMember before[513];memcpy(before,fixture.members,sizeof before);
    context.grids.state=&grids;context.user=&fixture;context.member_count=512;context.member_at=member_at;
    char error[256]="sentinel";
    CHECK(wood_world_validate_members(&context,error,sizeof error)&&!strcmp(error,"sentinel"),"capacity-validation-512-admitted");
    CHECK(fixture.calls==1536&&!fixture.bad_order,"capacity-validation-three-ordered-passes");
    for(size_t i=0;i<512;++i)CHECK(fixture.visits[i]==3,"capacity-validation-every-member-visited");
    CHECK(!memcmp(before,fixture.members,sizeof before),"capacity-validation-512-input-unchanged");
    fixture.calls=0;fixture.stop_first=true;context.member_count=513;
    CHECK(!wood_world_validate_members(&context,error,sizeof error),"capacity-validation-513-rejected");
    CHECK(fixture.calls==0&&!strcmp(error,"I33 CAPACITY: member count exceeds the contact capacity")&&
        !memcmp(before,fixture.members,sizeof before),"capacity-validation-513-before-callback");
    return 0;
}
static bool replace_member(void *user,WoodMember *target,const WoodMember *value)
{(void)user;*target=*value;return true;}
static int declaration_admission(void)
{
    CHECK(!values(),"capacity-declaration-prerequisite");
    WoodMember members[512];for(size_t i=0;i<512;++i)members[i]=member((uint32_t)(i+1),100);
    size_t count=512;WoodMemberDeclarationContext context={.members=members,.count=&count,.capacity=512,.replace=replace_member};
    const char *error="sentinel";WoodMember before[512];memcpy(before,members,sizeof before);
    /* No call to wood_member_declare on the withdrawn guard: the real API
     * has no second append bound. A normal admission ASSERT is sufficient. */
    CHECK(!wood_member_declaration_capacity(&context,true,513,&error)&&
        !strcmp(error,"角材的數量超過上限"),"capacity-declaration-513-refused");
    CHECK(count==512&&!memcmp(before,members,sizeof before),"capacity-declaration-refusal-atomic");
    error="sentinel";
    CHECK(wood_member_declaration_capacity(&context,true,512,&error)&&!strcmp(error,"sentinel"),"capacity-declaration-existing-full-admitted");
    CHECK(wood_member_declare(&context,512,22,33,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&count==512&&
        members[511].size_a==22&&members[511].size_b==33,"capacity-declaration-existing-full-replaced");
    return 0;
}
#endif
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"values"))return values();
#ifndef CAPACITY_VALUES_ONLY
    if(!strcmp(argv[1],"report"))return report_boundary();
    if(!strcmp(argv[1],"contact"))return contact_boundary();
    if(!strcmp(argv[1],"validation"))return validation_boundary();
    if(!strcmp(argv[1],"admission"))return declaration_admission();
#endif
    return 2;
}
