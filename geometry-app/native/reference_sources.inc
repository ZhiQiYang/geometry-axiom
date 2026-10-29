static GeoVersionStore *app_eng_version_store(const World *);
/* H binds every resolver to the exact ReferenceEval candidate. K sees opaque
 * keys and typed outputs; legacy token parsing remains in reference_quantity_raw. */
enum { APP_SOURCE_GUIDE=1, APP_SOURCE_MEMBER_POSE, APP_SOURCE_REFERENCE, APP_SOURCE_PARAMETER,
    APP_SOURCE_NAMED=6, APP_SOURCE_DATUM, APP_SOURCE_ENGINEERING_DIMENSION,
    APP_SOURCE_ENGINEERING_BINDING,APP_SOURCE_ENGINEERING_DEFINITION,APP_SOURCE_SECTION_PROFILE,
    APP_SOURCE_FINISH,APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,APP_SOURCE_GRID,APP_SOURCE_CONTACT,APP_SOURCE_ASSEMBLY,
    APP_SOURCE_ENCLOSURE,APP_SOURCE_WOOD_DEFINITION,APP_SOURCE_REGION_KEYS,
    APP_SOURCE_LINEAR_DEFINITION,APP_SOURCE_PARAMETER_DEFINITION,APP_SOURCE_VERSION }; /* token 5 belongs to model roots */
typedef struct {
    uint32_t placement;
    uint32_t guide_id;
    int direction;
    bool has_context;
    char expression[REF_EXPR_MAX];
} AppReferenceSourceKey;
static bool reference_source_id(const GeoSourceRef *source,uint32_t *id)
{if(source->key_size!=sizeof *id)return false;memcpy(id,source->key,sizeof *id);return true;}
static int reference_source_guide_index(const World *world,uint32_t id)
{for(size_t i=0;i<geo_guides_count(&world->geo.guide_lines);++i)if(geo_guides_values(&world->geo.guide_lines)[i].id==id)return (int)i;return -1;}
static bool reference_source_context(const GeoSourceRef *source,AppReferenceSourceKey *key)
{
    if(source->key_size!=sizeof *key)return false;
    memcpy(key,source->key,sizeof *key);
    return memchr(key->expression,0,sizeof key->expression)!=NULL;
}
static bool reference_source_is_dimension(const char *text)
{
    if(!strncmp(text,"spec:",5)||!strncmp(text,"panel:",6)||!strncmp(text,"gap:",4))return true;
    if(strncmp(text,"timber:",7))return false;
    const char *field=strchr(text+7,':');
    return field&&(!strcmp(field,":A")||!strcmp(field,":B"));
}
static bool reference_source_name(const GeoSourceRef *source,char name[GEO_NAMED_VALUE_NAME_BYTES])
{
    if(!source->key_size||source->key_size>=GEO_NAMED_VALUE_NAME_BYTES||!source->key||memchr(source->key,0,source->key_size))return false;
    memcpy(name,source->key,source->key_size);name[source->key_size]=0;return true;
}
static bool reference_source_describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *descriptor)
{
    ReferenceEval *ctx=opaque;World *world=ctx->world;uint32_t id;
    memset(descriptor,0,sizeof *descriptor);descriptor->unit=GEO_UNIT_LENGTH;
    if(source->provider==APP_SOURCE_NAMED){
        char name[GEO_NAMED_VALUE_NAME_BYTES];
        if(!reference_source_name(source,name)||!geo_named_values_find(&world->geo.named_values,name))return false;
        descriptor->kind=GEO_SOURCE_QUANTITY;descriptor->context.axis=-1;return true;
    }
    if(source->provider==APP_SOURCE_DATUM){
        if(!reference_source_id(source,&id))return false;
        const GeoDatum *datum=geo_datums_find(&world->geo.datum_planes,id);if(!datum)return false;
        descriptor->kind=GEO_SOURCE_AXIS_POSITION;
        if(!ctx->use_current_values){descriptor->context_from_value=true;descriptor->context.axis=-1;return true;}
        descriptor->context.axis=datum->axis;return true;
    }
    if(source->provider==APP_SOURCE_GUIDE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_source_guide_index(world,id);if(i<0)return false;
        const GuideLine *g=&geo_guides_values(&world->geo.guide_lines)[i];
        descriptor->kind=GEO_SOURCE_AXIS_POSITION;
        /* Placement and axis come from the actual definition and frame. Keep
         * metadata reads free of definition or geometry evaluation. */
        if(!ctx->use_current_values){descriptor->context.axis=-1;descriptor->context_from_value=true;return true;}
        descriptor->context=(GeoSourceContext){true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1};return true;
    }
    if(source->provider==APP_SOURCE_MEMBER_POSE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_timber_index(world,id);if(i<0)return false;
        descriptor->kind=GEO_SOURCE_BOX;descriptor->retry_failure=!ctx->wanted[i];
        descriptor->context=(GeoSourceContext){true,world->wood.anchors[i].placement_id,-1};return true;
    }
    if(source->provider==APP_SOURCE_REFERENCE){
        AppReferenceSourceKey key;if(!reference_source_context(source,&key))return false;
        descriptor->retry_failure=true;
        descriptor->kind=reference_source_is_dimension(key.expression)?GEO_SOURCE_QUANTITY:GEO_SOURCE_AXIS_POSITION;
        descriptor->context=(GeoSourceContext){key.has_context,key.placement,key.direction==GUIDE_ALONG_V?0:1};return true;
    }
    return false;
}
static bool reference_source_evaluate(void *opaque,GeoEvalContext *evaluation,const GeoSourceRef *source,GeoSourceValue *value)
{
    ReferenceEval *ctx=opaque;World *world=ctx->world;uint32_t id;
    if(evaluation!=ctx->sources)return false;
    if(source->provider==APP_SOURCE_NAMED){
        char name[GEO_NAMED_VALUE_NAME_BYTES];if(!reference_source_name(source,name))return false;
        const GeoNamedValue *named=geo_named_values_find(&world->geo.named_values,name);if(!named)return false;
        value->kind=GEO_SOURCE_QUANTITY;value->as.quantity=(GeoQuantity){named->value,1,GEO_UNIT_LENGTH};return true;
    }
    if(source->provider==APP_SOURCE_DATUM){
        if(!reference_source_id(source,&id))return false;
        const GeoDatum *datum=geo_datums_find(&world->geo.datum_planes,id);if(!datum)return false;
        size_t at=(size_t)(datum-geo_datums_values(&world->geo.datum_planes));
        value->kind=GEO_SOURCE_AXIS_POSITION;return reference_compute_datum(ctx,at,&value->as.position);
    }
    if(source->provider==APP_SOURCE_GUIDE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_source_guide_index(world,id);
        if(i<0)return false;value->kind=GEO_SOURCE_AXIS_POSITION;
        return reference_compute_guide(ctx,(size_t)i,&value->as.position);
    }
    if(source->provider==APP_SOURCE_MEMBER_POSE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_timber_index(world,id);
        if(i<0||!reference_compute_timber(ctx,(size_t)i))return false;
        const Timber *t=&world->wood.timbers[i];value->kind=GEO_SOURCE_BOX;
        value->as.box=(GeoBox3){{t->origin,t->axis_length,t->axis_a,t->axis_b},{t->length,t->size_a,t->size_b}};return true;
    }
    if(source->provider==APP_SOURCE_REFERENCE){
        AppReferenceSourceKey key;if(!reference_source_context(source,&key))return false;
        GuideLine context={0};context.id=key.guide_id;context.placement_id=key.placement;context.direction=(GuideDirection)key.direction;
        Coord coordinate;if(!reference_quantity_raw(ctx,key.has_context?&context:NULL,key.expression,&coordinate))return false;
        if(reference_source_is_dimension(key.expression)){
            value->kind=GEO_SOURCE_QUANTITY;value->as.quantity=(GeoQuantity){coordinate,1,GEO_UNIT_LENGTH};
        }else{
            value->kind=GEO_SOURCE_AXIS_POSITION;
            value->as.position=(GeoAxisPosition){coordinate,{key.has_context,key.placement,key.direction==GUIDE_ALONG_V?0:1}};
        }
        return true;
    }
    return false;
}
static bool reference_sp_dimension(void *opaque,const EngDimensionSource *source,const EngTarget *target,GeoCoord *out)
{ReferenceEval *ctx=opaque;return app_sp_resolve_dimension_sources(ctx->world,ctx->parameter_sources,ctx->engineering_sources,source,target,out);}
static bool reference_boundary_policy(ReferenceEval *,WoodBoundaryRegion *);
static bool reference_sp_host(void *opaque,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    ReferenceEval *ctx=opaque;if(ctx->use_current_values)return app_sp_live_host(ctx->world,id,frame,region,derived);
    if(!geo_placements_find(&ctx->world->geo.placement_data,id))return false;
    GeoPlacementDefinitionHeader definition;
    if(!geo_placement_sources_definition_header(ctx->placement_sources,id,&definition))return false;
    if(definition.domain==GEO_PLACEMENT_REGION_SET){*derived=true;return true;}
    PlacementSurface placement;SpaceBoundarySurface boundary;const SpaceBoundarySurface *view;
    if(!reference_host_read(ctx,id,&placement,&boundary,&view)||!surface_frame_is_valid(&placement.frame))return false;
    WoodBoundaryRegion actual=*placement_effective_boundary(&placement,view,&boundary);
    *frame=placement.frame;*region=actual;*derived=false;return true;
}
static bool reference_placement_binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{
    ReferenceEval *ctx=opaque;if(ctx->use_current_values||kind==GEO_PLACEMENT_SOURCE_DEFINITION)return false;
    GeoPlacementDefinitionHeader definition;
    if(!geo_placement_sources_definition_header(ctx->placement_sources,id,&definition)||definition.domain!=GEO_PLACEMENT_REGION_SET)return false;
    *out=wood_finish_source_ref(APP_SOURCE_FINISH,kind==GEO_PLACEMENT_SOURCE_FRAME?WOOD_FINISH_SOURCE_DERIVED_FRAME:WOOD_FINISH_SOURCE_DERIVED_REGION,id,&ctx->placement_binding_key);
    return true;
}
static void reference_region_geometry(SpaceBoundarySurface *,const GeoRegionView *);
static bool reference_boundary_policy(ReferenceEval *ctx,WoodBoundaryRegion *out)
{
    if(ctx->use_current_values)return true;WoodBoundaryPolicy policy;
    if(!wood_definition_sources_boundary(ctx->definition_sources,out->id,&policy))return false;
    out->kind=(BoundaryKind)policy.kind;
    for(size_t i=0;i<out->outline.count;++i)out->outline.fixity[i]=(EdgeFixity)policy.fixity[0][i];
    for(size_t h=0;h<out->hole_count;++h)for(size_t i=0;i<out->holes[h].count;++i)out->holes[h].fixity[i]=(EdgeFixity)policy.fixity[h+1][i];
    return true;
}
static bool reference_fs_boundary(void *opaque,uint32_t id,WoodBoundaryRegion *out)
{
    ReferenceEval *ctx=opaque;if(!app_fs_boundary(ctx->world,id,out))return false;
    GeoRegionSourceKey key;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,geo_region_source_ref(APP_SOURCE_REGION,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.as.regions.count!=1)return false;
    reference_region_geometry(out,&value.as.regions.regions[0]);return reference_boundary_policy(ctx,out);
}
static bool reference_fs_obstacle(void *opaque,const FinishObstacleRef *ref,Coord lo[3],Coord hi[3])
{
    ReferenceEval *ctx=opaque;if(!app_fs_obstacle_box(ctx->world,ref,lo,hi))return false;
    if(ctx->use_current_values)return true;
    if(ref->kind==FS_OBSTACLE_COLUMN){WoodColumn c;if(!wood_definition_sources_column(ctx->definition_sources,ref->id,&c))return false;
        lo[0]=c.x_lo;lo[1]=c.y_lo;lo[2]=c.z_lo;hi[0]=c.x_hi;hi[1]=c.y_hi;hi[2]=c.z_hi;
    }else{WoodBeam b;if(!wood_definition_sources_beam(ctx->definition_sources,ref->id,&b))return false;
        lo[0]=b.x_lo;lo[1]=b.y_lo;lo[2]=b.z_lo;hi[0]=b.x_hi;hi[1]=b.y_hi;hi[2]=b.z_hi;
    }return true;
}
static bool reference_fs_parameter_coord(void *opaque,ParameterRef ref,Coord *out)
{return app_fs_parameter_coord(((ReferenceEval *)opaque)->world,ref,out);}
static bool reference_fs_parameter_value(void *opaque,ParameterRef ref,GeoQuantity *out)
{return app_fs_parameter_value(((ReferenceEval *)opaque)->world,ref,out);}
static bool reference_fs_engineering_operation(void *opaque,GeoJson *j,int t)
{return app_fs_engineering_operation(((ReferenceEval *)opaque)->world,j,t);}
static bool reference_fs_derived_operation(void *opaque,GeoJson *j,int t,bool remove)
{return app_fs_derived_operation(((ReferenceEval *)opaque)->world,j,t,remove);}
static bool reference_dp_read(void *opaque,uint32_t id,WoodDerivedValue *out)
{return app_dp_read(((ReferenceEval *)opaque)->world,id,out);}
static bool reference_dp_write(void *opaque,const WoodDerivedValue *value)
{return app_dp_write(((ReferenceEval *)opaque)->world,value);}
static bool reference_dp_remove(void *opaque,uint32_t id)
{return app_dp_remove(((ReferenceEval *)opaque)->world,id);}
static size_t reference_dp_count(void *opaque)
{return app_dp_count(((ReferenceEval *)opaque)->world);}
static void reference_dp_remove_position(void *opaque,uint32_t id)
{app_dp_remove_position(((ReferenceEval *)opaque)->world,id);}
static void reference_finish_context(ReferenceEval *ctx,WoodFinishContext *finish)
{
    finish->user=ctx;finish->boundary=reference_fs_boundary;finish->obstacle_box=reference_fs_obstacle;
    finish->parameter_coord=reference_fs_parameter_coord;finish->parameter_value=reference_fs_parameter_value;
    finish->engineering_operation=reference_fs_engineering_operation;finish->derived_operation=reference_fs_derived_operation;
    wood_engineering_sources_bind(ctx->engineering_sources,&finish->engineering);
}
static void reference_derived_context(ReferenceEval *ctx,WoodDerivedContext *finish)
{
    reference_finish_context(ctx,&finish->finish);finish->placement_read=reference_dp_read;finish->placement_write=reference_dp_write;
    finish->placement_remove=reference_dp_remove;finish->placement_count=reference_dp_count;finish->remove_canvas_position=reference_dp_remove_position;
}
static bool reference_derived_resolve(ReferenceEval *ctx,const PlacementSurface *p,const char *key,int *hole,int *edge)
{
    if(!p||!p->derived_fill_id)return false;
    if(ctx->use_current_values){
        /* Snapshot reads must not acquire the ambient candidate's hooks. */
        WoodDerivedContext direct=app_dp_context(ctx->world);direct.evaluation=NULL;direct.finish.evaluation=NULL;
        direct.finish.user=ctx->world;direct.finish.boundary=app_fs_boundary;direct.finish.obstacle_box=app_fs_obstacle_box;
        direct.finish.parameter_coord=app_fs_parameter_coord;direct.finish.parameter_value=app_fs_parameter_value;
        direct.finish.engineering_operation=app_fs_engineering_operation;direct.finish.derived_operation=app_fs_derived_operation;
        WoodEngineeringContext *engineering=&direct.finish.engineering;engineering->sources=NULL;
        engineering->resolve_source=NULL;engineering->resolve_binding=NULL;engineering->last_terminal=NULL;engineering->source_named=NULL;
        engineering->source_parameter=NULL;engineering->depend_definition=NULL;engineering->validate_application=NULL;engineering->source_version_field=NULL;engineering->source_version_definition=NULL;engineering->source_application=NULL;
        direct.placement_read=app_dp_read;direct.placement_write=app_dp_write;direct.placement_remove=app_dp_remove;
        direct.placement_count=app_dp_count;direct.remove_canvas_position=app_dp_remove_position;
        WoodDerivedValue value={0};value.id=p->id;value.derived_fill_id=p->derived_fill_id;value.derived_h=p->derived_h;
        value.frame=p->frame;value.component_count=p->component_count;memcpy(value.components,p->components,sizeof value.components);
        return wood_dp_edge_resolve(&direct,&value,key,hole,edge);
    }
    if(!reference_sources_ensure(ctx))return false;
    return wood_finish_sources_edge_resolve(ctx->finish_sources,p->id,key,hole,edge);
}
static bool reference_grid_host(void *opaque,uint32_t id,WoodGridHost *out)
{
    ReferenceEval *ctx=opaque;PlacementSurface placement;SpaceBoundarySurface boundary;
    const SpaceBoundarySurface *b;
    if(!reference_host_read(ctx,id,&placement,&boundary,&b))return false;
    return app_grid_host_value(&placement,b,out);
}
static bool reference_grid_coordinate(void *opaque,GeoParameterRef ref,GeoCoord *out)
{return app_grid_coordinate(((ReferenceEval *)opaque)->world,ref,out);}
static bool reference_grid_vertex(void *opaque,uint32_t id,uint32_t key,GeoPoint2 *out)
{
    ReferenceEval *ctx=opaque;GeoPoint2 legacy_point;
    if(!app_grid_vertex(ctx->world,id,key,&legacy_point))return false;
    if(ctx->use_current_values){if(out)*out=legacy_point;return true;}
    return geo_region_key_sources_vertex(ctx->region_key_sources,id,key,out);
}
static bool reference_grid_reference(void *opaque,size_t index,WoodGridReference *out)
{return app_grid_reference(((ReferenceEval *)opaque)->world,index,out);}
static void reference_grid_context(ReferenceEval *ctx,WoodGridContext *grid)
{
    grid->user=ctx;grid->host=reference_grid_host;grid->coordinate=reference_grid_coordinate;
    grid->vertex=reference_grid_vertex;grid->reference=reference_grid_reference;
    wood_engineering_sources_bind(ctx->engineering_sources,&grid->engineering);
}
static bool reference_asm_json(void *opaque,GeoJson *json,const char *text)
{return app_asm_json(((ReferenceEval *)opaque)->world,json,text);}
static void reference_asm_drop_position(void *opaque,bool rule,uint32_t id)
{app_asm_drop_position(((ReferenceEval *)opaque)->world,rule,id);}
static bool reference_asm_other(void *opaque,GeoJson *json,int token)
{return app_asm_other(((ReferenceEval *)opaque)->world,json,token);}
static bool reference_asm_surface(void *opaque,uint32_t id)
{return app_asm_surface(((ReferenceEval *)opaque)->world,id);}
static bool reference_asm_guide(void *opaque,uint32_t id,WoodAssemblyGuide *out)
{
    ReferenceEval *ctx=opaque;if(!app_asm_guide(ctx->world,id,out))return false;if(ctx->use_current_values)return true;
    int index=reference_source_guide_index(ctx->world,id);GeoAxisPosition position;
    if(index<0||!reference_guide_position(ctx,(size_t)index,&position)||!position.context.has_placement||
       (position.context.axis!=0&&position.context.axis!=1))return false;
    out->surface_id=(uint32_t)position.context.placement;out->direction=position.context.axis?ASM_DIR_U:ASM_DIR_V;return true;
}
static bool reference_asm_member(void *opaque,uint32_t id,WoodAssemblyMember *out)
{
    ReferenceEval *ctx=opaque;if(!app_asm_member(ctx->world,id,out))return false;
    if(!out||ctx->use_current_values)return true;WoodMemberDefinition member;WoodMemberPlacement anchor;
    if(!wood_definition_sources_member(ctx->definition_sources,id,&member)||
       !wood_definition_sources_placement(ctx->definition_sources,id,&anchor))return false;
    /* Width/depth/placed intentionally remain the saved admission record so
     * I42 can compare it with generated dimensions; eligibility uses sources. */
    out->surface_id=anchor.placement_id;out->role=member.role;return true;
}
static bool reference_asm_footprint(void *opaque,uint32_t surface,uint32_t id,GeoRect2 *out)
{
    ReferenceEval *ctx=opaque;
    /* Retain the legacy callback's refusal and output timing. I42 reaches this
     * only after generation and ordinary member reconstruction have finished. */
    if(!app_asm_footprint(ctx->world,surface,id,out))return false;
    if(ctx->use_current_values)return true;
    GeoSourceValue value;GeoFrame frame;GeoQuad3 face;unsigned axis,side;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
        !reference_placement_frame(ctx,surface,&frame)||!wood_member_face_spec(WOOD_MEMBER_FACE_A0,&axis,&side)||
        !geo_box_face(&value.as.box,axis,side,&face))return false;
    GeoPoint2 first=geo_frame_project_uv(&frame,face.vertices[0]);GeoRect2 rect={first.u,first.v,first.u,first.v};
    for(size_t i=1;i<4;++i){GeoPoint2 point=geo_frame_project_uv(&frame,face.vertices[i]);
        rect.min_u=coord_min(rect.min_u,point.u);rect.max_u=coord_max(rect.max_u,point.u);
        rect.min_v=coord_min(rect.min_v,point.v);rect.max_v=coord_max(rect.max_v,point.v);}
    *out=rect;return true;
}
static size_t reference_asm_member_count(void *opaque)
{return app_asm_member_count(((ReferenceEval *)opaque)->world);}
static void reference_asm_allocate(void *opaque,uint32_t id)
{app_asm_allocate(((ReferenceEval *)opaque)->world,id);}
static bool reference_asm_remove(void *opaque,uint32_t id)
{return app_asm_remove(((ReferenceEval *)opaque)->world,id);}
static void reference_asm_write(void *opaque,const WoodMember *member,const WoodAssemblyDefinition *definition)
{app_asm_write(((ReferenceEval *)opaque)->world,member,definition);}
static bool reference_asm_anchor_matches(void *opaque,uint32_t id,const WoodAssemblyDefinition *definition)
{return app_asm_anchor_matches(((ReferenceEval *)opaque)->world,id,definition);}
static bool reference_asm_instance_content(void *opaque,AsmInstance *instance,GeoJson *json,int source)
{return app_asm_instance_content(((ReferenceEval *)opaque)->world,instance,json,source);}
static void reference_assembly_context(ReferenceEval *ctx,WoodAssemblyContext *assembly)
{
    assembly->user=ctx;assembly->json_parse=reference_asm_json;assembly->drop_position=reference_asm_drop_position;
    assembly->other_operation=reference_asm_other;assembly->surface=reference_asm_surface;assembly->guide=reference_asm_guide;
    assembly->member=reference_asm_member;assembly->footprint=reference_asm_footprint;assembly->member_count=reference_asm_member_count;
    assembly->allocate_member=reference_asm_allocate;assembly->remove_member=reference_asm_remove;assembly->write_member=reference_asm_write;
    assembly->anchor_matches=reference_asm_anchor_matches;assembly->instance_content=reference_asm_instance_content;
    wood_engineering_sources_bind(ctx->engineering_sources,&assembly->engineering);
}
static bool reference_eng_placement(void *opaque,uint32_t id,bool *derived)
{
    ReferenceEval *ctx=opaque;bool direct_derived=false;
    if(!app_eng_placement(ctx->world,id,&direct_derived)){if(derived)*derived=false;return false;}
    if(ctx->use_current_values){if(derived)*derived=direct_derived;return true;}
    GeoPlacementDefinition definition;
    if(!reference_sources_ensure(ctx)||!geo_placement_sources_definition(ctx->placement_sources,id,&definition))return false;
    if(derived)*derived=definition.domain==GEO_PLACEMENT_REGION_SET;return true;
}
static bool reference_grid_definition(ReferenceEval *ctx,uint32_t id,WoodGridApplication *out)
{
    if(ctx->use_current_values){const ReferenceGrid *grid=world_find_grid(ctx->world,id);if(!grid)return false;*out=*grid;return true;}
    return reference_sources_ensure(ctx)&&wood_grid_sources_definition(ctx->grid_sources,id,out);
}
static bool reference_eng_target(void *opaque,const EngTarget *target,WoodEngineeringTargetInfo *out)
{
    ReferenceEval *ctx=opaque;
    if(!app_eng_target(ctx->world,target,out))return false;if(ctx->use_current_values)return true;
    if(!target->kind){WoodGridApplication grid;if(!reference_grid_definition(ctx,target->id,&grid))return false;
        out->placement_id=grid.placement_id;out->from_system=grid.from_system||grid.from_binding;
        out->is_subgrid=grid.is_subgrid;out->panel_axis=grid.axis[target->axis].source==GRID_SRC_PANEL;
    }else{WoodMemberDefinition member;WoodMemberPlacement placement;
        if(!wood_definition_sources_member(ctx->definition_sources,target->id,&member)||
           !wood_definition_sources_placement(ctx->definition_sources,target->id,&placement))return false;
        out->placement_id=placement.placement_id;out->role=member.role;
    }
    return true;
}
static bool reference_eng_named(void *opaque,const char *name,GeoCoord *out)
{return app_eng_named(((ReferenceEval *)opaque)->world,name,out);}
static bool reference_eng_parameter(void *opaque,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{return app_eng_parameter(((ReferenceEval *)opaque)->world,ref,out,error,cap);}
static bool reference_member_owned(ReferenceEval *ctx,uint32_t id,bool *out)
{
    /* Owned scene records are reconstructed before their assembly blocks.
     * Keep that exact replay gate ahead of any source request. */
    if(app_assembly_replaying()||ctx->use_current_values){*out=assembly_owned(ctx->world,id);return true;}
    return reference_sources_ensure(ctx)&&wood_assembly_sources_owned(ctx->assembly_sources,id,out);
}
static bool reference_eng_owned(void *opaque,uint32_t id)
{
    ReferenceEval *ctx=opaque;bool owned;
    if(reference_member_owned(ctx,id,&owned))return owned;
    /* This legacy callback has no error result. A failed source denies the
     * write and marks the candidate failed; it must never grant permission. */
    ctx->source_failure=true;if(!g_revalidate_error[0])set_revalidate_error("I42: assembly ownership source evaluation failed");return true;
}
static void reference_eng_write(void *opaque,const EngTarget *target,GeoCoord value)
{app_eng_write(((ReferenceEval *)opaque)->world,target,value);}
static bool reference_eng_serializable(void *opaque,char *error,size_t cap)
{return app_eng_serializable(((ReferenceEval *)opaque)->world,error,cap);}
static void reference_engineering_context(ReferenceEval *ctx,WoodEngineeringContext *engineering)
{
    engineering->user=ctx;engineering->placement=reference_eng_placement;engineering->target=reference_eng_target;
    engineering->named_value=reference_eng_named;engineering->parameter=reference_eng_parameter;
    engineering->member_owned=reference_eng_owned;engineering->write_dimension=reference_eng_write;engineering->serializable=reference_eng_serializable;
}
static bool reference_contact_facts(void *,GeoEvalContext *,const WoodContactSourceRequest *,WoodContactSourceFacts *);
static bool reference_sources_ensure(ReferenceEval *ctx)
{
    if(ctx->sources_registered)return true;
    /* The lifetime itself is a unique in-process candidate evaluation identity.
     * The host's persistent revision is attached by its publish coordinator. */
    if(!ctx->sources)ctx->sources=geo_eval_create((uint64_t)(uintptr_t)ctx,0);if(!ctx->sources)return false;
    static const char *const names[]={"app.guide","woodworking.member.pose","app.legacy-reference"};
    for(uint32_t token=APP_SOURCE_GUIDE;token<APP_SOURCE_PARAMETER;++token){
        GeoSourceProvider provider={token,names[token-1],"geo261-native-source/1",ctx,reference_source_describe,reference_source_evaluate};
        if(!geo_eval_register(ctx->sources,&provider)){reference_sources_dispose(ctx);return false;}
    }
    GeoParameterStore *parameters=&ctx->world->geo.parameters;
    if(ctx->use_current_values){
        ctx->parameter_snapshot=geo_parameters_clone(parameters);parameters=ctx->parameter_snapshot;
        if(!parameters){reference_sources_dispose(ctx);return false;}
    }
    ctx->parameter_sources=geo_parameter_sources_register_with_definitions(ctx->sources,parameters,APP_SOURCE_PARAMETER,APP_SOURCE_PARAMETER_DEFINITION,
        "core.parameter.field","geo261-parameter-ast-source/1");
    if(!ctx->parameter_sources){reference_sources_dispose(ctx);return false;}
    ctx->linear_definition_sources=geo_linear_definition_sources_register(ctx->sources,&ctx->world->geo.datum_planes,&ctx->world->geo.guide_lines,APP_SOURCE_LINEAR_DEFINITION);
    if(!ctx->linear_definition_sources){reference_sources_dispose(ctx);return false;}
    for(uint32_t token=APP_SOURCE_NAMED;token<=APP_SOURCE_DATUM;++token){
        GeoSourceProvider provider={token,token==APP_SOURCE_NAMED?"core.named-value":"core.datum.position",
            "geo261-linear-definition-source/1",ctx,reference_source_describe,reference_source_evaluate};
        if(!geo_eval_register(ctx->sources,&provider)){reference_sources_dispose(ctx);return false;}
    }
    WoodEngineeringContext engineering=app_eng_context(ctx->world);reference_engineering_context(ctx,&engineering);
    ctx->version_sources=geo_version_sources_register(ctx->sources,app_eng_version_store(ctx->world),APP_SOURCE_VERSION);
    if(!ctx->version_sources){reference_sources_dispose(ctx);return false;}
    ctx->engineering_sources=wood_engineering_sources_register(ctx->sources,&engineering,
        (WoodEngineeringSourceTokens){APP_SOURCE_ENGINEERING_DIMENSION,APP_SOURCE_ENGINEERING_BINDING,
            APP_SOURCE_ENGINEERING_DEFINITION,APP_SOURCE_NAMED,APP_SOURCE_PARAMETER,APP_SOURCE_VERSION});
    if(!ctx->engineering_sources){reference_sources_dispose(ctx);return false;}
    WoodAssemblyContext assembly=app_asm_context(ctx->world);reference_assembly_context(ctx,&assembly);
    ctx->assembly_sources=wood_assembly_sources_create(ctx->sources,APP_SOURCE_ASSEMBLY,&assembly);
    if(!ctx->assembly_sources){reference_sources_dispose(ctx);return false;}
    WoodDerivedContext finish=app_dp_context(ctx->world);
    reference_derived_context(ctx,&finish);
    ctx->finish_sources=wood_finish_sources_create(ctx->sources,(WoodFinishSourceTokens){APP_SOURCE_FINISH,APP_SOURCE_PARAMETER},&finish);
    if(!ctx->finish_sources){reference_sources_dispose(ctx);return false;}
    ctx->placement_sources=geo_placement_sources_register(ctx->sources,&ctx->world->geo.placement_data,&ctx->world->geo.region_data,
        APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,reference_placement_binding,ctx);
    if(!ctx->placement_sources){reference_sources_dispose(ctx);return false;}
    ctx->region_key_sources=geo_region_key_sources_register(ctx->sources,&ctx->world->geo.region_data,APP_SOURCE_REGION_KEYS,APP_SOURCE_REGION);
    if(!ctx->region_key_sources){reference_sources_dispose(ctx);return false;}
    ctx->enclosure_sources=geo_enclosure_sources_register(ctx->sources,&ctx->world->geo.enclosures,
        &ctx->world->geo.region_data,&ctx->world->geo.placement_data,APP_SOURCE_ENCLOSURE,APP_SOURCE_PLACEMENT,APP_SOURCE_REGION);
    if(!ctx->enclosure_sources){reference_sources_dispose(ctx);return false;}
    WoodDefinitionContext definitions={&ctx->world->wood,&ctx->world->geo.region_data,APP_SOURCE_ENCLOSURE,APP_SOURCE_REGION};
    ctx->definition_sources=wood_definition_sources_create(ctx->sources,APP_SOURCE_WOOD_DEFINITION,&definitions);
    if(!ctx->definition_sources){reference_sources_dispose(ctx);return false;}
    WoodSectionProfileContext profiles=app_sp_context(ctx->world);
    profiles.user=ctx;profiles.resolve_dimension=reference_sp_dimension;profiles.live_host=reference_sp_host;
    wood_engineering_sources_bind(ctx->engineering_sources,&profiles.engineering);
    ctx->section_profile_sources=wood_sp_sources_create(ctx->sources,APP_SOURCE_SECTION_PROFILE,&profiles);
    if(!ctx->section_profile_sources){reference_sources_dispose(ctx);return false;}
    WoodGridContext grid=app_grid_context(ctx->world);reference_grid_context(ctx,&grid);
    ctx->grid_sources=wood_grid_sources_create(ctx->sources,(WoodGridSourceTokens){APP_SOURCE_GRID,APP_SOURCE_PARAMETER,APP_SOURCE_ENGINEERING_BINDING,APP_SOURCE_REGION_KEYS},&grid);
    if(!ctx->grid_sources){reference_sources_dispose(ctx);return false;}
    ctx->contact_sources=wood_contact_sources_create(ctx->sources,APP_SOURCE_CONTACT,reference_contact_facts,ctx);
    if(!ctx->contact_sources){reference_sources_dispose(ctx);return false;}
    ctx->sources_registered=true;return true;
}
/* Complete version identities only after the candidate's ordinary rebuild
 * has succeeded. Keep unused version fields lazy and retain this exact graph. */
static bool app_world_candidate_version_inventory(AppWorldCandidate *candidate,ReferenceEval *ctx)
{
    if(!candidate||!candidate->control||!ctx||app_candidate_evaluation_state(candidate->control)!=ctx)return false;
    GeoEvalContext *sources=geo_candidate_sources(app_candidate_core(candidate->control));
    if(!sources)return false;
    const EngineeringState *engineering=&candidate->after.wood.engineering;
    if(ctx->world!=&candidate->after||ctx->sources!=sources||!ctx->sources_borrowed||
       ctx->use_current_values||!ctx->sources_registered||
       geo_version_sources_context(ctx->version_sources)!=sources||
       geo_version_sources_store(ctx->version_sources)!=&candidate->after.geo.version_store||
       wood_engineering_sources_context(ctx->engineering_sources)!=sources||
       wood_engineering_sources_state(ctx->engineering_sources)!=engineering)return false;
    return wood_engineering_sources_definitions(ctx->engineering_sources)&&
        wood_engineering_sources_metadata(ctx->engineering_sources)&&
        geo_version_sources_definitions(ctx->version_sources);
}
static WoodEngineeringSources *app_engineering_sources(const World *world)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return NULL;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    return ctx?ctx->engineering_sources:NULL;
}
static bool app_finish_sources_bind(const World *world,WoodFinishContext *finish)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return false;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    if(!ctx||!ctx->finish_sources)return false;reference_finish_context(ctx,finish);
    return wood_finish_sources_bind_finish(ctx->finish_sources,finish);
}
static bool app_derived_sources_bind(const World *world,WoodDerivedContext *finish)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return false;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    if(!ctx||!ctx->finish_sources)return false;reference_derived_context(ctx,finish);
    return wood_finish_sources_bind(ctx->finish_sources,finish);
}
static bool app_grid_sources_bind(const World *world,WoodGridContext *grid)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return false;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    if(!ctx||!ctx->grid_sources)return false;reference_grid_context(ctx,grid);
    return wood_grid_sources_bind(ctx->grid_sources,grid);
}
static bool app_assembly_sources_bind(const World *world,WoodAssemblyContext *assembly)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return false;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    if(!ctx||!ctx->assembly_sources)return false;reference_assembly_context(ctx,assembly);
    return wood_assembly_sources_bind(ctx->assembly_sources,assembly);
}
static bool reference_placement_frame(ReferenceEval *ctx,uint32_t id,GeoFrame *out)
{
    if(!reference_sources_ensure(ctx))return false;GeoPlacementSourceKey key;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_FRAME,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.frame;return true;
}
static bool reference_member_footprint(ReferenceEval *ctx,size_t index,uint32_t placement_id,GeoRect2 *out)
{
    World *world=ctx->world;PlacementSurface placement;
    if(index>=world->wood.timber_count||!app_placement_read(world,placement_id,&placement))return false;
    if(ctx->use_current_values)return timber_a0_footprint_uv(&placement,&world->wood.timbers[index],&world->wood.anchors[index],out);
    uint32_t id=world->wood.timbers[index].id;GeoSourceValue value;GeoFrame frame;GeoQuad3 face;unsigned axis,side;
    WoodMemberPlacement anchor;
    if(!reference_sources_ensure(ctx)||!wood_definition_sources_placement(ctx->definition_sources,id,&anchor)||anchor.placement_id!=placement_id||
       geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
       value.kind!=GEO_SOURCE_BOX||!reference_placement_frame(ctx,placement_id,&frame)||
       !wood_member_face_spec(WOOD_MEMBER_FACE_A0,&axis,&side)||!geo_box_face(&value.as.box,axis,side,&face))return false;
    GeoPoint2 first=geo_frame_project_uv(&frame,face.vertices[0]);GeoRect2 rect={first.u,first.v,first.u,first.v};
    for(size_t i=1;i<4;++i){GeoPoint2 point=geo_frame_project_uv(&frame,face.vertices[i]);
        rect.min_u=coord_min(rect.min_u,point.u);rect.max_u=coord_max(rect.max_u,point.u);
        rect.min_v=coord_min(rect.min_v,point.v);rect.max_v=coord_max(rect.max_v,point.v);}
    *out=rect;return true;
}
static void reference_region_geometry(SpaceBoundarySurface *to,const GeoRegionView *from)
{
    to->outline.count=from->outline.count;memcpy(to->outline.v,from->outline.v,from->outline.count*sizeof *from->outline.v);to->hole_count=from->hole_count;
    for(size_t h=0;h<from->hole_count;++h){to->holes[h].count=from->holes[h].count;memcpy(to->holes[h].v,from->holes[h].v,from->holes[h].count*sizeof *from->holes[h].v);}
}
static bool reference_region_view_fits(const GeoRegionView *view)
{
    if(!view||view->outline.count>POLY_MAX_VERTICES||(view->outline.count&&!view->outline.v)||
       view->hole_count>POLY_MAX_HOLES||(view->hole_count&&!view->holes))return false;
    for(size_t h=0;h<view->hole_count;++h)
        if(view->holes[h].count>POLY_MAX_VERTICES||(view->holes[h].count&&!view->holes[h].v))return false;
    return true;
}
/* Compose host identity, geometry and W policy from one actual candidate.
 * The boundary view is selected after the returned placement definition. */
static bool reference_host_read(ReferenceEval *ctx,uint32_t id,PlacementSurface *placement,
    SpaceBoundarySurface *boundary,const SpaceBoundarySurface **view)
{
    PlacementSurface actual;SpaceBoundarySurface region={0};bool has_boundary=false;
    if(!ctx||!placement||!boundary||!view||!app_placement_read(ctx->world,id,&actual))return false;
    if(ctx->use_current_values){
        const SpaceBoundarySurface *raw=app_placement_boundary(ctx->world,&actual,&region);
        if(raw&&raw!=&region)region=*raw;has_boundary=raw!=NULL;
    }else{
        GeoPlacementSourceKey key;GeoSourceValue geometry;GeoPlacementDefinitionHeader definition;
        if(!reference_sources_ensure(ctx)||!reference_placement_frame(ctx,id,&actual.frame)||
           geo_eval_source(ctx->sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,id,&key),
               GEO_DEPENDENCY_VALUE_REQUIRED,&geometry)!=GEO_SOURCE_OK||
           geometry.kind!=GEO_SOURCE_REGION_SET||geometry.as.regions.count>DP_COMPONENT_MAX||
           (geometry.as.regions.count&&!geometry.as.regions.regions)||
           !geo_placement_sources_definition_header(ctx->placement_sources,id,&definition))return false;
        for(size_t i=0;i<geometry.as.regions.count;++i)if(!reference_region_view_fits(&geometry.as.regions.regions[i]))return false;
        actual.boundary_id=0;actual.derived_fill_id=0;actual.derived_h=0;actual.component_count=0;
        memset(actual.components,0,sizeof actual.components);
        if(definition.domain==GEO_PLACEMENT_REGION_SET){
            WoodDerivedValue derived;
            if(!wood_finish_sources_read_derived(ctx->finish_sources,id,&derived)||
               !derived.derived_fill_id||derived.component_count!=geometry.as.regions.count)return false;
            actual.derived_fill_id=derived.derived_fill_id;actual.derived_h=derived.derived_h;actual.component_count=derived.component_count;
            memcpy(actual.components,derived.components,sizeof actual.components);
            for(size_t i=0;i<actual.component_count;++i)reference_region_geometry(&actual.components[i],&geometry.as.regions.regions[i]);
            has_boundary=actual.component_count!=0;if(has_boundary)region=actual.components[0];
        }else if(definition.domain==GEO_PLACEMENT_REGION_REF){
            if(geometry.as.regions.count!=1)return false;
            actual.boundary_id=definition.region_id;region.id=definition.region_id;
            reference_region_geometry(&region,&geometry.as.regions.regions[0]);
            if(!reference_boundary_policy(ctx,&region))return false;has_boundary=true;
        }else{
            if(geometry.as.regions.count!=1)return false;
            GeoLoop2View loop=geometry.as.regions.regions[0].outline;
            geo_loop_bbox(&loop,&actual.rect.min_u,&actual.rect.min_v,&actual.rect.max_u,&actual.rect.max_v);
        }
    }
    *placement=actual;*boundary=region;
    *view=has_boundary?(actual.derived_fill_id?&placement->components[0]:boundary):NULL;return true;
}
static bool reference_member_placement(ReferenceEval *ctx,PlacementSurface *placement,SpaceBoundarySurface *boundary)
{
    PlacementSurface actual;SpaceBoundarySurface region;const SpaceBoundarySurface *view;
    if(!reference_host_read(ctx,placement->id,&actual,&region,&view))return false;
    *placement=actual;if(boundary&&view)*boundary=*view;return true;
}
static bool reference_contact_facts(void *opaque,GeoEvalContext *evaluation,
    const WoodContactSourceRequest *request,WoodContactSourceFacts *out)
{
    ReferenceEval *ctx=opaque;if(evaluation!=ctx->sources)return false;
    PlacementSurface placement;SpaceBoundarySurface boundary;
    const SpaceBoundarySurface *b;
    if(!reference_host_read(ctx,request->placement_id,&placement,&boundary,&b))return false;
    bool deferred=!ctx->use_current_values;AppContactRawSnapshot raw[WORLD_MAX_TIMBERS];size_t visited=0;
    AppContactFacts facts;app_contact_facts_prepare(ctx->world,&placement,b,&facts,deferred?raw:NULL);
    out->region_count=facts.world.region_count;
    for(size_t i=0;i<out->region_count;++i)out->regions[i]=*facts.world.regions[i];
    out->member_count=facts.world.member_count;
    for(size_t i=0;i<out->member_count;++i){
        WoodContactMemberFact *fact=&out->members[i];*fact=facts.members[i];
        if(deferred){raw[i].pending=1;visited=i+1;}
        if(!fact->member->placed||fact->member==request->exclude)continue;
        uint32_t id=fact->member->id;GeoSourceValue value;
        if(!ctx->use_current_values){WoodMemberPlacementContact anchor;
            if(!wood_definition_sources_placement_contact(ctx->definition_sources,id,&anchor)){
                if(deferred)app_contact_raw_complete(&placement,raw,out->members,visited);return false;
            }
            fact->placement_id=anchor.placement_id;fact->order=anchor.order;
            fact->along_v=anchor.length_direction==GEO_DIRECTION_POS_V||anchor.length_direction==GEO_DIRECTION_NEG_V;
        }
        if(fact->placement_id!=request->placement_id){fact->footprint_valid=false;if(deferred)raw[i].pending=2;continue;}
        /* 若既有 callback 暫切 snapshot 模式，原 raw 有效性仍須在守門前可用。 */
        if(deferred&&ctx->use_current_values)app_contact_raw_restore(&placement,&raw[i],fact);
        if(ctx->use_current_values&&!fact->footprint_valid)continue;
        if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK){
            if(deferred)app_contact_raw_complete(&placement,raw,out->members,visited);return false;
        }
        WoodMember geometry=*fact->member;geometry.origin=value.as.box.frame.origin;
        geometry.axis_length=value.as.box.frame.axis_u;geometry.axis_a=value.as.box.frame.axis_v;geometry.axis_b=value.as.box.frame.normal;
        geometry.length=value.as.box.extent[0];geometry.size_a=value.as.box.extent[1];geometry.size_b=value.as.box.extent[2];
        GeoQuad3 face;fact->footprint_valid=wood_member_face_room(&geometry,WOOD_MEMBER_FACE_A0,&face);
        if(deferred&&raw[i].pending)raw[i].pending=fact->footprint_valid?0:2;
        if(fact->footprint_valid){
            GeoPoint2 first=geo_frame_project_uv(&placement.frame,face.vertices[0]);
            fact->footprint=(GeoRect2){first.u,first.v,first.u,first.v};
            for(size_t v=1;v<4;++v){GeoPoint2 point=geo_frame_project_uv(&placement.frame,face.vertices[v]);
                fact->footprint.min_u=coord_min(fact->footprint.min_u,point.u);fact->footprint.max_u=coord_max(fact->footprint.max_u,point.u);
                fact->footprint.min_v=coord_min(fact->footprint.min_v,point.v);fact->footprint.max_v=coord_max(fact->footprint.max_v,point.v);
            }
        }
    }
    if(deferred)app_contact_raw_complete(&placement,raw,out->members,visited);
    return true;
}
static ReferenceEval *app_reference_sources_for_world(const World *world)
{
    if(g_reference_active&&g_reference_active->world==world)return g_reference_active;
    if(g_active_app_candidate&&world==&g_active_app_candidate->after)
        return app_candidate_evaluation_state(g_active_app_candidate->control);
    return NULL;
}
static bool app_reference_host_read(const World *world,uint32_t id,PlacementSurface *placement,
    SpaceBoundarySurface *boundary,const SpaceBoundarySurface **view)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(ctx)return reference_host_read(ctx,id,placement,boundary,view);
    if(!app_placement_read(world,id,placement))return false;*view=app_placement_boundary(world,placement,boundary);return true;
}
static bool app_reference_member_anchor(const World *world,size_t i,WoodMemberPlacement *out)
{
    if(i>=world->wood.timber_count)return false;ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(!ctx||ctx->use_current_values){*out=world->wood.anchors[i];return true;}
    WoodMemberPlacement actual;
    if(!reference_sources_ensure(ctx)||!wood_definition_sources_placement(ctx->definition_sources,world->wood.timbers[i].id,&actual))return false;
    actual.uv=world->wood.anchors[i].uv;*out=actual;return true;
}
static bool app_reference_member_footprint(const World *world,size_t i,uint32_t id,GeoRect2 *out)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(ctx)return reference_member_footprint(ctx,i,id,out);
    PlacementSurface placement;
    return i<world->wood.timber_count&&app_placement_read(world,id,&placement)&&
        timber_a0_footprint_uv(&placement,&world->wood.timbers[i],&world->wood.anchors[i],out);
}
static bool app_reference_member_geometry(const World *world,WoodMember *member,bool *from_source)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(!ctx||ctx->use_current_values){if(from_source)*from_source=false;return true;}
    uint32_t id=member->id;GeoSourceValue value;
    if(!reference_sources_ensure(ctx)||
       geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
       value.kind!=GEO_SOURCE_BOX)return false;
    member->origin=value.as.box.frame.origin;member->axis_length=value.as.box.frame.axis_u;
    member->axis_a=value.as.box.frame.axis_v;member->axis_b=value.as.box.frame.normal;
    member->length=value.as.box.extent[0];member->size_a=value.as.box.extent[1];member->size_b=value.as.box.extent[2];
    if(from_source)*from_source=true;return true;
}
typedef struct {
    const World *world;ReferenceEval *evaluation;WoodContactWorld *target;
    WoodContactSourceFacts facts;
} AppReferenceContactResolve;
static bool app_reference_end_stops(void *opaque,bool along_v,const WoodMember *exclude,
    WoodStopFace *out,size_t capacity,size_t *count)
{
    AppReferenceContactResolve *context=opaque;
    WoodContactSourceRequest request={context->target->placement_id,along_v,exclude};
    if(!reference_contact_facts(context->evaluation,context->evaluation->sources,&request,&context->facts))return false;
    context->target->members=context->facts.members;context->target->member_count=context->facts.member_count;
    AppContactResolve source={context->world,context->target};
    return app_contact_resolve_stops(&source,along_v,exclude,out,capacity,count);
}
static bool app_reference_end_faces(const World *world,const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,const WoodMember *member,bool along_v,
    Coord span_lo,Coord span_hi,Coord cross_lo,Coord cross_hi,char *error,size_t capacity)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(!ctx||ctx->use_current_values)return timber_end_face_check(world,placement,boundary,member,along_v,
        span_lo,span_hi,cross_lo,cross_hi,error,capacity);
    AppContactFacts facts;app_contact_facts(world,placement,boundary,&facts);
    AppReferenceContactResolve source={.world=world,.evaluation=ctx,.target=&facts.world};
    /* W calls the resolver after its span-extension check. Refresh member
     * facts there so source failures do not replace an earlier policy error. */
    return wood_contact_end_faces_with_sources(&facts.world,member,along_v,span_lo,span_hi,cross_lo,cross_hi,
        app_reference_end_stops,&source,error,capacity);
}
static bool app_reference_validation_room(const World *world,uint32_t id,WoodRoomBounds *out)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);GeoEnclosure actual;
    const Space *space=world_find_space(world,id);if(!space)return false;
    if(ctx&&!ctx->use_current_values){
        if(!reference_sources_ensure(ctx)||!geo_enclosure_sources_value(ctx->enclosure_sources,id,&actual,NULL))return false;
        space=&actual;
    }
    WoodRoomBounds value;
    for(size_t axis=0;axis<3;++axis){value.min[axis]=space->min[axis];value.max[axis]=space->max[axis];}
    *out=value;return true;
}
static bool app_reference_validation_obstacle(const World *world,bool column,size_t i,WoodSolidObstacle *out)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);WoodSolidObstacle value;
    if(column){
        if(i>=world->wood.column_count)return false;WoodColumn actual;const WoodColumn *box=&world->wood.columns[i];
        if(ctx&&!ctx->use_current_values){if(!reference_sources_ensure(ctx)||!wood_definition_sources_column(ctx->definition_sources,box->id,&actual))return false;box=&actual;}
        value=(WoodSolidObstacle){box->id,box->space_id,{box->x_lo,box->y_lo,box->z_lo},{box->x_hi,box->y_hi,box->z_hi}};
    }else{
        if(i>=world->wood.beam_count)return false;WoodBeam actual;const WoodBeam *box=&world->wood.beams[i];
        if(ctx&&!ctx->use_current_values){if(!reference_sources_ensure(ctx)||!wood_definition_sources_beam(ctx->definition_sources,box->id,&actual))return false;box=&actual;}
        value=(WoodSolidObstacle){box->id,box->space_id,{box->x_lo,box->y_lo,box->z_lo},{box->x_hi,box->y_hi,box->z_hi}};
    }
    *out=value;return true;
}
static bool reference_engineering_owned(const World *world,uint32_t id)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    return ctx?reference_eng_owned(ctx,id):assembly_owned(world,id);
}
static bool app_contact_sources_collect(const World *world,uint32_t placement,bool along_v,
    const WoodMember *exclude,WoodStopFace *out,size_t capacity,bool *handled,size_t *count)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    *handled=ctx&&!ctx->use_current_values;if(!*handled)return false;
    WoodContactSourceRequest request={placement,along_v,exclude};
    if(reference_sources_ensure(ctx)&&wood_contact_sources_collect(ctx->contact_sources,&request,out,capacity,count))return true;
    ctx->source_failure=true;if(!g_revalidate_error[0])set_revalidate_error("I8: ordered contact source evaluation failed");return false;
}
static bool app_reference_sources_valid(const World *world)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(!ctx)return true;
    if(ctx->source_failure)return false;
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return true;
    return app_world_candidate_version_inventory(g_active_app_candidate,ctx);
}
static bool reference_sp_bind(ReferenceEval *ctx,WoodSectionProfileContext *profiles)
{
    if(!ctx||!ctx->section_profile_sources)return false;
    profiles->user=ctx;profiles->resolve_dimension=reference_sp_dimension;profiles->live_host=reference_sp_host;
    wood_engineering_sources_bind(ctx->engineering_sources,&profiles->engineering);
    return wood_sp_sources_bind(ctx->section_profile_sources,profiles);
}
static bool app_section_profile_sources_bind(const World *world,WoodSectionProfileContext *profiles)
{
    if(!g_active_app_candidate||world!=&g_active_app_candidate->after)return false;
    ReferenceEval *ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
    return reference_sp_bind(ctx,profiles);
}
static bool reference_named_quantity(ReferenceEval *ctx,const char *name,Coord *out)
{
    if(!name||!reference_sources_ensure(ctx))return false;
    GeoSourceValue value;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_NAMED,name,strlen(name)},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.quantity.num;return true;
}
static bool reference_member_dimension(ReferenceEval *ctx,uint32_t id,bool b,Coord *out)
{
    int index=reference_timber_index(ctx->world,id);if(index<0)return false;
    const Timber *member=&ctx->world->wood.timbers[index];
    if(!ctx->use_current_values&&!app_assembly_saved_dimensions(ctx->world,id)){
        bool owned;if(!reference_member_owned(ctx,id,&owned))return false;
        if(owned){
            GeoCoord width,depth;if(!wood_assembly_sources_owned_dimensions(ctx->assembly_sources,id,&width,&depth))return false;
            *out=b?depth:width;return true;
        }
        WoodEngineeringContext engineering=app_eng_context(ctx->world);
        wood_engineering_sources_bind(ctx->engineering_sources,&engineering);
        EngTarget target={1,id,0,b?1:0};const EngBinding *binding=wood_eng_binding(&engineering,&target);
        if(binding)return wood_eng_effective(&engineering,binding,out,NULL,0);
        return wood_definition_sources_dimension(ctx->definition_sources,id,b,out);
    }
    *out=b?member->size_b:member->size_a;return true;
}
static bool reference_datum_position(ReferenceEval *ctx,size_t i,GeoAxisPosition *out)
{
    const GeoDatum *datum=geo_datums_at(&ctx->world->geo.datum_planes,i);
    if(!datum||!reference_sources_ensure(ctx))return false;
    uint32_t id=datum->id;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_DATUM,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_AXIS_POSITION||
        value.as.position.context.has_placement||value.as.position.context.axis<0||value.as.position.context.axis>2)return false;
    if(out)*out=value.as.position;return true;
}
static bool reference_eval_datum(ReferenceEval *ctx,size_t i)
{return reference_datum_position(ctx,i,NULL);}
static bool reference_guide_position(ReferenceEval *ctx,size_t i,GeoAxisPosition *out)
{
    if(i>=geo_guides_count(&ctx->world->geo.guide_lines)||!reference_sources_ensure(ctx))return false;
    uint32_t id=geo_guides_at(&ctx->world->geo.guide_lines,i)->id;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_GUIDE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_AXIS_POSITION||
        !value.as.position.context.has_placement||value.as.position.context.axis<0||value.as.position.context.axis>1)return false;
    ctx->guide_values[i]=value.as.position;ctx->guide_values_valid[i]=true;
    /* reference_rebuild clears resolved, but a guide already memoized in this
     * candidate graph (assembly generation reads member guides first) never
     * re-runs the provider that sets it. Restore only that flag, and only when
     * the stored offset is this returned value; any other cache stays as is. */
    if(!ctx->use_current_values){const GeoGuide *stored=geo_guides_at(&ctx->world->geo.guide_lines,i);
        if(stored&&!stored->resolved&&stored->offset==value.as.position.coordinate){GeoGuide actual=*stored;actual.resolved=true;
            if(!geo_guides_put(&ctx->world->geo.guide_lines,&actual))return false;}}
    if(out)*out=value.as.position;return true;
}
static bool reference_eval_guide(ReferenceEval *ctx,size_t i)
{return reference_guide_position(ctx,i,NULL);}
static bool reference_eval_timber_relation(ReferenceEval *ctx,size_t i,GeoDependencyKind relation)
{
    if(i>=ctx->world->wood.timber_count||!reference_sources_ensure(ctx))return false;
    Timber *t=&ctx->world->wood.timbers[i];uint32_t id=t->id;GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},relation,&value);
    if(status!=GEO_SOURCE_OK){
        if(!ctx->wanted[i]||status==GEO_SOURCE_CYCLE)
            return reference_issue(t->id,"I9/I7","acyclic placed dependencies","missing placement or cyclic reference");
        return false;
    }
    t->origin=value.as.box.frame.origin;t->axis_length=value.as.box.frame.axis_u;
    t->axis_a=value.as.box.frame.axis_v;t->axis_b=value.as.box.frame.normal;
    t->length=value.as.box.extent[0];t->size_a=value.as.box.extent[1];t->size_b=value.as.box.extent[2];
    t->placed=true;return true;
}
static bool reference_eval_timber(ReferenceEval *ctx,size_t i)
{return reference_eval_timber_relation(ctx,i,GEO_DEPENDENCY_VALUE_REQUIRED);}
static bool reference_quantity(ReferenceEval *ctx,const GuideLine *g,const char *text,Coord *out)
{
    if(!text||strlen(text)>=REF_EXPR_MAX||!reference_sources_ensure(ctx))return false;
    AppReferenceSourceKey key;memset(&key,0,sizeof key);
    if(g){key.has_context=true;key.placement=g->placement_id;key.guide_id=g->id;key.direction=g->direction;}
    memcpy(key.expression,text,strlen(text)+1);GeoSourceValue value;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_REFERENCE,&key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.kind==GEO_SOURCE_QUANTITY?value.as.quantity.num:value.as.position.coordinate;return true;
}
static bool reference_parameter_quantity(ReferenceEval *ctx,ParameterRef ref,GeoQuantity *out)
{
    /* This legacy expression slot still accepts dimension fields only. The K
     * provider itself supports all parameter field types and owns AST edges. */
    if(!parameter_value(ctx->world,ref,out)||!reference_sources_ensure(ctx))return false;
    GeoParameterError issue;
    if(!geo_parameter_sources_value(ctx->parameter_sources,ref,out,&issue))return parameter_kernel_error(ctx->world,&issue);
    return true;
}
