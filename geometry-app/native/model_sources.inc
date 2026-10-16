/* Internal H transport over one validated candidate. The coverage declaration
 * is deliberately incomplete until every definition edge is in the K graph. */
enum { MODEL_SOURCE_PROVIDER=5 };
typedef struct ModelSourceItem ModelSourceItem;
struct ModelSourceItem {
    char key[192];
    char owned_name[GEO_PARAMETER_NAME_MAX];
    const char *kind,*slot,*name,*quantity_type;
    uint32_t id,member_id;
    bool has_member,local;
    const char *owner_namespace;
    unsigned char owner_key[5];
    GeoSourceDescriptor descriptor;
    GeoSourceValue value;
    GeoRegionView *regions;
    GeoLoop2View *holes;
    const BoundaryVertexKeys **vertex_keys;
    GeoRegionKeys *owned_vertex_keys;
    GeoPoint2 rectangle[4];
    size_t region_count;
};
typedef struct {
    ReferenceEval reference;
    ModelSourceItem **items;
    size_t count,capacity;
    ProfileMember *profile_members;
    ProfileRun *profile_runs;
    size_t profile_member_count,profile_run_count;
} ModelSources;

static ModelSourceItem *model_source_item(ModelSources *state,const GeoSourceRef *ref)
{
    if(ref->provider!=MODEL_SOURCE_PROVIDER)return NULL;
    for(size_t i=0;i<state->count;++i)
        if(strlen(state->items[i]->key)==ref->key_size&&!memcmp(state->items[i]->key,ref->key,ref->key_size))return state->items[i];
    return NULL;
}
static const char *model_source_quantity_type(ModelSources *state,const GeoSourceRef *ref,const GeoSourceValue *value)
{
    ModelSourceItem *item=model_source_item(state,ref);
    if(item&&item->quantity_type)return item->quantity_type;
    if(ref->provider==APP_SOURCE_PARAMETER&&ref->key_size==2*sizeof(uint32_t)){
        uint32_t ids[2];memcpy(ids,ref->key,sizeof ids);
        for(size_t i=0;i<state->count;++i){const ModelSourceItem *root=state->items[i];
            if(!strcmp(root->kind,"parameter")&&root->id==ids[0]&&root->member_id==ids[1])return root->quantity_type;
        }
        return NULL;
    }
    return value->as.quantity.unit==GEO_UNIT_LENGTH?"dimension":NULL;
}
static bool model_source_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{ModelSourceItem *item=model_source_item(opaque,ref);if(!item)return false;*out=item->descriptor;return true;}
/* An optional ledger is an authored identity source. Preserve absence and
 * decode only its actual returned bytes after the root's geometry succeeds. */
static bool model_source_region_keys(ModelSources *state,ModelSourceItem *item,const GeoSourceValue *geometry)
{
    GeoPlacementDefinition placement;
    if(!geo_placement_sources_definition(state->reference.placement_sources,item->id,&placement))return false;
    if(placement.domain!=GEO_PLACEMENT_REGION_REF||!geo_region_keys_find(&state->reference.world->geo.region_data,placement.region_id)){
        if(item->region_count)item->vertex_keys[0]=NULL;return true;
    }
    uint32_t region_id=placement.region_id;GeoRegionKeySourceKey key;GeoSourceValue ledger;
    if(geo_eval_source(state->reference.sources,geo_region_key_source_ref(APP_SOURCE_REGION_KEYS,GEO_REGION_KEY_SOURCE_LEDGER,region_id,0,0,&key),
        GEO_DEPENDENCY_DEFINITION_REQUIRED,&ledger)!=GEO_SOURCE_OK||ledger.kind!=GEO_SOURCE_DEFINITION||!ledger.as.definition.schema||
        strcmp(ledger.as.definition.schema,"geometry.region-key-ledger/1"))return false;
    GeoRegionKeys decoded;
    if(!geo_region_key_ledger_decode(ledger.as.definition.content,ledger.as.definition.content_size,&decoded)||decoded.boundary_id!=region_id||
        geometry->kind!=GEO_SOURCE_REGION_SET||geometry->as.regions.count!=1||!geometry->as.regions.regions)return false;
    const GeoRegionView *region=geometry->as.regions.regions;
    if(region->hole_count>GEO_REGION_MAX_HOLES||(region->hole_count&&!region->holes)||
        region->outline.count>GEO_LOOP_MAX_VERTICES||(region->outline.count&&!region->outline.v))return false;
    GeoRegionDefinition shape={0};shape.id=region_id;shape.outline.count=region->outline.count;shape.hole_count=region->hole_count;
    for(size_t h=0;h<region->hole_count;++h){if(region->holes[h].count>GEO_LOOP_MAX_VERTICES||(region->holes[h].count&&!region->holes[h].v))return false;shape.holes[h].count=region->holes[h].count;}
    if(!geo_region_keys_valid(&shape,&decoded))return false;
    GeoRegionKeys *owned=item->owned_vertex_keys?item->owned_vertex_keys:malloc(sizeof *owned);if(!owned)return false;
    const BoundaryVertexKeys **keys=item->vertex_keys?item->vertex_keys:calloc(1,sizeof *keys);
    if(!keys){if(!item->owned_vertex_keys)free(owned);return false;}
    item->owned_vertex_keys=owned;item->vertex_keys=keys;if(!item->region_count)item->region_count=1;
    *item->owned_vertex_keys=decoded;item->vertex_keys[0]=item->owned_vertex_keys;return true;
}
static bool model_source_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    ModelSources *state=opaque;ModelSourceItem *item=model_source_item(state,ref);
    if(!item||ctx!=state->reference.sources)return false;
    if(!strcmp(item->kind,"timber")){
        uint32_t id=item->id;
        return geo_eval_source(ctx,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    }
    if(!strcmp(item->kind,"spec"))
        return geo_eval_source(ctx,(GeoSourceRef){APP_SOURCE_NAMED,item->name,strlen(item->name)},GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    if(!strcmp(item->kind,"parameter")){
        uint32_t ids[]={item->id,item->member_id};GeoSourceValue value,definition;GeoParameterDefinitionKey key;GeoParameterField field;
        if(geo_eval_source(ctx,(GeoSourceRef){APP_SOURCE_PARAMETER,ids,sizeof ids},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
           geo_eval_source(ctx,geo_parameter_definition_source_ref(APP_SOURCE_PARAMETER_DEFINITION,GEO_PARAMETER_DEFINITION_FIELD,
               item->id,item->member_id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK||
           definition.kind!=GEO_SOURCE_DEFINITION||!definition.as.definition.schema||
           strcmp(definition.as.definition.schema,"geometry.parameter-field/1")||
           !geo_parameter_field_definition_decode(definition.as.definition.content,definition.as.definition.content_size,&field)||
           field.parameter_id!=item->id||field.id!=item->member_id||value.kind!=GEO_SOURCE_QUANTITY||
           value.as.quantity.unit!=(field.type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR))return false;
        memcpy(item->owned_name,field.name,sizeof item->owned_name);item->name=item->owned_name;
        item->quantity_type=field.type==GEO_PARAMETER_COUNT?"count":field.type==GEO_PARAMETER_RATIO?"ratio":"dimension";
        *out=value;return true;
    }
    if(!strcmp(item->kind,"placement")){
        GeoPlacementSourceKey key;GeoPlacementSourceKind kind=!strcmp(item->slot,"placement.frame")?GEO_PLACEMENT_SOURCE_FRAME:GEO_PLACEMENT_SOURCE_REGIONS;
        GeoSourceValue value;
        if(geo_eval_source(ctx,geo_placement_source_ref(APP_SOURCE_PLACEMENT,kind,item->id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
            (kind==GEO_PLACEMENT_SOURCE_REGIONS&&!model_source_region_keys(state,item,&value)))return false;
        *out=value;return true;
    }
    if(!strcmp(item->kind,"column")||!strcmp(item->kind,"beam")){
        WoodFinishSourceKey key;WoodFinishSourceKind kind=!strcmp(item->kind,"column")?WOOD_FINISH_SOURCE_COLUMN_BOX:WOOD_FINISH_SOURCE_BEAM_BOX;
        return geo_eval_source(ctx,wood_finish_source_ref(APP_SOURCE_FINISH,kind,item->id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    }
    if(!strcmp(item->kind,"profile-run")){
        WoodSectionProfileSourceKind kind;uint32_t id=item->id;
        if(!strcmp(item->slot,"profile.length"))kind=WOOD_SP_SOURCE_RUN_LENGTH;
        else if(!strcmp(item->slot,"profile.region")){
            kind=item->has_member?WOOD_SP_SOURCE_MEMBER_REGION:WOOD_SP_SOURCE_RUN_REGION;
            if(item->has_member)id=item->member_id;
        }else kind=WOOD_SP_SOURCE_RUN_FRAME;
        WoodSectionProfileSourceKey key;
        GeoSourceRef source=wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,kind,id,&key);
        if(kind==WOOD_SP_SOURCE_RUN_FRAME&&item->local){
            /* An unplaced run has a local display frame, but no world frame.
             * Keep its unevaluated placement identity in the real graph. */
            if(geo_eval_depend(ctx,source,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
            *out=item->value;return true;
        }
        return geo_eval_source(ctx,source,GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    }
    *out=item->value;return true;
}
static void model_sources_free(ModelSources *state)
{
    reference_sources_dispose(&state->reference);
    for(size_t i=0;i<state->count;++i){free(state->items[i]->regions);free(state->items[i]->holes);free(state->items[i]->vertex_keys);free(state->items[i]->owned_vertex_keys);free(state->items[i]);}
    free(state->items);free(state->profile_members);free(state->profile_runs);memset(state,0,sizeof *state);
}
static ModelSourceItem *model_sources_add(ModelSources *state,const char *kind,uint32_t id,const char *slot,
    uint32_t member,bool has_member,GeoSourceValueKind type)
{
    if(state->count==state->capacity){
        size_t cap=state->capacity?state->capacity*2:32;
        ModelSourceItem **items=realloc(state->items,cap*sizeof *items);if(!items)return NULL;
        state->items=items;state->capacity=cap;
    }
    ModelSourceItem *item=calloc(1,sizeof *item);if(!item)return NULL;
    item->kind=kind;item->id=id;item->slot=slot;item->member_id=member;item->has_member=has_member;
    item->descriptor.kind=type;item->descriptor.unit=GEO_UNIT_LENGTH;item->descriptor.context.axis=-1;
    item->value.kind=type;
    snprintf(item->key,sizeof item->key,"%s:%u:%s:%s%u",kind,id,slot,has_member?"member:":"envelope:",member);
    state->items[state->count++]=item;return item;
}
static bool model_source_regions(ModelSourceItem *item,size_t count)
{
    item->region_count=count;
    if(count){
        item->regions=calloc(count,sizeof *item->regions);item->holes=calloc(count*POLY_MAX_HOLES,sizeof *item->holes);
        item->vertex_keys=calloc(count,sizeof *item->vertex_keys);
        if(!item->regions||!item->holes||!item->vertex_keys)return false;
    }
    item->value.as.regions=(GeoRegionSetView){item->regions,count};return true;
}
static void model_source_region(ModelSourceItem *item,size_t i,const PolygonLoop2 *outer,
    const PolygonLoop2 *holes,size_t count,const BoundaryVertexKeys *keys)
{
    item->regions[i]=(GeoRegionView){{outer->v,outer->count},item->holes+i*POLY_MAX_HOLES,count};
    for(size_t h=0;h<count;++h)item->holes[i*POLY_MAX_HOLES+h]=(GeoLoop2View){holes[h].v,holes[h].count};
    item->vertex_keys[i]=keys;
}
static void model_source_rectangle(ModelSourceItem *item,GeoRect2 rect)
{
    item->rectangle[0]=(GeoPoint2){rect.min_u,rect.min_v};item->rectangle[1]=(GeoPoint2){rect.max_u,rect.min_v};
    item->rectangle[2]=(GeoPoint2){rect.max_u,rect.max_v};item->rectangle[3]=(GeoPoint2){rect.min_u,rect.max_v};
    item->regions[0]=(GeoRegionView){{item->rectangle,4},NULL,0};
}
static bool model_sources_build(ModelSources *state,World *world)
{
    memset(state,0,sizeof *state);state->reference.world=world;
    if(!reference_sources_ensure(&state->reference))return false;
    GeoSourceProvider provider={MODEL_SOURCE_PROVIDER,"app.model-snapshot","geo261-model-snapshot/1",state,model_source_describe,model_source_evaluate};
    if(!geo_eval_register(state->reference.sources,&provider))return false;
    GeoParameterError parameter_error;
    if(!geo_parameter_sources_rebuild(state->reference.parameter_sources,&parameter_error))return parameter_kernel_error(world,&parameter_error);
    WoodEngineeringContext engineering=app_eng_context(world);char engineering_error[256];
    wood_engineering_sources_bind(state->reference.engineering_sources,&engineering);
    if(!wood_engineering_rebuild(&engineering,engineering_error,sizeof engineering_error))return false;
    WoodAssemblyContext assembly_context=app_asm_context(world);reference_assembly_context(&state->reference,&assembly_context);
    if(!wood_assembly_sources_bind(state->reference.assembly_sources,&assembly_context)||
        !wood_assembly_rebuild(&assembly_context,engineering_error,sizeof engineering_error))return false;
    WoodSectionProfileContext profiles_context=app_sp_context(world);
    if(!reference_sp_bind(&state->reference,&profiles_context)||
        !wood_sp_rebuild(&profiles_context,engineering_error,sizeof engineering_error))return false;
    WoodDerivedContext finish_context=app_dp_context(world);
    reference_derived_context(&state->reference,&finish_context);
    if(!wood_finish_sources_bind(state->reference.finish_sources,&finish_context)||
        !wood_fs_rebuild(&finish_context.finish,engineering_error,sizeof engineering_error)||
        !wood_pf_rebuild(&finish_context.finish)||!wood_dp_rebuild(&finish_context))return false;
    WoodGridContext grid_context=app_grid_context(world);reference_grid_context(&state->reference,&grid_context);
    if(!wood_grid_sources_bind(state->reference.grid_sources,&grid_context)||
        !wood_grid_systems_rebuild(&grid_context,engineering_error,sizeof engineering_error)||
        !wood_grid_bindings_rebuild(&grid_context,engineering_error,sizeof engineering_error))return false;
    if(!wood_assembly_generation_prepare(&assembly_context))return false;
    geo_guides_reset_resolved(&world->geo.guide_lines);
    for(size_t i=0;i<world->wood.timber_count;++i){state->reference.wanted[i]=world->wood.timbers[i].placed;world->wood.timbers[i].placed=false;}
    /* Re-evaluate through the actual source engine, preserving dependency order.
     * This process owns the candidate and exposes nothing until all roots pass. */
    if(!reference_eval_datums(&state->reference))return false;
    for(size_t i=0;i<world->wood.timber_count;++i)if(!reference_eval_timber(&state->reference,i))return false;
    for(size_t i=0;i<geo_guides_count(&world->geo.guide_lines);++i)if(!reference_eval_guide(&state->reference,i))return false;
    if(!wood_assembly_generation_check(&assembly_context)||!wood_assembly_sources_definitions(state->reference.assembly_sources))return false;
    if(!wood_engineering_sources_definitions(state->reference.engineering_sources)||
        !wood_engineering_sources_metadata(state->reference.engineering_sources)||
        !geo_version_sources_definitions(state->reference.version_sources)||
        !wood_sp_sources_complete(state->reference.section_profile_sources)||
        !geo_parameter_sources_definitions(state->reference.parameter_sources,&parameter_error)||
        !geo_linear_definition_sources_complete(state->reference.linear_definition_sources)||
        !app_enclosure_sources_complete(&state->reference)||!wood_definition_sources_complete(state->reference.definition_sources)||
        !wood_finish_sources_definitions(state->reference.finish_sources)||
        !geo_region_key_sources_definitions(state->reference.region_key_sources)||
        !wood_grid_sources_definitions(state->reference.grid_sources,engineering_error,sizeof engineering_error))return false;
    for(size_t i=0;i<geo_placements_count(&world->geo.placement_data);++i){
        const GeoPlacementDefinition *p=geo_placements_at(&world->geo.placement_data,i);
        ModelSourceItem *frame=model_sources_add(state,"placement",p->id,"placement.frame",0,false,GEO_SOURCE_FRAME);
        ModelSourceItem *region=model_sources_add(state,"placement",p->id,"placement.region",0,false,GEO_SOURCE_REGION_SET);
        if(!frame||!region)return false;
        frame->descriptor.context.has_placement=region->descriptor.context.has_placement=true;
        frame->descriptor.context.placement=region->descriptor.context.placement=p->id;frame->value.as.frame=p->frame;
        /* Placement roots obtain their geometry and optional identities during
         * evaluation. No raw domain view or ledger pointer is transported. */
        if(!model_source_regions(region,0))return false;
    }
    for(size_t i=0;i<world->wood.column_count+world->wood.beam_count;++i){
        bool column=i<world->wood.column_count;Coord xl,xh,yl,yh,zl,zh;uint32_t id;
        if(column){const RcColumn *b=&world->wood.columns[i];id=b->id;xl=b->x_lo;xh=b->x_hi;yl=b->y_lo;yh=b->y_hi;zl=b->z_lo;zh=b->z_hi;}
        else{const RcBeam *b=&world->wood.beams[i-world->wood.column_count];id=b->id;xl=b->x_lo;xh=b->x_hi;yl=b->y_lo;yh=b->y_hi;zl=b->z_lo;zh=b->z_hi;}
        ModelSourceItem *item=model_sources_add(state,column?"column":"beam",id,"solid.box",0,false,GEO_SOURCE_BOX);if(!item)return false;
        item->value.as.box=(GeoBox3){{{xl,yl,zl},{1,0,0},{0,1,0},{0,0,1}},{xh-xl,yh-yl,zh-zl}};
    }
    for(size_t i=0;i<world->wood.timber_count;++i){
        ModelSourceItem *item=model_sources_add(state,"timber",world->wood.timbers[i].id,"solid.box",0,false,GEO_SOURCE_BOX);if(!item)return false;
        item->descriptor.context=(GeoSourceContext){true,world->wood.anchors[i].placement_id,-1};
    }
    for(size_t i=0;i<geo_named_values_count(&world->geo.named_values);++i){
        const GeoNamedValue *spec=geo_named_values_at(&world->geo.named_values,i);
        ModelSourceItem *item=model_sources_add(state,"spec",0,"spec.value",0,false,GEO_SOURCE_QUANTITY);if(!item)return false;
        item->name=spec->name;snprintf(item->key,sizeof item->key,"spec:%s",spec->name);
        item->value.as.quantity=(GeoQuantity){spec->value,1,GEO_UNIT_LENGTH};
    }
    for(size_t i=0;i<geo_parameters_field_count(&world->geo.parameters);++i){
        const GeoParameterField *field=&geo_parameters_fields(&world->geo.parameters)[i];
        ModelSourceItem *item=model_sources_add(state,"parameter",field->parameter_id,"parameter.value",field->id,true,GEO_SOURCE_QUANTITY);if(!item)return false;
        item->descriptor.unit=field->value.unit;
    }
    const SectionProfileState *profiles=&world->wood.section_profiles;
    state->profile_member_count=profiles->member_count;state->profile_run_count=profiles->run_count;
    if(profiles->member_count){state->profile_members=calloc(profiles->member_count,sizeof *state->profile_members);if(!state->profile_members)return false;}
    if(profiles->run_count){state->profile_runs=calloc(profiles->run_count,sizeof *state->profile_runs);if(!state->profile_runs)return false;}
    for(size_t m=0;m<profiles->member_count;++m)
        if(!wood_sp_sources_member_definition(state->reference.section_profile_sources,profiles->members[m].id,&state->profile_members[m]))return false;
    for(size_t i=0;i<profiles->run_count;++i)
        if(!wood_sp_sources_run_definition(state->reference.section_profile_sources,profiles->runs[i].id,&state->profile_runs[i]))return false;
    for(size_t i=0;i<state->profile_run_count;++i){
        const ProfileRun *run=&state->profile_runs[i];SectionProfile actual_profile;
        if(!wood_sp_sources_profile_definition(state->reference.section_profile_sources,run->profile_id,&actual_profile))return false;
        const SectionProfile *profile=&actual_profile;
        GeoFrame frame=run->placed?run->frame:(GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};
        for(size_t m=0;m<=state->profile_member_count;++m){
            const ProfileMember *member=m?&state->profile_members[m-1]:NULL;
            if(member&&member->profile_id!=profile->id)continue;
            ModelSourceItem *f=model_sources_add(state,"profile-run",run->id,"profile.frame",member?member->id:0,member!=NULL,GEO_SOURCE_FRAME);
            ModelSourceItem *r=model_sources_add(state,"profile-run",run->id,"profile.region",member?member->id:0,member!=NULL,GEO_SOURCE_REGION_SET);
            ModelSourceItem *l=model_sources_add(state,"profile-run",run->id,"profile.length",member?member->id:0,member!=NULL,GEO_SOURCE_QUANTITY);
            if(!f||!r||!l||!model_source_regions(r,1))return false;
            f->local=r->local=l->local=!run->placed;f->value.as.frame=frame;l->value.as.quantity=(GeoQuantity){run->length,1,GEO_UNIT_LENGTH};
            if(member)model_source_rectangle(r,member->rect);else model_source_region(r,0,&profile->outline,NULL,0,NULL);
        }
    }
    for(size_t i=0;i<state->count;++i){ModelSourceItem *item=state->items[i];GeoSourceValue value;
        if(geo_eval_source(state->reference.sources,(GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    }
    for(size_t i=0;i<geo_eval_node_count(state->reference.sources);++i){GeoSourceNodeView node;
        if(!geo_eval_node_at(state->reference.sources,i,&node))return false;
        if(!node.described){GeoSourceDescriptor descriptor;
            if(geo_eval_describe(state->reference.sources,node.source,&descriptor)!=GEO_SOURCE_OK)return false;
        }
        if(node.value&&node.value->kind==GEO_SOURCE_QUANTITY&&!model_source_quantity_type(state,&node.source,node.value))return false;
    }
    return true;
}

static bool model_source_write_ok=true;
static void model_source_base64(const void *data,size_t size)
{
    size_t cap=(size+2)/3*4+1;char *text=malloc(cap);
    /* Every source key has already been bounded and allocated during build. */
    if(!text||!geo_base64_encode(data,size,text,cap,NULL)){free(text);model_source_write_ok=false;fputs("null",stdout);return;}
    model_string(stdout,text);free(text);
}
static const GeoSourceProvider *model_source_provider(const GeoEvalContext *ctx,GeoProviderToken token)
{for(size_t i=0;i<geo_eval_provider_count(ctx);++i){const GeoSourceProvider *p=geo_eval_provider_at(ctx,i);if(p->token==token)return p;}return NULL;}
static void model_source_ref(const GeoEvalContext *ctx,GeoSourceRef ref)
{
    const GeoSourceProvider *provider=model_source_provider(ctx,ref.provider);
    fputs("{\"namespace\":",stdout);model_string(stdout,provider->name_space);
    fputs(",\"keyBase64\":",stdout);model_source_base64(ref.key,ref.key_size);putchar('}');
}
static void model_source_owner(const ModelSourceItem *item)
{
    if(!item||!item->local){fputs("null",stdout);return;}
    if(item->owner_namespace){
        fputs("{\"namespace\":",stdout);model_string(stdout,item->owner_namespace);
        fputs(",\"keyBase64\":",stdout);model_source_base64(item->owner_key,sizeof item->owner_key);putchar('}');return;
    }
    char key[48];snprintf(key,sizeof key,"profile-run:%u",item->id);
    fputs("{\"namespace\":\"app.model-snapshot\",\"keyBase64\":",stdout);model_source_base64(key,strlen(key));putchar('}');
}
static const ModelSourceItem *model_source_semantics(ModelSources *state,const GeoSourceRef *ref,
    const ModelSourceItem *item,ModelSourceItem *scratch)
{
    if(item||ref->provider!=APP_SOURCE_SECTION_PROFILE)return item;
    WoodSectionProfileSourceKind kind;uint32_t id;
    if(!wood_sp_source_decode(ref,&kind,&id))return NULL;
    uint32_t profile=0;
    if(kind==WOOD_SP_SOURCE_MEMBER_REGION){
        for(size_t i=0;i<state->profile_member_count;++i)if(state->profile_members[i].id==id){profile=state->profile_members[i].profile_id;break;}
    }else if(kind==WOOD_SP_SOURCE_RUN_REGION){
        for(size_t i=0;i<state->profile_run_count;++i)if(state->profile_runs[i].id==id){profile=state->profile_runs[i].profile_id;break;}
    }else return NULL;
    memset(scratch,0,sizeof *scratch);scratch->local=true;scratch->owner_namespace="wood.section-profile";
    WoodSectionProfileSourceKey key;
    (void)wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_PROFILE_DEFINITION,profile,&key);
    memcpy(scratch->owner_key,key.bytes,sizeof scratch->owner_key);return scratch;
}
static void model_source_context(GeoSourceContext context,const ModelSourceItem *item)
{
    fputs("{\"placementId\":",stdout);if(context.has_placement)printf("%u",context.placement);else fputs("null",stdout);
    fputs(",\"axis\":",stdout);if(context.axis>=0)printf("%d",context.axis);else fputs("null",stdout);
    fputs(",\"owner\":",stdout);model_source_owner(item);putchar('}');
}
static void model_source_frame(GeoFrame frame,const ModelSourceItem *item)
{
    fputs("{\"origin\":",stdout);model_point(frame.origin);fputs(",\"u\":",stdout);model_vector(frame.axis_u);
    fputs(",\"v\":",stdout);model_vector(frame.axis_v);fputs(",\"n\":",stdout);model_vector(frame.normal);
    printf(",\"coordinateDomain\":\"%s\",\"owner\":",item&&item->local?"local":"world");model_source_owner(item);putchar('}');
}
static void model_source_loop(GeoLoop2View loop)
{putchar('[');for(size_t i=0;i<loop.count;++i)printf("%s[%" PRId64 ",%" PRId64 "]",i?",":"",loop.v[i].u,loop.v[i].v);putchar(']');}
static void model_source_keys(const BoundaryVertexKeys *keys)
{
    if(!keys){fputs("null",stdout);return;}putchar('[');
    for(size_t l=0;l<keys->loop_count;++l){if(l)putchar(',');putchar('[');for(size_t i=0;i<keys->counts[l];++i)printf("%s%u",i?",":"",keys->keys[l][i]);putchar(']');}putchar(']');
}
static void model_source_value(const GeoSourceValue *value,const ModelSourceItem *item,const char *quantity_type)
{
    switch(value->kind){
    case GEO_SOURCE_QUANTITY:printf("{\"num\":\"%" PRId64 "\",\"den\":\"%" PRId64 "\",\"unit\":\"%s\",\"quantityType\":\"%s\"}",value->as.quantity.num,value->as.quantity.den,value->as.quantity.unit==GEO_UNIT_LENGTH?"length":"scalar",quantity_type);break;
    case GEO_SOURCE_AXIS_POSITION:printf("{\"coordinate\":%" PRId64 ",\"context\":",value->as.position.coordinate);model_source_context(value->as.position.context,item);putchar('}');break;
    case GEO_SOURCE_FRAME:model_source_frame(value->as.frame,item);break;
    case GEO_SOURCE_BOX:fputs("{\"frame\":",stdout);model_source_frame(value->as.box.frame,item);printf(",\"lo\":[0,0,0],\"hi\":[%" PRId64 ",%" PRId64 ",%" PRId64 "]}",value->as.box.extent[0],value->as.box.extent[1],value->as.box.extent[2]);break;
    case GEO_SOURCE_REGION_SET:
        fputs("{\"components\":[",stdout);
        for(size_t i=0;i<value->as.regions.count;++i){const GeoRegionView *region=&value->as.regions.regions[i];if(i)putchar(',');fputs("{\"outer\":",stdout);model_source_loop(region->outline);fputs(",\"holes\":[",stdout);
            for(size_t h=0;h<region->hole_count;++h){if(h)putchar(',');model_source_loop(region->holes[h]);}fputs("],\"vertexKeys\":",stdout);model_source_keys(item&&i<item->region_count?item->vertex_keys[i]:NULL);putchar('}');}
        fputs("]}",stdout);break;
    case GEO_SOURCE_FEATURE:fputs("{\"keyBase64\":",stdout);model_source_base64(value->as.feature.key,value->as.feature.key_size);fputs(",\"segment\":[",stdout);model_point(value->as.feature.segment.start);putchar(',');model_point(value->as.feature.segment.end);fputs("]}",stdout);break;
    case GEO_SOURCE_DEFINITION:fputs("{\"schema\":",stdout);model_string(stdout,value->as.definition.schema);fputs(",\"contentBase64\":",stdout);model_source_base64(value->as.definition.content,value->as.definition.content_size);putchar('}');break;
    }
}
static void model_source_faces(const ModelSourceItem *item)
{
    static const char *const rc[]={"-X","+X","-Y","+Y","-Z","+Z"};
    putchar('[');for(unsigned f=0;f<6;++f){unsigned axis=f/2,side=f%2;const char *name=rc[f];
        if(!strcmp(item->kind,"timber")){if(!wood_member_face_spec((WoodMemberFace)f,&axis,&side))return;name=wood_member_face_short_name((WoodMemberFace)f);}
        char key[240];snprintf(key,sizeof key,"%s:%u:face:%s",item->kind,item->id,name);
        printf("%s{\"axis\":%u,\"side\":%u,\"legacyFeature\":",f?",":"",axis,side);model_string(stdout,name);
        fputs(",\"featureKeyBase64\":",stdout);model_source_base64(key,strlen(key));putchar('}');}putchar(']');
}
static void model_sources_write(ModelSources *state,const char *candidate)
{
    GeoEvalContext *ctx=state->reference.sources;
    fputs("{\"schema\":\"geometry-neutral-sources/1\",\"candidate\":{\"id\":",stdout);model_string(stdout,candidate);
    fputs(",\"baseRevision\":0},\"coverage\":{\"complete\":false,\"rootsComplete\":true,\"missingGroups\":[\"grid-fields-and-bindings\",\"material-source-overrides\",\"profile-definition-edges\",\"derived-region-provenance\",\"ordered-stop-features\"]},\"providers\":[",stdout);
    for(size_t i=0;i<geo_eval_provider_count(ctx);++i){const GeoSourceProvider *p=geo_eval_provider_at(ctx,i);if(i)putchar(',');fputs("{\"namespace\":",stdout);model_string(stdout,p->name_space);fputs(",\"implementationFingerprint\":",stdout);model_string(stdout,p->implementation_fingerprint);putchar('}');}
    fputs("],\"nodes\":[",stdout);
    static const char *const types[]={"quantity","axis-position","frame","region-set","box","feature","definition"};
    static const char *const status[]={"ok","missing","failed","cycle","invalid","memory"};
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;geo_eval_node_at(ctx,i,&node);ModelSourceItem semantic;
        const ModelSourceItem *item=model_source_semantics(state,&node.source,model_source_item(state,&node.source),&semantic);
        if(i)putchar(',');fputs("{\"ref\":",stdout);model_source_ref(ctx,node.source);fputs(",\"descriptor\":{\"valueType\":",stdout);model_string(stdout,types[node.descriptor.kind]);
        fputs(",\"unit\":",stdout);model_string(stdout,node.descriptor.unit==GEO_UNIT_LENGTH?"length":"scalar");fputs(",\"context\":",stdout);model_source_context(node.descriptor.context,item);
        fputs("},\"status\":",stdout);model_string(stdout,node.state==GEO_NODE_NEW?"unevaluated":status[node.status]);fputs(",\"value\":",stdout);if(node.value)model_source_value(node.value,item,node.value->kind==GEO_SOURCE_QUANTITY?model_source_quantity_type(state,&node.source,node.value):NULL);else fputs("null",stdout);putchar('}');}
    fputs("],\"edges\":[",stdout);static const char *const relation[]={"value-required","definition-required","evaluate-before"};
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;GeoSourceNodeView a,b;geo_eval_edge_at(ctx,i,&edge);geo_eval_node_at(ctx,edge.consumer,&a);geo_eval_node_at(ctx,edge.source,&b);
        if(i)putchar(',');fputs("{\"consumer\":",stdout);model_source_ref(ctx,a.source);fputs(",\"source\":",stdout);model_source_ref(ctx,b.source);fputs(",\"kind\":",stdout);model_string(stdout,relation[edge.kind]);putchar('}');}
    fputs("],\"roots\":[",stdout);
    for(size_t i=0;i<state->count;++i){ModelSourceItem *item=state->items[i];if(i)putchar(',');fputs("{\"kind\":",stdout);model_string(stdout,item->kind);printf(",\"id\":%u,\"slot\":",item->id);model_string(stdout,item->slot);
        fputs(",\"memberId\":",stdout);if(item->has_member)printf("%u",item->member_id);else fputs("null",stdout);fputs(",\"name\":",stdout);if(item->name)model_string(stdout,item->name);else fputs("null",stdout);
        fputs(",\"ref\":",stdout);model_source_ref(ctx,(GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)});
        if(item->descriptor.kind==GEO_SOURCE_BOX){fputs(",\"faces\":",stdout);model_source_faces(item);}putchar('}');}
    fputs("]}",stdout);
}
