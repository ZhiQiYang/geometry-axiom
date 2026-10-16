/* Actual H consumers are linked to the production W/K objects. The pose
 * input is typed K data; returned-frame/threshold controls change only the
 * values at the H boundary, never the candidate's authored arrays. */
#ifdef _WIN32
#undef _WIN32
#endif
#include "../geometry-core/kernel/source.h"
static GeoSourceStatus host_authority_eval(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source host_authority_eval
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#undef geo_eval_source
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static unsigned host_fault,host_hits;
static GeoSourceStatus host_authority_eval(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);
    if(status!=GEO_SOURCE_OK)return status;
    if(host_fault==1&&ref.provider==APP_SOURCE_MEMBER_POSE&&out->kind==GEO_SOURCE_BOX){out->as.box.frame.origin.x+=17;++host_hits;}
    if(host_fault==2&&ref.provider==APP_SOURCE_PLACEMENT&&out->kind==GEO_SOURCE_FRAME){out->as.frame.origin.x+=7;++host_hits;}
    if(host_fault==3&&ref.provider==APP_SOURCE_FINISH){WoodFinishSourceKind kind;uint32_t id;
        if(wood_finish_source_decode(&ref,&kind,&id)&&kind==WOOD_FINISH_SOURCE_THRESHOLD&&out->kind==GEO_SOURCE_QUANTITY){out->as.quantity.num=17;out->as.quantity.den=1;++host_hits;}}
    if(host_fault==4&&ref.provider==APP_SOURCE_PLACEMENT&&out->kind==GEO_SOURCE_FRAME){
        out->as.frame.axis_u=(GeoVector3){0,1,0};out->as.frame.axis_v=(GeoVector3){-1,0,0};++host_hits;}
    return status;
}
typedef struct {GeoEvalContext *graph;GeoBox3 box;unsigned calls;} HostPoseInput;
static bool host_pose_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)opaque;uint32_t id;if(ref->provider!=APP_SOURCE_MEMBER_POSE||ref->key_size!=sizeof id)return false;
    memcpy(&id,ref->key,sizeof id);if(id!=41)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;out->context=(GeoSourceContext){true,7,-1};return true;
}
static bool host_pose_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostPoseInput *input=opaque;GeoSourceDescriptor ignored;if(input->graph!=graph||!host_pose_describe(opaque,ref,&ignored))return false;
    ++input->calls;out->kind=GEO_SOURCE_BOX;out->as.box=input->box;return true;
}
static bool host_has_edge(GeoEvalContext *graph,GeoProviderToken consumer,GeoProviderToken source)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;GeoSourceNodeView a,b;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&geo_eval_node_at(graph,edge.consumer,&a)&&
           geo_eval_node_at(graph,edge.source,&b)&&a.source.provider==consumer&&b.source.provider==source)return true;}
    return false;
}
static int host_pose_case(const char *name)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK("host-pose-memory",world&&before);
    PlacementSurface placement={.id=7,.frame={{10,20,30},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,1000,1000}};
    CHECK("host-pose-placement",app_placement_stage(world,&placement));world->wood.timber_count=1;
    world->wood.timbers[0]=(WoodMember){.id=41,.length=40,.size_a=10,.size_b=5,.placed=true,.auto_length=true,
        .role=WOOD_MEMBER_ROLE_PRIMARY,.cut_priority=2,.origin={10,20,30},.axis_length={1,0,0},.axis_a={0,1,0},.axis_b={0,0,1}};
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=7,.uv={0,0},.order=1,
        .length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL};
    memcpy(before,world,sizeof *world);ReferenceEval ctx={0};ctx.world=world;ctx.sources=geo_eval_create(8151,0);
    CHECK("host-pose-graph",ctx.sources);
    ctx.placement_sources=geo_placement_sources_register(ctx.sources,&world->geo.placement_data,&world->geo.region_data,APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,NULL,NULL);
    CHECK("host-pose-real-placement-provider",ctx.placement_sources);
    HostPoseInput input={ctx.sources,{{{40,70,30},{1,0,0},{0,1,0},{0,0,1}},{40,10,5}},0};
    GeoSourceProvider provider={APP_SOURCE_MEMBER_POSE,"woodworking.member.pose","host-authority-input/1",&input,host_pose_describe,host_pose_evaluate};
    CHECK("host-pose-input",geo_eval_register(ctx.sources,&provider));
    GeoSourceProvider reference={APP_SOURCE_REFERENCE,"app.legacy-reference","host-authority/1",&ctx,reference_source_describe,reference_source_evaluate};
    CHECK("host-pose-real-reference-provider",geo_eval_register(ctx.sources,&reference));ctx.sources_registered=true;
    GeoRect2 rect={0};GeoCoord expected=30;
    if(!strcmp(name,"rotated")){input.box.frame.axis_u=(GeoVector3){0,1,0};input.box.frame.axis_v=(GeoVector3){-1,0,0};expected=20;}
    if(!strcmp(name,"frame")){host_fault=2;expected=23;}
    if(!strcmp(name,"snapshot")){ctx.use_current_values=true;expected=0;}
    if(!strcmp(name,"quantity")){
        GuideLine guide={.id=1,.placement_id=7,.direction=GUIDE_ALONG_V};GeoCoord value=-99;
        CHECK("host-quantity-actual-box-and-frame",reference_quantity(&ctx,&guide,"timber:41:u:lo",&value)&&value==expected);
        CHECK("host-quantity-exact-value-edges",host_has_edge(ctx.sources,APP_SOURCE_REFERENCE,APP_SOURCE_MEMBER_POSE)&&host_has_edge(ctx.sources,APP_SOURCE_REFERENCE,APP_SOURCE_PLACEMENT));
        CHECK("host-quantity-authored-anchor-unchanged",!memcmp(world->wood.anchors,before->wood.anchors,sizeof world->wood.anchors));
    }else if(!strcmp(name,"member")){
        AppMemberPlacementScratch scratch={0};scratch.placement=placement;
        AppMemberReferenceContext member={0};member.world=world;member.evaluation=&ctx;member.geometry=&scratch;
        CHECK("host-member-actual-box-and-frame",app_member_reference_footprint(&member,0,7,&rect)&&rect.min_u==expected&&rect.max_u==70&&rect.min_v==50&&rect.max_v==60);
    }else{
        CHECK("host-footprint-actual-box-and-frame",reference_member_footprint(&ctx,0,7,&rect)&&rect.min_u==expected);
        if(!strcmp(name,"rotated"))CHECK("host-footprint-actual-rotation",rect.max_u==30&&rect.min_v==50&&rect.max_v==90);
        else if(!strcmp(name,"frame"))CHECK("host-footprint-actual-frame",rect.max_u==63&&host_hits==1);
        else if(!strcmp(name,"snapshot"))CHECK("host-footprint-snapshot-is-direct",rect.max_u==40&&input.calls==0&&geo_eval_node_count(ctx.sources)==0);
        else CHECK("host-footprint-actual-origin",rect.max_u==70&&rect.min_v==50&&rect.max_v==60);
    }
    if(strcmp(name,"quantity"))CHECK("host-footprint-world-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
static int host_target_case(const char *name)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK("host-target-memory",world&&before);
    PlacementSurface placement={.id=1,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,100,100}};
    CHECK("host-target-placement",app_placement_stage(world,&placement));world->wood.timber_count=1;
    world->wood.timbers[0]=(WoodMember){.id=11,.size_a=40,.size_b=50,.role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1};
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=1,.order=7,.length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL};
    memcpy(before,world,sizeof *world);ReferenceEval ctx={0};ctx.world=world;CHECK("host-target-factory",reference_sources_ensure(&ctx));
    WoodEngineeringTargetInfo target;EngTarget key={1,11,0,0};
    if(!strcmp(name,"assembly-member")){WoodAssemblyMember member;
        CHECK("host-assembly-member-actual-policy",reference_asm_member(&ctx,11,&member)&&member.role==WOOD_MEMBER_ROLE_BOUNDARY&&member.surface_id==1&&member.width==40&&member.depth==50&&!member.placed);
    }else CHECK("host-target-actual-member-definition",reference_eng_target(&ctx,&key,&target)&&target.role==WOOD_MEMBER_ROLE_BOUNDARY&&target.placement_id==1);
    WoodEngineeringContext engineering=app_eng_context(world);wood_engineering_sources_bind(ctx.engineering_sources,&engineering);
    EngBinding binding={0};binding.target=key;binding.source.kind=ENG_LITERAL;binding.source.value=9;GeoCoord value;
    CHECK("host-target-bound-source",wood_eng_effective(&engineering,&binding,&value,NULL,0)&&value==9);
    CHECK("host-target-world-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
static bool host_guide_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)opaque;uint32_t id;if(ref->provider!=APP_SOURCE_GUIDE||ref->key_size!=sizeof id)return false;memcpy(&id,ref->key,sizeof id);if(id!=1)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_AXIS_POSITION;out->unit=GEO_UNIT_LENGTH;out->context=(GeoSourceContext){true,7,1};return true;
}
static bool host_guide_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)graph;GeoSourceDescriptor descriptor;if(!host_guide_describe(opaque,ref,&descriptor))return false;
    ++*(unsigned *)opaque;out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){.context={true,7,1},.coordinate=3};return true;
}
static int host_guide_case(void)
{
    World *world=calloc(1,sizeof *world);CHECK("host-assembly-guide-memory",world);
    GeoGuide guide={.id=1,.placement_id=7,.direction=GEO_GUIDE_ALONG_V,.source=GEO_GUIDE_LOCAL};
    CHECK("host-assembly-guide-store",geo_guides_put(&world->geo.guide_lines,&guide));ReferenceEval ctx={0};ctx.world=world;
    ctx.sources=geo_eval_create(8152,0);CHECK("host-assembly-guide-graph",ctx.sources);unsigned calls=0;
    GeoSourceProvider provider={APP_SOURCE_GUIDE,"app.guide","host-guide-input/1",&calls,host_guide_describe,host_guide_evaluate};
    CHECK("host-assembly-guide-provider",geo_eval_register(ctx.sources,&provider));ctx.sources_registered=true;
    WoodAssemblyGuide actual;
    CHECK("host-assembly-guide-actual-axis",reference_asm_guide(&ctx,1,&actual)&&actual.surface_id==7&&actual.direction==ASM_DIR_U&&calls==1);
    ctx.use_current_values=true;
    CHECK("host-assembly-guide-snapshot-direct",reference_asm_guide(&ctx,1,&actual)&&actual.direction==ASM_DIR_V&&calls==1);
    reference_sources_dispose(&ctx);free(world);return 0;
}
static int host_pf_case(const char *name,const char *scene)
{
    World *world=calloc(1,sizeof *world);CHECK("host-pf-memory",world);CHECK("host-pf-scene",parse_scene_file(scene,world));
    ReferenceEval ctx={0};ctx.world=world;CHECK("host-pf-factory",reference_sources_ensure(&ctx));
    const PanelFill *fill=pf_find(world,1);CHECK("host-pf-fill",fill);ReferenceEval *previous=g_reference_active;g_reference_active=&ctx;
    if(!strcmp(name,"pf-threshold")){GeoQuantity value={0};host_fault=3;
        bool ok=pf_support_threshold(world,fill,&value);g_reference_active=previous;
        CHECK("host-pf-actual-threshold",ok&&value.num==17&&value.den==1&&value.unit==GEO_UNIT_LENGTH&&host_hits==1);
    }else{
        PfFootprint original[WORLD_MAX_TIMBERS],changed[WORLD_MAX_TIMBERS];size_t count=0,next=0;
        CHECK("host-pf-footprint-baseline",pf_support_footprints(world,fill,original,&count)&&count==3);
        WoodMemberPlacement anchors[WORLD_MAX_TIMBERS];memcpy(anchors,world->wood.anchors,sizeof anchors);host_fault=1;
        bool ok=pf_support_footprints(world,fill,changed,&next);g_reference_active=previous;
        CHECK("host-pf-actual-member-box",ok&&next==count&&host_hits==count);
        for(size_t i=0;i<count;++i)CHECK("host-pf-actual-box-projection",changed[i].lo[0]==original[i].lo[0]+17&&changed[i].hi[0]==original[i].hi[0]+17&&changed[i].lo[1]==original[i].lo[1]&&changed[i].hi[1]==original[i].hi[1]);
        CHECK("host-pf-authored-anchors-unchanged",!memcmp(anchors,world->wood.anchors,sizeof anchors));
    }
    reference_sources_dispose(&ctx);free(world);return 0;
}
static int host_context_case(const char *name)
{
    World *world=calloc(1,sizeof *world);CHECK("host-context-memory",world);
    PlacementSurface placement={.id=7,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={-100,-100,100,100}};
    CHECK("host-context-placement",app_placement_stage(world,&placement));placement.id=8;
    CHECK("host-context-second-placement",app_placement_stage(world,&placement));
    CHECK("host-context-named",geo_named_values_put(&world->geo.named_values,"s",3));
    GeoLinearExpression expression;geo_linear_begin(&expression,GEO_LINEAR_FLOOR_FINAL);
    CHECK("host-context-expression",geo_linear_append(&expression,1,1,(GeoLinearSource){APP_LINEAR_SOURCE,0,0,"spec:s"}));geo_linear_finish(&expression,true);
    bool datum_case=!strcmp(name,"context-datum"),frame_case=!strcmp(name,"context-frame");
    CHECK("host-context-datum-store",geo_datums_put(&world->geo.datum_planes,1,frame_case?0:1,&expression));
    GeoGuide guide={.id=1,.placement_id=7,.direction=GEO_GUIDE_ALONG_U,.source=frame_case?GEO_GUIDE_DATUM:GEO_GUIDE_LOCAL,.datum_id=1};
    if(!frame_case)guide.expression=expression;
    CHECK("host-context-guide-store",geo_guides_put(&world->geo.guide_lines,&guide));
    ReferenceEval ctx={0};ctx.world=world;CHECK("host-context-factory",reference_sources_ensure(&ctx));
    uint32_t id=1;GeoSourceRef ref={datum_case?APP_SOURCE_DATUM:APP_SOURCE_GUIDE,&id,sizeof id};GeoSourceDescriptor descriptor;
    CHECK("host-context-metadata-stays-unevaluated",geo_eval_describe(ctx.sources,ref,&descriptor)==GEO_SOURCE_OK&&descriptor.context.axis==-1&&
        geo_eval_node_count(ctx.sources)==1&&geo_eval_edge_count(ctx.sources)==0&&host_hits==0);
    if(datum_case){GeoDatum actual;CHECK("host-context-datum-definition-prime",geo_linear_definition_sources_datum(ctx.linear_definition_sources,1,&actual)&&actual.axis==1);
        CHECK("host-context-datum-decoy",geo_datums_put(&world->geo.datum_planes,1,0,&expression));
    }else if(!frame_case){GeoGuide actual;CHECK("host-context-guide-definition-prime",geo_linear_definition_sources_guide(ctx.linear_definition_sources,1,&actual)&&actual.placement_id==7&&actual.direction==GEO_GUIDE_ALONG_U);
        guide.placement_id=8;guide.direction=GEO_GUIDE_ALONG_V;CHECK("host-context-guide-decoy",geo_guides_put(&world->geo.guide_lines,&guide));
    }else host_fault=4;
    GeoAxisPosition actual;
    if(datum_case){CHECK("host-context-actual-datum-axis",reference_datum_position(&ctx,0,&actual)&&actual.coordinate==3&&!actual.context.has_placement&&actual.context.axis==1);
        CHECK("host-context-datum-authored-unchanged",geo_datums_at(&world->geo.datum_planes,0)->axis==0);
    }else{CHECK("host-context-actual-guide-context",reference_guide_position(&ctx,0,&actual)&&actual.coordinate==(frame_case?-3:3)&&actual.context.has_placement&&actual.context.placement==7&&actual.context.axis==1);
        if(frame_case)CHECK("host-context-actual-frame-intersection",host_hits==1&&host_has_edge(ctx.sources,APP_SOURCE_GUIDE,APP_SOURCE_PLACEMENT)&&host_has_edge(ctx.sources,APP_SOURCE_GUIDE,APP_SOURCE_DATUM));
        else{GuideLine consumer={.id=2,.placement_id=7,.direction=GUIDE_ALONG_U};GeoCoord value=-99;
            CHECK("host-context-reference-actual-guide-placement",reference_quantity(&ctx,&consumer,"guide:1",&value)&&value==3);
            CHECK("host-context-guide-authored-unchanged",geo_guides_at(&world->geo.guide_lines,0)->placement_id==8&&geo_guides_at(&world->geo.guide_lines,0)->direction==GEO_GUIDE_ALONG_V);
        }
        WoodAssemblyGuide eligibility;CHECK("host-context-assembly-actual-guide-context",reference_asm_guide(&ctx,1,&eligibility)&&eligibility.surface_id==7&&eligibility.direction==ASM_DIR_U);
    }
    CHECK("host-context-metadata-publishes-actual-context",geo_eval_describe(ctx.sources,ref,&descriptor)==GEO_SOURCE_OK&&!descriptor.context_from_value&&
        descriptor.context.axis==actual.context.axis&&descriptor.context.has_placement==actual.context.has_placement&&(!actual.context.has_placement||descriptor.context.placement==actual.context.placement));
    reference_sources_dispose(&ctx);free(world);return 0;
}
static int host_owned_case(const char *name)
{
    World *world=calloc(1,sizeof *world);CHECK("host-owned-memory",world);ReferenceEval ctx={0};ctx.world=world;
    if(!strcmp(name,"owned-failure")){
        world->wood.assembly.instance_count=1;world->wood.assembly.instances[0].id=3;
        strcpy(world->wood.assembly.instances[0].content,"{}");
        CHECK("host-owned-factory",reference_sources_ensure(&ctx));bool owned=true;
        CHECK("host-owned-failure-is-atomic",!reference_member_owned(&ctx,41,&owned)&&owned);
        ReferenceEval *previous=g_reference_active;g_reference_active=&ctx;
        bool denied=app_eng_owned(world,41);g_reference_active=previous;
        CHECK("host-owned-source-failure-denies-write",denied&&ctx.source_failure&&strstr(g_revalidate_error,"ownership source"));
    }else{
        world->wood.assembly.owner_count=1;world->wood.assembly.owners[0].timber=41;bool owned=true;
        if(!strcmp(name,"owned-replay")){g_assembly_replay=true;bool ok=reference_member_owned(&ctx,41,&owned);g_assembly_replay=false;
            CHECK("host-owned-replay-before-any-source",ok&&!owned&&!ctx.sources&&!ctx.source_failure);
        }else{ctx.use_current_values=true;
            CHECK("host-owned-snapshot-is-direct",reference_member_owned(&ctx,41,&owned)&&owned&&!ctx.sources&&!ctx.source_failure);
        }
    }
    reference_sources_dispose(&ctx);free(world);return 0;
}
int main(int argc,char **argv)
{
    if(argc<2||argc>3)return 2;
    if(!strcmp(argv[1],"target")||!strcmp(argv[1],"assembly-member"))return host_target_case(argv[1]);
    if(!strcmp(argv[1],"assembly-guide"))return host_guide_case();
    if(!strncmp(argv[1],"context-",8))return host_context_case(argv[1]);
    if(!strncmp(argv[1],"owned-",6))return host_owned_case(argv[1]);
    if(!strncmp(argv[1],"pf-",3))return argc==3?host_pf_case(argv[1],argv[2]):2;
    return host_pose_case(argv[1]);
}
