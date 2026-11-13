#include "definition_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
enum {TOKEN=19,REGION=14,PLACEMENT=13,ENCLOSURE=18};
typedef struct {
    WoodDocument *document;GeoRegionStore *regions;GeoPlacementStore *placements;GeoEnclosureStore *enclosures;
    GeoEvalContext *graph;GeoPlacementSources *geometry;GeoEnclosureSources *enclosure;WoodDefinitionSources *sources;
} Fixture;
static bool init(Fixture *f,uint64_t candidate)
{
    memset(f,0,sizeof *f);f->document=calloc(1,sizeof *f->document);f->regions=geo_regions_create();f->placements=geo_placements_create();f->enclosures=geo_enclosures_create();f->graph=geo_eval_create(candidate,7);
    if(!f->document||!f->regions||!f->placements||!f->enclosures||!f->graph)return false;
    GeoRegionDefinition region={.id=7,.outline={{{0,0},{1000,0},{1000,800},{0,800}},4}};
    GeoPlacementDefinition placement={.id=9,.frame={{3,4,5},{1,0,0},{0,1,0},{0,0,1}},.domain=GEO_PLACEMENT_REGION_REF,.region_id=7};
    GeoEnclosure enclosure={.id=5,.member_ids={7},.member_count=1};
    if(!geo_regions_put(f->regions,&region)||!geo_placements_put(f->placements,&placement,f->regions)||!geo_enclosures_stage(f->enclosures,&enclosure))return false;
    WoodDocument *d=f->document;d->boundary_policy[0].id=7;d->boundary_policy[0].kind=WOOD_BOUNDARY_ROOM_PLAN;
    int fixes[]={1,0,-13,1};for(int i=0;i<4;++i)d->boundary_policy[0].fixity[0][i]=(WoodEdgeFixity)fixes[i];
    d->timber_count=3;d->timbers[0]=(WoodMember){.id=11,.size_a=40,.size_b=50,.role=WOOD_MEMBER_ROLE_CUSTOM,.cut_priority=9,.auto_length=true};
    d->anchors[0]=(WoodMemberPlacement){.placement_id=9,.anchor_kind=WOOD_ANCHOR_AT_EDGE,.span_mode=WOOD_SPAN_AUTO,.length_direction=GEO_DIRECTION_NEG_V,.depth_side=WOOD_DEPTH_NEGATIVE_NORMAL,.ref_hole=-1,.ref_edge=2,.has_through=true,.through=-27,.order=UINT64_MAX-1,.has_between=true};
    d->anchors[0].between[0]=(WoodMemberReferenceFace){.kind=0,.hole=-1,.edge=3};d->anchors[0].between[1]=(WoodMemberReferenceFace){.kind=1,.timber=31};
    d->anchors[0].ref_rule=(GeoGridRuleLineRef){.grid_id=6,.system_id=4,.rule_key=8,.cell={-7,INT64_MIN},.axis=1,.inner_index=3};
    strcpy(d->anchors[0].ref_derived_key,"boundary:7/outline/segment:2/total:4");strcpy(d->anchors[0].between[0].key,"edge/segment:0/total:1");
    d->timbers[1]=(WoodMember){.id=12,.size_a=999,.size_b=17,.role=WOOD_MEMBER_ROLE_PRIMARY,.cut_priority=2,.auto_length=true};
    d->engineering.binding_count=1;d->engineering.bindings[0].target=(EngTarget){1,12,0,0};
    d->timbers[2]=(WoodMember){.id=13,.size_a=27,.size_b=33,.auto_length=true};
    d->assembly.owner_count=1;d->assembly.owners[0].timber=13;
    d->column_count=1;d->columns[0]=(WoodColumn){29,5,-10,20,-30,40,-50,60};
    d->beam_count=1;d->beams[0]=(WoodBeam){31,0,1,1,2,3,4,5,6};
    f->geometry=geo_placement_sources_register(f->graph,f->placements,f->regions,PLACEMENT,REGION,NULL,NULL);
    f->enclosure=geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,ENCLOSURE,PLACEMENT,REGION);
    WoodDefinitionContext context={d,f->regions,ENCLOSURE,REGION};f->sources=wood_definition_sources_create(f->graph,TOKEN,&context);
    return f->geometry&&f->enclosure&&f->sources;
}
static void drop(Fixture *f,bool graph_first)
{if(graph_first)geo_eval_destroy(f->graph);wood_definition_sources_destroy(f->sources);geo_enclosure_sources_destroy(f->enclosure);geo_placement_sources_destroy(f->geometry);if(!graph_first)geo_eval_destroy(f->graph);geo_enclosures_destroy(f->enclosures);geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);free(f->document);}
static GeoSourceRef ref(WoodDefinitionKind k,uint32_t id,WoodDefinitionKey *key)
{return wood_definition_source_ref(TOKEN,k,id,key);}
static size_t node(Fixture *f,GeoSourceRef ref)
{for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView n;if(geo_eval_node_at(f->graph,i,&n)&&n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&!memcmp(n.source.key,ref.key,ref.key_size))return i;}return SIZE_MAX;}
static bool edge(Fixture *f,size_t from,size_t to,GeoDependencyKind kind)
{for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge e;if(geo_eval_edge_at(f->graph,i,&e)&&e.consumer==from&&e.source==to&&e.kind==kind)return true;}return false;}
static bool definition(Fixture *f,WoodDefinitionKind kind,uint32_t id,GeoSourceValue *out)
{WoodDefinitionKey key;return geo_eval_source(f->graph,ref(kind,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;}
static int codec(void)
{
    Fixture f;CHECK(init(&f,71),"fixture");WoodDefinitionKey key;GeoSourceRef r=ref(WOOD_DEFINITION_COLUMN,0x01020304,&key);
    const unsigned char expected[]={5,1,2,3,4};CHECK(r.key_size==5&&!memcmp(r.key,expected,5),"stable-five-byte-key");
    WoodDefinitionKind kind=WOOD_DEFINITION_BEAM;uint32_t id=99;CHECK(wood_definition_source_decode(&r,&kind,&id)&&kind==WOOD_DEFINITION_COLUMN&&id==0x01020304,"key-roundtrip");
    r.key_size=4;CHECK(!wood_definition_source_decode(&r,&kind,&id)&&kind==WOOD_DEFINITION_COLUMN&&id==0x01020304,"invalid-key-preserves-outputs");
    WoodMemberDefinition m;CHECK(wood_definition_sources_member(f.sources,11,&m)&&m.id==11&&m.role==WOOD_MEMBER_ROLE_CUSTOM&&m.priority==9&&m.auto_length&&m.literal[0]&&m.literal[1]&&m.dimension[0]==40&&m.dimension[1]==50,"member-authored-values");
    GeoCoord value;CHECK(wood_definition_sources_dimension(f.sources,11,false,&value)&&value==40,"literal-actual-quantity");
    WoodMemberPlacement a;CHECK(wood_definition_sources_placement(f.sources,11,&a)&&a.placement_id==9&&a.anchor_kind==WOOD_ANCHOR_AT_EDGE&&a.span_mode==WOOD_SPAN_AUTO&&a.length_direction==GEO_DIRECTION_NEG_V&&a.depth_side==WOOD_DEPTH_NEGATIVE_NORMAL&&a.ref_hole==-1&&a.ref_edge==2&&a.through==-27&&a.order==UINT64_MAX-1&&a.has_between&&a.between[1].timber==31&&a.ref_rule.cell[1]==INT64_MIN&&!strcmp(a.ref_derived_key,f.document->anchors[0].ref_derived_key),"full-anchor-authored-values");
    WoodColumn c;WoodBeam b;CHECK(wood_definition_sources_column(f.sources,29,&c)&&c.space_id==5&&c.x_lo==-10&&c.z_hi==60,"RC-authored-column");CHECK(wood_definition_sources_beam(f.sources,31,&b)&&b.axis==1&&b.z_lo==5,"RC-authored-beam");
    WoodBoundaryPolicy p;CHECK(wood_definition_sources_boundary(f.sources,7,&p)&&p.id==7&&p.kind==WOOD_BOUNDARY_ROOM_PLAN&&p.fixity[0][1]==0&&(int)p.fixity[0][2]==-13,"actual-boundary-fixity");
    GeoSourceValue bytes;CHECK(definition(&f,WOOD_DEFINITION_COLUMN,29,&bytes)&&bytes.as.definition.content_size==56,"column-canonical-size");
    const unsigned char prefix[]={0,0,0,29,0,0,0,5,255,255,255,255,255,255,255,246};CHECK(!memcmp(bytes.as.definition.content,prefix,sizeof prefix),"canonical-signed-integers");drop(&f,true);return 0;
}
static int graph(void)
{
    Fixture f;CHECK(init(&f,72),"fixture");GeoCoord width;WoodColumn column;WoodBoundaryPolicy boundary;
    CHECK(wood_definition_sources_dimension(f.sources,11,false,&width),"quantity");WoodDefinitionKey a,b;size_t quantity=node(&f,ref(WOOD_DEFINITION_MEMBER_A,11,&a)),declaration=node(&f,ref(WOOD_DEFINITION_MEMBER,11,&b));
    CHECK(edge(&f,quantity,declaration,GEO_DEPENDENCY_DEFINITION_REQUIRED),"literal-declaration-identity-edge");
    CHECK(wood_definition_sources_column(f.sources,29,&column),"column");GeoEnclosureSourceKey ek;size_t enclosure=node(&f,geo_enclosure_source_ref(ENCLOSURE,GEO_ENCLOSURE_SOURCE_DEFINITION,5,-1,-1,&ek));
    CHECK(edge(&f,node(&f,ref(WOOD_DEFINITION_COLUMN,29,&a)),enclosure,GEO_DEPENDENCY_DEFINITION_REQUIRED),"RC-room-definition-only-edge");
    GeoSourceNodeView n;CHECK(geo_eval_node_at(f.graph,enclosure,&n)&&n.state==GEO_NODE_NEW&&!n.value,"RC-does-not-force-live-room-height");
    CHECK(wood_definition_sources_boundary(f.sources,7,&boundary),"boundary");GeoRegionSourceKey rk;CHECK(edge(&f,node(&f,ref(WOOD_DEFINITION_BOUNDARY,7,&a)),node(&f,geo_region_source_ref(REGION,7,&rk)),GEO_DEPENDENCY_VALUE_REQUIRED),"boundary-actual-region-value-edge");
    CHECK(wood_definition_sources_complete(f.sources),"complete-unused-definitions");
    CHECK(node(&f,ref(WOOD_DEFINITION_MEMBER_A,12,&a))==SIZE_MAX&&node(&f,ref(WOOD_DEFINITION_MEMBER_B,13,&a))==SIZE_MAX,"unused-bound-owned-quantities-not-demanded");
    CHECK(node(&f,ref(WOOD_DEFINITION_MEMBER,13,&a))!=SIZE_MAX&&node(&f,ref(WOOD_DEFINITION_PLACEMENT,12,&a))!=SIZE_MAX,"unused-authored-definitions-present");drop(&f,false);return 0;
}
static int canonical(void)
{
    Fixture a,b;CHECK(init(&a,73)&&init(&b,74),"fixture");
    WoodMember *m=&b.document->timbers[0];m->placed=true;m->length=654;m->origin=(GeoPoint3){77,88,99};m->axis_a=(GeoVector3){0,-1,0};
    b.document->anchors[0].uv=(GeoPoint2){987,654};b.document->boundary_policy[0].fixity[0][20]=WOOD_EDGE_FIXED;b.document->timbers[1].size_a=-91;b.document->timbers[2].size_b=-51;
    WoodDefinitionKind kinds[]={WOOD_DEFINITION_MEMBER,WOOD_DEFINITION_PLACEMENT,WOOD_DEFINITION_COLUMN,WOOD_DEFINITION_BEAM,WOOD_DEFINITION_BOUNDARY};uint32_t ids[]={11,11,29,31,7};
    for(size_t i=0;i<5;++i){GeoSourceValue av,bv;CHECK(definition(&a,kinds[i],ids[i],&av)&&definition(&b,kinds[i],ids[i],&bv),"read-canonical");CHECK(av.as.definition.content_size==bv.as.definition.content_size&&!memcmp(av.as.definition.content,bv.as.definition.content,av.as.definition.content_size),"rebuilt-caches-excluded-from-definitions");}
    for(uint32_t id=12;id<=13;++id){GeoSourceValue av,bv;CHECK(definition(&a,WOOD_DEFINITION_MEMBER,id,&av)&&definition(&b,WOOD_DEFINITION_MEMBER,id,&bv)&&av.as.definition.content_size==bv.as.definition.content_size&&!memcmp(av.as.definition.content,bv.as.definition.content,av.as.definition.content_size),"bound-owned-dimensions-are-not-literals");}
    b.document->columns[0].x_lo=400;WoodColumn column;CHECK(wood_definition_sources_column(a.sources,29,&column)&&column.x_lo==-10,"candidate-isolation");
    CHECK(geo_eval_seal(a.graph),"seal");CHECK(wood_definition_sources_column(a.sources,29,&column)&&column.x_lo==-10,"memo-owned-definition-survives-other-reads");
    drop(&b,false);CHECK(wood_definition_sources_column(a.sources,29,&column)&&column.x_lo==-10,"independent-candidate-lifetime");drop(&a,true);return 0;
}
static int failure(void)
{
    Fixture f;CHECK(init(&f,75),"fixture");WoodDocument *before=malloc(sizeof *before);CHECK(before,"snapshot");memcpy(before,f.document,sizeof *before);
    WoodDefinitionKey key;GeoSourceDescriptor desc;CHECK(geo_eval_describe(f.graph,ref(WOOD_DEFINITION_MEMBER,11,&key),&desc)==GEO_SOURCE_OK&&!memcmp(before,f.document,sizeof *before)&&geo_eval_edge_count(f.graph)==0,"describe-is-read-only");
    WoodColumn out;memset(&out,0x56,sizeof out);WoodColumn prior=out;CHECK(!wood_definition_sources_column(f.sources,98,&out)&&!memcmp(&out,&prior,sizeof out),"missing-preserves-output");
    GeoCoord n=191;CHECK(!wood_definition_sources_dimension(f.sources,12,false,&n)&&n==191,"bound-is-not-literal");
    CHECK(!wood_definition_sources_dimension(f.sources,13,true,&n)&&n==191,"owned-is-not-literal");
    CHECK(!memcmp(before,f.document,sizeof *before),"queries-never-mutate-authored-store");free(before);drop(&f,false);return 0;
}
/* Intercept the registered production provider after it returns. The bytes
 * below are the real graph's cached definition, not a replacement evaluator
 * or a macro around geo_eval_source. Authored placement storage stays intact. */
typedef struct {
    Fixture fixture;
    bool (*evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
    unsigned calls;
    unsigned char bytes[4096],original[4096];
    size_t size,lengths[3];
    GeoSourceValue canonical,*cached;
} ContactViewProbe;
static ContactViewProbe *contact_view_active;
static void contact_view_be(unsigned char *bytes,uint64_t value,size_t count)
{for(size_t i=0;i<count;++i)bytes[i]=(unsigned char)(value>>(8*(count-i-1)));}
static bool contact_view_evaluate(void *state,GeoEvalContext *graph,const GeoSourceRef *source,GeoSourceValue *out)
{
    ContactViewProbe *p=contact_view_active;
    if(!p||!p->evaluate(state,graph,source,out))return false;
    WoodDefinitionKind kind;uint32_t id;
    if(wood_definition_source_decode(source,&kind,&id)&&kind==WOOD_DEFINITION_PLACEMENT&&id==11){
        if(out->kind!=GEO_SOURCE_DEFINITION||out->as.definition.content_size>sizeof p->bytes)return false;
        p->size=out->as.definition.content_size;
        memcpy(p->bytes,out->as.definition.content,p->size);
        /* Distinct values prove both readers consume the returned definition,
         * rather than copying the original document's placement fields. */
        contact_view_be(p->bytes+4,UINT32_MAX,4);contact_view_be(p->bytes+16,99,4);
        contact_view_be(p->bytes+131+p->lengths[0],UINT64_MAX,8);
        out->as.definition.content=p->bytes;++p->calls;
    }
    return true;
}
static int contact_view_init(ContactViewProbe *p,const size_t lengths[3])
{
    memset(p,0,sizeof *p);CHECK(init(&p->fixture,76),"contact-view-fixture");
    WoodMemberPlacement *a=&p->fixture.document->anchors[0];char *texts[]={a->ref_derived_key,a->between[0].key,a->between[1].key};
    for(size_t t=0;t<3;++t){p->lengths[t]=lengths[t];CHECK(lengths[t]<512,"contact-view-test-length");
        for(size_t i=0;i<lengths[t];++i)texts[t][i]=(char)('a'+(i+t)%26);texts[t][lengths[t]]=0;}
    a->has_between=false; /* Inactive between fields must still be decoded. */
    for(size_t i=0;i<geo_eval_provider_count(p->fixture.graph);++i){
        GeoSourceProvider *provider=(GeoSourceProvider *)geo_eval_provider_at(p->fixture.graph,i);
        if(provider->token==TOKEN){p->evaluate=provider->evaluate;provider->evaluate=contact_view_evaluate;}
    }
    CHECK(p->evaluate,"contact-view-production-provider");contact_view_active=p;
    GeoSourceValue value;CHECK(definition(&p->fixture,WOOD_DEFINITION_PLACEMENT,11,&value),"contact-view-prime-real-definition");
    WoodDefinitionKey key;GeoSourceNodeView cached;size_t index=node(&p->fixture,ref(WOOD_DEFINITION_PLACEMENT,11,&key));
    CHECK(index!=SIZE_MAX&&geo_eval_node_at(p->fixture.graph,index,&cached)&&cached.value&&
        cached.state==GEO_NODE_VALID&&cached.value->kind==GEO_SOURCE_DEFINITION&&
        cached.value->as.definition.content==p->bytes&&p->calls==1,"contact-view-real-cached-bytes");
    CHECK(p->size==180+lengths[0]+lengths[1]+lengths[2],"contact-view-canonical-wire-size");
    p->cached=(GeoSourceValue *)cached.value;p->canonical=*cached.value;
    memcpy(p->original,p->bytes,p->size);return 0;
}
static void contact_view_restore(ContactViewProbe *p)
{*p->cached=p->canonical;memcpy(p->bytes,p->original,p->size);}
static int contact_view_values(ContactViewProbe *p)
{
    WoodMemberPlacement full;WoodMemberPlacementContact contact;
    CHECK(wood_definition_sources_placement(p->fixture.sources,11,&full),"contact-view-valid-full");
    CHECK(wood_definition_sources_placement_contact(p->fixture.sources,11,&contact),"contact-view-valid-narrow");
    CHECK(full.placement_id==UINT32_MAX&&contact.placement_id==full.placement_id,"contact-view-placement-id-value");
    CHECK(full.length_direction==99&&contact.length_direction==full.length_direction,"contact-view-direction-value");
    CHECK(full.order==UINT64_MAX&&contact.order==full.order,"contact-view-order-value");
    CHECK(p->calls==1&&geo_eval_node_count(p->fixture.graph)==1&&geo_eval_edge_count(p->fixture.graph)==0,
        "contact-view-shared-cached-source-identity");return 0;
}
static int contact_view_reject(ContactViewProbe *p,const char *label)
{
    WoodMemberPlacement full;WoodMemberPlacementContact contact;
    unsigned char full_before[sizeof full],contact_before[sizeof contact];
    memset(&full,0x56,sizeof full);memset(&contact,0x6b,sizeof contact);
    memcpy(full_before,&full,sizeof full);memcpy(contact_before,&contact,sizeof contact);
    CHECK(!wood_definition_sources_placement(p->fixture.sources,11,&full)&&!memcmp(&full,full_before,sizeof full),label);
    CHECK(!wood_definition_sources_placement_contact(p->fixture.sources,11,&contact)&&!memcmp(&contact,contact_before,sizeof contact),label);
    CHECK(p->calls==1&&geo_eval_node_count(p->fixture.graph)==1,"contact-view-errors-keep-cached-source");return 0;
}
static int contact_view(void)
{
    const size_t lengths[][3]={{0,0,0},{1,511,0},{511,0,1},{511,511,511}};
    for(size_t family=0;family<sizeof lengths/sizeof *lengths;++family){
        ContactViewProbe p;if(contact_view_init(&p,lengths[family]))return 1;
        WoodMemberPlacement authored;memcpy(&authored,&p.fixture.document->anchors[0],sizeof authored);
        if(contact_view_values(&p))return 1;
        CHECK(!wood_definition_sources_placement(p.fixture.sources,11,NULL)&&
            !wood_definition_sources_placement_contact(p.fixture.sources,11,NULL)&&p.calls==1,"contact-view-null-output");
        /* Exact trailing size is independent of every other format guard. */
        p.bytes[p.size]=0x5a;p.cached->as.definition.content_size=p.size+1;
        if(contact_view_reject(&p,"contact-view-trailing-rejected"))return 1;
        for(size_t size=0;size<p.size;++size){contact_view_restore(&p);p.cached->as.definition.content_size=size;
            if(contact_view_reject(&p,"contact-view-every-truncation-rejected"))return 1;}
        if(family==3){
            const size_t prefix[]={127,156+511,176+511+511};
            const char *capacity_labels[]={"contact-view-text0-capacity","contact-view-text1-capacity","contact-view-text2-capacity"};
            for(size_t text=0;text<3;++text){
                /* Materialize the 512th byte and shift the remaining complete
                 * wire so only the text-capacity guard can reject this case. */
                contact_view_restore(&p);size_t end=prefix[text]+4+511;
                memmove(p.bytes+end+1,p.bytes+end,p.size-end);p.bytes[end]='z';
                contact_view_be(p.bytes+prefix[text],512,4);p.cached->as.definition.content_size=p.size+1;
                if(contact_view_reject(&p,capacity_labels[text]))return 1;
                contact_view_restore(&p);contact_view_be(p.bytes+prefix[text],UINT32_MAX,4);
                if(contact_view_reject(&p,"contact-view-u32-text-length-rejected"))return 1;
            }
            /* Reader acceptance includes embedded NUL/high bytes; it consumes
             * the declared length, including the inactive between strings. */
            const size_t content[]={131,160+511,180+511+511};
            for(size_t text=0;text<3;++text){contact_view_restore(&p);p.bytes[content[text]]=0;p.bytes[content[text]+1]=0xff;
                if(contact_view_values(&p))return 1;}
        }
        contact_view_restore(&p);contact_view_be(p.bytes,12,4);
        if(contact_view_reject(&p,"contact-view-id-rejected"))return 1;
        const char *schemas[]={NULL,"","wood.rc-column/1","wood.member.placement/2"};
        for(size_t s=0;s<sizeof schemas/sizeof *schemas;++s){contact_view_restore(&p);p.cached->as.definition.schema=schemas[s];
            if(contact_view_reject(&p,"contact-view-schema-rejected"))return 1;}
        contact_view_restore(&p);p.cached->kind=GEO_SOURCE_BOX;
        if(contact_view_reject(&p,"contact-view-value-kind-rejected"))return 1;
        contact_view_restore(&p);p.cached->as.definition.content=NULL;
        if(contact_view_reject(&p,"contact-view-null-content-rejected"))return 1;
        CHECK(!memcmp(&authored,&p.fixture.document->anchors[0],sizeof authored),"contact-view-authored-store-unchanged");
        contact_view_restore(&p);if(contact_view_values(&p))return 1;
        drop(&p.fixture,family&1);contact_view_active=NULL;
    }
    return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"codec"))return codec();if(!strcmp(argv[1],"graph"))return graph();if(!strcmp(argv[1],"canonical"))return canonical();if(!strcmp(argv[1],"failure"))return failure();if(!strcmp(argv[1],"contact-view"))return contact_view();return 2;}
