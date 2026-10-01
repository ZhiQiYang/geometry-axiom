/* The same native candidate/history machinery as engineering transactions. */
static void json_assembly_state(const World *w,bool geometry)
{
    (void)geometry;fputs("{\"capabilities\":[\"assembly-rule-authoring/1\"],\"rules\":[",stdout);
    for(size_t i=0;i<w->assembly.rule_count;++i){const AsmRuleVersion *r=&w->assembly.rules[i];
        printf("%s{\"value\":%s,\"fingerprint\":\"%s\"}",i?",":"",r->content,r->fingerprint);}
    fputs("],\"bindings\":[",stdout);
    for(size_t i=0;i<w->assembly.binding_count;++i){const AsmBinding *b=&w->assembly.bindings[i];
        printf("%s{\"value\":%s,\"complete\":%s,\"effective\":[",i?",":"",b->content,b->complete?"true":"false");
        EngJson j;if(eng_json_parse(&j,b->content)){int array=eng_json_member(&j,0,"slots");
            for(int k=0;k<eng_json_size(&j,array);++k){int slot=eng_json_at(&j,array,k);uint32_t id=0;eng_u32(&j,eng_json_member(&j,slot,"slotId"),&id,true);printf("%s{\"slotId\":%u",k?",":"",id);
                for(int axis=0;axis<2;++axis){int token=eng_json_member(&j,slot,axis?"B":"A");EngDimensionSource source;EngTarget target={1,0,0,axis};Coord value;char path[192];
                    printf(",\"%c\":",axis?'B':'A');
                    if(!eng_json_is_null(&j,token)&&eng_source_parse(&j,token,&source,false)&&eng_resolve((World*)w,&source,&target,UINT32_MAX,0,&value,path,sizeof path)){
                        printf("{\"value\":%lld,\"path\":",(long long)value);js_string(path);putchar('}');}else fputs("null",stdout);}
                putchar('}');}}
        eng_json_free(&j);fputs("]}",stdout);
    }fputs("]}",stdout);
}
static void cmd_assembly_read(void)
{
    char hash[65];if(!eng_definition_hash(&g_world,hash)){eng_bridge_error("IO","Cannot hash definitions");return;}
    printf("{\"ok\":true,\"revision\":%llu,\"definition_sha256\":\"%s\",\"state\":",(unsigned long long)g_definition_revision,hash);
    json_assembly_state(&g_world,false);fputs("}\n",stdout);
}

static void json_assembly_preview(void)
{
    char error[512];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:scene_last_error());
    printf("{\"token\":%u,\"valid\":%s,\"revision\":%llu,\"before\":",g_preview.token,g_preview.valid?"true":"false",(unsigned long long)g_preview.revision);
    json_assembly_state(&g_preview.before,true);fputs(",\"after\":",stdout);json_assembly_state(&g_preview.after,true);fputs(",\"violations\":[",stdout);
    if(!g_preview.valid){fputs("{\"code\":\"ASSEMBLY_INVALID\",\"clause\":\"I40/I41\",\"message\":",stdout);js_string(error);putchar('}');}
    for(size_t i=0;i<g_preview.issue_count;++i){const ReferenceIssue *e=&g_preview.issues[i];printf("%s{\"timber\":%u,\"clause\":",(!g_preview.valid||i)?",":"",e->timber);js_string(e->clause);fputs(",\"expected\":",stdout);js_string(e->expected);fputs(",\"message\":",stdout);js_string(e->actual);putchar('}');}fputs("]}",stdout);
}
static void cmd_assembly_preview(const char *path)
{
    if(g_hist_grouping){eng_bridge_error("HISTORY_GROUP","Finish or cancel the current history group first");return;}
    size_t size;char *text=eng_read_file(path,&size);if(!text){eng_bridge_error("INPUT",g_engineering_error);return;}
    EngJson j;if(!eng_json_parse_n(&j,text,size)){eng_bridge_error("JSON",j.error);eng_json_free(&j);free(text);return;}
    char schema[40];int64_t revision;int operations=eng_json_member(&j,0,"operations");
    if(!eng_json_keys(&j,0,"schema,expectedRevision,operations","")||!eng_json_string(&j,eng_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"assembly-transaction/1")||!eng_json_integer(&j,eng_json_member(&j,0,"expectedRevision"),&revision)||revision<0||!eng_json_is_array(&j,operations)){
        eng_bridge_error("SCHEMA","Expected assembly-transaction/1, expectedRevision and operations");eng_json_free(&j);free(text);return;
    }
    if((uint64_t)revision!=g_definition_revision){eng_bridge_error("STALE","Engineering source changed; read current definitions and preview again");eng_json_free(&j);free(text);return;}
    int count=eng_json_size(&j,operations);if(count<1||count>ENG_OPERATION_MAX){eng_bridge_error("CAPACITY","Transaction needs 1..256 operations");eng_json_free(&j);free(text);return;}
    World *candidate=malloc(sizeof *candidate);if(!candidate){eng_bridge_error("MEMORY","Cannot allocate engineering candidate");eng_json_free(&j);free(text);return;}*candidate=g_world;
    g_engineering_error[0]=0;g_scene_last_error[0]=0;g_reference_issue_count=0;bool ok=true;
    for(int i=0;i<count&&ok;++i)ok=assembly_operation(candidate,&j,eng_json_at(&j,operations,i));
    if(ok){const World *previous=g_subgrid_before;g_subgrid_before=&g_world;ok=world_revalidate(candidate);g_subgrid_before=previous;if(!ok&&!g_engineering_error[0])eng_fail(g_revalidate_error[0]?g_revalidate_error:"I35: candidate geometry is invalid");}
    for(size_t i=0;i<candidate->timber_count&&ok;++i)if(!candidate->timbers[i].placed){ok=eng_fail("I9: candidate still contains an unplaced timber");}
    char *label="assembly-transaction";reference_stage(&g_world,candidate,&label,1,ok);g_preview.engineering_batch=true;g_preview.assembly_batch=true;
    fputs("{\"ok\":true,\"preview\":",stdout);json_assembly_preview();fputs("}\n",stdout);
    free(candidate);eng_json_free(&j);free(text);
}
static void cmd_assembly_confirm(const char *arg)
{
    uint32_t token;if(!arg||!parse_u32(arg,&token)||!g_preview.ready||!g_preview.assembly_batch||g_preview.token!=token||!g_preview.valid){eng_bridge_error("TOKEN","Missing, invalid or unrelated engineering preview token");return;}
    if(g_hist_grouping||g_preview.revision!=g_definition_revision||!world_definitions_equal(&g_world,&g_preview.before)){g_preview.ready=false;eng_bridge_error("STALE","Engineering preview expired; preview the current definitions again");return;}
    const World *previous=g_subgrid_before;g_subgrid_before=&g_world;bool valid=world_revalidate(&g_preview.after);g_subgrid_before=previous;
    if(!valid){g_preview.ready=false;eng_bridge_error("INVALID",g_revalidate_error);return;}
    bool changed=!world_definitions_equal(&g_world,&g_preview.after);uint64_t before=g_definition_revision;
    if(changed){history_record(&g_world);history_restore_world(&g_world,&g_preview.after);++g_definition_revision;}
    g_preview.ready=false;char hash[65];bool hashed=eng_definition_hash(&g_world,hash);
    printf("{\"ok\":true,\"history_changed\":%s,\"revision\":%llu,\"before_revision\":%llu,\"transaction_id\":%u",changed?"true":"false",(unsigned long long)g_definition_revision,(unsigned long long)before,token);
    if(hashed)printf(",\"definition_sha256\":\"%s\"",hash);fputs("}\n",stdout);
}
static void cmd_assembly_cancel(const char *arg)
{
    uint32_t token;if(!arg||!parse_u32(arg,&token)){eng_bridge_error("TOKEN","Cancel requires an engineering preview token");return;}
    bool cancelled=g_preview.ready&&g_preview.assembly_batch&&g_preview.token==token;if(cancelled)g_preview.ready=false;
    printf("{\"ok\":true,\"cancelled\":%s,\"revision\":%llu}\n",cancelled?"true":"false",(unsigned long long)g_definition_revision);
}
