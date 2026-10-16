#include "grid_application.h"
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

static bool wood_grid_error(char *error,size_t cap,const char *format,...)
{if(error){va_list args;va_start(args,format);vsnprintf(error,cap,format,args);va_end(args);}return false;}
const WoodGridApplication *wood_grid_find(const WoodGridState *s,uint32_t id)
{if(s)for(size_t i=0;i<s->count;++i)if(s->items[i].id==id)return &s->items[i];return NULL;}
WoodGridApplication *wood_grid_find_mut(WoodGridState *s,uint32_t id)
{return (WoodGridApplication *)wood_grid_find(s,id);}
bool wood_grid_stage(WoodGridState *s,const WoodGridApplication *g)
{WoodGridApplication *old=wood_grid_find_mut(s,g->id);if(old){*old=*g;return true;}if(s->count>=WOOD_GRID_MAX)return false;s->items[s->count++]=*g;return true;}
int wood_grid_source_main_along(const WoodGridState *s,uint32_t id)
{for(size_t i=0;i<s->role_count;++i)if(s->roles[i].source_id==id)return s->roles[i].main_along;return 0;}
bool wood_grid_source_main_valid(const GeoGridSystem *s,int main_along)
{return main_along>=0&&main_along<=2&&(main_along!=1||s->axis[1].source)&&(main_along!=2||s->axis[0].source);}
static size_t wood_grid_role_slot(const WoodGridState *s,uint32_t id)
{size_t i=0;while(i<s->role_count&&s->roles[i].source_id!=id)++i;return i;}
bool wood_grid_source_put(WoodGridContext *c,const GeoGridSystem *s,int main_along)
{
    size_t at=wood_grid_role_slot(c->state,s->id);
    if(at>=GEO_GRID_SYSTEM_CAPACITY||!geo_grid_systems_put(c->sources,s))return false;
    c->state->roles[at]=(WoodGridSourceRole){s->id,main_along};
    if(at==c->state->role_count)++c->state->role_count;return true;
}
bool wood_grid_source_redeclare(WoodGridContext *c,const GeoGridSystem *s,int main_along,GeoGridStoreError *error)
{
    size_t at=wood_grid_role_slot(c->state,s->id);
    if(at>=GEO_GRID_SYSTEM_CAPACITY){if(error){memset(error,0,sizeof *error);error->status=GEO_GRID_STORE_CAPACITY;error->system_id=s->id;}return false;}
    if(!geo_grid_systems_redeclare(c->sources,s,error))return false;
    c->state->roles[at]=(WoodGridSourceRole){s->id,main_along};
    if(at==c->state->role_count)++c->state->role_count;return true;
}
bool wood_grid_source_remove(WoodGridContext *c,uint32_t id)
{
    if(!geo_grid_systems_remove(c->sources,id))return false;
    size_t at=wood_grid_role_slot(c->state,id);
    if(at<c->state->role_count){memmove(c->state->roles+at,c->state->roles+at+1,(c->state->role_count-at-1)*sizeof *c->state->roles);memset(c->state->roles+--c->state->role_count,0,sizeof *c->state->roles);}return true;
}
bool wood_grid_begin_direct(const WoodGridContext *c,uint32_t id,uint32_t pid,WoodGridApplication *out,char *error,size_t cap)
{
    const WoodGridApplication *old=wood_grid_find(c->state,id);
    if(old&&(old->from_system||old->from_binding))return wood_grid_error(error,cap,"D29: edit the grid-system source or its application origin; direct axis edits are not allowed");
    if(old&&old->is_subgrid)return wood_grid_error(error,cap,"D19：不能將既有子網格改成主網格");
    if(old&&old->placement_id!=pid)return wood_grid_error(error,cap,"這個 grid id 已經用在別的承載面");
    if(!old){
        for(size_t i=0;i<c->state->count;++i)if(!c->state->items[i].is_subgrid&&c->state->items[i].placement_id==pid)return wood_grid_error(error,cap,"這片承載面已經有一座網格（一面一格）");
        if(c->state->count==WOOD_GRID_MAX)return wood_grid_error(error,cap,"網格的數量超過上限");
        memset(out,0,sizeof *out);out->id=id;out->placement_id=pid;
    }else *out=*old;
    return true;
}
bool wood_grid_apply_system(WoodGridContext *c,const WoodGridApplication *definition,char *error,size_t cap)
{
    WoodGridApplication g=*definition;WoodGridHost host;
    if(!c->host(c->user,g.placement_id,&host)||!geo_grid_systems_find(c->sources,g.system_id))return wood_grid_error(error,cap,"I37: grid application needs an existing surface and grid-system");
    if(wood_eng_object_bound(&c->engineering,0,g.id))return wood_grid_error(error,cap,"D29/I37: detach engineering bindings before choosing a grid-system source");
    g.from_system=true;size_t slot=c->state->count;
    for(size_t k=0;k<c->state->count;++k){const WoodGridApplication *old=&c->state->items[k];
        if(old->id==g.id){if(old->is_subgrid||old->from_binding||old->placement_id!=g.placement_id)return wood_grid_error(error,cap,"I37: cannot change a subgrid or move an existing grid identity to another surface");slot=k;}
        else if(!old->is_subgrid&&old->placement_id==g.placement_id)return wood_grid_error(error,cap,"I10: this surface already has a main grid");
    }
    if(slot==c->state->count&&slot==WOOD_GRID_MAX)return wood_grid_error(error,cap,"I10: grid capacity exceeded");
    c->state->items[slot]=g;if(slot==c->state->count)++c->state->count;return true;
}
bool wood_grid_direct_declared(const WoodGridContext *c,const WoodGridApplication *g,int filled,bool has_main,char *error,size_t cap)
{
    if(!filled&&!(wood_grid_find(c->state,g->id)&&has_main))return wood_grid_error(error,cap,"新網格至少要一個格線來源");
    if((g->main_along==1&&g->axis[1].source==GEO_GRID_SOURCE_NONE)||(g->main_along==2&&g->axis[0].source==GEO_GRID_SOURCE_NONE))return wood_grid_error(error,cap,"grid 主支方向沒有對應的格線來源");
    return true;
}
bool wood_grid_direct_check(const WoodGridContext *c,const WoodGridApplication *g,char *error,size_t cap)
{
    WoodGridHost host;if(!c->host(c->user,g->placement_id,&host))return false;
    for(int axis=0;axis<2;++axis){GeoCoord probe[WOOD_GRID_MAX_LINES];size_t count;char detail[200]="";
        if(g->axis[axis].source==GEO_GRID_SOURCE_NONE)continue;
        if(!wood_grid_axis_lines(g,&host,axis,probe,&count,detail,sizeof detail))return wood_grid_error(error,cap,"grid 座標不合法（%c 軸）：%s",axis?'v':'u',detail[0]?detail:"要嚴格遞增、且落在承載面外接範圍內");
    }
    for(size_t i=0;i<c->state->count;++i)if(c->state->items[i].is_subgrid&&c->state->items[i].parent_id==g->id)return wood_grid_parent_count_valid(c,g,&host,error,cap);
    return true;
}
bool wood_grid_apply_binding(WoodGridContext *c,const WoodGridApplication *definition,char *error,size_t cap)
{
    WoodGridApplication g=*definition;
    if(wood_eng_object_bound(&c->engineering,0,g.id))goto invalid;
    g.from_binding=true;size_t slot=c->state->count;
    for(size_t i=0;i<c->state->count;++i){const WoodGridApplication *old=&c->state->items[i];
        if(old->id==g.id){if(!old->from_binding||old->is_subgrid||old->placement_id!=g.placement_id)goto invalid;slot=i;}
        else if(!old->is_subgrid&&old->placement_id==g.placement_id)goto invalid;
    }
    if(slot==WOOD_GRID_MAX)goto invalid;
    c->state->items[slot]=g;if(slot==c->state->count)++c->state->count;return true;
invalid:return wood_grid_error(error,cap,"D30/I37: from-binding requires an available lattice grid identity and the binding's boundary placement");
}
bool wood_grid_prepare_child(const WoodGridContext *c,WoodGridApplication *g,bool lattice,unsigned du,unsigned dv,char *error,size_t cap)
{
    const WoodGridApplication *old=wood_grid_find(c->state,g->id),*parent=wood_grid_find(c->state,g->parent_id);
    if(!parent||parent->is_subgrid||g->id==g->parent_id||(old&&(!old->is_subgrid||old->parent_id!=g->parent_id||old->lattice_cell!=lattice)))return wood_grid_error(error,cap,"D19/I25：父格必須是主網格；既有網格的類型與父格編號不能更換");
    if(parent->axis[0].stagger_set||parent->axis[1].stagger_set)return wood_grid_error(error,cap,"I24：有相位差的主格不能建立子網格");
    if(parent->from_binding!=lattice)return wood_grid_error(error,cap,"D19/I25：子格 %u 的父格 %u 必須使用 %s 參照形式",g->id,parent->id,parent->from_binding?"lattice-cell":"cell");
    g->is_subgrid=true;g->lattice_cell=lattice;g->placement_id=parent->placement_id;g->divisions[0]=du;g->divisions[1]=dv;return true;
}
bool wood_grid_child_check(const WoodGridContext *c,const WoodGridApplication *g,char *error,size_t cap)
{
    WoodGridHost host;
    if(!c->host(c->user,g->placement_id,&host))return wood_grid_error(error,cap,"I25：找不到父格所屬的面");
    if(!wood_grid_valid_in(c->state->items,c->state->count,g,&host,error,cap)){
        if(error&&!error[0])return wood_grid_error(error,cap,"I25：找不到父格所屬的面");return false;
    }
    if(!wood_grid_find(c->state,g->id)&&c->state->count>=WOOD_GRID_MAX)return wood_grid_error(error,cap,"I10：主網格與子網格合計不能超過 16 組");
    return true;
}
static size_t wood_grid_binding_index(const GeoGridStore *s,uint32_t id)
{size_t i=0;while(i<geo_grid_bindings_count(s)&&geo_grid_bindings_at(s,i)->id!=id)++i;return i;}
bool wood_grid_binding_cache(const WoodGridContext *c,const GeoGridBinding *binding,WoodGridApplication *g,char *err,size_t cap)
{if(c->evaluation&&c->evaluation->binding)return c->evaluation->binding(c->evaluation->user,binding,g,err,cap);return wood_grid_binding_cache_direct(c,binding,g,err,cap);}
bool wood_grid_binding_cache_direct(const WoodGridContext *c,const GeoGridBinding *binding,WoodGridApplication *g,char *err,size_t cap)
{
    GeoGridBindingCache cache={0};GeoGridStoreError detail;
    for(int axis=0;axis<2;++axis){cache.axis[axis]=g->axis[axis];cache.lattice[axis]=(GeoLattice){g->lattice_base[axis],g->lattice_step[axis],g->lattice_index[axis]};}
    bool ok=geo_grid_binding_evaluate(c->sources,wood_grid_binding_index(c->sources,binding->id),c->vertex,c->user,&cache,&detail);
    if(detail.status!=GEO_GRID_STORE_BINDING_SOURCE&&detail.status!=GEO_GRID_STORE_BINDING_MISSING&&detail.status!=GEO_GRID_STORE_INVALID){
        g->from_binding=true;g->binding_id=binding->id;g->main_along=wood_grid_source_main_along(c->state,binding->system_id);
        for(int axis=0;axis<2;++axis){g->axis[axis]=cache.axis[axis];g->lattice_base[axis]=cache.lattice[axis].base;g->lattice_step[axis]=cache.lattice[axis].pitch;g->lattice_index[axis]=cache.lattice[axis].index;}
    }
    if(ok)return true;
    switch(detail.status){
    case GEO_GRID_STORE_BINDING_CELL_RANGE:return wood_grid_error(err,cap,"D29/R32: cell upper line index exceeds signed int64");
    case GEO_GRID_STORE_BINDING_ANCHOR:return wood_grid_error(err,cap,"D1/I37: anchor must have an exact integer-millimetre offset");
    case GEO_GRID_STORE_BINDING_SHIFT_RANGE:return wood_grid_error(err,cap,"D10b/D30: 錯開後的錨點超出可表達範圍");
    default:return wood_grid_error(err,cap,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes");
    }
}
bool wood_grid_bindings_rebuild(WoodGridContext *c,char *err,size_t cap)
{
    if(geo_grid_bindings_count(c->sources)>GEO_GRID_BINDING_CAPACITY)goto invalid;
    for(size_t i=0;i<geo_grid_bindings_count(c->sources);++i){WoodGridApplication derived={0};
        if(!wood_grid_binding_cache(c,geo_grid_bindings_at(c->sources,i),&derived,err,cap))return false;
        for(size_t j=0;j<i;++j)if(geo_grid_bindings_at(c->sources,j)->id==geo_grid_bindings_at(c->sources,i)->id)goto invalid;
    }
    for(size_t i=0;i<c->state->count;++i){WoodGridApplication *g=&c->state->items[i];if(!g->from_binding)continue;
        const GeoGridBinding *binding=geo_grid_bindings_find(c->sources,g->binding_id);WoodGridHost host;
        if(!binding||!c->host(c->user,g->placement_id,&host)||!host.boundary_id||host.boundary_id!=binding->boundary_id||g->is_subgrid||g->from_system||wood_eng_object_bound(&c->engineering,0,g->id))goto invalid;
        if(c->evaluation&&c->evaluation->application){if(!c->evaluation->application(c->evaluation->user,g,err,cap))return false;}
        else if(!wood_grid_binding_cache(c,binding,g,err,cap))return false;
    }
    return true;
invalid:return wood_grid_error(err,cap,"D30/I37: invalid grid-binding identity, capacity or application");
}
bool wood_grid_delete(WoodGridContext *c,const char *kind,uint32_t id,char *err,size_t cap)
{
    if(!strcmp(kind,"grid-binding")){
        if(!geo_grid_bindings_find(c->sources,id))return wood_grid_error(err,cap,"I37: grid-binding does not exist");
        for(size_t i=0;i<c->state->count;++i)if(c->state->items[i].from_binding&&c->state->items[i].binding_id==id)return wood_grid_error(err,cap,"I37: grid-binding is still referenced by a grid");
        return geo_grid_bindings_remove(c->sources,id);
    }
    if(!strcmp(kind,"grid-system")){
        for(size_t i=0;i<geo_grid_bindings_count(c->sources);++i)if(geo_grid_bindings_at(c->sources,i)->system_id==id)return wood_grid_error(err,cap,"I37: grid-system is still referenced by a grid-binding");
        if(!geo_grid_systems_find(c->sources,id))return wood_grid_error(err,cap,"I37: grid-system does not exist");
        for(size_t i=0;i<c->state->count;++i)if(c->state->items[i].from_system&&c->state->items[i].system_id==id)return wood_grid_error(err,cap,"I37: grid-system %u is still referenced by grid %u",id,c->state->items[i].id);
        return wood_grid_source_remove(c,id);
    }
    size_t slot=0;while(slot<c->state->count&&c->state->items[slot].id!=id)++slot;
    if(slot==c->state->count)return wood_grid_error(err,cap,"這個網格不存在");
    for(size_t i=0;i<c->state->count;++i)if(c->state->items[i].is_subgrid&&c->state->items[i].parent_id==id)return wood_grid_error(err,cap,"I23：網格 %u 仍有子格 %u，不能刪除",id,c->state->items[i].id);
    WoodGridReference r;
    for(int phase=0;phase<2;++phase)for(size_t i=0;c->reference&&c->reference(c->user,i,&r);++i){
        if((r.kind==WOOD_GRID_REFERENCE_GUIDE)!=(phase==0))continue;
        if(r.kind==WOOD_GRID_REFERENCE_GUIDE){
            char rule[48],key[40];snprintf(rule,sizeof rule,"gridrule:%u:",id);snprintf(key,sizeof key,"grid:%u:",id);
            const char *text=r.expression?r.expression:"",*at=text;bool used=strstr(text,rule)!=NULL;
            while(!used&&(at=strstr(at,key))!=NULL){if(at==text||at[-1]=='+'||at[-1]=='-'||at[-1]=='*')used=true;else ++at;}
            if(used)return wood_grid_error(err,cap,"I23：網格 %u 仍被參考線 %u 引用，不能刪除",id,r.id);
        }else if(r.active&&r.grid_id==id)return wood_grid_error(err,cap,"V_GRID_LOCKED：有角材錨在這個網格上，先刪角材（timber）");
    }
    memmove(c->state->items+slot,c->state->items+slot+1,(c->state->count-slot-1)*sizeof *c->state->items);--c->state->count;return true;
}

static bool wood_grid_system_error(const WoodGridContext *c,const GeoGridStoreError *detail,char *error,size_t cap)
{
    switch(detail->status){
    case GEO_GRID_STORE_PARAMETER_AXIS: case GEO_GRID_STORE_PARAMETER_SOURCE:
        snprintf(error,cap,"grid-system %u %c: %.190s",detail->system_id,detail->axis?'v':'u',c->parameter_error?c->parameter_error:"");break;
    case GEO_GRID_STORE_STAGGER_SOURCE:
        snprintf(error,cap,"I24: 相位差只接受兩軸都存在的無限排法");break;
    case GEO_GRID_STORE_STAGGER_PITCH:
        snprintf(error,cap,"I24: grid-system %u %c has no positive pitch",detail->system_id,detail->axis?'v':'u');break;
    case GEO_GRID_STORE_STAGGER_ZERO:
        snprintf(error,cap,"I24: 相位差為 0。要貫通線請省略 stagger，不要寫 0");break;
    case GEO_GRID_STORE_STAGGER_MULTIPLE:
        snprintf(error,cap,"I24: 相位差是間距的整數倍，奇數格與偶數格的線會重合。要貫通線請省略這個欄位");break;
    case GEO_GRID_STORE_STAGGER_OVERFLOW:
        snprintf(error,cap,"I24: 相位加相位差超出可表達範圍");break;
    default:snprintf(error,cap,"I37: grid-system %u has an invalid definition",detail->system_id);break;
    }
    return false;
}
bool wood_grid_systems_rebuild(WoodGridContext *c,char *error,size_t cap)
{
    if (geo_grid_systems_count(c->sources)>GEO_GRID_SYSTEM_CAPACITY) {
        snprintf(error,cap,"I37: grid-system capacity exceeded"); return false;
    }
    for(size_t i=0;i<geo_grid_systems_count(c->sources);++i){
        const GeoGridSystem *system=geo_grid_systems_at(c->sources,i);
        if(c->evaluation&&c->evaluation->system){if(!c->evaluation->system(c->evaluation->user,system->id,error,cap))return false;}
        else if(!wood_grid_system_evaluate_direct(c,system->id,error,cap))return false;
        for(size_t j=0;j<i;++j)if(geo_grid_systems_at(c->sources,j)->id==system->id){
            snprintf(error,cap,"I37: duplicate grid-system identity");return false;
        }
    }
    for (size_t i=0;i<c->state->count;++i) {
        WoodGridApplication *g=&c->state->items[i]; if (!g->from_system) continue;
        if(c->evaluation&&c->evaluation->application){if(!c->evaluation->application(c->evaluation->user,g,error,cap))return false;}
        else if(!wood_grid_application_evaluate_direct(c,g,error,cap))return false;
    }
    return true;
}
bool wood_grid_system_evaluate_direct(WoodGridContext *c,uint32_t id,char *error,size_t cap)
{
    size_t index=0;while(index<geo_grid_systems_count(c->sources)&&geo_grid_systems_at(c->sources,index)->id!=id)++index;
    GeoGridStoreError detail;
    if(!geo_grid_system_evaluate(c->sources,index,c->coordinate,c->user,&detail))return wood_grid_system_error(c,&detail,error,cap);
    const GeoGridSystem *system=geo_grid_systems_at(c->sources,index);
    if(!wood_grid_source_main_valid(system,wood_grid_source_main_along(c->state,system->id)))return wood_grid_error(error,cap,"I37: grid-system %u has an invalid definition",system->id);
    return wood_grid_rules_valid(system,error,cap);
}
bool wood_grid_application_dimension_direct(const WoodGridContext *c,const WoodGridApplication *g,int axis,int field,GeoCoord *out,char *error,size_t cap)
{
    if(!c||!g||!out||axis<0||axis>1||field<0||field>1)return false;
    EngTarget target={0,g->id,axis,field};EngBinding *binding=wood_eng_binding((WoodEngineeringContext *)&c->engineering,&target);
    if(binding){
        if(!wood_eng_effective((WoodEngineeringContext *)&c->engineering,binding,out,NULL,0))return wood_grid_error(error,cap,"%s",c->engineering.error);
    }else *out=field?g->axis[axis].gap:g->axis[axis].body;
    return true;
}
bool wood_grid_application_evaluate_direct(WoodGridContext *c,WoodGridApplication *g,char *error,size_t cap)
{
    if(g->from_system){
        const GeoGridSystem *s=geo_grid_systems_find(c->sources,g->system_id);
        if(!s||geo_grid_system_is_infinite(s)||g->from_binding||g->is_subgrid||!geo_coord_in_range(g->system_origin[0])||!geo_coord_in_range(g->system_origin[1]))
            return wood_grid_error(error,cap,"I37: grid %u has a missing or invalid grid-system source",g->id);
        g->main_along=wood_grid_source_main_along(c->state,s->id);
        for(int axis=0;axis<2;++axis){GeoGridAxisDef *a=&g->axis[axis];*a=s->axis[axis];GeoCoord offset=g->system_origin[axis];
            if(a->source==GEO_GRID_SOURCE_EXPLICIT)for(size_t k=0;k<a->count;++k)a->coords[k]+=offset;
            else if(a->source==GEO_GRID_SOURCE_SERIES)a->start+=offset;
            else if(a->source==GEO_GRID_SOURCE_BODY_GAP)a->anchor+=offset;
            if(!geo_grid_axis_valid(a))return wood_grid_error(error,cap,"I37: grid %u %c translated coordinates exceed D1 range",g->id,axis?'v':'u');
        }
        return true;
    }
    if(g->from_binding){
        const GeoGridBinding *binding=geo_grid_bindings_find(c->sources,g->binding_id);WoodGridHost host;
        if(!binding||!c->host(c->user,g->placement_id,&host)||!host.boundary_id||host.boundary_id!=binding->boundary_id||g->is_subgrid||g->from_system||wood_eng_object_bound(&c->engineering,0,g->id))
            return wood_grid_error(error,cap,"D30/I37: invalid grid-binding identity, capacity or application");
        return wood_grid_binding_cache(c,binding,g,error,cap);
    }
    if(!g->is_subgrid)for(int axis=0;axis<2;++axis)if(g->axis[axis].source==GEO_GRID_SOURCE_BODY_GAP){
        for(int field=0;field<2;++field){GeoCoord *out=field?&g->axis[axis].gap:&g->axis[axis].body;
            bool ok=c->evaluation&&c->evaluation->dimension?c->evaluation->dimension(c->evaluation->user,g,axis,field,out,error,cap):wood_grid_application_dimension_direct(c,g,axis,field,out,error,cap);
            if(!ok)return false;
        }
    }
    return true;
}

/* D28/I36 engineering-grid admission and definitions remain template policy. */
bool wood_grid_bind_engineering(WoodGridContext *c,GeoJson *j,int t,uint32_t id,const EngApplication *a,const EngMethodVersion *method)
{
        WoodGridApplication *g=wood_grid_find_mut(c->state,id); int create=0;
        if (g && (g->from_system || g->from_binding)) return wood_eng_fail(&c->engineering,"D29: grid-system applications cannot have engineering bindings");
        int create_t=geo_json_member(j,t,"create"); if (create_t>=0 && !geo_json_boolean(j,create_t,&create)) return wood_eng_fail(&c->engineering,"D28: create must be boolean");
        if (g && (g->is_subgrid || g->placement_id!=a->placement_id)) return wood_eng_fail(&c->engineering,"D28: selected main grid belongs to another face or is a subgrid");
        if (!g) {
            if (!create) return wood_eng_fail(&c->engineering,"D28: selected main grid is missing; explicitly choose create");
            for (size_t k=0;k<c->state->count;++k) if (!c->state->items[k].is_subgrid && c->state->items[k].placement_id==a->placement_id) return wood_eng_fail(&c->engineering,"I10: placement already has a main grid");
            if (c->state->count==WOOD_GRID_MAX) return wood_eng_fail(&c->engineering,"I10: grid capacity exceeded");
            g=&c->state->items[c->state->count++]; memset(g,0,sizeof *g); g->id=id; g->placement_id=a->placement_id; g->main_along=a->main_along?a->main_along:method->main_along;
            if (!g->main_along) return wood_eng_fail(&c->engineering,"D28: new grid main direction is not set");
        } else if (create) return wood_eng_fail(&c->engineering,"D28: create grid ID already exists; select update instead");
        int anchors=geo_json_member(j,t,"anchors"); if (anchors>=0&&!geo_json_keys(j,anchors,"","u,v")) return wood_eng_fail(&c->engineering,"D28: anchor fields must be u/v");
        WoodGridHost host;
        if (!c->host(c->user,a->placement_id,&host) || !host.bounds_valid) return wood_eng_fail(&c->engineering,"D28: cannot resolve application face bounds");
        for (int axis=0;axis<2;++axis) {
            GeoCoord anchor=g->axis[axis].anchor; int supplied=anchors<0?-1:geo_json_member(j,anchors,axis?"v":"u");
            if (supplied>=0) { int64_t value; if (!geo_json_integer(j,supplied,&value)||!geo_coord_in_range(value)) return wood_eng_fail(&c->engineering,"D28: grid anchor must be integer mm in D1 range"); anchor=value; }
            else if (g->axis[axis].source!=GEO_GRID_SOURCE_BODY_GAP) {
                if (!a->anchor_kind[axis]) return wood_eng_fail(&c->engineering,"D28: new panel axis needs an explicit origin or chosen face edge");
                anchor=a->anchor_kind[axis]==1?a->anchor[axis]:a->anchor_kind[axis]==2?(axis?host.bounds.min_v:host.bounds.min_u):(axis?host.bounds.max_v:host.bounds.max_u);
            }
            memset(&g->axis[axis],0,sizeof g->axis[axis]); g->axis[axis].source=GEO_GRID_SOURCE_BODY_GAP; g->axis[axis].body=1; g->axis[axis].anchor=anchor; g->axis[axis].anchor_explicit=true;
            for (int field=0;field<2;++field) { EngTarget target={0,id,axis,field}; EngDimensionSource source={0}; source.kind=ENG_APPLICATION; source.field=(field?ENG_U_GAP:ENG_U_PANEL)+axis; snprintf(source.ref,sizeof source.ref,"%s",a->id); if (!wood_eng_bind(&c->engineering,&target,&source)) return false; }
        }
        return true;
}

bool wood_grid_dimension_read(WoodEngineeringContext *w,GeoJson *j,int t,const EngTarget *target,GeoCoord *cache)
{
    if (geo_json_integer(j,t,cache)) {
        if (*cache<((!target->kind&&target->field)?0:1) || *cache>GEO_COORD_LIMIT) return wood_eng_fail(w,"I35: invalid direct dimension");
        return true;
    }
    EngDimensionSource source;
    if (!geo_json_keys(j,t,"source,override","") || !wood_eng_source_parse(w,j,geo_json_member(j,t,"source"),&source,true) || !wood_eng_bind(w,target,&source)) return false;
    EngBinding *b=wood_eng_binding(w,target); int o=geo_json_member(j,t,"override"); b->has_override=!geo_json_is_null(j,o);
    if (b->has_override && !wood_eng_source_parse(w,j,o,&b->override_value,false)) return false;
    *cache=target->field&& !target->kind?0:1; return true;
}

bool wood_grid_restore_engineering(WoodGridContext *c,GeoJson *j,int t)
{
    uint32_t id,pid; int along; WoodGridHost host;
    if (!geo_json_keys(j,t,"id,placement_id,mainAlong,axes","") || !wood_eng_u32(j,geo_json_member(j,t,"id"),&id,false) || !wood_eng_u32(j,geo_json_member(j,t,"placement_id"),&pid,false) || !c->host(c->user,pid,&host) || !wood_eng_axis(j,geo_json_member(j,t,"mainAlong"),&along)) return wood_eng_fail(&c->engineering,"I36: invalid engineering grid declaration");
    if (wood_grid_find(c->state,id)) return wood_eng_fail(&c->engineering,"I36: repeated engineering grid declaration");
    for (size_t i=0;i<c->state->count;++i) if (!c->state->items[i].is_subgrid && c->state->items[i].placement_id==pid) return wood_eng_fail(&c->engineering,"I10: duplicate main grid on placement");
    if (c->state->count==WOOD_GRID_MAX) return wood_eng_fail(&c->engineering,"I10: grid capacity exceeded");
    int axes=geo_json_member(j,t,"axes"); if (!geo_json_keys(j,axes,"u,v","")) return wood_eng_fail(&c->engineering,"I36: grid axes require u/v");
    WoodGridApplication *g=&c->state->items[c->state->count++]; memset(g,0,sizeof *g); g->id=id; g->placement_id=pid; g->main_along=along;
    for (int axis=0;axis<2;++axis) {
        int a=geo_json_member(j,axes,axis?"v":"u"); if (geo_json_is_null(j,a)) continue;
        char kind[16]; if (!geo_json_string(j,geo_json_member(j,a,"kind"),kind,sizeof kind)) return wood_eng_fail(&c->engineering,"I36: missing grid axis kind");
        GeoGridAxisDef *def=&g->axis[axis];
        if (!strcmp(kind,"panel")) {
            int64_t anchor; if (!geo_json_keys(j,a,"kind,panel,gap,anchor","") || !geo_json_integer(j,geo_json_member(j,a,"anchor"),&anchor) || !geo_coord_in_range(anchor)) return wood_eng_fail(&c->engineering,"I36: invalid panel grid anchor");
            def->source=GEO_GRID_SOURCE_BODY_GAP; def->anchor=anchor; def->anchor_explicit=true;
            EngTarget panel={0,id,axis,0},gap={0,id,axis,1};
            if (!wood_grid_dimension_read(&c->engineering,j,geo_json_member(j,a,"panel"),&panel,&def->body) || !wood_grid_dimension_read(&c->engineering,j,geo_json_member(j,a,"gap"),&gap,&def->gap)) return false;
        } else if (!strcmp(kind,"series")) {
            int64_t start,step,n; if (!geo_json_keys(j,a,"kind,start,step,count","") || !geo_json_integer(j,geo_json_member(j,a,"start"),&start)||!geo_coord_in_range(start) || !geo_json_integer(j,geo_json_member(j,a,"step"),&step)||step<1||step>GEO_COORD_LIMIT || !geo_json_integer(j,geo_json_member(j,a,"count"),&n)||n<1||n>WOOD_GRID_MAX_LINES) return wood_eng_fail(&c->engineering,"I36: invalid series axis");
            def->source=GEO_GRID_SOURCE_SERIES;def->start=start;def->step=step;def->series_count=(size_t)n;
        } else if (!strcmp(kind,"explicit")) {
            int coords=geo_json_member(j,a,"coords"); if (!geo_json_keys(j,a,"kind,coords","") || !geo_json_is_array(j,coords)) return wood_eng_fail(&c->engineering,"I36: invalid explicit axis");
            int n=geo_json_size(j,coords); if (n<1||n>WOOD_GRID_MAX_LINES) return wood_eng_fail(&c->engineering,"I10: grid coordinate capacity exceeded");
            def->source=GEO_GRID_SOURCE_EXPLICIT;def->count=(size_t)n;
            for(int k=0;k<n;++k) { int64_t v;if(!geo_json_integer(j,geo_json_at(j,coords,k),&v)||!geo_coord_in_range(v))return wood_eng_fail(&c->engineering,"I36: invalid grid coordinate");def->coords[k]=v; }
        } else return wood_eng_fail(&c->engineering,"I36: unknown grid axis kind");
    }
    return true;
}
