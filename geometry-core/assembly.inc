/* H: World storage, scene codec and compatibility adapters for W assembly. */
static AsmDiagnostic g_asm_diagnostic;
static bool asm_instance_load(World *,GeoJson *,int);
static void asm_remove_position(World *,int,uint32_t);
static bool app_asm_surface(void *,uint32_t);
static bool app_asm_guide(void *,uint32_t,WoodAssemblyGuide *);
static bool app_asm_member(void *,uint32_t,WoodAssemblyMember *);
static bool app_asm_footprint(void *,uint32_t,uint32_t,GeoRect2 *);
static size_t app_asm_member_count(void *);
static void app_asm_allocate(void *,uint32_t);
static bool app_asm_remove(void *,uint32_t);
static void app_asm_write(void *,const WoodMember *,const WoodAssemblyDefinition *);
static bool app_asm_anchor_matches(void *,uint32_t,const WoodAssemblyDefinition *);
static bool app_asm_instance_content(void *,AsmInstance *,GeoJson *,int);
static bool app_asm_json(void *user,GeoJson *j,const char *text)
{(void)user;return app_json_parse(j,text);}
static void app_asm_drop_position(void *user,bool rule,uint32_t id)
{asm_remove_position((World *)user,rule?CANVAS_POS_ASSEMBLY_RULE:CANVAS_POS_ASSEMBLY_BINDING,id);}
static bool app_asm_other(void *user,GeoJson *j,int t)
{return eng_operation((World *)user,j,t);}
static WoodAssemblyContext app_asm_context(const World *world)
{
    World *w=(World *)world;WoodAssemblyContext c={0};c.state=&w->assembly;c.engineering=app_eng_context(w);c.diagnostic=&g_asm_diagnostic;c.parameter_dimension_error=&g_parameter_dimension_error;c.user=w;c.scene_loading=g_parsing_scene_file;
    c.json_parse=app_asm_json;c.drop_position=app_asm_drop_position;c.other_operation=app_asm_other;c.surface=app_asm_surface;c.guide=app_asm_guide;c.member=app_asm_member;c.footprint=app_asm_footprint;c.member_count=app_asm_member_count;c.member_capacity=WORLD_MAX_TIMBERS;c.allocate_member=app_asm_allocate;c.remove_member=app_asm_remove;c.write_member=app_asm_write;c.anchor_matches=app_asm_anchor_matches;c.instance_content=app_asm_instance_content;return c;
}
static bool asm_error(const char *format,...)
{
    g_asm_diagnostic=(AsmDiagnostic){0};
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    utf8_trim_tail(g_engineering_error);return false;
}
static void asm_remove_position(World *w,int kind,uint32_t id)
{
    for(size_t i=w->canvas_pos_count;i>0;--i)if(w->canvas_pos[i-1].kind==kind&&w->canvas_pos[i-1].id==id){
        memmove(&w->canvas_pos[i-1],&w->canvas_pos[i],(w->canvas_pos_count-i)*sizeof *w->canvas_pos);memset(&w->canvas_pos[--w->canvas_pos_count],0,sizeof *w->canvas_pos);}
}
static const AsmRuleVersion *assembly_rule(const World *w,uint32_t id,uint32_t version)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_rule(&c,id,version);}
static AsmBinding *assembly_binding(World *w,uint32_t id)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_binding(&c,id);}
static bool assembly_used(const World *w)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_used(&c);}
static bool asm_publish(World *w,GeoJson *j,int t,const char *expected)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_publish(&c,j,t,expected);}
static bool asm_put_binding(World *w,GeoJson *j,int t)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_put_binding(&c,j,t);}
static bool assembly_versions_immutable(const World *before,const World *after)
{WoodAssemblyContext a=app_asm_context(before),b=app_asm_context(after);return wood_assembly_versions_immutable(&a,&b);}
static bool assembly_rebuild(World *w,char *error,size_t cap)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_rebuild(&c,error,cap);}
static bool assembly_dimensions_changed(const World *before,const World *after)
{WoodAssemblyContext a=app_asm_context(before),b=app_asm_context(after);return wood_assembly_dimensions_changed(&a,&b);}
static bool assembly_operation(World *w,GeoJson *j,int t)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_operation(&c,j,t);}
/* Atomic replay uses 768-byte chunks, each safely below SCENE_MAX_LINE. */
static struct {char text[ASM_RECORD_MAX],kind[16],hash[65];size_t used,expected;bool active;} g_assembly_record;
static void asm_dump_record(FILE *out,const char *kind,const char *text)
{
    char hash[65],meta[160],encoded[1100];size_t n;geo_sha256(text,strlen(text),hash);
    snprintf(meta,sizeof meta,"{\"kind\":\"%s\",\"bytes\":%zu,\"sha256\":\"%s\"}",kind,strlen(text),hash);
    geo_base64_encode(meta,strlen(meta),encoded,sizeof encoded,&n);fprintf(out,"assembly record %s\n",encoded);
    for(size_t at=0;at<strlen(text);at+=768){size_t count=strlen(text)-at;if(count>768)count=768;geo_base64_encode(text+at,count,encoded,sizeof encoded,&n);fprintf(out,"assembly data %s\n",encoded);}
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
        if(!g_assembly_record.active||g_assembly_record.used!=g_assembly_record.expected)goto fail;char hash[65];geo_sha256(g_assembly_record.text,g_assembly_record.used,hash);
        if(strcmp(hash,g_assembly_record.hash))goto fail;GeoJson j;
        if(app_json_parse_n(&j,g_assembly_record.text,g_assembly_record.used)){
            if(!strcmp(g_assembly_record.kind,"rule")){uint32_t id,version;ok=eng_u32(&j,geo_json_member(&j,0,"id"),&id,true)&&eng_u32(&j,geo_json_member(&j,0,"version"),&version,true)&&!assembly_rule(w,id,version)&&asm_publish(w,&j,0,g_assembly_record.hash);}
            else if(!strcmp(g_assembly_record.kind,"instance"))ok=asm_instance_load(w,&j,0);
            else {uint32_t id;ok=eng_u32(&j,geo_json_member(&j,0,"id"),&id,true)&&!assembly_binding(w,id)&&asm_put_binding(w,&j,0);}
        }
        geo_json_free(&j);g_assembly_record.active=false;if(ok)return true;goto fail;
    }
    if(count!=3)goto fail;unsigned char decoded[1025];size_t n;
    if(!geo_base64_decode(t[2],strlen(t[2]),decoded,sizeof decoded-1,&n))goto fail;decoded[n]=0;
    if(!strcmp(t[1],"record")){
        if(g_assembly_record.active)goto fail;memset(&g_assembly_record,0,sizeof g_assembly_record);GeoJson j;int64_t length;
        ok=app_json_parse_n(&j,(char*)decoded,n)&&geo_json_keys(&j,0,"kind,bytes,sha256","")&&
           geo_json_string(&j,geo_json_member(&j,0,"kind"),g_assembly_record.kind,sizeof g_assembly_record.kind)&&
           (!strcmp(g_assembly_record.kind,"rule")||!strcmp(g_assembly_record.kind,"binding")||!strcmp(g_assembly_record.kind,"instance"))&&geo_json_integer(&j,geo_json_member(&j,0,"bytes"),&length)&&length>0&&length<ASM_RECORD_MAX&&
           geo_json_string(&j,geo_json_member(&j,0,"sha256"),g_assembly_record.hash,sizeof g_assembly_record.hash)&&strlen(g_assembly_record.hash)==64;
        geo_json_free(&j);if(ok){g_assembly_record.active=true;g_assembly_record.expected=(size_t)length;return true;}
    }else if(!strcmp(t[1],"data")){
        if(!g_assembly_record.active||!n||n>768||g_assembly_record.used+n>g_assembly_record.expected)goto fail;
        memcpy(g_assembly_record.text+g_assembly_record.used,decoded,n);g_assembly_record.used+=n;g_assembly_record.text[g_assembly_record.used]=0;return true;
    }
fail:scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I41: invalid, duplicate, truncated or corrupt assembly record");return false;
}
