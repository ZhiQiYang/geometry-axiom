/* D29 / I37 / R32: reusable definitions, without an implicit surface. */
static bool grid_system_axis_valid(const GridAxisDef *a)
{
    if (a->source==GRID_SRC_NONE) return true;
    if (a->source==GRID_SRC_EXPLICIT) {
        if (!a->count || a->count>GRID_MAX_LINES || !grid_coord_list_is_valid(a->coords,a->count)) return false;
        for (size_t k=0;k<a->count;++k) if (!coord_in_range(a->coords[k])) return false;
        return true;
    }
    if (a->source==GRID_SRC_SERIES) {
        if (!coord_in_range(a->start) || a->step<=0 || !coord_in_range(a->step) ||
            !a->series_count || a->series_count>GRID_MAX_LINES) return false;
        /* Bounded operands make this multiplication safe before range checking. */
        return coord_in_range(a->start+(Coord)(a->series_count-1)*a->step);
    }
    return a->source==GRID_SRC_PANEL && a->panel>0 && coord_in_range(a->panel) &&
        a->gap>=0 && coord_in_range(a->gap) && coord_in_range(a->anchor) && a->anchor_explicit;
}

static bool grid_system_name_valid(const unsigned char *name,size_t n)
{
    if (!n || n>GRID_SYSTEM_NAME_MAX) return false;
    for (size_t i=0;i<n;) {
        uint32_t cp=name[i++],minimum=0; unsigned tails=0;
        if (cp<0x80) { if (cp<0x20 || cp==0x7f) return false; continue; }
        if (cp>=0xc2 && cp<=0xdf) { cp&=31; tails=1; minimum=0x80; }
        else if (cp>=0xe0 && cp<=0xef) { cp&=15; tails=2; minimum=0x800; }
        else if (cp>=0xf0 && cp<=0xf4) { cp&=7; tails=3; minimum=0x10000; }
        else return false;
        if (tails>n-i) return false;
        while (tails--) { unsigned byte=name[i++]; if ((byte&0xc0)!=0x80) return false; cp=(cp<<6)|(byte&63); }
        if (cp<minimum || cp>0x10ffff || (cp>=0xd800 && cp<=0xdfff) || (cp>=0x80 && cp<=0x9f)) return false;
    }
    return true;
}

static bool grid_system_valid(const GridSystem *s)
{
    size_t n=0; while (n<=GRID_SYSTEM_NAME_MAX && s->name[n]) ++n;
    return grid_system_name_valid((const unsigned char*)s->name,n) &&
        grid_system_axis_valid(&s->axis[0]) && grid_system_axis_valid(&s->axis[1]) &&
        (s->axis[0].source || s->axis[1].source) && s->main_along>=0 && s->main_along<=2 &&
        (s->main_along!=1 || s->axis[1].source) && (s->main_along!=2 || s->axis[0].source);
}

static bool grid_systems_rebuild(World *w,char *error,size_t cap)
{
    if (w->grid_system_count>WORLD_MAX_GRID_SYSTEMS) {
        snprintf(error,cap,"I37: grid-system capacity exceeded"); return false;
    }
    for (size_t i=0;i<w->grid_system_count;++i) {
        if (!grid_system_valid(&w->grid_systems[i])) {
            snprintf(error,cap,"I37: grid-system %u has an invalid definition",w->grid_systems[i].id); return false;
        }
        for (size_t j=0;j<i;++j) if (w->grid_systems[j].id==w->grid_systems[i].id) {
            snprintf(error,cap,"I37: duplicate grid-system identity"); return false;
        }
    }
    for (size_t i=0;i<w->grid_count;++i) {
        ReferenceGrid *g=&w->grids[i]; if (!g->from_system) continue;
        const GridSystem *s=world_find_grid_system(w,g->system_id);
        if (!s || g->is_subgrid || !coord_in_range(g->system_origin[0]) || !coord_in_range(g->system_origin[1])) {
            snprintf(error,cap,"I37: grid %u has a missing or invalid grid-system source",g->id); return false;
        }
        g->main_along=s->main_along;
        for (int axis=0;axis<2;++axis) {
            GridAxisDef *a=&g->axis[axis]; *a=s->axis[axis]; Coord offset=g->system_origin[axis];
            if (a->source==GRID_SRC_EXPLICIT) for (size_t k=0;k<a->count;++k) a->coords[k]+=offset;
            else if (a->source==GRID_SRC_SERIES) a->start+=offset;
            else if (a->source==GRID_SRC_PANEL) a->anchor+=offset;
            if (!grid_system_axis_valid(a)) {
                snprintf(error,cap,"I37: grid %u %c translated coordinates exceed D1 range",g->id,axis?'v':'u'); return false;
            }
        }
    }
    return true;
}

static int grid_system_hex_digit(char c)
{
    return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:-1;
}
static bool grid_system_read_name(const char *hex,char out[GRID_SYSTEM_NAME_MAX+1])
{
    size_t n=strlen(hex); if (!n || n%2 || n>GRID_SYSTEM_NAME_MAX*2) return false;
    for (size_t i=0;i<n/2;++i) {
        int a=grid_system_hex_digit(hex[i*2]),b=grid_system_hex_digit(hex[i*2+1]);
        if (a<0 || b<0) return false; out[i]=(char)(a*16+b);
    }
    out[n/2]=0; return grid_system_name_valid((const unsigned char*)out,n/2);
}
static bool grid_system_read_axis(char **t,int count,int *at,GridAxisDef *a)
{
    int i=*at; if (i>=count) return false;
    if (!strcmp(t[i],"none")) ++i;
    else if (!strcmp(t[i],"series")) {
        Coord n;
        if (i+3>=count || !parse_coord(t[i+1],&a->start) || !parse_coord(t[i+2],&a->step) ||
            !parse_i64(t[i+3],&n) || n<1 || n>GRID_MAX_LINES) return false;
        a->source=GRID_SRC_SERIES; a->series_count=(size_t)n; i+=4;
    } else if (!strcmp(t[i],"panel")) {
        if (i+5>=count || strcmp(t[i+2],"gap") || strcmp(t[i+4],"from") ||
            !parse_coord(t[i+1],&a->panel) || !parse_coord(t[i+3],&a->gap) || !parse_coord(t[i+5],&a->anchor)) return false;
        a->source=GRID_SRC_PANEL; a->anchor_explicit=true; i+=6;
    } else {
        /* Accept the descriptive explicit keyword as well as grid's bare list. */
        if (!strcmp(t[i],"explicit")) ++i;
        a->source=GRID_SRC_EXPLICIT;
        while (i<count && strcmp(t[i],"u") && strcmp(t[i],"v")) {
            if (a->count==GRID_MAX_LINES || !parse_coord(t[i],&a->coords[a->count])) return false;
            ++a->count; ++i;
        }
    }
    *at=i; return grid_system_axis_valid(a);
}
static bool apply_grid_system_line(const char *path,int line_no,char **t,int count,World *w)
{
    GridSystem s={0}; int i=6;
    if (count<10 || !parse_u32(t[1],&s.id) || strcmp(t[2],"name-hex") ||
        !grid_system_read_name(t[3],s.name) || strcmp(t[4],"main-along")) goto invalid;
    if (!strcmp(t[5],"u")) s.main_along=1;
    else if (!strcmp(t[5],"v")) s.main_along=2;
    else if (strcmp(t[5],"none")) goto invalid;
    for (int axis=0;axis<2;++axis) {
        if (i>=count || strcmp(t[i++],axis?"v":"u") || !grid_system_read_axis(t,count,&i,&s.axis[axis])) goto invalid;
    }
    if (i!=count || !grid_system_valid(&s)) goto invalid;
    World candidate=*w; size_t slot=0;
    while (slot<candidate.grid_system_count && candidate.grid_systems[slot].id!=s.id) ++slot;
    if (slot==candidate.grid_system_count) {
        if (slot==WORLD_MAX_GRID_SYSTEMS) { scene_error(path,line_no,"I37: grid-system capacity is 16"); return false; }
        ++candidate.grid_system_count;
    }
    candidate.grid_systems[slot]=s; reference_capture_trial(&candidate);
    if (!world_revalidate(&candidate)) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I37: grid-system dependencies invalid; unchanged"); return false;
    }
    *w=candidate; return true;
invalid:
    scene_error(path,line_no,"D29/I37: grid-system requires a valid UTF-8 name-hex, main-along, and complete u/v definitions in D1 range"); return false;
}

static bool apply_grid_system_application(const char *path,int line_no,char **t,int count,World *w)
{
    ReferenceGrid g={0};
    if (count!=9 || !parse_u32(t[1],&g.id) || strcmp(t[2],"on") || !parse_u32(t[3],&g.placement_id) ||
        strcmp(t[4],"from-system") || !parse_u32(t[5],&g.system_id) || strcmp(t[6],"origin") ||
        !parse_coord(t[7],&g.system_origin[0]) || !parse_coord(t[8],&g.system_origin[1])) {
        scene_error(path,line_no,"D29: grid id on surface from-system id origin u v"); return false;
    }
    if (!world_find_placement(w,g.placement_id) || !world_find_grid_system(w,g.system_id)) {
        scene_error(path,line_no,"I37: grid application needs an existing surface and grid-system"); return false;
    }
    if (eng_object_bound(w,0,g.id)) {
        scene_error(path,line_no,"D29/I37: detach engineering bindings before choosing a grid-system source"); return false;
    }
    g.from_system=true; size_t slot=w->grid_count;
    for (size_t k=0;k<w->grid_count;++k) {
        const ReferenceGrid *old=&w->grids[k];
        if (old->id==g.id) {
            if (old->is_subgrid || old->placement_id!=g.placement_id) {
                scene_error(path,line_no,"I37: cannot change a subgrid or move an existing grid identity to another surface"); return false;
            }
            slot=k;
        } else if (!old->is_subgrid && old->placement_id==g.placement_id) {
            scene_error(path,line_no,"I10: this surface already has a main grid"); return false;
        }
    }
    if (slot==w->grid_count && slot==WORLD_MAX_GRIDS) { scene_error(path,line_no,"I10: grid capacity exceeded"); return false; }
    World candidate=*w; candidate.grids[slot]=g;
    if (slot==candidate.grid_count) ++candidate.grid_count;
    reference_capture_trial(&candidate);
    /* grid-preview calls this parser directly; retain the same I23 baseline. */
    const World *previous_baseline=g_subgrid_before;
    if (!previous_baseline) g_subgrid_before=w;
    bool valid=world_revalidate(&candidate);
    g_subgrid_before=previous_baseline;
    if (!valid) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I37: application or dependent geometry invalid; unchanged"); return false;
    }
    *w=candidate; return true;
}

static void grid_systems_dump(const World *w,FILE *out)
{
    for (size_t i=0;i<w->grid_system_count;++i) {
        const GridSystem *s=&w->grid_systems[i]; fprintf(out,"grid-system %u name-hex ",s->id);
        for (size_t k=0;s->name[k];++k) fprintf(out,"%02x",(unsigned char)s->name[k]);
        fprintf(out," main-along %s",s->main_along==1?"u":s->main_along==2?"v":"none");
        for (int axis=0;axis<2;++axis) {
            const GridAxisDef *a=&s->axis[axis]; fprintf(out," %c",axis?'v':'u');
            if (a->source==GRID_SRC_NONE) fputs(" none",out);
            else if (a->source==GRID_SRC_EXPLICIT) {
                fputs(" explicit",out); for (size_t k=0;k<a->count;++k) fprintf(out," %lld",(long long)a->coords[k]);
            } else if (a->source==GRID_SRC_SERIES) fprintf(out," series %lld %lld %u",(long long)a->start,(long long)a->step,(unsigned)a->series_count);
            else fprintf(out," panel %lld gap %lld from %lld",(long long)a->panel,(long long)a->gap,(long long)a->anchor);
        }
        fputc('\n',out);
    }
}
