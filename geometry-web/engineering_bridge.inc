/* The transport never evaluates dimensions; candidate Worlds use core R31. */
static void eng_bridge_error(const char *code,const char *message)
{
    fputs("{\"ok\":false,\"code\":",stdout);js_string(code);fputs(",\"error\":",stdout);js_string(message);fputs("}\n",stdout);
}
static bool eng_definition_hash(const World *w,char hash[65])
{
    World *copy=malloc(sizeof *copy);FILE *file=tmpfile();
    if(!copy||!file){free(copy);if(file)fclose(file);return false;}
    *copy=*w;copy->canvas_pos_count=0;world_dump_dsl(copy,file);free(copy);
    if(ferror(file)||fflush(file)||fseek(file,0,SEEK_END)){fclose(file);return false;}
    long n=ftell(file);if(n<0||n>ENG_INPUT_MAX||fseek(file,0,SEEK_SET)){fclose(file);return false;}
    char *text=malloc((size_t)n+1);if(!text){fclose(file);return false;}
    size_t got=fread(text,1,(size_t)n,file);bool ok=got==(size_t)n&&!ferror(file);fclose(file);
    if(ok)eng_sha256(text,got,hash);free(text);return ok;
}
static void json_engineering_capabilities(const World *w)
{
    fputs("\"capabilities\":[\"engineering-spec/1\",\"parameters/1\",\"assembly-rule-authoring/1\",\"assembly-timber-generation/1\",\"grid-subdivision-rules/1\",\"section-profile/1\"],\"required_capabilities\":[",stdout);
    if(engineering_used(w))js_string("engineering-spec/1");
    if(w->parameters.card_count){if(engineering_used(w))putchar(',');js_string("parameters/1");}
    if(assembly_used(w)){if(engineering_used(w)||w->parameters.card_count)putchar(',');js_string(ASM_CAPABILITY);}
    if(w->assembly.instance_count){if(engineering_used(w)||w->parameters.card_count||assembly_used(w))putchar(',');js_string(ASM_GENERATION_CAPABILITY);}
    if(grid_subdivision_used(w)){if(engineering_used(w)||w->parameters.card_count||assembly_used(w)||w->assembly.instance_count)putchar(',');js_string(GRID_SUBDIVISION_CAPABILITY);}
    if(sp_used(w)){if(engineering_used(w)||w->parameters.card_count||assembly_used(w)||w->assembly.instance_count||grid_subdivision_used(w))putchar(',');js_string(SP_CAPABILITY);}putchar(']');
    fputs(",\"native_capabilities\":[\"section-profile-native/1\"]",stdout);
}
static void json_engineering_sources(const World *w)
{
    putchar('[');
    for(size_t i=0;i<w->engineering.binding_count;++i){const EngBinding *b=&w->engineering.bindings[i];char source[640],override[640],path[400];Coord value;
        eng_source_json(&b->source,source,sizeof source);if(b->has_override)eng_source_json(&b->override_value,override,sizeof override);else snprintf(override,sizeof override,"null");
        printf("%s{\"target\":",i?",":"");eng_target_json(&b->target,stdout);printf(",\"source\":%s,\"override\":%s,\"effective\":",source,override);
        if(eng_effective((World*)w,b,&value,path,sizeof path)){printf("%lld,\"path\":",(long long)value);js_string(path);}else{fputs("null,\"path\":null,\"error\":",stdout);js_string(g_engineering_error);}putchar('}');
    }putchar(']');
}
static void json_assembly_state(const World *w,bool geometry);
static void json_engineering_state(const World *w,bool geometry)
{
    putchar('{');json_engineering_capabilities(w);fputs(",\"specs\":[",stdout);
    for(size_t i=0;i<w->spec_count;++i){if(i)putchar(',');fputs("{\"name\":",stdout);js_string(w->specs[i].name);printf(",\"value\":%lld}",(long long)w->specs[i].value);}
    fputs("],\"materials\":[",stdout);
    for(size_t i=0;i<w->engineering.material_count;++i){const EngMaterialVersion *m=&w->engineering.materials[i];printf("%s%.*s,\"fingerprint\":\"%s\",\"archived\":%s}",i?",":"",(int)strlen(m->content)-1,m->content,m->fingerprint,m->archived?"true":"false");}
    fputs("],\"methods\":[",stdout);
    for(size_t i=0;i<w->engineering.method_count;++i){const EngMethodVersion *m=&w->engineering.methods[i];printf("%s%.*s,\"fingerprint\":\"%s\",\"archived\":%s}",i?",":"",(int)strlen(m->content)-1,m->content,m->fingerprint,m->archived?"true":"false");}
    fputs("],\"applications\":[",stdout);
    for(size_t i=0;i<w->engineering.application_count;++i){const EngApplication *a=&w->engineering.applications[i];printf("%s%.*s,\"bindings\":[",i?",":"",(int)strlen(a->content)-1,a->content);bool first=true;
        for(size_t k=0;k<w->engineering.binding_count;++k){const EngBinding *b=&w->engineering.bindings[k];if(b->source.kind!=ENG_APPLICATION||strcmp(b->source.ref,a->id))continue;if(!first)putchar(',');first=false;eng_target_json(&b->target,stdout);}fputs("]}",stdout);
    }
    fputs("],\"sources\":",stdout);json_engineering_sources(w);
    fputs(",\"parameters\":[",stdout);
    for(size_t i=0;i<w->parameters.card_count;++i){if(i)putchar(',');parameter_json_card(w,&w->parameters.cards[i],stdout,true);}putchar(']');
    fputs(",\"assembly\":",stdout);json_assembly_state(w,false);
    fputs(",\"sectionProfiles\":",stdout);json_section_profile_state(w);
    if(geometry){fputs(",\"geometry\":{\"grids\":[",stdout);for(size_t i=0;i<w->grid_count;++i){if(i)putchar(',');json_reference_grid(w,&w->grids[i]);}
        fputs("],\"gridSystems\":[",stdout);for(size_t i=0;i<w->grid_system_count;++i){if(i)putchar(',');json_grid_system(w,&w->grid_systems[i]);}
        fputs("],\"datums\":[",stdout);for(size_t i=0;i<w->datum_count;++i){const DatumPlane *d=&w->datums[i];printf("%s{\"id\":%u,\"position\":%lld,\"expression\":",i?",":"",d->id,(long long)d->position);js_string(d->expression);putchar('}');}
        fputs("],\"guides\":[",stdout);for(size_t i=0;i<w->guide_count;++i){if(i)putchar(',');json_reference_guide(w,i);}
        fputs("],\"timbers\":[",stdout);for(size_t i=0;i<w->timber_count;++i){printf("%s{\"id\":%u,\"role\":",i?",":"",w->timbers[i].id);js_string(timber_role_name(w->timbers[i].role));fputs(",\"geometry\":",stdout);json_reference_geometry(w,(int)i);putchar('}');}fputs("]}",stdout);
    }putchar('}');
}
static void cmd_engineering_read(void)
{
    char hash[65];if(!eng_definition_hash(&g_world,hash)){eng_bridge_error("IO","Cannot hash canonical definitions");return;}
    printf("{\"ok\":true,\"revision\":%llu,\"definition_sha256\":\"%s\",\"state\":",(unsigned long long)g_definition_revision,hash);
    json_engineering_state(&g_world,false);fputs("}\n",stdout);
}
static char *eng_read_file(const char *path,size_t *size)
{
    FILE *f=fopen(path,"rb");if(!f){eng_fail("Cannot open engineering input file");return NULL;}
    if(fseek(f,0,SEEK_END)){fclose(f);eng_fail("Cannot read engineering input file");return NULL;}
    long n=ftell(f);if(n<0||n>ENG_INPUT_MAX||fseek(f,0,SEEK_SET)){fclose(f);eng_fail("I10: engineering input exceeds 1 MiB capacity");return NULL;}
    char *text=malloc((size_t)n+1);if(!text){fclose(f);eng_fail("Cannot allocate engineering input");return NULL;}
    *size=fread(text,1,(size_t)n,f);bool ok=*size==(size_t)n&&!ferror(f);fclose(f);if(!ok){free(text);eng_fail("Could not read complete engineering input");return NULL;}
    text[*size]=0;return text;
}
static void json_engineering_preview(void)
{
    char error[512];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:scene_last_error());
    printf("{\"token\":%u,\"valid\":%s,\"revision\":%llu,\"before\":",g_preview.token,g_preview.valid?"true":"false",(unsigned long long)g_preview.revision);
    json_engineering_state(&g_preview.before,true);fputs(",\"after\":",stdout);json_engineering_state(&g_preview.after,true);json_section_profile_impact(&g_preview.before,&g_preview.after);fputs(",\"violations\":[",stdout);
    if(!g_preview.valid){fputs("{\"code\":\"ENGINEERING_INVALID\",\"clause\":\"I8/I35\",\"message\":",stdout);js_string(error);putchar('}');}
    for(size_t i=0;i<g_preview.issue_count;++i){const ReferenceIssue *e=&g_preview.issues[i];printf("%s{\"timber\":%u,\"clause\":",(!g_preview.valid||i)?",":"",e->timber);js_string(e->clause);fputs(",\"expected\":",stdout);js_string(e->expected);fputs(",\"message\":",stdout);js_string(e->actual);putchar('}');}fputs("]}",stdout);
}
/* Shared candidate flow. Each caller keeps its schema, operation, preview JSON, and token kind. */
static void batch_preview(const char *path,const char *schema_name,const char *schema_error,const char *stale_message,const char *memory_message,const char *label,int kind,bool (*operation)(World *,EngJson *,int),void (*write_preview)(void))
{
    g_asm_diagnostic=(AsmDiagnostic){0};
    if(g_hist_grouping){eng_bridge_error("HISTORY_GROUP","Finish or cancel the current history group first");return;}
    size_t size;char *text=eng_read_file(path,&size);if(!text){eng_bridge_error("INPUT",g_engineering_error);return;}
    EngJson j;if(!eng_json_parse_n(&j,text,size)){eng_bridge_error("JSON",j.error);eng_json_free(&j);free(text);return;}
    char schema[40];int64_t revision;int operations=eng_json_member(&j,0,"operations");
    if(!eng_json_keys(&j,0,"schema,expectedRevision,operations","")||!eng_json_string(&j,eng_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,schema_name)||!eng_json_integer(&j,eng_json_member(&j,0,"expectedRevision"),&revision)||revision<0||!eng_json_is_array(&j,operations)){
        eng_bridge_error("SCHEMA",schema_error);eng_json_free(&j);free(text);return;
    }
    if((uint64_t)revision!=g_definition_revision){eng_bridge_error("STALE",stale_message);eng_json_free(&j);free(text);return;}
    int count=eng_json_size(&j,operations);if(count<1||count>ENG_OPERATION_MAX){eng_bridge_error("CAPACITY","Transaction needs 1..256 operations");eng_json_free(&j);free(text);return;}
    World *candidate=malloc(sizeof *candidate);if(!candidate){eng_bridge_error("MEMORY",memory_message);eng_json_free(&j);free(text);return;}*candidate=g_world;
    g_engineering_error[0]=0;g_scene_last_error[0]=0;g_reference_issue_count=0;bool ok=true;
    for(int i=0;i<count&&ok;++i){
        ok=operation(candidate,&j,eng_json_at(&j,operations,i));
        if(ok)ok=assembly_versions_immutable(&g_world,candidate);
    }
    if(ok&&!parameter_retirements_valid(candidate))ok=eng_fail(g_parameter_error);
    parameters_clear_candidate_scratch(candidate);  /* I39/P-062: no scratch reaches comparison, staging, or history */
    if(ok){const World *previous=g_subgrid_before;bool capturing=g_reference_capturing;g_reference_capturing=true;g_reference_trial=*candidate;
        g_subgrid_before=&g_world;ok=world_revalidate(candidate);g_subgrid_before=previous;g_reference_capturing=capturing;
        if(!ok){*candidate=g_reference_trial;if(!g_engineering_error[0])eng_fail(g_revalidate_error[0]?g_revalidate_error:"I35: candidate geometry is invalid");}}
    for(size_t i=0;i<candidate->timber_count&&ok;++i)if(!candidate->timbers[i].placed){ok=eng_fail("I9: candidate still contains an unplaced timber");}
    char *stage_label=(char *)label;reference_stage(&g_world,candidate,&stage_label,1,ok);g_preview.engineering_batch=true;g_preview.assembly_batch=kind==1;g_preview.profile_batch=kind==2;
    if(!ok)g_preview.assembly_diagnostic=g_asm_diagnostic;
    fputs("{\"ok\":true,\"preview\":",stdout);write_preview();fputs("}\n",stdout);
    free(candidate);eng_json_free(&j);free(text);
}
static bool batch_token_kind(int kind)
{
    return g_preview.engineering_batch && (kind==2?g_preview.profile_batch:kind==1?g_preview.assembly_batch:!g_preview.assembly_batch&&!g_preview.profile_batch);
}
static void batch_confirm(const char *arg,int kind,const char *token_message,const char *stale_message)
{
    uint32_t token;bool mine=batch_token_kind(kind);
    if(!arg||!parse_u32(arg,&token)||!g_preview.ready||!mine||g_preview.token!=token||!g_preview.valid){eng_bridge_error("TOKEN",token_message);return;}
    if(g_hist_grouping||g_preview.revision!=g_definition_revision||!world_definitions_equal(&g_world,&g_preview.before)){g_preview.ready=false;eng_bridge_error("STALE",stale_message);return;}
    if(!assembly_versions_immutable(&g_world,&g_preview.after)){g_preview.ready=false;eng_bridge_error("INVALID",g_engineering_error);return;}
    const World *previous=g_subgrid_before;g_subgrid_before=&g_world;bool valid=world_revalidate(&g_preview.after);g_subgrid_before=previous;
    if(!valid){g_preview.ready=false;eng_bridge_error("INVALID",g_revalidate_error);return;}
    bool changed=!world_definitions_equal(&g_world,&g_preview.after);uint64_t before=g_definition_revision;
    if(changed){history_record(&g_world);history_restore_world(&g_world,&g_preview.after);++g_definition_revision;}
    g_preview.ready=false;char hash[65];bool hashed=eng_definition_hash(&g_world,hash);
    printf("{\"ok\":true,\"history_changed\":%s,\"revision\":%llu,\"before_revision\":%llu,\"transaction_id\":%u",changed?"true":"false",(unsigned long long)g_definition_revision,(unsigned long long)before,token);
    if(hashed)printf(",\"definition_sha256\":\"%s\"",hash);fputs("}\n",stdout);
}
static void batch_cancel(const char *arg,int kind,const char *token_message)
{
    uint32_t token;if(!arg||!parse_u32(arg,&token)){eng_bridge_error("TOKEN",token_message);return;}
    bool mine=batch_token_kind(kind);
    bool cancelled=g_preview.ready&&mine&&g_preview.token==token;if(cancelled)g_preview.ready=false;
    printf("{\"ok\":true,\"cancelled\":%s,\"revision\":%llu}\n",cancelled?"true":"false",(unsigned long long)g_definition_revision);
}
static void cmd_engineering_preview(const char *path)
{
    batch_preview(path,"engineering-transaction/1",
        "Expected engineering-transaction/1, expectedRevision and operations",
        "Engineering source changed; read current definitions and preview again",
        "Cannot allocate engineering candidate",
        "engineering-transaction",false,eng_operation,json_engineering_preview);
}
static void cmd_engineering_confirm(const char *arg)
{
    batch_confirm(arg,false,"Missing, invalid or unrelated engineering preview token","Engineering preview expired; preview the current definitions again");
}
static void cmd_engineering_cancel(const char *arg)
{
    batch_cancel(arg,false,"Cancel requires an engineering preview token");
}
static void cmd_engineering_validate(const char *path)
{
    size_t n;char *text=eng_read_file(path,&n);if(!text){eng_bridge_error("INPUT",g_engineering_error);return;}
    if(memchr(text,0,n)||!utf8_is_valid(text)){free(text);eng_bridge_error("ENCODING","Scene must be complete UTF-8 text without NUL bytes");return;}free(text);
    World *candidate=calloc(1,sizeof *candidate);ReferencePreview *preview=malloc(sizeof *preview);
    if(!candidate||!preview){free(candidate);free(preview);eng_bridge_error("MEMORY","Cannot allocate validation candidate");return;}
    *preview=g_preview;uint32_t serial=g_preview_serial;uint64_t revision=g_definition_revision;const World *previous=g_subgrid_before;g_subgrid_before=NULL;
    bool ok=parse_scene_file(path,candidate);char error[512];snprintf(error,sizeof error,"%s",scene_last_error());char hash[65];if(ok)ok=eng_definition_hash(candidate,hash);
    g_preview=*preview;g_preview_serial=serial;g_definition_revision=revision;g_subgrid_before=previous;
    if(ok){fputs("{\"ok\":true,",stdout);json_engineering_capabilities(candidate);printf(",\"definition_sha256\":\"%s\"}\n",hash);}else eng_bridge_error("VALIDATION",error[0]?error:"Cannot validate canonical scene");
    free(preview);free(candidate);
}
