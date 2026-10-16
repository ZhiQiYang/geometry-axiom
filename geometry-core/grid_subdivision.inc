/* D19a/I25a/R32: source-owned rules; one authoritative cell evaluator. */
static bool g_rule_scene_highwater[WORLD_MAX_GRID_SYSTEMS];
static bool g_rule_scene_required;
static bool g_rule_scene_encountered;

static const GridSubdivisionRule *grid_rule_find(const GridSystem *s,uint32_t key)
{ return geo_grid_rule_find(s,key); }
static bool grid_rule_error(char *err,size_t cap,const char *code,uint32_t sid,uint32_t key)
{
    if(err)snprintf(err,cap,"I25a: %s source %u rule %u",code,sid,key);
    return false;
}
static bool grid_rules_valid(const GridSystem *s,char *err,size_t cap)
{
    GeoGridStoreError detail;if(geo_grid_rules_validate(s,&detail))return true;
    const char *code="RULE_KEY";
    switch(detail.status){
    case GEO_GRID_STORE_RULE_CAPACITY:code="RULE_CAPACITY";break;
    case GEO_GRID_STORE_RULE_SOURCE:code="SOURCE_KIND";break;
    case GEO_GRID_STORE_RULE_NAME:code="RULE_NAME";break;
    case GEO_GRID_STORE_RULE_DIVISIONS:code="DIVISION_RANGE";break;
    case GEO_GRID_STORE_RULE_NOT_DIVISIBLE:code="DIVISION_NOT_EXACT";break;
    case GEO_GRID_STORE_RULE_CELL_RANGE:code="CELL_RANGE";break;
    case GEO_GRID_STORE_RULE_OVERLAP:
        if(err)snprintf(err,cap,"I25a: RULE_OVERLAP source %u rules %u/%u",s->id,detail.other_rule_key,detail.rule_key);return false;
    default:break;
    }
    return grid_rule_error(err,cap,code,s->id,detail.rule_key);
}
static bool grid_rule_matches(const GridSubdivisionRule *r,const int64_t cell[2])
{ return geo_grid_rule_matches(r,cell); }

static bool grid_rule_ref_text(const char *text,GridRuleLineRef *r)
{
    if(strlen(text)>=REF_EXPR_MAX)return false;
    char buf[REF_EXPR_MAX],*parts[8];size_t n=0;snprintf(buf,sizeof buf,"%s",text);
    char *p=buf;
    while(n<8){parts[n++]=p;char *colon=strchr(p,':');if(!colon)break;*colon=0;p=colon+1;}
    if(n!=8 || strchr(parts[7],':') || strcmp(parts[0],"gridrule") ||
        !parse_u32(parts[1],&r->grid_id) || !parse_u32(parts[2],&r->system_id) ||
        !parse_u32(parts[3],&r->rule_key) || !r->rule_key || !parse_i64(parts[4],&r->cell[0]) ||
        !parse_i64(parts[5],&r->cell[1]) || (strcmp(parts[6],"u") && strcmp(parts[6],"v")) ||
        !parse_u32(parts[7],&r->inner_index))return false;
    r->axis=!strcmp(parts[6],"u")?0:1;return true;
}
static bool grid_rule_expression_uses(const char *expression,uint32_t sid,uint32_t key)
{
    const char *p=expression;
    while((p=strstr(p,"gridrule:"))!=NULL){
        const char *end=p;
        while(*end && !((*end=='+' || *end=='-') && !(end>p && end[-1]==':' && isdigit((unsigned char)end[1]))))++end;
        size_t n=(size_t)(end-p);GridRuleLineRef r={0};char term[REF_EXPR_MAX];
        if(n<sizeof term){memcpy(term,p,n);term[n]=0;if(grid_rule_ref_text(term,&r) && r.system_id==sid && r.rule_key==key)return true;}
        p+=9;
    }
    return false;
}
static bool grid_rule_used(const World *w,uint32_t sid,uint32_t key)
{
    for(size_t i=0;i<geo_guides_count(&w->guide_lines);++i)if(grid_rule_expression_uses(app_guide_expression(w,geo_guides_values(&w->guide_lines)[i].id),sid,key))return true;
    for(size_t i=0;i<w->timber_count;++i){const TimberAnchor *a=&w->anchors[i];
        if(w->timbers[i].placed && a->anchor_kind==ANCHOR_AT_RULE && a->ref_rule.system_id==sid && a->ref_rule.rule_key==key)return true;
    }
    return false;
}
static bool grid_rules_world_valid(const World *w,char *err,size_t cap)
{
    if(g_subgrid_before)for(size_t i=0;i<geo_grid_systems_count(&g_subgrid_before->grid_store);++i){
        const GridSystem *old=geo_grid_systems_at(&g_subgrid_before->grid_store,i),*now=world_find_grid_system(w,old->id);
        for(size_t j=0;j<old->rule_count;++j){const GridSubdivisionRule *r=&old->rules[j],*q=grid_rule_find(now,r->key);
            if(grid_rule_used(g_subgrid_before,old->id,r->key) && (!q || q->all_cells!=r->all_cells ||
                memcmp(q->cell,r->cell,sizeof r->cell) || memcmp(q->divisions,r->divisions,sizeof r->divisions)))
                return grid_rule_error(err,cap,"RULE_REFERENCED",old->id,r->key);
        }
    }
    for(size_t i=0;i<w->grid_count;++i){const ReferenceGrid *g=&w->grids[i];
        if(!g->is_subgrid || !g->lattice_cell)continue;
        const ReferenceGrid *parent=world_find_grid(w,g->parent_id);
        const GridBinding *binding=parent && parent->from_binding?world_find_grid_binding(w,parent->binding_id):NULL;
        const GridSystem *s=binding?world_find_grid_system(w,binding->system_id):NULL;
        if(s)for(size_t j=0;j<s->rule_count;++j)if(grid_rule_matches(&s->rules[j],g->lattice_cell_index)){
            if(err)snprintf(err,cap,"I25a: MANUAL_CONFLICT source %u rule %u manual %u parent %u cell (%lld,%lld)",
                s->id,s->rules[j].key,g->id,parent->id,(long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1]);
            return false;
        }
    }
    return true;
}

/* Returned DTO pointers borrow caller storage, including component boundaries
 * inside the placement; they must outlive the complete line/cell query. */
static bool grid_rule_target(const World *w,const char *kind,uint32_t id,ReferenceGrid *derived,
    const GridSystem **source,const PlacementSurface **placement,const SpaceBoundarySurface **boundary,
    PlacementSurface *placement_storage,SpaceBoundarySurface *boundary_storage,char *err,size_t cap)
{
    memset(derived,0,sizeof *derived);*source=NULL;*placement=NULL;*boundary=NULL;
    if(!strcmp(kind,"system")){
        *source=world_find_grid_system(w,id);
        if(!*source)return grid_rule_error(err,cap,"WRONG_SOURCE",id,0);
        derived->from_binding=true;
        for(int a=0;a<2;++a){derived->axis[a]=(*source)->axis[a];derived->lattice_base[a]=grid_axis_phase(&(*source)->axis[a]);derived->lattice_step[a]=grid_axis_pitch(&(*source)->axis[a]);}
    }else{
        const GridBinding *binding=NULL;
        if(!strcmp(kind,"binding"))binding=world_find_grid_binding(w,id);
        else if(!strcmp(kind,"grid")){
            const ReferenceGrid *g=world_find_grid(w,id);
            if(!g || !g->from_binding || g->is_subgrid)return grid_rule_error(err,cap,"WRONG_SOURCE",0,0);
            *derived=*g;binding=world_find_grid_binding(w,g->binding_id);
            *placement=app_placement_read(w,g->placement_id,placement_storage);
            if(!*placement)return grid_rule_error(err,cap,"WRONG_SOURCE",0,0);
        }
        if(!binding || !grid_binding_cache(w,binding,derived,err,cap))return false;
        *source=world_find_grid_system(w,binding->system_id);
        *boundary=*placement?app_placement_boundary(w,*placement,boundary_storage):app_boundary_read(w,binding->boundary_id,boundary_storage);
    }
    if(!*source || (*source)->axis[0].source!=GRID_SRC_REPEAT || (*source)->axis[1].source!=GRID_SRC_REPEAT ||
        (*source)->axis[0].stagger_set || (*source)->axis[1].stagger_set)return grid_rule_error(err,cap,"SOURCE_KIND",*source?(*source)->id:0,0);
    return true;
}
static bool grid_rule_cell(const World *w,const char *kind,uint32_t id,uint32_t key,const int64_t cell[2],
    ReferenceGrid *derived,const GridSystem **source,const GridSubdivisionRule **rule,SurfaceRegion2 *bounds,
    const PlacementSurface **placement,const SpaceBoundarySurface **boundary,
    PlacementSurface *placement_storage,SpaceBoundarySurface *boundary_storage,char *err,size_t cap)
{
    if(!grid_rule_target(w,kind,id,derived,source,placement,boundary,placement_storage,boundary_storage,err,cap))return false;
    *rule=grid_rule_find(*source,key);
    if(!*rule)return grid_rule_error(err,cap,"RULE_MISSING",(*source)->id,key);
    if(!grid_rule_matches(*rule,cell))return grid_rule_error(err,cap,"SELECTOR_MISS",(*source)->id,key);
    Coord ends[2][2];
    for(int a=0;a<2;++a)if(cell[a]==INT64_MAX || !grid_lattice_coord(derived,a,cell[a],&ends[a][0]) ||
        !grid_lattice_coord(derived,a,cell[a]+1,&ends[a][1]))return grid_rule_error(err,cap,"CELL_RANGE",(*source)->id,key);
    *bounds=(SurfaceRegion2){ends[0][0],ends[1][0],ends[0][1],ends[1][1]};return true;
}
static bool grid_rule_line(const World *w,const GridRuleLineRef *ref,SurfaceId pid,Coord *coordinate,
    SurfaceRegion2 *scope,char *err,size_t cap)
{
    ReferenceGrid derived;const GridSystem *s;const GridSubdivisionRule *r;SurfaceRegion2 cell;
    PlacementSurface placement_storage;SpaceBoundarySurface boundary_storage;
    const PlacementSurface *p;const SpaceBoundarySurface *b;
    if(!grid_rule_cell(w,"grid",ref->grid_id,ref->rule_key,ref->cell,&derived,&s,&r,&cell,&p,&b,&placement_storage,&boundary_storage,err,cap))return false;
    if(s->id!=ref->system_id || !p || p->id!=pid)return grid_rule_error(err,cap,"WRONG_SOURCE",ref->system_id,ref->rule_key);
    if(ref->axis<0 || ref->axis>1 || ref->inner_index>=r->divisions[ref->axis]-1)
        return grid_rule_error(err,cap,"INDEX_RANGE",s->id,r->key);
    Coord lo=ref->axis?cell.min_v:cell.min_u,pitch=grid_axis_pitch(&s->axis[ref->axis]);
    if(coordinate)*coordinate=lo+(Coord)(ref->inner_index+1)*(pitch/r->divisions[ref->axis]);
    if(scope)*scope=cell;return true;
}

static bool apply_grid_source_rule(const char *path,int line_no,char **t,int count,World *w)
{
    if(g_parsing_scene_file)g_rule_scene_encountered=true;
    uint32_t sid,key=0;int at=3;bool create=false,remove=false;GridSubdivisionRule r={0};char err[256]="";
    if(count<4 || !parse_u32(t[1],&sid))goto invalid;
    const GridSystem *old=world_find_grid_system(w,sid);if(!old){scene_error(path,line_no,"I25a: WRONG_SOURCE");return false;}
    if(!strcmp(t[2],"create")){create=true;if(g_parsing_scene_file || !old->next_rule_key){scene_error(path,line_no,"I25a: RULE_KEY_EXHAUSTED or create in scene");return false;}key=old->next_rule_key;}
    else if(!strcmp(t[2],"key") || !strcmp(t[2],"delete")){
        remove=!strcmp(t[2],"delete");if(!parse_u32(t[3],&key) || !key)goto invalid;at=4;
    }else goto invalid;
    const GridSubdivisionRule *existing=grid_rule_find(old,key);
    if((remove || (!create && !g_parsing_scene_file)) && !existing){scene_error(path,line_no,"I25a: RULE_MISSING");return false;}
    size_t source_slot=(size_t)(old-geo_grid_systems_values(&w->grid_store));
    if(g_parsing_scene_file && g_rule_scene_highwater[source_slot]){scene_error(path,line_no,"I25a: HIGHWATER must follow all rule declarations");return false;}
    if(g_parsing_scene_file && existing){scene_error(path,line_no,"I25a: duplicate RULE_KEY");return false;}
    if(remove){if(count!=4 || g_parsing_scene_file)goto invalid;}
    else{
        r.key=key;
        if(at+3>=count || strcmp(t[at],"name-hex") || !grid_system_read_name(t[at+1],r.name) || strcmp(t[at+2],"selector"))goto invalid;
        at+=3;
        if(!strcmp(t[at],"all-cells")){r.all_cells=true;++at;}
        else if(!strcmp(t[at],"cell") && at+2<count){if(!parse_i64(t[at+1],&r.cell[0]) || !parse_i64(t[at+2],&r.cell[1])){scene_error(path,line_no,"I25a: CELL_RANGE signed int64 required");return false;}at+=3;}
        else goto invalid;
        uint32_t u,v;
        if(at+3!=count || strcmp(t[at],"divide") || !parse_u32(t[at+1],&u) || !parse_u32(t[at+2],&v))goto invalid;
        r.divisions[0]=u;r.divisions[1]=v;
    }
    if(existing && grid_rule_used(w,sid,key) && (remove || r.all_cells!=existing->all_cells ||
        memcmp(r.cell,existing->cell,sizeof r.cell) || memcmp(r.divisions,existing->divisions,sizeof r.divisions))){
        grid_rule_error(err,sizeof err,"RULE_REFERENCED",sid,key);scene_error(path,line_no,err);return false;
    }
    World candidate=*w;GridSystem definition=*old,*s=&definition;
    size_t slot=0;while(slot<s->rule_count && s->rules[slot].key!=key)++slot;
    if(remove){memmove(s->rules+slot,s->rules+slot+1,(s->rule_count-slot-1)*sizeof r);memset(&s->rules[--s->rule_count],0,sizeof r);}
    else{
        if(slot==s->rule_count){if(slot==GRID_MAX_SUBDIVISION_RULES){scene_error(path,line_no,"I25a: RULE_CAPACITY");return false;}++s->rule_count;}
        s->rules[slot]=r;
        if(create || (g_parsing_scene_file && s->next_rule_key && key>=s->next_rule_key))s->next_rule_key=key==UINT32_MAX?0:key+1;
    }
    if(!app_grid_system_put(&candidate,s,app_grid_system_main_along(w,sid)))goto invalid;
    reference_capture_trial(&candidate);
    if(!app_world_revalidate_staged(w,&candidate)){scene_error(path,line_no,g_revalidate_error);return false;}
    return true;
invalid:
    scene_error(path,line_no,"I25a: RULE_SYNTAX requires integer divisions and valid source selector/name");return false;
}
static bool apply_grid_source_rule_highwater(const char *path,int line_no,char **t,int count,World *w)
{
    if(g_parsing_scene_file)g_rule_scene_encountered=true;
    uint32_t sid,next;
    if(!g_parsing_scene_file || count!=4 || !parse_u32(t[1],&sid) || strcmp(t[2],"next") ||
        (strcmp(t[3],"exhausted") && (!parse_u32(t[3],&next) || !next))){scene_error(path,line_no,"I25a: HIGHWATER replay-only declaration");return false;}
    if(!strcmp(t[3],"exhausted"))next=0;
    size_t slot=0;while(slot<geo_grid_systems_count(&w->grid_store) && (*geo_grid_systems_at(&w->grid_store,slot)).id!=sid)++slot;
    if(slot==geo_grid_systems_count(&w->grid_store) || g_rule_scene_highwater[slot] ||
        (!(*geo_grid_systems_at(&w->grid_store,slot)).next_rule_key && next) ||
        (next && next<(*geo_grid_systems_at(&w->grid_store,slot)).next_rule_key)){scene_error(path,line_no,"I25a: invalid HIGHWATER closure");return false;}
    GridSystem definition=*geo_grid_systems_at(&w->grid_store,slot);definition.next_rule_key=next;
    if(!app_grid_system_put(w,&definition,app_grid_system_main_along(w,sid)))return false;
    g_rule_scene_highwater[slot]=true;return true;
}
static bool grid_subdivision_used(const World *w)
{
    for(size_t i=0;i<geo_grid_systems_count(&w->grid_store);++i)if((*geo_grid_systems_at(&w->grid_store,i)).rule_count || (*geo_grid_systems_at(&w->grid_store,i)).next_rule_key!=1)return true;
    for(size_t i=0;i<geo_guides_count(&w->guide_lines);++i)if(strstr(app_guide_expression(w,geo_guides_values(&w->guide_lines)[i].id),"gridrule:"))return true;
    for(size_t i=0;i<w->timber_count;++i)if(w->timbers[i].placed && w->anchors[i].anchor_kind==ANCHOR_AT_RULE)return true;
    return false;
}
static bool grid_rules_scene_integrity(const World *w)
{
    if(g_rule_scene_encountered && !g_rule_scene_required)return false;
    if(!grid_subdivision_used(w))return true;
    if(!g_rule_scene_required)return false;
    for(size_t i=0;i<geo_grid_systems_count(&w->grid_store);++i)if(((*geo_grid_systems_at(&w->grid_store,i)).rule_count || (*geo_grid_systems_at(&w->grid_store,i)).next_rule_key!=1) && !g_rule_scene_highwater[i])return false;
    return true;
}
static void grid_rules_dump(const GridSystem *s,FILE *out)
{
    if(!s->rule_count && s->next_rule_key==1)return;
    for(size_t i=0;i<s->rule_count;++i){const GridSubdivisionRule *r=&s->rules[i];
        fprintf(out,"grid-source-rule %u key %u name-hex ",s->id,r->key);
        for(size_t j=0;r->name[j];++j)fprintf(out,"%02x",(unsigned char)r->name[j]);
        if(r->all_cells)fputs(" selector all-cells",out);
        else fprintf(out," selector cell %lld %lld",(long long)r->cell[0],(long long)r->cell[1]);
        fprintf(out," divide %u %u\n",r->divisions[0],r->divisions[1]);
    }
    fprintf(out,"grid-source-rule-highwater %u next ",s->id);
    if(s->next_rule_key)fprintf(out,"%u\n",s->next_rule_key);else fputs("exhausted\n",out);
}
