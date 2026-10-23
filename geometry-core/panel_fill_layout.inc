/* H compatibility names and scene codec; W owns fill policy/layout. */
#define PF_TILE_MAX WOOD_PANEL_TILE_MAX
#define PF_AXIS_MAX GEO_CLIP_AXIS_MAX
#define PF_EDGE_MAX GEO_CLIP_EDGE_MAX
#define PF_VERTEX_MAX WOOD_PANEL_VERTEX_MAX
typedef WoodPanelLoop PfLoop;
typedef WoodPanelFragment PfFragment;
typedef WoodPanelTile PfTile;
typedef WoodPanelSeamLine PfSeamLine;
typedef WoodFinishLayout PfLayout;
static const PanelFill *pf_find(const World *w,uint32_t id)
{WoodFinishContext c=app_fs_context(w);return wood_pf_find(&c,id);}
static void pf_free(PfLayout *d)
{wood_pf_free(d);}
static bool pf_parse(GeoJson *j,int t,PanelFill *p)
{WoodFinishContext c=app_fs_error_context();return wood_pf_parse(&c,j,t,p);}
static bool pf_values(const World *w,const PanelFill *p,PfLayout *d)
{WoodFinishContext c=app_fs_context(w);return wood_pf_values(&c,p,d);}
static GeoRegionView pf_region_view(const SpaceBoundarySurface *b,GeoLoop2View *holes)
{return wood_pf_region_view(b,holes);}
static int pf_point_order(SurfacePoint2 a,SurfacePoint2 b)
{return wood_pf_point_order(a,b);}
static bool pf_clip_status(GeoClipStatus status)
{WoodFinishContext c=app_fs_error_context();return wood_pf_clip_status(&c,status);}
static bool pf_clip(const World *w,PfLayout *d,PfTile *t)
{WoodFinishContext c=app_fs_context(w);return wood_pf_clip(&c,d,t);}
static bool pf_build(const World *w,const PanelFill *p,PfLayout *d)
{WoodFinishContext c=app_fs_context(w);return wood_pf_build(&c,p,d);}
static bool pf_rebuild(const World *w)
{WoodFinishContext c=app_fs_context(w);return wood_pf_rebuild(&c);}
static bool pf_operation(World *w,GeoJson *j,int t,bool remove)
{WoodFinishContext c=app_fs_context(w);return wood_pf_operation(&c,j,t,remove);}
static void pf_dump(const World *w,FILE *out)
{for(uint64_t i=0;i<w->wood.finish_surfaces.fill_count;++i){const PanelFill *p=&w->wood.finish_surfaces.fills[i];fprintf(out,"panel-fill %u definition-hex ",p->id);for(const unsigned char *c=(const unsigned char*)p->definition;*c;++c)fprintf(out,"%02x",*c);fputc('\n',out);}}
static bool apply_panel_fill_line(const char *path,int line,char **t,int count,World *w)
{
    if(!g_parsing_scene_file||!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){scene_error(path,line,"I56: panel-fill requires atomic scene with all three declared capabilities");return false;}
    uint32_t id;char text[1024];size_t n=strlen(t[3]);if(count!=4||strcmp(t[2],"definition-hex")||!parse_u32(t[1],&id)||!n||n%2||n/2>=sizeof text)goto invalid;
    for(size_t i=0;i<n/2;++i){int a=grid_system_hex_digit(t[3][2*i]),b=grid_system_hex_digit(t[3][2*i+1]);if(a<0||b<0||!(a*16+b))goto invalid;text[i]=(char)(a*16+b);}text[n/2]=0;
    GeoJson j;PanelFill p;bool ok=app_json_parse(&j,text);if(ok)ok=pf_parse(&j,0,&p);geo_json_free(&j);
    WoodFinishContext context=app_fs_context(w);if(ok)ok=wood_pf_load(&context,id,&p);
    if(!ok)scene_error(path,line,g_engineering_error);return ok;
invalid:scene_error(path,line,"D42: panel-fill id definition-hex HEX");return false;
}
