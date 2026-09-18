/* Structured I8a report, derived geometry for UI, and reference snapping. */
static void json_reference_geometry(const World *w,int i)
{
    if (i<0 || !w->timbers[i].placed) { fputs("null",stdout); return; }
    const Timber *t=&w->timbers[i]; const TimberAnchor *a=&w->anchors[i];
    const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 f;
    if (!p || !timber_a0_footprint_uv(p,t,a,&f)) { fputs("null",stdout); return; }
    bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
    Coord center=(along?f.min_u:f.min_v)+t->size_a/2;
    printf("{\"surface\":%u,\"centerline\":%lld,\"length\":%lld,\"u\":%lld,\"v\":%lld,\"dir\":\"%s\",\"side\":\"%s\",\"A\":%lld,\"B\":%lld,\"origin\":[%lld,%lld,%lld]",
        a->placement_id,(long long)center,(long long)t->length,(long long)a->uv.u,(long long)a->uv.v,
        length_dir_word(a->length_direction),depth_side_word(a->depth_side),(long long)t->size_a,(long long)t->size_b,
        (long long)t->origin.x,(long long)t->origin.y,(long long)t->origin.z);
    printf(",\"axes\":[[%lld,%lld,%lld],[%lld,%lld,%lld],[%lld,%lld,%lld]]}",
        (long long)t->axis_length.x,(long long)t->axis_length.y,(long long)t->axis_length.z,
        (long long)t->axis_a.x,(long long)t->axis_a.y,(long long)t->axis_a.z,
        (long long)t->axis_b.x,(long long)t->axis_b.y,(long long)t->axis_b.z);
}
static void json_reference_guide(const World *w,size_t i)
{
    const GuideLine *g=&w->guides[i];
    const PlacementSurface *p=world_find_placement(w,g->placement_id);
    if (!g->resolved || !p) { fputs("null",stdout); return; }
    printf("{\"id\":%u,\"surface\":%u,\"source\":\"%s\",\"datum\":%u,\"axis\":\"%s\",\"off\":%lld,\"expression\":",
        g->id,g->placement_id,g->source==GUIDE_DATUM?"datum":"local",g->datum_id,
        g->direction==GUIDE_ALONG_U?"u":"v",(long long)g->offset);
    js_string(g->expression);
    Vector3 along=g->direction==GUIDE_ALONG_U?p->frame.axis_u:p->frame.axis_v;
    Vector3 cross=g->direction==GUIDE_ALONG_U?p->frame.axis_v:p->frame.axis_u;
    printf(",\"worldPoint\":[%lld,%lld,%lld],\"worldDirection\":[%lld,%lld,%lld],\"segments\":[",
        (long long)(p->frame.origin.x+cross.x*g->offset),(long long)(p->frame.origin.y+cross.y*g->offset),(long long)(p->frame.origin.z+cross.z*g->offset),
        (long long)along.x,(long long)along.y,(long long)along.z);
    SurfaceSegment2 segments[POLY_MAX_VERTICES];
    size_t count=guide_line_get_local_segments(p,world_placement_boundary(w,p),g,segments,POLY_MAX_VERTICES);
    for (size_t j=0;j<count;++j) printf("%s[[%lld,%lld],[%lld,%lld]]",j?",":"",
        (long long)segments[j].start.u,(long long)segments[j].start.v,
        (long long)segments[j].end.u,(long long)segments[j].end.v);
    fputs("]}",stdout);
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
    fputs("],\"guides\":[",stdout);
    for (size_t i=0;i<g_preview.before.guide_count;++i) {
        const GuideLine *g=&g_preview.before.guides[i];
        printf("%s{\"id\":%u,\"before\":",i?",":"",g->id); json_reference_guide(&g_preview.before,i);
        fputs(",\"after\":",stdout); size_t j=0;
        while (j<g_preview.after.guide_count && g_preview.after.guides[j].id!=g->id) ++j;
        if (j==g_preview.after.guide_count) fputs("null",stdout); else json_reference_guide(&g_preview.after,j);
        putchar('}');
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
        if (i) putchar(','); json_reference_guide(&g_world,i);
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
    fputs("],\"datums\":[",stdout);
    for (size_t i=0;i<g_world.datum_count;++i) {
        const DatumPlane *d=&g_world.datums[i];
        printf("%s{\"id\":%u,\"axis\":\"%c\",\"position\":%lld,\"expression\":",i?",":"",d->id,"XYZ"[d->axis],(long long)d->position);
        js_string(d->expression); fputs(",\"guides\":[",stdout); bool first=true;
        for (size_t j=0;j<g_world.guide_count;++j) if (g_world.guides[j].source==GUIDE_DATUM && g_world.guides[j].datum_id==d->id) {
            printf("%s%u",first?"":",",g_world.guides[j].id); first=false;
        }
        fputs("]}",stdout);
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
