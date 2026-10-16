/* H consumes the values actually returned by K. Cache decoys below change
 * only existing derived fields, leaving every authored definition intact. */
#ifdef _WIN32
#undef _WIN32
#endif
#include "../geometry-core/kernel/source.h"
static GeoSourceStatus linear_product_eval(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source linear_product_eval
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#undef geo_eval_source
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static unsigned linear_product_fault,linear_product_hits;
static GeoSourceStatus linear_product_eval(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);
#ifdef GEO261_LINEAR_RETURN_CONTROL
    uint32_t id=0;if(ref.key_size==sizeof id)memcpy(&id,ref.key,sizeof id);
    if(status==GEO_SOURCE_OK&&id==1&&out->kind==GEO_SOURCE_AXIS_POSITION){
        if(linear_product_fault==1&&ref.provider==APP_SOURCE_DATUM){out->as.position.coordinate=17;++linear_product_hits;}
        if(linear_product_fault==2&&ref.provider==APP_SOURCE_GUIDE){out->as.position.coordinate=17;++linear_product_hits;}
        if(linear_product_fault==3&&ref.provider==APP_SOURCE_GUIDE){out->as.position.context.axis=1;++linear_product_hits;}
    }
#endif
    return status;
}
/* The changed K provider calls this after a successful definition request.
 * Its own memoized canonical bytes and the World authoring remain untouched. */
void geo261_linear_definition_product_control(GeoLinearDefinitionKind kind,uint32_t id,GeoSourceValue *out)
{
    static unsigned char content[GEO_LINEAR_DEFINITION_CONTENT_MAX];size_t size=0;
    if(out->kind!=GEO_SOURCE_DEFINITION)return;
    if(linear_product_fault==4&&kind==GEO_LINEAR_DEFINITION_DATUM&&id==1){GeoDatum datum;
        if(!geo_datum_definition_decode(out->as.definition.content,out->as.definition.content_size,&datum)||datum.expression.count!=1)return;
        datum.expression.terms[0].numerator=2;size=geo_datum_definition_encode(&datum,content);
    }else if(linear_product_fault==5&&kind==GEO_LINEAR_DEFINITION_GUIDE&&id==2){GeoGuide guide;
        if(!geo_guide_definition_decode(out->as.definition.content,out->as.definition.content_size,&guide)||guide.expression.count!=1)return;
        guide.expression.terms[0].numerator=2;size=geo_guide_definition_encode(&guide,content);
    }
    if(size){out->as.definition.content=content;out->as.definition.content_size=size;++linear_product_hits;}
}
static bool decoy_named(void *user,const GeoLinearSource *source,GeoQuantity *out)
{(void)user;(void)source;*out=(GeoQuantity){99,1,GEO_UNIT_LENGTH};return true;}
static bool cache_guide(World *world,size_t index,GeoCoord coordinate)
{GeoGuide guide=*geo_guides_at(&world->geo.guide_lines,index);guide.offset=coordinate;return geo_guides_put(&world->geo.guide_lines,&guide);}
static int snapshot_case(World *world,World *before)
{
    CHECK("linear-product-snapshot-guide-decoy",cache_guide(world,0,99));
    CHECK("linear-product-snapshot-datum-decoy",geo_datums_evaluate(&world->geo.datum_planes,0,decoy_named,NULL).status==GEO_LINEAR_OK);
    memcpy(before,world,sizeof *before);
    AppWorldCandidate *owner=app_world_candidate_create(world);CHECK("linear-product-snapshot-owner",owner);
    ReferenceEval active={0};active.world=&owner->after;CHECK("linear-product-snapshot-active",reference_sources_ensure(&active));
    app_candidate_set_evaluation_state(owner->control,&active,NULL);AppWorldCandidate *previous=g_active_app_candidate;g_active_app_candidate=owner;
    ReferenceEval ctx={0};ctx.world=world;ctx.use_current_values=true;GeoAxisPosition datum,guide;
    size_t nodes=geo_eval_node_count(active.sources),edges=geo_eval_edge_count(active.sources);
    bool ok=reference_datum_position(&ctx,0,&datum)&&reference_guide_position(&ctx,0,&guide);
    g_active_app_candidate=previous;
    CHECK("linear-product-snapshot-preserves-own-cache",ok&&datum.coordinate==99&&guide.coordinate==99&&guide.context.axis==0);
    CHECK("linear-product-snapshot-not-ambient",nodes==geo_eval_node_count(active.sources)&&edges==geo_eval_edge_count(active.sources));
    for(size_t i=0;i<geo_eval_node_count(ctx.sources);++i){GeoSourceNodeView node;CHECK("linear-product-snapshot-node",geo_eval_node_at(ctx.sources,i,&node));
        CHECK("linear-product-snapshot-no-definition-evaluation",node.source.provider!=APP_SOURCE_LINEAR_DEFINITION);}
    CHECK("linear-product-snapshot-world-unchanged",!memcmp(before,world,sizeof *world));
    reference_sources_dispose(&ctx);app_candidate_set_evaluation_state(owner->control,NULL,NULL);reference_sources_dispose(&active);app_world_candidate_destroy(owner);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);
    CHECK("linear-product-memory",world&&before);CHECK("linear-product-load",parse_scene_file(argv[1],world));
    if(!strcmp(argv[2],"snapshot")){int result=snapshot_case(world,before);free(before);free(world);return result;}
    ReferenceEval ctx={0};ctx.world=world;CHECK("linear-product-factory",reference_sources_ensure(&ctx));GeoAxisPosition value;
    if(!strcmp(argv[2],"datum-definition")){
        memcpy(before,world,sizeof *before);linear_product_fault=4;
        CHECK("linear-product-datum-definition-is-authoritative",reference_datum_position(&ctx,0,&value)&&value.coordinate==3);
    }else if(!strcmp(argv[2],"guide-definition")){
        memcpy(before,world,sizeof *before);linear_product_fault=5;
        CHECK("linear-product-guide-definition-is-authoritative",reference_guide_position(&ctx,1,&value)&&value.coordinate==3);
    }else if(!strcmp(argv[2],"datum")){
        CHECK("linear-product-datum-prime",reference_datum_position(&ctx,0,&value)&&value.coordinate==3);
        CHECK("linear-product-datum-decoy",geo_datums_evaluate(&world->geo.datum_planes,0,decoy_named,NULL).status==GEO_LINEAR_OK);
        memcpy(before,world,sizeof *before);linear_product_fault=1;
        CHECK("linear-product-datum-return-is-authoritative",reference_guide_position(&ctx,0,&value)&&value.coordinate==3&&value.context.axis==0);
    }else{
        CHECK("linear-product-guide-prime",reference_guide_position(&ctx,0,&value)&&value.coordinate==3);
        CHECK("linear-product-guide-decoy",cache_guide(world,0,99));memcpy(before,world,sizeof *before);
        linear_product_fault=!strcmp(argv[2],"guide-axis")?3:2;
        if(!strcmp(argv[2],"member")){
            CHECK("linear-product-member-guide-evaluation",reference_eval_guide(&ctx,0));
            AppMemberReferenceContext member={0};member.world=world;member.evaluation=&ctx;WoodMemberGuideFact fact;
            CHECK("linear-product-member-return-is-authoritative",app_member_reference_guide(&member,0,&fact)&&fact.offset==3&&fact.along_v&&fact.placement_id==1);
        }else if(!strcmp(argv[2],"guide")||!strcmp(argv[2],"guide-axis")){
            GuideLine guide={0};guide.id=2;guide.placement_id=1;guide.direction=GUIDE_ALONG_V;Coord coordinate=-99;
            CHECK("linear-product-guide-return-is-authoritative",reference_quantity_raw(&ctx,&guide,"guide:1",&coordinate)&&coordinate==3);
        }else return 2;
    }
    CHECK("linear-product-world-cache-decoy-unchanged",!memcmp(before,world,sizeof *world));
#ifndef GEO261_LINEAR_RETURN_CONTROL
    CHECK("linear-product-baseline-no-control-hits",linear_product_hits==0);
#endif
    reference_sources_dispose(&ctx);free(before);free(world);return 0;
}
