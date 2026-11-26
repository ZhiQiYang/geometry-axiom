/* Native source-rule query transport. No history, live World, revision or
 * pending reference preview is changed by either query form. */
static void json_grid_rule_query_cell(const GridRuleQueryResult *query,const GridRuleQueryCell *cell)
{
    printf("{\"ok\":true,\"systemId\":%u,\"ruleKey\":%u,\"cell\":[\"%lld\",\"%lld\"],"
        "\"bounds\":[%lld,%lld,%lld,%lld],\"lines\":[",cell->system_id,cell->rule_key,
        (long long)cell->cell[0],(long long)cell->cell[1],(long long)cell->bounds.min_u,
        (long long)cell->bounds.min_v,(long long)cell->bounds.max_u,(long long)cell->bounds.max_v);
    for (size_t i=0;i<cell->line_count;++i) {
        const GridRuleQueryLine *line=&query->lines[cell->line_first+i];
        printf("%s{\"axis\":\"%c\",\"innerIndex\":%u,\"coordinate\":%lld,\"segments\":[",
            i?",":"",line->axis?'v':'u',line->inner_index,(long long)line->coordinate);
        for (size_t j=0;j<line->segment_count;++j) {
            const SurfaceSegment2 *segment=&query->segments[line->segment_first+j];
            printf("%s[[%lld,%lld],[%lld,%lld]]",j?",":"",(long long)segment->start.u,
                (long long)segment->start.v,(long long)segment->end.u,(long long)segment->end.v);
        }
        fputs("],\"ref\":",stdout);
        if (query->has_placed_ref)
            printf("{\"kind\":\"grid-rule-line\",\"appliedGridId\":%u,\"systemId\":%u,\"ruleKey\":%u,"
                "\"cellI\":\"%lld\",\"cellJ\":\"%lld\",\"axis\":\"%c\",\"innerIndex\":%u}",
                query->grid_id,cell->system_id,cell->rule_key,(long long)cell->cell[0],
                (long long)cell->cell[1],line->axis?'v':'u',line->inner_index);
        else fputs("null",stdout);
        putchar('}');
    }
    fputs("]}",stdout);
}

static void json_grid_rule_query_rect(const GridRuleQueryResult *query)
{
    printf("{\"ok\":true,\"complete\":%s,\"requiredCells\":\"%llu\",\"stride\":\"%llu\",\"cells\":[",
        query->complete?"true":"false",(unsigned long long)query->required_cells,
        (unsigned long long)query->stride);
    for (size_t i=0;i<query->cell_count;++i) {
        if (i) putchar(',');
        json_grid_rule_query_cell(query,&query->cells[i]);
    }
    fputs("]}",stdout);
}

static void json_grid_rule_query_error(const char *error,const GridRuleQueryResult *query)
{
    const char *code="QUERY_INVALID";
    if (error && strstr(error,"QUERY_CAPACITY")) code="QUERY_CAPACITY";
    else if (error && strstr(error,"QUERY_OVERFLOW")) code="QUERY_OVERFLOW";
    else if (error && strstr(error,"INDEX_RANGE")) code="INDEX_RANGE";
    fputs("{\"ok\":false,\"code\":",stdout); js_string(code);
    fputs(",\"error\":",stdout); js_string(error && *error?error:"來源子規則查詢失敗");
    if (query && !strcmp(code,"QUERY_CAPACITY")) {
        printf(",\"requiredCells\":\"%llu\"",(unsigned long long)query->required_cells);
        if (query->segments_counted)
            printf(",\"requiredSegments\":\"%llu\"",(unsigned long long)query->required_segments);
    }
    putchar('}');
}

typedef struct {
    const char *kind;
    uint32_t id,key,limit;
    int64_t cell[2];
    Coord rect[4];
    bool cell_query,sample;
} GridRuleQueryRequest;

/* The live and candidate commands have the same bounded query grammar. */
static bool grid_rule_query_request(char **tokens,int count,GridRuleQueryRequest *request)
{
    memset(request,0,sizeof *request);
    if (count<5 || (strcmp(tokens[0],"system") && strcmp(tokens[0],"binding") && strcmp(tokens[0],"grid")) ||
        !parse_u32(tokens[1],&request->id) || strcmp(tokens[2],"rule") ||
        !parse_u32(tokens[3],&request->key) || !request->key) return false;
    request->kind=tokens[0];
    if (!strcmp(tokens[4],"cell")) {
        if (count!=7 || !parse_i64(tokens[5],&request->cell[0]) || !parse_i64(tokens[6],&request->cell[1])) return false;
        request->cell_query=true;
    } else if (!strcmp(tokens[4],"rect")) {
        if (count!=13 || !parse_coord(tokens[5],&request->rect[0]) || !parse_coord(tokens[6],&request->rect[1]) ||
            !parse_coord(tokens[7],&request->rect[2]) || !parse_coord(tokens[8],&request->rect[3]) || strcmp(tokens[9],"mode") ||
            (strcmp(tokens[10],"exact") && strcmp(tokens[10],"sample")) || strcmp(tokens[11],"limit") ||
            !parse_u32(tokens[12],&request->limit) || !request->limit || request->limit>GRID_RULE_QUERY_MAX_CELLS ||
            request->rect[0]>=request->rect[2] || request->rect[1]>=request->rect[3]) return false;
        request->sample=!strcmp(tokens[10],"sample");
    } else return false;
    return true;
}

static bool grid_rule_query_execute(const World *world,const GridRuleQueryRequest *request,
    GridRuleQueryResult *result,char *error,size_t capacity)
{
    return request->cell_query?
        grid_rule_query_cell(world,request->kind,request->id,request->key,request->cell,result,error,capacity):
        grid_rule_query_rect(world,request->kind,request->id,request->key,request->rect,
            request->limit,request->sample,result,error,capacity);
}

static void cmd_grid_rule_query(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        json_grid_rule_query_error("來源子規則查詢過長或編碼無效",NULL); putchar('\n'); return;
    }
    char text[SCENE_MAX_LINE]; snprintf(text,sizeof text,"%s",command);
    char *tokens[SCENE_MAX_TOKENS]; int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
    GridRuleQueryRequest request;
    if (!grid_rule_query_request(tokens,count,&request)) {
        json_grid_rule_query_error("grid-rule-query system|binding|grid ID rule K cell I J 或 rect U0 V0 U1 V1 mode exact|sample limit 1..1024",NULL);
        putchar('\n'); return;
    }
    GridRuleQueryResult result={0}; char error[256]="";
    if (grid_rule_query_execute(&g_world,&request,&result,error,sizeof error)) {
        if (request.cell_query) json_grid_rule_query_cell(&result,&result.cells[0]);
        else json_grid_rule_query_rect(&result);
    } else json_grid_rule_query_error(error,&result);
    grid_rule_query_free(&result); putchar('\n');
}

/* Defined by engineering_bridge.inc. Read the exact engineering owner gate;
 * assembly/profile/finish/timber/PF-6/framing candidates are not interchangeable. */
static bool batch_token_kind(int kind);

static void json_grid_rule_candidate_error(const char *code,const char *error)
{
    fputs("{\"ok\":false,\"code\":",stdout);js_string(code);
    fputs(",\"error\":",stdout);js_string(error);fputs("}\n",stdout);
}

static void cmd_grid_rule_candidate_query(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        json_grid_rule_candidate_error("QUERY_INVALID","候選子規則查詢過長或編碼無效");return;
    }
    char text[SCENE_MAX_LINE];snprintf(text,sizeof text,"%s",command);
    char *tokens[SCENE_MAX_TOKENS];int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
    uint32_t token;GridRuleQueryRequest request;
    if (count && strcmp(tokens[0],"reference") && strcmp(tokens[0],"engineering")) {
        json_grid_rule_candidate_error("CANDIDATE_KIND","候選種類須為 reference 或 engineering");return;
    }
    if (count<4 || !parse_u32(tokens[1],&token) || strcmp(tokens[2],"side") ||
        (strcmp(tokens[3],"before") && strcmp(tokens[3],"after")) ||
        !grid_rule_query_request(tokens+4,count-4,&request)) {
        json_grid_rule_candidate_error("QUERY_INVALID","grid-rule-candidate-query reference|engineering TOKEN side before|after system|binding|grid ID rule K cell I J 或 rect U0 V0 U1 V1 mode exact|sample limit 1..1024");return;
    }
    if (!g_preview.ready || !g_preview.valid || !g_preview.transaction || g_preview.token!=token) {
        json_grid_rule_candidate_error("CANDIDATE_STALE","候選不存在、無效或令牌已過期；請重新預覽");return;
    }
    bool engineering=!strcmp(tokens[0],"engineering");
    bool ordinary=!g_preview.definition_import && !g_preview.pair_batch;
    bool mine=ordinary && (engineering?batch_token_kind(0):
        !g_preview.engineering_batch && !g_preview.timber_batch && !g_preview.pf6_batch &&
        strcmp(g_preview.command,"framing-template-transaction"));
    if (!mine) {
        json_grid_rule_candidate_error("CANDIDATE_KIND","此令牌屬於其他候選種類");return;
    }
    if (g_history.grouping || g_preview.revision!=g_definition_revision ||
        !app_world_candidate_current(g_preview.transaction,&g_world)) {
        json_grid_rule_candidate_error("CANDIDATE_STALE","候選來源已變更；請重新預覽");return;
    }
    /* Borrow the sealed World. Never replay, publish, consume or discard it. */
    const World *world=!strcmp(tokens[3],"before")?
        &g_preview.transaction->before:&g_preview.transaction->after;
    bool exists=!strcmp(request.kind,"system")?world_find_grid_system(world,request.id)!=NULL:
        !strcmp(request.kind,"binding")?world_find_grid_binding(world,request.id)!=NULL:
        world_find_grid(world,request.id)!=NULL;
    if (!exists) {
        json_grid_rule_candidate_error("QUERY_NOT_FOUND","該候選側沒有指定的查詢目標");return;
    }
    ReferenceGrid derived;const GridSystem *source;const PlacementSurface *placement;
    const SpaceBoundarySurface *boundary;PlacementSurface placement_storage;
    SpaceBoundarySurface boundary_storage;char error[256]="";
    if (!grid_rule_target(world,request.kind,request.id,&derived,&source,&placement,&boundary,
        &placement_storage,&boundary_storage,error,sizeof error)) {
        json_grid_rule_query_error(error,NULL);putchar('\n');return;
    }
    const GridSubdivisionRule *rule=grid_rule_find(source,request.key);
    if (!rule) {
        json_grid_rule_candidate_error("QUERY_NOT_FOUND","該候選側沒有指定的來源子規則");return;
    }
    GridRuleQueryResult result={0};
    if (grid_rule_query_execute(world,&request,&result,error,sizeof error)) {
        fputs("{\"ok\":true,\"candidate\":{\"kind\":",stdout);js_string(tokens[0]);
        printf(",\"token\":%u,\"side\":",token);js_string(tokens[3]);
        printf(",\"revision\":\"%llu\"},\"source\":",(unsigned long long)g_preview.revision);
        json_grid_system(world,source);fputs(",\"metrics\":{",stdout);
        for (int axis=0;axis<2;++axis) {
            Coord pitch=geo_grid_axis_pitch(&source->axis[axis]);
            printf("%s\"%c\":{\"pitch\":%lld,\"divisions\":%u,\"innerStep\":%lld}",
                axis?",":"",axis?'v':'u',(long long)pitch,rule->divisions[axis],
                (long long)(pitch/rule->divisions[axis]));
        }
        fputs("},\"query\":",stdout);
        if (request.cell_query) json_grid_rule_query_cell(&result,&result.cells[0]);
        else json_grid_rule_query_rect(&result);
        putchar('}');
    } else json_grid_rule_query_error(error,&result);
    grid_rule_query_free(&result);putchar('\n');
}
