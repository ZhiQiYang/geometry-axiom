/* Actual H host admission consumes a bound canonical K placement definition. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
enum {HOST_INPUT=91,HOST_CONSUMER=92};
typedef struct {
    World world,before;ReferenceEval context;GeoPlacementDefinition actual;
    unsigned char content[GEO_PLACEMENT_DEFINITION_MAX_BYTES];size_t size;
    uint32_t id;unsigned calls,bindings,fault;
} HostDefinitionFixture;
static bool host_definition_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    HostDefinitionFixture *f=opaque;if(ref->key_size!=sizeof f->id||memcmp(ref->key,&f->id,sizeof f->id))return false;
    memset(out,0,sizeof *out);out->context.axis=-1;out->kind=ref->provider==HOST_INPUT?GEO_SOURCE_DEFINITION:GEO_SOURCE_QUANTITY;return true;
}
static bool host_definition_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostDefinitionFixture *f=opaque;if(graph!=f->context.sources)return false;
    if(ref->provider==HOST_INPUT){++f->calls;if(f->fault==4)return false;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){f->fault==1?"wrong/1":GEO_PLACEMENT_DEFINITION_SCHEMA,f->content,f->fault==3?f->size-1:f->size};return true;}
    bool derived=false;if(!reference_eng_placement(&f->context,f->id,&derived))return false;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){derived?1:0,1,GEO_UNIT_SCALAR};return true;
}
static bool host_definition_binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{
    HostDefinitionFixture *f=opaque;++f->bindings;if(id!=f->id||kind!=GEO_PLACEMENT_SOURCE_DEFINITION)return false;
    *out=(GeoSourceRef){HOST_INPUT,&f->id,sizeof f->id};return true;
}
static HostDefinitionFixture *host_definition_fixture(bool raw_derived,unsigned fault)
{
    HostDefinitionFixture *f=calloc(1,sizeof *f);if(!f)return NULL;f->id=7;f->fault=fault;
    PlacementSurface placement={.id=7,.frame={{0,0,30},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,100,100},.derived_fill_id=raw_derived?55:0};
    if(!app_placement_stage(&f->world,&placement))return NULL;
    f->actual=*geo_placements_find(&f->world.geo.placement_data,7);f->actual.domain=raw_derived?GEO_PLACEMENT_RECT:GEO_PLACEMENT_REGION_SET;
    f->actual.rect=(GeoRect2){0,0,100,100};if(fault==2)f->actual.id=8;
    f->size=geo_placement_definition_encode(&f->actual,f->content,sizeof f->content);if(!f->size)return NULL;
    memcpy(&f->before,&f->world,sizeof f->before);f->context.world=&f->world;f->context.sources=geo_eval_create(8191,0);if(!f->context.sources)return NULL;
    GeoSourceProvider input={HOST_INPUT,"test.host-definition","host-definition/1",f,host_definition_describe,host_definition_evaluate};
    GeoSourceProvider consumer={HOST_CONSUMER,"test.host-consumer","host-definition/1",f,host_definition_describe,host_definition_evaluate};
    if(!geo_eval_register(f->context.sources,&input))return NULL;
    f->context.placement_sources=geo_placement_sources_register(f->context.sources,&f->world.geo.placement_data,&f->world.geo.region_data,
        APP_SOURCE_PLACEMENT,APP_SOURCE_REGION,host_definition_binding,f);
    if(!f->context.placement_sources||!geo_eval_register(f->context.sources,&consumer))return NULL;
    f->context.sources_registered=true;return f;
}
static void host_definition_dispose(HostDefinitionFixture *f)
{reference_sources_dispose(&f->context);free(f);}
static bool host_definition_edge(GeoEvalContext *graph)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;GeoSourceNodeView a,b;GeoPlacementSourceKind kind;uint32_t id;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED&&geo_eval_node_at(graph,edge.consumer,&a)&&geo_eval_node_at(graph,edge.source,&b)&&
            a.source.provider==HOST_CONSUMER&&b.source.provider==APP_SOURCE_PLACEMENT&&geo_placement_source_decode(&b.source,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_DEFINITION&&id==7)return true;
    }return false;
}
static int host_definition_actual(void)
{
    for(unsigned raw=0;raw<2;++raw){HostDefinitionFixture *f=host_definition_fixture(raw!=0,0);CHECK("host-placement-fixture",f);GeoSourceValue value;
        CHECK("host-placement-actual-definition-controls-derived",geo_eval_source(f->context.sources,(GeoSourceRef){HOST_CONSUMER,&f->id,sizeof f->id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.quantity.num==!raw);
        CHECK("host-placement-definition-edge-no-geometry",host_definition_edge(f->context.sources)&&geo_eval_node_count(f->context.sources)==3&&f->calls==1&&f->bindings==1);
        CHECK("host-placement-null-output-keeps-definition-gate",reference_eng_placement(&f->context,7,NULL)&&f->calls==1&&f->bindings==1);
        memset(f->content,0,sizeof f->content);
        CHECK("host-placement-authored-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));host_definition_dispose(f);
    }return 0;
}
static int host_definition_gates(void)
{
    HostDefinitionFixture *f=host_definition_fixture(false,0);CHECK("host-placement-gates-fixture",f);bool derived=true;
    CHECK("host-placement-missing-before-source",!reference_eng_placement(&f->context,8,&derived)&&!derived&&geo_eval_node_count(f->context.sources)==0&&f->calls==0);
    f->context.use_current_values=true;derived=true;
    CHECK("host-placement-snapshot-direct",reference_eng_placement(&f->context,7,&derived)&&!derived&&geo_eval_node_count(f->context.sources)==0&&f->calls==0);
    CHECK("host-placement-gates-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));host_definition_dispose(f);return 0;
}
static int host_definition_malformed(void)
{
    for(unsigned fault=1;fault<=4;++fault){HostDefinitionFixture *f=host_definition_fixture(false,fault);CHECK("host-placement-malformed-fixture",f);bool derived=true;
        CHECK("host-placement-malformed-definition-rejects-atomically",!reference_eng_placement(&f->context,7,&derived)&&derived&&f->calls==1&&f->bindings==1&&!memcmp(&f->world,&f->before,sizeof f->world));
        host_definition_dispose(f);
    }return 0;
}
static int host_definition_derived(void)
{
    World *world=calloc(1,sizeof *world);CHECK("host-placement-derived-memory",world);
    PlacementSurface placement={.id=7,.frame={{0,0,30},{1,0,0},{0,1,0},{0,0,1}},.derived_fill_id=55};
    CHECK("host-placement-derived-stage",app_placement_stage(world,&placement));ReferenceEval context={0};context.world=world;bool derived=false;
    CHECK("host-placement-definition-avoids-derived-geometry",reference_eng_placement(&context,7,&derived)&&derived&&geo_eval_node_count(context.sources)==1&&geo_eval_edge_count(context.sources)==0);
    GeoSourceNodeView node;GeoPlacementSourceKind kind;uint32_t id;
    CHECK("host-placement-only-definition-evaluated",geo_eval_node_at(context.sources,0,&node)&&node.source.provider==APP_SOURCE_PLACEMENT&&geo_placement_source_decode(&node.source,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_DEFINITION&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION);
    reference_sources_dispose(&context);free(world);return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;return !strcmp(argv[1],"actual")?host_definition_actual():!strcmp(argv[1],"gates")?host_definition_gates():!strcmp(argv[1],"malformed")?host_definition_malformed():!strcmp(argv[1],"derived")?host_definition_derived():2;}
