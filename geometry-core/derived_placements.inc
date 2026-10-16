/* H copies caller-owned values and preserves the atomic scene codec. W owns
 * D4 identity/source policy and R41 reconstruction plus persistent edge keys. */
#include "../geometry-templates/woodworking/native/derived_placement.h"
static bool app_derived_sources_bind(const World *,WoodDerivedContext *);
static void app_dp_value(const PlacementSurface *p,WoodDerivedValue *out)
{
    memset(out,0,sizeof *out);out->id=p->id;out->derived_fill_id=p->derived_fill_id;
    out->derived_h=p->derived_h;out->frame=p->frame;out->component_count=p->component_count;
    memcpy(out->components,p->components,sizeof out->components);
}
static bool app_dp_read(void *user,uint32_t id,WoodDerivedValue *out)
{const PlacementSurface *p=world_find_placement((const World *)user,id);if(!p)return false;app_dp_value(p,out);return true;}
static bool app_dp_write(void *user,const WoodDerivedValue *value)
{
    PlacementSurface p={0};p.id=value->id;p.derived_fill_id=value->derived_fill_id;
    p.derived_h=value->derived_h;p.frame=value->frame;p.component_count=value->component_count;
    memcpy(p.components,value->components,sizeof p.components);return app_placement_stage((World *)user,&p);
}
static bool app_dp_remove(void *user,uint32_t id)
{return app_placement_remove((World *)user,id);}
static size_t app_dp_count(void *user)
{return world_placement_count((const World *)user);}
static void app_dp_remove_position(void *user,uint32_t id)
{asm_remove_position((World *)user,CANVAS_POS_PLACEMENT,id);}
static WoodDerivedContext app_dp_context(const World *w)
{
    WoodDerivedContext c={0};c.finish=app_fs_context(w);c.placement_read=app_dp_read;c.placement_write=app_dp_write;
    c.placement_remove=app_dp_remove;c.placement_count=app_dp_count;c.placement_capacity=WORLD_MAX_PLACEMENTS;c.remove_canvas_position=app_dp_remove_position;app_derived_sources_bind(w,&c);return c;
}
static const DerivedPlacement *dp_find(const World *w,uint32_t id)
{WoodDerivedContext c=app_dp_context(w);return wood_dp_find(&c,id);}
static bool dp_operation(World *w,GeoJson *j,int t,bool remove)
{WoodDerivedContext c=app_dp_context(w);return wood_dp_operation(&c,j,t,remove);}
static bool dp_rebuild(World *w)
{WoodDerivedContext c=app_dp_context(w);return wood_dp_rebuild(&c);}
static bool dp_edge_key(const World *w,const PlacementSurface *p,size_t component,int hole,size_t edge,char *out,size_t cap)
{WoodDerivedContext c=app_dp_context(w);WoodDerivedValue value;if(p)app_dp_value(p,&value);return wood_dp_edge_key(&c,p?&value:NULL,component,hole,edge,out,cap);}
static bool dp_edge_resolve(const World *w,const PlacementSurface *p,const char *key,int *hole,int *edge)
{WoodDerivedContext c=app_dp_context(w);WoodDerivedValue value;if(p)app_dp_value(p,&value);return wood_dp_edge_resolve(&c,p?&value:NULL,key,hole,edge);}
static void dp_dump(const World *w,FILE *out)
{for(uint64_t i=0;i<w->finish_surfaces.host_count;++i){const DerivedPlacement *p=&w->finish_surfaces.hosts[i];fprintf(out,"derived-placement %u definition-hex ",p->id);for(const unsigned char *c=(const unsigned char*)p->definition;*c;++c)fprintf(out,"%02x",*c);fputc('\n',out);}}
static bool apply_derived_placement_line(const char *path,int line,char **t,int count,World *w)
{
    if(!g_parsing_scene_file||!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){scene_error(path,line,"I56: derived-placement requires an atomic scene with all three capabilities");return false;}
    uint32_t id;char definition[1024];size_t n=strlen(t[3]);
    if(count!=4||strcmp(t[2],"definition-hex")||!parse_u32(t[1],&id)||!n||n%2||n/2>=sizeof definition)goto invalid;
    for(size_t i=0;i<n/2;++i){int a=grid_system_hex_digit(t[3][2*i]),b=grid_system_hex_digit(t[3][2*i+1]);if(a<0||b<0||!(a*16+b))goto invalid;definition[i]=(char)(a*16+b);}definition[n/2]=0;
    GeoJson j;DerivedPlacement p;bool ok=app_json_parse(&j,definition);if(ok){WoodDerivedContext c=app_dp_context(w);ok=wood_dp_parse(&c,&j,0,&p);}geo_json_free(&j);
    if(!ok){scene_error(path,line,g_engineering_error);return false;}
    WoodDerivedContext c=app_dp_context(w);const char *message=NULL;ok=wood_dp_load(&c,id,&p,&message);
    if(!ok&&message)scene_error(path,line,message);return ok;
invalid:scene_error(path,line,"D4: derived-placement id definition-hex HEX");return false;
}
