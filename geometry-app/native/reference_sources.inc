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
        descriptor->kind=GEO_SOURCE_AXIS_POSITION;descriptor->context.axis=datum->axis;return true;
    }
    if(source->provider==APP_SOURCE_GUIDE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_source_guide_index(world,id);if(i<0)return false;
        const GuideLine *g=&geo_guides_values(&world->geo.guide_lines)[i];
        descriptor->kind=GEO_SOURCE_AXIS_POSITION;
        descriptor->context=(GeoSourceContext){true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1};
        /* Datum guides acquire their axis during evaluation. Resolve the neutral
         * intersection here without changing the old diagnostic/mutation point. */
        if(g->source==GUIDE_DATUM&&!ctx->use_current_values){
            const GeoDatum *d=geo_datums_find(&world->geo.datum_planes,g->datum_id);
            const PlacementSurface *p=world_find_placement(world,g->placement_id);
            GeoDatumIntersection intersection;
            if(d&&p&&geo_datum_intersection(d,&p->frame,&intersection)==GEO_DATUM_INTERSECTION_OK)
                descriptor->context.axis=(int)intersection.coordinate_axis;
        }
        return true;
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
    ReferenceEval *ctx=opaque;if(!app_sp_live_host(ctx->world,id,frame,region,derived))return false;if(*derived)return true;
    GeoPlacementSourceKey key;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_FRAME,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *frame=value.as.frame;
    if(geo_eval_source(ctx->sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.as.regions.count!=1)return false;
    const GeoRegionView *view=&value.as.regions.regions[0];region->outline.count=view->outline.count;
    memcpy(region->outline.v,view->outline.v,view->outline.count*sizeof *view->outline.v);region->hole_count=view->hole_count;
    for(size_t h=0;h<view->hole_count;++h){region->holes[h].count=view->holes[h].count;memcpy(region->holes[h].v,view->holes[h].v,view->holes[h].count*sizeof *view->holes[h].v);}
    const GeoPlacementDefinition *placement=geo_placements_find(&ctx->world->geo.placement_data,id);
    return !placement||placement->domain!=GEO_PLACEMENT_REGION_REF||reference_boundary_policy(ctx,region);
}
static bool reference_placement_binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{
    ReferenceEval *ctx=opaque;if(ctx->use_current_values)return false;
    const PlacementSurface *p=world_find_placement(ctx->world,id);if(!p||!p->derived_fill_id)return false;
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
        engineering->resolve_source=NULL;engineering->resolve_binding=NULL;engineering->source_named=NULL;
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
    if(!app_placement_read(ctx->world,id,&placement))return false;
    const SpaceBoundarySurface *b=app_placement_boundary(ctx->world,&placement,&boundary);
    if(!reference_member_placement(ctx,&placement,b?&boundary:NULL))return false;
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
{return app_asm_guide(((ReferenceEval *)opaque)->world,id,out);}
static bool reference_asm_member(void *opaque,uint32_t id,WoodAssemblyMember *out)
{return app_asm_member(((ReferenceEval *)opaque)->world,id,out);}
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
    WoodEngineeringContext engineering=app_eng_context(ctx->world);
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
static void reference_region_geometry(SpaceBoundarySurface *to,const GeoRegionView *from)
{
    to->outline.count=from->outline.count;memcpy(to->outline.v,from->outline.v,from->outline.count*sizeof *from->outline.v);to->hole_count=from->hole_count;
    for(size_t h=0;h<from->hole_count;++h){to->holes[h].count=from->holes[h].count;memcpy(to->holes[h].v,from->holes[h].v,from->holes[h].count*sizeof *from->holes[h].v);}
}
static bool reference_member_placement(ReferenceEval *ctx,PlacementSurface *placement,SpaceBoundarySurface *boundary)
{
    if(!reference_placement_frame(ctx,placement->id,&placement->frame))return false;
    GeoPlacementSourceKey key;GeoSourceValue value;
    if(geo_eval_source(ctx->sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,placement->id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    if(placement->derived_fill_id){
        if(!ctx->use_current_values){WoodDerivedValue derived;
            if(!wood_finish_sources_read_derived(ctx->finish_sources,placement->id,&derived))return false;
            placement->derived_h=derived.derived_h;placement->component_count=derived.component_count;
            memcpy(placement->components,derived.components,sizeof placement->components);
        }
        if(value.as.regions.count!=placement->component_count)return false;
        for(size_t i=0;i<value.as.regions.count;++i)reference_region_geometry(&placement->components[i],&value.as.regions.regions[i]);
    }else if(boundary){if(value.as.regions.count!=1)return false;reference_region_geometry(boundary,&value.as.regions.regions[0]);if(!reference_boundary_policy(ctx,boundary))return false;}
    else{
        if(value.as.regions.count!=1)return false;GeoLoop2View loop=value.as.regions.regions[0].outline;
        geo_loop_bbox(&loop,&placement->rect.min_u,&placement->rect.min_v,&placement->rect.max_u,&placement->rect.max_v);
    }
    return true;
}
static bool reference_contact_facts(void *opaque,GeoEvalContext *evaluation,
    const WoodContactSourceRequest *request,WoodContactSourceFacts *out)
{
    ReferenceEval *ctx=opaque;if(evaluation!=ctx->sources)return false;
    PlacementSurface placement;SpaceBoundarySurface boundary;
    if(!app_placement_read(ctx->world,request->placement_id,&placement))return false;
    const SpaceBoundarySurface *b=app_placement_boundary(ctx->world,&placement,&boundary);
    if(!reference_member_placement(ctx,&placement,b?&boundary:NULL))return false;
    AppContactFacts facts;app_contact_facts(ctx->world,&placement,b,&facts);
    out->region_count=facts.world.region_count;
    for(size_t i=0;i<out->region_count;++i)out->regions[i]=*facts.world.regions[i];
    out->member_count=facts.world.member_count;
    for(size_t i=0;i<out->member_count;++i){
        WoodContactMemberFact *fact=&out->members[i];*fact=facts.members[i];
        if(!fact->member->placed||fact->member==request->exclude)continue;
        uint32_t id=fact->member->id;GeoSourceValue value;
        if(!ctx->use_current_values){WoodMemberPlacement anchor;
            if(!wood_definition_sources_placement(ctx->definition_sources,id,&anchor))return false;
            fact->placement_id=anchor.placement_id;fact->order=anchor.order;
            fact->along_v=anchor.length_direction==GEO_DIRECTION_POS_V||anchor.length_direction==GEO_DIRECTION_NEG_V;
        }
        if(fact->placement_id!=request->placement_id||!fact->footprint_valid)continue;
        if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
        WoodMember geometry=*fact->member;geometry.origin=value.as.box.frame.origin;
        geometry.axis_length=value.as.box.frame.axis_u;geometry.axis_a=value.as.box.frame.axis_v;geometry.axis_b=value.as.box.frame.normal;
        geometry.length=value.as.box.extent[0];geometry.size_a=value.as.box.extent[1];geometry.size_b=value.as.box.extent[2];
        GeoQuad3 face;fact->footprint_valid=wood_member_face_room(&geometry,WOOD_MEMBER_FACE_A0,&face);
        if(fact->footprint_valid){
            GeoPoint2 first=geo_frame_project_uv(&placement.frame,face.vertices[0]);
            fact->footprint=(GeoRect2){first.u,first.v,first.u,first.v};
            for(size_t v=1;v<4;++v){GeoPoint2 point=geo_frame_project_uv(&placement.frame,face.vertices[v]);
                fact->footprint.min_u=coord_min(fact->footprint.min_u,point.u);fact->footprint.max_u=coord_max(fact->footprint.max_u,point.u);
                fact->footprint.min_v=coord_min(fact->footprint.min_v,point.v);fact->footprint.max_v=coord_max(fact->footprint.max_v,point.v);
            }
        }
    }
    return true;
}
static ReferenceEval *app_reference_sources_for_world(const World *world)
{
    if(g_reference_active&&g_reference_active->world==world)return g_reference_active;
    if(g_active_app_candidate&&world==&g_active_app_candidate->after)
        return app_candidate_evaluation_state(g_active_app_candidate->control);
    return NULL;
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
{ReferenceEval *ctx=app_reference_sources_for_world(world);return !ctx||!ctx->source_failure;}
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
    if(!ctx->use_current_values){
        if(assembly_owned(ctx->world,id)){
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
