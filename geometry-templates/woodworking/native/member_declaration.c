#include "member_declaration.h"
#include <string.h>
static bool declaration_refuse(const char **error,const char *message)
{if(error)*error=message;return false;}
bool wood_member_declaration_capacity(const WoodMemberDeclarationContext *context,bool supplied,uint32_t id,const char **error)
{
    if(*context->count==context->capacity){
        bool existing=false;
        if(supplied)for(size_t i=0;i<*context->count;++i)if(context->members[i].id==id)existing=true;
        if(!existing)return declaration_refuse(error,"角材的數量超過上限");
    }
    return true;
}
bool wood_member_declaration_role(const char *name,WoodMemberRole *role,const char **error)
{
    if(!strcmp(name,"boundary"))*role=WOOD_MEMBER_ROLE_BOUNDARY;
    else if(!strcmp(name,"primary"))*role=WOOD_MEMBER_ROLE_PRIMARY;
    else if(!strcmp(name,"secondary"))*role=WOOD_MEMBER_ROLE_SECONDARY;
    else if(!strcmp(name,"custom"))*role=WOOD_MEMBER_ROLE_CUSTOM;
    else return declaration_refuse(error,"role 只能是 boundary、primary、secondary 或 custom");
    return true;
}
bool wood_member_declaration_priority(WoodMemberRole role,bool supplied,bool valid,GeoCoord priority,const char **error)
{
    if(role==WOOD_MEMBER_ROLE_CUSTOM){
        if(!supplied||!valid||priority<1)return declaration_refuse(error,"custom 角色需要 priority N（N 是 ≥1 的整數）");
    }else if(supplied)return declaration_refuse(error,"priority 只能配 custom 角色");
    return true;
}
bool wood_member_declare(WoodMemberDeclarationContext *context,uint32_t id,GeoCoord size_a,GeoCoord size_b,
    WoodMemberRole role,GeoCoord priority,const char **error)
{
    if(context->owned&&context->owned(context->user,id))return declaration_refuse(error,"I42: edit the owning assembly instance");
    for(size_t i=0;i<*context->count;++i)if(context->members[i].id==id){
        WoodMember updated;
        if(!wood_member_construct(id,0,size_a,size_b,true,role,priority,&updated))return false;
        updated.placed=context->members[i].placed;
        return context->replace(context->user,&context->members[i],&updated);
    }
    if(!wood_member_construct(id,0,size_a,size_b,true,role,priority,&context->members[*context->count]))
        return declaration_refuse(error,"角材的長度與 A/B 尺寸都要大於 0");
    ++*context->count;return true;
}
