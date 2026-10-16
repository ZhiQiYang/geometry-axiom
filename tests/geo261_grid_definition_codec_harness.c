/* Independent public W client: hand-authored BE64 vectors are the oracle.
 * No source graph, private state, policy evaluation, or production encoder is
 * used to construct authored input. Control kills are one exact named ASSERT. */
#include "grid_definition_codec.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define CHECK(test,label) do{if(!(test)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
#define TEST_ID UINT32_C(0x01020304)
enum { SYSTEM, BINDING, APPLICATION, RULE };
typedef struct {
    size_t source,count,coordinate[64],set[6],parameter[6],field[6],bound[6],number[6];
    size_t series,anchor,stagger;
} AxisPositions;
typedef struct {size_t key,name_size,name,all,cell[2],division[2];} RulePositions;
typedef struct {
    unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES+8];size_t size;
    size_t id,name_size,name,main,rule_count,next;
    size_t boundary,system,vertex,cell[2],numerator[2],denominator[2];
    size_t placement,flags[4],binding,parent,origin[2],cell_index[2],division[2],ref[2][2];
    AxisPositions axis[2];RulePositions rules[32];
} Vector;
typedef union {GeoGridSystem system;GeoGridBinding binding;WoodGridApplication application;GeoGridRule rule;} Decoded;

static void number_at(Vector *v,size_t at,uint64_t n)
{for(unsigned i=0;i<8;++i)v->bytes[at+7-i]=(unsigned char)(n>>(8*i));}
static size_t number(Vector *v,uint64_t n)
{size_t at=v->size;number_at(v,at,n);v->size+=8;return at;}
static size_t text(Vector *v,const unsigned char *s,size_t n,size_t *length)
{*length=number(v,n);size_t at=v->size;if(n)memcpy(v->bytes+v->size,s,n);v->size+=n;return at;}
static const GeoCoord numbers[2][6]={{INT64_MIN,INT64_MAX,-24,25,-26,27},{31,-32,33,-34,35,-36}};
static const bool parameter_set[2][6]={{true,false,false,false,false,true},{false,true,false,true,true,false}};
static void axis_vector(Vector *v,int a,bool direct,bool evaluated,bool maximal)
{
    AxisPositions *p=&v->axis[a];p->source=number(v,a?4:(uint64_t)-17);
    size_t count=maximal?64:(a?1:2);p->count=number(v,count);
    for(size_t i=0;i<count;++i)p->coordinate[i]=number(v,i==0?(a?33:(uint64_t)INT64_MIN):i==1?(uint64_t)INT64_MAX:100+i);
    for(size_t i=0;i<6;++i){
        bool bound=direct&&!evaluated&&((a==0&&i==2)||(a==1&&i==3));
        p->set[i]=number(v,parameter_set[a][i]);p->parameter[i]=number(v,101+100*a+i);
        p->field[i]=number(v,301+100*a+i);p->bound[i]=number(v,bound);
        p->number[i]=number(v,!evaluated&&(parameter_set[a][i]||bound)?0:(uint64_t)numbers[a][i]);
    }
    p->series=number(v,SIZE_MAX);p->anchor=number(v,a==0);p->stagger=number(v,a==1);
}
static void rule_vector(Vector *v,size_t index,const unsigned char *name,size_t length)
{
    RulePositions *p=&v->rules[index];p->key=number(v,index?5:UINT32_MAX);
    p->name=text(v,name,length,&p->name_size);p->all=number(v,index==0);
    for(int a=0;a<2;++a){
        p->cell[a]=number(v,index?(uint64_t)(a?3:-2):(uint64_t)(a?INT64_MAX:INT64_MIN));
        p->division[a]=number(v,index?(uint64_t)(a?3:2):(uint64_t)(a?UINT_MAX:0));
    }
}
static void system_vector(Vector *v,bool evaluated,bool maximal)
{
    memset(v,0,sizeof *v);v->id=number(v,TEST_ID);
    unsigned char long_name[96];memset(long_name,'N',sizeof long_name);
    const unsigned char name[]={0xe7,0xb3,0xbb,0xe7,0xb5,0xb1};
    v->name=text(v,maximal?long_name:name,maximal?96:sizeof name,&v->name_size);v->main=number(v,(uint64_t)-7);
    for(int a=0;a<2;++a)axis_vector(v,a,false,evaluated,maximal);
    v->rule_count=number(v,maximal?32:2);v->next=number(v,0);
    const unsigned char rule_name[]={0xe6,0xa0,0xbc};
    for(size_t i=0;i<(maximal?32:2);++i)rule_vector(v,i,maximal?long_name:rule_name,maximal?96:(i?0:sizeof rule_name));
}
static void binding_vector(Vector *v)
{
    memset(v,0,sizeof *v);v->id=number(v,TEST_ID);v->boundary=number(v,UINT32_MAX);
    v->system=number(v,0);v->vertex=number(v,0);
    for(int a=0;a<2;++a){v->cell[a]=number(v,(uint64_t)(a?INT64_MAX:INT64_MIN));
        v->numerator[a]=number(v,a?0:UINT32_MAX);v->denominator[a]=number(v,a?UINT32_MAX:0);}
}
static void application_vector(Vector *v,unsigned flags,bool evaluated)
{
    memset(v,0,sizeof *v);v->id=number(v,TEST_ID);v->placement=number(v,UINT32_MAX);
    v->flags[0]=number(v,(flags&1)!=0);v->flags[1]=number(v,(flags&2)!=0);v->flags[2]=number(v,(flags&4)!=0);
    v->binding=number(v,71);v->system=number(v,72);v->parent=number(v,73);v->flags[3]=number(v,1);
    for(int a=0;a<2;++a){
        v->origin[a]=number(v,(uint64_t)(a?INT64_MAX:INT64_MIN));
        v->cell_index[a]=number(v,(uint64_t)(a?INT64_MIN:INT64_MAX));v->division[a]=number(v,a?UINT_MAX:0);
        v->ref[a][0]=number(v,(uint64_t)(a?INT_MAX:INT_MIN));v->ref[a][1]=number(v,(uint64_t)(a?-2:-1));
    }
    if(!flags||evaluated){v->main=number(v,(uint64_t)-9);for(int a=0;a<2;++a)axis_vector(v,a,true,evaluated,false);}
    if(evaluated)for(int a=0;a<2;++a){number(v,(uint64_t)(a?INT64_MAX:INT64_MIN));
        number(v,(uint64_t)(a?-823:724));number(v,(uint64_t)(a?INT64_MIN:INT64_MAX));}
}
static void standalone_rule_vector(Vector *v,const unsigned char *name,size_t length)
{memset(v,0,sizeof *v);v->id=number(v,TEST_ID);rule_vector(v,0,name,length);}
static void authored_vector(Vector *v,int kind)
{
    if(kind==SYSTEM)system_vector(v,false,false);else if(kind==BINDING)binding_vector(v);
    else if(kind==APPLICATION)application_vector(v,0,false);
    else{const unsigned char name[]={0xe6,0xa0,0xbc};standalone_rule_vector(v,name,sizeof name);}
}
static GeoDefinitionValue value(const Vector *v,int kind)
{
    const char *schemas[]={"wood.grid.system/1","wood.grid.binding/1","wood.grid.application/1","wood.grid.rule/1"};
    return (GeoDefinitionValue){schemas[kind],v->bytes,v->size};
}
static void expected_axis(GeoGridAxisDef *out,int a,bool direct,bool evaluated,bool with_prior)
{
    memset(out,0,sizeof *out);out->source=a?4:-17;out->count=a?1:2;
    out->coords[0]=a?33:INT64_MIN;if(!a)out->coords[1]=INT64_MAX;
    GeoCoord values[6];for(size_t i=0;i<6;++i){bool masked=parameter_set[a][i]||(direct&&((a==0&&i==2)||(a==1&&i==3)));
        values[i]=!evaluated&&masked?(with_prior?(GeoCoord)(701+100*a+i):0):numbers[a][i];
        out->parameters[i].set=parameter_set[a][i];out->parameters[i].parameter_id=(uint32_t)(101+100*a+i);out->parameters[i].field_id=(uint32_t)(301+100*a+i);}
    out->start=values[0];out->step=values[1];out->body=values[2];out->gap=values[3];out->anchor=values[4];out->stagger=values[5];
    out->series_count=SIZE_MAX;out->anchor_explicit=a==0;out->stagger_set=a==1;
}
static void expected_rule(GeoGridRule *out,size_t i)
{
    memset(out,0,sizeof *out);out->key=i?5:UINT32_MAX;
    if(!i)memcpy(out->name,"\xe6\xa0\xbc",4);out->all_cells=i==0;
    out->cell[0]=i?-2:INT64_MIN;out->cell[1]=i?3:INT64_MAX;
    out->divisions[0]=i?2:0;out->divisions[1]=i?3:UINT_MAX;
}
static void expected_system(GeoGridSystem *out,bool evaluated,bool with_prior)
{
    memset(out,0,sizeof *out);out->id=TEST_ID;memcpy(out->name,"\xe7\xb3\xbb\xe7\xb5\xb1",7);
    for(int a=0;a<2;++a)expected_axis(&out->axis[a],a,false,evaluated,with_prior);
    out->rule_count=2;out->next_rule_key=0;for(size_t i=0;i<2;++i)expected_rule(&out->rules[i],i);
}
static void seed_axis(GeoGridAxisDef *out,int a)
{
    expected_axis(out,a,false,true,false);out->source=-99;out->count=0;
    out->start=701+100*a;out->step=702+100*a;out->body=703+100*a;
    out->gap=704+100*a;out->anchor=705+100*a;out->stagger=706+100*a;
}
static void seed_system(GeoGridSystem *out)
{expected_system(out,false,false);strcpy(out->name,"prior");out->next_rule_key=999;for(int a=0;a<2;++a)seed_axis(&out->axis[a],a);}
static void seed_application(WoodGridApplication *out)
{
    memset(out,0,sizeof *out);out->id=TEST_ID;out->placement_id=1;out->main_along=37;
    for(int a=0;a<2;++a){seed_axis(&out->axis[a],a);out->lattice_base[a]=a?INT64_MAX:INT64_MIN;
        out->lattice_step[a]=a?-823:724;out->lattice_index[a]=a?INT64_MIN:INT64_MAX;}
}
static void expected_application(WoodGridApplication *out,unsigned flags,bool evaluated,bool with_prior)
{
    if(with_prior)seed_application(out);else memset(out,0,sizeof *out);
    out->id=TEST_ID;out->placement_id=UINT32_MAX;out->from_system=(flags&1)!=0;out->from_binding=(flags&2)!=0;out->is_subgrid=(flags&4)!=0;
    out->binding_id=71;out->system_id=72;out->parent_id=73;out->lattice_cell=true;
    out->system_origin[0]=INT64_MIN;out->system_origin[1]=INT64_MAX;
    out->lattice_cell_index[0]=INT64_MAX;out->lattice_cell_index[1]=INT64_MIN;out->divisions[0]=0;out->divisions[1]=UINT_MAX;
    out->cell_ref[0][0]=INT_MIN;out->cell_ref[0][1]=-1;out->cell_ref[1][0]=INT_MAX;out->cell_ref[1][1]=-2;
    if(!flags||evaluated){out->main_along=-9;for(int a=0;a<2;++a)expected_axis(&out->axis[a],a,true,evaluated,with_prior);}
    if(evaluated)for(int a=0;a<2;++a){out->lattice_base[a]=a?INT64_MAX:INT64_MIN;
        out->lattice_step[a]=a?-823:724;out->lattice_index[a]=a?INT64_MIN:INT64_MAX;}
}
static bool same_axis(const GeoGridAxisDef *a,const GeoGridAxisDef *b)
{
    if(a->source!=b->source||a->count!=b->count||a->start!=b->start||a->step!=b->step||a->body!=b->body||a->gap!=b->gap||
       a->anchor!=b->anchor||a->stagger!=b->stagger||a->series_count!=b->series_count||a->anchor_explicit!=b->anchor_explicit||a->stagger_set!=b->stagger_set)return false;
    for(size_t i=0;i<a->count;++i)if(a->coords[i]!=b->coords[i])return false;
    for(size_t i=0;i<6;++i)if(a->parameters[i].set!=b->parameters[i].set||a->parameters[i].parameter_id!=b->parameters[i].parameter_id||a->parameters[i].field_id!=b->parameters[i].field_id)return false;
    return true;
}
static bool same_rule(const GeoGridRule *a,const GeoGridRule *b)
{return a->key==b->key&&!strcmp(a->name,b->name)&&a->all_cells==b->all_cells&&a->cell[0]==b->cell[0]&&a->cell[1]==b->cell[1]&&a->divisions[0]==b->divisions[0]&&a->divisions[1]==b->divisions[1];}
static bool same_system(const GeoGridSystem *a,const GeoGridSystem *b)
{
    if(a->id!=b->id||strcmp(a->name,b->name)||a->rule_count!=b->rule_count||a->next_rule_key!=b->next_rule_key)return false;
    for(int i=0;i<2;++i)if(!same_axis(&a->axis[i],&b->axis[i]))return false;
    for(size_t i=0;i<a->rule_count;++i)if(!same_rule(&a->rules[i],&b->rules[i]))return false;return true;
}
static bool same_application(const WoodGridApplication *a,const WoodGridApplication *b)
{
    if(a->id!=b->id||a->placement_id!=b->placement_id||a->from_system!=b->from_system||a->from_binding!=b->from_binding||
       a->binding_id!=b->binding_id||a->lattice_cell!=b->lattice_cell||a->system_id!=b->system_id||a->main_along!=b->main_along||a->is_subgrid!=b->is_subgrid||a->parent_id!=b->parent_id)return false;
    for(int i=0;i<2;++i)if(a->lattice_base[i]!=b->lattice_base[i]||a->lattice_step[i]!=b->lattice_step[i]||a->lattice_index[i]!=b->lattice_index[i]||
        a->lattice_cell_index[i]!=b->lattice_cell_index[i]||a->system_origin[i]!=b->system_origin[i]||!same_axis(&a->axis[i],&b->axis[i])||
        a->cell_ref[i][0]!=b->cell_ref[i][0]||a->cell_ref[i][1]!=b->cell_ref[i][1]||a->divisions[i]!=b->divisions[i])return false;return true;
}
static bool decode(int kind,const GeoDefinitionValue *v,uint32_t id,Decoded *out,const Decoded *prior,int *main)
{
    if(kind==SYSTEM)return wood_grid_decode_system(v,id,prior?&prior->system:NULL,&out->system,main);
    if(kind==BINDING)return wood_grid_decode_binding(v,id,&out->binding);
    if(kind==APPLICATION)return wood_grid_decode_application(v,id,prior?&prior->application:NULL,&out->application);
    return wood_grid_decode_rule(v,id,UINT32_MAX,&out->rule);
}
static bool rejects(int kind,const GeoDefinitionValue *v,uint32_t id)
{
    Decoded out,before,prior,prior_before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);memset(&prior,0,sizeof prior);
    if(kind==SYSTEM)seed_system(&prior.system);else if(kind==APPLICATION)seed_application(&prior.application);
    memcpy(&prior_before,&prior,sizeof prior);int main=983;
    return !decode(kind,v,id,&out,&prior,&main)&&!memcmp(&out,&before,sizeof out)&&main==983&&!memcmp(&prior,&prior_before,sizeof prior);
}
static bool rejected_vector(int kind,const Vector *v)
{GeoDefinitionValue input=value(v,kind);return rejects(kind,&input,TEST_ID);}

static int authored_case(void)
{
    Vector v;GeoGridSystem prior,old,system,expected;seed_system(&prior);memcpy(&old,&prior,sizeof old);expected_system(&expected,false,true);
    system_vector(&v,false,false);GeoDefinitionValue input=value(&v,SYSTEM);int main=99;
    CHECK(wood_grid_decode_system(&input,TEST_ID,&prior,&system,&main)&&main==-7&&same_system(&system,&expected),"authored-system-uses-cache-and-bytes");
    CHECK(!memcmp(&prior,&old,sizeof prior),"authored-system-seed-is-immutable");
    expected_system(&expected,false,false);CHECK(wood_grid_decode_system(&input,TEST_ID,NULL,&system,&main)&&same_system(&system,&expected),"authored-system-without-cache-is-zero");
    CHECK(system.axis[0].source==-17&&system.axis[0].series_count==SIZE_MAX&&system.rules[0].divisions[0]==0&&system.next_rule_key==0,"invalid-unused-policy-is-retained");
    binding_vector(&v);input=value(&v,BINDING);GeoGridBinding binding;
    CHECK(wood_grid_decode_binding(&input,TEST_ID,&binding)&&binding.id==TEST_ID&&binding.boundary_id==UINT32_MAX&&binding.system_id==0&&binding.vertex_key==0&&
        binding.cell[0]==INT64_MIN&&binding.cell[1]==INT64_MAX&&binding.anchor_num[0]==UINT32_MAX&&binding.anchor_den[0]==0&&binding.anchor_num[1]==0&&binding.anchor_den[1]==UINT32_MAX,"authored-binding-all-fields");
    WoodGridApplication app,seed,want,seed_old;seed_application(&seed);memcpy(&seed_old,&seed,sizeof seed);application_vector(&v,0,false);input=value(&v,APPLICATION);
    expected_application(&want,0,false,true);
    CHECK(wood_grid_decode_application(&input,TEST_ID,&seed,&app)&&same_application(&app,&want)&&!memcmp(&seed,&seed_old,sizeof seed),"authored-application-bound-cache-and-fields");
    CHECK(wood_grid_decode_application(&input,TEST_ID,&seed,&seed)&&same_application(&seed,&want),"authored-in-place-seed-output");
    expected_application(&want,0,false,false);CHECK(wood_grid_decode_application(&input,TEST_ID,NULL,&app)&&same_application(&app,&want),"authored-application-without-seed");
    authored_vector(&v,RULE);input=value(&v,RULE);GeoGridRule rule,want_rule;expected_rule(&want_rule,0);
    CHECK(wood_grid_decode_rule(&input,TEST_ID,UINT32_MAX,&rule)&&same_rule(&rule,&want_rule),"authored-rule-all-fields");return 0;
}
static int derived_case(void)
{
    Vector v;WoodGridApplication seed,out,want,old;seed_application(&seed);memcpy(&old,&seed,sizeof old);
    for(unsigned flags=1;flags<8;++flags){application_vector(&v,flags,false);GeoDefinitionValue input=value(&v,APPLICATION);expected_application(&want,flags,false,true);
        CHECK(v.size==152&&wood_grid_decode_application(&input,TEST_ID,&seed,&out)&&same_application(&out,&want),"derived-authored-fields-and-cache-seed");
        expected_application(&want,flags,false,false);CHECK(wood_grid_decode_application(&input,TEST_ID,NULL,&out)&&same_application(&out,&want),"derived-authored-without-cache");
        CHECK(!memcmp(&seed,&old,sizeof seed),"derived-cache-seed-is-immutable");}
    return 0;
}
static int scalars_case(void)
{
    Vector original,v;binding_vector(&original);
    size_t u32[]={original.boundary,original.id,original.system,original.vertex,original.numerator[0],original.denominator[0],original.numerator[1],original.denominator[1]};
    for(size_t i=0;i<sizeof u32/sizeof *u32;++i){v=original;number_at(&v,u32[i],UINT64_C(0x100000000)+(i==1?TEST_ID:UINT32_MAX));CHECK(rejected_vector(BINDING,&v),"u32-overflow-rejected");}
    system_vector(&original,false,false);size_t system_u32[]={original.next,original.axis[0].parameter[0],original.axis[0].field[0],original.rules[0].key};
    for(size_t i=0;i<sizeof system_u32/sizeof *system_u32;++i){v=original;number_at(&v,system_u32[i],UINT64_C(0x100000000));CHECK(rejected_vector(SYSTEM,&v),"system-u32-overflow-rejected");}
    authored_vector(&original,RULE);v=original;number_at(&v,original.rules[0].division[0],(uint64_t)UINT_MAX+1);
    CHECK(rejected_vector(RULE,&v),"unsigned-overflow-rejected");
    application_vector(&original,0,false);for(int a=0;a<2;++a){v=original;number_at(&v,original.division[a],(uint64_t)UINT_MAX+1);CHECK(rejected_vector(APPLICATION,&v),"application-unsigned-overflow-rejected");}
    system_vector(&original,false,false);size_t signed_positions[]={original.main,original.axis[0].source,original.axis[1].source};
    for(size_t i=0;i<sizeof signed_positions/sizeof *signed_positions;++i)for(int sign=0;sign<2;++sign){v=original;
        number_at(&v,signed_positions[i],(uint64_t)(sign?(int64_t)INT_MIN-1:(int64_t)INT_MAX+1));CHECK(rejected_vector(SYSTEM,&v),"int-overflow-rejected");}
    for(int extreme=0;extreme<2;++extreme){v=original;number_at(&v,v.main,(uint64_t)(extreme?INT_MAX:INT_MIN));number_at(&v,v.axis[0].source,(uint64_t)(extreme?INT_MIN:INT_MAX));
        GeoDefinitionValue input=value(&v,SYSTEM);GeoGridSystem out;int main=0;
        CHECK(wood_grid_decode_system(&input,TEST_ID,NULL,&out,&main)&&main==(extreme?INT_MAX:INT_MIN)&&out.axis[0].source==(extreme?INT_MIN:INT_MAX),"representable-int-extremes-retained");}
    application_vector(&original,0,false);for(int a=0;a<2;++a)for(int j=0;j<2;++j){v=original;number_at(&v,v.ref[a][j],(uint64_t)INT_MAX+1);CHECK(rejected_vector(APPLICATION,&v),"application-int-overflow-rejected");}
    system_vector(&original,false,false);v=original;number_at(&v,v.axis[0].anchor,2);CHECK(rejected_vector(SYSTEM,&v),"boolean-overflow-rejected");
    size_t bools[]={original.axis[0].stagger,original.axis[0].set[0],original.axis[0].bound[2],original.rules[0].all};
    for(size_t i=0;i<sizeof bools/sizeof *bools;++i){v=original;number_at(&v,bools[i],2);CHECK(rejected_vector(SYSTEM,&v),"system-boolean-overflow-rejected");}
    application_vector(&original,0,false);for(int i=0;i<4;++i){v=original;number_at(&v,v.flags[i],2);CHECK(rejected_vector(APPLICATION,&v),"application-boolean-overflow-rejected");}
    if(SIZE_MAX<UINT64_MAX){system_vector(&v,false,false);number_at(&v,v.axis[0].series,(uint64_t)SIZE_MAX+1);CHECK(rejected_vector(SYSTEM,&v),"size-t-overflow-rejected");}
    return 0;
}
static int malformed_case(void)
{
    Vector original,v;system_vector(&original,false,false);GeoDefinitionValue input=value(&original,SYSTEM);input.schema="wood.grid.system/2";
    CHECK(rejects(SYSTEM,&input,TEST_ID),"schema-mismatch-rejected");input=value(&original,SYSTEM);
    CHECK(rejects(SYSTEM,&input,TEST_ID+1),"system-identity-mismatch-rejected");
    authored_vector(&original,RULE);input=value(&original,RULE);GeoGridRule rule,before;memset(&rule,0xa5,sizeof rule);memcpy(&before,&rule,sizeof rule);
    CHECK(!wood_grid_decode_rule(&input,TEST_ID,7,&rule)&&!memcmp(&rule,&before,sizeof rule),"rule-key-mismatch-rejected");
    for(int kind=0;kind<4;++kind){authored_vector(&original,kind);input=value(&original,kind);
        for(size_t length=0;length<original.size;++length){input.content_size=length;CHECK(rejects(kind,&input,TEST_ID),"every-authored-truncation-is-atomic");}
        v=original;v.bytes[v.size++]=0;CHECK(rejected_vector(kind,&v),"authored-trailing-data-rejected");
        input=value(&original,kind);CHECK(rejects(kind,&input,TEST_ID+1),"each-authored-identity-is-checked");
        input.schema=NULL;CHECK(rejects(kind,&input,TEST_ID),"null-schema-rejected");input=value(&original,kind);input.content=NULL;
        CHECK(rejects(kind,&input,TEST_ID),"null-content-rejected");CHECK(rejects(kind,NULL,TEST_ID),"null-value-rejected");
        input=value(&original,kind);input.content_size=WOOD_GRID_CODEC_MAX_BYTES+1;CHECK(rejects(kind,&input,TEST_ID),"oversize-content-rejected");}
    const unsigned char surrogate[]={0xed,0xa0,0x80};standalone_rule_vector(&v,surrogate,sizeof surrogate);
    CHECK(rejected_vector(RULE,&v),"utf8-surrogate-rejected");
    const unsigned char bad_names[][4]={{0},{'A',0,'B'},{0x80},{0xc0,0xaf},{0xe0,0x80,0xaf},{0xf0,0x80,0x80,0xaf},{0xf4,0x90,0x80,0x80},{0xf5,0x80,0x80,0x80},{0xe2,0x82},{0xff},{0xc2,'A'}};
    const size_t lengths[]={1,3,1,2,3,4,4,4,2,1,2};
    for(size_t i=0;i<sizeof lengths/sizeof *lengths;++i){standalone_rule_vector(&v,bad_names[i],lengths[i]);CHECK(rejected_vector(RULE,&v),"malformed-utf8-or-nul-rejected");}
    const unsigned char valid_names[][4]={{0xc2,0x80},{0xe0,0xa0,0x80},{0xed,0x9f,0xbf},{0xf4,0x8f,0xbf,0xbf}};
    const size_t valid_lengths[]={2,3,3,4};
    for(size_t i=0;i<sizeof valid_lengths/sizeof *valid_lengths;++i){standalone_rule_vector(&v,valid_names[i],valid_lengths[i]);input=value(&v,RULE);
        CHECK(wood_grid_decode_rule(&input,TEST_ID,UINT32_MAX,&rule)&&!memcmp(rule.name,valid_names[i],valid_lengths[i])&&rule.name[valid_lengths[i]]==0,"utf8-boundary-codepoints-accepted");}
    standalone_rule_vector(&v,NULL,0);input=value(&v,RULE);CHECK(wood_grid_decode_rule(&input,TEST_ID,UINT32_MAX,&rule)&&!rule.name[0],"empty-incomplete-name-retained");
    system_vector(&v,false,false);number_at(&v,v.axis[0].number[0],1);CHECK(rejected_vector(SYSTEM,&v),"masked-number-nonzero-rejected");
    application_vector(&v,0,false);number_at(&v,v.axis[0].bound[0],1);CHECK(rejected_vector(APPLICATION,&v),"engineering-bound-slot-rejected");
    system_vector(&v,false,false);number_at(&v,v.axis[0].bound[2],1);number_at(&v,v.axis[0].number[2],0);CHECK(rejected_vector(SYSTEM,&v),"system-engineering-bound-rejected");
    application_vector(&v,0,false);number_at(&v,v.axis[0].number[2],1);CHECK(rejected_vector(APPLICATION,&v),"bound-cache-wire-number-must-be-zero");return 0;
}
static int bounds_case(void)
{
    Vector original,v;system_vector(&original,false,false);
    const uint64_t large[]={65,UINT64_MAX};
    for(size_t i=0;i<2;++i){v=original;number_at(&v,v.axis[0].count,large[i]);CHECK(rejected_vector(SYSTEM,&v),"coordinate-count-overflow-rejected");}
    for(size_t i=0;i<2;++i){v=original;number_at(&v,v.rule_count,i?UINT64_MAX:33);CHECK(rejected_vector(SYSTEM,&v),"rule-count-overflow-rejected");}
    unsigned char name[97];memset(name,'N',sizeof name);standalone_rule_vector(&v,name,sizeof name);CHECK(rejected_vector(RULE,&v),"name-capacity-rejected");
    standalone_rule_vector(&v,name,96);GeoDefinitionValue input=value(&v,RULE);GeoGridRule rule;
    CHECK(wood_grid_decode_rule(&input,TEST_ID,UINT32_MAX,&rule)&&strlen(rule.name)==96,"maximum-name-accepted");
    system_vector(&v,false,true);input=value(&v,SYSTEM);GeoGridSystem system;int main=0;
    CHECK(v.size==6584&&wood_grid_decode_system(&input,TEST_ID,NULL,&system,&main)&&system.rule_count==32&&system.axis[0].count==64&&system.axis[1].count==64&&strlen(system.rules[31].name)==96,"maximum-structural-system-accepted");
    unsigned char output[WOOD_GRID_CODEC_MAX_BYTES];size_t size=0;
    CHECK(wood_grid_encode_system_value(&system,main,output,sizeof output,&size)&&size==v.size&&!memcmp(output,v.bytes,size),"maximum-system-value-fits-bound");return 0;
}

/* Assign only active named fields over different sentinel bytes. This leaves
 * actual C padding, inactive coordinates/rules and string tails different. */
static void paint_axis(GeoGridAxisDef *out,const GeoGridAxisDef *in,unsigned char byte)
{
    memset(out,byte,sizeof *out);out->source=in->source;out->count=in->count;for(size_t i=0;i<in->count;++i)out->coords[i]=in->coords[i];
    out->start=in->start;out->step=in->step;out->body=in->body;out->gap=in->gap;out->anchor=in->anchor;out->stagger=in->stagger;
    out->series_count=in->series_count;out->anchor_explicit=in->anchor_explicit;out->stagger_set=in->stagger_set;
    for(size_t i=0;i<6;++i){out->parameters[i].set=in->parameters[i].set;out->parameters[i].parameter_id=in->parameters[i].parameter_id;out->parameters[i].field_id=in->parameters[i].field_id;}
}
static void paint_rule(GeoGridRule *out,const GeoGridRule *in,unsigned char byte)
{
    memset(out,byte,sizeof *out);out->key=in->key;memcpy(out->name,in->name,strlen(in->name)+1);out->all_cells=in->all_cells;
    for(int a=0;a<2;++a){out->cell[a]=in->cell[a];out->divisions[a]=in->divisions[a];}
}
static void paint_system(GeoGridSystem *out,const GeoGridSystem *in,unsigned char byte)
{
    memset(out,byte,sizeof *out);out->id=in->id;memcpy(out->name,in->name,strlen(in->name)+1);out->rule_count=in->rule_count;out->next_rule_key=in->next_rule_key;
    for(int a=0;a<2;++a)paint_axis(&out->axis[a],&in->axis[a],byte);
    for(size_t i=0;i<in->rule_count;++i)paint_rule(&out->rules[i],&in->rules[i],byte);
}
static void paint_application(WoodGridApplication *out,const WoodGridApplication *in,unsigned char byte)
{
    memset(out,byte,sizeof *out);out->id=in->id;out->placement_id=in->placement_id;out->from_system=in->from_system;out->from_binding=in->from_binding;
    out->binding_id=in->binding_id;out->lattice_cell=in->lattice_cell;out->system_id=in->system_id;out->main_along=in->main_along;out->is_subgrid=in->is_subgrid;out->parent_id=in->parent_id;
    for(int a=0;a<2;++a){out->lattice_base[a]=in->lattice_base[a];out->lattice_step[a]=in->lattice_step[a];out->lattice_index[a]=in->lattice_index[a];
        out->lattice_cell_index[a]=in->lattice_cell_index[a];out->system_origin[a]=in->system_origin[a];out->divisions[a]=in->divisions[a];
        for(int j=0;j<2;++j)out->cell_ref[a][j]=in->cell_ref[a][j];paint_axis(&out->axis[a],&in->axis[a],byte);}
}
static int system_value_case(void)
{
    Vector oracle;system_vector(&oracle,true,false);GeoGridSystem expected,out,a,b;expected_system(&expected,true,false);expected.next_rule_key=731;
    number_at(&oracle,oracle.next,731);unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES],other[WOOD_GRID_CODEC_MAX_BYTES];size_t size=17,other_size=19;
    CHECK(wood_grid_encode_system_value(&expected,-7,bytes,sizeof bytes,&size)&&size==oracle.size&&!memcmp(bytes,oracle.bytes,size),"system-value-independent-bytes");
    GeoDefinitionValue input={WOOD_GRID_SYSTEM_VALUE_SCHEMA,oracle.bytes,oracle.size};int main=0;
    CHECK(wood_grid_decode_system_value(&input,TEST_ID,&out,&main)&&main==-7&&same_system(&out,&expected),"system-value-every-field-roundtrip");
    paint_system(&a,&expected,0xa5);paint_system(&b,&expected,0x5a);
    CHECK(memcmp(&a,&b,sizeof a)&&wood_grid_encode_system_value(&a,-7,bytes,sizeof bytes,&size)&&wood_grid_encode_system_value(&b,-7,other,sizeof other,&other_size)&&size==other_size&&!memcmp(bytes,other,size)&&!memcmp(bytes,oracle.bytes,size),"system-value-excludes-padding-and-inactive-bytes");
    expected.id=0;CHECK(wood_grid_encode_system_value(&expected,INT_MIN,bytes,sizeof bytes,&size),"system-value-zero-id-write");input=(GeoDefinitionValue){WOOD_GRID_SYSTEM_VALUE_SCHEMA,bytes,size};
    CHECK(wood_grid_decode_system_value(&input,0,&out,&main)&&main==INT_MIN&&out.id==0,"system-value-zero-id-and-int-limit");return 0;
}
static int application_value_case(void)
{
    Vector oracle;WoodGridApplication expected,out,a,b;unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES],other[WOOD_GRID_CODEC_MAX_BYTES];size_t size,other_size;
    for(unsigned flags=0;flags<8;++flags){application_vector(&oracle,flags,true);expected_application(&expected,flags,true,false);
        CHECK(wood_grid_encode_application_value(&expected,bytes,sizeof bytes,&size)&&size==oracle.size&&!memcmp(bytes,oracle.bytes,size),"application-value-independent-bytes");
        GeoDefinitionValue input={WOOD_GRID_APPLICATION_VALUE_SCHEMA,oracle.bytes,oracle.size};
        CHECK(wood_grid_decode_application_value(&input,TEST_ID,&out)&&same_application(&out,&expected),"application-value-every-field-roundtrip");
        paint_application(&a,&expected,0xa5);paint_application(&b,&expected,0x5a);
        CHECK(memcmp(&a,&b,sizeof a)&&wood_grid_encode_application_value(&a,bytes,sizeof bytes,&size)&&wood_grid_encode_application_value(&b,other,sizeof other,&other_size)&&size==other_size&&!memcmp(bytes,other,size)&&!memcmp(bytes,oracle.bytes,size),"application-value-excludes-padding-and-inactive-bytes");}
    expected.id=0;CHECK(wood_grid_encode_application_value(&expected,bytes,sizeof bytes,&size),"binding-value-zero-grid-id-write");
    GeoDefinitionValue input={WOOD_GRID_APPLICATION_VALUE_SCHEMA,bytes,size};CHECK(wood_grid_decode_application_value(&input,0,&out)&&out.id==0,"binding-value-zero-grid-id-roundtrip");return 0;
}
static int atomic_case(void)
{
    Vector v;for(int kind=0;kind<4;++kind){authored_vector(&v,kind);v.bytes[v.size++]=0;CHECK(rejected_vector(kind,&v),"reader-failure-preserves-output-and-seed");}
    GeoGridSystem system;expected_system(&system,true,false);WoodGridApplication app;expected_application(&app,7,true,false);
    unsigned char bytes[WOOD_GRID_CODEC_MAX_BYTES],before[WOOD_GRID_CODEC_MAX_BYTES];memset(bytes,0xa5,sizeof bytes);memcpy(before,bytes,sizeof bytes);size_t size=937;
    CHECK(!wood_grid_encode_system_value(&system,-7,bytes,0,&size)&&size==937&&!memcmp(bytes,before,sizeof bytes),"writer-capacity-failure-is-atomic");
    CHECK(!wood_grid_encode_application_value(&app,bytes,1,&size)&&size==937&&!memcmp(bytes,before,sizeof bytes),"application-writer-capacity-failure-is-atomic");
    for(int bad=0;bad<5;++bad){GeoGridSystem changed=system;if(bad==0)changed.rule_count=33;else if(bad==1)changed.axis[0].count=65;
        else if(bad==2)memset(changed.name,'X',sizeof changed.name);else if(bad==3)memcpy(changed.rules[0].name,"\xed\xa0\x80",4);else changed.name[0]=(char)0xff;
        CHECK(!wood_grid_encode_system_value(&changed,0,bytes,sizeof bytes,&size)&&size==937&&!memcmp(bytes,before,sizeof bytes),"invalid-system-write-is-atomic");}
    app.axis[0].count=65;CHECK(!wood_grid_encode_application_value(&app,bytes,sizeof bytes,&size)&&size==937&&!memcmp(bytes,before,sizeof bytes),"invalid-application-write-is-atomic");
    CHECK(!wood_grid_encode_system_value(NULL,0,bytes,sizeof bytes,&size)&&!wood_grid_encode_application_value(NULL,bytes,sizeof bytes,&size)&&
        !wood_grid_encode_system_value(&system,0,NULL,sizeof bytes,&size)&&!wood_grid_encode_system_value(&system,0,bytes,sizeof bytes,NULL)&&size==937&&!memcmp(bytes,before,sizeof bytes),"null-writer-inputs-are-atomic");
    system_vector(&v,true,false);GeoGridSystem out,old;memset(&out,0xa5,sizeof out);memcpy(&old,&out,sizeof out);int main=937;
    for(size_t length=0;length<v.size;++length){GeoDefinitionValue input={WOOD_GRID_SYSTEM_VALUE_SCHEMA,v.bytes,length};
        CHECK(!wood_grid_decode_system_value(&input,TEST_ID,&out,&main)&&main==937&&!memcmp(&out,&old,sizeof out),"system-value-every-truncation-is-atomic");}
    for(int bad=0;bad<5;++bad){Vector changed=v;GeoDefinitionValue input={WOOD_GRID_SYSTEM_VALUE_SCHEMA,changed.bytes,changed.size};
        if(bad==0)input.schema="wood.grid.system/1";else if(bad==1)number_at(&changed,changed.id,TEST_ID+1);else if(bad==2)input.content_size=++changed.size;
        else if(bad==3)number_at(&changed,changed.axis[0].bound[2],1);else number_at(&changed,changed.rules[1].key,UINT64_MAX);
        CHECK(!wood_grid_decode_system_value(&input,TEST_ID,&out,&main)&&main==937&&!memcmp(&out,&old,sizeof out),"system-value-invalid-read-is-atomic");}
    application_vector(&v,7,true);WoodGridApplication app_out,app_old;memset(&app_out,0xa5,sizeof app_out);memcpy(&app_old,&app_out,sizeof app_out);
    for(size_t length=0;length<v.size;++length){GeoDefinitionValue input={WOOD_GRID_APPLICATION_VALUE_SCHEMA,v.bytes,length};
        CHECK(!wood_grid_decode_application_value(&input,TEST_ID,&app_out)&&!memcmp(&app_out,&app_old,sizeof app_out),"application-value-every-truncation-is-atomic");}
    for(int bad=0;bad<5;++bad){Vector changed=v;GeoDefinitionValue input={WOOD_GRID_APPLICATION_VALUE_SCHEMA,changed.bytes,changed.size};
        if(bad==0)input.schema="wood.grid.application/1";else if(bad==1)number_at(&changed,changed.id,TEST_ID+1);else if(bad==2)input.content_size=++changed.size;
        else if(bad==3)number_at(&changed,changed.axis[0].bound[2],1);else number_at(&changed,changed.flags[3],2);
        CHECK(!wood_grid_decode_application_value(&input,TEST_ID,&app_out)&&!memcmp(&app_out,&app_old,sizeof app_out),"application-value-invalid-read-is-atomic");}
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"authored"))return authored_case();if(!strcmp(argv[1],"derived"))return derived_case();
    if(!strcmp(argv[1],"scalars"))return scalars_case();if(!strcmp(argv[1],"malformed"))return malformed_case();
    if(!strcmp(argv[1],"bounds"))return bounds_case();if(!strcmp(argv[1],"system-value"))return system_value_case();
    if(!strcmp(argv[1],"application-value"))return application_value_case();if(!strcmp(argv[1],"atomic"))return atomic_case();return 2;
}
