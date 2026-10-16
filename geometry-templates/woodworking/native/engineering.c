#include "engineering.h"
#include <stdio.h>
#include <string.h>
/* Match the host diagnostic truncation without borrowing host globals. */
bool wood_eng_fail(const WoodEngineeringContext *w,const char *text)
{
    snprintf(w->error,w->error_capacity,"%s",text);
    size_t len=strlen(w->error),i=len;
    while(i>0&&((unsigned char)w->error[i-1]&0xC0)==0x80)--i;
    if(i){unsigned char lead=(unsigned char)w->error[i-1];size_t need=lead<0x80?1:(lead&0xE0)==0xC0?2:(lead&0xF0)==0xE0?3:(lead&0xF8)==0xF0?4:1;if(len-(i-1)<need)w->error[i-1]=0;}
    return false;
}
bool wood_eng_id(const char *s)
{
    size_t n=strlen(s); if (!n || n>=ENG_ID_MAX) return false;
    for (size_t i=0;i<n;++i) if (!((s[i]>='a'&&s[i]<='z')||(s[i]>='A'&&s[i]<='Z')||(s[i]>='0'&&s[i]<='9')||s[i]=='_'||s[i]=='-')) return false;
    return true;
}
bool wood_eng_u32(const GeoJson *j,int t,uint32_t *out,bool positive)
{
    int64_t n; if (!geo_json_integer(j,t,&n) || n<(positive?1:0) || (uint64_t)n>UINT32_MAX) return false;
    *out=(uint32_t)n; return true;
}
bool wood_eng_coord(const GeoJson *j,int t,GeoCoord *out,bool positive)
{
    int64_t n; if (!geo_json_integer(j,t,&n) || n<(positive?1:0) || n>GEO_COORD_LIMIT) return false;
    *out=n; return true;
}
bool wood_eng_optional_text(const GeoJson *j,int obj,const char *key)
{
    int t=geo_json_member(j,obj,key); char text[ENG_RECORD_MAX];
    return t<0 || geo_json_is_null(j,t) || geo_json_string(j,t,text,sizeof text);
}
bool wood_eng_ref_parse(GeoJson *j,int t,EngVersionRef *r,bool optional)
{
    memset(r,0,sizeof *r);
    if (optional && (t<0 || geo_json_is_null(j,t))) return true;
    return geo_json_keys(j,t,"id,version","") && geo_json_string(j,geo_json_member(j,t,"id"),r->id,sizeof r->id) && wood_eng_id(r->id) && wood_eng_u32(j,geo_json_member(j,t,"version"),&r->version,true);
}
bool wood_eng_axis(const GeoJson *j,int t,int *axis)
{
    *axis=0; if (t<0 || geo_json_is_null(j,t)) return true;
    char value[8]; if (!geo_json_string(j,t,value,sizeof value)) return false;
    if (!strcmp(value,"u")) *axis=1; else if (!strcmp(value,"v")) *axis=2; else return false;
    return true;
}
static const char *wood_eng_version_schema(int kind)
{return kind?"woodworking.method-version/1":"woodworking.material-version/1";}
static GeoVersionIdentity wood_eng_version_identity(int kind,const EngVersionRef *ref,unsigned char key[ENG_ID_MAX+1])
{size_t n=strlen(ref->id);key[0]=(unsigned char)(kind+1);memcpy(key+1,ref->id,n);return (GeoVersionIdentity){key,n+1,ref->version};}
bool wood_eng_version_view_direct(const WoodEngineeringContext *w,int kind,const char *id,uint32_t version,GeoVersionView *out)
{
    if(!w||!w->versions||!id||!out||(kind!=0&&kind!=1)||!wood_eng_id(id)||!version)return false;
    unsigned char key[ENG_ID_MAX+1];EngVersionRef ref={0};memcpy(ref.id,id,strlen(id)+1);ref.version=version;
    GeoVersionView view;const char *schema=wood_eng_version_schema(kind);
    if(geo_versions_find(w->versions,wood_eng_version_identity(kind,&ref,key),&view)!=GEO_VERSION_OK||
       view.schema_length!=strlen(schema)||memcmp(view.schema,schema,view.schema_length))return false;
    *out=view;return true;
}
bool wood_eng_version_view(const WoodEngineeringContext *w,int kind,const char *id,uint32_t version,GeoVersionView *out)
{return wood_eng_version_view_direct(w,kind,id,version,out);}
static bool wood_eng_read_version(const WoodEngineeringContext *w,int kind,const char *id,uint32_t version,GeoVersionView *out,GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY])
{
    if(!w||!id||!wood_eng_id(id)||!version)return false;
    if(w->source_version_definition){EngVersionRef identity={0};memcpy(identity.id,id,strlen(id)+1);identity.version=version;
        return w->source_version_definition(w->sources,kind,&identity,out,fields);}
    return wood_eng_version_view_direct(w,kind,id,version,out);
}
static const GeoVersionField *wood_eng_view_field(const GeoVersionView *view,uint32_t id)
{for(size_t i=0;i<view->field_count;++i)if(view->fields[i].id==id)return &view->fields[i];return NULL;}
static bool wood_eng_view_integer(const GeoVersionView *view,uint32_t field,GeoQuantityUnit unit,GeoCoord minimum,GeoCoord maximum,GeoCoord *out)
{const GeoVersionField *value=wood_eng_view_field(view,field);return value&&geo_version_field_integer(value,unit,minimum,maximum,out)==GEO_VERSION_OK;}
bool wood_eng_material_integer(const WoodEngineeringContext *w,const EngMaterialVersion *material,uint32_t field,GeoCoord minimum,GeoCoord maximum,GeoCoord *out)
{
    if(!w||!w->versions||!material||!out)return false;
    GeoVersionView view;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];
    return wood_eng_read_version(w,0,material->ref.id,material->ref.version,&view,fields)&&wood_eng_view_integer(&view,field,GEO_UNIT_LENGTH,minimum,maximum,out);
}
static bool wood_eng_version_copy(const GeoVersionView *view,char *content,char *fingerprint)
{
    if(view->content_length>=ENG_RECORD_MAX||view->fingerprint_length!=64)return false;
    memcpy(content,view->content,view->content_length);content[view->content_length]=0;
    memcpy(fingerprint,view->fingerprint,64);fingerprint[64]=0;return true;
}
const EngMaterialVersion *wood_eng_material(const WoodEngineeringContext *w,const char *id,uint32_t version)
{
    GeoVersionView view;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];if(!w||!w->state||!wood_eng_read_version(w,0,id,version,&view,fields))return NULL;
    size_t at=0;while(at<w->state->material_count&&(w->state->materials[at].ref.version!=version||strcmp(w->state->materials[at].ref.id,id)))++at;
    if(at==w->state->material_count)return NULL;
    EngMaterialVersion next;memset(&next,0,sizeof next);next.ref=w->state->materials[at].ref;next.archived=w->state->materials[at].archived;
    int64_t kind;if(!wood_eng_version_copy(&view,next.content,next.fingerprint)||
       !wood_eng_view_integer(&view,WOOD_ENG_VERSION_KIND,GEO_UNIT_SCALAR,0,1,&kind))return NULL;
    next.kind=(int)kind;
    if(next.kind){
        if(!wood_eng_view_integer(&view,ENG_A,GEO_UNIT_LENGTH,1,GEO_COORD_LIMIT,&next.a)||
           !wood_eng_view_integer(&view,ENG_B,GEO_UNIT_LENGTH,1,GEO_COORD_LIMIT,&next.b))return NULL;
    }else{
        if(!wood_eng_view_integer(&view,ENG_WIDTH,GEO_UNIT_LENGTH,1,GEO_COORD_LIMIT,&next.width)||
           !wood_eng_view_integer(&view,ENG_LENGTH,GEO_UNIT_LENGTH,1,GEO_COORD_LIMIT,&next.length))return NULL;
        const GeoVersionField *field=wood_eng_view_field(&view,WOOD_ENG_VERSION_THICKNESS);
        if(field){
            if(field->kind!=GEO_VERSION_DECIMAL_LITERAL||field->value.unit!=GEO_UNIT_LENGTH||field->literal_length>=sizeof next.thickness)return NULL;
            memcpy(next.thickness,field->literal,field->literal_length);next.has_thickness=true;
        }
    }
    memcpy(&w->state->materials[at],&next,sizeof next);return &w->state->materials[at];
}
const EngMethodVersion *wood_eng_method(const WoodEngineeringContext *w,const char *id,uint32_t version)
{
    GeoVersionView view;GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];if(!w||!w->state||!wood_eng_read_version(w,1,id,version,&view,fields))return NULL;
    size_t at=0;while(at<w->state->method_count&&(w->state->methods[at].ref.version!=version||strcmp(w->state->methods[at].ref.id,id)))++at;
    if(at==w->state->method_count)return NULL;
    EngMethodVersion next;memset(&next,0,sizeof next);next.ref=w->state->methods[at].ref;next.archived=w->state->methods[at].archived;
    if(!wood_eng_version_copy(&view,next.content,next.fingerprint))return NULL;
    int64_t value;
    if(!wood_eng_view_integer(&view,WOOD_ENG_VERSION_LONG_AXIS,GEO_UNIT_SCALAR,0,2,&value))return NULL;
    next.long_axis=(int)value;
    if(!wood_eng_view_integer(&view,WOOD_ENG_VERSION_MAIN_ALONG,GEO_UNIT_SCALAR,0,2,&value))return NULL;
    next.main_along=(int)value;
    const GeoVersionField *gap=wood_eng_view_field(&view,WOOD_ENG_VERSION_GAP);
    if(gap){
        if(geo_version_field_integer(gap,GEO_UNIT_LENGTH,0,GEO_COORD_LIMIT,&next.gap)!=GEO_VERSION_OK)return NULL;next.has_gap=true;
    }
    GeoJson j;bool ok=geo_json_parse_n(&j,(const char *)view.content,view.content_length);
    if(ok)ok=wood_eng_ref_parse(&j,geo_json_member(&j,0,"panel"),&next.panel,true);
    int roles=ok?geo_json_member(&j,0,"roles"):-1;const char *names[]={"boundary","primary","secondary"};
    if(ok&&roles>=0&&!geo_json_is_null(&j,roles))for(int r=0;r<3&&ok;++r)ok=wood_eng_ref_parse(&j,geo_json_member(&j,roles,names[r]),&next.roles[r],true);
    geo_json_free(&j);if(!ok)return NULL;
    memcpy(&w->state->methods[at],&next,sizeof next);return &w->state->methods[at];
}
const EngMaterialVersion *wood_eng_material_at(const WoodEngineeringContext *w,size_t index)
{if(!w||!w->state||index>=w->state->material_count)return NULL;EngVersionRef ref=w->state->materials[index].ref;return wood_eng_material(w,ref.id,ref.version);}
const EngMethodVersion *wood_eng_method_at(const WoodEngineeringContext *w,size_t index)
{if(!w||!w->state||index>=w->state->method_count)return NULL;EngVersionRef ref=w->state->methods[index].ref;return wood_eng_method(w,ref.id,ref.version);}
EngApplication *wood_eng_application_direct(WoodEngineeringContext *w,const char *id)
{
    for (size_t i=0;i<w->state->application_count;++i) if (!strcmp(w->state->applications[i].id,id)) return &w->state->applications[i];
    return NULL;
}
EngApplication *wood_eng_application(WoodEngineeringContext *w,const char *id)
{return w->source_application?w->source_application(w->sources,id):wood_eng_application_direct(w,id);}
const char *const ENG_FIELDS[]={"width","length","A","B","u.panel","v.panel","u.gap","v.gap","boundary.A","boundary.B","primary.A","primary.B","secondary.A","secondary.B"};
bool wood_eng_source_parse(WoodEngineeringContext *w,GeoJson *j,int t,EngDimensionSource *s,bool allow_app)
{
    memset(s,0,sizeof *s); char kind[24],field[32];
    if (!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind)) return wood_eng_fail(w,"I35: dimension source needs a kind");
    if (!strcmp(kind,"literal")) {
        s->kind=ENG_LITERAL;
        if (!geo_json_keys(j,t,"kind,value","") || !wood_eng_coord(j,geo_json_member(j,t,"value"),&s->value,false)) return wood_eng_fail(w,"I35: literal dimension must be integer mm in D1 range");
    } else if (!strcmp(kind,"spec")) {
        s->kind=ENG_SPEC;
        if (!geo_json_keys(j,t,"kind,name","") || !geo_json_string(j,geo_json_member(j,t,"name"),s->ref,sizeof s->ref) || !geo_named_value_name_valid(s->ref)) return wood_eng_fail(w,"I35: invalid named-spec dimension source");
    } else if (!strcmp(kind,"parameter")) {
        s->kind=ENG_PARAMETER;s->parameter.set=true;
        if(!geo_json_keys(j,t,"kind,parameterId,fieldId","")||!wood_eng_u32(j,geo_json_member(j,t,"parameterId"),&s->parameter.parameter_id,false)||!wood_eng_u32(j,geo_json_member(j,t,"fieldId"),&s->parameter.field_id,false))return wood_eng_fail(w,"I38: invalid parameter dimension source");
    } else if (!strcmp(kind,"material") || !strcmp(kind,"application")) {
        s->kind=!strcmp(kind,"material")?ENG_MATERIAL:ENG_APPLICATION;
        if (s->kind==ENG_APPLICATION && !allow_app) return wood_eng_fail(w,"I35: application override cannot refer to another application");
        if (!geo_json_keys(j,t,s->kind==ENG_MATERIAL?"kind,id,version,field":"kind,id,field","") ||
            !geo_json_string(j,geo_json_member(j,t,"id"),s->ref,sizeof s->ref) || !wood_eng_id(s->ref) ||
            (s->kind==ENG_MATERIAL && !wood_eng_u32(j,geo_json_member(j,t,"version"),&s->version,true)) ||
            !geo_json_string(j,geo_json_member(j,t,"field"),field,sizeof field)) return wood_eng_fail(w,"I35: incomplete material/application dimension source");
        int f=0; while (f<14 && strcmp(field,ENG_FIELDS[f])) ++f;
        if (f==14 || (s->kind==ENG_MATERIAL && f>ENG_B) || (s->kind==ENG_APPLICATION && f<ENG_U_PANEL)) return wood_eng_fail(w,"I35: unsupported source field");
        s->field=f;
    } else return wood_eng_fail(w,"I35: unsupported dimension source kind");
    return true;
}
bool wood_eng_target_parse(WoodEngineeringContext *w,GeoJson *j,int t,EngTarget *target)
{
    memset(target,0,sizeof *target); char kind[16],field[16],axis[8];
    if (!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind) || !wood_eng_u32(j,geo_json_member(j,t,"id"),&target->id,false) || !geo_json_string(j,geo_json_member(j,t,"field"),field,sizeof field)) return wood_eng_fail(w,"I35: invalid dimension target");
    if (!strcmp(kind,"grid")) {
        if (!geo_json_keys(j,t,"kind,id,axis,field","") || !geo_json_string(j,geo_json_member(j,t,"axis"),axis,sizeof axis) || (strcmp(axis,"u")&&strcmp(axis,"v")) || (strcmp(field,"panel")&&strcmp(field,"gap"))) return wood_eng_fail(w,"I35: grid target requires u/v and panel/gap");
        target->axis=!strcmp(axis,"v"); target->field=!strcmp(field,"gap");
    } else if (!strcmp(kind,"timber")) {
        if (!geo_json_keys(j,t,"kind,id,field","") || (strcmp(field,"A")&&strcmp(field,"B"))) return wood_eng_fail(w,"I35: timber target requires A/B");
        target->kind=1; target->field=!strcmp(field,"B");
    } else return wood_eng_fail(w,"I35: unsupported target kind");
    return true;
}
bool wood_eng_same_target(const EngTarget *a,const EngTarget *b) { return a->kind==b->kind && a->id==b->id && a->axis==b->axis && a->field==b->field; }
EngBinding *wood_eng_binding(WoodEngineeringContext *w,const EngTarget *target)
{
    for (size_t i=0;i<w->state->binding_count;++i) if (wood_eng_same_target(target,&w->state->bindings[i].target)) return &w->state->bindings[i];
    return NULL;
}
bool wood_eng_bind(WoodEngineeringContext *w,const EngTarget *target,const EngDimensionSource *source)
{
    if(target->kind&&w->member_owned(w->user,target->id))return wood_eng_fail(w,"I42: owned timber dimensions come from its assembly binding");
    EngBinding *b=wood_eng_binding(w,target);
    if (!b) {
        if (w->state->binding_count==ENG_BINDING_MAX) return wood_eng_fail(w,"I10: engineering dimension binding capacity exceeded");
        b=&w->state->bindings[w->state->binding_count++]; memset(b,0,sizeof *b); b->target=*target;
    }
    b->source=*source; return true;
}
bool wood_eng_object_bound(const WoodEngineeringContext *w,int kind,uint32_t id)
{
    for (size_t i=0;i<w->state->binding_count;++i) if (w->state->bindings[i].target.kind==kind && w->state->bindings[i].target.id==id) return true;
    return false;
}
bool wood_engineering_used(const WoodEngineeringContext *w) { return w->state->material_count || w->state->method_count || w->state->application_count || w->state->binding_count; }

static bool wood_eng_version_error(WoodEngineeringContext *w,int kind,GeoVersionStatus status)
{
    if(status==GEO_VERSION_FINGERPRINT)return wood_eng_fail(w,kind?"I34: method fingerprint mismatch":"I34: material fingerprint mismatch");
    if(status==GEO_VERSION_IMMUTABLE)return wood_eng_fail(w,kind?"I34: method ID/version already has different immutable content":"I34: material ID/version already has different immutable content");
    if(status==GEO_VERSION_CAPACITY_EXCEEDED)return wood_eng_fail(w,kind?"I10: method version capacity exceeded":"I10: material version capacity exceeded");
    return wood_eng_fail(w,kind?"I34: invalid typed method version storage":"I34: invalid typed material version storage");
}
static GeoVersionDefinition wood_eng_version_definition(int kind,const EngVersionRef *ref,const char *content,const char *fingerprint,
    const GeoVersionField *fields,size_t field_count,unsigned char key[ENG_ID_MAX+1])
{
    const char *schema=wood_eng_version_schema(kind);
    GeoVersionDefinition definition={wood_eng_version_identity(kind,ref,key),content,strlen(content),fingerprint,strlen(fingerprint),fields,field_count,schema,strlen(schema)};
    return definition;
}
bool wood_eng_publish_material(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint)
{
    EngMaterialVersion m;memset(&m,0,sizeof m);char kind[16],name[192],thickness[ENG_THICKNESS_CAPACITY];
    if (!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind)) return wood_eng_fail(w,"D26: material kind is required");
    m.kind=!strcmp(kind,"timber");
    if ((!m.kind && strcmp(kind,"panel")) || !geo_json_keys(j,t,m.kind?"id,version,kind,name,A,B":"id,version,kind,name,width,length",m.kind?"brand,model,notes":"thickness,brand,model,notes") ||
        !geo_json_string(j,geo_json_member(j,t,"id"),m.ref.id,sizeof m.ref.id) || !wood_eng_id(m.ref.id) ||
        !wood_eng_u32(j,geo_json_member(j,t,"version"),&m.ref.version,true) || !geo_json_string(j,geo_json_member(j,t,"name"),name,sizeof name) || !name[0] ||
        !wood_eng_optional_text(j,t,"brand") || !wood_eng_optional_text(j,t,"model") || !wood_eng_optional_text(j,t,"notes")) return wood_eng_fail(w,"D26: invalid material identity, name or fields");
    if (m.kind) {
        if (!wood_eng_coord(j,geo_json_member(j,t,"A"),&m.a,true) || !wood_eng_coord(j,geo_json_member(j,t,"B"),&m.b,true)) return wood_eng_fail(w,"D26: timber A/B must be positive integer mm");
    } else {
        if (!wood_eng_coord(j,geo_json_member(j,t,"width"),&m.width,true) || !wood_eng_coord(j,geo_json_member(j,t,"length"),&m.length,true)) return wood_eng_fail(w,"D26: panel width/length must be positive integer mm");
        int k=geo_json_member(j,t,"thickness");
        if (k>=0 && !geo_json_is_null(j,k)) {
            if (!geo_json_string(j,k,thickness,sizeof thickness) || !thickness[0]) return wood_eng_fail(w,"D26: thickness must be a positive decimal string or null");
            bool dot=false,positive=false; size_t n=strlen(thickness);
            for (size_t i=0;i<n;++i) { if (thickness[i]=='.' && !dot && i>0 && i+1<n) dot=true; else if (thickness[i]>='0'&&thickness[i]<='9') positive|=thickness[i]!='0'; else return wood_eng_fail(w,"D26: invalid decimal thickness"); }
            if (!positive) return wood_eng_fail(w,"D26: thickness must be positive");
            m.has_thickness=true;memcpy(m.thickness,thickness,n+1);
        }
    }
    if (!geo_json_canonical(j,t,m.content,sizeof m.content)) return wood_eng_fail(w,"I10: material content exceeds record capacity");
    geo_sha256(m.content,strlen(m.content),m.fingerprint);
    GeoVersionField fields[4]={0};size_t count=3;
    fields[0]=(GeoVersionField){WOOD_ENG_VERSION_KIND,{m.kind,1,GEO_UNIT_SCALAR}};
    fields[1]=(GeoVersionField){m.kind?ENG_A:ENG_WIDTH,{m.kind?m.a:m.width,1,GEO_UNIT_LENGTH}};
    fields[2]=(GeoVersionField){m.kind?ENG_B:ENG_LENGTH,{m.kind?m.b:m.length,1,GEO_UNIT_LENGTH}};
    if(m.has_thickness){fields[count].id=WOOD_ENG_VERSION_THICKNESS;fields[count].kind=GEO_VERSION_DECIMAL_LITERAL;
        fields[count].value.unit=GEO_UNIT_LENGTH;fields[count].literal_length=strlen(m.thickness);
        memcpy(fields[count].literal,m.thickness,fields[count].literal_length);++count;}
    unsigned char key[ENG_ID_MAX+1];GeoVersionDefinition definition=wood_eng_version_definition(0,&m.ref,m.content,fingerprint?fingerprint:m.fingerprint,fields,count,key);
    GeoVersionStatus status=geo_versions_check(w->versions,&definition,NULL);
    if(status!=GEO_VERSION_OK)return wood_eng_version_error(w,0,status);
    GeoVersionView previous;bool exists=geo_versions_find(w->versions,definition.identity,&previous)==GEO_VERSION_OK;
    if(!exists&&w->state->material_count==ENG_MATERIAL_MAX)return wood_eng_fail(w,"I10: material version capacity exceeded");
    status=geo_versions_put(w->versions,&definition,NULL);if(status!=GEO_VERSION_OK)return wood_eng_version_error(w,0,status);
    if(!exists)w->state->materials[w->state->material_count++]=m;
    return wood_eng_material(w,m.ref.id,m.ref.version)!=NULL||wood_eng_version_error(w,0,GEO_VERSION_INVALID);
}
bool wood_eng_publish_method(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint)
{
    EngMethodVersion m;memset(&m,0,sizeof m);char name[192];
    if (!geo_json_keys(j,t,"id,version,name","panel,roles,gap,longAxis,mainAlong,notes") || !geo_json_string(j,geo_json_member(j,t,"id"),m.ref.id,sizeof m.ref.id) || !wood_eng_id(m.ref.id) ||
        !wood_eng_u32(j,geo_json_member(j,t,"version"),&m.ref.version,true) || !geo_json_string(j,geo_json_member(j,t,"name"),name,sizeof name) || !name[0] || !wood_eng_optional_text(j,t,"notes") ||
        !wood_eng_ref_parse(j,geo_json_member(j,t,"panel"),&m.panel,true) || !wood_eng_axis(j,geo_json_member(j,t,"longAxis"),&m.long_axis) || !wood_eng_axis(j,geo_json_member(j,t,"mainAlong"),&m.main_along)) return wood_eng_fail(w,"D27: invalid method identity or settings");
    int roles=geo_json_member(j,t,"roles"); const char *names[]={"boundary","primary","secondary"};
    if (roles>=0 && !geo_json_is_null(j,roles)) {
        if (!geo_json_keys(j,roles,"","boundary,primary,secondary")) return wood_eng_fail(w,"D27: method has an unknown role slot");
        for (int r=0;r<3;++r) if (!wood_eng_ref_parse(j,geo_json_member(j,roles,names[r]),&m.roles[r],true)) return wood_eng_fail(w,"D27: invalid role material reference");
    }
    int gap=geo_json_member(j,t,"gap"); m.has_gap=gap>=0&&!geo_json_is_null(j,gap);
    if (m.has_gap && !wood_eng_coord(j,gap,&m.gap,false)) return wood_eng_fail(w,"D27: gap must be explicit nonnegative integer mm");
    for (int r=-1;r<3;++r) {
        const EngVersionRef *ref=r<0?&m.panel:&m.roles[r]; if (!ref->id[0]) continue;
        const EngMaterialVersion *mat=wood_eng_material(w,ref->id,ref->version);
        if (!mat || mat->kind!=(r<0?0:1)) return wood_eng_fail(w,"I34: method material version is missing or has incompatible kind");
    }
    if (!geo_json_canonical(j,t,m.content,sizeof m.content)) return wood_eng_fail(w,"I10: method content exceeds record capacity");
    geo_sha256(m.content,strlen(m.content),m.fingerprint);
    GeoVersionField fields[3]={0};size_t count=2;
    fields[0]=(GeoVersionField){WOOD_ENG_VERSION_LONG_AXIS,{m.long_axis,1,GEO_UNIT_SCALAR}};
    fields[1]=(GeoVersionField){WOOD_ENG_VERSION_MAIN_ALONG,{m.main_along,1,GEO_UNIT_SCALAR}};
    if(m.has_gap)fields[count++]=(GeoVersionField){WOOD_ENG_VERSION_GAP,{m.gap,1,GEO_UNIT_LENGTH}};
    unsigned char key[ENG_ID_MAX+1];GeoVersionDefinition definition=wood_eng_version_definition(1,&m.ref,m.content,fingerprint?fingerprint:m.fingerprint,fields,count,key);
    GeoVersionStatus status=geo_versions_check(w->versions,&definition,NULL);
    if(status!=GEO_VERSION_OK)return wood_eng_version_error(w,1,status);
    GeoVersionView previous;bool exists=geo_versions_find(w->versions,definition.identity,&previous)==GEO_VERSION_OK;
    if(!exists&&w->state->method_count==ENG_METHOD_MAX)return wood_eng_fail(w,"I10: method version capacity exceeded");
    status=geo_versions_put(w->versions,&definition,NULL);if(status!=GEO_VERSION_OK)return wood_eng_version_error(w,1,status);
    if(!exists)w->state->methods[w->state->method_count++]=m;
    return wood_eng_method(w,m.ref.id,m.ref.version)!=NULL||wood_eng_version_error(w,1,GEO_VERSION_INVALID);
}
bool wood_eng_archive(WoodEngineeringContext *w,GeoJson *j,int t)
{
    char kind[16],id[ENG_ID_MAX];uint32_t version;int archived;
    if(!geo_json_keys(j,t,"op,kind,id,version,value","")||!geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind)||
       !geo_json_string(j,geo_json_member(j,t,"id"),id,sizeof id)||!wood_eng_u32(j,geo_json_member(j,t,"version"),&version,true)||
       !geo_json_boolean(j,geo_json_member(j,t,"value"),&archived))return wood_eng_fail(w,"I35: invalid archive operation");
    if(!strcmp(kind,"material")){
        EngMaterialVersion *m=(EngMaterialVersion *)wood_eng_material(w,id,version);if(!m)return wood_eng_fail(w,"I34: material version not found");m->archived=archived!=0;
    }else if(!strcmp(kind,"method")){
        EngMethodVersion *m=(EngMethodVersion *)wood_eng_method(w,id,version);if(!m)return wood_eng_fail(w,"I34: method version not found");m->archived=archived!=0;
    }else return wood_eng_fail(w,"I35: archive kind must be material/method");
    return true;
}
bool wood_eng_application_decode(const void *data,size_t size,EngApplication *out)
{
    if(!data||!out||!size||size>=ENG_RECORD_MAX)return false;
    GeoJson j;bool ok=geo_json_parse_n(&j,data,size);EngApplication a;memset(&a,0,sizeof a);
    char error[256];WoodEngineeringContext context={.error=error,.error_capacity=sizeof error};
    if(ok)ok=geo_json_keys(&j,0,"id,placement_id,method","longAxis,mainAlong,overrides,anchorOptions")&&
        geo_json_string(&j,geo_json_member(&j,0,"id"),a.id,sizeof a.id)&&wood_eng_id(a.id)&&
        wood_eng_u32(&j,geo_json_member(&j,0,"placement_id"),&a.placement_id,false)&&
        wood_eng_ref_parse(&j,geo_json_member(&j,0,"method"),&a.method,false)&&
        wood_eng_axis(&j,geo_json_member(&j,0,"longAxis"),&a.long_axis)&&wood_eng_axis(&j,geo_json_member(&j,0,"mainAlong"),&a.main_along);
    int overrides=ok?geo_json_member(&j,0,"overrides"):-1;
    const char *names[]={"gap","boundary.A","boundary.B","primary.A","primary.B","secondary.A","secondary.B"};
    if(ok&&overrides>=0){ok=geo_json_keys(&j,overrides,"","gap,boundary.A,boundary.B,primary.A,primary.B,secondary.A,secondary.B");
        for(int i=0;i<7&&ok;++i){int v=geo_json_member(&j,overrides,names[i]);if(v<0)continue;a.overridden[i]=true;
            ok=wood_eng_source_parse(&context,&j,v,&a.overrides[i],false)&&a.overrides[i].kind!=ENG_PARAMETER;}}
    int anchors=ok?geo_json_member(&j,0,"anchorOptions"):-1;
    if(ok&&anchors>=0){ok=geo_json_keys(&j,anchors,"","u,v");
        for(int axis=0;axis<2&&ok;++axis){int v=geo_json_member(&j,anchors,axis?"v":"u");if(v<0||geo_json_is_null(&j,v))continue;
            char kind[24],side[8];ok=geo_json_string(&j,geo_json_member(&j,v,"kind"),kind,sizeof kind);if(!ok)break;
            if(!strcmp(kind,"coordinate")){int64_t value;
                ok=geo_json_keys(&j,v,"kind,value","")&&geo_json_integer(&j,geo_json_member(&j,v,"value"),&value)&&geo_coord_in_range(value);
                if(ok){a.anchor_kind[axis]=1;a.anchor[axis]=value;}}
            else if(!strcmp(kind,"edge")){ok=geo_json_keys(&j,v,"kind,side","")&&geo_json_string(&j,geo_json_member(&j,v,"side"),side,sizeof side)&&(!strcmp(side,"min")||!strcmp(side,"max"));
                if(ok)a.anchor_kind[axis]=!strcmp(side,"min")?2:3;}
            else ok=false;}}
    if(ok)ok=geo_json_canonical(&j,0,a.content,sizeof a.content)&&strlen(a.content)==size&&!memcmp(a.content,data,size);
    geo_json_free(&j);if(!ok)return false;*out=a;return true;
}
bool wood_eng_put_application(WoodEngineeringContext *w,GeoJson *j,int t)
{
    EngApplication a={0};
    if (!geo_json_keys(j,t,"id,placement_id,method","longAxis,mainAlong,overrides,anchorOptions") || !geo_json_string(j,geo_json_member(j,t,"id"),a.id,sizeof a.id) || !wood_eng_id(a.id) ||
        !wood_eng_u32(j,geo_json_member(j,t,"placement_id"),&a.placement_id,false) || !w->placement(w->user,a.placement_id,NULL) || !wood_eng_ref_parse(j,geo_json_member(j,t,"method"),&a.method,false) ||
        !wood_eng_method(w,a.method.id,a.method.version) || !wood_eng_axis(j,geo_json_member(j,t,"longAxis"),&a.long_axis) || !wood_eng_axis(j,geo_json_member(j,t,"mainAlong"),&a.main_along)) return wood_eng_fail(w,"D28: application needs an existing placement and fixed method version");
    int overrides=geo_json_member(j,t,"overrides"); const char *names[]={"gap","boundary.A","boundary.B","primary.A","primary.B","secondary.A","secondary.B"};
    bool derived=false; w->placement(w->user,a.placement_id,&derived);
    if(derived)return wood_eng_fail(w,"D4: derived placements cannot receive D28 face applications");
    if (overrides>=0) {
        if (!geo_json_keys(j,overrides,"","gap,boundary.A,boundary.B,primary.A,primary.B,secondary.A,secondary.B")) return wood_eng_fail(w,"D28: unknown face override field");
        for (int i=0;i<7;++i) { int v=geo_json_member(j,overrides,names[i]); if (v<0) continue; a.overridden[i]=true; if (!wood_eng_source_parse(w,j,v,&a.overrides[i],false)) return false; if(a.overrides[i].kind==ENG_PARAMETER)return wood_eng_fail(w,"D28: parameter fields bind object dimensions, not face application overrides"); }
    }
    int anchors=geo_json_member(j,t,"anchorOptions");
    if (anchors>=0) {
        if (!geo_json_keys(j,anchors,"","u,v")) return wood_eng_fail(w,"D28: anchor options accept only u/v");
        for (int axis=0;axis<2;++axis) {
            int v=geo_json_member(j,anchors,axis?"v":"u"); if (v<0||geo_json_is_null(j,v)) continue;
            char kind[24],side[8]; if (!geo_json_string(j,geo_json_member(j,v,"kind"),kind,sizeof kind)) return wood_eng_fail(w,"D28: anchor option needs a kind");
            if (!strcmp(kind,"coordinate")) {
                int64_t value; if (!geo_json_keys(j,v,"kind,value","") || !geo_json_integer(j,geo_json_member(j,v,"value"),&value) || !geo_coord_in_range(value)) return wood_eng_fail(w,"D28: anchor coordinate must be integer mm in D1 range");
                a.anchor_kind[axis]=1; a.anchor[axis]=value;
            } else if (!strcmp(kind,"edge")) {
                if (!geo_json_keys(j,v,"kind,side","") || !geo_json_string(j,geo_json_member(j,v,"side"),side,sizeof side) || (strcmp(side,"min")&&strcmp(side,"max"))) return wood_eng_fail(w,"D28: anchor edge must be min/max");
                a.anchor_kind[axis]=!strcmp(side,"min")?2:3;
            } else return wood_eng_fail(w,"D28: unknown anchor option");
        }
    }
    EngApplication *existing=wood_eng_application_direct(w,a.id);
    if (existing && existing->placement_id!=a.placement_id) return wood_eng_fail(w,"D28: application identity cannot move to another placement");
    for (size_t i=0;i<w->state->application_count;++i) if (&w->state->applications[i]!=existing && w->state->applications[i].placement_id==a.placement_id) return wood_eng_fail(w,"D28: placement already has another application");
    if (!geo_json_canonical(j,t,a.content,sizeof a.content)) return wood_eng_fail(w,"I10: application content exceeds record capacity");
    if (existing) *existing=a;
    else { if (w->state->application_count==ENG_APPLICATION_MAX) return wood_eng_fail(w,"I10: application capacity exceeded"); w->state->applications[w->state->application_count++]=a; }
    return true;
}
bool wood_eng_target_context(const WoodEngineeringContext *w,const EngTarget *t,uint32_t *pid,int *role)
{
    *role=-1;
    WoodEngineeringTargetInfo info={0};
    bool exists=w->target(w->user,t,&info);
    if (!t->kind) {
        if (exists && info.from_system) return wood_eng_fail(w,"D29: edit the grid-system source; engineering bindings are not allowed on its application");
        if (!exists || info.is_subgrid || !info.panel_axis) return wood_eng_fail(w,"I35: dimension target is not an existing PANEL_LAYOUT main-grid axis");
        *pid=info.placement_id;
    } else {
        if (!exists) return wood_eng_fail(w,"I35: dimension target timber does not exist");
        *pid=info.placement_id; *role=info.role;
    }
    return true;
}
bool wood_eng_resolve(WoodEngineeringContext *w,const EngDimensionSource *s,const EngTarget *target,uint32_t pid,int role,GeoCoord *value,char *path,size_t cap)
{
    if(w->resolve_source)return w->resolve_source(w->sources,s,target,pid,role,value,path,cap);
    return wood_eng_resolve_direct(w,s,target,pid,role,value,path,cap);
}
bool wood_eng_resolve_direct(WoodEngineeringContext *w,const EngDimensionSource *s,const EngTarget *target,uint32_t pid,int role,GeoCoord *value,char *path,size_t cap)
{
    if (s->kind==ENG_LITERAL) { *value=s->value; if (path) snprintf(path,cap,"explicit integer mm"); }
    else if (s->kind==ENG_SPEC) {
        bool found=w->source_named?w->source_named(w->sources,s->ref,value):w->named_value(w->user,s->ref,value);
        if (!found) return wood_eng_fail(w,"I35: named dimension spec is missing");
        if (path) snprintf(path,cap,"spec:%s",s->ref);
    } else if (s->kind==ENG_PARAMETER) {
        bool found=w->source_parameter?w->source_parameter(w->sources,s->parameter,value,w->error,w->error_capacity):w->parameter(w->user,s->parameter,value,w->error,w->error_capacity);
        if(!found)return false;
        if(path)snprintf(path,cap,"param:%u:%u",s->parameter.parameter_id,s->parameter.field_id);
    } else if (s->kind==ENG_MATERIAL) {
        const EngMaterialVersion *m=wood_eng_material(w,s->ref,s->version);
        if (!m) return wood_eng_fail(w,"I34: fixed material version is missing");
        if(w->depend_definition&&!w->depend_definition(w->sources,0,s->ref,s->version))return false;
        if (!target->kind) {
            if (target->field || m->kind || (s->field!=ENG_WIDTH&&s->field!=ENG_LENGTH)) return wood_eng_fail(w,"I35: grid panel accepts only panel material width/length; gap is separately explicit");
            *value=s->field==ENG_WIDTH?m->width:m->length;
        } else {
            if (!m->kind || s->field!=(target->field?ENG_B:ENG_A)) return wood_eng_fail(w,"I35: timber dimension requires matching timber material A/B field");
            *value=target->field?m->b:m->a;
        }
        if(w->source_version_field&&!w->source_version_field(w->sources,0,&m->ref,(uint32_t)s->field,value))return false;
        if (path) snprintf(path,cap,"material:%s@%u.%s",s->ref,s->version,ENG_FIELDS[s->field]);
    } else if (s->kind==ENG_APPLICATION) {
        EngApplication *a=wood_eng_application(w,s->ref);
        const EngMethodVersion *m=a?wood_eng_method(w,a->method.id,a->method.version):NULL;
        if (!a||!m || (pid!=UINT32_MAX && a->placement_id!=pid)) return wood_eng_fail(w,"I35: application source is missing or belongs to another placement");
        if(w->depend_definition&&(!w->depend_definition(w->sources,2,a->id,0)||
            !w->depend_definition(w->sources,1,a->method.id,a->method.version)))return false;
        EngDimensionSource nested={0}; int override=-1;
        if (!target->kind) {
            int field=target->field?(target->axis?ENG_V_GAP:ENG_U_GAP):(target->axis?ENG_V_PANEL:ENG_U_PANEL);
            if (s->field!=field) return wood_eng_fail(w,"I35: application field does not match target grid axis/field");
            if (target->field) { override=0; if (!a->overridden[0] && !m->has_gap) return wood_eng_fail(w,"I35: gap is not set; enter an explicit gap"); nested.value=m->gap;
                if(!a->overridden[0]&&w->source_version_field&&!w->source_version_field(w->sources,1,&m->ref,WOOD_ENG_VERSION_GAP,&nested.value))return false; }
            else {
                int axis=a->long_axis?a->long_axis:m->long_axis;
                if (!axis || !m->panel.id[0]) return wood_eng_fail(w,"I35: panel material or length-axis mapping is not set");
                nested.kind=ENG_MATERIAL; nested.version=m->panel.version; snprintf(nested.ref,sizeof nested.ref,"%s",m->panel.id);
                nested.field=axis==target->axis+1?ENG_LENGTH:ENG_WIDTH;
            }
        } else {
            int r=(s->field-ENG_BOUNDARY_A)/2;
            if (s->field<ENG_BOUNDARY_A || s->field>ENG_SECONDARY_B || (s->field-ENG_BOUNDARY_A)%2!=target->field || role!=r) return wood_eng_fail(w,"D28: timber role does not match the explicitly bound application slot");
            override=1+r*2+target->field;
            if (!a->overridden[override] && !m->roles[r].id[0]) return wood_eng_fail(w,"I35: selected timber material slot is not set");
            nested.kind=ENG_MATERIAL; nested.version=m->roles[r].version; snprintf(nested.ref,sizeof nested.ref,"%s",m->roles[r].id); nested.field=target->field?ENG_B:ENG_A;
        }
        if (override>=0 && a->overridden[override]) nested=a->overrides[override];
        char tail[192]; if (!wood_eng_resolve(w,&nested,target,pid,role,value,tail,sizeof tail)) return false;
        if (path) snprintf(path,cap,"application:%s -> method:%s@%u -> %s%s",a->id,a->method.id,a->method.version,override>=0&&a->overridden[override]?"face override -> ":"",tail);
    } else return wood_eng_fail(w,"I35: invalid dimension source kind");
    if (*value<((!target->kind&&target->field)?0:1) || *value>GEO_COORD_LIMIT) return wood_eng_fail(w,"I35: effective dimension violates its positive/nonnegative integer mm range");
    return true;
}
bool wood_eng_effective(WoodEngineeringContext *w,const EngBinding *b,GeoCoord *value,char *path,size_t cap)
{
    if(w->resolve_binding)return w->resolve_binding(w->sources,b,value,path,cap);
    return wood_eng_effective_direct(w,b,value,path,cap);
}
bool wood_eng_effective_direct(WoodEngineeringContext *w,const EngBinding *b,GeoCoord *value,char *path,size_t cap)
{
    uint32_t pid; int role; if (!wood_eng_target_context(w,&b->target,&pid,&role)) return false;
    /* During scene replay a timber declaration precedes its placement. Its role
     * is already known; final revalidation after place checks the actual face. */
    if (b->target.kind) { WoodEngineeringTargetInfo info={0}; w->target(w->user,&b->target,&info); if (!info.placed) pid=UINT32_MAX; }
    /* An override changes value, not binding identity: the base application must
     * still exist, be on the same face and bind the same role. */
    if (b->has_override && b->source.kind==ENG_APPLICATION) {
        EngApplication *a=wood_eng_application(w,b->source.ref);
        if (!a || (pid!=UINT32_MAX && a->placement_id!=pid)) return wood_eng_fail(w,"I35: overridden application source is missing or on another placement");
        if(w->depend_definition&&!w->depend_definition(w->sources,2,a->id,0))return false;
        int expected=b->target.kind?ENG_BOUNDARY_A+role*2+b->target.field:(b->target.field?ENG_U_GAP:ENG_U_PANEL)+b->target.axis;
        if (role==3 || b->source.field!=expected) return wood_eng_fail(w,"D28: overridden source still requires a matching application field/role");
    }
    if (b->has_override && b->source.kind!=ENG_APPLICATION) {
        GeoCoord ignored;
        if (!wood_eng_resolve(w,&b->source,&b->target,pid,role,&ignored,NULL,0)) return false;
    }
    return wood_eng_resolve(w,b->has_override?&b->override_value:&b->source,&b->target,pid,role,value,path,cap);
}
/* D28: these records belong to the deleted identity. This is deliberately not
 * a general orphan collector: malformed loaded references must still fail I35. */
void wood_engineering_drop_owned(WoodEngineeringContext *w,const char *kind,uint32_t id)
{
    EngineeringState *e=w->state;
    if (!strcmp(kind,"grid") || !strcmp(kind,"timber")) {
        size_t kept=0; int target_kind=!strcmp(kind,"timber");
        for (size_t i=0;i<e->binding_count;++i)
            if (e->bindings[i].target.kind!=target_kind || e->bindings[i].target.id!=id) e->bindings[kept++]=e->bindings[i];
        memset(e->bindings+kept,0,(e->binding_count-kept)*sizeof e->bindings[0]);
        e->binding_count=kept;
    } else if (!strcmp(kind,"placement")) {
        size_t kept=0;
        for (size_t i=0;i<e->application_count;++i)
            if (e->applications[i].placement_id!=id) e->applications[kept++]=e->applications[i];
        memset(e->applications+kept,0,(e->application_count-kept)*sizeof e->applications[0]);
        e->application_count=kept;
    }
}
/* R13: preserve the application identity when every attached dimension moves
 * to the same fragment. A split across faces has no implicit cloning rule. */
bool wood_engineering_follow_fragment(WoodEngineeringContext *w,uint32_t old_pid)
{
    for (size_t i=0;i<w->state->application_count;++i) {
        EngApplication *a=&w->state->applications[i];
        if (a->placement_id!=old_pid) continue;
        bool found=false; uint32_t destination=old_pid;
        for (size_t j=0;j<w->state->binding_count;++j) {
            const EngBinding *b=&w->state->bindings[j];
            if (b->source.kind!=ENG_APPLICATION || strcmp(b->source.ref,a->id)) continue;
            uint32_t pid; int role;
            if (!wood_eng_target_context(w,&b->target,&pid,&role)) return false;
            if (found && destination!=pid) return wood_eng_fail(w,"R13/I35: one application would span both fragments; separate its explicit bindings before splitting");
            destination=pid; found=true;
        }
        if (!found || destination==old_pid) continue;
        GeoJson json;
        if (!geo_json_parse(&json,a->content)) { geo_json_free(&json); return wood_eng_fail(w,"I35: invalid stored application definition"); }
        const char *keys[]={"anchorOptions","id","longAxis","mainAlong","method","overrides","placement_id"};
        char content[ENG_RECORD_MAX],value[ENG_RECORD_MAX]; size_t used=0; bool valid=true;
        content[used++]='{';
        for (size_t k=0;k<sizeof keys/sizeof keys[0] && valid;++k) {
            int token=geo_json_member(&json,0,keys[k]);
            if (token<0) continue;
            if (!strcmp(keys[k],"placement_id")) snprintf(value,sizeof value,"%u",destination);
            else if (!geo_json_canonical(&json,token,value,sizeof value)) { valid=false; break; }
            int n=snprintf(content+used,sizeof content-used,"%s\"%s\":%s",used>1?",":"",keys[k],value);
            if (n<0 || (size_t)n>=sizeof content-used) valid=false; else used+=(size_t)n;
        }
        if (valid && used+2<=sizeof content) { content[used++]='}'; content[used]=0; }
        else valid=false;
        geo_json_free(&json);
        if (!valid) return wood_eng_fail(w,"I10: moved application exceeds record capacity");
        a->placement_id=destination; snprintf(a->content,sizeof a->content,"%s",content);
    }
    return true;
}
bool wood_eng_validate_application_direct(WoodEngineeringContext *w,const EngApplication *a)
{
        bool derived=false; bool exists=w->placement(w->user,a->placement_id,&derived);
        if(exists&&derived)return wood_eng_fail(w,"D4: derived placements cannot receive D28 face applications");
        if (!exists || !wood_eng_method(w,a->method.id,a->method.version)) return wood_eng_fail(w,"I35: application has a dangling placement/method reference");
        if(w->depend_definition&&!w->depend_definition(w->sources,1,a->method.id,a->method.version))return false;
        for (int field=0;field<7;++field) if (a->overridden[field]) {
            EngTarget target={0}; GeoCoord ignored; int role=-1;
            if (!field) target.field=1;
            else { target.kind=1; target.field=(field-1)%2; role=(field-1)/2; }
            if (!wood_eng_resolve(w,&a->overrides[field],&target,a->placement_id,role,&ignored,NULL,0)) return false;
        }
    return true;
}
bool wood_engineering_rebuild(WoodEngineeringContext *w,char *error,size_t cap)
{
    for (size_t i=0;i<w->state->application_count;++i) {
        const EngApplication *a=&w->state->applications[i];
        if(w->validate_application?!w->validate_application(w->sources,a):!wood_eng_validate_application_direct(w,a))goto fail;
    }
    for (size_t i=0;i<w->state->binding_count;++i) {
        const EngBinding *b=&w->state->bindings[i]; GeoCoord value;
        if (!wood_eng_effective(w,b,&value,NULL,0)) goto fail;
        if (!b->target.kind) { WoodEngineeringTargetInfo info={0}; w->target(w->user,&b->target,&info); if (info.from_system) { wood_eng_fail(w,"D29: grid-system applications cannot have engineering bindings"); goto fail; } }
        w->write_dimension(w->user,&b->target,value);
    }
    if (!w->serializable(w->user,w->error,w->error_capacity)) goto fail;
    return true;
fail:
    snprintf(error,cap,"%s",w->error); return false;
}
