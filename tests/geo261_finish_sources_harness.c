/* Actual W policy and K graph. Leaf callbacks observe ACTIVE source nodes;
 * fixed geometry, exact edges and no-hook parity are independent oracles. */
#include "finish_sources.h"
#include "engineering_sources.h"
#include "parameter_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
enum { FS_NAMED=3,FS_PARAMETER=4,FS_DIMENSION=5,FS_BINDING=6,FS_DEFINITION=7,FS_SOURCE=12 };
typedef struct {
    FinishSurfaceState state;EngineeringState engineering;WoodDerivedContext context;
    WoodBoundaryRegion boundary;WoodDerivedValue placements[2];
    GeoEvalContext *graph;GeoParameterStore *parameters;GeoParameterSources *parameter_sources;GeoVersionStore *versions;
    WoodEngineeringSources *engineering_sources;WoodFinishSources *sources;
    FsDiagnosticKind diagnostic;char error[512],parameter_error[256];
    GeoCoord lo[3],hi[3],depth;bool boundary_ok,box_ok,named_ok;
    unsigned writes,reads,boundary_calls,box_calls,parameter_calls,named_calls,active_failures;
} Fixture;
static size_t source_index(const GeoEvalContext *graph,WoodFinishSourceKind kind,uint32_t id)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;WoodFinishSourceKind k;uint32_t n;
        if(geo_eval_node_at(graph,i,&node)&&node.source.provider==FS_SOURCE&&wood_finish_source_decode(&node.source,&k,&n)&&k==kind&&n==id)return i;}
    return SIZE_MAX;
}
static bool active(Fixture *f,WoodFinishSourceKind kind,uint32_t id)
{GeoSourceNodeView node;return !f->graph||(geo_eval_node_at(f->graph,source_index(f->graph,kind,id),&node)&&node.state==GEO_NODE_ACTIVE);}
static bool boundary(void *user,uint32_t id,WoodBoundaryRegion *out)
{Fixture *f=user;++f->boundary_calls;if(!active(f,WOOD_FINISH_SOURCE_BOUNDARY_REGION,id))++f->active_failures;if(id!=8||!f->boundary_ok)return false;*out=f->boundary;return true;}
static bool obstacle(void *user,const FinishObstacleRef *ref,GeoCoord lo[3],GeoCoord hi[3])
{Fixture *f=user;++f->box_calls;if(!active(f,WOOD_FINISH_SOURCE_BEAM_BOX,ref->id))++f->active_failures;if(ref->id!=20||ref->kind!=FS_OBSTACLE_BEAM||!f->box_ok)return false;memcpy(lo,f->lo,sizeof f->lo);memcpy(hi,f->hi,sizeof f->hi);return true;}
static bool parameter_coord(void *user,GeoParameterRef ref,GeoCoord *out)
{Fixture *f=user;++f->parameter_calls;GeoParameterError error;bool ok=geo_parameters_coordinate(f->parameters,ref,out,&error);if(!ok)snprintf(f->parameter_error,sizeof f->parameter_error,"I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);return ok;}
static bool parameter_value(void *user,GeoParameterRef ref,GeoQuantity *out)
{Fixture *f=user;++f->parameter_calls;GeoParameterError error;bool ok=geo_parameters_dimension_value(f->parameters,ref,out,&error);if(!ok)snprintf(f->parameter_error,sizeof f->parameter_error,"I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);return ok;}
static bool engineering_parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{Fixture *f=user;if(parameter_coord(user,ref,out))return true;snprintf(error,cap,"%s",f->parameter_error);return false;}
static bool named(void *user,const char *name,GeoCoord *out)
{Fixture *f=user;++f->named_calls;if(!f->named_ok||strcmp(name,"depth"))return false;*out=f->depth;return true;}
static bool placement_read(void *user,uint32_t id,WoodDerivedValue *out)
{Fixture *f=user;++f->reads;for(size_t i=0;i<2;++i)if(f->placements[i].id==id){*out=f->placements[i];return true;}return false;}
static bool placement_write(void *user,const WoodDerivedValue *value)
{Fixture *f=user;for(size_t i=0;i<2;++i)if(f->placements[i].id==value->id){f->placements[i]=*value;++f->writes;return true;}return false;}
static bool placement_remove(void *user,uint32_t id){(void)user;(void)id;return false;}
static size_t placement_count(void *user){(void)user;return 2;}
static void remove_position(void *user,uint32_t id){(void)user;(void)id;}
static bool named_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(ref->provider!=FS_NAMED||ref->key_size!=5||memcmp(ref->key,"depth",5))return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_QUANTITY,.unit=GEO_UNIT_LENGTH,.context={false,0,-1},.retry_failure=true};return true;}
static bool named_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{Fixture *f=user;GeoCoord value;(void)ref;if(graph!=f->graph||!named(user,"depth",&value))return false;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;}
static bool parameters(Fixture *f)
{
    GeoParameterCard card;GeoParameterField fields[4]={0};GeoParameterError error;geo_parameters_begin_definition(f->parameters,90,&card);strcpy(card.name,"layout");card.count=4;
    const int values[]={3,20,8,30};
    for(size_t i=0;i<4;++i){GeoParameterField *p=&fields[i];p->parameter_id=90;p->id=(uint32_t)i+1;p->type=GEO_PARAMETER_DIMENSION;snprintf(p->name,sizeof p->name,"value-%zu",i+1);
        snprintf(p->expression,sizeof p->expression,"{\"op\":\"literal\",\"num\":\"%d\",\"den\":\"1\",\"unit\":\"mm\"}",values[i]);}
    strcpy(fields[3].expression,"{\"op\":\"mul\",\"left\":{\"op\":\"ref\",\"parameterId\":90,\"fieldId\":1},\"right\":{\"op\":\"literal\",\"num\":\"10\",\"den\":\"1\",\"unit\":\"1\"}}");
    for(size_t i=0;i<4;++i)if(!geo_parameters_accept_field(f->parameters,&card,fields,i,&error))return false;
    return geo_parameters_put(f->parameters,&card,fields,&error)&&geo_parameters_rebuild(f->parameters,&error);
}
static bool parse(Fixture *f,const char *text,int kind,void *out)
{GeoJson json={0};if(!geo_json_parse(&json,text)){geo_json_free(&json);return false;}bool ok=kind==0?wood_eng_publish_material(&f->context.finish.engineering,&json,0,NULL):kind==1?wood_pf_parse(&f->context.finish,&json,0,out):wood_dp_parse(&f->context,&json,0,out);geo_json_free(&json);return ok;}
static Fixture *fixture_thickness(const char *thickness)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;f->parameters=geo_parameters_create();f->boundary_ok=f->box_ok=f->named_ok=true;f->depth=30;
    if(geo_versions_create(&f->versions)!=GEO_VERSION_OK)return NULL;
    f->context=(WoodDerivedContext){.finish={.state=&f->state,.engineering={.state=&f->engineering,.versions=f->versions,.user=f,.error=f->error,.error_capacity=sizeof f->error,.named_value=named,.parameter=engineering_parameter},
        .user=f,.error=f->error,.error_capacity=sizeof f->error,.diagnostic=&f->diagnostic,.boundary=boundary,.obstacle_box=obstacle,.parameter_coord=parameter_coord,.parameter_value=parameter_value,.parameter_error=f->parameter_error,.parameter_error_capacity=sizeof f->parameter_error},
        .placement_read=placement_read,.placement_write=placement_write,.placement_remove=placement_remove,.placement_count=placement_count,.placement_capacity=FS_MAX,.remove_canvas_position=remove_position};
    f->boundary.id=8;f->boundary.kind=WOOD_BOUNDARY_ROOM_PLAN;f->boundary.outline.count=4;
    f->boundary.outline.v[0]=(GeoPoint2){0,0};f->boundary.outline.v[1]=(GeoPoint2){100,0};f->boundary.outline.v[2]=(GeoPoint2){100,100};f->boundary.outline.v[3]=(GeoPoint2){0,100};
    for(size_t i=0;i<4;++i)f->boundary.outline.fixity[i]=WOOD_EDGE_FIXED;
    FinishSurface *finish=&f->state.items[0];finish->id=1;finish->boundary_id=8;finish->side=1;strcpy(finish->name,"finish");finish->frame=(GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};finish->obstacle_count=1;finish->obstacles[0]=(FinishObstacleRef){FS_OBSTACLE_BEAM,20};f->state.count=1;
    f->lo[0]=f->lo[1]=20;f->lo[2]=9;f->hi[0]=f->hi[1]=40;f->hi[2]=39;
    char panel[512];snprintf(panel,sizeof panel,"{\"id\":\"board\",\"version\":1,\"kind\":\"panel\",\"name\":\"board\",\"width\":100,\"length\":100,\"thickness\":\"%s\"}",thickness);
    if(!f->parameters||!parameters(f)||!parse(f,panel,0,NULL)||
       !parse(f,"{\"id\":\"timber\",\"version\":1,\"kind\":\"timber\",\"name\":\"timber\",\"A\":27,\"B\":32}",0,NULL)||
       !parse(f,"{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":{\"parameterId\":90,\"fieldId\":1},\"pattern\":\"stagger\",\"stagger\":{\"axis\":\"u\",\"value\":{\"parameterId\":90,\"fieldId\":2}},\"threshold\":{\"parameterId\":90,\"fieldId\":3}}",1,&f->state.fills[0])||
       !parse(f,"{\"id\":10,\"fillId\":1,\"h\":{\"kind\":\"spec\",\"name\":\"depth\"}}",2,&f->state.hosts[0]))return NULL;
    f->state.fill_count=f->state.host_count=1;f->placements[0].id=10;f->placements[0].derived_fill_id=1;f->placements[1].id=11;f->placements[1].derived_fill_id=2;return f;
}
static Fixture *fixture(void){return fixture_thickness("9.000");}
static bool attach(Fixture *f)
{
    f->graph=geo_eval_create(261,73);if(!f->graph)return false;
    GeoSourceProvider provider={FS_NAMED,"core.named-value","finish-test-named/1",f,named_describe,named_evaluate};
    if(!geo_eval_register(f->graph,&provider))return false;
    f->parameter_sources=geo_parameter_sources_register(f->graph,f->parameters,FS_PARAMETER,"core.parameter.field","finish-test-parameter/1");
    f->engineering_sources=wood_engineering_sources_register(f->graph,&f->context.finish.engineering,(WoodEngineeringSourceTokens){FS_DIMENSION,FS_BINDING,FS_DEFINITION,FS_NAMED,FS_PARAMETER});
    if(!f->parameter_sources||!f->engineering_sources)return false;wood_engineering_sources_bind(f->engineering_sources,&f->context.finish.engineering);
    f->sources=wood_finish_sources_create(f->graph,(WoodFinishSourceTokens){FS_SOURCE,FS_PARAMETER},&f->context);
    return f->sources&&wood_finish_sources_bind(f->sources,&f->context);
}
static void dispose(Fixture *f,bool graph_first)
{if(!f)return;if(graph_first)geo_eval_destroy(f->graph);wood_finish_sources_destroy(f->sources);wood_engineering_sources_destroy(f->engineering_sources);geo_parameter_sources_destroy(f->parameter_sources);if(!graph_first)geo_eval_destroy(f->graph);geo_parameters_destroy(f->parameters);geo_versions_destroy(f->versions);free(f);}
static bool edge_indices(const GeoEvalContext *g,size_t from,size_t to,GeoDependencyKind relation)
{for(size_t i=0;i<geo_eval_edge_count(g);++i){GeoSourceEdge edge;if(geo_eval_edge_at(g,i,&edge)&&edge.consumer==from&&edge.source==to&&edge.kind==relation)return true;}return false;}
static bool edge(Fixture *f,WoodFinishSourceKind a,uint32_t aid,WoodFinishSourceKind b,uint32_t bid,GeoDependencyKind relation)
{return edge_indices(f->graph,source_index(f->graph,a,aid),source_index(f->graph,b,bid),relation);}
static size_t parameter_index(Fixture *f,uint32_t field)
{for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;uint32_t key[2];if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==FS_PARAMETER&&n.source.key_size==sizeof key){memcpy(key,n.source.key,sizeof key);if(key[0]==90&&key[1]==field)return i;}}return SIZE_MAX;}
static bool get(Fixture *f,WoodFinishSourceKind kind,uint32_t id,GeoSourceValue *out)
{WoodFinishSourceKey key;return geo_eval_source(f->graph,wood_finish_source_ref(FS_SOURCE,kind,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}
static bool exact_derived(const WoodDerivedValue *p,GeoCoord depth)
{
    static const GeoPoint2 outer[]={{0,0},{100,0},{100,100},{0,100}},hole[]={{20,20},{20,40},{40,40},{40,20}};
    if(p->id!=10||p->derived_fill_id!=1||p->derived_h!=depth||p->frame.origin.z!=9||p->component_count!=1)return false;
    const WoodBoundaryRegion *r=&p->components[0];if(r->outline.count!=4||r->hole_count!=1||r->holes[0].count!=4||memcmp(r->outline.v,outer,sizeof outer)||memcmp(r->holes[0].v,hole,sizeof hole))return false;
    for(size_t i=0;i<4;++i)if(r->outline.fixity[i]!=WOOD_EDGE_FIXED||r->holes[0].fixity[i]!=WOOD_EDGE_FIXED)return false;return true;
}
static int graph_case(void)
{
    Fixture *f=fixture(),*plain=fixture();CHECK(f&&plain&&attach(f),"graph-fixtures");WoodDerivedValue value;
    CHECK(wood_finish_sources_read_derived(f->sources,10,&value)&&exact_derived(&value,30)&&f->writes==0,"derived-query-runs-policy-before-any-cache-write");
    CHECK(wood_dp_rebuild(&f->context)&&wood_dp_rebuild(&plain->context)&&exact_derived(&f->placements[0],30)&&!memcmp(&f->placements[0],&plain->placements[0],sizeof value),"numeric-geometry-and-no-hook-parity");
    CHECK(edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_H,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_FILL_FRAME,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_FRAME,10,GEO_DEPENDENCY_VALUE_REQUIRED),"derived-actual-input-edges");
    CHECK(edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_PANEL_THICKNESS,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_PANEL_THICKNESS,1,WOOD_FINISH_SOURCE_PANEL_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED),"panel-field-dependency-edge");
    CHECK(edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_FRAME,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_GAP,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_STAGGER,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_THRESHOLD,1,GEO_DEPENDENCY_VALUE_REQUIRED),"fill-active-value-edges");
    CHECK(edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_BEAM_BOX,20,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_BOUNDARY_REGION,8,GEO_DEPENDENCY_VALUE_REQUIRED)&&f->active_failures==0,"geometry-callbacks-inside-active-sources");
    GeoSourceValue d;CHECK(get(f,WOOD_FINISH_SOURCE_FILL_DEFINITION,1,&d)&&d.kind==GEO_SOURCE_DEFINITION&&d.as.definition.content_size==strlen(f->state.fills[0].definition)&&!memcmp(d.as.definition.content,f->state.fills[0].definition,d.as.definition.content_size),"canonical-definition-content");
    CHECK(get(f,WOOD_FINISH_SOURCE_PANEL_DEFINITION,1,&d)&&d.kind==GEO_SOURCE_DEFINITION,"panel-definition-value");
    GeoVersionView panel;CHECK(wood_eng_version_view(&f->context.finish.engineering,0,"board",1,&panel)&&d.as.definition.content==panel.content&&d.as.definition.content_size==panel.content_length,"panel-definition-borrows-actual-k-version");
    size_t material=SIZE_MAX;for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==FS_DEFINITION&&n.value&&n.value->kind==GEO_SOURCE_DEFINITION&&n.value->as.definition.content_size==panel.content_length&&!memcmp(n.value->as.definition.content,panel.content,panel.content_length))material=i;}
    CHECK(edge_indices(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_PANEL_DEFINITION,1),material,GEO_DEPENDENCY_DEFINITION_REQUIRED),"panel-shared-material-definition-edge");
    CHECK(get(f,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,10,&d)&&d.kind==GEO_SOURCE_DEFINITION&&d.as.definition.content_size==strlen(f->state.hosts[0].definition)&&!memcmp(d.as.definition.content,f->state.hosts[0].definition,d.as.definition.content_size),"derived-canonical-definition-content");
    CHECK(get(f,WOOD_FINISH_SOURCE_DEFINITION,1,&d)&&strstr(d.as.definition.content,"id=1;boundary=8;side=1;")&&strstr(d.as.definition.content,";obstacles=1;1:20"),"finish-owned-deterministic-definition");
    CHECK(edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"derived-definition-edge");
    unsigned calls=f->boundary_calls+f->box_calls+f->parameter_calls+f->named_calls;
    CHECK(geo_eval_seal(f->graph)&&wood_finish_sources_read_derived(f->sources,10,&value)&&exact_derived(&value,30)&&calls==f->boundary_calls+f->box_calls+f->parameter_calls+f->named_calls,"sealed-memoized-derived-query");
    dispose(f,false);dispose(plain,true);return 0;
}
static int shared_case(void)
{
    Fixture *f=fixture();CHECK(f,"shared-fixture");CHECK(parse(f,"{\"id\":10,\"fillId\":1,\"h\":{\"kind\":\"parameter\",\"parameterId\":90,\"fieldId\":4}}",2,&f->state.hosts[0])&&attach(f)&&wood_dp_rebuild(&f->context)&&exact_derived(&f->placements[0],30),"shared-actual-parameter-height");
    CHECK(edge_indices(f->graph,parameter_index(f,4),parameter_index(f,1),GEO_DEPENDENCY_VALUE_REQUIRED),"shared-parameter-ast-edge");
    CHECK(edge_indices(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_GAP,1),parameter_index(f,1),GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge_indices(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_STAGGER,1),parameter_index(f,2),GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge_indices(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_THRESHOLD,1),parameter_index(f,3),GEO_DEPENDENCY_VALUE_REQUIRED),"shared-parameter-field-edges");
    size_t parameters_count=0;for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;geo_eval_node_at(f->graph,i,&n);if(n.source.provider==FS_PARAMETER)++parameters_count;}
    CHECK(parameters_count==4,"shared-parameter-identity-memoizes");dispose(f,true);return 0;
}
static int lifetime_case(void)
{
    Fixture *a=fixture(),*b=fixture();CHECK(a&&b,"lifetime-fixtures");b->depth=32;CHECK(attach(a)&&attach(b),"lifetime-bindings");
    CHECK(!wood_finish_sources_bind(a->sources,&b->context)&&!wood_finish_sources_bind_finish(a->sources,&b->context.finish),"bind-rejects-other-candidate");
    WoodFinishContext copied=a->context.finish;copied.parameter_coord=NULL;CHECK(!wood_finish_sources_bind_finish(a->sources,&copied),"bind-rejects-other-callback");
    copied=a->context.finish;CHECK(wood_finish_sources_bind_finish(a->sources,&copied),"bind-finish-only-same-candidate");
    GeoSourceValue ar,br;CHECK(get(a,WOOD_FINISH_SOURCE_DERIVED_REGION,10,&ar)&&get(b,WOOD_FINISH_SOURCE_DERIVED_REGION,10,&br),"independent-candidates-evaluate");
    const GeoRegionView *borrowed=ar.as.regions.regions;CHECK(borrowed&&borrowed!=br.as.regions.regions&&borrowed[0].holes[0].v[0].u==20,"borrowed-regions-owned-per-handle");
    GeoSourceValue frame;CHECK(get(a,WOOD_FINISH_SOURCE_DERIVED_FRAME,10,&frame)&&frame.as.frame.origin.z==9&&borrowed[0].holes[0].v[0].u==20,"region-view-stable-across-queries");
    WoodFinishSourceKey key;GeoSourceRef ref=wood_finish_source_ref(FS_SOURCE,WOOD_FINISH_SOURCE_DERIVED_FRAME,0x01020304,&key);WoodFinishSourceKind kind;uint32_t id;
    CHECK(ref.key_size==5&&!memcmp(key.bytes,(unsigned char[]){19,1,2,3,4},5)&&wood_finish_source_decode(&ref,&kind,&id)&&kind==WOOD_FINISH_SOURCE_DERIVED_FRAME&&id==0x01020304,"stable-big-endian-source-key");
    ref.key_size=4;CHECK(!wood_finish_source_decode(&ref,&kind,&id),"malformed-key-rejected");dispose(a,false);dispose(b,true);return 0;
}
static int diagnostic_case(void)
{
    const char *messages[]={"D4: derived placement variant or identity missing","I35: named dimension spec is missing","I55/D4: derived placement 10 source fill is missing","I52: panel-fill thickness must be explicitly set positive integer mm in D1; no rounding"};
    for(int which=0;which<4;++which){Fixture *f=fixture_thickness(which==3?"9.25":"9.000"),*p=fixture_thickness(which==3?"9.25":"9.000");CHECK(f&&p,"diagnostic-fixtures");Fixture *all[]={f,p};
        for(int k=0;k<2;++k){Fixture *x=all[k];x->diagnostic=FS_DIAGNOSTIC_CAPACITY;x->state.fills[0].threshold.field_id=99;
            if(which<=2)x->state.hosts[0].fill_id=99;if(which<=1)x->named_ok=false;if(which==0)x->placements[0].derived_fill_id=0;}
        CHECK(attach(f)&&!wood_dp_rebuild(&f->context)&&!wood_dp_rebuild(&p->context),"both-policies-reject");
        CHECK(!strcmp(f->error,messages[which])&&!strcmp(f->error,p->error)&&f->diagnostic==p->diagnostic&&f->writes==0&&p->writes==0,"original-first-error-and-diagnostic-parity");
        strcpy(f->error,"unrelated later error");CHECK(!wood_dp_rebuild(&f->context)&&!strcmp(f->error,messages[which]),"failed-policy-retries-original-diagnostic");dispose(f,false);dispose(p,true);
    }
    Fixture *f=fixture(),*p=fixture();CHECK(f&&p,"partial-write-fixtures");Fixture *all[]={f,p};
    for(int i=0;i<2;++i){all[i]->state.hosts[1]=all[i]->state.hosts[0];all[i]->state.hosts[1].id=11;all[i]->state.hosts[1].fill_id=99;all[i]->state.host_count=2;}
    CHECK(attach(f)&&!wood_dp_rebuild(&f->context)&&!wood_dp_rebuild(&p->context)&&f->writes==1&&p->writes==1&&!strcmp(f->error,p->error)&&exact_derived(&f->placements[0],30),"original-ordered-partial-writes");dispose(f,false);dispose(p,true);return 0;
}
static int finish_case(void)
{
    Fixture *f=fixture(),*p=fixture();CHECK(f&&p&&attach(f),"finish-fixtures");char a[512],b[512];
    CHECK(wood_fs_rebuild(&f->context.finish,a,sizeof a)&&wood_fs_rebuild(&p->context.finish,b,sizeof b),"finish-rebuild-success");
    CHECK(edge(f,WOOD_FINISH_SOURCE_CHECK,1,WOOD_FINISH_SOURCE_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_CHECK,1,WOOD_FINISH_SOURCE_BOUNDARY_REGION,8,GEO_DEPENDENCY_VALUE_REQUIRED)&&
          edge(f,WOOD_FINISH_SOURCE_CHECK,1,WOOD_FINISH_SOURCE_BEAM_BOX,20,GEO_DEPENDENCY_VALUE_REQUIRED)&&f->active_failures==0,"finish-validation-real-geometry-dependencies");
    WoodFinishLayout d={0},plain={0};CHECK(wood_pf_values(&f->context.finish,&f->state.fills[0],&d)&&wood_pf_values(&p->context.finish,&p->state.fills[0],&plain)&&d.t==9&&d.layout.gap==3&&d.layout.stagger==20&&!d.cuts[0]&&plain.t==d.t,"fill-direct-policy-exact-scalars");
    dispose(f,true);dispose(p,false);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"graph"))return graph_case();
    if(!strcmp(argv[1],"shared"))return shared_case();
    if(!strcmp(argv[1],"lifetime"))return lifetime_case();
    if(!strcmp(argv[1],"diagnostics"))return diagnostic_case();
    if(!strcmp(argv[1],"finish"))return finish_case();
    return 2;
}
