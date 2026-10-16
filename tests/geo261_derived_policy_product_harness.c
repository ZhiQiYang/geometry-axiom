/* Actual H consumers, with controlled substitutions only at returned-value
 * seams. The authored World and its deliberate derived cache decoy stay put. */
#ifdef _WIN32
#undef _WIN32
#endif
#include "../geometry-core/kernel/source.h"
static GeoSourceStatus policy_product_eval(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source policy_product_eval
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#undef geo_eval_source
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static int policy_product_fault;
static GeoSourceStatus policy_product_eval(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);GeoPlacementSourceKind kind;uint32_t id;
    if(status==GEO_SOURCE_OK&&policy_product_fault==1&&ref.provider==APP_SOURCE_PLACEMENT&&
       geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_REGIONS&&id==10&&out->as.regions.count==1){
        static GeoRegionView region;static GeoPoint2 points[GEO_LOOP_MAX_VERTICES];region=out->as.regions.regions[0];
        memcpy(points,region.outline.v,region.outline.count*sizeof *points);points[0].u=7;
        region.outline.v=points;out->as.regions.regions=&region;
    }return status;
}
/* Linked only by the changed W source object. Normal product objects never
 * call it; the control changes a returned value without editing source caches. */
void geo261_policy_source_control(WoodFinishSourceKind kind,uint32_t id,GeoSourceValue *out)
{
    if(kind!=WOOD_FINISH_SOURCE_DERIVED_POLICY||id!=10||policy_product_fault<2||out->kind!=GEO_SOURCE_DEFINITION)return;
    static unsigned char bytes[65536];if(out->as.definition.content_size>sizeof bytes)return;
    memcpy(bytes,out->as.definition.content,out->as.definition.content_size);
    /* Fixture: version/id/kind/count, one component/hole count, outer count.
     * First edge starts at byte 18; its key starts at byte 21. */
    if(policy_product_fault==2)bytes[18]=WOOD_EDGE_FREE;
    else if(policy_product_fault==3){for(size_t i=21;i+3<out->as.definition.content_size;++i)
        if(bytes[i]=='"'&&bytes[i+1]=='e'&&bytes[i+2]=='0'&&bytes[i+3]=='"'){bytes[i+2]='9';break;}}
    out->as.definition.content=bytes;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);
    CHECK("derived-product-memory",world&&before);
    CHECK("derived-product-load",parse_scene_file(argv[1],world));
    PlacementSurface decoy={.id=10,.derived_fill_id=1,.derived_h=999,
        .frame={{500,500,500},{1,0,0},{0,1,0},{0,0,1}},.component_count=1};
    decoy.components[0].id=10;decoy.components[0].outline.count=4;
    decoy.components[0].outline.v[0]=(GeoPoint2){500,500};decoy.components[0].outline.v[1]=(GeoPoint2){600,500};
    decoy.components[0].outline.v[2]=(GeoPoint2){600,600};decoy.components[0].outline.v[3]=(GeoPoint2){500,600};
    for(size_t i=0;i<4;++i)decoy.components[0].outline.fixity[i]=WOOD_EDGE_FIXED;
    CHECK("derived-product-cache-decoy",app_placement_stage(world,&decoy));
    if(!strcmp(argv[2],"snapshot")){
        AppWorldCandidate *owner=app_world_candidate_create(world);CHECK("derived-product-snapshot-candidate",owner);
        ReferenceEval active={0};active.world=&owner->after;CHECK("derived-product-snapshot-factory",reference_sources_ensure(&active));
        WoodDerivedValue value;CHECK("derived-product-snapshot-prime",wood_finish_sources_read_derived(active.finish_sources,10,&value));
        app_candidate_set_evaluation_state(owner->control,&active,NULL);
        AppWorldCandidate *previous=g_active_app_candidate;g_active_app_candidate=owner;
        ReferenceEval snapshot={0};snapshot.world=&owner->after;snapshot.use_current_values=true;
        size_t nodes=geo_eval_node_count(active.sources),edges=geo_eval_edge_count(active.sources);int hole=-99,edge=-99;
        bool resolved=reference_derived_resolve(&snapshot,&decoy,"[[\"e0\",0,1]]",&hole,&edge);
        g_active_app_candidate=previous;
        CHECK("derived-product-snapshot-keeps-supplied-geometry",!resolved&&hole==-99&&edge==-99);
        CHECK("derived-product-snapshot-does-not-use-active-graph",nodes==geo_eval_node_count(active.sources)&&edges==geo_eval_edge_count(active.sources));
        app_candidate_set_evaluation_state(owner->control,NULL,NULL);reference_sources_dispose(&active);app_world_candidate_destroy(owner);
        free(before);free(world);return 0;
    }
    ReferenceEval ctx={0};ctx.world=world;CHECK("derived-product-factory",reference_sources_ensure(&ctx));
    WoodDerivedValue primed;CHECK("derived-product-policy-prime",wood_finish_sources_read_derived(ctx.finish_sources,10,&primed));
    memcpy(before,world,sizeof *world);
    if(!strcmp(argv[2],"geometry"))policy_product_fault=1;
    else if(!strcmp(argv[2],"fixity"))policy_product_fault=2;
    else if(!strcmp(argv[2],"guide-key")||!strcmp(argv[2],"member-key"))policy_product_fault=3;
    else return 2;
    PlacementSurface actual=decoy;
    CHECK("derived-product-read",reference_member_placement(&ctx,&actual,NULL));
    if(!strcmp(argv[2],"geometry")){
        CHECK("derived-product-geometry-is-returned-value",actual.components[0].outline.v[0].u==7&&actual.components[0].outline.v[1].u==100&&actual.frame.origin.z==9&&actual.derived_h==30);
    }else if(!strcmp(argv[2],"fixity")){
        CHECK("derived-product-fixity-is-returned-value",actual.components[0].outline.fixity[0]==WOOD_EDGE_FIXED);
    }else if(!strcmp(argv[2],"guide-key")){
        GuideLine guide={0};guide.placement_id=10;guide.direction=GUIDE_ALONG_U;Coord coordinate=-99;
        CHECK("derived-product-guide-key-is-returned-value",reference_quantity_raw(&ctx,&guide,"edge-key:5b5b226530222c302c315d5d:v",&coordinate)&&coordinate==0);
    }else{
        AppMemberPlacementScratch geometry={0};geometry.placement=actual;
        AppMemberReferenceContext member={0};member.world=world;member.evaluation=&ctx;member.geometry=&geometry;
        int hole=-99,edge=-99;char error[256]={0};
        CHECK("derived-product-member-key-is-returned-value",app_member_reference_key(&member,10,"[[\"e0\",0,1]]",&hole,&edge,error,sizeof error)&&hole==-1&&edge==0);
    }
    CHECK("derived-product-world-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
