#include "section_profile_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint32_t id;bool loaded,derived;
    GeoFrame frame;WoodBoundaryRegion region;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView view;
} WoodSectionHostSource;
typedef struct {
    uint32_t first,second;GeoPoint2 points[4];GeoRegionView region;
} WoodSectionPairSource;
struct WoodSectionProfileSources {
    GeoEvalContext *graph;GeoProviderToken token;
    WoodSectionProfileContext context;
    WoodSectionProfileEvaluation hooks;
    SectionProfileState *authored,decoded;
    GeoPoint2 member_points[SP_MEMBER_MAX][4];
    GeoRegionView member_regions[SP_MEMBER_MAX],run_regions[SP_RUN_MAX];
    char member_errors[SP_MEMBER_MAX][256],run_errors[SP_RUN_MAX][256];
    WoodSectionHostSource **hosts;size_t host_count;
    WoodSectionPairSource **pairs;size_t pair_count;
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
GeoSourceRef wood_sp_pair_source_ref(GeoProviderToken token,uint32_t first,uint32_t second,WoodSectionProfilePairKey *key)
{
    key->bytes[0]=WOOD_SP_SOURCE_MEMBER_PAIR_CHECK;
    for(int i=0;i<4;++i){key->bytes[i+1]=(unsigned char)(first>>(24-8*i));key->bytes[i+5]=(unsigned char)(second>>(24-8*i));}
    return (GeoSourceRef){token,key->bytes,sizeof key->bytes};
}
bool wood_sp_pair_source_decode(const GeoSourceRef *ref,uint32_t *first,uint32_t *second)
{
    if(!ref||!ref->key||ref->key_size!=9||!first||!second)return false;
    const unsigned char *bytes=ref->key;if(bytes[0]!=WOOD_SP_SOURCE_MEMBER_PAIR_CHECK)return false;
    uint32_t a=0,b=0;for(int i=0;i<4;++i){a=(a<<8)|bytes[i+1];b=(b<<8)|bytes[i+5];}
    if(a==b)return false;*first=a;*second=b;return true;
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
static void wood_sp_source_member_cache(ProfileMember *to,const ProfileMember *from)
{
    to->a=from->a;to->b=from->b;to->rect=from->rect;to->resolved=from->resolved;
    memcpy(to->source_error,from->source_error,sizeof to->source_error);
    to->missing_profile=from->missing_profile;to->outside=from->outside;to->range_error=from->range_error;
}
static void wood_sp_source_run_cache(ProfileRun *to,const ProfileRun *from)
{
    to->length=from->length;to->resolved=from->resolved;to->length_resolved=from->length_resolved;
    to->placement_resolved=from->placement_resolved;to->missing_profile=from->missing_profile;to->range_error=from->range_error;
    memcpy(to->length_error,from->length_error,sizeof to->length_error);memcpy(to->placement_error,from->placement_error,sizeof to->placement_error);
    if(to->simple&&from->simple)to->frame=from->frame;
}
static const char *wood_sp_source_schema(WoodSectionProfileSourceKind kind)
{
    return kind==WOOD_SP_SOURCE_PROFILE_DEFINITION?"wood.section-profile.definition/1":
        kind==WOOD_SP_SOURCE_MEMBER_DEFINITION?"wood.section-profile.member/1":"wood.section-profile.run/1";
}
static bool wood_sp_source_invalid_definition(WoodSectionProfileSources *s,WoodSectionProfileSourceKind kind,uint32_t id)
{snprintf(s->context.error,s->context.error_capacity,"I51: invalid section profile definition kind %u id %u",(unsigned)kind,id);return false;}
static bool wood_sp_source_load_definition(WoodSectionProfileSources *s,WoodSectionProfileSourceKind kind,uint32_t id)
{
    GeoSourceValue definition;
    if(wood_sp_source_get(s,kind,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)!=GEO_SOURCE_OK){
        snprintf(s->context.error,s->context.error_capacity,"I51: section profile definition kind %u id %u unavailable",(unsigned)kind,id);return false;}
    size_t limit=kind==WOOD_SP_SOURCE_RUN_DEFINITION?SP_RUN_RECORD_MAX:SP_RECORD_MAX;
    if(definition.kind!=GEO_SOURCE_DEFINITION||!definition.as.definition.schema||strcmp(definition.as.definition.schema,wood_sp_source_schema(kind))||
       !definition.as.definition.content||!definition.as.definition.content_size||definition.as.definition.content_size>=limit||
       memchr(definition.as.definition.content,0,definition.as.definition.content_size))return wood_sp_source_invalid_definition(s,kind,id);
    GeoJson json={0};if(!geo_json_parse_n(&json,definition.as.definition.content,definition.as.definition.content_size)){
        geo_json_free(&json);return wood_sp_source_invalid_definition(s,kind,id);}
    bool ok=false;const char *canonical=NULL;
    SectionProfile p;ProfileMember m;ProfileRun r;
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION){ok=wood_sp_parse_profile(&s->context,&json,0,&p);canonical=p.content;if(ok&&p.id!=id)ok=wood_sp_source_invalid_definition(s,kind,id);}
    else if(kind==WOOD_SP_SOURCE_MEMBER_DEFINITION){ok=wood_sp_parse_member(&s->context,&json,0,&m);canonical=m.content;if(ok&&m.id!=id)ok=wood_sp_source_invalid_definition(s,kind,id);}
    else{ok=wood_sp_parse_run(&s->context,&json,0,&r);canonical=r.content;if(ok&&r.id!=id)ok=wood_sp_source_invalid_definition(s,kind,id);}
    if(ok&&(strlen(canonical)!=definition.as.definition.content_size||memcmp(canonical,definition.as.definition.content,definition.as.definition.content_size)))ok=wood_sp_source_invalid_definition(s,kind,id);
    if(ok){
        if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION){SectionProfile *target=wood_sp_profile(&s->context,id);if(!target)ok=false;else *target=p;}
        else if(kind==WOOD_SP_SOURCE_MEMBER_DEFINITION){int i=wood_sp_source_member(s,id);if(i<0)ok=false;else{wood_sp_source_member_cache(&m,&s->decoded.members[i]);s->decoded.members[i]=m;}}
        else{int i=wood_sp_source_run(s,id);if(i<0)ok=false;else{wood_sp_source_run_cache(&r,&s->decoded.runs[i]);s->decoded.runs[i]=r;}}
    }
    geo_json_free(&json);return ok;
}
bool wood_sp_sources_profile_definition(WoodSectionProfileSources *s,uint32_t id,SectionProfile *out)
{
    if(!s||!out||!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,id))return false;
    const SectionProfile *value=wood_sp_profile(&s->context,id);if(!value)return false;*out=*value;return true;
}
bool wood_sp_sources_member_definition(WoodSectionProfileSources *s,uint32_t id,ProfileMember *out)
{
    if(!s||!out||!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id))return false;
    int i=wood_sp_source_member(s,id);if(i<0)return false;*out=s->decoded.members[i];return true;
}
bool wood_sp_sources_run_definition(WoodSectionProfileSources *s,uint32_t id,ProfileRun *out)
{
    if(!s||!out||!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_RUN_DEFINITION,id))return false;
    int i=wood_sp_source_run(s,id);if(i<0)return false;*out=s->decoded.runs[i];return true;
}
static bool wood_sp_source_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodSectionProfileSources *s=user;WoodSectionProfileSourceKind kind;uint32_t id;
    if(ref->provider!=s->token)return false;
    GeoSourceDescriptor d={.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};
    uint32_t second;
    if(wood_sp_pair_source_decode(ref,&id,&second)){
        if(wood_sp_source_member(s,id)<0||wood_sp_source_member(s,second)<0)return false;
        d.kind=GEO_SOURCE_REGION_SET;d.unit=GEO_UNIT_LENGTH;*out=d;return true;
    }
    if(!wood_sp_source_decode(ref,&kind,&id))return false;
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
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION){for(size_t i=0;i<s->authored->profile_count;++i)if(s->authored->profiles[i].id==id)content=s->authored->profiles[i].content;schema="wood.section-profile.definition/1";}
    else if(kind==WOOD_SP_SOURCE_MEMBER_DEFINITION){int i=wood_sp_source_member(s,id);if(i<0)return false;content=s->authored->members[i].content;schema="wood.section-profile.member/1";}
    else if(kind==WOOD_SP_SOURCE_RUN_DEFINITION){int i=wood_sp_source_run(s,id);if(i<0)return false;content=s->authored->runs[i].content;schema="wood.section-profile.run/1";}
    if(!content)return false;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,content,strlen(content)};return true;
}
static bool wood_sp_source_rectangle(const GeoSourceValue *value,GeoRect2 *out)
{
    if(value->kind!=GEO_SOURCE_REGION_SET||value->as.regions.count!=1||!value->as.regions.regions)return false;
    const GeoRegionView *region=&value->as.regions.regions[0];
    if(region->hole_count||region->outline.count!=4||!geo_region_is_valid(region))return false;
    const GeoPoint2 *p=region->outline.v;GeoRect2 r={p[0].u,p[0].v,p[0].u,p[0].v};
    for(size_t i=1;i<4;++i){if(p[i].u<r.min_u)r.min_u=p[i].u;if(p[i].u>r.max_u)r.max_u=p[i].u;if(p[i].v<r.min_v)r.min_v=p[i].v;if(p[i].v>r.max_v)r.max_v=p[i].v;}
    *out=r;return true;
}
static bool wood_sp_source_pair_region(WoodSectionProfileSources *s,uint32_t id,GeoSourceValue *out)
{
    WoodSectionProfileSourceKey key;GeoSourceRef ref=wood_sp_source_ref(s->token,WOOD_SP_SOURCE_MEMBER_REGION,id,&key);
    /* The member phase has already gathered all diagnostics. A failed member
     * must not be re-evaluated once for every pair and repeat leaf callbacks. */
    for(size_t i=0;i<geo_eval_node_count(s->graph);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(s->graph,i,&node)&&node.source.provider==ref.provider&&node.source.key_size==ref.key_size&&!memcmp(node.source.key,ref.key,ref.key_size)&&node.state==GEO_NODE_FAILED){
            (void)geo_eval_depend(s->graph,ref,GEO_DEPENDENCY_VALUE_REQUIRED);return false;}}
    return wood_sp_source_get(s,WOOD_SP_SOURCE_MEMBER_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
}
static bool wood_sp_source_pair_evaluate(WoodSectionProfileSources *s,uint32_t first,uint32_t second,GeoSourceValue *out)
{
    bool a_definition=wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,first);
    bool b_definition=wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,second);
    if(!a_definition||!b_definition)return false;
    GeoSourceValue a,b;bool a_ok=wood_sp_source_pair_region(s,first,&a),b_ok=wood_sp_source_pair_region(s,second,&b);
    if(!a_ok||!b_ok)return false;
    GeoRect2 ar,br;if(!wood_sp_source_rectangle(&a,&ar)||!wood_sp_source_rectangle(&b,&br))return false;
    ProfileMember *am=wood_sp_member(&s->context,first),*bm=wood_sp_member(&s->context,second);
    GeoRect2 r={ar.min_u>br.min_u?ar.min_u:br.min_u,ar.min_v>br.min_v?ar.min_v:br.min_v,
        ar.max_u<br.max_u?ar.max_u:br.max_u,ar.max_v<br.max_v?ar.max_v:br.max_v};
    out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){NULL,0};
    if(am->profile_id!=bm->profile_id||r.min_u>=r.max_u||r.min_v>=r.max_v)return true;
    WoodSectionPairSource *pair=NULL;
    for(size_t i=0;i<s->pair_count;++i)if(s->pairs[i]->first==first&&s->pairs[i]->second==second)pair=s->pairs[i];
    if(!pair){
        if(s->pair_count==SIZE_MAX/sizeof *s->pairs)return false;
        pair=calloc(1,sizeof *pair);if(!pair)return false;
        WoodSectionPairSource **next=realloc(s->pairs,(s->pair_count+1)*sizeof *next);if(!next){free(pair);return false;}
        s->pairs=next;next[s->pair_count++]=pair;pair->first=first;pair->second=second;
    }
    pair->points[0]=(GeoPoint2){r.min_u,r.min_v};pair->points[1]=(GeoPoint2){r.max_u,r.min_v};pair->points[2]=(GeoPoint2){r.max_u,r.max_v};pair->points[3]=(GeoPoint2){r.min_u,r.max_v};
    pair->region=(GeoRegionView){{pair->points,4},NULL,0};out->as.regions=(GeoRegionSetView){&pair->region,1};return true;
}
static bool wood_sp_source_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodSectionProfileSources *s=user;WoodSectionProfileSourceKind kind;uint32_t id;
    if(graph!=s->graph)return false;uint32_t second;
    if(wood_sp_pair_source_decode(ref,&id,&second))return wood_sp_source_pair_evaluate(s,id,second,out);
    if(!wood_sp_source_decode(ref,&kind,&id))return false;
    if(kind==WOOD_SP_SOURCE_PROFILE_DEFINITION||kind==WOOD_SP_SOURCE_MEMBER_DEFINITION||kind==WOOD_SP_SOURCE_RUN_DEFINITION)
        return wood_sp_source_definition(s,kind,id,out);
    if(kind>=WOOD_SP_SOURCE_MEMBER_A&&kind<=WOOD_SP_SOURCE_MEMBER_REGION){
        int index=wood_sp_source_member(s,id);if(index<0)return false;size_t i=(size_t)index;ProfileMember *m=&s->context.state->members[i];
        if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id)){
            if(kind==WOOD_SP_SOURCE_MEMBER_REGION)snprintf(s->member_errors[i],sizeof s->member_errors[i],"%s",s->context.error);return false;}
        if(kind==WOOD_SP_SOURCE_MEMBER_A||kind==WOOD_SP_SOURCE_MEMBER_B){
            int field=kind==WOOD_SP_SOURCE_MEMBER_B;GeoCoord *value=field?&m->b:&m->a;
            bool ok=wood_sp_member_dimension_direct(&s->context,i,field,value);wood_sp_source_member_cache(&s->authored->members[i],m);if(!ok)return false;
            out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){*value,1,GEO_UNIT_LENGTH};return true;
        }
        s->member_errors[i][0]=0;wood_sp_evaluate_member_direct(&s->context,i,s->member_errors[i],sizeof s->member_errors[i]);
        wood_sp_source_member_cache(&s->authored->members[i],m);
        if(!m->resolved||m->missing_profile||m->outside||m->range_error)return false;
        GeoPoint2 *p=s->member_points[i];p[0]=(GeoPoint2){m->rect.min_u,m->rect.min_v};p[1]=(GeoPoint2){m->rect.max_u,m->rect.min_v};p[2]=(GeoPoint2){m->rect.max_u,m->rect.max_v};p[3]=(GeoPoint2){m->rect.min_u,m->rect.max_v};
        s->member_regions[i]=(GeoRegionView){{p,4},NULL,0};out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&s->member_regions[i],1};return true;
    }
    if(kind>=WOOD_SP_SOURCE_RUN_LENGTH&&kind<=WOOD_SP_SOURCE_RUN_REGION){
        int index=wood_sp_source_run(s,id);if(index<0)return false;size_t i=(size_t)index;ProfileRun *r=&s->context.state->runs[i];
        if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_RUN_DEFINITION,id)){
            if(kind==WOOD_SP_SOURCE_RUN_REGION)snprintf(s->run_errors[i],sizeof s->run_errors[i],"%s",s->context.error);return false;}
        if(kind==WOOD_SP_SOURCE_RUN_LENGTH){
            GeoCoord *value=&r->length;bool ok=wood_sp_run_length_direct(&s->context,i,value);wood_sp_source_run_cache(&s->authored->runs[i],r);if(!ok)return false;
            out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){*value,1,GEO_UNIT_LENGTH};return true;
        }
        if(kind==WOOD_SP_SOURCE_RUN_FRAME){
            bool ok=r->placed&&wood_sp_resolve_placement(&s->context,r);wood_sp_source_run_cache(&s->authored->runs[i],r);if(!ok)return false;
            out->kind=GEO_SOURCE_FRAME;out->as.frame=r->frame;return true;
        }
        s->run_errors[i][0]=0;wood_sp_evaluate_run_direct(&s->context,i,s->run_errors[i],sizeof s->run_errors[i]);
        wood_sp_source_run_cache(&s->authored->runs[i],r);
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
static bool wood_sp_source_profile_dependency(void *user,WoodSectionProfileContext *w,uint32_t id,SectionProfile **out)
{WoodSectionProfileSources *s=user;(void)w;if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,id))return false;*out=wood_sp_profile(&s->context,id);return *out!=NULL;}
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
    GeoSourceValue value;
    if(wood_sp_source_get(s,WOOD_SP_SOURCE_RUN_FRAME,r->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK){
        r->placement_resolved=false;if(!r->placement_error[0])snprintf(r->placement_error,sizeof r->placement_error,"I48: run frame unavailable");return false;}
    if(value.kind!=GEO_SOURCE_FRAME||!geo_frame_is_valid(&value.as.frame)){
        snprintf(r->placement_error,sizeof r->placement_error,"I48: invalid returned run frame");r->placement_resolved=false;return false;}
    r->frame=value.as.frame;r->placement_resolved=true;return true;
}
static bool wood_sp_source_region_copy(const GeoSourceValue *value,WoodBoundaryRegion *out)
{
    if(value->kind!=GEO_SOURCE_REGION_SET||value->as.regions.count!=1||!value->as.regions.regions)return false;
    const GeoRegionView *region=&value->as.regions.regions[0];
    if(region->outline.count>GEO_LOOP_MAX_VERTICES||region->hole_count>GEO_REGION_MAX_HOLES||!geo_region_is_valid(region))return false;
    WoodBoundaryRegion copy={0};copy.outline.count=region->outline.count;copy.hole_count=region->hole_count;
    memcpy(copy.outline.v,region->outline.v,copy.outline.count*sizeof *copy.outline.v);
    for(size_t i=0;i<copy.hole_count;++i){if(region->holes[i].count>GEO_LOOP_MAX_VERTICES)return false;copy.holes[i].count=region->holes[i].count;memcpy(copy.holes[i].v,region->holes[i].v,copy.holes[i].count*sizeof *copy.holes[i].v);}
    *out=copy;return true;
}
static bool wood_sp_source_live_host(void *user,uint32_t id,GeoFrame *frame,WoodBoundaryRegion *region,bool *derived)
{
    WoodSectionProfileSources *s=user;GeoSourceValue f,r;
    GeoSourceStatus status=wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_FRAME,id,GEO_DEPENDENCY_VALUE_REQUIRED,&f);
    WoodSectionHostSource *host=wood_sp_source_host(s,id);if(!host)return false;
    if(host->loaded&&host->derived){*derived=true;return true;}
    if(status!=GEO_SOURCE_OK||wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&r)!=GEO_SOURCE_OK)return false;
    if(f.kind!=GEO_SOURCE_FRAME||!geo_frame_is_valid(&f.as.frame)||!wood_sp_source_region_copy(&r,region))return false;
    *derived=false;*frame=f.as.frame;return true;
}
static void wood_sp_source_pair_root(void *user,WoodSectionProfileContext *w,size_t first,size_t second,char *error,size_t capacity)
{
    WoodSectionProfileSources *s=user;uint32_t a=w->state->members[first].id,b=w->state->members[second].id;
    WoodSectionProfilePairKey key;GeoSourceValue value;
    if(geo_eval_source(s->graph,wood_sp_pair_source_ref(s->token,a,b,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK){
        if(!error[0])wood_sp_source_graph_error(s,error,capacity);return;}
    if(value.kind!=GEO_SOURCE_REGION_SET){wood_sp_source_graph_error(s,error,capacity);return;}
    if(!value.as.regions.count)return;GeoRect2 r;
    if(!wood_sp_source_rectangle(&value,&r)){wood_sp_source_graph_error(s,error,capacity);return;}
    snprintf(w->error,w->error_capacity,"V_PROFILE_OVERLAP I45: members %u,%u intersection [%lld,%lld]x[%lld,%lld]",a,b,(long long)r.min_u,(long long)r.max_u,(long long)r.min_v,(long long)r.max_v);
    wood_sp_source_first(error,capacity,w->error);
}
WoodSectionProfileSources *wood_sp_sources_create(GeoEvalContext *graph,GeoProviderToken token,const WoodSectionProfileContext *base)
{
    if(!graph||!base||!base->state||!base->resolve_dimension||!base->live_host)return NULL;
    WoodSectionProfileSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->token=token;s->context=*base;s->authored=base->state;s->decoded=*base->state;s->context.state=&s->decoded;
    s->hooks=(WoodSectionProfileEvaluation){s,wood_sp_source_begin,wood_sp_source_member_root,wood_sp_source_run_root,wood_sp_source_profile_dependency,
        wood_sp_source_member_dimension,wood_sp_source_run_length,wood_sp_source_run_placement,wood_sp_source_live_host,wood_sp_source_pair_root};
    s->context.evaluation=&s->hooks;
    GeoSourceProvider provider={token,"wood.section-profile","wood-section-profile-sources/1",s,wood_sp_source_describe,wood_sp_source_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
static bool wood_sp_source_context_matches(const WoodSectionProfileSources *s,const WoodSectionProfileContext *w)
{
    if(w->state!=s->authored||w->user!=s->context.user||w->error!=s->context.error||w->error_capacity!=s->context.error_capacity||w->resolve_dimension!=s->context.resolve_dimension||w->live_host!=s->context.live_host)return false;
    const WoodEngineeringContext *e=&w->engineering,*a=&s->context.engineering;
    return e->state==a->state&&e->user==a->user&&e->error==a->error&&e->error_capacity==a->error_capacity&&
        e->placement==a->placement&&e->target==a->target&&e->named_value==a->named_value&&e->parameter==a->parameter&&
        e->member_owned==a->member_owned&&e->write_dimension==a->write_dimension&&e->serializable==a->serializable&&
        e->sources==a->sources&&e->resolve_source==a->resolve_source&&e->resolve_binding==a->resolve_binding&&
        e->source_named==a->source_named&&e->source_parameter==a->source_parameter&&e->depend_definition==a->depend_definition&&
        e->validate_application==a->validate_application&&e->versions==a->versions&&e->source_version_field==a->source_version_field&&
        e->source_version_definition==a->source_version_definition&&e->source_application==a->source_application;
}
bool wood_sp_sources_bind(WoodSectionProfileSources *s,WoodSectionProfileContext *w)
{
    if(!s||!w||!wood_sp_source_context_matches(s,w))return false;
    w->evaluation=&s->hooks;return true;
}
bool wood_sp_sources_complete(WoodSectionProfileSources *s)
{
    if(!s)return false;
    for(size_t i=0;i<s->authored->profile_count;++i)if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,s->authored->profiles[i].id))return false;
    for(size_t i=0;i<s->authored->member_count;++i)if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,s->authored->members[i].id))return false;
    for(size_t i=0;i<s->authored->run_count;++i)if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_RUN_DEFINITION,s->authored->runs[i].id))return false;
    return true;
}
void wood_sp_sources_destroy(WoodSectionProfileSources *s)
{if(s){for(size_t i=0;i<s->host_count;++i)free(s->hosts[i]);free(s->hosts);for(size_t i=0;i<s->pair_count;++i)free(s->pairs[i]);free(s->pairs);free(s);}}
