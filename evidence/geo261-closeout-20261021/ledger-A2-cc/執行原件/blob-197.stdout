/* D64/I74/R60: one source definition, ordered inside the existing I8 candidate.
 * GEO-261 host adapter: GridSystem.card_reference and card_length live in the K
 * grid store, main-along stays the W source role, and every operation edits a
 * copy that the H grid adapter puts back. K resolves the controlled lengths
 * (geo_grid_system_evaluate / geo_grid_system_resolve_card); the R60 direct
 * capture is preview-only scratch in the H candidate ledger, never in World. */
static bool grid_card_fail(const char *format,...)
{va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);utf8_trim_tail(g_engineering_error);return false;}
static bool grid_card_read(GeoJson *j,int t,uint32_t grid_id,GridCardReference *r)
{
    bool parameter=parameter_u32(j,geo_json_member(j,t,"parameterId"),&r->parameter_id);
    bool u=parameter_u32(j,geo_json_member(j,t,"uFieldId"),&r->fields[0]);
    bool v=parameter_u32(j,geo_json_member(j,t,"vFieldId"),&r->fields[1]);
    if(geo_json_member(j,t,"uParameterId")>=0||geo_json_member(j,t,"vParameterId")>=0)
        return grid_card_fail("I74 SAME_CARD: grid-system %u parameter %u u field %u v field %u requires one parameterId, not per-axis card ids",grid_id,r->parameter_id,r->fields[0],r->fields[1]);
    if(!geo_json_keys(j,t,"parameterId,uFieldId,vFieldId","")||!parameter||!u||!v)
        return grid_card_fail("I74 COMPLETE_MAPPING: grid-system %u parameter %u requires parameterId and both uFieldId/vFieldId",grid_id,r->parameter_id);
    r->set=true;return true;
}
static bool grid_card_mark(GridSystem *s)
{
    /* I74: length comes exclusively from GridSystem.card_reference. */
    for(int a=0;a<2;++a){GridAxisDef *d=&s->axis[a];
        if(!grid_axis_is_infinite(d))return grid_card_fail("I74 MODE_SCOPE: grid-system %u %c parameter %u field %u requires repeat or repeat-panel",s->id,a?'v':'u',s->card_reference.parameter_id,s->card_reference.fields[a]);
        int slot=d->source==GRID_SRC_REPEAT?1:2;
        memset(&d->parameters[slot],0,sizeof d->parameters[slot]);d->card_length=true;
    }
    return true;
}
/* The edited copy replaces the K definition; the W main-along role is kept. */
static bool grid_card_store(World *w,const GridSystem *s)
{return app_grid_system_put(w,s,app_grid_system_main_along(w,s->id))?true:grid_card_fail("I37: grid-system %u could not be stored",s->id);}
static bool grid_card_put(World *w,GeoJson *j,int t)
{
    GridSystem s={0};char main[8],axes[2][SCENE_MAX_LINE];int main_along=0;s.next_rule_key=1;
    bool has_id=parameter_u32(j,geo_json_member(j,t,"id"),&s.id);
    if(!geo_json_keys(j,t,"id,name,mainAlong,u,v","cardReference")||
       !has_id||
       !geo_json_string(j,geo_json_member(j,t,"name"),s.name,sizeof s.name)||
       !geo_json_string(j,geo_json_member(j,t,"mainAlong"),main,sizeof main)||
       !geo_json_string(j,geo_json_member(j,t,"u"),axes[0],sizeof axes[0])||
       !geo_json_string(j,geo_json_member(j,t,"v"),axes[1],sizeof axes[1]))return grid_card_fail("D29 GRID_DEFINITION: grid-system %u requires id, name, mainAlong, u and v with their declared types and no unknown keys",s.id);
    if(!strcmp(main,"u"))main_along=1;else if(!strcmp(main,"v"))main_along=2;else if(strcmp(main,"none"))return grid_card_fail("D29 GRID_DEFINITION: grid-system %u mainAlong must be none, u or v",s.id);
    for(int a=0;a<2;++a){char *tokens[SCENE_MAX_TOKENS];int at=0,count=split_tokens(axes[a],tokens,SCENE_MAX_TOKENS);
        if(count<1||!grid_system_read_axis(tokens,count,&at,&s.axis[a],a)||at!=count)return eng_fail("I74 MODE_TRANSITION: invalid or incomplete axis definition");}
    int ref=geo_json_member(j,t,"cardReference");if(ref>=0&&!grid_card_read(j,ref,s.id,&s.card_reference))return false;
    const GridSystem *old=world_find_grid_system(w,s.id);
    if(old&&old->card_reference.set&&!s.card_reference.set)return eng_fail("I74 CONTROLLED_TOKEN_REJECT: explicitly unbind both axes before removing the card source");
    /* K keeps every rule and the rule-key allocator of an existing identity. */
    GeoGridStoreError detail;
    if(!app_grid_system_redeclare(w,&s,main_along,&detail)){
        if(detail.status==GEO_GRID_STORE_SPACE_CHANGE)return eng_fail("I37: legacy-finite identity cannot be implicitly converted");
        if(detail.status==GEO_GRID_STORE_CAPACITY)return eng_fail("UNSUPPORTED/CAPACITY: grid-system capacity is 16");
        return grid_card_fail("I37: grid-system %u could not be stored",s.id);
    }
    return parameter_declare(w,PARAM_OWNER_GRID_CARD,s.id,0)&&parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,s.id,0);
}
static bool grid_card_operation(World *w,GeoJson *j,int t,const char *op)
{
    if(!strcmp(op,"put-grid-system"))return geo_json_keys(j,t,"op,value","")?grid_card_put(w,j,geo_json_member(j,t,"value")):eng_fail("I74 invalid put-grid-system operation");
    uint32_t id;
    const char *keys=!strcmp(op,"set-grid-card-reference")?"op,id,value":!strcmp(op,"unbind-grid-card-reference")?"op,id,mode":"op,id";
    if(!geo_json_keys(j,t,keys,"")||!parameter_u32(j,geo_json_member(j,t,"id"),&id))return eng_fail("I74 invalid card operation");
    const GridSystem *found=world_find_grid_system(w,id);if(!found)return grid_card_fail("I74 MISSING: grid-system %u",id);
    GridSystem system=*found,*s=&system;
    if(!strcmp(op,"set-grid-card-reference")){
        GridCardReference ref={0};if(!grid_card_read(j,geo_json_member(j,t,"value"),id,&ref))return false;
        s->card_reference=ref;if(!grid_card_mark(s))return false;
    }else{
        if(!s->card_reference.set)return grid_card_fail("I74 MISSING: grid-system %u has no card reference",id);
        if(!strcmp(op,"swap-grid-card-reference")){
            uint32_t u=s->card_reference.fields[0];s->card_reference.fields[0]=s->card_reference.fields[1];s->card_reference.fields[1]=u;
        }else{
            char mode[16];if(!geo_json_string(j,geo_json_member(j,t,"mode"),mode,sizeof mode)||
                (strcmp(mode,"parameter")&&strcmp(mode,"direct")))return eng_fail("R60 EXPLICIT_UNBIND: choose parameter or direct for both axes");
            ParameterRef refs[2]={{true,s->card_reference.parameter_id,s->card_reference.fields[0]},
                                  {true,s->card_reference.parameter_id,s->card_reference.fields[1]}};
            if(!strcmp(mode,"direct")){
                char error[512];
                /* Read THIS ordered step; no deleted-value cache, future step or final-world snapshot. */
                if(!parameters_evaluate_refs(w,refs,2,error,sizeof error)||!grid_card_resolve(w,s,error,sizeof error))return grid_card_fail("R60 capture grid-system %u: %s",id,error);
            }
            ParameterCandidateLedger *ledger=parameter_ledger(w);
            if(!strcmp(mode,"direct")&&ledger){
                if(ledger->card_capture_count==PARAM_CARD_CAPTURE_MAX)return eng_fail("UNSUPPORTED/CAPACITY: card capture capacity");
                GridCardCapture *capture=&ledger->card_captures[ledger->card_capture_count++];
                *capture=(GridCardCapture){0};capture->id=id;capture->parameter_id=s->card_reference.parameter_id;capture->at=++ledger->candidate_order;
                for(int a=0;a<2;++a){capture->fields[a]=s->card_reference.fields[a];capture->values[a]=s->axis[a].source==GRID_SRC_REPEAT?s->axis[a].step:s->axis[a].body;}
            }
            for(int a=0;a<2;++a){GridAxisDef *d=&s->axis[a];int slot=d->source==GRID_SRC_REPEAT?1:2;
                d->card_length=false;if(!strcmp(mode,"parameter")){d->parameters[slot]=refs[a];if(!parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,id,a*6+slot+1))return false;}
                else memset(&d->parameters[slot],0,sizeof d->parameters[slot]);}
            memset(&s->card_reference,0,sizeof s->card_reference);
        }
    }
    return grid_card_store(w,s)&&parameter_declare(w,PARAM_OWNER_GRID_CARD,id,0);
}
