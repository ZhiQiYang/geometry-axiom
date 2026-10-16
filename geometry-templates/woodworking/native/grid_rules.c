/* D19a/I25a/R32: source-rule application, reference and edit policy.
 * Source/rule storage and exact interval arithmetic are owned by K. */
#include "grid_application.h"
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Existing guide-expression transport limit, including its terminator. */
#define WOOD_GRID_RULE_EXPRESSION_CAPACITY 1536

static bool wood_grid_rule_error(char *err,size_t cap,const char *code,uint32_t sid,uint32_t key)
{
    if(err)snprintf(err,cap,"I25a: %s source %u rule %u",code,sid,key);
    return false;
}
bool wood_grid_rules_valid(const GeoGridSystem *s,char *err,size_t cap)
{
    GeoGridStoreError detail;if(geo_grid_rules_validate(s,&detail))return true;
    const char *code="RULE_KEY";
    switch(detail.status){
    case GEO_GRID_STORE_RULE_CAPACITY:code="RULE_CAPACITY";break;
    case GEO_GRID_STORE_RULE_SOURCE:code="SOURCE_KIND";break;
    case GEO_GRID_STORE_RULE_NAME:code="RULE_NAME";break;
    case GEO_GRID_STORE_RULE_DIVISIONS:code="DIVISION_RANGE";break;
    case GEO_GRID_STORE_RULE_NOT_DIVISIBLE:code="DIVISION_NOT_EXACT";break;
    case GEO_GRID_STORE_RULE_CELL_RANGE:code="CELL_RANGE";break;
    case GEO_GRID_STORE_RULE_OVERLAP:
        if(err)snprintf(err,cap,"I25a: RULE_OVERLAP source %u rules %u/%u",s->id,detail.other_rule_key,detail.rule_key);return false;
    default:break;
    }
    return wood_grid_rule_error(err,cap,code,s?s->id:0,detail.rule_key);
}

/* Keep the existing expression grammar: a signed cell begins immediately
 * after ':', while any other +/- separates arithmetic terms. This scanner
 * consumes the H expression fact and never asks H to decide rule usage. */
static bool wood_grid_rule_i64(const char *text,int64_t *out)
{
    char *end=NULL;errno=0;long long value=strtoll(text,&end,10);
    if(end==text || *end || errno==ERANGE)return false;
    *out=(int64_t)value;return true;
}
static bool wood_grid_rule_u32(const char *text,uint32_t *out)
{
    int64_t value;
    if(!wood_grid_rule_i64(text,&value) || value<0 || value>UINT32_MAX)return false;
    *out=(uint32_t)value;return true;
}
static bool wood_grid_rule_ref_text(const char *text,GeoGridRuleLineRef *r)
{
    if(strlen(text)>=WOOD_GRID_RULE_EXPRESSION_CAPACITY)return false;
    char buf[WOOD_GRID_RULE_EXPRESSION_CAPACITY],*parts[8];size_t n=0;
    snprintf(buf,sizeof buf,"%s",text);char *p=buf;
    while(n<8){parts[n++]=p;char *colon=strchr(p,':');if(!colon)break;*colon=0;p=colon+1;}
    if(n!=8 || strchr(parts[7],':') || strcmp(parts[0],"gridrule") ||
        !wood_grid_rule_u32(parts[1],&r->grid_id) || !wood_grid_rule_u32(parts[2],&r->system_id) ||
        !wood_grid_rule_u32(parts[3],&r->rule_key) || !r->rule_key ||
        !wood_grid_rule_i64(parts[4],&r->cell[0]) || !wood_grid_rule_i64(parts[5],&r->cell[1]) ||
        (strcmp(parts[6],"u") && strcmp(parts[6],"v")) || !wood_grid_rule_u32(parts[7],&r->inner_index))return false;
    r->axis=!strcmp(parts[6],"u")?0:1;return true;
}
static bool wood_grid_rule_expression_uses(const char *expression,uint32_t sid,uint32_t key)
{
    const char *p=expression;
    if(!p)return false;
    while((p=strstr(p,"gridrule:"))!=NULL){
        const char *end=p;
        while(*end && !((*end=='+' || *end=='-') && !(end>p && end[-1]==':' && isdigit((unsigned char)end[1]))))++end;
        size_t n=(size_t)(end-p);GeoGridRuleLineRef r={0};char term[WOOD_GRID_RULE_EXPRESSION_CAPACITY];
        if(n<sizeof term){memcpy(term,p,n);term[n]=0;if(wood_grid_rule_ref_text(term,&r) && r.system_id==sid && r.rule_key==key)return true;}
        p+=9;
    }
    return false;
}
bool wood_grid_rule_used(const WoodGridContext *ctx,uint32_t sid,uint32_t key)
{
    if(!ctx || !ctx->reference)return false;
    WoodGridReference ref;
    for(size_t i=0;ctx->reference(ctx->user,i,&ref);++i){
        if(!ref.active)continue;
        if(ref.kind==WOOD_GRID_REFERENCE_GUIDE){if(wood_grid_rule_expression_uses(ref.expression,sid,key))return true;}
        else if(ref.kind==WOOD_GRID_REFERENCE_TIMBER && ref.is_rule && ref.rule.system_id==sid && ref.rule.rule_key==key)return true;
    }
    return false;
}
static bool wood_grid_rule_shape_changed(const GeoGridRule *a,const GeoGridRule *b)
{
    return !a || !b || a->all_cells!=b->all_cells ||
        memcmp(a->cell,b->cell,sizeof a->cell) || memcmp(a->divisions,b->divisions,sizeof a->divisions);
}
bool wood_grid_rule_change_allowed(const WoodGridContext *ctx,uint32_t sid,uint32_t key,
    const GeoGridRule *replacement,bool remove,char *err,size_t cap)
{
    const GeoGridSystem *s=ctx?geo_grid_systems_find(ctx->sources,sid):NULL;
    const GeoGridRule *old=geo_grid_rule_find(s,key);
    if(old && wood_grid_rule_used(ctx,sid,key) && (remove || wood_grid_rule_shape_changed(replacement,old)))
        return wood_grid_rule_error(err,cap,"RULE_REFERENCED",sid,key);
    return true;
}
bool wood_grid_rules_world_valid(const WoodGridContext *ctx,char *err,size_t cap)
{
    if(!ctx || !ctx->state || !ctx->sources)return false;
    if(ctx->before)for(size_t i=0;i<geo_grid_systems_count(ctx->before->sources);++i){
        const GeoGridSystem *old=geo_grid_systems_at(ctx->before->sources,i),*now=geo_grid_systems_find(ctx->sources,old->id);
        for(size_t j=0;j<old->rule_count;++j){const GeoGridRule *r=&old->rules[j],*q=geo_grid_rule_find(now,r->key);
            if(wood_grid_rule_used(ctx->before,old->id,r->key) && wood_grid_rule_shape_changed(q,r))
                return wood_grid_rule_error(err,cap,"RULE_REFERENCED",old->id,r->key);
        }
    }
    for(size_t i=0;i<ctx->state->count;++i){const WoodGridApplication *g=&ctx->state->items[i];
        if(!g->is_subgrid || !g->lattice_cell)continue;
        const WoodGridApplication *parent=wood_grid_find(ctx->state,g->parent_id);
        const GeoGridBinding *binding=parent && parent->from_binding?geo_grid_bindings_find(ctx->sources,parent->binding_id):NULL;
        const GeoGridSystem *s=binding?geo_grid_systems_find(ctx->sources,binding->system_id):NULL;
        if(s)for(size_t j=0;j<s->rule_count;++j)if(geo_grid_rule_matches(&s->rules[j],g->lattice_cell_index)){
            if(err)snprintf(err,cap,"I25a: MANUAL_CONFLICT source %u rule %u manual %u parent %u cell (%lld,%lld)",
                s->id,s->rules[j].key,g->id,parent->id,(long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1]);
            return false;
        }
    }
    return true;
}

bool wood_grid_rule_target(const WoodGridContext *ctx,const char *kind,uint32_t id,
    WoodGridRuleTarget *target,char *err,size_t cap)
{
    memset(target,0,sizeof *target);
    if(!ctx || !ctx->state || !ctx->sources || !kind)return false;
    WoodGridApplication *derived=&target->derived;
    if(!strcmp(kind,"system")){
        target->source=geo_grid_systems_find(ctx->sources,id);
        if(!target->source)return wood_grid_rule_error(err,cap,"WRONG_SOURCE",id,0);
        derived->from_binding=true;
        for(int a=0;a<2;++a){derived->axis[a]=target->source->axis[a];derived->lattice_base[a]=geo_grid_axis_phase(&target->source->axis[a]);derived->lattice_step[a]=geo_grid_axis_pitch(&target->source->axis[a]);}
    }else{
        const GeoGridBinding *binding=NULL;
        if(!strcmp(kind,"binding"))binding=geo_grid_bindings_find(ctx->sources,id);
        else if(!strcmp(kind,"grid")){
            const WoodGridApplication *g=wood_grid_find(ctx->state,id);WoodGridHost host;
            if(!g || !g->from_binding || g->is_subgrid)return wood_grid_rule_error(err,cap,"WRONG_SOURCE",0,0);
            *derived=*g;binding=geo_grid_bindings_find(ctx->sources,g->binding_id);
            if(!ctx->host || !ctx->host(ctx->user,g->placement_id,&host))return wood_grid_rule_error(err,cap,"WRONG_SOURCE",0,0);
            target->has_placement=true;target->placement_id=host.id;target->boundary_id=host.boundary_id;
        }
        if(!binding || !wood_grid_binding_cache(ctx,binding,derived,err,cap))return false;
        target->source=geo_grid_systems_find(ctx->sources,binding->system_id);
        target->has_boundary=true;
        if(!target->has_placement)target->boundary_id=binding->boundary_id;
    }
    if(!target->source || target->source->axis[0].source!=GEO_GRID_SOURCE_REPEAT ||
        target->source->axis[1].source!=GEO_GRID_SOURCE_REPEAT || target->source->axis[0].stagger_set ||
        target->source->axis[1].stagger_set)return wood_grid_rule_error(err,cap,"SOURCE_KIND",target->source?target->source->id:0,0);
    return true;
}
bool wood_grid_rule_cell(const WoodGridContext *ctx,const char *kind,uint32_t id,uint32_t key,
    const int64_t cell[2],WoodGridRuleTarget *target,char *err,size_t cap)
{
    if(!wood_grid_rule_target(ctx,kind,id,target,err,cap))return false;
    target->rule=geo_grid_rule_find(target->source,key);
    if(!target->rule)return wood_grid_rule_error(err,cap,"RULE_MISSING",target->source->id,key);
    if(!geo_grid_rule_matches(target->rule,cell))return wood_grid_rule_error(err,cap,"SELECTOR_MISS",target->source->id,key);
    GeoCoord ends[2][2];
    for(int a=0;a<2;++a)if(cell[a]==INT64_MAX || !wood_grid_lattice_coord(&target->derived,a,cell[a],&ends[a][0]) ||
        !wood_grid_lattice_coord(&target->derived,a,cell[a]+1,&ends[a][1]))return wood_grid_rule_error(err,cap,"CELL_RANGE",target->source->id,key);
    target->bounds=(GeoRect2){ends[0][0],ends[1][0],ends[0][1],ends[1][1]};return true;
}
bool wood_grid_rule_line(const WoodGridContext *ctx,const GeoGridRuleLineRef *ref,uint32_t pid,
    GeoCoord *coordinate,GeoRect2 *scope,char *err,size_t cap)
{
    WoodGridRuleTarget target;
    if(!wood_grid_rule_cell(ctx,"grid",ref->grid_id,ref->rule_key,ref->cell,&target,err,cap))return false;
    const GeoGridSystem *s=target.source;const GeoGridRule *r=target.rule;GeoRect2 cell=target.bounds;
    if(s->id!=ref->system_id || !target.has_placement || target.placement_id!=pid)
        return wood_grid_rule_error(err,cap,"WRONG_SOURCE",ref->system_id,ref->rule_key);
    if(ref->axis<0 || ref->axis>1 || ref->inner_index>=r->divisions[ref->axis]-1)
        return wood_grid_rule_error(err,cap,"INDEX_RANGE",s->id,r->key);
    GeoCoord lines[WOOD_GRID_MAX_LINES];size_t count;
    GeoCoord lo=ref->axis?cell.min_v:cell.min_u,hi=ref->axis?cell.max_v:cell.max_u;
    if(geo_interval_subdivide(lo,hi,r->divisions[ref->axis],lines,WOOD_GRID_MAX_LINES,&count)!=GEO_GRID_OK || ref->inner_index>=count)
        return wood_grid_rule_error(err,cap,"CELL_RANGE",s->id,r->key);
    if(coordinate)*coordinate=lines[ref->inner_index];
    if(scope)*scope=cell;return true;
}

bool wood_grid_rule_edit_begin(const WoodGridContext *ctx,uint32_t sid,uint32_t key,
    bool create,bool remove,bool replay,uint32_t *assigned,char *err,size_t cap)
{
    const GeoGridSystem *old=ctx?geo_grid_systems_find(ctx->sources,sid):NULL;
    if(!old){if(err)snprintf(err,cap,"I25a: WRONG_SOURCE");return false;}
    if(create){
        if(replay || !old->next_rule_key){if(err)snprintf(err,cap,"I25a: RULE_KEY_EXHAUSTED or create in scene");return false;}
        key=old->next_rule_key;
    }
    if((remove || (!create && !replay)) && !geo_grid_rule_find(old,key)){
        if(err)snprintf(err,cap,"I25a: RULE_MISSING");return false;
    }
    if(assigned)*assigned=key;return true;
}
bool wood_grid_rule_edit(WoodGridContext *ctx,uint32_t sid,const GeoGridRule *rule,
    bool create,bool remove,bool replay,char *err,size_t cap)
{
    if(!ctx || !rule)return false;
    uint32_t key=rule->key;
    if(!wood_grid_rule_edit_begin(ctx,sid,key,create,remove,replay,&key,err,cap))return false;
    if(!wood_grid_rule_change_allowed(ctx,sid,key,rule,remove,err,cap))return false;
    const GeoGridSystem *old=geo_grid_systems_find(ctx->sources,sid);
    GeoGridSystem definition=*old;size_t slot=0;
    while(slot<definition.rule_count && definition.rules[slot].key!=key)++slot;
    if(remove){
        memmove(definition.rules+slot,definition.rules+slot+1,(definition.rule_count-slot-1)*sizeof *rule);
        memset(&definition.rules[--definition.rule_count],0,sizeof *rule);
    }else{
        if(slot==definition.rule_count){
            if(slot==GEO_GRID_RULE_CAPACITY){if(err)snprintf(err,cap,"I25a: RULE_CAPACITY");return false;}
            ++definition.rule_count;
        }
        definition.rules[slot]=*rule;definition.rules[slot].key=key;
        if(create || (replay && definition.next_rule_key && key>=definition.next_rule_key))
            definition.next_rule_key=key==UINT32_MAX?0:key+1;
    }
    return wood_grid_source_put(ctx,&definition,wood_grid_source_main_along(ctx->state,sid));
}
