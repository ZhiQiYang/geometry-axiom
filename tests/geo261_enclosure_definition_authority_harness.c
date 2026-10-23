/* The original fixture supplies public K stores/providers. Only the value
 * returned to enclosure_sources.c is substituted; the real graph still owns
 * evaluation and edges and every raw authoring record stays untouched. */
#define main enclosure_original_fixture_main
#include "geo261_enclosure_sources_harness.c"
#undef main

static GeoEvalContext *changed_graph;
static GeoEnclosureSourceKind changed_kind;
static GeoSourceValue replacement;
static GeoSourceStatus replacement_status;
static unsigned changes;
static unsigned char returned_bytes[GEO_ENCLOSURE_RESULT_BYTES+1];
static GeoSourceStatus authority_source(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
    if(status!=GEO_SOURCE_OK||graph!=changed_graph||ref.provider!=ENC||
        !geo_enclosure_source_decode(&ref,&kind,&id,&axis,&slot)||id!=9||kind!=changed_kind)return status;
    ++changes;if(replacement_status!=GEO_SOURCE_OK)return replacement_status;
    *out=replacement;return GEO_SOURCE_OK;
}
#define geo_eval_source authority_source
#include "enclosure_sources.c"
#undef geo_eval_source

static void inject(Fixture *f,GeoEnclosureSourceKind kind,const GeoEnclosure *value)
{
    size_t size=0;CHECK(geo_enclosure_source_encode_definition(kind,value,returned_bytes,sizeof returned_bytes,&size),"authority-encode-fixture");
    changed_graph=f->graph;changed_kind=kind;replacement_status=GEO_SOURCE_OK;changes=0;
    replacement.kind=GEO_SOURCE_DEFINITION;replacement.as.definition=(GeoDefinitionValue){
        kind==GEO_ENCLOSURE_SOURCE_DEFINITION?"geo.enclosure.members/1":"geo.enclosure.result/1",returned_bytes,size};
}
static void clear(void){changed_graph=NULL;changes=0;}
static Fixture *two(void)
{
    Fixture *f=make();add_region(f,1,100,100);add_region(f,2,120,140);
    add_placement(f,11,1,zplus(100));add_placement(f,22,2,zplus(250));
    uint32_t ids[]={1};members(f,9,ids,1);start(f,false);return f;
}
static GeoEnclosure member_value(uint32_t first,uint32_t second,size_t count)
{GeoEnclosure value={0};value.id=9;value.member_count=count;value.member_ids[0]=first;value.member_ids[1]=second;return value;}
static void wire(void)
{
    const unsigned char members_wire[]={1,2,3,4,0,0,0,2,0,0,0,0,255,255,255,255};
    GeoDefinitionValue value={"geo.enclosure.members/1",members_wire,sizeof members_wire};GeoEnclosure out;
    CHECK(geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_DEFINITION,&value,0x01020304,&out)&&
        out.id==0x01020304&&out.member_count==2&&out.member_ids[0]==0&&out.member_ids[1]==UINT32_MAX&&
        !out.member_ids[2]&&!out.min[0]&&!out.max[2]&&!out.closed,"codec-independent-member-vector");
    unsigned char encoded[GEO_ENCLOSURE_RESULT_BYTES];size_t size=0;
    CHECK(geo_enclosure_source_encode_definition(GEO_ENCLOSURE_SOURCE_DEFINITION,&out,encoded,sizeof encoded,&size)&&
        size==sizeof members_wire&&!memcmp(encoded,members_wire,size),"codec-independent-member-encoding");
    const unsigned char result_wire[]={
        0,0,0,0,0,0,0,0,
        128,0,0,0,0,0,0,0, 255,255,255,255,255,255,255,255, 0,0,0,0,0,0,0,0,
        127,255,255,255,255,255,255,255, 0,0,0,0,0,0,0,1, 0,0,0,0,0,0,0,0, 1};
    value=(GeoDefinitionValue){"geo.enclosure.result/1",result_wire,sizeof result_wire};
    CHECK(geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value,0,&out)&&!out.member_count&&
        out.min[0]==INT64_MIN&&out.min[1]==-1&&!out.min[2]&&out.max[0]==INT64_MAX&&out.max[1]==1&&!out.max[2]&&out.closed,
        "codec-independent-signed-result-vector");
    CHECK(geo_enclosure_source_encode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&out,encoded,sizeof encoded,&size)&&
        size==sizeof result_wire&&!memcmp(encoded,result_wire,size),"codec-independent-result-encoding");
    out.member_count=GEO_ENCLOSURE_MEMBER_CAPACITY;out.member_ids[7]=UINT32_MAX;
    CHECK(geo_enclosure_source_encode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&out,encoded,sizeof encoded,&size)&&size==GEO_ENCLOSURE_RESULT_BYTES,
        "codec-full-capacity-result");
    value=(GeoDefinitionValue){"geo.enclosure.result/1",encoded,size};
    CHECK(geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value,0,&out)&&
        out.member_count==GEO_ENCLOSURE_MEMBER_CAPACITY&&out.member_ids[7]==UINT32_MAX,"codec-full-capacity-decode");
    unsigned char before[sizeof encoded];memcpy(before,encoded,sizeof before);size=123;
    CHECK(!geo_enclosure_source_encode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&out,encoded,1,&size)&&size==123&&
        !memcmp(before,encoded,sizeof before),"codec-encode-failure-atomic");
}
static void malformed(void)
{
    const unsigned char good[]={0,0,0,9,0,0,0,1,0,0,0,1};
    GeoEnclosure before,out;memset(&before,0xa5,sizeof before);
    for(int mode=0;mode<9;++mode){
        unsigned char bytes[GEO_ENCLOSURE_RESULT_BYTES+1]={0};memcpy(bytes,good,sizeof good);
        GeoDefinitionValue value={"geo.enclosure.members/1",bytes,sizeof good};
        if(mode==0)value.schema="geo.enclosure.result/1";
        if(mode==1)value.schema=NULL;
        if(mode==2)value.content=NULL;
        if(mode==3)value.content_size=7;
        if(mode==4)value.content_size=sizeof good-1;
        if(mode==5)value.content_size=sizeof good+1;
        if(mode==6)bytes[3]=10;
        if(mode==7){bytes[7]=9;value.content_size=44;}
        if(mode==8){bytes[7]=0;value.schema="geo.enclosure.result/1";value.content_size=57;bytes[56]=2;}
        memcpy(&out,&before,sizeof out);
        CHECK(!geo_enclosure_source_decode_definition(mode==8?GEO_ENCLOSURE_SOURCE_RESULT:GEO_ENCLOSURE_SOURCE_DEFINITION,&value,9,&out)&&
            !memcmp(&out,&before,sizeof out),"codec-malformed-rejected-atomically");
    }
    GeoDefinitionValue value={"geo.enclosure.members/1",good,sizeof good};memcpy(&out,&before,sizeof out);
    CHECK(!geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_AXIS_BOUND,&value,9,&out)&&!memcmp(&out,&before,sizeof out),"codec-wrong-domain-atomic");
}
static void result_members(void)
{
    Fixture *f=two();GeoEnclosure raw=*geo_enclosures_at(f->enclosures,0),returned=member_value(2,0,1),out;
    inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,777,1};
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,&fault)&&out.member_count==1&&out.member_ids[0]==2&&
        out.max[0]==120&&out.max[1]==140&&out.max[2]==250&&changes==1,"returned-members-control-result");
    CHECK(fault.kind==GEO_ENCLOSURE_FAULT_INVERTED&&fault.member_id==777&&fault.axis==1&&f->frame_calls[0]==0&&f->region_calls[0]==0&&
        !memcmp(&raw,geo_enclosures_at(f->enclosures,0),sizeof raw),"returned-members-preserve-authoring-and-fault");
    GeoSourceValue value;GeoEnclosure decoded;
    CHECK(source(f,GEO_ENCLOSURE_SOURCE_RESULT,9,-1,-1,&value)==GEO_SOURCE_OK&&
        geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,9,&decoded)&&
        decoded.member_ids[0]==2&&decoded.max[2]==250,"returned-members-published-result-identity");
    destroy(f);clear();
}
static void axis_members(void)
{
    Fixture *f=two();GeoEnclosure returned=member_value(2,1,2);inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);
    GeoCoord coordinate=777;
    CHECK(geo_enclosure_sources_axis_bound(f->sources,9,2,1,&coordinate)&&coordinate==250&&changes==1&&f->frame_calls[0]==0,
        "returned-members-control-axis-order");
    CHECK(f->region_calls[0]==0&&f->region_calls[1]==0&&geo_enclosures_at(f->enclosures,0)->member_ids[0]==1,
        "returned-axis-keeps-authoring-and-no-result");destroy(f);clear();
    f=two();inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);f->typed_frames[1]=xminus(0);f->fail_frame=22;coordinate=777;
    CHECK(!geo_enclosure_sources_axis_bound(f->sources,9,2,1,&coordinate)&&coordinate==777&&f->frame_calls[1]==1&&!f->frame_calls[0],
        "returned-axis-upstream-failure-precedes-later-match");destroy(f);clear();
}
static void fault_order(void)
{
    Fixture *f=two();GeoEnclosure returned=member_value(2,99,2),out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);
    inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);GeoEnclosureFault fault={0};
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_MISSING_REGION&&fault.member_id==99&&
        f->frame_calls[1]==1&&f->region_calls[1]==1&&f->frame_calls[0]==0&&!memcmp(&out,&before,sizeof out),
        "returned-members-control-ordered-fault");destroy(f);clear();
    f=two();inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);f->fail_frame=22;fault=(GeoEnclosureFault){GEO_ENCLOSURE_FAULT_INVERTED,777,1};
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_INVERTED&&fault.member_id==777&&
        fault.axis==1&&!memcmp(&out,&before,sizeof out)&&!f->region_calls[1],"returned-upstream-failure-precedes-later-missing-member");destroy(f);clear();
    f=two();returned=member_value(2,2,2);inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_DUPLICATE_REGION&&fault.member_id==2&&
        f->frame_calls[1]==1&&f->region_calls[1]==1,"returned-duplicate-retains-geometry-fault");destroy(f);clear();
    f=two();returned=member_value(2,1,2);inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);f->fail_region=1;
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_SLOT_TAKEN&&fault.member_id==1&&
        f->region_calls[0]==0,"returned-order-slot-precedes-outline");destroy(f);clear();
}
static void invalid_return(void)
{
    for(int axis=0;axis<2;++axis)for(int mode=0;mode<4;++mode){
        Fixture *f=two();GeoEnclosure returned=member_value(2,0,1),out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);
        inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);
        if(mode==0)replacement.as.definition.schema="wrong/1";
        if(mode==1)replacement.as.definition.content_size++;
        if(mode==2)replacement.kind=GEO_SOURCE_FEATURE;
        if(mode==3)replacement_status=GEO_SOURCE_FAILED;
        GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,777,1};GeoCoord coordinate=888;
        bool ok=axis?geo_enclosure_sources_axis_bound(f->sources,9,2,1,&coordinate):geo_enclosure_sources_value(f->sources,9,&out,&fault);
        CHECK(!ok&&changes==1&&coordinate==888&&!memcmp(&out,&before,sizeof out)&&fault.kind==GEO_ENCLOSURE_FAULT_INVERTED&&
            fault.member_id==777&&fault.axis==1&&!f->frame_calls[0]&&!f->frame_calls[1]&&!f->region_calls[0]&&!f->region_calls[1],
            "malformed-return-blocks-geometry-atomically");destroy(f);clear();
    }
}
static void result_value(void)
{
    Fixture *f=two();GeoEnclosure returned=member_value(2,1,2),out;returned.min[0]=-7;returned.max[2]=901;returned.closed=true;
    inject(f,GEO_ENCLOSURE_SOURCE_RESULT,&returned);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&changes==1&&out.member_count==2&&out.member_ids[0]==2&&out.member_ids[1]==1&&
        out.min[0]==-7&&out.max[2]==901&&out.closed,"returned-result-controls-public-value");
    CHECK(geo_enclosures_at(f->enclosures,0)->member_count==1&&geo_enclosures_at(f->enclosures,0)->member_ids[0]==1,
        "returned-result-keeps-authoring");destroy(f);clear();
}
static void invalid_result(void)
{
    for(int mode=0;mode<3;++mode){
    Fixture *f=two();GeoEnclosure returned=member_value(2,0,1),out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);
    inject(f,GEO_ENCLOSURE_SOURCE_RESULT,&returned);
    if(mode==0)returned_bytes[replacement.as.definition.content_size-1]=2;
    if(mode==1)replacement.kind=GEO_SOURCE_FEATURE;
    if(mode==2)--replacement.as.definition.content_size;
    GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,777,1};
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&changes==1&&!memcmp(&out,&before,sizeof out)&&
        fault.kind==GEO_ENCLOSURE_FAULT_INVERTED&&fault.member_id==777&&fault.axis==1,"malformed-result-preserves-output-and-fault");destroy(f);clear();
    }
}
static void lifetime(void)
{
    Fixture *f=two(),*other=two();GeoEnclosure returned=member_value(2,0,1),out;
    inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.member_ids[0]==2,"authority-lifetime-first-result");
    memset(returned_bytes,0,sizeof returned_bytes);
    CHECK(geo_eval_seal(f->graph)&&geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.member_ids[0]==2&&out.max[2]==250&&changes==1&&
        geo_enclosure_sources_value(other->sources,9,&out,NULL)&&out.member_ids[0]==1&&out.max[2]==100,"authority-memo-candidate-and-owned-result");
    destroy(f);clear();destroy(other);
    f=two();returned=member_value(0,0,0);inject(f,GEO_ENCLOSURE_SOURCE_DEFINITION,&returned);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&!out.member_count&&!out.closed&&!out.max[2]&&!f->frame_calls[0],"returned-empty-members-stay-empty");
    CHECK(geo_eval_reset(f->graph),"authority-reset");geo_enclosure_sources_destroy(f->sources);f->sources=NULL;clear();start(f,false);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.member_ids[0]==1&&out.max[2]==100,"authority-reset-reregister-isolation");destroy(f);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"wire"))wire();else if(!strcmp(argv[1],"malformed"))malformed();
    else if(!strcmp(argv[1],"result"))result_members();else if(!strcmp(argv[1],"axis"))axis_members();
    else if(!strcmp(argv[1],"fault"))fault_order();else if(!strcmp(argv[1],"invalid"))invalid_return();
    else if(!strcmp(argv[1],"result-value"))result_value();else if(!strcmp(argv[1],"invalid-result"))invalid_result();
    else if(!strcmp(argv[1],"lifetime"))lifetime();else return 2;
    return 0;
}
