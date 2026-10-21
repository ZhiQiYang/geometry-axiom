/* H chooses when the existing enclosure operation uses its same-candidate
 * source graph. Parser probes for a not-yet-staged definition keep their old
 * validation phase; the subsequent authoritative rebuild uses K sources. */
static bool app_enclosure_sources_value(const World *world,uint32_t id,
    const SurfaceId *members,size_t count,Space *out,SpaceFaultInfo *fault,bool *handled)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    const GeoEnclosure *stored=geo_enclosures_find(&world->geo.enclosures,id);
    *handled=ctx&&!ctx->use_current_values&&stored&&stored->member_count==count&&
        (!count||(members&&!memcmp(stored->member_ids,members,count*sizeof *members)));
    if(!*handled)return false;
    return reference_sources_ensure(ctx)&&
        geo_enclosure_sources_value(ctx->enclosure_sources,id,out,fault);
}

static bool app_enclosure_sources_axis_bound(const World *world,const Space *space,
    int axis,int slot,Coord *out,bool *handled)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    const GeoEnclosure *stored=space?geo_enclosures_find(&world->geo.enclosures,space->id):NULL;
    *handled=ctx&&!ctx->use_current_values&&stored&&stored->member_count==space->member_count&&
        (!space->member_count||!memcmp(stored->member_ids,space->member_ids,
            space->member_count*sizeof space->member_ids[0]));
    if(!*handled)return false;
    return reference_sources_ensure(ctx)&&
        geo_enclosure_sources_axis_bound(ctx->enclosure_sources,space->id,axis,slot,out);
}

/* Model inspection includes unused enclosure definitions. A partial enclosure
 * has no value for an absent normal slot; its in-plane bbox is not such a slot. */
static bool app_enclosure_sources_complete(ReferenceEval *ctx)
{
    if(!ctx||!reference_sources_ensure(ctx))return false;
    for(size_t i=0;i<geo_enclosures_count(&ctx->world->geo.enclosures);++i){
        const GeoEnclosure *definition=geo_enclosures_at(&ctx->world->geo.enclosures,i);
        GeoEnclosureSourceKey key;GeoSourceValue value;GeoEnclosure result;
        if(geo_eval_source(ctx->sources,geo_enclosure_source_ref(APP_SOURCE_ENCLOSURE,
                GEO_ENCLOSURE_SOURCE_DEFINITION,definition->id,-1,-1,&key),
                GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
           !geo_enclosure_sources_value(ctx->enclosure_sources,definition->id,&result,NULL))return false;
        for(int axis=0;axis<3;++axis)for(int slot=0;slot<2;++slot){
            GeoCoord coordinate;
            if(geo_enclosure_axis_bound(&ctx->world->geo.placement_data,definition,axis,slot,&coordinate)&&
               !geo_enclosure_sources_axis_bound(ctx->enclosure_sources,definition->id,axis,slot,&coordinate))return false;
        }
    }
    return true;
}
