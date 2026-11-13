/* Public W client. Boundary, obstacle boxes and parameter values are independent
 * data. Actual W parsing/reconstruction and public K clipping produce results. */
#include "derived_placement.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FinishSurfaceState state;
static EngineeringState engineering;
static GeoVersionStore *versions;
static void free_versions(void){geo_versions_destroy(versions);versions=NULL;}
static WoodDerivedContext context;
static FsDiagnosticKind diagnostic;
static char error[256],parameter_error[256],scene_message[256],resolved_key[512];
static WoodBoundaryRegion boundary;
static WoodDerivedValue placements[FS_MAX];
static size_t placement_count,forced_count;
static unsigned drops,writes;
static int resolved_hole,resolved_edge;
typedef struct {uint32_t id,kind;GeoCoord lo[3],hi[3];} Box;
static Box boxes[FS_OBSTACLE_MAX];static size_t box_count;

static int index_of(uint32_t id)
{for(size_t i=0;i<placement_count;++i)if(placements[i].id==id)return (int)i;return -1;}
static bool read_value(void *u,uint32_t id,WoodDerivedValue *out)
{(void)u;int i=index_of(id);if(i<0)return false;*out=placements[i];return true;}
static bool write_value(void *u,const WoodDerivedValue *p)
{(void)u;int i=index_of(p->id);if(i<0){if(placement_count==FS_MAX)return false;i=(int)placement_count++;}placements[i]=*p;++writes;return true;}
static bool remove_value(void *u,uint32_t id)
{(void)u;int i=index_of(id);if(i<0)return false;memmove(placements+i,placements+i+1,(placement_count-i-1)*sizeof *placements);memset(&placements[--placement_count],0,sizeof *placements);return true;}
static size_t count_value(void *u){(void)u;return forced_count?forced_count:placement_count;}
static void drop_position(void *u,uint32_t id){(void)u;(void)id;++drops;}
static bool boundary_value(void *u,uint32_t id,WoodBoundaryRegion *out)
{(void)u;if(id!=8)return false;*out=boundary;return true;}
static bool obstacle_value(void *u,const FinishObstacleRef *r,GeoCoord lo[3],GeoCoord hi[3])
{(void)u;for(size_t i=0;i<box_count;++i)if(boxes[i].id==r->id&&boxes[i].kind==r->kind){memcpy(lo,boxes[i].lo,sizeof boxes[i].lo);memcpy(hi,boxes[i].hi,sizeof boxes[i].hi);return true;}return false;}
static bool parameter_value(void *u,GeoParameterRef r,GeoQuantity *out)
{(void)u;if(r.parameter_id!=90||r.field_id!=3)return false;*out=(GeoQuantity){8,1,1};return true;}
static bool parameter_coord(void *u,GeoParameterRef r,GeoCoord *out)
{(void)u;if(r.parameter_id!=90||r.field_id!=2)return false;*out=31;return true;}
static bool engineering_parameter(void *u,GeoParameterRef r,GeoCoord *out,char *message,size_t cap)
{if(parameter_coord(u,r,out))return true;snprintf(message,cap,"I38 MISSING: parameter %u field %u",r.parameter_id,r.field_id);return false;}
static bool named(void *u,const char *name,GeoCoord *out)
{(void)u;if(strcmp(name,"depth"))return false;*out=30;return true;}
static bool init(void)
{
    if(geo_versions_create(&versions)!=GEO_VERSION_OK)return false;atexit(free_versions);
    context.finish.state=&state;context.finish.engineering.state=&engineering;context.finish.engineering.error=error;context.finish.engineering.error_capacity=sizeof error;
    context.finish.engineering.versions=versions;
    context.finish.engineering.parameter=engineering_parameter;context.finish.engineering.named_value=named;
    context.finish.error=error;context.finish.error_capacity=sizeof error;context.finish.diagnostic=&diagnostic;
    context.finish.boundary=boundary_value;context.finish.obstacle_box=obstacle_value;context.finish.parameter_coord=parameter_coord;context.finish.parameter_value=parameter_value;strcpy(parameter_error,"parameter fact unavailable");context.finish.parameter_error=parameter_error;context.finish.parameter_error_capacity=sizeof parameter_error;
    context.placement_read=read_value;context.placement_write=write_value;context.placement_remove=remove_value;context.placement_count=count_value;context.placement_capacity=16;context.remove_canvas_position=drop_position;
    boundary.id=8;boundary.kind=WOOD_BOUNDARY_ROOM_PLAN;boundary.outline.count=4;
    boundary.outline.v[0]=(GeoPoint2){0,0};boundary.outline.v[1]=(GeoPoint2){100,0};boundary.outline.v[2]=(GeoPoint2){100,100};boundary.outline.v[3]=(GeoPoint2){0,100};
    for(size_t i=0;i<4;++i)boundary.outline.fixity[i]=WOOD_EDGE_FIXED;
    state.count=1;state.items[0].id=1;state.items[0].boundary_id=8;state.items[0].side=1;strcpy(state.items[0].name,"finish");
    state.items[0].frame=(GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};
    GeoJson j;bool ok=geo_json_parse(&j,"{\"id\":\"board\",\"version\":1,\"kind\":\"panel\",\"name\":\"board\",\"width\":100,\"length\":100,\"thickness\":\"9.000\"}")&&wood_eng_publish_material(&context.finish.engineering,&j,0,NULL);geo_json_free(&j);if(!ok)return false;
    ok=geo_json_parse(&j,"{\"id\":\"timber\",\"version\":1,\"kind\":\"timber\",\"name\":\"timber\",\"A\":27,\"B\":32}")&&wood_eng_publish_material(&context.finish.engineering,&j,0,NULL);geo_json_free(&j);if(!ok)return false;
    ok=geo_json_parse(&j,"{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":0,\"pattern\":\"straight\",\"threshold\":{\"parameterId\":90,\"fieldId\":3}}")&&wood_pf_parse(&context.finish,&j,0,&state.fills[0]);geo_json_free(&j);if(ok)state.fill_count=1;return ok;
}
static int64_t number(GeoJson *j,int t,const char *key,int64_t fallback)
{int64_t n;return geo_json_integer(j,geo_json_member(j,t,key),&n)?n:fallback;}
static bool coords(GeoJson *j,int t,GeoCoord *out,int count)
{if(!geo_json_is_array(j,t)||geo_json_size(j,t)!=count)return false;for(int i=0;i<count;++i)if(!geo_json_integer(j,geo_json_at(j,t,i),out+i))return false;return true;}
static bool action(GeoJson *j,int t)
{
    char kind[32];if(!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind))return false;
    int value=geo_json_member(j,t,"value");uint32_t id=(uint32_t)number(j,t,"id",10);
    if(!strcmp(kind,"operation"))return wood_dp_operation(&context,j,value,number(j,t,"remove",0)!=0);
    if(!strcmp(kind,"rebuild"))return wood_dp_rebuild(&context);
    if(!strcmp(kind,"parse")){DerivedPlacement p;return wood_dp_parse(&context,j,value,&p);}
    if(!strcmp(kind,"load")){DerivedPlacement p;const char *message=NULL;bool ok=wood_dp_parse(&context,j,value,&p)&&wood_dp_load(&context,id,&p,&message);if(message)snprintf(scene_message,sizeof scene_message,"%s",message);return ok;}
    if(!strcmp(kind,"boundary")){
        int points=geo_json_member(j,t,"points"),fix=geo_json_member(j,t,"fixity");int n=geo_json_size(j,points);if(n<4||n>GEO_LOOP_MAX_VERTICES)return false;
        boundary.outline.count=(size_t)n;for(int i=0;i<n;++i){GeoCoord xy[2];if(!coords(j,geo_json_at(j,points,i),xy,2))return false;boundary.outline.v[i]=(GeoPoint2){xy[0],xy[1]};int64_t v;boundary.outline.fixity[i]=geo_json_integer(j,geo_json_at(j,fix,i),&v)?(WoodEdgeFixity)v:WOOD_EDGE_FIXED;}return true;
    }
    if(!strcmp(kind,"obstacle")){
        size_t i=0;while(i<box_count&&boxes[i].id!=id)++i;if(i==box_count){if(box_count==FS_OBSTACLE_MAX)return false;++box_count;}
        boxes[i].id=id;boxes[i].kind=(uint32_t)number(j,t,"type",FS_OBSTACLE_BEAM);
        if(!coords(j,geo_json_member(j,t,"lo"),boxes[i].lo,3)||!coords(j,geo_json_member(j,t,"hi"),boxes[i].hi,3))return false;
        state.items[0].obstacle_count=(uint32_t)box_count;for(size_t k=0;k<box_count;++k)state.items[0].obstacles[k]=(FinishObstacleRef){boxes[k].kind,boxes[k].id};return wood_fs_obstacles_normalize(&context.finish,&state.items[0]);
    }
    if(!strcmp(kind,"side")){state.items[0].side=(int32_t)number(j,t,"side",1);return true;}
    if(!strcmp(kind,"vertical")){state.items[0].frame=(GeoFrame){{1000,0,0},{0,1,0},{0,0,1},{1,0,0}};return true;}
    if(!strcmp(kind,"normal")){WoodDerivedValue p={0};p.id=id;return write_value(NULL,&p);}
    if(!strcmp(kind,"capacity")){forced_count=(size_t)number(j,t,"count",16);return true;}
    if(!strcmp(kind,"diagnostic")){diagnostic=(FsDiagnosticKind)number(j,t,"value",FS_DIAGNOSTIC_CAPACITY);return true;}
    if(!strcmp(kind,"duplicate-component")){int at=index_of(id);if(at<0||placements[at].component_count!=1)return false;placements[at].components[1]=placements[at].components[0];placements[at].component_count=2;return true;}
    if(!strcmp(kind,"resolve")){int at=index_of(id);if(at<0||!geo_json_canonical(j,geo_json_member(j,t,"key"),resolved_key,sizeof resolved_key))return false;return wood_dp_edge_resolve(&context,&placements[at],resolved_key,&resolved_hole,&resolved_edge);}
    if(!strcmp(kind,"key")){int at=index_of(id);if(at<0)return false;return wood_dp_edge_key(&context,&placements[at],(size_t)number(j,t,"component",0),(int)number(j,t,"hole",-1),(size_t)number(j,t,"edge",0),resolved_key,(size_t)number(j,t,"capacity",sizeof resolved_key));}
    return false;
}
static void loop_result(const WoodBoundaryLoop *l)
{putchar('[');for(size_t e=0;e<l->count;++e)printf("%s[%lld,%lld]",e?",":"",(long long)l->v[e].u,(long long)l->v[e].v);putchar(']');}
static void result(bool ok)
{
    char quoted[1024],message[1024],key[1024];geo_json_quote(error,quoted,sizeof quoted);geo_json_quote(scene_message,message,sizeof message);geo_json_quote(resolved_key,key,sizeof key);
    printf("{\"ok\":%s,\"error\":%s,\"sceneMessage\":%s,\"diagnostic\":%d,\"hostCount\":%llu,\"placementCount\":%zu,\"writes\":%u,\"drops\":%u,\"resolved\":[%d,%d],\"key\":%s,\"definitions\":[",ok?"true":"false",quoted,message,diagnostic,(unsigned long long)state.host_count,placement_count,writes,drops,resolved_hole,resolved_edge,key);
    for(uint64_t i=0;i<state.host_count;++i)printf("%s%s",i?",":"",state.hosts[i].definition[0]?state.hosts[i].definition:"null");printf("],\"placements\":[");
    for(size_t i=0;i<placement_count;++i){const WoodDerivedValue *p=&placements[i];printf("%s{\"id\":%u,\"fill\":%u,\"h\":%lld,\"origin\":[%lld,%lld,%lld],\"V\":[%lld,%lld,%lld],\"N\":[%lld,%lld,%lld],\"components\":[",i?",":"",p->id,p->derived_fill_id,(long long)p->derived_h,(long long)p->frame.origin.x,(long long)p->frame.origin.y,(long long)p->frame.origin.z,(long long)p->frame.axis_v.x,(long long)p->frame.axis_v.y,(long long)p->frame.axis_v.z,(long long)p->frame.normal.x,(long long)p->frame.normal.y,(long long)p->frame.normal.z);
        for(size_t c=0;c<p->component_count;++c){const WoodBoundaryRegion *b=&p->components[c];printf("%s{\"outline\":",c?",":"");loop_result(&b->outline);printf(",\"holes\":[");for(size_t h=0;h<b->hole_count;++h){if(h)putchar(',');loop_result(&b->holes[h]);}printf("],\"fixity\":[");for(size_t e=0;e<b->outline.count;++e)printf("%s%d",e?",":"",b->outline.fixity[e]);printf("]}");}printf("]}");}puts("]}");
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;FILE *f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long length=ftell(f);rewind(f);char *text=malloc((size_t)length+1);if(!text){fclose(f);return 2;}if(fread(text,1,(size_t)length,f)!=(size_t)length){free(text);fclose(f);return 2;}fclose(f);text[length]=0;
    GeoJson j;if(!geo_json_parse(&j,text)||!geo_json_is_array(&j,0)||!init()){fprintf(stderr,"initialization: %s\n",error);geo_json_free(&j);free(text);return 2;}
    for(int i=0;i<geo_json_size(&j,0);++i){error[0]=scene_message[0]=resolved_key[0]=0;resolved_hole=resolved_edge=-99;result(action(&j,geo_json_at(&j,0,i)));}geo_json_free(&j);free(text);return 0;
}
