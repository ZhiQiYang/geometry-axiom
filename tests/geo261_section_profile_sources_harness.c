/* Numeric graph witnesses drive the real wood_sp_rebuild hooks and K graph.
 * A leaf resolver observes ACTIVE nodes while producing values; cached-state
 * export cannot satisfy these witnesses. No host record is linked. */
#include "section_profile_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TOKEN 11
#define PARAM_TOKEN 90
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
typedef struct {
    SectionProfileState state;EngineeringState engineering;WoodSectionProfileContext context;
    GeoEvalContext *graph;WoodSectionProfileSources *sources;
    char error[700];int events[256],event_count,host_calls,parameter_calls,active_failures;
    bool fail_dimensions,fail_host,derived_host,long_error,overflow_run_length;
    GeoFrame host_frame;WoodBoundaryRegion host_region;GeoCoord parameter;
} Fixture;
static bool node(Fixture *f,int kind,uint32_t id,GeoSourceNodeView *out,size_t *index)
{
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;WoodSectionProfileSourceKind k;uint32_t value;
        if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==TOKEN&&wood_sp_source_decode(&n.source,&k,&value)&&k==kind&&value==id){if(out)*out=n;if(index)*index=i;return true;}}
    return false;
}
static bool active(Fixture *f,int kind,uint32_t id)
{GeoSourceNodeView n;return node(f,kind,id,&n,NULL)&&n.state==GEO_NODE_ACTIVE;}
static bool edge(Fixture *f,int consumer,uint32_t cid,int source,uint32_t sid,GeoDependencyKind relation)
{
    size_t c,s;if(!node(f,consumer,cid,NULL,&c)||!node(f,source,sid,NULL,&s))return false;
    for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;geo_eval_edge_at(f->graph,i,&e);if(e.consumer==c&&e.source==s&&e.kind==relation)return true;}return false;
}
static bool external_description(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(ref->provider!=PARAM_TOKEN||ref->key_size!=1||*(const unsigned char *)ref->key!=5)return false;*out=(GeoSourceDescriptor){GEO_SOURCE_QUANTITY,GEO_UNIT_LENGTH,{false,0,-1},true};return true;}
static bool external_value(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{Fixture *f=user;(void)graph;(void)ref;++f->parameter_calls;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){f->parameter,1,GEO_UNIT_LENGTH};return true;}
static bool dimension(void *user,const EngDimensionSource *source,const EngTarget *target,GeoCoord *out)
{
    Fixture *f=user;int kind=0;uint32_t id=0;
    for(size_t i=0;i<f->state.member_count;++i){if(source==&f->state.members[i].a_source){kind=WOOD_SP_SOURCE_MEMBER_A;id=f->state.members[i].id;}if(source==&f->state.members[i].b_source){kind=WOOD_SP_SOURCE_MEMBER_B;id=f->state.members[i].id;}}
    for(size_t i=0;i<f->state.run_count;++i)if(source==&f->state.runs[i].length_source){kind=WOOD_SP_SOURCE_RUN_LENGTH;id=f->state.runs[i].id;}
    /* Decoded definitions own their source structs. Observe the active typed
     * leaf rather than requiring the provider to pass a raw-record address. */
    if(f->graph)for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;WoodSectionProfileSourceKind k;uint32_t v;
        if(geo_eval_node_at(f->graph,i,&n)&&n.state==GEO_NODE_ACTIVE&&n.source.provider==TOKEN&&wood_sp_source_decode(&n.source,&k,&v)&&
           (k==WOOD_SP_SOURCE_MEMBER_A||k==WOOD_SP_SOURCE_MEMBER_B||k==WOOD_SP_SOURCE_RUN_LENGTH)){kind=k;id=v;}}
    f->events[f->event_count++]=kind*100+(int)id;
    if(f->graph&&!active(f,kind,id))++f->active_failures;
    if(f->fail_dimensions){
        if(f->long_error){memset(f->error,'Q',sizeof f->error-1);f->error[sizeof f->error-1]=0;memcpy(f->error,"dimension failure ",18);}
        else snprintf(f->error,sizeof f->error,"dimension %u field %d invalid",id,target->field);
        return false;
    }
    if(source->kind==ENG_PARAMETER){
        if(f->graph){unsigned char key=5;GeoSourceValue value;if(geo_eval_source(f->graph,(GeoSourceRef){PARAM_TOKEN,&key,1},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;*out=value.as.quantity.num;}
        else *out=f->parameter;
    }else *out=source->value;
    if(f->overflow_run_length&&kind==WOOD_SP_SOURCE_RUN_LENGTH&&id==5)*out=GEO_COORD_LIMIT+1;
    if(*out<=0||!geo_coord_in_range(*out)){snprintf(f->error,sizeof f->error,"dimension %u field %d outside positive D1",id,target->field);return false;}
    return true;
}
static bool live_host(void *user,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    Fixture *f=user;++f->host_calls;f->events[f->event_count++]=1000+(int)id;
    if(f->graph&&!active(f,WOOD_SP_SOURCE_HOST_FRAME,id))++f->active_failures;
    if(f->fail_host||id!=10)return false;
    *derived=f->derived_host;if(*derived)return true;*frame=f->host_frame;*region=f->host_region;return true;
}
static Fixture *fixture(void)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;
    f->parameter=27;f->host_frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    f->host_region.outline.count=4;GeoPoint2 p[4]={{0,0},{100,0},{100,100},{0,100}};memcpy(f->host_region.outline.v,p,sizeof p);
    f->context=(WoodSectionProfileContext){.state=&f->state,.engineering={.state=&f->engineering,.error=f->error,.error_capacity=sizeof f->error},.user=f,.error=f->error,.error_capacity=sizeof f->error,.resolve_dimension=dimension,.live_host=live_host};
    return f;
}
static bool record(Fixture *f,int kind,const char *text)
{GeoJson j={0};if(!geo_json_parse(&j,text))return false;bool ok=kind==0?wood_sp_put_profile(&f->context,&j,0):kind==1?wood_sp_put_member(&f->context,&j,0):wood_sp_put_run(&f->context,&j,0);geo_json_free(&j);return ok;}
static bool edit_record(char *content,size_t capacity,const char *before,const char *after)
{
    char *at=strstr(content,before);if(!at||strstr(at+strlen(before),before))return false;
    size_t size=strlen(content)-strlen(before)+strlen(after);if(size>=capacity)return false;
    memmove(at+strlen(after),at+strlen(before),strlen(at+strlen(before))+1);memcpy(at,after,strlen(after));return true;
}
static bool seed(Fixture *f)
{
    return record(f,0,"{\"id\":1,\"name\":\"shape\",\"outline\":[[0,0],[100,0],[100,100],[0,100]]}")&&
        record(f,0,"{\"id\":99,\"name\":\"unused\",\"outline\":[[0,0],[20,0],[20,20],[0,20]]}")&&
        record(f,1,"{\"id\":3,\"profileId\":1,\"kind\":\"timber\",\"A\":{\"kind\":\"parameter\",\"parameterId\":8,\"fieldId\":5},\"B\":{\"kind\":\"literal\",\"value\":33},\"orientation\":\"A-u\",\"u0\":10,\"v0\":20}")&&
        record(f,1,"{\"id\":4,\"profileId\":1,\"kind\":\"panel\",\"panelSpec\":\"calcium-silicate-6\",\"width\":30,\"orientation\":\"thickness-v\",\"u0\":60,\"v0\":20}")&&
        record(f,2,"{\"id\":5,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":120},\"placement\":{\"kind\":\"simple\",\"host\":{\"kind\":\"placement\",\"placementId\":10},\"dir\":\"+u\",\"p\":5,\"q\":7,\"up\":\"+Z\"}}")&&
        record(f,2,"{\"id\":6,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":50},\"placement\":null}");
}
static bool connect(Fixture *f)
{
    f->graph=geo_eval_create(401,77);if(!f->graph)return false;
    f->sources=wood_sp_sources_create(f->graph,TOKEN,&f->context);if(!f->sources)return false;
    GeoSourceProvider external={PARAM_TOKEN,"test.parameter","test/1",f,external_description,external_value};
    return geo_eval_register(f->graph,&external)&&wood_sp_sources_bind(f->sources,&f->context);
}
static void dispose(Fixture *f,bool provider_first)
{if(!f)return;if(provider_first){wood_sp_sources_destroy(f->sources);geo_eval_destroy(f->graph);}else{geo_eval_destroy(f->graph);wood_sp_sources_destroy(f->sources);}free(f);}
static bool rebuild(Fixture *f){char message[700];return wood_sp_rebuild(&f->context,message,sizeof message);}
static bool value(Fixture *f,int kind,uint32_t id,GeoSourceValue *out)
{WoodSectionProfileSourceKey key;return geo_eval_source(f->graph,wood_sp_source_ref(TOKEN,(WoodSectionProfileSourceKind)kind,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}

static int graph_values(void)
{
    Fixture *f=fixture();CHECK("graph-seed",f&&seed(f)&&connect(f));CHECK("register-without-evaluation",geo_eval_provider_count(f->graph)==2&&geo_eval_node_count(f->graph)==0);
    CHECK("actual-rebuild-positive",rebuild(f));CHECK("callbacks-inside-active-values",f->active_failures==0&&f->event_count==5&&f->events[0]==303&&f->events[1]==403&&f->events[2]==705&&f->events[3]==1010&&f->events[4]==706&&f->parameter_calls==1);
    GeoSourceValue v;CHECK("member-a-value",value(f,WOOD_SP_SOURCE_MEMBER_A,3,&v)&&v.kind==GEO_SOURCE_QUANTITY&&v.as.quantity.unit==GEO_UNIT_LENGTH&&v.as.quantity.num==27&&v.as.quantity.den==1);
    CHECK("panel-values",value(f,WOOD_SP_SOURCE_MEMBER_A,4,&v)&&v.as.quantity.num==30&&value(f,WOOD_SP_SOURCE_MEMBER_B,4,&v)&&v.as.quantity.num==6);
    CHECK("member-region-value",value(f,WOOD_SP_SOURCE_MEMBER_REGION,3,&v)&&v.kind==GEO_SOURCE_REGION_SET&&v.as.regions.count==1&&v.as.regions.regions[0].outline.count==4&&v.as.regions.regions[0].outline.v[2].u==37&&v.as.regions.regions[0].outline.v[2].v==53);
    CHECK("run-frame-value",value(f,WOOD_SP_SOURCE_RUN_FRAME,5,&v)&&v.kind==GEO_SOURCE_FRAME&&v.as.frame.origin.x==15&&v.as.frame.origin.y==27&&v.as.frame.origin.z==30&&v.as.frame.normal.x==1&&v.as.frame.axis_v.z==-1&&v.as.frame.axis_u.y==-1);
    CHECK("run-length-value",value(f,WOOD_SP_SOURCE_RUN_LENGTH,5,&v)&&v.as.quantity.num==120);
    CHECK("definition-canonical-content",value(f,WOOD_SP_SOURCE_PROFILE_DEFINITION,1,&v)&&v.kind==GEO_SOURCE_DEFINITION&&!strcmp(v.as.definition.schema,"wood.section-profile.definition/1")&&v.as.definition.content_size==strlen(f->state.profiles[0].content)&&!memcmp(v.as.definition.content,f->state.profiles[0].content,v.as.definition.content_size));
    CHECK("member-definition-edge",edge(f,WOOD_SP_SOURCE_MEMBER_REGION,3,WOOD_SP_SOURCE_MEMBER_DEFINITION,3,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&edge(f,WOOD_SP_SOURCE_MEMBER_A,3,WOOD_SP_SOURCE_MEMBER_DEFINITION,3,GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("member-profile-edge",edge(f,WOOD_SP_SOURCE_MEMBER_REGION,3,WOOD_SP_SOURCE_PROFILE_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("member-dimensions-drive-region",edge(f,WOOD_SP_SOURCE_MEMBER_REGION,3,WOOD_SP_SOURCE_MEMBER_A,3,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_SP_SOURCE_MEMBER_REGION,3,WOOD_SP_SOURCE_MEMBER_B,3,GEO_DEPENDENCY_VALUE_REQUIRED));
    CHECK("run-inputs-drive-region",edge(f,WOOD_SP_SOURCE_RUN_REGION,5,WOOD_SP_SOURCE_RUN_LENGTH,5,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_SP_SOURCE_RUN_REGION,5,WOOD_SP_SOURCE_RUN_FRAME,5,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_SP_SOURCE_RUN_REGION,5,WOOD_SP_SOURCE_PROFILE_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("live-host-value-edges",edge(f,WOOD_SP_SOURCE_RUN_FRAME,5,WOOD_SP_SOURCE_HOST_FRAME,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_SP_SOURCE_RUN_FRAME,5,WOOD_SP_SOURCE_HOST_REGION,10,GEO_DEPENDENCY_VALUE_REQUIRED));
    GeoSourceNodeView descriptor;CHECK("geometry-descriptor-length-units",node(f,WOOD_SP_SOURCE_RUN_FRAME,5,&descriptor,NULL)&&descriptor.descriptor.unit==GEO_UNIT_LENGTH&&node(f,WOOD_SP_SOURCE_MEMBER_REGION,3,&descriptor,NULL)&&descriptor.descriptor.unit==GEO_UNIT_LENGTH&&node(f,WOOD_SP_SOURCE_HOST_REGION,10,&descriptor,NULL)&&descriptor.descriptor.unit==GEO_UNIT_LENGTH);
    size_t consumer;CHECK("parameter-leaf",node(f,WOOD_SP_SOURCE_MEMBER_A,3,NULL,&consumer));bool parameter_edge=false;
    for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;GeoSourceNodeView n;geo_eval_edge_at(f->graph,i,&e);geo_eval_node_at(f->graph,e.source,&n);if(e.consumer==consumer&&n.source.provider==PARAM_TOKEN&&e.kind==GEO_DEPENDENCY_VALUE_REQUIRED)parameter_edge=true;}
    CHECK("parameter-closure-on-active-dimension",parameter_edge);dispose(f,false);return 0;
}
static int inactive(void)
{
    Fixture *f=fixture();CHECK("inactive-seed",f&&seed(f)&&connect(f));CHECK("unplaced-rebuild-without-frame-value",rebuild(f));GeoSourceNodeView n;
    CHECK("unused-definition-remains-new",node(f,WOOD_SP_SOURCE_PROFILE_DEFINITION,99,&n,NULL)&&n.described&&n.state==GEO_NODE_NEW&&n.value==NULL&&n.descriptor.kind==GEO_SOURCE_DEFINITION);
    CHECK("unplaced-frame-remains-new",node(f,WOOD_SP_SOURCE_RUN_FRAME,6,&n,NULL)&&n.described&&n.state==GEO_NODE_NEW&&n.value==NULL&&n.descriptor.kind==GEO_SOURCE_FRAME);
    CHECK("unplaced-frame-identity-edge",edge(f,WOOD_SP_SOURCE_RUN_REGION,6,WOOD_SP_SOURCE_RUN_FRAME,6,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&!edge(f,WOOD_SP_SOURCE_RUN_REGION,6,WOOD_SP_SOURCE_RUN_FRAME,6,GEO_DEPENDENCY_VALUE_REQUIRED));
    CHECK("unplaced-run-keeps-existing-cache",f->state.runs[1].resolved&&f->state.runs[1].placement_resolved&&!f->state.runs[1].placed&&f->state.runs[1].length==50);
    CHECK("sealed-existing-values",geo_eval_seal(f->graph));GeoSourceValue v;CHECK("sealed-value-still-readable",value(f,WOOD_SP_SOURCE_MEMBER_A,3,&v)&&v.as.quantity.num==27);
    WoodSectionProfileSourceKey key;GeoSourceDescriptor d;CHECK("sealed-new-metadata-readable",geo_eval_describe(f->graph,wood_sp_source_ref(TOKEN,WOOD_SP_SOURCE_RUN_FRAME,6,&key),&d)==GEO_SOURCE_OK&&d.kind==GEO_SOURCE_FRAME);
    dispose(f,true);return 0;
}
static int diagnostics(void)
{
    Fixture *plain=fixture(),*graph=fixture();CHECK("diagnostic-seed",plain&&graph&&seed(plain));
    plain->state.members[0].profile_id=88;plain->state.runs[0].profile_id=89;plain->fail_dimensions=true;plain->fail_host=true;
    CHECK("diagnostic-canonical-fixture",edit_record(plain->state.members[0].content,SP_RECORD_MAX,"\"profileId\":1","\"profileId\":88")&&edit_record(plain->state.runs[0].content,SP_RUN_RECORD_MAX,"\"profileId\":1","\"profileId\":89"));
    memcpy(&graph->state,&plain->state,sizeof plain->state);graph->fail_dimensions=true;graph->fail_host=true;CHECK("diagnostic-connect",connect(graph));
    CHECK("both-paths-refuse",!rebuild(plain)&&!rebuild(graph));
    CHECK("diagnostic-first-order",!strcmp(plain->error,graph->error)&&!strcmp(graph->error,"I49: member 3 references missing profile 88"));
    CHECK("diagnostic-all-attempts",plain->event_count==5&&graph->event_count==5&&!memcmp(plain->events,graph->events,5*sizeof(int))&&graph->active_failures==0);
    CHECK("diagnostic-cache-equivalence",!memcmp(&plain->state,&graph->state,sizeof plain->state));
    GeoSourceNodeView n;CHECK("failed-region-has-no-value",node(graph,WOOD_SP_SOURCE_MEMBER_REGION,3,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value);
    CHECK("second-dimension-attempted",node(graph,WOOD_SP_SOURCE_MEMBER_B,3,&n,NULL)&&n.state==GEO_NODE_FAILED&&graph->state.members[0].source_error[0][0]&&graph->state.members[0].source_error[1][0]);
    graph->event_count=0;CHECK("diagnostic-retry-preserves-first",!rebuild(graph)&&!strcmp(graph->error,plain->error)&&graph->event_count==5);
    dispose(plain,false);dispose(graph,true);
    plain=fixture();graph=fixture();CHECK("long-error-seed",plain&&graph&&seed(plain));plain->state.member_count=1;plain->state.run_count=0;plain->fail_dimensions=plain->long_error=true;
    memcpy(&graph->state,&plain->state,sizeof plain->state);graph->fail_dimensions=graph->long_error=true;CHECK("long-error-connect",connect(graph));
    CHECK("diagnostic-no-extra-truncation",!rebuild(plain)&&!rebuild(graph)&&strlen(plain->error)==255&&!strcmp(plain->error,graph->error)&&!memcmp(&plain->state,&graph->state,sizeof plain->state));dispose(plain,false);dispose(graph,false);
    plain=fixture();graph=fixture();CHECK("partial-write-seed",plain&&graph&&seed(plain));plain->parameter=-7;plain->state.members[0].b_source.value=0;plain->overflow_run_length=true;
    CHECK("partial-write-canonical-fixture",edit_record(plain->state.members[0].content,SP_RECORD_MAX,"\"B\":{\"kind\":\"literal\",\"value\":33}","\"B\":{\"kind\":\"literal\",\"value\":0}"));
    plain->state.members[0].a=71;plain->state.members[0].b=72;plain->state.runs[0].length=73;
    memcpy(&graph->state,&plain->state,sizeof plain->state);graph->parameter=plain->parameter;graph->overflow_run_length=true;CHECK("partial-write-connect",connect(graph));
    CHECK("partial-write-both-refuse",!rebuild(plain)&&!rebuild(graph));
    CHECK("failed-member-dimension-cache-write",plain->state.members[0].a==-7&&plain->state.members[0].b==0&&graph->state.members[0].a==-7&&graph->state.members[0].b==0);
    CHECK("failed-run-length-cache-write",plain->state.runs[0].length==GEO_COORD_LIMIT+1&&graph->state.runs[0].length==GEO_COORD_LIMIT+1);
    CHECK("failed-value-cache-equivalence",!strcmp(plain->error,graph->error)&&!memcmp(&plain->state,&graph->state,sizeof plain->state));
    CHECK("failed-numbers-never-published",node(graph,WOOD_SP_SOURCE_MEMBER_A,3,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value&&node(graph,WOOD_SP_SOURCE_MEMBER_B,3,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value&&node(graph,WOOD_SP_SOURCE_RUN_LENGTH,5,&n,NULL)&&n.state==GEO_NODE_FAILED&&!n.value);
    dispose(plain,false);dispose(graph,true);return 0;
}
static int region_guards(void)
{
    Fixture *f=fixture();CHECK("region-seed",f&&seed(f));f->state.members[0].u0=90;CHECK("region-canonical-fixture",edit_record(f->state.members[0].content,SP_RECORD_MAX,"\"u0\":10","\"u0\":90"));CHECK("region-connect",connect(f));
    CHECK("outside-is-real-region-failure",!rebuild(f)&&strstr(f->error,"V_PROFILE_OUTSIDE")&&f->state.members[0].resolved&&f->state.members[0].outside);
    GeoSourceNodeView n;CHECK("outside-source-refused",node(f,WOOD_SP_SOURCE_MEMBER_REGION,3,&n,NULL)&&n.state==GEO_NODE_FAILED&&n.value==NULL);
    dispose(f,false);f=fixture();CHECK("overlap-seed",f&&seed(f));f->state.members[1].u0=20;f->state.runs[0].profile_id=88;
    CHECK("overlap-canonical-fixture",edit_record(f->state.members[1].content,SP_RECORD_MAX,"\"u0\":60","\"u0\":20")&&edit_record(f->state.runs[0].content,SP_RUN_RECORD_MAX,"\"profileId\":1","\"profileId\":88"));CHECK("overlap-connect",connect(f));
    CHECK("overlap-before-run-diagnostics",!rebuild(f)&&strstr(f->error,"V_PROFILE_OVERLAP")&&f->state.runs[0].missing_profile);dispose(f,false);
    f=fixture();CHECK("run-range-seed",f&&seed(f));char advanced[1024];snprintf(advanced,sizeof advanced,"{\"id\":5,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":120},\"placement\":{\"kind\":\"advanced\",\"origin\":[%lld,0,0],\"N\":\"+X\",\"V\":\"+Y\"}}",(long long)(GEO_COORD_LIMIT-50));CHECK("run-range-canonical-fixture",record(f,2,advanced));CHECK("run-range-connect",connect(f));
    CHECK("range-is-real-run-failure",!rebuild(f)&&f->state.runs[0].range_error&&!f->state.runs[0].resolved&&strstr(f->error,"generated vertex"));
    CHECK("range-source-refused",node(f,WOOD_SP_SOURCE_RUN_REGION,5,&n,NULL)&&n.state==GEO_NODE_FAILED);dispose(f,true);return 0;
}
static int hosts(void)
{
    Fixture *f=fixture();CHECK("host-seed",f&&seed(f));f->derived_host=true;CHECK("host-connect",connect(f));
    CHECK("derived-live-host-refused",!rebuild(f)&&!f->state.runs[0].placement_resolved&&strstr(f->state.runs[0].placement_error,"live host 10"));
    GeoSourceNodeView n;CHECK("derived-frame-never-published",node(f,WOOD_SP_SOURCE_HOST_FRAME,10,&n,NULL)&&n.state==GEO_NODE_FAILED&&!node(f,WOOD_SP_SOURCE_HOST_REGION,10,NULL,NULL));dispose(f,false);
    f=fixture();CHECK("host-range-seed",f&&seed(f));f->state.runs[0].p=101;CHECK("host-range-canonical-fixture",edit_record(f->state.runs[0].content,SP_RUN_RECORD_MAX,"\"p\":5","\"p\":101"));CHECK("host-range-connect",connect(f));
    CHECK("live-host-range-checked",!rebuild(f)&&strstr(f->state.runs[0].placement_error,"outside closed host range"));dispose(f,true);
    f=fixture();CHECK("copied-host-seed",f&&seed(f));
    CHECK("copied-host-canonical-fixture",record(f,2,"{\"id\":5,\"profileId\":1,\"length\":{\"kind\":\"literal\",\"value\":120},\"placement\":{\"kind\":\"simple\",\"host\":{\"kind\":\"space-wall-values\",\"sourceDescription\":\"copied test wall\",\"frame\":{\"origin\":[10,20,30],\"U\":\"+X\",\"V\":\"+Y\",\"N\":\"+Z\"},\"region\":{\"outline\":[[0,0],[100,0],[100,100],[0,100]],\"holes\":[]}},\"dir\":\"+u\",\"p\":5,\"q\":7,\"up\":\"+Z\"}}"));f->fail_host=true;CHECK("copied-host-connect",connect(f));
    CHECK("copied-host-has-no-live-dependency",rebuild(f)&&f->host_calls==0&&!node(f,WOOD_SP_SOURCE_HOST_FRAME,10,NULL,NULL)&&edge(f,WOOD_SP_SOURCE_RUN_FRAME,5,WOOD_SP_SOURCE_RUN_DEFINITION,5,GEO_DEPENDENCY_DEFINITION_REQUIRED));dispose(f,false);return 0;
}
static int lifetime(void)
{
    Fixture *a=fixture(),*b=fixture();CHECK("isolation-seed",a&&b&&seed(a)&&seed(b));b->parameter=40;b->state.members[1].u0=70;b->state.members[1].width=20;
    CHECK("isolation-canonical-fixture",edit_record(b->state.members[1].content,SP_RECORD_MAX,"\"u0\":60","\"u0\":70")&&edit_record(b->state.members[1].content,SP_RECORD_MAX,"\"width\":30","\"width\":20"));CHECK("isolation-connect",connect(a)&&connect(b)&&rebuild(a)&&rebuild(b));
    GeoSourceValue av,bv;CHECK("candidate-values-isolated",value(a,WOOD_SP_SOURCE_MEMBER_A,3,&av)&&value(b,WOOD_SP_SOURCE_MEMBER_A,3,&bv)&&av.as.quantity.num==27&&bv.as.quantity.num==40);
    CHECK("bind-rejects-other-candidate",!wood_sp_sources_bind(a->sources,&b->context));
    GeoSourceValue region,host_region;CHECK("borrowed-region",value(a,WOOD_SP_SOURCE_MEMBER_REGION,3,&region)&&value(a,WOOD_SP_SOURCE_HOST_REGION,10,&host_region));const GeoPoint2 *points=region.as.regions.regions[0].outline.v,*host_points=host_region.as.regions.regions[0].outline.v;
    for(uint32_t id=100;id<180;++id){GeoSourceValue ignored;WoodSectionProfileSourceKey key;(void)geo_eval_source(a->graph,wood_sp_source_ref(TOKEN,WOOD_SP_SOURCE_HOST_FRAME,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&ignored);}
    CHECK("region-borrow-stable",points==region.as.regions.regions[0].outline.v&&points[2].u==37&&points[2].v==53&&host_points==host_region.as.regions.regions[0].outline.v&&host_points[2].u==100&&host_points[2].v==100);
    WoodSectionProfileSourceKey key;GeoSourceRef ref=wood_sp_source_ref(TOKEN,WOOD_SP_SOURCE_RUN_DEFINITION,UINT32_MAX,&key);WoodSectionProfileSourceKind kind=0;uint32_t id=0;
    CHECK("exact-key-roundtrip",wood_sp_source_decode(&ref,&kind,&id)&&kind==WOOD_SP_SOURCE_RUN_DEFINITION&&id==UINT32_MAX&&key.bytes[1]==255&&key.bytes[4]==255);
    unsigned char bad[5]={0};ref.key=bad;CHECK("invalid-key-output-preserved",!wood_sp_source_decode(&ref,&kind,&id)&&id==UINT32_MAX&&kind==WOOD_SP_SOURCE_RUN_DEFINITION);
    dispose(a,true);CHECK("other-candidate-survives",value(b,WOOD_SP_SOURCE_MEMBER_A,3,&bv)&&bv.as.quantity.num==40);dispose(b,false);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;if(!strcmp(argv[1],"graph"))return graph_values();if(!strcmp(argv[1],"inactive"))return inactive();if(!strcmp(argv[1],"diagnostics"))return diagnostics();
    if(!strcmp(argv[1],"regions"))return region_guards();if(!strcmp(argv[1],"hosts"))return hosts();if(!strcmp(argv[1],"lifetime"))return lifetime();return 2;
}
