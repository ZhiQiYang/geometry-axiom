/* R17 host adapter. It only authors the existing closed D16a package; all
 * geometry, validation, freshness and publication remain in the native route.
 * Context/owner keys are runtime metadata, never World or saved definitions. */
typedef struct {
    Coord a,b;
    char edge[24],direction[4],side[4];
} BoundaryPairHostMember;
typedef struct {
    uint32_t token;
    char owner[65],kind[12];
} BoundaryPairHostPending;
static char g_boundary_pair_context[65];
static BoundaryPairHostPending g_boundary_pair_host_pending;

static bool boundary_pair_host_key(const char *text)
{
    if(strlen(text)!=64)return false;
    for(size_t i=0;i<64;++i)if(!((text[i]>='0'&&text[i]<='9')||(text[i]>='a'&&text[i]<='f')))return false;
    return true;
}
static bool boundary_pair_host_document(const char *path,GeoJson *j,char **text)
{
    size_t size;*text=eng_read_file(path,&size);
    if(!*text){eng_bridge_error("BOUNDARY_PAIR_INPUT",g_engineering_error);return false;}
    if(size>1024*1024||memchr(*text,0,size)||!utf8_is_valid(*text)){
        eng_bridge_error("BOUNDARY_PAIR_INPUT","成組資料須為 1 MiB 內的完整 UTF-8，且不含 NUL");free(*text);*text=NULL;return false;
    }
    if(!app_json_parse_n(j,*text,size)){
        eng_bridge_error("BOUNDARY_PAIR_INPUT",j->error);geo_json_free(j);free(*text);*text=NULL;return false;
    }
    for(int i=0;i<j->count;++i)if(j->tokens[i].type==GEO_J_STRING)
        for(const unsigned char *p=(unsigned char*)j->tokens[i].string;*p;++p)if(*p<32||*p==127){
            eng_bridge_error("BOUNDARY_PAIR_INPUT","成組資料不得包含控制字元");geo_json_free(j);free(*text);*text=NULL;return false;
        }
    return true;
}
static bool boundary_pair_host_context(void)
{
    if(g_boundary_pair_context[0]||timber_edit_random_key(g_boundary_pair_context))return true;
    eng_bridge_error("BOUNDARY_PAIR_RANDOM","無法建立原生候選擁有碼");return false;
}
static bool boundary_pair_host_on_boundary(uint32_t timber,uint32_t boundary)
{
    int index=reference_timber_index(&g_world,timber);if(index<0)return false;
    const PlacementSurface *p=world_find_placement(&g_world,g_world.wood.anchors[index].placement_id);
    return p&&p->boundary_id==boundary;
}
static void cmd_boundary_pair_read(const char *path)
{
    GeoJson j;char *text;if(!boundary_pair_host_document(path,&j,&text))return;
    char schema[40];uint32_t boundary;
    if(!geo_json_keys(&j,0,"schema,boundaryId","")||!geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||
        strcmp(schema,"boundary-pair-read/1")||!eng_u32(&j,geo_json_member(&j,0,"boundaryId"),&boundary,true)||
        !world_find_boundary(&g_world,boundary)){
        eng_bridge_error("BOUNDARY_PAIR_SCHEMA","讀取需要 boundary-pair-read/1 與現有邊界識別");goto done;
    }
    if(!boundary_pair_host_context())goto done;
    printf("{\"ok\":true,\"schema\":\"boundary-pair-read-result/1\",\"boundaryId\":%u,\"revision\":\"%llu\",\"contextKey\":",boundary,(unsigned long long)g_definition_revision);
    js_string(g_boundary_pair_context);
    fputs(",\"complete\":false,\"memberDimensionSources\":[\"literal\"],\"groups\":[",stdout);
    bool first=true;
    for(size_t i=0;i<g_world.wood.boundary_pair_count;++i){
        const WoodBoundaryPair *pair=&g_world.wood.boundary_pairs[i];
        if(!boundary_pair_host_on_boundary(pair->first,boundary)||!boundary_pair_host_on_boundary(pair->second,boundary))continue;
        int at=reference_timber_index(&g_world,pair->first);
        printf("%s{\"first\":%u,\"second\":%u,\"ids\":[%u,%u],\"on\":%u,\"members\":[",first?"":",",pair->first,pair->second,pair->first,pair->second,g_world.wood.anchors[at].placement_id);first=false;
        json_pair_member(&g_world,pair->first);putchar(',');json_pair_member(&g_world,pair->second);
        fputs("],\"contacts\":",stdout);json_pair_contacts(&g_world,pair->first,pair->second);putchar('}');
    }
    fputs("]}\n",stdout);
done:geo_json_free(&j);free(text);
}
static bool boundary_pair_host_ids(GeoJson *j,int at,uint32_t ids[2])
{
    return geo_json_is_array(j,at)&&geo_json_size(j,at)==2&&
        eng_u32(j,geo_json_at(j,at,0),&ids[0],false)&&eng_u32(j,geo_json_at(j,at,1),&ids[1],false)&&ids[0]!=ids[1];
}
static bool boundary_pair_host_allocate(uint32_t ids[2])
{
    if(g_world.wood.timber_count>WORLD_MAX_TIMBERS-2)return false;
    WORLD_NEXT_ID(ids[0],g_world.wood.timbers,g_world.wood.timber_count,false);
    /* Same native wrap-safe policy as newid, with the first private id reserved.
     * A preview does not append a timber or consume an identity serial. */
    ids[1]=ids[0]+1;
    for(size_t i=0;i<=g_world.wood.timber_count+1;++i,++ids[1])
        if(ids[1]!=ids[0]&&reference_timber_index(&g_world,ids[1])<0)return true;
    return false;
}
static bool boundary_pair_host_member(GeoJson *j,int at,BoundaryPairHostMember *member)
{
    uint32_t edge;
    if(!geo_json_keys(j,at,"A,B,edge,direction,side","")||!eng_coord(j,geo_json_member(j,at,"A"),&member->a,true)||
        !eng_coord(j,geo_json_member(j,at,"B"),&member->b,true)||
        !geo_json_string(j,geo_json_member(j,at,"edge"),member->edge,sizeof member->edge)||
        member->edge[0]!='e'||!parse_u32(member->edge+1,&edge)||(member->edge[1]=='0'&&member->edge[2])||
        !geo_json_string(j,geo_json_member(j,at,"direction"),member->direction,sizeof member->direction)||
        (strcmp(member->direction,"+u")&&strcmp(member->direction,"-u")&&strcmp(member->direction,"+v")&&strcmp(member->direction,"-v"))||
        !geo_json_string(j,geo_json_member(j,at,"side"),member->side,sizeof member->side)||
        (strcmp(member->side,"+n")&&strcmp(member->side,"-n")))return false;
    return true;
}
static bool boundary_pair_host_existing(const uint32_t ids[2],uint32_t boundary)
{
    int a=boundary_pair_index(&g_world,ids[0]),b=boundary_pair_index(&g_world,ids[1]);
    return a>=0&&a==b&&boundary_pair_host_on_boundary(ids[0],boundary)&&boundary_pair_host_on_boundary(ids[1],boundary);
}
typedef struct {const char *kind;bool written;} BoundaryPairHostReport;
static void boundary_pair_host_failure_report(const char *message,void *opaque)
{
    BoundaryPairHostReport *report=opaque;
    /* Read the same failed native candidate before its mandatory discard.
     * Never change World/preview, publish a token, or evaluate a second candidate. */
    fputs("{\"ok\":false,\"code\":\"BOUNDARY_PAIR_INVALID\",\"error\":",stdout);js_string(message);
    fputs(",\"diagnostics\":{\"type\":\"boundary-pair\",\"kind\":",stdout);js_string(report->kind);putchar(',');
    json_reference_preview_payload(false);fputs("}}\n",stdout);report->written=true;
}
static void cmd_boundary_pair_preview(const char *path)
{
    GeoJson j;char *text;if(!boundary_pair_host_document(path,&j,&text))return;
    char schema[40],context[65],kind[12];uint64_t revision;uint32_t boundary,on=0,ids[2];BoundaryPairHostMember members[2];
    int operation=geo_json_member(&j,0,"operation");
    if(!geo_json_keys(&j,0,"schema,boundaryId,contextKey,expectedRevision,operation","")||
        !geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"boundary-pair-transaction/1")||
        !eng_u32(&j,geo_json_member(&j,0,"boundaryId"),&boundary,true)||!world_find_boundary(&g_world,boundary)||
        !geo_json_string(&j,geo_json_member(&j,0,"contextKey"),context,sizeof context)||!boundary_pair_host_key(context)||
        !timber_edit_revision(&j,geo_json_member(&j,0,"expectedRevision"),&revision)||
        !geo_json_string(&j,geo_json_member(&j,operation,"op"),kind,sizeof kind)){
        eng_bridge_error("BOUNDARY_PAIR_SCHEMA","預覽需要版本、原生 contextKey、來源版本、邊界與完整成組操作");goto done;
    }
    if(!g_boundary_pair_context[0]||strcmp(context,g_boundary_pair_context)){
        eng_bridge_error("CONTEXT","成組資料屬於其他原生工作區，請重新讀取");goto done;
    }
    if(revision!=g_definition_revision){eng_bridge_error("STALE","來源已變更，請重新讀取並預覽整組");goto done;}
    if(g_history.grouping){eng_bridge_error("HISTORY_GROUP","請先結束目前的歷史群組");goto done;}
    if(g_preview.ready||g_pair_interactive.active){eng_bridge_error("PENDING","已有待確認的候選或成組輸入；請由原操作確認或取消");goto done;}
    bool creating=!strcmp(kind,"create"),redeclaring=!strcmp(kind,"redeclare"),deleting=!strcmp(kind,"delete");
    if(!creating&&!redeclaring&&!deleting){eng_bridge_error("BOUNDARY_PAIR_SCHEMA","只接受 create、redeclare 或 delete");goto done;}
    if(!geo_json_keys(&j,operation,creating?"op,on,members":redeclaring?"op,on,ids,members":"op,ids","")){
        eng_bridge_error("BOUNDARY_PAIR_SCHEMA","成組操作含缺少或未支援的欄位");goto done;
    }
    if(!creating&&(!boundary_pair_host_ids(&j,geo_json_member(&j,operation,"ids"),ids)||!boundary_pair_host_existing(ids,boundary))){
        eng_bridge_error("BOUNDARY_PAIR_SCOPE","須明示目前邊界上同一組的兩個成員");goto done;
    }
    if(!deleting){
        const PlacementSurface *placement;
        int array=geo_json_member(&j,operation,"members");
        if(!eng_u32(&j,geo_json_member(&j,operation,"on"),&on,false)||!(placement=world_find_placement(&g_world,on))||placement->boundary_id!=boundary){
            eng_bridge_error("BOUNDARY_PAIR_SCOPE","承載面必須屬於目前選取的邊界");goto done;
        }
        if(!geo_json_is_array(&j,array)||geo_json_size(&j,array)!=2||
            !boundary_pair_host_member(&j,geo_json_at(&j,array,0),&members[0])||!boundary_pair_host_member(&j,geo_json_at(&j,array,1),&members[1])){
            eng_bridge_error("BOUNDARY_PAIR_INPUT","須完整指定兩支 boundary 的字面 A/B、外環邊、方向與深度側");goto done;
        }
        if(creating&&!boundary_pair_host_allocate(ids)){eng_bridge_error("CAPACITY","沒有足夠的角材容量或未使用識別");goto done;}
    }
    BoundaryPairHostPending pending={0};
    if(!timber_edit_random_key(pending.owner)){eng_bridge_error("BOUNDARY_PAIR_RANDOM","無法建立候選擁有碼");goto done;}
    snprintf(pending.kind,sizeof pending.kind,"%s",kind);
    char line[160];bool ok;
    BoundaryPairHostReport report={kind,false};
    BoundaryPairInvalidReport previous_report=g_pair_invalid_report;void *previous_context=g_pair_invalid_report_context;
    g_pair_invalid_report=boundary_pair_host_failure_report;g_pair_invalid_report_context=&report;
    g_scene_last_error[0]=0;
    if(deleting){
        snprintf(line,sizeof line,"boundary-pair delete %u %u",ids[0],ids[1]);
        ok=feed_line("boundary-pair-host",++g_input_line_no,line,&g_world);
    }else{
        snprintf(line,sizeof line,"boundary-pair begin %u %u",ids[0],ids[1]);
        ok=feed_line("boundary-pair-host",++g_input_line_no,line,&g_world);
        for(int i=0;i<2&&ok;++i){
            snprintf(line,sizeof line,"timber %u %lld %lld role boundary",ids[i],(long long)members[i].a,(long long)members[i].b);
            ok=feed_line("boundary-pair-host",++g_input_line_no,line,&g_world);
        }
        for(int i=0;i<2&&ok;++i){
            snprintf(line,sizeof line,"place %u on %u at-face %s %s %s",ids[i],on,members[i].edge,members[i].direction,members[i].side);
            ok=feed_line("boundary-pair-host",++g_input_line_no,line,&g_world);
        }
        if(ok)ok=feed_line("boundary-pair-host",++g_input_line_no,"boundary-pair end",&g_world);
    }
    g_pair_invalid_report=previous_report;g_pair_invalid_report_context=previous_context;
    if(!ok||!g_preview.ready||!g_preview.pair_batch){
        /* The command owns only the input it just began; another request cannot
         * interleave inside this bridge command. Never cancel a foreign token. */
        g_pair_interactive.active=false;
        if(!report.written)eng_bridge_error("BOUNDARY_PAIR_INVALID",scene_last_error()[0]?scene_last_error():"無法建立成組候選");goto done;
    }
    pending.token=g_preview.token;g_boundary_pair_host_pending=pending;
    printf("{\"ok\":true,\"history_changed\":false,\"revision\":\"%llu\",\"ownerKey\":",(unsigned long long)g_definition_revision);js_string(pending.owner);
    fputs(",\"preview\":{\"type\":\"boundary-pair\",\"kind\":",stdout);js_string(kind);
    printf(",\"noOp\":%s,",world_definitions_equal(&g_preview.transaction->before,&g_preview.transaction->after)?"true":"false");
    json_reference_preview_fields();fputs("}}\n",stdout);
done:geo_json_free(&j);free(text);
}
static void cmd_boundary_pair_token(const char *arg,bool cancel)
{
    char text[112],*parts[3];uint32_t token;
    if(!arg||strlen(arg)>=sizeof text){eng_bridge_error("TOKEN","成組操作需要 token 與擁有碼");return;}
    snprintf(text,sizeof text,"%s",arg);int count=split_tokens(text,parts,3);
    if(count!=2||!parse_u32(parts[0],&token)||!boundary_pair_host_key(parts[1])||
        !g_preview.ready||!g_preview.pair_batch||g_preview.token!=token||
        g_boundary_pair_host_pending.token!=token||strcmp(g_boundary_pair_host_pending.owner,parts[1])){
        eng_bridge_error("TOKEN","成組 token 已失效、擁有碼不符或屬於其他候選");return;
    }
    if(!cancel&&g_history.grouping){
        boundary_pair_discard_preview();memset(&g_boundary_pair_host_pending,0,sizeof g_boundary_pair_host_pending);
        eng_bridge_error("HISTORY_GROUP","歷史群組已改變，請結束群組後重新預覽整組");return;
    }
    uint64_t before=g_definition_revision;char line[80];
    snprintf(line,sizeof line,cancel?"boundary-pair cancel":"boundary-pair confirm %u",token);
    bool ok=feed_line("boundary-pair-host",++g_input_line_no,line,&g_world);
    memset(&g_boundary_pair_host_pending,0,sizeof g_boundary_pair_host_pending);
    printf("{\"ok\":%s,\"history_changed\":%s,\"revision\":\"%llu\",\"before_revision\":\"%llu\",\"transaction_id\":%u",ok?"true":"false",ok&&before!=g_definition_revision?"true":"false",(unsigned long long)g_definition_revision,(unsigned long long)before,token);
    if(cancel)printf(",\"cancelled\":%s",ok?"true":"false");
    if(!ok){fputs(",\"code\":\"STALE_OR_INVALID\",\"error\":",stdout);js_string(scene_last_error());}
    fputs("}\n",stdout);
}
