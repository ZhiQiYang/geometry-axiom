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
            (long long)d->panel,(long long)d->gap,(long long)d->anchor,
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
    if (system->main_along==1) fputs("\"u\"",stdout);
    else if (system->main_along==2) fputs("\"v\"",stdout);
    else fputs("null",stdout);
    for (int axis=0;axis<2;++axis) {
        printf(",\"%cDefinition\":",axis?'v':'u');
        json_grid_axis_definition(&system->axis[axis],false,0);
    }
    fputs(",\"applications\":[",stdout); bool first=true;
    for (size_t i=0;i<w->grid_count;++i) {
        const ReferenceGrid *grid=&w->grids[i];
        const GridBinding *binding=grid->from_binding?world_find_grid_binding(w,grid->binding_id):NULL;
        if (grid->from_binding ? (!binding || binding->system_id!=system->id) :
            (!grid->from_system || grid->system_id!=system->id)) continue;
        printf("%s{\"grid\":%u,\"surface\":%u}",first?"":",",grid->id,grid->placement_id);
        first=false;
    }
    fputs("],\"bindings\":[",stdout); first=true;
    for (size_t i=0;i<w->grid_binding_count;++i) {
        if (w->grid_bindings[i].system_id!=system->id) continue;
        printf("%s%u",first?"":",",w->grid_bindings[i].id); first=false;
    }
    fputs("],",stdout);
    const CanvasPos *pos=NULL;
    for (size_t i=0;i<w->canvas_pos_count;++i) {
        if (w->canvas_pos[i].kind==CANVAS_POS_GRID_SYSTEM && w->canvas_pos[i].id==system->id) {
            pos=&w->canvas_pos[i]; break;
        }
    }
    printf("\"cx\":%lld,\"cy\":%lld,\"hasPos\":%s}",
        pos?(long long)pos->x:0LL,pos?(long long)pos->y:0LL,pos?"true":"false");
}

static void json_grid_system_preview(void)
{
    fputs(",\"gridSystems\":[",stdout); bool first=true;
    for (size_t i=0;i<g_preview.before.grid_system_count;++i) {
        const GridSystem *before=&g_preview.before.grid_systems[i];
        const GridSystem *after=world_find_grid_system(&g_preview.after,before->id);
        printf("%s{\"id\":%u,\"before\":",first?"":",",before->id); first=false;
        json_grid_system(&g_preview.before,before);
        fputs(",\"after\":",stdout);
        if (after) json_grid_system(&g_preview.after,after); else fputs("null",stdout);
        putchar('}');
    }
    for (size_t i=0;i<g_preview.after.grid_system_count;++i) {
        const GridSystem *after=&g_preview.after.grid_systems[i];
        if (world_find_grid_system(&g_preview.before,after->id)) continue;
        printf("%s{\"id\":%u,\"before\":null,\"after\":",first?"":",",after->id); first=false;
        json_grid_system(&g_preview.after,after); putchar('}');
    }
    putchar(']');
}
