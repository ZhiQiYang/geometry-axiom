#include "assembly.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

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
static bool wood_asm_instance_parse(WoodAssemblyContext *w,GeoJson *j,int t,AsmInstance *a)
{
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
    if(!geo_json_keys(j,t,"source,mapping","")||!wood_asm_instance_parse(w,j,source,&a)||
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
    if(w->state->owner_count!=w->state->instance_count*3)return wood_asm_error(w,"I42: orphan owned records or missing instance mapping");
    if(w->state->instance_count&&!w->state->generation_required)return wood_asm_error(w,"I42: missing required generation capability");
    for(size_t i=0;i<w->state->owner_count;++i){const AsmOwner *o=&w->state->owners[i];bool found=false;
        for(size_t k=0;k<w->state->instance_count;++k)for(int m=0;m<3;++m){const AsmInstance *a=&w->state->instances[k];if(o->instance==a->id&&o->member==a->member[m]&&o->timber==a->timber[m])found=true;}
        if(!found||!w->member(w->user,o->timber,NULL))return wood_asm_error(w,"I42: invalid owned mapping");
        for(size_t k=0;k<i;++k)if(w->state->owners[k].timber==o->timber||(w->state->owners[k].instance==o->instance&&w->state->owners[k].member==o->member))return wood_asm_error(w,"I42: duplicate owner identity");
    }return true;
}
static int wood_asm_member_index(const AsmInstance *a,uint32_t id)
{for(int i=0;i<3;++i)if(a->member[i]==id)return i;return -1;}
static bool wood_asm_member_definition(WoodAssemblyContext *w,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{if(w->evaluation&&w->evaluation->generated)return w->evaluation->generated(w->evaluation->user,a,m,out);return wood_assembly_member_definition_direct(w,a,m,out);}
bool wood_assembly_member_definition_direct(WoodAssemblyContext *w,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{
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
    out->surface_id=a->surface_id;out->guide_id=a->guide[m];out->direction=a->secondary[m]?ASM_DIR_U:ASM_DIR_V;out->role=a->secondary[m]?WOOD_MEMBER_ROLE_SECONDARY:WOOD_MEMBER_ROLE_PRIMARY;out->timber_id=a->timber[m];out->reserved=0;
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
    if(del){
        AsmInstance copy=*old;size_t at=(size_t)(old-w->state->instances);memmove(old,old+1,(w->state->instance_count-at-1)*sizeof *old);memset(&w->state->instances[--w->state->instance_count],0,sizeof *old);
        for(int m=0;m<3;++m)if(!w->remove_member(w->user,copy.timber[m]))return false;
        for(size_t i=w->state->owner_count;i>0;--i)if(w->state->owners[i-1].instance==id){memmove(&w->state->owners[i-1],&w->state->owners[i],(w->state->owner_count-i)*sizeof(AsmOwner));memset(&w->state->owners[--w->state->owner_count],0,sizeof(AsmOwner));}w->state->generation_required=w->state->instance_count>0;return true;
    }
    if(edit){if(!wood_asm_instance_parse(w,j,source,&value))return false;if(value.id!=id)return wood_asm_error(w,"I42: edited instance identity mismatch");}
    AsmBinding *binding=wood_assembly_binding(w,value.binding_id);if(!binding||!wood_asm_hash_token(j,geo_json_member(j,t,"expectedBindingFingerprint"),expected))return wood_asm_error(w,"I42: expected binding fingerprint required");geo_sha256(binding->content,strlen(binding->content),actual);if(strcmp(expected,actual))return wood_asm_error(w,"STALE: instance binding source changed");
    if(edit){for(int m=0;m<3;++m){int at=wood_asm_member_index(old,value.member[m]);if(at<0||old->secondary[at]!=value.secondary[m])return wood_asm_error(w,"D34/UNSUPPORTED: member membership/roles cannot change");value.timber[m]=old->timber[at];}}
    else {
        if(w->state->instance_count==ASM_INSTANCE_MAX||w->member_count(w->user)+3>w->member_capacity)return wood_asm_error(w,"CAPACITY: at most 16 instances within native timber capacity");
        for(int phase=0;phase<2;++phase)for(int m=0;m<3;++m)if(value.secondary[m]==(phase!=0)){uint32_t tid=1;while(w->member(w->user,tid,NULL)){if(tid==UINT32_MAX)return wood_asm_error(w,"CAPACITY: no free timber identity");++tid;}value.timber[m]=tid;w->allocate_member(w->user,tid);w->state->owners[w->state->owner_count++]=(AsmOwner){tid,value.id,value.member[m]};}
        old=&w->state->instances[w->state->instance_count++];
    }
    if(!w->instance_content(w->user,&value,j,source))return false;*old=value;w->state->generation_required=true;return true;
}
bool wood_assembly_instance_load(WoodAssemblyContext *w,GeoJson *j,int t)
{
    if(!w->state->generation_required||!geo_json_keys(j,t,"source,mapping","")||w->state->instance_count==ASM_INSTANCE_MAX)return wood_asm_error(w,"I42: instance needs generation capability and source/mapping");AsmInstance a;int source=geo_json_member(j,t,"source"),map=geo_json_member(j,t,"mapping");if(!wood_asm_instance_parse(w,j,source,&a)||wood_assembly_instance(w,a.id)||!geo_json_is_array(j,map)||geo_json_size(j,map)!=3)return wood_asm_error(w,"I42: invalid or duplicate instance mapping");
    for(int i=0;i<3;++i){int v=geo_json_at(j,map,i);uint32_t member,tid;if(!geo_json_keys(j,v,"memberId,timberId","")||!wood_eng_u32(j,geo_json_member(j,v,"memberId"),&member,true)||!wood_eng_u32(j,geo_json_member(j,v,"timberId"),&tid,true))return false;int m=wood_asm_member_index(&a,member);if(m<0||a.timber[m])return wood_asm_error(w,"I42: duplicate/missing mapped member");a.timber[m]=tid;}
    if(!w->instance_content(w->user,&a,j,source))return false;
    /* Persisted owned definitions must equal sources before reconstruction, not be silently repaired. */
    for(int m=0;m<3;++m){WoodAssemblyDefinition expected;if(!wood_asm_member_definition(w,&a,m,&expected))return false;WoodAssemblyMember actual;if(!w->member(w->user,a.timber[m],&actual))return wood_asm_error(w,"I42: saved owned timber missing");
        if(actual.width!=expected.width||actual.depth!=expected.depth||actual.role!=expected.role||!actual.placed||!w->anchor_matches(w->user,a.timber[m],&expected))return wood_asm_error(w,"I42: saved owned definitions differ from instance sources");
    }
    w->state->instances[w->state->instance_count++]=a;return true;
}
