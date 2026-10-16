/* H: legacy placement encoding and storage callbacks; W owns D34/I42/R35. */
static bool g_assembly_replay;
static bool app_assembly_replaying(void){return g_assembly_replay;}
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
    for(int k=0;k<2;++k)a.between[k]=(ReferenceFace){1,-1,0,d->between[k]};return a;
}
static void app_asm_write(void *user,const WoodMember *value,const WoodAssemblyDefinition *d)
{World *w=(World *)user;int i=reference_timber_index(w,value->id);TimberAnchor a=app_asm_anchor(d);a.order=w->wood.anchors[i].order;if(!a.order)a.order=++w->app.next_order;w->wood.timbers[i]=*value;w->wood.anchors[i]=a;}
static bool app_asm_anchor_matches(void *user,uint32_t id,const WoodAssemblyDefinition *d)
{World *w=(World *)user;int i=reference_timber_index(w,id);TimberAnchor actual=w->wood.anchors[i],expected=app_asm_anchor(d);actual.uv=(SurfacePoint2){0};actual.order=0;return !memcmp(&actual,&expected,sizeof actual);}
static bool app_asm_instance_content(void *user,AsmInstance *a,GeoJson *j,int source)
{
    (void)user;char value[ASM_RECORD_MAX],text[ASM_RECORD_MAX];if(!geo_json_canonical(j,source,value,sizeof value))return false;
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
    (void)kind;for(size_t i=0;i<w->wood.assembly.owner_count;++i)if(w->wood.assembly.owners[i].timber==id){const AsmOwner *o=&w->wood.assembly.owners[i];fprintf(out,"owned %u %u ",o->instance,o->member);return;}
}
static bool apply_assembly_owned_line(const char *path,int line_no,char **t,int count,World *w)
{
    uint32_t inst,member,id;if(!g_parsing_scene_file||!w->wood.assembly.generation_required||count<6||!parse_u32(t[1],&inst)||!inst||!parse_u32(t[2],&member)||!member||!parse_u32(t[4],&id)||!id){scene_error(path,line_no,"I42: owned records require atomic generation scene and positive identities");return false;}
    bool timber=!strcmp(t[3],"timber"),place=!strcmp(t[3],"place");if(!timber&&!place)return false;
    if(timber){if(w->wood.assembly.owner_count==ASM_INSTANCE_MAX*3||reference_timber_index(w,id)>=0)return false;w->wood.assembly.owners[w->wood.assembly.owner_count++]=(AsmOwner){id,inst,member};}
    else {bool found=false;for(size_t i=0;i<w->wood.assembly.owner_count;++i){AsmOwner *o=&w->wood.assembly.owners[i];if(o->timber==id&&o->instance==inst&&o->member==member)found=true;}if(!found)return false;}
    g_assembly_replay=true;bool ok=timber?apply_timber_line(path,line_no,t+3,count-3,w):apply_reference_place(path,line_no,t+3,count-3,w);g_assembly_replay=false;if(!ok)scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I42: invalid owned record");return ok;
}
