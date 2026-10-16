#include "rectangular_grid.h"
#include <string.h>

static bool same_key(RGSourceKey a,RGSourceKey b)
{ return a.owner==b.owner && a.field==b.field && a.kind==b.kind; }

static RGStatus fail(RGDiagnostic *d,RGStatus status)
{ d->status=status; return status; }

const char *rectangular_grid_status_code(RGStatus status)
{
    static const char *const codes[]={
        "OK","INVALID_INPUT","MISSING_SOURCE","DUPLICATE_SOURCE",
        "FIELD_KIND_MISMATCH","UNIT_MISMATCH","INVALID_EXACT_VALUE",
        "FRACTIONAL_SOURCE","SOURCE_RANGE","CELL_CAPACITY",
        "FRACTIONAL_CELL","CORE_GRID_FAILURE","CORE_GEOMETRY_FAILURE"
    };
    return status>=RG_OK && status<=RG_CORE_GEOMETRY_FAILURE ? codes[status] : "UNKNOWN_STATUS";
}

RGStatus rectangular_grid_evaluate(const RGDefinition *definition,
    const RGSource *sources,size_t source_count,RGResult *out,RGDiagnostic *diagnostic)
{
    RGDiagnostic local_diagnostic;
    RGDiagnostic *d=diagnostic ? diagnostic : &local_diagnostic;
    RGResult candidate;
    memset(d,0,sizeof *d);
    memset(&candidate,0,sizeof candidate);
    if(!definition || !sources || !out || !source_count || source_count>RECTANGULAR_GRID_MAX_SOURCES)
        return fail(d,RG_INVALID_INPUT);

    for(size_t i=0;i<source_count;i++) {
        d->source=sources[i].key;
        if(!sources[i].key.owner || !sources[i].key.field || !sources[i].revision ||
            (sources[i].key.kind!=RG_LENGTH && sources[i].key.kind!=RG_COUNT))
            return fail(d,RG_INVALID_INPUT);
        for(size_t j=0;j<i;j++)
            if(same_key(sources[i].key,sources[j].key))return fail(d,RG_DUPLICATE_SOURCE);
    }
    for(unsigned f=0;f<RG_FIELD_COUNT;f++) {
        RGFieldKind kind=f<RG_COLUMNS ? RG_LENGTH : RG_COUNT;
        GeoQuantityUnit unit=kind==RG_LENGTH ? GEO_UNIT_LENGTH : GEO_UNIT_SCALAR;
        const RGSource *source=NULL;
        d->field=(RGField)f;
        d->source=definition->sources[f];
        if(d->source.kind!=kind)return fail(d,RG_FIELD_KIND_MISMATCH);
        for(size_t i=0;i<source_count;i++)
            if(same_key(d->source,sources[i].key)){source=&sources[i];break;}
        if(!source)return fail(d,RG_MISSING_SOURCE);
        d->value=source->value;
        if(source->value.unit!=unit)return fail(d,RG_UNIT_MISMATCH);
        candidate.sources[f]=*source;
        d->exact_status=geo_quantity_normalize(source->value,&candidate.sources[f].value);
        if(d->exact_status!=GEO_EXACT_OK)return fail(d,RG_INVALID_EXACT_VALUE);
        GeoQuantity q=candidate.sources[f].value;
        d->value=q;
        if(q.den!=1)return fail(d,RG_FRACTIONAL_SOURCE);
        if(q.num<=0 || (kind==RG_LENGTH && !geo_coord_in_range(q.num)) ||
            (kind==RG_COUNT && q.num>RECTANGULAR_GRID_MAX_DIVISIONS))
            return fail(d,RG_SOURCE_RANGE);
    }
    GeoCoord width=candidate.sources[RG_WIDTH].value.num;
    GeoCoord height=candidate.sources[RG_HEIGHT].value.num;
    unsigned columns=(unsigned)candidate.sources[RG_COLUMNS].value.num;
    unsigned rows=(unsigned)candidate.sources[RG_ROWS].value.num;
    if((size_t)columns*rows>RECTANGULAR_GRID_MAX_CELLS)return fail(d,RG_CELL_CAPACITY);

    for(unsigned axis=0;axis<2;axis++) {
        GeoCoord *lines=axis ? candidate.v : candidate.u;
        GeoCoord extent=axis ? height : width;
        unsigned divisions=axis ? rows : columns;
        size_t interior_count=0;
        d->field=(RGField)axis;
        d->source=candidate.sources[axis].key;
        d->value=candidate.sources[axis].value;
        d->divisions=divisions;
        d->grid_status=geo_interval_subdivide(0,extent,divisions,lines+1,
            RECTANGULAR_GRID_MAX_DIVISIONS-1,&interior_count);
        if(d->grid_status==GEO_GRID_NOT_DIVISIBLE) {
            d->exact_status=geo_quantity_binary(GEO_EXACT_DIVIDE,d->value,
                candidate.sources[axis+RG_COLUMNS].value,&d->required_step);
            if(d->exact_status!=GEO_EXACT_OK)return fail(d,RG_INVALID_EXACT_VALUE);
            return fail(d,RG_FRACTIONAL_CELL);
        }
        if(d->grid_status!=GEO_GRID_OK)return fail(d,RG_CORE_GRID_FAILURE);
        lines[0]=0;
        lines[interior_count+1]=extent;
        if(axis)candidate.v_count=interior_count+2;
        else candidate.u_count=interior_count+2;
    }
    candidate.outline[0]=(GeoPoint2){0,0};
    candidate.outline[1]=(GeoPoint2){width,0};
    candidate.outline[2]=(GeoPoint2){width,height};
    candidate.outline[3]=(GeoPoint2){0,height};
    GeoRegionView region={{candidate.outline,4},NULL,0};
    if(!geo_region_is_valid(&region))return fail(d,RG_CORE_GEOMETRY_FAILURE);
    for(unsigned row=0;row<rows;row++)for(unsigned column=0;column<columns;column++) {
        RGCell *cell=&candidate.cells[candidate.cell_count++];
        cell->column=column;cell->row=row;
        cell->bounds=(GeoRect2){candidate.u[column],candidate.v[row],
            candidate.u[column+1],candidate.v[row+1]};
        if(!geo_region_contains_rect(&region,cell->bounds.min_u,cell->bounds.min_v,
            cell->bounds.max_u,cell->bounds.max_v))return fail(d,RG_CORE_GEOMETRY_FAILURE);
    }
    *out=candidate;
    memset(d,0,sizeof *d);
    return RG_OK;
}
