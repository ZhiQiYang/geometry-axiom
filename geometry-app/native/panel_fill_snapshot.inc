/* H codec for an explicit R44 export inside the existing engineering candidate.
 * W resolves source values and the band/cell mapping; K owns ordinary D29.
 * Nothing here publishes, allocates a host/binding, or retains a fill reference. */
static bool app_panel_fill_snapshot(World *w,GeoJson *j,int t)
{
    GridSystem system={0};uint32_t fill_id;char main[8];int main_along=0;
    int value=geo_json_member(j,t,"value");system.next_rule_key=1;
    if(!geo_json_keys(j,t,"op,value","")||
       !geo_json_keys(j,value,"fillId,id,mainAlong","name")||
       !wood_eng_u32(j,geo_json_member(j,value,"fillId"),&fill_id,true)||
       !wood_eng_u32(j,geo_json_member(j,value,"id"),&system.id,false))
        return fs_error("R44 INPUT: export-fill-grid-snapshot needs fillId, new uint32 id and explicit mainAlong; only name is optional");
    if(!geo_json_string(j,geo_json_member(j,value,"mainAlong"),main,sizeof main)||
       (strcmp(main,"none")&&strcmp(main,"u")&&strcmp(main,"v")))
        return fs_error("D29 MAIN_ALONG: snapshot mainAlong must be none, u or v");
    if(!strcmp(main,"u"))main_along=1;else if(!strcmp(main,"v"))main_along=2;
    int name=geo_json_member(j,value,"name");
    if(name<0)snprintf(system.name,sizeof system.name,"試排 %u 快照",fill_id);
    else if(!geo_json_string(j,name,system.name,sizeof system.name)||
            !grid_system_name_valid((const unsigned char*)system.name,strlen(system.name)))
        return fs_error("D29 NAME: snapshot name requires 1..96 UTF-8 bytes without control characters");
    if(world_find_grid_system(w,system.id))
        return fs_error("R44 NEW_ID: grid-system %u already exists; snapshot creates a new ordinary source",system.id);
    const PanelFill *fill=pf_find(w,fill_id);
    if(!fill)return fs_error("R44 MISSING_FILL: panel-fill %u does not exist",fill_id);
    /* Capture THIS ordered operation. Resolve only its own parameter closure,
     * with fresh marks; later changes and unrelated invalid prefixes cannot
     * supply or block these values. Final candidate validation remains full. */
    ParameterRef refs[3];size_t count=0;char error[512];
    if(fill->gap_ref.set)refs[count++]=fill->gap_ref;
    if(fill->stagger_ref.set)refs[count++]=fill->stagger_ref;
    refs[count++]=fill->threshold;
    if(!parameters_evaluate_refs(w,refs,count,error,sizeof error))return fs_error("R44 capture: %s",error);
    WoodFinishContext context=app_fs_context(w);context.evaluation=NULL;
    WoodPanelGridSnapshot snapshot;
    if(!wood_pf_grid_snapshot(&context,fill,&snapshot))return false;
    for(int a=0;a<2;++a){GridAxisDef *axis=&system.axis[a];
        axis->source=GRID_SRC_REPEAT_PANEL;axis->body=snapshot.size[a];axis->gap=snapshot.gap;
        axis->anchor=snapshot.anchor[a];axis->anchor_explicit=true;
        if(snapshot.stagger_axis==a){axis->stagger_set=true;axis->stagger=snapshot.stagger;}
    }
    if(!grid_system_valid(&system,main_along))return fs_error("D29/I37: snapshot values cannot form an ordinary repeat-panel source");
    GeoGridStoreError detail;
    if(!app_grid_system_redeclare(w,&system,main_along,&detail)){
        if(detail.status==GEO_GRID_STORE_CAPACITY)return fs_capacity_error("I33 CAPACITY: grid-system capacity is 16");
        return fs_error("D29/I37: snapshot grid-system %u cannot be stored",system.id);
    }
    return parameter_declare(w,PARAM_OWNER_GRID_CARD,system.id,0)&&parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,system.id,0);
}
