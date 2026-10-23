/* Real W grid algorithms consuming the shared K parameter and region graph.
 * Independent coordinates, exact edges and no-hook failure parity are oracles. */
#include "grid_sources.h"
#include "engineering_sources.h"
#include "parameter_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
enum {GS_REGION=2,GS_NAMED=3,GS_PARAMETER=4,GS_DIMENSION=5,GS_BINDING=6,GS_DEFINITION=7,GS_GRID=15};
typedef struct {
    WoodGridState state;EngineeringState engineering;WoodGridContext context;
    GeoGridStore *store;GeoParameterStore *parameters;GeoVersionStore *versions;
    GeoEvalContext *graph;GeoParameterSources *parameter_sources;WoodEngineeringSources *engineering_sources;WoodGridSources *sources;
    GeoPoint2 points[4];GeoRegionView region;char error[1024],parameter_error[256];
    unsigned host_calls,vertex_calls,coordinate_calls,region_calls,active_failures;
    bool vertex_ok,coordinate_ok;
} Fixture;
static size_t node_index(const GeoEvalContext *g,GeoSourceRef ref)
{for(size_t i=0;i<geo_eval_node_count(g);++i){GeoSourceNodeView n;if(geo_eval_node_at(g,i,&n)&&n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&!memcmp(n.source.key,ref.key,ref.key_size))return i;}return SIZE_MAX;}
static size_t grid_index(Fixture *f,WoodGridSourceKind kind,uint32_t id)
{WoodGridSourceKey key;return node_index(f->graph,wood_grid_source_ref(GS_GRID,kind,id,&key));}
static bool edge_at(Fixture *f,size_t from,size_t to,GeoDependencyKind relation)
{for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;if(geo_eval_edge_at(f->graph,i,&e)&&e.consumer==from&&e.source==to&&e.kind==relation)return true;}return false;}
static bool edge(Fixture *f,WoodGridSourceKind from,uint32_t a,WoodGridSourceKind to,uint32_t b,GeoDependencyKind relation)
{return edge_at(f,grid_index(f,from,a),grid_index(f,to,b),relation);}
static size_t kind_index(Fixture *f,WoodGridSourceKind kind,uint32_t id)
{for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;WoodGridSourceKind k;uint32_t d;if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==GS_GRID&&wood_grid_source_decode(&n.source,&k,&d)&&k==kind&&d==id)return i;}return SIZE_MAX;}
static bool region_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;uint32_t id;if(ref->provider!=GS_REGION||ref->key_size!=sizeof id)return false;memcpy(&id,ref->key,sizeof id);if(id!=8)return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_REGION_SET,.unit=GEO_UNIT_LENGTH,.context={false,0,-1},.retry_failure=true};return true;}
static bool region_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{Fixture *f=user;GeoSourceNodeView node;++f->region_calls;if(graph!=f->graph||!geo_eval_node_at(graph,node_index(graph,*ref),&node)||node.state!=GEO_NODE_ACTIVE)++f->active_failures;out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&f->region,1};return true;}
static bool region_value(Fixture *f,GeoRegionSetView *out)
{if(!f->graph){*out=(GeoRegionSetView){&f->region,1};return true;}uint32_t id=8;GeoSourceValue value;if(geo_eval_source(f->graph,(GeoSourceRef){GS_REGION,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;*out=value.as.regions;return true;}
static bool host(void *user,uint32_t id,WoodGridHost *out)
{
    Fixture *f=user;++f->host_calls;if(id!=9)return false;GeoRegionSetView regions;if(!region_value(f,&regions))return false;
    memset(out,0,sizeof *out);out->id=9;out->boundary_id=8;out->bounds=(GeoRect2){0,0,500,500};out->bounds_valid=true;out->component_count=1;
    out->components[0].outline.count=regions.regions[0].outline.count;memcpy(out->components[0].outline.v,regions.regions[0].outline.v,regions.regions[0].outline.count*sizeof(GeoPoint2));return true;
}
static bool vertex(void *user,uint32_t id,uint32_t key,GeoPoint2 *out)
{Fixture *f=user;++f->vertex_calls;GeoRegionSetView regions;if(!f->vertex_ok||id!=8||key!=1||!region_value(f,&regions))return false;*out=regions.regions[0].outline.v[0];return true;}
static bool coordinate(void *user,GeoParameterRef ref,GeoCoord *out)
{Fixture *f=user;++f->coordinate_calls;if(!f->coordinate_ok){*out=37;snprintf(f->parameter_error,sizeof f->parameter_error,"I38 forced coordinate failure");return false;}GeoParameterError error;bool ok=geo_parameters_coordinate(f->parameters,ref,out,&error);if(!ok)snprintf(f->parameter_error,sizeof f->parameter_error,"I38 missing parameter %u:%u",ref.parameter_id,ref.field_id);return ok;}
static bool engineering_parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *err,size_t cap)
{Fixture *f=user;if(coordinate(user,ref,out))return true;if(err)snprintf(err,cap,"%s",f->parameter_error);return false;}
static bool target(void *user,const EngTarget *target,WoodEngineeringTargetInfo *out)
{Fixture *f=user;const WoodGridApplication *g=wood_grid_find(&f->state,target->id);if(!g||target->kind||target->axis<0||target->axis>1)return false;*out=(WoodEngineeringTargetInfo){.placement_id=g->placement_id,.from_system=g->from_system||g->from_binding,.is_subgrid=g->is_subgrid,.panel_axis=g->axis[target->axis].source==GEO_GRID_SOURCE_BODY_GAP};return true;}
static bool make_parameters(Fixture *f,GeoCoord pitch)
{
    GeoParameterCard card;GeoParameterField fields[2]={0};GeoParameterError error;geo_parameters_begin_definition(f->parameters,90,&card);strcpy(card.name,"grid-values");card.count=2;
    for(size_t i=0;i<2;++i){fields[i].parameter_id=90;fields[i].id=(uint32_t)i+1;fields[i].type=GEO_PARAMETER_DIMENSION;snprintf(fields[i].name,sizeof fields[i].name,"value-%zu",i+1);}
    snprintf(fields[0].expression,sizeof fields[0].expression,"{\"op\":\"literal\",\"num\":\"%lld\",\"den\":\"1\",\"unit\":\"mm\"}",(long long)pitch);
    strcpy(fields[1].expression,"{\"op\":\"div\",\"left\":{\"op\":\"ref\",\"parameterId\":90,\"fieldId\":1},\"right\":{\"op\":\"literal\",\"num\":\"2\",\"den\":\"1\",\"unit\":\"1\"}}");
    for(size_t i=0;i<2;++i)if(!geo_parameters_accept_field(f->parameters,&card,fields,i,&error))return false;
    return geo_parameters_put(f->parameters,&card,fields,&error)&&geo_parameters_rebuild(f->parameters,&error);
}
static Fixture *fixture(GeoCoord pitch)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;f->store=geo_grid_store_create();f->parameters=geo_parameters_create();f->vertex_ok=f->coordinate_ok=true;
    if(!f->store||!f->parameters||geo_versions_create(&f->versions)!=GEO_VERSION_OK||!make_parameters(f,pitch))return NULL;
    f->points[0]=(GeoPoint2){10,20};f->points[1]=(GeoPoint2){500,20};f->points[2]=(GeoPoint2){500,500};f->points[3]=(GeoPoint2){10,500};f->region=(GeoRegionView){.outline={f->points,4}};
    f->context=(WoodGridContext){.state=&f->state,.sources=f->store,.engineering={.state=&f->engineering,.versions=f->versions,.user=f,.error=f->error,.error_capacity=sizeof f->error,.target=target,.parameter=engineering_parameter},.user=f,.host=host,.coordinate=coordinate,.vertex=vertex,.parameter_error=f->parameter_error};
    GeoGridSystem system={.id=1,.rule_count=1,.next_rule_key=8};strcpy(system.name,"lattice");
    for(int a=0;a<2;++a){system.axis[a].source=GEO_GRID_SOURCE_REPEAT;system.axis[a].step=777;system.axis[a].parameters[1]=(GeoParameterRef){true,90,1};}
    system.rules[0]=(GeoGridRule){.key=7,.all_cells=true,.divisions={4,5}};strcpy(system.rules[0].name,"quarters");
    GeoGridBinding binding={.id=2,.boundary_id=8,.system_id=1,.vertex_key=1,.anchor_den={1,1}};
    if(!wood_grid_source_put(&f->context,&system,1)||!geo_grid_bindings_put(f->store,&binding))return NULL;
    f->state.items[0]=(WoodGridApplication){.id=3,.placement_id=9,.from_binding=true,.binding_id=2};
    f->state.items[1]=(WoodGridApplication){.id=4,.placement_id=9,.is_subgrid=true,.parent_id=3,.lattice_cell=true,.divisions={2,2}};
    f->state.items[2]=(WoodGridApplication){.id=5,.placement_id=9};f->state.items[2].axis[0]=(GeoGridAxisDef){.source=GEO_GRID_SOURCE_BODY_GAP,.body=999,.gap=10,.anchor=10,.anchor_explicit=true};f->state.count=3;
    EngBinding *e=&f->engineering.bindings[0];e->target=(EngTarget){0,5,0,0};e->source=(EngDimensionSource){.kind=ENG_PARAMETER,.parameter={true,90,2}};f->engineering.binding_count=1;return f;
}
static bool attach(Fixture *f)
{
    f->graph=geo_eval_create(261,80);if(!f->graph)return false;GeoSourceProvider region={GS_REGION,"core.region","grid-test-region/1",f,region_describe,region_evaluate};if(!geo_eval_register(f->graph,&region))return false;
    f->parameter_sources=geo_parameter_sources_register(f->graph,f->parameters,GS_PARAMETER,"core.parameter.field","grid-test-parameter/1");
    f->engineering_sources=wood_engineering_sources_register(f->graph,&f->context.engineering,(WoodEngineeringSourceTokens){GS_DIMENSION,GS_BINDING,GS_DEFINITION,GS_NAMED,GS_PARAMETER});if(!f->parameter_sources||!f->engineering_sources)return false;wood_engineering_sources_bind(f->engineering_sources,&f->context.engineering);
    f->sources=wood_grid_sources_create(f->graph,(WoodGridSourceTokens){GS_GRID,GS_PARAMETER,GS_BINDING,0},&f->context);return f->sources&&wood_grid_sources_bind(f->sources,&f->context);
}
static void dispose(Fixture *f,bool graph_first)
{if(!f)return;if(graph_first)geo_eval_destroy(f->graph);wood_grid_sources_destroy(f->sources);wood_engineering_sources_destroy(f->engineering_sources);geo_parameter_sources_destroy(f->parameter_sources);if(!graph_first)geo_eval_destroy(f->graph);geo_grid_store_destroy(f->store);geo_parameters_destroy(f->parameters);geo_versions_destroy(f->versions);free(f);}
static bool rect(GeoRect2 value,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{return value.min_u==a&&value.min_v==b&&value.max_u==c&&value.max_v==d;}
static bool get(Fixture *f,WoodGridSourceKind kind,uint32_t id,GeoSourceValue *out)
{WoodGridSourceKey key;return geo_eval_source(f->graph,wood_grid_source_ref(GS_GRID,kind,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}
/* D64: one card (parameter 90) controls both lengths, u repeat and v repeat-panel.
 * The `card` token leaves the numeric slots at the placeholder 1 (a cache). */
static bool card_system(Fixture *f,uint32_t u_field,uint32_t v_field)
{
    GeoGridSystem s={.id=6,.next_rule_key=1,.card_reference={true,90,{u_field,v_field}}};strcpy(s.name,"card");
    s.axis[0]=(GeoGridAxisDef){.source=GEO_GRID_SOURCE_REPEAT,.step=1,.card_length=true};
    s.axis[1]=(GeoGridAxisDef){.source=GEO_GRID_SOURCE_REPEAT_BODY_GAP,.body=1,.gap=10,.anchor_explicit=true,.card_length=true};
    return wood_grid_source_put(&f->context,&s,0);
}
static bool card_field_definition(Fixture *f,uint32_t field)
{
    uint32_t key[]={90,field};size_t node=node_index(f->graph,(GeoSourceRef){GS_PARAMETER,key,sizeof key});GeoSourceNodeView view;
    return edge_at(f,grid_index(f,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,6),node,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        geo_eval_node_at(f->graph,node,&view)&&view.state==GEO_NODE_NEW;
}
static int graph_case(void)
{
    Fixture *f=fixture(100),*plain=fixture(100);CHECK(f&&plain&&attach(f),"graph-fixtures");GeoCoord value=0;size_t total=19;char error[1024]="";
    CHECK(wood_grid_sources_line(f->sources,3,9,0,2,true,false,0,&value,&total,error,sizeof error)&&value==210&&total==19,"line-consumes-real-parameter-and-vertex");
    CHECK(wood_grid_systems_rebuild(&plain->context,error,sizeof error)&&wood_grid_bindings_rebuild(&plain->context,error,sizeof error)&&!memcmp(&f->state.items[0],&plain->state.items[0],sizeof(WoodGridApplication)),"direct-binding-cache-parity");
    CHECK(edge(f,WOOD_GRID_SOURCE_BINDING,2,WOOD_GRID_SOURCE_SYSTEM,1,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_GRID_SOURCE_APPLICATION,3,WOOD_GRID_SOURCE_BINDING,2,GEO_DEPENDENCY_VALUE_REQUIRED),"binding-system-application-edges");
    CHECK(edge(f,WOOD_GRID_SOURCE_SYSTEM,1,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&edge(f,WOOD_GRID_SOURCE_BINDING,2,WOOD_GRID_SOURCE_BINDING_DEFINITION,2,GEO_DEPENDENCY_DEFINITION_REQUIRED),"definition-relation-exact");
    uint32_t parameter[]={90,1},boundary=8;CHECK(edge_at(f,grid_index(f,WOOD_GRID_SOURCE_SYSTEM,1),node_index(f->graph,(GeoSourceRef){GS_PARAMETER,parameter,sizeof parameter}),GEO_DEPENDENCY_VALUE_REQUIRED),"shared-parameter-edge");
    CHECK(edge_at(f,grid_index(f,WOOD_GRID_SOURCE_BINDING,2),node_index(f->graph,(GeoSourceRef){GS_REGION,&boundary,sizeof boundary}),GEO_DEPENDENCY_VALUE_REQUIRED)&&f->active_failures==0,"actual-region-value-edge");
    GeoGridRuleLineRef rule={3,1,7,{1,-1},0,0};GeoRect2 scope;
    CHECK(wood_grid_rule_line(&f->context,&rule,9,&value,&scope,error,sizeof error)&&value==135&&rect(scope,110,-80,210,20),"rule-cell-returned-region-drives-line");
    CHECK(edge_at(f,kind_index(f,WOOD_GRID_SOURCE_RULE_LINE,3),kind_index(f,WOOD_GRID_SOURCE_RULE_CELL,3),GEO_DEPENDENCY_VALUE_REQUIRED),"rule-line-cell-value-edge");
    CHECK(wood_grid_sources_cell(f->sources,4,&scope,error,sizeof error)&&rect(scope,10,20,110,120),"manual-cell-returned-region");
    CHECK(wood_grid_sources_line(f->sources,4,9,0,0,false,false,0,&value,&total,error,sizeof error)&&value==60&&total==1,"child-line-real-subdivision");
    CHECK(edge_at(f,kind_index(f,WOOD_GRID_SOURCE_LINE,4),grid_index(f,WOOD_GRID_SOURCE_CELL,4),GEO_DEPENDENCY_VALUE_REQUIRED),"child-line-cell-value-edge");
    GeoSourceValue definition;CHECK(get(f,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1,&definition)&&definition.kind==GEO_SOURCE_DEFINITION&&definition.as.definition.content_size>100,"canonical-system-definition");
    unsigned callbacks=f->coordinate_calls+f->vertex_calls+f->host_calls;CHECK(geo_eval_seal(f->graph)&&wood_grid_sources_line(f->sources,3,9,0,2,true,false,0,&value,NULL,error,sizeof error)&&value==210&&callbacks==f->coordinate_calls+f->vertex_calls+f->host_calls,"sealed-line-memoization");
    dispose(f,false);dispose(plain,true);return 0;
}
static int engineering_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"engineering-fixture");char error[1024]="";GeoCoord value;
    CHECK(wood_grid_sources_application(f->sources,5,error,sizeof error)&&f->state.items[2].axis[0].body==50,"application-consumes-effective-engineering-binding");
    CHECK(wood_grid_sources_dimension(f->sources,5,0,0,&value,error,sizeof error)&&value==50,"typed-panel-quantity");
    WoodGridSourceKey key;size_t panel=node_index(f->graph,wood_grid_dimension_source_ref(GS_GRID,5,0,0,&key)),binding=SIZE_MAX;
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;WoodEngineeringBindingSourceKind kind;EngTarget target;
        if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==GS_BINDING&&wood_engineering_binding_source_decode(&n.source,&kind,&target,NULL)&&
            kind==WOOD_BINDING_SOURCE_EFFECTIVE&&target.id==5&&target.axis==0&&target.field==0)binding=i;}
    CHECK(edge_at(f,grid_index(f,WOOD_GRID_SOURCE_APPLICATION,5),panel,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge_at(f,panel,binding,GEO_DEPENDENCY_VALUE_REQUIRED),"panel-binding-actual-value-edges");
    uint32_t a[]={90,2},b[]={90,1};CHECK(edge_at(f,node_index(f->graph,(GeoSourceRef){GS_PARAMETER,a,sizeof a}),node_index(f->graph,(GeoSourceRef){GS_PARAMETER,b,sizeof b}),GEO_DEPENDENCY_VALUE_REQUIRED),"transitive-parameter-ast-edge");
    /* D10a: a=10, panel=50, gap=10, k=1 => 10+1*(50+10)+50+5=125. */
    CHECK(wood_grid_sources_line(f->sources,5,9,0,1,false,false,0,&value,NULL,error,sizeof error)&&value==125,"engineering-panel-drives-grid-line");dispose(f,false);return 0;
}
static int diagnostic_case(void)
{
    Fixture *f=fixture(100),*plain=fixture(100);CHECK(f&&plain,"diagnostic-fixture");GeoGridBinding binding=*geo_grid_bindings_find(f->store,2);binding.anchor_num[1]=1;binding.anchor_den[1]=3;
    CHECK(geo_grid_bindings_put(f->store,&binding)&&geo_grid_bindings_put(plain->store,&binding)&&attach(f),"diagnostic-binding");char a[1024]="",b[1024]="";
    CHECK(wood_grid_systems_rebuild(&plain->context,b,sizeof b),"diagnostic-plain-system");WoodGridApplication seed={.id=100,.placement_id=9,.main_along=2};seed.axis[1].body=919;seed.lattice_base[1]=81;seed.lattice_step[1]=82;seed.lattice_index[1]=83;WoodGridApplication x=seed,y=seed;
    CHECK(!wood_grid_binding_cache(&f->context,geo_grid_bindings_find(f->store,2),&x,a,sizeof a)&&!wood_grid_binding_cache(&plain->context,geo_grid_bindings_find(plain->store,2),&y,b,sizeof b)&&!strcmp(a,b)&&!memcmp(&x,&y,sizeof x)&&x.lattice_step[0]==100&&x.lattice_base[1]==81,"failed-binding-preserves-partial-cache-parity");
    unsigned calls=f->vertex_calls;x=seed;strcpy(a,"overwritten diagnostic");CHECK(!wood_grid_binding_cache(&f->context,geo_grid_bindings_find(f->store,2),&x,a,sizeof a)&&f->vertex_calls==calls+1&&!strcmp(a,b)&&!memcmp(&x,&y,sizeof x),"failed-policy-retries-original-diagnostic");
    dispose(f,false);dispose(plain,true);
    f=fixture(100);plain=fixture(100);CHECK(f&&plain,"coordinate-failure-fixtures");f->coordinate_ok=plain->coordinate_ok=false;CHECK(attach(f),"coordinate-failure-attach");
    CHECK(!wood_grid_systems_rebuild(&f->context,a,sizeof a)&&!wood_grid_systems_rebuild(&plain->context,b,sizeof b)&&!strcmp(a,b)&&geo_grid_systems_find(f->store,1)->axis[0].step==geo_grid_systems_find(plain->store,1)->axis[0].step,"coordinate-failure-partial-cache-and-diagnostic");dispose(f,true);dispose(plain,false);return 0;
}
static int failure_output_case(void)
{
    Fixture *f=fixture(100),*plain=fixture(100);CHECK(f&&plain&&attach(f),"failure-output-fixtures");char a[1024]="",b[1024]="";GeoCoord x=777,y=777;size_t nx=99,ny=99;
    CHECK(wood_grid_systems_rebuild(&plain->context,b,sizeof b)&&wood_grid_bindings_rebuild(&plain->context,b,sizeof b),"failure-output-plain");WoodGridHost host_value;CHECK(host(plain,9,&host_value),"failure-output-host");
    CHECK(!wood_grid_sources_line(f->sources,4,9,0,8,false,false,0,&x,&nx,a,sizeof a)&&!wood_grid_line_coord_in(plain->state.items,plain->state.count,&plain->state.items[1],&host_value,0,8,&y,&ny,b,sizeof b)&&x==y&&nx==ny&&nx==1&&!strcmp(a,b),"line-failure-preserves-total-and-output");
    dispose(f,false);dispose(plain,true);return 0;
}
static int child_value_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"child-value-fixture");char error[1024]="";GeoCoord value=0;size_t total=0;
    CHECK(wood_grid_sources_line(f->sources,4,9,0,0,false,false,0,&value,&total,error,sizeof error)&&value==60&&total==1,"child-line-returned-region-drives-subdivision");
    CHECK(edge_at(f,kind_index(f,WOOD_GRID_SOURCE_LINE,4),grid_index(f,WOOD_GRID_SOURCE_CELL,4),GEO_DEPENDENCY_VALUE_REQUIRED),"child-line-cell-value-edge");dispose(f,false);return 0;
}
static int lifetime_case(void)
{
    Fixture *a=fixture(100),*b=fixture(200);CHECK(a&&b&&attach(a)&&attach(b),"lifetime-fixtures");WoodGridContext wrong=b->context;wrong.evaluation=NULL;CHECK(!wood_grid_sources_bind(a->sources,&wrong),"reject-cross-candidate-bind");char error[1024]="";GeoCoord x,y;
    CHECK(wood_grid_sources_line(a->sources,3,9,0,2,false,false,0,&x,NULL,error,sizeof error)&&wood_grid_sources_line(b->sources,3,9,0,2,false,false,0,&y,NULL,error,sizeof error)&&x==210&&y==410,"candidate-values-remain-independent");
    GeoSourceValue defa,defb;CHECK(get(a,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1,&defa)&&get(b,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1,&defb)&&defa.as.definition.content_size==defb.as.definition.content_size&&!memcmp(defa.as.definition.content,defb.as.definition.content,defa.as.definition.content_size),"definitions-exclude-evaluated-parameter-cache");
    WoodGridSourceKey key,again;GeoSourceRef ref=wood_grid_line_source_ref(GS_GRID,3,9,1,INT64_MIN,true,true,INT64_MAX,&key);wood_grid_line_source_ref(GS_GRID,3,9,1,INT64_MIN,true,true,INT64_MAX,&again);WoodGridSourceKind kind;uint32_t id;
    CHECK(!memcmp(&key,&again,sizeof key)&&wood_grid_source_decode(&ref,&kind,&id)&&kind==WOOD_GRID_SOURCE_LINE&&id==3,"canonical-signed-source-key");key.bytes[63]=1;CHECK(!wood_grid_source_decode(&ref,&kind,&id),"reject-noncanonical-key");
    GeoRect2 scope;CHECK(wood_grid_sources_cell(a->sources,4,&scope,error,sizeof error),"borrowed-cell-region");GeoSourceValue cell;CHECK(get(a,WOOD_GRID_SOURCE_CELL,4,&cell)&&cell.as.regions.regions[0].outline.v[2].u==110,"borrowed-region-stable");
    dispose(a,true);dispose(b,false);return 0;
}
static int definitions_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&card_system(f,1,2),"unused-definition-fixture");
    WoodGridState before;memcpy(&before,&f->state,sizeof before);f->coordinate_ok=f->vertex_ok=false;
    CHECK(attach(f),"unused-definition-attach");char error[1024]="sentinel";
    CHECK(wood_grid_sources_definitions(f->sources,error,sizeof error),"unused-definitions-enumerate");
    CHECK(grid_index(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,3)!=SIZE_MAX&&
        grid_index(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,4)!=SIZE_MAX&&
        grid_index(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,5)!=SIZE_MAX,"unused-direct-and-child-definitions-present");
    CHECK(f->host_calls==0&&f->vertex_calls==0&&f->coordinate_calls==0&&f->region_calls==0&&
        !memcmp(&before,&f->state,sizeof before)&&!strcmp(error,"sentinel"),"unused-definitions-do-not-evaluate-or-write-caches");
    CHECK(edge(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,4,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,3,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        edge(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,3,WOOD_GRID_SOURCE_BINDING_DEFINITION,2,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        edge(f,WOOD_GRID_SOURCE_BINDING_DEFINITION,2,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED),"unused-definition-parent-source-edges");
    EngTarget target={0,5,0,0};WoodEngineeringBindingSourceKey key;
    size_t binding=node_index(f->graph,wood_engineering_binding_source_ref(GS_BINDING,WOOD_BINDING_SOURCE_DEFINITION,
        wood_eng_binding(&f->context.engineering,&target),&key));
    GeoSourceNodeView node;CHECK(edge_at(f,grid_index(f,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,5),binding,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        geo_eval_node_at(f->graph,binding,&node)&&node.state==GEO_NODE_NEW,"unused-engineering-binding-definition-edge");
    uint32_t parameter[]={90,1};size_t field=node_index(f->graph,(GeoSourceRef){GS_PARAMETER,parameter,sizeof parameter});
    CHECK(edge_at(f,grid_index(f,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1),field,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        geo_eval_node_at(f->graph,field,&node)&&node.state==GEO_NODE_NEW,"unused-parameter-definition-stays-unevaluated");
    /* D64/R60: both mapped card fields are definition inputs of the unused card system. */
    CHECK(card_field_definition(f,1),"unused-card-definition-requires-field-90:1");
    CHECK(card_field_definition(f,2),"unused-card-definition-requires-field-90:2");
    WoodGridSourceKey rule;size_t index=node_index(f->graph,wood_grid_rule_definition_source_ref(GS_GRID,1,7,&rule));
    CHECK(geo_eval_node_at(f->graph,index,&node)&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
        !strcmp(node.value->as.definition.schema,"wood.grid.rule/1"),"unused-rule-definition-present");
    CHECK(edge_at(f,index,grid_index(f,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,1),GEO_DEPENDENCY_DEFINITION_REQUIRED),"unused-rule-keeps-owner-definition");
    size_t nodes=geo_eval_node_count(f->graph),edges=geo_eval_edge_count(f->graph);
    CHECK(wood_grid_sources_definitions(f->sources,error,sizeof error)&&geo_eval_node_count(f->graph)==nodes&&
        geo_eval_edge_count(f->graph)==edges,"unused-definition-enumeration-idempotent");
    /* A swap changes the mapping (a definition) but not the set of definition inputs. */
    Fixture *g=fixture(100);CHECK(g&&card_system(g,2,1),"swapped-card-fixture");g->coordinate_ok=g->vertex_ok=false;
    CHECK(attach(g)&&wood_grid_sources_definitions(g->sources,error,sizeof error),"swapped-card-definitions-enumerate");
    GeoSourceNodeView mapped,swapped;
    CHECK(geo_eval_node_at(f->graph,grid_index(f,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,6),&mapped)&&mapped.value&&
        geo_eval_node_at(g->graph,grid_index(g,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,6),&swapped)&&swapped.value&&
        (mapped.value->as.definition.content_size!=swapped.value->as.definition.content_size||
         memcmp(mapped.value->as.definition.content,swapped.value->as.definition.content,mapped.value->as.definition.content_size)),"swapped-card-mapping-changes-definition");
    CHECK(card_field_definition(g,1),"swapped-card-definition-requires-field-90:1");
    CHECK(card_field_definition(g,2),"swapped-card-definition-requires-field-90:2");
    CHECK(g->host_calls==0&&g->vertex_calls==0&&g->coordinate_calls==0&&g->region_calls==0,"swapped-card-definitions-do-not-evaluate");
    dispose(f,false);dispose(g,false);return 0;
}
/* I74: evaluating the card system through the graph publishes the effective
 * lengths into the authored store's cache slots; the placeholder 1 must not stay. */
static int card_cache_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&card_system(f,1,2)&&attach(f),"card-cache-fixture");
    const GeoGridSystem *raw=geo_grid_systems_find(f->store,6);
    CHECK(raw&&raw->axis[0].step==1&&raw->axis[1].body==1,"card-cache-placeholder-before-evaluation");
    GeoSourceValue value;CHECK(get(f,WOOD_GRID_SOURCE_SYSTEM,6,&value),"card-cache-system-evaluates-through-graph");
    raw=geo_grid_systems_find(f->store,6);
    CHECK(raw&&raw->axis[0].step==100,"card-cache-u-step-is-card-field-90:1");
    CHECK(raw&&raw->axis[1].body==50,"card-cache-v-panel-is-card-field-90:2");
    CHECK(raw->card_reference.set&&raw->axis[0].card_length&&raw->axis[1].card_length&&
        !raw->axis[0].parameters[1].set&&!raw->axis[1].parameters[2].set,"card-cache-keeps-authored-card-source");
    dispose(f,false);return 0;
}
static int rule_definition_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"rule-definition-fixture");WoodGridSourceKey key;
    GeoSourceRef ref=wood_grid_rule_definition_source_ref(GS_GRID,1,7,&key);unsigned char expected_key[64]={13,0,0,0,1};expected_key[16]=7;
    CHECK(ref.key_size==64&&!memcmp(ref.key,expected_key,64),"rule-definition-independent-key-vector");
    WoodGridSourceKind kind;uint32_t id;CHECK(wood_grid_source_decode(&ref,&kind,&id)&&kind==WOOD_GRID_SOURCE_RULE_DEFINITION&&id==1,"rule-definition-key-decodes");
    key.bytes[63]=1;CHECK(!wood_grid_source_decode(&ref,&kind,&id),"rule-definition-padding-rejected");key.bytes[63]=0;
    GeoSourceValue value;CHECK(geo_eval_source(f->graph,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_DEFINITION&&value.as.definition.content_size==72,"rule-definition-exact-size");
    unsigned char expected[72]={0};expected[7]=1;expected[15]=7;expected[23]=8;memcpy(expected+24,"quarters",8);
    expected[39]=1;expected[55]=4;expected[71]=5;
    CHECK(!memcmp(value.as.definition.content,expected,sizeof expected),"rule-definition-independent-content-vector");
    CHECK(f->host_calls==0&&f->vertex_calls==0&&f->coordinate_calls==0,"rule-definition-no-geometry-evaluation");
    dispose(f,true);return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"definitions"))return definitions_case();if(!strcmp(argv[1],"card-cache"))return card_cache_case();if(!strcmp(argv[1],"rule-definition"))return rule_definition_case();if(!strcmp(argv[1],"graph"))return graph_case();if(!strcmp(argv[1],"engineering"))return engineering_case();if(!strcmp(argv[1],"diagnostics"))return diagnostic_case();if(!strcmp(argv[1],"failure-output"))return failure_output_case();if(!strcmp(argv[1],"child-value"))return child_value_case();if(!strcmp(argv[1],"lifetime"))return lifetime_case();return 2;}
