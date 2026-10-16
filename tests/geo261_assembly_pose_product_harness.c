/* Actual H footprint callback and W I42 check consume returned BOX geometry.
 * The test input replaces only member pose, while K placement storage is real. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)

typedef struct {GeoEvalContext *graph;GeoBox3 boxes[3];unsigned calls;} AssemblyPoseInput;
typedef struct {WoodAssemblyContext *assembly;AsmInstance instance;} AssemblyCheckInput;
static bool assembly_pose_id(const GeoSourceRef *ref,uint32_t *id)
{
    if(ref->provider!=APP_SOURCE_MEMBER_POSE||!ref->key||ref->key_size!=sizeof *id)return false;
    memcpy(id,ref->key,sizeof *id);return *id>=1&&*id<=3;
}
static bool assembly_pose_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)user;uint32_t id;if(!assembly_pose_id(ref,&id))return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;out->context=(GeoSourceContext){true,7,-1};return true;
}
static bool assembly_pose_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    AssemblyPoseInput *input=user;uint32_t id;if(graph!=input->graph||!assembly_pose_id(ref,&id))return false;
    ++input->calls;out->kind=GEO_SOURCE_BOX;out->as.box=input->boxes[id-1];return true;
}
static bool assembly_check_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)user;if(ref->provider!=18||ref->key_size!=1||memcmp(ref->key,"c",1))return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_DEFINITION;out->context.axis=-1;return true;
}
static bool assembly_check_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)graph;(void)ref;AssemblyCheckInput *input=user;
    if(!wood_assembly_instance_check_direct(input->assembly,&input->instance))return false;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"assembly-check-input/1","{}",2};return true;
}
static bool assembly_check_edge(GeoEvalContext *graph,GeoProviderToken source)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;GeoSourceNodeView a,b;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&geo_eval_node_at(graph,edge.consumer,&a)&&
            geo_eval_node_at(graph,edge.source,&b)&&a.source.provider==18&&b.source.provider==source)return true;}
    return false;
}
static int assembly_pose_case(unsigned mode)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK("assembly-h-world-memory",world&&before);
    PlacementSurface placement={0};placement.id=7;placement.frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    placement.rect=(GeoRect2){0,0,100,100};CHECK("assembly-h-real-placement-store",app_placement_stage(world,&placement));
    GeoRect2 rects[]={{0,0,10,100},{90,0,100,100},{10,40,90,50}};
    world->wood.timber_count=3;AssemblyPoseInput input={0};
    for(int i=0;i<3;++i){Timber *member=&world->wood.timbers[i];member->id=(uint32_t)i+1;member->placed=true;
        member->length=rects[i].max_u-rects[i].min_u;member->size_a=rects[i].max_v-rects[i].min_v;member->size_b=5;
        member->role=i==2?WOOD_MEMBER_ROLE_SECONDARY:WOOD_MEMBER_ROLE_PRIMARY;
        member->origin=(GeoPoint3){10+rects[i].min_u,20+rects[i].min_v,30};
        member->axis_length=(GeoVector3){1,0,0};member->axis_a=(GeoVector3){0,1,0};member->axis_b=(GeoVector3){0,0,1};
        world->wood.anchors[i].placement_id=7;world->wood.anchors[i].uv=(GeoPoint2){rects[i].min_u,rects[i].min_v};
        world->wood.anchors[i].length_direction=SURFACE_DIRECTION_POS_U;world->wood.anchors[i].depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
        input.boxes[i]=(GeoBox3){{member->origin,member->axis_length,member->axis_a,member->axis_b},{member->length,member->size_a,member->size_b}};
    }
    memcpy(before,world,sizeof *world);
    ReferenceEval ctx={0};ctx.world=world;ctx.sources=geo_eval_create(9200+mode,27);CHECK("assembly-h-graph",ctx.sources);input.graph=ctx.sources;
    ctx.placement_sources=geo_placement_sources_register(ctx.sources,&world->geo.placement_data,&world->geo.region_data,
        APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,NULL,NULL);CHECK("assembly-h-k-placement",ctx.placement_sources);
    GeoSourceProvider pose={APP_SOURCE_MEMBER_POSE,"woodworking.member.pose","assembly-pose-input/1",&input,assembly_pose_describe,assembly_pose_evaluate};
    CHECK("assembly-h-pose-input",geo_eval_register(ctx.sources,&pose));ctx.sources_registered=true;
    WoodAssemblyContext assembly=app_asm_context(world);reference_assembly_context(&ctx,&assembly);
    AssemblyCheckInput check={0};check.assembly=&assembly;check.instance.surface_id=7;
    for(int i=0;i<3;++i){check.instance.member[i]=(uint32_t)i+1;check.instance.timber[i]=(uint32_t)i+1;}
    check.instance.secondary[2]=true;check.instance.ends[2][0]=1;check.instance.ends[2][1]=2;
    GeoSourceProvider root={18,"test.assembly.check","assembly-check-input/1",&check,assembly_check_describe,assembly_check_evaluate};
    CHECK("assembly-h-check-provider",geo_eval_register(ctx.sources,&root));
    GeoRect2 unused={-4,-3,-2,-1};CHECK("assembly-h-old-callback-refusal-first",!reference_asm_footprint(&ctx,7,999,&unused)&&input.calls==0);
    if(mode==1)++input.boxes[2].frame.origin.x;
    if(mode==2){input.boxes[2].frame.axis_u=(GeoVector3){0,1,0};input.boxes[2].frame.axis_v=(GeoVector3){-1,0,0};}
    if(mode==3)check.instance.surface_id=999;
    GeoSourceValue value;GeoSourceStatus status=geo_eval_source(ctx.sources,(GeoSourceRef){18,"c",1},GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    CHECK("assembly-h-returned-pose-controls-i42",status==(mode?GEO_SOURCE_FAILED:GEO_SOURCE_OK));
    if(mode==3)CHECK("assembly-h-missing-surface-before-pose",input.calls==0&&!strcmp(g_engineering_error,"I42: missing instance surface"));
    else{
        CHECK("assembly-h-real-box-frame-edges",input.calls==3&&assembly_check_edge(ctx.sources,APP_SOURCE_MEMBER_POSE)&&assembly_check_edge(ctx.sources,APP_SOURCE_PLACEMENT));
        GeoRect2 actual;CHECK("assembly-h-numeric-footprint",reference_asm_footprint(&ctx,7,3,&actual));
        GeoRect2 expected=mode==2?(GeoRect2){0,40,10,120}:mode==1?(GeoRect2){11,40,91,50}:rects[2];
        CHECK("assembly-h-returned-box-origin-and-axes",!memcmp(&actual,&expected,sizeof actual));
        if(mode)CHECK("assembly-h-original-i42-message",!strcmp(g_engineering_error,"I42: secondary endpoints do not contact the declared inward primary sides"));
    }
    CHECK("assembly-h-world-and-anchor-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2||strcmp(argv[1],"pose"))return 2;
    for(unsigned mode=0;mode<4;++mode){int result=assembly_pose_case(mode);if(result)return result;}
    puts("PASS pose");return 0;
}
