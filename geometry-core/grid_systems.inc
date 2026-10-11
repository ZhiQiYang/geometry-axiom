/* D29 / D10b / I37 / R32: reusable definitions, without an implicit surface. */
static char g_grid_stagger_error[256];
/* Diagnostics only: the existing definition predicates remain authoritative. */
static char g_grid_definition_error[256];
static bool grid_definition_error(const char *field,const char *detail)
{
    snprintf(g_grid_definition_error,sizeof g_grid_definition_error,"D29/I37: grid-system %s %s",field,detail);
    return false;
}
static bool grid_axis_definition_error(int axis,const char *field,const char *detail)
{
    snprintf(g_grid_definition_error,sizeof g_grid_definition_error,"D29/I37: grid-system %c %s %s",axis?'v':'u',field,detail);
    return false;
}
static void grid_rules_dump(const GridSystem *,FILE *);
static bool grid_axis_stagger_ok(const GridSystem *,int,char *,size_t);
static bool grid_parameter_token(const char *,Coord *,ParameterRef *,bool);
static bool grid_system_axis_valid(const GridAxisDef *a)
{
    if (a->source==GRID_SRC_NONE) return true;
    if (a->source==GRID_SRC_REPEAT) return coord_in_range(a->start) && a->step>0 && coord_in_range(a->step);
    if (a->source==GRID_SRC_REPEAT_PANEL) return a->panel>0 && coord_in_range(a->panel) &&
        a->gap>=0 && coord_in_range(a->gap) && coord_in_range(a->anchor) && a->anchor_explicit;
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
    if(grid_system_is_infinite(s)) for(int a=0;a<2;++a)
        if(s->axis[a].source && !grid_axis_is_infinite(&s->axis[a])) return false;
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
        for(int axis=0;axis<2;++axis){
            GridAxisDef *a=&w->grid_systems[i].axis[axis];
            Coord *values[]={&a->start,&a->step,&a->panel,&a->gap,&a->anchor,&a->stagger};
            for(int field=0;field<6;++field)if(a->parameters[field].set){
                if(!grid_axis_is_infinite(a)||!parameter_coord(w,a->parameters[field],values[field])){
                    snprintf(error,cap,"grid-system %u %c: %.190s",w->grid_systems[i].id,axis?'v':'u',g_parameter_error);return false;
                }
            }
            if(!grid_axis_stagger_ok(&w->grid_systems[i],axis,error,cap)) return false;
        }
        if (!grid_system_valid(&w->grid_systems[i])) {
            snprintf(error,cap,"I37: grid-system %u has an invalid definition",w->grid_systems[i].id); return false;
        }
        if(!grid_rules_valid(&w->grid_systems[i],error,cap)) return false;
        for (size_t j=0;j<i;++j) if (w->grid_systems[j].id==w->grid_systems[i].id) {
            snprintf(error,cap,"I37: duplicate grid-system identity"); return false;
        }
    }
    for (size_t i=0;i<w->grid_count;++i) {
        ReferenceGrid *g=&w->grids[i]; if (!g->from_system) continue;
        const GridSystem *s=world_find_grid_system(w,g->system_id);
        if (!s || grid_system_is_infinite(s) || g->from_binding || g->is_subgrid || !coord_in_range(g->system_origin[0]) || !coord_in_range(g->system_origin[1])) {
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
    if (!strcmp(hex,"main-along")) return grid_definition_error("name-hex","must be non-empty");
    size_t n=strlen(hex);
    if (!n || n%2 || n>GRID_SYSTEM_NAME_MAX*2) {
        if (!n) return grid_definition_error("name-hex","must be non-empty");
        if (n>GRID_SYSTEM_NAME_MAX*2) return grid_definition_error("name-hex","exceeds 96 bytes");
        return grid_definition_error("name-hex","requires complete hexadecimal byte pairs");
    }
    for (size_t i=0;i<n/2;++i) {
        int a=grid_system_hex_digit(hex[i*2]),b=grid_system_hex_digit(hex[i*2+1]);
        if (a<0 || b<0) return grid_definition_error("name-hex","contains a non-hexadecimal byte");
        out[i]=(char)(a*16+b);
    }
    out[n/2]=0;
    if (!grid_system_name_valid((const unsigned char*)out,n/2)) {
        for (size_t i=0;i<n/2;++i) {
            unsigned char byte=(unsigned char)out[i];
            if (byte<0x20 || byte==0x7f) {
                snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                    "D29/I37: grid-system name-hex contains control byte 0x%02x",(unsigned)byte);
                return false;
            }
        }
        return grid_definition_error("name-hex","requires valid UTF-8 without control characters");
    }
    return true;
}
static bool grid_axis_stagger_ok(const GridSystem *s,int axis,char *error,size_t cap)
{
    const GridAxisDef *a=&s->axis[axis],*other=&s->axis[1-axis];
    Coord pitch; int64_t sum;
    if(!a->stagger_set) return true;
    if(!grid_axis_is_infinite(a) || !grid_axis_is_infinite(other)){
        snprintf(error,cap,"I24: 相位差只接受兩軸都存在的無限排法"); return false;
    }
    pitch=grid_axis_pitch(a);
    if(pitch<=0){ snprintf(error,cap,"I24: grid-system %u %c has no positive pitch",s->id,axis?'v':'u'); return false; }
    if(a->stagger==0){
        snprintf(error,cap,"I24: 相位差為 0。要貫通線請省略 stagger，不要寫 0"); return false;
    }
    if(a->stagger%pitch==0){
        snprintf(error,cap,"I24: 相位差是間距的整數倍，奇數格與偶數格的線會重合。要貫通線請省略這個欄位"); return false;
    }
    if(!grid_i64_add(grid_axis_phase(a),a->stagger,&sum)){
        snprintf(error,cap,"I24: 相位加相位差超出可表達範圍"); return false;
    }
    return true;
}
static bool grid_system_read_stagger(char **t,int count,int *at,GridAxisDef *a)
{
    int i=*at;
    if(i>=count || strcmp(t[i],"stagger")) return true;
    if(!grid_axis_is_infinite(a)){
        snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差只接受無限軸"); return false;
    }
    if(i+1>=count || !grid_parameter_token(t[i+1],&a->stagger,&a->parameters[5],true)) return false;
    if(!a->parameters[5].set && a->stagger==0){
        snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差為 0。要貫通線請省略 stagger，不要寫 0"); return false;
    }
    a->stagger_set=true; *at=i+2; return true;
}
static bool grid_parameter_token(const char *text,Coord *value,ParameterRef *ref,bool allowed)
{
    if(allowed&&!strncmp(text,"param:",6)){*value=1;return parameter_ref_parse(text,ref);}
    return parse_coord(text,value);
}
static void grid_parameter_dump(FILE *out,Coord value,ParameterRef ref)
{
    if(ref.set)fprintf(out,"param:%u:%u",ref.parameter_id,ref.field_id);
    else fprintf(out,"%lld",(long long)value);
}
static bool grid_system_read_axis(char **t,int count,int *at,GridAxisDef *a,int axis)
{
    int i=*at; if (i>=count) return grid_axis_definition_error(axis,"definition","is missing");
    if (!strcmp(t[i],"none")) ++i;
    else if (!strcmp(t[i],"repeat")) {
        if(i+2>=count) return grid_axis_definition_error(axis,"repeat","requires phase and step");
        if(!grid_parameter_token(t[i+1],&a->start,&a->parameters[0],true)) return grid_axis_definition_error(axis,"phase","requires an integer in D1 range or ParameterRef");
        if(!grid_parameter_token(t[i+2],&a->step,&a->parameters[1],true)) return grid_axis_definition_error(axis,"step","requires an integer in D1 range or ParameterRef");
        a->source=GRID_SRC_REPEAT; i+=3;
    }
    else if (!strcmp(t[i],"series")) {
        Coord n;
        if (i+3>=count) return grid_axis_definition_error(axis,"series","requires start, step and count");
        if (!parse_coord(t[i+1],&a->start)) return grid_axis_definition_error(axis,"start","requires an integer in D1 range");
        if (!parse_coord(t[i+2],&a->step)) return grid_axis_definition_error(axis,"step","requires an integer in D1 range");
        if (!parse_i64(t[i+3],&n)) return grid_axis_definition_error(axis,"count","requires a signed integer");
        if (n<1 || n>GRID_MAX_LINES) {
            snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                "D29/I37: grid-system %c count=%lld must be in 1..64",axis?'v':'u',(long long)n);
            return false;
        }
        a->source=GRID_SRC_SERIES; a->series_count=(size_t)n; i+=4;
    } else if (!strcmp(t[i],"panel") || !strcmp(t[i],"repeat-panel")) {
        if (i+5>=count || strcmp(t[i+2],"gap") || strcmp(t[i+4],"from"))
            return grid_axis_definition_error(axis,"anchor","requires explicit from after panel and gap");
        if (!grid_parameter_token(t[i+1],&a->panel,&a->parameters[2],!strcmp(t[i],"repeat-panel"))) return grid_axis_definition_error(axis,"panel","requires an integer in D1 range");
        if (!grid_parameter_token(t[i+3],&a->gap,&a->parameters[3],!strcmp(t[i],"repeat-panel"))) return grid_axis_definition_error(axis,"gap","requires an integer in D1 range");
        if (!grid_parameter_token(t[i+5],&a->anchor,&a->parameters[4],!strcmp(t[i],"repeat-panel"))) return grid_axis_definition_error(axis,"anchor","requires an integer in D1 range");
        a->source=!strcmp(t[i],"panel")?GRID_SRC_PANEL:GRID_SRC_REPEAT_PANEL; a->anchor_explicit=true; i+=6;
    } else {
        /* Accept the descriptive explicit keyword as well as grid's bare list. */
        if (!strcmp(t[i],"explicit")) ++i;
        a->source=GRID_SRC_EXPLICIT;
        while (i<count && strcmp(t[i],"u") && strcmp(t[i],"v")) {
            if (!strcmp(t[i],"stagger")) {
                snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差只接受無限軸"); return false;
            }
            if (a->count==GRID_MAX_LINES) return grid_axis_definition_error(axis,"explicit count","exceeds 64 lines");
            if (!parse_coord(t[i],&a->coords[a->count])) return grid_axis_definition_error(axis,"explicit coordinate","requires an integer in D1 range");
            ++a->count; ++i;
        }
    }
    if (!grid_system_read_stagger(t,count,&i,a)) {
        if (!g_grid_stagger_error[0]) grid_axis_definition_error(axis,"stagger","requires an integer in D1 range or ParameterRef");
        return false;
    }
    *at=i;
    if (!grid_system_axis_valid(a)) {
        if ((a->source==GRID_SRC_REPEAT || a->source==GRID_SRC_SERIES) && a->step<=0) {
            snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                "D29/I37: grid-system %c step=%lld must be positive",axis?'v':'u',(long long)a->step);
        } else if (a->source==GRID_SRC_EXPLICIT) {
            if (!a->count) return grid_axis_definition_error(axis,"explicit coordinates","must be non-empty");
            for (size_t k=1;k<a->count;++k) if (a->coords[k]<=a->coords[k-1]) {
                snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                    "D29/I37: grid-system %c explicit coordinate[%u]=%lld must be greater than coordinate[%u]=%lld",
                    axis?'v':'u',(unsigned)k,(long long)a->coords[k],(unsigned)(k-1),(long long)a->coords[k-1]);
                return false;
            }
            return grid_axis_definition_error(axis,"explicit coordinates","exceed D1 range");
        } else if (a->source==GRID_SRC_SERIES) {
            return grid_axis_definition_error(axis,"series last coordinate","exceeds D1 range");
        } else if (a->panel<=0) {
            snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                "D29/I37: grid-system %c panel=%lld must be positive",axis?'v':'u',(long long)a->panel);
        } else if (a->gap<0) {
            snprintf(g_grid_definition_error,sizeof g_grid_definition_error,
                "D29/I37: grid-system %c gap=%lld must be non-negative",axis?'v':'u',(long long)a->gap);
        } else return grid_axis_definition_error(axis,"definition","has values outside D1 range");
        return false;
    }
    return true;
}
static bool apply_grid_system_line(const char *path,int line_no,char **t,int count,World *w)
{
    GridSystem s={0}; s.next_rule_key=1; int i=6; g_grid_stagger_error[0]=0; g_grid_definition_error[0]=0;
    if (count<10) { grid_definition_error("declaration","requires name-hex, main-along and u/v definitions"); goto invalid; }
    if (!parse_u32(t[1],&s.id)) { grid_definition_error("id","must be uint32 (0..4294967295)"); goto invalid; }
    if (strcmp(t[2],"name-hex")) { grid_definition_error("name-hex","keyword is missing"); goto invalid; }
    if (!grid_system_read_name(t[3],s.name)) goto invalid;
    if (strcmp(t[4],"main-along")) { grid_definition_error("main-along","keyword is missing"); goto invalid; }
    if (!strcmp(t[5],"u")) s.main_along=1;
    else if (!strcmp(t[5],"v")) s.main_along=2;
    else if (strcmp(t[5],"none")) { grid_definition_error("main-along","must be none, u or v"); goto invalid; }
    for (int axis=0;axis<2;++axis) {
        if (i>=count || strcmp(t[i++],axis?"v":"u")) { grid_axis_definition_error(axis,"definition","keyword is missing"); goto invalid; }
        if (!grid_system_read_axis(t,count,&i,&s.axis[axis],axis)) goto invalid;
    }
    if (i!=count) { grid_definition_error("declaration","has unexpected trailing tokens"); goto invalid; }
    if (!grid_system_valid(&s)) {
        if (grid_system_is_infinite(&s)) {
            for (int axis=0;axis<2;++axis) if (s.axis[axis].source && !grid_axis_is_infinite(&s.axis[axis])) {
                grid_axis_definition_error(axis,"source","cannot mix legacy-finite with infinite axes"); goto invalid;
            }
        }
        if (!s.axis[0].source && !s.axis[1].source) grid_definition_error("u/v sources","cannot both be none");
        else if (s.main_along==1 && !s.axis[1].source) grid_definition_error("main-along=u","requires v source");
        else if (s.main_along==2 && !s.axis[0].source) grid_definition_error("main-along=v","requires u source");
        else grid_definition_error("definition","has invalid name or axis values");
        goto invalid;
    }
    World candidate=*w; size_t slot=0;
    while (slot<candidate.grid_system_count && candidate.grid_systems[slot].id!=s.id) ++slot;
    if(slot<candidate.grid_system_count && grid_system_is_infinite(&candidate.grid_systems[slot])!=grid_system_is_infinite(&s)) {
        scene_error(path,line_no,"D29/I37: legacy-finite and infinite identities cannot be converted implicitly"); return false;
    }
    if (slot==candidate.grid_system_count) {
        if (slot==WORLD_MAX_GRID_SYSTEMS) { scene_error(path,line_no,"I37: grid-system capacity is 16"); return false; }
        ++candidate.grid_system_count;
    }
    if(slot<w->grid_system_count) {
        s.rule_count=w->grid_systems[slot].rule_count;
        s.next_rule_key=w->grid_systems[slot].next_rule_key;
        memcpy(s.rules,w->grid_systems[slot].rules,sizeof s.rules);
    }
    candidate.grid_systems[slot]=s; reference_capture_trial(&candidate);
    if (!world_revalidate(&candidate)) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I37: grid-system dependencies invalid; unchanged"); return false;
    }
    *w=candidate; return true;
invalid:
    scene_error(path,line_no,g_grid_stagger_error[0]?g_grid_stagger_error:g_grid_definition_error); return false;
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
            if (old->is_subgrid || old->from_binding || old->placement_id!=g.placement_id) {
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
            else if(a->source==GRID_SRC_REPEAT) {
                fputs(" repeat ",out);grid_parameter_dump(out,a->start,a->parameters[0]);fputc(' ',out);grid_parameter_dump(out,a->step,a->parameters[1]);
                if(a->stagger_set){fputs(" stagger ",out);grid_parameter_dump(out,a->stagger,a->parameters[5]);}
            } else {
                fprintf(out," %s ",a->source==GRID_SRC_REPEAT_PANEL?"repeat-panel":"panel");grid_parameter_dump(out,a->panel,a->parameters[2]);
                fputs(" gap ",out);grid_parameter_dump(out,a->gap,a->parameters[3]);fputs(" from ",out);grid_parameter_dump(out,a->anchor,a->parameters[4]);
                if(a->source==GRID_SRC_REPEAT_PANEL && a->stagger_set){fputs(" stagger ",out);grid_parameter_dump(out,a->stagger,a->parameters[5]);}
            }
        }
        fputc('\n',out);
        grid_rules_dump(s,out);
    }
}
