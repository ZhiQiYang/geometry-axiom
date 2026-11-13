#include "assembly.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
static bool wood_bay_retired(const WoodAssemblyContext *,uint32_t);

/* Authoring validates sources and local topology; it never generates timber. */
const AsmRuleVersion *wood_assembly_rule(const WoodAssemblyContext *w,uint32_t id,uint32_t version)
{
    const AsmRuleVersion *found=NULL;
    for(size_t i=0;i<w->state->rule_count;++i){const AsmRuleVersion *r=&w->state->rules[i];
        if(r->id==id && ((!version&&(!found||r->version>found->version))||r->version==version))found=r;}
    return found;
}
AsmBinding *wood_assembly_binding(WoodAssemblyContext *w,uint32_t id)
{
    for(size_t i=0;i<w->state->binding_count;++i)if(w->state->bindings[i].id==id)return &w->state->bindings[i];
    return NULL;
}
bool wood_assembly_used(const WoodAssemblyContext *w){return w->state->rule_count||w->state->binding_count;}
static bool wood_asm_error(const WoodAssemblyContext *w,const char *format,...)
{
    *w->diagnostic=(AsmDiagnostic){0};
    char text[256];va_list args;va_start(args,format);vsnprintf(text,sizeof text,format,args);va_end(args);
    return wood_eng_fail(&w->engineering,text);
}
static bool wood_asm_rule_immutable(const WoodAssemblyContext *w,uint32_t id,uint32_t version)
{
    bool result=wood_asm_error(w,"D32: published rule %u@%u is immutable",id,version);
    (*w->diagnostic)=(AsmDiagnostic){2,id,0,version};return result;
}
static bool wood_asm_name(GeoJson *j,int t,char out[ASM_NAME_MAX])
{return geo_json_string(j,t,out,ASM_NAME_MAX)&&out[0];}
static bool wood_asm_enum(GeoJson *j,int t,const char *choices,bool nullable)
{
    char value[40];return (nullable&&geo_json_is_null(j,t))||
        (geo_json_string(j,t,value,sizeof value)&&geo_json_csv_has(choices,value));
}
static bool wood_asm_ids(GeoJson *j,int array,uint32_t *ids,size_t *count,size_t limit)
{
    if(!geo_json_is_array(j,array))return false;int n=geo_json_size(j,array);
    if(n<1||(size_t)n>limit)return false;*count=(size_t)n;
    for(int i=0;i<n;++i){int t=geo_json_at(j,array,i);if(!wood_eng_u32(j,geo_json_member(j,t,"id"),&ids[i],true))return false;
        for(int k=0;k<i;++k)if(ids[k]==ids[i])return false;}
    return true;
}
static bool wood_asm_has(const uint32_t *ids,size_t count,uint32_t id)
{for(size_t i=0;i<count;++i)if(ids[i]==id)return true;return false;}
static bool wood_asm_validate_rule(WoodAssemblyContext *w,GeoJson *j,int t,AsmRuleVersion *r)
{
    uint32_t slots[ASM_SLOT_MAX],members[ASM_MEMBER_MAX],joints[ASM_JOINT_MAX];size_t ns,nm,nj;
    char scopes[ASM_JOINT_MAX][65];uint32_t ends[ASM_JOINT_MAX*2],end_joints[ASM_JOINT_MAX*2];int end_types[ASM_JOINT_MAX*2],end_count=0;
    memset(r,0,sizeof *r);
    if(!geo_json_keys(j,t,"id,version,name,slots,members,joints","")||
       !wood_eng_u32(j,geo_json_member(j,t,"id"),&r->id,true)||!wood_eng_u32(j,geo_json_member(j,t,"version"),&r->version,true)||
       !wood_asm_name(j,geo_json_member(j,t,"name"),r->name))return wood_asm_error(w,"D32: rule needs positive id/version, name and typed slots/members/joints");
    int sa=geo_json_member(j,t,"slots"),ma=geo_json_member(j,t,"members"),ja=geo_json_member(j,t,"joints");
    if(!wood_asm_ids(j,sa,slots,&ns,ASM_SLOT_MAX)||!wood_asm_ids(j,ma,members,&nm,ASM_MEMBER_MAX)||!wood_asm_ids(j,ja,joints,&nj,ASM_JOINT_MAX))
        return wood_asm_error(w,"I40/CAPACITY: rule %u needs 1..8 unique slots, 1..12 unique members and 1..16 unique joints",r->id);
    for(size_t i=0;i<ns;++i){int s=geo_json_at(j,sa,(int)i);char name[ASM_NAME_MAX];
        if(!geo_json_keys(j,s,"id,name","")||!wood_asm_name(j,geo_json_member(j,s,"name"),name))return wood_asm_error(w,"I40: slot %u needs a name; unknown fields are rejected",slots[i]);}
    for(size_t i=0;i<nm;++i){int m=geo_json_at(j,ma,(int)i);uint32_t sid;
        if(!geo_json_keys(j,m,"id,slotId","")||!wood_eng_u32(j,geo_json_member(j,m,"slotId"),&sid,true)||!wood_asm_has(slots,ns,sid))return wood_asm_error(w,"I40: member %u refers to a missing slot",members[i]);}
    for(size_t i=0;i<nj;++i){int a=geo_json_at(j,ja,(int)i);char kind[32],end[16];uint32_t term[2],target;int et[2],nt;
        if(!geo_json_string(j,geo_json_member(j,a,"kind"),kind,sizeof kind)||
           !geo_json_string(j,geo_json_member(j,a,"scope"),scopes[i],sizeof scopes[i])||!scopes[i][0])return wood_asm_error(w,"I40: joint %u needs kind and stable junction scope",joints[i]);
        for(size_t k=0;k<i;++k)if(!strcmp(scopes[k],scopes[i]))return wood_asm_error(w,"I40: joints %u and %u conflict at scope %s",joints[k],joints[i],scopes[i]);
        if(!strcmp(kind,"end-to-side")){
            if(!geo_json_keys(j,a,"id,kind,scope,terminatedMember,targetMember,end,side,dir","")||
               !wood_eng_u32(j,geo_json_member(j,a,"terminatedMember"),&term[0],true)||!wood_eng_u32(j,geo_json_member(j,a,"targetMember"),&target,true)||
               !geo_json_string(j,geo_json_member(j,a,"end"),end,sizeof end)||(strcmp(end,"start")&&strcmp(end,"finish")))return wood_asm_error(w,"I40: joint %u has invalid endpoint definition",joints[i]);
            et[0]=!strcmp(end,"finish");nt=1;
        }else if(!strcmp(kind,"ortho-split")){
            int split=geo_json_member(j,a,"splitMembers");
            if(!geo_json_keys(j,a,"id,kind,scope,continuousMember,splitMembers,side,dir","")||
               !wood_eng_u32(j,geo_json_member(j,a,"continuousMember"),&target,true)||!geo_json_is_array(j,split)||geo_json_size(j,split)!=2||
               !wood_eng_u32(j,geo_json_at(j,split,0),&term[0],true)||!wood_eng_u32(j,geo_json_at(j,split,1),&term[1],true)||term[0]==term[1])return wood_asm_error(w,"I40: joint %u needs one continuous and two distinct split members",joints[i]);
            et[0]=1;et[1]=0;nt=2;
        }else return wood_asm_error(w,"I40: joint %u has unknown kind; nested rules are unsupported",joints[i]);
        if(!wood_asm_has(members,nm,target)||!wood_asm_enum(j,geo_json_member(j,a,"side"),"+u,-u,+v,-v",false)||!wood_asm_enum(j,geo_json_member(j,a,"dir"),"u,v",false))return wood_asm_error(w,"I40: joint %u has missing target or invalid local side/direction",joints[i]);
        for(int k=0;k<nt;++k){if(term[k]==target||!wood_asm_has(members,nm,term[k]))return wood_asm_error(w,"I40: joint %u needs distinct existing members",joints[i]);
            for(int q=0;q<end_count;++q)if(ends[q]==term[k]&&end_types[q]==et[k])return wood_asm_error(w,"I40: joints %u and %u assign the same endpoint of member %u",end_joints[q],joints[i],term[k]);
            ends[end_count]=term[k];end_types[end_count]=et[k];end_joints[end_count++]=joints[i];}
    }
    if(!geo_json_canonical(j,t,r->content,sizeof r->content))return wood_asm_error(w,"CAPACITY: assembly rule exceeds 8191 UTF-8 bytes");
    geo_sha256(r->content,strlen(r->content),r->fingerprint);return true;
}
bool wood_assembly_rule_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmRuleVersion *out)
{return wood_asm_validate_rule(w,j,t,out);}
bool wood_assembly_publish(WoodAssemblyContext *w,GeoJson *j,int t,const char *expected)
{
    AsmRuleVersion rule;if(!wood_asm_validate_rule(w,j,t,&rule))return false;
    if(expected&&strcmp(expected,rule.fingerprint))return wood_asm_error(w,"I41: rule %u@%u fingerprint mismatch",rule.id,rule.version);
    const AsmRuleVersion *old=wood_assembly_rule(w,rule.id,rule.version);
    if(old)return !strcmp(old->fingerprint,rule.fingerprint)||wood_asm_rule_immutable(w,rule.id,rule.version);
    if(w->state->rule_count==ASM_RULE_MAX)return wood_asm_error(w,"CAPACITY: at most 32 published assembly versions");
    w->state->rules[w->state->rule_count++]=rule;return true;
}
/* Compare with transaction-entry identities, not only the mutable candidate.
 * Removed versions may stay absent after explicit unbinding; an identity that
 * reappears must retain its original content, including delete/copy/reinsert. */
bool wood_assembly_versions_immutable(const WoodAssemblyContext *before,const WoodAssemblyContext *after)
{
    for(size_t i=0;i<before->state->rule_count;++i){const AsmRuleVersion *old=&before->state->rules[i];
        const AsmRuleVersion *next=wood_assembly_rule(after,old->id,old->version);
        if(next&&strcmp(old->fingerprint,next->fingerprint))return wood_asm_rule_immutable(after,old->id,old->version);
    }
    return true;
}
static bool wood_asm_binding_slot_values(WoodAssemblyContext *w,GeoJson *j,int s,AsmBinding *b,uint32_t id,bool resolve)
{
    for(int axis=0;axis<2;++axis){int value=geo_json_member(j,s,axis?"B":"A");
        if(geo_json_is_null(j,value)){b->complete=false;continue;}
        (*w->parameter_dimension_error)=(GeoParameterRef){0};
        EngDimensionSource source={0};EngTarget target={1,0,0,axis};GeoCoord effective;char path[192];
        if(!wood_eng_source_parse(&w->engineering,j,value,&source,false)||source.kind==ENG_APPLICATION||(resolve&&!(w->evaluation&&w->evaluation->slot_dimension?w->evaluation->slot_dimension(w->evaluation->user,b->id,id,axis,&source,&effective,path,sizeof path):wood_eng_resolve(&w->engineering,&source,&target,UINT32_MAX,0,&effective,path,sizeof path)))){
            char error[256];snprintf(error,sizeof error,"%s",w->engineering.error);
            bool result=wood_asm_error(w,"I40: binding %u slot %u.%c: %.155s",b->id,id,axis?'B':'A',error);
            if(source.kind==ENG_PARAMETER && (*w->parameter_dimension_error).set &&
                (*w->parameter_dimension_error).parameter_id==source.parameter.parameter_id &&
                (*w->parameter_dimension_error).field_id==source.parameter.field_id)
                (*w->diagnostic)=(AsmDiagnostic){1,source.parameter.parameter_id,source.parameter.field_id,0};
            return result;}
    }
    const char *keys[]={"contactFace","orientation"};for(int axis=0;axis<2;++axis){int value=geo_json_member(j,s,keys[axis]);
        if(!wood_asm_enum(j,value,"A,B",true))return wood_asm_error(w,"I40: binding %u slot %u needs explicit A/B or unset %s",b->id,id,keys[axis]);
        if(geo_json_is_null(j,value))b->complete=false;}
    return true;
}
static bool wood_asm_binding_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmBinding *b,bool resolve)
{
    memset(b,0,sizeof *b);int rule=geo_json_member(j,t,"rule"),array=geo_json_member(j,t,"slots");
    if(!geo_json_keys(j,t,"id,name,rule,slots","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&b->id,true)||!wood_asm_name(j,geo_json_member(j,t,"name"),b->name)||
       !geo_json_keys(j,rule,"id,version","")||!wood_eng_u32(j,geo_json_member(j,rule,"id"),&b->rule_id,true)||!wood_eng_u32(j,geo_json_member(j,rule,"version"),&b->rule_version,true))return wood_asm_error(w,"D33: invalid binding identity or fixed rule reference");
    const AsmRuleVersion *r=wood_assembly_rule(w,b->rule_id,b->rule_version);if(!r)return wood_asm_error(w,"I40: binding %u refers to missing rule %u@%u",b->id,b->rule_id,b->rule_version);
    GeoJson definition;if(!w->json_parse(w->user,&definition,r->content)){geo_json_free(&definition);return wood_asm_error(w,"I40: invalid stored rule");}
    uint32_t ids[ASM_SLOT_MAX],seen[ASM_SLOT_MAX];size_t n;bool ok=wood_asm_ids(&definition,geo_json_member(&definition,0,"slots"),ids,&n,ASM_SLOT_MAX);geo_json_free(&definition);
    if(!ok||!geo_json_is_array(j,array)||geo_json_size(j,array)!=(int)n)return wood_asm_error(w,"I40: binding %u must explicitly map every fixed rule slot",b->id);
    b->complete=true;
    for(size_t i=0;i<n;++i){int s=geo_json_at(j,array,(int)i);uint32_t id;
        if(!geo_json_keys(j,s,"slotId,A,B,contactFace,orientation","")||!wood_eng_u32(j,geo_json_member(j,s,"slotId"),&id,true)||!wood_asm_has(ids,n,id)||wood_asm_has(seen,i,id))return wood_asm_error(w,"I40: binding %u has missing, duplicate or unknown slots",b->id);
        seen[i]=id;
        if(resolve&&w->evaluation&&w->evaluation->slot_definition&&!w->evaluation->slot_definition(w->evaluation->user,b->id,id))return false;
        if(resolve&&w->evaluation&&w->evaluation->slot_record){
            char text[ASM_RECORD_MAX];GeoJson selected={0};uint32_t actual;
            if(!w->evaluation->slot_record(w->evaluation->user,b->id,id,text,sizeof text))return false;
            bool valid=w->json_parse(w->user,&selected,text)&&geo_json_keys(&selected,0,"slotId,A,B,contactFace,orientation","")&&
                wood_eng_u32(&selected,geo_json_member(&selected,0,"slotId"),&actual,true)&&actual==id;
            if(!valid){geo_json_free(&selected);return wood_asm_error(w,"I40: binding %u has missing, duplicate or unknown slots",b->id);}
            bool resolved=wood_asm_binding_slot_values(w,&selected,0,b,id,resolve);geo_json_free(&selected);if(!resolved)return false;
        }else if(!wood_asm_binding_slot_values(w,j,s,b,id,resolve))return false;
    }
    if(!geo_json_canonical(j,t,b->content,sizeof b->content))return wood_asm_error(w,"CAPACITY: binding exceeds 8191 UTF-8 bytes");return true;
}
bool wood_assembly_put_binding(WoodAssemblyContext *w,GeoJson *j,int t)
{
    AsmBinding value;if(!wood_asm_binding_parse(w,j,t,&value,false))return false;AsmBinding *b=wood_assembly_binding(w,value.id);
    if(!b){if(w->state->binding_count==ASM_BINDING_MAX)return wood_asm_error(w,"CAPACITY: at most 64 assembly bindings");b=&w->state->bindings[w->state->binding_count++];}
    *b=value;return w->declare_binding?w->declare_binding(w->user,value.id):true;
}
bool wood_assembly_rebuild(WoodAssemblyContext *w,char *error,size_t cap)
{
    if(w->state->loading){snprintf(error,cap,"I41: truncated assembly block");return false;}
    if(w->evaluation&&w->evaluation->rule_definition)for(size_t i=0;i<w->state->rule_count;++i){const AsmRuleVersion *r=&w->state->rules[i];if(!w->evaluation->rule_definition(w->evaluation->user,r->id,r->version)){snprintf(error,cap,"%s",w->engineering.error);return false;}}
    for(size_t i=0;i<w->state->binding_count;++i){AsmBinding b;const AsmBinding *stored=&w->state->bindings[i];bool ok=w->evaluation&&w->evaluation->binding?w->evaluation->binding(w->evaluation->user,stored,&b):wood_assembly_binding_rebuild_direct(w,stored,&b);
        if(!ok){snprintf(error,cap,"%s",w->engineering.error);return false;}w->state->bindings[i]=b;}
    return true;
}
bool wood_assembly_binding_rebuild_direct(WoodAssemblyContext *w,const AsmBinding *stored,AsmBinding *out)
{GeoJson j;bool ok=w->json_parse(w->user,&j,stored->content)&&wood_asm_binding_parse(w,&j,0,out,true);geo_json_free(&j);return ok;}
bool wood_assembly_slot_dimension_direct(WoodAssemblyContext *w,uint32_t binding_id,uint32_t slot_id,int axis,GeoCoord *out,char *path,size_t cap)
{
    AsmBinding *binding=wood_assembly_binding(w,binding_id);if(!binding||axis<0||axis>1)return false;GeoJson j;
    if(!w->json_parse(w->user,&j,binding->content)){geo_json_free(&j);return false;}int slots=geo_json_member(&j,0,"slots"),selected=-1;
    for(int i=0;i<geo_json_size(&j,slots);++i){int t=geo_json_at(&j,slots,i);uint32_t id;if(wood_eng_u32(&j,geo_json_member(&j,t,"slotId"),&id,true)&&id==slot_id){selected=t;break;}}
    EngDimensionSource source;EngTarget target={1,0,0,axis};bool ok=selected>=0&&!geo_json_is_null(&j,geo_json_member(&j,selected,axis?"B":"A"))&&wood_eng_source_parse(&w->engineering,&j,geo_json_member(&j,selected,axis?"B":"A"),&source,false)&&source.kind!=ENG_APPLICATION&&wood_eng_resolve(&w->engineering,&source,&target,UINT32_MAX,0,out,path,cap);
    geo_json_free(&j);return ok;
}

/* A legacy spec edit previews assembly consumers even without geometry. */
bool wood_assembly_dimensions_changed(const WoodAssemblyContext *before,const WoodAssemblyContext *after)
{
    for(size_t i=0;i<before->state->binding_count;++i){GeoJson j;
        if(!before->json_parse(before->user,&j,before->state->bindings[i].content)){geo_json_free(&j);return true;}
        int slots=geo_json_member(&j,0,"slots");bool changed=false;
        for(int k=0;k<geo_json_size(&j,slots)&&!changed;++k)for(int axis=0;axis<2&&!changed;++axis){
            int t=geo_json_member(&j,geo_json_at(&j,slots,k),axis?"B":"A");if(geo_json_is_null(&j,t))continue;
            EngDimensionSource src;EngTarget target={1,0,0,axis};GeoCoord a,b;char path[192];
            if(!wood_eng_source_parse((WoodEngineeringContext *)&before->engineering,&j,t,&src,false)||!wood_eng_resolve((WoodEngineeringContext *)&before->engineering,&src,&target,UINT32_MAX,0,&a,path,sizeof path)||
               !wood_eng_resolve((WoodEngineeringContext *)&after->engineering,&src,&target,UINT32_MAX,0,&b,path,sizeof path)||a!=b)changed=true;
        }
        geo_json_free(&j);if(changed)return true;
    }
    return false;
}
bool wood_assembly_operation(WoodAssemblyContext *w,GeoJson *j,int t)
{
    char op[32];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return wood_asm_error(w,"I40: assembly operation needs op");
    if(!strcmp(op,"publish-rule"))return geo_json_keys(j,t,"op,value","")?wood_assembly_publish(w,j,geo_json_member(j,t,"value"),NULL):wood_asm_error(w,"I40: invalid publish operation");
    if(!strcmp(op,"create-binding")){
        uint32_t id;int value=geo_json_member(j,t,"value");
        if(!geo_json_keys(j,t,"op,value","")||!wood_eng_u32(j,geo_json_member(j,value,"id"),&id,true))return wood_asm_error(w,"I40: invalid new binding identity");
        if(wood_assembly_binding(w,id))return wood_asm_error(w,"I40: new binding %u already exists; edit it explicitly",id);
        return wood_assembly_put_binding(w,j,value);
    }
    if(!strcmp(op,"edit-binding")){
        uint32_t id,value_id;char expected[65],actual[65];int value=geo_json_member(j,t,"value");
        if(!geo_json_keys(j,t,"op,id,expectedFingerprint,value","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true)||
           !wood_eng_u32(j,geo_json_member(j,value,"id"),&value_id,true)||value_id!=id||
           !geo_json_string(j,geo_json_member(j,t,"expectedFingerprint"),expected,sizeof expected)||strlen(expected)!=64)
            return wood_asm_error(w,"I40: invalid explicit binding edit");
        for(size_t i=0;i<64;++i)if(!((expected[i]>='0'&&expected[i]<='9')||(expected[i]>='a'&&expected[i]<='f')))
            return wood_asm_error(w,"I40: invalid binding fingerprint");
        AsmBinding *b=wood_assembly_binding(w,id);if(!b)return wood_asm_error(w,"I40: edited binding %u does not exist",id);
        geo_sha256(b->content,strlen(b->content),actual);
        if(strcmp(expected,actual))return wood_asm_error(w,"STALE: binding %u changed; reopen before editing",id);
        return wood_assembly_put_binding(w,j,value);
    }
    if(!strcmp(op,"put-binding"))return geo_json_keys(j,t,"op,value","")?wood_assembly_put_binding(w,j,geo_json_member(j,t,"value")):wood_asm_error(w,"I40: invalid binding operation");
    if(!strcmp(op,"delete-binding")){
        uint32_t id;if(!geo_json_keys(j,t,"op,id","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true))return wood_asm_error(w,"I40: invalid binding id");
        AsmBinding *b=wood_assembly_binding(w,id);if(!b)return wood_asm_error(w,"I40: binding %u does not exist",id);size_t at=(size_t)(b-w->state->bindings);
        memmove(b,b+1,(w->state->binding_count-at-1)*sizeof *b);memset(&w->state->bindings[--w->state->binding_count],0,sizeof *b);w->drop_position(w->user,false,id);return true;
    }
    if(!strcmp(op,"delete-rule")){
        uint32_t id,version;if(!geo_json_keys(j,t,"op,id,version","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true)||!wood_eng_u32(j,geo_json_member(j,t,"version"),&version,true))return wood_asm_error(w,"I40: invalid rule identity");
        const AsmRuleVersion *r=wood_assembly_rule(w,id,version);if(!r)return wood_asm_error(w,"I40: rule version does not exist");size_t at=(size_t)(r-w->state->rules);
        memmove(&w->state->rules[at],&w->state->rules[at+1],(w->state->rule_count-at-1)*sizeof *r);memset(&w->state->rules[--w->state->rule_count],0,sizeof *r);
        if(!wood_assembly_rule(w,id,0))w->drop_position(w->user,true,id);return true;
    }
    if(!strcmp(op,"copy-rule")){
        uint32_t id,version,next;if(!geo_json_keys(j,t,"op,id,version,newId","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true)||!wood_eng_u32(j,geo_json_member(j,t,"version"),&version,true)||!wood_eng_u32(j,geo_json_member(j,t,"newId"),&next,true)||wood_assembly_rule(w,next,0))return wood_asm_error(w,"I40: copy needs an unused rule identity");
        const AsmRuleVersion *r=wood_assembly_rule(w,id,version);if(!r)return wood_asm_error(w,"I40: copied rule does not exist");GeoJson copy;
        if(!w->json_parse(w->user,&copy,r->content)){geo_json_free(&copy);return false;}copy.tokens[geo_json_member(&copy,0,"id")].number=next;copy.tokens[geo_json_member(&copy,0,"version")].number=1;
        bool ok=wood_assembly_publish(w,&copy,0,NULL);geo_json_free(&copy);return ok;
    }
    return w->other_operation(w->user,j,t); /* Explicit unbind/delete shares one candidate. */
}

AsmInstance *wood_assembly_instance(WoodAssemblyContext *w,uint32_t id)
{for(size_t i=0;i<w->state->instance_count;++i)if(w->state->instances[i].id==id)return &w->state->instances[i];return NULL;}
bool wood_assembly_owned(const WoodAssemblyContext *w,uint32_t id)
{for(size_t i=0;i<w->state->owner_count;++i)if(w->state->owners[i].timber==id)return true;return false;}
static bool wood_asm_hash_token(GeoJson *j,int t,char hash[65])
{if(!geo_json_string(j,t,hash,65)||strlen(hash)!=64)return false;for(int i=0;i<64;++i)if(!((hash[i]>='0'&&hash[i]<='9')||(hash[i]>='a'&&hash[i]<='f')))return false;return true;}
static bool wood_asm_bay_mapping(WoodAssemblyContext *,GeoJson *,int,AsmInstance *);
static bool wood_asm_bay_operation(WoodAssemblyContext *,GeoJson *,int,const char *,AsmInstance *);
static bool wood_asm_instance_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmInstance *a)
{
    if(geo_json_member(j,t,"layout")>=0)return wood_assembly_bay_parse(w,j,t,a);
    memset(a,0,sizeof *a);int r=geo_json_member(j,t,"rule"),m=geo_json_member(j,t,"members");
    if(!geo_json_keys(j,t,"id,name,bindingId,rule,surfaceId,members","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&a->id,true)||!wood_asm_name(j,geo_json_member(j,t,"name"),a->name)||
       !wood_eng_u32(j,geo_json_member(j,t,"bindingId"),&a->binding_id,true)||
       !geo_json_keys(j,r,"id,version,fingerprint","")||!wood_eng_u32(j,geo_json_member(j,r,"id"),&a->rule_id,true)||!wood_eng_u32(j,geo_json_member(j,r,"version"),&a->rule_version,true)||!wood_asm_hash_token(j,geo_json_member(j,r,"fingerprint"),a->rule_hash)||
       !geo_json_is_array(j,m)||geo_json_size(j,m)!=3)return wood_asm_error(w,"D34/UNSUPPORTED: instance needs exactly three typed members and fixed sources");
    if(!wood_eng_u32(j,geo_json_member(j,t,"surfaceId"),&a->surface_id,true))return wood_asm_error(w,"I42: select a valid instance surface");
    const AsmRuleVersion *rule=wood_assembly_rule(w,a->rule_id,a->rule_version);AsmBinding *binding=wood_assembly_binding(w,a->binding_id);
    if(!rule||strcmp(rule->fingerprint,a->rule_hash)||!binding||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version)return wood_asm_error(w,"I42: missing binding or mismatched fixed rule fingerprint/version");
    GeoJson q;if(!w->json_parse(w->user,&q,rule->content)){geo_json_free(&q);return false;}int members=geo_json_member(&q,0,"members"),joints=geo_json_member(&q,0,"joints");bool ok=geo_json_size(&q,members)==3&&geo_json_size(&q,joints)==2;int sec=-1,primary=0;
    for(int i=0;i<3&&ok;++i){int v=geo_json_at(j,m,i),e=geo_json_member(j,v,"ends");char role[16],dir[8],depth[8];
        ok=geo_json_keys(j,v,"memberId,role,guideId,dir,depthSide,ends","")&&wood_eng_u32(j,geo_json_member(j,v,"memberId"),&a->member[i],true)&&
           geo_json_string(j,geo_json_member(j,v,"role"),role,sizeof role)&&geo_json_string(j,geo_json_member(j,v,"dir"),dir,sizeof dir)&&geo_json_string(j,geo_json_member(j,v,"depthSide"),depth,sizeof depth)&&!strcmp(depth,"+n")&&geo_json_keys(j,e,"start,finish","");
        if(!ok)break;
        if(!wood_eng_u32(j,geo_json_member(j,v,"guideId"),&a->guide[i],true)){geo_json_free(&q);return wood_asm_error(w,"I42: member %u needs a valid selected guide",a->member[i]);}
        a->secondary[i]=!strcmp(role,"secondary");if(a->secondary[i]){if(sec>=0)ok=false;sec=i;}else if(!strcmp(role,"primary"))++primary;else ok=false;
        if(strcmp(dir,a->secondary[i]?"+u":"+v"))ok=false;
        for(int k=0;k<i;++k)if(a->member[k]==a->member[i]||a->guide[k]==a->guide[i])ok=false;
        bool found=false;for(int k=0;k<3;++k){uint32_t id;if(wood_eng_u32(&q,geo_json_member(&q,geo_json_at(&q,members,k),"id"),&id,true)&&id==a->member[i])found=true;}if(!found)ok=false;
        for(int k=0;k<2&&ok;++k){int end=geo_json_member(j,e,k?"finish":"start");char kind[16];ok=geo_json_string(j,geo_json_member(j,end,"kind"),kind,sizeof kind)&&!strcmp(kind,a->secondary[i]?"member":"timber")&&geo_json_keys(j,end,a->secondary[i]?"kind,memberId":"kind,id","");
            if(ok&&!wood_eng_u32(j,geo_json_member(j,end,a->secondary[i]?"memberId":"id"),&a->ends[i][k],true)){geo_json_free(&q);return wood_asm_error(w,"I42: member %u needs a valid selected %s support",a->member[i],k?"finish":"start");}}
    }
    if(sec<0||primary!=2)ok=false;
    for(int k=0;k<2&&ok;++k){int target=-1;for(int i=0;i<3;++i)if(a->member[i]==a->ends[sec][k]&&!a->secondary[i])target=i;if(target<0||a->ends[sec][0]==a->ends[sec][1]){ok=false;break;}
        bool found=false;for(int h=0;h<2;++h){int joint=geo_json_at(&q,joints,h);uint32_t term,to;char kind[24],end[16],side[8],dir[8];
            if(geo_json_string(&q,geo_json_member(&q,joint,"kind"),kind,sizeof kind)&&!strcmp(kind,"end-to-side")&&wood_eng_u32(&q,geo_json_member(&q,joint,"terminatedMember"),&term,true)&&term==a->member[sec]&&wood_eng_u32(&q,geo_json_member(&q,joint,"targetMember"),&to,true)&&to==a->member[target]&&geo_json_string(&q,geo_json_member(&q,joint,"end"),end,sizeof end)&&!strcmp(end,k?"finish":"start")&&geo_json_string(&q,geo_json_member(&q,joint,"side"),side,sizeof side)&&!strcmp(side,k?"-u":"+u")&&geo_json_string(&q,geo_json_member(&q,joint,"dir"),dir,sizeof dir)&&!strcmp(dir,"u"))found=true;
        }if(!found)ok=false;
    }
    geo_json_free(&q);return ok||wood_asm_error(w,"D34/UNSUPPORTED: only two +v primary and one +u secondary with inward end-to-side joints");
}
bool wood_assembly_instance_definition_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmInstance *out)
{
    AsmInstance a;int source=geo_json_member(j,t,"source"),mapping=geo_json_member(j,t,"mapping");
    if(!geo_json_keys(j,t,"source,mapping","")||!wood_asm_instance_parse(w,j,source,&a))return false;
    if(a.bay_repeat){
        if(!wood_asm_bay_mapping(w,j,mapping,&a))return false;
        if(!geo_json_canonical(j,t,a.content,sizeof a.content))return wood_assembly_bay_failure(w,"CAPACITY","CAPACITY","I69",a.id,0,0,"source and mapping <= 8191 UTF-8 bytes","oversized instance record");
        *out=a;return true;
    }
    if(
       !geo_json_is_array(j,mapping)||geo_json_size(j,mapping)!=3)return wood_asm_error(w,"I42: invalid or duplicate instance mapping");
    for(int i=0;i<3;++i){int item=geo_json_at(j,mapping,i);uint32_t member,timber;
        if(!geo_json_keys(j,item,"memberId,timberId","")||!wood_eng_u32(j,geo_json_member(j,item,"memberId"),&member,true)||
           !wood_eng_u32(j,geo_json_member(j,item,"timberId"),&timber,true))return wood_asm_error(w,"I42: invalid or duplicate instance mapping");
        int index=-1;for(int m=0;m<3;++m)if(a.member[m]==member)index=m;
        if(index<0||a.timber[index])return wood_asm_error(w,"I42: duplicate/missing mapped member");a.timber[index]=timber;
    }
    if(!geo_json_canonical(j,t,a.content,sizeof a.content))return wood_asm_error(w,"CAPACITY: instance exceeds 8191 UTF-8 bytes");
    *out=a;return true;
}

bool wood_assembly_generation_integrity(const WoodAssemblyContext *w)
{
    size_t expected=0;bool repeat=false;
    for(size_t k=0;k<w->state->instance_count;++k){const AsmInstance *a=&w->state->instances[k];expected+=wood_assembly_mapping_count(a);repeat|=a->bay_repeat;}
    if((repeat?w->state->owner_count!=expected:w->state->owner_count!=w->state->instance_count*3)||expected>ASM_OWNER_MAX)return wood_asm_error(w,"I42: orphan owned records or missing instance mapping");
    if(w->state->instance_count&&!w->state->generation_required)return wood_asm_error(w,"I42: missing required generation capability");
    if(repeat&&!w->state->bay_required)return wood_asm_error(w,"I69: missing required assembly-bay-repeat/1 capability");
    if(w->bay_report)for(size_t i=0;i<w->bay_report->retired_count;++i)if(w->member(w->user,w->bay_report->retired[i],NULL))return wood_asm_error(w,"I69: a removed owned timber id cannot be reused in this candidate");
    for(size_t i=0;i<w->state->owner_count;++i){const AsmOwner *o=&w->state->owners[i];bool found=false;
        for(size_t k=0;k<w->state->instance_count;++k){const AsmInstance *a=&w->state->instances[k];for(size_t m=0;m<wood_assembly_mapping_count(a);++m){AsmMapping map=wood_assembly_mapping_at(a,m);if(o->instance==a->id&&wood_assembly_identity_equal(wood_assembly_owner_identity(o),map.identity)&&o->timber==map.timber)found=true;}}
        if(!found||!w->member(w->user,o->timber,NULL))return wood_asm_error(w,"I42: invalid owned mapping");
        for(size_t k=0;k<i;++k)if(w->state->owners[k].timber==o->timber||(w->state->owners[k].instance==o->instance&&wood_assembly_identity_equal(wood_assembly_owner_identity(&w->state->owners[k]),wood_assembly_owner_identity(o))))return wood_asm_error(w,"I42: duplicate owner identity");
    }return true;
}
static int wood_asm_member_index(const AsmInstance *a,uint32_t id)
{for(int i=0;i<3;++i)if(a->member[i]==id)return i;return -1;}
static bool wood_asm_member_definition(WoodAssemblyContext *w,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{if(w->evaluation&&w->evaluation->generated)return w->evaluation->generated(w->evaluation->user,a,m,out);return wood_assembly_member_definition_direct(w,a,m,out);}
bool wood_assembly_member_definition_direct(WoodAssemblyContext *w,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{
    if(a->bay_repeat)return m>=0&&(size_t)m<a->mapping_count&&wood_assembly_bay_member_definition_direct(w,a,a->mapping[m].identity,out);
    AsmBinding *binding=wood_assembly_binding(w,a->binding_id);const AsmRuleVersion *rule=wood_assembly_rule(w,a->rule_id,a->rule_version);
    if(!binding||!binding->complete||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version||!rule||strcmp(a->rule_hash,rule->fingerprint))return wood_asm_error(w,"I42: incomplete or changed instance binding/rule");
    GeoJson q,b;bool ok=w->json_parse(w->user,&q,rule->content);if(!ok){geo_json_free(&q);return false;}ok=w->json_parse(w->user,&b,binding->content);if(!ok){geo_json_free(&q);geo_json_free(&b);return false;}
    uint32_t slot=0;int members=geo_json_member(&q,0,"members"),slots=geo_json_member(&b,0,"slots");
    for(int i=0;i<geo_json_size(&q,members);++i){uint32_t id;int t=geo_json_at(&q,members,i);if(wood_eng_u32(&q,geo_json_member(&q,t,"id"),&id,true)&&id==a->member[m])wood_eng_u32(&q,geo_json_member(&q,t,"slotId"),&slot,true);}
    int selected=-1;for(int i=0;i<geo_json_size(&b,slots);++i){uint32_t id;int t=geo_json_at(&b,slots,i);if(wood_eng_u32(&b,geo_json_member(&b,t,"slotId"),&id,true)&&id==slot)selected=t;}
    GeoJson replacement={0},*values=&b;char record[ASM_RECORD_MAX];int selected_value=selected;ok=selected>=0;
    if(ok&&w->evaluation&&w->evaluation->slot_record){ok=w->evaluation->slot_record(w->evaluation->user,binding->id,slot,record,sizeof record)&&w->json_parse(w->user,&replacement,record);values=&replacement;selected_value=0;}
    char face[8],orient[8];ok=ok&&geo_json_string(values,geo_json_member(values,selected_value,"contactFace"),face,sizeof face)&&!strcmp(face,"A")&&geo_json_string(values,geo_json_member(values,selected_value,"orientation"),orient,sizeof orient)&&!strcmp(orient,"A");
    for(int axis=0;axis<2&&ok;++axis){EngDimensionSource src;EngTarget target={1,0,0,axis};char path[192];ok=wood_eng_source_parse(&w->engineering,values,geo_json_member(values,selected_value,axis?"B":"A"),&src,false)&&(w->evaluation&&w->evaluation->generated_dimension?w->evaluation->generated_dimension(w->evaluation->user,a,m,slot,axis,&src,axis?&out->depth:&out->width,path,sizeof path):wood_eng_resolve(&w->engineering,&src,&target,UINT32_MAX,0,axis?&out->depth:&out->width,path,sizeof path));}
    geo_json_free(&replacement);geo_json_free(&q);geo_json_free(&b);if(!ok)return wood_asm_error(w,"D34/UNSUPPORTED: generation needs complete A contact, A transverse width and B depth sources");
    WoodAssemblyGuide guide;
    if(!w->surface(w->user,a->surface_id)||!w->guide(w->user,a->guide[m],&guide)||guide.surface_id!=a->surface_id||guide.direction!=(a->secondary[m]?ASM_DIR_U:ASM_DIR_V))return wood_asm_error(w,"I42: member needs a matching same-surface guide");
    out->surface_id=a->surface_id;out->guide_id=a->guide[m];out->direction=a->secondary[m]?ASM_DIR_U:ASM_DIR_V;out->role=a->secondary[m]?WOOD_MEMBER_ROLE_SECONDARY:WOOD_MEMBER_ROLE_PRIMARY;out->timber_id=a->timber[m];out->reserved=0;out->at=(AsmLocation){0};
    for(int k=0;k<2;++k){uint32_t id=a->ends[m][k];if(a->secondary[m]){int target=wood_asm_member_index(a,id);if(target<0||a->secondary[target])return wood_asm_error(w,"I42: invalid secondary member dependency");id=a->timber[target];}WoodAssemblyMember member;
        if(!w->member(w->user,id,&member)||id==a->timber[m]||(!a->secondary[m]&&member.role!=WOOD_MEMBER_ROLE_BOUNDARY)||member.surface_id!=a->surface_id)return wood_asm_error(w,"I42/V_CUT_PRIORITY: primary requires existing same-face boundary supports; secondary requires its two primary members");
        out->between[k]=id;
    }return true;
}
bool wood_assembly_generated_dimension_direct(WoodAssemblyContext *w,const AsmInstance *a,int m,int axis,GeoCoord *out,char *path,size_t cap)
{
    if(!a||m<0||m>=3||axis<0||axis>1)return false;AsmBinding *binding=wood_assembly_binding(w,a->binding_id);const AsmRuleVersion *rule=wood_assembly_rule(w,a->rule_id,a->rule_version);
    if(!binding||!binding->complete||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version||!rule||strcmp(a->rule_hash,rule->fingerprint))return wood_asm_error(w,"I42: incomplete or changed instance binding/rule");
    GeoJson q,b;bool ok=w->json_parse(w->user,&q,rule->content);if(!ok){geo_json_free(&q);return false;}ok=w->json_parse(w->user,&b,binding->content);if(!ok){geo_json_free(&q);geo_json_free(&b);return false;}
    uint32_t slot=0;int members=geo_json_member(&q,0,"members"),slots=geo_json_member(&b,0,"slots");
    for(int i=0;i<geo_json_size(&q,members);++i){uint32_t id;int t=geo_json_at(&q,members,i);if(wood_eng_u32(&q,geo_json_member(&q,t,"id"),&id,true)&&id==a->member[m])wood_eng_u32(&q,geo_json_member(&q,t,"slotId"),&slot,true);}
    int selected=-1;for(int i=0;i<geo_json_size(&b,slots);++i){uint32_t id;int t=geo_json_at(&b,slots,i);if(wood_eng_u32(&b,geo_json_member(&b,t,"slotId"),&id,true)&&id==slot)selected=t;}
    GeoJson replacement={0},*values=&b;char record[ASM_RECORD_MAX];int selected_value=selected;ok=selected>=0;
    if(ok&&w->evaluation&&w->evaluation->slot_record){ok=w->evaluation->slot_record(w->evaluation->user,binding->id,slot,record,sizeof record)&&w->json_parse(w->user,&replacement,record);values=&replacement;selected_value=0;}
    char face[8],orient[8];ok=ok&&geo_json_string(values,geo_json_member(values,selected_value,"contactFace"),face,sizeof face)&&!strcmp(face,"A")&&geo_json_string(values,geo_json_member(values,selected_value,"orientation"),orient,sizeof orient)&&!strcmp(orient,"A");
    EngDimensionSource src;EngTarget target={1,0,0,axis};if(ok)ok=wood_eng_source_parse(&w->engineering,values,geo_json_member(values,selected_value,axis?"B":"A"),&src,false)&&(w->evaluation&&w->evaluation->slot_dimension?w->evaluation->slot_dimension(w->evaluation->user,a->binding_id,slot,axis,&src,out,path,cap):wood_eng_resolve(&w->engineering,&src,&target,UINT32_MAX,0,out,path,cap));
    geo_json_free(&replacement);geo_json_free(&q);geo_json_free(&b);return ok||wood_asm_error(w,"D34/UNSUPPORTED: generation needs complete A contact, A transverse width and B depth sources");
}
bool wood_assembly_generation_prepare(WoodAssemblyContext *w)
{
    if(!w->scene_loading&&!wood_assembly_generation_integrity(w))return false;
    for(size_t i=0;i<w->state->instance_count;++i){const AsmInstance *a=&w->state->instances[i];
        if(w->evaluation&&w->evaluation->instance_definition&&!w->evaluation->instance_definition(w->evaluation->user,a,&a))return false;
        if(a->bay_repeat){
            for(int phase=0;phase<2;++phase)for(size_t m=0;m<a->mapping_count;++m)if((a->mapping[m].identity.kind==ASM_ID_SECONDARY)==(phase!=0)){
                WoodAssemblyDefinition definition={0};bool ok=w->evaluation&&w->evaluation->bay_generated?w->evaluation->bay_generated(w->evaluation->user,a,a->mapping[m].identity,&definition):wood_assembly_bay_member_definition_direct(w,a,a->mapping[m].identity,&definition);
                if(!ok||!w->member(w->user,definition.timber_id,NULL))return false;
                WoodMember value;if(!wood_member_construct(definition.timber_id,0,definition.width,definition.depth,true,definition.role,0,&value))return wood_asm_error(w,"D1: invalid generated section");
                value.placed=true;w->write_member(w->user,&value,&definition);
            }continue;
        }
        for(int phase=0;phase<2;++phase)for(int m=0;m<3;++m)if(a->secondary[m]==(phase!=0)){
            WoodAssemblyDefinition definition;if(!wood_asm_member_definition(w,a,m,&definition))return false;if(!w->member(w->user,definition.timber_id,NULL))return wood_asm_error(w,"I42: missing owned timber");
            WoodMember value;if(!wood_member_construct(definition.timber_id,0,definition.width,definition.depth,true,definition.role,0,&value))return wood_asm_error(w,"D1: invalid generated section");
            value.placed=true;w->write_member(w->user,&value,&definition);
        }
    }return true;
}
bool wood_assembly_generation_check(const WoodAssemblyContext *w)
{
    for(size_t i=0;i<w->state->instance_count;++i){const AsmInstance *a=&w->state->instances[i];if(w->evaluation&&w->evaluation->instance_check){if(!w->evaluation->instance_check(w->evaluation->user,a))return false;}else if(!wood_assembly_instance_check_direct(w,a))return false;}return true;
}
bool wood_assembly_instance_check_direct(const WoodAssemblyContext *w,const AsmInstance *a)
{
    if(a->bay_repeat)return wood_assembly_bay_check(w,a);
    if(!w->surface(w->user,a->surface_id))return wood_asm_error(w,"I42: missing instance surface");
        for(int m=0;m<3;++m){WoodAssemblyMember member;if(!w->member(w->user,a->timber[m],&member)||!member.placed)return wood_asm_error(w,"I42: unplaced owned member");
            if(!a->secondary[m])continue;int li=wood_asm_member_index(a,a->ends[m][0]),ri=wood_asm_member_index(a,a->ends[m][1]);GeoRect2 f,l,r;
            if(li<0||ri<0||!w->member(w->user,a->timber[li],NULL)||!w->member(w->user,a->timber[ri],NULL)||!w->footprint(w->user,a->surface_id,a->timber[m],&f)||!w->footprint(w->user,a->surface_id,a->timber[li],&l)||!w->footprint(w->user,a->surface_id,a->timber[ri],&r)||f.min_u!=l.max_u||f.max_u!=r.min_u||f.min_v<l.min_v||f.max_v>l.max_v||f.min_v<r.min_v||f.max_v>r.max_v)return wood_asm_error(w,"I42: secondary endpoints do not contact the declared inward primary sides");
        }
    return true;
}
bool wood_assembly_generation_operation(WoodAssemblyContext *w,GeoJson *j,int t)
{
    char op[24];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return false;bool create=!strcmp(op,"create-instance"),edit=!strcmp(op,"edit-instance"),del=!strcmp(op,"delete-instance");if(!create&&!edit&&!del)return wood_assembly_operation(w,j,t);
    uint32_t id;AsmInstance value,*old=NULL;char expected[65],actual[65];int source=geo_json_member(j,t,"value");
    if(create){if(!geo_json_keys(j,t,"op,expectedBindingFingerprint,value","")||!wood_asm_instance_parse(w,j,source,&value))return false;id=value.id;if(wood_assembly_instance(w,id))return wood_asm_error(w,"I42: instance already exists");}
    else {if(!geo_json_keys(j,t,edit?"op,id,expectedFingerprint,expectedBindingFingerprint,value":"op,id,expectedFingerprint","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true)||!wood_asm_hash_token(j,geo_json_member(j,t,"expectedFingerprint"),expected))return wood_asm_error(w,"I42: invalid guarded instance edit/delete");old=wood_assembly_instance(w,id);if(!old)return wood_asm_error(w,"I42: instance does not exist");geo_sha256(old->content,strlen(old->content),actual);if(strcmp(expected,actual))return wood_asm_error(w,"STALE: instance source changed");}
    if((del&&old->bay_repeat)||(!del&&((old&&old->bay_repeat)||geo_json_member(j,source,"layout")>=0)))return wood_asm_bay_operation(w,j,t,op,old);
    if(del){
        AsmInstance copy=*old;size_t at=(size_t)(old-w->state->instances);memmove(old,old+1,(w->state->instance_count-at-1)*sizeof *old);memset(&w->state->instances[--w->state->instance_count],0,sizeof *old);
        for(int m=0;m<3;++m)if(!w->remove_member(w->user,copy.timber[m]))return false;
        for(size_t i=w->state->owner_count;i>0;--i)if(w->state->owners[i-1].instance==id){memmove(&w->state->owners[i-1],&w->state->owners[i],(w->state->owner_count-i)*sizeof(AsmOwner));memset(&w->state->owners[--w->state->owner_count],0,sizeof(AsmOwner));}w->state->generation_required=w->state->instance_count>0;return true;
    }
    if(edit){if(!wood_asm_instance_parse(w,j,source,&value))return false;if(value.id!=id)return wood_asm_error(w,"I42: edited instance identity mismatch");}
    AsmBinding *binding=wood_assembly_binding(w,value.binding_id);if(!binding||!wood_asm_hash_token(j,geo_json_member(j,t,"expectedBindingFingerprint"),expected))return wood_asm_error(w,"I42: expected binding fingerprint required");geo_sha256(binding->content,strlen(binding->content),actual);if(strcmp(expected,actual))return wood_asm_error(w,"STALE: instance binding source changed");
    if(edit){for(int m=0;m<3;++m){int at=wood_asm_member_index(old,value.member[m]);if(at<0||old->secondary[at]!=value.secondary[m])return wood_asm_error(w,"D34/UNSUPPORTED: member membership/roles cannot change");value.timber[m]=old->timber[at];}}
    else {
        if(w->state->instance_count==ASM_INSTANCE_MAX||w->state->owner_count+3>ASM_OWNER_MAX||w->member_count(w->user)+3>w->member_capacity)return wood_asm_error(w,"CAPACITY: at most 16 instances within native timber capacity");
        for(int phase=0;phase<2;++phase)for(int m=0;m<3;++m)if(value.secondary[m]==(phase!=0)){uint32_t tid=1;while(w->member(w->user,tid,NULL)||wood_bay_retired(w,tid)){if(tid==UINT32_MAX)return wood_asm_error(w,"CAPACITY: no free timber identity");++tid;}value.timber[m]=tid;w->allocate_member(w->user,tid);w->state->owners[w->state->owner_count++]=(AsmOwner){tid,value.id,value.member[m]};}
        old=&w->state->instances[w->state->instance_count++];
    }
    if(!w->instance_content(w->user,&value,j,source))return false;*old=value;w->state->generation_required=true;return true;
}
bool wood_assembly_instance_load(WoodAssemblyContext *w,GeoJson *j,int t)
{
    int value=geo_json_member(j,t,"source");
    if(geo_json_member(j,value,"layout")>=0){
        if(!w->state->generation_required||!w->state->bay_required)return wood_asm_error(w,"I69: repeat instance requires both generation capabilities");
        AsmInstance a;if(w->state->instance_count>=ASM_INSTANCE_MAX||!wood_assembly_instance_definition_parse(w,j,t,&a)||wood_assembly_instance(w,a.id))return false;
        for(size_t m=0;m<a.mapping_count;++m){WoodAssemblyDefinition expected={0};WoodAssemblyMember actual;
            if(!wood_assembly_bay_member_definition_direct(w,&a,a.mapping[m].identity,&expected)||!w->member(w->user,a.mapping[m].timber,&actual)||!actual.placed||actual.width!=expected.width||actual.depth!=expected.depth||actual.role!=expected.role||!w->anchor_matches(w->user,a.mapping[m].timber,&expected))return wood_asm_error(w,"I69: saved owned definitions differ from repeat sources");}
        w->state->instances[w->state->instance_count++]=a;return true;
    }
    if(!w->state->generation_required||!geo_json_keys(j,t,"source,mapping","")||w->state->instance_count==ASM_INSTANCE_MAX)return wood_asm_error(w,"I42: instance needs generation capability and source/mapping");AsmInstance a;int source=geo_json_member(j,t,"source"),map=geo_json_member(j,t,"mapping");if(!wood_asm_instance_parse(w,j,source,&a)||wood_assembly_instance(w,a.id)||!geo_json_is_array(j,map)||geo_json_size(j,map)!=3)return wood_asm_error(w,"I42: invalid or duplicate instance mapping");
    for(int i=0;i<3;++i){int v=geo_json_at(j,map,i);uint32_t member,tid;if(!geo_json_keys(j,v,"memberId,timberId","")||!wood_eng_u32(j,geo_json_member(j,v,"memberId"),&member,true)||!wood_eng_u32(j,geo_json_member(j,v,"timberId"),&tid,true))return false;int m=wood_asm_member_index(&a,member);if(m<0||a.timber[m])return wood_asm_error(w,"I42: duplicate/missing mapped member");a.timber[m]=tid;}
    if(!w->instance_content(w->user,&a,j,source))return false;
    /* Persisted owned definitions must equal sources before reconstruction, not be silently repaired. */
    for(int m=0;m<3;++m){WoodAssemblyDefinition expected;if(!wood_asm_member_definition(w,&a,m,&expected))return false;WoodAssemblyMember actual;if(!w->member(w->user,a.timber[m],&actual))return wood_asm_error(w,"I42: saved owned timber missing");
        if(actual.width!=expected.width||actual.depth!=expected.depth||actual.role!=expected.role||!actual.placed||!w->anchor_matches(w->user,a.timber[m],&expected))return wood_asm_error(w,"I42: saved owned definitions differ from instance sources");
    }
    w->state->instances[w->state->instance_count++]=a;return true;
}

/* D58/I69/R55: bounded repetition is W policy. These identities never depend
 * on a list index, a coordinate, a generated timber id or a display label. */
bool wood_assembly_identity_equal(AsmIdentity a,AsmIdentity b)
{return a.kind==b.kind&&a.key==b.key&&a.left==b.left&&a.right==b.right;}
size_t wood_assembly_mapping_count(const AsmInstance *a)
{return a->bay_repeat?a->mapping_count:3;}
AsmMapping wood_assembly_mapping_at(const AsmInstance *a,size_t n)
{return a->bay_repeat?a->mapping[n]:(AsmMapping){{ASM_ID_MEMBER,a->member[n],0,0},a->timber[n]};}
AsmIdentity wood_assembly_owner_identity(const AsmOwner *o)
{return (AsmIdentity){o->kind,o->member,o->left,o->right};}
int wood_assembly_mapping_index(const AsmInstance *a,AsmIdentity id)
{for(size_t i=0;i<wood_assembly_mapping_count(a);++i)if(wood_assembly_identity_equal(wood_assembly_mapping_at(a,i).identity,id))return (int)i;return -1;}
bool wood_assembly_bay_failure(const WoodAssemblyContext *w,const char *category,const char *code,const char *clause,uint32_t instance,uint32_t primary,uint32_t line,const char *expected,const char *actual)
{
    if(w->bay_report&&w->bay_report->issue_count<ASM_OWNER_MAX){AsmBayIssue *e=&w->bay_report->issues[w->bay_report->issue_count++];memset(e,0,sizeof *e);
        snprintf(e->category,sizeof e->category,"%s",category);snprintf(e->code,sizeof e->code,"%s",code);snprintf(e->clause,sizeof e->clause,"%s",clause);
        snprintf(e->expected,sizeof e->expected,"%s",expected);snprintf(e->actual,sizeof e->actual,"%s",actual);e->instance=instance;e->primary=primary;e->line=line;}
    return wood_asm_error(w,"%s/%s %s: %s",category,code,clause,actual);
}
static bool wood_bay_bad(const WoodAssemblyContext *w,uint32_t id,const char *text)
{return wood_assembly_bay_failure(w,"INVALID","INVALID","I69",id,0,0,"complete, unique typed repeat inputs",text);}
static bool wood_bay_unsupported(const WoodAssemblyContext *w,uint32_t id,const char *text)
{return wood_assembly_bay_failure(w,"UNSUPPORTED","UNSUPPORTED","D58/I69",id,0,0,"supported single-bay topology and position references",text);}
static bool wood_bay_capacity(const WoodAssemblyContext *w,uint32_t id,const char *text)
{return wood_assembly_bay_failure(w,"CAPACITY","CAPACITY","I33/I69",id,0,0,"12 primaries, 24 lines, 24 omissions, 48 total owned, 8191 record bytes",text);}
static bool wood_bay_index(GeoJson *j,int t,int64_t *out)
{
    char s[ASM_RECORD_MAX];if(!geo_json_string(j,t,s,sizeof s)||!s[0])return false;const unsigned char *p=(const unsigned char *)s;bool neg=*p=='-';if(neg)++p;if(!*p)return false;
    uint64_t n=0,limit=neg?(uint64_t)INT64_MAX+1:(uint64_t)INT64_MAX;
    for(;*p;++p){if(*p<'0'||*p>'9'||n>(limit-(*p-'0'))/10)return false;n=n*10+(*p-'0');}
    *out=neg?(n==(uint64_t)INT64_MAX+1?INT64_MIN:-(int64_t)n):(int64_t)n;return true;
}
static bool wood_bay_location_equal(const AsmLocation *a,const AsmLocation *b)
{return a->kind==b->kind&&a->id==b->id&&a->axis==b->axis&&a->index==b->index&&a->edge==b->edge&&!strcmp(a->edge_key,b->edge_key);}
static bool wood_bay_location(WoodAssemblyContext *w,GeoJson *j,int t,bool primary,uint32_t instance,AsmLocation *at)
{
    char kind[32],axis[8];memset(at,0,sizeof *at);
    if(!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind))return wood_bay_bad(w,instance,"missing position reference kind");
    if(!strcmp(kind,"guide")){at->kind=ASM_AT_GUIDE;return (geo_json_keys(j,t,"kind,id","")&&wood_eng_u32(j,geo_json_member(j,t,"id"),&at->id,false))||wood_bay_bad(w,instance,"invalid guide reference");}
    if(!strcmp(kind,"grid-line")){at->kind=ASM_AT_GRID;
        if(!geo_json_keys(j,t,"kind,gridId,axis,index","")||!wood_eng_u32(j,geo_json_member(j,t,"gridId"),&at->id,false)||!geo_json_string(j,geo_json_member(j,t,"axis"),axis,sizeof axis)||
           (strcmp(axis,"u")&&strcmp(axis,"v"))||!wood_bay_index(j,geo_json_member(j,t,"index"),&at->index))return wood_bay_bad(w,instance,"invalid exact decimal grid reference");
        at->axis=!strcmp(axis,"v");return (at->axis==(primary?0:1))||wood_bay_bad(w,instance,"grid coordinate axis must be perpendicular to member length");}
    if(!strcmp(kind,"outline-edge")&&primary){int64_t edge;at->kind=ASM_AT_OUTLINE;
        int key=geo_json_member(j,t,"edgeKey");
        if(key>=0)return (geo_json_keys(j,t,"kind,edgeKey","")&&geo_json_is_array(j,key)&&geo_json_size(j,key)>0&&geo_json_canonical(j,key,at->edge_key,sizeof at->edge_key))||wood_bay_bad(w,instance,"invalid R41 outer edge key");
        if(!geo_json_keys(j,t,"kind,edge","")||!geo_json_integer(j,geo_json_member(j,t,"edge"),&edge)||edge<0||edge>INT32_MAX)return wood_bay_bad(w,instance,"invalid outer outline edge");at->edge=(int)edge;return true;}
    return wood_bay_unsupported(w,instance,"position kind is outside D58; hole, phase, child and rule lines are not supported");
}
static bool wood_bay_topology(WoodAssemblyContext *w,AsmInstance *a)
{
    const AsmRuleVersion *rule=wood_assembly_rule(w,a->rule_id,a->rule_version);AsmBinding *binding=wood_assembly_binding(w,a->binding_id);
    if(!rule||strcmp(rule->fingerprint,a->rule_hash)||!binding||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version)return wood_bay_bad(w,a->id,"missing binding or changed fixed rule fingerprint/version");
    GeoJson q;if(!w->json_parse(w->user,&q,rule->content)){geo_json_free(&q);return false;}
    int members=geo_json_member(&q,0,"members"),joints=geo_json_member(&q,0,"joints");bool ok=geo_json_size(&q,members)==3&&geo_json_size(&q,joints)==2;
    uint32_t slots[3]={0};bool ends[2]={false,false};
    for(int k=0;k<2&&ok;++k){int t=geo_json_at(&q,joints,k);char kind[24],end[16],side[8],dir[8];uint32_t term,target;
        ok=geo_json_string(&q,geo_json_member(&q,t,"kind"),kind,sizeof kind)&&!strcmp(kind,"end-to-side")&&
           geo_json_string(&q,geo_json_member(&q,t,"end"),end,sizeof end)&&(!strcmp(end,"start")||!strcmp(end,"finish"))&&
           geo_json_string(&q,geo_json_member(&q,t,"side"),side,sizeof side)&&geo_json_string(&q,geo_json_member(&q,t,"dir"),dir,sizeof dir)&&!strcmp(dir,"u")&&
           wood_eng_u32(&q,geo_json_member(&q,t,"terminatedMember"),&term,true)&&wood_eng_u32(&q,geo_json_member(&q,t,"targetMember"),&target,true);
        if(!ok)break;int e=!strcmp(end,"finish");if(ends[e]||strcmp(side,e?"-u":"+u")||(a->member[2]&&a->member[2]!=term))ok=false;
        ends[e]=true;a->member[e]=target;a->member[2]=term;
    }
    ok=ok&&ends[0]&&ends[1]&&a->member[0]!=a->member[1]&&a->member[0]!=a->member[2]&&a->member[1]!=a->member[2];
    for(int m=0;m<3&&ok;++m){for(int k=0;k<3;++k){int t=geo_json_at(&q,members,k);uint32_t id;if(wood_eng_u32(&q,geo_json_member(&q,t,"id"),&id,true)&&id==a->member[m])wood_eng_u32(&q,geo_json_member(&q,t,"slotId"),&slots[m],true);}if(!slots[m])ok=false;}
    geo_json_free(&q);a->secondary[2]=true;
    return (ok&&slots[0]==slots[1])||wood_bay_unsupported(w,a->id,"repeat requires two primary members in one slot and one secondary with start +u / finish -u end-to-side joints");
}
bool wood_assembly_bay_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmInstance *a)
{
    memset(a,0,sizeof *a);a->bay_repeat=true;char layout[24];int rule=geo_json_member(j,t,"rule");
    char bounded_source[ASM_RECORD_MAX];if(!geo_json_canonical(j,t,bounded_source,sizeof bounded_source))return wood_bay_capacity(w,0,"repeat source exceeds the instance record byte limit");
    if(!geo_json_string(j,geo_json_member(j,t,"layout"),layout,sizeof layout)||strcmp(layout,"bay-repeat"))return wood_bay_unsupported(w,0,"unknown instance layout");
    if(!geo_json_keys(j,t,"id,name,bindingId,rule,surfaceId,layout,primaries,secondaryLines","omit")||
       !wood_eng_u32(j,geo_json_member(j,t,"id"),&a->id,true)||!wood_asm_name(j,geo_json_member(j,t,"name"),a->name)||
       !wood_eng_u32(j,geo_json_member(j,t,"bindingId"),&a->binding_id,true)||!wood_eng_u32(j,geo_json_member(j,t,"surfaceId"),&a->surface_id,false)||
       !geo_json_keys(j,rule,"id,version,fingerprint","")||!wood_eng_u32(j,geo_json_member(j,rule,"id"),&a->rule_id,true)||
       !wood_eng_u32(j,geo_json_member(j,rule,"version"),&a->rule_version,true)||!wood_asm_hash_token(j,geo_json_member(j,rule,"fingerprint"),a->rule_hash))return wood_bay_bad(w,a->id,"invalid repeat source or fixed rule");
    if(!wood_bay_topology(w,a))return false;
    int p=geo_json_member(j,t,"primaries"),lines=geo_json_member(j,t,"secondaryLines"),omit=geo_json_member(j,t,"omit");
    if(!geo_json_is_array(j,p)||!geo_json_is_array(j,lines)||(omit>=0&&!geo_json_is_array(j,omit)))return wood_bay_bad(w,a->id,"repeat lists must be arrays");
    int np=geo_json_size(j,p),nl=geo_json_size(j,lines),no=omit<0?0:geo_json_size(j,omit);
    if(np>ASM_BAY_PRIMARY_MAX||nl>ASM_BAY_LINE_MAX||no>ASM_BAY_OMIT_MAX)return wood_bay_capacity(w,a->id,"repeat input list capacity exceeded");
    if(np<2||nl<1)return wood_bay_bad(w,a->id,"at least two primaries and one secondary line are required");
    a->primary_count=(size_t)np;a->line_count=(size_t)nl;a->omit_count=(size_t)no;
    for(int i=0;i<np;++i){int item=geo_json_at(j,p,i),ends=geo_json_member(j,item,"ends");AsmBayPrimary *v=&a->primaries[i];
        if(!geo_json_keys(j,item,"key,at,ends","")||!wood_eng_u32(j,geo_json_member(j,item,"key"),&v->key,true)||!geo_json_keys(j,ends,"start,finish",""))return wood_bay_bad(w,a->id,"invalid primary key or supports");
        if(!wood_bay_location(w,j,geo_json_member(j,item,"at"),true,a->id,&v->at))return false;
        for(int e=0;e<2;++e){int end=geo_json_member(j,ends,e?"finish":"start");char kind[16];
            if(!geo_json_string(j,geo_json_member(j,end,"kind"),kind,sizeof kind)||strcmp(kind,"timber"))return wood_bay_unsupported(w,a->id,"primary between supports must name placed external timbers");
            if(!geo_json_keys(j,end,"kind,id","")||!wood_eng_u32(j,geo_json_member(j,end,"id"),&v->ends[e],false))return wood_bay_bad(w,a->id,"invalid primary support identity");}
        if(v->ends[0]==v->ends[1])return wood_bay_bad(w,a->id,"between must name two distinct supports");
        for(int k=0;k<i;++k)if(a->primaries[k].key==v->key||wood_bay_location_equal(&a->primaries[k].at,&v->at))return wood_bay_bad(w,a->id,"duplicate primary key or position reference");
    }
    for(int i=0;i<nl;++i){int item=geo_json_at(j,lines,i);AsmBayLine *v=&a->lines[i];
        if(!geo_json_keys(j,item,"key,at","")||!wood_eng_u32(j,geo_json_member(j,item,"key"),&v->key,true))return wood_bay_bad(w,a->id,"invalid secondary line key");
        if(!wood_bay_location(w,j,geo_json_member(j,item,"at"),false,a->id,&v->at))return false;
        for(int k=0;k<i;++k)if(a->lines[k].key==v->key||wood_bay_location_equal(&a->lines[k].at,&v->at))return wood_bay_bad(w,a->id,"duplicate line key or position reference");
        for(int k=0;k<np;++k)if(wood_bay_location_equal(&a->primaries[k].at,&v->at))return wood_bay_bad(w,a->id,"primary and secondary cannot share a position reference");
    }
    for(int i=0;i<no;++i){int item=geo_json_at(j,omit,i);AsmBayCell *v=&a->omit[i];
        if(!geo_json_keys(j,item,"line,left,right","")||!wood_eng_u32(j,geo_json_member(j,item,"line"),&v->line,true)||!wood_eng_u32(j,geo_json_member(j,item,"left"),&v->left,true)||!wood_eng_u32(j,geo_json_member(j,item,"right"),&v->right,true)||v->left==v->right)return wood_bay_bad(w,a->id,"invalid omission identity");
        for(int k=0;k<i;++k)if(!memcmp(v,&a->omit[k],sizeof *v))return wood_bay_bad(w,a->id,"duplicate omission identity");}
    return true;
}
static bool wood_asm_bay_mapping(WoodAssemblyContext *w,GeoJson *j,int list,AsmInstance *a)
{
    if(!geo_json_is_array(j,list))return wood_bay_bad(w,a->id,"mapping must be an array");int count=geo_json_size(j,list);
    if(count>ASM_OWNER_MAX)return wood_bay_capacity(w,a->id,"owned mapping exceeds 48");a->mapping_count=(size_t)count;
    for(int i=0;i<count;++i){int item=geo_json_at(j,list,i),secondary=geo_json_member(j,item,"secondary");AsmMapping *m=&a->mapping[i];
        if(!wood_eng_u32(j,geo_json_member(j,item,"timberId"),&m->timber,true))return wood_bay_bad(w,a->id,"invalid mapped timber identity");
        if(secondary>=0){m->identity.kind=ASM_ID_SECONDARY;if(!geo_json_keys(j,item,"secondary,timberId","")||!geo_json_keys(j,secondary,"line,left,right","")||
            !wood_eng_u32(j,geo_json_member(j,secondary,"line"),&m->identity.key,true)||!wood_eng_u32(j,geo_json_member(j,secondary,"left"),&m->identity.left,true)||!wood_eng_u32(j,geo_json_member(j,secondary,"right"),&m->identity.right,true)||m->identity.left==m->identity.right)return wood_bay_bad(w,a->id,"invalid secondary mapping identity");}
        else{m->identity.kind=ASM_ID_PRIMARY;if(!geo_json_keys(j,item,"primary,timberId","")||!wood_eng_u32(j,geo_json_member(j,item,"primary"),&m->identity.key,true))return wood_bay_bad(w,a->id,"invalid primary mapping identity");}
        for(int k=0;k<i;++k)if(a->mapping[k].timber==m->timber||wood_assembly_identity_equal(a->mapping[k].identity,m->identity))return wood_bay_bad(w,a->id,"duplicate owned identity or timber");
    }return true;
}
static int wood_bay_primary(const AsmInstance *a,uint32_t key)
{for(size_t i=0;i<a->primary_count;++i)if(a->primaries[i].key==key)return (int)i;return -1;}
static int wood_bay_line(const AsmInstance *a,uint32_t key)
{for(size_t i=0;i<a->line_count;++i)if(a->lines[i].key==key)return (int)i;return -1;}
static WoodAssemblyDependency wood_bay_position_dependency(uint32_t surface,const AsmLocation *at)
{return (WoodAssemblyDependency){at->kind==ASM_AT_GUIDE?ASM_DEP_GUIDE:at->kind==ASM_AT_GRID?ASM_DEP_GRID:ASM_DEP_OUTLINE,at->kind==ASM_AT_OUTLINE?surface:at->id};}
static bool wood_bay_walk(WoodAssemblyContext *w,const AsmInstance *a,WoodAssemblyDependency node,bool selected,WoodAssemblyDependency *path,size_t depth,uint32_t primary,uint32_t line)
{
    if(depth==ASM_BAY_PATH_MAX)return wood_bay_capacity(w,a->id,"support dependency path exceeds 64 identities");path[depth++]=node;
    if(node.kind==ASM_DEP_TIMBER)for(size_t k=0;k<w->state->owner_count;++k)if(w->state->owners[k].instance==a->id&&w->state->owners[k].timber==node.id){
        wood_assembly_bay_failure(w,"UNSUPPORTED","SELF_SUPPORT","I69",a->id,primary,line,"support and position closure excludes this instance's owned members","support or position depends on this instance's owned timber");
        if(w->bay_report&&w->bay_report->issue_count){AsmBayIssue *e=&w->bay_report->issues[w->bay_report->issue_count-1];e->owned=node.id;e->path_count=depth;memcpy(e->path,path,depth*sizeof *path);}return false;}
    for(size_t k=0;k+1<depth;++k)if(path[k].kind==node.kind&&path[k].id==node.id)return wood_bay_bad(w,a->id,"cyclic support or position reference");
    WoodAssemblyDependency children[ASM_BAY_PATH_MAX];size_t count=0;
    if(!w->dependencies||!w->dependencies(w->user,node,children,ASM_BAY_PATH_MAX,&count,selected))return wood_bay_bad(w,a->id,"missing or invalid support/position dependency");
    for(size_t k=0;k<count;++k)if(!wood_bay_walk(w,a,children[k],selected,path,depth,primary,line))return false;
    return true;
}
static bool wood_bay_dependencies(WoodAssemblyContext *w,const AsmInstance *a,bool selected)
{
    WoodAssemblyDependency path[ASM_BAY_PATH_MAX];
    for(size_t i=0;i<a->primary_count;++i){const AsmBayPrimary *p=&a->primaries[i];
        if(!wood_bay_walk(w,a,wood_bay_position_dependency(a->surface_id,&p->at),selected,path,0,p->key,0))return false;
        for(int k=0;k<2;++k)if(!wood_bay_walk(w,a,(WoodAssemblyDependency){ASM_DEP_TIMBER,p->ends[k]},selected,path,0,p->key,0))return false;}
    for(size_t i=0;i<a->line_count;++i)if(!wood_bay_walk(w,a,wood_bay_position_dependency(a->surface_id,&a->lines[i].at),selected,path,0,0,a->lines[i].key))return false;return true;
}
static bool wood_bay_band(WoodAssemblyContext *w,const AsmInstance *a,const AsmLocation *at,bool primary,GeoCoord width,GeoCoord *lo,GeoCoord *hi)
{
    WoodAssemblyPosition value={0};if(!w->position||!w->position(w->user,a->surface_id,at,&value))return wood_bay_bad(w,a->id,"position reference is missing or cannot be resolved");
    if(value.subgrid||value.phased||value.from_fill)return wood_bay_unsupported(w,a->id,"position is not an unphased finite or configured main grid line");
    if(value.surface_id!=a->surface_id||value.axis!=(primary?0:1))return wood_bay_bad(w,a->id,"position must be on the same surface and perpendicular to the member axis");
    if(at->kind==ASM_AT_OUTLINE){if(!primary||value.edge.start.u!=value.edge.end.u||!value.outward.u)return wood_bay_bad(w,a->id,"outer edge must be parallel to +v");*lo=value.edge.start.u-(value.outward.u>0?width:0);}
    else *lo=value.coordinate-width/2;
    if(!geo_coord_in_range(*lo)||width<=0||!geo_coord_in_range(width)||*lo>INT64_MAX-width)return wood_bay_bad(w,a->id,"position band is out of coordinate range");*hi=*lo+width;
    return geo_coord_in_range(*hi)||wood_bay_bad(w,a->id,"position band is out of coordinate range");
}
bool wood_assembly_bay_member_definition_direct(WoodAssemblyContext *w,const AsmInstance *a,AsmIdentity identity,WoodAssemblyDefinition *out)
{
    memset(out,0,sizeof *out);int map=wood_assembly_mapping_index(a,identity);if(map<0)return wood_bay_bad(w,a->id,"missing owned mapping identity");
    bool secondary=identity.kind==ASM_ID_SECONDARY;int index=secondary?wood_bay_line(a,identity.key):wood_bay_primary(a,identity.key);if(index<0)return wood_bay_bad(w,a->id,"mapped occurrence does not exist");
    char path[192];if(!wood_assembly_generated_dimension_direct(w,a,secondary?2:0,0,&out->width,path,sizeof path)||!wood_assembly_generated_dimension_direct(w,a,secondary?2:0,1,&out->depth,path,sizeof path))return false;
    out->at=secondary?a->lines[index].at:a->primaries[index].at;GeoCoord lo,hi;if(!wood_bay_band(w,a,&out->at,!secondary,out->width,&lo,&hi))return false;
    out->surface_id=a->surface_id;out->guide_id=out->at.kind==ASM_AT_GUIDE?out->at.id:0;out->direction=secondary?ASM_DIR_U:ASM_DIR_V;out->role=secondary?WOOD_MEMBER_ROLE_SECONDARY:WOOD_MEMBER_ROLE_PRIMARY;out->timber_id=a->mapping[map].timber;
    for(int k=0;k<2;++k){uint32_t id;
        if(secondary){AsmIdentity primary={ASM_ID_PRIMARY,k?identity.right:identity.left,0,0};int at=wood_assembly_mapping_index(a,primary);if(at<0)return wood_bay_bad(w,a->id,"secondary mapping lacks its primary");id=a->mapping[at].timber;}
        else id=a->primaries[index].ends[k];
        WoodAssemblyMember member;if(!w->member(w->user,id,&member)||member.surface_id!=a->surface_id||(!secondary&&member.role!=WOOD_MEMBER_ROLE_BOUNDARY))return wood_bay_bad(w,a->id,"primary requires existing same-surface boundary supports");out->between[k]=id;
    }return true;
}
typedef struct {
    AsmInstance *target,value;
    GeoRect2 primary[ASM_BAY_PRIMARY_MAX];
    AsmMapping next[ASM_OWNER_MAX];size_t count,cell_start,cell_end;
} WoodBayPlan;
static int wood_bay_identity_order(AsmIdentity a,AsmIdentity b)
{if(a.kind!=b.kind)return a.kind<b.kind?-1:1;if(a.key!=b.key)return a.key<b.key?-1:1;if(a.left!=b.left)return a.left<b.left?-1:1;return a.right==b.right?0:a.right<b.right?-1:1;}
static bool wood_bay_add(WoodAssemblyContext *w,WoodBayPlan *plan,AsmIdentity id)
{if(plan->count==ASM_OWNER_MAX)return wood_bay_capacity(w,plan->value.id,"generated identity count exceeds global owned capacity");int old=wood_assembly_mapping_index(&plan->value,id);AsmMapping value={id,old<0?0:wood_assembly_mapping_at(&plan->value,(size_t)old).timber};size_t n=plan->count++;while(n&&wood_bay_identity_order(plan->next[n-1].identity,id)>0){plan->next[n]=plan->next[n-1];--n;}plan->next[n]=value;return true;}
static bool wood_assembly_bay_cells(WoodAssemblyContext *w,WoodBayPlan *plan,GeoCoord secondary_width)
{
    const AsmInstance *a=&plan->value;bool seen[ASM_BAY_OMIT_MAX]={0},capacity=true;AsmBayReport *report=w->bay_report;
    plan->cell_start=report?report->cell_count:0;
    for(size_t l=0;l<a->line_count;++l){GeoCoord lo,hi;if(!wood_bay_band(w,a,&a->lines[l].at,false,secondary_width,&lo,&hi))return false;
        size_t order[ASM_BAY_PRIMARY_MAX],count=0;bool partial=false;
        for(size_t p=0;p<a->primary_count;++p){const GeoRect2 *r=&plan->primary[p];
            if(r->min_v<=lo&&r->max_v>=hi){size_t n=count++;GeoCoord center=r->min_u+(r->max_u-r->min_u)/2;
                while(n){const GeoRect2 *prev=&plan->primary[order[n-1]];GeoCoord other=prev->min_u+(prev->max_u-prev->min_u)/2;if(other<center||(other==center&&a->primaries[order[n-1]].key<a->primaries[p].key))break;order[n]=order[n-1];--n;}order[n]=p;
            }else if(r->min_v<hi&&lo<r->max_v){wood_assembly_bay_failure(w,"INVALID","PARTIAL_COVERAGE","I69",a->id,a->primaries[p].key,a->lines[l].key,"primary fully covers the secondary width band or has zero positive overlap","primary only partly covers the secondary width band");partial=true;}}
        if(partial)return false;
        for(size_t k=1;k<count;++k){AsmBayCell cell={a->lines[l].key,a->primaries[order[k-1]].key,a->primaries[order[k]].key};bool omitted=false;
            for(size_t o=0;o<a->omit_count;++o)if(!memcmp(&cell,&a->omit[o],sizeof cell)){omitted=true;seen[o]=true;}
            if(report){if(report->cell_count>=ASM_INSTANCE_MAX*ASM_BAY_CELL_MAX)return wood_bay_capacity(w,a->id,"candidate cell report capacity exceeded");report->cells[report->cell_count++]=(AsmBayCellReport){a->id,cell.line,cell.left,cell.right,0,omitted};}
            if(!omitted&&capacity)capacity=wood_bay_add(w,plan,(AsmIdentity){ASM_ID_SECONDARY,cell.line,cell.left,cell.right});
        }
    }
    plan->cell_end=report?report->cell_count:0;
    for(size_t o=0;o<a->omit_count;++o)if(!seen[o])return wood_assembly_bay_failure(w,"INVALID","OMIT_NOT_A_BAY","I69",a->id,0,a->omit[o].line,"omission names a currently derived bay","omission no longer names a current line/left/right bay");
    return capacity;
}
static bool wood_assembly_bay_plan(WoodAssemblyContext *w,AsmInstance *stored,WoodBayPlan *plan)
{
    memset(plan,0,sizeof *plan);plan->target=stored;const AsmInstance *effective=stored;
    if(w->evaluation&&w->evaluation->instance_definition&&!w->evaluation->instance_definition(w->evaluation->user,stored,&effective))return false;plan->value=*effective;
    AsmInstance *a=&plan->value;if(!wood_bay_dependencies(w,a,false))return false;
    GeoCoord width,depth,secondary_width;char path[192];
    if(!wood_assembly_generated_dimension_direct(w,a,0,0,&width,path,sizeof path)||!wood_assembly_generated_dimension_direct(w,a,0,1,&depth,path,sizeof path)||!wood_assembly_generated_dimension_direct(w,a,2,0,&secondary_width,path,sizeof path))return false;
    for(size_t i=0;i<a->primary_count;++i){const AsmBayPrimary *p=&a->primaries[i];GeoCoord lo,hi;if(!wood_bay_band(w,a,&p->at,true,width,&lo,&hi))return false;
        GeoRect2 supports[2];for(int k=0;k<2;++k){WoodAssemblyMember member;
            if(!w->member(w->user,p->ends[k],&member)||member.surface_id!=a->surface_id||member.role!=WOOD_MEMBER_ROLE_BOUNDARY||!w->footprint(w->user,a->surface_id,p->ends[k],&supports[k])||supports[k].min_u>lo||supports[k].max_u<hi)return wood_assembly_bay_failure(w,"INVALID","SUPPORT_RANGE","I19/R21/R55",a->id,p->key,0,"two same-face boundary supports cover the complete primary width","support is missing, has wrong role/face, or does not cover full width");}
        GeoCoord start,finish;
        if(supports[0].max_v<supports[1].min_v){start=supports[0].max_v;finish=supports[1].min_v;}
        else if(supports[1].max_v<supports[0].min_v){start=supports[1].max_v;finish=supports[0].min_v;}
        else return wood_assembly_bay_failure(w,"INVALID","SUPPORT_FACING_AMBIGUOUS","R21/R55",a->id,p->key,0,"unique facing support sides with positive interval","named supports have no unique facing interval");
        plan->primary[i]=(GeoRect2){lo,start,hi,finish};if(!wood_bay_add(w,plan,(AsmIdentity){ASM_ID_PRIMARY,p->key,0,0}))return false;
        if(w->bay_report){if(w->bay_report->primary_count>=ASM_INSTANCE_MAX*ASM_BAY_PRIMARY_MAX)return wood_bay_capacity(w,a->id,"primary report capacity exceeded");w->bay_report->primaries[w->bay_report->primary_count++]=(AsmBayPrimaryReport){a->id,p->key,plan->primary[i]};}
    }
    if(!wood_bay_dependencies(w,a,true))return false;
    return wood_assembly_bay_cells(w,plan,secondary_width);
}
static bool wood_bay_retired(const WoodAssemblyContext *w,uint32_t id)
{if(w->bay_report)for(size_t i=0;i<w->bay_report->retired_count;++i)if(w->bay_report->retired[i]==id)return true;return false;}
static bool wood_bay_retire(WoodAssemblyContext *w,uint32_t instance,uint32_t id)
{
    char reason[256];if(w->external_reference&&w->external_reference(w->user,instance,id,reason,sizeof reason))return wood_assembly_bay_failure(w,"INVALID","OWNED_REFERENCED","I69",instance,0,0,"deleted owned identity has no external users",reason);
    if(!wood_bay_retired(w,id)&&w->bay_report){if(w->bay_report->retired_count==ASM_OWNER_MAX)return wood_bay_capacity(w,instance,"candidate retired identity capacity exceeded");w->bay_report->retired[w->bay_report->retired_count++]=id;}return true;
}
static bool wood_bay_store(WoodAssemblyContext *w,AsmInstance *a)
{GeoJson j;if(!w->json_parse(w->user,&j,a->content)){geo_json_free(&j);return false;}bool ok=w->instance_content(w->user,a,&j,geo_json_member(&j,0,"source"));geo_json_free(&j);return ok;}
static bool wood_assembly_bay_reconcile(WoodAssemblyContext *w,WoodBayPlan *plans,size_t count)
{
    size_t total=0,new_count=0,deleted_count=0;
    for(size_t i=0;i<w->state->instance_count;++i)if(!w->state->instances[i].bay_repeat)total+=3;
    for(size_t p=0;p<count;++p){WoodBayPlan *plan=&plans[p];total+=plan->count;
        for(size_t i=0;i<plan->count;++i)if(!plan->next[i].timber)++new_count;
        for(size_t i=0;i<plan->value.mapping_count;++i){const AsmMapping *old=&plan->value.mapping[i];bool found=false;for(size_t j=0;j<plan->count;++j)if(wood_assembly_identity_equal(old->identity,plan->next[j].identity))found=true;
            if(!found){++deleted_count;if(!wood_bay_retire(w,plan->value.id,old->timber))return false;}}
    }
    size_t scene_members=w->member_count(w->user)-deleted_count+new_count;
    if(total>ASM_OWNER_MAX||scene_members>ASM_BAY_WORLD_MAX||scene_members>w->member_capacity)
        return wood_bay_capacity(w,0,"candidate exceeds global owned or scene timber capacity");
    if(w->scene_loading){
        for(size_t p=0;p<count;++p){WoodBayPlan *plan=&plans[p];if(plan->count!=plan->value.mapping_count)return wood_bay_bad(w,plan->value.id,"saved mapping does not equal derived identities");for(size_t i=0;i<plan->count;++i)if(!plan->next[i].timber)return wood_bay_bad(w,plan->value.id,"saved mapping lacks a derived identity");}
    }else{
        /* Compare identity before touching the id pool. Every removed id stays
         * reserved throughout this candidate, including other operations. */
        for(size_t p=0;p<count;++p){WoodBayPlan *plan=&plans[p];for(size_t i=0;i<plan->value.mapping_count;++i){const AsmMapping *old=&plan->value.mapping[i];bool keep=false;for(size_t j=0;j<plan->count;++j)if(wood_assembly_identity_equal(old->identity,plan->next[j].identity))keep=true;if(!keep&&!w->remove_member(w->user,old->timber))return false;}}
        for(size_t i=w->state->owner_count;i>0;--i){bool repeat=false;for(size_t p=0;p<count;++p)if(w->state->owners[i-1].instance==plans[p].value.id)repeat=true;if(repeat){memmove(&w->state->owners[i-1],&w->state->owners[i],(w->state->owner_count-i)*sizeof(AsmOwner));memset(&w->state->owners[--w->state->owner_count],0,sizeof(AsmOwner));}}
        for(int phase=0;phase<2;++phase)for(size_t p=0;p<count;++p)for(size_t i=0;i<plans[p].count;++i){AsmMapping *m=&plans[p].next[i];if((m->identity.kind==ASM_ID_SECONDARY)!=(phase!=0)||m->timber)continue;
            uint32_t id=1;while(w->member(w->user,id,NULL)||wood_bay_retired(w,id)){if(id==UINT32_MAX)return wood_bay_capacity(w,plans[p].value.id,"no free timber identity");++id;}m->timber=id;w->allocate_member(w->user,id);}
        for(size_t p=0;p<count;++p){WoodBayPlan *plan=&plans[p];plan->value.mapping_count=plan->count;memset(plan->value.mapping,0,sizeof plan->value.mapping);memcpy(plan->value.mapping,plan->next,plan->count*sizeof(AsmMapping));
            for(size_t i=0;i<plan->count;++i){const AsmMapping *m=&plan->next[i];w->state->owners[w->state->owner_count++]=(AsmOwner){m->timber,plan->value.id,m->identity.key,m->identity.kind,m->identity.left,m->identity.right};}
            if(!wood_bay_store(w,&plan->value))return wood_bay_capacity(w,plan->value.id,"canonical source plus mapping exceeds 8191 UTF-8 bytes");*plan->target=plan->value;}
    }
    if(w->bay_report)for(size_t p=0;p<count;++p)for(size_t i=plans[p].cell_start;i<plans[p].cell_end;++i){AsmBayCellReport *cell=&w->bay_report->cells[i];if(cell->omitted)continue;AsmIdentity id={ASM_ID_SECONDARY,cell->line,cell->left,cell->right};for(size_t k=0;k<plans[p].count;++k)if(wood_assembly_identity_equal(id,plans[p].next[k].identity))cell->timber=plans[p].next[k].timber;}
    return true;
}
bool wood_assembly_bay_prepare(WoodAssemblyContext *w)
{
    size_t count=0;for(size_t i=0;i<w->state->instance_count;++i)if(w->state->instances[i].bay_repeat)++count;if(!count)return true;
    WoodBayPlan *plans=calloc(count,sizeof *plans);if(!plans)return wood_bay_capacity(w,0,"repeat planning allocation failed");bool ok=true;size_t n=0;
    for(size_t i=0;i<w->state->instance_count&&ok;++i)if(w->state->instances[i].bay_repeat)ok=wood_assembly_bay_plan(w,&w->state->instances[i],&plans[n++]);
    if(ok)ok=wood_assembly_bay_reconcile(w,plans,count);free(plans);return ok;
}
bool wood_assembly_bay_check(const WoodAssemblyContext *view,const AsmInstance *a)
{
    WoodAssemblyContext *w=(WoodAssemblyContext *)view;
    for(size_t i=0;i<a->mapping_count;++i){const AsmMapping *m=&a->mapping[i];WoodAssemblyDefinition def;WoodAssemblyMember member;GeoRect2 footprint;
        if(!wood_assembly_bay_member_definition_direct(w,a,m->identity,&def)||!w->member(w->user,m->timber,&member)||!member.placed||!w->footprint(w->user,a->surface_id,m->timber,&footprint))return wood_bay_bad(w,a->id,"owned member has no valid generated geometry");
        GeoRect2 left,right;if(!w->footprint(w->user,a->surface_id,def.between[0],&left)||!w->footprint(w->user,a->surface_id,def.between[1],&right))return false;
        if(m->identity.kind==ASM_ID_PRIMARY){GeoCoord start,finish;if(left.max_v<right.min_v){start=left.max_v;finish=right.min_v;}else if(right.max_v<left.min_v){start=right.max_v;finish=left.min_v;}else return wood_bay_bad(w,a->id,"formal supports have no unique facing range");
            if(w->bay_report)for(size_t r=0;r<w->bay_report->primary_count;++r){const AsmBayPrimaryReport *pre=&w->bay_report->primaries[r];if(pre->instance==a->id&&pre->key==m->identity.key&&(footprint.min_v!=pre->range.min_v||footprint.max_v!=pre->range.max_v))return wood_assembly_bay_failure(w,"INVALID","PRIMARY_RANGE_CHANGED","R55",a->id,m->identity.key,0,"formal primary range equals facing-side preplan","formal primary range differs from preplan");}
            if(footprint.min_v!=start||footprint.max_v!=finish)return wood_assembly_bay_failure(w,"INVALID","PRIMARY_RANGE_CHANGED","R55",a->id,m->identity.key,0,"formal primary range equals facing-side preplan","formal primary range differs from preplan");}
        else if(footprint.min_u!=left.max_u||footprint.max_u!=right.min_u||footprint.min_v<left.min_v||footprint.max_v>left.max_v||footprint.min_v<right.min_v||footprint.max_v>right.max_v)return wood_assembly_bay_failure(w,"INVALID","CELL_CONTACT","I69/R21",a->id,0,m->identity.key,"secondary spans exact inward sides of its two primary identities","secondary contact differs from its mapped cell");
    }return true;
}
static bool wood_asm_bay_operation(WoodAssemblyContext *w,GeoJson *j,int t,const char *op,AsmInstance *old)
{
    bool del=!strcmp(op,"delete-instance"),create=!strcmp(op,"create-instance");
    if(del){for(size_t i=0;i<old->mapping_count;++i)if(!wood_bay_retire(w,old->id,old->mapping[i].timber))return false;
        uint32_t id=old->id;for(size_t i=0;i<old->mapping_count;++i)if(!w->remove_member(w->user,old->mapping[i].timber))return false;
        size_t at=(size_t)(old-w->state->instances);memmove(old,old+1,(w->state->instance_count-at-1)*sizeof *old);memset(&w->state->instances[--w->state->instance_count],0,sizeof *old);
        for(size_t i=w->state->owner_count;i>0;--i)if(w->state->owners[i-1].instance==id){memmove(&w->state->owners[i-1],&w->state->owners[i],(w->state->owner_count-i)*sizeof(AsmOwner));memset(&w->state->owners[--w->state->owner_count],0,sizeof(AsmOwner));}
        w->state->generation_required=w->state->instance_count>0;w->state->bay_required=false;for(size_t i=0;i<w->state->instance_count;++i)w->state->bay_required|=w->state->instances[i].bay_repeat;return true;
    }
    AsmInstance a;int source=geo_json_member(j,t,"value");if(!wood_asm_instance_parse(w,j,source,&a))return false;
    if(!a.bay_repeat||(old&&!old->bay_repeat))return wood_bay_unsupported(w,a.id,"existing instances do not change layout or identity namespace");
    if(old&&old->id!=a.id)return wood_bay_bad(w,a.id,"edited instance identity differs");
    AsmBinding *binding=wood_assembly_binding(w,a.binding_id);char expected[65],actual[65];if(!binding||!wood_asm_hash_token(j,geo_json_member(j,t,"expectedBindingFingerprint"),expected))return wood_bay_bad(w,a.id,"expected binding fingerprint required");
    geo_sha256(binding->content,strlen(binding->content),actual);if(strcmp(expected,actual))return wood_asm_error(w,"STALE: instance binding source changed");
    if(create){if(w->state->instance_count==ASM_INSTANCE_MAX)return wood_bay_capacity(w,a.id,"instance capacity exceeded");old=&w->state->instances[w->state->instance_count++];}
    else{a.mapping_count=old->mapping_count;memcpy(a.mapping,old->mapping,sizeof a.mapping);}
    if(!w->instance_content(w->user,&a,j,source))return wood_bay_capacity(w,a.id,"canonical source plus mapping exceeds 8191 UTF-8 bytes");*old=a;w->state->generation_required=true;w->state->bay_required=true;return true;
}
