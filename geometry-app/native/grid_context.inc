/* H supplies geometry and reference facts from exactly this candidate. */
static bool app_grid_coordinate(void *,GeoParameterRef,GeoCoord *);
static bool app_grid_vertex(void *,uint32_t,uint32_t,GeoPoint2 *);
static bool app_grid_host(void *user,uint32_t id,WoodGridHost *out)
{
    const World *w=(const World *)user;PlacementSurface p;SpaceBoundarySurface b;
    const PlacementSurface *value=app_placement_read(w,id,&p);
    return app_grid_host_value(value,value?app_placement_boundary(w,value,&b):NULL,out);
}
static bool app_grid_reference(void *user,size_t index,WoodGridReference *out)
{
    const World *w=(const World *)user;size_t guides=geo_guides_count(&w->guide_lines);
    memset(out,0,sizeof *out);
    if(index<guides){const GeoGuide *g=geo_guides_at(&w->guide_lines,index);
        out->kind=WOOD_GRID_REFERENCE_GUIDE;out->id=g->id;out->active=true;out->expression=app_guide_expression(w,g->id);return true;}
    index-=guides;if(index>=w->timber_count)return false;
    const TimberAnchor *a=&w->anchors[index];out->kind=WOOD_GRID_REFERENCE_TIMBER;out->id=w->timbers[index].id;
    out->active=w->timbers[index].placed&&(a->anchor_kind==ANCHOR_AT_GRID||a->anchor_kind==ANCHOR_AT_RULE);
    out->is_rule=a->anchor_kind==ANCHOR_AT_RULE;out->rule=a->ref_rule;
    out->grid_id=out->is_rule?a->ref_rule.grid_id:a->ref_grid;return true;
}
static WoodGridContext app_grid_context(const World *world)
{
    World *w=(World *)world;WoodGridContext c={0};
    c.state=&w->grid_applications;c.sources=&w->grid_store;c.user=w;
    c.engineering.state=&w->engineering;c.engineering.user=w;
    c.host=app_grid_host;c.coordinate=app_grid_coordinate;c.vertex=app_grid_vertex;
    c.reference=app_grid_reference;c.parameter_error=g_parameter_error;return c;
}
