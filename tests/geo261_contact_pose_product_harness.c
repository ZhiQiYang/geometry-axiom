/* The actual H adapter consumes typed BOX values, not its World anchor copy.
 * Only the pose provider is a test input. K placement sources, H contact facts,
 * W contact sources/policy, and the FEATURE-to-stop consumer are production. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)

typedef struct {GeoEvalContext *graph;GeoBox3 box;unsigned calls;} ContactPoseInput;
static bool contact_pose_key(const GeoSourceRef *ref)
{
    uint32_t id;if(ref->provider!=APP_SOURCE_MEMBER_POSE||!ref->key||ref->key_size!=sizeof id)return false;
    memcpy(&id,ref->key,sizeof id);return id==41;
}
static bool contact_pose_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)user;if(!contact_pose_key(ref))return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;
    out->context=(GeoSourceContext){true,7,-1};return true;
}
static bool contact_pose_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    ContactPoseInput *input=user;if(graph!=input->graph||!contact_pose_key(ref))return false;
    ++input->calls;out->kind=GEO_SOURCE_BOX;out->as.box=input->box;return true;
}
static bool contact_pose_sides(const WoodStopFace *faces,size_t count,GeoCoord left,GeoCoord right,GeoCoord lo,GeoCoord hi)
{
    size_t found=0;
    for(size_t i=0;i<count;++i){const WoodStopFace *f=&faces[i];
        if(f->kind!=WOOD_STOP_MEMBER_SIDE)continue;
        if(found>=2||f->timber_id!=41||f->edge_index!=(int)found||f->fixed!=(found?right:left)||f->lo!=lo||f->hi!=hi)return false;
        ++found;
    }
    return found==2;
}
static bool contact_pose_has_edge(GeoEvalContext *graph,GeoProviderToken consumer,GeoProviderToken source)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;GeoSourceNodeView a,b;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&
           geo_eval_node_at(graph,edge.consumer,&a)&&geo_eval_node_at(graph,edge.source,&b)&&
           a.source.provider==consumer&&b.source.provider==source)return true;
    }
    return false;
}
static int contact_pose_case(unsigned mode)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);CHECK("contact-h-world-memory",world&&before);
    PlacementSurface placement={0};placement.id=7;placement.frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    placement.rect=(GeoRect2){0,0,1000,1000};CHECK("contact-h-real-placement-store",app_placement_stage(world,&placement));
    world->wood.timber_count=1;Timber *member=&world->wood.timbers[0];member->id=41;member->length=40;member->size_a=10;member->size_b=5;
    member->role=WOOD_MEMBER_ROLE_PRIMARY;member->cut_priority=2;member->placed=true;member->auto_length=true;
    member->origin=placement.frame.origin;member->axis_length=(GeoVector3){1,0,0};member->axis_a=(GeoVector3){0,1,0};member->axis_b=(GeoVector3){0,0,1};
    world->wood.anchors[0].placement_id=7;world->wood.anchors[0].uv=(GeoPoint2){0,0};world->wood.anchors[0].order=1;
    world->wood.anchors[0].length_direction=SURFACE_DIRECTION_POS_U;world->wood.anchors[0].depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
    memcpy(before,world,sizeof *world);
    ReferenceEval ctx={0};ctx.world=world;ctx.sources=geo_eval_create(8100+mode,17);CHECK("contact-h-candidate-graph",ctx.sources);
    ctx.placement_sources=geo_placement_sources_register(ctx.sources,&world->geo.placement_data,&world->geo.region_data,
        APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,NULL,NULL);CHECK("contact-h-real-k-placement-provider",ctx.placement_sources);
    WoodDefinitionContext definitions={&world->wood,&world->geo.region_data,APP_SOURCE_ENCLOSURE,APP_SOURCE_REGION};
    ctx.definition_sources=wood_definition_sources_create(ctx.sources,APP_SOURCE_WOOD_DEFINITION,&definitions);
    CHECK("contact-h-real-authored-definition-provider",ctx.definition_sources);
    ContactPoseInput input={0};input.graph=ctx.sources;
    input.box=(GeoBox3){{{40,70,30},{1,0,0},{0,1,0},{0,0,1}},{40,10,5}};
    if(mode)input.box.frame.origin=(GeoPoint3){47,81,30};
    if(mode==2){input.box.frame.axis_u=(GeoVector3){0,1,0};input.box.frame.axis_v=(GeoVector3){-1,0,0};}
    GeoSourceProvider provider={APP_SOURCE_MEMBER_POSE,"woodworking.member.pose","contact-pose-input/1",&input,contact_pose_describe,contact_pose_evaluate};
    CHECK("contact-h-pose-input-provider",geo_eval_register(ctx.sources,&provider));
    ctx.contact_sources=wood_contact_sources_create(ctx.sources,APP_SOURCE_CONTACT,reference_contact_facts,&ctx);
    CHECK("contact-h-real-contact-provider",ctx.contact_sources);ctx.sources_registered=true;
    ReferenceEval *previous=g_reference_active;g_reference_active=&ctx;
    WoodStopFace faces[8];size_t count=99;bool handled=false;
    bool ok=app_contact_sources_collect(world,7,false,NULL,faces,8,&handled,&count);g_reference_active=previous;
    CHECK("contact-h-uses-active-candidate-and-real-collector",ok&&handled&&!ctx.source_failure&&count==4&&input.calls==1);
    if(mode==0)CHECK("contact-h-box-origin-controls-stop",contact_pose_sides(faces,count,30,70,50,60));
    else if(mode==1)CHECK("contact-h-box-translation-controls-stop",contact_pose_sides(faces,count,37,77,61,71));
    else CHECK("contact-h-box-axes-control-stop",contact_pose_sides(faces,count,27,37,61,101));
    CHECK("contact-h-real-box-and-placement-value-edges",contact_pose_has_edge(ctx.sources,APP_SOURCE_CONTACT,APP_SOURCE_MEMBER_POSE)&&
        contact_pose_has_edge(ctx.sources,APP_SOURCE_CONTACT,APP_SOURCE_PLACEMENT));
    CHECK("contact-h-world-and-anchor-remain-unchanged",!memcmp(before,world,sizeof *world));
    Timber copied=*member;g_reference_active=&ctx;handled=false;
    ok=app_contact_sources_collect(world,7,false,&copied,faces,8,&handled,&count);g_reference_active=previous;
    CHECK("contact-h-equal-id-copy-is-not-excluded",ok&&handled&&count==4&&input.calls==1);
    g_reference_active=&ctx;handled=false;
    ok=app_contact_sources_collect(world,7,false,member,faces,8,&handled,&count);g_reference_active=previous;
    CHECK("contact-h-original-pointer-is-excluded",ok&&handled&&count==2&&input.calls==1);
    CHECK("contact-h-final-world-and-anchor-remain-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2||strcmp(argv[1],"pose"))return 2;
    for(unsigned mode=0;mode<3;++mode){int result=contact_pose_case(mode);if(result)return result;}
    puts("PASS pose");return 0;
}
