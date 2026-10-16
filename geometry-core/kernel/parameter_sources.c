#include "parameter_sources.h"
#include "internal/parameter_store.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>

typedef struct GeoParameterDefinitionResult GeoParameterDefinitionResult;
struct GeoParameterDefinitionResult {
    GeoParameterDefinitionKey key;
    unsigned char content[GEO_PARAMETER_FIELD_CONTENT_MAX];size_t size;
    GeoParameterDefinitionResult *next;
};
struct GeoParameterSources {
    GeoEvalContext *sources;
    GeoParameterStore *store;
    GeoParameterStore *working;
    GeoParameterEvaluation *evaluation;
    GeoProviderToken token,definition_token;
    GeoParameterDefinitionResult *definitions;
    GeoParameterError definition_error;
};
static void geo_parameter_definition_u32(unsigned char *p,uint32_t value)
{for(unsigned i=0;i<4;++i)p[i]=(unsigned char)(value>>(24-8*i));}
static uint32_t geo_parameter_definition_read32(const unsigned char *p)
{uint32_t n=0;for(unsigned i=0;i<4;++i)n=(n<<8)|p[i];return n;}
GeoSourceRef geo_parameter_definition_source_ref(GeoProviderToken token,GeoParameterDefinitionKind kind,
    uint32_t card,uint32_t field,GeoParameterDefinitionKey *out)
{
    if(!out)return (GeoSourceRef){token,NULL,0};
    geo_parameter_definition_u32(out->bytes,(uint32_t)kind);geo_parameter_definition_u32(out->bytes+4,card);
    geo_parameter_definition_u32(out->bytes+8,kind==GEO_PARAMETER_DEFINITION_CARD?0:field);
    return (GeoSourceRef){token,out->bytes,sizeof out->bytes};
}
bool geo_parameter_definition_source_decode(const GeoSourceRef *source,GeoParameterDefinitionKind *kind,
    uint32_t *card,uint32_t *field)
{
    if(!source||!source->key||source->key_size!=12||!kind||!card||!field)return false;
    const unsigned char *p=source->key;uint32_t k=geo_parameter_definition_read32(p);
    uint32_t c=geo_parameter_definition_read32(p+4),f=geo_parameter_definition_read32(p+8);
    if(k==GEO_PARAMETER_DEFINITION_CARD){if(f)return false;}
    else if(k!=GEO_PARAMETER_DEFINITION_FIELD)return false;
    *kind=(GeoParameterDefinitionKind)k;*card=c;*field=f;return true;
}
static bool geo_parameter_definition_text(const char *text,size_t capacity,size_t *size,bool name)
{
    const char *end=memchr(text,0,capacity);if(!end)return false;size_t n=(size_t)(end-text);
    if(name&&!geo_utf8_name_valid((const unsigned char *)text,n,GEO_PARAMETER_NAME_MAX-1))return false;
    *size=n;return true;
}
static bool geo_parameter_card_definition_valid(const GeoParameterCard *card,size_t *name_size)
{
    if(!card||card->count>GEO_PARAMETER_FIELDS_PER_CARD||
       !geo_parameter_definition_text(card->name,sizeof card->name,name_size,true))return false;
    for(size_t i=0;i<card->count;++i){
        if(card->next_field_id&&card->fields[i]>=card->next_field_id)return false;
        for(size_t j=0;j<i;++j)if(card->fields[j]==card->fields[i])return false;
    }
    return true;
}
size_t geo_parameter_card_definition_encode(const GeoParameterCard *card,void *out,size_t capacity)
{
    size_t name_size;if(!out||!geo_parameter_card_definition_valid(card,&name_size))return 0;
    size_t size=16+name_size+4*card->count;if(capacity<size)return 0;
    unsigned char bytes[GEO_PARAMETER_CARD_CONTENT_MAX];
    geo_parameter_definition_u32(bytes,card->id);geo_parameter_definition_u32(bytes+4,card->next_field_id);
    geo_parameter_definition_u32(bytes+8,(uint32_t)name_size);memcpy(bytes+12,card->name,name_size);
    size_t at=12+name_size;geo_parameter_definition_u32(bytes+at,(uint32_t)card->count);at+=4;
    for(size_t i=0;i<card->count;++i){geo_parameter_definition_u32(bytes+at,card->fields[i]);at+=4;}
    memcpy(out,bytes,size);return size;
}
bool geo_parameter_card_definition_decode(const void *content,size_t size,GeoParameterCard *out)
{
    if(!content||!out||size<16||size>GEO_PARAMETER_CARD_CONTENT_MAX)return false;
    const unsigned char *p=content;GeoParameterCard card={0};card.id=geo_parameter_definition_read32(p);
    card.next_field_id=geo_parameter_definition_read32(p+4);size_t n=geo_parameter_definition_read32(p+8);
    if(n>=sizeof card.name||n>size-16||memchr(p+12,0,n))return false;
    memcpy(card.name,p+12,n);size_t at=12+n;card.count=geo_parameter_definition_read32(p+at);at+=4;
    if(card.count>GEO_PARAMETER_FIELDS_PER_CARD||card.count!=(size-at)/4||(size-at)%4)return false;
    for(size_t i=0;i<card.count;++i){card.fields[i]=geo_parameter_definition_read32(p+at);at+=4;}
    size_t name_size;if(at!=size||!geo_parameter_card_definition_valid(&card,&name_size))return false;
    *out=card;return true;
}
/* Syntax canonicalization is not semantic AST validation. Invalid syntax is
 * retained verbatim, allowing the original parser to own its first error. */
static bool geo_parameter_definition_expression(const char *expression,char *out,size_t *size)
{
    GeoJson json;bool parsed=geo_json_parse(&json,expression);
    bool canonical=parsed&&geo_json_canonical(&json,0,out,GEO_PARAMETER_EXPR_MAX);
    geo_json_free(&json);
    if(!canonical)memcpy(out,expression,strlen(expression)+1);
    *size=strlen(out);return canonical;
}
size_t geo_parameter_field_definition_encode(const GeoParameterField *field,void *out,size_t capacity)
{
    size_t name_size,input_size;
    if(!out||!field||field->type<GEO_PARAMETER_DIMENSION||field->type>GEO_PARAMETER_RATIO||
       !geo_parameter_definition_text(field->name,sizeof field->name,&name_size,true)||
       !geo_parameter_definition_text(field->expression,sizeof field->expression,&input_size,false))return 0;
    char expression[GEO_PARAMETER_EXPR_MAX];size_t expression_size;
    bool canonical=geo_parameter_definition_expression(field->expression,expression,&expression_size);
    size_t size=21+name_size+expression_size;if(capacity<size)return 0;
    unsigned char bytes[GEO_PARAMETER_FIELD_CONTENT_MAX];geo_parameter_definition_u32(bytes,field->parameter_id);
    geo_parameter_definition_u32(bytes+4,field->id);geo_parameter_definition_u32(bytes+8,(uint32_t)field->type);
    geo_parameter_definition_u32(bytes+12,(uint32_t)name_size);memcpy(bytes+16,field->name,name_size);
    size_t at=16+name_size;bytes[at++]=canonical?1:0;
    geo_parameter_definition_u32(bytes+at,(uint32_t)expression_size);at+=4;memcpy(bytes+at,expression,expression_size);
    memcpy(out,bytes,size);return size;
}
bool geo_parameter_field_definition_decode(const void *content,size_t size,GeoParameterField *out)
{
    if(!content||!out||size<21||size>GEO_PARAMETER_FIELD_CONTENT_MAX)return false;
    const unsigned char *p=content;GeoParameterField field={0};field.parameter_id=geo_parameter_definition_read32(p);
    field.id=geo_parameter_definition_read32(p+4);uint32_t type=geo_parameter_definition_read32(p+8);
    size_t n=geo_parameter_definition_read32(p+12);if(type>GEO_PARAMETER_RATIO||n>=sizeof field.name||n>size-21||memchr(p+16,0,n))return false;
    field.type=(int)type;memcpy(field.name,p+16,n);size_t at=16+n;unsigned canonical=p[at++];
    if(canonical>1)return false;size_t expression_size=geo_parameter_definition_read32(p+at);at+=4;
    if(expression_size>=sizeof field.expression||expression_size!=size-at||memchr(p+at,0,expression_size))return false;
    memcpy(field.expression,p+at,expression_size);size_t name_size;
    if(!geo_parameter_definition_text(field.name,sizeof field.name,&name_size,true))return false;
    char expected[GEO_PARAMETER_EXPR_MAX];size_t expected_size;
    bool actual=geo_parameter_definition_expression(field.expression,expected,&expected_size);
    if(actual!=(canonical!=0)||expected_size!=expression_size||memcmp(expected,field.expression,expression_size))return false;
    *out=field;return true;
}
static bool geo_parameter_source_ref(const GeoParameterSources *state,const GeoSourceRef *source,GeoParameterRef *ref)
{
    if(source->provider!=state->token||source->key_size!=2*sizeof(uint32_t)||!source->key)return false;
    uint32_t ids[2];memcpy(ids,source->key,sizeof ids);
    *ref=(GeoParameterRef){true,ids[0],ids[1]};return true;
}
static GeoParameterStatus geo_parameter_source_status(GeoSourceStatus status)
{
    switch(status){
    case GEO_SOURCE_OK:return GEO_PARAMETER_OK;
    case GEO_SOURCE_CYCLE:return GEO_PARAMETER_CYCLE;
    case GEO_SOURCE_MISSING:return GEO_PARAMETER_MISSING_FIELD;
    case GEO_SOURCE_MEMORY:return GEO_PARAMETER_MEMORY;
    default:return GEO_PARAMETER_INVALID_DEFINITION;
    }
}
static GeoParameterStatus geo_parameter_source_resolve(void *opaque,GeoParameterRef ref,GeoQuantity *out)
{
    GeoParameterSources *state=opaque;uint32_t ids[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(state->sources,(GeoSourceRef){state->token,ids,sizeof ids},
        GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    if(status==GEO_SOURCE_OK)*out=value.as.quantity;
    return geo_parameter_source_status(status);
}
static bool geo_parameter_definition_failure(GeoParameterSources *s,GeoParameterStatus status,GeoParameterRef ref)
{memset(&s->definition_error,0,sizeof s->definition_error);s->definition_error.status=status;s->definition_error.source=ref;return false;}
static bool geo_parameter_definition_get(GeoParameterSources *s,GeoParameterDefinitionKind kind,
    uint32_t card,uint32_t field,GeoSourceValue *out)
{
    GeoParameterDefinitionKey key;
    GeoSourceStatus status=geo_eval_source(s->sources,
        geo_parameter_definition_source_ref(s->definition_token,kind,card,field,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,out);
    return status==GEO_SOURCE_OK?true:geo_parameter_definition_failure(s,geo_parameter_source_status(status),(GeoParameterRef){true,card,field});
}
static bool geo_parameter_card_contains(const GeoParameterCard *card,uint32_t field)
{for(size_t i=0;i<card->count;++i)if(card->fields[i]==field)return true;return false;}
static GeoParameterDefinitionResult *geo_parameter_definition_record(GeoParameterSources *s,
    GeoParameterDefinitionKind kind,uint32_t card,uint32_t field)
{
    GeoParameterDefinitionKey key;(void)geo_parameter_definition_source_ref(s->definition_token,kind,card,field,&key);
    for(GeoParameterDefinitionResult *r=s->definitions;r;r=r->next)
        if(!memcmp(r->key.bytes,key.bytes,sizeof key.bytes))return r;
    unsigned char content[GEO_PARAMETER_FIELD_CONTENT_MAX];size_t size=0;
    if(kind==GEO_PARAMETER_DEFINITION_CARD){const GeoParameterCard *authored=geo_parameters_find(s->store,card);
        if(authored)size=geo_parameter_card_definition_encode(authored,content,sizeof content);
    }else{int index=geo_parameters_field_index(s->store,card,field);
        if(index>=0)size=geo_parameter_field_definition_encode(&geo_parameters_fields(s->store)[index],content,sizeof content);}
    if(!size)return NULL;GeoParameterDefinitionResult *result=calloc(1,sizeof *result);if(!result)return NULL;
    result->key=key;memcpy(result->content,content,size);result->size=size;result->next=s->definitions;s->definitions=result;
    return result;
}
static bool geo_parameter_definition_describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    GeoParameterSources *s=opaque;GeoParameterDefinitionKind kind;uint32_t card,field;
    if(source->provider!=s->definition_token||!geo_parameter_definition_source_decode(source,&kind,&card,&field))return false;
    *out=(GeoSourceDescriptor){.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1}};return true;
}
static bool geo_parameter_definition_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *source,GeoSourceValue *out)
{
    GeoParameterSources *s=opaque;GeoParameterDefinitionKind kind;uint32_t card,field;
    if(ctx!=s->sources||source->provider!=s->definition_token||!geo_parameter_definition_source_decode(source,&kind,&card,&field))return false;
    const char *schema;
    if(kind==GEO_PARAMETER_DEFINITION_CARD){
        schema="geometry.parameter-card/1";
    }else{
        GeoSourceValue owner;GeoParameterCard decoded;
        if(!geo_parameter_definition_get(s,GEO_PARAMETER_DEFINITION_CARD,card,0,&owner)||
           owner.kind!=GEO_SOURCE_DEFINITION||strcmp(owner.as.definition.schema,"geometry.parameter-card/1")||
           !geo_parameter_card_definition_decode(owner.as.definition.content,owner.as.definition.content_size,&decoded)||
           decoded.id!=card||!geo_parameter_card_contains(&decoded,field))return false;
        schema="geometry.parameter-field/1";
    }
    GeoParameterDefinitionResult *result=geo_parameter_definition_record(s,kind,card,field);if(!result)return false;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,result->content,result->size};return true;
}
static bool geo_parameter_source_working(GeoParameterSources *s,GeoParameterRef ref)
{
    if(s->evaluation)return true;
    s->working=geo_parameters_clone(s->store);
    if(s->working)s->evaluation=geo_parameter_evaluation_create(s->working,geo_parameter_source_resolve,s);
    if(s->evaluation)return true;
    geo_parameters_destroy(s->working);s->working=NULL;
    return geo_parameter_definition_failure(s,GEO_PARAMETER_MEMORY,ref);
}
static bool geo_parameter_source_definition(GeoParameterSources *s,GeoParameterRef ref,int index)
{
    GeoSourceValue definition;GeoParameterField field;
    if(!geo_parameter_definition_get(s,GEO_PARAMETER_DEFINITION_FIELD,ref.parameter_id,ref.field_id,&definition))return false;
    if(definition.kind!=GEO_SOURCE_DEFINITION||strcmp(definition.as.definition.schema,"geometry.parameter-field/1")||
       !geo_parameter_field_definition_decode(definition.as.definition.content,definition.as.definition.content_size,&field)||
       field.parameter_id!=ref.parameter_id||field.id!=ref.field_id)
        return geo_parameter_definition_failure(s,GEO_PARAMETER_INVALID_DEFINITION,ref);
    /* The original parser and its recursive state consume only these returned
     * authored bytes. Preserve its previous cache until this field succeeds. */
    GeoQuantity cached=s->working->fields[index].value;
    s->working->fields[index]=field;s->working->fields[index].value=cached;return true;
}
static bool geo_parameter_source_describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    GeoParameterSources *state=opaque;GeoParameterRef ref;
    if(!geo_parameter_source_ref(state,source,&ref))return false;
    int index=geo_parameters_field_index(state->store,ref.parameter_id,ref.field_id);
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->context.axis=-1;
    out->unit=index>=0&&geo_parameters_fields(state->store)[index].type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;
    if(state->definition_token&&index>=0){
        /* Describing a quantity freezes only authored metadata, never a K
         * source value or a quantity. The later field provider returns this
         * same record after recording its real card dependency. */
        GeoParameterDefinitionResult *owner=geo_parameter_definition_record(state,GEO_PARAMETER_DEFINITION_CARD,ref.parameter_id,0);
        GeoParameterDefinitionResult *record=geo_parameter_definition_record(state,GEO_PARAMETER_DEFINITION_FIELD,ref.parameter_id,ref.field_id);
        GeoParameterField definition;
        if(!owner||!record||!geo_parameter_field_definition_decode(record->content,record->size,&definition))return false;
        out->unit=definition.type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;
    }
    return true;
}
static bool geo_parameter_source_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *source,GeoSourceValue *out)
{
    GeoParameterSources *state=opaque;GeoParameterRef ref;
    if(ctx!=state->sources||!geo_parameter_source_ref(state,source,&ref))return false;
    if(state->definition_token){
        if(!geo_parameter_source_working(state,ref))return false;
        int index=geo_parameters_field_index(state->working,ref.parameter_id,ref.field_id);
        /* Missing references retain the original evaluator's exact diagnostic. */
        if(index>=0&&!geo_parameter_source_definition(state,ref,index))return false;
    }
    out->kind=GEO_SOURCE_QUANTITY;
    if(!geo_parameter_evaluation_field(state->evaluation,ref,&out->as.quantity))return false;
    if(state->definition_token){int index=geo_parameters_field_index(state->store,ref.parameter_id,ref.field_id);
        if(index<0)return false;
        /* Publish only the successful quantity, preserving candidate bytes
         * outside its members exactly as the original evaluator does. */
        GeoQuantity *cached=&state->store->fields[index].value;
        memcpy(&cached->num,&out->as.quantity.num,sizeof cached->num);
        memcpy(&cached->den,&out->as.quantity.den,sizeof cached->den);
        memcpy(&cached->unit,&out->as.quantity.unit,sizeof cached->unit);}
    return true;
}
GeoParameterSources *geo_parameter_sources_register(GeoEvalContext *ctx,GeoParameterStore *store,
    GeoProviderToken token,const char *name_space,const char *fingerprint)
{
    if(!ctx||!store)return NULL;
    GeoParameterSources *state=calloc(1,sizeof *state);if(!state)return NULL;
    state->sources=ctx;state->store=store;state->token=token;
    state->evaluation=geo_parameter_evaluation_create(store,geo_parameter_source_resolve,state);
    GeoSourceProvider provider={token,name_space,fingerprint,state,geo_parameter_source_describe,geo_parameter_source_evaluate};
    if(!state->evaluation||!geo_eval_register(ctx,&provider)){geo_parameter_sources_destroy(state);return NULL;}
    return state;
}
GeoParameterSources *geo_parameter_sources_register_with_definitions(GeoEvalContext *ctx,GeoParameterStore *store,
    GeoProviderToken token,GeoProviderToken definition_token,const char *name_space,const char *fingerprint)
{
    if(!ctx||!store||!token||!definition_token||token==definition_token)return NULL;
    GeoParameterSources *state=calloc(1,sizeof *state);if(!state)return NULL;
    state->sources=ctx;state->store=store;state->token=token;state->definition_token=definition_token;
    GeoSourceProvider providers[]={
        {token,name_space,fingerprint,state,geo_parameter_source_describe,geo_parameter_source_evaluate},
        {definition_token,"core.parameter.definition","geometry-parameter-definitions/1",state,geo_parameter_definition_describe,geo_parameter_definition_evaluate}};
    if(!geo_eval_register_many(ctx,providers,2)){geo_parameter_sources_destroy(state);return NULL;}return state;
}
void geo_parameter_sources_destroy(GeoParameterSources *state)
{if(state){geo_parameter_evaluation_destroy(state->evaluation);geo_parameters_destroy(state->working);
    GeoParameterDefinitionResult *r=state->definitions;while(r){GeoParameterDefinitionResult *next=r->next;free(r);r=next;}free(state);}}
const GeoParameterStore *geo_parameter_sources_store(const GeoParameterSources *state)
{return state?state->store:NULL;}
const GeoEvalContext *geo_parameter_sources_context(const GeoParameterSources *state)
{return state?state->sources:NULL;}
static bool geo_parameter_source_bound(const GeoParameterSources *state)
{
    if(!state->definition_token)return true;
    bool value=false,definition=false;
    for(size_t i=0;i<geo_eval_provider_count(state->sources);++i){
        const GeoSourceProvider *provider=geo_eval_provider_at(state->sources,i);
        if(provider->candidate_state!=state)continue;
        if(provider->token==state->token&&provider->evaluate==geo_parameter_source_evaluate)value=true;
        if(provider->token==state->definition_token&&provider->evaluate==geo_parameter_definition_evaluate)definition=true;
    }
    return value&&definition;
}
bool geo_parameter_sources_value(GeoParameterSources *state,GeoParameterRef ref,GeoQuantity *out,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!state||!out){if(error)error->status=GEO_PARAMETER_INVALID_DEFINITION;return false;}
    if(!geo_parameter_source_bound(state)){
        if(error){error->status=GEO_PARAMETER_INVALID_DEFINITION;error->source=ref;}return false;}
    GeoParameterStatus status=geo_parameter_source_resolve(state,ref,out);
    if(status==GEO_PARAMETER_OK)return true;
    if(error){const GeoParameterError *issue=geo_parameter_evaluation_error(state->evaluation);
        if(issue)*error=*issue;
        if(error->status==GEO_PARAMETER_OK&&state->definition_error.status!=GEO_PARAMETER_OK)*error=state->definition_error;
        if(error->status==GEO_PARAMETER_OK){error->status=status;error->source=ref;}}
    return false;
}
bool geo_parameter_sources_rebuild(GeoParameterSources *state,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!state||!geo_parameter_source_bound(state)){if(error)error->status=GEO_PARAMETER_INVALID_DEFINITION;return false;}
    const GeoParameterField *fields=geo_parameters_fields(state->store);
    for(size_t i=0;i<geo_parameters_field_count(state->store);++i){GeoQuantity value;
        if(!geo_parameter_sources_value(state,(GeoParameterRef){true,fields[i].parameter_id,fields[i].id},&value,error))return false;}
    return true;
}
bool geo_parameter_sources_definitions(GeoParameterSources *state,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!state||!state->definition_token||!geo_parameter_source_bound(state)){if(error)error->status=GEO_PARAMETER_INVALID_DEFINITION;return false;}
    GeoSourceValue value;
    const GeoParameterCard *cards=geo_parameters_cards(state->store);
    for(size_t i=0;i<geo_parameters_card_count(state->store);++i)
        if(!geo_parameter_definition_get(state,GEO_PARAMETER_DEFINITION_CARD,cards[i].id,0,&value)){if(error)*error=state->definition_error;return false;}
    const GeoParameterField *fields=geo_parameters_fields(state->store);
    for(size_t i=0;i<geo_parameters_field_count(state->store);++i)
        if(!geo_parameter_definition_get(state,GEO_PARAMETER_DEFINITION_FIELD,fields[i].parameter_id,fields[i].id,&value)){if(error)*error=state->definition_error;return false;}
    return true;
}
