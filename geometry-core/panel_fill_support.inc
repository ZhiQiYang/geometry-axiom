/* Host footprint selection; the W evaluator owns all seam/support policy. */
#define PF_SUPPORT_MAX WOOD_PANEL_SUPPORT_MAX
#define PF_SUPPORT_WORK_MAX WOOD_PANEL_SUPPORT_WORK_MAX
typedef WoodPanelFootprint PfFootprint;
typedef WoodPanelEffectiveSeam PfEffectiveSeam;
typedef WoodPanelSupportPart PfSupportPart;
typedef WoodPanelSupport PfSupport;
static void pf_support_free(PfSupport *s){wood_panel_support_free(s);}
static bool pf_support_footprints(const World *w,const PanelFill *p,PfFootprint *rects,size_t *count)
{
    *count=0;PlacementSurface host_value;const PlacementSurface *host=NULL;
    ReferenceEval *ctx=app_reference_sources_for_world(w);if(ctx&&ctx->use_current_values)ctx=NULL;
    PanelFill fill_definition;FinishSurface finish_definition;
    if(ctx){if(!reference_sources_ensure(ctx)||!wood_finish_sources_fill_definition(ctx->finish_sources,p->id,&fill_definition))return false;p=&fill_definition;}
    for(size_t i=0;i<w->wood.finish_surfaces.host_count;++i){const DerivedPlacement *definition=&w->wood.finish_surfaces.hosts[i];DerivedPlacement returned;
        if(ctx){if(!wood_finish_sources_derived_definition(ctx->finish_sources,definition->id,&returned))return false;definition=&returned;}
        if(definition->fill_id==p->id)host=app_placement_read(w,definition->id,&host_value);
    }
    if(!host)return true;
    const FinishSurface *finish=fs_find(w,p->finish_id);
    if(ctx){if(!wood_finish_sources_surface_definition(ctx->finish_sources,p->finish_id,&finish_definition))return false;finish=&finish_definition;}
    for(size_t i=0;i<w->wood.timber_count;++i){
        if(!w->wood.timbers[i].placed)continue;uint32_t placement=w->wood.anchors[i].placement_id;
        if(ctx){WoodMemberPlacement anchor;if(!wood_definition_sources_placement(ctx->definition_sources,w->wood.timbers[i].id,&anchor))return false;placement=anchor.placement_id;}
        if(placement!=host->id)continue;
        SurfaceRegion2 f;
        bool available=ctx?reference_member_footprint(ctx,i,host->id,&f):timber_a0_footprint_uv(host,&w->wood.timbers[i],&w->wood.anchors[i],&f);
        if(!available)return fs_error("R43: timber %u footprint unavailable",w->wood.timbers[i].id);
        PfFootprint *r=&rects[(*count)++];r->lo[0]=f.min_u;r->hi[0]=f.max_u;
        r->lo[1]=coord_min(finish->side*f.min_v,finish->side*f.max_v);
        r->hi[1]=coord_max(finish->side*f.min_v,finish->side*f.max_v);
    }
    return true;
}
static bool pf_support_evaluate(const PfLayout *d,const PfFootprint *rects,size_t count,GeoQuantity threshold,PfSupport *s)
{
    switch(wood_panel_support_evaluate(&d->layout,rects,count,WORLD_MAX_TIMBERS,threshold,s)){
    case WOOD_PANEL_SUPPORT_OK:return true;
    case WOOD_PANEL_SUPPORT_FOOTPRINT_LIMIT:return fs_capacity_error("I33 CAPACITY: PF-3 footprint limit is %d",WORLD_MAX_TIMBERS);
    case WOOD_PANEL_SUPPORT_WORKSPACE:return fs_capacity_error("I33 CAPACITY: PF-3 workspace unavailable");
    case WOOD_PANEL_SUPPORT_SLAB_LIMIT:return fs_capacity_error("I33 CAPACITY: PF-3 open-slab evaluation limit is %d",PF_SUPPORT_WORK_MAX);
    case WOOD_PANEL_SUPPORT_SEAM_LIMIT:return fs_capacity_error("I33 CAPACITY: PF-3 effective/non-seam limit is %d",PF_SUPPORT_MAX);
    case WOOD_PANEL_SUPPORT_PART_LIMIT:return fs_capacity_error("I33 CAPACITY: PF-3 support subsegment limit is %d",PF_SUPPORT_MAX);
    }
    return false;
}
static bool pf_support_threshold(const World *w,const PanelFill *p,GeoQuantity *out)
{
    ReferenceEval *ctx=app_reference_sources_for_world(w);
    if(!ctx||ctx->use_current_values)return parameter_value(w,p->threshold,out);
    PanelFill definition;
    if(!reference_sources_ensure(ctx)||!wood_finish_sources_fill_definition(ctx->finish_sources,p->id,&definition)||
       !parameter_value(w,definition.threshold,out))return false;
    WoodFinishSourceKey key;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,wood_finish_source_ref(APP_SOURCE_FINISH,WOOD_FINISH_SOURCE_THRESHOLD,p->id,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_QUANTITY)return false;
    *out=value.as.quantity;return true;
}
static bool pf_support_build(const World *w,const PanelFill *p,const PfLayout *d,PfSupport *s)
{
    memset(s,0,sizeof *s);PfFootprint *rects=malloc(WORLD_MAX_TIMBERS*sizeof *rects);GeoQuantity threshold;size_t count;
    if(!rects)return fs_capacity_error("I33 CAPACITY: PF-3 footprints unavailable");
    bool ok=pf_support_threshold(w,p,&threshold)&&pf_support_footprints(w,p,rects,&count)&&pf_support_evaluate(d,rects,count,threshold,s);
    free(rects);return ok;
}
/* Called after D7 reconstruction, before committing any candidate. A capacity
 * failure must reject the transaction, rather than truncate a later read. */
static bool pf_support_rebuild(const World *w)
{
    for(size_t i=0;i<w->wood.finish_surfaces.fill_count;++i){PfLayout d;PfSupport s={0};const PanelFill *p=&w->wood.finish_surfaces.fills[i];
        bool ok=pf_build(w,p,&d)&&pf_support_build(w,p,&d,&s);pf_support_free(&s);pf_free(&d);if(!ok)return false;}
    return true;
}
