/* PF-5: read-only spatial diagnostics of the SAME native R41 candidate.
 * No spatial definition, height, joint policy or side face is authored here.
 * Panel envelopes reuse wood_pf_clip; timber envelopes are rebuilt D4 hosts.
 * K strip queries only partition those finished regions for exact pair
 * diagnostics. These boxes never become a second cutter or World objects. */
#define PF_SPATIAL_RECT_MAX 4096
#define PF_SPATIAL_SEGMENT_MAX 4096
#define PF_SPATIAL_PAIR_WORK_MAX 1000000
typedef struct { GeoLoop2View *loops; size_t count; } PfSpatialComponent;
typedef struct { GeoCoord lo[3],hi[3]; } PfSpatialBox;
typedef struct {
    PfSpatialComponent *components; size_t count; GeoCoord area;
    GeoFrame frame; int to_finish_side; GeoCoord depth,interval[2];
    PfSpatialBox *boxes; size_t box_count; bool boxes_ready;
    const char *diagnostic_code;
} PfSpatialLayer;
typedef struct {
    const PanelFill *fill; const FinishSurface *finish;
    const DerivedPlacement *definition; const PlacementSurface *host;
    PlacementSurface host_value;
    char **edge_keys; size_t edge_key_count;
    PfLayout layout; PfSpatialLayer panel,timber;
    bool valid; const char *status,*code; char message[512];
} PfSpatialFinish;
typedef struct { GeoCoord start[3],end[3],length; } PfSpatialSegment;
typedef struct { GeoCoord volume; int dimension; bool available; } PfSpatialContact;
typedef struct {
    size_t first,second; const char *status,*code; char message[160];
    PfSpatialSegment *segments; size_t segment_count,work;
    int visible_dimension; GeoCoord gap; bool has_gap;
    PfSpatialContact layers[4];
} PfSpatialJunction;

static void pf_spatial_i64(GeoCoord value)
{printf("\"%lld\"",(long long)value);}
static void pf_spatial_coords(const GeoCoord *values,size_t count)
{putchar('[');for(size_t i=0;i<count;++i){if(i)putchar(',');pf_spatial_i64(values[i]);}putchar(']');}
static void pf_spatial_point(GeoPoint3 p)
{GeoCoord v[3]={p.x,p.y,p.z};pf_spatial_coords(v,3);}
static void pf_spatial_axis(GeoVector3 v)
{printf("[%d,%d,%d]",(int)v.x,(int)v.y,(int)v.z);}
static void pf_spatial_frame(const GeoFrame *frame)
{
    fputs("{\"origin\":",stdout);pf_spatial_point(frame->origin);
    fputs(",\"u\":",stdout);pf_spatial_axis(frame->axis_u);
    fputs(",\"v\":",stdout);pf_spatial_axis(frame->axis_v);
    fputs(",\"n\":",stdout);pf_spatial_axis(frame->normal);putchar('}');
}
static int pf_spatial_coord_order(const void *a,const void *b)
{GeoCoord x=*(const GeoCoord *)a,y=*(const GeoCoord *)b;return x<y?-1:x>y;}
static int pf_spatial_fill_order(const void *a,const void *b)
{const PanelFill *x=*(const PanelFill *const *)a,*y=*(const PanelFill *const *)b;return x->id<y->id?-1:x->id>y->id;}
static void pf_spatial_layer_free(PfSpatialLayer *layer)
{
    for(size_t i=0;i<layer->count;++i)free(layer->components[i].loops);
    free(layer->components);free(layer->boxes);memset(layer,0,sizeof *layer);
}
static void pf_spatial_finish_free(PfSpatialFinish *finish)
{
    pf_spatial_layer_free(&finish->panel);pf_spatial_layer_free(&finish->timber);pf_free(&finish->layout);
    if(finish->edge_keys)for(size_t i=0;i<finish->edge_key_count;++i)free(finish->edge_keys[i]);free(finish->edge_keys);
}
static bool pf_spatial_components(PfSpatialLayer *layer,size_t count)
{
    layer->count=count;
    if(!count)return true;
    layer->components=calloc(count,sizeof *layer->components);
    if(!layer->components){layer->count=0;return false;}
    return true;
}
static bool pf_spatial_panel(const World *w,PfSpatialFinish *finish)
{
    PfLayout *d=&finish->layout;
    if(!pf_values(w,finish->fill,d))return false;
    finish->finish=d->finish;
    const SpaceBoundarySurface *boundary=world_find_boundary(w,d->finish->boundary_id);
    if(!boundary)return fs_error("I52: PF-5 finish boundary is unavailable");
    d->layout.tiles=calloc(1,sizeof *d->layout.tiles);
    if(!d->layout.tiles)return fs_capacity_error("I33 CAPACITY: PF-5 panel envelope workspace unavailable");
    d->layout.count=1;d->keep_collinear=true;
    PfTile *tile=d->layout.tiles;GeoLoop2View outer={boundary->outline.v,boundary->outline.count};
    geo_loop_bbox(&outer,&tile->body[0],&tile->body[1],&tile->body[2],&tile->body[3]);
    if(!pf_clip(w,d,tile))return false; /* PF5_NATIVE_PANEL_CLIP */
    PfSpatialLayer *layer=&finish->panel;
    if(!pf_spatial_components(layer,tile->count))return fs_capacity_error("I33 CAPACITY: PF-5 panel component views unavailable");
    layer->frame=d->frame;
    layer->frame.normal=(d->finish->side>0?d->frame.normal:geo_vector_negate(d->frame.normal)); /* PF5_NATIVE_PANEL_NORMAL */
    layer->to_finish_side=1;layer->depth=d->t;layer->interval[1]=d->t;layer->area=tile->area;
    for(size_t c=0;c<tile->count;++c){const PfFragment *part=&tile->fragments[c];PfSpatialComponent *out=&layer->components[c];
        out->loops=calloc(part->count,sizeof *out->loops);if(!out->loops)return fs_capacity_error("I33 CAPACITY: PF-5 panel ring views unavailable");out->count=part->count;
        for(size_t l=0;l<part->count;++l)out->loops[l]=(GeoLoop2View){part->loops[l].points,part->loops[l].count};
    }
    return true;
}
static GeoCoord pf_spatial_area2(const GeoLoop2View *loop)
{
    GeoCoord sum=0;
    for(size_t i=0;i<loop->count;++i){GeoPoint2 p=loop->v[i],q=loop->v[(i+1)%loop->count];sum+=p.u*q.v-q.u*p.v;}
    return sum<0?-sum:sum;
}
static bool pf_spatial_timber(const World *w,PfSpatialFinish *finish)
{
    for(uint64_t i=0;i<w->wood.finish_surfaces.host_count;++i)
        if(w->wood.finish_surfaces.hosts[i].fill_id==finish->fill->id){finish->definition=&w->wood.finish_surfaces.hosts[i];break;}
    if(!finish->definition)return true;
    finish->host=app_placement_read(w,finish->definition->id,&finish->host_value);
    if(!finish->host||finish->host->derived_fill_id!=finish->fill->id)
        return fs_error("I55/D4: PF-5 derived placement does not resolve to its source fill");
    const PlacementSurface *host=finish->host;PfSpatialLayer *layer=&finish->timber;
    if(!pf_spatial_components(layer,host->component_count))return fs_capacity_error("I33 CAPACITY: PF-5 host component views unavailable");
    layer->frame=host->frame;layer->to_finish_side=finish->finish->side;layer->depth=host->derived_h;
    layer->interval[0]=finish->layout.t;layer->interval[1]=finish->layout.t+host->derived_h;
    for(size_t c=0;c<host->component_count;++c){const SpaceBoundarySurface *b=&host->components[c];PfSpatialComponent *out=&layer->components[c];
        out->loops=calloc(b->hole_count+1,sizeof *out->loops);if(!out->loops)return fs_capacity_error("I33 CAPACITY: PF-5 host ring views unavailable");out->count=b->hole_count+1;
        GeoCoord area2=0;
        for(size_t l=0;l<out->count;++l){const PolygonLoop2 *loop=l?&b->holes[l-1]:&b->outline;out->loops[l]=(GeoLoop2View){loop->v,loop->count};
            GeoCoord a=pf_spatial_area2(&out->loops[l]);area2+=l?-a:a;}
        layer->area+=area2/2;
    }
    return true;
}
/* K supplies a complete disjoint strip partition of the already clipped
 * region. The diagnostic capacity is explicit; no partial partition is used. */
static bool pf_spatial_boxes(PfSpatialLayer *layer)
{
    if(!layer->count){layer->boxes_ready=true;return true;}
    layer->boxes=calloc(PF_SPATIAL_RECT_MAX,sizeof *layer->boxes);
    if(!layer->boxes){layer->diagnostic_code="SPATIAL_WORKSPACE";return false;}
    for(size_t c=0;c<layer->count;++c){const PfSpatialComponent *part=&layer->components[c];size_t vertices=0;
        for(size_t l=0;l<part->count;++l){
            if(part->loops[l].count>GEO_LOOP_MAX_VERTICES||part->count>GEO_REGION_MAX_HOLES+1){layer->diagnostic_code="SPATIAL_REGION_CAPACITY";return false;}
            vertices+=part->loops[l].count;
        }
        GeoCoord *levels=calloc(vertices,sizeof *levels),*cuts=calloc(vertices,sizeof *cuts);
        GeoInterval *intervals=calloc(vertices,sizeof *intervals);
        if(!levels||!cuts||!intervals){free(levels);free(cuts);free(intervals);layer->diagnostic_code="SPATIAL_WORKSPACE";return false;}
        size_t count=0;
        for(size_t l=0;l<part->count;++l)for(size_t p=0;p<part->loops[l].count;++p)levels[count++]=part->loops[l].v[p].v;
        qsort(levels,count,sizeof *levels,pf_spatial_coord_order);size_t unique=0;
        for(size_t i=0;i<count;++i)if(!unique||levels[i]!=levels[unique-1])levels[unique++]=levels[i];
        GeoRegionView region={part->loops[0],part->loops+1,part->count-1};GeoRegionSetView domain={&region,1};bool ok=true;
        for(size_t b=0;b+1<unique&&ok;++b){GeoIntervalBuffer result={intervals,vertices,0};GeoStripScratch scratch={cuts,vertices};
            if(geo_strip_intervals(&domain,false,(GeoInterval){levels[b],levels[b+1]},NULL,0,&result,scratch)!=GEO_GEOMETRY_OK){layer->diagnostic_code="SPATIAL_REGION_CAPACITY";ok=false;break;}
            for(size_t i=0;i<result.count;++i){
                if(layer->box_count>=PF_SPATIAL_RECT_MAX){layer->diagnostic_code="SPATIAL_REGION_CAPACITY";ok=false;break;}
                GeoPoint3 a=geo_frame_point(&layer->frame,result.items[i].start,levels[b],0);
                GeoPoint3 z=geo_frame_point(&layer->frame,result.items[i].end,levels[b+1],layer->depth);
                GeoCoord av[3]={a.x,a.y,a.z},zv[3]={z.x,z.y,z.z};PfSpatialBox *box=&layer->boxes[layer->box_count++];
                for(int k=0;k<3;++k){box->lo[k]=av[k]<zv[k]?av[k]:zv[k];box->hi[k]=av[k]>zv[k]?av[k]:zv[k];}
            }
        }
        free(levels);free(cuts);free(intervals);if(!ok)return false;
    }
    layer->boxes_ready=true;return true;
}
static bool pf_spatial_coordinates_in_range(const PfSpatialLayer *layer)
{
    for(size_t c=0;c<layer->count;++c)for(size_t l=0;l<layer->components[c].count;++l){const GeoLoop2View *loop=&layer->components[c].loops[l];
        for(size_t i=0;i<loop->count;++i)for(int end=0;end<2;++end){GeoPoint3 p=geo_frame_point(&layer->frame,loop->v[i].u,loop->v[i].v,end?layer->depth:0);
            if(!geo_coord_in_range(p.x)||!geo_coord_in_range(p.y)||!geo_coord_in_range(p.z))return false;
        }
    }
    return true;
}
/* The complete native keys must be known before a status/complete flag is
 * emitted. Cache exact successful bytes; never invent a key or print null. */
static bool pf_spatial_host_keys(const World *w,PfSpatialFinish *finish)
{
    if(!finish->host)return true;
    for(size_t c=0;c<finish->host->component_count;++c){const SpaceBoundarySurface *b=&finish->host->components[c];
        finish->edge_key_count+=b->outline.count;for(size_t h=0;h<b->hole_count;++h)finish->edge_key_count+=b->holes[h].count;
    }
    if(!finish->edge_key_count)return true;
    finish->edge_keys=calloc(finish->edge_key_count,sizeof *finish->edge_keys);
    if(!finish->edge_keys)return false;
    size_t index=0;
    for(size_t c=0;c<finish->host->component_count;++c){const SpaceBoundarySurface *b=&finish->host->components[c];
        for(size_t h=0;h<=b->hole_count;++h){const PolygonLoop2 *loop=h?&b->holes[h-1]:&b->outline;
            for(size_t e=0;e<loop->count;++e){char key[512];
                if(!dp_edge_key(w,finish->host,c,h?(int)h-1:-1,e,key,sizeof key))return false;
                size_t length=strlen(key);finish->edge_keys[index]=malloc(length+1);if(!finish->edge_keys[index])return false;
                memcpy(finish->edge_keys[index],key,length+1);++index;
            }
        }
    }
    return true;
}
static void pf_spatial_finish_build(const World *w,const PanelFill *fill,PfSpatialFinish *out)
{
    out->fill=fill;out->finish=fs_find(w,fill->finish_id);out->status="invalid";
    if(!pf_spatial_panel(w,out)||!pf_spatial_timber(w,out)){
        out->code=g_fs_diagnostic==FS_DIAGNOSTIC_CAPACITY?"SPATIAL_CAPACITY":"SPATIAL_SOURCE_INVALID";
        out->status=g_fs_diagnostic==FS_DIAGNOSTIC_CAPACITY?"unsupported":"invalid";
        snprintf(out->message,sizeof out->message,"%s",g_engineering_error);return;
    }
    if(!pf_spatial_coordinates_in_range(&out->panel)||(out->host&&!pf_spatial_coordinates_in_range(&out->timber))){
        out->code="SPATIAL_COORD_CAPACITY";out->status="unsupported";
        snprintf(out->message,sizeof out->message,"A complete native layer projection exceeds D1; no partial or clamped geometry is returned");return;
    }
    if(!pf_spatial_host_keys(w,out)){
        out->code="SPATIAL_EDGE_KEY_UNAVAILABLE";out->status="unsupported";
        snprintf(out->message,sizeof out->message,"Complete native R41 edge identities are unavailable; no partial or substitute keys are returned");return;
    }
    out->valid=true;out->status=out->host?"complete":"pending";
    pf_spatial_boxes(&out->panel);if(out->host)pf_spatial_boxes(&out->timber);
}
static GeoPoint2 pf_spatial_loop_point(const PfSpatialLayer *layer,const GeoLoop2View *loop,size_t index)
{
    /* Reflection changes winding; choose the corresponding original vertex
     * before reflecting so source/host rings stay valid in finish coordinates. */
    return loop->v[layer->to_finish_side<0?(loop->count-index)%loop->count:index];
}
static void pf_spatial_loop_json(const PfSpatialLayer *layer,const GeoLoop2View *loop,int output,GeoCoord depth)
{
    putchar('[');
    for(size_t i=0;i<loop->count;++i){if(i)putchar(',');GeoPoint2 uv=pf_spatial_loop_point(layer,loop,i);
        if(output<0){GeoCoord p[2]={uv.u,uv.v*layer->to_finish_side};pf_spatial_coords(p,2);}
        else{GeoPoint3 point=geo_frame_point(&layer->frame,uv.u,uv.v,depth);
            GeoCoord xyz[3]={point.x,point.y,point.z};
            if(output==3)pf_spatial_coords(xyz,3);
            else {GeoCoord p[2]={xyz[output==2?1:0],xyz[output==0?1:2]};pf_spatial_coords(p,2);}
        }
    }
    putchar(']');
}
static void pf_spatial_rings_json(const PfSpatialLayer *layer,const PfSpatialComponent *part,int output,GeoCoord depth)
{
    fputs("{\"outer\":",stdout);pf_spatial_loop_json(layer,&part->loops[0],output,depth);fputs(",\"holes\":[",stdout);
    for(size_t l=1;l<part->count;++l){if(l>1)putchar(',');pf_spatial_loop_json(layer,&part->loops[l],output,depth);}fputs("]}",stdout);
}
static void pf_spatial_layer_json(const PfSpatialLayer *layer)
{
    fputs("{\"status\":\"complete\",\"interval\":",stdout);pf_spatial_coords(layer->interval,2);
    fputs(",\"area\":",stdout);pf_spatial_i64(layer->area);fputs(",\"components\":[",stdout);
    for(size_t c=0;c<layer->count;++c){if(c)putchar(',');const PfSpatialComponent *part=&layer->components[c];
        fputs("{\"outer\":",stdout);pf_spatial_loop_json(layer,&part->loops[0],-1,0);fputs(",\"holes\":[",stdout);
        for(size_t l=1;l<part->count;++l){if(l>1)putchar(',');pf_spatial_loop_json(layer,&part->loops[l],-1,0);}fputs("],\"world\":{\"near\":",stdout);
        pf_spatial_rings_json(layer,part,3,0);fputs(",\"far\":",stdout);pf_spatial_rings_json(layer,part,3,layer->depth);fputs("},\"projections\":{",stdout);
        const char *names[3]={"top","front","side"};
        for(int p=0;p<3;++p){if(p)putchar(',');js_string(names[p]);fputs(":{\"near\":",stdout);pf_spatial_rings_json(layer,part,p,0);fputs(",\"far\":",stdout);pf_spatial_rings_json(layer,part,p,layer->depth);putchar('}');}
        fputs("}}",stdout);
    }
    fputs("]}",stdout);
}
static const char *pf_spatial_obstacle_relation(const FsObstacleView *view,GeoCoord a,GeoCoord b)
{
    GeoCoord lo=view->q[0]>a?view->q[0]:a,hi=view->q[1]<b?view->q[1]:b;
    if(view->relation==FS_INTERIOR&&lo<hi)return "cut";
    if(view->relation!=FS_SEPARATE&&lo<=hi)return "touch";
    return "clear";
}
static void pf_spatial_host_json(const PfSpatialFinish *finish)
{
    const PlacementSurface *p=finish->host;const PfSpatialLayer *layer=&finish->timber;
    printf("{\"id\":%u,\"definition\":%s,\"frame\":",p->id,finish->definition->definition);pf_spatial_frame(&p->frame);
    fputs(",\"h\":",stdout);pf_spatial_i64(p->derived_h);fputs(",\"region\":{\"area\":",stdout);pf_spatial_i64(layer->area);fputs(",\"components\":[",stdout);
    size_t key_index=0;
    for(size_t c=0;c<p->component_count;++c){if(c)putchar(',');const SpaceBoundarySurface *b=&p->components[c];PfSpatialLayer identity=*layer;identity.to_finish_side=1;
        fputs("{\"outer\":",stdout);pf_spatial_loop_json(&identity,&layer->components[c].loops[0],-1,0);fputs(",\"holes\":[",stdout);
        for(size_t l=1;l<layer->components[c].count;++l){if(l>1)putchar(',');pf_spatial_loop_json(&identity,&layer->components[c].loops[l],-1,0);}fputs("],\"edges\":[",stdout);bool first=true;
        for(size_t h=0;h<=b->hole_count;++h){const PolygonLoop2 *loop=h?&b->holes[h-1]:&b->outline;
            for(size_t e=0;e<loop->count;++e){if(!first)putchar(',');first=false;fputs("{\"key\":",stdout);fputs(finish->edge_keys[key_index++],stdout);
                GeoCoord start[2]={loop->v[e].u,loop->v[e].v},end[2]={loop->v[(e+1)%loop->count].u,loop->v[(e+1)%loop->count].v};
                fputs(",\"start\":",stdout);pf_spatial_coords(start,2);fputs(",\"end\":",stdout);pf_spatial_coords(end,2);printf(",\"fixity\":\"%s\"}",loop->fixity[e]==EDGE_FREE?"FREE":"FIXED");
            }
        }
        fputs("]}",stdout);
    }
    fputs("]}}",stdout);
}
static void pf_spatial_finish_json(const World *w,const PfSpatialFinish *finish)
{
    printf("{\"id\":%u,\"finishId\":%u,\"status\":",finish->fill->id,finish->fill->finish_id);js_string(finish->status);
    fputs(",\"missing\":[",stdout);if(finish->valid&&!finish->host)js_string("derived-placement.h");fputs("],\"label\":",stdout);js_string(finish->finish?finish->finish->name:"");
    if(!finish->valid){fputs(",\"error\":{\"code\":",stdout);js_string(finish->code);fputs(",\"message\":",stdout);js_string(finish->message);fputs("},\"panel\":null,\"timber\":null,\"host\":null}",stdout);return;}
    fputs(",\"frame\":",stdout);pf_spatial_frame(&finish->finish->frame);printf(",\"side\":%d,\"thickness\":",finish->finish->side);pf_spatial_i64(finish->layout.t);
    fputs(",\"panelVersion\":{\"id\":",stdout);js_string(finish->fill->panel.id);printf(",\"version\":%u},\"h\":",finish->fill->panel.version);
    if(finish->host)pf_spatial_i64(finish->host->derived_h);else fputs("null",stdout);
    fputs(",\"hostId\":",stdout);if(finish->host)printf("%u",finish->host->id);else fputs("null",stdout);
    fputs(",\"obstacles\":[",stdout);
    for(uint32_t i=0;i<finish->finish->obstacle_count;++i){if(i)putchar(',');const FinishObstacleRef *ref=&finish->finish->obstacles[i];const FsObstacleView *view=&finish->layout.obstacles[i];char name[16];fs_obstacle_text(ref,name);
        fputs("{\"ref\":",stdout);js_string(name);fputs(",\"projectedRect\":",stdout);pf_spatial_coords(view->rect,4);fputs(",\"normalInterval\":",stdout);pf_spatial_coords(view->q,2);
        fputs(",\"footprintRelation\":",stdout);js_string(view->relation==FS_INTERIOR?"overlap":fs_relation_name(view->relation));fputs(",\"panel\":",stdout);js_string(pf_spatial_obstacle_relation(view,0,finish->layout.t));fputs(",\"timber\":",stdout);
        if(finish->host)js_string(pf_spatial_obstacle_relation(view,finish->layout.t,finish->layout.t+finish->host->derived_h));else fputs("null",stdout);
        Coord lo[3],hi[3];
        if(fs_obstacle_box(w,ref,lo,hi)){fputs(",\"world\":{\"min\":",stdout);pf_spatial_coords(lo,3);fputs(",\"max\":",stdout);pf_spatial_coords(hi,3);fputs("},\"projections\":{",stdout);
            const char *names[3]={"top","front","side"};for(int p=0;p<3;++p){if(p)putchar(',');js_string(names[p]);putchar(':');int x=p==2?1:0,y=p==0?1:2;GeoCoord rect[4]={lo[x],lo[y],hi[x],hi[y]};pf_spatial_coords(rect,4);}putchar('}');
        }
        putchar('}');
    }
    fputs("],\"panel\":",stdout);pf_spatial_layer_json(&finish->panel);fputs(",\"timber\":",stdout);if(finish->host)pf_spatial_layer_json(&finish->timber);else fputs("null",stdout);
    fputs(",\"host\":",stdout);if(finish->host)pf_spatial_host_json(finish);else fputs("null",stdout);putchar('}');
}

static void pf_spatial_surface_box(const PfSpatialLayer *layer,const PfSpatialBox *solid,PfSpatialBox *surface)
{
    *surface=*solid;GeoCoord origin[3]={layer->frame.origin.x,layer->frame.origin.y,layer->frame.origin.z};GeoCoord normal[3]={layer->frame.normal.x,layer->frame.normal.y,layer->frame.normal.z};
    for(int k=0;k<3;++k)if(normal[k])surface->lo[k]=surface->hi[k]=origin[k];
}
static int pf_spatial_box_dimension(const PfSpatialBox *a,const PfSpatialBox *b,GeoCoord widths[3])
{
    int dimension=0;
    for(int k=0;k<3;++k){GeoCoord lo=a->lo[k]>b->lo[k]?a->lo[k]:b->lo[k],hi=a->hi[k]<b->hi[k]?a->hi[k]:b->hi[k];if(lo>hi)return -1;widths[k]=hi-lo;if(lo<hi)++dimension;}
    return dimension;
}
static bool pf_spatial_layer_contact(const PfSpatialLayer *a,const PfSpatialLayer *b,PfSpatialContact *out)
{
    out->dimension=-1;out->available=true;
    for(size_t i=0;i<a->box_count;++i)for(size_t j=0;j<b->box_count;++j){GeoCoord widths[3];int dimension=pf_spatial_box_dimension(&a->boxes[i],&b->boxes[j],widths);
        if(dimension>out->dimension)out->dimension=dimension;
        if(dimension==3){GeoCoord volume=1;
            for(int k=0;k<3;++k){if(volume>INT64_MAX/widths[k])return false;volume*=widths[k];}
            if(out->volume>INT64_MAX-volume)return false;out->volume+=volume;
        }
    }
    return true;
}
static int pf_spatial_segment_axis(const PfSpatialSegment *segment)
{for(int k=0;k<3;++k)if(segment->start[k]!=segment->end[k])return k;return -1;}
static int pf_spatial_segment_order(const void *left,const void *right)
{
    const PfSpatialSegment *a=left,*b=right;
    for(int k=0;k<3;++k)if(a->start[k]!=b->start[k])return a->start[k]<b->start[k]?-1:1;
    for(int k=0;k<3;++k)if(a->end[k]!=b->end[k])return a->end[k]<b->end[k]?-1:1;return 0;
}
static PfSpatialSegment pf_spatial_segment(const PfSpatialLayer *layer,const GeoLoop2View *loop,size_t index)
{
    GeoPoint2 u=loop->v[index],v=loop->v[(index+1)%loop->count];GeoPoint3 a=geo_frame_point(&layer->frame,u.u,u.v,0),b=geo_frame_point(&layer->frame,v.u,v.v,0);
    PfSpatialSegment result={{a.x,a.y,a.z},{b.x,b.y,b.z},0};int axis=pf_spatial_segment_axis(&result);
    if(axis>=0&&result.start[axis]>result.end[axis]){GeoCoord swap=result.start[axis];result.start[axis]=result.end[axis];result.end[axis]=swap;}
    if(axis>=0)result.length=result.end[axis]-result.start[axis];return result;
}
static bool pf_spatial_shared_edges(const PfSpatialLayer *a,const PfSpatialLayer *b,PfSpatialJunction *out)
{
    out->segments=calloc(PF_SPATIAL_SEGMENT_MAX,sizeof *out->segments);if(!out->segments)return false;
    for(size_t ac=0;ac<a->count;++ac)for(size_t al=0;al<a->components[ac].count;++al){const GeoLoop2View *av=&a->components[ac].loops[al];
        for(size_t ai=0;ai<av->count;++ai){PfSpatialSegment as=pf_spatial_segment(a,av,ai);int axis=pf_spatial_segment_axis(&as);
            for(size_t bc=0;bc<b->count;++bc)for(size_t bl=0;bl<b->components[bc].count;++bl){const GeoLoop2View *bv=&b->components[bc].loops[bl];
                for(size_t bi=0;bi<bv->count;++bi){if(++out->work>PF_SPATIAL_PAIR_WORK_MAX)return false;PfSpatialSegment bs=pf_spatial_segment(b,bv,bi);
                    if(axis<0||pf_spatial_segment_axis(&bs)!=axis)continue;bool same=true;
                    for(int k=0;k<3;++k)if(k!=axis&&as.start[k]!=bs.start[k])same=false;if(!same)continue;
                    GeoCoord lo=as.start[axis]>bs.start[axis]?as.start[axis]:bs.start[axis],hi=as.end[axis]<bs.end[axis]?as.end[axis]:bs.end[axis];
                    if(lo>=hi)continue; /* PF5_NATIVE_SHARED_EDGE_INTERSECTION */
                    if(out->segment_count>=PF_SPATIAL_SEGMENT_MAX)return false;
                    PfSpatialSegment *segment=&out->segments[out->segment_count++];*segment=as;segment->start[axis]=lo;segment->end[axis]=hi;segment->length=hi-lo;
                }
            }
        }
    }
    /* Merge touching/overlapping collinear subsegments; source fixity breaks
     * remain untouched in the separately emitted native host edge keys. */
    for(size_t i=0;i<out->segment_count;++i){PfSpatialSegment *a=&out->segments[i];int axis=pf_spatial_segment_axis(a);
        for(size_t j=i+1;j<out->segment_count;){if(++out->work>PF_SPATIAL_PAIR_WORK_MAX)return false;PfSpatialSegment *b=&out->segments[j];bool same=axis==pf_spatial_segment_axis(b);
            for(int k=0;k<3&&same;++k)if(k!=axis&&a->start[k]!=b->start[k])same=false;
            if(same&&a->start[axis]<=b->end[axis]&&b->start[axis]<=a->end[axis]){
                if(b->start[axis]<a->start[axis])a->start[axis]=b->start[axis];if(b->end[axis]>a->end[axis])a->end[axis]=b->end[axis];a->length=a->end[axis]-a->start[axis];
                memmove(b,b+1,(out->segment_count-j-1)*sizeof *b);--out->segment_count;j=i+1;
            }else ++j;
        }
    }
    qsort(out->segments,out->segment_count,sizeof *out->segments,pf_spatial_segment_order);return true;
}
static void pf_spatial_junction_failure(PfSpatialJunction *out,const char *code,const char *message)
{out->status="unsupported";out->code=code;snprintf(out->message,sizeof out->message,"%s",message);}
static void pf_spatial_junction_build(const PfSpatialFinish *a,const PfSpatialFinish *b,PfSpatialJunction *out)
{
    out->status="complete";out->visible_dimension=-1;
    if(!a->valid||!b->valid){pf_spatial_junction_failure(out,"SPATIAL_SOURCE_UNAVAILABLE","Complete native source layers are unavailable; no empty or separate relation is inferred");return;}
    if(!a->panel.boxes_ready||!b->panel.boxes_ready){pf_spatial_junction_failure(out,"SPATIAL_REGION_CAPACITY","Complete native region exceeds the bounded pair diagnostic partition");return;}
    if(a->panel.box_count&&b->panel.box_count>PF_SPATIAL_PAIR_WORK_MAX/a->panel.box_count){pf_spatial_junction_failure(out,"SPATIAL_PAIR_CAPACITY","Complete pair diagnostic exceeds the declared work capacity");return;}
    out->work=a->panel.box_count*b->panel.box_count;
    for(size_t i=0;i<a->panel.box_count;++i)for(size_t j=0;j<b->panel.box_count;++j){PfSpatialBox ab,bb;GeoCoord widths[3],gap=0;
        pf_spatial_surface_box(&a->panel,&a->panel.boxes[i],&ab);pf_spatial_surface_box(&b->panel,&b->panel.boxes[j],&bb);
        int dimension=pf_spatial_box_dimension(&ab,&bb,widths);if(dimension>out->visible_dimension)out->visible_dimension=dimension;
        for(int k=0;k<3;++k){if(ab.hi[k]<bb.lo[k])gap+=bb.lo[k]-ab.hi[k];else if(bb.hi[k]<ab.lo[k])gap+=ab.lo[k]-bb.hi[k];}
        if(!out->has_gap||gap<out->gap){out->gap=gap;out->has_gap=true;}
    }
    if(!pf_spatial_shared_edges(&a->panel,&b->panel,out)){pf_spatial_junction_failure(out,"SPATIAL_PAIR_CAPACITY","Complete shared-edge diagnostic exceeds the declared work capacity");return;}
    for(int k=0;k<4;++k){const PfSpatialLayer *x=k/2?&a->timber:&a->panel,*y=k%2?&b->timber:&b->panel;
        if((k/2&&!a->host)||(k%2&&!b->host)){out->status="pending";continue;}
        if(!x->boxes_ready||!y->boxes_ready){pf_spatial_junction_failure(out,"SPATIAL_REGION_CAPACITY","Complete native region exceeds the bounded pair diagnostic partition");return;}
        if(x->box_count&&y->box_count>(PF_SPATIAL_PAIR_WORK_MAX-out->work)/x->box_count){pf_spatial_junction_failure(out,"SPATIAL_PAIR_CAPACITY","Complete pair diagnostic exceeds the declared work capacity");return;}
        out->work+=x->box_count*y->box_count;
        if(!pf_spatial_layer_contact(x,y,&out->layers[k])){pf_spatial_junction_failure(out,"SPATIAL_VOLUME_CAPACITY","Exact overlap volume exceeds signed int64; no rounded or truncated volume is returned");return;}
    }
}
static void pf_spatial_junction_json(const PfSpatialFinish *finishes,const PfSpatialJunction *junction)
{
    printf("{\"finishes\":[%u,%u],\"status\":",finishes[junction->first].fill->id,finishes[junction->second].fill->id);js_string(junction->status);
    fputs(",\"joinPolicy\":\"unselected\"",stdout);
    if(junction->code){fputs(",\"error\":{\"code\":",stdout);js_string(junction->code);fputs(",\"message\":",stdout);js_string(junction->message);fputs("}}",stdout);return;}
    fputs(",\"missing\":[",stdout);if(!strcmp(junction->status,"pending"))js_string("complete-panel-and-derived-placement");fputs("],\"sharedEdges\":[",stdout);
    for(size_t i=0;i<junction->segment_count;++i){if(i)putchar(',');const PfSpatialSegment *segment=&junction->segments[i];fputs("{\"start\":",stdout);pf_spatial_coords(segment->start,3);fputs(",\"end\":",stdout);pf_spatial_coords(segment->end,3);fputs(",\"length\":",stdout);pf_spatial_i64(segment->length);putchar('}');}
    printf("],\"visibleContactDimension\":%d,\"minimumL1Gap\":",junction->visible_dimension);if(junction->has_gap)pf_spatial_i64(junction->gap);else fputs("null",stdout);
    fputs(",\"layers\":{",stdout);const char *names[4]={"panel-panel","panel-timber","timber-panel","timber-timber"};
    for(int k=0;k<4;++k){if(k)putchar(',');js_string(names[k]);putchar(':');const PfSpatialContact *contact=&junction->layers[k];if(!contact->available){fputs("null",stdout);continue;}
        fputs("{\"volume\":",stdout);pf_spatial_i64(contact->volume);printf(",\"contactDimension\":%d,\"relation\":\"%s\"}",contact->dimension,contact->volume?"overlap":contact->dimension>=0?"touch":"separate");
    }
    fputs("}}",stdout);
}
static void json_panel_fill_spatial(const World *w,bool valid,const char *failure)
{
    FsDiagnosticKind saved_kind=g_fs_diagnostic;char saved_error[sizeof g_engineering_error];snprintf(saved_error,sizeof saved_error,"%s",g_engineering_error);
    PfSpatialFinish *finishes=NULL;PfSpatialJunction *junctions=NULL;size_t count=w->wood.finish_surfaces.fill_count,pair_count=0;bool complete=valid;
    if(valid){finishes=calloc(count?count:1,sizeof *finishes);junctions=calloc(count>1?count*(count-1)/2:1,sizeof *junctions);if(!finishes||!junctions){valid=false;complete=false;failure="PF-5 diagnostic workspace unavailable";}}
    if(valid){
        const PanelFill *ordered[FS_MAX];for(size_t i=0;i<count;++i)ordered[i]=&w->wood.finish_surfaces.fills[i];qsort(ordered,count,sizeof *ordered,pf_spatial_fill_order);
        for(size_t i=0;i<count;++i){pf_spatial_finish_build(w,ordered[i],&finishes[i]);if(strcmp(finishes[i].status,"complete"))complete=false;}
        for(size_t i=0;i<count;++i)for(size_t j=i+1;j<count;++j){PfSpatialJunction *pair=&junctions[pair_count++];pair->first=i;pair->second=j;pf_spatial_junction_build(&finishes[i],&finishes[j],pair);if(strcmp(pair->status,"complete"))complete=false;}
    }
    printf("{\"schema\":\"panel-fill-spatial/1\",\"scope\":\"diagnostic-envelope-only\",\"complete\":%s,\"selection\":\"existing-panel-fills\",\"capacity\":{\"rectanglesPerLayer\":%d,\"sharedSegmentsPerPair\":%d,\"geometryComparisonsPerPair\":%d,\"pairLoopVertices\":%d,\"pairHolesPerComponent\":%d,\"volumeMax\":\"%lld\"},\"finishes\":[",complete?"true":"false",PF_SPATIAL_RECT_MAX,PF_SPATIAL_SEGMENT_MAX,PF_SPATIAL_PAIR_WORK_MAX,GEO_LOOP_MAX_VERTICES,GEO_REGION_MAX_HOLES,(long long)INT64_MAX);
    if(valid)for(size_t i=0;i<count;++i){if(i)putchar(',');pf_spatial_finish_json(w,&finishes[i]);}fputs("],\"junctions\":[",stdout);
    if(valid)for(size_t i=0;i<pair_count;++i){if(i)putchar(',');pf_spatial_junction_json(finishes,&junctions[i]);}fputs("],\"errors\":[",stdout);bool first=true;
    if(!valid){fputs("{\"fillId\":null,\"finishes\":null,\"code\":\"CANDIDATE_UNAVAILABLE\",\"message\":",stdout);js_string(failure?failure:"Candidate is invalid; no stale derived host is reported");putchar('}');first=false;}
    if(valid)for(size_t i=0;i<count;++i)if(finishes[i].code){if(!first)putchar(',');first=false;printf("{\"fillId\":%u,\"finishes\":null,\"code\":",finishes[i].fill->id);js_string(finishes[i].code);fputs(",\"message\":",stdout);js_string(finishes[i].message);putchar('}');}
    if(valid)for(size_t i=0;i<pair_count;++i)if(junctions[i].code){if(!first)putchar(',');first=false;printf("{\"fillId\":null,\"finishes\":[%u,%u],\"code\":",finishes[junctions[i].first].fill->id,finishes[junctions[i].second].fill->id);js_string(junctions[i].code);fputs(",\"message\":",stdout);js_string(junctions[i].message);putchar('}');}
    fputs("]}",stdout);
    if(finishes)for(size_t i=0;i<count;++i)pf_spatial_finish_free(&finishes[i]);if(junctions)for(size_t i=0;i<pair_count;++i)free(junctions[i].segments);free(finishes);free(junctions);
    snprintf(g_engineering_error,sizeof g_engineering_error,"%s",saved_error);g_fs_diagnostic=saved_kind;
}
