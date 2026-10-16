/* Public W API witness: real engineering resolution and public K geometry.
 * Facts below are explicit host inputs; no World or legacy include is linked. */
#include "section_profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x,n) do { if (!(x)) { fprintf(stderr,"ASSERT:%s error=%s\n",n,error); return 1; } } while (0)
static SectionProfileState state;
static EngineeringState engineering;
static WoodSectionProfileContext context;
static char error[512];
static GeoCoord parameter_value=33;
static bool parameter_available=true,host_available=true,host_derived=false;
static GeoFrame host_frame;
static WoodBoundaryRegion host_region;
static size_t dimension_calls,host_calls;
static EngTarget dimension_targets[32];
static EngDimensionSource dimension_sources[32];

static bool named_value(void *user,const char *name,GeoCoord *out)
{
    (void)user;
    if(!strcmp(name,"alpha"))*out=27;
    else if(!strcmp(name,"length"))*out=2400;
    else return false;
    return true;
}
static bool parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *message,size_t cap)
{
    (void)user;
    if(parameter_available&&ref.parameter_id==3&&ref.field_id==5){*out=parameter_value;return true;}
    snprintf(message,cap,"I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);return false;
}
static bool dimension(void *user,const EngDimensionSource *source,const EngTarget *target,GeoCoord *out)
{
    (void)user;
    if(dimension_calls<32){dimension_targets[dimension_calls]=*target;dimension_sources[dimension_calls]=*source;}
    ++dimension_calls;
    return wood_eng_resolve(&context.engineering,source,target,UINT32_MAX,0,out,NULL,0);
}
static bool live_host(void *user,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    (void)user;++host_calls;if(!host_available||id!=10)return false;
    *frame=host_frame;*region=host_region;*derived=host_derived;return true;
}
static void reset(void)
{
    memset(&state,0,sizeof state);memset(&engineering,0,sizeof engineering);memset(error,0,sizeof error);
    memset(dimension_targets,0,sizeof dimension_targets);memset(dimension_sources,0,sizeof dimension_sources);
    parameter_value=33;parameter_available=host_available=true;host_derived=false;dimension_calls=host_calls=0;
    host_frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    memset(&host_region,0,sizeof host_region);host_region.outline.count=4;
    host_region.outline.v[0]=(GeoPoint2){0,0};host_region.outline.v[1]=(GeoPoint2){100,0};
    host_region.outline.v[2]=(GeoPoint2){100,100};host_region.outline.v[3]=(GeoPoint2){0,100};
    context=(WoodSectionProfileContext){.state=&state,
        .engineering={.state=&engineering,.error=error,.error_capacity=sizeof error,.named_value=named_value,.parameter=parameter},
        .error=error,.error_capacity=sizeof error,.resolve_dimension=dimension,.live_host=live_host};
}
static bool record(const char *text,int kind)
{
    GeoJson json={0};if(!geo_json_parse(&json,text)){geo_json_free(&json);return false;}
    bool ok=kind==0?wood_sp_put_profile(&context,&json,0):kind==1?wood_sp_put_member(&context,&json,0):
        kind==2?wood_sp_put_run(&context,&json,0):wood_eng_publish_material(&context.engineering,&json,0,NULL);
    geo_json_free(&json);return ok;
}
static bool profile(uint32_t id)
{
    char text[256];snprintf(text,sizeof text,"{\"id\":%u,\"name\":\"square\",\"outline\":[[0,0],[1000,0],[1000,1000],[0,1000]]}",id);
    return record(text,0);
}
static bool panel(uint32_t id,GeoCoord width,const char *orientation,GeoCoord u,GeoCoord v)
{
    char text[384];snprintf(text,sizeof text,"{\"id\":%u,\"profileId\":1,\"kind\":\"panel\",\"panelSpec\":\"calcium-silicate-6\",\"width\":%lld,\"orientation\":\"%s\",\"u0\":%lld,\"v0\":%lld}",id,(long long)width,orientation,(long long)u,(long long)v);
    return record(text,1);
}
static bool run_record(uint32_t id,GeoCoord length,const char *placement)
{
    char text[2048];snprintf(text,sizeof text,"{\"id\":%u,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":%lld},\"placement\":%s}",id,(long long)length,placement);
    return record(text,2);
}
static bool rebuild(void){char message[512];return wood_sp_rebuild(&context,message,sizeof message);}
static bool rect_is(GeoRect2 r,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{return r.min_u==a&&r.min_v==b&&r.max_u==c&&r.max_v==d;}
static bool point_is(GeoPoint3 p,GeoCoord x,GeoCoord y,GeoCoord z)
{return p.x==x&&p.y==y&&p.z==z;}
static EngDimensionSource literal(GeoCoord value)
{EngDimensionSource s={0};s.kind=ENG_LITERAL;s.value=value;return s;}
static EngDimensionSource missing_parameter(uint32_t field)
{EngDimensionSource s={0};s.kind=ENG_PARAMETER;s.parameter=(GeoParameterRef){true,90,field};return s;}
static const char *material="{\"id\":\"t\",\"version\":1,\"kind\":\"timber\",\"name\":\"timber\",\"A\":27,\"B\":33}";
static const char *material_member="{\"id\":2,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"material\",\"id\":\"t\",\"version\":1,\"field\":\"A\"},\"B\":{\"kind\":\"material\",\"id\":\"t\",\"version\":1,\"field\":\"B\"},\"orientation\":\"A-v\",\"u0\":100,\"v0\":100}";
static const char *simple="{\"kind\":\"simple\",\"host\":{\"kind\":\"placement\",\"placementId\":10},\"dir\":\"+u\",\"p\":5,\"q\":6,\"up\":\"+Z\"}";

static int authoring(void)
{
    REQUIRE(!wood_sp_used(&context)&&profile(1),"profile-authoring");
    REQUIRE(wood_sp_used(&context)&&state.profile_count==1,"profile-used");
    REQUIRE(!strcmp(state.profiles[0].content,"{\"id\":1,\"name\":\"square\",\"outline\":[[0,0],[1000,0],[1000,1000],[0,1000]]}"),"profile-canonical");
    REQUIRE(!record("{\"id\":1,\"name\":\"bad\",\"outline\":[[0,0],[9,1],[10,10],[0,10]]}",0)&&strstr(error,"simple closed orthogonal polygon"),"profile-orthogonal");
    REQUIRE(!record("{\"id\":1,\"name\":\"bad\",\"outline\":[[0,0],[10,0],[10,10],[0,10]],\"holes\":[]}",0)&&strstr(error,"holes are unsupported"),"profile-no-holes");
    REQUIRE(!record("{\"id\":1,\"name\":\"bad\",\"outline\":[[0,0],[1.5,0],[1,1],[0,1]]}",0),"profile-no-rounding");
    REQUIRE(panel(1,914,"thickness-v",0,0)&&rebuild(),"panel-width-914");
    REQUIRE(rect_is(state.members[0].rect,0,0,914,6)&&state.members[0].a==914&&state.members[0].b==6,"panel-fixed-thickness");
    ProfileMember saved=state.members[0];
    REQUIRE(!panel(1,915,"thickness-v",0,0),"panel-strict-width");
    REQUIRE(strstr(error,"V_PANEL_WIDTH I46: member 1 expected integer 1 <= width < 915")&&!memcmp(&saved,&state.members[0],sizeof saved),"panel-width-preserved");
    REQUIRE(!panel(1,0,"thickness-v",0,0)&&!panel(1,-1,"thickness-v",0,0),"panel-positive");
    REQUIRE(panel(1,1,"thickness-u",0,0)&&rebuild()&&rect_is(state.members[0].rect,0,0,6,1),"panel-second-orientation");
    REQUIRE(!panel(1,1,"other",0,0),"panel-orientation");
    REQUIRE(!record("{\"id\":1,\"profileId\":1,\"kind\":\"panel\",\"panelSpec\":\"calcium-silicate-6\",\"width\":1,\"thickness\":9,\"orientation\":\"thickness-v\",\"u0\":0,\"v0\":0}",1),"panel-no-thickness-override");
    REQUIRE(record(material,3)&&record(material_member,1)&&rebuild(),"material-member-authoring");
    REQUIRE(state.members[1].a_source.field==ENG_A&&state.members[1].b_source.field==ENG_B&&rect_is(state.members[1].rect,100,100,133,127),"material-rotated-identity");
    REQUIRE(!record("{\"id\":2,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"material\",\"id\":\"t\",\"version\":1,\"field\":\"B\"},\"B\":{\"kind\":\"literal\",\"value\":33},\"orientation\":\"A-v\",\"u0\":0,\"v0\":20}",1),"material-source-identity");
    REQUIRE(!strcmp(error,"D36: material source must retain matching A/B field identity"),"material-source-error");
    REQUIRE(!record("{\"id\":1,\"profileId\":1,\"length\":{\"kind\":\"material\",\"id\":\"t\",\"version\":1,\"field\":\"A\"},\"placement\":null}",2)&&!strcmp(error,"D36/D37: unsupported dimension source"),"run-material-source-refusal");
    return 0;
}

static int geometry(void)
{
    WoodBoundaryLoop notch={.v={{0,0},{100,0},{100,100},{60,100},{60,40},{40,40},{40,100},{0,100}},.count=8};
    GeoRect2 out[SP_OUTSIDE_MAX],query={40,50,60,70};
    REQUIRE(wood_sp_outside_regions(&notch,&query,out)==1&&rect_is(out[0],40,50,60,70),"notch-is-outside");
    query=(GeoRect2){0,50,40,70};REQUIRE(wood_sp_outside_regions(&notch,&query,out)==0,"closed-boundary-contact");
    query=(GeoRect2){-10,-10,110,110};
    const GeoRect2 expected[]={{-10,-10,110,0},{-10,0,0,40},{100,0,110,40},{-10,40,0,100},{40,40,60,100},{100,40,110,100},{-10,100,110,110}};
    size_t count=wood_sp_outside_regions(&notch,&query,out);
    REQUIRE(count==7&&!memcmp(out,expected,sizeof expected),"complement-exact-order");
    GeoLoop2View view={notch.v,notch.count};size_t total=999;
    REQUIRE(geo_loop_rect_complement(&view,&query,out,7,&total)==GEO_GEOMETRY_OK&&total==7,"complement-capacity-exact");
    total=999;REQUIRE(geo_loop_rect_complement(&view,&query,out,6,&total)==GEO_GEOMETRY_CAPACITY&&total==0,"complement-capacity-no-truncation");
    REQUIRE(geo_loop_rect_complement(&view,&query,NULL,0,&total)==GEO_GEOMETRY_CAPACITY&&total==0,"complement-zero-capacity");
    ProfileMember a={.profile_id=1,.rect={0,0,10,10},.resolved=true},b={.profile_id=1,.rect={10,0,20,10},.resolved=true};
    GeoRect2 overlap={0};REQUIRE(!wood_sp_intersection(&a,&b,&overlap),"overlap-edge-contact");
    b.rect=(GeoRect2){10,10,20,20};REQUIRE(!wood_sp_intersection(&a,&b,&overlap),"overlap-point-contact");
    b.rect=(GeoRect2){9,8,20,20};REQUIRE(wood_sp_intersection(&a,&b,&overlap)&&rect_is(overlap,9,8,10,10),"overlap-positive-area");
    b.profile_id=2;REQUIRE(!wood_sp_intersection(&a,&b,&overlap),"overlap-profile-isolation");
    b.profile_id=1;b.resolved=false;REQUIRE(!wood_sp_intersection(&a,&b,&overlap),"overlap-unresolved");
    return 0;
}

static int sources(void)
{
    REQUIRE(profile(1)&&record(material,3),"sources-seed");
    REQUIRE(record("{\"id\":1,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"spec\",\"name\":\"alpha\"},\"B\":{\"kind\":\"parameter\",\"parameterId\":3,\"fieldId\":5},\"orientation\":\"A-u\",\"u0\":0,\"v0\":0}",1)&&record(material_member,1),"sources-authoring");
    strcpy(error,"unrelated earlier dependency diagnostic");REQUIRE(rebuild(),"sources-selected-closure");
    REQUIRE(dimension_calls==4&&dimension_sources[0].kind==ENG_SPEC&&dimension_sources[1].parameter.parameter_id==3&&dimension_sources[1].parameter.field_id==5,"sources-selected-identities");
    for(size_t i=0;i<4;++i)REQUIRE(dimension_targets[i].kind==1&&dimension_targets[i].id==0&&dimension_targets[i].axis==0&&dimension_targets[i].field==(int)(i%2),"sources-target-fields");
    REQUIRE(rect_is(state.members[0].rect,0,0,27,33)&&rect_is(state.members[1].rect,100,100,133,127),"sources-independent-dimensions");
    parameter_value=35;REQUIRE(rebuild()&&rect_is(state.members[0].rect,0,0,27,35),"sources-recompute-fixed-anchor");
    parameter_available=false;REQUIRE(!rebuild()&&!state.members[0].resolved&&state.members[1].resolved,"sources-error-isolation");
    REQUIRE(!strcmp(error,"I38 MISSING: parameter 3 field 5")&&!strcmp(state.members[0].source_error[1],error)&&!state.members[0].source_error[0][0],"sources-exact-error");
    REQUIRE(state.members[0].a==27&&state.members[0].b==35,"sources-failed-value-cache");
    parameter_available=true;parameter_value=0;REQUIRE(!rebuild()&&strstr(error,"positive/nonnegative integer mm range"),"sources-positive");
    return 0;
}

static int placement(void)
{
    REQUIRE(run_record(1,2400,simple),"placement-authoring");ProfileRun *r=wood_sp_run(&context,1);
    REQUIRE(wood_sp_resolve_placement(&context,r),"placement-live-resolve");
    REQUIRE(point_is(r->frame.origin,15,26,30)&&geo_vector_equal(r->frame.normal,(GeoVector3){1,0,0})&&geo_vector_equal(r->frame.axis_v,(GeoVector3){0,0,-1})&&geo_vector_equal(r->frame.axis_u,(GeoVector3){0,-1,0}),"placement-frame-signs");
    REQUIRE(point_is(wood_sp_point(r,2,3,4),19,24,27),"placement-world-point");
    const GeoVector3 normals[]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0}};
    for(int dir=0;dir<4;++dir){r->dir=dir;REQUIRE(wood_sp_resolve_placement(&context,r)&&geo_frame_is_valid(&r->frame)&&geo_vector_equal(r->frame.normal,normals[dir]),"placement-four-directions");}
    r->dir=0;r->p=100;r->q=100;REQUIRE(wood_sp_resolve_placement(&context,r),"placement-closed-host-edge");
    r->p=101;REQUIRE(!wood_sp_resolve_placement(&context,r)&&!strcmp(r->placement_error,"I48: p,q outside closed host range;"),"placement-host-range");
    r->p=5;r->q=6;r->up=(GeoVector3){1,0,0};REQUIRE(!wood_sp_resolve_placement(&context,r)&&strstr(r->placement_error,"up must be perpendicular"),"placement-up-perpendicular");r->up=(GeoVector3){0,0,1};
    host_frame.origin.x=GEO_COORD_LIMIT;r->p=1;REQUIRE(!wood_sp_resolve_placement(&context,r)&&strstr(r->placement_error,"origin exceeds D1"),"placement-origin-range");host_frame.origin.x=10;r->p=5;
    GeoFrame frame;WoodBoundaryRegion region;host_derived=true;
    REQUIRE(!wood_sp_host(&context,r,&frame,&region)&&!strcmp(error,"D4: derived placements cannot host D38 positioning"),"placement-derived-host");
    REQUIRE(!wood_sp_resolve_placement(&context,r)&&!strcmp(r->placement_error,"I48: live host 10 is missing or invalid"),"placement-derived-cache-error");host_derived=false;
    host_available=false;REQUIRE(!wood_sp_resolve_placement(&context,r),"placement-missing-live-host");
    const char *copied="{\"kind\":\"simple\",\"host\":{\"kind\":\"space-wall-values\",\"sourceDescription\":\"saved wall\",\"frame\":{\"origin\":[100,200,300],\"U\":\"+Y\",\"V\":\"+Z\",\"N\":\"+X\"},\"region\":{\"outline\":[[0,0],[100,0],[100,100],[0,100]],\"holes\":[]}},\"dir\":\"+v\",\"p\":5,\"q\":6,\"up\":\"+X\"}";
    REQUIRE(run_record(2,100,copied),"placement-copied-authoring");r=wood_sp_run(&context,2);size_t calls=host_calls;
    REQUIRE(wood_sp_resolve_placement(&context,r)&&host_calls==calls&&point_is(r->frame.origin,100,205,306),"placement-copied-independent");
    REQUIRE(geo_vector_equal(r->frame.normal,(GeoVector3){0,0,1})&&geo_vector_equal(r->frame.axis_v,(GeoVector3){-1,0,0})&&geo_vector_equal(r->frame.axis_u,(GeoVector3){0,1,0}),"placement-copied-frame");
    r->host_region.hole_count=GEO_REGION_MAX_HOLES+1;
    REQUIRE(!wood_sp_resolve_placement(&context,r)&&strstr(r->placement_error,"outside closed host range"),"placement-copied-hole-capacity");
    REQUIRE(!run_record(3,1,"{\"kind\":\"advanced\",\"origin\":[0,0,0],\"N\":\"+X\",\"V\":\"+X\"}"),"placement-advanced-orthogonal");
    return 0;
}

static int conversion(void)
{
    ProfileRun r={.id=7,.placed=true,.frame={{15,26,30},{0,-1,0},{0,0,-1},{1,0,0}}};
    int dir=99;GeoCoord p=99,q=99;GeoVector3 up={9,9,9};
    REQUIRE(wood_sp_conversion_fields(&context,&r,&host_frame,&host_region,&dir,&p,&q,&up)&&dir==0&&p==5&&q==6&&geo_vector_equal(up,(GeoVector3){0,0,1}),"conversion-exact-fields");
    ProfileRun bad=r;bad.frame.origin.z=31;dir=99;p=q=99;up=(GeoVector3){9,9,9};
    REQUIRE(!wood_sp_conversion_fields(&context,&bad,&host_frame,&host_region,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: origin not in host plane;"),"conversion-plane");
    REQUIRE(dir==99&&p==99&&q==99&&up.x==9,"conversion-failed-output");
    WoodBoundaryRegion excessive=host_region;excessive.hole_count=GEO_REGION_MAX_HOLES+1;
    REQUIRE(!wood_sp_conversion_fields(&context,&r,&host_frame,&excessive,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: p,q outside host range;"),"conversion-hole-capacity");
    bad=r;bad.frame.normal=(GeoVector3){0,0,1};bad.frame.axis_v=(GeoVector3){0,1,0};
    REQUIRE(!wood_sp_conversion_fields(&context,&bad,&host_frame,&host_region,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: N not a host-plane direction;"),"conversion-direction");
    bad=r;bad.frame.origin.x=111;
    REQUIRE(!wood_sp_conversion_fields(&context,&bad,&host_frame,&host_region,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: p,q outside host range;"),"conversion-range");
    bad=r;bad.frame.axis_v=(GeoVector3){0,0,2};
    REQUIRE(!wood_sp_conversion_fields(&context,&bad,&host_frame,&host_region,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: V has no legal up;"),"conversion-up");
    bad=r;bad.frame.origin=(GeoPoint3){111,20,31};bad.frame.normal=bad.frame.axis_v=(GeoVector3){0,0,1};
    REQUIRE(!wood_sp_conversion_fields(&context,&bad,&host_frame,&host_region,&dir,&p,&q,&up)&&!strcmp(error,"I48 conversion: origin not in host plane; N not a host-plane direction; p,q outside host range; V has no legal up;"),"conversion-all-reasons");
    ProfileRun out;REQUIRE(!wood_sp_begin_conversion(&context,7,true,&out)&&!strcmp(error,"I48: conversion requires a placed run"),"conversion-missing-run");
    state.runs[0]=r;state.run_count=1;REQUIRE(!wood_sp_begin_conversion(&context,7,false,&out)&&!strcmp(error,"I48: run is already advanced"),"conversion-already-advanced");
    REQUIRE(wood_sp_begin_conversion(&context,7,true,&out)&&!memcmp(&r,&state.runs[0],sizeof r),"conversion-original-unchanged");
    REQUIRE(run_record(7,20,simple),"conversion-simple-authoring");ProfileRun saved=*wood_sp_run(&context,7);
    REQUIRE(!wood_sp_begin_conversion(&context,7,true,&out)&&!strcmp(error,"I48: run is already simple"),"conversion-already-simple");
    REQUIRE(wood_sp_begin_conversion(&context,7,false,&out)&&point_is(out.frame.origin,15,26,30)&&!memcmp(&saved,wood_sp_run(&context,7),sizeof saved),"conversion-simple-frame-copy");
    return 0;
}

static int diagnostics(void)
{
    REQUIRE(profile(1),"diagnostics-profile");
    ProfileMember *m=&state.members[0];m->id=7;m->profile_id=99;m->a_source=missing_parameter(1);m->b_source=missing_parameter(2);
    m->a=17;m->b=19;m->rect=(GeoRect2){5,6,22,25};m->resolved=m->outside=m->range_error=true;
    ProfileMember *later=&state.members[1];later->id=8;later->profile_id=1;later->panel=true;later->width=8;later->u0=GEO_COORD_LIMIT-4;state.member_count=2;
    ProfileRun *run=&state.runs[0];run->id=9;run->profile_id=98;run->length_source=missing_parameter(3);run->length=23;run->resolved=true;run->simple=true;run->host_id=77;state.run_count=1;
    REQUIRE(!rebuild()&&!strcmp(error,"I49: member 7 references missing profile 99"),"diagnostics-first-error");
    REQUIRE(!m->resolved&&m->missing_profile&&!m->range_error&&!m->outside&&rect_is(m->rect,5,6,22,25),"diagnostics-source-cache");
    REQUIRE(!strcmp(m->source_error[0],"I38 MISSING: parameter 90 field 1")&&!strcmp(m->source_error[1],"I38 MISSING: parameter 90 field 2"),"diagnostics-both-sources");
    REQUIRE(later->resolved&&later->range_error&&later->outside,"diagnostics-later-member-caches");
    REQUIRE(run->missing_profile&&!run->resolved&&!run->length_resolved&&!run->placement_resolved&&run->length==23&&!strcmp(run->length_error,"I47: I38 MISSING: parameter 90 field 3")&&!strcmp(run->placement_error,"I48: live host 77 is missing or invalid"),"diagnostics-run-caches");
    m->profile_id=1;m->u0=m->v0=0;m->a_source=literal(10);m->b_source=literal(20);state.member_count=1;state.run_count=0;
    REQUIRE(rebuild()&&m->resolved&&!m->missing_profile&&!m->outside&&!m->range_error&&!m->source_error[0][0]&&!m->source_error[1][0]&&rect_is(m->rect,0,0,10,20),"diagnostics-cache-reset");
    return 0;
}

static int runs(void)
{
    REQUIRE(profile(1)&&run_record(1,2400,"null")&&rebuild(),"run-long-unplaced");ProfileRun *r=wood_sp_run(&context,1);
    REQUIRE(!r->placed&&r->resolved&&r->length==2400&&r->placement_resolved&&point_is(wood_sp_point(r,2,3,2400),2,3,2400),"run-unplaced-local");
    REQUIRE(run_record(1,1,"null")&&rebuild()&&r->length==1,"run-minimum-length");
    REQUIRE(run_record(1,0,"null")&&!rebuild()&&!r->length_resolved&&!r->resolved&&strstr(r->length_error,"I47: I35: effective dimension violates"),"run-zero-refused");
    REQUIRE(run_record(1,-1,"null")&&!rebuild(),"run-negative-refused");
    REQUIRE(run_record(1,GEO_COORD_LIMIT,"null")&&rebuild()&&r->length==GEO_COORD_LIMIT,"run-upper-length");
    REQUIRE(!run_record(1,GEO_COORD_LIMIT+1,"null"),"run-input-range");
    char place[256];snprintf(place,sizeof place,"{\"kind\":\"advanced\",\"origin\":[%lld,0,0],\"N\":\"+X\",\"V\":\"+Y\"}",(long long)GEO_COORD_LIMIT-50);
    REQUIRE(run_record(1,60,place)&&!rebuild(),"run-vertex-range-refused");
    REQUIRE(r->range_error&&!r->resolved&&r->length_resolved&&r->placement_resolved,"run-range-cache");
    REQUIRE(strstr(error,"I47/I48/D1: run 1 generated vertex")!=NULL,"run-range-error");
    REQUIRE(run_record(1,40,place)&&rebuild()&&!r->range_error&&r->resolved,"run-range-recovery");
    return 0;
}

static int capacity(void)
{
    for(uint32_t i=0;i<SP_PROFILE_MAX;++i)REQUIRE(profile(i),"capacity-profile-full");
    REQUIRE(state.profile_count==SP_PROFILE_MAX&&profile(0)&&state.profile_count==SP_PROFILE_MAX,"capacity-profile-replace");
    SectionProfileState *before=malloc(sizeof *before);REQUIRE(before,"capacity-snapshot");*before=state;
    REQUIRE(!profile(SP_PROFILE_MAX)&&!memcmp(before,&state,sizeof state)&&!strcmp(error,"I51 CAPACITY: profile limit is 16"),"capacity-profile-refusal");
    for(uint32_t i=0;i<SP_MEMBER_MAX;++i)REQUIRE(panel(i,1,"thickness-v",i,0),"capacity-member-full");
    REQUIRE(panel(0,2,"thickness-v",0,0)&&state.member_count==SP_MEMBER_MAX,"capacity-member-replace");*before=state;
    REQUIRE(!panel(SP_MEMBER_MAX,1,"thickness-v",0,0)&&!memcmp(before,&state,sizeof state),"capacity-member-refusal");
    for(uint32_t i=0;i<SP_RUN_MAX;++i)REQUIRE(run_record(i,1,"null"),"capacity-run-full");
    REQUIRE(run_record(0,2,"null")&&state.run_count==SP_RUN_MAX,"capacity-run-replace");*before=state;
    REQUIRE(!run_record(SP_RUN_MAX,1,"null")&&!memcmp(before,&state,sizeof state),"capacity-run-refusal");
    REQUIRE(wood_sp_remove(&context,"profile",0)&&state.profile_count==SP_PROFILE_MAX-1&&state.profiles[0].id==1&&state.profiles[SP_PROFILE_MAX-2].id==SP_PROFILE_MAX-1,"capacity-profile-compaction");
    SectionProfile zero_profile={0};REQUIRE(!memcmp(&state.profiles[SP_PROFILE_MAX-1],&zero_profile,sizeof zero_profile),"capacity-tail-zero");
    REQUIRE(wood_sp_remove(&context,"member",0)&&state.member_count==SP_MEMBER_MAX-1&&state.members[0].id==1,"capacity-member-compaction");
    ProfileMember zero_member={0};REQUIRE(!memcmp(&state.members[SP_MEMBER_MAX-1],&zero_member,sizeof zero_member),"capacity-member-tail");
    REQUIRE(wood_sp_remove(&context,"run",0)&&state.run_count==SP_RUN_MAX-1&&state.runs[0].id==1,"capacity-run-compaction");
    ProfileRun zero_run={0};REQUIRE(!memcmp(&state.runs[SP_RUN_MAX-1],&zero_run,sizeof zero_run),"capacity-run-tail");
    *before=state;REQUIRE(!wood_sp_remove(&context,"run",0)&&!memcmp(before,&state,sizeof state)&&!strcmp(error,"I49: deleted run id 0 does not exist"),"capacity-delete-missing");
    free(before);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;reset();
    if(!strcmp(argv[1],"authoring"))return authoring();
    if(!strcmp(argv[1],"geometry"))return geometry();
    if(!strcmp(argv[1],"sources"))return sources();
    if(!strcmp(argv[1],"placement"))return placement();
    if(!strcmp(argv[1],"conversion"))return conversion();
    if(!strcmp(argv[1],"diagnostics"))return diagnostics();
    if(!strcmp(argv[1],"runs"))return runs();
    if(!strcmp(argv[1],"capacity"))return capacity();
    return 2;
}
