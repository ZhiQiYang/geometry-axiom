#include "datums.h"
#include <stdio.h>
#include <string.h>
#include <limits.h>
static bool value(void *opaque,const GeoLinearSource *source,GeoQuantity *out)
{
    if(source->provider!=21||strcmp(source->key,"distance"))return false;
    *out=*(GeoQuantity *)opaque;return true;
}
static GeoLinearExpression expression(bool complete)
{
    GeoLinearExpression result;geo_linear_begin(&result,GEO_LINEAR_EXACT_INTEGER_FINAL);
    geo_linear_append(&result,1,1,(GeoLinearSource){21,0,0,"distance"});geo_linear_finish(&result,complete);return result;
}
static int ownership(void)
{
    GeoDatumStore *a=geo_datums_create();if(!a)return 2;
    GeoLinearExpression input=expression(true);GeoQuantity quantity={37,1,GEO_UNIT_LENGTH};
    if(!geo_datums_put(a,0,2,&input)||geo_datums_evaluate(a,0,value,&quantity).status!=GEO_LINEAR_OK)return 1;
    memset(&input,0,sizeof input);
    if(geo_datums_find(a,0)->position!=37||strcmp(geo_datums_find(a,0)->expression.keys,"distance"))return 1;
    GeoDatumStore *b=geo_datums_clone(a);if(!b)return 2;
    quantity.num=91;if(geo_datums_evaluate(b,0,value,&quantity).status!=GEO_LINEAR_OK||geo_datums_find(a,0)->position!=37)return 1;
    const GeoDatum *borrowed=geo_datums_find(b,0);
    if(!geo_datums_put(b,0,1,&borrowed->expression)||geo_datums_find(b,0)->position!=0)return 1;
    if(!geo_datums_remove(b,0)||geo_datums_count(b)||geo_datums_count(a)!=1)return 1;
    geo_datums_destroy(a);geo_datums_destroy(b);return 0;
}
static int capacity(void)
{
    GeoDatumStore *store=geo_datums_create();if(!store)return 2;GeoLinearExpression input=expression(true);
    for(uint32_t i=0;i<64;++i)if(!geo_datums_put(store,i,0,&input))return 1;
    if(geo_datums_put(store,64,0,&input)||!geo_datums_put(store,12,2,&input))return 1;
    if(!geo_datums_remove(store,31)||!geo_datums_put(store,UINT32_MAX,1,&input)||geo_datums_values(store)[63].id!=UINT32_MAX)return 1;
    if(geo_datums_at(store,64)||geo_datums_remove(store,31))return 1;
    geo_datums_destroy(store);return 0;
}
static int failures(void)
{
    GeoDatumStore *store=geo_datums_create();if(!store)return 2;GeoLinearExpression input=expression(true);GeoQuantity quantity={17,1,GEO_UNIT_LENGTH};
    geo_datums_put(store,7,0,&input);geo_datums_evaluate(store,0,value,&quantity);
    quantity.den=2;if(geo_datums_evaluate(store,0,value,&quantity).status!=GEO_LINEAR_NOT_INTEGER||geo_datums_find(store,7)->position!=17)return 1;
    quantity=(GeoQuantity){GEO_COORD_LIMIT+1,1,GEO_UNIT_LENGTH};
    if(geo_datums_evaluate(store,0,value,&quantity).status!=GEO_LINEAR_RANGE||geo_datums_find(store,7)->position!=GEO_COORD_LIMIT+1)return 1;
    geo_linear_finish(&input,false);geo_datums_put(store,7,0,&input);quantity.num=9;
    if(geo_datums_evaluate(store,0,value,&quantity).status!=GEO_LINEAR_INVALID||geo_datums_find(store,7)->position!=0)return 1;
    geo_datums_destroy(store);return 0;
}
static int frames(void)
{
    const GeoVector3 vectors[]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    GeoDatum datum={0};datum.position=37;
    for(size_t u=0;u<6;++u)for(size_t v=0;v<6;++v)if(!geo_vector_dot(vectors[u],vectors[v])){
        GeoFrame frame={{101,-211,307},vectors[u],vectors[v],geo_vector_cross(vectors[u],vectors[v])};
        for(int axis=0;axis<3;++axis){datum.axis=axis;GeoDatumIntersection result={9,1234};
            GeoDatumIntersectionStatus status=geo_datum_intersection(&datum,&frame,&result);
            GeoCoord normal=axis==0?frame.normal.x:axis==1?frame.normal.y:frame.normal.z;bool parallel=normal!=0;
            if(parallel){if(status!=GEO_DATUM_INTERSECTION_PARALLEL||result.coordinate_axis!=9||result.coordinate!=1234)return 1;continue;}
            if(status!=GEO_DATUM_INTERSECTION_OK)return 1;
            GeoPoint2 local={result.coordinate_axis==0?result.coordinate:0,result.coordinate_axis==1?result.coordinate:0};
            GeoPoint3 point=geo_frame_point(&frame,local.u,local.v,0);
            GeoCoord component=axis==0?point.x:axis==1?point.y:point.z;
            if(component!=37)return 1;
        }
    }
    GeoFrame horizontal={{0,0,37},{1,0,0},{0,1,0},{0,0,1}};GeoDatumIntersection result;datum.axis=2;
    if(geo_datum_intersection(&datum,&horizontal,&result)!=GEO_DATUM_INTERSECTION_COINCIDENT)return 1;
    horizontal.origin.z=38;if(geo_datum_intersection(&datum,&horizontal,&result)!=GEO_DATUM_INTERSECTION_PARALLEL)return 1;
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ownership"))return ownership();
    if(!strcmp(argv[1],"capacity"))return capacity();
    if(!strcmp(argv[1],"failures"))return failures();
    if(!strcmp(argv[1],"frames"))return frames();
    return 2;
}
