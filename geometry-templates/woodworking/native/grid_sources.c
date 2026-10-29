#include "grid_sources.h"
#include "grid_definition_codec.h"
#include "engineering_sources.h"
#ifndef GEO_KERNEL_REGION_KEY_SOURCES_H
#include "region_key_sources.h"
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct WoodGridSourceResult {
    WoodGridSourceKey key;struct WoodGridSourceResult *next;
    unsigned char *definition;size_t definition_size;
    WoodGridApplication seed,cache;size_t cache_attempts;
    WoodGridRuleTarget target;
    GeoGridSystem target_source;GeoGridRule target_rule;
    GeoCoord coordinate,seed_coordinate;size_t total,query_attempts;GeoRect2 scope;
    GeoPoint2 points[4];GeoRegionView region;char error[1024];
} WoodGridSourceResult;
struct WoodGridSources {
    GeoEvalContext *graph;WoodGridSourceTokens tokens;
    WoodGridContext base,context;WoodGridEvaluation hooks;
    WoodGridState evaluated;
    GeoGridStore *evaluated_sources;
    WoodGridSourceResult *results;
};
static void wood_grid_key_u32(unsigned char *p,uint32_t n)
{for(int i=0;i<4;++i)p[i]=(unsigned char)(n>>(24-8*i));}
static uint32_t wood_grid_key_read32(const unsigned char *p)
{uint32_t n=0;for(int i=0;i<4;++i)n=(n<<8)|p[i];return n;}
static void wood_grid_key_u64(unsigned char *p,uint64_t n)
{for(int i=0;i<8;++i)p[i]=(unsigned char)(n>>(56-8*i));}
static uint64_t wood_grid_key_read64(const unsigned char *p)
{uint64_t n=0;for(int i=0;i<8;++i)n=(n<<8)|p[i];return n;}
static int64_t wood_grid_key_signed64(const unsigned char *p)
{uint64_t n=wood_grid_key_read64(p);return n<=INT64_MAX?(int64_t)n:-1-(int64_t)(UINT64_MAX-n);}
static int wood_grid_key_axis(const unsigned char *p)
{uint32_t n=wood_grid_key_read32(p);return n<=INT32_MAX?(int)n:-1-(int)(UINT32_MAX-n);}
GeoSourceRef wood_grid_source_ref(GeoProviderToken token,WoodGridSourceKind kind,uint32_t id,WoodGridSourceKey *key)
{memset(key,0,sizeof *key);key->bytes[0]=(unsigned char)kind;wood_grid_key_u32(key->bytes+1,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
GeoSourceRef wood_grid_dimension_source_ref(GeoProviderToken token,uint32_t id,int axis,int field,WoodGridSourceKey *key)
{GeoSourceRef ref=wood_grid_source_ref(token,field?WOOD_GRID_SOURCE_GAP:WOOD_GRID_SOURCE_PANEL,id,key);wood_grid_key_u32(key->bytes+17,(uint32_t)axis);return ref;}
GeoSourceRef wood_grid_line_source_ref(GeoProviderToken token,uint32_t id,uint32_t pid,int axis,int64_t index,bool anchor,bool has_band,int64_t band,WoodGridSourceKey *key)
{GeoSourceRef ref=wood_grid_source_ref(token,WOOD_GRID_SOURCE_LINE,id,key);wood_grid_key_u32(key->bytes+5,pid);wood_grid_key_u32(key->bytes+17,(uint32_t)axis);key->bytes[21]=(unsigned char)((anchor?2:0)|(has_band?1:0));wood_grid_key_u64(key->bytes+22,(uint64_t)index);wood_grid_key_u64(key->bytes+30,(uint64_t)band);return ref;}
GeoSourceRef wood_grid_rule_source_ref(GeoProviderToken token,const GeoGridRuleLineRef *rule,uint32_t pid,WoodGridSourceKey *key)
{GeoSourceRef ref=wood_grid_source_ref(token,WOOD_GRID_SOURCE_RULE_LINE,rule->grid_id,key);wood_grid_key_u32(key->bytes+5,pid);wood_grid_key_u32(key->bytes+9,rule->system_id);wood_grid_key_u32(key->bytes+13,rule->rule_key);wood_grid_key_u32(key->bytes+17,(uint32_t)rule->axis);wood_grid_key_u64(key->bytes+38,(uint64_t)rule->cell[0]);wood_grid_key_u64(key->bytes+46,(uint64_t)rule->cell[1]);wood_grid_key_u32(key->bytes+54,rule->inner_index);return ref;}
static GeoSourceRef wood_grid_rule_cell_ref(GeoProviderToken token,uint32_t id,uint32_t rule,const int64_t cell[2],WoodGridSourceKey *key)
{GeoSourceRef ref=wood_grid_source_ref(token,WOOD_GRID_SOURCE_RULE_CELL,id,key);wood_grid_key_u32(key->bytes+13,rule);wood_grid_key_u64(key->bytes+38,(uint64_t)cell[0]);wood_grid_key_u64(key->bytes+46,(uint64_t)cell[1]);return ref;}
GeoSourceRef wood_grid_rule_definition_source_ref(GeoProviderToken token,uint32_t system,uint32_t rule,WoodGridSourceKey *key)
{GeoSourceRef ref=wood_grid_source_ref(token,WOOD_GRID_SOURCE_RULE_DEFINITION,system,key);wood_grid_key_u32(key->bytes+13,rule);return ref;}
bool wood_grid_source_decode(const GeoSourceRef *ref,WoodGridSourceKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=64||!kind||!id)return false;
    const unsigned char *p=ref->key;if(p[0]<WOOD_GRID_SOURCE_SYSTEM_DEFINITION||p[0]>WOOD_GRID_SOURCE_RULE_DEFINITION)return false;
    WoodGridSourceKind k=(WoodGridSourceKind)p[0];uint32_t n=wood_grid_key_read32(p+1);WoodGridSourceKey canonical;
    if(k==WOOD_GRID_SOURCE_LINE){if(p[21]>3)return false;wood_grid_line_source_ref(ref->provider,n,wood_grid_key_read32(p+5),wood_grid_key_axis(p+17),wood_grid_key_signed64(p+22),(p[21]&2)!=0,(p[21]&1)!=0,wood_grid_key_signed64(p+30),&canonical);}
    else if(k==WOOD_GRID_SOURCE_RULE_LINE){GeoGridRuleLineRef rule={n,wood_grid_key_read32(p+9),wood_grid_key_read32(p+13),{wood_grid_key_signed64(p+38),wood_grid_key_signed64(p+46)},wood_grid_key_axis(p+17),wood_grid_key_read32(p+54)};wood_grid_rule_source_ref(ref->provider,&rule,wood_grid_key_read32(p+5),&canonical);}
    else if(k==WOOD_GRID_SOURCE_RULE_CELL){int64_t cell[]={wood_grid_key_signed64(p+38),wood_grid_key_signed64(p+46)};wood_grid_rule_cell_ref(ref->provider,n,wood_grid_key_read32(p+13),cell,&canonical);}
    else if(k==WOOD_GRID_SOURCE_RULE_DEFINITION)wood_grid_rule_definition_source_ref(ref->provider,n,wood_grid_key_read32(p+13),&canonical);
    else if(k==WOOD_GRID_SOURCE_PANEL||k==WOOD_GRID_SOURCE_GAP)wood_grid_dimension_source_ref(ref->provider,n,wood_grid_key_axis(p+17),k==WOOD_GRID_SOURCE_GAP,&canonical);
    else wood_grid_source_ref(ref->provider,k,n,&canonical);
    if(memcmp(p,canonical.bytes,64))return false;*kind=k;*id=n;return true;
}
static WoodGridSourceResult *wood_grid_result(WoodGridSources *s,const GeoSourceRef *ref)
{
    for(WoodGridSourceResult *r=s->results;r;r=r->next)if(!memcmp(r->key.bytes,ref->key,64))return r;
    WoodGridSourceResult *r=calloc(1,sizeof *r);if(!r)return NULL;memcpy(r->key.bytes,ref->key,64);r->next=s->results;s->results=r;return r;
}
static bool wood_grid_source_get(WoodGridSources *s,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out,char *error,size_t cap)
{
    GeoSourceStatus status=geo_eval_source(s->graph,ref,relation,out);
    if(status==GEO_SOURCE_OK)return true;
    WoodGridSourceResult *r=wood_grid_result(s,&ref);
    if(error&&cap){if(r&&r->error[0])snprintf(error,cap,"%s",r->error);
        else if(status==GEO_SOURCE_MEMORY)snprintf(error,cap,"I37: grid source graph capacity exceeded");
        else if(status==GEO_SOURCE_CYCLE)snprintf(error,cap,"R44: cyclic grid source");}
    return false;
}
static bool wood_grid_root_get(WoodGridSources *s,WoodGridSourceKind kind,uint32_t id,GeoDependencyKind relation,GeoSourceValue *out,char *error,size_t cap)
{WoodGridSourceKey key;return wood_grid_source_get(s,wood_grid_source_ref(s->tokens.grid,kind,id,&key),relation,out,error,cap);}

/* Canonical authored definitions exclude evaluated numeric cache fields. */
typedef struct {unsigned char bytes[16384];size_t size;bool ok;} WoodGridDefinition;
static void wood_grid_def_number(WoodGridDefinition *d,uint64_t value)
{if(!d->ok||sizeof d->bytes-d->size<8){d->ok=false;return;}wood_grid_key_u64(d->bytes+d->size,value);d->size+=8;}
static void wood_grid_def_text(WoodGridDefinition *d,const char *value,size_t capacity)
{size_t n=0;while(n<capacity&&value[n])++n;wood_grid_def_number(d,n);if(!d->ok||sizeof d->bytes-d->size<n){d->ok=false;return;}memcpy(d->bytes+d->size,value,n);d->size+=n;}
static void wood_grid_def_axis(WoodGridDefinition *d,const GeoGridAxisDef *a,bool body_bound,bool gap_bound)
{
    wood_grid_def_number(d,(uint64_t)a->source);wood_grid_def_number(d,a->count);
    if(a->count>GEO_GRID_COORDINATE_CAPACITY){d->ok=false;return;}
    for(size_t i=0;i<a->count;++i)wood_grid_def_number(d,(uint64_t)a->coords[i]);
    const GeoCoord values[]={a->start,a->step,a->body,a->gap,a->anchor,a->stagger};
    size_t card=a->card_length?(a->source==GEO_GRID_SOURCE_REPEAT?1:2):6;
    for(size_t i=0;i<6;++i){GeoParameterRef p=a->parameters[i];wood_grid_def_number(d,p.set);wood_grid_def_number(d,p.parameter_id);wood_grid_def_number(d,p.field_id);
        bool bound=(i==2&&body_bound)||(i==3&&gap_bound);wood_grid_def_number(d,bound);wood_grid_def_number(d,p.set||bound||i==card?0:(uint64_t)values[i]);}
    wood_grid_def_number(d,a->series_count);wood_grid_def_number(d,a->anchor_explicit);wood_grid_def_number(d,a->stagger_set);wood_grid_def_number(d,a->card_length);
}
static bool wood_grid_definition_depend(WoodGridSources *s,WoodGridSourceKind kind,uint32_t id)
{WoodGridSourceKey key;return geo_eval_depend(s->graph,wood_grid_source_ref(s->tokens.grid,kind,id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK;}
static bool wood_grid_parameter_definitions(WoodGridSources *s,const GeoGridAxisDef *axis)
{
    if(!s->tokens.parameter)return true;
    for(size_t i=0;i<6;++i)if(axis->parameters[i].set){uint32_t key[]={axis->parameters[i].parameter_id,axis->parameters[i].field_id};
        if(geo_eval_depend(s->graph,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;}
    return true;
}
/* D64: both mapped card fields are definition inputs of the grid system. */
static bool wood_grid_card_definitions(WoodGridSources *s,const GeoGridCardReference *card)
{
    if(!s->tokens.parameter||!card->set)return true;
    for(int a=0;a<2;++a){uint32_t key[]={card->parameter_id,card->fields[a]};
        if(geo_eval_depend(s->graph,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;}
    return true;
}
static bool wood_grid_binding_definition_depend(WoodGridSources *s,uint32_t id,int axis,int field)
{
    if(!s->tokens.engineering_binding)return true;
    EngTarget target={0,id,axis,field};const EngBinding *binding=wood_eng_binding(&s->context.engineering,&target);
    if(!binding)return true;WoodEngineeringBindingSourceKey key;
    return geo_eval_depend(s->graph,wood_engineering_binding_source_ref(s->tokens.engineering_binding,
        WOOD_BINDING_SOURCE_DEFINITION,binding,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK;
}
static bool wood_grid_definition(WoodGridSources *s,WoodGridSourceKind kind,uint32_t id,WoodGridSourceResult *r,GeoSourceValue *out)
{
    WoodGridDefinition d={.ok=true};const char *schema=NULL;wood_grid_def_number(&d,id);
    if(kind==WOOD_GRID_SOURCE_SYSTEM_DEFINITION){
        const GeoGridSystem *g=geo_grid_systems_find(s->base.sources,id);if(!g)return false;schema="wood.grid.system/1";
        wood_grid_def_text(&d,g->name,sizeof g->name);wood_grid_def_number(&d,(uint64_t)wood_grid_source_main_along(s->base.state,id));
        for(int a=0;a<2;++a){wood_grid_def_axis(&d,&g->axis[a],false,false);if(!wood_grid_parameter_definitions(s,&g->axis[a]))return false;}
        wood_grid_def_number(&d,g->rule_count);wood_grid_def_number(&d,g->next_rule_key);if(g->rule_count>GEO_GRID_RULE_CAPACITY)return false;
        for(size_t i=0;i<g->rule_count;++i){const GeoGridRule *v=&g->rules[i];wood_grid_def_number(&d,v->key);wood_grid_def_text(&d,v->name,sizeof v->name);wood_grid_def_number(&d,v->all_cells);for(int a=0;a<2;++a){wood_grid_def_number(&d,(uint64_t)v->cell[a]);wood_grid_def_number(&d,v->divisions[a]);}}
        wood_grid_def_number(&d,g->card_reference.set);wood_grid_def_number(&d,g->card_reference.parameter_id);
        wood_grid_def_number(&d,g->card_reference.fields[0]);wood_grid_def_number(&d,g->card_reference.fields[1]);
        if(!wood_grid_card_definitions(s,&g->card_reference))return false;
    }else if(kind==WOOD_GRID_SOURCE_RULE_DEFINITION){
        GeoSourceValue parent;GeoGridSystem decoded;int main;
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&parent,NULL,0)||
            parent.kind!=GEO_SOURCE_DEFINITION||!wood_grid_decode_system(&parent.as.definition,id,NULL,&decoded,&main))return false;
        const GeoGridRule *rule=geo_grid_rule_find(&decoded,wood_grid_key_read32(r->key.bytes+13));if(!rule)return false;
        schema="wood.grid.rule/1";wood_grid_def_number(&d,rule->key);wood_grid_def_text(&d,rule->name,sizeof rule->name);wood_grid_def_number(&d,rule->all_cells);
        for(int a=0;a<2;++a){wood_grid_def_number(&d,(uint64_t)rule->cell[a]);wood_grid_def_number(&d,rule->divisions[a]);}
    }else if(kind==WOOD_GRID_SOURCE_BINDING_DEFINITION){
        const GeoGridBinding *b=geo_grid_bindings_find(s->base.sources,id);if(!b)return false;schema="wood.grid.binding/1";
        wood_grid_def_number(&d,b->boundary_id);wood_grid_def_number(&d,b->system_id);wood_grid_def_number(&d,b->vertex_key);
        for(int a=0;a<2;++a){wood_grid_def_number(&d,(uint64_t)b->cell[a]);wood_grid_def_number(&d,b->anchor_num[a]);wood_grid_def_number(&d,b->anchor_den[a]);}
        if(!wood_grid_definition_depend(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,b->system_id))return false;
        if(s->tokens.region_keys){GeoRegionKeySourceKey key;
            if(geo_eval_depend(s->graph,geo_region_key_source_ref(s->tokens.region_keys,GEO_REGION_KEY_SOURCE_LEDGER,b->boundary_id,0,0,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;}
    }else{
        const WoodGridApplication *g=wood_grid_find(s->base.state,id);if(!g)return false;schema="wood.grid.application/1";
        wood_grid_def_number(&d,g->placement_id);wood_grid_def_number(&d,g->from_system);wood_grid_def_number(&d,g->from_binding);wood_grid_def_number(&d,g->is_subgrid);
        wood_grid_def_number(&d,g->binding_id);wood_grid_def_number(&d,g->system_id);wood_grid_def_number(&d,g->parent_id);wood_grid_def_number(&d,g->lattice_cell);
        for(int a=0;a<2;++a){wood_grid_def_number(&d,(uint64_t)g->system_origin[a]);wood_grid_def_number(&d,(uint64_t)g->lattice_cell_index[a]);wood_grid_def_number(&d,g->divisions[a]);for(int j=0;j<2;++j)wood_grid_def_number(&d,(uint64_t)g->cell_ref[a][j]);}
        if(!g->from_system&&!g->from_binding&&!g->is_subgrid){wood_grid_def_number(&d,(uint64_t)g->main_along);
            for(int a=0;a<2;++a){EngTarget body={0,id,a,0},gap={0,id,a,1};wood_grid_def_axis(&d,&g->axis[a],wood_eng_binding(&s->context.engineering,&body)!=NULL,wood_eng_binding(&s->context.engineering,&gap)!=NULL);
                if(!wood_grid_parameter_definitions(s,&g->axis[a])||!wood_grid_binding_definition_depend(s,id,a,0)||!wood_grid_binding_definition_depend(s,id,a,1))return false;}}
        if(g->is_subgrid&&!wood_grid_definition_depend(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,g->parent_id))return false;
        if(g->from_system&&!wood_grid_definition_depend(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,g->system_id))return false;
        if(g->from_binding&&!wood_grid_definition_depend(s,WOOD_GRID_SOURCE_BINDING_DEFINITION,g->binding_id))return false;
    }
    if(!d.ok)return false;unsigned char *content=realloc(r->definition,d.size);if(!content)return false;r->definition=content;r->definition_size=d.size;memcpy(content,d.bytes,d.size);
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,content,d.size};return true;
}
static bool wood_grid_source_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodGridSources *s=user;WoodGridSourceKind kind;uint32_t id;
    if(ref->provider!=s->tokens.grid||!wood_grid_source_decode(ref,&kind,&id))return false;
    GeoSourceDescriptor d={.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};const unsigned char *key=ref->key;
    if(kind==WOOD_GRID_SOURCE_PANEL||kind==WOOD_GRID_SOURCE_GAP){d.kind=GEO_SOURCE_QUANTITY;d.unit=GEO_UNIT_LENGTH;}
    else if(kind==WOOD_GRID_SOURCE_CELL||kind==WOOD_GRID_SOURCE_RULE_CELL){d.kind=GEO_SOURCE_REGION_SET;d.unit=GEO_UNIT_LENGTH;}
    else if(kind==WOOD_GRID_SOURCE_LINE||kind==WOOD_GRID_SOURCE_RULE_LINE){int axis=wood_grid_key_axis(key+17);d.kind=GEO_SOURCE_AXIS_POSITION;d.unit=GEO_UNIT_LENGTH;d.context=(GeoSourceContext){true,wood_grid_key_read32(key+5),axis>=0&&axis<2?axis:-1};}
    *out=d;return true;
}
static bool wood_grid_coordinate_source(void *user,GeoParameterRef ref,GeoCoord *out)
{
    WoodGridSources *s=user;GeoCoord checked=*out;if(!s->base.coordinate)return false;
    bool accepted=s->base.coordinate(s->base.user,ref,&checked);*out=checked;if(!accepted)return false;
    if(!ref.set||!s->tokens.parameter){*out=checked;return true;}
    uint32_t key[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    if(geo_eval_source(s->graph,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den<=0||value.as.quantity.num%value.as.quantity.den||!geo_coord_in_range(value.as.quantity.num/value.as.quantity.den))return false;
    *out=value.as.quantity.num/value.as.quantity.den;return true;
}
static bool wood_grid_host_source(void *user,uint32_t id,WoodGridHost *out)
{WoodGridSources *s=user;return s->base.host&&s->base.host(s->base.user,id,out);}
static bool wood_grid_vertex_source(void *user,uint32_t id,uint32_t key,GeoPoint2 *out)
{WoodGridSources *s=user;return s->base.vertex&&s->base.vertex(s->base.user,id,key,out);}
static bool wood_grid_reference_source(void *user,size_t i,WoodGridReference *out)
{WoodGridSources *s=user;return s->base.reference&&s->base.reference(s->base.user,i,out);}
static bool wood_grid_prepare_application(WoodGridSources *,uint32_t,char *,size_t);
static void wood_grid_scope_value(WoodGridSourceResult *r,GeoSourceValue *out)
{GeoRect2 q=r->scope;r->points[0]=(GeoPoint2){q.min_u,q.min_v};r->points[1]=(GeoPoint2){q.max_u,q.min_v};r->points[2]=(GeoPoint2){q.max_u,q.max_v};r->points[3]=(GeoPoint2){q.min_u,q.max_v};r->region=(GeoRegionView){.outline={r->points,4}};out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&r->region,1};}
static bool wood_grid_scope_read(const GeoSourceValue *value,GeoRect2 *out)
{
    if(value->kind!=GEO_SOURCE_REGION_SET||value->as.regions.count!=1)return false;const GeoRegionView *r=value->as.regions.regions;
    if(!r||r->hole_count||r->outline.count!=4||!r->outline.v)return false;const GeoPoint2 *p=r->outline.v;
    if(p[0].u!=p[3].u||p[1].u!=p[2].u||p[0].v!=p[1].v||p[2].v!=p[3].v||p[0].u>=p[1].u||p[0].v>=p[2].v)return false;
    *out=(GeoRect2){p[0].u,p[0].v,p[2].u,p[2].v};return true;
}
static bool wood_grid_cell_resolve(void *user,const WoodGridApplication *g,const WoodGridHost *host,GeoRect2 *out,char *error,size_t cap)
{
    WoodGridSources *s=user;if(!g||!host||g->placement_id!=host->id||wood_grid_find(s->context.state,g->id)!=g)return wood_grid_cell_bounds(s->context.state->items,s->context.state->count,g,host,out,error,cap);
    return wood_grid_sources_cell(s,g->id,out,error,cap);
}
/* Policies run on candidate-owned decoded shadows. Only evaluated cache slots
 * are copied back; authored definitions remain in the original document. */
static bool wood_grid_value_bytes(WoodGridSourceResult *r,const unsigned char *bytes,size_t size,const char *schema,GeoSourceValue *out)
{
    unsigned char *copy=realloc(r->definition,size);if(!copy)return false;
    r->definition=copy;r->definition_size=size;memcpy(copy,bytes,size);
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,copy,size};return true;
}
static bool wood_grid_system_value(WoodGridSources *s,uint32_t id,WoodGridSourceResult *r,GeoSourceValue *out)
{
    unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES];size_t size;
    const GeoGridSystem *system=geo_grid_systems_find(s->context.sources,id);
    return system&&wood_grid_encode_system_value(system,wood_grid_source_main_along(s->context.state,id),bytes,sizeof bytes,&size)&&
        wood_grid_value_bytes(r,bytes,size,WOOD_GRID_SYSTEM_VALUE_SCHEMA,out);
}
static bool wood_grid_application_value(const WoodGridApplication *g,WoodGridSourceResult *r,GeoSourceValue *out)
{
    unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES];size_t size;
    return wood_grid_encode_application_value(g,bytes,sizeof bytes,&size)&&wood_grid_value_bytes(r,bytes,size,WOOD_GRID_APPLICATION_VALUE_SCHEMA,out);
}
static bool wood_grid_install_system(WoodGridSources *s,uint32_t id,const GeoSourceValue *value,bool evaluated)
{
    GeoGridSystem system;int main;
    if(value->kind!=GEO_SOURCE_DEFINITION)return false;
    bool ok=evaluated?wood_grid_decode_system_value(&value->as.definition,id,&system,&main):
        wood_grid_decode_system(&value->as.definition,id,geo_grid_systems_find(s->context.sources,id),&system,&main);
    return ok&&wood_grid_source_put(&s->context,&system,main);
}
static bool wood_grid_install_binding(WoodGridSources *s,uint32_t id,GeoGridBinding *out,char *error,size_t cap)
{
    GeoSourceValue value;GeoGridBinding binding;
    if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_BINDING_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap)||
       value.kind!=GEO_SOURCE_DEFINITION||!wood_grid_decode_binding(&value.as.definition,id,&binding)||!geo_grid_bindings_put(s->context.sources,&binding))return false;
    if(out)*out=binding;return true;
}
bool wood_grid_sources_definition(WoodGridSources *s,uint32_t id,WoodGridApplication *out)
{
    if(!s||!out)return false;GeoSourceValue value;
    return wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,NULL,0)&&
        value.kind==GEO_SOURCE_DEFINITION&&wood_grid_decode_application(&value.as.definition,id,wood_grid_find(s->base.state,id),out);
}
static bool wood_grid_install_application(WoodGridSources *s,uint32_t id,const GeoSourceValue *value,bool evaluated)
{
    WoodGridApplication application;
    if(value->kind!=GEO_SOURCE_DEFINITION)return false;
    bool ok=evaluated?wood_grid_decode_application_value(&value->as.definition,id,&application):
        wood_grid_decode_application(&value->as.definition,id,wood_grid_find(s->context.state,id),&application);
    return ok&&wood_grid_stage(s->context.state,&application);
}
static void wood_grid_publish_system_cache(WoodGridSources *s,uint32_t id)
{
    const GeoGridSystem *raw=geo_grid_systems_find(s->base.sources,id),*computed=geo_grid_systems_find(s->context.sources,id);
    if(!raw||!computed)return;GeoGridSystem next=*raw;
    for(int axis=0;axis<2;++axis){GeoGridAxisDef *to=&next.axis[axis];const GeoGridAxisDef *from=&computed->axis[axis];
        GeoCoord *slots[]={&to->start,&to->step,&to->body,&to->gap,&to->anchor,&to->stagger};
        const GeoCoord values[]={from->start,from->step,from->body,from->gap,from->anchor,from->stagger};
        int card=to->card_length?(to->source==GEO_GRID_SOURCE_REPEAT?1:2):6;
        for(int field=0;field<6;++field)if(to->parameters[field].set||field==card)*slots[field]=values[field];}
    (void)geo_grid_systems_put(s->base.sources,&next);
}
static void wood_grid_publish_application_cache(WoodGridSources *s,const WoodGridApplication *computed)
{
    WoodGridApplication *raw=wood_grid_find_mut(s->base.state,computed->id);if(!raw)return;
    if(raw->from_binding||raw->from_system){raw->main_along=computed->main_along;
        for(int a=0;a<2;++a){raw->axis[a]=computed->axis[a];raw->lattice_base[a]=computed->lattice_base[a];raw->lattice_step[a]=computed->lattice_step[a];raw->lattice_index[a]=computed->lattice_index[a];}}
    else if(!raw->is_subgrid)for(int a=0;a<2;++a)if(raw->axis[a].source==GEO_GRID_SOURCE_BODY_GAP){
        EngTarget body={0,raw->id,a,0},gap={0,raw->id,a,1};
        if(wood_eng_binding(&s->context.engineering,&body))raw->axis[a].body=computed->axis[a].body;
        if(wood_eng_binding(&s->context.engineering,&gap))raw->axis[a].gap=computed->axis[a].gap;}
}
static bool wood_grid_prepare_application(WoodGridSources *s,uint32_t id,char *err,size_t cap)
{
    GeoSourceValue value;
    if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value,err,cap)||!wood_grid_install_application(s,id,&value,true))return false;
    const WoodGridApplication *g=wood_grid_find(s->context.state,id);
    if(g->is_subgrid){uint32_t parent=g->parent_id;
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION,parent,GEO_DEPENDENCY_VALUE_REQUIRED,&value,err,cap)||!wood_grid_install_application(s,parent,&value,true))return false;}
    return true;
}
static bool wood_grid_source_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodGridSources *s=user;WoodGridSourceKind kind;uint32_t id;
    if(graph!=s->graph||ref->provider!=s->tokens.grid||!wood_grid_source_decode(ref,&kind,&id))return false;
    WoodGridSourceResult *r=wood_grid_result(s,ref);if(!r)return false;r->error[0]=0;GeoSourceValue definition;
    if(kind==WOOD_GRID_SOURCE_SYSTEM_DEFINITION||kind==WOOD_GRID_SOURCE_BINDING_DEFINITION||kind==WOOD_GRID_SOURCE_APPLICATION_DEFINITION||kind==WOOD_GRID_SOURCE_RULE_DEFINITION)return wood_grid_definition(s,kind,id,r,out);
    if(kind==WOOD_GRID_SOURCE_SYSTEM){
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition,r->error,sizeof r->error)||!wood_grid_install_system(s,id,&definition,false))return false;
        bool ok=wood_grid_system_evaluate_direct(&s->context,id,r->error,sizeof r->error);wood_grid_publish_system_cache(s,id);
        return ok&&wood_grid_system_value(s,id,r,out);
    }
    if(kind==WOOD_GRID_SOURCE_BINDING){
        GeoGridBinding binding;if(!wood_grid_install_binding(s,id,&binding,r->error,sizeof r->error))return false;
        GeoSourceValue system;if(geo_grid_systems_find(s->context.sources,binding.system_id)&&
            (!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM,binding.system_id,GEO_DEPENDENCY_VALUE_REQUIRED,&system,r->error,sizeof r->error)||!wood_grid_install_system(s,binding.system_id,&system,true)))return false;
        r->cache=r->seed;++r->cache_attempts;if(!wood_grid_binding_cache_direct(&s->context,&binding,&r->cache,r->error,sizeof r->error))return false;
        WoodGridApplication value=r->cache;value.id=id;return wood_grid_application_value(&value,r,out);
    }
    const unsigned char *key=ref->key;int axis=wood_grid_key_axis(key+17);
    WoodGridApplication *g=wood_grid_find_mut(s->context.state,id);
    if(kind==WOOD_GRID_SOURCE_APPLICATION){
        if(!g||!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition,r->error,sizeof r->error)||!wood_grid_install_application(s,id,&definition,false))return false;
        GeoSourceValue source;if(g->from_system&&geo_grid_systems_find(s->context.sources,g->system_id)&&
            (!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM,g->system_id,GEO_DEPENDENCY_VALUE_REQUIRED,&source,r->error,sizeof r->error)||!wood_grid_install_system(s,g->system_id,&source,true)))return false;
        if(g->from_binding&&geo_grid_bindings_find(s->context.sources,g->binding_id)&&!wood_grid_install_binding(s,g->binding_id,NULL,r->error,sizeof r->error))return false;
        bool ok=wood_grid_application_evaluate_direct(&s->context,g,r->error,sizeof r->error);wood_grid_publish_application_cache(s,g);
        return ok&&wood_grid_application_value(g,r,out);
    }
    if(kind==WOOD_GRID_SOURCE_PANEL||kind==WOOD_GRID_SOURCE_GAP){
        /* A dimension read must not overwrite sibling returned quantities
         * already consumed by an active APPLICATION evaluation. */
        WoodGridApplication application;
        if(!g||axis<0||axis>1||!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition,r->error,sizeof r->error)||
           definition.kind!=GEO_SOURCE_DEFINITION||!wood_grid_decode_application(&definition.as.definition,id,g,&application))return false;
        if(application.from_system||application.from_binding){
            if(!wood_grid_prepare_application(s,id,r->error,sizeof r->error))return false;
            application=*wood_grid_find(s->context.state,id);
        }
        GeoCoord value;if(!wood_grid_application_dimension_direct(&s->context,&application,axis,kind==WOOD_GRID_SOURCE_GAP,&value,r->error,sizeof r->error))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    if(kind==WOOD_GRID_SOURCE_RULE_CELL){
        if(g&&(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition,r->error,sizeof r->error)||!wood_grid_install_application(s,id,&definition,false)))return false;
        if(g&&g->from_binding&&geo_grid_bindings_find(s->context.sources,g->binding_id)&&!wood_grid_install_binding(s,g->binding_id,NULL,r->error,sizeof r->error))return false;
        int64_t cell[]={wood_grid_key_signed64(key+38),wood_grid_key_signed64(key+46)};
        if(!wood_grid_rule_cell_direct(&s->context,"grid",id,wood_grid_key_read32(key+13),cell,&r->target,r->error,sizeof r->error))return false;
        /* A memoized cell owns the policy metadata that produced its region.
         * Later SYSTEM reads may reinstall a different decoded shadow. */
        r->target_source=*r->target.source;r->target_rule=*r->target.rule;
        r->target.source=&r->target_source;r->target.rule=&r->target_rule;
        r->scope=r->target.bounds;wood_grid_scope_value(r,out);return true;
    }
    if(kind==WOOD_GRID_SOURCE_RULE_LINE){
        /* The direct rule policy selects its source and checks it in the same
         * order. Its binding-cache hook consumes the evaluated K system. */
        if(g&&(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition,r->error,sizeof r->error)||!wood_grid_install_application(s,id,&definition,false)))return false;
        if(g&&g->from_binding&&geo_grid_bindings_find(s->context.sources,g->binding_id)&&!wood_grid_install_binding(s,g->binding_id,NULL,r->error,sizeof r->error))return false;
        GeoGridRuleLineRef rule={id,wood_grid_key_read32(key+9),wood_grid_key_read32(key+13),{wood_grid_key_signed64(key+38),wood_grid_key_signed64(key+46)},axis,wood_grid_key_read32(key+54)};uint32_t pid=wood_grid_key_read32(key+5);
        if(!wood_grid_rule_line_direct(&s->context,&rule,pid,&r->coordinate,&r->scope,r->error,sizeof r->error))return false;
        out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){r->coordinate,{true,pid,axis}};return true;
    }
    if(!g||!wood_grid_prepare_application(s,id,r->error,sizeof r->error))return false;
    WoodGridHost host;uint32_t pid=kind==WOOD_GRID_SOURCE_LINE?wood_grid_key_read32(key+5):g->placement_id;
    if(!s->context.host(s->context.user,pid,&host))return false;
    if(kind==WOOD_GRID_SOURCE_CELL){
        if(!wood_grid_cell_bounds(s->context.state->items,s->context.state->count,g,&host,&r->scope,r->error,sizeof r->error))return false;wood_grid_scope_value(r,out);return true;
    }
    if(kind==WOOD_GRID_SOURCE_LINE){
        bool anchor=(key[21]&2)!=0,has_band=(key[21]&1)!=0;int64_t index=wood_grid_key_signed64(key+22),band=wood_grid_key_signed64(key+30);r->total=0;r->coordinate=r->seed_coordinate;++r->query_attempts;
        bool ok=anchor?wood_grid_anchor_line_coord_resolved(s->context.state->items,s->context.state->count,g,&host,axis,index,has_band,band,&r->coordinate,r->error,sizeof r->error,wood_grid_cell_resolve,s):wood_grid_line_coord_in_resolved(s->context.state->items,s->context.state->count,g,&host,axis,index,&r->coordinate,&r->total,r->error,sizeof r->error,wood_grid_cell_resolve,s);
        if(!ok)return false;out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){r->coordinate,{true,pid,axis}};return true;
    }
    return false;
}

static bool wood_grid_system_hook(void *user,uint32_t id,char *error,size_t cap)
{WoodGridSources *s=user;GeoSourceValue value;bool ok=wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap)&&wood_grid_install_system(s,id,&value,true);if(ok)wood_grid_publish_system_cache(s,id);return ok;}
static void wood_grid_copy_binding_cache(WoodGridApplication *to,const WoodGridApplication *from)
{to->from_binding=from->from_binding;to->binding_id=from->binding_id;to->main_along=from->main_along;for(int a=0;a<2;++a){to->axis[a]=from->axis[a];to->lattice_base[a]=from->lattice_base[a];to->lattice_step[a]=from->lattice_step[a];to->lattice_index[a]=from->lattice_index[a];}}
static bool wood_grid_binding_hook(void *user,const GeoGridBinding *binding,WoodGridApplication *g,char *error,size_t cap)
{
    WoodGridSources *s=user;if(geo_grid_bindings_find(s->context.sources,binding->id)!=binding&&geo_grid_bindings_find(s->base.sources,binding->id)!=binding)return wood_grid_binding_cache_direct(&s->base,binding,g,error,cap);
    WoodGridSourceKey key;GeoSourceRef ref=wood_grid_source_ref(s->tokens.grid,WOOD_GRID_SOURCE_BINDING,binding->id,&key);WoodGridSourceResult *r=wood_grid_result(s,&ref);if(!r)return false;
    r->seed=*g;size_t attempts=r->cache_attempts;GeoSourceValue value;bool ok=wood_grid_source_get(s,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap);
    if(ok){WoodGridApplication decoded;if(value.kind!=GEO_SOURCE_DEFINITION||!wood_grid_decode_application_value(&value.as.definition,binding->id,&decoded))return false;r->cache=decoded;}
    if(ok||r->cache_attempts!=attempts)wood_grid_copy_binding_cache(g,&r->cache);return ok;
}
bool wood_grid_sources_application(WoodGridSources *s,uint32_t id,char *error,size_t cap)
{if(!s)return false;GeoSourceValue value;if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap)||!wood_grid_install_application(s,id,&value,true))return false;wood_grid_publish_application_cache(s,wood_grid_find(s->context.state,id));return true;}
static bool wood_grid_application_hook(void *user,WoodGridApplication *g,char *error,size_t cap)
{WoodGridSources *s=user;if(wood_grid_find(s->context.state,g->id)!=g&&wood_grid_find(s->base.state,g->id)!=g)return wood_grid_application_evaluate_direct(&s->base,g,error,cap);return wood_grid_sources_application(s,g->id,error,cap);}
bool wood_grid_sources_dimension(WoodGridSources *s,uint32_t id,int axis,int field,GeoCoord *out,char *error,size_t cap)
{if(!s||!out||field<0||field>1)return false;WoodGridSourceKey key;GeoSourceValue value;if(!wood_grid_source_get(s,wood_grid_dimension_source_ref(s->tokens.grid,id,axis,field,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap)||value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den<=0||value.as.quantity.num%value.as.quantity.den||!geo_coord_in_range(value.as.quantity.num/value.as.quantity.den))return false;*out=value.as.quantity.num/value.as.quantity.den;return true;}
static bool wood_grid_dimension_hook(void *user,const WoodGridApplication *g,int axis,int field,GeoCoord *out,char *error,size_t cap)
{WoodGridSources *s=user;if(wood_grid_find(s->context.state,g->id)!=g&&wood_grid_find(s->base.state,g->id)!=g)return wood_grid_application_dimension_direct(&s->base,g,axis,field,out,error,cap);return wood_grid_sources_dimension(s,g->id,axis,field,out,error,cap);}
bool wood_grid_sources_line(WoodGridSources *s,uint32_t id,uint32_t pid,int axis,int64_t index,bool anchor,bool has_band,int64_t band,GeoCoord *out,size_t *total,char *error,size_t cap)
{
    if(!s)return false;WoodGridSourceKey key;GeoSourceRef ref=wood_grid_line_source_ref(s->tokens.grid,id,pid,axis,index,anchor,has_band,band,&key);GeoSourceValue value;
    WoodGridSourceResult *r=wood_grid_result(s,&ref);if(!r)return false;r->seed_coordinate=out?*out:0;size_t attempts=r->query_attempts;
    bool ok=wood_grid_source_get(s,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap);
    if(ok||r->query_attempts!=attempts){if(out)*out=ok?value.as.position.coordinate:r->coordinate;if(total&&!anchor)*total=r->total;}return ok;
}
bool wood_grid_sources_cell(WoodGridSources *s,uint32_t id,GeoRect2 *out,char *error,size_t cap)
{if(!s)return false;WoodGridSourceKey key;GeoSourceRef ref=wood_grid_source_ref(s->tokens.grid,WOOD_GRID_SOURCE_CELL,id,&key);GeoSourceValue value;GeoRect2 scope;if(!wood_grid_source_get(s,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap)||!wood_grid_scope_read(&value,&scope))return false;if(out)*out=scope;return true;}
bool wood_grid_sources_rule_line(WoodGridSources *s,const GeoGridRuleLineRef *rule,uint32_t pid,GeoCoord *out,GeoRect2 *scope,char *error,size_t cap)
{
    if(!s||!rule)return false;WoodGridSourceKey key;GeoSourceRef ref=wood_grid_rule_source_ref(s->tokens.grid,rule,pid,&key);GeoSourceValue value;
    if(!wood_grid_source_get(s,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap))return false;
    GeoRect2 rectangle;if(scope){WoodGridSourceKey cell_key;GeoSourceValue cell;
        if(!wood_grid_source_get(s,wood_grid_rule_cell_ref(s->tokens.grid,rule->grid_id,rule->rule_key,rule->cell,&cell_key),GEO_DEPENDENCY_VALUE_REQUIRED,&cell,error,cap)||!wood_grid_scope_read(&cell,&rectangle))return false;}
    if(out)*out=value.as.position.coordinate;if(scope)*scope=rectangle;return true;
}
static bool wood_grid_rule_hook(void *user,const GeoGridRuleLineRef *rule,uint32_t pid,GeoCoord *out,GeoRect2 *scope,char *error,size_t cap)
{return wood_grid_sources_rule_line(user,rule,pid,out,scope,error,cap);}
static bool wood_grid_rule_cell_hook(void *user,uint32_t id,uint32_t rule,const int64_t cell[2],WoodGridRuleTarget *target,char *error,size_t cap)
{
    WoodGridSources *s=user;WoodGridSourceKey key;GeoSourceRef ref=wood_grid_rule_cell_ref(s->tokens.grid,id,rule,cell,&key);GeoSourceValue value;GeoRect2 scope;
    if(!wood_grid_source_get(s,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value,error,cap)||!wood_grid_scope_read(&value,&scope))return false;
    WoodGridSourceResult *r=wood_grid_result(s,&ref);if(!r)return false;*target=r->target;target->bounds=scope;return true;
}
static const GeoGridRule *wood_grid_rule_definition_hook(void *user,const GeoGridSystem *system,uint32_t key,char *error,size_t cap)
{
    WoodGridSources *s=user;WoodGridSourceKey source;GeoSourceValue value;GeoGridRule rule;
    if(!system||!wood_grid_source_get(s,wood_grid_rule_definition_source_ref(s->tokens.grid,system->id,key,&source),GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap)||
       value.kind!=GEO_SOURCE_DEFINITION||!wood_grid_decode_rule(&value.as.definition,system->id,key,&rule))return NULL;
    GeoGridSystem decoded=*system;size_t at=0;while(at<decoded.rule_count&&decoded.rules[at].key!=key)++at;
    if(at==decoded.rule_count)return NULL;decoded.rules[at]=rule;
    if(!geo_grid_systems_put(s->context.sources,&decoded))return NULL;
    return geo_grid_rule_find(geo_grid_systems_find(s->context.sources,system->id),key);
}
static bool wood_grid_policy_definitions(WoodGridSources *s,char *error,size_t cap)
{
    GeoSourceValue value;
    for(size_t i=0;i<geo_grid_systems_count(s->base.sources);++i){
        uint32_t id=geo_grid_systems_at(s->base.sources,i)->id;
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap)||!wood_grid_install_system(s,id,&value,false))return false;
        const GeoGridSystem *system=geo_grid_systems_find(s->context.sources,id);
        for(size_t j=0;j<system->rule_count;++j)
            if(!wood_grid_rule_definition_hook(s,system,system->rules[j].key,error,cap))return false;
    }
    for(size_t i=0;i<geo_grid_bindings_count(s->base.sources);++i)
        if(!wood_grid_install_binding(s,geo_grid_bindings_at(s->base.sources,i)->id,NULL,error,cap))return false;
    for(size_t i=0;i<s->base.state->count;++i){uint32_t id=s->base.state->items[i].id;
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap)||!wood_grid_install_application(s,id,&value,false))return false;
    }
    return true;
}
static bool wood_grid_world_valid_hook(void *user,const WoodGridContext *context,char *error,size_t cap)
{
    WoodGridSources *s=user;if(!wood_grid_policy_definitions(s,error,cap))return false;
    WoodGridContext evaluated=s->context;evaluated.before=context->before;
    return wood_grid_world_valid_direct(&evaluated,error,cap);
}
static bool wood_grid_rules_valid_hook(void *user,const WoodGridContext *context,char *error,size_t cap)
{
    WoodGridSources *s=user;if(!wood_grid_policy_definitions(s,error,cap))return false;
    WoodGridContext evaluated=s->context;evaluated.before=context->before;
    return wood_grid_rules_world_valid_direct(&evaluated,error,cap);
}
WoodGridSources *wood_grid_sources_create(GeoEvalContext *graph,WoodGridSourceTokens tokens,const WoodGridContext *base)
{
    if(!graph||!base||!base->state||!base->sources||!base->host||base->evaluation)return NULL;
    WoodGridSources *s=calloc(1,sizeof *s);if(!s)return NULL;s->graph=graph;s->tokens=tokens;s->base=*base;s->context=*base;
    s->evaluated=*base->state;s->evaluated_sources=geo_grid_store_clone(base->sources);if(!s->evaluated_sources){free(s);return NULL;}
    s->context.state=&s->evaluated;s->context.sources=s->evaluated_sources;
    s->hooks=(WoodGridEvaluation){s,wood_grid_system_hook,wood_grid_binding_hook,wood_grid_application_hook,wood_grid_dimension_hook,wood_grid_rule_hook,wood_grid_rule_cell_hook,wood_grid_rule_definition_hook,wood_grid_world_valid_hook,wood_grid_rules_valid_hook};
    s->context.user=s;s->context.host=wood_grid_host_source;s->context.coordinate=wood_grid_coordinate_source;s->context.vertex=wood_grid_vertex_source;s->context.reference=wood_grid_reference_source;s->context.evaluation=&s->hooks;
    GeoSourceProvider provider={tokens.grid,"wood.grid","wood-grid-sources/1",s,wood_grid_source_describe,wood_grid_source_evaluate};
    if(!geo_eval_register(graph,&provider)){geo_grid_store_destroy(s->evaluated_sources);free(s);return NULL;}return s;
}
bool wood_grid_sources_bind(WoodGridSources *s,WoodGridContext *c)
{
    if(!s||!c)return false;const WoodGridContext *b=&s->base;const WoodEngineeringContext *e=&c->engineering,*a=&b->engineering;
    if((c->evaluation&&c->evaluation!=&s->hooks)||c->state!=b->state||c->sources!=b->sources||c->user!=b->user||c->host!=b->host||c->coordinate!=b->coordinate||c->vertex!=b->vertex||c->reference!=b->reference||c->parameter_error!=b->parameter_error||c->before!=b->before||
       e->state!=a->state||e->versions!=a->versions||e->user!=a->user||e->error!=a->error||e->error_capacity!=a->error_capacity||e->sources!=a->sources||e->placement!=a->placement||e->target!=a->target||e->named_value!=a->named_value||e->parameter!=a->parameter||e->member_owned!=a->member_owned||e->write_dimension!=a->write_dimension||e->serializable!=a->serializable||e->resolve_source!=a->resolve_source||e->resolve_binding!=a->resolve_binding||e->last_terminal!=a->last_terminal||e->source_named!=a->source_named||e->source_parameter!=a->source_parameter||e->depend_definition!=a->depend_definition||e->validate_application!=a->validate_application||e->source_version_field!=a->source_version_field||e->source_version_definition!=a->source_version_definition||e->source_application!=a->source_application)return false;
    c->evaluation=&s->hooks;return true;
}
bool wood_grid_sources_definitions(WoodGridSources *s,char *error,size_t cap)
{
    if(!s)return false;GeoSourceValue value;
    for(size_t i=0;i<geo_grid_systems_count(s->context.sources);++i){const GeoGridSystem *g=geo_grid_systems_at(s->context.sources,i);
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,g->id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap))return false;
        for(size_t j=0;j<g->rule_count;++j){WoodGridSourceKey key;
            if(!wood_grid_source_get(s,wood_grid_rule_definition_source_ref(s->tokens.grid,g->id,g->rules[j].key,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap))return false;}}
    for(size_t i=0;i<geo_grid_bindings_count(s->context.sources);++i)
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_BINDING_DEFINITION,geo_grid_bindings_at(s->context.sources,i)->id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap))return false;
    for(size_t i=0;i<s->context.state->count;++i)
        if(!wood_grid_root_get(s,WOOD_GRID_SOURCE_APPLICATION_DEFINITION,s->context.state->items[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value,error,cap))return false;
    return true;
}
void wood_grid_sources_destroy(WoodGridSources *s)
{if(!s)return;WoodGridSourceResult *r=s->results;while(r){WoodGridSourceResult *next=r->next;free(r->definition);free(r);r=next;}geo_grid_store_destroy(s->evaluated_sources);free(s);}
