/* engineering-spec/1: definitions and evaluation shared by every C entry point. */
#include "engineering_json.inc"
#include <stdarg.h>
static bool engineering_serializable(const World *w);
static char g_engineering_error[256];
static bool eng_fail(const char *text) { snprintf(g_engineering_error,sizeof g_engineering_error,"%s",text); utf8_trim_tail(g_engineering_error); return false; }
static bool eng_id(const char *s)
{
    size_t n=strlen(s); if (!n || n>=ENG_ID_MAX) return false;
    for (size_t i=0;i<n;++i) if (!((s[i]>='a'&&s[i]<='z')||(s[i]>='A'&&s[i]<='Z')||(s[i]>='0'&&s[i]<='9')||s[i]=='_'||s[i]=='-')) return false;
    return true;
}
static bool eng_u32(const EngJson *j,int t,uint32_t *out,bool positive)
{
    int64_t n; if (!eng_json_integer(j,t,&n) || n<(positive?1:0) || (uint64_t)n>UINT32_MAX) return false;
    *out=(uint32_t)n; return true;
}
static bool eng_coord(const EngJson *j,int t,Coord *out,bool positive)
{
    int64_t n; if (!eng_json_integer(j,t,&n) || n<(positive?1:0) || n>COORD_LIMIT) return false;
    *out=n; return true;
}
static bool eng_optional_text(const EngJson *j,int obj,const char *key)
{
    int t=eng_json_member(j,obj,key); char text[ENG_RECORD_MAX];
    return t<0 || eng_json_is_null(j,t) || eng_json_string(j,t,text,sizeof text);
}
static bool eng_ref_parse(EngJson *j,int t,EngVersionRef *r,bool optional)
{
    memset(r,0,sizeof *r);
    if (optional && (t<0 || eng_json_is_null(j,t))) return true;
    return eng_json_keys(j,t,"id,version","") && eng_json_string(j,eng_json_member(j,t,"id"),r->id,sizeof r->id) && eng_id(r->id) && eng_u32(j,eng_json_member(j,t,"version"),&r->version,true);
}
static bool eng_axis(const EngJson *j,int t,int *axis)
{
    *axis=0; if (t<0 || eng_json_is_null(j,t)) return true;
    char value[8]; if (!eng_json_string(j,t,value,sizeof value)) return false;
    if (!strcmp(value,"u")) *axis=1; else if (!strcmp(value,"v")) *axis=2; else return false;
    return true;
}
static const EngMaterialVersion *eng_material(const World *w,const char *id,uint32_t version)
{
    for (size_t i=0;i<w->engineering.material_count;++i) if (w->engineering.materials[i].ref.version==version && !strcmp(w->engineering.materials[i].ref.id,id)) return &w->engineering.materials[i];
    return NULL;
}
static const EngMethodVersion *eng_method(const World *w,const char *id,uint32_t version)
{
    for (size_t i=0;i<w->engineering.method_count;++i) if (w->engineering.methods[i].ref.version==version && !strcmp(w->engineering.methods[i].ref.id,id)) return &w->engineering.methods[i];
    return NULL;
}
static EngApplication *eng_application(World *w,const char *id)
{
    for (size_t i=0;i<w->engineering.application_count;++i) if (!strcmp(w->engineering.applications[i].id,id)) return &w->engineering.applications[i];
    return NULL;
}
static const char *const ENG_FIELDS[]={"width","length","A","B","u.panel","v.panel","u.gap","v.gap","boundary.A","boundary.B","primary.A","primary.B","secondary.A","secondary.B"};
static bool eng_source_parse(EngJson *j,int t,EngDimensionSource *s,bool allow_app)
{
    memset(s,0,sizeof *s); char kind[24],field[32];
    if (!eng_json_string(j,eng_json_member(j,t,"kind"),kind,sizeof kind)) return eng_fail("I35: dimension source needs a kind");
    if (!strcmp(kind,"literal")) {
        s->kind=ENG_LITERAL;
        if (!eng_json_keys(j,t,"kind,value","") || !eng_coord(j,eng_json_member(j,t,"value"),&s->value,false)) return eng_fail("I35: literal dimension must be integer mm in D1 range");
    } else if (!strcmp(kind,"spec")) {
        s->kind=ENG_SPEC;
        if (!eng_json_keys(j,t,"kind,name","") || !eng_json_string(j,eng_json_member(j,t,"name"),s->ref,sizeof s->ref) || !reference_name(s->ref)) return eng_fail("I35: invalid named-spec dimension source");
    } else if (!strcmp(kind,"parameter")) {
        s->kind=ENG_PARAMETER;s->parameter.set=true;
        if(!eng_json_keys(j,t,"kind,parameterId,fieldId","")||!parameter_u32(j,eng_json_member(j,t,"parameterId"),&s->parameter.parameter_id)||!parameter_u32(j,eng_json_member(j,t,"fieldId"),&s->parameter.field_id))return eng_fail("I38: invalid parameter dimension source");
    } else if (!strcmp(kind,"material") || !strcmp(kind,"application")) {
        s->kind=!strcmp(kind,"material")?ENG_MATERIAL:ENG_APPLICATION;
        if (s->kind==ENG_APPLICATION && !allow_app) return eng_fail("I35: application override cannot refer to another application");
        if (!eng_json_keys(j,t,s->kind==ENG_MATERIAL?"kind,id,version,field":"kind,id,field","") ||
            !eng_json_string(j,eng_json_member(j,t,"id"),s->ref,sizeof s->ref) || !eng_id(s->ref) ||
            (s->kind==ENG_MATERIAL && !eng_u32(j,eng_json_member(j,t,"version"),&s->version,true)) ||
            !eng_json_string(j,eng_json_member(j,t,"field"),field,sizeof field)) return eng_fail("I35: incomplete material/application dimension source");
        int f=0; while (f<14 && strcmp(field,ENG_FIELDS[f])) ++f;
        if (f==14 || (s->kind==ENG_MATERIAL && f>ENG_B) || (s->kind==ENG_APPLICATION && f<ENG_U_PANEL)) return eng_fail("I35: unsupported source field");
        s->field=f;
    } else return eng_fail("I35: unsupported dimension source kind");
    return true;
}
static bool eng_target_parse(EngJson *j,int t,EngTarget *target)
{
    memset(target,0,sizeof *target); char kind[16],field[16],axis[8];
    if (!eng_json_string(j,eng_json_member(j,t,"kind"),kind,sizeof kind) || !eng_u32(j,eng_json_member(j,t,"id"),&target->id,false) || !eng_json_string(j,eng_json_member(j,t,"field"),field,sizeof field)) return eng_fail("I35: invalid dimension target");
    if (!strcmp(kind,"grid")) {
        if (!eng_json_keys(j,t,"kind,id,axis,field","") || !eng_json_string(j,eng_json_member(j,t,"axis"),axis,sizeof axis) || (strcmp(axis,"u")&&strcmp(axis,"v")) || (strcmp(field,"panel")&&strcmp(field,"gap"))) return eng_fail("I35: grid target requires u/v and panel/gap");
        target->axis=!strcmp(axis,"v"); target->field=!strcmp(field,"gap");
    } else if (!strcmp(kind,"timber")) {
        if (!eng_json_keys(j,t,"kind,id,field","") || (strcmp(field,"A")&&strcmp(field,"B"))) return eng_fail("I35: timber target requires A/B");
        target->kind=1; target->field=!strcmp(field,"B");
    } else return eng_fail("I35: unsupported target kind");
    return true;
}
static bool eng_same_target(const EngTarget *a,const EngTarget *b) { return a->kind==b->kind && a->id==b->id && a->axis==b->axis && a->field==b->field; }
static EngBinding *eng_binding(World *w,const EngTarget *target)
{
    for (size_t i=0;i<w->engineering.binding_count;++i) if (eng_same_target(target,&w->engineering.bindings[i].target)) return &w->engineering.bindings[i];
    return NULL;
}
static bool eng_bind(World *w,const EngTarget *target,const EngDimensionSource *source)
{
    if(target->kind&&assembly_owned(w,target->id))return eng_fail("I42: owned timber dimensions come from its assembly binding");
    EngBinding *b=eng_binding(w,target);
    if (!b) {
        if (w->engineering.binding_count==ENG_BINDING_MAX) return eng_fail("I10: engineering dimension binding capacity exceeded");
        b=&w->engineering.bindings[w->engineering.binding_count++]; memset(b,0,sizeof *b); b->target=*target;
    }
    b->source=*source; return true;
}
static bool eng_object_bound(const World *w,int kind,uint32_t id)
{
    for (size_t i=0;i<w->engineering.binding_count;++i) if (w->engineering.bindings[i].target.kind==kind && w->engineering.bindings[i].target.id==id) return true;
    return false;
}
static bool engineering_used(const World *w) { return w->engineering.material_count || w->engineering.method_count || w->engineering.application_count || w->engineering.binding_count; }

static bool eng_publish_material(World *w,EngJson *j,int t,const char *fingerprint)
{
    EngMaterialVersion m={0}; char kind[16],name[192],thickness[ENG_THICKNESS_CAPACITY];
    if (!eng_json_string(j,eng_json_member(j,t,"kind"),kind,sizeof kind)) return eng_fail("D26: material kind is required");
    m.kind=!strcmp(kind,"timber");
    if ((!m.kind && strcmp(kind,"panel")) || !eng_json_keys(j,t,m.kind?"id,version,kind,name,A,B":"id,version,kind,name,width,length",m.kind?"brand,model,notes":"thickness,brand,model,notes") ||
        !eng_json_string(j,eng_json_member(j,t,"id"),m.ref.id,sizeof m.ref.id) || !eng_id(m.ref.id) ||
        !eng_u32(j,eng_json_member(j,t,"version"),&m.ref.version,true) || !eng_json_string(j,eng_json_member(j,t,"name"),name,sizeof name) || !name[0] ||
        !eng_optional_text(j,t,"brand") || !eng_optional_text(j,t,"model") || !eng_optional_text(j,t,"notes")) return eng_fail("D26: invalid material identity, name or fields");
    if (m.kind) {
        if (!eng_coord(j,eng_json_member(j,t,"A"),&m.a,true) || !eng_coord(j,eng_json_member(j,t,"B"),&m.b,true)) return eng_fail("D26: timber A/B must be positive integer mm");
    } else {
        if (!eng_coord(j,eng_json_member(j,t,"width"),&m.width,true) || !eng_coord(j,eng_json_member(j,t,"length"),&m.length,true)) return eng_fail("D26: panel width/length must be positive integer mm");
        int k=eng_json_member(j,t,"thickness");
        if (k>=0 && !eng_json_is_null(j,k)) {
            if (!eng_json_string(j,k,thickness,sizeof thickness) || !thickness[0]) return eng_fail("D26: thickness must be a positive decimal string or null");
            bool dot=false,positive=false; size_t n=strlen(thickness);
            for (size_t i=0;i<n;++i) { if (thickness[i]=='.' && !dot && i>0 && i+1<n) dot=true; else if (thickness[i]>='0'&&thickness[i]<='9') positive|=thickness[i]!='0'; else return eng_fail("D26: invalid decimal thickness"); }
            if (!positive) return eng_fail("D26: thickness must be positive");
        }
    }
    if (!eng_json_canonical(j,t,m.content,sizeof m.content)) return eng_fail("I10: material content exceeds record capacity");
    eng_sha256(m.content,strlen(m.content),m.fingerprint);
    if (fingerprint && strcmp(fingerprint,m.fingerprint)) return eng_fail("I34: material fingerprint mismatch");
    const EngMaterialVersion *old=eng_material(w,m.ref.id,m.ref.version);
    if (old) return !strcmp(old->content,m.content) || eng_fail("I34: material ID/version already has different immutable content");
    if (w->engineering.material_count==ENG_MATERIAL_MAX) return eng_fail("I10: material version capacity exceeded");
    w->engineering.materials[w->engineering.material_count++]=m; return true;
}
static bool eng_publish_method(World *w,EngJson *j,int t,const char *fingerprint)
{
    EngMethodVersion m={0}; char name[192];
    if (!eng_json_keys(j,t,"id,version,name","panel,roles,gap,longAxis,mainAlong,notes") || !eng_json_string(j,eng_json_member(j,t,"id"),m.ref.id,sizeof m.ref.id) || !eng_id(m.ref.id) ||
        !eng_u32(j,eng_json_member(j,t,"version"),&m.ref.version,true) || !eng_json_string(j,eng_json_member(j,t,"name"),name,sizeof name) || !name[0] || !eng_optional_text(j,t,"notes") ||
        !eng_ref_parse(j,eng_json_member(j,t,"panel"),&m.panel,true) || !eng_axis(j,eng_json_member(j,t,"longAxis"),&m.long_axis) || !eng_axis(j,eng_json_member(j,t,"mainAlong"),&m.main_along)) return eng_fail("D27: invalid method identity or settings");
    int roles=eng_json_member(j,t,"roles"); const char *names[]={"boundary","primary","secondary"};
    if (roles>=0 && !eng_json_is_null(j,roles)) {
        if (!eng_json_keys(j,roles,"","boundary,primary,secondary")) return eng_fail("D27: method has an unknown role slot");
        for (int r=0;r<3;++r) if (!eng_ref_parse(j,eng_json_member(j,roles,names[r]),&m.roles[r],true)) return eng_fail("D27: invalid role material reference");
    }
    int gap=eng_json_member(j,t,"gap"); m.has_gap=gap>=0&&!eng_json_is_null(j,gap);
    if (m.has_gap && !eng_coord(j,gap,&m.gap,false)) return eng_fail("D27: gap must be explicit nonnegative integer mm");
    for (int r=-1;r<3;++r) {
        const EngVersionRef *ref=r<0?&m.panel:&m.roles[r]; if (!ref->id[0]) continue;
        const EngMaterialVersion *mat=eng_material(w,ref->id,ref->version);
        if (!mat || mat->kind!=(r<0?0:1)) return eng_fail("I34: method material version is missing or has incompatible kind");
    }
    if (!eng_json_canonical(j,t,m.content,sizeof m.content)) return eng_fail("I10: method content exceeds record capacity");
    eng_sha256(m.content,strlen(m.content),m.fingerprint);
    if (fingerprint && strcmp(fingerprint,m.fingerprint)) return eng_fail("I34: method fingerprint mismatch");
    const EngMethodVersion *old=eng_method(w,m.ref.id,m.ref.version);
    if (old) return !strcmp(old->content,m.content) || eng_fail("I34: method ID/version already has different immutable content");
    if (w->engineering.method_count==ENG_METHOD_MAX) return eng_fail("I10: method version capacity exceeded");
    w->engineering.methods[w->engineering.method_count++]=m; return true;
}
static bool eng_put_application(World *w,EngJson *j,int t)
{
    EngApplication a={0};
    if (!eng_json_keys(j,t,"id,placement_id,method","longAxis,mainAlong,overrides,anchorOptions") || !eng_json_string(j,eng_json_member(j,t,"id"),a.id,sizeof a.id) || !eng_id(a.id) ||
        !eng_u32(j,eng_json_member(j,t,"placement_id"),&a.placement_id,false) || !world_find_placement(w,a.placement_id) || !eng_ref_parse(j,eng_json_member(j,t,"method"),&a.method,false) ||
        !eng_method(w,a.method.id,a.method.version) || !eng_axis(j,eng_json_member(j,t,"longAxis"),&a.long_axis) || !eng_axis(j,eng_json_member(j,t,"mainAlong"),&a.main_along)) return eng_fail("D28: application needs an existing placement and fixed method version");
    int overrides=eng_json_member(j,t,"overrides"); const char *names[]={"gap","boundary.A","boundary.B","primary.A","primary.B","secondary.A","secondary.B"};
    if(world_find_placement(w,a.placement_id)->derived_fill_id)return eng_fail("D4: derived placements cannot receive D28 face applications");
    if (overrides>=0) {
        if (!eng_json_keys(j,overrides,"","gap,boundary.A,boundary.B,primary.A,primary.B,secondary.A,secondary.B")) return eng_fail("D28: unknown face override field");
        for (int i=0;i<7;++i) { int v=eng_json_member(j,overrides,names[i]); if (v<0) continue; a.overridden[i]=true; if (!eng_source_parse(j,v,&a.overrides[i],false)) return false; if(a.overrides[i].kind==ENG_PARAMETER)return eng_fail("D28: parameter fields bind object dimensions, not face application overrides"); }
    }
    int anchors=eng_json_member(j,t,"anchorOptions");
    if (anchors>=0) {
        if (!eng_json_keys(j,anchors,"","u,v")) return eng_fail("D28: anchor options accept only u/v");
        for (int axis=0;axis<2;++axis) {
            int v=eng_json_member(j,anchors,axis?"v":"u"); if (v<0||eng_json_is_null(j,v)) continue;
            char kind[24],side[8]; if (!eng_json_string(j,eng_json_member(j,v,"kind"),kind,sizeof kind)) return eng_fail("D28: anchor option needs a kind");
            if (!strcmp(kind,"coordinate")) {
                int64_t value; if (!eng_json_keys(j,v,"kind,value","") || !eng_json_integer(j,eng_json_member(j,v,"value"),&value) || !coord_in_range(value)) return eng_fail("D28: anchor coordinate must be integer mm in D1 range");
                a.anchor_kind[axis]=1; a.anchor[axis]=value;
            } else if (!strcmp(kind,"edge")) {
                if (!eng_json_keys(j,v,"kind,side","") || !eng_json_string(j,eng_json_member(j,v,"side"),side,sizeof side) || (strcmp(side,"min")&&strcmp(side,"max"))) return eng_fail("D28: anchor edge must be min/max");
                a.anchor_kind[axis]=!strcmp(side,"min")?2:3;
            } else return eng_fail("D28: unknown anchor option");
        }
    }
    EngApplication *existing=eng_application(w,a.id);
    if (existing && existing->placement_id!=a.placement_id) return eng_fail("D28: application identity cannot move to another placement");
    for (size_t i=0;i<w->engineering.application_count;++i) if (&w->engineering.applications[i]!=existing && w->engineering.applications[i].placement_id==a.placement_id) return eng_fail("D28: placement already has another application");
    if (!eng_json_canonical(j,t,a.content,sizeof a.content)) return eng_fail("I10: application content exceeds record capacity");
    if (existing) *existing=a;
    else { if (w->engineering.application_count==ENG_APPLICATION_MAX) return eng_fail("I10: application capacity exceeded"); w->engineering.applications[w->engineering.application_count++]=a; }
    return true;
}
static bool eng_target_context(const World *w,const EngTarget *t,uint32_t *pid,int *role)
{
    *role=-1;
    if (!t->kind) {
        const ReferenceGrid *g=world_find_grid(w,t->id);
        if (g && (g->from_system || g->from_binding)) return eng_fail("D29: edit the grid-system source; engineering bindings are not allowed on its application");
        if (!g || g->is_subgrid || g->axis[t->axis].source!=GRID_SRC_PANEL) return eng_fail("I35: dimension target is not an existing PANEL_LAYOUT main-grid axis");
        *pid=g->placement_id;
    } else {
        int i=reference_timber_index(w,t->id); if (i<0) return eng_fail("I35: dimension target timber does not exist");
        *pid=w->anchors[i].placement_id; *role=w->timbers[i].role;
    }
    return true;
}
static bool eng_resolve(World *w,const EngDimensionSource *s,const EngTarget *target,uint32_t pid,int role,Coord *value,char *path,size_t cap)
{
    if (s->kind==ENG_LITERAL) { *value=s->value; if (path) snprintf(path,cap,"explicit integer mm"); }
    else if (s->kind==ENG_SPEC) {
        size_t i=0; while (i<w->spec_count&&strcmp(w->specs[i].name,s->ref)) ++i;
        if (i==w->spec_count) return eng_fail("I35: named dimension spec is missing");
        *value=w->specs[i].value; if (path) snprintf(path,cap,"spec:%s",s->ref);
    } else if (s->kind==ENG_PARAMETER) {
        if(!parameter_coord(w,s->parameter,value))return eng_fail(g_parameter_error);
        if(path)snprintf(path,cap,"param:%u:%u",s->parameter.parameter_id,s->parameter.field_id);
    } else if (s->kind==ENG_MATERIAL) {
        const EngMaterialVersion *m=eng_material(w,s->ref,s->version);
        if (!m) return eng_fail("I34: fixed material version is missing");
        if (!target->kind) {
            if (target->field || m->kind || (s->field!=ENG_WIDTH&&s->field!=ENG_LENGTH)) return eng_fail("I35: grid panel accepts only panel material width/length; gap is separately explicit");
            *value=s->field==ENG_WIDTH?m->width:m->length;
        } else {
            if (!m->kind || s->field!=(target->field?ENG_B:ENG_A)) return eng_fail("I35: timber dimension requires matching timber material A/B field");
            *value=target->field?m->b:m->a;
        }
        if (path) snprintf(path,cap,"material:%s@%u.%s",s->ref,s->version,ENG_FIELDS[s->field]);
    } else if (s->kind==ENG_APPLICATION) {
        EngApplication *a=eng_application(w,s->ref);
        const EngMethodVersion *m=a?eng_method(w,a->method.id,a->method.version):NULL;
        if (!a||!m || (pid!=UINT32_MAX && a->placement_id!=pid)) return eng_fail("I35: application source is missing or belongs to another placement");
        EngDimensionSource nested={0}; int override=-1;
        if (!target->kind) {
            int field=target->field?(target->axis?ENG_V_GAP:ENG_U_GAP):(target->axis?ENG_V_PANEL:ENG_U_PANEL);
            if (s->field!=field) return eng_fail("I35: application field does not match target grid axis/field");
            if (target->field) { override=0; if (!a->overridden[0] && !m->has_gap) return eng_fail("I35: gap is not set; enter an explicit gap"); nested.value=m->gap; }
            else {
                int axis=a->long_axis?a->long_axis:m->long_axis;
                if (!axis || !m->panel.id[0]) return eng_fail("I35: panel material or length-axis mapping is not set");
                nested.kind=ENG_MATERIAL; nested.version=m->panel.version; snprintf(nested.ref,sizeof nested.ref,"%s",m->panel.id);
                nested.field=axis==target->axis+1?ENG_LENGTH:ENG_WIDTH;
            }
        } else {
            int r=(s->field-ENG_BOUNDARY_A)/2;
            if (s->field<ENG_BOUNDARY_A || s->field>ENG_SECONDARY_B || (s->field-ENG_BOUNDARY_A)%2!=target->field || role!=r) return eng_fail("D28: timber role does not match the explicitly bound application slot");
            override=1+r*2+target->field;
            if (!a->overridden[override] && !m->roles[r].id[0]) return eng_fail("I35: selected timber material slot is not set");
            nested.kind=ENG_MATERIAL; nested.version=m->roles[r].version; snprintf(nested.ref,sizeof nested.ref,"%s",m->roles[r].id); nested.field=target->field?ENG_B:ENG_A;
        }
        if (override>=0 && a->overridden[override]) nested=a->overrides[override];
        char tail[192]; if (!eng_resolve(w,&nested,target,pid,role,value,tail,sizeof tail)) return false;
        if (path) snprintf(path,cap,"application:%s -> method:%s@%u -> %s%s",a->id,a->method.id,a->method.version,override>=0&&a->overridden[override]?"face override -> ":"",tail);
    } else return eng_fail("I35: invalid dimension source kind");
    if (*value<((!target->kind&&target->field)?0:1) || *value>COORD_LIMIT) return eng_fail("I35: effective dimension violates its positive/nonnegative integer mm range");
    return true;
}
static bool eng_effective(World *w,const EngBinding *b,Coord *value,char *path,size_t cap)
{
    uint32_t pid; int role; if (!eng_target_context(w,&b->target,&pid,&role)) return false;
    /* During scene replay a timber declaration precedes its placement. Its role
     * is already known; final revalidation after place checks the actual face. */
    if (b->target.kind) { int i=reference_timber_index(w,b->target.id); if (!w->timbers[i].placed) pid=UINT32_MAX; }
    /* An override changes value, not binding identity: the base application must
     * still exist, be on the same face and bind the same role. */
    if (b->has_override && b->source.kind==ENG_APPLICATION) {
        EngApplication *a=eng_application(w,b->source.ref);
        if (!a || (pid!=UINT32_MAX && a->placement_id!=pid)) return eng_fail("I35: overridden application source is missing or on another placement");
        int expected=b->target.kind?ENG_BOUNDARY_A+role*2+b->target.field:(b->target.field?ENG_U_GAP:ENG_U_PANEL)+b->target.axis;
        if (role==TIMBER_ROLE_CUSTOM || b->source.field!=expected) return eng_fail("D28: overridden source still requires a matching application field/role");
    }
    if (b->has_override && b->source.kind!=ENG_APPLICATION) {
        Coord ignored;
        if (!eng_resolve(w,&b->source,&b->target,pid,role,&ignored,NULL,0)) return false;
    }
    return eng_resolve(w,b->has_override?&b->override_value:&b->source,&b->target,pid,role,value,path,cap);
}
/* D28: these records belong to the deleted identity. This is deliberately not
 * a general orphan collector: malformed loaded references must still fail I35. */
static void engineering_drop_owned(World *w,const char *kind,uint32_t id)
{
    EngineeringState *e=&w->engineering;
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
static bool engineering_follow_fragment(World *w,uint32_t old_pid)
{
    for (size_t i=0;i<w->engineering.application_count;++i) {
        EngApplication *a=&w->engineering.applications[i];
        if (a->placement_id!=old_pid) continue;
        bool found=false; uint32_t destination=old_pid;
        for (size_t j=0;j<w->engineering.binding_count;++j) {
            const EngBinding *b=&w->engineering.bindings[j];
            if (b->source.kind!=ENG_APPLICATION || strcmp(b->source.ref,a->id)) continue;
            uint32_t pid; int role;
            if (!eng_target_context(w,&b->target,&pid,&role)) return false;
            if (found && destination!=pid) return eng_fail("R13/I35: one application would span both fragments; separate its explicit bindings before splitting");
            destination=pid; found=true;
        }
        if (!found || destination==old_pid) continue;
        EngJson json;
        if (!eng_json_parse(&json,a->content)) { eng_json_free(&json); return eng_fail("I35: invalid stored application definition"); }
        const char *keys[]={"anchorOptions","id","longAxis","mainAlong","method","overrides","placement_id"};
        char content[ENG_RECORD_MAX],value[ENG_RECORD_MAX]; size_t used=0; bool valid=true;
        content[used++]='{';
        for (size_t k=0;k<sizeof keys/sizeof keys[0] && valid;++k) {
            int token=eng_json_member(&json,0,keys[k]);
            if (token<0) continue;
            if (!strcmp(keys[k],"placement_id")) snprintf(value,sizeof value,"%u",destination);
            else if (!eng_json_canonical(&json,token,value,sizeof value)) { valid=false; break; }
            int n=snprintf(content+used,sizeof content-used,"%s\"%s\":%s",used>1?",":"",keys[k],value);
            if (n<0 || (size_t)n>=sizeof content-used) valid=false; else used+=(size_t)n;
        }
        if (valid && used+2<=sizeof content) { content[used++]='}'; content[used]=0; }
        else valid=false;
        eng_json_free(&json);
        if (!valid) return eng_fail("I10: moved application exceeds record capacity");
        a->placement_id=destination; snprintf(a->content,sizeof a->content,"%s",content);
    }
    return true;
}
static bool engineering_rebuild(World *w,char *error,size_t cap)
{
    for (size_t i=0;i<w->engineering.application_count;++i) {
        const EngApplication *a=&w->engineering.applications[i];
        const PlacementSurface *placement=world_find_placement(w,a->placement_id);
        if(placement&&placement->derived_fill_id){eng_fail("D4: derived placements cannot receive D28 face applications");goto fail;}
        if (!world_find_placement(w,a->placement_id) || !eng_method(w,a->method.id,a->method.version)) { eng_fail("I35: application has a dangling placement/method reference"); goto fail; }
        for (int field=0;field<7;++field) if (a->overridden[field]) {
            EngTarget target={0}; Coord ignored; int role=-1;
            if (!field) target.field=1;
            else { target.kind=1; target.field=(field-1)%2; role=(field-1)/2; }
            if (!eng_resolve(w,&a->overrides[field],&target,a->placement_id,role,&ignored,NULL,0)) goto fail;
        }
    }
    for (size_t i=0;i<w->engineering.binding_count;++i) {
        const EngBinding *b=&w->engineering.bindings[i]; Coord value;
        if (!eng_effective(w,b,&value,NULL,0)) goto fail;
        if (!b->target.kind) { ReferenceGrid *g=world_find_grid_mut(w,b->target.id); if (g->from_system || g->from_binding) { eng_fail("D29: grid-system applications cannot have engineering bindings"); goto fail; } if (b->target.field) g->axis[b->target.axis].gap=value; else g->axis[b->target.axis].panel=value; }
        else { int t=reference_timber_index(w,b->target.id); if (b->target.field) w->timbers[t].size_b=value; else w->timbers[t].size_a=value; }
    }
    if (!engineering_serializable(w)) goto fail;
    return true;
fail:
    snprintf(error,cap,"%s",g_engineering_error); return false;
}
static bool eng_source_json(const EngDimensionSource *s,char *out,size_t cap)
{
    char q[600]; int n;
    if (s->kind==ENG_LITERAL) n=snprintf(out,cap,"{\"kind\":\"literal\",\"value\":%lld}",(long long)s->value);
    else if(s->kind==ENG_PARAMETER)n=snprintf(out,cap,"{\"kind\":\"parameter\",\"parameterId\":%u,\"fieldId\":%u}",s->parameter.parameter_id,s->parameter.field_id);
    else if (s->kind==ENG_SPEC) { if (!eng_json_quote(s->ref,q,sizeof q)) return false; n=snprintf(out,cap,"{\"kind\":\"spec\",\"name\":%s}",q); }
    else { if (!eng_json_quote(s->ref,q,sizeof q)) return false; if (s->kind==ENG_MATERIAL) n=snprintf(out,cap,"{\"field\":\"%s\",\"id\":%s,\"kind\":\"material\",\"version\":%u}",ENG_FIELDS[s->field],q,s->version); else n=snprintf(out,cap,"{\"field\":\"%s\",\"id\":%s,\"kind\":\"application\"}",ENG_FIELDS[s->field],q); }
    return n>=0&&(size_t)n<cap;
}
static void eng_target_json(const EngTarget *t,FILE *out)
{
    if (!t->kind) fprintf(out,"{\"axis\":\"%c\",\"field\":\"%s\",\"id\":%u,\"kind\":\"grid\"}",t->axis?'v':'u',t->field?"gap":"panel",t->id);
    else fprintf(out,"{\"field\":\"%s\",\"id\":%u,\"kind\":\"timber\"}",t->field?"B":"A",t->id);
}
typedef struct { char text[1450]; size_t size; bool ok; } EngBuffer;
static void eng_append(EngBuffer *b,const char *format,...)
{
    if(!b->ok)return;va_list args;va_start(args,format);int n=vsnprintf(b->text+b->size,sizeof b->text-b->size,format,args);va_end(args);
    if(n<0||(size_t)n>=sizeof b->text-b->size)b->ok=false;else b->size+=(size_t)n;
}
static void eng_dimension_json(const World *w,const EngTarget *t,Coord direct,EngBuffer *out)
{
    const EngBinding *b=NULL;for(size_t i=0;i<w->engineering.binding_count;++i)if(eng_same_target(t,&w->engineering.bindings[i].target)){b=&w->engineering.bindings[i];break;}
    if(!b){eng_append(out,"%lld",(long long)direct);return;}
    char source[640],override[640];if(!eng_source_json(&b->source,source,sizeof source)){out->ok=false;return;}
    if(b->has_override){if(!eng_source_json(&b->override_value,override,sizeof override)){out->ok=false;return;}}else snprintf(override,sizeof override,"null");
    eng_append(out,"{\"override\":%s,\"source\":%s}",override,source);
}
static bool eng_grid_content(const World *w,const ReferenceGrid *g,EngBuffer *b)
{
    memset(b,0,sizeof *b);b->ok=true;eng_append(b,"{\"axes\":{");
    for(int axis=0;axis<2;++axis){const GridAxisDef *d=&g->axis[axis];eng_append(b,"%s\"%c\":",axis?",":"",axis?'v':'u');
        if(d->source==GRID_SRC_NONE){eng_append(b,"null");continue;}
        if(d->source==GRID_SRC_PANEL){eng_append(b,"{\"anchor\":%lld,\"gap\":",(long long)d->anchor);EngTarget gap={0,g->id,axis,1},panel={0,g->id,axis,0};eng_dimension_json(w,&gap,d->gap,b);eng_append(b,",\"kind\":\"panel\",\"panel\":");eng_dimension_json(w,&panel,d->panel,b);eng_append(b,"}");}
        else if(d->source==GRID_SRC_SERIES)eng_append(b,"{\"count\":%u,\"kind\":\"series\",\"start\":%lld,\"step\":%lld}",(unsigned)d->series_count,(long long)d->start,(long long)d->step);
        else{eng_append(b,"{\"coords\":[");for(size_t k=0;k<d->count;++k)eng_append(b,"%s%lld",k?",":"",(long long)d->coords[k]);eng_append(b,"],\"kind\":\"explicit\"}");}
    }
    eng_append(b,"},\"id\":%u,\"mainAlong\":",g->id);if(g->main_along)eng_append(b,"\"%c\"",g->main_along==1?'u':'v');else eng_append(b,"null");eng_append(b,",\"placement_id\":%u}",g->placement_id);return b->ok;
}
static bool eng_timber_content(const World *w,const Timber *t,EngBuffer *b)
{
    memset(b,0,sizeof *b);b->ok=true;EngTarget a={1,t->id,0,0},z={1,t->id,0,1};eng_append(b,"{\"A\":");eng_dimension_json(w,&a,t->size_a,b);eng_append(b,",\"B\":");eng_dimension_json(w,&z,t->size_b,b);eng_append(b,",\"id\":%u",t->id);if(t->role==TIMBER_ROLE_CUSTOM)eng_append(b,",\"priority\":%lld",(long long)t->cut_priority);eng_append(b,",\"role\":\"%s\"}",timber_role_name(t->role));return b->ok;
}
static bool engineering_serializable(const World *w)
{
    EngBuffer b;
    for(size_t i=0;i<w->grid_count;++i)if(eng_object_bound(w,0,w->grids[i].id)&&!eng_grid_content(w,&w->grids[i],&b))return eng_fail("I10: bound grid definition exceeds scene record capacity");
    for(size_t i=0;i<w->timber_count;++i)if(eng_object_bound(w,1,w->timbers[i].id)&&!eng_timber_content(w,&w->timbers[i],&b))return eng_fail("I10: bound timber definition exceeds scene record capacity");
    return true;
}
static void eng_dump_record(FILE *out,const char *kind,const char *json)
{
    char encoded[1950];size_t n;if(!eng_base64_encode(json,strlen(json),encoded,sizeof encoded,&n)){fputs("requires engineering-record-capacity-error\n",out);return;}
    fprintf(out,"engineering %s %s\n",kind,encoded);
}
static void engineering_dump_versions(const World *w,FILE *out)
{
    if(!engineering_used(w))return;fputs("requires engineering-spec/1\n",out);char record[1200];
    for(size_t i=0;i<w->engineering.material_count;++i){const EngMaterialVersion *m=&w->engineering.materials[i];snprintf(record,sizeof record,"{\"fingerprint\":\"%s\",\"value\":%s}",m->fingerprint,m->content);eng_dump_record(out,"material",record);}
    for(size_t i=0;i<w->engineering.method_count;++i){const EngMethodVersion *m=&w->engineering.methods[i];snprintf(record,sizeof record,"{\"fingerprint\":\"%s\",\"value\":%s}",m->fingerprint,m->content);eng_dump_record(out,"method",record);}
    for(int kind=0;kind<2;++kind){size_t count=kind?w->engineering.method_count:w->engineering.material_count;for(size_t i=0;i<count;++i){bool archived=kind?w->engineering.methods[i].archived:w->engineering.materials[i].archived;const EngVersionRef *r=kind?&w->engineering.methods[i].ref:&w->engineering.materials[i].ref;if(archived){snprintf(record,sizeof record,"{\"id\":\"%s\",\"kind\":\"%s\",\"op\":\"archive\",\"value\":true,\"version\":%u}",r->id,kind?"method":"material",r->version);eng_dump_record(out,"archive",record);}}}
}
static void engineering_dump_applications(const World *w,FILE *out)
{
    for(size_t i=0;i<w->engineering.application_count;++i)eng_dump_record(out,"application",w->engineering.applications[i].content);
}
static bool engineering_dump_grid(const World *w,const ReferenceGrid *g,FILE *out)
{
    if(!eng_object_bound(w,0,g->id))return false;EngBuffer b;if(eng_grid_content(w,g,&b))eng_dump_record(out,"grid",b.text);else fputs("requires engineering-record-capacity-error\n",out);return true;
}
static bool engineering_dump_timber(const World *w,const Timber *t,FILE *out)
{
    if(!eng_object_bound(w,1,t->id))return false;EngBuffer b;if(eng_timber_content(w,t,&b))eng_dump_record(out,"timber",b.text);else fputs("requires engineering-record-capacity-error\n",out);return true;
}
