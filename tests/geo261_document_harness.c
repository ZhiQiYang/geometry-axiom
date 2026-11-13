/* Public-handle witness for the neutral owned document. No private layout is
 * visible here: every observation goes through the nine store APIs. */
#include "document.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(value,name) do{if(!(value)){fprintf(stderr,"ASSERT:%s\n",name);exit(1);}}while(0)
enum { STORE_COUNT=9 };
static const unsigned char version_key[3]={'d',0,'v'};
static const char fingerprint[]="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";

static void handles(GeoDocument *d,void *out[STORE_COUNT])
{
    out[0]=geo_document_parameters(d);out[1]=geo_document_named_values(d);
    out[2]=geo_document_datums(d);out[3]=geo_document_guides(d);
    out[4]=geo_document_regions(d);out[5]=geo_document_placements(d);
    out[6]=geo_document_grids(d);out[7]=geo_document_versions(d);
    out[8]=geo_document_enclosures(d);
}
static void views(const GeoDocument *d,const void *out[STORE_COUNT])
{
    out[0]=geo_document_parameters_view(d);out[1]=geo_document_named_values_view(d);
    out[2]=geo_document_datums_view(d);out[3]=geo_document_guides_view(d);
    out[4]=geo_document_regions_view(d);out[5]=geo_document_placements_view(d);
    out[6]=geo_document_grids_view(d);out[7]=geo_document_versions_view(d);
    out[8]=geo_document_enclosures_view(d);
}
static bool empty(const GeoDocument *d)
{
    return !geo_parameters_card_count(geo_document_parameters_view(d))&&
        !geo_parameters_field_count(geo_document_parameters_view(d))&&
        !geo_named_values_count(geo_document_named_values_view(d))&&
        !geo_datums_count(geo_document_datums_view(d))&&
        !geo_guides_count(geo_document_guides_view(d))&&
        !geo_regions_count(geo_document_regions_view(d))&&
        !geo_region_keys_count(geo_document_regions_view(d))&&
        !geo_placements_count(geo_document_placements_view(d))&&
        !geo_grid_systems_count(geo_document_grids_view(d))&&
        !geo_grid_bindings_count(geo_document_grids_view(d))&&
        !geo_versions_count(geo_document_versions_view(d))&&
        !geo_enclosures_count(geo_document_enclosures_view(d));
}
static GeoVersionIdentity identity(uint32_t version)
{GeoVersionIdentity id={version_key,sizeof version_key,version};return id;}
static void put_version(GeoDocument *d,GeoCoord tag,uint32_t version)
{
    unsigned char key[3]={'d',0,'v'};char content[]="abc",schema[]="test.document/1";
    GeoVersionField field={0};field.id=88;field.value=(GeoQuantity){tag+88,1,GEO_UNIT_LENGTH};
    GeoVersionDefinition definition={0};definition.identity=(GeoVersionIdentity){key,sizeof key,version};
    definition.content=content;definition.content_length=3;
    definition.fingerprint=fingerprint;definition.fingerprint_length=64;
    definition.schema=schema;definition.schema_length=strlen(schema);
    definition.fields=&field;definition.field_count=1;
    CHECK(geo_versions_put(geo_document_versions(d),&definition,NULL)==GEO_VERSION_OK,"seed-version");
    memset(key,0xff,sizeof key);memset(content,0xff,sizeof content);
    memset(schema,0xff,sizeof schema);memset(&field,0xff,sizeof field);
}
static void seed(GeoDocument *d,GeoCoord tag)
{
    GeoParameterCard card={0};card.id=11;card.next_field_id=2;strcpy(card.name,"dimensions");
    GeoParameterField field={0};field.parameter_id=11;field.id=1;field.type=GEO_PARAMETER_DIMENSION;
    strcpy(field.name,"width");snprintf(field.expression,sizeof field.expression,
        "{\"op\":\"literal\",\"num\":%lld,\"den\":1,\"unit\":\"mm\"}",(long long)(tag+11));
    field.value=(GeoQuantity){tag+11,1,GEO_UNIT_LENGTH};
    CHECK(geo_parameters_stage_card(geo_document_parameters(d),&card),"seed-parameter-card");
    CHECK(geo_parameters_stage_field(geo_document_parameters(d),&field),"seed-parameter-field");
    CHECK(geo_named_values_put(geo_document_named_values(d),"document_width",tag+22),"seed-named-value");
    GeoLinearExpression expression;geo_linear_begin(&expression,GEO_LINEAR_EXACT_INTEGER_FINAL);
    CHECK(geo_linear_append(&expression,tag+33,1,(GeoLinearSource){9,70,1,"owned-datum-key"}),"seed-linear");
    geo_linear_finish(&expression,true);
    CHECK(geo_datums_put(geo_document_datums(d),33,0,&expression),"seed-datum");
    GeoGuide guide={0};guide.id=44;guide.placement_id=66;guide.direction=GEO_GUIDE_ALONG_V;
    guide.source=GEO_GUIDE_LOCAL;guide.resolved=true;guide.offset=tag+44;guide.expression=expression;
    CHECK(geo_guides_put(geo_document_guides(d),&guide),"seed-guide");
    GeoRegionDefinition region={0};region.id=55;region.outline.count=4;
    region.outline.v[0]=(GeoPoint2){0,0};region.outline.v[1]=(GeoPoint2){tag+55,0};
    region.outline.v[2]=(GeoPoint2){tag+55,10};region.outline.v[3]=(GeoPoint2){0,10};
    CHECK(geo_regions_put(geo_document_regions(d),&region),"seed-region");
    CHECK(geo_region_keys_initialize(geo_document_regions(d),&region),"seed-region-keys");
    GeoPlacementDefinition placement={0};placement.id=66;placement.domain=GEO_PLACEMENT_RECT;
    placement.frame=(GeoFrame){{tag+66,0,0},{1,0,0},{0,1,0},{0,0,1}};
    placement.rect=(GeoRect2){0,0,1,1};
    CHECK(geo_placements_put(geo_document_placements(d),&placement,geo_document_regions(d)),"seed-placement");
    GeoGridSystem grid={0};grid.id=77;strcpy(grid.name,"document-grid");
    grid.axis[0].source=GEO_GRID_SOURCE_REPEAT;grid.axis[0].start=tag+77;grid.axis[0].step=10;
    grid.rule_count=1;grid.next_rule_key=6;grid.rules[0].key=5;strcpy(grid.rules[0].name,"halves");
    grid.rules[0].all_cells=true;grid.rules[0].divisions[0]=2;grid.rules[0].divisions[1]=1;
    CHECK(geo_grid_systems_put(geo_document_grids(d),&grid),"seed-grid");
    GeoGridBinding binding={0};binding.id=78;binding.system_id=77;binding.boundary_id=55;
    binding.vertex_key=1;binding.cell[0]=3;binding.cell[1]=-2;binding.anchor_den[0]=binding.anchor_den[1]=1;
    CHECK(geo_grid_bindings_put(geo_document_grids(d),&binding),"seed-binding");
    put_version(d,tag,1);
    GeoEnclosure enclosure={0};enclosure.id=99;enclosure.member_count=1;enclosure.member_ids[0]=55;
    enclosure.min[0]=tag+99;enclosure.max[0]=tag+100;enclosure.max[1]=2;enclosure.max[2]=3;
    enclosure.closed=true; /* Staging owns supplied cache; no evaluation is requested. */
    CHECK(geo_enclosures_stage(geo_document_enclosures(d),&enclosure),"seed-enclosure");
}
static bool linear_matches(const GeoLinearExpression *e,GeoCoord tag)
{
    return e->mode==GEO_LINEAR_EXACT_INTEGER_FINAL&&e->complete&&e->count==1&&
        e->terms[0].numerator==tag+33&&e->terms[0].denominator==1&&
        e->terms[0].provider==9&&e->terms[0].id==70&&e->terms[0].field==1&&
        e->terms[0].key_offset<e->key_bytes&&!strcmp(e->keys+e->terms[0].key_offset,"owned-datum-key");
}
static unsigned matches(const GeoDocument *d,GeoCoord tag)
{
    unsigned bits=0;
    const GeoParameterStore *parameters=geo_document_parameters_view(d);
    const GeoParameterCard *card=geo_parameters_find(parameters,11);
    const GeoParameterField *fields=geo_parameters_fields(parameters);
    char expression[GEO_PARAMETER_EXPR_MAX];snprintf(expression,sizeof expression,
        "{\"op\":\"literal\",\"num\":%lld,\"den\":1,\"unit\":\"mm\"}",(long long)(tag+11));
    if(geo_parameters_card_count(parameters)==1&&geo_parameters_field_count(parameters)==1&&card&&fields&&
        card->id==11&&card->next_field_id==2&&card->count==1&&card->fields[0]==1&&!strcmp(card->name,"dimensions")&&
        fields[0].parameter_id==11&&fields[0].id==1&&fields[0].type==GEO_PARAMETER_DIMENSION&&
        !strcmp(fields[0].name,"width")&&!strcmp(fields[0].expression,expression)&&
        fields[0].value.num==tag+11&&fields[0].value.den==1&&fields[0].value.unit==GEO_UNIT_LENGTH)bits|=1u;
    const GeoNamedValues *named=geo_document_named_values_view(d);
    const GeoNamedValue *value=geo_named_values_find(named,"document_width");
    if(geo_named_values_count(named)==1&&value&&value->value==tag+22)bits|=2u;
    const GeoDatumStore *datums=geo_document_datums_view(d);const GeoDatum *datum=geo_datums_find(datums,33);
    if(geo_datums_count(datums)==1&&datum&&datum->axis==0&&linear_matches(&datum->expression,tag))bits|=4u;
    const GeoGuideStore *guides=geo_document_guides_view(d);const GeoGuide *guide=geo_guides_find(guides,44);
    if(geo_guides_count(guides)==1&&guide&&guide->placement_id==66&&guide->direction==GEO_GUIDE_ALONG_V&&
        guide->source==GEO_GUIDE_LOCAL&&guide->resolved&&guide->offset==tag+44&&linear_matches(&guide->expression,tag))bits|=8u;
    const GeoRegionStore *regions=geo_document_regions_view(d);const GeoRegionDefinition *region=geo_regions_find(regions,55);
    const GeoRegionKeys *keys=geo_region_keys_find(regions,55);
    if(geo_regions_count(regions)==1&&geo_region_keys_count(regions)==1&&region&&keys&&
        region->outline.count==4&&region->outline.v[1].u==tag+55&&region->outline.v[2].v==10&&
        keys->loop_count==1&&keys->counts[0]==4&&keys->keys[0][0]==1&&keys->keys[0][3]==4&&keys->next_key==5)bits|=16u;
    const GeoPlacementStore *placements=geo_document_placements_view(d);
    const GeoPlacementDefinition *placement=geo_placements_find(placements,66);
    if(geo_placements_count(placements)==1&&placement&&placement->domain==GEO_PLACEMENT_RECT&&
        placement->frame.origin.x==tag+66&&placement->frame.axis_u.x==1&&placement->frame.axis_v.y==1&&
        placement->frame.normal.z==1&&placement->rect.max_u==1&&placement->rect.max_v==1)bits|=32u;
    const GeoGridStore *grids=geo_document_grids_view(d);const GeoGridSystem *grid=geo_grid_systems_find(grids,77);
    const GeoGridBinding *binding=geo_grid_bindings_find(grids,78);
    if(geo_grid_systems_count(grids)==1&&geo_grid_bindings_count(grids)==1&&grid&&binding&&
        !strcmp(grid->name,"document-grid")&&grid->axis[0].source==GEO_GRID_SOURCE_REPEAT&&
        grid->axis[0].start==tag+77&&grid->axis[0].step==10&&grid->rule_count==1&&grid->next_rule_key==6&&
        grid->rules[0].key==5&&!strcmp(grid->rules[0].name,"halves")&&grid->rules[0].all_cells&&
        grid->rules[0].divisions[0]==2&&grid->rules[0].divisions[1]==1&&binding->system_id==77&&
        binding->boundary_id==55&&binding->vertex_key==1&&binding->cell[0]==3&&binding->cell[1]==-2&&
        binding->anchor_den[0]==1&&binding->anchor_den[1]==1)bits|=64u;
    const GeoVersionStore *versions=geo_document_versions_view(d);GeoVersionView version={0};
    if(geo_versions_count(versions)==1&&geo_versions_find(versions,identity(1),&version)==GEO_VERSION_OK&&
        version.identity.key_length==3&&!memcmp(version.identity.key,version_key,3)&&
        version.content_length==3&&!memcmp(version.content,"abc",3)&&
        version.fingerprint_length==64&&!memcmp(version.fingerprint,fingerprint,64)&&
        version.schema_length==15&&!memcmp(version.schema,"test.document/1",15)&&version.field_count==1&&
        version.fields[0].id==88&&version.fields[0].value.num==tag+88&&
        version.fields[0].value.den==1&&version.fields[0].value.unit==GEO_UNIT_LENGTH)bits|=128u;
    const GeoEnclosureStore *enclosures=geo_document_enclosures_view(d);const GeoEnclosure *enclosure=geo_enclosures_find(enclosures,99);
    if(geo_enclosures_count(enclosures)==1&&enclosure&&enclosure->member_count==1&&enclosure->member_ids[0]==55&&
        enclosure->min[0]==tag+99&&enclosure->max[0]==tag+100&&enclosure->max[1]==2&&enclosure->max[2]==3&&enclosure->closed)bits|=256u;
    return bits;
}
static void check_clone_values(const GeoDocument *copy)
{
    unsigned bits=matches(copy,0);
    CHECK(bits&1u,"clone-parameters");CHECK(bits&2u,"clone-named-values");CHECK(bits&4u,"clone-datums");
    CHECK(bits&8u,"clone-guides");CHECK(bits&16u,"clone-regions");CHECK(bits&32u,"clone-placements");
    CHECK(bits&64u,"clone-grids");CHECK(bits&128u,"clone-versions");CHECK(bits&256u,"clone-enclosures");
}
static void case_handles(void)
{
    GeoDocument *a=geo_document_create(),*b=geo_document_create();CHECK(a&&b&&a!=b,"handles-create");
    void *ah[STORE_COUNT],*bh[STORE_COUNT];const void *av[STORE_COUNT];handles(a,ah);handles(b,bh);views(a,av);
    for(size_t i=0;i<STORE_COUNT;++i){
        CHECK(ah[i]&&bh[i]&&ah[i]==av[i],"handles-mutable-const-agree");
        for(size_t j=0;j<i;++j)CHECK(ah[i]!=ah[j],"handles-nine-distinct");
        for(size_t j=0;j<STORE_COUNT;++j)CHECK(ah[i]!=bh[j],"handles-documents-distinct");
    }
    CHECK(empty(a)&&empty(b),"handles-create-empty");
    geo_document_destroy(a);geo_document_destroy(b);
}
static void case_contents(void)
{
    GeoDocument *a=geo_document_create(),*b=geo_document_create();CHECK(a&&b,"contents-create");
    seed(a,0);seed(b,100);
    CHECK(matches(a,0)==511u&&matches(b,100)==511u,"contents-nine-stores-owned");
    geo_document_destroy(a);CHECK(matches(b,100)==511u,"contents-other-document-survives");geo_document_destroy(b);
}
static void case_clone(void)
{
    GeoDocument *source=geo_document_create();CHECK(source,"clone-create");seed(source,0);
    GeoDocument *copy=geo_document_clone(source);CHECK(copy&&copy!=source,"clone-distinct-document");
    void *sh[STORE_COUNT],*ch[STORE_COUNT];handles(source,sh);handles(copy,ch);
    for(size_t i=0;i<STORE_COUNT;++i)for(size_t j=0;j<STORE_COUNT;++j)
        CHECK(sh[i]!=ch[j],"clone-distinct-store-handles");
    check_clone_values(copy);
    GeoVersionView sv={0},cv={0};
    CHECK(geo_versions_find(geo_document_versions(source),identity(1),&sv)==GEO_VERSION_OK&&
        geo_versions_find(geo_document_versions(copy),identity(1),&cv)==GEO_VERSION_OK,"clone-version-views");
    CHECK(sv.content!=cv.content&&sv.identity.key!=cv.identity.key&&sv.fields!=cv.fields&&
        sv.schema!=cv.schema&&sv.fingerprint!=cv.fingerprint,"clone-version-storage-owned");
    CHECK(geo_parameters_remove(geo_document_parameters(copy),11,NULL),"clone-remove-parameters");
    CHECK(geo_named_values_remove(geo_document_named_values(copy),"document_width"),"clone-remove-named");
    CHECK(geo_datums_remove(geo_document_datums(copy),33),"clone-remove-datum");
    CHECK(geo_guides_remove(geo_document_guides(copy),44),"clone-remove-guide");
    CHECK(geo_regions_remove(geo_document_regions(copy),55)&&geo_region_keys_remove(geo_document_regions(copy),55),"clone-remove-region");
    CHECK(geo_placements_remove(geo_document_placements(copy),66),"clone-remove-placement");
    CHECK(geo_grid_bindings_remove(geo_document_grids(copy),78)&&geo_grid_systems_remove(geo_document_grids(copy),77),"clone-remove-grid");
    CHECK(geo_enclosures_remove(geo_document_enclosures(copy),99),"clone-remove-enclosure");
    put_version(copy,100,2);
    CHECK(matches(source,0)==511u&&geo_versions_count(geo_document_versions(copy))==2,"clone-mutations-isolated");
    geo_document_clear(copy);CHECK(empty(copy),"clone-clear-empty");seed(copy,100);
    geo_document_destroy(source);CHECK(matches(copy,100)==511u,"clone-survives-source-destruction");geo_document_destroy(copy);
}
static void case_clear(void)
{
    GeoDocument *a=geo_document_create(),*b=geo_document_create();CHECK(a&&b,"clear-create");seed(a,0);seed(b,100);
    void *before[STORE_COUNT],*after[STORE_COUNT];handles(a,before);geo_document_clear(a);handles(a,after);
    CHECK(empty(a),"clear-all-nine-stores");
    for(size_t i=0;i<STORE_COUNT;++i)CHECK(before[i]==after[i],"clear-keeps-borrowed-handles");
    CHECK(matches(b,100)==511u,"clear-other-document-unchanged");
    geo_document_clear(a);CHECK(empty(a),"clear-idempotent");seed(a,200);
    CHECK(matches(a,200)==511u,"clear-reuse-all-stores");geo_document_destroy(a);geo_document_destroy(b);
}
static void case_null(void)
{
    void *mutable[STORE_COUNT];const void *readonly[STORE_COUNT];handles(NULL,mutable);views(NULL,readonly);
    for(size_t i=0;i<STORE_COUNT;++i)CHECK(mutable[i]==NULL,"null-mutable-accessors");
    for(size_t i=0;i<STORE_COUNT;++i)CHECK(readonly[i]==NULL,"null-const-accessors");
    CHECK(geo_document_clone(NULL)==NULL,"null-clone");geo_document_clear(NULL);geo_document_destroy(NULL);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"handles"))case_handles();else if(!strcmp(argv[1],"contents"))case_contents();
    else if(!strcmp(argv[1],"clone"))case_clone();else if(!strcmp(argv[1],"clear"))case_clear();
    else if(!strcmp(argv[1],"null"))case_null();else return 2;
    return 0;
}
