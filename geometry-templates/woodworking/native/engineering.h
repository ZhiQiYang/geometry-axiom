/* D26-D28 woodworking definitions. This POD store belongs to W and can be
 * copied with an isolated host candidate; it has no kernel or host backpointer. */
#ifndef GEOMETRY_WOODWORKING_ENGINEERING_H
#define GEOMETRY_WOODWORKING_ENGINEERING_H
#ifndef GEOMETRY_KERNEL_GEOMETRY_H
#include "geometry.h"
#endif
#ifndef GEOMETRY_KERNEL_PARAMETERS_H
#include "parameters.h"
#endif
#ifndef GEO_KERNEL_NAMED_VALUES_H
#include "named_values.h"
#endif
#ifndef GEOMETRY_KERNEL_CODEC_H
#include "codec.h"
#endif
/* D26-D28: fixed-capacity definitions, copied with the native World/history. */
#define ENG_ID_MAX 65
#define ENG_RECORD_MAX 1024
#define ENG_THICKNESS_CAPACITY 128 /* D26 decimal source, including the terminating NUL. */
#define ENG_MATERIAL_MAX 64
#define ENG_METHOD_MAX 32
#define ENG_APPLICATION_MAX 16
#define ENG_BINDING_MAX 192
#define ENG_OPERATION_MAX 256
#define ENG_INPUT_MAX (1024u * 1024u)

typedef struct { char id[ENG_ID_MAX]; uint32_t version; } EngVersionRef;
typedef enum { ENG_LITERAL, ENG_SPEC, ENG_MATERIAL, ENG_APPLICATION, ENG_PARAMETER } EngSourceKind;
typedef enum {
    ENG_WIDTH, ENG_LENGTH, ENG_A, ENG_B,
    ENG_U_PANEL, ENG_V_PANEL, ENG_U_GAP, ENG_V_GAP,
    ENG_BOUNDARY_A, ENG_BOUNDARY_B, ENG_PRIMARY_A, ENG_PRIMARY_B,
    ENG_SECONDARY_A, ENG_SECONDARY_B
} EngField;
typedef struct {
    int kind, field;
    GeoCoord value;
    char ref[GEO_NAMED_VALUE_NAME_BYTES];
    uint32_t version;
    GeoParameterRef parameter;
} EngDimensionSource;
typedef struct {
    int kind; /* 0=grid, 1=timber */
    uint32_t id;
    int axis, field; /* grid: axis 0/1, field 0=panel/1=gap; timber: 0=A/1=B */
} EngTarget;
typedef struct {
    EngTarget target;
    EngDimensionSource source, override_value;
    bool has_override;
} EngBinding;
typedef struct {
    EngVersionRef ref;
    char fingerprint[65], content[ENG_RECORD_MAX];
    int kind; /* 0=panel, 1=timber */
    GeoCoord width, length, a, b;
    bool archived;
} EngMaterialVersion;
typedef struct {
    EngVersionRef ref;
    char fingerprint[65], content[ENG_RECORD_MAX];
    EngVersionRef panel, roles[3];
    bool has_gap, archived;
    GeoCoord gap;
    int long_axis, main_along; /* 0=unset, 1=u, 2=v */
} EngMethodVersion;
typedef struct {
    char id[ENG_ID_MAX], content[ENG_RECORD_MAX];
    uint32_t placement_id;
    EngVersionRef method;
    int long_axis, main_along;
    bool overridden[7]; /* gap then each role A/B */
    EngDimensionSource overrides[7];
    int anchor_kind[2]; /* 0=unset,1=coordinate,2=min,3=max */
    GeoCoord anchor[2]; /* creation preference only, never an effective grid anchor */
} EngApplication;
typedef struct {
    EngMaterialVersion materials[ENG_MATERIAL_MAX]; size_t material_count;
    EngMethodVersion methods[ENG_METHOD_MAX]; size_t method_count;
    EngApplication applications[ENG_APPLICATION_MAX]; size_t application_count;
    EngBinding bindings[ENG_BINDING_MAX]; size_t binding_count;
} EngineeringState;

typedef struct {
    uint32_t placement_id;
    int role;
    bool from_system, is_subgrid, panel_axis, placed;
} WoodEngineeringTargetInfo;
/* Required callbacks expose host-selected facts and commit each resolved
 * cache in original order. They never select materials or override policy.
 * serializable is the final legacy-record capacity check. Its error storage
 * and the parameter callback's error storage are owned by this context. */
typedef struct {
    EngineeringState *state;
    void *user;
    char *error;
    size_t error_capacity;
    bool (*placement)(void *,uint32_t,bool *);
    bool (*target)(void *,const EngTarget *,WoodEngineeringTargetInfo *);
    bool (*named_value)(void *,const char *,GeoCoord *);
    bool (*parameter)(void *,GeoParameterRef,GeoCoord *,char *,size_t);
    bool (*member_owned)(void *,uint32_t);
    void (*write_dimension)(void *,const EngTarget *,GeoCoord);
    bool (*serializable)(void *,char *,size_t);
} WoodEngineeringContext;
bool wood_eng_fail(const WoodEngineeringContext *,const char *);
extern const char *const ENG_FIELDS[14];
bool wood_eng_u32(const GeoJson *j,int t,uint32_t *out,bool positive);
bool wood_eng_id(const char *s);
bool wood_eng_coord(const GeoJson *j,int t,GeoCoord *out,bool positive);
bool wood_eng_optional_text(const GeoJson *j,int obj,const char *key);
bool wood_eng_ref_parse(GeoJson *j,int t,EngVersionRef *r,bool optional);
bool wood_eng_axis(const GeoJson *j,int t,int *axis);
const EngMaterialVersion *wood_eng_material(const WoodEngineeringContext *w,const char *id,uint32_t version);
const EngMethodVersion *wood_eng_method(const WoodEngineeringContext *w,const char *id,uint32_t version);
EngApplication *wood_eng_application(WoodEngineeringContext *w,const char *id);
bool wood_eng_source_parse(WoodEngineeringContext *w,GeoJson *j,int t,EngDimensionSource *s,bool allow_app);
bool wood_eng_target_parse(WoodEngineeringContext *w,GeoJson *j,int t,EngTarget *target);
bool wood_eng_same_target(const EngTarget *a,const EngTarget *b);
EngBinding *wood_eng_binding(WoodEngineeringContext *w,const EngTarget *target);
bool wood_eng_bind(WoodEngineeringContext *w,const EngTarget *target,const EngDimensionSource *source);
bool wood_eng_object_bound(const WoodEngineeringContext *w,int kind,uint32_t id);
bool wood_engineering_used(const WoodEngineeringContext *w);
bool wood_eng_publish_material(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint);
bool wood_eng_publish_method(WoodEngineeringContext *w,GeoJson *j,int t,const char *fingerprint);
bool wood_eng_put_application(WoodEngineeringContext *w,GeoJson *j,int t);
bool wood_eng_target_context(const WoodEngineeringContext *w,const EngTarget *t,uint32_t *pid,int *role);
bool wood_eng_resolve(WoodEngineeringContext *w,const EngDimensionSource *s,const EngTarget *target,uint32_t pid,int role,GeoCoord *value,char *path,size_t cap);
bool wood_eng_effective(WoodEngineeringContext *w,const EngBinding *b,GeoCoord *value,char *path,size_t cap);
void wood_engineering_drop_owned(WoodEngineeringContext *w,const char *kind,uint32_t id);
bool wood_engineering_follow_fragment(WoodEngineeringContext *w,uint32_t old_pid);
bool wood_engineering_rebuild(WoodEngineeringContext *w,char *error,size_t cap);
#endif
