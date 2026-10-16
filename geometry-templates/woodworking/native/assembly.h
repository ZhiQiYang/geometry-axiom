/* D32/D33: bounded canonical definitions copied with native World/history. */
#ifndef GEOMETRY_WOODWORKING_ASSEMBLY_H
#define GEOMETRY_WOODWORKING_ASSEMBLY_H
#include "engineering.h"
#include "members.h"
#define ASM_NAME_MAX 97
#define ASM_ID_MAX 65
#define ASM_RULE_MAX 32
#define ASM_SLOT_MAX 8
#define ASM_MEMBER_MAX 12
#define ASM_JOINT_MAX 16
#define ASM_BINDING_MAX 64
#define ASM_RECORD_MAX 8192
#define ASM_SCHEMA "assembly-rule/1"
#define ASM_CAPABILITY "assembly-rule-authoring/1"

typedef enum { ASM_JOINT_END_TO_SIDE = 1, ASM_JOINT_ORTHO_SPLIT = 2 } AsmJointKind;
typedef enum { ASM_END_START = 1, ASM_END_FINISH = 2 } AsmEnd;
typedef enum { ASM_SIDE_POS_U = 1, ASM_SIDE_NEG_U = 2, ASM_SIDE_POS_V = 3, ASM_SIDE_NEG_V = 4 } AsmSide;
typedef enum { ASM_DIR_U = 1, ASM_DIR_V = 2 } AsmDir;
typedef enum { ASM_SRC_UNSET = 0, ASM_SRC_MATERIAL = 1, ASM_SRC_PARAMETER = 2, ASM_SRC_LITERAL = 3 } AsmSourceKind;
typedef enum { ASM_FACE_UNSET = 0, ASM_FACE_A = 1, ASM_FACE_B = 2 } AsmContactFace;
typedef enum { ASM_ORIENT_UNSET = 0, ASM_ORIENT_A = 1, ASM_ORIENT_B = 2 } AsmSectionOrient;

typedef struct { uint32_t id; char name[ASM_NAME_MAX]; } AsmSlot;
typedef struct { uint32_t id; uint32_t slot_id; } AsmMember;
typedef struct {
    uint32_t id;
    int kind;
    uint32_t members[4];
    int member_count;
    uint32_t continuous_member;
    uint32_t terminated_member;
    int term_end;
    int target_side;
    int relative_dir;
} AsmJoint;
typedef struct {
    uint32_t id, version;
    char name[ASM_NAME_MAX];
    char fingerprint[65];
    char content[ASM_RECORD_MAX];
} AsmRuleVersion;
typedef struct {
    int kind;
    char material_id[ASM_ID_MAX];
    uint32_t material_version, parameter_id, field_id;
    int64_t literal_mm;
    int contact_face, section_orient;
} AsmSlotBinding;
typedef struct {
    uint32_t id, rule_id, rule_version;
    char name[ASM_NAME_MAX], content[ASM_RECORD_MAX];
    bool complete;
} AsmBinding;
#define ASM_INSTANCE_MAX 16
#define ASM_GENERATION_CAPABILITY "assembly-timber-generation/1"
typedef struct {
    uint32_t id,binding_id,surface_id,rule_id,rule_version;
    char name[ASM_NAME_MAX],rule_hash[65],content[ASM_RECORD_MAX];
    uint32_t member[3],timber[3],guide[3],ends[3][2];
    bool secondary[3];
} AsmInstance;
typedef struct { uint32_t timber,instance,member; } AsmOwner;
typedef struct {
    AsmRuleVersion rules[ASM_RULE_MAX];
    size_t rule_count;
    AsmBinding bindings[ASM_BINDING_MAX];
    size_t binding_count;
    AsmInstance instances[ASM_INSTANCE_MAX];
    size_t instance_count;
    AsmOwner owners[ASM_INSTANCE_MAX*3];
    size_t owner_count;
    bool generation_required;
    bool loading;
} AssemblyState;

/* Transient diagnostics stay outside the copied definition store. */
typedef struct { int kind;uint32_t id,field_id,version; } AsmDiagnostic;
typedef struct { uint32_t surface_id; AsmDir direction; } WoodAssemblyGuide;
typedef struct { uint32_t surface_id; WoodMemberRole role; GeoCoord width,depth; bool placed; } WoodAssemblyMember;
typedef struct {
    GeoCoord width,depth;
    uint32_t surface_id,guide_id,between[2];
    AsmDir direction;
    WoodMemberRole role;
} WoodAssemblyDefinition;
/* Host callbacks expose facts, storage writes and legacy serialization only.
 * W selects topology, dimensions, roles, support dependencies and phase order. */
typedef struct {
    AssemblyState *state;
    WoodEngineeringContext engineering;
    AsmDiagnostic *diagnostic;
    GeoParameterRef *parameter_dimension_error;
    void *user;
    bool scene_loading;
    bool (*json_parse)(void *,GeoJson *,const char *);
    void (*drop_position)(void *,bool,uint32_t);
    bool (*other_operation)(void *,GeoJson *,int);
    bool (*surface)(void *,uint32_t);
    bool (*guide)(void *,uint32_t,WoodAssemblyGuide *);
    bool (*member)(void *,uint32_t,WoodAssemblyMember *);
    bool (*footprint)(void *,uint32_t,uint32_t,GeoRect2 *);
    size_t (*member_count)(void *);
    size_t member_capacity;
    void (*allocate_member)(void *,uint32_t);
    bool (*remove_member)(void *,uint32_t);
    void (*write_member)(void *,const WoodMember *,const WoodAssemblyDefinition *);
    bool (*anchor_matches)(void *,uint32_t,const WoodAssemblyDefinition *);
    bool (*instance_content)(void *,AsmInstance *,GeoJson *,int);
} WoodAssemblyContext;
const AsmRuleVersion *wood_assembly_rule(const WoodAssemblyContext *,uint32_t,uint32_t);
AsmBinding *wood_assembly_binding(WoodAssemblyContext *,uint32_t);
AsmInstance *wood_assembly_instance(WoodAssemblyContext *,uint32_t);
bool wood_assembly_used(const WoodAssemblyContext *);
bool wood_assembly_owned(const WoodAssemblyContext *,uint32_t);
bool wood_assembly_publish(WoodAssemblyContext *,GeoJson *,int,const char *);
bool wood_assembly_put_binding(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_versions_immutable(const WoodAssemblyContext *,const WoodAssemblyContext *);
bool wood_assembly_rebuild(WoodAssemblyContext *,char *,size_t);
bool wood_assembly_dimensions_changed(const WoodAssemblyContext *,const WoodAssemblyContext *);
bool wood_assembly_operation(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_generation_integrity(const WoodAssemblyContext *);
bool wood_assembly_generation_prepare(WoodAssemblyContext *);
bool wood_assembly_generation_check(const WoodAssemblyContext *);
bool wood_assembly_generation_operation(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_instance_load(WoodAssemblyContext *,GeoJson *,int);

#endif
