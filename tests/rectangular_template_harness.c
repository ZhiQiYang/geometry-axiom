/* Executable contract for rectangular-grid/1. No application headers. */
#include "rectangular_grid.h"
#include <stdio.h>
#include <string.h>

#define EXPECT(condition,message) do { if(!(condition)) { \
    fprintf(stderr,"%s:%d: %s\n",__FILE__,__LINE__,message); return 1; } } while(0)

static void fixture(RGDefinition *definition,RGSource sources[4])
{
    const int64_t values[4]={1000,600,5,3};
    memset(definition,0,sizeof *definition);
    memset(sources,0,4*sizeof *sources);
    for(unsigned i=0;i<4;i++) {
        sources[i].key=(RGSourceKey){71,i+1,i<2 ? RG_LENGTH : RG_COUNT};
        sources[i].revision=1;
        sources[i].value=(GeoQuantity){values[i],1,i<2 ? GEO_UNIT_LENGTH : GEO_UNIT_SCALAR};
        definition->sources[i]=sources[i].key;
    }
}

static int exact_cells(void)
{
    RGDefinition d;RGSource s[4];RGResult result;RGDiagnostic diagnostic;
    fixture(&d,s);
    EXPECT(!strcmp(RECTANGULAR_GRID_TEMPLATE_ID,"rectangular-grid/1"),"template identity");
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_OK,"exact recipe rejected");
    EXPECT(result.cell_count==15 && result.u_count==6 && result.v_count==4,"15 exact cells");
    for(unsigned i=0;i<6;i++)EXPECT(result.u[i]==(GeoCoord)i*200,"exact U line");
    for(unsigned i=0;i<4;i++)EXPECT(result.v[i]==(GeoCoord)i*200,"exact V line");
    for(unsigned i=0;i<15;i++) {
        const RGCell *c=&result.cells[i];
        EXPECT(c->column==i%5 && c->row==i/5,"stable row and column slots");
        EXPECT(c->bounds.min_u==(GeoCoord)c->column*200 &&
            c->bounds.min_v==(GeoCoord)c->row*200,"cell position");
        EXPECT(c->bounds.max_u-c->bounds.min_u==200 &&
            c->bounds.max_v-c->bounds.min_v==200,"200 x 200 cell dimensions");
    }
    EXPECT(result.outline[2].u==1000 && result.outline[2].v==600,"rectangle extent");
    EXPECT(result.sources[0].key.owner==71 && result.sources[0].key.field==1 &&
        result.sources[0].key.kind==RG_LENGTH && result.sources[0].revision==1,"source provenance");
    EXPECT(diagnostic.status==RG_OK,"success diagnostic");
    return 0;
}

static int source_update(void)
{
    RGDefinition d,original;RGSource s[4],swap;RGResult before,after;RGDiagnostic diagnostic;
    fixture(&d,s);original=d;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&before,&diagnostic)==RG_OK,"before source edit");
    s[0].value.num=1200;s[0].revision=2;
    swap=s[0];s[0]=s[3];s[3]=swap;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&after,&diagnostic)==RG_OK,"after source edit");
    EXPECT(!memcmp(&d,&original,sizeof d),"source edit must not rebind references");
    EXPECT(after.cell_count==15 && after.u[1]==240 && after.u[5]==1200,"dependent U values updated");
    EXPECT(after.v[1]==200 && after.v[3]==600,"independent V values preserved");
    EXPECT(after.sources[0].key.field==1 && after.sources[0].revision==2,"same source, new revision");
    EXPECT(before.sources[0].revision==1 && before.u[1]==200,"prior result is immutable value");
    return 0;
}

static int fractional_rollback(void)
{
    RGDefinition d;RGSource s[4];RGResult result,snapshot;RGDiagnostic diagnostic;
    fixture(&d,s);
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_OK,"fractional baseline");
    memcpy(&snapshot,&result,sizeof result);
    s[RG_COLUMNS].value.num=3;s[RG_COLUMNS].revision=2;
    RGStatus status=rectangular_grid_evaluate(&d,s,4,&result,&diagnostic);
    EXPECT(status==RG_FRACTIONAL_CELL,"FRACTIONAL_CELL_ACCEPTED: 1000 / 3 must reject");
    EXPECT(!strcmp(rectangular_grid_status_code(status),"FRACTIONAL_CELL"),"precise status code");
    EXPECT(diagnostic.field==RG_WIDTH && diagnostic.source.owner==71 &&
        diagnostic.source.field==1 && diagnostic.source.kind==RG_LENGTH,"exact source diagnostic");
    EXPECT(diagnostic.value.num==1000 && diagnostic.value.den==1 && diagnostic.divisions==3,
        "rejected dimensions diagnostic");
    EXPECT(diagnostic.required_step.num==1000 && diagnostic.required_step.den==3 &&
        diagnostic.required_step.unit==GEO_UNIT_LENGTH && diagnostic.grid_status==GEO_GRID_NOT_DIVISIBLE,
        "unsupported exact fractional coordinate is not rounded");
    EXPECT(!memcmp(&snapshot,&result,sizeof result),"failed evaluation changed previous result");
    fixture(&d,s);s[RG_ROWS].value.num=7;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_FRACTIONAL_CELL,
        "second axis fractional failure");
    EXPECT(diagnostic.field==RG_HEIGHT && diagnostic.required_step.num==600 &&
        diagnostic.required_step.den==7,"second axis exact diagnostic");
    EXPECT(!memcmp(&snapshot,&result,sizeof result),"second axis failure exposed partial U result");
    return 0;
}

static int field_types(void)
{
    RGDefinition d;RGSource s[4];RGResult result;RGDiagnostic diagnostic;
    fixture(&d,s);d.sources[RG_WIDTH]=s[RG_COLUMNS].key;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_FIELD_KIND_MISMATCH,
        "count source accepted as length");
    fixture(&d,s);d.sources[RG_COLUMNS]=s[RG_WIDTH].key;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_FIELD_KIND_MISMATCH,
        "length source accepted as count");
    fixture(&d,s);s[RG_COLUMNS].value.unit=GEO_UNIT_LENGTH;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_UNIT_MISMATCH,
        "count scalar unit required");
    fixture(&d,s);s[RG_HEIGHT].value.unit=GEO_UNIT_SCALAR;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_UNIT_MISMATCH,
        "dimension length unit required");
    return 0;
}

static int exact_sources(void)
{
    RGDefinition d;RGSource s[4];RGResult result;RGDiagnostic diagnostic;
    fixture(&d,s);s[RG_WIDTH].value.num=2000;s[RG_WIDTH].value.den=2;
    s[RG_COLUMNS].value.num=10;s[RG_COLUMNS].value.den=2;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_OK,"exact integral normalization");
    EXPECT(result.sources[RG_WIDTH].value.num==1000 && result.sources[RG_WIDTH].value.den==1 &&
        result.u[1]==200,"kernel normalized result");
    s[RG_WIDTH].value.num=1000;s[RG_WIDTH].value.den=3;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_FRACTIONAL_SOURCE,
        "fractional length truncated");
    fixture(&d,s);s[RG_ROWS].value.den=2;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_FRACTIONAL_SOURCE,
        "fractional count truncated");
    fixture(&d,s);s[RG_WIDTH].value.den=0;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_INVALID_EXACT_VALUE &&
        diagnostic.exact_status==GEO_EXACT_DENOMINATOR,"invalid rational diagnostic");
    return 0;
}

static int references(void)
{
    RGDefinition d;RGSource s[4];RGResult result;RGDiagnostic diagnostic;
    fixture(&d,s);d.sources[RG_WIDTH].owner=72;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_MISSING_SOURCE &&
        diagnostic.source.owner==72,"owner identity was ignored");
    fixture(&d,s);d.sources[RG_HEIGHT].field=77;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_MISSING_SOURCE,
        "missing field silently substituted");
    fixture(&d,s);s[1].key=s[0].key;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_DUPLICATE_SOURCE,
        "ambiguous source silently selected");
    fixture(&d,s);s[0].revision=0;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_INVALID_INPUT,
        "missing source revision");
    return 0;
}

static int bounds_capacity(void)
{
    RGDefinition d;RGSource s[4];RGResult result,snapshot;RGDiagnostic diagnostic;
    fixture(&d,s);s[0].value.num=1024;s[1].value.num=256;
    s[2].value.num=32;s[3].value.num=8;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_OK && result.cell_count==256,
        "exact capacity must work");
    memcpy(&snapshot,&result,sizeof result);s[3].value.num=9;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_CELL_CAPACITY,
        "capacity must not truncate cells");
    EXPECT(!memcmp(&snapshot,&result,sizeof result),"capacity failure wrote output");
    fixture(&d,s);s[2].value.num=33;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_SOURCE_RANGE,"axis capacity");
    fixture(&d,s);s[0].value.num=GEO_COORD_LIMIT+1;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_SOURCE_RANGE,"coordinate range");
    fixture(&d,s);s[0].value.num=0;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_SOURCE_RANGE,"zero width");
    fixture(&d,s);s[3].value.num=-1;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_SOURCE_RANGE,"negative count");
    fixture(&d,s);s[2].value.num=1;s[3].value.num=1;
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,&diagnostic)==RG_OK &&
        result.cell_count==1 && result.u_count==2 && result.v_count==2,"one-cell exact domain");
    return 0;
}

static int invalid_input(void)
{
    RGDefinition d;RGSource s[4];RGResult result,snapshot;RGDiagnostic diagnostic;
    fixture(&d,s);memset(&result,0x5a,sizeof result);memcpy(&snapshot,&result,sizeof result);
    EXPECT(rectangular_grid_evaluate(NULL,s,4,&result,&diagnostic)==RG_INVALID_INPUT,"null definition");
    EXPECT(rectangular_grid_evaluate(&d,NULL,4,&result,&diagnostic)==RG_INVALID_INPUT,"null sources");
    EXPECT(rectangular_grid_evaluate(&d,s,4,NULL,&diagnostic)==RG_INVALID_INPUT,"null output");
    EXPECT(rectangular_grid_evaluate(&d,s,0,&result,&diagnostic)==RG_INVALID_INPUT,"empty sources");
    EXPECT(rectangular_grid_evaluate(&d,s,65,&result,&diagnostic)==RG_INVALID_INPUT,"source capacity");
    EXPECT(!memcmp(&snapshot,&result,sizeof result),"invalid argument changed output");
    EXPECT(rectangular_grid_evaluate(&d,s,4,&result,NULL)==RG_OK,"optional diagnostic");
    EXPECT(!strcmp(rectangular_grid_status_code((RGStatus)999),"UNKNOWN_STATUS"),"unknown status");
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"exact-cells"))return exact_cells();
    if(!strcmp(argv[1],"source-update"))return source_update();
    if(!strcmp(argv[1],"fractional-rollback"))return fractional_rollback();
    if(!strcmp(argv[1],"field-types"))return field_types();
    if(!strcmp(argv[1],"exact-sources"))return exact_sources();
    if(!strcmp(argv[1],"references"))return references();
    if(!strcmp(argv[1],"bounds-capacity"))return bounds_capacity();
    if(!strcmp(argv[1],"invalid-input"))return invalid_input();
    return 2;
}
