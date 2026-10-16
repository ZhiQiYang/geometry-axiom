#include "linear.h"
#include <limits.h>
#include <string.h>

/* Legacy floor-mode reduction order is intentionally distinct from quantity
 * operations: it cancels the source value before summing coefficients. */
static int64_t geo_linear_gcd(int64_t a,int64_t b)
{if(a<0)a=-a;while(b){int64_t r=a%b;a=b;b=r;}return a;}

void geo_linear_begin(GeoLinearExpression *expression,GeoLinearMode mode)
{
    if(!expression)return;
    memset(expression,0,sizeof *expression); expression->mode=mode;
}
bool geo_linear_append(GeoLinearExpression *expression,int64_t numerator,int64_t denominator,
                       GeoLinearSource source)
{
    if(!expression||expression->count>=GEO_LINEAR_MAX_TERMS||expression->key_bytes>GEO_LINEAR_KEY_BYTES||numerator==INT64_MIN||denominator<=0||!source.provider)return false;
    const char *key=source.key?source.key:""; size_t length=strlen(key)+1;
    if(length>GEO_LINEAR_KEY_BYTES-expression->key_bytes)return false;
    GeoLinearTerm term={numerator,denominator,source.provider,source.id,source.field,expression->key_bytes};
    memcpy(expression->keys+expression->key_bytes,key,length); expression->key_bytes+=length;
    expression->terms[expression->count++]=term; return true;
}
void geo_linear_finish(GeoLinearExpression *expression,bool complete)
{if(expression)expression->complete=complete;}

GeoLinearResult geo_linear_evaluate(const GeoLinearExpression *expression,GeoLinearResolver resolve,void *state)
{
    GeoLinearResult result={GEO_LINEAR_INVALID,GEO_EXACT_OK,0,{0,1,GEO_UNIT_LENGTH}};
    if(!expression||!resolve||expression->count>GEO_LINEAR_MAX_TERMS||expression->key_bytes>GEO_LINEAR_KEY_BYTES||
       (expression->mode!=GEO_LINEAR_FLOOR_FINAL&&expression->mode!=GEO_LINEAR_EXACT_INTEGER_FINAL))return result;
    int64_t sum=0,den=1;
    for(size_t i=0;i<expression->count;++i){
        result.term=i; const GeoLinearTerm *term=&expression->terms[i];
        if(term->denominator<=0||term->numerator==INT64_MIN||!term->provider||term->key_offset>=expression->key_bytes||
           !memchr(expression->keys+term->key_offset,0,expression->key_bytes-term->key_offset))return result;
        GeoLinearSource source={term->provider,term->id,term->field,expression->keys+term->key_offset};
        GeoQuantity value={0,1,GEO_UNIT_LENGTH};
        if(!resolve(state,&source,&value)){result.status=GEO_LINEAR_SOURCE_FAILED;return result;}
        GeoExactStatus exact=GEO_EXACT_OK;
        if(expression->mode==GEO_LINEAR_EXACT_INTEGER_FINAL){
            GeoQuantity coefficient={term->numerator,term->denominator,GEO_UNIT_SCALAR},product;
            exact=geo_quantity_binary(GEO_EXACT_MULTIPLY,value,coefficient,&product);
            if(exact==GEO_EXACT_OK)exact=geo_quantity_binary(GEO_EXACT_ADD,result.value,product,&result.value);
        }else{
            if(value.den!=1||value.unit!=GEO_UNIT_LENGTH||value.num==INT64_MIN)return result;
            int64_t num=term->numerator,d=term->denominator,v=value.num;
            int64_t k=geo_linear_gcd(v,d);v/=k;d/=k;
            k=geo_linear_gcd(num,d);num/=k;d/=k;
            exact=geo_integer_multiply(num,v,&num);
            if(exact==GEO_EXACT_OK){
                int64_t x,y,newden;k=geo_linear_gcd(den,d);
                exact=geo_integer_multiply(sum,d/k,&x);
                if(exact==GEO_EXACT_OK)exact=geo_integer_multiply(num,den/k,&y);
                if(exact==GEO_EXACT_OK)exact=geo_integer_add(x,y,&sum);
                if(exact==GEO_EXACT_OK)exact=geo_integer_multiply(den,d/k,&newden);
                if(exact==GEO_EXACT_OK){den=newden;k=geo_linear_gcd(sum,den);sum/=k;den/=k;}
            }
        }
        if(exact!=GEO_EXACT_OK){result.status=GEO_LINEAR_ARITHMETIC;result.exact_status=exact;return result;}
    }
    result.term=expression->count;
    if(!expression->complete||!expression->count)return result;
    if(expression->mode==GEO_LINEAR_EXACT_INTEGER_FINAL){
        if(result.value.den!=1){result.status=GEO_LINEAR_NOT_INTEGER;return result;}
    }else result.value=(GeoQuantity){sum/den-(sum<0&&sum%den!=0),1,GEO_UNIT_LENGTH};
    result.status=geo_coord_in_range(result.value.num)?GEO_LINEAR_OK:GEO_LINEAR_RANGE;
    return result;
}
