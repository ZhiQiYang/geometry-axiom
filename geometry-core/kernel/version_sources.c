#include "version_sources.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static void geo_vs_u32(unsigned char **p,uint32_t n)
{for(unsigned i=0;i<4;++i)*(*p)++=(unsigned char)(n>>(24-8*i));}
static uint32_t geo_vs_read32(const unsigned char **p)
{uint32_t n=0;for(unsigned i=0;i<4;++i)n=(n<<8)|*(*p)++;return n;}
static void geo_vs_i64(unsigned char **p,int64_t value)
{uint64_t n=(uint64_t)value;for(unsigned i=0;i<8;++i)*(*p)++=(unsigned char)(n>>(56-8*i));}
static int64_t geo_vs_read64(const unsigned char **p)
{uint64_t n=0;for(unsigned i=0;i<8;++i)n=(n<<8)|*(*p)++;return n<=INT64_MAX?(int64_t)n:-(int64_t)(~n)-1;}
static bool geo_vs_identity(GeoVersionIdentity a,GeoVersionIdentity b)
{return a.version==b.version&&a.key_length==b.key_length&&!memcmp(a.key,b.key,a.key_length);}
static bool geo_vs_field_canonical(const GeoVersionField *f)
{
    if((f->value.unit!=GEO_UNIT_SCALAR&&f->value.unit!=GEO_UNIT_LENGTH)||f->literal_length>GEO_VERSION_DECIMAL_BYTES)return false;
    if(f->kind==GEO_VERSION_QUANTITY){GeoQuantity q;
        return !f->literal_length&&geo_quantity_normalize(f->value,&q)==GEO_EXACT_OK&&q.num==f->value.num&&q.den==f->value.den;}
    if(f->kind!=GEO_VERSION_DECIMAL_LITERAL||!f->literal_length)return false;
    size_t n=f->literal_length,first=(f->literal[0]=='+'||f->literal[0]=='-')?1:0,point=n;if(first==n)return false;
    for(size_t i=first;i<n;++i){char c=f->literal[i];if(c=='.'&&point==n&&i>first&&i+1<n)point=i;else if(c<'0'||c>'9')return false;}
    return true;
}
GeoSourceRef geo_version_source_ref(GeoProviderToken token,GeoVersionSourceKind kind,GeoVersionIdentity identity,uint32_t field,GeoVersionSourceKey *out)
{
    if(!out||!identity.key||!identity.key_length||identity.key_length>GEO_VERSION_KEY_BYTES||!identity.version||
       (kind!=GEO_VERSION_SOURCE_DEFINITION&&kind!=GEO_VERSION_SOURCE_FIELD)||(kind==GEO_VERSION_SOURCE_DEFINITION&&field))return (GeoSourceRef){token,NULL,0};
    GeoVersionSourceKey key;memset(&key,0,sizeof key);unsigned char *p=key.bytes;*p++=(unsigned char)kind;
    geo_vs_u32(&p,(uint32_t)identity.key_length);geo_vs_u32(&p,identity.version);geo_vs_u32(&p,field);
    memcpy(p,identity.key,identity.key_length);key.size=13+identity.key_length;*out=key;
    return (GeoSourceRef){token,out->bytes,out->size};
}
bool geo_version_source_decode(const GeoSourceRef *source,GeoVersionSourceKind *kind,GeoVersionIdentity *identity,uint32_t *field)
{
    if(!source||!source->key||source->key_size<14||source->key_size>GEO_VERSION_SOURCE_KEY_MAX||!kind||!identity||!field)return false;
    const unsigned char *p=source->key;unsigned k=*p++;uint32_t n=geo_vs_read32(&p),version=geo_vs_read32(&p),f=geo_vs_read32(&p);
    if((k!=GEO_VERSION_SOURCE_DEFINITION&&k!=GEO_VERSION_SOURCE_FIELD)||!n||n>GEO_VERSION_KEY_BYTES||source->key_size!=13+n||!version||(k==GEO_VERSION_SOURCE_DEFINITION&&f))return false;
    *kind=(GeoVersionSourceKind)k;*identity=(GeoVersionIdentity){p,n,version};*field=f;return true;
}
size_t geo_version_definition_encode(const GeoVersionView *v,void *out,size_t capacity)
{
    if(!v||!out||!v->identity.key||!v->identity.key_length||v->identity.key_length>GEO_VERSION_KEY_BYTES||!v->identity.version||
       (!v->content&&v->content_length)||v->content_length>GEO_VERSION_CONTENT_BYTES||!v->fingerprint||v->fingerprint_length!=GEO_VERSION_FINGERPRINT_BYTES||
       (!v->schema&&v->schema_length)||v->schema_length>GEO_VERSION_SCHEMA_BYTES||(!v->fields&&v->field_count)||v->field_count>GEO_VERSION_FIELD_CAPACITY)return 0;
    char fingerprint[65];geo_sha256(v->content,v->content_length,fingerprint);if(memcmp(v->fingerprint,fingerprint,64))return 0;
    unsigned char bytes[GEO_VERSION_DEFINITION_MAX],*p=bytes;memcpy(p,"GVS1",4);p+=4;
    geo_vs_u32(&p,(uint32_t)v->identity.key_length);memcpy(p,v->identity.key,v->identity.key_length);p+=v->identity.key_length;
    geo_vs_u32(&p,v->identity.version);geo_vs_u32(&p,(uint32_t)v->content_length);
    if(v->content_length)memcpy(p,v->content,v->content_length);p+=v->content_length;
    memcpy(p,v->fingerprint,GEO_VERSION_FINGERPRINT_BYTES);p+=GEO_VERSION_FINGERPRINT_BYTES;
    geo_vs_u32(&p,(uint32_t)v->schema_length);if(v->schema_length)memcpy(p,v->schema,v->schema_length);p+=v->schema_length;
    geo_vs_u32(&p,(uint32_t)v->field_count);
    for(size_t i=0;i<v->field_count;++i){const GeoVersionField *f=&v->fields[i];
        if((i&&v->fields[i-1].id>=f->id)||!geo_vs_field_canonical(f))return 0;
        geo_vs_u32(&p,f->id);*p++=(unsigned char)f->kind;*p++=(unsigned char)f->value.unit;
        geo_vs_i64(&p,f->kind==GEO_VERSION_QUANTITY?f->value.num:0);geo_vs_i64(&p,f->kind==GEO_VERSION_QUANTITY?f->value.den:1);
        geo_vs_u32(&p,(uint32_t)f->literal_length);memcpy(p,f->literal,f->literal_length);p+=f->literal_length;
    }
    size_t n=(size_t)(p-bytes);if(n>capacity)return 0;memcpy(out,bytes,n);return n;
}
bool geo_version_definition_decode(const void *data,size_t size,GeoVersionView *out,GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY])
{
    if(!data||!out||!fields||size<24+1+GEO_VERSION_FINGERPRINT_BYTES||size>GEO_VERSION_DEFINITION_MAX)return false;
    const unsigned char *p=data,*end=p+size;GeoVersionView v;memset(&v,0,sizeof v);
    GeoVersionField decoded[GEO_VERSION_FIELD_CAPACITY];memset(decoded,0,sizeof decoded);
    if(memcmp(p,"GVS1",4))return false;p+=4;uint32_t n=geo_vs_read32(&p);
    if(!n||n>GEO_VERSION_KEY_BYTES||(size_t)(end-p)<n+8)return false;
    v.identity.key=p;v.identity.key_length=n;p+=n;v.identity.version=geo_vs_read32(&p);if(!v.identity.version)return false;
    n=geo_vs_read32(&p);if(n>GEO_VERSION_CONTENT_BYTES||(size_t)(end-p)<n+GEO_VERSION_FINGERPRINT_BYTES+4)return false;
    v.content=p;v.content_length=n;p+=n;v.fingerprint=(const char *)p;v.fingerprint_length=GEO_VERSION_FINGERPRINT_BYTES;p+=GEO_VERSION_FINGERPRINT_BYTES;
    char fingerprint[65];geo_sha256(v.content,v.content_length,fingerprint);if(memcmp(v.fingerprint,fingerprint,64))return false;
    n=geo_vs_read32(&p);if(n>GEO_VERSION_SCHEMA_BYTES||(size_t)(end-p)<n+4)return false;
    v.schema=(const char *)p;v.schema_length=n;p+=n;n=geo_vs_read32(&p);if(n>GEO_VERSION_FIELD_CAPACITY)return false;v.field_count=n;
    for(size_t i=0;i<v.field_count;++i){GeoVersionField *f=&decoded[i];if((size_t)(end-p)<26)return false;
        f->id=geo_vs_read32(&p);f->kind=(GeoVersionFieldKind)*p++;f->value.unit=(GeoQuantityUnit)*p++;
        f->value.num=geo_vs_read64(&p);f->value.den=geo_vs_read64(&p);n=geo_vs_read32(&p);
        if((i&&decoded[i-1].id>=f->id)||n>GEO_VERSION_DECIMAL_BYTES||(size_t)(end-p)<n||
           (f->kind!=GEO_VERSION_QUANTITY&&f->kind!=GEO_VERSION_DECIMAL_LITERAL)||
           (f->value.unit!=GEO_UNIT_SCALAR&&f->value.unit!=GEO_UNIT_LENGTH))return false;
        f->literal_length=n;memcpy(f->literal,p,n);p+=n;
        if(!geo_vs_field_canonical(f)||(f->kind==GEO_VERSION_DECIMAL_LITERAL&&(f->value.num||f->value.den!=1)))return false;
    }
    if(p!=end)return false;memcpy(fields,decoded,sizeof decoded);v.fields=fields;*out=v;return true;
}
typedef struct GeoVersionSourceResult {GeoVersionSourceKey key;unsigned char bytes[GEO_VERSION_DEFINITION_MAX];size_t size;struct GeoVersionSourceResult *next;} GeoVersionSourceResult;
struct GeoVersionSources {GeoEvalContext *context;const GeoVersionStore *store;GeoProviderToken token;GeoVersionSourceResult *results;};
static bool geo_vs_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    GeoVersionSources *s=opaque;GeoVersionSourceKind kind;GeoVersionIdentity identity;uint32_t field;GeoVersionView version;
    if(ref->provider!=s->token||!geo_version_source_decode(ref,&kind,&identity,&field)||geo_versions_find(s->store,identity,&version)!=GEO_VERSION_OK)return false;
    GeoSourceDescriptor value;memset(&value,0,sizeof value);value.context.axis=-1;value.unit=GEO_UNIT_SCALAR;
    if(kind==GEO_VERSION_SOURCE_DEFINITION)value.kind=GEO_SOURCE_DEFINITION;
    else {size_t i=0;while(i<version.field_count&&version.fields[i].id!=field)++i;if(i==version.field_count)return false;
        value.kind=GEO_SOURCE_QUANTITY;value.unit=version.fields[i].value.unit;}
    *out=value;return true;
}
static bool geo_vs_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    GeoVersionSources *s=opaque;GeoVersionSourceKind kind;GeoVersionIdentity identity;uint32_t field;
    if(ctx!=s->context||ref->provider!=s->token||!geo_version_source_decode(ref,&kind,&identity,&field))return false;
    if(kind==GEO_VERSION_SOURCE_DEFINITION){
        GeoVersionSourceResult *r=s->results;while(r&&(r->key.size!=ref->key_size||memcmp(r->key.bytes,ref->key,ref->key_size)))r=r->next;
        if(!r){GeoVersionView version;if(geo_versions_find(s->store,identity,&version)!=GEO_VERSION_OK)return false;
            r=calloc(1,sizeof *r);if(!r)return false;r->size=geo_version_definition_encode(&version,r->bytes,sizeof r->bytes);
            if(!r->size){free(r);return false;}r->key.size=ref->key_size;memcpy(r->key.bytes,ref->key,ref->key_size);r->next=s->results;s->results=r;}
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"geometry.version/1",r->bytes,r->size};return true;
    }
    GeoVersionSourceKey key;GeoSourceRef upstream=geo_version_source_ref(s->token,GEO_VERSION_SOURCE_DEFINITION,identity,0,&key);GeoSourceValue definition;
    if(geo_eval_source(ctx,upstream,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK||definition.kind!=GEO_SOURCE_DEFINITION||
       !definition.as.definition.schema||strcmp(definition.as.definition.schema,"geometry.version/1"))return false;
    GeoVersionView version;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];
    if(!geo_version_definition_decode(definition.as.definition.content,definition.as.definition.content_size,&version,fields)||!geo_vs_identity(identity,version.identity))return false;
    size_t i=0;while(i<version.field_count&&fields[i].id!=field)++i;if(i==version.field_count)return false;
    GeoQuantity quantity;if(geo_version_field_quantity(&fields[i],&quantity,NULL)!=GEO_VERSION_OK)return false;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=quantity;return true;
}
GeoVersionSources *geo_version_sources_register(GeoEvalContext *ctx,const GeoVersionStore *store,GeoProviderToken token)
{
    if(!ctx||!store||!token)return NULL;GeoVersionSources *s=calloc(1,sizeof *s);if(!s)return NULL;s->context=ctx;s->store=store;s->token=token;
    GeoSourceProvider provider={token,"core.version","geometry.version-source/1",s,geo_vs_describe,geo_vs_evaluate};
    if(!geo_eval_register(ctx,&provider)){free(s);return NULL;}return s;
}
void geo_version_sources_destroy(GeoVersionSources *s)
{if(s){GeoVersionSourceResult *r=s->results;while(r){GeoVersionSourceResult *next=r->next;free(r);r=next;}free(s);}}
bool geo_version_sources_definitions(GeoVersionSources *s)
{
    if(!s)return false;for(size_t i=0;i<geo_versions_count(s->store);++i){GeoVersionView version;GeoVersionSourceKey key;GeoSourceValue value;
        if(geo_versions_at(s->store,i,&version)!=GEO_VERSION_OK||geo_eval_source(s->context,geo_version_source_ref(s->token,GEO_VERSION_SOURCE_DEFINITION,version.identity,0,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)!=GEO_SOURCE_OK)return false;}
    return true;
}
const GeoVersionStore *geo_version_sources_store(const GeoVersionSources *s){return s?s->store:NULL;}
const GeoEvalContext *geo_version_sources_context(const GeoVersionSources *s){return s?s->context:NULL;}
