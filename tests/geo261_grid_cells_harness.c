/* Independent public W fixture. Expected coordinates and errors are literals;
 * no old implementation or expected-value geometry algorithm is copied. */
#include "grid_application.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(condition,label) do{if(!(condition)){fprintf(stderr,"ASSERT:%s line=%d error=%s\n",label,__LINE__,error);return 1;}}while(0)

static WoodGridState state,before_state;
static WoodGridHost host,before_host;
static WoodGridContext context,before_context;
static char error[512];
static bool read_host(void *user,uint32_t id,WoodGridHost *out)
{const WoodGridHost *value=user;if(id!=value->id)return false;*out=*value;return true;}
static void rectangle(WoodBoundaryLoop *loop,GeoCoord u0,GeoCoord v0,GeoCoord u1,GeoCoord v1)
{memset(loop,0,sizeof *loop);loop->count=4;loop->v[0]=(GeoPoint2){u0,v0};loop->v[1]=(GeoPoint2){u1,v0};loop->v[2]=(GeoPoint2){u1,v1};loop->v[3]=(GeoPoint2){u0,v1};}
static void host_rect(WoodGridHost *h,uint32_t id,GeoCoord u0,GeoCoord v0,GeoCoord u1,GeoCoord v1)
{memset(h,0,sizeof *h);h->id=id;h->bounds=(GeoRect2){u0,v0,u1,v1};h->bounds_valid=true;h->component_count=1;rectangle(&h->components[0].outline,u0,v0,u1,v1);}
static void reset(void)
{
    memset(&state,0,sizeof state);memset(&before_state,0,sizeof before_state);memset(error,0,sizeof error);
    host_rect(&host,90,0,0,120,100);before_host=host;
    context=(WoodGridContext){.state=&state,.user=&host,.host=read_host};before_context=(WoodGridContext){.state=&before_state,.user=&before_host,.host=read_host};
    state.count=2;WoodGridApplication *p=&state.items[0],*c=&state.items[1];
    p->id=10;p->placement_id=90;p->main_along=2;p->axis[0].source=GEO_GRID_SOURCE_EXPLICIT;p->axis[0].count=4;
    p->axis[0].coords[0]=0;p->axis[0].coords[1]=30;p->axis[0].coords[2]=60;p->axis[0].coords[3]=120;
    c->id=20;c->placement_id=90;c->is_subgrid=true;c->parent_id=10;c->cell_ref[0][0]=WOOD_GRID_CELL_MIN;c->cell_ref[0][1]=1;
    c->cell_ref[1][0]=WOOD_GRID_CELL_MIN;c->cell_ref[1][1]=WOOD_GRID_CELL_MAX;c->divisions[0]=3;c->divisions[1]=4;
}
static void body_gap_parent(void)
{WoodGridApplication *p=&state.items[0];memset(&p->axis[0],0,sizeof p->axis[0]);p->axis[0].source=GEO_GRID_SOURCE_BODY_GAP;p->axis[0].body=30;p->axis[0].gap=3;p->axis[0].anchor=0;state.items[1].cell_ref[0][1]=0;state.items[1].divisions[0]=1;state.items[1].divisions[1]=2;}
static void lattice_parent(void)
{WoodGridApplication *p=&state.items[0];p->from_binding=true;p->main_along=0;p->lattice_base[0]=5;p->lattice_step[0]=30;p->lattice_index[0]=-2;p->lattice_base[1]=7;p->lattice_step[1]=20;p->lattice_index[1]=3;
 host_rect(&host,90,-120,-100,120,100);state.items[1].lattice_cell=true;state.items[1].lattice_cell_index[0]=-3;state.items[1].lattice_cell_index[1]=3;}
static bool cell(GeoRect2 *out)
{return wood_grid_cell_bounds(state.items,state.count,&state.items[1],&host,out,error,sizeof error);}

static int finite(void)
{
    GeoCoord lines[WOOD_GRID_MAX_LINES];size_t count=99;WoodGridApplication *p=&state.items[0];
    REQUIRE(wood_grid_axis_lines(p,&host,0,lines,&count,error,sizeof error)&&count==4,"finite-explicit-count");
    REQUIRE(lines[0]==0&&lines[1]==30&&lines[2]==60&&lines[3]==120,"finite-explicit-values");
    REQUIRE(!wood_grid_axis_lines(p,&host,1,lines,&count,error,sizeof error)&&count==0&&!strcmp(error,"這一軸沒有宣告格線"),"finite-missing-is-not-empty");
    REQUIRE(wood_grid_valid(p,&host),"finite-direction-v-has-u-lines");p->main_along=1;REQUIRE(!wood_grid_valid(p,&host),"finite-direction-u-needs-v-lines");p->main_along=2;
    body_gap_parent();REQUIRE(wood_grid_axis_lines(p,&host,0,lines,&count,error,sizeof error)&&count==3,"panel-count");
    REQUIRE(lines[0]==31&&lines[1]==64&&lines[2]==97,"panel-odd-gap-centers");
    host_rect(&host,90,0,0,32,100);REQUIRE(wood_grid_axis_lines(p,&host,0,lines,&count,error,sizeof error)&&count==0,"panel-zero-lines-valid");
    p->axis[0].anchor=-1;REQUIRE(!wood_grid_axis_lines(p,&host,0,lines,&count,error,sizeof error)&&!strcmp(error,"面材參數不合法（面材寬 > 0、縫寬非負、起算點須落在承載面範圍內）"),"panel-anchor-range");
    return 0;
}
static int adjacency(void)
{
    GeoRect2 r;REQUIRE(cell(&r)&&r.min_u==0&&r.max_u==30&&r.min_v==0&&r.max_v==100,"cell-exact-bounds");
    state.items[1].cell_ref[0][1]=2;
    REQUIRE(!cell(&r)&&!strcmp(error,"I25：子格 20 的父格 10 u 軸兩界須存在、採標準參照且彼此相鄰"),"adjacent-only");
    state.items[1].cell_ref[0][1]=0;REQUIRE(!cell(&r),"min-alias-rejects-line-at-min");
    state.items[1].cell_ref[0][0]=2;state.items[1].cell_ref[0][1]=3;REQUIRE(!cell(&r),"max-alias-rejects-line-at-max");
    state.items[1].cell_ref[0][1]=WOOD_GRID_CELL_MAX;REQUIRE(cell(&r)&&r.min_u==60&&r.max_u==120,"canonical-max");
    state.items[1].lattice_cell=true;REQUIRE(!cell(&r)&&!strcmp(error,"D19/I37: subgrid cell index space must match its parent grid"),"index-space-exact");
    return 0;
}
static int division(void)
{
    GeoCoord lines[WOOD_GRID_MAX_LINES],coordinate=-999;size_t n=0,total=99;WoodGridApplication *g=&state.items[1];
    REQUIRE(wood_grid_axis_lines_in(state.items,state.count,g,&host,0,lines,&n,error,sizeof error)&&n==2&&lines[0]==10&&lines[1]==20,"divide-u-exact");
    REQUIRE(wood_grid_axis_lines_in(state.items,state.count,g,&host,1,lines,&n,error,sizeof error)&&n==3&&lines[0]==25&&lines[1]==50&&lines[2]==75,"divide-v-exact");
    REQUIRE(wood_grid_line_coord_in(state.items,state.count,g,&host,0,1,&coordinate,&total,error,sizeof error)&&coordinate==20&&total==2,"child-index-value");
    REQUIRE(!wood_grid_line_coord_in(state.items,state.count,g,&host,0,2,&coordinate,&total,error,sizeof error)&&total==2&&!strcmp(error,"I23: 網格 20 u 軸索引 2 超出範圍（本軸共 2 條）"),"child-index-range");
    g->divisions[0]=7;REQUIRE(!wood_grid_axis_lines_in(state.items,state.count,g,&host,0,lines,&n,error,sizeof error)&&!strcmp(error,"I25：子格 20（父格 10）u 軸跨度 30 mm 無法精確分成 7 等分；等分數須為 1…65"),"no-rounded-subdivision");
    g->divisions[0]=1;REQUIRE(wood_grid_axis_lines_in(state.items,state.count,g,&host,0,lines,&n,error,sizeof error)&&n==0,"one-part-has-zero-inner-lines");
    g->divisions[0]=66;REQUIRE(!wood_grid_axis_lines_in(state.items,state.count,g,&host,0,lines,&n,error,sizeof error),"division-capacity");
    return 0;
}
static int area(void)
{
    WoodGridApplication *p=&state.items[0],*g=&state.items[1];GeoRect2 r;
    p->axis[0].count=2;p->axis[0].coords[0]=30;p->axis[0].coords[1]=60;p->axis[1].source=GEO_GRID_SOURCE_EXPLICIT;p->axis[1].count=2;p->axis[1].coords[0]=20;p->axis[1].coords[1]=80;
    g->cell_ref[0][0]=0;g->cell_ref[0][1]=1;g->cell_ref[1][0]=0;g->cell_ref[1][1]=1;
    host.components[0].hole_count=1;rectangle(&host.components[0].holes[0],30,20,60,80);
    REQUIRE(!cell(&r)&&!strcmp(error,"I25：子格 20 的父格 10 所選矩形與有效面沒有正面積交集"),"positive-area-not-bbox");
    rectangle(&host.components[0].holes[0],31,20,60,80);REQUIRE(cell(&r),"one-mm-positive-area");
    host.components[0].hole_count=0;rectangle(&host.components[0].outline,0,0,30,100);host.component_count=2;rectangle(&host.components[1].outline,60,0,120,100);
    REQUIRE(!cell(&r),"touching-component-boundaries-not-area");rectangle(&host.components[1].outline,59,0,120,100);REQUIRE(cell(&r),"second-component-area");
    return 0;
}
static int lattice(void)
{
    lattice_parent();GeoRect2 r;GeoCoord x,lines[WOOD_GRID_MAX_LINES];size_t n,total=99;WoodGridApplication *p=&state.items[0],*c=&state.items[1];
    REQUIRE(cell(&r)&&r.min_u==-25&&r.max_u==5&&r.min_v==7&&r.max_v==27,"signed-lattice-cell");
    REQUIRE(wood_grid_axis_lines_in(state.items,state.count,c,&host,0,lines,&n,error,sizeof error)&&n==2&&lines[0]==-15&&lines[1]==-5,"signed-inner-lines");
    REQUIRE(wood_grid_line_coord_in(state.items,state.count,p,&host,0,1000,&x,&total,error,sizeof error)&&x==30065&&total==0,"offscreen-index-exists");
    c->lattice_cell_index[0]=INT64_MAX;REQUIRE(!cell(&r)&&strstr(error,"signed-index or D1"),"cell-successor-overflow");
    host.bounds_valid=false;REQUIRE(wood_grid_valid(p,&host),"lattice-validity-does-not-query-visible-bounds");
    REQUIRE(!wood_grid_axis_lines(p,&host,0,lines,&n,error,sizeof error),"lattice-query-needs-bounds");
    host.bounds_valid=true;p->lattice_base[0]=0;p->lattice_index[0]=0;p->lattice_step[0]=1;
    REQUIRE(!wood_grid_axis_lines(p,&host,0,lines,&n,error,sizeof error)&&!strcmp(error,"R32: QUERY_CAPACITY requires 241 lines; limit 64"),"exact-query-never-samples");
    return 0;
}
static int bands(void)
{
    lattice_parent();WoodGridApplication *p=&state.items[0];GeoCoord x=0;p->axis[0].stagger_set=true;p->axis[0].stagger=-7;
    REQUIRE(!wood_grid_anchor_line_coord(state.items,state.count,p,&host,0,-3,false,0,&x,error,sizeof error)&&!strcmp(error,"I24: 有相位差的格線必須寫 band，不默認第 0 格"),"missing-band-rejected");
    REQUIRE(wood_grid_anchor_line_coord(state.items,state.count,p,&host,0,-3,true,-1,&x,error,sizeof error)&&x==-32,"negative-odd-band");
    REQUIRE(wood_grid_anchor_line_coord(state.items,state.count,p,&host,0,-3,true,-2,&x,error,sizeof error)&&x==-25,"negative-even-band");
    p->axis[0].stagger_set=false;REQUIRE(!wood_grid_anchor_line_coord(state.items,state.count,p,&host,0,-3,true,0,&x,error,sizeof error)&&!strcmp(error,"I24: 沒有相位差的格線不能寫 band"),"extra-band-rejected");
    p->axis[0].stagger_set=true;p->axis[0].stagger=1;p->lattice_base[0]=GEO_COORD_LIMIT;p->lattice_index[0]=0;
    REQUIRE(!wood_grid_anchor_line_coord(state.items,state.count,p,&host,0,0,true,1,&x,error,sizeof error)&&!strcmp(error,"D10b/D1: 錯開後的格線座標超出可表達範圍"),"shift-output-range");
    return 0;
}
static int duplicate(void)
{
    state.items[2]=state.items[1];state.items[2].id=21;state.count=3;
    REQUIRE(!wood_grid_world_valid(&context,error,sizeof error)&&!strcmp(error,"I25：父格 10 的這個格子已有子格 21"),"duplicate-child-rejected");
    state.count=2;state.items[0].axis[0].stagger_set=true;
    REQUIRE(!wood_grid_valid_in(state.items,state.count,&state.items[1],&host,error,sizeof error)&&!strcmp(error,"I24：有相位差的主格 10 不能建立子網格"),"stagger-parent-rejected");
    state.items[1].main_along=1;
    REQUIRE(!wood_grid_valid_in(state.items,state.count,&state.items[1],&host,error,sizeof error)&&!strcmp(error,"I25：子格 20 至少一軸須大於 1 等分；子格不設定主支方向"),"child-direction-error-precedes-stagger");
    reset();state.items[1]=state.items[0];state.items[1].id=11;
    REQUIRE(!wood_grid_world_valid(&context,error,sizeof error)&&!strcmp(error,"I10：面 90 只能有一組主網格"),"one-parent-per-face");
    return 0;
}
static int cardinality(void)
{
    body_gap_parent();before_state=state;before_host=host;context.before=&before_context;
    host_rect(&host,90,0,0,150,100);
    REQUIRE(!wood_grid_world_valid(&context,error,sizeof error)&&!strcmp(error,"I23：父網格 10 仍有子格，u 軸線數不可從 3 改成 4；請先處理子格與引用"),"parent-cardinality-locked");
    host=before_host;state.items[0].axis[0].gap=2;
    REQUIRE(wood_grid_world_valid(&context,error,sizeof error),"equal-count-lines-may-move");
    state.items[0].from_binding=true;state.items[0].lattice_step[0]=30;state.items[0].lattice_step[1]=20;
    REQUIRE(!wood_grid_parent_count_valid(&before_context,&state.items[0],&host,error,sizeof error)&&!strcmp(error,"I37: a parent grid cannot change its ordinal/lattice index space"),"index-space-cannot-change");
    before_state.items[0].from_binding=true;REQUIRE(wood_grid_parent_count_valid(&before_context,&state.items[0],&host,error,sizeof error),"infinite-visibility-count-not-identity");
    return 0;
}
static int family(void)
{
    body_gap_parent();before_state=state;before_host=host;context.before=&before_context;WoodGridState untouched=state;WoodGridHost target;
    host_rect(&target,71,0,0,120,100);
    REQUIRE(wood_grid_family_fits(&context,&state.items[0],&target),"whole-family-fits-new-id");
    REQUIRE(!memcmp(&state,&untouched,sizeof state),"family-probe-does-not-mutate");
    host_rect(&target,71,0,0,60,100);REQUIRE(!wood_grid_family_fits(&context,&state.items[0],&target),"family-keeps-old-geometry-count");
    context.before=NULL;REQUIRE(wood_grid_family_fits(&context,&state.items[0],&target),"same-family-without-old-count-lock");
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;reset();int result;
    if(!strcmp(argv[1],"finite"))result=finite();else if(!strcmp(argv[1],"adjacency"))result=adjacency();else if(!strcmp(argv[1],"division"))result=division();
    else if(!strcmp(argv[1],"area"))result=area();else if(!strcmp(argv[1],"lattice"))result=lattice();else if(!strcmp(argv[1],"bands"))result=bands();
    else if(!strcmp(argv[1],"duplicate"))result=duplicate();else if(!strcmp(argv[1],"cardinality"))result=cardinality();else if(!strcmp(argv[1],"family"))result=family();else return 2;
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
