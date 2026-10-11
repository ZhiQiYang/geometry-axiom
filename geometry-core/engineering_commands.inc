/* Ordered engineering operations mutate only a caller-owned candidate. */
static bool eng_operation(World *w,EngJson *j,int t)
{
    char op[40]; if (!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op)) return eng_fail("I35: operation requires an op name");
    if(!strcmp(op,"import-parameters")){
        if(!eng_json_keys(j,t,"op,value","")||!parameter_import(w,j,eng_json_member(j,t,"value")))return eng_fail(g_parameter_error[0]?g_parameter_error:"I39: invalid parameter package");return true;
    }
    if(!strcmp(op,"put-parameter")) {
        if(!eng_json_keys(j,t,"op,value","")||!parameter_put(w,j,eng_json_member(j,t,"value")))return eng_fail(g_parameter_error[0]?g_parameter_error:"I38: invalid parameter operation");return true;
    }
    if(!strcmp(op,"delete-parameter")) {
        uint32_t id;if(!eng_json_keys(j,t,"op,id","")||!parameter_u32(j,eng_json_member(j,t,"id"),&id))return eng_fail("I38: invalid parameter identity");
        return parameter_remove(w,id)?true:eng_fail(g_parameter_error);
    }
    if(!strcmp(op,"unbind-source")) {
        EngTarget target;Coord value;
        if(!eng_json_keys(j,t,"op,target","")||!eng_target_parse(j,eng_json_member(j,t,"target"),&target))return eng_fail("I38: invalid unbind target");
        EngBinding *b=eng_binding(w,&target);if(!b)return eng_fail("I38: target has no source binding");
        char error[512]="";if(!parameters_rebuild(w,error,sizeof error))return eng_fail(error);if(!eng_effective(w,b,&value,NULL,0))return false;
        if(target.kind){int i=reference_timber_index(w,target.id);if(target.field)w->timbers[i].size_b=value;else w->timbers[i].size_a=value;}
        else {GridAxisDef *a=&world_find_grid_mut(w,target.id)->axis[target.axis];if(target.field)a->gap=value;else a->panel=value;}
        size_t k=(size_t)(b-w->engineering.bindings);memmove(b,b+1,(w->engineering.binding_count-k-1)*sizeof *b);memset(&w->engineering.bindings[--w->engineering.binding_count],0,sizeof *b);return true;
    }
    if (!strcmp(op,"publish-material") || !strcmp(op,"publish-method")) {
        char hash[65],*expected=NULL; int h=eng_json_member(j,t,"fingerprint");
        if (!eng_json_keys(j,t,"op,value","fingerprint")) return eng_fail("I35: unexpected publication operation fields");
        if (h>=0) { if (!eng_json_string(j,h,hash,sizeof hash)) return eng_fail("I34: invalid fingerprint"); expected=hash; }
        return !strcmp(op,"publish-material")?eng_publish_material(w,j,eng_json_member(j,t,"value"),expected):eng_publish_method(w,j,eng_json_member(j,t,"value"),expected);
    }
    if (!strcmp(op,"put-application")) return eng_json_keys(j,t,"op,value","")?eng_put_application(w,j,eng_json_member(j,t,"value")):eng_fail("I35: unexpected application operation fields");
    if (!strcmp(op,"archive")) {
        char kind[16],id[ENG_ID_MAX]; uint32_t version; int archived;
        if (!eng_json_keys(j,t,"op,kind,id,version,value","") || !eng_json_string(j,eng_json_member(j,t,"kind"),kind,sizeof kind) || !eng_json_string(j,eng_json_member(j,t,"id"),id,sizeof id) || !eng_u32(j,eng_json_member(j,t,"version"),&version,true) || !eng_json_boolean(j,eng_json_member(j,t,"value"),&archived)) return eng_fail("I35: invalid archive operation");
        if (!strcmp(kind,"material")) { EngMaterialVersion *m=(EngMaterialVersion*)eng_material(w,id,version); if (!m) return eng_fail("I34: material version not found"); m->archived=archived!=0; }
        else if (!strcmp(kind,"method")) { EngMethodVersion *m=(EngMethodVersion*)eng_method(w,id,version); if (!m) return eng_fail("I34: method version not found"); m->archived=archived!=0; }
        else return eng_fail("I35: archive kind must be material/method");
        return true;
    }
    if (!strcmp(op,"set-source") || !strcmp(op,"set-override")) {
        EngTarget target;
        bool override=!strcmp(op,"set-override");
        if (!eng_json_keys(j,t,override?"op,target,value":"op,target,source","") || !eng_target_parse(j,eng_json_member(j,t,"target"),&target)) return eng_fail("I35: invalid source/override operation");
        uint32_t pid; int role; if (!eng_target_context(w,&target,&pid,&role)) return false;
        if (target.kind) { int i=reference_timber_index(w,target.id); if (!w->timbers[i].placed) return eng_fail("D28: bind only an already placed timber"); }
        if (!override) { EngDimensionSource source; if (!eng_source_parse(j,eng_json_member(j,t,"source"),&source,true)) return false; return eng_bind(w,&target,&source); }
        EngBinding *b=eng_binding(w,&target); if (!b) return eng_fail("D28: object override requires an explicit source binding");
        int value=eng_json_member(j,t,"value");
        if (eng_json_is_null(j,value)) { b->has_override=false; memset(&b->override_value,0,sizeof b->override_value); return true; }
        if (!eng_source_parse(j,value,&b->override_value,false)) return false; b->has_override=true; return true;
    }
    if (!strcmp(op,"bind-grid") || !strcmp(op,"bind-timber")) {
        bool grid=!strcmp(op,"bind-grid"); uint32_t id; char appid[ENG_ID_MAX];
        if (!eng_json_keys(j,t,grid?"op,id,application":"op,id,application,slot",grid?"anchors,create":"") || !eng_u32(j,eng_json_member(j,t,"id"),&id,false) || !eng_json_string(j,eng_json_member(j,t,"application"),appid,sizeof appid)) return eng_fail("D28: invalid binding operation");
        EngApplication *a=eng_application(w,appid); if (!a) return eng_fail("D28: application not found");
        const EngMethodVersion *method=eng_method(w,a->method.id,a->method.version); if (!method) return eng_fail("I34: application method not found");
        if (!grid) {
            char slot[16]; int r=-1; const char *names[]={"boundary","primary","secondary"};
            if (!eng_json_string(j,eng_json_member(j,t,"slot"),slot,sizeof slot)) return eng_fail("D28: timber binding requires an explicit role slot");
            for (int k=0;k<3;++k) if (!strcmp(slot,names[k])) r=k;
            int i=reference_timber_index(w,id);
            if (r<0 || i<0 || !w->timbers[i].placed || w->anchors[i].placement_id!=a->placement_id || (int)w->timbers[i].role!=r) return eng_fail("D28: timber must be placed on the application face with the selected matching role");
            for (int field=0;field<2;++field) { EngTarget target={1,id,0,field}; EngDimensionSource source={0}; source.kind=ENG_APPLICATION; source.field=ENG_BOUNDARY_A+r*2+field; snprintf(source.ref,sizeof source.ref,"%s",a->id); if (!eng_bind(w,&target,&source)) return false; }
            return true;
        }
        ReferenceGrid *g=world_find_grid_mut(w,id); int create=0;
        if (g && (g->from_system || g->from_binding)) return eng_fail("D29: grid-system applications cannot have engineering bindings");
        int create_t=eng_json_member(j,t,"create"); if (create_t>=0 && !eng_json_boolean(j,create_t,&create)) return eng_fail("D28: create must be boolean");
        if (g && (g->is_subgrid || g->placement_id!=a->placement_id)) return eng_fail("D28: selected main grid belongs to another face or is a subgrid");
        if (!g) {
            if (!create) return eng_fail("D28: selected main grid is missing; explicitly choose create");
            for (size_t k=0;k<w->grid_count;++k) if (!w->grids[k].is_subgrid && w->grids[k].placement_id==a->placement_id) return eng_fail("I10: placement already has a main grid");
            if (w->grid_count==WORLD_MAX_GRIDS) return eng_fail("I10: grid capacity exceeded");
            g=&w->grids[w->grid_count++]; memset(g,0,sizeof *g); g->id=id; g->placement_id=a->placement_id; g->main_along=a->main_along?a->main_along:method->main_along;
            if (!g->main_along) return eng_fail("D28: new grid main direction is not set");
        } else if (create) return eng_fail("D28: create grid ID already exists; select update instead");
        int anchors=eng_json_member(j,t,"anchors"); if (anchors>=0&&!eng_json_keys(j,anchors,"","u,v")) return eng_fail("D28: anchor fields must be u/v");
        const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 bounds;
        if (!p || !placement_local_bounds(p,world_placement_boundary(w,p),&bounds)) return eng_fail("D28: cannot resolve application face bounds");
        for (int axis=0;axis<2;++axis) {
            Coord anchor=g->axis[axis].anchor; int supplied=anchors<0?-1:eng_json_member(j,anchors,axis?"v":"u");
            if (supplied>=0) { int64_t value; if (!eng_json_integer(j,supplied,&value)||!coord_in_range(value)) return eng_fail("D28: grid anchor must be integer mm in D1 range"); anchor=value; }
            else if (g->axis[axis].source!=GRID_SRC_PANEL) {
                if (!a->anchor_kind[axis]) return eng_fail("D28: new panel axis needs an explicit origin or chosen face edge");
                anchor=a->anchor_kind[axis]==1?a->anchor[axis]:a->anchor_kind[axis]==2?(axis?bounds.min_v:bounds.min_u):(axis?bounds.max_v:bounds.max_u);
            }
            memset(&g->axis[axis],0,sizeof g->axis[axis]); g->axis[axis].source=GRID_SRC_PANEL; g->axis[axis].panel=1; g->axis[axis].anchor=anchor; g->axis[axis].anchor_explicit=true;
            for (int field=0;field<2;++field) { EngTarget target={0,id,axis,field}; EngDimensionSource source={0}; source.kind=ENG_APPLICATION; source.field=(field?ENG_U_GAP:ENG_U_PANEL)+axis; snprintf(source.ref,sizeof source.ref,"%s",a->id); if (!eng_bind(w,&target,&source)) return false; }
        }
        return true;
    }
    return eng_fail("I35: unknown engineering operation");
}

/* Native scene records contain only definitions. Values attached to bound
 * dimensions are sources and overrides, never copied evaluated dimensions. */
static bool eng_dimension_read(World *w,EngJson *j,int t,const EngTarget *target,Coord *cache)
{
    if (eng_json_integer(j,t,cache)) {
        if (*cache<((!target->kind&&target->field)?0:1) || *cache>COORD_LIMIT) return eng_fail("I35: invalid direct dimension");
        return true;
    }
    EngDimensionSource source;
    if (!eng_json_keys(j,t,"source,override","") || !eng_source_parse(j,eng_json_member(j,t,"source"),&source,true) || !eng_bind(w,target,&source)) return false;
    EngBinding *b=eng_binding(w,target); int o=eng_json_member(j,t,"override"); b->has_override=!eng_json_is_null(j,o);
    if (b->has_override && !eng_source_parse(j,o,&b->override_value,false)) return false;
    *cache=target->field&& !target->kind?0:1; return true;
}
static bool eng_restore_grid(World *w,EngJson *j,int t)
{
    uint32_t id,pid; int along;
    if (!eng_json_keys(j,t,"id,placement_id,mainAlong,axes","") || !eng_u32(j,eng_json_member(j,t,"id"),&id,false) || !eng_u32(j,eng_json_member(j,t,"placement_id"),&pid,false) || !world_find_placement(w,pid) || !eng_axis(j,eng_json_member(j,t,"mainAlong"),&along)) return eng_fail("I36: invalid engineering grid declaration");
    if (world_find_grid(w,id)) return eng_fail("I36: repeated engineering grid declaration");
    for (size_t i=0;i<w->grid_count;++i) if (!w->grids[i].is_subgrid && w->grids[i].placement_id==pid) return eng_fail("I10: duplicate main grid on placement");
    if (w->grid_count==WORLD_MAX_GRIDS) return eng_fail("I10: grid capacity exceeded");
    int axes=eng_json_member(j,t,"axes"); if (!eng_json_keys(j,axes,"u,v","")) return eng_fail("I36: grid axes require u/v");
    ReferenceGrid *g=&w->grids[w->grid_count++]; memset(g,0,sizeof *g); g->id=id; g->placement_id=pid; g->main_along=along;
    for (int axis=0;axis<2;++axis) {
        int a=eng_json_member(j,axes,axis?"v":"u"); if (eng_json_is_null(j,a)) continue;
        char kind[16]; if (!eng_json_string(j,eng_json_member(j,a,"kind"),kind,sizeof kind)) return eng_fail("I36: missing grid axis kind");
        GridAxisDef *def=&g->axis[axis];
        if (!strcmp(kind,"panel")) {
            int64_t anchor; if (!eng_json_keys(j,a,"kind,panel,gap,anchor","") || !eng_json_integer(j,eng_json_member(j,a,"anchor"),&anchor) || !coord_in_range(anchor)) return eng_fail("I36: invalid panel grid anchor");
            def->source=GRID_SRC_PANEL; def->anchor=anchor; def->anchor_explicit=true;
            EngTarget panel={0,id,axis,0},gap={0,id,axis,1};
            if (!eng_dimension_read(w,j,eng_json_member(j,a,"panel"),&panel,&def->panel) || !eng_dimension_read(w,j,eng_json_member(j,a,"gap"),&gap,&def->gap)) return false;
        } else if (!strcmp(kind,"series")) {
            int64_t start,step,n; if (!eng_json_keys(j,a,"kind,start,step,count","") || !eng_json_integer(j,eng_json_member(j,a,"start"),&start)||!coord_in_range(start) || !eng_json_integer(j,eng_json_member(j,a,"step"),&step)||step<1||step>COORD_LIMIT || !eng_json_integer(j,eng_json_member(j,a,"count"),&n)||n<1||n>GRID_MAX_LINES) return eng_fail("I36: invalid series axis");
            def->source=GRID_SRC_SERIES;def->start=start;def->step=step;def->series_count=(size_t)n;
        } else if (!strcmp(kind,"explicit")) {
            int coords=eng_json_member(j,a,"coords"); if (!eng_json_keys(j,a,"kind,coords","") || !eng_json_is_array(j,coords)) return eng_fail("I36: invalid explicit axis");
            int n=eng_json_size(j,coords); if (n<1||n>GRID_MAX_LINES) return eng_fail("I10: grid coordinate capacity exceeded");
            def->source=GRID_SRC_EXPLICIT;def->count=(size_t)n;
            for(int k=0;k<n;++k) { int64_t v;if(!eng_json_integer(j,eng_json_at(j,coords,k),&v)||!coord_in_range(v))return eng_fail("I36: invalid grid coordinate");def->coords[k]=v; }
        } else return eng_fail("I36: unknown grid axis kind");
    }
    return reference_checked("engineering",0,w);
}
static bool eng_restore_timber(World *w,EngJson *j,int t)
{
    uint32_t id;char role_name[16];TimberRole role;Coord priority=0;
    if (!eng_json_keys(j,t,"id,A,B,role","priority") || !eng_u32(j,eng_json_member(j,t,"id"),&id,false) || !eng_json_string(j,eng_json_member(j,t,"role"),role_name,sizeof role_name)) return eng_fail("I36: invalid engineering timber declaration");
    if (!strcmp(role_name,"boundary")) role=TIMBER_ROLE_BOUNDARY; else if (!strcmp(role_name,"primary")) role=TIMBER_ROLE_PRIMARY; else if (!strcmp(role_name,"secondary")) role=TIMBER_ROLE_SECONDARY; else if (!strcmp(role_name,"custom")) role=TIMBER_ROLE_CUSTOM; else return eng_fail("I36: unknown timber role");
    int pt=eng_json_member(j,t,"priority");if(role==TIMBER_ROLE_CUSTOM){int64_t v;if(!eng_json_integer(j,pt,&v)||v<1)return eng_fail("I36: custom role requires positive priority");priority=v;}else if(pt>=0)return eng_fail("I36: non-custom role cannot set priority");
    if (world_find_timber(w,id) || w->timber_count==WORLD_MAX_TIMBERS) return eng_fail("I10: timber ID exists or capacity exceeded");
    size_t i=w->timber_count++;Timber *timber=&w->timbers[i];if(!timber_construct(id,0,1,1,true,role,priority,timber))return false;memset(&w->anchors[i],0,sizeof w->anchors[i]);w->anchors[i].span_mode=SPAN_AUTO;
    EngTarget a={1,id,0,0},b={1,id,0,1};if(!eng_dimension_read(w,j,eng_json_member(j,t,"A"),&a,&timber->size_a)||!eng_dimension_read(w,j,eng_json_member(j,t,"B"),&b,&timber->size_b))return false;
    char error[256];if(!engineering_rebuild(w,error,sizeof error))return eng_fail(error);return true;
}
static bool apply_engineering_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    (void)count; unsigned char decoded[1800];size_t n=0;
    if(!eng_base64_decode(tokens[2],strlen(tokens[2]),decoded,sizeof decoded-1,&n)) {scene_error(path,line_no,"I36: invalid engineering record encoding");return false;}
    decoded[n]=0;EngJson j;
    if(!eng_json_parse_n(&j,(const char*)decoded,n)){scene_error(path,line_no,j.error);eng_json_free(&j);return false;}
    bool ok=false;g_engineering_error[0]=0;
    if(!strcmp(tokens[1],"material")||!strcmp(tokens[1],"method")){
        char fingerprint[65];
        if(eng_json_keys(&j,0,"value,fingerprint","")&&eng_json_string(&j,eng_json_member(&j,0,"fingerprint"),fingerprint,sizeof fingerprint))ok=!strcmp(tokens[1],"material")?eng_publish_material(w,&j,eng_json_member(&j,0,"value"),fingerprint):eng_publish_method(w,&j,eng_json_member(&j,0,"value"),fingerprint);
    }else if(!strcmp(tokens[1],"application"))ok=eng_put_application(w,&j,0);
    else if(!strcmp(tokens[1],"grid"))ok=eng_restore_grid(w,&j,0);
    else if(!strcmp(tokens[1],"timber"))ok=eng_restore_timber(w,&j,0);
    else if(!strcmp(tokens[1],"archive")){ok=eng_operation(w,&j,0);w->parameters.retired_count=0;}
    if(!ok)scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I36: invalid engineering record");
    eng_json_free(&j);return ok;
}
static bool sp_scene_required;
static bool apply_requires_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    if(!strcmp(tokens[1],SP_CAPABILITY)){sp_scene_required=true;return true;}
    (void)count;if(!strcmp(tokens[1],GRID_SUBDIVISION_CAPABILITY)){g_rule_scene_required=true;return true;}if(!strcmp(tokens[1],ASM_GENERATION_CAPABILITY)){w->assembly.generation_required=true;return true;}if(!strcmp(tokens[1],"engineering-spec/1")||!strcmp(tokens[1],"parameters/1")||!strcmp(tokens[1],ASM_CAPABILITY))return true;scene_error(path,line_no,"I32: unsupported required scene capability");return false;
}
