/* I8/I8a: one atomic entry point shared by file parser, CLI, GDI and bridge. */
typedef struct {
    bool ready, valid;
    uint32_t token;
    World before, after;
    char command[SCENE_MAX_LINE];
    ReferenceIssue issues[REFERENCE_MAX_ISSUES];
    size_t issue_count;
} ReferencePreview;
static ReferencePreview g_preview;
static uint32_t g_preview_serial;
static bool g_preview_confirming;
static bool reference_preview_pending(void) { return g_preview.ready; }
static bool reference_preview_valid(void) { return g_preview.ready && g_preview.valid; }
static uint32_t reference_preview_token(void) { return g_preview.token; }

static void reference_pose_text(const World *w,int index,char *out,size_t cap)
{
    if (index<0 || !w->timbers[index].placed) { snprintf(out,cap,"unavailable"); return; }
    const Timber *t=&w->timbers[index];
    snprintf(out,cap,"surface %u origin [%lld,%lld,%lld] axes [%lld,%lld,%lld]/[%lld,%lld,%lld]/[%lld,%lld,%lld]",
        w->anchors[index].placement_id,(long long)t->origin.x,(long long)t->origin.y,(long long)t->origin.z,
        (long long)t->axis_length.x,(long long)t->axis_length.y,(long long)t->axis_length.z,
        (long long)t->axis_a.x,(long long)t->axis_a.y,(long long)t->axis_a.z,
        (long long)t->axis_b.x,(long long)t->axis_b.y,(long long)t->axis_b.z);
}

static void reference_guide_text(const World *w,uint32_t id,char *out,size_t cap)
{
    const GuideLine *g=world_find_guide(w,id);
    const PlacementSurface *p=g?world_find_placement(w,g->placement_id):NULL;
    if (!g || !g->resolved || !p) { snprintf(out,cap,"unavailable"); return; }
    Vector3 along=g->direction==GUIDE_ALONG_U?p->frame.axis_u:p->frame.axis_v;
    Vector3 cross=g->direction==GUIDE_ALONG_U?p->frame.axis_v:p->frame.axis_u;
    snprintf(out,cap,"surface %u %c=%lld world [%lld,%lld,%lld] direction [%lld,%lld,%lld]",
        g->placement_id,g->direction==GUIDE_ALONG_U?'v':'u',(long long)g->offset,
        (long long)(p->frame.origin.x+cross.x*g->offset),(long long)(p->frame.origin.y+cross.y*g->offset),(long long)(p->frame.origin.z+cross.z*g->offset),
        (long long)along.x,(long long)along.y,(long long)along.z);
}

#ifdef _WIN32
static bool reference_gdi_confirm(HWND window, World *world)
{
    if (!g_preview.ready) return false;
    char text[32768]; size_t used=0; bool truncated=false;
    int n=snprintf(text,sizeof text,"I8a 影響預覽：場景尚未改動。\n%s\n\n",g_preview.command);
    used=(size_t)n;
    for (size_t i=0;i<g_preview.before.timber_count;++i) {
        const Timber *t=&g_preview.before.timbers[i]; if (!t->placed) continue;
        if (used+900>=sizeof text) { truncated=true; break; }
        int j=reference_timber_index(&g_preview.after,t->id); bool valid=j>=0 && g_preview.after.timbers[j].placed;
        const TimberAnchor *a=&g_preview.before.anchors[i];
        const PlacementSurface *p=world_find_placement(&g_preview.before,a->placement_id); SurfaceRegion2 f;
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        Coord old=0,newc=0;
        if (p && timber_a0_footprint_uv(p,t,a,&f)) old=(along?f.min_u:f.min_v)+t->size_a/2;
        if (valid) {
            const Timber *nt=&g_preview.after.timbers[j]; const TimberAnchor *na=&g_preview.after.anchors[j];
            p=world_find_placement(&g_preview.after,na->placement_id);
            if (p && timber_a0_footprint_uv(p,nt,na,&f)) newc=(along?f.min_u:f.min_v)+nt->size_a/2;
        }
        n=snprintf(text+used,sizeof text-used,"角材 %u：中線 %lld → %lld；長度 %lld → %lld mm%s\n",t->id,(long long)old,(long long)newc,(long long)t->length,
            valid?(long long)g_preview.after.timbers[j].length:0,valid?"":"（已刪除或無法推導）"); used+=(size_t)n;
        char before[240],after[240];
        reference_pose_text(&g_preview.before,(int)i,before,sizeof before);
        reference_pose_text(&g_preview.after,j,after,sizeof after);
        n=snprintf(text+used,sizeof text-used,"  %s → %s\n",before,after); used+=(size_t)n;
    }
    for (size_t i=0;i<g_preview.before.guide_count;++i) {
        uint32_t id=g_preview.before.guides[i].id; char before[240],after[240];
        reference_guide_text(&g_preview.before,id,before,sizeof before);
        reference_guide_text(&g_preview.after,id,after,sizeof after);
        if (!strcmp(before,after)) continue;
        if (used+600>=sizeof text) { truncated=true; break; }
        n=snprintf(text+used,sizeof text-used,"參考線 %u: %s → %s\n",id,before,after); used+=(size_t)n;
    }
    for (size_t i=0;i<g_preview.issue_count;++i) {
        if (used+600>=sizeof text) { truncated=true; break; }
        const ReferenceIssue *e=&g_preview.issues[i];
        n=snprintf(text+used,sizeof text-used,"\n角材 %u · %s\n預期：%s\n實際：%s\n",e->timber,e->clause,e->expected,e->actual); used+=(size_t)n;
    }
    if (truncated) {
        MessageBoxW(window,L"影響明細超過此視窗容量，未提交。請使用網頁或 CLI 檢視完整預覽後確認。",L"需要完整預覽",MB_OK|MB_ICONWARNING);
        g_preview.ready=false; return false;
    }
    WCHAR wide[32768]; utf8_to_wide(text,wide,32768);
    if (!g_preview.valid) { MessageBoxW(window,wide,L"變更無法套用",MB_OK|MB_ICONWARNING); g_preview.ready=false; return false; }
    if (MessageBoxW(window,wide,L"確認連動變更",MB_OKCANCEL|MB_ICONQUESTION)!=IDOK) { g_preview.ready=false; return false; }
    char command[64],*tokens[2]; snprintf(command,sizeof command,"confirm %u",g_preview.token);
    int count=split_tokens(command,tokens,2);
    return apply_interactive_tokens("confirm",1,tokens,count,world);
}
#endif

static bool reference_geometry_changed(const World *before,const World *after)
{
    for (size_t i=0;i<before->timber_count;++i) {
        const Timber *t=&before->timbers[i]; if (!t->placed) continue;
        int j=reference_timber_index(after,t->id);
        if (j<0 || !after->timbers[j].placed ||
            memcmp(t,&after->timbers[j],sizeof *t) ||
            memcmp(&before->anchors[i],&after->anchors[j],sizeof(TimberAnchor))) return true;
    }
    return false;
}
static bool reference_may_affect(const World *w,char **tokens,int count)
{
    bool placed=false;
    for (size_t i=0;i<w->timber_count;++i) if (w->timbers[i].placed) placed=true;
    if (!placed || !count) return false;
    const char *c=tokens[0];
    if (!strcmp(c,"move") || !strcmp(c,"spec") || !strcmp(c,"datum") || !strcmp(c,"boundary") || !strcmp(c,"surface") ||
        !strcmp(c,"placement") || !strcmp(c,"grid") || !strcmp(c,"guide") || !strcmp(c,"apply-proj") || !strcmp(c,"delete")) return true;
    if ((!strcmp(c,"place") || !strcmp(c,"timber")) && count>1) {
        uint32_t id;
        if (parse_u32(tokens[1],&id)) { int i=reference_timber_index(w,id); return i>=0 && w->timbers[i].placed; }
    }
    return false;
}
static void reference_stage(const World *before,const World *after,char **tokens,int count,bool valid)
{
    g_preview.ready=true; g_preview.valid=valid; g_preview.token=++g_preview_serial;
    g_preview.before=*before; g_preview.after=*after; g_preview.issue_count=g_reference_issue_count;
    memcpy(g_preview.issues,g_reference_issues,g_preview.issue_count*sizeof(ReferenceIssue));
    if (!valid && !g_preview.issue_count) {
        ReferenceIssue *e=&g_preview.issues[g_preview.issue_count++]; e->timber=0;
        snprintf(e->clause,sizeof e->clause,"I8");
        snprintf(e->expected,sizeof e->expected,"all world invariants pass");
        snprintf(e->actual,sizeof e->actual,"%s",scene_last_error()[0]?scene_last_error():"candidate rejected");
    }
    g_preview.command[0]='\0'; size_t used=0;
    for (int i=0;i<count;++i) {
        int n=snprintf(g_preview.command+used,sizeof g_preview.command-used,"%s%s",i?" ":"",tokens[i]);
        if (n<0 || (size_t)n>=sizeof g_preview.command-used) { g_preview.valid=false; break; }
        used+=(size_t)n;
    }
}
static void reference_preview_text(void)
{
    fprintf(stderr,"I8a preview %u: %s\n",g_preview.token,g_preview.valid?"valid; confirm token to apply":"invalid; cannot apply");
    for (size_t i=0;i<g_preview.before.timber_count;++i) {
        const Timber *t=&g_preview.before.timbers[i]; if (!t->placed) continue;
        int j=reference_timber_index(&g_preview.after,t->id);
        const TimberAnchor *a=&g_preview.before.anchors[i];
        const PlacementSurface *p=world_find_placement(&g_preview.before,a->placement_id);
        SurfaceRegion2 f; Coord old=0,newc=0;
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        if (p && timber_a0_footprint_uv(p,t,a,&f)) old=(along?f.min_u:f.min_v)+t->size_a/2;
        bool valid=j>=0 && g_preview.after.timbers[j].placed;
        if (valid) {
            const TimberAnchor *na=&g_preview.after.anchors[j]; const Timber *nt=&g_preview.after.timbers[j];
            p=world_find_placement(&g_preview.after,na->placement_id);
            if (p && timber_a0_footprint_uv(p,nt,na,&f)) newc=(along?f.min_u:f.min_v)+nt->size_a/2;
        }
        fprintf(stderr," timber %u center %lld -> %lld length %lld -> %lld%s\n",t->id,(long long)old,(long long)newc,(long long)t->length,
            valid?(long long)g_preview.after.timbers[j].length:0,valid?"":" (unavailable/deleted)");
        char before[240],after[240];
        reference_pose_text(&g_preview.before,(int)i,before,sizeof before);
        reference_pose_text(&g_preview.after,j,after,sizeof after);
        fprintf(stderr,"  %s -> %s\n",before,after);
    }
    for (size_t i=0;i<g_preview.before.guide_count;++i) {
        uint32_t id=g_preview.before.guides[i].id; char before[240],after[240];
        reference_guide_text(&g_preview.before,id,before,sizeof before);
        reference_guide_text(&g_preview.after,id,after,sizeof after);
        if (strcmp(before,after)) fprintf(stderr," guide %u: %s -> %s\n",id,before,after);
    }
    for (size_t i=0;i<g_preview.issue_count;++i) {
        const ReferenceIssue *e=&g_preview.issues[i];
        fprintf(stderr," timber %u %s expected: %s; actual: %s\n",e->timber,e->clause,e->expected,e->actual);
    }
}

static bool apply_scene_line(const char *path,int line_no,char *tokens[],int count,World *world)
{
    if (!count) return true;
    if (!strcmp(tokens[0],"cancel-preview")) {
        if (count!=1) return false;
        g_preview.ready=false; return true;
    }
    if (!strcmp(tokens[0],"confirm")) {
        uint32_t token;
        if (count!=2 || !parse_u32(tokens[1],&token) || !g_preview.ready || token!=g_preview.token || !g_preview.valid) {
            scene_error(path,line_no,"I8a: missing/invalid preview token; cannot apply"); return false;
        }
        /* Canvas layout does not invalidate geometry approval (D12/I14). */
        World current=*world,expected=g_preview.before;
        current.canvas_pos_count=expected.canvas_pos_count=0;
        memset(current.canvas_pos,0,sizeof current.canvas_pos); memset(expected.canvas_pos,0,sizeof expected.canvas_pos);
        if (memcmp(&current,&expected,sizeof current)) {
            g_preview.ready=false;
            scene_error(path,line_no,"I8a: preview is stale; preview again against the current world"); return false;
        }
        char command[SCENE_MAX_LINE],*parts[SCENE_MAX_TOKENS];
        snprintf(command,sizeof command,"%s",g_preview.command);
        int n=split_tokens(command,parts,SCENE_MAX_TOKENS);
        g_preview.ready=false; g_preview_confirming=true;
        bool ok=apply_scene_line(path,line_no,parts,n,world);
        g_preview_confirming=false; return ok;
    }
    bool explicit_preview=!strcmp(tokens[0],"preview");
    if (explicit_preview) {
        if (count<2 || !strcmp(tokens[1],"preview") || !strcmp(tokens[1],"confirm")) return false;
        ++tokens; --count;
    }
    World candidate=*world;
    g_scene_last_error[0]='\0'; g_reference_issue_count=0;
    g_reference_trial=candidate; g_reference_capturing=true;
    bool ok=apply_scene_line_unchecked(path,line_no,tokens,count,&candidate);
    g_reference_capturing=false;
    bool affects=reference_may_affect(world,tokens,count);
    if (explicit_preview || (!g_preview_confirming && affects && (!ok || reference_geometry_changed(world,&candidate)))) {
        reference_stage(world,ok?&candidate:&g_reference_trial,tokens,count,ok);
        reference_preview_text();
        if (explicit_preview) return true;
        scene_error(path,line_no,"I8a: impact preview required; inspect preview, then confirm token (World unchanged)");
        return false;
    }
    if (!ok) {
        if (!g_scene_last_error[0]) scene_error(path,line_no,"I8: invalid definition/reference; World unchanged");
        return false;
    }
    *world=candidate;
    return true;
}

static bool reference_default_world(World *world)
{
    const char *lines[]={
        "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
        "timber 1 27 33 role boundary", "place 1 on 1 at-face e0 +u +n",
        "timber 2 27 33 role boundary", "place 2 on 1 at-face e2 +u +n",
        "spec 主支中線 500", "guide 1 1 v spec:主支中線",
        "timber 3 27 33 role primary", "place 3 on 1 at-line guide 1 +v +n"
    };
    memset(world,0,sizeof *world);
    for (size_t i=0;i<sizeof lines/sizeof lines[0];++i) {
        char buf[SCENE_MAX_LINE],*tokens[SCENE_MAX_TOKENS];
        snprintf(buf,sizeof buf,"%s",lines[i]); int n=split_tokens(buf,tokens,SCENE_MAX_TOKENS);
        if (!apply_scene_line("default",(int)i+1,tokens,n,world)) return false;
    }
    return true;
}
