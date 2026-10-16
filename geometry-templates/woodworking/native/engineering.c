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
const EngMaterialVersion *wood_eng_material(const WoodEngineeringContext *w,const char *id,uint32_t version)
{
    for (size_t i=0;i<w->state->material_count;++i) if (w->state->materials[i].ref.version==version && !strcmp(w->state->materials[i].ref.id,id)) return &w->state->materials[i];
    return NULL;
}
const EngMethodVersion *wood_eng_method(const WoodEngineeringContext *w,const char *id,uint32_t version)
{
    for (size_t i=0;i<w->state->method_count;++i) if (w->state->methods[i].ref.version==version && !strcmp(w->state->methods[i].ref.id,id)) return &w->state->methods[i];
    return NULL;
}
EngApplication *wood_eng_application(WoodEngineeringContext *w,const char *id)
{
    for (size_t i=0;i<w->state->application_count;++i) if (!strcmp(w->state->applications[i].id,id)) return &w->state->applications[i];
    return NULL;
}
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

bool wood_eng_publish_material(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint)
{
    EngMaterialVersion m={0}; char kind[16],name[192],thickness[ENG_THICKNESS_CAPACITY];
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
        }
    }
    if (!geo_json_canonical(j,t,m.content,sizeof m.content)) return wood_eng_fail(w,"I10: material content exceeds record capacity");
    geo_sha256(m.content,strlen(m.content),m.fingerprint);
    if (fingerprint && strcmp(fingerprint,m.fingerprint)) return wood_eng_fail(w,"I34: material fingerprint mismatch");
    const EngMaterialVersion *old=wood_eng_material(w,m.ref.id,m.ref.version);
    if (old) return !strcmp(old->content,m.content) || wood_eng_fail(w,"I34: material ID/version already has different immutable content");
    if (w->state->material_count==ENG_MATERIAL_MAX) return wood_eng_fail(w,"I10: material version capacity exceeded");
    w->state->materials[w->state->material_count++]=m; return true;
}
bool wood_eng_publish_method(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint)
{
    EngMethodVersion m={0}; char name[192];
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
    if (fingerprint && strcmp(fingerprint,m.fingerprint)) return wood_eng_fail(w,"I34: method fingerprint mismatch");
    const EngMethodVersion *old=wood_eng_method(w,m.ref.id,m.ref.version);
    if (old) return !strcmp(old->content,m.content) || wood_eng_fail(w,"I34: method ID/version already has different immutable content");
    if (w->state->method_count==ENG_METHOD_MAX) return wood_eng_fail(w,"I10: method version capacity exceeded");
    w->state->methods[w->state->method_count++]=m; return true;
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
    EngApplication *existing=wood_eng_application(w,a.id);
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
    if (s->kind==ENG_LITERAL) { *value=s->value; if (path) snprintf(path,cap,"explicit integer mm"); }
    else if (s->kind==ENG_SPEC) {
        if (!w->named_value(w->user,s->ref,value)) return wood_eng_fail(w,"I35: named dimension spec is missing");
        if (path) snprintf(path,cap,"spec:%s",s->ref);
    } else if (s->kind==ENG_PARAMETER) {
        if(!w->parameter(w->user,s->parameter,value,w->error,w->error_capacity))return false;
        if(path)snprintf(path,cap,"param:%u:%u",s->parameter.parameter_id,s->parameter.field_id);
    } else if (s->kind==ENG_MATERIAL) {
        const EngMaterialVersion *m=wood_eng_material(w,s->ref,s->version);
        if (!m) return wood_eng_fail(w,"I34: fixed material version is missing");
        if (!target->kind) {
            if (target->field || m->kind || (s->field!=ENG_WIDTH&&s->field!=ENG_LENGTH)) return wood_eng_fail(w,"I35: grid panel accepts only panel material width/length; gap is separately explicit");
            *value=s->field==ENG_WIDTH?m->width:m->length;
        } else {
            if (!m->kind || s->field!=(target->field?ENG_B:ENG_A)) return wood_eng_fail(w,"I35: timber dimension requires matching timber material A/B field");
            *value=target->field?m->b:m->a;
        }
        if (path) snprintf(path,cap,"material:%s@%u.%s",s->ref,s->version,ENG_FIELDS[s->field]);
    } else if (s->kind==ENG_APPLICATION) {
        EngApplication *a=wood_eng_application(w,s->ref);
        const EngMethodVersion *m=a?wood_eng_method(w,a->method.id,a->method.version):NULL;
        if (!a||!m || (pid!=UINT32_MAX && a->placement_id!=pid)) return wood_eng_fail(w,"I35: application source is missing or belongs to another placement");
        EngDimensionSource nested={0}; int override=-1;
        if (!target->kind) {
            int field=target->field?(target->axis?ENG_V_GAP:ENG_U_GAP):(target->axis?ENG_V_PANEL:ENG_U_PANEL);
            if (s->field!=field) return wood_eng_fail(w,"I35: application field does not match target grid axis/field");
            if (target->field) { override=0; if (!a->overridden[0] && !m->has_gap) return wood_eng_fail(w,"I35: gap is not set; enter an explicit gap"); nested.value=m->gap; }
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
    uint32_t pid; int role; if (!wood_eng_target_context(w,&b->target,&pid,&role)) return false;
    /* During scene replay a timber declaration precedes its placement. Its role
     * is already known; final revalidation after place checks the actual face. */
    if (b->target.kind) { WoodEngineeringTargetInfo info={0}; w->target(w->user,&b->target,&info); if (!info.placed) pid=UINT32_MAX; }
    /* An override changes value, not binding identity: the base application must
     * still exist, be on the same face and bind the same role. */
    if (b->has_override && b->source.kind==ENG_APPLICATION) {
        EngApplication *a=wood_eng_application(w,b->source.ref);
        if (!a || (pid!=UINT32_MAX && a->placement_id!=pid)) return wood_eng_fail(w,"I35: overridden application source is missing or on another placement");
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
bool wood_engineering_rebuild(WoodEngineeringContext *w,char *error,size_t cap)
{
    for (size_t i=0;i<w->state->application_count;++i) {
        const EngApplication *a=&w->state->applications[i];
        bool derived=false; bool exists=w->placement(w->user,a->placement_id,&derived);
        if(exists&&derived){wood_eng_fail(w,"D4: derived placements cannot receive D28 face applications");goto fail;}
        if (!exists || !wood_eng_method(w,a->method.id,a->method.version)) { wood_eng_fail(w,"I35: application has a dangling placement/method reference"); goto fail; }
        for (int field=0;field<7;++field) if (a->overridden[field]) {
            EngTarget target={0}; GeoCoord ignored; int role=-1;
            if (!field) target.field=1;
            else { target.kind=1; target.field=(field-1)%2; role=(field-1)/2; }
            if (!wood_eng_resolve(w,&a->overrides[field],&target,a->placement_id,role,&ignored,NULL,0)) goto fail;
        }
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
