/* Public W consumers over the actual K values. The optional return fault hook
 * clones returned views/bytes; it never edits the provider's candidate cache. */
#define main legacy_finish_main
#include "geo261_finish_sources_harness.c"
#undef main

enum { DP_CONSUMER=44 };
static unsigned return_fault,return_hits;
static uint32_t policy_be32(const unsigned char *p)
{return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static void policy_write32(unsigned char *p,uint32_t v)
{p[0]=(unsigned char)(v>>24);p[1]=(unsigned char)(v>>16);p[2]=(unsigned char)(v>>8);p[3]=(unsigned char)v;}
static size_t policy_edge_offsets(const unsigned char *p,size_t size,size_t *offsets,size_t cap)
{
    if(size<10)return 0;size_t at=10,n=0;uint32_t count=policy_be32(p+6);
    for(uint32_t c=0;c<count;++c){if(size-at<4)return 0;uint32_t holes=policy_be32(p+at);at+=4;
        for(uint32_t h=0;h<=holes;++h){if(size-at<4)return 0;uint32_t edges=policy_be32(p+at);at+=4;
            for(uint32_t e=0;e<edges;++e){if(size-at<3||n==cap)return 0;offsets[n++]=at;
                size_t length=((size_t)p[at+1]<<8)|p[at+2];at+=3;if(length>size-at)return 0;at+=length;}}}
    return at==size?n:0;
}
void geo261_policy_source_control(WoodFinishSourceKind kind,uint32_t id,GeoSourceValue *value)
{
    static unsigned char bytes[32768];static GeoRegionView regions[WOOD_DERIVED_COMPONENT_MAX];static GeoPoint2 vertices[GEO_LOOP_MAX_VERTICES];
    if(!return_fault)return;
    if(return_fault==1&&kind==WOOD_FINISH_SOURCE_DERIVED_REGION&&id==10&&value->kind==GEO_SOURCE_REGION_SET){
        if(value->as.regions.count!=1||value->as.regions.regions[0].outline.count>GEO_LOOP_MAX_VERTICES)return;
        regions[0]=value->as.regions.regions[0];memcpy(vertices,regions[0].outline.v,regions[0].outline.count*sizeof *vertices);
        vertices[0].u=7;regions[0].outline.v=vertices;value->as.regions.regions=regions;++return_hits;return;
    }
    bool boundary_control=return_fault==4||return_fault==45;
    if(kind!=(boundary_control?WOOD_FINISH_SOURCE_BOUNDARY_POLICY:WOOD_FINISH_SOURCE_DERIVED_POLICY)||id!=(boundary_control?8u:10u)||value->kind!=GEO_SOURCE_DEFINITION)return;
    size_t size=value->as.definition.content_size,offsets[64];if(size>sizeof bytes/2||!value->as.definition.content)return;
    memcpy(bytes,value->as.definition.content,size);size_t edges=policy_edge_offsets(bytes,size,offsets,64);if(!edges)return;
    value->as.definition.content=bytes;++return_hits;
    if(return_fault==2||return_fault==4)bytes[offsets[0]]=WOOD_EDGE_FREE;
    else if(return_fault==3)bytes[offsets[0]+3+4]='9';
    else if(return_fault==20){memcpy(bytes+size,bytes+10,size-10);policy_write32(bytes+6,2);value->as.definition.content_size=2*size-10;}
    else if(return_fault==21)bytes[offsets[edges-1]]=255;
    else if(return_fault==30||return_fault==45)value->as.definition.schema="wood.finish.wrong-policy/1";
    else if(return_fault==31)value->as.definition.content=NULL;
    else if(return_fault==32)value->as.definition.content_size=9;
    else if(return_fault==33)bytes[0]=2;
    else if(return_fault==34)policy_write32(bytes+1,11);
    else if(return_fault==35)policy_write32(bytes+6,WOOD_DERIVED_COMPONENT_MAX+1);
    else if(return_fault==36)policy_write32(bytes+10,GEO_REGION_MAX_HOLES+1);
    else if(return_fault==37)policy_write32(bytes+14,GEO_LOOP_MAX_VERTICES+1);
    else if(return_fault==38){bytes[offsets[0]+1]=2;bytes[offsets[0]+2]=0;}
    else if(return_fault==39)bytes[offsets[0]+3]=0;
    else if(return_fault==40){bytes[size]=0;value->as.definition.content_size=size+1;}
    else if(return_fault==41)policy_write32(bytes+6,0);
    else if(return_fault==42)policy_write32(bytes+10,0);
    else if(return_fault==43)policy_write32(bytes+14,3);
    else if(return_fault==44){bytes[offsets[0]+1]=0;bytes[offsets[0]+2]=0;}
    else if(return_fault>=46&&return_fault<=50){size_t at=offsets[0]+3;
        if(return_fault==46)bytes[at]=0xff;
        else if(return_fault==47){bytes[at]=0xc0;bytes[at+1]=0x80;}
        else if(return_fault==48){bytes[at]=0xed;bytes[at+1]=0xa0;bytes[at+2]=0x80;}
        else if(return_fault==49){bytes[at]=0xf4;bytes[at+1]=0x90;bytes[at+2]=0x80;bytes[at+3]=0x80;}
        else{size_t length=((size_t)bytes[offsets[0]+1]<<8)|bytes[offsets[0]+2];bytes[at+length-1]=0xc2;}}
    else if(return_fault==51){bytes[offsets[0]+3]=0xc2;bytes[offsets[0]+4]=0xa2;}
    else if(return_fault==52){bytes[offsets[0]+3]=0xe4;bytes[offsets[0]+4]=0xb8;bytes[offsets[0]+5]=0xad;}
    else if(return_fault==53){bytes[offsets[0]+3]=0xf0;bytes[offsets[0]+4]=0x9f;bytes[offsets[0]+5]=0x98;bytes[offsets[0]+6]=0x80;}
    else if(return_fault==54)bytes[offsets[edges-1]+3]=0xff;
}
static unsigned policy_facts(const Fixture *f)
{return f->reads+f->writes+f->boundary_calls+f->box_calls+f->parameter_calls+f->named_calls;}
static bool consumer_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)user;uint32_t request;if(ref->provider!=DP_CONSUMER||ref->key_size!=sizeof request)return false;
    memcpy(&request,ref->key,sizeof request);if(request<1||request>4)return false;
    *out=(GeoSourceDescriptor){.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};return true;
}
static bool consumer_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=user;uint32_t request;memcpy(&request,ref->key,sizeof request);if(graph!=f->graph)return false;
    bool ok=false;char key[512];int hole=-99,edge=-99;
    if(request==1){WoodDerivedValue *value=malloc(sizeof *value);if(!value)return false;ok=wood_finish_sources_read_derived(f->sources,10,value);free(value);}
    else if(request==2)ok=wood_finish_sources_edge_key(f->sources,10,0,-1,0,key,sizeof key);
    else if(request==3)ok=wood_finish_sources_edge_resolve(f->sources,10,"[[\"e0\",0,1]]",&hole,&edge);
    else if(request==4)ok=wood_finish_sources_definitions(f->sources);
    if(ok){out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"test.derived-policy-consumer/1","ok",2};}return ok;
}
static bool attach_consumer(Fixture *f)
{if(!attach(f))return false;GeoSourceProvider p={DP_CONSUMER,"test.derived-policy-consumer","test/1",f,consumer_describe,consumer_evaluate};return geo_eval_register(f->graph,&p);}
static bool consume(Fixture *f,uint32_t request)
{GeoSourceValue value;return geo_eval_source(f->graph,(GeoSourceRef){DP_CONSUMER,&request,sizeof request},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK;}
static size_t consumer_index(Fixture *f,uint32_t request)
{
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;uint32_t key;
        if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==DP_CONSUMER&&n.source.key_size==sizeof key){memcpy(&key,n.source.key,sizeof key);if(key==request)return i;}}
    return SIZE_MAX;
}
static bool consumer_edge(Fixture *f,uint32_t request,WoodFinishSourceKind kind,uint32_t id,GeoDependencyKind relation)
{return edge_indices(f->graph,consumer_index(f,request),source_index(f->graph,kind,id),relation);}
static int policy_metadata_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach_consumer(f),"policy-metadata-fixture");unsigned facts=policy_facts(f);
    FinishSurfaceState *saved=malloc(sizeof *saved);CHECK(saved,"policy-metadata-snapshot");memcpy(saved,&f->state,sizeof *saved);
    const WoodFinishSourceKind kinds[]={WOOD_FINISH_SOURCE_DERIVED_POLICY,WOOD_FINISH_SOURCE_BOUNDARY_POLICY};
    for(size_t i=0;i<2;++i){WoodFinishSourceKey key;uint32_t id=i?8:10;GeoSourceDescriptor desc;GeoSourceNodeView node;
        GeoSourceRef ref=wood_finish_source_ref(FS_SOURCE,kinds[i],id,&key);
        CHECK(key.bytes[0]==21+i&&!memcmp(key.bytes+1,(unsigned char[]){0,0,0,(unsigned char)id},4),"policy-stable-big-endian-key");
        CHECK(geo_eval_describe(f->graph,ref,&desc)==GEO_SOURCE_OK&&desc.kind==GEO_SOURCE_DEFINITION&&desc.unit==GEO_UNIT_SCALAR&&desc.retry_failure,"policy-scalar-descriptor");
        CHECK(geo_eval_node_at(f->graph,source_index(f->graph,kinds[i],id),&node)&&node.state==GEO_NODE_NEW&&!node.value,"policy-describe-does-not-evaluate");}
    CHECK(policy_facts(f)==facts&&geo_eval_edge_count(f->graph)==0&&!memcmp(saved,&f->state,sizeof *saved),"policy-description-readonly");
    CHECK(consume(f,4),"definition-only-consumer");
    CHECK(consumer_edge(f,4,WOOD_FINISH_SOURCE_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&consumer_edge(f,4,WOOD_FINISH_SOURCE_FILL_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&consumer_edge(f,4,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"definition-only-exact-identity-edges");
    CHECK(policy_facts(f)==facts&&source_index(f->graph,WOOD_FINISH_SOURCE_DERIVED_REGION,10)==SIZE_MAX&&!memcmp(saved,&f->state,sizeof *saved),"definition-only-never-evaluates-geometry");
    free(saved);dispose(f,false);return 0;
}
static size_t expected_policy(unsigned char *bytes,bool boundary_policy)
{
    static const char *keys[]={"[[\"e0\",0,1]]","[[\"e1\",0,1]]","[[\"e2\",0,1]]","[[\"e3\",0,1]]","[[\"b20:u-\",0,1]]","[[\"b20:v+\",0,1]]","[[\"b20:u+\",0,1]]","[[\"b20:v-\",0,1]]"};
    bytes[0]=1;policy_write32(bytes+1,boundary_policy?8:10);bytes[5]=boundary_policy?WOOD_BOUNDARY_ROOM_PLAN:0;policy_write32(bytes+6,1);policy_write32(bytes+10,boundary_policy?0:1);size_t at=14;
    for(size_t h=0;h<(boundary_policy?1u:2u);++h){policy_write32(bytes+at,4);at+=4;
        for(size_t e=0;e<4;++e){size_t length=boundary_policy?0:strlen(keys[h*4+e]);bytes[at++]=WOOD_EDGE_FIXED;bytes[at++]=(unsigned char)(length>>8);bytes[at++]=(unsigned char)length;if(length){memcpy(bytes+at,keys[h*4+e],length);at+=length;}}}
    return at;
}
static int policy_graph_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach_consumer(f),"policy-graph-fixture");CHECK(consume(f,1),"policy-read-consumer");
    CHECK(consumer_edge(f,1,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"derived-policy-definition-required-edge");
    CHECK(consumer_edge(f,1,WOOD_FINISH_SOURCE_DERIVED_REGION,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&consumer_edge(f,1,WOOD_FINISH_SOURCE_DERIVED_H,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&consumer_edge(f,1,WOOD_FINISH_SOURCE_DERIVED_FRAME,10,GEO_DEPENDENCY_VALUE_REQUIRED),"consumer-reads-actual-derived-values");
    CHECK(edge(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,WOOD_FINISH_SOURCE_DERIVED_REGION,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,WOOD_FINISH_SOURCE_DERIVED_H,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,WOOD_FINISH_SOURCE_DERIVED_FRAME,10,GEO_DEPENDENCY_VALUE_REQUIRED),"policy-exact-geometry-height-frame-edges");
    CHECK(edge(f,WOOD_FINISH_SOURCE_BOUNDARY_POLICY,8,WOOD_FINISH_SOURCE_BOUNDARY_REGION,8,GEO_DEPENDENCY_VALUE_REQUIRED)&&edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_BOUNDARY_POLICY,8,GEO_DEPENDENCY_DEFINITION_REQUIRED),"boundary-policy-exact-source-edges");
    CHECK(!edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,GEO_DEPENDENCY_VALUE_REQUIRED)&&!edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"region-does-not-cycle-through-policy");
    CHECK(consume(f,2)&&consume(f,3)&&consumer_edge(f,2,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,GEO_DEPENDENCY_DEFINITION_REQUIRED)&&consumer_edge(f,3,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"key-and-resolve-consume-policy-definition");
    for(size_t i=0;i<2;++i){GeoSourceValue value;unsigned char expected[512];size_t size=expected_policy(expected,i!=0);
        CHECK(get(f,i?WOOD_FINISH_SOURCE_BOUNDARY_POLICY:WOOD_FINISH_SOURCE_DERIVED_POLICY,i?8:10,&value)&&value.kind==GEO_SOURCE_DEFINITION&&value.as.definition.content_size==size&&!memcmp(value.as.definition.content,expected,size),"policy-canonical-complete-byte-content");
        CHECK(!strcmp(value.as.definition.schema,i?"wood.finish.boundary-policy/1":"wood.finish.derived-policy/1"),"policy-exact-schema");}
    CHECK(f->writes==0&&f->active_failures==0,"policy-query-no-cache-write-or-untracked-leaf");dispose(f,true);return 0;
}
static int policy_order_case(void)
{
    Fixture *a=fixture(),*b=fixture();CHECK(a&&b&&attach(a)&&attach(b),"policy-order-fixtures");GeoSourceValue ap,ar,bp,br;
    CHECK(get(a,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&ap)&&get(a,WOOD_FINISH_SOURCE_DERIVED_REGION,10,&ar),"policy-first-does-not-cycle");
    CHECK(get(b,WOOD_FINISH_SOURCE_DERIVED_REGION,10,&br)&&get(b,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&bp),"region-first-does-not-cycle");
    WoodDerivedValue *av=malloc(sizeof *av),*bv=malloc(sizeof *bv);CHECK(av&&bv,"policy-order-values");
    CHECK(wood_finish_sources_read_derived(a->sources,10,av)&&wood_finish_sources_read_derived(b->sources,10,bv)&&exact_derived(av,30)&&exact_derived(bv,30)&&!memcmp(av,bv,sizeof *av),"both-orders-same-exact-geometry-and-fixity");
    CHECK(ap.as.definition.content_size==bp.as.definition.content_size&&!memcmp(ap.as.definition.content,bp.as.definition.content,ap.as.definition.content_size),"both-orders-identical-policy-bytes");
    free(av);free(bv);dispose(a,false);dispose(b,true);return 0;
}
static int policy_lifetime_case(void)
{
    Fixture *a=fixture(),*b=fixture();CHECK(a&&b,"policy-lifetime-fixtures");b->depth=32;b->boundary.outline.fixity[0]=WOOD_EDGE_FREE;
    CHECK(attach(a)&&attach(b)&&!wood_finish_sources_bind(a->sources,&b->context),"policy-candidates-have-independent-bindings");GeoSourceValue ap,bp,other;
    CHECK(get(a,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&ap)&&get(b,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&bp),"policy-candidate-values");
    const unsigned char *borrowed=ap.as.definition.content;unsigned char saved[512];CHECK(ap.as.definition.content_size<=sizeof saved,"policy-borrow-size");memcpy(saved,borrowed,ap.as.definition.content_size);
    CHECK(borrowed!=bp.as.definition.content&&ap.as.definition.content_size==bp.as.definition.content_size&&memcmp(borrowed,bp.as.definition.content,ap.as.definition.content_size),"same-key-candidate-policy-isolation");
    CHECK(get(a,WOOD_FINISH_SOURCE_BOUNDARY_POLICY,8,&other)&&!memcmp(borrowed,saved,ap.as.definition.content_size)&&wood_finish_sources_definitions(a->sources),"borrowed-policy-stable-across-queries");
    unsigned facts=policy_facts(a);size_t nodes=geo_eval_node_count(a->graph),edges=geo_eval_edge_count(a->graph);CHECK(geo_eval_seal(a->graph),"policy-graph-seals");
    WoodDerivedValue *value=malloc(sizeof *value);CHECK(value,"policy-sealed-value");char key[512];int hole=-99,edge_number=-99;
    CHECK(wood_finish_sources_read_derived(a->sources,10,value)&&exact_derived(value,30)&&wood_finish_sources_edge_key(a->sources,10,0,-1,0,key,sizeof key)&&wood_finish_sources_edge_resolve(a->sources,10,key,&hole,&edge_number)&&hole==-1&&edge_number==0&&wood_finish_sources_definitions(a->sources),"sealed-policy-public-queries");
    CHECK(facts==policy_facts(a)&&nodes==geo_eval_node_count(a->graph)&&edges==geo_eval_edge_count(a->graph)&&!memcmp(borrowed,saved,ap.as.definition.content_size),"sealed-policy-does-not-evaluate-or-mutate");
    CHECK(wood_finish_sources_read_derived(b->sources,10,value)&&value->derived_h==32&&value->components[0].outline.fixity[0]==WOOD_EDGE_FREE,"other-candidate-values-retained");
    free(value);dispose(a,true);dispose(b,false);return 0;
}
static int policy_keys_case(void)
{
    Fixture *f=fixture(),*plain=fixture();CHECK(f&&plain&&attach(f),"policy-key-fixtures");WoodDerivedValue *value=malloc(sizeof *value),*direct=malloc(sizeof *direct);CHECK(value&&direct,"policy-key-values");
    CHECK(wood_finish_sources_read_derived(f->sources,10,value)&&wood_dp_value_direct(&plain->context,&plain->state.hosts[0],direct),"policy-key-values-ready");
    for(int hole=-1;hole<1;++hole)for(size_t e=0;e<4;++e){char full[512];CHECK(wood_dp_edge_key_direct(&plain->context,direct,0,hole,e,full,sizeof full),"direct-key-oracle");size_t length=strlen(full),caps[]={0,1,2,3,4,length,length+1,512};
        for(size_t i=0;i<sizeof caps/sizeof caps[0];++i){char a[512],b[512];memset(a,0x5a,sizeof a);memcpy(b,a,sizeof b);strcpy(f->error,"seed");strcpy(plain->error,"seed");f->diagnostic=plain->diagnostic=FS_DIAGNOSTIC_CAPACITY;
            bool got=wood_finish_sources_edge_key(f->sources,10,0,hole,e,a,caps[i]),expected=wood_dp_edge_key_direct(&plain->context,direct,0,hole,e,b,caps[i]);
            CHECK(got==expected&&!memcmp(a,b,sizeof a)&&!strcmp(f->error,plain->error)&&f->diagnostic==plain->diagnostic,"key-full-and-small-capacity-byte-error-parity");}
        char hooked[512];CHECK(wood_dp_edge_key(&f->context,value,0,hole,e,hooked,sizeof hooked)&&!strcmp(hooked,full),"public-W-key-hook-consumes-policy");}
    char negative[512];CHECK(wood_finish_sources_edge_key(f->sources,10,0,-9,0,negative,sizeof negative)&&!strcmp(negative,"[[\"e0\",0,1]]"),"all-negative-hole-values-address-outline");
    free(value);free(direct);dispose(f,false);dispose(plain,true);return 0;
}
static int policy_resolve_case(void)
{
    Fixture *f=fixture(),*plain=fixture();CHECK(f&&plain&&attach(f),"policy-resolve-fixtures");CHECK(wood_dp_rebuild(&f->context)&&wood_dp_rebuild(&plain->context),"policy-resolve-rebuild");
    for(int h=-1;h<1;++h)for(size_t e=0;e<4;++e){char key[512];CHECK(wood_dp_edge_key_direct(&plain->context,&plain->placements[0],0,h,e,key,sizeof key),"resolve-direct-key");int ah=-99,ae=-99,bh=-99,be=-99;
        CHECK(wood_finish_sources_edge_resolve(f->sources,10,key,&ah,&ae)&&wood_dp_edge_resolve(&plain->context,&plain->placements[0],key,&bh,&be)&&ah==bh&&ae==be&&ah==h&&ae==(int)e,"unique-resolve-keeps-hole-edge-address");
        ah=ae=-99;CHECK(wood_dp_edge_resolve(&f->context,&f->placements[0],key,&ah,&ae)&&ah==h&&ae==(int)e,"public-W-resolve-hook-consumes-policy");}
    int ah=-99,ae=-99,bh=-99,be=-99;strcpy(f->error,"seed");strcpy(plain->error,"seed");
    CHECK(!wood_finish_sources_edge_resolve(f->sources,10,"stale",&ah,&ae)&&!wood_dp_edge_resolve(&plain->context,&plain->placements[0],"stale",&bh,&be)&&ah==-99&&ae==-99&&bh==-99&&be==-99&&!strcmp(f->error,plain->error),"zero-resolve-keeps-outputs-and-exact-error");dispose(f,false);dispose(plain,true);
    f=fixture();CHECK(f,"split-resolve-fixture");f->lo[0]=40;f->hi[0]=60;f->lo[1]=-10;f->hi[1]=110;CHECK(attach(f),"split-resolve-attach");
    ah=ae=-99;CHECK(wood_finish_sources_edge_resolve(f->sources,10,"[[\"e0\",1,2]]",&ah,&ae)&&ah==-1&&ae==GEO_LOOP_MAX_VERTICES,"component-outline-address-is-preserved");dispose(f,true);return 0;
}
static int returned_value_case(unsigned fault)
{
    Fixture *f=fixture();CHECK(f&&attach(f),"returned-value-fixture");GeoSourceValue policy;CHECK(get(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&policy),"returned-value-policy-primed");return_fault=fault;
    if(fault==3){char key[512];CHECK(wood_finish_sources_edge_key(f->sources,10,0,-1,0,key,sizeof key),"returned-key-query");CHECK(!strcmp(key,"[[\"e0\",0,1]]"),"actual-returned-policy-key-bytes");}
    else if(fault==4){WoodBoundaryRegion *region=malloc(sizeof *region);CHECK(region,"returned-boundary-allocation");CHECK(wood_fs_boundary(&f->context.finish,8,region),"returned-boundary-query");CHECK(region->outline.fixity[0]==WOOD_EDGE_FIXED,"actual-returned-boundary-policy-fixity");free(region);}
    else {WoodDerivedValue *value=malloc(sizeof *value);CHECK(value,"returned-value-allocation");CHECK(wood_finish_sources_read_derived(f->sources,10,value),"returned-value-query");
        if(fault==1)CHECK(value->components[0].outline.v[0].u==0,"actual-returned-region-coordinate");
        else CHECK(value->components[0].outline.fixity[0]==WOOD_EDGE_FIXED,"actual-returned-policy-fixity");free(value);}
    return_fault=0;dispose(f,false);return 0;
}
static int controlled_resolve_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach(f),"controlled-resolve-fixture");GeoSourceValue policy;CHECK(get(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&policy),"controlled-resolve-policy-primed");
    int hole=-99,edge_number=-99;return_fault=20;return_hits=0;
    CHECK(!wood_finish_sources_edge_resolve(f->sources,10,"[[\"e0\",0,1]]",&hole,&edge_number)&&return_hits==1&&hole==-1&&edge_number==GEO_LOOP_MAX_VERTICES&&!strcmp(f->error,"R41: key [[\"e0\",0,1]] matches 2 derived edges; exactly one is required"),"ambiguous-policy-keeps-last-match-before-error");
    hole=edge_number=-99;strcpy(f->error,"seed");return_fault=21;return_hits=0;
    CHECK(!wood_finish_sources_edge_resolve(f->sources,10,"[[\"e0\",0,1]]",&hole,&edge_number)&&return_hits==1&&hole==-1&&edge_number==0&&!strcmp(f->error,"seed"),"malformed-later-edge-keeps-earlier-match");
    return_fault=0;dispose(f,true);return 0;
}
static int malformed_policy_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach(f),"malformed-policy-fixture");GeoSourceValue policy;CHECK(get(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&policy),"malformed-policy-primed");
    WoodDerivedValue *value=malloc(sizeof *value),*saved=malloc(sizeof *saved);CHECK(value&&saved,"malformed-policy-output-allocation");
    for(unsigned fault=30;fault<=44;++fault){memset(value,0x5a,sizeof *value);memcpy(saved,value,sizeof *saved);return_fault=fault;return_hits=0;
        CHECK(!wood_finish_sources_read_derived(f->sources,10,value)&&return_hits==1&&!memcmp(value,saved,sizeof *value),"malformed-policy-rejected-with-output-unchanged");}
    return_fault=0;free(value);free(saved);dispose(f,false);return 0;
}
static int malformed_boundary_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach(f),"malformed-boundary-fixture");
    WoodDerivedValue *value=malloc(sizeof *value),*saved=malloc(sizeof *saved),*partial=malloc(sizeof *partial);
    CHECK(value&&saved&&partial,"malformed-boundary-output-allocation");
    CHECK(wood_finish_sources_read_derived(f->sources,10,value)&&exact_derived(value,30),"malformed-boundary-full-policy-primed");
    memcpy(saved,value,sizeof *saved);return_fault=45;return_hits=0;memset(partial,0x5a,sizeof *partial);
    CHECK(!wood_dp_value_direct(&f->context,&f->state.hosts[0],partial)&&return_hits==1&&partial->id==10&&partial->derived_fill_id==1&&partial->derived_h==30&&partial->frame.origin.z==9&&partial->component_count==0,"malformed-boundary-value-rejects-at-original-partial-output-point");
    char key[512],before[512];memset(key,0x5a,sizeof key);memcpy(before,key,sizeof before);return_hits=0;
    CHECK(!wood_dp_edge_key_direct(&f->context,value,0,-1,0,key,sizeof key)&&return_hits==1&&!memcmp(key,before,sizeof key),"malformed-boundary-key-rejects-with-bytes-unchanged");
    return_hits=0;CHECK(!wood_dp_fixities_direct(&f->context,value)&&return_hits==1&&!memcmp(value,saved,sizeof *value),"malformed-boundary-fixity-rejects-with-geometry-unchanged");
    return_fault=0;free(value);free(saved);free(partial);dispose(f,true);return 0;
}
static int malformed_utf8_case(void)
{
    Fixture *f=fixture();CHECK(f&&attach(f),"malformed-utf8-fixture");GeoSourceValue policy;
    CHECK(get(f,WOOD_FINISH_SOURCE_DERIVED_POLICY,10,&policy),"malformed-utf8-prime");
    WoodDerivedValue *value=malloc(sizeof *value),*saved=malloc(sizeof *saved);CHECK(value&&saved,"malformed-utf8-output-allocation");
    for(unsigned fault=46;fault<=50;++fault){return_fault=fault;return_hits=0;memset(value,0x5a,sizeof *value);memcpy(saved,value,sizeof *saved);
        CHECK(!wood_finish_sources_read_derived(f->sources,10,value)&&return_hits==1&&!memcmp(value,saved,sizeof *value),"malformed-utf8-policy-rejected-with-output-unchanged");
        char key[512],sentinel[512];memset(key,0x5a,sizeof key);memcpy(sentinel,key,sizeof key);return_hits=0;
        CHECK(!wood_finish_sources_edge_key(f->sources,10,0,-1,0,key,sizeof key)&&return_hits==1&&!memcmp(key,sentinel,sizeof key),"malformed-utf8-key-rejected-with-output-unchanged");}
    for(unsigned fault=51;fault<=53;++fault){return_fault=fault;return_hits=0;
        CHECK(wood_finish_sources_read_derived(f->sources,10,value)&&return_hits==1&&exact_derived(value,30),"valid-multibyte-policy-is-accepted");
        char key[512];return_hits=0;CHECK(wood_finish_sources_edge_key(f->sources,10,0,-1,0,key,sizeof key)&&return_hits==1,"valid-multibyte-key-is-accepted");
        static const unsigned char prefixes[3][4]={{0xc2,0xa2,0,0},{0xe4,0xb8,0xad,0},{0xf0,0x9f,0x98,0x80}};
        CHECK(!memcmp(key,prefixes[fault-51],fault-49),"valid-multibyte-key-is-copied-verbatim");
        int hole=-99,edge_number=-99;return_hits=0;CHECK(wood_finish_sources_edge_resolve(f->sources,10,key,&hole,&edge_number)&&return_hits==1&&hole==-1&&edge_number==0,"valid-multibyte-key-resolves");}
    int hole=-99,edge_number=-99;return_fault=54;return_hits=0;strcpy(f->error,"seed");
    CHECK(!wood_finish_sources_edge_resolve(f->sources,10,"[[\"e0\",0,1]]",&hole,&edge_number)&&return_hits==1&&hole==-1&&edge_number==0&&!strcmp(f->error,"seed"),"malformed-later-utf8-edge-keeps-earlier-match");
    return_fault=0;free(value);free(saved);dispose(f,true);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"metadata"))return policy_metadata_case();
    if(!strcmp(argv[1],"graph"))return policy_graph_case();
    if(!strcmp(argv[1],"order"))return policy_order_case();
    if(!strcmp(argv[1],"lifetime"))return policy_lifetime_case();
    if(!strcmp(argv[1],"keys"))return policy_keys_case();
    if(!strcmp(argv[1],"resolve"))return policy_resolve_case();
    if(!strcmp(argv[1],"returned-region"))return returned_value_case(1);
    if(!strcmp(argv[1],"returned-fixity"))return returned_value_case(2);
    if(!strcmp(argv[1],"returned-key"))return returned_value_case(3);
    if(!strcmp(argv[1],"returned-boundary"))return returned_value_case(4);
    if(!strcmp(argv[1],"controlled-resolve"))return controlled_resolve_case();
    if(!strcmp(argv[1],"malformed"))return malformed_policy_case();
    if(!strcmp(argv[1],"malformed-utf8"))return malformed_utf8_case();
    if(!strcmp(argv[1],"malformed-boundary"))return malformed_boundary_case();
    return 2;
}
