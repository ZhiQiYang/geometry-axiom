/* Test-only observer, inserted into a copied real bridge after all adapters.
 * No production build includes this file. Never serialize borrowed pointers. */
static void x7_hex(const void *data,size_t length)
{const unsigned char *p=data;for(size_t i=0;i<length;++i)printf("%02x",p[i]);}
static void x7_point(GeoPoint3 p)
{printf("%lld,%lld,%lld;",(long long)p.x,(long long)p.y,(long long)p.z);}
static void x7_vector(GeoVector3 p)
{printf("%lld,%lld,%lld;",(long long)p.x,(long long)p.y,(long long)p.z);}
static void x7_frame(GeoFrame f)
{x7_point(f.origin);x7_vector(f.axis_u);x7_vector(f.axis_v);x7_vector(f.normal);}
static void x7_loop(GeoLoop2View loop)
{printf("%zu:",loop.count);for(size_t i=0;i<loop.count;++i)printf("%lld,%lld;",(long long)loop.v[i].u,(long long)loop.v[i].v);}
static void x7_value(const GeoSourceValue *v)
{
    if(!v){fputs("null;",stdout);return;}
    printf("V%d:",v->kind);
    switch(v->kind){
    case GEO_SOURCE_QUANTITY:printf("%lld,%lld,%d;",(long long)v->as.quantity.num,(long long)v->as.quantity.den,v->as.quantity.unit);break;
    case GEO_SOURCE_AXIS_POSITION:printf("%lld,%d,%u,%d;",(long long)v->as.position.coordinate,v->as.position.context.has_placement,v->as.position.context.placement,v->as.position.context.axis);break;
    case GEO_SOURCE_FRAME:x7_frame(v->as.frame);break;
    case GEO_SOURCE_BOX:x7_frame(v->as.box.frame);for(int i=0;i<3;++i)printf("%lld;",(long long)v->as.box.extent[i]);break;
    case GEO_SOURCE_FEATURE:printf("%zu:",v->as.feature.key_size);x7_hex(v->as.feature.key,v->as.feature.key_size);x7_point(v->as.feature.segment.start);x7_point(v->as.feature.segment.end);break;
    case GEO_SOURCE_DEFINITION:x7_hex(v->as.definition.schema,strlen(v->as.definition.schema));printf(":%zu:",v->as.definition.content_size);x7_hex(v->as.definition.content,v->as.definition.content_size);break;
    case GEO_SOURCE_REGION_SET:
        printf("%zu:",v->as.regions.count);
        for(size_t i=0;i<v->as.regions.count;++i){const GeoRegionView *r=&v->as.regions.regions[i];x7_loop(r->outline);printf("%zu:",r->hole_count);for(size_t h=0;h<r->hole_count;++h)x7_loop(r->holes[h]);}break;
    default:fputs("UNHANDLED_KIND",stdout);break;
    }
}
static void x7_graph(void)
{
    if(!g_preview.ready||!g_preview.transaction){puts("{\"ok\":false,\"reason\":\"no retained candidate\"}");return;}
    GeoEvalContext *g=geo_candidate_sources(app_candidate_core(g_preview.transaction->control));
    printf("{\"ok\":true,\"sealed\":%s,\"nodes\":%zu,\"edges\":%zu,\"graph\":\"",geo_eval_is_sealed(g)?"true":"false",geo_eval_node_count(g),geo_eval_edge_count(g));
    for(size_t i=0;i<geo_eval_node_count(g);++i){GeoSourceNodeView n;if(!geo_eval_node_at(g,i,&n)){fputs("MISSING_NODE",stdout);continue;}
        printf("N%u:%zu:",n.source.provider,n.source.key_size);x7_hex(n.source.key,n.source.key_size);
        printf(";%d,%d,%d,%d,%d,%d,%u,%d,%d,%d;",n.state,n.status,n.described,n.descriptor.kind,n.descriptor.unit,n.descriptor.context.has_placement,n.descriptor.context.placement,n.descriptor.context.axis,n.descriptor.retry_failure,n.descriptor.context_from_value);
        x7_value(n.value);
    }
    for(size_t i=0;i<geo_eval_edge_count(g);++i){GeoSourceEdge e;if(!geo_eval_edge_at(g,i,&e)){fputs("MISSING_EDGE",stdout);continue;}printf("E%zu,%zu,%d;",e.consumer,e.source,e.kind);}
    puts("\"}");
}
static void x7_probe(const char *arg)
{
    if(arg){unsigned serial,fault,allocation;char extra;
        if(sscanf(arg,"%u %u %u %c",&serial,&fault,&allocation,&extra)!=3||serial>1||fault>2||allocation>1){puts("{\"ok\":false}");return;}
        g_x7_serial=serial;g_x7_fault=fault;g_x7_fail_snapshot=allocation;
        g_x7_full=0;g_x7_snapshot_failures=0;
    }
    printf("{\"ok\":true,\"full\":%llu,\"deferred\":%s,\"muted\":%s,\"issues\":%zu,\"snapshotFailures\":%u,\"hasBatch\":%s}\n",g_x7_full,g_reference_validation_deferred?"true":"false",g_scene_error_muted?"true":"false",g_reference_issue_count,g_x7_snapshot_failures,g_x7_has_batch?"true":"false");
}
