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
    const ReferenceGrid *parent=world_find_grid(world,candidate.parent_id);
    if (!parent || parent->is_subgrid || candidate.id==candidate.parent_id ||
        (existing && (!existing->is_subgrid || existing->parent_id!=candidate.parent_id || existing->lattice_cell!=lattice))) {
        scene_error(path,line_no,"D19/I25：父格必須是主網格；既有網格的類型與父格編號不能更換"); return false;
    }
    if (parent->from_binding!=lattice) {
        char message[192];
        snprintf(message,sizeof message,"D19/I25：子格 %u 的父格 %u 必須使用 %s 參照形式",
                    candidate.id,parent->id,parent->from_binding?"lattice-cell":"cell");
        scene_error(path,line_no,message);
        return false;
    }
    candidate.is_subgrid=true; candidate.lattice_cell=lattice; candidate.placement_id=parent->placement_id;
    candidate.divisions[0]=du; candidate.divisions[1]=dv;
    /* I8a: invalid candidates must never masquerade as the old definition. */
    World trial=*world;
    if (existing) trial.grids[existing-world->grids]=candidate;
    else if (trial.grid_count<WORLD_MAX_GRIDS) trial.grids[trial.grid_count++]=candidate;
    reference_capture_trial(&trial);
    const PlacementSurface *p=world_find_placement(world,parent->placement_id);
    char err[256]="";
    if (!p || !grid_is_valid_in(world->grids,world->grid_count,&candidate,p,world_placement_boundary(world,p),err,sizeof err)) {
        scene_error(path,line_no,err[0]?err:"I25：找不到父格所屬的面"); return false;
    }
    if (!existing && world->grid_count>=WORLD_MAX_GRIDS) {
        scene_error(path,line_no,"I10：主網格與子網格合計不能超過 16 組"); return false;
    }
    if (existing) {
        if (!world_replace_object(world,existing,&candidate,sizeof candidate)) {
            scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I25：子格變更導致引用失效，已回滾");
            return false;
        }
    } else {
        World backup=*world;
        world->grids[world->grid_count++]=candidate;
        if (!world_revalidate(world)) {
            *world=backup;
            scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I25：新子格不合法，已回滾");
            return false;
        }
    }
    return true;
}

static bool grid_guide_references(const GuideLine *guide,uint32_t id)
{
    char key[40]; snprintf(key,sizeof key,"grid:%u:",id);
    const char *at=guide->expression;
    while ((at=strstr(at,key))!=NULL) {
        if (at==guide->expression || at[-1]=='+' || at[-1]=='-' || at[-1]=='*') return true;
        ++at;
    }
    return false;
}
