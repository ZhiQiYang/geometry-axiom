/* Actual H adapter and linked K/W objects. Only test counters are inserted
 * at the real eager wrapper/facts callback; providers and geometry are real. */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stddef.h>
static size_t dead_facts_eager_calls,dead_facts_callback_calls;
#define main geometry_dead_facts_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
typedef struct {GeoEvalContext *graph;GeoBox3 box;size_t calls;bool fail;} PoseInput;
typedef struct {World *world,*before;PlacementSurface placement;ReferenceEval ctx;PoseInput pose;} Fixture;
static bool pose_key(const GeoSourceRef *ref)
{uint32_t id;if(ref->provider!=APP_SOURCE_MEMBER_POSE||!ref->key||ref->key_size!=sizeof id)return false;memcpy(&id,ref->key,sizeof id);return id==41;}
static bool pose_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{(void)user;if(!pose_key(ref))return false;memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;out->context=(GeoSourceContext){true,7,-1};return true;}
static bool pose_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{PoseInput *p=user;if(graph!=p->graph||!pose_key(ref))return false;++p->calls;if(p->fail)return false;out->kind=GEO_SOURCE_BOX;out->as.box=p->box;return true;}
static int setup(Fixture *f)
{
    memset(f,0,sizeof *f);f->world=calloc(1,sizeof *f->world);f->before=malloc(sizeof *f->before);
    CHECK("dead-facts-fixture-memory",f->world&&f->before);
    f->placement.id=7;f->placement.frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    f->placement.rect=(GeoRect2){0,0,1000,1000};CHECK("dead-facts-real-placement-store",app_placement_stage(f->world,&f->placement));
    f->world->wood.timber_count=1;Timber *m=&f->world->wood.timbers[0];
    m->id=41;m->length=40;m->size_a=10;m->size_b=5;m->role=WOOD_MEMBER_ROLE_PRIMARY;m->cut_priority=2;m->placed=true;m->auto_length=true;
    m->origin=f->placement.frame.origin;m->axis_length=(GeoVector3){1,0,0};m->axis_a=(GeoVector3){0,1,0};m->axis_b=(GeoVector3){0,0,1};
    f->world->wood.anchors[0].placement_id=7;f->world->wood.anchors[0].uv=(GeoPoint2){0,0};f->world->wood.anchors[0].order=1;
    f->world->wood.anchors[0].length_direction=SURFACE_DIRECTION_POS_U;f->world->wood.anchors[0].depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
    memcpy(f->before,f->world,sizeof *f->before);f->ctx.world=f->world;f->ctx.sources=geo_eval_create(7001,17);
    CHECK("dead-facts-graph",f->ctx.sources);
    f->ctx.placement_sources=geo_placement_sources_register(f->ctx.sources,&f->world->geo.placement_data,&f->world->geo.region_data,APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,NULL,NULL);
    CHECK("dead-facts-placement-provider",f->ctx.placement_sources);
    WoodDefinitionContext d={&f->world->wood,&f->world->geo.region_data,APP_SOURCE_ENCLOSURE,APP_SOURCE_REGION};
    f->ctx.definition_sources=wood_definition_sources_create(f->ctx.sources,APP_SOURCE_WOOD_DEFINITION,&d);
    CHECK("dead-facts-definition-provider",f->ctx.definition_sources);
    f->pose.graph=f->ctx.sources;f->pose.box=(GeoBox3){{{40,70,30},{1,0,0},{0,1,0},{0,0,1}},{40,10,5}};
    GeoSourceProvider p={APP_SOURCE_MEMBER_POSE,"woodworking.member.pose","dead-facts-pose/1",&f->pose,pose_describe,pose_evaluate};
    CHECK("dead-facts-pose-provider",geo_eval_register(f->ctx.sources,&p));
    f->ctx.contact_sources=wood_contact_sources_create(f->ctx.sources,APP_SOURCE_CONTACT,reference_contact_facts,&f->ctx);
    CHECK("dead-facts-contact-provider",f->ctx.contact_sources);f->ctx.sources_registered=true;return 0;
}
static void dispose(Fixture *f)
{reference_sources_dispose(&f->ctx);free(f->before);free(f->world);}
/* Frozen pre-change call order. This oracle deliberately retains eager work. */
static size_t legacy_collect(const World *world,const PlacementSurface *placement,const SpaceBoundarySurface *boundary,bool along_v,const Timber *exclude,StopFace *out,size_t cap)
{AppContactFacts facts;app_contact_facts(world,placement,boundary,&facts);AppContactResolve context={world,&facts.world};size_t count=0;return app_contact_resolve_stops(&context,along_v,exclude,out,cap,&count)?count:0;}
static bool legacy_ends(const World *world,const PlacementSurface *placement,const SpaceBoundarySurface *boundary,const WoodMember *member,bool along_v,Coord lo,Coord hi,Coord clo,Coord chi,char *error,size_t cap)
{
    ReferenceEval *ctx=app_reference_sources_for_world(world);
    if(!ctx||ctx->use_current_values)return timber_end_face_check(world,placement,boundary,member,along_v,lo,hi,clo,chi,error,cap);
    AppContactFacts facts;app_contact_facts(world,placement,boundary,&facts);
    AppReferenceContactResolve source={.world=world,.evaluation=ctx,.target=&facts.world};
    return wood_contact_end_faces_with_sources(&facts.world,member,along_v,lo,hi,clo,chi,app_reference_end_stops,&source,error,cap);
}
static bool same_source(GeoSourceRef a,GeoSourceRef b)
{return a.provider==b.provider&&a.key_size==b.key_size&&(!a.key_size||!memcmp(a.key,b.key,a.key_size));}
static bool same_loop(GeoLoop2View a,GeoLoop2View b)
{return a.count==b.count&&(!a.count||!memcmp(a.v,b.v,a.count*sizeof *a.v));}
static bool same_value(const GeoSourceValue *a,const GeoSourceValue *b)
{
    if(!a||!b)return a==b;if(a->kind!=b->kind)return false;
    switch(a->kind){
    case GEO_SOURCE_DEFINITION:return !strcmp(a->as.definition.schema,b->as.definition.schema)&&a->as.definition.content_size==b->as.definition.content_size&&(!a->as.definition.content_size||!memcmp(a->as.definition.content,b->as.definition.content,a->as.definition.content_size));
    case GEO_SOURCE_FEATURE:return a->as.feature.key_size==b->as.feature.key_size&&(!a->as.feature.key_size||!memcmp(a->as.feature.key,b->as.feature.key,a->as.feature.key_size))&&!memcmp(&a->as.feature.segment,&b->as.feature.segment,sizeof a->as.feature.segment);
    case GEO_SOURCE_BOX:return !memcmp(&a->as.box,&b->as.box,sizeof a->as.box);
    case GEO_SOURCE_FRAME:return !memcmp(&a->as.frame,&b->as.frame,sizeof a->as.frame);
    case GEO_SOURCE_REGION_SET:
        if(a->as.regions.count!=b->as.regions.count)return false;
        for(size_t i=0;i<a->as.regions.count;++i){const GeoRegionView *x=&a->as.regions.regions[i],*y=&b->as.regions.regions[i];
            if(!same_loop(x->outline,y->outline)||x->hole_count!=y->hole_count)return false;
            for(size_t h=0;h<x->hole_count;++h)if(!same_loop(x->holes[h],y->holes[h]))return false;}
        return true;
    case GEO_SOURCE_QUANTITY:return a->as.quantity.num==b->as.quantity.num&&a->as.quantity.den==b->as.quantity.den&&a->as.quantity.unit==b->as.quantity.unit;
    case GEO_SOURCE_AXIS_POSITION:return a->as.position.coordinate==b->as.position.coordinate&&a->as.position.context.has_placement==b->as.position.context.has_placement&&a->as.position.context.placement==b->as.position.context.placement&&a->as.position.context.axis==b->as.position.context.axis;
    }
    return false;
}
static bool same_graph(GeoEvalContext *a,GeoEvalContext *b)
{
    if(geo_eval_node_count(a)!=geo_eval_node_count(b)||geo_eval_edge_count(a)!=geo_eval_edge_count(b))return false;
    for(size_t i=0;i<geo_eval_node_count(a);++i){GeoSourceNodeView x,y;
        if(!geo_eval_node_at(a,i,&x)||!geo_eval_node_at(b,i,&y)||!same_source(x.source,y.source)||x.state!=y.state||x.status!=y.status||x.described!=y.described||
           x.descriptor.kind!=y.descriptor.kind||x.descriptor.unit!=y.descriptor.unit||x.descriptor.context.has_placement!=y.descriptor.context.has_placement||
           x.descriptor.context.placement!=y.descriptor.context.placement||x.descriptor.context.axis!=y.descriptor.context.axis||x.descriptor.retry_failure!=y.descriptor.retry_failure||
           x.descriptor.context_from_value!=y.descriptor.context_from_value||!same_value(x.value,y.value))return false;}
    for(size_t i=0;i<geo_eval_edge_count(a);++i){GeoSourceEdge x,y;if(!geo_eval_edge_at(a,i,&x)||!geo_eval_edge_at(b,i,&y)||x.consumer!=y.consumer||x.source!=y.source||x.kind!=y.kind)return false;}
    return true;
}
static bool same_faces(const StopFace *a,const StopFace *b,size_t n)
{for(size_t i=0;i<n;++i)if(a[i].kind!=b[i].kind||a[i].boundary_id!=b[i].boundary_id||a[i].timber_id!=b[i].timber_id||a[i].hole_index!=b[i].hole_index||a[i].edge_index!=b[i].edge_index||a[i].fixity!=b[i].fixity||a[i].fixed!=b[i].fixed||a[i].lo!=b[i].lo||a[i].hi!=b[i].hi)return false;return true;}
static void counters(void){dead_facts_eager_calls=dead_facts_callback_calls=0;g_revalidate_error[0]=0;}
static int collect_case(bool failure,int fallback)
{
    Fixture a,b;CHECK("dead-facts-setup-a",!setup(&a));CHECK("dead-facts-setup-b",!setup(&b));a.pose.fail=b.pose.fail=failure;
    a.ctx.use_current_values=b.ctx.use_current_values=fallback==2;
    StopFace x[8],y[8];memset(x,0x5a,sizeof x);memset(y,0x5a,sizeof y);
    ReferenceEval *old=g_reference_active;g_reference_active=fallback==1?NULL:&a.ctx;counters();
    size_t n=collect_stop_faces(a.world,&a.placement,NULL,false,NULL,x,8),eager=dead_facts_eager_calls,callbacks=dead_facts_callback_calls;char error[sizeof g_revalidate_error];memcpy(error,g_revalidate_error,sizeof error);
    if(!fallback&&!failure)CHECK("dead-collect-skips-unused-eager-facts",eager==0);
    if(fallback)CHECK("dead-collect-fallback-keeps-eager-facts",eager==1&&callbacks==0);
    g_reference_active=fallback==1?NULL:&b.ctx;counters();size_t m=legacy_collect(b.world,&b.placement,NULL,false,NULL,y,8);
    CHECK("dead-collect-exact-original-output",n==m&&same_faces(x,y,n));
    CHECK("dead-collect-callback-and-provider-sequence",callbacks==dead_facts_callback_calls&&a.pose.calls==b.pose.calls);
    CHECK("dead-collect-original-ordered-graph",same_graph(a.ctx.sources,b.ctx.sources));
    CHECK("dead-collect-original-error",!memcmp(error,g_revalidate_error,sizeof error)&&a.ctx.source_failure==b.ctx.source_failure);
    if(failure){StopFace untouched[8];memset(untouched,0x5a,sizeof untouched);CHECK("dead-collect-failure-keeps-output",n==0&&!memcmp(x,untouched,sizeof x)&&a.ctx.source_failure&&callbacks==1);}
    else CHECK("dead-collect-real-contact-output",n==4&&(!fallback?callbacks==1:true));
    CHECK("dead-collect-world-unchanged",!memcmp(a.world,a.before,sizeof *a.world)&&!memcmp(b.world,b.before,sizeof *b.world));
    g_reference_active=old;dispose(&a);dispose(&b);return 0;
}
static SpaceBoundarySurface elbow(void)
{SpaceBoundarySurface b={0};b.id=7;b.outline.count=6;GeoPoint2 v[6]={{0,0},{100,0},{100,50},{50,50},{50,100},{0,100}};memcpy(b.outline.v,v,sizeof v);for(size_t i=0;i<6;++i)b.outline.fixity[i]=WOOD_STOP_FIXED;return b;}
static int end_case(unsigned mode)
{
    Fixture a,b;CHECK("dead-end-setup-a",!setup(&a));CHECK("dead-end-setup-b",!setup(&b));a.pose.fail=b.pose.fail=mode!=0;
    WoodMember self={0};self.id=17;self.role=WOOD_MEMBER_ROLE_PRIMARY;self.cut_priority=2;
    SpaceBoundarySurface boundary=elbow();const SpaceBoundarySurface *region=mode==2?&boundary:NULL;
    Coord lo=mode==2?0:20,hi=mode==2?100:80,clo=mode==2?40:20,chi=mode==2?50:30;
    char x[256],y[256];memset(x,0x5a,sizeof x);memset(y,0x5a,sizeof y);strcpy(x,"unchanged");strcpy(y,"unchanged");
    ReferenceEval *old=g_reference_active;g_reference_active=&a.ctx;counters();
    bool ok=app_reference_end_faces(a.world,&a.placement,region,&self,false,lo,hi,clo,chi,x,sizeof x);size_t eager=dead_facts_eager_calls,callbacks=dead_facts_callback_calls;
    if(!mode)CHECK("dead-end-skips-unused-eager-members",eager==0);
    g_reference_active=&b.ctx;counters();bool expected=legacy_ends(b.world,&b.placement,region,&self,false,lo,hi,clo,chi,y,sizeof y);
    CHECK("dead-end-original-result-error",ok==expected&&!memcmp(x,y,sizeof x));
    CHECK("dead-end-callback-provider-sequence",callbacks==dead_facts_callback_calls&&a.pose.calls==b.pose.calls);
    CHECK("dead-end-original-ordered-graph",same_graph(a.ctx.sources,b.ctx.sources));
    if(mode==2)CHECK("dead-end-extension-before-provider-failure",!ok&&strstr(x,"V_EXTENSION")&&callbacks==0&&a.pose.calls==0&&geo_eval_node_count(a.ctx.sources)==0);
    else if(mode==1)CHECK("dead-end-provider-error-at-original-position",!ok&&!strcmp(x,"I8: ordered contact source evaluation failed")&&callbacks==1&&a.pose.calls==1);
    else CHECK("dead-end-real-source-success",ok&&callbacks==2&&a.pose.calls==1&&!strcmp(x,"unchanged"));
    CHECK("dead-end-world-unchanged",!memcmp(a.world,a.before,sizeof *a.world)&&!memcmp(b.world,b.before,sizeof *b.world));
    g_reference_active=old;dispose(&a);dispose(&b);return 0;
}
static int domain_case(void)
{
    Fixture f;CHECK("dead-domain-setup",!setup(&f));AppContactFacts a,b;SpaceBoundarySurface region=elbow();
    for(unsigned mode=0;mode<4;++mode){PlacementSurface p=f.placement;const SpaceBoundarySurface *boundary=mode==1?&region:NULL;
        if(mode>=2){p.derived_fill_id=9;p.component_count=mode==2?2:0;p.components[0]=region;p.components[1]=region;p.components[1].id=8;}
        memset(&a,0x5a,sizeof a);memset(&b,0x5a,sizeof b);app_contact_domain_only(&p,boundary,&a);app_contact_facts(f.world,&p,boundary,&b);
        CHECK("dead-domain-placement-and-count",a.world.placement_id==b.world.placement_id&&a.world.region_count==b.world.region_count);
        CHECK("dead-domain-effective-role-boundary",a.world.role_boundary&&b.world.role_boundary&&!memcmp(a.world.role_boundary,b.world.role_boundary,sizeof *a.world.role_boundary));
        for(size_t i=0;i<a.world.region_count;++i)CHECK("dead-domain-exact-component-view",!memcmp(a.world.regions[i],b.world.regions[i],sizeof *a.world.regions[i]));
        if(mode==2)CHECK("dead-domain-derived-component-pointer-lifetime",a.world.regions[0]==&p.components[0]&&a.world.regions[1]==&p.components[1]);
        CHECK("dead-domain-no-premature-member-view",a.world.member_count==0&&a.world.members==NULL);
    }
    dispose(&f);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"collect"))return collect_case(false,0);
    if(!strcmp(argv[1],"collect-failure"))return collect_case(true,0);
    if(!strcmp(argv[1],"fallback")){int r=collect_case(false,1);return r?r:collect_case(false,2);}
    if(!strcmp(argv[1],"ends"))return end_case(0);
    if(!strcmp(argv[1],"end-failure"))return end_case(1);
    if(!strcmp(argv[1],"extension"))return end_case(2);
    if(!strcmp(argv[1],"domain"))return domain_case();return 2;
}
