/* D29 / D10b / I37 / R32: reusable definitions, without an implicit surface. */
static char g_grid_stagger_error[256];
static void grid_rules_dump(const GridSystem *,FILE *);
static bool grid_parameter_token(const char *,Coord *,ParameterRef *,bool);
static bool grid_system_axis_valid(const GridAxisDef *a)
{ return geo_grid_axis_valid(a); }

static bool grid_system_name_valid(const unsigned char *name,size_t n)
{return geo_utf8_name_valid(name,n,GRID_SYSTEM_NAME_MAX);}

static bool grid_system_valid(const GridSystem *s,int main_along)
{ return geo_grid_system_validate(s,NULL) && app_grid_system_main_valid(s,main_along); }

static bool app_grid_coordinate(void *state,GeoParameterRef ref,GeoCoord *out)
{ return parameter_coord((const World *)state,ref,out); }

static bool grid_systems_rebuild(World *w,char *error,size_t cap)
{WoodGridContext c=app_grid_context(w);return wood_grid_systems_rebuild(&c,error,cap);}


static int grid_system_hex_digit(char c)
{
    return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:-1;
}
static bool grid_system_read_name(const char *hex,char out[GRID_SYSTEM_NAME_MAX+1])
{
    size_t n=strlen(hex); if (!n || n%2 || n>GRID_SYSTEM_NAME_MAX*2) return false;
    for (size_t i=0;i<n/2;++i) {
        int a=grid_system_hex_digit(hex[i*2]),b=grid_system_hex_digit(hex[i*2+1]);
        if (a<0 || b<0) return false; out[i]=(char)(a*16+b);
    }
    out[n/2]=0; return grid_system_name_valid((const unsigned char*)out,n/2);
}

static bool grid_system_read_stagger(char **t,int count,int *at,GridAxisDef *a)
{
    int i=*at;
    if(i>=count || strcmp(t[i],"stagger")) return true;
    if(!grid_axis_is_infinite(a)){
        snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差只接受無限軸"); return false;
    }
    if(i+1>=count || !grid_parameter_token(t[i+1],&a->stagger,&a->parameters[5],true)) return false;
    if(!a->parameters[5].set && a->stagger==0){
        snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差為 0。要貫通線請省略 stagger，不要寫 0"); return false;
    }
    a->stagger_set=true; *at=i+2; return true;
}
static bool grid_parameter_token(const char *text,Coord *value,ParameterRef *ref,bool allowed)
{
    if(allowed&&!strncmp(text,"param:",6)){*value=1;return parameter_ref_parse(text,ref);}
    return parse_coord(text,value);
}
static void grid_parameter_dump(FILE *out,Coord value,ParameterRef ref)
{
    if(ref.set)fprintf(out,"param:%u:%u",ref.parameter_id,ref.field_id);
    else fprintf(out,"%lld",(long long)value);
}
static bool grid_system_read_axis(char **t,int count,int *at,GridAxisDef *a)
{
    int i=*at; if (i>=count) return false;
    if (!strcmp(t[i],"none")) ++i;
    else if (!strcmp(t[i],"repeat")) {
        if(i+2>=count || !grid_parameter_token(t[i+1],&a->start,&a->parameters[0],true) || !grid_parameter_token(t[i+2],&a->step,&a->parameters[1],true)) return false;
        a->source=GRID_SRC_REPEAT; i+=3;
    }
    else if (!strcmp(t[i],"series")) {
        Coord n;
        if (i+3>=count || !parse_coord(t[i+1],&a->start) || !parse_coord(t[i+2],&a->step) ||
            !parse_i64(t[i+3],&n) || n<1 || n>GRID_MAX_LINES) return false;
        a->source=GRID_SRC_SERIES; a->series_count=(size_t)n; i+=4;
    } else if (!strcmp(t[i],"panel") || !strcmp(t[i],"repeat-panel")) {
        if (i+5>=count || strcmp(t[i+2],"gap") || strcmp(t[i+4],"from") ||
            !grid_parameter_token(t[i+1],&a->body,&a->parameters[2],!strcmp(t[i],"repeat-panel")) ||
            !grid_parameter_token(t[i+3],&a->gap,&a->parameters[3],!strcmp(t[i],"repeat-panel")) ||
            !grid_parameter_token(t[i+5],&a->anchor,&a->parameters[4],!strcmp(t[i],"repeat-panel"))) return false;
        a->source=!strcmp(t[i],"panel")?GRID_SRC_PANEL:GRID_SRC_REPEAT_PANEL; a->anchor_explicit=true; i+=6;
    } else {
        /* Accept the descriptive explicit keyword as well as grid's bare list. */
        if (!strcmp(t[i],"explicit")) ++i;
        a->source=GRID_SRC_EXPLICIT;
        while (i<count && strcmp(t[i],"u") && strcmp(t[i],"v")) {
            if (!strcmp(t[i],"stagger")) {
                snprintf(g_grid_stagger_error,sizeof g_grid_stagger_error,"I24: 相位差只接受無限軸"); return false;
            }
            if (a->count==GRID_MAX_LINES || !parse_coord(t[i],&a->coords[a->count])) return false;
            ++a->count; ++i;
        }
    }
    if (!grid_system_read_stagger(t,count,&i,a)) return false;
    *at=i; return grid_system_axis_valid(a);
}
static bool apply_grid_system_line(const char *path,int line_no,char **t,int count,World *w)
{
    GridSystem s={0}; s.next_rule_key=1; int main_along=0,i=6; g_grid_stagger_error[0]=0;
    if (count<10 || !parse_u32(t[1],&s.id) || strcmp(t[2],"name-hex") ||
        !grid_system_read_name(t[3],s.name) || strcmp(t[4],"main-along")) goto invalid;
    if (!strcmp(t[5],"u")) main_along=1;
    else if (!strcmp(t[5],"v")) main_along=2;
    else if (strcmp(t[5],"none")) goto invalid;
    for (int axis=0;axis<2;++axis) {
        if (i>=count || strcmp(t[i++],axis?"v":"u") || !grid_system_read_axis(t,count,&i,&s.axis[axis])) goto invalid;
    }
    if (i!=count || !grid_system_valid(&s,main_along)) goto invalid;
    World candidate=*w; GeoGridStoreError detail;
    if(!app_grid_system_redeclare(&candidate,&s,main_along,&detail)){
        if(detail.status==GEO_GRID_STORE_SPACE_CHANGE){scene_error(path,line_no,"D29/I37: legacy-finite and infinite identities cannot be converted implicitly");return false;}
        if(detail.status==GEO_GRID_STORE_CAPACITY){scene_error(path,line_no,"I37: grid-system capacity is 16");return false;}
        goto invalid;
    }
    reference_capture_trial(&candidate);
    if (!app_world_revalidate_staged(w,&candidate)) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I37: grid-system dependencies invalid; unchanged"); return false;
    }
     return true;
invalid:
    scene_error(path,line_no,g_grid_stagger_error[0]?g_grid_stagger_error:"D29/I37: grid-system requires a valid UTF-8 name-hex, main-along, and complete u/v definitions in D1 range"); return false;
}

static bool apply_grid_system_application(const char *path,int line_no,char **t,int count,World *w)
{
    ReferenceGrid g={0};
    if (count!=9 || !parse_u32(t[1],&g.id) || strcmp(t[2],"on") || !parse_u32(t[3],&g.placement_id) ||
        strcmp(t[4],"from-system") || !parse_u32(t[5],&g.system_id) || strcmp(t[6],"origin") ||
        !parse_coord(t[7],&g.system_origin[0]) || !parse_coord(t[8],&g.system_origin[1])) {
        scene_error(path,line_no,"D29: grid id on surface from-system id origin u v"); return false;
    }
    World candidate=*w;WoodGridContext context=app_grid_context(&candidate);char error[256]="";
    if(!wood_grid_apply_system(&context,&g,error,sizeof error)){scene_error(path,line_no,error);return false;}
    reference_capture_trial(&candidate);
    /* grid-preview calls this parser directly; retain the same I23 baseline. */
    const World *previous_baseline=g_subgrid_before;
    if (!previous_baseline) g_subgrid_before=w;
    bool valid=app_world_revalidate_staged(w,&candidate);
    g_subgrid_before=previous_baseline;
    if (!valid) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I37: application or dependent geometry invalid; unchanged"); return false;
    }
     return true;
}

static void grid_systems_dump(const World *w,FILE *out)
{
    for (size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i) {
        const GridSystem *s=geo_grid_systems_at(&w->geo.grid_store,i); fprintf(out,"grid-system %u name-hex ",s->id);
        for (size_t k=0;s->name[k];++k) fprintf(out,"%02x",(unsigned char)s->name[k]);
        fprintf(out," main-along %s",app_grid_system_main_along(w,s->id)==1?"u":app_grid_system_main_along(w,s->id)==2?"v":"none");
        for (int axis=0;axis<2;++axis) {
            const GridAxisDef *a=&s->axis[axis]; fprintf(out," %c",axis?'v':'u');
            if (a->source==GRID_SRC_NONE) fputs(" none",out);
            else if (a->source==GRID_SRC_EXPLICIT) {
                fputs(" explicit",out); for (size_t k=0;k<a->count;++k) fprintf(out," %lld",(long long)a->coords[k]);
            } else if (a->source==GRID_SRC_SERIES) fprintf(out," series %lld %lld %u",(long long)a->start,(long long)a->step,(unsigned)a->series_count);
            else if(a->source==GRID_SRC_REPEAT) {
                fputs(" repeat ",out);grid_parameter_dump(out,a->start,a->parameters[0]);fputc(' ',out);grid_parameter_dump(out,a->step,a->parameters[1]);
                if(a->stagger_set){fputs(" stagger ",out);grid_parameter_dump(out,a->stagger,a->parameters[5]);}
            } else {
                fprintf(out," %s ",a->source==GRID_SRC_REPEAT_PANEL?"repeat-panel":"panel");grid_parameter_dump(out,a->body,a->parameters[2]);
                fputs(" gap ",out);grid_parameter_dump(out,a->gap,a->parameters[3]);fputs(" from ",out);grid_parameter_dump(out,a->anchor,a->parameters[4]);
                if(a->source==GRID_SRC_REPEAT_PANEL && a->stagger_set){fputs(" stagger ",out);grid_parameter_dump(out,a->stagger,a->parameters[5]);}
            }
        }
        fputc('\n',out);
        grid_rules_dump(s,out);
    }
}
