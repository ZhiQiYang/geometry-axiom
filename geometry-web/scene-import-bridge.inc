/* Scene imports use the native parser once. Metadata is checked against these
 * final typed objects before confirmation installs this exact candidate. */
static World *g_load_before, *g_load_after;
static uint32_t g_load_serial, g_load_token;
static uint64_t g_load_revision;
static bool g_load_ready;

static bool scene_load_prepare(const char *path)
{
    g_load_ready=false;
    if(g_history.grouping){eng_bridge_error("HISTORY_GROUP","Finish or cancel the current history group first");return false;}
    if(g_load_serial==UINT32_MAX){eng_bridge_error("CAPACITY","Restart the service before another scene import");return false;}
    if(!g_load_before)g_load_before=malloc(sizeof *g_load_before);
    if(!g_load_after)g_load_after=malloc(sizeof *g_load_after);
    ReferencePreview *saved=malloc(sizeof *saved);
    if(!g_load_before||!g_load_after||!saved){free(saved);eng_bridge_error("MEMORY","Cannot allocate scene import candidate");return false;}
    *g_load_before=g_world;memset(g_load_after,0,sizeof *g_load_after);
    *saved=g_preview;uint32_t serial=g_preview_serial;uint64_t revision=g_definition_revision;
    const World *previous=g_subgrid_before;g_subgrid_before=NULL;
    bool ok=parse_scene_file(path,g_load_after);
    g_preview=*saved;g_preview_serial=serial;g_definition_revision=revision;g_subgrid_before=previous;free(saved);
    if(!ok){eng_bridge_error("VALIDATION",scene_last_error());return false;}
    g_load_revision=revision;g_load_token=++g_load_serial;g_load_ready=true;return true;
}
static void cmd_load_prepare(const char *path)
{
    if(!scene_load_prepare(path))return;
    /* Serialize this detached World completely before publishing a receipt.
     * Input syntax can require a capability that replay removes from the World. */
    FILE *file=tmpfile();char *canonical=NULL;long size=-1;
    if(file){world_dump_dsl(g_load_after,file);
        if(!ferror(file)&&!fflush(file)&&!fseek(file,0,SEEK_END))size=ftell(file);
        if(size>=0&&(uint64_t)size<SIZE_MAX&&!fseek(file,0,SEEK_SET)){
            canonical=malloc((size_t)size+1);
            if(canonical){size_t got=fread(canonical,1,(size_t)size,file);
                if(got!=(size_t)size||ferror(file)){free(canonical);canonical=NULL;}
                else{char *out=canonical;for(size_t i=0;i<got;++i)if(canonical[i]!='\r')*out++=canonical[i];*out=0;}}
        }
        fclose(file);
    }
    if(!canonical){g_load_ready=false;eng_bridge_error("IO","Cannot serialize scene import candidate");return;}
    printf("{\"ok\":true,\"token\":%u,",g_load_token);json_engineering_capabilities(g_load_after);
    fputs(",\"final_scene\":",stdout);js_string(canonical);free(canonical);
    fputs(",\"final_objects\":{\"boundaries\":[",stdout);
    for(size_t i=0;i<g_load_after->boundary_count;++i)printf("%s%u",i?",":"",g_load_after->boundaries[i].id);
    fputs("],\"boundaryFingerprints\":[",stdout);
    /* Same native pin as boundary reads, from the detached final candidate.
     * One bounded row per boundary; no live World lookup or geometry copy. */
    for(size_t i=0;i<g_load_after->boundary_count;++i){const SpaceBoundarySurface *b=&g_load_after->boundaries[i];
        char hash[65];boundary_geometry_hash(b,hash);
        printf("%s{\"id\":%u,\"geometryFingerprint\":",i?",":"",b->id);js_string(hash);putchar('}');}
    fputs("],\"placements\":[",stdout);
    for(size_t i=0;i<g_load_after->placement_count;++i){const PlacementSurface *p=&g_load_after->placements[i];
        printf("%s{\"id\":%u,\"bid\":%u,\"horizontal\":%s}",i?",":"",p->id,p->boundary_id,
            p->frame.axis_u.z==0&&p->frame.axis_v.z==0?"true":"false");}
    fputs("]}}\n",stdout);
}
static void cmd_load_confirm(const char *arg)
{
    uint32_t token;
    if(!parse_u32(arg,&token)||!g_load_ready||token!=g_load_token){eng_bridge_error("TOKEN","Missing or expired scene import candidate");return;}
    g_load_ready=false;
    if(g_history.grouping||g_definition_revision!=g_load_revision||memcmp(&g_world,g_load_before,sizeof g_world)){
        eng_bridge_error("STALE","Current World changed during scene import; open the project again");return;}
    history_record(&g_world);g_world=*g_load_after;++g_definition_revision;g_preview.ready=false;
    char hash[65];bool hashed=eng_definition_hash(&g_world,hash);
    printf("{\"ok\":true,\"revision\":%llu,",(unsigned long long)g_definition_revision);json_engineering_capabilities(&g_world);
    if(hashed)printf(",\"definition_sha256\":\"%s\"",hash);fputs("}\n",stdout);
}
static void cmd_load_cancel(const char *arg)
{
    uint32_t token;if(!parse_u32(arg,&token)){eng_bridge_error("TOKEN","Cancel requires a scene import token");return;}
    bool cancelled=g_load_ready&&g_load_token==token;if(cancelled)g_load_ready=false;
    printf("{\"ok\":true,\"cancelled\":%s}\n",cancelled?"true":"false");
}
