/* W assembly policy with independent dimensions/geometry and the real K graph.
 * The pose provider consumes returned A/B quantities; I42 reads its BOX value. */
#include "assembly_sources.h"
#include "engineering_sources.h"
#include "parameter_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
enum {AS_NAMED=3,AS_PARAMETER=4,AS_DIMENSION=5,AS_BINDING=6,AS_DEFINITION=7,AS_ASSEMBLY=17,AS_POSE=20};
typedef struct {uint32_t id;WoodAssemblyMember fact;WoodAssemblyDefinition definition;} Item;
typedef struct {
    AssemblyState state;EngineeringState engineering;WoodAssemblyContext context;AsmDiagnostic diagnostic;GeoParameterRef parameter_error;
    GeoEvalContext *graph;GeoParameterStore *parameters;GeoVersionStore *versions;GeoParameterSources *parameter_sources;WoodEngineeringSources *engineering_sources;WoodAssemblySources *sources;
    Item items[16];size_t count;uint32_t writes[32];size_t write_count;
    char error[512];unsigned parameter_calls,named_calls,guide_calls,footprint_calls,pose_calls,active_failures;
    bool parameter_ok,named_ok;uint32_t bad_guide;GeoCoord secondary_shift,depth;
} Fixture;
static char *fixture_text;
static Item *item(Fixture *f,uint32_t id)
{for(size_t i=0;i<f->count;++i)if(f->items[i].id==id)return &f->items[i];return NULL;}
static bool parse(void *user,GeoJson *j,const char *text){(void)user;return geo_json_parse(j,text);}
static bool surface(void *user,uint32_t id){(void)user;return id==1;}
static bool guide(void *user,uint32_t id,WoodAssemblyGuide *out)
{Fixture *f=user;++f->guide_calls;if(id==f->bad_guide||id<1||id>3)return false;*out=(WoodAssemblyGuide){1,id==3?ASM_DIR_U:ASM_DIR_V};return true;}
static bool member(void *user,uint32_t id,WoodAssemblyMember *out)
{Item *p=item(user,id);if(!p)return false;if(out)*out=p->fact;return true;}
static size_t member_count(void *user){Fixture *f=user;return f->count;}
static void allocate(void *user,uint32_t id){Fixture *f=user;f->items[f->count++].id=id;}
static bool remove_member(void *user,uint32_t id)
{Fixture *f=user;Item *p=item(f,id);if(!p)return false;size_t at=(size_t)(p-f->items);memmove(p,p+1,(f->count-at-1)*sizeof *p);memset(&f->items[--f->count],0,sizeof *p);return true;}
static void write_member(void *user,const WoodMember *value,const WoodAssemblyDefinition *definition)
{Fixture *f=user;Item *p=item(f,value->id);p->fact=(WoodAssemblyMember){definition->surface_id,value->role,value->size_a,value->size_b,value->placed};p->definition=*definition;f->writes[f->write_count++]=value->id;}
static bool anchor(void *user,uint32_t id,const WoodAssemblyDefinition *definition)
{Item *p=item(user,id);return p&&!memcmp(&p->definition,definition,sizeof *definition);}
static bool content(void *user,AsmInstance *a,GeoJson *j,int token)
{
    (void)user;char value[ASM_RECORD_MAX],text[ASM_RECORD_MAX];if(!geo_json_canonical(j,token,value,sizeof value))return false;
    int n=snprintf(text,sizeof text,"{\"source\":%s,\"mapping\":[{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u}]}",value,a->member[0],a->timber[0],a->member[1],a->timber[1],a->member[2],a->timber[2]);
    if(n<0||(size_t)n>=sizeof text)return false;GeoJson q;bool ok=geo_json_parse(&q,text)&&geo_json_canonical(&q,0,a->content,sizeof a->content);geo_json_free(&q);return ok;
}
static void drop(void *user,bool rule,uint32_t id){(void)user;(void)rule;(void)id;}
static bool other(void *user,GeoJson *j,int t){(void)user;(void)j;(void)t;return false;}
static bool named(void *user,const char *name,GeoCoord *out)
{Fixture *f=user;++f->named_calls;if(!f->named_ok||strcmp(name,"depth"))return false;*out=f->depth;return true;}
static bool parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{Fixture *f=user;++f->parameter_calls;GeoParameterError detail;if(f->parameter_ok&&geo_parameters_coordinate(f->parameters,ref,out,&detail))return true;f->parameter_error=ref;*out=37;snprintf(error,cap,"I38 DIMENSION: parameter %u field %u",ref.parameter_id,ref.field_id);return false;}
static size_t node_index(Fixture *f,GeoSourceRef ref)
{for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&!memcmp(n.source.key,ref.key,ref.key_size))return i;}return SIZE_MAX;}
static size_t assembly_index(Fixture *f,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub)
{WoodAssemblySourceKey key;return node_index(f,wood_assembly_source_ref(AS_ASSEMBLY,kind,id,version,sub,&key));}
static bool edge(Fixture *f,size_t from,size_t to,GeoDependencyKind relation)
{for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;if(geo_eval_edge_at(f->graph,i,&e)&&e.consumer==from&&e.source==to&&e.kind==relation)return true;}return false;}
static bool named_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(ref->provider!=AS_NAMED||ref->key_size!=5||memcmp(ref->key,"depth",5))return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_QUANTITY,.unit=GEO_UNIT_LENGTH,.context={false,0,-1},.retry_failure=true};return true;}
static bool named_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{Fixture *f=user;(void)ref;GeoCoord n;if(graph!=f->graph||!named(f,"depth",&n))return false;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){n,1,GEO_UNIT_LENGTH};return true;}
static bool pose_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(ref->provider!=AS_POSE||ref->key_size!=sizeof(uint32_t))return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_BOX,.unit=GEO_UNIT_LENGTH,.context={false,0,-1},.retry_failure=true};return true;}
static bool pose_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=user;uint32_t id;memcpy(&id,ref->key,sizeof id);++f->pose_calls;GeoSourceNodeView node;
    if(graph!=f->graph||!geo_eval_node_at(graph,node_index(f,*ref),&node)||node.state!=GEO_NODE_ACTIVE)++f->active_failures;
    Item *p=item(f,id);GeoCoord a,b;if(!p||!p->fact.placed||id<1||id>3||!wood_assembly_sources_owned_dimensions(f->sources,id,&a,&b))return false;
    GeoFrame frame={{id==1?487:id==2?2487:514,id==3?1480:20,0},{1,0,0},{0,1,0},{0,0,1}};
    if(id==3)frame.origin.x+=f->secondary_shift;out->kind=GEO_SOURCE_BOX;out->as.box=(GeoBox3){.frame=frame,.extent={id==3?1973:a,id==3?a:2960,b}};return true;
}
static bool footprint(void *user,uint32_t surface_id,uint32_t id,GeoRect2 *out)
{
    Fixture *f=user;++f->footprint_calls;if(surface_id!=1||id<1||id>3)return false;
    if(!f->graph){*out=id==1?(GeoRect2){487,20,514,2980}:id==2?(GeoRect2){2487,20,2514,2980}:(GeoRect2){514+f->secondary_shift,1480,2487+f->secondary_shift,1520};return true;}
    GeoSourceValue value;if(geo_eval_source(f->graph,(GeoSourceRef){AS_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    GeoBox3 box=value.as.box;*out=(GeoRect2){box.frame.origin.x,box.frame.origin.y,box.frame.origin.x+box.extent[0],box.frame.origin.y+box.extent[1]};return true;
}
static bool parameters(Fixture *f)
{
    GeoParameterCard card;GeoParameterField fields[2]={0};GeoParameterError error;geo_parameters_begin_definition(f->parameters,90,&card);strcpy(card.name,"assembly");card.count=2;
    for(size_t i=0;i<2;++i){fields[i].parameter_id=90;fields[i].id=(uint32_t)i+1;fields[i].type=GEO_PARAMETER_DIMENSION;snprintf(fields[i].name,sizeof fields[i].name,"value-%zu",i+1);}
    strcpy(fields[0].expression,"{\"op\":\"literal\",\"num\":\"20\",\"den\":\"1\",\"unit\":\"mm\"}");
    strcpy(fields[1].expression,"{\"op\":\"mul\",\"left\":{\"op\":\"ref\",\"parameterId\":90,\"fieldId\":1},\"right\":{\"op\":\"literal\",\"num\":\"2\",\"den\":\"1\",\"unit\":\"1\"}}");
    for(size_t i=0;i<2;++i)if(!geo_parameters_accept_field(f->parameters,&card,fields,i,&error))return false;return geo_parameters_put(f->parameters,&card,fields,&error)&&geo_parameters_rebuild(f->parameters,&error);
}
static Fixture *fixture(bool instance)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;f->parameters=geo_parameters_create();f->parameter_ok=f->named_ok=true;f->depth=50;
    if(!f->parameters||geo_versions_create(&f->versions)!=GEO_VERSION_OK||!parameters(f))return NULL;
    f->context=(WoodAssemblyContext){.state=&f->state,.engineering={.state=&f->engineering,.versions=f->versions,.user=f,.error=f->error,.error_capacity=sizeof f->error,.named_value=named,.parameter=parameter},.diagnostic=&f->diagnostic,.parameter_dimension_error=&f->parameter_error,.user=f,.json_parse=parse,.drop_position=drop,.other_operation=other,.surface=surface,.guide=guide,.member=member,.footprint=footprint,.member_count=member_count,.member_capacity=16,.allocate_member=allocate,.remove_member=remove_member,.write_member=write_member,.anchor_matches=anchor,.instance_content=content};
    f->items[0]=(Item){.id=90,.fact={1,WOOD_MEMBER_ROLE_BOUNDARY,20,20,true}};f->items[1]=(Item){.id=91,.fact={1,WOOD_MEMBER_ROLE_BOUNDARY,20,20,true}};f->count=2;
    GeoJson j;if(!geo_json_parse(&j,fixture_text))return NULL;
    bool ok=wood_eng_publish_material(&f->context.engineering,&j,geo_json_member(&j,0,"material"),NULL)&&wood_assembly_publish(&f->context,&j,geo_json_member(&j,0,"rule"),NULL)&&wood_assembly_publish(&f->context,&j,geo_json_member(&j,0,"unusedRule"),NULL)&&wood_assembly_put_binding(&f->context,&j,geo_json_member(&j,0,"binding"))&&wood_assembly_put_binding(&f->context,&j,geo_json_member(&j,0,"incomplete"));
    if(ok&&instance)ok=wood_assembly_generation_operation(&f->context,&j,geo_json_member(&j,0,"create"));geo_json_free(&j);if(!ok)return NULL;return f;
}
static bool attach(Fixture *f)
{
    f->graph=geo_eval_create(261,81);if(!f->graph)return false;GeoSourceProvider providers[]={{AS_NAMED,"core.named-value","assembly-test-named/1",f,named_describe,named_evaluate},{AS_POSE,"wood.member-pose","assembly-test-pose/1",f,pose_describe,pose_evaluate}};
    if(!geo_eval_register_many(f->graph,providers,2))return false;f->parameter_sources=geo_parameter_sources_register(f->graph,f->parameters,AS_PARAMETER,"core.parameter.field","assembly-test-parameter/1");
    f->engineering_sources=wood_engineering_sources_register(f->graph,&f->context.engineering,(WoodEngineeringSourceTokens){AS_DIMENSION,AS_BINDING,AS_DEFINITION,AS_NAMED,AS_PARAMETER});if(!f->parameter_sources||!f->engineering_sources)return false;wood_engineering_sources_bind(f->engineering_sources,&f->context.engineering);
    f->sources=wood_assembly_sources_create(f->graph,AS_ASSEMBLY,&f->context);return f->sources&&wood_assembly_sources_bind(f->sources,&f->context);
}
static void dispose(Fixture *f,bool graph_first)
{if(!f)return;if(graph_first)geo_eval_destroy(f->graph);wood_assembly_sources_destroy(f->sources);wood_engineering_sources_destroy(f->engineering_sources);geo_parameter_sources_destroy(f->parameter_sources);if(!graph_first)geo_eval_destroy(f->graph);geo_parameters_destroy(f->parameters);geo_versions_destroy(f->versions);free(f);}
static bool get(Fixture *f,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,GeoSourceValue *out)
{WoodAssemblySourceKey key;return geo_eval_source(f->graph,wood_assembly_source_ref(AS_ASSEMBLY,kind,id,version,sub,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}
static int graph_case(void)
{
    Fixture *f=fixture(true),*plain=fixture(true);CHECK(f&&plain&&attach(f),"graph-fixtures");char error[512]="";CHECK(wood_assembly_rebuild(&f->context,error,sizeof error)&&wood_assembly_rebuild(&plain->context,error,sizeof error),"binding-policy-rebuild");
    CHECK(wood_assembly_sources_definitions(f->sources)&&f->pose_calls==0&&f->guide_calls==0&&f->footprint_calls==0,"definitions-do-not-eagerly-evaluate-generation");
    CHECK(wood_assembly_generation_prepare(&f->context)&&wood_assembly_generation_prepare(&plain->context)&&f->write_count==3&&!memcmp(f->writes,(uint32_t[]){1,2,3},3*sizeof(uint32_t)),"primary-before-secondary-original-writes");
    for(uint32_t id=1;id<=3;++id){Item *p=item(f,id),*q=item(plain,id);CHECK(p->fact.width==(id==3?40:27)&&p->fact.depth==(id==3?50:33)&&!memcmp(&p->fact,&q->fact,sizeof p->fact)&&!memcmp(&p->definition,&q->definition,sizeof p->definition),"generated-dimensions-and-direct-policy-parity");}
    CHECK(f->pose_calls==0&&f->footprint_calls==0,"generation-does-not-advance-I42");
    CHECK(edge(f,assembly_index(f,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,9,0,0),assembly_index(f,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,8,1,0),GEO_DEPENDENCY_DEFINITION_REQUIRED),"binding-rule-definition-identity-edge");
    CHECK(edge(f,assembly_index(f,WOOD_ASSEMBLY_SOURCE_GENERATED,2,0,89),assembly_index(f,WOOD_ASSEMBLY_SOURCE_GENERATED_A,2,0,89),GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,assembly_index(f,WOOD_ASSEMBLY_SOURCE_GENERATED_A,2,0,89),assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,9,0,41),GEO_DEPENDENCY_VALUE_REQUIRED),"generated-slot-actual-quantity-edges");
    size_t slot=assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,9,0,41);bool engineering_edge=false;for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==AS_DIMENSION&&edge(f,slot,i,GEO_DEPENDENCY_VALUE_REQUIRED))engineering_edge=true;}CHECK(engineering_edge,"slot-shared-engineering-edge");
    uint32_t from[]={90,2},to[]={90,1};CHECK(edge(f,node_index(f,(GeoSourceRef){AS_PARAMETER,from,sizeof from}),node_index(f,(GeoSourceRef){AS_PARAMETER,to,sizeof to}),GEO_DEPENDENCY_VALUE_REQUIRED),"transitive-parameter-ast-edge");
    uint32_t timber=1;GeoSourceValue pose;CHECK(geo_eval_source(f->graph,(GeoSourceRef){AS_POSE,&timber,sizeof timber},GEO_DEPENDENCY_VALUE_REQUIRED,&pose)==GEO_SOURCE_OK&&pose.as.box.extent[0]==27&&pose.as.box.extent[2]==33,"owner-pose-consumes-returned-A-B");
    CHECK(edge(f,node_index(f,(GeoSourceRef){AS_POSE,&timber,sizeof timber}),assembly_index(f,WOOD_ASSEMBLY_SOURCE_GENERATED_A,2,0,11),GEO_DEPENDENCY_VALUE_REQUIRED),"pose-generated-A-edge");
    CHECK(wood_assembly_generation_check(&f->context)&&wood_assembly_generation_check(&plain->context)&&f->active_failures==0,"I42-real-box-contact-policy");
    timber=3;CHECK(edge(f,assembly_index(f,WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK,2,0,0),node_index(f,(GeoSourceRef){AS_POSE,&timber,sizeof timber}),GEO_DEPENDENCY_VALUE_REQUIRED),"I42-actual-pose-value-edge");
    unsigned callbacks=f->parameter_calls+f->named_calls+f->guide_calls+f->footprint_calls+f->pose_calls;CHECK(geo_eval_seal(f->graph)&&wood_assembly_generation_check(&f->context)&&callbacks==f->parameter_calls+f->named_calls+f->guide_calls+f->footprint_calls+f->pose_calls,"sealed-check-memoization");dispose(f,false);dispose(plain,true);return 0;
}
static int definitions_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f),"definition-fixture");CHECK(wood_assembly_sources_definitions(f->sources)&&f->parameter_calls==0&&f->named_calls==0&&f->guide_calls==0&&f->pose_calls==0,"bare-definitions-no-quantity-or-geometry");
    GeoSourceValue value;CHECK(get(f,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,80,1,0,&value)&&value.as.definition.content==wood_assembly_rule(&f->context,80,1)->content,"unused-rule-full-canonical-definition");
    CHECK(get(f,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,10,0,0,&value)&&value.as.definition.content==wood_assembly_binding(&f->context,10)->content,"unused-binding-full-canonical-definition");
    CHECK(get(f,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,10,0,41,&value)&&strstr(value.as.definition.content,"\"A\":null")&&strstr(value.as.definition.content,"\"orientation\":null"),"nullable-slot-canonical-definition");
    CHECK(assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,10,0,41)==SIZE_MAX&&assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_B,10,0,41)==SIZE_MAX,"nullable-fields-not-forced-to-quantity");
    CHECK(get(f,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,2,0,89,&value)&&strstr(value.as.definition.content,"\"mapping\":[")&&strstr(value.as.definition.content,"\"source\":{")&&strstr(value.as.definition.content,"\"memberId\":89"),"generated-definition-full-body-and-mapping");
    char error[512]="";CHECK(wood_assembly_rebuild(&f->context,error,sizeof error)&&!wood_assembly_binding(&f->context,10)->complete&&assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,10,0,41)==SIZE_MAX,"incomplete-binding-remains-legal");dispose(f,false);return 0;
}
static int diagnostic_case(void)
{
    Fixture *f=fixture(false),*plain=fixture(false);CHECK(f&&plain&&attach(f),"diagnostic-fixtures");f->parameter_ok=plain->parameter_ok=false;char a[512]="",b[512]="";
    CHECK(!wood_assembly_rebuild(&f->context,a,sizeof a)&&!wood_assembly_rebuild(&plain->context,b,sizeof b)&&!strcmp(a,b)&&!memcmp(&f->diagnostic,&plain->diagnostic,sizeof f->diagnostic)&&f->diagnostic.kind==1&&f->diagnostic.id==90&&f->diagnostic.field_id==2,"first-slot-error-preserves-anonymous-target-diagnostic");
    CHECK(assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,9,0,17)==SIZE_MAX&&assembly_index(f,WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,10,0,0)==SIZE_MAX,"binding-failure-stops-original-order");
    unsigned calls=f->parameter_calls;strcpy(f->error,"overwritten");CHECK(!wood_assembly_rebuild(&f->context,a,sizeof a)&&!strcmp(a,b)&&f->parameter_calls==calls+1,"failed-binding-retries-original-diagnostic");dispose(f,true);dispose(plain,false);return 0;
}
static int partial_case(void)
{
    Fixture *f=fixture(true),*plain=fixture(true);CHECK(f&&plain&&attach(f),"partial-fixtures");char error[512]="";CHECK(wood_assembly_rebuild(&f->context,error,sizeof error)&&wood_assembly_rebuild(&plain->context,error,sizeof error),"partial-binding-rebuild");f->bad_guide=plain->bad_guide=2;
    CHECK(!wood_assembly_generation_prepare(&f->context)&&!wood_assembly_generation_prepare(&plain->context)&&!strcmp(f->error,plain->error)&&f->write_count==1&&plain->write_count==1&&f->writes[0]==1&&!item(f,2)->fact.placed&&!item(f,3)->fact.placed,"prepare-retains-earlier-primary-write-and-first-error");dispose(f,false);dispose(plain,true);
    f=fixture(true);plain=fixture(true);CHECK(f&&plain&&attach(f),"contact-fixtures");CHECK(wood_assembly_rebuild(&f->context,error,sizeof error)&&wood_assembly_rebuild(&plain->context,error,sizeof error)&&wood_assembly_generation_prepare(&f->context)&&wood_assembly_generation_prepare(&plain->context),"contact-prepare");f->secondary_shift=plain->secondary_shift=1;
    CHECK(!wood_assembly_generation_check(&f->context)&&!wood_assembly_generation_check(&plain->context)&&!strcmp(f->error,plain->error)&&strstr(f->error,"secondary endpoints"),"I42-one-unit-real-box-contact-rejection");dispose(f,true);dispose(plain,false);return 0;
}
static int lifetime_case(void)
{
    Fixture *a=fixture(true),*b=fixture(true);CHECK(a&&b&&attach(a)&&attach(b),"lifetime-fixtures");b->depth=51;WoodAssemblyContext wrong=b->context;wrong.evaluation=NULL;CHECK(!wood_assembly_sources_bind(a->sources,&wrong),"reject-cross-candidate-context");
    CHECK(a->context.engineering.last_terminal!=NULL,"lifetime-terminal-hook-bound");
    wrong=a->context;wrong.engineering.last_terminal=NULL;CHECK(!wood_assembly_sources_bind(a->sources,&wrong),"reject-other-terminal-hook");
    wrong=a->context;CHECK(wood_assembly_sources_bind(a->sources,&wrong),"accept-same-terminal-hook");
    char error[512]="";CHECK(wood_assembly_rebuild(&a->context,error,sizeof error)&&wood_assembly_rebuild(&b->context,error,sizeof error),"candidate-rebuilds");GeoCoord aa,ab,ba,bb;
    CHECK(wood_assembly_sources_owned_dimensions(a->sources,3,&aa,&ab)&&wood_assembly_sources_owned_dimensions(b->sources,3,&ba,&bb)&&aa==40&&ba==40&&ab==50&&bb==51&&a->pose_calls==0&&b->pose_calls==0,"owned-dimensions-isolated-without-pose");
    AsmOwner saved=a->state.owners[0];a->state.owners[0].instance=999;CHECK(!wood_assembly_sources_owned_dimensions(a->sources,saved.timber,&aa,&ab),"invalid-owner-is-safe");a->state.owners[0]=saved;
    WoodAssemblySourceKey key,again;GeoSourceRef ref=wood_assembly_source_ref(AS_ASSEMBLY,WOOD_ASSEMBLY_SOURCE_GENERATED_A,2,0,89,&key);wood_assembly_source_ref(AS_ASSEMBLY,WOOD_ASSEMBLY_SOURCE_GENERATED_A,2,0,89,&again);WoodAssemblySourceKind kind;uint32_t id,version,sub;
    CHECK(!memcmp(&key,&again,sizeof key)&&wood_assembly_source_decode(&ref,&kind,&id,&version,&sub)&&kind==WOOD_ASSEMBLY_SOURCE_GENERATED_A&&id==2&&version==0&&sub==89,"canonical-key-no-values-or-padding");key.bytes[8]=1;CHECK(!wood_assembly_source_decode(&ref,&kind,&id,&version,&sub),"reject-noncanonical-key-fields");
    dispose(a,true);dispose(b,false);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;FILE *file=fopen(argv[2],"rb");if(!file)return 2;fseek(file,0,SEEK_END);long size=ftell(file);rewind(file);fixture_text=malloc((size_t)size+1);if(!fixture_text){fclose(file);return 2;}if(fread(fixture_text,1,(size_t)size,file)!=(size_t)size){fclose(file);free(fixture_text);return 2;}fclose(file);fixture_text[size]=0;
    int result=!strcmp(argv[1],"graph")?graph_case():!strcmp(argv[1],"definitions")?definitions_case():!strcmp(argv[1],"diagnostics")?diagnostic_case():!strcmp(argv[1],"partial")?partial_case():!strcmp(argv[1],"lifetime")?lifetime_case():2;free(fixture_text);return result;
}
