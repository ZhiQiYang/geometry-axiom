/* Includes the real model adapter; Python only renames its command main. */
#ifdef _WIN32
#undef _WIN32
#endif
#include "../geometry-core/kernel/source.h"
static GeoSourceStatus ledger_eval(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source ledger_eval
#include "../geometry-core/model_base.c"
#undef geo_eval_source
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static unsigned ledger_fault,ledger_hits;
static unsigned char ledger_content[GEO_REGION_KEY_LEDGER_CONTENT_MAX];
static GeoSourceStatus ledger_eval(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);
    if(status!=GEO_SOURCE_OK||ref.provider!=APP_SOURCE_REGION_KEYS)return status;
    GeoRegionKeySourceKind kind;uint32_t id,key,axis;
    if(!geo_region_key_source_decode(&ref,&kind,&id,&key,&axis)||kind!=GEO_REGION_KEY_SOURCE_LEDGER)return status;
    ++ledger_hits;GeoRegionKeys decoded;
    if(!geo_region_key_ledger_decode(out->as.definition.content,out->as.definition.content_size,&decoded))return GEO_SOURCE_INVALID;
    if(ledger_fault==1){uint32_t first=decoded.keys[0][0];decoded.keys[0][0]=decoded.keys[0][1];decoded.keys[0][1]=first;}
    if(ledger_fault==2)out->as.definition.schema="wrong/1";
    if(ledger_fault==3)out->as.definition.schema=NULL;
    if(ledger_fault==4)decoded.boundary_id++;
    if(ledger_fault==5)decoded.counts[0]--;
    size_t size=geo_region_key_ledger_encode(&decoded,ledger_content,sizeof ledger_content);if(!size)return GEO_SOURCE_INVALID;
    if(ledger_fault==6)--size;
    if(ledger_fault==7)memcpy(ledger_content+20,ledger_content+16,4);
    if(ledger_fault==8)return GEO_SOURCE_FAILED;
    out->as.definition.content=ledger_content;out->as.definition.content_size=size;return status;
}
static const char *ledger_components_scene;
static World *ledger_world(const char *name)
{
    World *world=calloc(1,sizeof *world);if(!world)return NULL;
    /* D4: only the derived (panel-fill/1) variant has a region-set range, and
     * R41 derives it; a stored component copy is not an admissible placement.
     * The driver's scene derives two components on keyed boundary 7. */
    if(!strcmp(name,"components")){if(!ledger_components_scene||!parse_scene_file(ledger_components_scene,world)){free(world);return NULL;}return world;}
    SpaceBoundarySurface boundary={.id=7,.outline={.v={{0,0},{1000,0},{1000,1000},{0,1000}},.count=4},.hole_count=1};
    boundary.holes[0]=(PolygonLoop2){.v={{100,100},{200,100},{200,200},{100,200}},.count=4};
    if(!app_boundary_stage(world,&boundary)){free(world);return NULL;}
    GeoPlacementDefinition placement={.id=9,.frame={{0,0,30},{1,0,0},{0,1,0},{0,0,1}},.domain=GEO_PLACEMENT_REGION_REF,.region_id=7};
    if(!strcmp(name,"rectangle")){placement.domain=GEO_PLACEMENT_RECT;placement.id=7;placement.rect=(GeoRect2){0,0,100,100};}
    if(!geo_placements_stage(&world->geo.placement_data,&placement)){free(world);return NULL;}
    if(!strcmp(name,"shared")){placement.id=10;if(!geo_placements_stage(&world->geo.placement_data,&placement)){free(world);return NULL;}}
    if(strcmp(name,"absent")){GeoRegionKeys keys={.boundary_id=7,.loop_count=2,.counts={4,4},.keys={{1,2,3,4},{5,6,7,8}},.next_key=9};
        if(!geo_region_keys_put(&world->geo.region_data,&keys)){free(world);return NULL;}}
    return world;
}
static bool ledger_edge(ModelSources *state,const ModelSourceItem *item,uint32_t expected_id)
{
    for(size_t i=0;i<geo_eval_edge_count(state->reference.sources);++i){GeoSourceEdge edge;GeoSourceNodeView consumer,source;
        if(!geo_eval_edge_at(state->reference.sources,i,&edge)||edge.kind!=GEO_DEPENDENCY_DEFINITION_REQUIRED||
            !geo_eval_node_at(state->reference.sources,edge.consumer,&consumer)||!geo_eval_node_at(state->reference.sources,edge.source,&source)||
            consumer.source.provider!=MODEL_SOURCE_PROVIDER||source.source.provider!=APP_SOURCE_REGION_KEYS||
            consumer.source.key_size!=strlen(item->key)||memcmp(consumer.source.key,item->key,consumer.source.key_size))continue;
        GeoRegionKeySourceKind kind;uint32_t id,key,axis;
        if(geo_region_key_source_decode(&source.source,&kind,&id,&key,&axis)&&kind==GEO_REGION_KEY_SOURCE_LEDGER&&id==expected_id)return true;
    }return false;
}
static int ledger_case(const char *name)
{
    World *world=ledger_world(name),*before=malloc(sizeof *before);CHECK("ledger-memory",world&&before);memcpy(before,world,sizeof *before);
    ModelSources state={0};if(!strcmp(name,"actual")||!strcmp(name,"shared"))ledger_fault=1;
    CHECK("ledger-build",model_sources_build(&state,world));size_t roots=0;
    for(size_t i=0;i<state.count;++i){ModelSourceItem *item=state.items[i];if(strcmp(item->slot,"placement.region"))continue;++roots;
        bool keyed=!strcmp(name,"actual")||!strcmp(name,"shared");
        if(keyed){const GeoRegionKeys *keys=item->vertex_keys[0];
            CHECK("ledger-actual-return-controls-attached-keys",keys&&keys==item->owned_vertex_keys&&keys!=geo_region_keys_find(&world->geo.region_data,7)&&keys->keys[0][0]==2&&keys->keys[0][1]==1&&keys->keys[1][0]==5);
            CHECK("ledger-root-has-definition-edge",ledger_edge(&state,item,7));
            memset(ledger_content,0,sizeof ledger_content);
            CHECK("ledger-root-owns-decoded-storage",keys->keys[0][0]==2&&keys->keys[1][3]==8);
        }else{GeoSourceValue geometry;CHECK("ledger-unkeyed-root-value",geo_eval_source(state.reference.sources,(GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)},GEO_DEPENDENCY_VALUE_REQUIRED,&geometry)==GEO_SOURCE_OK);
            CHECK("ledger-unkeyed-component-count",geometry.as.regions.count==(!strcmp(name,"components")?2:1));
            for(size_t c=0;c<geometry.as.regions.count;++c)CHECK("ledger-absence-and-domains-remain-null",!item->vertex_keys||c>=item->region_count||!item->vertex_keys[c]);CHECK("ledger-unkeyed-root-has-no-ledger-edge",!ledger_edge(&state,item,7));}
    }
    CHECK("ledger-root-count",roots==(!strcmp(name,"shared")?2:1));
    CHECK("ledger-world-unchanged",!memcmp(before,world,sizeof *world));
    if(!strcmp(name,"absent"))CHECK("ledger-read-does-not-initialize",geo_region_keys_count(&world->geo.region_data)==0&&ledger_hits==0);
    model_sources_free(&state);free(before);free(world);return 0;
}
static int ledger_malformed_case(void)
{
    for(unsigned fault=2;fault<=8;++fault){World *world=ledger_world("actual"),*before=malloc(sizeof *before);CHECK("ledger-malformed-memory",world&&before);memcpy(before,world,sizeof *before);
        ledger_fault=fault;ModelSources state={0};CHECK("ledger-malformed-return-rejects-root",!model_sources_build(&state,world));
        for(size_t i=0;i<state.count;++i){ModelSourceItem *item=state.items[i];if(strcmp(item->slot,"placement.region"))continue;
            GeoSourceValue value,saved;memset(&value,0x5a,sizeof value);memcpy(&saved,&value,sizeof saved);
            CHECK("ledger-malformed-output-is-atomic",!model_source_evaluate(&state,state.reference.sources,&(GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)},&value)&&!memcmp(&value,&saved,sizeof value)&&!item->owned_vertex_keys&&(!item->vertex_keys||!item->vertex_keys[0]));
        }
        CHECK("ledger-malformed-world-unchanged",!memcmp(before,world,sizeof *world));model_sources_free(&state);free(before);free(world);
    }return 0;
}
typedef struct {uint32_t id;unsigned char content[GEO_PLACEMENT_DEFINITION_MAX_BYTES];size_t size;} LedgerPlacementInput;
static bool ledger_placement_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{LedgerPlacementInput *input=opaque;if(ref->provider!=93||ref->key_size!=sizeof input->id||memcmp(ref->key,&input->id,sizeof input->id))return false;memset(out,0,sizeof *out);out->kind=GEO_SOURCE_DEFINITION;out->context.axis=-1;return true;}
static bool ledger_placement_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{(void)graph;LedgerPlacementInput *input=opaque;GeoSourceDescriptor descriptor;if(!ledger_placement_describe(opaque,ref,&descriptor))return false;out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){GEO_PLACEMENT_DEFINITION_SCHEMA,input->content,input->size};return true;}
static bool ledger_placement_binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{LedgerPlacementInput *input=opaque;if(id!=input->id||kind!=GEO_PLACEMENT_SOURCE_DEFINITION)return false;*out=(GeoSourceRef){93,&input->id,sizeof input->id};return true;}
static int ledger_selection_case(void)
{
    for(unsigned mode=0;mode<3;++mode){World *world=ledger_world(mode==0?"rectangle":"actual"),*before=malloc(sizeof *before);LedgerPlacementInput *input=calloc(1,sizeof *input);
        CHECK("ledger-selection-memory",world&&before&&input);input->id=mode==0?7:9;GeoPlacementDefinition actual=*geo_placements_find(&world->geo.placement_data,input->id);
        actual.domain=mode==1?GEO_PLACEMENT_RECT:GEO_PLACEMENT_REGION_REF;actual.rect=(GeoRect2){0,0,100,100};actual.region_id=mode==2?8:7;
        if(mode==2){GeoRegionDefinition other=*geo_regions_find(&world->geo.region_data,7);other.id=8;GeoRegionKeys keys=*geo_region_keys_find(&world->geo.region_data,7);keys.boundary_id=8;keys.next_key+=10;
            for(size_t l=0;l<keys.loop_count;++l)for(size_t v=0;v<keys.counts[l];++v)keys.keys[l][v]+=10;
            CHECK("ledger-selection-other-region",geo_regions_stage(&world->geo.region_data,&other)&&geo_region_keys_put(&world->geo.region_data,&keys));}
        input->size=geo_placement_definition_encode(&actual,input->content,sizeof input->content);CHECK("ledger-selection-definition",input->size);memcpy(before,world,sizeof *before);
        ModelSources state={0};state.reference.world=world;state.reference.sources=geo_eval_create(8192,0);CHECK("ledger-selection-graph",state.reference.sources);
        GeoSourceProvider provider={93,"test.placement-definition","ledger-selection/1",input,ledger_placement_describe,ledger_placement_evaluate};
        CHECK("ledger-selection-input",geo_eval_register(state.reference.sources,&provider));
        state.reference.placement_sources=geo_placement_sources_register(state.reference.sources,&world->geo.placement_data,&world->geo.region_data,APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,ledger_placement_binding,input);
        state.reference.region_key_sources=geo_region_key_sources_register(state.reference.sources,&world->geo.region_data,APP_SOURCE_REGION_KEYS,APP_SOURCE_REGION);
        CHECK("ledger-selection-providers",state.reference.placement_sources&&state.reference.region_key_sources);state.reference.sources_registered=true;
        GeoSourceProvider root={MODEL_SOURCE_PROVIDER,"app.model-snapshot","ledger-selection/1",&state,model_source_describe,model_source_evaluate};CHECK("ledger-selection-root",geo_eval_register(state.reference.sources,&root));
        ModelSourceItem *item=model_sources_add(&state,"placement",input->id,"placement.region",0,false,GEO_SOURCE_REGION_SET);CHECK("ledger-selection-item",item&&model_source_regions(item,0));GeoSourceValue value;
        CHECK("ledger-selection-actual-definition-controls-attachment",geo_eval_source(state.reference.sources,(GeoSourceRef){MODEL_SOURCE_PROVIDER,item->key,strlen(item->key)},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
            (mode==1?!item->vertex_keys:item->vertex_keys&&item->vertex_keys[0]&&item->vertex_keys[0]->keys[0][0]==(mode==2?11:1)));
        CHECK("ledger-selection-actual-region-identity-edge",mode==1?!ledger_edge(&state,item,7):ledger_edge(&state,item,actual.region_id));
        CHECK("ledger-selection-authored-world-unchanged",!memcmp(before,world,sizeof *world));model_sources_free(&state);free(input);free(before);free(world);
    }return 0;
}
int main(int argc,char **argv)
{if(argc==3&&!strcmp(argv[1],"components"))ledger_components_scene=argv[2];else if(argc!=2)return 2;return !strcmp(argv[1],"malformed")?ledger_malformed_case():!strcmp(argv[1],"selection")?ledger_selection_case():ledger_case(argv[1]);}
