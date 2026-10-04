/* Structured I8a report, derived geometry for UI, and reference snapping. */
static void json_reference_grid(const World *w,const ReferenceGrid *g);
static void json_assembly_state(const World *w,bool geometry);
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
    SurfaceSegment2 segments[GUIDE_MAX_SEGMENTS];
    size_t count=guide_line_get_local_segments(p,world_placement_boundary(w,p),g,segments,GUIDE_MAX_SEGMENTS);
    for (size_t j=0;j<count;++j) printf("%s[[%lld,%lld],[%lld,%lld]]",j?",":"",
        (long long)segments[j].start.u,(long long)segments[j].start.v,
        (long long)segments[j].end.u,(long long)segments[j].end.v);
    fputs("]}",stdout);
}
static void json_reference_datum(const DatumPlane *d)
{
    if(!d){fputs("null",stdout);return;}
    printf("{\"id\":%u,\"axis\":\"%c\",\"position\":%lld,\"expression\":",d->id,'X'+d->axis,(long long)d->position);js_string(d->expression);putchar('}');
}
/* Serialize the rebuilt candidate, never an ownership-selected dependency set.
 * Reference previews retain their existing before-only timber list; assembly
 * also needs newly generated timbers. Both use the same native geometry. */
static void json_candidate_timbers(const World *before,const World *after,bool include_new)
{
    putchar('[');bool first=true;
    for (int pass=0;pass<(include_new?2:1);++pass) {
        const World *w=pass?after:before;
        for (size_t i=0;i<w->timber_count;++i) {
            const Timber *t=&w->timbers[i];if (!t->placed) continue;
            int old=reference_timber_index(before,t->id),now=reference_timber_index(after,t->id);
            if (pass && old>=0 && before->timbers[old].placed) continue;
            if (!first) putchar(',');first=false;
            printf("{\"id\":%u,\"before\":",t->id);json_reference_geometry(before,old);
            fputs(",\"after\":",stdout);json_reference_geometry(after,now);putchar('}');
        }
    }
    putchar(']');
}
static void json_candidate_guides(const World *before,const World *after)
{
    putchar('[');
    for (size_t i=0;i<before->guide_count;++i) {
        const GuideLine *g=&before->guides[i];
        printf("%s{\"id\":%u,\"before\":",i?",":"",g->id); json_reference_guide(before,i);
        fputs(",\"after\":",stdout); size_t j=0;
        while (j<after->guide_count && after->guides[j].id!=g->id) ++j;
        if (j==after->guide_count) fputs("null",stdout); else json_reference_guide(after,j);
        putchar('}');
    }
    bool first=before->guide_count==0;
    for (size_t i=0;i<after->guide_count;++i) {
        const GuideLine *g=&after->guides[i];
        if (world_find_guide(before,g->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",g->id); first=false;
        json_reference_guide(after,i); putchar('}');
    }
    putchar(']');
}
static void json_candidate_geometry(const World *before,const World *after)
{
    fputs("{\"schema\":\"candidate-geometry/1\",\"timbers\":",stdout);
    json_candidate_timbers(before,after,true);
    fputs(",\"guides\":",stdout);json_candidate_guides(before,after);putchar('}');
}
static void json_reference_preview(void)
{
    printf("{\"token\":%u,\"valid\":%s,\"command\":",g_preview.token,g_preview.valid?"true":"false");
    js_string(g_preview.command);fputs(",\"timbers\":",stdout);
    json_candidate_timbers(&g_preview.before,&g_preview.after,false);
    fputs(",\"guides\":",stdout);json_candidate_guides(&g_preview.before,&g_preview.after);
    fputs(",\"grids\":[",stdout); bool first=true;
    for (size_t i=0;i<g_preview.before.grid_count;++i) {
        const ReferenceGrid *g=&g_preview.before.grids[i];
        const ReferenceGrid *after=world_find_grid(&g_preview.after,g->id);
        printf("%s{\"id\":%u,\"before\":",first?"":",",g->id); first=false;
        json_reference_grid(&g_preview.before,g);
        fputs(",\"after\":",stdout);
        if (after) json_reference_grid(&g_preview.after,after); else fputs("null",stdout);
        putchar('}');
    }
    for (size_t i=0;i<g_preview.after.grid_count;++i) {
        const ReferenceGrid *g=&g_preview.after.grids[i];
        if (world_find_grid(&g_preview.before,g->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",g->id); first=false;
        json_reference_grid(&g_preview.after,g); putchar('}');
    }
    fputs("],\"datums\":[",stdout);first=true;
    for(int pass=0;pass<2;++pass){const World *w=pass?&g_preview.after:&g_preview.before;
        for(size_t i=0;i<w->datum_count;++i){uint32_t id=w->datums[i].id;
            const DatumPlane *before=world_find_datum(&g_preview.before,id),*after=world_find_datum(&g_preview.after,id);
            if(pass && before)continue;
            printf("%s{\"id\":%u,\"before\":",first?"":",",id);first=false;json_reference_datum(before);fputs(",\"after\":",stdout);json_reference_datum(after);putchar('}');
        }
    }putchar(']');
    json_grid_system_preview();
    json_grid_binding_preview();
    json_boundary_preview();
    fputs(",\"assembly\":{\"before\":",stdout);json_assembly_state(&g_preview.before,false);
    fputs(",\"after\":",stdout);json_assembly_state(&g_preview.after,false);putchar('}');
    fputs(",\"violations\":[",stdout);
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
/* Inspect quantity terms, not substrings: grid 1 must never match grid 10.
 * This reports direct dependencies; the core remains the deletion authority. */
static bool reference_expression_uses_grid(const char *expression,uint32_t id)
{
    const char *cursor=expression;
    while (*cursor) {
        if (*cursor=='+' || *cursor=='-') ++cursor;
        const char *end=cursor;
        while (*end && *end!='+' && *end!='-') ++end;
        const char *quantity=cursor;
        for (const char *p=cursor;p<end;++p) if (*p=='*') quantity=p+1;
        const char *number=NULL;
        if ((size_t)(end-quantity)>=5 && !strncmp(quantity,"grid:",5)) number=quantity+5;
        else if ((size_t)(end-quantity)>=6 && !strncmp(quantity,"panel:",6)) number=quantity+6;
        else if ((size_t)(end-quantity)>=4 && !strncmp(quantity,"gap:",4)) number=quantity+4;
        if (number) {
            const char *stop=number;
            while (stop<end && *stop>='0' && *stop<='9') ++stop;
            if (stop>number && stop<end && *stop==':' && (size_t)(stop-number)<16) {
                char value[16]; uint32_t found;
                memcpy(value,number,(size_t)(stop-number)); value[stop-number]='\0';
                if (parse_u32(value,&found) && found==id) return true;
            }
        }
        cursor=end;
    }
    return false;
}
static void json_grid_dependencies(const World *w,const ReferenceGrid *g)
{
    fputs(",\"dependencies\":{\"children\":[",stdout); bool first=true;
    for (size_t i=0;i<w->grid_count;++i) {
        if (!w->grids[i].is_subgrid || w->grids[i].parent_id!=g->id) continue;
        printf("%s%u",first?"":",",w->grids[i].id); first=false;
    }
    fputs("],\"guides\":[",stdout); first=true;
    for (size_t i=0;i<w->guide_count;++i) {
        if (!reference_expression_uses_grid(w->guides[i].expression,g->id) && !grid_guide_references(&w->guides[i],g->id)) continue;
        printf("%s%u",first?"":",",w->guides[i].id); first=false;
    }
    fputs("],\"timbers\":[",stdout); first=true;
    for (size_t i=0;i<w->timber_count;++i) {
        if (!w->timbers[i].placed || !((w->anchors[i].anchor_kind==ANCHOR_AT_GRID && w->anchors[i].ref_grid==g->id) ||
            (w->anchors[i].anchor_kind==ANCHOR_AT_RULE && w->anchors[i].ref_rule.grid_id==g->id))) continue;
        printf("%s%u",first?"":",",w->timbers[i].id); first=false;
    }
    fputs("]}",stdout);
}
static void json_reference_grid(const World *w,const ReferenceGrid *g)
{
    const PlacementSurface *p=world_find_placement(w,g->placement_id);
    const SpaceBoundarySurface *b=p?world_placement_boundary(w,p):NULL;
    printf("{\"id\":%u,\"surface\":%u",g->id,g->placement_id);
    fputs(",\"bindingId\":",stdout);
    if (g->from_binding) printf("%u",g->binding_id); else fputs("null",stdout);
    printf(",\"indexSpace\":\"%s\"",g->from_binding?"lattice":"ordinal");
    fputs(",\"sourceSystem\":",stdout);
    const GridBinding *binding=g->from_binding?world_find_grid_binding(w,g->binding_id):NULL;
    if (binding) printf("%u",binding->system_id);
    else if (g->from_system) printf("%u",g->system_id); else fputs("null",stdout);
    printf(",\"origin\":[%lld,%lld]",g->from_system?(long long)g->system_origin[0]:0LL,
        g->from_system?(long long)g->system_origin[1]:0LL);
    printf(",\"kind\":\"%s\",\"parentId\":",g->is_subgrid?"subgrid":"main");
    if (g->is_subgrid) {
        printf("%u,\"latticeCell\":",g->parent_id);
        if (g->lattice_cell) {
            printf("[\"%lld\",\"%lld\"],\"cellMode\":\"lattice\",\"cell\":{\"i\":\"%lld\",\"j\":\"%lld\"}",
                (long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1],
                (long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1]);
        } else {
            fputs("null,\"cellMode\":\"ordinal\",\"cell\":{",stdout);
            for (int axis=0;axis<2;++axis) {
                printf("%s\"%c\":[",axis?",":"",axis?'v':'u');
                for (int side=0;side<2;++side) {
                    char ref[32]; grid_cell_ref_format(g->cell_ref[axis][side],ref,sizeof ref);
                    if (side) putchar(','); js_string(ref);
                }
                putchar(']');
            }
            putchar('}');
        }
        printf(",\"divisions\":{\"u\":%u,\"v\":%u}",g->divisions[0],g->divisions[1]);
    } else fputs("null,\"cell\":null,\"divisions\":null",stdout);
    SurfaceRegion2 bounds;
    bool has_bounds=p && (g->is_subgrid?
        grid_cell_bounds(w->grids,w->grid_count,g,p,b,&bounds,NULL,0):
        placement_local_bounds(p,b,&bounds));
    fputs(",\"bounds\":",stdout);
    if (has_bounds) printf("{\"u\":[%lld,%lld],\"v\":[%lld,%lld]}",
        (long long)bounds.min_u,(long long)bounds.max_u,(long long)bounds.min_v,(long long)bounds.max_v);
    else fputs("null",stdout);
    if (!g->is_subgrid && g->main_along==1) fputs(",\"mainAlong\":\"u\"",stdout);
    else if (!g->is_subgrid && g->main_along==2) fputs(",\"mainAlong\":\"v\"",stdout);
    else fputs(",\"mainAlong\":null",stdout);
    GridQueryAxis *sampled=NULL; bool query_ok=false;
    if (g->from_binding) {
        Coord rect[4]={0}; char error[256]="";
        sampled=calloc(2,sizeof *sampled);
        if (has_bounds) {
            rect[0]=bounds.min_u; rect[1]=bounds.min_v; rect[2]=bounds.max_u; rect[3]=bounds.max_v;
            if (sampled) query_ok=grid_query(w,"grid",g->id,rect,GRID_MAX_LINES,true,sampled,error,sizeof error);
        }
        fputs(",\"geometryMode\":\"sample\",\"geometryExact\":false,\"query\":",stdout);
        if (query_ok) json_grid_query_result(sampled,rect,true);
        else json_grid_query_error(error[0]?error:"無法產生主格預覽");
    } else fputs(",\"geometryMode\":\"exact\",\"geometryExact\":true",stdout);
    for (int axis=0;axis<2;++axis) {
        const GridAxisDef *d=&g->axis[axis];
        Coord values[GRID_MAX_LINES]; size_t count=0;
        if (g->from_binding) {
            if (query_ok) { count=sampled[axis].count; for (size_t k=0;k<count;++k) values[k]=sampled[axis].lines[k].coordinate; }
        } else if (p) grid_axis_lines_in(w->grids,w->grid_count,g,p,b,axis,values,&count,NULL,0);
        printf(",\"%c\":[",axis?'v':'u');
        for (size_t k=0;k<count;++k) printf("%s%lld",k?",":"",(long long)values[k]);
        printf("],\"%cDefinition\":",axis?'v':'u');
        json_grid_axis_definition(d,g->is_subgrid,g->divisions[axis]);
    }
    if (g->from_binding) {
        fputs(",\"indices\":{",stdout);
        for (int axis=0;axis<2;++axis) {
            printf("%s\"%c\":[",axis?",":"",axis?'v':'u');
            if (query_ok) for (size_t k=0;k<sampled[axis].count;++k)
                printf("%s\"%lld\"",k?",":"",(long long)sampled[axis].lines[k].index);
            putchar(']');
        }
        fputs("},\"lattice\":{",stdout);
        for (int axis=0;axis<2;++axis) {
            printf("%s\"%c\":{\"defined\":%s,\"pitch\":%lld,\"baseIndex\":\"%lld\",\"baseCoordinate\":%lld}",
                axis?",":"",axis?'v':'u',g->lattice_step[axis]>0?"true":"false",
                (long long)g->lattice_step[axis],(long long)g->lattice_index[axis],(long long)g->lattice_base[axis]);
        }
        putchar('}');
    }
    fputs(",\"lines\":[",stdout);
    bool first=true;
    for (int axis=0;axis<2;++axis) {
        Coord values[GRID_MAX_LINES]; size_t count=0;
        if (g->from_binding) {
            if (query_ok) { count=sampled[axis].count; for (size_t k=0;k<count;++k) values[k]=sampled[axis].lines[k].coordinate; }
        } else if (p) grid_axis_lines_in(w->grids,w->grid_count,g,p,b,axis,values,&count,NULL,0);
        for (size_t k=0;k<count;++k) {
            if (!first) putchar(',');
            first=false;
            printf("{\"axis\":\"%c\",\"index\":",axis?'v':'u');
            if (g->from_binding) printf("\"%lld\"",(long long)sampled[axis].lines[k].index);
            else printf("%zu",k);
            printf(",\"coordinate\":%lld,\"role\":",(long long)values[k]);
            int role=g->is_subgrid?3:g->main_along==0?0:((g->main_along==1&&axis==1)||(g->main_along==2&&axis==0)?2:3);
            if (role==2) fputs("\"primary\",\"priority\":2",stdout);
            else if (role==3) fputs("\"secondary\",\"priority\":3",stdout);
            else fputs("null,\"priority\":null",stdout);
            fputs(",\"segments\":[",stdout);
            SurfaceSegment2 finite_segments[GUIDE_MAX_SEGMENTS];
            const SurfaceSegment2 *segments=finite_segments; size_t n;
            if (g->from_binding) { segments=sampled[axis].lines[k].segments; n=sampled[axis].lines[k].segment_count; }
            else n=grid_line_segments(w->grids,w->grid_count,g,p,b,axis,k,finite_segments,GUIDE_MAX_SEGMENTS);
            for (size_t j=0;j<n;++j) {
                printf("%s[[%lld,%lld],[%lld,%lld]",j?",":"",
                    (long long)segments[j].start.u,(long long)segments[j].start.v,
                    (long long)segments[j].end.u,(long long)segments[j].end.v);
                if (g->from_binding && sampled[axis].lines[k].segment_has_band[j])
                    printf(",\"%lld\"",(long long)sampled[axis].lines[k].segment_band[j]);
                fputs("]",stdout);
            }
            fputs("]}",stdout);
        }
    }
    putchar(']');
    free(sampled);
    json_grid_dependencies(w,g);
    putchar('}');
}
/* Read-only draft: run the canonical grid parser and expander on a World copy. */
static void cmd_grid_preview(const char *command)
{
    if (!command || strlen(command)>=SCENE_MAX_LINE || !utf8_is_valid(command)) {
        fputs("{\"ok\":false,\"error\":\"網格指令過長或編碼無效\"}\n",stdout); return;
    }
    char line[SCENE_MAX_LINE]; snprintf(line,sizeof line,"%s",command);
    char *tokens[SCENE_MAX_TOKENS];
    int count=split_tokens(line,tokens,SCENE_MAX_TOKENS);
    bool subgrid=count>0 && !strcmp(tokens[0],"subgrid");
    if (count<5 || (strcmp(tokens[0],"grid")!=0 && !subgrid)) {
        fputs("{\"ok\":false,\"error\":\"預覽需要 grid 或 subgrid 指令\"}\n",stdout); return;
    }
    World *draft=(World *)malloc(sizeof *draft);
    if (!draft) { fputs("{\"ok\":false,\"error\":\"預覽記憶體不足\"}\n",stdout); return; }
    *draft=g_world;
    g_scene_last_error[0]='\0';
    bool ok=subgrid?apply_subgrid_line("preview",0,tokens,count,draft):apply_grid_line("preview",0,tokens,count,draft);
    uint32_t id=0;
    if (ok && !parse_u32(tokens[1],&id)) ok=false;
    ReferenceGrid *grid=ok?world_find_grid_mut(draft,id):NULL;
    if (!grid) {
        fputs("{\"ok\":false,\"error\":",stdout); js_string(scene_last_error()); fputs("}\n",stdout);
    } else {
        fputs("{\"ok\":true,\"grid\":",stdout); json_reference_grid(draft,grid); fputs("}\n",stdout);
    }
    free(draft);
}
static void reference_face_text(char *out,size_t size,const ReferenceFace *r)
{
    if (r->kind) snprintf(out,size,"t%u",r->timber);
    else if (r->hole>=0) snprintf(out,size,"h%de%d",r->hole,r->edge);
    else snprintf(out,size,"e%d",r->edge);
}
/* Return stored I13 references; derived uv is never used to reconstruct an anchor. */
static void json_reference_timber_definition(const Timber *t,const TimberAnchor *a)
{
    char anchor[128],selector[128]="",face[32];
    if (a->anchor_kind==ANCHOR_AT_LINE) snprintf(anchor,sizeof anchor,"at-line guide %u",a->ref_guide);
    else if (a->anchor_kind==ANCHOR_AT_GRID) {
        if (a->ref_grid_has_band)
            snprintf(anchor,sizeof anchor,"at-line grid %u %c %lld band %lld",a->ref_grid,a->ref_grid_axis==0?'u':'v',(long long)a->ref_grid_index,(long long)a->ref_grid_band);
        else
            snprintf(anchor,sizeof anchor,"at-line grid %u %c %lld",a->ref_grid,a->ref_grid_axis==0?'u':'v',(long long)a->ref_grid_index);
    }
    else if(a->anchor_kind==ANCHOR_AT_RULE){
        const GridRuleLineRef *r=&a->ref_rule;
        snprintf(anchor,sizeof anchor,"at-line rule %u %u %u %lld %lld %c %u",r->grid_id,r->system_id,r->rule_key,
            (long long)r->cell[0],(long long)r->cell[1],r->axis?'v':'u',r->inner_index);
    }
    else {
        ReferenceFace ref={a->ref_is_timber?1:0,a->ref_hole,a->ref_edge,a->ref_timber};
        reference_face_text(face,sizeof face,&ref); snprintf(anchor,sizeof anchor,"at-face %s",face);
    }
    if (a->has_through) snprintf(selector,sizeof selector,"through %lld",(long long)a->through);
    else if (a->has_between) {
        char other[32]; reference_face_text(face,sizeof face,&a->between[0]);
        reference_face_text(other,sizeof other,&a->between[1]);
        snprintf(selector,sizeof selector,"between %s %s",face,other);
    }
    fputs("{\"anchor\":",stdout); js_string(anchor);
    fputs(",\"selector\":",stdout); js_string(selector);
    printf(",\"priority\":%lld}",(long long)t->cut_priority);
}
#include "timber_support_projection.inc"
/* Both readers serialize one authoritative World and its already checked hash.
 * No newline here: saved-source indexing embeds this same read-only payload. */
static void json_references_world(const World *w,const char *fingerprint)
{
    printf("{\"ok\":true,\"sourceFingerprint\":\"%s\",\"guides\":[",fingerprint);
    for (size_t i=0;i<w->guide_count;++i) {
        if (i) putchar(','); json_reference_guide(w,i);
    }
    fputs("],\"grids\":[",stdout);
    for (size_t i=0;i<w->grid_count;++i) {
        const ReferenceGrid *g=&w->grids[i];
        if (i) putchar(',');
        json_reference_grid(w,g);
    }
    fputs("],\"timbers\":[",stdout); bool first=true;
    for (size_t i=0;i<w->timber_count;++i) {
        if (!w->timbers[i].placed) continue;
        printf("%s{\"id\":%u,\"role\":",first?"":",",w->timbers[i].id); first=false;
        js_string(timber_role_name(w->timbers[i].role)); fputs(",\"geometry\":",stdout);
        json_reference_geometry(w,(int)i);
        fputs(",\"definition\":",stdout); json_reference_timber_definition(&w->timbers[i],&w->anchors[i]); putchar('}');
    }
    fputs("],\"timberSupports\":",stdout);
    json_timber_supports(w,fingerprint);
    fputs(",\"specs\":[",stdout);
    for (size_t i=0;i<w->spec_count;++i) {
        printf("%s{\"name\":",i?",":""); js_string(w->specs[i].name);
        printf(",\"value\":%lld}",(long long)w->specs[i].value);
    }
    fputs("],\"datums\":[",stdout);
    for (size_t i=0;i<w->datum_count;++i) {
        const DatumPlane *d=&w->datums[i];
        printf("%s{\"id\":%u,\"axis\":\"%c\",\"position\":%lld,\"expression\":",i?",":"",d->id,"XYZ"[d->axis],(long long)d->position);
        js_string(d->expression); fputs(",\"guides\":[",stdout); bool first=true;
        for (size_t j=0;j<w->guide_count;++j) if (w->guides[j].source==GUIDE_DATUM && w->guides[j].datum_id==d->id) {
            printf("%s%u",first?"":",",w->guides[j].id); first=false;
        }
        fputs("]}",stdout);
    }
    fputs("],\"engineeringSources\":",stdout);json_engineering_sources(w);
    /* Reuse the authoritative typed read: owned timbers inherit binding
       sources and must not be described as independent literal dimensions. */
    fputs(",\"assembly\":",stdout);json_assembly_state(w,false);putchar('}');
}
static void cmd_references(void)
{
    char fingerprint[65];
    if (!eng_definition_hash(&g_world,fingerprint)) {
        fputs("{\"ok\":false,\"error\":\"無法核對來源定義\"}\n",stdout);
        return;
    }
    json_references_world(&g_world,fingerprint);putchar('\n');
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
