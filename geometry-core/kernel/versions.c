#include "internal/versions.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static bool geo_version_identity_valid(GeoVersionIdentity identity)
{return identity.key&&identity.key_length&&identity.key_length<=GEO_VERSION_KEY_BYTES&&identity.version;}

static const GeoVersionRecord *geo_version_record_find(const GeoVersionStore *store,GeoVersionIdentity identity)
{
    for(size_t i=0;i<store->count;++i){const GeoVersionRecord *record=&store->records[i];
        if(record->version==identity.version&&record->key_length==identity.key_length&&
           !memcmp(record->key,identity.key,identity.key_length))return record;
    }
    return NULL;
}

static bool geo_version_record_equal(const GeoVersionRecord *a,const GeoVersionRecord *b)
{
    if(a->key_length!=b->key_length||a->version!=b->version||
       memcmp(a->key,b->key,a->key_length)||a->content_length!=b->content_length||
       memcmp(a->content,b->content,a->content_length)||
       memcmp(a->fingerprint,b->fingerprint,GEO_VERSION_FINGERPRINT_BYTES)||a->field_count!=b->field_count||
       a->schema_length!=b->schema_length||memcmp(a->schema,b->schema,a->schema_length))return false;
    for(size_t i=0;i<a->field_count;++i){const GeoVersionField *x=&a->fields[i],*y=&b->fields[i];
        if(x->id!=y->id||x->kind!=y->kind||x->value.num!=y->value.num||x->value.den!=y->value.den||x->value.unit!=y->value.unit||
           x->literal_length!=y->literal_length||memcmp(x->literal,y->literal,x->literal_length))return false;
    }
    return true;
}

static GeoVersionView geo_version_view(const GeoVersionRecord *record)
{
    GeoVersionView view;
    view.identity=(GeoVersionIdentity){record->key,record->key_length,record->version};
    view.content=record->content;view.content_length=record->content_length;
    view.fingerprint=record->fingerprint;view.fingerprint_length=GEO_VERSION_FINGERPRINT_BYTES;
    view.fields=record->fields;view.field_count=record->field_count;
    view.schema=record->schema;view.schema_length=record->schema_length;
    return view;
}

GeoVersionStatus geo_versions_create(GeoVersionStore **out)
{
    if(!out)return GEO_VERSION_INVALID;
    GeoVersionStore *store=calloc(1,sizeof *store);
    if(!store)return GEO_VERSION_MEMORY;
    *out=store;return GEO_VERSION_OK;
}

GeoVersionStatus geo_versions_clone(const GeoVersionStore *source,GeoVersionStore **out)
{
    if(!source||!out)return GEO_VERSION_INVALID;
    GeoVersionStore *copy=malloc(sizeof *copy);
    if(!copy)return GEO_VERSION_MEMORY;
    memcpy(copy,source,sizeof *copy);
    *out=copy;return GEO_VERSION_OK;
}

void geo_versions_destroy(GeoVersionStore *store){free(store);}
size_t geo_versions_count(const GeoVersionStore *store){return store?store->count:0;}

bool geo_versions_equal(const GeoVersionStore *a,const GeoVersionStore *b)
{
    if(!a||!b||a->count!=b->count)return false;
    for(size_t i=0;i<a->count;++i){const GeoVersionRecord *record=&a->records[i];
        GeoVersionIdentity identity={record->key,record->key_length,record->version};
        const GeoVersionRecord *other=geo_version_record_find(b,identity);
        if(!other||!geo_version_record_equal(record,other))return false;
    }
    return true;
}

GeoVersionStatus geo_versions_at(const GeoVersionStore *store,size_t index,GeoVersionView *out)
{
    if(!store||!out)return GEO_VERSION_INVALID;
    if(index>=store->count)return GEO_VERSION_MISSING;
    *out=geo_version_view(&store->records[index]);return GEO_VERSION_OK;
}

GeoVersionStatus geo_versions_find(const GeoVersionStore *store,GeoVersionIdentity identity,GeoVersionView *out)
{
    if(!store||!out||!geo_version_identity_valid(identity))return GEO_VERSION_INVALID;
    const GeoVersionRecord *record=geo_version_record_find(store,identity);
    if(!record)return GEO_VERSION_MISSING;
    *out=geo_version_view(record);return GEO_VERSION_OK;
}

GeoVersionStatus geo_versions_field(const GeoVersionStore *store,GeoVersionIdentity identity,uint32_t field_id,GeoVersionFieldView *out)
{
    if(!store||!out||!geo_version_identity_valid(identity))return GEO_VERSION_INVALID;
    const GeoVersionRecord *record=geo_version_record_find(store,identity);
    if(!record)return GEO_VERSION_MISSING;
    for(size_t i=0;i<record->field_count;++i){
        if(record->fields[i].id==field_id){
            GeoVersionFieldView view={{record->key,record->key_length,record->version},record->fields[i]};
            *out=view;return GEO_VERSION_OK;
        }
    }
    return GEO_VERSION_MISSING;
}

static GeoVersionStatus geo_version_decimal(const GeoVersionField *field,size_t *first,size_t *point,GeoExactStatus *exact_detail)
{
    if(!field->literal_length||field->literal_length>GEO_VERSION_DECIMAL_BYTES)return GEO_VERSION_DECIMAL;
    GeoQuantity unit;GeoExactStatus exact=geo_quantity_normalize((GeoQuantity){0,1,field->value.unit},&unit);
    if(exact!=GEO_EXACT_OK){if(exact_detail)*exact_detail=exact;return GEO_VERSION_EXACT;}
    size_t start=(field->literal[0]=='-'||field->literal[0]=='+')?1:0,dot=field->literal_length;
    if(start==field->literal_length)return GEO_VERSION_DECIMAL;
    for(size_t i=start;i<field->literal_length;++i){char c=field->literal[i];
        if(c=='.'&&dot==field->literal_length&&i>start&&i+1<field->literal_length)dot=i;
        else if(c<'0'||c>'9')return GEO_VERSION_DECIMAL;
    }
    if(first)*first=start;if(point)*point=dot;return GEO_VERSION_OK;
}

static void geo_version_decimal_divide(char *digits,size_t *count,unsigned divisor)
{
    unsigned remainder=0;size_t used=0;
    for(size_t i=0;i<*count;++i){unsigned value=remainder*10+(unsigned)(digits[i]-'0');
        unsigned digit=value/divisor;remainder=value%divisor;
        if(digit||used)digits[used++]=(char)('0'+digit);
    }
    if(!used)digits[used++]='0';*count=used;
}

GeoVersionStatus geo_version_field_quantity(const GeoVersionField *field,GeoQuantity *out,GeoExactStatus *exact_detail)
{
    if(exact_detail)*exact_detail=GEO_EXACT_OK;
    if(!field||!out)return GEO_VERSION_INVALID;
    if(field->kind==GEO_VERSION_QUANTITY){
        GeoQuantity value;GeoExactStatus exact=geo_quantity_normalize(field->value,&value);
        if(exact!=GEO_EXACT_OK){if(exact_detail)*exact_detail=exact;return GEO_VERSION_EXACT;}
        *out=value;return GEO_VERSION_OK;
    }
    if(field->kind!=GEO_VERSION_DECIMAL_LITERAL)return GEO_VERSION_INVALID;
    size_t start,point;GeoVersionStatus status=geo_version_decimal(field,&start,&point,exact_detail);
    if(status!=GEO_VERSION_OK)return status;
    /* Reduce decimal factors before converting to int64. An unreduced 19+
     * digit numerator can still represent an exact in-range rational. */
    char digits[GEO_VERSION_DECIMAL_BYTES];size_t count=0;
    for(size_t i=start;i<field->literal_length;++i)if(i!=point&&(count||field->literal[i]!='0'))digits[count++]=field->literal[i];
    if(!count){*out=(GeoQuantity){0,1,field->value.unit};return GEO_VERSION_OK;}
    size_t twos=point<field->literal_length?field->literal_length-point-1:0,fives=twos;
    while(twos&&((digits[count-1]-'0')%2)==0){geo_version_decimal_divide(digits,&count,2);--twos;}
    while(fives&&((digits[count-1]-'0')%5)==0){geo_version_decimal_divide(digits,&count,5);--fives;}
    int64_t numerator=0,denominator=1;
    for(size_t i=0;i<count;++i){int digit=digits[i]-'0';
        if(numerator>(INT64_MAX-digit)/10){if(exact_detail)*exact_detail=GEO_EXACT_INTEGER_MAGNITUDE;return GEO_VERSION_EXACT;}
        numerator=numerator*10+digit;
    }
    for(size_t i=0;i<twos+fives;++i){int64_t factor=i<twos?2:5;
        if(denominator>INT64_MAX/factor){if(exact_detail)*exact_detail=GEO_EXACT_MULTIPLICATION_OVERFLOW;return GEO_VERSION_EXACT;}
        denominator*=factor;
    }
    if(field->literal[0]=='-')numerator=-numerator;
    GeoQuantity value;GeoExactStatus exact=geo_quantity_normalize((GeoQuantity){numerator,denominator,field->value.unit},&value);
    if(exact!=GEO_EXACT_OK){if(exact_detail)*exact_detail=exact;return GEO_VERSION_EXACT;}
    *out=value;return GEO_VERSION_OK;
}

GeoVersionStatus geo_version_field_integer(const GeoVersionField *field,GeoQuantityUnit unit,int64_t minimum,int64_t maximum,int64_t *out)
{
    if(!field||!out||minimum>maximum||(unit!=GEO_UNIT_SCALAR&&unit!=GEO_UNIT_LENGTH))return GEO_VERSION_INVALID;
    if(field->value.unit!=unit)return GEO_VERSION_UNIT;
    int64_t value=0;
    if(field->kind==GEO_VERSION_QUANTITY){
        GeoQuantity normalized;GeoVersionStatus status=geo_version_field_quantity(field,&normalized,NULL);
        if(status!=GEO_VERSION_OK)return status;
        if(normalized.den!=1)return GEO_VERSION_INTEGER;
        value=normalized.num;
    }else if(field->kind==GEO_VERSION_DECIMAL_LITERAL){
        size_t start,point;GeoVersionStatus status=geo_version_decimal(field,&start,&point,NULL);
        if(status!=GEO_VERSION_OK)return status;
        for(size_t i=point<field->literal_length?point+1:point;i<field->literal_length;++i)
            if(field->literal[i]!='0')return GEO_VERSION_INTEGER;
        for(size_t i=start;i<point;++i){int digit=field->literal[i]-'0';
            if(value>(INT64_MAX-digit)/10)return GEO_VERSION_RANGE;
            value=value*10+digit;
        }
        if(field->literal[0]=='-')value=-value;
    }else return GEO_VERSION_INVALID;
    if(value<minimum||value>maximum)return GEO_VERSION_RANGE;
    *out=value;return GEO_VERSION_OK;
}

GeoVersionStatus geo_versions_integer(const GeoVersionStore *store,GeoVersionIdentity identity,uint32_t field_id,GeoQuantityUnit unit,int64_t minimum,int64_t maximum,int64_t *out)
{
    GeoVersionFieldView field;GeoVersionStatus status=geo_versions_field(store,identity,field_id,&field);
    return status==GEO_VERSION_OK?geo_version_field_integer(&field.field,unit,minimum,maximum,out):status;
}

static GeoVersionStatus geo_version_prepare(const GeoVersionDefinition *definition,GeoVersionRecord *result,GeoExactStatus *exact_detail)
{
    if(exact_detail)*exact_detail=GEO_EXACT_OK;
    if(!definition||!definition->identity.key||!definition->identity.key_length||!definition->identity.version||
       (!definition->content&&definition->content_length)||(!definition->fields&&definition->field_count)||
       (!definition->schema&&definition->schema_length))return GEO_VERSION_INVALID;
    if(definition->identity.key_length>GEO_VERSION_KEY_BYTES||definition->content_length>GEO_VERSION_CONTENT_BYTES||
       definition->field_count>GEO_VERSION_FIELD_CAPACITY||definition->schema_length>GEO_VERSION_SCHEMA_BYTES)return GEO_VERSION_CAPACITY_EXCEEDED;
    if(!definition->fingerprint||definition->fingerprint_length!=GEO_VERSION_FINGERPRINT_BYTES)return GEO_VERSION_FINGERPRINT;
    for(size_t i=0;i<GEO_VERSION_FINGERPRINT_BYTES;++i){char c=definition->fingerprint[i];
        if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return GEO_VERSION_FINGERPRINT;
    }
    /* Snapshot every borrowed input before writing: even an insertion from an
     * existing view owns separate storage. Inactive bytes remain zero. */
    GeoVersionRecord next;memset(&next,0,sizeof next);
    memcpy(next.key,definition->identity.key,definition->identity.key_length);
    next.key_length=definition->identity.key_length;next.version=definition->identity.version;
    if(definition->content_length)memcpy(next.content,definition->content,definition->content_length);
    next.content_length=definition->content_length;
    geo_sha256(next.content,next.content_length,next.fingerprint);
    if(memcmp(next.fingerprint,definition->fingerprint,GEO_VERSION_FINGERPRINT_BYTES))return GEO_VERSION_FINGERPRINT;
    for(size_t i=0;i<definition->field_count;++i){
        const GeoVersionField *field=&definition->fields[i];GeoQuantity normalized={0,1,field->value.unit};
        if(field->kind==GEO_VERSION_QUANTITY){GeoExactStatus exact=geo_quantity_normalize(field->value,&normalized);
            if(exact!=GEO_EXACT_OK){if(exact_detail)*exact_detail=exact;return GEO_VERSION_EXACT;}
        }else if(field->kind==GEO_VERSION_DECIMAL_LITERAL){
            GeoVersionStatus status=geo_version_decimal(field,NULL,NULL,exact_detail);if(status!=GEO_VERSION_OK)return status;
        }else return GEO_VERSION_INVALID;
        size_t at=0;while(at<i&&next.fields[at].id<definition->fields[i].id)++at;
        if(at<i&&next.fields[at].id==definition->fields[i].id)return GEO_VERSION_DUPLICATE_FIELD;
        memmove(next.fields+at+1,next.fields+at,(i-at)*sizeof *next.fields);
        memset(&next.fields[at],0,sizeof next.fields[at]);
        next.fields[at].id=definition->fields[i].id;
        next.fields[at].value.num=normalized.num;next.fields[at].value.den=normalized.den;next.fields[at].value.unit=normalized.unit;
        next.fields[at].kind=field->kind;
        if(field->kind==GEO_VERSION_DECIMAL_LITERAL){
            memcpy(next.fields[at].literal,field->literal,field->literal_length);next.fields[at].literal_length=field->literal_length;
        }
    }
    next.field_count=definition->field_count;
    if(definition->schema_length)memcpy(next.schema,definition->schema,definition->schema_length);next.schema_length=definition->schema_length;
    memcpy(result,&next,sizeof next);return GEO_VERSION_OK;
}

static GeoVersionStatus geo_version_admission(const GeoVersionStore *store,const GeoVersionRecord *next)
{
    GeoVersionIdentity identity={next->key,next->key_length,next->version};
    const GeoVersionRecord *existing=geo_version_record_find(store,identity);
    if(existing)return geo_version_record_equal(existing,next)?GEO_VERSION_OK:GEO_VERSION_IMMUTABLE;
    if(store->count>=GEO_VERSION_CAPACITY)return GEO_VERSION_CAPACITY_EXCEEDED;
    return GEO_VERSION_OK;
}

GeoVersionStatus geo_versions_check(const GeoVersionStore *store,const GeoVersionDefinition *definition,GeoExactStatus *exact_detail)
{
    if(exact_detail)*exact_detail=GEO_EXACT_OK;if(!store)return GEO_VERSION_INVALID;
    GeoVersionRecord next;GeoVersionStatus status=geo_version_prepare(definition,&next,exact_detail);
    return status==GEO_VERSION_OK?geo_version_admission(store,&next):status;
}

GeoVersionStatus geo_versions_put(GeoVersionStore *store,const GeoVersionDefinition *definition,GeoExactStatus *exact_detail)
{
    if(exact_detail)*exact_detail=GEO_EXACT_OK;if(!store)return GEO_VERSION_INVALID;
    GeoVersionRecord next;GeoVersionStatus status=geo_version_prepare(definition,&next,exact_detail);
    if(status!=GEO_VERSION_OK)return status;
    status=geo_version_admission(store,&next);if(status!=GEO_VERSION_OK)return status;
    GeoVersionIdentity identity={next.key,next.key_length,next.version};
    if(geo_version_record_find(store,identity))return GEO_VERSION_OK;
    memcpy(&store->records[store->count],&next,sizeof next);++store->count;return GEO_VERSION_OK;
}
