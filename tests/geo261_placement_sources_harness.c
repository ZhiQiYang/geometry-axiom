/* Standalone K placement/region source graph. Expected values and edges are
 * fixed here; no host, template, bridge, private store or alternate evaluator. */
#include "placement_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(label,expression) do{if(!(expression)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
enum { PLACEMENT_TOKEN=31,REGION_TOKEN=32,UPSTREAM_TOKEN=41 };

typedef struct {
    GeoEvalContext *graph;
    GeoFrame frame;
    GeoPoint2 points[4],hole_points[4];
    GeoLoop2View holes[1];
    GeoRegionView region;
    unsigned char keys[2];
    unsigned frame_calls,region_calls,binding_calls;
    unsigned frame_binding_calls,region_binding_calls,definition_binding_calls;
    GeoSourceValueKind frame_kind,region_kind;
    bool enabled,fail,lie;
} Upstream;
typedef struct {
    GeoPlacementStore *placements;
    GeoRegionStore *regions;
    GeoEvalContext *graph;
    GeoPlacementSources *sources;
    Upstream upstream;
} Fixture;

static GeoFrame frame(GeoCoord origin)
{return (GeoFrame){{origin,-20,30},{0,1,0},{0,0,1},{1,0,0}};}
static bool same_frame(GeoFrame a,GeoFrame b)
{
    return a.origin.x==b.origin.x&&a.origin.y==b.origin.y&&a.origin.z==b.origin.z&&
        geo_vector_equal(a.axis_u,b.axis_u)&&geo_vector_equal(a.axis_v,b.axis_v)&&geo_vector_equal(a.normal,b.normal);
}
static void box(GeoRegionLoop *loop,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{
    memset(loop,0,sizeof *loop);loop->count=4;
    loop->v[0]=(GeoPoint2){a,b};loop->v[1]=(GeoPoint2){c,b};
    loop->v[2]=(GeoPoint2){c,d};loop->v[3]=(GeoPoint2){a,d};
}
static GeoRegionDefinition region(uint32_t id,GeoCoord offset,bool hole)
{
    GeoRegionDefinition r;memset(&r,0,sizeof r);r.id=id;
    box(&r.outline,offset,0,offset+20,20);
    if(hole){r.hole_count=1;box(&r.holes[0],offset+5,5,offset+10,10);}
    return r;
}
static GeoPlacementDefinition rectangle(uint32_t id,GeoCoord origin)
{
    GeoPlacementDefinition p;memset(&p,0,sizeof p);p.id=id;p.frame=frame(origin);
    p.domain=GEO_PLACEMENT_RECT;p.rect=(GeoRect2){-10,-5,30,20};return p;
}
static bool loop_is_box(GeoLoop2View loop,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{
    return loop.count==4&&loop.v&&loop.v[0].u==a&&loop.v[0].v==b&&
        loop.v[1].u==c&&loop.v[1].v==b&&loop.v[2].u==c&&loop.v[2].v==d&&loop.v[3].u==a&&loop.v[3].v==d;
}
static bool is_region(GeoRegionSetView set,GeoCoord offset,bool hole)
{
    return set.count==1&&set.regions&&loop_is_box(set.regions[0].outline,offset,0,offset+20,20)&&
        set.regions[0].hole_count==(hole?1u:0u)&&(!hole||
            (set.regions[0].holes&&loop_is_box(set.regions[0].holes[0],offset+5,5,offset+10,10)));
}
static bool upstream_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    Upstream *s=opaque;if(ref->key_size!=1||!ref->key)return false;
    unsigned key=*(const unsigned char *)ref->key;if(key<1||key>2)return false;
    memset(out,0,sizeof *out);out->kind=key==1?s->frame_kind:s->region_kind;
    out->unit=GEO_UNIT_LENGTH;out->context.axis=-1;return true;
}
static bool upstream_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Upstream *s=opaque;if(graph!=s->graph||ref->key_size!=1||!ref->key)return false;
    unsigned key=*(const unsigned char *)ref->key;if(key<1||key>2)return false;
    if(key==1)++s->frame_calls;else ++s->region_calls;
    if(s->fail)return false;
    out->kind=s->lie?GEO_SOURCE_QUANTITY:key==1?s->frame_kind:s->region_kind;
    if(out->kind==GEO_SOURCE_FRAME)out->as.frame=s->frame;
    else if(out->kind==GEO_SOURCE_REGION_SET)out->as.regions=(GeoRegionSetView){&s->region,1};
    else if(out->kind==GEO_SOURCE_QUANTITY)out->as.quantity=(GeoQuantity){77,1,GEO_UNIT_LENGTH};
    else return false;
    return true;
}
static bool binding(void *opaque,uint32_t id,GeoPlacementSourceKind kind,GeoSourceRef *out)
{
    Upstream *s=opaque;++s->binding_calls;
    if(kind==GEO_PLACEMENT_SOURCE_FRAME)++s->frame_binding_calls;
    else if(kind==GEO_PLACEMENT_SOURCE_REGIONS)++s->region_binding_calls;
    else if(kind==GEO_PLACEMENT_SOURCE_DEFINITION)++s->definition_binding_calls;
    if(!s->enabled)return false;
    if(id==10&&kind==GEO_PLACEMENT_SOURCE_FRAME){*out=(GeoSourceRef){UPSTREAM_TOKEN,s->keys,1};return true;}
    if(id==11&&kind==GEO_PLACEMENT_SOURCE_REGIONS){*out=(GeoSourceRef){UPSTREAM_TOKEN,s->keys+1,1};return true;}
    return false;
}
static int setup(Fixture *f,uint64_t candidate,GeoCoord offset,bool use_binding)
{
    memset(f,0,sizeof *f);f->placements=geo_placements_create();f->regions=geo_regions_create();
    f->graph=geo_eval_create(candidate,73);CHECK("fixture-owned-stores-and-graph",f->placements&&f->regions&&f->graph);
    GeoRegionDefinition r=region(29,offset,true);CHECK("fixture-region-29",geo_regions_put(f->regions,&r));
    r=region(30,offset+100,true);CHECK("fixture-region-30",geo_regions_put(f->regions,&r));
    GeoPlacementDefinition p=rectangle(10,offset+10);CHECK("fixture-rectangle",geo_placements_put(f->placements,&p,f->regions));
    p=rectangle(11,offset+11);p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=29;
    CHECK("fixture-region-reference",geo_placements_put(f->placements,&p,f->regions));
    p=rectangle(12,offset+12);p.domain=GEO_PLACEMENT_REGION_SET;p.component_count=2;
    p.components[0]=region(700,offset+200,true);p.components[1]=region(900,offset+300,false);
    CHECK("fixture-region-set",geo_placements_put(f->placements,&p,f->regions));
    p=rectangle(13,offset+13);p.domain=GEO_PLACEMENT_REGION_SET;p.component_count=0;
    CHECK("fixture-empty-region-set",geo_placements_put(f->placements,&p,f->regions));
    Upstream *u=&f->upstream;u->graph=f->graph;u->frame=frame(offset+777);u->keys[0]=1;u->keys[1]=2;
    u->frame_kind=GEO_SOURCE_FRAME;u->region_kind=GEO_SOURCE_REGION_SET;u->enabled=use_binding;
    r=region(99,offset+500,true);memcpy(u->points,r.outline.v,sizeof u->points);memcpy(u->hole_points,r.holes[0].v,sizeof u->hole_points);
    u->holes[0]=(GeoLoop2View){u->hole_points,4};u->region=(GeoRegionView){{u->points,4},u->holes,1};
    if(use_binding){GeoSourceProvider upstream={UPSTREAM_TOKEN,"test.upstream","typed-geometry/1",u,upstream_describe,upstream_evaluate};
        CHECK("fixture-upstream-provider",geo_eval_register(f->graph,&upstream));}
    f->sources=geo_placement_sources_register(f->graph,f->placements,f->regions,PLACEMENT_TOKEN,REGION_TOKEN,
        use_binding?binding:NULL,use_binding?u:NULL);
    CHECK("fixture-placement-source-family",f->sources);return 0;
}
static void dispose(Fixture *f,bool graph_first)
{
    if(graph_first){geo_eval_destroy(f->graph);geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);geo_placement_sources_destroy(f->sources);}
    else{geo_placement_sources_destroy(f->sources);geo_eval_destroy(f->graph);geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);}
}
static GeoSourceStatus placement_value(Fixture *f,uint32_t id,GeoPlacementSourceKind kind,GeoSourceValue *out)
{
    GeoPlacementSourceKey key;return geo_eval_source(f->graph,geo_placement_source_ref(PLACEMENT_TOKEN,kind,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out);
}
static GeoSourceStatus region_value(Fixture *f,uint32_t id,GeoSourceValue *out)
{
    GeoRegionSourceKey key;return geo_eval_source(f->graph,geo_region_source_ref(REGION_TOKEN,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out);
}
static size_t node_index(GeoEvalContext *graph,GeoSourceRef source)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(graph,i,&n)&&n.source.provider==source.provider&&n.source.key_size==source.key_size&&
           !memcmp(n.source.key,source.key,source.key_size))return i;}
    return SIZE_MAX;
}
static bool typed_edge(GeoEvalContext *graph,GeoSourceRef from,GeoSourceRef to,GeoDependencyKind kind)
{
    size_t a=node_index(graph,from),b=node_index(graph,to);
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(graph,i,&e)&&e.consumer==a&&e.source==b&&e.kind==kind)return true;}
    return false;
}
static bool edge(GeoEvalContext *graph,GeoSourceRef from,GeoSourceRef to)
{return typed_edge(graph,from,to,GEO_DEPENDENCY_VALUE_REQUIRED);}
static bool definition_edge(GeoEvalContext *graph,uint32_t id,GeoPlacementSourceKind kind)
{
    GeoPlacementSourceKey value_key,definition_key;
    return typed_edge(graph,geo_placement_source_ref(PLACEMENT_TOKEN,kind,id,&value_key),
        geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_DEFINITION,id,&definition_key),GEO_DEPENDENCY_DEFINITION_REQUIRED);
}
static bool definition_node(GeoEvalContext *graph,uint32_t id)
{
    GeoPlacementSourceKey key;GeoSourceNodeView node;
    size_t index=node_index(graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_DEFINITION,id,&key));
    return geo_eval_node_at(graph,index,&node)&&node.descriptor.kind==GEO_SOURCE_DEFINITION&&node.descriptor.unit==GEO_UNIT_SCALAR&&
        node.descriptor.context.has_placement&&node.descriptor.context.placement==id&&node.descriptor.context.axis==-1&&
        node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&
        node.value->as.definition.schema&&!strcmp(node.value->as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA);
}
static bool stable_inline_view(GeoRegionSetView value,const GeoRegionView *regions,const GeoPoint2 *first,
    const GeoPoint2 *second,const GeoLoop2View *holes,const GeoPoint2 *hole_vertices)
{
    return value.count==2&&value.regions==regions&&value.regions[0].outline.v==first&&value.regions[1].outline.v==second&&
        value.regions[0].holes==holes&&value.regions[0].holes[0].v==hole_vertices&&
        is_region((GeoRegionSetView){value.regions,1},200,true)&&is_region((GeoRegionSetView){value.regions+1,1},300,false);
}
static int key_contract(void)
{
    GeoPlacementSourceKey key;GeoRegionSourceKey rkey;
    GeoSourceRef ref=geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,UINT32_C(0x010002ff),&key);
    const unsigned char expected[]={2,1,0,2,255};
    CHECK("placement-key-canonical-bytes",ref.provider==PLACEMENT_TOKEN&&ref.key_size==5&&!memcmp(key.bytes,expected,5));
    GeoPlacementSourceKind kind=GEO_PLACEMENT_SOURCE_FRAME;uint32_t id=99;
    CHECK("placement-key-decodes-full-id",geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_REGIONS&&id==UINT32_C(0x010002ff));
    ref=geo_region_source_ref(REGION_TOKEN,UINT32_MAX,&rkey);
    CHECK("region-key-decodes-full-id",ref.key_size==4&&geo_region_source_decode(&ref,&id)&&id==UINT32_MAX);
    ref=geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_DEFINITION,UINT32_C(0x010002ff),&key);
    const unsigned char definition_expected[]={3,1,0,2,255};
    CHECK("definition-key-canonical-bytes",ref.provider==PLACEMENT_TOKEN&&ref.key_size==5&&!memcmp(key.bytes,definition_expected,5));
    CHECK("definition-key-decodes-full-id",geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_DEFINITION&&id==UINT32_C(0x010002ff));
    kind=GEO_PLACEMENT_SOURCE_FRAME;id=123;key.bytes[0]=0;ref=(GeoSourceRef){PLACEMENT_TOKEN,key.bytes,5};
    CHECK("invalid-key-keeps-decode-outputs",!geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_FRAME&&id==123);
    key.bytes[0]=0xff;CHECK("unknown-key-kind-rejected",!geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_FRAME&&id==123);
    for(unsigned tag=4;tag<0xff;++tag){key.bytes[0]=(unsigned char)tag;
        CHECK("all-other-unknown-key-kinds-rejected",!geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_FRAME&&id==123);}
    key.bytes[0]=1;ref.key_size=4;CHECK("short-placement-key-rejected",!geo_placement_source_decode(&ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_FRAME&&id==123);
    ref.key=NULL;CHECK("null-region-key-rejected",!geo_region_source_decode(&ref,&id)&&id==123);
    CHECK("null-decode-arguments-rejected",!geo_region_source_decode(NULL,&id)&&!geo_placement_source_decode(NULL,&kind,&id));return 0;
}
static int explicit_leaves(void)
{
    Fixture f;CHECK("setup",setup(&f,901,0,false)==0);
    CHECK("family-registers-two-providers",geo_eval_provider_count(f.graph)==2&&
        !strcmp(geo_eval_provider_at(f.graph,0)->name_space,"core.region")&&
        !strcmp(geo_eval_provider_at(f.graph,1)->name_space,"core.placement"));
    GeoPlacementSourceKey key;GeoSourceDescriptor d;GeoSourceValue value;
    CHECK("frame-description",geo_eval_describe(f.graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,10,&key),&d)==GEO_SOURCE_OK&&
        d.kind==GEO_SOURCE_FRAME&&d.unit==GEO_UNIT_LENGTH&&d.context.has_placement&&d.context.placement==10&&d.context.axis==-1);
    GeoSourceNodeView node;CHECK("describe-does-not-evaluate",geo_eval_node_at(f.graph,0,&node)&&node.state==GEO_NODE_NEW&&!node.value&&geo_eval_edge_count(f.graph)==0);
    CHECK("actual-stored-frame-leaf",placement_value(&f,10,GEO_PLACEMENT_SOURCE_FRAME,&value)==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_FRAME&&same_frame(value.as.frame,frame(10)));
    CHECK("actual-rectangle-leaf",placement_value(&f,10,GEO_PLACEMENT_SOURCE_REGIONS,&value)==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_REGION_SET&&
        value.as.regions.count==1&&loop_is_box(value.as.regions.regions[0].outline,-10,-5,30,20)&&value.as.regions.regions[0].hole_count==0);
    CHECK("actual-region-leaf",region_value(&f,29,&value)==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_REGION_SET&&is_region(value.as.regions,0,true));
    const GeoRegionDefinition *owned=geo_regions_find(f.regions,29);
    CHECK("region-leaf-borrows-owned-vertices",value.as.regions.regions[0].outline.v==owned->outline.v&&value.as.regions.regions[0].holes[0].v==owned->holes[0].v);
    CHECK("explicit-geometry-has-one-shared-definition",geo_eval_node_count(f.graph)==4&&geo_eval_edge_count(f.graph)==2&&definition_node(f.graph,10));
    CHECK("explicit-frame-requires-its-definition",definition_edge(f.graph,10,GEO_PLACEMENT_SOURCE_FRAME));
    CHECK("explicit-regions-require-the-same-definition",definition_edge(f.graph,10,GEO_PLACEMENT_SOURCE_REGIONS));
    dispose(&f,true);return 0;
}
static int region_reference(void)
{
    Fixture f;CHECK("setup",setup(&f,902,0,false)==0);GeoSourceValue value,leaf;
    CHECK("region-reference-returns-actual-geometry",placement_value(&f,11,GEO_PLACEMENT_SOURCE_REGIONS,&value)==GEO_SOURCE_OK&&is_region(value.as.regions,0,true));
    GeoPlacementSourceKey key;GeoRegionSourceKey rkey;
    CHECK("placement-region-reference-edge",edge(f.graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,11,&key),geo_region_source_ref(REGION_TOKEN,29,&rkey)));
    CHECK("region-reference-has-definition-and-value-edges",geo_eval_node_count(f.graph)==3&&geo_eval_edge_count(f.graph)==2&&
        definition_node(f.graph,11)&&definition_edge(f.graph,11,GEO_PLACEMENT_SOURCE_REGIONS));
    CHECK("region-reference-reuses-core-region-value",region_value(&f,29,&leaf)==GEO_SOURCE_OK&&leaf.as.regions.regions==value.as.regions.regions);
    size_t region_index=node_index(f.graph,geo_region_source_ref(REGION_TOKEN,29,&rkey));
    GeoSourceNodeView n;CHECK("region-node-does-not-claim-placement-context",geo_eval_node_at(f.graph,region_index,&n)&&n.descriptor.kind==GEO_SOURCE_REGION_SET&&!n.descriptor.context.has_placement);
    CHECK("region-reference-seals",geo_eval_seal(f.graph));GeoSourceValue again;
    CHECK("region-reference-sealed-borrow-stable",placement_value(&f,11,GEO_PLACEMENT_SOURCE_REGIONS,&again)==GEO_SOURCE_OK&&
        again.as.regions.regions==value.as.regions.regions&&is_region(value.as.regions,0,true));
    dispose(&f,false);return 0;
}
static int borrowed_views(void)
{
    Fixture f;CHECK("setup",setup(&f,903,0,false)==0);GeoSourceValue region_a,region_b,set,rect,empty;
    CHECK("first-hole-view",region_value(&f,29,&region_a)==GEO_SOURCE_OK);
    CHECK("second-hole-view",region_value(&f,30,&region_b)==GEO_SOURCE_OK);
    CHECK("inline-component-views",placement_value(&f,12,GEO_PLACEMENT_SOURCE_REGIONS,&set)==GEO_SOURCE_OK);
    CHECK("inline-set-preserves-order-and-holes",set.kind==GEO_SOURCE_REGION_SET&&set.as.regions.count==2&&set.as.regions.regions&&
        loop_is_box(set.as.regions.regions[0].outline,200,0,220,20)&&set.as.regions.regions[0].hole_count==1&&set.as.regions.regions[0].holes&&
        loop_is_box(set.as.regions.regions[0].holes[0],205,5,210,10)&&loop_is_box(set.as.regions.regions[1].outline,300,0,320,20)&&set.as.regions.regions[1].hole_count==0);
    const GeoRegionView *inline_regions=set.as.regions.regions;
    const GeoPoint2 *first_vertices=inline_regions[0].outline.v,*second_vertices=inline_regions[1].outline.v;
    const GeoLoop2View *inline_holes=inline_regions[0].holes;const GeoPoint2 *hole_vertices=inline_holes[0].v;
    CHECK("rectangle-scratch-view",placement_value(&f,10,GEO_PLACEMENT_SOURCE_REGIONS,&rect)==GEO_SOURCE_OK);
    CHECK("empty-region-set-is-a-valid-value",placement_value(&f,13,GEO_PLACEMENT_SOURCE_REGIONS,&empty)==GEO_SOURCE_OK&&empty.kind==GEO_SOURCE_REGION_SET&&empty.as.regions.count==0);
    CHECK("separate-region-hole-scratch-survives-other-reads",is_region(region_a.as.regions,0,true)&&is_region(region_b.as.regions,100,true)&&
        region_a.as.regions.regions!=region_b.as.regions.regions&&region_a.as.regions.regions[0].holes!=region_b.as.regions.regions[0].holes);
    CHECK("inline-set-survives-other-placement-reads",stable_inline_view(set.as.regions,inline_regions,first_vertices,second_vertices,inline_holes,hole_vertices));
    GeoSourceValue same_placement_frame,cached_set;
    CHECK("inline-set-frame-read-after-other-placements",placement_value(&f,12,GEO_PLACEMENT_SOURCE_FRAME,&same_placement_frame)==GEO_SOURCE_OK&&
        same_placement_frame.kind==GEO_SOURCE_FRAME&&same_frame(same_placement_frame.as.frame,frame(12)));
    CHECK("inline-set-borrows-stable-candidate-definition",placement_value(&f,12,GEO_PLACEMENT_SOURCE_REGIONS,&cached_set)==GEO_SOURCE_OK&&
        cached_set.kind==GEO_SOURCE_REGION_SET&&stable_inline_view(cached_set.as.regions,inline_regions,first_vertices,second_vertices,inline_holes,hole_vertices)&&
        stable_inline_view(set.as.regions,inline_regions,first_vertices,second_vertices,inline_holes,hole_vertices));
    CHECK("rectangle-scratch-is-not-overwritten",loop_is_box(rect.as.regions.regions[0].outline,-10,-5,30,20));
    CHECK("borrowed-views-seal",geo_eval_seal(f.graph));
    for(unsigned i=0;i<10;++i){GeoSourceValue cached;
        CHECK("cached-holes-remain-alive",region_value(&f,29,&cached)==GEO_SOURCE_OK&&cached.as.regions.regions==region_a.as.regions.regions&&is_region(cached.as.regions,0,true));
        CHECK("sealed-inline-borrow-keeps-pointers-and-literal-geometry",placement_value(&f,12,GEO_PLACEMENT_SOURCE_REGIONS,&cached)==GEO_SOURCE_OK&&
            cached.kind==GEO_SOURCE_REGION_SET&&stable_inline_view(cached.as.regions,inline_regions,first_vertices,second_vertices,inline_holes,hole_vertices));}
    dispose(&f,true);return 0;
}
static int binding_values(void)
{
    Fixture a,b;CHECK("binding-first-setup",setup(&a,904,0,true)==0);CHECK("binding-second-setup",setup(&b,905,1000,true)==0);
    GeoSourceValue af,bf,ar,br;
    CHECK("binding-first-frame-evaluates",placement_value(&a,10,GEO_PLACEMENT_SOURCE_FRAME,&af)==GEO_SOURCE_OK);
    CHECK("placement-binding-consumes-upstream-frame",af.kind==GEO_SOURCE_FRAME&&same_frame(af.as.frame,frame(777)));
    CHECK("binding-new-candidate-frame-evaluates",placement_value(&b,10,GEO_PLACEMENT_SOURCE_FRAME,&bf)==GEO_SOURCE_OK);
    CHECK("changed-upstream-frame-reaches-returned-value",bf.kind==GEO_SOURCE_FRAME&&same_frame(bf.as.frame,frame(1777))&&same_frame(af.as.frame,frame(777)));
    CHECK("binding-first-regions-evaluates",placement_value(&a,11,GEO_PLACEMENT_SOURCE_REGIONS,&ar)==GEO_SOURCE_OK);
    CHECK("placement-binding-consumes-upstream-regions",ar.kind==GEO_SOURCE_REGION_SET&&is_region(ar.as.regions,500,true));
    CHECK("changed-upstream-regions-reach-returned-value",placement_value(&b,11,GEO_PLACEMENT_SOURCE_REGIONS,&br)==GEO_SOURCE_OK&&is_region(br.as.regions,1500,true)&&is_region(ar.as.regions,500,true));
    GeoPlacementSourceKey key;
    CHECK("frame-binding-records-value-edge",edge(a.graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,10,&key),(GeoSourceRef){UPSTREAM_TOKEN,a.upstream.keys,1}));
    CHECK("region-binding-records-value-edge",edge(a.graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,11,&key),(GeoSourceRef){UPSTREAM_TOKEN,a.upstream.keys+1,1}));
    CHECK("binding-overrides-explicit-region-reference",geo_eval_node_count(a.graph)==4&&geo_eval_edge_count(a.graph)==2);
    CHECK("binding-callbacks-memoize-per-candidate",a.upstream.frame_calls==1&&a.upstream.region_calls==1&&a.upstream.binding_calls==2&&
        b.upstream.frame_calls==1&&b.upstream.region_calls==1&&b.upstream.binding_calls==2);
    CHECK("bindings-seal",geo_eval_seal(a.graph)&&geo_eval_seal(b.graph));
    GeoSourceValue again;CHECK("sealed-binding-read-still-uses-upstream-value",placement_value(&a,10,GEO_PLACEMENT_SOURCE_FRAME,&again)==GEO_SOURCE_OK&&same_frame(again.as.frame,frame(777))&&a.upstream.frame_calls==1);
    dispose(&a,false);CHECK("other-candidate-borrow-survives-destruction",is_region(br.as.regions,1500,true));dispose(&b,true);return 0;
}
static int binding_declines(void)
{
    Fixture f;CHECK("setup",setup(&f,906,0,true)==0);f.upstream.enabled=false;GeoSourceValue value;
    CHECK("declined-binding-uses-explicit-frame",placement_value(&f,10,GEO_PLACEMENT_SOURCE_FRAME,&value)==GEO_SOURCE_OK&&same_frame(value.as.frame,frame(10)));
    CHECK("declined-binding-keeps-explicit-region-edge",placement_value(&f,11,GEO_PLACEMENT_SOURCE_REGIONS,&value)==GEO_SOURCE_OK&&is_region(value.as.regions,0,true));
    GeoPlacementSourceKey key;GeoRegionSourceKey rkey;
    CHECK("declined-binding-records-core-region-edge",edge(f.graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,11,&key),geo_region_source_ref(REGION_TOKEN,29,&rkey)));
    CHECK("declined-binding-never-reads-upstream",f.upstream.frame_calls==0&&f.upstream.region_calls==0&&f.upstream.binding_calls==4);
    CHECK("declined-binding-probes-each-requested-source-kind",f.upstream.frame_binding_calls==1&&f.upstream.region_binding_calls==1&&f.upstream.definition_binding_calls==2);
    CHECK("declined-binding-keeps-exact-definition-closure",geo_eval_node_count(f.graph)==5&&geo_eval_edge_count(f.graph)==3&&
        definition_node(f.graph,10)&&definition_node(f.graph,11)&&
        definition_edge(f.graph,10,GEO_PLACEMENT_SOURCE_FRAME)&&definition_edge(f.graph,11,GEO_PLACEMENT_SOURCE_REGIONS));
    dispose(&f,true);return 0;
}
static int typed_failures(void)
{
    for(unsigned mode=0;mode<4;++mode){Fixture f;CHECK("setup",setup(&f,907+mode,0,true)==0);
        if(mode==0)f.upstream.frame_kind=GEO_SOURCE_QUANTITY;
        if(mode==1)f.upstream.region_kind=GEO_SOURCE_FRAME;
        if(mode==2)f.upstream.lie=true;
        if(mode==3)f.upstream.fail=true;
        GeoSourceValue out,saved;memset(&out,0xa5,sizeof out);memcpy(&saved,&out,sizeof out);
        GeoSourceStatus status=placement_value(&f,mode==1?11:10,mode==1?GEO_PLACEMENT_SOURCE_REGIONS:GEO_PLACEMENT_SOURCE_FRAME,&out);
        CHECK("typed-binding-error-rejected",status==(mode<2?GEO_SOURCE_INVALID:GEO_SOURCE_FAILED));
        CHECK("typed-binding-failure-keeps-output-bytes",!memcmp(&out,&saved,sizeof out));
        CHECK("typed-binding-failure-keeps-value-edge",geo_eval_node_count(f.graph)==2&&geo_eval_edge_count(f.graph)==1);
        CHECK("typed-binding-failure-is-memoized",placement_value(&f,mode==1?11:10,mode==1?GEO_PLACEMENT_SOURCE_REGIONS:GEO_PLACEMENT_SOURCE_FRAME,&out)==status&&
            f.upstream.binding_calls==1&&f.upstream.frame_calls+f.upstream.region_calls==1);
        dispose(&f,mode%2==0);
    }
    return 0;
}
static int missing_outputs(void)
{
    Fixture f;CHECK("setup",setup(&f,911,0,false)==0);GeoSourceValue out,saved;memset(&out,0x5a,sizeof out);memcpy(&saved,&out,sizeof out);
    GeoPlacementDefinition p=rectangle(14,14);p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=999;
    CHECK("stage-unresolved-reference",geo_placements_stage(f.placements,&p));
    CHECK("missing-placement-keeps-output",placement_value(&f,999,GEO_PLACEMENT_SOURCE_FRAME,&out)==GEO_SOURCE_MISSING&&!memcmp(&out,&saved,sizeof out));
    CHECK("missing-region-keeps-output",region_value(&f,999,&out)==GEO_SOURCE_MISSING&&!memcmp(&out,&saved,sizeof out));
    CHECK("unresolved-reference-keeps-output",placement_value(&f,14,GEO_PLACEMENT_SOURCE_REGIONS,&out)==GEO_SOURCE_FAILED&&!memcmp(&out,&saved,sizeof out));
    GeoSourceDescriptor desc,previous;memset(&desc,0x3c,sizeof desc);memcpy(&previous,&desc,sizeof desc);
    unsigned char bad[]={0,0,0,0,10};GeoSourceRef ref={PLACEMENT_TOKEN,bad,sizeof bad};
    CHECK("bad-kind-description-keeps-output",geo_eval_describe(f.graph,ref,&desc)==GEO_SOURCE_MISSING&&!memcmp(&desc,&previous,sizeof desc));
    CHECK("bad-kind-evaluation-keeps-output",geo_eval_source(f.graph,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&out)==GEO_SOURCE_MISSING&&!memcmp(&out,&saved,sizeof out));
    CHECK("failed-graph-can-seal",geo_eval_seal(f.graph));
    CHECK("sealed-unseen-source-keeps-output",placement_value(&f,10,GEO_PLACEMENT_SOURCE_FRAME,&out)==GEO_SOURCE_INVALID&&!memcmp(&out,&saved,sizeof out));
    dispose(&f,false);return 0;
}
static int candidate_isolation(void)
{
    Fixture a,b;CHECK("isolation-a",setup(&a,912,0,false)==0);CHECK("isolation-b",setup(&b,913,1000,false)==0);
    GeoSourceValue av,bv,af,bf;
    CHECK("isolation-same-key-different-regions",region_value(&a,29,&av)==GEO_SOURCE_OK&&region_value(&b,29,&bv)==GEO_SOURCE_OK&&
        is_region(av.as.regions,0,true)&&is_region(bv.as.regions,1000,true)&&av.as.regions.regions!=bv.as.regions.regions);
    CHECK("isolation-same-key-different-frames",placement_value(&a,10,GEO_PLACEMENT_SOURCE_FRAME,&af)==GEO_SOURCE_OK&&
        placement_value(&b,10,GEO_PLACEMENT_SOURCE_FRAME,&bf)==GEO_SOURCE_OK&&same_frame(af.as.frame,frame(10))&&same_frame(bf.as.frame,frame(1010)));
    const GeoSourceProvider *provider=geo_eval_provider_at(a.graph,1);GeoPlacementSourceKey key;
    GeoSourceRef ref=geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,10,&key);
    GeoSourceValue out,saved;memset(&out,0x7c,sizeof out);memcpy(&saved,&out,sizeof out);
    CHECK("source-handle-rejects-other-candidate-graph",!provider->evaluate(provider->candidate_state,b.graph,&ref,&out)&&!memcmp(&out,&saved,sizeof out));
    CHECK("candidate-identity-is-unchanged",geo_eval_candidate_id(a.graph)==912&&geo_eval_candidate_id(b.graph)==913&&geo_eval_base_revision(a.graph)==73);
    dispose(&a,true);CHECK("independent-region-borrow-still-readable",is_region(bv.as.regions,1000,true));dispose(&b,false);return 0;
}
static int destruction_orders(void)
{
    for(unsigned order=0;order<2;++order){Fixture f;CHECK("destroy-order-setup",setup(&f,914+order,0,false)==0);GeoSourceValue value;
        CHECK("destroy-order-has-borrowed-holes",placement_value(&f,11,GEO_PLACEMENT_SOURCE_REGIONS,&value)==GEO_SOURCE_OK&&is_region(value.as.regions,0,true));
        dispose(&f,order!=0); /* No evaluations or borrowed reads after disposal. */
    }
    geo_placement_sources_destroy(NULL);return 0;
}

typedef struct { GeoCoord number;unsigned calls; } Number;
static bool number_describe(void *state,const GeoSourceRef *source,GeoSourceDescriptor *out)
{(void)state;(void)source;memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;out->context.axis=-1;return true;}
static bool number_evaluate(void *state,GeoEvalContext *graph,const GeoSourceRef *source,GeoSourceValue *out)
{(void)graph;(void)source;Number *n=state;++n->calls;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){n->number,1,GEO_UNIT_LENGTH};return true;}
static GeoSourceProvider number_provider(GeoProviderToken token,const char *name,Number *state)
{return (GeoSourceProvider){token,name,"number-provider/1",state,number_describe,number_evaluate};}
static bool same_provider(const GeoSourceProvider *actual,GeoSourceProvider saved)
{
    return actual&&actual->token==saved.token&&actual->name_space==saved.name_space&&actual->implementation_fingerprint==saved.implementation_fingerprint&&
        actual->candidate_state==saved.candidate_state&&actual->describe==saved.describe&&actual->evaluate==saved.evaluate;
}
static int batch_invalid(void)
{
    for(unsigned mode=0;mode<6;++mode){GeoEvalContext *graph=geo_eval_create(920+mode,73);Number n[3]={{11,0},{22,0},{33,0}};
        GeoSourceProvider original=number_provider(1,"existing",n),providers[]={number_provider(2,"first",n+1),number_provider(3,"second",n+2)};
        CHECK("batch-existing-provider",graph&&geo_eval_register(graph,&original));GeoSourceProvider saved=*geo_eval_provider_at(graph,0);
        GeoSourceProvider good=providers[1];
        if(mode==0)providers[1].describe=NULL;else if(mode==1)providers[1].evaluate=NULL;
        else if(mode==2)providers[1].name_space=NULL;else if(mode==3)providers[1].name_space="";
        else if(mode==4)providers[1].implementation_fingerprint=NULL;else providers[1].implementation_fingerprint="";
        CHECK("batch-invalid-second-rejected",!geo_eval_register_many(graph,providers,2));
        CHECK("batch-invalid-second-is-atomic",geo_eval_provider_count(graph)==1&&same_provider(geo_eval_provider_at(graph,0),saved)&&
            geo_eval_node_count(graph)==0&&geo_eval_edge_count(graph)==0&&n[0].calls+n[1].calls+n[2].calls==0);
        providers[1]=good;CHECK("batch-retry-does-not-find-partial-first",geo_eval_register_many(graph,providers,2)&&geo_eval_provider_count(graph)==3);
        unsigned char key=1;GeoSourceValue out;CHECK("batch-existing-binding-survives-failure",geo_eval_source(graph,(GeoSourceRef){1,&key,1},GEO_DEPENDENCY_VALUE_REQUIRED,&out)==GEO_SOURCE_OK&&out.as.quantity.num==11&&n[0].calls==1);
        geo_eval_destroy(graph);
    }
    return 0;
}
static int batch_duplicate(void)
{
    for(unsigned mode=0;mode<4;++mode){GeoEvalContext *graph=geo_eval_create(930+mode,73);Number n[3]={{11,0},{22,0},{33,0}};
        GeoSourceProvider original=number_provider(1,"existing",n),providers[]={number_provider(2,"first",n+1),number_provider(3,"second",n+2)};
        CHECK("duplicate-existing-provider",graph&&geo_eval_register(graph,&original));GeoSourceProvider saved=*geo_eval_provider_at(graph,0),good=providers[1];
        if(mode==0)providers[1].token=2;else if(mode==1)providers[1].name_space="first";
        else if(mode==2)providers[1].token=1;else providers[1].name_space="existing";
        CHECK("batch-duplicate-second-rejected",!geo_eval_register_many(graph,providers,2));
        CHECK("batch-duplicate-second-is-atomic",geo_eval_provider_count(graph)==1&&same_provider(geo_eval_provider_at(graph,0),saved)&&geo_eval_node_count(graph)==0);
        providers[1]=good;CHECK("duplicate-batch-retry",geo_eval_register_many(graph,providers,2)&&geo_eval_provider_count(graph)==3);
        geo_eval_destroy(graph);
    }
    return 0;
}
static int batch_success_and_closed(void)
{
    for(unsigned mode=0;mode<4;++mode){GeoEvalContext *graph=geo_eval_create(940+mode,73);Number n[4]={{11,0},{22,0},{33,0},{44,0}};
        char first_name[]="first",fingerprint[]="owned-fingerprint/1";
        GeoSourceProvider providers[]={number_provider(1,first_name,n),number_provider(2,"second",n+1)};providers[0].implementation_fingerprint=fingerprint;
        CHECK("batch-admits-entire-family",graph&&geo_eval_register_many(graph,providers,2)&&geo_eval_provider_count(graph)==2);
        first_name[0]='X';fingerprint[0]='X';providers[0].candidate_state=n+3;
        CHECK("batch-copies-provider-metadata",!strcmp(geo_eval_provider_at(graph,0)->name_space,"first")&&
            !strcmp(geo_eval_provider_at(graph,0)->implementation_fingerprint,"owned-fingerprint/1")&&geo_eval_provider_at(graph,0)->candidate_state==n);
        unsigned char key=1;GeoSourceRef ref={1,&key,1};GeoSourceValue out;GeoSourceDescriptor d;
        if(mode==0)CHECK("graph-used-by-evaluation",geo_eval_source(graph,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&out)==GEO_SOURCE_OK&&out.as.quantity.num==11);
        else if(mode==1)CHECK("graph-used-by-description",geo_eval_describe(graph,ref,&d)==GEO_SOURCE_OK);
        else if(mode==2)CHECK("graph-used-by-dependency",geo_eval_depend(graph,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK);
        else CHECK("graph-sealed-before-use",geo_eval_seal(graph));
        GeoSourceProvider saved=*geo_eval_provider_at(graph,0),extra[]={number_provider(3,"third",n+2),number_provider(4,"fourth",n+3)};
        CHECK("batch-used-or-sealed-graph-rejected",!geo_eval_register_many(graph,extra,2));
        CHECK("closed-batch-keeps-existing-family",geo_eval_provider_count(graph)==2&&same_provider(geo_eval_provider_at(graph,0),saved));
        if(mode<3){CHECK("graph-rebuild-reset",geo_eval_reset(graph)&&geo_eval_provider_count(graph)==0);
            CHECK("fresh-rebuild-allows-new-complete-batch",geo_eval_register_many(graph,extra,2)&&geo_eval_provider_count(graph)==2&&geo_eval_candidate_id(graph)==940+mode);
            CHECK("rebuild-seal",geo_eval_seal(graph));
            CHECK("rebuilt-sealed-graph-rejects-original-family",!geo_eval_register_many(graph,providers,2)&&geo_eval_provider_count(graph)==2);}
        else CHECK("sealed-graph-cannot-reset",!geo_eval_reset(graph));
        geo_eval_destroy(graph);
    }
    return 0;
}
static int family_atomic(void)
{
    GeoPlacementStore *placements=geo_placements_create();GeoRegionStore *regions=geo_regions_create();GeoEvalContext *graph=geo_eval_create(950,73);
    Number n={9,0};GeoSourceProvider occupied=number_provider(PLACEMENT_TOKEN,"occupied",&n);
    CHECK("family-atomic-setup",placements&&regions&&graph&&geo_eval_register(graph,&occupied));GeoSourceProvider saved=*geo_eval_provider_at(graph,0);
    CHECK("family-second-provider-collision-rejects-all",geo_placement_sources_register(graph,placements,regions,PLACEMENT_TOKEN,REGION_TOKEN,NULL,NULL)==NULL);
    CHECK("family-collision-does-not-leak-core-region",geo_eval_provider_count(graph)==1&&same_provider(geo_eval_provider_at(graph,0),saved));
    GeoPlacementSources *sources=geo_placement_sources_register(graph,placements,regions,PLACEMENT_TOKEN+2,REGION_TOKEN,NULL,NULL);
    CHECK("family-retry-after-second-collision",sources&&geo_eval_provider_count(graph)==3&&geo_eval_provider_at(graph,1)->token==REGION_TOKEN);
    geo_placement_sources_destroy(sources);geo_eval_destroy(graph);geo_placements_destroy(placements);geo_regions_destroy(regions);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;int result;const char *name=argv[1];
    if(!strcmp(name,"keys"))result=key_contract();else if(!strcmp(name,"leaves"))result=explicit_leaves();
    else if(!strcmp(name,"region-edge"))result=region_reference();else if(!strcmp(name,"views"))result=borrowed_views();
    else if(!strcmp(name,"binding-values"))result=binding_values();else if(!strcmp(name,"binding-declines"))result=binding_declines();
    else if(!strcmp(name,"typed-failures"))result=typed_failures();else if(!strcmp(name,"missing-outputs"))result=missing_outputs();
    else if(!strcmp(name,"isolation"))result=candidate_isolation();else if(!strcmp(name,"destroy-orders"))result=destruction_orders();
    else if(!strcmp(name,"batch-invalid"))result=batch_invalid();else if(!strcmp(name,"batch-duplicate"))result=batch_duplicate();
    else if(!strcmp(name,"batch-closed"))result=batch_success_and_closed();else if(!strcmp(name,"family-atomic"))result=family_atomic();
    else return 2;if(!result)printf("PASS %s\n",name);return result;
}
