/* Transient candidate evidence. Never part of World/dump or capability data. */
typedef struct { int kind;uint32_t id,field_id,version; } AsmDiagnostic;
static AsmDiagnostic g_asm_diagnostic;
static bool asm_instance_load(World *,EngJson *,int);
/* Authoring validates sources and local topology; it never generates timber. */
static const AsmRuleVersion *assembly_rule(const World *w,uint32_t id,uint32_t version)
{
    const AsmRuleVersion *found=NULL;
    for(size_t i=0;i<w->assembly.rule_count;++i){const AsmRuleVersion *r=&w->assembly.rules[i];
        if(r->id==id && ((!version&&(!found||r->version>found->version))||r->version==version))found=r;}
    return found;
}
static AsmBinding *assembly_binding(World *w,uint32_t id)
{
    for(size_t i=0;i<w->assembly.binding_count;++i)if(w->assembly.bindings[i].id==id)return &w->assembly.bindings[i];
    return NULL;
}
static bool assembly_used(const World *w){return w->assembly.rule_count||w->assembly.binding_count;}
static bool asm_error(const char *format,...)
{
    g_asm_diagnostic=(AsmDiagnostic){0};
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    utf8_trim_tail(g_engineering_error);return false;
}
static bool asm_rule_immutable(uint32_t id,uint32_t version)
{
    bool result=asm_error("D32: published rule %u@%u is immutable",id,version);
    g_asm_diagnostic=(AsmDiagnostic){2,id,0,version};return result;
}
static bool asm_name(EngJson *j,int t,char out[ASM_NAME_MAX])
{return eng_json_string(j,t,out,ASM_NAME_MAX)&&out[0];}
static bool asm_enum(EngJson *j,int t,const char *choices,bool nullable)
{
    char value[40];return (nullable&&eng_json_is_null(j,t))||
        (eng_json_string(j,t,value,sizeof value)&&eng_json_csv_has(choices,value));
}
static bool asm_ids(EngJson *j,int array,uint32_t *ids,size_t *count,size_t limit)
{
    if(!eng_json_is_array(j,array))return false;int n=eng_json_size(j,array);
    if(n<1||(size_t)n>limit)return false;*count=(size_t)n;
    for(int i=0;i<n;++i){int t=eng_json_at(j,array,i);if(!eng_u32(j,eng_json_member(j,t,"id"),&ids[i],true))return false;
        for(int k=0;k<i;++k)if(ids[k]==ids[i])return false;}
    return true;
}
static bool asm_has(const uint32_t *ids,size_t count,uint32_t id)
{for(size_t i=0;i<count;++i)if(ids[i]==id)return true;return false;}
static bool asm_validate_rule(EngJson *j,int t,AsmRuleVersion *r)
{
    uint32_t slots[ASM_SLOT_MAX],members[ASM_MEMBER_MAX],joints[ASM_JOINT_MAX];size_t ns,nm,nj;
    char scopes[ASM_JOINT_MAX][65];uint32_t ends[ASM_JOINT_MAX*2],end_joints[ASM_JOINT_MAX*2];int end_types[ASM_JOINT_MAX*2],end_count=0;
    memset(r,0,sizeof *r);
    if(!eng_json_keys(j,t,"id,version,name,slots,members,joints","")||
       !eng_u32(j,eng_json_member(j,t,"id"),&r->id,true)||!eng_u32(j,eng_json_member(j,t,"version"),&r->version,true)||
       !asm_name(j,eng_json_member(j,t,"name"),r->name))return asm_error("D32: rule needs positive id/version, name and typed slots/members/joints");
    int sa=eng_json_member(j,t,"slots"),ma=eng_json_member(j,t,"members"),ja=eng_json_member(j,t,"joints");
    if(!asm_ids(j,sa,slots,&ns,ASM_SLOT_MAX)||!asm_ids(j,ma,members,&nm,ASM_MEMBER_MAX)||!asm_ids(j,ja,joints,&nj,ASM_JOINT_MAX))
        return asm_error("I40/CAPACITY: rule %u needs 1..8 unique slots, 1..12 unique members and 1..16 unique joints",r->id);
    for(size_t i=0;i<ns;++i){int s=eng_json_at(j,sa,(int)i);char name[ASM_NAME_MAX];
        if(!eng_json_keys(j,s,"id,name","")||!asm_name(j,eng_json_member(j,s,"name"),name))return asm_error("I40: slot %u needs a name; unknown fields are rejected",slots[i]);}
    for(size_t i=0;i<nm;++i){int m=eng_json_at(j,ma,(int)i);uint32_t sid;
        if(!eng_json_keys(j,m,"id,slotId","")||!eng_u32(j,eng_json_member(j,m,"slotId"),&sid,true)||!asm_has(slots,ns,sid))return asm_error("I40: member %u refers to a missing slot",members[i]);}
    for(size_t i=0;i<nj;++i){int a=eng_json_at(j,ja,(int)i);char kind[32],end[16];uint32_t term[2],target;int et[2],nt;
        if(!eng_json_string(j,eng_json_member(j,a,"kind"),kind,sizeof kind)||
           !eng_json_string(j,eng_json_member(j,a,"scope"),scopes[i],sizeof scopes[i])||!scopes[i][0])return asm_error("I40: joint %u needs kind and stable junction scope",joints[i]);
        for(size_t k=0;k<i;++k)if(!strcmp(scopes[k],scopes[i]))return asm_error("I40: joints %u and %u conflict at scope %s",joints[k],joints[i],scopes[i]);
        if(!strcmp(kind,"end-to-side")){
            if(!eng_json_keys(j,a,"id,kind,scope,terminatedMember,targetMember,end,side,dir","")||
               !eng_u32(j,eng_json_member(j,a,"terminatedMember"),&term[0],true)||!eng_u32(j,eng_json_member(j,a,"targetMember"),&target,true)||
               !eng_json_string(j,eng_json_member(j,a,"end"),end,sizeof end)||(strcmp(end,"start")&&strcmp(end,"finish")))return asm_error("I40: joint %u has invalid endpoint definition",joints[i]);
            et[0]=!strcmp(end,"finish");nt=1;
        }else if(!strcmp(kind,"ortho-split")){
            int split=eng_json_member(j,a,"splitMembers");
            if(!eng_json_keys(j,a,"id,kind,scope,continuousMember,splitMembers,side,dir","")||
               !eng_u32(j,eng_json_member(j,a,"continuousMember"),&target,true)||!eng_json_is_array(j,split)||eng_json_size(j,split)!=2||
               !eng_u32(j,eng_json_at(j,split,0),&term[0],true)||!eng_u32(j,eng_json_at(j,split,1),&term[1],true)||term[0]==term[1])return asm_error("I40: joint %u needs one continuous and two distinct split members",joints[i]);
            et[0]=1;et[1]=0;nt=2;
        }else return asm_error("I40: joint %u has unknown kind; nested rules are unsupported",joints[i]);
        if(!asm_has(members,nm,target)||!asm_enum(j,eng_json_member(j,a,"side"),"+u,-u,+v,-v",false)||!asm_enum(j,eng_json_member(j,a,"dir"),"u,v",false))return asm_error("I40: joint %u has missing target or invalid local side/direction",joints[i]);
        for(int k=0;k<nt;++k){if(term[k]==target||!asm_has(members,nm,term[k]))return asm_error("I40: joint %u needs distinct existing members",joints[i]);
            for(int q=0;q<end_count;++q)if(ends[q]==term[k]&&end_types[q]==et[k])return asm_error("I40: joints %u and %u assign the same endpoint of member %u",end_joints[q],joints[i],term[k]);
            ends[end_count]=term[k];end_types[end_count]=et[k];end_joints[end_count++]=joints[i];}
    }
    if(!eng_json_canonical(j,t,r->content,sizeof r->content))return asm_error("CAPACITY: assembly rule exceeds 8191 UTF-8 bytes");
    eng_sha256(r->content,strlen(r->content),r->fingerprint);return true;
}
static bool asm_publish(World *w,EngJson *j,int t,const char *expected)
{
    AsmRuleVersion rule;if(!asm_validate_rule(j,t,&rule))return false;
    if(expected&&strcmp(expected,rule.fingerprint))return asm_error("I41: rule %u@%u fingerprint mismatch",rule.id,rule.version);
    const AsmRuleVersion *old=assembly_rule(w,rule.id,rule.version);
    if(old)return !strcmp(old->fingerprint,rule.fingerprint)||asm_rule_immutable(rule.id,rule.version);
    if(w->assembly.rule_count==ASM_RULE_MAX)return asm_error("CAPACITY: at most 32 published assembly versions");
    w->assembly.rules[w->assembly.rule_count++]=rule;return true;
}
/* Compare with transaction-entry identities, not only the mutable candidate.
 * Removed versions may stay absent after explicit unbinding; an identity that
 * reappears must retain its original content, including delete/copy/reinsert. */
static bool assembly_versions_immutable(const World *before,const World *after)
{
    for(size_t i=0;i<before->assembly.rule_count;++i){const AsmRuleVersion *old=&before->assembly.rules[i];
        const AsmRuleVersion *next=assembly_rule(after,old->id,old->version);
        if(next&&strcmp(old->fingerprint,next->fingerprint))return asm_rule_immutable(old->id,old->version);
    }
    return true;
}
static bool asm_binding_parse(World *w,EngJson *j,int t,AsmBinding *b,bool resolve)
{
    memset(b,0,sizeof *b);int rule=eng_json_member(j,t,"rule"),array=eng_json_member(j,t,"slots");
    if(!eng_json_keys(j,t,"id,name,rule,slots","")||!eng_u32(j,eng_json_member(j,t,"id"),&b->id,true)||!asm_name(j,eng_json_member(j,t,"name"),b->name)||
       !eng_json_keys(j,rule,"id,version","")||!eng_u32(j,eng_json_member(j,rule,"id"),&b->rule_id,true)||!eng_u32(j,eng_json_member(j,rule,"version"),&b->rule_version,true))return asm_error("D33: invalid binding identity or fixed rule reference");
    const AsmRuleVersion *r=assembly_rule(w,b->rule_id,b->rule_version);if(!r)return asm_error("I40: binding %u refers to missing rule %u@%u",b->id,b->rule_id,b->rule_version);
    EngJson definition;if(!eng_json_parse(&definition,r->content)){eng_json_free(&definition);return asm_error("I40: invalid stored rule");}
    uint32_t ids[ASM_SLOT_MAX],seen[ASM_SLOT_MAX];size_t n;bool ok=asm_ids(&definition,eng_json_member(&definition,0,"slots"),ids,&n,ASM_SLOT_MAX);eng_json_free(&definition);
    if(!ok||!eng_json_is_array(j,array)||eng_json_size(j,array)!=(int)n)return asm_error("I40: binding %u must explicitly map every fixed rule slot",b->id);
    b->complete=true;
    for(size_t i=0;i<n;++i){int s=eng_json_at(j,array,(int)i);uint32_t id;
        if(!eng_json_keys(j,s,"slotId,A,B,contactFace,orientation","")||!eng_u32(j,eng_json_member(j,s,"slotId"),&id,true)||!asm_has(ids,n,id)||asm_has(seen,i,id))return asm_error("I40: binding %u has missing, duplicate or unknown slots",b->id);
        seen[i]=id;
        for(int axis=0;axis<2;++axis){int value=eng_json_member(j,s,axis?"B":"A");
            if(eng_json_is_null(j,value)){b->complete=false;continue;}
            g_parameter_dimension_error=(ParameterRef){0};
            EngDimensionSource source={0};EngTarget target={1,0,0,axis};Coord effective;char path[192];
            if(!eng_source_parse(j,value,&source,false)||source.kind==ENG_APPLICATION||(resolve&&!eng_resolve(w,&source,&target,UINT32_MAX,0,&effective,path,sizeof path))){
                char error[256];snprintf(error,sizeof error,"%s",g_engineering_error);
                bool result=asm_error("I40: binding %u slot %u.%c: %.155s",b->id,id,axis?'B':'A',error);
                if(source.kind==ENG_PARAMETER && g_parameter_dimension_error.set &&
                    g_parameter_dimension_error.parameter_id==source.parameter.parameter_id &&
                    g_parameter_dimension_error.field_id==source.parameter.field_id)
                    g_asm_diagnostic=(AsmDiagnostic){1,source.parameter.parameter_id,source.parameter.field_id,0};
                return result;}
        }
        const char *keys[]={"contactFace","orientation"};for(int axis=0;axis<2;++axis){int value=eng_json_member(j,s,keys[axis]);
            if(!asm_enum(j,value,"A,B",true))return asm_error("I40: binding %u slot %u needs explicit A/B or unset %s",b->id,id,keys[axis]);
            if(eng_json_is_null(j,value))b->complete=false;}
    }
    if(!eng_json_canonical(j,t,b->content,sizeof b->content))return asm_error("CAPACITY: binding exceeds 8191 UTF-8 bytes");return true;
}
static bool asm_put_binding(World *w,EngJson *j,int t)
{
    AsmBinding value;if(!asm_binding_parse(w,j,t,&value,false))return false;AsmBinding *b=assembly_binding(w,value.id);
    if(!b){if(w->assembly.binding_count==ASM_BINDING_MAX)return asm_error("CAPACITY: at most 64 assembly bindings");b=&w->assembly.bindings[w->assembly.binding_count++];}
    *b=value;return parameter_declare(w,PARAM_OWNER_ASSEMBLY,value.id,0);
}
static bool assembly_rebuild(World *w,char *error,size_t cap)
{
    if(w->assembly.loading){snprintf(error,cap,"I41: truncated assembly block");return false;}
    for(size_t i=0;i<w->assembly.binding_count;++i){AsmBinding b;EngJson j;bool ok=eng_json_parse(&j,w->assembly.bindings[i].content)&&asm_binding_parse(w,&j,0,&b,true);eng_json_free(&j);
        if(!ok){snprintf(error,cap,"%s",g_engineering_error);return false;}w->assembly.bindings[i]=b;}
    return true;
}
static void asm_remove_position(World *w,int kind,uint32_t id)
{
    for(size_t i=w->canvas_pos_count;i>0;--i)if(w->canvas_pos[i-1].kind==kind&&w->canvas_pos[i-1].id==id){
        memmove(&w->canvas_pos[i-1],&w->canvas_pos[i],(w->canvas_pos_count-i)*sizeof *w->canvas_pos);memset(&w->canvas_pos[--w->canvas_pos_count],0,sizeof *w->canvas_pos);}
}
/* A legacy spec edit previews assembly consumers even without geometry. */
static bool assembly_dimensions_changed(const World *before,const World *after)
{
    for(size_t i=0;i<before->assembly.binding_count;++i){EngJson j;
        if(!eng_json_parse(&j,before->assembly.bindings[i].content)){eng_json_free(&j);return true;}
        int slots=eng_json_member(&j,0,"slots");bool changed=false;
        for(int k=0;k<eng_json_size(&j,slots)&&!changed;++k)for(int axis=0;axis<2&&!changed;++axis){
            int t=eng_json_member(&j,eng_json_at(&j,slots,k),axis?"B":"A");if(eng_json_is_null(&j,t))continue;
            EngDimensionSource src;EngTarget target={1,0,0,axis};Coord a,b;char path[192];
            if(!eng_source_parse(&j,t,&src,false)||!eng_resolve((World*)before,&src,&target,UINT32_MAX,0,&a,path,sizeof path)||
               !eng_resolve((World*)after,&src,&target,UINT32_MAX,0,&b,path,sizeof path)||a!=b)changed=true;
        }
        eng_json_free(&j);if(changed)return true;
    }
    return false;
}
static bool assembly_operation(World *w,EngJson *j,int t)
{
    char op[32];if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return asm_error("I40: assembly operation needs op");
    if(!strcmp(op,"publish-rule"))return eng_json_keys(j,t,"op,value","")?asm_publish(w,j,eng_json_member(j,t,"value"),NULL):asm_error("I40: invalid publish operation");
    if(!strcmp(op,"create-binding")){
        uint32_t id;int value=eng_json_member(j,t,"value");
        if(!eng_json_keys(j,t,"op,value","")||!eng_u32(j,eng_json_member(j,value,"id"),&id,true))return asm_error("I40: invalid new binding identity");
        if(assembly_binding(w,id))return asm_error("I40: new binding %u already exists; edit it explicitly",id);
        return asm_put_binding(w,j,value);
    }
    if(!strcmp(op,"edit-binding")){
        uint32_t id,value_id;char expected[65],actual[65];int value=eng_json_member(j,t,"value");
        if(!eng_json_keys(j,t,"op,id,expectedFingerprint,value","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,true)||
           !eng_u32(j,eng_json_member(j,value,"id"),&value_id,true)||value_id!=id||
           !eng_json_string(j,eng_json_member(j,t,"expectedFingerprint"),expected,sizeof expected)||strlen(expected)!=64)
            return asm_error("I40: invalid explicit binding edit");
        for(size_t i=0;i<64;++i)if(!((expected[i]>='0'&&expected[i]<='9')||(expected[i]>='a'&&expected[i]<='f')))
            return asm_error("I40: invalid binding fingerprint");
        AsmBinding *b=assembly_binding(w,id);if(!b)return asm_error("I40: edited binding %u does not exist",id);
        eng_sha256(b->content,strlen(b->content),actual);
        if(strcmp(expected,actual))return asm_error("STALE: binding %u changed; reopen before editing",id);
        return asm_put_binding(w,j,value);
    }
    if(!strcmp(op,"put-binding"))return eng_json_keys(j,t,"op,value","")?asm_put_binding(w,j,eng_json_member(j,t,"value")):asm_error("I40: invalid binding operation");
    if(!strcmp(op,"delete-binding")){
        uint32_t id;if(!eng_json_keys(j,t,"op,id","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,true))return asm_error("I40: invalid binding id");
        AsmBinding *b=assembly_binding(w,id);if(!b)return asm_error("I40: binding %u does not exist",id);size_t at=(size_t)(b-w->assembly.bindings);
        memmove(b,b+1,(w->assembly.binding_count-at-1)*sizeof *b);memset(&w->assembly.bindings[--w->assembly.binding_count],0,sizeof *b);asm_remove_position(w,CANVAS_POS_ASSEMBLY_BINDING,id);return true;
    }
    if(!strcmp(op,"delete-rule")){
        uint32_t id,version;if(!eng_json_keys(j,t,"op,id,version","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,true)||!eng_u32(j,eng_json_member(j,t,"version"),&version,true))return asm_error("I40: invalid rule identity");
        const AsmRuleVersion *r=assembly_rule(w,id,version);if(!r)return asm_error("I40: rule version does not exist");size_t at=(size_t)(r-w->assembly.rules);
        memmove(&w->assembly.rules[at],&w->assembly.rules[at+1],(w->assembly.rule_count-at-1)*sizeof *r);memset(&w->assembly.rules[--w->assembly.rule_count],0,sizeof *r);
        if(!assembly_rule(w,id,0))asm_remove_position(w,CANVAS_POS_ASSEMBLY_RULE,id);return true;
    }
    if(!strcmp(op,"copy-rule")){
        uint32_t id,version,next;if(!eng_json_keys(j,t,"op,id,version,newId","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,true)||!eng_u32(j,eng_json_member(j,t,"version"),&version,true)||!eng_u32(j,eng_json_member(j,t,"newId"),&next,true)||assembly_rule(w,next,0))return asm_error("I40: copy needs an unused rule identity");
        const AsmRuleVersion *r=assembly_rule(w,id,version);if(!r)return asm_error("I40: copied rule does not exist");EngJson copy;
        if(!eng_json_parse(&copy,r->content)){eng_json_free(&copy);return false;}copy.tokens[eng_json_member(&copy,0,"id")].number=next;copy.tokens[eng_json_member(&copy,0,"version")].number=1;
        bool ok=asm_publish(w,&copy,0,NULL);eng_json_free(&copy);return ok;
    }
    return eng_operation(w,j,t); /* Explicit unbind/delete shares one candidate. */
}
/* Atomic replay uses 768-byte chunks, each safely below SCENE_MAX_LINE. */
static struct {char text[ASM_RECORD_MAX],kind[16],hash[65];size_t used,expected;bool active;} g_assembly_record;
static void asm_dump_record(FILE *out,const char *kind,const char *text)
{
    char hash[65],meta[160],encoded[1100];size_t n;eng_sha256(text,strlen(text),hash);
    snprintf(meta,sizeof meta,"{\"kind\":\"%s\",\"bytes\":%zu,\"sha256\":\"%s\"}",kind,strlen(text),hash);
    eng_base64_encode(meta,strlen(meta),encoded,sizeof encoded,&n);fprintf(out,"assembly record %s\n",encoded);
    for(size_t at=0;at<strlen(text);at+=768){size_t count=strlen(text)-at;if(count>768)count=768;eng_base64_encode(text+at,count,encoded,sizeof encoded,&n);fprintf(out,"assembly data %s\n",encoded);}
    fputs("assembly commit\n",out);
}
static void assembly_dump(const World *w,FILE *out)
{
    if(!assembly_used(w))return;fputs("requires assembly-rule-authoring/1\nassembly begin\n",out);
    for(size_t i=0;i<w->assembly.rule_count;++i)asm_dump_record(out,"rule",w->assembly.rules[i].content);
    for(size_t i=0;i<w->assembly.binding_count;++i)asm_dump_record(out,"binding",w->assembly.bindings[i].content);
    for(size_t i=0;i<w->assembly.instance_count;++i)asm_dump_record(out,"instance",w->assembly.instances[i].content);
    fputs("assembly end\n",out);
}
static bool apply_assembly_line(const char *path,int line_no,char **t,int count,World *w)
{
    bool ok=false;
    if(!g_parsing_scene_file){scene_error(path,line_no,"I41: assembly records require atomic scene loading; edit through preview/confirm");return false;}
    if(count==2&&!strcmp(t[1],"begin")){if(w->assembly.loading)goto fail;w->assembly.loading=true;memset(&g_assembly_record,0,sizeof g_assembly_record);return true;}
    if(!w->assembly.loading)goto fail;
    if(count==2&&!strcmp(t[1],"end")){if(g_assembly_record.active)goto fail;w->assembly.loading=false;char e[256];if(!assembly_rebuild(w,e,sizeof e)){scene_error(path,line_no,e);return false;}return true;}
    if(count==2&&!strcmp(t[1],"commit")){
        if(!g_assembly_record.active||g_assembly_record.used!=g_assembly_record.expected)goto fail;char hash[65];eng_sha256(g_assembly_record.text,g_assembly_record.used,hash);
        if(strcmp(hash,g_assembly_record.hash))goto fail;EngJson j;
        if(eng_json_parse_n(&j,g_assembly_record.text,g_assembly_record.used)){
            if(!strcmp(g_assembly_record.kind,"rule")){uint32_t id,version;ok=eng_u32(&j,eng_json_member(&j,0,"id"),&id,true)&&eng_u32(&j,eng_json_member(&j,0,"version"),&version,true)&&!assembly_rule(w,id,version)&&asm_publish(w,&j,0,g_assembly_record.hash);}
            else if(!strcmp(g_assembly_record.kind,"instance"))ok=asm_instance_load(w,&j,0);
            else {uint32_t id;ok=eng_u32(&j,eng_json_member(&j,0,"id"),&id,true)&&!assembly_binding(w,id)&&asm_put_binding(w,&j,0);}
        }
        eng_json_free(&j);g_assembly_record.active=false;if(ok)return true;goto fail;
    }
    if(count!=3)goto fail;unsigned char decoded[1025];size_t n;
    if(!eng_base64_decode(t[2],strlen(t[2]),decoded,sizeof decoded-1,&n))goto fail;decoded[n]=0;
    if(!strcmp(t[1],"record")){
        if(g_assembly_record.active)goto fail;memset(&g_assembly_record,0,sizeof g_assembly_record);EngJson j;int64_t length;
        ok=eng_json_parse_n(&j,(char*)decoded,n)&&eng_json_keys(&j,0,"kind,bytes,sha256","")&&
           eng_json_string(&j,eng_json_member(&j,0,"kind"),g_assembly_record.kind,sizeof g_assembly_record.kind)&&
           (!strcmp(g_assembly_record.kind,"rule")||!strcmp(g_assembly_record.kind,"binding")||!strcmp(g_assembly_record.kind,"instance"))&&eng_json_integer(&j,eng_json_member(&j,0,"bytes"),&length)&&length>0&&length<ASM_RECORD_MAX&&
           eng_json_string(&j,eng_json_member(&j,0,"sha256"),g_assembly_record.hash,sizeof g_assembly_record.hash)&&strlen(g_assembly_record.hash)==64;
        eng_json_free(&j);if(ok){g_assembly_record.active=true;g_assembly_record.expected=(size_t)length;return true;}
    }else if(!strcmp(t[1],"data")){
        if(!g_assembly_record.active||!n||n>768||g_assembly_record.used+n>g_assembly_record.expected)goto fail;
        memcpy(g_assembly_record.text+g_assembly_record.used,decoded,n);g_assembly_record.used+=n;g_assembly_record.text[g_assembly_record.used]=0;return true;
    }
fail:scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I41: invalid, duplicate, truncated or corrupt assembly record");return false;
}
