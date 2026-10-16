/* D29/R32: a grid system is a definition, never an implicit surface. */
static void json_grid_axis_definition(const GridAxisDef *d,bool subgrid,unsigned divisions)
{
    printf("{\"source\":\"%s\"",subgrid?"subgrid":
        d->source==GRID_SRC_EXPLICIT?"explicit":d->source==GRID_SRC_SERIES?"series":
        d->source==GRID_SRC_PANEL?"panel":d->source==GRID_SRC_REPEAT?"repeat":
        d->source==GRID_SRC_REPEAT_PANEL?"repeat-panel":"none");
    if (subgrid) printf(",\"divisions\":%u",divisions);
    else if (d->source==GRID_SRC_EXPLICIT) {
        fputs(",\"coordinates\":[",stdout);
        for (size_t k=0;k<d->count;++k) printf("%s%lld",k?",":"",(long long)d->coords[k]);
        putchar(']');
    } else if (d->source==GRID_SRC_SERIES) {
        printf(",\"start\":%lld,\"step\":%lld,\"count\":%zu",
            (long long)d->start,(long long)d->step,d->series_count);
    } else if (d->source==GRID_SRC_REPEAT) {
        printf(",\"phase\":%lld,\"step\":%lld",(long long)d->start,(long long)d->step);
        if (d->stagger_set) printf(",\"stagger\":%lld",(long long)d->stagger);
    } else if (d->source==GRID_SRC_PANEL || d->source==GRID_SRC_REPEAT_PANEL) {
        printf(",\"panel\":%lld,\"gap\":%lld,\"anchor\":%lld,\"anchorExplicit\":%s",
            (long long)d->body,(long long)d->gap,(long long)d->anchor,
            d->anchor_explicit?"true":"false");
        if (d->stagger_set) printf(",\"stagger\":%lld",(long long)d->stagger);
    }
    bool first=true;const char *names[]={"phase","step","panel","gap","anchor","stagger"};
    for(int i=0;i<6;++i)if(d->parameters[i].set){if(first)fputs(",\"parameterRefs\":{",stdout);printf("%s\"%s\":{\"kind\":\"parameter\",\"parameterId\":%u,\"fieldId\":%u}",first?"":",",names[i],d->parameters[i].parameter_id,d->parameters[i].field_id);first=false;}
    if(!first)putchar('}');putchar('}');
}

static void json_grid_system(const World *w,const GridSystem *system)
{
    printf("{\"kind\":\"grid-system\",\"id\":%u,\"name\":",system->id);
    js_string(system->name);
    printf(",\"mode\":\"%s\"",grid_system_is_infinite(system)?"infinite":"legacy-finite");
    fputs(",\"mainAlong\":",stdout);
    if (app_grid_system_main_along(w,system->id)==1) fputs("\"u\"",stdout);
    else if (app_grid_system_main_along(w,system->id)==2) fputs("\"v\"",stdout);
    else fputs("null",stdout);
    for (int axis=0;axis<2;++axis) {
        printf(",\"%cDefinition\":",axis?'v':'u');
        json_grid_axis_definition(&system->axis[axis],false,0);
    }
    printf(",\"nextRuleKey\":%u,\"rules\":[",system->next_rule_key);
    for(size_t i=0;i<system->rule_count;++i){const GridSubdivisionRule *r=&system->rules[i];
        printf("%s{\"ruleKey\":%u,\"name\":",i?",":"",r->key);js_string(r->name);
        fputs(",\"selector\":{\"kind\":",stdout);js_string(r->all_cells?"all-cells":"cell");
        if(!r->all_cells)printf(",\"cell\":[\"%lld\",\"%lld\"]",(long long)r->cell[0],(long long)r->cell[1]);
        printf("},\"divisions\":[%u,%u]}",r->divisions[0],r->divisions[1]);
    }
    fputs("],\"applications\":[",stdout); bool first=true;
    for (size_t i=0;i<w->wood.grid_applications.count;++i) {
        const ReferenceGrid *grid=&w->wood.grid_applications.items[i];
        const GridBinding *binding=grid->from_binding?world_find_grid_binding(w,grid->binding_id):NULL;
        if (grid->from_binding ? (!binding || binding->system_id!=system->id) :
            (!grid->from_system || grid->system_id!=system->id)) continue;
        printf("%s{\"grid\":%u,\"surface\":%u}",first?"":",",grid->id,grid->placement_id);
        first=false;
    }
    fputs("],\"bindings\":[",stdout); first=true;
    for (size_t i=0;i<geo_grid_bindings_count(&w->geo.grid_store);++i) {
        if ((*geo_grid_bindings_at(&w->geo.grid_store,i)).system_id!=system->id) continue;
        printf("%s%u",first?"":",",(*geo_grid_bindings_at(&w->geo.grid_store,i)).id); first=false;
    }
    fputs("],",stdout);
    const CanvasPos *pos=NULL;
    for (size_t i=0;i<w->app.canvas_pos_count;++i) {
        if (w->app.canvas_pos[i].kind==CANVAS_POS_GRID_SYSTEM && w->app.canvas_pos[i].id==system->id) {
            pos=&w->app.canvas_pos[i]; break;
        }
    }
    printf("\"cx\":%lld,\"cy\":%lld,\"hasPos\":%s}",
        pos?(long long)pos->x:0LL,pos?(long long)pos->y:0LL,pos?"true":"false");
}

static void json_grid_system_preview(void)
{
    fputs(",\"gridSystems\":[",stdout); bool first=true;
    for (size_t i=0;i<geo_grid_systems_count(&g_preview.transaction->before.geo.grid_store);++i) {
        const GridSystem *before=geo_grid_systems_at(&g_preview.transaction->before.geo.grid_store,i);
        const GridSystem *after=world_find_grid_system(&g_preview.transaction->after,before->id);
        printf("%s{\"id\":%u,\"before\":",first?"":",",before->id); first=false;
        json_grid_system(&g_preview.transaction->before,before);
        fputs(",\"after\":",stdout);
        if (after) json_grid_system(&g_preview.transaction->after,after); else fputs("null",stdout);
        putchar('}');
    }
    for (size_t i=0;i<geo_grid_systems_count(&g_preview.transaction->after.geo.grid_store);++i) {
        const GridSystem *after=geo_grid_systems_at(&g_preview.transaction->after.geo.grid_store,i);
        if (world_find_grid_system(&g_preview.transaction->before,after->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",after->id); first=false;
        json_grid_system(&g_preview.transaction->after,after); putchar('}');
    }
    putchar(']');
}
