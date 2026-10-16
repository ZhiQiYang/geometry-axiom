#include "engineering_operations.h"
#include <stdio.h>
#include <string.h>

bool wood_engineering_operation(WoodEngineeringOperations *operations,GeoJson *j,int t,const char *op)
{
    WoodEngineeringContext *w=&operations->grids.engineering;
    if(!strcmp(op,"unbind-source")) {
        EngTarget target;GeoCoord value;
        if(!geo_json_keys(j,t,"op,target","")||!wood_eng_target_parse(w,j,geo_json_member(j,t,"target"),&target))return wood_eng_fail(w,"I38: invalid unbind target");
        EngBinding *b=wood_eng_binding(w,&target);if(!b)return wood_eng_fail(w,"I38: target has no source binding");
        char error[512]="";if(!operations->rebuild_parameters(operations->user,error,sizeof error))return wood_eng_fail(w,error);if(!wood_eng_effective(w,b,&value,NULL,0))return false;
        w->write_dimension(w->user,&target,value);
        size_t k=(size_t)(b-w->state->bindings);memmove(b,b+1,(w->state->binding_count-k-1)*sizeof *b);memset(&w->state->bindings[--w->state->binding_count],0,sizeof *b);return true;
    }
    if (!strcmp(op,"publish-material") || !strcmp(op,"publish-method")) {
        char hash[65],*expected=NULL; int h=geo_json_member(j,t,"fingerprint");
        if (!geo_json_keys(j,t,"op,value","fingerprint")) return wood_eng_fail(w,"I35: unexpected publication operation fields");
        if (h>=0) { if (!geo_json_string(j,h,hash,sizeof hash)) return wood_eng_fail(w,"I34: invalid fingerprint"); expected=hash; }
        return !strcmp(op,"publish-material")?wood_eng_publish_material(w,j,geo_json_member(j,t,"value"),expected):wood_eng_publish_method(w,j,geo_json_member(j,t,"value"),expected);
    }
    if (!strcmp(op,"put-application")) return geo_json_keys(j,t,"op,value","")?wood_eng_put_application(w,j,geo_json_member(j,t,"value")):wood_eng_fail(w,"I35: unexpected application operation fields");
    if (!strcmp(op,"set-source") || !strcmp(op,"set-override")) {
        EngTarget target;
        bool override=!strcmp(op,"set-override");
        if (!geo_json_keys(j,t,override?"op,target,value":"op,target,source","") || !wood_eng_target_parse(w,j,geo_json_member(j,t,"target"),&target)) return wood_eng_fail(w,"I35: invalid source/override operation");
        uint32_t pid; int role; if (!wood_eng_target_context(w,&target,&pid,&role)) return false;
        if (target.kind) { WoodEngineeringTargetInfo fact={0};w->target(w->user,&target,&fact);if (!fact.placed) return wood_eng_fail(w,"D28: bind only an already placed timber"); }
        if (!override) { EngDimensionSource source; if (!wood_eng_source_parse(w,j,geo_json_member(j,t,"source"),&source,true)) return false; return wood_eng_bind(w,&target,&source); }
        EngBinding *b=wood_eng_binding(w,&target); if (!b) return wood_eng_fail(w,"D28: object override requires an explicit source binding");
        int value=geo_json_member(j,t,"value");
        if (geo_json_is_null(j,value)) { b->has_override=false; memset(&b->override_value,0,sizeof b->override_value); return true; }
        if (!wood_eng_source_parse(w,j,value,&b->override_value,false)) return false; b->has_override=true; return true;
    }
    if (!strcmp(op,"bind-grid") || !strcmp(op,"bind-timber")) {
        bool grid=!strcmp(op,"bind-grid"); uint32_t id; char appid[ENG_ID_MAX];
        if (!geo_json_keys(j,t,grid?"op,id,application":"op,id,application,slot",grid?"anchors,create":"") || !wood_eng_u32(j,geo_json_member(j,t,"id"),&id,false) || !geo_json_string(j,geo_json_member(j,t,"application"),appid,sizeof appid)) return wood_eng_fail(w,"D28: invalid binding operation");
        EngApplication *a=wood_eng_application(w,appid); if (!a) return wood_eng_fail(w,"D28: application not found");
        const EngMethodVersion *method=wood_eng_method(w,a->method.id,a->method.version); if (!method) return wood_eng_fail(w,"I34: application method not found");
        if (!grid) {
            char slot[16]; int r=-1; const char *names[]={"boundary","primary","secondary"};
            if (!geo_json_string(j,geo_json_member(j,t,"slot"),slot,sizeof slot)) return wood_eng_fail(w,"D28: timber binding requires an explicit role slot");
            for (int k=0;k<3;++k) if (!strcmp(slot,names[k])) r=k;
            EngTarget member={1,id,0,0};WoodEngineeringTargetInfo fact={0};bool exists=w->target(w->user,&member,&fact);
            if (r<0 || !exists || !fact.placed || fact.placement_id!=a->placement_id || fact.role!=r) return wood_eng_fail(w,"D28: timber must be placed on the application face with the selected matching role");
            for (int field=0;field<2;++field) { EngTarget target={1,id,0,field}; EngDimensionSource source={0}; source.kind=ENG_APPLICATION; source.field=ENG_BOUNDARY_A+r*2+field; snprintf(source.ref,sizeof source.ref,"%s",a->id); if (!wood_eng_bind(w,&target,&source)) return false; }
            return true;
        }
        return wood_grid_bind_engineering(&operations->grids,j,t,id,a,method);
    }
    return wood_eng_fail(w,"I35: unknown engineering operation");
}

bool wood_engineering_restore_member(WoodEngineeringOperations *operations,GeoJson *j,int t)
{
    WoodEngineeringContext *w=&operations->grids.engineering;
    uint32_t id;char role_name[16];WoodMemberRole role;GeoCoord priority=0;
    if (!geo_json_keys(j,t,"id,A,B,role","priority") || !wood_eng_u32(j,geo_json_member(j,t,"id"),&id,false) || !geo_json_string(j,geo_json_member(j,t,"role"),role_name,sizeof role_name)) return wood_eng_fail(w,"I36: invalid engineering timber declaration");
    if (!strcmp(role_name,"boundary")) role=WOOD_MEMBER_ROLE_BOUNDARY; else if (!strcmp(role_name,"primary")) role=WOOD_MEMBER_ROLE_PRIMARY; else if (!strcmp(role_name,"secondary")) role=WOOD_MEMBER_ROLE_SECONDARY; else if (!strcmp(role_name,"custom")) role=WOOD_MEMBER_ROLE_CUSTOM; else return wood_eng_fail(w,"I36: unknown timber role");
    int pt=geo_json_member(j,t,"priority");if(role==WOOD_MEMBER_ROLE_CUSTOM){int64_t v;if(!geo_json_integer(j,pt,&v)||v<1)return wood_eng_fail(w,"I36: custom role requires positive priority");priority=v;}else if(pt>=0)return wood_eng_fail(w,"I36: non-custom role cannot set priority");
    EngTarget lookup={1,id,0,0};WoodEngineeringTargetInfo fact={0};
    if (w->target(w->user,&lookup,&fact) || *operations->member_count==operations->member_capacity) return wood_eng_fail(w,"I10: timber ID exists or capacity exceeded");
    size_t i=(*operations->member_count)++;WoodMember *timber=&operations->members[i];
    if(!wood_member_construct(id,0,1,1,true,role,priority,timber))return false;
    operations->member_created(operations->user,i);
    EngTarget a={1,id,0,0},b={1,id,0,1};if(!wood_grid_dimension_read(w,j,geo_json_member(j,t,"A"),&a,&timber->size_a)||!wood_grid_dimension_read(w,j,geo_json_member(j,t,"B"),&b,&timber->size_b))return false;
    char error[256];if(!wood_engineering_rebuild(w,error,sizeof error))return wood_eng_fail(w,error);return true;
}
