#include "assembly_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <errno.h>

typedef struct WoodAssemblySourceResult {
    WoodAssemblyBaySourceKey key;size_t key_size;struct WoodAssemblySourceResult *next;
    char *text;size_t text_size;char path[192];
    AsmBinding binding;AsmInstance instance;WoodAssemblyDefinition generated;
} WoodAssemblySourceResult;
struct WoodAssemblySources {
    GeoEvalContext *graph;GeoProviderToken token;
    WoodAssemblyContext base,context;WoodAssemblyEvaluation hooks;
    WoodAssemblySourceResult *results;AssemblyState *shadow;
};
static void wood_assembly_key_write(unsigned char *p,uint32_t n)
{for(int i=0;i<4;++i)p[i]=(unsigned char)(n>>(24-8*i));}
static uint32_t wood_assembly_key_read(const unsigned char *p)
{uint32_t n=0;for(int i=0;i<4;++i)n=(n<<8)|p[i];return n;}
GeoSourceRef wood_assembly_source_ref(GeoProviderToken token,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,WoodAssemblySourceKey *key)
{key->bytes[0]=(unsigned char)kind;wood_assembly_key_write(key->bytes+1,id);wood_assembly_key_write(key->bytes+5,version);wood_assembly_key_write(key->bytes+9,sub);return (GeoSourceRef){token,key->bytes,13};}
GeoSourceRef wood_assembly_bay_source_ref(GeoProviderToken token,WoodAssemblySourceKind kind,uint32_t id,AsmIdentity identity,WoodAssemblyBaySourceKey *key)
{key->bytes[0]=(unsigned char)kind;wood_assembly_key_write(key->bytes+1,id);wood_assembly_key_write(key->bytes+5,(uint32_t)identity.kind);wood_assembly_key_write(key->bytes+9,identity.key);wood_assembly_key_write(key->bytes+13,identity.left);wood_assembly_key_write(key->bytes+17,identity.right);return (GeoSourceRef){token,key->bytes,21};}
static bool wood_assembly_bay_source_decode(const GeoSourceRef *ref,WoodAssemblySourceKind *kind,uint32_t *id,AsmIdentity *identity)
{
    if(!ref||!ref->key||ref->key_size!=21)return false;const unsigned char *p=ref->key;
    if(p[0]<WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION||p[0]>WOOD_ASSEMBLY_SOURCE_BAY_GENERATED)return false;
    *kind=(WoodAssemblySourceKind)p[0];*id=wood_assembly_key_read(p+1);*identity=(AsmIdentity){(int)wood_assembly_key_read(p+5),wood_assembly_key_read(p+9),wood_assembly_key_read(p+13),wood_assembly_key_read(p+17)};
    return *id&&identity->key&&((identity->kind==ASM_ID_PRIMARY&&!identity->left&&!identity->right)||(identity->kind==ASM_ID_SECONDARY&&identity->left&&identity->right&&identity->left!=identity->right));
}
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
    if(ref->key_size!=13&&ref->key_size!=21)return NULL;
    for(WoodAssemblySourceResult *r=s->results;r;r=r->next)if(r->key_size==ref->key_size&&!memcmp(r->key.bytes,ref->key,ref->key_size))return r;
    WoodAssemblySourceResult *r=calloc(1,sizeof *r);if(!r)return NULL;r->key_size=ref->key_size;memcpy(r->key.bytes,ref->key,ref->key_size);r->next=s->results;s->results=r;return r;
}
static bool wood_assembly_bay_get(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,AsmIdentity identity,GeoDependencyKind relation,GeoSourceValue *out)
{WoodAssemblyBaySourceKey key;return geo_eval_source(s->graph,wood_assembly_bay_source_ref(s->token,kind,id,identity,&key),relation,out)==GEO_SOURCE_OK;}
static bool wood_assembly_bay_evaluate(WoodAssemblySources *,const GeoSourceRef *,GeoSourceValue *);
static bool wood_assembly_bay_record(WoodAssemblySources *,uint32_t,AsmIdentity,AsmInstance **,int *);
static bool wood_assembly_bay_quantity(WoodAssemblySources *,uint32_t,AsmIdentity,int,GeoCoord *);
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
/* Every policy read is decoded from the returned definition into candidate-
 * local storage. The original arrays remain authoring/admission records. */
static bool wood_assembly_read_json(WoodAssemblySources *s,const GeoSourceValue *value,const char *schema,char *text,size_t capacity,GeoJson *j)
{
    memset(j,0,sizeof *j);
    if(value->kind!=GEO_SOURCE_DEFINITION||!value->as.definition.schema||strcmp(value->as.definition.schema,schema)||
       !value->as.definition.content||value->as.definition.content_size>=capacity||memchr(value->as.definition.content,0,value->as.definition.content_size))
        return wood_eng_fail(&s->context.engineering,"I40: invalid assembly source definition");
    memcpy(text,value->as.definition.content,value->as.definition.content_size);text[value->as.definition.content_size]=0;
    char canonical[ASM_RECORD_MAX+256];
    if(!s->context.json_parse(s->context.user,j,text)||!geo_json_canonical(j,0,canonical,sizeof canonical)||strlen(canonical)!=value->as.definition.content_size||memcmp(canonical,text,value->as.definition.content_size))return wood_eng_fail(&s->context.engineering,"I40: invalid assembly source definition");
    return true;
}
static WoodAssemblySourceResult *wood_assembly_record(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub)
{WoodAssemblySourceKey key;GeoSourceRef ref=wood_assembly_source_ref(s->token,kind,id,version,sub,&key);return wood_assembly_result(s,&ref);}
static bool wood_assembly_load_rule(WoodAssemblySources *s,uint32_t id,uint32_t version)
{
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,id,version,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    char text[ASM_RECORD_MAX];GeoJson j;AsmRuleVersion decoded;
    bool ok=wood_assembly_read_json(s,&value,"wood.assembly.rule/1",text,sizeof text,&j)&&wood_assembly_rule_parse(&s->context,&j,0,&decoded)&&decoded.id==id&&decoded.version==version;geo_json_free(&j);
    if(!ok)return false;const AsmRuleVersion *slot=wood_assembly_rule(&s->context,id,version);if(!slot)return false;
    *(AsmRuleVersion *)slot=decoded;return true;
}
static bool wood_assembly_load_binding(WoodAssemblySources *s,uint32_t id)
{
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    AsmBinding *slot=wood_assembly_binding(&s->context,id);if(!slot)return false;AsmBinding decoded=*slot;char text[ASM_RECORD_MAX];GeoJson j;
    bool ok=wood_assembly_read_json(s,&value,"wood.assembly.binding/1",text,sizeof text,&j);uint32_t actual=0;
    if(ok){int rule=geo_json_member(&j,0,"rule");ok=wood_eng_u32(&j,geo_json_member(&j,0,"id"),&actual,true)&&actual==id&&
        wood_eng_u32(&j,geo_json_member(&j,rule,"id"),&decoded.rule_id,true)&&wood_eng_u32(&j,geo_json_member(&j,rule,"version"),&decoded.rule_version,true)&&
        geo_json_string(&j,geo_json_member(&j,0,"name"),decoded.name,sizeof decoded.name)&&geo_json_canonical(&j,0,decoded.content,sizeof decoded.content);}
    geo_json_free(&j);if(!ok)return false;
    if(wood_assembly_rule(&s->base,decoded.rule_id,decoded.rule_version)&&!wood_assembly_load_rule(s,decoded.rule_id,decoded.rule_version))return false;
    *slot=decoded;return true;
}
static bool wood_assembly_slot_text(WoodAssemblySources *s,uint32_t id,uint32_t sub,char *out,size_t capacity)
{
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,id,0,sub,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    char text[ASM_RECORD_MAX],canonical[ASM_RECORD_MAX];GeoJson j;uint32_t slot=0;
    bool ok=wood_assembly_read_json(s,&value,"wood.assembly.slot/1",text,sizeof text,&j)&&geo_json_keys(&j,0,"slotId,A,B,contactFace,orientation","")&&
        wood_eng_u32(&j,geo_json_member(&j,0,"slotId"),&slot,true)&&slot==sub&&geo_json_canonical(&j,0,canonical,sizeof canonical);geo_json_free(&j);
    if(!ok||strlen(canonical)>=capacity)return false;memcpy(out,canonical,strlen(canonical)+1);return true;
}
static bool wood_assembly_apply_slot(WoodAssemblySources *s,uint32_t id,uint32_t sub,const char *replacement)
{
    if(!wood_assembly_load_binding(s,id))return false;AsmBinding *binding=wood_assembly_binding(&s->context,id);GeoJson j;
    if(!s->context.json_parse(s->context.user,&j,binding->content)){geo_json_free(&j);return false;}
    char name[ASM_NAME_MAX*6+3],text[ASM_RECORD_MAX],part[ASM_RECORD_MAX];bool ok=geo_json_canonical(&j,geo_json_member(&j,0,"name"),name,sizeof name);int n=ok?snprintf(text,sizeof text,"{\"id\":%u,\"name\":%s,\"rule\":{\"id\":%u,\"version\":%u},\"slots\":[",id,name,binding->rule_id,binding->rule_version):-1;
    size_t used=n<0?sizeof text:(size_t)n;int slots=geo_json_member(&j,0,"slots"),found=0;
    for(int i=0;i<geo_json_size(&j,slots)&&ok;++i){uint32_t key;int at=geo_json_at(&j,slots,i);ok=wood_eng_u32(&j,geo_json_member(&j,at,"slotId"),&key,true);const char *item=replacement;
        if(key==sub)++found;else{ok=ok&&geo_json_canonical(&j,at,part,sizeof part);item=part;}size_t size=strlen(item);
        if(!ok||used+size+(i?1:0)+3>=sizeof text){ok=false;break;}if(i)text[used++]=',';memcpy(text+used,item,size);used+=size;}
    geo_json_free(&j);if(!ok||found!=1||used+3>=sizeof text)return false;text[used++]=']';text[used++]='}';text[used]=0;
    memcpy(binding->content,text,used+1);return true;
}
static bool wood_assembly_decode_instance(WoodAssemblySources *s,GeoJson *j,int token,uint32_t id,AsmInstance *out)
{
    int source=geo_json_member(j,token,"source"),rule=geo_json_member(j,source,"rule");uint32_t actual,binding,rule_id,version;
    if(!wood_eng_u32(j,geo_json_member(j,source,"id"),&actual,true)||actual!=id||!wood_eng_u32(j,geo_json_member(j,source,"bindingId"),&binding,true)||
       !wood_eng_u32(j,geo_json_member(j,rule,"id"),&rule_id,true)||!wood_eng_u32(j,geo_json_member(j,rule,"version"),&version,true))return false;
    if(wood_assembly_binding(&s->base,binding)&&!wood_assembly_load_binding(s,binding))return false;
    if(wood_assembly_rule(&s->base,rule_id,version)&&!wood_assembly_load_rule(s,rule_id,version))return false;
    return wood_assembly_instance_definition_parse(&s->context,j,token,out);
}
static bool wood_assembly_load_instance(WoodAssemblySources *s,uint32_t id,AsmInstance **out)
{
    GeoSourceValue definition,mapping;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)||
       !wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&mapping))return false;
    char text[ASM_RECORD_MAX],map_text[ASM_RECORD_MAX],source[ASM_RECORD_MAX],combined[ASM_RECORD_MAX];GeoJson j,map;memset(&map,0,sizeof map);
    bool ok=wood_assembly_read_json(s,&definition,"wood.assembly.instance/1",text,sizeof text,&j)&&geo_json_keys(&j,0,"source,mapping","")&&geo_json_canonical(&j,geo_json_member(&j,0,"source"),source,sizeof source)&&
        wood_assembly_read_json(s,&mapping,"wood.assembly.mapping/1",map_text,sizeof map_text,&map)&&geo_json_is_array(&map,0);geo_json_free(&j);geo_json_free(&map);if(!ok)return false;
    int n=snprintf(combined,sizeof combined,"{\"source\":%s,\"mapping\":%s}",source,map_text);if(n<0||(size_t)n>=sizeof combined)return false;
    AsmInstance decoded;ok=s->context.json_parse(s->context.user,&j,combined)&&wood_assembly_decode_instance(s,&j,0,id,&decoded);geo_json_free(&j);if(!ok)return false;
    AsmInstance *slot=wood_assembly_instance(&s->context,id);if(!slot)return false;*slot=decoded;*out=slot;return true;
}
static bool wood_assembly_load_generated(WoodAssemblySources *s,uint32_t id,uint32_t member,WoodAssemblySourceResult *r,const GeoSourceValue *value,int *index)
{
    char text[ASM_RECORD_MAX+96];GeoJson j;uint32_t actual;AsmInstance decoded;
    bool ok=wood_assembly_read_json(s,value,"wood.assembly.generated/1",text,sizeof text,&j)&&geo_json_keys(&j,0,"instance,memberId","")&&
        wood_eng_u32(&j,geo_json_member(&j,0,"memberId"),&actual,true)&&actual==member&&wood_assembly_decode_instance(s,&j,geo_json_member(&j,0,"instance"),id,&decoded);geo_json_free(&j);
    if(!ok)return false;int m=wood_assembly_source_member(&decoded,member);if(m<0)return false;r->instance=decoded;*index=m;return true;
}
static bool wood_assembly_generated_record(WoodAssemblySources *s,uint32_t id,uint32_t member,AsmInstance **out,int *index)
{
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,id,0,member,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    WoodAssemblySourceResult *r=wood_assembly_record(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,id,0,member);if(!r||!wood_assembly_load_generated(s,id,member,r,&value,index))return false;*out=&r->instance;return true;
}
static bool wood_assembly_definition(WoodAssemblySources *s,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,WoodAssemblySourceResult *r,GeoSourceValue *out)
{
    if(kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION){const AsmRuleVersion *rule=wood_assembly_rule(&s->base,id,version);if(!rule)return false;wood_assembly_definition_value(out,"wood.assembly.rule/1",rule->content);return true;}
    if(kind==WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION){AsmBinding *binding=wood_assembly_binding(&s->base,id);if(!binding)return false;
        /* Identity is recorded before direct binding validation. Missing fixed
         * rules retain the original I40 first error in BINDING_CHECK. */
        if(!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,binding->rule_id,binding->rule_version,0))return false;
        wood_assembly_definition_value(out,"wood.assembly.binding/1",binding->content);return true;
    }
    GeoSourceValue value;
    if(kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION){
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        char authored[ASM_RECORD_MAX];GeoJson j;if(!wood_assembly_read_json(s,&value,"wood.assembly.binding/1",authored,sizeof authored,&j)){geo_json_free(&j);return false;}
        int slots=geo_json_member(&j,0,"slots"),selected=-1;for(int i=0;i<geo_json_size(&j,slots);++i){uint32_t slot;int t=geo_json_at(&j,slots,i);if(wood_eng_u32(&j,geo_json_member(&j,t,"slotId"),&slot,true)&&slot==sub){selected=t;break;}}
        char text[ASM_RECORD_MAX];bool ok=selected>=0&&geo_json_canonical(&j,selected,text,sizeof text);geo_json_free(&j);
        if(!ok||!wood_assembly_text(r,text,strlen(text)))return false;wood_assembly_definition_value(out,"wood.assembly.slot/1",r->text);return true;
    }
    AsmInstance *a=wood_assembly_instance(&s->base,id);if(!a)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION){
        if(!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,a->binding_id,0,0)||!wood_assembly_identity(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,a->rule_id,a->rule_version,0))return false;
        wood_assembly_definition_value(out,"wood.assembly.instance/1",a->content);return true;
    }
    if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION){char authored[ASM_RECORD_MAX];GeoJson j;if(!wood_assembly_read_json(s,&value,"wood.assembly.instance/1",authored,sizeof authored,&j)){geo_json_free(&j);return false;}
        char text[ASM_RECORD_MAX];int mapping=geo_json_member(&j,0,"mapping");bool ok=geo_json_is_array(&j,mapping)&&geo_json_canonical(&j,mapping,text,sizeof text);geo_json_free(&j);
        if(!ok||!wood_assembly_text(r,text,strlen(text)))return false;wood_assembly_definition_value(out,"wood.assembly.mapping/1",r->text);return true;
    }
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION){
        char authored[ASM_RECORD_MAX],source[ASM_RECORD_MAX],mapping[ASM_RECORD_MAX];GeoJson j;
        bool ok=wood_assembly_read_json(s,&value,"wood.assembly.instance/1",authored,sizeof authored,&j)&&geo_json_keys(&j,0,"source,mapping","")&&geo_json_canonical(&j,geo_json_member(&j,0,"source"),source,sizeof source);
        int members=geo_json_member(&j,geo_json_member(&j,0,"source"),"members");bool found=false;
        for(int m=0;m<geo_json_size(&j,members)&&ok;++m){uint32_t member;if(wood_eng_u32(&j,geo_json_member(&j,geo_json_at(&j,members,m),"memberId"),&member,true)&&member==sub)found=true;}ok=ok&&found;geo_json_free(&j);
        if(!ok||!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        ok=wood_assembly_read_json(s,&value,"wood.assembly.mapping/1",mapping,sizeof mapping,&j)&&geo_json_is_array(&j,0);geo_json_free(&j);if(!ok)return false;
        char text[ASM_RECORD_MAX+96];int n=snprintf(text,sizeof text,"{\"instance\":{\"mapping\":%s,\"source\":%s},\"memberId\":%u}",mapping,source,sub);
        if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,"wood.assembly.generated/1",r->text);return true;
    }
    return false;
}
static bool wood_assembly_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodAssemblySources *s=user;WoodAssemblySourceKind kind;uint32_t id,version,sub;bool quantity;
    if(ref->key_size==21){AsmIdentity identity;if(ref->provider!=s->token||!wood_assembly_bay_source_decode(ref,&kind,&id,&identity))return false;quantity=kind==WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_A||kind==WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_B;}
    else{if(ref->provider!=s->token||!wood_assembly_source_decode(ref,&kind,&id,&version,&sub))return false;
        quantity=kind==WOOD_ASSEMBLY_SOURCE_SLOT_A||kind==WOOD_ASSEMBLY_SOURCE_SLOT_B||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_A||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B;}
    *out=(GeoSourceDescriptor){.kind=quantity?GEO_SOURCE_QUANTITY:GEO_SOURCE_DEFINITION,.unit=quantity?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};return true;
}
static bool wood_assembly_generated_value(WoodAssemblySourceResult *r,GeoSourceValue *out)
{
    const WoodAssemblyDefinition *d=&r->generated;char text[512];int n=snprintf(text,sizeof text,
        "{\"between\":[%u,%u],\"depth\":%" PRId64 ",\"direction\":%d,\"guideId\":%u,\"role\":%d,\"surfaceId\":%u,\"timberId\":%u,\"width\":%" PRId64 "}",
        d->between[0],d->between[1],d->depth,(int)d->direction,d->guide_id,(int)d->role,d->surface_id,d->timber_id,d->width);
    if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,"wood.assembly.result/1",r->text);return true;
}
static bool wood_assembly_generated_read(WoodAssemblySources *s,const GeoSourceValue *value,WoodAssemblyDefinition *out)
{
    char text[512];GeoJson j;WoodAssemblyDefinition d={0};int64_t direction,role;
    bool ok=wood_assembly_read_json(s,value,"wood.assembly.result/1",text,sizeof text,&j)&&geo_json_keys(&j,0,"between,depth,direction,guideId,role,surfaceId,timberId,width","")&&
        geo_json_integer(&j,geo_json_member(&j,0,"width"),&d.width)&&d.width>0&&geo_coord_in_range(d.width)&&geo_json_integer(&j,geo_json_member(&j,0,"depth"),&d.depth)&&d.depth>0&&geo_coord_in_range(d.depth)&&
        geo_json_integer(&j,geo_json_member(&j,0,"direction"),&direction)&&(direction==ASM_DIR_U||direction==ASM_DIR_V)&&
        geo_json_integer(&j,geo_json_member(&j,0,"role"),&role)&&(role==WOOD_MEMBER_ROLE_PRIMARY||role==WOOD_MEMBER_ROLE_SECONDARY)&&
        wood_eng_u32(&j,geo_json_member(&j,0,"guideId"),&d.guide_id,true)&&wood_eng_u32(&j,geo_json_member(&j,0,"surfaceId"),&d.surface_id,true)&&wood_eng_u32(&j,geo_json_member(&j,0,"timberId"),&d.timber_id,true);
    int between=geo_json_member(&j,0,"between");ok=ok&&geo_json_is_array(&j,between)&&geo_json_size(&j,between)==2&&wood_eng_u32(&j,geo_json_at(&j,between,0),&d.between[0],true)&&wood_eng_u32(&j,geo_json_at(&j,between,1),&d.between[1],true);geo_json_free(&j);
    if(!ok)return false;d.direction=(AsmDir)direction;d.role=(WoodMemberRole)role;*out=d;return true;
}
static bool wood_assembly_check_value(WoodAssemblySourceResult *r,const char *schema,uint32_t id,const char *field,bool result,GeoSourceValue *out)
{
    char text[96];int n=!strcmp(field,"complete")?snprintf(text,sizeof text,"{\"complete\":%s,\"id\":%u}",result?"true":"false",id):snprintf(text,sizeof text,"{\"id\":%u,\"valid\":%s}",id,result?"true":"false");
    if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,schema,r->text);return true;
}
static bool wood_assembly_check_read(WoodAssemblySources *s,const GeoSourceValue *value,const char *schema,uint32_t id,const char *field,bool *out)
{
    char text[96];GeoJson j;uint32_t actual;int result;
    bool ok=wood_assembly_read_json(s,value,schema,text,sizeof text,&j)&&geo_json_keys(&j,0,!strcmp(field,"complete")?"complete,id":"id,valid","")&&
        wood_eng_u32(&j,geo_json_member(&j,0,"id"),&actual,true)&&actual==id&&geo_json_boolean(&j,geo_json_member(&j,0,field),&result);geo_json_free(&j);
    if(!ok)return false;*out=result!=0;return true;
}
static bool wood_assembly_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodAssemblySources *s=user;WoodAssemblySourceKind kind;uint32_t id,version,sub;
    if(ref->key_size==21)return graph==s->graph&&ref->provider==s->token&&wood_assembly_bay_evaluate(s,ref,out);
    if(graph!=s->graph||ref->provider!=s->token||!wood_assembly_source_decode(ref,&kind,&id,&version,&sub))return false;
    WoodAssemblySourceResult *r=wood_assembly_result(s,ref);if(!r)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION)return wood_assembly_definition(s,kind,id,version,sub,r,out);
    GeoSourceValue definition;
    if(kind==WOOD_ASSEMBLY_SOURCE_BINDING_CHECK){
        if(!wood_assembly_load_binding(s,id))return false;AsmBinding *binding=wood_assembly_binding(&s->context,id);
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)||!wood_assembly_binding_rebuild_direct(&s->context,binding,&r->binding))return false;
        binding->complete=r->binding.complete;return wood_assembly_check_value(r,"wood.assembly.binding-result/1",id,"complete",r->binding.complete,out);
    }
    if(kind==WOOD_ASSEMBLY_SOURCE_SLOT_A||kind==WOOD_ASSEMBLY_SOURCE_SLOT_B){
        char text[ASM_RECORD_MAX];if(!wood_assembly_slot_text(s,id,sub,text,sizeof text)||!wood_assembly_apply_slot(s,id,sub,text))return false;GeoCoord value;
        if(!wood_assembly_slot_dimension_direct(&s->context,id,sub,kind==WOOD_ASSEMBLY_SOURCE_SLOT_B,&value,r->path,sizeof r->path))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    if(kind==WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK){
        AsmInstance *a;if(!wood_assembly_load_instance(s,id,&a))return false;AsmInstance effective=*a;
        if(a->bay_repeat){for(size_t m=0;m<a->mapping_count;++m){AsmInstance *generated;int selected;if(!wood_assembly_bay_record(s,id,a->mapping[m].identity,&generated,&selected))return false;effective.mapping[m]=generated->mapping[selected];}
            if(!wood_assembly_instance_check_direct(&s->context,&effective))return false;return wood_assembly_check_value(r,"wood.assembly.check-result/1",id,"valid",true,out);}
        for(int m=0;m<3;++m){AsmInstance *generated;int selected;if(!wood_assembly_generated_record(s,id,a->member[m],&generated,&selected))return false;effective.timber[m]=generated->timber[selected];effective.secondary[m]=generated->secondary[selected];memcpy(effective.ends[m],generated->ends[selected],sizeof effective.ends[m]);}
        if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)||!wood_assembly_instance_check_direct(&s->context,&effective))return false;return wood_assembly_check_value(r,"wood.assembly.check-result/1",id,"valid",true,out);
    }
    if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,id,0,sub,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition))return false;
    int m;if(!wood_assembly_load_generated(s,id,sub,r,&definition,&m))return false;AsmInstance *a=&r->instance;
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED){if(!wood_assembly_member_definition_direct(&s->context,a,m,&r->generated))return false;return wood_assembly_generated_value(r,out);}
    if(kind==WOOD_ASSEMBLY_SOURCE_GENERATED_A||kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B){GeoCoord value;
        if(!wood_assembly_generated_dimension_direct(&s->context,a,m,kind==WOOD_ASSEMBLY_SOURCE_GENERATED_B,&value,r->path,sizeof r->path))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    return false;
}
static bool wood_assembly_rule_hook(void *user,uint32_t id,uint32_t version)
{return wood_assembly_load_rule(user,id,version);}
static bool wood_assembly_binding_hook(void *user,const AsmBinding *binding,AsmBinding *out)
{
    WoodAssemblySources *s=user;if(wood_assembly_binding(&s->base,binding->id)!=binding&&wood_assembly_binding(&s->context,binding->id)!=binding)return wood_assembly_binding_rebuild_direct(&s->context,binding,out);
    GeoSourceValue value;if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,binding->id,0,0,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    bool complete;if(!wood_assembly_check_read(s,&value,"wood.assembly.binding-result/1",binding->id,"complete",&complete))return false;*out=*binding;out->complete=complete;wood_assembly_binding(&s->context,binding->id)->complete=complete;return true;
}
static bool wood_assembly_slot_hook(void *user,uint32_t binding,uint32_t slot)
{WoodAssemblySources *s=user;GeoSourceValue value;return wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,binding,0,slot,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
static bool wood_assembly_slot_record_hook(void *user,uint32_t binding,uint32_t slot,char *out,size_t capacity)
{WoodAssemblySources *s=user;return wood_assembly_slot_text(s,binding,slot,out,capacity)&&wood_assembly_apply_slot(s,binding,slot,out);}
static bool wood_assembly_instance_hook(void *user,const AsmInstance *a,const AsmInstance **out)
{WoodAssemblySources *s=user;if(wood_assembly_instance(&s->base,a->id)!=a&&wood_assembly_instance(&s->context,a->id)!=a){*out=a;return true;}AsmInstance *decoded;if(!wood_assembly_load_instance(s,a->id,&decoded))return false;*out=decoded;return true;}
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
    return wood_assembly_generated_read(s,&value,out);
}
static bool wood_assembly_generated_hook(void *user,const AsmInstance *a,int m,WoodAssemblyDefinition *out)
{WoodAssemblySources *s=user;if(wood_assembly_instance(&s->base,a->id)!=a&&wood_assembly_instance(&s->context,a->id)!=a)return wood_assembly_member_definition_direct(&s->context,a,m,out);if(m<0||m>=3)return false;return wood_assembly_sources_generated(s,a->id,a->member[m],out);}
static bool wood_assembly_generated_dimension_hook(void *user,const AsmInstance *a,int m,uint32_t slot,int axis,const EngDimensionSource *source,GeoCoord *out,char *path,size_t cap)
{
    WoodAssemblySources *s=user;(void)slot;bool canonical=wood_assembly_instance(&s->base,a->id)==a||wood_assembly_instance(&s->context,a->id)==a;
    for(WoodAssemblySourceResult *r=s->results;!canonical&&r;r=r->next)canonical=&r->instance==a;
    if(!canonical){EngTarget target={1,0,0,axis};return wood_eng_resolve(&s->context.engineering,source,&target,UINT32_MAX,0,out,path,cap);}
    if(m<0||m>=3||axis<0||axis>1)return false;return wood_assembly_quantity(s,axis?WOOD_ASSEMBLY_SOURCE_GENERATED_B:WOOD_ASSEMBLY_SOURCE_GENERATED_A,a->id,a->member[m],out,path,cap);
}
static bool wood_assembly_check_hook(void *user,const AsmInstance *a)
{WoodAssemblySources *s=user;if(wood_assembly_instance(&s->base,a->id)!=a&&wood_assembly_instance(&s->context,a->id)!=a)return wood_assembly_instance_check_direct(&s->context,a);GeoSourceValue value;bool valid;return wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK,a->id,0,0,GEO_DEPENDENCY_VALUE_REQUIRED,&value)&&wood_assembly_check_read(s,&value,"wood.assembly.check-result/1",a->id,"valid",&valid)&&valid;}
bool wood_assembly_sources_member_dimensions(WoodAssemblySources *s,uint32_t id,uint32_t member,GeoCoord *a,GeoCoord *b)
{if(!s||!a||!b)return false;GeoCoord width,depth;if(!wood_assembly_quantity(s,WOOD_ASSEMBLY_SOURCE_GENERATED_A,id,member,&width,NULL,0)||!wood_assembly_quantity(s,WOOD_ASSEMBLY_SOURCE_GENERATED_B,id,member,&depth,NULL,0))return false;*a=width;*b=depth;return true;}
bool wood_assembly_sources_owned_dimensions(WoodAssemblySources *s,uint32_t timber,GeoCoord *a,GeoCoord *b)
{
    if(!s)return false;for(size_t i=0;i<s->base.state->owner_count;++i){const AsmOwner *owner=&s->base.state->owners[i];
        if(owner->kind!=ASM_ID_MEMBER){AsmInstance *instance;int selected;AsmIdentity identity=wood_assembly_owner_identity(owner);if(!wood_assembly_bay_record(s,owner->instance,identity,&instance,&selected))return false;if(instance->mapping[selected].timber==timber)return wood_assembly_bay_quantity(s,owner->instance,identity,0,a)&&wood_assembly_bay_quantity(s,owner->instance,identity,1,b);continue;}
        const AsmInstance *authored=wood_assembly_instance(&s->base,owner->instance);int original=wood_assembly_source_member(authored,owner->member);
        if(original<0||authored->timber[original]!=owner->timber){if(owner->timber==timber)return false;continue;}
        AsmInstance *instance;int m;if(!wood_assembly_generated_record(s,owner->instance,owner->member,&instance,&m))return false;
        if(instance->timber[m]==timber)return wood_assembly_sources_member_dimensions(s,owner->instance,owner->member,a,b);}return false;
}
bool wood_assembly_sources_owned(WoodAssemblySources *s,uint32_t timber,bool *out)
{
    if(!s||!out)return false;bool found=false;
    for(size_t i=0;i<s->base.state->instance_count;++i){AsmInstance *a;if(!wood_assembly_load_instance(s,s->base.state->instances[i].id,&a))return false;
        if(a->bay_repeat){for(size_t m=0;m<a->mapping_count;++m){AsmInstance *generated;int selected;if(!wood_assembly_bay_record(s,a->id,a->mapping[m].identity,&generated,&selected))return false;if(generated->mapping[selected].timber==timber)found=true;}continue;}
        for(int m=0;m<3;++m){AsmInstance *generated;int selected;if(!wood_assembly_generated_record(s,a->id,a->member[m],&generated,&selected))return false;if(generated->timber[selected]==timber)found=true;}}
    *out=found;return true;
}
bool wood_assembly_sources_definitions(WoodAssemblySources *s)
{
    if(!s)return false;GeoSourceValue value;
    for(size_t i=0;i<s->base.state->rule_count;++i){const AsmRuleVersion *r=&s->base.state->rules[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,r->id,r->version,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;}
    for(size_t i=0;i<s->base.state->binding_count;++i){const AsmBinding *b=&s->base.state->bindings[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,b->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        char text[ASM_RECORD_MAX];GeoJson j;if(!wood_assembly_read_json(s,&value,"wood.assembly.binding/1",text,sizeof text,&j)){geo_json_free(&j);return false;}int slots=geo_json_member(&j,0,"slots");bool ok=true;
        for(int k=0;k<geo_json_size(&j,slots)&&ok;++k){uint32_t id;ok=wood_eng_u32(&j,geo_json_member(&j,geo_json_at(&j,slots,k),"slotId"),&id,true)&&wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,b->id,0,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}geo_json_free(&j);if(!ok)return false;
    }
    for(size_t i=0;i<s->base.state->instance_count;++i){const AsmInstance *a=&s->base.state->instances[i];if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,a->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        if(a->bay_repeat){AsmInstance *actual;if(!wood_assembly_load_instance(s,a->id,&actual))return false;for(size_t m=0;m<actual->mapping_count;++m)if(!wood_assembly_bay_get(s,WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION,a->id,actual->mapping[m].identity,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;continue;}
        char text[ASM_RECORD_MAX];GeoJson j;if(!wood_assembly_read_json(s,&value,"wood.assembly.instance/1",text,sizeof text,&j)){geo_json_free(&j);return false;}
        uint32_t members[3];int list=geo_json_member(&j,geo_json_member(&j,0,"source"),"members");bool ok=geo_json_is_array(&j,list)&&geo_json_size(&j,list)==3;
        for(int m=0;m<3&&ok;++m)ok=wood_eng_u32(&j,geo_json_member(&j,geo_json_at(&j,list,m),"memberId"),&members[m],true);geo_json_free(&j);if(!ok||!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,a->id,0,0,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        for(int m=0;m<3;++m)if(!wood_assembly_get(s,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,a->id,0,members[m],GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    }return true;
}
static bool wood_assembly_bay_identity_json(AsmIdentity identity,char *text,size_t capacity)
{
    int n=identity.kind==ASM_ID_PRIMARY?snprintf(text,capacity,"{\"primary\":%u}",identity.key):snprintf(text,capacity,"{\"secondary\":{\"left\":%u,\"line\":%u,\"right\":%u}}",identity.left,identity.key,identity.right);
    return n>=0&&(size_t)n<capacity;
}
static bool wood_assembly_bay_identity_read(GeoJson *j,int t,AsmIdentity *out)
{
    AsmIdentity id={0};int secondary=geo_json_member(j,t,"secondary");
    if(secondary>=0){id.kind=ASM_ID_SECONDARY;if(!geo_json_keys(j,t,"secondary","")||!geo_json_keys(j,secondary,"line,left,right","")||!wood_eng_u32(j,geo_json_member(j,secondary,"line"),&id.key,true)||!wood_eng_u32(j,geo_json_member(j,secondary,"left"),&id.left,true)||!wood_eng_u32(j,geo_json_member(j,secondary,"right"),&id.right,true)||id.left==id.right)return false;}
    else{id.kind=ASM_ID_PRIMARY;if(!geo_json_keys(j,t,"primary","")||!wood_eng_u32(j,geo_json_member(j,t,"primary"),&id.key,true))return false;}
    *out=id;return true;
}
static bool wood_assembly_bay_load_generated(WoodAssemblySources *s,uint32_t id,AsmIdentity identity,WoodAssemblySourceResult *r,const GeoSourceValue *value,int *index)
{
    char text[ASM_RECORD_MAX+256];GeoJson j;AsmIdentity actual;AsmInstance decoded;
    bool ok=wood_assembly_read_json(s,value,"wood.assembly.bay-generated/1",text,sizeof text,&j)&&geo_json_keys(&j,0,"identity,instance","")&&
        wood_assembly_bay_identity_read(&j,geo_json_member(&j,0,"identity"),&actual)&&wood_assembly_identity_equal(actual,identity)&&wood_assembly_decode_instance(s,&j,geo_json_member(&j,0,"instance"),id,&decoded);geo_json_free(&j);
    if(!ok||!decoded.bay_repeat)return false;int selected=wood_assembly_mapping_index(&decoded,identity);if(selected<0)return false;r->instance=decoded;*index=selected;return true;
}
static bool wood_assembly_bay_record(WoodAssemblySources *s,uint32_t id,AsmIdentity identity,AsmInstance **out,int *index)
{
    GeoSourceValue value;if(!wood_assembly_bay_get(s,WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION,id,identity,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    WoodAssemblyBaySourceKey key;GeoSourceRef ref=wood_assembly_bay_source_ref(s->token,WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION,id,identity,&key);WoodAssemblySourceResult *r=wood_assembly_result(s,&ref);
    if(!r||!wood_assembly_bay_load_generated(s,id,identity,r,&value,index))return false;*out=&r->instance;return true;
}
static bool wood_assembly_bay_result(WoodAssemblySourceResult *r,GeoSourceValue *out)
{
    const WoodAssemblyDefinition *d=&r->generated;char text[1280],key[524]="";
    if(d->at.edge_key[0]){int n=snprintf(key,sizeof key,",\"edgeKey\":%s",d->at.edge_key);if(n<0||(size_t)n>=sizeof key)return false;}
    int n=snprintf(text,sizeof text,
        "{\"at\":{\"axis\":%d,\"edge\":%d%s,\"id\":%u,\"index\":\"%" PRId64 "\",\"kind\":%d},\"between\":[%u,%u],\"depth\":%" PRId64 ",\"direction\":%d,\"guideId\":%u,\"role\":%d,\"surfaceId\":%u,\"timberId\":%u,\"width\":%" PRId64 "}",
        d->at.axis,d->at.edge,key,d->at.id,d->at.index,d->at.kind,d->between[0],d->between[1],d->depth,d->direction,d->guide_id,d->role,d->surface_id,d->timber_id,d->width);
    if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,"wood.assembly.result/2",r->text);return true;
}
static bool wood_assembly_bay_result_read(WoodAssemblySources *s,const GeoSourceValue *value,WoodAssemblyDefinition *out)
{
    char text[1280],index[32];GeoJson j;WoodAssemblyDefinition d={0};int64_t direction,role,kind,axis,edge;
    bool ok=wood_assembly_read_json(s,value,"wood.assembly.result/2",text,sizeof text,&j)&&geo_json_keys(&j,0,"at,between,depth,direction,guideId,role,surfaceId,timberId,width","")&&
        geo_json_integer(&j,geo_json_member(&j,0,"width"),&d.width)&&d.width>0&&geo_coord_in_range(d.width)&&geo_json_integer(&j,geo_json_member(&j,0,"depth"),&d.depth)&&d.depth>0&&geo_coord_in_range(d.depth)&&
        geo_json_integer(&j,geo_json_member(&j,0,"direction"),&direction)&&(direction==ASM_DIR_U||direction==ASM_DIR_V)&&geo_json_integer(&j,geo_json_member(&j,0,"role"),&role)&&(role==WOOD_MEMBER_ROLE_PRIMARY||role==WOOD_MEMBER_ROLE_SECONDARY)&&
        wood_eng_u32(&j,geo_json_member(&j,0,"guideId"),&d.guide_id,false)&&wood_eng_u32(&j,geo_json_member(&j,0,"surfaceId"),&d.surface_id,false)&&wood_eng_u32(&j,geo_json_member(&j,0,"timberId"),&d.timber_id,true);
    int at=geo_json_member(&j,0,"at"),between=geo_json_member(&j,0,"between"),key=geo_json_member(&j,at,"edgeKey");ok=ok&&geo_json_keys(&j,at,"axis,edge,id,index,kind","edgeKey")&&geo_json_integer(&j,geo_json_member(&j,at,"axis"),&axis)&&(axis==0||axis==1)&&
        geo_json_integer(&j,geo_json_member(&j,at,"edge"),&edge)&&edge>=0&&edge<=INT32_MAX&&geo_json_integer(&j,geo_json_member(&j,at,"kind"),&kind)&&kind>=ASM_AT_GUIDE&&kind<=ASM_AT_OUTLINE&&
        wood_eng_u32(&j,geo_json_member(&j,at,"id"),&d.at.id,false)&&geo_json_string(&j,geo_json_member(&j,at,"index"),index,sizeof index)&&
        geo_json_is_array(&j,between)&&geo_json_size(&j,between)==2&&wood_eng_u32(&j,geo_json_at(&j,between,0),&d.between[0],false)&&wood_eng_u32(&j,geo_json_at(&j,between,1),&d.between[1],false);
    ok=ok&&(key<0||(geo_json_is_array(&j,key)&&geo_json_size(&j,key)>0&&geo_json_canonical(&j,key,d.at.edge_key,sizeof d.at.edge_key)));
    if(ok){char *end;errno=0;intmax_t integer=strtoimax(index,&end,10);ok=!errno&&end!=index&&!*end&&integer>=INT64_MIN&&integer<=INT64_MAX;d.at.index=(int64_t)integer;}
    geo_json_free(&j);if(!ok)return false;d.at.kind=(int)kind;d.at.axis=(int)axis;d.at.edge=(int)edge;d.direction=(AsmDir)direction;d.role=(WoodMemberRole)role;*out=d;return true;
}
static bool wood_assembly_bay_evaluate(WoodAssemblySources *s,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodAssemblySourceKind kind;uint32_t id;AsmIdentity identity;if(!wood_assembly_bay_source_decode(ref,&kind,&id,&identity))return false;WoodAssemblySourceResult *r=wood_assembly_result(s,ref);if(!r)return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION){AsmInstance *a;if(!wood_assembly_load_instance(s,id,&a)||!a->bay_repeat||wood_assembly_mapping_index(a,identity)<0)return false;
        char key[128],text[ASM_RECORD_MAX+256];if(!wood_assembly_bay_identity_json(identity,key,sizeof key))return false;
        int n=snprintf(text,sizeof text,"{\"identity\":%s,\"instance\":%s}",key,a->content);if(n<0||(size_t)n>=sizeof text||!wood_assembly_text(r,text,(size_t)n))return false;wood_assembly_definition_value(out,"wood.assembly.bay-generated/1",r->text);return true;}
    GeoSourceValue definition;if(!wood_assembly_bay_get(s,WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION,id,identity,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition))return false;int selected;
    if(!wood_assembly_bay_load_generated(s,id,identity,r,&definition,&selected))return false;
    if(kind==WOOD_ASSEMBLY_SOURCE_BAY_GENERATED){if(!wood_assembly_bay_member_definition_direct(&s->context,&r->instance,identity,&r->generated))return false;return wood_assembly_bay_result(r,out);}
    GeoCoord value;if(!wood_assembly_generated_dimension_direct(&s->context,&r->instance,identity.kind==ASM_ID_SECONDARY?2:0,kind==WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_B,&value,r->path,sizeof r->path))return false;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
}
static bool wood_assembly_bay_quantity(WoodAssemblySources *s,uint32_t id,AsmIdentity identity,int axis,GeoCoord *out)
{GeoSourceValue quantity;if(!wood_assembly_bay_get(s,axis?WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_B:WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_A,id,identity,GEO_DEPENDENCY_VALUE_REQUIRED,&quantity)||quantity.kind!=GEO_SOURCE_QUANTITY||quantity.as.quantity.unit!=GEO_UNIT_LENGTH||quantity.as.quantity.den!=1)return false;*out=quantity.as.quantity.num;return true;}
static bool wood_assembly_bay_generated_hook(void *opaque,const AsmInstance *a,AsmIdentity identity,WoodAssemblyDefinition *out)
{WoodAssemblySources *s=opaque;GeoSourceValue value;return wood_assembly_bay_get(s,WOOD_ASSEMBLY_SOURCE_BAY_GENERATED,a->id,identity,GEO_DEPENDENCY_VALUE_REQUIRED,&value)&&wood_assembly_bay_result_read(s,&value,out);}
WoodAssemblySources *wood_assembly_sources_create(GeoEvalContext *graph,GeoProviderToken token,const WoodAssemblyContext *base)
{
    if(!graph||!base||!base->state||!base->diagnostic||!base->parameter_dimension_error||!base->json_parse||base->evaluation)return NULL;
    WoodAssemblySources *s=calloc(1,sizeof *s);if(!s)return NULL;s->shadow=malloc(sizeof *s->shadow);if(!s->shadow){free(s);return NULL;}*s->shadow=*base->state;s->graph=graph;s->token=token;s->base=*base;s->context=*base;s->context.state=s->shadow;
    s->hooks=(WoodAssemblyEvaluation){s,wood_assembly_rule_hook,wood_assembly_binding_hook,wood_assembly_slot_hook,wood_assembly_slot_dimension_hook,wood_assembly_generated_hook,wood_assembly_generated_dimension_hook,wood_assembly_check_hook,wood_assembly_slot_record_hook,wood_assembly_instance_hook,wood_assembly_bay_generated_hook};s->context.evaluation=&s->hooks;
    GeoSourceProvider provider={token,"wood.assembly","wood-assembly-sources/2",s,wood_assembly_describe,wood_assembly_evaluate};if(!geo_eval_register(graph,&provider)){free(s->shadow);free(s);return NULL;}return s;
}
bool wood_assembly_sources_bind(WoodAssemblySources *s,WoodAssemblyContext *w)
{
    if(!s||!w)return false;const WoodAssemblyContext *b=&s->base;const WoodEngineeringContext *e=&w->engineering,*a=&b->engineering;
    if((w->evaluation&&w->evaluation!=&s->hooks)||w->state!=b->state||w->diagnostic!=b->diagnostic||w->parameter_dimension_error!=b->parameter_dimension_error||w->user!=b->user||w->scene_loading!=b->scene_loading||w->json_parse!=b->json_parse||w->drop_position!=b->drop_position||w->other_operation!=b->other_operation||w->surface!=b->surface||w->guide!=b->guide||w->member!=b->member||w->footprint!=b->footprint||w->member_count!=b->member_count||w->member_capacity!=b->member_capacity||w->allocate_member!=b->allocate_member||w->remove_member!=b->remove_member||w->write_member!=b->write_member||w->anchor_matches!=b->anchor_matches||w->instance_content!=b->instance_content||w->bay_report!=b->bay_report||w->position!=b->position||w->dependencies!=b->dependencies||w->external_reference!=b->external_reference||
       e->state!=a->state||e->versions!=a->versions||e->user!=a->user||e->error!=a->error||e->error_capacity!=a->error_capacity||e->sources!=a->sources||e->placement!=a->placement||e->target!=a->target||e->named_value!=a->named_value||e->parameter!=a->parameter||e->member_owned!=a->member_owned||e->write_dimension!=a->write_dimension||e->serializable!=a->serializable||e->resolve_source!=a->resolve_source||e->resolve_binding!=a->resolve_binding||e->source_named!=a->source_named||e->source_parameter!=a->source_parameter||e->depend_definition!=a->depend_definition||e->validate_application!=a->validate_application||e->source_version_field!=a->source_version_field||e->source_version_definition!=a->source_version_definition||e->source_application!=a->source_application)return false;
    w->evaluation=&s->hooks;return true;
}
void wood_assembly_sources_destroy(WoodAssemblySources *s)
{if(!s)return;WoodAssemblySourceResult *r=s->results;while(r){WoodAssemblySourceResult *next=r->next;free(r->text);free(r);r=next;}free(s->shadow);free(s);}
