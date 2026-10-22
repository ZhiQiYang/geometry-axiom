/* H consumers include the real product and link the real K/W objects. Each
 * hook first calls a registered production provider, then changes its actual
 * canonical return value. K caches that value before any consumer reads it.
 * Authored World records are never used as the replacement authority. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,c) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)

enum {HF_REF=1,HF_RECT_REF,HF_REF_RECT,HF_RAW_DERIVED,HF_ACTUAL_DERIVED,HF_MOVED,HF_RC,HF_END};
typedef bool (*HostFactsEvaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
typedef struct {
    World world,before;ReferenceEval ctx;unsigned mode,bad;
    GeoPlacementDefinition actual;
    unsigned char placement[GEO_PLACEMENT_DEFINITION_MAX_BYTES],anchor[4096],column[4096],beam[4096],room[GEO_ENCLOSURE_RESULT_BYTES];
    size_t placement_size;unsigned placement_hits,anchor_hits,column_hits,beam_hits,room_hits,pose_hits;
    unsigned provider_calls[4];
    HostFactsEvaluate placement_evaluate,wood_evaluate,enclosure_evaluate,pose_evaluate;
} HostFacts;
static HostFacts *hf_active;
static void hf_be(unsigned char *bytes,size_t at,uint64_t value,size_t width)
{for(size_t i=0;i<width;++i)bytes[at+i]=(unsigned char)(value>>(8*(width-i-1)));}
static bool hf_node(GeoEvalContext *graph,GeoSourceRef ref,GeoSourceNodeView *out,size_t *index)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(graph,i,&n)&&n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&
           !memcmp(n.source.key,ref.key,ref.key_size)){if(out)*out=n;if(index)*index=i;return true;}}
    return false;
}
static bool hf_edge(GeoEvalContext *graph,GeoSourceRef consumer,GeoSourceRef source,GeoDependencyKind kind)
{
    size_t c,s;if(!hf_node(graph,consumer,NULL,&c)||!hf_node(graph,source,NULL,&s))return false;
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(graph,i,&e)&&e.consumer==c&&e.source==s&&e.kind==kind)return true;}
    return false;
}
static bool hf_placement_provider(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostFacts *f=hf_active;++f->provider_calls[0];if(!f->placement_evaluate(state,graph,ref,out))return false;
    GeoPlacementSourceKind kind;uint32_t id;
    if(geo_placement_source_decode(ref,&kind,&id)&&kind==GEO_PLACEMENT_SOURCE_DEFINITION&&id==7&&f->mode!=HF_MOVED&&f->mode!=HF_RC){
        ++f->placement_hits;out->as.definition.content=f->placement;out->as.definition.content_size=f->placement_size;
        if(f->mode==HF_END&&f->bad)out->as.definition.schema="wrong.placement/1";}
    return true;
}
static bool hf_wood_provider(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostFacts *f=hf_active;++f->provider_calls[1];if(!f->wood_evaluate(state,graph,ref,out))return false;
    WoodDefinitionKind kind;uint32_t id;if(!wood_definition_source_decode(ref,&kind,&id))return false;
    if((f->mode==HF_MOVED||f->mode==HF_END)&&kind==WOOD_DEFINITION_PLACEMENT&&id==41){
        if(out->as.definition.content_size>sizeof f->anchor)return false;
        memcpy(f->anchor,out->as.definition.content,out->as.definition.content_size);
        hf_be(f->anchor,4,7,4);hf_be(f->anchor,16,GEO_DIRECTION_POS_U,4);
        out->as.definition.content=f->anchor;++f->anchor_hits;
    }
    if(f->mode==HF_RC&&(kind==WOOD_DEFINITION_COLUMN||kind==WOOD_DEFINITION_BEAM)){
        unsigned char *bytes=kind==WOOD_DEFINITION_COLUMN?f->column:f->beam;
        if(out->as.definition.content_size>sizeof f->column)return false;
        memcpy(bytes,out->as.definition.content,out->as.definition.content_size);
        /* The documented W wire starts id, room id, optional beam axis, then
         * ordered x/y/z low/high. Rebind the real return to room 2. */
        hf_be(bytes,4,2,4);size_t at=kind==WOOD_DEFINITION_COLUMN?8:12;
        hf_be(bytes,at,70,8);hf_be(bytes,at+8,90,8);
        out->as.definition.content=bytes;
        if(kind==WOOD_DEFINITION_COLUMN)++f->column_hits;else ++f->beam_hits;
        if(f->bad&&((f->bad<=4&&kind==WOOD_DEFINITION_COLUMN)||(f->bad>=5&&f->bad<=8&&kind==WOOD_DEFINITION_BEAM))){
            unsigned fault=(f->bad-1)%4+1;
            if(fault==1)out->as.definition.schema="wrong.rc/1";
            if(fault==2)out->as.definition.schema=NULL;
            if(fault==3)hf_be(bytes,0,99,4);
            if(fault==4)--out->as.definition.content_size;
        }
    }
    return true;
}
static bool hf_enclosure_provider(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostFacts *f=hf_active;++f->provider_calls[2];if(!f->enclosure_evaluate(state,graph,ref,out))return false;
    GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
    if(f->mode==HF_RC&&geo_enclosure_source_decode(ref,&kind,&id,&axis,&slot)&&kind==GEO_ENCLOSURE_SOURCE_RESULT&&id==2){
        GeoEnclosure actual;size_t size;
        if(!geo_enclosure_source_decode_definition(kind,&out->as.definition,id,&actual))return false;
        for(size_t a=0;a<3;++a){actual.min[a]=0;actual.max[a]=100;}
        if(!geo_enclosure_source_encode_definition(kind,&actual,f->room,sizeof f->room,&size))return false;
        out->as.definition.content=f->room;out->as.definition.content_size=size;++f->room_hits;
        if(f->bad>=9){unsigned fault=f->bad-8;
            if(fault==1)out->as.definition.schema="wrong.enclosure/1";
            if(fault==2)out->as.definition.schema=NULL;
            if(fault==3)hf_be(f->room,0,99,4);
            if(fault==4)--out->as.definition.content_size;
        }
    }
    return true;
}
static bool hf_pose_provider(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    HostFacts *f=hf_active;++f->provider_calls[3];if(!f->pose_evaluate(state,graph,ref,out))return false;
    if((f->mode==HF_MOVED||f->mode==HF_END)&&out->kind==GEO_SOURCE_BOX){++f->pose_hits;out->as.box.frame.origin.y=f->mode==HF_END?40:0;}
    return true;
}
static bool hf_install(HostFacts *f)
{
    hf_active=f;if(!reference_sources_ensure(&f->ctx))return false;
    for(size_t i=0;i<geo_eval_provider_count(f->ctx.sources);++i){GeoSourceProvider *p=(GeoSourceProvider *)geo_eval_provider_at(f->ctx.sources,i);
        if(p->token==APP_SOURCE_PLACEMENT){f->placement_evaluate=p->evaluate;p->evaluate=hf_placement_provider;}
        if(p->token==APP_SOURCE_WOOD_DEFINITION){f->wood_evaluate=p->evaluate;p->evaluate=hf_wood_provider;}
        if(p->token==APP_SOURCE_ENCLOSURE){f->enclosure_evaluate=p->evaluate;p->evaluate=hf_enclosure_provider;}
        if(p->token==APP_SOURCE_MEMBER_POSE){f->pose_evaluate=p->evaluate;p->evaluate=hf_pose_provider;}
    }
    return f->placement_evaluate&&f->wood_evaluate&&f->enclosure_evaluate&&f->pose_evaluate;
}
static HostFacts *hf_fixture(unsigned mode)
{
    HostFacts *f=calloc(1,sizeof *f);if(!f)return NULL;f->mode=mode;f->ctx.world=&f->world;
    SpaceBoundarySurface b={.id=7,.outline={.v={{0,0},{100,0},{100,100},{0,100}},.count=4}};
    if(mode==HF_END){b.outline=(PolygonLoop2){.v={{0,0},{100,0},{100,50},{50,50},{50,100},{0,100}},.count=6};
        for(size_t i=0;i<6;++i)b.outline.fixity[i]=EDGE_FIXED;}
    if(!app_boundary_stage(&f->world,&b))return NULL;b.id=8;
    for(size_t i=0;i<4;++i)b.outline.fixity[i]=EDGE_FIXED;
    if(mode==HF_RECT_REF){b.hole_count=1;b.holes[0]=(PolygonLoop2){.v={{40,40},{40,60},{60,60},{60,40}},.count=4};
        for(size_t i=0;i<4;++i)b.holes[0].fixity[i]=EDGE_FIXED;}
    if(!app_boundary_stage(&f->world,&b))return NULL;
    PlacementSurface p={.id=7,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,100,100}};
    if(mode==HF_REF||mode==HF_REF_RECT||mode==HF_END)p.boundary_id=7;
    if(mode==HF_RAW_DERIVED)p.derived_fill_id=55;
    if(!app_placement_stage(&f->world,&p))return NULL;
    f->actual=*geo_placements_find(&f->world.geo.placement_data,7);
    if(mode==HF_REF||mode==HF_RECT_REF){f->actual.domain=GEO_PLACEMENT_REGION_REF;f->actual.region_id=8;}
    if(mode==HF_REF_RECT){f->actual.domain=GEO_PLACEMENT_RECT;f->actual.rect=(GeoRect2){10,20,90,80};}
    if(mode==HF_RAW_DERIVED){f->actual.domain=GEO_PLACEMENT_RECT;f->actual.rect=(GeoRect2){0,0,100,100};}
    if(mode==HF_ACTUAL_DERIVED){f->actual.domain=GEO_PLACEMENT_REGION_SET;f->actual.component_count=0;}
    f->placement_size=geo_placement_definition_encode(&f->actual,f->placement,sizeof f->placement);
    if(!f->placement_size)return NULL;
    if(mode==HF_MOVED||mode==HF_END){
        f->world.wood.timber_count=1;
        f->world.wood.timbers[0]=(WoodMember){.id=41,.length=100,.size_a=10,.size_b=5,.placed=true,.auto_length=true,
            .role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1,.origin={0,mode==HF_END?45:20,0},.axis_length={1,0,0},.axis_a={0,1,0},.axis_b={0,0,1}};
        f->world.wood.anchors[0]=(WoodMemberPlacement){.placement_id=mode==HF_END?7:8,.uv={0,mode==HF_END?45:0},.order=1,.anchor_kind=WOOD_ANCHOR_AT,
            .length_direction=mode==HF_END?GEO_DIRECTION_POS_V:99,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL};
    }
    if(mode==HF_RC){
        GeoEnclosure room={.id=1,.min={0,0,0},.max={50,50,50}};
        if(!geo_enclosures_stage(&f->world.geo.enclosures,&room))return NULL;
        room.id=2;for(size_t a=0;a<3;++a)room.max[a]=10;
        if(!geo_enclosures_stage(&f->world.geo.enclosures,&room))return NULL;
        f->world.wood.column_count=1;f->world.wood.columns[0]=(WoodColumn){.id=11,.space_id=1,.x_lo=20,.x_hi=40,.y_lo=20,.y_hi=40,.z_lo=0,.z_hi=50};
        f->world.wood.beam_count=1;f->world.wood.beams[0]=(WoodBeam){.id=12,.space_id=1,.axis=0,.x_lo=20,.x_hi=40,.y_lo=20,.y_hi=40,.z_lo=30,.z_hi=50};
    }
    memcpy(&f->before,&f->world,sizeof f->world);if(!hf_install(f))return NULL;return f;
}
static void hf_free(HostFacts *f)
{g_reference_active=NULL;reference_sources_dispose(&f->ctx);hf_active=NULL;free(f);}
static bool hf_actual_definition(HostFacts *f)
{
    GeoPlacementSourceKey key;GeoSourceNodeView node;
    return hf_node(f->ctx.sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_DEFINITION,7,&key),&node,NULL)&&
        node.value&&node.value->kind==GEO_SOURCE_DEFINITION&&node.value->as.definition.content_size==f->placement_size&&
        !memcmp(node.value->as.definition.content,f->placement,f->placement_size)&&f->placement_hits==1;
}
/* D6a(a) admits outline and hole vertex coordinates; geometry-core/README.md
 * spells them vertex:v<j>:<axis> and vertex:h<i>v<j>:<axis>. Actual hole 0 of
 * boundary 8 is (40,40) (40,60) (60,60) (60,40). Each index is read exactly:
 * a missing, non-digit or absent hole/vertex index and a foreign axis fail. */
static int hf_hole_vertex_grammar(HostFacts *f)
{
    GuideLine along_v={.id=1,.placement_id=7,.direction=GUIDE_ALONG_V},along_u={.id=1,.placement_id=7,.direction=GUIDE_ALONG_U};
    Coord u=-1,v=-1;
    CHECK("facts-hole-vertex-grammar-is-exact",reference_quantity(&f->ctx,&along_v,"vertex:h0v3:u",&u)&&u==60&&
        reference_quantity(&f->ctx,&along_u,"vertex:h0v1:v",&v)&&v==60);
    static const char *const malformed[]={"vertex:hxv0:u","vertex:hv0:u","vertex:h0:u","vertex:h0vx:u","vertex:h1v0:u","vertex:h0v4:u"};
    for(size_t i=0;i<sizeof malformed/sizeof *malformed;++i){Coord value=-1;
        CHECK("facts-hole-vertex-grammar-rejects-malformed",!reference_quantity(&f->ctx,&along_v,malformed[i],&value)&&value==-1);}
    Coord value=-1;CHECK("facts-hole-vertex-axis-must-match",!reference_quantity(&f->ctx,&along_u,"vertex:h0v0:u",&value)&&value==-1);
    return 0;
}
static int hf_host_case(unsigned mode)
{
    HostFacts *f=hf_fixture(mode);CHECK("facts-fixture",f);PlacementSurface p;SpaceBoundarySurface b;const SpaceBoundarySurface *view;
    CHECK("facts-host-read",reference_host_read(&f->ctx,7,&p,&b,&view));
    if(mode==HF_REF){CHECK("facts-ref-policy-follows-actual-region",p.boundary_id==8&&view==&b&&b.id==8&&b.outline.fixity[0]==EDGE_FIXED);
        GeoPlacementSourceKey a,d;GeoRegionSourceKey r;WoodDefinitionKey w;
        CHECK("facts-real-typed-dependencies",hf_edge(f->ctx.sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,7,&a),
            geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_DEFINITION,7,&d),GEO_DEPENDENCY_DEFINITION_REQUIRED)&&
            hf_edge(f->ctx.sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_REGIONS,7,&a),
                geo_region_source_ref(APP_SOURCE_REGION,8,&r),GEO_DEPENDENCY_VALUE_REQUIRED)&&
            hf_node(f->ctx.sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_BOUNDARY,8,&w),NULL,NULL)&&
            !hf_node(f->ctx.sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_BOUNDARY,7,&w),NULL,NULL));
    }else if(mode==HF_RECT_REF){CHECK("facts-rect-to-ref-preserves-hole",p.boundary_id==8&&view&&view->hole_count==1&&view->holes[0].v[0].u==40&&view->holes[0].fixity[0]==EDGE_FIXED);
        GuideLine guide={.id=1,.placement_id=7,.direction=GUIDE_ALONG_V};Coord value=-1;
        CHECK("facts-edge-reference-uses-actual-hole",reference_quantity(&f->ctx,&guide,"vertex:h0v0:u",&value)&&value==40);
    }else CHECK("facts-ref-to-rect-clears-boundary",p.boundary_id==0&&!view&&p.rect.min_u==10&&p.rect.min_v==20&&p.rect.max_u==90&&p.rect.max_v==80);
    CHECK("facts-actual-definition-is-k-node",hf_actual_definition(f));
    WoodGridHost grid;CHECK("facts-grid-consumes-same-host",reference_grid_host(&f->ctx,7,&grid)&&grid.boundary_id==p.boundary_id);
    AppMemberPlacementScratch scratch={0};AppMemberReferenceContext member={.world=&f->world,.evaluation=&f->ctx,.geometry=&scratch};WoodMemberPlacementFact fact;
    CHECK("facts-member-consumes-same-host",app_member_reference_placement(&member,7,&fact)&&scratch.placement.boundary_id==p.boundary_id);
    if(mode==HF_RECT_REF)CHECK("facts-member-preserves-hole",scratch.boundary_view&&scratch.boundary_view->hole_count==1);
    WoodContactSourceFacts *contacts=calloc(1,sizeof *contacts);CHECK("facts-contact-memory",contacts);WoodContactSourceRequest request={.placement_id=7};
    CHECK("facts-contact-consumes-same-host",reference_contact_facts(&f->ctx,f->ctx.sources,&request,contacts)&&contacts->region_count==1&&
        (mode==HF_REF_RECT||contacts->regions[0].id==8));
    if(mode==HF_RECT_REF)CHECK("facts-contact-preserves-hole",contacts->regions[0].hole_count==1);
    free(contacts);g_reference_active=&f->ctx;
    AppValidationInputs inputs={0};(void)app_world_validation_context(&f->world,&inputs);
    CHECK("facts-final-validator-host-consumes-same-host",app_validation_host(&inputs,7,NULL,&grid)&&grid.boundary_id==p.boundary_id);
    CHECK("facts-host-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));
    /* Last, so a control that reaches it has passed every earlier oracle. */
    if(mode==HF_RECT_REF&&hf_hole_vertex_grammar(f))return 1;
    hf_free(f);return 0;
}
static int hf_sp_case(bool lazy)
{
    HostFacts *f=hf_fixture(lazy?HF_ACTUAL_DERIVED:HF_RAW_DERIVED);CHECK("facts-sp-fixture",f);
    GeoFrame frame,saved_frame;WoodBoundaryRegion region,saved_region;memset(&frame,0x5a,sizeof frame);memset(&region,0x5a,sizeof region);
    memcpy(&saved_frame,&frame,sizeof frame);memcpy(&saved_region,&region,sizeof region);bool derived=!lazy;
    CHECK("facts-sp-actual-domain-controls-admission",reference_sp_host(&f->ctx,7,&frame,&region,&derived)&&derived==lazy);
    CHECK("facts-sp-actual-definition",hf_actual_definition(f));
    if(lazy)CHECK("facts-sp-derived-is-lazy",geo_eval_node_count(f->ctx.sources)==1&&!memcmp(&frame,&saved_frame,sizeof frame)&&!memcmp(&region,&saved_region,sizeof region));
    else CHECK("facts-sp-raw-derived-becomes-ordinary",!derived&&region.outline.count==4&&frame.axis_u.x==1);
    for(size_t i=0;i<geo_eval_node_count(f->ctx.sources);++i){GeoSourceNodeView n;CHECK("facts-sp-no-stale-finish-source",geo_eval_node_at(f->ctx.sources,i,&n)&&n.source.provider!=APP_SOURCE_FINISH);}
    CHECK("facts-sp-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);return 0;
}
static int hf_snapshot(void)
{
    HostFacts *f=hf_fixture(HF_REF);CHECK("facts-snapshot-fixture",f);f->ctx.use_current_values=true;
    PlacementSurface p;SpaceBoundarySurface b;const SpaceBoundarySurface *view;
    CHECK("facts-snapshot-host-is-raw",reference_host_read(&f->ctx,7,&p,&b,&view)&&p.boundary_id==7&&view&&view->outline.fixity[0]==EDGE_FREE);
    GeoFrame frame;WoodBoundaryRegion region;bool derived=true;
    CHECK("facts-snapshot-sp-is-raw",reference_sp_host(&f->ctx,7,&frame,&region,&derived)&&!derived&&region.id==7);
    g_reference_active=&f->ctx;CHECK("facts-snapshot-wrapper-is-raw",app_reference_host_read(&f->world,7,&p,&b,&view)&&p.boundary_id==7);
    g_reference_active=NULL;CHECK("facts-no-context-wrapper-is-raw",app_reference_host_read(&f->world,7,&p,&b,&view)&&p.boundary_id==7);
    CHECK("facts-snapshot-never-evaluates",geo_eval_node_count(f->ctx.sources)==0&&f->placement_hits==0&&!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);return 0;
}
static int hf_malformed(void)
{
    for(unsigned fault=1;fault<=4;++fault){HostFacts *f=hf_fixture(HF_REF);CHECK("facts-malformed-fixture",f);
        PlacementSurface p,saved_p;SpaceBoundarySurface b,saved_b;const SpaceBoundarySurface *view;
        CHECK("facts-malformed-prime-real-geometry",reference_host_read(&f->ctx,7,&p,&b,&view));
        GeoPlacementSourceKey key;GeoSourceNodeView node;
        CHECK("facts-malformed-cached-definition",hf_node(f->ctx.sources,geo_placement_source_ref(APP_SOURCE_PLACEMENT,GEO_PLACEMENT_SOURCE_DEFINITION,7,&key),&node,NULL)&&node.value);
        GeoSourceValue *actual=(GeoSourceValue *)node.value;
        if(fault==1)actual->as.definition.schema="wrong.placement/1";
        if(fault==2)actual->as.definition.schema=NULL;
        if(fault==3)hf_be(f->placement,0,99,4);
        if(fault==4)--actual->as.definition.content_size;
        memset(&p,0x5a,sizeof p);memset(&b,0x5a,sizeof b);memcpy(&saved_p,&p,sizeof p);memcpy(&saved_b,&b,sizeof b);view=&saved_b;
        CHECK("facts-malformed-actual-definition-is-atomic",!reference_host_read(&f->ctx,7,&p,&b,&view)&&view==&saved_b&&
            !memcmp(&p,&saved_p,sizeof p)&&!memcmp(&b,&saved_b,sizeof b)&&!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);
    }return 0;
}
static bool hf_prime_pose(HostFacts *f)
{
    /* Prime a real returned BOX through the provider's supported snapshot
     * path, so host-facts queries do not rerun placement reconstruction. */
    uint32_t id=41;GeoSourceValue value;f->ctx.use_current_values=true;
    bool ok=geo_eval_source(f->ctx.sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK;
    f->ctx.use_current_values=false;return ok&&value.kind==GEO_SOURCE_BOX&&value.as.box.frame.origin.y==(f->mode==HF_END?40:0)&&f->pose_hits==1;
}
typedef struct {
    size_t node_count,edge_count;
    GeoSourceNodeView *nodes;
    GeoSourceValue *values;
    unsigned char **keys;
    GeoSourceEdge *edges;
} HostFactsGraph;
static void hf_graph_free(HostFactsGraph *saved)
{
    if(saved->keys)for(size_t i=0;i<saved->node_count;++i)free(saved->keys[i]);
    free(saved->nodes);free(saved->values);free(saved->keys);free(saved->edges);
    memset(saved,0,sizeof *saved);
}
static bool hf_graph_save(GeoEvalContext *graph,HostFactsGraph *saved)
{
    *saved=(HostFactsGraph){.node_count=geo_eval_node_count(graph),.edge_count=geo_eval_edge_count(graph)};
    saved->nodes=calloc(saved->node_count+1,sizeof *saved->nodes);
    saved->values=calloc(saved->node_count+1,sizeof *saved->values);
    saved->keys=calloc(saved->node_count+1,sizeof *saved->keys);
    saved->edges=calloc(saved->edge_count+1,sizeof *saved->edges);
    if(!saved->nodes||!saved->values||!saved->keys||!saved->edges)return false;
    for(size_t i=0;i<saved->node_count;++i){
        if(!geo_eval_node_at(graph,i,&saved->nodes[i]))return false;
        GeoSourceNodeView *node=&saved->nodes[i];
        saved->keys[i]=malloc(node->source.key_size+1);if(!saved->keys[i])return false;
        memcpy(saved->keys[i],node->source.key,node->source.key_size);
        if(node->value)memcpy(&saved->values[i],node->value,sizeof *node->value);
    }
    for(size_t i=0;i<saved->edge_count;++i)if(!geo_eval_edge_at(graph,i,&saved->edges[i]))return false;
    return true;
}
static bool hf_graph_same(GeoEvalContext *graph,const HostFactsGraph *saved)
{
    if(geo_eval_node_count(graph)!=saved->node_count||geo_eval_edge_count(graph)!=saved->edge_count)return false;
    for(size_t i=0;i<saved->node_count;++i){GeoSourceNodeView node;
        const GeoSourceNodeView *before=&saved->nodes[i];
        if(!geo_eval_node_at(graph,i,&node)||node.source.provider!=before->source.provider||
           node.source.key_size!=before->source.key_size||memcmp(node.source.key,saved->keys[i],node.source.key_size)||
           node.descriptor.kind!=before->descriptor.kind||node.descriptor.unit!=before->descriptor.unit||
           node.descriptor.context.has_placement!=before->descriptor.context.has_placement||
           node.descriptor.context.placement!=before->descriptor.context.placement||node.descriptor.context.axis!=before->descriptor.context.axis||
           node.descriptor.retry_failure!=before->descriptor.retry_failure||node.descriptor.context_from_value!=before->descriptor.context_from_value||node.state!=before->state||
           node.status!=before->status||node.described!=before->described||(node.value==NULL)!=(before->value==NULL)||
           (node.value&&memcmp(node.value,&saved->values[i],sizeof *node.value)))return false;
    }
    for(size_t i=0;i<saved->edge_count;++i){GeoSourceEdge edge;
        const GeoSourceEdge *before=&saved->edges[i];
        if(!geo_eval_edge_at(graph,i,&edge)||edge.consumer!=before->consumer||edge.source!=before->source||edge.kind!=before->kind)return false;
    }
    return true;
}
static bool hf_loop_same(const WoodBoundaryLoop *a,const WoodBoundaryLoop *b)
{
    if(a->count!=b->count)return false;
    for(size_t i=0;i<a->count;++i)if(a->v[i].u!=b->v[i].u||a->v[i].v!=b->v[i].v||a->fixity[i]!=b->fixity[i])return false;
    return true;
}
static bool hf_contact_same(const WoodContactSourceFacts *a,const WoodContactSourceFacts *b)
{
    if(a->region_count!=b->region_count||a->member_count!=b->member_count)return false;
    for(size_t i=0;i<a->region_count;++i){const WoodBoundaryRegion *x=&a->regions[i],*y=&b->regions[i];
        if(x->id!=y->id||x->kind!=y->kind||x->hole_count!=y->hole_count||!hf_loop_same(&x->outline,&y->outline))return false;
        for(size_t h=0;h<x->hole_count;++h)if(!hf_loop_same(&x->holes[h],&y->holes[h]))return false;
    }
    for(size_t i=0;i<a->member_count;++i){const WoodContactMemberFact *x=&a->members[i],*y=&b->members[i];
        if(x->member!=y->member||x->placement_id!=y->placement_id||x->order!=y->order||x->along_v!=y->along_v||
           x->footprint_valid!=y->footprint_valid||memcmp(&x->footprint,&y->footprint,sizeof x->footprint))return false;
    }
    return true;
}
static bool hf_hits_same(const HostFacts *f,const unsigned hits[10])
{
    return f->placement_hits==hits[0]&&f->anchor_hits==hits[1]&&f->column_hits==hits[2]&&
        f->beam_hits==hits[3]&&f->room_hits==hits[4]&&f->pose_hits==hits[5]&&
        f->provider_calls[0]==hits[6]&&f->provider_calls[1]==hits[7]&&f->provider_calls[2]==hits[8]&&f->provider_calls[3]==hits[9];
}
static int hf_sealed_contacts(bool warm_pose)
{
    HostFacts *f=hf_fixture(HF_MOVED);CHECK("sealed-contact-facts-fixture",f);
    WoodContactSourceRequest request={.placement_id=7};
    WoodContactSourceFacts *warm=calloc(1,sizeof *warm),*after=calloc(1,sizeof *after);
    CHECK("sealed-contact-facts-memory",warm&&after);
    if(warm_pose){
        CHECK("sealed-contact-facts-real-returned-pose",hf_prime_pose(f));
        CHECK("sealed-contact-facts-warm",reference_contact_facts(&f->ctx,f->ctx.sources,&request,warm)&&warm->member_count==1&&
            warm->members[0].member==&f->world.wood.timbers[0]&&warm->members[0].placement_id==7&&warm->members[0].order==1&&
            warm->members[0].footprint_valid&&warm->members[0].footprint.min_u==0&&warm->members[0].footprint.max_u==100&&
            warm->members[0].footprint.min_v==0&&warm->members[0].footprint.max_v==10&&
            f->ctx.member_reads[0].footprint_valid&&f->ctx.member_reads[0].placement==7&&f->anchor_hits==1&&f->pose_hits==1);
    }else{
        PlacementSurface placement;SpaceBoundarySurface boundary;const SpaceBoundarySurface *view;WoodMemberPlacement anchor;
        CHECK("sealed-contact-facts-warm-host-only",reference_host_read(&f->ctx,7,&placement,&boundary,&view)&&
            reference_member_anchor_read(&f->ctx,0,41,&anchor)&&anchor.placement_id==7);
        uint32_t id=41;
        CHECK("sealed-contact-facts-pose-is-unknown",!hf_node(f->ctx.sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},NULL,NULL)&&
            !f->ctx.member_reads[0].footprint_valid&&f->pose_hits==0);
    }
    for(size_t i=0;i<geo_eval_node_count(f->ctx.sources);++i){GeoSourceNodeView node;
        CHECK("sealed-contact-facts-all-warmed-nodes-valid",geo_eval_node_at(f->ctx.sources,i,&node)&&
            node.state==GEO_NODE_VALID&&node.status==GEO_SOURCE_OK&&node.value);
    }
    HostFactsGraph graph;
    CHECK("sealed-contact-facts-save-full-ordered-graph",hf_graph_save(f->ctx.sources,&graph));
    unsigned hits[]={f->placement_hits,f->anchor_hits,f->column_hits,f->beam_hits,f->room_hits,f->pose_hits,
        f->provider_calls[0],f->provider_calls[1],f->provider_calls[2],f->provider_calls[3]};
    CHECK("sealed-contact-facts-seal",geo_eval_seal(f->ctx.sources)&&geo_eval_is_sealed(f->ctx.sources));
    if(warm_pose){
        CHECK("sealed-contact-facts-remain-readable",reference_contact_facts(&f->ctx,f->ctx.sources,&request,after));
        CHECK("sealed-contact-facts-preserve-all-facts",hf_contact_same(warm,after));
    }else CHECK("sealed-contact-facts-unknown-pose-stays-rejected",!reference_contact_facts(&f->ctx,f->ctx.sources,&request,after));
    CHECK("sealed-contact-facts-do-not-evaluate-providers",hf_hits_same(f,hits));
    CHECK("sealed-contact-facts-preserve-full-ordered-graph",hf_graph_same(f->ctx.sources,&graph));
    CHECK("sealed-contact-facts-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));
    hf_graph_free(&graph);free(warm);free(after);hf_free(f);return 0;
}
static int hf_moved(bool final)
{
    HostFacts *f=hf_fixture(HF_MOVED);CHECK("facts-moved-fixture",f);CHECK("facts-moved-real-returned-pose",hf_prime_pose(f));
    PlacementSurface p;GeoRect2 rect;CHECK("facts-moved-raw-footprint-is-invalid",app_placement_read(&f->world,7,&p)&&!timber_a0_footprint_uv(&p,&f->world.wood.timbers[0],&f->world.wood.anchors[0],&rect));
    CHECK("facts-moved-actual-anchor-footprint",reference_member_footprint(&f->ctx,0,7,&rect)&&rect.min_u==0&&rect.max_u==100&&rect.min_v==0&&rect.max_v==10&&f->anchor_hits==1);
    WoodContactSourceFacts *facts=calloc(1,sizeof *facts);CHECK("facts-moved-contact-memory",facts);WoodContactSourceRequest request={.placement_id=7};
    CHECK("facts-moved-contact-admits-actual-footprint",reference_contact_facts(&f->ctx,f->ctx.sources,&request,facts)&&facts->member_count==1&&
        facts->members[0].placement_id==7&&facts->members[0].footprint_valid&&facts->members[0].footprint.min_v==0);
    free(facts);g_reference_active=&f->ctx;WoodWorldMemberFact member;AppValidationInputs inputs={0};
    WoodWorldValidationContext validation=app_world_validation_context(&f->world,&inputs);
    CHECK("facts-final-validator-actual-anchor",app_validation_member(&inputs,0,&member)&&member.placement_id==7&&member.uv.v==0&&member.length_direction==GEO_DIRECTION_POS_U);
    CHECK("facts-final-validator-actual-footprint",app_validation_footprint(&inputs,0,7,&rect)&&rect.min_v==0);
    if(final){char error[256]="";
        CHECK("facts-final-world-validation-uses-actual-facts",wood_world_validate_members(&validation,error,sizeof error));
        CHECK("facts-reference-check-uses-actual-facts",reference_check_all(&f->world));
    }
    CHECK("facts-moved-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);return 0;
}
static int hf_end_faces(void)
{
    HostFacts *f=hf_fixture(HF_END);CHECK("facts-end-fixture",f);CHECK("facts-end-real-returned-pose",hf_prime_pose(f));
    g_reference_active=&f->ctx;WoodMember probe=f->world.wood.timbers[0];bool from_source=false;
    CHECK("facts-probe-consumes-actual-box",app_reference_member_geometry(&f->world,&probe,&from_source)&&from_source&&probe.id==41&&probe.origin.y==40&&f->world.wood.timbers[0].origin.y==45);
    AppValidationInputs inputs={0};(void)app_world_validation_context(&f->world,&inputs);
    CHECK("facts-probe-projects-actual-origin",app_validation_place(&inputs,7,&probe,(GeoPoint2){200,300},GEO_DIRECTION_POS_U,WOOD_DEPTH_POSITIVE_NORMAL)&&probe.origin.x==0&&probe.origin.y==40);
    PlacementSurface p;SpaceBoundarySurface b;const SpaceBoundarySurface *view;
    CHECK("facts-end-host",reference_host_read(&f->ctx,7,&p,&b,&view));
    WoodMember self={.id=17,.role=WOOD_MEMBER_ROLE_PRIMARY,.cut_priority=2,.placed=true};char error[512]="";
    CHECK("facts-delayed-refresh-controls-owner-extension",!app_reference_end_faces(&f->world,&p,view,&self,true,10,40,20,30,error,sizeof error)&&
        !strcmp(error,"V_CUT_PRIORITY：角材 17（優先級 2）端面頂到角材 41（優先級 2）側面——擋面擁有者優先級必須嚴格小於自己")&&f->anchor_hits==1);
    CHECK("facts-end-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);
    f=hf_fixture(HF_END);CHECK("facts-end-order-fixture",f);f->bad=1;g_reference_active=&f->ctx;
    CHECK("facts-end-order-raw-input",app_placement_read(&f->world,7,&p)&&app_boundary_read(&f->world,7,&b));
    strcpy(error,"untouched");
    CHECK("facts-span-error-precedes-source-failure",!app_reference_end_faces(&f->world,&p,&b,&self,false,0,100,40,50,error,sizeof error)&&
        !strcmp(error,"V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍")&&geo_eval_node_count(f->ctx.sources)==0&&f->placement_hits==0);
    CHECK("facts-source-failure-after-span-check",!app_reference_end_faces(&f->world,&p,&b,&self,true,10,40,20,30,error,sizeof error)&&
        !strcmp(error,"I8: ordered contact source evaluation failed")&&f->placement_hits==1);
    CHECK("facts-end-order-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);return 0;
}
static int hf_rc(bool malformed)
{
    unsigned count=malformed?12:1;
    for(unsigned fault=1;fault<=count;++fault){HostFacts *f=hf_fixture(HF_RC);CHECK("facts-rc-fixture",f);f->bad=malformed?fault:0;g_reference_active=&f->ctx;
        WoodSolidObstacle column,beam,saved;WoodRoomBounds room,saved_room;
        if(malformed){memset(&column,0x5a,sizeof column);memcpy(&saved,&column,sizeof saved);memset(&room,0x5a,sizeof room);memcpy(&saved_room,&room,sizeof room);
            bool ok=fault<=8?app_reference_validation_obstacle(&f->world,fault<=4,0,&column):app_reference_validation_room(&f->world,2,&room);
            CHECK("facts-rc-malformed-is-atomic",!ok&&!memcmp(&column,&saved,sizeof column)&&!memcmp(&room,&saved_room,sizeof room));
            CHECK("facts-rc-malformed-final-fails-closed",!app_world_obstacles_valid(&f->world));
        }else{
            CHECK("facts-rc-column-actual-definition",app_reference_validation_obstacle(&f->world,true,0,&column)&&column.id==11&&column.space_id==2&&column.min[0]==70&&column.max[0]==90);
            CHECK("facts-rc-beam-actual-definition",app_reference_validation_obstacle(&f->world,false,0,&beam)&&beam.id==12&&beam.space_id==2&&beam.min[0]==70&&beam.max[0]==90);
            CHECK("facts-rc-room-actual-result",app_reference_validation_room(&f->world,2,&room)&&room.min[0]==0&&room.max[0]==100&&f->room_hits==1);
            CHECK("facts-rc-final-validator-shares-facts",app_world_obstacles_valid(&f->world)&&f->column_hits==1&&f->beam_hits==1);
            f->ctx.use_current_values=true;
            CHECK("facts-rc-snapshot-is-direct",app_reference_validation_obstacle(&f->world,true,0,&column)&&column.space_id==1&&column.min[0]==20&&app_reference_validation_room(&f->world,2,&room)&&room.max[0]==10);
            g_reference_active=NULL;CHECK("facts-rc-no-context-is-direct",app_reference_validation_obstacle(&f->world,false,0,&beam)&&beam.space_id==1&&beam.min[0]==20);
        }
        CHECK("facts-rc-world-unchanged",!memcmp(&f->world,&f->before,sizeof f->world));hf_free(f);
    }return 0;
}
/* R5 snaps only to finite visible references; a hole vertex is one (D6a(a)).
 * Outline vertices are far away, so only the hole can be within the radius. */
static int hf_hole_snap(void)
{
    World *world=calloc(1,sizeof *world);CHECK("facts-snap-memory",world);
    SpaceBoundarySurface b={.id=3,.outline={.v={{0,0},{1000,0},{1000,1000},{0,1000}},.count=4},.hole_count=1};
    b.holes[0]=(PolygonLoop2){.v={{300,300},{300,600},{600,600},{600,300}},.count=4};
    PlacementSurface p={.id=4,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.boundary_id=3};
    CHECK("facts-snap-fixture",app_boundary_stage(world,&b)&&app_placement_stage(world,&p));
    char expression[REF_EXPR_MAX]="";
    CHECK("facts-snap-selects-hole-vertex-u",reference_snap(world,4,GUIDE_ALONG_V,0,303,8,expression)&&!strcmp(expression,"vertex:h0v0:u"));
    CHECK("facts-snap-selects-hole-vertex-v",reference_snap(world,4,GUIDE_ALONG_U,0,597,8,expression)&&!strcmp(expression,"vertex:h0v1:v"));
    free(world);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ref-policy"))return hf_host_case(HF_REF);
    if(!strcmp(argv[1],"rect-ref"))return hf_host_case(HF_RECT_REF);
    if(!strcmp(argv[1],"ref-rect"))return hf_host_case(HF_REF_RECT);
    if(!strcmp(argv[1],"sp-ordinary"))return hf_sp_case(false);
    if(!strcmp(argv[1],"sp-derived"))return hf_sp_case(true);
    if(!strcmp(argv[1],"snapshot"))return hf_snapshot();
    if(!strcmp(argv[1],"malformed"))return hf_malformed();
    if(!strcmp(argv[1],"moved"))return hf_moved(false);
    if(!strcmp(argv[1],"final"))return hf_moved(true);
    if(!strcmp(argv[1],"sealed-contact-facts"))return hf_sealed_contacts(true);
    if(!strcmp(argv[1],"sealed-contact-missing-pose"))return hf_sealed_contacts(false);
    if(!strcmp(argv[1],"end-facts"))return hf_end_faces();
    if(!strcmp(argv[1],"rc"))return hf_rc(false);
    if(!strcmp(argv[1],"rc-malformed"))return hf_rc(true);
    if(!strcmp(argv[1],"hole-snap"))return hf_hole_snap();
    return 2;
}
