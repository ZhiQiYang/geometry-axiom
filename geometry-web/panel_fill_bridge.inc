/* PF-1 native transport for D41 finish surfaces (panel-fill-native/1).
 * Every derived value below (F, R_k, q, relation) is recomputed per response and never stored (I56, R4).
 * Layers (I53) need a panel fill's thickness t and a derived placement's h; PF-1 reports them as pending. */
static void fs_json_axis(Vector3 a)
{
    char sign=(a.x+a.y+a.z)>0?'+':'-',letter=a.x?'X':a.y?'Y':'Z';
    printf("\"%c%c\"",sign,letter);
}
static void fs_json_loop(const PolygonLoop2 *p)
{
    putchar('[');
    for(size_t i=0;i<p->count;++i)printf("%s[%lld,%lld]",i?",":"",(long long)p->v[i].u,(long long)p->v[i].v);
    putchar(']');
}
static void fs_json_layer_pending(void)
{
    fputs("{\"status\":\"pending\",\"clause\":\"I53/R41\",\"reason\":\"two-layer judgement needs the panel thickness t of a D42 panel fill and the h of its derived placement; PF-1 has neither\"}",stdout);
}
static void json_finish_surface(const World *w,const FinishSurface *f)
{
    printf("{\"id\":%u,\"name\":",(unsigned)f->id);js_string(f->name);
    printf(",\"boundaryId\":%u,\"frame\":{\"origin\":[%lld,%lld,%lld],\"U\":",(unsigned)f->boundary_id,
        (long long)f->frame.origin.x,(long long)f->frame.origin.y,(long long)f->frame.origin.z);
    fs_json_axis(f->frame.axis_u);fputs(",\"V\":",stdout);fs_json_axis(f->frame.axis_v);fputs(",\"N\":",stdout);fs_json_axis(f->frame.normal);
    printf("},\"structureSide\":%d,\"obstacles\":[",(int)f->side);
    for(uint32_t i=0;i<f->obstacle_count;++i){char text[16];fs_obstacle_text(&f->obstacles[i],text);if(i)putchar(',');js_string(text);}
    fputs("],\"derived\":",stdout);
    const SpaceBoundarySurface *b=world_find_boundary(w,f->boundary_id);
    if(!b){fputs("null}",stdout);return;}
    Vector3 n={f->frame.normal.x*f->side,f->frame.normal.y*f->side,f->frame.normal.z*f->side};
    fputs("{\"n\":",stdout);fs_json_axis(n);
    fputs(",\"region\":{\"outline\":",stdout);fs_json_loop(&b->outline);fputs(",\"holes\":[",stdout);
    for(size_t h=0;h<b->hole_count;++h){if(h)putchar(',');fs_json_loop(&b->holes[h]);}
    fputs("]},\"obstacles\":[",stdout);
    char saved[sizeof g_engineering_error];snprintf(saved,sizeof saved,"%s",g_engineering_error);
    for(uint32_t i=0;i<f->obstacle_count;++i){char text[16];FsObstacleView v;fs_obstacle_text(&f->obstacles[i],text);
        if(i)putchar(',');fputs("{\"ref\":",stdout);js_string(text);
        if(fs_obstacle_view(w,f,&f->obstacles[i],&v))
            printf(",\"rect\":[%lld,%lld,%lld,%lld],\"q\":[%lld,%lld],\"relation\":\"%s\",\"layers\":null}",
                (long long)v.rect[0],(long long)v.rect[1],(long long)v.rect[2],(long long)v.rect[3],
                (long long)v.q[0],(long long)v.q[1],fs_relation_name(v.relation));
        else {fputs(",\"error\":",stdout);js_string(g_engineering_error);putchar('}');}
    }
    snprintf(g_engineering_error,sizeof g_engineering_error,"%s",saved);
    fputs("]}}",stdout);
}
static void json_panel_fill_state(const World *w)
{
    fputs("{\"finishSurfaces\":[",stdout);
    for(uint64_t i=0;i<w->finish_surfaces.count;++i){if(i)putchar(',');json_finish_surface(w,&w->finish_surfaces.items[i]);}
    fputs("]}",stdout);
}
static void json_panel_fill_changes(const World *before,const World *after)
{
    bool first=true;putchar('[');
    for(uint64_t i=0;i<after->finish_surfaces.count;++i){const FinishSurface *z=&after->finish_surfaces.items[i],*a=fs_find(before,z->id);
        if(a&&!memcmp(a,z,sizeof *a))continue;
        printf("%s{\"id\":%u,\"change\":\"%s\"}",first?"":",",(unsigned)z->id,a?"modified":"created");first=false;}
    for(uint64_t i=0;i<before->finish_surfaces.count;++i){const FinishSurface *a=&before->finish_surfaces.items[i];
        if(fs_find(after,a->id))continue;
        printf("%s{\"id\":%u,\"change\":\"deleted\"}",first?"":",",(unsigned)a->id);first=false;}
    putchar(']');
}
static void json_panel_fill_preview(void)
{
    char error[sizeof g_engineering_error];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:scene_last_error());
    printf("{\"token\":%u,\"valid\":%s,\"revision\":%llu,\"diagnosticsComplete\":true,\"layerJudgement\":",
        g_preview.token,g_preview.valid?"true":"false",(unsigned long long)g_preview.revision);
    fs_json_layer_pending();
    fputs(",\"before\":",stdout);json_panel_fill_state(&g_preview.before);
    fputs(",\"after\":",stdout);json_panel_fill_state(&g_preview.after);
    fputs(",\"changes\":",stdout);json_panel_fill_changes(&g_preview.before,&g_preview.after);
    fputs(",\"violations\":[",stdout);
    if(!g_preview.valid){
        size_t n=strcspn(error,": ");char clause[24];snprintf(clause,sizeof clause,"%.*s",(int)(n<sizeof clause-1?n:sizeof clause-1),error);
        fputs("{\"code\":\"PANEL_FILL_INVALID\",\"clause\":",stdout);js_string(clause);fputs(",\"message\":",stdout);js_string(error);putchar('}');
    }
    fputs("]}",stdout);
}
static void cmd_panel_fill_read(void)
{
    printf("{\"ok\":true,\"schema\":\"%s\",\"capability\":\"%s\",\"complete\":false,\"supportedRecords\":[\"finish-surface\"],"
           "\"revision\":%llu,\"capacity\":{\"finishSurfaces\":%d,\"obstacles\":%d,\"nameBytes\":%d},",
        FS_NATIVE_CAPABILITY,FS_CAPABILITY,(unsigned long long)g_definition_revision,FS_MAX,FS_OBSTACLE_MAX,FS_NAME_MAX);
    json_engineering_capabilities(&g_world);
    fputs(",\"layerJudgement\":",stdout);fs_json_layer_pending();
    fputs(",\"state\":",stdout);json_panel_fill_state(&g_world);fputs("}\n",stdout);
}
static void cmd_panel_fill_preview(const char *path)
{
    batch_preview(path,"panel-fill-transaction/1","Expected panel-fill-transaction/1, expectedRevision and operations",
        "Panel-fill definitions changed; read and preview again","Cannot allocate panel-fill candidate","panel-fill-transaction",3,
        fs_operation,json_panel_fill_preview);
}
static void cmd_panel_fill_confirm(const char *arg)
{ batch_confirm(arg,3,"Missing, invalid or unrelated panel-fill token","Panel-fill preview expired; preview again"); }
static void cmd_panel_fill_cancel(const char *arg)
{ batch_cancel(arg,3,"Cancel requires a panel-fill token"); }
