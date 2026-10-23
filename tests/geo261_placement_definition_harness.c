/* Public K-only witness. Independent BE wire vectors are the oracle; no
 * production encoder creates decoder input or replacement-provider content. */
#include "placement_sources.h"
#include <stdio.h>
#include <string.h>

#define CHECK(test,label) do{if(!(test)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
#define TEST_ID UINT32_C(0x01020304)
typedef struct {unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES+1];size_t size;} Vector;
static void u32(Vector *v,uint32_t n)
{for(unsigned i=0;i<4;++i)v->bytes[v->size++]=(unsigned char)(n>>(8*(3-i)));}
static void i64(Vector *v,int64_t n)
{uint64_t bits=(uint64_t)n;for(unsigned i=0;i<8;++i)v->bytes[v->size++]=(unsigned char)(bits>>(8*(7-i)));}
static void fixed_vector(Vector *v,int domain)
{
    memset(v,0,sizeof *v);u32(v,TEST_ID);
    i64(v,INT64_MIN);i64(v,INT64_MAX);i64(v,-3);
    i64(v,4);i64(v,-5);i64(v,6);i64(v,-7);i64(v,8);i64(v,-9);i64(v,10);i64(v,-11);i64(v,12);
    v->bytes[v->size++]=(unsigned char)domain;
    if(domain==GEO_PLACEMENT_RECT){i64(v,INT64_MAX);i64(v,-21);i64(v,INT64_MIN);i64(v,22);}
    else if(domain==GEO_PLACEMENT_REGION_REF)u32(v,UINT32_MAX);
    else{u32(v,2);u32(v,UINT32_MAX);u32(v,2);i64(v,-41);i64(v,42);i64(v,43);i64(v,-44);
        u32(v,2);u32(v,1);i64(v,INT64_MIN);i64(v,INT64_MAX);u32(v,0);
        u32(v,0);u32(v,0);u32(v,0);}
}
static void expected(GeoPlacementDefinition *p,int domain)
{
    memset(p,0,sizeof *p);p->id=TEST_ID;p->domain=(GeoPlacementDomain)domain;
    p->frame=(GeoFrame){{INT64_MIN,INT64_MAX,-3},{4,-5,6},{-7,8,-9},{10,-11,12}};
    if(domain==GEO_PLACEMENT_RECT)p->rect=(GeoRect2){INT64_MAX,-21,INT64_MIN,22};
    else if(domain==GEO_PLACEMENT_REGION_REF)p->region_id=UINT32_MAX;
    else{p->component_count=2;p->components[0].id=UINT32_MAX;p->components[0].outline.count=2;
        p->components[0].outline.v[0]=(GeoPoint2){-41,42};p->components[0].outline.v[1]=(GeoPoint2){43,-44};
        p->components[0].hole_count=2;p->components[0].holes[0].count=1;
        p->components[0].holes[0].v[0]=(GeoPoint2){INT64_MIN,INT64_MAX};}
}
static void maximal(Vector *v,GeoPlacementDefinition *p)
{
    fixed_vector(v,GEO_PLACEMENT_REGION_SET);expected(p,GEO_PLACEMENT_REGION_SET);
    v->size=101;u32(v,GEO_PLACEMENT_COMPONENT_CAPACITY);p->component_count=GEO_PLACEMENT_COMPONENT_CAPACITY;
    for(size_t c=0;c<GEO_PLACEMENT_COMPONENT_CAPACITY;++c){GeoRegionDefinition *r=&p->components[c];memset(r,0,sizeof *r);
        r->id=(uint32_t)(100*c+7);r->outline.count=GEO_LOOP_MAX_VERTICES;r->hole_count=GEO_REGION_MAX_HOLES;
        u32(v,(uint32_t)(100*c+7));u32(v,GEO_LOOP_MAX_VERTICES);
        for(size_t n=0;n<GEO_LOOP_MAX_VERTICES;++n){i64(v,(int64_t)(1000*c+n));i64(v,-(int64_t)(2000*c+n));
            r->outline.v[n]=(GeoPoint2){(int64_t)(1000*c+n),-(int64_t)(2000*c+n)};}
        u32(v,GEO_REGION_MAX_HOLES);
        for(size_t h=0;h<GEO_REGION_MAX_HOLES;++h){u32(v,GEO_LOOP_MAX_VERTICES);r->holes[h].count=GEO_LOOP_MAX_VERTICES;
            for(size_t n=0;n<GEO_LOOP_MAX_VERTICES;++n){i64(v,-(int64_t)(10000*c+100*h+n));i64(v,(int64_t)(20000*c+200*h+n));
                r->holes[h].v[n]=(GeoPoint2){-(int64_t)(10000*c+100*h+n),(int64_t)(20000*c+200*h+n)};}}
    }
}
static bool rejects(const void *bytes,size_t size)
{
    GeoPlacementDefinition out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof before);
    return !geo_placement_definition_decode(bytes,size,&out)&&!memcmp(&out,&before,sizeof out);
}
static bool encode_rejects(const GeoPlacementDefinition *p,size_t capacity)
{
    unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES],before[sizeof bytes];memset(bytes,0xa5,sizeof bytes);memcpy(before,bytes,sizeof bytes);
    return !geo_placement_definition_encode(p,bytes,capacity)&&!memcmp(bytes,before,sizeof bytes);
}
static int keys_case(void)
{
    GeoPlacementSourceKey key;GeoPlacementSourceKind kind=(GeoPlacementSourceKind)99;uint32_t id=55;
    const unsigned char want[]={3,1,2,3,4};GeoSourceRef ref=geo_placement_source_ref(7,GEO_PLACEMENT_SOURCE_DEFINITION,TEST_ID,&key);
    CHECK(ref.provider==7&&ref.key==key.bytes&&ref.key_size==5&&!memcmp(key.bytes,want,5),"definition-key-fixed-big-endian");
    CHECK(geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_DEFINITION&&id==TEST_ID,"definition-key-decodes-kind-three");
    for(unsigned k=1;k<=2;++k){ref=geo_placement_source_ref(7,(GeoPlacementSourceKind)k,TEST_ID,&key);
        CHECK(key.bytes[0]==k&&!memcmp(key.bytes+1,want+1,4)&&geo_placement_source_decode(&ref,&kind,&id)&&kind==(GeoPlacementSourceKind)k,"legacy-key-bytes-unchanged");}
    for(unsigned k=0;k<256;++k)if(k<1||k>3){key.bytes[0]=(unsigned char)k;kind=(GeoPlacementSourceKind)99;id=55;
        CHECK(!geo_placement_source_decode(&ref,&kind,&id)&&kind==(GeoPlacementSourceKind)99&&id==55,"invalid-key-tag-is-atomic");}
    key.bytes[0]=3;ref.key_size=4;CHECK(!geo_placement_source_decode(&ref,&kind,&id)&&kind==(GeoPlacementSourceKind)99&&id==55,"invalid-key-size-is-atomic");
    return 0;
}
static int codec_case(void)
{
    Vector v;GeoPlacementDefinition p,out;unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES];
    const char *labels[]={"rect-exact-canonical-wire","reference-exact-canonical-wire","ordered-components-exact-canonical-wire"};
    for(int domain=0;domain<=2;++domain){fixed_vector(&v,domain);expected(&p,domain);
        CHECK(geo_placement_definition_encode(&p,bytes,sizeof bytes)==v.size&&!memcmp(bytes,v.bytes,v.size),labels[domain]);
        memset(&out,0xa5,sizeof out);CHECK(geo_placement_definition_decode(v.bytes,v.size,&out)&&!memcmp(&out,&p,sizeof p),"independent-vector-decodes-all-active-fields");
        if(domain!=GEO_PLACEMENT_REGION_SET){p.component_count=SIZE_MAX;memset(p.components,0x97,sizeof p.components);}
        if(domain!=GEO_PLACEMENT_REGION_REF)p.region_id=12345;
        if(domain!=GEO_PLACEMENT_RECT)memset(&p.rect,0x98,sizeof p.rect);
        CHECK(geo_placement_definition_encode(&p,bytes,sizeof bytes)==v.size&&!memcmp(bytes,v.bytes,v.size),"inactive-fields-do-not-enter-wire");
    }
    expected(&p,GEO_PLACEMENT_REGION_SET);fixed_vector(&v,GEO_PLACEMENT_REGION_SET);p.component_count=0;v.size=101;u32(&v,0);
    CHECK(geo_placement_definition_encode(&p,bytes,sizeof bytes)==105&&!memcmp(bytes,v.bytes,105)&&geo_placement_definition_decode(v.bytes,v.size,&out)&&out.component_count==0,"empty-region-set-remains-representable");
    return 0;
}
static int bounds_case(void)
{
    Vector v;GeoPlacementDefinition p,out;unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES];maximal(&v,&p);
    CHECK(v.size==GEO_PLACEMENT_DEFINITION_MAX_BYTES,"wire-capacity-is-exact");
    CHECK(geo_placement_definition_encode(&p,bytes,sizeof bytes)==v.size&&!memcmp(bytes,v.bytes,v.size),"maximal-definition-encodes-exactly");
    CHECK(geo_placement_definition_decode(v.bytes,v.size,&out)&&!memcmp(&out,&p,sizeof p),"maximal-definition-decodes-exactly");
    CHECK(encode_rejects(&p,v.size-1),"short-encode-capacity-is-atomic");
    p.component_count=GEO_PLACEMENT_COMPONENT_CAPACITY+1;CHECK(encode_rejects(&p,sizeof bytes),"oversized-component-encode-is-atomic");
    p.component_count=GEO_PLACEMENT_COMPONENT_CAPACITY;p.components[0].hole_count=GEO_REGION_MAX_HOLES+1;CHECK(encode_rejects(&p,sizeof bytes),"oversized-hole-encode-is-atomic");
    p.components[0].hole_count=GEO_REGION_MAX_HOLES;p.components[0].outline.count=GEO_LOOP_MAX_VERTICES+1;CHECK(encode_rejects(&p,sizeof bytes),"oversized-outline-encode-is-atomic");
    p.components[0].outline.count=GEO_LOOP_MAX_VERTICES;p.components[0].holes[0].count=GEO_LOOP_MAX_VERTICES+1;CHECK(encode_rejects(&p,sizeof bytes),"oversized-hole-loop-encode-is-atomic");
    return 0;
}
static int malformed_case(void)
{
    Vector v;GeoPlacementDefinition p;
    for(int domain=0;domain<=2;++domain){fixed_vector(&v,domain);
        for(size_t n=0;n<v.size;++n)CHECK(rejects(v.bytes,n),"truncated-definition-output-is-atomic");
        v.bytes[v.size]=0;CHECK(rejects(v.bytes,v.size+1),"trailing-definition-output-is-atomic");}
    fixed_vector(&v,GEO_PLACEMENT_REGION_SET);v.bytes[100]=255;CHECK(rejects(v.bytes,v.size),"unknown-domain-output-is-atomic");
    fixed_vector(&v,GEO_PLACEMENT_REGION_SET);v.bytes[104]=GEO_PLACEMENT_COMPONENT_CAPACITY+1;CHECK(rejects(v.bytes,v.size),"oversized-component-decode-is-atomic");
    fixed_vector(&v,GEO_PLACEMENT_REGION_SET);v.bytes[112]=GEO_LOOP_MAX_VERTICES+1;CHECK(rejects(v.bytes,v.size),"oversized-outline-decode-is-atomic");
    fixed_vector(&v,GEO_PLACEMENT_REGION_SET);v.bytes[148]=GEO_REGION_MAX_HOLES+1;CHECK(rejects(v.bytes,v.size),"oversized-hole-decode-is-atomic");
    fixed_vector(&v,GEO_PLACEMENT_REGION_SET);v.bytes[152]=GEO_LOOP_MAX_VERTICES+1;CHECK(rejects(v.bytes,v.size),"oversized-hole-loop-decode-is-atomic");
    CHECK(rejects(v.bytes,GEO_PLACEMENT_DEFINITION_MAX_BYTES+1)&&rejects(NULL,0),"invalid-content-size-or-pointer-is-atomic");
    expected(&p,GEO_PLACEMENT_RECT);p.domain=(GeoPlacementDomain)-1;CHECK(encode_rejects(&p,GEO_PLACEMENT_DEFINITION_MAX_BYTES),"unknown-encode-domain-is-atomic");
    CHECK(encode_rejects(NULL,0)&&!geo_placement_definition_encode(&p,NULL,0)&&!geo_placement_definition_decode(v.bytes,v.size,NULL),"null-codec-arguments-rejected");
    return 0;
}
typedef struct {
    Vector wire;GeoSourceValueKind kind;const char *schema;int calls,frame_calls,region_calls;unsigned char key;
    bool bind_geometry,fail_geometry,null_content;GeoPoint2 bound_points[2];GeoRegionView bound_region;
} Replacement;
static bool replacement_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    Replacement *s=opaque;if(ref->provider!=33||ref->key_size!=1||!ref->key||*(const unsigned char *)ref->key!=9)return false;
    memset(out,0,sizeof *out);out->kind=s->kind;out->unit=GEO_UNIT_SCALAR;out->context.axis=-1;return true;
}
static bool replacement_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Replacement *s=opaque;(void)graph;(void)ref;++s->calls;memset(out,0,sizeof *out);out->kind=s->kind;
    if(s->fail_geometry)return false;
    if(s->kind==GEO_SOURCE_DEFINITION)out->as.definition=(GeoDefinitionValue){s->schema,s->null_content?NULL:s->wire.bytes,s->wire.size};
    else if(s->kind==GEO_SOURCE_FRAME)out->as.frame=(GeoFrame){{91,92,93},{1,0,0},{0,1,0},{0,0,1}};
    else if(s->kind==GEO_SOURCE_REGION_SET){s->bound_points[0]=(GeoPoint2){81,82};s->bound_points[1]=(GeoPoint2){83,84};
        s->bound_region=(GeoRegionView){{s->bound_points,2},NULL,0};out->as.regions=(GeoRegionSetView){&s->bound_region,1};}
    return true;
}
static bool binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{
    Replacement *s=opaque;if(kind==GEO_PLACEMENT_SOURCE_FRAME)++s->frame_calls;if(kind==GEO_PLACEMENT_SOURCE_REGIONS)++s->region_calls;
    if(id!=TEST_ID)return false;
    if(kind!=GEO_PLACEMENT_SOURCE_DEFINITION&&!(s->bind_geometry&&
        ((kind==GEO_PLACEMENT_SOURCE_FRAME&&s->kind==GEO_SOURCE_FRAME)||(kind==GEO_PLACEMENT_SOURCE_REGIONS&&s->kind==GEO_SOURCE_REGION_SET))))return false;
    s->key=9;*out=(GeoSourceRef){33,&s->key,1};return true;
}
typedef struct {GeoEvalContext *graph;GeoPlacementSources *sources;GeoPlacementStore *placements;GeoRegionStore *regions;} Fixture;
static bool attach(Fixture *f,Replacement *replacement)
{
    if(replacement){GeoSourceProvider provider={33,"test.replacement","test/1",replacement,replacement_describe,replacement_evaluate};if(!geo_eval_register(f->graph,&provider))return false;}
    f->sources=geo_placement_sources_register(f->graph,f->placements,f->regions,11,22,replacement?binding:NULL,replacement);
    return f->sources!=NULL;
}
static bool fixture(Fixture *f,Replacement *replacement)
{
    memset(f,0,sizeof *f);f->graph=geo_eval_create(71,13);f->placements=geo_placements_create();f->regions=geo_regions_create();
    if(!f->graph||!f->placements||!f->regions)return false;
    GeoPlacementDefinition raw;expected(&raw,GEO_PLACEMENT_RECT);if(!geo_placements_stage(f->placements,&raw))return false;
    return attach(f,replacement);
}
/* K's geo_eval_reset drops every provider registration (source.c clear):
 * destroy this generation's handle and register the same candidate anew. */
static bool reset(Fixture *f,Replacement *replacement)
{
    if(!geo_eval_reset(f->graph))return false;
    geo_placement_sources_destroy(f->sources);f->sources=NULL;return attach(f,replacement);
}
static void destroy(Fixture *f,bool graph_first)
{
    if(graph_first)geo_eval_destroy(f->graph);geo_placement_sources_destroy(f->sources);
    if(!graph_first)geo_eval_destroy(f->graph);geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);
}
static bool definitions_only(GeoEvalContext *graph)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;if(!geo_eval_node_at(graph,i,&n))return false;
        if(n.descriptor.kind!=GEO_SOURCE_DEFINITION)return false;
        if(n.source.provider==11){GeoPlacementSourceKind kind;uint32_t id;if(!geo_placement_source_decode(&n.source,&kind,&id)||kind!=GEO_PLACEMENT_SOURCE_DEFINITION)return false;}}
    return true;
}
static int definition_case(void)
{
    Fixture f;CHECK(fixture(&f,NULL),"definition-fixture-created");GeoPlacementSourceKey key;GeoSourceDescriptor description;GeoPlacementDefinition out,want;GeoSourceValue value;
    GeoSourceRef ref=geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_DEFINITION,TEST_ID,&key);
    CHECK(geo_eval_node_count(f.graph)==0,"registration-does-not-evaluate");
    CHECK(geo_eval_describe(f.graph,ref,&description)==GEO_SOURCE_OK&&description.kind==GEO_SOURCE_DEFINITION&&description.unit==GEO_UNIT_SCALAR&&description.context.axis==-1,"definition-description-is-scalar-axisless");
    GeoSourceNodeView node;CHECK(geo_eval_node_at(f.graph,0,&node)&&node.state==GEO_NODE_NEW,"description-does-not-evaluate");
    expected(&want,GEO_PLACEMENT_RECT);
    CHECK(geo_placement_sources_definition(f.sources,TEST_ID,&out)&&!memcmp(&out,&want,sizeof out)&&definitions_only(f.graph),"definition-only-reads-staged-invalid-geometry");
    CHECK(geo_eval_source(f.graph,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)==GEO_SOURCE_OK&&!strcmp(value.as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA),"definition-source-is-schema-tagged");
    Vector wire;fixed_vector(&wire,GEO_PLACEMENT_RECT);CHECK(value.as.definition.content_size==wire.size&&!memcmp(value.as.definition.content,wire.bytes,wire.size),"source-emits-full-canonical-definition");
    const void *stable=value.as.definition.content;out.rect.min_u=17;GeoPlacementDefinition again;
    CHECK(geo_placement_sources_definition(f.sources,TEST_ID,&again)&&again.rect.min_u==INT64_MAX,"returned-definition-has-owned-fields");
    for(uint32_t id=1;id<=3;++id){expected(&want,(int)(id-1));want.id=id;CHECK(geo_placements_stage(f.placements,&want),"other-definition-staged");
        CHECK(geo_placement_sources_definition(f.sources,id,&out),"other-definition-readable");}
    CHECK(!memcmp(stable,wire.bytes,wire.size),"candidate-owned-bytes-survive-other-reads");
    CHECK(geo_eval_seal(f.graph)&&geo_placement_sources_definition(f.sources,TEST_ID,&out)&&!geo_placement_sources_definition(f.sources,900,&out),"sealed-definition-read-is-memoized");
    destroy(&f,true);return 0;
}
static int typed_case(void)
{
    Replacement s;memset(&s,0,sizeof s);s.kind=GEO_SOURCE_DEFINITION;s.schema=GEO_PLACEMENT_DEFINITION_SCHEMA;fixed_vector(&s.wire,GEO_PLACEMENT_REGION_SET);
    Fixture f;CHECK(fixture(&f,&s),"typed-fixture-created");GeoPlacementDefinition out,want;expected(&want,GEO_PLACEMENT_REGION_SET);
    CHECK(geo_placement_sources_definition(f.sources,TEST_ID,&out)&&!memcmp(&out,&want,sizeof out),"returned-definition-overrides-raw-placement");
    CHECK(s.calls==1&&!s.frame_calls&&!s.region_calls&&definitions_only(f.graph),"read-never-requests-frame-or-regions");
    CHECK(geo_eval_edge_count(f.graph)==1,"replacement-has-one-source-edge");GeoSourceEdge edge;
    CHECK(geo_eval_edge_at(f.graph,0,&edge)&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED,"replacement-edge-requires-definition");
    CHECK(geo_placements_find(f.placements,TEST_ID)->domain==GEO_PLACEMENT_RECT,"replacement-does-not-mutate-authored-store");
    CHECK(geo_placement_sources_definition(f.sources,TEST_ID,&out)&&s.calls==1,"replacement-value-is-memoized");
    destroy(&f,false);return 0;
}
static bool accessor_rejects(Fixture *f,uint32_t id)
{
    GeoPlacementDefinition out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);
    return !geo_placement_sources_definition(f->sources,id,&out)&&!memcmp(&out,&before,sizeof out);
}
static int typed_invalid_case(void)
{
    Replacement s;memset(&s,0,sizeof s);s.kind=GEO_SOURCE_DEFINITION;s.schema=GEO_PLACEMENT_DEFINITION_SCHEMA;fixed_vector(&s.wire,GEO_PLACEMENT_REGION_SET);
    Fixture f;CHECK(fixture(&f,&s),"invalid-typed-fixture-created");s.wire.bytes[3]=5;
    CHECK(accessor_rejects(&f,TEST_ID),"replacement-id-mismatch-is-atomic");
    CHECK(reset(&f,&s),"invalid-id-reset");fixed_vector(&s.wire,GEO_PLACEMENT_REGION_SET);s.schema="other.schema/1";
    CHECK(accessor_rejects(&f,TEST_ID),"replacement-schema-mismatch-is-atomic");
    CHECK(reset(&f,&s),"invalid-schema-reset");s.schema=GEO_PLACEMENT_DEFINITION_SCHEMA;--s.wire.size;
    CHECK(accessor_rejects(&f,TEST_ID),"replacement-malformed-wire-is-atomic");
    CHECK(reset(&f,&s),"invalid-wire-reset");fixed_vector(&s.wire,GEO_PLACEMENT_REGION_SET);s.kind=GEO_SOURCE_FRAME;
    CHECK(accessor_rejects(&f,TEST_ID),"replacement-wrong-value-kind-is-atomic");
    CHECK(accessor_rejects(&f,999),"missing-definition-is-atomic");
    CHECK(!s.frame_calls&&!s.region_calls,"failed-definition-reads-never-request-geometry");destroy(&f,true);return 0;
}
static int lifecycle_case(void)
{
    Fixture a,b;CHECK(fixture(&a,NULL)&&fixture(&b,NULL),"isolated-candidates-created");GeoPlacementDefinition out,raw;expected(&raw,GEO_PLACEMENT_REGION_REF);
    CHECK(geo_placements_stage(b.placements,&raw)&&geo_placement_sources_definition(a.sources,TEST_ID,&out)&&out.domain==GEO_PLACEMENT_RECT&&
        geo_placement_sources_definition(b.sources,TEST_ID,&out)&&out.domain==GEO_PLACEMENT_REGION_REF,"candidate-definition-storage-is-isolated");
    CHECK(reset(&a,NULL)&&geo_placements_stage(a.placements,&raw)&&geo_placement_sources_definition(a.sources,TEST_ID,&out)&&out.domain==GEO_PLACEMENT_REGION_REF,"reset-reencodes-candidate-definition");
    /* Definition addition must not change the established FRAME/REGIONS keys. */
    raw.frame=(GeoFrame){{1,2,3},{1,0,0},{0,1,0},{0,0,1}};raw.domain=GEO_PLACEMENT_RECT;raw.rect=(GeoRect2){0,0,100,200};raw.id=99;
    CHECK(geo_placements_stage(a.placements,&raw),"legacy-domains-staged");GeoPlacementSourceKey key;GeoSourceValue value;
    CHECK(geo_eval_source(a.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_FRAME,99,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_FRAME&&!memcmp(&value.as.frame,&raw.frame,sizeof raw.frame),"legacy-frame-value-unchanged");
    CHECK(geo_eval_source(a.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,99,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_REGION_SET&&value.as.regions.count==1&&value.as.regions.regions[0].outline.count==4,"legacy-regions-value-unchanged");
    destroy(&a,false);destroy(&b,true);return 0;
}
static void replace_origin(Vector *v)
{
    size_t size=v->size;v->size=4;i64(v,301);i64(v,-302);i64(v,303);v->size=size;
}
static bool geometry_has_definition_edge(GeoEvalContext *graph,GeoPlacementSourceKind kind)
{
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;GeoSourceNodeView consumer,source;GeoPlacementSourceKind a,b;uint32_t x,y;
        if(!geo_eval_edge_at(graph,i,&edge)||!geo_eval_node_at(graph,edge.consumer,&consumer)||!geo_eval_node_at(graph,edge.source,&source))return false;
        if(consumer.source.provider==11&&source.source.provider==11&&geo_placement_source_decode(&consumer.source,&a,&x)&&geo_placement_source_decode(&source.source,&b,&y)&&
           a==kind&&b==GEO_PLACEMENT_SOURCE_DEFINITION&&x==TEST_ID&&y==TEST_ID&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED)return true;
    }return false;
}
static int local_geometry_case(void)
{
    Replacement s;memset(&s,0,sizeof s);s.kind=GEO_SOURCE_DEFINITION;s.schema=GEO_PLACEMENT_DEFINITION_SCHEMA;fixed_vector(&s.wire,GEO_PLACEMENT_RECT);replace_origin(&s.wire);
    /* The independently supplied rectangle differs from the owned raw RECT. */
    s.wire.size=101;i64(&s.wire,-51);i64(&s.wire,-52);i64(&s.wire,53);i64(&s.wire,54);
    Fixture f;CHECK(fixture(&f,&s),"local-geometry-fixture-created");GeoPlacementSourceKey key;GeoSourceValue frame,regions;
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_FRAME,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&frame)==GEO_SOURCE_OK&&
        frame.as.frame.origin.x==301&&frame.as.frame.origin.y==-302&&frame.as.frame.origin.z==303,"local-frame-uses-actual-definition");
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&regions)==GEO_SOURCE_OK&&
        regions.as.regions.count==1&&regions.as.regions.regions[0].outline.count==4&&regions.as.regions.regions[0].outline.v[0].u==-51&&
        regions.as.regions.regions[0].outline.v[0].v==-52&&regions.as.regions.regions[0].outline.v[2].u==53&&regions.as.regions.regions[0].outline.v[2].v==54,"local-rect-uses-actual-definition");
    CHECK(s.calls==1&&geometry_has_definition_edge(f.graph,GEO_PLACEMENT_SOURCE_FRAME)&&geometry_has_definition_edge(f.graph,GEO_PLACEMENT_SOURCE_REGIONS),"local-geometry-shares-memoized-definition");
    CHECK(reset(&f,&s),"local-reference-reset");fixed_vector(&s.wire,GEO_PLACEMENT_REGION_REF);
    GeoRegionDefinition target;memset(&target,0,sizeof target);target.id=UINT32_MAX;target.outline.count=1;target.outline.v[0]=(GeoPoint2){661,662};
    CHECK(geo_regions_stage(f.regions,&target),"actual-reference-region-staged");
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&regions)==GEO_SOURCE_OK&&
        regions.as.regions.count==1&&regions.as.regions.regions[0].outline.count==1&&regions.as.regions.regions[0].outline.v[0].u==661,"local-region-reference-uses-actual-definition");
    CHECK(reset(&f,&s),"local-components-reset");fixed_vector(&s.wire,GEO_PLACEMENT_REGION_SET);
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&regions)==GEO_SOURCE_OK&&
        regions.as.regions.count==2&&regions.as.regions.regions[0].outline.count==2&&regions.as.regions.regions[0].outline.v[1].u==43&&
        regions.as.regions.regions[0].hole_count==2&&regions.as.regions.regions[0].holes[0].v[0].u==INT64_MIN&&regions.as.regions.regions[1].outline.count==0,"local-components-use-actual-definition");
    const GeoRegionView *stable=regions.as.regions.regions;const GeoPoint2 *vertices=stable[0].outline.v,*hole=stable[0].holes[0].v;
    GeoPlacementDefinition sibling;expected(&sibling,GEO_PLACEMENT_REGION_SET);sibling.id=71;sibling.components[0].outline.v[1].u=999;
    CHECK(geo_placements_stage(f.placements,&sibling)&&geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,71,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&regions)==GEO_SOURCE_OK,"sibling-component-view-built");
    CHECK(vertices[1].u==43&&hole[0].u==INT64_MIN,"sibling-read-does-not-overwrite-decoded-view");
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_FRAME,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&frame)==GEO_SOURCE_OK,"same-placement-frame-read-after-regions");
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&regions)==GEO_SOURCE_OK&&
        regions.as.regions.regions==stable&&stable[0].outline.v==vertices&&stable[0].holes[0].v==hole&&vertices[1].u==43&&hole[0].u==INT64_MIN,"decoded-component-views-remain-candidate-owned");
    destroy(&f,false);return 0;
}
static int bound_geometry_case(void)
{
    Replacement s;memset(&s,0,sizeof s);s.bind_geometry=true;s.kind=GEO_SOURCE_FRAME;s.schema="deliberately.invalid/1";
    Fixture f;CHECK(fixture(&f,&s),"bound-geometry-fixture-created");GeoPlacementSourceKey key;GeoSourceValue value;
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_FRAME,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.as.frame.origin.x==91&&s.calls==1&&geo_eval_node_count(f.graph)==2,"bound-frame-precedes-authored-definition");
    CHECK(reset(&f,&s),"bound-regions-reset");s.kind=GEO_SOURCE_REGION_SET;
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_REGIONS,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.as.regions.count==1&&value.as.regions.regions[0].outline.v[0].u==81&&geo_eval_node_count(f.graph)==2,"bound-regions-precede-authored-definition");
    CHECK(reset(&f,&s),"bound-failure-reset");s.fail_geometry=true;s.kind=GEO_SOURCE_FRAME;
    CHECK(geo_eval_source(f.graph,geo_placement_source_ref(11,GEO_PLACEMENT_SOURCE_FRAME,TEST_ID,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED&&
        geo_eval_node_count(f.graph)==2,"bound-failure-does-not-fall-back-to-definition");
    destroy(&f,true);return 0;
}
/* Differential oracle: the unchanged public full accessor decodes independent
 * BE vectors above; no copy of the new header parser is used by this client. */
enum { HEADER_CONSUMER_TOKEN=44 };
typedef struct {
    Fixture fixture;Replacement replacement;bool header,ok;unsigned calls;GeoPlacementDomain raw_domain;
    GeoPlacementDefinition full;GeoPlacementDefinitionHeader small;
    GeoSourceProvider original[4];size_t original_count;
    char events[4096];size_t event_size;bool trace_ok;
} HeaderRun;
static HeaderRun *header_active;
static bool header_event(unsigned phase,const GeoSourceRef *ref,bool result)
{
    HeaderRun *s=header_active;if(!s||ref->key_size>8||(ref->key_size&&!ref->key))return false;
    char line[128];int n=snprintf(line,sizeof line,"%u/%u/%zu/",phase,ref->provider,ref->key_size);
    if(n<0||(size_t)n>=sizeof line)return false;size_t at=(size_t)n;
    for(size_t i=0;i<ref->key_size;++i){n=snprintf(line+at,sizeof line-at,"%02x",((const unsigned char *)ref->key)[i]);if(n!=2)return false;at+=2;}
    n=snprintf(line+at,sizeof line-at,"/%u\n",result?1u:0u);if(n<0||(size_t)n>=sizeof line-at)return false;at+=(size_t)n;
    if(at>=sizeof s->events-s->event_size)return false;
    memcpy(s->events+s->event_size,line,at+1);s->event_size+=at;return true;
}
static const GeoSourceProvider *header_original(GeoProviderToken token)
{for(size_t i=0;i<header_active->original_count;++i)if(header_active->original[i].token==token)return &header_active->original[i];return NULL;}
static bool header_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    const GeoSourceProvider *p=header_original(ref->provider);if(!p)return false;
    header_active->trace_ok=header_event(1,ref,false)&&header_active->trace_ok;
    bool ok=p->describe(opaque,ref,out);header_active->trace_ok=header_event(2,ref,ok)&&header_active->trace_ok;return ok;
}
static bool header_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    const GeoSourceProvider *p=header_original(ref->provider);if(!p)return false;
    header_active->trace_ok=header_event(3,ref,false)&&header_active->trace_ok;
    bool ok=p->evaluate(opaque,graph,ref,out);header_active->trace_ok=header_event(4,ref,ok)&&header_active->trace_ok;return ok;
}
static bool header_consumer_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)opaque;if(ref->provider!=HEADER_CONSUMER_TOKEN||ref->key_size!=1||!ref->key||*(const unsigned char *)ref->key!=7)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_SCALAR;out->context.axis=-1;return true;
}
static bool header_consumer_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HeaderRun *s=opaque;(void)ref;if(graph!=s->fixture.graph)return false;++s->calls;
    s->ok=s->header?geo_placement_sources_definition_header(s->fixture.sources,TEST_ID,&s->small):
        geo_placement_sources_definition(s->fixture.sources,TEST_ID,&s->full);
    if(!s->ok)return false;
    GeoPlacementDomain domain=s->header?s->small.domain:s->full.domain;
    uint32_t region=s->header?s->small.region_id:s->full.region_id;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){(int64_t)domain,(int64_t)region+1,GEO_UNIT_SCALAR};return true;
}
static bool header_start(HeaderRun *s,const Replacement *replacement,bool small,GeoPlacementDomain raw_domain)
{
    memset(s,0,sizeof *s);s->replacement=*replacement;s->replacement.calls=0;s->replacement.frame_calls=0;s->replacement.region_calls=0;
    s->header=small;s->raw_domain=raw_domain;s->trace_ok=true;memset(&s->full,0xa5,sizeof s->full);memset(&s->small,0x6b,sizeof s->small);
    if(!fixture(&s->fixture,&s->replacement))return false;
    GeoPlacementDefinition raw;expected(&raw,raw_domain);if(!geo_placements_stage(s->fixture.placements,&raw))return false;
    GeoSourceProvider consumer={HEADER_CONSUMER_TOKEN,"test.header-consumer","header-differential/1",s,header_consumer_describe,header_consumer_evaluate};
    if(!geo_eval_register(s->fixture.graph,&consumer))return false;
    s->original_count=geo_eval_provider_count(s->fixture.graph);if(s->original_count!=4)return false;
    for(size_t i=0;i<s->original_count;++i){GeoSourceProvider *p=(GeoSourceProvider *)geo_eval_provider_at(s->fixture.graph,i);
        s->original[i]=*p;p->describe=header_describe;p->evaluate=header_evaluate;}
    return true;
}
static bool header_text_equal(const char *a,const char *b)
{return a&&b?!strcmp(a,b):a==b;}
static bool header_value_equal(const GeoSourceValue *a,const GeoSourceValue *b)
{
    if(!a||!b)return a==b;if(a->kind!=b->kind)return false;
    if(a->kind==GEO_SOURCE_DEFINITION)return header_text_equal(a->as.definition.schema,b->as.definition.schema)&&
        a->as.definition.content_size==b->as.definition.content_size&&
        (a->as.definition.content&&b->as.definition.content?
         !memcmp(a->as.definition.content,b->as.definition.content,a->as.definition.content_size):a->as.definition.content==b->as.definition.content);
    if(a->kind==GEO_SOURCE_QUANTITY)return a->as.quantity.num==b->as.quantity.num&&a->as.quantity.den==b->as.quantity.den&&a->as.quantity.unit==b->as.quantity.unit;
    if(a->kind==GEO_SOURCE_FRAME)return !memcmp(&a->as.frame,&b->as.frame,sizeof a->as.frame);
    return false;
}
static bool header_graph_equal(const GeoEvalContext *a,const GeoEvalContext *b)
{
    if(geo_eval_node_count(a)!=geo_eval_node_count(b)||geo_eval_edge_count(a)!=geo_eval_edge_count(b))return false;
    for(size_t i=0;i<geo_eval_node_count(a);++i){GeoSourceNodeView x,y;
        if(!geo_eval_node_at(a,i,&x)||!geo_eval_node_at(b,i,&y)||x.source.provider!=y.source.provider||x.source.key_size!=y.source.key_size||
           memcmp(x.source.key,y.source.key,x.source.key_size)||x.described!=y.described||x.state!=y.state||x.status!=y.status||
           x.descriptor.kind!=y.descriptor.kind||x.descriptor.unit!=y.descriptor.unit||
           x.descriptor.context.has_placement!=y.descriptor.context.has_placement||x.descriptor.context.placement!=y.descriptor.context.placement||x.descriptor.context.axis!=y.descriptor.context.axis||
           x.descriptor.retry_failure!=y.descriptor.retry_failure||x.descriptor.context_from_value!=y.descriptor.context_from_value||!header_value_equal(x.value,y.value))return false;
    }
    for(size_t i=0;i<geo_eval_edge_count(a);++i){GeoSourceEdge x,y;
        if(!geo_eval_edge_at(a,i,&x)||!geo_eval_edge_at(b,i,&y)||x.consumer!=y.consumer||x.source!=y.source||x.kind!=y.kind)return false;}
    return true;
}
static bool header_definition_edges(const GeoEvalContext *graph)
{
    if(geo_eval_edge_count(graph)!=2)return false;
    const GeoProviderToken from[]={HEADER_CONSUMER_TOKEN,11},to[]={11,33};
    for(size_t i=0;i<2;++i){GeoSourceEdge e;GeoSourceNodeView a,b;
        if(!geo_eval_edge_at(graph,i,&e)||e.kind!=GEO_DEPENDENCY_DEFINITION_REQUIRED||!geo_eval_node_at(graph,e.consumer,&a)||!geo_eval_node_at(graph,e.source,&b)||
           a.source.provider!=from[i]||b.source.provider!=to[i])return false;}
    return true;
}
static int header_pair_raw(const Replacement *replacement,GeoPlacementDomain raw_domain,bool accepted,const char *mismatch)
{
    HeaderRun a,b;CHECK(header_start(&a,replacement,false,raw_domain)&&header_start(&b,replacement,true,raw_domain),"header-pair-fresh-fixtures");
    unsigned char key=7;GeoSourceValue av,bv;header_active=&a;
    GeoSourceStatus ar=geo_eval_source(a.fixture.graph,(GeoSourceRef){HEADER_CONSUMER_TOKEN,&key,1},GEO_DEPENDENCY_VALUE_REQUIRED,&av);
    header_active=&b;GeoSourceStatus br=geo_eval_source(b.fixture.graph,(GeoSourceRef){HEADER_CONSUMER_TOKEN,&key,1},GEO_DEPENDENCY_VALUE_REQUIRED,&bv);header_active=NULL;
    CHECK(a.calls==1&&b.calls==1&&a.trace_ok&&b.trace_ok,"header-pair-exercises-both-real-accessors");
    CHECK(a.ok==accepted,"header-full-oracle-has-independent-expected-outcome");
    CHECK(a.ok==b.ok&&ar==br,mismatch);
    if(a.ok){
        CHECK(a.full.domain==b.small.domain,"header-domain-matches-full-projection");
        CHECK(a.full.region_id==b.small.region_id,"header-region-matches-full-projection");
    }else{
        unsigned char full[sizeof a.full],small[sizeof b.small];memset(full,0xa5,sizeof full);memset(small,0x6b,sizeof small);
        CHECK(!memcmp(&a.full,full,sizeof full)&&!memcmp(&b.small,small,sizeof small),"header-failure-preserves-all-output-bytes");
    }
    CHECK(header_definition_edges(a.fixture.graph)&&header_definition_edges(b.fixture.graph),"header-consumer-edge-requires-definition");
    CHECK(!strcmp(a.events,b.events)&&header_graph_equal(a.fixture.graph,b.fixture.graph),"header-ordered-calls-and-typed-graph-match-full");
    CHECK(a.replacement.calls==1&&b.replacement.calls==1&&!a.replacement.frame_calls&&!a.replacement.region_calls&&!b.replacement.frame_calls&&!b.replacement.region_calls,
        "header-reads-only-the-bound-definition-once");
    CHECK(geo_placements_find(a.fixture.placements,TEST_ID)->domain==raw_domain&&geo_placements_find(b.fixture.placements,TEST_ID)->domain==raw_domain,
        "header-binding-does-not-mutate-authored-store");
    if(a.ok){GeoPlacementDefinition again;GeoPlacementDefinitionHeader small;
        size_t an=geo_eval_node_count(a.fixture.graph),bn=geo_eval_node_count(b.fixture.graph),ae=geo_eval_edge_count(a.fixture.graph),be=geo_eval_edge_count(b.fixture.graph);
        header_active=&a;bool x=geo_placement_sources_definition_header(a.fixture.sources,TEST_ID,&small);
        header_active=&b;bool y=geo_placement_sources_definition(b.fixture.sources,TEST_ID,&again);header_active=NULL;
        CHECK(x&&y&&small.domain==a.full.domain&&small.region_id==a.full.region_id&&again.domain==b.small.domain&&again.region_id==b.small.region_id&&
            a.replacement.calls==1&&b.replacement.calls==1&&geo_eval_node_count(a.fixture.graph)==an&&geo_eval_node_count(b.fixture.graph)==bn&&
            geo_eval_edge_count(a.fixture.graph)==ae&&geo_eval_edge_count(b.fixture.graph)==be,"header-full-both-read-orders-share-one-cached-source");
    }
    destroy(&a.fixture,true);destroy(&b.fixture,false);return 0;
}
static int header_pair(const Replacement *replacement,bool accepted,const char *mismatch)
{return header_pair_raw(replacement,GEO_PLACEMENT_RECT,accepted,mismatch);}
static void header_replacement(Replacement *s,int domain)
{memset(s,0,sizeof *s);s->kind=GEO_SOURCE_DEFINITION;s->schema=GEO_PLACEMENT_DEFINITION_SCHEMA;fixed_vector(&s->wire,domain);}
static int header_values_case(void)
{
    Replacement s;GeoPlacementDefinition maximum;
    for(int domain=0;domain<=2;++domain){header_replacement(&s,domain);if(header_pair(&s,true,"header-valid-wire-acceptance-matches-full"))return 1;}
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.wire.size=101;u32(&s.wire,0);
    if(header_pair(&s,true,"header-empty-set-acceptance-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_REF);memset(s.wire.bytes+101,0,4);
    if(header_pair(&s,true,"header-zero-reference-acceptance-matches-full"))return 1;
    maximal(&s.wire,&maximum);if(header_pair(&s,true,"header-maximal-wire-acceptance-matches-full"))return 1;
    return 0;
}
static void header_count_wire(Vector *v,size_t components,size_t outline,size_t holes,size_t vertices)
{
    fixed_vector(v,GEO_PLACEMENT_REGION_SET);v->size=101;u32(v,(uint32_t)components);
    for(size_t c=0;c<components;++c){u32(v,(uint32_t)c);u32(v,(uint32_t)outline);
        for(size_t n=0;n<outline;++n){i64(v,(int64_t)n);i64(v,-(int64_t)n);}
        u32(v,(uint32_t)holes);for(size_t h=0;h<holes;++h){u32(v,(uint32_t)vertices);
            for(size_t n=0;n<vertices;++n){i64(v,INT64_MIN);i64(v,INT64_MAX);}}}
}
static int header_malformed_case(void)
{
    Replacement s;Vector original;GeoPlacementDefinition maximum;
    for(int domain=0;domain<=2;++domain){header_replacement(&s,domain);original=s.wire;
        for(size_t n=0;n<original.size;++n){s.wire.size=n;if(header_pair(&s,false,"header-truncation-matches-full"))return 1;}
        s.wire=original;s.wire.bytes[s.wire.size++]=0xa5;if(header_pair(&s,false,"header-tail-matches-full"))return 1;}
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);
    for(unsigned domain=3;domain<256;++domain){s.wire.bytes[100]=(unsigned char)domain;if(header_pair(&s,false,"header-domain-bound-matches-full"))return 1;}
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);header_count_wire(&s.wire,GEO_PLACEMENT_COMPONENT_CAPACITY+1,0,0,0);
    if(header_pair(&s,false,"header-component-bound-matches-full"))return 1;
    header_count_wire(&s.wire,1,0,GEO_REGION_MAX_HOLES+1,0);if(header_pair(&s,false,"header-hole-bound-matches-full"))return 1;
    header_count_wire(&s.wire,1,GEO_LOOP_MAX_VERTICES+1,0,0);if(header_pair(&s,false,"header-vertex-bound-matches-full"))return 1;
    header_count_wire(&s.wire,1,0,1,GEO_LOOP_MAX_VERTICES+1);if(header_pair(&s,false,"header-hole-vertex-bound-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);maximal(&s.wire,&maximum);original=s.wire;
    const size_t coordinates=16u*GEO_LOOP_MAX_VERTICES,component_bytes=12u+coordinates+GEO_REGION_MAX_HOLES*(4u+coordinates);
    for(size_t c=0;c<GEO_PLACEMENT_COMPONENT_CAPACITY;++c){size_t at=105u+c*component_bytes;
        const size_t cuts[]={at-1,at+3,at+4,at+7,at+8,at+8+coordinates-1,at+8+coordinates+3};
        for(size_t n=0;n<sizeof cuts/sizeof *cuts;++n){s.wire=original;s.wire.size=cuts[n];if(header_pair(&s,false,"header-maximal-boundary-truncation-matches-full"))return 1;}
        for(size_t h=0;h<GEO_REGION_MAX_HOLES;++h){size_t start=at+12u+coordinates+h*(4u+coordinates);
            const size_t hole_cuts[]={start,start+3,start+4,start+4+coordinates-1};
            for(size_t n=0;n<sizeof hole_cuts/sizeof *hole_cuts;++n){s.wire=original;s.wire.size=hole_cuts[n];if(header_pair(&s,false,"header-maximal-hole-truncation-matches-full"))return 1;}}
    }
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);memset(s.wire.bytes+101,0xff,4);
    if(header_pair(&s,false,"header-u32-component-count-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.wire.size=GEO_PLACEMENT_DEFINITION_MAX_BYTES+1;
    if(header_pair(&s,false,"header-oversize-matches-full"))return 1;
    return 0;
}
static int header_authority_case(void)
{
    Replacement s;header_replacement(&s,GEO_PLACEMENT_REGION_SET);
    if(header_pair(&s,true,"header-binding-acceptance-matches-full"))return 1;
    for(int domain=0;domain<=1;++domain){header_replacement(&s,domain);
        if(header_pair_raw(&s,GEO_PLACEMENT_REGION_SET,true,"header-reverse-binding-acceptance-matches-full"))return 1;}
    const char *schemas[]={NULL,"","other.schema/1","geometry.placement-definition/2"};
    for(size_t i=0;i<sizeof schemas/sizeof *schemas;++i){header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.schema=schemas[i];
        if(header_pair(&s,false,"header-schema-rejection-matches-full"))return 1;}
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.wire.bytes[3]^=1;
    if(header_pair(&s,false,"header-id-rejection-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.kind=GEO_SOURCE_FRAME;
    if(header_pair(&s,false,"header-value-kind-rejection-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.fail_geometry=true;
    if(header_pair(&s,false,"header-upstream-failure-matches-full"))return 1;
    header_replacement(&s,GEO_PLACEMENT_REGION_SET);s.null_content=true;
    if(header_pair(&s,false,"header-null-content-rejection-matches-full"))return 1;
    GeoPlacementDefinitionHeader untouched,before;memset(&untouched,0x93,sizeof untouched);memcpy(&before,&untouched,sizeof before);
    CHECK(!geo_placement_sources_definition_header(NULL,TEST_ID,&untouched)&&!memcmp(&untouched,&before,sizeof untouched),"header-null-handle-preserves-output");
    Fixture f;header_replacement(&s,GEO_PLACEMENT_REGION_SET);CHECK(fixture(&f,&s),"header-null-output-fixture");
    CHECK(!geo_placement_sources_definition_header(f.sources,TEST_ID,NULL)&&geo_eval_node_count(f.graph)==0,"header-null-output-does-not-evaluate");
    GeoPlacementDefinitionHeader first,changed;GeoPlacementDefinition full;
    CHECK(geo_placement_sources_definition_header(f.sources,TEST_ID,&first)&&first.domain==GEO_PLACEMENT_REGION_SET,"header-lifecycle-primes-binding");
    header_replacement(&s,GEO_PLACEMENT_REGION_REF);CHECK(reset(&f,&s),"header-lifecycle-reset");
    CHECK(geo_placement_sources_definition_header(f.sources,TEST_ID,&changed)&&geo_placement_sources_definition(f.sources,TEST_ID,&full)&&
        changed.domain==full.domain&&changed.region_id==full.region_id&&changed.domain==GEO_PLACEMENT_REGION_REF&&changed.region_id==UINT32_MAX&&first.domain==GEO_PLACEMENT_REGION_SET,"header-reset-sees-new-binding-and-owned-old-fields");
    Replacement other;header_replacement(&other,GEO_PLACEMENT_RECT);Fixture sibling;CHECK(fixture(&sibling,&other),"header-isolation-fixture");
    CHECK(geo_placement_sources_definition_header(sibling.sources,TEST_ID,&changed)&&changed.domain==GEO_PLACEMENT_RECT&&
        geo_placement_sources_definition_header(f.sources,TEST_ID,&first)&&first.domain==GEO_PLACEMENT_REGION_REF,"header-same-key-candidates-never-share-values");
    destroy(&sibling,false);
    destroy(&f,true);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"header-values"))return header_values_case();
    if(!strcmp(argv[1],"header-malformed"))return header_malformed_case();
    if(!strcmp(argv[1],"header-authority"))return header_authority_case();
    if(!strcmp(argv[1],"keys"))return keys_case();if(!strcmp(argv[1],"codec"))return codec_case();
    if(!strcmp(argv[1],"bounds"))return bounds_case();if(!strcmp(argv[1],"malformed"))return malformed_case();
    if(!strcmp(argv[1],"definition"))return definition_case();if(!strcmp(argv[1],"typed"))return typed_case();
    if(!strcmp(argv[1],"typed-invalid"))return typed_invalid_case();if(!strcmp(argv[1],"lifecycle"))return lifecycle_case();
    if(!strcmp(argv[1],"local-geometry"))return local_geometry_case();if(!strcmp(argv[1],"bound-geometry"))return bound_geometry_case();return 2;
}
