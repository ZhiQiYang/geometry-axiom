/* Real K provider and W policy witnesses. Product mode includes the actual H
 * candidate, without reimplementing its provider registration or resolver. */
#ifdef GEO261_VERSION_FIELD_PRODUCT
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
#define VF_CHECK(test,label) do{if(!(test)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)

static bool vf_edge(const GeoEvalContext *graph,size_t from,size_t to,GeoDependencyKind relation)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.consumer==from&&edge.source==to&&edge.kind==relation)return true;}
    return false;
}
static size_t vf_version_node(const GeoEvalContext *graph,GeoProviderToken token,GeoVersionSourceKind wanted,
    int kind,const char *id,uint32_t version,uint32_t field)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;GeoVersionSourceKind actual;GeoVersionIdentity identity;uint32_t actual_field;
        if(!geo_eval_node_at(graph,i,&node)||node.source.provider!=token||!geo_version_source_decode(&node.source,&actual,&identity,&actual_field))continue;
        const unsigned char *key=identity.key;
        if(actual==wanted&&identity.key_length==strlen(id)+1&&key[0]==kind+1&&!memcmp(key+1,id,strlen(id))&&identity.version==version&&actual_field==field)return i;}
    return SIZE_MAX;
}
static size_t vf_schema_count(const GeoEvalContext *graph,const char *schema)
{
    size_t count=0;for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(graph,i,&node)&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
            !strcmp(node.value->as.definition.schema,schema))++count;}return count;
}
static bool vf_quantity(const GeoEvalContext *graph,size_t index,GeoCoord expected)
{
    GeoSourceNodeView node;return geo_eval_node_at(graph,index,&node)&&node.state==GEO_NODE_VALID&&node.value&&
        node.value->kind==GEO_SOURCE_QUANTITY&&node.value->as.quantity.unit==GEO_UNIT_LENGTH&&
        node.value->as.quantity.den==1&&node.value->as.quantity.num==expected;
}
static int vf_chain(const GeoEvalContext *graph,GeoProviderToken version_token,GeoProviderToken dimension_token,
    int kind,const char *id,uint32_t field,GeoCoord expected)
{
    size_t value=vf_version_node(graph,version_token,GEO_VERSION_SOURCE_FIELD,kind,id,1,field);
    size_t definition=vf_version_node(graph,version_token,GEO_VERSION_SOURCE_DEFINITION,kind,id,1,0);
    bool consumed=false;for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(graph,i,&node)&&node.source.provider==dimension_token&&vf_edge(graph,i,value,GEO_DEPENDENCY_VALUE_REQUIRED))consumed=true;}
    VF_CHECK(consumed,"version-field-value-edge");
    VF_CHECK(vf_quantity(graph,value,expected),"version-field-real-quantity");
    VF_CHECK(vf_edge(graph,value,definition,GEO_DEPENDENCY_DEFINITION_REQUIRED),"version-field-definition-edge");
    GeoSourceNodeView node;GeoVersionView decoded;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];
    VF_CHECK(geo_eval_node_at(graph,definition,&node)&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
        !strcmp(node.value->as.definition.schema,"geometry.version/1")&&
        geo_version_definition_decode(node.value->as.definition.content,node.value->as.definition.content_size,&decoded,fields),"version-field-complete-definition");
    return 0;
}

#ifndef GEO261_VERSION_FIELD_PRODUCT
enum {VF_VERSION=23,VF_DIMENSION=41,VF_BINDING=42,VF_DEFINITION=43,VF_NAMED=44,VF_PARAMETER=45};
typedef struct {
    EngineeringState state;WoodEngineeringContext context;GeoVersionStore *store;
    GeoEvalContext *graph;GeoVersionSources *versions;WoodEngineeringSources *engineering;
    int targets,placements,writes,named;char error[256];
} VfFixture;
static bool vf_place(void *opaque,uint32_t id,bool *derived)
{VfFixture *f=opaque;++f->placements;if(derived)*derived=false;return id==10;}
static bool vf_target(void *opaque,const EngTarget *target,WoodEngineeringTargetInfo *out)
{VfFixture *f=opaque;++f->targets;if(target->id!=7)return false;*out=(WoodEngineeringTargetInfo){10,target->kind?1:-1,false,false,true,true};return true;}
static bool vf_named(void *opaque,const char *name,GeoCoord *out)
{VfFixture *f=opaque;++f->named;if(strcmp(name,"unused"))return false;*out=13;return true;}
static void vf_write(void *opaque,const EngTarget *target,GeoCoord value)
{VfFixture *f=opaque;(void)target;(void)value;++f->writes;}
static bool vf_serial(void *opaque,char *error,size_t cap)
{(void)opaque;(void)error;(void)cap;return true;}
static bool vf_publish(VfFixture *f,int kind,const char *text)
{
    GeoJson json;bool ok=geo_json_parse(&json,text);if(ok)ok=kind==0?wood_eng_publish_material(&f->context,&json,0,NULL):
        kind==1?wood_eng_publish_method(&f->context,&json,0,NULL):wood_eng_put_application(&f->context,&json,0);
    geo_json_free(&json);return ok;
}
static VfFixture *vf_fixture(bool archived)
{
    VfFixture *f=calloc(1,sizeof *f);if(!f)return NULL;if(geo_versions_create(&f->store)!=GEO_VERSION_OK){free(f);return NULL;}
    f->context=(WoodEngineeringContext){.state=&f->state,.versions=f->store,.user=f,.error=f->error,.error_capacity=sizeof f->error,
        .placement=vf_place,.target=vf_target,.named_value=vf_named,.write_dimension=vf_write,.serializable=vf_serial};
    char literal[128],panel[512];memset(literal,'9',127);literal[127]=0;
    snprintf(panel,sizeof panel,"{\"id\":\"p\",\"version\":1,\"kind\":\"panel\",\"name\":\"Panel\",\"width\":100,\"length\":200,\"thickness\":\"%s\"}",literal);
    if(!vf_publish(f,0,panel)||
       !vf_publish(f,0,"{\"id\":\"t\",\"version\":1,\"kind\":\"timber\",\"name\":\"Timber\",\"A\":30,\"B\":40}")||
       !vf_publish(f,0,"{\"id\":\"unused\",\"version\":1,\"kind\":\"timber\",\"name\":\"Unused\",\"A\":31,\"B\":41}")||
       !vf_publish(f,1,"{\"id\":\"t\",\"version\":1,\"name\":\"Method\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"primary\":{\"id\":\"t\",\"version\":1},\"secondary\":{\"id\":\"unused\",\"version\":1}},\"gap\":3,\"longAxis\":\"v\"}")||
       !vf_publish(f,1,"{\"id\":\"empty\",\"version\":1,\"name\":\"Unselected\"}")||
       !vf_publish(f,2,"{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"t\",\"version\":1}}"))return NULL;
    f->state.materials[1].archived=archived;f->targets=f->placements=f->named=0;
    f->graph=geo_eval_create(71,9);if(!f->graph)return NULL;
    f->versions=geo_version_sources_register(f->graph,f->store,VF_VERSION);if(!f->versions)return NULL;
    f->engineering=wood_engineering_sources_register(f->graph,&f->context,(WoodEngineeringSourceTokens){VF_DIMENSION,VF_BINDING,VF_DEFINITION,VF_NAMED,VF_PARAMETER,VF_VERSION});
    if(!f->engineering)return NULL;wood_engineering_sources_bind(f->engineering,&f->context);return f;
}
static void vf_free(VfFixture *f)
{if(f){geo_eval_destroy(f->graph);wood_engineering_sources_destroy(f->engineering);geo_version_sources_destroy(f->versions);geo_versions_destroy(f->store);free(f);}}
static bool vf_resolve(VfFixture *f,int kind,const char *id,int field,int target_kind,int target_field,int axis,GeoCoord *out)
{
    EngDimensionSource source={0};source.kind=kind;source.field=field;source.version=kind==ENG_MATERIAL?1:0;snprintf(source.ref,sizeof source.ref,"%s",id);
    EngTarget target={target_kind,7,axis,target_field};return wood_eng_resolve(&f->context,&source,&target,10,1,out,NULL,0);
}
static int vf_codec(void)
{
    const unsigned char opaque[]={0,0xff,'x'},content[]={0,1,0xff};char fingerprint[65];geo_sha256(content,sizeof content,fingerprint);
    GeoVersionField source[2];memset(source,0,sizeof source);source[0]=(GeoVersionField){4,{30,1,GEO_UNIT_LENGTH}};
    source[1].id=9;source[1].kind=GEO_VERSION_DECIMAL_LITERAL;source[1].value.unit=GEO_UNIT_LENGTH;
    source[1].literal_length=128;memset(source[1].literal,'9',128);
    const char schema[]={'s',0,'x'};GeoVersionView input={{opaque,sizeof opaque,0x01020304},content,sizeof content,fingerprint,64,source,2,schema,sizeof schema};
    unsigned char encoded[GEO_VERSION_DEFINITION_MAX],other[GEO_VERSION_DEFINITION_MAX];GeoVersionField decoded_fields[GEO_VERSION_FIELD_CAPACITY];GeoVersionView decoded;
    size_t size=geo_version_definition_encode(&input,encoded,sizeof encoded);
    VF_CHECK(size&&geo_version_definition_decode(encoded,size,&decoded,decoded_fields),"version-codec-complete-decode");
    VF_CHECK(decoded.identity.key_length==3&&!memcmp(decoded.identity.key,opaque,3)&&decoded.identity.version==0x01020304&&
        decoded.content_length==3&&!memcmp(decoded.content,content,3)&&decoded.schema_length==3&&!memcmp(decoded.schema,schema,3)&&
        decoded.field_count==2&&decoded_fields[1].kind==GEO_VERSION_DECIMAL_LITERAL&&decoded_fields[1].literal_length==128&&
        !memcmp(decoded_fields[1].literal,source[1].literal,128),"version-codec-retains-opaque-and-full-decimal-bytes");
    VF_CHECK(geo_version_definition_encode(&decoded,other,sizeof other)==size&&!memcmp(encoded,other,size),"version-codec-byte-roundtrip");
    memset(other,0xa5,sizeof other);source[0].value.den=2;
    VF_CHECK(!geo_version_definition_encode(&input,other,sizeof other)&&other[0]==0xa5&&other[sizeof other-1]==0xa5,"version-codec-rejects-noncanonical-quantity-without-write");
    source[0].value.den=1;source[1].literal[0]='x';
    VF_CHECK(!geo_version_definition_encode(&input,other,sizeof other)&&other[0]==0xa5&&other[sizeof other-1]==0xa5,"version-codec-rejects-invalid-decimal-without-write");source[1].literal[0]='9';
    GeoVersionView before=decoded;GeoVersionField before_fields[GEO_VERSION_FIELD_CAPACITY];memcpy(before_fields,decoded_fields,sizeof before_fields);
    for(size_t n=0;n<size;++n)VF_CHECK(!geo_version_definition_decode(encoded,n,&decoded,decoded_fields)&&!memcmp(&before,&decoded,sizeof decoded)&&
        !memcmp(before_fields,decoded_fields,sizeof before_fields),"version-codec-truncated-output-unchanged");
    GeoVersionSourceKey key,other_key;GeoSourceRef ref=geo_version_source_ref(23,GEO_VERSION_SOURCE_FIELD,input.identity,4,&key);
    static const unsigned char expected[]={2,0,0,0,3,1,2,3,4,0,0,0,4,0,255,120};
    VF_CHECK(ref.key_size==sizeof expected&&!memcmp(ref.key,expected,sizeof expected),"version-key-independent-canonical-bytes");
    other_key=key;VF_CHECK(!geo_version_source_ref(23,GEO_VERSION_SOURCE_DEFINITION,input.identity,1,&other_key).key&&!memcmp(&other_key,&key,sizeof key),"version-key-invalid-preserves-output");
    EngVersionRef identity={"a",0x01020304},returned;bool archived=false;int kind=9;unsigned char metadata[WOOD_VERSION_METADATA_MAX];
    static const unsigned char meta_expected[]={1,1,2,3,4,0,0,0,1,97,1};
    size=wood_engineering_version_metadata_encode(1,&identity,true,metadata,sizeof metadata);
    VF_CHECK(size==sizeof meta_expected&&!memcmp(metadata,meta_expected,size)&&wood_engineering_version_metadata_decode(metadata,size,&kind,&returned,&archived)&&
        kind==1&&archived&&!strcmp(returned.id,"a")&&returned.version==identity.version,"metadata-independent-canonical-bytes");
    returned=identity;archived=false;kind=9;metadata[size-1]=2;
    VF_CHECK(!wood_engineering_version_metadata_decode(metadata,size,&kind,&returned,&archived)&&kind==9&&!archived&&!memcmp(&returned,&identity,sizeof identity),"metadata-invalid-preserves-output");return 0;
}
static int vf_inventory(void)
{
    VfFixture *f=vf_fixture(false);VF_CHECK(f,"inventory-fixture");EngineeringState *before=malloc(sizeof *before);VF_CHECK(before,"inventory-snapshot");memcpy(before,&f->state,sizeof *before);
    GeoVersionStore *stored=NULL;VF_CHECK(geo_versions_clone(f->store,&stored)==GEO_VERSION_OK,"inventory-version-snapshot");
    GeoVersionView version;VF_CHECK(wood_eng_version_view(&f->context,0,"p",1,&version),"inventory-panel-view");
    GeoVersionSourceKey key;GeoSourceRef ref=geo_version_source_ref(VF_VERSION,GEO_VERSION_SOURCE_FIELD,version.identity,WOOD_ENG_VERSION_THICKNESS,&key);GeoSourceDescriptor descriptor;
    VF_CHECK(geo_eval_describe(f->graph,ref,&descriptor)==GEO_SOURCE_OK&&descriptor.kind==GEO_SOURCE_QUANTITY&&descriptor.unit==GEO_UNIT_LENGTH,"inventory-description-without-decimal-conversion");
    VF_CHECK(geo_version_sources_definitions(f->versions)&&wood_engineering_sources_definitions(f->engineering)&&wood_engineering_sources_metadata(f->engineering),"inventory-complete-definitions");
    VF_CHECK(!f->placements&&!f->targets&&!f->writes&&!f->named&&!memcmp(before,&f->state,sizeof *before)&&geo_versions_equal(stored,f->store),"inventory-zero-value-work-or-store-mutation");
    VF_CHECK(vf_schema_count(f->graph,"geometry.version/1")==5&&vf_schema_count(f->graph,"woodworking.version-metadata/1")==5&&
        vf_schema_count(f->graph,"woodworking.face-application/1")==1,"inventory-includes-all-unused-metadata-and-versions");
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView node;VF_CHECK(geo_eval_node_at(f->graph,i,&node),"inventory-node-readable");
        VF_CHECK((node.state==GEO_NODE_NEW&&!node.value)||(node.value&&node.value->kind==GEO_SOURCE_DEFINITION),"inventory-no-quantity-evaluation");}
    size_t nodes=geo_eval_node_count(f->graph),edges=geo_eval_edge_count(f->graph);
    VF_CHECK(geo_eval_seal(f->graph)&&geo_version_sources_definitions(f->versions)&&wood_engineering_sources_metadata(f->engineering)&&
        geo_eval_node_count(f->graph)==nodes&&geo_eval_edge_count(f->graph)==edges,"inventory-sealed-memoized-definitions");
    geo_versions_destroy(stored);free(before);vf_free(f);return 0;
}
static int vf_selected(void)
{
    VfFixture *f=vf_fixture(false);VF_CHECK(f,"selected-fixture");GeoCoord value;
    VF_CHECK(vf_resolve(f,ENG_MATERIAL,"p",ENG_WIDTH,0,0,0,&value)&&value==100,"selected-width-value");
    VF_CHECK(vf_resolve(f,ENG_MATERIAL,"p",ENG_LENGTH,0,0,0,&value)&&value==200,"selected-length-value");
    VF_CHECK(vf_resolve(f,ENG_MATERIAL,"t",ENG_A,1,0,0,&value)&&value==30,"selected-a-value");
    VF_CHECK(vf_resolve(f,ENG_MATERIAL,"t",ENG_B,1,1,0,&value)&&value==40,"selected-b-value");
    VF_CHECK(vf_resolve(f,ENG_APPLICATION,"a",ENG_U_GAP,0,1,0,&value)&&value==3,"selected-method-gap-value");
    if(vf_chain(f->graph,VF_VERSION,VF_DIMENSION,0,"p",ENG_WIDTH,100)||vf_chain(f->graph,VF_VERSION,VF_DIMENSION,0,"p",ENG_LENGTH,200)||
       vf_chain(f->graph,VF_VERSION,VF_DIMENSION,0,"t",ENG_A,30)||vf_chain(f->graph,VF_VERSION,VF_DIMENSION,0,"t",ENG_B,40)||
       vf_chain(f->graph,VF_VERSION,VF_DIMENSION,1,"t",WOOD_ENG_VERSION_GAP,3))return 1;
    VF_CHECK(vf_version_node(f->graph,VF_VERSION,GEO_VERSION_SOURCE_FIELD,0,"p",1,WOOD_ENG_VERSION_THICKNESS)==SIZE_MAX&&
        vf_version_node(f->graph,VF_VERSION,GEO_VERSION_SOURCE_FIELD,0,"unused",1,ENG_A)==SIZE_MAX,"selected-keeps-unused-fields-unevaluated");vf_free(f);return 0;
}
static int vf_override(void)
{
    VfFixture *f=vf_fixture(false);VF_CHECK(f,"override-fixture");
    VF_CHECK(vf_publish(f,2,"{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"t\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"literal\",\"value\":9}}}"),"override-canonical-definition");GeoCoord value;
    VF_CHECK(vf_resolve(f,ENG_APPLICATION,"a",ENG_U_GAP,0,1,0,&value)&&value==9,"override-selected-face-value");
    VF_CHECK(vf_version_node(f->graph,VF_VERSION,GEO_VERSION_SOURCE_FIELD,1,"t",1,WOOD_ENG_VERSION_GAP)==SIZE_MAX,"override-keeps-inactive-gap-definition-only");
    EngDimensionSource bad={.kind=ENG_MATERIAL,.field=ENG_WIDTH,.version=1};strcpy(bad.ref,"t");EngTarget target={0,7,0,0};value=997;
    VF_CHECK(!wood_eng_resolve(&f->context,&bad,&target,10,1,&value,NULL,0)&&value==997&&
        !strcmp(f->error,"I35: grid panel accepts only panel material width/length; gap is separately explicit"),"original-type-diagnostic-precedes-field-request");
    VF_CHECK(vf_version_node(f->graph,VF_VERSION,GEO_VERSION_SOURCE_FIELD,0,"t",1,ENG_WIDTH)==SIZE_MAX,"invalid-source-does-not-request-wrong-field");vf_free(f);return 0;
}
static bool (*vf_original_evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
static int vf_tamper_kind;
static unsigned char vf_tampered[GEO_VERSION_DEFINITION_MAX];
static bool vf_changed_content(GeoVersionView *version,const char *content,char fingerprint[65])
{
    GeoJson json;bool ok=geo_json_parse(&json,content);static char canonical[ENG_RECORD_MAX];
    if(ok)ok=geo_json_canonical(&json,0,canonical,sizeof canonical);geo_json_free(&json);if(!ok)return false;
    version->content=canonical;version->content_length=strlen(canonical);geo_sha256(canonical,version->content_length,fingerprint);
    version->fingerprint=fingerprint;version->fingerprint_length=64;return true;
}
static bool vf_intercept(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(!vf_original_evaluate(opaque,ctx,ref,out))return false;
    if(vf_tamper_kind==6){
        if(out->kind==GEO_SOURCE_DEFINITION&&!strcmp(out->as.definition.schema,"woodworking.face-application/1")){
            static const char content[]="{\"anchorOptions\":{\"u\":{\"kind\":\"coordinate\",\"value\":21},\"v\":{\"kind\":\"edge\",\"side\":\"max\"}},\"id\":\"a\",\"longAxis\":\"u\",\"mainAlong\":\"v\",\"method\":{\"id\":\"empty\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"literal\",\"value\":9},\"primary.A\":{\"kind\":\"literal\",\"value\":17}},\"placement_id\":10}";
            out->as.definition.content=content;out->as.definition.content_size=strlen(content);}
        return true;
    }
    GeoVersionSourceKind kind;GeoVersionIdentity identity;uint32_t field;if(!geo_version_source_decode(ref,&kind,&identity,&field))return false;
    const unsigned char *id=identity.key;if(identity.key_length!=2||id[1]!='t')return true;
    if((vf_tamper_kind==1||vf_tamper_kind==5||vf_tamper_kind>=7)&&id[0]!=1)return true;
    if((vf_tamper_kind==3||vf_tamper_kind==4)&&id[0]!=2)return true;
    if((vf_tamper_kind==1||vf_tamper_kind>=3)&&kind==GEO_VERSION_SOURCE_DEFINITION){
        GeoVersionView version;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];
        if(!geo_version_definition_decode(out->as.definition.content,out->as.definition.content_size,&version,fields))return false;
        char fingerprint[65];
        if(vf_tamper_kind==1)for(size_t i=0;i<version.field_count;++i)if(fields[i].id==ENG_A)fields[i].value.num=37;
        if(vf_tamper_kind==3&&!vf_changed_content(&version,"{\"id\":\"t\",\"version\":1,\"name\":\"Method\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"primary\":{\"id\":\"unused\",\"version\":1}},\"gap\":3,\"longAxis\":\"v\"}",fingerprint))return false;
        if(vf_tamper_kind==4){
            if(!vf_changed_content(&version,"{\"id\":\"t\",\"version\":1,\"name\":\"Method\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"primary\":{\"id\":\"t\",\"version\":1}},\"gap\":3,\"longAxis\":\"u\"}",fingerprint))return false;
            for(size_t i=0;i<version.field_count;++i)if(fields[i].id==WOOD_ENG_VERSION_LONG_AXIS)fields[i].value.num=1;}
        if(vf_tamper_kind==5){
            if(!vf_changed_content(&version,"{\"id\":\"t\",\"version\":1,\"name\":\"Timber\",\"kind\":\"panel\",\"width\":30,\"length\":40}",fingerprint))return false;
            memset(fields,0,sizeof fields);fields[0]=(GeoVersionField){ENG_WIDTH,{30,1,GEO_UNIT_LENGTH}};fields[1]=(GeoVersionField){ENG_LENGTH,{40,1,GEO_UNIT_LENGTH}};
            fields[2]=(GeoVersionField){WOOD_ENG_VERSION_KIND,{0,1,GEO_UNIT_SCALAR}};version.field_count=3;}
        if(vf_tamper_kind==7){out->as.definition.schema=NULL;return true;}
        if(vf_tamper_kind==8)for(size_t i=0;i<version.field_count;++i)if(fields[i].id==ENG_A)fields[i].value.unit=GEO_UNIT_SCALAR;
        if(vf_tamper_kind==9){size_t i=0;while(i<version.field_count&&fields[i].id!=ENG_A)++i;
            if(i<version.field_count){memmove(fields+i,fields+i+1,(version.field_count-i-1)*sizeof *fields);--version.field_count;}}
        size_t n=geo_version_definition_encode(&version,vf_tampered,sizeof vf_tampered);if(!n)return false;
        out->as.definition.content=vf_tampered;out->as.definition.content_size=n;
    }else if(vf_tamper_kind==2&&kind==GEO_VERSION_SOURCE_FIELD&&field==ENG_A)out->as.quantity.num=41;
    return true;
}
static int vf_tamper(int kind)
{
    VfFixture *f=vf_fixture(false);VF_CHECK(f,"tamper-fixture");GeoSourceProvider *provider=NULL;
    for(size_t i=0;i<geo_eval_provider_count(f->graph);++i){const GeoSourceProvider *p=geo_eval_provider_at(f->graph,i);if(p->token==(kind==6?VF_DEFINITION:VF_VERSION))provider=(GeoSourceProvider *)p;}
    VF_CHECK(provider,"tamper-real-k-provider");vf_original_evaluate=provider->evaluate;vf_tamper_kind=kind;provider->evaluate=vf_intercept;
    if(kind>=3){GeoCoord value=997;bool ok;
        if(kind==3){ok=vf_resolve(f,ENG_APPLICATION,"a",ENG_PRIMARY_A,1,0,0,&value);
            VF_CHECK(ok&&value==31,"actual-returned-method-slot-controls-selection");}
        else if(kind==4){ok=vf_resolve(f,ENG_APPLICATION,"a",ENG_U_PANEL,0,0,0,&value);
            VF_CHECK(ok&&value==200,"actual-returned-method-axis-controls-selection");}
        else if(kind==5){ok=vf_resolve(f,ENG_MATERIAL,"t",ENG_A,1,0,0,&value);
            VF_CHECK(!ok&&value==997&&!strcmp(f->error,"I35: timber dimension requires matching timber material A/B field"),"actual-returned-material-kind-controls-policy");}
        else if(kind==6){ok=vf_resolve(f,ENG_APPLICATION,"a",ENG_PRIMARY_A,1,0,0,&value);
            VF_CHECK(ok&&value==17,"actual-returned-application-controls-selection");
            EngApplication *application=wood_eng_application(&f->context,"a");
            VF_CHECK(application&&!strcmp(application->method.id,"empty")&&application->long_axis==1&&application->main_along==2&&application->overridden[0]&&
                application->overrides[0].value==9&&application->anchor_kind[0]==1&&application->anchor[0]==21&&application->anchor_kind[1]==3,"actual-returned-application-complete-fields");
            VF_CHECK(!strcmp(f->state.applications[0].method.id,"t")&&!f->state.applications[0].overridden[0]&&!f->state.applications[0].anchor_kind[0],"application-shadow-keeps-authored-state");
            VF_CHECK(vf_publish(f,2,"{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"t\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"literal\",\"value\":5}}}")&&
                f->state.application_count==1&&f->state.applications[0].overridden[0]&&f->state.applications[0].overrides[0].value==5,
                "application-put-updates-authored-record-not-shadow");}
        else{ok=vf_resolve(f,ENG_MATERIAL,"t",ENG_A,1,0,0,&value);
            VF_CHECK(!ok&&value==997,"malformed-returned-definition-rejected-without-fallback");
            GeoVersionView raw;GeoVersionSourceKey key;GeoSourceValue quantity={.kind=GEO_SOURCE_QUANTITY,.as.quantity={997,1,GEO_UNIT_LENGTH}};
            VF_CHECK(wood_eng_version_view_direct(&f->context,0,"t",1,&raw),"malformed-raw-identity-remains-valid");
            GeoSourceRef ref=geo_version_source_ref(VF_VERSION,GEO_VERSION_SOURCE_FIELD,raw.identity,ENG_A,&key);
            VF_CHECK(geo_eval_source(f->graph,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&quantity)!=GEO_SOURCE_OK&&quantity.as.quantity.num==997,
                "malformed-returned-definition-cannot-become-raw-quantity");}
        vf_free(f);return 0;
    }
    GeoCoord value=997;VF_CHECK(vf_resolve(f,ENG_MATERIAL,"t",ENG_A,1,0,0,&value),"tamper-evaluation-success");
    if(kind==1)VF_CHECK(value==37,"actual-returned-definition-controls-field");
    else VF_CHECK(value==41,"actual-returned-field-controls-wood-value");
    GeoVersionView version;GeoVersionFieldView original;
    VF_CHECK(wood_eng_version_view(&f->context,0,"t",1,&version)&&geo_versions_field(f->store,version.identity,ENG_A,&original)==GEO_VERSION_OK&&
        original.field.value.num==30,"tamper-does-not-change-immutable-store");
    if(vf_chain(f->graph,VF_VERSION,VF_DIMENSION,0,"t",ENG_A,kind==1?37:41))return 1;vf_free(f);return 0;
}
static int vf_archive(void)
{
    VfFixture *a=vf_fixture(false),*b=vf_fixture(true);VF_CHECK(a&&b,"archive-fixtures");
    VF_CHECK(geo_versions_equal(a->store,b->store)&&wood_engineering_sources_definitions(a->engineering)&&wood_engineering_sources_definitions(b->engineering)&&
        wood_engineering_sources_metadata(a->engineering)&&wood_engineering_sources_metadata(b->engineering),"archive-complete-same-immutable-inventory");
    size_t changed=0;VF_CHECK(geo_eval_node_count(a->graph)==geo_eval_node_count(b->graph)&&geo_eval_edge_count(a->graph)==geo_eval_edge_count(b->graph),"archive-identical-graph-identities");
    for(size_t i=0;i<geo_eval_node_count(a->graph);++i){GeoSourceNodeView x,y;VF_CHECK(geo_eval_node_at(a->graph,i,&x)&&geo_eval_node_at(b->graph,i,&y)&&
        x.source.provider==y.source.provider&&x.source.key_size==y.source.key_size&&!memcmp(x.source.key,y.source.key,x.source.key_size)&&
        x.value&&y.value&&x.value->kind==GEO_SOURCE_DEFINITION&&y.value->kind==GEO_SOURCE_DEFINITION,"archive-matching-definition-nodes");
        const GeoDefinitionValue *p=&x.value->as.definition,*q=&y.value->as.definition;
        VF_CHECK(!strcmp(p->schema,q->schema)&&p->content_size==q->content_size,"archive-matching-schema-and-length");
        if(memcmp(p->content,q->content,p->content_size)){int kind;EngVersionRef identity;bool archived;
            VF_CHECK(!strcmp(p->schema,"woodworking.version-metadata/1")&&wood_engineering_version_metadata_decode(q->content,q->content_size,&kind,&identity,&archived)&&
                !kind&&!strcmp(identity.id,"t")&&identity.version==1&&archived,"archive-only-mutable-metadata-differs");++changed;}}
    VF_CHECK(changed==1,"archive-exactly-one-metadata-change");GeoCoord x,y;
    VF_CHECK(vf_resolve(a,ENG_MATERIAL,"t",ENG_A,1,0,0,&x)&&vf_resolve(b,ENG_MATERIAL,"t",ENG_A,1,0,0,&y)&&x==30&&y==30,"archive-keeps-existing-reference-value");
    VF_CHECK(geo_eval_seal(a->graph)&&geo_eval_seal(b->graph),"archive-seal-independent-candidates");vf_free(a);
    VF_CHECK(vf_resolve(b,ENG_MATERIAL,"t",ENG_A,1,0,0,&y)&&y==30&&geo_version_sources_store(b->versions)==b->store&&geo_version_sources_context(b->versions)==b->graph,"archive-other-candidate-survives-destroy");vf_free(b);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;if(!strcmp(argv[1],"codec"))return vf_codec();if(!strcmp(argv[1],"inventory"))return vf_inventory();
    if(!strcmp(argv[1],"selected"))return vf_selected();if(!strcmp(argv[1],"override"))return vf_override();
    if(!strcmp(argv[1],"definition-tamper"))return vf_tamper(1);if(!strcmp(argv[1],"field-tamper"))return vf_tamper(2);
    if(!strcmp(argv[1],"slot-tamper"))return vf_tamper(3);if(!strcmp(argv[1],"axis-tamper"))return vf_tamper(4);
    if(!strcmp(argv[1],"kind-tamper"))return vf_tamper(5);if(!strcmp(argv[1],"application-tamper"))return vf_tamper(6);
    if(!strcmp(argv[1],"schema-tamper"))return vf_tamper(7);if(!strcmp(argv[1],"unit-tamper"))return vf_tamper(8);
    if(!strcmp(argv[1],"missing-field-tamper"))return vf_tamper(9);
    if(!strcmp(argv[1],"archive"))return vf_archive();return 2;
}
#else
static char *vf_product_dump(const World *world)
{
    FILE *stream=tmpfile();if(!stream)return NULL;world_dump_dsl(world,stream);if(fflush(stream)){fclose(stream);return NULL;}
    long length=ftell(stream);if(length<0||fseek(stream,0,SEEK_SET)){fclose(stream);return NULL;}
    char *text=malloc((size_t)length+1);if(!text){fclose(stream);return NULL;}
    size_t used=fread(text,1,(size_t)length,stream);if(ferror(stream)){free(text);fclose(stream);return NULL;}
    text[used]=0;fclose(stream);return text;
}
static int vf_product_graph(AppWorldCandidate *owner)
{
    ReferenceEval *host=app_candidate_evaluation_state(owner->control);GeoEvalContext *graph=geo_candidate_sources(app_candidate_core(owner->control));
    VF_CHECK(host&&host->world==&owner->after&&host->sources==graph&&geo_eval_is_sealed(graph)&&host->version_sources&&
        geo_version_sources_context(host->version_sources)==graph&&geo_version_sources_store(host->version_sources)==&owner->after.geo.version_store,"product-version-provider-owned-by-candidate");
    VF_CHECK(vf_schema_count(graph,"geometry.version/1")==1&&vf_schema_count(graph,"woodworking.version-metadata/1")==1,"product-complete-version-and-metadata-inventory");
    return vf_chain(graph,APP_SOURCE_VERSION,APP_SOURCE_ENGINEERING_DIMENSION,0,"t",ENG_A,30);
}
int main(int argc,char **argv)
{
    if(argc!=3||strcmp(argv[1],"product"))return 2;memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    VF_CHECK(parse_scene_file(argv[2],&g_world),"product-existing-engineering-scene");history_clear();g_preview.ready=false;
    World *before=malloc(sizeof *before);VF_CHECK(before,"product-snapshot-memory");memcpy(before,&g_world,sizeof *before);uint64_t revision=g_definition_revision;
    VF_CHECK(g_world.wood.engineering.material_count==1&&geo_versions_count(&g_world.geo.version_store)==1,"product-material-version-scene-loaded");
    char *initial_dump=vf_product_dump(&g_world);VF_CHECK(initial_dump,"product-canvaspos-before-dump");
    VF_CHECK(feed_line("version-field-witness",1,"canvas-pos placement 1 17 29",&g_world),"product-material-canvaspos-succeeds");
    VF_CHECK(world_definitions_equal(before,&g_world)&&g_definition_revision==revision,"product-material-canvaspos-keeps-definitions");
    char *display_dump=vf_product_dump(&g_world);size_t initial_length=strlen(initial_dump);
    VF_CHECK(display_dump&&strlen(display_dump)>=initial_length&&!memcmp(initial_dump,display_dump,initial_length)&&
        !strcmp(display_dump+initial_length,"canvas-pos placement 1 17 29\n"),"product-material-canvaspos-exact-dump");
    free(initial_dump);free(display_dump);memcpy(before,&g_world,sizeof *before);
    VF_CHECK(feed_line("version-field-witness",1,"preview spec x 600",&g_world)&&g_preview.ready&&g_preview.valid,"product-valid-preview");
    AppWorldCandidate *owner=g_preview.transaction;GeoCandidate *core=app_candidate_core(owner->control);uint64_t id=geo_candidate_id(core);
    if(vf_product_graph(owner))return 1;
    VF_CHECK(!memcmp(before,&g_world,sizeof *before)&&g_definition_revision==revision&&owner->after.wood.timbers[0].size_a==30,"product-preview-value-and-live-snapshot");
    char command[64];snprintf(command,sizeof command,"confirm %u",g_preview.token);
    VF_CHECK(feed_line("version-field-witness",1,command,&g_world)&&g_preview.transaction==owner&&app_candidate_core(owner->control)==core&&
        geo_candidate_id(core)==id&&geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED,"product-retains-candidate-through-confirm");
    if(vf_product_graph(owner))return 1;
    VF_CHECK(g_world.wood.timbers[0].size_a==30&&g_definition_revision==revision+1,"product-publishes-actual-field-value");
    VF_CHECK(feed_line("version-field-witness",1,"undo",&g_world)&&geo_versions_equal(&g_world.geo.version_store,&before->geo.version_store)&&
        !memcmp(&g_world.wood.engineering,&before->wood.engineering,sizeof before->wood.engineering),"product-one-undo-restores-version-and-metadata");
    free(before);return 0;
}
#endif
