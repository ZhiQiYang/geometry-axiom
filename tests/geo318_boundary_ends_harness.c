/* Approved Reading A numeric witnesses. Returned faces deliberately differ
 * from the raw member footprint in FEATURE controls; W must consume faces. */
#include "contact_world.h"
#include "member_reference.h"
#include "world_validation.h"
#include <stdio.h>
#include <string.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
typedef struct {
    WoodBoundaryRegion boundary;
    WoodMember self,other,liner;
    WoodContactMemberFact members[3];
    WoodContactWorld world;
    WoodStopFace faces[32];size_t count;
    WoodGridState grids;
    bool overlap,source_fail;
} Fixture;
static void init(Fixture *f,GeoCoord step)
{
    memset(f,0,sizeof *f);
    f->boundary.id=7;f->boundary.outline.count=6;
    GeoPoint2 p[6]={{0,0},{500,0},{500,step},{1000,step},{1000,1000},{0,1000}};
    memcpy(f->boundary.outline.v,p,sizeof p);
    for(size_t i=0;i<6;++i)f->boundary.outline.fixity[i]=WOOD_STOP_FIXED;
    f->self=(WoodMember){.id=1,.size_a=27,.size_b=20,.length=500,.role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1,.auto_length=true,.placed=true};
    f->other=(WoodMember){.id=2,.size_a=27,.size_b=20,.length=500,.role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=99,.auto_length=true,.placed=true};
    f->members[0]=(WoodContactMemberFact){&f->self,7,2,false,true,{0,0,500,27}};
    f->members[1]=(WoodContactMemberFact){&f->other,7,1,false,true,{500,step,1000,step+27}};
    f->world=(WoodContactWorld){.placement_id=7,.regions={&f->boundary},.region_count=1,.role_boundary=&f->boundary,.members=f->members,.member_count=2};
    f->count=wood_contact_collect_stops(&f->world,false,&f->self,f->faces,32);
}
/* Enables a third placed member whose footprint may line the RC plane at the
 * end from the member's own side; collected stops are left unchanged. */
static void line_rc(Fixture *f,GeoRect2 footprint)
{f->liner=f->self;f->liner.id=3;f->members[2]=(WoodContactMemberFact){&f->liner,7,3,true,true,footprint};f->world.member_count=3;}
static WoodStopFace *member_face(Fixture *f)
{for(size_t i=0;i<f->count;++i)if(f->faces[i].kind==WOOD_STOP_MEMBER_SIDE&&f->faces[i].timber_id==2&&f->faces[i].edge_index==0)return &f->faces[i];return NULL;}
static WoodStopFace *rc_face(Fixture *f)
{for(size_t i=0;i<f->count;++i)if(f->faces[i].kind==WOOD_STOP_OUTLINE_EDGE&&f->faces[i].fixed==500)return &f->faces[i];return NULL;}
static WoodBoundaryEndAdmission policy(Fixture *f,const WoodStopFace *required)
{return wood_contact_boundary_end_admission(&f->world,&f->self,false,0,500,0,27,1,f->faces,f->count,required);}
static bool span_policy(void *user,const WoodMember *self,bool along,GeoCoord s,GeoCoord e,GeoCoord lo,GeoCoord hi,int end,
    const WoodStopFace *faces,size_t count,const WoodStopFace *required,WoodBoundaryEndAdmission *out)
{Fixture *f=user;if(f->source_fail)return false;*out=wood_contact_boundary_end_admission(&f->world,self,along,s,e,lo,hi,end,faces,count,required);return true;}
static int eligibility(void)
{
    Fixture f;
    for(GeoCoord step=1;step<=26;++step){init(&f,step);CHECK("positive-contact-without-new-minimum",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);}
    init(&f,13);CHECK("same-axis-fourteen-mm-contact",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);
    for(int role=WOOD_MEMBER_ROLE_BOUNDARY;role<=WOOD_MEMBER_ROLE_CUSTOM;++role){f.other.role=(WoodMemberRole)role;CHECK("target-role-and-priority-not-locked",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);}
    f.self.role=WOOD_MEMBER_ROLE_PRIMARY;CHECK("primary-cannot-borrow-boundary",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    f.self.role=WOOD_MEMBER_ROLE_SECONDARY;CHECK("secondary-cannot-borrow-boundary",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    f.self.role=WOOD_MEMBER_ROLE_CUSTOM;CHECK("custom-cannot-borrow-boundary",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    init(&f,13);f.other.placed=false;CHECK("only-already-placed-timber",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);f.other.placed=true;
    f.members[1].placement_id=8;CHECK("same-placement-required",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);f.members[1].placement_id=7;
    f.members[1].footprint_valid=false;CHECK("invalid-source-footprint-refused",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);f.members[1].footprint_valid=true;
    f.boundary.outline.fixity[0]=WOOD_STOP_FREE;CHECK("fixed-positioning-edge-required",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);f.boundary.outline.fixity[0]=WOOD_STOP_FIXED;
    CHECK("whole-fixed-edge-required",wood_contact_boundary_end_admission(&f.world,&f.self,false,0,499,0,27,1,f.faces,f.count,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    CHECK("positioning-edge-endpoint-required",wood_contact_boundary_end_admission(&f.world,&f.self,false,0,600,0,27,1,f.faces,f.count,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    CHECK("i5-complete-footprint-required",wood_contact_boundary_end_admission(&f.world,&f.self,false,0,600,0,27,0,f.faces,f.count,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    return 0;
}
static int features(void)
{
    Fixture f;init(&f,13);WoodStopFace *m=member_face(&f),*rc=rc_face(&f);CHECK("feature-fixture",m&&rc);
    CHECK("returned-partial-feature-positive",policy(&f,m)==WOOD_BOUNDARY_END_PARTIAL);
    m->fixed=501;CHECK("moved-feature-not-raw-footprint",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);m->fixed=500;
    m->lo=m->hi=27;CHECK("zero-feature-not-raw-footprint",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    m->lo=27;m->hi=54;CHECK("point-feature-is-not-contact",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);
    m->lo=13;m->hi=40;m->edge_index=1;CHECK("wrong-side-feature-not-contact",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);m->edge_index=0;
    m->fixity=WOOD_STOP_FREE;CHECK("free-member-face-not-contact",policy(&f,NULL)==WOOD_BOUNDARY_END_ORDINARY);m->fixity=WOOD_STOP_FIXED;
    rc->hi=26;CHECK("short-rc-feature-permitted",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);
    rc->hi=27;CHECK("exact-width-rc-feature-refused",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    rc->hi=100;CHECK("true-rc-length-not-leftover-gap",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    rc->hi=15;f.faces[f.count++]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,7,0,-1,2,WOOD_STOP_FIXED,500,15,30};
    CHECK("collinear-rc-subdivision-joined",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    f.faces[f.count-1].boundary_id=99;CHECK("different-rc-host-not-joined",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);
    /* #318 RC run rule: the 113 mm RC face is measured along the unlined run
     * holding the exposed 13 mm, bounded by placed members lining it. */
    init(&f,13);rc=rc_face(&f);CHECK("run-fixture",rc!=NULL);rc->lo=-100;
    CHECK("long-unlined-rc-run-refused",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    line_rc(&f,(GeoRect2){400,-100,500,0});
    CHECK("lined-rc-short-run-permitted",policy(&f,NULL)==WOOD_BOUNDARY_END_PARTIAL);
    f.members[2].footprint=(GeoRect2){400,-100,500,-14};
    CHECK("lined-rc-run-that-fits-refused",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    f.members[2].footprint=(GeoRect2){500,-100,600,0};
    CHECK("far-side-member-does-not-line",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    f.members[2].footprint=(GeoRect2){400,-100,500,0};f.liner.placed=false;
    CHECK("unplaced-member-does-not-line",policy(&f,NULL)==WOOD_BOUNDARY_END_BARE_RC);
    return 0;
}
static WoodMemberSpanStatus resolve(Fixture *f,bool between,uint32_t named,char *error,size_t cap)
{
    GeoRegionView region={{f->boundary.outline.v,f->boundary.outline.count},NULL,0};
    GeoRect2 obstacle=f->members[1].footprint;
    WoodMemberSpanFacts facts={.domain={&region,1},.obstacles=&obstacle,.obstacle_count=1,.stops=f->faces,.stop_count=f->count,.boundary_end=span_policy,.boundary_user=f};
    WoodMemberSpanRequest request={.along_v=false,.cross_lo=0,.cross_hi=27,.between=between,.stops={{0,-1,5,0},{1,-1,0,named}},.self=&f->self};
    GeoCoord s=-1,e=-1;WoodMemberSpanStatus status=wood_member_resolve_span(&facts,&request,&s,&e,error,cap);
    if(status==WOOD_SPAN_OK&&(s!=0||e!=500)){snprintf(error,cap,"wrong numeric span");return WOOD_SPAN_NO_INTERVAL;}
    return status;
}
static int spans(void)
{
    Fixture f;char error[512];init(&f,13);
    CHECK("collector-partial-without-fullwidth",wood_contact_end_support_check(policy(&f,NULL),0,false,error,sizeof error));
    CHECK("collector-ordinary-still-fullwidth",!wood_contact_end_support_check(WOOD_BOUNDARY_END_ORDINARY,0,false,error,sizeof error));
    CHECK("collector-bare-rc-never-falls-back",!wood_contact_end_support_check(WOOD_BOUNDARY_END_BARE_RC,1,false,error,sizeof error));
    CHECK("span-accepts-partial-end",resolve(&f,false,0,error,sizeof error)==WOOD_SPAN_OK);
    CHECK("between-accepts-exact-contact-source",resolve(&f,true,2,error,sizeof error)==WOOD_SPAN_OK);
    CHECK("between-does-not-borrow-other-source",resolve(&f,true,999,error,sizeof error)==WOOD_SPAN_BETWEEN_BLOCKED);
    WoodStopFace *m=member_face(&f);CHECK("between-member-fixture",m!=NULL);m->edge_index=1;
    CHECK("between-wrong-side-not-contact",resolve(&f,true,2,error,sizeof error)==WOOD_SPAN_BETWEEN_BLOCKED);m->edge_index=0;
    /* A named narrow face at this endpoint cannot borrow a different member's
     * valid partial contact. This deliberately uses immutable returned facts. */
    f.faces[f.count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,3,-1,1,WOOD_STOP_FIXED,500,13,40};
    CHECK("between-required-face-must-itself-contact",resolve(&f,true,3,error,sizeof error)==WOOD_SPAN_BETWEEN_BLOCKED);
    f.source_fail=true;CHECK("ordered-source-failure-closed",resolve(&f,false,0,error,sizeof error)==WOOD_SPAN_START_UNSUPPORTED);f.source_fail=false;
    rc_face(&f)->hi=27;
    CHECK("single-full-rc-span-refused",resolve(&f,false,0,error,sizeof error)==WOOD_SPAN_END_UNSUPPORTED&&strstr(error,"V_CUT_PRIORITY")&&strstr(error,"裸露"));
    CHECK("between-bare-rc-refused",resolve(&f,true,2,error,sizeof error)==WOOD_SPAN_BETWEEN_BLOCKED&&strstr(error,"V_CUT_PRIORITY")&&strstr(error,"裸露"));
    init(&f,13);f.world.member_count=1;f.count=wood_contact_collect_stops(&f.world,false,&f.self,f.faces,32);
    CHECK("partial-rc-alone-remains-unsupported",resolve(&f,false,0,error,sizeof error)==WOOD_SPAN_END_UNSUPPORTED);
    return 0;
}
static bool validation_member(void *user,size_t i,WoodWorldMemberFact *out)
{Fixture *f=user;*out=(WoodWorldMemberFact){.member=i?&f->other:&f->self,.placement_id=7,.length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL,.has_between=false};return true;}
static uint32_t validation_placement(void *user,size_t i){(void)user;(void)i;return 7;}
static bool validation_host(void *user,uint32_t id,const GeoRect2 *rect,WoodGridHost *out)
{(void)user;(void)id;(void)rect;*out=(WoodGridHost){.id=7};return true;}
static bool validation_footprint(void *user,size_t i,uint32_t id,GeoRect2 *out)
{Fixture *f=user;(void)id;*out=i&&f->overlap?(GeoRect2){400,13,600,40}:f->members[i].footprint;return true;}
static bool validation_place(void *user,uint32_t id,WoodMember *m,GeoPoint2 uv,int direction,int depth)
{(void)user;(void)id;(void)m;(void)uv;(void)direction;(void)depth;return true;}
static size_t validation_stops(void *user,uint32_t id,const GeoRect2 *rect,bool along,const WoodMember *m,WoodStopFace *out,size_t cap)
{Fixture *f=user;(void)id;(void)along;(void)cap;if(m->id==1){memcpy(out,f->faces,f->count*sizeof *out);return f->count;}
 out[0]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,7,0,-1,5,WOOD_STOP_FIXED,rect->min_u,rect->min_v,rect->max_v};
 out[1]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,7,0,-1,1,WOOD_STOP_FIXED,rect->max_u,rect->min_v,rect->max_v};return 2;}
static bool validation_end(void *user,uint32_t id,const GeoRect2 *rect,const WoodMember *m,bool along,char *error,size_t cap)
{(void)user;(void)id;(void)rect;(void)m;(void)along;(void)error;(void)cap;return true;}
static bool validation_policy(void *user,uint32_t id,const GeoRect2 *rect,const WoodMember *m,bool along,int end,const WoodStopFace *faces,size_t count,WoodBoundaryEndAdmission *out)
{Fixture *f=user;(void)id;if(f->source_fail)return false;*out=wood_contact_boundary_end_admission(&f->world,m,along,rect->min_u,rect->max_u,rect->min_v,rect->max_v,end,faces,count,NULL);return true;}
static int revalidation(void)
{
    Fixture f;init(&f,13);char error[512];f.other.role=WOOD_MEMBER_ROLE_CUSTOM;
    WoodWorldValidationContext ctx={.grids={.state=&f.grids},.user=&f,.member_count=1,.placement_count=1,.member_at=validation_member,.placement_id=validation_placement,.host=validation_host,.footprint=validation_footprint,.place=validation_place,.stops=validation_stops,.end_faces=validation_end,.boundary_role=validation_end,.boundary_end=validation_policy};
    CHECK("r6e-accepts-partial-without-fullwidth-recheck",wood_world_validate_members(&ctx,error,sizeof error));
    rc_face(&f)->hi=27;CHECK("r6e-single-full-rc-feature-refused",!wood_world_validate_members(&ctx,error,sizeof error)&&strstr(error,"V_CUT_PRIORITY")&&strstr(error,"裸露"));rc_face(&f)->hi=13;
    f.source_fail=true;CHECK("r6e-source-failure-closed",!wood_world_validate_members(&ctx,error,sizeof error));f.source_fail=false;
    ctx.member_count=2;f.overlap=true;
    CHECK("partial-does-not-skip-world-collision",!wood_world_validate_members(&ctx,error,sizeof error));
    f.overlap=false;CHECK("nonoverlapping-world-preserved",wood_world_validate_members(&ctx,error,sizeof error));
    return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"eligibility"))return eligibility();if(!strcmp(argv[1],"features"))return features();if(!strcmp(argv[1],"spans"))return spans();if(!strcmp(argv[1],"revalidation"))return revalidation();return 2;}
