/* The Python driver copies the real adapter, renames only its main, and adds
 * two observation hooks to the copied transport. Definitions below are the
 * registered providers' ACTUAL results, cached by K before W/H consume them.
 * No production source, authored record, or copied evaluator is substituted. */
#ifdef _WIN32
#undef _WIN32
#endif
#include "../geometry-core/model_base.c"
#include <stddef.h>
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)

enum { SEM_NONE,SEM_PARAMETER,SEM_RUN,SEM_MEMBER,SEM_BAD_PARAMETER,SEM_BAD_SP };
static unsigned sem_mode,sem_fault,sem_hits,sem_kind;
static uint32_t sem_id;
static bool (*sem_sp_evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
static unsigned char sem_field_bytes[GEO_PARAMETER_FIELD_CONTENT_MAX];
static size_t sem_field_size;
static char sem_json[SP_RUN_RECORD_MAX];

static bool sem_same_ref(GeoSourceRef a,GeoSourceRef b)
{return a.provider==b.provider&&a.key_size==b.key_size&&!memcmp(a.key,b.key,a.key_size);}
static bool sem_node(GeoEvalContext *graph,GeoSourceRef ref,GeoSourceNodeView *out,size_t *index)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(graph,i,&n)&&sem_same_ref(n.source,ref)){if(out)*out=n;if(index)*index=i;return true;}}
    return false;
}
static bool sem_edge(GeoEvalContext *graph,GeoSourceRef consumer,GeoSourceRef source,GeoDependencyKind kind)
{
    size_t c,s;if(!sem_node(graph,consumer,NULL,&c)||!sem_node(graph,source,NULL,&s))return false;
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.consumer==c&&edge.source==s&&edge.kind==kind)return true;}
    return false;
}
static GeoSourceRef sem_root_ref(const ModelSourceItem *item)
{return (GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)};}
static ModelSourceItem *sem_root(ModelSources *s,uint32_t id,const char *slot,uint32_t member)
{
    for(size_t i=0;i<s->count;++i){ModelSourceItem *item=s->items[i];
        if(item->id==id&&!strcmp(item->slot,slot)&&item->has_member==(member!=0)&&(!member||item->member_id==member))return item;}
    return NULL;
}
static bool sem_value(ModelSources *s,const ModelSourceItem *item,GeoSourceValue *out)
{return item&&geo_eval_source(s->reference.sources,sem_root_ref(item),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}
static bool sem_canonical(const char *text)
{
    GeoJson json={0};if(!geo_json_parse(&json,text))return false;
    bool ok=geo_json_canonical(&json,0,sem_json,sizeof sem_json);geo_json_free(&json);return ok;
}
/* K's parameter binding verifies its original registered callbacks. Prime
 * FIELDDEF through that unchanged provider, then replace only the actual
 * cached canonical result before the real quantity rebuild consumes it. */
static bool sem_prime_parameter_definition(ReferenceEval *reference)
{
    GeoParameterDefinitionKey key;GeoSourceValue returned;GeoSourceNodeView node;
    GeoSourceRef definition=geo_parameter_definition_source_ref(APP_SOURCE_PARAMETER_DEFINITION,
        GEO_PARAMETER_DEFINITION_FIELD,8,1,&key);
    uint32_t ids[]={8,1};
    if(sem_node(reference->sources,(GeoSourceRef){APP_SOURCE_PARAMETER,ids,sizeof ids},NULL,NULL)||
       geo_eval_source(reference->sources,definition,GEO_DEPENDENCY_DEFINITION_REQUIRED,&returned)!=GEO_SOURCE_OK||
       !sem_node(reference->sources,definition,&node,NULL)||node.state!=GEO_NODE_VALID||!node.value||
       returned.kind!=GEO_SOURCE_DEFINITION||!returned.as.definition.schema||
       strcmp(returned.as.definition.schema,"geometry.parameter-field/1"))return false;
    GeoSourceValue *actual=(GeoSourceValue *)node.value;
    if(actual->kind!=GEO_SOURCE_DEFINITION||actual->as.definition.content!=returned.as.definition.content||
       actual->as.definition.content_size!=returned.as.definition.content_size)return false;
    actual->as.definition.content=sem_field_bytes;actual->as.definition.content_size=sem_field_size;
    ++sem_hits;return true;
}
static bool sem_sp_provider(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    if(!sem_sp_evaluate(state,graph,ref,out))return false;
    WoodSectionProfileSourceKind kind;uint32_t id;
    if((sem_mode==SEM_RUN||sem_mode==SEM_MEMBER||sem_mode==SEM_BAD_SP)&&
       wood_sp_source_decode(ref,&kind,&id)&&kind==sem_kind&&id==sem_id){
        ++sem_hits;
        out->as.definition.content=sem_json;out->as.definition.content_size=strlen(sem_json);
        if(sem_mode==SEM_BAD_SP){
            if(sem_fault==1)out->as.definition.schema="wrong.section-profile/1";
            if(sem_fault==2)out->as.definition.schema=NULL;
            if(sem_fault==4)out->as.definition.content_size--;
        }
    }
    return true;
}
/* Inserted immediately after the real reference_sources_ensure succeeds. */
static bool semantics_install(ReferenceEval *reference)
{
    bool parameter=false,profile=false;sem_hits=0;
    for(size_t i=0;i<geo_eval_provider_count(reference->sources);++i){
        GeoSourceProvider *provider=(GeoSourceProvider *)geo_eval_provider_at(reference->sources,i);
        if(provider->token==APP_SOURCE_PARAMETER_DEFINITION)parameter=true;
        if(provider->token==APP_SOURCE_SECTION_PROFILE){sem_sp_evaluate=provider->evaluate;provider->evaluate=sem_sp_provider;profile=true;}
    }
    return parameter&&profile&&(sem_mode!=SEM_PARAMETER||sem_prime_parameter_definition(reference));
}
/* Bad FIELDDEF cases are injected after K has successfully computed the
 * scalar but before the H alias runs. This isolates H's own validation: K's
 * earlier guard cannot accidentally kill a control that bypasses H's guard. */
static bool semantics_before_aliases(ModelSources *state)
{
    if(sem_mode!=SEM_BAD_PARAMETER)return true;
    GeoParameterDefinitionKey key;GeoSourceNodeView node;
    if(!sem_node(state->reference.sources,geo_parameter_definition_source_ref(APP_SOURCE_PARAMETER_DEFINITION,
        GEO_PARAMETER_DEFINITION_FIELD,8,1,&key),&node,NULL)||!node.value)return false;
    GeoSourceValue *actual=(GeoSourceValue *)node.value;
    if(actual->kind!=GEO_SOURCE_DEFINITION||actual->as.definition.content_size>sizeof sem_field_bytes)return false;
    sem_field_size=actual->as.definition.content_size;memcpy(sem_field_bytes,actual->as.definition.content,sem_field_size);
    actual->as.definition.content=sem_field_bytes;++sem_hits;
    if(sem_fault==1)actual->as.definition.schema="wrong.parameter-field/1";
    if(sem_fault==2)actual->as.definition.schema=NULL;
    if(sem_fault==3)sem_field_bytes[7]=99; /* field identity, same schema */
    if(sem_fault==4)sem_field_bytes[3]=99; /* card identity, same schema */
    if(sem_fault==5){ /* canonical flag disagrees with the canonical AST */
        size_t name=0;for(size_t i=12;i<16;++i)name=(name<<8)|sem_field_bytes[i];
        if(16+name>=sem_field_size)return false;sem_field_bytes[16+name]=0;
    }
    if(sem_fault==6)--actual->as.definition.content_size;
    return true;
}

static World *sem_parameter_world(bool ratio)
{
    World *world=calloc(1,sizeof *world);if(!world)return NULL;
    GeoParameterCard card={.id=8,.next_field_id=2,.fields={1},.count=1};strcpy(card.name,"authored card");
    GeoParameterField field={.parameter_id=8,.id=1,.type=ratio?GEO_PARAMETER_RATIO:GEO_PARAMETER_COUNT};
    strcpy(field.name,"authored field");strcpy(field.expression,"{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"1\"}");
    if(!geo_parameters_stage_card(&world->geo.parameters,&card)||!geo_parameters_stage_field(&world->geo.parameters,&field)){free(world);return NULL;}
    return world;
}
static bool sem_parameter_authored(const World *world,const GeoParameterField *before)
{
    const GeoParameterField *field=geo_parameters_fields(&world->geo.parameters);
    return geo_parameters_field_count(&world->geo.parameters)==1&&field->parameter_id==before->parameter_id&&field->id==before->id&&
        field->type==before->type&&!strcmp(field->name,before->name)&&!strcmp(field->expression,before->expression);
}
static int sem_parameter_case(bool reverse)
{
    World *world=sem_parameter_world(reverse);CHECK("sem-parameter-memory",world);
    GeoParameterField before=*geo_parameters_fields(&world->geo.parameters),actual=before;
    actual.type=reverse?GEO_PARAMETER_COUNT:GEO_PARAMETER_RATIO;strcpy(actual.name,reverse?"actual count":"actual ratio");
    if(!reverse)strcpy(actual.expression,"{\"op\":\"literal\",\"num\":\"1\",\"den\":\"3\",\"unit\":\"1\"}");
    sem_field_size=geo_parameter_field_definition_encode(&actual,sem_field_bytes,sizeof sem_field_bytes);
    CHECK("sem-parameter-canonical",sem_field_size);sem_mode=SEM_PARAMETER;
    ModelSources state={0};CHECK("sem-parameter-build",model_sources_build(&state,world));
    ModelSourceItem *item=sem_root(&state,8,"parameter.value",1);GeoSourceValue value;GeoParameterDefinitionKey key;GeoSourceNodeView node;
    GeoSourceRef definition=geo_parameter_definition_source_ref(APP_SOURCE_PARAMETER_DEFINITION,GEO_PARAMETER_DEFINITION_FIELD,8,1,&key);
    CHECK("sem-parameter-actual-definition-is-k-node",sem_hits==1&&sem_node(state.reference.sources,definition,&node,NULL)&&node.value&&
        node.value->kind==GEO_SOURCE_DEFINITION&&node.value->as.definition.content_size==sem_field_size&&
        !memcmp(node.value->as.definition.content,sem_field_bytes,sem_field_size));
    CHECK("sem-parameter-actual-exact-quantity",sem_value(&state,item,&value)&&value.as.quantity.num==(reverse?3:1)&&value.as.quantity.den==(reverse?1:3)&&value.as.quantity.unit==GEO_UNIT_SCALAR);
    CHECK("sem-parameter-actual-type-controls-alias",item->quantity_type&&!strcmp(item->quantity_type,reverse?"count":"ratio"));
    CHECK("sem-parameter-actual-name-controls-root",item->name&&!strcmp(item->name,actual.name));
    uint32_t ids[]={8,1};GeoSourceRef scalar={APP_SOURCE_PARAMETER,ids,sizeof ids};
    const char *type=model_source_quantity_type(&state,&scalar,&value);
    CHECK("sem-parameter-actual-type-controls-core-export",type&&!strcmp(type,reverse?"count":"ratio"));
    CHECK("sem-parameter-alias-definition-required",sem_edge(state.reference.sources,sem_root_ref(item),definition,GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("sem-parameter-alias-value-required",sem_edge(state.reference.sources,sem_root_ref(item),scalar,GEO_DEPENDENCY_VALUE_REQUIRED));
    CHECK("sem-parameter-authored-fields-unchanged",sem_parameter_authored(world,&before));
    model_sources_free(&state);free(world);return 0;
}
static int sem_parameter_bad(void)
{
    for(unsigned fault=1;fault<=6;++fault){World *world=sem_parameter_world(false);CHECK("sem-parameter-bad-memory",world);
        GeoParameterField before=*geo_parameters_fields(&world->geo.parameters);sem_mode=SEM_BAD_PARAMETER;sem_fault=fault;
        ModelSources state={0};CHECK("sem-parameter-invalid-definition-refuses-alias",!model_sources_build(&state,world)&&sem_hits==1);
        ModelSourceItem *item=sem_root(&state,8,"parameter.value",1);CHECK("sem-parameter-bad-alias-present",item);
        const char *saved_name=item->name,*saved_type=item->quantity_type;char saved_owned[GEO_PARAMETER_NAME_MAX];GeoSourceValue value,saved;
        memcpy(saved_owned,item->owned_name,sizeof saved_owned);
        memset(&value,0x5a,sizeof value);memcpy(&saved,&value,sizeof saved);
        GeoSourceRef root=sem_root_ref(item);
        CHECK("sem-parameter-invalid-output-atomic",!model_source_evaluate(&state,state.reference.sources,&root,&value)&&
            !memcmp(&value,&saved,sizeof value)&&item->name==saved_name&&item->quantity_type==saved_type&&
            !memcmp(saved_owned,item->owned_name,sizeof saved_owned));
        CHECK("sem-parameter-bad-authored-fields-unchanged",sem_parameter_authored(world,&before));
        model_sources_free(&state);free(world);
    }return 0;
}

static bool sem_record(World *world,unsigned kind,const char *text)
{
    WoodSectionProfileContext context=app_sp_context(world);GeoJson json={0};if(!geo_json_parse(&json,text))return false;
    bool ok=kind==1?wood_sp_put_profile(&context,&json,0):kind==2?wood_sp_put_member(&context,&json,0):wood_sp_put_run(&context,&json,0);
    geo_json_free(&json);return ok;
}
static const char *sem_run_text(bool placed,unsigned profile,unsigned id)
{
    static char text[512];snprintf(text,sizeof text,
        "{\"id\":%u,\"profileId\":%u,\"length\":{\"kind\":\"literal\",\"value\":120},\"placement\":%s}",id,profile,
        placed?"{\"kind\":\"advanced\",\"origin\":[100,200,300],\"N\":\"+Y\",\"V\":\"-Z\"}":"null");return text;
}
static const char *sem_member_text(unsigned id,unsigned profile)
{
    static char text[512];snprintf(text,sizeof text,
        "{\"id\":%u,\"profileId\":%u,\"kind\":\"timber\",\"A\":{\"kind\":\"literal\",\"value\":27},\"B\":{\"kind\":\"literal\",\"value\":33},\"orientation\":\"A-u\",\"u0\":%u,\"v0\":20}",id,profile,id==3?10:60);return text;
}
static World *sem_profile_world(bool placed)
{
    World *world=calloc(1,sizeof *world);if(!world)return NULL;
    if(!sem_record(world,1,"{\"id\":1,\"name\":\"first\",\"outline\":[[0,0],[100,0],[100,100],[0,100]]}")||
       !sem_record(world,1,"{\"id\":2,\"name\":\"second\",\"outline\":[[0,0],[160,0],[160,100],[0,100]]}")||
       !sem_record(world,2,sem_member_text(3,1))||!sem_record(world,2,sem_member_text(4,2))||
       !sem_record(world,3,sem_run_text(placed,1,5))||!sem_record(world,3,sem_run_text(false,2,6))){free(world);return NULL;}
    return world;
}
/* Only the suffixes identified as rebuilt caches in section_profile.h may
 * change. These fixtures use advanced/null placement, so their prefix frame
 * is authored too; there is deliberately no live/simple-frame cache here. */
static bool sem_profile_authored(const World *world,const SectionProfileState *before)
{
    const SectionProfileState *after=&world->wood.section_profiles;
    if(after->profile_count!=before->profile_count||after->member_count!=before->member_count||after->run_count!=before->run_count)return false;
    for(size_t i=0;i<after->profile_count;++i)if(memcmp(&after->profiles[i],&before->profiles[i],sizeof after->profiles[i]))return false;
    for(size_t i=0;i<after->member_count;++i)if(memcmp(&after->members[i],&before->members[i],offsetof(ProfileMember,a)))return false;
    for(size_t i=0;i<after->run_count;++i)if(memcmp(&after->runs[i],&before->runs[i],offsetof(ProfileRun,length)))return false;
    return true;
}
static bool sem_owner(ModelSources *state,WoodSectionProfileSourceKind kind,uint32_t id,uint32_t expected)
{
    WoodSectionProfileSourceKey key,owner;ModelSourceItem scratch;
    GeoSourceRef ref=wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,kind,id,&key);
    const ModelSourceItem *item=model_source_semantics(state,&ref,NULL,&scratch);
    (void)wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_PROFILE_DEFINITION,expected,&owner);
    return item&&item->local&&item->owner_namespace&&!strcmp(item->owner_namespace,"wood.section-profile")&&
        !memcmp(item->owner_key,owner.bytes,sizeof owner.bytes);
}
static bool sem_frame_equal(GeoFrame f,bool placed)
{
    GeoFrame expected=placed?(GeoFrame){{100,200,300},{1,0,0},{0,0,-1},{0,1,0}}:(GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};
    return !memcmp(&f,&expected,sizeof f);
}
static int sem_profile_case(const char *name)
{
    bool to_placed=!strcmp(name,"to-placed"),to_local=!strcmp(name,"to-local"),run_map=!strcmp(name,"run-map");
    bool member_map=!strcmp(name,"member-map"),member_back=!strcmp(name,"member-back"),baseline=!strcmp(name,"baseline");
    World *world=sem_profile_world(to_local);SectionProfileState *before=malloc(sizeof *before);CHECK("sem-profile-memory",world&&before);
    memcpy(before,&world->wood.section_profiles,sizeof *before);sem_mode=SEM_NONE;
    if(to_placed||to_local||run_map){sem_mode=SEM_RUN;sem_kind=WOOD_SP_SOURCE_RUN_DEFINITION;sem_id=5;
        CHECK("sem-run-canonical",sem_canonical(sem_run_text(to_placed,run_map?2:1,5)));}
    if(member_map||member_back){sem_mode=SEM_MEMBER;sem_kind=WOOD_SP_SOURCE_MEMBER_DEFINITION;sem_id=member_back?4:3;
        CHECK("sem-member-canonical",sem_canonical(sem_member_text(sem_id,member_back?1:2)));}
    ModelSources state={0};CHECK("sem-profile-build",model_sources_build(&state,world));
    if(!baseline){WoodSectionProfileSourceKey key;GeoSourceNodeView node;
        CHECK("sem-sp-actual-definition-is-k-node",sem_hits==1&&sem_node(state.reference.sources,
            wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,(WoodSectionProfileSourceKind)sem_kind,sem_id,&key),&node,NULL)&&node.value&&
            node.value->kind==GEO_SOURCE_DEFINITION&&node.value->as.definition.content_size==strlen(sem_json)&&
            !memcmp(node.value->as.definition.content,sem_json,strlen(sem_json)));}
    CHECK("sem-profile-exact-root-count",state.count==12);
    for(unsigned r=5;r<=6;++r){unsigned profile=r==5?(run_map?2:1):2;bool placed=r==5&&to_placed;
        for(unsigned member=0;member<=4;++member){if(member==1||member==2)continue;
            unsigned member_profile=member==3?(member_map?2:1):(member_back?1:2);
            bool expected=!member||member_profile==profile;
            const char *slots[]={"profile.frame","profile.region","profile.length"};
            for(unsigned slot=0;slot<3;++slot){ModelSourceItem *item=sem_root(&state,r,slots[slot],member);
                CHECK("sem-sp-actual-mapping-controls-root-membership",(item!=NULL)==expected);if(!item)continue;
                CHECK("sem-sp-actual-placement-controls-domain",item->local==!placed);
                CHECK("sem-sp-local-root-owner-is-run-identity",item->id==r&&!item->owner_namespace);
                GeoSourceValue value;CHECK("sem-sp-root-value",sem_value(&state,item,&value));
                if(slot==0){CHECK("sem-sp-actual-placement-controls-frame",sem_frame_equal(value.as.frame,placed));
                    WoodSectionProfileSourceKey key;GeoSourceRef frame=wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_RUN_FRAME,r,&key);
                    CHECK("sem-sp-frame-edge-kind",sem_edge(state.reference.sources,sem_root_ref(item),frame,placed?GEO_DEPENDENCY_VALUE_REQUIRED:GEO_DEPENDENCY_DEFINITION_REQUIRED));}
                if(slot==1){CHECK("sem-sp-actual-profile-controls-outline",value.as.regions.count==1&&value.as.regions.regions[0].outline.count==4&&
                    value.as.regions.regions[0].outline.v[2].u==(member?(member==3?37:87):(profile==1?100:160)));}
                if(slot==2)CHECK("sem-sp-exact-length",value.as.quantity.num==120&&value.as.quantity.den==1&&value.as.quantity.unit==GEO_UNIT_LENGTH);
            }
        }
        WoodSectionProfileSourceKey key;GeoSourceNodeView frame;
        CHECK("sem-sp-world-frame-node-present",sem_node(state.reference.sources,wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_RUN_FRAME,r,&key),&frame,NULL));
        CHECK("sem-sp-unplaced-world-frame-is-new",placed?(frame.state==GEO_NODE_VALID&&frame.value):(frame.state==GEO_NODE_NEW&&frame.described&&!frame.value));
        CHECK("sem-sp-actual-run-owner",sem_owner(&state,WOOD_SP_SOURCE_RUN_REGION,r,profile));
    }
    CHECK("sem-sp-actual-member-owner",sem_owner(&state,WOOD_SP_SOURCE_MEMBER_REGION,3,member_map?2:1)&&sem_owner(&state,WOOD_SP_SOURCE_MEMBER_REGION,4,member_back?1:2));
    CHECK("sem-sp-authored-fields-unchanged",sem_profile_authored(world,before));
    model_sources_free(&state);free(before);free(world);return 0;
}
static int sem_profile_bad(void)
{
    const unsigned kinds[]={WOOD_SP_SOURCE_PROFILE_DEFINITION,WOOD_SP_SOURCE_MEMBER_DEFINITION,WOOD_SP_SOURCE_RUN_DEFINITION};
    const uint32_t ids[]={1,3,5};
    for(size_t kind=0;kind<3;++kind)for(unsigned fault=1;fault<=5;++fault){
        World *world=sem_profile_world(false);SectionProfileState *before=malloc(sizeof *before);CHECK("sem-sp-bad-memory",world&&before);
        memcpy(before,&world->wood.section_profiles,sizeof *before);sem_mode=SEM_BAD_SP;sem_kind=kinds[kind];sem_id=ids[kind];sem_fault=fault;
        const char *record=kind==0?before->profiles[0].content:kind==1?before->members[0].content:before->runs[0].content;
        CHECK("sem-sp-bad-canonical",sem_canonical(record));
        if(fault==3){char *id=strstr(sem_json,"\"id\":");CHECK("sem-sp-bad-id-anchor",id);id[5]='9';}
        if(fault==5){size_t len=strlen(sem_json);CHECK("sem-sp-bad-canonical-space",len+1<sizeof sem_json);sem_json[len]=' ';sem_json[len+1]=0;}
        ModelSources state={0};CHECK("sem-sp-invalid-definition-refuses-model",!model_sources_build(&state,world)&&sem_hits>0);
        SectionProfile p,ps;ProfileMember m,ms;ProfileRun r,rs;
        memset(&p,0x5a,sizeof p);memcpy(&ps,&p,sizeof p);memset(&m,0x5a,sizeof m);memcpy(&ms,&m,sizeof m);memset(&r,0x5a,sizeof r);memcpy(&rs,&r,sizeof r);
        bool ok=kind==0?wood_sp_sources_profile_definition(state.reference.section_profile_sources,1,&p):
            kind==1?wood_sp_sources_member_definition(state.reference.section_profile_sources,3,&m):wood_sp_sources_run_definition(state.reference.section_profile_sources,5,&r);
        CHECK("sem-sp-invalid-definition-copy-atomic",!ok&&!memcmp(&p,&ps,sizeof p)&&!memcmp(&m,&ms,sizeof m)&&!memcmp(&r,&rs,sizeof r));
        CHECK("sem-sp-bad-authored-fields-unchanged",sem_profile_authored(world,before));
        model_sources_free(&state);free(before);free(world);
    }return 0;
}
static int sem_graph(void)
{
    World *world=sem_profile_world(false);CHECK("sem-graph-memory",world);sem_mode=SEM_RUN;sem_kind=WOOD_SP_SOURCE_RUN_DEFINITION;sem_id=5;
    CHECK("sem-graph-canonical",sem_canonical(sem_run_text(false,2,5)));ModelSources state={0};CHECK("sem-graph-build",model_sources_build(&state,world));
    for(unsigned r=5;r<=6;++r){WoodSectionProfileSourceKey a,b;GeoSourceRef region=wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_RUN_REGION,r,&a);
        CHECK("sem-graph-run-definition-edge",sem_edge(state.reference.sources,region,wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_RUN_DEFINITION,r,&b),GEO_DEPENDENCY_DEFINITION_REQUIRED));
        CHECK("sem-graph-actual-profile-edge",sem_edge(state.reference.sources,region,wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_PROFILE_DEFINITION,2,&b),GEO_DEPENDENCY_DEFINITION_REQUIRED));
        ModelSourceItem *item=sem_root(&state,r,"profile.region",0);CHECK("sem-graph-alias-region-edge",item&&sem_edge(state.reference.sources,sem_root_ref(item),region,GEO_DEPENDENCY_VALUE_REQUIRED));}
    WoodSectionProfileSourceKey a,b;GeoSourceRef member=wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_MEMBER_REGION,4,&a);
    CHECK("sem-graph-member-definition-edge",sem_edge(state.reference.sources,member,wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_MEMBER_DEFINITION,4,&b),GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("sem-graph-member-profile-edge",sem_edge(state.reference.sources,member,wood_sp_source_ref(APP_SOURCE_SECTION_PROFILE,WOOD_SP_SOURCE_PROFILE_DEFINITION,2,&b),GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("sem-graph-seal",geo_eval_seal(state.reference.sources));SectionProfile profile;ProfileMember m;ProfileRun run;
    CHECK("sem-definition-copies-after-seal",wood_sp_sources_profile_definition(state.reference.section_profile_sources,2,&profile)&&profile.id==2&&
        wood_sp_sources_member_definition(state.reference.section_profile_sources,4,&m)&&m.id==4&&m.profile_id==2&&
        wood_sp_sources_run_definition(state.reference.section_profile_sources,5,&run)&&run.id==5&&run.profile_id==2&&!run.placed);
    run.profile_id=99;CHECK("sem-definition-copy-does-not-alias",wood_sp_sources_run_definition(state.reference.section_profile_sources,5,&run)&&run.profile_id==2);
    model_sources_free(&state);free(world);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"parameter-ratio"))return sem_parameter_case(false);
    if(!strcmp(argv[1],"parameter-count"))return sem_parameter_case(true);
    if(!strcmp(argv[1],"parameter-bad"))return sem_parameter_bad();
    if(!strcmp(argv[1],"sp-bad"))return sem_profile_bad();
    if(!strcmp(argv[1],"graph"))return sem_graph();
    const char *cases[]={"baseline","to-placed","to-local","run-map","member-map","member-back"};
    for(size_t i=0;i<sizeof cases/sizeof *cases;++i)if(!strcmp(argv[1],cases[i]))return sem_profile_case(argv[1]);
    return 2;
}
