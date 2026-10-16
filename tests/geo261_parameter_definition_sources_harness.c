/* Public K-only client. Fixed authored bytes and exact values precede parity.
 * Every negative control must return exactly one named ASSERT, never a crash. */
#include "parameter_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(test,label) do{if(!(test)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
#define VALUE_TOKEN 37
#define DEFINITION_TOKEN 38
typedef struct {GeoEvalContext *graph;GeoParameterSources *sources;} Binding;
static GeoParameterRef ref(uint32_t card,uint32_t field)
{return (GeoParameterRef){true,card,field};}
static bool quantity(GeoQuantity q,int64_t num,int64_t den,GeoQuantityUnit unit)
{return q.num==num&&q.den==den&&q.unit==unit;}
static bool same_ref(GeoParameterRef a,GeoParameterRef b)
{return a.set==b.set&&a.parameter_id==b.parameter_id&&a.field_id==b.field_id;}
static bool same_error(const GeoParameterError *a,const GeoParameterError *b)
{
    if(a->status!=b->status||a->exact!=b->exact||!same_ref(a->source,b->source)||
       !quantity(a->quantity,b->quantity.num,b->quantity.den,b->quantity.unit)||
       strcmp(a->detail,b->detail)||a->trace_count!=b->trace_count)return false;
    for(size_t i=0;i<a->trace_count;++i)if(!same_ref(a->trace[i],b->trace[i]))return false;
    return true;
}
static void literal(GeoParameterField *f,uint32_t card,uint32_t field,int type,int num,int den)
{
    memset(f,0,sizeof *f);f->parameter_id=card;f->id=field;f->type=type;
    snprintf(f->name,sizeof f->name,"field-%u",field);
    snprintf(f->expression,sizeof f->expression,"{\"op\":\"literal\",\"num\":\"%d\",\"den\":\"%d\",\"unit\":\"%s\"}",
        num,den,type==GEO_PARAMETER_DIMENSION?"mm":"1");
}
static void reference(GeoParameterField *f,uint32_t card,uint32_t field,uint32_t source_card,uint32_t source_field)
{
    literal(f,card,field,GEO_PARAMETER_DIMENSION,0,1);
    snprintf(f->expression,sizeof f->expression,"{\"op\":\"ref\",\"parameterId\":%u,\"fieldId\":%u}",source_card,source_field);
}
static bool put(GeoParameterStore *store,uint32_t id,GeoParameterField *fields,size_t count)
{
    GeoParameterCard card;GeoParameterError error;geo_parameters_begin_definition(store,id,&card);
    snprintf(card.name,sizeof card.name,"card-%u",id);card.count=count;
    for(size_t i=0;i<count;++i)if(!geo_parameters_accept_field(store,&card,fields,i,&error))return false;
    return geo_parameters_put(store,&card,fields,&error);
}
static bool bind(Binding *binding,GeoParameterStore *store,uint64_t candidate)
{
    binding->graph=geo_eval_create(candidate,73);if(!binding->graph)return false;
    binding->sources=geo_parameter_sources_register_with_definitions(binding->graph,store,VALUE_TOKEN,DEFINITION_TOKEN,
        "test.parameter.field","parameter-definition-test/1");return binding->sources!=NULL;
}
static void dispose(Binding *binding,bool graph_first)
{
    if(graph_first){geo_eval_destroy(binding->graph);geo_parameter_sources_destroy(binding->sources);}
    else{geo_parameter_sources_destroy(binding->sources);geo_eval_destroy(binding->graph);}
    memset(binding,0,sizeof *binding);
}
static bool definition(Binding *binding,GeoParameterDefinitionKind kind,uint32_t card,uint32_t field,GeoSourceValue *out)
{
    GeoParameterDefinitionKey key;return geo_eval_source(binding->graph,
        geo_parameter_definition_source_ref(DEFINITION_TOKEN,kind,card,field,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,out)==GEO_SOURCE_OK;
}
static size_t node(const GeoEvalContext *graph,bool authored,GeoParameterDefinitionKind kind,uint32_t card,uint32_t field)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;if(!geo_eval_node_at(graph,i,&n))continue;
        if(authored){GeoParameterDefinitionKind k;uint32_t c,f;
            if(n.source.provider==DEFINITION_TOKEN&&geo_parameter_definition_source_decode(&n.source,&k,&c,&f)&&k==kind&&c==card&&f==field)return i;
        }else if(n.source.provider==VALUE_TOKEN&&n.source.key_size==8){uint32_t ids[2];memcpy(ids,n.source.key,sizeof ids);
            if(ids[0]==card&&ids[1]==field)return i;}}
    return SIZE_MAX;
}
static bool edge(const GeoEvalContext *graph,size_t consumer,size_t source,GeoDependencyKind kind)
{
    if(consumer==SIZE_MAX||source==SIZE_MAX)return false;
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(graph,i,&e)&&e.consumer==consumer&&e.source==source&&e.kind==kind)return true;}
    return false;
}
static int keys_case(void)
{
    const unsigned char expected[]={0,0,0,2,1,2,3,4,0x89,0xab,0xcd,0xef};GeoParameterDefinitionKey key;
    GeoSourceRef source=geo_parameter_definition_source_ref(38,GEO_PARAMETER_DEFINITION_FIELD,0x01020304,0x89abcdef,&key);
    CHECK(source.provider==38&&source.key_size==12&&source.key==key.bytes&&!memcmp(key.bytes,expected,12),"definition-key-fixed-big-endian");
    GeoParameterDefinitionKind kind=GEO_PARAMETER_DEFINITION_CARD;uint32_t card=8,field=9;
    CHECK(geo_parameter_definition_source_decode(&source,&kind,&card,&field)&&kind==GEO_PARAMETER_DEFINITION_FIELD&&card==0x01020304&&field==0x89abcdef,"definition-key-roundtrip");
    source=geo_parameter_definition_source_ref(38,GEO_PARAMETER_DEFINITION_CARD,0,UINT32_MAX,&key);
    CHECK(geo_parameter_definition_source_decode(&source,&kind,&card,&field)&&kind==GEO_PARAMETER_DEFINITION_CARD&&!card&&!field,"card-key-zero-and-reserved-field");
    for(unsigned bad=0;bad<5;++bad){GeoSourceRef invalid=source;GeoParameterDefinitionKey changed=key;
        if(bad==0)invalid.key_size=11;else if(bad==1)invalid.key=NULL;
        else if(bad==2){changed.bytes[3]=0;invalid.key=changed.bytes;}
        else if(bad==3){changed.bytes[3]=3;invalid.key=changed.bytes;}
        else{changed.bytes[11]=1;invalid.key=changed.bytes;}
        kind=GEO_PARAMETER_DEFINITION_FIELD;card=123;field=456;
        CHECK(!geo_parameter_definition_source_decode(&invalid,&kind,&card,&field)&&kind==GEO_PARAMETER_DEFINITION_FIELD&&card==123&&field==456,"invalid-definition-key-decode-atomic");}
    source=geo_parameter_definition_source_ref(38,GEO_PARAMETER_DEFINITION_FIELD,UINT32_MAX,UINT32_MAX,&key);
    CHECK(geo_parameter_definition_source_decode(&source,&kind,&card,&field)&&card==UINT32_MAX&&field==UINT32_MAX,"definition-key-max-identities");
    return 0;
}
static int codec_case(void)
{
    GeoParameterCard card={0};card.id=0x01020304;card.next_field_id=0x11002233;strcpy(card.name,"C");card.count=2;card.fields[0]=0;card.fields[1]=0x01020304;
    const unsigned char card_bytes[]={1,2,3,4,0x11,0,0x22,0x33,0,0,0,1,'C',0,0,0,2,0,0,0,0,1,2,3,4};
    unsigned char a[GEO_PARAMETER_FIELD_CONTENT_MAX+1],b[sizeof a];memset(a,0xa5,sizeof a);
    size_t n=geo_parameter_card_definition_encode(&card,a,sizeof a);
    CHECK(n==sizeof card_bytes&&!memcmp(a,card_bytes,n),"card-fixed-authored-bytes");
    GeoParameterCard decoded;memset(&decoded,0x5a,sizeof decoded);
    CHECK(geo_parameter_card_definition_decode(a,n,&decoded)&&decoded.id==card.id&&decoded.next_field_id==card.next_field_id&&decoded.count==2&&!strcmp(decoded.name,"C")&&decoded.fields[0]==0&&decoded.fields[1]==0x01020304,"card-decodes-active-metadata");
    GeoParameterCard padding=card;memset(padding.name+2,0xfe,sizeof padding.name-2);padding.fields[15]=UINT32_MAX;
    CHECK(geo_parameter_card_definition_encode(&padding,b,sizeof b)==n&&!memcmp(a,b,n),"card-ignores-inactive-padding");
    for(unsigned bad=0;bad<8;++bad){memcpy(b,a,n);size_t size=n;
        if(bad==0)--size;else if(bad==1)b[size++]=0;else if(bad==2)b[12]=0xff;
        else if(bad==3)b[16]=17;else if(bad==4)memset(b+21,0,4);
        else if(bad==5){memset(b+4,0,4);b[7]=1;}else if(bad==6)b[12]=0;else b[11]=97;
        GeoParameterCard untouched;memset(&untouched,0x5a,sizeof untouched);decoded=untouched;
        CHECK(!geo_parameter_card_definition_decode(b,size,&decoded)&&!memcmp(&decoded,&untouched,sizeof decoded),"card-invalid-decode-is-atomic");}
    card.next_field_id=0;card.fields[1]=UINT32_MAX;CHECK(geo_parameter_card_definition_encode(&card,b,sizeof b)&&geo_parameter_card_definition_decode(b,n,&decoded)&&decoded.next_field_id==0&&decoded.fields[1]==UINT32_MAX,"card-exhausted-highwater-retained");
    GeoParameterField field;literal(&field,0x01020304,0x05060708,GEO_PARAMETER_COUNT,1,1);strcpy(field.name,"F");strcpy(field.expression,"{}");field.value=(GeoQuantity){99,7,GEO_UNIT_LENGTH};
    const unsigned char field_bytes[]={1,2,3,4,5,6,7,8,0,0,0,1,0,0,0,1,'F',1,0,0,0,2,'{','}'};
    n=geo_parameter_field_definition_encode(&field,a,sizeof a);
    CHECK(n==sizeof field_bytes&&!memcmp(a,field_bytes,n),"field-fixed-authored-bytes");GeoParameterField result;
    CHECK(geo_parameter_field_definition_decode(a,n,&result)&&result.parameter_id==field.parameter_id&&result.id==field.id&&result.type==GEO_PARAMETER_COUNT&&!strcmp(result.name,"F")&&!strcmp(result.expression,"{}")&&quantity(result.value,0,0,GEO_UNIT_SCALAR),"field-decode-clears-derived-cache");
    for(unsigned bad=0;bad<7;++bad){memcpy(b,a,n);size_t size=n;
        if(bad==0)--size;else if(bad==1)b[size++]=0;else if(bad==2)b[11]=3;else if(bad==3)b[16]=0xff;
        else if(bad==4)b[17]=0;else if(bad==5)b[17]=2;else b[23]=0;
        GeoParameterField untouched;memset(&untouched,0x5a,sizeof untouched);result=untouched;
        CHECK(!geo_parameter_field_definition_decode(b,size,&result)&&!memcmp(&result,&untouched,sizeof result),"field-invalid-decode-is-atomic");}
    literal(&field,2,3,GEO_PARAMETER_DIMENSION,7,1);strcpy(field.name,"F");
    n=geo_parameter_field_definition_encode(&field,a,sizeof a);
    CHECK(geo_parameter_field_definition_decode(a,n,&result)&&!strcmp(result.expression,"{\"den\":\"1\",\"num\":\"7\",\"op\":\"literal\",\"unit\":\"mm\"}"),"field-canonical-full-ast");
    strcpy(field.expression," { \"unit\" : \"mm\", \"num\" : \"7\", \"op\" : \"literal\", \"den\" : \"1\" } ");
    CHECK(geo_parameter_field_definition_encode(&field,b,sizeof b)==n&&!memcmp(a,b,n),"field-equivalent-json-is-canonical");
    strcpy(field.expression,"{\"op\":\"add\",\"left\":{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"mm\"},\"right\":{\"op\":\"literal\",\"num\":\"4\",\"den\":\"1\",\"unit\":\"mm\"}}");
    size_t m=geo_parameter_field_definition_encode(&field,b,sizeof b);
    CHECK(m&&geo_parameter_field_definition_decode(b,m,&result)&&strstr(result.expression,"\"left\"")&&strstr(result.expression,"\"right\"")&&(m!=n||memcmp(a,b,n)),"equal-quantity-does-not-erase-authored-ast");
    strcpy(field.expression," {\"op\": ");m=geo_parameter_field_definition_encode(&field,b,sizeof b);
    CHECK(m&&b[17]==0&&geo_parameter_field_definition_decode(b,m,&result)&&!strcmp(result.expression,field.expression),"invalid-json-preserves-parser-input");
    memset(a,0xa5,sizeof a);memcpy(b,a,sizeof a);field.type=-1;
    CHECK(!geo_parameter_field_definition_encode(&field,a,sizeof a)&&!memcmp(a,b,sizeof a),"field-encode-failure-is-atomic");
    card.count=17;CHECK(!geo_parameter_card_definition_encode(&card,a,sizeof a)&&!memcmp(a,b,sizeof a),"card-encode-failure-is-atomic");
    return 0;
}
static int definitions_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"definitions-store");GeoParameterField fields[2];
    literal(&fields[0],10,9,GEO_PARAMETER_DIMENSION,7,1);literal(&fields[1],10,2,GEO_PARAMETER_COUNT,1,1);strcpy(fields[1].expression,"{bad");
    CHECK(put(store,10,fields,2),"definitions-unused-invalid-ast");GeoParameterCard empty={0};empty.id=99;empty.next_field_id=77;strcpy(empty.name,"Empty");
    CHECK(geo_parameters_stage_card(store,&empty),"definitions-empty-card");empty.id=UINT32_MAX;empty.next_field_id=0;strcpy(empty.name,"Exhausted");
    literal(&fields[0],UINT32_MAX,UINT32_MAX,GEO_PARAMETER_RATIO,11,3);fields[0].value=(GeoQuantity){123,7,GEO_UNIT_SCALAR};
    CHECK(geo_parameters_stage_card(store,&empty)&&geo_parameters_stage_field(store,&fields[0]),"definitions-exhausted-card");
    GeoParameterStore *before=geo_parameters_clone(store);Binding binding={0};CHECK(before&&bind(&binding,store,901),"definitions-bind");
    CHECK(geo_eval_provider_count(binding.graph)==2&&geo_eval_node_count(binding.graph)==0,"registration-does-not-evaluate");GeoParameterError error;
    CHECK(geo_parameter_sources_definitions(binding.sources,&error)&&error.status==GEO_PARAMETER_OK,"definitions-enumerates-unused-and-empty");
    for(size_t i=0;i<geo_eval_node_count(binding.graph);++i){GeoSourceNodeView n;
        CHECK(geo_eval_node_at(binding.graph,i,&n)&&n.source.provider==DEFINITION_TOKEN&&n.state==GEO_NODE_VALID&&n.value&&n.value->kind==GEO_SOURCE_DEFINITION,"metadata-enumeration-never-evaluates-quantities");}
    CHECK(geo_eval_node_count(binding.graph)==6&&geo_eval_edge_count(binding.graph)==3&&geo_parameters_equal(store,before),"metadata-all-definitions-and-no-cache-writes");
    GeoSourceValue value;CHECK(definition(&binding,GEO_PARAMETER_DEFINITION_CARD,10,0,&value),"metadata-card-value");GeoParameterCard card;
    CHECK(geo_parameter_card_definition_decode(value.as.definition.content,value.as.definition.content_size,&card)&&card.count==2&&card.fields[0]==9&&card.fields[1]==2&&card.next_field_id==10&&!strcmp(card.name,"card-10"),"metadata-preserves-order-name-and-highwater");
    CHECK(definition(&binding,GEO_PARAMETER_DEFINITION_FIELD,10,2,&value),"metadata-invalid-field-value");GeoParameterField field;
    CHECK(geo_parameter_field_definition_decode(value.as.definition.content,value.as.definition.content_size,&field)&&!strcmp(field.expression,"{bad")&&field.type==GEO_PARAMETER_COUNT,"metadata-includes-unused-invalid-ast");
    CHECK(geo_eval_seal(binding.graph)&&geo_parameter_sources_definitions(binding.sources,&error),"metadata-sealed-repeat");GeoQuantity out={97,11,GEO_UNIT_LENGTH};
    CHECK(!geo_parameter_sources_value(binding.sources,ref(10,9),&out,&error)&&quantity(out,97,11,GEO_UNIT_LENGTH)&&geo_parameters_equal(store,before)&&geo_eval_node_count(binding.graph)==6,"sealed-metadata-does-not-enable-new-values");
    dispose(&binding,true);geo_parameters_destroy(before);geo_parameters_destroy(store);return 0;
}
static int typed_case(void)
{
    for(unsigned which=0;which<2;++which){GeoParameterStore *store=geo_parameters_create();CHECK(store,"typed-store");GeoParameterField field;
        literal(&field,1,1,which?GEO_PARAMETER_RATIO:GEO_PARAMETER_DIMENSION,which?-3:7,which?2:1);CHECK(put(store,1,&field,1),"typed-original-definition");
        Binding binding={0};CHECK(bind(&binding,store,910+which),"typed-bind");GeoSourceValue value;
        CHECK(definition(&binding,GEO_PARAMETER_DEFINITION_FIELD,1,1,&value),"typed-memo-authored-definition");
        const void *borrowed=value.as.definition.content;size_t length=value.as.definition.content_size;unsigned char original[GEO_PARAMETER_FIELD_CONTENT_MAX];memcpy(original,borrowed,length);
        literal(&field,1,1,which?GEO_PARAMETER_COUNT:GEO_PARAMETER_DIMENSION,which?-3:19,which?2:1);CHECK(put(store,1,&field,1),"typed-divergent-raw-authoring");
        GeoQuantity out={0};GeoParameterError error;
        CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error)&&quantity(out,which?-3:7,which?2:1,which?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH),"quantity-consumes-returned-field-definition");
        const GeoParameterField *raw=geo_parameters_fields(store);
        CHECK(raw[0].type==field.type&&!strcmp(raw[0].expression,field.expression)&&quantity(raw[0].value,out.num,out.den,out.unit)&&!memcmp(borrowed,original,length),"typed-consumption-changes-only-success-cache");
        CHECK(geo_eval_seal(binding.graph)&&geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error),"typed-sealed-memo");
        dispose(&binding,which==0);geo_parameters_destroy(store);}
    return 0;
}
static int graph_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"graph-store");GeoParameterField field;
    literal(&field,1,1,GEO_PARAMETER_DIMENSION,0,1);strcpy(field.expression,"{\"op\":\"add\",\"left\":{\"op\":\"ref\",\"parameterId\":2,\"fieldId\":1},\"right\":{\"op\":\"ref\",\"parameterId\":3,\"fieldId\":1}}");
    CHECK(put(store,1,&field,1),"graph-root");literal(&field,2,1,GEO_PARAMETER_DIMENSION,7,3);CHECK(put(store,2,&field,1),"graph-first-leaf");
    literal(&field,3,1,GEO_PARAMETER_DIMENSION,2,3);CHECK(put(store,3,&field,1),"graph-second-leaf");GeoParameterStore *plain=geo_parameters_clone(store);
    Binding binding={0};CHECK(plain&&bind(&binding,store,920),"graph-bind");GeoParameterError a,b;GeoQuantity out;
    CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&a)&&quantity(out,3,1,GEO_UNIT_LENGTH),"graph-exact-value");
    for(uint32_t card=1;card<=3;++card){size_t q=node(binding.graph,false,0,card,1),f=node(binding.graph,true,GEO_PARAMETER_DEFINITION_FIELD,card,1),c=node(binding.graph,true,GEO_PARAMETER_DEFINITION_CARD,card,0);
        CHECK(edge(binding.graph,q,f,GEO_DEPENDENCY_DEFINITION_REQUIRED),"quantity-field-definition-edge");
        CHECK(edge(binding.graph,f,c,GEO_DEPENDENCY_DEFINITION_REQUIRED),"field-card-definition-edge");}
    CHECK(edge(binding.graph,node(binding.graph,false,0,1,1),node(binding.graph,false,0,2,1),GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(binding.graph,node(binding.graph,false,0,1,1),node(binding.graph,false,0,3,1),GEO_DEPENDENCY_VALUE_REQUIRED),"ast-reference-value-edges");
    CHECK(geo_eval_node_count(binding.graph)==9&&geo_eval_edge_count(binding.graph)==8&&geo_parameters_rebuild(plain,&b)&&geo_parameters_equal(store,plain),"full-graph-exact-node-edge-and-cache-parity");
    CHECK(geo_parameter_sources_definitions(binding.sources,&a)&&geo_eval_seal(binding.graph)&&geo_parameter_sources_value(binding.sources,ref(1,1),&out,&a)&&quantity(out,3,1,GEO_UNIT_LENGTH)&&geo_eval_node_count(binding.graph)==9&&geo_eval_edge_count(binding.graph)==8,"graph-completion-and-sealed-memo");
    dispose(&binding,true);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int descriptor_case(void)
{
    for(unsigned which=0;which<3;++which){GeoParameterStore *store=geo_parameters_create();CHECK(store,"descriptor-store");GeoParameterField field;
        int authored_type=which==1?GEO_PARAMETER_RATIO:GEO_PARAMETER_DIMENSION;
        literal(&field,1,1,authored_type,which==1?-3:7,which==1?2:1);CHECK(put(store,1,&field,1),"descriptor-authored-field");Binding binding={0};CHECK(bind(&binding,store,925+which),"descriptor-bind");
        if(which<2){GeoSourceValue value;CHECK(definition(&binding,GEO_PARAMETER_DEFINITION_FIELD,1,1,&value),"descriptor-memo-definition");}
        else{uint32_t ids[]={1,1};GeoSourceDescriptor descriptor;GeoSourceNodeView n;
            CHECK(geo_eval_describe(binding.graph,(GeoSourceRef){VALUE_TOKEN,ids,sizeof ids},&descriptor)==GEO_SOURCE_OK&&descriptor.unit==GEO_UNIT_LENGTH&&geo_eval_node_count(binding.graph)==1&&geo_eval_edge_count(binding.graph)==0&&geo_eval_node_at(binding.graph,0,&n)&&n.state==GEO_NODE_NEW&&!n.value,"quantity-description-does-not-evaluate-sources");}
        literal(&field,1,1,which==1?GEO_PARAMETER_DIMENSION:GEO_PARAMETER_COUNT,19,1);CHECK(put(store,1,&field,1),"descriptor-cross-unit-raw-change");GeoQuantity out={97,11,GEO_UNIT_LENGTH};GeoParameterError error;
        CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error)&&quantity(out,which==1?-3:7,which==1?2:1,which==1?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH),"quantity-descriptor-uses-canonical-unit");
        GeoSourceNodeView n;CHECK(geo_eval_node_at(binding.graph,node(binding.graph,false,0,1,1),&n)&&n.descriptor.unit==out.unit&&n.state==GEO_NODE_VALID&&edge(binding.graph,node(binding.graph,true,GEO_PARAMETER_DEFINITION_FIELD,1,1),node(binding.graph,true,GEO_PARAMETER_DEFINITION_CARD,1,0),GEO_DEPENDENCY_DEFINITION_REQUIRED),"descriptor-memo-keeps-real-card-dependency");
        const GeoParameterField *raw=geo_parameters_fields(store);CHECK(raw[0].type==field.type&&!strcmp(raw[0].expression,field.expression)&&quantity(raw[0].value,out.num,out.den,out.unit),"descriptor-authority-preserves-raw-metadata");
        dispose(&binding,which!=1);geo_parameters_destroy(store);}
    return 0;
}
static int diagnostics_case(void)
{
    const char *expressions[]={"{", "{}", "{\"op\":\"unknown\"}",
        "{\"op\":\"literal\",\"num\":\"3\",\"den\":\"0\",\"unit\":\"mm\"}",
        "{\"op\":\"literal\",\"num\":\"3x\",\"den\":\"1\",\"unit\":\"mm\"}",
        "{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"1\"}",
        "{\"op\":\"ref\",\"parameterId\":99,\"fieldId\":7}",
        "{\"op\":\"literal\",\"op\":\"ref\"}",
        "{\"op\":\"literal\",\"num\":\"3\",\"den\":\"2\",\"unit\":\"1\"}"};
    GeoParameterStatus expected[]={GEO_PARAMETER_JSON,GEO_PARAMETER_AST_OPERATION_MISSING,GEO_PARAMETER_UNSUPPORTED_OPERATION,
        GEO_PARAMETER_DENOMINATOR,GEO_PARAMETER_INTEGER,GEO_PARAMETER_FIELD_UNIT,GEO_PARAMETER_MISSING_FIELD,GEO_PARAMETER_JSON,GEO_PARAMETER_COUNT_VALUE};
    for(size_t which=0;which<sizeof expected/sizeof *expected;++which){GeoParameterStore *store=geo_parameters_create();CHECK(store,"diagnostics-store");GeoParameterField field;
        literal(&field,8,3,which==8?GEO_PARAMETER_COUNT:GEO_PARAMETER_DIMENSION,0,1);strcpy(field.expression,expressions[which]);CHECK(put(store,8,&field,1),"diagnostics-input");
        GeoParameterStore *plain=geo_parameters_clone(store);Binding binding={0};CHECK(plain&&bind(&binding,store,930+which),"diagnostics-bind");
        GeoParameterError a,b;GeoQuantity out={97,11,GEO_UNIT_LENGTH};CHECK(geo_parameter_sources_definitions(binding.sources,&a),"diagnostics-metadata-does-not-validate-ast");
        CHECK(!geo_parameter_sources_value(binding.sources,ref(8,3),&out,&a)&&a.status==expected[which]&&a.trace_count==1&&same_ref(a.trace[0],ref(8,3))&&same_ref(a.source,which==6?ref(99,7):ref(0,0))&&quantity(out,97,11,GEO_UNIT_LENGTH),"diagnostics-fixed-status-trace-output");
        CHECK(!geo_parameters_evaluate_field(plain,ref(8,3),&b)&&same_error(&a,&b)&&geo_parameters_equal(store,plain),"diagnostics-original-parser-and-cache-parity");
        dispose(&binding,false);geo_parameters_destroy(plain);geo_parameters_destroy(store);}
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"cycle-store");GeoParameterField fields[2];reference(&fields[0],1,1,1,2);reference(&fields[1],1,2,1,1);CHECK(put(store,1,fields,2),"cycle-input");
    GeoParameterStore *plain=geo_parameters_clone(store);Binding binding={0};CHECK(plain&&bind(&binding,store,940),"cycle-bind");GeoParameterError a,b;GeoQuantity out={97,11,GEO_UNIT_LENGTH};
    CHECK(!geo_parameter_sources_value(binding.sources,ref(1,1),&out,&a)&&a.status==GEO_PARAMETER_CYCLE&&same_ref(a.source,ref(1,1))&&a.trace_count==2&&same_ref(a.trace[0],ref(1,2))&&same_ref(a.trace[1],ref(1,1))&&quantity(out,97,11,GEO_UNIT_LENGTH),"cycle-exact-identity-and-trace");
    CHECK(!geo_parameters_evaluate_field(plain,ref(1,1),&b)&&same_error(&a,&b)&&geo_parameters_equal(store,plain),"cycle-original-parity");
    dispose(&binding,true);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static GeoParameterRef chain_ref(size_t i){return ref((uint32_t)(i/16)+1,(uint32_t)(i%16)+1);}
static bool chain(GeoParameterStore *store,size_t count,bool cached)
{
    for(size_t start=0;start<count;start+=16){GeoParameterField fields[16];size_t n=count-start<16?count-start:16;
        for(size_t k=0;k<n;++k){size_t i=start+k;GeoParameterRef here=chain_ref(i);
            if((cached&&i==0)||(!cached&&i+1==count))literal(&fields[k],here.parameter_id,here.field_id,GEO_PARAMETER_DIMENSION,7,3);
            else{GeoParameterRef from=chain_ref(cached?i-1:i+1);reference(&fields[k],here.parameter_id,here.field_id,from.parameter_id,from.field_id);}}
        if(!put(store,chain_ref(start).parameter_id,fields,n))return false;}
    return true;
}
static int depth_case(void)
{
    for(unsigned cached=0;cached<2;++cached)for(size_t count=64;count<=65;++count){GeoParameterStore *store=geo_parameters_create();CHECK(store&&chain(store,count,cached!=0),"depth-input");
        GeoParameterStore *plain=geo_parameters_clone(store);Binding binding={0};CHECK(plain&&bind(&binding,store,950+cached),"depth-bind");GeoParameterError a,b;
        bool actual=geo_parameter_sources_rebuild(binding.sources,&a),expected=geo_parameters_rebuild(plain,&b);
        CHECK(actual==(count==64)&&expected==(count==64),"definition-mode-preserves-depth-64-boundary");
        CHECK(same_error(&a,&b)&&geo_parameters_equal(store,plain),"definition-mode-preserves-depth-diagnostics-and-caches");
        if(count==65){CHECK(a.status==GEO_PARAMETER_DEPTH&&a.trace_count==(cached?1:64)&&same_ref(a.source,ref(0,0)),"depth-65-fixed-diagnostic");
            for(size_t i=0;i<a.trace_count;++i)CHECK(same_ref(a.trace[i],chain_ref(cached?64:63-i)),"depth-65-fixed-trace");}
        dispose(&binding,true);geo_parameters_destroy(plain);geo_parameters_destroy(store);}
    return 0;
}
static int prefix_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"prefix-store");GeoParameterField fields[3];
    literal(&fields[0],1,1,GEO_PARAMETER_DIMENSION,0,1);strcpy(fields[0].expression,"{\"op\":\"add\",\"left\":{\"op\":\"ref\",\"parameterId\":1,\"fieldId\":2},\"right\":{\"op\":\"ref\",\"parameterId\":1,\"fieldId\":3}}");
    literal(&fields[1],1,2,GEO_PARAMETER_DIMENSION,7,1);strcpy(fields[1].expression," { \"op\":\"literal\", \"num\":\"7\", \"den\":\"1\", \"unit\":\"mm\" } ");reference(&fields[2],1,3,99,9);
    GeoParameterCard card={0};card.id=1;card.next_field_id=4;strcpy(card.name,"Prefix");CHECK(geo_parameters_stage_card(store,&card),"prefix-card");
    for(size_t i=0;i<3;++i){fields[i].value=(GeoQuantity){101+(int64_t)i,13,GEO_UNIT_LENGTH};CHECK(geo_parameters_stage_field(store,&fields[i]),"prefix-staged-caches");}
    GeoParameterStore *plain=geo_parameters_clone(store);Binding binding={0};CHECK(plain&&bind(&binding,store,960),"prefix-bind");GeoParameterError a,b;GeoQuantity out={97,11,GEO_UNIT_LENGTH};
    CHECK(!geo_parameter_sources_value(binding.sources,ref(1,1),&out,&a)&&a.status==GEO_PARAMETER_MISSING_FIELD&&same_ref(a.source,ref(99,9))&&a.trace_count==2&&same_ref(a.trace[0],ref(1,3))&&same_ref(a.trace[1],ref(1,1))&&quantity(out,97,11,GEO_UNIT_LENGTH),"prefix-fixed-failure");
    const GeoParameterField *actual=geo_parameters_fields(store);
    CHECK(quantity(actual[0].value,101,13,GEO_UNIT_LENGTH)&&quantity(actual[1].value,7,1,GEO_UNIT_LENGTH)&&quantity(actual[2].value,103,13,GEO_UNIT_LENGTH),"successful-prefix-cache-is-published");
    CHECK(!geo_parameters_evaluate_field(plain,ref(1,1),&b)&&same_error(&a,&b)&&geo_parameters_equal(store,plain)&&!strcmp(actual[1].expression,fields[1].expression),"failed-root-retains-original-authoring-and-parser-parity");
    CHECK(geo_parameter_sources_value(binding.sources,ref(1,2),&out,&a)&&a.status==GEO_PARAMETER_OK&&quantity(out,7,1,GEO_UNIT_LENGTH),"successful-prefix-readable-after-failure");
    dispose(&binding,false);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int reset_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"reset-store");GeoParameterField field;literal(&field,1,1,GEO_PARAMETER_DIMENSION,7,1);CHECK(put(store,1,&field,1),"reset-initial-definition");
    Binding binding={0};CHECK(bind(&binding,store,970),"reset-bind");GeoParameterError error;GeoQuantity out;CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error)&&quantity(out,7,1,GEO_UNIT_LENGTH),"reset-initial-value");
    for(unsigned generation=1;generation<=2;++generation){GeoParameterSources *old=binding.sources;CHECK(geo_eval_reset(binding.graph)&&geo_eval_provider_count(binding.graph)==0&&geo_eval_node_count(binding.graph)==0,"reset-clears-registry");
        out=(GeoQuantity){97,11,GEO_UNIT_LENGTH};
        CHECK(!geo_parameter_sources_value(old,ref(1,1),&out,&error)&&error.status==GEO_PARAMETER_INVALID_DEFINITION&&quantity(out,97,11,GEO_UNIT_LENGTH)&&!geo_parameter_sources_definitions(old,&error),"reset-old-handle-is-rejected-before-register");
        literal(&field,1,1,GEO_PARAMETER_DIMENSION,(int)(7+12*generation),1);GeoParameterCard card=*geo_parameters_find(store,1);card.next_field_id=100+generation;strcpy(card.name,generation==1?"Second":"Third");
        CHECK(geo_parameters_put(store,&card,&field,&error),"reset-new-authored-generation");
        binding.sources=geo_parameter_sources_register_with_definitions(binding.graph,store,VALUE_TOKEN,DEFINITION_TOKEN,"test.parameter.field","parameter-definition-test/1");
        CHECK(binding.sources&&geo_eval_provider_count(binding.graph)==2,"old-handle-check-does-not-close-registration");
        CHECK(!geo_parameter_sources_value(old,ref(1,1),&out,&error)&&quantity(out,97,11,GEO_UNIT_LENGTH),"reset-old-handle-cannot-read-new-generation");
        geo_parameter_sources_destroy(old);CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error)&&quantity(out,7+12*generation,1,GEO_UNIT_LENGTH),"reset-rebuilds-shadow-and-actual-definition-value");GeoSourceValue value;
        CHECK(definition(&binding,GEO_PARAMETER_DEFINITION_CARD,1,0,&value)&&geo_parameter_card_definition_decode(value.as.definition.content,value.as.definition.content_size,&card)&&card.next_field_id==100+generation&&!strcmp(card.name,generation==1?"Second":"Third"),"reset-rebuilds-complete-card-definition");}
    CHECK(geo_eval_candidate_id(binding.graph)==970&&geo_eval_base_revision(binding.graph)==73,"reset-preserves-candidate-identity");
    dispose(&binding,true);geo_parameters_destroy(store);return 0;
}
static int lifetime_case(void)
{
    GeoParameterStore *live=geo_parameters_create();CHECK(live,"lifetime-store");GeoParameterField field;literal(&field,0,0,GEO_PARAMETER_DIMENSION,7,1);CHECK(put(live,0,&field,1),"lifetime-zero-identities");
    GeoParameterStore *before=geo_parameters_clone(live),*left=geo_parameters_clone(live),*right=geo_parameters_clone(live);CHECK(before&&left&&right,"lifetime-clones");
    literal(&field,0,0,GEO_PARAMETER_DIMENSION,19,1);CHECK(put(left,0,&field,1),"lifetime-left-change");Binding a={0},b={0};CHECK(bind(&a,left,980)&&bind(&b,right,981),"lifetime-independent-bindings");GeoQuantity out;GeoParameterError error;
    CHECK(geo_parameter_sources_value(a.sources,ref(0,0),&out,&error)&&quantity(out,19,1,GEO_UNIT_LENGTH)&&geo_parameter_sources_value(b.sources,ref(0,0),&out,&error)&&quantity(out,7,1,GEO_UNIT_LENGTH)&&geo_parameters_equal(live,before),"lifetime-candidate-isolation");
    CHECK(geo_parameter_sources_store(a.sources)==left&&geo_parameter_sources_context(a.sources)==a.graph&&geo_eval_seal(a.graph)&&geo_eval_seal(b.graph),"lifetime-bound-identities");
    GeoSourceValue av,bv;CHECK(definition(&a,GEO_PARAMETER_DEFINITION_FIELD,0,0,&av)&&definition(&b,GEO_PARAMETER_DEFINITION_FIELD,0,0,&bv)&&av.as.definition.content!=bv.as.definition.content,"lifetime-candidate-owned-content");
    dispose(&a,true);CHECK(geo_parameter_sources_value(b.sources,ref(0,0),&out,&error)&&quantity(out,7,1,GEO_UNIT_LENGTH),"lifetime-other-candidate-survives");dispose(&b,false);
    geo_parameters_destroy(before);geo_parameters_destroy(left);geo_parameters_destroy(right);geo_parameters_destroy(live);return 0;
}
static bool dummy_describe(void *state,const GeoSourceRef *source,GeoSourceDescriptor *out)
{(void)state;(void)source;*out=(GeoSourceDescriptor){.kind=GEO_SOURCE_QUANTITY,.unit=GEO_UNIT_SCALAR,.context={false,0,-1}};return true;}
static bool dummy_evaluate(void *state,GeoEvalContext *graph,const GeoSourceRef *source,GeoSourceValue *out)
{(void)state;(void)graph;(void)source;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){1,1,GEO_UNIT_SCALAR};return true;}
static int registration_case(void)
{
    GeoParameterStore *store=geo_parameters_create();GeoEvalContext *graph=geo_eval_create(990,73);CHECK(store&&graph,"registration-fixture");
    CHECK(!geo_parameter_sources_register_with_definitions(graph,store,0,38,"test.parameter.field","1")&&!geo_parameter_sources_register_with_definitions(graph,store,37,37,"test.parameter.field","1")&&!geo_parameter_sources_register_with_definitions(graph,store,37,0,"test.parameter.field","1")&&geo_eval_provider_count(graph)==0,"registration-invalid-identities-atomic");
    GeoSourceProvider existing={77,"core.parameter.definition","existing/1",NULL,dummy_describe,dummy_evaluate};CHECK(geo_eval_register(graph,&existing),"registration-existing-definition-namespace");
    GeoParameterSources *conflict=geo_parameter_sources_register_with_definitions(graph,store,37,38,"test.parameter.field","1");
    CHECK(!conflict&&geo_eval_provider_count(graph)==1&&geo_eval_provider_at(graph,0)->token==77,"definition-family-registration-is-atomic");
    CHECK(geo_eval_reset(graph),"registration-reset");Binding binding={graph,NULL};binding.sources=geo_parameter_sources_register_with_definitions(graph,store,37,38,"test.parameter.field","1");CHECK(binding.sources&&geo_eval_provider_count(graph)==2&&geo_eval_node_count(graph)==0,"registration-complete-family");
    GeoParameterDefinitionKey key;GeoSourceDescriptor descriptor;CHECK(geo_eval_describe(graph,geo_parameter_definition_source_ref(38,GEO_PARAMETER_DEFINITION_FIELD,123,456,&key),&descriptor)==GEO_SOURCE_OK&&descriptor.kind==GEO_SOURCE_DEFINITION,"description-is-independent-of-value-existence");GeoSourceNodeView n;
    CHECK(geo_eval_node_at(graph,0,&n)&&n.state==GEO_NODE_NEW&&!n.value&&!geo_parameter_sources_register_with_definitions(graph,store,41,42,"later.field","1")&&geo_eval_provider_count(graph)==2,"description-does-not-evaluate-and-registration-closes");
    dispose(&binding,false);geo_parameters_destroy(store);return 0;
}
static int legacy_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"legacy-store");GeoParameterField fields[2];reference(&fields[0],1,1,1,2);literal(&fields[1],1,2,GEO_PARAMETER_DIMENSION,7,3);CHECK(put(store,1,fields,2),"legacy-definitions");
    Binding binding={geo_eval_create(999,73),NULL};CHECK(binding.graph,"legacy-context");binding.sources=geo_parameter_sources_register(binding.graph,store,37,"test.parameter.field","legacy/1");CHECK(binding.sources,"legacy-register");GeoParameterError error;GeoQuantity out;
    CHECK(geo_parameter_sources_value(binding.sources,ref(1,1),&out,&error)&&quantity(out,7,3,GEO_UNIT_LENGTH)&&geo_eval_provider_count(binding.graph)==1&&geo_eval_node_count(binding.graph)==2&&geo_eval_edge_count(binding.graph)==1,"legacy-provider-values-key-shape-and-edge-count");
    CHECK(!geo_parameter_sources_definitions(binding.sources,&error)&&error.status==GEO_PARAMETER_INVALID_DEFINITION&&geo_eval_node_count(binding.graph)==2,"legacy-does-not-silently-add-definition-mode");
    dispose(&binding,true);geo_parameters_destroy(store);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"keys"))return keys_case();
    if(!strcmp(argv[1],"codec"))return codec_case();
    if(!strcmp(argv[1],"definitions"))return definitions_case();
    if(!strcmp(argv[1],"typed"))return typed_case();
    if(!strcmp(argv[1],"graph"))return graph_case();
    if(!strcmp(argv[1],"descriptor"))return descriptor_case();
    if(!strcmp(argv[1],"diagnostics"))return diagnostics_case();
    if(!strcmp(argv[1],"depth"))return depth_case();
    if(!strcmp(argv[1],"prefix"))return prefix_case();
    if(!strcmp(argv[1],"reset"))return reset_case();
    if(!strcmp(argv[1],"lifetime"))return lifetime_case();
    if(!strcmp(argv[1],"registration"))return registration_case();
    if(!strcmp(argv[1],"legacy"))return legacy_case();
    return 2;
}
