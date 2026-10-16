/* D19a/I25a/R32: source-owned rules; one authoritative cell evaluator. */
static bool g_rule_scene_highwater[WORLD_MAX_GRID_SYSTEMS];
static bool g_rule_scene_required;
static bool g_rule_scene_encountered;

static const GridSubdivisionRule *grid_rule_find(const GridSystem *s,uint32_t key)
{ return geo_grid_rule_find(s,key); }
static bool grid_rules_valid(const GridSystem *s,char *err,size_t cap)
{ return wood_grid_rules_valid(s,err,cap); }
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
static bool grid_rule_used(const World *w,uint32_t sid,uint32_t key)
{
    WoodGridContext context=app_grid_context(w);
    return wood_grid_rule_used(&context,sid,key);
}
static bool grid_rules_world_valid(const World *w,char *err,size_t cap)
{
    WoodGridContext context=app_grid_context(w),before;
    if(g_subgrid_before){before=app_grid_context(g_subgrid_before);context.before=&before;}
    return wood_grid_rules_world_valid(&context,err,cap);
}

/* Returned DTO pointers borrow caller storage, including component boundaries
 * inside the placement; they must outlive the complete line/cell query. */
static bool grid_rule_target(const World *w,const char *kind,uint32_t id,ReferenceGrid *derived,
    const GridSystem **source,const PlacementSurface **placement,const SpaceBoundarySurface **boundary,
    PlacementSurface *placement_storage,SpaceBoundarySurface *boundary_storage,char *err,size_t cap)
{
    WoodGridContext context=app_grid_context(w);WoodGridRuleTarget target;
    memset(derived,0,sizeof *derived);*source=NULL;*placement=NULL;*boundary=NULL;
    if(!wood_grid_rule_target(&context,kind,id,&target,err,cap))return false;
    *derived=target.derived;*source=target.source;
    if(target.has_placement)*placement=app_placement_read(w,target.placement_id,placement_storage);
    *boundary=*placement?app_placement_boundary(w,*placement,boundary_storage):
        (target.has_boundary?app_boundary_read(w,target.boundary_id,boundary_storage):NULL);
    return true;
}
static bool grid_rule_cell(const World *w,const char *kind,uint32_t id,uint32_t key,const int64_t cell[2],
    ReferenceGrid *derived,const GridSystem **source,const GridSubdivisionRule **rule,SurfaceRegion2 *bounds,
    const PlacementSurface **placement,const SpaceBoundarySurface **boundary,
    PlacementSurface *placement_storage,SpaceBoundarySurface *boundary_storage,char *err,size_t cap)
{
    WoodGridContext context=app_grid_context(w);WoodGridRuleTarget target;
    memset(derived,0,sizeof *derived);*source=NULL;*rule=NULL;*placement=NULL;*boundary=NULL;
    if(!wood_grid_rule_cell(&context,kind,id,key,cell,&target,err,cap))return false;
    *derived=target.derived;*source=target.source;*rule=target.rule;*bounds=target.bounds;
    if(target.has_placement)*placement=app_placement_read(w,target.placement_id,placement_storage);
    *boundary=*placement?app_placement_boundary(w,*placement,boundary_storage):
        (target.has_boundary?app_boundary_read(w,target.boundary_id,boundary_storage):NULL);
    return true;
}
static bool grid_rule_line(const World *w,const GridRuleLineRef *ref,SurfaceId pid,Coord *coordinate,
    SurfaceRegion2 *scope,char *err,size_t cap)
{
    WoodGridContext context=app_grid_context(w);
    return wood_grid_rule_line(&context,ref,pid,coordinate,scope,err,cap);
}

static bool apply_grid_source_rule(const char *path,int line_no,char **t,int count,World *w)
{
    if(g_parsing_scene_file)g_rule_scene_encountered=true;
    uint32_t sid,key=0;int at=3;bool create=false,remove=false;GridSubdivisionRule r={0};char err[256]="";
    if(count<4 || !parse_u32(t[1],&sid))goto invalid;
    const GridSystem *old=world_find_grid_system(w,sid);if(!old){scene_error(path,line_no,"I25a: WRONG_SOURCE");return false;}
    if(!strcmp(t[2],"create"))create=true;
    else if(!strcmp(t[2],"key") || !strcmp(t[2],"delete")){
        remove=!strcmp(t[2],"delete");if(!parse_u32(t[3],&key) || !key)goto invalid;at=4;
    }else goto invalid;
    WoodGridContext context=app_grid_context(w);
    if(!wood_grid_rule_edit_begin(&context,sid,key,create,remove,g_parsing_scene_file,&key,err,sizeof err)){scene_error(path,line_no,err);return false;}
    const GridSubdivisionRule *existing=grid_rule_find(old,key);
    size_t source_slot=(size_t)(old-geo_grid_systems_values(&w->geo.grid_store));
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
    World candidate=*w;WoodGridContext trial=app_grid_context(&candidate);r.key=key;
    if(!wood_grid_rule_edit(&trial,sid,&r,create,remove,g_parsing_scene_file,err,sizeof err)){
        if(!*err)goto invalid;scene_error(path,line_no,err);return false;
    }
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
    size_t slot=0;while(slot<geo_grid_systems_count(&w->geo.grid_store) && (*geo_grid_systems_at(&w->geo.grid_store,slot)).id!=sid)++slot;
    if(slot==geo_grid_systems_count(&w->geo.grid_store) || g_rule_scene_highwater[slot] ||
        (!(*geo_grid_systems_at(&w->geo.grid_store,slot)).next_rule_key && next) ||
        (next && next<(*geo_grid_systems_at(&w->geo.grid_store,slot)).next_rule_key)){scene_error(path,line_no,"I25a: invalid HIGHWATER closure");return false;}
    GridSystem definition=*geo_grid_systems_at(&w->geo.grid_store,slot);definition.next_rule_key=next;
    if(!app_grid_system_put(w,&definition,app_grid_system_main_along(w,sid)))return false;
    g_rule_scene_highwater[slot]=true;return true;
}
static bool grid_subdivision_used(const World *w)
{
    for(size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i)if((*geo_grid_systems_at(&w->geo.grid_store,i)).rule_count || (*geo_grid_systems_at(&w->geo.grid_store,i)).next_rule_key!=1)return true;
    for(size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i)if(strstr(app_guide_expression(w,geo_guides_values(&w->geo.guide_lines)[i].id),"gridrule:"))return true;
    for(size_t i=0;i<w->wood.timber_count;++i)if(w->wood.timbers[i].placed && w->wood.anchors[i].anchor_kind==ANCHOR_AT_RULE)return true;
    return false;
}
static bool grid_rules_scene_integrity(const World *w)
{
    if(g_rule_scene_encountered && !g_rule_scene_required)return false;
    if(!grid_subdivision_used(w))return true;
    if(!g_rule_scene_required)return false;
    for(size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i)if(((*geo_grid_systems_at(&w->geo.grid_store,i)).rule_count || (*geo_grid_systems_at(&w->geo.grid_store,i)).next_rule_key!=1) && !g_rule_scene_highwater[i])return false;
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
