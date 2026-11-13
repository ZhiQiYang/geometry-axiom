/* H: legacy placement encoding and storage callbacks; W owns D34/I42/R35. */
static bool g_assembly_replay;
static bool app_assembly_replaying(void){return g_assembly_replay;}
/* Owned scene records precede their assembly blocks. Until the owning instance
 * record loads, the saved dimensions are the only ones: neither literal nor yet
 * resolvable from assembly sources. EOF integrity rejects an owner that never
 * gains its instance; EOF revalidation then resolves every owned dimension. */
static bool app_assembly_saved_dimensions(const World *w,uint32_t id)
{
    if(g_assembly_replay)return true;if(!g_parsing_scene_file)return false;
    for(size_t i=0;i<w->wood.assembly.owner_count;++i){const AsmOwner *o=&w->wood.assembly.owners[i];if(o->timber!=id)continue;
        for(size_t k=0;k<w->wood.assembly.instance_count;++k)if(w->wood.assembly.instances[k].id==o->instance)return false;
        return true;}
    return false;
}
static bool app_asm_surface(void *user,uint32_t id)
{return world_find_placement((World *)user,id)!=NULL;}
static bool app_asm_guide(void *user,uint32_t id,WoodAssemblyGuide *out)
{
    World *w=(World *)user;for(size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i){const GuideLine *g=&geo_guides_values(&w->geo.guide_lines)[i];if(g->id==id){out->surface_id=g->placement_id;out->direction=g->direction==GUIDE_ALONG_U?ASM_DIR_U:g->direction==GUIDE_ALONG_V?ASM_DIR_V:0;return true;}}return false;
}
static bool app_asm_member(void *user,uint32_t id,WoodAssemblyMember *out)
{
    World *w=(World *)user;int i=reference_timber_index(w,id);if(i<0)return false;
    if(out){const Timber *t=&w->wood.timbers[i];*out=(WoodAssemblyMember){w->wood.anchors[i].placement_id,t->role,t->size_a,t->size_b,t->placed};}return true;
}
static bool app_asm_footprint(void *user,uint32_t surface,uint32_t id,GeoRect2 *out)
{World *w=(World *)user;const PlacementSurface *p=world_find_placement(w,surface);int i=reference_timber_index(w,id);return p&&i>=0&&timber_a0_footprint_uv(p,&w->wood.timbers[i],&w->wood.anchors[i],out);}
static size_t app_asm_member_count(void *user){return ((World *)user)->wood.timber_count;}
static void app_asm_allocate(void *user,uint32_t id)
{
    World *w=(World *)user;Timber *t=&w->wood.timbers[w->wood.timber_count];memset(t,0,sizeof *t);t->id=id;memset(&w->wood.anchors[w->wood.timber_count],0,sizeof(TimberAnchor));w->wood.anchors[w->wood.timber_count++].order=++w->app.next_order;
}
static bool app_asm_remove(void *user,uint32_t id)
{
    World *w=(World *)user;int i=reference_timber_index(w,id);if(i<0)return false;memmove(&w->wood.timbers[i],&w->wood.timbers[i+1],(w->wood.timber_count-i-1)*sizeof(Timber));memmove(&w->wood.anchors[i],&w->wood.anchors[i+1],(w->wood.timber_count-i-1)*sizeof(TimberAnchor));memset(&w->wood.timbers[--w->wood.timber_count],0,sizeof(Timber));memset(&w->wood.anchors[w->wood.timber_count],0,sizeof(TimberAnchor));return true;
}
static TimberAnchor app_asm_anchor(const WoodAssemblyDefinition *d)
{
    TimberAnchor a;memset(&a,0,sizeof a);a.placement_id=d->surface_id;a.ref_hole=-1;a.anchor_kind=ANCHOR_AT_LINE;a.span_mode=SPAN_AUTO;a.ref_guide=d->guide_id;a.has_between=true;a.length_direction=d->direction==ASM_DIR_U?SURFACE_DIRECTION_POS_U:SURFACE_DIRECTION_POS_V;a.depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
    if(d->at.kind==ASM_AT_GRID){a.anchor_kind=ANCHOR_AT_GRID;a.ref_guide=0;a.ref_grid=d->at.id;a.ref_grid_axis=d->at.axis;a.ref_grid_index=d->at.index;}
    else if(d->at.kind==ASM_AT_OUTLINE){a.anchor_kind=ANCHOR_AT_EDGE;a.ref_guide=0;a.ref_edge=d->at.edge;memcpy(a.ref_derived_key,d->at.edge_key,sizeof a.ref_derived_key);}
    for(int k=0;k<2;++k)a.between[k]=(ReferenceFace){1,-1,0,d->between[k]};return a;
}
static void app_asm_write(void *user,const WoodMember *value,const WoodAssemblyDefinition *d)
{World *w=(World *)user;int i=reference_timber_index(w,value->id);TimberAnchor a=app_asm_anchor(d);a.order=w->wood.anchors[i].order;if(!a.order)a.order=++w->app.next_order;w->wood.timbers[i]=*value;w->wood.anchors[i]=a;}
static bool app_asm_anchor_matches(void *user,uint32_t id,const WoodAssemblyDefinition *d)
{World *w=(World *)user;int i=reference_timber_index(w,id);TimberAnchor actual=w->wood.anchors[i],expected=app_asm_anchor(d);actual.uv=(SurfacePoint2){0};actual.order=0;return !memcmp(&actual,&expected,sizeof actual);}
static bool app_asm_instance_content(void *user,AsmInstance *a,GeoJson *j,int source)
{
    (void)user;char value[ASM_RECORD_MAX],text[ASM_RECORD_MAX];if(!geo_json_canonical(j,source,value,sizeof value))return false;
    if(a->bay_repeat){int n=snprintf(text,sizeof text,"{\"source\":%s,\"mapping\":[",value);if(n<0||(size_t)n>=sizeof text)return false;size_t used=(size_t)n;
        for(size_t i=0;i<a->mapping_count;++i){const AsmMapping *m=&a->mapping[i];
            if(m->identity.kind==ASM_ID_PRIMARY)n=snprintf(text+used,sizeof text-used,"%s{\"primary\":%u,\"timberId\":%u}",i?",":"",m->identity.key,m->timber);
            else n=snprintf(text+used,sizeof text-used,"%s{\"secondary\":{\"line\":%u,\"left\":%u,\"right\":%u},\"timberId\":%u}",i?",":"",m->identity.key,m->identity.left,m->identity.right,m->timber);
            if(n<0||(size_t)n>=sizeof text-used)return false;used+=(size_t)n;}
        if(used+3>sizeof text)return false;memcpy(text+used,"]}",3);GeoJson q;bool ok=app_json_parse(&q,text)&&geo_json_canonical(&q,0,a->content,sizeof a->content);geo_json_free(&q);return ok;}
    int n=snprintf(text,sizeof text,"{\"source\":%s,\"mapping\":[{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u}]}",value,a->member[0],a->timber[0],a->member[1],a->timber[1],a->member[2],a->timber[2]);
    if(n<0||(size_t)n>=sizeof text)return asm_error("CAPACITY: instance exceeds 8191 bytes");GeoJson q;bool ok=app_json_parse(&q,text)&&geo_json_canonical(&q,0,a->content,sizeof a->content);geo_json_free(&q);return ok;
}
static AsmInstance *assembly_instance(World *w,uint32_t id)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_instance(&c,id);}
static bool assembly_owned(const World *w,uint32_t id)
{if(g_assembly_replay)return false;WoodAssemblyContext c=app_asm_context(w);return wood_assembly_owned(&c,id);}
static bool assembly_generation_integrity(const World *w)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_generation_integrity(&c);}
static bool assembly_generation_prepare(World *w)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_generation_prepare(&c);}
static bool assembly_generation_check(const World *w)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_generation_check(&c);}
static bool asm_generation_operation(World *w,GeoJson *j,int t)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_generation_operation(&c,j,t);}
static bool asm_instance_load(World *w,GeoJson *j,int t)
{WoodAssemblyContext c=app_asm_context(w);return wood_assembly_instance_load(&c,j,t);}
static void assembly_owned_prefix(const World *w,uint32_t id,const char *kind,FILE *out)
{
    (void)kind;for(size_t i=0;i<w->wood.assembly.owner_count;++i)if(w->wood.assembly.owners[i].timber==id){const AsmOwner *o=&w->wood.assembly.owners[i];
        if(o->kind==ASM_ID_PRIMARY)fprintf(out,"owned %u bay-primary %u ",o->instance,o->member);
        else if(o->kind==ASM_ID_SECONDARY)fprintf(out,"owned %u bay-secondary %u %u %u ",o->instance,o->member,o->left,o->right);
        else fprintf(out,"owned %u %u ",o->instance,o->member);return;}
}
static bool apply_assembly_owned_line(const char *path,int line_no,char **t,int count,World *w)
{
    if(count>2&&(!strcmp(t[2],"bay-primary")||!strcmp(t[2],"bay-secondary"))){AsmOwner owner={0};int offset=!strcmp(t[2],"bay-primary")?4:6;owner.kind=offset==4?ASM_ID_PRIMARY:ASM_ID_SECONDARY;
        if(!g_parsing_scene_file||!w->wood.assembly.generation_required||!w->wood.assembly.bay_required||count<offset+3||!parse_u32(t[1],&owner.instance)||!owner.instance||!parse_u32(t[3],&owner.member)||!owner.member||!parse_u32(t[offset+1],&owner.timber)||!owner.timber||
           (offset==6&&(!parse_u32(t[4],&owner.left)||!owner.left||!parse_u32(t[5],&owner.right)||!owner.right||owner.left==owner.right))){scene_error(path,line_no,"I69: repeat owned records require both capabilities and positive identities");return false;}
        bool timber=!strcmp(t[offset],"timber"),place=!strcmp(t[offset],"place");if(!timber&&!place)return false;
        if(timber){if(w->wood.assembly.owner_count>=ASM_OWNER_MAX||reference_timber_index(w,owner.timber)>=0)return false;w->wood.assembly.owners[w->wood.assembly.owner_count++]=owner;}
        else{bool found=false;for(size_t i=0;i<w->wood.assembly.owner_count;++i){const AsmOwner *saved=&w->wood.assembly.owners[i];if(saved->timber==owner.timber&&saved->instance==owner.instance&&wood_assembly_identity_equal(wood_assembly_owner_identity(saved),wood_assembly_owner_identity(&owner)))found=true;}if(!found)return false;}
        g_assembly_replay=true;bool ok=timber?apply_timber_line(path,line_no,t+offset,count-offset,w):apply_reference_place(path,line_no,t+offset,count-offset,w);g_assembly_replay=false;if(!ok)scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I69: invalid repeat owned record");return ok;
    }
    uint32_t inst,member,id;if(!g_parsing_scene_file||!w->wood.assembly.generation_required||count<6||!parse_u32(t[1],&inst)||!inst||!parse_u32(t[2],&member)||!member||!parse_u32(t[4],&id)||!id){scene_error(path,line_no,"I42: owned records require atomic generation scene and positive identities");return false;}
    bool timber=!strcmp(t[3],"timber"),place=!strcmp(t[3],"place");if(!timber&&!place)return false;
    if(timber){if(w->wood.assembly.owner_count==ASM_INSTANCE_MAX*3||reference_timber_index(w,id)>=0)return false;w->wood.assembly.owners[w->wood.assembly.owner_count++]=(AsmOwner){id,inst,member};}
    else {bool found=false;for(size_t i=0;i<w->wood.assembly.owner_count;++i){AsmOwner *o=&w->wood.assembly.owners[i];if(o->timber==id&&o->instance==inst&&o->member==member)found=true;}if(!found)return false;}
    g_assembly_replay=true;bool ok=timber?apply_timber_line(path,line_no,t+3,count-3,w):apply_reference_place(path,line_no,t+3,count-3,w);g_assembly_replay=false;if(!ok)scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I42: invalid owned record");return ok;
}
/* R55 planning owns a disposable source graph. The ordinary candidate graph
 * starts afterwards, over the final identity set; no cached deleted member or
 * provisional mapping can become a source of the published candidate. */
static bool assembly_bay_prepare(World *w)
{
    bool repeat=false;for(size_t i=0;i<w->wood.assembly.instance_count;++i)repeat|=w->wood.assembly.instances[i].bay_repeat;if(!repeat)return true;
    if(g_active_app_candidate&&w==&g_active_app_candidate->after){g_active_app_candidate->bay_report.cell_count=0;g_active_app_candidate->bay_report.primary_count=0;}
    size_t previous_issues=g_reference_issue_count;
    char previous_error[sizeof g_revalidate_error],previous_engineering[sizeof g_engineering_error];
    memcpy(previous_error,g_revalidate_error,sizeof previous_error);memcpy(previous_engineering,g_engineering_error,sizeof previous_engineering);
    ReferenceEval ctx={0};ctx.world=w;ctx.bay_planning=true;
    uint32_t original_ids[WORLD_MAX_TIMBERS];bool original_placed[WORLD_MAX_TIMBERS];size_t original_count=w->wood.timber_count;
    for(size_t i=0;i<original_count;++i){original_ids[i]=w->wood.timbers[i].id;original_placed[i]=ctx.wanted[i]=w->wood.timbers[i].placed;}
    if(!reference_sources_ensure(&ctx)){reference_sources_dispose(&ctx);return asm_error("CAPACITY: cannot allocate repeat planning sources");}
    WoodAssemblyContext assembly=app_asm_context(w);assembly.evaluation=NULL;reference_assembly_context(&ctx,&assembly);
    size_t previous_bay_issues=assembly.bay_report?assembly.bay_report->issue_count:0;
    for(size_t i=0;i<original_count;++i)w->wood.timbers[i].placed=false;
    bool ok=wood_assembly_sources_bind(ctx.assembly_sources,&assembly)&&wood_assembly_bay_prepare(&assembly);
    for(size_t i=0;i<original_count;++i){int at=reference_timber_index(w,original_ids[i]);if(at>=0)w->wood.timbers[at].placed=original_placed[i];}
    /* Evaluate-before probes are not support dependency edges. Their old-cell
     * diagnostics cannot survive into the formal, minus-deleted evaluation. */
    if(ok){g_reference_issue_count=previous_issues;memcpy(g_revalidate_error,previous_error,sizeof previous_error);memcpy(g_engineering_error,previous_engineering,sizeof previous_engineering);if(assembly.bay_report)assembly.bay_report->issue_count=previous_bay_issues;}
    reference_sources_dispose(&ctx);return ok;
}
static bool app_asm_position(void *user,uint32_t surface,const AsmLocation *at,WoodAssemblyPosition *out)
{ReferenceEval ctx={0};ctx.world=user;ctx.use_current_values=true;return reference_asm_position(&ctx,surface,at,out);}
static bool app_asm_dependencies(void *user,WoodAssemblyDependency node,WoodAssemblyDependency *out,size_t cap,size_t *count,bool selected)
{ReferenceEval ctx={0};ctx.world=user;ctx.use_current_values=true;return reference_asm_dependencies(&ctx,node,out,cap,count,selected);}
static bool app_asm_external_reference(void *user,uint32_t instance,uint32_t timber,char *out,size_t cap)
{ReferenceEval ctx={0};ctx.world=user;ctx.use_current_values=true;return reference_asm_external_reference(&ctx,instance,timber,out,cap);}
