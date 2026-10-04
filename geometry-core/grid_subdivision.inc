/* D19a/I25a/R32: source-owned rules; one authoritative cell evaluator. */
static bool g_rule_scene_highwater[WORLD_MAX_GRID_SYSTEMS];
static bool g_rule_scene_required;

static const GridSubdivisionRule *grid_rule_find(const GridSystem *s,uint32_t key)
{
    if(s)for(size_t i=0;i<s->rule_count;++i)if(s->rules[i].key==key)return &s->rules[i];
    return NULL;
}
static bool grid_rule_error(char *err,size_t cap,const char *code,uint32_t sid,uint32_t key)
{
    if(err)snprintf(err,cap,"I25a: %s source %u rule %u",code,sid,key);
    return false;
}
static bool grid_rules_valid(const GridSystem *s,char *err,size_t cap)
{
    if(s->rule_count>GRID_MAX_SUBDIVISION_RULES)return grid_rule_error(err,cap,"RULE_CAPACITY",s->id,0);
    if(!s->rule_count)return true;
    for(int a=0;a<2;++a)if(!grid_axis_is_infinite(&s->axis[a]) || s->axis[a].stagger_set)
        return grid_rule_error(err,cap,"SOURCE_KIND",s->id,0);
    for(size_t i=0;i<s->rule_count;++i){
        const GridSubdivisionRule *r=&s->rules[i];
        if(!r->key || (s->next_rule_key && r->key>=s->next_rule_key))
            return grid_rule_error(err,cap,"RULE_KEY",s->id,r->key);
        size_t n=strlen(r->name);
        if(!grid_system_name_valid((const unsigned char*)r->name,n))return grid_rule_error(err,cap,"RULE_NAME",s->id,r->key);
        if(r->divisions[0]<1 || r->divisions[1]<1 || r->divisions[0]>65 || r->divisions[1]>65 ||
            (r->divisions[0]==1 && r->divisions[1]==1))return grid_rule_error(err,cap,"DIVISION_RANGE",s->id,r->key);
        for(int a=0;a<2;++a)if(grid_axis_pitch(&s->axis[a])%r->divisions[a])
            return grid_rule_error(err,cap,"DIVISION_NOT_EXACT",s->id,r->key);
        if(!r->all_cells && (r->cell[0]==INT64_MAX || r->cell[1]==INT64_MAX))
            return grid_rule_error(err,cap,"CELL_RANGE",s->id,r->key);
        for(size_t j=0;j<i;++j){
            const GridSubdivisionRule *q=&s->rules[j];
            if(q->key==r->key)return grid_rule_error(err,cap,"RULE_KEY",s->id,r->key);
            if(q->all_cells || r->all_cells || (q->cell[0]==r->cell[0] && q->cell[1]==r->cell[1])){
                if(err)snprintf(err,cap,"I25a: RULE_OVERLAP source %u rules %u/%u",s->id,q->key,r->key);
                return false;
            }
        }
    }
    return true;
}
static bool grid_rule_matches(const GridSubdivisionRule *r,const int64_t cell[2])
{return r->all_cells || (r->cell[0]==cell[0] && r->cell[1]==cell[1]);}

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
    for(size_t i=0;i<w->guide_count;++i)if(grid_rule_expression_uses(w->guides[i].expression,sid,key))return true;
    for(size_t i=0;i<w->timber_count;++i){const TimberAnchor *a=&w->anchors[i];
        if(w->timbers[i].placed && a->anchor_kind==ANCHOR_AT_RULE && a->ref_rule.system_id==sid && a->ref_rule.rule_key==key)return true;
    }
    return false;
}
static bool grid_rules_world_valid(const World *w,char *err,size_t cap)
{
    if(g_subgrid_before)for(size_t i=0;i<g_subgrid_before->grid_system_count;++i){
        const GridSystem *old=&g_subgrid_before->grid_systems[i],*now=world_find_grid_system(w,old->id);
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

static bool grid_rule_target(const World *w,const char *kind,uint32_t id,ReferenceGrid *derived,
    const GridSystem **source,const PlacementSurface **placement,const SpaceBoundarySurface **boundary,char *err,size_t cap)
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
            *placement=world_find_placement(w,g->placement_id);
            if(!*placement)return grid_rule_error(err,cap,"WRONG_SOURCE",0,0);
        }
        if(!binding || !grid_binding_cache(w,binding,derived,err,cap))return false;
        *source=world_find_grid_system(w,binding->system_id);
        *boundary=*placement?world_placement_boundary(w,*placement):world_find_boundary(w,binding->boundary_id);
    }
    if(!*source || !grid_axis_is_infinite(&(*source)->axis[0]) || !grid_axis_is_infinite(&(*source)->axis[1]) ||
        (*source)->axis[0].stagger_set || (*source)->axis[1].stagger_set)return grid_rule_error(err,cap,"SOURCE_KIND",*source?(*source)->id:0,0);
    return true;
}
static bool grid_rule_cell(const World *w,const char *kind,uint32_t id,uint32_t key,const int64_t cell[2],
    ReferenceGrid *derived,const GridSystem **source,const GridSubdivisionRule **rule,SurfaceRegion2 *bounds,
    const PlacementSurface **placement,const SpaceBoundarySurface **boundary,char *err,size_t cap)
{
    if(!grid_rule_target(w,kind,id,derived,source,placement,boundary,err,cap))return false;
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
    const PlacementSurface *p;const SpaceBoundarySurface *b;
    if(!grid_rule_cell(w,"grid",ref->grid_id,ref->rule_key,ref->cell,&derived,&s,&r,&cell,&p,&b,err,cap))return false;
    if(s->id!=ref->system_id || !p || p->id!=pid)return grid_rule_error(err,cap,"WRONG_SOURCE",ref->system_id,ref->rule_key);
    if(ref->axis<0 || ref->axis>1 || ref->inner_index>=r->divisions[ref->axis]-1)
        return grid_rule_error(err,cap,"INDEX_RANGE",s->id,r->key);
    Coord lo=ref->axis?cell.min_v:cell.min_u,pitch=grid_axis_pitch(&s->axis[ref->axis]);
    if(coordinate)*coordinate=lo+(Coord)(ref->inner_index+1)*(pitch/r->divisions[ref->axis]);
    if(scope)*scope=cell;return true;
}

static bool apply_grid_source_rule(const char *path,int line_no,char **t,int count,World *w)
{
    uint32_t sid,key=0;int at=3;bool create=false,remove=false;GridSubdivisionRule r={0};char err[256]="";
    if(count<4 || !parse_u32(t[1],&sid))goto invalid;
    const GridSystem *old=world_find_grid_system(w,sid);if(!old){scene_error(path,line_no,"I25a: WRONG_SOURCE");return false;}
    if(!strcmp(t[2],"create")){create=true;if(g_parsing_scene_file || !old->next_rule_key){scene_error(path,line_no,"I25a: RULE_KEY_EXHAUSTED or create in scene");return false;}key=old->next_rule_key;}
    else if(!strcmp(t[2],"key") || !strcmp(t[2],"delete")){
        remove=!strcmp(t[2],"delete");if(!parse_u32(t[3],&key) || !key)goto invalid;at=4;
    }else goto invalid;
    const GridSubdivisionRule *existing=grid_rule_find(old,key);
    if((remove || (!create && !g_parsing_scene_file)) && !existing){scene_error(path,line_no,"I25a: RULE_MISSING");return false;}
    size_t source_slot=(size_t)(old-w->grid_systems);
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
    World candidate=*w;GridSystem *s=NULL;
    for(size_t i=0;i<candidate.grid_system_count;++i)if(candidate.grid_systems[i].id==sid)s=&candidate.grid_systems[i];
    size_t slot=0;while(slot<s->rule_count && s->rules[slot].key!=key)++slot;
    if(remove){memmove(s->rules+slot,s->rules+slot+1,(s->rule_count-slot-1)*sizeof r);memset(&s->rules[--s->rule_count],0,sizeof r);}
    else{
        if(slot==s->rule_count){if(slot==GRID_MAX_SUBDIVISION_RULES){scene_error(path,line_no,"I25a: RULE_CAPACITY");return false;}++s->rule_count;}
        s->rules[slot]=r;
        if(create || (g_parsing_scene_file && s->next_rule_key && key>=s->next_rule_key))s->next_rule_key=key==UINT32_MAX?0:key+1;
    }
    reference_capture_trial(&candidate);
    if(!world_revalidate(&candidate)){scene_error(path,line_no,g_revalidate_error);return false;}
    *w=candidate;return true;
invalid:
    scene_error(path,line_no,"I25a: RULE_SYNTAX requires integer divisions and valid source selector/name");return false;
}
static bool apply_grid_source_rule_highwater(const char *path,int line_no,char **t,int count,World *w)
{
    uint32_t sid,next;
    if(!g_parsing_scene_file || count!=4 || !parse_u32(t[1],&sid) || strcmp(t[2],"next") ||
        (strcmp(t[3],"exhausted") && (!parse_u32(t[3],&next) || !next))){scene_error(path,line_no,"I25a: HIGHWATER replay-only declaration");return false;}
    if(!strcmp(t[3],"exhausted"))next=0;
    size_t slot=0;while(slot<w->grid_system_count && w->grid_systems[slot].id!=sid)++slot;
    if(slot==w->grid_system_count || g_rule_scene_highwater[slot] ||
        (!w->grid_systems[slot].next_rule_key && next) ||
        (next && next<w->grid_systems[slot].next_rule_key)){scene_error(path,line_no,"I25a: invalid HIGHWATER closure");return false;}
    w->grid_systems[slot].next_rule_key=next;g_rule_scene_highwater[slot]=true;return true;
}
static bool grid_subdivision_used(const World *w)
{
    for(size_t i=0;i<w->grid_system_count;++i)if(w->grid_systems[i].rule_count || w->grid_systems[i].next_rule_key!=1)return true;
    for(size_t i=0;i<w->guide_count;++i)if(strstr(w->guides[i].expression,"gridrule:"))return true;
    for(size_t i=0;i<w->timber_count;++i)if(w->timbers[i].placed && w->anchors[i].anchor_kind==ANCHOR_AT_RULE)return true;
    return false;
}
static bool grid_rules_scene_integrity(const World *w)
{
    if(!grid_subdivision_used(w))return true;
    if(!g_rule_scene_required)return false;
    for(size_t i=0;i<w->grid_system_count;++i)if((w->grid_systems[i].rule_count || w->grid_systems[i].next_rule_key!=1) && !g_rule_scene_highwater[i])return false;
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
