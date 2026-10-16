#include "section_profile_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint32_t id;bool loaded,derived;
    GeoFrame frame;WoodBoundaryRegion region;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView view;
} WoodSectionHostSource;
struct WoodSectionProfileSources {
    GeoEvalContext *graph;GeoProviderToken token;
    WoodSectionProfileContext context;
    WoodSectionProfileEvaluation hooks;
    GeoPoint2 member_points[SP_MEMBER_MAX][4];
    GeoRegionView member_regions[SP_MEMBER_MAX],run_regions[SP_RUN_MAX];
    char member_errors[SP_MEMBER_MAX][256],run_errors[SP_RUN_MAX][256];
    WoodSectionHostSource **hosts;size_t host_count;
};
GeoSourceRef wood_sp_source_ref(GeoProviderToken token,WoodSectionProfileSourceKind kind,uint32_t id,WoodSectionProfileSourceKey *key)
{
    key->bytes[0]=(unsigned char)kind;
    for(int i=0;i<4;++i)key->bytes[i+1]=(unsigned char)(id>>(24-8*i));
    return (GeoSourceRef){token,key->bytes,sizeof key->bytes};
}
bool wood_sp_source_decode(const GeoSourceRef *ref,WoodSectionProfileSourceKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;
    const unsigned char *bytes=ref->key;
    if(bytes[0]<WOOD_SP_SOURCE_PROFILE_DEFINITION||bytes[0]>WOOD_SP_SOURCE_HOST_REGION)return false;
    uint32_t value=0;for(int i=1;i<5;++i)value=(value<<8)|bytes[i];
    *kind=(WoodSectionProfileSourceKind)bytes[0];*id=value;return true;
}
static int wood_sp_source_member(const WoodSectionProfileSources *s,uint32_t id)
{for(size_t i=0;i<s->context.state->member_count;++i)if(s->context.state->members[i].id==id)return (int)i;return -1;}
static int wood_sp_source_run(const WoodSectionProfileSources *s,uint32_t id)
{for(size_t i=0;i<s->context.state->run_count;++i)if(s->context.state->runs[i].id==id)return (int)i;return -1;}
static WoodSectionHostSource *wood_sp_source_host(WoodSectionProfileSources *s,uint32_t id)
{
    for(size_t i=0;i<s->host_count;++i)if(s->hosts[i]->id==id)return s->hosts[i];
    if(s->host_count==SIZE_MAX/sizeof *s->hosts)return NULL;
    WoodSectionHostSource *host=calloc(1,sizeof *host);if(!host)return NULL;
    WoodSectionHostSource **next=realloc(s->hosts,(s->host_count+1)*sizeof *next);
    if(!next){free(host);return NULL;}
    s->hosts=next;host->id=id;next[s->host_count++]=host;return host;
}
static GeoSourceStatus wood_sp_source_get(WoodSectionProfileSources *s,WoodSectionProfileSourceKind kind,uint32_t id,GeoDependencyKind relation,GeoSourceValue *out)
{WoodSectionProfileSourceKey key;return geo_eval_source(s->graph,wood_sp_source_ref(s->token,kind,id,&key),relation,out);}
static GeoSourceStatus wood_sp_source_identity(WoodSectionProfileSources *s,WoodSectionProfileSourceKind kind,uint32_t id,GeoDependencyKind relation)
{
    WoodSectionProfileSourceKey key;GeoSourceRef ref=wood_sp_source_ref(s->token,kind,id,&key);
    GeoSourceStatus status=geo_eval_depend(s->graph,ref,relation);if(status!=GEO_SOURCE_OK)return status;
    GeoSourceDescriptor descriptor;return geo_eval_describe(s->graph,ref,&descriptor);
}
static void wood_sp_source_first(char *first,size_t capacity,const char *message)
{if(!first[0]&&message[0])snprintf(first,capacity,"%s",message);}
static void wood_sp_source_graph_error(WoodSectionProfileSources *s,char *first,size_t capacity)
{
    const char *message="I51 CAPACITY: section profile source evaluation unavailable";
    snprintf(s->context.error,s->context.error_capacity,"%s",message);wood_sp_source_first(first,capacity,message);
}
static bool wood_sp_source_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodSectionProfileSources *s=user;WoodSectionProfileSourceKind kind;uint32_t id;
    if(ref->provider!=s->token||!wood_sp_source_decode(ref,&kind,&id))return false;
    GeoSourceDescriptor d={.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION){if(!wood_sp_profile(&s->context,id))return false;}
    else if(kind>=WOOD_SP_SOURCE_MEMBER_DEFINITION&&kind<=WOOD_SP_SOURCE_MEMBER_REGION){
        if(wood_sp_source_member(s,id)<0)return false;
        if(kind==WOOD_SP_SOURCE_MEMBER_A||kind==WOOD_SP_SOURCE_MEMBER_B){d.kind=GEO_SOURCE_QUANTITY;d.unit=GEO_UNIT_LENGTH;}
        else if(kind==WOOD_SP_SOURCE_MEMBER_REGION)d.kind=GEO_SOURCE_REGION_SET;
    }else if(kind>=WOOD_SP_SOURCE_RUN_DEFINITION&&kind<=WOOD_SP_SOURCE_RUN_REGION){
        if(wood_sp_source_run(s,id)<0)return false;
        if(kind==WOOD_SP_SOURCE_RUN_LENGTH){d.kind=GEO_SOURCE_QUANTITY;d.unit=GEO_UNIT_LENGTH;}
        else if(kind==WOOD_SP_SOURCE_RUN_FRAME)d.kind=GEO_SOURCE_FRAME;
        else if(kind==WOOD_SP_SOURCE_RUN_REGION)d.kind=GEO_SOURCE_REGION_SET;
    }else d.kind=kind==WOOD_SP_SOURCE_HOST_FRAME?GEO_SOURCE_FRAME:GEO_SOURCE_REGION_SET;
    if(d.kind!=GEO_SOURCE_DEFINITION)d.unit=GEO_UNIT_LENGTH;
    *out=d;return true;
}
static bool wood_sp_source_definition(WoodSectionProfileSources *s,WoodSectionProfileSourceKind kind,uint32_t id,GeoSourceValue *out)
{
    const char *content=NULL,*schema=NULL;
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION){SectionProfile *p=wood_sp_profile(&s->context,id);if(!p)return false;content=p->content;schema="wood.section-profile.definition/1";}
    else if(kind==WOOD_SP_SOURCE_MEMBER_DEFINITION){int i=wood_sp_source_member(s,id);if(i<0)return false;content=s->context.state->members[i].content;schema="wood.section-profile.member/1";}
    else if(kind==WOOD_SP_SOURCE_RUN_DEFINITION){int i=wood_sp_source_run(s,id);if(i<0)return false;content=s->context.state->runs[i].content;schema="wood.section-profile.run/1";}
    if(!content)return false;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,content,strlen(content)};return true;
}
static bool wood_sp_source_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodSectionProfileSources *s=user;WoodSectionProfileSourceKind kind;uint32_t id;
    if(graph!=s->graph||!wood_sp_source_decode(ref,&kind,&id))return false;
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION||kind==WOOD_SP_SOURCE_MEMBER_DEFINITION||kind==WOOD_SP_SOURCE_RUN_DEFINITION)
        return wood_sp_source_definition(s,kind,id,out);
    GeoSourceValue definition;
    if(kind>=WOOD_SP_SOURCE_MEMBER_A&&kind<=WOOD_SP_SOURCE_MEMBER_REGION){
        int index=wood_sp_source_member(s,id);if(index<0)return false;size_t i=(size_t)index;ProfileMember *m=&s->context.state->members[i];
        if(wood_sp_source_get(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK)return false;
        if(kind==WOOD_SP_SOURCE_MEMBER_A||kind==WOOD_SP_SOURCE_MEMBER_B){
            int field=kind==WOOD_SP_SOURCE_MEMBER_B;GeoCoord *value=field?&m->b:&m->a;
            if(!wood_sp_member_dimension_direct(&s->context,i,field,value))return false;
            out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){*value,1,GEO_UNIT_LENGTH};return true;
        }
        s->member_errors[i][0]=0;wood_sp_evaluate_member_direct(&s->context,i,s->member_errors[i],sizeof s->member_errors[i]);
        if(!m->resolved||m->missing_profile||m->outside||m->range_error)return false;
        GeoPoint2 *p=s->member_points[i];p[0]=(GeoPoint2){m->rect.min_u,m->rect.min_v};p[1]=(GeoPoint2){m->rect.max_u,m->rect.min_v};p[2]=(GeoPoint2){m->rect.max_u,m->rect.max_v};p[3]=(GeoPoint2){m->rect.min_u,m->rect.max_v};
        s->member_regions[i]=(GeoRegionView){{p,4},NULL,0};out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&s->member_regions[i],1};return true;
    }
    if(kind>=WOOD_SP_SOURCE_RUN_LENGTH&&kind<=WOOD_SP_SOURCE_RUN_REGION){
        int index=wood_sp_source_run(s,id);if(index<0)return false;size_t i=(size_t)index;ProfileRun *r=&s->context.state->runs[i];
        if(wood_sp_source_get(s,WOOD_SP_SOURCE_RUN_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK)return false;
        if(kind==WOOD_SP_SOURCE_RUN_LENGTH){
            GeoCoord *value=&r->length;if(!wood_sp_run_length_direct(&s->context,i,value))return false;
            out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){*value,1,GEO_UNIT_LENGTH};return true;
        }
        if(kind==WOOD_SP_SOURCE_RUN_FRAME){
            if(!r->placed||!wood_sp_resolve_placement(&s->context,r))return false;
            out->kind=GEO_SOURCE_FRAME;out->as.frame=r->frame;return true;
        }
        s->run_errors[i][0]=0;wood_sp_evaluate_run_direct(&s->context,i,s->run_errors[i],sizeof s->run_errors[i]);
        if(!r->resolved)return false;SectionProfile *p=wood_sp_profile(&s->context,r->profile_id);
        s->run_regions[i]=(GeoRegionView){{p->outline.v,p->outline.count},NULL,0};out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&s->run_regions[i],1};return true;
    }
    WoodSectionHostSource *host=wood_sp_source_host(s,id);if(!host)return false;
    if(kind==WOOD_SP_SOURCE_HOST_FRAME){
        host->loaded=false;host->derived=false;
        if(!s->context.live_host(s->context.user,id,&host->frame,&host->region,&host->derived))return false;
        host->loaded=true;if(host->derived||!geo_frame_is_valid(&host->frame))return false;
        out->kind=GEO_SOURCE_FRAME;out->as.frame=host->frame;return true;
    }
    if(kind==WOOD_SP_SOURCE_HOST_REGION){
        GeoSourceValue frame;if(wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_FRAME,id,GEO_DEPENDENCY_VALUE_REQUIRED,&frame)!=GEO_SOURCE_OK)return false;
        if(!host->loaded||host->derived||host->region.hole_count>GEO_REGION_MAX_HOLES)return false;
        for(size_t i=0;i<host->region.hole_count;++i)host->holes[i]=(GeoLoop2View){host->region.holes[i].v,host->region.holes[i].count};
        host->view=(GeoRegionView){{host->region.outline.v,host->region.outline.count},host->holes,host->region.hole_count};
        if(!geo_region_is_valid(&host->view))return false;
        out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&host->view,1};return true;
    }
    return false;
}
static void wood_sp_source_begin(void *user,WoodSectionProfileContext *w,char *first,size_t capacity)
{
    WoodSectionProfileSources *s=user;
    for(size_t i=0;i<w->state->profile_count;++i)
        if(wood_sp_source_identity(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,w->state->profiles[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)wood_sp_source_graph_error(s,first,capacity);
}
static void wood_sp_source_member_root(void *user,WoodSectionProfileContext *w,size_t i,char *first,size_t capacity)
{
    WoodSectionProfileSources *s=user;GeoSourceValue value;GeoSourceStatus status=wood_sp_source_get(s,WOOD_SP_SOURCE_MEMBER_REGION,w->state->members[i].id,GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    wood_sp_source_first(first,capacity,s->member_errors[i]);
    if(status!=GEO_SOURCE_OK&&!s->member_errors[i][0])wood_sp_source_graph_error(s,first,capacity);
}
static void wood_sp_source_run_root(void *user,WoodSectionProfileContext *w,size_t i,char *first,size_t capacity)
{
    WoodSectionProfileSources *s=user;GeoSourceValue value;GeoSourceStatus status=wood_sp_source_get(s,WOOD_SP_SOURCE_RUN_REGION,w->state->runs[i].id,GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    wood_sp_source_first(first,capacity,s->run_errors[i]);
    if(status!=GEO_SOURCE_OK&&!s->run_errors[i][0])wood_sp_source_graph_error(s,first,capacity);
}
static void wood_sp_source_profile_dependency(void *user,WoodSectionProfileContext *w,uint32_t id)
{WoodSectionProfileSources *s=user;(void)w;GeoSourceValue value;(void)wood_sp_source_get(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
static bool wood_sp_source_member_dimension(void *user,WoodSectionProfileContext *w,size_t i,int field,GeoCoord *out)
{
    WoodSectionProfileSources *s=user;GeoSourceValue value;
    if(wood_sp_source_get(s,field?WOOD_SP_SOURCE_MEMBER_B:WOOD_SP_SOURCE_MEMBER_A,w->state->members[i].id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.quantity.num;return true;
}
static bool wood_sp_source_run_length(void *user,WoodSectionProfileContext *w,size_t i,GeoCoord *out)
{
    WoodSectionProfileSources *s=user;GeoSourceValue value;
    if(wood_sp_source_get(s,WOOD_SP_SOURCE_RUN_LENGTH,w->state->runs[i].id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.quantity.num;return true;
}
static bool wood_sp_source_run_placement(void *user,WoodSectionProfileContext *w,size_t i)
{
    WoodSectionProfileSources *s=user;ProfileRun *r=&w->state->runs[i];
    if(!r->placed){
        if(wood_sp_source_identity(s,WOOD_SP_SOURCE_RUN_FRAME,r->id,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
        return wood_sp_resolve_placement(w,r);
    }
    GeoSourceValue value;return wood_sp_source_get(s,WOOD_SP_SOURCE_RUN_FRAME,r->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK;
}
static bool wood_sp_source_live_host(void *user,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    WoodSectionProfileSources *s=user;GeoSourceValue f,r;
    GeoSourceStatus status=wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_FRAME,id,GEO_DEPENDENCY_VALUE_REQUIRED,&f);
    WoodSectionHostSource *host=wood_sp_source_host(s,id);if(!host)return false;
    if(host->loaded&&host->derived){*derived=true;return true;}
    if(status!=GEO_SOURCE_OK||wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&r)!=GEO_SOURCE_OK)return false;
    *derived=false;*frame=f.as.frame;*region=host->region;return true;
}
WoodSectionProfileSources *wood_sp_sources_create(GeoEvalContext *graph,GeoProviderToken token,const WoodSectionProfileContext *base)
{
    if(!graph||!base||!base->state||!base->resolve_dimension||!base->live_host)return NULL;
    WoodSectionProfileSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->token=token;s->context=*base;
    s->hooks=(WoodSectionProfileEvaluation){s,wood_sp_source_begin,wood_sp_source_member_root,wood_sp_source_run_root,wood_sp_source_profile_dependency,
        wood_sp_source_member_dimension,wood_sp_source_run_length,wood_sp_source_run_placement,wood_sp_source_live_host};
    s->context.evaluation=&s->hooks;
    GeoSourceProvider provider={token,"wood.section-profile","wood-section-profile-sources/1",s,wood_sp_source_describe,wood_sp_source_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
bool wood_sp_sources_bind(WoodSectionProfileSources *s,WoodSectionProfileContext *w)
{
    if(!s||!w||w->state!=s->context.state||w->user!=s->context.user||w->error!=s->context.error||w->error_capacity!=s->context.error_capacity||w->resolve_dimension!=s->context.resolve_dimension||w->live_host!=s->context.live_host)return false;
    w->evaluation=&s->hooks;return true;
}
void wood_sp_sources_destroy(WoodSectionProfileSources *s)
{if(s){for(size_t i=0;i<s->host_count;++i)free(s->hosts[i]);free(s->hosts);free(s);}}
