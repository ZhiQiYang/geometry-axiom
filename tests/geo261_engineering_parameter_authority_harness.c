/* Exercise the actual registered K parameter provider, changing only its
 * returned value after it evaluates the original definition. The raw store
 * and legacy admission callback remain 3; no copied W resolver is involved. */
#ifdef GEO261_ENGINEERING_PARAMETER_PRODUCT
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

#define PA_CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
enum {PA_VALUE,PA_KIND,PA_UNIT,PA_FRACTION,PA_RANGE,PA_ZERO,PA_NEGATIVE,PA_FAILURE};
static int pa_mode,pa_evaluations;
static bool (*pa_original_describe)(void *,const GeoSourceRef *,GeoSourceDescriptor *);
static bool (*pa_original_evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
static bool pa_describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    if(!pa_original_describe(state,ref,out))return false;
    if(pa_mode==PA_KIND){out->kind=GEO_SOURCE_DEFINITION;out->unit=GEO_UNIT_SCALAR;}
    if(pa_mode==PA_UNIT)out->unit=GEO_UNIT_SCALAR;
    return true;
}
static bool pa_evaluate(void *state,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    ++pa_evaluations;if(!pa_original_evaluate(state,ctx,ref,out))return false;
    if(pa_mode==PA_FAILURE)return false;
    if(pa_mode==PA_KIND){out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"authority-probe/1","{}",2};return true;}
    out->as.quantity=(GeoQuantity){pa_mode==PA_RANGE?GEO_COORD_LIMIT+1:pa_mode==PA_ZERO?0:pa_mode==PA_NEGATIVE?-17:17,
        pa_mode==PA_FRACTION?2:1,pa_mode==PA_UNIT?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH};return true;
}
static bool pa_intercept(GeoEvalContext *ctx,GeoProviderToken token,int mode)
{
    for(size_t i=0;i<geo_eval_provider_count(ctx);++i){
        GeoSourceProvider *p=(GeoSourceProvider *)geo_eval_provider_at(ctx,i);
        if(p->token!=token)continue;
        pa_mode=mode;pa_evaluations=0;pa_original_describe=p->describe;pa_original_evaluate=p->evaluate;
        p->describe=pa_describe;p->evaluate=pa_evaluate;return true;
    }
    return false;
}
static size_t pa_node(const GeoEvalContext *ctx,GeoProviderToken token)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(ctx,i,&node)&&node.source.provider==token)return i;}
    return SIZE_MAX;
}
static bool pa_edge(const GeoEvalContext *ctx,size_t consumer,size_t source,GeoDependencyKind kind)
{
    if(consumer==SIZE_MAX||source==SIZE_MAX)return false;
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;
        if(geo_eval_edge_at(ctx,i,&edge)&&edge.consumer==consumer&&edge.source==source&&edge.kind==kind)return true;}
    return false;
}
static int pa_graph(const GeoEvalContext *ctx,GeoProviderToken dimension,GeoProviderToken parameter,GeoProviderToken definitions)
{
    size_t p=pa_node(ctx,parameter),d=pa_node(ctx,dimension),field=SIZE_MAX;GeoSourceNodeView node;
    PA_CHECK(geo_eval_node_at(ctx,p,&node)&&node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_QUANTITY&&
        node.value->as.quantity.num==17&&node.value->as.quantity.den==1&&node.value->as.quantity.unit==GEO_UNIT_LENGTH,"parameter-actual-return-memoized");
    PA_CHECK(pa_edge(ctx,d,p,GEO_DEPENDENCY_VALUE_REQUIRED),"engineering-parameter-value-required-edge");
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoParameterDefinitionKind kind;uint32_t card,id;
        if(geo_eval_node_at(ctx,i,&node)&&node.source.provider==definitions&&
           geo_parameter_definition_source_decode(&node.source,&kind,&card,&id)&&kind==GEO_PARAMETER_DEFINITION_FIELD&&card==4&&id==7){
            GeoParameterField decoded;
            PA_CHECK(node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
                geo_parameter_field_definition_decode(node.value->as.definition.content,node.value->as.definition.content_size,&decoded)&&
                decoded.parameter_id==4&&decoded.id==7&&decoded.type==GEO_PARAMETER_DIMENSION&&
                !strcmp(decoded.expression,"{\"den\":\"1\",\"num\":\"3\",\"op\":\"literal\",\"unit\":\"mm\"}"),"parameter-original-definition-retained");field=i;
        }
    }
    PA_CHECK(pa_edge(ctx,p,field,GEO_DEPENDENCY_DEFINITION_REQUIRED),"parameter-original-definition-required-edge");return 0;
}

#ifndef GEO261_ENGINEERING_PARAMETER_PRODUCT
enum {PA_DIMENSION=41,PA_BINDING=42,PA_DEFINITION=43,PA_NAMED=44,PA_PARAMETER=45,PA_PARAMETER_DEFINITION=46};
typedef struct {
    EngineeringState state;WoodEngineeringContext context;GeoParameterStore *parameters;
    GeoEvalContext *graph;GeoParameterSources *parameter_sources;WoodEngineeringSources *sources;
    int callbacks;bool callback_failure;char error[256];
} PaFixture;
static const char pa_range_error[]="I35: effective dimension violates its positive/nonnegative integer mm range";
static bool pa_parameter(void *opaque,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{
    PaFixture *f=opaque;++f->callbacks;
    if(f->callback_failure){*out=29;if(error&&cap)snprintf(error,cap,"I38: original callback rejection");return false;}
    GeoParameterError issue;return geo_parameters_coordinate(f->parameters,ref,out,&issue);
}
static PaFixture *pa_fixture(int mode)
{
    PaFixture *f=calloc(1,sizeof *f);if(!f)return NULL;
    f->parameters=geo_parameters_create();f->graph=geo_eval_create(261,73);if(!f->parameters||!f->graph)return NULL;
    GeoParameterCard card;GeoParameterField field={0};GeoParameterError error;
    geo_parameters_begin_definition(f->parameters,4,&card);card.count=1;strcpy(card.name,"raw-three");
    field.parameter_id=4;field.id=7;field.type=GEO_PARAMETER_DIMENSION;strcpy(field.name,"length");
    strcpy(field.expression,"{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"mm\"}");
    if(!geo_parameters_accept_field(f->parameters,&card,&field,0,&error)||!geo_parameters_put(f->parameters,&card,&field,&error)||
       !geo_parameters_rebuild(f->parameters,&error))return NULL;
    f->context=(WoodEngineeringContext){.state=&f->state,.user=f,.error=f->error,.error_capacity=sizeof f->error,.parameter=pa_parameter};
    f->parameter_sources=geo_parameter_sources_register_with_definitions(f->graph,f->parameters,PA_PARAMETER,PA_PARAMETER_DEFINITION,
        "core.parameter.field","engineering-parameter-authority/1");
    f->sources=wood_engineering_sources_register(f->graph,&f->context,
        (WoodEngineeringSourceTokens){PA_DIMENSION,PA_BINDING,PA_DEFINITION,PA_NAMED,PA_PARAMETER,0});
    if(!f->parameter_sources||!f->sources||!pa_intercept(f->graph,PA_PARAMETER,mode))return NULL;
    wood_engineering_sources_bind(f->sources,&f->context);return f;
}
static void pa_free(PaFixture *f)
{
    if(!f)return;wood_engineering_sources_destroy(f->sources);geo_parameter_sources_destroy(f->parameter_sources);
    geo_eval_destroy(f->graph);geo_parameters_destroy(f->parameters);free(f);
}
static bool pa_resolve(PaFixture *f,bool gap,GeoCoord *out,char *path,size_t cap)
{
    EngDimensionSource source={.kind=ENG_PARAMETER,.parameter={true,4,7}};
    EngTarget target={gap?0:1,7,0,gap?1:0};return wood_eng_resolve(&f->context,&source,&target,10,1,out,path,cap);
}
static int pa_authority(void)
{
    PaFixture *f=pa_fixture(PA_VALUE);PA_CHECK(f,"authority-fixture");GeoCoord out=-1;char path[80]="unchanged";
    PA_CHECK(pa_resolve(f,false,&out,path,sizeof path)&&out==17,"engineering-parameter-actual-value-authority");
    PA_CHECK(f->callbacks==1&&pa_evaluations==1&&!strcmp(path,"param:4:7")&&!f->error[0],"parameter-original-callback-and-path");
    GeoCoord raw=-1;GeoParameterError issue;
    PA_CHECK(geo_parameters_coordinate(f->parameters,(GeoParameterRef){true,4,7},&raw,&issue)&&raw==3,"parameter-raw-store-remains-three");
    int graph_result=pa_graph(f->graph,PA_DIMENSION,PA_PARAMETER,PA_PARAMETER_DEFINITION);if(graph_result)return graph_result;
    PA_CHECK(geo_eval_seal(f->graph)&&pa_resolve(f,false,&out,path,sizeof path)&&out==17&&f->callbacks==1&&pa_evaluations==1,
        "parameter-success-memoized-after-seal");pa_free(f);return 0;
}
static int pa_rejected(int mode)
{
    PaFixture *f=pa_fixture(mode);PA_CHECK(f,"rejection-fixture");GeoCoord out=-1;char path[80]="unchanged";
    PA_CHECK(!pa_resolve(f,false,&out,path,sizeof path),"malformed-parameter-return-rejected");
    PA_CHECK(out==3&&!strcmp(path,"unchanged")&&f->callbacks==1&&pa_evaluations==1,"malformed-return-preserves-admission-output");
    PA_CHECK(mode==PA_FAILURE?!f->error[0]:!strcmp(f->error,pa_range_error),"malformed-return-diagnostic");
    GeoSourceNodeView node;PA_CHECK(geo_eval_node_at(f->graph,pa_node(f->graph,PA_DIMENSION),&node)&&node.state==GEO_NODE_FAILED&&!node.value,
        "malformed-return-publishes-no-W-value");pa_free(f);return 0;
}
static int pa_callback_failure(void)
{
    PaFixture *f=pa_fixture(PA_VALUE);PA_CHECK(f,"callback-failure-fixture");f->callback_failure=true;GeoCoord out=-1;char path[80]="unchanged";
    PA_CHECK(!pa_resolve(f,false,&out,path,sizeof path)&&out==29&&!strcmp(path,"unchanged")&&
        !strcmp(f->error,"I38: original callback rejection"),"callback-original-failure-output-and-diagnostic");
    PA_CHECK(f->callbacks==1&&!pa_evaluations&&pa_node(f->graph,PA_PARAMETER)==SIZE_MAX,
        "callback-failure-precedes-any-K-quantity-request");pa_free(f);return 0;
}
static int pa_policy(int mode,bool gap)
{
    PaFixture *f=pa_fixture(mode);PA_CHECK(f,"policy-fixture");GeoCoord out=-1;char path[80]="unchanged";bool ok=pa_resolve(f,gap,&out,path,sizeof path);
    PA_CHECK(ok==(mode==PA_ZERO&&gap)&&out==(mode==PA_ZERO?0:-17)&&!strcmp(path,"param:4:7"),"actual-value-reaches-original-target-policy");
    PA_CHECK(ok?!f->error[0]:!strcmp(f->error,pa_range_error),"original-target-policy-diagnostic");pa_free(f);return 0;
}
static int pa_small_error(void)
{
    PaFixture *f=pa_fixture(PA_FRACTION);PA_CHECK(f,"small-error-fixture");
    struct {char before;char text[8];char after;} guard={'L',"xxxxxxx",'R'};GeoCoord out=-1;
    PA_CHECK(!f->context.source_parameter(f->context.sources,(GeoParameterRef){true,4,7},&out,guard.text,sizeof guard.text)&&out==3,
        "small-error-return-rejected");
    PA_CHECK(guard.before=='L'&&guard.after=='R'&&!strcmp(guard.text,"I35: ef"),"small-error-capacity-respected");pa_free(f);return 0;
}
static int pa_material_decode(void)
{
    const char *values[]={
        "{\"id\":\"p\",\"kind\":\"panel\",\"length\":200,\"name\":\"Panel\",\"version\":1,\"width\":100}",
        "{\"id\":\"p\",\"kind\":\"panel\",\"length\":200,\"name\":\"Panel\",\"thickness\":null,\"version\":1,\"width\":100}",
        "{\"id\":\"p\",\"kind\":\"panel\",\"length\":200,\"name\":\"Panel\",\"thickness\":\"000.0100\",\"version\":1,\"width\":100}",
        "{\"A\":30,\"B\":40,\"id\":\"t\",\"kind\":\"timber\",\"name\":\"Timber\",\"version\":1}"};
    for(size_t i=0;i<sizeof values/sizeof values[0];++i){EngMaterialVersion material;
        PA_CHECK(wood_eng_material_decode(values[i],strlen(values[i]),&material)&&!strcmp(material.content,values[i])&&
            material.kind==(i==3)&&material.has_thickness==(i==2),"material-decoder-canonical-source-preserved");
        if(i==2)PA_CHECK(!strcmp(material.thickness,"000.0100"),"material-decoder-decimal-not-rounded");
        char fingerprint[65];geo_sha256(values[i],strlen(values[i]),fingerprint);
        PA_CHECK(!strcmp(material.fingerprint,fingerprint)&&material.ref.version==1&&!material.archived,"material-decoder-exact-identity-and-fingerprint");
    }
    char decimal[129],json[512];memset(decimal,'9',127);decimal[127]=0;
    snprintf(json,sizeof json,"{\"id\":\"p\",\"kind\":\"panel\",\"length\":2,\"name\":\"P\",\"thickness\":\"%s\",\"version\":1,\"width\":1}",decimal);
    EngMaterialVersion out;PA_CHECK(wood_eng_material_decode(json,strlen(json),&out)&&!strcmp(out.thickness,decimal),"material-decoder-full-127-byte-decimal");
    decimal[127]='9';decimal[128]=0;snprintf(json,sizeof json,"{\"id\":\"p\",\"kind\":\"panel\",\"length\":2,\"name\":\"P\",\"thickness\":\"%s\",\"version\":1,\"width\":1}",decimal);
    EngMaterialVersion before=out;PA_CHECK(!wood_eng_material_decode(json,strlen(json),&out)&&!memcmp(&before,&out,sizeof out),"material-decoder-128-byte-overflow-atomic");return 0;
}
static int pa_material_rejections(void)
{
    const char *values[]={"{}","{", " {\"A\":30,\"B\":40,\"id\":\"t\",\"kind\":\"timber\",\"name\":\"T\",\"version\":1}",
        "{\"A\":0,\"B\":40,\"id\":\"t\",\"kind\":\"timber\",\"name\":\"T\",\"version\":1}",
        "{\"A\":30,\"B\":40,\"id\":\"bad id\",\"kind\":\"timber\",\"name\":\"T\",\"version\":1}",
        "{\"id\":\"p\",\"kind\":\"panel\",\"length\":2,\"name\":\"P\",\"thickness\":\"0.00\",\"version\":1,\"width\":1}",
        "{\"id\":\"p\",\"kind\":\"panel\",\"length\":2,\"name\":\"P\",\"thickness\":1,\"version\":1,\"width\":1}"};
    EngMaterialVersion out,before;memset(&out,0x5a,sizeof out);before=out;
    for(size_t i=0;i<sizeof values/sizeof values[0];++i)
        PA_CHECK(!wood_eng_material_decode(values[i],strlen(values[i]),&out)&&!memcmp(&out,&before,sizeof out),"material-decoder-invalid-input-preserves-output");
    PA_CHECK(!wood_eng_material_decode(NULL,0,&out)&&!wood_eng_material_decode("{}",2,NULL),"material-decoder-null-input-rejected");return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;const char *name=argv[1];
    if(!strcmp(name,"authority"))return pa_authority();
    if(!strcmp(name,"callback-failure"))return pa_callback_failure();
    if(!strcmp(name,"kind"))return pa_rejected(PA_KIND);
    if(!strcmp(name,"unit"))return pa_rejected(PA_UNIT);
    if(!strcmp(name,"fraction"))return pa_rejected(PA_FRACTION);
    if(!strcmp(name,"range"))return pa_rejected(PA_RANGE);
    if(!strcmp(name,"source-failure"))return pa_rejected(PA_FAILURE);
    if(!strcmp(name,"gap-zero"))return pa_policy(PA_ZERO,true);
    if(!strcmp(name,"positive-zero"))return pa_policy(PA_ZERO,false);
    if(!strcmp(name,"negative"))return pa_policy(PA_NEGATIVE,false);
    if(!strcmp(name,"small-error"))return pa_small_error();
    if(!strcmp(name,"material-decode"))return pa_material_decode();
    if(!strcmp(name,"material-rejections"))return pa_material_rejections();return 2;
}
#else
int main(int argc,char **argv)
{
    if(argc!=3||strcmp(argv[1],"product"))return 2;memset(&g_world,0,sizeof g_world);
    PA_CHECK(parse_scene_file(argv[2],&g_world),"product-parameter-existing-scene-DSL");
    PA_CHECK(g_world.wood.timber_count==1&&g_world.wood.timbers[0].size_a==3,"product-parameter-raw-dimension-three");
    ReferenceEval *evaluation=calloc(1,sizeof *evaluation);PA_CHECK(evaluation,"product-parameter-evaluation-allocation");evaluation->world=&g_world;
    PA_CHECK(reference_sources_ensure(evaluation)&&pa_intercept(evaluation->sources,APP_SOURCE_PARAMETER,PA_VALUE),"product-parameter-real-provider-interception");
    GeoCoord value=-1;PA_CHECK(reference_member_dimension(evaluation,1,false,&value)&&value==17,"product-engineering-parameter-actual-value-authority");
    GeoCoord raw=-1;GeoParameterError error;
    PA_CHECK(geo_parameters_coordinate(&g_world.geo.parameters,(GeoParameterRef){true,4,7},&raw,&error)&&raw==3&&g_world.wood.timbers[0].size_a==3,
        "product-parameter-raw-store-and-live-member-unchanged");
    int graph_result=pa_graph(evaluation->sources,APP_SOURCE_ENGINEERING_DIMENSION,APP_SOURCE_PARAMETER,APP_SOURCE_PARAMETER_DEFINITION);
    if(graph_result)return graph_result;
    reference_sources_dispose(evaluation);free(evaluation);return 0;
}
#endif
