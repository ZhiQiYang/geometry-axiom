#include "members.h"
#include <stdio.h>
#include <string.h>

/* The pre-extraction product ABI. This is a compatibility witness, not a
 * second implementation or a value oracle for the member operations. */
typedef enum { OLD_BOUNDARY=0, OLD_PRIMARY, OLD_SECONDARY, OLD_CUSTOM } OldRole;
typedef struct {
    uint32_t id;
    int64_t length, size_a, size_b;
    OldRole role;
    int64_t cut_priority;
    bool auto_length, placed;
    GeoPoint3 origin;
    GeoVector3 axis_length, axis_a, axis_b;
} OldMemberLayout;

static bool point_equal(GeoPoint3 a,GeoPoint3 b)
{
    return a.x==b.x&&a.y==b.y&&a.z==b.z;
}

static int layout(void)
{
    if(sizeof(WoodMember)!=sizeof(OldMemberLayout))return 1;
#define FIELD(member) if(offsetof(WoodMember,member)!=offsetof(OldMemberLayout,member))return 1
    FIELD(id);FIELD(length);FIELD(size_a);FIELD(size_b);FIELD(role);
    FIELD(cut_priority);FIELD(auto_length);FIELD(placed);FIELD(origin);
    FIELD(axis_length);FIELD(axis_a);FIELD(axis_b);
#undef FIELD
    if(WOOD_MEMBER_ROLE_BOUNDARY!=0||WOOD_MEMBER_ROLE_PRIMARY!=1||
       WOOD_MEMBER_ROLE_SECONDARY!=2||WOOD_MEMBER_ROLE_CUSTOM!=3)return 1;
    if(WOOD_MEMBER_FACE_A0!=0||WOOD_MEMBER_FACE_A1!=1||WOOD_MEMBER_FACE_B0!=2||
       WOOD_MEMBER_FACE_B1!=3||WOOD_MEMBER_FACE_START!=4||WOOD_MEMBER_FACE_END!=5||
       WOOD_MEMBER_FACE_COUNT!=6)return 1;
    return 0;
}

static int construction(void)
{
    WoodMember value;
    const char *names[]={"boundary","primary","secondary","custom"};
    for(int role=0;role<4;++role){
        if(!wood_member_construct(UINT32_MAX,0,37,53,true,(WoodMemberRole)role,17,&value))return 1;
        if(value.id!=UINT32_MAX||value.length!=0||value.size_a!=37||value.size_b!=53||
           !value.auto_length||value.placed||(int)value.role!=role||
           value.cut_priority!=(role==3?17:role+1)||strcmp(wood_member_role_name(value.role),names[role]))return 1;
        if(!point_equal(value.origin,(GeoPoint3){0,0,0})||
           !point_equal((GeoPoint3){value.axis_length.x,value.axis_length.y,value.axis_length.z},(GeoPoint3){1,0,0})||
           !point_equal((GeoPoint3){value.axis_a.x,value.axis_a.y,value.axis_a.z},(GeoPoint3){0,1,0})||
           !point_equal((GeoPoint3){value.axis_b.x,value.axis_b.y,value.axis_b.z},(GeoPoint3){0,0,1}))return 1;
    }
    /* Constructor boundaries stay unchanged; parser and World admit roles
     * and ranges. Moving this code must not introduce another admission gate. */
    if(!wood_member_construct(0,0,INT64_MAX,GEO_COORD_LIMIT+1,true,(WoodMemberRole)7,0,&value)||
       value.id!=0||value.size_a!=INT64_MAX||value.size_b!=GEO_COORD_LIMIT+1||
       (int)value.role!=7||value.cut_priority!=8||strcmp(wood_member_role_name(value.role),"?"))return 1;
    if(!wood_member_construct(0,0,1,1,true,WOOD_MEMBER_ROLE_CUSTOM,INT64_MAX,&value)||value.cut_priority!=INT64_MAX)return 1;
    return 0;
}

static int rejection(void)
{
    const struct {GeoCoord length,a,b;bool automatic;WoodMemberRole role;GeoCoord priority;} invalid[]={
        {0,0,4,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {0,-1,4,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {0,4,0,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {0,4,-1,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {0,4,4,false,WOOD_MEMBER_ROLE_PRIMARY,0},
        {1,4,4,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {-1,4,4,true,WOOD_MEMBER_ROLE_PRIMARY,0},
        {0,4,4,true,WOOD_MEMBER_ROLE_CUSTOM,0},
        {0,4,4,true,WOOD_MEMBER_ROLE_CUSTOM,-1}
    };
    for(size_t i=0;i<sizeof invalid/sizeof invalid[0];++i){
        WoodMember output,before;memset(&output,0x5a,sizeof output);memcpy(&before,&output,sizeof output);
        if(wood_member_construct(3,invalid[i].length,invalid[i].a,invalid[i].b,invalid[i].automatic,
                                 invalid[i].role,invalid[i].priority,&output)||memcmp(&output,&before,sizeof output))return 1;
    }
    if(wood_member_construct(0,0,1,1,true,WOOD_MEMBER_ROLE_PRIMARY,0,NULL))return 1;
    return 0;
}

static int names(void)
{
    const char *full[]={"A0（接觸面）","A1（另一個 A 面）","B0","B1","START 端面","END 端面"};
    const char *brief[]={"A0","A1","B0","B1","START","END"};
    for(int face=0;face<6;++face){
        if(!wood_member_face_valid((WoodMemberFace)face)||
           strcmp(wood_member_face_name((WoodMemberFace)face),full[face])||
           strcmp(wood_member_face_short_name((WoodMemberFace)face),brief[face]))return 1;
    }
    const int invalid[]={-1,6,7,1000};
    for(size_t i=0;i<sizeof invalid/sizeof invalid[0];++i){
        WoodMemberFace face=(WoodMemberFace)invalid[i];
        if(wood_member_face_valid(face)||strcmp(wood_member_face_name(face),"UNKNOWN_FACE")||
           strcmp(wood_member_face_short_name(face),"?"))return 1;
    }
    return 0;
}

/* Explicit expected local corners for L=10,A=20,B=30 in the historical
 * outward order. This oracle does not consult K's axis/side or walk tables. */
static const GeoPoint3 corners[6][4]={
    {{0,0,0},{0,20,0},{10,20,0},{10,0,0}},
    {{0,0,30},{10,0,30},{10,20,30},{0,20,30}},
    {{0,0,0},{10,0,0},{10,0,30},{0,0,30}},
    {{0,20,0},{0,20,30},{10,20,30},{10,20,0}},
    {{0,0,0},{0,0,30},{0,20,30},{0,20,0}},
    {{10,0,0},{10,20,0},{10,20,30},{10,0,30}}
};

static int faces(void)
{
    const GeoVector3 directions[]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    unsigned frames=0;
    for(size_t l=0;l<6;++l)for(size_t a=0;a<6;++a){
        GeoVector3 x=directions[l],y=directions[a];
        if(x.x*y.x+x.y*y.y+x.z*y.z)continue;
        GeoVector3 z={x.y*y.z-x.z*y.y,x.z*y.x-x.x*y.z,x.x*y.y-x.y*y.x};
        WoodMember member,before;
        if(!wood_member_construct(5,0,20,30,true,WOOD_MEMBER_ROLE_SECONDARY,0,&member))return 1;
        member.length=10;member.placed=true;member.origin=(GeoPoint3){101,-211,307};
        member.axis_length=x;member.axis_a=y;member.axis_b=z;memcpy(&before,&member,sizeof member);
        for(int face=0;face<6;++face){
            GeoQuad3 quad;if(!wood_member_face_room(&member,(WoodMemberFace)face,&quad))return 1;
            for(size_t i=0;i<4;++i){
                GeoPoint3 local=corners[face][i];
                GeoPoint3 expected={101+local.x*x.x+local.y*y.x+local.z*z.x,
                    -211+local.x*x.y+local.y*y.y+local.z*z.y,
                    307+local.x*x.z+local.y*y.z+local.z*z.z};
                if(!point_equal(quad.vertices[i],expected))return 1;
            }
            if(memcmp(&member,&before,sizeof member))return 1;
        }
        ++frames;
    }
    return frames==24?0:1;
}

static int face_rejection(void)
{
    WoodMember member;GeoQuad3 output,before;
    wood_member_construct(5,0,20,30,true,WOOD_MEMBER_ROLE_PRIMARY,0,&member);
    memset(&output,0x5a,sizeof output);memcpy(&before,&output,sizeof output);
    if(wood_member_face_room(&member,WOOD_MEMBER_FACE_A0,&output)||memcmp(&output,&before,sizeof output))return 1;
    member.placed=true;
    if(wood_member_face_room(NULL,WOOD_MEMBER_FACE_A0,&output)||memcmp(&output,&before,sizeof output))return 1;
    if(wood_member_face_room(&member,WOOD_MEMBER_FACE_A0,NULL))return 1;
    for(int face=-1;face<=6;face+=7){
        if(wood_member_face_room(&member,(WoodMemberFace)face,&output)||memcmp(&output,&before,sizeof output))return 1;
    }
    /* No added length/admission check: the original geometry path also
     * exposes a degenerate face when a caller supplies placed length zero. */
    if(!wood_member_face_room(&member,WOOD_MEMBER_FACE_A0,&output))return 1;
    if(!point_equal(output.vertices[0],(GeoPoint3){0,0,0})||
       !point_equal(output.vertices[1],(GeoPoint3){0,20,0})||
       !point_equal(output.vertices[2],(GeoPoint3){0,20,0})||
       !point_equal(output.vertices[3],(GeoPoint3){0,0,0}))return 1;
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"layout"))return layout();
    if(!strcmp(argv[1],"construction"))return construction();
    if(!strcmp(argv[1],"rejection"))return rejection();
    if(!strcmp(argv[1],"names"))return names();
    if(!strcmp(argv[1],"faces"))return faces();
    if(!strcmp(argv[1],"face-rejection"))return face_rejection();
    return 2;
}
