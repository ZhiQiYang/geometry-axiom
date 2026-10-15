/* D64/I74/R60: one source definition, ordered inside the existing I8 candidate. */
static bool grid_card_fail(const char *format,...)
{va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);utf8_trim_tail(g_engineering_error);return false;}
static GridSystem *grid_card_system(World *w,uint32_t id)
{for(size_t i=0;i<w->grid_system_count;++i)if(w->grid_systems[i].id==id)return &w->grid_systems[i];return NULL;}
static bool grid_card_read(EngJson *j,int t,GridCardReference *r)
{
    if(!eng_json_keys(j,t,"parameterId,uFieldId,vFieldId","")||
       !parameter_u32(j,eng_json_member(j,t,"parameterId"),&r->parameter_id)||
       !parameter_u32(j,eng_json_member(j,t,"uFieldId"),&r->fields[0])||
       !parameter_u32(j,eng_json_member(j,t,"vFieldId"),&r->fields[1]))return eng_fail("I74 COMPLETE_MAPPING: expected one card and both field ids (SAME_CARD)");
    r->set=true;return true;
}
static bool grid_card_mark(GridSystem *s)
{
    for(int a=0;a<2;++a){GridAxisDef *d=&s->axis[a];
        if(!grid_axis_is_infinite(d))return eng_fail("I74 MODE_SCOPE: both axes must use repeat or repeat-panel");
        int slot=d->source==GRID_SRC_REPEAT?1:2;
        memset(&d->parameters[slot],0,sizeof d->parameters[slot]);d->card_length=true;
    }
    return true;
}
static bool grid_card_put(World *w,EngJson *j,int t)
{
    GridSystem s={0};char main[8],axes[2][SCENE_MAX_LINE];s.next_rule_key=1;
    if(!eng_json_keys(j,t,"id,name,mainAlong,u,v","cardReference")||
       !parameter_u32(j,eng_json_member(j,t,"id"),&s.id)||
       !eng_json_string(j,eng_json_member(j,t,"name"),s.name,sizeof s.name)||
       !eng_json_string(j,eng_json_member(j,t,"mainAlong"),main,sizeof main)||
       !eng_json_string(j,eng_json_member(j,t,"u"),axes[0],sizeof axes[0])||
       !eng_json_string(j,eng_json_member(j,t,"v"),axes[1],sizeof axes[1]))return eng_fail("I74 COMPLETE_MAPPING: invalid grid-system definition");
    if(!strcmp(main,"u"))s.main_along=1;else if(!strcmp(main,"v"))s.main_along=2;else if(strcmp(main,"none"))return eng_fail("I74 invalid mainAlong");
    for(int a=0;a<2;++a){char *tokens[SCENE_MAX_TOKENS];int at=0,count=split_tokens(axes[a],tokens,SCENE_MAX_TOKENS);
        if(count<1||!grid_system_read_axis(tokens,count,&at,&s.axis[a])||at!=count)return eng_fail("I74 MODE_TRANSITION: invalid or incomplete axis definition");}
    int ref=eng_json_member(j,t,"cardReference");if(ref>=0&&!grid_card_read(j,ref,&s.card_reference))return false;
    GridSystem *old=grid_card_system(w,s.id);
    if(old){
        if(old->card_reference.set&&!s.card_reference.set)return eng_fail("I74 CONTROLLED_TOKEN_REJECT: explicitly unbind both axes before removing the card source");
        if(grid_system_is_infinite(old)!=grid_system_is_infinite(&s))return eng_fail("I37: legacy-finite identity cannot be implicitly converted");
        s.rule_count=old->rule_count;s.next_rule_key=old->next_rule_key;memcpy(s.rules,old->rules,sizeof s.rules);
    }else{
        if(w->grid_system_count==WORLD_MAX_GRID_SYSTEMS)return eng_fail("UNSUPPORTED/CAPACITY: grid-system capacity is 16");
        old=&w->grid_systems[w->grid_system_count++];
    }
    *old=s;
    return parameter_declare(w,PARAM_OWNER_GRID_CARD,s.id,0)&&parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,s.id,0);
}
static bool grid_card_operation(World *w,EngJson *j,int t,const char *op)
{
    if(!strcmp(op,"put-grid-system"))return eng_json_keys(j,t,"op,value","")?grid_card_put(w,j,eng_json_member(j,t,"value")):eng_fail("I74 invalid put-grid-system operation");
    uint32_t id;
    const char *keys=!strcmp(op,"set-grid-card-reference")?"op,id,value":!strcmp(op,"unbind-grid-card-reference")?"op,id,mode":"op,id";
    if(!eng_json_keys(j,t,keys,"")||!parameter_u32(j,eng_json_member(j,t,"id"),&id))return eng_fail("I74 invalid card operation");
    GridSystem *s=grid_card_system(w,id);if(!s)return grid_card_fail("I74 MISSING: grid-system %u",id);
    if(!strcmp(op,"set-grid-card-reference")){
        GridCardReference ref={0};if(!grid_card_read(j,eng_json_member(j,t,"value"),&ref))return false;
        s->card_reference=ref;if(!grid_card_mark(s))return false;
    }else{
        if(!s->card_reference.set)return grid_card_fail("I74 MISSING: grid-system %u has no card reference",id);
        if(!strcmp(op,"swap-grid-card-reference")){
            uint32_t u=s->card_reference.fields[0];s->card_reference.fields[0]=s->card_reference.fields[1];s->card_reference.fields[1]=u;
        }else{
            char mode[16];if(!eng_json_string(j,eng_json_member(j,t,"mode"),mode,sizeof mode)||
                (strcmp(mode,"parameter")&&strcmp(mode,"direct")))return eng_fail("R60 EXPLICIT_UNBIND: choose parameter or direct for both axes");
            ParameterRef refs[2]={{true,s->card_reference.parameter_id,s->card_reference.fields[0]},
                                  {true,s->card_reference.parameter_id,s->card_reference.fields[1]}};
            if(!strcmp(mode,"direct")){
                char error[512];
                /* Read THIS ordered step; no deleted-value cache, future step or final-world snapshot. */
                if(!parameters_evaluate_refs(w,refs,2,error,sizeof error)||!grid_card_resolve(w,s,error,sizeof error))return grid_card_fail("R60 capture grid-system %u: %s",id,error);
            }
            if(!strcmp(mode,"direct")&&w->parameters.tracking){
                if(w->parameters.card_capture_count==256)return eng_fail("UNSUPPORTED/CAPACITY: card capture capacity");
                GridCardCapture *capture=&w->parameters.card_captures[w->parameters.card_capture_count++];
                *capture=(GridCardCapture){0};capture->id=id;capture->parameter_id=s->card_reference.parameter_id;capture->at=++w->parameters.candidate_order;
                for(int a=0;a<2;++a){capture->fields[a]=s->card_reference.fields[a];capture->values[a]=s->axis[a].source==GRID_SRC_REPEAT?s->axis[a].step:s->axis[a].panel;}
            }
            for(int a=0;a<2;++a){GridAxisDef *d=&s->axis[a];int slot=d->source==GRID_SRC_REPEAT?1:2;
                d->card_length=false;if(!strcmp(mode,"parameter")){d->parameters[slot]=refs[a];if(!parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,id,a*6+slot+1))return false;}
                else memset(&d->parameters[slot],0,sizeof d->parameters[slot]);}
            memset(&s->card_reference,0,sizeof s->card_reference);
        }
    }
    return parameter_declare(w,PARAM_OWNER_GRID_CARD,id,0);
}
