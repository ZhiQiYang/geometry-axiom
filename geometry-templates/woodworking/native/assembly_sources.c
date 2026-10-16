#include "assembly_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct WoodAssemblySourceResult {
    WoodAssemblySourceKey key;struct WoodAssemblySourceResult *next;
    char *text;size_t text_size;char path[192];
    AsmBinding binding;WoodAssemblyDefinition generated;
} WoodAssemblySourceResult;
struct WoodAssemblySources {
    GeoEvalContext *graph;GeoProviderToken token;
    WoodAssemblyContext base,context;WoodAssemblyEvaluation hooks;
    WoodAssemblySourceResult *results;
};
static void wood_assembly_key_write(unsigned char *p,uint32_t n)
{for(int i=0;i<4;++i)p[i]=(unsigned char)(n>>(24-8*i));}
static uint32_t wood_assembly_key_read(const unsigned char *p)
{uint32_t n=0;for(int i=0;i<4;++i)n=(n<<8)|p[i];return n;}
GeoSourceRef wood_assembly_source_ref(GeoProviderToken token,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,WoodAssemblySourceKey *key)
{key->bytes[0]=(unsigned char)kind;wood_assembly_key_write(key->bytes+1,id);wood_assembly_key_write(key->bytes+5,version);wood_assembly_key_write(key->bytes+9,sub);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
bool wood_assembly_source_decode(const GeoSourceRef *ref,WoodAssemblySourceKind *kind,uint32_t *id,uint32_t *version,uint32_t *sub)
{
    if(!ref||!ref->key||ref->key_size!=13||!kind||!id||!version||!sub)return false;const unsigned char *p=ref->key;
    if(p[0]<WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION||p[0]>WOOD_ASSEMBLY_SOURCE_GENERATED)return false;
    WoodAssemblySourceKind k=(WoodAssemblySourceKind)p[0];uint32_t v=wood_assembly_key_read(p+5),q=wood_assembly_key_read(p+9);
    bool member=k==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION||k==WOOD_ASSEMBLY_SOURCE_GENERATED_A||k==WOOD_ASSEMBLY_SOURCE_GENERATED_B||k==WOOD_ASSEMBLY_SOURCE_GENERATED;
    bool slot=k>=WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION&&k<=WOOD_ASSEMBLY_SOURCE_SLOT_B;
    if((k==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION&&q)||(k!=WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION&&v)||(!member&&!slot&&q))return false;
    *kind=k;*id=wood_assembly_key_read(p+1);*version=v;*sub=q;return true;
}
static WoodAssemblySourceResult *wood_assembly_result(WoodAssemblySources *s,const GeoSourceRef *ref)
{
    for(WoodAssemblySourceResult *r=s->results;r;r=r->next)if(!memcmp(r->key.bytes,ref->key,13))return r;
    WoodAssemblySourceResult *r=calloc(1,sizeof *r);if(!r)return NULL;memcpy(r->key.bytes,ref->key,13);r->next=s->results;s->results=r;return r;
}
static bool wood_assembly_get(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,GeoDependencyKind relation,GeoSourceValue *out)
{
    WoodAssemblySourceKey key;GeoSourceStatus status=geo_eval_source(s->graph,wood_assembly_source_ref(s->token,kind,id,version,sub,&key),relation,out);
    if(status==GEO_SOURCE_MEMORY||status==GEO_SOURCE_CYCLE){*s->context.diagnostic=(AsmDiagnostic){0};return wood_eng_fail(&s->context.engineering,status==GEO_SOURCE_CYCLE?"R44: cyclic assembly source":"CAPACITY: assembly source graph unavailable");}
    return status==GEO_SOURCE_OK;
}
static bool wood_assembly_identity(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub)
{WoodAssemblySourceKey key;return geo_eval_depend(s->graph,wood_assembly_source_ref(s->token,kind,id,version,sub,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK;}
static int wood_assembly_source_member(const AsmInstance *a,uint32_t member)
{if(a)for(int m=0;m<3;++m)if(a->member[m]==member)return m;return -1;}
static bool wood_assembly_text(WoodAssemblySourceResult *r,const char *text,size_t size)
{char *copy=realloc(r->text,size+1);if(!copy)return false;r->text=copy;r->text_size=size;memcpy(copy,text,size);copy[size]=0;return true;}
static void wood_assembly_definition_value(GeoSourceValue *out,const char *schema,const char *text)
{out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,text,strlen(text)};}
static bool wood_assembly_definition(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,WoodAssemblySourceResult *r,GeoSourceValue *out)
{
    if(kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION){const AsmRuleVersion *rule=wood_assembly_rule(&s->context,id,version);if(!rule)return false;wood_assembly_definition_value(out,"wood.assembly.rule/1",rule->content);return true;}
    if(kind==WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION){AsmBinding *binding=wood_assembly_binding(&s->context,id);if(!binding)return false;
        /* Identity is recorded before direct binding validation. Missing fixed
         * rules retain the original I40 first error in BINDING_CHECK. */
        if(!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,binding->rule_id,binding->rule_version,0))return false;
        wood_assembly_definition_value(out,"wood.assembly.binding/1",binding->content);return true;
    }
    GeoSourceValue value;
    if(kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION){
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        AsmBinding *binding=wood_assembly_binding(&s->context,id);GeoJson j;if(!s->context.json_parse(s->context.user,&j,binding->content)){geo_json_free(&j);return false;}
        int slots=geo_json_member(&j,0,"slots"),selected=-1;for(int i=0;i<geo_json_size(&j,slots);++i){uint32_t slot;int t=geo_json_at(&j,slots,i);if(wood_eng_u32(&j,geo_json_member(&j,t,"slotId"),&slot,true)&&slot==sub){selected=t;break;}}
        char text[ASM_RECORD_MAX];bool ok=selected>=0&&geo_json_canonical(&j,selected,text,sizeof text);geo_json_free(&j);
        if(!ok||!wood_assembly_text(r,text,strlen(text)))return false;wood_assembly_definition_value(out,"wood.assembly.slot/1",r->text);return true;
    }
    AsmInstance *a=wood_assembly_instance(&s->context,id);if(!a)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION){
        if(!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,a->binding_id,0,0)||!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,a->rule_id,a->rule_version,0))return false;
        wood_assembly_definition_value(out,"wood.assembly.instance/1",a->content);return true;
    }
    if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION){GeoJson j;if(!s->context.json_parse(s->context.user,&j,a->content)){geo_json_free(&j);return false;}
        char text[ASM_RECORD_MAX];int mapping=geo_json_member(&j,0,"mapping");bool ok=geo_json_is_array(&j,mapping)&&geo_json_canonical(&j,mapping,text,sizeof text);geo_json_free(&j);
        if(!ok||!wood_assembly_text(r,text,strlen(text)))return false;wood_assembly_definition_value(out,"wood.assembly.mapping/1",r->text);return true;
    }
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION){
        if(wood_assembly_source_member(a,sub)<0||!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        char text[ASM_RECORD_MAX+96];int n=snprintf(text,sizeof text,"{\"instance\":%s,\"memberId\":%u}",a->content,sub);
        if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,"wood.assembly.generated/1",r->text);return true;
    }
    return false;
}
static bool wood_assembly_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodAssemblySources *s=user;WoodAssemblySourceKind kind;uint32_t id,version,sub;
    if(ref->provider!=s->token||!wood_assembly_source_decode(ref,&kind,&id,&version,&sub))return false;
    bool quantity=kind==WOOD_ASSEMBLY_SOURCE_SLOT_A||kind==WOOD_ASSEMBLY_SOURCE_SLOT_B||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_A||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B;
    *out=(GeoSourceDescriptor){.kind=quantity?GEO_SOURCE_QUANTITY:GEO_SOURCE_DEFINITION,.unit=quantity?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};return true;
}
static bool wood_assembly_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodAssemblySources *s=user;WoodAssemblySourceKind kind;uint32_t id,version,sub;
    if(graph!=s->graph||ref->provider!=s->token||!wood_assembly_source_decode(ref,&kind,&id,&version,&sub))return false;
    WoodAssemblySourceResult *r=wood_assembly_result(s,ref);if(!r)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION)return wood_assembly_definition(s,kind,id,version,sub,r,out);
    GeoSourceValue definition;
    if(kind==WOOD_ASSEMBLY_SOURCE_BINDING_CHECK){AsmBinding *binding=wood_assembly_binding(&s->context,id);if(!binding)return false;
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)||!wood_assembly_binding_rebuild_direct(&s->context,binding,&r->binding))return false;*out=definition;return true;
    }
    if(kind==WOOD_ASSEMBLY_SOURCE_SLOT_A||kind==WOOD_ASSEMBLY_SOURCE_SLOT_B){
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,id,0,sub,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition))return false;GeoCoord value;
        if(!wood_assembly_slot_dimension_direct(&s->context,id,sub,kind==WOOD_ASSEMBLY_SOURCE_SLOT_B,&value,r->path,sizeof r->path))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    AsmInstance *a=wood_assembly_instance(&s->context,id);if(!a)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK){
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)||!wood_assembly_instance_check_direct(&s->context,a))return false;*out=definition;return true;
    }
    int m=wood_assembly_source_member(a,sub);if(m<0)return false;
    if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,id,0,sub,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition))return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED){if(!wood_assembly_member_definition_direct(&s->context,a,m,&r->generated))return false;*out=definition;return true;}
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED_A||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B){GeoCoord value;
        if(!wood_assembly_generated_dimension_direct(&s->context,a,m,kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B,&value,r->path,sizeof r->path))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    return false;
}
static bool wood_assembly_rule_hook(void *user,uint32_t id,uint32_t version)
{WoodAssemblySources *s=user;GeoSourceValue value;return wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,id,version,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
static bool wood_assembly_binding_hook(void *user,const AsmBinding *binding,AsmBinding *out)
{
    WoodAssemblySources *s=user;if(wood_assembly_binding(&s->context,binding->id)!=binding)return wood_assembly_binding_rebuild_direct(&s->context,binding,out);
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,binding->id,0,0,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    WoodAssemblySourceKey key;GeoSourceRef ref=wood_assembly_source_ref(s->token,WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,binding->id,0,0,&key);WoodAssemblySourceResult *r=wood_assembly_result(s,&ref);if(!r)return false;*out=r->binding;return true;
}
static bool wood_assembly_slot_hook(void *user,uint32_t binding,uint32_t slot)
{WoodAssemblySources *s=user;GeoSourceValue value;return wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,binding,0,slot,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
static bool wood_assembly_quantity(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t sub,GeoCoord *out,char *path,size_t cap)
{
    GeoSourceValue value;if(!wood_assembly_get(s,kind,id,0,sub,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;*out=value.as.quantity.num;
    if(path){WoodAssemblySourceKey key;GeoSourceRef ref=wood_assembly_source_ref(s->token,kind,id,0,sub,&key);WoodAssemblySourceResult *r=wood_assembly_result(s,&ref);if(!r)return false;snprintf(path,cap,"%s",r->path);}return true;
}
static bool wood_assembly_slot_dimension_hook(void *user,uint32_t binding,uint32_t slot,int axis,const EngDimensionSource *source,GeoCoord *out,char *path,size_t cap)
{WoodAssemblySources *s=user;(void)source;if(axis<0||axis>1)return false;return wood_assembly_quantity(s,axis?WOOD_ASSEMBLY_SOURCE_SLOT_B:WOOD_ASSEMBLY_SOURCE_SLOT_A,binding,slot,out,path,cap);}
bool wood_assembly_sources_generated(WoodAssemblySources *s,uint32_t id,uint32_t member,WoodAssemblyDefinition *out)
{
    if(!s||!out)return false;GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED,id,0,member,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    WoodAssemblySourceKey key;GeoSourceRef ref=wood_assembly_source_ref(s->token,WOOD_ASSEMBLY_SOURCE_GENERATED,id,0,member,&key);WoodAssemblySourceResult *r=wood_assembly_result(s,&ref);if(!r)return false;*out=r->generated;return true;
}
static bool wood_assembly_generated_hook(void *user,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{WoodAssemblySources *s=user;if(wood_assembly_instance(&s->context,a->id)!=a)return wood_assembly_member_definition_direct(&s->context,a,m,out);if(m<0||m>=3)return false;return wood_assembly_sources_generated(s,a->id,a->member[m],out);}
static bool wood_assembly_generated_dimension_hook(void *user,const AsmInstance *a,int m,uint32_t slot,int axis,const EngDimensionSource *source,GeoCoord *out,char *path,size_t cap)
{
    WoodAssemblySources *s=user;(void)slot;if(wood_assembly_instance(&s->context,a->id)!=a){EngTarget target={1,0,0,axis};return wood_eng_resolve(&s->context.engineering,source,&target,UINT32_MAX,0,out,path,cap);}
    if(m<0||m>=3||axis<0||axis>1)return false;return wood_assembly_quantity(s,axis?WOOD_ASSEMBLY_SOURCE_GENERATED_B:WOOD_ASSEMBLY_SOURCE_GENERATED_A,a->id,a->member[m],out,path,cap);
}
static bool wood_assembly_check_hook(void *user,const AsmInstance *a)
{WoodAssemblySources *s=user;if(wood_assembly_instance(&s->context,a->id)!=a)return wood_assembly_instance_check_direct(&s->context,a);GeoSourceValue value;return wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK,a->id,0,0,GEO_DEPENDENCY_VALUE_REQUIRED,&value);}
bool wood_assembly_sources_member_dimensions(WoodAssemblySources *s,uint32_t id,uint32_t member,GeoCoord *a,GeoCoord *b)
{if(!s||!a||!b)return false;return wood_assembly_quantity(s,WOOD_ASSEMBLY_SOURCE_GENERATED_A,id,member,a,NULL,0)&&wood_assembly_quantity(s,WOOD_ASSEMBLY_SOURCE_GENERATED_B,id,member,b,NULL,0);}
bool wood_assembly_sources_owned_dimensions(WoodAssemblySources *s,uint32_t timber,GeoCoord *a,GeoCoord *b)
{
    if(!s)return false;for(size_t i=0;i<s->context.state->owner_count;++i){const AsmOwner *owner=&s->context.state->owners[i];if(owner->timber!=timber)continue;
        const AsmInstance *instance=wood_assembly_instance(&s->context,owner->instance);int m=wood_assembly_source_member(instance,owner->member);if(m<0||instance->timber[m]!=timber)return false;
        return wood_assembly_sources_member_dimensions(s,owner->instance,owner->member,a,b);}return false;
}
bool wood_assembly_sources_definitions(WoodAssemblySources *s)
{
    if(!s)return false;GeoSourceValue value;
    for(size_t i=0;i<s->context.state->rule_count;++i){const AsmRuleVersion *r=&s->context.state->rules[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,r->id,r->version,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;}
    for(size_t i=0;i<s->context.state->binding_count;++i){const AsmBinding *b=&s->context.state->bindings[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,b->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        GeoJson j;if(!s->context.json_parse(s->context.user,&j,b->content)){geo_json_free(&j);return false;}int slots=geo_json_member(&j,0,"slots");bool ok=true;
        for(int k=0;k<geo_json_size(&j,slots)&&ok;++k){uint32_t id;ok=wood_eng_u32(&j,geo_json_member(&j,geo_json_at(&j,slots,k),"slotId"),&id,true)&&wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,b->id,0,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}geo_json_free(&j);if(!ok)return false;
    }
    for(size_t i=0;i<s->context.state->instance_count;++i){const AsmInstance *a=&s->context.state->instances[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,a->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)||!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,a->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        for(int m=0;m<3;++m)if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,a->id,0,a->member[m],GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    }return true;
}
WoodAssemblySources *wood_assembly_sources_create(GeoEvalContext *graph,GeoProviderToken token,const WoodAssemblyContext *base)
{
    if(!graph||!base||!base->state||!base->diagnostic||!base->parameter_dimension_error||!base->json_parse||base->evaluation)return NULL;
    WoodAssemblySources *s=calloc(1,sizeof *s);if(!s)return NULL;s->graph=graph;s->token=token;s->base=*base;s->context=*base;
    s->hooks=(WoodAssemblyEvaluation){s,wood_assembly_rule_hook,wood_assembly_binding_hook,wood_assembly_slot_hook,wood_assembly_slot_dimension_hook,wood_assembly_generated_hook,wood_assembly_generated_dimension_hook,wood_assembly_check_hook};s->context.evaluation=&s->hooks;
    GeoSourceProvider provider={token,"wood.assembly","wood-assembly-sources/1",s,wood_assembly_describe,wood_assembly_evaluate};if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
bool wood_assembly_sources_bind(WoodAssemblySources *s,WoodAssemblyContext *w)
{
    if(!s||!w)return false;const WoodAssemblyContext *b=&s->base;const WoodEngineeringContext *e=&w->engineering,*a=&b->engineering;
    if((w->evaluation&&w->evaluation!=&s->hooks)||w->state!=b->state||w->diagnostic!=b->diagnostic||w->parameter_dimension_error!=b->parameter_dimension_error||w->user!=b->user||w->scene_loading!=b->scene_loading||w->json_parse!=b->json_parse||w->drop_position!=b->drop_position||w->other_operation!=b->other_operation||w->surface!=b->surface||w->guide!=b->guide||w->member!=b->member||w->footprint!=b->footprint||w->member_count!=b->member_count||w->member_capacity!=b->member_capacity||w->allocate_member!=b->allocate_member||w->remove_member!=b->remove_member||w->write_member!=b->write_member||w->anchor_matches!=b->anchor_matches||w->instance_content!=b->instance_content||
       e->state!=a->state||e->versions!=a->versions||e->user!=a->user||e->error!=a->error||e->error_capacity!=a->error_capacity||e->sources!=a->sources||e->placement!=a->placement||e->target!=a->target||e->named_value!=a->named_value||e->parameter!=a->parameter||e->member_owned!=a->member_owned||e->write_dimension!=a->write_dimension||e->serializable!=a->serializable||e->resolve_source!=a->resolve_source||e->resolve_binding!=a->resolve_binding||e->source_named!=a->source_named||e->source_parameter!=a->source_parameter||e->depend_definition!=a->depend_definition||e->validate_application!=a->validate_application||e->source_version_field!=a->source_version_field||e->source_version_definition!=a->source_version_definition||e->source_application!=a->source_application)return false;
    w->evaluation=&s->hooks;return true;
}
void wood_assembly_sources_destroy(WoodAssemblySources *s)
{if(!s)return;WoodAssemblySourceResult *r=s->results;while(r){WoodAssemblySourceResult *next=r->next;free(r->text);free(r);r=next;}free(s);}
