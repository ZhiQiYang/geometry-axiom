/* Declaration policy witnesses use the real W constructor and caller-owned
 * candidate records. No host parser or duplicate declaration algorithm. */
#include "member_declaration.h"
#include <stdio.h>
#include <string.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static const char untouched[]="previous diagnostic";
static const char capacity_error[]="角材的數量超過上限";
static const char role_error[]="role 只能是 boundary、primary、secondary 或 custom";
static const char priority_error[]="custom 角色需要 priority N（N 是 ≥1 的整數）";
static const char dimension_error[]="角材的長度與 A/B 尺寸都要大於 0";
typedef struct {
    WoodMember members[66];size_t count;
    bool is_owned,allow_replace,write_replace;
    int owned_calls,replace_calls;uint32_t owned_id;
    WoodMember *expected;bool exact_target,separate_source;WoodMember proposed;
    WoodMemberDeclarationContext context;
} Fixture;
static bool owned(void *user,uint32_t id)
{Fixture *f=user;++f->owned_calls;f->owned_id=id;return f->is_owned;}
static bool replace(void *user,WoodMember *target,const WoodMember *source)
{Fixture *f=user;++f->replace_calls;f->exact_target=target==f->expected;f->separate_source=target!=source;f->proposed=*source;if(f->allow_replace&&f->write_replace)*target=*source;return f->allow_replace;}
static void init(Fixture *f,size_t capacity)
{memset(f,0,sizeof *f);f->allow_replace=f->write_replace=true;f->context=(WoodMemberDeclarationContext){f->members,&f->count,capacity,f,owned,replace};}
static bool make(WoodMember *m,uint32_t id)
{return wood_member_construct(id,0,27,33,true,WOOD_MEMBER_ROLE_PRIMARY,0,m);}

static int capacity(void)
{
    Fixture f;init(&f,64);const char *error=untouched;WoodMember snapshot[66];
    CHECK("under-capacity-no-id-needed",wood_member_declaration_capacity(&f.context,false,0,&error)&&error==untouched);
    for(size_t i=0;i<64;++i)CHECK("capacity-seed",make(&f.members[i],(uint32_t)(100+i)));f.count=64;memcpy(snapshot,f.members,sizeof snapshot);
    CHECK("capacity-first-missing-id",!wood_member_declaration_capacity(&f.context,false,100,&error)&&!strcmp(error,capacity_error));
    error=untouched;CHECK("capacity-first-new-id",!wood_member_declaration_capacity(&f.context,true,99,&error)&&!strcmp(error,capacity_error));
    error=untouched;CHECK("capacity-existing-update-allowed",wood_member_declaration_capacity(&f.context,true,100,&error)&&wood_member_declaration_capacity(&f.context,true,163,&error)&&error==untouched);
    CHECK("capacity-read-only-no-callbacks",f.count==64&&!memcmp(snapshot,f.members,sizeof snapshot)&&f.owned_calls==0&&f.replace_calls==0);
    f.expected=&f.members[63];CHECK("existing-declaration-at-full-capacity",wood_member_declare(&f.context,163,40,50,WOOD_MEMBER_ROLE_SECONDARY,0,&error)&&f.count==64&&f.replace_calls==1&&f.exact_target&&f.members[63].size_a==40&&f.members[63].size_b==50);
    f.context.capacity=0;f.count=0;CHECK("zero-capacity-refuses-new",!wood_member_declaration_capacity(&f.context,false,0,NULL));return 0;
}
static int roles(void)
{
    const char *names[]={"boundary","primary","secondary","custom"};
    for(int i=0;i<4;++i){char input[32]={0};strcpy(input,names[i]);char before[32];memcpy(before,input,sizeof input);WoodMemberRole role=(WoodMemberRole)99;const char *error=untouched;
        CHECK("four-exact-role-identities",wood_member_declaration_role(input,&role,&error)&&role==(WoodMemberRole)i);
        CHECK("role-input-and-diagnostic-unchanged",!memcmp(input,before,sizeof input)&&error==untouched);}
    const char *bad[]={"Boundary","PRIMARY","custom ","","0","secondaryx"};
    for(size_t i=0;i<sizeof bad/sizeof bad[0];++i){WoodMemberRole role=WOOD_MEMBER_ROLE_SECONDARY;const char *error=untouched;CHECK("unknown-role-preserves-output",!wood_member_declaration_role(bad[i],&role,&error)&&role==WOOD_MEMBER_ROLE_SECONDARY&&!strcmp(error,role_error));}
    const char *error=untouched;
    CHECK("custom-priority-must-be-supplied",!wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,false,true,1,&error)&&!strcmp(error,priority_error));
    error=untouched;CHECK("custom-priority-must-parse",!wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,true,false,1,&error)&&!strcmp(error,priority_error));
    error=untouched;CHECK("custom-zero-priority-refused",!wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,true,true,0,&error)&&!strcmp(error,priority_error));
    CHECK("custom-negative-priority-refused",!wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,true,true,-1,NULL));
    error=untouched;CHECK("custom-positive-wide-priority-accepted",wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,true,true,1,&error)&&wood_member_declaration_priority(WOOD_MEMBER_ROLE_CUSTOM,true,true,INT64_MAX,&error)&&error==untouched);
    for(int i=0;i<3;++i){error=untouched;CHECK("fixed-role-priority-forbidden",!wood_member_declaration_priority((WoodMemberRole)i,true,true,3,&error)&&!strcmp(error,"priority 只能配 custom 角色"));error=untouched;
        CHECK("fixed-role-no-priority-input-accepted",wood_member_declaration_priority((WoodMemberRole)i,false,false,-99,&error)&&error==untouched);}
    return 0;
}
static int ownership(void)
{
    Fixture f;init(&f,2);CHECK("owned-seed",make(&f.members[0],17));f.count=1;f.expected=&f.members[0];f.is_owned=true;WoodMember snapshot[66];memcpy(snapshot,f.members,sizeof snapshot);const char *error=untouched;
    CHECK("assembly-owner-before-invalid-dimensions",!wood_member_declare(&f.context,17,0,-3,WOOD_MEMBER_ROLE_CUSTOM,0,&error)&&!strcmp(error,"I42: edit the owning assembly instance")&&f.owned_calls==1&&f.owned_id==17&&f.replace_calls==0);
    CHECK("owned-existing-candidate-unchanged",f.count==1&&!memcmp(snapshot,f.members,sizeof snapshot));
    error=untouched;CHECK("assembly-owner-before-new-record",!wood_member_declare(&f.context,UINT32_MAX,27,33,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&!strcmp(error,"I42: edit the owning assembly instance")&&f.owned_id==UINT32_MAX&&f.count==1&&!memcmp(snapshot,f.members,sizeof snapshot));
    CHECK("assembly-error-pointer-optional",!wood_member_declare(&f.context,17,27,33,WOOD_MEMBER_ROLE_PRIMARY,0,NULL));
    f.context.owned=NULL;error=untouched;CHECK("optional-owner-service",wood_member_declare(&f.context,18,27,33,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&f.count==2&&error==untouched&&f.replace_calls==0);return 0;
}
static int updates(void)
{
    Fixture f;init(&f,2);CHECK("update-seed",make(&f.members[0],17));f.count=1;f.expected=&f.members[0];f.members[0].placed=true;f.members[0].length=800;f.members[0].origin=(GeoPoint3){10,20,30};f.members[0].axis_length=(GeoVector3){0,1,0};
    const char *error=untouched;CHECK("update-calls-host-replacement",wood_member_declare(&f.context,17,40,60,WOOD_MEMBER_ROLE_CUSTOM,9,&error)&&f.replace_calls==1&&f.owned_calls==1&&f.exact_target&&f.separate_source&&f.count==1);
    CHECK("update-retains-placed-state",f.proposed.placed&&f.members[0].placed);
    CHECK("update-rebuilds-declaration-fields",f.proposed.id==17&&f.proposed.length==0&&f.proposed.auto_length&&f.proposed.size_a==40&&f.proposed.size_b==60&&f.proposed.role==WOOD_MEMBER_ROLE_CUSTOM&&f.proposed.cut_priority==9&&f.proposed.origin.x==0&&f.proposed.origin.y==0&&f.proposed.origin.z==0&&f.proposed.axis_length.x==1&&f.proposed.axis_a.y==1&&f.proposed.axis_b.z==1&&error==untouched);
    f.members[0].placed=false;CHECK("unplaced-redeclare-stays-unplaced",wood_member_declare(&f.context,17,41,61,WOOD_MEMBER_ROLE_SECONDARY,0,&error)&&!f.proposed.placed&&!f.members[0].placed&&f.members[0].cut_priority==3);
    WoodMember snapshot[66];memcpy(snapshot,f.members,sizeof snapshot);f.allow_replace=false;int calls=f.replace_calls;
    CHECK("replacement-failure-propagates",!wood_member_declare(&f.context,17,90,91,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&f.replace_calls==calls+1&&f.count==1&&!memcmp(snapshot,f.members,sizeof snapshot)&&error==untouched);
    f.allow_replace=true;f.write_replace=false;calls=f.replace_calls;CHECK("host-controls-final-write",wood_member_declare(&f.context,17,99,100,WOOD_MEMBER_ROLE_BOUNDARY,0,&error)&&f.replace_calls==calls+1&&!memcmp(snapshot,f.members,sizeof snapshot));
    calls=f.replace_calls;error=untouched;CHECK("existing-invalid-keeps-old-diagnostic",!wood_member_declare(&f.context,17,0,33,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&error==untouched&&f.replace_calls==calls&&f.count==1&&!memcmp(snapshot,f.members,sizeof snapshot));
    error=NULL;CHECK("existing-invalid-does-not-invent-diagnostic",!wood_member_declare(&f.context,17,27,-1,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&error==NULL);return 0;
}
static int append(void)
{
    Fixture f;init(&f,8);const char *error=untouched;WoodMember snapshot[66];memcpy(snapshot,f.members,sizeof snapshot);
    CHECK("new-invalid-dimension-diagnostic",!wood_member_declare(&f.context,17,0,33,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&!strcmp(error,dimension_error)&&f.count==0&&!memcmp(snapshot,f.members,sizeof snapshot));
    error=untouched;CHECK("new-invalid-b-diagnostic",!wood_member_declare(&f.context,17,27,-1,WOOD_MEMBER_ROLE_PRIMARY,0,&error)&&!strcmp(error,dimension_error)&&f.count==0);
    error=untouched;CHECK("constructor-still-refuses-custom-zero",!wood_member_declare(&f.context,17,27,33,WOOD_MEMBER_ROLE_CUSTOM,0,&error)&&!strcmp(error,dimension_error)&&f.count==0);
    for(int i=0;i<4;++i){error=untouched;CHECK("append-one-record-per-success",wood_member_declare(&f.context,(uint32_t)(100+i),27+i,33+i,(WoodMemberRole)i,7,&error)&&f.count==(size_t)i+1&&error==untouched);
        WoodMember *m=&f.members[i];CHECK("new-role-priority-and-canonical-pose",m->id==(uint32_t)(100+i)&&m->size_a==27+i&&m->size_b==33+i&&m->role==(WoodMemberRole)i&&m->cut_priority==(i==3?7:i+1)&&m->auto_length&&!m->placed&&m->length==0&&m->origin.x==0&&m->axis_length.x==1&&m->axis_a.y==1&&m->axis_b.z==1);}
    CHECK("append-never-calls-replacement",f.replace_calls==0&&f.owned_calls==7&&!memcmp(&f.members[4],&snapshot[4],sizeof f.members-sizeof f.members[0]*4));
    f.context.owned=NULL;f.context.replace=NULL;CHECK("new-record-needs-no-replacement-service",wood_member_declare(&f.context,UINT32_MAX,1,1,WOOD_MEMBER_ROLE_CUSTOM,INT64_MAX,NULL)&&f.count==5&&f.members[4].id==UINT32_MAX&&f.members[4].cut_priority==INT64_MAX);return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"capacity"))return capacity();if(!strcmp(argv[1],"roles"))return roles();if(!strcmp(argv[1],"ownership"))return ownership();if(!strcmp(argv[1],"updates"))return updates();if(!strcmp(argv[1],"append"))return append();return 2;}
