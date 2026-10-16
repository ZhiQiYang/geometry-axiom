#include "parameters.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#define CHECK(condition) do{if(!(condition)){fprintf(stderr,"line %d: %s\n",__LINE__,#condition);return 1;}}while(0)
static void literal(GeoParameterField *f,uint32_t card,uint32_t id,int type,const char *num,const char *den)
{
    memset(f,0,sizeof *f);f->parameter_id=card;f->id=id;f->type=type;snprintf(f->name,sizeof f->name,"f%u",id);
    snprintf(f->expression,sizeof f->expression,"{\"op\":\"literal\",\"num\":\"%s\",\"den\":\"%s\",\"unit\":\"%s\"}",num,den,type==0?"mm":"1");
}
static bool put(GeoParameterStore *s,uint32_t id,GeoParameterField *fields,size_t n,GeoParameterError *error)
{
    GeoParameterCard card;geo_parameters_begin_definition(s,id,&card);snprintf(card.name,sizeof card.name,"c%u",id);card.count=n;
    for(size_t i=0;i<n;++i)if(!geo_parameters_accept_field(s,&card,fields,i,error))return false;
    return geo_parameters_put(s,&card,fields,error);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;GeoParameterStore *s=geo_parameters_create();CHECK(s);GeoParameterError e;GeoParameterField f[3];
    if(!strcmp(argv[1],"exact")){
        literal(&f[0],9,7,0,"7","3");literal(&f[1],9,8,0,"1","1");
        snprintf(f[1].expression,sizeof f[1].expression,"{\"op\":\"mul\",\"left\":{\"op\":\"ref\",\"parameterId\":9,\"fieldId\":7},\"right\":{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"1\"}}");
        CHECK(put(s,9,f,2,&e));CHECK(geo_parameters_rebuild(s,&e));GeoQuantity q;GeoCoord x=197;
        CHECK(geo_parameters_dimension_value(s,(GeoParameterRef){true,9,7},&q,&e)&&q.num==7&&q.den==3);
        CHECK(!geo_parameters_coordinate(s,(GeoParameterRef){true,9,7},&x,&e)&&x==197&&e.status==GEO_PARAMETER_COORDINATE);
        CHECK(geo_parameters_coordinate(s,(GeoParameterRef){true,9,8},&x,&e)&&x==7);
    }else if(!strcmp(argv[1],"types")){
        literal(f,1,1,GEO_PARAMETER_COUNT,"-1","1");CHECK(put(s,1,f,1,&e));
        CHECK(!geo_parameters_rebuild(s,&e)&&e.status==GEO_PARAMETER_COUNT_VALUE);
        CHECK(e.trace_count==1&&e.trace[0].parameter_id==1&&e.trace[0].field_id==1);
        literal(f,1,1,GEO_PARAMETER_COUNT,"3","2");CHECK(put(s,1,f,1,&e));CHECK(!geo_parameters_rebuild(s,&e)&&e.status==GEO_PARAMETER_COUNT_VALUE);
        literal(f,1,1,GEO_PARAMETER_RATIO,"3","2");CHECK(put(s,1,f,1,&e));CHECK(geo_parameters_rebuild(s,&e));
        GeoQuantity q={197,1,0};CHECK(!geo_parameters_dimension_value(s,(GeoParameterRef){true,1,1},&q,&e)&&e.status==GEO_PARAMETER_NOT_DIMENSION&&q.num==197);
    }else if(!strcmp(argv[1],"identity")){
        literal(&f[0],0,1,0,"1","1");literal(&f[1],0,4,0,"4","1");CHECK(put(s,0,f,2,&e));
        CHECK(geo_parameters_find(s,0)->next_field_id==5);CHECK(put(s,0,f,1,&e));
        CHECK(!put(s,0,f,2,&e)&&e.status==GEO_PARAMETER_REUSED_FIELD);CHECK(geo_parameters_field_count(s)==1);
        literal(&f[1],0,5,0,"5","1");CHECK(put(s,0,f,2,&e));CHECK(geo_parameters_find(s,0)->next_field_id==6);
        literal(&f[1],0,UINT32_MAX,0,"9","1");CHECK(put(s,0,f,2,&e));CHECK(!geo_parameters_find(s,0)->next_field_id);
        CHECK(put(s,0,f,1,&e));literal(&f[1],0,6,0,"6","1");CHECK(!put(s,0,f,2,&e)&&e.status==GEO_PARAMETER_REUSED_FIELD);
    }else if(!strcmp(argv[1],"clone")){
        literal(f,1,1,0,"1","1");CHECK(put(s,1,f,1,&e));CHECK(geo_parameters_rebuild(s,&e));
        GeoParameterStore *copy=geo_parameters_clone(s);CHECK(copy&&geo_parameters_equal(s,copy));
        literal(f,1,1,0,"5","1");CHECK(put(copy,1,f,1,&e));CHECK(geo_parameters_rebuild(copy,&e));
        CHECK(!geo_parameters_equal(s,copy));CHECK(geo_parameters_fields(s)[0].value.num==1);CHECK(geo_parameters_fields(copy)[0].value.num==5);
        CHECK(geo_parameters_remove(copy,1,&e));CHECK(!geo_parameters_card_count(copy));CHECK(geo_parameters_card_count(s)==1);geo_parameters_destroy(copy);
        literal(f,2,8,0,"8","1");CHECK(put(s,2,f,1,&e));
        CHECK(geo_parameters_put(s,geo_parameters_find(s,1),geo_parameters_fields(s),&e));
        CHECK(geo_parameters_rebuild(s,&e));
        CHECK(geo_parameters_field_index(s,1,1)>=0&&geo_parameters_field_index(s,2,8)>=0);
        CHECK(geo_parameters_fields(s)[geo_parameters_field_index(s,1,1)].value.num==1);
    }else if(!strcmp(argv[1],"references")){
        literal(f,0,1,0,"1","1");snprintf(f[0].expression,sizeof f[0].expression,"{\"op\":\"ref\",\"parameterId\":2,\"fieldId\":3}");
        CHECK(put(s,0,f,1,&e));CHECK(!geo_parameters_rebuild(s,&e));CHECK(e.status==GEO_PARAMETER_MISSING_FIELD&&e.source.parameter_id==2&&e.source.field_id==3&&e.trace_count==1);
        literal(f,2,3,0,"1","1");snprintf(f[0].expression,sizeof f[0].expression,"{\"op\":\"ref\",\"parameterId\":0,\"fieldId\":1}");CHECK(put(s,2,f,1,&e));
        CHECK(!geo_parameters_rebuild(s,&e)&&e.status==GEO_PARAMETER_CYCLE&&e.trace_count==2);
        CHECK(e.trace[0].parameter_id==2&&e.trace[1].parameter_id==0);
    }else if(!strcmp(argv[1],"staging")){
        GeoParameterCard card={.id=12,.next_field_id=5};strcpy(card.name,"staged");CHECK(geo_parameters_stage_card(s,&card));CHECK(!geo_parameters_stage_card(s,&card));
        literal(f,12,4,0,"9","1");CHECK(geo_parameters_stage_field(s,f));CHECK(!geo_parameters_stage_field(s,f));CHECK(geo_parameters_rebuild(s,&e));
        CHECK(geo_parameters_find(s,12)->fields[0]==4&&geo_parameters_fields(s)[0].value.num==9);
        literal(f,12,5,0,"10","1");CHECK(!geo_parameters_stage_field(s,f));
        /* A profile dimension's own closure must not inherit an unrelated
         * failed field or consume a stale zero cache after a definition edit. */
        literal(f,1,1,0,"4","1");strcpy(f[0].expression,"{\"op\":\"ref\",\"parameterId\":99,\"fieldId\":1}");
        CHECK(put(s,1,f,1,&e));literal(f,12,4,0,"17","1");CHECK(put(s,12,f,1,&e));
        CHECK(!geo_parameters_rebuild(s,&e)&&e.status==GEO_PARAMETER_MISSING_FIELD);
        CHECK(geo_parameters_evaluate_field(s,(GeoParameterRef){true,12,4},&e));
        CHECK(geo_parameters_fields(s)[geo_parameters_field_index(s,12,4)].value.num==17);
        CHECK(!geo_parameters_evaluate_field(s,(GeoParameterRef){true,1,1},&e)&&e.trace_count==1);
        CHECK(e.trace[0].parameter_id==1&&e.source.parameter_id==99);
    }else{geo_parameters_destroy(s);return 2;}
    geo_parameters_destroy(s);return 0;
}
