/* Independent W client: host facts are fixed data, not a copied generator. */
#include "assembly.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static AssemblyState state,saved;
static EngineeringState engineering;
static AsmDiagnostic diagnostic;
static GeoParameterRef dimension_error;
static char error[256];
static WoodAssemblyContext context;
typedef struct {uint32_t id;WoodAssemblyMember fact;WoodAssemblyDefinition definition;GeoRect2 rect;bool anchor_ok;} Item;
static Item items[64];static size_t count;
static uint32_t writes[128];static size_t write_count;
static int index_of(uint32_t id){for(size_t i=0;i<count;++i)if(items[i].id==id)return (int)i;return -1;}
static bool parse(void *u,GeoJson *j,const char *text){(void)u;return geo_json_parse(j,text);}
static bool surface(void *u,uint32_t id){(void)u;return id==1;}
static bool guide(void *u,uint32_t id,WoodAssemblyGuide *out)
{(void)u;if(id<1||id>3)return false;*out=(WoodAssemblyGuide){1,id==3?ASM_DIR_U:ASM_DIR_V};return true;}
static bool member(void *u,uint32_t id,WoodAssemblyMember *out)
{(void)u;int i=index_of(id);if(i<0)return false;if(out)*out=items[i].fact;return true;}
static bool footprint(void *u,uint32_t surface_id,uint32_t id,GeoRect2 *out)
{(void)u;int i=index_of(id);if(surface_id!=1||i<0)return false;*out=items[i].rect;return true;}
static size_t member_count(void *u){(void)u;return count;}
static void allocate(void *u,uint32_t id)
{(void)u;items[count].id=id;items[count].anchor_ok=true;++count;}
static bool remove_member(void *u,uint32_t id)
{(void)u;int i=index_of(id);if(i<0)return false;memmove(&items[i],&items[i+1],(count-i-1)*sizeof *items);memset(&items[--count],0,sizeof *items);return true;}
static void write_member(void *u,const WoodMember *value,const WoodAssemblyDefinition *d)
{
    (void)u;int i=index_of(value->id);items[i].fact=(WoodAssemblyMember){d->surface_id,value->role,value->size_a,value->size_b,value->placed};items[i].definition=*d;writes[write_count++]=value->id;
    /* Rectangles are independent declared facts for the contact predicate. */
    items[i].rect=d->guide_id==1?(GeoRect2){487,20,514,2980}:d->guide_id==2?(GeoRect2){2487,20,2514,2980}:(GeoRect2){514,1480,2487,1520};
}
static bool anchor_matches(void *u,uint32_t id,const WoodAssemblyDefinition *d)
{(void)u;(void)d;int i=index_of(id);return i>=0&&items[i].anchor_ok;}
static bool content(void *u,AsmInstance *a,GeoJson *j,int token)
{
    (void)u;char value[ASM_RECORD_MAX],text[ASM_RECORD_MAX];if(!geo_json_canonical(j,token,value,sizeof value))return false;
    int n=snprintf(text,sizeof text,"{\"source\":%s,\"mapping\":[{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u}]}",value,a->member[0],a->timber[0],a->member[1],a->timber[1],a->member[2],a->timber[2]);
    if(n<0||(size_t)n>=sizeof text)return false;GeoJson q;bool ok=geo_json_parse(&q,text)&&geo_json_canonical(&q,0,a->content,sizeof a->content);geo_json_free(&q);return ok;
}
static void drop(void *u,bool rule,uint32_t id){(void)u;(void)rule;(void)id;}
static bool other(void *u,GeoJson *j,int t){(void)u;(void)j;(void)t;return false;}
static bool named(void *u,const char *name,GeoCoord *out)
{(void)u;if(strcmp(name,"known"))return false;*out=42;return true;}
static bool parameter(void *u,GeoParameterRef ref,GeoCoord *out,char *message,size_t cap)
{(void)u;if(ref.parameter_id==10&&ref.field_id==5){*out=40;return true;}dimension_error=ref;snprintf(message,cap,"I38 DIMENSION: parameter %u field %u",ref.parameter_id,ref.field_id);return false;}
static void init(void)
{
    memset(&context,0,sizeof context);context.state=&state;context.diagnostic=&diagnostic;context.parameter_dimension_error=&dimension_error;
    context.engineering.state=&engineering;context.engineering.error=error;context.engineering.error_capacity=sizeof error;context.engineering.named_value=named;context.engineering.parameter=parameter;
    context.json_parse=parse;context.drop_position=drop;context.other_operation=other;context.surface=surface;context.guide=guide;context.member=member;context.footprint=footprint;context.member_count=member_count;context.member_capacity=64;context.allocate_member=allocate;context.remove_member=remove_member;context.write_member=write_member;context.anchor_matches=anchor_matches;context.instance_content=content;
    items[0]=(Item){90,{1,WOOD_MEMBER_ROLE_BOUNDARY,20,20,true}};items[1]=(Item){91,{1,WOOD_MEMBER_ROLE_BOUNDARY,20,20,true}};count=2;
}
static int64_t number(GeoJson *j,int t,const char *key,int64_t fallback)
{int64_t value;return geo_json_integer(j,geo_json_member(j,t,key),&value)?value:fallback;}
static bool action(GeoJson *j,int t)
{
    char kind[32];if(!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind))return false;int value=geo_json_member(j,t,"value");
    if(!strcmp(kind,"publish")){char expected[65];const char *hash=geo_json_string(j,geo_json_member(j,t,"expected"),expected,sizeof expected)?expected:NULL;return wood_assembly_publish(&context,j,value,hash);}
    if(!strcmp(kind,"bind"))return wood_assembly_put_binding(&context,j,value);
    if(!strcmp(kind,"operation"))return wood_assembly_operation(&context,j,value);
    if(!strcmp(kind,"generation"))return wood_assembly_generation_operation(&context,j,value);
    if(!strcmp(kind,"rebuild")){char output[256]={0};bool ok=wood_assembly_rebuild(&context,output,sizeof output);if(!ok)snprintf(error,sizeof error,"%s",output);return ok;}
    if(!strcmp(kind,"prepare"))return wood_assembly_generation_prepare(&context);
    if(!strcmp(kind,"check"))return wood_assembly_generation_check(&context);
    if(!strcmp(kind,"integrity"))return wood_assembly_generation_integrity(&context);
    if(!strcmp(kind,"load"))return wood_assembly_instance_load(&context,j,value);
    if(!strcmp(kind,"save")){saved=state;return true;}
    if(!strcmp(kind,"immutable")){WoodAssemblyContext before=context;before.state=&saved;return wood_assembly_versions_immutable(&before,&context);}
    if(!strcmp(kind,"owner-count")){state.owner_count=(size_t)number(j,t,"count",0);return true;}
    if(!strcmp(kind,"duplicate-owner")){state.owners[1]=state.owners[0];return true;}
    if(!strcmp(kind,"clear-instances")){state.instance_count=0;memset(state.instances,0,sizeof state.instances);return true;}
    if(!strcmp(kind,"require-generation")){state.generation_required=number(j,t,"required",0)!=0;return true;}
    if(!strcmp(kind,"loading")){state.loading=number(j,t,"loading",0)!=0;return true;}
    if(!strcmp(kind,"full-catalog")){state.rule_count=ASM_RULE_MAX;return true;}
    if(!strcmp(kind,"member-fact")){
        int i=index_of((uint32_t)number(j,t,"id",0));if(i<0)return false;Item *p=&items[i];
        p->fact.role=(WoodMemberRole)number(j,t,"role",p->fact.role);p->fact.surface_id=(uint32_t)number(j,t,"surface",p->fact.surface_id);p->fact.width=number(j,t,"width",p->fact.width);p->fact.placed=number(j,t,"placed",p->fact.placed)!=0;p->anchor_ok=number(j,t,"anchor",p->anchor_ok)!=0;
        p->rect.min_u=number(j,t,"min_u",p->rect.min_u);p->rect.max_u=number(j,t,"max_u",p->rect.max_u);p->rect.min_v=number(j,t,"min_v",p->rect.min_v);p->rect.max_v=number(j,t,"max_v",p->rect.max_v);return true;
    }
    return false;
}
static void result(bool ok)
{
    char quoted[1024];geo_json_quote(error,quoted,sizeof quoted);printf("{\"ok\":%s,\"error\":%s,\"diagnostic\":[%d,%u,%u,%u],\"ruleCount\":%zu,\"bindingCount\":%zu,\"instanceCount\":%zu,\"ownerCount\":%zu,\"memberCount\":%zu,\"required\":%s,\"rules\":[",ok?"true":"false",quoted,diagnostic.kind,diagnostic.id,diagnostic.field_id,diagnostic.version,state.rule_count,state.binding_count,state.instance_count,state.owner_count,count,state.generation_required?"true":"false");
    bool comma=false;for(size_t i=0;i<state.rule_count;++i)if(state.rules[i].content[0]){printf("%s{\"value\":%s,\"hash\":\"%s\"}",comma?",":"",state.rules[i].content,state.rules[i].fingerprint);comma=true;}
    printf("],\"bindings\":[");for(size_t i=0;i<state.binding_count;++i)printf("%s{\"value\":%s,\"complete\":%s}",i?",":"",state.bindings[i].content,state.bindings[i].complete?"true":"false");
    printf("],\"instances\":[");for(size_t i=0;i<state.instance_count;++i)printf("%s%s",i?",":"",state.instances[i].content[0]?state.instances[i].content:"null");
    printf("],\"writes\":[");for(size_t i=0;i<write_count;++i)printf("%s%u",i?",":"",writes[i]);
    printf("],\"members\":[");for(size_t i=0;i<count;++i){const Item *p=&items[i];printf("%s{\"id\":%u,\"role\":%d,\"width\":%lld,\"depth\":%lld,\"surface\":%u,\"guide\":%u,\"between\":[%u,%u],\"placed\":%s}",i?",":"",p->id,p->fact.role,(long long)p->fact.width,(long long)p->fact.depth,p->fact.surface_id,p->definition.guide_id,p->definition.between[0],p->definition.between[1],p->fact.placed?"true":"false");}puts("]}");
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;FILE *f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long length=ftell(f);rewind(f);char *text=malloc((size_t)length+1);if(!text){fclose(f);return 2;}if(fread(text,1,(size_t)length,f)!=(size_t)length){free(text);fclose(f);return 2;}fclose(f);text[length]=0;
    GeoJson j;if(!geo_json_parse(&j,text)||!geo_json_is_array(&j,0)){geo_json_free(&j);free(text);return 2;}init();for(int i=0;i<geo_json_size(&j,0);++i){error[0]=0;diagnostic=(AsmDiagnostic){0};result(action(&j,geo_json_at(&j,0,i)));}geo_json_free(&j);free(text);return 0;
}
