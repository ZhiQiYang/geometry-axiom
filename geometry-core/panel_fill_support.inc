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
    *count=0;const PlacementSurface *host=NULL;
    for(size_t i=0;i<w->finish_surfaces.host_count;++i)if(w->finish_surfaces.hosts[i].fill_id==p->id)
        host=world_find_placement(w,w->finish_surfaces.hosts[i].id);
    if(!host)return true;
    const FinishSurface *finish=fs_find(w,p->finish_id);
    for(size_t i=0;i<w->timber_count;++i){
        if(!w->timbers[i].placed||w->anchors[i].placement_id!=host->id)continue;
        SurfaceRegion2 f;
        if(!timber_a0_footprint_uv(host,&w->timbers[i],&w->anchors[i],&f))return fs_error("R43: timber %u footprint unavailable",w->timbers[i].id);
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
static bool pf_support_build(const World *w,const PanelFill *p,const PfLayout *d,PfSupport *s)
{
    memset(s,0,sizeof *s);PfFootprint *rects=malloc(WORLD_MAX_TIMBERS*sizeof *rects);GeoQuantity threshold;size_t count;
    if(!rects)return fs_capacity_error("I33 CAPACITY: PF-3 footprints unavailable");
    bool ok=parameter_value(w,p->threshold,&threshold)&&pf_support_footprints(w,p,rects,&count)&&pf_support_evaluate(d,rects,count,threshold,s);
    free(rects);return ok;
}
/* Called after D7 reconstruction, before committing any candidate. A capacity
 * failure must reject the transaction, rather than truncate a later read. */
static bool pf_support_rebuild(const World *w)
{
    for(size_t i=0;i<w->finish_surfaces.fill_count;++i){PfLayout d;PfSupport s={0};const PanelFill *p=&w->finish_surfaces.fills[i];
        bool ok=pf_build(w,p,&d)&&pf_support_build(w,p,&d,&s);pf_support_free(&s);pf_free(&d);if(!ok)return false;}
    return true;
}
