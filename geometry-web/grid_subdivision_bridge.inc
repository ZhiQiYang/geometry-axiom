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

static void cmd_grid_rule_query(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        json_grid_rule_query_error("來源子規則查詢過長或編碼無效",NULL); putchar('\n'); return;
    }
    char text[SCENE_MAX_LINE]; snprintf(text,sizeof text,"%s",command);
    char *tokens[SCENE_MAX_TOKENS]; int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
    uint32_t id,key,limit=0; int64_t cell[2]; Coord rect[4]; bool cell_query=false,sample=false;
    if (count<5 || (strcmp(tokens[0],"system") && strcmp(tokens[0],"binding") && strcmp(tokens[0],"grid")) ||
        !parse_u32(tokens[1],&id) || strcmp(tokens[2],"rule") || !parse_u32(tokens[3],&key) || !key) goto invalid;
    if (!strcmp(tokens[4],"cell")) {
        if (count!=7 || !parse_i64(tokens[5],&cell[0]) || !parse_i64(tokens[6],&cell[1])) goto invalid;
        cell_query=true;
    } else if (!strcmp(tokens[4],"rect")) {
        if (count!=13 || !parse_coord(tokens[5],&rect[0]) || !parse_coord(tokens[6],&rect[1]) ||
            !parse_coord(tokens[7],&rect[2]) || !parse_coord(tokens[8],&rect[3]) || strcmp(tokens[9],"mode") ||
            (strcmp(tokens[10],"exact") && strcmp(tokens[10],"sample")) || strcmp(tokens[11],"limit") ||
            !parse_u32(tokens[12],&limit) || !limit || limit>GRID_RULE_QUERY_MAX_CELLS ||
            rect[0]>=rect[2] || rect[1]>=rect[3]) goto invalid;
        sample=!strcmp(tokens[10],"sample");
    } else goto invalid;
    GridRuleQueryResult result={0}; char error[256]="";
    bool ok=cell_query?grid_rule_query_cell(&g_world,tokens[0],id,key,cell,&result,error,sizeof error)
        :grid_rule_query_rect(&g_world,tokens[0],id,key,rect,limit,sample,&result,error,sizeof error);
    if (ok) {
        if (cell_query) json_grid_rule_query_cell(&result,&result.cells[0]);
        else json_grid_rule_query_rect(&result);
    } else json_grid_rule_query_error(error,&result);
    grid_rule_query_free(&result); putchar('\n'); return;
invalid:
    json_grid_rule_query_error("grid-rule-query system|binding|grid ID rule K cell I J 或 rect U0 V0 U1 V1 mode exact|sample limit 1..1024",NULL);
    putchar('\n');
}
