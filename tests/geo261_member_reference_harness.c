/* Independent numeric and ordered-event witnesses for the actual W policy.
 * Callback facts isolate reference selection; pose/span cases invoke actual K. */
#include "member_reference.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static char error_text[512];
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s error=%s\n",tag,error_text);return 1;}}while(0)
static GeoFrame frame(void){return (GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};}
typedef struct {
    WoodMemberReferenceFact members[8];size_t count;
    WoodMemberGuideFact guides[4];size_t guide_count;
    WoodMemberPlacementFact placement;WoodMemberGridFact grid;
    GeoRect2 scope,footprint;WoodMemberEdgeFact edge;WoodMemberEdgeStatus edge_status;
    bool missing_placement,missing_grid,bad_line,bad_scope,bad_rule,bad_key,fail_guide,fail_member;
    bool fail_axis,fail_end,fail_boundary,fail_place,fail_span;
    int span_side,events[64],event_count,issues,writes,key_calls;char clause[64],first[256];
    GeoPoint2 uv;WoodMember written;WoodMemberSpanRequest requests[4];int request_count;
} Mock;
static bool member_at(void *u,size_t i,WoodMemberReferenceFact *out){Mock *m=u;if(i>=m->count)return false;*out=m->members[i];return true;}
static bool guide_at(void *u,size_t i,WoodMemberGuideFact *out){Mock *m=u;if(i>=m->guide_count)return false;*out=m->guides[i];return true;}
static bool placement_at(void *u,uint32_t id,WoodMemberPlacementFact *out){Mock *m=u;if(m->missing_placement||id!=m->placement.id)return false;*out=m->placement;return true;}
static bool grid_at(void *u,uint32_t id,WoodMemberGridFact *out){Mock *m=u;if(m->missing_grid||id!=m->grid.id)return false;*out=m->grid;return true;}
static bool grid_line(void *u,const WoodMemberReference *a,GeoCoord *out,char *err,size_t cap){Mock *m=u;(void)a;if(m->bad_line){snprintf(err,cap,"line invalid");return false;}*out=50;return true;}
static bool grid_scope(void *u,uint32_t id,GeoRect2 *out,char *err,size_t cap){Mock *m=u;(void)id;if(m->bad_scope){snprintf(err,cap,"scope invalid");return false;}*out=m->scope;return true;}
static bool rule_line(void *u,const GeoGridRuleLineRef *r,uint32_t id,GeoCoord *out,GeoRect2 *scope,char *err,size_t cap){Mock *m=u;(void)r;(void)id;if(m->bad_rule){snprintf(err,cap,"rule invalid");return false;}*out=50;*scope=m->scope;return true;}
static bool member_footprint(void *u,size_t i,uint32_t id,GeoRect2 *out){Mock *m=u;(void)i;(void)id;*out=m->footprint;return true;}
static bool resolve_key(void *u,uint32_t id,const char *key,int *hole,int *edge,char *err,size_t cap){Mock *m=u;(void)id;++m->key_calls;if(m->bad_key||strcmp(key,"exact")){snprintf(err,cap,"key invalid");return false;}*hole=10;*edge=7;return true;}
static WoodMemberEdgeStatus edge_at(void *u,uint32_t id,int hole,int edge,WoodMemberEdgeFact *out){Mock *m=u;(void)id;(void)hole;(void)edge;*out=m->edge;return m->edge_status;}
static bool eval_member(void *u,size_t i,GeoDependencyKind kind){Mock *m=u;m->events[m->event_count++]=100+(int)i*10+(int)kind;return !m->fail_member;}
static bool eval_guide(void *u,size_t i){Mock *m=u;m->events[m->event_count++]=200+(int)i;return !m->fail_guide;}
static bool span(void *u,uint32_t id,const WoodMemberSpanRequest *r,GeoCoord *lo,GeoCoord *hi,char *err,size_t cap){Mock *m=u;(void)id;m->events[m->event_count++]=300;m->requests[m->request_count++]=*r;if(m->fail_span||(m->span_side&&r->cross_lo<0)){snprintf(err,cap,"span invalid");return false;}*lo=0;*hi=100;return true;}
static bool axis(void *u,uint32_t id,const WoodMember *t,bool v,char *err,size_t cap){Mock *m=u;(void)id;(void)t;(void)v;m->events[m->event_count++]=401;if(m->fail_axis)snprintf(err,cap,"first axis error");return !m->fail_axis;}
static bool ends(void *u,uint32_t id,const WoodMember *t,const WoodMemberSpanRequest *r,GeoCoord lo,GeoCoord hi,const GeoRect2 *f,char *err,size_t cap){Mock *m=u;(void)id;(void)t;(void)r;(void)lo;(void)hi;(void)f;m->events[m->event_count++]=402;if(m->fail_end)snprintf(err,cap,"second ends error");return !m->fail_end;}
static bool boundary(void *u,uint32_t id,const WoodMember *t,const WoodMemberSpanRequest *r,GeoCoord lo,GeoCoord hi,const GeoRect2 *f,char *err,size_t cap){Mock *m=u;(void)id;(void)t;(void)r;(void)lo;(void)hi;(void)f;m->events[m->event_count++]=403;if(m->fail_boundary)snprintf(err,cap,"third boundary error");return !m->fail_boundary;}
static bool place(void *u,uint32_t id,WoodMember *t,GeoPoint2 uv,int dir,int depth){Mock *m=u;(void)id;(void)uv;(void)dir;(void)depth;m->events[m->event_count++]=500;if(m->fail_place)return false;t->placed=true;return true;}
static void write_member(void *u,size_t i,const WoodMember *t,GeoPoint2 uv){Mock *m=u;(void)i;++m->writes;m->written=*t;m->uv=uv;}
static bool issue(void *u,uint32_t id,const char *clause,const char *expected,const char *actual){Mock *m=u;(void)id;(void)expected;++m->issues;snprintf(m->clause,sizeof m->clause,"%s",clause);snprintf(error_text,sizeof error_text,"%s",actual);return false;}
static size_t issue_count(void *u){return (size_t)((Mock *)u)->issues;}
static void first_error(void *u,const char *err){Mock *m=u;snprintf(m->first,sizeof m->first,"%s",err);}
static WoodMemberReferenceContext context(Mock *m){
    WoodMemberReferenceContext w={0};w.user=m;w.member_count=m->count;w.guide_count=m->guide_count;
    w.member_at=member_at;w.guide_at=guide_at;w.placement=placement_at;w.grid=grid_at;w.grid_line=grid_line;w.grid_scope=grid_scope;w.rule_line=rule_line;w.member_footprint=member_footprint;w.resolve_key=resolve_key;w.edge=edge_at;
    w.evaluate_member=eval_member;w.evaluate_guide=eval_guide;w.span=span;w.primary_axis=axis;w.end_faces=ends;w.boundary_role=boundary;w.place=place;w.write=write_member;w.issue=issue;w.issue_count=issue_count;w.first_error=first_error;return w;
}
static Mock setup(void){
    Mock m={0};m.count=1;m.guide_count=1;m.placement=(WoodMemberPlacementFact){1,frame(),false,33};m.grid=(WoodMemberGridFact){7,1,false};m.scope=(GeoRect2){0,0,100,100};
    m.members[0].member=(WoodMember){.id=9,.size_a=27,.size_b=33,.auto_length=true,.role=WOOD_MEMBER_ROLE_PRIMARY};
    m.members[0].anchor=(WoodMemberReference){.placement_id=1,.anchor_kind=WOOD_ANCHOR_AT_LINE,.length_direction=GEO_DIRECTION_POS_V,.depth_side=0,.ref_guide=1,.order=10};m.members[0].wanted=true;
    m.guides[0]=(WoodMemberGuideFact){1,1,true,50};m.footprint=(GeoRect2){0,10,20,90};
    m.edge=(WoodMemberEdgeFact){{{0,0},{0,100}},{-1,0},-1};return m;
}
static int dependencies(void){
    Mock m=setup();m.count=4;m.members[1]=m.members[0];m.members[1].member.id=0;m.members[1].anchor.order=1;
    m.members[2]=m.members[1];m.members[2].member.id=2;m.members[2].anchor.placement_id=2;m.members[3]=m.members[1];m.members[3].member.id=3;m.members[3].wanted=false;
    m.guide_count=2;m.guides[1]=m.guides[0];m.fail_member=true;WoodMemberReferenceContext w=context(&m);bool needs=false;
    CHECK("ordered-before-is-not-required",wood_member_reference_compute(&w,0,&needs)&&needs&&m.issues==0);
    CHECK("dependency-order-kind",m.event_count==3&&m.events[0]==110+GEO_DEPENDENCY_EVALUATE_BEFORE&&m.events[1]==200&&m.events[2]==201);
    m.event_count=0;m.members[0].anchor.ref_is_timber=true;m.members[0].anchor.ref_timber=0;m.members[0].anchor.has_between=true;m.members[0].anchor.between[0]=(WoodMemberReferenceFace){.kind=1,.timber=0};m.members[0].anchor.between[1]=(WoodMemberReferenceFace){.kind=1,.timber=99};needs=true;
    CHECK("zero-identity-source-required",!wood_member_reference_compute(&w,0,&needs)&&!needs&&m.issues==1&&m.event_count==5&&m.events[3]==110+GEO_DEPENDENCY_VALUE_REQUIRED&&m.events[4]==110+GEO_DEPENDENCY_VALUE_REQUIRED&&!strcmp(m.clause,"I9/I13"));
    m=setup();m.count=2;m.members[1]=m.members[0];m.members[1].member.id=0;m.members[1].anchor.order=10;m.members[0].anchor.ref_is_timber=true;m.members[0].anchor.ref_timber=0;w=context(&m);
    CHECK("equal-order-source-refused",!wood_member_reference_compute(&w,0,&needs)&&m.event_count==1);
    m=setup();m.members[0].member.placed=true;m.members[0].wanted=false;w=context(&m);w.use_current_values=true;
    CHECK("current-placement-fastpath",wood_member_reference_compute(&w,0,&needs)&&!needs&&m.event_count==0);
    w.use_current_values=false;CHECK("unwanted-not-reconstructed",!wood_member_reference_compute(&w,0,&needs)&&!needs&&m.issues==0);
    m=setup();m.fail_guide=true;w=context(&m);CHECK("all-guide-dependencies-required",!wood_member_reference_compute(&w,0,&needs)&&!strcmp(m.clause,"I9/I13"));return 0;
}
static int anchors(void){
    Mock m=setup();WoodMemberReferenceContext w=context(&m);
    CHECK("line-positive",wood_member_reference_place(&w,0)&&m.writes==1&&m.written.length==100&&m.written.placed);
    CHECK("odd-width-positive-side",m.requests[0].cross_lo==37&&m.requests[0].cross_hi==64&&m.uv.u==64&&m.uv.v==0);
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_GRID;m.members[0].anchor.ref_grid=7;m.members[0].anchor.ref_grid_axis=1;w=context(&m);
    CHECK("grid-coordinate-axis",!wood_member_reference_place(&w,0)&&!strcmp(m.clause,"I13/I23")&&m.request_count==0);
    m.members[0].anchor.ref_grid_axis=0;m.grid.subgrid=true;m.scope=(GeoRect2){38,0,100,100};
    CHECK("scope-full-footprint",!wood_member_reference_place(&w,0)&&m.writes==0&&strstr(error_text,"完整足跡"));
    m=setup();m.placement.derived=true;m.placement.height=34;w=context(&m);
    CHECK("derived-height-and-side",!wood_member_reference_place(&w,0)&&!strcmp(m.clause,"I53")&&m.request_count==0);
    m.placement.height=33;m.members[0].anchor.depth_side=1;CHECK("derived-side",!wood_member_reference_place(&w,0)&&!strcmp(m.clause,"I53"));
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_RULE;m.members[0].anchor.ref_rule.axis=0;w=context(&m);
    CHECK("rule-scoped",wood_member_reference_place(&w,0)&&m.requests[0].scoped&&m.requests[0].scope.max_v==100);
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT;w=context(&m);CHECK("obsolete-anchor-refused",!wood_member_reference_place(&w,0)&&!strcmp(m.clause,"I12"));return 0;
}
static int candidates(void){
    Mock m=setup();m.fail_axis=m.fail_end=m.fail_boundary=true;WoodMemberReferenceContext w=context(&m);
    CHECK("all-checks-recorded-in-order",!wood_member_reference_place(&w,0)&&m.issues==3&&m.event_count==4&&m.events[1]==401&&m.events[2]==402&&m.events[3]==403&&!strcmp(m.first,"first axis error")&&m.writes==0);
    m=setup();m.count=2;m.members[1]=m.members[0];m.members[1].member.id=17;m.members[1].member.placed=true;m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_EDGE;m.members[0].anchor.ref_is_timber=true;m.members[0].anchor.ref_timber=17;w=context(&m);
    CHECK("two-candidates-ambiguous",!wood_member_reference_place(&w,0)&&m.request_count==2&&m.writes==0&&!strcmp(m.clause,"I13/R3")&&strstr(error_text,"cross[-27,0]")&&strstr(error_text,"cross[20,47]"));
    m=setup();m.count=2;m.members[1]=m.members[0];m.members[1].member.id=17;m.members[1].member.placed=true;m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_EDGE;m.members[0].anchor.ref_is_timber=true;m.members[0].anchor.ref_timber=17;m.span_side=1;w=context(&m);
    CHECK("unique-second-candidate",wood_member_reference_place(&w,0)&&m.writes==1&&m.uv.u==47&&m.requests[0].contact&&m.requests[0].contact_lo==10&&m.requests[0].contact_hi==90);
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_EDGE;w=context(&m);CHECK("outer-edge-inward",wood_member_reference_place(&w,0)&&m.requests[0].cross_lo==0&&m.requests[0].cross_hi==27);
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_EDGE;m.edge.hole=0;w=context(&m);CHECK("hole-edge-outward",wood_member_reference_place(&w,0)&&m.requests[0].cross_lo==-27&&m.requests[0].cross_hi==0);
    m=setup();m.members[0].anchor.anchor_kind=WOOD_ANCHOR_AT_EDGE;m.placement.derived=true;w=context(&m);CHECK("derived-exact-key",!wood_member_reference_place(&w,0)&&!strcmp(m.clause,"R41/I13"));
    strcpy(m.members[0].anchor.ref_derived_key,"exact");m.members[0].anchor.has_between=true;m.members[0].anchor.between[0].kind=2;strcpy(m.members[0].anchor.between[0].key,"exact");m.members[0].anchor.between[1].kind=1;m.members[0].anchor.between[1].timber=0;
    CHECK("derived-key-between",wood_member_reference_place(&w,0)&&m.key_calls==2&&m.requests[0].stops[0].hole==10&&m.requests[0].stops[0].edge==7&&m.requests[0].stops[1].kind==1&&m.requests[0].stops[1].timber==0);return 0;
}
static int roles(void){
    WoodMemberAxisFact facts[4]={{1,8,WOOD_MEMBER_ROLE_PRIMARY,true,false},{2,8,WOOD_MEMBER_ROLE_PRIMARY,true,true},{3,9,WOOD_MEMBER_ROLE_PRIMARY,true,true},{4,8,WOOD_MEMBER_ROLE_PRIMARY,false,true}};
    CHECK("primary-axis-unique",!wood_member_primary_axis_check(facts,4,8,NULL,false,error_text,sizeof error_text)&&strstr(error_text,"角材 1 沿 u,角材 2 沿 v"));
    facts[1].role=WOOD_MEMBER_ROLE_SECONDARY;CHECK("secondary-perpendicular",wood_member_primary_axis_check(facts,4,8,NULL,false,error_text,sizeof error_text));
    facts[1].along_v=false;CHECK("secondary-parallel-refused",!wood_member_primary_axis_check(facts,4,8,NULL,false,error_text,sizeof error_text));
    facts[0].role=WOOD_MEMBER_ROLE_CUSTOM;CHECK("secondary-needs-axis",!wood_member_primary_axis_check(facts,4,8,NULL,false,error_text,sizeof error_text)&&strstr(error_text,"未定義"));
    facts[0].role=WOOD_MEMBER_ROLE_BOUNDARY;CHECK("boundary-fallback-axis",wood_member_primary_axis_check(facts,4,8,NULL,false,error_text,sizeof error_text));
    WoodMember extra={.id=5,.role=WOOD_MEMBER_ROLE_PRIMARY};CHECK("extra-even-unplaced",!wood_member_primary_axis_check(facts,1,8,&extra,false,error_text,sizeof error_text));return 0;
}
static int boundary_roles(void){
    GeoPoint2 points[]={{0,0},{100,0},{100,100},{0,100}};GeoLoop2View loop={points,4};int fixed[]={1,1,1,1};WoodMember t={.id=17,.role=WOOD_MEMBER_ROLE_BOUNDARY};
    CHECK("boundary-complete-fixed",wood_member_boundary_role_check(&t,&loop,fixed,true,false,0,100,0,10,error_text,sizeof error_text));
    fixed[0]=0;CHECK("boundary-fixed-required",!wood_member_boundary_role_check(&t,&loop,fixed,true,false,0,100,0,10,error_text,sizeof error_text)&&strstr(error_text,"e0 是自由邊"));
    fixed[0]=1;CHECK("boundary-full-edge-required",!wood_member_boundary_role_check(&t,&loop,fixed,true,false,10,90,0,10,error_text,sizeof error_text)&&strstr(error_text,"80 / 100 mm"));
    CHECK("boundary-side-required",!wood_member_boundary_role_check(&t,&loop,fixed,true,false,0,100,10,20,error_text,sizeof error_text)&&strstr(error_text,"沒有任何側面"));
    CHECK("outside-defers-to-i5",wood_member_boundary_role_check(&t,&loop,fixed,false,false,-5,100,0,10,error_text,sizeof error_text));
    t.role=WOOD_MEMBER_ROLE_PRIMARY;CHECK("nonboundary-exempt",wood_member_boundary_role_check(&t,&loop,fixed,true,false,10,90,10,20,error_text,sizeof error_text));return 0;
}
static int poses(void){
    GeoPoint2 points[]={{0,0},{100,0},{100,100},{0,100}};GeoRegionView region={{points,4},NULL,0};GeoRegionSetView domain={&region,1};int fixed[]={1,1,1,1};const int *fixities[]={fixed};GeoFrame f=frame();
    for(int dir=0;dir<4;++dir)for(int depth=0;depth<2;++depth){
        GeoRect2 rect=dir<2?(GeoRect2){10,20,60,30}:(GeoRect2){20,10,30,60};
        const GeoPoint2 corners[4][2]={{{10,20},{10,30}},{{60,30},{60,20}},{{30,10},{20,10}},{{20,60},{30,60}}};
        GeoPoint2 corner=wood_member_anchor_corner(&f,dir,depth,&rect);CHECK("anchor-corners-all-signs",corner.u==corners[dir][depth].u&&corner.v==corners[dir][depth].v);
        WoodMember t={.length=50,.size_a=10,.size_b=5};CHECK("pose-all-signs",wood_member_place_a0(&t,&f,&domain,fixities,corner,dir,depth)&&t.placed&&t.origin.x==10+corner.u&&t.origin.y==20+corner.v&&t.origin.z==30);
        GeoVector3 b=geo_vector_cross(t.axis_length,t.axis_a);CHECK("pose-right-handed",b.x==t.axis_b.x&&b.y==t.axis_b.y&&b.z==t.axis_b.z&&b.z==(depth?-1:1));
    }
    WoodMember t={.length=100,.size_a=10,.size_b=5},before=t;fixed[1]=0;
    CHECK("pose-free-end-refused",!wood_member_place_a0(&t,&f,&domain,fixities,(GeoPoint2){0,20},0,0)&&!memcmp(&t,&before,sizeof t));
    CHECK("rect-no-end-fixity",wood_member_place_a0(&t,&f,&domain,NULL,(GeoPoint2){0,20},0,0));
    fixed[1]=1;GeoPoint2 hp[]={{40,40},{60,40},{60,60},{40,60}};GeoLoop2View hole={hp,4};region.holes=&hole;region.hole_count=1;t=(WoodMember){.length=100,.size_a=20,.size_b=5};before=t;
    CHECK("pose-hole-complete-footprint",!wood_member_place_a0(&t,&f,&domain,NULL,(GeoPoint2){0,40},0,0)&&!memcmp(&t,&before,sizeof t));
    GeoPoint2 left[]={{0,0},{50,0},{50,100},{0,100}},right[]={{50,0},{100,0},{100,100},{50,100}};GeoRegionView parts[]={{{left,4},NULL,0},{{right,4},NULL,0}};GeoRegionSetView split={parts,2};
    CHECK("pose-one-complete-component",!wood_member_place_a0(&t,&f,&split,NULL,(GeoPoint2){0,20},0,0));return 0;
}
static WoodStopFace stop(int edge,GeoCoord at){return (WoodStopFace){WOOD_STOP_OUTLINE_EDGE,8,0,-1,edge,WOOD_STOP_FIXED,at,0,100};}
static int spans(void){
    GeoPoint2 points[]={{0,0},{100,0},{100,100},{0,100}};GeoRegionView region={{points,4},NULL,0};WoodStopFace stops[6]={stop(3,0),stop(1,100)};
    WoodMemberSpanFacts facts={{&region,1},NULL,0,stops,2};WoodMemberSpanRequest r={.cross_lo=10,.cross_hi=20};GeoCoord lo=-7,hi=-8;
    CHECK("span-positive",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_OK&&lo==0&&hi==100);
    r.contact=true;r.contact_lo=100;r.contact_hi=110;CHECK("contact-positive-overlap",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_OUTSIDE_CONTACT);
    r.contact=false;r.scoped=true;r.scope=(GeoRect2){0,0,90,100};CHECK("scope-never-clips-interval",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_NO_INTERVAL&&strstr(error_text,"完整跨距"));
    r.scope=(GeoRect2){0,11,100,100};CHECK("scope-full-width",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_NO_INTERVAL&&strstr(error_text,"完整寬度"));
    r.scoped=false;r.through=true;r.through_at=0;CHECK("through-closed-endpoint",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_OK&&lo==0&&hi==100);
    r.through_at=101;CHECK("through-outside",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_THROUGH_OUTSIDE);r.through=false;
    stops[2]=stop(7,0);facts.stop_count=3;CHECK("unique-start-stop",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_START_AMBIGUOUS);facts.stop_count=2;
    stops[0].fixity=0;CHECK("free-start-stop",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_FREE_EDGE_END);stops[0].fixity=1;
    facts.stops=stops+1;facts.stop_count=1;CHECK("unsupported-start",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_START_UNSUPPORTED);facts.stops=stops;
    CHECK("unsupported-end",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_END_UNSUPPORTED);
    facts.stop_count=3;stops[2]=stop(7,100);CHECK("ambiguous-end",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_END_AMBIGUOUS);facts.stop_count=2;stops[1].fixity=0;
    CHECK("free-end",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_FREE_EDGE_END);stops[1].fixity=1;
    GeoRect2 obstacle={40,0,60,100};facts.obstacles=&obstacle;facts.obstacle_count=1;stops[2]=stop(7,40);stops[3]=stop(8,60);facts.stop_count=4;
    CHECK("multiple-intervals-explicit",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_AMBIGUOUS&&strstr(error_text,"[0,40] [60,100]"));
    r.through=true;r.through_at=70;CHECK("through-selects-complete",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_OK&&lo==60&&hi==100);
    r.through=false;r.between=true;r.stops[0]=(WoodStopRef){0,-1,3,0};r.stops[1]=(WoodStopRef){0,-1,1,0};lo=-7;hi=-8;
    CHECK("between-cannot-cross-obstacle",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_BETWEEN_BLOCKED&&lo==-7&&hi==-8);
    facts.obstacle_count=0;CHECK("between-positive",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_OK&&lo==0&&hi==100);
    stops[0].fixity=0;CHECK("between-free-refused",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_FREE_EDGE_END);stops[0].fixity=1;stops[0].hi=15;
    CHECK("between-full-end-width",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_BETWEEN_BLOCKED&&strstr(error_text,"全寬"));stops[0].hi=100;
    stops[4]=stop(3,20);facts.stop_count=5;CHECK("between-pair-ambiguity",wood_member_resolve_span(&facts,&r,&lo,&hi,error_text,sizeof error_text)==WOOD_SPAN_BETWEEN_AMBIGUOUS);
    return 0;
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"dependencies"))return dependencies();if(!strcmp(argv[1],"anchors"))return anchors();if(!strcmp(argv[1],"candidates"))return candidates();
    if(!strcmp(argv[1],"roles"))return roles();if(!strcmp(argv[1],"boundary"))return boundary_roles();if(!strcmp(argv[1],"poses"))return poses();if(!strcmp(argv[1],"spans"))return spans();return 2;
}
