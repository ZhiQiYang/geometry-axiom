/* Second-template result exporter. Link only K exact/geometry/grid and the
 * existing rectangular_grid recipe; no World, model-base or application code. */
#include "rectangular_grid.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

static void key(RGSourceKey source)
{
    printf("{\"owner\":\"%" PRIu64 "\",\"field\":\"%" PRIu64 "\",\"kind\":\"%s\"}",
        source.owner,source.field,source.kind==RG_LENGTH?"length":"count");
}

static void quantity(GeoQuantity value)
{
    printf("{\"num\":\"%" PRId64 "\",\"den\":\"%" PRId64 "\",\"unit\":\"%s\"}",
        value.num,value.den,value.unit==GEO_UNIT_LENGTH?"length":"scalar");
}

static void source(const RGSource *value)
{
    fputs("{\"key\":",stdout);key(value->key);
    printf(",\"revision\":\"%" PRIu64 "\",\"value\":",value->revision);
    quantity(value->value);putchar('}');
}

static void success(const RGResult *result,const RGSource *thickness)
{
    static const char *const names[]={"width","height","columns","rows","thickness"};
    fputs("{\"schema\":\"rectangular-grid-native-view/1\",\"status\":\"OK\",\"recipe\":\"rectangular-grid/1\",\"sources\":[",stdout);
    for(unsigned i=0;i<RG_FIELD_COUNT;i++){if(i)putchar(',');source(&result->sources[i]);}
    putchar(',');source(thickness);fputs("],\"bindings\":{",stdout);
    for(unsigned i=0;i<=RG_FIELD_COUNT;i++){
        printf("%s\"%s\":",i?",":"",names[i]);key(i<RG_FIELD_COUNT?result->sources[i].key:thickness->key);
    }
    fputs("},\"frame\":{\"origin\":[0,0,0],\"u\":[1,0,0],\"v\":[0,1,0],\"n\":[0,0,1]},\"cells\":[",stdout);
    for(size_t i=0;i<result->cell_count;i++){
        const RGCell *cell=&result->cells[i];GeoRect2 b=cell->bounds;
        printf("%s{\"column\":%u,\"row\":%u,\"region\":{\"outer\":[[%" PRId64 ",%" PRId64 "],[%" PRId64 ",%" PRId64 "],[%" PRId64 ",%" PRId64 "],[%" PRId64 ",%" PRId64 "]],\"holes\":[]}}",
            i?",":"",cell->column,cell->row,b.min_u,b.min_v,b.max_u,b.min_v,b.max_u,b.max_v,b.min_u,b.max_v);
    }
    fputs("]}\n",stdout);
}

static void rejected(const RGDiagnostic *diagnostic,bool unchanged)
{
    printf("{\"schema\":\"rectangular-grid-native-view/1\",\"status\":\"%s\",\"previousUnchanged\":%s,\"diagnostic\":{\"source\":",
        rectangular_grid_status_code(diagnostic->status),unchanged?"true":"false");
    key(diagnostic->source);fputs(",\"value\":",stdout);quantity(diagnostic->value);
    printf(",\"divisions\":%u,\"requiredStep\":",diagnostic->divisions);quantity(diagnostic->required_step);
    printf(",\"coreStatus\":%d}}\n",(int)diagnostic->grid_status);
}

int main(void)
{
    RGSource inputs[]={
        {{71,1,RG_LENGTH},1,{1000,1,GEO_UNIT_LENGTH}},
        {{71,2,RG_LENGTH},1,{600,1,GEO_UNIT_LENGTH}},
        {{71,3,RG_COUNT},1,{5,1,GEO_UNIT_SCALAR}},
        {{71,4,RG_COUNT},1,{3,1,GEO_UNIT_SCALAR}},
    };
    RGSource thickness={{71,5,RG_LENGTH},1,{10,1,GEO_UNIT_LENGTH}};
    if(geo_quantity_normalize(thickness.value,&thickness.value)!=GEO_EXACT_OK ||
       thickness.value.den!=1 || thickness.value.num<=0 || !geo_coord_in_range(thickness.value.num))return 2;
    RGDefinition definition;for(unsigned i=0;i<RG_FIELD_COUNT;i++)definition.sources[i]=inputs[i].key;
    RGResult current,before;RGDiagnostic diagnostic;memset(&current,0,sizeof current);
    if(rectangular_grid_evaluate(&definition,inputs,4,&current,&diagnostic)!=RG_OK){fputs("INITIAL_NATIVE_REJECTED\n",stderr);return 1;}
    success(&current,&thickness);
    inputs[RG_WIDTH].value.num=1200;inputs[RG_WIDTH].revision=2;
    if(rectangular_grid_evaluate(&definition,inputs,4,&current,&diagnostic)!=RG_OK){fputs("UPDATED_NATIVE_REJECTED\n",stderr);return 1;}
    success(&current,&thickness);before=current;
    inputs[RG_WIDTH].value.num=1000;inputs[RG_WIDTH].revision=3;
    inputs[RG_COLUMNS].value.num=3;inputs[RG_COLUMNS].revision=2;
    RGStatus status=rectangular_grid_evaluate(&definition,inputs,4,&current,&diagnostic);
    if(status!=RG_FRACTIONAL_CELL){fputs("FRACTIONAL_CELL_ACCEPTED\n",stderr);return 1;}
    bool unchanged=memcmp(&current,&before,sizeof current)==0;
    rejected(&diagnostic,unchanged);
    return unchanged?0:1;
}
