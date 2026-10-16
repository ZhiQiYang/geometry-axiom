#include "engineering_sources.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void wood_binding_u32(unsigned char **p,uint32_t n)
{for(unsigned i=0;i<4;++i)*(*p)++=(unsigned char)(n>>(24-8*i));}
static uint32_t wood_binding_read_u32(const unsigned char **p)
{uint32_t n=0;for(unsigned i=0;i<4;++i)n=(n<<8)|*(*p)++;return n;}
static int wood_binding_signed32(uint32_t n)
{return n<=INT32_MAX?(int)n:-(int)(~n)-1;}
static void wood_binding_target_write(unsigned char **p,const EngTarget *t)
{wood_binding_u32(p,(uint32_t)t->kind);wood_binding_u32(p,t->id);wood_binding_u32(p,(uint32_t)t->axis);wood_binding_u32(p,(uint32_t)t->field);}
static void wood_binding_target_read(const unsigned char **p,EngTarget *t)
{t->kind=wood_binding_signed32(wood_binding_read_u32(p));t->id=wood_binding_read_u32(p);t->axis=wood_binding_signed32(wood_binding_read_u32(p));t->field=wood_binding_signed32(wood_binding_read_u32(p));}
static bool wood_binding_source_write(unsigned char **p,const EngDimensionSource *s)
{
    const char *end=memchr(s->ref,0,sizeof s->ref);if(!end)return false;
    size_t length=(size_t)(end-s->ref);wood_binding_u32(p,(uint32_t)s->kind);wood_binding_u32(p,(uint32_t)s->field);
    uint64_t n=(uint64_t)s->value;for(unsigned i=0;i<8;++i)*(*p)++=(unsigned char)(n>>(56-8*i));
    wood_binding_u32(p,(uint32_t)length);memcpy(*p,s->ref,length);*p+=length;wood_binding_u32(p,s->version);
    *(*p)++=s->parameter.set?1:0;wood_binding_u32(p,s->parameter.parameter_id);wood_binding_u32(p,s->parameter.field_id);return true;
}
static bool wood_binding_source_read(const unsigned char **p,const unsigned char *end,EngDimensionSource *s)
{
    if((size_t)(end-*p)<33)return false;
    s->kind=wood_binding_signed32(wood_binding_read_u32(p));s->field=wood_binding_signed32(wood_binding_read_u32(p));
    uint64_t n=0;for(unsigned i=0;i<8;++i)n=(n<<8)|*(*p)++;
    s->value=n<=INT64_MAX?(int64_t)n:-(int64_t)(~n)-1;
    uint32_t length=wood_binding_read_u32(p);
    if(length>=sizeof s->ref||(size_t)(end-*p)<(size_t)length+13||memchr(*p,0,length))return false;
    memcpy(s->ref,*p,length);s->ref[length]=0;*p+=length;s->version=wood_binding_read_u32(p);
    unsigned set=*(*p)++;if(set>1)return false;s->parameter.set=set!=0;
    s->parameter.parameter_id=wood_binding_read_u32(p);s->parameter.field_id=wood_binding_read_u32(p);return true;
}
size_t wood_engineering_binding_encode(const EngBinding *binding,unsigned char out[WOOD_ENGINEERING_BINDING_CONTENT_MAX])
{
    if(!binding||!out)return 0;unsigned char bytes[WOOD_ENGINEERING_BINDING_CONTENT_MAX],*p=bytes;
    wood_binding_target_write(&p,&binding->target);if(!wood_binding_source_write(&p,&binding->source))return 0;
    *p++=binding->has_override?1:0;
    if(binding->has_override&&!wood_binding_source_write(&p,&binding->override_value))return 0;
    size_t length=(size_t)(p-bytes);memcpy(out,bytes,length);return length;
}
bool wood_engineering_binding_decode(const void *data,size_t size,EngBinding *out)
{
    if(!data||!out||size<50||size>WOOD_ENGINEERING_BINDING_CONTENT_MAX)return false;
    const unsigned char *p=data,*end=p+size;EngBinding value;memset(&value,0,sizeof value);
    wood_binding_target_read(&p,&value.target);if(!wood_binding_source_read(&p,end,&value.source)||p==end)return false;
    unsigned has=*p++;if(has>1)return false;value.has_override=has!=0;
    if(value.has_override&&!wood_binding_source_read(&p,end,&value.override_value))return false;
    if(p!=end)return false;memcpy(out,&value,sizeof value);return true;
}
GeoSourceRef wood_engineering_binding_source_ref(GeoProviderToken token,WoodEngineeringBindingSourceKind kind,
    const EngBinding *binding,WoodEngineeringBindingSourceKey *key)
{
    if(!binding||!key||kind<WOOD_BINDING_SOURCE_DEFINITION||kind>WOOD_BINDING_SOURCE_REQUEST_VALUE)return (GeoSourceRef){token,NULL,0};
    key->bytes[0]=(unsigned char)kind;
    if(kind<=WOOD_BINDING_SOURCE_EFFECTIVE){unsigned char *p=key->bytes+1;wood_binding_target_write(&p,&binding->target);key->size=17;}
    else{size_t n=wood_engineering_binding_encode(binding,key->bytes+1);if(!n)return (GeoSourceRef){token,NULL,0};key->size=n+1;}
    return (GeoSourceRef){token,key->bytes,key->size};
}
bool wood_engineering_binding_source_decode(const GeoSourceRef *source,WoodEngineeringBindingSourceKind *kind,
    EngTarget *target,EngBinding *request)
{
    if(!source||!source->key||!kind||!target||!source->key_size)return false;
    const unsigned char *p=source->key;WoodEngineeringBindingSourceKind k=(WoodEngineeringBindingSourceKind)*p++;
    EngBinding value;memset(&value,0,sizeof value);
    if(k==WOOD_BINDING_SOURCE_DEFINITION||k==WOOD_BINDING_SOURCE_EFFECTIVE){
        if(source->key_size!=17)return false;wood_binding_target_read(&p,&value.target);
    }else if(k==WOOD_BINDING_SOURCE_REQUEST_DEFINITION||k==WOOD_BINDING_SOURCE_REQUEST_VALUE){
        if(!wood_engineering_binding_decode(p,source->key_size-1,&value))return false;
    }else return false;
    *kind=k;*target=value.target;if(request)memcpy(request,&value,sizeof value);return true;
}

typedef struct {
    EngDimensionSource source;
    EngTarget target;
    uint32_t placement;
    int role;
} WoodDimensionKey;
typedef struct {int kind;uint32_t version;char id[ENG_ID_MAX];} WoodDefinitionKey;
typedef struct WoodDimensionResult WoodDimensionResult;
struct WoodDimensionResult {
    GeoProviderToken provider;
    union {WoodDimensionKey dimension;unsigned char binding[WOOD_ENGINEERING_BINDING_KEY_MAX];} key;
    size_t key_size;
    unsigned char definition[WOOD_ENGINEERING_BINDING_CONTENT_MAX];
    size_t definition_size;
    GeoCoord value;
    GeoCoord *requested_output;
    size_t attempts;
    char path[512];
    WoodDimensionResult *next;
};
struct WoodEngineeringSources {
    GeoEvalContext *evaluation;
    WoodEngineeringContext context;
    WoodEngineeringSourceTokens tokens;
    WoodDimensionResult *results;
};
static void wood_source_dimension_copy(EngDimensionSource *out,const EngDimensionSource *in)
{
    memset(out,0,sizeof *out);out->kind=in->kind;out->field=in->field;out->value=in->value;
    memcpy(out->ref,in->ref,strlen(in->ref)+1);out->version=in->version;
    out->parameter.set=in->parameter.set;out->parameter.parameter_id=in->parameter.parameter_id;out->parameter.field_id=in->parameter.field_id;
}
static void wood_source_target_copy(EngTarget *out,const EngTarget *in)
{memset(out,0,sizeof *out);out->kind=in->kind;out->id=in->id;out->axis=in->axis;out->field=in->field;}
static WoodDimensionResult *wood_source_result(WoodEngineeringSources *s,GeoProviderToken token,const void *key,size_t size,bool create)
{
    for(WoodDimensionResult *r=s->results;r;r=r->next)
        if(r->provider==token&&r->key_size==size&&!memcmp(&r->key,key,size))return r;
    if(!create||size>sizeof ((WoodDimensionResult *)0)->key)return NULL;
    WoodDimensionResult *r=calloc(1,sizeof *r);if(!r)return NULL;
    r->provider=token;r->key_size=size;memcpy(&r->key,key,size);r->next=s->results;s->results=r;return r;
}
static bool wood_source_failure(WoodEngineeringSources *s,GeoSourceStatus status)
{
    if(status==GEO_SOURCE_MEMORY)return wood_eng_fail(&s->context,"I10: engineering source graph capacity exceeded");
    if(status==GEO_SOURCE_CYCLE)return wood_eng_fail(&s->context,"I35: cyclic dimension source");
    return false;
}
static bool wood_source_result_value(WoodEngineeringSources *s,WoodDimensionResult *r,GeoCoord *out,char *path,size_t cap)
{
    if(!r)return wood_source_failure(s,GEO_SOURCE_MEMORY);
    size_t attempts=r->attempts;r->requested_output=out;
    GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){r->provider,&r->key,r->key_size},GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    r->requested_output=NULL;
    if(status!=GEO_SOURCE_OK){
        if(path&&r->attempts!=attempts&&r->path[0]!='\177')snprintf(path,cap,"%s",r->path);
        return wood_source_failure(s,status);
    }
    *out=value.as.quantity.num;if(path)snprintf(path,cap,"%s",r->path);return true;
}
static bool wood_source_resolve(void *opaque,const EngDimensionSource *source,const EngTarget *target,uint32_t pid,int role,GeoCoord *out,char *path,size_t cap)
{
    WoodEngineeringSources *s=opaque;WoodDimensionKey key;memset(&key,0,sizeof key);
    wood_source_dimension_copy(&key.source,source);wood_source_target_copy(&key.target,target);key.placement=pid;key.role=role;
    return wood_source_result_value(s,wood_source_result(s,s->tokens.dimension,&key,sizeof key,true),out,path,cap);
}
static bool wood_source_binding(void *opaque,const EngBinding *binding,GeoCoord *out,char *path,size_t cap)
{
    WoodEngineeringSources *s=opaque;unsigned char payload[WOOD_ENGINEERING_BINDING_CONTENT_MAX],stored_payload[WOOD_ENGINEERING_BINDING_CONTENT_MAX];
    size_t size=wood_engineering_binding_encode(binding,payload);if(!size)return false;
    const EngBinding *stored=wood_eng_binding(&s->context,&binding->target);
    size_t stored_size=stored?wood_engineering_binding_encode(stored,stored_payload):0;
    bool owned=stored_size==size&&!memcmp(payload,stored_payload,size);
    WoodEngineeringBindingSourceKey key;
    GeoSourceRef ref=wood_engineering_binding_source_ref(s->tokens.binding,
        owned?WOOD_BINDING_SOURCE_EFFECTIVE:WOOD_BINDING_SOURCE_REQUEST_VALUE,binding,&key);
    WoodDimensionResult *result=wood_source_result(s,ref.provider,ref.key,ref.key_size,true);
    if(!result)return wood_source_failure(s,GEO_SOURCE_MEMORY);
    if(result->definition_size&&(result->definition_size!=size||memcmp(result->definition,payload,size)))
        return wood_eng_fail(&s->context,"I8: engineering binding definition changed during evaluation");
    memcpy(result->definition,payload,size);result->definition_size=size;
    return wood_source_result_value(s,result,out,path,cap);
}
static bool wood_source_named(void *opaque,const char *name,GeoCoord *out)
{
    WoodEngineeringSources *s=opaque;GeoSourceValue value;
    if(geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.named,name,strlen(name)},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    if(value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den!=1)return false;
    *out=value.as.quantity.num;return true;
}
static bool wood_source_parameter(void *opaque,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{
    WoodEngineeringSources *s=opaque;
    /* Retain the established field-kind/integer/range diagnostics before the
     * shared graph supplies the actual value and transitive AST dependencies. */
    if(!s->context.parameter(s->context.user,ref,out,error,cap))return false;
    GeoCoord checked=*out;
    uint32_t key[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    if(status!=GEO_SOURCE_OK)return wood_source_failure(s,status);
    if(value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den!=1||value.as.quantity.num!=checked)return false;
    *out=value.as.quantity.num;return true;
}
static bool wood_source_definition_key(WoodDefinitionKey *key,int kind,const char *id,uint32_t version)
{
    if(!id||strlen(id)>=sizeof key->id||kind<0||kind>2)return false;
    memset(key,0,sizeof *key);key->kind=kind;key->version=version;memcpy(key->id,id,strlen(id)+1);return true;
}
static bool wood_source_definition(void *opaque,int kind,const char *id,uint32_t version)
{
    WoodEngineeringSources *s=opaque;WoodDefinitionKey key;
    if(!wood_source_definition_key(&key,kind,id,version))return false;
    GeoSourceRef ref={s->tokens.definition,&key,sizeof key};GeoSourceStatus status;
    if(kind==2)status=geo_eval_depend(s->evaluation,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED);
    else{GeoSourceValue value;status=geo_eval_source(s->evaluation,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
    return status==GEO_SOURCE_OK?true:wood_source_failure(s,status);
}
static bool wood_source_application(void *opaque,const EngApplication *a)
{
    WoodEngineeringSources *s=opaque;WoodDefinitionKey key;GeoSourceValue value;
    if(!wood_source_definition_key(&key,2,a->id,0))return false;
    GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.definition,&key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    return status==GEO_SOURCE_OK?true:wood_source_failure(s,status);
}
void wood_engineering_sources_bind(WoodEngineeringSources *s,WoodEngineeringContext *context)
{
    if(!s||!context)return;
    context->sources=s;context->resolve_source=wood_source_resolve;context->resolve_binding=wood_source_binding;
    context->source_named=wood_source_named;context->source_parameter=wood_source_parameter;
    context->depend_definition=wood_source_definition;context->validate_application=wood_source_application;
}
static bool wood_source_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodEngineeringSources *s=opaque;memset(out,0,sizeof *out);out->context.axis=-1;out->retry_failure=true;
    if(ref->provider==s->tokens.definition){
        if(ref->key_size!=sizeof(WoodDefinitionKey))return false;
        WoodDefinitionKey key;memcpy(&key,ref->key,sizeof key);
        if(!memchr(key.id,0,sizeof key.id)||key.kind<0||key.kind>2)return false;
        bool found=false;
        if(key.kind<2){
            /* Metadata completion also runs after evaluation has been hashed.
             * Check the K version and W identity without refreshing W caches. */
            GeoVersionView version;
            if(wood_eng_version_view(&s->context,key.kind,key.id,key.version,&version)){
                EngineeringState *state=s->context.state;
                size_t count=key.kind?state->method_count:state->material_count;
                for(size_t i=0;i<count;++i){const EngVersionRef *identity=key.kind?&state->methods[i].ref:&state->materials[i].ref;
                    if(identity->version==key.version&&!strcmp(identity->id,key.id)){found=true;break;}}
            }
        }else found=wood_eng_application(&s->context,key.id)!=NULL;
        if(!found)return false;out->kind=GEO_SOURCE_DEFINITION;out->unit=GEO_UNIT_SCALAR;return true;
    }
    if(ref->provider==s->tokens.binding){
        WoodEngineeringBindingSourceKind kind;EngTarget target;EngBinding request;
        if(!wood_engineering_binding_source_decode(ref,&kind,&target,&request))return false;
        if(kind==WOOD_BINDING_SOURCE_DEFINITION||kind==WOOD_BINDING_SOURCE_REQUEST_DEFINITION){
            if(kind==WOOD_BINDING_SOURCE_DEFINITION&&!wood_eng_binding(&s->context,&target))return false;
            out->kind=GEO_SOURCE_DEFINITION;out->unit=GEO_UNIT_SCALAR;return true;
        }
    }
    if(!wood_source_result(s,ref->provider,ref->key,ref->key_size,false))return false;
    out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;return true;
}
static bool wood_source_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodEngineeringSources *s=opaque;if(ctx!=s->evaluation)return false;
    if(ref->provider==s->tokens.definition){
        WoodDefinitionKey key;if(ref->key_size!=sizeof key)return false;memcpy(&key,ref->key,sizeof key);
        const char *content,*schema;size_t content_size;
        if(key.kind==0){GeoVersionView version;if(!wood_eng_version_view(&s->context,0,key.id,key.version,&version))return false;content=version.content;schema=version.schema;content_size=version.content_length;}
        else if(key.kind==1){
            const EngMethodVersion *m=wood_eng_method(&s->context,key.id,key.version);if(!m)return false;
            GeoVersionView version;if(!wood_eng_version_view(&s->context,1,key.id,key.version,&version))return false;
            content=version.content;schema=version.schema;content_size=version.content_length;
            /* Version identities are retained even for currently unused slots;
             * their field values are evaluated only when the policy selects them. */
            const EngVersionRef *refs[]={&m->panel,&m->roles[0],&m->roles[1],&m->roles[2]};
            for(size_t i=0;i<4;++i)if(refs[i]->id[0]){
                WoodDefinitionKey upstream;if(!wood_source_definition_key(&upstream,0,refs[i]->id,refs[i]->version))return false;
                if(geo_eval_depend(ctx,(GeoSourceRef){s->tokens.definition,&upstream,sizeof upstream},GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
            }
        }else if(key.kind==2){
            EngApplication *a=wood_eng_application(&s->context,key.id);if(!a||!wood_eng_validate_application_direct(&s->context,a))return false;
            content=a->content;schema="woodworking.face-application/1";content_size=strlen(content);
        }else return false;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,content,content_size};return true;
    }
    if(ref->provider==s->tokens.binding){
        WoodEngineeringBindingSourceKind kind;EngTarget target;EngBinding request;
        if(!wood_engineering_binding_source_decode(ref,&kind,&target,&request))return false;
        if(kind==WOOD_BINDING_SOURCE_DEFINITION||kind==WOOD_BINDING_SOURCE_REQUEST_DEFINITION){
            const EngBinding *binding=kind==WOOD_BINDING_SOURCE_DEFINITION?wood_eng_binding(&s->context,&target):&request;
            WoodDimensionResult *definition=wood_source_result(s,ref->provider,ref->key,ref->key_size,true);
            if(!binding||!definition)return false;
            size_t size=wood_engineering_binding_encode(binding,definition->definition);if(!size)return false;
            definition->definition_size=size;out->kind=GEO_SOURCE_DEFINITION;
            out->as.definition=(GeoDefinitionValue){"woodworking.dimension-binding/2",definition->definition,size};return true;
        }
    }
    WoodDimensionResult *result=wood_source_result(s,ref->provider,ref->key,ref->key_size,false);if(!result)return false;
    /* The legacy policy may write an invalid numeric value into candidate
     * diagnostic state before rejecting it. Use that exact caller destination;
     * K still publishes no value for the failed source. */
    GeoCoord *destination=result->requested_output;if(!destination)return false;
    ++result->attempts;result->path[0]='\177';result->path[1]=0;
    bool ok;
    if(ref->provider==s->tokens.dimension){WoodDimensionKey *key=&result->key.dimension;
        ok=wood_eng_resolve_direct(&s->context,&key->source,&key->target,key->placement,key->role,destination,result->path,sizeof result->path);
    }else if(ref->provider==s->tokens.binding){
        WoodEngineeringBindingSourceKind kind;EngTarget target;EngBinding binding;
        if(!wood_engineering_binding_source_decode(ref,&kind,&target,&binding)||
           !wood_engineering_binding_decode(result->definition,result->definition_size,&binding))return false;
        WoodEngineeringBindingSourceKey key;GeoSourceValue definition;
        GeoSourceRef upstream=wood_engineering_binding_source_ref(s->tokens.binding,
            kind==WOOD_BINDING_SOURCE_EFFECTIVE?WOOD_BINDING_SOURCE_DEFINITION:WOOD_BINDING_SOURCE_REQUEST_DEFINITION,&binding,&key);
        if(geo_eval_source(ctx,upstream,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK||
           definition.kind!=GEO_SOURCE_DEFINITION)return false;
        if(definition.as.definition.content_size!=result->definition_size||
           memcmp(definition.as.definition.content,result->definition,result->definition_size))
            return wood_eng_fail(&s->context,"I8: engineering binding definition changed during evaluation");
        if(!wood_engineering_binding_decode(definition.as.definition.content,definition.as.definition.content_size,&binding))return false;
        ok=wood_eng_effective_direct(&s->context,&binding,destination,result->path,sizeof result->path);
    }
    else return false;
    if(!ok)return false;result->value=*destination;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){result->value,1,GEO_UNIT_LENGTH};return true;
}
WoodEngineeringSources *wood_engineering_sources_register(GeoEvalContext *ctx,const WoodEngineeringContext *context,WoodEngineeringSourceTokens tokens)
{
    if(!ctx||!context||!context->state)return NULL;
    WoodEngineeringSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->evaluation=ctx;s->context=*context;s->tokens=tokens;wood_engineering_sources_bind(s,&s->context);
    GeoSourceProvider providers[]={
        {tokens.dimension,"woodworking.dimension-source","woodworking.dimension-source/1",s,wood_source_describe,wood_source_evaluate},
        {tokens.binding,"woodworking.dimension-binding","woodworking.dimension-binding/2",s,wood_source_describe,wood_source_evaluate},
        {tokens.definition,"woodworking.engineering-definition","woodworking.engineering-definition/1",s,wood_source_describe,wood_source_evaluate}};
    if(!geo_eval_register_many(ctx,providers,3)){wood_engineering_sources_destroy(s);return NULL;}
    return s;
}
void wood_engineering_sources_destroy(WoodEngineeringSources *s)
{if(s){WoodDimensionResult *r=s->results;while(r){WoodDimensionResult *next=r->next;free(r);r=next;}free(s);}}
bool wood_engineering_sources_definitions(WoodEngineeringSources *s)
{
    if(!s)return false;
    const EngineeringState *state=s->context.state;
    /* Rebuild has already validated applications and effective bindings in
     * their original order. Finish the inventory without asking W to resolve
     * an unselected material field, method slot or binding value. */
    for(size_t i=0;i<state->material_count;++i){
        const EngVersionRef *identity=&state->materials[i].ref;WoodDefinitionKey key;GeoSourceValue value;
        if(!wood_source_definition_key(&key,0,identity->id,identity->version))return false;
        GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.definition,&key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);
        if(status!=GEO_SOURCE_OK)return wood_source_failure(s,status);
    }
    for(size_t i=0;i<state->method_count;++i){
        const EngVersionRef *identity=&state->methods[i].ref;WoodDefinitionKey key;GeoSourceValue value;
        if(!wood_source_definition_key(&key,1,identity->id,identity->version))return false;
        GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.definition,&key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);
        if(status!=GEO_SOURCE_OK)return wood_source_failure(s,status);
    }
    for(size_t i=0;i<state->application_count;++i){
        WoodDefinitionKey key;GeoSourceValue value;
        if(!wood_source_definition_key(&key,2,state->applications[i].id,0))return false;
        GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.definition,&key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);
        if(status!=GEO_SOURCE_OK)return wood_source_failure(s,status);
    }
    for(size_t i=0;i<state->binding_count;++i){
        WoodEngineeringBindingSourceKey key;GeoSourceValue value;
        GeoSourceRef ref=wood_engineering_binding_source_ref(s->tokens.binding,WOOD_BINDING_SOURCE_DEFINITION,&state->bindings[i],&key);
        GeoSourceStatus status=geo_eval_source(s->evaluation,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);
        if(status!=GEO_SOURCE_OK)return wood_source_failure(s,status);
    }
    return true;
}
const EngineeringState *wood_engineering_sources_state(const WoodEngineeringSources *s){return s?s->context.state:NULL;}
GeoEvalContext *wood_engineering_sources_context(const WoodEngineeringSources *s){return s?s->evaluation:NULL;}
