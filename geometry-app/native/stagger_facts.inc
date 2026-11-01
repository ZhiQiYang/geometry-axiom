/* H facts for I24's ordered parameter/source exception. These are immutable
 * candidate evidence, never World definitions, dump records, or history. Each
 * snapshot re-evaluates only the referenced dependency closure with fresh marks;
 * cached axis values and unrelated invalid fields cannot stand in for that step.
 * Failure to resolve an intermediate source supplies no exception: the existing
 * final rebuild still owns validity and the primary diagnostic. */
typedef struct {
    uint32_t id;
    WoodGridStaggerPoint axis[2];
} AppStaggerSystemPoint;
typedef struct {
    AppStaggerSystemPoint systems[GEO_GRID_SYSTEM_CAPACITY];
    size_t count;
} AppStaggerSnapshot;
static bool app_stagger_same_point(const WoodGridStaggerPoint *a,const WoodGridStaggerPoint *b)
{
    return a->set==b->set&&(!a->set||(a->resolved==b->resolved&&a->value==b->value&&
        a->source.set==b->source.set&&(!a->source.set||
        (a->source.parameter_id==b->source.parameter_id&&a->source.field_id==b->source.field_id))));
}
static bool app_stagger_snapshot(World *world,AppStaggerSnapshot *out)
{
    memset(out,0,sizeof *out);
    out->count=geo_grid_systems_count(&world->geo.grid_store);
    if(out->count>GEO_GRID_SYSTEM_CAPACITY)return false;
    GeoParameterEvaluation *evaluation=NULL;
    for(size_t i=0;i<out->count;++i){
        const GeoGridSystem *system=geo_grid_systems_at(&world->geo.grid_store,i);
        AppStaggerSystemPoint *saved=&out->systems[i];saved->id=system->id;
        for(unsigned axis=0;axis<2;++axis){
            const GeoGridAxisDef *definition=&system->axis[axis];WoodGridStaggerPoint *point=&saved->axis[axis];
            point->set=definition->stagger_set;if(!point->set)continue;
            point->source.set=definition->parameters[5].set;
            if(!point->source.set){point->resolved=true;point->value=definition->stagger;continue;}
            point->source.parameter_id=definition->parameters[5].parameter_id;
            point->source.field_id=definition->parameters[5].field_id;
            if(!evaluation){evaluation=geo_parameter_evaluation_create(&world->geo.parameters,NULL,NULL);
                if(!evaluation)return false;}
            GeoQuantity value;
            int index=geo_parameters_field_index(&world->geo.parameters,point->source.parameter_id,point->source.field_id);
            if(index>=0&&geo_parameters_fields(&world->geo.parameters)[index].type==GEO_PARAMETER_DIMENSION&&
               geo_parameter_evaluation_field(evaluation,point->source,&value)&&value.den==1&&geo_coord_in_range(value.num)){
                point->resolved=true;point->value=value.num;
            }
        }
    }
    geo_parameter_evaluation_destroy(evaluation);return true;
}
static const AppStaggerSystemPoint *app_stagger_find(const AppStaggerSnapshot *snapshot,uint32_t id)
{
    for(size_t i=0;i<snapshot->count;++i)if(snapshot->systems[i].id==id)return &snapshot->systems[i];
    return NULL;
}
static bool app_stagger_append(AppWorldCandidate *candidate,uint32_t id,unsigned axis,uint32_t order,
    const WoodGridStaggerPoint *before,const WoodGridStaggerPoint *after)
{
    if(app_stagger_same_point(before,after))return true;
    size_t count=candidate->operation.stagger_count;
    if(count==candidate->stagger_capacity){
        size_t capacity=candidate->stagger_capacity?candidate->stagger_capacity*2:8;
        if(capacity<candidate->stagger_capacity||capacity>SIZE_MAX/sizeof(WoodGridStaggerFact))return false;
        WoodGridStaggerFact *facts=realloc(candidate->stagger_facts,capacity*sizeof *facts);
        if(!facts)return false;candidate->stagger_facts=facts;candidate->stagger_capacity=capacity;
    }
    WoodGridStaggerFact *fact=&candidate->stagger_facts[count];memset(fact,0,sizeof *fact);
    fact->system_id=id;fact->axis=axis;fact->order=order;fact->before=*before;fact->after=*after;
    candidate->operation.stagger_count=count+1;return true;
}
static bool app_stagger_record_step(World *world,const AppStaggerSnapshot *before)
{
    AppWorldCandidate *candidate=g_active_app_candidate;
    if(!candidate||world!=&candidate->after)return false;
    AppStaggerSnapshot after;if(!app_stagger_snapshot(world,&after))return false;
    uint32_t order=++candidate->operation.stagger_steps;
    const WoodGridStaggerPoint absent={0};
    for(size_t i=0;i<before->count;++i){
        const AppStaggerSystemPoint *old=&before->systems[i],*now=app_stagger_find(&after,old->id);
        for(unsigned axis=0;axis<2;++axis)if(!app_stagger_append(candidate,old->id,axis,order,
            &old->axis[axis],now?&now->axis[axis]:&absent))return false;
    }
    for(size_t i=0;i<after.count;++i)if(!app_stagger_find(before,after.systems[i].id))
        for(unsigned axis=0;axis<2;++axis)if(!app_stagger_append(candidate,after.systems[i].id,axis,order,
            &absent,&after.systems[i].axis[axis]))return false;
    return true;
}
