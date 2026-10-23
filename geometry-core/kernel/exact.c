#ifndef GEOMETRY_KERNEL_EXACT_IMPLEMENTATION
#define GEOMETRY_KERNEL_EXACT_IMPLEMENTATION
#include "exact.h"
#include <limits.h>

/* Called only after signed-magnitude and positive-denominator validation. */
static int64_t geo_exact_gcd(int64_t a,int64_t b)
{ if(a<0)a=-a;while(b){int64_t r=a%b;a=b;b=r;}return a; }
static GeoExactStatus geo_quantity_valid(GeoQuantity value)
{
    if(value.num==INT64_MIN)return GEO_EXACT_INTEGER_MAGNITUDE;
    if(value.den<=0)return GEO_EXACT_DENOMINATOR;
    if(value.unit!=GEO_UNIT_SCALAR&&value.unit!=GEO_UNIT_LENGTH)return GEO_EXACT_INVALID_UNIT;
    return GEO_EXACT_OK;
}
GeoExactStatus geo_integer_multiply(int64_t a,int64_t b,int64_t *out)
{
    int64_t x,y;
    if(a==INT64_MIN||b==INT64_MIN)return GEO_EXACT_INTEGER_MAGNITUDE;
    x=a<0?-a:a;y=b<0?-b:b;
    if(y&&x>INT64_MAX/y)return GEO_EXACT_MULTIPLICATION_OVERFLOW;
    *out=a*b;return GEO_EXACT_OK;
}
GeoExactStatus geo_integer_add(int64_t a,int64_t b,int64_t *out)
{
    if(a==INT64_MIN||b==INT64_MIN)return GEO_EXACT_INTEGER_MAGNITUDE;
    if((b>0&&a>INT64_MAX-b)||(b<0&&a< -INT64_MAX-b))return GEO_EXACT_SUM_OVERFLOW;
    *out=a+b;return GEO_EXACT_OK;
}
GeoExactStatus geo_quantity_normalize(GeoQuantity value,GeoQuantity *out)
{
    GeoExactStatus status=geo_quantity_valid(value);int64_t g;
    if(status!=GEO_EXACT_OK)return status;
    g=geo_exact_gcd(value.num,value.den);value.num/=g;value.den/=g;
    *out=value;return GEO_EXACT_OK;
}
GeoExactStatus geo_quantity_binary(GeoExactOperation operation,GeoQuantity a,GeoQuantity b,GeoQuantity *out)
{
    GeoExactStatus status;GeoQuantity result;int64_t g,x,y,n,d;
    status=geo_quantity_valid(a);if(status!=GEO_EXACT_OK)return status;
    status=geo_quantity_valid(b);if(status!=GEO_EXACT_OK)return status;
    if(operation==GEO_EXACT_ADD||operation==GEO_EXACT_SUBTRACT){
        if(a.unit!=b.unit)return GEO_EXACT_UNIT_MISMATCH;
        if(operation==GEO_EXACT_SUBTRACT)b.num=-b.num;
        g=geo_exact_gcd(a.den,b.den);
        status=geo_integer_multiply(a.num,b.den/g,&x);if(status!=GEO_EXACT_OK)return status;
        status=geo_integer_multiply(b.num,a.den/g,&y);if(status!=GEO_EXACT_OK)return status;
        status=geo_integer_add(x,y,&n);if(status!=GEO_EXACT_OK)return status;
        status=geo_integer_multiply(a.den,b.den/g,&d);if(status!=GEO_EXACT_OK)return status;
        return geo_quantity_normalize((GeoQuantity){n,d,a.unit},out);
    }
    if(operation==GEO_EXACT_MULTIPLY){
        if(a.unit&&b.unit)return GEO_EXACT_PRODUCT_UNIT;
        result.unit=(GeoQuantityUnit)(a.unit+b.unit);
    }else if(operation==GEO_EXACT_DIVIDE){
        if(!b.num)return GEO_EXACT_DIVISION_ZERO;
        if(!a.unit&&b.unit)return GEO_EXACT_INVERSE_UNIT;
        result.unit=(GeoQuantityUnit)(a.unit-b.unit);n=b.num;b.num=b.den;b.den=n;
        if(b.den<0){b.den=-b.den;b.num=-b.num;}
    }else return GEO_EXACT_UNKNOWN_OPERATION;
    g=geo_exact_gcd(a.num,b.den);a.num/=g;b.den/=g;
    g=geo_exact_gcd(b.num,a.den);b.num/=g;a.den/=g;
    status=geo_integer_multiply(a.num,b.num,&result.num);if(status!=GEO_EXACT_OK)return status;
    status=geo_integer_multiply(a.den,b.den,&result.den);if(status!=GEO_EXACT_OK)return status;
    return geo_quantity_normalize(result,out);
}
#endif
