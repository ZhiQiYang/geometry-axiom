/* D30/R32: read-only transport of lattice identities and core-clipped queries. */
static void json_boundary_definition(const World *w,const SpaceBoundarySurface *b,bool response)
{
    const BoundaryVertexKeys *keys=world_find_vertex_keys(w,b->id);
    char hash[65]=""; boundary_geometry_hash(b,hash);
    printf("{%s\"id\":%u,\"geometryFingerprint\":",response?"\"ok\":true,":"",b->id); js_string(hash);
    printf(",\"kind\":\"%s\",\"keysPersisted\":%s,\"loops\":[",
        b->kind==BOUNDARY_ROOM_PLAN?"room_plan":b->kind==BOUNDARY_WALL_ELEVATION?"wall_elevation":"unspecified",
        keys?"true":"false");
    for (int li=-1;li<(int)b->hole_count;++li) {
        const PolygonLoop2 *loop=li<0?&b->outline:&b->holes[li]; size_t ki=(size_t)(li+1);
        printf("%s{\"loop\":%d,\"verts\":[",li>=0?",":"",li);
        for (size_t i=0;i<loop->count;++i)
            printf("%s[%lld,%lld]",i?",":"",(long long)loop->v[i].u,(long long)loop->v[i].v);
        fputs("],\"fixity\":[",stdout);
        for (size_t i=0;i<loop->count;++i) printf("%s%d",i?",":"",loop->fixity[i]==EDGE_FREE?0:1);
        fputs("],\"vertices\":[",stdout);
        for (size_t i=0;i<loop->count;++i) {
            printf("%s{\"index\":%zu,\"key\":",i?",":"",i);
            if (keys && ki<keys->loop_count && i<keys->counts[ki]) printf("%u",keys->keys[ki][i]);
            else fputs("null",stdout);
            printf(",\"uv\":[%lld,%lld]}",(long long)loop->v[i].u,(long long)loop->v[i].v);
        }
        fputs("]}",stdout);
    }
    fputs("]}",stdout);
}

static bool boundary_preview_changed(const SpaceBoundarySurface *before,const SpaceBoundarySurface *after)
{
    if (!before || !after) return true;
    char a[65]="",b[65]=""; boundary_geometry_hash(before,a); boundary_geometry_hash(after,b);
    if (strcmp(a,b)) return true;
    const BoundaryVertexKeys *ak=world_find_vertex_keys(&g_preview.before,before->id);
    const BoundaryVertexKeys *bk=world_find_vertex_keys(&g_preview.after,after->id);
    if (!ak || !bk) return ak!=bk;
    if (ak->loop_count!=bk->loop_count) return true;
    for (size_t li=0;li<ak->loop_count;++li) {
        if (ak->counts[li]!=bk->counts[li]) return true;
        for (size_t i=0;i<ak->counts[li];++i) if (ak->keys[li][i]!=bk->keys[li][i]) return true;
    }
    return false;
}

static void json_boundary_preview(void)
{
    fputs(",\"boundaries\":[",stdout); bool first=true;
    for (size_t i=0;i<g_preview.before.boundary_count;++i) {
        const SpaceBoundarySurface *before=&g_preview.before.boundaries[i];
        const SpaceBoundarySurface *after=world_find_boundary(&g_preview.after,before->id);
        if (!boundary_preview_changed(before,after)) continue;
        printf("%s{\"id\":%u,\"before\":",first?"":",",before->id); first=false;
        json_boundary_definition(&g_preview.before,before,false); fputs(",\"after\":",stdout);
        if (after) json_boundary_definition(&g_preview.after,after,false); else fputs("null",stdout);
        putchar('}');
    }
    for (size_t i=0;i<g_preview.after.boundary_count;++i) {
        const SpaceBoundarySurface *after=&g_preview.after.boundaries[i];
        if (world_find_boundary(&g_preview.before,after->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",after->id); first=false;
        json_boundary_definition(&g_preview.after,after,false); putchar('}');
    }
    putchar(']');
}

static void json_grid_query_axes(const GridQueryAxis axes[2])
{
    fputs("{",stdout);
    for (int axis=0;axis<2;++axis) {
        const GridQueryAxis *a=&axes[axis];
        printf("%s\"%c\":{\"defined\":%s,\"firstIndex\":",axis?",":"",axis?'v':'u',a->defined?"true":"false");
        if (a->defined && a->total) printf("\"%lld\"",(long long)a->first); else fputs("null",stdout);
        fputs(",\"lastIndex\":",stdout);
        if (a->defined && a->total) printf("\"%lld\"",(long long)a->last); else fputs("null",stdout);
        printf(",\"total\":\"%llu\",\"stride\":\"%llu\",\"lines\":[",
            (unsigned long long)a->total,(unsigned long long)a->stride);
        for (size_t k=0;k<a->count;++k) {
            const GridQueryLine *line=&a->lines[k];
            printf("%s{\"index\":\"%lld\",\"coordinate\":%lld,\"segments\":[",k?",":"",
                (long long)line->index,(long long)line->coordinate);
            for (size_t j=0;j<line->segment_count;++j) {
                const SurfaceSegment2 *s=&line->segments[j];
                printf("%s{\"a\":[%lld,%lld],\"b\":[%lld,%lld]",j?",":"",
                    (long long)s->start.u,(long long)s->start.v,(long long)s->end.u,(long long)s->end.v);
                if (line->segment_has_band[j]) printf(",\"band\":\"%lld\"",(long long)line->segment_band[j]);
                putchar('}');
            }
            fputs("]}",stdout);
        }
        fputs("]}",stdout);
    }
    putchar('}');
}

static void json_grid_query_result(const GridQueryAxis axes[2],const Coord rect[4],bool sample)
{
    printf("{\"ok\":true,\"mode\":\"%s\",\"exact\":%s,\"rect\":[%lld,%lld,%lld,%lld],\"axes\":",
        sample?"sample":"exact",sample?"false":"true",(long long)rect[0],(long long)rect[1],
        (long long)rect[2],(long long)rect[3]);
    json_grid_query_axes(axes); putchar('}');
}

static void json_grid_query_error(const char *error)
{
    const char *code="QUERY_INVALID";
    if (error && strstr(error,"QUERY_CAPACITY")) code="QUERY_CAPACITY";
    else if (error && strstr(error,"QUERY_OVERFLOW")) code="QUERY_OVERFLOW";
    else if (error && strstr(error,"INDEX_RANGE")) code="INDEX_RANGE";
    fputs("{\"ok\":false,\"code\":",stdout); js_string(code);
    fputs(",\"error\":",stdout); js_string(error && *error?error:"網格查詢失敗"); putchar('}');
}

static void cmd_grid_query(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        json_grid_query_error("網格查詢過長或編碼無效"); putchar('\n'); return;
    }
    char text[SCENE_MAX_LINE]; snprintf(text,sizeof text,"%s",command);
    char *tokens[SCENE_MAX_TOKENS]; int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
    Coord rect[4]; uint32_t id,limit;
    if (count!=11 || (strcmp(tokens[0],"system") && strcmp(tokens[0],"binding") && strcmp(tokens[0],"grid")) ||
        !parse_u32(tokens[1],&id) || strcmp(tokens[2],"rect") ||
        !parse_coord(tokens[3],&rect[0]) || !parse_coord(tokens[4],&rect[1]) ||
        !parse_coord(tokens[5],&rect[2]) || !parse_coord(tokens[6],&rect[3]) ||
        strcmp(tokens[7],"mode") || (strcmp(tokens[8],"exact") && strcmp(tokens[8],"sample")) ||
        strcmp(tokens[9],"limit") || !parse_u32(tokens[10],&limit) || limit<1 || limit>GRID_MAX_LINES ||
        rect[0]>rect[2] || rect[1]>rect[3]) {
        json_grid_query_error("grid-query system|binding|grid ID rect U0 V0 U1 V1 mode exact|sample limit 1..64");
        putchar('\n'); return;
    }
    GridQueryAxis *axes=calloc(2,sizeof *axes); char error[256]="";
    if (!axes) { json_grid_query_error("網格查詢記憶體不足"); putchar('\n'); return; }
    bool sample=!strcmp(tokens[8],"sample");
    if (grid_query(&g_world,tokens[0],id,rect,limit,sample,axes,error,sizeof error))
        json_grid_query_result(axes,rect,sample);
    else json_grid_query_error(error);
    free(axes); putchar('\n');
}

/* Presentation-only source trial. No live World, revision, undo or pending
 * I8a preview is touched. The scratch world carries only current parameters;
 * this is not an impact/engineering validation of existing applications. */
static void cmd_grid_trial_query(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        json_grid_query_error("試擺查詢過長或編碼無效"); putchar('\n'); return;
    }
    char text[SCENE_MAX_LINE]; snprintf(text,sizeof text,"%s",command);
    char *tokens[SCENE_MAX_TOKENS]; int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
    Coord rect[4]; uint32_t id;
    if (count<15 || strcmp(tokens[0],"rect") ||
        !parse_coord(tokens[1],&rect[0]) || !parse_coord(tokens[2],&rect[1]) ||
        !parse_coord(tokens[3],&rect[2]) || !parse_coord(tokens[4],&rect[3]) ||
        rect[0]>=rect[2] || rect[1]>=rect[3] || strcmp(tokens[5],"grid-system") || !parse_u32(tokens[6],&id)) {
        json_grid_query_error("grid-trial-query rect U0 V0 U1 V1 grid-system ...；矩形須有正面積"); putchar('\n'); return;
    }
    World *draft=calloc(1,sizeof *draft);
    GridQueryAxis *axes=calloc(2,sizeof *axes); char error[256]="";
    if (!draft || !axes) { free(draft); free(axes); json_grid_query_error("試擺記憶體不足"); putchar('\n'); return; }
    draft->parameters=g_world.parameters;
    g_scene_last_error[0]='\0';
    bool ok=apply_grid_system_line("trial",0,tokens+5,count-5,draft);
    const GridSystem *source=ok?world_find_grid_system(draft,id):NULL;
    if (!source || !grid_system_is_infinite(source)) json_grid_query_error(ok?"試擺只接受無限網格來源":scene_last_error());
    else if (grid_query(draft,"system",id,rect,GRID_MAX_LINES,false,axes,error,sizeof error)) json_grid_query_result(axes,rect,false);
    else json_grid_query_error(error);
    free(axes); free(draft); putchar('\n');
}

static bool grid_binding_preview_rect(const World *w,const GridBinding *binding,Coord rect[4])
{
    const SpaceBoundarySurface *b=world_find_boundary(w,binding->boundary_id);
    if (!b || !b->outline.count) return false;
    rect[0]=rect[2]=b->outline.v[0].u; rect[1]=rect[3]=b->outline.v[0].v;
    for (size_t i=1;i<b->outline.count;++i) {
        rect[0]=coord_min(rect[0],b->outline.v[i].u); rect[2]=coord_max(rect[2],b->outline.v[i].u);
        rect[1]=coord_min(rect[1],b->outline.v[i].v); rect[3]=coord_max(rect[3],b->outline.v[i].v);
    }
    return true;
}

static void json_grid_binding(const World *w,const GridBinding *binding,bool with_preview)
{
    Coord translation[2]; bool representable=grid_binding_translation(w,binding,translation);
    printf("{\"kind\":\"grid-binding\",\"id\":%u,\"boundary\":%u,\"system\":%u,\"vertexKey\":%u,"
        "\"cell\":[\"%lld\",\"%lld\"],\"anchor\":[{\"num\":%u,\"den\":%u},{\"num\":%u,\"den\":%u}],\"translation\":",
        binding->id,binding->boundary_id,binding->system_id,binding->vertex_key,
        (long long)binding->cell[0],(long long)binding->cell[1],binding->anchor_num[0],binding->anchor_den[0],
        binding->anchor_num[1],binding->anchor_den[1]);
    if (representable) printf("[%lld,%lld]",(long long)translation[0],(long long)translation[1]); else fputs("null",stdout);
    fputs(",\"translationExact\":",stdout);
    if (representable) printf("[\"%lld\",\"%lld\"]",(long long)translation[0],(long long)translation[1]);
    else fputs("null",stdout);
    printf(",\"translationRepresentable\":%s,\"applications\":[",representable?"true":"false");
    bool first=true;
    for (size_t i=0;i<w->grid_count;++i) {
        const ReferenceGrid *g=&w->grids[i]; if (!g->from_binding || g->binding_id!=binding->id) continue;
        printf("%s{\"grid\":%u,\"surface\":%u}",first?"":",",g->id,g->placement_id); first=false;
    }
    fputs("],",stdout);
    const CanvasPos *pos=NULL;
    for (size_t i=0;i<w->canvas_pos_count;++i) {
        if (w->canvas_pos[i].kind==CANVAS_POS_GRID_BINDING && w->canvas_pos[i].id==binding->id) { pos=&w->canvas_pos[i]; break; }
    }
    printf("\"cx\":%lld,\"cy\":%lld,\"hasPos\":%s",pos?(long long)pos->x:0LL,
        pos?(long long)pos->y:0LL,pos?"true":"false");
    if (with_preview) {
        Coord rect[4]; GridQueryAxis *axes=calloc(2,sizeof *axes); char error[256]="";
        fputs(",\"preview\":",stdout);
        if (axes && grid_binding_preview_rect(w,binding,rect) &&
            grid_query(w,"binding",binding->id,rect,GRID_MAX_LINES,true,axes,error,sizeof error))
            json_grid_query_result(axes,rect,true);
        else json_grid_query_error(error[0]?error:"無法產生配置預覽");
        free(axes);
    }
    putchar('}');
}

static void json_grid_binding_preview(void)
{
    fputs(",\"gridBindings\":[",stdout); bool first=true;
    for (size_t i=0;i<geo_grid_bindings_count(&g_preview.before.grid_store);++i) {
        const GridBinding *before=geo_grid_bindings_at(&g_preview.before.grid_store,i);
        const GridBinding *after=world_find_grid_binding(&g_preview.after,before->id);
        printf("%s{\"id\":%u,\"before\":",first?"":",",before->id); first=false;
        json_grid_binding(&g_preview.before,before,true); fputs(",\"after\":",stdout);
        if (after) json_grid_binding(&g_preview.after,after,true); else fputs("null",stdout);
        putchar('}');
    }
    for (size_t i=0;i<geo_grid_bindings_count(&g_preview.after.grid_store);++i) {
        const GridBinding *after=geo_grid_bindings_at(&g_preview.after.grid_store,i);
        if (world_find_grid_binding(&g_preview.before,after->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",after->id); first=false;
        json_grid_binding(&g_preview.after,after,true); putchar('}');
    }
    putchar(']');
}
