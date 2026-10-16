/* H binds every resolver to the exact ReferenceEval candidate. K sees opaque
 * keys and typed outputs; legacy token parsing remains in reference_quantity_raw. */
enum { APP_SOURCE_GUIDE=1, APP_SOURCE_MEMBER_POSE, APP_SOURCE_REFERENCE, APP_SOURCE_PARAMETER };
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
{for(size_t i=0;i<geo_guides_count(&world->guide_lines);++i)if(geo_guides_values(&world->guide_lines)[i].id==id)return (int)i;return -1;}
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
static bool reference_source_describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *descriptor)
{
    ReferenceEval *ctx=opaque;World *world=ctx->world;uint32_t id;
    memset(descriptor,0,sizeof *descriptor);descriptor->unit=GEO_UNIT_LENGTH;
    if(source->provider==APP_SOURCE_GUIDE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_source_guide_index(world,id);if(i<0)return false;
        const GuideLine *g=&geo_guides_values(&world->guide_lines)[i];
        descriptor->kind=GEO_SOURCE_AXIS_POSITION;
        descriptor->context=(GeoSourceContext){true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1};
        /* Datum guides acquire their axis during evaluation. Resolve the neutral
         * intersection here without changing the old diagnostic/mutation point. */
        if(g->source==GUIDE_DATUM&&!ctx->use_current_values){
            const GeoDatum *d=geo_datums_find(&world->datum_planes,g->datum_id);
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
        descriptor->context=(GeoSourceContext){true,world->anchors[i].placement_id,-1};return true;
    }
    if(source->provider==APP_SOURCE_REFERENCE){
        AppReferenceSourceKey key;if(!reference_source_context(source,&key))return false;
        descriptor->retry_failure=true;
        descriptor->kind=reference_source_is_dimension(key.expression)?GEO_SOURCE_QUANTITY:GEO_SOURCE_AXIS_POSITION;
        descriptor->context=(GeoSourceContext){key.has_context,key.placement,key.direction==GUIDE_ALONG_V?0:1};return true;
    }
    if(source->provider==APP_SOURCE_PARAMETER){
        if(source->key_size!=2*sizeof(uint32_t))return false;
        descriptor->kind=GEO_SOURCE_QUANTITY;descriptor->retry_failure=true;
        /* The existing H reference adapter accepts dimension fields only. */
        return true;
    }
    return false;
}
static bool reference_source_evaluate(void *opaque,GeoEvalContext *evaluation,const GeoSourceRef *source,GeoSourceValue *value)
{
    ReferenceEval *ctx=opaque;World *world=ctx->world;uint32_t id;
    if(evaluation!=ctx->sources)return false;
    if(source->provider==APP_SOURCE_GUIDE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_source_guide_index(world,id);
        if(i<0||!reference_compute_guide(ctx,(size_t)i))return false;
        const GuideLine *g=&geo_guides_values(&world->guide_lines)[i];value->kind=GEO_SOURCE_AXIS_POSITION;
        value->as.position=(GeoAxisPosition){g->offset,{true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1}};return true;
    }
    if(source->provider==APP_SOURCE_MEMBER_POSE){
        if(!reference_source_id(source,&id))return false;
        int i=reference_timber_index(world,id);
        if(i<0||!reference_compute_timber(ctx,(size_t)i))return false;
        const Timber *t=&world->timbers[i];value->kind=GEO_SOURCE_BOX;
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
    if(source->provider==APP_SOURCE_PARAMETER){
        if(source->key_size!=2*sizeof(uint32_t))return false;
        uint32_t ids[2];memcpy(ids,source->key,sizeof ids);value->kind=GEO_SOURCE_QUANTITY;
        return parameter_value(world,(ParameterRef){true,ids[0],ids[1]},&value->as.quantity);
    }
    return false;
}
static bool reference_sources_ensure(ReferenceEval *ctx)
{
    if(ctx->sources)return true;
    /* The lifetime itself is a unique in-process candidate evaluation identity.
     * The host's persistent revision is attached by its publish coordinator. */
    ctx->sources=geo_eval_create((uint64_t)(uintptr_t)ctx,0);if(!ctx->sources)return false;
    static const char *const names[]={"app.guide","woodworking.member.pose","app.legacy-reference","core.parameter.field"};
    for(uint32_t token=APP_SOURCE_GUIDE;token<=APP_SOURCE_PARAMETER;++token){
        GeoSourceProvider provider={token,names[token-1],"geo261-native-source/1",ctx,reference_source_describe,reference_source_evaluate};
        if(!geo_eval_register(ctx->sources,&provider)){reference_sources_dispose(ctx);return false;}
    }
    return true;
}
static bool reference_eval_guide(ReferenceEval *ctx,size_t i)
{
    if(i>=geo_guides_count(&ctx->world->guide_lines)||!reference_sources_ensure(ctx))return false;
    uint32_t id=geo_guides_at(&ctx->world->guide_lines,i)->id;GeoSourceValue value;
    return geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_GUIDE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK;
}
static bool reference_eval_timber_relation(ReferenceEval *ctx,size_t i,GeoDependencyKind relation)
{
    if(i>=ctx->world->timber_count||!reference_sources_ensure(ctx))return false;
    Timber *t=&ctx->world->timbers[i];uint32_t id=t->id;GeoSourceValue value;
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
    if(!reference_sources_ensure(ctx))return false;
    uint32_t ids[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    if(geo_eval_source(ctx->sources,(GeoSourceRef){APP_SOURCE_PARAMETER,ids,sizeof ids},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.quantity;return true;
}
