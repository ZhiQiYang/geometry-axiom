/* Host selection and compatibility diagnostics for the actual K/W evaluators. */
#define PF_TILE_MAX WOOD_PANEL_TILE_MAX
#define PF_AXIS_MAX GEO_CLIP_AXIS_MAX
#define PF_EDGE_MAX GEO_CLIP_EDGE_MAX
#define PF_VERTEX_MAX WOOD_PANEL_VERTEX_MAX
typedef WoodPanelLoop PfLoop;
typedef WoodPanelFragment PfFragment;
typedef WoodPanelTile PfTile;
typedef WoodPanelSeamLine PfSeamLine;
typedef struct {
    WoodPanelLayout layout;Coord t;const FinishSurface *finish;
    FsObstacleView obstacles[FS_OBSTACLE_MAX];bool cuts[FS_OBSTACLE_MAX];bool keep_collinear;
} PfLayout;
static const PanelFill *pf_find(const World *w,uint32_t id)
{ for(uint64_t i=0;i<w->finish_surfaces.fill_count;++i)if(w->finish_surfaces.fills[i].id==id)return &w->finish_surfaces.fills[i];return NULL; }
static void pf_free(PfLayout *d)
{wood_panel_layout_free(&d->layout);memset(d,0,sizeof *d);}
static bool pf_source(GeoJson *j,int t,Coord *value,ParameterRef *ref)
{
    if(geo_json_integer(j,t,value))return coord_in_range(*value)||fs_error("I52/D1: panel-fill source outside D1");
    ref->set=true;
    return (geo_json_keys(j,t,"parameterId,fieldId","")&&parameter_u32(j,geo_json_member(j,t,"parameterId"),&ref->parameter_id)&&parameter_u32(j,geo_json_member(j,t,"fieldId"),&ref->field_id))||fs_error("D42: source must be integer mm or ParameterRef");
}
static bool pf_parse(GeoJson *j,int t,PanelFill *p)
{
    memset(p,0,sizeof *p);int axis;char pattern[16];
    int o=geo_json_member(j,t,"origin"),s=geo_json_member(j,t,"stagger"),x=geo_json_member(j,t,"threshold");
    if(!geo_json_keys(j,t,"id,finishSurfaceId,panel,lengthAlong,origin,gap,pattern,threshold","stagger")||
       !eng_u32(j,geo_json_member(j,t,"id"),&p->id,true)||!eng_u32(j,geo_json_member(j,t,"finishSurfaceId"),&p->finish_id,true)||
       !eng_ref_parse(j,geo_json_member(j,t,"panel"),&p->panel,false)||!eng_axis(j,geo_json_member(j,t,"lengthAlong"),&axis)||!axis||
       !geo_json_is_array(j,o)||geo_json_size(j,o)!=2||!geo_json_integer(j,geo_json_at(j,o,0),&p->origin[0])||!coord_in_range(p->origin[0])||!geo_json_integer(j,geo_json_at(j,o,1),&p->origin[1])||!coord_in_range(p->origin[1])||
       !geo_json_string(j,geo_json_member(j,t,"pattern"),pattern,sizeof pattern))return fs_error("D42: invalid panel-fill definition");
    p->length_axis=axis-1;p->stagger_axis=-1;
    if(!pf_source(j,geo_json_member(j,t,"gap"),&p->gap,&p->gap_ref))return false;
    if(!strcmp(pattern,"stagger")){
        if(!geo_json_keys(j,s,"axis,value","")||!eng_axis(j,geo_json_member(j,s,"axis"),&axis)||!axis)return fs_error("D42: stagger needs one axis and source");
        p->stagger_axis=axis-1;if(!pf_source(j,geo_json_member(j,s,"value"),&p->stagger,&p->stagger_ref))return false;
    }else if(strcmp(pattern,"straight")||s>=0)return fs_error("D42: straight must omit stagger; pattern must be straight or stagger");
    p->threshold.set=true;
    if(!geo_json_keys(j,x,"parameterId,fieldId","")||!parameter_u32(j,geo_json_member(j,x,"parameterId"),&p->threshold.parameter_id)||!parameter_u32(j,geo_json_member(j,x,"fieldId"),&p->threshold.field_id))return fs_error("D44: threshold must be a ParameterRef");
    if(!geo_json_canonical(j,t,p->definition,sizeof p->definition))return fs_capacity_error("I33 CAPACITY: panel-fill definition limit is 1023 bytes");
    return true;
}
static bool pf_values(const World *w,const PanelFill *p,PfLayout *d)
{
    d->finish=fs_find(w,p->finish_id);const EngMaterialVersion *m=eng_material(w,p->panel.id,p->panel.version);GeoQuantity x;
    if(!d->finish)return fs_error("I55: panel-fill %u references missing finish surface %u",p->id,p->finish_id);
    if(!m||m->kind!=0)return fs_error("I52: panel-fill %u needs an existing fixed panel material version",p->id);
    d->layout.size[p->length_axis]=m->length;d->layout.size[1-p->length_axis]=m->width;
    GeoJson j;bool ok=app_json_parse(&j,m->content);char thickness[ENG_THICKNESS_CAPACITY];
    if(ok)ok=geo_json_string(&j,geo_json_member(&j,0,"thickness"),thickness,sizeof thickness);geo_json_free(&j);
    d->t=0;
    if(ok){bool decimal=false;for(char *s=thickness;*s&&ok;++s){if(*s=='.')decimal=true;else if(decimal)ok=*s=='0';else if(*s<'0'||*s>'9'||d->t>(COORD_LIMIT-(*s-'0'))/10)ok=false;else d->t=d->t*10+(*s-'0');}}
    if(!ok||d->t<=0)return fs_error("I52: panel-fill thickness must be explicitly set positive integer mm in D1; no rounding");
    d->layout.gap=p->gap;d->layout.stagger=p->stagger;
    if((p->gap_ref.set&&!parameter_coord(w,p->gap_ref,&d->layout.gap))||(p->stagger_ref.set&&!parameter_coord(w,p->stagger_ref,&d->layout.stagger))||!parameter_value(w,p->threshold,&x))return fs_error("%s",g_parameter_error);
    if(x.num<=0)return fs_error("D44: panel-fill threshold must be a positive dimension");
    if(d->layout.gap<0)return fs_error("I52: panel-fill gap must be nonnegative integer mm");
    if(p->stagger_axis>=0&&(!d->layout.stagger||d->layout.stagger%panel_layout_pitch(d->layout.size[p->stagger_axis],d->layout.gap)==0))return fs_error("I52: stagger is zero or a whole pitch; odd and even rows coincide");
    for(uint32_t i=0;i<d->finish->obstacle_count;++i){if(!fs_obstacle_view(w,d->finish,&d->finish->obstacles[i],&d->obstacles[i]))return false;
        d->cuts[i]=d->obstacles[i].relation==FS_INTERIOR&&d->obstacles[i].q[0]<d->t&&d->obstacles[i].q[1]>0;}
    return true;
}
static GeoRegionView pf_region_view(const SpaceBoundarySurface *b,GeoLoop2View *holes)
{for(size_t i=0;i<b->hole_count;++i)holes[i]=(GeoLoop2View){b->holes[i].v,b->holes[i].count};return (GeoRegionView){{b->outline.v,b->outline.count},holes,b->hole_count};}
static size_t pf_selected_cuts(const PfLayout *d,GeoRect2 *cuts)
{size_t n=0;for(size_t i=0;i<d->finish->obstacle_count;++i)if(d->cuts[i]){const Coord *r=d->obstacles[i].rect;cuts[n++]=(GeoRect2){r[0],r[1],r[2],r[3]};}return n;}
static int pf_point_order(SurfacePoint2 a,SurfacePoint2 b)
{return geo_clip_point_order(a,b);}
static bool pf_clip_status(GeoClipStatus status)
{
    switch(status){
    case GEO_CLIP_OK:return true;
    case GEO_CLIP_AXIS_LIMIT:return fs_capacity_error("I33 CAPACITY: clipping axis limit is %d",PF_AXIS_MAX);
    case GEO_CLIP_WORKSPACE:return fs_capacity_error("I33 CAPACITY: clipping workspace unavailable");
    case GEO_CLIP_COMPONENT_WORKSPACE:return fs_capacity_error("I33 CAPACITY: fragment workspace unavailable");
    case GEO_CLIP_EDGE_LIMIT:return fs_capacity_error("I33 CAPACITY: tile contour edge limit is %d",PF_EDGE_MAX);
    case GEO_CLIP_LOOP_WORKSPACE:return fs_capacity_error("I33 CAPACITY: loop workspace unavailable");
    case GEO_CLIP_TRAVERSAL:return fs_error("R42: contour traversal did not close");
    case GEO_CLIP_OPEN_CONTOUR:return fs_error("R42: open contour after clipping");
    case GEO_CLIP_CORNERS_WORKSPACE:return fs_capacity_error("I33 CAPACITY: contour corners unavailable");
    case GEO_CLIP_ORDERED_WORKSPACE:return fs_capacity_error("I33 CAPACITY: ordered loop unavailable");
    case GEO_CLIP_VERTEX_LIMIT:return fs_capacity_error("I33 CAPACITY: layout vertex limit is %d",PF_VERTEX_MAX);
    case GEO_CLIP_COLLECTION_WORKSPACE:return fs_capacity_error("I33 CAPACITY: loop collection unavailable");
    case GEO_CLIP_NO_OUTER:return fs_error("R42: clipped component lacks an outer loop");
    }
    return false;
}
/* Also consumed by derived placements, with their selected layer and retained
 * subdivision vertices. The cumulative budget belongs to this whole result. */
static bool pf_clip(const World *w,PfLayout *d,PfTile *t)
{
    GeoLoop2View holes[POLY_MAX_HOLES];GeoRect2 cuts[FS_OBSTACLE_MAX];
    GeoRegionView region=pf_region_view(world_find_boundary(w,d->finish->boundary_id),holes);
    size_t count=pf_selected_cuts(d,cuts);GeoRect2 body={t->body[0],t->body[1],t->body[2],t->body[3]};
    GeoClipResult result={t->fragments,t->count,t->area};
    GeoClipStatus status=geo_region_clip_rect_minus_rects(&region,&body,cuts,count,d->keep_collinear,PF_VERTEX_MAX,&d->layout.vertices,&result);
    t->fragments=result.fragments;t->count=result.count;t->area=result.area;return pf_clip_status(status);
}
static bool pf_build(const World *w,const PanelFill *p,PfLayout *d)
{
    memset(d,0,sizeof *d);if(!pf_values(w,p,d))return false;
    GeoLoop2View holes[POLY_MAX_HOLES];GeoRect2 cuts[FS_OBSTACLE_MAX];WoodPanelLayoutInput input={0};
    input.region=pf_region_view(world_find_boundary(w,d->finish->boundary_id),holes);input.frame=d->finish->frame;
    input.cuts=cuts;input.cut_count=pf_selected_cuts(d,cuts);input.size[0]=d->layout.size[0];input.size[1]=d->layout.size[1];
    input.gap=d->layout.gap;input.stagger=d->layout.stagger;input.origin[0]=p->origin[0];input.origin[1]=p->origin[1];input.stagger_axis=p->stagger_axis;
    GeoClipStatus clip_status;WoodPanelStatus status=wood_panel_layout_build(&input,&d->layout,&clip_status);
    if(status==WOOD_PANEL_OK)return true;pf_free(d);
    switch(status){
    case WOOD_PANEL_WORKSPACE:return fs_capacity_error("I33 CAPACITY: layout workspace unavailable");
    case WOOD_PANEL_ENUM_LIMIT:return fs_capacity_error("I33 CAPACITY: full layout enumeration limit is %d tiles",PF_TILE_MAX);
    case WOOD_PANEL_CLIP:return pf_clip_status(clip_status);
    case WOOD_PANEL_CORNER_RANGE:return fs_capacity_error("I52/D1 CAPACITY: returned sheet corner outside D1");
    case WOOD_PANEL_VERTEX_RANGE:return fs_capacity_error("I52/D1 CAPACITY: returned panel-fill vertex outside D1");
    case WOOD_PANEL_SEAM_WORKSPACE:return fs_capacity_error("I33 CAPACITY: seam workspace unavailable");
    case WOOD_PANEL_SEAM_LIMIT:return fs_capacity_error("I33 CAPACITY: seam line limit is %d",4*PF_TILE_MAX);
    case WOOD_PANEL_BAND_RANGE:return fs_capacity_error("I52/D1 CAPACITY: returned seam band outside D1");
    default:return false;
    }
}
static bool pf_rebuild(const World *w)
{for(uint64_t i=0;i<w->finish_surfaces.fill_count;++i){PfLayout d;bool ok=pf_build(w,&w->finish_surfaces.fills[i],&d);pf_free(&d);if(!ok)return false;}return true;}
static bool pf_operation(World *w,GeoJson *j,int t,bool remove)
{
    FinishSurfaceState *s=&w->finish_surfaces;PanelFill p;uint32_t id;
    if(remove){if(!geo_json_keys(j,t,"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,true))return fs_error("D42: delete-panel-fill needs id");}
    else{if(!geo_json_keys(j,t,"op,value","")||!pf_parse(j,geo_json_member(j,t,"value"),&p))return false;id=p.id;}
    size_t at=0;while(at<s->fill_count&&s->fills[at].id!=id)++at;
    if(remove){if(at==s->fill_count)return fs_error("D42: deleted panel-fill does not exist");memmove(&s->fills[at],&s->fills[at+1],(s->fill_count-at-1)*sizeof p);memset(&s->fills[--s->fill_count],0,sizeof p);return true;}
    if(at==s->fill_count){if(at==FS_MAX)return fs_capacity_error("I33 CAPACITY: panel-fill limit is %d",FS_MAX);++s->fill_count;}s->fills[at]=p;return true;
}
static void pf_dump(const World *w,FILE *out)
{for(uint64_t i=0;i<w->finish_surfaces.fill_count;++i){const PanelFill *p=&w->finish_surfaces.fills[i];fprintf(out,"panel-fill %u definition-hex ",p->id);for(const unsigned char *c=(const unsigned char*)p->definition;*c;++c)fprintf(out,"%02x",*c);fputc('\n',out);}}
static bool apply_panel_fill_line(const char *path,int line,char **t,int count,World *w)
{
    if(!g_parsing_scene_file||!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){scene_error(path,line,"I56: panel-fill requires atomic scene with all three declared capabilities");return false;}
    uint32_t id;char text[1024];size_t n=strlen(t[3]);if(count!=4||strcmp(t[2],"definition-hex")||!parse_u32(t[1],&id)||!n||n%2||n/2>=sizeof text)goto invalid;
    for(size_t i=0;i<n/2;++i){int a=grid_system_hex_digit(t[3][2*i]),b=grid_system_hex_digit(t[3][2*i+1]);if(a<0||b<0||!(a*16+b))goto invalid;text[i]=(char)(a*16+b);}text[n/2]=0;
    GeoJson j;PanelFill p;bool ok=app_json_parse(&j,text);if(ok)ok=pf_parse(&j,0,&p);geo_json_free(&j);
    if(ok&&(p.id!=id||pf_find(w,id)))ok=fs_error("I56: panel-fill id mismatch or duplicate");
    if(ok&&w->finish_surfaces.fill_count==FS_MAX)ok=fs_capacity_error("I33 CAPACITY: panel-fill limit is %d",FS_MAX);
    if(ok)w->finish_surfaces.fills[w->finish_surfaces.fill_count++]=p;else scene_error(path,line,g_engineering_error);return ok;
invalid:scene_error(path,line,"D42: panel-fill id definition-hex HEX");return false;
}
