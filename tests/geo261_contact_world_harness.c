/* Independent numeric witnesses for the real ordered W contact evaluator.
 * Borrowed member addresses are candidate identities, including on failure. */
#include "contact_world.h"
#include <stdio.h>
#include <string.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static WoodMember member(uint32_t id,WoodMemberRole role,GeoCoord priority)
{WoodMember m={0};m.id=id;m.role=role;m.cut_priority=priority;m.placed=true;return m;}
static WoodBoundaryRegion square(uint32_t id,GeoCoord u,GeoCoord v,GeoCoord size)
{WoodBoundaryRegion b={0};b.id=id;b.outline.count=4;GeoPoint2 p[4]={{u,v},{u+size,v},{u+size,v+size},{u,v+size}};memcpy(b.outline.v,p,sizeof p);for(int i=0;i<4;++i)b.outline.fixity[i]=WOOD_STOP_FIXED;return b;}
static WoodBoundaryRegion elbow(void)
{WoodBoundaryRegion b={0};b.id=7;b.outline.count=6;GeoPoint2 p[6]={{0,0},{100,0},{100,50},{50,50},{50,100},{0,100}};memcpy(b.outline.v,p,sizeof p);for(int i=0;i<6;++i)b.outline.fixity[i]=WOOD_STOP_FIXED;return b;}
static WoodContactMemberFact fact(const WoodMember *m,uint64_t order,bool along,GeoRect2 rect)
{return (WoodContactMemberFact){m,7,order,along,true,rect};}
static bool face(const WoodStopFace *f,int kind,uint32_t bid,uint32_t mid,int hole,int edge,int fixity,GeoCoord at,GeoCoord lo,GeoCoord hi)
{return f->kind==kind&&f->boundary_id==bid&&f->timber_id==mid&&f->hole_index==hole&&f->edge_index==edge&&f->fixity==fixity&&f->fixed==at&&f->lo==lo&&f->hi==hi;}
static size_t sides(const WoodStopFace *f,size_t n,uint32_t id)
{size_t count=0;for(size_t i=0;i<n;++i)if(f[i].kind==WOOD_STOP_MEMBER_SIDE&&f[i].timber_id==id)++count;return count;}

static int ordering(void)
{
    WoodMember m[4]={member(41,WOOD_MEMBER_ROLE_BOUNDARY,1),member(42,WOOD_MEMBER_ROLE_PRIMARY,2),member(43,WOOD_MEMBER_ROLE_PRIMARY,2),member(44,WOOD_MEMBER_ROLE_PRIMARY,2)};
    WoodContactMemberFact f[4]={fact(&m[0],30,false,(GeoRect2){70,0,80,10}),fact(&m[1],10,false,(GeoRect2){20,20,30,30}),fact(&m[2],10,false,(GeoRect2){40,40,50,50}),fact(&m[3],20,false,(GeoRect2){55,60,65,70})};
    WoodContactWorld w={.placement_id=7,.members=f,.member_count=4};WoodStopFace out[20];size_t n=wood_contact_collect_stops(&w,false,NULL,out,20);
    CHECK("placement-order-before-declaration",n==8&&(out[0].timber_id==42||out[0].timber_id==43)&&out[4].timber_id==44&&out[6].timber_id==41);
    CHECK("placement-stable-equal-order-sides",out[0].edge_index==0&&out[1].edge_index==1&&out[2].timber_id==43&&out[2].edge_index==0&&out[3].edge_index==1);
    CHECK("member-side-numeric-values",face(&out[0],WOOD_STOP_MEMBER_SIDE,0,42,-1,0,WOOD_STOP_FIXED,20,20,30)&&face(&out[1],WOOD_STOP_MEMBER_SIDE,0,42,-1,1,WOOD_STOP_FIXED,30,20,30));
    f[2].footprint=f[1].footprint;w.members=f+1;w.member_count=2;n=wood_contact_collect_stops(&w,false,NULL,out,20);
    CHECK("equal-order-not-deduplicated",n==4&&sides(out,n,42)==2&&sides(out,n,43)==2);
    f[1].order=1;f[2].order=2;n=wood_contact_collect_stops(&w,false,NULL,out,20);
    CHECK("earlier-full-cover-deduplicates",n==2&&sides(out,n,42)==2&&sides(out,n,43)==0);
    f[1].footprint=(GeoRect2){20,20,30,30};f[2].footprint=(GeoRect2){20,20,30,40};n=wood_contact_collect_stops(&w,false,NULL,out,20);
    CHECK("partial-shadow-retains-exposed-face",n==4&&sides(out,n,43)==2);
    CHECK("partial-shadow-request-specific",wood_stop_shadowed(out,2,22,28)&&!wood_stop_shadowed(out,2,32,38));
    WoodBoundaryRegion b=square(7,0,0,100);b.outline.fixity[3]=WOOD_STOP_FREE;w.regions[0]=&b;w.region_count=1;w.members=f;w.member_count=1;f[0].footprint=(GeoRect2){0,20,10,30};
    n=wood_contact_collect_stops(&w,false,NULL,out,20);CHECK("boundary-even-free-owns-coincident-face",n==3&&sides(out,n,41)==1&&out[2].fixed==10&&out[1].fixity==WOOD_STOP_FREE);
    WoodMember copy=m[0];w.region_count=0;n=wood_contact_collect_stops(&w,false,&copy,out,20);CHECK("stop-exclusion-keeps-candidate-identity",n==2&&wood_contact_collect_stops(&w,false,&m[0],out,20)==0);
    f[0].placement_id=8;CHECK("stop-other-placement-ignored",wood_contact_collect_stops(&w,false,NULL,out,20)==0);f[0].placement_id=7;
    f[0].footprint_valid=false;CHECK("stop-invalid-footprint-ignored",wood_contact_collect_stops(&w,false,NULL,out,20)==0);f[0].footprint_valid=true;
    m[0].placed=false;CHECK("stop-unplaced-member-ignored",wood_contact_collect_stops(&w,false,NULL,out,20)==0);return 0;
}
static int regions_and_capacity(void)
{
    WoodBoundaryRegion a=square(7,0,0,100),b=square(8,200,300,100),hole=square(0,20,30,10),hole2=square(0,220,330,10);
    a.holes[0]=hole.outline;a.hole_count=1;b.holes[0]=hole2.outline;b.hole_count=1;b.outline.fixity[1]=WOOD_STOP_FREE;b.holes[0].fixity[3]=WOOD_STOP_FREE;
    WoodContactWorld w={.placement_id=7,.regions={&a,&b},.region_count=2};WoodStopFace out[16];size_t n=wood_contact_collect_stops(&w,false,NULL,out,16);
    CHECK("regions-all-outline-and-hole-faces",n==8&&face(&out[0],WOOD_STOP_OUTLINE_EDGE,7,0,-1,1,1,100,0,100)&&face(&out[2],WOOD_STOP_HOLE_EDGE,7,0,0,1,1,30,30,40));
    CHECK("region-outline-index-encoded",face(&out[4],WOOD_STOP_OUTLINE_EDGE,8,0,-1,33,0,300,300,400)&&face(&out[5],WOOD_STOP_OUTLINE_EDGE,8,0,-1,35,1,200,300,400));
    CHECK("region-hole-index-encoded",face(&out[6],WOOD_STOP_HOLE_EDGE,8,0,8,1,1,230,330,340)&&face(&out[7],WOOD_STOP_HOLE_EDGE,8,0,8,3,0,220,330,340));
    n=wood_contact_collect_stops(&w,true,NULL,out,16);CHECK("along-v-uses-horizontal-edges",n==8&&face(&out[0],WOOD_STOP_OUTLINE_EDGE,7,0,-1,0,1,0,0,100)&&face(&out[4],WOOD_STOP_OUTLINE_EDGE,8,0,-1,32,1,300,200,300));
    memset(out,0x5a,sizeof out);WoodStopFace untouched=out[1];CHECK("boundary-capacity-and-tail",wood_contact_collect_stops(&w,false,NULL,out,1)==1&&!memcmp(&out[1],&untouched,sizeof untouched));
    CHECK("zero-capacity-no-output",wood_contact_collect_stops(&w,false,NULL,NULL,0)==0);
    WoodMember m[2]={member(11,WOOD_MEMBER_ROLE_PRIMARY,2),member(12,WOOD_MEMBER_ROLE_PRIMARY,2)};WoodContactMemberFact f[2]={fact(&m[0],9,false,(GeoRect2){10,20,30,40}),fact(&m[1],1,false,(GeoRect2){50,60,70,80})};w.region_count=0;w.members=f;w.member_count=2;
    memset(out,0x5a,sizeof out);untouched=out[2];n=wood_contact_collect_stops(&w,false,NULL,out,3);
    CHECK("member-capacity-pair-atomic",n==2&&!memcmp(&out[2],&untouched,sizeof untouched));
    CHECK("capacity-before-placement-order",out[0].timber_id==11&&out[1].timber_id==11);
    CHECK("face-capacity-contract",WOOD_CONTACT_FACE_CAPACITY==2432&&WOOD_CONTACT_COMPONENT_CAPACITY==8&&WOOD_CONTACT_MEMBER_CAPACITY==64);
    WoodBoundaryRegion many[8];WoodMember members[64];WoodContactMemberFact facts[64];WoodStopFace full[WOOD_CONTACT_FACE_CAPACITY+1];
    for(size_t c=0;c<8;++c){many[c]=square((uint32_t)(80+c),(GeoCoord)c*1000,0,100);many[c].hole_count=8;for(size_t h=0;h<8;++h){WoodBoundaryRegion cut=square(0,(GeoCoord)c*1000+10+(GeoCoord)h*10,20,4);many[c].holes[h]=cut.outline;}w.regions[c]=&many[c];}
    for(size_t i=0;i<64;++i){members[i]=member((uint32_t)(100+i),WOOD_MEMBER_ROLE_PRIMARY,2);facts[i]=fact(&members[i],64-i,false,(GeoRect2){10000+(GeoCoord)i*10,200,10002+(GeoCoord)i*10,210});}
    w.region_count=8;w.members=facts;w.member_count=64;memset(full,0x5a,sizeof full);untouched=full[272];n=wood_contact_collect_stops(&w,false,NULL,full,WOOD_CONTACT_FACE_CAPACITY);
    CHECK("all-eight-components-holes-and-sixty-four-members",n==272&&full[126].edge_index==225&&full[142].hole_index==63&&full[142].edge_index==1&&full[142].fixed==7084&&full[144].timber_id==163&&full[270].timber_id==100&&!memcmp(&full[272],&untouched,sizeof untouched));return 0;
}
static int active_dedup(void)
{
    /* Repeated public IDs use the last order for sorting and the minimum
     * order for shadowing. Removed faces must stop shadowing later faces. */
    WoodMember m=member(42,WOOD_MEMBER_ROLE_PRIMARY,2),late=member(99,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodContactMemberFact facts[3]={fact(&m,1,false,(GeoRect2){0,0,100,27}),fact(&m,2,false,(GeoRect2){0,0,100,27}),fact(&late,3,false,(GeoRect2){200,0,300,27})};
    WoodContactWorld w={.placement_id=7,.members=facts,.member_count=2};WoodStopFace out[5];
    memset(out,0x5a,sizeof out);WoodStopFace untouched=out[4];
    size_t n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("dedup-mutual-duplicate-id-leaves-final-pair",n==2&&face(&out[0],WOOD_STOP_MEMBER_SIDE,0,42,-1,0,WOOD_STOP_FIXED,0,0,27)&&face(&out[1],WOOD_STOP_MEMBER_SIDE,0,42,-1,1,WOOD_STOP_FIXED,100,0,27));
    CHECK("dedup-compaction-keeps-uncollected-tail",!memcmp(&out[4],&untouched,sizeof untouched));
    w.member_count=3;n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("dedup-never-refills-capacity-from-later-members",n==2&&out[0].timber_id==42&&out[1].timber_id==42);w.member_count=2;
    /* Zero/reversed intervals cannot shadow, even when containment alone
     * would hold. Distinct full-width coordinates must remain distinct. */
    facts[0].footprint=(GeoRect2){INT64_C(4294967296),0,INT64_C(4294967396),27};
    facts[1].footprint=(GeoRect2){0,0,100,27};
    n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("dedup-full-width-planes-preserved",n==4&&out[0].fixed==INT64_C(4294967296)&&out[2].fixed==0);
    facts[0].footprint=(GeoRect2){0,5,100,5};facts[1].footprint=facts[0].footprint;
    n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("dedup-zero-span-strict-overlap-preserved",n==4&&out[0].lo==5&&out[0].hi==5&&out[2].lo==5&&out[2].hi==5);
    facts[0].footprint=(GeoRect2){0,8,100,3};facts[1].footprint=facts[0].footprint;
    n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("dedup-reversed-span-strict-overlap-preserved",n==4&&out[0].lo==8&&out[0].hi==3&&out[2].lo==8&&out[2].hi==3);
    /* Public views may exceed the host capacity. No new rejection, heap
     * allocation or truncated bitmap is allowed in that legacy fallback. */
    enum { MANY=WOOD_CONTACT_FACE_CAPACITY/2+1 };
    static WoodContactMemberFact many[MANY];static WoodStopFace full[MANY*2+1];
    for(size_t i=0;i<MANY;++i)many[i]=fact(&m,(uint64_t)i,false,(GeoRect2){0,0,100,27});
    w.members=many;w.member_count=MANY;memset(full,0x5a,sizeof full);untouched=full[MANY*2];
    n=wood_contact_collect_stops(&w,false,NULL,full,MANY*2);
    CHECK("dedup-large-public-buffer-keeps-original-fallback",n==2&&face(&full[0],WOOD_STOP_MEMBER_SIDE,0,42,-1,0,WOOD_STOP_FIXED,0,0,27)&&face(&full[1],WOOD_STOP_MEMBER_SIDE,0,42,-1,1,WOOD_STOP_FIXED,100,0,27));
    CHECK("dedup-large-fallback-keeps-uncollected-tail",!memcmp(&full[MANY*2],&untouched,sizeof untouched));
    return 0;
}
static int indexed_dedup(void)
{
    WoodMember m[3]={member(51,WOOD_MEMBER_ROLE_PRIMARY,2),member(52,WOOD_MEMBER_ROLE_PRIMARY,2),member(53,WOOD_MEMBER_ROLE_PRIMARY,2)};
    WoodContactMemberFact f[3]={fact(&m[0],1,false,(GeoRect2){0,0,100,27}),fact(&m[1],2,false,(GeoRect2){INT64_C(4294967296),0,INT64_C(4294967396),27}),fact(&m[2],3,false,(GeoRect2){0,0,100,27})};
    WoodContactWorld w={.placement_id=7,.members=f,.member_count=2};WoodStopFace out[8];size_t n;
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-full-coordinate-plane",n==4&&sides(out,n,51)==2&&sides(out,n,52)==2&&out[2].fixed==INT64_C(4294967296));
    f[0]=fact(&m[0],1,false,(GeoRect2){0,0,100,5});f[1]=fact(&m[1],1,false,(GeoRect2){0,5,100,10});f[2]=fact(&m[2],2,false,(GeoRect2){0,0,100,10});w.member_count=3;
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-two-halves-not-one-cover",n==6&&sides(out,n,51)==2&&sides(out,n,52)==2&&sides(out,n,53)==2);
    w.member_count=2;f[0]=fact(&m[0],1,false,(GeoRect2){0,5,100,6});f[1]=fact(&m[1],2,false,(GeoRect2){0,5,100,5});
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-zero-lower-strict",n==4&&sides(out,n,52)==2);
    f[0].footprint=(GeoRect2){0,4,100,5};n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-zero-upper-strict",n==4&&sides(out,n,52)==2);
    f[0].footprint=(GeoRect2){0,2,100,9};f[1].footprint=(GeoRect2){0,8,100,3};
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-enclosed-reversed-span",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0);
    f[0].footprint=(GeoRect2){0,3,100,9};n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-reversed-touch-is-not-overlap",n==4&&sides(out,n,52)==2);
    f[0].footprint=(GeoRect2){0,4,100,6};f[1].footprint=(GeoRect2){0,5,100,5};
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-enclosed-zero-span",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0);
    f[0].footprint=(GeoRect2){0,INT64_MIN,100,INT64_MAX};f[1].footprint=(GeoRect2){0,INT64_MIN+1,100,INT64_MAX-1};
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-coordinate-extremes-without-subtraction",n==2&&face(&out[0],WOOD_STOP_MEMBER_SIDE,0,51,-1,0,WOOD_STOP_FIXED,0,INT64_MIN,INT64_MAX));
    /* The last fact is filtered from faces, but still supplies the last
     * order for ID51. Its minimum1 can shadow ID52 before ID51's sorted turn. */
    m[2].id=m[0].id;f[0]=fact(&m[0],1,false,(GeoRect2){0,0,100,27});f[1]=fact(&m[1],2,false,(GeoRect2){0,0,100,27});f[2]=fact(&m[2],3,false,(GeoRect2){0,0,100,27});w.member_count=3;
    m[2].placed=false;n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-filtered-duplicate-order",n==2&&face(&out[0],WOOD_STOP_MEMBER_SIDE,0,51,-1,0,WOOD_STOP_FIXED,0,0,27)&&face(&out[1],WOOD_STOP_MEMBER_SIDE,0,51,-1,1,WOOD_STOP_FIXED,100,0,27));
    m[2].placed=true;f[2].placement_id=8;n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-other-placement-duplicate-fallback",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0);f[2].placement_id=7;
    f[2].footprint_valid=false;n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-invalid-footprint-duplicate-fallback",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0);f[2].footprint_valid=true;
    n=wood_contact_collect_stops(&w,false,&m[2],out,8);
    CHECK("indexed-excluded-duplicate-keeps-pointer-identity",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0);
    memset(out,0x5a,sizeof out);WoodStopFace tail=out[4];n=wood_contact_collect_stops(&w,false,NULL,out,4);
    CHECK("indexed-truncated-fact-still-requires-fallback",n==2&&sides(out,n,51)==2&&sides(out,n,52)==0&&!memcmp(&out[4],&tail,sizeof tail));
    m[2].placed=false;f[0]=fact(&m[0],1,false,(GeoRect2){0,20,100,30});f[1]=fact(&m[1],2,false,(GeoRect2){0,20,100,40});f[2].order=1;
    n=wood_contact_collect_stops(&w,false,NULL,out,8);
    CHECK("indexed-duplicate-fallback-keeps-partial-shadow",n==4&&sides(out,n,51)==2&&sides(out,n,52)==2);
    return 0;
}

static int intervals(void)
{
    WoodBoundaryRegion b=elbow();GeoCoord lo=-999,hi=-888;
    CHECK("boundary-edge-whole-numeric-interval",wood_contact_boundary_interval(&b,false,0,100,40,50,&lo,&hi)&&lo==50&&hi==100);
    CHECK("boundary-vertical-numeric-interval",wood_contact_boundary_interval(&b,true,0,100,40,50,&lo,&hi)&&lo==50&&hi==100);
    {int edge=-7;
        CHECK("boundary-edge-index-horizontal",wood_contact_boundary_edge(&b,false,0,100,40,50,&lo,&hi,&edge)&&edge==2&&lo==50&&hi==100);
        edge=-7;CHECK("boundary-edge-index-vertical",wood_contact_boundary_edge(&b,true,0,100,40,50,&lo,&hi,&edge)&&edge==3&&lo==50&&hi==100);
        CHECK("boundary-edge-null-index-accepted",wood_contact_boundary_edge(&b,false,0,100,40,50,&lo,&hi,NULL)&&lo==50&&hi==100);}
    lo=-999;hi=-888;CHECK("i5-notched-footprint-deferred",!wood_contact_boundary_interval(&b,false,0,100,50,60,&lo,&hi)&&lo==-999&&hi==-888);
    {int edge=-7;lo=-999;hi=-888;CHECK("boundary-edge-failure-leaves-outputs",!wood_contact_boundary_edge(&b,false,0,100,50,60,&lo,&hi,&edge)&&edge==-7&&lo==-999&&hi==-888);}
    CHECK("interior-has-no-positioning-edge",!wood_contact_boundary_interval(&b,false,10,40,10,20,&lo,&hi));
    CHECK("null-boundary-output-preserved",!wood_contact_boundary_interval(NULL,false,0,100,40,50,&lo,&hi)&&lo==-999&&hi==-888);
    b=square(7,0,0,100);WoodBoundaryRegion hole=square(0,5,20,30);b.holes[0]=hole.outline;b.hole_count=1;
    CHECK("hole-cut-footprint-deferred",!wood_contact_boundary_interval(&b,true,0,100,0,10,&lo,&hi));
    b=square(7,0,0,100);b.outline.fixity[0]=WOOD_STOP_FREE;CHECK("interval-does-not-invent-fixity-policy",wood_contact_boundary_interval(&b,false,20,80,0,10,&lo,&hi)&&lo==0&&hi==100);return 0;
}
static int extensions(void)
{
    WoodBoundaryRegion b=elbow();WoodMember owner=member(23,WOOD_MEMBER_ROLE_BOUNDARY,1),copy=owner;
    WoodContactMemberFact f=fact(&owner,1,false,(GeoRect2){0,40,100,50});WoodContactWorld w={.placement_id=7,.role_boundary=&b,.members=&f,.member_count=1};
    CHECK("owner-extension-outside-fixed-part",wood_contact_owner_extension(&w,&owner,20,30));
    CHECK("owner-fixed-interval-inclusive",!wood_contact_owner_extension(&w,&owner,50,100)&&!wood_contact_owner_extension(&w,&owner,50,50));
    CHECK("owner-straddling-fixed-boundary",wood_contact_owner_extension(&w,&owner,49,50));
    CHECK("owner-pointer-not-id",!wood_contact_owner_extension(&w,&copy,20,30));
    owner.role=WOOD_MEMBER_ROLE_PRIMARY;CHECK("owner-boundary-role-required",!wood_contact_owner_extension(&w,&owner,20,30));owner.role=WOOD_MEMBER_ROLE_BOUNDARY;
    f.footprint_valid=false;CHECK("owner-invalid-footprint-refused",!wood_contact_owner_extension(&w,&owner,20,30));f.footprint_valid=true;
    f.footprint=(GeoRect2){0,45,100,55};CHECK("owner-notched-footprint-no-extension",!wood_contact_owner_extension(&w,&owner,20,30));
    f.footprint=(GeoRect2){40,0,50,100};f.along_v=true;CHECK("owner-vertical-axis-extension",wood_contact_owner_extension(&w,&owner,20,30)&&!wood_contact_owner_extension(&w,&owner,50,100));
    w.role_boundary=NULL;CHECK("owner-missing-role-boundary",!wood_contact_owner_extension(&w,&owner,20,30));return 0;
}
static int end_faces(void)
{
    WoodBoundaryRegion b=square(7,0,0,100);WoodMember self=member(17,WOOD_MEMBER_ROLE_PRIMARY,2);char error[512]="unchanged";
    WoodContactWorld w={.placement_id=7,.regions={&b},.region_count=1,.role_boundary=&b};
    CHECK("outline-first-error",!wood_contact_end_faces(&w,&self,false,0,100,20,30,error,sizeof error)&&!strcmp(error,"V_CUT_PRIORITY：角材 17 端面頂到外輪廓邊（RC）——那條邊還沒鋪邊界材；只有 boundary 可頂 RC"));
    for(int i=0;i<4;++i)b.outline.fixity[i]=WOOD_STOP_FREE;strcpy(error,"unchanged");CHECK("free-end-faces-ignored",wood_contact_end_faces(&w,&self,false,0,100,20,30,error,sizeof error)&&!strcmp(error,"unchanged"));
    WoodMember owners[3]={member(23,WOOD_MEMBER_ROLE_PRIMARY,8),member(24,WOOD_MEMBER_ROLE_PRIMARY,9),member(25,WOOD_MEMBER_ROLE_BOUNDARY,1)};
    WoodContactMemberFact f[3]={fact(&owners[0],10,true,(GeoRect2){-10,0,0,100}),fact(&owners[1],1,true,(GeoRect2){100,0,110,100}),fact(&owners[2],0,false,(GeoRect2){0,0,100,10})};
    w.region_count=0;w.role_boundary=NULL;w.members=f;w.member_count=2;
    CHECK("start-end-before-global-placement-order",!wood_contact_end_faces(&w,&self,false,0,100,20,30,error,sizeof error)&&strstr(error,"角材 23（優先級 8）"));
    f[1].footprint=(GeoRect2){-20,0,0,100};f[1].order=20;
    CHECK("first-face-follows-placement-order",!wood_contact_end_faces(&w,&self,false,0,100,20,30,error,sizeof error)&&strstr(error,"角材 23（優先級 8）"));
    w.member_count=1;f[0].footprint=(GeoRect2){-10,25,0,35};CHECK("narrow-end-face-ignored",wood_contact_end_faces(&w,&self,false,0,100,20,30,NULL,0));
    f[0].footprint=(GeoRect2){-10,0,-1,100};CHECK("different-end-coordinate-ignored",wood_contact_end_faces(&w,&self,false,0,100,20,30,NULL,0));
    owners[0].cut_priority=1;owners[1].cut_priority=9;f[0].order=1;f[1].order=2;f[0].footprint=(GeoRect2){-10,0,0,20};f[1].footprint=(GeoRect2){-5,0,0,100};w.member_count=2;
    CHECK("partial-earlier-face-shadows-only-contact",wood_contact_end_faces(&w,&self,false,0,100,2,8,NULL,0));
    CHECK("exposed-later-face-still-enforces-priority",!wood_contact_end_faces(&w,&self,false,0,100,25,30,NULL,0));
    b=elbow();w.role_boundary=&b;w.regions[0]=&b;w.region_count=1;owners[0].role=WOOD_MEMBER_ROLE_BOUNDARY;owners[0].cut_priority=1;f[0]=fact(&owners[0],1,false,(GeoRect2){0,40,100,50});f[1]=fact(&owners[2],0,false,(GeoRect2){0,0,100,10});
    CHECK("actual-owner-extension-priority",!wood_contact_end_faces(&w,&self,true,10,40,20,30,error,sizeof error)&&strstr(error,"角材 23（優先級 2）"));
    self.role=WOOD_MEMBER_ROLE_CUSTOM;self.cut_priority=3;CHECK("custom-three-accepts-extension",wood_contact_end_faces(&w,&self,true,10,40,20,30,NULL,0));
    self.role=WOOD_MEMBER_ROLE_PRIMARY;self.cut_priority=2;CHECK("extension-refusal-precedes-contact",!wood_contact_end_faces(&w,&self,false,0,100,40,50,error,sizeof error)&&!strcmp(error,"V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e2 [50,100] mm，低端超出 [0,50] mm"));
    self.role=WOOD_MEMBER_ROLE_BOUNDARY;owners[0].role=WOOD_MEMBER_ROLE_PRIMARY;owners[0].cut_priority=9;f[0]=fact(&owners[0],1,true,(GeoRect2){10,40,20,50});w.members=f;w.member_count=1;
    CHECK("self-boundary-extension-end-exempt",wood_contact_end_faces(&w,&self,false,20,100,40,50,NULL,0));
    self.placed=false;w.region_count=0;w.role_boundary=NULL;w.member_count=1;f[0]=fact(&self,1,true,(GeoRect2){-10,0,0,100});CHECK("unplaced-owner-is-not-contact",wood_contact_end_faces(&w,&self,false,0,100,20,30,NULL,0));return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"ordering"))return ordering();if(!strcmp(argv[1],"regions"))return regions_and_capacity();if(!strcmp(argv[1],"active-dedup"))return active_dedup();if(!strcmp(argv[1],"indexed-dedup"))return indexed_dedup();if(!strcmp(argv[1],"intervals"))return intervals();if(!strcmp(argv[1],"extensions"))return extensions();if(!strcmp(argv[1],"ends"))return end_faces();return 2;}
