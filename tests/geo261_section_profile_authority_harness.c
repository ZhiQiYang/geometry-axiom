/* Returned-value controls use the real K evaluation first, then substitute its
 * public result at W's call boundary. Stored authored data and K cached values
 * remain untouched. A second set of linked W mutants must fail named checks. */
#define main legacy_section_profile_main
#include "geo261_section_profile_sources_harness.c"
#undef main

enum { AUTH_NONE,AUTH_MEMBER,AUTH_RUN,AUTH_PROFILE,AUTH_FRAME,AUTH_HOST_REGION,
    AUTH_PAIR_FIRST,AUTH_PAIR_SECOND,AUTH_MALFORMED,AUTH_STATUS,AUTH_SCHEMA,AUTH_IDENTITY,AUTH_COPIED };
static int authority_mode,authority_kind;
static uint32_t authority_id;
static char authority_content[SP_RUN_RECORD_MAX];
static GeoPoint2 authority_points[4];
static GeoRegionView authority_region;
static Fixture *authority_fixture;
static int authority_hits;
static bool unchanged_cache_at_return;

static bool pair_active(GeoEvalContext *graph)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;uint32_t a,b;
        if(geo_eval_node_at(graph,i,&n)&&n.source.provider==TOKEN&&n.state==GEO_NODE_ACTIVE&&wood_sp_pair_source_decode(&n.source,&a,&b))return true;}
    return false;
}
GeoSourceStatus geo261_sp_get(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);WoodSectionProfileSourceKind kind;uint32_t id;
    if(status!=GEO_SOURCE_OK||ref.provider!=TOKEN||!wood_sp_source_decode(&ref,&kind,&id))return status;
    bool definition=(kind==authority_kind&&id==authority_id);
    if(definition&&(authority_mode==AUTH_MEMBER||authority_mode==AUTH_RUN||authority_mode==AUTH_PROFILE||authority_mode==AUTH_COPIED||authority_mode==AUTH_IDENTITY)){
        ++authority_hits;out->as.definition.content=authority_content;out->as.definition.content_size=strlen(authority_content);
    }else if(definition&&authority_mode==AUTH_MALFORMED){
        ++authority_hits;out->as.definition.content="{";out->as.definition.content_size=1;
    }else if(definition&&authority_mode==AUTH_STATUS){++authority_hits;return GEO_SOURCE_FAILED;
    }else if(definition&&authority_mode==AUTH_SCHEMA){++authority_hits;out->as.definition.schema="wrong.section-profile.schema/1";
    }else if(authority_mode==AUTH_FRAME&&kind==WOOD_SP_SOURCE_RUN_FRAME&&id==5){
        ++authority_hits;unchanged_cache_at_return=authority_fixture->state.runs[0].frame.origin.x==15;
        out->as.frame.origin.x=GEO_COORD_LIMIT-50;
    }else if(authority_mode==AUTH_HOST_REGION&&kind==WOOD_SP_SOURCE_HOST_REGION&&id==10){
        ++authority_hits;unchanged_cache_at_return=authority_fixture->host_region.outline.v[2].u==100;
        out->as.regions=(GeoRegionSetView){&authority_region,1};
    }else if(kind==WOOD_SP_SOURCE_MEMBER_REGION&&pair_active(graph)&&
             ((authority_mode==AUTH_PAIR_FIRST&&id==3)||(authority_mode==AUTH_PAIR_SECOND&&id==4))){
        ++authority_hits;unchanged_cache_at_return=authority_fixture->state.members[0].rect.max_u==37&&authority_fixture->state.members[1].rect.min_u==60;
        out->as.regions=(GeoRegionSetView){&authority_region,1};
    }
    return status;
}
static bool canonical(const char *text)
{
    GeoJson j={0};if(!geo_json_parse(&j,text))return false;
    bool ok=geo_json_canonical(&j,0,authority_content,sizeof authority_content);geo_json_free(&j);return ok;
}
static void rectangle(GeoCoord u,GeoCoord v,GeoCoord max_u,GeoCoord max_v)
{
    authority_points[0]=(GeoPoint2){u,v};authority_points[1]=(GeoPoint2){max_u,v};authority_points[2]=(GeoPoint2){max_u,max_v};authority_points[3]=(GeoPoint2){u,max_v};
    authority_region=(GeoRegionView){{authority_points,4},NULL,0};
}
static Fixture *authority_seed(int mode,int kind,uint32_t id)
{
    authority_mode=mode;authority_kind=kind;authority_id=id;authority_hits=0;unchanged_cache_at_return=false;
    Fixture *f=fixture();if(!f||!seed(f)||!connect(f)){dispose(f,false);return NULL;}authority_fixture=f;return f;
}
static bool pair_node(Fixture *f,GeoSourceNodeView *out,size_t *index)
{
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;uint32_t a,b;
        if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==TOKEN&&wood_sp_pair_source_decode(&n.source,&a,&b)&&a==3&&b==4){if(out)*out=n;if(index)*index=i;return true;}}
    return false;
}
static bool pair_edge(Fixture *f,int kind,uint32_t id)
{
    size_t consumer,source;if(!pair_node(f,NULL,&consumer)||!node(f,kind,id,NULL,&source))return false;
    for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;geo_eval_edge_at(f->graph,i,&e);if(e.consumer==consumer&&e.source==source&&e.kind==GEO_DEPENDENCY_VALUE_REQUIRED)return true;}
    return false;
}
static int member_authority(void)
{
    Fixture *f=authority_seed(AUTH_MEMBER,WOOD_SP_SOURCE_MEMBER_DEFINITION,3);CHECK("member-authority-setup",f&&canonical("{\"id\":3,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"literal\",\"value\":12},\"B\":{\"kind\":\"literal\",\"value\":8},\"orientation\":\"A-v\",\"u0\":31,\"v0\":44}"));
    char before[SP_RECORD_MAX];strcpy(before,f->state.members[0].content);
    CHECK("member-authority-rebuild",rebuild(f));ProfileMember *m=&f->state.members[0];
    CHECK("member-definition-controls-geometry",authority_hits>0&&m->a==12&&m->b==8&&m->rect.min_u==31&&m->rect.min_v==44&&m->rect.max_u==39&&m->rect.max_v==56);
    CHECK("member-raw-authoring-preserved",m->u0==10&&m->v0==20&&!m->rotated&&m->a_source.kind==ENG_PARAMETER&&!strcmp(before,m->content));
    GeoSourceValue v;CHECK("member-authoritative-region",value(f,WOOD_SP_SOURCE_MEMBER_REGION,3,&v)&&v.as.regions.regions[0].outline.v[2].u==39);
    dispose(f,false);return 0;
}
static int run_authority(bool copied)
{
    Fixture *f=authority_seed(copied?AUTH_COPIED:AUTH_RUN,WOOD_SP_SOURCE_RUN_DEFINITION,5);CHECK("run-authority-setup",f);
    const char *definition=copied?
        "{\"id\":5,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":25},\"placement\":{\"kind\":\"simple\",\"host\":{\"kind\":\"space-wall-values\",\"sourceDescription\":\"copied authority provenance\",\"frame\":{\"origin\":[10,20,30],\"U\":\"+X\",\"V\":\"+Y\",\"N\":\"+Z\"},\"region\":{\"outline\":[[0,0],[100,0],[100,100],[0,100]],\"holes\":[]}},\"dir\":\"+u\",\"p\":5,\"q\":7,\"up\":\"+Z\"}}":
        "{\"id\":5,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":25},\"placement\":{\"kind\":\"advanced\",\"origin\":[100,200,300],\"N\":\"+Z\",\"V\":\"+Y\"}}";
    CHECK("run-authority-canonical",canonical(definition));char before[SP_RUN_RECORD_MAX];strcpy(before,f->state.runs[0].content);f->fail_host=true;
    CHECK("run-definition-controls-length-placement",rebuild(f)&&authority_hits>0&&f->state.runs[0].length==25&&f->host_calls==0);
    CHECK("run-raw-authoring-preserved",f->state.runs[0].length_source.value==120&&f->state.runs[0].simple&&!f->state.runs[0].copied_host&&!strcmp(before,f->state.runs[0].content));
    GeoSourceValue v;CHECK("run-returned-frame-geometry",value(f,WOOD_SP_SOURCE_RUN_FRAME,5,&v)&&v.as.frame.origin.x==(copied?15:100)&&v.as.frame.origin.y==(copied?27:200)&&v.as.frame.origin.z==(copied?30:300));
    CHECK("copied-or-advanced-no-live-host-edge",!node(f,WOOD_SP_SOURCE_HOST_FRAME,10,NULL,NULL)&&!node(f,WOOD_SP_SOURCE_HOST_REGION,10,NULL,NULL));
    dispose(f,true);
    if(copied){
        authority_mode=AUTH_NONE;f=fixture();CHECK("copied-authored-setup",f&&seed(f)&&record(f,2,definition)&&connect(f));f->fail_host=true;
        CHECK("copied-authored-complete",rebuild(f)&&wood_sp_sources_complete(f->sources)&&geo_eval_seal(f->graph));
        CHECK("copied-source-description-retained",value(f,WOOD_SP_SOURCE_RUN_DEFINITION,5,&v)&&v.as.definition.content_size==strlen(f->state.runs[0].content)&&
            !memcmp(v.as.definition.content,f->state.runs[0].content,v.as.definition.content_size)&&strstr((const char *)v.as.definition.content,"copied authority provenance"));
        CHECK("copied-authored-no-live-edge",f->host_calls==0&&!node(f,WOOD_SP_SOURCE_HOST_FRAME,10,NULL,NULL));dispose(f,false);
    }
    return 0;
}
static int profile_authority(void)
{
    Fixture *f=authority_seed(AUTH_PROFILE,WOOD_SP_SOURCE_PROFILE_DEFINITION,1);CHECK("profile-authority-setup",f&&canonical("{\"id\":1,\"name\":\"returned profile\",\"outline\":[[0,0],[25,0],[25,25],[0,25]]}"));
    CHECK("profile-definition-controls-containment",!rebuild(f)&&authority_hits>0&&!strcmp(f->error,"V_PROFILE_OUTSIDE I44: member 3 profile 1 rectangle is not contained")&&f->state.members[0].outside&&f->state.members[1].outside);
    CHECK("profile-raw-outline-preserved",f->state.profiles[0].outline.v[2].u==100&&!strcmp(f->state.profiles[0].name,"shape"));
    GeoSourceValue v;CHECK("run-region-consumes-returned-profile",value(f,WOOD_SP_SOURCE_RUN_REGION,5,&v)&&v.as.regions.regions[0].outline.v[2].u==25);
    dispose(f,false);return 0;
}
static int geometry_authority(bool frame)
{
    Fixture *f=authority_seed(frame?AUTH_FRAME:AUTH_HOST_REGION,0,0);CHECK("geometry-authority-setup",f);rectangle(0,0,4,4);
    bool ok=rebuild(f);
    if(frame){CHECK("run-frame-return-controls-range",!ok&&authority_hits>0&&unchanged_cache_at_return&&f->state.runs[0].range_error&&!f->state.runs[0].resolved&&strstr(f->error,"I47/I48/D1: run 5 generated vertex"));}
    else{CHECK("host-region-return-controls-placement",!ok&&authority_hits>0&&unchanged_cache_at_return&&!f->state.runs[0].placement_resolved&&!strcmp(f->error,"I48: p,q outside closed host range;"));}
    dispose(f,true);return 0;
}
static int geometry_status(bool frame)
{
    Fixture *f=authority_seed(AUTH_STATUS,frame?WOOD_SP_SOURCE_RUN_FRAME:WOOD_SP_SOURCE_HOST_REGION,frame?5:10);CHECK("geometry-status-setup",f);
    CHECK("geometry-status-refused",!rebuild(f)&&authority_hits>0&&!f->state.runs[0].resolved&&!f->state.runs[0].placement_resolved&&
        !strcmp(f->error,frame?"I48: run frame unavailable":"I48: live host 10 is missing or invalid"));
    GeoSourceNodeView n;CHECK("geometry-status-no-run-region",node(f,WOOD_SP_SOURCE_RUN_REGION,5,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value);
    dispose(f,false);return 0;
}
static int pair_authority(int mode)
{
    Fixture *f=authority_seed(mode,0,0);CHECK("pair-authority-setup",f);
    if(mode==AUTH_PAIR_FIRST)rectangle(65,20,75,30);else rectangle(15,25,25,40);
    bool ok=rebuild(f);GeoSourceNodeView n;
    if(mode==AUTH_NONE)CHECK("pair-successful-no-overlap",ok);
    else if(mode==AUTH_PAIR_FIRST)CHECK("pair-first-return-controls-overlap",!ok&&authority_hits>0&&unchanged_cache_at_return&&!strcmp(f->error,"V_PROFILE_OVERLAP I45: members 3,4 intersection [65,75]x[20,26]"));
    else CHECK("pair-second-return-controls-overlap",!ok&&authority_hits>0&&unchanged_cache_at_return&&!strcmp(f->error,"V_PROFILE_OVERLAP I45: members 3,4 intersection [15,25]x[25,40]"));
    CHECK("pair-check-node",pair_node(f,&n,NULL)&&n.state==GEO_NODE_VALID&&n.value&&n.value->kind==GEO_SOURCE_REGION_SET&&n.value->as.regions.count==(mode==AUTH_NONE?0:1));
    CHECK("pair-first-member-edge",pair_edge(f,WOOD_SP_SOURCE_MEMBER_REGION,3));
    CHECK("pair-second-member-edge",pair_edge(f,WOOD_SP_SOURCE_MEMBER_REGION,4));
    CHECK("pair-raw-caches-preserved",f->state.members[0].rect.max_u==37&&f->state.members[1].rect.min_u==60);
    WoodSectionProfilePairKey key;uint32_t a=0,b=0;GeoSourceRef ref=wood_sp_pair_source_ref(TOKEN,UINT32_MAX,0,&key);
    CHECK("pair-exact-nine-byte-identity",ref.key_size==9&&wood_sp_pair_source_decode(&ref,&a,&b)&&a==UINT32_MAX&&b==0);
    dispose(f,false);return 0;
}
static int definition_failure(int mode,int kind,uint32_t id)
{
    Fixture *f=authority_seed(mode,kind,id);CHECK("definition-failure-setup",f);
    if(mode==AUTH_IDENTITY)CHECK("definition-wrong-id-setup",canonical(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION?
        "{\"id\":88,\"name\":\"wrong identity\",\"outline\":[[0,0],[100,0],[100,100],[0,100]]}":kind==WOOD_SP_SOURCE_MEMBER_DEFINITION?
        "{\"id\":88,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"literal\",\"value\":27},\"B\":{\"kind\":\"literal\",\"value\":33},\"orientation\":\"A-u\",\"u0\":10,\"v0\":20}":
        "{\"id\":88,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":120},\"placement\":null}"));
    char expected[192];snprintf(expected,sizeof expected,mode==AUTH_STATUS?"I51: section profile definition kind %u id %u unavailable":"I51: invalid section profile definition kind %u id %u",(unsigned)kind,id);
    bool ok=id==99?wood_sp_sources_complete(f->sources):rebuild(f);
    if(mode==AUTH_STATUS)CHECK("definition-status-refused",!ok&&authority_hits>0&&!strcmp(f->error,expected));
    else CHECK("definition-bytes-refused",!ok&&authority_hits>0&&!strcmp(f->error,expected));
    if(id!=99){GeoSourceNodeView n;int root=kind==WOOD_SP_SOURCE_RUN_DEFINITION?WOOD_SP_SOURCE_RUN_REGION:WOOD_SP_SOURCE_MEMBER_REGION;uint32_t root_id=root==WOOD_SP_SOURCE_RUN_REGION?5:3;
        CHECK("bad-definition-no-derived-value",node(f,root,root_id,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value);}
    dispose(f,false);return 0;
}
static int inactive_complete(void)
{
    Fixture *f=authority_seed(AUTH_NONE,0,0);CHECK("complete-setup",f&&rebuild(f));
    CHECK("complete-call-succeeds",wood_sp_sources_complete(f->sources));GeoSourceNodeView n;
    CHECK("unused-definition-complete",node(f,WOOD_SP_SOURCE_PROFILE_DEFINITION,99,&n,NULL)&&n.state==GEO_NODE_VALID&&n.value&&n.value->as.definition.content_size==strlen(f->state.profiles[1].content)&&!memcmp(n.value->as.definition.content,f->state.profiles[1].content,n.value->as.definition.content_size));
    CHECK("complete-preserves-unplaced-frame-new",node(f,WOOD_SP_SOURCE_RUN_FRAME,6,&n,NULL)&&n.state==GEO_NODE_NEW&&n.described&&!n.value);
    CHECK("complete-seal",geo_eval_seal(f->graph));GeoSourceValue v;
    CHECK("sealed-unused-bytes-readable",value(f,WOOD_SP_SOURCE_PROFILE_DEFINITION,99,&v)&&v.as.definition.content_size==strlen(f->state.profiles[1].content));
    CHECK("sealed-unplaced-frame-still-new",node(f,WOOD_SP_SOURCE_RUN_FRAME,6,&n,NULL)&&n.state==GEO_NODE_NEW&&!n.value);
    dispose(f,true);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"member"))return member_authority();if(!strcmp(argv[1],"run"))return run_authority(false);if(!strcmp(argv[1],"copied"))return run_authority(true);
    if(!strcmp(argv[1],"profile"))return profile_authority();if(!strcmp(argv[1],"frame"))return geometry_authority(true);if(!strcmp(argv[1],"host-region"))return geometry_authority(false);
    if(!strcmp(argv[1],"frame-status"))return geometry_status(true);if(!strcmp(argv[1],"host-status"))return geometry_status(false);
    if(!strcmp(argv[1],"pair"))return pair_authority(AUTH_NONE);if(!strcmp(argv[1],"pair-first"))return pair_authority(AUTH_PAIR_FIRST);if(!strcmp(argv[1],"pair-second"))return pair_authority(AUTH_PAIR_SECOND);
    if(!strcmp(argv[1],"complete"))return inactive_complete();
    if(!strcmp(argv[1],"parity"))return graph_values()||diagnostics()||region_guards()||hosts();
    const char *names[]={"malformed","status","schema","identity"};int modes[]={AUTH_MALFORMED,AUTH_STATUS,AUTH_SCHEMA,AUTH_IDENTITY};
    for(size_t i=0;i<4;++i){char name[64];const char *types[]={"profile","member","run","unused"};int kinds[]={WOOD_SP_SOURCE_PROFILE_DEFINITION,WOOD_SP_SOURCE_MEMBER_DEFINITION,WOOD_SP_SOURCE_RUN_DEFINITION,WOOD_SP_SOURCE_PROFILE_DEFINITION};uint32_t ids[]={1,3,5,99};
        for(size_t j=0;j<4;++j){snprintf(name,sizeof name,"%s-%s",names[i],types[j]);if(!strcmp(argv[1],name))return definition_failure(modes[i],kinds[j],ids[j]);}}
    return 2;
}
