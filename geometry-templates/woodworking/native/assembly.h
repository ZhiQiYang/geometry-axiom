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
#define ASM_INSTANCE_RECORD_MAX 65536
#define ASM_GENERATION_CAPABILITY "assembly-timber-generation/1"
#define ASM_BAY_CAPABILITY "assembly-bay-repeat/1"
/* R06 storage, planning and the host share GEO-300's member capacity. */
#define ASM_BAY_WORLD_MAX WOOD_MEMBER_CAPACITY
#define ASM_OWNER_MAX WOOD_MEMBER_CAPACITY
#define ASM_BAY_PRIMARY_MAX 12
#define ASM_BAY_LINE_MAX 24
#define ASM_BAY_OMIT_MAX 24
#define ASM_BAY_CELL_MAX ((ASM_BAY_PRIMARY_MAX-1)*ASM_BAY_LINE_MAX)
typedef enum { ASM_ID_MEMBER=0, ASM_ID_PRIMARY=1, ASM_ID_SECONDARY=2 } AsmIdentityKind;
typedef struct { int kind; uint32_t key,left,right; } AsmIdentity;
typedef enum { ASM_AT_GUIDE=1, ASM_AT_GRID=2, ASM_AT_OUTLINE=3 } AsmLocationKind;
typedef struct { int kind,axis,edge; uint32_t id; int64_t index; char edge_key[512]; } AsmLocation;
typedef struct { uint32_t key; AsmLocation at; uint32_t ends[2]; } AsmBayPrimary;
typedef struct { uint32_t key; AsmLocation at; } AsmBayLine;
typedef struct { uint32_t line,left,right; } AsmBayCell;
typedef struct { AsmIdentity identity; uint32_t timber; } AsmMapping;
typedef struct {
    uint32_t id,binding_id,surface_id,rule_id,rule_version;
    char name[ASM_NAME_MAX],rule_hash[65],content[ASM_INSTANCE_RECORD_MAX];
    uint32_t member[3],timber[3],guide[3],ends[3][2];
    bool secondary[3];
    bool bay_repeat;
    AsmBayPrimary primaries[ASM_BAY_PRIMARY_MAX];
    AsmBayLine lines[ASM_BAY_LINE_MAX];
    AsmBayCell omit[ASM_BAY_OMIT_MAX];
    AsmMapping mapping[ASM_OWNER_MAX];
    size_t primary_count,line_count,omit_count,mapping_count;
} AsmInstance;
/* Legacy member stays first: old scene records and initializers are unchanged. */
typedef struct { uint32_t timber,instance,member; int kind; uint32_t left,right; } AsmOwner;
typedef struct {
    AsmRuleVersion rules[ASM_RULE_MAX];
    size_t rule_count;
    AsmBinding bindings[ASM_BINDING_MAX];
    size_t binding_count;
    AsmInstance instances[ASM_INSTANCE_MAX];
    size_t instance_count;
    AsmOwner owners[ASM_OWNER_MAX];
    size_t owner_count;
    bool generation_required;
    bool loading;
    bool bay_required;
} AssemblyState;

/* Transient diagnostics stay outside the copied definition store. */
typedef struct { int kind;uint32_t id,field_id,version; } AsmDiagnostic;
typedef struct { uint32_t surface_id; AsmDir direction; } WoodAssemblyGuide;
typedef struct { uint32_t surface_id; WoodMemberRole role; GeoCoord width,depth; bool placed; } WoodAssemblyMember;
typedef struct {
    uint32_t surface_id; int axis;
    GeoCoord coordinate;
    bool subgrid,phased,from_fill;
    GeoSegment2 edge; GeoPoint2 outward;
} WoodAssemblyPosition;
typedef struct { int kind; uint32_t id; } WoodAssemblyDependency;
enum { ASM_DEP_TIMBER=1,ASM_DEP_GUIDE=2,ASM_DEP_GRID=3,ASM_DEP_OUTLINE=4,ASM_DEP_DATUM=5 };
#define ASM_BAY_PATH_MAX 64
typedef struct {
    char category[16],code[32],clause[32],expected[160],actual[256];
    uint32_t instance,primary,line,owned;
    WoodAssemblyDependency path[ASM_BAY_PATH_MAX]; size_t path_count;
} AsmBayIssue;
typedef struct { uint32_t instance,line,left,right,timber; bool omitted; } AsmBayCellReport;
typedef struct { uint32_t instance,key; GeoRect2 range; } AsmBayPrimaryReport;
/* Candidate-only evidence: never copied into World/history or serialized. */
typedef struct {
    AsmBayCellReport cells[ASM_INSTANCE_MAX*ASM_BAY_CELL_MAX]; size_t cell_count;
    AsmBayPrimaryReport primaries[ASM_INSTANCE_MAX*ASM_BAY_PRIMARY_MAX]; size_t primary_count;
    AsmBayIssue issues[ASM_OWNER_MAX]; size_t issue_count;
    uint32_t retired[ASM_OWNER_MAX]; size_t retired_count;
} AsmBayReport;
typedef struct {
    GeoCoord width,depth;
    uint32_t surface_id,guide_id,between[2];
    AsmDir direction;
    WoodMemberRole role;
    uint32_t timber_id,reserved;
    AsmLocation at;
} WoodAssemblyDefinition;
typedef struct {
    void *user;
    bool (*rule_definition)(void *,uint32_t,uint32_t);
    bool (*binding)(void *,const AsmBinding *,AsmBinding *);
    bool (*slot_definition)(void *,uint32_t,uint32_t);
    bool (*slot_dimension)(void *,uint32_t,uint32_t,int,const EngDimensionSource *,GeoCoord *,char *,size_t);
    bool (*generated)(void *,const AsmInstance *,int,WoodAssemblyDefinition *);
    bool (*generated_dimension)(void *,const AsmInstance *,int,uint32_t,int,const EngDimensionSource *,GeoCoord *,char *,size_t);
    bool (*instance_check)(void *,const AsmInstance *);
    /* Optional returned authored records. Slot replacement is read at the
     * existing per-slot policy phase; instance replacement precedes only that
     * instance's original primary/secondary write sequence. */
    bool (*slot_record)(void *,uint32_t,uint32_t,char *,size_t);
    bool (*instance_definition)(void *,const AsmInstance *,const AsmInstance **);
    bool (*bay_generated)(void *,const AsmInstance *,AsmIdentity,WoodAssemblyDefinition *);
} WoodAssemblyEvaluation;
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
    /* P-121/P-129: after a binding put succeeds, H records that owner's explicit
     * parameter-source declaration in the candidate order (no-op when untracked). */
    bool (*declare_binding)(void *,uint32_t);
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
    const WoodAssemblyEvaluation *evaluation;
    AsmBayReport *bay_report;
    /* Read-only same-candidate facts. W chooses admissibility and traversal. */
    bool (*position)(void *,uint32_t,const AsmLocation *,WoodAssemblyPosition *);
    bool (*dependencies)(void *,WoodAssemblyDependency,WoodAssemblyDependency *,size_t,size_t *,bool);
    bool (*external_reference)(void *,uint32_t,uint32_t,char *,size_t);
} WoodAssemblyContext;
const AsmRuleVersion *wood_assembly_rule(const WoodAssemblyContext *,uint32_t,uint32_t);
AsmBinding *wood_assembly_binding(WoodAssemblyContext *,uint32_t);
AsmInstance *wood_assembly_instance(WoodAssemblyContext *,uint32_t);
bool wood_assembly_used(const WoodAssemblyContext *);
bool wood_assembly_owned(const WoodAssemblyContext *,uint32_t);
bool wood_assembly_publish(WoodAssemblyContext *,GeoJson *,int,const char *);
/* Definition readers share the authoring policy but never allocate members,
 * write candidate authoring, resolve dimensions or read host geometry. */
bool wood_assembly_rule_parse(WoodAssemblyContext *,GeoJson *,int,AsmRuleVersion *);
bool wood_assembly_instance_definition_parse(WoodAssemblyContext *,GeoJson *,int,AsmInstance *);
bool wood_assembly_put_binding(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_versions_immutable(const WoodAssemblyContext *,const WoodAssemblyContext *);
bool wood_assembly_rebuild(WoodAssemblyContext *,char *,size_t);
bool wood_assembly_binding_rebuild_direct(WoodAssemblyContext *,const AsmBinding *,AsmBinding *);
bool wood_assembly_slot_dimension_direct(WoodAssemblyContext *,uint32_t,uint32_t,int,GeoCoord *,char *,size_t);
bool wood_assembly_dimensions_changed(const WoodAssemblyContext *,const WoodAssemblyContext *);
bool wood_assembly_operation(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_generation_integrity(const WoodAssemblyContext *);
bool wood_assembly_generation_prepare(WoodAssemblyContext *);
bool wood_assembly_generation_check(const WoodAssemblyContext *);
bool wood_assembly_member_definition_direct(WoodAssemblyContext *,const AsmInstance *,int,WoodAssemblyDefinition *);
bool wood_assembly_generated_dimension_direct(WoodAssemblyContext *,const AsmInstance *,int,int,GeoCoord *,char *,size_t);
bool wood_assembly_instance_check_direct(const WoodAssemblyContext *,const AsmInstance *);
bool wood_assembly_generation_operation(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_instance_load(WoodAssemblyContext *,GeoJson *,int);
bool wood_assembly_identity_equal(AsmIdentity,AsmIdentity);
size_t wood_assembly_mapping_count(const AsmInstance *);
AsmMapping wood_assembly_mapping_at(const AsmInstance *,size_t);
AsmIdentity wood_assembly_owner_identity(const AsmOwner *);
int wood_assembly_mapping_index(const AsmInstance *,AsmIdentity);
bool wood_assembly_bay_parse(WoodAssemblyContext *,GeoJson *,int,AsmInstance *);
bool wood_assembly_bay_prepare(WoodAssemblyContext *);
bool wood_assembly_bay_member_definition_direct(WoodAssemblyContext *,const AsmInstance *,AsmIdentity,WoodAssemblyDefinition *);
bool wood_assembly_bay_check(const WoodAssemblyContext *,const AsmInstance *);
bool wood_assembly_bay_failure(const WoodAssemblyContext *,const char *,const char *,const char *,uint32_t,uint32_t,uint32_t,const char *,const char *);

#endif
