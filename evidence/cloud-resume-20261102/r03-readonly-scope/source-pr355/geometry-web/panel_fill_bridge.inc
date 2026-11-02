/* PF-1 native transport for D41 finish surfaces (panel-fill-native/1).
 * Every derived value below (F, R_k, q, relation) is recomputed per response and never stored (I56, R4).
 * Layers (I53) need a panel fill's thickness t and a derived placement's h; PF-1 reports them as pending. */
/* The legacy transport remains numeric. Only panel-fill-workspace/1 uses the
 * exact writer: every int64 quantity is a decimal string, while bounded IDs,
 * counts and source definitions retain their existing JSON types. */
typedef struct {
    const char *record_type, *stage, *code;
    uint32_t id;
    char message[512];
} PfUiError;
static bool g_pf_ui_exact;
static const char *g_pf_ui_stage;
/* At most one incomplete-view diagnostic per record and stage, plus the
 * transaction diagnostic. Each World has at most FS_MAX records of each kind. */
static PfUiError g_pf_ui_errors[6 * FS_MAX + 1];
static size_t g_pf_ui_error_count;
static void pf_json_i64(int64_t value)
{
    printf(g_pf_ui_exact?"\"%lld\"":"%lld",(long long)value);
}
static void pf_json_pair(int64_t a,int64_t b)
{
    putchar('[');pf_json_i64(a);putchar(',');pf_json_i64(b);putchar(']');
}
static void pf_json_point(Point3 v)
{
    putchar('[');pf_json_i64(v.x);putchar(',');pf_json_i64(v.y);putchar(',');pf_json_i64(v.z);putchar(']');
}
static void pf_ui_error(const char *record,uint32_t id,const char *code,const char *message)
{
    if(!g_pf_ui_exact)return;
    for(size_t i=0;i<g_pf_ui_error_count;++i)
        if(g_pf_ui_errors[i].id==id&&!strcmp(g_pf_ui_errors[i].record_type,record)&&!strcmp(g_pf_ui_errors[i].stage,g_pf_ui_stage))return;
    if(g_pf_ui_error_count>=sizeof g_pf_ui_errors/sizeof *g_pf_ui_errors)return;
    PfUiError *e=&g_pf_ui_errors[g_pf_ui_error_count++];
    e->record_type=record;e->id=id;e->stage=g_pf_ui_stage;e->code=code;
    snprintf(e->message,sizeof e->message,"%s",message);
}
static void fs_json_axis(Vector3 a)
{
    char sign=(a.x+a.y+a.z)>0?'+':'-',letter=a.x?'X':a.y?'Y':'Z';
    printf("\"%c%c\"",sign,letter);
}
static void fs_json_loop(const PolygonLoop2 *p)
{
    putchar('[');
    for(size_t i=0;i<p->count;++i){if(i)putchar(',');pf_json_pair(p->v[i].u,p->v[i].v);}
    putchar(']');
}
static void fs_json_layer_pending(void)
{
    fputs("{\"status\":\"pending\",\"clause\":\"I53/R41\",\"reason\":\"full two-layer judgement needs a derived placement h; PF-2 reports the panel layer per fill, while the timber layer remains pending\"}",stdout);
}
static void json_finish_surface(const World *w,const FinishSurface *f)
{
    printf("{\"id\":%u,\"name\":",(unsigned)f->id);js_string(f->name);
    printf(",\"boundaryId\":%u,\"frame\":{\"origin\":",(unsigned)f->boundary_id);
    pf_json_point(f->frame.origin);fputs(",\"U\":",stdout);
    fs_json_axis(f->frame.axis_u);fputs(",\"V\":",stdout);fs_json_axis(f->frame.axis_v);fputs(",\"N\":",stdout);fs_json_axis(f->frame.normal);
    printf("},\"structureSide\":%d,\"obstacles\":[",(int)f->side);
    for(uint32_t i=0;i<f->obstacle_count;++i){char text[16];fs_obstacle_text(&f->obstacles[i],text);if(i)putchar(',');js_string(text);}
    fputs("],\"derived\":",stdout);
    const SpaceBoundarySurface *b=world_find_boundary(w,f->boundary_id);
    if(!b){pf_ui_error("finish-surface",f->id,"BOUNDARY_MISSING","D41: finish surface boundary is missing");fputs("null}",stdout);return;}
    Vector3 n={f->frame.normal.x*f->side,f->frame.normal.y*f->side,f->frame.normal.z*f->side};
    fputs("{\"n\":",stdout);fs_json_axis(n);
    fputs(",\"region\":{\"outline\":",stdout);fs_json_loop(&b->outline);fputs(",\"holes\":[",stdout);
    for(size_t h=0;h<b->hole_count;++h){if(h)putchar(',');fs_json_loop(&b->holes[h]);}
    fputs("]},\"obstacles\":[",stdout);
    FsDiagnosticKind saved_kind=g_fs_diagnostic;
    char saved[sizeof g_engineering_error];snprintf(saved,sizeof saved,"%s",g_engineering_error);
    for(uint32_t i=0;i<f->obstacle_count;++i){char text[16];FsObstacleView v;fs_obstacle_text(&f->obstacles[i],text);
        if(i)putchar(',');fputs("{\"ref\":",stdout);js_string(text);
        if(fs_obstacle_view(w,f,&f->obstacles[i],&v)){
            fputs(",\"rect\":[",stdout);for(size_t k=0;k<4;++k){if(k)putchar(',');pf_json_i64(v.rect[k]);}
            fputs("],\"q\":",stdout);pf_json_pair(v.q[0],v.q[1]);
            printf(",\"relation\":\"%s\",\"layers\":null}",fs_relation_name(v.relation));
        }else {pf_ui_error("finish-surface",f->id,"OBSTACLE_VIEW_UNAVAILABLE",g_engineering_error);fputs(",\"error\":",stdout);js_string(g_engineering_error);putchar('}');}
    }
    snprintf(g_engineering_error,sizeof g_engineering_error,"%s",saved);g_fs_diagnostic=saved_kind;
    fputs("]}}",stdout);
}
#include "panel_layout_bridge.inc"
static void dp_json_host(const World *w,const DerivedPlacement *d)
{
    const PlacementSurface *p=world_find_placement(w,d->id);
    printf("{\"id\":%u,\"definition\":%s,\"derived\":",d->id,d->definition);
    if(!p){pf_ui_error("derived-placement",d->id,"HOST_MISSING","D4: derived placement is missing");fputs("null}",stdout);return;}
    fputs("{\"h\":",stdout);pf_json_i64(p->derived_h);fputs(",\"frame\":{\"origin\":",stdout);
    pf_json_point(p->frame.origin);fputs(",\"U\":",stdout);
    fs_json_axis(p->frame.axis_u);fputs(",\"V\":",stdout);fs_json_axis(p->frame.axis_v);fputs(",\"N\":",stdout);fs_json_axis(p->frame.normal);fputs("},\"components\":[",stdout);
    for(size_t c=0;c<p->component_count;++c){const SpaceBoundarySurface *b=&p->components[c];if(c)putchar(',');fputs("{\"outline\":",stdout);fs_json_loop(&b->outline);fputs(",\"holes\":[",stdout);
        for(size_t h=0;h<b->hole_count;++h){if(h)putchar(',');fs_json_loop(&b->holes[h]);}fputs("],\"edges\":[",stdout);bool first=true;
        for(size_t h=0;h<=b->hole_count;++h){const PolygonLoop2 *l=h?&b->holes[h-1]:&b->outline;for(size_t e=0;e<l->count;++e){char key[512];if(!first)putchar(',');first=false;
            fputs("{\"key\":",stdout);if(dp_edge_key(w,p,c,h?(int)h-1:-1,e,key,sizeof key))fputs(key,stdout);else {pf_ui_error("derived-placement",d->id,"EDGE_KEY_UNAVAILABLE","R41: derived edge identity is unavailable");fputs("null",stdout);}
            fputs(",\"start\":",stdout);pf_json_pair(l->v[e].u,l->v[e].v);fputs(",\"end\":",stdout);pf_json_pair(l->v[(e+1)%l->count].u,l->v[(e+1)%l->count].v);
            printf(",\"fixity\":\"%s\"}",l->fixity[e]==EDGE_FREE?"FREE":"FIXED");}}
        fputs("]}",stdout);}
    fputs("]}}",stdout);
}
static void json_panel_fill_state(const World *w)
{
    fputs("{\"finishSurfaces\":[",stdout);
    for(uint64_t i=0;i<w->wood.finish_surfaces.count;++i){if(i)putchar(',');json_finish_surface(w,&w->wood.finish_surfaces.items[i]);}
    putchar(']');pf_json_state(w);fputs(",\"derivedPlacements\":[",stdout);
    for(uint64_t i=0;i<w->wood.finish_surfaces.host_count;++i){if(i)putchar(',');dp_json_host(w,&w->wood.finish_surfaces.hosts[i]);}fputs("]}",stdout);
}
static void pf_ui_scope(const World *before,const World *after)
{
    fputs("{\"finishSurfaceIds\":[",stdout);bool first=true;
    for(uint64_t i=0;i<before->wood.finish_surfaces.count;++i){printf("%s%u",first?"":",",before->wood.finish_surfaces.items[i].id);first=false;}
    if(after)for(uint64_t i=0;i<after->wood.finish_surfaces.count;++i){uint32_t id=after->wood.finish_surfaces.items[i].id;if(fs_find(before,id))continue;printf("%s%u",first?"":",",id);first=false;}
    fputs("],\"fillIds\":[",stdout);first=true;
    for(uint64_t i=0;i<before->wood.finish_surfaces.fill_count;++i){printf("%s%u",first?"":",",before->wood.finish_surfaces.fills[i].id);first=false;}
    if(after)for(uint64_t i=0;i<after->wood.finish_surfaces.fill_count;++i){uint32_t id=after->wood.finish_surfaces.fills[i].id;if(pf_find(before,id))continue;printf("%s%u",first?"":",",id);first=false;}
    fputs("]}",stdout);
}
static void json_panel_fill_ui_contract(const World *before,const World *after,uint64_t revision,bool valid,FsDiagnosticKind failure_kind,const char *error)
{
    FsDiagnosticKind saved_kind=g_fs_diagnostic;
    char saved[sizeof g_engineering_error];snprintf(saved,sizeof saved,"%s",g_engineering_error);
    g_pf_ui_exact=true;g_pf_ui_error_count=0;
    fputs(",\"uiContract\":{\"schema\":\"panel-fill-workspace/1\",\"supportedActions\":[\"read\",\"edit-definitions\",\"read-layout\",\"read-support\"],\"scope\":",stdout);
    pf_ui_scope(before,after);printf(",\"revision\":\"%llu\"",(unsigned long long)revision);
    g_pf_ui_stage=after?"before":"state";
    fputs(after?",\"before\":":",\"state\":",stdout);json_panel_fill_state(before);
    if(after){g_pf_ui_stage="after";fputs(",\"after\":",stdout);json_panel_fill_state(after);}
    if(!valid)pf_ui_error("transaction",0,failure_kind==FS_DIAGNOSTIC_CAPACITY?"CAPACITY":"PANEL_FILL_INVALID",error);
    printf(",\"completeForScope\":%s,\"errors\":[",valid&&!g_pf_ui_error_count?"true":"false");
    for(size_t i=0;i<g_pf_ui_error_count;++i){const PfUiError *e=&g_pf_ui_errors[i];
        size_t n=strcspn(e->message,": ");char clause[24];snprintf(clause,sizeof clause,"%.*s",(int)(n<sizeof clause-1?n:sizeof clause-1),e->message);
        if(i)putchar(',');fputs("{\"recordType\":",stdout);js_string(e->record_type);fputs(",\"id\":",stdout);
        if(!strcmp(e->record_type,"transaction"))fputs("null",stdout);else printf("%u",e->id);
        fputs(",\"stage\":",stdout);js_string(e->stage);fputs(",\"code\":",stdout);js_string(e->code);
        fputs(",\"clause\":",stdout);js_string(clause);fputs(",\"expected\":\"complete native record view\",\"actual\":",stdout);js_string(e->message);
        fputs(",\"missing\":[",stdout);js_string(e->code);fputs("],\"message\":",stdout);js_string(e->message);putchar('}');
    }
    fputs("]}",stdout);g_pf_ui_exact=false;g_pf_ui_stage=NULL;g_pf_ui_error_count=0;
    snprintf(g_engineering_error,sizeof g_engineering_error,"%s",saved);g_fs_diagnostic=saved_kind;
}
static void json_panel_fill_changes(const World *before,const World *after)
{
    bool first=true;putchar('[');
    for(uint64_t i=0;i<after->wood.finish_surfaces.count;++i){const FinishSurface *z=&after->wood.finish_surfaces.items[i],*a=fs_find(before,z->id);
        if(a&&!memcmp(a,z,sizeof *a))continue;
        printf("%s{\"id\":%u,\"change\":\"%s\"}",first?"":",",(unsigned)z->id,a?"modified":"created");first=false;}
    for(uint64_t i=0;i<before->wood.finish_surfaces.count;++i){const FinishSurface *a=&before->wood.finish_surfaces.items[i];
        if(fs_find(after,a->id))continue;
        printf("%s{\"id\":%u,\"change\":\"deleted\"}",first?"":",",(unsigned)a->id);first=false;}
    for(uint64_t i=0;i<after->wood.finish_surfaces.fill_count;++i){const PanelFill *z=&after->wood.finish_surfaces.fills[i],*a=pf_find(before,z->id);
        if(a&&!memcmp(a,z,sizeof *a)&&world_definitions_equal(before,after))continue;
        printf("%s{\"record\":\"panel-fill\",\"id\":%u,\"change\":\"%s\"}",first?"":",",z->id,!a?"created":memcmp(a,z,sizeof *a)?"modified":"derived");first=false;}
    for(uint64_t i=0;i<before->wood.finish_surfaces.fill_count;++i){const PanelFill *a=&before->wood.finish_surfaces.fills[i];if(pf_find(after,a->id))continue;
        printf("%s{\"record\":\"panel-fill\",\"id\":%u,\"change\":\"deleted\"}",first?"":",",a->id);first=false;}
    for(uint64_t i=0;i<after->wood.finish_surfaces.host_count;++i){const DerivedPlacement *z=&after->wood.finish_surfaces.hosts[i],*a=dp_find(before,z->id);
        if(a&&!memcmp(a,z,sizeof *a)&&world_definitions_equal(before,after))continue;
        printf("%s{\"record\":\"derived-placement\",\"id\":%u,\"change\":\"%s\"}",first?"":",",z->id,!a?"created":memcmp(a,z,sizeof *a)?"modified":"derived");first=false;}
    for(uint64_t i=0;i<before->wood.finish_surfaces.host_count;++i){const DerivedPlacement *a=&before->wood.finish_surfaces.hosts[i];if(dp_find(after,a->id))continue;
        printf("%s{\"record\":\"derived-placement\",\"id\":%u,\"change\":\"deleted\"}",first?"":",",a->id);first=false;}
    putchar(']');
}
static void json_panel_fill_preview(void)
{
    /* Derived-state serialization must not replace the failed operation's classification. */
    FsDiagnosticKind failure_kind=g_fs_diagnostic;
    char error[sizeof g_engineering_error];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:scene_last_error());
    printf("{\"token\":%u,\"valid\":%s,\"revision\":%llu,\"diagnosticsComplete\":true,\"layerJudgement\":",
        g_preview.token,g_preview.valid?"true":"false",(unsigned long long)g_preview.revision);
    fs_json_layer_pending();
    fputs(",\"before\":",stdout);json_panel_fill_state(&g_preview.transaction->before);
    fputs(",\"after\":",stdout);json_panel_fill_state(&g_preview.transaction->after);
    json_parameter_rebindings();
    fputs(",\"changes\":",stdout);json_panel_fill_changes(&g_preview.transaction->before,&g_preview.transaction->after);
    if(g_preview.transaction->before.wood.finish_surfaces.host_count||g_preview.transaction->after.wood.finish_surfaces.host_count){
        fputs(",\"dependencies\":{\"before\":",stdout);json_engineering_state(&g_preview.transaction->before,true);
        fputs(",\"after\":",stdout);json_engineering_state(&g_preview.transaction->after,true);putchar('}');
    }
    fputs(",\"violations\":[",stdout);
    if(!g_preview.valid){
        size_t n=strcspn(error,": ");char clause[24];snprintf(clause,sizeof clause,"%.*s",(int)(n<sizeof clause-1?n:sizeof clause-1),error);
        fputs("{\"status\":",stdout);js_string(failure_kind==FS_DIAGNOSTIC_CAPACITY?"UNSUPPORTED":"INVALID");
        fputs(",\"code\":",stdout);js_string(failure_kind==FS_DIAGNOSTIC_CAPACITY?"CAPACITY":"PANEL_FILL_INVALID");
        fputs(",\"clause\":",stdout);js_string(clause);fputs(",\"message\":",stdout);js_string(error);putchar('}');
        for(size_t i=0;i<g_preview.issue_count;++i){const ReferenceIssue *issue=&g_preview.issues[i];
            printf(",{\"status\":\"INVALID\",\"code\":\"PANEL_FILL_DEPENDENCY\",\"timber\":%u,\"clause\":",issue->timber);js_string(issue->clause);
            fputs(",\"message\":",stdout);js_string(issue->actual);putchar('}');}
    }
    putchar(']');json_panel_fill_ui_contract(&g_preview.transaction->before,&g_preview.transaction->after,g_preview.revision,g_preview.valid,failure_kind,error);putchar('}');
}
static void cmd_panel_fill_read(void)
{
    printf("{\"ok\":true,\"schema\":\"%s\",\"capability\":\"%s\",\"complete\":false,\"supportedRecords\":[\"finish-surface\",\"panel-fill\",\"derived-placement\"],"
           "\"revision\":%llu,\"capacity\":{\"finishSurfaces\":%d,\"obstacles\":%d,\"nameBytes\":%d},",
        FS_NATIVE_CAPABILITY,FS_CAPABILITY,(unsigned long long)g_definition_revision,FS_MAX,FS_OBSTACLE_MAX,FS_NAME_MAX);
    json_engineering_capabilities(&g_world);
    fputs(",\"layerJudgement\":",stdout);fs_json_layer_pending();
    fputs(",\"state\":",stdout);json_panel_fill_state(&g_world);
    json_panel_fill_ui_contract(&g_world,NULL,g_definition_revision,true,FS_DIAGNOSTIC_INVALID,"");fputs("}\n",stdout);
}
static void cmd_panel_fill_preview(const char *path)
{
    g_fs_diagnostic=FS_DIAGNOSTIC_INVALID;
    batch_preview(path,"panel-fill-transaction/1","Expected panel-fill-transaction/1, expectedRevision and operations",
        "Panel-fill definitions changed; read and preview again","Cannot allocate panel-fill candidate","panel-fill-transaction",3,
        fs_operation,json_panel_fill_preview);
}
static void cmd_panel_fill_confirm(const char *arg)
{ batch_confirm(arg,3,"Missing, invalid or unrelated panel-fill token","Panel-fill preview expired; preview again"); }
static void cmd_panel_fill_cancel(const char *arg)
{ batch_cancel(arg,3,"Cancel requires a panel-fill token"); }
