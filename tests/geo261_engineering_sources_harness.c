/* The default build is an isolated W/K client. The product build includes the
 * real bridge and links the same W resolver objects; no private graph-key
 * layout or synthetic product callback is copied into this witness. */
#ifdef GEO261_ENGINEERING_PRODUCT
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#else
#include "engineering_sources.h"
#include "parameter_sources.h"
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ES_CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
static const char es_panel_json[]="{\"id\":\"p\",\"version\":1,\"kind\":\"panel\",\"name\":\"Panel\",\"width\":100,\"length\":200,\"thickness\":\"6.50\"}";
static const char es_member_json[]="{\"id\":\"t\",\"version\":1,\"kind\":\"timber\",\"name\":\"Member\",\"A\":30,\"B\":40}";
static const char es_method_json[]="{\"id\":\"m\",\"version\":1,\"name\":\"Method\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"primary\":{\"id\":\"t\",\"version\":1}},\"gap\":0,\"longAxis\":\"v\",\"mainAlong\":\"u\"}";
static const char es_app_json[]="{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"m\",\"version\":1}}";
static const char es_override_app_json[]="{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"primary.A\":{\"kind\":\"spec\",\"name\":\"width\"}}}";
static const char es_panel_canonical[]="{\"id\":\"p\",\"kind\":\"panel\",\"length\":200,\"name\":\"Panel\",\"thickness\":\"6.50\",\"version\":1,\"width\":100}";
static const char es_member_canonical[]="{\"A\":30,\"B\":40,\"id\":\"t\",\"kind\":\"timber\",\"name\":\"Member\",\"version\":1}";
static const char es_unused_member_json[]="{\"id\":\"unused\",\"version\":1,\"kind\":\"timber\",\"name\":\"Unused\",\"A\":31,\"B\":41}";
static const char es_unused_member_canonical[]="{\"A\":31,\"B\":41,\"id\":\"unused\",\"kind\":\"timber\",\"name\":\"Unused\",\"version\":1}";
static const char es_orphan_panel_json[]="{\"id\":\"orphan\",\"version\":1,\"kind\":\"panel\",\"name\":\"Unreferenced\",\"width\":70,\"length\":90}";
static const char es_orphan_panel_canonical[]="{\"id\":\"orphan\",\"kind\":\"panel\",\"length\":90,\"name\":\"Unreferenced\",\"version\":1,\"width\":70}";
static const char es_unused_method_json[]="{\"id\":\"unused\",\"version\":1,\"name\":\"Unused\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"boundary\":{\"id\":\"unused\",\"version\":1},\"secondary\":{\"id\":\"t\",\"version\":1}}}";
static const char es_empty_method_json[]="{\"id\":\"empty\",\"version\":1,\"name\":\"Not yet selected\"}";

static bool es_quantity(const GeoSourceNodeView *node,GeoCoord expected)
{return node->state==GEO_NODE_VALID&&node->status==GEO_SOURCE_OK&&node->value&&node->value->kind==GEO_SOURCE_QUANTITY&&
    node->value->as.quantity.num==expected&&node->value->as.quantity.den==1&&node->value->as.quantity.unit==GEO_UNIT_LENGTH;}
static size_t es_binding_node(const GeoEvalContext *ctx,GeoProviderToken token,EngTarget target)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;EngTarget decoded;WoodEngineeringBindingSourceKind kind;
        if(!geo_eval_node_at(ctx,i,&node)||node.source.provider!=token||
           !wood_engineering_binding_source_decode(&node.source,&kind,&decoded,NULL))continue;
        if((kind==WOOD_BINDING_SOURCE_EFFECTIVE||kind==WOOD_BINDING_SOURCE_REQUEST_VALUE)&&wood_eng_same_target(&decoded,&target))return i;}
    return SIZE_MAX;
}
static size_t es_definition_node(const GeoEvalContext *ctx,GeoProviderToken token,const char *schema,const char *content)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;
        if(!geo_eval_node_at(ctx,i,&node)||node.source.provider!=token||node.state!=GEO_NODE_VALID||!node.value||node.value->kind!=GEO_SOURCE_DEFINITION)continue;
        const GeoDefinitionValue *value=&node.value->as.definition;
        if(value->schema&&!strcmp(value->schema,schema)&&value->content_size==strlen(content)&&
            !memcmp(value->content,content,value->content_size))return i;}
    return SIZE_MAX;
}
static bool es_edge(const GeoEvalContext *ctx,size_t consumer,size_t source,GeoDependencyKind kind)
{
    if(consumer==SIZE_MAX||source==SIZE_MAX)return false;
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;
        if(geo_eval_edge_at(ctx,i,&edge)&&edge.consumer==consumer&&edge.source==source&&edge.kind==kind)return true;}
    return false;
}
static size_t es_child(const GeoEvalContext *ctx,size_t consumer,GeoProviderToken provider,GeoDependencyKind kind)
{
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;GeoSourceNodeView node;
        if(geo_eval_edge_at(ctx,i,&edge)&&edge.consumer==consumer&&edge.kind==kind&&geo_eval_node_at(ctx,edge.source,&node)&&node.source.provider==provider)return edge.source;}
    return SIZE_MAX;
}
static bool es_owned_providers(const GeoEvalContext *ctx,WoodEngineeringSourceTokens tokens,const WoodEngineeringSources *owner)
{
    unsigned found=0;
    for(size_t i=0;i<geo_eval_provider_count(ctx);++i){const GeoSourceProvider *provider=geo_eval_provider_at(ctx,i);if(!provider)return false;
        const char *name=provider->token==tokens.dimension?"woodworking.dimension-source":provider->token==tokens.binding?
            "woodworking.dimension-binding":provider->token==tokens.definition?"woodworking.engineering-definition":NULL;
        if(name){if(provider->candidate_state!=owner||strcmp(provider->name_space,name))return false;++found;}}
    return found==3;
}
static int es_material_chain(const GeoEvalContext *ctx,WoodEngineeringSourceTokens tokens,EngTarget target,GeoCoord expected,const char *canonical)
{
    size_t binding=es_binding_node(ctx,tokens.binding,target),definition=es_definition_node(ctx,tokens.definition,"woodworking.material-version/1",canonical);
    GeoSourceNodeView node;ES_CHECK(geo_eval_node_at(ctx,binding,&node)&&es_quantity(&node,expected),"engineering-binding-exact-value");
    ES_CHECK(definition!=SIZE_MAX,"engineering-material-canonical-definition");
    size_t dimension=es_child(ctx,binding,tokens.dimension,GEO_DEPENDENCY_VALUE_REQUIRED);
    /* Hook bypass still yields the exact binding value and canonical material.
     * Its first rejected verdict must be this missing quantity-source edge. */
    ES_CHECK(dimension!=SIZE_MAX&&es_edge(ctx,dimension,definition,GEO_DEPENDENCY_DEFINITION_REQUIRED),"engineering-source-dependency-edge");
    ES_CHECK(geo_eval_node_at(ctx,dimension,&node)&&es_quantity(&node,expected),"engineering-source-quantity-is-actual-memoized-value");return 0;
}

#ifndef GEO261_ENGINEERING_PRODUCT
enum {ES_NAMED=41,ES_PARAMETER=42,ES_DIMENSION=43,ES_BINDING=44,ES_DEFINITION=45};
static const WoodEngineeringSourceTokens es_tokens={ES_DIMENSION,ES_BINDING,ES_DEFINITION,ES_NAMED,ES_PARAMETER};
typedef struct {
    EngineeringState state;
    WoodEngineeringContext context;
    GeoNamedValues *named;
    GeoParameterStore *parameters;
    GeoVersionStore *versions;
    GeoEvalContext *graph;
    GeoParameterSources *parameter_sources;
    WoodEngineeringSources *engineering_sources;
    char error[256];
    WoodEngineeringTargetInfo targets[4];
    GeoCoord written[8];uint32_t written_ids[8];int writes,serial_calls,target_calls,named_evaluations;
    bool serial_ok,derived;
} EsFixture;
static int es_slot(uint32_t id){return id==1?0:id==2?1:id==7?2:id==8?3:-1;}
static bool es_placement(void *opaque,uint32_t id,bool *derived)
{EsFixture *f=opaque;if(derived)*derived=f->derived;return id==10||id==20;}
static bool es_target(void *opaque,const EngTarget *target,WoodEngineeringTargetInfo *out)
{EsFixture *f=opaque;++f->target_calls;int slot=es_slot(target->id);if(slot<0)return false;*out=f->targets[slot];return true;}
static bool es_named(void *opaque,const char *name,GeoCoord *out)
{EsFixture *f=opaque;const GeoNamedValue *value=geo_named_values_find(f->named,name);if(!value)return false;*out=value->value;return true;}
static bool es_parameter(void *opaque,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{
    EsFixture *f=opaque;GeoParameterError issue;
    if(geo_parameters_coordinate(f->parameters,ref,out,&issue))return true;
    snprintf(error,cap,"I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);return false;
}
static bool es_owned(void *opaque,uint32_t id){(void)opaque;(void)id;return false;}
static void es_write(void *opaque,const EngTarget *target,GeoCoord value)
{EsFixture *f=opaque;if(f->writes<8){f->written[f->writes]=value;f->written_ids[f->writes]=target->id;}++f->writes;}
static bool es_serializable(void *opaque,char *error,size_t cap)
{EsFixture *f=opaque;++f->serial_calls;if(!f->serial_ok)snprintf(error,cap,"I10: test record capacity");return f->serial_ok;}
static bool es_publish(EsFixture *f,const char *text,int kind)
{
    GeoJson json;if(!geo_json_parse(&json,text)){geo_json_free(&json);return false;}
    bool ok=kind==0?wood_eng_publish_material(&f->context,&json,0,NULL):kind==1?
        wood_eng_publish_method(&f->context,&json,0,NULL):wood_eng_put_application(&f->context,&json,0);
    geo_json_free(&json);return ok;
}
static bool es_parameter_put(GeoParameterStore *store,uint32_t card_id,uint32_t field_id,const char *expression)
{
    GeoParameterCard card;GeoParameterField field={0};GeoParameterError error;
    geo_parameters_begin_definition(store,card_id,&card);card.count=1;snprintf(card.name,sizeof card.name,"card-%u",card_id);
    field.parameter_id=card_id;field.id=field_id;field.type=GEO_PARAMETER_DIMENSION;strcpy(field.name,"length");strcpy(field.expression,expression);
    return geo_parameters_accept_field(store,&card,&field,0,&error)&&geo_parameters_put(store,&card,&field,&error);
}
static EsFixture *es_fixture(void)
{
    EsFixture *f=calloc(1,sizeof *f);if(!f)return NULL;f->serial_ok=true;
    f->named=geo_named_values_create();f->parameters=geo_parameters_create();
    if(geo_versions_create(&f->versions)!=GEO_VERSION_OK)return NULL;
    f->context=(WoodEngineeringContext){.state=&f->state,.versions=f->versions,.user=f,.error=f->error,.error_capacity=sizeof f->error,
        .placement=es_placement,.target=es_target,.named_value=es_named,.parameter=es_parameter,.member_owned=es_owned,.write_dimension=es_write,.serializable=es_serializable};
    for(int i=0;i<4;++i)f->targets[i]=(WoodEngineeringTargetInfo){10,i>=2?1:-1,false,false,true,true};
    GeoParameterError error;
    if(!f->named||!f->parameters||!geo_named_values_put(f->named,"width",42)||
        !es_parameter_put(f->parameters,3,5,"{\"op\":\"mul\",\"left\":{\"op\":\"ref\",\"parameterId\":4,\"fieldId\":1},\"right\":{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"1\"}}")||
        !es_parameter_put(f->parameters,4,1,"{\"op\":\"literal\",\"num\":\"67\",\"den\":\"3\",\"unit\":\"mm\"}")||
        !geo_parameters_rebuild(f->parameters,&error)||!es_publish(f,es_panel_json,0)||!es_publish(f,es_member_json,0)||
        !es_publish(f,es_method_json,1)||!es_publish(f,es_app_json,2))return NULL;
    return f;
}
static bool es_named_key(const GeoSourceRef *ref,char *name)
{if(ref->provider!=ES_NAMED||!ref->key||ref->key_size>=GEO_NAMED_VALUE_NAME_BYTES)return false;memcpy(name,ref->key,ref->key_size);name[ref->key_size]=0;return true;}
static bool es_named_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    EsFixture *f=opaque;char name[GEO_NAMED_VALUE_NAME_BYTES];if(!es_named_key(ref,name)||!geo_named_values_find(f->named,name))return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;out->context.axis=-1;return true;
}
static bool es_named_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    EsFixture *f=opaque;char name[GEO_NAMED_VALUE_NAME_BYTES];GeoCoord value;
    if(ctx!=f->graph||!es_named_key(ref,name)||!es_named(f,name,&value))return false;
    ++f->named_evaluations;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
}
static bool es_attach(EsFixture *f)
{
    f->graph=geo_eval_create(261,73);if(!f->graph)return false;
    GeoSourceProvider named={ES_NAMED,"core.named-value","engineering-test-native-named/1",f,es_named_describe,es_named_evaluate};
    if(!geo_eval_register(f->graph,&named))return false;
    f->parameter_sources=geo_parameter_sources_register(f->graph,f->parameters,ES_PARAMETER,"core.parameter.field","geo261-parameter-ast-source/1");
    f->engineering_sources=wood_engineering_sources_register(f->graph,&f->context,es_tokens);
    if(!f->parameter_sources||!f->engineering_sources)return false;
    wood_engineering_sources_bind(f->engineering_sources,&f->context);return true;
}
static void es_free(EsFixture *f)
{
    if(!f)return;wood_engineering_sources_destroy(f->engineering_sources);geo_parameter_sources_destroy(f->parameter_sources);
    geo_eval_destroy(f->graph);geo_named_values_destroy(f->named);geo_parameters_destroy(f->parameters);geo_versions_destroy(f->versions);free(f);
}
static EngDimensionSource es_source(int kind,int field,const char *name)
{EngDimensionSource source={0};source.kind=kind;source.field=field;source.version=1;if(name)snprintf(source.ref,sizeof source.ref,"%s",name);return source;}
static int es_plain_parity(EsFixture *graph,EsFixture *plain,bool expected)
{
    ES_CHECK(!plain->context.sources&&!plain->context.resolve_source&&!plain->context.resolve_binding&&!plain->context.depend_definition,"parity-context-has-no-hooks");
    char a[256]={0},b[256]={0};bool graph_ok=wood_engineering_rebuild(&graph->context,a,sizeof a),plain_ok=wood_engineering_rebuild(&plain->context,b,sizeof b);
    ES_CHECK(graph_ok==expected&&plain_ok==expected,"hook-and-no-hook-rebuild-result");
    ES_CHECK(!strcmp(a,b)&&!strcmp(graph->error,plain->error)&&graph->writes==plain->writes&&graph->serial_calls==plain->serial_calls&&
        !memcmp(graph->written,plain->written,sizeof graph->written)&&!memcmp(graph->written_ids,plain->written_ids,sizeof graph->written_ids),"hook-and-no-hook-errors-and-ordered-writes-match");return 0;
}
static int es_material(void)
{
    EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain&&es_attach(f),"material-fixtures");
    EngTarget target={0,1,0,0};EngBinding binding={.target=target,.source=es_source(ENG_MATERIAL,ENG_WIDTH,"p")};
    GeoCoord value=-1,old=-1;char path[256],plain_path[256];
    ES_CHECK(wood_eng_effective(&f->context,&binding,&value,path,sizeof path)&&wood_eng_effective(&plain->context,&binding,&old,plain_path,sizeof plain_path)&&
        value==100&&old==100&&!strcmp(path,"material:p@1.width")&&!strcmp(path,plain_path),"material-exact-value-and-no-hook-path");
    ES_CHECK(es_material_chain(f->graph,es_tokens,target,100,es_panel_canonical)==0,"material-chain");
    ES_CHECK(geo_eval_node_count(f->graph)==4&&geo_eval_edge_count(f->graph)==3,"material-exact-four-nodes-three-edges");
    ES_CHECK(wood_engineering_sources_state(f->engineering_sources)==&f->state&&wood_engineering_sources_context(f->engineering_sources)==f->graph,"material-provider-exact-candidate-state");
    ES_CHECK(es_owned_providers(f->graph,es_tokens,f->engineering_sources),"material-all-registered-providers-share-candidate-binding");
    int calls=f->target_calls;ES_CHECK(wood_eng_effective(&f->context,&binding,&value,path,sizeof path)&&value==100&&f->target_calls==calls,"binding-value-memoization-skips-policy-reentry");
    ES_CHECK(geo_eval_seal(f->graph)&&wood_eng_effective(&f->context,&binding,&value,path,sizeof path)&&value==100&&f->target_calls==calls,"sealed-binding-uses-actual-cache");
    es_free(f);es_free(plain);return 0;
}
static int es_application(void)
{
    EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain,"application-fixtures");EngTarget target={0,1,0,0};EngDimensionSource source=es_source(ENG_APPLICATION,ENG_U_PANEL,"a");
    ES_CHECK(wood_eng_bind(&f->context,&target,&source)&&wood_eng_bind(&plain->context,&target,&source)&&es_attach(f),"application-binding");
    ES_CHECK(es_plain_parity(f,plain,true)==0&&f->writes==1&&f->written[0]==100,"application-exact-published-dimension");
    size_t application=es_definition_node(f->graph,ES_DEFINITION,"woodworking.face-application/1",f->state.applications[0].content);
    size_t method=es_definition_node(f->graph,ES_DEFINITION,"woodworking.method-version/1",f->state.methods[0].content);
    size_t panel=es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_panel_canonical),unused=SIZE_MAX;size_t unused_count=0;
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView node;ES_CHECK(geo_eval_node_at(f->graph,i,&node),"application-node-view");
        if(node.source.provider==ES_DEFINITION&&node.state==GEO_NODE_NEW){unused=i;++unused_count;ES_CHECK(!node.value,"unused-material-identity-has-no-effective-value");}}
    ES_CHECK(application!=SIZE_MAX&&method!=SIZE_MAX&&panel!=SIZE_MAX&&unused_count==1&&
        es_edge(f->graph,application,method,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&es_edge(f->graph,method,panel,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        es_edge(f->graph,method,unused,GEO_DEPENDENCY_DEFINITION_REQUIRED),"application-method-both-material-identities-retained");
    size_t binding=es_binding_node(f->graph,ES_BINDING,target),app_dimension=es_child(f->graph,binding,ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED);
    size_t material_dimension=es_child(f->graph,app_dimension,ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED);
    ES_CHECK(es_edge(f->graph,app_dimension,application,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&es_edge(f->graph,app_dimension,method,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        es_edge(f->graph,material_dimension,panel,GEO_DEPENDENCY_DEFINITION_REQUIRED),"application-selected-value-chain");
    /* Describe an unused identity after perturbing only its legacy cache.
     * Metadata completion must never refresh bytes after candidate hashing. */
    f->state.materials[1].a=777;
    EngineeringState *snapshot=malloc(sizeof *snapshot);ES_CHECK(snapshot,"metadata-snapshot-allocation");memcpy(snapshot,&f->state,sizeof *snapshot);
    GeoSourceNodeView unused_node;GeoSourceDescriptor descriptor;size_t edges=geo_eval_edge_count(f->graph);
    ES_CHECK(geo_eval_node_at(f->graph,unused,&unused_node)&&geo_eval_describe(f->graph,unused_node.source,&descriptor)==GEO_SOURCE_OK&&
        descriptor.kind==GEO_SOURCE_DEFINITION&&descriptor.unit==GEO_UNIT_SCALAR&&!memcmp(snapshot,&f->state,sizeof *snapshot)&&
        geo_eval_edge_count(f->graph)==edges,"definition-description-does-not-refresh-candidate-cache");free(snapshot);
    /* Reveal the unused material through the public resolver, then match its
     * pre-existing identity edge without decoding private definition keys. */
    EngTarget timber={1,7,0,1};source=es_source(ENG_MATERIAL,ENG_B,"t");GeoCoord value;
    ES_CHECK(wood_eng_resolve(&f->context,&source,&timber,10,1,&value,NULL,0)&&value==40&&
        es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_member_canonical)==unused,"retained-unused-identity-is-actual-timber-material");
    ES_CHECK(geo_eval_node_count(f->graph)==9&&geo_eval_edge_count(f->graph)==10,"application-exact-graph-after-public-identity-probe");es_free(f);es_free(plain);return 0;
}
static bool es_override_setup(EsFixture *f,bool object_override)
{
    if(!es_publish(f,es_override_app_json,2))return false;
    EngTarget target={1,7,0,0};EngDimensionSource source=es_source(ENG_APPLICATION,ENG_PRIMARY_A,"a");
    if(!wood_eng_bind(&f->context,&target,&source))return false;
    EngBinding *binding=wood_eng_binding(&f->context,&target);binding->has_override=object_override;binding->override_value.kind=ENG_LITERAL;binding->override_value.value=9;
    target=(EngTarget){0,1,0,0};source=es_source(ENG_APPLICATION,ENG_U_PANEL,"a");if(!wood_eng_bind(&f->context,&target,&source))return false;
    target=(EngTarget){1,8,0,1};source=es_source(ENG_MATERIAL,ENG_B,"t");return wood_eng_bind(&f->context,&target,&source);
}
static int es_overrides(void)
{
    for(int object_override=0;object_override<=1;++object_override){EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain,"override-fixtures");
        ES_CHECK(es_override_setup(f,object_override!=0)&&es_override_setup(plain,object_override!=0)&&es_attach(f),"override-definitions");
        ES_CHECK(es_plain_parity(f,plain,true)==0&&f->writes==3&&f->written[0]==(object_override?9:42)&&f->written[1]==100&&f->written[2]==40,"override-fixed-values-in-original-order");
        size_t app=es_definition_node(f->graph,ES_DEFINITION,"woodworking.face-application/1",f->state.applications[0].content),
            method=es_definition_node(f->graph,ES_DEFINITION,"woodworking.method-version/1",f->state.methods[0].content),
            timber=es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_member_canonical);
        ES_CHECK(es_edge(f->graph,app,method,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&es_edge(f->graph,method,timber,GEO_DEPENDENCY_DEFINITION_REQUIRED),"override-keeps-application-method-base-material-identity");
        EngTarget target={1,7,0,0};size_t binding=es_binding_node(f->graph,ES_BINDING,target),active=es_child(f->graph,binding,ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED);
        GeoSourceNodeView node;ES_CHECK(geo_eval_node_at(f->graph,active,&node)&&es_quantity(&node,object_override?9:42),"override-uses-active-source-quantity");
        GeoCoord value;char path[256];ES_CHECK(wood_eng_effective(&f->context,wood_eng_binding(&f->context,&target),&value,path,sizeof path)&&
            !strcmp(path,object_override?"explicit integer mm":"application:a -> method:m@1 -> face override -> spec:width"),"override-exact-resolution-path");
        if(object_override)ES_CHECK(es_edge(f->graph,binding,app,GEO_DEPENDENCY_DEFINITION_REQUIRED),"object-override-retains-inactive-base-application-identity");
        else{size_t spec=es_child(f->graph,active,ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED);
            ES_CHECK(es_child(f->graph,spec,ES_NAMED,GEO_DEPENDENCY_VALUE_REQUIRED)!=SIZE_MAX,"face-override-selects-shared-named-source");}
        for(size_t i=0;i<geo_eval_node_count(f->graph);++i){ES_CHECK(geo_eval_node_at(f->graph,i,&node),"override-node-view");
            ES_CHECK(node.source.provider!=ES_DIMENSION||!es_quantity(&node,30),"inactive-base-A-is-identity-not-an-active-value");}
        ES_CHECK(f->named_evaluations==1,"shared-face-spec-memoizes-once");es_free(f);es_free(plain);}
    return 0;
}
static size_t es_parameter_node(const GeoEvalContext *ctx,uint32_t card,uint32_t field)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;uint32_t key[2];
        if(geo_eval_node_at(ctx,i,&node)&&node.source.provider==ES_PARAMETER&&node.source.key_size==sizeof key){
            memcpy(key,node.source.key,sizeof key);if(key[0]==card&&key[1]==field)return i;}}
    return SIZE_MAX;
}
static int es_shared(void)
{
    EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain&&es_attach(f),"shared-fixtures");
    for(uint32_t id=1;id<=2;++id){EngTarget target={0,id,0,0};EngBinding binding={.target=target,.source=es_source(id==1?ENG_SPEC:ENG_PARAMETER,0,id==1?"width":NULL)};
        binding.source.parameter=(GeoParameterRef){true,3,5};GeoCoord value,other;char path[256],expected[256];
        ES_CHECK(wood_eng_effective(&f->context,&binding,&value,path,sizeof path)&&wood_eng_effective(&plain->context,&binding,&other,expected,sizeof expected)&&
            value==(id==1?42:67)&&other==value&&!strcmp(path,id==1?"spec:width":"param:3:5")&&!strcmp(path,expected),"shared-source-exact-value-and-no-hook-parity");
        size_t root=es_binding_node(f->graph,ES_BINDING,target),dimension=es_child(f->graph,root,ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED);
        ES_CHECK(es_child(f->graph,dimension,id==1?ES_NAMED:ES_PARAMETER,GEO_DEPENDENCY_VALUE_REQUIRED)!=SIZE_MAX,"shared-K-provider-is-real-dependency");}
    size_t root=es_parameter_node(f->graph,3,5),leaf=es_parameter_node(f->graph,4,1);GeoSourceNodeView node;
    ES_CHECK(es_edge(f->graph,root,leaf,GEO_DEPENDENCY_VALUE_REQUIRED)&&geo_eval_node_at(f->graph,root,&node)&&es_quantity(&node,67),"shared-parameter-native-AST-edge-and-value");
    ES_CHECK(geo_eval_node_at(f->graph,leaf,&node)&&node.value&&node.value->kind==GEO_SOURCE_QUANTITY&&node.value->as.quantity.num==67&&
        node.value->as.quantity.den==3&&node.value->as.quantity.unit==GEO_UNIT_LENGTH,"shared-parameter-retains-exact-fractional-leaf");
    ES_CHECK(geo_parameter_sources_store(f->parameter_sources)==f->parameters&&geo_parameter_sources_context(f->parameter_sources)==f->graph&&
        geo_eval_node_count(f->graph)==9&&geo_eval_edge_count(f->graph)==7&&f->named_evaluations==1,"shared-provider-ownership-and-exact-graph");
    es_free(f);es_free(plain);return 0;
}
static int es_identity_errors(void)
{
    static const char *const errors[]={"I35: named dimension spec is missing","I34: fixed material version is missing",
        "I35: overridden application source is missing or on another placement","D28: overridden source still requires a matching application field/role"};
    for(int which=0;which<4;++which){EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain&&es_attach(f),"identity-error-fixtures");
        EngBinding binding={.target={0,1,0,0},.has_override=true};binding.override_value.kind=ENG_LITERAL;binding.override_value.value=0;
        binding.source=es_source(which==0?ENG_SPEC:which==1?ENG_MATERIAL:ENG_APPLICATION,which==1?ENG_WIDTH:ENG_U_PANEL,which<3?"missing":"a");
        if(which==3)binding.source.field=ENG_V_PANEL;
        GeoCoord value=913,other=913;ES_CHECK(!wood_eng_effective(&f->context,&binding,&value,NULL,0)&&!wood_eng_effective(&plain->context,&binding,&other,NULL,0),"invalid-base-is-not-masked-by-override");
        ES_CHECK(!strcmp(f->error,errors[which])&&!strcmp(plain->error,errors[which])&&value==913&&other==913,"identity-validation-precedes-invalid-override-exact-error");
        ES_CHECK(es_child(f->graph,es_binding_node(f->graph,ES_BINDING,binding.target),ES_DIMENSION,GEO_DEPENDENCY_VALUE_REQUIRED)==SIZE_MAX||which<2,"invalid-application-never-evaluates-override");
        es_free(f);es_free(plain);}
    return 0;
}
static bool es_rebuild_setup(EsFixture *f,int which)
{
    EngTarget target={0,1,0,0};EngDimensionSource source=es_source(ENG_LITERAL,0,NULL);source.value=17;
    if(!wood_eng_bind(&f->context,&target,&source))return false;
    target.id=2;source.value=0;if(!wood_eng_bind(&f->context,&target,&source))return false;
    if(which==0)strcpy(f->state.applications[0].method.id,"missing");
    if(which==2){f->state.bindings[1].source.value=19;f->serial_ok=false;}
    return true;
}
static int es_rebuild_errors(void)
{
    static const char *const errors[]={"I35: application has a dangling placement/method reference",
        "I35: effective dimension violates its positive/nonnegative integer mm range","I10: test record capacity"};
    for(int which=0;which<3;++which){EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain,"rebuild-error-fixtures");
        ES_CHECK(es_rebuild_setup(f,which)&&es_rebuild_setup(plain,which)&&es_attach(f),"rebuild-error-definitions");
        ES_CHECK(es_plain_parity(f,plain,false)==0&&!strcmp(f->error,errors[which]),"rebuild-original-error-order-and-no-hook-parity");
        ES_CHECK(f->writes==which&&f->serial_calls==(which==2?1:0),"rebuild-stops-at-original-validation-phase");
        if(which>=1)ES_CHECK(f->written[0]==17&&f->written_ids[0]==1,"first-cache-write-retained-in-order");
        if(which==2)ES_CHECK(f->written[1]==19&&f->written_ids[1]==2,"final-capacity-follows-second-cache-write");
        es_free(f);es_free(plain);}
    return 0;
}
static int es_binding_codec(void)
{
    EngBinding value={.target={1,0x01020304,0,1},.source={.kind=ENG_LITERAL,.value=-7}};
    unsigned char content[WOOD_ENGINEERING_BINDING_CONTENT_MAX],other[WOOD_ENGINEERING_BINDING_CONTENT_MAX];
    size_t size=wood_engineering_binding_encode(&value,content);
    ES_CHECK(size==50,"binding-canonical-literal-length");
    static const unsigned char expected[50]={
        0,0,0,1,1,2,3,4,0,0,0,0,0,0,0,1,
        0,0,0,0,0,0,0,0,255,255,255,255,255,255,255,249,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
    ES_CHECK(!memcmp(content,expected,sizeof expected),"binding-fixed-canonical-vector");
    EngBinding decoded;memset(&decoded,0xa5,sizeof decoded);
    ES_CHECK(wood_engineering_binding_decode(content,size,&decoded)&&decoded.source.value==-7&&
        wood_eng_same_target(&decoded.target,&value.target)&&!decoded.has_override&&decoded.override_value.value==0,
        "binding-canonical-roundtrip-and-inactive-zero");
    value.override_value.value=999;memset(value.override_value.ref,0xff,sizeof value.override_value.ref);
    ES_CHECK(wood_engineering_binding_encode(&value,other)==size&&!memcmp(content,other,size),"binding-inactive-override-is-not-definition");
    WoodEngineeringBindingSourceKey first,second;GeoSourceRef a=wood_engineering_binding_source_ref(44,WOOD_BINDING_SOURCE_EFFECTIVE,&value,&first);
    value.source.value=23;GeoSourceRef b=wood_engineering_binding_source_ref(44,WOOD_BINDING_SOURCE_EFFECTIVE,&value,&second);
    static const unsigned char stable[17]={2,0,0,0,1,1,2,3,4,0,0,0,0,0,0,0,1};
    ES_CHECK(a.key_size==sizeof stable&&b.key_size==sizeof stable&&!memcmp(a.key,b.key,sizeof stable)&&
        !memcmp(a.key,stable,sizeof stable),"binding-target-key-stable-across-source-change");
    EngTarget target;WoodEngineeringBindingSourceKind kind;
    ES_CHECK(wood_engineering_binding_source_decode(&a,&kind,&target,NULL)&&kind==WOOD_BINDING_SOURCE_EFFECTIVE&&
        wood_eng_same_target(&target,&value.target),"binding-public-key-decoder");
    value.source.value=-7;a=wood_engineering_binding_source_ref(44,WOOD_BINDING_SOURCE_REQUEST_VALUE,&value,&first);
    value.source.value=23;b=wood_engineering_binding_source_ref(44,WOOD_BINDING_SOURCE_REQUEST_VALUE,&value,&second);
    ES_CHECK(a.key_size==51&&b.key_size==51&&memcmp(a.key,b.key,a.key_size),"temporary-key-keeps-full-source-payload");
    ES_CHECK(wood_engineering_binding_source_decode(&b,&kind,&target,&decoded)&&
        kind==WOOD_BINDING_SOURCE_REQUEST_VALUE&&decoded.source.value==23,"temporary-key-public-decodes-payload");
    EngBinding before;memset(&decoded,0xa5,sizeof decoded);memcpy(&before,&decoded,sizeof before);
    for(size_t cut=0;cut<size;++cut)ES_CHECK(!wood_engineering_binding_decode(content,cut,&decoded)&&
        !memcmp(&decoded,&before,sizeof before),"binding-truncation-keeps-output");
    memcpy(other,content,size);other[size]=0;
    ES_CHECK(!wood_engineering_binding_decode(other,size+1,&decoded)&&!memcmp(&decoded,&before,sizeof before),"binding-trailing-byte-rejected");
    memcpy(other,content,size);other[49]=2;
    ES_CHECK(!wood_engineering_binding_decode(other,size,&decoded)&&!memcmp(&decoded,&before,sizeof before),"binding-noncanonical-bool-rejected");
    memset(other,0xa5,sizeof other);memset(value.source.ref,'x',sizeof value.source.ref);
    ES_CHECK(!wood_engineering_binding_encode(&value,other)&&other[0]==0xa5&&other[sizeof other-1]==0xa5,
        "binding-invalid-string-keeps-output");return 0;
}
static int es_binding_identity(void)
{
    EsFixture *first=es_fixture(),*second=es_fixture();ES_CHECK(first&&second,"binding-identity-fixtures");
    EngTarget target={0,1,0,0};EngDimensionSource source={.kind=ENG_LITERAL,.value=17};
    ES_CHECK(wood_eng_bind(&first->context,&target,&source),"binding-first-definition");source.value=23;
    ES_CHECK(wood_eng_bind(&second->context,&target,&source)&&es_attach(first)&&es_attach(second),"binding-second-definition");
    GeoCoord a,b;char path[256];
    ES_CHECK(wood_eng_effective(&first->context,wood_eng_binding(&first->context,&target),&a,path,sizeof path)&&a==17&&
        wood_eng_effective(&second->context,wood_eng_binding(&second->context,&target),&b,path,sizeof path)&&b==23,"binding-fresh-context-values");
    size_t left=es_binding_node(first->graph,ES_BINDING,target),right=es_binding_node(second->graph,ES_BINDING,target);
    GeoSourceNodeView l,r;ES_CHECK(geo_eval_node_at(first->graph,left,&l)&&geo_eval_node_at(second->graph,right,&r)&&
        l.source.key_size==17&&r.source.key_size==17&&!memcmp(l.source.key,r.source.key,17),"binding-real-stable-owned-keys");
    size_t ld=es_child(first->graph,left,ES_BINDING,GEO_DEPENDENCY_DEFINITION_REQUIRED);
    size_t rd=es_child(second->graph,right,ES_BINDING,GEO_DEPENDENCY_DEFINITION_REQUIRED);
    ES_CHECK(geo_eval_node_at(first->graph,ld,&l)&&geo_eval_node_at(second->graph,rd,&r)&&
        l.value&&r.value&&l.value->kind==GEO_SOURCE_DEFINITION&&r.value->kind==GEO_SOURCE_DEFINITION&&
        l.source.key_size==17&&!memcmp(l.source.key,r.source.key,17),"binding-canonical-definition-edge");
    EngBinding old,newer;ES_CHECK(wood_engineering_binding_decode(l.value->as.definition.content,l.value->as.definition.content_size,&old)&&
        wood_engineering_binding_decode(r.value->as.definition.content,r.value->as.definition.content_size,&newer)&&
        old.source.value==17&&newer.source.value==23,"binding-definition-content-tracks-source");
    es_free(first);es_free(second);return 0;
}
static int es_binding_definition_first(void)
{
    EsFixture *f=es_fixture();ES_CHECK(f,"binding-definition-first-fixture");
    EngTarget target={0,1,0,0};EngDimensionSource source={.kind=ENG_LITERAL,.value=17};
    ES_CHECK(wood_eng_bind(&f->context,&target,&source)&&es_attach(f),"binding-definition-first-setup");
    WoodEngineeringBindingSourceKey key;GeoSourceValue definition;
    GeoSourceRef ref=wood_engineering_binding_source_ref(ES_BINDING,WOOD_BINDING_SOURCE_DEFINITION,
        wood_eng_binding(&f->context,&target),&key);
    EngBinding decoded;
    ES_CHECK(geo_eval_source(f->graph,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)==GEO_SOURCE_OK&&
        definition.kind==GEO_SOURCE_DEFINITION&&wood_engineering_binding_decode(definition.as.definition.content,
        definition.as.definition.content_size,&decoded)&&decoded.source.value==17,"binding-definition-first-cached-original");
    EngBinding *stored=wood_eng_binding(&f->context,&target);stored->source.value=23;
    GeoCoord value=997;char path[256];strcpy(path,"sentinel");
    ES_CHECK(!wood_eng_effective(&f->context,stored,&value,path,sizeof path)&&value==997&&!strcmp(path,"sentinel")&&
        !strcmp(f->error,"I8: engineering binding definition changed during evaluation"),"binding-definition-first-stale-rejected");
    ES_CHECK(geo_eval_source(f->graph,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)==GEO_SOURCE_OK&&
        wood_engineering_binding_decode(definition.as.definition.content,definition.as.definition.content_size,&decoded)&&
        decoded.source.value==17,"binding-definition-first-original-retained");
    es_free(f);return 0;
}
static int es_binding_temporary(void)
{
    EsFixture *f=es_fixture();ES_CHECK(f,"binding-temporary-fixture");EngTarget target={0,1,0,0};
    EngDimensionSource source={.kind=ENG_LITERAL,.value=17};
    ES_CHECK(wood_eng_bind(&f->context,&target,&source)&&es_attach(f),"binding-temporary-owned-setup");
    EngBinding owned=*wood_eng_binding(&f->context,&target),request=owned;GeoCoord value;char path[256];
    ES_CHECK(wood_eng_effective(&f->context,&owned,&value,path,sizeof path)&&value==17,"binding-owned-first");
    request.source.value=23;
    ES_CHECK(wood_eng_effective(&f->context,&request,&value,path,sizeof path)&&value==23,"binding-temporary-does-not-alias-owned-target");
    ES_CHECK(wood_eng_effective(&f->context,&owned,&value,path,sizeof path)&&value==17,"binding-owned-after-temporary");
    size_t nodes=geo_eval_node_count(f->graph),edges=geo_eval_edge_count(f->graph);int calls=f->target_calls;
    ES_CHECK(geo_eval_seal(f->graph)&&wood_eng_effective(&f->context,&request,&value,path,sizeof path)&&value==23&&
        wood_eng_effective(&f->context,&owned,&value,path,sizeof path)&&value==17&&f->target_calls==calls&&
        geo_eval_node_count(f->graph)==nodes&&geo_eval_edge_count(f->graph)==edges,"binding-sealed-independent-memoized-values");
    request.source.value=31;value=997;strcpy(path,"sentinel");
    ES_CHECK(!wood_eng_effective(&f->context,&request,&value,path,sizeof path)&&value==997&&!strcmp(path,"sentinel")&&
        geo_eval_node_count(f->graph)==nodes&&geo_eval_edge_count(f->graph)==edges,"binding-sealed-new-request-rejected-without-writes");
    es_free(f);return 0;
}

static bool es_unused_definitions(EsFixture *f)
{
    return es_publish(f,es_unused_member_json,0)&&es_publish(f,es_orphan_panel_json,0)&&
        es_publish(f,es_unused_method_json,1)&&es_publish(f,es_empty_method_json,1);
}
static size_t es_stored_binding_definition(const GeoEvalContext *ctx,EngTarget target,GeoCoord expected,int source_kind)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){
        GeoSourceNodeView node;EngTarget decoded_target;WoodEngineeringBindingSourceKind kind;EngBinding value;
        if(!geo_eval_node_at(ctx,i,&node)||node.source.provider!=ES_BINDING||node.source.key_size!=17||
           !wood_engineering_binding_source_decode(&node.source,&kind,&decoded_target,NULL)||
           kind!=WOOD_BINDING_SOURCE_DEFINITION||!wood_eng_same_target(&decoded_target,&target)||
           node.state!=GEO_NODE_VALID||!node.value||node.value->kind!=GEO_SOURCE_DEFINITION)continue;
        const GeoDefinitionValue *definition=&node.value->as.definition;
        if(strcmp(definition->schema,"woodworking.dimension-binding/2")||
           !wood_engineering_binding_decode(definition->content,definition->content_size,&value))continue;
        if(wood_eng_same_target(&value.target,&target)&&value.source.kind==source_kind&&!value.has_override&&
           (source_kind==ENG_LITERAL?value.source.value==expected:!strcmp(value.source.ref,"width")))return i;
    }
    return SIZE_MAX;
}
static int es_definitions(void)
{
    EsFixture *f=es_fixture();ES_CHECK(f&&es_unused_definitions(f),"definitions-fixture");
    ES_CHECK(es_publish(f,"{\"id\":\"b\",\"placement_id\":20,\"method\":{\"id\":\"m\",\"version\":1}}",2),"definitions-second-application");
    EngTarget first={0,1,0,0},second={0,2,0,0};EngDimensionSource source={.kind=ENG_LITERAL,.value=17};
    ES_CHECK(wood_eng_bind(&f->context,&first,&source),"definitions-first-binding");source=es_source(ENG_SPEC,0,"width");
    ES_CHECK(wood_eng_bind(&f->context,&second,&source),"definitions-second-binding");
    char error[256]={0};ES_CHECK(wood_engineering_rebuild(&f->context,error,sizeof error)&&f->writes==2&&
        f->written_ids[0]==1&&f->written[0]==17&&f->written_ids[1]==2&&f->written[1]==42,
        "definitions-original-validation-values-and-order");
    EngineeringState *before=malloc(sizeof *before);ES_CHECK(before&&es_attach(f),"definitions-attach");memcpy(before,&f->state,sizeof *before);
    int writes=f->writes,calls=f->target_calls,serial=f->serial_calls;
    uint32_t unused_key[]={4,1};GeoSourceRef unused_ref={ES_PARAMETER,unused_key,sizeof unused_key};
    ES_CHECK(geo_eval_depend(f->graph,unused_ref,GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK,"definitions-unused-fraction-identity");
    ES_CHECK(wood_engineering_sources_definitions(f->engineering_sources),"definitions-inventory-success");
    ES_CHECK(f->writes==writes&&f->target_calls==calls&&f->serial_calls==serial&&f->named_evaluations==0&&
        !memcmp(before,&f->state,sizeof *before)&&!strcmp(error,f->error),"definitions-no-effective-value-or-cache-writes");
    size_t unused=es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_unused_member_canonical);
    ES_CHECK(unused!=SIZE_MAX&&es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_orphan_panel_canonical)!=SIZE_MAX,
        "definitions-unused-material-published");
    size_t method=es_definition_node(f->graph,ES_DEFINITION,"woodworking.method-version/1",f->state.methods[1].content);
    ES_CHECK(method!=SIZE_MAX&&es_definition_node(f->graph,ES_DEFINITION,"woodworking.method-version/1",f->state.methods[2].content)!=SIZE_MAX,
        "definitions-unused-method-published");
    ES_CHECK(es_definition_node(f->graph,ES_DEFINITION,"woodworking.face-application/1",f->state.applications[0].content)!=SIZE_MAX&&
        es_definition_node(f->graph,ES_DEFINITION,"woodworking.face-application/1",f->state.applications[1].content)!=SIZE_MAX,
        "definitions-unselected-application-published");
    ES_CHECK(es_stored_binding_definition(f->graph,first,17,ENG_LITERAL)!=SIZE_MAX&&
        es_stored_binding_definition(f->graph,second,42,ENG_SPEC)!=SIZE_MAX,"definitions-unused-binding-published");
    size_t panel=es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_panel_canonical);
    size_t member=es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_member_canonical);
    ES_CHECK(es_edge(f->graph,method,panel,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
        es_edge(f->graph,method,unused,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&es_edge(f->graph,method,member,GEO_DEPENDENCY_DEFINITION_REQUIRED),
        "definitions-inactive-method-slots-definition-required");
    size_t new_value=es_parameter_node(f->graph,4,1);GeoSourceNodeView node;
    ES_CHECK(geo_eval_node_at(f->graph,new_value,&node)&&node.state==GEO_NODE_NEW&&!node.value,
        "definitions-keeps-unused-value-new");
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){ES_CHECK(geo_eval_node_at(f->graph,i,&node),"definitions-node-view");
        ES_CHECK(node.source.provider!=ES_DIMENSION&&node.source.provider!=ES_NAMED&&
            (i==new_value||(node.value&&node.value->kind==GEO_SOURCE_DEFINITION)),"definitions-never-requests-unused-geometry-values");}
    ES_CHECK(geo_eval_node_count(f->graph)==12&&geo_eval_edge_count(f->graph)==7,"definitions-complete-inventory-counts");
    ES_CHECK(geo_eval_seal(f->graph)&&wood_engineering_sources_definitions(f->engineering_sources)&&
        geo_eval_node_count(f->graph)==12&&geo_eval_edge_count(f->graph)==7,"definitions-sealed-idempotence");
    free(before);es_free(f);return 0;
}
static int es_definitions_after_values(void)
{
    EsFixture *f=es_fixture(),*plain=es_fixture();ES_CHECK(f&&plain&&es_unused_definitions(f)&&es_unused_definitions(plain),"definitions-after-values-fixtures");
    ES_CHECK(es_override_setup(f,true)&&es_override_setup(plain,true)&&es_attach(f)&&es_plain_parity(f,plain,true)==0&&
        f->writes==3&&f->written_ids[0]==7&&f->written[0]==9&&f->written_ids[1]==1&&f->written[1]==100&&
        f->written_ids[2]==8&&f->written[2]==40,"definitions-after-values-original-order-and-values");
    size_t count=geo_eval_node_count(f->graph);GeoSourceNodeView nodes[128];GeoQuantity quantities[128];
    ES_CHECK(count<=sizeof nodes/sizeof nodes[0],"definitions-after-values-snapshot-capacity");
    for(size_t i=0;i<count;++i){ES_CHECK(geo_eval_node_at(f->graph,i,&nodes[i]),"definitions-after-values-snapshot-node");
        if(nodes[i].value&&nodes[i].value->kind==GEO_SOURCE_QUANTITY)quantities[i]=nodes[i].value->as.quantity;}
    EngineeringState *before=malloc(sizeof *before);ES_CHECK(before,"definitions-after-values-snapshot-state");memcpy(before,&f->state,sizeof *before);
    int writes=f->writes,calls=f->target_calls,named=f->named_evaluations,serial=f->serial_calls;
    ES_CHECK(wood_engineering_sources_definitions(f->engineering_sources),"definitions-after-values-complete");
    ES_CHECK(f->writes==writes&&f->target_calls==calls&&f->named_evaluations==named&&f->serial_calls==serial&&
        !memcmp(before,&f->state,sizeof *before),"definitions-after-values-no-reentry-or-mutation");
    for(size_t i=0;i<count;++i)if(nodes[i].value&&nodes[i].value->kind==GEO_SOURCE_QUANTITY){GeoSourceNodeView node;
        ES_CHECK(geo_eval_node_at(f->graph,i,&node)&&node.state==GEO_NODE_VALID&&node.value==nodes[i].value&&
            node.value->kind==GEO_SOURCE_QUANTITY&&node.value->as.quantity.num==quantities[i].num&&
            node.value->as.quantity.den==quantities[i].den&&node.value->as.quantity.unit==quantities[i].unit,
            "definitions-after-values-keeps-memoized-quantities");}
    ES_CHECK(es_definition_node(f->graph,ES_DEFINITION,"woodworking.material-version/1",es_unused_member_canonical)!=SIZE_MAX&&
        es_definition_node(f->graph,ES_DEFINITION,"woodworking.method-version/1",f->state.methods[2].content)!=SIZE_MAX,
        "definitions-after-values-includes-unused-published-content");
    free(before);es_free(f);es_free(plain);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"binding-codec"))return es_binding_codec();
    if(!strcmp(argv[1],"binding-identity"))return es_binding_identity();
    if(!strcmp(argv[1],"binding-definition-first"))return es_binding_definition_first();
    if(!strcmp(argv[1],"binding-temporary"))return es_binding_temporary();
    if(!strcmp(argv[1],"definitions"))return es_definitions();
    if(!strcmp(argv[1],"definitions-after-values"))return es_definitions_after_values();
    if(!strcmp(argv[1],"material"))return es_material();
    if(!strcmp(argv[1],"application"))return es_application();
    if(!strcmp(argv[1],"overrides"))return es_overrides();
    if(!strcmp(argv[1],"shared"))return es_shared();
    if(!strcmp(argv[1],"identity-errors"))return es_identity_errors();
    if(!strcmp(argv[1],"rebuild-errors"))return es_rebuild_errors();
    return 2;
}
#else
static bool es_product_line(const char *line){return feed_line("engineering-source-witness",1,line,&g_world);}
static bool es_product_confirm(void){char line[64];snprintf(line,sizeof line,"confirm %u",g_preview.token);return es_product_line(line);}
static char *es_product_dump(const World *world)
{
    FILE *stream=tmpfile();if(!stream)return NULL;world_dump_dsl(world,stream);if(fflush(stream)){fclose(stream);return NULL;}
    long length=ftell(stream);if(length<0||fseek(stream,0,SEEK_SET)){fclose(stream);return NULL;}
    char *text=malloc((size_t)length+1);if(!text){fclose(stream);return NULL;}
    size_t used=fread(text,1,(size_t)length,stream);if(ferror(stream)){free(text);fclose(stream);return NULL;}
    text[used]=0;fclose(stream);return text;
}
static int es_product_graph(AppWorldCandidate *owner)
{
    GeoCandidate *core=app_candidate_core(owner->control);GeoEvalContext *graph=geo_candidate_sources(core);
    ReferenceEval *host=app_candidate_evaluation_state(owner->control);ES_CHECK(host&&host->world==&owner->after&&host->sources==graph&&geo_eval_is_sealed(graph),"product-engineering-exact-candidate-context");
    ES_CHECK(host->engineering_sources&&wood_engineering_sources_state(host->engineering_sources)==&owner->after.wood.engineering&&
        wood_engineering_sources_context(host->engineering_sources)==graph,"product-engineering-provider-owned-by-after-state");
    WoodEngineeringSourceTokens tokens={APP_SOURCE_ENGINEERING_DIMENSION,APP_SOURCE_ENGINEERING_BINDING,APP_SOURCE_ENGINEERING_DEFINITION,APP_SOURCE_NAMED,APP_SOURCE_PARAMETER};
    ES_CHECK(es_owned_providers(graph,tokens,host->engineering_sources),"product-all-engineering-providers-use-retained-candidate-state");
    EngTarget target={1,1,0,0};ES_CHECK(es_material_chain(graph,tokens,target,30,es_member_canonical)==0,"product-real-material-source-chain");
    size_t binding=es_binding_node(graph,tokens.binding,target),pose=SIZE_MAX;
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;uint32_t id;
        if(geo_eval_node_at(graph,i,&node)&&node.source.provider==APP_SOURCE_MEMBER_POSE&&node.source.key_size==sizeof id){memcpy(&id,node.source.key,sizeof id);if(id==1)pose=i;}}
    ES_CHECK(es_edge(graph,pose,binding,GEO_DEPENDENCY_VALUE_REQUIRED),"actual-member-pose-consumes-memoized-engineering-binding");return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3||strcmp(argv[1],"product"))return 2;memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    ES_CHECK(parse_scene_file(argv[2],&g_world),"product-existing-engineering-scene-dsl");history_clear();g_preview.ready=false;
    World *before=malloc(sizeof *before);ES_CHECK(before,"product-before-memory");memcpy(before,&g_world,sizeof *before);
    char *before_dump=es_product_dump(&g_world);ES_CHECK(before_dump,"product-before-dump");uint64_t revision=g_definition_revision;
    ES_CHECK(g_world.wood.timber_count==1&&g_world.wood.timbers[0].size_a==30&&g_world.wood.timbers[0].size_b==40,"product-fixed-baseline-values");
    ES_CHECK(es_product_line("preview spec x 600")&&g_preview.ready&&g_preview.valid,"product-ready-valid-preview");
    AppWorldCandidate *owner=g_preview.transaction;ES_CHECK(owner,"product-preview-owner");GeoCandidate *core=app_candidate_core(owner->control);
    uint64_t id=geo_candidate_id(core);const void *before_buffer=app_candidate_before(owner->control);void *after_buffer=app_candidate_after(owner->control);
    const GuideLine *guide=geo_guides_find(&owner->after.geo.guide_lines,1);
    ES_CHECK(guide&&guide->offset==600&&owner->after.wood.timbers[0].size_a==30&&owner->after.wood.timbers[0].size_b==40,"product-preview-fixed-values");
    ES_CHECK(es_product_graph(owner)==0,"product-preview-graph");
    ES_CHECK(!memcmp(before,&g_world,sizeof *before)&&g_definition_revision==revision&&geo_candidate_evaluation_generation(core)==1,"product-preview-keeps-live-bytes");
    char *after_dump=es_product_dump(&owner->after);ES_CHECK(after_dump&&strcmp(after_dump,before_dump),"product-real-staged-change");
    ES_CHECK(es_product_confirm()&&g_preview.transaction==owner&&app_candidate_core(owner->control)==core&&geo_candidate_id(core)==id&&
        app_candidate_before(owner->control)==before_buffer&&app_candidate_after(owner->control)==after_buffer&&
        geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_evaluation_generation(core)==2,"product-confirm-revalidates-same-candidate");
    ES_CHECK(es_product_graph(owner)==0&&g_definition_revision==revision+1,"product-published-graph-and-revision");
    char *published=es_product_dump(&g_world);ES_CHECK(published&&!strcmp(published,after_dump),"product-publishes-reviewed-definitions");free(published);
    ES_CHECK(es_product_line("undo"),"product-one-undo");char *restored=es_product_dump(&g_world);
    ES_CHECK(restored&&!strcmp(restored,before_dump),"product-one-undo-restores-whole-definition");
    free(restored);free(after_dump);free(before_dump);free(before);return 0;
}
#endif
