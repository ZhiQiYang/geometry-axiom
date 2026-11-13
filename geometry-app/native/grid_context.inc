/* H supplies geometry and reference facts from exactly this candidate. */
static bool app_grid_coordinate(void *,GeoParameterRef,GeoCoord *);
static bool app_grid_vertex(void *,uint32_t,uint32_t,GeoPoint2 *);
static WoodEngineeringContext app_eng_context(const World *);
static WoodFinishContext app_fs_context(const World *);
static bool app_grid_sources_bind(const World *,WoodGridContext *);
static bool app_grid_host(void *user,uint32_t id,WoodGridHost *out)
{
    const World *w=(const World *)user;PlacementSurface p;SpaceBoundarySurface b;
    const PlacementSurface *value=app_placement_read(w,id,&p);
    return app_grid_host_value(value,value?app_placement_boundary(w,value,&b):NULL,out);
}
static bool app_grid_fill_value(const WoodFinishContext *context,uint32_t id,WoodGridFill *out)
{
    const PanelFill *fill=wood_pf_find(context,id);WoodFinishLayout value={0};
    if(!fill||!wood_pf_values(context,fill,&value)||!value.fill||!value.finish)return false;
    *out=(WoodGridFill){.side=value.finish->side,.stagger_axis=value.fill->stagger_axis,
        .size={value.layout.size[0],value.layout.size[1]},.gap=value.layout.gap,
        .origin={value.fill->origin[0],value.fill->origin[1]},.stagger=value.layout.stagger};
    return true;
}
static bool app_grid_fill(void *user,uint32_t id,WoodGridFill *out)
{WoodFinishContext context=app_fs_context((const World *)user);return app_grid_fill_value(&context,id,out);}
static bool app_grid_fill_definition(void *user,uint32_t id)
{WoodFinishContext context=app_fs_context((const World *)user);return wood_pf_find(&context,id)!=NULL;}
static bool app_grid_reference(void *user,size_t index,WoodGridReference *out)
{
    const World *w=(const World *)user;size_t guides=geo_guides_count(&w->geo.guide_lines);
    memset(out,0,sizeof *out);
    if(index<guides){const GeoGuide *g=geo_guides_at(&w->geo.guide_lines,index);
        out->kind=WOOD_GRID_REFERENCE_GUIDE;out->id=g->id;out->active=true;out->expression=app_guide_expression(w,g->id);return true;}
    index-=guides;if(index>=w->wood.timber_count)return false;
    const TimberAnchor *a=&w->wood.anchors[index];out->kind=WOOD_GRID_REFERENCE_TIMBER;out->id=w->wood.timbers[index].id;
    out->active=w->wood.timbers[index].placed&&(a->anchor_kind==ANCHOR_AT_GRID||a->anchor_kind==ANCHOR_AT_RULE);
    out->is_rule=a->anchor_kind==ANCHOR_AT_RULE;out->rule=a->ref_rule;
    out->grid_id=out->is_rule?a->ref_rule.grid_id:a->ref_grid;return true;
}
static WoodGridContext app_grid_context(const World *world)
{
    World *w=(World *)world;WoodGridContext c={0};
    c.state=&w->wood.grid_applications;c.sources=&w->geo.grid_store;c.user=w;
    c.engineering=app_eng_context(world);
    c.host=app_grid_host;c.fill=app_grid_fill;c.coordinate=app_grid_coordinate;c.vertex=app_grid_vertex;
    c.fill_definition=app_grid_fill_definition;
    c.reference=app_grid_reference;c.parameter_error=g_parameter_error;
    app_grid_sources_bind(world,&c);return c;
}
