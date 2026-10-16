/* Public W finish/fill policy: independent D41-D44 / R41-R43 oracles. */
#include "finish.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s line=%d error=%s\n",n,__LINE__,error);return 1;}}while(0)
static FinishSurfaceState state;
static EngineeringState engineering;
static GeoVersionStore *versions;
static void free_versions(void){geo_versions_destroy(versions);versions=NULL;}
static WoodBoundaryRegion region;
static WoodFinishContext context;
static FsDiagnosticKind diagnostic;
static char error[512],parameter_error[512];
static bool boundary_available,box_available,parameter_available[3];
static GeoCoord box_lo[64][3],box_hi[64][3],coordinates[2];
static GeoQuantity threshold;
static unsigned boundary_calls,box_calls,parameter_calls,parameter_log[8],engineering_calls,derived_calls;
static bool derived_remove;
static bool boundary(void *user,uint32_t id,WoodBoundaryRegion *out)
{(void)user;++boundary_calls;if(!boundary_available||id!=8)return false;*out=region;return true;}
static bool obstacle(void *user,const FinishObstacleRef *ref,GeoCoord lo[3],GeoCoord hi[3])
{(void)user;++box_calls;if(!box_available||ref->id>=64)return false;memcpy(lo,box_lo[ref->id],sizeof box_lo[0]);memcpy(hi,box_hi[ref->id],sizeof box_hi[0]);return true;}
static bool parameter_coord(void *user,GeoParameterRef ref,GeoCoord *out)
{(void)user;if(parameter_calls<8)parameter_log[parameter_calls]=ref.field_id;++parameter_calls;
 if(ref.parameter_id!=90||ref.field_id<1||ref.field_id>2||!parameter_available[ref.field_id-1])return false;*out=coordinates[ref.field_id-1];return true;}
static bool parameter_value(void *user,GeoParameterRef ref,GeoQuantity *out)
{(void)user;if(parameter_calls<8)parameter_log[parameter_calls]=ref.field_id;++parameter_calls;
 if(ref.parameter_id!=90||ref.field_id!=3||!parameter_available[2])return false;*out=threshold;return true;}
static bool engineering_operation(void *user,GeoJson *j,int t)
{(void)user;(void)j;(void)t;++engineering_calls;return true;}
static bool derived_operation(void *user,GeoJson *j,int t,bool remove)
{(void)user;(void)j;(void)t;++derived_calls;derived_remove=remove;return true;}
static void rectangle(WoodBoundaryLoop *loop,GeoCoord u0,GeoCoord v0,GeoCoord u1,GeoCoord v1)
{memset(loop,0,sizeof *loop);loop->count=4;loop->v[0]=(GeoPoint2){u0,v0};loop->v[1]=(GeoPoint2){u1,v0};loop->v[2]=(GeoPoint2){u1,v1};loop->v[3]=(GeoPoint2){u0,v1};}
static void reset(void)
{
 free_versions();if(geo_versions_create(&versions)!=GEO_VERSION_OK){fputs("SETUP:version storage\n",stderr);exit(2);}
 memset(&state,0,sizeof state);memset(&engineering,0,sizeof engineering);memset(&region,0,sizeof region);memset(error,0,sizeof error);
 memset(box_lo,0,sizeof box_lo);memset(box_hi,0,sizeof box_hi);memset(parameter_log,0,sizeof parameter_log);
 region.id=8;rectangle(&region.outline,0,0,100,100);boundary_available=box_available=true;
 for(int i=0;i<3;++i)parameter_available[i]=true;
 coordinates[0]=3;coordinates[1]=-20;threshold=(GeoQuantity){8,1,1};diagnostic=FS_DIAGNOSTIC_INVALID;strcpy(parameter_error,"selected parameter unavailable");
 boundary_calls=box_calls=parameter_calls=engineering_calls=derived_calls=0;derived_remove=false;
 context=(WoodFinishContext){.state=&state,.engineering={.state=&engineering,.error=error,.error_capacity=sizeof error,.versions=versions},
   .error=error,.error_capacity=sizeof error,.diagnostic=&diagnostic,.boundary=boundary,.obstacle_box=obstacle,
   .parameter_coord=parameter_coord,.parameter_value=parameter_value,.parameter_error=parameter_error,.parameter_error_capacity=sizeof parameter_error,
   .engineering_operation=engineering_operation,.derived_operation=derived_operation};
}
static FinishSurface finish(uint32_t id)
{FinishSurface f={0};f.id=id;f.boundary_id=8;f.frame=(GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};f.side=1;strcpy(f.name,"finish");return f;}
static bool json_record(const char *text,int kind,void *out)
{
 GeoJson j={0};if(!geo_json_parse(&j,text)){geo_json_free(&j);return false;}
 bool ok=kind==0?wood_fs_put(&context,&j,0):kind==1?wood_fs_operation(&context,&j,0):
   kind==2?wood_pf_parse(&context,&j,0,out):wood_eng_publish_material(&context.engineering,&j,0,NULL);
 geo_json_free(&j);return ok;
}
static bool put_finish(uint32_t id,const char *name)
{char text[512];snprintf(text,sizeof text,"{\"id\":%u,\"name\":\"%s\",\"boundaryId\":8,\"frame\":{\"origin\":[0,0,0],\"U\":\"+X\",\"V\":\"+Y\",\"N\":\"+Z\"},\"structureSide\":1,\"obstacles\":[]}",id,name);return json_record(text,0,NULL);}
static bool material(uint32_t version,const char *thickness)
{char text[512];snprintf(text,sizeof text,"{\"id\":\"board\",\"version\":%u,\"kind\":\"panel\",\"name\":\"board\",\"width\":100,\"length\":100%s%s%s}",version,thickness?",\"thickness\":\"":"",thickness?thickness:"",thickness?"\"":"");return json_record(text,3,NULL);}
static const char *fill_json="{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":0,\"pattern\":\"straight\",\"threshold\":{\"parameterId\":90,\"fieldId\":3}}";
static bool seed(PanelFill *p)
{state.items[0]=finish(1);state.count=1;return material(1,"9.000")&&json_record(fill_json,2,p);}
static void box(unsigned id,GeoCoord x0,GeoCoord y0,GeoCoord z0,GeoCoord x1,GeoCoord y1,GeoCoord z1)
{box_lo[id][0]=x0;box_lo[id][1]=y0;box_lo[id][2]=z0;box_hi[id][0]=x1;box_hi[id][1]=y1;box_hi[id][2]=z1;}
static bool zeroed(const void *p,size_t n)
{const unsigned char *s=p;for(size_t i=0;i<n;++i)if(s[i])return false;return true;}

static int names(void)
{
 unsigned char text[110];memset(text,'a',sizeof text);
 REQUIRE(wood_fs_name_check(&context,text,96),"name-exact-capacity");
 REQUIRE(!wood_fs_name_check(&context,text,97)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&strstr(error,"96 bytes"),"name-capacity-diagnostic");
 text[100]=0xc0;text[101]=0x80;
 REQUIRE(!wood_fs_name_check(&context,text,102)&&diagnostic==FS_DIAGNOSTIC_INVALID&&strstr(error,"printable UTF-8"),"name-entire-input-before-capacity");
 for(size_t i=0;i<96;i+=3){text[i]=0xe7;text[i+1]=0x95;text[i+2]=0x8c;}
 REQUIRE(wood_fs_name_check(&context,text,96),"name-unicode-byte-capacity");
 static const unsigned char bad[][5]={{0},{0x1f},{0x7f},{0xc2,0x85},{0xe7,0x95},{0xed,0xa0,0x80},{0xf4,0x90,0x80,0x80}};
 static const size_t lengths[]={0,1,1,2,2,3,4};
 for(size_t i=0;i<sizeof lengths/sizeof lengths[0];++i)REQUIRE(!wood_fs_name_check(&context,bad[i],lengths[i])&&diagnostic==FS_DIAGNOSTIC_INVALID,"name-invalid-scalars-controls");
 WoodFinishContext small=context;char short_error[6];small.error=short_error;small.error_capacity=sizeof short_error;
 REQUIRE(!wood_fs_error(&small,"A\xe7\x95\x8c\xe7\x95\x8c")&&!strcmp(short_error,"A\xe7\x95\x8c")&&diagnostic==FS_DIAGNOSTIC_INVALID,"diagnostic-utf8-tail");
 REQUIRE(!wood_fs_capacity_error(&small,"capacity")&&diagnostic==FS_DIAGNOSTIC_CAPACITY,"diagnostic-kind");
 return 0;
}

static int obstacles(void)
{
 FinishObstacleRef r;char text[16];
 REQUIRE(wood_fs_obstacle_parse("c0",&r)&&r.kind==FS_OBSTACLE_COLUMN&&r.id==0,"obstacle-zero-id");
 REQUIRE(wood_fs_obstacle_parse("b4294967295",&r)&&r.kind==FS_OBSTACLE_BEAM&&r.id==UINT32_MAX,"obstacle-max-id");
 wood_fs_obstacle_text(&r,text);REQUIRE(!strcmp(text,"b4294967295"),"obstacle-canonical-text");
 static const char *bad[]={"c","c00","b01","c-1","c+1","C1","b4294967296","p1","1","c1x"};
 for(size_t i=0;i<sizeof bad/sizeof bad[0];++i)REQUIRE(!wood_fs_obstacle_parse(bad[i],&r),"obstacle-canonical-only");
 FinishSurface f=finish(1);f.obstacle_count=5;f.obstacles[0]=(FinishObstacleRef){1,1};f.obstacles[1]=(FinishObstacleRef){0,10};
 f.obstacles[2]=(FinishObstacleRef){1,0};f.obstacles[3]=(FinishObstacleRef){0,2};f.obstacles[4]=(FinishObstacleRef){0,0};
 REQUIRE(wood_fs_obstacles_normalize(&context,&f),"obstacle-sort");
 static const FinishObstacleRef ordered[]={{0,0},{0,2},{0,10},{1,0},{1,1}};
 REQUIRE(!memcmp(f.obstacles,ordered,sizeof ordered),"obstacle-typed-numeric-order");
 f.obstacles[4]=f.obstacles[3];REQUIRE(!wood_fs_obstacles_normalize(&context,&f)&&strstr(error,"b0 more than once"),"obstacle-duplicate");
 rectangle(&region.outline,-100,-100,100,100);box(0,12,23,35,16,28,41);f=finish(1);f.frame.origin=(GeoPoint3){10,20,30};r=(FinishObstacleRef){0,0};
 static const GeoVector3 axes[6][3]={{{1,0,0},{0,1,0},{0,0,1}},{{-1,0,0},{0,1,0},{0,0,-1}},{{0,1,0},{0,0,1},{1,0,0}},{{0,-1,0},{0,0,1},{-1,0,0}},{{0,0,1},{1,0,0},{0,1,0}},{{0,0,-1},{1,0,0},{0,-1,0}}};
 static const GeoCoord expected[6][6]={{2,3,6,8,5,11},{-6,3,-2,8,-11,-5},{3,5,8,11,2,6},{-8,5,-3,11,-6,-2},{5,2,11,6,3,8},{-11,2,-5,6,-8,-3}};
 for(int i=0;i<6;++i){f.frame.axis_u=axes[i][0];f.frame.axis_v=axes[i][1];f.frame.normal=axes[i][2];
   for(int side=-1;side<=1;side+=2){FsObstacleView view;f.side=side;REQUIRE(geo_frame_is_valid(&f.frame)&&wood_fs_obstacle_view(&context,&f,&r,&view),"projection-valid-frames");
     REQUIRE(!memcmp(view.rect,expected[i],4*sizeof(GeoCoord)),"projection-all-axis-signs");
     REQUIRE(view.q[0]==(side>0?expected[i][4]:-expected[i][5])&&view.q[1]==(side>0?expected[i][5]:-expected[i][4]),"projection-structure-side");
     REQUIRE(view.relation==FS_INTERIOR,"projection-relation");}}
 f=finish(1);f.frame.origin.x=-GEO_COORD_LIMIT;box(0,GEO_COORD_LIMIT,0,0,GEO_COORD_LIMIT,1,1);boundary_available=false;boundary_calls=0;
 FsObstacleView view;REQUIRE(!wood_fs_obstacle_view(&context,&f,&r,&view)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&boundary_calls==0,"projection-local-capacity-before-boundary");
 f=finish(1);f.frame.origin.z=-GEO_COORD_LIMIT;box(0,0,0,GEO_COORD_LIMIT,1,1,GEO_COORD_LIMIT);
 REQUIRE(!wood_fs_obstacle_view(&context,&f,&r,&view)&&diagnostic==FS_DIAGNOSTIC_CAPACITY,"projection-depth-capacity");
 box_available=false;REQUIRE(!wood_fs_obstacle_view(&context,&f,&r,&view)&&diagnostic==FS_DIAGNOSTIC_INVALID&&strstr(error,"obstacle c0 does not exist"),"projection-missing-source-first");
 return 0;
}

static int relations(void)
{
 region.hole_count=1;rectangle(&region.holes[0],40,40,60,60);
 static const GeoCoord rects[][4]={{10,10,20,20},{45,45,55,55},{40,45,50,55},{30,45,50,55},{100,10,110,20},{100,100,110,110},{101,10,110,20},{40,40,60,60}};
 static const int expected[]={FS_INTERIOR,FS_SEPARATE,FS_TOUCH,FS_INTERIOR,FS_TOUCH,FS_TOUCH,FS_SEPARATE,FS_TOUCH};
 REQUIRE(wood_fs_relation(&region,rects[1])==FS_SEPARATE,"relation-hole-interior-excluded");
 REQUIRE(wood_fs_relation(&region,rects[4])==FS_TOUCH,"relation-edge-touch-closed");
 for(size_t i=0;i<sizeof expected/sizeof expected[0];++i)REQUIRE(wood_fs_relation(&region,rects[i])==expected[i],"relation-positive-area-not-bbox");
 GeoPoint2 notch[]={{0,0},{100,0},{100,40},{40,40},{40,100},{0,100}};memcpy(region.outline.v,notch,sizeof notch);region.outline.count=6;region.hole_count=0;
 REQUIRE(wood_fs_relation(&region,(GeoCoord[]){50,50,90,90})==FS_SEPARATE,"relation-concave-notch");
 REQUIRE(wood_fs_relation(&region,(GeoCoord[]){40,50,90,90})==FS_TOUCH,"relation-concave-contact");
 GeoLoop2View loop={region.outline.v,region.outline.count};
 REQUIRE(geo_loop_rect_intersection_area(&loop,&(GeoRect2){20,20,80,80})==2000,"intersection-exact-concave-area");
 REQUIRE(!strcmp(wood_fs_relation_name(FS_INTERIOR),"interior")&&!strcmp(wood_fs_relation_name(FS_TOUCH),"touch")&&!strcmp(wood_fs_relation_name(FS_SEPARATE),"separate"),"relation-names");
 return 0;
}

static int materials(void)
{
 PanelFill p;WoodFinishLayout d={0};state.items[0]=finish(1);state.count=1;
 REQUIRE(json_record("{\"id\":\"board\",\"version\":1,\"kind\":\"panel\",\"name\":\"board\",\"width\":40,\"length\":60,\"thickness\":\"9.000\"}",3,NULL)&&json_record(fill_json,2,&p)&&wood_pf_values(&context,&p,&d)&&d.t==9,"thickness-exact-decimal-integer");
 REQUIRE(material(2,"12.000")&&material(3,"9.5")&&material(4,NULL)&&material(5,"100000001"),"material-fixed-versions");
 REQUIRE(wood_pf_values(&context,&p,&d)&&d.t==9&&d.layout.size[0]==40&&d.layout.size[1]==60,"material-fixed-selected-version");
 p.length_axis=0;REQUIRE(wood_pf_values(&context,&p,&d)&&d.layout.size[0]==60&&d.layout.size[1]==40,"material-length-field-axis");
 p.panel.version=2;REQUIRE(wood_pf_values(&context,&p,&d)&&d.t==12,"material-second-version");
 p.panel.version=3;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"no rounding")&&diagnostic==FS_DIAGNOSTIC_INVALID,"thickness-no-fractional-rounding");
 p.panel.version=4;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"explicitly set"),"thickness-required-without-obstacles");
 p.panel.version=5;REQUIRE(!wood_pf_values(&context,&p,&d),"thickness-bounded-integer");
 char long_decimal[ENG_THICKNESS_CAPACITY];long_decimal[0]='9';long_decimal[1]='.';memset(long_decimal+2,'0',sizeof long_decimal-3);long_decimal[sizeof long_decimal-1]=0;
 REQUIRE(material(6,long_decimal),"thickness-full-precision-source");p.panel.version=6;
 REQUIRE(wood_pf_values(&context,&p,&d)&&d.t==9,"thickness-full-zero-tail");
 long_decimal[sizeof long_decimal-2]='1';REQUIRE(material(7,long_decimal),"thickness-last-digit-source");p.panel.version=7;
 REQUIRE(!wood_pf_values(&context,&p,&d),"thickness-last-digit-no-rounding");
 p.panel.version=99;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"existing fixed panel material version"),"material-missing-version");
 REQUIRE(json_record("{\"id\":\"timber\",\"version\":1,\"kind\":\"timber\",\"name\":\"t\",\"A\":27,\"B\":33}",3,NULL),"material-timber-published");
 strcpy(p.panel.id,"timber");p.panel.version=1;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"existing fixed panel material version"),"material-panel-kind-required");
 p.finish_id=99;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"missing finish surface 99"),"material-finish-error-first");
 return 0;
}

static int sources(void)
{
 PanelFill p;WoodFinishLayout d={0};REQUIRE(seed(&p),"sources-seed");
 p.gap_ref=(GeoParameterRef){true,90,1};p.stagger_ref=(GeoParameterRef){true,90,2};p.stagger_axis=0;
 threshold=(GeoQuantity){1,3,1};REQUIRE(wood_pf_values(&context,&p,&d)&&d.layout.gap==3&&d.layout.stagger==-20,"sources-exact-positive-rational");
 REQUIRE(parameter_calls==3&&parameter_log[0]==1&&parameter_log[1]==2&&parameter_log[2]==3,"sources-evaluation-order");
 parameter_calls=0;parameter_available[0]=false;REQUIRE(!wood_pf_values(&context,&p,&d)&&parameter_calls==1&&!strcmp(error,"selected parameter unavailable"),"sources-first-failure-short-circuit");
 parameter_available[0]=true;parameter_available[1]=false;parameter_calls=0;REQUIRE(!wood_pf_values(&context,&p,&d)&&parameter_calls==2,"sources-second-failure-short-circuit");
 parameter_available[1]=true;parameter_available[2]=false;parameter_calls=0;REQUIRE(!wood_pf_values(&context,&p,&d)&&parameter_calls==3,"sources-threshold-failure");
 parameter_available[2]=true;threshold.num=0;coordinates[0]=-1;
 REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"threshold must be a positive dimension"),"threshold-before-gap");
 threshold.num=1;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"gap must be nonnegative"),"gap-nonnegative");
 coordinates[0]=3;coordinates[1]=103;REQUIRE(!wood_pf_values(&context,&p,&d)&&strstr(error,"whole pitch"),"stagger-not-whole-pitch");
 coordinates[1]=-103;REQUIRE(!wood_pf_values(&context,&p,&d),"stagger-negative-whole-pitch");
 coordinates[1]=0;REQUIRE(!wood_pf_values(&context,&p,&d),"stagger-nonzero");
 coordinates[1]=-20;coordinates[0]=0;REQUIRE(wood_pf_values(&context,&p,&d),"zero-gap-negative-stagger-valid");
 REQUIRE(!json_record("{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":0,\"pattern\":\"straight\",\"stagger\":{\"axis\":\"u\",\"value\":1},\"threshold\":{\"parameterId\":90,\"fieldId\":3}}",2,&p),"straight-omits-stagger");
 REQUIRE(json_record(fill_json,2,&p)&&p.threshold.set&&p.threshold.parameter_id==90&&p.threshold.field_id==3&&!p.gap_ref.set&&p.stagger_axis==-1,"sources-authored-definition");
 REQUIRE(strstr(p.definition,"\"threshold\":{\"fieldId\":3,\"parameterId\":90}")!=NULL,"sources-canonical-reference");
 REQUIRE(!json_record("{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":{\"parameterId\":-1,\"fieldId\":1},\"pattern\":\"straight\",\"threshold\":{\"parameterId\":90,\"fieldId\":3}}",2,&p)&&!strcmp(error,"D42: source must be integer mm or ParameterRef")&&!strcmp(parameter_error,"I38 ID: expected uint32 identity"),"source-invalid-id-dual-diagnostic");
 return 0;
}

static int operations(void)
{
 REQUIRE(!wood_fs_used(&context)&&put_finish(1,"first")&&put_finish(2,"second")&&wood_fs_used(&context),"finish-put");
 FinishSurface before=state.items[0];
 REQUIRE(!put_finish(1,"")&&!memcmp(&before,&state.items[0],sizeof before),"finish-invalid-put-atomic");
 REQUIRE(put_finish(1,"replaced")&&state.count==2&&!strcmp(state.items[0].name,"replaced"),"finish-replace-position");
 state.items[0].obstacle_count=2;state.items[0].obstacles[0]=(FinishObstacleRef){0,0};state.items[0].obstacles[1]=(FinishObstacleRef){1,7};
 REQUIRE(wood_fs_reference_owner(&context,"boundary",8)==1&&wood_fs_reference_owner(&context,"column",0)==1&&wood_fs_reference_owner(&context,"beam",7)==1&&wood_fs_reference_owner(&context,"column",7)==0&&wood_fs_reference_owner(&context,"other",8)==0,"finish-typed-reference-owner");
 REQUIRE(wood_fs_delete(&context,1)&&state.count==1&&state.items[0].id==2&&zeroed(&state.items[1],sizeof state.items[1]),"finish-delete-compaction");
 REQUIRE(!wood_fs_delete(&context,1)&&state.count==1,"finish-delete-missing");
 REQUIRE(!json_record("{\"op\":\"put-parameter\"}",1,NULL)&&engineering_calls==0&&strstr(error,"PF-2 scope"),"operation-scoped-without-host");
 state.host_count=1;REQUIRE(json_record("{\"op\":\"put-parameter\"}",1,NULL)&&engineering_calls==1,"operation-scoped-host-edit");
 REQUIRE(json_record("{\"op\":\"put-derived-placement\"}",1,NULL)&&derived_calls==1&&!derived_remove,"operation-derived-put");
 REQUIRE(json_record("{\"op\":\"delete-derived-placement\"}",1,NULL)&&derived_calls==2&&derived_remove,"operation-derived-delete");
 REQUIRE(!json_record("{\"op\":\"publish-material\"}",1,NULL)&&engineering_calls==1&&strstr(error,"publish-material"),"operation-no-undisclosed-material");
 char text[1400];snprintf(text,sizeof text,"{\"op\":\"put-panel-fill\",\"value\":%s}",fill_json);
 REQUIRE(json_record(text,1,NULL)&&state.fill_count==1&&wood_pf_find(&context,1),"operation-fill-put");
 REQUIRE(json_record("{\"op\":\"delete-panel-fill\",\"id\":1}",1,NULL)&&state.fill_count==0&&zeroed(&state.fills[0],sizeof state.fills[0]),"operation-fill-delete-zero");
 REQUIRE(!json_record("{\"op\":\"delete-panel-fill\",\"id\":1}",1,NULL),"operation-fill-delete-missing");
 REQUIRE(!json_record("{\"op\":\"delete-finish-surface\",\"id\":2,\"hidden\":1}",1,NULL)&&state.count==1,"operation-strict-keys");
 return 0;
}

static int layout(void)
{
 PanelFill p;WoodFinishLayout d={0};REQUIRE(seed(&p),"layout-seed");
 region.hole_count=1;rectangle(&region.holes[0],60,60,80,80);
 state.items[0].obstacle_count=5;for(unsigned i=0;i<5;++i)state.items[0].obstacles[i]=(FinishObstacleRef){0,i+1};
 box(1,20,20,-1,40,40,4);box(2,10,10,9,20,20,12);box(3,10,10,-2,20,20,0);box(4,100,10,0,110,20,9);box(5,65,65,0,75,75,9);
 REQUIRE(wood_pf_values(&context,&p,&d),"layout-obstacle-values");
 REQUIRE(d.cuts[0]&&!d.cuts[1]&&!d.cuts[2]&&!d.cuts[3]&&!d.cuts[4],"layer-open-depth-and-positive-area");
 GeoRect2 cuts[64];REQUIRE(wood_pf_selected_cuts(&d,cuts)==1&&cuts[0].min_u==20&&cuts[0].max_u==40,"layout-selected-source-order");
 REQUIRE(wood_pf_build(&context,&p,&d),"layout-real-w-and-k-build");
 REQUIRE(d.layout.count==1&&d.layout.whole==0&&d.layout.fragments==1&&d.layout.vertices==12&&d.layout.tiles[0].area==9200&&d.layout.tiles[0].count==1&&d.layout.tiles[0].fragments[0].count==3,"layout-exact-holes-and-cut-area");
 REQUIRE(d.layout.tiles[0].fragments[0].loops[0].hole==false&&d.layout.tiles[0].fragments[0].loops[1].hole&&d.layout.tiles[0].fragments[0].loops[2].hole,"layout-canonical-loop-kinds");
 wood_pf_free(&d);REQUIRE(zeroed(&d,sizeof d),"layout-release-zero");
 box(1,20,20,9,40,40,12);REQUIRE(wood_pf_build(&context,&p,&d)&&d.layout.tiles[0].area==9600,"layout-live-source-rebuild");wood_pf_free(&d);
 state.items[0].obstacle_count=0;region.hole_count=0;rectangle(&region.outline,0,0,200000,100);
 REQUIRE(!wood_pf_build(&context,&p,&d)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&strstr(error,"full layout enumeration limit")&&zeroed(&d,sizeof d),"layout-full-enumeration-refusal");
 rectangle(&region.outline,0,0,100,100);state.items[0].frame.origin.x=GEO_COORD_LIMIT-50;
 REQUIRE(!wood_pf_build(&context,&p,&d)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&strstr(error,"returned panel-fill vertex outside D1")&&zeroed(&d,sizeof d),"layout-world-vertex-refusal");
 REQUIRE(!wood_pf_clip_status(&context,GEO_CLIP_VERTEX_LIMIT)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&strstr(error,"32768"),"clip-capacity-diagnostic");
 REQUIRE(!wood_pf_clip_status(&context,GEO_CLIP_OPEN_CONTOUR)&&diagnostic==FS_DIAGNOSTIC_INVALID&&!strcmp(error,"R42: open contour after clipping"),"clip-topology-diagnostic");
 return 0;
}

static int capacity(void)
{
 for(unsigned i=1;i<=FS_MAX;++i)REQUIRE(put_finish(i,"full"),"finish-exact-capacity");
 REQUIRE(state.count==FS_MAX&&put_finish(8,"replacement")&&state.count==FS_MAX,"finish-replace-at-capacity");
 REQUIRE(!put_finish(99,"overflow")&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&state.count==FS_MAX&&!wood_fs_find(&context,99),"finish-capacity-refusal-atomic");
 char message[512];REQUIRE(wood_fs_rebuild(&context,message,sizeof message),"finish-rebuild-full");
 state.items[1].id=state.items[0].id;REQUIRE(!wood_fs_rebuild(&context,message,sizeof message)&&strstr(message,"duplicate finish surface id 1"),"finish-rebuild-duplicate");state.items[1].id=2;
 REQUIRE(wood_fs_delete(&context,1)&&state.items[0].id==2&&zeroed(&state.items[FS_MAX-1],sizeof state.items[0]),"finish-full-compaction-tail");
 const char *scene=NULL;FinishSurface f=finish(20);f.obstacle_count=2;f.obstacles[0]=(FinishObstacleRef){1,2};f.obstacles[1]=(FinishObstacleRef){0,2};
 REQUIRE(wood_fs_load(&context,&f,&scene)&&scene==NULL&&state.items[FS_MAX-1].obstacles[0].kind==FS_OBSTACLE_COLUMN,"finish-load-canonical");
 REQUIRE(!wood_fs_load(&context,&f,&scene)&&!strcmp(scene,"I56: duplicate finish-surface record")&&state.count==FS_MAX,"finish-load-duplicate");
 PanelFill p;REQUIRE(json_record(fill_json,2,&p),"fill-capacity-seed");
 for(unsigned i=1;i<=FS_MAX;++i){p.id=i;REQUIRE(wood_pf_load(&context,i,&p),"fill-exact-capacity");}
 p.id=99;REQUIRE(!wood_pf_load(&context,99,&p)&&diagnostic==FS_DIAGNOSTIC_CAPACITY&&state.fill_count==FS_MAX,"fill-load-capacity");
 p.id=1;REQUIRE(!wood_pf_load(&context,1,&p)&&strstr(error,"mismatch or duplicate"),"fill-load-duplicate-before-capacity");
 REQUIRE(!wood_pf_load(&context,2,&p)&&state.fill_count==FS_MAX,"fill-load-id-mismatch");
 return 0;
}
int main(int argc,char **argv)
{
 if(argc!=2)return 2;atexit(free_versions);reset();
 if(!strcmp(argv[1],"names"))return names();if(!strcmp(argv[1],"obstacles"))return obstacles();
 if(!strcmp(argv[1],"relations"))return relations();if(!strcmp(argv[1],"materials"))return materials();
 if(!strcmp(argv[1],"sources"))return sources();if(!strcmp(argv[1],"operations"))return operations();
 if(!strcmp(argv[1],"layout"))return layout();if(!strcmp(argv[1],"capacity"))return capacity();return 2;
}
