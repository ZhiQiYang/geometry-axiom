/* The same native candidate/history machinery as engineering transactions. */
static void json_assembly_state(const World *w,bool geometry)
{
    (void)geometry;printf("{\"capabilities\":[\"assembly-rule-authoring/1\",\"assembly-timber-generation/1\",\"assembly-bay-repeat/1\"],\"limits\":{\"instances\":%d,\"ownedTimbers\":%d,\"worldTimbers\":%d,\"instanceRecordBytes\":%d,\"bayPrimaries\":%d,\"baySecondaryLines\":%d,\"bayOmit\":%d},\"rules\":[",ASM_INSTANCE_MAX,ASM_OWNER_MAX,ASM_BAY_WORLD_MAX,ASM_INSTANCE_RECORD_MAX-1,ASM_BAY_PRIMARY_MAX,ASM_BAY_LINE_MAX,ASM_BAY_OMIT_MAX);
    for(size_t i=0;i<w->wood.assembly.rule_count;++i){const AsmRuleVersion *r=&w->wood.assembly.rules[i];
        printf("%s{\"value\":%s,\"fingerprint\":\"%s\"}",i?",":"",r->content,r->fingerprint);}
    fputs("],\"bindings\":[",stdout);
    for(size_t i=0;i<w->wood.assembly.binding_count;++i){const AsmBinding *b=&w->wood.assembly.bindings[i];
        char fingerprint[65];geo_sha256(b->content,strlen(b->content),fingerprint);
        printf("%s{\"value\":%s,\"fingerprint\":\"%s\",\"complete\":%s,\"effective\":[",i?",":"",b->content,fingerprint,b->complete?"true":"false");
        GeoJson j;if(app_json_parse(&j,b->content)){int array=geo_json_member(&j,0,"slots");
            for(int k=0;k<geo_json_size(&j,array);++k){int slot=geo_json_at(&j,array,k);uint32_t id=0;eng_u32(&j,geo_json_member(&j,slot,"slotId"),&id,true);printf("%s{\"slotId\":%u",k?",":"",id);
                for(int axis=0;axis<2;++axis){int token=geo_json_member(&j,slot,axis?"B":"A");EngDimensionSource source;EngTarget target={1,0,0,axis};Coord value;char path[192];
                    printf(",\"%c\":",axis?'B':'A');
                    EngTerminal terminal={0};
                    if(!geo_json_is_null(&j,token)&&eng_source_parse(&j,token,&source,false)&&eng_resolve_terminal((World*)w,&source,&target,UINT32_MAX,0,&value,path,sizeof path,&terminal)){
                        printf("{\"value\":%lld,\"path\":",(long long)value);js_string(path);fputs(",\"terminal\":",stdout);json_eng_terminal(&terminal);putchar('}');}else fputs("null",stdout);}
                putchar('}');}}
        geo_json_free(&j);fputs("]}",stdout);
    }fputs("],\"instances\":[",stdout);
    for(size_t i=0;i<w->wood.assembly.instance_count;++i){const AsmInstance *a=&w->wood.assembly.instances[i];char fingerprint[65];geo_sha256(a->content,strlen(a->content),fingerprint);
        printf("%s{\"value\":%s,\"fingerprint\":\"%s\",\"members\":[",i?",":"",a->content,fingerprint);
        for(size_t m=0;m<wood_assembly_mapping_count(a);++m){AsmMapping map=wood_assembly_mapping_at(a,m);int at=reference_timber_index(w,map.timber);printf("%s{",m?",":"");json_assembly_identity_fields(map.identity);printf(",\"timberId\":%u,\"geometry\":",map.timber);json_reference_geometry(w,at);fputs(",\"definition\":",stdout);if(at>=0)json_reference_timber_definition(&w->wood.timbers[at],&w->wood.anchors[at]);else fputs("null",stdout);putchar('}');}fputs("]}",stdout);
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
    json_assembly_state(&g_preview.transaction->before,true);fputs(",\"after\":",stdout);json_assembly_state(&g_preview.transaction->after,true);
    json_parameter_rebindings();
    fputs(",\"impact\":",stdout);json_candidate_geometry(&g_preview.transaction->before,&g_preview.transaction->after);
    fputs(",\"bayCells\":",stdout);json_bay_cells();
    fputs(",\"violations\":[",stdout);
    size_t printed=json_bay_issues(false);
    if(!g_preview.valid&&!printed){
        const AsmDiagnostic *d=&g_preview.assembly_diagnostic;
        if(d->kind==1)printf("{\"code\":\"DIMENSION_TYPE\",\"clause\":\"D33\",\"ref\":{\"kind\":\"parameter\",\"id\":%u,\"fieldId\":%u},\"message\":",d->id,d->field_id);
        else if(d->kind==2)printf("{\"code\":\"RULE_VERSION_IMMUTABLE\",\"clause\":\"D32\",\"ref\":{\"kind\":\"rule\",\"id\":%u,\"version\":%u},\"message\":",d->id,d->version);
        else if(strstr(error,"CAPACITY"))fputs("{\"category\":\"CAPACITY\",\"code\":\"CAPACITY\",\"clause\":\"I33/I69\",\"message\":",stdout);
        else if(strstr(error,"UNSUPPORTED"))fputs("{\"category\":\"UNSUPPORTED\",\"code\":\"UNSUPPORTED\",\"clause\":\"D58/I69\",\"message\":",stdout);
        else fprintf(stdout,"{\"code\":\"ASSEMBLY_INVALID\",\"clause\":\"%s\",\"message\":",strstr(g_preview.command,"generation")?"I42":"I40/I41");
        js_string(error);putchar('}');
        ++printed;
    }
    for(size_t i=0;i<g_preview.issue_count;++i){const ReferenceIssue *e=&g_preview.issues[i];printf("%s{\"timber\":%u,\"clause\":",(printed||i)?",":"",e->timber);js_string(e->clause);fputs(",\"expected\":",stdout);js_string(e->expected);fputs(",\"actual\":",stdout);js_string(e->actual);fputs(",\"message\":",stdout);js_string(e->actual);putchar('}');}fputs("]}",stdout);
}
static void cmd_assembly_preview(const char *path)
{
    batch_preview(path,"assembly-transaction/1",
        "Expected assembly-transaction/1, expectedRevision and operations",
        "Assembly source changed; read current definitions and preview again",
        "Cannot allocate assembly candidate",
        "assembly-transaction",true,assembly_operation,json_assembly_preview);
}
static void cmd_assembly_confirm(const char *arg)
{
    batch_confirm(arg,true,"Missing, invalid or unrelated assembly preview token","Assembly preview expired; preview the current definitions again");
}
static void cmd_assembly_cancel(const char *arg)
{
    batch_cancel(arg,true,"Cancel requires an assembly preview token");
}

static void cmd_assembly_generation_preview(const char *path)
{
    batch_preview(path,"assembly-generation-transaction/1","Expected assembly-generation-transaction/1",
        "Generation source changed; read and preview again","Cannot allocate generation candidate",
        "assembly-generation",true,asm_generation_operation,json_assembly_preview);
}
