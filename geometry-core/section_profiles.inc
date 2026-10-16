/* H scene/protocol composition. W owns section recipes, material policy,
 * validation and placement; callbacks observe this same candidate World. */
#include "../geometry-templates/woodworking/native/section_profile.h"
#define sp_panel_spec wood_sp_panel_spec
static bool app_section_profile_sources_bind(const World *,WoodSectionProfileContext *);
static bool sp_error(const char *format,...)
{
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    return false;
}
static bool app_sp_resolve_dimension_sources(World *w,GeoParameterSources *parameters,WoodEngineeringSources *engineering_sources,const EngDimensionSource *source,const EngTarget *target,Coord *out)
{
    if(source->kind==ENG_PARAMETER){
        int at=parameter_field_index(w,source->parameter.parameter_id,source->parameter.field_id);
        if(at<0)return sp_error("I38 MISSING: parameter %u field %u",source->parameter.parameter_id,source->parameter.field_id);
        GeoParameterError issue;
        GeoQuantity value;
        bool evaluated=parameters?geo_parameter_sources_value(parameters,source->parameter,&value,&issue):
            geo_parameters_evaluate_field(&w->parameters,source->parameter,&issue);
        if(!evaluated){
            if(issue.status==GEO_PARAMETER_MEMORY)return sp_error("I32 CAPACITY: parameter evaluation memory");
            parameter_kernel_error(w,&issue);return sp_error("%s",g_parameter_error);
        }
    }
    WoodEngineeringContext engineering=app_eng_context(w);
    if(engineering_sources)wood_engineering_sources_bind(engineering_sources,&engineering);
    return wood_eng_resolve(&engineering,source,target,UINT32_MAX,0,out,NULL,0);
}
static bool app_sp_resolve_dimension(void *user,const EngDimensionSource *source,const EngTarget *target,Coord *out)
{return app_sp_resolve_dimension_sources((World *)user,NULL,NULL,source,target,out);}

static bool app_sp_live_host(void *user,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    const World *w=(const World *)user;const PlacementSurface *p=world_find_placement(w,id);
    if(!p)return false;*derived=p->derived_fill_id!=0;
    if(*derived)return true;
    if(!surface_frame_is_valid(&p->frame))return false;
    const SpaceBoundarySurface *b=world_placement_boundary(w,p);if(p->boundary_id&&!b)return false;
    *frame=p->frame;*region=*placement_effective_boundary(p,b,region);return true;
}
static WoodSectionProfileContext app_sp_context(const World *world)
{World *w=(World *)world;WoodSectionProfileContext c={&w->section_profiles,app_eng_context(w),w,g_engineering_error,sizeof g_engineering_error,app_sp_resolve_dimension,app_sp_live_host};app_section_profile_sources_bind(w,&c);return c;}
static bool sp_used(const World *w)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_used(&c);}
static SectionProfile *sp_profile(World *w,uint32_t id)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_profile(&c,id);}
static ProfileMember *sp_member(World *w,uint32_t id)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_member(&c,id);}
static ProfileRun *sp_run(World *w,uint32_t id)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_run(&c,id);}
static bool sp_coord(GeoJson *j,int token,Coord *out)
{return wood_sp_coord(j,token,out);}
static bool sp_put_profile(World *w,GeoJson *j,int t)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_put_profile(&c,j,t);}
static bool sp_put_member(World *w,GeoJson *j,int t)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_put_member(&c,j,t);}
static bool sp_put_run(World *w,GeoJson *j,int t)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_put_run(&c,j,t);}
static Point3 sp_point(const ProfileRun *r,Coord u,Coord v,Coord along)
{return wood_sp_point(r,u,v,along);}
static size_t sp_outside_regions(const PolygonLoop2 *p,const SurfaceRegion2 *r,SurfaceRegion2 out[SP_OUTSIDE_MAX])
{return wood_sp_outside_regions(p,r,out);}
static bool sp_intersection(const ProfileMember *a,const ProfileMember *b,SurfaceRegion2 *r)
{return wood_sp_intersection(a,b,r);}
static bool sp_rebuild(World *w,char *error,size_t capacity)
{WoodSectionProfileContext c=app_sp_context(w);return wood_sp_rebuild(&c,error,capacity);}
static void sp_capture_diagnostics(World *w)
{
    if(!sp_used(w))return;
    char saved[sizeof g_engineering_error],error[256];
    memcpy(saved,g_engineering_error,sizeof saved);
    sp_rebuild(w,error,sizeof error);
    memcpy(g_engineering_error,saved,sizeof saved);
}

#include "section_profile_conversion.inc"
static bool sp_operation(World *w,GeoJson *j,int t)
{
    char op[32];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return sp_error("I49: section-profile operation needs op");
    if(!strcmp(op,"convert-run-to-advanced")||!strcmp(op,"convert-run-to-simple"))return sp_convert_run(w,j,t,!strcmp(op,"convert-run-to-simple"));
    if(!strcmp(op,"delete-placement")){
        uint32_t id;if(!geo_json_keys(j,t,"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,false))return sp_error("I49: invalid placement identity");
        if(!app_placement_remove(w,id))return sp_error("I49: placement does not exist");
        for(size_t i=0;i<w->canvas_pos_count;++i)if(w->canvas_pos[i].kind==CANVAS_POS_PLACEMENT&&w->canvas_pos[i].id==id){memmove(w->canvas_pos+i,w->canvas_pos+i+1,(w->canvas_pos_count-i-1)*sizeof w->canvas_pos[0]);memset(&w->canvas_pos[--w->canvas_pos_count],0,sizeof w->canvas_pos[0]);break;}
        return true;
    }
    if(!strcmp(op,"put-profile")||!strcmp(op,"put-member")||!strcmp(op,"put-run")){
        if(!geo_json_keys(j,t,"op,value",""))return sp_error("I49: invalid put operation fields");int value=geo_json_member(j,t,"value");
        return !strcmp(op,"put-profile")?sp_put_profile(w,j,value):!strcmp(op,"put-member")?sp_put_member(w,j,value):sp_put_run(w,j,value);
    }
    if(!strcmp(op,"delete-profile")||!strcmp(op,"delete-member")||!strcmp(op,"delete-run")){
        uint32_t id;if(!geo_json_keys(j,t,"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,false))return sp_error("I49: invalid delete identity");
        WoodSectionProfileContext c=app_sp_context(w);
        return wood_sp_remove(&c,op+7,id);
    }
    if(!strcmp(op,"put-spec")||!strcmp(op,"delete-spec")){
        char name[SPEC_NAME_MAX];Coord value=0;bool remove=!strcmp(op,"delete-spec");
        if(!geo_json_keys(j,t,remove?"op,name":"op,name,value","")||!geo_json_string(j,geo_json_member(j,t,"name"),name,sizeof name)||!reference_name(name)||
           (!remove&&!sp_coord(j,geo_json_member(j,t,"value"),&value)))return sp_error("D6b: invalid named integer spec");
        if(remove){if(!geo_named_values_remove(&w->named_values,name))return sp_error("D6b: deleted spec missing");}
        else if(!geo_named_values_put(&w->named_values,name,value))return sp_error("D6b CAPACITY: spec limit exceeded");
        return true;
    }
    return eng_operation(w,j,t);
}
static void sp_dump(const World *w,FILE *out)
{
    if(!sp_used(w))return;fputs("requires section-profile/1\n",out);
    const SectionProfileState *s=&w->section_profiles;char encoded[SP_RUN_RECORD_MAX*2];size_t n;
    for(int kind=0;kind<3;++kind){size_t count=kind==0?s->profile_count:kind==1?s->member_count:s->run_count;
        for(size_t i=0;i<count;++i){const char *text=kind==0?s->profiles[i].content:kind==1?s->members[i].content:s->runs[i].content;
            if(!geo_base64_encode(text,strlen(text),encoded,sizeof encoded,&n)){fputs("requires section-profile-record-capacity-error\n",out);return;}
            fprintf(out,"section-profile %s %s\n",kind==0?"profile":kind==1?"member":"run",encoded);}}
}
static bool apply_section_profile_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    (void)count;bool ok=false;unsigned char decoded[SP_RUN_RECORD_MAX];size_t n;uint32_t id;GeoJson j={0};
    if(!g_parsing_scene_file){scene_error(path,line_no,"I49: section-profile records require atomic scene load; use section-profile-preview/confirm");return false;}
    if(!sp_scene_required){scene_error(path,line_no,"I51: section-profile records require section-profile/1 declaration first");return false;}
    if(geo_base64_decode(tokens[2],strlen(tokens[2]),decoded,sizeof decoded-1,&n)){
        decoded[n]=0;
        if(app_json_parse_n(&j,(char*)decoded,n)&&eng_u32(&j,geo_json_member(&j,0,"id"),&id,false)){
            if(!strcmp(tokens[1],"profile")&&!sp_profile(w,id))ok=sp_put_profile(w,&j,0);
            else if(!strcmp(tokens[1],"member")&&!sp_member(w,id))ok=sp_put_member(w,&j,0);
            else if(!strcmp(tokens[1],"run")&&!sp_run(w,id))ok=sp_put_run(w,&j,0);
        }
    }
    geo_json_free(&j);if(!ok)scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I51: invalid/duplicate section-profile record");return ok;
}
