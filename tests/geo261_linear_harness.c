#include "linear.h"
#include "named_values.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

typedef struct { GeoQuantity values[64];size_t count,calls;bool failed; } Sources;
static bool resolve(void *opaque,const GeoLinearSource *source,GeoQuantity *value)
{
    Sources *sources=opaque;++sources->calls;
    if(source->provider!=71||source->id>=sources->count||sources->failed)return false;
    if(strcmp(source->key,"opaque:unchanged/whole key")||source->field!=9)return false;
    *value=sources->values[source->id];return true;
}
static GeoLinearSource source(size_t id)
{GeoLinearSource result={71,(uint32_t)id,9,"opaque:unchanged/whole key"};return result;}
static int named(void)
{
    GeoNamedValues *a=geo_named_values_create();if(!a)return 2;
    if(!geo_named_values_put(a,"width",91)||geo_named_values_find(a,"width")->value!=91)return 1;
    if(geo_named_values_put(a,"bad name",3)||geo_named_values_put(a,"a",GEO_COORD_LIMIT+1))return 1;
    const GeoNamedValue *borrowed=geo_named_values_find(a,"width");
    if(!geo_named_values_put(a,borrowed->name,37)||geo_named_values_count(a)!=1)return 1;
    GeoNamedValues *b=geo_named_values_clone(a);if(!b)return 2;
    if(!geo_named_values_remove(b,"width")||geo_named_values_count(b)!=0||geo_named_values_count(a)!=1)return 1;
    char name[32];for(int i=1;i<64;++i){snprintf(name,sizeof name,"v%d",i);if(!geo_named_values_put(a,name,i))return 1;}
    if(geo_named_values_put(a,"overflow",1)||geo_named_values_count(a)!=64)return 1;
    if(!geo_named_values_remove(a,"v32")||!geo_named_values_put(a,"replacement",1)||strcmp(geo_named_values_at(a,63)->name,"replacement"))return 1;
    geo_named_values_destroy(a);geo_named_values_destroy(b);return 0;
}
static int statuses(void)
{
    GeoLinearExpression expression;Sources sources={0};sources.count=1;sources.values[0]=(GeoQuantity){-1,1,GEO_UNIT_LENGTH};
    geo_linear_begin(&expression,GEO_LINEAR_FLOOR_FINAL);geo_linear_append(&expression,1,2,source(0));geo_linear_finish(&expression,true);
    GeoLinearResult result=geo_linear_evaluate(&expression,resolve,&sources);
    if(result.status!=GEO_LINEAR_OK||result.value.num!=-1)return 1;
    expression.mode=GEO_LINEAR_EXACT_INTEGER_FINAL;result=geo_linear_evaluate(&expression,resolve,&sources);
    if(result.status!=GEO_LINEAR_NOT_INTEGER||result.value.num!=-1||result.value.den!=2)return 1;
    sources.values[0].num=INT64_MAX;expression.terms[0].numerator=3;expression.terms[0].denominator=1;
    result=geo_linear_evaluate(&expression,resolve,&sources);if(result.status!=GEO_LINEAR_ARITHMETIC)return 1;
    sources.failed=true;result=geo_linear_evaluate(&expression,resolve,&sources);if(result.status!=GEO_LINEAR_SOURCE_FAILED)return 1;
    sources.failed=false;sources.values[0].num=1;expression.terms[0].numerator=1;expression.complete=false;sources.calls=0;
    result=geo_linear_evaluate(&expression,resolve,&sources);if(result.status!=GEO_LINEAR_INVALID||sources.calls!=1)return 1;
    expression.complete=true;sources.values[0].num=GEO_COORD_LIMIT+1;result=geo_linear_evaluate(&expression,resolve,&sources);
    if(result.status!=GEO_LINEAR_RANGE||result.value.num!=GEO_COORD_LIMIT+1)return 1;
    return 0;
}
int main(int argc,char **argv)
{
    if(argc==2&&!strcmp(argv[1],"named"))return named();
    if(argc==2&&!strcmp(argv[1],"statuses"))return statuses();
    if(argc<5||(argc-2)%3)return 2;
    GeoLinearExpression expression;Sources sources={0};geo_linear_begin(&expression,(GeoLinearMode)atoi(argv[1]));
    for(int i=2;i<argc;i+=3){size_t at=sources.count++;sources.values[at]=(GeoQuantity){strtoll(argv[i],NULL,10),1,GEO_UNIT_LENGTH};
        if(!geo_linear_append(&expression,strtoll(argv[i+1],NULL,10),strtoll(argv[i+2],NULL,10),source(at)))return 2;}
    geo_linear_finish(&expression,true);GeoLinearResult result=geo_linear_evaluate(&expression,resolve,&sources);
    printf("%d %lld %lld %zu\n",(int)result.status,(long long)result.value.num,(long long)result.value.den,sources.calls);return 0;
}
