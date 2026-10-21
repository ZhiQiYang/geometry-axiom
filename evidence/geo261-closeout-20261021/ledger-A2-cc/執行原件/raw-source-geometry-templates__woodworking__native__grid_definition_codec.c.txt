#include "grid_definition_codec.h"
#include <limits.h>
#include <string.h>

typedef struct {
    const unsigned char *bytes;
    size_t size,offset;
} WoodGridReader;
typedef struct {
    unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES];
    size_t size;
    bool ok;
} WoodGridWriter;

static bool wood_grid_codec_begin(const GeoDefinitionValue *value,const char *schema,
    WoodGridReader *reader)
{
    if(!value||!value->schema||strcmp(value->schema,schema)||!value->content||
       value->content_size>WOOD_GRID_CODEC_MAX_BYTES)return false;
    *reader=(WoodGridReader){value->content,value->content_size,0};return true;
}
static bool wood_grid_codec_u64(WoodGridReader *reader,uint64_t *out)
{
    if(reader->size-reader->offset<8)return false;
    uint64_t value=0;
    for(int i=0;i<8;++i)value=(value<<8)|reader->bytes[reader->offset++];
    *out=value;return true;
}
static bool wood_grid_codec_i64(WoodGridReader *reader,int64_t *out)
{
    uint64_t value;if(!wood_grid_codec_u64(reader,&value))return false;
    *out=value<=INT64_MAX?(int64_t)value:-1-(int64_t)(UINT64_MAX-value);return true;
}
static bool wood_grid_codec_u32(WoodGridReader *reader,uint32_t *out)
{
    uint64_t value;if(!wood_grid_codec_u64(reader,&value)||value>UINT32_MAX)return false;
    *out=(uint32_t)value;return true;
}
static bool wood_grid_codec_unsigned(WoodGridReader *reader,unsigned *out)
{
    uint64_t value;if(!wood_grid_codec_u64(reader,&value)||value>UINT_MAX)return false;
    *out=(unsigned)value;return true;
}
static bool wood_grid_codec_int(WoodGridReader *reader,int *out)
{
    int64_t value;if(!wood_grid_codec_i64(reader,&value)||value<INT_MIN||value>INT_MAX)return false;
    *out=(int)value;return true;
}
static bool wood_grid_codec_size(WoodGridReader *reader,size_t limit,size_t *out)
{
    uint64_t value;if(!wood_grid_codec_u64(reader,&value)||value>SIZE_MAX||value>limit)return false;
    *out=(size_t)value;return true;
}
static bool wood_grid_codec_bool(WoodGridReader *reader,bool *out)
{
    uint64_t value;if(!wood_grid_codec_u64(reader,&value)||value>1)return false;
    *out=value!=0;return true;
}
static bool wood_grid_codec_utf8(const unsigned char *text,size_t size)
{
    for(size_t i=0;i<size;){
        uint32_t value=text[i++],minimum;unsigned remaining;
        if(!value)return false;
        if(value<0x80)continue;
        if(value>=0xc2&&value<=0xdf){value&=0x1f;remaining=1;minimum=0x80;}
        else if(value>=0xe0&&value<=0xef){value&=0x0f;remaining=2;minimum=0x800;}
        else if(value>=0xf0&&value<=0xf4){value&=0x07;remaining=3;minimum=0x10000;}
        else return false;
        if(size-i<remaining)return false;
        while(remaining--){unsigned char byte=text[i++];if((byte&0xc0)!=0x80)return false;value=(value<<6)|(byte&0x3f);}
        if(value<minimum||value>0x10ffff||(value>=0xd800&&value<=0xdfff))return false;
    }
    return true;
}
static bool wood_grid_codec_text(WoodGridReader *reader,char *out,size_t capacity)
{
    size_t size;if(!capacity||!wood_grid_codec_size(reader,capacity-1,&size)||
       size>reader->size-reader->offset||!wood_grid_codec_utf8(reader->bytes+reader->offset,size))return false;
    memcpy(out,reader->bytes+reader->offset,size);out[size]=0;reader->offset+=size;return true;
}
static bool wood_grid_codec_axis(WoodGridReader *reader,const GeoGridAxisDef *prior,
    GeoGridAxisDef *out,bool direct_application,bool evaluated)
{
    GeoGridAxisDef axis={0};
    if(!wood_grid_codec_int(reader,&axis.source)||
       !wood_grid_codec_size(reader,GEO_GRID_COORDINATE_CAPACITY,&axis.count))return false;
    for(size_t i=0;i<axis.count;++i)if(!wood_grid_codec_i64(reader,&axis.coords[i]))return false;
    GeoCoord *values[]={&axis.start,&axis.step,&axis.body,&axis.gap,&axis.anchor,&axis.stagger};
    GeoCoord cache[6]={0};
    if(prior){cache[0]=prior->start;cache[1]=prior->step;cache[2]=prior->body;
        cache[3]=prior->gap;cache[4]=prior->anchor;cache[5]=prior->stagger;}
    bool masked[6];int64_t numbers[6];
    for(size_t i=0;i<6;++i){
        GeoParameterRef *parameter=&axis.parameters[i];bool bound;int64_t number;
        if(!wood_grid_codec_bool(reader,&parameter->set)||
           !wood_grid_codec_u32(reader,&parameter->parameter_id)||
           !wood_grid_codec_u32(reader,&parameter->field_id)||
           !wood_grid_codec_bool(reader,&bound)||!wood_grid_codec_i64(reader,&number))return false;
        if(bound&&(!direct_application||evaluated||(i!=2&&i!=3)))return false;
        masked[i]=!evaluated&&(parameter->set||bound);numbers[i]=number;
    }
    if(!wood_grid_codec_size(reader,SIZE_MAX,&axis.series_count)||
       !wood_grid_codec_bool(reader,&axis.anchor_explicit)||
       !wood_grid_codec_bool(reader,&axis.stagger_set)||
       !wood_grid_codec_bool(reader,&axis.card_length))return false;
    /* D64: a card-controlled step/body slot is an evaluated cache as well. */
    if(!evaluated&&axis.card_length)masked[axis.source==GEO_GRID_SOURCE_REPEAT?1:2]=true;
    for(size_t i=0;i<6;++i){
        int64_t number=numbers[i];
        if(masked[i]){
            if(number)return false;
            *values[i]=cache[i];
        }else *values[i]=number;
    }
    *out=axis;return true;
}
static bool wood_grid_codec_rule(WoodGridReader *reader,GeoGridRule *out)
{
    if(!wood_grid_codec_u32(reader,&out->key)||
       !wood_grid_codec_text(reader,out->name,sizeof out->name)||
       !wood_grid_codec_bool(reader,&out->all_cells))return false;
    for(int axis=0;axis<2;++axis)
        if(!wood_grid_codec_i64(reader,&out->cell[axis])||
           !wood_grid_codec_unsigned(reader,&out->divisions[axis]))return false;
    return true;
}
static bool wood_grid_codec_system(const GeoDefinitionValue *value,const char *schema,
    uint32_t expected_id,const GeoGridSystem *prior,GeoGridSystem *out,int *main_along,bool evaluated)
{
    WoodGridReader reader;GeoGridSystem system={0};int main;
    if(!out||!main_along||!wood_grid_codec_begin(value,schema,&reader)||
       !wood_grid_codec_u32(&reader,&system.id)||system.id!=expected_id||
       !wood_grid_codec_text(&reader,system.name,sizeof system.name)||
       !wood_grid_codec_int(&reader,&main))return false;
    for(int axis=0;axis<2;++axis)
        if(!wood_grid_codec_axis(&reader,prior?&prior->axis[axis]:NULL,
            &system.axis[axis],false,evaluated))return false;
    if(!wood_grid_codec_size(&reader,GEO_GRID_RULE_CAPACITY,&system.rule_count)||
       !wood_grid_codec_u32(&reader,&system.next_rule_key))return false;
    for(size_t i=0;i<system.rule_count;++i)
        if(!wood_grid_codec_rule(&reader,&system.rules[i]))return false;
    if(!wood_grid_codec_bool(&reader,&system.card_reference.set)||
       !wood_grid_codec_u32(&reader,&system.card_reference.parameter_id)||
       !wood_grid_codec_u32(&reader,&system.card_reference.fields[0])||
       !wood_grid_codec_u32(&reader,&system.card_reference.fields[1]))return false;
    if(reader.offset!=reader.size)return false;
    *out=system;*main_along=main;return true;
}
bool wood_grid_decode_system(const GeoDefinitionValue *value,uint32_t expected_id,
    const GeoGridSystem *prior,GeoGridSystem *out,int *main_along)
{return wood_grid_codec_system(value,"wood.grid.system/1",expected_id,prior,out,main_along,false);}
bool wood_grid_decode_system_value(const GeoDefinitionValue *value,uint32_t expected_id,
    GeoGridSystem *out,int *main_along)
{return wood_grid_codec_system(value,WOOD_GRID_SYSTEM_VALUE_SCHEMA,expected_id,NULL,out,main_along,true);}
bool wood_grid_decode_binding(const GeoDefinitionValue *value,uint32_t expected_id,GeoGridBinding *out)
{
    WoodGridReader reader;GeoGridBinding binding={0};
    if(!out||!wood_grid_codec_begin(value,"wood.grid.binding/1",&reader)||
       !wood_grid_codec_u32(&reader,&binding.id)||binding.id!=expected_id||
       !wood_grid_codec_u32(&reader,&binding.boundary_id)||
       !wood_grid_codec_u32(&reader,&binding.system_id)||
       !wood_grid_codec_u32(&reader,&binding.vertex_key))return false;
    for(int axis=0;axis<2;++axis)
        if(!wood_grid_codec_i64(&reader,&binding.cell[axis])||
           !wood_grid_codec_u32(&reader,&binding.anchor_num[axis])||
           !wood_grid_codec_u32(&reader,&binding.anchor_den[axis]))return false;
    if(reader.offset!=reader.size)return false;
    *out=binding;return true;
}
bool wood_grid_decode_rule(const GeoDefinitionValue *value,uint32_t expected_system_id,
    uint32_t expected_rule_key,GeoGridRule *out)
{
    WoodGridReader reader;GeoGridRule rule={0};uint32_t system_id;
    if(!out||!wood_grid_codec_begin(value,"wood.grid.rule/1",&reader)||
       !wood_grid_codec_u32(&reader,&system_id)||system_id!=expected_system_id||
       !wood_grid_codec_rule(&reader,&rule)||rule.key!=expected_rule_key||reader.offset!=reader.size)return false;
    *out=rule;return true;
}
static bool wood_grid_codec_application_prefix(WoodGridReader *reader,uint32_t expected_id,
    WoodGridApplication *application)
{
    if(!wood_grid_codec_u32(reader,&application->id)||application->id!=expected_id||
       !wood_grid_codec_u32(reader,&application->placement_id)||
       !wood_grid_codec_bool(reader,&application->from_system)||
       !wood_grid_codec_bool(reader,&application->from_binding)||
       !wood_grid_codec_bool(reader,&application->is_subgrid)||
       !wood_grid_codec_u32(reader,&application->binding_id)||
       !wood_grid_codec_u32(reader,&application->system_id)||
       !wood_grid_codec_u32(reader,&application->parent_id)||
       !wood_grid_codec_bool(reader,&application->lattice_cell))return false;
    for(int axis=0;axis<2;++axis){
        if(!wood_grid_codec_i64(reader,&application->system_origin[axis])||
           !wood_grid_codec_i64(reader,&application->lattice_cell_index[axis])||
           !wood_grid_codec_unsigned(reader,&application->divisions[axis]))return false;
        for(int j=0;j<2;++j)if(!wood_grid_codec_int(reader,&application->cell_ref[axis][j]))return false;
    }
    return true;
}
bool wood_grid_decode_application(const GeoDefinitionValue *value,uint32_t expected_id,
    const WoodGridApplication *prior,WoodGridApplication *out)
{
    WoodGridReader reader;WoodGridApplication application={0};
    if(prior)application=*prior;
    if(!out||!wood_grid_codec_begin(value,"wood.grid.application/1",&reader)||
       !wood_grid_codec_application_prefix(&reader,expected_id,&application))return false;
    if(!application.from_system&&!application.from_binding&&!application.is_subgrid){
        if(!wood_grid_codec_int(&reader,&application.main_along))return false;
        for(int axis=0;axis<2;++axis)
            if(!wood_grid_codec_axis(&reader,prior?&prior->axis[axis]:NULL,
                &application.axis[axis],true,false))return false;
    }
    if(reader.offset!=reader.size)return false;
    *out=application;return true;
}
bool wood_grid_decode_application_value(const GeoDefinitionValue *value,uint32_t expected_id,
    WoodGridApplication *out)
{
    WoodGridReader reader;WoodGridApplication application={0};
    if(!out||!wood_grid_codec_begin(value,WOOD_GRID_APPLICATION_VALUE_SCHEMA,&reader)||
       !wood_grid_codec_application_prefix(&reader,expected_id,&application)||
       !wood_grid_codec_int(&reader,&application.main_along))return false;
    for(int axis=0;axis<2;++axis)
        if(!wood_grid_codec_axis(&reader,NULL,&application.axis[axis],false,true))return false;
    for(int axis=0;axis<2;++axis)
        if(!wood_grid_codec_i64(&reader,&application.lattice_base[axis])||
           !wood_grid_codec_i64(&reader,&application.lattice_step[axis])||
           !wood_grid_codec_i64(&reader,&application.lattice_index[axis]))return false;
    if(reader.offset!=reader.size)return false;
    *out=application;return true;
}

static void wood_grid_codec_write_number(WoodGridWriter *writer,uint64_t value)
{
    if(!writer->ok||sizeof writer->bytes-writer->size<8){writer->ok=false;return;}
    for(int i=0;i<8;++i)writer->bytes[writer->size++]=(unsigned char)(value>>(56-8*i));
}
static void wood_grid_codec_write_text(WoodGridWriter *writer,const char *text,size_t capacity)
{
    size_t size=0;while(size<capacity&&text[size])++size;
    if(size==capacity||!wood_grid_codec_utf8((const unsigned char *)text,size)){writer->ok=false;return;}
    wood_grid_codec_write_number(writer,(uint64_t)size);
    if(!writer->ok||sizeof writer->bytes-writer->size<size){writer->ok=false;return;}
    memcpy(writer->bytes+writer->size,text,size);writer->size+=size;
}
static void wood_grid_codec_write_axis(WoodGridWriter *writer,const GeoGridAxisDef *axis)
{
    if(axis->count>GEO_GRID_COORDINATE_CAPACITY){writer->ok=false;return;}
    wood_grid_codec_write_number(writer,(uint64_t)axis->source);
    wood_grid_codec_write_number(writer,(uint64_t)axis->count);
    for(size_t i=0;i<axis->count;++i)wood_grid_codec_write_number(writer,(uint64_t)axis->coords[i]);
    const GeoCoord values[]={axis->start,axis->step,axis->body,axis->gap,axis->anchor,axis->stagger};
    for(size_t i=0;i<6;++i){
        const GeoParameterRef *parameter=&axis->parameters[i];
        wood_grid_codec_write_number(writer,parameter->set);
        wood_grid_codec_write_number(writer,parameter->parameter_id);
        wood_grid_codec_write_number(writer,parameter->field_id);
        wood_grid_codec_write_number(writer,0);
        wood_grid_codec_write_number(writer,(uint64_t)values[i]);
    }
    wood_grid_codec_write_number(writer,(uint64_t)axis->series_count);
    wood_grid_codec_write_number(writer,axis->anchor_explicit);
    wood_grid_codec_write_number(writer,axis->stagger_set);
    wood_grid_codec_write_number(writer,axis->card_length);
}
static void wood_grid_codec_write_rule(WoodGridWriter *writer,const GeoGridRule *rule)
{
    wood_grid_codec_write_number(writer,rule->key);
    wood_grid_codec_write_text(writer,rule->name,sizeof rule->name);
    wood_grid_codec_write_number(writer,rule->all_cells);
    for(int axis=0;axis<2;++axis){
        wood_grid_codec_write_number(writer,(uint64_t)rule->cell[axis]);
        wood_grid_codec_write_number(writer,rule->divisions[axis]);
    }
}
static bool wood_grid_codec_finish(const WoodGridWriter *writer,unsigned char *bytes,
    size_t capacity,size_t *size)
{
    if(!writer->ok||!bytes||!size||writer->size>capacity)return false;
    memcpy(bytes,writer->bytes,writer->size);*size=writer->size;return true;
}
bool wood_grid_encode_system_value(const GeoGridSystem *system,int main_along,
    unsigned char *bytes,size_t capacity,size_t *size)
{
    WoodGridWriter writer={.ok=true};
    if(!system||system->rule_count>GEO_GRID_RULE_CAPACITY)return false;
    wood_grid_codec_write_number(&writer,system->id);
    wood_grid_codec_write_text(&writer,system->name,sizeof system->name);
    wood_grid_codec_write_number(&writer,(uint64_t)main_along);
    for(int axis=0;axis<2;++axis)wood_grid_codec_write_axis(&writer,&system->axis[axis]);
    wood_grid_codec_write_number(&writer,(uint64_t)system->rule_count);
    wood_grid_codec_write_number(&writer,system->next_rule_key);
    for(size_t i=0;i<system->rule_count;++i)wood_grid_codec_write_rule(&writer,&system->rules[i]);
    wood_grid_codec_write_number(&writer,system->card_reference.set);
    wood_grid_codec_write_number(&writer,system->card_reference.parameter_id);
    wood_grid_codec_write_number(&writer,system->card_reference.fields[0]);
    wood_grid_codec_write_number(&writer,system->card_reference.fields[1]);
    return wood_grid_codec_finish(&writer,bytes,capacity,size);
}
bool wood_grid_encode_application_value(const WoodGridApplication *application,
    unsigned char *bytes,size_t capacity,size_t *size)
{
    WoodGridWriter writer={.ok=true};if(!application)return false;
    wood_grid_codec_write_number(&writer,application->id);
    wood_grid_codec_write_number(&writer,application->placement_id);
    wood_grid_codec_write_number(&writer,application->from_system);
    wood_grid_codec_write_number(&writer,application->from_binding);
    wood_grid_codec_write_number(&writer,application->is_subgrid);
    wood_grid_codec_write_number(&writer,application->binding_id);
    wood_grid_codec_write_number(&writer,application->system_id);
    wood_grid_codec_write_number(&writer,application->parent_id);
    wood_grid_codec_write_number(&writer,application->lattice_cell);
    for(int axis=0;axis<2;++axis){
        wood_grid_codec_write_number(&writer,(uint64_t)application->system_origin[axis]);
        wood_grid_codec_write_number(&writer,(uint64_t)application->lattice_cell_index[axis]);
        wood_grid_codec_write_number(&writer,application->divisions[axis]);
        for(int j=0;j<2;++j)wood_grid_codec_write_number(&writer,(uint64_t)application->cell_ref[axis][j]);
    }
    wood_grid_codec_write_number(&writer,(uint64_t)application->main_along);
    for(int axis=0;axis<2;++axis)wood_grid_codec_write_axis(&writer,&application->axis[axis]);
    for(int axis=0;axis<2;++axis){
        wood_grid_codec_write_number(&writer,(uint64_t)application->lattice_base[axis]);
        wood_grid_codec_write_number(&writer,(uint64_t)application->lattice_step[axis]);
        wood_grid_codec_write_number(&writer,(uint64_t)application->lattice_index[axis]);
    }
    return wood_grid_codec_finish(&writer,bytes,capacity,size);
}
