/* Public K-only client: source values, not raw region caches, choose vertices. */
#include "region_key_sources.h"
#include "placement_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KEY_TOKEN 31
#define REGION_TOKEN 32
#define PLACEMENT_TOKEN 33
#define CHECK(name,condition) do {if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}} while(0)

typedef struct {
    GeoEvalContext *graph;
    GeoRegionStore *store;
    GeoRegionKeySources *sources;
    GeoRegionDefinition raw,typed;
    GeoRegionKeys keys;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];
    GeoRegionView views[2];
    GeoSourceValueKind described_kind,returned_kind;
    size_t region_count,calls,descriptions;
    bool fail,cycle,null_regions;
} Fixture;

static GeoRegionDefinition rectangle(uint32_t id,GeoCoord shift,bool typed)
{
    GeoRegionDefinition r={0};r.id=id;r.outline.count=4;r.hole_count=1;r.holes[0].count=4;
    GeoCoord x=typed?101:10,y=typed?202:20,w=typed?800:80,h=typed?800:80;
    r.outline.v[0]=(GeoPoint2){x+shift,y+shift};r.outline.v[1]=(GeoPoint2){x+w+shift,y+shift};
    r.outline.v[2]=(GeoPoint2){x+w+shift,y+h+shift};r.outline.v[3]=(GeoPoint2){x+shift,y+h+shift};
    GeoCoord dx=typed?200:20,dy=typed?200:20,d=typed?200:20;
    r.holes[0].v[0]=(GeoPoint2){x+dx+shift,y+dy+shift};r.holes[0].v[1]=(GeoPoint2){x+dx+shift,y+dy+d+shift};
    r.holes[0].v[2]=(GeoPoint2){x+dx+d+shift,y+dy+d+shift};r.holes[0].v[3]=(GeoPoint2){x+dx+d+shift,y+dy+shift};
    return r;
}
static GeoRegionKeys ledger(uint32_t id)
{
    GeoRegionKeys k={0};k.boundary_id=id;k.next_key=100;k.loop_count=2;k.counts[0]=k.counts[1]=4;
    const uint32_t outer[]={11,7,33,2},hole[]={41,53,59,61};
    memcpy(k.keys[0],outer,sizeof outer);memcpy(k.keys[1],hole,sizeof hole);return k;
}
static void views(Fixture *f)
{
    for(size_t h=0;h<f->typed.hole_count&&h<GEO_REGION_MAX_HOLES;++h)f->holes[h]=(GeoLoop2View){f->typed.holes[h].v,f->typed.holes[h].count};
    f->views[0]=(GeoRegionView){{f->typed.outline.v,f->typed.outline.count},f->holes,f->typed.hole_count};f->views[1]=f->views[0];
}
static bool region_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    Fixture *f=opaque;uint32_t id;++f->descriptions;
    if(ref->provider!=REGION_TOKEN||!geo_region_source_decode(ref,&id)||id!=f->typed.id)return false;
    *out=(GeoSourceDescriptor){.kind=f->described_kind,.unit=GEO_UNIT_LENGTH,.context={false,0,-1}};return true;
}
static bool region_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=opaque;uint32_t id;++f->calls;
    if(graph!=f->graph||!geo_region_source_decode(ref,&id)||id!=f->typed.id||f->fail)return false;
    if(f->cycle){GeoRegionKeySourceKey key;GeoSourceValue value;
        return geo_eval_source(graph,geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,id,11,0,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK;}
    out->kind=f->returned_kind;
    if(out->kind==GEO_SOURCE_REGION_SET)out->as.regions=(GeoRegionSetView){f->null_regions?NULL:f->views,f->region_count};
    else out->as.quantity=(GeoQuantity){919,1,GEO_UNIT_LENGTH};
    return true;
}
static bool register_sources(Fixture *f)
{
    GeoSourceProvider p={REGION_TOKEN,"test.typed-region","region-key-witness/1",f,region_describe,region_evaluate};
    return geo_eval_register(f->graph,&p)&&(f->sources=geo_region_key_sources_register(f->graph,f->store,KEY_TOKEN,REGION_TOKEN))!=NULL;
}
static Fixture *fixture(uint32_t id,GeoCoord shift)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;
    f->graph=geo_eval_create(900+id,7);f->store=geo_regions_create();
    f->raw=rectangle(id,0,false);f->typed=rectangle(id,shift,true);f->keys=ledger(id);views(f);
    f->described_kind=f->returned_kind=GEO_SOURCE_REGION_SET;f->region_count=1;
    if(!f->graph||!f->store||!geo_regions_stage(f->store,&f->raw)||!geo_region_keys_put(f->store,&f->keys)||!register_sources(f)){
        geo_region_key_sources_destroy(f->sources);geo_eval_destroy(f->graph);geo_regions_destroy(f->store);free(f);return NULL;}
    return f;
}
static void dispose(Fixture *f,bool graph_first)
{
    if(!f)return;if(graph_first)geo_eval_destroy(f->graph);
    geo_region_key_sources_destroy(f->sources);if(!graph_first)geo_eval_destroy(f->graph);geo_regions_destroy(f->store);free(f);
}
static GeoSourceStatus value(Fixture *f,GeoRegionKeySourceKind kind,uint32_t vertex,uint32_t axis,GeoSourceValue *out)
{GeoRegionKeySourceKey key;return geo_eval_source(f->graph,geo_region_key_source_ref(KEY_TOKEN,kind,f->typed.id,vertex,axis,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out);}
static bool same_ref(GeoSourceRef a,GeoSourceRef b)
{return a.provider==b.provider&&a.key_size==b.key_size&&(!a.key_size||!memcmp(a.key,b.key,a.key_size));}
static size_t node(const GeoEvalContext *g,GeoSourceRef ref)
{
    for(size_t i=0;i<geo_eval_node_count(g);++i){GeoSourceNodeView n;if(geo_eval_node_at(g,i,&n)&&same_ref(n.source,ref))return i;}return SIZE_MAX;
}
static bool edge(const GeoEvalContext *g,GeoSourceRef consumer,GeoSourceRef source,GeoDependencyKind kind)
{
    size_t a=node(g,consumer),b=node(g,source);if(a==SIZE_MAX||b==SIZE_MAX)return false;
    for(size_t i=0;i<geo_eval_edge_count(g);++i){GeoSourceEdge e;if(geo_eval_edge_at(g,i,&e)&&e.consumer==a&&e.source==b&&e.kind==kind)return true;}return false;
}
static bool point(GeoPoint2 p,GeoCoord u,GeoCoord v){return p.u==u&&p.v==v;}

static int keys_case(void)
{
    static const unsigned char expected[]={0,0,0,2,1,35,69,103,137,171,205,239,0,0,0,1};
    GeoRegionKeySourceKey key;GeoSourceRef ref=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,UINT32_C(0x01234567),UINT32_C(0x89abcdef),1,&key);
    CHECK("source-key-fixed-big-endian-bytes",ref.key_size==16&&!memcmp(ref.key,expected,sizeof expected));
    GeoRegionKeySourceKind kind=0;uint32_t id=0,vertex=0,axis=0;
    CHECK("source-key-roundtrip",geo_region_key_source_decode(&ref,&kind,&id,&vertex,&axis)&&kind==GEO_REGION_KEY_SOURCE_COORDINATE&&id==UINT32_C(0x01234567)&&vertex==UINT32_C(0x89abcdef)&&axis==1);
    ref=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,UINT32_MAX,UINT32_MAX,0,&key);
    CHECK("source-key-uint32-max",geo_region_key_source_decode(&ref,&kind,&id,&vertex,&axis)&&id==UINT32_MAX&&vertex==UINT32_MAX&&!axis);
    ref=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_LEDGER,0,999,88,&key);
    CHECK("source-key-zero-id-and-ledger-reserved-fields",geo_region_key_source_decode(&ref,&kind,&id,&vertex,&axis)&&kind==GEO_REGION_KEY_SOURCE_LEDGER&&!id&&!vertex&&!axis);
    for(unsigned mode=0;mode<8;++mode){GeoRegionKeySourceKey bad;GeoSourceRef r=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,17,3,0,&bad);
        if(mode==0)r.key=NULL;if(mode==1)r.key_size=15;if(mode==2)r.key_size=17;
        if(mode==3)bad.bytes[3]=0;if(mode==4)bad.bytes[3]=3;if(mode==5)bad.bytes[15]=2;
        if(mode==6||mode==7){r=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_LEDGER,17,0,0,&bad);bad.bytes[mode==6?11:15]=1;}
        kind=(GeoRegionKeySourceKind)71;id=72;vertex=73;axis=74;
        CHECK("source-key-decode-failure-atomic",!geo_region_key_source_decode(&r,&kind,&id,&vertex,&axis)&&kind==71&&id==72&&vertex==73&&axis==74);
    }
    return 0;
}
static int codec_case(void)
{
    GeoRegionKeys k={0};k.boundary_id=UINT32_C(0x01020304);k.next_key=256;k.loop_count=2;k.counts[0]=3;k.counts[1]=2;
    k.keys[0][0]=11;k.keys[0][1]=7;k.keys[0][2]=33;k.keys[1][0]=41;k.keys[1][1]=53;
    static const unsigned char expected[]={1,2,3,4,0,0,1,0,0,0,0,2,0,0,0,3,0,0,0,11,0,0,0,7,0,0,0,33,0,0,0,2,0,0,0,41,0,0,0,53};
    unsigned char bytes[GEO_REGION_KEY_LEDGER_CONTENT_MAX];memset(bytes,0xa5,sizeof bytes);
    size_t size=geo_region_key_ledger_encode(&k,bytes,sizeof bytes);
    CHECK("ledger-fixed-canonical-bytes",size==sizeof expected&&!memcmp(bytes,expected,sizeof expected)&&bytes[size]==0xa5);
    GeoRegionKeys decoded;CHECK("ledger-codec-roundtrip",geo_region_key_ledger_decode(bytes,size,&decoded)&&geo_region_keys_same(&k,&decoded));
    GeoRegionKeys dirty=k;dirty.counts[2]=123;dirty.keys[0][31]=999;dirty.keys[8][31]=777;
    unsigned char clean[GEO_REGION_KEY_LEDGER_CONTENT_MAX];
    CHECK("ledger-excludes-inactive-storage",geo_region_key_ledger_encode(&dirty,clean,sizeof clean)==size&&!memcmp(clean,expected,size));
    GeoRegionKeys exhausted={0};exhausted.boundary_id=0;exhausted.loop_count=1;exhausted.counts[0]=1;exhausted.keys[0][0]=UINT32_MAX;
    size_t exhausted_size=geo_region_key_ledger_encode(&exhausted,clean,sizeof clean);
    CHECK("ledger-preserves-zero-id-and-exhausted-highwater",exhausted_size==20&&geo_region_key_ledger_decode(clean,exhausted_size,&decoded)&&!decoded.boundary_id&&!decoded.next_key&&decoded.keys[0][0]==UINT32_MAX);
    for(unsigned mode=0;mode<6;++mode){GeoRegionKeys bad=k;size_t capacity=sizeof clean;
        if(mode==0)capacity=size-1;if(mode==1)bad.loop_count=0;if(mode==2)bad.counts[0]=GEO_LOOP_MAX_VERTICES+1;
        if(mode==3)bad.keys[0][1]=bad.keys[0][0];if(mode==4)bad.keys[0][0]=0;if(mode==5)bad.next_key=53;
        memset(clean,0x5a,sizeof clean);unsigned char saved[sizeof clean];memcpy(saved,clean,sizeof saved);
        CHECK("ledger-encode-failure-atomic",geo_region_key_ledger_encode(&bad,clean,capacity)==0&&!memcmp(saved,clean,sizeof saved));
    }
    for(size_t length=0;length<size;++length){GeoRegionKeys out,saved;memset(&out,0x3c,sizeof out);saved=out;
        CHECK("ledger-truncated-decode-atomic",!geo_region_key_ledger_decode(expected,length,&out)&&!memcmp(&out,&saved,sizeof out));}
    for(unsigned mode=0;mode<7;++mode){unsigned char bad[sizeof expected+1];memcpy(bad,expected,sizeof expected);bad[sizeof expected]=0;size_t length=sizeof expected;
        if(mode==0)++length;if(mode==1)bad[11]=0;if(mode==2)bad[11]=GEO_REGION_MAX_HOLES+2;
        if(mode==3)bad[15]=GEO_LOOP_MAX_VERTICES+1;if(mode==4)bad[19]=0;if(mode==5)bad[23]=11;if(mode==6){bad[6]=0;bad[7]=53;}
        GeoRegionKeys out,saved;memset(&out,0x6d,sizeof out);saved=out;
        CHECK("ledger-invalid-and-trailing-decode-atomic",!geo_region_key_ledger_decode(bad,length,&out)&&!memcmp(&out,&saved,sizeof out));
    }
    return 0;
}
static int definitions_case(void)
{
    Fixture *f=fixture(0,0);CHECK("definitions-setup",f);
    GeoRegionKeys unused={0};unused.boundary_id=9;unused.next_key=27;unused.loop_count=1;
    GeoRegionKeys exhausted={0};exhausted.boundary_id=UINT32_MAX;exhausted.loop_count=1;exhausted.counts[0]=1;exhausted.keys[0][0]=UINT32_MAX;
    CHECK("definitions-orphan-ledgers-stage",geo_region_keys_put(f->store,&unused)&&geo_region_keys_put(f->store,&exhausted));
    CHECK("definitions-enumeration-success",geo_region_key_sources_definitions(f->sources));
    CHECK("unused-ledgers-never-request-geometry",f->calls==0&&f->descriptions==0&&geo_eval_node_count(f->graph)==3&&geo_eval_edge_count(f->graph)==0);
    for(size_t i=0;i<3;++i){GeoSourceNodeView n;GeoRegionKeys decoded;
        CHECK("definitions-canonical-content-and-scalar-metadata",geo_eval_node_at(f->graph,i,&n)&&n.state==GEO_NODE_VALID&&n.descriptor.kind==GEO_SOURCE_DEFINITION&&n.descriptor.unit==GEO_UNIT_SCALAR&&n.value&&
            !strcmp(n.value->as.definition.schema,"geometry.region-key-ledger/1")&&geo_region_key_ledger_decode(n.value->as.definition.content,n.value->as.definition.content_size,&decoded)&&
            geo_region_keys_same(&decoded,geo_region_keys_at(f->store,i)));
    }
    CHECK("definitions-store-untouched",geo_region_keys_same(&f->keys,geo_region_keys_find(f->store,0))&&geo_region_keys_same(&unused,geo_region_keys_find(f->store,9))&&
        geo_region_keys_same(&exhausted,geo_region_keys_find(f->store,UINT32_MAX))&&geo_regions_count(f->store)==1&&!memcmp(&f->raw,geo_regions_find(f->store,0),sizeof f->raw));
    CHECK("definitions-sealed-memo",geo_eval_seal(f->graph)&&geo_region_key_sources_definitions(f->sources)&&f->calls==0&&geo_eval_node_count(f->graph)==3);
    dispose(f,true);return 0;
}
static int typed_case(void)
{
    Fixture *f=fixture(0,0);CHECK("typed-setup",f);GeoPoint2 p;
    CHECK("coordinate-consumes-typed-region-value",geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,101,202));
    CHECK("coordinate-hole-key-selects-returned-loop",geo_region_key_sources_vertex(f->sources,0,41,&p)&&point(p,301,402));
    dispose(f,false);
    f=fixture(0,0);CHECK("ledger-value-setup",f);GeoSourceValue definition;
    CHECK("ledger-value-materialized",value(f,GEO_REGION_KEY_SOURCE_LEDGER,0,0,&definition)==GEO_SOURCE_OK);
    const void *borrowed=definition.as.definition.content;size_t size=definition.as.definition.content_size;unsigned char saved[GEO_REGION_KEY_LEDGER_CONTENT_MAX];memcpy(saved,borrowed,size);
    GeoRegionKeys changed=f->keys;changed.keys[0][0]=7;changed.keys[0][1]=11;changed.next_key=999;
    CHECK("ledger-raw-cache-divergence-staged",geo_region_keys_put(f->store,&changed));
    CHECK("coordinate-consumes-canonical-ledger-value",geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,101,202));
    CHECK("ledger-borrowed-content-stays-stable",!memcmp(borrowed,saved,size)&&value(f,GEO_REGION_KEY_SOURCE_LEDGER,0,0,&definition)==GEO_SOURCE_OK&&definition.as.definition.content==borrowed);
    dispose(f,true);
    f=fixture(0,0);CHECK("existing-policy-setup",f);f->typed.outline.v[1]=f->typed.outline.v[0];GeoPoint2 expected;
    CHECK("coordinate-keeps-existing-key-validity-policy",geo_region_vertex_by_key(&f->typed,&f->keys,7,&expected)&&geo_region_key_sources_vertex(f->sources,0,7,&p)&&point(p,expected.u,expected.v));
    dispose(f,false);
    f=fixture(UINT32_MAX,0);CHECK("exhausted-coordinate-setup",f);f->keys.next_key=0;f->keys.keys[0][0]=UINT32_MAX;
    CHECK("coordinate-max-key-and-region-id",geo_region_keys_put(f->store,&f->keys)&&geo_region_key_sources_vertex(f->sources,UINT32_MAX,UINT32_MAX,&p)&&point(p,101,202));
    dispose(f,true);return 0;
}
static int graph_case(void)
{
    Fixture *f=fixture(0,0),*other=fixture(0,10000);CHECK("graph-setup",f&&other);GeoPoint2 p;
    CHECK("graph-vertex-value",geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,101,202));
    GeoRegionKeySourceKey u,v,k;GeoRegionSourceKey r;
    GeoSourceRef ur=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,0,11,0,&u),vr=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,0,11,1,&v);
    GeoSourceRef kr=geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_LEDGER,0,0,0,&k),rr=geo_region_source_ref(REGION_TOKEN,0,&r);
    CHECK("coordinate-ledger-definition-edge",edge(f->graph,ur,kr,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&edge(f->graph,vr,kr,GEO_DEPENDENCY_DEFINITION_REQUIRED));
    CHECK("coordinate-region-value-edge",edge(f->graph,ur,rr,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f->graph,vr,rr,GEO_DEPENDENCY_VALUE_REQUIRED));
    CHECK("graph-exact-shared-dependencies",geo_eval_node_count(f->graph)==4&&geo_eval_edge_count(f->graph)==4&&f->calls==1);
    GeoSourceNodeView n;CHECK("coordinate-quantity-metadata",geo_eval_node_at(f->graph,node(f->graph,ur),&n)&&n.descriptor.kind==GEO_SOURCE_QUANTITY&&n.descriptor.unit==GEO_UNIT_LENGTH&&n.value&&n.value->as.quantity.num==101&&n.value->as.quantity.den==1);
    CHECK("graph-sealed-memo",geo_eval_seal(f->graph)&&geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,101,202)&&f->calls==1&&geo_eval_node_count(f->graph)==4&&geo_eval_edge_count(f->graph)==4);
    CHECK("graph-same-identity-isolated-candidates",geo_region_key_sources_vertex(other->sources,0,11,&p)&&point(p,10101,10202));
    dispose(f,true);
    CHECK("graph-other-candidate-survives-destruction",geo_region_key_sources_vertex(other->sources,0,11,&p)&&point(p,10101,10202)&&other->calls==1);
    dispose(other,false);return 0;
}
static int errors_case(void)
{
    for(unsigned mode=0;mode<15;++mode){Fixture *f=fixture(0,0);CHECK("errors-setup",f);uint32_t key=11;
        if(mode==0)CHECK("errors-remove-ledger",geo_region_keys_remove(f->store,0));
        if(mode==1)key=999;if(mode==2)key=0;if(mode==3)f->views[0].outline.count=3;
        if(mode==4)f->region_count=2;if(mode==5)f->region_count=0;if(mode==6)f->null_regions=true;
        if(mode==7)f->views[0].holes=NULL;if(mode==8)f->views[0].outline.v=NULL;
        if(mode==9)f->views[0].outline.count=GEO_LOOP_MAX_VERTICES+1;if(mode==10)f->views[0].hole_count=GEO_REGION_MAX_HOLES+1;
        if(mode==11)f->described_kind=f->returned_kind=GEO_SOURCE_QUANTITY;if(mode==12)f->returned_kind=GEO_SOURCE_QUANTITY;
        if(mode==13)f->fail=true;if(mode==14)f->cycle=true;
        GeoSourceValue out,saved;memset(&out,0x6b,sizeof out);saved=out;
        CHECK("invalid-coordinate-preserves-value",value(f,GEO_REGION_KEY_SOURCE_COORDINATE,key,0,&out)!=GEO_SOURCE_OK&&!memcmp(&out,&saved,sizeof out));
        GeoPoint2 p={771,882};CHECK("invalid-vertex-preserves-point",!geo_region_key_sources_vertex(f->sources,0,key,&p)&&point(p,771,882));
        CHECK("invalid-coordinate-keeps-owned-geometry",!memcmp(&f->raw,geo_regions_find(f->store,0),sizeof f->raw));
        dispose(f,mode%2==0);
    }
    return 0;
}
static int atomic_case(void)
{
    Fixture *f=fixture(0,0);CHECK("atomic-setup",f);GeoSourceValue u;
    CHECK("atomic-first-axis-ready",value(f,GEO_REGION_KEY_SOURCE_COORDINATE,11,0,&u)==GEO_SOURCE_OK&&u.as.quantity.num==101&&geo_eval_seal(f->graph));
    size_t nodes=geo_eval_node_count(f->graph),edges=geo_eval_edge_count(f->graph);GeoPoint2 p={771,882};
    CHECK("vertex-second-axis-failure-is-atomic",!geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,771,882));
    CHECK("sealed-missing-coordinate-does-not-evaluate",f->calls==1&&geo_eval_node_count(f->graph)==nodes&&geo_eval_edge_count(f->graph)==edges);
    CHECK("sealed-new-identity-does-not-return-old-point",!geo_region_key_sources_vertex(f->sources,0,999,&p)&&point(p,771,882));
    dispose(f,true);return 0;
}
static int reset_case(void)
{
    Fixture *f=fixture(0,0);CHECK("reset-setup",f);GeoPoint2 p;
    CHECK("reset-initial-value",geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,101,202));
    GeoRegionKeySourceKey old_key,new_key;geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,0,11,0,&old_key);
    CHECK("reset-clears-complete-generation",geo_eval_reset(f->graph)&&geo_eval_provider_count(f->graph)==0&&geo_eval_node_count(f->graph)==0&&geo_eval_edge_count(f->graph)==0);
    geo_region_key_sources_destroy(f->sources);f->sources=NULL;
    f->keys.next_key=500;f->typed=rectangle(0,5000,true);views(f);
    CHECK("reset-new-generation-registers",geo_region_keys_put(f->store,&f->keys)&&register_sources(f));
    geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,0,11,0,&new_key);
    CHECK("reset-stable-key-new-actual-value",!memcmp(old_key.bytes,new_key.bytes,sizeof old_key.bytes)&&geo_region_key_sources_vertex(f->sources,0,11,&p)&&point(p,5101,5202)&&f->calls==2);
    GeoSourceValue definition;GeoRegionKeys decoded;
    CHECK("reset-fresh-canonical-ledger",value(f,GEO_REGION_KEY_SOURCE_LEDGER,0,0,&definition)==GEO_SOURCE_OK&&geo_region_key_ledger_decode(definition.as.definition.content,definition.as.definition.content_size,&decoded)&&decoded.next_key==500);
    dispose(f,false);return 0;
}
static int registration_case(void)
{
    Fixture *f=fixture(0,0);CHECK("registration-setup",f);
    CHECK("registration-does-not-evaluate",geo_eval_provider_count(f->graph)==2&&geo_eval_node_count(f->graph)==0&&f->calls==0&&f->descriptions==0);
    CHECK("registration-invalid-token-atomic",!geo_region_key_sources_register(f->graph,f->store,0,REGION_TOKEN)&&!geo_region_key_sources_register(f->graph,f->store,REGION_TOKEN,REGION_TOKEN)&&geo_eval_provider_count(f->graph)==2);
    CHECK("registration-duplicate-atomic",!geo_region_key_sources_register(f->graph,f->store,KEY_TOKEN,REGION_TOKEN)&&!geo_region_key_sources_register(f->graph,f->store,99,REGION_TOKEN)&&geo_eval_provider_count(f->graph)==2&&geo_eval_node_count(f->graph)==0);
    GeoRegionKeys before=*geo_region_keys_find(f->store,0);GeoRegionKeySourceKey key;GeoSourceDescriptor d;
    CHECK("description-has-no-upstream-or-cache-writes",geo_eval_describe(f->graph,geo_region_key_source_ref(KEY_TOKEN,GEO_REGION_KEY_SOURCE_COORDINATE,0,11,0,&key),&d)==GEO_SOURCE_OK&&d.kind==GEO_SOURCE_QUANTITY&&d.unit==GEO_UNIT_LENGTH&&
        f->calls==0&&f->descriptions==0&&geo_eval_edge_count(f->graph)==0&&geo_region_keys_same(&before,geo_region_keys_find(f->store,0)));
    GeoSourceNodeView n;CHECK("description-keeps-node-unevaluated",geo_eval_node_at(f->graph,0,&n)&&n.state==GEO_NODE_NEW&&!n.value);
    dispose(f,true);
    f=fixture(0,0);CHECK("registration-used-graph-setup",f&&geo_eval_reset(f->graph));
    geo_region_key_sources_destroy(f->sources);f->sources=NULL;
    GeoSourceProvider region={REGION_TOKEN,"test.typed-region","region-key-witness/1",f,region_describe,region_evaluate};
    GeoRegionSourceKey region_key;GeoSourceValue actual;
    CHECK("registration-used-graph-evaluated",geo_eval_register(f->graph,&region)&&
        geo_eval_source(f->graph,geo_region_source_ref(REGION_TOKEN,0,&region_key),GEO_DEPENDENCY_VALUE_REQUIRED,&actual)==GEO_SOURCE_OK);
    CHECK("registration-used-graph-atomic",!geo_region_key_sources_register(f->graph,f->store,KEY_TOKEN,REGION_TOKEN)&&geo_eval_provider_count(f->graph)==1&&geo_eval_node_count(f->graph)==1);
    dispose(f,true);return 0;
}
static int actual_region_case(void)
{
    GeoRegionStore *store=geo_regions_create();GeoPlacementStore *placements=geo_placements_create();GeoEvalContext *graph=geo_eval_create(501,0);
    CHECK("actual-region-setup",store&&placements&&graph);GeoRegionDefinition r=rectangle(0,0,false);GeoRegionKeys keys=ledger(0);
    CHECK("actual-region-stage",geo_regions_stage(store,&r)&&geo_region_keys_put(store,&keys));
    GeoPlacementSources *regions=geo_placement_sources_register(graph,placements,store,PLACEMENT_TOKEN,REGION_TOKEN,NULL,NULL);
    GeoRegionKeySources *source=geo_region_key_sources_register(graph,store,KEY_TOKEN,REGION_TOKEN);
    CHECK("actual-region-register",regions&&source);GeoPoint2 p,expected;
    CHECK("actual-region-provider-agrees-with-original-key-policy",geo_region_vertex_by_key(&r,&keys,53,&expected)&&geo_region_key_sources_vertex(source,0,53,&p)&&point(p,expected.u,expected.v));
    CHECK("actual-region-null-output-check",geo_region_key_sources_vertex(source,0,53,NULL));
    geo_eval_destroy(graph);geo_region_key_sources_destroy(source);geo_placement_sources_destroy(regions);geo_placements_destroy(placements);geo_regions_destroy(store);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"keys"))return keys_case();if(!strcmp(argv[1],"codec"))return codec_case();
    if(!strcmp(argv[1],"definitions"))return definitions_case();if(!strcmp(argv[1],"typed"))return typed_case();
    if(!strcmp(argv[1],"graph"))return graph_case();if(!strcmp(argv[1],"errors"))return errors_case();
    if(!strcmp(argv[1],"atomic"))return atomic_case();if(!strcmp(argv[1],"reset"))return reset_case();
    if(!strcmp(argv[1],"registration"))return registration_case();if(!strcmp(argv[1],"actual-region"))return actual_region_case();
    return 2;
}
