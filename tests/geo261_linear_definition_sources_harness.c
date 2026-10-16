/* Public K-only witness. Fixed wire bytes are independent of the encoder.
 * No term provider, placement or geometric result is needed to retain a definition. */
#include "linear_definition_sources.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TOKEN 71
#define TERM_TOKEN 99
#define CHECK(name,condition) do {if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}} while(0)

static const unsigned char datum_bytes[]={
    1,2,3,4,2, 0,0,0,1,0, 0,0,0,2,
    255,255,255,255,255,255,255,250, 0,0,0,0,0,0,0,4,
    0x11,0x22,0x33,0x44, 0x55,0x66,0x77,0x88, 0x99,0xaa,0xbb,0xcc, 0,0,0,3, 'a','/',0xfe,
    1,2,3,4,5,6,7,8, 0,0x11,0x22,0x33,0x44,0x55,0x66,0x77,
    0,0,0,7, 0,0,0,0, 255,255,255,255, 0,0,0,4, 'b',':','[',']'
};
static GeoLinearExpression expression(int64_t numerator,int64_t denominator,bool complete)
{
    GeoLinearExpression e;geo_linear_begin(&e,GEO_LINEAR_FLOOR_FINAL);
    (void)geo_linear_append(&e,numerator,denominator,(GeoLinearSource){TERM_TOKEN,5,8,"opaque:/[]"});
    geo_linear_finish(&e,complete);return e;
}
static GeoDatum wire_datum(void)
{
    GeoDatum d={0};d.id=0x01020304;d.axis=2;d.position=7654321;
    geo_linear_begin(&d.expression,GEO_LINEAR_EXACT_INTEGER_FINAL);
    (void)geo_linear_append(&d.expression,-6,4,(GeoLinearSource){0x11223344,0x55667788,0x99aabbcc,"a/\xfe"});
    (void)geo_linear_append(&d.expression,INT64_C(0x0102030405060708),INT64_C(0x0011223344556677),
        (GeoLinearSource){7,0,UINT32_MAX,"b:[]"});
    geo_linear_finish(&d.expression,false);return d;
}
static bool same_expression(const GeoLinearExpression *a,const GeoLinearExpression *b)
{
    if(a->mode!=b->mode||a->complete!=b->complete||a->count!=b->count)return false;
    for(size_t i=0;i<a->count;++i){const GeoLinearTerm *x=&a->terms[i],*y=&b->terms[i];
        if(x->numerator!=y->numerator||x->denominator!=y->denominator||x->provider!=y->provider||x->id!=y->id||x->field!=y->field||
           strcmp(a->keys+x->key_offset,b->keys+y->key_offset))return false;}
    return true;
}
static bool source_equal(GeoSourceRef a,GeoSourceRef b)
{return a.provider==b.provider&&a.key_size==b.key_size&&(!a.key_size||!memcmp(a.key,b.key,a.key_size));}
static size_t node_index(GeoEvalContext *graph,GeoSourceRef ref)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(graph,i,&node)&&source_equal(node.source,ref))return i;}
    return SIZE_MAX;
}
static bool definition_edge(GeoEvalContext *graph,uint32_t guide,uint32_t datum)
{
    GeoLinearDefinitionKey g,d;
    size_t from=node_index(graph,geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_GUIDE,guide,&g));
    size_t to=node_index(graph,geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,datum,&d));
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge edge;
        if(geo_eval_edge_at(graph,i,&edge)&&edge.consumer==from&&edge.source==to&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED)return true;}
    return false;
}
typedef struct {GeoQuantity value;size_t calls;bool fail;GeoLinearSource last;} Resolver;
static bool resolve(void *state,const GeoLinearSource *source,GeoQuantity *out)
{
    Resolver *r=state;++r->calls;r->last=*source;if(r->fail)return false;*out=r->value;return true;
}
typedef struct {
    GeoEvalContext *graph;GeoDatumStore *datums;GeoGuideStore *guides;GeoLinearDefinitionSources *sources;
    size_t poison_descriptions,poison_values;
} Fixture;
static bool poison_describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{Fixture *f=state;(void)ref;(void)out;++f->poison_descriptions;return false;}
static bool poison_evaluate(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{Fixture *f=state;(void)graph;(void)ref;(void)out;++f->poison_values;return false;}
static bool register_sources(Fixture *f)
{
    GeoSourceProvider poison={TERM_TOKEN,"test.unused-term","linear-definitions/1",f,poison_describe,poison_evaluate};
    return geo_eval_register(f->graph,&poison)&&(f->sources=geo_linear_definition_sources_register(f->graph,f->datums,f->guides,TOKEN))!=NULL;
}
static void dispose(Fixture *f,bool graph_first)
{
    if(!f)return;
    if(graph_first){geo_eval_destroy(f->graph);geo_linear_definition_sources_destroy(f->sources);}
    else{geo_linear_definition_sources_destroy(f->sources);geo_eval_destroy(f->graph);}
    geo_datums_destroy(f->datums);geo_guides_destroy(f->guides);free(f);
}
static Fixture *fixture(int64_t coefficient,bool complete)
{
    Fixture *f=calloc(1,sizeof *f);if(!f)return NULL;
    f->graph=geo_eval_create((uint64_t)(1000+coefficient),17);f->datums=geo_datums_create();f->guides=geo_guides_create();
    GeoLinearExpression e=expression(coefficient,1,complete);
    GeoGuide local={0};local.id=10;local.placement_id=777;local.source=GEO_GUIDE_LOCAL;local.direction=GEO_GUIDE_ALONG_U;
    local.expression=expression(coefficient+1,1,complete);local.offset=222;local.resolved=true;
    GeoGuide shared={0};shared.id=11;shared.placement_id=888;shared.source=GEO_GUIDE_DATUM;shared.datum_id=0;
    shared.direction=GEO_GUIDE_ALONG_V;shared.offset=333;shared.resolved=true;
    if(!f->graph||!f->datums||!f->guides||!geo_datums_put(f->datums,0,1,&e)||!geo_guides_put(f->guides,&local)||!geo_guides_put(f->guides,&shared)||!register_sources(f)){
        dispose(f,true);return NULL;}
    return f;
}
static GeoSourceStatus get_value(Fixture *f,GeoLinearDefinitionKind kind,uint32_t id,GeoSourceValue *out)
{GeoLinearDefinitionKey key;return geo_eval_source(f->graph,geo_linear_definition_source_ref(TOKEN,kind,id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,out);}

static int keys_case(void)
{
    GeoLinearDefinitionKey key;const unsigned char expected[]={2,0x10,0x20,0x30,0x40};
    GeoSourceRef ref=geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_GUIDE,0x10203040,&key);
    CHECK("key-fixed-big-endian",ref.provider==TOKEN&&ref.key_size==5&&!memcmp(ref.key,expected,5));
    GeoLinearDefinitionKind kind;uint32_t id;
    CHECK("key-zero-and-maximum-identities",geo_linear_definition_source_decode(&ref,&kind,&id)&&kind==GEO_LINEAR_DEFINITION_GUIDE&&id==0x10203040&&
        (ref=geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,0,&key)).key_size==5&&geo_linear_definition_source_decode(&ref,&kind,&id)&&id==0&&kind==GEO_LINEAR_DEFINITION_DATUM);
    ref=geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,UINT32_MAX,&key);
    CHECK("key-maximum-decodes",geo_linear_definition_source_decode(&ref,&kind,&id)&&id==UINT32_MAX);
    for(size_t size=0;size<=6;++size)if(size!=5){GeoSourceRef bad=ref;bad.key_size=size;kind=GEO_LINEAR_DEFINITION_GUIDE;id=123;
        CHECK("key-invalid-size-atomic",!geo_linear_definition_source_decode(&bad,&kind,&id)&&kind==GEO_LINEAR_DEFINITION_GUIDE&&id==123);}
    key.bytes[0]=3;kind=GEO_LINEAR_DEFINITION_DATUM;id=987;
    CHECK("key-invalid-kind-atomic",!geo_linear_definition_source_decode(&ref,&kind,&id)&&kind==GEO_LINEAR_DEFINITION_DATUM&&id==987);
    memset(&key,0x59,sizeof key);GeoLinearDefinitionKey saved=key;
    ref=geo_linear_definition_source_ref(TOKEN,(GeoLinearDefinitionKind)0,8,&key);
    CHECK("key-invalid-encode-atomic",!ref.key&&!ref.key_size&&!memcmp(&key,&saved,sizeof key)&&!geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,0,NULL).key);
    return 0;
}
static int codec_case(void)
{
    GeoDatum datum=wire_datum(),decoded;unsigned char out[GEO_LINEAR_DEFINITION_CONTENT_MAX],again[GEO_LINEAR_DEFINITION_CONTENT_MAX];
    size_t size=geo_datum_definition_encode(&datum,out);
    CHECK("datum-fixed-canonical-vector",size==sizeof datum_bytes&&!memcmp(out,datum_bytes,size));
    CHECK("datum-roundtrip-authored-fields",geo_datum_definition_decode(datum_bytes,sizeof datum_bytes,&decoded)&&decoded.id==datum.id&&decoded.axis==2&&decoded.position==0&&same_expression(&decoded.expression,&datum.expression));
    datum.position=-999;datum.expression.terms[12].numerator=123;datum.expression.keys[400]='x';
    CHECK("datum-cache-and-inactive-storage-excluded",geo_datum_definition_encode(&datum,again)==size&&!memcmp(out,again,size));
    GeoGuide local={0},guide;local.id=0x0a0b0c0d;local.placement_id=0x10203040;local.source=GEO_GUIDE_LOCAL;
    local.direction=GEO_GUIDE_ALONG_V;local.expression=datum.expression;local.offset=-77;local.resolved=true;local.datum_id=999;
    const unsigned char local_header[]={10,11,12,13,0x10,0x20,0x30,0x40,0,1};
    size=geo_guide_definition_encode(&local,out);
    CHECK("local-guide-fixed-canonical-vector",size==sizeof local_header+sizeof datum_bytes-5&&!memcmp(out,local_header,sizeof local_header)&&!memcmp(out+sizeof local_header,datum_bytes+5,sizeof datum_bytes-5));
    CHECK("local-guide-authored-roundtrip",geo_guide_definition_decode(out,size,&guide)&&guide.id==local.id&&guide.placement_id==local.placement_id&&guide.source==GEO_GUIDE_LOCAL&&guide.direction==GEO_GUIDE_ALONG_V&&guide.offset==0&&!guide.resolved&&!guide.datum_id&&same_expression(&guide.expression,&local.expression));
    local.offset=888;local.resolved=false;local.datum_id=12345;
    CHECK("local-guide-caches-excluded",geo_guide_definition_encode(&local,again)==size&&!memcmp(out,again,size));
    const unsigned char shared_bytes[]={10,11,12,13,0x10,0x20,0x30,0x40,1,0xde,0xad,0xbe,0xef};
    local.source=GEO_GUIDE_DATUM;local.datum_id=0xdeadbeef;local.direction=(GeoGuideDirection)99;memset(&local.expression,0x6b,sizeof local.expression);
    size=geo_guide_definition_encode(&local,out);
    CHECK("datum-guide-only-authored-reference",size==sizeof shared_bytes&&!memcmp(out,shared_bytes,size)&&geo_guide_definition_decode(out,size,&guide)&&guide.datum_id==0xdeadbeef&&guide.direction==0&&guide.offset==0&&!guide.resolved&&guide.expression.count==0);
    datum=wire_datum();datum.expression.mode=(GeoLinearMode)-9;
    size=geo_datum_definition_encode(&datum,out);
    CHECK("invalid-mode-retained-as-authored-definition",size&&geo_datum_definition_decode(out,size,&decoded)&&decoded.expression.mode==(GeoLinearMode)-9&&!decoded.expression.complete);
    datum.expression=expression(1,1,false);datum.expression.count=0;datum.expression.key_bytes=0;
    size=geo_datum_definition_encode(&datum,out);
    CHECK("empty-incomplete-definition-retained",size&&geo_datum_definition_decode(out,size,&decoded)&&decoded.expression.count==0&&!decoded.expression.complete);
    return 0;
}
static bool rejects_datum(const unsigned char *bytes,size_t size)
{GeoDatum out,saved;memset(&out,0x5d,sizeof out);memcpy(&saved,&out,sizeof out);return !geo_datum_definition_decode(bytes,size,&out)&&!memcmp(&out,&saved,sizeof out);}
static bool rejects_guide(const unsigned char *bytes,size_t size)
{GeoGuide out,saved;memset(&out,0x6d,sizeof out);memcpy(&saved,&out,sizeof out);return !geo_guide_definition_decode(bytes,size,&out)&&!memcmp(&out,&saved,sizeof out);}
static int rejection_case(void)
{
    for(size_t n=0;n<sizeof datum_bytes;++n)CHECK("datum-truncation-atomic",rejects_datum(datum_bytes,n));
    unsigned char bad[GEO_LINEAR_DEFINITION_CONTENT_MAX+1];
    for(unsigned mode=0;mode<10;++mode){memcpy(bad,datum_bytes,sizeof datum_bytes);size_t size=sizeof datum_bytes;
        if(mode==0)bad[size++]=0;if(mode==1)bad[4]=3;if(mode==2)bad[9]=2;if(mode==3)bad[13]=65;
        if(mode==4){memset(bad+14,0,8);bad[14]=128;}if(mode==5)memset(bad+22,0,8);
        if(mode==6)memset(bad+30,0,4);if(mode==7)memset(bad+42,255,4);
        if(mode==8)bad[46]=0;if(mode==9){memset(bad+22,255,8);}
        CHECK("invalid-datum-decode-atomic",rejects_datum(bad,size));}
    memcpy(bad,datum_bytes,14);size_t at=14;
    for(unsigned i=0;i<2;++i){memcpy(bad+at,datum_bytes+14,32);bad[at+28]=bad[at+29]=0;bad[at+30]=3;bad[at+31]=32;at+=32;memset(bad+at,'q',800);at+=800;}
    CHECK("aggregate-key-capacity-decode-atomic",rejects_datum(bad,at));
    CHECK("oversize-and-null-decode-atomic",rejects_datum(bad,sizeof bad)&&rejects_datum(NULL,0)&&rejects_guide(NULL,0));
    GeoDatum d=wire_datum();unsigned char out[GEO_LINEAR_DEFINITION_CONTENT_MAX],saved[GEO_LINEAR_DEFINITION_CONTENT_MAX];
    for(unsigned mode=0;mode<8;++mode){d=wire_datum();memset(out,0x69,sizeof out);memcpy(saved,out,sizeof out);
        if(mode==0)d.axis=3;if(mode==1)d.expression.count=GEO_LINEAR_MAX_TERMS+1;if(mode==2)d.expression.key_bytes=GEO_LINEAR_KEY_BYTES+1;
        if(mode==3)d.expression.terms[0].numerator=INT64_MIN;if(mode==4)d.expression.terms[0].denominator=0;
        if(mode==5)d.expression.terms[0].provider=0;if(mode==6)d.expression.terms[0].key_offset=d.expression.key_bytes;
        if(mode==7)memset(d.expression.keys,'q',d.expression.key_bytes);
        CHECK("invalid-encode-atomic",geo_datum_definition_encode(&d,out)==0&&!memcmp(out,saved,sizeof out));}
    GeoGuide g={0};g.id=8;g.placement_id=9;g.source=GEO_GUIDE_LOCAL;g.expression=wire_datum().expression;
    size_t size=geo_guide_definition_encode(&g,out);CHECK("guide-rejection-setup",size>10);
    for(size_t n=0;n<size;++n)CHECK("guide-truncation-atomic",rejects_guide(out,n));
    memcpy(bad,out,size);bad[size]=0;CHECK("guide-trailing-atomic",rejects_guide(bad,size+1));
    memcpy(bad,out,size);bad[8]=2;CHECK("guide-source-rejection-atomic",rejects_guide(bad,size));
    memcpy(bad,out,size);bad[9]=2;CHECK("guide-direction-rejection-atomic",rejects_guide(bad,size));
    return 0;
}
static int definitions_case(void)
{
    Fixture *f=fixture(2,false);CHECK("definitions-setup",f);GeoDatum before;GeoGuide local;
    memcpy(&before,geo_datums_find(f->datums,0),sizeof before);memcpy(&local,geo_guides_find(f->guides,10),sizeof local);
    GeoLinearDefinitionKey key;GeoSourceDescriptor descriptor;
    CHECK("describe-is-definition-only",geo_eval_describe(f->graph,geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,0,&key),&descriptor)==GEO_SOURCE_OK&&
        descriptor.kind==GEO_SOURCE_DEFINITION&&descriptor.unit==GEO_UNIT_SCALAR&&descriptor.context.axis==-1&&!descriptor.context.has_placement&&geo_eval_edge_count(f->graph)==0);
    GeoSourceNodeView node;CHECK("description-never-evaluates",geo_eval_node_at(f->graph,0,&node)&&node.state==GEO_NODE_NEW&&!node.value&&f->poison_descriptions==0&&f->poison_values==0);
    CHECK("all-unused-definitions-enumerated",geo_linear_definition_sources_complete(f->sources)&&geo_eval_node_count(f->graph)==3&&geo_eval_edge_count(f->graph)==1);
    CHECK("guide-datum-edge-is-definition-only",definition_edge(f->graph,11,0));
    for(size_t i=0;i<3;++i){CHECK("enumeration-never-requests-geometry",geo_eval_node_at(f->graph,i,&node)&&node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&f->poison_descriptions==0&&f->poison_values==0);}
    GeoDatum d;GeoGuide g;
    CHECK("unused-incomplete-prefix-is-preserved",geo_linear_definition_sources_datum(f->sources,0,&d)&&!d.expression.complete&&d.expression.count==1&&
        geo_linear_definition_sources_guide(f->sources,10,&g)&&!g.expression.complete&&g.expression.count==1&&g.placement_id==777);
    CHECK("definition-enumeration-preserves-stores",!memcmp(&before,geo_datums_find(f->datums,0),sizeof before)&&!memcmp(&local,geo_guides_find(f->guides,10),sizeof local));
    CHECK("definitions-readable-after-seal",geo_eval_seal(f->graph)&&geo_linear_definition_sources_complete(f->sources)&&f->poison_values==0);
    dispose(f,true);return 0;
}
static int typed_case(void)
{
    Fixture *f=fixture(2,true);CHECK("typed-setup",f);GeoSourceValue datum_value,guide_value;
    CHECK("typed-materialized",get_value(f,GEO_LINEAR_DEFINITION_DATUM,0,&datum_value)==GEO_SOURCE_OK&&get_value(f,GEO_LINEAR_DEFINITION_GUIDE,10,&guide_value)==GEO_SOURCE_OK);
    CHECK("typed-canonical-schemas",!strcmp(datum_value.as.definition.schema,"geometry.datum-definition/1")&&!strcmp(guide_value.as.definition.schema,"geometry.guide-definition/1"));
    unsigned char saved[GEO_LINEAR_DEFINITION_CONTENT_MAX];size_t size=datum_value.as.definition.content_size;memcpy(saved,datum_value.as.definition.content,size);
    /* Deliberate adversarial divergence: a raw store cannot replace the value
     * already returned by this graph. Normal candidate composition is immutable. */
    GeoLinearExpression different=expression(91,1,true);GeoGuide raw=*geo_guides_find(f->guides,10);raw.expression=expression(92,1,true);raw.offset=-999;
    CHECK("typed-raw-store-divergence",geo_datums_put(f->datums,0,1,&different)&&geo_guides_put(f->guides,&raw));
    GeoDatum d;GeoGuide g;
    CHECK("datum-accessor-reads-returned-definition",geo_linear_definition_sources_datum(f->sources,0,&d)&&d.expression.terms[0].numerator==2&&d.position==0);
    CHECK("guide-accessor-reads-returned-definition",geo_linear_definition_sources_guide(f->sources,10,&g)&&g.expression.terms[0].numerator==3&&g.offset==0&&!g.resolved);
    Resolver r={{10,1,GEO_UNIT_LENGTH},0,false,{0}};GeoFrame frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}};
    CHECK("returned-datum-drives-evaluation",geo_datums_evaluate_definition(f->datums,0,&d,resolve,&r).status==GEO_LINEAR_OK&&geo_datums_at(f->datums,0)->position==20);
    CHECK("returned-guide-drives-evaluation",geo_guides_evaluate_definition(f->guides,0,&g,&frame,NULL,resolve,&r).status==GEO_GUIDE_OK&&geo_guides_at(f->guides,0)->offset==30);
    CHECK("returned-values-stable-with-raw-cache-writes",!memcmp(saved,datum_value.as.definition.content,size)&&geo_datums_at(f->datums,0)->expression.terms[0].numerator==91&&geo_guides_at(f->guides,0)->expression.terms[0].numerator==92);
    GeoDatum sentinel,copy;memset(&sentinel,0x59,sizeof sentinel);memcpy(&copy,&sentinel,sizeof copy);
    CHECK("missing-definition-read-atomic",!geo_linear_definition_sources_datum(f->sources,999,&sentinel)&&!memcmp(&sentinel,&copy,sizeof copy));
    dispose(f,false);return 0;
}
static int lifecycle_case(void)
{
    Fixture *f=fixture(2,true),*other=fixture(8,true);CHECK("lifecycle-setup",f&&other);
    CHECK("registration-duplicate-namespace-is-atomic-across-tokens",geo_eval_provider_count(f->graph)==2&&!geo_linear_definition_sources_register(f->graph,f->datums,f->guides,TOKEN)&&
        !geo_linear_definition_sources_register(f->graph,f->datums,f->guides,0)&&!geo_linear_definition_sources_register(f->graph,f->datums,f->guides,72)&&geo_eval_provider_count(f->graph)==2&&geo_eval_node_count(f->graph)==0);
    GeoDatum a,b;CHECK("same-identity-candidate-isolation",geo_linear_definition_sources_datum(f->sources,0,&a)&&geo_linear_definition_sources_datum(other->sources,0,&b)&&
        a.expression.terms[0].numerator==2&&b.expression.terms[0].numerator==8&&geo_eval_candidate_id(f->graph)!=geo_eval_candidate_id(other->graph));
    GeoLinearDefinitionKey old_key,new_key;geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,0,&old_key);
    CHECK("reset-clears-generation",geo_eval_reset(f->graph)&&geo_eval_provider_count(f->graph)==0&&geo_eval_node_count(f->graph)==0&&geo_eval_edge_count(f->graph)==0);
    geo_linear_definition_sources_destroy(f->sources);f->sources=NULL;GeoLinearExpression e=expression(17,1,true);
    CHECK("reset-reregisters",geo_datums_put(f->datums,0,1,&e)&&register_sources(f));
    geo_linear_definition_source_ref(TOKEN,GEO_LINEAR_DEFINITION_DATUM,0,&new_key);
    CHECK("reset-same-key-new-definition",!memcmp(old_key.bytes,new_key.bytes,5)&&geo_linear_definition_sources_datum(f->sources,0,&a)&&a.expression.terms[0].numerator==17);
    CHECK("seal-keeps-evaluated-definition",geo_eval_seal(f->graph)&&geo_linear_definition_sources_datum(f->sources,0,&a)&&a.expression.terms[0].numerator==17&&!geo_eval_reset(f->graph));
    GeoGuide out,saved;memset(&out,0x6c,sizeof out);memcpy(&saved,&out,sizeof out);size_t count=geo_eval_node_count(f->graph);
    CHECK("sealed-unread-definition-is-atomic",!geo_linear_definition_sources_guide(f->sources,10,&out)&&!memcmp(&out,&saved,sizeof out)&&geo_eval_node_count(f->graph)==count);
    dispose(f,true);
    CHECK("other-candidate-survives-teardown",geo_linear_definition_sources_datum(other->sources,0,&b)&&b.expression.terms[0].numerator==8);
    dispose(other,false);geo_linear_definition_sources_destroy(NULL);return 0;
}
static int datum_case(void)
{
    GeoDatumStore *store=geo_datums_create();GeoLinearExpression raw=expression(99,1,true);CHECK("datum-eval-setup",store&&geo_datums_put(store,0,0,&raw));
    GeoDatum supplied=*geo_datums_at(store,0);supplied.expression=expression(-3,2,true);supplied.position=987654;
    Resolver r={{5,1,GEO_UNIT_LENGTH},0,false,{0}};GeoLinearResult result=geo_datums_evaluate_definition(store,0,&supplied,resolve,&r);
    CHECK("datum-evaluate-supplied-coefficients",result.status==GEO_LINEAR_OK&&result.value.num==-8&&geo_datums_at(store,0)->position==-8&&r.calls==1);
    CHECK("datum-keeps-authored-store-and-key",geo_datums_at(store,0)->expression.terms[0].numerator==99&&r.last.provider==TERM_TOKEN&&r.last.id==5&&r.last.field==8&&!strcmp(r.last.key,"opaque:/[]"));
    supplied.expression=expression(2,1,true);supplied.expression.mode=GEO_LINEAR_EXACT_INTEGER_FINAL;r.calls=0;r.value.num=7;
    CHECK("datum-supplied-exact-mode",geo_datums_evaluate_definition(store,0,&supplied,resolve,&r).status==GEO_LINEAR_OK&&geo_datums_at(store,0)->position==14&&r.calls==1);
    CHECK("datum-legacy-wrapper-still-uses-store",geo_datums_evaluate(store,0,resolve,&r).status==GEO_LINEAR_OK&&geo_datums_at(store,0)->position==693);
    geo_datums_destroy(store);return 0;
}
static int datum_errors_case(void)
{
    GeoDatumStore *store=geo_datums_create();GeoLinearExpression raw=expression(1,1,true);CHECK("datum-errors-setup",store&&geo_datums_put(store,0,0,&raw));
    Resolver r={{3,1,GEO_UNIT_LENGTH},0,false,{0}};GeoDatum definition=*geo_datums_at(store,0);
    CHECK("datum-errors-prior-cache",geo_datums_evaluate(store,0,resolve,&r).status==GEO_LINEAR_OK);
    r.value.num=GEO_COORD_LIMIT+1;GeoLinearResult result=geo_datums_evaluate_definition(store,0,&definition,resolve,&r);
    CHECK("datum-range-keeps-attempted-position",result.status==GEO_LINEAR_RANGE&&result.value.num==GEO_COORD_LIMIT+1&&geo_datums_at(store,0)->position==GEO_COORD_LIMIT+1);
    for(unsigned mode=0;mode<7;++mode){definition=*geo_datums_at(store,0);r.calls=0;r.fail=false;r.value=(GeoQuantity){3,1,GEO_UNIT_LENGTH};GeoLinearStatus expected=GEO_LINEAR_INVALID;
        if(mode==0){r.fail=true;expected=GEO_LINEAR_SOURCE_FAILED;}if(mode==1)definition.expression.complete=false;
        if(mode==2){definition.expression=expression(INT64_MAX,1,true);r.value.num=2;expected=GEO_LINEAR_ARITHMETIC;}
        if(mode==3){definition.expression=expression(1,2,true);definition.expression.mode=GEO_LINEAR_EXACT_INTEGER_FINAL;expected=GEO_LINEAR_NOT_INTEGER;}
        if(mode==4)definition.id=99;if(mode==5)definition.axis=3;if(mode==6)definition.expression.mode=(GeoLinearMode)-1;
        GeoDatum saved;memcpy(&saved,geo_datums_at(store,0),sizeof saved);result=geo_datums_evaluate_definition(store,0,&definition,resolve,&r);
        CHECK("datum-failures-retain-cache-and-definition",result.status==expected&&!memcmp(&saved,geo_datums_at(store,0),sizeof saved));
        CHECK("datum-valid-prefix-and-early-rejection-order",r.calls==(mode<4?1:0));}
    geo_datums_destroy(store);return 0;
}
static int guide_case(void)
{
    GeoGuideStore *store=geo_guides_create();GeoGuide raw={0};raw.id=10;raw.placement_id=4;raw.source=GEO_GUIDE_LOCAL;raw.direction=GEO_GUIDE_ALONG_U;raw.expression=expression(99,1,true);raw.offset=321;
    CHECK("guide-eval-setup",store&&geo_guides_put(store,&raw));GeoGuide definition=raw;definition.expression=expression(-3,2,true);definition.direction=GEO_GUIDE_ALONG_V;definition.offset=987;
    Resolver r={{5,1,GEO_UNIT_LENGTH},0,false,{0}};GeoFrame frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}};
    GeoGuideResult result=geo_guides_evaluate_definition(store,0,&definition,&frame,NULL,resolve,&r);
    CHECK("guide-evaluate-supplied-coefficients",result.status==GEO_GUIDE_OK&&geo_guides_at(store,0)->offset==-8&&geo_guides_at(store,0)->resolved&&r.calls==1);
    CHECK("guide-authored-fields-retained",geo_guides_at(store,0)->direction==GEO_GUIDE_ALONG_U&&geo_guides_at(store,0)->expression.terms[0].numerator==99&&geo_guides_at(store,0)->placement_id==4);
    CHECK("guide-legacy-wrapper-still-uses-store",geo_guides_evaluate(store,0,&frame,NULL,resolve,&r).status==GEO_GUIDE_OK&&geo_guides_at(store,0)->offset==495);
    raw.source=GEO_GUIDE_DATUM;raw.datum_id=7;raw.offset=444;raw.resolved=false;CHECK("guide-datum-stage",geo_guides_put(store,&raw));
    definition=raw;definition.datum_id=8;GeoDatum datum={0};datum.id=8;datum.axis=0;datum.position=20;frame.origin.x=3;r.calls=0;
    result=geo_guides_evaluate_definition(store,0,&definition,&frame,&datum,resolve,&r);
    CHECK("guide-evaluate-supplied-datum-reference",result.status==GEO_GUIDE_OK&&geo_guides_at(store,0)->offset==17&&geo_guides_at(store,0)->direction==GEO_GUIDE_ALONG_V&&geo_guides_at(store,0)->resolved&&geo_guides_at(store,0)->datum_id==7&&r.calls==0);
    geo_guides_destroy(store);return 0;
}
static int guide_errors_case(void)
{
    GeoGuideStore *store=geo_guides_create();GeoGuide raw={0};raw.id=10;raw.source=GEO_GUIDE_LOCAL;raw.expression=expression(1,1,true);raw.offset=321;raw.resolved=true;
    CHECK("guide-errors-setup",store&&geo_guides_put(store,&raw));GeoGuide definition=raw;GeoFrame frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}};Resolver r={{GEO_COORD_LIMIT+1,1,GEO_UNIT_LENGTH},0,false,{0}};
    GeoGuideResult result=geo_guides_evaluate_definition(store,0,&definition,&frame,NULL,resolve,&r);
    CHECK("local-range-does-not-publish-attempt",result.status==GEO_GUIDE_LINEAR_FAILED&&result.linear.status==GEO_LINEAR_RANGE&&result.linear.value.num==GEO_COORD_LIMIT+1&&geo_guides_at(store,0)->offset==321&&geo_guides_at(store,0)->resolved);
    for(unsigned mode=0;mode<2;++mode){definition=raw;r.calls=0;r.value.num=3;
        if(mode==0)definition.source=(GeoGuideSource)99;else definition.direction=(GeoGuideDirection)99;
        GeoGuide saved;memcpy(&saved,geo_guides_at(store,0),sizeof saved);
        result=geo_guides_evaluate_definition(store,0,&definition,&frame,NULL,resolve,&r);
        if(mode==0){CHECK("invalid-guide-source-precedes-resolution",result.status==GEO_GUIDE_INVALID&&r.calls==0&&!memcmp(&saved,geo_guides_at(store,0),sizeof saved));}
        else{CHECK("invalid-local-direction-precedes-resolution",result.status==GEO_GUIDE_INVALID&&r.calls==0&&!memcmp(&saved,geo_guides_at(store,0),sizeof saved));}}
    definition=raw;definition.source=GEO_GUIDE_DATUM;definition.datum_id=8;
    GeoDatum other={0};other.id=8;other.axis=0;other.position=20;
    GeoGuide saved_local;memcpy(&saved_local,geo_guides_at(store,0),sizeof saved_local);r.calls=0;
    result=geo_guides_evaluate_definition(store,0,&definition,&frame,&other,resolve,&r);
    CHECK("guide-source-kind-cannot-change-authored-storage",result.status==GEO_GUIDE_INVALID&&r.calls==0&&!memcmp(&saved_local,geo_guides_at(store,0),sizeof saved_local));
    for(unsigned mode=0;mode<5;++mode){definition=raw;r.calls=0;r.fail=false;r.value.num=3;const GeoFrame *provided=&frame;GeoGuideStatus expected=GEO_GUIDE_LINEAR_FAILED;
        if(mode==0){provided=NULL;expected=GEO_GUIDE_MISSING_FRAME;}if(mode==1)definition.expression.complete=false;if(mode==2)r.fail=true;
        if(mode==3){definition.expression=expression(1,2,true);definition.expression.mode=GEO_LINEAR_EXACT_INTEGER_FINAL;}
        if(mode==4){definition.id=99;expected=GEO_GUIDE_INVALID;}GeoGuide saved;memcpy(&saved,geo_guides_at(store,0),sizeof saved);
        result=geo_guides_evaluate_definition(store,0,&definition,provided,NULL,resolve,&r);
        CHECK("local-guide-failures-preserve-prior-state",result.status==expected&&!memcmp(&saved,geo_guides_at(store,0),sizeof saved)&&r.calls==((mode==0||mode==4)?0:1));}
    raw.source=GEO_GUIDE_DATUM;raw.datum_id=8;raw.direction=GEO_GUIDE_ALONG_U;raw.resolved=false;raw.offset=321;
    CHECK("guide-datum-errors-stage",geo_guides_put(store,&raw));definition=raw;GeoDatum datum={0};datum.id=8;datum.axis=0;datum.position=GEO_COORD_LIMIT;frame.origin.x=-GEO_COORD_LIMIT;
    result=geo_guides_evaluate_definition(store,0,&definition,&frame,&datum,resolve,&r);
    CHECK("datum-guide-range-publishes-partial-cache",result.status==GEO_GUIDE_DATUM_FAILED&&result.intersection==GEO_DATUM_INTERSECTION_RANGE&&geo_guides_at(store,0)->offset==2*GEO_COORD_LIMIT&&geo_guides_at(store,0)->direction==GEO_GUIDE_ALONG_V&&!geo_guides_at(store,0)->resolved);
    for(unsigned mode=0;mode<4;++mode){datum.id=8;datum.axis=2;datum.position=0;frame.origin=(GeoPoint3){0,0,0};const GeoDatum *provided=&datum;
        GeoGuideStatus expected=GEO_GUIDE_DATUM_FAILED;if(mode==0)datum.position=1;if(mode==1)datum.position=0;if(mode==2){provided=NULL;expected=GEO_GUIDE_MISSING_DATUM;}if(mode==3){datum.id=99;expected=GEO_GUIDE_MISSING_DATUM;}
        GeoGuide saved;memcpy(&saved,geo_guides_at(store,0),sizeof saved);result=geo_guides_evaluate_definition(store,0,&definition,&frame,provided,resolve,&r);
        CHECK("datum-guide-other-failures-atomic",result.status==expected&&!memcmp(&saved,geo_guides_at(store,0),sizeof saved));}
    geo_guides_destroy(store);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"keys"))return keys_case();if(!strcmp(argv[1],"codec"))return codec_case();
    if(!strcmp(argv[1],"rejection"))return rejection_case();if(!strcmp(argv[1],"definitions"))return definitions_case();
    if(!strcmp(argv[1],"typed"))return typed_case();if(!strcmp(argv[1],"lifecycle"))return lifecycle_case();
    if(!strcmp(argv[1],"datum"))return datum_case();if(!strcmp(argv[1],"datum-errors"))return datum_errors_case();
    if(!strcmp(argv[1],"guide"))return guide_case();if(!strcmp(argv[1],"guide-errors"))return guide_errors_case();
    return 2;
}
