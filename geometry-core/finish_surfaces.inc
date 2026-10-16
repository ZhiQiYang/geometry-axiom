/* H scene codecs and same-candidate facts for W finish/fill policy. */
#include "../geometry-templates/woodworking/native/finish.h"
static FsDiagnosticKind g_fs_diagnostic=FS_DIAGNOSTIC_INVALID;
static bool app_finish_sources_bind(const World *,WoodFinishContext *);
static bool pf_rebuild(const World *);
static bool pf_operation(World *,GeoJson *,int,bool);
static void pf_dump(const World *,FILE *);
static bool dp_operation(World *,GeoJson *,int,bool);
static void dp_dump(const World *,FILE *);
static bool fs_error(const char *format,...)
{
    g_fs_diagnostic=FS_DIAGNOSTIC_INVALID;
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    utf8_trim_tail(g_engineering_error);return false;
}
static bool fs_capacity_error(const char *format,...)
{
    g_fs_diagnostic=FS_DIAGNOSTIC_CAPACITY;
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    utf8_trim_tail(g_engineering_error);return false;
}
static bool fs_obstacle_box(const World *w,const FinishObstacleRef *r,Coord lo[3],Coord hi[3])
{
    if(r->kind==FS_OBSTACLE_COLUMN){
        const RcColumn *c=world_find_column(w,r->id);if(!c)return false;
        lo[0]=c->x_lo;lo[1]=c->y_lo;lo[2]=c->z_lo;hi[0]=c->x_hi;hi[1]=c->y_hi;hi[2]=c->z_hi;return true;
    }
    const RcBeam *b=world_find_beam(w,r->id);if(!b)return false;
    lo[0]=b->x_lo;lo[1]=b->y_lo;lo[2]=b->z_lo;hi[0]=b->x_hi;hi[1]=b->y_hi;hi[2]=b->z_hi;return true;
}

static bool app_fs_boundary(void *user,uint32_t id,WoodBoundaryRegion *out)
{return app_boundary_read((const World *)user,id,out)!=NULL;}
static bool app_fs_obstacle_box(void *user,const FinishObstacleRef *r,Coord lo[3],Coord hi[3])
{return fs_obstacle_box((const World *)user,r,lo,hi);}
static bool app_fs_parameter_coord(void *user,ParameterRef ref,Coord *out)
{return parameter_coord((const World *)user,ref,out);}
static bool app_fs_parameter_value(void *user,ParameterRef ref,GeoQuantity *out)
{return parameter_value((const World *)user,ref,out);}
static bool app_fs_engineering_operation(void *user,GeoJson *j,int t)
{return eng_operation((World *)user,j,t);}
static bool app_fs_derived_operation(void *user,GeoJson *j,int t,bool remove)
{return dp_operation((World *)user,j,t,remove);}
static WoodFinishContext app_fs_error_context(void)
{WoodFinishContext c={0};c.error=g_engineering_error;c.error_capacity=sizeof g_engineering_error;c.diagnostic=&g_fs_diagnostic;c.parameter_error=g_parameter_error;c.parameter_error_capacity=sizeof g_parameter_error;return c;}
static WoodFinishContext app_fs_context(const World *world)
{
    World *w=(World *)world;WoodFinishContext c=app_fs_error_context();
    c.state=&w->finish_surfaces;c.engineering=app_eng_context(w);c.user=w;
    c.boundary=app_fs_boundary;c.obstacle_box=app_fs_obstacle_box;
    c.parameter_coord=app_fs_parameter_coord;c.parameter_value=app_fs_parameter_value;c.parameter_error=g_parameter_error;
    c.engineering_operation=app_fs_engineering_operation;c.derived_operation=app_fs_derived_operation;app_finish_sources_bind(w,&c);return c;
}
static bool fs_name_check(const unsigned char *name,size_t n)
{WoodFinishContext c=app_fs_error_context();return wood_fs_name_check(&c,name,n);}
static bool fs_used(const World *w)
{WoodFinishContext c=app_fs_context(w);return wood_fs_used(&c);}
static int fs_index(const World *w,uint32_t id)
{WoodFinishContext c=app_fs_context(w);return wood_fs_index(&c,id);}
static const FinishSurface *fs_find(const World *w,uint32_t id)
{WoodFinishContext c=app_fs_context(w);return wood_fs_find(&c,id);}
static void fs_obstacle_text(const FinishObstacleRef *r,char out[16])
{wood_fs_obstacle_text(r,out);}
static bool fs_obstacle_parse(const char *s,FinishObstacleRef *out)
{return wood_fs_obstacle_parse(s,out);}
static int fs_obstacle_compare(const void *a,const void *b)
{return wood_fs_obstacle_compare(a,b);}
static bool fs_obstacles_normalize(FinishSurface *f)
{WoodFinishContext c=app_fs_error_context();return wood_fs_obstacles_normalize(&c,f);}
static const char *fs_relation_name(int relation)
{return wood_fs_relation_name(relation);}
static bool fs_obstacle_view(const World *w,const FinishSurface *f,const FinishObstacleRef *r,FsObstacleView *out)
{WoodFinishContext c=app_fs_context(w);return wood_fs_obstacle_view(&c,f,r,out);}
static bool fs_check(const World *w,const FinishSurface *f)
{WoodFinishContext c=app_fs_context(w);return wood_fs_check(&c,f);}
static bool fs_rebuild(World *w,char *error,size_t capacity)
{
    WoodFinishContext c=app_fs_context(w);if(!wood_fs_rebuild(&c,error,capacity))return false;
    if(!pf_rebuild(w)){snprintf(error,capacity,"%s",g_engineering_error);return false;}
    if(!dp_rebuild(w)){snprintf(error,capacity,"%s",g_engineering_error);return false;}
    return true;
}
static uint32_t fs_reference_owner(const World *w,const char *kind,uint32_t id)
{WoodFinishContext c=app_fs_context(w);return wood_fs_reference_owner(&c,kind,id);}
static bool fs_from_json(GeoJson *j,int t,FinishSurface *f)
{WoodFinishContext c=app_fs_error_context();return wood_fs_from_json(&c,j,t,f);}
static bool fs_put(World *w,GeoJson *j,int t)
{WoodFinishContext c=app_fs_context(w);return wood_fs_put(&c,j,t);}
static bool fs_delete(World *w,uint32_t id)
{WoodFinishContext c=app_fs_context(w);return wood_fs_delete(&c,id);}
static bool fs_operation(World *w,GeoJson *j,int t)
{WoodFinishContext c=app_fs_context(w);return wood_fs_operation(&c,j,t);}
/* ---- scene records (I56 / R4) ---- */
static const char *fs_axis_word(Vector3 axis)
{
    for(size_t i=0;i<sizeof AXIS_WORDS/sizeof AXIS_WORDS[0];++i)
        if(AXIS_WORDS[i].axis.x==axis.x&&AXIS_WORDS[i].axis.y==axis.y&&AXIS_WORDS[i].axis.z==axis.z)return AXIS_WORDS[i].word;
    return "?";
}
static bool fs_scene_integrity(void)
{ return !fs_scene_required||(fs_scene_engineering&&fs_scene_parameters); }
static void fs_dump(const World *w,FILE *out)
{
    if(!fs_used(w))return;
    if(!engineering_used(w))fputs("requires engineering-spec/1\n",out);
    if(!geo_parameters_card_count(&w->parameters))fputs("requires parameters/1\n",out);
    fputs("requires " FS_CAPABILITY "\n",out);
    for(uint64_t i=0;i<w->finish_surfaces.count;++i){const FinishSurface *f=&w->finish_surfaces.items[i];
        fprintf(out,"finish-surface %u on boundary %u origin %lld %lld %lld u %s v %s n %s side %s",(unsigned)f->id,(unsigned)f->boundary_id,
            (long long)f->frame.origin.x,(long long)f->frame.origin.y,(long long)f->frame.origin.z,
            fs_axis_word(f->frame.axis_u),fs_axis_word(f->frame.axis_v),fs_axis_word(f->frame.normal),f->side>0?"+n":"-n");
        if(f->obstacle_count){fputs(" obstacles",out);for(uint32_t k=0;k<f->obstacle_count;++k){char text[16];fs_obstacle_text(&f->obstacles[k],text);fprintf(out," %s",text);}}
        fputs(" name-hex ",out);for(size_t k=0;f->name[k];++k)fprintf(out,"%02x",(unsigned char)f->name[k]);
        fputc('\n',out);
    }
    pf_dump(w,out);
    dp_dump(w,out);
}
static bool apply_finish_surface_line(const char *path,int line_no,char **t,int count,World *w)
{
    FinishSurface f;int at;memset(&f,0,sizeof f);
    if(!g_parsing_scene_file){scene_error(path,line_no,"D41/I55: finish-surface records load only with an atomic scene; edit through panel-fill-preview/confirm");return false;}
    if(!fs_scene_required||!fs_scene_engineering||!fs_scene_parameters){
        scene_error(path,line_no,"I56: finish-surface needs requires panel-fill/1, engineering-spec/1 and parameters/1 declared first");return false;}
    if(count<19||!parse_u32(t[1],&f.id)||strcmp(t[2],"on")||strcmp(t[3],"boundary")||!parse_u32(t[4],&f.boundary_id)||strcmp(t[5],"origin")||
       !parse_coord(t[6],&f.frame.origin.x)||!parse_coord(t[7],&f.frame.origin.y)||!parse_coord(t[8],&f.frame.origin.z)||
       strcmp(t[9],"u")||!lookup_axis(t[10],&f.frame.axis_u)||strcmp(t[11],"v")||!lookup_axis(t[12],&f.frame.axis_v)||
       strcmp(t[13],"n")||!lookup_axis(t[14],&f.frame.normal)||strcmp(t[15],"side")||(strcmp(t[16],"+n")&&strcmp(t[16],"-n")))goto invalid;
    f.side=t[16][0]=='+'?1:-1;at=17;
    if(at<count&&!strcmp(t[at],"obstacles")){
        for(++at;at<count&&strcmp(t[at],"name-hex");++at){
            FinishObstacleRef ref;Coord lo[3],hi[3];
            if(!fs_obstacle_parse(t[at],&ref))goto invalid;
            if(!fs_obstacle_box(w,&ref,lo,hi)){fs_error("I52: finish surface obstacle %s does not exist",t[at]);scene_error(path,line_no,g_engineering_error);return false;}
            for(uint32_t k=0;k<f.obstacle_count;++k)if(!fs_obstacle_compare(&ref,&f.obstacles[k]))goto invalid;
            if(f.obstacle_count==FS_OBSTACLE_MAX){fs_capacity_error("I33 CAPACITY: finish surface obstacle set is limited to %d",FS_OBSTACLE_MAX);scene_error(path,line_no,g_engineering_error);return false;}
            f.obstacles[f.obstacle_count]=ref;
            ++f.obstacle_count;}
        if(!f.obstacle_count)goto invalid;
    }
    if(at+2!=count||strcmp(t[at],"name-hex"))goto invalid;
    size_t bytes=strlen(t[at+1]);if(!bytes||bytes%2)goto invalid;
    unsigned char *name=malloc(bytes/2);if(!name){fs_capacity_error("I33 CAPACITY: finish surface name memory unavailable");scene_error(path,line_no,g_engineering_error);return false;}
    for(size_t k=0;k<bytes/2;++k){int a=grid_system_hex_digit(t[at+1][2*k]),b=grid_system_hex_digit(t[at+1][2*k+1]);if(a<0||b<0){free(name);goto invalid;}name[k]=(unsigned char)(a*16+b);}
    bool named=fs_name_check(name,bytes/2);if(named){memcpy(f.name,name,bytes/2);f.name[bytes/2]=0;}free(name);if(!named){scene_error(path,line_no,g_engineering_error);return false;}
    WoodFinishContext context=app_fs_context(w);const char *message;
    if(!wood_fs_load(&context,&f,&message)){if(message)scene_error(path,line_no,message);return false;}return true;
invalid:
    scene_error(path,line_no,"D41: finish-surface id on boundary B origin x y z u A v A n A side +n|-n [obstacles c<id>|b<id> ...] name-hex HEX");
    return false;
}
