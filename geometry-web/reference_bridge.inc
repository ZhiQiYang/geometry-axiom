/* Structured I8a report, derived geometry for UI, and reference snapping. */
static void json_reference_geometry(const World *w,int i)
{
    if (i<0 || !w->timbers[i].placed) { fputs("null",stdout); return; }
    const Timber *t=&w->timbers[i]; const TimberAnchor *a=&w->anchors[i];
    const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 f;
    if (!p || !timber_a0_footprint_uv(p,t,a,&f)) { fputs("null",stdout); return; }
    bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
    Coord center=(along?f.min_u:f.min_v)+t->size_a/2;
    printf("{\"surface\":%u,\"centerline\":%lld,\"length\":%lld,\"u\":%lld,\"v\":%lld,\"dir\":\"%s\",\"side\":\"%s\",\"A\":%lld,\"B\":%lld,\"origin\":[%lld,%lld,%lld]}",
        a->placement_id,(long long)center,(long long)t->length,(long long)a->uv.u,(long long)a->uv.v,
        length_dir_word(a->length_direction),depth_side_word(a->depth_side),(long long)t->size_a,(long long)t->size_b,
        (long long)t->origin.x,(long long)t->origin.y,(long long)t->origin.z);
}
static void json_reference_preview(void)
{
    printf("{\"token\":%u,\"valid\":%s,\"command\":",g_preview.token,g_preview.valid?"true":"false");
    js_string(g_preview.command); fputs(",\"timbers\":[",stdout); bool first=true;
    for (size_t i=0;i<g_preview.before.timber_count;++i) {
        const Timber *t=&g_preview.before.timbers[i]; if (!t->placed) continue;
        int j=reference_timber_index(&g_preview.after,t->id);
        if (!first) putchar(','); first=false;
        printf("{\"id\":%u,\"before\":",t->id); json_reference_geometry(&g_preview.before,(int)i);
        fputs(",\"after\":",stdout); json_reference_geometry(&g_preview.after,j); putchar('}');
    }
    fputs("],\"violations\":[",stdout);
    for (size_t i=0;i<g_preview.issue_count;++i) {
        const ReferenceIssue *e=&g_preview.issues[i];
        printf("%s{\"timber\":%u,\"clause\":",i?",":"",e->timber); js_string(e->clause);
        fputs(",\"expected\":",stdout); js_string(e->expected);
        fputs(",\"actual\":",stdout); js_string(e->actual); putchar('}');
    }
    fputs("]}",stdout);
}
static void cmd_reference_result(bool ok,uint32_t old_token)
{
    printf("{\"ok\":%s",ok?"true":"false");
    if (!ok) { fputs(",\"error\":",stdout); js_string(scene_last_error()); }
    if (g_preview.ready && g_preview.token!=old_token) { fputs(",\"preview\":",stdout); json_reference_preview(); }
    fputs("}\n",stdout);
}
static void cmd_references(void)
{
    fputs("{\"ok\":true,\"guides\":[",stdout);
    for (size_t i=0;i<g_world.guide_count;++i) {
        const GuideLine *g=&g_world.guides[i];
        printf("%s{\"id\":%u,\"surface\":%u,\"axis\":\"%s\",\"off\":%lld,\"expression\":",i?",":"",g->id,g->placement_id,g->direction==GUIDE_ALONG_U?"u":"v",(long long)g->offset);
        js_string(g->expression); putchar('}');
    }
    fputs("],\"grids\":[",stdout);
    for (size_t i=0;i<g_world.grid_count;++i) {
        const ReferenceGrid *g=&g_world.grids[i];
        const PlacementSurface *p=world_find_placement(&g_world,g->placement_id);
        printf("%s{\"id\":%u,\"surface\":%u",i?",":"",g->id,g->placement_id);
        for (int axis=0;axis<2;++axis) {
            Coord values[GRID_MAX_LINES]; size_t count=0;
            if (p) grid_axis_lines(g,p,world_placement_boundary(&g_world,p),axis,values,&count,NULL,0);
            printf(",\"%c\":[",axis?'v':'u');
            for (size_t k=0;k<count;++k) printf("%s%lld",k?",":"",(long long)values[k]);
            putchar(']');
        }
        putchar('}');
    }
    fputs("],\"timbers\":[",stdout); bool first=true;
    for (size_t i=0;i<g_world.timber_count;++i) {
        if (!g_world.timbers[i].placed) continue;
        printf("%s{\"id\":%u,\"role\":",first?"":",",g_world.timbers[i].id); first=false;
        js_string(timber_role_name(g_world.timbers[i].role)); fputs(",\"geometry\":",stdout);
        json_reference_geometry(&g_world,(int)i); putchar('}');
    }
    fputs("],\"specs\":[",stdout);
    for (size_t i=0;i<g_world.spec_count;++i) {
        printf("%s{\"name\":",i?",":""); js_string(g_world.specs[i].name);
        printf(",\"value\":%lld}",(long long)g_world.specs[i].value);
    }
    fputs("]}\n",stdout);
}
static void cmd_snap_reference(const char *args)
{
    unsigned pid,exclude; char dir; long long at,radius; char tail;
    if (sscanf(args,"%u %c %u %lld %lld %c",&pid,&dir,&exclude,&at,&radius,&tail)!=5 ||
        (dir!='u' && dir!='v') || !coord_in_range(at) || radius<0 || radius>COORD_LIMIT) {
        fputs("{\"ok\":false,\"error\":\"snap surface u|v excludeGuide at radius\"}\n",stdout); return;
    }
    char expr[REF_EXPR_MAX];
    if (!reference_snap(&g_world,pid,dir=='u'?GUIDE_ALONG_U:GUIDE_ALONG_V,exclude,at,radius,expr)) {
        fputs("{\"ok\":false,\"error\":\"R5: 附近沒有合法引用，請先宣告具名規格或選擇既有邊／線\"}\n",stdout); return;
    }
    fputs("{\"ok\":true,\"expression\":",stdout); js_string(expr); fputs("}\n",stdout);
}
