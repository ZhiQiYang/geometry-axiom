#include "linear_definition_sources.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static void geo_ld_put32(unsigned char **p,uint32_t value)
{for(unsigned i=0;i<4;++i)*(*p)++=(unsigned char)(value>>(24-8*i));}
static void geo_ld_put64(unsigned char **p,int64_t value)
{uint64_t n=(uint64_t)value;for(unsigned i=0;i<8;++i)*(*p)++=(unsigned char)(n>>(56-8*i));}
typedef struct {const unsigned char *p,*end;} GeoLDReader;
static bool geo_ld_read(GeoLDReader *r,unsigned bytes,uint64_t *out)
{if((size_t)(r->end-r->p)<bytes)return false;uint64_t value=0;for(unsigned i=0;i<bytes;++i)value=(value<<8)|*r->p++;*out=value;return true;}
static int64_t geo_ld_signed64(uint64_t n)
{return n<=INT64_MAX?(int64_t)n:-(int64_t)(~n)-1;}
static int geo_ld_signed32(uint32_t n)
{return n<=INT32_MAX?(int)n:-(int)(~n)-1;}
static bool geo_ld_expression_write(unsigned char **p,const GeoLinearExpression *expression)
{
    if(expression->count>GEO_LINEAR_MAX_TERMS||expression->key_bytes>GEO_LINEAR_KEY_BYTES)return false;
    geo_ld_put32(p,(uint32_t)expression->mode);*(*p)++=expression->complete?1:0;geo_ld_put32(p,(uint32_t)expression->count);
    size_t key_bytes=0;
    for(size_t i=0;i<expression->count;++i){const GeoLinearTerm *term=&expression->terms[i];
        if(term->numerator==INT64_MIN||term->denominator<=0||!term->provider||term->key_offset>=expression->key_bytes)return false;
        const char *key=expression->keys+term->key_offset,*end=memchr(key,0,expression->key_bytes-term->key_offset);
        if(!end)return false;size_t length=(size_t)(end-key);if(length+1>GEO_LINEAR_KEY_BYTES-key_bytes)return false;key_bytes+=length+1;
        geo_ld_put64(p,term->numerator);geo_ld_put64(p,term->denominator);geo_ld_put32(p,term->provider);geo_ld_put32(p,term->id);geo_ld_put32(p,term->field);geo_ld_put32(p,(uint32_t)length);
        memcpy(*p,key,length);*p+=length;
    }return true;
}
static bool geo_ld_expression_read(GeoLDReader *r,GeoLinearExpression *out)
{
    uint64_t mode,complete,count;
    if(!geo_ld_read(r,4,&mode)||!geo_ld_read(r,1,&complete)||complete>1||!geo_ld_read(r,4,&count)||count>GEO_LINEAR_MAX_TERMS)return false;
    geo_linear_begin(out,(GeoLinearMode)geo_ld_signed32((uint32_t)mode));
    for(size_t i=0;i<(size_t)count;++i){uint64_t numerator,denominator,provider,id,field,length;
        if(!geo_ld_read(r,8,&numerator)||!geo_ld_read(r,8,&denominator)||!geo_ld_read(r,4,&provider)||!geo_ld_read(r,4,&id)||!geo_ld_read(r,4,&field)||!geo_ld_read(r,4,&length)||
           length>=GEO_LINEAR_KEY_BYTES||length>(size_t)(r->end-r->p)||memchr(r->p,0,(size_t)length))return false;
        char key[GEO_LINEAR_KEY_BYTES];memcpy(key,r->p,(size_t)length);key[length]=0;r->p+=length;
        if(!geo_linear_append(out,geo_ld_signed64(numerator),geo_ld_signed64(denominator),(GeoLinearSource){(uint32_t)provider,(uint32_t)id,(uint32_t)field,key}))return false;
    }
    geo_linear_finish(out,complete!=0);return true;
}
GeoSourceRef geo_linear_definition_source_ref(GeoProviderToken token,GeoLinearDefinitionKind kind,uint32_t id,GeoLinearDefinitionKey *key)
{if(!key||(kind!=GEO_LINEAR_DEFINITION_DATUM&&kind!=GEO_LINEAR_DEFINITION_GUIDE))return (GeoSourceRef){token,NULL,0};key->bytes[0]=(unsigned char)kind;unsigned char *p=key->bytes+1;geo_ld_put32(&p,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
bool geo_linear_definition_source_decode(const GeoSourceRef *ref,GeoLinearDefinitionKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;
    const unsigned char *p=ref->key;if(*p!=GEO_LINEAR_DEFINITION_DATUM&&*p!=GEO_LINEAR_DEFINITION_GUIDE)return false;
    GeoLDReader r={p+1,p+5};uint64_t n;if(!geo_ld_read(&r,4,&n))return false;*kind=(GeoLinearDefinitionKind)*p;*id=(uint32_t)n;return true;
}
size_t geo_datum_definition_encode(const GeoDatum *datum,unsigned char out[GEO_LINEAR_DEFINITION_CONTENT_MAX])
{
    if(!datum||!out||datum->axis<0||datum->axis>2)return 0;
    unsigned char content[GEO_LINEAR_DEFINITION_CONTENT_MAX],*p=content;geo_ld_put32(&p,datum->id);*p++=(unsigned char)datum->axis;
    if(!geo_ld_expression_write(&p,&datum->expression))return 0;
    size_t size=(size_t)(p-content);memcpy(out,content,size);return size;
}
bool geo_datum_definition_decode(const void *content,size_t size,GeoDatum *out)
{
    if(!content||!out||size>GEO_LINEAR_DEFINITION_CONTENT_MAX)return false;
    GeoLDReader r={content,(const unsigned char *)content+size};uint64_t id,axis;GeoDatum value;memset(&value,0,sizeof value);
    if(!geo_ld_read(&r,4,&id)||!geo_ld_read(&r,1,&axis)||axis>2||!geo_ld_expression_read(&r,&value.expression)||r.p!=r.end)return false;
    value.id=(uint32_t)id;value.axis=(int)axis;memcpy(out,&value,sizeof value);return true;
}
size_t geo_guide_definition_encode(const GeoGuide *guide,unsigned char out[GEO_LINEAR_DEFINITION_CONTENT_MAX])
{
    if(!guide||!out||(guide->source!=GEO_GUIDE_LOCAL&&guide->source!=GEO_GUIDE_DATUM))return 0;
    unsigned char content[GEO_LINEAR_DEFINITION_CONTENT_MAX],*p=content;geo_ld_put32(&p,guide->id);geo_ld_put32(&p,guide->placement_id);*p++=(unsigned char)guide->source;
    if(guide->source==GEO_GUIDE_DATUM)geo_ld_put32(&p,guide->datum_id);
    else{if(guide->direction!=GEO_GUIDE_ALONG_U&&guide->direction!=GEO_GUIDE_ALONG_V)return 0;*p++=(unsigned char)guide->direction;if(!geo_ld_expression_write(&p,&guide->expression))return 0;}
    size_t size=(size_t)(p-content);memcpy(out,content,size);return size;
}
bool geo_guide_definition_decode(const void *content,size_t size,GeoGuide *out)
{
    if(!content||!out||size>GEO_LINEAR_DEFINITION_CONTENT_MAX)return false;
    GeoLDReader r={content,(const unsigned char *)content+size};uint64_t id,placement,source,n;GeoGuide value;memset(&value,0,sizeof value);
    if(!geo_ld_read(&r,4,&id)||!geo_ld_read(&r,4,&placement)||!geo_ld_read(&r,1,&source)||source>GEO_GUIDE_DATUM)return false;
    value.id=(uint32_t)id;value.placement_id=(uint32_t)placement;value.source=(GeoGuideSource)source;
    if(source==GEO_GUIDE_DATUM){if(!geo_ld_read(&r,4,&n))return false;value.datum_id=(uint32_t)n;}
    else{if(!geo_ld_read(&r,1,&n)||n>GEO_GUIDE_ALONG_V||!geo_ld_expression_read(&r,&value.expression))return false;value.direction=(GeoGuideDirection)n;}
    if(r.p!=r.end)return false;memcpy(out,&value,sizeof value);return true;
}
typedef struct GeoLDValue GeoLDValue;
struct GeoLDValue {GeoLinearDefinitionKind kind;uint32_t id;unsigned char content[GEO_LINEAR_DEFINITION_CONTENT_MAX];size_t size;GeoLDValue *next;};
struct GeoLinearDefinitionSources {GeoEvalContext *graph;const GeoDatumStore *datums;const GeoGuideStore *guides;GeoProviderToken token;GeoLDValue *values;};
static bool geo_ld_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    GeoLinearDefinitionSources *s=opaque;GeoLinearDefinitionKind kind;uint32_t id;
    if(ref->provider!=s->token||!geo_linear_definition_source_decode(ref,&kind,&id))return false;
    if(kind==GEO_LINEAR_DEFINITION_DATUM?!geo_datums_find(s->datums,id):!geo_guides_find(s->guides,id))return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_DEFINITION;out->unit=GEO_UNIT_SCALAR;out->context.axis=-1;return true;
}
static bool geo_ld_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    GeoLinearDefinitionSources *s=opaque;GeoLinearDefinitionKind kind;uint32_t id;
    if(graph!=s->graph||ref->provider!=s->token||!geo_linear_definition_source_decode(ref,&kind,&id))return false;
    GeoLDValue *value=s->values;while(value&&(value->kind!=kind||value->id!=id))value=value->next;
    if(!value){value=calloc(1,sizeof *value);if(!value)return false;value->kind=kind;value->id=id;value->next=s->values;s->values=value;}
    const char *schema;
    if(kind==GEO_LINEAR_DEFINITION_DATUM){value->size=geo_datum_definition_encode(geo_datums_find(s->datums,id),value->content);schema="geometry.datum-definition/1";}
    else{const GeoGuide *guide=geo_guides_find(s->guides,id);value->size=geo_guide_definition_encode(guide,value->content);schema="geometry.guide-definition/1";
        if(value->size&&guide->source==GEO_GUIDE_DATUM){GeoLinearDefinitionKey key;
            if(geo_eval_depend(graph,geo_linear_definition_source_ref(s->token,GEO_LINEAR_DEFINITION_DATUM,guide->datum_id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;}}
    if(!value->size)return false;out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,value->content,value->size};return true;
}
GeoLinearDefinitionSources *geo_linear_definition_sources_register(GeoEvalContext *graph,const GeoDatumStore *datums,const GeoGuideStore *guides,GeoProviderToken token)
{
    if(!graph||!datums||!guides)return NULL;GeoLinearDefinitionSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->datums=datums;s->guides=guides;s->token=token;
    GeoSourceProvider provider={token,"core.linear-definition","geometry.linear-definition/1",s,geo_ld_describe,geo_ld_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
void geo_linear_definition_sources_destroy(GeoLinearDefinitionSources *s)
{if(s){GeoLDValue *value=s->values;while(value){GeoLDValue *next=value->next;free(value);value=next;}free(s);}}
static bool geo_ld_get(GeoLinearDefinitionSources *s,GeoLinearDefinitionKind kind,uint32_t id,GeoSourceValue *out)
{if(!s)return false;GeoLinearDefinitionKey key;return geo_eval_source(s->graph,geo_linear_definition_source_ref(s->token,kind,id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,out)==GEO_SOURCE_OK;}
bool geo_linear_definition_sources_datum(GeoLinearDefinitionSources *s,uint32_t id,GeoDatum *out)
{GeoSourceValue value;GeoDatum result;if(!out||!geo_ld_get(s,GEO_LINEAR_DEFINITION_DATUM,id,&value)||value.kind!=GEO_SOURCE_DEFINITION||!value.as.definition.schema||strcmp(value.as.definition.schema,"geometry.datum-definition/1")||!geo_datum_definition_decode(value.as.definition.content,value.as.definition.content_size,&result)||result.id!=id)return false;memcpy(out,&result,sizeof result);return true;}
bool geo_linear_definition_sources_guide(GeoLinearDefinitionSources *s,uint32_t id,GeoGuide *out)
{GeoSourceValue value;GeoGuide result;if(!out||!geo_ld_get(s,GEO_LINEAR_DEFINITION_GUIDE,id,&value)||value.kind!=GEO_SOURCE_DEFINITION||!value.as.definition.schema||strcmp(value.as.definition.schema,"geometry.guide-definition/1")||!geo_guide_definition_decode(value.as.definition.content,value.as.definition.content_size,&result)||result.id!=id)return false;memcpy(out,&result,sizeof result);return true;}
bool geo_linear_definition_sources_complete(GeoLinearDefinitionSources *s)
{
    if(!s)return false;GeoSourceValue value;
    for(size_t i=0;i<geo_datums_count(s->datums);++i)if(!geo_ld_get(s,GEO_LINEAR_DEFINITION_DATUM,geo_datums_at(s->datums,i)->id,&value))return false;
    for(size_t i=0;i<geo_guides_count(s->guides);++i)if(!geo_ld_get(s,GEO_LINEAR_DEFINITION_GUIDE,geo_guides_at(s->guides,i)->id,&value))return false;
    return true;
}
