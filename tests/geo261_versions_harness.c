#include "versions.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define CHECK(label,test) do {if(!(test)){fprintf(stderr,"ASSERT:%s line %d\n",label,__LINE__);return 1;}}while(0)
static const char abc_hash[]="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
static const char abd_hash[]="a52d159f262b2c6ddb724a61840befc36eb30c88877a4030b65cbe86298449c9";
static const char binary_hash[]="76fe3925c7167317f2df68454339f5ec3650e4062178b4f2be219b105a507907";
static const char empty_hash[]="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
static const char full_hash[]="49abd65bbf7f7e40c7055093ed2e3fd75f2f602f2c5fcf955c213e3135eb03f7";

static GeoVersionDefinition definition(const void *key,size_t length,uint32_t version)
{
    GeoVersionDefinition d={{key,length,version},"abc",3,abc_hash,64,NULL,0};return d;
}
static int identity(void)
{
    GeoVersionStore *store=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    unsigned char key[]={0x61,0,0x62},other[]={0x61,0,0x63},kind[]={0x62,0,0x62};
    GeoVersionDefinition d=definition(key,sizeof key,1);
    CHECK("binary-key",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    d.identity.key=other;CHECK("nul-suffix-distinct",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    d.identity.key=key;d.identity.key_length=1;CHECK("prefix-distinct",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    d.identity.key=kind;d.identity.key_length=3;CHECK("namespace-distinct",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    d.identity.key=key;d.identity.version=UINT32_MAX;CHECK("uint32-version",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    CHECK("five-distinct-identities",geo_versions_count(store)==5);
    GeoVersionView view;CHECK("lookup-version",geo_versions_find(store,d.identity,&view)==GEO_VERSION_OK&&view.identity.version==UINT32_MAX);
    CHECK("exact-key-length",view.identity.key_length==3&&!memcmp(view.identity.key,key,3));
    d.identity.version=2;CHECK("no-latest-fallback",geo_versions_find(store,d.identity,&view)==GEO_VERSION_MISSING);
    CHECK("first-insertion-order",geo_versions_at(store,0,&view)==GEO_VERSION_OK&&view.identity.version==1);
    geo_versions_destroy(store);return 0;
}

static int fingerprint(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionDefinition d=definition("k",1,1);char hash[65];memcpy(hash,abc_hash,65);
    hash[0]='0';d.fingerprint=hash;
    CHECK("fingerprint-verified",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_count(store)==0);
    memcpy(hash,abc_hash,64);hash[64]='!';
    CHECK("fingerprint-length-not-terminator",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    d.identity.version=2;d.content="abd";
    CHECK("hash-covers-content",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    d.content="abc";d.fingerprint_length=63;
    CHECK("short-hash",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    d.fingerprint_length=65;CHECK("long-hash",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    d.fingerprint_length=64;hash[0]='B';CHECK("uppercase-hash",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    hash[0]='g';CHECK("nonhex-hash",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    d.fingerprint=NULL;CHECK("missing-hash",geo_versions_put(store,&d,NULL)==GEO_VERSION_FINGERPRINT&&geo_versions_equal(store,before));
    const unsigned char binary[]={'A',0,'B'};d.content=binary;d.content_length=3;d.fingerprint=binary_hash;
    CHECK("hash-includes-zero-byte",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    GeoVersionView view;CHECK("binary-content-owned",geo_versions_find(store,d.identity,&view)==GEO_VERSION_OK&&!memcmp(view.content,binary,3));
    d.identity.version=3;d.content=NULL;d.content_length=0;d.fingerprint=empty_hash;
    CHECK("empty-content",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    CHECK("empty-content-length",geo_versions_find(store,d.identity,&view)==GEO_VERSION_OK&&view.content_length==0);
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static int fields(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionField values[]={{UINT32_MAX,{-6,4,GEO_UNIT_SCALAR}},{0,{2,4,GEO_UNIT_LENGTH}},{7,{0,17,GEO_UNIT_SCALAR}}};
    GeoVersionDefinition d=definition("field",5,1);d.fields=values;d.field_count=3;
    CHECK("typed-put",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    GeoVersionView view;CHECK("sorted-fields",geo_versions_at(store,0,&view)==GEO_VERSION_OK&&view.fields[0].id==0&&view.fields[1].id==7&&view.fields[2].id==UINT32_MAX);
    CHECK("exact-half",view.fields[0].value.num==1&&view.fields[0].value.den==2&&view.fields[0].value.unit==GEO_UNIT_LENGTH);
    CHECK("zero-normalized",view.fields[1].value.num==0&&view.fields[1].value.den==1);
    CHECK("negative-rational",view.fields[2].value.num==-3&&view.fields[2].value.den==2&&view.fields[2].value.unit==GEO_UNIT_SCALAR);
    GeoVersionField equivalent[]={{7,{0,1,GEO_UNIT_SCALAR}},{UINT32_MAX,{-3,2,GEO_UNIT_SCALAR}},{0,{50,100,GEO_UNIT_LENGTH}}};
    d.fields=equivalent;CHECK("normalization-idempotent",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK&&geo_versions_count(store)==1);
    CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);d.identity.version=2;
    GeoVersionField duplicate[]={{0,{1,2,GEO_UNIT_LENGTH}},{0,{1,2,GEO_UNIT_LENGTH}}};d.fields=duplicate;d.field_count=2;
    CHECK("duplicate-field-rejected",geo_versions_put(store,&d,NULL)==GEO_VERSION_DUPLICATE_FIELD&&geo_versions_equal(store,before));
    GeoVersionField invalid={99,{1,0,GEO_UNIT_LENGTH}};d.fields=&invalid;d.field_count=1;GeoExactStatus detail=GEO_EXACT_OK;
    CHECK("zero-denominator",geo_versions_put(store,&d,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_DENOMINATOR&&geo_versions_equal(store,before));
    invalid.value.den=-1;CHECK("negative-denominator",geo_versions_put(store,&d,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_DENOMINATOR&&geo_versions_equal(store,before));
    invalid.value.den=1;invalid.value.num=INT64_MIN;
    CHECK("signed-magnitude-limit",geo_versions_put(store,&d,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_INTEGER_MAGNITUDE&&geo_versions_equal(store,before));
    invalid.value.num=1;invalid.value.unit=(GeoQuantityUnit)2;
    CHECK("invalid-unit",geo_versions_put(store,&d,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_INVALID_UNIT&&geo_versions_equal(store,before));
    invalid.value=(GeoQuantity){INT64_MAX,INT64_MAX,GEO_UNIT_LENGTH};
    CHECK("exact-max-normalizes",geo_versions_put(store,&d,&detail)==GEO_VERSION_OK&&detail==GEO_EXACT_OK);
    CHECK("exact-max-value",geo_versions_find(store,d.identity,&view)==GEO_VERSION_OK&&view.fields[0].value.num==1&&view.fields[0].value.den==1);
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static int immutable(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionField f={0,{1,2,GEO_UNIT_LENGTH}};GeoVersionDefinition d=definition("k",1,1);d.fields=&f;d.field_count=1;
    CHECK("put",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    d.content="abd";d.fingerprint=abd_hash;
    CHECK("immutable-content",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    d.content="abc";d.fingerprint=abc_hash;f.value.num=3;
    CHECK("immutable-field-value",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    f.value.num=1;f.value.unit=GEO_UNIT_SCALAR;
    CHECK("immutable-field-unit",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    f.value.unit=GEO_UNIT_LENGTH;f.id=1;
    CHECK("immutable-field-identity",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    f.id=0;d.field_count=0;
    CHECK("immutable-missing-field",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    d.field_count=1;f.value.num=2;f.value.den=4;
    CHECK("same-normalized-definition",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK&&geo_versions_equal(store,before));
    d.identity.version=2;d.content="abd";d.fingerprint=abd_hash;
    CHECK("new-version-permitted",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK&&geo_versions_count(store)==2);
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static int lookup(void)
{
    GeoVersionStore *store=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionField fields[]={{0,{5,2,GEO_UNIT_LENGTH}},{9,{7,1,GEO_UNIT_SCALAR}}};
    const unsigned char key[]={1,0,2};GeoVersionDefinition d=definition(key,3,4);d.fields=fields;d.field_count=2;
    CHECK("put",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    GeoVersionFieldView result;memset(&result,0x5a,sizeof result);unsigned char previous[sizeof result];memcpy(previous,&result,sizeof result);
    CHECK("field-existence",geo_versions_field(store,d.identity,8,&result)==GEO_VERSION_MISSING&&!memcmp(previous,&result,sizeof result));
    CHECK("field-zero-resolves",geo_versions_field(store,d.identity,0,&result)==GEO_VERSION_OK);
    CHECK("full-terminal-identity",result.identity.version==4&&result.identity.key_length==3&&!memcmp(result.identity.key,key,3)&&result.field.id==0);
    CHECK("fraction-not-rounded",result.field.value.num==5&&result.field.value.den==2&&result.field.value.unit==GEO_UNIT_LENGTH);
    CHECK("scalar-distinct",geo_versions_field(store,d.identity,9,&result)==GEO_VERSION_OK&&result.field.value.unit==GEO_UNIT_SCALAR);
    memcpy(previous,&result,sizeof result);d.identity.version=5;
    CHECK("missing-version-output",geo_versions_field(store,d.identity,0,&result)==GEO_VERSION_MISSING&&!memcmp(previous,&result,sizeof result));
    d.identity.version=0;CHECK("invalid-version-output",geo_versions_field(store,d.identity,0,&result)==GEO_VERSION_INVALID&&!memcmp(previous,&result,sizeof result));
    GeoVersionView view;memset(&view,0x5a,sizeof view);unsigned char old_view[sizeof view];memcpy(old_view,&view,sizeof view);
    CHECK("missing-index-output",geo_versions_at(store,1,&view)==GEO_VERSION_MISSING&&!memcmp(old_view,&view,sizeof view));
    CHECK("invalid-find-output",geo_versions_find(store,d.identity,&view)==GEO_VERSION_INVALID&&!memcmp(old_view,&view,sizeof view));
    d.identity.version=5;CHECK("missing-find-output",geo_versions_find(store,d.identity,&view)==GEO_VERSION_MISSING&&!memcmp(old_view,&view,sizeof view));
    geo_versions_destroy(store);return 0;
}

static int ownership(void)
{
    GeoVersionStore *store=NULL,*copy=NULL,*reordered=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    char key[]="key",content[]="abc",hash[65];memcpy(hash,abc_hash,65);
    GeoVersionField f={4,{3,2,GEO_UNIT_LENGTH}};GeoVersionDefinition d=definition(key,3,1);d.content=content;d.fingerprint=hash;d.fields=&f;d.field_count=1;
    CHECK("put",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);GeoVersionView view;
    CHECK("view",geo_versions_at(store,0,&view)==GEO_VERSION_OK);
    CHECK("owned-pointers",view.identity.key!=key&&view.content!=content&&view.fingerprint!=hash&&view.fields!=&f);
    key[0]='X';content[0]='X';hash[0]='0';f.value.num=77;
    CHECK("borrowed-input-copied",!memcmp(view.identity.key,"key",3)&&!memcmp(view.content,"abc",3)&&!memcmp(view.fingerprint,abc_hash,64)&&view.fields[0].value.num==3);
    const void *saved_key=view.identity.key,*saved_content=view.content;const GeoVersionField *saved_fields=view.fields;
    CHECK("borrowed-view-idempotent",geo_versions_put(store,&view,NULL)==GEO_VERSION_OK);
    GeoVersionDefinition another=view;another.identity.version=2;
    CHECK("borrowed-view-new-version",geo_versions_put(store,&another,NULL)==GEO_VERSION_OK);
    CHECK("view-stable",view.identity.key==saved_key&&view.content==saved_content&&view.fields==saved_fields&&view.fields[0].value.num==3);
    CHECK("clone",geo_versions_clone(store,&copy)==GEO_VERSION_OK);
    CHECK("copy-independent",copy!=store);
    GeoVersionView cloned;CHECK("clone-values",geo_versions_at(copy,0,&cloned)==GEO_VERSION_OK&&geo_versions_equal(copy,store));
    CHECK("clone-owned-pointers",cloned.identity.key!=view.identity.key&&cloned.content!=view.content&&cloned.fields!=view.fields);
    CHECK("new-store",geo_versions_create(&reordered)==GEO_VERSION_OK);
    CHECK("reverse-insert-2",geo_versions_put(reordered,&another,NULL)==GEO_VERSION_OK);
    CHECK("reverse-insert-1",geo_versions_put(reordered,&view,NULL)==GEO_VERSION_OK);
    CHECK("order-independent-equality",geo_versions_equal(store,reordered)&&geo_versions_equal(reordered,store));
    another.identity.version=3;CHECK("clone-append",geo_versions_put(copy,&another,NULL)==GEO_VERSION_OK);
    CHECK("clone-does-not-change-original",geo_versions_count(store)==2&&geo_versions_count(copy)==3&&!geo_versions_equal(store,copy));
    geo_versions_destroy(store);
    CHECK("clone-survives-original",cloned.identity.version==1&&!memcmp(cloned.content,"abc",3)&&cloned.fields[0].value.num==3);
    geo_versions_destroy(copy);geo_versions_destroy(reordered);return 0;
}

static int limits(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    CHECK("compatibility-capacities",GEO_VERSION_CAPACITY>=96&&GEO_VERSION_KEY_BYTES>=96&&GEO_VERSION_CONTENT_BYTES>=1024&&GEO_VERSION_FIELD_CAPACITY>=16);
    unsigned char key[GEO_VERSION_KEY_BYTES+1],content[GEO_VERSION_CONTENT_BYTES+1];memset(key,0x80,sizeof key);memset(content,'x',sizeof content);
    GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY+1];
    for(size_t i=0;i<GEO_VERSION_FIELD_CAPACITY+1;++i)fields[i]=(GeoVersionField){(uint32_t)i,{(int64_t)i,1,GEO_UNIT_LENGTH}};
    GeoVersionDefinition d=definition(key,GEO_VERSION_KEY_BYTES,UINT32_MAX);d.content=content;d.content_length=1024;d.fingerprint=full_hash;d.fields=fields;d.field_count=GEO_VERSION_FIELD_CAPACITY;
    CHECK("max-lengths",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    GeoVersionView view;CHECK("full-content-not-truncated",geo_versions_at(store,0,&view)==GEO_VERSION_OK&&view.content_length==1024&&!memcmp(view.content,content,1024));
    d.identity.key_length=GEO_VERSION_KEY_BYTES+1;
    CHECK("key-capacity",geo_versions_put(store,&d,NULL)==GEO_VERSION_CAPACITY_EXCEEDED&&geo_versions_equal(store,before));
    d.identity.key_length=GEO_VERSION_KEY_BYTES;d.content_length=GEO_VERSION_CONTENT_BYTES+1;
    CHECK("content-capacity",geo_versions_put(store,&d,NULL)==GEO_VERSION_CAPACITY_EXCEEDED&&geo_versions_equal(store,before));
    d.content_length=1024;d.field_count=GEO_VERSION_FIELD_CAPACITY+1;
    CHECK("field-capacity",geo_versions_put(store,&d,NULL)==GEO_VERSION_CAPACITY_EXCEEDED&&geo_versions_equal(store,before));
    d.field_count=GEO_VERSION_FIELD_CAPACITY;d.identity.version=0;
    CHECK("version-zero",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    d.identity.version=1;d.identity.key_length=0;
    CHECK("empty-key",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    d.identity.key_length=1;d.identity.key=NULL;
    CHECK("null-key",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    d.identity.key=key;d.content=NULL;
    CHECK("null-content",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    d.content=content;d.fields=NULL;
    CHECK("null-fields",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    GeoVersionStore *unchanged=store;
    CHECK("invalid-clone-output",geo_versions_clone(NULL,&unchanged)==GEO_VERSION_INVALID&&unchanged==store);
    CHECK("null-output",geo_versions_create(NULL)==GEO_VERSION_INVALID&&geo_versions_clone(store,NULL)==GEO_VERSION_INVALID);
    CHECK("null-store-contract",geo_versions_count(NULL)==0&&!geo_versions_equal(NULL,NULL)&&!geo_versions_equal(store,NULL));
    geo_versions_destroy(NULL);geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static int capacity(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    unsigned char key[4]={0};GeoVersionDefinition d=definition(key,4,1);
    for(size_t i=0;i<GEO_VERSION_CAPACITY;++i){key[0]=(unsigned char)i;key[1]=(unsigned char)(i>>8);
        CHECK("fill-capacity",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    }
    CHECK("count-at-capacity",geo_versions_count(store)==GEO_VERSION_CAPACITY);
    CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    GeoVersionView first;CHECK("first",geo_versions_at(store,0,&first)==GEO_VERSION_OK);
    CHECK("idempotent-at-capacity",geo_versions_put(store,&first,NULL)==GEO_VERSION_OK&&geo_versions_equal(store,before));
    GeoVersionDefinition changed=first;changed.content="abd";changed.fingerprint=abd_hash;
    CHECK("immutable-before-capacity",geo_versions_put(store,&changed,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    key[2]=1;CHECK("capacity-is-atomic",geo_versions_put(store,&d,NULL)==GEO_VERSION_CAPACITY_EXCEEDED&&geo_versions_equal(store,before));
    CHECK("old-view-stable-at-capacity",first.identity.key_length==4&&((const unsigned char *)first.identity.key)[0]==0&&!memcmp(first.content,"abc",3));
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static GeoVersionField decimal_field(uint32_t id,const char *text,GeoQuantityUnit unit)
{
    GeoVersionField f;memset(&f,0,sizeof f);f.id=id;f.kind=GEO_VERSION_DECIMAL_LITERAL;
    f.value.unit=unit;f.literal_length=strlen(text);memcpy(f.literal,text,f.literal_length);return f;
}

static int decimal_precision(void)
{
    GeoVersionStore *store=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    char leading[128],huge[128],tiny[128];memset(leading,'0',127);leading[126]='9';leading[127]=0;
    memset(huge,'9',127);huge[127]=0;memset(tiny,'0',127);tiny[1]='.';tiny[126]='1';tiny[127]=0;
    GeoVersionField values[]={decimal_field(1,leading,GEO_UNIT_LENGTH),decimal_field(2,huge,GEO_UNIT_LENGTH),decimal_field(3,tiny,GEO_UNIT_LENGTH)};
    GeoVersionDefinition d=definition("decimal",7,1);d.fields=values;d.field_count=3;
    CHECK("full-precision-publish",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    GeoVersionFieldView field;CHECK("full-precision-present",geo_versions_field(store,d.identity,2,&field)==GEO_VERSION_OK&&field.field.literal_length==127&&!memcmp(field.field.literal,huge,127));
    int64_t integer=-44;CHECK("leading-zero-integer",geo_versions_integer(store,d.identity,1,GEO_UNIT_LENGTH,1,100,&integer)==GEO_VERSION_OK&&integer==9);
    CHECK("huge-use-site-range",geo_versions_integer(store,d.identity,2,GEO_UNIT_LENGTH,1,100,&integer)==GEO_VERSION_RANGE&&integer==9);
    CHECK("tiny-fraction-not-rounded",geo_versions_integer(store,d.identity,3,GEO_UNIT_LENGTH,0,100,&integer)==GEO_VERSION_INTEGER&&integer==9);
    CHECK("missing-decimal-distinct",geo_versions_integer(store,d.identity,4,GEO_UNIT_LENGTH,0,100,&integer)==GEO_VERSION_MISSING&&integer==9);
    values[0].literal[126]='7';CHECK("literal-identity-immutable",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE);
    values[0]=decimal_field(1,"9",GEO_UNIT_LENGTH);CHECK("literal-spelling-retained",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE);
    GeoQuantity q={-7,3,GEO_UNIT_SCALAR};GeoExactStatus detail;
    GeoVersionField reduced=decimal_field(0,"1.8446744073709551614",GEO_UNIT_LENGTH);
    CHECK("reduce-before-int64",geo_version_field_quantity(&reduced,&q,&detail)==GEO_VERSION_OK&&q.num==INT64_MAX&&q.den==5000000000000000000LL&&q.unit==GEO_UNIT_LENGTH);
    reduced=decimal_field(0,"-12.5000",GEO_UNIT_SCALAR);
    CHECK("negative-exact-fraction",geo_version_field_quantity(&reduced,&q,&detail)==GEO_VERSION_OK&&q.num==-25&&q.den==2&&q.unit==GEO_UNIT_SCALAR);
    reduced=decimal_field(0,"+0009.000",GEO_UNIT_LENGTH);
    CHECK("signed-trailing-zero-integer",geo_version_field_integer(&reduced,GEO_UNIT_LENGTH,1,9,&integer)==GEO_VERSION_OK&&integer==9);
    CHECK("decimal-unit",geo_version_field_integer(&reduced,GEO_UNIT_SCALAR,1,9,&integer)==GEO_VERSION_UNIT&&integer==9);
    reduced=decimal_field(0,"-0009.000",GEO_UNIT_LENGTH);
    CHECK("negative-integer",geo_version_field_integer(&reduced,GEO_UNIT_LENGTH,-10,-1,&integer)==GEO_VERSION_OK&&integer==-9);
    reduced=decimal_field(0,tiny,GEO_UNIT_LENGTH);q=(GeoQuantity){7,3,GEO_UNIT_SCALAR};
    CHECK("tiny-rational-limit-explicit",geo_version_field_quantity(&reduced,&q,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_MULTIPLICATION_OVERFLOW&&q.num==7&&q.den==3&&q.unit==GEO_UNIT_SCALAR);
    reduced=decimal_field(0,huge,GEO_UNIT_LENGTH);
    CHECK("huge-rational-limit-explicit",geo_version_field_quantity(&reduced,&q,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_INTEGER_MAGNITUDE&&q.num==7&&q.den==3);
    reduced=decimal_field(0,"-0.0000000000000000000000000000000000000000",GEO_UNIT_LENGTH);
    CHECK("decimal-zero-normalizes",geo_version_field_quantity(&reduced,&q,&detail)==GEO_VERSION_OK&&q.num==0&&q.den==1);
    geo_versions_destroy(store);return 0;
}

static int decimal_validation(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionDefinition d=definition("syntax",6,1);GeoVersionField field=decimal_field(8,"9.5",GEO_UNIT_LENGTH);d.fields=&field;d.field_count=1;
    CHECK("fractional-source-legal",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    const char *invalid[]={"","+","-",".1","1.","1..0","1e3"," 9","9 ","--9","9/1"};d.identity.version=2;
    for(size_t i=0;i<sizeof invalid/sizeof *invalid;++i){field=decimal_field(8,invalid[i],GEO_UNIT_LENGTH);
        CHECK("malformed-decimal-atomic",geo_versions_put(store,&d,NULL)==GEO_VERSION_DECIMAL&&geo_versions_equal(store,before));
    }
    memset(field.literal,'9',GEO_VERSION_DECIMAL_BYTES);field.literal_length=GEO_VERSION_DECIMAL_BYTES+1;
    CHECK("decimal-too-long",geo_versions_put(store,&d,NULL)==GEO_VERSION_DECIMAL&&geo_versions_equal(store,before));
    field.literal_length=GEO_VERSION_DECIMAL_BYTES;field.value.unit=(GeoQuantityUnit)5;GeoExactStatus detail;
    CHECK("decimal-invalid-unit",geo_versions_put(store,&d,&detail)==GEO_VERSION_EXACT&&detail==GEO_EXACT_INVALID_UNIT&&geo_versions_equal(store,before));
    field.value.unit=GEO_UNIT_LENGTH;field.kind=(GeoVersionFieldKind)9;
    CHECK("unknown-field-kind",geo_versions_put(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    field.kind=GEO_VERSION_DECIMAL_LITERAL;
    CHECK("decimal-max-length",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    GeoVersionFieldView view;CHECK("decimal-max-not-truncated",geo_versions_field(store,d.identity,8,&view)==GEO_VERSION_OK&&view.field.literal_length==128&&!memcmp(view.field.literal,field.literal,128));
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

static int schemas_and_check(void)
{
    GeoVersionStore *store=NULL,*before=NULL;CHECK("create",geo_versions_create(&store)==GEO_VERSION_OK);
    GeoVersionDefinition d=definition("schema",6,1);char schema[]={'s',0,'1'};d.schema=schema;d.schema_length=3;
    CHECK("check-admits-without-publish",geo_versions_check(store,&d,NULL)==GEO_VERSION_OK&&geo_versions_count(store)==0);
    CHECK("schema-publish",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);CHECK("clone",geo_versions_clone(store,&before)==GEO_VERSION_OK);
    GeoVersionView view;CHECK("schema-owned",geo_versions_at(store,0,&view)==GEO_VERSION_OK&&view.schema!=schema&&view.schema_length==3&&!memcmp(view.schema,schema,3));
    schema[2]='2';CHECK("schema-immutable-check",geo_versions_check(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    CHECK("schema-immutable-put",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE&&geo_versions_equal(store,before));
    schema[2]='1';d.schema_length=1;CHECK("schema-length-immutable",geo_versions_put(store,&d,NULL)==GEO_VERSION_IMMUTABLE);
    d.schema=NULL;d.schema_length=3;CHECK("schema-null-invalid",geo_versions_check(store,&d,NULL)==GEO_VERSION_INVALID&&geo_versions_equal(store,before));
    char full[GEO_VERSION_SCHEMA_BYTES+1];memset(full,'s',sizeof full);d.schema=full;d.schema_length=sizeof full;
    CHECK("schema-too-long",geo_versions_put(store,&d,NULL)==GEO_VERSION_CAPACITY_EXCEEDED&&geo_versions_equal(store,before));
    d.schema_length=GEO_VERSION_SCHEMA_BYTES;d.identity.version=2;
    CHECK("full-schema-check",geo_versions_check(store,&d,NULL)==GEO_VERSION_OK&&geo_versions_equal(store,before));
    CHECK("full-schema-publish",geo_versions_put(store,&d,NULL)==GEO_VERSION_OK);
    CHECK("full-schema-read",geo_versions_find(store,d.identity,&view)==GEO_VERSION_OK&&view.schema_length==GEO_VERSION_SCHEMA_BYTES&&!memcmp(view.schema,full,sizeof full-1));
    geo_versions_destroy(before);geo_versions_destroy(store);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;int result=2;
    if(!strcmp(argv[1],"identity"))result=identity();
    else if(!strcmp(argv[1],"fingerprint"))result=fingerprint();
    else if(!strcmp(argv[1],"fields"))result=fields();
    else if(!strcmp(argv[1],"immutable"))result=immutable();
    else if(!strcmp(argv[1],"lookup"))result=lookup();
    else if(!strcmp(argv[1],"ownership"))result=ownership();
    else if(!strcmp(argv[1],"limits"))result=limits();
    else if(!strcmp(argv[1],"capacity"))result=capacity();
    else if(!strcmp(argv[1],"decimal-precision"))result=decimal_precision();
    else if(!strcmp(argv[1],"decimal-validation"))result=decimal_validation();
    else if(!strcmp(argv[1],"schemas-and-check"))result=schemas_and_check();
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
