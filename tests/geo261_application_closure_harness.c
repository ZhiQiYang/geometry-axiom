/* Full-mode application checks own validation dependencies, while the APP
 * definition stays metadata-only. The product variant calls actual H/W/K. */
#ifdef GEO261_APPLICATION_CLOSURE_PRODUCT
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#else
#include "engineering_sources.h"
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AC_CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
static const char ac_app_schema[]="woodworking.face-application/1";
static const char ac_check_schema[]="woodworking.face-application-check/1";
static const char ac_range_error[]="I35: effective dimension violates its positive/nonnegative integer mm range";
static const char ac_application[]="{\"id\":\"a\",\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"literal\",\"value\":0},\"primary.A\":{\"kind\":\"spec\",\"name\":\"width\"},\"secondary.B\":{\"field\":\"B\",\"id\":\"t\",\"kind\":\"material\",\"version\":1}},\"placement_id\":10}";
static const char ac_bad_returned_application[]="{\"id\":\"a\",\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"primary.A\":{\"kind\":\"literal\",\"value\":0}},\"placement_id\":10}";
static const char ac_missing_method_application[]="{\"id\":\"a\",\"method\":{\"id\":\"missing\",\"version\":1},\"overrides\":{\"primary.A\":{\"kind\":\"spec\",\"name\":\"width\"}},\"placement_id\":10}";
static size_t ac_schema_node(const GeoEvalContext *ctx,const char *schema)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(ctx,i,&n)&&n.value&&n.value->kind==GEO_SOURCE_DEFINITION&&n.value->as.definition.schema&&
           !strcmp(n.value->as.definition.schema,schema))return i;}
    return SIZE_MAX;
}
static bool ac_edge(const GeoEvalContext *ctx,size_t consumer,size_t source,GeoDependencyKind kind)
{
    if(consumer==SIZE_MAX||source==SIZE_MAX)return false;
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(ctx,i,&e)&&e.consumer==consumer&&e.source==source&&e.kind==kind)return true;}
    return false;
}
static size_t ac_provider_node(const GeoEvalContext *ctx,GeoProviderToken provider,GeoSourceValueKind kind)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(ctx,i,&n)&&n.source.provider==provider&&n.value&&n.value->kind==kind)return i;}
    return SIZE_MAX;
}
static int ac_closure(const GeoEvalContext *ctx,GeoProviderToken dimensions,GeoProviderToken named,GeoProviderToken versions,size_t host)
{
    size_t check=ac_schema_node(ctx,ac_check_schema),app=ac_schema_node(ctx,ac_app_schema);
    AC_CHECK(check!=SIZE_MAX&&app!=SIZE_MAX,"application-check-and-definition-are-distinct");
    AC_CHECK(ac_edge(ctx,check,app,GEO_DEPENDENCY_DEFINITION_REQUIRED),"application-check-consumes-returned-definition");
    AC_CHECK(ac_edge(ctx,check,host,GEO_DEPENDENCY_DEFINITION_REQUIRED),"application-check-host-definition-edge");
    size_t method=ac_schema_node(ctx,"woodworking.method-version/1");
    AC_CHECK(ac_edge(ctx,check,method,GEO_DEPENDENCY_DEFINITION_REQUIRED),"application-check-method-definition-edge");
    unsigned count=0;bool zero=false,seventeen=false,forty=false,named_edge=false;size_t material_dimension=SIZE_MAX;
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;GeoSourceNodeView n;
        if(!geo_eval_edge_at(ctx,i,&edge)||edge.consumer!=check||edge.kind!=GEO_DEPENDENCY_VALUE_REQUIRED||
           !geo_eval_node_at(ctx,edge.source,&n)||n.source.provider!=dimensions)continue;
        AC_CHECK(n.value&&n.value->kind==GEO_SOURCE_QUANTITY&&n.value->as.quantity.unit==GEO_UNIT_LENGTH&&n.value->as.quantity.den==1,
            "application-check-override-has-typed-value");
        ++count;GeoCoord value=n.value->as.quantity.num;zero|=value==0;seventeen|=value==17;forty|=value==40;
        if(value==40)material_dimension=edge.source;
        if(value==17)named_edge=ac_edge(ctx,edge.source,ac_provider_node(ctx,named,GEO_SOURCE_QUANTITY),GEO_DEPENDENCY_VALUE_REQUIRED);
    }
    AC_CHECK(count==3&&zero&&seventeen&&forty,"application-check-all-unused-override-values");
    AC_CHECK(named_edge,"application-check-unused-named-override-edge");
    bool material_edge=false;for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView n;GeoVersionSourceKind kind;GeoVersionIdentity id;uint32_t field;
        if(geo_eval_node_at(ctx,i,&n)&&n.source.provider==versions&&geo_version_source_decode(&n.source,&kind,&id,&field)&&
           kind==GEO_VERSION_SOURCE_FIELD&&field==ENG_B&&id.key_length==2&&((const unsigned char *)id.key)[0]==1&&((const unsigned char *)id.key)[1]=='t')
            material_edge=ac_edge(ctx,material_dimension,i,GEO_DEPENDENCY_VALUE_REQUIRED);}
    AC_CHECK(material_edge,"application-check-unused-material-field-edge");return 0;
}

static bool (*ac_original_evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
static int ac_intercept_mode;
static bool ac_intercept_evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(!ac_original_evaluate(state,ctx,ref,out))return false;
    if(out->kind!=GEO_SOURCE_DEFINITION)return true;
    if(ac_intercept_mode==1&&!strcmp(out->as.definition.schema,ac_app_schema))
        out->as.definition=(GeoDefinitionValue){ac_app_schema,ac_bad_returned_application,strlen(ac_bad_returned_application)};
    if(ac_intercept_mode==6&&!strcmp(out->as.definition.schema,ac_app_schema))
        out->as.definition=(GeoDefinitionValue){ac_app_schema,ac_missing_method_application,strlen(ac_missing_method_application)};
    if(!strcmp(out->as.definition.schema,ac_check_schema)){
        static const char no[]="{\"id\":\"a\",\"valid\":false}",wrong_id[]="{\"id\":\"other\",\"valid\":true}",bad[]="{\"id\":\"a\",\"valid\":1}";
        if(ac_intercept_mode==2)out->as.definition=(GeoDefinitionValue){ac_check_schema,no,strlen(no)};
        if(ac_intercept_mode==3)out->as.definition.schema="wrong.application-check/1";
        if(ac_intercept_mode==4)out->as.definition=(GeoDefinitionValue){ac_check_schema,wrong_id,strlen(wrong_id)};
        if(ac_intercept_mode==5)out->as.definition=(GeoDefinitionValue){ac_check_schema,bad,strlen(bad)};
    }
    return true;
}
static bool ac_intercept(GeoEvalContext *ctx,GeoProviderToken token,int mode)
{
    for(size_t i=0;i<geo_eval_provider_count(ctx);++i){GeoSourceProvider *p=(GeoSourceProvider *)geo_eval_provider_at(ctx,i);
        if(p->token==token){ac_original_evaluate=p->evaluate;ac_intercept_mode=mode;p->evaluate=ac_intercept_evaluate;return true;}}
    return false;
}

#ifndef GEO261_APPLICATION_CLOSURE_PRODUCT
enum {AC_DIMENSION=41,AC_BINDING=42,AC_DEFINITION=43,AC_NAMED=44,AC_PARAMETER=45,AC_VERSION=46,AC_HOST=47};
typedef struct {
    EngineeringState state;WoodEngineeringContext context;GeoVersionStore *versions;GeoEvalContext *graph;
    GeoVersionSources *version_sources;WoodEngineeringSources *sources;GeoCoord named_return;
    bool exists,derived;unsigned placements,named,serial,writes;char names[128],error[256];
} AcFixture;
static bool ac_host_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(ref->key_size!=sizeof(uint32_t))return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1}};return true;}
static bool ac_host_evaluate(void *user,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    AcFixture *f=user;uint32_t id;memcpy(&id,ref->key,sizeof id);if(ctx!=f->graph||id!=10)return false;
    static const char live[]="{\"derived\":false,\"exists\":true}",derived[]="{\"derived\":true,\"exists\":true}",missing[]="{\"derived\":false,\"exists\":false}";
    const char *text=!f->exists?missing:f->derived?derived:live;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"fixture.host/1",text,strlen(text)};return true;
}
static bool ac_raw_placement(void *user,uint32_t id,bool *derived)
{AcFixture *f=user;if(derived)*derived=f->derived;return f->exists&&id==10;}
static bool ac_placement(void *user,uint32_t id,bool *derived)
{
    AcFixture *f=user;++f->placements;if(!f->graph)return ac_raw_placement(user,id,derived);
    GeoSourceValue value;if(geo_eval_source(f->graph,(GeoSourceRef){AC_HOST,&id,sizeof id},GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)!=GEO_SOURCE_OK||
       value.kind!=GEO_SOURCE_DEFINITION||strcmp(value.as.definition.schema,"fixture.host/1"))return false;
    GeoJson json;int exists=0,is_derived=0;bool ok=geo_json_parse_n(&json,value.as.definition.content,value.as.definition.content_size)&&
        geo_json_boolean(&json,geo_json_member(&json,0,"exists"),&exists)&&geo_json_boolean(&json,geo_json_member(&json,0,"derived"),&is_derived);
    geo_json_free(&json);if(ok&&derived)*derived=is_derived!=0;return ok&&exists!=0;
}
static bool ac_raw_named(void *user,const char *name,GeoCoord *out)
{(void)user;(void)name;*out=3;return true;}
static bool ac_named_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(!ref->key||!ref->key_size||ref->key_size>=16)return false;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_QUANTITY,.unit=GEO_UNIT_LENGTH,.context={false,0,-1}};return true;}
static bool ac_named_evaluate(void *user,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    AcFixture *f=user;if(ctx!=f->graph)return false;++f->named;
    size_t n=strlen(f->names);if(n+ref->key_size+2>=sizeof f->names)return false;
    memcpy(f->names+n,ref->key,ref->key_size);f->names[n+ref->key_size]='|';f->names[n+ref->key_size+1]=0;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){f->named_return,1,GEO_UNIT_LENGTH};return true;
}
static bool ac_serial(void *user,char *error,size_t cap)
{AcFixture *f=user;(void)error;(void)cap;++f->serial;return true;}
static void ac_write(void *user,const EngTarget *target,GeoCoord value)
{AcFixture *f=user;(void)target;(void)value;++f->writes;}
static bool ac_publish(AcFixture *f,int kind,const char *text)
{
    GeoJson json;bool ok=geo_json_parse(&json,text);
    if(ok)ok=kind==0?wood_eng_publish_material(&f->context,&json,0,NULL):kind==1?wood_eng_publish_method(&f->context,&json,0,NULL):wood_eng_put_application(&f->context,&json,0);
    geo_json_free(&json);return ok;
}
static AcFixture *ac_fixture(const char *application)
{
    AcFixture *f=calloc(1,sizeof *f);if(!f||geo_versions_create(&f->versions)!=GEO_VERSION_OK)return NULL;
    f->exists=true;f->named_return=17;f->context=(WoodEngineeringContext){.state=&f->state,.user=f,.error=f->error,.error_capacity=sizeof f->error,
        .placement=ac_placement,.named_value=ac_raw_named,.write_dimension=ac_write,.serializable=ac_serial,.versions=f->versions};
    if(!ac_publish(f,0,"{\"id\":\"t\",\"version\":1,\"kind\":\"timber\",\"name\":\"Timber\",\"A\":30,\"B\":40}")||
       !ac_publish(f,1,"{\"id\":\"m\",\"version\":1,\"name\":\"Method\"}")||!ac_publish(f,2,application?application:ac_application))return NULL;
    f->placements=0;f->graph=geo_eval_create(261,19);if(!f->graph)return NULL;
    GeoSourceProvider providers[]={{AC_HOST,"fixture.host","application-host/1",f,ac_host_describe,ac_host_evaluate},
        {AC_NAMED,"core.named-value","application-named/1",f,ac_named_describe,ac_named_evaluate}};
    if(!geo_eval_register_many(f->graph,providers,2))return NULL;
    f->version_sources=geo_version_sources_register(f->graph,f->versions,AC_VERSION);
    f->sources=wood_engineering_sources_register(f->graph,&f->context,(WoodEngineeringSourceTokens){AC_DIMENSION,AC_BINDING,AC_DEFINITION,AC_NAMED,AC_PARAMETER,AC_VERSION});
    if(!f->version_sources||!f->sources)return NULL;wood_engineering_sources_bind(f->sources,&f->context);return f;
}
static void ac_free(AcFixture *f)
{if(f){wood_engineering_sources_destroy(f->sources);geo_version_sources_destroy(f->version_sources);geo_eval_destroy(f->graph);geo_versions_destroy(f->versions);free(f);}}
static bool ac_rebuild(AcFixture *f)
{char error[256];return wood_engineering_rebuild(&f->context,error,sizeof error);}
static int ac_inventory(void)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f,"application-inventory-fixture");
    AC_CHECK(wood_engineering_sources_definitions(f->sources)&&wood_engineering_sources_metadata(f->sources),"application-pure-definition-inventory");
    AC_CHECK(!f->placements&&!f->named&&!f->writes&&!f->serial&&ac_schema_node(f->graph,ac_check_schema)==SIZE_MAX,
        "application-inventory-does-not-run-checks-or-values");
    AC_CHECK(ac_schema_node(f->graph,ac_app_schema)!=SIZE_MAX,"application-inventory-retains-canonical-definition");ac_free(f);return 0;
}
static int ac_no_binding(void)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f&&!f->state.binding_count,"application-no-binding-fixture");
    AC_CHECK(ac_rebuild(f)&&!f->writes&&f->serial==1,"application-no-binding-validation-success");
    int result=ac_closure(f->graph,AC_DIMENSION,AC_NAMED,AC_VERSION,ac_schema_node(f->graph,"fixture.host/1"));if(result)return result;
    AC_CHECK(f->placements==1&&f->named==1,"application-validation-runs-once-in-check");
    size_t nodes=geo_eval_node_count(f->graph),edges=geo_eval_edge_count(f->graph);f->named_return=0;
    AC_CHECK(geo_eval_seal(f->graph)&&ac_rebuild(f)&&f->placements==1&&f->named==1&&f->serial==2&&
        geo_eval_node_count(f->graph)==nodes&&geo_eval_edge_count(f->graph)==edges,"application-check-sealed-memoization");ac_free(f);return 0;
}
static int ac_named_authority(void)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f,"application-named-fixture");f->named_return=0;
    AC_CHECK(!ac_rebuild(f)&&!strcmp(f->error,ac_range_error),"application-unused-returned-named-value-controls-validation");
    AC_CHECK(!f->writes&&!f->serial&&f->placements==1&&f->named==1&&ac_schema_node(f->graph,ac_check_schema)==SIZE_MAX,
        "application-failed-override-never-publishes-check");ac_free(f);return 0;
}
static int ac_returned_definition(void)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f&&ac_intercept(f->graph,AC_DEFINITION,1),"application-returned-definition-fixture");
    AC_CHECK(!ac_rebuild(f)&&!strcmp(f->error,ac_range_error),"application-returned-definition-controls-unused-override");
    AC_CHECK(f->state.applications[0].overrides[3].kind==ENG_SPEC&&!strcmp(f->state.applications[0].overrides[3].ref,"width")&&!f->named,
        "application-returned-definition-keeps-authored-source");ac_free(f);return 0;
}
static int ac_returned_check(int mode)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f&&ac_intercept(f->graph,AC_DEFINITION,mode),"application-returned-check-fixture");
    AC_CHECK(!ac_rebuild(f)&&!f->serial&&!f->writes,"application-returned-check-result-controls-caller");ac_free(f);return 0;
}
static int ac_order(int which)
{
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f&&ac_intercept(f->graph,AC_DEFINITION,6),"application-order-fixture");
    f->derived=which==0;f->exists=which!=1;f->named_return=0;
    AC_CHECK(!ac_rebuild(f)&&!strcmp(f->error,which==0?"D4: derived placements cannot receive D28 face applications":"I35: application has a dangling placement/method reference"),
        "application-original-host-method-error-order");
    AC_CHECK(f->placements==1&&!f->named&&!f->serial&&!f->writes,"application-order-stops-before-unused-overrides");ac_free(f);return 0;
}
static int ac_all_slots(void)
{
    const char *app="{\"id\":\"a\",\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"spec\",\"name\":\"g\"},\"boundary.A\":{\"kind\":\"spec\",\"name\":\"bA\"},\"boundary.B\":{\"kind\":\"spec\",\"name\":\"bB\"},\"primary.A\":{\"kind\":\"spec\",\"name\":\"pA\"},\"primary.B\":{\"kind\":\"spec\",\"name\":\"pB\"},\"secondary.A\":{\"kind\":\"spec\",\"name\":\"sA\"},\"secondary.B\":{\"kind\":\"spec\",\"name\":\"sB\"}},\"placement_id\":10}";
    AcFixture *f=ac_fixture(app);AC_CHECK(f,"application-all-slots-fixture");
    AC_CHECK(ac_rebuild(f)&&f->named==7&&!strcmp(f->names,"g|bA|bB|pA|pB|sA|sB|"),"application-seven-enabled-overrides-original-order");
    size_t check=ac_schema_node(f->graph,ac_check_schema);unsigned count=0;
    for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;GeoSourceNodeView n;
        if(geo_eval_edge_at(f->graph,i,&e)&&e.consumer==check&&e.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&geo_eval_node_at(f->graph,e.source,&n)&&n.source.provider==AC_DIMENSION)++count;}
    AC_CHECK(count==7,"application-all-seven-overrides-belong-to-check");ac_free(f);return 0;
}
static int ac_forbidden_parameter(void)
{
    const char *text="{\"id\":\"a\",\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"primary.A\":{\"fieldId\":7,\"kind\":\"parameter\",\"parameterId\":4}},\"placement_id\":10}";
    AcFixture *f=ac_fixture(NULL);AC_CHECK(f,"application-forbidden-parameter-fixture");
    EngineeringState *before=malloc(sizeof *before);AC_CHECK(before,"application-forbidden-snapshot");memcpy(before,&f->state,sizeof *before);
    AC_CHECK(!ac_publish(f,2,text)&&!strcmp(f->error,"D28: parameter fields bind object dimensions, not face application overrides")&&
        !memcmp(before,&f->state,sizeof *before),"application-parameter-override-remains-forbidden");
    EngApplication decoded,old;memset(&decoded,0x63,sizeof decoded);memcpy(&old,&decoded,sizeof old);
    AC_CHECK(!wood_eng_application_decode(text,strlen(text),&decoded)&&!memcmp(&old,&decoded,sizeof old),"application-parameter-override-decode-is-atomic");
    free(before);ac_free(f);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;const char *name=argv[1];
    if(!strcmp(name,"inventory"))return ac_inventory();if(!strcmp(name,"no-binding"))return ac_no_binding();
    if(!strcmp(name,"named-authority"))return ac_named_authority();if(!strcmp(name,"returned-definition"))return ac_returned_definition();
    if(!strcmp(name,"check-false"))return ac_returned_check(2);if(!strcmp(name,"check-schema"))return ac_returned_check(3);
    if(!strcmp(name,"check-id"))return ac_returned_check(4);if(!strcmp(name,"check-boolean"))return ac_returned_check(5);
    if(!strcmp(name,"derived-first"))return ac_order(0);if(!strcmp(name,"missing-host"))return ac_order(1);
    if(!strcmp(name,"missing-method"))return ac_order(2);if(!strcmp(name,"all-slots"))return ac_all_slots();
    if(!strcmp(name,"forbidden-parameter"))return ac_forbidden_parameter();return 2;
}
#else
static bool (*ac_product_named_original)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
static GeoCoord ac_product_named_value;
static bool ac_product_named(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(!ac_product_named_original(state,ctx,ref,out))return false;
    if(ref->key_size==5&&!memcmp(ref->key,"width",5))out->as.quantity.num=ac_product_named_value;return true;
}
int main(int argc,char **argv)
{
    if(argc!=3||(strcmp(argv[1],"product")&&strcmp(argv[1],"product-zero")))return 2;
    bool zero=!strcmp(argv[1],"product-zero");memset(&g_world,0,sizeof g_world);
    AC_CHECK(parse_scene_file(argv[2],&g_world),"application-product-existing-scene");
    AC_CHECK(g_world.wood.engineering.application_count==1&&!g_world.wood.engineering.binding_count&&!g_world.wood.timber_count,
        "application-product-has-no-object-binding");
    ReferenceEval *evaluation=calloc(1,sizeof *evaluation);AC_CHECK(evaluation,"application-product-evaluation");evaluation->world=&g_world;
    AC_CHECK(reference_sources_ensure(evaluation),"application-product-real-H-registration");
    bool installed=false;for(size_t i=0;i<geo_eval_provider_count(evaluation->sources);++i){GeoSourceProvider *p=(GeoSourceProvider *)geo_eval_provider_at(evaluation->sources,i);
        if(p->token==APP_SOURCE_NAMED){ac_product_named_original=p->evaluate;p->evaluate=ac_product_named;installed=true;}}
    AC_CHECK(installed,"application-product-real-named-provider");ac_product_named_value=zero?0:17;
    WoodEngineeringContext context=app_eng_context(&g_world);wood_engineering_sources_bind(evaluation->engineering_sources,&context);char error[256];
    bool ok=wood_engineering_rebuild(&context,error,sizeof error);
    if(zero){AC_CHECK(!ok&&!strcmp(error,ac_range_error),"application-product-unused-named-return-controls-validation");}
    else{AC_CHECK(ok,"application-product-check-success");
        size_t host=ac_provider_node(evaluation->sources,APP_SOURCE_PLACEMENT,GEO_SOURCE_DEFINITION);
        int result=ac_closure(evaluation->sources,APP_SOURCE_ENGINEERING_DIMENSION,APP_SOURCE_NAMED,APP_SOURCE_VERSION,host);if(result)return result;
        for(size_t i=0;i<geo_eval_node_count(evaluation->sources);++i){GeoSourceNodeView n;
            if(geo_eval_node_at(evaluation->sources,i,&n)&&n.source.provider==APP_SOURCE_PLACEMENT)
                AC_CHECK(n.value&&n.value->kind==GEO_SOURCE_DEFINITION,"application-product-host-check-never-forces-geometry");}}
    const GeoNamedValue *raw=geo_named_values_find(&g_world.geo.named_values,"width");
    AC_CHECK(raw&&raw->value==3&&!g_world.wood.engineering.binding_count,"application-product-keeps-raw-source-and-bindings");
    reference_sources_dispose(evaluation);free(evaluation);return 0;
}
#endif
