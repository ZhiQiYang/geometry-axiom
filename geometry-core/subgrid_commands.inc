/* D19/I25: declaration is a complete, atomic child definition. */
static bool grid_cell_ref_parse(const char *s,int *out)
{
    if (!strcmp(s,"min")) { *out=GRID_CELL_MIN; return true; }
    if (!strcmp(s,"max")) { *out=GRID_CELL_MAX; return true; }
    uint32_t n;
    if (strncmp(s,"line:",5) || !parse_u32(s+5,&n) || n>=GRID_MAX_LINES) return false;
    *out=(int)n; return true;
}

static bool apply_subgrid_line(const char *path,int line_no,char **t,int count,World *world)
{
    ReferenceGrid candidate={0}; uint32_t du,dv;
    bool header=count>=5 && parse_u32(t[1],&candidate.id) && !strcmp(t[2],"parent") &&
        parse_u32(t[3],&candidate.parent_id);
    bool lattice=header && !strcmp(t[4],"lattice-cell");
    bool valid=header && (lattice ?
        (count==12 && parse_i64(t[5],&candidate.lattice_cell_index[0]) &&
            parse_i64(t[6],&candidate.lattice_cell_index[1]) && !strcmp(t[7],"divisions") &&
            !strcmp(t[8],"u") && parse_u32(t[9],&du) && !strcmp(t[10],"v") && parse_u32(t[11],&dv)) :
        (count==16 && !strcmp(t[4],"cell") && !strcmp(t[5],"u") &&
            grid_cell_ref_parse(t[6],&candidate.cell_ref[0][0]) && grid_cell_ref_parse(t[7],&candidate.cell_ref[0][1]) &&
            !strcmp(t[8],"v") && grid_cell_ref_parse(t[9],&candidate.cell_ref[1][0]) &&
            grid_cell_ref_parse(t[10],&candidate.cell_ref[1][1]) && !strcmp(t[11],"divisions") &&
            !strcmp(t[12],"u") && parse_u32(t[13],&du) && !strcmp(t[14],"v") && parse_u32(t[15],&dv)));
    if (!valid) {
        scene_error(path,line_no,"D19/I25: subgrid id parent id cell u lo hi v lo hi divisions u NU v NV; lattice parent uses lattice-cell I J divisions u NU v NV");
        return false;
    }
    ReferenceGrid *existing=world_find_grid_mut(world,candidate.id);
    WoodGridContext context=app_grid_context(world);char prepare_error[256]="";
    if(!wood_grid_prepare_child(&context,&candidate,lattice,du,dv,prepare_error,sizeof prepare_error)){
        scene_error(path,line_no,prepare_error);return false;
    }
    /* I8a: invalid candidates must never masquerade as the old definition. */
    World *trial=malloc(sizeof *trial);
    if(!trial){scene_error(path,line_no,"I32: subgrid trial allocation failed");return false;}
    *trial=*world;
    if (existing) trial->grid_applications.items[existing-world->grid_applications.items]=candidate;
    else if (trial->grid_applications.count<WORLD_MAX_GRIDS) trial->grid_applications.items[trial->grid_applications.count++]=candidate;
    reference_capture_trial(trial);
    free(trial);
    char err[256]="";
    if(!wood_grid_child_check(&context,&candidate,err,sizeof err)){scene_error(path,line_no,err);return false;}
    if (existing) {
        if (!world_replace_object(world,existing,&candidate,sizeof candidate)) {
            scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I25：子格變更導致引用失效，已回滾");
            return false;
        }
    } else {
        World backup=*world;
        world->grid_applications.items[world->grid_applications.count++]=candidate;
        if (!world_revalidate(world)) {
            *world=backup;
            scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I25：新子格不合法，已回滾");
            return false;
        }
    }
    return true;
}

static bool grid_guide_references(const World *world,const GuideLine *guide,uint32_t id)
{
    char rule_key[48];snprintf(rule_key,sizeof rule_key,"gridrule:%u:",id);
    if(strstr(app_guide_expression(world,guide->id),rule_key))return true;
    char key[40]; snprintf(key,sizeof key,"grid:%u:",id);
    const char *at=app_guide_expression(world,guide->id);
    while ((at=strstr(at,key))!=NULL) {
        if (at==app_guide_expression(world,guide->id) || at[-1]=='+' || at[-1]=='-' || at[-1]=='*') return true;
        ++at;
    }
    return false;
}
