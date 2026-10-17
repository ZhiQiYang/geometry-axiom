/* Ordered engineering operations mutate only a caller-owned candidate. */
#include "../geometry-templates/woodworking/native/engineering_operations.h"
/* H binds storage and callbacks to exactly the command's candidate. */
/* I38/R33: an intermediate unbind needs its current source closure, not unrelated
 * fields. The block check stays here; app_eng_operation_unbind evaluates only the
 * binding's own live sources. The complete candidate is rebuilt at validation. */
static bool app_eng_operation_parameters(void *user,char *error,size_t cap)
{
    const World *w=(const World *)user;if(!w->app.parameter_loading)return true;
    snprintf(error,cap,"I39: unterminated parameter block");return false;
}
/* P-065/P-141: a currently present source is evaluated at the unbind step. Only
 * an actually absent source whose ended generation follows this binding's
 * declaration uses its last valid value, as a local literal of the copy. */
static bool app_eng_operation_unbind(void *user,EngBinding *resolved,char *error,size_t cap)
{
    World *w=(World *)user;ParameterRef refs[2];size_t ref_count=0;
    EngDimensionSource *sources[2]={&resolved->source,&resolved->override_value};
    for(size_t i=0;i<(resolved->has_override?2u:1u);++i){
        EngDimensionSource *source=sources[i];if(source->kind!=ENG_PARAMETER)continue;
        unsigned generation;
        if(parameter_unbind_generation(w,source->parameter,parameter_engineering_owner(&resolved->target),resolved->target.id,parameter_engineering_slot(&resolved->target,(int)i),&generation)){
            if(!parameter_deleted_coord(w,source->parameter,generation,&source->value)){snprintf(error,cap,"%s",g_parameter_error);return false;}
            source->kind=ENG_LITERAL;  /* local resolution only; never rewrite the formal binding */
        }else refs[ref_count++]=source->parameter;
    }
    return parameters_evaluate_refs(w,refs,ref_count,error,cap);
}
/* P-121/P-122: base source and override are independent declaration slots. */
static bool app_eng_operation_declared(void *user,const EngTarget *target,int override)
{
    return parameter_declare((World *)user,parameter_engineering_owner(target),target->id,parameter_engineering_slot(target,override))||
        eng_fail(g_parameter_error);
}
static void app_eng_operation_member_created(void *user,size_t i)
{World *w=(World *)user;memset(&w->wood.anchors[i],0,sizeof w->wood.anchors[i]);w->wood.anchors[i].span_mode=SPAN_AUTO;}
static WoodEngineeringOperations app_eng_operations(World *w)
{
    WoodEngineeringOperations o={0};o.grids=app_grid_context(w);o.grids.engineering=app_eng_context(w);
    o.members=w->wood.timbers;o.member_count=&w->wood.timber_count;o.member_capacity=WORLD_MAX_TIMBERS;
    o.user=w;o.rebuild_parameters=app_eng_operation_parameters;o.unbind_sources=app_eng_operation_unbind;
    o.source_declared=app_eng_operation_declared;o.member_created=app_eng_operation_member_created;return o;
}
static bool eng_operation(World *w,GeoJson *j,int t)
{
    char op[40]; if (!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op)) return eng_fail("I35: operation requires an op name");
    if(!strcmp(op,"import-parameters")){
        if(!geo_json_keys(j,t,"op,value","")||!parameter_import(w,j,geo_json_member(j,t,"value")))return eng_fail(g_parameter_error[0]?g_parameter_error:"I39: invalid parameter package");return true;
    }
    if(!strcmp(op,"put-parameter")) {
        if(!geo_json_keys(j,t,"op,value","")||!parameter_put(w,j,geo_json_member(j,t,"value")))return eng_fail(g_parameter_error[0]?g_parameter_error:"I38: invalid parameter operation");return true;
    }
    if(!strcmp(op,"delete-parameter")) {
        uint32_t id;if(!geo_json_keys(j,t,"op,id","")||!parameter_u32(j,geo_json_member(j,t,"id"),&id))return eng_fail("I38: invalid parameter identity");
        return parameter_remove(w,id)?true:eng_fail(g_parameter_error);
    }
    if (!strcmp(op,"archive")) {
        WoodEngineeringContext c=app_eng_context(w);return wood_eng_archive(&c,j,t);
    }
    WoodEngineeringOperations operations=app_eng_operations(w);
    return wood_engineering_operation(&operations,j,t,op);
}

/* Native scene records contain only definitions. Values attached to bound
 * dimensions are sources and overrides, never copied evaluated dimensions. */
static bool eng_dimension_read(World *w,GeoJson *j,int t,const EngTarget *target,Coord *cache)
{WoodEngineeringContext context=app_eng_context(w);return wood_grid_dimension_read(&context,j,t,target,cache);}
static bool eng_restore_grid(World *w,GeoJson *j,int t)
{
    WoodGridContext context=app_grid_context(w);context.engineering=app_eng_context(w);
    return wood_grid_restore_engineering(&context,j,t)&&reference_checked("engineering",0,w);
}
static bool eng_restore_timber(World *w,GeoJson *j,int t)
{WoodEngineeringOperations operations=app_eng_operations(w);return wood_engineering_restore_member(&operations,j,t);}
static bool apply_engineering_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    (void)count; unsigned char decoded[1800];size_t n=0;
    if(!geo_base64_decode(tokens[2],strlen(tokens[2]),decoded,sizeof decoded-1,&n)) {scene_error(path,line_no,"I36: invalid engineering record encoding");return false;}
    decoded[n]=0;GeoJson j;
    if(!app_json_parse_n(&j,(const char*)decoded,n)){scene_error(path,line_no,j.error);geo_json_free(&j);return false;}
    bool ok=false;g_engineering_error[0]=0;
    if(!strcmp(tokens[1],"material")||!strcmp(tokens[1],"method")){
        char fingerprint[65];
        if(geo_json_keys(&j,0,"value,fingerprint","")&&geo_json_string(&j,geo_json_member(&j,0,"fingerprint"),fingerprint,sizeof fingerprint))ok=!strcmp(tokens[1],"material")?eng_publish_material(w,&j,geo_json_member(&j,0,"value"),fingerprint):eng_publish_method(w,&j,geo_json_member(&j,0,"value"),fingerprint);
    }else if(!strcmp(tokens[1],"application"))ok=eng_put_application(w,&j,0);
    else if(!strcmp(tokens[1],"grid"))ok=eng_restore_grid(w,&j,0);
    else if(!strcmp(tokens[1],"timber"))ok=eng_restore_timber(w,&j,0);
    else if(!strcmp(tokens[1],"archive")){
        ParameterCandidateOrder *order=parameters_begin_candidate(w);
        if(!order)ok=eng_fail("UNSUPPORTED/CAPACITY: candidate parameter order memory");
        else{
            ok=eng_operation(w,&j,0);
            if(ok&&!parameter_retirements_valid(w))ok=eng_fail(g_parameter_error);
        }
        parameters_end_candidate(order);  /* I39/P-062: no scratch reaches the line's later checks */
        /* I8/I38: the interactive archive entry is one complete candidate.
         * Scene loading defers its complete rebuild until all records are read. */
        if(ok&&!g_parsing_scene_file&&!reference_checked(path,line_no,w)){
            geo_json_free(&j);return false;
        }
    }
    if(!ok)scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I36: invalid engineering record");
    geo_json_free(&j);return ok;
}
static bool sp_scene_required;
/* I56: panel-fill/1 is usable only together with engineering-spec/1 and parameters/1. */
static bool fs_scene_required, fs_scene_engineering, fs_scene_parameters;
static bool apply_requires_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    if(!strcmp(tokens[1],SP_CAPABILITY)){sp_scene_required=true;return true;}
    if(!strcmp(tokens[1],FS_CAPABILITY)){fs_scene_required=true;return true;}
    if(!strcmp(tokens[1],"engineering-spec/1"))fs_scene_engineering=true;
    if(!strcmp(tokens[1],"parameters/1"))fs_scene_parameters=true;
    (void)count;if(!strcmp(tokens[1],GRID_SUBDIVISION_CAPABILITY)){g_rule_scene_required=true;return true;}if(!strcmp(tokens[1],ASM_GENERATION_CAPABILITY)){w->wood.assembly.generation_required=true;return true;}if(!strcmp(tokens[1],"engineering-spec/1")||!strcmp(tokens[1],"parameters/1")||!strcmp(tokens[1],ASM_CAPABILITY))return true;scene_error(path,line_no,"I32: unsupported required scene capability");return false;
}
